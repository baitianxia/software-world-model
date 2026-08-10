"""Deterministic Maven reactor structure evaluation for ITER-003.

The evaluator in this module is deliberately a pure boundary.  It consumes an
explicit map of repository-relative POM bytes plus Git tree-entry metadata.  It
does not discover files, invoke Git or Maven, consult settings, read the process
environment, resolve a local repository, or use the network.

The output DTOs are intentionally independent from the knowledge-kernel DTOs.
They retain the frozen root/state derivation inputs and typed relation endpoints
so an application adapter can admit them without reparsing Maven data.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import posixpath
import re
from types import MappingProxyType
from typing import Any, Mapping, Sequence
import unicodedata
import xml.etree.ElementTree as ET

from software_world_model.cross_cutting import Digest, StableId
from software_world_model.knowledge_engine.structure import (
    CompleteMemberManifest,
    CoverageRecord,
    CoverageRoot,
    CoverageState,
    EntityRecord,
    EntityRoot,
    EntityState,
    EntityType,
    ObservationModality,
    PublicationMode,
    RelationFactRecord,
    RelationFactRoot,
    RelationFactState,
    RelationPredicate,
    StructureEvidence,
    StructureKnowledgeBatch,
)


SCHEMA_REF = "MAVEN-REACTOR-STRUCTURE@1.0.0"
SCHEMA_DIGEST = "sha256:947bea83028ff6658b01c18dccfd0c1ef028fa5e9a8701a4a0e90d16b8a58ce9"
PROFILE_REF = "MAVEN_REACTOR_STRUCTURE@1"
EVALUATION_CONTEXT_REF = "MAVEN-EVALUATION-CONTEXT@1.0.0"
EVALUATION_CONTEXT_DIGEST = (
    "sha256:4fce4ccbcc8ddbe254dc90e8419a178ce37c6fd9ea287e6fad8d15d571161ffd"
)
CANONICALIZATION_REF = "MAVEN-REACTOR-CANONICALIZATION@1.0.0"
CANONICALIZATION_DIGEST = (
    "sha256:4fae328bd8c2959cfc1eaaae3b9b27f40d601bf2ffb488bf3abe2cc81c5da6cf"
)
COVERAGE_ROOT_REF = "MAVEN_REACTOR_STRUCTURE_COVERAGE@1"
PUBLICATION_MODE = "REPLACE_COVERAGE"

MAVEN_NAMESPACE = "http://maven.apache.org/POM/4.0.0"
_NS = f"{{{MAVEN_NAMESPACE}}}"
_PROPERTY_REFERENCE = re.compile(r"\$\{([^{}]+)\}")
_REGULAR_GIT_MODES = frozenset({"100644", "100755"})
_SYMLINK_GIT_MODE = "120000"
_MAX_PROPERTY_EXPANSIONS = 32


class MavenStructureErrorCode(str, Enum):
    """Stable evaluator rejection codes, including every frozen fixture code."""

    INVALID_INPUT = "INVALID_INPUT"
    ROOT_POM_MISSING = "ROOT_POM_MISSING"
    POM_ENTRY_METADATA_MISSING = "POM_ENTRY_METADATA_MISSING"
    POM_ENTRY_NOT_REGULAR_FILE = "POM_ENTRY_NOT_REGULAR_FILE"
    POM_EVIDENCE_MISSING = "POM_EVIDENCE_MISSING"
    POM_CONTENT_DIGEST_MISMATCH = "POM_CONTENT_DIGEST_MISMATCH"
    TREE_EVIDENCE_INVALID = "TREE_EVIDENCE_INVALID"
    TREE_ENTRY_DUPLICATE = "TREE_ENTRY_DUPLICATE"
    TREE_ENTRY_METADATA_MISMATCH = "TREE_ENTRY_METADATA_MISMATCH"
    MALFORMED_POM = "MALFORMED_POM"
    MODULE_TARGET_MISSING = "MODULE_TARGET_MISSING"
    MODULE_PATH_ESCAPES_ROOT = "MODULE_PATH_ESCAPES_ROOT"
    MODULE_PATH_SYMLINK_UNSUPPORTED = "MODULE_PATH_SYMLINK_UNSUPPORTED"
    MODULE_CANONICAL_TARGET_DUPLICATE = "MODULE_CANONICAL_TARGET_DUPLICATE"
    MODULE_GRAPH_CYCLE = "MODULE_GRAPH_CYCLE"
    REACTOR_GA_AMBIGUOUS = "REACTOR_GA_AMBIGUOUS"
    RELEVANT_PROFILE_UNSUPPORTED = "RELEVANT_PROFILE_UNSUPPORTED"
    REQUIRED_PROPERTY_UNRESOLVED = "REQUIRED_PROPERTY_UNRESOLVED"
    REQUIRED_DEPENDENCY_VERSION_UNRESOLVED = (
        "REQUIRED_DEPENDENCY_VERSION_UNRESOLVED"
    )
    DISALLOWED_PROPERTY_SOURCE = "DISALLOWED_PROPERTY_SOURCE"
    PROPERTY_CYCLE = "PROPERTY_CYCLE"
    PROPERTY_EXPANSION_LIMIT = "PROPERTY_EXPANSION_LIMIT"
    VERSION_RANGE_UNSUPPORTED = "VERSION_RANGE_UNSUPPORTED"
    EXTERNAL_PARENT_REQUIRED = "EXTERNAL_PARENT_REQUIRED"
    EXTERNAL_BOM_REQUIRED = "EXTERNAL_BOM_REQUIRED"
    DUPLICATE_LOCAL_DEPENDENCY_GA = "DUPLICATE_LOCAL_DEPENDENCY_GA"
    DUPLICATE_DEPENDENCY_MANAGEMENT_GA = "DUPLICATE_DEPENDENCY_MANAGEMENT_GA"
    DUPLICATE_POM_PROPERTY = "DUPLICATE_POM_PROPERTY"
    REACTOR_DEPENDENCY_SHAPE_UNSUPPORTED = (
        "REACTOR_DEPENDENCY_SHAPE_UNSUPPORTED"
    )
    LOCAL_PARENT_GAV_MISMATCH = "LOCAL_PARENT_GAV_MISMATCH"
    LOCAL_PARENT_SYMLINK_UNSUPPORTED = "LOCAL_PARENT_SYMLINK_UNSUPPORTED"
    PARENT_CYCLE = "PARENT_CYCLE"


class MavenStructureError(ValueError):
    """Fail-closed rejection of a complete reactor evaluation."""

    def __init__(
        self,
        code: MavenStructureErrorCode,
        detail: str,
        *,
        locator: str | None = None,
    ) -> None:
        self.code = code
        self.detail = detail
        self.locator = locator
        location = f" at {locator}" if locator else ""
        super().__init__(f"{code.value}{location}: {detail}")


@dataclass(frozen=True, slots=True)
class GitEntryMetadata:
    """The relevant immutable fields from an exact Git tree entry."""

    mode: str
    object_type: str = "blob"
    object_id: str | None = None

    def __post_init__(self) -> None:
        mode = str(self.mode)
        object_type = str(self.object_type)
        if not mode or not object_type:
            raise ValueError("Git entry mode and object type must be non-empty")
        object.__setattr__(self, "mode", mode)
        object.__setattr__(self, "object_type", object_type)
        if self.object_id is not None and not str(self.object_id).strip():
            raise ValueError("Git object ID cannot be empty")
        if self.object_id is not None:
            object.__setattr__(self, "object_id", str(self.object_id))

    @property
    def is_symlink(self) -> bool:
        return self.mode == _SYMLINK_GIT_MODE

    @property
    def is_regular_file(self) -> bool:
        return self.mode in _REGULAR_GIT_MODES and self.object_type == "blob"


@dataclass(frozen=True, slots=True)
class PomEvidenceMetadata:
    """Exact source-owned metadata required to create traceable Evidence.

    The evaluator verifies ``artifact_content_digest`` against the supplied POM
    bytes and propagates the Artifact/Context/locator unchanged.  It never
    invents an Artifact or Source Context identity.
    """

    artifact_id: StableId
    source_context_id: StableId
    artifact_content_digest: Digest
    locator: str

    def __post_init__(self) -> None:
        if not isinstance(self.artifact_id, StableId):
            raise ValueError("POM Evidence Artifact ID must be a StableId")
        if not isinstance(self.source_context_id, StableId):
            raise ValueError("POM Evidence Source Context ID must be a StableId")
        if not isinstance(self.artifact_content_digest, Digest):
            raise ValueError("POM Evidence Artifact content digest must be a Digest")
        object.__setattr__(self, "locator", _input_text(self.locator, "POM Evidence locator"))


@dataclass(frozen=True, slots=True)
class MavenEvaluationInput:
    owning_scope_id: StableId
    canonical_system_key: str
    source_binding_id: StableId
    source_revision: str
    knowledge_context_digest: Digest
    pom_bytes: Mapping[str, bytes]
    git_entries: Mapping[str, GitEntryMetadata]
    pom_evidence: Mapping[str, PomEvidenceMetadata]
    tree_evidence: Sequence[StructureEvidence]
    logical_reactor_root: str = "pom.xml"


# Name retained for callers that prefer the fully qualified profile term.
MavenReactorEvaluationInput = MavenEvaluationInput


@dataclass(frozen=True, slots=True)
class BuildExclusion:
    consumer_pom_locator: str
    declared_dependency_gav_expression: str
    resolved_dependency_ga: str
    resolved_dependency_version_or_null: str | None
    matched_reactor_target_gav_or_null: str | None
    decision: str
    reason_code: str
    evidence_references: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class DependencyEvaluation:
    consumer_pom_locator: str
    consumer_gav: str
    declared_dependency_gav_expression: str
    resolved_dependency_ga: str
    resolved_dependency_version_or_null: str | None
    matched_reactor_target_gav_or_null: str | None
    decision: str
    reason_code: str | None
    evidence_references: tuple[str, ...]
    relation_root_id: str | None = None
    relation_state_id: str | None = None


@dataclass(frozen=True, slots=True)
class BuildReport:
    schema_ref: str
    evaluation_context_ref: str
    canonicalization_ref: str
    source_revision: str
    scanned_pom_locators: tuple[str, ...]
    dependency_declarations: tuple[DependencyEvaluation, ...]
    exclusions: tuple[BuildExclusion, ...]
    complete: bool
    lines: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class MavenStructureEvaluation:
    root_project: EntityRecord
    modules: tuple[EntityRecord, ...]
    relations: tuple[RelationFactRecord, ...]
    coverage: CoverageRecord
    complete_member_manifest: CompleteMemberManifest
    evidence: tuple[StructureEvidence, ...]
    exclusions: tuple[BuildExclusion, ...]
    report: BuildReport
    batch: StructureKnowledgeBatch

    @property
    def entities(self) -> tuple[EntityRecord, ...]:
        return (self.root_project, *self.modules)


@dataclass(frozen=True, slots=True)
class _RawParent:
    group_id: str | None
    artifact_id: str | None
    version: str | None
    relative_path_present: bool
    relative_path: str | None


@dataclass(frozen=True, slots=True)
class _RawModule:
    expression: str | None
    locator: str


@dataclass(frozen=True, slots=True)
class _RawDependency:
    group_id: str | None
    artifact_id: str | None
    version: str | None
    scope: str | None
    type: str | None
    classifier: str | None
    optional: str | None
    locator: str

    @property
    def expression(self) -> str:
        group_id = self.group_id if self.group_id is not None else "<missing-groupId>"
        artifact_id = (
            self.artifact_id
            if self.artifact_id is not None
            else "<missing-artifactId>"
        )
        version = self.version if self.version is not None else "<managed>"
        return f"{group_id}:{artifact_id}:{version}"


@dataclass(frozen=True, slots=True)
class _RawPom:
    path: str
    content_digest: str
    group_id: str | None
    artifact_id: str | None
    version: str | None
    packaging: str | None
    name: str | None
    parent: _RawParent | None
    modules: tuple[_RawModule, ...]
    properties: Mapping[str, str]
    dependencies: tuple[_RawDependency, ...]
    dependency_management: tuple[_RawDependency, ...]
    profile_has_structural_fields: bool
    profile_property_keys: frozenset[str]


@dataclass(frozen=True, slots=True)
class _ParentLink:
    local_path: str | None
    external: bool


@dataclass(frozen=True, slots=True)
class _EffectivePom:
    path: str
    group_id: str
    artifact_id: str
    version: str
    packaging: str
    label: str
    local_parent_path: str | None
    has_external_parent: bool

    @property
    def ga(self) -> tuple[str, str]:
        return (self.group_id, self.artifact_id)

    @property
    def gav(self) -> tuple[str, str, str]:
        return (self.group_id, self.artifact_id, self.version)


@dataclass(frozen=True, slots=True)
class _DiscoveredModule:
    path: str
    module_path: str
    declaration_locator: str
    membership_evidence_locators: tuple[str, ...]


def evaluate_maven_reactor(
    evaluation_input: MavenEvaluationInput,
) -> MavenStructureEvaluation:
    """Evaluate an exact in-memory Maven reactor under the frozen profile."""

    return MavenStructureEvaluator().evaluate(evaluation_input)


class MavenStructureEvaluator:
    """Pure deterministic evaluator for ``MAVEN_REACTOR_STRUCTURE@1``."""

    def evaluate(
        self, evaluation_input: MavenEvaluationInput
    ) -> MavenStructureEvaluation:
        state = _EvaluationState(evaluation_input)
        return state.evaluate()


class _EvaluationState:
    def __init__(self, value: MavenEvaluationInput) -> None:
        if not isinstance(value.owning_scope_id, StableId):
            raise MavenStructureError(
                MavenStructureErrorCode.INVALID_INPUT,
                "owning scope ID must be a typed StableId",
            )
        self.scope_id = value.owning_scope_id
        self.system_key = _input_text(
            value.canonical_system_key, "canonical system key"
        )
        if not isinstance(value.source_binding_id, StableId):
            raise MavenStructureError(
                MavenStructureErrorCode.INVALID_INPUT,
                "source binding ID must be a typed StableId",
            )
        self.source_binding_id = value.source_binding_id
        self.source_revision = _input_text(value.source_revision, "source revision")
        if not isinstance(value.knowledge_context_digest, Digest):
            raise MavenStructureError(
                MavenStructureErrorCode.INVALID_INPUT,
                "knowledge context digest must be a typed Digest",
            )
        self.knowledge_context_digest = value.knowledge_context_digest
        tree_evidence: dict[StableId, StructureEvidence] = {}
        for item in value.tree_evidence:
            if not isinstance(item, StructureEvidence):
                raise MavenStructureError(
                    MavenStructureErrorCode.INVALID_INPUT,
                    "tree Evidence values must be typed StructureEvidence",
                )
            item.require_valid_identity()
            if not item.locator.startswith(f"git-tree:{self.source_revision}:"):
                raise MavenStructureError(
                    MavenStructureErrorCode.INVALID_INPUT,
                    "tree Evidence locator is not bound to the requested source revision",
                    locator=item.locator,
                )
            if item.evidence_id in tree_evidence:
                raise MavenStructureError(
                    MavenStructureErrorCode.INVALID_INPUT,
                    "tree Evidence IDs must be unique",
                    locator=item.locator,
                )
            tree_evidence[item.evidence_id] = item
        if not tree_evidence:
            raise MavenStructureError(
                MavenStructureErrorCode.INVALID_INPUT,
                "complete Git tree Evidence is required for Maven evaluation",
            )
        self.tree_evidence = tuple(
            sorted(tree_evidence.values(), key=lambda item: item.evidence_id.value)
        )

        self.root_path = _input_path(value.logical_reactor_root)
        self.logical_root_directory = posixpath.dirname(self.root_path)
        self.pom_bytes: dict[str, bytes] = {}
        for raw_path, payload in value.pom_bytes.items():
            path = _input_path(raw_path)
            if path in self.pom_bytes:
                raise MavenStructureError(
                    MavenStructureErrorCode.INVALID_INPUT,
                    "POM byte map contains duplicate canonical paths",
                    locator=path,
                )
            if not isinstance(payload, bytes):
                raise MavenStructureError(
                    MavenStructureErrorCode.INVALID_INPUT,
                    "POM payloads must be immutable bytes",
                    locator=path,
                )
            self.pom_bytes[path] = payload

        self.git_entries: dict[str, GitEntryMetadata] = {}
        for raw_path, metadata in value.git_entries.items():
            path = _input_path(raw_path)
            if path in self.git_entries:
                raise MavenStructureError(
                    MavenStructureErrorCode.INVALID_INPUT,
                    "Git entry map contains duplicate canonical paths",
                    locator=path,
                )
            if not isinstance(metadata, GitEntryMetadata):
                raise MavenStructureError(
                    MavenStructureErrorCode.INVALID_INPUT,
                    "Git entry values must be GitEntryMetadata",
                    locator=path,
                )
            self.git_entries[path] = metadata
        self._validate_tree_evidence()

        self.pom_evidence: dict[str, PomEvidenceMetadata] = {}
        for raw_path, metadata in value.pom_evidence.items():
            path = _input_path(raw_path)
            if path in self.pom_evidence:
                raise MavenStructureError(
                    MavenStructureErrorCode.INVALID_INPUT,
                    "POM Evidence map contains duplicate canonical paths",
                    locator=path,
                )
            if not isinstance(metadata, PomEvidenceMetadata):
                raise MavenStructureError(
                    MavenStructureErrorCode.INVALID_INPUT,
                    "POM Evidence values must be PomEvidenceMetadata",
                    locator=path,
                )
            self.pom_evidence[path] = metadata

        self._raw_poms: dict[str, _RawPom] = {}
        self._parent_links: dict[str, _ParentLink] = {}
        self._effective_poms: dict[str, _EffectivePom] = {}
        self._model_stack: list[str] = []
        self._field_cache: dict[tuple[str, str], str] = {}
        self._field_stack: list[tuple[str, str]] = []
        self._evidence_by_path: dict[str, StructureEvidence] = {}

    def _validate_tree_evidence(self) -> None:
        observed: dict[str, GitEntryMetadata] = {}
        required_keys = {"is_symlink", "mode", "object_id", "path", "type"}
        for evidence in self.tree_evidence:
            encoded = evidence.excerpt.encode("utf-8")
            actual_content_digest = f"sha256:{hashlib.sha256(encoded).hexdigest()}"
            if actual_content_digest != evidence.artifact_content_digest.value:
                raise MavenStructureError(
                    MavenStructureErrorCode.TREE_EVIDENCE_INVALID,
                    "tree Evidence excerpt does not match its Artifact content digest",
                    locator=evidence.locator,
                )
            lines = evidence.excerpt.splitlines()
            if not lines:
                raise MavenStructureError(
                    MavenStructureErrorCode.TREE_EVIDENCE_INVALID,
                    "tree Evidence page must contain canonical JSONL entries",
                    locator=evidence.locator,
                )
            for line_number, line in enumerate(lines, 1):
                line_locator = f"{evidence.locator}#line={line_number}"
                if not line:
                    raise MavenStructureError(
                        MavenStructureErrorCode.TREE_EVIDENCE_INVALID,
                        "tree Evidence JSONL cannot contain blank lines",
                        locator=line_locator,
                    )
                try:
                    value = json.loads(line, object_pairs_hook=_unique_json_object)
                except (json.JSONDecodeError, ValueError) as exc:
                    raise MavenStructureError(
                        MavenStructureErrorCode.TREE_EVIDENCE_INVALID,
                        "tree Evidence line is not duplicate-free JSON",
                        locator=line_locator,
                    ) from exc
                if not isinstance(value, dict) or set(value) != required_keys:
                    raise MavenStructureError(
                        MavenStructureErrorCode.TREE_EVIDENCE_INVALID,
                        "tree Evidence entry must contain exactly the frozen fields",
                        locator=line_locator,
                    )
                canonical_line = json.dumps(
                    value,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                    allow_nan=False,
                )
                if line != canonical_line:
                    raise MavenStructureError(
                        MavenStructureErrorCode.TREE_EVIDENCE_INVALID,
                        "tree Evidence entry is not canonical JSON",
                        locator=line_locator,
                    )
                path_value = value["path"]
                mode = value["mode"]
                object_type = value["type"]
                object_id = value["object_id"]
                is_symlink = value["is_symlink"]
                if (
                    not isinstance(path_value, str)
                    or not isinstance(mode, str)
                    or not isinstance(object_type, str)
                    or not isinstance(object_id, str)
                    or type(is_symlink) is not bool
                    or not re.fullmatch(r"[0-7]{6}", mode)
                    or not re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", object_id)
                    or not object_type
                    or is_symlink != (mode == _SYMLINK_GIT_MODE)
                ):
                    raise MavenStructureError(
                        MavenStructureErrorCode.TREE_EVIDENCE_INVALID,
                        "tree Evidence entry contains invalid Git metadata",
                        locator=line_locator,
                    )
                canonical_path = _input_path(path_value)
                if canonical_path != path_value:
                    raise MavenStructureError(
                        MavenStructureErrorCode.TREE_EVIDENCE_INVALID,
                        "tree Evidence path is not canonical",
                        locator=line_locator,
                    )
                if canonical_path in observed:
                    raise MavenStructureError(
                        MavenStructureErrorCode.TREE_ENTRY_DUPLICATE,
                        "tree Evidence pages repeat a Git entry path",
                        locator=canonical_path,
                    )
                observed[canonical_path] = GitEntryMetadata(
                    mode=mode,
                    object_type=object_type,
                    object_id=object_id,
                )

        if set(observed) != set(self.git_entries):
            missing = sorted(set(self.git_entries) - set(observed))
            extra = sorted(set(observed) - set(self.git_entries))
            raise MavenStructureError(
                MavenStructureErrorCode.TREE_ENTRY_METADATA_MISMATCH,
                f"tree Evidence paths differ from Git metadata; missing={missing}, extra={extra}",
            )
        for path, expected in self.git_entries.items():
            if observed[path] != expected:
                raise MavenStructureError(
                    MavenStructureErrorCode.TREE_ENTRY_METADATA_MISMATCH,
                    "tree Evidence entry differs from supplied Git metadata",
                    locator=path,
                )

    def evaluate(self) -> MavenStructureEvaluation:
        if self.root_path not in self.pom_bytes:
            raise MavenStructureError(
                MavenStructureErrorCode.ROOT_POM_MISSING,
                "the logical reactor root POM bytes were not provided",
                locator=self.root_path,
            )
        self._require_regular_pom(self.root_path, module_target=False)
        root_raw = self._raw_pom(self.root_path)
        root_model = self._effective_pom(self.root_path)
        discovered = self._discover_modules(root_raw)

        module_models: dict[str, _EffectivePom] = {
            item.path: self._effective_pom(item.path) for item in discovered
        }
        ga_to_path: dict[tuple[str, str], str] = {}
        for item in discovered:
            model = module_models[item.path]
            previous = ga_to_path.get(model.ga)
            if previous is not None:
                raise MavenStructureError(
                    MavenStructureErrorCode.REACTOR_GA_AMBIGUOUS,
                    (
                        f"reactor child GA {_ga_text(model.ga)} resolves from both "
                        f"{previous} and {item.path}"
                    ),
                    locator=item.path,
                )
            ga_to_path[model.ga] = item.path
        if root_model.ga in ga_to_path:
            raise MavenStructureError(
                MavenStructureErrorCode.REACTOR_GA_AMBIGUOUS,
                "root project GA is also used by a reactor child module",
                locator=ga_to_path[root_model.ga],
            )
        self._reject_structural_profiles()

        root_entity = self._entity_record(
            entity_type="SOFTWARE_SYSTEM",
            root_fields={
                "canonical_system_key": self.system_key,
            },
            state_payload={
                "label": root_model.label,
                "effective_group_id": root_model.group_id,
                "artifact_id": root_model.artifact_id,
                "effective_version": root_model.version,
                "packaging": root_model.packaging,
                "source_binding_id": self.source_binding_id,
                "source_revision": self.source_revision,
                "root_pom_locator": self.root_path,
                "evidence_references": self._pom_evidence_references(
                    self._local_parent_chain(self.root_path)
                ),
            },
        )

        module_entities_by_path: dict[str, EntityRecord] = {}
        for item in discovered:
            model = module_models[item.path]
            module_entities_by_path[item.path] = self._entity_record(
                entity_type="MAVEN_MODULE",
                root_fields={
                    "effective_group_id": model.group_id,
                    "artifact_id": model.artifact_id,
                },
                state_payload={
                    "effective_version": model.version,
                    "packaging": model.packaging,
                    "module_path": item.module_path,
                    "label": model.label,
                    "source_revision": self.source_revision,
                    "evidence_references": self._pom_evidence_references(
                        self._local_parent_chain(item.path)
                    ),
                },
            )

        module_entities = tuple(
            sorted(
                module_entities_by_path.values(),
                key=lambda candidate: (
                    str(candidate.root.root_fields["effective_group_id"]),
                    str(candidate.root.root_fields["artifact_id"]),
                    str(candidate.state.state_payload_fields["module_path"]),
                ),
            )
        )

        relations: list[RelationFactRecord] = []
        for item in discovered:
            target = module_entities_by_path[item.path]
            membership_paths = tuple(
                locator.split("#", 1)[0]
                for locator in item.membership_evidence_locators
            )
            evidence_refs = self._pom_evidence_references(
                self._local_parent_chain(self.root_path),
                *(self._local_parent_chain(path) for path in membership_paths),
                self._local_parent_chain(item.path),
            )
            relations.append(
                self._relation_candidate(
                    subject=root_entity,
                    predicate="CONTAINS_MODULE",
                    object_=target,
                    observation_modality="RECURSIVE_REACTOR_MEMBERSHIP@1",
                    evidence_references=evidence_refs,
                    predicate_payload={
                        "module_declaration_path": item.module_path,
                    },
                )
            )

        ga_to_entity = {
            module_models[path].ga: module_entities_by_path[path]
            for path in module_models
        }
        dependency_reports: list[DependencyEvaluation] = []
        exclusions: list[BuildExclusion] = []
        consumers: list[tuple[str, _EffectivePom, EntityRecord]] = [
            (self.root_path, root_model, root_entity)
        ]
        consumers.extend(
            (item.path, module_models[item.path], module_entities_by_path[item.path])
            for item in discovered
        )
        for path, consumer_model, consumer_entity in consumers:
            raw = self._raw_pom(path)
            seen_dependency_ga: set[tuple[str, str]] = set()
            for dependency in raw.dependencies:
                group_id = self._resolve_required_expression(
                    path,
                    dependency.group_id,
                    locator=dependency.locator,
                    field="dependency groupId",
                )
                artifact_id = self._resolve_required_expression(
                    path,
                    dependency.artifact_id,
                    locator=dependency.locator,
                    field="dependency artifactId",
                )
                ga = (group_id, artifact_id)
                if ga in seen_dependency_ga:
                    raise MavenStructureError(
                        MavenStructureErrorCode.DUPLICATE_LOCAL_DEPENDENCY_GA,
                        f"POM locally declares canonical dependency GA {_ga_text(ga)} more than once",
                        locator=dependency.locator,
                    )
                seen_dependency_ga.add(ga)
                consumer_evidence_paths = self._local_parent_chain(path)

                if ga == root_model.ga:
                    exclusion = self._exclusion(
                        path,
                        dependency,
                        ga,
                        version=None,
                        target_gav=None,
                        reason="ROOT_PROJECT_TARGET_OUTSIDE_PROFILE",
                        evidence_references=self._pom_evidence_references(
                            consumer_evidence_paths,
                            self._local_parent_chain(self.root_path),
                        ),
                    )
                    exclusions.append(exclusion)
                    dependency_reports.append(
                        self._dependency_report_from_exclusion(
                            consumer_model, exclusion
                        )
                    )
                    continue

                target = ga_to_entity.get(ga)
                if target is None:
                    exclusion = self._exclusion(
                        path,
                        dependency,
                        ga,
                        version=None,
                        target_gav=None,
                        reason="GA_NOT_IN_REACTOR_CHILD_SET",
                        evidence_references=self._pom_evidence_references(
                            consumer_evidence_paths
                        ),
                    )
                    exclusions.append(exclusion)
                    dependency_reports.append(
                        self._dependency_report_from_exclusion(
                            consumer_model, exclusion
                        )
                    )
                    continue

                type_value = self._resolve_optional_expression(
                    path,
                    dependency.type,
                    default="jar",
                    locator=dependency.locator,
                    field="dependency type",
                )
                classifier_value = self._resolve_optional_expression(
                    path,
                    dependency.classifier,
                    default=None,
                    locator=dependency.locator,
                    field="dependency classifier",
                )
                if type_value != "jar" or classifier_value is not None:
                    raise MavenStructureError(
                        MavenStructureErrorCode.REACTOR_DEPENDENCY_SHAPE_UNSUPPORTED,
                        (
                            "a dependency matching a reactor child must use omitted/jar "
                            "type and no classifier"
                        ),
                        locator=dependency.locator,
                    )

                version_expression = dependency.version
                if version_expression is None:
                    managed = self._managed_dependency(path, ga)
                    if managed is None:
                        if self._has_external_parent(path):
                            raise MavenStructureError(
                                MavenStructureErrorCode.EXTERNAL_PARENT_REQUIRED,
                                (
                                    f"exact version for reactor dependency {_ga_text(ga)} "
                                    "would require disabled external parent content"
                                ),
                                locator=dependency.locator,
                            )
                        if self._has_external_bom(path):
                            raise MavenStructureError(
                                MavenStructureErrorCode.EXTERNAL_BOM_REQUIRED,
                                (
                                    f"exact version for reactor dependency {_ga_text(ga)} "
                                    "would require disabled external BOM content"
                                ),
                                locator=dependency.locator,
                            )
                        raise MavenStructureError(
                            MavenStructureErrorCode.REQUIRED_DEPENDENCY_VERSION_UNRESOLVED,
                            f"reactor dependency {_ga_text(ga)} has no exact version",
                            locator=dependency.locator,
                        )
                    version_expression = managed.version

                version = self._resolve_required_expression(
                    path,
                    version_expression,
                    locator=dependency.locator,
                    field="reactor dependency version",
                )
                self._reject_version_range(version, dependency.locator)
                target_path = ga_to_path[ga]
                target_model = module_models[target_path]
                target_gav = _gav_text(target_model.gav)
                dependency_evidence = self._pom_evidence_references(
                    consumer_evidence_paths,
                    self._local_parent_chain(target_path),
                )
                if version != target_model.version:
                    exclusion = self._exclusion(
                        path,
                        dependency,
                        ga,
                        version=version,
                        target_gav=target_gav,
                        reason="REACTOR_TARGET_VERSION_MISMATCH",
                        evidence_references=dependency_evidence,
                    )
                    exclusions.append(exclusion)
                    dependency_reports.append(
                        self._dependency_report_from_exclusion(
                            consumer_model, exclusion
                        )
                    )
                    continue

                scope = self._resolve_optional_expression(
                    path,
                    dependency.scope,
                    default="compile",
                    locator=dependency.locator,
                    field="dependency scope",
                )
                optional_text = self._resolve_optional_expression(
                    path,
                    dependency.optional,
                    default="false",
                    locator=dependency.locator,
                    field="dependency optional",
                )
                if optional_text not in ("true", "false"):
                    raise MavenStructureError(
                        MavenStructureErrorCode.REACTOR_DEPENDENCY_SHAPE_UNSUPPORTED,
                        "dependency optional must resolve to true or false",
                        locator=dependency.locator,
                    )
                relation = self._relation_candidate(
                    subject=consumer_entity,
                    predicate="DEPENDS_ON",
                    object_=target,
                    observation_modality=(
                        "POM_LOCAL_DECLARED_INTERNAL_DEPENDENCY@1"
                    ),
                    evidence_references=dependency_evidence,
                    predicate_payload={
                        "declared_dependency_gav_expression": dependency.expression,
                        "resolved_dependency_gav": _gav_text((group_id, artifact_id, version)),
                        "scope": scope,
                        "type": type_value,
                        "classifier": classifier_value,
                        "optional": optional_text == "true",
                    },
                )
                relations.append(relation)
                dependency_reports.append(
                    DependencyEvaluation(
                        consumer_pom_locator=path,
                        consumer_gav=_gav_text(consumer_model.gav),
                        declared_dependency_gav_expression=dependency.expression,
                        resolved_dependency_ga=_ga_text(ga),
                        resolved_dependency_version_or_null=version,
                        matched_reactor_target_gav_or_null=target_gav,
                        decision="INTERNAL_DEPENDS_ON",
                        reason_code=None,
                        evidence_references=tuple(
                            item.value for item in dependency_evidence
                        ),
                        relation_root_id=relation.root_id.value,
                        relation_state_id=relation.state_id.value,
                    )
                )

        relations_tuple = tuple(
            sorted(
                relations,
                key=lambda item: (
                    item.root.predicate.value,
                    item.root.subject.entity_root_id.value,
                    item.root.object.entity_root_id.value,
                ),
            )
        )
        manifest = CompleteMemberManifest.create(
            tuple(item.coverage_member for item in (root_entity, *module_entities))
            + tuple(item.coverage_member for item in relations_tuple)
        )
        coverage = self._coverage_candidate(
            manifest,
            tuple(
                self._pom_evidence(path).evidence_id
                for path in sorted(self._raw_poms)
            )
            + tuple(item.evidence_id for item in self.tree_evidence),
        )

        evidence_tuple = tuple(
            sorted(
                (*self.tree_evidence, *self._evidence_by_path.values()),
                key=lambda item: item.evidence_id.value,
            )
        )
        batch = StructureKnowledgeBatch.admit(
            evidence=evidence_tuple,
            entities=(root_entity, *module_entities),
            relation_facts=relations_tuple,
            coverage=coverage,
            publication_mode=PublicationMode.REPLACE_COVERAGE,
        )

        exclusions_tuple = tuple(
            sorted(
                exclusions,
                key=lambda item: (
                    item.consumer_pom_locator,
                    item.resolved_dependency_ga,
                    item.declared_dependency_gav_expression,
                ),
            )
        )
        dependency_reports_tuple = tuple(
            sorted(
                dependency_reports,
                key=lambda item: (
                    item.consumer_pom_locator,
                    item.resolved_dependency_ga,
                    item.declared_dependency_gav_expression,
                ),
            )
        )
        report = self._build_report(
            root_entity,
            module_entities,
            relations_tuple,
            coverage,
            dependency_reports_tuple,
            exclusions_tuple,
            tuple(sorted(self._raw_poms)),
        )
        return MavenStructureEvaluation(
            root_project=root_entity,
            modules=module_entities,
            relations=relations_tuple,
            coverage=coverage,
            complete_member_manifest=manifest,
            evidence=evidence_tuple,
            exclusions=exclusions_tuple,
            report=report,
            batch=batch,
        )

    def _discover_modules(self, root: _RawPom) -> tuple[_DiscoveredModule, ...]:
        discovered: list[_DiscoveredModule] = []
        declared_targets: set[str] = set()

        def visit(
            pom: _RawPom,
            ancestry: tuple[str, ...],
            membership_evidence: tuple[str, ...],
        ) -> None:
            for declaration in pom.modules:
                module_expression = self._resolve_required_expression(
                    pom.path,
                    declaration.expression,
                    locator=declaration.locator,
                    field="module path",
                )
                target_path, module_path = self._module_target(
                    pom.path, module_expression, declaration.locator
                )
                if target_path in ancestry:
                    raise MavenStructureError(
                        MavenStructureErrorCode.MODULE_GRAPH_CYCLE,
                        "recursive Maven module declarations form a cycle",
                        locator=declaration.locator,
                    )
                if target_path in declared_targets:
                    raise MavenStructureError(
                        MavenStructureErrorCode.MODULE_CANONICAL_TARGET_DUPLICATE,
                        "multiple module declarations resolve to the same canonical POM",
                        locator=declaration.locator,
                    )
                declared_targets.add(target_path)
                self._require_regular_pom(target_path, module_target=True)
                child = self._raw_pom(target_path)
                child_membership_evidence = (
                    *membership_evidence,
                    declaration.locator,
                )
                discovered.append(
                    _DiscoveredModule(
                        path=target_path,
                        module_path=module_path,
                        declaration_locator=declaration.locator,
                        membership_evidence_locators=child_membership_evidence,
                    )
                )
                visit(
                    child,
                    (*ancestry, target_path),
                    child_membership_evidence,
                )

        visit(root, (self.root_path,), ())
        return tuple(discovered)

    def _module_target(
        self, parent_pom: str, expression: str, locator: str
    ) -> tuple[str, str]:
        if "\\" in expression or expression.startswith("/"):
            raise MavenStructureError(
                MavenStructureErrorCode.MODULE_PATH_ESCAPES_ROOT,
                "module path must be a repository-relative POSIX directory",
                locator=locator,
            )
        candidate_directory = posixpath.normpath(
            posixpath.join(posixpath.dirname(parent_pom), expression)
        )
        if not self._inside_logical_root(candidate_directory):
            raise MavenStructureError(
                MavenStructureErrorCode.MODULE_PATH_ESCAPES_ROOT,
                "module path escapes the logical reactor root directory",
                locator=locator,
            )
        if candidate_directory in ("", "."):
            target = "pom.xml"
            module_path = "."
        else:
            target = f"{candidate_directory}/pom.xml"
            module_path = candidate_directory
        self._reject_symlink_prefix(
            target,
            MavenStructureErrorCode.MODULE_PATH_SYMLINK_UNSUPPORTED,
            locator,
        )
        return target, module_path

    def _inside_logical_root(self, path: str) -> bool:
        if path == ".." or path.startswith("../") or path.startswith("/"):
            return False
        root = self.logical_root_directory
        if not root:
            return True
        return path == root or path.startswith(f"{root}/")

    def _raw_pom(self, path: str) -> _RawPom:
        cached = self._raw_poms.get(path)
        if cached is not None:
            return cached
        payload = self.pom_bytes.get(path)
        if payload is None:
            raise MavenStructureError(
                MavenStructureErrorCode.MODULE_TARGET_MISSING,
                "POM bytes are not present in the exact input",
                locator=path,
            )
        if b"<!DOCTYPE" in payload.upper() or b"<!ENTITY" in payload.upper():
            raise MavenStructureError(
                MavenStructureErrorCode.MALFORMED_POM,
                "DTD and entity declarations are not allowed",
                locator=path,
            )
        try:
            root = ET.fromstring(payload)
        except (ET.ParseError, UnicodeDecodeError) as exc:
            raise MavenStructureError(
                MavenStructureErrorCode.MALFORMED_POM,
                f"POM is not well-formed UTF-8 XML: {exc}",
                locator=path,
            ) from exc
        if root.tag != f"{_NS}project":
            raise MavenStructureError(
                MavenStructureErrorCode.MALFORMED_POM,
                "root element must be Maven 4 project in the frozen namespace",
                locator=path,
            )
        model_version = _single_text(root, "modelVersion", path)
        if model_version != "4.0.0":
            raise MavenStructureError(
                MavenStructureErrorCode.MALFORMED_POM,
                "modelVersion must be exactly 4.0.0",
                locator=path,
            )

        parent_elements = _children(root, "parent")
        if len(parent_elements) > 1:
            self._malformed(path, "project contains duplicate parent elements")
        parent: _RawParent | None = None
        if parent_elements:
            parent_element = parent_elements[0]
            relative_elements = _children(parent_element, "relativePath")
            if len(relative_elements) > 1:
                self._malformed(path, "parent contains duplicate relativePath elements")
            parent = _RawParent(
                group_id=_single_text(parent_element, "groupId", path),
                artifact_id=_single_text(parent_element, "artifactId", path),
                version=_single_text(parent_element, "version", path),
                relative_path_present=bool(relative_elements),
                relative_path=(
                    _leaf_text(relative_elements[0], path)
                    if relative_elements
                    else None
                ),
            )

        modules_elements = _children(root, "modules")
        if len(modules_elements) > 1:
            self._malformed(path, "project contains duplicate modules elements")
        modules: list[_RawModule] = []
        if modules_elements:
            for index, item in enumerate(_children(modules_elements[0], "module"), 1):
                modules.append(
                    _RawModule(
                        expression=_leaf_text(item, path),
                        locator=f"{path}#/project/modules/module[{index}]",
                    )
                )

        properties_elements = _children(root, "properties")
        if len(properties_elements) > 1:
            self._malformed(path, "project contains duplicate properties elements")
        properties: dict[str, str] = {}
        if properties_elements:
            for item in list(properties_elements[0]):
                key = _local_name(item.tag)
                if key in properties:
                    raise MavenStructureError(
                        MavenStructureErrorCode.DUPLICATE_POM_PROPERTY,
                        f"POM declares property {key!r} more than once",
                        locator=path,
                    )
                properties[key] = _leaf_text(item, path) or ""

        dependencies_elements = _children(root, "dependencies")
        if len(dependencies_elements) > 1:
            self._malformed(path, "project contains duplicate dependencies elements")
        dependencies = self._parse_dependencies(
            dependencies_elements[0] if dependencies_elements else None,
            path,
            "dependencies",
        )

        management_elements = _children(root, "dependencyManagement")
        if len(management_elements) > 1:
            self._malformed(path, "project contains duplicate dependencyManagement elements")
        managed_dependencies: tuple[_RawDependency, ...] = ()
        if management_elements:
            nested = _children(management_elements[0], "dependencies")
            if len(nested) > 1:
                self._malformed(
                    path,
                    "dependencyManagement contains duplicate dependencies elements",
                )
            managed_dependencies = self._parse_dependencies(
                nested[0] if nested else None,
                path,
                "dependencyManagement/dependencies",
            )

        profile_has_structural_fields = False
        profile_property_keys: set[str] = set()
        profiles_elements = _children(root, "profiles")
        if len(profiles_elements) > 1:
            self._malformed(path, "project contains duplicate profiles elements")
        if profiles_elements:
            for profile in _children(profiles_elements[0], "profile"):
                if any(
                    _children(profile, name)
                    for name in (
                        "modules",
                        "dependencies",
                        "dependencyManagement",
                        "groupId",
                        "artifactId",
                        "version",
                    )
                ):
                    profile_has_structural_fields = True
                for block in _children(profile, "properties"):
                    profile_property_keys.update(
                        _local_name(item.tag) for item in list(block)
                    )

        raw = _RawPom(
            path=path,
            content_digest=f"sha256:{hashlib.sha256(payload).hexdigest()}",
            group_id=_single_text(root, "groupId", path),
            artifact_id=_single_text(root, "artifactId", path),
            version=_single_text(root, "version", path),
            packaging=_single_text(root, "packaging", path),
            name=_single_text(root, "name", path),
            parent=parent,
            modules=tuple(modules),
            properties=_mapping(properties),
            dependencies=dependencies,
            dependency_management=managed_dependencies,
            profile_has_structural_fields=profile_has_structural_fields,
            profile_property_keys=frozenset(profile_property_keys),
        )
        self._raw_poms[path] = raw
        return raw

    def _parse_dependencies(
        self, element: ET.Element | None, path: str, xml_path: str
    ) -> tuple[_RawDependency, ...]:
        if element is None:
            return ()
        result: list[_RawDependency] = []
        for index, dependency in enumerate(_children(element, "dependency"), 1):
            locator = f"{path}#/project/{xml_path}/dependency[{index}]"
            result.append(
                _RawDependency(
                    group_id=_single_text(dependency, "groupId", locator),
                    artifact_id=_single_text(dependency, "artifactId", locator),
                    version=_single_text(dependency, "version", locator),
                    scope=_single_text(dependency, "scope", locator),
                    type=_single_text(dependency, "type", locator),
                    classifier=_single_text(dependency, "classifier", locator),
                    optional=_single_text(dependency, "optional", locator),
                    locator=locator,
                )
            )
        return tuple(result)

    def _effective_pom(self, path: str) -> _EffectivePom:
        cached = self._effective_poms.get(path)
        if cached is not None:
            return cached
        if path in self._model_stack:
            raise MavenStructureError(
                MavenStructureErrorCode.PARENT_CYCLE,
                "local Maven parent declarations form a cycle",
                locator=path,
            )
        self._model_stack.append(path)
        try:
            raw = self._raw_pom(path)
            link = self._parent_link(path)
            parent_model = (
                self._effective_pom(link.local_path)
                if link.local_path is not None
                else None
            )
            if raw.parent is not None:
                declared_parent = (
                    self._resolve_required_expression(
                        path,
                        raw.parent.group_id,
                        locator=path,
                        field="parent groupId",
                    ),
                    self._resolve_required_expression(
                        path,
                        raw.parent.artifact_id,
                        locator=path,
                        field="parent artifactId",
                    ),
                    self._resolve_required_expression(
                        path,
                        raw.parent.version,
                        locator=path,
                        field="parent version",
                    ),
                )
                self._reject_version_range(declared_parent[2], path)
                if parent_model is not None and declared_parent != parent_model.gav:
                    raise MavenStructureError(
                        MavenStructureErrorCode.LOCAL_PARENT_GAV_MISMATCH,
                        (
                            f"declared parent {_gav_text(declared_parent)} does not match "
                            f"local parent {_gav_text(parent_model.gav)}"
                        ),
                        locator=path,
                    )

            group_id = self._project_field(path, "group_id")
            artifact_id = self._project_field(path, "artifact_id")
            version = self._project_field(path, "version")
            self._reject_version_range(version, path)
            packaging = self._resolve_optional_expression(
                path,
                raw.packaging,
                default="jar",
                locator=path,
                field="packaging",
            )
            name = self._resolve_optional_expression(
                path,
                raw.name,
                default=artifact_id,
                locator=path,
                field="project name",
            )
            model = _EffectivePom(
                path=path,
                group_id=group_id,
                artifact_id=artifact_id,
                version=version,
                packaging=packaging,
                label=name,
                local_parent_path=link.local_path,
                has_external_parent=(
                    link.external
                    or (parent_model.has_external_parent if parent_model else False)
                ),
            )
            self._effective_poms[path] = model
            return model
        finally:
            self._model_stack.pop()

    def _project_field(self, path: str, field: str) -> str:
        cache_key = (path, field)
        cached = self._field_cache.get(cache_key)
        if cached is not None:
            return cached
        if cache_key in self._field_stack:
            raise MavenStructureError(
                MavenStructureErrorCode.PROPERTY_CYCLE,
                f"project alias expansion cycles through {field}",
                locator=path,
            )
        self._field_stack.append(cache_key)
        try:
            raw = self._raw_pom(path)
            expression: str | None
            if field == "group_id":
                expression = raw.group_id
                if expression is None and raw.parent is not None:
                    expression = raw.parent.group_id
                label = "project groupId"
            elif field == "artifact_id":
                expression = raw.artifact_id
                label = "project artifactId"
            elif field == "version":
                expression = raw.version
                if expression is None and raw.parent is not None:
                    expression = raw.parent.version
                label = "project version"
            else:  # pragma: no cover - internal programming error
                raise AssertionError(field)
            result = self._resolve_required_expression(
                path, expression, locator=path, field=label
            )
            self._field_cache[cache_key] = result
            return result
        finally:
            self._field_stack.pop()

    def _parent_link(self, path: str) -> _ParentLink:
        cached = self._parent_links.get(path)
        if cached is not None:
            return cached
        raw = self._raw_pom(path)
        if raw.parent is None:
            link = _ParentLink(local_path=None, external=False)
            self._parent_links[path] = link
            return link
        if raw.parent.relative_path_present and raw.parent.relative_path in (None, ""):
            link = _ParentLink(local_path=None, external=True)
            self._parent_links[path] = link
            return link
        relative_path = raw.parent.relative_path or "../pom.xml"
        if "\\" in relative_path or relative_path.startswith("/"):
            link = _ParentLink(local_path=None, external=True)
            self._parent_links[path] = link
            return link
        candidate = posixpath.normpath(
            posixpath.join(posixpath.dirname(path), relative_path)
        )
        if not self._inside_logical_root(candidate):
            link = _ParentLink(local_path=None, external=True)
            self._parent_links[path] = link
            return link
        candidates = (candidate, f"{candidate}/pom.xml")
        local_path = next(
            (item for item in candidates if item in self.pom_bytes), None
        )
        symlink_probe = local_path or candidate
        self._reject_symlink_prefix(
            symlink_probe,
            MavenStructureErrorCode.LOCAL_PARENT_SYMLINK_UNSUPPORTED,
            path,
        )
        if local_path is None:
            link = _ParentLink(local_path=None, external=True)
        else:
            self._require_regular_pom(local_path, module_target=False)
            link = _ParentLink(local_path=local_path, external=False)
        self._parent_links[path] = link
        return link

    def _local_parent_chain(self, path: str) -> tuple[str, ...]:
        """Return only the local POMs that participate in this effective model."""

        chain: list[str] = []
        seen: set[str] = set()
        current = path
        while current not in seen:
            seen.add(current)
            chain.append(current)
            link = self._parent_link(current)
            if link.local_path is None:
                return tuple(chain)
            current = link.local_path
        raise MavenStructureError(
            MavenStructureErrorCode.PARENT_CYCLE,
            "local Maven parent declarations form a cycle",
            locator=path,
        )

    def _reject_structural_profiles(self) -> None:
        for path in sorted(self._raw_poms):
            if self._raw_poms[path].profile_has_structural_fields:
                raise MavenStructureError(
                    MavenStructureErrorCode.RELEVANT_PROFILE_UNSUPPORTED,
                    "POM contains a profile that can affect frozen structure fields",
                    locator=path,
                )

    def _resolve_required_expression(
        self,
        path: str,
        expression: str | None,
        *,
        locator: str,
        field: str,
    ) -> str:
        if expression is None:
            raise MavenStructureError(
                MavenStructureErrorCode.REQUIRED_PROPERTY_UNRESOLVED,
                f"required {field} is absent",
                locator=locator,
            )
        result = self._expand_expression(
            path, expression, locator=locator, property_stack=(), depth=0
        )
        return _canonical_text(result, field, locator)

    def _resolve_optional_expression(
        self,
        path: str,
        expression: str | None,
        *,
        default: str | None,
        locator: str,
        field: str,
    ) -> str | None:
        if expression is None:
            return default
        result = self._expand_expression(
            path, expression, locator=locator, property_stack=(), depth=0
        )
        return _canonical_text(result, field, locator)

    def _expand_expression(
        self,
        path: str,
        expression: str,
        *,
        locator: str,
        property_stack: tuple[tuple[str, str], ...],
        depth: int,
    ) -> str:
        if depth > _MAX_PROPERTY_EXPANSIONS:
            raise MavenStructureError(
                MavenStructureErrorCode.PROPERTY_EXPANSION_LIMIT,
                "property interpolation exceeds the frozen expansion limit",
                locator=locator,
            )
        matches = tuple(_PROPERTY_REFERENCE.finditer(expression))
        if not matches:
            return expression
        chunks: list[str] = []
        cursor = 0
        for match in matches:
            chunks.append(expression[cursor : match.start()])
            chunks.append(
                self._property_value(
                    path,
                    match.group(1),
                    locator=locator,
                    property_stack=property_stack,
                    depth=depth + 1,
                )
            )
            cursor = match.end()
        chunks.append(expression[cursor:])
        expanded = "".join(chunks)
        return self._expand_expression(
            path,
            expanded,
            locator=locator,
            property_stack=property_stack,
            depth=depth + 1,
        )

    def _property_value(
        self,
        path: str,
        key: str,
        *,
        locator: str,
        property_stack: tuple[tuple[str, str], ...],
        depth: int,
    ) -> str:
        key = _canonical_text(key, "property name", locator)
        if key.startswith(("env.", "settings.", "system.", "user.")):
            raise MavenStructureError(
                MavenStructureErrorCode.DISALLOWED_PROPERTY_SOURCE,
                f"property source {key!r} is disabled by the evaluation context",
                locator=locator,
            )
        aliases = {
            "project.groupId": "group_id",
            "pom.groupId": "group_id",
            "project.artifactId": "artifact_id",
            "pom.artifactId": "artifact_id",
            "project.version": "version",
            "pom.version": "version",
        }
        if key in aliases:
            return self._project_field(path, aliases[key])
        parent_aliases = {
            "project.parent.groupId": "group_id",
            "project.parent.artifactId": "artifact_id",
            "project.parent.version": "version",
        }
        if key in parent_aliases:
            raw = self._raw_pom(path)
            if raw.parent is None:
                self._unresolved_property(path, key, locator)
            parent_expression = getattr(raw.parent, parent_aliases[key])
            return self._resolve_required_expression(
                path,
                parent_expression,
                locator=locator,
                field=key,
            )

        marker = (path, key)
        if marker in property_stack:
            raise MavenStructureError(
                MavenStructureErrorCode.PROPERTY_CYCLE,
                f"property interpolation cycle includes {key!r}",
                locator=locator,
            )
        raw = self._raw_pom(path)
        if key in raw.profile_property_keys:
            raise MavenStructureError(
                MavenStructureErrorCode.RELEVANT_PROFILE_UNSUPPORTED,
                (
                    f"profile property {key!r} can affect a field required by "
                    "the frozen structure evaluation"
                ),
                locator=locator,
            )
        if key in raw.properties:
            return self._expand_expression(
                path,
                raw.properties[key],
                locator=locator,
                property_stack=(*property_stack, marker),
                depth=depth,
            )
        parent = self._parent_link(path)
        if parent.local_path is not None:
            return self._property_value(
                parent.local_path,
                key,
                locator=locator,
                property_stack=(*property_stack, marker),
                depth=depth,
            )
        self._unresolved_property(path, key, locator)

    def _unresolved_property(self, path: str, key: str, locator: str) -> None:
        if self._has_external_parent(path):
            raise MavenStructureError(
                MavenStructureErrorCode.EXTERNAL_PARENT_REQUIRED,
                (
                    f"property {key!r} is unavailable and resolving it could require "
                    "disabled external parent content"
                ),
                locator=locator,
            )
        raise MavenStructureError(
            MavenStructureErrorCode.REQUIRED_PROPERTY_UNRESOLVED,
            f"required property {key!r} is not defined in the reactor parent chain",
            locator=locator,
        )

    def _has_external_parent(self, path: str) -> bool:
        seen: set[str] = set()
        current = path
        while current not in seen:
            seen.add(current)
            link = self._parent_link(current)
            if link.external:
                return True
            if link.local_path is None:
                return False
            current = link.local_path
        raise MavenStructureError(
            MavenStructureErrorCode.PARENT_CYCLE,
            "local Maven parent declarations form a cycle",
            locator=path,
        )

    def _managed_dependency(
        self, consumer_path: str, ga: tuple[str, str]
    ) -> _RawDependency | None:
        seen_paths: set[str] = set()
        current = consumer_path
        while current not in seen_paths:
            seen_paths.add(current)
            raw = self._raw_pom(current)
            matches: list[_RawDependency] = []
            seen_ga: set[tuple[str, str]] = set()
            for dependency in raw.dependency_management:
                managed_group = self._resolve_required_expression(
                    consumer_path,
                    dependency.group_id,
                    locator=dependency.locator,
                    field="managed dependency groupId",
                )
                managed_artifact = self._resolve_required_expression(
                    consumer_path,
                    dependency.artifact_id,
                    locator=dependency.locator,
                    field="managed dependency artifactId",
                )
                managed_ga = (managed_group, managed_artifact)
                if managed_ga in seen_ga:
                    raise MavenStructureError(
                        MavenStructureErrorCode.DUPLICATE_DEPENDENCY_MANAGEMENT_GA,
                        f"dependencyManagement repeats canonical GA {_ga_text(managed_ga)}",
                        locator=dependency.locator,
                    )
                seen_ga.add(managed_ga)
                if managed_ga == ga:
                    matches.append(dependency)
            if matches:
                return matches[0]
            link = self._parent_link(current)
            if link.local_path is None:
                return None
            current = link.local_path
        raise MavenStructureError(
            MavenStructureErrorCode.PARENT_CYCLE,
            "local Maven parent declarations form a cycle",
            locator=consumer_path,
        )

    def _has_external_bom(self, path: str) -> bool:
        seen: set[str] = set()
        current = path
        while current not in seen:
            seen.add(current)
            raw = self._raw_pom(current)
            for dependency in raw.dependency_management:
                type_value = dependency.type or "jar"
                scope_value = dependency.scope or "compile"
                if type_value == "pom" and scope_value == "import":
                    return True
            link = self._parent_link(current)
            if link.local_path is None:
                return False
            current = link.local_path
        return False

    def _reject_version_range(self, version: str, locator: str) -> None:
        if version.startswith(("[", "(")):
            raise MavenStructureError(
                MavenStructureErrorCode.VERSION_RANGE_UNSUPPORTED,
                f"version range {version!r} is outside the frozen exact-version subset",
                locator=locator,
            )

    def _require_regular_pom(self, path: str, *, module_target: bool) -> None:
        if path not in self.pom_bytes:
            code = (
                MavenStructureErrorCode.MODULE_TARGET_MISSING
                if module_target
                else MavenStructureErrorCode.ROOT_POM_MISSING
            )
            raise MavenStructureError(
                code,
                "target POM bytes are absent from the exact input",
                locator=path,
            )
        metadata = self.git_entries.get(path)
        if metadata is None:
            raise MavenStructureError(
                MavenStructureErrorCode.POM_ENTRY_METADATA_MISSING,
                "target POM has no exact Git entry metadata",
                locator=path,
            )
        if not metadata.is_regular_file:
            raise MavenStructureError(
                MavenStructureErrorCode.POM_ENTRY_NOT_REGULAR_FILE,
                "target POM must be an exact-revision regular blob",
                locator=path,
            )

    def _reject_symlink_prefix(
        self,
        path: str,
        code: MavenStructureErrorCode,
        locator: str,
    ) -> None:
        parts = path.split("/")
        for index in range(1, len(parts) + 1):
            prefix = "/".join(parts[:index])
            metadata = self.git_entries.get(prefix)
            if metadata is not None and metadata.is_symlink:
                raise MavenStructureError(
                    code,
                    f"path traverses Git symlink entry {prefix!r}",
                    locator=locator,
                )

    def _pom_evidence(self, path: str) -> StructureEvidence:
        cached = self._evidence_by_path.get(path)
        if cached is not None:
            return cached
        raw = self._raw_pom(path)
        metadata = self.pom_evidence.get(path)
        if metadata is None:
            raise MavenStructureError(
                MavenStructureErrorCode.POM_EVIDENCE_MISSING,
                "consumed POM has no exact source Evidence metadata",
                locator=path,
            )
        if metadata.artifact_content_digest.value != raw.content_digest:
            raise MavenStructureError(
                MavenStructureErrorCode.POM_CONTENT_DIGEST_MISMATCH,
                "POM bytes do not match the source Artifact content digest",
                locator=path,
            )
        try:
            excerpt = self.pom_bytes[path].decode("utf-8")
        except UnicodeDecodeError as exc:
            raise MavenStructureError(
                MavenStructureErrorCode.MALFORMED_POM,
                "POM Evidence excerpt must be exact UTF-8",
                locator=path,
            ) from exc
        evidence = StructureEvidence.create(
            artifact_id=metadata.artifact_id,
            source_context_id=metadata.source_context_id,
            byte_start=0,
            byte_end=len(self.pom_bytes[path]),
            locator=metadata.locator,
            excerpt=excerpt,
            artifact_content_digest=metadata.artifact_content_digest,
        )
        self._evidence_by_path[path] = evidence
        return evidence

    def _pom_evidence_references(
        self, *path_groups: Sequence[str]
    ) -> tuple[StableId, ...]:
        references = {
            self._pom_evidence(path).evidence_id
            for paths in path_groups
            for path in paths
        }
        return tuple(sorted(references, key=lambda item: item.value))

    def _entity_record(
        self,
        *,
        entity_type: str,
        root_fields: Mapping[str, Any],
        state_payload: Mapping[str, Any],
    ) -> EntityRecord:
        root = EntityRoot.create(
            entity_type=EntityType(entity_type),
            owning_scope_id=self.scope_id,
            identity_fields=root_fields,
        )
        state = EntityState.create(
            root=root,
            state_payload_fields=state_payload,
        )
        return EntityRecord(root=root, state=state)

    def _relation_candidate(
        self,
        *,
        subject: EntityRecord,
        predicate: str,
        object_: EntityRecord,
        observation_modality: str,
        evidence_references: Sequence[StableId],
        predicate_payload: Mapping[str, Any],
    ) -> RelationFactRecord:
        root = RelationFactRoot.create(
            owning_scope_id=self.scope_id,
            subject=subject.root.ref,
            predicate=RelationPredicate(predicate),
            object=object_.root.ref,
            observation_modality=ObservationModality(observation_modality),
            schema_ref=SCHEMA_REF,
        )
        state = RelationFactState.create(
            root=root,
            subject_state=subject.state,
            object_state=object_.state,
            source_revision=self.source_revision,
            knowledge_context_digest=self.knowledge_context_digest,
            evidence_references=evidence_references,
            predicate_state_payload_fields=predicate_payload,
        )
        return RelationFactRecord(root=root, state=state)

    def _coverage_candidate(
        self,
        manifest: CompleteMemberManifest,
        evidence_references: tuple[StableId, ...],
    ) -> CoverageRecord:
        root = CoverageRoot.create(
            owning_scope_id=self.scope_id,
            source_binding_id=self.source_binding_id,
            logical_reactor_root=self.root_path,
            profile_ref=PROFILE_REF,
            schema_ref=SCHEMA_REF,
            schema_digest=Digest(SCHEMA_DIGEST),
            maven_evaluation_context_ref=EVALUATION_CONTEXT_REF,
            maven_evaluation_context_digest=Digest(EVALUATION_CONTEXT_DIGEST),
            covered_entity_types=(EntityType.MAVEN_MODULE, EntityType.SOFTWARE_SYSTEM),
            covered_relation_predicates=(
                RelationPredicate.CONTAINS_MODULE,
                RelationPredicate.DEPENDS_ON,
            ),
            canonicalization_ref=CANONICALIZATION_REF,
            canonicalization_digest=Digest(CANONICALIZATION_DIGEST),
            coverage_root_ref=COVERAGE_ROOT_REF,
        )
        state = CoverageState.create(
            root=root,
            source_revision=self.source_revision,
            knowledge_context_digest=self.knowledge_context_digest,
            complete_member_manifest=manifest,
            evidence_references=evidence_references,
        )
        return CoverageRecord(root=root, state=state)

    def _exclusion(
        self,
        consumer_path: str,
        dependency: _RawDependency,
        ga: tuple[str, str],
        *,
        version: str | None,
        target_gav: str | None,
        reason: str,
        evidence_references: Sequence[StableId],
    ) -> BuildExclusion:
        return BuildExclusion(
            consumer_pom_locator=consumer_path,
            declared_dependency_gav_expression=dependency.expression,
            resolved_dependency_ga=_ga_text(ga),
            resolved_dependency_version_or_null=version,
            matched_reactor_target_gav_or_null=target_gav,
            decision="EXCLUDED",
            reason_code=reason,
            evidence_references=tuple(
                item.value for item in evidence_references
            ),
        )

    @staticmethod
    def _dependency_report_from_exclusion(
        consumer: _EffectivePom, exclusion: BuildExclusion
    ) -> DependencyEvaluation:
        return DependencyEvaluation(
            consumer_pom_locator=exclusion.consumer_pom_locator,
            consumer_gav=_gav_text(consumer.gav),
            declared_dependency_gav_expression=(
                exclusion.declared_dependency_gav_expression
            ),
            resolved_dependency_ga=exclusion.resolved_dependency_ga,
            resolved_dependency_version_or_null=(
                exclusion.resolved_dependency_version_or_null
            ),
            matched_reactor_target_gav_or_null=(
                exclusion.matched_reactor_target_gav_or_null
            ),
            decision=exclusion.decision,
            reason_code=exclusion.reason_code,
            evidence_references=exclusion.evidence_references,
        )

    def _build_report(
        self,
        root: EntityRecord,
        modules: tuple[EntityRecord, ...],
        relations: tuple[RelationFactRecord, ...],
        coverage: CoverageRecord,
        dependencies: tuple[DependencyEvaluation, ...],
        exclusions: tuple[BuildExclusion, ...],
        scanned_poms: tuple[str, ...],
    ) -> BuildReport:
        evidence_locators = {
            item.evidence_id.value: item.locator
            for item in (*self.tree_evidence, *self._evidence_by_path.values())
        }

        def rendered_locators(references: Sequence[StableId]) -> str:
            return ",".join(
                evidence_locators[reference.value] for reference in references
            )

        lines = [
            (
                f"ROOT type={root.root.entity_type.value} root={root.root_id.value} "
                f"state={root.state_id.value} state_digest={root.state_digest.value} "
                f"locator={self.root_path} "
                f"evidence={rendered_locators(root.state.evidence_references)}"
            )
        ]
        for module in modules:
            lines.append(
                (
                    f"MODULE ga={module.root.root_fields['effective_group_id']}:"
                    f"{module.root.root_fields['artifact_id']} root={module.root_id.value} "
                    f"state={module.state_id.value} "
                    f"state_digest={module.state_digest.value} "
                    f"path={module.state.state_payload_fields['module_path']} "
                    f"evidence={rendered_locators(module.state.evidence_references)}"
                )
            )
        for relation in relations:
            lines.append(
                (
                    f"RELATION predicate={relation.root.predicate.value} "
                    f"source={relation.root.subject.entity_root_id.value} "
                    f"target={relation.root.object.entity_root_id.value} "
                    f"root={relation.root_id.value} state={relation.state_id.value} "
                    f"state_digest={relation.state_digest.value} "
                    f"evidence={rendered_locators(relation.state.evidence_references)}"
                )
            )
        for dependency in dependencies:
            locators = ",".join(
                evidence_locators[reference]
                for reference in dependency.evidence_references
            )
            lines.append(
                (
                    f"DEPENDENCY consumer={dependency.consumer_gav} "
                    f"declared={dependency.declared_dependency_gav_expression} "
                    f"resolved_ga={dependency.resolved_dependency_ga} "
                    f"resolved_version={dependency.resolved_dependency_version_or_null} "
                    f"decision={dependency.decision} reason={dependency.reason_code} "
                    f"evidence={locators}"
                )
            )
        lines.append(
            (
                f"COVERAGE root={coverage.root_id.value} state={coverage.state_id.value} "
                f"state_digest={coverage.state.state_digest.value} "
                f"status=COMPLETE members={len(coverage.state.complete_member_manifest.members)} "
                f"mode={PUBLICATION_MODE} "
                f"evidence={rendered_locators(coverage.state.evidence_references)}"
            )
        )
        return BuildReport(
            schema_ref=SCHEMA_REF,
            evaluation_context_ref=EVALUATION_CONTEXT_REF,
            canonicalization_ref=CANONICALIZATION_REF,
            source_revision=self.source_revision,
            scanned_pom_locators=scanned_poms,
            dependency_declarations=dependencies,
            exclusions=exclusions,
            complete=True,
            lines=tuple(lines),
        )

    @staticmethod
    def _malformed(path: str, detail: str) -> None:
        raise MavenStructureError(
            MavenStructureErrorCode.MALFORMED_POM, detail, locator=path
        )


def _mapping(value: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType(dict(value))


def _ga_text(ga: tuple[str, str]) -> str:
    return f"{ga[0]}:{ga[1]}"


def _gav_text(gav: tuple[str, str, str]) -> str:
    return f"{gav[0]}:{gav[1]}:{gav[2]}"


def _input_text(value: object, label: str) -> str:
    if not isinstance(value, str):
        raise MavenStructureError(
            MavenStructureErrorCode.INVALID_INPUT, f"{label} must be a string"
        )
    return _canonical_text(value, label, None)


def _input_path(value: object) -> str:
    text = _input_text(value, "repository-relative path")
    if "\\" in text or text.startswith("/"):
        raise MavenStructureError(
            MavenStructureErrorCode.INVALID_INPUT,
            "repository paths must be relative POSIX paths",
            locator=text,
        )
    normalized = posixpath.normpath(text)
    if normalized in ("", ".", "..") or normalized.startswith("../"):
        raise MavenStructureError(
            MavenStructureErrorCode.INVALID_INPUT,
            "repository path escapes or does not identify a file",
            locator=text,
        )
    return normalized


def _canonical_text(value: str, label: str, locator: str | None) -> str:
    normalized = unicodedata.normalize("NFC", value.strip())
    if not normalized:
        raise MavenStructureError(
            MavenStructureErrorCode.REQUIRED_PROPERTY_UNRESOLVED,
            f"{label} cannot be empty",
            locator=locator,
        )
    if any(unicodedata.category(character) in {"Cc", "Cf"} for character in normalized):
        raise MavenStructureError(
            MavenStructureErrorCode.MALFORMED_POM,
            f"{label} contains a control character",
            locator=locator,
        )
    return normalized


def _children(element: ET.Element, name: str) -> list[ET.Element]:
    return list(element.findall(f"{_NS}{name}"))


def _single_text(element: ET.Element, name: str, locator: str) -> str | None:
    values = _children(element, name)
    if len(values) > 1:
        raise MavenStructureError(
            MavenStructureErrorCode.MALFORMED_POM,
            f"element contains duplicate {name} children",
            locator=locator,
        )
    return _leaf_text(values[0], locator) if values else None


def _leaf_text(element: ET.Element, locator: str) -> str:
    if list(element):
        raise MavenStructureError(
            MavenStructureErrorCode.MALFORMED_POM,
            "structure values must be plain XML text",
            locator=locator,
        )
    return unicodedata.normalize("NFC", (element.text or "").strip())


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _unique_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


__all__ = [
    "BuildExclusion",
    "BuildReport",
    "CANONICALIZATION_DIGEST",
    "CANONICALIZATION_REF",
    "DependencyEvaluation",
    "EVALUATION_CONTEXT_DIGEST",
    "EVALUATION_CONTEXT_REF",
    "GitEntryMetadata",
    "MavenEvaluationInput",
    "MavenReactorEvaluationInput",
    "MavenStructureError",
    "MavenStructureErrorCode",
    "MavenStructureEvaluation",
    "MavenStructureEvaluator",
    "PomEvidenceMetadata",
    "PROFILE_REF",
    "PUBLICATION_MODE",
    "SCHEMA_DIGEST",
    "SCHEMA_REF",
    "evaluate_maven_reactor",
]
