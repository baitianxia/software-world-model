"""Application-owned queryable Read Sets and sealed Source-off catalogs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import re
from typing import Callable, Mapping, Protocol, Sequence

from software_world_model.application_services.structure_read_bundle import (
    StructureReadBundleKind,
    StructureReadBundleReceipt,
    StoredStructureReadBundle,
    structure_read_bundle_receipt_core,
)
from software_world_model.application_services.structure_read_session import (
    StructureCoverageReadBinding,
    StructureReadSession,
    StructureSnapshotReadBinding,
)
from software_world_model.cross_cutting import (
    Digest,
    DomainError,
    ErrorCode,
    IdGenerator,
    IdempotencyKey,
    Revision,
    StableId,
    Uuid4IdGenerator,
    digest_of,
)


READ_SET_CATALOG_SCHEMA = "SWM-READ-SET-CATALOG@1"
READ_SET_REGISTRATION_SCHEMA = "SWM-READ-SET-REGISTRATION@1"
_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")


class ReadSetAvailability(str, Enum):
    QUERYABLE = "QUERYABLE"


class ReadSetFileRole(str, Enum):
    ORDERED_ENVELOPE = "ORDERED_ENVELOPE"
    SNAPSHOT = "SNAPSHOT"


@dataclass(frozen=True, slots=True)
class ReadSetFile:
    ordinal: int
    role: ReadSetFileRole
    locator: str
    format_ref: str
    bundle_digest: Digest
    file_digest: Digest
    receipt_id: StableId
    receipt_digest: Digest

    @classmethod
    def from_receipt(
        cls,
        *,
        ordinal: int,
        role: ReadSetFileRole,
        receipt: StructureReadBundleReceipt,
    ) -> "ReadSetFile":
        receipt.require_valid()
        value = cls(
            ordinal=ordinal,
            role=role,
            locator=receipt.stored_bundle.locator,
            format_ref=receipt.stored_bundle.format_ref,
            bundle_digest=receipt.stored_bundle.bundle_digest,
            file_digest=receipt.stored_bundle.file_digest,
            receipt_id=receipt.receipt_id,
            receipt_digest=receipt.digest,
        )
        value.require_valid()
        return value

    def require_valid(self) -> None:
        if type(self.ordinal) is not int or self.ordinal < 0:
            raise _invalid("READ_SET_FILE_ORDINAL_INVALID", "Read Set file ordinal is invalid")
        if not isinstance(self.role, ReadSetFileRole):
            raise _invalid("READ_SET_FILE_ROLE_INVALID", "Read Set file role is invalid")
        _relative_locator(self.locator, "Read Set file locator")
        _text(self.format_ref, "Bundle format ref")
        if self.receipt_id.kind != "read_bundle_receipt":
            raise _invalid("READ_SET_FILE_RECEIPT_INVALID", "Read Set file requires a Bundle Receipt")

    def canonical_value(self) -> dict[str, object]:
        return {
            "ordinal": self.ordinal,
            "role": self.role.value,
            "locator": self.locator,
            "format_ref": self.format_ref,
            "bundle_digest": self.bundle_digest.value,
            "file_digest": self.file_digest.value,
            "receipt_id": self.receipt_id.value,
            "receipt_digest": self.receipt_digest.value,
        }


@dataclass(frozen=True, slots=True)
class CatalogCoverageBinding:
    coverage_root_id: StableId
    coverage_root_digest: Digest
    coverage_root_ref: str
    coverage_state_id: StableId
    coverage_state_digest: Digest
    profile_ref: str
    schema_ref: str
    schema_digest: Digest
    source_binding_id: StableId
    logical_reactor_root: str
    evaluation_context_ref: str
    evaluation_context_digest: Digest
    canonicalization_ref: str
    canonicalization_digest: Digest
    knowledge_context_digest: Digest
    member_manifest_digest: Digest
    comparison_basis_digest: Digest
    binding_digest: Digest

    @classmethod
    def from_binding(cls, value: StructureCoverageReadBinding) -> "CatalogCoverageBinding":
        value.require_valid()
        result = cls(
            coverage_root_id=value.coverage_root_id,
            coverage_root_digest=value.coverage_root_digest,
            coverage_root_ref=value.coverage_root_ref,
            coverage_state_id=value.coverage_state_id,
            coverage_state_digest=value.coverage_state_digest,
            profile_ref=value.profile_ref,
            schema_ref=value.schema_ref,
            schema_digest=value.schema_digest,
            source_binding_id=value.source_binding_id,
            logical_reactor_root=value.logical_reactor_root,
            evaluation_context_ref=value.evaluation_context_ref,
            evaluation_context_digest=value.evaluation_context_digest,
            canonicalization_ref=value.canonicalization_ref,
            canonicalization_digest=value.canonicalization_digest,
            knowledge_context_digest=value.knowledge_context_digest,
            member_manifest_digest=value.member_manifest_digest,
            comparison_basis_digest=value.comparison_basis_digest,
            binding_digest=value.digest,
        )
        result.require_valid()
        return result

    def require_valid(self) -> None:
        if self.coverage_root_id.kind != "coverage_root" or self.coverage_state_id.kind != "coverage_state":
            raise _invalid("READ_SET_COVERAGE_ID_INVALID", "Catalog Coverage identity is invalid")
        if self.source_binding_id.kind != "binding":
            raise _invalid("READ_SET_SOURCE_BINDING_INVALID", "Catalog Coverage requires a Source Binding")
        for value, label in (
            (self.coverage_root_ref, "Coverage ref"),
            (self.profile_ref, "Profile ref"),
            (self.schema_ref, "Schema ref"),
            (self.logical_reactor_root, "logical reactor root"),
            (self.evaluation_context_ref, "Evaluation Context ref"),
            (self.canonicalization_ref, "Canonicalization ref"),
        ):
            _text(value, label)

    def canonical_value(self) -> dict[str, object]:
        return {
            "coverage_root_id": self.coverage_root_id.value,
            "coverage_root_digest": self.coverage_root_digest.value,
            "coverage_root_ref": self.coverage_root_ref,
            "coverage_state_id": self.coverage_state_id.value,
            "coverage_state_digest": self.coverage_state_digest.value,
            "profile_ref": self.profile_ref,
            "schema_ref": self.schema_ref,
            "schema_digest": self.schema_digest.value,
            "source_binding_id": self.source_binding_id.value,
            "logical_reactor_root": self.logical_reactor_root,
            "evaluation_context_ref": self.evaluation_context_ref,
            "evaluation_context_digest": self.evaluation_context_digest.value,
            "canonicalization_ref": self.canonicalization_ref,
            "canonicalization_digest": self.canonicalization_digest.value,
            "knowledge_context_digest": self.knowledge_context_digest.value,
            "member_manifest_digest": self.member_manifest_digest.value,
            "comparison_basis_digest": self.comparison_basis_digest.value,
            "binding_digest": self.binding_digest.value,
        }


@dataclass(frozen=True, slots=True)
class CatalogSnapshotBinding:
    ordinal: int
    snapshot_id: StableId
    source_revision: str
    snapshot_manifest_digest: Digest
    schema_ref: str
    schema_digest: Digest
    schema_registration_digest: Digest
    schema_availability_digest: Digest
    schema_adoption_digest: Digest
    coverage_set_digest: Digest
    binding_digest: Digest
    coverages: tuple[CatalogCoverageBinding, ...]

    @classmethod
    def from_binding(cls, ordinal: int, value: StructureSnapshotReadBinding) -> "CatalogSnapshotBinding":
        value.require_valid()
        source_revisions = {item.source_revision for item in value.coverages}
        if len(source_revisions) != 1:
            raise _invalid(
                "READ_SET_SOURCE_REVISION_AMBIGUOUS",
                "one Catalog Snapshot binding must have one exact source revision",
            )
        result = cls(
            ordinal=ordinal,
            snapshot_id=value.snapshot_id,
            source_revision=next(iter(source_revisions)),
            snapshot_manifest_digest=value.snapshot_manifest_digest,
            schema_ref=value.schema_ref,
            schema_digest=value.schema_digest,
            schema_registration_digest=value.schema_registration_digest,
            schema_availability_digest=value.schema_availability_digest,
            schema_adoption_digest=value.schema_adoption_digest,
            coverage_set_digest=value.coverage_set_digest,
            binding_digest=value.digest,
            coverages=tuple(CatalogCoverageBinding.from_binding(item) for item in value.coverages),
        )
        result.require_valid()
        return result

    def require_valid(self) -> None:
        if type(self.ordinal) is not int or self.ordinal < 0:
            raise _invalid("READ_SET_SNAPSHOT_ORDINAL_INVALID", "Catalog Snapshot ordinal is invalid")
        if self.snapshot_id.kind != "structure_snapshot":
            raise _invalid("READ_SET_SNAPSHOT_ID_INVALID", "Catalog Snapshot ID is invalid")
        if not _COMMIT_RE.fullmatch(self.source_revision):
            raise _invalid("READ_SET_SOURCE_REVISION_INVALID", "Catalog source revision must be an exact full Git commit")
        _text(self.schema_ref, "Schema ref")
        if not self.coverages:
            raise _invalid("READ_SET_COVERAGE_REQUIRED", "Catalog Snapshot requires Coverage")
        for coverage in self.coverages:
            coverage.require_valid()
            if coverage.schema_ref != self.schema_ref or coverage.schema_digest != self.schema_digest:
                raise _invalid("READ_SET_COVERAGE_SCHEMA_MISMATCH", "Catalog Snapshot and Coverage schema differ")

    def canonical_value(self) -> dict[str, object]:
        return {
            "ordinal": self.ordinal,
            "snapshot_id": self.snapshot_id.value,
            "source_revision": self.source_revision,
            "snapshot_manifest_digest": self.snapshot_manifest_digest.value,
            "schema_ref": self.schema_ref,
            "schema_digest": self.schema_digest.value,
            "schema_registration_digest": self.schema_registration_digest.value,
            "schema_availability_digest": self.schema_availability_digest.value,
            "schema_adoption_digest": self.schema_adoption_digest.value,
            "coverage_set_digest": self.coverage_set_digest.value,
            "binding_digest": self.binding_digest.value,
            "coverages": tuple(item.canonical_value() for item in self.coverages),
        }


@dataclass(frozen=True, slots=True)
class ReadSetRegistration:
    read_set_id: StableId
    workspace_id: StableId
    workspace_version_ids: tuple[StableId, ...]
    scope_id: StableId
    scope_revision: Revision
    snapshot_bindings: tuple[CatalogSnapshotBinding, ...]
    session_id: StableId
    read_set_digest: Digest
    ordered_receipt: StructureReadBundleReceipt
    snapshot_receipts: tuple[StructureReadBundleReceipt, ...]
    bundle_locator: str
    file_manifest: tuple[ReadSetFile, ...]
    file_manifest_digest: Digest
    availability: ReadSetAvailability
    digest: Digest
    schema: str = READ_SET_REGISTRATION_SCHEMA

    @classmethod
    def create(
        cls,
        *,
        read_set_id: StableId,
        workspace_id: StableId,
        workspace_version_ids: tuple[StableId, ...],
        session: StructureReadSession,
        ordered_receipt: StructureReadBundleReceipt,
        snapshot_receipts: tuple[StructureReadBundleReceipt, ...],
        bundle_locator: str,
    ) -> "ReadSetRegistration":
        bindings = tuple(
            CatalogSnapshotBinding.from_binding(ordinal, item)
            for ordinal, item in enumerate(session.snapshots)
        )
        files = (
            ReadSetFile.from_receipt(
                ordinal=0,
                role=ReadSetFileRole.ORDERED_ENVELOPE,
                receipt=ordered_receipt,
            ),
            *tuple(
                ReadSetFile.from_receipt(
                    ordinal=ordinal,
                    role=ReadSetFileRole.SNAPSHOT,
                    receipt=receipt,
                )
                for ordinal, receipt in enumerate(snapshot_receipts)
            ),
        )
        manifest_digest = digest_of(
            ["SWM-READ-SET-FILE-MANIFEST@1", tuple(item.canonical_value() for item in files)]
        )
        core = read_set_registration_core(
            read_set_id=read_set_id,
            workspace_id=workspace_id,
            workspace_version_ids=workspace_version_ids,
            scope_id=session.scope_id,
            scope_revision=session.scope_revision,
            snapshot_bindings=bindings,
            session_id=session.session_id,
            read_set_digest=session.read_set_digest,
            ordered_receipt=ordered_receipt,
            snapshot_receipts=snapshot_receipts,
            bundle_locator=bundle_locator,
            file_manifest=files,
            file_manifest_digest=manifest_digest,
            availability=ReadSetAvailability.QUERYABLE,
        )
        value = cls(
            read_set_id=read_set_id,
            workspace_id=workspace_id,
            workspace_version_ids=workspace_version_ids,
            scope_id=session.scope_id,
            scope_revision=session.scope_revision,
            snapshot_bindings=bindings,
            session_id=session.session_id,
            read_set_digest=session.read_set_digest,
            ordered_receipt=ordered_receipt,
            snapshot_receipts=snapshot_receipts,
            bundle_locator=bundle_locator,
            file_manifest=files,
            file_manifest_digest=manifest_digest,
            availability=ReadSetAvailability.QUERYABLE,
            digest=digest_of([READ_SET_REGISTRATION_SCHEMA, core]),
        )
        value.require_valid()
        return value

    def require_valid(self) -> None:
        if self.schema != READ_SET_REGISTRATION_SCHEMA:
            raise _invalid("READ_SET_REGISTRATION_SCHEMA_INVALID", "Read Set registration schema is unsupported")
        if self.read_set_id.kind != "read_set" or self.workspace_id.kind != "maven_workspace":
            raise _invalid("READ_SET_REGISTRATION_ID_INVALID", "Read Set registration identity is invalid")
        if (
            not self.workspace_version_ids
            or any(item.kind != "workspace_version" for item in self.workspace_version_ids)
            or len(set(self.workspace_version_ids)) != len(self.workspace_version_ids)
        ):
            raise _invalid("READ_SET_WORKSPACE_VERSION_INVALID", "Read Set requires exact Workspace Versions")
        if len(self.workspace_version_ids) != len(self.snapshot_bindings):
            raise _invalid("READ_SET_VERSION_SNAPSHOT_MISMATCH", "Workspace Version and Snapshot order differ")
        if self.scope_id.kind != "scope" or self.session_id.kind != "structure_read_session":
            raise _invalid("READ_SET_AUTHORITY_ID_INVALID", "Read Set Scope or Session identity is invalid")
        if (
            not self.snapshot_bindings
            or tuple(item.ordinal for item in self.snapshot_bindings)
            != tuple(range(len(self.snapshot_bindings)))
            or len({item.snapshot_id for item in self.snapshot_bindings})
            != len(self.snapshot_bindings)
        ):
            raise _invalid("READ_SET_SNAPSHOT_ORDER_INVALID", "Read Set Snapshot order is not contiguous")
        for item in self.snapshot_bindings:
            item.require_valid()
        if any(item.snapshot_id not in self.ordered_receipt.snapshot_ids for item in self.snapshot_bindings):
            raise _invalid("READ_SET_RECEIPT_SNAPSHOT_MISMATCH", "ordered Receipt omits a registered Snapshot")
        expected_snapshot_ids = tuple(item.snapshot_id for item in self.snapshot_bindings)
        self.ordered_receipt.require_valid()
        if (
            self.ordered_receipt.kind is not StructureReadBundleKind.ORDERED_READ_SET
            or self.ordered_receipt.scope_id != self.scope_id
            or self.ordered_receipt.snapshot_ids != expected_snapshot_ids
            or self.ordered_receipt.session_id != self.session_id
            or self.ordered_receipt.read_set_digest != self.read_set_digest
        ):
            raise _invalid("READ_SET_ORDERED_RECEIPT_INVALID", "Read Set ordered Receipt binding is invalid")
        if len(self.snapshot_receipts) != len(expected_snapshot_ids):
            raise _invalid("READ_SET_SNAPSHOT_RECEIPTS_INCOMPLETE", "Read Set Snapshot Receipts are incomplete")
        for snapshot_id, receipt in zip(expected_snapshot_ids, self.snapshot_receipts):
            receipt.require_valid()
            if (
                receipt.kind is not StructureReadBundleKind.SNAPSHOT
                or receipt.scope_id != self.scope_id
                or receipt.snapshot_ids != (snapshot_id,)
            ):
                raise _invalid("READ_SET_SNAPSHOT_RECEIPT_INVALID", "Read Set Snapshot Receipt is not exact")
        directory = _relative_locator(self.bundle_locator, "Read Set Bundle locator")
        expected_files = (
            ReadSetFile.from_receipt(ordinal=0, role=ReadSetFileRole.ORDERED_ENVELOPE, receipt=self.ordered_receipt),
            *tuple(
                ReadSetFile.from_receipt(ordinal=ordinal, role=ReadSetFileRole.SNAPSHOT, receipt=receipt)
                for ordinal, receipt in enumerate(self.snapshot_receipts)
            ),
        )
        if self.file_manifest != expected_files:
            raise _invalid("READ_SET_FILE_MANIFEST_MISMATCH", "Read Set file manifest differs from exact Receipts")
        for item in self.file_manifest:
            item.require_valid()
            if not _is_child_locator(directory, item.locator):
                raise _invalid("READ_SET_FILE_OUTSIDE_BUNDLE", "Read Set file is outside its immutable Bundle directory")
        expected_manifest_digest = digest_of(
            ["SWM-READ-SET-FILE-MANIFEST@1", tuple(item.canonical_value() for item in self.file_manifest)]
        )
        if self.file_manifest_digest != expected_manifest_digest:
            raise _invalid("READ_SET_FILE_MANIFEST_DIGEST_MISMATCH", "Read Set file manifest digest is not canonical")
        if self.availability is not ReadSetAvailability.QUERYABLE:
            raise _invalid("READ_SET_NOT_QUERYABLE", "Catalog registration must be queryable")
        core = read_set_registration_core(
            read_set_id=self.read_set_id,
            workspace_id=self.workspace_id,
            workspace_version_ids=self.workspace_version_ids,
            scope_id=self.scope_id,
            scope_revision=self.scope_revision,
            snapshot_bindings=self.snapshot_bindings,
            session_id=self.session_id,
            read_set_digest=self.read_set_digest,
            ordered_receipt=self.ordered_receipt,
            snapshot_receipts=self.snapshot_receipts,
            bundle_locator=self.bundle_locator,
            file_manifest=self.file_manifest,
            file_manifest_digest=self.file_manifest_digest,
            availability=self.availability,
        )
        if self.digest != digest_of([READ_SET_REGISTRATION_SCHEMA, core]):
            raise _invalid("READ_SET_REGISTRATION_DIGEST_MISMATCH", "Read Set registration digest is not canonical")

    def document(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            **read_set_registration_core(
                read_set_id=self.read_set_id,
                workspace_id=self.workspace_id,
                workspace_version_ids=self.workspace_version_ids,
                scope_id=self.scope_id,
                scope_revision=self.scope_revision,
                snapshot_bindings=self.snapshot_bindings,
                session_id=self.session_id,
                read_set_digest=self.read_set_digest,
                ordered_receipt=self.ordered_receipt,
                snapshot_receipts=self.snapshot_receipts,
                bundle_locator=self.bundle_locator,
                file_manifest=self.file_manifest,
                file_manifest_digest=self.file_manifest_digest,
                availability=self.availability,
            ),
            "registration_digest": self.digest.value,
        }

    def catalog_entry(self) -> dict[str, object]:
        return {
            "read_set_id": self.read_set_id.value,
            "workspace_id": self.workspace_id.value,
            "workspace_version_ids": tuple(item.value for item in self.workspace_version_ids),
            "scope_id": self.scope_id.value,
            "scope_revision": self.scope_revision.value,
            "snapshot_bindings": tuple(item.canonical_value() for item in self.snapshot_bindings),
            "session_id": self.session_id.value,
            "read_set_digest": self.read_set_digest.value,
            "ordered_receipt": _receipt_value(self.ordered_receipt),
            "snapshot_receipts": tuple(_receipt_value(item) for item in self.snapshot_receipts),
            "bundle_locator": self.bundle_locator,
            "file_manifest": tuple(item.canonical_value() for item in self.file_manifest),
            "file_manifest_digest": self.file_manifest_digest.value,
            "availability": self.availability.value,
            "registration_digest": self.digest.value,
        }


@dataclass(frozen=True, slots=True)
class ReadSetCatalog:
    catalog_id: StableId
    revision: Revision
    producer_commit: str
    producer_tree: str
    generated_at: datetime
    entries: tuple[ReadSetRegistration, ...]
    previous_catalog_digest: Digest | None
    document_digest: Digest
    schema: str = READ_SET_CATALOG_SCHEMA

    @classmethod
    def create(
        cls,
        *,
        catalog_id: StableId,
        revision: Revision,
        producer_commit: str,
        producer_tree: str,
        generated_at: datetime,
        entries: tuple[ReadSetRegistration, ...],
        previous_catalog_digest: Digest | None,
    ) -> "ReadSetCatalog":
        normalized = tuple(sorted(entries, key=lambda item: item.read_set_id.value))
        core = read_set_catalog_core(
            catalog_id=catalog_id,
            revision=revision,
            producer_commit=producer_commit,
            producer_tree=producer_tree,
            generated_at=generated_at,
            entries=normalized,
            previous_catalog_digest=previous_catalog_digest,
        )
        value = cls(
            catalog_id=catalog_id,
            revision=revision,
            producer_commit=producer_commit,
            producer_tree=producer_tree,
            generated_at=generated_at,
            entries=normalized,
            previous_catalog_digest=previous_catalog_digest,
            document_digest=digest_of([READ_SET_CATALOG_SCHEMA, core]),
        )
        value.require_valid()
        return value

    def require_valid(self) -> None:
        if self.schema != READ_SET_CATALOG_SCHEMA or self.catalog_id.kind != "read_set_catalog":
            raise _invalid("READ_SET_CATALOG_ID_INVALID", "Read Set Catalog identity or schema is invalid")
        if not _COMMIT_RE.fullmatch(self.producer_commit) or not _COMMIT_RE.fullmatch(self.producer_tree):
            raise _invalid("READ_SET_CATALOG_PRODUCER_INVALID", "Catalog producer commit/tree must be exact Git identities")
        if (self.revision.value == 1) != (self.previous_catalog_digest is None):
            raise _invalid(
                "READ_SET_CATALOG_CHAIN_INVALID",
                "Catalog revision and previous digest do not form a canonical chain",
            )
        _aware_time(self.generated_at, "Catalog generated time")
        expected_entries = tuple(sorted(self.entries, key=lambda item: item.read_set_id.value))
        if self.entries != expected_entries or len({item.read_set_id for item in self.entries}) != len(self.entries):
            raise _invalid("READ_SET_CATALOG_ENTRY_SET_INVALID", "Catalog entries must be sorted and unique")
        for entry in self.entries:
            entry.require_valid()
        core = read_set_catalog_core(
            catalog_id=self.catalog_id,
            revision=self.revision,
            producer_commit=self.producer_commit,
            producer_tree=self.producer_tree,
            generated_at=self.generated_at,
            entries=self.entries,
            previous_catalog_digest=self.previous_catalog_digest,
        )
        if self.document_digest != digest_of([READ_SET_CATALOG_SCHEMA, core]):
            raise _invalid("READ_SET_CATALOG_DIGEST_MISMATCH", "Catalog document digest is not canonical")

    @property
    def entry_set_digest(self) -> Digest:
        return digest_of(["SWM-READ-SET-CATALOG-ENTRY-SET@1", tuple(item.digest.value for item in self.entries)])

    def document(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            **read_set_catalog_core(
                catalog_id=self.catalog_id,
                revision=self.revision,
                producer_commit=self.producer_commit,
                producer_tree=self.producer_tree,
                generated_at=self.generated_at,
                entries=self.entries,
                previous_catalog_digest=self.previous_catalog_digest,
            ),
            "document_digest": self.document_digest.value,
        }


@dataclass(frozen=True, slots=True)
class ReadSetCatalogPointer:
    catalog_id: StableId
    revision: Revision
    catalog_digest: Digest

    @classmethod
    def from_catalog(cls, catalog: ReadSetCatalog) -> "ReadSetCatalogPointer":
        catalog.require_valid()
        return cls(catalog.catalog_id, catalog.revision, catalog.document_digest)

    def require_valid(self) -> None:
        if self.catalog_id.kind != "read_set_catalog":
            raise _invalid("READ_SET_CATALOG_POINTER_INVALID", "Catalog pointer ID is invalid")

    def document(self) -> dict[str, object]:
        return {
            "catalog_id": self.catalog_id.value,
            "revision": self.revision.value,
            "catalog_digest": self.catalog_digest.value,
        }


@dataclass(frozen=True, slots=True)
class CatalogPublication:
    catalog_id: StableId
    revision: Revision
    catalog_digest: Digest
    entry_set_digest: Digest
    published_at: datetime
    digest: Digest

    @classmethod
    def create(cls, catalog: ReadSetCatalog, *, published_at: datetime) -> "CatalogPublication":
        core = {
            "catalog_id": catalog.catalog_id.value,
            "revision": catalog.revision.value,
            "catalog_digest": catalog.document_digest.value,
            "entry_set_digest": catalog.entry_set_digest.value,
            "published_at": published_at,
        }
        value = cls(
            catalog_id=catalog.catalog_id,
            revision=catalog.revision,
            catalog_digest=catalog.document_digest,
            entry_set_digest=catalog.entry_set_digest,
            published_at=published_at,
            digest=digest_of(["SWM-READ-SET-CATALOG-PUBLICATION@1", core]),
        )
        value.require_valid()
        return value

    def require_valid(self) -> None:
        if self.catalog_id.kind != "read_set_catalog":
            raise _invalid("READ_SET_CATALOG_PUBLICATION_ID_INVALID", "Catalog Publication identity is invalid")
        _aware_time(self.published_at, "Catalog publication time")
        core = {
            "catalog_id": self.catalog_id.value,
            "revision": self.revision.value,
            "catalog_digest": self.catalog_digest.value,
            "entry_set_digest": self.entry_set_digest.value,
            "published_at": self.published_at,
        }
        if self.digest != digest_of(["SWM-READ-SET-CATALOG-PUBLICATION@1", core]):
            raise _invalid("READ_SET_CATALOG_PUBLICATION_DIGEST_MISMATCH", "Catalog Publication digest is not canonical")


class ReadSetCatalogRepository(Protocol):
    def save_read_set(self, registration: ReadSetRegistration) -> ReadSetRegistration: ...
    def get_read_set(self, read_set_id: StableId) -> ReadSetRegistration: ...
    def list_read_sets(self, workspace_id: StableId | None = None) -> tuple[ReadSetRegistration, ...]: ...
    def get_or_create_catalog_id(self) -> StableId: ...
    def latest_catalog_publication(self) -> CatalogPublication | None: ...
    def save_catalog_publication(self, publication: CatalogPublication) -> CatalogPublication: ...


class ReadSetCatalogStore(Protocol):
    def read_pointer(self) -> ReadSetCatalogPointer | None: ...
    def read_catalog(self, pointer: ReadSetCatalogPointer, *, verify_files: bool) -> ReadSetCatalog: ...
    def publish(self, catalog: ReadSetCatalog, *, expected: ReadSetCatalogPointer | None) -> ReadSetCatalogPointer: ...


class ReadSetCatalogService:
    """Register exact Read Sets and publish deterministic immutable catalogs."""

    def __init__(
        self,
        repository: ReadSetCatalogRepository,
        store: ReadSetCatalogStore,
        *,
        producer_commit: str,
        producer_tree: str,
        id_generator: IdGenerator | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        if not _COMMIT_RE.fullmatch(producer_commit) or not _COMMIT_RE.fullmatch(producer_tree):
            raise _invalid("READ_SET_CATALOG_PRODUCER_INVALID", "Catalog producer commit/tree must be exact Git identities")
        self._repository = repository
        self._store = store
        self._producer_commit = producer_commit
        self._producer_tree = producer_tree
        self._ids = id_generator or Uuid4IdGenerator()
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def allocate_read_set_id(self) -> StableId:
        return self._ids.new("read_set")

    def register(
        self,
        *,
        read_set_id: StableId,
        workspace_id: StableId,
        workspace_version_ids: tuple[StableId, ...],
        session: StructureReadSession,
        ordered_receipt: StructureReadBundleReceipt,
        snapshot_receipts: tuple[StructureReadBundleReceipt, ...],
        bundle_locator: str,
    ) -> ReadSetRegistration:
        value = ReadSetRegistration.create(
            read_set_id=read_set_id,
            workspace_id=workspace_id,
            workspace_version_ids=workspace_version_ids,
            session=session,
            ordered_receipt=ordered_receipt,
            snapshot_receipts=snapshot_receipts,
            bundle_locator=bundle_locator,
        )
        saved = self._repository.save_read_set(value)
        saved.require_valid()
        return saved

    def get(self, read_set_id: StableId) -> ReadSetRegistration:
        value = self._repository.get_read_set(read_set_id)
        value.require_valid()
        return value

    def list(self, workspace_id: StableId | None = None) -> tuple[ReadSetRegistration, ...]:
        values = self._repository.list_read_sets(workspace_id)
        for value in values:
            value.require_valid()
        return values

    def publish(self) -> tuple[ReadSetCatalog, ReadSetCatalogPointer]:
        entries = self._repository.list_read_sets()
        for entry in entries:
            entry.require_valid()
        entry_set_digest = digest_of(
            ["SWM-READ-SET-CATALOG-ENTRY-SET@1", tuple(item.digest.value for item in entries)]
        )
        pointer = self._store.read_pointer()
        latest = self._repository.latest_catalog_publication()
        catalog_id = self._repository.get_or_create_catalog_id()
        if latest is not None and latest.catalog_id != catalog_id:
            raise _inconsistent(
                "Catalog publication authority has another stable Catalog identity"
            )
        if pointer is not None and pointer.catalog_id != catalog_id:
            raise _inconsistent(
                "Catalog pointer has another stable Catalog identity"
            )
        if pointer is not None:
            current = self._store.read_catalog(pointer, verify_files=True)
            if latest is None:
                if pointer.revision.value != 1:
                    raise _inconsistent(
                        "Catalog pointer is separated from Application publication history"
                    )
                latest = self._repository.save_catalog_publication(
                    CatalogPublication.create(
                        current, published_at=current.generated_at
                    )
                )
            elif latest.revision == pointer.revision:
                if (
                    latest.catalog_digest != pointer.catalog_digest
                    or latest.entry_set_digest != current.entry_set_digest
                ):
                    raise _inconsistent(
                        "Catalog file pointer and Application publication authority disagree"
                    )
            elif latest.revision.value + 1 == pointer.revision.value:
                if current.previous_catalog_digest != latest.catalog_digest:
                    raise _inconsistent(
                        "Catalog pointer does not continue Application publication history"
                    )
                # Recover the crash window after the immutable manifest and
                # current pointer were committed but before the authority receipt.
                latest = self._repository.save_catalog_publication(
                    CatalogPublication.create(
                        current, published_at=current.generated_at
                    )
                )
            else:
                raise _inconsistent(
                    "Catalog pointer and Application publication history are not contiguous"
                )
            if current.entry_set_digest == entry_set_digest:
                return current, pointer

        base_revision = max(
            pointer.revision.value if pointer is not None else 0,
            latest.revision.value if latest is not None else 0,
        )
        previous_digest = (
            pointer.catalog_digest
            if pointer is not None
            else latest.catalog_digest if latest is not None else None
        )
        generated_at = max(
            (item.ordered_receipt.created_at for item in entries),
            default=self._now(),
        )
        catalog = ReadSetCatalog.create(
            catalog_id=catalog_id,
            revision=Revision(base_revision + 1),
            producer_commit=self._producer_commit,
            producer_tree=self._producer_tree,
            generated_at=generated_at,
            entries=entries,
            previous_catalog_digest=previous_digest,
        )
        new_pointer = self._store.publish(catalog, expected=pointer)
        publication = CatalogPublication.create(catalog, published_at=self._now())
        self._repository.save_catalog_publication(publication)
        return catalog, new_pointer

    def read_current_source_off(self) -> ReadSetCatalog:
        pointer = self._store.read_pointer()
        if pointer is None:
            raise _invalid("READ_SET_CATALOG_POINTER_NOT_FOUND", "Read Set Catalog current pointer was not found")
        return self._store.read_catalog(pointer, verify_files=True)

    def _now(self) -> datetime:
        return _aware_time(self._clock(), "Catalog clock").astimezone(timezone.utc)


def read_set_registration_core(
    *,
    read_set_id: StableId,
    workspace_id: StableId,
    workspace_version_ids: tuple[StableId, ...],
    scope_id: StableId,
    scope_revision: Revision,
    snapshot_bindings: tuple[CatalogSnapshotBinding, ...],
    session_id: StableId,
    read_set_digest: Digest,
    ordered_receipt: StructureReadBundleReceipt,
    snapshot_receipts: tuple[StructureReadBundleReceipt, ...],
    bundle_locator: str,
    file_manifest: tuple[ReadSetFile, ...],
    file_manifest_digest: Digest,
    availability: ReadSetAvailability,
) -> dict[str, object]:
    return {
        "read_set_id": read_set_id.value,
        "workspace_id": workspace_id.value,
        "workspace_version_ids": tuple(item.value for item in workspace_version_ids),
        "scope_id": scope_id.value,
        "scope_revision": scope_revision.value,
        "snapshot_bindings": tuple(item.canonical_value() for item in snapshot_bindings),
        "session_id": session_id.value,
        "read_set_digest": read_set_digest.value,
        "ordered_receipt": _receipt_value(ordered_receipt),
        "snapshot_receipts": tuple(_receipt_value(item) for item in snapshot_receipts),
        "bundle_locator": bundle_locator,
        "file_manifest": tuple(item.canonical_value() for item in file_manifest),
        "file_manifest_digest": file_manifest_digest.value,
        "availability": availability.value,
    }


def read_set_catalog_core(
    *,
    catalog_id: StableId,
    revision: Revision,
    producer_commit: str,
    producer_tree: str,
    generated_at: datetime,
    entries: tuple[ReadSetRegistration, ...],
    previous_catalog_digest: Digest | None,
) -> dict[str, object]:
    return {
        "catalog_id": catalog_id.value,
        "revision": revision.value,
        "producer_commit": producer_commit,
        "producer_tree": producer_tree,
        "generated_at": generated_at,
        "entries": tuple(item.catalog_entry() for item in entries),
        "previous_catalog_digest": previous_catalog_digest.value if previous_catalog_digest is not None else None,
    }


def read_set_registration_from_document(document: Mapping[str, object]) -> ReadSetRegistration:
    value = _object(
        document,
        {
            "schema", "read_set_id", "workspace_id", "workspace_version_ids", "scope_id",
            "scope_revision", "snapshot_bindings", "session_id", "read_set_digest",
            "ordered_receipt", "snapshot_receipts", "bundle_locator", "file_manifest",
            "file_manifest_digest", "availability", "registration_digest",
        },
        "Read Set registration",
    )
    if value["schema"] != READ_SET_REGISTRATION_SCHEMA:
        raise _invalid("READ_SET_REGISTRATION_SCHEMA_INVALID", "Read Set registration schema is unsupported")
    result = ReadSetRegistration(
        read_set_id=StableId(_string(value["read_set_id"], "Read Set ID")),
        workspace_id=StableId(_string(value["workspace_id"], "Workspace ID")),
        workspace_version_ids=tuple(StableId(_string(item, "Workspace Version ID")) for item in _array(value["workspace_version_ids"], "Workspace Versions")),
        scope_id=StableId(_string(value["scope_id"], "Scope ID")),
        scope_revision=Revision(_integer(value["scope_revision"], "Scope revision")),
        snapshot_bindings=tuple(_snapshot_binding(item) for item in _array(value["snapshot_bindings"], "Snapshot bindings")),
        session_id=StableId(_string(value["session_id"], "Session ID")),
        read_set_digest=Digest(_string(value["read_set_digest"], "Read Set digest")),
        ordered_receipt=_receipt(value["ordered_receipt"]),
        snapshot_receipts=tuple(_receipt(item) for item in _array(value["snapshot_receipts"], "Snapshot Receipts")),
        bundle_locator=_string(value["bundle_locator"], "Bundle locator"),
        file_manifest=tuple(_read_set_file(item) for item in _array(value["file_manifest"], "file manifest")),
        file_manifest_digest=Digest(_string(value["file_manifest_digest"], "file manifest digest")),
        availability=ReadSetAvailability(_string(value["availability"], "availability")),
        digest=Digest(_string(value["registration_digest"], "registration digest")),
    )
    result.require_valid()
    return result


def read_set_catalog_from_document(document: Mapping[str, object]) -> ReadSetCatalog:
    value = _object(
        document,
        {
            "schema", "catalog_id", "revision", "producer_commit", "producer_tree",
            "generated_at", "entries", "previous_catalog_digest", "document_digest",
        },
        "Read Set Catalog",
    )
    if value["schema"] != READ_SET_CATALOG_SCHEMA:
        raise _invalid("READ_SET_CATALOG_SCHEMA_INVALID", "Read Set Catalog schema is unsupported")
    entries = tuple(_registration_from_catalog_entry(item) for item in _array(value["entries"], "Catalog entries"))
    previous = value["previous_catalog_digest"]
    result = ReadSetCatalog(
        catalog_id=StableId(_string(value["catalog_id"], "Catalog ID")),
        revision=Revision(_integer(value["revision"], "Catalog revision")),
        producer_commit=_string(value["producer_commit"], "producer commit"),
        producer_tree=_string(value["producer_tree"], "producer tree"),
        generated_at=_time(value["generated_at"], "Catalog generated time"),
        entries=entries,
        previous_catalog_digest=Digest(_string(previous, "previous Catalog digest")) if previous is not None else None,
        document_digest=Digest(_string(value["document_digest"], "Catalog document digest")),
    )
    result.require_valid()
    return result


def read_set_catalog_pointer_from_document(document: Mapping[str, object]) -> ReadSetCatalogPointer:
    value = _object(document, {"catalog_id", "revision", "catalog_digest"}, "Catalog pointer")
    pointer = ReadSetCatalogPointer(
        catalog_id=StableId(_string(value["catalog_id"], "Catalog ID")),
        revision=Revision(_integer(value["revision"], "Catalog revision")),
        catalog_digest=Digest(_string(value["catalog_digest"], "Catalog digest")),
    )
    pointer.require_valid()
    return pointer


def _registration_from_catalog_entry(value: object) -> ReadSetRegistration:
    entry = _object(
        value,
        {
            "read_set_id", "workspace_id", "workspace_version_ids", "scope_id",
            "scope_revision", "snapshot_bindings", "session_id", "read_set_digest",
            "ordered_receipt", "snapshot_receipts", "bundle_locator", "file_manifest",
            "file_manifest_digest", "availability", "registration_digest",
        },
        "Catalog entry",
    )
    ordered = _receipt(entry["ordered_receipt"])
    snapshots = tuple(_receipt(item) for item in _array(entry["snapshot_receipts"], "Snapshot Receipts"))
    bindings = tuple(_snapshot_binding(item) for item in _array(entry["snapshot_bindings"], "Snapshot bindings"))
    files = tuple(_read_set_file(item) for item in _array(entry["file_manifest"], "file manifest"))
    registration_digest = Digest(_string(entry["registration_digest"], "registration digest"))
    result = ReadSetRegistration(
        read_set_id=StableId(_string(entry["read_set_id"], "Read Set ID")),
        workspace_id=StableId(_string(entry["workspace_id"], "Workspace ID")),
        workspace_version_ids=tuple(StableId(_string(item, "Workspace Version ID")) for item in _array(entry["workspace_version_ids"], "Workspace Versions")),
        scope_id=StableId(_string(entry["scope_id"], "Scope ID")),
        scope_revision=Revision(_integer(entry["scope_revision"], "Scope revision")),
        snapshot_bindings=bindings,
        session_id=StableId(_string(entry["session_id"], "Session ID")),
        read_set_digest=Digest(_string(entry["read_set_digest"], "Read Set digest")),
        ordered_receipt=ordered,
        snapshot_receipts=snapshots,
        bundle_locator=_string(entry["bundle_locator"], "Bundle locator"),
        file_manifest=files,
        file_manifest_digest=Digest(_string(entry["file_manifest_digest"], "file manifest digest")),
        availability=ReadSetAvailability(_string(entry["availability"], "availability")),
        digest=registration_digest,
    )
    result.require_valid()
    return result


def _receipt_value(receipt: StructureReadBundleReceipt) -> dict[str, object]:
    receipt.require_valid()
    return {
        **structure_read_bundle_receipt_core(
            receipt_id=receipt.receipt_id,
            idempotency_key=receipt.idempotency_key,
            kind=receipt.kind,
            request_digest=receipt.request_digest,
            scope_id=receipt.scope_id,
            snapshot_ids=receipt.snapshot_ids,
            session_id=receipt.session_id,
            read_set_digest=receipt.read_set_digest,
            stored_bundle=receipt.stored_bundle,
            created_at=receipt.created_at,
        ),
        "receipt_digest": receipt.digest.value,
    }


def _receipt(value: object) -> StructureReadBundleReceipt:
    item = _object(
        value,
        {
            "receipt_id", "idempotency_key", "kind", "request_digest", "scope_id",
            "snapshot_ids", "session_id", "read_set_digest", "stored_bundle",
            "created_at", "receipt_digest",
        },
        "Bundle Receipt",
    )
    stored = _object(item["stored_bundle"], {"locator", "format_ref", "bundle_digest", "file_digest"}, "stored Bundle")
    session_id = item["session_id"]
    read_set_digest = item["read_set_digest"]
    receipt = StructureReadBundleReceipt(
        receipt_id=StableId(_string(item["receipt_id"], "Receipt ID")),
        idempotency_key=IdempotencyKey(_string(item["idempotency_key"], "idempotency key")),
        kind=StructureReadBundleKind(_string(item["kind"], "Bundle kind")),
        request_digest=Digest(_string(item["request_digest"], "request digest")),
        scope_id=StableId(_string(item["scope_id"], "Scope ID")),
        snapshot_ids=tuple(StableId(_string(snapshot, "Snapshot ID")) for snapshot in _array(item["snapshot_ids"], "Snapshot IDs")),
        session_id=StableId(_string(session_id, "Session ID")) if session_id is not None else None,
        read_set_digest=Digest(_string(read_set_digest, "Read Set digest")) if read_set_digest is not None else None,
        stored_bundle=StoredStructureReadBundle(
            locator=_string(stored["locator"], "Bundle locator"),
            format_ref=_string(stored["format_ref"], "Bundle format"),
            bundle_digest=Digest(_string(stored["bundle_digest"], "Bundle digest")),
            file_digest=Digest(_string(stored["file_digest"], "file digest")),
        ),
        created_at=_time(item["created_at"], "Receipt time"),
        digest=Digest(_string(item["receipt_digest"], "Receipt digest")),
    )
    receipt.require_valid()
    _relative_locator(receipt.stored_bundle.locator, "Receipt Bundle locator")
    return receipt


def _snapshot_binding(value: object) -> CatalogSnapshotBinding:
    item = _object(
        value,
        {
            "ordinal", "snapshot_id", "source_revision", "snapshot_manifest_digest",
            "schema_ref", "schema_digest", "schema_registration_digest",
            "schema_availability_digest", "schema_adoption_digest", "coverage_set_digest",
            "binding_digest", "coverages",
        },
        "Catalog Snapshot binding",
    )
    result = CatalogSnapshotBinding(
        ordinal=_integer(item["ordinal"], "Snapshot ordinal"),
        snapshot_id=StableId(_string(item["snapshot_id"], "Snapshot ID")),
        source_revision=_string(item["source_revision"], "source revision"),
        snapshot_manifest_digest=Digest(_string(item["snapshot_manifest_digest"], "Snapshot manifest digest")),
        schema_ref=_string(item["schema_ref"], "Schema ref"),
        schema_digest=Digest(_string(item["schema_digest"], "Schema digest")),
        schema_registration_digest=Digest(_string(item["schema_registration_digest"], "Schema registration digest")),
        schema_availability_digest=Digest(_string(item["schema_availability_digest"], "Schema availability digest")),
        schema_adoption_digest=Digest(_string(item["schema_adoption_digest"], "Schema adoption digest")),
        coverage_set_digest=Digest(_string(item["coverage_set_digest"], "Coverage set digest")),
        binding_digest=Digest(_string(item["binding_digest"], "binding digest")),
        coverages=tuple(_coverage_binding(coverage) for coverage in _array(item["coverages"], "Coverage bindings")),
    )
    result.require_valid()
    return result


def _coverage_binding(value: object) -> CatalogCoverageBinding:
    item = _object(
        value,
        {
            "coverage_root_id", "coverage_root_digest", "coverage_root_ref",
            "coverage_state_id", "coverage_state_digest", "profile_ref", "schema_ref",
            "schema_digest", "source_binding_id", "logical_reactor_root",
            "evaluation_context_ref", "evaluation_context_digest", "canonicalization_ref",
            "canonicalization_digest", "knowledge_context_digest", "member_manifest_digest",
            "comparison_basis_digest", "binding_digest",
        },
        "Catalog Coverage binding",
    )
    result = CatalogCoverageBinding(
        coverage_root_id=StableId(_string(item["coverage_root_id"], "Coverage Root ID")),
        coverage_root_digest=Digest(_string(item["coverage_root_digest"], "Coverage Root digest")),
        coverage_root_ref=_string(item["coverage_root_ref"], "Coverage ref"),
        coverage_state_id=StableId(_string(item["coverage_state_id"], "Coverage State ID")),
        coverage_state_digest=Digest(_string(item["coverage_state_digest"], "Coverage State digest")),
        profile_ref=_string(item["profile_ref"], "Profile ref"),
        schema_ref=_string(item["schema_ref"], "Schema ref"),
        schema_digest=Digest(_string(item["schema_digest"], "Schema digest")),
        source_binding_id=StableId(_string(item["source_binding_id"], "Source Binding ID")),
        logical_reactor_root=_string(item["logical_reactor_root"], "logical reactor root"),
        evaluation_context_ref=_string(item["evaluation_context_ref"], "Evaluation Context ref"),
        evaluation_context_digest=Digest(_string(item["evaluation_context_digest"], "Evaluation Context digest")),
        canonicalization_ref=_string(item["canonicalization_ref"], "canonicalization ref"),
        canonicalization_digest=Digest(_string(item["canonicalization_digest"], "canonicalization digest")),
        knowledge_context_digest=Digest(_string(item["knowledge_context_digest"], "knowledge context digest")),
        member_manifest_digest=Digest(_string(item["member_manifest_digest"], "member manifest digest")),
        comparison_basis_digest=Digest(_string(item["comparison_basis_digest"], "comparison basis digest")),
        binding_digest=Digest(_string(item["binding_digest"], "binding digest")),
    )
    result.require_valid()
    return result


def _read_set_file(value: object) -> ReadSetFile:
    item = _object(value, {"ordinal", "role", "locator", "format_ref", "bundle_digest", "file_digest", "receipt_id", "receipt_digest"}, "Read Set file")
    result = ReadSetFile(
        ordinal=_integer(item["ordinal"], "file ordinal"),
        role=ReadSetFileRole(_string(item["role"], "file role")),
        locator=_string(item["locator"], "file locator"),
        format_ref=_string(item["format_ref"], "Bundle format"),
        bundle_digest=Digest(_string(item["bundle_digest"], "Bundle digest")),
        file_digest=Digest(_string(item["file_digest"], "file digest")),
        receipt_id=StableId(_string(item["receipt_id"], "Receipt ID")),
        receipt_digest=Digest(_string(item["receipt_digest"], "Receipt digest")),
    )
    result.require_valid()
    return result


def _object(value: object, allowed: set[str], label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping) or any(not isinstance(key, str) for key in value):
        raise _invalid("READ_SET_CATALOG_DOCUMENT_INVALID", f"{label} must be an object")
    if set(value) != allowed:
        raise _invalid("READ_SET_CATALOG_FIELDS_INVALID", f"{label} has missing or extra fields")
    return value


def _array(value: object, label: str) -> Sequence[object]:
    if not isinstance(value, list):
        raise _invalid("READ_SET_CATALOG_DOCUMENT_INVALID", f"{label} must be an array")
    return value


def _string(value: object, label: str) -> str:
    if not isinstance(value, str):
        raise _invalid("READ_SET_CATALOG_DOCUMENT_INVALID", f"{label} must be text")
    return value


def _integer(value: object, label: str) -> int:
    if type(value) is not int:
        raise _invalid("READ_SET_CATALOG_DOCUMENT_INVALID", f"{label} must be an integer")
    return value


def _time(value: object, label: str) -> datetime:
    text = _string(value, label)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as error:
        raise _invalid("READ_SET_CATALOG_TIME_INVALID", f"{label} is invalid") from error
    return _aware_time(parsed, label)


def _aware_time(value: datetime, label: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise _invalid("READ_SET_CATALOG_TIME_INVALID", f"{label} must include a timezone")
    return value


def _text(value: str, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip() or len(value.encode("utf-8")) > 512:
        raise _invalid("READ_SET_CATALOG_TEXT_INVALID", f"{label} is invalid")
    return value


def _relative_locator(value: str, label: str) -> str:
    text = _text(value, label)
    if "\\" in text or text.startswith("/") or text.endswith("/"):
        raise _invalid("READ_SET_LOCATOR_INVALID", f"{label} must be a normalized relative POSIX path")
    parts = text.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise _invalid("READ_SET_LOCATOR_INVALID", f"{label} must be a normalized relative POSIX path")
    return text


def _is_child_locator(directory: str, locator: str) -> bool:
    return locator.startswith(directory + "/") and "/" not in locator[len(directory) + 1 :]


def _invalid(reason_code: str, message: str) -> DomainError:
    return DomainError(ErrorCode.INVALID_ARGUMENT, message, {"reason_code": reason_code})


def _inconsistent(message: str) -> DomainError:
    return DomainError(ErrorCode.AUTHORITY_RECORD_INCONSISTENT, message)


__all__ = [
    "CatalogPublication",
    "ReadSetAvailability",
    "ReadSetCatalog",
    "ReadSetCatalogPointer",
    "ReadSetCatalogRepository",
    "ReadSetCatalogService",
    "ReadSetCatalogStore",
    "ReadSetFile",
    "ReadSetFileRole",
    "ReadSetRegistration",
    "READ_SET_CATALOG_SCHEMA",
    "read_set_catalog_from_document",
    "read_set_catalog_pointer_from_document",
    "read_set_registration_from_document",
]
