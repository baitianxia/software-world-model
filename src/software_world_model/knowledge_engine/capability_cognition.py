"""Compact, exact-revision cognition read model for engineering Agents.

The objects in this module are a deterministic projection of admitted Source
evidence.  They are not a second Knowledge authority: every item retains the
exact source revision and provenance needed to return to the owning Source
boundary before an answer is delivered.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from enum import Enum
import re
from pathlib import PurePosixPath
from typing import Iterable, Mapping, Sequence

from software_world_model.cross_cutting import Digest, DomainError, ErrorCode, StableId, digest_of


CAPABILITY_COGNITION_SCHEMA = "JAVA-CAPABILITY-COGNITION@1"
CAPABILITY_COGNITION_PROFILE = "JAVA_CAPABILITY_COGNITION@1"

_EXACT_SEARCH_MATCH_WEIGHT = 4
_PREFIX_SEARCH_MATCH_WEIGHT = 1
_MINIMUM_RELATIVE_SEARCH_NUMERATOR = 3
_MINIMUM_RELATIVE_SEARCH_DENOMINATOR = 4
_SEARCH_QUERY_STOP_TOKENS = frozenset(
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


class CognitionEntityKind(str, Enum):
    MODULE = "MODULE"
    PACKAGE = "PACKAGE"
    FILE = "FILE"
    TYPE = "TYPE"
    METHOD = "METHOD"


class CognitionRelationKind(str, Enum):
    CONTAINS = "CONTAINS"
    IMPORTS = "IMPORTS"
    INHERITS = "INHERITS"
    IMPLEMENTS = "IMPLEMENTS"
    INVOKES = "INVOKES"


class CognitionBehaviorKind(str, Enum):
    CONDITION = "CONDITION"
    THROWS = "THROWS"
    CATCHES = "CATCHES"
    STATE_READ = "STATE_READ"
    STATE_WRITE = "STATE_WRITE"
    CALL = "CALL"
    EXTERNAL_CALL = "EXTERNAL_CALL"
    RETURN = "RETURN"


class CognitionCoverage(str, Enum):
    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"


class CognitionResolution(str, Enum):
    INTERNAL = "INTERNAL"
    EXTERNAL = "EXTERNAL"
    AMBIGUOUS = "AMBIGUOUS"
    UNKNOWN = "UNKNOWN"


class CognitionDirection(str, Enum):
    OUTGOING = "OUTGOING"
    INCOMING = "INCOMING"
    BOTH = "BOTH"


@dataclass(frozen=True, slots=True)
class CognitionEpistemics:
    coverage: CognitionCoverage
    conflicts: tuple[str, ...] = ()
    unknowns: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.coverage, CognitionCoverage):
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "cognition coverage is invalid")
        _canonical_texts(self.conflicts, "cognition conflicts")
        _canonical_texts(self.unknowns, "cognition unknowns")
        if self.coverage is CognitionCoverage.COMPLETE and (self.conflicts or self.unknowns):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "complete cognition cannot retain conflict or unknown markers",
            )

    def to_payload(self) -> dict[str, object]:
        return {
            "coverage": self.coverage.value,
            "conflicts": list(self.conflicts),
            "unknowns": list(self.unknowns),
        }

    @classmethod
    def from_payload(cls, value: object) -> "CognitionEpistemics":
        item = _mapping(value, "cognition epistemics")
        return cls(
            coverage=CognitionCoverage(_required_text(item, "coverage")),
            conflicts=_text_sequence(item.get("conflicts", ()), "cognition conflicts"),
            unknowns=_text_sequence(item.get("unknowns", ()), "cognition unknowns"),
        )


@dataclass(frozen=True, slots=True)
class CognitionProvenance:
    source_revision: str
    source_tree: str
    path: str
    start_line: int
    end_line: int
    content_digest: Digest
    evidence_kind: str

    def __post_init__(self) -> None:
        _git_oid(self.source_revision, "cognition source revision")
        _git_oid(self.source_tree, "cognition source tree")
        _relative_path(self.path)
        if (
            type(self.start_line) is not int
            or type(self.end_line) is not int
            or self.start_line < 1
            or self.end_line < self.start_line
        ):
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "cognition line range is invalid")
        if not isinstance(self.content_digest, Digest):
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "cognition content digest is invalid")
        _text(self.evidence_kind, "cognition evidence kind")

    @property
    def locator(self) -> str:
        suffix = f"L{self.start_line}"
        if self.end_line != self.start_line:
            suffix += f"-L{self.end_line}"
        return f"{self.path}:{suffix}"

    def to_payload(self) -> dict[str, object]:
        return {
            "source_revision": self.source_revision,
            "source_tree": self.source_tree,
            "path": self.path,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "content_digest": self.content_digest.value,
            "evidence_kind": self.evidence_kind,
            "locator": self.locator,
        }

    @classmethod
    def from_payload(cls, value: object) -> "CognitionProvenance":
        item = _mapping(value, "cognition provenance")
        return cls(
            source_revision=_required_text(item, "source_revision"),
            source_tree=_required_text(item, "source_tree"),
            path=_required_text(item, "path"),
            start_line=_required_int(item, "start_line"),
            end_line=_required_int(item, "end_line"),
            content_digest=Digest(_required_text(item, "content_digest")),
            evidence_kind=_required_text(item, "evidence_kind"),
        )


@dataclass(frozen=True, slots=True)
class CognitionEntity:
    entity_id: StableId
    kind: CognitionEntityKind
    name: str
    qualified_name: str
    parent_id: StableId | None
    provenance: CognitionProvenance
    epistemics: CognitionEpistemics
    attributes: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        if self.entity_id.kind != "cog_entity":
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "cognition entity ID is invalid")
        if not isinstance(self.kind, CognitionEntityKind):
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "cognition entity kind is invalid")
        _text(self.name, "cognition entity name")
        _text(self.qualified_name, "cognition qualified name")
        if self.parent_id is not None and self.parent_id.kind != "cog_entity":
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "cognition parent ID is invalid")
        _attributes(self.attributes)

    def to_payload(self) -> dict[str, object]:
        return {
            "entity_id": self.entity_id.value,
            "kind": self.kind.value,
            "name": self.name,
            "qualified_name": self.qualified_name,
            "parent_id": self.parent_id.value if self.parent_id is not None else None,
            "provenance": self.provenance.to_payload(),
            "epistemics": self.epistemics.to_payload(),
            "attributes": [{"name": key, "value": value} for key, value in self.attributes],
        }

    @classmethod
    def from_payload(cls, value: object) -> "CognitionEntity":
        item = _mapping(value, "cognition entity")
        parent = item.get("parent_id")
        return cls(
            entity_id=StableId(_required_text(item, "entity_id")),
            kind=CognitionEntityKind(_required_text(item, "kind")),
            name=_required_text(item, "name"),
            qualified_name=_required_text(item, "qualified_name"),
            parent_id=StableId(parent) if isinstance(parent, str) else None,
            provenance=CognitionProvenance.from_payload(item.get("provenance")),
            epistemics=CognitionEpistemics.from_payload(item.get("epistemics")),
            attributes=_attribute_payload(item.get("attributes", ())),
        )


@dataclass(frozen=True, slots=True)
class CognitionRelation:
    relation_id: StableId
    kind: CognitionRelationKind
    subject_id: StableId
    object_id: StableId | None
    object_symbol: str
    resolution: CognitionResolution
    provenance: CognitionProvenance
    epistemics: CognitionEpistemics
    attributes: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        if self.relation_id.kind != "cog_relation":
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "cognition relation ID is invalid")
        if self.subject_id.kind != "cog_entity":
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "cognition relation subject is invalid")
        if self.object_id is not None and self.object_id.kind != "cog_entity":
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "cognition relation object is invalid")
        _text(self.object_symbol, "cognition relation object symbol")
        if self.resolution is CognitionResolution.INTERNAL and self.object_id is None:
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "internal relation needs an entity object")
        if self.resolution is not CognitionResolution.INTERNAL and self.object_id is not None:
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "non-internal relation cannot claim an entity object")
        _attributes(self.attributes)

    def to_payload(self) -> dict[str, object]:
        return {
            "relation_id": self.relation_id.value,
            "kind": self.kind.value,
            "subject_id": self.subject_id.value,
            "object_id": self.object_id.value if self.object_id is not None else None,
            "object_symbol": self.object_symbol,
            "resolution": self.resolution.value,
            "provenance": self.provenance.to_payload(),
            "epistemics": self.epistemics.to_payload(),
            "attributes": [{"name": key, "value": value} for key, value in self.attributes],
        }

    @classmethod
    def from_payload(cls, value: object) -> "CognitionRelation":
        item = _mapping(value, "cognition relation")
        object_id = item.get("object_id")
        return cls(
            relation_id=StableId(_required_text(item, "relation_id")),
            kind=CognitionRelationKind(_required_text(item, "kind")),
            subject_id=StableId(_required_text(item, "subject_id")),
            object_id=StableId(object_id) if isinstance(object_id, str) else None,
            object_symbol=_required_text(item, "object_symbol"),
            resolution=CognitionResolution(_required_text(item, "resolution")),
            provenance=CognitionProvenance.from_payload(item.get("provenance")),
            epistemics=CognitionEpistemics.from_payload(item.get("epistemics")),
            attributes=_attribute_payload(item.get("attributes", ())),
        )


@dataclass(frozen=True, slots=True)
class CognitionBehavior:
    behavior_id: StableId
    method_id: StableId
    kind: CognitionBehaviorKind
    ordinal: int
    statement: str
    relation_id: StableId | None
    provenance: CognitionProvenance
    epistemics: CognitionEpistemics

    def __post_init__(self) -> None:
        if self.behavior_id.kind != "cog_behavior" or self.method_id.kind != "cog_entity":
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "cognition behavior identity is invalid")
        if type(self.ordinal) is not int or self.ordinal < 0:
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "cognition behavior ordinal is invalid")
        _text(self.statement, "cognition behavior statement")
        if self.relation_id is not None and self.relation_id.kind != "cog_relation":
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "cognition behavior relation is invalid")

    def to_payload(self) -> dict[str, object]:
        return {
            "behavior_id": self.behavior_id.value,
            "method_id": self.method_id.value,
            "kind": self.kind.value,
            "ordinal": self.ordinal,
            "statement": self.statement,
            "relation_id": self.relation_id.value if self.relation_id is not None else None,
            "provenance": self.provenance.to_payload(),
            "epistemics": self.epistemics.to_payload(),
        }

    @classmethod
    def from_payload(cls, value: object) -> "CognitionBehavior":
        item = _mapping(value, "cognition behavior")
        relation_id = item.get("relation_id")
        return cls(
            behavior_id=StableId(_required_text(item, "behavior_id")),
            method_id=StableId(_required_text(item, "method_id")),
            kind=CognitionBehaviorKind(_required_text(item, "kind")),
            ordinal=_required_int(item, "ordinal", minimum=0),
            statement=_required_text(item, "statement"),
            relation_id=StableId(relation_id) if isinstance(relation_id, str) else None,
            provenance=CognitionProvenance.from_payload(item.get("provenance")),
            epistemics=CognitionEpistemics.from_payload(item.get("epistemics")),
        )


@dataclass(frozen=True, slots=True)
class CapabilityCognitionSnapshot:
    snapshot_id: StableId
    project_name: str
    source_revision: str
    source_tree: str
    selected_roots: tuple[str, ...]
    frontend_ref: str
    entities: tuple[CognitionEntity, ...]
    relations: tuple[CognitionRelation, ...]
    behaviors: tuple[CognitionBehavior, ...]
    parsed_file_count: int
    partial_file_count: int
    conflicts: tuple[str, ...]
    unknowns: tuple[str, ...]
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        project_name: str,
        source_revision: str,
        source_tree: str,
        selected_roots: Sequence[str],
        frontend_ref: str,
        entities: Iterable[CognitionEntity],
        relations: Iterable[CognitionRelation],
        behaviors: Iterable[CognitionBehavior],
        parsed_file_count: int,
        partial_file_count: int,
        conflicts: Sequence[str] = (),
        unknowns: Sequence[str] = (),
    ) -> "CapabilityCognitionSnapshot":
        ordered_entities = tuple(sorted(entities, key=lambda item: item.entity_id.value))
        ordered_relations = tuple(sorted(relations, key=lambda item: item.relation_id.value))
        ordered_behaviors = tuple(
            sorted(
                behaviors,
                key=lambda item: (
                    item.method_id.value,
                    item.ordinal,
                    item.behavior_id.value,
                ),
            )
        )
        roots = tuple(sorted({_relative_path(item) for item in selected_roots}))
        conflict_values = tuple(sorted(set(conflicts)))
        unknown_values = tuple(sorted(set(unknowns)))
        core = _snapshot_core(
            project_name=_text(project_name, "cognition project name"),
            source_revision=_git_oid(source_revision, "cognition source revision"),
            source_tree=_git_oid(source_tree, "cognition source tree"),
            selected_roots=roots,
            frontend_ref=_text(frontend_ref, "cognition frontend reference"),
            entities=ordered_entities,
            relations=ordered_relations,
            behaviors=ordered_behaviors,
            parsed_file_count=parsed_file_count,
            partial_file_count=partial_file_count,
            conflicts=conflict_values,
            unknowns=unknown_values,
        )
        allocation = digest_of(core)
        snapshot_id = StableId(f"cog_snapshot_{allocation.value[-32:]}")
        digest = digest_of({**core, "snapshot_id": snapshot_id.value})
        value = cls(
            snapshot_id=snapshot_id,
            project_name=project_name,
            source_revision=source_revision,
            source_tree=source_tree,
            selected_roots=roots,
            frontend_ref=frontend_ref,
            entities=ordered_entities,
            relations=ordered_relations,
            behaviors=ordered_behaviors,
            parsed_file_count=parsed_file_count,
            partial_file_count=partial_file_count,
            conflicts=conflict_values,
            unknowns=unknown_values,
            digest=digest,
        )
        value._validate()
        return value

    def _validate(self) -> None:
        if type(self.parsed_file_count) is not int or self.parsed_file_count < 0:
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "parsed file count is invalid")
        if type(self.partial_file_count) is not int or self.partial_file_count < 0:
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "partial file count is invalid")
        entity_ids = {item.entity_id for item in self.entities}
        relation_ids = {item.relation_id for item in self.relations}
        if len(entity_ids) != len(self.entities) or len(relation_ids) != len(self.relations):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "cognition snapshot contains duplicate identities",
            )
        for entity in self.entities:
            if entity.provenance.source_revision != self.source_revision or entity.provenance.source_tree != self.source_tree:
                raise DomainError(ErrorCode.AUTHORITY_RECORD_INCONSISTENT, "cognition entity revision drifted")
            if entity.parent_id is not None and entity.parent_id not in entity_ids:
                raise DomainError(ErrorCode.AUTHORITY_RECORD_INCONSISTENT, "cognition parent is absent")
        method_ids = {item.entity_id for item in self.entities if item.kind is CognitionEntityKind.METHOD}
        for relation in self.relations:
            if relation.subject_id not in entity_ids or (
                relation.object_id is not None and relation.object_id not in entity_ids
            ):
                raise DomainError(ErrorCode.AUTHORITY_RECORD_INCONSISTENT, "cognition relation endpoint is absent")
        for behavior in self.behaviors:
            if behavior.method_id not in method_ids or (
                behavior.relation_id is not None and behavior.relation_id not in relation_ids
            ):
                raise DomainError(ErrorCode.AUTHORITY_RECORD_INCONSISTENT, "cognition behavior owner is absent")

    def to_payload(self) -> dict[str, object]:
        core = _snapshot_core(
            project_name=self.project_name,
            source_revision=self.source_revision,
            source_tree=self.source_tree,
            selected_roots=self.selected_roots,
            frontend_ref=self.frontend_ref,
            entities=self.entities,
            relations=self.relations,
            behaviors=self.behaviors,
            parsed_file_count=self.parsed_file_count,
            partial_file_count=self.partial_file_count,
            conflicts=self.conflicts,
            unknowns=self.unknowns,
        )
        return {**core, "snapshot_id": self.snapshot_id.value, "digest": self.digest.value}

    @classmethod
    def from_payload(cls, value: object) -> "CapabilityCognitionSnapshot":
        item = _mapping(value, "capability cognition snapshot")
        if item.get("schema") != CAPABILITY_COGNITION_SCHEMA or item.get("profile_ref") != CAPABILITY_COGNITION_PROFILE:
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "cognition artifact schema is unsupported")
        created = cls.create(
            project_name=_required_text(item, "project_name"),
            source_revision=_required_text(item, "source_revision"),
            source_tree=_required_text(item, "source_tree"),
            selected_roots=_text_sequence(item.get("selected_roots"), "selected roots"),
            frontend_ref=_required_text(item, "frontend_ref"),
            entities=tuple(CognitionEntity.from_payload(entry) for entry in _sequence(item.get("entities"), "entities")),
            relations=tuple(CognitionRelation.from_payload(entry) for entry in _sequence(item.get("relations"), "relations")),
            behaviors=tuple(CognitionBehavior.from_payload(entry) for entry in _sequence(item.get("behaviors"), "behaviors")),
            parsed_file_count=_required_int(item, "parsed_file_count", minimum=0),
            partial_file_count=_required_int(item, "partial_file_count", minimum=0),
            conflicts=_text_sequence(item.get("conflicts", ()), "snapshot conflicts"),
            unknowns=_text_sequence(item.get("unknowns", ()), "snapshot unknowns"),
        )
        if item.get("snapshot_id") != created.snapshot_id.value or item.get("digest") != created.digest.value:
            raise DomainError(ErrorCode.AUTHORITY_RECORD_INCONSISTENT, "cognition artifact digest is invalid")
        return created


@dataclass(frozen=True, slots=True)
class CognitionPage:
    operation: str
    items: tuple[Mapping[str, object], ...]
    total: int
    next_cursor: int | None
    snapshot_digest: Digest
    snapshot_epistemics: CognitionEpistemics

    def to_payload(self) -> dict[str, object]:
        return {
            "operation": self.operation,
            "items": [dict(item) for item in self.items],
            "total": self.total,
            "next_cursor": self.next_cursor,
            "snapshot_digest": self.snapshot_digest.value,
            "snapshot_epistemics": self.snapshot_epistemics.to_payload(),
        }


class CapabilityCognitionIndex:
    """Three bounded Agent-facing cognition operations over one snapshot."""

    def __init__(self, snapshot: CapabilityCognitionSnapshot) -> None:
        if not isinstance(snapshot, CapabilityCognitionSnapshot):
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "cognition index needs a snapshot")
        self.snapshot = snapshot
        self._snapshot_epistemics = (
            CognitionEpistemics(
                CognitionCoverage.PARTIAL,
                conflicts=snapshot.conflicts,
                unknowns=snapshot.unknowns,
            )
            if snapshot.conflicts or snapshot.unknowns or snapshot.partial_file_count
            else CognitionEpistemics(CognitionCoverage.COMPLETE)
        )
        self._entities = {item.entity_id: item for item in snapshot.entities}
        self._relations = {item.relation_id: item for item in snapshot.relations}
        self._behaviors_by_method: dict[StableId, tuple[CognitionBehavior, ...]] = {}
        for method_id in {item.method_id for item in snapshot.behaviors}:
            self._behaviors_by_method[method_id] = tuple(
                item for item in snapshot.behaviors if item.method_id == method_id
            )
        self._search_documents: dict[StableId, frozenset[str]] = {}
        token_frequency: Counter[str] = Counter()
        for entity in snapshot.entities:
            semantic_values = [entity.name, entity.qualified_name]
            semantic_values.extend(
                PurePosixPath(value).name if key == "source_path" else value
                for key, value in entity.attributes
            )
            semantic_values.extend(
                behavior.statement
                for behavior in self._behaviors_by_method.get(entity.entity_id, ())
            )
            searchable_tokens = frozenset(_tokens(" ".join(semantic_values)))
            token_frequency.update(searchable_tokens)
            self._search_documents[entity.entity_id] = searchable_tokens
        self._search_token_frequency = dict(token_frequency)
        method_contract_companions: dict[StableId, dict[StableId, CognitionEntity]] = {}
        for relation in snapshot.relations:
            if (
                relation.kind is not CognitionRelationKind.IMPLEMENTS
                or relation.object_id is None
            ):
                continue
            subject = self._entities[relation.subject_id]
            object_entity = self._entities[relation.object_id]
            if (
                subject.kind is not CognitionEntityKind.METHOD
                or object_entity.kind is not CognitionEntityKind.METHOD
            ):
                continue
            method_contract_companions.setdefault(subject.entity_id, {})[
                object_entity.entity_id
            ] = object_entity
            method_contract_companions.setdefault(object_entity.entity_id, {})[
                subject.entity_id
            ] = subject
        self._method_contract_companions = {
            entity_id: tuple(
                sorted(values.values(), key=lambda item: item.entity_id.value)
            )
            for entity_id, values in method_contract_companions.items()
        }

    def search(
        self,
        query: str,
        *,
        kinds: Sequence[CognitionEntityKind] = (),
        cursor: int = 0,
        limit: int = 12,
    ) -> CognitionPage:
        query_value = _text(query, "cognition query")
        allowed = frozenset(kinds)
        if any(not isinstance(item, CognitionEntityKind) for item in allowed):
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "cognition kind filter is invalid")
        query_tokens = self._search_query_tokens(query_value)
        matches: list[tuple[int, int, str, CognitionEntity]] = []
        for entity in self.snapshot.entities:
            if allowed and entity.kind not in allowed:
                continue
            exact, prefix = self._match_counts(query_tokens, entity)
            score = exact * _EXACT_SEARCH_MATCH_WEIGHT + prefix * _PREFIX_SEARCH_MATCH_WEIGHT
            if score > 0:
                matches.append((score, exact, entity.qualified_name.lower(), entity))
        strongest_score = max((item[0] for item in matches), default=0)
        strongest_exact = max((item[1] for item in matches), default=0)
        minimum_score = (
            strongest_score * _MINIMUM_RELATIVE_SEARCH_NUMERATOR
            + _MINIMUM_RELATIVE_SEARCH_DENOMINATOR
            - 1
        ) // _MINIMUM_RELATIVE_SEARCH_DENOMINATOR
        ranked = [
            (-score, -exact, qualified_name, entity)
            for score, exact, qualified_name, entity in matches
            if score >= max(1, minimum_score)
            and not (strongest_exact >= 2 and exact == 0)
        ]
        ranked.sort(
            key=lambda item: (
                item[0],
                item[1],
                _search_kind_priority(item[3].kind),
                item[2],
                item[3].entity_id.value,
            )
        )
        expanded: list[tuple[int, int, str, CognitionEntity]] = []
        selected_ids: set[StableId] = set()
        for item in ranked:
            entity = item[3]
            if entity.entity_id not in selected_ids:
                expanded.append(item)
                selected_ids.add(entity.entity_id)
            for companion in self._method_contract_companions.get(entity.entity_id, ()):
                if companion.entity_id in selected_ids:
                    continue
                companion_exact, companion_prefix = self._counts_for_tokens(
                    query_tokens,
                    self._search_documents[companion.entity_id],
                )
                companion_score = (
                    companion_exact * _EXACT_SEARCH_MATCH_WEIGHT
                    + companion_prefix * _PREFIX_SEARCH_MATCH_WEIGHT
                )
                expanded.append(
                    (
                        -companion_score,
                        -companion_exact,
                        companion.qualified_name.lower(),
                        companion,
                    )
                )
                selected_ids.add(companion.entity_id)
        # Diversify the fixed default navigation window, not the requested
        # page: every cursor/limit must slice the same ordered entity domain.
        # Move one equally ranked, self-name-matching method into an all-TYPE
        # window; retain all other entities and their relative order. Lexical
        # relevance, Source identity and authority are unchanged.
        navigation_window = 12
        prefix = expanded[:navigation_window]
        if len(prefix) == navigation_window:
            matching_positions = [
                position for position, item in enumerate(prefix)
                if item[3].kind is CognitionEntityKind.METHOD
                and any(token in _tokens(item[3].name) for token in query_tokens)
            ]
            method_candidates = [
                (position, item)
                for position, item in enumerate(expanded[navigation_window:], navigation_window)
                if item[3].kind is CognitionEntityKind.METHOD
                and any(token in _tokens(item[3].name) for token in query_tokens)
            ]
            need = min(2 - len(matching_positions), len(method_candidates))
            promoted = sorted(
                (item for _, item in method_candidates),
                key=lambda item: (item[0], item[1], item[2]),
            )[:need]
            promoted_ids = {item[3].entity_id for item in promoted}
            if promoted:
                expanded = [item for item in expanded if item[3].entity_id not in promoted_ids]
                insert_position = navigation_window - need
                expanded[insert_position:insert_position] = promoted
        selected, next_cursor = _page(expanded, cursor, limit)
        items = tuple(self._entity_summary(item[3], score=-item[0]) for item in selected)
        return CognitionPage(
            "SEARCH_COGNITION",
            items,
            len(expanded),
            next_cursor,
            self.snapshot.digest,
            self._snapshot_epistemics,
        )

    def traverse(
        self,
        entity_id: StableId | str,
        *,
        kinds: Sequence[CognitionRelationKind] = (),
        direction: CognitionDirection = CognitionDirection.OUTGOING,
        maximum_depth: int = 2,
        cursor: int = 0,
        limit: int = 24,
    ) -> CognitionPage:
        start = StableId(entity_id) if isinstance(entity_id, str) else entity_id
        if start not in self._entities:
            raise DomainError(
                ErrorCode.SOURCE_TARGET_NOT_FOUND,
                "cognition traversal start was not found",
            )
        if type(maximum_depth) is not int or not 1 <= maximum_depth <= 4:
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "cognition traversal depth must be 1..4")
        allowed = frozenset(kinds)
        if any(not isinstance(item, CognitionRelationKind) for item in allowed):
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "cognition relation filter is invalid")
        frontier: list[tuple[StableId, int, tuple[str, ...]]] = [(start, 0, ())]
        best_depth: dict[StableId, int] = {start: 0}
        paths: list[dict[str, object]] = []
        while frontier:
            current, depth, path = frontier.pop(0)
            if depth >= maximum_depth:
                continue
            adjacent = self._adjacent(current, allowed, direction)
            for relation, next_id, relation_direction in adjacent:
                relation_path = (*path, relation.relation_id.value)
                paths.append(
                    {
                        "depth": depth + 1,
                        "direction": relation_direction,
                        "relation": self._relation_summary(relation),
                        "from": self._entity_summary(self._entities[current]),
                        "to": (
                            self._entity_summary(self._entities[next_id])
                            if next_id is not None
                            else {"external_symbol": relation.object_symbol}
                        ),
                        "path_relation_ids": list(relation_path),
                    }
                )
                if next_id is not None and best_depth.get(next_id, maximum_depth + 1) > depth + 1:
                    best_depth[next_id] = depth + 1
                    frontier.append((next_id, depth + 1, relation_path))
        paths.sort(
            key=lambda item: (
                int(item["depth"]),
                str(item["relation"]["kind"]),
                str(item["relation"]["relation_id"]),
            )
        )
        selected, next_cursor = _page(paths, cursor, limit)
        return CognitionPage(
            "TRAVERSE_RELATIONS",
            tuple(selected),
            len(paths),
            next_cursor,
            self.snapshot.digest,
            self._snapshot_epistemics,
        )

    def detail(
        self,
        entity_id: StableId | str,
        *,
        cursor: int = 0,
        limit: int = 32,
    ) -> CognitionPage:
        target = StableId(entity_id) if isinstance(entity_id, str) else entity_id
        entity = self._entities.get(target)
        if entity is None:
            raise DomainError(
                ErrorCode.SOURCE_TARGET_NOT_FOUND,
                "cognition detail entity was not found",
            )
        parent_chain: list[dict[str, object]] = []
        current = entity
        seen: set[StableId] = set()
        while current.parent_id is not None and current.parent_id not in seen:
            seen.add(current.parent_id)
            current = self._entities[current.parent_id]
            parent_chain.append(self._entity_summary(current))
        details: list[dict[str, object]] = [
            {"detail_kind": "ENTITY", "entity": entity.to_payload(), "parent_chain": parent_chain}
        ]
        for relation in self.snapshot.relations:
            if relation.subject_id == target or relation.object_id == target:
                details.append(
                    {
                        "detail_kind": "RELATION",
                        "relation": self._relation_summary(relation),
                        "from": self._entity_summary(
                            self._entities[relation.subject_id]
                        ),
                        "to": (
                            self._entity_summary(self._entities[relation.object_id])
                            if relation.object_id is not None
                            else {"external_symbol": relation.object_symbol}
                        ),
                    }
                )
        for behavior in self._behaviors_by_method.get(target, ()):
            details.append({"detail_kind": "BEHAVIOR", "behavior": behavior.to_payload()})
        selected, next_cursor = _page(details, cursor, limit)
        return CognitionPage(
            "RETRIEVE_COGNITION_DETAIL",
            tuple(selected),
            len(details),
            next_cursor,
            self.snapshot.digest,
            self._snapshot_epistemics,
        )

    def _score(self, query: str, entity: CognitionEntity) -> int:
        exact, prefix = self._match_counts(self._search_query_tokens(query), entity)
        return exact * _EXACT_SEARCH_MATCH_WEIGHT + prefix * _PREFIX_SEARCH_MATCH_WEIGHT

    def _search_query_tokens(self, query: str) -> tuple[str, ...]:
        query_tokens = tuple(
            token for token in _tokens(query) if token not in _SEARCH_QUERY_STOP_TOKENS
        )
        discriminative = tuple(
            token
            for token in query_tokens
            if self._search_token_frequency.get(token, 0) * 2 <= len(self.snapshot.entities)
        )
        return discriminative or query_tokens

    def _match_counts(
        self,
        query_tokens: Sequence[str],
        entity: CognitionEntity,
    ) -> tuple[int, int]:
        item_tokens = self._search_documents[entity.entity_id]
        for companion in self._method_contract_companions.get(entity.entity_id, ()):
            item_tokens = item_tokens | self._search_documents[companion.entity_id]
        return self._counts_for_tokens(query_tokens, item_tokens)

    @staticmethod
    def _counts_for_tokens(
        query_tokens: Sequence[str],
        item_tokens: frozenset[str],
    ) -> tuple[int, int]:
        exact = sum(token in item_tokens for token in query_tokens)
        prefix = sum(
            1
            for query_token in query_tokens
            if query_token not in item_tokens
            and any(
                min(len(query_token), len(item_token)) >= 4
                and (
                    query_token.startswith(item_token)
                    or item_token.startswith(query_token)
                )
                for item_token in item_tokens
            )
        )
        return exact, prefix

    def _adjacent(
        self,
        entity_id: StableId,
        kinds: frozenset[CognitionRelationKind],
        direction: CognitionDirection,
    ) -> list[tuple[CognitionRelation, StableId | None, str]]:
        values: list[tuple[CognitionRelation, StableId | None, str]] = []
        for relation in self.snapshot.relations:
            if kinds and relation.kind not in kinds:
                continue
            if direction in {CognitionDirection.OUTGOING, CognitionDirection.BOTH} and relation.subject_id == entity_id:
                values.append((relation, relation.object_id, CognitionDirection.OUTGOING.value))
            if direction in {CognitionDirection.INCOMING, CognitionDirection.BOTH} and relation.object_id == entity_id:
                values.append((relation, relation.subject_id, CognitionDirection.INCOMING.value))
        values.sort(key=lambda item: (item[0].kind.value, item[0].relation_id.value, item[2]))
        return values

    def _entity_summary(self, entity: CognitionEntity, *, score: int | None = None) -> dict[str, object]:
        result: dict[str, object] = {
            "entity_id": entity.entity_id.value,
            "kind": entity.kind.value,
            "name": entity.name,
            "qualified_name": entity.qualified_name,
            "parent_id": entity.parent_id.value if entity.parent_id is not None else None,
            "coverage": entity.epistemics.coverage.value,
            "conflicts": list(entity.epistemics.conflicts),
            "unknowns": list(entity.epistemics.unknowns),
            "attributes": dict(entity.attributes),
            "provenance": entity.provenance.to_payload(),
        }
        if score is not None:
            result["score"] = score
        return result

    @staticmethod
    def _relation_summary(relation: CognitionRelation) -> dict[str, object]:
        return {
            "relation_id": relation.relation_id.value,
            "kind": relation.kind.value,
            "subject_id": relation.subject_id.value,
            "object_id": relation.object_id.value if relation.object_id is not None else None,
            "object_symbol": relation.object_symbol,
            "resolution": relation.resolution.value,
            "coverage": relation.epistemics.coverage.value,
            "conflicts": list(relation.epistemics.conflicts),
            "unknowns": list(relation.epistemics.unknowns),
            "attributes": dict(relation.attributes),
            "provenance": relation.provenance.to_payload(),
        }


def _search_kind_priority(kind: CognitionEntityKind) -> int:
    return {
        CognitionEntityKind.TYPE: 0,
        CognitionEntityKind.METHOD: 1,
        CognitionEntityKind.FILE: 2,
        CognitionEntityKind.PACKAGE: 3,
        CognitionEntityKind.MODULE: 4,
    }[kind]


def _snapshot_core(
    *,
    project_name: str,
    source_revision: str,
    source_tree: str,
    selected_roots: Sequence[str],
    frontend_ref: str,
    entities: Sequence[CognitionEntity],
    relations: Sequence[CognitionRelation],
    behaviors: Sequence[CognitionBehavior],
    parsed_file_count: int,
    partial_file_count: int,
    conflicts: Sequence[str],
    unknowns: Sequence[str],
) -> dict[str, object]:
    return {
        "schema": CAPABILITY_COGNITION_SCHEMA,
        "profile_ref": CAPABILITY_COGNITION_PROFILE,
        "project_name": project_name,
        "source_revision": source_revision,
        "source_tree": source_tree,
        "selected_roots": list(selected_roots),
        "frontend_ref": frontend_ref,
        "entities": [item.to_payload() for item in entities],
        "relations": [item.to_payload() for item in relations],
        "behaviors": [item.to_payload() for item in behaviors],
        "parsed_file_count": parsed_file_count,
        "partial_file_count": partial_file_count,
        "conflicts": list(conflicts),
        "unknowns": list(unknowns),
    }


def _page(values: Sequence, cursor: int, limit: int):
    if type(cursor) is not int or cursor < 0 or type(limit) is not int or not 1 <= limit <= 64:
        raise DomainError(ErrorCode.INVALID_ARGUMENT, "cognition page must use cursor >= 0 and limit 1..64")
    selected = values[cursor : cursor + limit]
    next_cursor = cursor + len(selected) if cursor + len(selected) < len(values) else None
    return selected, next_cursor


def _tokens(value: str) -> tuple[str, ...]:
    expanded = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", value)
    raw_identifiers = re.findall(r"[^\W_]+", value, flags=re.UNICODE)
    split_identifiers = re.findall(r"[^\W_]+", expanded, flags=re.UNICODE)
    return tuple(
        sorted(
            {
                item.casefold()
                for item in (*raw_identifiers, *split_identifiers)
                if item
            }
        )
    )


def _attributes(values: tuple[tuple[str, str], ...]) -> None:
    if tuple(sorted(values)) != values or len({key for key, _ in values}) != len(values):
        raise DomainError(ErrorCode.INVALID_ARGUMENT, "cognition attributes must be unique and sorted")
    for key, value in values:
        _text(key, "cognition attribute name")
        _text(value, "cognition attribute value")


def _attribute_payload(value: object) -> tuple[tuple[str, str], ...]:
    result = []
    for item in _sequence(value, "cognition attributes"):
        entry = _mapping(item, "cognition attribute")
        result.append((_required_text(entry, "name"), _required_text(entry, "value")))
    return tuple(result)


def _canonical_texts(values: tuple[str, ...], label: str) -> None:
    if tuple(sorted(set(values))) != values:
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} must be unique and sorted")
    for value in values:
        _text(value, label)


def _text_sequence(value: object, label: str) -> tuple[str, ...]:
    result = tuple(_text(item, label) for item in _sequence(value, label))
    return result


def _mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping) or any(not isinstance(key, str) for key in value):
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} must be an object")
    return value


def _sequence(value: object, label: str) -> Sequence[object]:
    if not isinstance(value, (list, tuple)):
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} must be an array")
    return value


def _required_text(value: Mapping[str, object], key: str) -> str:
    return _text(value.get(key), key)


def _required_int(value: Mapping[str, object], key: str, *, minimum: int = 1) -> int:
    item = value.get(key)
    if type(item) is not int or item < minimum:
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{key} must be an integer >= {minimum}")
    return item


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} must be canonical non-empty text")
    return value


def _git_oid(value: str, label: str) -> str:
    if re.fullmatch(r"[0-9a-f]{40}", value) is None:
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} must be an exact Git object ID")
    return value


def _relative_path(value: str) -> str:
    text = _text(value, "cognition path")
    path = PurePosixPath(text)
    if path.is_absolute() or str(path) != text or any(part in {"", ".", ".."} for part in path.parts):
        raise DomainError(ErrorCode.INVALID_ARGUMENT, "cognition path must be canonical and relative")
    return text


__all__ = [
    "CAPABILITY_COGNITION_PROFILE",
    "CAPABILITY_COGNITION_SCHEMA",
    "CapabilityCognitionIndex",
    "CapabilityCognitionSnapshot",
    "CognitionBehavior",
    "CognitionBehaviorKind",
    "CognitionCoverage",
    "CognitionDirection",
    "CognitionEntity",
    "CognitionEntityKind",
    "CognitionEpistemics",
    "CognitionPage",
    "CognitionProvenance",
    "CognitionRelation",
    "CognitionRelationKind",
    "CognitionResolution",
]
