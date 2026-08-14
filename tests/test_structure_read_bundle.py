from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest

from software_world_model.application_services.knowledge_use import TaskBoundary
from software_world_model.application_services.structure_read_bundle import (
    JAVA_IMPLEMENTATION_FEATURE_DISCOVERY_CONTRACT_REF,
    STRUCTURE_ORDERED_READ_BUNDLE_WITH_DISCOVERY_FORMAT,
    StructureBusinessDiscoveryRecallBinding,
    StructureBusinessDiscoveryRecallVerdict,
    StructureOrderedReadBundle,
    StructureReadBundleAvailabilityStatus,
    StructureReadBundleService,
    StructureSnapshotBundleReference,
)
from software_world_model.application_services.structure_read_session import (
    StructureCoverageReadBinding,
    StructureReadPurpose,
    StructureReadSessionService,
    StructureSnapshotReadBinding,
    structure_ordered_read_set_digest,
    structure_read_session_digest,
)
from software_world_model.cross_cutting import (
    CorrelationRef,
    Digest,
    DomainError,
    ErrorCode,
    IdempotencyKey,
    Revision,
    StableId,
    canonical_json_bytes,
    digest_of,
)
from software_world_model.infrastructure.file_structure_read_bundle import (
    FileStructureReadBundleStore,
)
from software_world_model.infrastructure.sqlite_database import SqliteDatabase
from software_world_model.infrastructure.sqlite_scope_repository import (
    SqliteKnowledgeScopeRepository,
)
from software_world_model.infrastructure.sqlite_structure_read_bundle_repository import (
    SqliteStructureReadBundleRepository,
)
from software_world_model.infrastructure.sqlite_structure_read_session_repository import (
    SqliteStructureReadSessionRepository,
)
from software_world_model.knowledge_engine.context_comparison import (
    StructureContextComparisonService,
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
    PublicationMode,
    StructureEvidence,
)
from software_world_model.knowledge_engine.structure_authority import (
    StructureSchemaAdoptionMode,
)
from software_world_model.knowledge_engine.structure_publication import (
    SnapshotCoverage,
    StructureEvidenceMetadata,
    StructureSnapshot,
)


class SequenceIds:
    def __init__(self) -> None:
        self.value = 0

    def new(self, kind: str) -> StableId:
        self.value += 1
        return StableId(f"{kind}_{self.value:032x}")


class FrozenClock:
    def __init__(self) -> None:
        self.value = datetime(2026, 8, 10, 12, 0, tzinfo=timezone.utc)

    def __call__(self) -> datetime:
        return self.value


class FakeStructureBundleSource:
    def __init__(self) -> None:
        self.snapshots: dict[StableId, StructureSnapshot] = {}
        self.coverages: dict[tuple[StableId, StableId], CoverageRecord] = {}
        self.entities: dict[tuple[StableId, StableId], EntityRecord] = {}
        self.evidence: dict[StableId, StructureEvidenceMetadata] = {}
        self.current_by_scope: dict[StableId, StableId] = {}

    def add(
        self,
        snapshot: StructureSnapshot,
        coverage: CoverageRecord,
        entity: EntityRecord,
        metadata: StructureEvidenceMetadata,
        *,
        current: bool = False,
    ) -> None:
        self.snapshots[snapshot.snapshot_id] = snapshot
        self.coverages[(snapshot.snapshot_id, coverage.root_id)] = coverage
        self.entities[(snapshot.snapshot_id, entity.root_id)] = entity
        self.evidence[metadata.evidence_id] = metadata
        if current:
            self.current_by_scope[snapshot.scope_id] = snapshot.snapshot_id

    def current_snapshot(self, scope_id: StableId) -> StructureSnapshot | None:
        snapshot_id = self.current_by_scope.get(scope_id)
        return self.snapshots.get(snapshot_id) if snapshot_id is not None else None

    def get_snapshot(self, snapshot_id: StableId) -> StructureSnapshot:
        return self.snapshots[snapshot_id]

    def get_coverage(
        self, snapshot_id: StableId, coverage_root_id: StableId
    ) -> CoverageRecord:
        return self.coverages[(snapshot_id, coverage_root_id)]

    def get_entity(
        self, snapshot_id: StableId, entity_root_id: StableId
    ) -> EntityRecord:
        return self.entities[(snapshot_id, entity_root_id)]

    def get_relation_fact(self, snapshot_id: StableId, relation_root_id: StableId):
        raise KeyError((snapshot_id, relation_root_id))

    def get_literal_fact(self, snapshot_id: StableId, literal_root_id: StableId):
        raise KeyError((snapshot_id, literal_root_id))

    def get_evidence_metadata(
        self, evidence_id: StableId
    ) -> StructureEvidenceMetadata:
        return self.evidence[evidence_id]


class FailingFileStore:
    def write_snapshot(self, locator: str, bundle):
        raise OSError("simulated write failure")


class WrongOrderedReceiptFileStore:
    def __init__(self, delegate: FileStructureReadBundleStore) -> None:
        self._delegate = delegate

    def read_snapshot(self, locator: str):
        return self._delegate.read_snapshot(locator)

    def write_ordered(self, locator: str, bundle):
        stored = self._delegate.write_ordered(locator, bundle)
        return replace(stored, bundle_digest=digest_of({"wrong": "ordered"}))


class StructureReadBundleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.database = SqliteDatabase()
        self.ids = SequenceIds()
        self.clock = FrozenClock()
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

        self.scopes = KnowledgeScopeService(
            SqliteKnowledgeScopeRepository(self.database, id_generator=self.ids),
            clock=self.clock,
        )
        scope = self.scopes.create_scope(
            scope_type=ScopeType.SYSTEM,
            metadata={"display_name": "Structure Bundle fixture"},
            idempotency_key=IdempotencyKey("structure-bundle-scope"),
            actor="test",
            reason="Structure Bundle tests",
            correlation_ref=CorrelationRef("structure-bundle-tests"),
        )
        self.scope = scope.scope_id
        self.scope_revision = scope.definition_revision
        self.binding = StableId("binding_" + "2" * 32)
        self.schema_ref = "TEST-STRUCTURE@1"
        self.schema_digest = digest_of({"schema": self.schema_ref})

        excerpt = "SENSITIVE-POM-OBSERVATION"
        evidence = StructureEvidence.create(
            artifact_id=StableId("source_artifact_" + "3" * 32),
            source_context_id=StableId("source_context_" + "4" * 32),
            byte_start=0,
            byte_end=len(excerpt.encode("utf-8")),
            locator="pom.xml:1",
            excerpt=excerpt,
            artifact_content_digest=digest_of({"artifact": "pom.xml"}),
        )
        self.evidence_excerpt = excerpt
        self.metadata = StructureEvidenceMetadata.from_evidence(evidence)
        self.entity_root = EntityRoot.software_system(
            owning_scope_id=self.scope,
            canonical_system_key="https://example.invalid/mall.git",
        )
        self.coverage_root = CoverageRoot.create(
            owning_scope_id=self.scope,
            source_binding_id=self.binding,
            logical_reactor_root="pom.xml",
            profile_ref="TEST-STRUCTURE-PROFILE@1",
            schema_ref=self.schema_ref,
            schema_digest=self.schema_digest,
            maven_evaluation_context_ref="TEST-MAVEN-EVALUATION@1",
            maven_evaluation_context_digest=digest_of({"evaluation": 1}),
            canonicalization_ref="TEST-MAVEN-CANONICALIZATION@1",
            canonicalization_digest=digest_of({"canonicalization": 1}),
            coverage_root_ref="TEST-STRUCTURE-COVERAGE@1",
        )

        self.a = self._snapshot(marker="a", revision=Revision(1))
        self.b = self._snapshot(
            marker="b",
            revision=Revision(2),
            previous_snapshot_id=self.a[0].snapshot_id,
        )
        self.source = FakeStructureBundleSource()
        self.source.add(*self.a, self.metadata)
        self.source.add(*self.b, self.metadata, current=True)

        self.session_repository = SqliteStructureReadSessionRepository(
            self.database,
            id_generator=self.ids,
        )
        self.sessions = StructureReadSessionService(
            self.session_repository,
            self.source,
            self.scopes,
            StructureContextComparisonService(),
            clock=self.clock,
        )
        self.repository = SqliteStructureReadBundleRepository(
            self.database,
            id_generator=self.ids,
        )
        self.files = FileStructureReadBundleStore()
        self.service = StructureReadBundleService(
            self.repository,
            self.files,
            self.source,
            self.sessions,
            clock=self.clock,
        )

    def tearDown(self) -> None:
        self.database.close()
        self.temp.cleanup()

    def _snapshot(
        self,
        *,
        marker: str,
        revision: Revision,
        previous_snapshot_id: StableId | None = None,
    ) -> tuple[StructureSnapshot, CoverageRecord, EntityRecord]:
        entity_state = EntityState.create(
            root=self.entity_root,
            state_payload_fields={
                "label": f"mall-{marker}",
                "effective_group_id": "com.example",
                "artifact_id": "mall",
                "effective_version": f"{revision.value}.0.0",
                "packaging": "pom",
                "source_binding_id": self.binding,
                "source_revision": f"revision-{marker}",
                "root_pom_locator": "pom.xml",
                "evidence_references": (self.metadata.evidence_id,),
            },
        )
        entity = EntityRecord(self.entity_root, entity_state)
        manifest = CompleteMemberManifest.create((entity.coverage_member,))
        coverage_state = CoverageState.create(
            root=self.coverage_root,
            source_revision=f"revision-{marker}",
            knowledge_context_digest=digest_of({"revision": marker}),
            complete_member_manifest=manifest,
            evidence_references=(self.metadata.evidence_id,),
        )
        coverage = CoverageRecord(self.coverage_root, coverage_state)
        snapshot = StructureSnapshot.create(
            snapshot_id=StableId("structure_snapshot_" + marker * 32),
            scope_id=self.scope,
            snapshot_revision=revision,
            previous_snapshot_id=previous_snapshot_id,
            schema_ref=self.schema_ref,
            schema_digest=self.schema_digest,
            schema_adoption_mode=(
                StructureSchemaAdoptionMode.INITIAL
                if previous_snapshot_id is None
                else StructureSchemaAdoptionMode.UNCHANGED
            ),
            schema_registration_digest=digest_of({"registration": self.schema_ref}),
            schema_availability_digest=digest_of({"availability": self.schema_ref}),
            schema_adoption_digest=digest_of(
                {"adoption": self.scope.value, "schema": self.schema_ref}
            ),
            publication_mode=PublicationMode.REPLACE_COVERAGE,
            members=(entity.coverage_member,),
            coverages=(
                SnapshotCoverage(
                    coverage_root_id=coverage.root_id,
                    coverage_state_id=coverage.state_id,
                    coverage_state_digest=coverage.state.state_digest,
                ),
            ),
            upstream_entities=(),
            published_at=datetime(
                2026,
                8,
                10,
                10,
                revision.value,
                tzinfo=timezone.utc,
            ),
        )
        return snapshot, coverage, entity

    def _destination(self, name: str) -> str:
        return str(self.root / name)

    def _build_a(self, *, key: str = "bundle-a", name: str = "a.json"):
        return self.service.build_snapshot(
            snapshot_id=self.a[0].snapshot_id,
            idempotency_key=IdempotencyKey(key),
            destination=self._destination(name),
        )

    def _comparison_session(self):
        return self.sessions.open_ordered(
            scope_id=self.scope,
            scope_revision=self.scope_revision,
            task_boundary=TaskBoundary.create(
                task_id=StableId("task_" + "9" * 32),
                task_revision=Revision(1),
                scope_id=self.scope,
                purpose=StructureReadPurpose.SNAPSHOT_COMPARISON.value,
                classification="INTERNAL",
            ),
            caller_ref="structure-bundle-test",
            snapshot_ids=(self.b[0].snapshot_id, self.a[0].snapshot_id),
            idempotency_key=IdempotencyKey("bundle-comparison-session"),
        )

    @staticmethod
    def _reason(error: DomainError) -> str:
        return str(error.details.get("reason_code", ""))

    def test_snapshot_bundle_round_trip_is_byte_stable_and_has_no_payload(self) -> None:
        first = self._build_a()
        first_bytes = Path(first.stored_bundle.locator).read_bytes()
        replay = self._build_a()
        second = self._build_a(key="bundle-a-copy", name="a-copy.json")
        second_bytes = Path(second.stored_bundle.locator).read_bytes()

        self.assertEqual(replay, first)
        self.assertEqual(second_bytes, first_bytes)
        self.assertEqual(second.stored_bundle.bundle_digest, first.stored_bundle.bundle_digest)
        loaded, file_digest = self.files.read_snapshot(first.stored_bundle.locator)
        self.assertEqual(loaded.snapshot, self.a[0])
        self.assertEqual(loaded.entities, (self.a[2],))
        self.assertEqual(loaded.evidence_metadata, (self.metadata,))
        self.assertEqual(file_digest, first.stored_bundle.file_digest)
        self.assertNotIn(self.evidence_excerpt.encode("utf-8"), first_bytes)

        document = json.loads(first_bytes)
        all_keys: set[str] = set()

        def collect(value: object) -> None:
            if isinstance(value, dict):
                all_keys.update(value)
                for nested in value.values():
                    collect(nested)
            elif isinstance(value, list):
                for nested in value:
                    collect(nested)

        collect(document)
        self.assertFalse(
            {"excerpt", "observation", "artifact_bytes", "source_bytes", "provider_input"}
            & all_keys
        )
        self.assertIn("excerpt_digest", all_keys)
        self.assertEqual(
            self.service.availability(self.a[0].snapshot_id).status,
            StructureReadBundleAvailabilityStatus.AVAILABLE,
        )

    def test_receipt_is_required_even_when_an_unreceipted_file_exists(self) -> None:
        receipt = self._build_a()
        empty_database = SqliteDatabase()
        try:
            service = StructureReadBundleService(
                SqliteStructureReadBundleRepository(empty_database),
                self.files,
                self.source,
                self.sessions,
                clock=self.clock,
            )
            availability = service.availability(self.a[0].snapshot_id)
        finally:
            empty_database.close()
        self.assertTrue(Path(receipt.stored_bundle.locator).is_file())
        self.assertEqual(
            availability.status,
            StructureReadBundleAvailabilityStatus.UNAVAILABLE,
        )
        self.assertEqual(availability.reason_code, "READ_BUNDLE_RECEIPT_NOT_FOUND")

    def test_file_failure_creates_no_receipt_and_does_not_change_snapshot(self) -> None:
        original = self.source.get_snapshot(self.a[0].snapshot_id)
        service = StructureReadBundleService(
            self.repository,
            FailingFileStore(),
            self.source,
            self.sessions,
            clock=self.clock,
        )
        with self.assertRaises(OSError):
            service.build_snapshot(
                snapshot_id=self.a[0].snapshot_id,
                idempotency_key=IdempotencyKey("failed-bundle"),
                destination=self._destination("failed.json"),
            )
        self.assertIsNone(self.repository.latest_snapshot(self.a[0].snapshot_id))
        self.assertIs(self.source.get_snapshot(self.a[0].snapshot_id), original)

    def test_replay_restores_a_deleted_disposable_file_exactly(self) -> None:
        receipt = self._build_a()
        path = Path(receipt.stored_bundle.locator)
        original = path.read_bytes()
        path.unlink()

        replay = self._build_a()

        self.assertEqual(replay, receipt)
        self.assertEqual(path.read_bytes(), original)

    def test_idempotency_key_rejects_a_different_destination(self) -> None:
        self._build_a()
        with self.assertRaises(DomainError) as raised:
            self._build_a(name="different.json")
        self.assertEqual(raised.exception.code, ErrorCode.IDEMPOTENCY_MISMATCH)

    def test_ordered_envelope_requires_receipts_and_preserves_session_order(self) -> None:
        session = self._comparison_session()
        with self.assertRaises(DomainError) as raised:
            self.service.build_ordered(
                session_id=session.session_id,
                idempotency_key=IdempotencyKey("ordered-missing"),
                destination=self._destination("ordered-missing.json"),
            )
        self.assertEqual(
            self._reason(raised.exception),
            "READ_BUNDLE_SNAPSHOT_RECEIPT_REQUIRED",
        )

        receipt_a = self._build_a()
        receipt_b = self.service.build_snapshot(
            snapshot_id=self.b[0].snapshot_id,
            idempotency_key=IdempotencyKey("bundle-b"),
            destination=self._destination("b.json"),
        )
        ordered_receipt = self.service.build_ordered(
            session_id=session.session_id,
            idempotency_key=IdempotencyKey("ordered-complete"),
            destination=self._destination("ordered.json"),
        )
        ordered, _ = self.files.read_ordered(ordered_receipt.stored_bundle.locator)

        self.assertEqual(
            tuple(item.snapshot_id for item in ordered.snapshots),
            (self.b[0].snapshot_id, self.a[0].snapshot_id),
        )
        ordered.verify_snapshot_bundles(
            (
                self.files.read_snapshot(receipt_b.stored_bundle.locator),
                self.files.read_snapshot(receipt_a.stored_bundle.locator),
            )
        )

    def test_ordered_envelope_seals_pre_question_discovery_recall_binding(self) -> None:
        session = self._comparison_session()
        receipt_a = self._build_a()
        receipt_b = self.service.build_snapshot(
            snapshot_id=self.b[0].snapshot_id,
            idempotency_key=IdempotencyKey("bundle-b-discovery"),
            destination=self._destination("b-discovery.json"),
        )
        bundle_b, _ = self.files.read_snapshot(receipt_b.stored_bundle.locator)
        binding = StructureBusinessDiscoveryRecallBinding.create(
            oracle_ref="pre-question-recall-oracle@1",
            oracle_result_digest=digest_of("pre-question-recall-result"),
            profile_ref="TEST-STRUCTURE-PROFILE@1",
            discovery_contract_ref=(
                JAVA_IMPLEMENTATION_FEATURE_DISCOVERY_CONTRACT_REF
            ),
            snapshot_id=bundle_b.snapshot_id,
            snapshot_bundle_digest=bundle_b.digest,
            counterexample_classes=("synonym", "alternate-entry", "naming"),
            verdict=StructureBusinessDiscoveryRecallVerdict.COMPLETE,
        )
        ordered_receipt = self.service.build_ordered(
            session_id=session.session_id,
            idempotency_key=IdempotencyKey("ordered-discovery"),
            destination=self._destination("ordered-discovery.json"),
            business_discovery_recall_bindings=(binding,),
        )

        ordered, _ = self.files.read_ordered(
            ordered_receipt.stored_bundle.locator
        )
        self.assertEqual(
            ordered.format_ref,
            STRUCTURE_ORDERED_READ_BUNDLE_WITH_DISCOVERY_FORMAT,
        )
        self.assertEqual(
            ordered.business_discovery_recall_bindings,
            (binding,),
        )
        ordered.verify_snapshot_bundles(
            (
                self.files.read_snapshot(receipt_b.stored_bundle.locator),
                self.files.read_snapshot(receipt_a.stored_bundle.locator),
            )
        )

        document = json.loads(
            Path(ordered_receipt.stored_bundle.locator).read_bytes()
        )
        document["business_discovery_recall_bindings"][0][
            "oracle_result_digest"
        ] = digest_of("tampered-recall-result").value
        tampered = self.root / "ordered-discovery-tampered.json"
        tampered.write_bytes(canonical_json_bytes(document))
        with self.assertRaises(DomainError) as raised:
            self.files.read_ordered(str(tampered))
        self.assertEqual(
            self._reason(raised.exception),
            "READ_BUNDLE_DISCOVERY_RECALL_BINDING_INVALID",
        )

    def test_ordered_first_write_rejects_store_metadata_before_receipt(self) -> None:
        session = self._comparison_session()
        self._build_a()
        self.service.build_snapshot(
            snapshot_id=self.b[0].snapshot_id,
            idempotency_key=IdempotencyKey("bundle-b-for-fault"),
            destination=self._destination("b-for-fault.json"),
        )
        service = StructureReadBundleService(
            self.repository,
            WrongOrderedReceiptFileStore(self.files),
            self.source,
            self.sessions,
            clock=self.clock,
        )

        with self.assertRaises(DomainError) as raised:
            service.build_ordered(
                session_id=session.session_id,
                idempotency_key=IdempotencyKey("ordered-store-metadata-fault"),
                destination=self._destination("ordered-store-metadata-fault.json"),
            )

        self.assertEqual(
            raised.exception.code,
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
        )
        with self.database.read() as connection:
            ordered_count = connection.execute(
                """SELECT COUNT(*) AS count
                   FROM app_structure_read_bundle_receipts
                   WHERE bundle_kind = 'ORDERED_READ_SET'"""
            ).fetchone()["count"]
        self.assertEqual(ordered_count, 0)

    def test_ordered_envelope_rejects_full_coverage_binding_mismatch(self) -> None:
        receipt = self._build_a()
        bundle, file_digest = self.files.read_snapshot(
            receipt.stored_bundle.locator
        )
        session = self.sessions.open_ordered(
            scope_id=self.scope,
            scope_revision=self.scope_revision,
            task_boundary=TaskBoundary.create(
                task_id=StableId("task_" + "8" * 32),
                task_revision=Revision(1),
                scope_id=self.scope,
                purpose=StructureReadPurpose.EXACT_SNAPSHOT.value,
                classification="INTERNAL",
            ),
            caller_ref="structure-bundle-binding-fault",
            snapshot_ids=(self.a[0].snapshot_id,),
            idempotency_key=IdempotencyKey("bundle-binding-fault-session"),
        )
        forged_coverage = CoverageRecord(
            self.a[1].root,
            CoverageState.create(
                root=self.a[1].root,
                source_revision="forged-revision",
                knowledge_context_digest=digest_of({"forged": True}),
                complete_member_manifest=(
                    self.a[1].state.complete_member_manifest
                ),
                evidence_references=self.a[1].state.evidence_references,
            ),
        )
        forged_binding = StructureSnapshotReadBinding.create(
            snapshot=self.a[0],
            coverages=(StructureCoverageReadBinding.from_record(forged_coverage),),
        )
        forged_read_set = structure_ordered_read_set_digest(
            (forged_binding,), ()
        )
        forged_session = replace(
            session,
            snapshots=(forged_binding,),
            read_set_digest=forged_read_set,
            digest=structure_read_session_digest(
                session_id=session.session_id,
                request_digest=session.request_digest,
                scope_id=session.scope_id,
                scope_revision=session.scope_revision,
                task_boundary=session.task_boundary,
                scope_assertion=session.scope_assertion,
                caller_ref=session.caller_ref,
                purpose=session.purpose,
                selection_mode=session.selection_mode,
                order=session.order,
                read_set_digest=forged_read_set,
                opened_at=session.opened_at,
            ),
        )
        envelope = StructureOrderedReadBundle.create(
            session=forged_session,
            snapshots=(
                StructureSnapshotBundleReference(
                    ordinal=0,
                    snapshot_id=bundle.snapshot_id,
                    snapshot_binding_digest=forged_binding.digest,
                    snapshot_manifest_digest=bundle.snapshot.manifest_digest,
                    bundle_digest=bundle.digest,
                    file_digest=file_digest,
                ),
            ),
        )

        with self.assertRaises(DomainError) as raised:
            envelope.verify_snapshot_bundles(((bundle, file_digest),))

        self.assertEqual(
            self._reason(raised.exception),
            "READ_BUNDLE_LOADED_REFERENCE_MISMATCH",
        )

    def test_strict_file_reader_rejects_duplicate_unknown_and_noncanonical_json(self) -> None:
        receipt = self._build_a()
        original = Path(receipt.stored_bundle.locator).read_bytes()
        document = json.loads(original)

        duplicate = self.root / "duplicate.json"
        duplicate.write_bytes(b'{"format_ref":"duplicate",' + original[1:])
        with self.assertRaises(DomainError) as raised_duplicate:
            self.files.read_snapshot(str(duplicate))
        self.assertEqual(
            self._reason(raised_duplicate.exception),
            "READ_BUNDLE_JSON_INVALID",
        )

        document["unknown_field"] = "forbidden"
        unknown = self.root / "unknown.json"
        unknown.write_bytes(canonical_json_bytes(document))
        with self.assertRaises(DomainError) as raised_unknown:
            self.files.read_snapshot(str(unknown))
        self.assertEqual(
            self._reason(raised_unknown.exception),
            "READ_BUNDLE_FIELD_SET_INVALID",
        )

        noncanonical = self.root / "noncanonical.json"
        noncanonical.write_bytes(original + b"\n")
        with self.assertRaises(DomainError) as raised_noncanonical:
            self.files.read_snapshot(str(noncanonical))
        self.assertEqual(
            self._reason(raised_noncanonical.exception),
            "READ_BUNDLE_JSON_NONCANONICAL",
        )

    def test_strict_file_reader_rejects_digest_tamper_and_symlinks(self) -> None:
        receipt = self._build_a()
        original_path = Path(receipt.stored_bundle.locator)
        document = json.loads(original_path.read_bytes())
        document["bundle_digest"] = digest_of({"tampered": True}).value
        tampered = self.root / "tampered.json"
        tampered.write_bytes(canonical_json_bytes(document))
        with self.assertRaises(DomainError) as raised_tamper:
            self.files.read_snapshot(str(tampered))
        self.assertEqual(
            self._reason(raised_tamper.exception),
            "READ_BUNDLE_DIGEST_MISMATCH",
        )

        symlink = self.root / "symlink.json"
        symlink.symlink_to(original_path)
        with self.assertRaises(DomainError) as raised_symlink:
            self.files.read_snapshot(str(symlink))
        self.assertEqual(
            self._reason(raised_symlink.exception),
            "READ_BUNDLE_SYMLINK_FORBIDDEN",
        )

    def test_strict_file_reader_rejects_alternate_typed_time_encoding(self) -> None:
        receipt = self._build_a()
        document = json.loads(Path(receipt.stored_bundle.locator).read_bytes())
        canonical_time = document["snapshot"]["published_at"]
        self.assertTrue(canonical_time.endswith(".000000Z"))
        document["snapshot"]["published_at"] = canonical_time.replace(
            ".000000Z", "Z"
        )
        alternate = self.root / "alternate-time.json"
        alternate.write_bytes(canonical_json_bytes(document))

        with self.assertRaises(DomainError) as raised:
            self.files.read_snapshot(str(alternate))

        self.assertEqual(
            self._reason(raised.exception),
            "READ_BUNDLE_DOCUMENT_NONCANONICAL",
        )

    def test_typed_bundle_requires_exact_evidence_metadata_closure(self) -> None:
        receipt = self._build_a()
        bundle, _ = self.files.read_snapshot(receipt.stored_bundle.locator)
        missing = replace(bundle, evidence_metadata=())
        with self.assertRaises(DomainError) as raised:
            missing.require_valid()
        self.assertEqual(
            self._reason(raised.exception),
            "READ_BUNDLE_SUPPORT_METADATA_MISMATCH",
        )

    def test_persisted_receipt_tamper_fails_closed(self) -> None:
        receipt = self._build_a()
        with self.database.transaction() as connection:
            connection.execute(
                """UPDATE app_structure_read_bundle_receipts
                   SET bundle_locator = ? WHERE receipt_id = ?""",
                (self._destination("other.json"), receipt.receipt_id.value),
            )
        with self.assertRaises(DomainError) as raised:
            self.service.get_receipt(receipt.receipt_id)
        self.assertEqual(
            raised.exception.code,
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
        )

    def test_persisted_idempotency_key_tamper_fails_closed(self) -> None:
        receipt = self._build_a()
        forged = IdempotencyKey("forged-bundle-idempotency-key")
        with self.database.transaction() as connection:
            connection.execute(
                """UPDATE app_structure_read_bundle_receipts
                   SET idempotency_key = ? WHERE receipt_id = ?""",
                (forged.value, receipt.receipt_id.value),
            )

        with self.assertRaises(DomainError) as loaded:
            self.repository.get(receipt.receipt_id)
        self.assertEqual(
            loaded.exception.code,
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
        )
        with self.assertRaises(DomainError) as replayed:
            self.repository.replay(
                idempotency_key=forged,
                request_digest=receipt.request_digest,
            )
        self.assertEqual(
            replayed.exception.code,
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
        )

    def test_receipt_persistence_has_no_payload_columns(self) -> None:
        self._build_a()
        with self.database.read() as connection:
            columns = {
                row["name"]
                for table in (
                    "app_structure_read_bundle_receipts",
                    "app_structure_read_bundle_receipt_snapshots",
                )
                for row in connection.execute(f"PRAGMA table_info({table})")
            }
        self.assertFalse(
            {"excerpt", "observation", "artifact_bytes", "source_bytes", "provider_input"}
            & columns
        )


if __name__ == "__main__":
    unittest.main()
