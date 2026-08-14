"""Typed, revision-stable knowledge primitives for Structure profiles.

This module is deliberately independent from the legacy objects in ``formal``.
It implements the identity derivation frozen for ITER-003 and provides a pure
admission boundary that persistence adapters can call before publication.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
import unicodedata
from typing import Any, TypeAlias
import re

from software_world_model.cross_cutting import (
    CanonicalizationError,
    Digest,
    DomainError,
    ErrorCode,
    StableId,
    canonical_json_bytes,
    digest_of,
)


MAVEN_STRUCTURE_SCHEMA_REF = "MAVEN-REACTOR-STRUCTURE@1.0.0"
MAVEN_STRUCTURE_SCHEMA_DIGEST = Digest(
    "sha256:947bea83028ff6658b01c18dccfd0c1ef028fa5e9a8701a4a0e90d16b8a58ce9"
)
MAVEN_STRUCTURE_PROFILE_REF = "MAVEN_REACTOR_STRUCTURE@1"
MAVEN_STRUCTURE_COVERAGE_ROOT_REF = "MAVEN_REACTOR_STRUCTURE_COVERAGE@1"
MAVEN_EVALUATION_CONTEXT_REF = "MAVEN-EVALUATION-CONTEXT@1.0.0"
MAVEN_EVALUATION_CONTEXT_DIGEST = Digest(
    "sha256:4fce4ccbcc8ddbe254dc90e8419a178ce37c6fd9ea287e6fad8d15d571161ffd"
)
MAVEN_CANONICALIZATION_REF = "MAVEN-REACTOR-CANONICALIZATION@1.0.0"
MAVEN_CANONICALIZATION_DIGEST = Digest(
    "sha256:4fae328bd8c2959cfc1eaaae3b9b27f40d601bf2ffb488bf3abe2cc81c5da6cf"
)
JAVA_STATIC_CALL_SCHEMA_REF = "JAVA-STATIC-CALL-GRAPH@1.0.0"
JAVA_STATIC_CALL_SCHEMA_DIGEST = Digest(
    "sha256:32ab1a12e5cb87a9751b25238d5ef6cace620ab0da47f0fc31f9d10e081e47c8"
)
JAVA_STATIC_CALL_PROFILE_REF = "JAVA_STATIC_CALL_GRAPH@1"
JAVA_STATIC_CALL_COVERAGE_ROOT_REF = "JAVA_STATIC_CALL_GRAPH_COVERAGE@1"
JAVA_STATIC_CALL_EVALUATION_CONTEXT_REF = (
    "JAVA-STATIC-CALL-EVALUATION-CONTEXT@1.0.0"
)
JAVA_STATIC_CALL_EVALUATION_CONTEXT_DIGEST = Digest(
    "sha256:0b08eab7334a06e267da6270b9074d0f121a235b086b61a898eb66cb83507f5c"
)
JAVA_STATIC_CALL_CANONICALIZATION_REF = (
    "JAVA-STATIC-CALL-CANONICALIZATION@1.0.0"
)
JAVA_STATIC_CALL_CANONICALIZATION_DIGEST = Digest(
    "sha256:598c0ab07e3411ecc46b80743332290305c4325f5a098a258a78cdd3d338582f"
)
JAVA_SOURCE_SEMANTICS_SCHEMA_REF = "JAVA-SOURCE-SEMANTICS@1.0.0"
JAVA_SOURCE_SEMANTICS_SCHEMA_DIGEST = digest_of(
    [
        JAVA_SOURCE_SEMANTICS_SCHEMA_REF,
        "TREE_SITTER_JAVA_FRONTEND@1",
        "JAVA_SOURCE_SEMANTICS_CANONICALIZATION@1",
    ]
)
JAVA_SOURCE_SEMANTICS_PROFILE_REF = "JAVA_SOURCE_SEMANTICS@1"
JAVA_SOURCE_SEMANTICS_COVERAGE_ROOT_REF = "JAVA_SOURCE_SEMANTICS_COVERAGE@1"
JAVA_SOURCE_SEMANTICS_FRONTEND_REF = "TREE_SITTER_JAVA_FRONTEND@1"
JAVA_SOURCE_SEMANTICS_FRONTEND_DIGEST = Digest(
    "sha256:45b49edd3dbaaec472533c13a4a6d1e3e0eab6a3be2d1529685bdca5560e65b3"
)
JAVA_SOURCE_SEMANTICS_EVALUATION_CONTEXT_REF = (
    "JAVA-SOURCE-SEMANTICS-EVALUATION-CONTEXT@1.0.0"
)
JAVA_SOURCE_SEMANTICS_EVALUATION_CONTEXT_DIGEST = digest_of(
    [
        JAVA_SOURCE_SEMANTICS_EVALUATION_CONTEXT_REF,
        JAVA_SOURCE_SEMANTICS_FRONTEND_REF,
        JAVA_SOURCE_SEMANTICS_FRONTEND_DIGEST,
        "MIT",
        "JAVA_LANGUAGE_ABI=14",
    ]
)
JAVA_SOURCE_SEMANTICS_CANONICALIZATION_REF = (
    "JAVA-SOURCE-SEMANTICS-CANONICALIZATION@1.0.0"
)
JAVA_SOURCE_SEMANTICS_CANONICALIZATION_DIGEST = digest_of(
    [
        JAVA_SOURCE_SEMANTICS_CANONICALIZATION_REF,
        "UTF8_BYTE_RANGE",
        "SOURCE_ORDER_ORDINAL",
        "NO_SOURCE_PAYLOAD",
    ]
)


class EntityType(str, Enum):
    SOFTWARE_SYSTEM = "SOFTWARE_SYSTEM"
    MAVEN_MODULE = "MAVEN_MODULE"
    JAVA_SOURCE_FILE = "JAVA_SOURCE_FILE"
    JAVA_TYPE = "JAVA_TYPE"
    JAVA_METHOD = "JAVA_METHOD"
    JAVA_IMPLEMENTATION_ATOM = "JAVA_IMPLEMENTATION_ATOM"
    JAVA_STATE_SLOT = "JAVA_STATE_SLOT"


class RelationPredicate(str, Enum):
    CONTAINS_MODULE = "CONTAINS_MODULE"
    DEPENDS_ON = "DEPENDS_ON"
    DECLARES_METHOD = "DECLARES_METHOD"
    CALLS = "CALLS"
    HAS_IMPLEMENTATION_ATOM = "HAS_IMPLEMENTATION_ATOM"
    CONTROLS = "CONTROLS"
    NEXT_IN_SOURCE = "NEXT_IN_SOURCE"
    CALL_SITE_TARGETS = "CALL_SITE_TARGETS"
    READS_STATE = "READS_STATE"
    WRITES_STATE = "WRITES_STATE"
    HANDLES_THROW = "HANDLES_THROW"


class ObservationModality(str, Enum):
    RECURSIVE_REACTOR_MEMBERSHIP = "RECURSIVE_REACTOR_MEMBERSHIP@1"
    POM_LOCAL_DECLARED_INTERNAL_DEPENDENCY = (
        "POM_LOCAL_DECLARED_INTERNAL_DEPENDENCY@1"
    )
    JAVA_SOURCE_DECLARATION = "JAVA_SOURCE_DECLARATION@1"
    JAVA_SOURCE_STATIC_CALL = "JAVA_SOURCE_STATIC_CALL@1"
    JAVA_SOURCE_IMPLEMENTATION_MEMBERSHIP = (
        "JAVA_SOURCE_IMPLEMENTATION_MEMBERSHIP@1"
    )
    JAVA_SOURCE_TRUE_BRANCH_CONTROL = "JAVA_SOURCE_TRUE_BRANCH_CONTROL@1"
    JAVA_SOURCE_FALSE_BRANCH_CONTROL = "JAVA_SOURCE_FALSE_BRANCH_CONTROL@1"
    JAVA_SOURCE_ORDER = "JAVA_SOURCE_ORDER@1"
    JAVA_SOURCE_CALL_SITE_TARGET = "JAVA_SOURCE_CALL_SITE_TARGET@1"
    JAVA_SOURCE_STATE_READ = "JAVA_SOURCE_STATE_READ@1"
    JAVA_SOURCE_STATE_WRITE = "JAVA_SOURCE_STATE_WRITE@1"
    JAVA_SOURCE_LEXICAL_EXCEPTION_HANDLER = (
        "JAVA_SOURCE_LEXICAL_EXCEPTION_HANDLER@1"
    )


class JavaSemanticDisposition(str, Enum):
    SEMANTICS_COMPLETE = "SEMANTICS_COMPLETE"
    UNSUPPORTED_EXCLUDED = "UNSUPPORTED_EXCLUDED"
    FAILED = "FAILED"


class JavaSemanticFacetCompleteness(str, Enum):
    COMPLETE = "COMPLETE"
    INCOMPLETE = "INCOMPLETE"
    FAILED = "FAILED"


class JavaImplementationAtomKind(str, Enum):
    BRANCH = "BRANCH"
    CALL_SITE = "CALL_SITE"
    RETURN = "RETURN"
    THROW = "THROW"
    CATCH = "CATCH"
    FINALLY = "FINALLY"
    STATE_READ = "STATE_READ"
    STATE_WRITE = "STATE_WRITE"


class JavaStateSlotKind(str, Enum):
    PARAMETER = "PARAMETER"
    LOCAL = "LOCAL"
    FIELD = "FIELD"


class JavaSemanticForm(str, Enum):
    BOOLEAN_SLOT_TEST = "BOOLEAN_SLOT_TEST"
    STATIC_CALL = "STATIC_CALL"
    RETURN_VALUE = "RETURN_VALUE"
    THROW_CONSTRUCTION = "THROW_CONSTRUCTION"
    LEXICAL_CATCH = "LEXICAL_CATCH"
    LEXICAL_FINALLY = "LEXICAL_FINALLY"
    STATE_ACCESS = "STATE_ACCESS"


class JavaSemanticOperator(str, Enum):
    NONE = "NONE"
    NOT = "NOT"
    IS_TRUE = "IS_TRUE"
    IS_FALSE = "IS_FALSE"
    IS_NULL = "IS_NULL"
    NOT_NULL = "NOT_NULL"
    AND = "AND"
    OR = "OR"
    DIRECT_CALL = "DIRECT_CALL"
    RETURN = "RETURN"
    THROW = "THROW"
    READ = "READ"
    WRITE = "WRITE"


class JavaValueCategory(str, Enum):
    BOOLEAN = "BOOLEAN"
    NULL = "NULL"
    INTEGER = "INTEGER"
    ENUM = "ENUM"
    CALL_RESULT = "CALL_RESULT"
    VOID = "VOID"
    EXCEPTION = "EXCEPTION"
    STATE = "STATE"


class JavaSemanticOperandKind(str, Enum):
    ENTITY_REF = "ENTITY_REF"
    BOOLEAN_LITERAL = "BOOLEAN_LITERAL"
    NULL_LITERAL = "NULL_LITERAL"
    INTEGER_LITERAL = "INTEGER_LITERAL"
    ENUM_LITERAL = "ENUM_LITERAL"
    TYPE_REF = "TYPE_REF"
    CONSTRUCTOR_ARITY = "CONSTRUCTOR_ARITY"


class JavaCallResolutionClass(str, Enum):
    LEGACY_EXACT_STATIC_DIRECT = "LEGACY_EXACT_STATIC_DIRECT"


JAVA_SOURCE_SEMANTICS_ENTITY_TYPES = tuple(
    sorted(
        (
            EntityType.JAVA_SOURCE_FILE,
            EntityType.JAVA_TYPE,
            EntityType.JAVA_METHOD,
            EntityType.JAVA_IMPLEMENTATION_ATOM,
            EntityType.JAVA_STATE_SLOT,
        ),
        key=lambda item: item.value,
    )
)
JAVA_SOURCE_SEMANTICS_RELATION_PREDICATES = tuple(
    sorted(
        (
            RelationPredicate.DECLARES_METHOD,
            RelationPredicate.CALLS,
            RelationPredicate.HAS_IMPLEMENTATION_ATOM,
            RelationPredicate.CONTROLS,
            RelationPredicate.NEXT_IN_SOURCE,
            RelationPredicate.CALL_SITE_TARGETS,
            RelationPredicate.READS_STATE,
            RelationPredicate.WRITES_STATE,
            RelationPredicate.HANDLES_THROW,
        ),
        key=lambda item: item.value,
    )
)

_JAVA_QUALIFIED_IDENTIFIER = re.compile(
    r"^[A-Za-z_$][A-Za-z0-9_$]*(?:\.[A-Za-z_$][A-Za-z0-9_$]*)*$"
)


class FactKind(str, Enum):
    LITERAL = "LITERAL"
    RELATION = "RELATION"


class LiteralType(str, Enum):
    BOOLEAN = "BOOLEAN"
    INTEGER = "INTEGER"
    STRING = "STRING"


class CoverageCompleteness(str, Enum):
    COMPLETE = "COMPLETE"


class PublicationMode(str, Enum):
    ENRICH = "ENRICH"
    REPLACE_COVERAGE = "REPLACE_COVERAGE"


class RootStateIdentity(str, Enum):
    DIFFERENT_ROOT = "DIFFERENT_ROOT"
    SAME_ROOT_SAME_STATE = "SAME_ROOT_SAME_STATE"
    SAME_ROOT_DIFFERENT_STATE = "SAME_ROOT_DIFFERENT_STATE"


class CoverageMemberKind(str, Enum):
    ENTITY = "ENTITY"
    LITERAL_FACT = "LITERAL_FACT"
    RELATION_FACT = "RELATION_FACT"


@dataclass(frozen=True, slots=True)
class StructureEvidence:
    """Immutable direct observation retained outside Snapshot membership.

    ``excerpt`` is the exact UTF-8 observation payload.  A no-payload read
    bundle may project the remaining fields, but cannot use that projection to
    re-create or expand the proposition supported by this record.
    """

    evidence_id: StableId
    artifact_id: StableId
    source_context_id: StableId
    byte_start: int
    byte_end: int
    locator: str
    excerpt: str
    excerpt_digest: Digest
    artifact_content_digest: Digest
    digest: Digest

    def __post_init__(self) -> None:
        _require_stable_id(self.evidence_id, "structure Evidence ID", kind="evidence")
        _require_stable_id(self.artifact_id, "Evidence Artifact ID")
        _require_stable_id(self.source_context_id, "Evidence Source Context ID")
        _require_digest(self.excerpt_digest, "Evidence excerpt digest")
        _require_digest(self.artifact_content_digest, "Evidence Artifact content digest")
        _require_digest(self.digest, "structure Evidence digest")
        self.require_valid_identity()

    @classmethod
    def create(
        cls,
        *,
        artifact_id: StableId,
        source_context_id: StableId,
        byte_start: int,
        byte_end: int,
        locator: str,
        excerpt: str,
        artifact_content_digest: Digest,
    ) -> "StructureEvidence":
        _require_stable_id(artifact_id, "Evidence Artifact ID")
        _require_stable_id(source_context_id, "Evidence Source Context ID")
        _require_digest(artifact_content_digest, "Evidence Artifact content digest")
        normalized_locator = _text(locator, "Evidence locator")
        _validate_excerpt_range(byte_start, byte_end, excerpt)
        excerpt_digest = digest_of(excerpt)
        core = CanonicalFields(
            {
                "artifact_id": artifact_id.value,
                "source_context_id": source_context_id.value,
                "byte_start": byte_start,
                "byte_end": byte_end,
                "locator": normalized_locator,
                "excerpt_digest": excerpt_digest.value,
                "artifact_content_digest": artifact_content_digest.value,
            }
        )
        identity_digest = digest_of(core)
        return cls(
            evidence_id=_stable("evidence", identity_digest),
            artifact_id=artifact_id,
            source_context_id=source_context_id,
            byte_start=byte_start,
            byte_end=byte_end,
            locator=normalized_locator,
            excerpt=excerpt,
            excerpt_digest=excerpt_digest,
            artifact_content_digest=artifact_content_digest,
            digest=identity_digest,
        )

    @property
    def observation(self) -> str:
        return self.excerpt

    @property
    def identity_fields(self) -> CanonicalFields:
        return CanonicalFields(
            {
                "artifact_id": self.artifact_id.value,
                "source_context_id": self.source_context_id.value,
                "byte_start": self.byte_start,
                "byte_end": self.byte_end,
                "locator": self.locator,
                "excerpt_digest": self.excerpt_digest.value,
                "artifact_content_digest": self.artifact_content_digest.value,
            }
        )

    def require_valid_identity(self) -> None:
        _validate_excerpt_range(self.byte_start, self.byte_end, self.excerpt)
        if self.locator != _text(self.locator, "Evidence locator"):
            _fail("EVIDENCE_LOCATOR_NOT_CANONICAL", "Evidence locator is not canonical")
        excerpt_digest = digest_of(self.excerpt)
        identity_digest = digest_of(self.identity_fields)
        if (
            excerpt_digest != self.excerpt_digest
            or identity_digest != self.digest
            or self.evidence_id != _stable("evidence", identity_digest)
        ):
            _fail("EVIDENCE_IDENTITY_MISMATCH", "structure Evidence identity is not canonical")


CanonicalScalar: TypeAlias = None | bool | int | str
# Keep this runtime-safe on the project's Python 3.11 floor.  CanonicalFields
# performs the recursive validation; the alias need not recursively name itself.
CanonicalValue: TypeAlias = CanonicalScalar | tuple[Any, ...] | Mapping[str, Any]


class CanonicalFields(Mapping[str, CanonicalValue]):
    """Small immutable mapping whose values are safe for the frozen codec."""

    __slots__ = ("_entries", "_values")

    def __init__(self, values: Mapping[str, object]) -> None:
        if not isinstance(values, Mapping):
            _fail("FIELDS_NOT_MAPPING", "canonical fields must be a mapping")
        normalized: list[tuple[str, CanonicalValue]] = []
        for key, value in values.items():
            if not isinstance(key, str):
                _fail("NON_STRING_FIELD_NAME", "canonical field names must be strings")
            normalized.append((_canonical_text(key, "canonical field name"), _canonical_value(value)))
        normalized.sort(key=lambda item: item[0])
        if len({key for key, _ in normalized}) != len(normalized):
            _fail("DUPLICATE_FIELD", "canonical fields must have unique names")
        self._entries = tuple(normalized)
        self._values = dict(normalized)

    def __getitem__(self, key: str) -> CanonicalValue:
        return self._values[key]

    def __iter__(self) -> Iterator[str]:
        return (key for key, _ in self._entries)

    def __len__(self) -> int:
        return len(self._entries)

    def __repr__(self) -> str:
        return f"CanonicalFields({dict(self._entries)!r})"

    def __hash__(self) -> int:
        return hash(self._entries)

    def as_dict(self) -> dict[str, object]:
        return {key: _plain_value(value) for key, value in self._entries}


_ENTITY_ROOT_FIELDS: dict[EntityType, tuple[str, ...]] = {
    EntityType.SOFTWARE_SYSTEM: ("owning_scope_id", "canonical_system_key"),
    EntityType.MAVEN_MODULE: (
        "owning_scope_id",
        "effective_group_id",
        "artifact_id",
    ),
    EntityType.JAVA_SOURCE_FILE: ("owning_scope_id", "source_path"),
    EntityType.JAVA_TYPE: ("owning_scope_id", "qualified_name"),
    EntityType.JAVA_METHOD: (
        "owning_scope_id",
        "declaring_type_qualified_name",
        "method_name",
        "parameter_types",
    ),
    EntityType.JAVA_IMPLEMENTATION_ATOM: (
        "owning_scope_id",
        "method_entity_root_id",
        "atom_kind",
        "structural_ordinal",
    ),
    EntityType.JAVA_STATE_SLOT: (
        "owning_scope_id",
        "declaring_entity_root_id",
        "slot_kind",
        "canonical_identifier",
        "declaration_ordinal",
    ),
}
_ENTITY_STATE_FIELDS: dict[EntityType, tuple[str, ...]] = {
    EntityType.SOFTWARE_SYSTEM: (
        "label",
        "effective_group_id",
        "artifact_id",
        "effective_version",
        "packaging",
        "source_binding_id",
        "source_revision",
        "root_pom_locator",
        "evidence_references",
    ),
    EntityType.MAVEN_MODULE: (
        "effective_version",
        "packaging",
        "module_path",
        "label",
        "source_revision",
        "evidence_references",
    ),
    EntityType.JAVA_SOURCE_FILE: (
        "source_revision",
        "disposition",
        "evidence_references",
    ),
    EntityType.JAVA_TYPE: (
        "simple_name",
        "package_name",
        "declaration_kind",
        "source_path",
        "source_revision",
        "evidence_references",
    ),
    EntityType.JAVA_METHOD: (
        "return_type",
        "visibility",
        "modifiers",
        "source_path",
        "source_revision",
        "evidence_references",
    ),
    EntityType.JAVA_IMPLEMENTATION_ATOM: (
        "source_revision",
        "source_order_ordinal",
        "semantic_form",
        "operator",
        "value_category",
        "semantic_operands",
        "referenced_entity_root_ids",
        "method_disposition",
        "evidence_references",
    ),
    EntityType.JAVA_STATE_SLOT: (
        "declared_type",
        "source_revision",
        "evidence_references",
    ),
}
_JAVA_TYPE_SEMANTICS_STATE_FIELDS = _ENTITY_STATE_FIELDS[EntityType.JAVA_TYPE] + (
    "disposition",
)
_JAVA_METHOD_SEMANTICS_STATE_FIELDS = _ENTITY_STATE_FIELDS[EntityType.JAVA_METHOD] + (
    "method_disposition",
    "declaration_completeness",
    "legacy_static_call_completeness",
    "implementation_semantics_completeness",
)
_ENTITY_IDENTITY_SCHEMES: dict[EntityType, str] = {
    EntityType.SOFTWARE_SYSTEM: "SOFTWARE_SYSTEM@1",
    EntityType.MAVEN_MODULE: "MAVEN_MODULE@1",
    EntityType.JAVA_SOURCE_FILE: "JAVA_SOURCE_FILE@1",
    EntityType.JAVA_TYPE: "JAVA_TYPE@1",
    EntityType.JAVA_METHOD: "JAVA_METHOD@1",
    EntityType.JAVA_IMPLEMENTATION_ATOM: "JAVA_IMPLEMENTATION_ATOM@1",
    EntityType.JAVA_STATE_SLOT: "JAVA_STATE_SLOT@1",
}
_RELATION_STATE_FIELDS = (
    "subject_entity_state_id",
    "object_entity_state_id",
    "source_revision",
    "knowledge_context_digest",
    "evidence_references",
)
_PREDICATE_STATE_FIELDS: dict[RelationPredicate, tuple[str, ...]] = {
    RelationPredicate.CONTAINS_MODULE: ("module_declaration_path",),
    RelationPredicate.DEPENDS_ON: (
        "declared_dependency_gav_expression",
        "resolved_dependency_gav",
        "scope",
        "type",
        "classifier",
        "optional",
    ),
    RelationPredicate.DECLARES_METHOD: ("declaration_ordinal",),
    RelationPredicate.CALLS: ("call_site_count",),
    RelationPredicate.HAS_IMPLEMENTATION_ATOM: ("source_order_ordinal",),
    RelationPredicate.CONTROLS: ("controlled_source_order_ordinal",),
    RelationPredicate.NEXT_IN_SOURCE: ("source_order_distance",),
    RelationPredicate.CALL_SITE_TARGETS: ("resolution_class",),
    RelationPredicate.READS_STATE: ("access_ordinal",),
    RelationPredicate.WRITES_STATE: ("access_ordinal",),
    RelationPredicate.HANDLES_THROW: ("handler_type",),
}
_COVERAGE_ROOT_FIELDS = (
    "owning_scope_id",
    "profile_ref",
    "schema_ref",
    "schema_digest",
    "source_binding_id",
    "logical_reactor_root",
    "maven_evaluation_context_ref",
    "maven_evaluation_context_digest",
    "covered_entity_types",
    "covered_relation_predicates",
    "canonicalization_ref",
    "canonicalization_digest",
)
_COVERAGE_STATE_FIELDS = (
    "source_revision",
    "knowledge_context_digest",
    "schema_ref",
    "schema_digest",
    "maven_evaluation_context_ref",
    "maven_evaluation_context_digest",
    "canonicalization_ref",
    "canonicalization_digest",
    "complete_member_manifest",
    "evidence_references",
)


@dataclass(frozen=True, slots=True)
class EntityRef:
    entity_root_id: StableId
    entity_type: EntityType
    owning_scope_id: StableId

    def __post_init__(self) -> None:
        _require_stable_id(self.entity_root_id, "entity root ID", kind="entity_root")
        _require_stable_id(self.owning_scope_id, "entity owning scope ID")
        object.__setattr__(self, "entity_type", _enum(EntityType, self.entity_type, "entity type"))

    @classmethod
    def from_root(cls, root: "EntityRoot") -> "EntityRef":
        root.require_valid_identity()
        return cls(
            entity_root_id=root.entity_root_id,
            entity_type=root.entity_type,
            owning_scope_id=root.owning_scope_id,
        )

    def canonical_value(self) -> dict[str, str]:
        return {
            "entity_root_id": self.entity_root_id.value,
            "entity_type": self.entity_type.value,
            "owning_scope_id": self.owning_scope_id.value,
        }


@dataclass(frozen=True, slots=True)
class EntityRoot:
    entity_root_id: StableId
    entity_type: EntityType
    identity_scheme: str
    root_fields: CanonicalFields
    allocation_key_digest: Digest

    def __post_init__(self) -> None:
        object.__setattr__(self, "entity_type", _enum(EntityType, self.entity_type, "entity type"))
        _require_stable_id(self.entity_root_id, "entity root ID", kind="entity_root")
        _require_digest(self.allocation_key_digest, "entity root allocation key digest")
        self.require_valid_identity()

    @classmethod
    def create(
        cls,
        *,
        entity_type: EntityType | str,
        owning_scope_id: StableId,
        identity_fields: Mapping[str, object],
    ) -> "EntityRoot":
        normalized_type = _enum(EntityType, entity_type, "entity type")
        _require_stable_id(owning_scope_id, "entity owning scope ID")
        supplied = dict(identity_fields)
        supplied["owning_scope_id"] = owning_scope_id.value
        root_fields = _exact_fields(
            supplied,
            _ENTITY_ROOT_FIELDS[normalized_type],
            f"{normalized_type.value} root",
        )
        identity_scheme = _ENTITY_IDENTITY_SCHEMES[normalized_type]
        allocation_key = digest_of(
            ["ENTITY_ROOT", normalized_type.value, identity_scheme, root_fields]
        )
        return cls(
            entity_root_id=_stable("entity_root", allocation_key),
            entity_type=normalized_type,
            identity_scheme=identity_scheme,
            root_fields=root_fields,
            allocation_key_digest=allocation_key,
        )

    @classmethod
    def software_system(
        cls,
        *,
        owning_scope_id: StableId,
        canonical_system_key: str,
    ) -> "EntityRoot":
        return cls.create(
            entity_type=EntityType.SOFTWARE_SYSTEM,
            owning_scope_id=owning_scope_id,
            identity_fields={"canonical_system_key": canonical_system_key},
        )

    @classmethod
    def maven_module(
        cls,
        *,
        owning_scope_id: StableId,
        effective_group_id: str,
        artifact_id: str,
    ) -> "EntityRoot":
        return cls.create(
            entity_type=EntityType.MAVEN_MODULE,
            owning_scope_id=owning_scope_id,
            identity_fields={
                "effective_group_id": effective_group_id,
                "artifact_id": artifact_id,
            },
        )

    @classmethod
    def java_source_file(
        cls,
        *,
        owning_scope_id: StableId,
        source_path: str,
    ) -> "EntityRoot":
        return cls.create(
            entity_type=EntityType.JAVA_SOURCE_FILE,
            owning_scope_id=owning_scope_id,
            identity_fields={"source_path": source_path},
        )

    @classmethod
    def java_type(
        cls,
        *,
        owning_scope_id: StableId,
        qualified_name: str,
    ) -> "EntityRoot":
        return cls.create(
            entity_type=EntityType.JAVA_TYPE,
            owning_scope_id=owning_scope_id,
            identity_fields={"qualified_name": qualified_name},
        )

    @classmethod
    def java_method(
        cls,
        *,
        owning_scope_id: StableId,
        declaring_type_qualified_name: str,
        method_name: str,
        parameter_types: Sequence[str],
    ) -> "EntityRoot":
        return cls.create(
            entity_type=EntityType.JAVA_METHOD,
            owning_scope_id=owning_scope_id,
            identity_fields={
                "declaring_type_qualified_name": declaring_type_qualified_name,
                "method_name": method_name,
                "parameter_types": tuple(parameter_types),
            },
        )

    @classmethod
    def java_implementation_atom(
        cls,
        *,
        owning_scope_id: StableId,
        method_entity_root_id: StableId,
        atom_kind: str,
        structural_ordinal: int,
    ) -> "EntityRoot":
        return cls.create(
            entity_type=EntityType.JAVA_IMPLEMENTATION_ATOM,
            owning_scope_id=owning_scope_id,
            identity_fields={
                "method_entity_root_id": method_entity_root_id,
                "atom_kind": atom_kind,
                "structural_ordinal": structural_ordinal,
            },
        )

    @classmethod
    def java_state_slot(
        cls,
        *,
        owning_scope_id: StableId,
        declaring_entity_root_id: StableId,
        slot_kind: str,
        canonical_identifier: str,
        declaration_ordinal: int,
    ) -> "EntityRoot":
        return cls.create(
            entity_type=EntityType.JAVA_STATE_SLOT,
            owning_scope_id=owning_scope_id,
            identity_fields={
                "declaring_entity_root_id": declaring_entity_root_id,
                "slot_kind": slot_kind,
                "canonical_identifier": canonical_identifier,
                "declaration_ordinal": declaration_ordinal,
            },
        )

    @property
    def owning_scope_id(self) -> StableId:
        return StableId(_required_str(self.root_fields, "owning_scope_id"))

    @property
    def root_id(self) -> StableId:
        return self.entity_root_id

    @property
    def ref(self) -> EntityRef:
        return EntityRef.from_root(self)

    def require_valid_identity(self) -> None:
        expected_scheme = _ENTITY_IDENTITY_SCHEMES[self.entity_type]
        _require_exact_keys(
            self.root_fields,
            _ENTITY_ROOT_FIELDS[self.entity_type],
            f"{self.entity_type.value} root",
        )
        if self.identity_scheme != expected_scheme:
            _fail("IDENTITY_SCHEME_MISMATCH", "entity identity scheme does not match its type")
        allocation_key = digest_of(
            ["ENTITY_ROOT", self.entity_type.value, self.identity_scheme, self.root_fields]
        )
        if allocation_key != self.allocation_key_digest or self.entity_root_id != _stable(
            "entity_root", allocation_key
        ):
            _fail("ENTITY_ROOT_IDENTITY_MISMATCH", "entity Root identity is not canonical")


@dataclass(frozen=True, slots=True)
class EntityState:
    entity_state_id: StableId
    entity_state_digest: Digest
    entity_root_id: StableId
    entity_type: EntityType
    state_payload_fields: CanonicalFields
    allocation_key_digest: Digest

    def __post_init__(self) -> None:
        object.__setattr__(self, "entity_type", _enum(EntityType, self.entity_type, "entity type"))
        _require_stable_id(self.entity_state_id, "entity state ID", kind="entity_state")
        _require_stable_id(self.entity_root_id, "entity root ID", kind="entity_root")
        _require_digest(self.entity_state_digest, "entity state digest")
        _require_digest(self.allocation_key_digest, "entity state allocation key digest")
        self.require_valid_identity()

    @classmethod
    def create(
        cls,
        *,
        root: EntityRoot,
        state_payload_fields: Mapping[str, object],
    ) -> "EntityState":
        if not isinstance(root, EntityRoot):
            _fail("ENTITY_ROOT_REQUIRED", "Entity State requires a typed EntityRoot")
        root.require_valid_identity()
        payload = _normalize_entity_state_payload(root.entity_type, state_payload_fields)
        state_digest = digest_of(
            [
                "ENTITY_STATE_PAYLOAD",
                root.entity_type.value,
                root.entity_root_id.value,
                payload,
            ]
        )
        allocation_key = digest_of(
            ["ENTITY_STATE", root.entity_root_id.value, state_digest.value]
        )
        return cls(
            entity_state_id=_stable("entity_state", allocation_key),
            entity_state_digest=state_digest,
            entity_root_id=root.entity_root_id,
            entity_type=root.entity_type,
            state_payload_fields=payload,
            allocation_key_digest=allocation_key,
        )

    @property
    def state_id(self) -> StableId:
        return self.entity_state_id

    @property
    def state_digest(self) -> Digest:
        return self.entity_state_digest

    @property
    def evidence_references(self) -> tuple[StableId, ...]:
        value = self.state_payload_fields["evidence_references"]
        assert isinstance(value, tuple)
        return tuple(StableId(_expect_string(item, "evidence reference")) for item in value)

    def require_valid_identity(self) -> None:
        expected_fields = _ENTITY_STATE_FIELDS[self.entity_type]
        if (
            self.entity_type is EntityType.JAVA_TYPE
            and set(self.state_payload_fields) == set(_JAVA_TYPE_SEMANTICS_STATE_FIELDS)
        ):
            expected_fields = _JAVA_TYPE_SEMANTICS_STATE_FIELDS
        elif (
            self.entity_type is EntityType.JAVA_METHOD
            and set(self.state_payload_fields)
            == set(_JAVA_METHOD_SEMANTICS_STATE_FIELDS)
        ):
            expected_fields = _JAVA_METHOD_SEMANTICS_STATE_FIELDS
        _require_exact_keys(
            self.state_payload_fields,
            expected_fields,
            f"{self.entity_type.value} state payload",
        )
        state_digest = digest_of(
            [
                "ENTITY_STATE_PAYLOAD",
                self.entity_type.value,
                self.entity_root_id.value,
                self.state_payload_fields,
            ]
        )
        allocation_key = digest_of(
            ["ENTITY_STATE", self.entity_root_id.value, state_digest.value]
        )
        if (
            state_digest != self.entity_state_digest
            or allocation_key != self.allocation_key_digest
            or self.entity_state_id != _stable("entity_state", allocation_key)
        ):
            _fail("ENTITY_STATE_IDENTITY_MISMATCH", "entity State identity is not canonical")


@dataclass(frozen=True, slots=True)
class RelationFactRoot:
    relation_root_id: StableId
    owning_scope_id: StableId
    schema_ref: str
    subject: EntityRef
    predicate: RelationPredicate
    object: EntityRef
    observation_modality: ObservationModality
    allocation_key_digest: Digest

    def __post_init__(self) -> None:
        object.__setattr__(self, "predicate", _enum(RelationPredicate, self.predicate, "relation predicate"))
        object.__setattr__(
            self,
            "observation_modality",
            _enum(ObservationModality, self.observation_modality, "observation modality"),
        )
        _require_stable_id(self.relation_root_id, "relation root ID", kind="relation_root")
        _require_stable_id(self.owning_scope_id, "relation owning scope ID")
        _require_digest(self.allocation_key_digest, "relation root allocation key digest")
        self.require_valid_identity()

    @classmethod
    def create(
        cls,
        *,
        owning_scope_id: StableId,
        subject: EntityRef,
        predicate: RelationPredicate | str,
        object: EntityRef,
        observation_modality: ObservationModality | str,
        schema_ref: str = MAVEN_STRUCTURE_SCHEMA_REF,
    ) -> "RelationFactRoot":
        _require_stable_id(owning_scope_id, "relation owning scope ID")
        if not isinstance(subject, EntityRef) or not isinstance(object, EntityRef):
            _fail(
                "RELATION_ENDPOINT_NOT_ENTITY_REF",
                "Relation Fact endpoints must both be typed EntityRef values",
            )
        normalized_predicate = _enum(RelationPredicate, predicate, "relation predicate")
        normalized_modality = _enum(
            ObservationModality, observation_modality, "observation modality"
        )
        normalized_schema_ref = _text(schema_ref, "schema ref")
        _validate_relation_shape(
            subject=subject,
            predicate=normalized_predicate,
            object=object,
            observation_modality=normalized_modality,
        )
        root_fields = CanonicalFields(
            {
                "owning_scope_id": owning_scope_id.value,
                "schema_ref": normalized_schema_ref,
                "subject_entity_root_id": subject.entity_root_id.value,
                "predicate": normalized_predicate.value,
                "object_entity_root_id": object.entity_root_id.value,
                "observation_modality": normalized_modality.value,
            }
        )
        allocation_key = digest_of(["RELATION_ROOT", root_fields])
        return cls(
            relation_root_id=_stable("relation_root", allocation_key),
            owning_scope_id=owning_scope_id,
            schema_ref=normalized_schema_ref,
            subject=subject,
            predicate=normalized_predicate,
            object=object,
            observation_modality=normalized_modality,
            allocation_key_digest=allocation_key,
        )

    @property
    def root_id(self) -> StableId:
        return self.relation_root_id

    @property
    def fact_kind(self) -> FactKind:
        return FactKind.RELATION

    @property
    def root_fields(self) -> CanonicalFields:
        return CanonicalFields(
            {
                "owning_scope_id": self.owning_scope_id.value,
                "schema_ref": self.schema_ref,
                "subject_entity_root_id": self.subject.entity_root_id.value,
                "predicate": self.predicate.value,
                "object_entity_root_id": self.object.entity_root_id.value,
                "observation_modality": self.observation_modality.value,
            }
        )

    def require_valid_identity(self) -> None:
        _validate_relation_shape(
            subject=self.subject,
            predicate=self.predicate,
            object=self.object,
            observation_modality=self.observation_modality,
        )
        allocation_key = digest_of(["RELATION_ROOT", self.root_fields])
        if allocation_key != self.allocation_key_digest or self.relation_root_id != _stable(
            "relation_root", allocation_key
        ):
            _fail("RELATION_ROOT_IDENTITY_MISMATCH", "Relation Fact Root identity is not canonical")


@dataclass(frozen=True, slots=True)
class RelationFactState:
    relation_state_id: StableId
    relation_state_digest: Digest
    relation_root_id: StableId
    subject_entity_state_id: StableId
    object_entity_state_id: StableId
    source_revision: str
    knowledge_context_digest: Digest
    evidence_references: tuple[StableId, ...]
    predicate_state_payload_fields: CanonicalFields
    allocation_key_digest: Digest

    def __post_init__(self) -> None:
        _require_stable_id(self.relation_state_id, "relation state ID", kind="relation_state")
        _require_stable_id(self.relation_root_id, "relation root ID", kind="relation_root")
        _require_stable_id(self.subject_entity_state_id, "relation subject State ID", kind="entity_state")
        _require_stable_id(self.object_entity_state_id, "relation object State ID", kind="entity_state")
        _require_digest(self.relation_state_digest, "relation state digest")
        _require_digest(self.knowledge_context_digest, "knowledge context digest")
        _require_digest(self.allocation_key_digest, "relation state allocation key digest")
        object.__setattr__(self, "source_revision", _text(self.source_revision, "source revision"))
        object.__setattr__(
            self,
            "evidence_references",
            _sorted_unique_stable_ids(self.evidence_references, "relation evidence reference"),
        )

    @classmethod
    def create(
        cls,
        *,
        root: RelationFactRoot,
        subject_state: EntityState,
        object_state: EntityState,
        source_revision: str,
        knowledge_context_digest: Digest,
        evidence_references: Sequence[StableId],
        predicate_state_payload_fields: Mapping[str, object],
    ) -> "RelationFactState":
        if not isinstance(root, RelationFactRoot):
            _fail("RELATION_ROOT_REQUIRED", "Relation Fact State requires a typed RelationFactRoot")
        if not isinstance(subject_state, EntityState) or not isinstance(object_state, EntityState):
            _fail("RELATION_ENDPOINT_STATE_REQUIRED", "Relation Fact State requires two typed EntityState values")
        _require_digest(knowledge_context_digest, "knowledge context digest")
        root.require_valid_identity()
        if subject_state.entity_root_id != root.subject.entity_root_id:
            _fail("SUBJECT_STATE_ROOT_MISMATCH", "relation subject State does not belong to its endpoint Root")
        if object_state.entity_root_id != root.object.entity_root_id:
            _fail("OBJECT_STATE_ROOT_MISMATCH", "relation object State does not belong to its endpoint Root")
        if subject_state.entity_type != root.subject.entity_type:
            _fail("SUBJECT_STATE_TYPE_MISMATCH", "relation subject State type does not match EntityRef")
        if object_state.entity_type != root.object.entity_type:
            _fail("OBJECT_STATE_TYPE_MISMATCH", "relation object State type does not match EntityRef")
        normalized_evidence = _sorted_unique_stable_ids(
            evidence_references, "relation evidence reference"
        )
        predicate_fields = _normalize_predicate_payload(
            root.predicate, predicate_state_payload_fields
        )
        common_fields = CanonicalFields(
            {
                "subject_entity_state_id": subject_state.entity_state_id.value,
                "object_entity_state_id": object_state.entity_state_id.value,
                "source_revision": _text(source_revision, "source revision"),
                "knowledge_context_digest": knowledge_context_digest.value,
                "evidence_references": tuple(item.value for item in normalized_evidence),
            }
        )
        state_digest = digest_of(
            [
                "RELATION_STATE_PAYLOAD",
                root.relation_root_id.value,
                common_fields,
                predicate_fields,
            ]
        )
        allocation_key = digest_of(
            ["RELATION_STATE", root.relation_root_id.value, state_digest.value]
        )
        return cls(
            relation_state_id=_stable("relation_state", allocation_key),
            relation_state_digest=state_digest,
            relation_root_id=root.relation_root_id,
            subject_entity_state_id=subject_state.entity_state_id,
            object_entity_state_id=object_state.entity_state_id,
            source_revision=_text(source_revision, "source revision"),
            knowledge_context_digest=knowledge_context_digest,
            evidence_references=normalized_evidence,
            predicate_state_payload_fields=predicate_fields,
            allocation_key_digest=allocation_key,
        )

    @property
    def state_id(self) -> StableId:
        return self.relation_state_id

    @property
    def state_digest(self) -> Digest:
        return self.relation_state_digest

    @property
    def state_payload_fields(self) -> CanonicalFields:
        return CanonicalFields(
            {
                "subject_entity_state_id": self.subject_entity_state_id.value,
                "object_entity_state_id": self.object_entity_state_id.value,
                "source_revision": self.source_revision,
                "knowledge_context_digest": self.knowledge_context_digest.value,
                "evidence_references": tuple(item.value for item in self.evidence_references),
            }
        )

    def require_valid_identity(self, root: RelationFactRoot) -> None:
        if self.relation_root_id != root.relation_root_id:
            _fail("RELATION_STATE_ROOT_MISMATCH", "Relation Fact State does not belong to its Root")
        _require_exact_keys(
            self.state_payload_fields, _RELATION_STATE_FIELDS, "relation state payload"
        )
        _require_exact_keys(
            self.predicate_state_payload_fields,
            _PREDICATE_STATE_FIELDS[root.predicate],
            f"{root.predicate.value} state payload",
        )
        state_digest = digest_of(
            [
                "RELATION_STATE_PAYLOAD",
                self.relation_root_id.value,
                self.state_payload_fields,
                self.predicate_state_payload_fields,
            ]
        )
        allocation_key = digest_of(
            ["RELATION_STATE", self.relation_root_id.value, state_digest.value]
        )
        if (
            state_digest != self.relation_state_digest
            or allocation_key != self.allocation_key_digest
            or self.relation_state_id != _stable("relation_state", allocation_key)
        ):
            _fail("RELATION_STATE_IDENTITY_MISMATCH", "Relation Fact State identity is not canonical")


@dataclass(frozen=True, slots=True)
class LiteralObject:
    literal_type: LiteralType
    value: bool | int | str

    def __post_init__(self) -> None:
        object.__setattr__(self, "literal_type", _enum(LiteralType, self.literal_type, "literal type"))
        expected: type[object]
        if self.literal_type is LiteralType.BOOLEAN:
            expected = bool
        elif self.literal_type is LiteralType.INTEGER:
            expected = int
        else:
            expected = str
        if type(self.value) is not expected:
            _fail("LITERAL_TYPE_MISMATCH", "literal value does not match its declared type")
        if isinstance(self.value, str):
            object.__setattr__(self, "value", _canonical_text(self.value, "literal string"))

    def canonical_value(self) -> dict[str, bool | int | str]:
        return {"literal_type": self.literal_type.value, "value": self.value}


@dataclass(frozen=True, slots=True)
class LiteralFactRoot:
    literal_root_id: StableId
    owning_scope_id: StableId
    schema_ref: str
    subject: EntityRef
    predicate: str
    object: LiteralObject
    observation_modality: str
    allocation_key_digest: Digest

    def __post_init__(self) -> None:
        _require_stable_id(self.literal_root_id, "literal root ID", kind="literal_root")
        _require_stable_id(self.owning_scope_id, "literal owning scope ID")
        if not isinstance(self.subject, EntityRef) or not isinstance(self.object, LiteralObject):
            _fail("LITERAL_FACT_SHAPE_INVALID", "Literal Fact requires an EntityRef subject and typed literal object")
        _require_digest(self.allocation_key_digest, "literal root allocation key digest")
        self.require_valid_identity()

    @classmethod
    def create(
        cls,
        *,
        owning_scope_id: StableId,
        schema_ref: str,
        subject: EntityRef,
        predicate: str,
        object: LiteralObject,
        observation_modality: str,
    ) -> "LiteralFactRoot":
        _require_stable_id(owning_scope_id, "literal owning scope ID")
        if not isinstance(subject, EntityRef) or not isinstance(object, LiteralObject):
            _fail("LITERAL_FACT_SHAPE_INVALID", "Literal Fact cannot use a relation endpoint as its object")
        normalized_schema = _text(schema_ref, "schema ref")
        normalized_predicate = _text(predicate, "literal predicate")
        normalized_modality = _text(observation_modality, "observation modality")
        root_fields = CanonicalFields(
            {
                "owning_scope_id": owning_scope_id.value,
                "schema_ref": normalized_schema,
                "subject_entity_root_id": subject.entity_root_id.value,
                "predicate": normalized_predicate,
                "literal_object": object.canonical_value(),
                "observation_modality": normalized_modality,
            }
        )
        allocation_key = digest_of(["LITERAL_ROOT", root_fields])
        return cls(
            literal_root_id=_stable("literal_root", allocation_key),
            owning_scope_id=owning_scope_id,
            schema_ref=normalized_schema,
            subject=subject,
            predicate=normalized_predicate,
            object=object,
            observation_modality=normalized_modality,
            allocation_key_digest=allocation_key,
        )

    @property
    def root_id(self) -> StableId:
        return self.literal_root_id

    @property
    def fact_kind(self) -> FactKind:
        return FactKind.LITERAL

    @property
    def root_fields(self) -> CanonicalFields:
        return CanonicalFields(
            {
                "owning_scope_id": self.owning_scope_id.value,
                "schema_ref": self.schema_ref,
                "subject_entity_root_id": self.subject.entity_root_id.value,
                "predicate": self.predicate,
                "literal_object": self.object.canonical_value(),
                "observation_modality": self.observation_modality,
            }
        )

    def require_valid_identity(self) -> None:
        allocation_key = digest_of(["LITERAL_ROOT", self.root_fields])
        if allocation_key != self.allocation_key_digest or self.literal_root_id != _stable(
            "literal_root", allocation_key
        ):
            _fail("LITERAL_ROOT_IDENTITY_MISMATCH", "Literal Fact Root identity is not canonical")


@dataclass(frozen=True, slots=True)
class LiteralFactState:
    literal_state_id: StableId
    literal_state_digest: Digest
    literal_root_id: StableId
    subject_entity_state_id: StableId
    source_revision: str
    knowledge_context_digest: Digest
    evidence_references: tuple[StableId, ...]
    allocation_key_digest: Digest

    def __post_init__(self) -> None:
        _require_stable_id(self.literal_state_id, "literal state ID", kind="literal_state")
        _require_stable_id(self.literal_root_id, "literal root ID", kind="literal_root")
        _require_stable_id(self.subject_entity_state_id, "literal subject State ID", kind="entity_state")
        _require_digest(self.literal_state_digest, "literal state digest")
        _require_digest(self.knowledge_context_digest, "literal knowledge context digest")
        _require_digest(self.allocation_key_digest, "literal state allocation key digest")
        object.__setattr__(self, "source_revision", _text(self.source_revision, "source revision"))
        object.__setattr__(
            self,
            "evidence_references",
            _sorted_unique_stable_ids(self.evidence_references, "literal evidence reference"),
        )

    @classmethod
    def create(
        cls,
        *,
        root: LiteralFactRoot,
        subject_state: EntityState,
        source_revision: str,
        knowledge_context_digest: Digest,
        evidence_references: Sequence[StableId],
    ) -> "LiteralFactState":
        if not isinstance(root, LiteralFactRoot):
            _fail("LITERAL_ROOT_REQUIRED", "Literal Fact State requires a typed LiteralFactRoot")
        if not isinstance(subject_state, EntityState):
            _fail("LITERAL_SUBJECT_STATE_REQUIRED", "Literal Fact State requires a typed EntityState subject")
        _require_digest(knowledge_context_digest, "literal knowledge context digest")
        if subject_state.entity_root_id != root.subject.entity_root_id:
            _fail("SUBJECT_STATE_ROOT_MISMATCH", "literal subject State does not belong to its endpoint Root")
        normalized_evidence = _sorted_unique_stable_ids(
            evidence_references, "literal evidence reference"
        )
        payload = CanonicalFields(
            {
                "subject_entity_state_id": subject_state.entity_state_id.value,
                "source_revision": _text(source_revision, "source revision"),
                "knowledge_context_digest": knowledge_context_digest.value,
                "evidence_references": tuple(item.value for item in normalized_evidence),
            }
        )
        state_digest = digest_of(
            ["LITERAL_STATE_PAYLOAD", root.literal_root_id.value, payload]
        )
        allocation_key = digest_of(
            ["LITERAL_STATE", root.literal_root_id.value, state_digest.value]
        )
        return cls(
            literal_state_id=_stable("literal_state", allocation_key),
            literal_state_digest=state_digest,
            literal_root_id=root.literal_root_id,
            subject_entity_state_id=subject_state.entity_state_id,
            source_revision=_text(source_revision, "source revision"),
            knowledge_context_digest=knowledge_context_digest,
            evidence_references=normalized_evidence,
            allocation_key_digest=allocation_key,
        )

    @property
    def state_id(self) -> StableId:
        return self.literal_state_id

    @property
    def state_digest(self) -> Digest:
        return self.literal_state_digest

    @property
    def state_payload_fields(self) -> CanonicalFields:
        return CanonicalFields(
            {
                "subject_entity_state_id": self.subject_entity_state_id.value,
                "source_revision": self.source_revision,
                "knowledge_context_digest": self.knowledge_context_digest.value,
                "evidence_references": tuple(item.value for item in self.evidence_references),
            }
        )

    def require_valid_identity(self, root: LiteralFactRoot) -> None:
        if self.literal_root_id != root.literal_root_id:
            _fail("LITERAL_STATE_ROOT_MISMATCH", "Literal Fact State does not belong to its Root")
        state_digest = digest_of(
            ["LITERAL_STATE_PAYLOAD", self.literal_root_id.value, self.state_payload_fields]
        )
        allocation_key = digest_of(
            ["LITERAL_STATE", self.literal_root_id.value, state_digest.value]
        )
        if (
            state_digest != self.literal_state_digest
            or allocation_key != self.allocation_key_digest
            or self.literal_state_id != _stable("literal_state", allocation_key)
        ):
            _fail("LITERAL_STATE_IDENTITY_MISMATCH", "Literal Fact State identity is not canonical")


@dataclass(frozen=True, slots=True)
class CoverageMember:
    kind: CoverageMemberKind
    root_id: StableId
    state_id: StableId
    state_digest: Digest

    def __post_init__(self) -> None:
        object.__setattr__(self, "kind", _enum(CoverageMemberKind, self.kind, "coverage member kind"))
        _require_stable_id(self.root_id, "coverage member Root ID")
        _require_stable_id(self.state_id, "coverage member State ID")
        _require_digest(self.state_digest, "coverage member State digest")
        expected_kinds = {
            CoverageMemberKind.ENTITY: ("entity_root", "entity_state"),
            CoverageMemberKind.RELATION_FACT: ("relation_root", "relation_state"),
            CoverageMemberKind.LITERAL_FACT: ("literal_root", "literal_state"),
        }
        root_kind, state_kind = expected_kinds[self.kind]
        if self.root_id.kind != root_kind or self.state_id.kind != state_kind:
            _fail("COVERAGE_MEMBER_KIND_MISMATCH", "coverage member IDs do not match its typed kind")

    def canonical_value(self) -> dict[str, str]:
        return {
            "kind": self.kind.value,
            "root_id": self.root_id.value,
            "state_id": self.state_id.value,
            "state_digest": self.state_digest.value,
        }


@dataclass(frozen=True, slots=True)
class CompleteMemberManifest:
    members: tuple[CoverageMember, ...]
    digest: Digest
    completeness: CoverageCompleteness = CoverageCompleteness.COMPLETE

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "completeness",
            _enum(CoverageCompleteness, self.completeness, "coverage completeness"),
        )
        normalized = _sorted_members(self.members)
        if normalized != self.members:
            _fail("MEMBER_MANIFEST_NOT_CANONICAL", "complete member Manifest must be sorted")
        if len({member.root_id for member in self.members}) != len(self.members):
            _fail("MULTIPLE_STATES_FOR_ROOT", "complete member Manifest has more than one State for a Root")
        expected = digest_of(["COMPLETE_MEMBER_MANIFEST", self.canonical_value()])
        if self.digest != expected:
            _fail("MEMBER_MANIFEST_DIGEST_MISMATCH", "complete member Manifest digest is not canonical")

    @classmethod
    def create(cls, members: Sequence[CoverageMember]) -> "CompleteMemberManifest":
        normalized = _sorted_members(members)
        value = {
            "completeness": CoverageCompleteness.COMPLETE.value,
            "members": tuple(member.canonical_value() for member in normalized),
        }
        return cls(
            members=normalized,
            digest=digest_of(["COMPLETE_MEMBER_MANIFEST", value]),
        )

    def canonical_value(self) -> dict[str, object]:
        return {
            "completeness": self.completeness.value,
            "members": tuple(member.canonical_value() for member in self.members),
        }


@dataclass(frozen=True, slots=True)
class CoverageRoot:
    coverage_root_id: StableId
    coverage_root_ref: str
    owning_scope_id: StableId
    profile_ref: str
    schema_ref: str
    schema_digest: Digest
    source_binding_id: StableId
    logical_reactor_root: str
    maven_evaluation_context_ref: str
    maven_evaluation_context_digest: Digest
    covered_entity_types: tuple[EntityType, ...]
    covered_relation_predicates: tuple[RelationPredicate, ...]
    canonicalization_ref: str
    canonicalization_digest: Digest
    allocation_key_digest: Digest

    def __post_init__(self) -> None:
        _require_stable_id(self.coverage_root_id, "coverage root ID", kind="coverage_root")
        _require_stable_id(self.owning_scope_id, "coverage owning scope ID")
        _require_stable_id(self.source_binding_id, "coverage source binding ID")
        _require_digest(self.schema_digest, "coverage schema digest")
        _require_digest(self.maven_evaluation_context_digest, "Maven evaluation context digest")
        _require_digest(self.canonicalization_digest, "canonicalization digest")
        _require_digest(self.allocation_key_digest, "coverage root allocation key digest")
        object.__setattr__(
            self,
            "covered_entity_types",
            _sorted_unique_enums(EntityType, self.covered_entity_types, "covered entity type"),
        )
        object.__setattr__(
            self,
            "covered_relation_predicates",
            _sorted_unique_enums(
                RelationPredicate,
                self.covered_relation_predicates,
                "covered relation predicate",
            ),
        )
        self.require_valid_identity()

    @classmethod
    def create(
        cls,
        *,
        owning_scope_id: StableId,
        source_binding_id: StableId,
        logical_reactor_root: str,
        profile_ref: str = MAVEN_STRUCTURE_PROFILE_REF,
        schema_ref: str = MAVEN_STRUCTURE_SCHEMA_REF,
        schema_digest: Digest = MAVEN_STRUCTURE_SCHEMA_DIGEST,
        maven_evaluation_context_ref: str = MAVEN_EVALUATION_CONTEXT_REF,
        maven_evaluation_context_digest: Digest = MAVEN_EVALUATION_CONTEXT_DIGEST,
        covered_entity_types: Sequence[EntityType | str] = (
            EntityType.SOFTWARE_SYSTEM,
            EntityType.MAVEN_MODULE,
        ),
        covered_relation_predicates: Sequence[RelationPredicate | str] = (
            RelationPredicate.CONTAINS_MODULE,
            RelationPredicate.DEPENDS_ON,
        ),
        canonicalization_ref: str = MAVEN_CANONICALIZATION_REF,
        canonicalization_digest: Digest = MAVEN_CANONICALIZATION_DIGEST,
        coverage_root_ref: str = MAVEN_STRUCTURE_COVERAGE_ROOT_REF,
    ) -> "CoverageRoot":
        normalized_types = _sorted_unique_enums(
            EntityType, covered_entity_types, "covered entity type"
        )
        normalized_predicates = _sorted_unique_enums(
            RelationPredicate,
            covered_relation_predicates,
            "covered relation predicate",
        )
        root_fields = _coverage_root_fields(
            owning_scope_id=owning_scope_id,
            profile_ref=profile_ref,
            schema_ref=schema_ref,
            schema_digest=schema_digest,
            source_binding_id=source_binding_id,
            logical_reactor_root=logical_reactor_root,
            maven_evaluation_context_ref=maven_evaluation_context_ref,
            maven_evaluation_context_digest=maven_evaluation_context_digest,
            covered_entity_types=normalized_types,
            covered_relation_predicates=normalized_predicates,
            canonicalization_ref=canonicalization_ref,
            canonicalization_digest=canonicalization_digest,
        )
        normalized_root_ref = _text(coverage_root_ref, "coverage root ref")
        allocation_key = digest_of(
            ["COVERAGE_ROOT", normalized_root_ref, root_fields]
        )
        return cls(
            coverage_root_id=_stable("coverage_root", allocation_key),
            coverage_root_ref=normalized_root_ref,
            owning_scope_id=owning_scope_id,
            profile_ref=_text(profile_ref, "profile ref"),
            schema_ref=_text(schema_ref, "schema ref"),
            schema_digest=schema_digest,
            source_binding_id=source_binding_id,
            logical_reactor_root=_text(logical_reactor_root, "logical reactor root"),
            maven_evaluation_context_ref=_text(
                maven_evaluation_context_ref, "Maven evaluation context ref"
            ),
            maven_evaluation_context_digest=maven_evaluation_context_digest,
            covered_entity_types=normalized_types,
            covered_relation_predicates=normalized_predicates,
            canonicalization_ref=_text(canonicalization_ref, "canonicalization ref"),
            canonicalization_digest=canonicalization_digest,
            allocation_key_digest=allocation_key,
        )

    @property
    def root_id(self) -> StableId:
        return self.coverage_root_id

    @property
    def root_fields(self) -> CanonicalFields:
        return _coverage_root_fields(
            owning_scope_id=self.owning_scope_id,
            profile_ref=self.profile_ref,
            schema_ref=self.schema_ref,
            schema_digest=self.schema_digest,
            source_binding_id=self.source_binding_id,
            logical_reactor_root=self.logical_reactor_root,
            maven_evaluation_context_ref=self.maven_evaluation_context_ref,
            maven_evaluation_context_digest=self.maven_evaluation_context_digest,
            covered_entity_types=self.covered_entity_types,
            covered_relation_predicates=self.covered_relation_predicates,
            canonicalization_ref=self.canonicalization_ref,
            canonicalization_digest=self.canonicalization_digest,
        )

    def require_valid_identity(self) -> None:
        _require_exact_keys(self.root_fields, _COVERAGE_ROOT_FIELDS, "coverage root")
        allocation_key = digest_of(
            ["COVERAGE_ROOT", self.coverage_root_ref, self.root_fields]
        )
        if allocation_key != self.allocation_key_digest or self.coverage_root_id != _stable(
            "coverage_root", allocation_key
        ):
            _fail("COVERAGE_ROOT_IDENTITY_MISMATCH", "Coverage Root identity is not canonical")


@dataclass(frozen=True, slots=True)
class CoverageState:
    coverage_state_id: StableId
    coverage_state_digest: Digest
    coverage_root_id: StableId
    source_revision: str
    knowledge_context_digest: Digest
    schema_ref: str
    schema_digest: Digest
    maven_evaluation_context_ref: str
    maven_evaluation_context_digest: Digest
    canonicalization_ref: str
    canonicalization_digest: Digest
    complete_member_manifest: CompleteMemberManifest
    evidence_references: tuple[StableId, ...]
    allocation_key_digest: Digest

    def __post_init__(self) -> None:
        _require_stable_id(self.coverage_state_id, "coverage state ID", kind="coverage_state")
        _require_stable_id(self.coverage_root_id, "coverage root ID", kind="coverage_root")
        _require_digest(self.coverage_state_digest, "coverage state digest")
        _require_digest(self.knowledge_context_digest, "coverage knowledge context digest")
        _require_digest(self.schema_digest, "coverage schema digest")
        _require_digest(self.maven_evaluation_context_digest, "Maven evaluation context digest")
        _require_digest(self.canonicalization_digest, "canonicalization digest")
        _require_digest(self.allocation_key_digest, "coverage state allocation key digest")
        object.__setattr__(self, "source_revision", _text(self.source_revision, "source revision"))
        object.__setattr__(
            self,
            "evidence_references",
            _sorted_unique_stable_ids(self.evidence_references, "coverage evidence reference"),
        )

    @classmethod
    def create(
        cls,
        *,
        root: CoverageRoot,
        source_revision: str,
        knowledge_context_digest: Digest,
        complete_member_manifest: CompleteMemberManifest,
        evidence_references: Sequence[StableId],
    ) -> "CoverageState":
        if not isinstance(root, CoverageRoot):
            _fail("COVERAGE_ROOT_REQUIRED", "Coverage State requires a typed CoverageRoot")
        _require_digest(knowledge_context_digest, "coverage knowledge context digest")
        root.require_valid_identity()
        if not isinstance(complete_member_manifest, CompleteMemberManifest):
            _fail("MEMBER_MANIFEST_INVALID", "Coverage State requires a complete member Manifest")
        normalized_evidence = _sorted_unique_stable_ids(
            evidence_references, "coverage evidence reference"
        )
        payload = _coverage_state_fields(
            source_revision=source_revision,
            knowledge_context_digest=knowledge_context_digest,
            schema_ref=root.schema_ref,
            schema_digest=root.schema_digest,
            maven_evaluation_context_ref=root.maven_evaluation_context_ref,
            maven_evaluation_context_digest=root.maven_evaluation_context_digest,
            canonicalization_ref=root.canonicalization_ref,
            canonicalization_digest=root.canonicalization_digest,
            complete_member_manifest=complete_member_manifest,
            evidence_references=normalized_evidence,
        )
        state_digest = digest_of(
            ["COVERAGE_STATE_PAYLOAD", root.coverage_root_id.value, payload]
        )
        allocation_key = digest_of(
            ["COVERAGE_STATE", root.coverage_root_id.value, state_digest.value]
        )
        return cls(
            coverage_state_id=_stable("coverage_state", allocation_key),
            coverage_state_digest=state_digest,
            coverage_root_id=root.coverage_root_id,
            source_revision=_text(source_revision, "source revision"),
            knowledge_context_digest=knowledge_context_digest,
            schema_ref=root.schema_ref,
            schema_digest=root.schema_digest,
            maven_evaluation_context_ref=root.maven_evaluation_context_ref,
            maven_evaluation_context_digest=root.maven_evaluation_context_digest,
            canonicalization_ref=root.canonicalization_ref,
            canonicalization_digest=root.canonicalization_digest,
            complete_member_manifest=complete_member_manifest,
            evidence_references=normalized_evidence,
            allocation_key_digest=allocation_key,
        )

    @property
    def state_id(self) -> StableId:
        return self.coverage_state_id

    @property
    def state_digest(self) -> Digest:
        return self.coverage_state_digest

    @property
    def state_payload_fields(self) -> CanonicalFields:
        return _coverage_state_fields(
            source_revision=self.source_revision,
            knowledge_context_digest=self.knowledge_context_digest,
            schema_ref=self.schema_ref,
            schema_digest=self.schema_digest,
            maven_evaluation_context_ref=self.maven_evaluation_context_ref,
            maven_evaluation_context_digest=self.maven_evaluation_context_digest,
            canonicalization_ref=self.canonicalization_ref,
            canonicalization_digest=self.canonicalization_digest,
            complete_member_manifest=self.complete_member_manifest,
            evidence_references=self.evidence_references,
        )

    def require_valid_identity(self, root: CoverageRoot) -> None:
        if self.coverage_root_id != root.coverage_root_id:
            _fail("COVERAGE_STATE_ROOT_MISMATCH", "Coverage State does not belong to its Root")
        definition_pairs = (
            (self.schema_ref, root.schema_ref),
            (self.schema_digest, root.schema_digest),
            (self.maven_evaluation_context_ref, root.maven_evaluation_context_ref),
            (self.maven_evaluation_context_digest, root.maven_evaluation_context_digest),
            (self.canonicalization_ref, root.canonicalization_ref),
            (self.canonicalization_digest, root.canonicalization_digest),
        )
        if any(actual != expected for actual, expected in definition_pairs):
            _fail("COVERAGE_DEFINITION_MISMATCH", "Coverage State Definition refs/digests differ from its Root")
        _require_exact_keys(self.state_payload_fields, _COVERAGE_STATE_FIELDS, "coverage state payload")
        state_digest = digest_of(
            ["COVERAGE_STATE_PAYLOAD", self.coverage_root_id.value, self.state_payload_fields]
        )
        allocation_key = digest_of(
            ["COVERAGE_STATE", self.coverage_root_id.value, state_digest.value]
        )
        if (
            state_digest != self.coverage_state_digest
            or allocation_key != self.allocation_key_digest
            or self.coverage_state_id != _stable("coverage_state", allocation_key)
        ):
            _fail("COVERAGE_STATE_IDENTITY_MISMATCH", "Coverage State identity is not canonical")


@dataclass(frozen=True, slots=True)
class EntityRecord:
    root: EntityRoot
    state: EntityState

    def __post_init__(self) -> None:
        self.root.require_valid_identity()
        self.state.require_valid_identity()
        if self.root.entity_root_id != self.state.entity_root_id or self.root.entity_type != self.state.entity_type:
            _fail("ENTITY_RECORD_ROOT_STATE_MISMATCH", "Entity Root and State do not belong together")
        _validate_java_semantic_entity_record(self.root, self.state)

    @property
    def root_id(self) -> StableId:
        return self.root.entity_root_id

    @property
    def state_id(self) -> StableId:
        return self.state.entity_state_id

    @property
    def state_digest(self) -> Digest:
        return self.state.entity_state_digest

    @property
    def coverage_member(self) -> CoverageMember:
        return CoverageMember(CoverageMemberKind.ENTITY, self.root_id, self.state_id, self.state_digest)


@dataclass(frozen=True, slots=True)
class RelationFactRecord:
    root: RelationFactRoot
    state: RelationFactState

    def __post_init__(self) -> None:
        self.root.require_valid_identity()
        self.state.require_valid_identity(self.root)

    @property
    def root_id(self) -> StableId:
        return self.root.relation_root_id

    @property
    def state_id(self) -> StableId:
        return self.state.relation_state_id

    @property
    def state_digest(self) -> Digest:
        return self.state.relation_state_digest

    @property
    def coverage_member(self) -> CoverageMember:
        return CoverageMember(CoverageMemberKind.RELATION_FACT, self.root_id, self.state_id, self.state_digest)


@dataclass(frozen=True, slots=True)
class LiteralFactRecord:
    root: LiteralFactRoot
    state: LiteralFactState

    def __post_init__(self) -> None:
        self.root.require_valid_identity()
        self.state.require_valid_identity(self.root)

    @property
    def root_id(self) -> StableId:
        return self.root.literal_root_id

    @property
    def state_id(self) -> StableId:
        return self.state.literal_state_id

    @property
    def state_digest(self) -> Digest:
        return self.state.literal_state_digest

    @property
    def coverage_member(self) -> CoverageMember:
        return CoverageMember(CoverageMemberKind.LITERAL_FACT, self.root_id, self.state_id, self.state_digest)


@dataclass(frozen=True, slots=True)
class CoverageRecord:
    root: CoverageRoot
    state: CoverageState

    def __post_init__(self) -> None:
        self.root.require_valid_identity()
        self.state.require_valid_identity(self.root)

    @property
    def root_id(self) -> StableId:
        return self.root.coverage_root_id

    @property
    def state_id(self) -> StableId:
        return self.state.coverage_state_id


@dataclass(frozen=True, slots=True)
class ExactUpstreamEntity:
    snapshot_id: StableId
    entity: EntityRecord

    def __post_init__(self) -> None:
        _require_stable_id(self.snapshot_id, "exact upstream Snapshot ID")


@dataclass(frozen=True, slots=True)
class StructureKnowledgeBatch:
    evidence: tuple[StructureEvidence, ...]
    entities: tuple[EntityRecord, ...]
    relation_facts: tuple[RelationFactRecord, ...]
    literal_facts: tuple[LiteralFactRecord, ...]
    coverage: CoverageRecord
    publication_mode: PublicationMode
    exact_upstream_entities: tuple[ExactUpstreamEntity, ...] = ()

    @classmethod
    def admit(
        cls,
        *,
        evidence: Sequence[StructureEvidence],
        entities: Sequence[EntityRecord],
        relation_facts: Sequence[RelationFactRecord],
        coverage: CoverageRecord,
        publication_mode: PublicationMode | str,
        literal_facts: Sequence[LiteralFactRecord] = (),
        exact_upstream_entities: Sequence[ExactUpstreamEntity] = (),
    ) -> "StructureKnowledgeBatch":
        batch = cls(
            evidence=tuple(evidence),
            entities=tuple(entities),
            relation_facts=tuple(relation_facts),
            literal_facts=tuple(literal_facts),
            coverage=coverage,
            publication_mode=_enum(PublicationMode, publication_mode, "publication mode"),
            exact_upstream_entities=tuple(exact_upstream_entities),
        )
        batch.require_admissible()
        return batch

    def require_admissible(self) -> None:
        self.coverage.root.require_valid_identity()
        self.coverage.state.require_valid_identity(self.coverage.root)
        if self.coverage.root.schema_ref == MAVEN_STRUCTURE_SCHEMA_REF:
            if self.coverage.root.profile_ref != MAVEN_STRUCTURE_PROFILE_REF:
                _fail("PROFILE_SCHEMA_MISMATCH", "Maven Structure Schema requires its exact Profile ref")
            if self.publication_mode is not PublicationMode.REPLACE_COVERAGE:
                _fail("PUBLICATION_MODE_MISMATCH", "Maven Structure complete Coverage requires REPLACE_COVERAGE")
            if self.literal_facts:
                _fail("LITERAL_FACT_NOT_ALLOWED", "Maven Structure Schema declares no Literal Fact kinds")
            exact_definitions = (
                (self.coverage.root.schema_digest, MAVEN_STRUCTURE_SCHEMA_DIGEST),
                (
                    self.coverage.root.maven_evaluation_context_ref,
                    MAVEN_EVALUATION_CONTEXT_REF,
                ),
                (
                    self.coverage.root.maven_evaluation_context_digest,
                    MAVEN_EVALUATION_CONTEXT_DIGEST,
                ),
                (self.coverage.root.canonicalization_ref, MAVEN_CANONICALIZATION_REF),
                (
                    self.coverage.root.canonicalization_digest,
                    MAVEN_CANONICALIZATION_DIGEST,
                ),
                (
                    self.coverage.root.coverage_root_ref,
                    MAVEN_STRUCTURE_COVERAGE_ROOT_REF,
                ),
            )
            if any(actual != expected for actual, expected in exact_definitions):
                _fail(
                    "FROZEN_DEFINITION_MISMATCH",
                    "Maven Structure Coverage must bind all frozen Definition refs and digests",
                )
            expected_types = tuple(
                sorted(
                    (EntityType.SOFTWARE_SYSTEM, EntityType.MAVEN_MODULE),
                    key=lambda item: item.value,
                )
            )
            expected_predicates = tuple(
                sorted(
                    (RelationPredicate.CONTAINS_MODULE, RelationPredicate.DEPENDS_ON),
                    key=lambda item: item.value,
                )
            )
            if self.coverage.root.covered_entity_types != expected_types or self.coverage.root.covered_relation_predicates != expected_predicates:
                _fail("INCOMPLETE_PROFILE_COVERAGE", "Maven Structure Coverage must declare all frozen types and predicates")
        elif self.coverage.root.profile_ref == MAVEN_STRUCTURE_PROFILE_REF:
            _fail(
                "PROFILE_SCHEMA_MISMATCH",
                "Maven Structure Profile requires its exact frozen Schema ref",
            )
        elif self.coverage.root.schema_ref == JAVA_STATIC_CALL_SCHEMA_REF:
            if self.coverage.root.profile_ref != JAVA_STATIC_CALL_PROFILE_REF:
                _fail(
                    "PROFILE_SCHEMA_MISMATCH",
                    "Java Static Call Schema requires its exact Profile ref",
                )
            if self.publication_mode is not PublicationMode.REPLACE_COVERAGE:
                _fail(
                    "PUBLICATION_MODE_MISMATCH",
                    "Java Static Call complete Coverage requires REPLACE_COVERAGE",
                )
            if self.literal_facts:
                _fail(
                    "LITERAL_FACT_NOT_ALLOWED",
                    "Java Static Call Schema declares no Literal Fact kinds",
                )
            exact_definitions = (
                (
                    self.coverage.root.schema_digest,
                    JAVA_STATIC_CALL_SCHEMA_DIGEST,
                ),
                (
                    self.coverage.root.maven_evaluation_context_ref,
                    JAVA_STATIC_CALL_EVALUATION_CONTEXT_REF,
                ),
                (
                    self.coverage.root.maven_evaluation_context_digest,
                    JAVA_STATIC_CALL_EVALUATION_CONTEXT_DIGEST,
                ),
                (
                    self.coverage.root.canonicalization_ref,
                    JAVA_STATIC_CALL_CANONICALIZATION_REF,
                ),
                (
                    self.coverage.root.canonicalization_digest,
                    JAVA_STATIC_CALL_CANONICALIZATION_DIGEST,
                ),
                (
                    self.coverage.root.coverage_root_ref,
                    JAVA_STATIC_CALL_COVERAGE_ROOT_REF,
                ),
            )
            if any(actual != expected for actual, expected in exact_definitions):
                _fail(
                    "FROZEN_DEFINITION_MISMATCH",
                    "Java Static Call Coverage must bind all frozen Definition refs and digests",
                )
            expected_types = tuple(
                sorted(
                    (EntityType.JAVA_TYPE, EntityType.JAVA_METHOD),
                    key=lambda item: item.value,
                )
            )
            expected_predicates = tuple(
                sorted(
                    (RelationPredicate.DECLARES_METHOD, RelationPredicate.CALLS),
                    key=lambda item: item.value,
                )
            )
            if (
                self.coverage.root.covered_entity_types != expected_types
                or self.coverage.root.covered_relation_predicates
                != expected_predicates
            ):
                _fail(
                    "INCOMPLETE_PROFILE_COVERAGE",
                    "Java Static Call Coverage must declare all frozen types and predicates",
                )
        elif self.coverage.root.profile_ref == JAVA_STATIC_CALL_PROFILE_REF:
            _fail(
                "PROFILE_SCHEMA_MISMATCH",
                "Java Static Call Profile requires its exact frozen Schema ref",
            )
        elif self.coverage.root.schema_ref == JAVA_SOURCE_SEMANTICS_SCHEMA_REF:
            if self.coverage.root.profile_ref != JAVA_SOURCE_SEMANTICS_PROFILE_REF:
                _fail(
                    "PROFILE_SCHEMA_MISMATCH",
                    "Java Source Semantics Schema requires its exact Profile ref",
                )
            if self.publication_mode is not PublicationMode.REPLACE_COVERAGE:
                _fail(
                    "PUBLICATION_MODE_MISMATCH",
                    "Java Source Semantics complete Coverage requires REPLACE_COVERAGE",
                )
            if self.literal_facts:
                _fail(
                    "LITERAL_FACT_NOT_ALLOWED",
                    "Java Source Semantics stores typed semantics in Entity States",
                )
            exact_definitions = (
                (
                    self.coverage.root.schema_digest,
                    JAVA_SOURCE_SEMANTICS_SCHEMA_DIGEST,
                ),
                (
                    self.coverage.root.maven_evaluation_context_ref,
                    JAVA_SOURCE_SEMANTICS_EVALUATION_CONTEXT_REF,
                ),
                (
                    self.coverage.root.maven_evaluation_context_digest,
                    JAVA_SOURCE_SEMANTICS_EVALUATION_CONTEXT_DIGEST,
                ),
                (
                    self.coverage.root.canonicalization_ref,
                    JAVA_SOURCE_SEMANTICS_CANONICALIZATION_REF,
                ),
                (
                    self.coverage.root.canonicalization_digest,
                    JAVA_SOURCE_SEMANTICS_CANONICALIZATION_DIGEST,
                ),
                (
                    self.coverage.root.coverage_root_ref,
                    JAVA_SOURCE_SEMANTICS_COVERAGE_ROOT_REF,
                ),
            )
            if any(actual != expected for actual, expected in exact_definitions):
                _fail(
                    "FROZEN_DEFINITION_MISMATCH",
                    "Java Source Semantics Coverage must bind all frozen definitions",
                )
            if (
                self.coverage.root.covered_entity_types
                != JAVA_SOURCE_SEMANTICS_ENTITY_TYPES
                or self.coverage.root.covered_relation_predicates
                != JAVA_SOURCE_SEMANTICS_RELATION_PREDICATES
            ):
                _fail(
                    "INCOMPLETE_PROFILE_COVERAGE",
                    "Java Source Semantics Coverage must declare its entire schema",
                )
        elif self.coverage.root.profile_ref == JAVA_SOURCE_SEMANTICS_PROFILE_REF:
            _fail(
                "PROFILE_SCHEMA_MISMATCH",
                "Java Source Semantics Profile requires its exact frozen Schema ref",
            )

        _require_unique_records(self.entities, "Entity")
        _require_unique_records(self.relation_facts, "Relation Fact")
        _require_unique_records(self.literal_facts, "Literal Fact")
        evidence_by_id: dict[StableId, StructureEvidence] = {}
        for evidence in self.evidence:
            evidence.require_valid_identity()
            if evidence.evidence_id in evidence_by_id:
                _fail("DUPLICATE_EVIDENCE", "structure closure contains duplicate Evidence")
            evidence_by_id[evidence.evidence_id] = evidence

        local_by_root = {record.root_id: record for record in self.entities}
        candidates: dict[StableId, list[EntityRecord]] = {
            root_id: [record] for root_id, record in local_by_root.items()
        }
        for upstream in self.exact_upstream_entities:
            candidates.setdefault(upstream.entity.root_id, []).append(upstream.entity)

        for fact in self.relation_facts:
            if fact.root.owning_scope_id != self.coverage.root.owning_scope_id:
                _fail("FACT_SCOPE_MISMATCH", "Relation Fact and Coverage must have one owning Scope")
            if fact.root.schema_ref != self.coverage.root.schema_ref:
                _fail("FACT_SCHEMA_MISMATCH", "Relation Fact and Coverage must use one exact Schema")
            subject = _resolve_endpoint(fact.root.subject, candidates, "subject")
            object_record = _resolve_endpoint(fact.root.object, candidates, "object")
            if fact.state.subject_entity_state_id != subject.state_id:
                _fail("DANGLING_SUBJECT_STATE", "Relation Fact subject State is outside the exact endpoint closure")
            if fact.state.object_entity_state_id != object_record.state_id:
                _fail("DANGLING_OBJECT_STATE", "Relation Fact object State is outside the exact endpoint closure")

        for fact in self.literal_facts:
            if fact.root.owning_scope_id != self.coverage.root.owning_scope_id:
                _fail("FACT_SCOPE_MISMATCH", "Literal Fact and Coverage must have one owning Scope")
            if fact.root.schema_ref != self.coverage.root.schema_ref:
                _fail("FACT_SCHEMA_MISMATCH", "Literal Fact and Coverage must use one exact Schema")
            subject = _resolve_endpoint(fact.root.subject, candidates, "literal subject")
            if fact.state.subject_entity_state_id != subject.state_id:
                _fail("DANGLING_SUBJECT_STATE", "Literal Fact subject State is outside the exact endpoint closure")

        if self.coverage.root.profile_ref == JAVA_SOURCE_SEMANTICS_PROFILE_REF:
            _validate_java_source_semantics_closure(
                entities=self.entities,
                relation_facts=self.relation_facts,
            )

        actual_members = CompleteMemberManifest.create(
            tuple(record.coverage_member for record in self.entities)
            + tuple(record.coverage_member for record in self.relation_facts)
            + tuple(record.coverage_member for record in self.literal_facts)
        )
        declared = self.coverage.state.complete_member_manifest
        actual_member_set = set(actual_members.members)
        declared_member_set = set(declared.members)
        if self.publication_mode is PublicationMode.REPLACE_COVERAGE:
            valid_manifest = declared_member_set == actual_member_set
        else:
            # Additional members represent exact inherited base States.  The
            # transactional Publisher must verify them against expected CURRENT.
            valid_manifest = actual_member_set <= declared_member_set
        if not valid_manifest:
            _fail("COVERAGE_MANIFEST_MISMATCH", "Coverage member Manifest does not cover the admitted local closure for its mode")
        for entity in self.entities:
            if entity.root.owning_scope_id != self.coverage.root.owning_scope_id:
                _fail("ENTITY_SCOPE_MISMATCH", "Entity and Coverage must have one owning Scope")
            if entity.root.entity_type not in self.coverage.root.covered_entity_types:
                _fail("ENTITY_TYPE_OUTSIDE_COVERAGE", "Entity type is outside declared Coverage")
        for fact in self.relation_facts:
            if fact.root.predicate not in self.coverage.root.covered_relation_predicates:
                _fail("PREDICATE_OUTSIDE_COVERAGE", "Relation predicate is outside declared Coverage")

        referenced_evidence: set[StableId] = set(self.coverage.state.evidence_references)
        for entity in self.entities:
            if not entity.state.evidence_references:
                _fail("ENTITY_EVIDENCE_MISSING", "source-backed Entity State requires direct Evidence")
            referenced_evidence.update(entity.state.evidence_references)
        for fact in self.relation_facts:
            if not fact.state.evidence_references:
                _fail("FACT_EVIDENCE_MISSING", "Relation Fact State requires direct Evidence")
            referenced_evidence.update(fact.state.evidence_references)
        for fact in self.literal_facts:
            if not fact.state.evidence_references:
                _fail("FACT_EVIDENCE_MISSING", "Literal Fact State requires direct Evidence")
            referenced_evidence.update(fact.state.evidence_references)
        if not self.coverage.state.evidence_references:
            _fail("COVERAGE_EVIDENCE_MISSING", "complete Coverage State requires direct Evidence")
        missing_evidence = referenced_evidence - set(evidence_by_id)
        if missing_evidence:
            _fail(
                "EVIDENCE_REFERENCE_DANGLING",
                "State Evidence refs must resolve inside the admitted Evidence closure",
                evidence_id=sorted(item.value for item in missing_evidence)[0],
            )
        unused_evidence = set(evidence_by_id) - referenced_evidence
        if unused_evidence:
            _fail(
                "UNREFERENCED_EVIDENCE",
                "admitted Evidence closure cannot contain unused payloads",
                evidence_id=sorted(item.value for item in unused_evidence)[0],
            )


RootStateRecord: TypeAlias = EntityRecord | RelationFactRecord | LiteralFactRecord | CoverageRecord


def compare_root_state(left: RootStateRecord, right: RootStateRecord) -> RootStateIdentity:
    """Classify two records without conflating a stable Root with its State."""

    if type(left) is not type(right) or left.root_id != right.root_id:
        return RootStateIdentity.DIFFERENT_ROOT
    if left.state_id == right.state_id:
        return RootStateIdentity.SAME_ROOT_SAME_STATE
    return RootStateIdentity.SAME_ROOT_DIFFERENT_STATE


def _validate_java_source_semantics_closure(
    *,
    entities: Sequence[EntityRecord],
    relation_facts: Sequence[RelationFactRecord],
) -> None:
    by_root = {item.root_id: item for item in entities}
    source_paths = {
        str(item.root.root_fields["source_path"])
        for item in entities
        if item.root.entity_type is EntityType.JAVA_SOURCE_FILE
    }
    methods = {
        item.root_id: item
        for item in entities
        if item.root.entity_type is EntityType.JAVA_METHOD
    }
    atoms = {
        item.root_id: item
        for item in entities
        if item.root.entity_type is EntityType.JAVA_IMPLEMENTATION_ATOM
    }
    for entity in entities:
        state_fields = set(entity.state.state_payload_fields)
        if entity.root.entity_type is EntityType.JAVA_TYPE:
            if state_fields != set(_JAVA_TYPE_SEMANTICS_STATE_FIELDS):
                _fail(
                    "JAVA_DISPOSITION_MANIFEST_INCOMPLETE",
                    "Java Source Semantics requires a disposition on every type",
                )
            if entity.state.state_payload_fields["source_path"] not in source_paths:
                _fail(
                    "JAVA_SOURCE_FILE_MANIFEST_INCOMPLETE",
                    "Every Java type must resolve to one covered source file",
                )
        elif entity.root.entity_type is EntityType.JAVA_METHOD:
            if state_fields != set(_JAVA_METHOD_SEMANTICS_STATE_FIELDS):
                _fail(
                    "JAVA_DISPOSITION_MANIFEST_INCOMPLETE",
                    "Java Source Semantics requires disposition and facet completeness on every method",
                )
            if entity.state.state_payload_fields["source_path"] not in source_paths:
                _fail(
                    "JAVA_SOURCE_FILE_MANIFEST_INCOMPLETE",
                    "Every Java method must resolve to one covered source file",
                )
        elif entity.root.entity_type is EntityType.JAVA_IMPLEMENTATION_ATOM:
            method_id = StableId(
                str(entity.root.root_fields["method_entity_root_id"])
            )
            if method_id not in methods:
                _fail(
                    "JAVA_ATOM_METHOD_DANGLING",
                    "Java implementation Atom must belong to one covered method",
                )
            referenced = {
                StableId(str(value))
                for value in entity.state.state_payload_fields[
                    "referenced_entity_root_ids"
                ]
            }
            if not referenced <= set(by_root):
                _fail(
                    "JAVA_ATOM_ENTITY_REF_DANGLING",
                    "Java Atom referenced Entity Roots must resolve in the exact closure",
                )
            operand_refs = {
                StableId(str(operand["value"]))
                for operand in entity.state.state_payload_fields["semantic_operands"]
                if operand["kind"] == JavaSemanticOperandKind.ENTITY_REF.value
            }
            if operand_refs != referenced:
                _fail(
                    "JAVA_ATOM_ENTITY_REF_MISMATCH",
                    "Java Atom typed operands and referenced Entity Roots must match",
                )
        elif entity.root.entity_type is EntityType.JAVA_STATE_SLOT:
            declaring_id = StableId(
                str(entity.root.root_fields["declaring_entity_root_id"])
            )
            declaring = by_root.get(declaring_id)
            if declaring is None or declaring.root.entity_type not in {
                EntityType.JAVA_TYPE,
                EntityType.JAVA_METHOD,
            }:
                _fail(
                    "JAVA_SLOT_DECLARATION_DANGLING",
                    "Java state slot must belong to one covered type or method",
                )

    membership: dict[StableId, RelationFactRecord] = {}
    next_pairs: set[tuple[StableId, StableId]] = set()
    call_targets: set[StableId] = set()
    declarations: set[StableId] = set()
    for relation in relation_facts:
        predicate = relation.root.predicate
        if predicate is RelationPredicate.HAS_IMPLEMENTATION_ATOM:
            atom_id = relation.root.object.entity_root_id
            if atom_id in membership:
                _fail(
                    "JAVA_ATOM_MEMBERSHIP_DUPLICATE",
                    "Each Java implementation Atom must have exactly one method membership",
                )
            atom = atoms[atom_id]
            expected_method = StableId(
                str(atom.root.root_fields["method_entity_root_id"])
            )
            if relation.root.subject.entity_root_id != expected_method:
                _fail(
                    "JAVA_ATOM_MEMBERSHIP_MISMATCH",
                    "Java Atom membership method differs from its Root identity",
                )
            if relation.state.predicate_state_payload_fields[
                "source_order_ordinal"
            ] != atom.state.state_payload_fields["source_order_ordinal"]:
                _fail(
                    "JAVA_ATOM_MEMBERSHIP_ORDINAL_MISMATCH",
                    "Java Atom membership ordinal differs from its State",
                )
            membership[atom_id] = relation
        elif predicate is RelationPredicate.NEXT_IN_SOURCE:
            next_pairs.add(
                (
                    relation.root.subject.entity_root_id,
                    relation.root.object.entity_root_id,
                )
            )
        elif predicate is RelationPredicate.CALL_SITE_TARGETS:
            subject = atoms[relation.root.subject.entity_root_id]
            if subject.root.root_fields["atom_kind"] != JavaImplementationAtomKind.CALL_SITE.value:
                _fail(
                    "JAVA_CALL_TARGET_SUBJECT_INVALID",
                    "CALL_SITE_TARGETS subject must be a CALL_SITE Atom",
                )
            call_targets.add(subject.root_id)
        elif predicate is RelationPredicate.DECLARES_METHOD:
            declarations.add(relation.root.object.entity_root_id)
        elif predicate is RelationPredicate.CONTROLS:
            subject = atoms[relation.root.subject.entity_root_id]
            if subject.root.root_fields["atom_kind"] != JavaImplementationAtomKind.BRANCH.value:
                _fail(
                    "JAVA_CONTROL_SUBJECT_INVALID",
                    "CONTROLS subject must be a BRANCH Atom",
                )

    if set(membership) != set(atoms):
        _fail(
            "JAVA_ATOM_MEMBERSHIP_INCOMPLETE",
            "Every Java implementation Atom requires exactly one method membership",
        )
    if declarations != set(methods):
        _fail(
            "JAVA_METHOD_DECLARATION_INCOMPLETE",
            "Every Java method requires exactly one type declaration relation",
        )
    for method_id in methods:
        ordered = sorted(
            (
                item.state.state_payload_fields["source_order_ordinal"],
                item.root_id,
            )
            for item in atoms.values()
            if item.root.root_fields["method_entity_root_id"] == method_id.value
        )
        if [ordinal for ordinal, _ in ordered] != list(range(len(ordered))):
            _fail(
                "JAVA_ATOM_SOURCE_ORDER_INCOMPLETE",
                "Java method Atom ordinals must be contiguous from zero",
            )
        expected_pairs = set(zip(
            (root_id for _, root_id in ordered),
            (root_id for _, root_id in ordered[1:]),
        ))
        actual_pairs = {
            pair
            for pair in next_pairs
            if StableId(
                str(atoms[pair[0]].root.root_fields["method_entity_root_id"])
            ) == method_id
        }
        if actual_pairs != expected_pairs:
            _fail(
                "JAVA_ATOM_SOURCE_ORDER_RELATIONS_INCOMPLETE",
                "NEXT_IN_SOURCE must cover every adjacent Atom pair exactly",
            )
    expected_call_targets = {
        item.root_id
        for item in atoms.values()
        if item.root.root_fields["atom_kind"]
        == JavaImplementationAtomKind.CALL_SITE.value
    }
    if call_targets != expected_call_targets:
        _fail(
            "JAVA_CALL_TARGET_RELATIONS_INCOMPLETE",
            "Every supported CALL_SITE Atom requires one target relation",
        )


def _resolve_endpoint(
    ref: EntityRef,
    candidates: Mapping[StableId, Sequence[EntityRecord]],
    label: str,
) -> EntityRecord:
    matches = candidates.get(ref.entity_root_id, ())
    if not matches:
        _fail("DANGLING_RELATION_ENDPOINT", f"Relation Fact {label} EntityRef is not in the exact closure")
    if len(matches) != 1:
        _fail("AMBIGUOUS_RELATION_ENDPOINT", f"Relation Fact {label} EntityRef resolves to multiple exact States")
    match = matches[0]
    if match.root.entity_type != ref.entity_type or match.root.owning_scope_id != ref.owning_scope_id:
        _fail("RELATION_ENDPOINT_TYPE_MISMATCH", f"Relation Fact {label} EntityRef metadata does not match its Root")
    return match


def _require_unique_records(records: Sequence[RootStateRecord], label: str) -> None:
    by_root: dict[StableId, list[StableId]] = {}
    for record in records:
        by_root.setdefault(record.root_id, []).append(record.state_id)
    for states in by_root.values():
        if len(set(states)) > 1:
            _fail("MULTIPLE_STATES_FOR_ROOT", f"{label} closure contains different States for one Root")
        if len(states) > 1:
            _fail("DUPLICATE_ROOT", f"{label} closure contains a duplicate Root")


def _validate_relation_shape(
    *,
    subject: EntityRef,
    predicate: RelationPredicate,
    object: EntityRef,
    observation_modality: ObservationModality,
) -> None:
    if predicate is RelationPredicate.CONTAINS_MODULE:
        valid = (
            subject.entity_type is EntityType.SOFTWARE_SYSTEM
            and object.entity_type is EntityType.MAVEN_MODULE
            and observation_modality is ObservationModality.RECURSIVE_REACTOR_MEMBERSHIP
        )
    elif predicate is RelationPredicate.DEPENDS_ON:
        valid = (
            subject.entity_type in (EntityType.SOFTWARE_SYSTEM, EntityType.MAVEN_MODULE)
            and object.entity_type is EntityType.MAVEN_MODULE
            and observation_modality
            is ObservationModality.POM_LOCAL_DECLARED_INTERNAL_DEPENDENCY
        )
    elif predicate is RelationPredicate.DECLARES_METHOD:
        valid = (
            subject.entity_type is EntityType.JAVA_TYPE
            and object.entity_type is EntityType.JAVA_METHOD
            and observation_modality
            is ObservationModality.JAVA_SOURCE_DECLARATION
        )
    elif predicate is RelationPredicate.CALLS:
        valid = (
            subject.entity_type is EntityType.JAVA_METHOD
            and object.entity_type is EntityType.JAVA_METHOD
            and observation_modality is ObservationModality.JAVA_SOURCE_STATIC_CALL
        )
    elif predicate is RelationPredicate.HAS_IMPLEMENTATION_ATOM:
        valid = (
            subject.entity_type is EntityType.JAVA_METHOD
            and object.entity_type is EntityType.JAVA_IMPLEMENTATION_ATOM
            and observation_modality
            is ObservationModality.JAVA_SOURCE_IMPLEMENTATION_MEMBERSHIP
        )
    elif predicate is RelationPredicate.CONTROLS:
        valid = (
            subject.entity_type is EntityType.JAVA_IMPLEMENTATION_ATOM
            and object.entity_type is EntityType.JAVA_IMPLEMENTATION_ATOM
            and observation_modality
            in {
                ObservationModality.JAVA_SOURCE_TRUE_BRANCH_CONTROL,
                ObservationModality.JAVA_SOURCE_FALSE_BRANCH_CONTROL,
            }
        )
    elif predicate is RelationPredicate.NEXT_IN_SOURCE:
        valid = (
            subject.entity_type is EntityType.JAVA_IMPLEMENTATION_ATOM
            and object.entity_type is EntityType.JAVA_IMPLEMENTATION_ATOM
            and observation_modality is ObservationModality.JAVA_SOURCE_ORDER
        )
    elif predicate is RelationPredicate.CALL_SITE_TARGETS:
        valid = (
            subject.entity_type is EntityType.JAVA_IMPLEMENTATION_ATOM
            and object.entity_type is EntityType.JAVA_METHOD
            and observation_modality
            is ObservationModality.JAVA_SOURCE_CALL_SITE_TARGET
        )
    elif predicate in {RelationPredicate.READS_STATE, RelationPredicate.WRITES_STATE}:
        expected_modality = (
            ObservationModality.JAVA_SOURCE_STATE_READ
            if predicate is RelationPredicate.READS_STATE
            else ObservationModality.JAVA_SOURCE_STATE_WRITE
        )
        valid = (
            subject.entity_type is EntityType.JAVA_IMPLEMENTATION_ATOM
            and object.entity_type is EntityType.JAVA_STATE_SLOT
            and observation_modality is expected_modality
        )
    elif predicate is RelationPredicate.HANDLES_THROW:
        valid = (
            subject.entity_type is EntityType.JAVA_IMPLEMENTATION_ATOM
            and object.entity_type is EntityType.JAVA_IMPLEMENTATION_ATOM
            and observation_modality
            is ObservationModality.JAVA_SOURCE_LEXICAL_EXCEPTION_HANDLER
        )
    else:  # pragma: no cover - all enum values are handled above
        valid = False
    if not valid:
        _fail("RELATION_SCHEMA_MISMATCH", "Relation Fact endpoint types, predicate, and modality do not match")


def _normalize_entity_state_payload(
    entity_type: EntityType, values: Mapping[str, object]
) -> CanonicalFields:
    supplied = dict(values)
    expected_fields = _ENTITY_STATE_FIELDS[entity_type]
    if (
        entity_type is EntityType.JAVA_TYPE
        and set(supplied) == set(_JAVA_TYPE_SEMANTICS_STATE_FIELDS)
    ):
        expected_fields = _JAVA_TYPE_SEMANTICS_STATE_FIELDS
    elif (
        entity_type is EntityType.JAVA_METHOD
        and set(supplied) == set(_JAVA_METHOD_SEMANTICS_STATE_FIELDS)
    ):
        expected_fields = _JAVA_METHOD_SEMANTICS_STATE_FIELDS
    _require_exact_keys(
        supplied, expected_fields, f"{entity_type.value} state payload"
    )
    evidence = _sorted_unique_stable_ids(
        _require_sequence(supplied["evidence_references"], "entity evidence references"),
        "entity evidence reference",
    )
    supplied["evidence_references"] = tuple(item.value for item in evidence)
    if entity_type is EntityType.SOFTWARE_SYSTEM:
        binding = supplied["source_binding_id"]
        _require_stable_id(binding, "source binding ID")
        supplied["source_binding_id"] = binding.value
    if entity_type is EntityType.JAVA_METHOD:
        modifiers = _require_sequence(supplied["modifiers"], "Java method modifiers")
        supplied["modifiers"] = tuple(
            sorted({_text(item, "Java method modifier") for item in modifiers})
        )
    if entity_type is EntityType.JAVA_SOURCE_FILE:
        supplied["disposition"] = _enum(
            JavaSemanticDisposition,
            supplied["disposition"],
            "Java source-file disposition",
        ).value
    if entity_type is EntityType.JAVA_TYPE and expected_fields == _JAVA_TYPE_SEMANTICS_STATE_FIELDS:
        supplied["disposition"] = _enum(
            JavaSemanticDisposition,
            supplied["disposition"],
            "Java type disposition",
        ).value
    if entity_type is EntityType.JAVA_METHOD and expected_fields == _JAVA_METHOD_SEMANTICS_STATE_FIELDS:
        supplied["method_disposition"] = _enum(
            JavaSemanticDisposition,
            supplied["method_disposition"],
            "Java method disposition",
        ).value
        for key in (
            "declaration_completeness",
            "legacy_static_call_completeness",
            "implementation_semantics_completeness",
        ):
            supplied[key] = _enum(
                JavaSemanticFacetCompleteness,
                supplied[key],
                f"Java method {key}",
            ).value
    if entity_type is EntityType.JAVA_IMPLEMENTATION_ATOM:
        ordinal = supplied["source_order_ordinal"]
        if type(ordinal) is not int or ordinal < 0:
            _fail(
                "JAVA_ATOM_ORDINAL_INVALID",
                "Java implementation Atom ordinal must be non-negative",
            )
        supplied["semantic_form"] = _enum(
            JavaSemanticForm,
            supplied["semantic_form"],
            "Java Atom semantic form",
        ).value
        supplied["operator"] = _enum(
            JavaSemanticOperator,
            supplied["operator"],
            "Java Atom operator",
        ).value
        supplied["value_category"] = _enum(
            JavaValueCategory,
            supplied["value_category"],
            "Java Atom value category",
        ).value
        supplied["method_disposition"] = _enum(
            JavaSemanticDisposition,
            supplied["method_disposition"],
            "Java Atom method disposition",
        ).value
        operands = _require_sequence(
            supplied["semantic_operands"], "Java Atom semantic operands"
        )
        if len(operands) > 8:
            _fail(
                "JAVA_ATOM_OPERAND_BUDGET_EXCEEDED",
                "Java implementation Atom exceeds its semantic operand budget",
            )
        supplied["semantic_operands"] = tuple(
            _normalize_java_semantic_operand(item) for item in operands
        )
        referenced = _sorted_unique_stable_ids(
            _require_sequence(
                supplied["referenced_entity_root_ids"],
                "Java Atom referenced Entity Roots",
            ),
            "Java Atom referenced Entity Root",
        )
        supplied["referenced_entity_root_ids"] = tuple(
            item.value for item in referenced
        )
    if entity_type is EntityType.JAVA_STATE_SLOT:
        supplied["declared_type"] = _java_type_ref(
            supplied["declared_type"], "Java state-slot declared type"
        )
    for key in expected_fields:
        if key != "evidence_references" and key != "source_binding_id":
            if entity_type is EntityType.JAVA_METHOD and key == "modifiers":
                continue
            if entity_type is EntityType.JAVA_IMPLEMENTATION_ATOM and key in {
                "source_order_ordinal",
                "semantic_operands",
                "referenced_entity_root_ids",
                "semantic_form",
                "operator",
                "value_category",
                "method_disposition",
            }:
                continue
            if entity_type is EntityType.JAVA_SOURCE_FILE and key == "disposition":
                continue
            if entity_type is EntityType.JAVA_TYPE and key == "disposition":
                continue
            if entity_type is EntityType.JAVA_METHOD and key in {
                "method_disposition",
                "declaration_completeness",
                "legacy_static_call_completeness",
                "implementation_semantics_completeness",
            }:
                continue
            if entity_type is EntityType.JAVA_STATE_SLOT and key == "declared_type":
                continue
            supplied[key] = _text(supplied[key], key)
    return CanonicalFields(supplied)


def _normalize_java_semantic_operand(value: object) -> CanonicalFields:
    if not isinstance(value, Mapping):
        _fail(
            "JAVA_ATOM_OPERAND_INVALID",
            "Java semantic operands must be typed mappings",
        )
    supplied = dict(value)
    _require_exact_keys(supplied, ("kind", "value"), "Java semantic operand")
    kind = _enum(
        JavaSemanticOperandKind,
        supplied["kind"],
        "Java semantic operand kind",
    )
    operand = supplied["value"]
    if kind is JavaSemanticOperandKind.ENTITY_REF:
        if isinstance(operand, str):
            try:
                operand = StableId(operand)
            except ValueError:
                _fail(
                    "JAVA_ATOM_ENTITY_REF_INVALID",
                    "Java semantic Entity Ref is not a StableId",
                )
        _require_stable_id(operand, "Java semantic Entity Ref", kind="entity_root")
        normalized: object = operand.value
    elif kind is JavaSemanticOperandKind.BOOLEAN_LITERAL:
        if type(operand) is not bool:
            _fail(
                "JAVA_ATOM_LITERAL_INVALID",
                "Java boolean semantic operand must be boolean",
            )
        normalized = operand
    elif kind is JavaSemanticOperandKind.NULL_LITERAL:
        if operand is not None:
            _fail(
                "JAVA_ATOM_LITERAL_INVALID",
                "Java null semantic operand must be null",
            )
        normalized = None
    elif kind in {
        JavaSemanticOperandKind.INTEGER_LITERAL,
        JavaSemanticOperandKind.CONSTRUCTOR_ARITY,
    }:
        minimum = 0 if kind is JavaSemanticOperandKind.CONSTRUCTOR_ARITY else -(2**31)
        maximum = 255 if kind is JavaSemanticOperandKind.CONSTRUCTOR_ARITY else 2**31 - 1
        if type(operand) is not int or not minimum <= operand <= maximum:
            _fail(
                "JAVA_ATOM_LITERAL_INVALID",
                "Java integer semantic operand is outside its frozen budget",
            )
        normalized = operand
    else:
        normalized = _java_qualified_identifier(
            operand,
            "Java enum/type semantic operand",
        )
    return CanonicalFields({"kind": kind.value, "value": normalized})


def _validate_java_semantic_entity_record(
    root: EntityRoot,
    state: EntityState,
) -> None:
    if root.entity_type is EntityType.JAVA_SOURCE_FILE:
        _enum(
            JavaSemanticDisposition,
            state.state_payload_fields["disposition"],
            "Java source-file disposition",
        )
        return
    if root.entity_type is EntityType.JAVA_TYPE:
        if "disposition" in state.state_payload_fields:
            _enum(
                JavaSemanticDisposition,
                state.state_payload_fields["disposition"],
                "Java type disposition",
            )
        return
    if root.entity_type is EntityType.JAVA_METHOD:
        if "method_disposition" in state.state_payload_fields:
            disposition = _enum(
                JavaSemanticDisposition,
                state.state_payload_fields["method_disposition"],
                "Java method disposition",
            )
            facets = tuple(
                _enum(
                    JavaSemanticFacetCompleteness,
                    state.state_payload_fields[key],
                    f"Java method {key}",
                )
                for key in (
                    "declaration_completeness",
                    "legacy_static_call_completeness",
                    "implementation_semantics_completeness",
                )
            )
            if disposition is JavaSemanticDisposition.SEMANTICS_COMPLETE and any(
                item is not JavaSemanticFacetCompleteness.COMPLETE for item in facets
            ):
                _fail(
                    "JAVA_METHOD_COMPLETENESS_INCONSISTENT",
                    "SEMANTICS_COMPLETE methods require all completeness facets COMPLETE",
                )
        return
    if root.entity_type is EntityType.JAVA_STATE_SLOT:
        _enum(
            JavaStateSlotKind,
            root.root_fields["slot_kind"],
            "Java state-slot kind",
        )
        _java_identifier(
            root.root_fields["canonical_identifier"],
            "Java state-slot identifier",
        )
        _java_type_ref(
            state.state_payload_fields["declared_type"],
            "Java state-slot declared type",
        )
        return
    if root.entity_type is not EntityType.JAVA_IMPLEMENTATION_ATOM:
        return
    kind = _enum(
        JavaImplementationAtomKind,
        root.root_fields["atom_kind"],
        "Java implementation Atom kind",
    )
    structural_ordinal = root.root_fields["structural_ordinal"]
    source_ordinal = state.state_payload_fields["source_order_ordinal"]
    if structural_ordinal != source_ordinal:
        _fail(
            "JAVA_ATOM_ORDINAL_MISMATCH",
            "Java Atom structural and source-order ordinals must match",
        )
    form = _enum(JavaSemanticForm, state.state_payload_fields["semantic_form"], "Java Atom semantic form")
    operator = _enum(JavaSemanticOperator, state.state_payload_fields["operator"], "Java Atom operator")
    category = _enum(JavaValueCategory, state.state_payload_fields["value_category"], "Java Atom value category")
    expected: dict[
        JavaImplementationAtomKind,
        tuple[set[JavaSemanticForm], set[JavaSemanticOperator], set[JavaValueCategory]],
    ] = {
        JavaImplementationAtomKind.BRANCH: (
            {JavaSemanticForm.BOOLEAN_SLOT_TEST},
            {
                JavaSemanticOperator.NOT,
                JavaSemanticOperator.IS_TRUE,
                JavaSemanticOperator.IS_FALSE,
                JavaSemanticOperator.IS_NULL,
                JavaSemanticOperator.NOT_NULL,
                JavaSemanticOperator.AND,
                JavaSemanticOperator.OR,
            },
            {JavaValueCategory.BOOLEAN},
        ),
        JavaImplementationAtomKind.CALL_SITE: (
            {JavaSemanticForm.STATIC_CALL},
            {JavaSemanticOperator.DIRECT_CALL},
            {JavaValueCategory.CALL_RESULT, JavaValueCategory.VOID},
        ),
        JavaImplementationAtomKind.RETURN: (
            {JavaSemanticForm.RETURN_VALUE},
            {JavaSemanticOperator.RETURN},
            {
                JavaValueCategory.BOOLEAN,
                JavaValueCategory.NULL,
                JavaValueCategory.INTEGER,
                JavaValueCategory.ENUM,
                JavaValueCategory.CALL_RESULT,
                JavaValueCategory.VOID,
                JavaValueCategory.STATE,
            },
        ),
        JavaImplementationAtomKind.THROW: (
            {JavaSemanticForm.THROW_CONSTRUCTION},
            {JavaSemanticOperator.THROW},
            {JavaValueCategory.EXCEPTION},
        ),
        JavaImplementationAtomKind.CATCH: (
            {JavaSemanticForm.LEXICAL_CATCH},
            {JavaSemanticOperator.NONE},
            {JavaValueCategory.EXCEPTION},
        ),
        JavaImplementationAtomKind.FINALLY: (
            {JavaSemanticForm.LEXICAL_FINALLY},
            {JavaSemanticOperator.NONE},
            {JavaValueCategory.VOID},
        ),
        JavaImplementationAtomKind.STATE_READ: (
            {JavaSemanticForm.STATE_ACCESS},
            {JavaSemanticOperator.READ},
            {JavaValueCategory.STATE},
        ),
        JavaImplementationAtomKind.STATE_WRITE: (
            {JavaSemanticForm.STATE_ACCESS},
            {JavaSemanticOperator.WRITE},
            {JavaValueCategory.STATE},
        ),
    }
    forms, operators, categories = expected[kind]
    if form not in forms or operator not in operators or category not in categories:
        _fail(
            "JAVA_ATOM_SEMANTIC_SHAPE_INVALID",
            "Java Atom kind, form, operator, and value category are inconsistent",
        )
    for operand in state.state_payload_fields["semantic_operands"]:
        _normalize_java_semantic_operand(operand)


def _normalize_predicate_payload(
    predicate: RelationPredicate, values: Mapping[str, object]
) -> CanonicalFields:
    supplied = dict(values)
    _require_exact_keys(supplied, _PREDICATE_STATE_FIELDS[predicate], f"{predicate.value} state payload")
    if predicate is RelationPredicate.CONTAINS_MODULE:
        supplied["module_declaration_path"] = _text(
            supplied["module_declaration_path"], "module declaration path"
        )
    elif predicate is RelationPredicate.DEPENDS_ON:
        for key in (
            "declared_dependency_gav_expression",
            "resolved_dependency_gav",
            "scope",
            "type",
        ):
            supplied[key] = _text(supplied[key], key)
        classifier = supplied["classifier"]
        if classifier is not None:
            supplied["classifier"] = _text(classifier, "classifier")
        if type(supplied["optional"]) is not bool:
            _fail("OPTIONAL_NOT_BOOLEAN", "dependency optional state must be a boolean")
    elif predicate is RelationPredicate.DECLARES_METHOD:
        ordinal = supplied["declaration_ordinal"]
        if type(ordinal) is not int or ordinal < 0:
            _fail(
                "DECLARATION_ORDINAL_INVALID",
                "Java declaration ordinal must be a non-negative integer",
            )
    elif predicate is RelationPredicate.CALLS:
        count = supplied["call_site_count"]
        if type(count) is not int or count < 1:
            _fail(
                "CALL_SITE_COUNT_INVALID",
                "Java call relation must contain at least one exact call site",
            )
    elif predicate in {
        RelationPredicate.HAS_IMPLEMENTATION_ATOM,
        RelationPredicate.CONTROLS,
        RelationPredicate.NEXT_IN_SOURCE,
        RelationPredicate.READS_STATE,
        RelationPredicate.WRITES_STATE,
    }:
        field = _PREDICATE_STATE_FIELDS[predicate][0]
        value = supplied[field]
        minimum = 1 if predicate is RelationPredicate.NEXT_IN_SOURCE else 0
        if type(value) is not int or value < minimum:
            _fail(
                "JAVA_SEMANTIC_RELATION_ORDINAL_INVALID",
                f"{predicate.value} requires a valid canonical ordinal",
            )
        if predicate is RelationPredicate.NEXT_IN_SOURCE and value != 1:
            _fail(
                "JAVA_SOURCE_ORDER_DISTANCE_INVALID",
                "NEXT_IN_SOURCE only relates adjacent implementation Atoms",
            )
    elif predicate is RelationPredicate.CALL_SITE_TARGETS:
        supplied["resolution_class"] = _enum(
            JavaCallResolutionClass,
            supplied["resolution_class"],
            "Java call-site resolution class",
        ).value
    else:
        field = _PREDICATE_STATE_FIELDS[predicate][0]
        supplied[field] = _java_qualified_identifier(supplied[field], field)
    return CanonicalFields(supplied)


def _coverage_root_fields(
    *,
    owning_scope_id: StableId,
    profile_ref: str,
    schema_ref: str,
    schema_digest: Digest,
    source_binding_id: StableId,
    logical_reactor_root: str,
    maven_evaluation_context_ref: str,
    maven_evaluation_context_digest: Digest,
    covered_entity_types: Sequence[EntityType],
    covered_relation_predicates: Sequence[RelationPredicate],
    canonicalization_ref: str,
    canonicalization_digest: Digest,
) -> CanonicalFields:
    _require_stable_id(owning_scope_id, "coverage owning scope ID")
    _require_stable_id(source_binding_id, "coverage source binding ID")
    for value, label in (
        (schema_digest, "coverage schema digest"),
        (maven_evaluation_context_digest, "Maven evaluation context digest"),
        (canonicalization_digest, "canonicalization digest"),
    ):
        _require_digest(value, label)
    return CanonicalFields(
        {
            "owning_scope_id": owning_scope_id.value,
            "profile_ref": _text(profile_ref, "profile ref"),
            "schema_ref": _text(schema_ref, "schema ref"),
            "schema_digest": schema_digest.value,
            "source_binding_id": source_binding_id.value,
            "logical_reactor_root": _text(logical_reactor_root, "logical reactor root"),
            "maven_evaluation_context_ref": _text(
                maven_evaluation_context_ref, "Maven evaluation context ref"
            ),
            "maven_evaluation_context_digest": maven_evaluation_context_digest.value,
            "covered_entity_types": tuple(item.value for item in covered_entity_types),
            "covered_relation_predicates": tuple(
                item.value for item in covered_relation_predicates
            ),
            "canonicalization_ref": _text(canonicalization_ref, "canonicalization ref"),
            "canonicalization_digest": canonicalization_digest.value,
        }
    )


def _coverage_state_fields(
    *,
    source_revision: str,
    knowledge_context_digest: Digest,
    schema_ref: str,
    schema_digest: Digest,
    maven_evaluation_context_ref: str,
    maven_evaluation_context_digest: Digest,
    canonicalization_ref: str,
    canonicalization_digest: Digest,
    complete_member_manifest: CompleteMemberManifest,
    evidence_references: Sequence[StableId],
) -> CanonicalFields:
    return CanonicalFields(
        {
            "source_revision": _text(source_revision, "source revision"),
            "knowledge_context_digest": knowledge_context_digest.value,
            "schema_ref": _text(schema_ref, "schema ref"),
            "schema_digest": schema_digest.value,
            "maven_evaluation_context_ref": _text(
                maven_evaluation_context_ref, "Maven evaluation context ref"
            ),
            "maven_evaluation_context_digest": maven_evaluation_context_digest.value,
            "canonicalization_ref": _text(canonicalization_ref, "canonicalization ref"),
            "canonicalization_digest": canonicalization_digest.value,
            "complete_member_manifest": complete_member_manifest.canonical_value(),
            "evidence_references": tuple(
                item.value
                for item in _sorted_unique_stable_ids(
                    evidence_references, "coverage evidence reference"
                )
            ),
        }
    )


def _exact_fields(values: Mapping[str, object], expected: Sequence[str], label: str) -> CanonicalFields:
    _require_exact_keys(values, expected, label)
    normalized: dict[str, object] = {}
    for key in expected:
        value = values[key]
        if isinstance(value, StableId):
            normalized[key] = value.value
        elif isinstance(value, Digest):
            normalized[key] = value.value
        elif key in {"structural_ordinal", "declaration_ordinal"}:
            if type(value) is not int or value < 0:
                _fail(
                    "JAVA_STRUCTURAL_ORDINAL_INVALID",
                    f"{key} must be a non-negative integer",
                )
            normalized[key] = value
        elif key == "atom_kind":
            normalized[key] = _enum(
                JavaImplementationAtomKind,
                value,
                "Java implementation Atom kind",
            ).value
        elif key == "slot_kind":
            normalized[key] = _enum(
                JavaStateSlotKind,
                value,
                "Java state-slot kind",
            ).value
        elif key == "canonical_identifier":
            normalized[key] = _java_identifier(
                value,
                "Java canonical identifier",
            )
        elif key == "parameter_types":
            if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
                _fail(
                    "PARAMETER_TYPES_INVALID",
                    "parameter_types must be an ordered sequence of canonical type names",
                )
            normalized[key] = tuple(
                _text(item, "parameter type") for item in value
            )
        else:
            normalized[key] = _text(value, key)
    return CanonicalFields(normalized)


def _java_identifier(value: object, label: str) -> str:
    normalized = _text(value, label)
    if len(normalized) > 64 or _JAVA_QUALIFIED_IDENTIFIER.fullmatch(normalized) is None or "." in normalized:
        _fail(
            "JAVA_IDENTIFIER_INVALID",
            f"{label} is not a bounded Java identifier",
        )
    return normalized


def _java_qualified_identifier(value: object, label: str) -> str:
    normalized = _text(value, label)
    segments = normalized.split(".")
    if (
        len(normalized) > 192
        or any(len(segment) > 64 for segment in segments)
        or _JAVA_QUALIFIED_IDENTIFIER.fullmatch(normalized) is None
    ):
        _fail(
            "JAVA_QUALIFIED_IDENTIFIER_INVALID",
            f"{label} is not a bounded Java qualified identifier",
        )
    return normalized


def _java_type_ref(value: object, label: str) -> str:
    normalized = _text(value, label)
    base = normalized
    dimensions = 0
    while base.endswith("[]"):
        base = base[:-2]
        dimensions += 1
    if dimensions > 8:
        _fail("JAVA_TYPE_REF_INVALID", f"{label} exceeds the array budget")
    _java_qualified_identifier(base, label)
    return normalized


def _require_exact_keys(values: Mapping[str, object], expected: Sequence[str], label: str) -> None:
    actual = set(values)
    expected_set = set(expected)
    if actual != expected_set:
        missing = ",".join(sorted(expected_set - actual)) or "-"
        extra = ",".join(sorted(actual - expected_set)) or "-"
        _fail(
            "FIELD_SET_MISMATCH",
            f"{label} must contain exactly the frozen fields",
            missing=missing,
            extra=extra,
        )


def _canonical_value(value: object) -> CanonicalValue:
    if value is None or type(value) in (bool, int):
        return value  # type: ignore[return-value]
    if isinstance(value, str):
        return _canonical_text(value, "canonical string")
    if isinstance(value, StableId):
        return value.value
    if isinstance(value, Digest):
        return value.value
    if isinstance(value, Enum):
        return _canonical_value(value.value)
    if isinstance(value, Mapping):
        return CanonicalFields(value)
    if isinstance(value, (list, tuple)):
        return tuple(_canonical_value(item) for item in value)
    if isinstance(value, float):
        raise CanonicalizationError("floating-point values are not canonical")
    raise CanonicalizationError(f"unsupported canonical value type: {type(value).__name__}")


def _plain_value(value: CanonicalValue) -> object:
    if isinstance(value, CanonicalFields):
        return value.as_dict()
    if isinstance(value, tuple):
        return [_plain_value(item) for item in value]
    return value


def _canonical_text(value: object, label: str) -> str:
    if not isinstance(value, str):
        _fail("TEXT_VALUE_REQUIRED", f"{label} must be a string")
    return unicodedata.normalize("NFC", value)


def _text(value: object, label: str) -> str:
    normalized = _canonical_text(value, label).strip()
    if not normalized:
        _fail("EMPTY_TEXT", f"{label} must be non-empty")
    if any(unicodedata.category(char) == "Cc" for char in normalized):
        _fail("CONTROL_CHARACTER", f"{label} cannot contain control characters")
    return normalized


def _expect_string(value: object, label: str) -> str:
    if not isinstance(value, str):
        _fail("TEXT_VALUE_REQUIRED", f"{label} must be a string")
    return value


def _required_str(values: Mapping[str, CanonicalValue], key: str) -> str:
    return _expect_string(values[key], key)


def _require_sequence(value: object, label: str) -> Sequence[object]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        _fail("SEQUENCE_REQUIRED", f"{label} must be a sequence")
    return value


def _validate_excerpt_range(byte_start: object, byte_end: object, excerpt: object) -> None:
    if (
        type(byte_start) is not int
        or type(byte_end) is not int
        or byte_start < 0
        or byte_end <= byte_start
    ):
        _fail("EVIDENCE_RANGE_INVALID", "Evidence byte range must be non-empty and ordered")
    if not isinstance(excerpt, str):
        _fail("EVIDENCE_EXCERPT_INVALID", "Evidence excerpt must be exact UTF-8 text")
    try:
        encoded = excerpt.encode("utf-8")
    except UnicodeEncodeError:
        _fail("EVIDENCE_EXCERPT_INVALID", "Evidence excerpt must be exact UTF-8 text")
    if len(encoded) != byte_end - byte_start:
        _fail("EVIDENCE_RANGE_INVALID", "Evidence byte range must match the exact excerpt bytes")


def _sorted_unique_stable_ids(
    values: Sequence[object], label: str
) -> tuple[StableId, ...]:
    normalized: dict[str, StableId] = {}
    for value in values:
        _require_stable_id(value, label)
        normalized[value.value] = value
    return tuple(normalized[key] for key in sorted(normalized))


def _sorted_unique_enums(
    enum_type: type[Enum], values: Sequence[object], label: str
) -> tuple[Any, ...]:
    normalized = {_enum(enum_type, value, label) for value in values}
    return tuple(sorted(normalized, key=lambda item: item.value))


def _sorted_members(values: Sequence[CoverageMember]) -> tuple[CoverageMember, ...]:
    for value in values:
        if not isinstance(value, CoverageMember):
            _fail("COVERAGE_MEMBER_INVALID", "member Manifest can contain only typed CoverageMember values")
    return tuple(
        sorted(values, key=lambda item: (item.kind.value, item.root_id.value, item.state_id.value))
    )


def _enum(enum_type: type[Enum], value: object, label: str) -> Any:
    try:
        return value if isinstance(value, enum_type) else enum_type(value)
    except (TypeError, ValueError):
        _fail("UNKNOWN_ENUM_VALUE", f"{label} is not supported", value=str(value))


def _require_stable_id(value: object, label: str, *, kind: str | None = None) -> None:
    if not isinstance(value, StableId):
        _fail("STABLE_ID_REQUIRED", f"{label} must be a typed StableId")
    if kind is not None and value.kind != kind:
        _fail("STABLE_ID_KIND_MISMATCH", f"{label} must have kind {kind}")


def _require_digest(value: object, label: str) -> None:
    if not isinstance(value, Digest):
        _fail("DIGEST_REQUIRED", f"{label} must be a typed Digest")


def _stable(kind: str, allocation_key: Digest) -> StableId:
    return StableId(f"{kind}_{allocation_key.value[-32:]}")


def _fail(reason_code: str, message: str, **details: str | int) -> None:
    raise DomainError(
        ErrorCode.INVALID_ARGUMENT,
        message,
        {"reason_code": reason_code, **details},
    )


__all__ = [
    "CanonicalFields",
    "CompleteMemberManifest",
    "CoverageCompleteness",
    "CoverageMember",
    "CoverageMemberKind",
    "CoverageRecord",
    "CoverageRoot",
    "CoverageState",
    "EntityRecord",
    "EntityRef",
    "EntityRoot",
    "EntityState",
    "EntityType",
    "ExactUpstreamEntity",
    "FactKind",
    "LiteralFactRecord",
    "LiteralFactRoot",
    "LiteralFactState",
    "LiteralObject",
    "LiteralType",
    "JAVA_SOURCE_SEMANTICS_CANONICALIZATION_DIGEST",
    "JAVA_SOURCE_SEMANTICS_CANONICALIZATION_REF",
    "JAVA_SOURCE_SEMANTICS_COVERAGE_ROOT_REF",
    "JAVA_SOURCE_SEMANTICS_ENTITY_TYPES",
    "JAVA_SOURCE_SEMANTICS_EVALUATION_CONTEXT_DIGEST",
    "JAVA_SOURCE_SEMANTICS_EVALUATION_CONTEXT_REF",
    "JAVA_SOURCE_SEMANTICS_FRONTEND_DIGEST",
    "JAVA_SOURCE_SEMANTICS_FRONTEND_REF",
    "JAVA_SOURCE_SEMANTICS_PROFILE_REF",
    "JAVA_SOURCE_SEMANTICS_RELATION_PREDICATES",
    "JAVA_SOURCE_SEMANTICS_SCHEMA_DIGEST",
    "JAVA_SOURCE_SEMANTICS_SCHEMA_REF",
    "JavaCallResolutionClass",
    "JavaImplementationAtomKind",
    "JavaSemanticDisposition",
    "JavaSemanticFacetCompleteness",
    "JavaSemanticForm",
    "JavaSemanticOperandKind",
    "JavaSemanticOperator",
    "JavaStateSlotKind",
    "JavaValueCategory",
    "MAVEN_CANONICALIZATION_DIGEST",
    "MAVEN_CANONICALIZATION_REF",
    "MAVEN_EVALUATION_CONTEXT_DIGEST",
    "MAVEN_EVALUATION_CONTEXT_REF",
    "MAVEN_STRUCTURE_COVERAGE_ROOT_REF",
    "MAVEN_STRUCTURE_PROFILE_REF",
    "MAVEN_STRUCTURE_SCHEMA_DIGEST",
    "MAVEN_STRUCTURE_SCHEMA_REF",
    "ObservationModality",
    "PublicationMode",
    "RelationFactRecord",
    "RelationFactRoot",
    "RelationFactState",
    "RelationPredicate",
    "RootStateIdentity",
    "StructureEvidence",
    "StructureKnowledgeBatch",
    "compare_root_state",
]
