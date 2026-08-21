"""Bundle-only World Model cognition projection for Engineering QA.

The projector mounts one verified no-payload Structure Snapshot Bundle through
an exact Structure View read authority.  It never reads a repository, chooses
facts from question text, or obtains a Source/Provider handle.  Projection is
deterministic and any byte-bound truncation is disclosed as an explicit
unknown boundary.
"""

from __future__ import annotations

from dataclasses import dataclass, field

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
from software_world_model.knowledge_engine.structure import RelationPredicate


ENGINEERING_QA_STRUCTURE_COGNITION_AUTHORITY = (
    "ENGINEERING_QA_STRUCTURE_COGNITION_AUTHORITY@1"
)

_BEHAVIOR_PREDICATES = frozenset(
    {
        RelationPredicate.DECLARES_METHOD,
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
                dimension=CognitionDimension.ENTITY,
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


def _statement(kind: str, value: dict[str, object]) -> str:
    return canonical_json_bytes({"kind": kind, **value}).decode("utf-8")


__all__ = [
    "ENGINEERING_QA_STRUCTURE_COGNITION_AUTHORITY",
    "StructureBundleWorldModelCognitionProjector",
]
