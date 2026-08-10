"""Knowledge-owned deterministic Context Comparison assessments.

The Application layer may select and order exact Snapshot bindings, but it
must not decide whether those bindings are comparable.  This module accepts a
small no-payload representation of each exact Snapshot and reconstructs the
sealed Assessment from those inputs.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from software_world_model.cross_cutting import (
    Digest,
    DomainError,
    ErrorCode,
    StableId,
    digest_of,
)


class StructureContextComparisonPurpose(str, Enum):
    SNAPSHOT_COMPARISON = "STRUCTURE_SNAPSHOT_COMPARISON@1"


class StructureContextComparisonOutcome(str, Enum):
    COMPATIBLE = "COMPATIBLE"


@dataclass(frozen=True, slots=True)
class StructureContextComparisonCoverageInput:
    """Exact Context and comparison basis for one Coverage Root."""

    coverage_root_id: StableId
    knowledge_context_digest: Digest
    comparison_basis_digest: Digest

    def require_valid(self) -> None:
        if not isinstance(self.coverage_root_id, StableId):
            raise _invalid(
                "CONTEXT_COMPARISON_COVERAGE_ROOT_REQUIRED",
                "Context Comparison Coverage Root must be a typed StableId",
            )
        if self.coverage_root_id.kind != "coverage_root":
            raise _invalid(
                "CONTEXT_COMPARISON_COVERAGE_ROOT_KIND_INVALID",
                "Context Comparison Coverage Root ID has the wrong kind",
            )
        for value, label in (
            (self.knowledge_context_digest, "Knowledge Context digest"),
            (self.comparison_basis_digest, "comparison basis digest"),
        ):
            if not isinstance(value, Digest):
                raise _invalid(
                    "CONTEXT_COMPARISON_DIGEST_REQUIRED",
                    f"{label} must be a typed Digest",
                )


@dataclass(frozen=True, slots=True)
class StructureContextComparisonInput:
    """No-payload exact input reconstructed from one Snapshot read binding."""

    scope_id: StableId
    snapshot_id: StableId
    snapshot_binding_digest: Digest
    schema_ref: str
    schema_digest: Digest
    coverages: tuple[StructureContextComparisonCoverageInput, ...]

    def require_valid(self) -> None:
        if not isinstance(self.scope_id, StableId) or self.scope_id.kind != "scope":
            raise _invalid(
                "CONTEXT_COMPARISON_SCOPE_ID_INVALID",
                "Context Comparison Scope ID must be a typed Scope ID",
            )
        if (
            not isinstance(self.snapshot_id, StableId)
            or self.snapshot_id.kind != "structure_snapshot"
        ):
            raise _invalid(
                "CONTEXT_COMPARISON_SNAPSHOT_ID_INVALID",
                "Context Comparison Snapshot ID must be a typed Structure Snapshot ID",
            )
        if not isinstance(self.snapshot_binding_digest, Digest) or not isinstance(
            self.schema_digest, Digest
        ):
            raise _invalid(
                "CONTEXT_COMPARISON_DIGEST_REQUIRED",
                "Context Comparison binding and Schema digests must be typed Digests",
            )
        _text(self.schema_ref, "Context Comparison Schema ref")
        if not self.coverages:
            raise _invalid(
                "CONTEXT_COMPARISON_COVERAGE_EMPTY",
                "Context Comparison requires a non-empty Coverage set",
            )
        for coverage in self.coverages:
            if not isinstance(coverage, StructureContextComparisonCoverageInput):
                raise _invalid(
                    "CONTEXT_COMPARISON_COVERAGE_INPUT_REQUIRED",
                    "Context Comparison requires typed Coverage inputs",
                )
            coverage.require_valid()
        expected = tuple(
            sorted(self.coverages, key=lambda item: item.coverage_root_id.value)
        )
        if self.coverages != expected or len(
            {item.coverage_root_id for item in self.coverages}
        ) != len(self.coverages):
            raise _invalid(
                "CONTEXT_COMPARISON_COVERAGE_SET_INVALID",
                "Context Comparison Coverage inputs must be sorted and unique",
            )


@dataclass(frozen=True, slots=True)
class StructureContextComparisonAssessment:
    """Knowledge-owned compatibility gate for one ordered exact input pair."""

    assessment_id: StableId
    ordinal: int
    purpose: StructureContextComparisonPurpose
    base_snapshot_id: StableId
    base_snapshot_binding_digest: Digest
    target_snapshot_id: StableId
    target_snapshot_binding_digest: Digest
    base_knowledge_context_digests: tuple[Digest, ...]
    target_knowledge_context_digests: tuple[Digest, ...]
    comparison_basis_digests: tuple[Digest, ...]
    outcome: StructureContextComparisonOutcome
    digest: Digest

    def require_valid(
        self,
        *,
        ordinal: int,
        base: StructureContextComparisonInput,
        target: StructureContextComparisonInput,
    ) -> None:
        expected = StructureContextComparisonService().assess(
            ordinal=ordinal,
            purpose=self.purpose,
            base=base,
            target=target,
        )
        if self != expected:
            raise _invalid(
                "READ_SET_CONTEXT_ASSESSMENT_INVALID",
                "Structure Context Comparison does not bind the adjacent exact Snapshots",
            )


class StructureContextComparisonService:
    """Rebuild deterministic Assessments without Application-owned judgment."""

    def assess(
        self,
        *,
        ordinal: int,
        purpose: StructureContextComparisonPurpose | str,
        base: StructureContextComparisonInput,
        target: StructureContextComparisonInput,
    ) -> StructureContextComparisonAssessment:
        if type(ordinal) is not int or ordinal < 0:
            raise _invalid(
                "READ_SET_COMPARISON_ORDINAL_INVALID",
                "Structure Context Comparison ordinal must be non-negative",
            )
        try:
            normalized_purpose = (
                purpose
                if isinstance(purpose, StructureContextComparisonPurpose)
                else StructureContextComparisonPurpose(purpose)
            )
        except (TypeError, ValueError) as exc:
            raise _invalid(
                "READ_SET_COMPARISON_PURPOSE_INVALID",
                "ordered Structure Context Comparison requires the comparison purpose",
            ) from exc
        if not isinstance(base, StructureContextComparisonInput) or not isinstance(
            target, StructureContextComparisonInput
        ):
            raise _invalid(
                "CONTEXT_COMPARISON_INPUT_REQUIRED",
                "Structure Context Comparison requires typed exact inputs",
            )
        base.require_valid()
        target.require_valid()
        if base.scope_id != target.scope_id:
            raise _invalid(
                "READ_SET_SCOPE_MISMATCH",
                "ordered Structure Context Comparison crosses Scope",
            )
        if (base.schema_ref, base.schema_digest) != (
            target.schema_ref,
            target.schema_digest,
        ):
            raise _invalid(
                "READ_SET_SCHEMA_INCOMPARABLE",
                "ordered Structure Snapshots use different Schema definitions",
            )
        base_basis = tuple(
            (item.coverage_root_id, item.comparison_basis_digest)
            for item in base.coverages
        )
        target_basis = tuple(
            (item.coverage_root_id, item.comparison_basis_digest)
            for item in target.coverages
        )
        if base_basis != target_basis:
            raise _invalid(
                "READ_SET_COVERAGE_INCOMPARABLE",
                "ordered Structure Snapshots use different Profile, Evaluation Context, canonicalizer, or Coverage definitions",
            )
        core = {
            "ordinal": ordinal,
            "purpose": normalized_purpose.value,
            "base_snapshot_id": base.snapshot_id.value,
            "base_snapshot_binding_digest": base.snapshot_binding_digest.value,
            "target_snapshot_id": target.snapshot_id.value,
            "target_snapshot_binding_digest": target.snapshot_binding_digest.value,
            "base_knowledge_context_digests": tuple(
                item.knowledge_context_digest.value for item in base.coverages
            ),
            "target_knowledge_context_digests": tuple(
                item.knowledge_context_digest.value for item in target.coverages
            ),
            "comparison_basis_digests": tuple(
                item.comparison_basis_digest.value for item in base.coverages
            ),
            "outcome": StructureContextComparisonOutcome.COMPATIBLE.value,
        }
        assessment_digest = digest_of(
            ["STRUCTURE_CONTEXT_COMPARISON_ASSESSMENT@1", core]
        )
        return StructureContextComparisonAssessment(
            assessment_id=StableId(
                f"structure_context_comparison_{assessment_digest.value[-32:]}"
            ),
            ordinal=ordinal,
            purpose=normalized_purpose,
            base_snapshot_id=base.snapshot_id,
            base_snapshot_binding_digest=base.snapshot_binding_digest,
            target_snapshot_id=target.snapshot_id,
            target_snapshot_binding_digest=target.snapshot_binding_digest,
            base_knowledge_context_digests=tuple(
                item.knowledge_context_digest for item in base.coverages
            ),
            target_knowledge_context_digests=tuple(
                item.knowledge_context_digest for item in target.coverages
            ),
            comparison_basis_digests=tuple(
                item.comparison_basis_digest for item in base.coverages
            ),
            outcome=StructureContextComparisonOutcome.COMPATIBLE,
            digest=assessment_digest,
        )


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise _invalid(
            "CONTEXT_COMPARISON_TEXT_INVALID",
            f"{label} must be canonical text",
        )
    return value


def _invalid(reason_code: str, message: str) -> DomainError:
    return DomainError(
        ErrorCode.INVALID_ARGUMENT,
        message,
        {"reason_code": reason_code},
    )


__all__ = [
    "StructureContextComparisonAssessment",
    "StructureContextComparisonCoverageInput",
    "StructureContextComparisonInput",
    "StructureContextComparisonOutcome",
    "StructureContextComparisonPurpose",
    "StructureContextComparisonService",
]
