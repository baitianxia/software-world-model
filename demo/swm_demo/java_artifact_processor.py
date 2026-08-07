from __future__ import annotations

import json
from typing import Iterable

from tree_sitter import Language, Node, Parser
import tree_sitter_java

from swm_demo.artifact_contract import SourceArtifact
from swm_demo.ids import content_hash, stable_id


PROCESSOR_VERSION = "java-ast-v1"


class JavaArtifactProcessor:
    """Turns Java source into a generic, replayable AST summary Artifact.

    The processor records syntax and source locations only. It does not decide
    which declarations are Entities or which relations are Facts; those are
    Knowledge Engine responsibilities.
    """

    def __init__(self) -> None:
        language = Language(tree_sitter_java.language())
        self.parser = Parser(language)

    def derive(self, source: SourceArtifact) -> SourceArtifact:
        raw = source.content.encode("utf-8")
        tree = self.parser.parse(raw)
        if tree.root_node.has_error:
            raise ValueError(f"Java parser reported syntax errors: {source.relative_path}")

        package = ""
        imports: list[dict[str, object]] = []
        types: list[dict[str, object]] = []

        for node in tree.root_node.named_children:
            if node.type == "package_declaration":
                package = self._declaration_name(node, raw, "package", ";")
            elif node.type == "import_declaration":
                text = self._text(node, raw).strip()
                value = text.removeprefix("import ").removesuffix(";").strip()
                is_static = value.startswith("static ")
                if is_static:
                    value = value.removeprefix("static ").strip()
                imports.append(
                    {
                        "name": value.removesuffix(".*"),
                        "wildcard": value.endswith(".*"),
                        "static": is_static,
                        "line": node.start_point.row + 1,
                    }
                )
            elif node.type in {
                "class_declaration",
                "interface_declaration",
                "enum_declaration",
                "record_declaration",
            }:
                types.append(self._type(node, raw, package))

        payload = {
            "schema": PROCESSOR_VERSION,
            "source_artifact_id": source.artifact_id,
            "source_path": source.relative_path,
            "package": package,
            "imports": imports,
            "types": types,
        }
        rendered = json.dumps(
            payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
        digest = content_hash(rendered)
        return SourceArtifact(
            artifact_id=stable_id(
                "artifact",
                source.scope_id,
                source.relative_path,
                source.revision,
                PROCESSOR_VERSION,
                digest,
            ),
            artifact_type="java-ast-summary",
            source_id=source.source_id,
            scope_id=source.scope_id,
            relative_path=f"{source.relative_path}#{PROCESSOR_VERSION}.json",
            revision=source.revision,
            content_hash=digest,
            content=rendered,
            lineage_ids=(source.artifact_id,),
        )

    def _type(
        self, node: Node, raw: bytes, package: str
    ) -> dict[str, object]:
        name_node = node.child_by_field_name("name")
        if name_node is None:
            raise ValueError("Java type declaration has no name")
        name = self._text(name_node, raw)
        body = node.child_by_field_name("body")
        declaration_line = name_node.start_point.row + 1
        annotations = self._annotations(node, raw)

        interfaces_node = node.child_by_field_name("interfaces")
        interfaces = (
            [
                self._text(item, raw)
                for item in self._walk(interfaces_node)
                if item.type in {"type_identifier", "scoped_type_identifier"}
                and not any(
                    ancestor.type in {"type_arguments", "generic_type"}
                    for ancestor in self._ancestors_until(item, interfaces_node)
                )
            ]
            if interfaces_node is not None
            else []
        )
        # Tree-sitter can expose both a scoped type and its child identifiers;
        # retain the widest unique spelling in source order.
        interfaces = self._outermost_type_names(interfaces)

        fields: list[dict[str, object]] = []
        methods: list[dict[str, object]] = []
        nested_types: list[dict[str, object]] = []
        if body is not None:
            for member in body.named_children:
                if member.type == "field_declaration":
                    fields.extend(self._fields(member, raw))
                elif member.type in {"method_declaration", "constructor_declaration"}:
                    methods.append(self._method(member, raw))
                elif member.type in {
                    "class_declaration",
                    "interface_declaration",
                    "enum_declaration",
                    "record_declaration",
                }:
                    nested_types.append(self._type(member, raw, f"{package}.{name}"))

        superclass_node = node.child_by_field_name("superclass")
        return {
            "kind": node.type.removesuffix("_declaration"),
            "name": name,
            "qualified_name": f"{package}.{name}" if package else name,
            "line_start": node.start_point.row + 1,
            "line_end": node.end_point.row + 1,
            "declaration_line": declaration_line,
            "declaration_text": self._line(raw, declaration_line),
            "annotations": annotations,
            "interfaces": interfaces,
            "superclass": (
                self._text(superclass_node, raw) if superclass_node is not None else None
            ),
            "fields": fields,
            "methods": methods,
            "nested_types": nested_types,
        }

    def _fields(self, node: Node, raw: bytes) -> list[dict[str, object]]:
        type_node = node.child_by_field_name("type")
        declared_type = self._text(type_node, raw) if type_node is not None else ""
        result: list[dict[str, object]] = []
        for item in node.named_children:
            if item.type != "variable_declarator":
                continue
            name_node = item.child_by_field_name("name")
            if name_node is None:
                continue
            line = name_node.start_point.row + 1
            result.append(
                {
                    "name": self._text(name_node, raw),
                    "type": declared_type,
                    "line": line,
                    "text": self._line(raw, line),
                }
            )
        return result

    def _method(self, node: Node, raw: bytes) -> dict[str, object]:
        name_node = node.child_by_field_name("name")
        if name_node is None:
            raise ValueError("Java method declaration has no name")
        parameters_node = node.child_by_field_name("parameters")
        parameter_types: list[str] = []
        if parameters_node is not None:
            for parameter in parameters_node.named_children:
                if parameter.type not in {
                    "formal_parameter",
                    "spread_parameter",
                    "receiver_parameter",
                }:
                    continue
                type_node = parameter.child_by_field_name("type")
                if type_node is not None:
                    value = self._text(type_node, raw)
                    if parameter.type == "spread_parameter":
                        value += "..."
                    parameter_types.append(value)

        return_type = node.child_by_field_name("type")
        calls: list[dict[str, object]] = []
        comments: list[dict[str, object]] = []
        guards: list[dict[str, object]] = []
        body = node.child_by_field_name("body")
        if body is not None:
            for item in self._walk(body):
                if item.type == "method_invocation":
                    call_name = item.child_by_field_name("name")
                    arguments = item.child_by_field_name("arguments")
                    object_node = item.child_by_field_name("object")
                    if call_name is None:
                        continue
                    calls.append(
                        {
                            "object": (
                                self._text(object_node, raw)
                                if object_node is not None
                                else None
                            ),
                            "name": self._text(call_name, raw),
                            "arity": (
                                len(arguments.named_children)
                                if arguments is not None
                                else 0
                            ),
                            "line": item.start_point.row + 1,
                            "text": self._text(item, raw),
                        }
                    )
                elif item.type in {"line_comment", "block_comment"}:
                    comments.append(
                        {
                            "line_start": item.start_point.row + 1,
                            "line_end": item.end_point.row + 1,
                            "text": self._text(item, raw).strip(),
                        }
                    )
                elif item.type == "if_statement":
                    guard = self._failure_guard(item, raw)
                    if guard is not None:
                        guards.append(guard)

        signature_line = name_node.start_point.row + 1
        return {
            "name": self._text(name_node, raw),
            "parameter_types": parameter_types,
            "arity": len(parameter_types),
            "return_type": (
                self._text(return_type, raw) if return_type is not None else None
            ),
            "line_start": node.start_point.row + 1,
            "line_end": node.end_point.row + 1,
            "signature_line": signature_line,
            "signature_text": self._line(raw, signature_line),
            "annotations": self._annotations(node, raw),
            "calls": calls,
            "comments": comments,
            "failure_guards": guards,
        }

    def _failure_guard(self, node: Node, raw: bytes) -> dict[str, object] | None:
        condition = node.child_by_field_name("condition")
        consequence = node.child_by_field_name("consequence")
        if condition is None or consequence is None:
            return None
        failure_call: Node | None = None
        for item in self._walk(consequence):
            if item.type != "method_invocation":
                continue
            name = item.child_by_field_name("name")
            if name is not None and self._text(name, raw) == "fail":
                failure_call = item
                break
        if failure_call is None:
            return None
        arguments = failure_call.child_by_field_name("arguments")
        message = None
        if arguments is not None:
            literal = next(
                (child for child in arguments.named_children if child.type == "string_literal"),
                None,
            )
            if literal is not None:
                message = self._text(literal, raw).strip('"')
        line = failure_call.start_point.row + 1
        return {
            "condition": self._text(condition, raw),
            "message": message,
            "line_start": node.start_point.row + 1,
            "line_end": failure_call.end_point.row + 1,
            "failure_line": line,
            "failure_text": self._line(raw, line),
        }

    def _annotations(self, node: Node, raw: bytes) -> list[dict[str, object]]:
        modifiers = next(
            (child for child in node.named_children if child.type == "modifiers"),
            None,
        )
        if modifiers is None:
            return []
        result: list[dict[str, object]] = []
        for item in modifiers.named_children:
            if item.type not in {"annotation", "marker_annotation"}:
                continue
            name_node = item.child_by_field_name("name")
            text = self._text(item, raw)
            name = (
                self._text(name_node, raw)
                if name_node is not None
                else text.lstrip("@").split("(", maxsplit=1)[0]
            )
            result.append(
                {
                    "name": name,
                    "text": text,
                    "line_start": item.start_point.row + 1,
                    "line_end": item.end_point.row + 1,
                }
            )
        return result

    @staticmethod
    def _walk(node: Node | None) -> Iterable[Node]:
        if node is None:
            return
        stack = list(reversed(node.named_children))
        while stack:
            current = stack.pop()
            yield current
            stack.extend(reversed(current.named_children))

    @staticmethod
    def _ancestors_until(node: Node, stop: Node) -> Iterable[Node]:
        current = node.parent
        while current is not None and current != stop:
            yield current
            current = current.parent

    @staticmethod
    def _outermost_type_names(values: list[str]) -> list[str]:
        result: list[str] = []
        for value in values:
            if value in result:
                continue
            if any(other != value and value in other for other in values):
                continue
            result.append(value)
        return result

    @staticmethod
    def _text(node: Node, raw: bytes) -> str:
        return raw[node.start_byte : node.end_byte].decode("utf-8")

    @staticmethod
    def _line(raw: bytes, line_number: int) -> str:
        return raw.decode("utf-8").splitlines()[line_number - 1].strip()

    @staticmethod
    def _declaration_name(node: Node, raw: bytes, prefix: str, suffix: str) -> str:
        text = JavaArtifactProcessor._text(node, raw).strip()
        return text.removeprefix(f"{prefix} ").removesuffix(suffix).strip()
