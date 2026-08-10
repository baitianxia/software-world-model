"""Sealed, one-way citation projection for Structure View results.

The trusted broker accepts the actual typed Structure View Result, derives its
no-payload citation seal, and copies only that Result's exact Knowledge-owned
observations into a disposable store.  The projector consumes the derived seal
and that store; it has no Query, Update, model, network, or answer-return
capability.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Protocol, Sequence

from software_world_model.cross_cutting import (
    Digest,
    DomainError,
    ErrorCode,
    StableId,
    digest_of,
)
from software_world_model.knowledge_engine.structure import StructureEvidence
from software_world_model.knowledge_engine.structure_publication import (
    StructureEvidenceMetadata,
)
from software_world_model.application_services.structure_view import (
    StructureViewResult,
)


_RESULT_KIND = "STRUCTURE_VIEW_RESULT@1"


@dataclass(frozen=True, slots=True)
class CitationEvidenceReference:
    """No-payload Evidence identity sealed into a Structure View Result."""

    evidence_id: StableId
    artifact_id: StableId
    source_context_id: StableId
    byte_start: int
    byte_end: int
    locator: str
    excerpt_digest: Digest
    artifact_content_digest: Digest
    evidence_digest: Digest

    @classmethod
    def from_metadata(
        cls, metadata: StructureEvidenceMetadata
    ) -> "CitationEvidenceReference":
        return cls(
            evidence_id=metadata.evidence_id,
            artifact_id=metadata.artifact_id,
            source_context_id=metadata.source_context_id,
            byte_start=metadata.byte_start,
            byte_end=metadata.byte_end,
            locator=metadata.locator,
            excerpt_digest=metadata.excerpt_digest,
            artifact_content_digest=metadata.artifact_content_digest,
            evidence_digest=metadata.digest,
        )

    def require_valid(self) -> None:
        if self.evidence_id.kind != "evidence":
            _invalid(
                "CITATION_EVIDENCE_ID_INVALID",
                "Citation Evidence ID has the wrong kind",
            )
        _typed(self.artifact_id, StableId, "Citation Artifact ID")
        _typed(self.source_context_id, StableId, "Citation Source Context ID")
        for value, label in (
            (self.excerpt_digest, "Citation excerpt digest"),
            (self.artifact_content_digest, "Citation Artifact content digest"),
            (self.evidence_digest, "Citation Evidence digest"),
        ):
            _typed(value, Digest, label)
        if (
            type(self.byte_start) is not int
            or type(self.byte_end) is not int
            or self.byte_start < 0
            or self.byte_end <= self.byte_start
        ):
            _invalid(
                "CITATION_EVIDENCE_RANGE_INVALID",
                "Citation Evidence range must be non-empty and ordered",
            )
        _text(self.locator, "Citation Evidence locator")
        expected_digest = digest_of(self.identity_fields)
        expected_id = StableId(
            "evidence_"
            + expected_digest.value.removeprefix("sha256:")[-32:]
        )
        if (
            self.evidence_digest != expected_digest
            or self.evidence_id != expected_id
        ):
            _inconsistent(
                "CITATION_EVIDENCE_REFERENCE_NONCANONICAL",
                "Citation Evidence reference is not the canonical Knowledge identity",
                evidence_id=self.evidence_id.value,
            )

    @property
    def identity_fields(self) -> Mapping[str, object]:
        return {
            "artifact_id": self.artifact_id.value,
            "source_context_id": self.source_context_id.value,
            "byte_start": self.byte_start,
            "byte_end": self.byte_end,
            "locator": self.locator,
            "excerpt_digest": self.excerpt_digest.value,
            "artifact_content_digest": self.artifact_content_digest.value,
        }


@dataclass(frozen=True, slots=True)
class StructureViewResultSeal:
    """Citation-facing seal over one immutable Structure View Result."""

    result_id: StableId
    result_kind: str
    view_digest: Digest
    evidence_allowlist: tuple[CitationEvidenceReference, ...]
    allowlist_digest: Digest
    digest: Digest

    @classmethod
    def seal(
        cls,
        *,
        result_id: StableId,
        view_digest: Digest,
        evidence_allowlist: Sequence[CitationEvidenceReference],
    ) -> "StructureViewResultSeal":
        entries = tuple(evidence_allowlist)
        for entry in entries:
            if not isinstance(entry, CitationEvidenceReference):
                _invalid(
                    "CITATION_ALLOWLIST_ENTRY_INVALID",
                    "Citation allowlist entries must be typed Evidence references",
                )
            entry.require_valid()
        _require_canonical_allowlist(entries)
        allowlist_digest = citation_allowlist_digest(entries)
        seal_digest = structure_view_result_seal_digest(
            result_id=result_id,
            result_kind=_RESULT_KIND,
            view_digest=view_digest,
            evidence_allowlist=entries,
            allowlist_digest=allowlist_digest,
        )
        result = cls(
            result_id=result_id,
            result_kind=_RESULT_KIND,
            view_digest=view_digest,
            evidence_allowlist=entries,
            allowlist_digest=allowlist_digest,
            digest=seal_digest,
        )
        result.require_valid()
        return result

    def require_valid(self) -> None:
        if self.result_id.kind != "structure_view_result":
            _invalid(
                "CITATION_RESULT_ID_INVALID",
                "Citation seal requires a Structure View Result ID",
            )
        if self.result_kind != _RESULT_KIND:
            _invalid(
                "CITATION_RESULT_KIND_INVALID",
                "Citation seal has an unsupported Result kind",
            )
        _typed(self.view_digest, Digest, "Structure View digest")
        _typed(self.allowlist_digest, Digest, "Citation allowlist digest")
        _typed(self.digest, Digest, "Structure View Result seal digest")
        if not isinstance(self.evidence_allowlist, tuple):
            _invalid(
                "CITATION_ALLOWLIST_NOT_TUPLE",
                "Citation Evidence allowlist must be immutable",
            )
        for entry in self.evidence_allowlist:
            if not isinstance(entry, CitationEvidenceReference):
                _invalid(
                    "CITATION_ALLOWLIST_ENTRY_INVALID",
                    "Citation allowlist entries must be typed Evidence references",
                )
            entry.require_valid()
        _require_canonical_allowlist(self.evidence_allowlist)
        if citation_allowlist_digest(self.evidence_allowlist) != self.allowlist_digest:
            _inconsistent(
                "CITATION_ALLOWLIST_DIGEST_MISMATCH",
                "Citation Evidence allowlist digest is not canonical",
            )
        expected = structure_view_result_seal_digest(
            result_id=self.result_id,
            result_kind=self.result_kind,
            view_digest=self.view_digest,
            evidence_allowlist=self.evidence_allowlist,
            allowlist_digest=self.allowlist_digest,
        )
        if expected != self.digest:
            _inconsistent(
                "CITATION_RESULT_SEAL_DIGEST_MISMATCH",
                "Structure View Result citation seal is not canonical",
            )


@dataclass(frozen=True, slots=True)
class CitationObservation:
    """Self-contained Knowledge observation copied into the disposable store."""

    reference: CitationEvidenceReference
    excerpt: str
    digest: Digest

    @classmethod
    def from_evidence(cls, evidence: StructureEvidence) -> "CitationObservation":
        if not isinstance(evidence, StructureEvidence):
            _invalid(
                "CITATION_OBSERVATION_TYPE_INVALID",
                "Knowledge owner returned an invalid Evidence observation",
            )
        evidence.require_valid_identity()
        reference = CitationEvidenceReference.from_metadata(
            StructureEvidenceMetadata.from_evidence(evidence)
        )
        return cls(
            reference=reference,
            excerpt=evidence.excerpt,
            digest=citation_observation_digest(reference, evidence.excerpt),
        )

    def require_valid(self) -> None:
        if not isinstance(self.reference, CitationEvidenceReference):
            _invalid(
                "CITATION_OBSERVATION_REFERENCE_INVALID",
                "Citation observation requires a typed Evidence reference",
            )
        self.reference.require_valid()
        if not isinstance(self.excerpt, str):
            _invalid(
                "CITATION_OBSERVATION_TEXT_INVALID",
                "Citation observation must be exact UTF-8 text",
            )
        try:
            excerpt_bytes = self.excerpt.encode("utf-8")
        except UnicodeEncodeError as exc:
            raise _invalid_error(
                "CITATION_OBSERVATION_TEXT_INVALID",
                "Citation observation must be exact UTF-8 text",
            ) from exc
        if (
            len(excerpt_bytes)
            != self.reference.byte_end - self.reference.byte_start
            or digest_of(self.excerpt) != self.reference.excerpt_digest
        ):
            _inconsistent(
                "CITATION_OBSERVATION_PAYLOAD_MISMATCH",
                "Citation observation differs from its sealed Evidence reference",
                evidence_id=self.reference.evidence_id.value,
            )
        if citation_observation_digest(self.reference, self.excerpt) != self.digest:
            _inconsistent(
                "CITATION_OBSERVATION_DIGEST_MISMATCH",
                "Citation observation digest is not canonical",
                evidence_id=self.reference.evidence_id.value,
            )


@dataclass(frozen=True, slots=True)
class CitationStoreReceipt:
    store_id: StableId
    result_id: StableId
    result_digest: Digest
    allowlist_digest: Digest
    manifest_digest: Digest
    observation_count: int
    disposable: bool

    def require_valid(self) -> None:
        if self.store_id.kind != "citation_store":
            _invalid("CITATION_STORE_ID_INVALID", "Citation Store ID has the wrong kind")
        if self.result_id.kind != "structure_view_result":
            _invalid("CITATION_RESULT_ID_INVALID", "Citation Store Result ID is invalid")
        for value, label in (
            (self.result_digest, "Citation Store Result digest"),
            (self.allowlist_digest, "Citation Store allowlist digest"),
            (self.manifest_digest, "Citation Store manifest digest"),
        ):
            _typed(value, Digest, label)
        if type(self.observation_count) is not int or self.observation_count < 0:
            _invalid(
                "CITATION_STORE_COUNT_INVALID",
                "Citation Store observation count is invalid",
            )
        if self.disposable is not True:
            _invalid(
                "CITATION_STORE_NOT_DISPOSABLE",
                "Citation Store must be explicitly disposable",
            )


@dataclass(frozen=True, slots=True)
class CitationStoreSnapshot:
    receipt: CitationStoreReceipt
    observations: tuple[CitationObservation, ...]

    def require_exact(self, result: StructureViewResultSeal) -> None:
        result.require_valid()
        self.receipt.require_valid()
        if (
            self.receipt.result_id != result.result_id
            or self.receipt.result_digest != result.digest
            or self.receipt.allowlist_digest != result.allowlist_digest
            or self.receipt.observation_count != len(self.observations)
        ):
            _inconsistent(
                "CITATION_STORE_RESULT_MISMATCH",
                "Citation Store is bound to another sealed Structure View Result",
            )
        if not isinstance(self.observations, tuple):
            _invalid(
                "CITATION_STORE_OBSERVATIONS_MUTABLE",
                "Citation Store observations must be immutable",
            )
        references: list[CitationEvidenceReference] = []
        for observation in self.observations:
            if not isinstance(observation, CitationObservation):
                _invalid(
                    "CITATION_STORE_OBSERVATION_INVALID",
                    "Citation Store contains an untyped observation",
                )
            observation.require_valid()
            references.append(observation.reference)
        actual = tuple(references)
        if actual != result.evidence_allowlist:
            _inconsistent(
                "CITATION_STORE_ALLOWLIST_MISMATCH",
                "Citation Store observations are missing, extra, duplicated, or reordered",
            )


class CitationKnowledgeObservationOwner(Protocol):
    """Narrow trusted broker port; it is not available to the projector."""

    def get_evidence(self, evidence_id: StableId) -> StructureEvidence: ...


class CitationStoreWriter(Protocol):
    def create_disposable_store(
        self,
        *,
        result: StructureViewResultSeal,
        observations: tuple[CitationObservation, ...],
    ) -> CitationStoreReceipt: ...


class CitationStoreReader(Protocol):
    def read_exact(
        self, result: StructureViewResultSeal
    ) -> CitationStoreSnapshot: ...


@dataclass(frozen=True, slots=True)
class CitationMaterialization:
    """One trusted derivation of a Citation seal and its exact Store Receipt."""

    seal: StructureViewResultSeal
    receipt: CitationStoreReceipt

    def require_valid(self) -> None:
        self.seal.require_valid()
        self.receipt.require_valid()
        if (
            self.receipt.result_id != self.seal.result_id
            or self.receipt.result_digest != self.seal.digest
            or self.receipt.allowlist_digest != self.seal.allowlist_digest
            or self.receipt.observation_count != len(self.seal.evidence_allowlist)
        ):
            _inconsistent(
                "CITATION_MATERIALIZATION_MISMATCH",
                "Citation materialization Receipt differs from its derived Result seal",
            )


class CitationObservationBroker:
    """Trusted one-way broker from Knowledge owner to disposable store."""

    def __init__(
        self,
        owner: CitationKnowledgeObservationOwner,
        writer: CitationStoreWriter,
    ) -> None:
        if not callable(getattr(owner, "get_evidence", None)):
            _invalid(
                "CITATION_KNOWLEDGE_OWNER_REQUIRED",
                "Citation broker requires the narrow Knowledge Evidence owner port",
            )
        if not callable(getattr(writer, "create_disposable_store", None)):
            _invalid(
                "CITATION_STORE_WRITER_REQUIRED",
                "Citation broker requires a disposable Store writer",
            )
        self._owner = owner
        self._writer = writer

    def materialize(self, result: StructureViewResult) -> CitationMaterialization:
        if not isinstance(result, StructureViewResult):
            _invalid(
                "CITATION_VIEW_RESULT_REQUIRED",
                "Citation broker requires the actual typed Structure View Result",
            )
        result.require_valid()
        seal = citation_seal_for_result(result)
        observations: list[CitationObservation] = []
        for expected in seal.evidence_allowlist:
            evidence = self._owner.get_evidence(expected.evidence_id)
            observation = CitationObservation.from_evidence(evidence)
            if observation.reference != expected:
                _inconsistent(
                    "CITATION_OWNER_OBSERVATION_MISMATCH",
                    "Knowledge owner observation differs from the sealed Result allowlist",
                    evidence_id=expected.evidence_id.value,
                )
            observations.append(observation)
        receipt = self._writer.create_disposable_store(
            result=seal,
            observations=tuple(observations),
        )
        if not isinstance(receipt, CitationStoreReceipt):
            _invalid(
                "CITATION_STORE_RECEIPT_INVALID",
                "Citation Store writer returned an invalid receipt",
            )
        receipt.require_valid()
        if (
            receipt.result_id != seal.result_id
            or receipt.result_digest != seal.digest
            or receipt.allowlist_digest != seal.allowlist_digest
            or receipt.observation_count != len(seal.evidence_allowlist)
        ):
            _inconsistent(
                "CITATION_STORE_RECEIPT_MISMATCH",
                "Citation Store receipt differs from the sealed Result",
            )
        materialization = CitationMaterialization(seal=seal, receipt=receipt)
        materialization.require_valid()
        return materialization


def citation_seal_for_result(
    result: StructureViewResult,
) -> StructureViewResultSeal:
    """Derive the only broker-eligible allowlist from an actual View Result."""

    if not isinstance(result, StructureViewResult):
        _invalid(
            "CITATION_VIEW_RESULT_REQUIRED",
            "Citation seal derivation requires an actual Structure View Result",
        )
    result.require_valid()
    references = tuple(
        CitationEvidenceReference.from_metadata(item)
        for item in result.citation_evidence_metadata()
    )
    if tuple(item.evidence_id for item in references) != result.evidence_allowlist:
        _inconsistent(
            "CITATION_VIEW_ALLOWLIST_MISMATCH",
            "Structure View Result metadata differs from its sealed Evidence allowlist",
        )
    return StructureViewResultSeal.seal(
        result_id=result.result_id,
        view_digest=result.digest,
        evidence_allowlist=references,
    )


@dataclass(frozen=True, slots=True)
class CitationDisplay:
    evidence_id: StableId
    artifact_id: StableId
    source_context_id: StableId
    locator: str
    byte_start: int
    byte_end: int
    observation: str
    excerpt_digest: Digest
    evidence_digest: Digest
    digest: Digest


@dataclass(frozen=True, slots=True)
class CitationProjection:
    result_id: StableId
    result_digest: Digest
    store_id: StableId
    store_manifest_digest: Digest
    citations: tuple[CitationDisplay, ...]
    digest: Digest


class CitationProjector:
    """Read-only browser-display projector with no answer-chain return port."""

    def __init__(self, store: CitationStoreReader) -> None:
        if not callable(getattr(store, "read_exact", None)):
            _invalid(
                "CITATION_STORE_READER_REQUIRED",
                "Citation Projector requires a read-only exact Store port",
            )
        self._store = store

    def project(self, result: StructureViewResultSeal) -> CitationProjection:
        if not isinstance(result, StructureViewResultSeal):
            _invalid(
                "CITATION_RESULT_SEAL_REQUIRED",
                "Citation Projector requires a typed sealed Structure View Result",
            )
        result.require_valid()
        snapshot = self._store.read_exact(result)
        if not isinstance(snapshot, CitationStoreSnapshot):
            _invalid(
                "CITATION_STORE_SNAPSHOT_INVALID",
                "Citation Store returned an invalid snapshot",
            )
        snapshot.require_exact(result)
        citations = tuple(_display(observation) for observation in snapshot.observations)
        projection_digest = digest_of(
            [
                "CITATION_BROWSER_PROJECTION@1",
                {
                    "result_id": result.result_id.value,
                    "result_digest": result.digest.value,
                    "store_id": snapshot.receipt.store_id.value,
                    "store_manifest_digest": snapshot.receipt.manifest_digest.value,
                    "citations": citations,
                },
            ]
        )
        return CitationProjection(
            result_id=result.result_id,
            result_digest=result.digest,
            store_id=snapshot.receipt.store_id,
            store_manifest_digest=snapshot.receipt.manifest_digest,
            citations=citations,
            digest=projection_digest,
        )


def citation_allowlist_digest(
    entries: Sequence[CitationEvidenceReference],
) -> Digest:
    return digest_of(["CITATION_EVIDENCE_ALLOWLIST@1", tuple(entries)])


def citation_observation_digest(
    reference: CitationEvidenceReference, excerpt: str
) -> Digest:
    return digest_of(
        [
            "CITATION_OBSERVATION@1",
            {
                "reference": reference,
                "excerpt": excerpt,
            },
        ]
    )


def structure_view_result_seal_digest(
    *,
    result_id: StableId,
    result_kind: str,
    view_digest: Digest,
    evidence_allowlist: tuple[CitationEvidenceReference, ...],
    allowlist_digest: Digest,
) -> Digest:
    return digest_of(
        [
            "STRUCTURE_VIEW_RESULT_CITATION_SEAL@1",
            {
                "result_id": result_id.value,
                "result_kind": result_kind,
                "view_digest": view_digest.value,
                "evidence_allowlist": evidence_allowlist,
                "allowlist_digest": allowlist_digest.value,
            },
        ]
    )


def _display(observation: CitationObservation) -> CitationDisplay:
    reference = observation.reference
    display_digest = digest_of(
        [
            "CITATION_BROWSER_DISPLAY@1",
            {
                "evidence_id": reference.evidence_id.value,
                "artifact_id": reference.artifact_id.value,
                "source_context_id": reference.source_context_id.value,
                "locator": reference.locator,
                "byte_start": reference.byte_start,
                "byte_end": reference.byte_end,
                "observation": observation.excerpt,
                "excerpt_digest": reference.excerpt_digest.value,
                "evidence_digest": reference.evidence_digest.value,
            },
        ]
    )
    return CitationDisplay(
        evidence_id=reference.evidence_id,
        artifact_id=reference.artifact_id,
        source_context_id=reference.source_context_id,
        locator=reference.locator,
        byte_start=reference.byte_start,
        byte_end=reference.byte_end,
        observation=observation.excerpt,
        excerpt_digest=reference.excerpt_digest,
        evidence_digest=reference.evidence_digest,
        digest=display_digest,
    )


def _require_canonical_allowlist(
    entries: tuple[CitationEvidenceReference, ...],
) -> None:
    keys = tuple(entry.evidence_id.value for entry in entries)
    if len(keys) != len(set(keys)):
        _invalid(
            "CITATION_ALLOWLIST_DUPLICATE",
            "Citation Evidence allowlist contains duplicate identities",
        )
    if keys != tuple(sorted(keys)):
        _invalid(
            "CITATION_ALLOWLIST_NONCANONICAL_ORDER",
            "Citation Evidence allowlist must be sorted by exact Evidence ID",
        )


def _typed(value: object, expected: type, label: str) -> None:
    if not isinstance(value, expected):
        _invalid("CITATION_VALUE_TYPE_INVALID", f"{label} has the wrong type")


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        _invalid("CITATION_TEXT_NONCANONICAL", f"{label} is not canonical")
    return value


def _invalid(reason_code: str, message: str) -> None:
    raise _invalid_error(reason_code, message)


def _invalid_error(reason_code: str, message: str) -> DomainError:
    return DomainError(
        ErrorCode.INVALID_ARGUMENT,
        message,
        {"reason_code": reason_code},
    )


def _inconsistent(reason_code: str, message: str, **details: str) -> None:
    raise DomainError(
        ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
        message,
        {"reason_code": reason_code, **details},
    )


__all__ = [
    "CitationDisplay",
    "CitationEvidenceReference",
    "CitationKnowledgeObservationOwner",
    "CitationObservation",
    "CitationObservationBroker",
    "CitationProjection",
    "CitationProjector",
    "CitationStoreReader",
    "CitationStoreReceipt",
    "CitationStoreSnapshot",
    "CitationStoreWriter",
    "StructureViewResultSeal",
    "citation_allowlist_digest",
    "citation_observation_digest",
    "structure_view_result_seal_digest",
]
