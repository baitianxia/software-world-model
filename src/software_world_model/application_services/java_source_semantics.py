"""Deterministic Java implementation-semantics candidate for ITER-007.

The frontend is tree-sitter Java with an exact runtime identity.  The emitted
knowledge is a deliberately small typed projection: declaration and legacy
``CALLS`` semantics remain exact, while method bodies contribute only bounded
branch/call/return/throw atoms and their direct structural relations.  Source
bytes and parser nodes never enter Entity or Fact state.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from importlib.metadata import distribution
from pathlib import PurePosixPath
import hashlib
import json
import re

from tree_sitter import Language, Node, Parser
import tree_sitter_java

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
    JAVA_SOURCE_SEMANTICS_CANONICALIZATION_DIGEST,
    JAVA_SOURCE_SEMANTICS_CANONICALIZATION_REF,
    JAVA_SOURCE_SEMANTICS_COVERAGE_ROOT_REF,
    JAVA_SOURCE_SEMANTICS_ENTITY_TYPES,
    JAVA_SOURCE_SEMANTICS_EVALUATION_CONTEXT_DIGEST,
    JAVA_SOURCE_SEMANTICS_EVALUATION_CONTEXT_REF,
    JAVA_SOURCE_SEMANTICS_FRONTEND_DIGEST,
    JAVA_SOURCE_SEMANTICS_FRONTEND_REF,
    JAVA_SOURCE_SEMANTICS_PROFILE_REF,
    JAVA_SOURCE_SEMANTICS_RELATION_PREDICATES,
    JAVA_SOURCE_SEMANTICS_SCHEMA_DIGEST,
    JAVA_SOURCE_SEMANTICS_SCHEMA_REF,
    JavaCallResolutionClass,
    JavaImplementationAtomKind,
    JavaSemanticDisposition,
    JavaSemanticFacetCompleteness,
    JavaSemanticForm,
    JavaSemanticOperandKind,
    JavaSemanticOperator,
    JavaStateSlotKind,
    JavaValueCategory,
    ObservationModality,
    PublicationMode,
    RelationFactRecord,
    RelationFactRoot,
    RelationFactState,
    RelationPredicate,
    StructureEvidence,
    StructureKnowledgeBatch,
)

from .java_static_call import (
    JavaSourceEvidenceMetadata,
    JavaStaticCallError,
    JavaStaticCallEvaluation,
    JavaStaticCallInput,
    evaluate_java_static_calls,
)
from .maven_structure import GitEntryMetadata


SCHEMA_REF = JAVA_SOURCE_SEMANTICS_SCHEMA_REF
SCHEMA_DIGEST = JAVA_SOURCE_SEMANTICS_SCHEMA_DIGEST
PROFILE_REF = JAVA_SOURCE_SEMANTICS_PROFILE_REF
COVERAGE_ROOT_REF = JAVA_SOURCE_SEMANTICS_COVERAGE_ROOT_REF
EVALUATION_CONTEXT_REF = JAVA_SOURCE_SEMANTICS_EVALUATION_CONTEXT_REF
EVALUATION_CONTEXT_DIGEST = JAVA_SOURCE_SEMANTICS_EVALUATION_CONTEXT_DIGEST
CANONICALIZATION_REF = JAVA_SOURCE_SEMANTICS_CANONICALIZATION_REF
CANONICALIZATION_DIGEST = JAVA_SOURCE_SEMANTICS_CANONICALIZATION_DIGEST
FRONTEND_REF = JAVA_SOURCE_SEMANTICS_FRONTEND_REF
FRONTEND_DIGEST = JAVA_SOURCE_SEMANTICS_FRONTEND_DIGEST

EXPECTED_COMPONENTS = (
    (
        "tree-sitter",
        "0.25.2",
        "sha256:86952fb273226021793f76c972d782b66c308d3ef8d20a4df4dd5ad6d31ec45c",
    ),
    (
        "tree-sitter-java",
        "0.23.5",
        "sha256:33106942ffed3b3df935320ac8ac9499e453ce66730a2130ba81b2dffef7c9dc",
    ),
)
EXPECTED_LANGUAGE_ABI = 14
_FULL_GIT_OBJECT = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
_JAVA_IDENTIFIER = re.compile(r"^[A-Za-z_$][A-Za-z0-9_$]*$")
_MODIFIERS = {
    "public",
    "protected",
    "private",
    "static",
    "final",
    "synchronized",
    "strictfp",
}
_VISIBILITY = {"public", "protected", "private"}
_JAVA_LANG_TYPES = {
    "Boolean",
    "Byte",
    "Character",
    "Class",
    "Double",
    "Exception",
    "Float",
    "IllegalArgumentException",
    "IllegalStateException",
    "Integer",
    "Long",
    "NullPointerException",
    "Object",
    "RuntimeException",
    "Short",
    "String",
    "Throwable",
}
_ATOM_NODE_TYPES = {
    "if_statement",
    "method_invocation",
    "return_statement",
    "throw_statement",
}


class JavaSourceSemanticsError(ValueError):
    """Profile rejection with a stable machine reason and exact locator."""

    def __init__(self, reason_code: str, message: str, *, locator: str) -> None:
        super().__init__(message)
        self.reason_code = reason_code
        self.locator = locator


@dataclass(frozen=True, slots=True)
class JavaSourceSemanticsInput:
    owning_scope_id: StableId
    source_binding_id: StableId
    source_revision: str
    knowledge_context_digest: Digest
    source_bytes: Mapping[str, bytes]
    git_entries: Mapping[str, GitEntryMetadata]
    source_evidence: Mapping[str, JavaSourceEvidenceMetadata]
    tree_evidence: tuple[StructureEvidence, ...]
    logical_source_root: str


@dataclass(frozen=True, slots=True)
class JavaSourceSemanticsBuildReport:
    complete: bool
    source_revision: str
    source_root: str
    schema_ref: str
    schema_digest: Digest
    frontend_ref: str
    frontend_digest: Digest
    language_abi: int
    evaluation_context_ref: str
    evaluation_context_digest: Digest
    canonicalization_ref: str
    canonicalization_digest: Digest
    source_file_count: int
    type_count: int
    method_count: int
    state_slot_count: int
    implementation_atom_count: int
    declaration_count: int
    legacy_call_relation_count: int
    legacy_call_site_count: int


@dataclass(frozen=True, slots=True)
class JavaSourceSemanticsEvaluation:
    source_files: tuple[EntityRecord, ...]
    types: tuple[EntityRecord, ...]
    methods: tuple[EntityRecord, ...]
    state_slots: tuple[EntityRecord, ...]
    implementation_atoms: tuple[EntityRecord, ...]
    relations: tuple[RelationFactRecord, ...]
    coverage: CoverageRecord
    complete_member_manifest: CompleteMemberManifest
    evidence: tuple[StructureEvidence, ...]
    report: JavaSourceSemanticsBuildReport
    batch: StructureKnowledgeBatch

    @property
    def entities(self) -> tuple[EntityRecord, ...]:
        return (
            *self.source_files,
            *self.types,
            *self.methods,
            *self.state_slots,
            *self.implementation_atoms,
        )


@dataclass(frozen=True, slots=True)
class _ParsedParameter:
    name: str
    declared_type: str
    ordinal: int
    byte_start: int
    byte_end: int


@dataclass(frozen=True, slots=True)
class _ParsedMethod:
    declaring_type: str
    name: str
    parameter_types: tuple[str, ...]
    parameters: tuple[_ParsedParameter, ...]
    return_type: str
    visibility: str
    modifiers: tuple[str, ...]
    source_path: str
    declaration_ordinal: int
    header_start: int
    header_end: int
    body: Node

    @property
    def signature(self) -> str:
        return (
            f"{self.declaring_type}#{self.name}"
            f"({','.join(self.parameter_types)})"
        )


@dataclass(frozen=True, slots=True)
class _ParsedType:
    qualified_name: str
    simple_name: str
    package_name: str
    source_path: str
    header_start: int
    header_end: int
    imports: tuple[tuple[str, str], ...]
    methods: tuple[_ParsedMethod, ...]


@dataclass(frozen=True, slots=True)
class _PendingAtom:
    method_signature: str
    kind: JavaImplementationAtomKind
    ordinal: int
    byte_start: int
    byte_end: int
    evidence_kind: str
    semantic_form: JavaSemanticForm
    operator: JavaSemanticOperator
    value_category: JavaValueCategory
    operands: tuple[tuple[JavaSemanticOperandKind, object], ...]
    referenced_signatures: tuple[str, ...] = ()
    referenced_slot_names: tuple[str, ...] = ()
    control_parent_ordinal: int | None = None
    control_true_branch: bool = True


class JavaSourceSemanticsEvaluator:
    def evaluate(
        self, value: JavaSourceSemanticsInput
    ) -> JavaSourceSemanticsEvaluation:
        return _EvaluationState(value).evaluate()


def evaluate_java_source_semantics(
    value: JavaSourceSemanticsInput,
) -> JavaSourceSemanticsEvaluation:
    return JavaSourceSemanticsEvaluator().evaluate(value)


class _EvaluationState:
    def __init__(self, value: JavaSourceSemanticsInput) -> None:
        self.scope_id = value.owning_scope_id
        self.binding_id = value.source_binding_id
        self.source_revision = _text(value.source_revision, "source revision")
        self.knowledge_context_digest = value.knowledge_context_digest
        self.source_root = _path(value.logical_source_root, "Java source root")
        self.source_bytes = {
            _path(path, "Java source path"): payload
            for path, payload in value.source_bytes.items()
        }
        self.git_entries = {
            _path(path, "Git tree path"): metadata
            for path, metadata in value.git_entries.items()
        }
        self.source_evidence = {
            _path(path, "Java Evidence path"): metadata
            for path, metadata in value.source_evidence.items()
        }
        self.tree_evidence = tuple(value.tree_evidence)
        self.language = _frozen_language()
        self.parser = Parser(self.language)
        self._validate_input()

    def evaluate(self) -> JavaSourceSemanticsEvaluation:
        # The accepted ITER-006 evaluator is retained only as an independent
        # consistency facet for declaration keys and exact CALLS.  It is not a
        # parser fallback: tree-sitter parses and validates every source first.
        parsed_types = tuple(
            self._parse_compilation_unit(path, self.source_bytes[path])
            for path in sorted(self.source_bytes)
        )
        legacy = self._legacy_evaluation()
        legacy_types = {_type_name(item): item for item in legacy.types}
        legacy_methods = {_method_signature(item): item for item in legacy.methods}
        parsed_methods = {
            method.signature: method
            for parsed_type in parsed_types
            for method in parsed_type.methods
        }
        if set(legacy_types) != {item.qualified_name for item in parsed_types}:
            self._fail(
                "JAVA_LEGACY_DECLARATION_CONSISTENCY_FAILED",
                "tree-sitter type closure differs from accepted legacy declarations",
                self.source_root,
            )
        if set(legacy_methods) != set(parsed_methods):
            self._fail(
                "JAVA_LEGACY_DECLARATION_CONSISTENCY_FAILED",
                "tree-sitter method closure differs from accepted legacy declarations",
                self.source_root,
            )

        evidence: dict[StableId, StructureEvidence] = {
            item.evidence_id: item for item in self.tree_evidence
        }
        legacy_evidence = {item.evidence_id: item for item in legacy.evidence}
        evidence.update(legacy_evidence)

        source_files: dict[str, EntityRecord] = {}
        for path in sorted(self.source_bytes):
            support = self._evidence(path, 0, len(self.source_bytes[path]), "java-source-file")
            evidence[support.evidence_id] = support
            root = EntityRoot.java_source_file(
                owning_scope_id=self.scope_id,
                source_path=path,
            )
            source_files[path] = EntityRecord(
                root,
                EntityState.create(
                    root=root,
                    state_payload_fields={
                        "source_revision": self.source_revision,
                        "disposition": JavaSemanticDisposition.SEMANTICS_COMPLETE,
                        "evidence_references": (support.evidence_id,),
                    },
                ),
            )

        types: dict[str, EntityRecord] = {}
        for qualified_name, legacy_record in sorted(legacy_types.items()):
            payload = legacy_record.state.state_payload_fields
            root = EntityRoot.java_type(
                owning_scope_id=self.scope_id,
                qualified_name=qualified_name,
            )
            types[qualified_name] = EntityRecord(
                root,
                EntityState.create(
                    root=root,
                    state_payload_fields={
                        **payload.as_dict(),
                        "evidence_references": legacy_record.state.evidence_references,
                        "disposition": JavaSemanticDisposition.SEMANTICS_COMPLETE,
                    },
                ),
            )

        methods: dict[str, EntityRecord] = {}
        for signature, legacy_record in sorted(legacy_methods.items()):
            root_fields = legacy_record.root.root_fields
            root = EntityRoot.java_method(
                owning_scope_id=self.scope_id,
                declaring_type_qualified_name=str(
                    root_fields["declaring_type_qualified_name"]
                ),
                method_name=str(root_fields["method_name"]),
                parameter_types=tuple(
                    str(item) for item in root_fields["parameter_types"]
                ),
            )
            legacy_payload = legacy_record.state.state_payload_fields
            methods[signature] = EntityRecord(
                root,
                EntityState.create(
                    root=root,
                    state_payload_fields={
                        **legacy_payload.as_dict(),
                        "evidence_references": legacy_record.state.evidence_references,
                        "method_disposition": JavaSemanticDisposition.SEMANTICS_COMPLETE,
                        "declaration_completeness": JavaSemanticFacetCompleteness.COMPLETE,
                        "legacy_static_call_completeness": JavaSemanticFacetCompleteness.COMPLETE,
                        "implementation_semantics_completeness": JavaSemanticFacetCompleteness.COMPLETE,
                    },
                ),
            )

        slots: dict[tuple[str, str], EntityRecord] = {}
        for signature, parsed in sorted(parsed_methods.items()):
            for parameter in parsed.parameters:
                support = self._evidence(
                    parsed.source_path,
                    parameter.byte_start,
                    parameter.byte_end,
                    "java-source-semantics-parameter",
                )
                evidence[support.evidence_id] = support
                root = EntityRoot.java_state_slot(
                    owning_scope_id=self.scope_id,
                    declaring_entity_root_id=methods[signature].root_id,
                    slot_kind=JavaStateSlotKind.PARAMETER,
                    canonical_identifier=parameter.name,
                    declaration_ordinal=parameter.ordinal,
                )
                slots[(signature, parameter.name)] = EntityRecord(
                    root,
                    EntityState.create(
                        root=root,
                        state_payload_fields={
                            "declared_type": parameter.declared_type,
                            "source_revision": self.source_revision,
                            "evidence_references": (support.evidence_id,),
                        },
                    ),
                )

        pending_atoms: dict[str, tuple[_PendingAtom, ...]] = {}
        for signature, parsed in sorted(parsed_methods.items()):
            pending_atoms[signature] = self._project_method(
                parsed,
                methods=methods,
                slots=slots,
            )

        atoms: dict[tuple[str, int], EntityRecord] = {}
        atom_evidence: dict[tuple[str, int], StructureEvidence] = {}
        for signature, pending_values in pending_atoms.items():
            method = methods[signature]
            for pending in pending_values:
                support = self._evidence(
                    parsed_methods[signature].source_path,
                    pending.byte_start,
                    pending.byte_end,
                    pending.evidence_kind,
                )
                evidence[support.evidence_id] = support
                atom_evidence[(signature, pending.ordinal)] = support
                referenced_ids: list[StableId] = []
                operands: list[dict[str, object]] = []
                for kind, raw_value in pending.operands:
                    value = raw_value
                    if kind is JavaSemanticOperandKind.ENTITY_REF:
                        if not isinstance(raw_value, tuple) or len(raw_value) != 2:
                            self._fail(
                                "JAVA_SEMANTIC_PROJECTION_INVALID",
                                "internal Java Entity Ref operand is malformed",
                                support.locator,
                            )
                        ref_kind, ref_value = raw_value
                        if ref_kind == "method":
                            value = methods[str(ref_value)].root_id
                        elif ref_kind == "slot":
                            value = slots[(signature, str(ref_value))].root_id
                        elif ref_kind == "atom":
                            value = atoms[(signature, int(ref_value))].root_id
                        else:
                            self._fail(
                                "JAVA_SEMANTIC_PROJECTION_INVALID",
                                "internal Java Entity Ref target kind is unsupported",
                                support.locator,
                            )
                        referenced_ids.append(value)
                    operands.append({"kind": kind.value, "value": value})
                root = EntityRoot.java_implementation_atom(
                    owning_scope_id=self.scope_id,
                    method_entity_root_id=method.root_id,
                    atom_kind=pending.kind,
                    structural_ordinal=pending.ordinal,
                )
                atoms[(signature, pending.ordinal)] = EntityRecord(
                    root,
                    EntityState.create(
                        root=root,
                        state_payload_fields={
                            "source_revision": self.source_revision,
                            "source_order_ordinal": pending.ordinal,
                            "semantic_form": pending.semantic_form,
                            "operator": pending.operator,
                            "value_category": pending.value_category,
                            "semantic_operands": tuple(operands),
                            "referenced_entity_root_ids": tuple(referenced_ids),
                            "method_disposition": JavaSemanticDisposition.SEMANTICS_COMPLETE,
                            "evidence_references": (support.evidence_id,),
                        },
                    ),
                )

        relations: list[RelationFactRecord] = []
        # Declaration relations are rebuilt with the new exact Schema while
        # preserving ordinal and Evidence from the accepted legacy evaluation.
        for relation in legacy.relations:
            if relation.root.predicate is not RelationPredicate.DECLARES_METHOD:
                continue
            legacy_subject = legacy_types_by_id(legacy)[
                relation.root.subject.entity_root_id
            ]
            legacy_object = legacy_methods_by_id(legacy)[
                relation.root.object.entity_root_id
            ]
            relations.append(
                self._relation(
                    subject=types[_type_name(legacy_subject)],
                    predicate=RelationPredicate.DECLARES_METHOD,
                    object_=methods[_method_signature(legacy_object)],
                    modality=ObservationModality.JAVA_SOURCE_DECLARATION,
                    evidence_references=relation.state.evidence_references,
                    predicate_payload=relation.state.predicate_state_payload_fields,
                )
            )

        legacy_call_sites = self._legacy_call_site_support(legacy, methods)
        for relation in legacy.relations:
            if relation.root.predicate is not RelationPredicate.CALLS:
                continue
            caller = _method_signature(
                legacy_methods_by_id(legacy)[relation.root.subject.entity_root_id]
            )
            callee = _method_signature(
                legacy_methods_by_id(legacy)[relation.root.object.entity_root_id]
            )
            relations.append(
                self._relation(
                    subject=methods[caller],
                    predicate=RelationPredicate.CALLS,
                    object_=methods[callee],
                    modality=ObservationModality.JAVA_SOURCE_STATIC_CALL,
                    evidence_references=relation.state.evidence_references,
                    predicate_payload=relation.state.predicate_state_payload_fields,
                )
            )

        for signature, pending_values in sorted(pending_atoms.items()):
            method = methods[signature]
            for pending in pending_values:
                atom = atoms[(signature, pending.ordinal)]
                support_id = atom_evidence[(signature, pending.ordinal)].evidence_id
                relations.append(
                    self._relation(
                        subject=method,
                        predicate=RelationPredicate.HAS_IMPLEMENTATION_ATOM,
                        object_=atom,
                        modality=ObservationModality.JAVA_SOURCE_IMPLEMENTATION_MEMBERSHIP,
                        evidence_references=(support_id,),
                        predicate_payload={"source_order_ordinal": pending.ordinal},
                    )
                )
                if pending.control_parent_ordinal is not None:
                    relations.append(
                        self._relation(
                            subject=atoms[(signature, pending.control_parent_ordinal)],
                            predicate=RelationPredicate.CONTROLS,
                            object_=atom,
                            modality=(
                                ObservationModality.JAVA_SOURCE_TRUE_BRANCH_CONTROL
                                if pending.control_true_branch
                                else ObservationModality.JAVA_SOURCE_FALSE_BRANCH_CONTROL
                            ),
                            evidence_references=(support_id,),
                            predicate_payload={
                                "controlled_source_order_ordinal": pending.ordinal
                            },
                        )
                    )
                if pending.kind is JavaImplementationAtomKind.CALL_SITE:
                    target_signature = pending.referenced_signatures[0]
                    site_support = legacy_call_sites.get(
                        (
                            signature,
                            target_signature,
                            pending.byte_start,
                            pending.byte_end,
                        )
                    )
                    if site_support is None:
                        self._fail(
                            "JAVA_LEGACY_CALL_CONSISTENCY_FAILED",
                            "tree-sitter call site does not match accepted legacy CALLS support",
                            atom_evidence[(signature, pending.ordinal)].locator,
                        )
                    relations.append(
                        self._relation(
                            subject=atom,
                            predicate=RelationPredicate.CALL_SITE_TARGETS,
                            object_=methods[target_signature],
                            modality=ObservationModality.JAVA_SOURCE_CALL_SITE_TARGET,
                            evidence_references=(site_support,),
                            predicate_payload={
                                "resolution_class": JavaCallResolutionClass.LEGACY_EXACT_STATIC_DIRECT
                            },
                        )
                    )
                if pending.kind is JavaImplementationAtomKind.BRANCH:
                    slot_name = pending.referenced_slot_names[0]
                    relations.append(
                        self._relation(
                            subject=atom,
                            predicate=RelationPredicate.READS_STATE,
                            object_=slots[(signature, slot_name)],
                            modality=ObservationModality.JAVA_SOURCE_STATE_READ,
                            evidence_references=(support_id,),
                            predicate_payload={"access_ordinal": 0},
                        )
                    )
            for current, following in zip(pending_values, pending_values[1:]):
                following_support = atom_evidence[(signature, following.ordinal)]
                relations.append(
                    self._relation(
                        subject=atoms[(signature, current.ordinal)],
                        predicate=RelationPredicate.NEXT_IN_SOURCE,
                        object_=atoms[(signature, following.ordinal)],
                        modality=ObservationModality.JAVA_SOURCE_ORDER,
                        evidence_references=(following_support.evidence_id,),
                        predicate_payload={"source_order_distance": 1},
                    )
                )

        source_file_records = tuple(source_files[key] for key in sorted(source_files))
        type_records = tuple(types[key] for key in sorted(types))
        method_records = tuple(methods[key] for key in sorted(methods))
        slot_records = tuple(
            slots[key]
            for key in sorted(slots, key=lambda item: (item[0], item[1]))
        )
        atom_records = tuple(
            atoms[key]
            for key in sorted(atoms, key=lambda item: (item[0], item[1]))
        )
        relation_records = tuple(
            sorted(
                relations,
                key=lambda item: (
                    item.root.predicate.value,
                    item.root.subject.entity_root_id.value,
                    item.root.object.entity_root_id.value,
                    item.root.observation_modality.value,
                ),
            )
        )
        entities = (
            *source_file_records,
            *type_records,
            *method_records,
            *slot_records,
            *atom_records,
        )
        manifest = CompleteMemberManifest.create(
            tuple(item.coverage_member for item in entities)
            + tuple(item.coverage_member for item in relation_records)
        )
        evidence_tuple = tuple(
            sorted(evidence.values(), key=lambda item: item.evidence_id.value)
        )
        coverage = self._coverage(
            manifest,
            tuple(item.evidence_id for item in evidence_tuple),
        )
        batch = StructureKnowledgeBatch.admit(
            evidence=evidence_tuple,
            entities=entities,
            relation_facts=relation_records,
            coverage=coverage,
            publication_mode=PublicationMode.REPLACE_COVERAGE,
        )
        report = JavaSourceSemanticsBuildReport(
            complete=True,
            source_revision=self.source_revision,
            source_root=self.source_root,
            schema_ref=SCHEMA_REF,
            schema_digest=SCHEMA_DIGEST,
            frontend_ref=FRONTEND_REF,
            frontend_digest=FRONTEND_DIGEST,
            language_abi=self.language.abi_version,
            evaluation_context_ref=EVALUATION_CONTEXT_REF,
            evaluation_context_digest=EVALUATION_CONTEXT_DIGEST,
            canonicalization_ref=CANONICALIZATION_REF,
            canonicalization_digest=CANONICALIZATION_DIGEST,
            source_file_count=len(source_file_records),
            type_count=len(type_records),
            method_count=len(method_records),
            state_slot_count=len(slot_records),
            implementation_atom_count=len(atom_records),
            declaration_count=sum(
                item.root.predicate is RelationPredicate.DECLARES_METHOD
                for item in relation_records
            ),
            legacy_call_relation_count=sum(
                item.root.predicate is RelationPredicate.CALLS
                for item in relation_records
            ),
            legacy_call_site_count=sum(
                int(item.state.predicate_state_payload_fields["call_site_count"])
                for item in relation_records
                if item.root.predicate is RelationPredicate.CALLS
            ),
        )
        return JavaSourceSemanticsEvaluation(
            source_files=source_file_records,
            types=type_records,
            methods=method_records,
            state_slots=slot_records,
            implementation_atoms=atom_records,
            relations=relation_records,
            coverage=coverage,
            complete_member_manifest=manifest,
            evidence=evidence_tuple,
            report=report,
            batch=batch,
        )

    def _legacy_evaluation(self) -> JavaStaticCallEvaluation:
        try:
            return evaluate_java_static_calls(
                JavaStaticCallInput(
                    owning_scope_id=self.scope_id,
                    source_binding_id=self.binding_id,
                    source_revision=self.source_revision,
                    knowledge_context_digest=self.knowledge_context_digest,
                    source_bytes=self.source_bytes,
                    git_entries=self.git_entries,
                    source_evidence=self.source_evidence,
                    tree_evidence=self.tree_evidence,
                    logical_source_root=self.source_root,
                )
            )
        except JavaStaticCallError as exc:
            raise JavaSourceSemanticsError(
                "JAVA_LEGACY_CALL_CONSISTENCY_FAILED",
                str(exc),
                locator=exc.locator,
            ) from exc

    def _parse_compilation_unit(self, path: str, payload: bytes) -> _ParsedType:
        tree = self.parser.parse(payload)
        if tree.root_node.has_error:
            error = _first_error(tree.root_node)
            self._fail(
                "JAVA_FRONTEND_PARSE_ERROR",
                "tree-sitter Java reported a parse or missing-node error",
                _node_locator(path, error),
            )
        if tree.root_node.start_byte != 0 or tree.root_node.end_byte != len(payload):
            self._fail(
                "JAVA_FRONTEND_RANGE_INVALID",
                "tree-sitter root byte range does not cover the exact source",
                path,
            )
        package_name = ""
        imports: dict[str, str] = {}
        classes: list[Node] = []
        for node in tree.root_node.named_children:
            if node.type == "package_declaration":
                name = next(
                    (item for item in node.named_children if item.type in {"scoped_identifier", "identifier"}),
                    None,
                )
                if name is None:
                    self._unsupported(node, path, "package declaration")
                package_name = _node_text(payload, name)
            elif node.type == "import_declaration":
                if any(child.type in {"static", "asterisk"} for child in node.children):
                    self._unsupported(node, path, "static or wildcard import")
                name = next(
                    (item for item in node.named_children if item.type in {"scoped_identifier", "identifier"}),
                    None,
                )
                if name is None:
                    self._unsupported(node, path, "import declaration")
                imported = _node_text(payload, name)
                simple = imported.rsplit(".", 1)[-1]
                if simple in imports and imports[simple] != imported:
                    self._fail(
                        "JAVA_IMPORT_AMBIGUOUS",
                        f"simple imported type {simple} is ambiguous",
                        _node_locator(path, node),
                    )
                imports[simple] = imported
            elif node.type == "class_declaration":
                classes.append(node)
            elif node.type == "line_comment" or node.type == "block_comment":
                continue
            else:
                self._unsupported(node, path, "top-level declaration")
        if len(classes) != 1:
            self._fail(
                "JAVA_TOP_LEVEL_CLASS_REQUIRED",
                "Java source must contain exactly one supported top-level class",
                path,
            )
        class_node = classes[0]
        class_name_node = class_node.child_by_field_name("name")
        class_body = class_node.child_by_field_name("body")
        if class_name_node is None or class_body is None:
            self._unsupported(class_node, path, "class declaration")
        class_name = _node_text(payload, class_name_node)
        if class_name != PurePosixPath(path).stem:
            self._fail(
                "JAVA_TYPE_FILE_NAME_MISMATCH",
                "top-level class name must match its source file name",
                path,
            )
        expected_parent = PurePosixPath(path).relative_to(self.source_root).parent
        expected_package = "" if str(expected_parent) == "." else ".".join(expected_parent.parts)
        if package_name != expected_package:
            self._fail(
                "JAVA_PACKAGE_PATH_MISMATCH",
                "Java package differs from its source-root-relative path",
                path,
            )
        qualified_name = f"{package_name}.{class_name}" if package_name else class_name
        methods: list[_ParsedMethod] = []
        for child in class_body.named_children:
            if child.type in {"line_comment", "block_comment"}:
                continue
            if child.type != "method_declaration":
                self._unsupported(child, path, "class member")
            methods.append(
                self._parse_method(
                    child,
                    payload,
                    path=path,
                    declaring_type=qualified_name,
                    imports=imports,
                    declaration_ordinal=len(methods),
                )
            )
        return _ParsedType(
            qualified_name=qualified_name,
            simple_name=class_name,
            package_name=package_name,
            source_path=path,
            header_start=class_node.start_byte,
            header_end=class_body.start_byte,
            imports=tuple(sorted(imports.items())),
            methods=tuple(methods),
        )

    def _parse_method(
        self,
        node: Node,
        payload: bytes,
        *,
        path: str,
        declaring_type: str,
        imports: Mapping[str, str],
        declaration_ordinal: int,
    ) -> _ParsedMethod:
        name_node = node.child_by_field_name("name")
        type_node = node.child_by_field_name("type")
        parameters_node = node.child_by_field_name("parameters")
        body_node = node.child_by_field_name("body")
        if any(item is None for item in (name_node, type_node, parameters_node, body_node)):
            self._unsupported(node, path, "method declaration")
        modifiers_node = next(
            (child for child in node.named_children if child.type == "modifiers"),
            None,
        )
        raw_modifiers = (
            ()
            if modifiers_node is None
            else tuple(_node_text(payload, modifiers_node).split())
        )
        if len(set(raw_modifiers)) != len(raw_modifiers) or any(
            item not in _MODIFIERS for item in raw_modifiers
        ):
            self._unsupported(modifiers_node or node, path, "method modifier")
        modifiers = tuple(sorted(raw_modifiers))
        visibility_values = tuple(item for item in modifiers if item in _VISIBILITY)
        if len(visibility_values) > 1:
            self._unsupported(modifiers_node or node, path, "method visibility")
        visibility = visibility_values[0] if visibility_values else "package-private"
        return_type = _canonical_type(
            _node_text(payload, type_node),
            declaring_type=declaring_type,
            imports=imports,
        )
        parameters: list[_ParsedParameter] = []
        for child in parameters_node.named_children:
            if child.type != "formal_parameter":
                self._unsupported(child, path, "method parameter")
            parameter_name = child.child_by_field_name("name")
            parameter_type = child.child_by_field_name("type")
            if parameter_name is None or parameter_type is None:
                self._unsupported(child, path, "method parameter")
            parameters.append(
                _ParsedParameter(
                    name=_node_text(payload, parameter_name),
                    declared_type=_canonical_type(
                        _node_text(payload, parameter_type),
                        declaring_type=declaring_type,
                        imports=imports,
                    ),
                    ordinal=len(parameters),
                    byte_start=child.start_byte,
                    byte_end=child.end_byte,
                )
            )
        assert name_node is not None and body_node is not None
        return _ParsedMethod(
            declaring_type=declaring_type,
            name=_node_text(payload, name_node),
            parameter_types=tuple(item.declared_type for item in parameters),
            parameters=tuple(parameters),
            return_type=return_type,
            visibility=visibility,
            modifiers=modifiers,
            source_path=path,
            declaration_ordinal=declaration_ordinal,
            header_start=node.start_byte,
            header_end=body_node.start_byte,
            body=body_node,
        )

    def _project_method(
        self,
        method: _ParsedMethod,
        *,
        methods: Mapping[str, EntityRecord],
        slots: Mapping[tuple[str, str], EntityRecord],
    ) -> tuple[_PendingAtom, ...]:
        payload = self.source_bytes[method.source_path]
        by_target: dict[tuple[str, int], list[str]] = {}
        for signature in methods:
            owner, tail = signature.split("#", 1)
            method_name, raw_parameters = tail[:-1].split("(", 1)
            arity = 0 if not raw_parameters else len(raw_parameters.split(","))
            by_target.setdefault((method_name, arity), []).append(signature)
        pending: list[_PendingAtom] = []
        parameters = {item.name: item for item in method.parameters}

        def append_atom(
            *,
            kind: JavaImplementationAtomKind,
            node: Node,
            evidence_kind: str,
            semantic_form: JavaSemanticForm,
            operator: JavaSemanticOperator,
            value_category: JavaValueCategory,
            operands: tuple[tuple[JavaSemanticOperandKind, object], ...],
            referenced_signatures: tuple[str, ...] = (),
            referenced_slot_names: tuple[str, ...] = (),
            control_parent_ordinal: int | None = None,
            byte_start: int | None = None,
            byte_end: int | None = None,
        ) -> int:
            ordinal = len(pending)
            pending.append(
                _PendingAtom(
                    method_signature=method.signature,
                    kind=kind,
                    ordinal=ordinal,
                    byte_start=node.start_byte if byte_start is None else byte_start,
                    byte_end=node.end_byte if byte_end is None else byte_end,
                    evidence_kind=evidence_kind,
                    semantic_form=semantic_form,
                    operator=operator,
                    value_category=value_category,
                    operands=operands,
                    referenced_signatures=referenced_signatures,
                    referenced_slot_names=referenced_slot_names,
                    control_parent_ordinal=control_parent_ordinal,
                )
            )
            return ordinal

        def resolve_invocation(node: Node) -> str:
            name_node = node.child_by_field_name("name")
            arguments = node.child_by_field_name("arguments")
            object_node = node.child_by_field_name("object")
            if name_node is None or arguments is None:
                self._unsupported(node, method.source_path, "method invocation")
            name = _node_text(payload, name_node)
            arity = len(arguments.named_children)
            if any(child.type not in {"identifier", "decimal_integer_literal", "true", "false", "null_literal"} for child in arguments.named_children):
                self._unsupported(node, method.source_path, "call argument")
            if object_node is None:
                candidates = by_target.get((name, arity), ())
                candidates = tuple(
                    item for item in candidates if item.startswith(method.declaring_type + "#")
                )
            else:
                receiver = _node_text(payload, object_node)
                if not _JAVA_IDENTIFIER.fullmatch(receiver):
                    self._unsupported(object_node, method.source_path, "call receiver")
                owner = dict(methods_by_simple_name(methods)).get(receiver)
                candidates = () if owner is None else tuple(
                    item
                    for item in by_target.get((name, arity), ())
                    if item.startswith(owner + "#")
                )
            if len(candidates) != 1:
                self._fail(
                    "JAVA_CALL_TARGET_UNRESOLVED",
                    "supported call site must resolve to exactly one source method",
                    _node_locator(method.source_path, node),
                )
            return candidates[0]

        def project_call(node: Node, control: int | None) -> int:
            target = resolve_invocation(node)
            target_record = methods[target]
            category = (
                JavaValueCategory.VOID
                if target_record.state.state_payload_fields["return_type"] == "void"
                else JavaValueCategory.CALL_RESULT
            )
            return append_atom(
                kind=JavaImplementationAtomKind.CALL_SITE,
                node=node,
                evidence_kind="java-static-call-site",
                semantic_form=JavaSemanticForm.STATIC_CALL,
                operator=JavaSemanticOperator.DIRECT_CALL,
                value_category=category,
                operands=((JavaSemanticOperandKind.ENTITY_REF, ("method", target)),),
                referenced_signatures=(target,),
                control_parent_ordinal=control,
            )

        def project_return(node: Node, control: int | None) -> None:
            values = node.named_children
            operands: tuple[tuple[JavaSemanticOperandKind, object], ...]
            category: JavaValueCategory
            if not values:
                category = JavaValueCategory.VOID
                operands = ()
            elif len(values) == 1 and values[0].type == "method_invocation":
                call_ordinal = project_call(values[0], control)
                category = JavaValueCategory.CALL_RESULT
                operands = ((JavaSemanticOperandKind.ENTITY_REF, ("atom", call_ordinal)),)
            elif len(values) == 1 and values[0].type in {"true", "false"}:
                category = JavaValueCategory.BOOLEAN
                operands = ((JavaSemanticOperandKind.BOOLEAN_LITERAL, values[0].type == "true"),)
            elif len(values) == 1 and values[0].type == "null_literal":
                category = JavaValueCategory.NULL
                operands = ((JavaSemanticOperandKind.NULL_LITERAL, None),)
            elif len(values) == 1 and values[0].type == "decimal_integer_literal":
                category = JavaValueCategory.INTEGER
                operands = ((JavaSemanticOperandKind.INTEGER_LITERAL, int(_node_text(payload, values[0]).replace("_", ""))),)
            elif len(values) == 1 and values[0].type == "identifier":
                name = _node_text(payload, values[0])
                if name not in parameters:
                    self._unsupported(values[0], method.source_path, "return value")
                category = JavaValueCategory.STATE
                operands = ((JavaSemanticOperandKind.ENTITY_REF, ("slot", name)),)
            else:
                self._unsupported(node, method.source_path, "return value")
            append_atom(
                kind=JavaImplementationAtomKind.RETURN,
                node=node,
                evidence_kind="java-source-semantics-return",
                semantic_form=JavaSemanticForm.RETURN_VALUE,
                operator=JavaSemanticOperator.RETURN,
                value_category=category,
                operands=operands,
                control_parent_ordinal=control,
            )

        def project_throw(node: Node, control: int | None) -> None:
            if len(node.named_children) != 1 or node.named_children[0].type != "object_creation_expression":
                self._unsupported(node, method.source_path, "throw value")
            created = node.named_children[0]
            type_node = created.child_by_field_name("type")
            arguments = created.child_by_field_name("arguments")
            if type_node is None or arguments is None:
                self._unsupported(created, method.source_path, "throw construction")
            if arguments.named_children:
                self._unsupported(arguments, method.source_path, "throw constructor argument")
            exception_type = _canonical_type(
                _node_text(payload, type_node),
                declaring_type=method.declaring_type,
                imports={},
            )
            append_atom(
                kind=JavaImplementationAtomKind.THROW,
                node=node,
                evidence_kind="java-source-semantics-throw",
                semantic_form=JavaSemanticForm.THROW_CONSTRUCTION,
                operator=JavaSemanticOperator.THROW,
                value_category=JavaValueCategory.EXCEPTION,
                operands=(
                    (JavaSemanticOperandKind.TYPE_REF, exception_type),
                    (JavaSemanticOperandKind.CONSTRUCTOR_ARITY, 0),
                ),
                control_parent_ordinal=control,
            )

        def project_if(node: Node, outer_control: int | None) -> None:
            if outer_control is not None:
                self._unsupported(node, method.source_path, "nested branch")
            condition = node.child_by_field_name("condition")
            consequence = node.child_by_field_name("consequence")
            alternative = node.child_by_field_name("alternative")
            if condition is None or consequence is None or alternative is not None:
                self._unsupported(node, method.source_path, "if statement")
            while condition.type == "parenthesized_expression" and len(condition.named_children) == 1:
                condition = condition.named_children[0]
            operator = JavaSemanticOperator.IS_TRUE
            operand = condition
            if condition.type == "unary_expression":
                operand = condition.child_by_field_name("operand")
                if operand is None or payload[condition.start_byte:operand.start_byte].strip() != b"!":
                    self._unsupported(condition, method.source_path, "branch condition")
                operator = JavaSemanticOperator.NOT
            if operand.type != "identifier":
                self._unsupported(condition, method.source_path, "branch condition")
            name = _node_text(payload, operand)
            parameter = parameters.get(name)
            if parameter is None or parameter.declared_type != "boolean":
                self._unsupported(condition, method.source_path, "branch condition")
            branch_ordinal = append_atom(
                kind=JavaImplementationAtomKind.BRANCH,
                node=condition,
                byte_start=condition.start_byte,
                byte_end=condition.end_byte,
                evidence_kind="java-source-semantics-branch",
                semantic_form=JavaSemanticForm.BOOLEAN_SLOT_TEST,
                operator=operator,
                value_category=JavaValueCategory.BOOLEAN,
                operands=((JavaSemanticOperandKind.ENTITY_REF, ("slot", name)),),
                referenced_slot_names=(name,),
            )
            project_statement(consequence, branch_ordinal)

        def project_statement(node: Node, control: int | None = None) -> None:
            if node.type == "block":
                for child in node.named_children:
                    if child.type in {"line_comment", "block_comment"}:
                        continue
                    project_statement(child, control)
            elif node.type == "if_statement":
                project_if(node, control)
            elif node.type == "expression_statement":
                named = node.named_children
                if len(named) != 1 or named[0].type != "method_invocation":
                    self._unsupported(node, method.source_path, "expression statement")
                project_call(named[0], control)
            elif node.type == "return_statement":
                project_return(node, control)
            elif node.type == "throw_statement":
                project_throw(node, control)
            else:
                self._unsupported(node, method.source_path, "method-body construct")

        project_statement(method.body)
        if len(pending) > 64:
            self._fail(
                "JAVA_METHOD_ATOM_BUDGET_EXCEEDED",
                "supported method exceeds 64 implementation atoms",
                method.source_path,
            )
        if any(
            child.type in _ATOM_NODE_TYPES
            for child in _walk_named(method.body)
            if child != method.body
        ) and not pending:
            self._fail(
                "JAVA_SEMANTIC_PROJECTION_EMPTY",
                "method contains supported semantic nodes but produced no atoms",
                method.source_path,
            )
        return tuple(pending)

    def _legacy_call_site_support(
        self,
        legacy: JavaStaticCallEvaluation,
        methods: Mapping[str, EntityRecord],
    ) -> dict[tuple[str, str, int, int], StableId]:
        legacy_method_ids = {
            item.root_id: _method_signature(item) for item in legacy.methods
        }
        result: dict[tuple[str, str, int, int], StableId] = {}
        evidence_by_id = {item.evidence_id: item for item in legacy.evidence}
        for relation in legacy.relations:
            if relation.root.predicate is not RelationPredicate.CALLS:
                continue
            caller = legacy_method_ids[relation.root.subject.entity_root_id]
            callee = legacy_method_ids[relation.root.object.entity_root_id]
            for evidence_id in relation.state.evidence_references:
                item = evidence_by_id[evidence_id]
                result[(caller, callee, item.byte_start, item.byte_end)] = evidence_id
        return result

    def _relation(
        self,
        *,
        subject: EntityRecord,
        predicate: RelationPredicate,
        object_: EntityRecord,
        modality: ObservationModality,
        evidence_references: tuple[StableId, ...],
        predicate_payload: Mapping[str, object],
    ) -> RelationFactRecord:
        root = RelationFactRoot.create(
            owning_scope_id=self.scope_id,
            subject=subject.root.ref,
            predicate=predicate,
            object=object_.root.ref,
            observation_modality=modality,
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
        return RelationFactRecord(root, state)

    def _coverage(
        self,
        manifest: CompleteMemberManifest,
        evidence_references: tuple[StableId, ...],
    ) -> CoverageRecord:
        root = CoverageRoot.create(
            owning_scope_id=self.scope_id,
            source_binding_id=self.binding_id,
            logical_reactor_root=self.source_root,
            profile_ref=PROFILE_REF,
            schema_ref=SCHEMA_REF,
            schema_digest=SCHEMA_DIGEST,
            maven_evaluation_context_ref=EVALUATION_CONTEXT_REF,
            maven_evaluation_context_digest=EVALUATION_CONTEXT_DIGEST,
            covered_entity_types=JAVA_SOURCE_SEMANTICS_ENTITY_TYPES,
            covered_relation_predicates=JAVA_SOURCE_SEMANTICS_RELATION_PREDICATES,
            canonicalization_ref=CANONICALIZATION_REF,
            canonicalization_digest=CANONICALIZATION_DIGEST,
            coverage_root_ref=COVERAGE_ROOT_REF,
        )
        return CoverageRecord(
            root,
            CoverageState.create(
                root=root,
                source_revision=self.source_revision,
                knowledge_context_digest=self.knowledge_context_digest,
                complete_member_manifest=manifest,
                evidence_references=evidence_references,
            ),
        )

    def _evidence(
        self,
        path: str,
        byte_start: int,
        byte_end: int,
        kind: str,
    ) -> StructureEvidence:
        metadata = self.source_evidence[path]
        payload = self.source_bytes[path]
        try:
            excerpt = payload[byte_start:byte_end].decode("utf-8")
        except UnicodeDecodeError as exc:  # frontend ranges must be UTF-8 boundaries
            raise JavaSourceSemanticsError(
                "JAVA_FRONTEND_RANGE_INVALID",
                "tree-sitter byte range splits an exact UTF-8 sequence",
                locator=f"{path}#bytes={byte_start}-{byte_end}",
            ) from exc
        return StructureEvidence.create(
            artifact_id=metadata.artifact_id,
            source_context_id=metadata.source_context_id,
            byte_start=byte_start,
            byte_end=byte_end,
            locator=f"{path}#bytes={byte_start}-{byte_end};kind={kind}",
            excerpt=excerpt,
            artifact_content_digest=metadata.artifact_content_digest,
        )

    def _validate_input(self) -> None:
        if self.scope_id.kind != "scope" or self.binding_id.kind != "binding":
            self._fail(
                "JAVA_AUTHORITY_ID_INVALID",
                "Java semantics requires typed Scope and Binding IDs",
                self.source_root,
            )
        if not isinstance(self.knowledge_context_digest, Digest):
            self._fail(
                "JAVA_CONTEXT_DIGEST_INVALID",
                "Java semantics requires a typed Context digest",
                self.source_root,
            )
        prefix = self.source_root + "/"
        expected = {
            path
            for path in self.git_entries
            if path.startswith(prefix) and path.endswith(".java")
        }
        if not expected:
            self._fail(
                "JAVA_SOURCE_SET_EMPTY",
                "Java source root contains no .java files",
                self.source_root,
            )
        if expected != set(self.source_bytes) or expected != set(self.source_evidence):
            self._fail(
                "JAVA_SOURCE_CLOSURE_INCOMPLETE",
                "Java source bytes, Evidence metadata, and Git tree differ",
                self.source_root,
            )
        observed_tree = _tree_entries(self.tree_evidence, self.source_revision)
        if observed_tree != self.git_entries:
            self._fail(
                "JAVA_TREE_EVIDENCE_MISMATCH",
                "tree Evidence differs from supplied Git metadata",
                self.source_root,
            )
        for path in sorted(expected):
            entry = self.git_entries[path]
            payload = self.source_bytes[path]
            metadata = self.source_evidence[path]
            if (
                entry.mode != "100644"
                or entry.object_type != "blob"
                or entry.is_symlink
                or _FULL_GIT_OBJECT.fullmatch(entry.object_id) is None
            ):
                self._fail(
                    "JAVA_SOURCE_ENTRY_UNSUPPORTED",
                    "Java source must be a regular non-symlink Git blob",
                    path,
                )
            if not isinstance(payload, bytes):
                self._fail(
                    "JAVA_SOURCE_NOT_BYTES",
                    "Java source payload must be immutable bytes",
                    path,
                )
            try:
                payload.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise JavaSourceSemanticsError(
                    "JAVA_SOURCE_UTF8_INVALID",
                    "Java source must be exact UTF-8",
                    locator=path,
                ) from exc
            actual_digest = Digest(f"sha256:{hashlib.sha256(payload).hexdigest()}")
            if (
                metadata.locator != path
                or metadata.artifact_id.kind != "source_artifact"
                or metadata.source_context_id.kind != "source_context"
                or metadata.artifact_content_digest != actual_digest
            ):
                self._fail(
                    "JAVA_SOURCE_EVIDENCE_INVALID",
                    "Java source Evidence metadata is not exact",
                    path,
                )

    def _unsupported(self, node: Node, path: str, label: str) -> None:
        self._fail(
            "JAVA_SEMANTIC_CONSTRUCT_UNSUPPORTED",
            f"{label} is outside the SLICE-001 semantic closure",
            _node_locator(path, node),
        )

    @staticmethod
    def _fail(reason_code: str, message: str, locator: str) -> None:
        raise JavaSourceSemanticsError(reason_code, message, locator=locator)


def _frozen_language() -> Language:
    components: list[dict[str, object]] = []
    for name, expected_version, expected_digest in EXPECTED_COMPONENTS:
        package = distribution(name)
        if package.version != expected_version:
            raise JavaSourceSemanticsError(
                "JAVA_FRONTEND_VERSION_DRIFT",
                f"{name} runtime version drifted from the frozen frontend",
                locator=name,
            )
        actual_digest = _runtime_fileset_digest(name)
        if actual_digest != expected_digest:
            raise JavaSourceSemanticsError(
                "JAVA_FRONTEND_ARTIFACT_DRIFT",
                f"{name} runtime fileset drifted from the frozen frontend",
                locator=name,
            )
        components.append(
            {
                "distribution": name,
                "version": package.version,
                "runtime_fileset_digest": actual_digest,
            }
        )
    language = Language(tree_sitter_java.language())
    if language.abi_version != EXPECTED_LANGUAGE_ABI:
        raise JavaSourceSemanticsError(
            "JAVA_FRONTEND_ABI_DRIFT",
            "tree-sitter Java language ABI drifted",
            locator=FRONTEND_REF,
        )
    identity = {
        "frontend_ref": FRONTEND_REF,
        "language_abi": language.abi_version,
        "components": components,
    }
    if _canonical_digest(identity) != FRONTEND_DIGEST.value:
        raise JavaSourceSemanticsError(
            "JAVA_FRONTEND_IDENTITY_DRIFT",
            "combined tree-sitter Java frontend identity drifted",
            locator=FRONTEND_REF,
        )
    return language


def _runtime_fileset_digest(name: str) -> str:
    package = distribution(name)
    entries: list[dict[str, object]] = []
    for item in sorted(package.files or (), key=str):
        relative = str(item)
        if (
            "__pycache__/" in relative
            or relative.endswith("/RECORD")
            or relative.endswith("/INSTALLER")
            or relative.endswith("/REQUESTED")
        ):
            continue
        path = package.locate_file(item)
        if path.is_file():
            content = path.read_bytes()
            entries.append(
                {
                    "path": relative,
                    "size": len(content),
                    "sha256": hashlib.sha256(content).hexdigest(),
                }
            )
    return _canonical_digest(
        {"distribution": name, "version": package.version, "files": entries}
    )


def _canonical_digest(value: object) -> str:
    return "sha256:" + hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def _tree_entries(
    evidence_values: tuple[StructureEvidence, ...],
    revision: str,
) -> dict[str, GitEntryMetadata]:
    if not evidence_values:
        raise JavaSourceSemanticsError(
            "JAVA_TREE_EVIDENCE_MISSING",
            "complete Java Coverage requires Git tree Evidence",
            locator=revision,
        )
    result: dict[str, GitEntryMetadata] = {}
    for evidence in evidence_values:
        evidence.require_valid_identity()
        if not evidence.locator.startswith(f"git-tree:{revision}:"):
            raise JavaSourceSemanticsError(
                "JAVA_TREE_EVIDENCE_INVALID",
                "tree Evidence is not bound to the exact revision",
                locator=evidence.locator,
            )
        for line_number, line in enumerate(evidence.excerpt.splitlines(), 1):
            locator = f"{evidence.locator}#line={line_number}"
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise JavaSourceSemanticsError(
                    "JAVA_TREE_EVIDENCE_INVALID",
                    "tree Evidence line is not JSON",
                    locator=locator,
                ) from exc
            if not isinstance(value, dict) or set(value) != {
                "is_symlink",
                "mode",
                "object_id",
                "path",
                "type",
            }:
                raise JavaSourceSemanticsError(
                    "JAVA_TREE_EVIDENCE_INVALID",
                    "tree Evidence entry has the wrong shape",
                    locator=locator,
                )
            canonical = json.dumps(
                value,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            if line != canonical:
                raise JavaSourceSemanticsError(
                    "JAVA_TREE_EVIDENCE_INVALID",
                    "tree Evidence entry is not canonical JSON",
                    locator=locator,
                )
            path = _path(value["path"], "tree Evidence path")
            metadata = GitEntryMetadata(
                mode=_text(value["mode"], "Git mode"),
                object_type=_text(value["type"], "Git object type"),
                object_id=_text(value["object_id"], "Git object ID"),
            )
            if value["is_symlink"] != metadata.is_symlink or path in result:
                raise JavaSourceSemanticsError(
                    "JAVA_TREE_EVIDENCE_INVALID",
                    "tree Evidence symlink flag or path is invalid",
                    locator=locator,
                )
            result[path] = metadata
    return result


def _canonical_type(
    raw: str,
    *,
    declaring_type: str,
    imports: Mapping[str, str],
) -> str:
    value = raw.strip()
    dimensions = ""
    while value.endswith("[]"):
        dimensions += "[]"
        value = value[:-2]
    if value in {
        "boolean",
        "byte",
        "char",
        "double",
        "float",
        "int",
        "long",
        "short",
        "void",
    }:
        return value + dimensions
    if value in imports:
        return imports[value] + dimensions
    if value in _JAVA_LANG_TYPES:
        return f"java.lang.{value}{dimensions}"
    if "." in value:
        return value + dimensions
    package = declaring_type.rsplit(".", 1)[0] if "." in declaring_type else ""
    return (f"{package}.{value}" if package else value) + dimensions


def _node_text(payload: bytes, node: Node) -> str:
    return payload[node.start_byte:node.end_byte].decode("utf-8")


def _node_locator(path: str, node: Node) -> str:
    return f"{path}#bytes={node.start_byte}-{node.end_byte}"


def _first_error(root: Node) -> Node:
    for node in _walk_named(root):
        if node.is_error or node.is_missing:
            return node
    return root


def _walk_named(root: Node):
    stack = [root]
    while stack:
        node = stack.pop()
        yield node
        stack.extend(reversed(node.named_children))


def methods_by_simple_name(
    methods: Mapping[str, EntityRecord],
) -> tuple[tuple[str, str], ...]:
    values: dict[str, str] = {}
    ambiguous: set[str] = set()
    for record in methods.values():
        qualified = str(record.root.root_fields["declaring_type_qualified_name"])
        simple = qualified.rsplit(".", 1)[-1]
        if simple in values and values[simple] != qualified:
            ambiguous.add(simple)
        values[simple] = qualified
    return tuple(
        sorted((key, value) for key, value in values.items() if key not in ambiguous)
    )


def legacy_types_by_id(
    legacy: JavaStaticCallEvaluation,
) -> dict[StableId, EntityRecord]:
    return {item.root_id: item for item in legacy.types}


def legacy_methods_by_id(
    legacy: JavaStaticCallEvaluation,
) -> dict[StableId, EntityRecord]:
    return {item.root_id: item for item in legacy.methods}


def _type_name(record: EntityRecord) -> str:
    return str(record.root.root_fields["qualified_name"])


def _method_signature(record: EntityRecord) -> str:
    fields = record.root.root_fields
    parameters = ",".join(str(item) for item in fields["parameter_types"])
    return (
        f"{fields['declaring_type_qualified_name']}#"
        f"{fields['method_name']}({parameters})"
    )


def _path(value: object, label: str) -> str:
    text = _text(value, label)
    path = PurePosixPath(text)
    if path.is_absolute() or ".." in path.parts or str(path) != text:
        raise JavaSourceSemanticsError(
            "JAVA_PATH_INVALID",
            f"{label} must be a canonical relative POSIX path",
            locator=text,
        )
    return text


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise JavaSourceSemanticsError(
            "JAVA_TEXT_INVALID",
            f"{label} must be non-empty canonical text",
            locator=label,
        )
    return value


__all__ = [
    "JavaSourceSemanticsBuildReport",
    "JavaSourceSemanticsError",
    "JavaSourceSemanticsEvaluation",
    "JavaSourceSemanticsEvaluator",
    "JavaSourceSemanticsInput",
    "evaluate_java_source_semantics",
]
