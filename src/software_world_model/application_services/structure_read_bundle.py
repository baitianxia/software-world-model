"""Post-publication, no-payload read bundles for Structure Snapshots.

The bundle is a deterministic, disposable read copy of already committed
Structure knowledge.  It deliberately owns neither Snapshot membership nor
CURRENT.  Application-owned receipts are persisted separately and are the
only way a connected runtime may advertise a Snapshot as available for an
isolated read.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Callable, Protocol

from software_world_model.application_services.structure_read_session import (
    StructureCoverageReadBinding,
    StructureReadSession,
    StructureSnapshotReadBinding,
)
from software_world_model.cross_cutting import (
    Digest,
    DomainError,
    ErrorCode,
    IdempotencyKey,
    StableId,
    digest_of,
)
from software_world_model.knowledge_engine.structure import (
    CanonicalFields,
    CoverageMember,
    CoverageMemberKind,
    CoverageRecord,
    EntityRecord,
    EntityRef,
    LiteralFactRecord,
    RelationFactRecord,
)
from software_world_model.knowledge_engine.structure_publication import (
    StructureEvidenceMetadata,
    StructureSnapshot,
    structure_snapshot_manifest_digest,
)


STRUCTURE_SNAPSHOT_READ_BUNDLE_FORMAT = "STRUCTURE_SNAPSHOT_READ_BUNDLE@1"
STRUCTURE_ORDERED_READ_BUNDLE_FORMAT = "STRUCTURE_ORDERED_READ_BUNDLE@1"


class StructureReadBundleKind(str, Enum):
    SNAPSHOT = "SNAPSHOT"
    ORDERED_READ_SET = "ORDERED_READ_SET"


class StructureReadBundleAvailabilityStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True, slots=True)
class StructureBundleUpstreamEntityRecord:
    snapshot_id: StableId
    entity: EntityRecord

    def require_valid(self) -> None:
        if self.snapshot_id.kind != "structure_snapshot":
            raise _invalid(
                "READ_BUNDLE_UPSTREAM_SNAPSHOT_KIND_INVALID",
                "Bundle upstream Entity requires an exact Structure Snapshot ID",
            )
        if not isinstance(self.entity, EntityRecord):
            raise _invalid(
                "READ_BUNDLE_UPSTREAM_ENTITY_REQUIRED",
                "Bundle upstream Entity must be a typed Entity record",
            )
        self.entity.root.require_valid_identity()
        self.entity.state.require_valid_identity()


@dataclass(frozen=True, slots=True)
class StructureSnapshotReadBundle:
    """Canonical no-payload copy of one committed exact Snapshot."""

    snapshot: StructureSnapshot
    coverages: tuple[CoverageRecord, ...]
    entities: tuple[EntityRecord, ...]
    relation_facts: tuple[RelationFactRecord, ...]
    literal_facts: tuple[LiteralFactRecord, ...]
    upstream_entity_records: tuple[StructureBundleUpstreamEntityRecord, ...]
    evidence_metadata: tuple[StructureEvidenceMetadata, ...]
    digest: Digest
    format_ref: str = STRUCTURE_SNAPSHOT_READ_BUNDLE_FORMAT

    @classmethod
    def create(
        cls,
        *,
        snapshot: StructureSnapshot,
        coverages: tuple[CoverageRecord, ...],
        entities: tuple[EntityRecord, ...],
        relation_facts: tuple[RelationFactRecord, ...],
        literal_facts: tuple[LiteralFactRecord, ...],
        upstream_entity_records: tuple[StructureBundleUpstreamEntityRecord, ...],
        evidence_metadata: tuple[StructureEvidenceMetadata, ...],
    ) -> "StructureSnapshotReadBundle":
        normalized_coverages = tuple(
            sorted(coverages, key=lambda item: item.root_id.value)
        )
        normalized_entities = tuple(
            sorted(entities, key=lambda item: item.root_id.value)
        )
        normalized_relations = tuple(
            sorted(relation_facts, key=lambda item: item.root_id.value)
        )
        normalized_literals = tuple(
            sorted(literal_facts, key=lambda item: item.root_id.value)
        )
        normalized_upstream = tuple(
            sorted(
                upstream_entity_records,
                key=lambda item: (
                    item.entity.root_id.value,
                    item.snapshot_id.value,
                ),
            )
        )
        normalized_evidence = tuple(
            sorted(evidence_metadata, key=lambda item: item.evidence_id.value)
        )
        core = structure_snapshot_read_bundle_core(
            snapshot=snapshot,
            coverages=normalized_coverages,
            entities=normalized_entities,
            relation_facts=normalized_relations,
            literal_facts=normalized_literals,
            upstream_entity_records=normalized_upstream,
            evidence_metadata=normalized_evidence,
        )
        value = cls(
            snapshot=snapshot,
            coverages=normalized_coverages,
            entities=normalized_entities,
            relation_facts=normalized_relations,
            literal_facts=normalized_literals,
            upstream_entity_records=normalized_upstream,
            evidence_metadata=normalized_evidence,
            digest=digest_of([STRUCTURE_SNAPSHOT_READ_BUNDLE_FORMAT, core]),
        )
        value.require_valid()
        return value

    @property
    def snapshot_id(self) -> StableId:
        return self.snapshot.snapshot_id

    @property
    def scope_id(self) -> StableId:
        return self.snapshot.scope_id

    def canonical_core(self) -> dict[str, object]:
        return structure_snapshot_read_bundle_core(
            snapshot=self.snapshot,
            coverages=self.coverages,
            entities=self.entities,
            relation_facts=self.relation_facts,
            literal_facts=self.literal_facts,
            upstream_entity_records=self.upstream_entity_records,
            evidence_metadata=self.evidence_metadata,
        )

    def document(self) -> dict[str, object]:
        return {
            **self.canonical_core(),
            "bundle_digest": self.digest.value,
        }

    def require_valid(self) -> None:
        if self.format_ref != STRUCTURE_SNAPSHOT_READ_BUNDLE_FORMAT:
            raise _invalid(
                "READ_BUNDLE_FORMAT_UNSUPPORTED",
                "Structure Snapshot Bundle format is not supported",
            )
        if not isinstance(self.snapshot, StructureSnapshot):
            raise _invalid(
                "READ_BUNDLE_SNAPSHOT_REQUIRED",
                "Structure Snapshot Bundle requires a typed Snapshot",
            )
        if self.snapshot.manifest_digest != structure_snapshot_manifest_digest(
            self.snapshot
        ):
            raise _inconsistent(
                "Structure Snapshot Bundle binds a non-canonical Snapshot manifest"
            )
        _require_sorted_unique_records(self.coverages, "Coverage")
        _require_sorted_unique_records(self.entities, "Entity")
        _require_sorted_unique_records(self.relation_facts, "Relation Fact")
        _require_sorted_unique_records(self.literal_facts, "Literal Fact")
        expected_upstream = tuple(
            sorted(
                self.upstream_entity_records,
                key=lambda item: (
                    item.entity.root_id.value,
                    item.snapshot_id.value,
                ),
            )
        )
        if self.upstream_entity_records != expected_upstream or len(
            {item.entity.root_id for item in self.upstream_entity_records}
        ) != len(self.upstream_entity_records):
            raise _invalid(
                "READ_BUNDLE_UPSTREAM_SET_INVALID",
                "Bundle upstream Entity records must be sorted and unambiguous",
            )
        for item in self.upstream_entity_records:
            item.require_valid()
        expected_evidence = tuple(
            sorted(self.evidence_metadata, key=lambda item: item.evidence_id.value)
        )
        if self.evidence_metadata != expected_evidence or len(
            {item.evidence_id for item in self.evidence_metadata}
        ) != len(self.evidence_metadata):
            raise _invalid(
                "READ_BUNDLE_EVIDENCE_METADATA_SET_INVALID",
                "Bundle Evidence metadata must be sorted and unique",
            )
        for item in self.evidence_metadata:
            _require_valid_evidence_metadata(item)

        members_by_kind = {
            CoverageMemberKind.ENTITY: {
                item.root_id: item for item in self.entities
            },
            CoverageMemberKind.RELATION_FACT: {
                item.root_id: item for item in self.relation_facts
            },
            CoverageMemberKind.LITERAL_FACT: {
                item.root_id: item for item in self.literal_facts
            },
        }
        expected_member_keys = {
            (item.kind, item.root_id): item for item in self.snapshot.members
        }
        actual_member_keys: dict[
            tuple[CoverageMemberKind, StableId], CoverageMember
        ] = {}
        for kind, records in members_by_kind.items():
            for record in records.values():
                if record.coverage_member.kind is not kind:
                    raise _inconsistent(
                        "Bundle record kind differs from its typed member"
                    )
                actual_member_keys[(kind, record.root_id)] = record.coverage_member
                _require_local_record_boundary(
                    record,
                    scope_id=self.snapshot.scope_id,
                    schema_ref=self.snapshot.schema_ref,
                )
        if actual_member_keys != expected_member_keys:
            raise _invalid(
                "READ_BUNDLE_MEMBER_MANIFEST_MISMATCH",
                "Bundle typed records do not exactly match the Snapshot Manifest",
            )

        snapshot_coverages = {
            item.coverage_root_id: item for item in self.snapshot.coverages
        }
        bundle_coverages = {item.root_id: item for item in self.coverages}
        if set(snapshot_coverages) != set(bundle_coverages):
            raise _invalid(
                "READ_BUNDLE_COVERAGE_SET_MISMATCH",
                "Bundle Coverage records do not exactly match the Snapshot",
            )
        ownership: dict[StableId, StableId] = {}
        for root_id, record in bundle_coverages.items():
            binding = snapshot_coverages[root_id]
            if (
                record.state_id != binding.coverage_state_id
                or record.state.state_digest != binding.coverage_state_digest
                or record.root.owning_scope_id != self.snapshot.scope_id
                or record.root.schema_ref != self.snapshot.schema_ref
            ):
                raise _invalid(
                    "READ_BUNDLE_COVERAGE_BINDING_MISMATCH",
                    "Bundle Coverage record differs from its exact Snapshot binding",
                )
            record.root.require_valid_identity()
            record.state.require_valid_identity(record.root)
            for member in record.state.complete_member_manifest.members:
                existing = ownership.get(member.root_id)
                if existing is not None and existing != root_id:
                    raise _invalid(
                        "READ_BUNDLE_COVERAGE_OVERLAP",
                        "Bundle Coverage ownership overlaps",
                    )
                if expected_member_keys.get((member.kind, member.root_id)) != member:
                    raise _invalid(
                        "READ_BUNDLE_COVERAGE_MEMBER_MISMATCH",
                        "Coverage Manifest is not an exact subset of the Snapshot",
                    )
                ownership[member.root_id] = root_id
        if set(ownership) != {item.root_id for item in self.snapshot.members}:
            raise _invalid(
                "READ_BUNDLE_COVERAGE_OWNERSHIP_INCOMPLETE",
                "Bundle Coverage does not own every exact Snapshot member",
            )

        local_entities = {item.root_id: item for item in self.entities}
        upstream_entities = {
            item.entity.root_id: item for item in self.upstream_entity_records
        }
        if set(local_entities) & set(upstream_entities):
            raise _invalid(
                "READ_BUNDLE_UPSTREAM_LOCAL_OVERLAP",
                "Bundle Entity cannot be both a local member and an upstream endpoint",
            )
        expected_upstream_bindings = tuple(
            sorted(
                (
                    (
                        item.entity.root_id,
                        item.snapshot_id,
                        item.entity.state_id,
                        item.entity.state_digest,
                    )
                    for item in self.upstream_entity_records
                ),
                key=lambda item: (item[0].value, item[1].value),
            )
        )
        actual_upstream_bindings = tuple(
            (
                item.entity_root_id,
                item.upstream_snapshot_id,
                item.entity_state_id,
                item.entity_state_digest,
            )
            for item in self.snapshot.upstream_entities
        )
        if expected_upstream_bindings != actual_upstream_bindings:
            raise _invalid(
                "READ_BUNDLE_UPSTREAM_MANIFEST_MISMATCH",
                "Bundle upstream records differ from the Snapshot upstream Manifest",
            )
        for relation in self.relation_facts:
            _require_endpoint(
                relation.root.subject,
                relation.state.subject_entity_state_id,
                local_entities,
                upstream_entities,
            )
            _require_endpoint(
                relation.root.object,
                relation.state.object_entity_state_id,
                local_entities,
                upstream_entities,
            )
        for literal in self.literal_facts:
            _require_endpoint(
                literal.root.subject,
                literal.state.subject_entity_state_id,
                local_entities,
                upstream_entities,
            )

        evidence_ids = {item.evidence_id for item in self.evidence_metadata}
        required_evidence: set[StableId] = set()
        for record in (*self.entities, *self.upstream_entity_records):
            entity = record.entity if isinstance(record, StructureBundleUpstreamEntityRecord) else record
            required_evidence.update(entity.state.evidence_references)
        for record in self.relation_facts:
            required_evidence.update(record.state.evidence_references)
        for record in self.literal_facts:
            required_evidence.update(record.state.evidence_references)
        for record in self.coverages:
            required_evidence.update(record.state.evidence_references)
        if evidence_ids != required_evidence:
            raise _invalid(
                "READ_BUNDLE_SUPPORT_METADATA_MISMATCH",
                "Bundle Evidence metadata is not the exact Support closure",
            )

        expected_digest = digest_of(
            [STRUCTURE_SNAPSHOT_READ_BUNDLE_FORMAT, self.canonical_core()]
        )
        if self.digest != expected_digest:
            raise _invalid(
                "READ_BUNDLE_DIGEST_MISMATCH",
                "Structure Snapshot Bundle digest is not canonical",
            )


@dataclass(frozen=True, slots=True)
class StructureSnapshotBundleReference:
    ordinal: int
    snapshot_id: StableId
    snapshot_binding_digest: Digest
    snapshot_manifest_digest: Digest
    bundle_digest: Digest
    file_digest: Digest

    def require_valid(self) -> None:
        if type(self.ordinal) is not int or self.ordinal < 0:
            raise _invalid(
                "READ_BUNDLE_ORDINAL_INVALID",
                "ordered Bundle reference ordinal must be non-negative",
            )
        if self.snapshot_id.kind != "structure_snapshot":
            raise _invalid(
                "READ_BUNDLE_SNAPSHOT_ID_INVALID",
                "ordered Bundle reference requires a Structure Snapshot ID",
            )
        for value in (
            self.snapshot_binding_digest,
            self.snapshot_manifest_digest,
            self.bundle_digest,
            self.file_digest,
        ):
            if not isinstance(value, Digest):
                raise _invalid(
                    "READ_BUNDLE_REFERENCE_DIGEST_REQUIRED",
                    "ordered Bundle reference requires typed digests",
                )


@dataclass(frozen=True, slots=True)
class StructureOrderedReadBundle:
    """Exact caller-ordered Bundle set bound to one persisted read Session."""

    session: StructureReadSession
    snapshots: tuple[StructureSnapshotBundleReference, ...]
    digest: Digest
    format_ref: str = STRUCTURE_ORDERED_READ_BUNDLE_FORMAT

    @classmethod
    def create(
        cls,
        *,
        session: StructureReadSession,
        snapshots: tuple[StructureSnapshotBundleReference, ...],
    ) -> "StructureOrderedReadBundle":
        core = structure_ordered_read_bundle_core(
            session=session,
            snapshots=snapshots,
        )
        value = cls(
            session=session,
            snapshots=snapshots,
            digest=digest_of([STRUCTURE_ORDERED_READ_BUNDLE_FORMAT, core]),
        )
        value.require_valid()
        return value

    def canonical_core(self) -> dict[str, object]:
        return structure_ordered_read_bundle_core(
            session=self.session,
            snapshots=self.snapshots,
        )

    def document(self) -> dict[str, object]:
        return {**self.canonical_core(), "bundle_digest": self.digest.value}

    def require_valid(self) -> None:
        if self.format_ref != STRUCTURE_ORDERED_READ_BUNDLE_FORMAT:
            raise _invalid(
                "READ_BUNDLE_FORMAT_UNSUPPORTED",
                "ordered Structure Bundle format is not supported",
            )
        if not isinstance(self.session, StructureReadSession):
            raise _invalid(
                "READ_BUNDLE_SESSION_REQUIRED",
                "ordered Structure Bundle requires a typed read Session",
            )
        self.session.require_valid()
        if len(self.snapshots) != len(self.session.snapshots):
            raise _invalid(
                "READ_BUNDLE_ORDERED_SET_SIZE_MISMATCH",
                "ordered Bundle references do not cover the exact read set",
            )
        for ordinal, (reference, binding) in enumerate(
            zip(self.snapshots, self.session.snapshots)
        ):
            reference.require_valid()
            if (
                reference.ordinal != ordinal
                or reference.snapshot_id != binding.snapshot_id
                or reference.snapshot_binding_digest != binding.digest
                or reference.snapshot_manifest_digest
                != binding.snapshot_manifest_digest
            ):
                raise _invalid(
                    "READ_BUNDLE_ORDERED_BINDING_MISMATCH",
                    "ordered Bundle reference differs from its exact Session binding",
                )
        if len({item.snapshot_id for item in self.snapshots}) != len(self.snapshots):
            raise _invalid(
                "READ_BUNDLE_ORDERED_SET_DUPLICATE",
                "ordered Bundle cannot repeat a Snapshot",
            )
        expected_digest = digest_of(
            [STRUCTURE_ORDERED_READ_BUNDLE_FORMAT, self.canonical_core()]
        )
        if self.digest != expected_digest:
            raise _invalid(
                "READ_BUNDLE_DIGEST_MISMATCH",
                "ordered Structure Bundle digest is not canonical",
            )

    def verify_snapshot_bundles(
        self,
        bundles: tuple[tuple[StructureSnapshotReadBundle, Digest], ...],
    ) -> None:
        """Verify loaded Snapshot Bundles and raw file digests in exact order."""

        self.require_valid()
        if len(bundles) != len(self.snapshots):
            raise _invalid(
                "READ_BUNDLE_LOADED_SET_SIZE_MISMATCH",
                "loaded Snapshot Bundles do not cover the ordered Bundle",
            )
        for reference, binding, (bundle, file_digest) in zip(
            self.snapshots, self.session.snapshots, bundles
        ):
            bundle.require_valid()
            exact_binding = StructureSnapshotReadBinding.create(
                snapshot=bundle.snapshot,
                coverages=tuple(
                    StructureCoverageReadBinding.from_record(item)
                    for item in bundle.coverages
                ),
            )
            if (
                bundle.snapshot_id != reference.snapshot_id
                or bundle.snapshot.manifest_digest
                != reference.snapshot_manifest_digest
                or bundle.digest != reference.bundle_digest
                or file_digest != reference.file_digest
                or exact_binding != binding
            ):
                raise _invalid(
                    "READ_BUNDLE_LOADED_REFERENCE_MISMATCH",
                    "loaded Snapshot Bundle differs from its exact Session binding",
                )


@dataclass(frozen=True, slots=True)
class StoredStructureReadBundle:
    locator: str
    format_ref: str
    bundle_digest: Digest
    file_digest: Digest

    def require_valid(self) -> None:
        _text(self.locator, "Bundle locator")
        if self.format_ref not in {
            STRUCTURE_SNAPSHOT_READ_BUNDLE_FORMAT,
            STRUCTURE_ORDERED_READ_BUNDLE_FORMAT,
        }:
            raise _invalid(
                "READ_BUNDLE_FORMAT_UNSUPPORTED",
                "stored Bundle format is not supported",
            )
        if not isinstance(self.bundle_digest, Digest) or not isinstance(
            self.file_digest, Digest
        ):
            raise _invalid(
                "READ_BUNDLE_STORED_DIGEST_REQUIRED",
                "stored Bundle requires typed semantic and file digests",
            )


@dataclass(frozen=True, slots=True)
class StructureReadBundleReceipt:
    receipt_id: StableId
    idempotency_key: IdempotencyKey
    kind: StructureReadBundleKind
    request_digest: Digest
    scope_id: StableId
    snapshot_ids: tuple[StableId, ...]
    session_id: StableId | None
    read_set_digest: Digest | None
    stored_bundle: StoredStructureReadBundle
    created_at: datetime
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        receipt_id: StableId,
        idempotency_key: IdempotencyKey,
        kind: StructureReadBundleKind,
        request_digest: Digest,
        scope_id: StableId,
        snapshot_ids: tuple[StableId, ...],
        session_id: StableId | None,
        read_set_digest: Digest | None,
        stored_bundle: StoredStructureReadBundle,
        created_at: datetime,
    ) -> "StructureReadBundleReceipt":
        core = structure_read_bundle_receipt_core(
            receipt_id=receipt_id,
            idempotency_key=idempotency_key,
            kind=kind,
            request_digest=request_digest,
            scope_id=scope_id,
            snapshot_ids=snapshot_ids,
            session_id=session_id,
            read_set_digest=read_set_digest,
            stored_bundle=stored_bundle,
            created_at=created_at,
        )
        value = cls(
            receipt_id=receipt_id,
            idempotency_key=idempotency_key,
            kind=kind,
            request_digest=request_digest,
            scope_id=scope_id,
            snapshot_ids=snapshot_ids,
            session_id=session_id,
            read_set_digest=read_set_digest,
            stored_bundle=stored_bundle,
            created_at=created_at,
            digest=digest_of(["STRUCTURE_READ_BUNDLE_RECEIPT@1", core]),
        )
        value.require_valid()
        return value

    def require_valid(self) -> None:
        if self.receipt_id.kind != "read_bundle_receipt":
            raise _invalid(
                "READ_BUNDLE_RECEIPT_ID_INVALID",
                "Bundle Receipt has the wrong ID kind",
            )
        if not isinstance(self.idempotency_key, IdempotencyKey):
            raise _invalid(
                "READ_BUNDLE_RECEIPT_IDEMPOTENCY_KEY_INVALID",
                "Bundle Receipt requires its exact idempotency key binding",
            )
        if not isinstance(self.kind, StructureReadBundleKind):
            raise _invalid(
                "READ_BUNDLE_RECEIPT_KIND_INVALID",
                "Bundle Receipt kind is invalid",
            )
        if self.scope_id.kind != "scope" or not self.snapshot_ids:
            raise _invalid(
                "READ_BUNDLE_RECEIPT_SCOPE_INVALID",
                "Bundle Receipt requires a Scope and exact Snapshot IDs",
            )
        if any(item.kind != "structure_snapshot" for item in self.snapshot_ids):
            raise _invalid(
                "READ_BUNDLE_RECEIPT_SNAPSHOT_INVALID",
                "Bundle Receipt contains a non-Structure Snapshot ID",
            )
        if len(set(self.snapshot_ids)) != len(self.snapshot_ids):
            raise _invalid(
                "READ_BUNDLE_RECEIPT_SNAPSHOT_DUPLICATE",
                "Bundle Receipt cannot repeat a Snapshot",
            )
        if self.created_at.tzinfo is None or self.created_at.utcoffset() is None:
            raise _invalid(
                "READ_BUNDLE_RECEIPT_TIME_INVALID",
                "Bundle Receipt time must include a timezone",
            )
        self.stored_bundle.require_valid()
        if self.kind is StructureReadBundleKind.SNAPSHOT:
            if (
                len(self.snapshot_ids) != 1
                or self.session_id is not None
                or self.read_set_digest is not None
                or self.stored_bundle.format_ref
                != STRUCTURE_SNAPSHOT_READ_BUNDLE_FORMAT
            ):
                raise _invalid(
                    "READ_BUNDLE_SNAPSHOT_RECEIPT_SHAPE_INVALID",
                    "Snapshot Bundle Receipt has an invalid shape",
                )
        else:
            if (
                self.session_id is None
                or self.session_id.kind != "structure_read_session"
                or self.read_set_digest is None
                or self.stored_bundle.format_ref
                != STRUCTURE_ORDERED_READ_BUNDLE_FORMAT
            ):
                raise _invalid(
                    "READ_BUNDLE_ORDERED_RECEIPT_SHAPE_INVALID",
                    "ordered Bundle Receipt has an invalid shape",
                )
        expected = digest_of(
            [
                "STRUCTURE_READ_BUNDLE_RECEIPT@1",
                structure_read_bundle_receipt_core(
                    receipt_id=self.receipt_id,
                    idempotency_key=self.idempotency_key,
                    kind=self.kind,
                    request_digest=self.request_digest,
                    scope_id=self.scope_id,
                    snapshot_ids=self.snapshot_ids,
                    session_id=self.session_id,
                    read_set_digest=self.read_set_digest,
                    stored_bundle=self.stored_bundle,
                    created_at=self.created_at,
                ),
            ]
        )
        if self.digest != expected:
            raise _invalid(
                "READ_BUNDLE_RECEIPT_DIGEST_MISMATCH",
                "Bundle Receipt digest is not canonical",
            )


@dataclass(frozen=True, slots=True)
class StructureReadBundleAvailability:
    snapshot_id: StableId
    status: StructureReadBundleAvailabilityStatus
    receipt: StructureReadBundleReceipt | None
    reason_code: str | None

    def require_valid(self) -> None:
        if self.snapshot_id.kind != "structure_snapshot":
            raise _invalid(
                "READ_BUNDLE_AVAILABILITY_SNAPSHOT_INVALID",
                "Bundle availability requires a Structure Snapshot ID",
            )
        if self.status is StructureReadBundleAvailabilityStatus.AVAILABLE:
            if (
                self.receipt is None
                or self.reason_code is not None
                or self.receipt.kind is not StructureReadBundleKind.SNAPSHOT
                or self.receipt.snapshot_ids != (self.snapshot_id,)
            ):
                raise _invalid(
                    "READ_BUNDLE_AVAILABILITY_INVALID",
                    "available Bundle status requires an exact Snapshot Receipt",
                )
            self.receipt.require_valid()
        elif self.receipt is not None or self.reason_code is None:
            raise _invalid(
                "READ_BUNDLE_AVAILABILITY_INVALID",
                "unavailable Bundle status requires a reason and no Receipt",
            )


class StructureSnapshotBundleSource(Protocol):
    def get_snapshot(self, snapshot_id: StableId) -> StructureSnapshot: ...

    def get_entity(
        self, snapshot_id: StableId, entity_root_id: StableId
    ) -> EntityRecord: ...

    def get_relation_fact(
        self, snapshot_id: StableId, relation_root_id: StableId
    ) -> RelationFactRecord: ...

    def get_literal_fact(
        self, snapshot_id: StableId, literal_root_id: StableId
    ) -> LiteralFactRecord: ...

    def get_coverage(
        self, snapshot_id: StableId, coverage_root_id: StableId
    ) -> CoverageRecord: ...

    def get_evidence_metadata(
        self, evidence_id: StableId
    ) -> StructureEvidenceMetadata: ...


class StructureReadSessionSource(Protocol):
    def get_session(self, session_id: StableId) -> StructureReadSession: ...


class StructureReadBundleFileStore(Protocol):
    def write_snapshot(
        self, locator: str, bundle: StructureSnapshotReadBundle
    ) -> StoredStructureReadBundle: ...

    def read_snapshot(
        self, locator: str
    ) -> tuple[StructureSnapshotReadBundle, Digest]: ...

    def write_ordered(
        self, locator: str, bundle: StructureOrderedReadBundle
    ) -> StoredStructureReadBundle: ...

    def read_ordered(
        self, locator: str
    ) -> tuple[StructureOrderedReadBundle, Digest]: ...


class StructureReadBundleRepository(Protocol):
    def replay(
        self, *, idempotency_key: IdempotencyKey, request_digest: Digest
    ) -> StructureReadBundleReceipt | None: ...

    def save(
        self,
        *,
        idempotency_key: IdempotencyKey,
        request_digest: Digest,
        kind: StructureReadBundleKind,
        scope_id: StableId,
        snapshot_ids: tuple[StableId, ...],
        session_id: StableId | None,
        read_set_digest: Digest | None,
        stored_bundle: StoredStructureReadBundle,
        created_at: datetime,
    ) -> StructureReadBundleReceipt: ...

    def get(self, receipt_id: StableId) -> StructureReadBundleReceipt: ...

    def latest_snapshot(
        self, snapshot_id: StableId
    ) -> StructureReadBundleReceipt | None: ...


class StructureReadBundleService:
    """Build and receipt exact Bundles only after Snapshot publication."""

    def __init__(
        self,
        repository: StructureReadBundleRepository,
        files: StructureReadBundleFileStore,
        snapshots: StructureSnapshotBundleSource,
        sessions: StructureReadSessionSource,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._repository = repository
        self._files = files
        self._snapshots = snapshots
        self._sessions = sessions
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def build_snapshot(
        self,
        *,
        snapshot_id: StableId,
        idempotency_key: IdempotencyKey,
        destination: str,
    ) -> StructureReadBundleReceipt:
        locator = _text(destination, "Bundle destination")
        request_digest = digest_of(
            [
                "BUILD_STRUCTURE_SNAPSHOT_READ_BUNDLE@1",
                {"snapshot_id": snapshot_id.value, "destination": locator},
            ]
        )
        replay = self._repository.replay(
            idempotency_key=idempotency_key,
            request_digest=request_digest,
        )
        bundle = self._collect_snapshot(snapshot_id)
        if replay is not None:
            self._restore_or_verify_snapshot(replay, bundle)
            return replay
        stored = self._files.write_snapshot(locator, bundle)
        if (
            stored.bundle_digest != bundle.digest
            or stored.format_ref != STRUCTURE_SNAPSHOT_READ_BUNDLE_FORMAT
        ):
            raise _inconsistent("Bundle file store returned another semantic digest")
        return self._repository.save(
            idempotency_key=idempotency_key,
            request_digest=request_digest,
            kind=StructureReadBundleKind.SNAPSHOT,
            scope_id=bundle.scope_id,
            snapshot_ids=(bundle.snapshot_id,),
            session_id=None,
            read_set_digest=None,
            stored_bundle=stored,
            created_at=self._now(),
        )

    def build_ordered(
        self,
        *,
        session_id: StableId,
        idempotency_key: IdempotencyKey,
        destination: str,
    ) -> StructureReadBundleReceipt:
        locator = _text(destination, "ordered Bundle destination")
        session = self._sessions.get_session(session_id)
        session.require_valid()
        request_digest = digest_of(
            [
                "BUILD_STRUCTURE_ORDERED_READ_BUNDLE@1",
                {
                    "session_id": session.session_id.value,
                    "session_digest": session.digest.value,
                    "read_set_digest": session.read_set_digest.value,
                    "destination": locator,
                },
            ]
        )
        replay = self._repository.replay(
            idempotency_key=idempotency_key,
            request_digest=request_digest,
        )
        references: list[StructureSnapshotBundleReference] = []
        loaded: list[tuple[StructureSnapshotReadBundle, Digest]] = []
        for ordinal, binding in enumerate(session.snapshots):
            receipt = self._repository.latest_snapshot(binding.snapshot_id)
            if receipt is None:
                raise _invalid(
                    "READ_BUNDLE_SNAPSHOT_RECEIPT_REQUIRED",
                    "ordered Bundle requires an available Receipt for every Snapshot",
                )
            receipt.require_valid()
            try:
                snapshot_bundle, file_digest = self._files.read_snapshot(
                    receipt.stored_bundle.locator
                )
            except FileNotFoundError as exc:
                raise _invalid(
                    "READ_BUNDLE_SNAPSHOT_FILE_UNAVAILABLE",
                    "ordered Bundle references a missing Snapshot Bundle file",
                ) from exc
            if (
                snapshot_bundle.snapshot_id != binding.snapshot_id
                or snapshot_bundle.snapshot.manifest_digest
                != binding.snapshot_manifest_digest
                or snapshot_bundle.digest != receipt.stored_bundle.bundle_digest
                or file_digest != receipt.stored_bundle.file_digest
            ):
                raise _inconsistent(
                    "Snapshot Bundle Receipt does not verify against the exact read Session"
                )
            references.append(
                StructureSnapshotBundleReference(
                    ordinal=ordinal,
                    snapshot_id=binding.snapshot_id,
                    snapshot_binding_digest=binding.digest,
                    snapshot_manifest_digest=binding.snapshot_manifest_digest,
                    bundle_digest=snapshot_bundle.digest,
                    file_digest=file_digest,
                )
            )
            loaded.append((snapshot_bundle, file_digest))
        envelope = StructureOrderedReadBundle.create(
            session=session,
            snapshots=tuple(references),
        )
        envelope.verify_snapshot_bundles(tuple(loaded))
        if replay is not None:
            self._restore_or_verify_ordered(replay, envelope)
            return replay
        stored = self._files.write_ordered(locator, envelope)
        if (
            stored.bundle_digest != envelope.digest
            or stored.format_ref != STRUCTURE_ORDERED_READ_BUNDLE_FORMAT
        ):
            raise _inconsistent(
                "Bundle file store returned another ordered semantic digest"
            )
        return self._repository.save(
            idempotency_key=idempotency_key,
            request_digest=request_digest,
            kind=StructureReadBundleKind.ORDERED_READ_SET,
            scope_id=session.scope_id,
            snapshot_ids=tuple(item.snapshot_id for item in session.snapshots),
            session_id=session.session_id,
            read_set_digest=session.read_set_digest,
            stored_bundle=stored,
            created_at=self._now(),
        )

    def get_receipt(self, receipt_id: StableId) -> StructureReadBundleReceipt:
        receipt = self._repository.get(receipt_id)
        receipt.require_valid()
        return receipt

    def availability(
        self, snapshot_id: StableId
    ) -> StructureReadBundleAvailability:
        receipt = self._repository.latest_snapshot(snapshot_id)
        if receipt is None:
            value = StructureReadBundleAvailability(
                snapshot_id=snapshot_id,
                status=StructureReadBundleAvailabilityStatus.UNAVAILABLE,
                receipt=None,
                reason_code="READ_BUNDLE_RECEIPT_NOT_FOUND",
            )
            value.require_valid()
            return value
        receipt.require_valid()
        try:
            bundle, file_digest = self._files.read_snapshot(
                receipt.stored_bundle.locator
            )
        except FileNotFoundError:
            value = StructureReadBundleAvailability(
                snapshot_id=snapshot_id,
                status=StructureReadBundleAvailabilityStatus.UNAVAILABLE,
                receipt=None,
                reason_code="READ_BUNDLE_FILE_NOT_FOUND",
            )
            value.require_valid()
            return value
        if (
            bundle.snapshot_id != snapshot_id
            or bundle.digest != receipt.stored_bundle.bundle_digest
            or file_digest != receipt.stored_bundle.file_digest
        ):
            raise _inconsistent("Bundle availability Receipt does not verify")
        value = StructureReadBundleAvailability(
            snapshot_id=snapshot_id,
            status=StructureReadBundleAvailabilityStatus.AVAILABLE,
            receipt=receipt,
            reason_code=None,
        )
        value.require_valid()
        return value

    def _collect_snapshot(
        self, snapshot_id: StableId
    ) -> StructureSnapshotReadBundle:
        snapshot = self._snapshots.get_snapshot(snapshot_id)
        if snapshot.snapshot_id != snapshot_id:
            raise _inconsistent("exact Snapshot lookup returned another identity")
        coverages = tuple(
            self._snapshots.get_coverage(snapshot_id, item.coverage_root_id)
            for item in snapshot.coverages
        )
        entities: list[EntityRecord] = []
        relations: list[RelationFactRecord] = []
        literals: list[LiteralFactRecord] = []
        for member in snapshot.members:
            if member.kind is CoverageMemberKind.ENTITY:
                entities.append(
                    self._snapshots.get_entity(snapshot_id, member.root_id)
                )
            elif member.kind is CoverageMemberKind.RELATION_FACT:
                relations.append(
                    self._snapshots.get_relation_fact(snapshot_id, member.root_id)
                )
            elif member.kind is CoverageMemberKind.LITERAL_FACT:
                literals.append(
                    self._snapshots.get_literal_fact(snapshot_id, member.root_id)
                )
            else:  # pragma: no cover - Enum exhaustiveness guard
                raise _inconsistent("Snapshot contains an unsupported member kind")
        upstream = tuple(
            StructureBundleUpstreamEntityRecord(
                snapshot_id=item.upstream_snapshot_id,
                entity=self._snapshots.get_entity(
                    item.upstream_snapshot_id, item.entity_root_id
                ),
            )
            for item in snapshot.upstream_entities
        )
        evidence_ids: set[StableId] = set()
        for record in (*entities, *(item.entity for item in upstream)):
            evidence_ids.update(record.state.evidence_references)
        for record in relations:
            evidence_ids.update(record.state.evidence_references)
        for record in literals:
            evidence_ids.update(record.state.evidence_references)
        for record in coverages:
            evidence_ids.update(record.state.evidence_references)
        evidence = tuple(
            self._snapshots.get_evidence_metadata(item)
            for item in sorted(evidence_ids, key=lambda value: value.value)
        )
        return StructureSnapshotReadBundle.create(
            snapshot=snapshot,
            coverages=coverages,
            entities=tuple(entities),
            relation_facts=tuple(relations),
            literal_facts=tuple(literals),
            upstream_entity_records=upstream,
            evidence_metadata=evidence,
        )

    def _restore_or_verify_snapshot(
        self,
        receipt: StructureReadBundleReceipt,
        bundle: StructureSnapshotReadBundle,
    ) -> None:
        receipt.require_valid()
        if (
            receipt.kind is not StructureReadBundleKind.SNAPSHOT
            or receipt.snapshot_ids != (bundle.snapshot_id,)
            or receipt.scope_id != bundle.scope_id
            or receipt.stored_bundle.bundle_digest != bundle.digest
        ):
            raise _inconsistent("replayed Bundle Receipt differs from exact Snapshot")
        try:
            loaded, file_digest = self._files.read_snapshot(
                receipt.stored_bundle.locator
            )
        except FileNotFoundError:
            stored = self._files.write_snapshot(
                receipt.stored_bundle.locator, bundle
            )
            if stored != receipt.stored_bundle:
                raise _inconsistent(
                    "regenerated Snapshot Bundle differs from its Receipt"
                )
            return
        if loaded != bundle or file_digest != receipt.stored_bundle.file_digest:
            raise _inconsistent("replayed Snapshot Bundle file differs from its Receipt")

    def _restore_or_verify_ordered(
        self,
        receipt: StructureReadBundleReceipt,
        bundle: StructureOrderedReadBundle,
    ) -> None:
        receipt.require_valid()
        if (
            receipt.kind is not StructureReadBundleKind.ORDERED_READ_SET
            or receipt.session_id != bundle.session.session_id
            or receipt.snapshot_ids
            != tuple(item.snapshot_id for item in bundle.snapshots)
            or receipt.stored_bundle.bundle_digest != bundle.digest
        ):
            raise _inconsistent("replayed ordered Bundle Receipt differs from its Session")
        try:
            loaded, file_digest = self._files.read_ordered(
                receipt.stored_bundle.locator
            )
        except FileNotFoundError:
            stored = self._files.write_ordered(
                receipt.stored_bundle.locator, bundle
            )
            if stored != receipt.stored_bundle:
                raise _inconsistent(
                    "regenerated ordered Bundle differs from its Receipt"
                )
            return
        if loaded != bundle or file_digest != receipt.stored_bundle.file_digest:
            raise _inconsistent("replayed ordered Bundle file differs from its Receipt")

    def _now(self) -> datetime:
        now = self._clock()
        if now.tzinfo is None or now.utcoffset() is None:
            raise _invalid(
                "READ_BUNDLE_TIME_INVALID",
                "Bundle clock must return a timezone-aware value",
            )
        return now.astimezone(timezone.utc)


def structure_snapshot_read_bundle_core(
    *,
    snapshot: StructureSnapshot,
    coverages: tuple[CoverageRecord, ...],
    entities: tuple[EntityRecord, ...],
    relation_facts: tuple[RelationFactRecord, ...],
    literal_facts: tuple[LiteralFactRecord, ...],
    upstream_entity_records: tuple[StructureBundleUpstreamEntityRecord, ...],
    evidence_metadata: tuple[StructureEvidenceMetadata, ...],
) -> dict[str, object]:
    return {
        "format_ref": STRUCTURE_SNAPSHOT_READ_BUNDLE_FORMAT,
        "snapshot": _snapshot_value(snapshot),
        "coverages": tuple(_coverage_value(item) for item in coverages),
        "entities": tuple(_entity_value(item) for item in entities),
        "relation_facts": tuple(_relation_value(item) for item in relation_facts),
        "literal_facts": tuple(_literal_value(item) for item in literal_facts),
        "upstream_entity_records": tuple(
            {
                "snapshot_id": item.snapshot_id.value,
                "entity": _entity_value(item.entity),
            }
            for item in upstream_entity_records
        ),
        "evidence_metadata": tuple(
            _evidence_metadata_value(item) for item in evidence_metadata
        ),
        "payload_policy": {
            "evidence_observation_fields": 0,
            "evidence_excerpt_fields": 0,
            "artifact_payload_fields": 0,
            "source_payload_fields": 0,
            "provider_input_fields": 0,
        },
    }


def structure_ordered_read_bundle_core(
    *,
    session: StructureReadSession,
    snapshots: tuple[StructureSnapshotBundleReference, ...],
) -> dict[str, object]:
    return {
        "format_ref": STRUCTURE_ORDERED_READ_BUNDLE_FORMAT,
        "session": _session_value(session),
        "snapshots": tuple(
            {
                "ordinal": item.ordinal,
                "snapshot_id": item.snapshot_id.value,
                "snapshot_binding_digest": item.snapshot_binding_digest.value,
                "snapshot_manifest_digest": item.snapshot_manifest_digest.value,
                "bundle_digest": item.bundle_digest.value,
                "file_digest": item.file_digest.value,
            }
            for item in snapshots
        ),
        "payload_policy": {
            "evidence_observation_fields": 0,
            "evidence_excerpt_fields": 0,
            "artifact_payload_fields": 0,
            "source_payload_fields": 0,
            "provider_input_fields": 0,
        },
    }


def structure_read_bundle_receipt_core(
    *,
    receipt_id: StableId,
    idempotency_key: IdempotencyKey,
    kind: StructureReadBundleKind,
    request_digest: Digest,
    scope_id: StableId,
    snapshot_ids: tuple[StableId, ...],
    session_id: StableId | None,
    read_set_digest: Digest | None,
    stored_bundle: StoredStructureReadBundle,
    created_at: datetime,
) -> dict[str, object]:
    return {
        "receipt_id": receipt_id.value,
        "idempotency_key": idempotency_key.value,
        "kind": kind.value,
        "request_digest": request_digest.value,
        "scope_id": scope_id.value,
        "snapshot_ids": tuple(item.value for item in snapshot_ids),
        "session_id": session_id.value if session_id is not None else None,
        "read_set_digest": (
            read_set_digest.value if read_set_digest is not None else None
        ),
        "stored_bundle": {
            "locator": stored_bundle.locator,
            "format_ref": stored_bundle.format_ref,
            "bundle_digest": stored_bundle.bundle_digest.value,
            "file_digest": stored_bundle.file_digest.value,
        },
        "created_at": created_at,
    }


def _snapshot_value(snapshot: StructureSnapshot) -> dict[str, object]:
    return {
        "snapshot_id": snapshot.snapshot_id.value,
        "scope_id": snapshot.scope_id.value,
        "snapshot_revision": snapshot.snapshot_revision.value,
        "previous_snapshot_id": (
            snapshot.previous_snapshot_id.value
            if snapshot.previous_snapshot_id is not None
            else None
        ),
        "schema_ref": snapshot.schema_ref,
        "schema_digest": snapshot.schema_digest.value,
        "schema_adoption_mode": snapshot.schema_adoption_mode.value,
        "schema_registration_digest": snapshot.schema_registration_digest.value,
        "schema_availability_digest": snapshot.schema_availability_digest.value,
        "schema_adoption_digest": snapshot.schema_adoption_digest.value,
        "publication_mode": snapshot.publication_mode.value,
        "members": tuple(_member_value(item) for item in snapshot.members),
        "coverages": tuple(
            {
                "coverage_root_id": item.coverage_root_id.value,
                "coverage_state_id": item.coverage_state_id.value,
                "coverage_state_digest": item.coverage_state_digest.value,
            }
            for item in snapshot.coverages
        ),
        "upstream_entities": tuple(
            {
                "upstream_snapshot_id": item.upstream_snapshot_id.value,
                "entity_root_id": item.entity_root_id.value,
                "entity_state_id": item.entity_state_id.value,
                "entity_state_digest": item.entity_state_digest.value,
            }
            for item in snapshot.upstream_entities
        ),
        "manifest_digest": snapshot.manifest_digest.value,
        "published_at": _time(snapshot.published_at),
    }


def _entity_value(record: EntityRecord) -> dict[str, object]:
    return {
        "root": {
            "entity_root_id": record.root.entity_root_id.value,
            "entity_type": record.root.entity_type.value,
            "identity_scheme": record.root.identity_scheme,
            "root_fields": record.root.root_fields.as_dict(),
            "allocation_key_digest": record.root.allocation_key_digest.value,
        },
        "state": {
            "entity_state_id": record.state.entity_state_id.value,
            "entity_state_digest": record.state.entity_state_digest.value,
            "entity_root_id": record.state.entity_root_id.value,
            "entity_type": record.state.entity_type.value,
            "state_payload_fields": record.state.state_payload_fields.as_dict(),
            "allocation_key_digest": record.state.allocation_key_digest.value,
        },
    }


def _relation_value(record: RelationFactRecord) -> dict[str, object]:
    return {
        "root": {
            "relation_root_id": record.root.relation_root_id.value,
            "owning_scope_id": record.root.owning_scope_id.value,
            "schema_ref": record.root.schema_ref,
            "subject": record.root.subject.canonical_value(),
            "predicate": record.root.predicate.value,
            "object": record.root.object.canonical_value(),
            "observation_modality": record.root.observation_modality.value,
            "allocation_key_digest": record.root.allocation_key_digest.value,
        },
        "state": {
            "relation_state_id": record.state.relation_state_id.value,
            "relation_state_digest": record.state.relation_state_digest.value,
            "relation_root_id": record.state.relation_root_id.value,
            "subject_entity_state_id": record.state.subject_entity_state_id.value,
            "object_entity_state_id": record.state.object_entity_state_id.value,
            "source_revision": record.state.source_revision,
            "knowledge_context_digest": record.state.knowledge_context_digest.value,
            "evidence_references": tuple(
                item.value for item in record.state.evidence_references
            ),
            "predicate_state_payload_fields": (
                record.state.predicate_state_payload_fields.as_dict()
            ),
            "allocation_key_digest": record.state.allocation_key_digest.value,
        },
    }


def _literal_value(record: LiteralFactRecord) -> dict[str, object]:
    return {
        "root": {
            "literal_root_id": record.root.literal_root_id.value,
            "owning_scope_id": record.root.owning_scope_id.value,
            "schema_ref": record.root.schema_ref,
            "subject": record.root.subject.canonical_value(),
            "predicate": record.root.predicate,
            "object": record.root.object.canonical_value(),
            "observation_modality": record.root.observation_modality,
            "allocation_key_digest": record.root.allocation_key_digest.value,
        },
        "state": {
            "literal_state_id": record.state.literal_state_id.value,
            "literal_state_digest": record.state.literal_state_digest.value,
            "literal_root_id": record.state.literal_root_id.value,
            "subject_entity_state_id": record.state.subject_entity_state_id.value,
            "source_revision": record.state.source_revision,
            "knowledge_context_digest": record.state.knowledge_context_digest.value,
            "evidence_references": tuple(
                item.value for item in record.state.evidence_references
            ),
            "allocation_key_digest": record.state.allocation_key_digest.value,
        },
    }


def _coverage_value(record: CoverageRecord) -> dict[str, object]:
    return {
        "root": {
            "coverage_root_id": record.root.coverage_root_id.value,
            "coverage_root_ref": record.root.coverage_root_ref,
            "owning_scope_id": record.root.owning_scope_id.value,
            "profile_ref": record.root.profile_ref,
            "schema_ref": record.root.schema_ref,
            "schema_digest": record.root.schema_digest.value,
            "source_binding_id": record.root.source_binding_id.value,
            "logical_reactor_root": record.root.logical_reactor_root,
            "maven_evaluation_context_ref": (
                record.root.maven_evaluation_context_ref
            ),
            "maven_evaluation_context_digest": (
                record.root.maven_evaluation_context_digest.value
            ),
            "covered_entity_types": tuple(
                item.value for item in record.root.covered_entity_types
            ),
            "covered_relation_predicates": tuple(
                item.value for item in record.root.covered_relation_predicates
            ),
            "canonicalization_ref": record.root.canonicalization_ref,
            "canonicalization_digest": record.root.canonicalization_digest.value,
            "allocation_key_digest": record.root.allocation_key_digest.value,
        },
        "state": {
            "coverage_state_id": record.state.coverage_state_id.value,
            "coverage_state_digest": record.state.coverage_state_digest.value,
            "coverage_root_id": record.state.coverage_root_id.value,
            "source_revision": record.state.source_revision,
            "knowledge_context_digest": record.state.knowledge_context_digest.value,
            "schema_ref": record.state.schema_ref,
            "schema_digest": record.state.schema_digest.value,
            "maven_evaluation_context_ref": (
                record.state.maven_evaluation_context_ref
            ),
            "maven_evaluation_context_digest": (
                record.state.maven_evaluation_context_digest.value
            ),
            "canonicalization_ref": record.state.canonicalization_ref,
            "canonicalization_digest": record.state.canonicalization_digest.value,
            "complete_member_manifest": {
                "completeness": (
                    record.state.complete_member_manifest.completeness.value
                ),
                "members": tuple(
                    _member_value(item)
                    for item in record.state.complete_member_manifest.members
                ),
                "digest": record.state.complete_member_manifest.digest.value,
            },
            "evidence_references": tuple(
                item.value for item in record.state.evidence_references
            ),
            "allocation_key_digest": record.state.allocation_key_digest.value,
        },
    }


def _evidence_metadata_value(
    metadata: StructureEvidenceMetadata,
) -> dict[str, object]:
    return {
        "evidence_id": metadata.evidence_id.value,
        "artifact_id": metadata.artifact_id.value,
        "source_context_id": metadata.source_context_id.value,
        "byte_start": metadata.byte_start,
        "byte_end": metadata.byte_end,
        "locator": metadata.locator,
        "excerpt_digest": metadata.excerpt_digest.value,
        "artifact_content_digest": metadata.artifact_content_digest.value,
        "digest": metadata.digest.value,
    }


def _session_value(session: StructureReadSession) -> dict[str, object]:
    return {
        "session_id": session.session_id.value,
        "request_digest": session.request_digest.value,
        "scope_id": session.scope_id.value,
        "scope_revision": session.scope_revision.value,
        "task_boundary": {
            "task_id": session.task_boundary.task_id.value,
            "task_revision": session.task_boundary.task_revision.value,
            "scope_id": session.task_boundary.scope_id.value,
            "purpose": session.task_boundary.purpose,
            "classification": session.task_boundary.classification,
            "digest": session.task_boundary.digest.value,
        },
        "scope_assertion": {
            "assertion_id": session.scope_assertion.assertion_id.value,
            "scope_id": session.scope_assertion.scope_id.value,
            "scope_type": session.scope_assertion.scope_type.value,
            "definition_revision": session.scope_assertion.definition_revision.value,
            "lifecycle": session.scope_assertion.lifecycle.value,
            "purpose": session.scope_assertion.purpose.value,
            "outcome": session.scope_assertion.outcome.value,
            "caller_ref": session.scope_assertion.caller_ref,
            "request_ref": session.scope_assertion.request_ref,
            "classification": session.scope_assertion.classification,
            "read_at": _time(session.scope_assertion.read_at),
            "digest": session.scope_assertion.digest.value,
        },
        "caller_ref": session.caller_ref,
        "purpose": session.purpose.value,
        "selection_mode": session.selection_mode.value,
        "order": session.order.value,
        "snapshots": tuple(
            {
                "scope_id": item.scope_id.value,
                "snapshot_id": item.snapshot_id.value,
                "snapshot_revision": item.snapshot_revision.value,
                "snapshot_manifest_digest": item.snapshot_manifest_digest.value,
                "schema_ref": item.schema_ref,
                "schema_digest": item.schema_digest.value,
                "schema_registration_digest": (
                    item.schema_registration_digest.value
                ),
                "schema_availability_digest": (
                    item.schema_availability_digest.value
                ),
                "schema_adoption_digest": item.schema_adoption_digest.value,
                "coverages": tuple(
                    {
                        "coverage_root_id": coverage.coverage_root_id.value,
                        "coverage_root_digest": coverage.coverage_root_digest.value,
                        "coverage_root_ref": coverage.coverage_root_ref,
                        "coverage_state_id": coverage.coverage_state_id.value,
                        "coverage_state_digest": coverage.coverage_state_digest.value,
                        "profile_ref": coverage.profile_ref,
                        "schema_ref": coverage.schema_ref,
                        "schema_digest": coverage.schema_digest.value,
                        "source_binding_id": coverage.source_binding_id.value,
                        "logical_reactor_root": coverage.logical_reactor_root,
                        "evaluation_context_ref": coverage.evaluation_context_ref,
                        "evaluation_context_digest": (
                            coverage.evaluation_context_digest.value
                        ),
                        "canonicalization_ref": coverage.canonicalization_ref,
                        "canonicalization_digest": (
                            coverage.canonicalization_digest.value
                        ),
                        "knowledge_context_digest": (
                            coverage.knowledge_context_digest.value
                        ),
                        "source_revision": coverage.source_revision,
                        "member_manifest_digest": (
                            coverage.member_manifest_digest.value
                        ),
                        "comparison_basis_digest": (
                            coverage.comparison_basis_digest.value
                        ),
                        "digest": coverage.digest.value,
                    }
                    for coverage in item.coverages
                ),
                "coverage_set_digest": item.coverage_set_digest.value,
                "digest": item.digest.value,
            }
            for item in session.snapshots
        ),
        "context_comparisons": tuple(
            {
                "assessment_id": item.assessment_id.value,
                "ordinal": item.ordinal,
                "purpose": item.purpose.value,
                "base_snapshot_id": item.base_snapshot_id.value,
                "base_snapshot_binding_digest": (
                    item.base_snapshot_binding_digest.value
                ),
                "target_snapshot_id": item.target_snapshot_id.value,
                "target_snapshot_binding_digest": (
                    item.target_snapshot_binding_digest.value
                ),
                "base_knowledge_context_digests": tuple(
                    value.value for value in item.base_knowledge_context_digests
                ),
                "target_knowledge_context_digests": tuple(
                    value.value for value in item.target_knowledge_context_digests
                ),
                "comparison_basis_digests": tuple(
                    value.value for value in item.comparison_basis_digests
                ),
                "outcome": item.outcome.value,
                "digest": item.digest.value,
            }
            for item in session.context_comparisons
        ),
        "read_set_digest": session.read_set_digest.value,
        "opened_at": _time(session.opened_at),
        "digest": session.digest.value,
    }


def _member_value(member: CoverageMember) -> dict[str, str]:
    return member.canonical_value()


def _require_sorted_unique_records(records: tuple[object, ...], label: str) -> None:
    expected = tuple(sorted(records, key=lambda item: item.root_id.value))
    if records != expected or len({item.root_id for item in records}) != len(records):
        raise _invalid(
            "READ_BUNDLE_RECORD_SET_INVALID",
            f"Bundle {label} records must be sorted and unique",
        )


def _require_local_record_boundary(
    record: EntityRecord | RelationFactRecord | LiteralFactRecord,
    *,
    scope_id: StableId,
    schema_ref: str,
) -> None:
    if isinstance(record, EntityRecord):
        record.root.require_valid_identity()
        record.state.require_valid_identity()
        owner = record.root.owning_scope_id
        record_schema = schema_ref
    elif isinstance(record, RelationFactRecord):
        record.root.require_valid_identity()
        record.state.require_valid_identity(record.root)
        owner = record.root.owning_scope_id
        record_schema = record.root.schema_ref
    elif isinstance(record, LiteralFactRecord):
        record.root.require_valid_identity()
        record.state.require_valid_identity(record.root)
        owner = record.root.owning_scope_id
        record_schema = record.root.schema_ref
    else:  # pragma: no cover - typed callers only
        raise _invalid(
            "READ_BUNDLE_RECORD_TYPE_INVALID",
            "Bundle contains an unsupported typed record",
        )
    if owner != scope_id or record_schema != schema_ref:
        raise _invalid(
            "READ_BUNDLE_RECORD_BOUNDARY_MISMATCH",
            "Bundle record is outside the exact Snapshot Scope/Schema",
        )


def _require_endpoint(
    reference: EntityRef,
    state_id: StableId,
    local: dict[StableId, EntityRecord],
    upstream: dict[StableId, StructureBundleUpstreamEntityRecord],
) -> None:
    local_record = local.get(reference.entity_root_id)
    upstream_record = upstream.get(reference.entity_root_id)
    if local_record is not None and upstream_record is not None:
        raise _invalid(
            "READ_BUNDLE_ENDPOINT_AMBIGUOUS",
            "Relation endpoint exists in both local and upstream Bundle closure",
        )
    record = (
        local_record
        if local_record is not None
        else upstream_record.entity if upstream_record is not None else None
    )
    if record is None:
        raise _invalid(
            "READ_BUNDLE_ENDPOINT_DANGLING",
            "Bundle Relation endpoint is not present in its exact closure",
        )
    if (
        record.root.ref != reference
        or record.state_id != state_id
        or record.root.entity_type != reference.entity_type
    ):
        raise _invalid(
            "READ_BUNDLE_ENDPOINT_BINDING_MISMATCH",
            "Bundle Relation endpoint differs from its typed Root/State binding",
        )


def _require_valid_evidence_metadata(metadata: StructureEvidenceMetadata) -> None:
    if not isinstance(metadata, StructureEvidenceMetadata):
        raise _invalid(
            "READ_BUNDLE_EVIDENCE_METADATA_REQUIRED",
            "Bundle requires typed Evidence metadata",
        )
    if (
        metadata.evidence_id.kind != "evidence"
        or type(metadata.byte_start) is not int
        or type(metadata.byte_end) is not int
        or metadata.byte_start < 0
        or metadata.byte_end <= metadata.byte_start
    ):
        raise _invalid(
            "READ_BUNDLE_EVIDENCE_METADATA_INVALID",
            "Bundle Evidence metadata identity or range is invalid",
        )
    _text(metadata.locator, "Evidence locator")
    core = CanonicalFields(
        {
            "artifact_id": metadata.artifact_id.value,
            "source_context_id": metadata.source_context_id.value,
            "byte_start": metadata.byte_start,
            "byte_end": metadata.byte_end,
            "locator": metadata.locator,
            "excerpt_digest": metadata.excerpt_digest.value,
            "artifact_content_digest": metadata.artifact_content_digest.value,
        }
    )
    expected_digest = digest_of(core)
    if (
        metadata.digest != expected_digest
        or metadata.evidence_id
        != StableId(f"evidence_{expected_digest.value[-32:]}")
    ):
        raise _invalid(
            "READ_BUNDLE_EVIDENCE_METADATA_DIGEST_MISMATCH",
            "Bundle Evidence metadata is not canonical",
        )


def _time(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise _invalid(
            "READ_BUNDLE_TIME_INVALID",
            "Bundle timestamps must include a timezone",
        )
    return (
        value.astimezone(timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise _invalid(
            "READ_BUNDLE_TEXT_INVALID",
            f"{label} must be canonical text",
        )
    return value


def _invalid(reason_code: str, message: str) -> DomainError:
    return DomainError(
        ErrorCode.INVALID_ARGUMENT,
        message,
        {"reason_code": reason_code},
    )


def _inconsistent(message: str) -> DomainError:
    return DomainError(ErrorCode.AUTHORITY_RECORD_INCONSISTENT, message)


__all__ = [
    "STRUCTURE_ORDERED_READ_BUNDLE_FORMAT",
    "STRUCTURE_SNAPSHOT_READ_BUNDLE_FORMAT",
    "StoredStructureReadBundle",
    "StructureBundleUpstreamEntityRecord",
    "StructureOrderedReadBundle",
    "StructureReadBundleAvailability",
    "StructureReadBundleAvailabilityStatus",
    "StructureReadBundleFileStore",
    "StructureReadBundleKind",
    "StructureReadBundleReceipt",
    "StructureReadBundleRepository",
    "StructureReadBundleService",
    "StructureReadSessionSource",
    "StructureSnapshotBundleReference",
    "StructureSnapshotBundleSource",
    "StructureSnapshotReadBundle",
    "structure_ordered_read_bundle_core",
    "structure_read_bundle_receipt_core",
    "structure_snapshot_read_bundle_core",
]
