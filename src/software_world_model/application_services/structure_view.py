"""Deterministic Structure projections over verified no-payload read bundles.

The service in this module deliberately has no repository, Source, SQLite, or
model dependency.  Its complete input is one ordered read-bundle envelope plus
the exact Snapshot bundles named by that envelope.  This makes the same query
code usable in the isolated G2 answer worker.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
import re
import unicodedata

from software_world_model.application_services.structure_read_bundle import (
    StructureBusinessDiscoveryRecallBinding,
    StructureOrderedReadBundle,
    StructureSnapshotReadBundle,
)
from software_world_model.application_services.structure_read_session import (
    StructureReadSession,
)
from software_world_model.cross_cutting import (
    Digest,
    DomainError,
    ErrorCode,
    StableId,
    digest_of,
)
from software_world_model.knowledge_engine.context_comparison import (
    StructureContextComparisonOutcome,
)
from software_world_model.knowledge_engine.structure import (
    CanonicalFields,
    CoverageRecord,
    EntityRecord,
    EntityType,
    JAVA_SOURCE_SEMANTICS_PROFILE_REF,
    JavaSemanticDisposition,
    LiteralFactRecord,
    ObservationModality,
    RelationFactRecord,
    RelationPredicate,
)
from software_world_model.knowledge_engine.structure_publication import (
    StructureEvidenceMetadata,
)


class StructureViewOperation(str, Enum):
    ENTITY_CANDIDATES = "ENTITY_CANDIDATES"
    CHILD_MODULE_INVENTORY = "CHILD_MODULE_INVENTORY"
    DECLARED_METHOD_INVENTORY = "DECLARED_METHOD_INVENTORY"
    IMPLEMENTATION_CANDIDATES = "IMPLEMENTATION_CANDIDATES"
    METHOD_IMPLEMENTATION = "METHOD_IMPLEMENTATION"
    DIRECT_NEIGHBORHOOD = "DIRECT_NEIGHBORHOOD"
    PATH_EXISTS = "PATH_EXISTS"
    ALL_SIMPLE_PATHS = "ALL_SIMPLE_PATHS"
    ORDERED_SNAPSHOT_DIFF = "ORDERED_SNAPSHOT_DIFF"


class EntityResolutionStatus(str, Enum):
    ZERO = "ZERO"
    UNIQUE = "UNIQUE"
    AMBIGUOUS = "AMBIGUOUS"
    TRUNCATED = "TRUNCATED"
    INCOMPLETE_COVERAGE = "INCOMPLETE_COVERAGE"


class StructureViewCompleteness(str, Enum):
    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"


class StructureViewArgumentOrigin(str, Enum):
    CALLER_EXACT_REF = "CALLER_EXACT_REF"
    SEALED_UNIQUE_CANDIDATE = "SEALED_UNIQUE_CANDIDATE"
    SEALED_RESULT_MEMBER = "SEALED_RESULT_MEMBER"


class NeighborhoodDirection(str, Enum):
    OUTGOING = "OUTGOING"
    INCOMING = "INCOMING"
    BOTH = "BOTH"


_PUBLIC_ENTITY_ROOT_FIELDS: dict[EntityType, tuple[str, ...]] = {
    EntityType.SOFTWARE_SYSTEM: ("canonical_system_key",),
    EntityType.MAVEN_MODULE: ("effective_group_id", "artifact_id"),
    EntityType.JAVA_SOURCE_FILE: ("source_path",),
    EntityType.JAVA_TYPE: ("qualified_name",),
    EntityType.JAVA_METHOD: (
        "declaring_type_qualified_name",
        "method_name",
        "parameter_types",
    ),
    EntityType.JAVA_IMPLEMENTATION_ATOM: ("atom_kind",),
    EntityType.JAVA_STATE_SLOT: ("slot_kind", "canonical_identifier"),
}
_PUBLIC_ENTITY_STATE_FIELDS: dict[EntityType, tuple[str, ...]] = {
    EntityType.SOFTWARE_SYSTEM: (
        "label",
        "effective_group_id",
        "artifact_id",
        "effective_version",
        "packaging",
        "root_pom_locator",
    ),
    EntityType.MAVEN_MODULE: (
        "label",
        "effective_version",
        "packaging",
        "module_path",
    ),
    EntityType.JAVA_SOURCE_FILE: ("disposition",),
    EntityType.JAVA_TYPE: (
        "simple_name",
        "package_name",
        "declaration_kind",
        "source_path",
    ),
    EntityType.JAVA_METHOD: (
        "return_type",
        "visibility",
        "source_path",
    ),
    EntityType.JAVA_IMPLEMENTATION_ATOM: (
        "semantic_form",
        "operator",
        "value_category",
        "method_disposition",
    ),
    EntityType.JAVA_STATE_SLOT: ("declared_type",),
}

_FEATURE_TOKEN_PART = re.compile(
    r"[A-Z]+(?=[A-Z][a-z]|\d|$)|[A-Z]?[a-z]+|[A-Z]+|\d+"
)


@dataclass(frozen=True, slots=True)
class StructureEntityCandidate:
    entity_root_id: StableId
    entity_state_id: StableId
    entity_state_digest: Digest
    entity_type: EntityType
    root_fields: CanonicalFields
    state_fields: CanonicalFields
    matched_fields: tuple[str, ...]
    canonical_ga: str | None
    canonical_gav: str | None
    evidence_references: tuple[StableId, ...]
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        record: EntityRecord,
        matched_fields: Sequence[str],
    ) -> "StructureEntityCandidate":
        record.root.require_valid_identity()
        record.state.require_valid_identity()
        root_fields = record.root.root_fields
        state_fields = record.state.state_payload_fields
        normalized_matches = tuple(sorted({_text(item, "matched field") for item in matched_fields}))
        ga, gav = _entity_coordinates(record)
        core = {
            "entity_root_id": record.root_id.value,
            "entity_state_id": record.state_id.value,
            "entity_state_digest": record.state_digest.value,
            "entity_type": record.root.entity_type.value,
            "root_fields": root_fields,
            "state_fields": state_fields,
            "matched_fields": normalized_matches,
            "canonical_ga": ga,
            "canonical_gav": gav,
            "evidence_references": tuple(
                item.value for item in record.state.evidence_references
            ),
        }
        result = cls(
            entity_root_id=record.root_id,
            entity_state_id=record.state_id,
            entity_state_digest=record.state_digest,
            entity_type=record.root.entity_type,
            root_fields=root_fields,
            state_fields=state_fields,
            matched_fields=normalized_matches,
            canonical_ga=ga,
            canonical_gav=gav,
            evidence_references=record.state.evidence_references,
            digest=digest_of(["STRUCTURE_ENTITY_CANDIDATE@1", core]),
        )
        return result

    def canonical_value(self) -> dict[str, object]:
        return {
            "entity_root_id": self.entity_root_id.value,
            "entity_state_id": self.entity_state_id.value,
            "entity_state_digest": self.entity_state_digest.value,
            "entity_type": self.entity_type.value,
            "root_fields": self.root_fields,
            "state_fields": self.state_fields,
            "matched_fields": self.matched_fields,
            "canonical_ga": self.canonical_ga,
            "canonical_gav": self.canonical_gav,
            "evidence_references": tuple(
                item.value for item in self.evidence_references
            ),
            "digest": self.digest.value,
        }

@dataclass(frozen=True, slots=True)
class StructureViewSupport:
    snapshot_id: StableId
    member_kind: str
    root_id: StableId
    state_id: StableId
    state_digest: Digest
    evidence: tuple[StructureEvidenceMetadata, ...]
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        snapshot_id: StableId,
        member_kind: str,
        root_id: StableId,
        state_id: StableId,
        state_digest: Digest,
        evidence: Sequence[StructureEvidenceMetadata],
    ) -> "StructureViewSupport":
        normalized_kind = _text(member_kind, "support member kind")
        normalized_evidence = tuple(
            sorted(evidence, key=lambda item: item.evidence_id.value)
        )
        if len({item.evidence_id for item in normalized_evidence}) != len(
            normalized_evidence
        ):
            raise _invalid(
                "VIEW_SUPPORT_EVIDENCE_DUPLICATE",
                "Structure View Support contains duplicate Evidence references",
            )
        core = {
            "snapshot_id": snapshot_id.value,
            "member_kind": normalized_kind,
            "root_id": root_id.value,
            "state_id": state_id.value,
            "state_digest": state_digest.value,
            "evidence": tuple(_evidence_value(item) for item in normalized_evidence),
        }
        result = cls(
            snapshot_id=snapshot_id,
            member_kind=normalized_kind,
            root_id=root_id,
            state_id=state_id,
            state_digest=state_digest,
            evidence=normalized_evidence,
            digest=digest_of(["STRUCTURE_VIEW_SUPPORT@1", core]),
        )
        return result

    def canonical_value(self) -> dict[str, object]:
        return {
            "snapshot_id": self.snapshot_id.value,
            "member_kind": self.member_kind,
            "root_id": self.root_id.value,
            "state_id": self.state_id.value,
            "state_digest": self.state_digest.value,
            "evidence": tuple(_evidence_value(item) for item in self.evidence),
            "digest": self.digest.value,
        }


@dataclass(frozen=True, slots=True)
class StructureViewResult:
    result_id: StableId
    operation: StructureViewOperation
    session_id: StableId
    session_digest: Digest
    read_set_digest: Digest
    ordered_bundle_digest: Digest
    snapshot_ids: tuple[StableId, ...]
    snapshot_bundle_digests: tuple[Digest, ...]
    profile_refs: tuple[str, ...]
    relation_modalities: tuple[str, ...]
    coverage: tuple[CanonicalFields, ...]
    completeness: StructureViewCompleteness
    truncated: bool
    limitations: tuple[str, ...]
    payload: CanonicalFields
    support_map: tuple[StructureViewSupport, ...]
    evidence_allowlist: tuple[StableId, ...]
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        operation: StructureViewOperation,
        ordered: StructureOrderedReadBundle,
        selected_bundles: Sequence[StructureSnapshotReadBundle],
        completeness: StructureViewCompleteness,
        truncated: bool,
        limitations: Sequence[str],
        payload: Mapping[str, object],
        support_map: Sequence[StructureViewSupport],
    ) -> "StructureViewResult":
        if type(truncated) is not bool:
            raise _invalid(
                "VIEW_RESULT_TRUNCATED_INVALID",
                "Structure View Result truncated marker must be an exact boolean",
            )
        bundles = tuple(selected_bundles)
        if not bundles:
            raise _invalid(
                "VIEW_RESULT_SNAPSHOT_REQUIRED",
                "Structure View Result requires at least one exact Snapshot bundle",
            )
        normalized_support = tuple(
            sorted(
                support_map,
                key=lambda item: (
                    item.snapshot_id.value,
                    item.member_kind,
                    item.root_id.value,
                ),
            )
        )
        if len(
            {
                (item.snapshot_id, item.member_kind, item.root_id)
                for item in normalized_support
            }
        ) != len(normalized_support):
            raise _invalid(
                "VIEW_SUPPORT_DUPLICATE",
                "Structure View Result contains duplicate Support entries",
            )
        normalized_limitations = tuple(
            sorted({_text(item, "View Limitation") for item in limitations})
        )
        payload_fields = CanonicalFields(payload)
        evidence_allowlist = tuple(
            sorted(
                {
                    evidence.evidence_id
                    for support in normalized_support
                    for evidence in support.evidence
                },
                key=lambda item: item.value,
            )
        )
        profiles = tuple(
            sorted(
                {
                    coverage.root.profile_ref
                    for bundle in bundles
                    for coverage in bundle.coverages
                }
            )
        )
        modalities = tuple(
            sorted(
                {
                    relation.root.observation_modality.value
                    for bundle in bundles
                    for relation in bundle.relation_facts
                }
            )
        )
        coverage_values = tuple(
            CanonicalFields(
                {
                    "snapshot_id": bundle.snapshot_id.value,
                    "coverage_root_id": coverage.root_id.value,
                    "coverage_root_digest": coverage.root.allocation_key_digest.value,
                    "coverage_state_id": coverage.state_id.value,
                    "coverage_state_digest": coverage.state.state_digest.value,
                    "profile_ref": coverage.root.profile_ref,
                    "covered_entity_types": tuple(
                        item.value for item in coverage.root.covered_entity_types
                    ),
                    "covered_relation_predicates": tuple(
                        item.value
                        for item in coverage.root.covered_relation_predicates
                    ),
                    "source_revision": coverage.state.source_revision,
                    "knowledge_context_digest": (
                        coverage.state.knowledge_context_digest.value
                    ),
                    "evaluation_context_ref": (
                        coverage.root.maven_evaluation_context_ref
                    ),
                    "evaluation_context_digest": (
                        coverage.root.maven_evaluation_context_digest.value
                    ),
                    "canonicalization_ref": coverage.root.canonicalization_ref,
                    "canonicalization_digest": (
                        coverage.root.canonicalization_digest.value
                    ),
                    "member_manifest_digest": (
                        coverage.state.complete_member_manifest.digest.value
                    ),
                    "completeness": (
                        coverage.state.complete_member_manifest.completeness.value
                    ),
                }
            )
            for bundle in bundles
            for coverage in bundle.coverages
        )
        core = {
            "operation": operation.value,
            "session_id": ordered.session.session_id.value,
            "session_digest": ordered.session.digest.value,
            "read_set_digest": ordered.session.read_set_digest.value,
            "ordered_bundle_digest": ordered.digest.value,
            "snapshot_ids": tuple(bundle.snapshot_id.value for bundle in bundles),
            "snapshot_bundle_digests": tuple(
                bundle.digest.value for bundle in bundles
            ),
            "profile_refs": profiles,
            "relation_modalities": modalities,
            "coverage": coverage_values,
            "completeness": completeness.value,
            "truncated": truncated,
            "limitations": normalized_limitations,
            "payload": payload_fields,
            "support_map": tuple(item.canonical_value() for item in normalized_support),
            "evidence_allowlist": tuple(
                item.value for item in evidence_allowlist
            ),
        }
        identity = digest_of(["STRUCTURE_VIEW_RESULT_ID@1", core])
        result_id = _stable("structure_view_result", identity)
        result = cls(
            result_id=result_id,
            operation=operation,
            session_id=ordered.session.session_id,
            session_digest=ordered.session.digest,
            read_set_digest=ordered.session.read_set_digest,
            ordered_bundle_digest=ordered.digest,
            snapshot_ids=tuple(bundle.snapshot_id for bundle in bundles),
            snapshot_bundle_digests=tuple(bundle.digest for bundle in bundles),
            profile_refs=profiles,
            relation_modalities=modalities,
            coverage=coverage_values,
            completeness=completeness,
            truncated=truncated,
            limitations=normalized_limitations,
            payload=payload_fields,
            support_map=normalized_support,
            evidence_allowlist=evidence_allowlist,
            digest=digest_of(
                [
                    "STRUCTURE_VIEW_RESULT@1",
                    {"result_id": result_id.value, **core},
                ]
            ),
        )
        result.require_valid()
        return result

    def canonical_value(self) -> dict[str, object]:
        return {
            "result_id": self.result_id.value,
            "operation": self.operation.value,
            "session_id": self.session_id.value,
            "session_digest": self.session_digest.value,
            "read_set_digest": self.read_set_digest.value,
            "ordered_bundle_digest": self.ordered_bundle_digest.value,
            "snapshot_ids": tuple(item.value for item in self.snapshot_ids),
            "snapshot_bundle_digests": tuple(
                item.value for item in self.snapshot_bundle_digests
            ),
            "profile_refs": self.profile_refs,
            "relation_modalities": self.relation_modalities,
            "coverage": self.coverage,
            "completeness": self.completeness.value,
            "truncated": self.truncated,
            "limitations": self.limitations,
            "payload": self.payload,
            "support_map": tuple(item.canonical_value() for item in self.support_map),
            "evidence_allowlist": tuple(
                item.value for item in self.evidence_allowlist
            ),
            "digest": self.digest.value,
        }

    def citation_evidence_metadata(self) -> tuple[StructureEvidenceMetadata, ...]:
        """Return the exact no-payload metadata sealed by this Result."""

        by_id: dict[StableId, StructureEvidenceMetadata] = {}
        for support in self.support_map:
            for evidence in support.evidence:
                previous = by_id.get(evidence.evidence_id)
                if previous is not None and previous != evidence:
                    raise _inconsistent(
                        "View Result binds conflicting metadata for one Evidence ID"
                    )
                by_id[evidence.evidence_id] = evidence
        try:
            values = tuple(by_id[item] for item in self.evidence_allowlist)
        except KeyError as exc:
            raise _inconsistent(
                "View Result Evidence metadata is incomplete"
            ) from exc
        return values

    def require_valid(self) -> None:
        if type(self.truncated) is not bool:
            raise _invalid(
                "VIEW_RESULT_TRUNCATED_INVALID",
                "Structure View Result truncated marker must be an exact boolean",
            )
        if self.result_id.kind != "structure_view_result":
            raise _invalid(
                "VIEW_RESULT_ID_KIND_INVALID",
                "Structure View Result ID has the wrong kind",
            )
        if self.session_id.kind != "structure_read_session":
            raise _invalid(
                "VIEW_RESULT_SESSION_KIND_INVALID",
                "Structure View Result Session ID has the wrong kind",
            )
        if not self.snapshot_ids or len(self.snapshot_ids) != len(
            self.snapshot_bundle_digests
        ):
            raise _invalid(
                "VIEW_RESULT_SNAPSHOT_BINDING_INVALID",
                "Structure View Result Snapshot bindings are incomplete",
            )
        if tuple(sorted(set(self.profile_refs))) != self.profile_refs:
            raise _invalid(
                "VIEW_RESULT_PROFILE_SET_INVALID",
                "Structure View Result Profile refs are not canonical",
            )
        if tuple(sorted(set(self.relation_modalities))) != self.relation_modalities:
            raise _invalid(
                "VIEW_RESULT_MODALITY_SET_INVALID",
                "Structure View Result modalities are not canonical",
            )
        if tuple(sorted(set(self.limitations))) != self.limitations:
            raise _invalid(
                "VIEW_RESULT_LIMITATION_SET_INVALID",
                "Structure View Result limitations are not canonical",
            )
        expected_support = tuple(
            sorted(
                self.support_map,
                key=lambda item: (
                    item.snapshot_id.value,
                    item.member_kind,
                    item.root_id.value,
                ),
            )
        )
        if expected_support != self.support_map:
            raise _invalid(
                "VIEW_RESULT_SUPPORT_ORDER_INVALID",
                "Structure View Result Support order is not canonical",
            )
        for support in self.support_map:
            expected = StructureViewSupport.create(
                snapshot_id=support.snapshot_id,
                member_kind=support.member_kind,
                root_id=support.root_id,
                state_id=support.state_id,
                state_digest=support.state_digest,
                evidence=support.evidence,
            )
            if expected != support:
                raise _invalid(
                    "VIEW_RESULT_SUPPORT_INVALID",
                    "Structure View Result Support does not verify",
                )
        expected_allowlist = tuple(
            sorted(
                {
                    evidence.evidence_id
                    for support in self.support_map
                    for evidence in support.evidence
                },
                key=lambda item: item.value,
            )
        )
        if self.evidence_allowlist != expected_allowlist:
            raise _invalid(
                "VIEW_RESULT_EVIDENCE_ALLOWLIST_INVALID",
                "Structure View Result Evidence allowlist does not match Support",
            )
        core = {
            "operation": self.operation.value,
            "session_id": self.session_id.value,
            "session_digest": self.session_digest.value,
            "read_set_digest": self.read_set_digest.value,
            "ordered_bundle_digest": self.ordered_bundle_digest.value,
            "snapshot_ids": tuple(item.value for item in self.snapshot_ids),
            "snapshot_bundle_digests": tuple(
                item.value for item in self.snapshot_bundle_digests
            ),
            "profile_refs": self.profile_refs,
            "relation_modalities": self.relation_modalities,
            "coverage": self.coverage,
            "completeness": self.completeness.value,
            "truncated": self.truncated,
            "limitations": self.limitations,
            "payload": self.payload,
            "support_map": tuple(item.canonical_value() for item in self.support_map),
            "evidence_allowlist": tuple(
                item.value for item in self.evidence_allowlist
            ),
        }
        identity = digest_of(["STRUCTURE_VIEW_RESULT_ID@1", core])
        expected_id = _stable("structure_view_result", identity)
        expected_digest = digest_of(
            [
                "STRUCTURE_VIEW_RESULT@1",
                {"result_id": expected_id.value, **core},
            ]
        )
        if self.result_id != expected_id or self.digest != expected_digest:
            raise _invalid(
                "VIEW_RESULT_DIGEST_MISMATCH",
                "Structure View Result is not canonical",
            )


@dataclass(frozen=True, slots=True)
class StructureEntityArgument:
    origin: StructureViewArgumentOrigin
    session_id: StableId
    read_set_digest: Digest
    ordered_bundle_digest: Digest
    snapshot_id: StableId
    snapshot_bundle_digest: Digest
    entity_root_id: StableId
    entity_state_id: StableId
    candidate_result: StructureViewResult | None
    candidate_result_id: StableId | None
    candidate_result_digest: Digest | None
    digest: Digest

    @classmethod
    def from_unique_candidate(
        cls,
        result: StructureViewResult,
    ) -> "StructureEntityArgument":
        if result.operation not in {
            StructureViewOperation.ENTITY_CANDIDATES,
            StructureViewOperation.IMPLEMENTATION_CANDIDATES,
        }:
            raise _invalid(
                "VIEW_CANDIDATE_RESULT_REQUIRED",
                "typed argument requires a supported candidate Result",
            )
        resolution_status = (
            result.payload["resolution_status"]
            if result.operation is StructureViewOperation.ENTITY_CANDIDATES
            else (
                EntityResolutionStatus.UNIQUE.value
                if (
                    result.payload["candidate_count"] == 1
                    and result.payload["query_status"] == "SUPPORTED"
                    and not result.truncated
                )
                else EntityResolutionStatus.AMBIGUOUS.value
            )
        )
        if resolution_status != EntityResolutionStatus.UNIQUE.value:
            raise _invalid(
                "VIEW_CANDIDATE_NOT_UNIQUE",
                "only a sealed unique candidate can bind a typed argument",
            )
        candidates = result.payload["candidates"]
        if not isinstance(candidates, tuple) or len(candidates) != 1:
            raise _invalid(
                "VIEW_CANDIDATE_RESULT_INVALID",
                "unique candidate Result has the wrong canonical shape",
            )
        candidate = candidates[0]
        if not isinstance(candidate, Mapping):
            raise _invalid(
                "VIEW_CANDIDATE_RESULT_INVALID",
                "candidate Result payload is malformed",
            )
        entity_value = (
            candidate
            if result.operation is StructureViewOperation.ENTITY_CANDIDATES
            else candidate.get("method")
        )
        if not isinstance(entity_value, Mapping):
            raise _invalid(
                "VIEW_CANDIDATE_RESULT_INVALID",
                "candidate Result method payload is malformed",
            )
        return cls._create(
            origin=StructureViewArgumentOrigin.SEALED_UNIQUE_CANDIDATE,
            session_id=result.session_id,
            read_set_digest=result.read_set_digest,
            ordered_bundle_digest=result.ordered_bundle_digest,
            snapshot_id=result.snapshot_ids[0],
            snapshot_bundle_digest=result.snapshot_bundle_digests[0],
            entity_root_id=StableId(
                _mapping_text(
                    entity_value,
                    (
                        "entity_root_id"
                        if result.operation is StructureViewOperation.ENTITY_CANDIDATES
                        else "root_id"
                    ),
                )
            ),
            entity_state_id=StableId(
                _mapping_text(
                    entity_value,
                    (
                        "entity_state_id"
                        if result.operation is StructureViewOperation.ENTITY_CANDIDATES
                        else "state_id"
                    ),
                )
            ),
            candidate_result=result,
            candidate_result_id=result.result_id,
            candidate_result_digest=result.digest,
        )

    @classmethod
    def from_result_member(
        cls,
        result: StructureViewResult,
        *,
        entity_root_id: StableId,
        entity_state_id: StableId,
    ) -> "StructureEntityArgument":
        """Bind one exact Entity member exposed by a sealed typed Result.

        Unlike ``from_unique_candidate``, this constructor deliberately does
        not collapse a 0/N result into a unique resolution.  It proves only
        that the selected Root/State pair is a public member of the exact
        Result and leaves relevance and query sufficiency to the investigation
        authority chain.
        """

        result.require_valid()
        if len(result.snapshot_ids) != 1:
            raise _invalid(
                "VIEW_RESULT_MEMBER_SNAPSHOT_INVALID",
                "typed Result member requires one exact Snapshot",
            )
        root_id = _typed_stable_id(entity_root_id, "result member Root ID")
        state_id = _typed_stable_id(entity_state_id, "result member State ID")
        if (root_id, state_id) not in _public_result_entity_refs(result):
            raise _invalid(
                "VIEW_RESULT_MEMBER_NOT_EXPOSED",
                "typed Entity argument is not a public member of the sealed Result",
            )
        return cls._create(
            origin=StructureViewArgumentOrigin.SEALED_RESULT_MEMBER,
            session_id=result.session_id,
            read_set_digest=result.read_set_digest,
            ordered_bundle_digest=result.ordered_bundle_digest,
            snapshot_id=result.snapshot_ids[0],
            snapshot_bundle_digest=result.snapshot_bundle_digests[0],
            entity_root_id=root_id,
            entity_state_id=state_id,
            candidate_result=result,
            candidate_result_id=result.result_id,
            candidate_result_digest=result.digest,
        )

    @classmethod
    def caller_exact_ref(
        cls,
        *,
        service: "StructureViewService",
        snapshot_id: StableId,
        entity_root_id: StableId,
        entity_state_id: StableId,
    ) -> "StructureEntityArgument":
        bundle = service._bundle(snapshot_id)
        return cls._create(
            origin=StructureViewArgumentOrigin.CALLER_EXACT_REF,
            session_id=service.session_id,
            read_set_digest=service.read_set_digest,
            ordered_bundle_digest=service.ordered_bundle_digest,
            snapshot_id=snapshot_id,
            snapshot_bundle_digest=bundle.digest,
            entity_root_id=entity_root_id,
            entity_state_id=entity_state_id,
            candidate_result=None,
            candidate_result_id=None,
            candidate_result_digest=None,
        )

    @classmethod
    def _create(
        cls,
        *,
        origin: StructureViewArgumentOrigin,
        session_id: StableId,
        read_set_digest: Digest,
        ordered_bundle_digest: Digest,
        snapshot_id: StableId,
        snapshot_bundle_digest: Digest,
        entity_root_id: StableId,
        entity_state_id: StableId,
        candidate_result: StructureViewResult | None,
        candidate_result_id: StableId | None,
        candidate_result_digest: Digest | None,
    ) -> "StructureEntityArgument":
        core = {
            "origin": origin.value,
            "session_id": session_id.value,
            "read_set_digest": read_set_digest.value,
            "ordered_bundle_digest": ordered_bundle_digest.value,
            "snapshot_id": snapshot_id.value,
            "snapshot_bundle_digest": snapshot_bundle_digest.value,
            "entity_root_id": entity_root_id.value,
            "entity_state_id": entity_state_id.value,
            "candidate_result_id": (
                candidate_result_id.value if candidate_result_id is not None else None
            ),
            "candidate_result_digest": (
                candidate_result_digest.value
                if candidate_result_digest is not None
                else None
            ),
        }
        return cls(
            origin=origin,
            session_id=session_id,
            read_set_digest=read_set_digest,
            ordered_bundle_digest=ordered_bundle_digest,
            snapshot_id=snapshot_id,
            snapshot_bundle_digest=snapshot_bundle_digest,
            entity_root_id=entity_root_id,
            entity_state_id=entity_state_id,
            candidate_result=candidate_result,
            candidate_result_id=candidate_result_id,
            candidate_result_digest=candidate_result_digest,
            digest=digest_of(["STRUCTURE_ENTITY_ARGUMENT@1", core]),
        )

    def require_valid(self) -> None:
        """Verify the complete typed-argument proof without a mounted Store."""

        expected = type(self)._create(
            origin=self.origin,
            session_id=self.session_id,
            read_set_digest=self.read_set_digest,
            ordered_bundle_digest=self.ordered_bundle_digest,
            snapshot_id=self.snapshot_id,
            snapshot_bundle_digest=self.snapshot_bundle_digest,
            entity_root_id=self.entity_root_id,
            entity_state_id=self.entity_state_id,
            candidate_result=self.candidate_result,
            candidate_result_id=self.candidate_result_id,
            candidate_result_digest=self.candidate_result_digest,
        )
        if expected.digest != self.digest:
            raise _invalid(
                "VIEW_ENTITY_ARGUMENT_DIGEST_MISMATCH",
                "typed Entity argument is not canonical",
            )
        if self.origin in {
            StructureViewArgumentOrigin.SEALED_UNIQUE_CANDIDATE,
            StructureViewArgumentOrigin.SEALED_RESULT_MEMBER,
        }:
            if (
                self.candidate_result is None
                or self.candidate_result_id is None
                or self.candidate_result_digest is None
            ):
                raise _invalid(
                    "VIEW_CANDIDATE_PROOF_REQUIRED",
                    "candidate-derived Entity argument lacks its sealed proof",
                )
            if (
                self.candidate_result.result_id != self.candidate_result_id
                or self.candidate_result.digest != self.candidate_result_digest
            ):
                raise _invalid(
                    "VIEW_CANDIDATE_PROOF_MISMATCH",
                    "candidate-derived Entity argument proof does not bind its exact unique candidate",
                )
            try:
                self.candidate_result.require_valid()
                rebuilt = (
                    type(self).from_unique_candidate(self.candidate_result)
                    if self.origin
                    is StructureViewArgumentOrigin.SEALED_UNIQUE_CANDIDATE
                    else type(self).from_result_member(
                        self.candidate_result,
                        entity_root_id=self.entity_root_id,
                        entity_state_id=self.entity_state_id,
                    )
                )
            except DomainError as exc:
                raise _invalid(
                    "VIEW_CANDIDATE_PROOF_MISMATCH",
                    "candidate-derived Entity argument proof is invalid",
                ) from exc
            if rebuilt != self:
                raise _invalid(
                    "VIEW_CANDIDATE_PROOF_MISMATCH",
                    "result-derived Entity argument proof does not bind its exact public member",
                )
            return
        if (
            self.origin is not StructureViewArgumentOrigin.CALLER_EXACT_REF
            or self.candidate_result is not None
            or self.candidate_result_id is not None
            or self.candidate_result_digest is not None
        ):
            raise _invalid(
                "VIEW_ENTITY_ARGUMENT_ORIGIN_INVALID",
                "typed Entity argument origin is inconsistent",
            )


@dataclass(frozen=True, slots=True)
class _JavaFeatureTokenSource:
    token: str
    field_class: str
    member_kind: str
    root_id: StableId


@dataclass(frozen=True, slots=True)
class _JavaFeatureIndexEntry:
    method: EntityRecord
    signature: str
    disposition: str
    implementation_completeness: str
    sources: tuple[_JavaFeatureTokenSource, ...]

    @property
    def tokens(self) -> tuple[str, ...]:
        return tuple(sorted({item.token for item in self.sources}))


class StructureViewService:
    """Bundle-only, deterministic Structure query service."""

    def __init__(
        self,
        ordered_bundle: StructureOrderedReadBundle,
        snapshot_bundles: Sequence[
            tuple[StructureSnapshotReadBundle, Digest]
        ],
    ) -> None:
        if not isinstance(ordered_bundle, StructureOrderedReadBundle):
            raise _invalid(
                "ORDERED_READ_BUNDLE_REQUIRED",
                "Structure View requires a typed ordered Read Bundle",
            )
        ordered_bundle.require_valid()
        supplied = tuple(snapshot_bundles)
        ordered_bundle.verify_snapshot_bundles(supplied)
        self._ordered = ordered_bundle
        self._bundles = tuple(item[0] for item in supplied)
        self._file_digests = tuple(item[1] for item in supplied)
        self._by_snapshot = {bundle.snapshot_id: bundle for bundle in self._bundles}
        if len(self._by_snapshot) != len(self._bundles):
            raise _invalid(
                "VIEW_DUPLICATE_SNAPSHOT_BUNDLE",
                "Structure View cannot mount a Snapshot bundle twice",
            )
        for recall in ordered_bundle.business_discovery_recall_bindings:
            bundle = self._by_snapshot.get(recall.snapshot_id)
            if bundle is None or not any(
                coverage.root.profile_ref == recall.profile_ref
                for coverage in bundle.coverages
            ):
                raise _invalid(
                    "VIEW_DISCOVERY_RECALL_PROFILE_MISMATCH",
                    "discovery recall authority binds a Profile absent from its exact Snapshot",
                )
        # Build the derived feature index when the exact no-payload Bundle is
        # mounted, before any question or search terms are available.  The
        # index is deliberately not authoritative: it can always be rebuilt
        # from the same verified Bundle.
        self._java_feature_indexes = {
            bundle.snapshot_id: _java_feature_index(bundle)
            for bundle in self._bundles
            if any(
                coverage.root.profile_ref
                == JAVA_SOURCE_SEMANTICS_PROFILE_REF
                for coverage in bundle.coverages
            )
        }

    @property
    def session_id(self) -> StableId:
        return self._ordered.session.session_id

    @property
    def read_session(self) -> StructureReadSession:
        """Expose the immutable Session authority, never its connected repository."""

        return self._ordered.session

    @property
    def read_set_digest(self) -> Digest:
        return self._ordered.session.read_set_digest

    @property
    def ordered_bundle_digest(self) -> Digest:
        return self._ordered.digest

    @property
    def snapshot_bundle_digests(self) -> tuple[Digest, ...]:
        return tuple(bundle.digest for bundle in self._bundles)

    @property
    def snapshot_ids(self) -> tuple[StableId, ...]:
        return tuple(bundle.snapshot_id for bundle in self._bundles)

    @property
    def business_discovery_recall_bindings(
        self,
    ) -> tuple[StructureBusinessDiscoveryRecallBinding, ...]:
        return self._ordered.business_discovery_recall_bindings

    def entity_candidates(
        self,
        *,
        snapshot_id: StableId,
        mention: str,
        entity_type: EntityType | str | None = None,
        exact_root_id: StableId | None = None,
        canonical_ga: str | None = None,
        canonical_gav: str | None = None,
        max_candidates: int = 100,
    ) -> StructureViewResult:
        bundle = self._bundle(snapshot_id)
        if not isinstance(mention, str):
            raise _invalid(
                "VIEW_MENTION_TEXT_REQUIRED",
                "entity mention must be text",
            )
        original_mention = unicodedata.normalize("NFC", mention)
        normalized_mention = _mention(mention)
        normalized_type = _optional_enum(EntityType, entity_type, "entity type")
        normalized_ga = _coordinate(canonical_ga, 2, "canonical GA")
        normalized_gav = _coordinate(canonical_gav, 3, "canonical GAV")
        _budget(max_candidates, "candidate budget")
        if exact_root_id is not None and exact_root_id.kind != "entity_root":
            raise _invalid(
                "VIEW_EXACT_ROOT_KIND_INVALID",
                "entity candidate exact Root has the wrong kind",
            )

        coverage_limitations = self._coverage_limitations(
            (bundle,),
            entity_types=(
                (normalized_type,)
                if normalized_type is not None
                else _covered_entity_types(bundle)
            ),
        )

        matched: list[StructureEntityCandidate] = []
        for record in _entities_by_root(bundle).values():
            if normalized_type is not None and record.root.entity_type is not normalized_type:
                continue
            if exact_root_id is not None and record.root_id != exact_root_id:
                continue
            ga, gav = _entity_coordinates(record)
            if normalized_ga is not None and ga != normalized_ga:
                continue
            if normalized_gav is not None and gav != normalized_gav:
                continue
            hits = _mention_hits(record, normalized_mention)
            if hits:
                matched.append(
                    StructureEntityCandidate.create(
                        record=record,
                        matched_fields=hits,
                    )
                )
        matched.sort(key=lambda item: item.entity_root_id.value)
        truncated = len(matched) > max_candidates
        visible = tuple(matched[:max_candidates])
        if truncated:
            status = EntityResolutionStatus.TRUNCATED
            limitations = (
                "ENTITY_CANDIDATE_BUDGET_EXHAUSTED",
                *coverage_limitations,
            )
        elif coverage_limitations:
            status = EntityResolutionStatus.INCOMPLETE_COVERAGE
            limitations = coverage_limitations
        elif not visible:
            status = EntityResolutionStatus.ZERO
            limitations = ("ENTITY_RESOLUTION_ZERO_CANDIDATES",)
        elif len(visible) == 1:
            status = EntityResolutionStatus.UNIQUE
            limitations = ()
        else:
            status = EntityResolutionStatus.AMBIGUOUS
            limitations = ("ENTITY_RESOLUTION_AMBIGUOUS",)
        support = tuple(
            self._entity_support(bundle, candidate.entity_root_id)
            for candidate in visible
        )
        return self._result(
            operation=StructureViewOperation.ENTITY_CANDIDATES,
            bundles=(bundle,),
            completeness=(
                StructureViewCompleteness.PARTIAL
                if truncated or coverage_limitations
                else StructureViewCompleteness.COMPLETE
            ),
            truncated=truncated,
            limitations=limitations,
            payload={
                "mention_original": original_mention,
                "mention": normalized_mention,
                "entity_type": (
                    normalized_type.value if normalized_type is not None else None
                ),
                "exact_root_id": (
                    exact_root_id.value if exact_root_id is not None else None
                ),
                "canonical_ga": normalized_ga,
                "canonical_gav": normalized_gav,
                "resolution_status": status.value,
                "candidate_count": len(visible),
                "max_candidates": max_candidates,
                "candidates": tuple(item.canonical_value() for item in visible),
            },
            support=support,
        )

    def implementation_candidates(
        self,
        *,
        snapshot_id: StableId,
        search_terms: Sequence[str],
        limit: int = 10,
    ) -> StructureViewResult:
        """Discover Java methods from a question-independent formal index."""

        bundle = self._bundle(snapshot_id)
        _require_java_semantics_profile(bundle)
        original_terms, normalized_terms = _feature_query_terms(search_terms)
        if type(limit) is not int or not 1 <= limit <= 20:
            raise _invalid(
                "IMPLEMENTATION_CANDIDATE_LIMIT_INVALID",
                "implementation candidate limit must be from 1 through 20",
            )
        coverage_limitations = self._coverage_limitations(
            (bundle,),
            entity_types=(
                EntityType.JAVA_METHOD,
                EntityType.JAVA_IMPLEMENTATION_ATOM,
                EntityType.JAVA_STATE_SLOT,
            ),
            relation_predicates=(RelationPredicate.CALL_SITE_TARGETS,),
        )
        query_tokens = set(normalized_terms)
        ranked: list[
            tuple[
                tuple[int, int, int, str, str],
                _JavaFeatureIndexEntry,
                tuple[_JavaFeatureTokenSource, ...],
            ]
        ] = []
        feature_index = self._java_feature_indexes.get(bundle.snapshot_id)
        if feature_index is None:
            raise _inconsistent(
                "Java implementation feature index is absent for the exact Bundle"
            )
        feature_index_digest = digest_of(
            [
                "JAVA_IMPLEMENTATION_FEATURE_INDEX@1",
                bundle.snapshot_id.value,
                bundle.digest.value,
                tuple(
                    (
                        entry.method.root_id.value,
                        entry.method.state_id.value,
                        entry.signature,
                        entry.disposition,
                        entry.implementation_completeness,
                        tuple(
                            (
                                item.token,
                                item.field_class,
                                item.member_kind,
                                item.root_id.value,
                            )
                            for item in entry.sources
                        ),
                    )
                    for entry in feature_index
                ),
            ]
        )
        for entry in feature_index:
            matches = tuple(
                item for item in entry.sources if item.token in query_tokens
            )
            if not matches:
                continue
            matched_tokens = {item.token for item in matches}
            matched_classes = {item.field_class for item in matches}
            complete = (
                entry.disposition == JavaSemanticDisposition.SEMANTICS_COMPLETE.value
                and entry.implementation_completeness == "COMPLETE"
            )
            ranked.append(
                (
                    (
                        -len(matched_tokens),
                        -len(matched_classes),
                        -int(complete),
                        entry.signature,
                        entry.method.root_id.value,
                    ),
                    entry,
                    matches,
                )
            )
        ranked.sort(key=lambda item: item[0])
        truncated = len(ranked) > limit
        visible = tuple(ranked[:limit])
        support: list[StructureViewSupport] = []
        candidates: list[dict[str, object]] = []
        for _, entry, matches in visible:
            matched_tokens = tuple(sorted({item.token for item in matches}))
            matched_classes = tuple(
                sorted({item.field_class for item in matches})
            )
            source_refs = tuple(
                {
                    "token": item.token,
                    "field_class": item.field_class,
                    "member_kind": item.member_kind,
                    "root_id": item.root_id.value,
                }
                for item in sorted(
                    set(matches),
                    key=lambda value: (
                        value.token,
                        value.field_class,
                        value.member_kind,
                        value.root_id.value,
                    ),
                )
            )
            candidates.append(
                {
                    "method": _entity_value(entry.method),
                    "canonical_signature": entry.signature,
                    "matched_terms": matched_tokens,
                    "matched_field_classes": matched_classes,
                    "matched_unique_term_count": len(matched_tokens),
                    "matched_field_class_count": len(matched_classes),
                    "method_disposition": entry.disposition,
                    "implementation_semantics_completeness": (
                        entry.implementation_completeness
                    ),
                    "matched_sources": source_refs,
                    "snapshot_id": bundle.snapshot_id.value,
                    "bundle_digest": bundle.digest.value,
                }
            )
            support.append(self._entity_support(bundle, entry.method.root_id))
            support.extend(
                self._member_support(bundle, item.member_kind, item.root_id)
                for item in matches
            )
        if coverage_limitations:
            query_status = "EXECUTION_FAILURE"
            limitations = coverage_limitations
        elif not candidates:
            query_status = "KNOWLEDGE_GAP"
            limitations = ("IMPLEMENTATION_CANDIDATES_ZERO",)
        else:
            query_status = "SUPPORTED"
            limitations = (
                ("IMPLEMENTATION_CANDIDATE_LIMIT_REACHED",)
                if truncated
                else ()
            )
        return self._result(
            operation=StructureViewOperation.IMPLEMENTATION_CANDIDATES,
            bundles=(bundle,),
            completeness=(
                StructureViewCompleteness.PARTIAL
                if limitations
                else StructureViewCompleteness.COMPLETE
            ),
            truncated=truncated,
            limitations=limitations,
            payload={
                "query_status": query_status,
                "search_terms_original": original_terms,
                "normalized_terms": normalized_terms,
                "limit": limit,
                "total": len(ranked),
                "returned": len(candidates),
                "next_cursor": None,
                "candidate_count": len(candidates),
                "candidates": tuple(candidates),
                "ranking": (
                    "MATCHED_TERMS_DESC_FIELD_CLASSES_DESC_"
                    "SEMANTICS_COMPLETE_DESC_SIGNATURE_ROOT_ASC"
                ),
                "snapshot_id": bundle.snapshot_id.value,
                "bundle_digest": bundle.digest.value,
                "feature_index_digest": feature_index_digest.value,
            },
            support=_unique_support(support),
        )

    def method_implementation(
        self,
        *,
        method: StructureEntityArgument,
    ) -> StructureViewResult:
        """Return bounded typed implementation semantics for one exact method."""

        bundle, method_record = self._require_argument(method)
        _require_java_semantics_profile(bundle)
        if method_record.root.entity_type is not EntityType.JAVA_METHOD:
            raise _invalid(
                "VIEW_JAVA_METHOD_ARGUMENT_REQUIRED",
                "method implementation requires a JAVA_METHOD Entity",
            )
        coverage_limitations = self._coverage_limitations(
            (bundle,),
            entity_types=(
                EntityType.JAVA_METHOD,
                EntityType.JAVA_IMPLEMENTATION_ATOM,
                EntityType.JAVA_STATE_SLOT,
            ),
            relation_predicates=(
                RelationPredicate.HAS_IMPLEMENTATION_ATOM,
                RelationPredicate.CONTROLS,
                RelationPredicate.NEXT_IN_SOURCE,
                RelationPredicate.CALL_SITE_TARGETS,
                RelationPredicate.READS_STATE,
                RelationPredicate.WRITES_STATE,
                RelationPredicate.HANDLES_THROW,
                RelationPredicate.CALLS,
            ),
        )
        entities = _entities_by_root(bundle)
        memberships = tuple(
            sorted(
                (
                    item
                    for item in bundle.relation_facts
                    if item.root.predicate
                    is RelationPredicate.HAS_IMPLEMENTATION_ATOM
                    and item.root.subject.entity_root_id == method_record.root_id
                ),
                key=lambda item: (
                    _mapping_int(
                        item.state.predicate_state_payload_fields,
                        "source_order_ordinal",
                    ),
                    item.root.object.entity_root_id.value,
                ),
            )
        )
        atoms: list[EntityRecord] = []
        for membership in memberships:
            atom = entities.get(membership.root.object.entity_root_id)
            if (
                atom is None
                or atom.root.entity_type
                is not EntityType.JAVA_IMPLEMENTATION_ATOM
            ):
                raise _inconsistent(
                    "implementation membership endpoint is absent or not an Atom"
                )
            atoms.append(atom)
        atom_ids = {item.root_id for item in atoms}
        slots = tuple(
            sorted(
                (
                    item
                    for item in entities.values()
                    if item.root.entity_type is EntityType.JAVA_STATE_SLOT
                    and item.root.root_fields["declaring_entity_root_id"]
                    == method_record.root_id.value
                ),
                key=lambda item: (
                    item.root.root_fields["declaration_ordinal"],
                    item.root_id.value,
                ),
            )
        )
        implementation_predicates = {
            RelationPredicate.CONTROLS,
            RelationPredicate.NEXT_IN_SOURCE,
            RelationPredicate.CALL_SITE_TARGETS,
            RelationPredicate.READS_STATE,
            RelationPredicate.WRITES_STATE,
            RelationPredicate.HANDLES_THROW,
        }
        implementation_relations = tuple(
            sorted(
                (
                    item
                    for item in bundle.relation_facts
                    if item.root.predicate in implementation_predicates
                    and item.root.subject.entity_root_id in atom_ids
                ),
                key=lambda item: (
                    item.root.predicate.value,
                    item.root.subject.entity_root_id.value,
                    item.root.object.entity_root_id.value,
                    item.root.observation_modality.value,
                ),
            )
        )
        legacy_calls = tuple(
            sorted(
                (
                    item
                    for item in bundle.relation_facts
                    if item.root.predicate is RelationPredicate.CALLS
                    and item.root.subject.entity_root_id == method_record.root_id
                ),
                key=lambda item: (
                    item.root.object.entity_root_id.value,
                    item.root_id.value,
                ),
            )
        )
        method_fields = method_record.state.state_payload_fields
        disposition = _field_text(method_fields, "method_disposition")
        implementation_completeness = _field_text(
            method_fields,
            "implementation_semantics_completeness",
        )
        method_complete = (
            disposition == JavaSemanticDisposition.SEMANTICS_COMPLETE.value
            and implementation_completeness == "COMPLETE"
        )
        limitations = (
            *coverage_limitations,
            *(("METHOD_SEMANTICS_INCOMPLETE",) if not method_complete else ()),
        )
        support: list[StructureViewSupport] = [
            self._entity_support(bundle, method_record.root_id)
        ]
        support.extend(
            self._relation_support(bundle, item) for item in memberships
        )
        support.extend(self._entity_support(bundle, item.root_id) for item in atoms)
        support.extend(self._entity_support(bundle, item.root_id) for item in slots)
        support.extend(
            self._relation_support(bundle, item)
            for item in (*implementation_relations, *legacy_calls)
        )
        referenced_entity_ids = {
            endpoint
            for relation in (*implementation_relations, *legacy_calls)
            for endpoint in (
                relation.root.subject.entity_root_id,
                relation.root.object.entity_root_id,
            )
            if endpoint not in atom_ids and endpoint != method_record.root_id
        }
        support.extend(
            self._entity_support(bundle, root_id)
            for root_id in sorted(
                referenced_entity_ids & set(entities),
                key=lambda item: item.value,
            )
        )
        return self._result(
            operation=StructureViewOperation.METHOD_IMPLEMENTATION,
            bundles=(bundle,),
            completeness=(
                StructureViewCompleteness.PARTIAL
                if limitations
                else StructureViewCompleteness.COMPLETE
            ),
            truncated=False,
            limitations=limitations,
            payload={
                "query_status": (
                    "SUPPORTED"
                    if not limitations
                    else "METHOD_SEMANTICS_LIMITATION"
                ),
                "method": _entity_value(method_record),
                "canonical_signature": _java_method_signature(method_record),
                "method_disposition": disposition,
                "declaration_completeness": _field_text(
                    method_fields,
                    "declaration_completeness",
                ),
                "legacy_static_call_completeness": _field_text(
                    method_fields,
                    "legacy_static_call_completeness",
                ),
                "implementation_semantics_completeness": (
                    implementation_completeness
                ),
                "negative_conclusion_supported": (
                    method_complete and not coverage_limitations
                ),
                "state_slots": tuple(_entity_value(item) for item in slots),
                "ordered_atoms": tuple(_entity_value(item) for item in atoms),
                "implementation_relations": tuple(
                    _relation_value(item) for item in implementation_relations
                ),
                "legacy_calls_direction": "OUTGOING",
                "legacy_calls": tuple(
                    _relation_value(item) for item in legacy_calls
                ),
                "snapshot_id": bundle.snapshot_id.value,
                "bundle_digest": bundle.digest.value,
            },
            support=_unique_support(support),
        )

    def child_module_inventory(
        self,
        *,
        system: StructureEntityArgument,
    ) -> StructureViewResult:
        bundle, system_record = self._require_argument(system)
        if system_record.root.entity_type is not EntityType.SOFTWARE_SYSTEM:
            raise _invalid(
                "VIEW_SOFTWARE_SYSTEM_ARGUMENT_REQUIRED",
                "child module inventory requires a SOFTWARE_SYSTEM Entity",
            )
        coverage_limitations = self._coverage_limitations(
            (bundle,),
            entity_types=(EntityType.SOFTWARE_SYSTEM, EntityType.MAVEN_MODULE),
            relation_predicates=(RelationPredicate.CONTAINS_MODULE,),
        )
        relations = tuple(
            sorted(
                (
                    item
                    for item in bundle.relation_facts
                    if item.root.predicate is RelationPredicate.CONTAINS_MODULE
                    and item.root.subject.entity_root_id == system.entity_root_id
                ),
                key=lambda item: (
                    item.root.object.entity_root_id.value,
                    item.root_id.value,
                ),
            )
        )
        entities = _entities_by_root(bundle)
        modules: list[dict[str, object]] = []
        support: list[StructureViewSupport] = [
            self._entity_support(bundle, system_record.root_id)
        ]
        for relation in relations:
            target = entities.get(relation.root.object.entity_root_id)
            if target is None or target.root.entity_type is not EntityType.MAVEN_MODULE:
                raise _inconsistent(
                    "CONTAINS_MODULE endpoint is absent or not a MAVEN_MODULE"
                )
            modules.append(_entity_value(target))
            support.extend(
                (
                    self._relation_support(bundle, relation),
                    self._entity_support(bundle, target.root_id),
                )
            )
        return self._result(
            operation=StructureViewOperation.CHILD_MODULE_INVENTORY,
            bundles=(bundle,),
            completeness=(
                StructureViewCompleteness.PARTIAL
                if coverage_limitations
                else StructureViewCompleteness.COMPLETE
            ),
            truncated=False,
            limitations=coverage_limitations,
            payload={
                "system": _entity_value(system_record),
                "module_count": len(modules),
                "modules": tuple(modules),
                "relation_predicate": RelationPredicate.CONTAINS_MODULE.value,
                "relation_modality": ObservationModality.RECURSIVE_REACTOR_MEMBERSHIP.value,
            },
            support=support,
        )

    def declared_method_inventory(
        self,
        *,
        java_type: StructureEntityArgument,
    ) -> StructureViewResult:
        bundle, type_record = self._require_argument(java_type)
        if type_record.root.entity_type is not EntityType.JAVA_TYPE:
            raise _invalid(
                "VIEW_JAVA_TYPE_ARGUMENT_REQUIRED",
                "declared method inventory requires a JAVA_TYPE Entity",
            )
        coverage_limitations = self._coverage_limitations(
            (bundle,),
            entity_types=(EntityType.JAVA_TYPE, EntityType.JAVA_METHOD),
            relation_predicates=(RelationPredicate.DECLARES_METHOD,),
        )
        relations = tuple(
            sorted(
                (
                    item
                    for item in bundle.relation_facts
                    if item.root.predicate is RelationPredicate.DECLARES_METHOD
                    and item.root.subject.entity_root_id == java_type.entity_root_id
                ),
                key=lambda item: (
                    _mapping_int(
                        item.state.predicate_state_payload_fields,
                        "declaration_ordinal",
                    ),
                    item.root.object.entity_root_id.value,
                ),
            )
        )
        entities = _entities_by_root(bundle)
        methods: list[dict[str, object]] = []
        support: list[StructureViewSupport] = [
            self._entity_support(bundle, type_record.root_id)
        ]
        for relation in relations:
            target = entities.get(relation.root.object.entity_root_id)
            if target is None or target.root.entity_type is not EntityType.JAVA_METHOD:
                raise _inconsistent(
                    "DECLARES_METHOD endpoint is absent or not a JAVA_METHOD"
                )
            methods.append(_entity_value(target))
            support.extend(
                (
                    self._relation_support(bundle, relation),
                    self._entity_support(bundle, target.root_id),
                )
            )
        return self._result(
            operation=StructureViewOperation.DECLARED_METHOD_INVENTORY,
            bundles=(bundle,),
            completeness=(
                StructureViewCompleteness.PARTIAL
                if coverage_limitations
                else StructureViewCompleteness.COMPLETE
            ),
            truncated=False,
            limitations=coverage_limitations,
            payload={
                "java_type": _entity_value(type_record),
                "method_count": len(methods),
                "methods": tuple(methods),
                "relation_predicate": RelationPredicate.DECLARES_METHOD.value,
                "relation_modality": (
                    ObservationModality.JAVA_SOURCE_DECLARATION.value
                ),
            },
            support=support,
        )

    def direct_neighborhood(
        self,
        *,
        entity: StructureEntityArgument,
        direction: NeighborhoodDirection | str = NeighborhoodDirection.BOTH,
        predicate: RelationPredicate | str | None = None,
    ) -> StructureViewResult:
        bundle, entity_record = self._require_argument(entity)
        normalized_direction = _enum(
            NeighborhoodDirection, direction, "neighborhood direction"
        )
        normalized_predicate = _optional_enum(
            RelationPredicate, predicate, "relation predicate"
        )
        coverage_limitations = self._coverage_limitations(
            (bundle,),
            entity_types=(entity_record.root.entity_type,),
            relation_predicates=(
                (normalized_predicate,)
                if normalized_predicate is not None
                else _covered_relation_predicates(bundle)
            ),
        )
        relations: list[RelationFactRecord] = []
        for relation in bundle.relation_facts:
            if normalized_predicate is not None and relation.root.predicate is not normalized_predicate:
                continue
            outgoing = relation.root.subject.entity_root_id == entity.entity_root_id
            incoming = relation.root.object.entity_root_id == entity.entity_root_id
            if (
                (normalized_direction is NeighborhoodDirection.OUTGOING and outgoing)
                or (normalized_direction is NeighborhoodDirection.INCOMING and incoming)
                or (normalized_direction is NeighborhoodDirection.BOTH and (outgoing or incoming))
            ):
                relations.append(relation)
        relations.sort(key=lambda item: item.root_id.value)
        entities = _entities_by_root(bundle)
        neighbor_ids = sorted(
            {
                endpoint
                for relation in relations
                for endpoint in (
                    relation.root.subject.entity_root_id,
                    relation.root.object.entity_root_id,
                )
                if endpoint != entity.entity_root_id
            },
            key=lambda item: item.value,
        )
        support: list[StructureViewSupport] = [
            self._entity_support(bundle, entity_record.root_id)
        ]
        for relation in relations:
            support.append(self._relation_support(bundle, relation))
        for root_id in neighbor_ids:
            if root_id in entities:
                support.append(self._entity_support(bundle, root_id))
        return self._result(
            operation=StructureViewOperation.DIRECT_NEIGHBORHOOD,
            bundles=(bundle,),
            completeness=(
                StructureViewCompleteness.PARTIAL
                if coverage_limitations
                else StructureViewCompleteness.COMPLETE
            ),
            truncated=False,
            limitations=coverage_limitations,
            payload={
                "entity": _entity_value(entity_record),
                "direction": normalized_direction.value,
                "predicate": (
                    normalized_predicate.value
                    if normalized_predicate is not None
                    else None
                ),
                "relations": tuple(_relation_value(item) for item in relations),
                "neighbors": tuple(
                    _entity_value(entities[item]) for item in neighbor_ids
                ),
            },
            support=support,
        )

    def path_exists(
        self,
        *,
        source: StructureEntityArgument,
        target: StructureEntityArgument,
        predicate: RelationPredicate | str = RelationPredicate.DEPENDS_ON,
        max_depth: int = 64,
        max_expansions: int = 100_000,
    ) -> StructureViewResult:
        bundle, source_record = self._require_argument(source)
        target_bundle, target_record = self._require_argument(target)
        if target_bundle.snapshot_id != bundle.snapshot_id:
            raise _invalid(
                "VIEW_PATH_SNAPSHOT_MISMATCH",
                "path endpoints must belong to the same exact Snapshot",
            )
        normalized_predicate = _enum(
            RelationPredicate, predicate, "path relation predicate"
        )
        coverage_limitations = self._coverage_limitations(
            (bundle,),
            entity_types=(
                source_record.root.entity_type,
                target_record.root.entity_type,
            ),
            relation_predicates=(normalized_predicate,),
        )
        _budget(max_depth, "path depth budget")
        _budget(max_expansions, "path expansion budget")
        paths, truncated, expansions = _simple_paths(
            bundle,
            source.entity_root_id,
            target.entity_root_id,
            predicate=normalized_predicate,
            max_depth=max_depth,
            max_paths=1,
            max_expansions=max_expansions,
            stop_after_first=True,
        )
        exists = bool(paths)
        if truncated or coverage_limitations:
            completeness = StructureViewCompleteness.PARTIAL
            limitations = (
                *(("PATH_SEARCH_TRUNCATED",) if truncated else ()),
                *coverage_limitations,
            )
        else:
            completeness = StructureViewCompleteness.COMPLETE
            limitations = ()
        support = _unique_support(
            (
                self._entity_support(bundle, source_record.root_id),
                self._entity_support(bundle, target_record.root_id),
                *self._path_support(bundle, paths),
            )
        )
        return self._result(
            operation=StructureViewOperation.PATH_EXISTS,
            bundles=(bundle,),
            completeness=completeness,
            truncated=truncated,
            limitations=limitations,
            payload={
                "source": _entity_value(source_record),
                "target": _entity_value(target_record),
                "predicate": normalized_predicate.value,
                "max_depth": max_depth,
                "max_expansions": max_expansions,
                "expansions": expansions,
                "exists": exists,
                "path": paths[0] if paths else None,
                "negative_conclusion_supported": (
                    not exists and not truncated and not coverage_limitations
                ),
            },
            support=support,
        )

    def all_simple_paths(
        self,
        *,
        source: StructureEntityArgument,
        target: StructureEntityArgument,
        predicate: RelationPredicate | str = RelationPredicate.DEPENDS_ON,
        max_depth: int = 64,
        max_paths: int = 1000,
        max_expansions: int = 100_000,
    ) -> StructureViewResult:
        bundle, source_record = self._require_argument(source)
        target_bundle, target_record = self._require_argument(target)
        if target_bundle.snapshot_id != bundle.snapshot_id:
            raise _invalid(
                "VIEW_PATH_SNAPSHOT_MISMATCH",
                "path endpoints must belong to the same exact Snapshot",
            )
        normalized_predicate = _enum(
            RelationPredicate, predicate, "path relation predicate"
        )
        coverage_limitations = self._coverage_limitations(
            (bundle,),
            entity_types=(
                source_record.root.entity_type,
                target_record.root.entity_type,
            ),
            relation_predicates=(normalized_predicate,),
        )
        _budget(max_depth, "path depth budget")
        _budget(max_paths, "path count budget")
        _budget(max_expansions, "path expansion budget")
        paths, truncated, expansions = _simple_paths(
            bundle,
            source.entity_root_id,
            target.entity_root_id,
            predicate=normalized_predicate,
            max_depth=max_depth,
            max_paths=max_paths,
            max_expansions=max_expansions,
            stop_after_first=False,
        )
        return self._result(
            operation=StructureViewOperation.ALL_SIMPLE_PATHS,
            bundles=(bundle,),
            completeness=(
                StructureViewCompleteness.PARTIAL
                if truncated or coverage_limitations
                else StructureViewCompleteness.COMPLETE
            ),
            truncated=truncated,
            limitations=(
                *(("PATH_SEARCH_TRUNCATED",) if truncated else ()),
                *coverage_limitations,
            ),
            payload={
                "source": _entity_value(source_record),
                "target": _entity_value(target_record),
                "predicate": normalized_predicate.value,
                "max_depth": max_depth,
                "max_paths": max_paths,
                "max_expansions": max_expansions,
                "expansions": expansions,
                "path_count": len(paths),
                "paths": paths,
                "negative_conclusion_supported": (
                    not paths and not truncated and not coverage_limitations
                ),
            },
            support=_unique_support(
                (
                    self._entity_support(bundle, source_record.root_id),
                    self._entity_support(bundle, target_record.root_id),
                    *self._path_support(bundle, paths),
                )
            ),
        )

    def ordered_snapshot_diff(
        self,
        *,
        base_snapshot_id: StableId,
        target_snapshot_id: StableId,
    ) -> StructureViewResult:
        base = self._bundle(base_snapshot_id)
        target = self._bundle(target_snapshot_id)
        order = self.snapshot_ids
        try:
            base_ordinal = order.index(base_snapshot_id)
            target_ordinal = order.index(target_snapshot_id)
        except ValueError as exc:  # pragma: no cover - _bundle already fences this
            raise _invalid(
                "VIEW_DIFF_SNAPSHOT_NOT_IN_READ_SET",
                "diff Snapshot is not in the ordered Read Set",
            ) from exc
        if target_ordinal != base_ordinal + 1:
            raise _invalid(
                "VIEW_DIFF_ORDER_INVALID",
                "Snapshot diff requires an adjacent caller-declared base/target pair",
            )
        comparison = tuple(
            item
            for item in self._ordered.session.context_comparisons
            if item.ordinal == base_ordinal
            and item.base_snapshot_id == base_snapshot_id
            and item.target_snapshot_id == target_snapshot_id
        )
        if (
            len(comparison) != 1
            or comparison[0].outcome
            is not StructureContextComparisonOutcome.COMPATIBLE
        ):
            raise _invalid(
                "VIEW_DIFF_CONTEXT_INCOMPATIBLE",
                "Snapshot diff requires the exact compatible Context assessment",
            )
        entity_diff = _record_diff(
            base.entities,
            target.entities,
            value=_entity_value,
        )
        relation_diff = _record_diff(
            base.relation_facts,
            target.relation_facts,
            value=_relation_value,
        )
        literal_diff = _record_diff(
            base.literal_facts,
            target.literal_facts,
            value=_literal_value,
        )
        support = _diff_support(self, base, target, entity_diff, relation_diff, literal_diff)
        return self._result(
            operation=StructureViewOperation.ORDERED_SNAPSHOT_DIFF,
            bundles=(base, target),
            completeness=StructureViewCompleteness.COMPLETE,
            truncated=False,
            limitations=(),
            payload={
                "base_snapshot_id": base_snapshot_id.value,
                "target_snapshot_id": target_snapshot_id.value,
                "base_ordinal": base_ordinal,
                "target_ordinal": target_ordinal,
                "context_assessment_id": comparison[0].assessment_id.value,
                "context_assessment_digest": comparison[0].digest.value,
                "entities": entity_diff,
                "relations": relation_diff,
                "literals": literal_diff,
            },
            support=support,
        )

    def _bundle(self, snapshot_id: StableId) -> StructureSnapshotReadBundle:
        try:
            return self._by_snapshot[snapshot_id]
        except KeyError as exc:
            raise _invalid(
                "VIEW_SNAPSHOT_NOT_IN_READ_SET",
                "Structure View Snapshot is outside the exact ordered Read Set",
            ) from exc

    def _require_argument(
        self, argument: StructureEntityArgument
    ) -> tuple[StructureSnapshotReadBundle, EntityRecord]:
        if not isinstance(argument, StructureEntityArgument):
            raise _invalid(
                "VIEW_TYPED_ENTITY_ARGUMENT_REQUIRED",
                "Structure View operation requires a typed Entity argument",
            )
        bundle = self._bundle(argument.snapshot_id)
        if (
            argument.session_id != self.session_id
            or argument.read_set_digest != self.read_set_digest
            or argument.ordered_bundle_digest != self.ordered_bundle_digest
            or argument.snapshot_bundle_digest != bundle.digest
        ):
            raise _invalid(
                "VIEW_ENTITY_ARGUMENT_SESSION_MISMATCH",
                "typed Entity argument belongs to another Read Session or Bundle",
            )
        record = _entities_by_root(bundle).get(argument.entity_root_id)
        if record is None or record.state_id != argument.entity_state_id:
            raise _invalid(
                "VIEW_ENTITY_ARGUMENT_NOT_IN_SNAPSHOT",
                "typed Entity argument does not match the exact Snapshot State",
            )
        argument.require_valid()
        if argument.origin in {
            StructureViewArgumentOrigin.SEALED_UNIQUE_CANDIDATE,
            StructureViewArgumentOrigin.SEALED_RESULT_MEMBER,
        }:
            if (
                argument.candidate_result_id is None
                or argument.candidate_result_digest is None
                or argument.candidate_result is None
            ):
                raise _invalid(
                    "VIEW_CANDIDATE_PROOF_REQUIRED",
                    "candidate-derived Entity argument lacks its sealed proof",
                )
            proof = argument.candidate_result
            if (
                proof.result_id != argument.candidate_result_id
                or proof.digest != argument.candidate_result_digest
            ):
                raise _invalid(
                    "VIEW_CANDIDATE_PROOF_MISMATCH",
                    "candidate-derived Entity argument proof identity does not match",
                )
            replay = _replay_structure_view_result(self, proof)
            if replay != proof:
                raise _invalid(
                    "VIEW_CANDIDATE_PROOF_INVALID",
                    "result-derived Entity argument does not contain a valid sealed Result",
                )
        elif (
            argument.origin is not StructureViewArgumentOrigin.CALLER_EXACT_REF
            or argument.candidate_result is not None
            or argument.candidate_result_id is not None
            or argument.candidate_result_digest is not None
        ):
            raise _invalid(
                "VIEW_ENTITY_ARGUMENT_ORIGIN_INVALID",
                "typed Entity argument origin is inconsistent",
            )
        expected = StructureEntityArgument._create(
            origin=argument.origin,
            session_id=argument.session_id,
            read_set_digest=argument.read_set_digest,
            ordered_bundle_digest=argument.ordered_bundle_digest,
            snapshot_id=argument.snapshot_id,
            snapshot_bundle_digest=argument.snapshot_bundle_digest,
            entity_root_id=argument.entity_root_id,
            entity_state_id=argument.entity_state_id,
            candidate_result=argument.candidate_result,
            candidate_result_id=argument.candidate_result_id,
            candidate_result_digest=argument.candidate_result_digest,
        )
        if expected.digest != argument.digest:
            raise _invalid(
                "VIEW_ENTITY_ARGUMENT_DIGEST_MISMATCH",
                "typed Entity argument is not canonical",
            )
        return bundle, record

    def _result(
        self,
        *,
        operation: StructureViewOperation,
        bundles: Sequence[StructureSnapshotReadBundle],
        completeness: StructureViewCompleteness,
        truncated: bool,
        limitations: Sequence[str],
        payload: Mapping[str, object],
        support: Sequence[StructureViewSupport],
    ) -> StructureViewResult:
        coverage_support = tuple(
            self._coverage_support(bundle, coverage)
            for bundle in bundles
            for coverage in bundle.coverages
        )
        return StructureViewResult.create(
            operation=operation,
            ordered=self._ordered,
            selected_bundles=bundles,
            completeness=completeness,
            truncated=truncated,
            limitations=limitations,
            payload=payload,
            support_map=_unique_support((*support, *coverage_support)),
        )

    @staticmethod
    def _coverage_limitations(
        bundles: Sequence[StructureSnapshotReadBundle],
        *,
        entity_types: Sequence[EntityType] = (),
        relation_predicates: Sequence[RelationPredicate] = (),
    ) -> tuple[str, ...]:
        """Return fail-closed limitations for requirements outside exact Coverage.

        A query spanning an exact Snapshot cannot treat a declaration from one
        Coverage root as completing another root's domain.  Every selected
        Coverage must therefore declare each Entity type and Relation predicate
        required by the operation.
        """

        required_types = set(entity_types)
        required_predicates = set(relation_predicates)
        limitations: list[str] = []
        if required_types and any(
            not bundle.coverages
            or any(
                not required_types.issubset(
                    set(coverage.root.covered_entity_types)
                )
                for coverage in bundle.coverages
            )
            for bundle in bundles
        ):
            limitations.append("VIEW_ENTITY_TYPE_COVERAGE_INSUFFICIENT")
        if required_predicates and any(
            not bundle.coverages
            or any(
                not required_predicates.issubset(
                    set(coverage.root.covered_relation_predicates)
                )
                for coverage in bundle.coverages
            )
            for bundle in bundles
        ):
            limitations.append("VIEW_RELATION_PREDICATE_COVERAGE_INSUFFICIENT")
        return tuple(limitations)

    def _entity_support(
        self,
        bundle: StructureSnapshotReadBundle,
        root_id: StableId,
    ) -> StructureViewSupport:
        record = _entities_by_root(bundle).get(root_id)
        if record is None:
            raise _inconsistent("View Support Entity is absent from exact bundle")
        support_snapshot_id = bundle.snapshot_id
        for upstream in bundle.upstream_entity_records:
            if upstream.entity.root_id == root_id:
                support_snapshot_id = upstream.snapshot_id
                break
        return StructureViewSupport.create(
            snapshot_id=support_snapshot_id,
            member_kind="ENTITY",
            root_id=record.root_id,
            state_id=record.state_id,
            state_digest=record.state_digest,
            evidence=_evidence_for(bundle, record.state.evidence_references),
        )

    def _coverage_support(
        self,
        bundle: StructureSnapshotReadBundle,
        record: CoverageRecord,
    ) -> StructureViewSupport:
        return StructureViewSupport.create(
            snapshot_id=bundle.snapshot_id,
            member_kind="COVERAGE",
            root_id=record.root_id,
            state_id=record.state_id,
            state_digest=record.state.state_digest,
            evidence=_evidence_for(bundle, record.state.evidence_references),
        )

    def _relation_support(
        self,
        bundle: StructureSnapshotReadBundle,
        record: RelationFactRecord,
    ) -> StructureViewSupport:
        return StructureViewSupport.create(
            snapshot_id=bundle.snapshot_id,
            member_kind="RELATION_FACT",
            root_id=record.root_id,
            state_id=record.state_id,
            state_digest=record.state_digest,
            evidence=_evidence_for(bundle, record.state.evidence_references),
        )

    def _member_support(
        self,
        bundle: StructureSnapshotReadBundle,
        member_kind: str,
        root_id: StableId,
    ) -> StructureViewSupport:
        if member_kind == "ENTITY":
            return self._entity_support(bundle, root_id)
        if member_kind == "RELATION_FACT":
            relation = {item.root_id: item for item in bundle.relation_facts}.get(
                root_id
            )
            if relation is None:
                raise _inconsistent(
                    "feature-index Support references an absent Relation"
                )
            return self._relation_support(bundle, relation)
        raise _inconsistent("feature-index Support has an unknown member kind")

    def _literal_support(
        self,
        bundle: StructureSnapshotReadBundle,
        record: LiteralFactRecord,
    ) -> StructureViewSupport:
        return StructureViewSupport.create(
            snapshot_id=bundle.snapshot_id,
            member_kind="LITERAL_FACT",
            root_id=record.root_id,
            state_id=record.state_id,
            state_digest=record.state_digest,
            evidence=_evidence_for(bundle, record.state.evidence_references),
        )

    def _path_support(
        self,
        bundle: StructureSnapshotReadBundle,
        paths: Sequence[Mapping[str, object]],
    ) -> tuple[StructureViewSupport, ...]:
        relation_ids = {
            StableId(item)
            for path in paths
            for item in _mapping_string_sequence(path, "relation_root_ids")
        }
        entity_ids = {
            StableId(item)
            for path in paths
            for item in _mapping_string_sequence(path, "entity_root_ids")
        }
        relations = {item.root_id: item for item in bundle.relation_facts}
        support: list[StructureViewSupport] = []
        for root_id in sorted(entity_ids, key=lambda item: item.value):
            support.append(self._entity_support(bundle, root_id))
        for root_id in sorted(relation_ids, key=lambda item: item.value):
            relation = relations.get(root_id)
            if relation is None:
                raise _inconsistent("path Support references an absent Relation")
            support.append(self._relation_support(bundle, relation))
        return tuple(support)


def _simple_paths(
    bundle: StructureSnapshotReadBundle,
    source: StableId,
    target: StableId,
    *,
    predicate: RelationPredicate,
    max_depth: int,
    max_paths: int,
    max_expansions: int,
    stop_after_first: bool,
) -> tuple[tuple[dict[str, object], ...], bool, int]:
    entities = _entities_by_root(bundle)
    if source not in entities or target not in entities:
        raise _invalid(
            "VIEW_PATH_ENDPOINT_NOT_IN_SNAPSHOT",
            "path endpoint is absent from the exact Snapshot bundle",
        )
    adjacency: dict[StableId, list[tuple[StableId, RelationFactRecord]]] = {}
    for relation in bundle.relation_facts:
        if relation.root.predicate is not predicate:
            continue
        adjacency.setdefault(relation.root.subject.entity_root_id, []).append(
            (relation.root.object.entity_root_id, relation)
        )
    for edges in adjacency.values():
        edges.sort(key=lambda item: (item[0].value, item[1].root_id.value))

    paths: list[dict[str, object]] = []
    truncated = False
    expansions = 0
    stack: list[
        tuple[StableId, tuple[StableId, ...], tuple[RelationFactRecord, ...]]
    ] = [(source, (source,), ())]
    while stack:
        if expansions >= max_expansions:
            truncated = True
            break
        node, entity_path, relation_path = stack.pop()
        expansions += 1
        if node == target:
            paths.append(
                {
                    "entity_root_ids": tuple(item.value for item in entity_path),
                    "entity_state_ids": tuple(
                        entities[item].state_id.value for item in entity_path
                    ),
                    "relation_root_ids": tuple(
                        item.root_id.value for item in relation_path
                    ),
                    "relation_state_ids": tuple(
                        item.state_id.value for item in relation_path
                    ),
                }
            )
            if stop_after_first:
                break
            if len(paths) > max_paths:
                truncated = True
                paths.pop()
                break
            continue
        edges = adjacency.get(node, ())
        if len(relation_path) >= max_depth:
            if any(next_node not in entity_path for next_node, _ in edges):
                truncated = True
            continue
        for next_node, relation in reversed(edges):
            if next_node in entity_path:
                continue
            stack.append(
                (
                    next_node,
                    (*entity_path, next_node),
                    (*relation_path, relation),
                )
            )
    return tuple(paths), truncated, expansions


def _record_diff(
    base_records: Sequence[object],
    target_records: Sequence[object],
    *,
    value,
) -> CanonicalFields:
    base = {item.root_id: item for item in base_records}
    target = {item.root_id: item for item in target_records}
    base_ids = set(base)
    target_ids = set(target)
    added = tuple(
        value(target[item]) for item in sorted(target_ids - base_ids, key=lambda x: x.value)
    )
    removed = tuple(
        value(base[item]) for item in sorted(base_ids - target_ids, key=lambda x: x.value)
    )
    unchanged: list[dict[str, object]] = []
    state_changed: list[dict[str, object]] = []
    for root_id in sorted(base_ids & target_ids, key=lambda item: item.value):
        base_item = base[root_id]
        target_item = target[root_id]
        if base_item.state_id == target_item.state_id:
            unchanged.append(value(target_item))
        else:
            state_changed.append(
                {
                    "root_id": root_id.value,
                    "base": value(base_item),
                    "target": value(target_item),
                }
            )
    return CanonicalFields(
        {
            "added": added,
            "removed": removed,
            "unchanged": tuple(unchanged),
            "state_changed": tuple(state_changed),
            "counts": {
                "added": len(added),
                "removed": len(removed),
                "unchanged": len(unchanged),
                "state_changed": len(state_changed),
            },
        }
    )


def _diff_support(
    service: StructureViewService,
    base: StructureSnapshotReadBundle,
    target: StructureSnapshotReadBundle,
    entity_diff: CanonicalFields,
    relation_diff: CanonicalFields,
    literal_diff: CanonicalFields,
) -> tuple[StructureViewSupport, ...]:
    support: list[StructureViewSupport] = []
    for bundle, side in ((base, "base"), (target, "target")):
        for diff, kind in (
            (entity_diff, "ENTITY"),
            (relation_diff, "RELATION_FACT"),
            (literal_diff, "LITERAL_FACT"),
        ):
            root_ids: set[StableId] = set()
            selected = (
                (*diff["added"], *diff["unchanged"])
                if side == "target"
                else (*diff["removed"], *diff["unchanged"])
            )
            for entry in selected:
                assert isinstance(entry, CanonicalFields)
                root_ids.add(StableId(_mapping_text(entry, "root_id")))
            for entry in diff["state_changed"]:
                assert isinstance(entry, CanonicalFields)
                root_ids.add(StableId(_mapping_text(entry, "root_id")))
            for root_id in sorted(root_ids, key=lambda item: item.value):
                if kind == "ENTITY":
                    support.append(service._entity_support(bundle, root_id))
                elif kind == "RELATION_FACT":
                    record = {item.root_id: item for item in bundle.relation_facts}.get(root_id)
                    if record is None:
                        raise _inconsistent("diff Relation Support is absent")
                    support.append(service._relation_support(bundle, record))
                else:
                    record = {item.root_id: item for item in bundle.literal_facts}.get(root_id)
                    if record is None:
                        raise _inconsistent("diff Literal Support is absent")
                    support.append(service._literal_support(bundle, record))
    return _unique_support(support)


def _entities_by_root(
    bundle: StructureSnapshotReadBundle,
) -> dict[StableId, EntityRecord]:
    values = {item.root_id: item for item in bundle.entities}
    for upstream in bundle.upstream_entity_records:
        previous = values.get(upstream.entity.root_id)
        if previous is not None and previous != upstream.entity:
            raise _inconsistent(
                "local and upstream Bundle Entity bindings conflict"
            )
        values[upstream.entity.root_id] = upstream.entity
    return dict(sorted(values.items(), key=lambda item: item[0].value))


def _require_java_semantics_profile(
    bundle: StructureSnapshotReadBundle,
) -> None:
    profiles = {item.root.profile_ref for item in bundle.coverages}
    if profiles != {JAVA_SOURCE_SEMANTICS_PROFILE_REF}:
        raise _invalid(
            "IMPLEMENTATION_QUERY_PROFILE_UNSUPPORTED",
            "implementation query requires one exact Java Source Semantics Coverage",
        )


def _feature_query_terms(
    values: Sequence[str],
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise _invalid(
            "IMPLEMENTATION_SEARCH_TERMS_INVALID",
            "implementation search terms must be an ordered sequence",
        )
    if not 1 <= len(values) <= 12:
        raise _invalid(
            "IMPLEMENTATION_SEARCH_TERMS_INVALID",
            "implementation search requires from 1 through 12 terms",
        )
    original: list[str] = []
    normalized: set[str] = set()
    for raw in values:
        term = _text(raw, "implementation search term")
        if len(term.encode("utf-8")) > 128:
            raise _invalid(
                "IMPLEMENTATION_SEARCH_TERM_BUDGET_EXCEEDED",
                "implementation search term exceeds 128 UTF-8 bytes",
            )
        tokens = _feature_tokens(term)
        if not tokens:
            raise _invalid(
                "IMPLEMENTATION_SEARCH_TERM_EMPTY",
                "implementation search term has no canonical identifier token",
            )
        original.append(term)
        normalized.update(tokens)
    if len(normalized) > 64:
        raise _invalid(
            "IMPLEMENTATION_SEARCH_TOKEN_BUDGET_EXCEEDED",
            "implementation search exceeds 64 normalized tokens",
        )
    return tuple(original), tuple(sorted(normalized))


def _feature_tokens(value: str) -> tuple[str, ...]:
    normalized = unicodedata.normalize("NFC", value)
    tokens: set[str] = set()
    for segment in re.split(r"[^0-9A-Za-z]+", normalized):
        if not segment:
            continue
        parts = _FEATURE_TOKEN_PART.findall(segment)
        if not parts:
            parts = [segment]
        tokens.update(part.casefold() for part in parts if part)
    return tuple(sorted(token for token in tokens if token))


def _java_method_signature(record: EntityRecord) -> str:
    if record.root.entity_type is not EntityType.JAVA_METHOD:
        raise _inconsistent("Java method signature requires a JAVA_METHOD Entity")
    fields = record.root.root_fields
    return (
        f"{_field_text(fields, 'declaring_type_qualified_name')}#"
        f"{_field_text(fields, 'method_name')}"
        f"({','.join(_field_text_sequence(fields, 'parameter_types'))})"
    )


def _java_feature_index(
    bundle: StructureSnapshotReadBundle,
) -> tuple[_JavaFeatureIndexEntry, ...]:
    """Rebuild the question-independent feature index from exact Bundle fields."""

    entities = _entities_by_root(bundle)
    methods = tuple(
        sorted(
            (
                item
                for item in entities.values()
                if item.root.entity_type is EntityType.JAVA_METHOD
            ),
            key=lambda item: (_java_method_signature(item), item.root_id.value),
        )
    )
    slots_by_method: dict[StableId, list[EntityRecord]] = {}
    atoms_by_method: dict[StableId, list[EntityRecord]] = {}
    atom_method: dict[StableId, StableId] = {}
    for entity in entities.values():
        if entity.root.entity_type is EntityType.JAVA_STATE_SLOT:
            declaring = StableId(
                _field_text(entity.root.root_fields, "declaring_entity_root_id")
            )
            if declaring in {item.root_id for item in methods}:
                slots_by_method.setdefault(declaring, []).append(entity)
        elif entity.root.entity_type is EntityType.JAVA_IMPLEMENTATION_ATOM:
            declaring = StableId(
                _field_text(entity.root.root_fields, "method_entity_root_id")
            )
            atoms_by_method.setdefault(declaring, []).append(entity)
            atom_method[entity.root_id] = declaring
    call_targets_by_method: dict[
        StableId, list[tuple[RelationFactRecord, EntityRecord]]
    ] = {}
    for relation in bundle.relation_facts:
        if relation.root.predicate is not RelationPredicate.CALL_SITE_TARGETS:
            continue
        owner = atom_method.get(relation.root.subject.entity_root_id)
        target = entities.get(relation.root.object.entity_root_id)
        if owner is None or target is None or target.root.entity_type is not EntityType.JAVA_METHOD:
            raise _inconsistent(
                "feature index CALL_SITE_TARGETS closure is incomplete"
            )
        call_targets_by_method.setdefault(owner, []).append((relation, target))

    result: list[_JavaFeatureIndexEntry] = []
    for method in methods:
        sources: set[_JavaFeatureTokenSource] = set()

        def add(
            raw: str,
            field_class: str,
            member_kind: str,
            root_id: StableId,
        ) -> None:
            for token in _feature_tokens(raw):
                sources.add(
                    _JavaFeatureTokenSource(
                        token=token,
                        field_class=field_class,
                        member_kind=member_kind,
                        root_id=root_id,
                    )
                )

        root_fields = method.root.root_fields
        state_fields = method.state.state_payload_fields
        declaring_type = _field_text(
            root_fields,
            "declaring_type_qualified_name",
        )
        add(declaring_type, "DECLARING_TYPE", "ENTITY", method.root_id)
        package = declaring_type.rsplit(".", 1)[0] if "." in declaring_type else declaring_type
        add(package, "PACKAGE", "ENTITY", method.root_id)
        add(
            _field_text(root_fields, "method_name"),
            "METHOD_NAME",
            "ENTITY",
            method.root_id,
        )
        for parameter_type in _field_text_sequence(root_fields, "parameter_types"):
            add(parameter_type, "PARAMETER_TYPE", "ENTITY", method.root_id)
        add(
            _field_text(state_fields, "return_type"),
            "RETURN_TYPE",
            "ENTITY",
            method.root_id,
        )
        for slot in slots_by_method.get(method.root_id, ()):
            add(
                _field_text(slot.root.root_fields, "canonical_identifier"),
                "STATE_SLOT_IDENTIFIER",
                "ENTITY",
                slot.root_id,
            )
            add(
                _field_text(slot.state.state_payload_fields, "declared_type"),
                "STATE_SLOT_TYPE",
                "ENTITY",
                slot.root_id,
            )
        for atom in atoms_by_method.get(method.root_id, ()):
            atom_state = atom.state.state_payload_fields
            add(
                _field_text(atom.root.root_fields, "atom_kind"),
                "ATOM_KIND",
                "ENTITY",
                atom.root_id,
            )
            add(
                _field_text(atom_state, "semantic_form"),
                "SEMANTIC_FORM",
                "ENTITY",
                atom.root_id,
            )
            add(
                _field_text(atom_state, "operator"),
                "OPERATOR",
                "ENTITY",
                atom.root_id,
            )
            add(
                _field_text(atom_state, "value_category"),
                "VALUE_CATEGORY",
                "ENTITY",
                atom.root_id,
            )
            raw_operands = atom_state["semantic_operands"]
            if not isinstance(raw_operands, tuple):
                raise _inconsistent("Java Atom semantic operands are malformed")
            for operand in raw_operands:
                if not isinstance(operand, Mapping):
                    raise _inconsistent("Java Atom semantic operand is malformed")
                if operand.get("kind") == "TYPE_REF" and isinstance(
                    operand.get("value"), str
                ):
                    add(
                        operand["value"],
                        "EXCEPTION_TYPE",
                        "ENTITY",
                        atom.root_id,
                    )
        for relation, target in call_targets_by_method.get(method.root_id, ()):
            target_fields = target.root.root_fields
            add(
                _field_text(target_fields, "declaring_type_qualified_name"),
                "CALLEE_TYPE",
                "RELATION_FACT",
                relation.root_id,
            )
            add(
                _field_text(target_fields, "method_name"),
                "CALLEE_METHOD",
                "RELATION_FACT",
                relation.root_id,
            )
        result.append(
            _JavaFeatureIndexEntry(
                method=method,
                signature=_java_method_signature(method),
                disposition=_field_text(state_fields, "method_disposition"),
                implementation_completeness=_field_text(
                    state_fields,
                    "implementation_semantics_completeness",
                ),
                sources=tuple(
                    sorted(
                        sources,
                        key=lambda item: (
                            item.token,
                            item.field_class,
                            item.member_kind,
                            item.root_id.value,
                        ),
                    )
                ),
            )
        )
    return tuple(result)


def _covered_entity_types(
    bundle: StructureSnapshotReadBundle,
) -> tuple[EntityType, ...]:
    return tuple(
        sorted(
            {
                entity_type
                for coverage in bundle.coverages
                for entity_type in coverage.root.covered_entity_types
            },
            key=lambda item: item.value,
        )
    )


def _covered_relation_predicates(
    bundle: StructureSnapshotReadBundle,
) -> tuple[RelationPredicate, ...]:
    return tuple(
        sorted(
            {
                predicate
                for coverage in bundle.coverages
                for predicate in coverage.root.covered_relation_predicates
            },
            key=lambda item: item.value,
        )
    )


def _entity_coordinates(record: EntityRecord) -> tuple[str | None, str | None]:
    if record.root.entity_type is not EntityType.MAVEN_MODULE:
        return None, None
    group_id = _field_text(record.root.root_fields, "effective_group_id")
    artifact_id = _field_text(record.root.root_fields, "artifact_id")
    version = _field_text(record.state.state_payload_fields, "effective_version")
    return f"{group_id}:{artifact_id}", f"{group_id}:{artifact_id}:{version}"


def _entity_value(record: EntityRecord) -> dict[str, object]:
    ga, gav = _entity_coordinates(record)
    return {
        "root_id": record.root_id.value,
        "state_id": record.state_id.value,
        "state_digest": record.state_digest.value,
        "entity_type": record.root.entity_type.value,
        "root_fields": record.root.root_fields,
        "state_fields": record.state.state_payload_fields,
        "canonical_ga": ga,
        "canonical_gav": gav,
    }


def _relation_value(record: RelationFactRecord) -> dict[str, object]:
    return {
        "root_id": record.root_id.value,
        "state_id": record.state_id.value,
        "state_digest": record.state_digest.value,
        "subject_entity_root_id": record.root.subject.entity_root_id.value,
        "subject_entity_state_id": record.state.subject_entity_state_id.value,
        "predicate": record.root.predicate.value,
        "object_entity_root_id": record.root.object.entity_root_id.value,
        "object_entity_state_id": record.state.object_entity_state_id.value,
        "observation_modality": record.root.observation_modality.value,
        "predicate_state_fields": record.state.predicate_state_payload_fields,
    }


def _literal_value(record: LiteralFactRecord) -> dict[str, object]:
    return {
        "root_id": record.root_id.value,
        "state_id": record.state_id.value,
        "state_digest": record.state_digest.value,
        "subject_entity_root_id": record.root.subject.entity_root_id.value,
        "subject_entity_state_id": record.state.subject_entity_state_id.value,
        "predicate": record.root.predicate,
        "literal_object": record.root.object.canonical_value(),
        "observation_modality": record.root.observation_modality,
    }


def _mention_hits(record: EntityRecord, mention: str) -> tuple[str, ...]:
    ga, gav = _entity_coordinates(record)
    public: dict[str, object] = {
        "entity_root_id": record.root_id.value,
        "canonical_ga": ga,
        "canonical_gav": gav,
    }
    try:
        root_fields = _PUBLIC_ENTITY_ROOT_FIELDS[record.root.entity_type]
        state_fields = _PUBLIC_ENTITY_STATE_FIELDS[record.root.entity_type]
    except KeyError as exc:  # pragma: no cover - fail closed for future types
        raise _inconsistent(
            "View candidate public-field policy is missing an Entity type"
        ) from exc
    for key in root_fields:
        if key == "parameter_types":
            public[f"root.{key}"] = ",".join(
                _field_text_sequence(record.root.root_fields, key)
            )
        else:
            public[f"root.{key}"] = _field_text(record.root.root_fields, key)
    for key in state_fields:
        public[f"state.{key}"] = _field_text(
            record.state.state_payload_fields, key
        )
    if record.root.entity_type is EntityType.JAVA_METHOD:
        declaring_type = _field_text(
            record.root.root_fields, "declaring_type_qualified_name"
        )
        method_name = _field_text(record.root.root_fields, "method_name")
        parameters = ",".join(
            _field_text_sequence(record.root.root_fields, "parameter_types")
        )
        public["java_method_signature"] = (
            f"{declaring_type}#{method_name}({parameters})"
        )
        public["java_method_simple_signature"] = f"{method_name}({parameters})"
    return tuple(
        sorted(
            key
            for key, value in public.items()
            if isinstance(value, str) and _mention(value) == mention
        )
    )


def _evidence_for(
    bundle: StructureSnapshotReadBundle,
    references: Sequence[StableId],
) -> tuple[StructureEvidenceMetadata, ...]:
    by_id = {item.evidence_id: item for item in bundle.evidence_metadata}
    values: list[StructureEvidenceMetadata] = []
    for reference in references:
        evidence = by_id.get(reference)
        if evidence is None:
            raise _inconsistent("View Support Evidence is absent from exact bundle")
        values.append(evidence)
    return tuple(sorted(values, key=lambda item: item.evidence_id.value))


def _evidence_value(value: StructureEvidenceMetadata) -> dict[str, object]:
    return {
        "evidence_id": value.evidence_id.value,
        "artifact_id": value.artifact_id.value,
        "source_context_id": value.source_context_id.value,
        "byte_start": value.byte_start,
        "byte_end": value.byte_end,
        "locator": value.locator,
        "excerpt_digest": value.excerpt_digest.value,
        "artifact_content_digest": value.artifact_content_digest.value,
        "digest": value.digest.value,
    }


def _unique_support(
    values: Sequence[StructureViewSupport],
) -> tuple[StructureViewSupport, ...]:
    by_key: dict[tuple[StableId, str, StableId], StructureViewSupport] = {}
    for value in values:
        key = (value.snapshot_id, value.member_kind, value.root_id)
        previous = by_key.get(key)
        if previous is not None and previous != value:
            raise _inconsistent("View Support key resolves to different exact States")
        by_key[key] = value
    return tuple(
        sorted(
            by_key.values(),
            key=lambda item: (
                item.snapshot_id.value,
                item.member_kind,
                item.root_id.value,
            ),
        )
    )


def _typed_stable_id(value: object, label: str) -> StableId:
    if not isinstance(value, StableId):
        raise _invalid(
            "VIEW_STABLE_ID_REQUIRED",
            f"{label} must be a typed StableId",
        )
    return value


def _public_result_entity_refs(
    result: StructureViewResult,
) -> frozenset[tuple[StableId, StableId]]:
    """Return Entity Root/State pairs both exposed and support-authorized."""

    exposed: set[tuple[StableId, StableId]] = set()

    def visit(value: object) -> None:
        if isinstance(value, Mapping):
            for root_key, state_key in (
                ("root_id", "state_id"),
                ("entity_root_id", "entity_state_id"),
            ):
                root_value = value.get(root_key)
                state_value = value.get(state_key)
                if isinstance(root_value, str) and isinstance(state_value, str):
                    try:
                        exposed.add((StableId(root_value), StableId(state_value)))
                    except (TypeError, ValueError):
                        pass
            for nested in value.values():
                visit(nested)
        elif isinstance(value, (tuple, list)):
            for nested in value:
                visit(nested)

    visit(result.payload)
    supported = {
        (item.root_id, item.state_id) for item in result.support_map
    }
    return frozenset(exposed & supported)


def _caller_argument_from_result_field(
    service: StructureViewService,
    result: StructureViewResult,
    key: str,
) -> StructureEntityArgument:
    value = result.payload.get(key)
    if not isinstance(value, Mapping):
        raise _invalid(
            "VIEW_RESULT_ENTITY_FIELD_INVALID",
            f"sealed View Result field {key} is not an Entity",
        )
    root_value = value.get("root_id", value.get("entity_root_id"))
    state_value = value.get("state_id", value.get("entity_state_id"))
    if not isinstance(root_value, str) or not isinstance(state_value, str):
        raise _invalid(
            "VIEW_RESULT_ENTITY_FIELD_INVALID",
            f"sealed View Result field {key} has no exact Root/State pair",
        )
    return StructureEntityArgument.caller_exact_ref(
        service=service,
        snapshot_id=result.snapshot_ids[0],
        entity_root_id=StableId(root_value),
        entity_state_id=StableId(state_value),
    )


def _replay_structure_view_result(
    service: StructureViewService,
    result: StructureViewResult,
) -> StructureViewResult:
    """Replay a sealed Result before it may authorize a later Entity Ref."""

    payload = result.payload
    operation = result.operation
    if operation is StructureViewOperation.ENTITY_CANDIDATES:
        exact_root = payload.get("exact_root_id")
        return service.entity_candidates(
            snapshot_id=result.snapshot_ids[0],
            mention=_mapping_text(payload, "mention_original"),
            entity_type=payload.get("entity_type"),
            exact_root_id=(
                StableId(exact_root) if isinstance(exact_root, str) else None
            ),
            canonical_ga=(
                payload.get("canonical_ga")
                if isinstance(payload.get("canonical_ga"), str)
                else None
            ),
            canonical_gav=(
                payload.get("canonical_gav")
                if isinstance(payload.get("canonical_gav"), str)
                else None
            ),
            max_candidates=_mapping_int(payload, "max_candidates"),
        )
    if operation is StructureViewOperation.IMPLEMENTATION_CANDIDATES:
        return service.implementation_candidates(
            snapshot_id=result.snapshot_ids[0],
            search_terms=_mapping_string_sequence(
                payload, "search_terms_original"
            ),
            limit=_mapping_int(payload, "limit"),
        )
    if operation is StructureViewOperation.METHOD_IMPLEMENTATION:
        return service.method_implementation(
            method=_caller_argument_from_result_field(
                service, result, "method"
            )
        )
    if operation is StructureViewOperation.CHILD_MODULE_INVENTORY:
        return service.child_module_inventory(
            system=_caller_argument_from_result_field(
                service, result, "system"
            )
        )
    if operation is StructureViewOperation.DECLARED_METHOD_INVENTORY:
        return service.declared_method_inventory(
            java_type=_caller_argument_from_result_field(
                service, result, "java_type"
            )
        )
    if operation is StructureViewOperation.DIRECT_NEIGHBORHOOD:
        return service.direct_neighborhood(
            entity=_caller_argument_from_result_field(
                service, result, "entity"
            ),
            direction=_mapping_text(payload, "direction"),
            predicate=payload.get("predicate"),
        )
    if operation is StructureViewOperation.PATH_EXISTS:
        return service.path_exists(
            source=_caller_argument_from_result_field(
                service, result, "source"
            ),
            target=_caller_argument_from_result_field(
                service, result, "target"
            ),
            predicate=_mapping_text(payload, "predicate"),
            max_depth=_mapping_int(payload, "max_depth"),
            max_expansions=_mapping_int(payload, "max_expansions"),
        )
    if operation is StructureViewOperation.ALL_SIMPLE_PATHS:
        return service.all_simple_paths(
            source=_caller_argument_from_result_field(
                service, result, "source"
            ),
            target=_caller_argument_from_result_field(
                service, result, "target"
            ),
            predicate=_mapping_text(payload, "predicate"),
            max_depth=_mapping_int(payload, "max_depth"),
            max_paths=_mapping_int(payload, "max_paths"),
            max_expansions=_mapping_int(payload, "max_expansions"),
        )
    if operation is StructureViewOperation.ORDERED_SNAPSHOT_DIFF:
        return service.ordered_snapshot_diff(
            base_snapshot_id=StableId(
                _mapping_text(payload, "base_snapshot_id")
            ),
            target_snapshot_id=StableId(
                _mapping_text(payload, "target_snapshot_id")
            ),
        )
    raise _invalid(
        "VIEW_RESULT_REPLAY_UNSUPPORTED",
        "sealed View Result operation cannot authorize a later Entity Ref",
    )


def _field_text(values: CanonicalFields, key: str) -> str:
    try:
        value = values[key]
    except KeyError as exc:
        raise _inconsistent(f"typed Structure record lacks {key}") from exc
    if not isinstance(value, str):
        raise _inconsistent(f"typed Structure field {key} is not text")
    return value


def _field_text_sequence(
    values: CanonicalFields, key: str
) -> tuple[str, ...]:
    try:
        value = values[key]
    except KeyError as exc:
        raise _inconsistent(f"typed Structure record lacks {key}") from exc
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise _inconsistent(f"typed Structure field {key} is not a sequence")
    result = tuple(value)
    if not all(isinstance(item, str) for item in result):
        raise _inconsistent(f"typed Structure field {key} contains non-text")
    return result


def _mapping_text(values: Mapping[str, object], key: str) -> str:
    try:
        value = values[key]
    except KeyError as exc:
        raise _invalid(
            "VIEW_RESULT_FIELD_MISSING",
            f"sealed View Result lacks {key}",
        ) from exc
    if not isinstance(value, str):
        raise _invalid(
            "VIEW_RESULT_FIELD_INVALID",
            f"sealed View Result field {key} is not text",
        )
    return value


def _mapping_int(values: Mapping[str, object], key: str) -> int:
    try:
        value = values[key]
    except KeyError as exc:
        raise _invalid(
            "VIEW_RESULT_FIELD_MISSING",
            f"sealed View Result lacks {key}",
        ) from exc
    if type(value) is not int:
        raise _invalid(
            "VIEW_RESULT_FIELD_INVALID",
            f"sealed View Result field {key} is not an integer",
        )
    return value


def _mapping_string_sequence(
    values: Mapping[str, object], key: str
) -> tuple[str, ...]:
    try:
        raw = values[key]
    except KeyError as exc:
        raise _inconsistent(f"path value lacks {key}") from exc
    if not isinstance(raw, (tuple, list)) or any(
        not isinstance(item, str) for item in raw
    ):
        raise _inconsistent(f"path value {key} is malformed")
    return tuple(raw)


def _mention(value: object) -> str:
    if not isinstance(value, str):
        raise _invalid(
            "VIEW_MENTION_TEXT_REQUIRED",
            "entity mention must be text",
        )
    normalized = unicodedata.normalize("NFC", value).strip()
    if not normalized:
        raise _invalid(
            "VIEW_MENTION_EMPTY",
            "entity mention must be non-empty",
        )
    return normalized


def _coordinate(value: str | None, parts: int, label: str) -> str | None:
    if value is None:
        return None
    normalized = _mention(value)
    tokens = normalized.split(":")
    if len(tokens) != parts or any(not token or token != token.strip() for token in tokens):
        raise _invalid(
            "VIEW_COORDINATE_INVALID",
            f"{label} must contain exactly {parts} canonical non-empty parts",
        )
    return ":".join(unicodedata.normalize("NFC", token) for token in tokens)


def _budget(value: object, label: str) -> int:
    if type(value) is not int or value < 1 or value > 100_000:
        raise _invalid(
            "VIEW_BUDGET_INVALID",
            f"{label} must be an integer from 1 through 100000",
        )
    return value


def _text(value: object, label: str) -> str:
    if not isinstance(value, str):
        raise _invalid("VIEW_TEXT_REQUIRED", f"{label} must be text")
    normalized = unicodedata.normalize("NFC", value).strip()
    if not normalized:
        raise _invalid("VIEW_TEXT_EMPTY", f"{label} must be non-empty")
    return normalized


def _enum(enum_type, value: object, label: str):
    try:
        return value if isinstance(value, enum_type) else enum_type(value)
    except (TypeError, ValueError) as exc:
        raise _invalid("VIEW_ENUM_INVALID", f"{label} is invalid") from exc


def _optional_enum(enum_type, value: object | None, label: str):
    return None if value is None else _enum(enum_type, value, label)


def _stable(kind: str, digest: Digest) -> StableId:
    return StableId(f"{kind}_{digest.value.removeprefix('sha256:')[-32:]}")


def _invalid(reason_code: str, message: str) -> DomainError:
    return DomainError(
        ErrorCode.INVALID_ARGUMENT,
        message,
        {"reason_code": reason_code},
    )


def _inconsistent(message: str) -> DomainError:
    return DomainError(ErrorCode.AUTHORITY_RECORD_INCONSISTENT, message)
