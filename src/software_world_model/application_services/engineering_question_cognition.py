"""Bundle-only World Model cognition projection for Engineering QA.

The projector mounts one verified no-payload Structure Snapshot Bundle through
an exact Structure View read authority.  It never reads a repository, chooses
facts from question text, or obtains a Source/Provider handle.  Projection is
deterministic and any byte-bound truncation is disclosed as an explicit
unknown boundary.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import Enum
import json
import re

from software_world_model.application_services.engineering_question_answering import (
    CognitionDimension,
    CognitionItem,
    EngineeringQuestionRequest,
    WorldModelCognitionContext,
)
from software_world_model.application_services.structure_read_bundle import (
    StructureSnapshotReadBundle,
)
from software_world_model.application_services.structure_view import (
    StructureViewService,
)
from software_world_model.cross_cutting import (
    Digest,
    DomainError,
    ErrorCode,
    StableId,
    canonical_json_bytes,
    digest_of,
)
from software_world_model.knowledge_engine.structure import (
    EntityRecord,
    EntityType,
    JAVA_SOURCE_SEMANTICS_PROFILE_REF,
    MAVEN_STRUCTURE_PROFILE_REF,
    RelationPredicate,
)


ENGINEERING_QA_STRUCTURE_COGNITION_AUTHORITY = (
    "ENGINEERING_QA_STRUCTURE_COGNITION_AUTHORITY@1"
)
ENGINEERING_COGNITION_CAPABILITY_MANIFEST = (
    "ENGINEERING_COGNITION_CAPABILITY_MANIFEST@1"
)
ENGINEERING_COGNITION_NEED_CLASSIFIER = (
    "ENGINEERING_COGNITION_NEED_CLASSIFIER@1"
)

_BEHAVIOR_PREDICATES = frozenset(
    {
        RelationPredicate.CALLS,
        RelationPredicate.HAS_IMPLEMENTATION_ATOM,
        RelationPredicate.CONTROLS,
        RelationPredicate.NEXT_IN_SOURCE,
        RelationPredicate.CALL_SITE_TARGETS,
        RelationPredicate.READS_STATE,
        RelationPredicate.WRITES_STATE,
        RelationPredicate.HANDLES_THROW,
    }
)


@dataclass(frozen=True, slots=True)
class StructureBundleWorldModelCognitionProjector:
    """Project one exact persistent Structure Snapshot into typed cognition."""

    view: StructureViewService
    snapshot_bundle: StructureSnapshotReadBundle
    maximum_items: int = 4_096
    read_authority_digest: Digest = field(init=False)
    source_revision: str = field(init=False)
    binding_id: StableId = field(init=False)

    def __post_init__(self) -> None:
        if (
            isinstance(self.maximum_items, bool)
            or not isinstance(self.maximum_items, int)
            or not 1 <= self.maximum_items <= 4_096
        ):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "Structure cognition item limit must be from 1 through 4096",
            )
        self._require_exact_mount()
        revisions = self._source_revisions()
        if len(revisions) != 1:
            raise DomainError(
                ErrorCode.SOURCE_REVISION_INCONSISTENT,
                "Structure cognition Snapshot must bind one exact source revision",
            )
        bindings = {
            coverage.root.source_binding_id
            for coverage in self.snapshot_bundle.coverages
        }
        if len(bindings) != 1:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Structure cognition Snapshot must bind one exact Source Binding",
            )
        authority = digest_of(
            [
                ENGINEERING_QA_STRUCTURE_COGNITION_AUTHORITY,
                self.view.session_id.value,
                self.view.read_session.digest.value,
                self.view.read_set_digest.value,
                self.view.ordered_bundle_digest.value,
                self.snapshot_bundle.snapshot_id.value,
                self.snapshot_bundle.digest.value,
            ]
        )
        object.__setattr__(self, "read_authority_digest", authority)
        object.__setattr__(self, "source_revision", next(iter(revisions)))
        object.__setattr__(self, "binding_id", next(iter(bindings)))

    def project(
        self,
        *,
        request: EngineeringQuestionRequest,
    ) -> WorldModelCognitionContext:
        self._require_exact_mount()
        if (
            request.binding_id != self.binding_id
            or request.world_model_read_authority_digest
            != self.read_authority_digest
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Structure cognition authority does not bind the Engineering Question Request",
            )
        all_items = self._project_items()
        visible_items = all_items[: self.maximum_items]
        coverage = self._coverage_summary(total_items=len(all_items))
        base_unknowns = self._profile_unknowns()

        def build(item_count: int) -> WorldModelCognitionContext:
            omitted = len(all_items) - item_count
            unknowns = base_unknowns
            if omitted:
                unknowns = (
                    *unknowns,
                    "World Model cognition projection retained "
                    f"{item_count} of {len(all_items)} deterministic items; "
                    "omitted records remain unknown to this question context.",
                )
            return WorldModelCognitionContext.create(
                request=request,
                scope_ref=self.snapshot_bundle.scope_id.value,
                context_ref=self.view.session_id.value,
                schema_ref=self.snapshot_bundle.snapshot.schema_ref,
                snapshot_ids=(self.snapshot_bundle.snapshot_id.value,),
                read_authority_digest=self.read_authority_digest,
                source_revision=self.source_revision,
                items=visible_items[:item_count],
                coverage=coverage,
                unknowns=unknowns,
            )

        low = 0
        high = len(visible_items)
        selected: WorldModelCognitionContext | None = None
        while low <= high:
            middle = (low + high) // 2
            candidate = build(middle)
            if (
                len(canonical_json_bytes(candidate.model_view()))
                <= request.limits.maximum_world_model_bytes
            ):
                selected = candidate
                low = middle + 1
            else:
                high = middle - 1
        if selected is None:
            raise DomainError(
                ErrorCode.BUDGET_EXHAUSTED,
                "World Model cognition authority metadata exceeds its byte fuse",
            )
        return selected

    def _require_exact_mount(self) -> None:
        if not isinstance(self.view, StructureViewService) or not isinstance(
            self.snapshot_bundle, StructureSnapshotReadBundle
        ):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "Structure cognition requires a typed View and Snapshot Bundle",
            )
        self.view.read_session.require_valid()
        self.snapshot_bundle.require_valid()
        try:
            ordinal = self.view.snapshot_ids.index(self.snapshot_bundle.snapshot_id)
        except ValueError as exc:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Structure cognition Snapshot is outside the mounted read authority",
            ) from exc
        if self.view.snapshot_bundle_digests[ordinal] != self.snapshot_bundle.digest:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Structure cognition Snapshot Bundle differs from the mounted read authority",
            )

    def _source_revisions(self) -> set[str]:
        revisions = {
            item.state.source_revision.casefold()
            for item in (
                *self.snapshot_bundle.coverages,
                *self.snapshot_bundle.relation_facts,
                *self.snapshot_bundle.literal_facts,
            )
        }
        revisions.update(
            str(item.state.state_payload_fields["source_revision"]).casefold()
            for item in self.snapshot_bundle.entities
        )
        return revisions

    def _project_items(self) -> tuple[CognitionItem, ...]:
        bundle = self.snapshot_bundle
        entities_by_id = {record.root_id: record for record in bundle.entities}
        coverage_items = tuple(
            CognitionItem.create(
                dimension=CognitionDimension.COVERAGE,
                statement=_statement(
                    "STRUCTURE_COVERAGE",
                    {
                        "profile_ref": record.root.profile_ref,
                        "covered_entity_types": tuple(
                            item.value for item in record.root.covered_entity_types
                        ),
                        "covered_relation_predicates": tuple(
                            item.value
                            for item in record.root.covered_relation_predicates
                        ),
                        "complete_member_count": len(
                            record.state.complete_member_manifest.members
                        ),
                    },
                ),
                modality="STRUCTURE_COMPLETE_MEMBER_MANIFEST",
                context_ref=bundle.snapshot_id.value,
                source_revision=self.source_revision,
                locator=(
                    f"world-model:snapshot:{bundle.snapshot_id.value}:"
                    f"coverage:{record.root_id.value}"
                ),
                support_references=tuple(
                    item.value for item in record.state.evidence_references
                ),
                coverage="Exact complete-member manifest from the verified Snapshot Bundle.",
            )
            for record in bundle.coverages
        )
        entity_items = tuple(
            CognitionItem.create(
                dimension=(
                    CognitionDimension.STATE
                    if record.root.entity_type is EntityType.JAVA_STATE_SLOT
                    else CognitionDimension.BEHAVIOR
                    if record.root.entity_type
                    is EntityType.JAVA_IMPLEMENTATION_ATOM
                    else CognitionDimension.ENTITY
                ),
                statement=_statement(
                    "STRUCTURE_ENTITY",
                    {
                        "entity_type": record.root.entity_type.value,
                        "root_fields": dict(record.root.root_fields),
                        "state_fields": dict(record.state.state_payload_fields),
                    },
                ),
                modality="STRUCTURE_ENTITY_STATE",
                context_ref=bundle.snapshot_id.value,
                source_revision=self.source_revision,
                locator=(
                    f"world-model:snapshot:{bundle.snapshot_id.value}:"
                    f"entity:{record.root_id.value}"
                ),
                support_references=tuple(
                    item.value for item in record.state.evidence_references
                ),
                coverage="Typed Entity Root and exact State from the verified Snapshot Bundle.",
            )
            for record in bundle.entities
            if record.state.evidence_references
        )
        relation_items = tuple(
            CognitionItem.create(
                dimension=(
                    CognitionDimension.BEHAVIOR
                    if record.root.predicate in _BEHAVIOR_PREDICATES
                    else CognitionDimension.RELATION
                ),
                statement=_statement(
                    "STRUCTURE_RELATION",
                    {
                        "subject_entity_root_id": (
                            record.root.subject.entity_root_id.value
                        ),
                        "predicate": record.root.predicate.value,
                        "object_entity_root_id": (
                            record.root.object.entity_root_id.value
                        ),
                        "subject_identity": _entity_identity(
                            entities_by_id.get(
                                record.root.subject.entity_root_id
                            ),
                            entities_by_id=entities_by_id,
                        ),
                        "object_identity": _entity_identity(
                            entities_by_id.get(
                                record.root.object.entity_root_id
                            ),
                            entities_by_id=entities_by_id,
                        ),
                        "observation_modality": (
                            record.root.observation_modality.value
                        ),
                        "state_fields": dict(
                            record.state.predicate_state_payload_fields
                        ),
                    },
                ),
                modality=(
                    "STRUCTURE_BEHAVIOR_RELATION"
                    if record.root.predicate in _BEHAVIOR_PREDICATES
                    else "STRUCTURE_RELATION_FACT"
                ),
                context_ref=bundle.snapshot_id.value,
                source_revision=self.source_revision,
                locator=(
                    f"world-model:snapshot:{bundle.snapshot_id.value}:"
                    f"relation:{record.root_id.value}"
                ),
                support_references=tuple(
                    item.value for item in record.state.evidence_references
                ),
                coverage="Typed Relation Root and exact State from the verified Snapshot Bundle.",
            )
            for record in bundle.relation_facts
            if record.state.evidence_references
        )
        literal_items = tuple(
            CognitionItem.create(
                dimension=CognitionDimension.STATE,
                statement=_statement(
                    "STRUCTURE_LITERAL",
                    {
                        "subject_entity_root_id": (
                            record.root.subject.entity_root_id.value
                        ),
                        "predicate": record.root.predicate,
                        "literal_object": record.root.object.canonical_value(),
                        "observation_modality": record.root.observation_modality,
                    },
                ),
                modality="STRUCTURE_LITERAL_FACT",
                context_ref=bundle.snapshot_id.value,
                source_revision=self.source_revision,
                locator=(
                    f"world-model:snapshot:{bundle.snapshot_id.value}:"
                    f"literal:{record.root_id.value}"
                ),
                support_references=tuple(
                    item.value for item in record.state.evidence_references
                ),
                coverage="Typed Literal Root and exact State from the verified Snapshot Bundle.",
            )
            for record in bundle.literal_facts
            if record.state.evidence_references
        )
        evidence_items = tuple(
            CognitionItem.create(
                dimension=CognitionDimension.EVIDENCE,
                statement=_statement(
                    "STRUCTURE_EVIDENCE_METADATA",
                    {
                        "evidence_id": evidence.evidence_id.value,
                        "artifact_id": evidence.artifact_id.value,
                        "source_context_id": evidence.source_context_id.value,
                        "byte_start": evidence.byte_start,
                        "byte_end": evidence.byte_end,
                        "excerpt_digest": evidence.excerpt_digest.value,
                        "artifact_content_digest": (
                            evidence.artifact_content_digest.value
                        ),
                    },
                ),
                modality="STRUCTURE_EVIDENCE_METADATA",
                context_ref=bundle.snapshot_id.value,
                source_revision=self.source_revision,
                locator=evidence.locator,
                support_references=(evidence.evidence_id.value,),
                coverage="No-payload Evidence identity and locator metadata only.",
            )
            for evidence in bundle.evidence_metadata
        )
        groups = (
            coverage_items,
            entity_items,
            relation_items,
            literal_items,
            evidence_items,
        )
        interleaved: list[CognitionItem] = []
        for ordinal in range(max((len(group) for group in groups), default=0)):
            interleaved.extend(
                group[ordinal] for group in groups if ordinal < len(group)
            )
        return tuple(interleaved)

    def _coverage_summary(self, *, total_items: int) -> tuple[str, ...]:
        bundle = self.snapshot_bundle
        return (
            f"Exact Snapshot {bundle.snapshot_id.value} and Bundle "
            f"{bundle.digest.value} are mounted through read Session "
            f"{self.view.session_id.value}.",
            "Projection is question-independent and contains typed Entity, Relation, "
            "Literal, Evidence metadata, and complete Coverage records only.",
            f"Deterministic projection candidate count is {total_items}; raw Source payload "
            "is not present in the World Model Bundle.",
        )

    def _profile_unknowns(self) -> tuple[str, ...]:
        bundle = self.snapshot_bundle
        unknowns: list[str] = [
            "The mounted Structure profile has no dedicated universal constraint fact "
            "class; constraints not represented by its typed records remain unknown."
        ]
        if not bundle.relation_facts:
            unknowns.append(
                "The Snapshot contains no formal relation records within this profile; "
                "this is not proof that the repository has no relationships."
            )
        if not any(
            record.root.predicate in _BEHAVIOR_PREDICATES
            for record in bundle.relation_facts
        ):
            unknowns.append(
                "The Snapshot contains no formal behavior relation records within this "
                "profile; query-time Source investigation may still be required."
            )
        if not bundle.literal_facts:
            unknowns.append(
                "The Snapshot contains no formal literal-state records within this profile."
            )
        return tuple(unknowns)


class CognitionMaterialNeedKind(str, Enum):
    STRUCTURE = "STRUCTURE"
    IMPLEMENTATION_BEHAVIOR = "IMPLEMENTATION_BEHAVIOR"
    RESPONSIBILITY_FAILURE_BOUNDARY = "RESPONSIBILITY_FAILURE_BOUNDARY"
    GENERAL_ENGINEERING = "GENERAL_ENGINEERING"


@dataclass(frozen=True, slots=True)
class CognitionMaterialNeed:
    kind: CognitionMaterialNeedKind
    required_dimensions: tuple[CognitionDimension, ...]
    required_query_capabilities: tuple[str, ...]
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        kind: CognitionMaterialNeedKind,
        required_dimensions: Sequence[CognitionDimension],
        required_query_capabilities: Sequence[str] = (),
    ) -> "CognitionMaterialNeed":
        dimensions = tuple(
            sorted(set(required_dimensions), key=lambda item: item.value)
        )
        if not dimensions:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "Cognition material Need must require at least one dimension",
            )
        capabilities = tuple(sorted(set(required_query_capabilities)))
        if any(
            not isinstance(item, str) or not item or item != item.strip()
            for item in capabilities
        ):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "Cognition material Need query capabilities are invalid",
            )
        core = {
            "schema": "ENGINEERING_COGNITION_MATERIAL_NEED@1",
            "kind": kind.value,
            "required_dimensions": tuple(item.value for item in dimensions),
            "required_query_capabilities": capabilities,
        }
        return cls(
            kind=kind,
            required_dimensions=dimensions,
            required_query_capabilities=capabilities,
            digest=digest_of(core),
        )

    def model_view(self) -> dict[str, object]:
        return {
            "kind": self.kind.value,
            "required_dimensions": [
                item.value for item in self.required_dimensions
            ],
            "required_query_capabilities": list(
                self.required_query_capabilities
            ),
            "digest": self.digest.value,
        }


@dataclass(frozen=True, slots=True)
class CognitionProfileCapability:
    ordinal: int
    profile_ref: str
    schema_ref: str
    source_binding_id: StableId
    source_revision: str
    snapshot_id: StableId
    snapshot_bundle_digest: Digest
    read_session_id: StableId
    read_session_digest: Digest
    read_set_digest: Digest
    ordered_bundle_digest: Digest
    read_authority_digest: Digest
    coverage_bindings: tuple[tuple[str, str, str], ...]
    dimensions: tuple[CognitionDimension, ...]
    query_capabilities: tuple[str, ...]
    explicit_gaps: tuple[str, ...]
    digest: Digest

    @classmethod
    def from_projector(
        cls,
        *,
        ordinal: int,
        projector: StructureBundleWorldModelCognitionProjector,
    ) -> "CognitionProfileCapability":
        projector._require_exact_mount()
        bundle = projector.snapshot_bundle
        profiles = {item.root.profile_ref for item in bundle.coverages}
        schemas = {item.root.schema_ref for item in bundle.coverages}
        if len(profiles) != 1 or len(schemas) != 1:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Cognition Profile authority must contain one exact Profile and Schema",
            )
        profile_ref = next(iter(profiles))
        dimensions: set[CognitionDimension] = {
            CognitionDimension.COVERAGE,
        }
        if bundle.entities:
            dimensions.add(CognitionDimension.ENTITY)
        if any(
            item.root.entity_type is EntityType.JAVA_IMPLEMENTATION_ATOM
            for item in bundle.entities
        ) or any(
            item.root.predicate in _BEHAVIOR_PREDICATES
            for item in bundle.relation_facts
        ):
            dimensions.add(CognitionDimension.BEHAVIOR)
        if any(
            item.root.entity_type is EntityType.JAVA_STATE_SLOT
            for item in bundle.entities
        ) or bundle.literal_facts:
            dimensions.add(CognitionDimension.STATE)
        if any(
            item.root.predicate not in _BEHAVIOR_PREDICATES
            for item in bundle.relation_facts
        ):
            dimensions.add(CognitionDimension.RELATION)
        if bundle.evidence_metadata:
            dimensions.add(CognitionDimension.EVIDENCE)

        query_capabilities = [
            "cognition_projection@1",
            "entity_candidates@1",
            "direct_neighborhood@1",
        ]
        if profile_ref == MAVEN_STRUCTURE_PROFILE_REF:
            query_capabilities.extend(
                ("module_membership@1", "direct_dependency@1", "simple_paths@1")
            )
        if profile_ref == JAVA_SOURCE_SEMANTICS_PROFILE_REF:
            query_capabilities.extend(
                (
                    "implementation_candidates@1",
                    "method_implementation@1",
                    "method_implementations@1",
                )
            )

        unsupported = 0
        failed = 0
        incomplete_methods = 0
        for record in bundle.entities:
            fields = record.state.state_payload_fields
            if record.root.entity_type in {
                EntityType.JAVA_SOURCE_FILE,
                EntityType.JAVA_TYPE,
                EntityType.JAVA_METHOD,
            }:
                disposition = fields.get(
                    "method_disposition", fields.get("disposition")
                )
                if disposition == "UNSUPPORTED_EXCLUDED":
                    unsupported += 1
                elif disposition == "FAILED":
                    failed += 1
            if record.root.entity_type is EntityType.JAVA_METHOD and (
                fields.get("implementation_semantics_completeness")
                not in {None, "COMPLETE"}
            ):
                incomplete_methods += 1
        gaps = ["UNIVERSAL_CONSTRAINT_DIMENSION_UNAVAILABLE"]
        if CognitionDimension.BEHAVIOR not in dimensions:
            gaps.append("BEHAVIOR_DIMENSION_UNAVAILABLE")
        if CognitionDimension.STATE not in dimensions:
            gaps.append("STATE_DIMENSION_UNAVAILABLE")
        if unsupported:
            gaps.append(f"UNSUPPORTED_EXCLUDED_UNITS:{unsupported}")
        if failed:
            gaps.append(f"FAILED_UNITS:{failed}")
        if incomplete_methods:
            gaps.append(f"INCOMPLETE_IMPLEMENTATION_METHODS:{incomplete_methods}")

        coverage_bindings = tuple(
            sorted(
                (
                    item.root_id.value,
                    item.state_id.value,
                    item.state.state_digest.value,
                )
                for item in bundle.coverages
            )
        )
        normalized_dimensions = tuple(
            sorted(dimensions, key=lambda item: item.value)
        )
        normalized_capabilities = tuple(sorted(set(query_capabilities)))
        normalized_gaps = tuple(sorted(set(gaps)))
        core = {
            "schema": "ENGINEERING_COGNITION_PROFILE_CAPABILITY@1",
            "ordinal": ordinal,
            "profile_ref": profile_ref,
            "schema_ref": next(iter(schemas)),
            "source_binding_id": projector.binding_id.value,
            "source_revision": projector.source_revision,
            "snapshot_id": bundle.snapshot_id.value,
            "snapshot_bundle_digest": bundle.digest.value,
            "read_session_id": projector.view.session_id.value,
            "read_session_digest": projector.view.read_session.digest.value,
            "read_set_digest": projector.view.read_set_digest.value,
            "ordered_bundle_digest": projector.view.ordered_bundle_digest.value,
            "read_authority_digest": projector.read_authority_digest.value,
            "coverage_bindings": coverage_bindings,
            "dimensions": tuple(item.value for item in normalized_dimensions),
            "query_capabilities": normalized_capabilities,
            "explicit_gaps": normalized_gaps,
        }
        return cls(
            ordinal=ordinal,
            profile_ref=profile_ref,
            schema_ref=next(iter(schemas)),
            source_binding_id=projector.binding_id,
            source_revision=projector.source_revision,
            snapshot_id=bundle.snapshot_id,
            snapshot_bundle_digest=bundle.digest,
            read_session_id=projector.view.session_id,
            read_session_digest=projector.view.read_session.digest,
            read_set_digest=projector.view.read_set_digest,
            ordered_bundle_digest=projector.view.ordered_bundle_digest,
            read_authority_digest=projector.read_authority_digest,
            coverage_bindings=coverage_bindings,
            dimensions=normalized_dimensions,
            query_capabilities=normalized_capabilities,
            explicit_gaps=normalized_gaps,
            digest=digest_of(core),
        )

    def model_view(self) -> dict[str, object]:
        return {
            "ordinal": self.ordinal,
            "profile_ref": self.profile_ref,
            "schema_ref": self.schema_ref,
            "source_binding_id": self.source_binding_id.value,
            "source_revision": self.source_revision,
            "snapshot_id": self.snapshot_id.value,
            "snapshot_bundle_digest": self.snapshot_bundle_digest.value,
            "read_session_id": self.read_session_id.value,
            "read_session_digest": self.read_session_digest.value,
            "read_set_digest": self.read_set_digest.value,
            "ordered_bundle_digest": self.ordered_bundle_digest.value,
            "read_authority_digest": self.read_authority_digest.value,
            "coverage_bindings": [list(item) for item in self.coverage_bindings],
            "dimensions": [item.value for item in self.dimensions],
            "query_capabilities": list(self.query_capabilities),
            "explicit_gaps": list(self.explicit_gaps),
            "digest": self.digest.value,
        }


@dataclass(frozen=True, slots=True)
class EngineeringCognitionCapabilityManifest:
    repository_id: StableId
    binding_id: StableId
    source_revision: str
    profiles: tuple[CognitionProfileCapability, ...]
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        repository_id: StableId,
        binding_id: StableId,
        profiles: Sequence[CognitionProfileCapability],
    ) -> "EngineeringCognitionCapabilityManifest":
        values = tuple(profiles)
        if (
            repository_id.kind != "repository"
            or binding_id.kind != "binding"
            or not values
            or tuple(item.ordinal for item in values) != tuple(range(len(values)))
            or len({item.profile_ref for item in values}) != len(values)
            or len({item.snapshot_id for item in values}) != len(values)
            or len({item.read_authority_digest for item in values}) != len(values)
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Cognition Capability Manifest authority order or identity is invalid",
            )
        revisions = {item.source_revision for item in values}
        if len(revisions) != 1:
            raise DomainError(
                ErrorCode.SOURCE_REVISION_INCONSISTENT,
                "Cognition Capability Manifest Profiles must share one exact revision",
            )
        source_revision = next(iter(revisions))
        core = {
            "schema": ENGINEERING_COGNITION_CAPABILITY_MANIFEST,
            "repository_id": repository_id.value,
            "binding_id": binding_id.value,
            "source_revision": source_revision,
            "profiles": tuple(item.digest.value for item in values),
        }
        return cls(
            repository_id=repository_id,
            binding_id=binding_id,
            source_revision=source_revision,
            profiles=values,
            digest=digest_of(core),
        )

    @property
    def dimensions(self) -> tuple[CognitionDimension, ...]:
        return tuple(
            sorted(
                {dimension for profile in self.profiles for dimension in profile.dimensions},
                key=lambda item: item.value,
            )
        )

    def model_view(self) -> dict[str, object]:
        return {
            "schema": ENGINEERING_COGNITION_CAPABILITY_MANIFEST,
            "repository_id": self.repository_id.value,
            "binding_id": self.binding_id.value,
            "source_revision": self.source_revision,
            "profiles": [item.model_view() for item in self.profiles],
            "dimensions": [item.value for item in self.dimensions],
            "digest": self.digest.value,
        }


@dataclass(frozen=True, slots=True)
class CognitionNeedEligibility:
    need: CognitionMaterialNeed
    eligible_profile_refs: tuple[str, ...]
    dimension_profile_bindings: tuple[
        tuple[CognitionDimension, tuple[str, ...]], ...
    ]
    capability_profile_bindings: tuple[tuple[str, tuple[str, ...]], ...]
    missing_dimensions: tuple[CognitionDimension, ...]
    missing_query_capabilities: tuple[str, ...]
    digest: Digest

    @property
    def eligible(self) -> bool:
        return not self.missing_dimensions and not self.missing_query_capabilities

    def model_view(self) -> dict[str, object]:
        return {
            "need": self.need.model_view(),
            "status": "ELIGIBLE" if self.eligible else "COGNITION_GAP",
            "eligible_profile_refs": list(self.eligible_profile_refs),
            "dimension_profile_bindings": [
                {
                    "dimension": dimension.value,
                    "profile_refs": list(profile_refs),
                }
                for dimension, profile_refs in self.dimension_profile_bindings
            ],
            "capability_profile_bindings": [
                {
                    "query_capability": capability,
                    "profile_refs": list(profile_refs),
                }
                for capability, profile_refs in self.capability_profile_bindings
            ],
            "missing_dimensions": [
                item.value for item in self.missing_dimensions
            ],
            "missing_query_capabilities": list(
                self.missing_query_capabilities
            ),
            "digest": self.digest.value,
        }


@dataclass(frozen=True, slots=True)
class CognitionEligibilityAssessment:
    classifier_ref: str
    question_digest: Digest
    manifest_digest: Digest
    needs: tuple[CognitionNeedEligibility, ...]
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        question: str,
        manifest: EngineeringCognitionCapabilityManifest,
    ) -> "CognitionEligibilityAssessment":
        material_needs = _material_needs(question)
        entries: list[CognitionNeedEligibility] = []
        for need in material_needs:
            dimension_bindings = tuple(
                (
                    dimension,
                    tuple(
                        profile.profile_ref
                        for profile in manifest.profiles
                        if dimension in profile.dimensions
                    ),
                )
                for dimension in need.required_dimensions
            )
            capability_bindings = tuple(
                (
                    capability,
                    tuple(
                        profile.profile_ref
                        for profile in manifest.profiles
                        if capability in profile.query_capabilities
                    ),
                )
                for capability in need.required_query_capabilities
            )
            eligible_profiles = tuple(
                profile.profile_ref
                for profile in manifest.profiles
                if set(need.required_dimensions).issubset(profile.dimensions)
                and set(need.required_query_capabilities).issubset(
                    profile.query_capabilities
                )
            )
            missing = tuple(
                dimension for dimension, profiles in dimension_bindings if not profiles
            )
            missing_capabilities = tuple(
                capability
                for capability, profiles in capability_bindings
                if not profiles
            )
            core = {
                "need_digest": need.digest.value,
                "eligible_profile_refs": eligible_profiles,
                "dimension_profile_bindings": tuple(
                    (
                        dimension.value,
                        profile_refs,
                    )
                    for dimension, profile_refs in dimension_bindings
                ),
                "capability_profile_bindings": capability_bindings,
                "missing_dimensions": tuple(item.value for item in missing),
                "missing_query_capabilities": missing_capabilities,
            }
            entries.append(
                CognitionNeedEligibility(
                    need=need,
                    eligible_profile_refs=eligible_profiles,
                    dimension_profile_bindings=dimension_bindings,
                    capability_profile_bindings=capability_bindings,
                    missing_dimensions=missing,
                    missing_query_capabilities=missing_capabilities,
                    digest=digest_of(
                        ["ENGINEERING_COGNITION_NEED_ELIGIBILITY@1", core]
                    ),
                )
            )
        question_digest = digest_of(
            [ENGINEERING_COGNITION_NEED_CLASSIFIER, question]
        )
        core = {
            "schema": "ENGINEERING_COGNITION_ELIGIBILITY_ASSESSMENT@1",
            "classifier_ref": ENGINEERING_COGNITION_NEED_CLASSIFIER,
            "question_digest": question_digest.value,
            "manifest_digest": manifest.digest.value,
            "needs": tuple(item.digest.value for item in entries),
        }
        return cls(
            classifier_ref=ENGINEERING_COGNITION_NEED_CLASSIFIER,
            question_digest=question_digest,
            manifest_digest=manifest.digest,
            needs=tuple(entries),
            digest=digest_of(core),
        )

    @property
    def required_dimensions(self) -> tuple[CognitionDimension, ...]:
        return tuple(
            sorted(
                {
                    dimension
                    for entry in self.needs
                    for dimension in entry.need.required_dimensions
                },
                key=lambda item: item.value,
            )
        )

    def model_view(self) -> dict[str, object]:
        return {
            "schema": "ENGINEERING_COGNITION_ELIGIBILITY_ASSESSMENT@1",
            "classifier_ref": self.classifier_ref,
            "question_digest": self.question_digest.value,
            "manifest_digest": self.manifest_digest.value,
            "needs": [item.model_view() for item in self.needs],
            "digest": self.digest.value,
        }


@dataclass(frozen=True, slots=True)
class MultiProfileWorldModelCognitionProjector:
    repository_id: StableId
    binding_id: StableId
    projectors: tuple[StructureBundleWorldModelCognitionProjector, ...]
    maximum_items: int = 32
    manifest: EngineeringCognitionCapabilityManifest = field(init=False)
    read_authority_digest: Digest = field(init=False)
    source_revision: str = field(init=False)

    def __post_init__(self) -> None:
        if (
            type(self.maximum_items) is not int
            or not 1 <= self.maximum_items <= 4_096
            or not self.projectors
        ):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "multi-Profile cognition requires one to 4096 bounded items",
            )
        capabilities = tuple(
            CognitionProfileCapability.from_projector(
                ordinal=ordinal,
                projector=projector,
            )
            for ordinal, projector in enumerate(self.projectors)
        )
        manifest = EngineeringCognitionCapabilityManifest.create(
            repository_id=self.repository_id,
            binding_id=self.binding_id,
            profiles=capabilities,
        )
        object.__setattr__(self, "manifest", manifest)
        object.__setattr__(self, "read_authority_digest", manifest.digest)
        object.__setattr__(self, "source_revision", manifest.source_revision)

    def project(
        self,
        *,
        request: EngineeringQuestionRequest,
    ) -> WorldModelCognitionContext:
        return self._project(request=request, relevance_query=request.original_question)

    def project_for_query(
        self,
        *,
        request: EngineeringQuestionRequest,
        query: str,
    ) -> WorldModelCognitionContext:
        if not isinstance(query, str) or not query.strip():
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "World Model relevance query must be non-empty text",
            )
        return self._project(request=request, relevance_query=query)

    def _project(
        self,
        *,
        request: EngineeringQuestionRequest,
        relevance_query: str,
    ) -> WorldModelCognitionContext:
        if (
            request.repository_id != self.repository_id
            or request.binding_id != self.binding_id
            or request.repository_revision != self.source_revision
            or request.world_model_read_authority_digest
            != self.read_authority_digest
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "multi-Profile cognition Manifest does not bind the Engineering Question Request",
            )
        assessment = CognitionEligibilityAssessment.create(
            question=request.original_question,
            manifest=self.manifest,
        )
        required = set(assessment.required_dimensions)
        explicit_source_scopes = _explicit_question_source_scopes(
            request.original_question,
            request.source_allowlist,
        )
        profile_source_scopes = {
            profile.profile_ref: _projector_source_scopes(projector)
            for profile, projector in zip(
                self.manifest.profiles,
                self.projectors,
                strict=True,
            )
        }
        scope_incompatible_profile_refs = {
            profile_ref
            for profile_ref, source_scopes in profile_source_scopes.items()
            if explicit_source_scopes
            and source_scopes
            and explicit_source_scopes.isdisjoint(source_scopes)
        }
        scope_compatible_profile_refs = {
            profile.profile_ref for profile in self.manifest.profiles
        } - scope_incompatible_profile_refs
        active_profile_refs: set[str] = set()
        for entry in assessment.needs:
            eligible_profile_refs = (
                set(entry.eligible_profile_refs)
                & scope_compatible_profile_refs
            )
            if eligible_profile_refs:
                active_profile_refs.update(eligible_profile_refs)
            else:
                partial_dimensions = {
                    profile.profile_ref: (
                        set(profile.dimensions)
                        & set(entry.need.required_dimensions)
                    )
                    for profile in self.manifest.profiles
                    if profile.profile_ref in scope_compatible_profile_refs
                }
                active_profile_refs.update(
                    profile_ref
                    for profile_ref, dimensions in partial_dimensions.items()
                    if dimensions
                    and not any(
                        dimensions < other_dimensions
                        for other_ref, other_dimensions in partial_dimensions.items()
                        if other_ref != profile_ref
                    )
                )
        candidates: list[CognitionItem] = []
        for profile, projector in zip(
            self.manifest.profiles, self.projectors, strict=True
        ):
            if profile.profile_ref not in active_profile_refs:
                continue
            for item in projector._project_items():
                if item.dimension not in required or item.dimension in {
                    CognitionDimension.COVERAGE,
                    CognitionDimension.EVIDENCE,
                    CognitionDimension.UNKNOWN,
                }:
                    continue
                candidates.append(item)
        relevant = _rank_relevant_cognition_items(
            relevance_query,
            candidates,
            maximum_items=self.maximum_items,
        )

        manifest_items = tuple(
            CognitionItem.create(
                dimension=CognitionDimension.COVERAGE,
                statement=_statement(
                    "COGNITION_CAPABILITY_PROFILE",
                    profile.model_view(),
                ),
                modality="COGNITION_CAPABILITY_MANIFEST_PROFILE",
                context_ref=self.manifest.digest.value,
                source_revision=self.source_revision,
                locator=(
                    "world-model:cognition-manifest:"
                    f"{self.manifest.digest.value}:profile:{profile.ordinal}"
                ),
                support_references=(),
                coverage=(
                    "Application-owned profile-specific exact Read Authority; "
                    "it does not merge Snapshot or Read Set identity."
                ),
            )
            for profile in self.manifest.profiles
        )
        assessment_items = tuple(
            CognitionItem.create(
                dimension=(
                    CognitionDimension.COVERAGE
                    if entry.eligible
                    else CognitionDimension.UNKNOWN
                ),
                statement=_statement(
                    "COGNITION_NEED_ELIGIBILITY",
                    entry.model_view(),
                ),
                modality="COGNITION_QUESTION_ELIGIBILITY",
                context_ref=assessment.digest.value,
                source_revision=self.source_revision,
                locator=(
                    "world-model:cognition-eligibility:"
                    f"{assessment.digest.value}:{entry.need.kind.value}"
                ),
                support_references=(),
                coverage=(
                    "Original-question material Need matched only against the "
                    "sealed Capability Manifest."
                ),
            )
            for entry in assessment.needs
        )
        mandatory = (*manifest_items, *assessment_items)
        unknowns: list[str] = []
        for profile in self.manifest.profiles:
            if profile.profile_ref not in scope_incompatible_profile_refs:
                continue
            unknowns.append(
                f"{profile.profile_ref}: explicit Source scope(s) "
                f"{', '.join(sorted(explicit_source_scopes))} are outside "
                "Profile root scope(s) "
                f"{', '.join(sorted(profile_source_scopes[profile.profile_ref]))}."
            )
        for entry in assessment.needs:
            if entry.missing_dimensions:
                unknowns.append(
                    f"Cognition Need {entry.need.kind.value} is missing dimensions: "
                    + ", ".join(
                        item.value for item in entry.missing_dimensions
                    )
                )
            if entry.missing_query_capabilities:
                unknowns.append(
                    f"Cognition Need {entry.need.kind.value} is missing query "
                    "capabilities: "
                    + ", ".join(entry.missing_query_capabilities)
                )
        if not relevant:
            unknowns.append(
                "No formal cognition item matched the current relevance query; "
                "profile capability is not evidence that this question is answered."
            )
        for profile in self.manifest.profiles:
            if profile.profile_ref in active_profile_refs:
                unknowns.extend(
                    f"{profile.profile_ref}: {gap}"
                    for gap in profile.explicit_gaps
                    if _gap_relevant(gap, required)
                )
        normalized_unknowns = tuple(dict.fromkeys(unknowns))

        def build(count: int) -> WorldModelCognitionContext:
            return WorldModelCognitionContext.create(
                request=request,
                scope_ref=f"cognition-binding:{self.binding_id.value}",
                context_ref=self.manifest.digest.value,
                schema_ref=ENGINEERING_COGNITION_CAPABILITY_MANIFEST,
                snapshot_ids=tuple(
                    item.snapshot_id.value for item in self.manifest.profiles
                ),
                read_authority_digest=self.read_authority_digest,
                source_revision=self.source_revision,
                items=(*mandatory, *relevant[:count]),
                coverage=(
                    canonical_json_bytes(self.manifest.model_view()).decode("utf-8"),
                    canonical_json_bytes(assessment.model_view()).decode("utf-8"),
                    "Relevant cognition projection selected "
                    f"{count} of {len(relevant)} query-matched formal items.",
                ),
                unknowns=normalized_unknowns,
            )

        low = 0
        high = len(relevant)
        selected: WorldModelCognitionContext | None = None
        while low <= high:
            middle = (low + high) // 2
            candidate = build(middle)
            if (
                len(canonical_json_bytes(candidate.model_view()))
                <= request.limits.maximum_world_model_bytes
            ):
                selected = candidate
                low = middle + 1
            else:
                high = middle - 1
        if selected is None:
            raise DomainError(
                ErrorCode.BUDGET_EXHAUSTED,
                "Cognition Capability Manifest metadata exceeds the World Model byte fuse",
            )
        return selected


def _material_needs(question: str) -> tuple[CognitionMaterialNeed, ...]:
    normalized = question.casefold()
    tokens = set(_feature_tokens(normalized))

    def contains(terms: set[str]) -> bool:
        return bool(tokens & terms) or any(term in normalized for term in terms)

    structure = contains(
        {
            "architecture",
            "component",
            "dependency",
            "module",
            "structure",
            "依赖",
            "架构",
            "模块",
            "结构",
            "组件",
        }
    )
    behavior = contains(
        {
            "authenticate",
            "authentication",
            "behavior",
            "call",
            "execute",
            "flow",
            "implementation",
            "login",
            "process",
            "work",
            "实现",
            "执行",
            "流程",
            "登录",
            "行为",
            "调用",
            "认证",
        }
    )
    boundary = contains(
        {
            "boundary",
            "configuration",
            "error",
            "exception",
            "fail",
            "failure",
            "permission",
            "responsibility",
            "state",
            "unknown",
            "异常",
            "失败",
            "权限",
            "状态",
            "职责",
            "边界",
            "配置",
        }
    )
    needs: list[CognitionMaterialNeed] = []
    if structure:
        needs.append(
            CognitionMaterialNeed.create(
                kind=CognitionMaterialNeedKind.STRUCTURE,
                required_dimensions=(
                    CognitionDimension.ENTITY,
                    CognitionDimension.RELATION,
                ),
                required_query_capabilities=("direct_dependency@1",),
            )
        )
    if behavior:
        needs.append(
            CognitionMaterialNeed.create(
                kind=CognitionMaterialNeedKind.IMPLEMENTATION_BEHAVIOR,
                required_dimensions=(
                    CognitionDimension.ENTITY,
                    CognitionDimension.BEHAVIOR,
                ),
                required_query_capabilities=("method_implementations@1",),
            )
        )
    if boundary:
        needs.append(
            CognitionMaterialNeed.create(
                kind=CognitionMaterialNeedKind.RESPONSIBILITY_FAILURE_BOUNDARY,
                required_dimensions=(
                    CognitionDimension.ENTITY,
                    CognitionDimension.BEHAVIOR,
                    CognitionDimension.STATE,
                    CognitionDimension.CONSTRAINT,
                ),
                required_query_capabilities=("method_implementations@1",),
            )
        )
    if not needs:
        needs.append(
            CognitionMaterialNeed.create(
                kind=CognitionMaterialNeedKind.GENERAL_ENGINEERING,
                required_dimensions=(
                    CognitionDimension.ENTITY,
                    CognitionDimension.RELATION,
                    CognitionDimension.BEHAVIOR,
                ),
            )
        )
    return tuple(needs)


def _feature_tokens(value: str) -> tuple[str, ...]:
    separated = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", value)
    return tuple(
        sorted(
            {
                item.casefold()
                for item in re.findall(r"[^\W_]+", separated, flags=re.UNICODE)
                if item
            }
        )
    )


def _statement_feature_tokens(value: str) -> tuple[str, ...]:
    """Tokenize semantic values without letting JSON field names match a query."""

    try:
        decoded = json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return _feature_tokens(value)
    values: list[str] = []
    stack = [decoded]
    while stack:
        current = stack.pop()
        if isinstance(current, Mapping):
            for key, item in current.items():
                if key in _NON_SEMANTIC_STATEMENT_FIELDS:
                    continue
                if (
                    key in _BASENAME_ONLY_STATEMENT_FIELDS
                    and isinstance(item, str)
                ):
                    values.append(item.rsplit("/", 1)[-1])
                    continue
                stack.append(item)
        elif isinstance(current, (list, tuple)):
            stack.extend(current)
        elif isinstance(current, str):
            values.append(current)
    return _feature_tokens(" ".join(values))


_NON_SEMANTIC_STATEMENT_FIELDS = frozenset(
    {
        "atom_kind",
        "declaration_completeness",
        "disposition",
        "entity_type",
        "entity_root_id",
        "evidence_references",
        "implementation_semantics_completeness",
        "kind",
        "legacy_static_call_completeness",
        "method_disposition",
        "object_entity_root_id",
        "observation_modality",
        "owning_scope_id",
        "resolution_class",
        "schema_ref",
        "source_revision",
        "subject_entity_root_id",
    }
)

_BASENAME_ONLY_STATEMENT_FIELDS = frozenset({"source_path"})

_EXACT_RELEVANCE_MATCH_WEIGHT = 4
_PREFIX_RELEVANCE_MATCH_WEIGHT = 1
_MINIMUM_RELATIVE_RELEVANCE_NUMERATOR = 3
_MINIMUM_RELATIVE_RELEVANCE_DENOMINATOR = 4

_RELEVANCE_QUERY_STOP_TOKENS = frozenset(
    {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "by",
        "for",
        "from",
        "in",
        "into",
        "is",
        "it",
        "of",
        "on",
        "or",
        "the",
        "these",
        "this",
        "to",
        "with",
    }
)


def _rank_relevant_cognition_items(
    query: str,
    items: Sequence[CognitionItem],
    *,
    maximum_items: int,
) -> tuple[CognitionItem, ...]:
    candidates = tuple(items)
    if not candidates:
        return ()
    query_tokens = tuple(
        item
        for item in _feature_tokens(query)
        if item not in _RELEVANCE_QUERY_STOP_TOKENS
    )
    item_tokens = tuple(
        frozenset(_statement_feature_tokens(item.statement))
        for item in candidates
    )
    document_frequency = Counter(
        token for tokens in item_tokens for token in tokens
    )
    discriminative_query_tokens = tuple(
        token
        for token in query_tokens
        if document_frequency[token] * 2 <= len(candidates)
    )
    if not discriminative_query_tokens:
        discriminative_query_tokens = query_tokens

    matches = tuple(
        _relevance_match_counts(discriminative_query_tokens, tokens)
        for tokens in item_tokens
    )
    strongest_exact_match = max(
        (exact for exact, _ in matches),
        default=0,
    )
    strongest_score = max(
        (
            exact * _EXACT_RELEVANCE_MATCH_WEIGHT
            + prefix * _PREFIX_RELEVANCE_MATCH_WEIGHT
            for exact, prefix in matches
        ),
        default=0,
    )
    minimum_score = (
        strongest_score * _MINIMUM_RELATIVE_RELEVANCE_NUMERATOR
        + _MINIMUM_RELATIVE_RELEVANCE_DENOMINATOR
        - 1
    ) // _MINIMUM_RELATIVE_RELEVANCE_DENOMINATOR
    ranked: list[tuple[int, int, str, CognitionItem]] = []
    for item, (exact_matches, prefix_matches) in zip(
        candidates, matches, strict=True
    ):
        score = (
            exact_matches * _EXACT_RELEVANCE_MATCH_WEIGHT
            + prefix_matches * _PREFIX_RELEVANCE_MATCH_WEIGHT
        )
        if score < max(1, minimum_score) or (
            strongest_exact_match >= 2 and exact_matches == 0
        ):
            continue
        ranked.append(
            (-score, -exact_matches, item.digest.value, item)
        )
    ranked.sort(key=lambda value: (value[0], value[1], value[2]))
    return _append_ranked_relation_endpoint_entities(
        tuple(item for _, _, _, item in ranked),
        candidates=candidates,
        maximum_items=maximum_items,
    )


def _append_ranked_relation_endpoint_entities(
    ranked: Sequence[CognitionItem],
    *,
    candidates: Sequence[CognitionItem],
    maximum_items: int,
) -> tuple[CognitionItem, ...]:
    """Keep direct typed relation endpoints with their selected relation.

    Lexical ranking may select a relation because the relation expresses the
    requested behavior while placing one of its endpoint Entity states below a
    global relative-score cutoff.  Appending the exact endpoint immediately
    after that relation preserves a bounded, deterministic graph projection and
    lets downstream navigation use the endpoint's verified source identity.
    This is direct graph closure only; it does not walk transitive neighbors or
    admit an otherwise unrelated lexical tail.
    """

    entities: dict[tuple[str, str, str], CognitionItem] = {}
    for item in candidates:
        entity_root_id = _cognition_entity_root_id(item)
        if entity_root_id is None:
            continue
        entities[(item.context_ref, item.source_revision, entity_root_id)] = item

    selected: list[CognitionItem] = []
    selected_digests: set[Digest] = set()
    for item in ranked:
        if item.digest not in selected_digests:
            selected.append(item)
            selected_digests.add(item.digest)
        if len(selected) == maximum_items:
            break
        for entity_root_id in _relation_endpoint_root_ids(item):
            endpoint = entities.get(
                (item.context_ref, item.source_revision, entity_root_id)
            )
            if endpoint is None or endpoint.digest in selected_digests:
                continue
            selected.append(endpoint)
            selected_digests.add(endpoint.digest)
            if len(selected) == maximum_items:
                break
        if len(selected) == maximum_items:
            break
    return tuple(selected)


def _cognition_entity_root_id(item: CognitionItem) -> str | None:
    if item.modality != "STRUCTURE_ENTITY_STATE":
        return None
    prefix = f"world-model:snapshot:{item.context_ref}:entity:"
    if not item.locator.startswith(prefix):
        return None
    entity_root_id = item.locator[len(prefix) :]
    return entity_root_id or None


def _relation_endpoint_root_ids(item: CognitionItem) -> tuple[str, ...]:
    if item.modality not in {
        "STRUCTURE_BEHAVIOR_RELATION",
        "STRUCTURE_RELATION_FACT",
    }:
        return ()
    try:
        statement = json.loads(item.statement)
    except (TypeError, json.JSONDecodeError):
        return ()
    if (
        not isinstance(statement, Mapping)
        or statement.get("kind") != "STRUCTURE_RELATION"
    ):
        return ()
    roots = (
        statement.get("subject_entity_root_id"),
        statement.get("object_entity_root_id"),
    )
    return tuple(
        dict.fromkeys(root for root in roots if isinstance(root, str) and root)
    )


def _explicit_question_source_scopes(
    question: str,
    source_allowlist: Sequence[str],
) -> frozenset[str]:
    normalized = question.casefold()
    available: set[str] = set()
    for path in source_allowlist:
        first, separator, _ = path.partition("/")
        if separator or (first not in {"", "."} and "." not in first):
            available.add(first.casefold())
    return frozenset(
        scope
        for scope in available
        if re.search(
            rf"(?<![0-9a-z_.-]){re.escape(scope)}(?![0-9a-z_.-])",
            normalized,
        )
    )


def _projector_source_scopes(
    projector: StructureBundleWorldModelCognitionProjector,
) -> frozenset[str]:
    scopes: set[str] = set()
    for coverage in projector.snapshot_bundle.coverages:
        root = coverage.root.logical_reactor_root
        first, separator, _ = root.partition("/")
        if not separator and (first in {"", "."} or "." in first):
            return frozenset()
        if separator or (first not in {"", "."} and "." not in first):
            scopes.add(first.casefold())
    return frozenset(scopes)


def _relevance_match_counts(
    query_tokens: Sequence[str], item_tokens: Sequence[str]
) -> tuple[int, int]:
    item_set = frozenset(item_tokens)
    exact = sum(query in item_set for query in query_tokens)
    prefix = sum(
        1
        for query in query_tokens
        if query not in item_set
        and any(
            min(len(query), len(item)) >= 4
            and (query.startswith(item) or item.startswith(query))
            for item in item_set
        )
    )
    return exact, prefix


def _gap_relevant(
    gap: str, required_dimensions: set[CognitionDimension]
) -> bool:
    if gap.startswith("BEHAVIOR_DIMENSION_"):
        return CognitionDimension.BEHAVIOR in required_dimensions
    if gap.startswith("STATE_DIMENSION_"):
        return CognitionDimension.STATE in required_dimensions
    if gap.startswith("UNIVERSAL_CONSTRAINT_"):
        return CognitionDimension.CONSTRAINT in required_dimensions
    if gap.startswith(("UNSUPPORTED_EXCLUDED_UNITS:", "FAILED_UNITS:")):
        return CognitionDimension.BEHAVIOR in required_dimensions
    if gap.startswith("INCOMPLETE_IMPLEMENTATION_METHODS:"):
        return CognitionDimension.BEHAVIOR in required_dimensions
    return True


def _entity_identity(
    record: EntityRecord | None,
    *,
    entities_by_id: Mapping[StableId, EntityRecord],
) -> dict[str, object] | None:
    if record is None:
        return None
    root = record.root.root_fields
    state = record.state.state_payload_fields
    result: dict[str, object] = {
        "entity_type": record.root.entity_type.value,
        "entity_root_id": record.root_id.value,
    }
    if record.root.entity_type is EntityType.SOFTWARE_SYSTEM:
        result["canonical_system_key"] = root["canonical_system_key"]
        if state.get("display_name") is not None:
            result["display_name"] = state["display_name"]
        elif state.get("label") is not None:
            result["label"] = state["label"]
    elif record.root.entity_type is EntityType.MAVEN_MODULE:
        result["effective_group_id"] = root["effective_group_id"]
        result["artifact_id"] = root["artifact_id"]
        result["label"] = state["label"]
        result["module_path"] = state["module_path"]
    elif record.root.entity_type is EntityType.JAVA_TYPE:
        result["qualified_name"] = root["qualified_name"]
        result["declaration_kind"] = state["declaration_kind"]
    elif record.root.entity_type is EntityType.JAVA_METHOD:
        result["declaring_type_qualified_name"] = root[
            "declaring_type_qualified_name"
        ]
        result["method_name"] = root["method_name"]
        result["parameter_types"] = root["parameter_types"]
    elif record.root.entity_type is EntityType.JAVA_IMPLEMENTATION_ATOM:
        result["atom_kind"] = root["atom_kind"]
        result["structural_ordinal"] = root["structural_ordinal"]
        method_id = StableId(str(root["method_entity_root_id"]))
        method = entities_by_id.get(method_id)
        if method is not None:
            result["owning_method"] = _entity_identity(
                method,
                entities_by_id=entities_by_id,
            )
    elif record.root.entity_type is EntityType.JAVA_STATE_SLOT:
        result["slot_kind"] = root["slot_kind"]
        result["canonical_identifier"] = root["canonical_identifier"]
    elif record.root.entity_type is EntityType.JAVA_SOURCE_FILE:
        result["source_path"] = root["source_path"]
    return result


def _statement(kind: str, value: dict[str, object]) -> str:
    return canonical_json_bytes({"kind": kind, **value}).decode("utf-8")


__all__ = [
    "CognitionEligibilityAssessment",
    "CognitionMaterialNeed",
    "CognitionMaterialNeedKind",
    "CognitionNeedEligibility",
    "CognitionProfileCapability",
    "ENGINEERING_COGNITION_CAPABILITY_MANIFEST",
    "ENGINEERING_COGNITION_NEED_CLASSIFIER",
    "ENGINEERING_QA_STRUCTURE_COGNITION_AUTHORITY",
    "EngineeringCognitionCapabilityManifest",
    "MultiProfileWorldModelCognitionProjector",
    "StructureBundleWorldModelCognitionProjector",
]
