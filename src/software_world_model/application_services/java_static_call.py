"""Deterministic Java static-call knowledge candidate for the ITER-006 profile.

The parser intentionally accepts a small, closed Java subset.  Unsupported or
ambiguous source fails the complete candidate instead of producing a partial
graph that could later support an unsafe negative answer.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import PurePosixPath
import hashlib
import json
import re
import unicodedata

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
    JAVA_STATIC_CALL_CANONICALIZATION_DIGEST,
    JAVA_STATIC_CALL_CANONICALIZATION_REF,
    JAVA_STATIC_CALL_COVERAGE_ROOT_REF,
    JAVA_STATIC_CALL_EVALUATION_CONTEXT_DIGEST,
    JAVA_STATIC_CALL_EVALUATION_CONTEXT_REF,
    JAVA_STATIC_CALL_PROFILE_REF,
    JAVA_STATIC_CALL_SCHEMA_DIGEST,
    JAVA_STATIC_CALL_SCHEMA_REF,
    ObservationModality,
    PublicationMode,
    RelationFactRecord,
    RelationFactRoot,
    RelationFactState,
    RelationPredicate,
    StructureEvidence,
    StructureKnowledgeBatch,
)

from .maven_structure import GitEntryMetadata


SCHEMA_REF = JAVA_STATIC_CALL_SCHEMA_REF
SCHEMA_DIGEST = JAVA_STATIC_CALL_SCHEMA_DIGEST
PROFILE_REF = JAVA_STATIC_CALL_PROFILE_REF
COVERAGE_ROOT_REF = JAVA_STATIC_CALL_COVERAGE_ROOT_REF
EVALUATION_CONTEXT_REF = JAVA_STATIC_CALL_EVALUATION_CONTEXT_REF
EVALUATION_CONTEXT_DIGEST = JAVA_STATIC_CALL_EVALUATION_CONTEXT_DIGEST
CANONICALIZATION_REF = JAVA_STATIC_CALL_CANONICALIZATION_REF
CANONICALIZATION_DIGEST = JAVA_STATIC_CALL_CANONICALIZATION_DIGEST

_IDENTIFIER = re.compile(r"^[A-Za-z_$][A-Za-z0-9_$]*$")
_FULL_GIT_OBJECT = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
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
_CONTROL_PAREN = {
    "if",
    "for",
    "while",
    "switch",
    "catch",
    "synchronized",
    "try",
}
_PRIMITIVE_TYPES = {
    "boolean",
    "byte",
    "char",
    "double",
    "float",
    "int",
    "long",
    "short",
    "void",
}


class JavaStaticCallError(ValueError):
    """Profile rejection with a stable machine reason and source locator."""

    def __init__(self, reason_code: str, message: str, *, locator: str) -> None:
        super().__init__(message)
        self.reason_code = reason_code
        self.locator = locator


@dataclass(frozen=True, slots=True)
class JavaSourceEvidenceMetadata:
    artifact_id: StableId
    source_context_id: StableId
    artifact_content_digest: Digest
    locator: str


@dataclass(frozen=True, slots=True)
class JavaStaticCallInput:
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
class JavaStaticCallBuildReport:
    complete: bool
    source_revision: str
    source_root: str
    schema_ref: str
    schema_digest: Digest
    evaluation_context_ref: str
    evaluation_context_digest: Digest
    canonicalization_ref: str
    canonicalization_digest: Digest
    source_file_count: int
    type_count: int
    method_count: int
    declaration_count: int
    call_relation_count: int
    call_site_count: int


@dataclass(frozen=True, slots=True)
class JavaStaticCallEvaluation:
    types: tuple[EntityRecord, ...]
    methods: tuple[EntityRecord, ...]
    relations: tuple[RelationFactRecord, ...]
    coverage: CoverageRecord
    complete_member_manifest: CompleteMemberManifest
    evidence: tuple[StructureEvidence, ...]
    report: JavaStaticCallBuildReport
    batch: StructureKnowledgeBatch

    @property
    def entities(self) -> tuple[EntityRecord, ...]:
        return (*self.types, *self.methods)


@dataclass(frozen=True, slots=True)
class _Token:
    text: str
    kind: str
    byte_start: int
    byte_end: int


@dataclass(frozen=True, slots=True)
class _ParsedMethod:
    declaring_type: str
    name: str
    parameter_types: tuple[str, ...]
    return_type: str
    visibility: str
    modifiers: tuple[str, ...]
    source_path: str
    declaration_ordinal: int
    header_start: int
    header_end: int
    body_token_start: int
    body_token_end: int

    @property
    def arity(self) -> int:
        return len(self.parameter_types)

    @property
    def display_signature(self) -> str:
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
    tokens: tuple[_Token, ...]
    methods: tuple[_ParsedMethod, ...]


@dataclass(frozen=True, slots=True)
class _CallSite:
    caller_signature: str
    callee_signature: str
    source_path: str
    byte_start: int
    byte_end: int


class JavaStaticCallEvaluator:
    def evaluate(self, value: JavaStaticCallInput) -> JavaStaticCallEvaluation:
        state = _EvaluationState(value)
        return state.evaluate()


def evaluate_java_static_calls(
    value: JavaStaticCallInput,
) -> JavaStaticCallEvaluation:
    return JavaStaticCallEvaluator().evaluate(value)


class _EvaluationState:
    def __init__(self, value: JavaStaticCallInput) -> None:
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
        if self.scope_id.kind != "scope" or self.binding_id.kind != "binding":
            self._fail(
                "JAVA_AUTHORITY_ID_INVALID",
                "Java evaluation requires typed Scope and Binding IDs",
                self.source_root,
            )
        if not isinstance(self.knowledge_context_digest, Digest):
            self._fail(
                "JAVA_CONTEXT_DIGEST_INVALID",
                "Java evaluation requires a typed Context digest",
                self.source_root,
            )
        self._validate_tree_evidence()
        self._validate_source_closure()

    def evaluate(self) -> JavaStaticCallEvaluation:
        parsed_types = tuple(
            self._parse_compilation_unit(path, self.source_bytes[path])
            for path in sorted(self.source_bytes)
        )
        by_fqcn: dict[str, _ParsedType] = {}
        for parsed in parsed_types:
            if parsed.qualified_name in by_fqcn:
                self._fail(
                    "JAVA_TYPE_DUPLICATE",
                    f"Java type {parsed.qualified_name} is declared more than once",
                    parsed.source_path,
                )
            by_fqcn[parsed.qualified_name] = parsed

        parsed_methods: list[_ParsedMethod] = []
        by_signature: dict[str, _ParsedMethod] = {}
        by_target: dict[tuple[str, str, int], list[_ParsedMethod]] = {}
        for parsed in parsed_types:
            for method in parsed.methods:
                if method.display_signature in by_signature:
                    self._fail(
                        "JAVA_METHOD_SIGNATURE_DUPLICATE",
                        f"Java method signature {method.display_signature} is duplicated",
                        method.source_path,
                    )
                by_signature[method.display_signature] = method
                by_target.setdefault(
                    (method.declaring_type, method.name, method.arity), []
                ).append(method)
                parsed_methods.append(method)

        call_sites = self._resolve_calls(parsed_types, by_fqcn, by_target)
        evidence: dict[StableId, StructureEvidence] = {
            item.evidence_id: item for item in self.tree_evidence
        }

        type_records: dict[str, EntityRecord] = {}
        type_evidence: dict[str, StructureEvidence] = {}
        for parsed in parsed_types:
            support = self._evidence(
                parsed.source_path,
                parsed.header_start,
                parsed.header_end,
                "java-type-declaration",
            )
            evidence[support.evidence_id] = support
            type_evidence[parsed.qualified_name] = support
            root = EntityRoot.java_type(
                owning_scope_id=self.scope_id,
                qualified_name=parsed.qualified_name,
            )
            state = EntityState.create(
                root=root,
                state_payload_fields={
                    "simple_name": parsed.simple_name,
                    "package_name": parsed.package_name,
                    "declaration_kind": "CLASS",
                    "source_path": parsed.source_path,
                    "source_revision": self.source_revision,
                    "evidence_references": (support.evidence_id,),
                },
            )
            type_records[parsed.qualified_name] = EntityRecord(root, state)

        method_records: dict[str, EntityRecord] = {}
        method_evidence: dict[str, StructureEvidence] = {}
        for parsed in sorted(
            parsed_methods, key=lambda item: item.display_signature
        ):
            support = self._evidence(
                parsed.source_path,
                parsed.header_start,
                parsed.header_end,
                "java-method-declaration",
            )
            evidence[support.evidence_id] = support
            method_evidence[parsed.display_signature] = support
            root = EntityRoot.java_method(
                owning_scope_id=self.scope_id,
                declaring_type_qualified_name=parsed.declaring_type,
                method_name=parsed.name,
                parameter_types=parsed.parameter_types,
            )
            state = EntityState.create(
                root=root,
                state_payload_fields={
                    "return_type": parsed.return_type,
                    "visibility": parsed.visibility,
                    "modifiers": parsed.modifiers,
                    "source_path": parsed.source_path,
                    "source_revision": self.source_revision,
                    "evidence_references": (support.evidence_id,),
                },
            )
            method_records[parsed.display_signature] = EntityRecord(root, state)

        relations: list[RelationFactRecord] = []
        for parsed in sorted(
            parsed_methods,
            key=lambda item: (item.declaring_type, item.declaration_ordinal),
        ):
            relations.append(
                self._relation(
                    subject=type_records[parsed.declaring_type],
                    predicate=RelationPredicate.DECLARES_METHOD,
                    object_=method_records[parsed.display_signature],
                    modality=ObservationModality.JAVA_SOURCE_DECLARATION,
                    evidence_references=(
                        method_evidence[parsed.display_signature].evidence_id,
                    ),
                    predicate_payload={
                        "declaration_ordinal": parsed.declaration_ordinal
                    },
                )
            )

        grouped_calls: dict[tuple[str, str], list[_CallSite]] = {}
        for call in call_sites:
            grouped_calls.setdefault(
                (call.caller_signature, call.callee_signature), []
            ).append(call)
        for (caller, callee), sites in sorted(grouped_calls.items()):
            site_evidence: list[StableId] = []
            for site in sites:
                support = self._evidence(
                    site.source_path,
                    site.byte_start,
                    site.byte_end,
                    "java-static-call-site",
                )
                evidence[support.evidence_id] = support
                site_evidence.append(support.evidence_id)
            relations.append(
                self._relation(
                    subject=method_records[caller],
                    predicate=RelationPredicate.CALLS,
                    object_=method_records[callee],
                    modality=ObservationModality.JAVA_SOURCE_STATIC_CALL,
                    evidence_references=tuple(site_evidence),
                    predicate_payload={"call_site_count": len(sites)},
                )
            )

        types = tuple(
            type_records[key] for key in sorted(type_records)
        )
        methods = tuple(
            method_records[key] for key in sorted(method_records)
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
            tuple(item.coverage_member for item in (*types, *methods))
            + tuple(item.coverage_member for item in relations_tuple)
        )
        coverage = self._coverage(
            manifest,
            tuple(sorted(evidence, key=lambda item: item.value)),
        )
        evidence_tuple = tuple(
            sorted(evidence.values(), key=lambda item: item.evidence_id.value)
        )
        batch = StructureKnowledgeBatch.admit(
            evidence=evidence_tuple,
            entities=(*types, *methods),
            relation_facts=relations_tuple,
            coverage=coverage,
            publication_mode=PublicationMode.REPLACE_COVERAGE,
        )
        report = JavaStaticCallBuildReport(
            complete=True,
            source_revision=self.source_revision,
            source_root=self.source_root,
            schema_ref=SCHEMA_REF,
            schema_digest=SCHEMA_DIGEST,
            evaluation_context_ref=EVALUATION_CONTEXT_REF,
            evaluation_context_digest=EVALUATION_CONTEXT_DIGEST,
            canonicalization_ref=CANONICALIZATION_REF,
            canonicalization_digest=CANONICALIZATION_DIGEST,
            source_file_count=len(self.source_bytes),
            type_count=len(types),
            method_count=len(methods),
            declaration_count=len(parsed_methods),
            call_relation_count=len(grouped_calls),
            call_site_count=len(call_sites),
        )
        return JavaStaticCallEvaluation(
            types=types,
            methods=methods,
            relations=relations_tuple,
            coverage=coverage,
            complete_member_manifest=manifest,
            evidence=evidence_tuple,
            report=report,
            batch=batch,
        )

    def _validate_source_closure(self) -> None:
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
        if expected != set(self.source_bytes):
            missing = sorted(expected - set(self.source_bytes))
            extra = sorted(set(self.source_bytes) - expected)
            self._fail(
                "JAVA_SOURCE_CLOSURE_INCOMPLETE",
                f"Java source bytes differ from exact Git tree; missing={missing}, extra={extra}",
                self.source_root,
            )
        if set(self.source_evidence) != expected:
            self._fail(
                "JAVA_SOURCE_EVIDENCE_INCOMPLETE",
                "Java source Evidence metadata differs from exact source set",
                self.source_root,
            )
        for path in sorted(expected):
            metadata = self.git_entries[path]
            if (
                metadata.mode != "100644"
                or metadata.object_type != "blob"
                or metadata.is_symlink
                or not _FULL_GIT_OBJECT.fullmatch(metadata.object_id)
            ):
                self._fail(
                    "JAVA_SOURCE_ENTRY_UNSUPPORTED",
                    "Java source must be a regular non-symlink Git blob",
                    path,
                )
            payload = self.source_bytes[path]
            if not isinstance(payload, bytes):
                self._fail(
                    "JAVA_SOURCE_NOT_BYTES",
                    "Java source payload must be immutable bytes",
                    path,
                )
            try:
                payload.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise JavaStaticCallError(
                    "JAVA_SOURCE_UTF8_INVALID",
                    "Java source must be exact UTF-8",
                    locator=path,
                ) from exc
            evidence = self.source_evidence[path]
            if (
                evidence.artifact_id.kind != "source_artifact"
                or evidence.source_context_id.kind != "source_context"
                or not isinstance(evidence.artifact_content_digest, Digest)
                or evidence.locator != path
            ):
                self._fail(
                    "JAVA_SOURCE_EVIDENCE_INVALID",
                    "Java source Evidence metadata is not exact",
                    path,
                )
            actual_digest = Digest(
                f"sha256:{hashlib.sha256(payload).hexdigest()}"
            )
            if evidence.artifact_content_digest != actual_digest:
                self._fail(
                    "JAVA_SOURCE_CONTENT_DIGEST_MISMATCH",
                    "Java source bytes do not match their Artifact content digest",
                    path,
                )
        if not self.tree_evidence:
            self._fail(
                "JAVA_TREE_EVIDENCE_MISSING",
                "complete Java Coverage requires exact Git tree Evidence",
                self.source_root,
            )

    def _validate_tree_evidence(self) -> None:
        observed: dict[str, GitEntryMetadata] = {}
        required_keys = {"is_symlink", "mode", "object_id", "path", "type"}
        if not self.tree_evidence:
            self._fail(
                "JAVA_TREE_EVIDENCE_MISSING",
                "complete Java Coverage requires exact Git tree Evidence",
                self.source_root,
            )
        for evidence in self.tree_evidence:
            if not isinstance(evidence, StructureEvidence):
                self._fail(
                    "JAVA_TREE_EVIDENCE_INVALID",
                    "tree Evidence values must be typed StructureEvidence",
                    self.source_root,
                )
            evidence.require_valid_identity()
            if not evidence.locator.startswith(f"git-tree:{self.source_revision}:"):
                self._fail(
                    "JAVA_TREE_EVIDENCE_INVALID",
                    "tree Evidence locator is not bound to the requested revision",
                    evidence.locator,
                )
            encoded = evidence.excerpt.encode("utf-8")
            actual_digest = Digest(
                f"sha256:{hashlib.sha256(encoded).hexdigest()}"
            )
            if evidence.artifact_content_digest != actual_digest:
                self._fail(
                    "JAVA_TREE_EVIDENCE_INVALID",
                    "tree Evidence excerpt does not match its Artifact digest",
                    evidence.locator,
                )
            lines = evidence.excerpt.splitlines()
            if not lines:
                self._fail(
                    "JAVA_TREE_EVIDENCE_INVALID",
                    "tree Evidence must contain canonical JSONL entries",
                    evidence.locator,
                )
            for line_number, line in enumerate(lines, 1):
                locator = f"{evidence.locator}#line={line_number}"
                try:
                    value = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise JavaStaticCallError(
                        "JAVA_TREE_EVIDENCE_INVALID",
                        "tree Evidence line is not JSON",
                        locator=locator,
                    ) from exc
                if not isinstance(value, dict) or set(value) != required_keys:
                    self._fail(
                        "JAVA_TREE_EVIDENCE_INVALID",
                        "tree Evidence entry has the wrong shape",
                        locator,
                    )
                canonical = json.dumps(
                    value,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                    allow_nan=False,
                )
                if line != canonical:
                    self._fail(
                        "JAVA_TREE_EVIDENCE_INVALID",
                        "tree Evidence entry is not canonical JSON",
                        locator,
                    )
                raw_path = value["path"]
                mode = value["mode"]
                object_type = value["type"]
                object_id = value["object_id"]
                is_symlink = value["is_symlink"]
                if (
                    not isinstance(raw_path, str)
                    or not isinstance(mode, str)
                    or not isinstance(object_type, str)
                    or not isinstance(object_id, str)
                    or type(is_symlink) is not bool
                    or not re.fullmatch(r"[0-7]{6}", mode)
                    or not _FULL_GIT_OBJECT.fullmatch(object_id)
                    or not object_type
                    or is_symlink != (mode == "120000")
                ):
                    self._fail(
                        "JAVA_TREE_EVIDENCE_INVALID",
                        "tree Evidence entry contains invalid Git metadata",
                        locator,
                    )
                path = _path(raw_path, "tree Evidence path")
                if path != raw_path or path in observed:
                    self._fail(
                        "JAVA_TREE_EVIDENCE_INVALID",
                        "tree Evidence path is non-canonical or duplicated",
                        locator,
                    )
                observed[path] = GitEntryMetadata(
                    mode=mode,
                    object_type=object_type,
                    object_id=object_id,
                )
        if set(observed) != set(self.git_entries):
            self._fail(
                "JAVA_TREE_EVIDENCE_MISMATCH",
                "tree Evidence paths differ from supplied Git metadata",
                self.source_root,
            )
        for path, metadata in self.git_entries.items():
            if observed[path] != metadata:
                self._fail(
                    "JAVA_TREE_EVIDENCE_MISMATCH",
                    "tree Evidence metadata differs from supplied Git metadata",
                    path,
                )

    def _parse_compilation_unit(
        self, path: str, payload: bytes
    ) -> _ParsedType:
        text = payload.decode("utf-8")
        tokens = _tokenize(text, path)
        if not tokens:
            self._fail("JAVA_SOURCE_EMPTY", "Java source is empty", path)
        forbidden = next(
            (token for token in tokens if token.text in {"::", "->", "..."}),
            None,
        )
        if forbidden is not None:
            self._fail(
                "JAVA_SYNTAX_OUTSIDE_PROFILE",
                f"Java token {forbidden.text!r} is outside the static-call profile",
                _token_locator(path, forbidden),
            )

        index = 0
        package_name = ""
        if tokens[index].text == "package":
            package_name, index = _qualified_name_until(tokens, index + 1, ";", path)
        imports: dict[str, str] = {}
        while index < len(tokens) and tokens[index].text == "import":
            if index + 1 < len(tokens) and tokens[index + 1].text == "static":
                self._fail(
                    "JAVA_STATIC_IMPORT_UNSUPPORTED",
                    "static imports are outside the Java static-call profile",
                    _token_locator(path, tokens[index]),
                )
            imported, index = _qualified_name_until(tokens, index + 1, ";", path)
            if imported.endswith(".*"):
                self._fail(
                    "JAVA_WILDCARD_IMPORT_UNSUPPORTED",
                    "wildcard imports are outside the Java static-call profile",
                    path,
                )
            simple = imported.rsplit(".", 1)[-1]
            previous = imports.get(simple)
            if previous is not None and previous != imported:
                self._fail(
                    "JAVA_IMPORT_AMBIGUOUS",
                    f"simple imported type {simple} is ambiguous",
                    path,
                )
            imports[simple] = imported

        header_start_index = index
        while index < len(tokens) and tokens[index].text in _MODIFIERS:
            index += 1
        if index >= len(tokens) or tokens[index].text != "class":
            self._fail(
                "JAVA_TOP_LEVEL_CLASS_REQUIRED",
                "Java source must contain exactly one supported top-level class",
                path,
            )
        class_token = tokens[index]
        index += 1
        if index >= len(tokens) or not _is_identifier(tokens[index]):
            self._fail(
                "JAVA_TYPE_NAME_INVALID",
                "Java class declaration has no supported identifier",
                _token_locator(path, class_token),
            )
        simple_name = _identifier(tokens[index], path)
        index += 1
        if index >= len(tokens) or tokens[index].text != "{":
            self._fail(
                "JAVA_TYPE_HEADER_UNSUPPORTED",
                "generic, inherited, implemented, or malformed class headers are outside the profile",
                path,
            )
        open_index = index
        close_index = _matching_token(tokens, open_index, "{", "}", path)
        if close_index != len(tokens) - 1:
            self._fail(
                "JAVA_MULTIPLE_TOP_LEVEL_TYPES_UNSUPPORTED",
                "Java source must contain exactly one top-level class",
                _token_locator(path, tokens[close_index + 1]),
            )
        expected_simple = PurePosixPath(path).stem
        if simple_name != expected_simple:
            self._fail(
                "JAVA_TYPE_FILE_NAME_MISMATCH",
                "top-level class name must match its source file name",
                path,
            )
        relative_parent = PurePosixPath(path).relative_to(self.source_root).parent
        expected_package = (
            "" if str(relative_parent) == "." else ".".join(relative_parent.parts)
        )
        if package_name != expected_package:
            self._fail(
                "JAVA_PACKAGE_PATH_MISMATCH",
                f"package {package_name!r} differs from source path {expected_package!r}",
                path,
            )
        qualified_name = (
            f"{package_name}.{simple_name}" if package_name else simple_name
        )
        methods = self._parse_members(
            path,
            tokens,
            qualified_name,
            simple_name,
            open_index,
            close_index,
        )
        return _ParsedType(
            qualified_name=qualified_name,
            simple_name=simple_name,
            package_name=package_name,
            source_path=path,
            header_start=tokens[header_start_index].byte_start,
            header_end=tokens[open_index].byte_start,
            imports=tuple(sorted(imports.items())),
            tokens=tokens,
            methods=methods,
        )

    def _parse_members(
        self,
        path: str,
        tokens: tuple[_Token, ...],
        qualified_name: str,
        simple_name: str,
        class_open: int,
        class_close: int,
    ) -> tuple[_ParsedMethod, ...]:
        methods: list[_ParsedMethod] = []
        index = class_open + 1
        ordinal = 0
        while index < class_close:
            member_start = index
            delimiter = _next_top_level_member_delimiter(
                tokens, index, class_close, path
            )
            token = tokens[delimiter]
            segment = tokens[member_start:delimiter]
            if token.text == ";":
                if any(item.text == "(" for item in segment):
                    self._fail(
                        "JAVA_MEMBER_DECLARATION_UNSUPPORTED",
                        "abstract methods or call-bearing field initializers are outside the profile",
                        _token_locator(path, segment[0] if segment else token),
                    )
                index = delimiter + 1
                continue
            declaration_start = 0
            while (
                declaration_start < len(segment)
                and segment[declaration_start].text in _MODIFIERS
            ):
                declaration_start += 1
            if (
                declaration_start < len(segment)
                and segment[declaration_start].text
                in {"class", "interface", "enum", "record"}
            ):
                self._fail(
                    "JAVA_NESTED_TYPE_UNSUPPORTED",
                    "nested Java types are outside the static-call profile",
                    _token_locator(path, segment[0] if segment else token),
                )
            method = self._parse_method_header(
                path,
                tokens,
                segment,
                qualified_name,
                simple_name,
                ordinal,
                delimiter,
            )
            body_close = _matching_token(tokens, delimiter, "{", "}", path)
            if body_close > class_close:
                self._fail(
                    "JAVA_METHOD_BODY_OUTSIDE_TYPE",
                    "Java method body is outside its declaring class",
                    path,
                )
            methods.append(
                _ParsedMethod(
                    declaring_type=method.declaring_type,
                    name=method.name,
                    parameter_types=method.parameter_types,
                    return_type=method.return_type,
                    visibility=method.visibility,
                    modifiers=method.modifiers,
                    source_path=method.source_path,
                    declaration_ordinal=method.declaration_ordinal,
                    header_start=method.header_start,
                    header_end=method.header_end,
                    body_token_start=delimiter + 1,
                    body_token_end=body_close,
                )
            )
            ordinal += 1
            index = body_close + 1
        return tuple(methods)

    def _parse_method_header(
        self,
        path: str,
        tokens: tuple[_Token, ...],
        segment: tuple[_Token, ...],
        qualified_name: str,
        simple_name: str,
        ordinal: int,
        body_open: int,
    ) -> _ParsedMethod:
        if not segment:
            self._fail(
                "JAVA_INITIALIZER_BLOCK_UNSUPPORTED",
                "initializer blocks are outside the Java static-call profile",
                _token_locator(path, tokens[body_open]),
            )
        if any(item.text in {"@", "<", ">", "throws"} for item in segment):
            self._fail(
                "JAVA_METHOD_HEADER_UNSUPPORTED",
                "annotated, generic, or throws-bearing methods are outside the profile",
                _token_locator(path, segment[0]),
            )
        open_positions = [
            index for index, item in enumerate(segment) if item.text == "("
        ]
        if len(open_positions) != 1:
            self._fail(
                "JAVA_MEMBER_DECLARATION_UNSUPPORTED",
                "class member is not one supported method declaration",
                _token_locator(path, segment[0]),
            )
        parameter_open = open_positions[0]
        if parameter_open == 0 or not _is_identifier(segment[parameter_open - 1]):
            self._fail(
                "JAVA_METHOD_NAME_INVALID",
                "Java method declaration has no supported method name",
                _token_locator(path, segment[0]),
            )
        parameter_close = _matching_token(
            segment, parameter_open, "(", ")", path
        )
        if parameter_close != len(segment) - 1:
            self._fail(
                "JAVA_METHOD_HEADER_UNSUPPORTED",
                "tokens after the parameter list are outside the profile",
                _token_locator(path, segment[parameter_close + 1]),
            )
        name = _identifier(segment[parameter_open - 1], path)
        if name == simple_name:
            self._fail(
                "JAVA_CONSTRUCTOR_UNSUPPORTED",
                "constructors are outside the Java static-call profile",
                _token_locator(path, segment[parameter_open - 1]),
            )
        prefix = list(segment[: parameter_open - 1])
        modifiers: list[str] = []
        while prefix and prefix[0].text in _MODIFIERS:
            modifiers.append(prefix.pop(0).text)
        if any(item in {"abstract", "native"} for item in modifiers):
            self._fail(
                "JAVA_BODYLESS_METHOD_UNSUPPORTED",
                "abstract/native methods are outside the profile",
                path,
            )
        if not prefix:
            self._fail(
                "JAVA_METHOD_RETURN_TYPE_REQUIRED",
                "Java method requires an explicit return type",
                _token_locator(path, segment[0]),
            )
        return_type = _canonical_type(tuple(prefix), path)
        visibility_values = [item for item in modifiers if item in _VISIBILITY]
        if len(visibility_values) > 1:
            self._fail(
                "JAVA_METHOD_VISIBILITY_INVALID",
                "Java method has conflicting visibility modifiers",
                path,
            )
        visibility = visibility_values[0].upper() if visibility_values else "PACKAGE"
        parameters = _split_parameters(
            segment[parameter_open + 1 : parameter_close], path
        )
        parameter_types = tuple(
            _parameter_type(parameter, path) for parameter in parameters
        )
        return _ParsedMethod(
            declaring_type=qualified_name,
            name=name,
            parameter_types=parameter_types,
            return_type=return_type,
            visibility=visibility,
            modifiers=tuple(sorted(modifiers)),
            source_path=path,
            declaration_ordinal=ordinal,
            header_start=segment[0].byte_start,
            header_end=tokens[body_open].byte_start,
            body_token_start=0,
            body_token_end=0,
        )

    def _resolve_calls(
        self,
        parsed_types: tuple[_ParsedType, ...],
        by_fqcn: Mapping[str, _ParsedType],
        by_target: Mapping[tuple[str, str, int], list[_ParsedMethod]],
    ) -> tuple[_CallSite, ...]:
        simple_types: dict[str, list[str]] = {}
        for fqcn, parsed in by_fqcn.items():
            simple_types.setdefault(parsed.simple_name, []).append(fqcn)
        result: list[_CallSite] = []
        for parsed_type in parsed_types:
            imports = dict(parsed_type.imports)
            tokens = parsed_type.tokens
            for method in parsed_type.methods:
                for open_index in range(
                    method.body_token_start, method.body_token_end
                ):
                    if tokens[open_index].text != "(":
                        continue
                    if open_index == 0:
                        continue
                    name_token = tokens[open_index - 1]
                    if not _is_identifier(name_token):
                        continue
                    name = name_token.text
                    if name in _CONTROL_PAREN:
                        continue
                    if open_index >= 2 and tokens[open_index - 2].text == "new":
                        continue
                    close_index = _matching_token(
                        tokens, open_index, "(", ")", method.source_path
                    )
                    if close_index > method.body_token_end:
                        self._fail(
                            "JAVA_CALL_OUTSIDE_METHOD",
                            "invocation delimiter escapes the method body",
                            _token_locator(method.source_path, name_token),
                        )
                    arity = _argument_arity(
                        tokens[open_index + 1 : close_index], method.source_path
                    )
                    target_type = parsed_type.qualified_name
                    evidence_start = name_token.byte_start
                    if open_index >= 2 and tokens[open_index - 2].text == ".":
                        receiver_start = _receiver_start(tokens, open_index - 2)
                        receiver_tokens = tokens[receiver_start : open_index - 2]
                        receiver = _dotted_name(receiver_tokens, method.source_path)
                        evidence_start = receiver_tokens[0].byte_start
                        if receiver == "this":
                            target_type = parsed_type.qualified_name
                        elif receiver == "super":
                            self._fail(
                                "JAVA_CALL_RECEIVER_UNSUPPORTED",
                                "super calls are outside the Java static-call profile",
                                _token_locator(method.source_path, receiver_tokens[0]),
                            )
                        else:
                            target_type = _resolve_type_receiver(
                                receiver,
                                current_package=parsed_type.package_name,
                                imports=imports,
                                by_fqcn=by_fqcn,
                                simple_types=simple_types,
                            )
                            if target_type is None:
                                self._fail(
                                    "JAVA_CALL_RECEIVER_UNSUPPORTED",
                                    f"call receiver {receiver!r} is not a unique in-scope type or this",
                                    _token_locator(method.source_path, receiver_tokens[0]),
                                )
                    candidates = by_target.get((target_type, name, arity), [])
                    if len(candidates) > 1:
                        self._fail(
                            "JAVA_CALL_TARGET_AMBIGUOUS",
                            f"call {target_type}#{name}/{arity} has multiple in-scope overload targets",
                            _token_locator(method.source_path, name_token),
                        )
                    if not candidates:
                        self._fail(
                            "JAVA_CALL_TARGET_UNRESOLVED",
                            f"call {target_type}#{name}/{arity} has no unique in-scope target",
                            _token_locator(method.source_path, name_token),
                        )
                    result.append(
                        _CallSite(
                            caller_signature=method.display_signature,
                            callee_signature=candidates[0].display_signature,
                            source_path=method.source_path,
                            byte_start=evidence_start,
                            byte_end=tokens[close_index].byte_end,
                        )
                    )
        return tuple(
            sorted(
                result,
                key=lambda item: (
                    item.caller_signature,
                    item.callee_signature,
                    item.source_path,
                    item.byte_start,
                ),
            )
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
        except UnicodeDecodeError as exc:  # offsets are produced by the lexer
            raise JavaStaticCallError(
                "JAVA_EVIDENCE_RANGE_INVALID",
                "Java Evidence range does not align to UTF-8",
                locator=path,
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

    def _relation(
        self,
        *,
        subject: EntityRecord,
        predicate: RelationPredicate,
        object_: EntityRecord,
        modality: ObservationModality,
        evidence_references: Sequence[StableId],
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
            covered_entity_types=(EntityType.JAVA_TYPE, EntityType.JAVA_METHOD),
            covered_relation_predicates=(
                RelationPredicate.DECLARES_METHOD,
                RelationPredicate.CALLS,
            ),
            canonicalization_ref=CANONICALIZATION_REF,
            canonicalization_digest=CANONICALIZATION_DIGEST,
            coverage_root_ref=COVERAGE_ROOT_REF,
        )
        state = CoverageState.create(
            root=root,
            source_revision=self.source_revision,
            knowledge_context_digest=self.knowledge_context_digest,
            complete_member_manifest=manifest,
            evidence_references=evidence_references,
        )
        return CoverageRecord(root, state)

    @staticmethod
    def _fail(reason_code: str, message: str, locator: str) -> None:
        raise JavaStaticCallError(reason_code, message, locator=locator)


def _tokenize(text: str, path: str) -> tuple[_Token, ...]:
    offsets = [0]
    for character in text:
        offsets.append(offsets[-1] + len(character.encode("utf-8")))
    tokens: list[_Token] = []
    index = 0
    length = len(text)
    while index < length:
        character = text[index]
        if character.isspace():
            index += 1
            continue
        if text.startswith("//", index):
            newline = text.find("\n", index + 2)
            index = length if newline < 0 else newline + 1
            continue
        if text.startswith("/*", index):
            end = text.find("*/", index + 2)
            if end < 0:
                raise JavaStaticCallError(
                    "JAVA_COMMENT_UNTERMINATED",
                    "Java block comment is unterminated",
                    locator=f"{path}#byte={offsets[index]}",
                )
            index = end + 2
            continue
        if text.startswith('"""', index):
            raise JavaStaticCallError(
                "JAVA_TEXT_BLOCK_UNSUPPORTED",
                "Java text blocks are outside the static-call profile",
                locator=f"{path}#byte={offsets[index]}",
            )
        if character in {'"', "'"}:
            quote = character
            start = index
            index += 1
            escaped = False
            while index < length:
                current = text[index]
                if escaped:
                    escaped = False
                elif current == "\\":
                    escaped = True
                elif current == quote:
                    index += 1
                    break
                elif current in "\r\n":
                    raise JavaStaticCallError(
                        "JAVA_LITERAL_UNTERMINATED",
                        "Java string or character literal is unterminated",
                        locator=f"{path}#byte={offsets[start]}",
                    )
                index += 1
            else:
                raise JavaStaticCallError(
                    "JAVA_LITERAL_UNTERMINATED",
                    "Java string or character literal is unterminated",
                    locator=f"{path}#byte={offsets[start]}",
                )
            tokens.append(
                _Token(
                    text=text[start:index],
                    kind="LITERAL",
                    byte_start=offsets[start],
                    byte_end=offsets[index],
                )
            )
            continue
        if character.isascii() and (character.isalpha() or character in "_$"):
            start = index
            index += 1
            while index < length and text[index].isascii() and (
                text[index].isalnum() or text[index] in "_$"
            ):
                index += 1
            value = unicodedata.normalize("NFC", text[start:index])
            tokens.append(_Token(value, "IDENT", offsets[start], offsets[index]))
            continue
        if character.isdigit():
            start = index
            index += 1
            while index < length and (
                text[index].isalnum() or text[index] in "._"
            ):
                index += 1
            tokens.append(
                _Token(text[start:index], "NUMBER", offsets[start], offsets[index])
            )
            continue
        matched = next(
            (
                symbol
                for symbol in (
                    "...",
                    "::",
                    "->",
                    ">>>",
                    ">>",
                    "<<",
                    "==",
                    "!=",
                    "<=",
                    ">=",
                    "&&",
                    "||",
                    "++",
                    "--",
                    "+=",
                    "-=",
                    "*=",
                    "/=",
                    "%=",
                )
                if text.startswith(symbol, index)
            ),
            None,
        )
        if matched is not None:
            end = index + len(matched)
            tokens.append(_Token(matched, "SYMBOL", offsets[index], offsets[end]))
            index = end
            continue
        if character.isascii() and character in "{}()[];,.=@<>:+-*/%!&|^~?":
            tokens.append(
                _Token(character, "SYMBOL", offsets[index], offsets[index + 1])
            )
            index += 1
            continue
        raise JavaStaticCallError(
            "JAVA_TOKEN_UNSUPPORTED",
            f"Java character {character!r} is outside the frozen lexer",
            locator=f"{path}#byte={offsets[index]}",
        )
    return tuple(tokens)


def _qualified_name_until(
    tokens: tuple[_Token, ...], index: int, terminator: str, path: str
) -> tuple[str, int]:
    values: list[str] = []
    expect_identifier = True
    while index < len(tokens) and tokens[index].text != terminator:
        token = tokens[index]
        if expect_identifier:
            if token.text == "*" and values:
                values.append("*")
                expect_identifier = False
            elif _is_identifier(token):
                values.append(_identifier(token, path))
                expect_identifier = False
            else:
                raise JavaStaticCallError(
                    "JAVA_QUALIFIED_NAME_INVALID",
                    "Java package/import name is malformed",
                    locator=_token_locator(path, token),
                )
        else:
            if token.text != ".":
                raise JavaStaticCallError(
                    "JAVA_QUALIFIED_NAME_INVALID",
                    "Java package/import name is malformed",
                    locator=_token_locator(path, token),
                )
            values.append(".")
            expect_identifier = True
        index += 1
    if index >= len(tokens) or not values or expect_identifier:
        raise JavaStaticCallError(
            "JAVA_QUALIFIED_NAME_INVALID",
            "Java package/import declaration is incomplete",
            locator=path,
        )
    return "".join(values), index + 1


def _next_top_level_member_delimiter(
    tokens: tuple[_Token, ...], start: int, limit: int, path: str
) -> int:
    paren = 0
    bracket = 0
    for index in range(start, limit):
        value = tokens[index].text
        if value == "(":
            paren += 1
        elif value == ")":
            paren -= 1
        elif value == "[":
            bracket += 1
        elif value == "]":
            bracket -= 1
        if paren < 0 or bracket < 0:
            raise JavaStaticCallError(
                "JAVA_DELIMITER_UNBALANCED",
                "Java member delimiter is unbalanced",
                locator=_token_locator(path, tokens[index]),
            )
        if paren == 0 and bracket == 0 and value in {";", "{"}:
            return index
    raise JavaStaticCallError(
        "JAVA_MEMBER_UNTERMINATED",
        "Java class member is unterminated",
        locator=path,
    )


def _matching_token(
    tokens: Sequence[_Token], index: int, opening: str, closing: str, path: str
) -> int:
    if index >= len(tokens) or tokens[index].text != opening:
        raise JavaStaticCallError(
            "JAVA_DELIMITER_INVALID",
            f"expected Java delimiter {opening!r}",
            locator=path,
        )
    depth = 0
    for candidate in range(index, len(tokens)):
        value = tokens[candidate].text
        if value == opening:
            depth += 1
        elif value == closing:
            depth -= 1
            if depth == 0:
                return candidate
    raise JavaStaticCallError(
        "JAVA_DELIMITER_UNBALANCED",
        f"Java delimiter {opening!r} has no matching {closing!r}",
        locator=_token_locator(path, tokens[index]),
    )


def _split_parameters(
    tokens: Sequence[_Token], path: str
) -> tuple[tuple[_Token, ...], ...]:
    if not tokens:
        return ()
    values: list[tuple[_Token, ...]] = []
    current: list[_Token] = []
    bracket = 0
    for token in tokens:
        if token.text == "[":
            bracket += 1
        elif token.text == "]":
            bracket -= 1
        if bracket < 0:
            raise JavaStaticCallError(
                "JAVA_PARAMETER_INVALID",
                "Java parameter array delimiter is unbalanced",
                locator=_token_locator(path, token),
            )
        if token.text == "," and bracket == 0:
            if not current:
                raise JavaStaticCallError(
                    "JAVA_PARAMETER_INVALID",
                    "Java parameter list contains an empty parameter",
                    locator=_token_locator(path, token),
                )
            values.append(tuple(current))
            current = []
        else:
            current.append(token)
    if bracket or not current:
        raise JavaStaticCallError(
            "JAVA_PARAMETER_INVALID",
            "Java parameter list is malformed",
            locator=path,
        )
    values.append(tuple(current))
    return tuple(values)


def _parameter_type(tokens: tuple[_Token, ...], path: str) -> str:
    values = list(tokens)
    if values and values[0].text == "final":
        values.pop(0)
    if any(item.text in {"@", "...", "<", ">"} for item in values):
        raise JavaStaticCallError(
            "JAVA_PARAMETER_UNSUPPORTED",
            "annotated, varargs, or generic parameters are outside the profile",
            locator=_token_locator(path, values[0] if values else tokens[0]),
        )
    if len(values) < 2 or not _is_identifier(values[-1]):
        raise JavaStaticCallError(
            "JAVA_PARAMETER_INVALID",
            "Java parameter must end in a supported identifier",
            locator=path,
        )
    return _canonical_type(tuple(values[:-1]), path)


def _canonical_type(tokens: tuple[_Token, ...], path: str) -> str:
    if not tokens:
        raise JavaStaticCallError(
            "JAVA_TYPE_REFERENCE_INVALID",
            "Java type reference is empty",
            locator=path,
        )
    parts: list[str] = []
    expect_identifier = True
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if expect_identifier:
            if not _is_identifier(token):
                raise JavaStaticCallError(
                    "JAVA_TYPE_REFERENCE_UNSUPPORTED",
                    "Java type reference is outside the frozen canonicalizer",
                    locator=_token_locator(path, token),
                )
            parts.append(_identifier(token, path))
            expect_identifier = False
        elif token.text == ".":
            parts.append(".")
            expect_identifier = True
        elif token.text == "[" and index + 1 < len(tokens) and tokens[index + 1].text == "]":
            parts.append("[]")
            index += 1
        else:
            raise JavaStaticCallError(
                "JAVA_TYPE_REFERENCE_UNSUPPORTED",
                "Java type reference is outside the frozen canonicalizer",
                locator=_token_locator(path, token),
            )
        index += 1
    if expect_identifier:
        raise JavaStaticCallError(
            "JAVA_TYPE_REFERENCE_INVALID",
            "Java type reference is incomplete",
            locator=path,
        )
    value = "".join(parts)
    if value == "void" or value.removesuffix("[]") in _PRIMITIVE_TYPES:
        return value
    return unicodedata.normalize("NFC", value)


def _argument_arity(tokens: Sequence[_Token], path: str) -> int:
    if not tokens:
        return 0
    depths = {"(": 0, "[": 0, "{": 0}
    pairs = {")": "(", "]": "[", "}": "{"}
    count = 1
    for token in tokens:
        if token.text in depths:
            depths[token.text] += 1
        elif token.text in pairs:
            opening = pairs[token.text]
            depths[opening] -= 1
            if depths[opening] < 0:
                raise JavaStaticCallError(
                    "JAVA_ARGUMENT_DELIMITER_INVALID",
                    "Java invocation argument delimiter is unbalanced",
                    locator=_token_locator(path, token),
                )
        elif token.text == "," and not any(depths.values()):
            count += 1
    if any(depths.values()):
        raise JavaStaticCallError(
            "JAVA_ARGUMENT_DELIMITER_INVALID",
            "Java invocation argument delimiter is unbalanced",
            locator=path,
        )
    return count


def _receiver_start(tokens: tuple[_Token, ...], dot_index: int) -> int:
    index = dot_index - 1
    if index < 0 or not _is_identifier(tokens[index]):
        return dot_index
    while index >= 2 and tokens[index - 1].text == "." and _is_identifier(tokens[index - 2]):
        index -= 2
    return index


def _dotted_name(tokens: Sequence[_Token], path: str) -> str:
    if not tokens:
        raise JavaStaticCallError(
            "JAVA_CALL_RECEIVER_UNSUPPORTED",
            "Java call receiver is not a supported name",
            locator=path,
        )
    parts: list[str] = []
    expect_identifier = True
    for token in tokens:
        if expect_identifier and _is_identifier(token):
            parts.append(_identifier(token, path))
            expect_identifier = False
        elif not expect_identifier and token.text == ".":
            parts.append(".")
            expect_identifier = True
        else:
            raise JavaStaticCallError(
                "JAVA_CALL_RECEIVER_UNSUPPORTED",
                "Java call receiver is not a supported type name or this",
                locator=_token_locator(path, token),
            )
    if expect_identifier:
        raise JavaStaticCallError(
            "JAVA_CALL_RECEIVER_UNSUPPORTED",
            "Java call receiver is incomplete",
            locator=path,
        )
    return "".join(parts)


def _resolve_type_receiver(
    receiver: str,
    *,
    current_package: str,
    imports: Mapping[str, str],
    by_fqcn: Mapping[str, _ParsedType],
    simple_types: Mapping[str, list[str]],
) -> str | None:
    if receiver in by_fqcn:
        return receiver
    local = f"{current_package}.{receiver}" if current_package else receiver
    if local in by_fqcn:
        return local
    imported = imports.get(receiver)
    if imported in by_fqcn:
        return imported
    values = simple_types.get(receiver, [])
    return values[0] if len(values) == 1 else None


def _is_identifier(token: _Token) -> bool:
    return token.kind == "IDENT" and _IDENTIFIER.fullmatch(token.text) is not None


def _identifier(token: _Token, path: str) -> str:
    if not _is_identifier(token):
        raise JavaStaticCallError(
            "JAVA_IDENTIFIER_INVALID",
            "Java identifier is outside the frozen ASCII identifier subset",
            locator=_token_locator(path, token),
        )
    return unicodedata.normalize("NFC", token.text)


def _token_locator(path: str, token: _Token) -> str:
    return f"{path}#bytes={token.byte_start}-{token.byte_end}"


def _path(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip() or "\\" in value:
        raise JavaStaticCallError(
            "JAVA_PATH_INVALID", f"{label} must be canonical", locator=str(value)
        )
    parsed = PurePosixPath(value)
    if parsed.is_absolute() or any(part in {"", ".", ".."} for part in parsed.parts):
        raise JavaStaticCallError(
            "JAVA_PATH_INVALID", f"{label} must be repository-relative", locator=value
        )
    return parsed.as_posix()


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise JavaStaticCallError(
            "JAVA_TEXT_INVALID", f"{label} must be non-empty", locator=str(value)
        )
    return unicodedata.normalize("NFC", value)


__all__ = [
    "CANONICALIZATION_DIGEST",
    "CANONICALIZATION_REF",
    "COVERAGE_ROOT_REF",
    "EVALUATION_CONTEXT_DIGEST",
    "EVALUATION_CONTEXT_REF",
    "JavaSourceEvidenceMetadata",
    "JavaStaticCallBuildReport",
    "JavaStaticCallError",
    "JavaStaticCallEvaluation",
    "JavaStaticCallEvaluator",
    "JavaStaticCallInput",
    "PROFILE_REF",
    "SCHEMA_DIGEST",
    "SCHEMA_REF",
    "evaluate_java_static_calls",
]
