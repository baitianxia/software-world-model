"""Build a reusable Java cognition projection from one exact Source tree."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import PurePosixPath
import re
from typing import Mapping, Sequence

from tree_sitter import Node, Parser

from software_world_model.cross_cutting import Digest, DomainError, ErrorCode, StableId, digest_of
from software_world_model.knowledge_engine.capability_cognition import (
    CAPABILITY_COGNITION_PROFILE,
    CapabilityCognitionSnapshot,
    CognitionBehavior,
    CognitionBehaviorKind,
    CognitionCoverage,
    CognitionEntity,
    CognitionEntityKind,
    CognitionEpistemics,
    CognitionProvenance,
    CognitionRelation,
    CognitionRelationKind,
    CognitionResolution,
)

from .java_source_semantics import FRONTEND_REF, frozen_java_language


_GIT_OID = re.compile(r"^[0-9a-f]{40}$")
_TYPE_DECLARATIONS = frozenset(
    {
        "annotation_type_declaration",
        "class_declaration",
        "enum_declaration",
        "interface_declaration",
        "record_declaration",
    }
)
_EXECUTABLE_BOUNDARIES = _TYPE_DECLARATIONS.union(
    {
        "compact_constructor_declaration",
        "constructor_declaration",
        "lambda_expression",
        "method_declaration",
    }
)
_CONDITION_NODES = frozenset(
    {
        "if_statement",
        "while_statement",
        "do_statement",
        "for_statement",
        "ternary_expression",
    }
)


@dataclass(frozen=True, slots=True)
class JavaCognitionModuleSource:
    module_root: str
    module_name: str
    descriptor_path: str
    descriptor_bytes: bytes

    def __post_init__(self) -> None:
        _relative_path(self.module_root)
        _text(self.module_name, "Java cognition module name")
        _relative_path(self.descriptor_path)
        if not isinstance(self.descriptor_bytes, bytes) or not self.descriptor_bytes:
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "module descriptor bytes are required")


@dataclass(frozen=True, slots=True)
class ExactJavaCognitionSource:
    project_name: str
    source_revision: str
    source_tree: str
    selected_roots: tuple[str, ...]
    modules: tuple[JavaCognitionModuleSource, ...]
    source_files: Mapping[str, bytes]

    def __post_init__(self) -> None:
        _text(self.project_name, "Java cognition project name")
        if _GIT_OID.fullmatch(self.source_revision) is None or _GIT_OID.fullmatch(self.source_tree) is None:
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "Java cognition Source identity must be exact Git OIDs")
        roots = tuple(sorted({_relative_path(item) for item in self.selected_roots}))
        if not roots or roots != self.selected_roots:
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "selected Java roots must be unique and sorted")
        if not self.modules:
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "Java cognition needs at least one module")
        module_roots = tuple(item.module_root for item in self.modules)
        if tuple(sorted(set(module_roots))) != module_roots:
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "Java cognition modules must be unique and sorted")
        for path, payload in self.source_files.items():
            normalized = _relative_path(path)
            if normalized != path or not path.endswith(".java") or not _under_any(path, roots):
                raise DomainError(ErrorCode.SOURCE_TARGET_OUT_OF_SCOPE, "Java cognition file is outside selected roots")
            if not isinstance(payload, bytes) or not payload:
                raise DomainError(ErrorCode.INVALID_ARGUMENT, "Java cognition source bytes are required")


@dataclass(slots=True)
class _CompilationUnit:
    path: str
    payload: bytes
    root: Node
    module: JavaCognitionModuleSource
    package_name: str
    package_node: Node | None
    imports: tuple[tuple[str, Node, bool, bool], ...]
    file_entity: CognitionEntity


@dataclass(slots=True)
class _TypeProjection:
    entity: CognitionEntity
    node: Node
    body: Node
    unit: _CompilationUnit
    fields: dict[str, str]
    inheritance: tuple[tuple[str, Node], ...]
    methods: list["_MethodProjection"]


@dataclass(slots=True)
class _MethodProjection:
    entity: CognitionEntity
    node: Node
    body: Node | None
    owner: _TypeProjection
    arity: int
    parameters: dict[str, str]


class JavaCapabilityCognitionBuilder:
    """Use the frozen Java frontend to construct one immutable read snapshot."""

    def build(self, source: ExactJavaCognitionSource) -> CapabilityCognitionSnapshot:
        if not isinstance(source, ExactJavaCognitionSource):
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "Java cognition builder needs exact Source")
        self.source = source
        self.parser = Parser(frozen_java_language())
        self.entities: list[CognitionEntity] = []
        self.relations: list[CognitionRelation] = []
        self.behaviors: list[CognitionBehavior] = []
        self.units: list[_CompilationUnit] = []
        self.types: list[_TypeProjection] = []
        self.methods: list[_MethodProjection] = []
        self.conflicts: list[str] = []
        self.unknowns: list[str] = []
        self.partial_file_count = 0
        self._module_entities: dict[str, CognitionEntity] = {}
        self._package_entities: dict[tuple[str, str], CognitionEntity] = {}

        self._project_modules()
        for path in sorted(source.source_files):
            self._project_compilation_unit(path, source.source_files[path])
        self._index_types_and_methods()
        self._project_imports_and_inheritance()
        self._project_method_behavior()
        if not self.entities:
            raise DomainError(ErrorCode.SOURCE_OPERATION_FAILED, "Java cognition produced no entities")
        if self.partial_file_count:
            self.unknowns.append(
                f"{self.partial_file_count} selected Java files could not be parsed completely"
            )
        self.unknowns.append(
            "Source outside selected roots and non-Java resources are not represented by this snapshot"
        )
        self.unknowns.append(
            "dynamic dispatch, reflection, framework wiring, generated implementations, and runtime effects remain unknown unless direct Source relations prove them"
        )
        return CapabilityCognitionSnapshot.create(
            project_name=source.project_name,
            source_revision=source.source_revision,
            source_tree=source.source_tree,
            selected_roots=source.selected_roots,
            frontend_ref=FRONTEND_REF,
            entities=self.entities,
            relations=self.relations,
            behaviors=self.behaviors,
            parsed_file_count=len(self.units),
            partial_file_count=self.partial_file_count,
            conflicts=tuple(sorted(set(self.conflicts))),
            unknowns=tuple(sorted(set(self.unknowns))),
        )

    def _project_modules(self) -> None:
        for module in self.source.modules:
            provenance = self._bytes_provenance(
                module.descriptor_path,
                module.descriptor_bytes,
                "MAVEN_MODULE_DESCRIPTOR",
            )
            entity = self._entity(
                kind=CognitionEntityKind.MODULE,
                identity=(module.module_root,),
                name=module.module_name,
                qualified_name=f"{self.source.project_name}:{module.module_root}",
                parent_id=None,
                provenance=provenance,
                attributes=(("module_root", module.module_root),),
            )
            self.entities.append(entity)
            self._module_entities[module.module_root] = entity

    def _project_compilation_unit(self, path: str, payload: bytes) -> None:
        module = self._module_for(path)
        tree = self.parser.parse(payload)
        root = tree.root_node
        file_epistemics = CognitionEpistemics(CognitionCoverage.COMPLETE)
        if root.has_error or root.start_byte != 0 or root.end_byte != len(payload):
            self.partial_file_count += 1
            file_epistemics = CognitionEpistemics(
                CognitionCoverage.PARTIAL,
                unknowns=("tree-sitter did not produce a complete compilation unit",),
            )
        package_node = next(
            (item for item in root.named_children if item.type == "package_declaration"),
            None,
        )
        package_name = self._package_name(package_node, payload)
        package_entity = self._package(module, package_name, package_node, path, payload)
        file_entity = self._entity(
            kind=CognitionEntityKind.FILE,
            identity=(path,),
            name=PurePosixPath(path).name,
            qualified_name=path,
            parent_id=package_entity.entity_id,
            provenance=self._node_provenance(path, payload, root, "JAVA_COMPILATION_UNIT"),
            epistemics=file_epistemics,
            attributes=(("module", module.module_name), ("package", package_name or "<default>")),
        )
        self.entities.append(file_entity)
        self.relations.append(
            self._relation(
                CognitionRelationKind.CONTAINS,
                package_entity,
                object_entity=file_entity,
                object_symbol=file_entity.qualified_name,
                provenance=file_entity.provenance,
            )
        )
        imports: list[tuple[str, Node, bool, bool]] = []
        for node in root.named_children:
            if node.type != "import_declaration":
                continue
            text = _node_text(payload, node)
            imports.append(
                (
                    text.removeprefix("import ").removeprefix("static ").removesuffix(";").strip(),
                    node,
                    text.startswith("import static "),
                    "*" in text,
                )
            )
        unit = _CompilationUnit(
            path=path,
            payload=payload,
            root=root,
            module=module,
            package_name=package_name,
            package_node=package_node,
            imports=tuple(imports),
            file_entity=file_entity,
        )
        self.units.append(unit)
        if file_epistemics.coverage is CognitionCoverage.PARTIAL:
            return
        for node in root.named_children:
            if node.type in _TYPE_DECLARATIONS:
                self._project_type(unit, node, file_entity, enclosing_name=None)

    def _package(
        self,
        module: JavaCognitionModuleSource,
        package_name: str,
        node: Node | None,
        path: str,
        payload: bytes,
    ) -> CognitionEntity:
        key = (module.module_root, package_name)
        existing = self._package_entities.get(key)
        if existing is not None:
            return existing
        module_entity = self._module_entities[module.module_root]
        provenance = (
            self._node_provenance(path, payload, node, "JAVA_PACKAGE_DECLARATION")
            if node is not None
            else self._node_provenance(path, payload, self.parser.parse(payload).root_node, "JAVA_DEFAULT_PACKAGE")
        )
        display = package_name or "<default>"
        entity = self._entity(
            kind=CognitionEntityKind.PACKAGE,
            identity=(module.module_root, display),
            name=display.rsplit(".", 1)[-1],
            qualified_name=f"{module.module_name}:{display}",
            parent_id=module_entity.entity_id,
            provenance=provenance,
            attributes=(("java_package", display), ("module", module.module_name)),
        )
        self.entities.append(entity)
        self._package_entities[key] = entity
        self.relations.append(
            self._relation(
                CognitionRelationKind.CONTAINS,
                module_entity,
                object_entity=entity,
                object_symbol=entity.qualified_name,
                provenance=provenance,
            )
        )
        return entity

    def _project_type(
        self,
        unit: _CompilationUnit,
        node: Node,
        parent: CognitionEntity,
        *,
        enclosing_name: str | None,
    ) -> None:
        name_node = node.child_by_field_name("name")
        body = node.child_by_field_name("body")
        if name_node is None or body is None:
            self.partial_file_count += 1
            self.unknowns.append(f"type declaration without canonical name/body at {unit.path}")
            return
        simple = _node_text(unit.payload, name_node)
        local = simple if enclosing_name is None else f"{enclosing_name}.{simple}"
        qualified = f"{unit.package_name}.{local}" if unit.package_name else local
        declaration_kind = node.type.removesuffix("_declaration").upper()
        entity = self._entity(
            kind=CognitionEntityKind.TYPE,
            identity=(unit.path, qualified, str(node.start_byte)),
            name=simple,
            qualified_name=qualified,
            parent_id=parent.entity_id,
            provenance=self._node_provenance(unit.path, unit.payload, node, "JAVA_TYPE_DECLARATION"),
            attributes=(
                ("declaration_kind", declaration_kind),
                ("package", unit.package_name or "<default>"),
                ("source_path", unit.path),
            ),
        )
        projection = _TypeProjection(
            entity=entity,
            node=node,
            body=body,
            unit=unit,
            fields=self._fields(body, unit.payload),
            inheritance=self._inheritance(node, unit.payload),
            methods=[],
        )
        self.entities.append(entity)
        self.types.append(projection)
        self.relations.append(
            self._relation(
                CognitionRelationKind.CONTAINS,
                parent,
                object_entity=entity,
                object_symbol=qualified,
                provenance=entity.provenance,
            )
        )
        for child in _direct_type_members(body):
            if child.type in {"method_declaration", "constructor_declaration", "compact_constructor_declaration"}:
                method = self._project_method(projection, child)
                if method is not None:
                    projection.methods.append(method)
                    self.methods.append(method)
            elif child.type in _TYPE_DECLARATIONS:
                self._project_type(unit, child, entity, enclosing_name=local)

    def _project_method(self, owner: _TypeProjection, node: Node) -> _MethodProjection | None:
        payload = owner.unit.payload
        name_node = node.child_by_field_name("name")
        parameters_node = node.child_by_field_name("parameters")
        body = node.child_by_field_name("body")
        if name_node is None:
            if node.type == "compact_constructor_declaration":
                name = owner.entity.name
            else:
                self.unknowns.append(f"method without canonical name at {owner.unit.path}")
                return None
        else:
            name = _node_text(payload, name_node)
        parameters: dict[str, str] = {}
        parameter_types: list[str] = []
        if parameters_node is not None:
            for parameter in parameters_node.named_children:
                parameter_name = parameter.child_by_field_name("name")
                parameter_type = parameter.child_by_field_name("type")
                if parameter_name is None or parameter_type is None:
                    continue
                declared = _node_text(payload, parameter_type)
                parameters[_node_text(payload, parameter_name)] = declared
                parameter_types.append(declared)
        return_node = node.child_by_field_name("type")
        return_type = owner.entity.name if "constructor" in node.type else (
            _node_text(payload, return_node) if return_node is not None else "void"
        )
        signature = f"{owner.entity.qualified_name}#{name}({','.join(parameter_types)})"
        modifier_text = _modifier_text(node, payload)
        entity = self._entity(
            kind=CognitionEntityKind.METHOD,
            identity=(owner.unit.path, signature, str(node.start_byte)),
            name=name,
            qualified_name=signature,
            parent_id=owner.entity.entity_id,
            provenance=self._node_provenance(owner.unit.path, payload, node, "JAVA_METHOD_DECLARATION"),
            attributes=tuple(
                sorted(
                    {
                        "arity": str(len(parameter_types)),
                        "declaration_kind": node.type,
                        "modifiers": modifier_text or "<none>",
                        "return_type": return_type,
                        "source_path": owner.unit.path,
                    }.items()
                )
            ),
        )
        self.entities.append(entity)
        self.relations.append(
            self._relation(
                CognitionRelationKind.CONTAINS,
                owner.entity,
                object_entity=entity,
                object_symbol=signature,
                provenance=entity.provenance,
            )
        )
        return _MethodProjection(entity, node, body, owner, len(parameter_types), parameters)

    def _index_types_and_methods(self) -> None:
        self.types_by_qualified: dict[str, list[_TypeProjection]] = {}
        self.types_by_simple: dict[str, list[_TypeProjection]] = {}
        for item in self.types:
            self.types_by_qualified.setdefault(item.entity.qualified_name, []).append(item)
            self.types_by_simple.setdefault(item.entity.name, []).append(item)
        for qualified, values in self.types_by_qualified.items():
            if len(values) > 1:
                self.conflicts.append(f"duplicate Java type identity: {qualified}")
        self.methods_by_owner_name_arity: dict[tuple[str, str, int], list[_MethodProjection]] = {}
        for item in self.methods:
            self.methods_by_owner_name_arity.setdefault(
                (item.owner.entity.qualified_name, item.entity.name, item.arity), []
            ).append(item)

    def _project_imports_and_inheritance(self) -> None:
        for unit in self.units:
            for imported, node, is_static, is_wildcard in unit.imports:
                target, resolution, unknowns = self._resolve_type(imported, unit, allow_wildcard=is_wildcard)
                attributes = tuple(sorted({"static": str(is_static).lower(), "wildcard": str(is_wildcard).lower()}.items()))
                self.relations.append(
                    self._relation(
                        CognitionRelationKind.IMPORTS,
                        unit.file_entity,
                        object_entity=target.entity if target is not None else None,
                        object_symbol=imported,
                        resolution=resolution,
                        provenance=self._node_provenance(unit.path, unit.payload, node, "JAVA_IMPORT_DECLARATION"),
                        unknowns=unknowns,
                        attributes=attributes,
                    )
                )
        for item in self.types:
            for raw_target, node in item.inheritance:
                target, resolution, unknowns = self._resolve_type(raw_target, item.unit)
                self.relations.append(
                    self._relation(
                        CognitionRelationKind.INHERITS,
                        item.entity,
                        object_entity=target.entity if target is not None else None,
                        object_symbol=raw_target,
                        resolution=resolution,
                        provenance=self._node_provenance(item.unit.path, item.unit.payload, node, "JAVA_INHERITANCE_CLAUSE"),
                        unknowns=unknowns,
                    )
                )

    def _project_method_behavior(self) -> None:
        for method in self.methods:
            if method.body is None:
                continue
            variables = dict(method.owner.fields)
            variables.update(method.parameters)
            for node in _walk_executable(method.body):
                if node.type == "local_variable_declaration":
                    declared_type = node.child_by_field_name("type")
                    if declared_type is not None:
                        for child in node.named_children:
                            if child.type == "variable_declarator":
                                name = child.child_by_field_name("name")
                                if name is not None:
                                    variables[_node_text(method.owner.unit.payload, name)] = _node_text(method.owner.unit.payload, declared_type)
            candidates: list[tuple[int, str, Node]] = []
            for node in _walk_executable(method.body):
                if node.type == "method_invocation":
                    candidates.append((node.start_byte, "CALL", node))
                elif node.type in _CONDITION_NODES:
                    candidates.append((node.start_byte, "CONDITION", node))
                elif node.type == "throw_statement":
                    candidates.append((node.start_byte, "THROWS", node))
                elif node.type == "catch_clause":
                    candidates.append((node.start_byte, "CATCHES", node))
                elif node.type == "return_statement":
                    candidates.append((node.start_byte, "RETURN", node))
                elif node.type in {"assignment_expression", "update_expression"}:
                    candidates.append((node.start_byte, "STATE_WRITE", node))
                elif node.type == "field_access":
                    candidates.append((node.start_byte, "STATE_READ", node))
            candidates.sort(key=lambda item: (item[0], item[1], item[2].end_byte))
            if len(candidates) > 96:
                self.unknowns.append(
                    f"behavior projection truncated at 96 atoms for {method.entity.qualified_name}"
                )
                candidates = candidates[:96]
            write_ranges = {
                (node.start_byte, node.end_byte)
                for _, kind, node in candidates
                if kind == "STATE_WRITE"
            }
            for _, candidate_kind, node in candidates:
                if candidate_kind == "CALL":
                    relation = self._invocation_relation(method, node, variables)
                    self.relations.append(relation)
                    behavior_kind = (
                        CognitionBehaviorKind.EXTERNAL_CALL
                        if relation.resolution is CognitionResolution.EXTERNAL
                        else CognitionBehaviorKind.CALL
                    )
                    self._behavior(method, behavior_kind, node, relation=relation)
                elif candidate_kind == "CONDITION":
                    condition = node.child_by_field_name("condition")
                    self._behavior(method, CognitionBehaviorKind.CONDITION, condition or node)
                elif candidate_kind == "THROWS":
                    self._behavior(method, CognitionBehaviorKind.THROWS, node)
                elif candidate_kind == "CATCHES":
                    self._behavior(method, CognitionBehaviorKind.CATCHES, node)
                elif candidate_kind == "RETURN":
                    self._behavior(method, CognitionBehaviorKind.RETURN, node)
                elif candidate_kind == "STATE_WRITE":
                    left = node.child_by_field_name("left") or node.child_by_field_name("argument")
                    if left is not None and self._is_field_reference(method.owner, left):
                        self._behavior(method, CognitionBehaviorKind.STATE_WRITE, node)
                elif candidate_kind == "STATE_READ":
                    if any(start <= node.start_byte and node.end_byte <= end for start, end in write_ranges):
                        continue
                    if self._is_field_reference(method.owner, node):
                        self._behavior(method, CognitionBehaviorKind.STATE_READ, node)

    def _invocation_relation(
        self,
        method: _MethodProjection,
        node: Node,
        variables: Mapping[str, str],
    ) -> CognitionRelation:
        payload = method.owner.unit.payload
        name_node = node.child_by_field_name("name")
        arguments = node.child_by_field_name("arguments")
        object_node = node.child_by_field_name("object")
        name = _node_text(payload, name_node) if name_node is not None else "<unknown>"
        arity = len(arguments.named_children) if arguments is not None else 0
        owner_type: _TypeProjection | None = None
        owner_symbol: str
        resolution = CognitionResolution.UNKNOWN
        unknowns: tuple[str, ...] = ("call receiver or target cannot be resolved statically",)
        if object_node is None or _node_text(payload, object_node) in {"this", "super"}:
            owner_type = method.owner
            owner_symbol = method.owner.entity.qualified_name
        else:
            receiver = _node_text(payload, object_node)
            variable_name = receiver.rsplit(".", 1)[-1]
            declared = variables.get(variable_name)
            if declared is not None:
                owner_type, type_resolution, type_unknowns = self._resolve_type(declared, method.owner.unit)
                owner_symbol = self._qualified_type_symbol(declared, method.owner.unit)
                resolution = type_resolution
                unknowns = type_unknowns
            else:
                owner_type, type_resolution, type_unknowns = self._resolve_type(receiver, method.owner.unit)
                owner_symbol = self._qualified_type_symbol(receiver, method.owner.unit)
                resolution = type_resolution
                unknowns = type_unknowns
        target: _MethodProjection | None = None
        if owner_type is not None:
            candidates = self.methods_by_owner_name_arity.get(
                (owner_type.entity.qualified_name, name, arity), ()
            )
            if len(candidates) == 1:
                target = candidates[0]
                resolution = CognitionResolution.INTERNAL
                unknowns = ()
            elif len(candidates) > 1:
                resolution = CognitionResolution.AMBIGUOUS
                unknowns = ("multiple source methods match the static owner/name/arity",)
            elif self._inherits_external(owner_type):
                resolution = CognitionResolution.EXTERNAL
                unknowns = ("target method may be supplied by an external inherited type",)
            else:
                resolution = CognitionResolution.UNKNOWN
                unknowns = ("static owner is internal but no exact method declaration matches",)
        elif resolution is CognitionResolution.INTERNAL:
            resolution = CognitionResolution.UNKNOWN
        object_symbol = (
            target.entity.qualified_name if target is not None else f"{owner_symbol}#{name}/{arity}"
        )
        return self._relation(
            CognitionRelationKind.INVOKES,
            method.entity,
            object_entity=target.entity if target is not None else None,
            object_symbol=object_symbol,
            resolution=resolution,
            provenance=self._node_provenance(method.owner.unit.path, payload, node, "JAVA_METHOD_INVOCATION"),
            unknowns=unknowns,
            attributes=(("arity", str(arity)), ("method_name", name)),
        )

    def _resolve_type(
        self,
        raw: str,
        unit: _CompilationUnit,
        *,
        allow_wildcard: bool = False,
    ) -> tuple[_TypeProjection | None, CognitionResolution, tuple[str, ...]]:
        base = _base_type(raw)
        if allow_wildcard or raw.endswith(".*"):
            return None, CognitionResolution.UNKNOWN, ("wildcard target cannot resolve to one exact type",)
        candidates: list[_TypeProjection] = []
        if "." in base:
            candidates.extend(self.types_by_qualified.get(base, ()))
        else:
            imported = {
                value.rsplit(".", 1)[-1]: value
                for value, _, is_static, is_wildcard in unit.imports
                if not is_static and not is_wildcard
            }.get(base)
            if imported is not None:
                candidates.extend(self.types_by_qualified.get(imported, ()))
            same_package = f"{unit.package_name}.{base}" if unit.package_name else base
            candidates.extend(self.types_by_qualified.get(same_package, ()))
            if not candidates:
                candidates.extend(self.types_by_simple.get(base, ()))
        unique = {item.entity.entity_id: item for item in candidates}
        if len(unique) == 1:
            return next(iter(unique.values())), CognitionResolution.INTERNAL, ()
        if len(unique) > 1:
            return None, CognitionResolution.AMBIGUOUS, ("type reference matches multiple selected Source types",)
        qualified = self._qualified_type_symbol(raw, unit)
        if qualified and qualified != "<unknown>":
            return None, CognitionResolution.EXTERNAL, ("type implementation is outside selected Source coverage",)
        return None, CognitionResolution.UNKNOWN, ("type reference cannot be resolved statically",)

    def _qualified_type_symbol(self, raw: str, unit: _CompilationUnit) -> str:
        base = _base_type(raw)
        if not base:
            return "<unknown>"
        if "." in base:
            return base
        imported = {
            value.rsplit(".", 1)[-1]: value
            for value, _, is_static, is_wildcard in unit.imports
            if not is_static and not is_wildcard
        }.get(base)
        if imported is not None:
            return imported
        same_package = f"{unit.package_name}.{base}" if unit.package_name else base
        if same_package in self.types_by_qualified:
            return same_package
        return base

    def _inherits_external(self, owner: _TypeProjection) -> bool:
        return any(
            self._resolve_type(raw, owner.unit)[1] is CognitionResolution.EXTERNAL
            for raw, _ in owner.inheritance
        )

    def _behavior(
        self,
        method: _MethodProjection,
        kind: CognitionBehaviorKind,
        node: Node,
        *,
        relation: CognitionRelation | None = None,
    ) -> None:
        payload = method.owner.unit.payload
        statement, truncated = _display_text(payload, node)
        unknowns = ("display text was truncated; provenance digest still covers the exact Source range",) if truncated else ()
        provenance = self._node_provenance(
            method.owner.unit.path,
            payload,
            node,
            f"JAVA_BEHAVIOR_{kind.value}",
        )
        ordinal = sum(item.method_id == method.entity.entity_id for item in self.behaviors)
        allocation = digest_of(
            [
                CAPABILITY_COGNITION_PROFILE,
                method.entity.entity_id.value,
                kind.value,
                ordinal,
                provenance.content_digest.value,
            ]
        )
        self.behaviors.append(
            CognitionBehavior(
                behavior_id=StableId(f"cog_behavior_{allocation.value[-32:]}"),
                method_id=method.entity.entity_id,
                kind=kind,
                ordinal=ordinal,
                statement=statement,
                relation_id=relation.relation_id if relation is not None else None,
                provenance=provenance,
                epistemics=(
                    CognitionEpistemics(CognitionCoverage.PARTIAL, unknowns=unknowns)
                    if unknowns
                    else CognitionEpistemics(CognitionCoverage.COMPLETE)
                ),
            )
        )

    def _entity(
        self,
        *,
        kind: CognitionEntityKind,
        identity: Sequence[str],
        name: str,
        qualified_name: str,
        parent_id: StableId | None,
        provenance: CognitionProvenance,
        epistemics: CognitionEpistemics | None = None,
        attributes: tuple[tuple[str, str], ...] = (),
    ) -> CognitionEntity:
        allocation = digest_of([CAPABILITY_COGNITION_PROFILE, "ENTITY", kind.value, tuple(identity)])
        return CognitionEntity(
            entity_id=StableId(f"cog_entity_{allocation.value[-32:]}"),
            kind=kind,
            name=name,
            qualified_name=qualified_name,
            parent_id=parent_id,
            provenance=provenance,
            epistemics=epistemics or CognitionEpistemics(CognitionCoverage.COMPLETE),
            attributes=tuple(sorted(attributes)),
        )

    def _relation(
        self,
        kind: CognitionRelationKind,
        subject: CognitionEntity,
        *,
        object_entity: CognitionEntity | None,
        object_symbol: str,
        provenance: CognitionProvenance,
        resolution: CognitionResolution = CognitionResolution.INTERNAL,
        unknowns: tuple[str, ...] = (),
        conflicts: tuple[str, ...] = (),
        attributes: tuple[tuple[str, str], ...] = (),
    ) -> CognitionRelation:
        if object_entity is None and resolution is CognitionResolution.INTERNAL:
            raise DomainError(ErrorCode.AUTHORITY_RECORD_INCONSISTENT, "internal cognition relation lacks target")
        epistemics = (
            CognitionEpistemics(
                CognitionCoverage.PARTIAL,
                conflicts=tuple(sorted(set(conflicts))),
                unknowns=tuple(sorted(set(unknowns))),
            )
            if conflicts or unknowns or resolution is not CognitionResolution.INTERNAL
            else CognitionEpistemics(CognitionCoverage.COMPLETE)
        )
        allocation = digest_of(
            [
                CAPABILITY_COGNITION_PROFILE,
                "RELATION",
                kind.value,
                subject.entity_id.value,
                object_entity.entity_id.value if object_entity is not None else None,
                object_symbol,
                provenance.path,
                provenance.start_line,
                provenance.content_digest.value,
                len(self.relations),
            ]
        )
        return CognitionRelation(
            relation_id=StableId(f"cog_relation_{allocation.value[-32:]}"),
            kind=kind,
            subject_id=subject.entity_id,
            object_id=object_entity.entity_id if object_entity is not None else None,
            object_symbol=object_symbol,
            resolution=resolution,
            provenance=provenance,
            epistemics=epistemics,
            attributes=tuple(sorted(attributes)),
        )

    def _module_for(self, path: str) -> JavaCognitionModuleSource:
        matches = [item for item in self.source.modules if _under(path, item.module_root)]
        if not matches:
            raise DomainError(ErrorCode.SOURCE_TARGET_OUT_OF_SCOPE, f"no module owns {path}")
        matches.sort(key=lambda item: len(PurePosixPath(item.module_root).parts), reverse=True)
        return matches[0]

    def _package_name(self, node: Node | None, payload: bytes) -> str:
        if node is None:
            return ""
        name = next(
            (
                item
                for item in node.named_children
                if item.type in {"scoped_identifier", "identifier"}
            ),
            None,
        )
        return _node_text(payload, name) if name is not None else ""

    def _fields(self, body: Node, payload: bytes) -> dict[str, str]:
        values: dict[str, str] = {}
        for child in _direct_type_members(body):
            if child.type != "field_declaration":
                continue
            type_node = child.child_by_field_name("type")
            if type_node is None:
                continue
            declared = _node_text(payload, type_node)
            for item in child.named_children:
                if item.type != "variable_declarator":
                    continue
                name = item.child_by_field_name("name")
                if name is not None:
                    values[_node_text(payload, name)] = declared
        return values

    @staticmethod
    def _inheritance(node: Node, payload: bytes) -> tuple[tuple[str, Node], ...]:
        values: list[tuple[str, Node]] = []
        for child in node.named_children:
            if child.type not in {"superclass", "super_interfaces", "extends_interfaces"}:
                continue
            candidates = child.named_children
            if len(candidates) == 1 and candidates[0].type == "type_list":
                candidates = candidates[0].named_children
            for candidate in candidates:
                text = _node_text(payload, candidate)
                if text:
                    values.append((text, candidate))
        return tuple(values)

    @staticmethod
    def _is_field_reference(owner: _TypeProjection, node: Node) -> bool:
        text = _node_text(owner.unit.payload, node)
        name = text.rsplit(".", 1)[-1]
        return name in owner.fields

    def _node_provenance(
        self,
        path: str,
        payload: bytes,
        node: Node,
        evidence_kind: str,
    ) -> CognitionProvenance:
        excerpt = payload[node.start_byte : node.end_byte]
        return CognitionProvenance(
            source_revision=self.source.source_revision,
            source_tree=self.source.source_tree,
            path=path,
            start_line=_row(node.start_point) + 1,
            end_line=max(_row(node.start_point) + 1, _row(node.end_point) + 1),
            content_digest=Digest("sha256:" + hashlib.sha256(excerpt).hexdigest()),
            evidence_kind=evidence_kind,
        )

    def _bytes_provenance(
        self,
        path: str,
        payload: bytes,
        evidence_kind: str,
    ) -> CognitionProvenance:
        return CognitionProvenance(
            source_revision=self.source.source_revision,
            source_tree=self.source.source_tree,
            path=path,
            start_line=1,
            end_line=max(1, payload.count(b"\n") + 1),
            content_digest=Digest("sha256:" + hashlib.sha256(payload).hexdigest()),
            evidence_kind=evidence_kind,
        )


def build_java_capability_cognition(
    source: ExactJavaCognitionSource,
) -> CapabilityCognitionSnapshot:
    return JavaCapabilityCognitionBuilder().build(source)


def _walk_executable(root: Node):
    stack = [root]
    while stack:
        node = stack.pop()
        if node is not root and node.type in _EXECUTABLE_BOUNDARIES:
            continue
        yield node
        stack.extend(reversed(node.named_children))


def _direct_type_members(body: Node):
    for child in body.named_children:
        if child.type == "enum_body_declarations":
            yield from child.named_children
        else:
            yield child


def _node_text(payload: bytes, node: Node | None) -> str:
    if node is None:
        return ""
    return payload[node.start_byte : node.end_byte].decode("utf-8", errors="strict")


def _display_text(payload: bytes, node: Node) -> tuple[str, bool]:
    value = " ".join(_node_text(payload, node).split())
    if not value:
        value = f"<{node.type}>"
    if len(value) <= 1024:
        return value, False
    return value[:1023] + "…", True


def _modifier_text(node: Node, payload: bytes) -> str:
    modifiers = next((item for item in node.named_children if item.type == "modifiers"), None)
    return " ".join(_node_text(payload, modifiers).split()) if modifiers is not None else ""


def _base_type(value: str) -> str:
    text = re.sub(r"@[A-Za-z_$][A-Za-z0-9_$.]*(?:\([^)]*\))?", "", value).strip()
    text = re.sub(r"<.*>", "", text)
    text = text.replace("[]", "").replace("...", "").strip()
    return text.split()[-1] if text else ""


def _row(value) -> int:
    return int(value.row if hasattr(value, "row") else value[0])


def _under(path: str, root: str) -> bool:
    path_parts = PurePosixPath(path).parts
    root_parts = PurePosixPath(root).parts
    return path_parts[: len(root_parts)] == root_parts


def _under_any(path: str, roots: Sequence[str]) -> bool:
    return any(_under(path, root) for root in roots)


def _relative_path(value: str) -> str:
    text = _text(value, "Java cognition path")
    path = PurePosixPath(text)
    if path.is_absolute() or str(path) != text or any(part in {"", ".", ".."} for part in path.parts):
        raise DomainError(ErrorCode.INVALID_ARGUMENT, "Java cognition path must be canonical and relative")
    return text


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} must be canonical non-empty text")
    return value


__all__ = [
    "ExactJavaCognitionSource",
    "JavaCapabilityCognitionBuilder",
    "JavaCognitionModuleSource",
    "build_java_capability_cognition",
]
