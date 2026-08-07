"""Deterministic derived-artifact processing and immutable lineage."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from software_world_model.cross_cutting import Digest, DomainError, ErrorCode, StableId, digest_of

from .operations import SourceArtifact, content_digest


class TransformationClass(str, Enum):
    LOSSLESS = "LOSSLESS"
    LOCATOR_PRESERVING = "LOCATOR_PRESERVING"
    SEMANTIC_TRANSFORMING = "SEMANTIC_TRANSFORMING"
    AGGREGATING = "AGGREGATING"


@dataclass(frozen=True, slots=True)
class DerivedArtifact:
    artifact_id: StableId
    artifact_kind: str
    payload_schema_version: str
    parent_artifact_ids: tuple[StableId, ...]
    content_digest: Digest
    payload: bytes
    classification: str
    derivation_key_digest: Digest


@dataclass(frozen=True, slots=True)
class ArtifactLineage:
    lineage_id: StableId
    child_artifact_id: StableId
    parent_artifact_ids: tuple[StableId, ...]
    transformation_class: TransformationClass
    transformation_contract: str
    input_ranges: tuple[tuple[str, int, int], ...]
    output_range: tuple[int, int]
    locator_reversible: bool
    replayable: bool
    source_root_cardinality: int
    digest: Digest


class ArtifactProcessingRepository(Protocol):
    def save(
        self,
        *,
        artifacts: tuple[DerivedArtifact, ...],
        lineages: tuple[ArtifactLineage, ...],
    ) -> tuple[DerivedArtifact, ...]: ...


class DeterministicArtifactProcessingService:
    def __init__(self, repository: ArtifactProcessingRepository) -> None:
        self._repository = repository

    def chunk_text(
        self,
        *,
        parent: SourceArtifact,
        max_chunk_bytes: int,
        transformation_contract: str = "utf8-byte-chunk@1",
    ) -> tuple[DerivedArtifact, ...]:
        if parent.truncated:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "a truncated parent cannot be represented as complete deterministic chunks",
            )
        if max_chunk_bytes < 1:
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "chunk size must be positive")
        try:
            parent.payload.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "text chunking requires UTF-8") from exc
        artifacts: list[DerivedArtifact] = []
        lineages: list[ArtifactLineage] = []
        start = 0
        while start < len(parent.payload):
            end = min(start + max_chunk_bytes, len(parent.payload))
            while end < len(parent.payload):
                try:
                    parent.payload[start:end].decode("utf-8")
                    break
                except UnicodeDecodeError:
                    end -= 1
            if end <= start:
                end = min(start + max_chunk_bytes, len(parent.payload))
                while end < len(parent.payload) and (parent.payload[end] & 0b11000000) == 0b10000000:
                    end += 1
            payload = parent.payload[start:end]
            derivation_key = digest_of(
                {
                    "parent_artifact_id": parent.artifact_id.value,
                    "parent_content_digest": parent.content_digest.value,
                    "input_range": (start, end),
                    "transformation_contract": transformation_contract,
                    "output_kind": "TEXT_CHUNK@1",
                }
            )
            artifact_id = StableId(f"derived_artifact_{derivation_key.value[-32:]}")
            artifact = DerivedArtifact(
                artifact_id=artifact_id,
                artifact_kind="TEXT_CHUNK@1",
                payload_schema_version="1",
                parent_artifact_ids=(parent.artifact_id,),
                content_digest=content_digest(payload),
                payload=payload,
                classification=parent.classification,
                derivation_key_digest=derivation_key,
            )
            lineage_core = {
                "child_artifact_id": artifact_id.value,
                "parent_artifact_ids": (parent.artifact_id.value,),
                "transformation_class": TransformationClass.LOCATOR_PRESERVING.value,
                "transformation_contract": transformation_contract,
                "input_ranges": ((parent.artifact_id.value, start, end),),
                "output_range": (0, len(payload)),
                "locator_reversible": True,
                "replayable": True,
                "source_root_cardinality": 1,
            }
            lineage_digest = digest_of(lineage_core)
            lineages.append(
                ArtifactLineage(
                    lineage_id=StableId(f"artifact_lineage_{lineage_digest.value[-32:]}"),
                    child_artifact_id=artifact_id,
                    parent_artifact_ids=(parent.artifact_id,),
                    transformation_class=TransformationClass.LOCATOR_PRESERVING,
                    transformation_contract=transformation_contract,
                    input_ranges=((parent.artifact_id.value, start, end),),
                    output_range=(0, len(payload)),
                    locator_reversible=True,
                    replayable=True,
                    source_root_cardinality=1,
                    digest=lineage_digest,
                )
            )
            artifacts.append(artifact)
            start = end
        return self._repository.save(artifacts=tuple(artifacts), lineages=tuple(lineages))
