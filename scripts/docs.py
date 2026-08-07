#!/usr/bin/env python3
"""Validate current documentation and generate agent-oriented indexes."""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


REPOSITORY = Path(__file__).resolve().parents[1]
DOCS = REPOSITORY / "docs"
GENERATED = DOCS / "_generated"
SCAN_ROOTS = (DOCS / "system", DOCS / "project")
PLAIN_LINK_FILES = (
    REPOSITORY / "README.md",
    REPOSITORY / "AGENTS.md",
    DOCS / "README.md",
    DOCS / "_generated" / "README.md",
    DOCS / "archive" / "README.md",
)
REQUIRED = ("id", "kind", "status", "authority", "owners", "depends_on", "code", "tests")
LIST_FIELDS = {"owners", "depends_on", "code", "tests", "derived_from"}
LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
ACTIVE_ITERATION_STATUSES = {"authorized", "in-progress"}
ACTIVE_SLICE_STATUSES = {"authorized", "in-progress"}
ACCEPTED_PROPOSAL_STATUSES = {"accepted", "authorized"}
ACCEPTED_READINESS_STATUSES = {"accepted", "authorized"}
FINAL_ITERATION_STATUSES = {"completed", "accepted"}
FINDING_CLASSIFICATIONS = {
    "local-implementation",
    "iteration-design",
    "system-contract",
    "verification",
    "roadmap",
    "invalid",
}
PENDING_VALUES = {"", "pending", "unclassified"}
PLACEHOLDER_RE = re.compile(
    r"(?:\b(?:ITER|SLICE|FINDING)-NNN\b|\bNNN\b|"
    r"<(?!https?://|mailto:)[A-Za-z][^<>\n]*>)",
    re.IGNORECASE,
)
HEX_COMMIT_RE = re.compile(r"[0-9a-f]{40}")
MANIFEST_PENDING_RE = re.compile(
    r'''(?mix)^\s*(?:-\s*)?(?:[A-Za-z_][A-Za-z0-9_-]*:\s*)?
    (?:pending|"pending"|'pending')\s*$'''
)
ACTIVE_REQUIRED_SECTIONS = {
    "iteration-index": ("Status and authorization", "Required inputs"),
    "iteration-proposal": (
        "Trigger and evidence",
        "Outcome and users",
        "Scope / non-goals",
        "Adopted system IDs",
        "Development slices and dependencies",
        "Risks and unknowns",
        "Verification and acceptance",
        "Authorization decision",
    ),
    "iteration-readiness": (
        "Reviewed exact inputs",
        "Outcome, scope and non-goals",
        "System contracts and unresolved decisions",
        "Slice, dependency and risk closure",
        "Verification readiness",
        "Authorization decision",
    ),
    "development-slice": (
        "Status and dependencies",
        "Current vs expected behavior",
        "System contracts and invariants",
        "Interfaces and affected code",
        "Compatibility, data and security boundaries",
        "Open questions and implementation risks",
        "Acceptance scenarios",
        "Findings",
    ),
}
COMPLETED_ACCEPTANCE_FIELDS = (
    "accepted_scope",
    "subject_identity",
    "baseline_commit",
    "baseline_relation",
    "production_activation",
)
COMPLETED_ACCEPTANCE_SECTIONS = (
    "Exact subject and scope",
    "Gate results and limitations",
    "Finding dispositions and System write-back",
    "Verdict",
)


@dataclass(frozen=True)
class Document:
    path: Path
    metadata: dict[str, object]
    body: str

    @property
    def relative_path(self) -> str:
        return self.path.relative_to(REPOSITORY).as_posix()

    @property
    def identifier(self) -> str:
        return str(self.metadata["id"])


def parse_inline_list(value: str) -> list[str]:
    inner = value[1:-1].strip()
    if not inner:
        return []
    return [part.strip().strip("'\"") for part in inner.split(",") if part.strip()]


def parse_document(path: Path) -> tuple[Document | None, list[str]]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, [f"{path.relative_to(REPOSITORY)}: missing front matter"]

    try:
        end = next(index for index, line in enumerate(lines[1:], 1) if line.strip() == "---")
    except StopIteration:
        return None, [f"{path.relative_to(REPOSITORY)}: unclosed front matter"]

    metadata: dict[str, object] = {}
    for number, line in enumerate(lines[1:end], 2):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            errors.append(f"{path.relative_to(REPOSITORY)}:{number}: malformed metadata")
            continue
        key, raw = line.split(":", 1)
        key = key.strip()
        raw = raw.strip()
        if not key or key in metadata:
            errors.append(f"{path.relative_to(REPOSITORY)}:{number}: invalid or duplicate key")
            continue
        if raw.startswith("[") and raw.endswith("]"):
            metadata[key] = parse_inline_list(raw)
        else:
            metadata[key] = raw.strip("'\"")

    for field in REQUIRED:
        if field not in metadata:
            errors.append(f"{path.relative_to(REPOSITORY)}: missing metadata field '{field}'")
    for field in LIST_FIELDS:
        if field in metadata and not isinstance(metadata[field], list):
            errors.append(f"{path.relative_to(REPOSITORY)}: '{field}' must be an inline list")

    body = "\n".join(lines[end + 1 :]) + "\n"
    return Document(path=path, metadata=metadata, body=body), errors


def source_paths() -> Iterable[Path]:
    for root in SCAN_ROOTS:
        for path in sorted(root.rglob("*.md")):
            relative = path.relative_to(DOCS).as_posix()
            if "/governance/templates/" in f"/{relative}":
                continue
            yield path


def load_documents() -> tuple[list[Document], list[str]]:
    documents: list[Document] = []
    errors: list[str] = []
    for path in source_paths():
        document, parse_errors = parse_document(path)
        errors.extend(parse_errors)
        if document is not None:
            documents.append(document)
    return documents, errors


def validate_markdown_links(path: Path, body: str) -> list[str]:
    errors: list[str] = []
    relative_path = path.relative_to(REPOSITORY).as_posix()
    for match in LINK_RE.finditer(body):
        target = match.group(1).strip()
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        target = target.split("#", 1)[0]
        if not target:
            continue
        if target.startswith("<") and target.endswith(">"):
            target = target[1:-1]
        resolved = (path.parent / target).resolve()
        try:
            resolved.relative_to(REPOSITORY)
        except ValueError:
            errors.append(f"{relative_path}: link escapes repository: {target}")
            continue
        if not resolved.exists():
            errors.append(f"{relative_path}: broken link: {target}")
    return errors


def validate_links(document: Document) -> list[str]:
    errors = validate_markdown_links(document.path, document.body)
    if not document.relative_path.startswith("docs/system/"):
        return errors

    for match in LINK_RE.finditer(document.body):
        target = match.group(1).strip().split("#", 1)[0]
        if not target or target.startswith(("http://", "https://", "mailto:")):
            continue
        if target.startswith("<") and target.endswith(">"):
            target = target[1:-1]
        resolved = (document.path.parent / target).resolve()
        try:
            resolved.relative_to(DOCS / "project")
        except ValueError:
            continue
        errors.append(
            f"{document.relative_path}: system document links to project document: {target}"
        )
    return errors


def is_true(value: object) -> bool:
    return str(value).strip().lower() == "true"


def is_pending(value: object) -> bool:
    return str(value).strip().lower() in PENDING_VALUES


def has_unresolved_placeholder(value: object) -> bool:
    """Return whether a current-development value still contains template input."""

    if isinstance(value, dict):
        return any(
            has_unresolved_placeholder(key) or has_unresolved_placeholder(item)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return any(has_unresolved_placeholder(item) for item in value)
    return isinstance(value, str) and PLACEHOLDER_RE.search(value) is not None


def has_pending_marker(value: object) -> bool:
    if isinstance(value, dict):
        return any(has_pending_marker(item) for item in value.values())
    if isinstance(value, list):
        return any(has_pending_marker(item) for item in value)
    return isinstance(value, str) and is_pending(value)


def empty_required_sections(document: Document, required: Iterable[str]) -> list[str]:
    required = tuple(required)
    if not required:
        return []

    sections: dict[str, list[str]] = {}
    current: str | None = None
    for line in document.body.splitlines():
        heading = re.match(r"^##\s+(.+?)\s*$", line)
        if heading:
            current = heading.group(1).rstrip("#").strip()
            sections.setdefault(current, [])
        elif current is not None:
            sections[current].append(line)

    empty: list[str] = []
    for name in required:
        content = sections.get(name)
        if content is None or not any(
            line.strip() and re.match(r"^#{1,6}\s", line) is None
            for line in content
        ):
            empty.append(name)
    return empty


def empty_active_required_sections(document: Document) -> list[str]:
    required = ACTIVE_REQUIRED_SECTIONS.get(str(document.metadata.get("kind", "")), ())
    return empty_required_sections(document, required)


def has_substantive_body(document: Document) -> bool:
    return any(
        line.strip() and re.match(r"^#{1,6}\s", line) is None
        for line in document.body.splitlines()
    )


class SafeYamlError(ValueError):
    """Raised when a manifest is outside the deliberately small safe YAML subset."""


def _parse_yaml_scalar(value: str, line_number: int) -> object:
    value = value.strip()
    if value.startswith(("!", "&", "*", "|", ">")):
        raise SafeYamlError(
            f"line {line_number}: tags, aliases, anchors, and block scalars are not allowed"
        )
    if value.startswith(("[", "{")):
        if value in {"[]", "{}"}:
            return [] if value == "[]" else {}
        raise SafeYamlError(
            f"line {line_number}: non-empty inline collections are not supported"
        )
    if value.startswith('"'):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError as error:
            raise SafeYamlError(
                f"line {line_number}: invalid double-quoted scalar"
            ) from error
        if not isinstance(parsed, str):
            raise SafeYamlError(f"line {line_number}: quoted scalar must be a string")
        return parsed
    if value.startswith("'"):
        if len(value) < 2 or not value.endswith("'"):
            raise SafeYamlError(f"line {line_number}: invalid single-quoted scalar")
        return value[1:-1].replace("''", "'")
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    if lowered in {"null", "~"}:
        return None
    if re.fullmatch(r"-?(?:0|[1-9][0-9]*)", value):
        return int(value)
    return value


def safe_load_manifest(text: str) -> dict[str, object]:
    """Load a manifest as inert data and reject duplicate keys or YAML features.

    Manifests intentionally use only mappings, scalar sequences, and empty inline
    collections. Rejecting the rest keeps this gate dependency-free and fail-closed.
    """

    root: dict[str, object] = {}
    stack: list[tuple[int, dict[str, object]]] = [(-1, root)]
    sequence_containers: set[int] = set()
    collection_indents: dict[int, int | None] = {id(root): 0}
    for line_number, raw_line in enumerate(text.splitlines(), 1):
        if "\t" in raw_line:
            raise SafeYamlError(f"line {line_number}: tabs are not allowed")
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        if re.search(r"\s+#", raw_line):
            raise SafeYamlError(f"line {line_number}: inline comments are not supported")
        indentation = len(raw_line) - len(raw_line.lstrip(" "))
        content = raw_line[indentation:].rstrip()
        while indentation <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        expected_indent = collection_indents[id(parent)]
        if expected_indent is None:
            collection_indents[id(parent)] = indentation
        elif indentation != expected_indent:
            raise SafeYamlError(f"line {line_number}: inconsistent indentation")

        if content == "-" or content.startswith("- "):
            item = content[1:].strip()
            if (
                len(stack) == 1
                or parent
                or not item
                or re.match(r"^[A-Za-z_][A-Za-z0-9_-]*:(?:\s|$)", item)
            ):
                raise SafeYamlError(
                    f"line {line_number}: only scalar sequence items are supported"
                )
            _parse_yaml_scalar(item, line_number)
            sequence_containers.add(id(parent))
            continue
        if ":" not in content:
            raise SafeYamlError(f"line {line_number}: expected a mapping entry")

        key, raw_value = content.split(":", 1)
        key = key.strip()
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_-]*", key) or key == "<<":
            raise SafeYamlError(f"line {line_number}: invalid mapping key")
        if id(parent) in sequence_containers:
            raise SafeYamlError(f"line {line_number}: mixed mapping and sequence")
        if key in parent:
            raise SafeYamlError(f"line {line_number}: duplicate key '{key}'")

        raw_value = raw_value.strip()
        if raw_value:
            parent[key] = _parse_yaml_scalar(raw_value, line_number)
        else:
            child: dict[str, object] = {}
            parent[key] = child
            collection_indents[id(child)] = None
            stack.append((indentation, child))

    if not root:
        raise SafeYamlError("manifest is empty")
    return root


def _path_label(path: Path) -> str:
    try:
        return path.relative_to(REPOSITORY).as_posix()
    except ValueError:
        return path.as_posix()


def validate_active_manifest(path: Path, iteration: str) -> list[str]:
    label = _path_label(path)
    try:
        manifest_text = path.read_text(encoding="utf-8")
        manifest = safe_load_manifest(manifest_text)
    except (OSError, UnicodeError, SafeYamlError) as error:
        return [f"{label}: invalid safe YAML: {error}"]

    errors: list[str] = []
    iteration_data = manifest.get("iteration")
    if not isinstance(iteration_data, dict):
        errors.append(f"{label}: iteration must be a mapping")
    else:
        manifest_iteration = iteration_data.get("id")
        if not isinstance(manifest_iteration, str) or manifest_iteration != iteration:
            errors.append(f"{label}: iteration.id must equal active iteration {iteration}")
        manifest_status = iteration_data.get("status")
        if (
            not isinstance(manifest_status, str)
            or manifest_status not in ACTIVE_ITERATION_STATUSES
        ):
            errors.append(
                f"{label}: iteration.status must be authorized or in-progress"
            )

    baseline = manifest.get("baseline")
    if not isinstance(baseline, dict):
        errors.append(f"{label}: baseline must be a mapping")
    else:
        commit = baseline.get("commit")
        if not isinstance(commit, str) or HEX_COMMIT_RE.fullmatch(commit) is None:
            errors.append(
                f"{label}: baseline.commit must be an exact 40-character lowercase Git commit"
            )

    if (
        has_unresolved_placeholder(manifest_text)
        or has_pending_marker(manifest)
        or MANIFEST_PENDING_RE.search(manifest_text)
    ):
        errors.append(f"{label}: contains unresolved template placeholders")
    return errors


def validate_dependency_cycles(by_id: dict[str, Document]) -> list[str]:
    errors: list[str] = []
    state: dict[str, int] = {}
    stack: list[str] = []

    def visit(identifier: str) -> None:
        mark = state.get(identifier, 0)
        if mark == 2:
            return
        if mark == 1:
            start = stack.index(identifier)
            errors.append("dependency cycle: " + " -> ".join(stack[start:] + [identifier]))
            return
        state[identifier] = 1
        stack.append(identifier)
        dependencies = by_id[identifier].metadata.get("depends_on", [])
        if isinstance(dependencies, list):
            for dependency in dependencies:
                if dependency in by_id:
                    visit(dependency)
        stack.pop()
        state[identifier] = 2

    for identifier in sorted(by_id):
        visit(identifier)
    return errors


def _validate_finding_target(
    document: Document,
    classification: str,
    target: str,
    by_id: dict[str, Document],
) -> list[str]:
    errors: list[str] = []
    label = document.relative_path
    target_document = by_id.get(target)

    if classification == "local-implementation":
        references: list[str] = []
        for field in ("code", "tests"):
            value = document.metadata.get(field, [])
            if isinstance(value, list):
                references.extend(str(item) for item in value)
        if target not in references:
            errors.append(
                f"{label}: local-implementation target must be one code/tests reference"
            )
        else:
            resolved = (REPOSITORY / target).resolve()
            try:
                resolved.relative_to(REPOSITORY)
            except ValueError:
                errors.append(f"{label}: local-implementation target escapes repository")
            else:
                if not resolved.exists():
                    errors.append(
                        f"{label}: local-implementation target does not exist: {target}"
                    )
        return errors

    if target_document is None:
        return [f"{label}: finding target is not an existing document ID: {target}"]

    target_kind = str(target_document.metadata.get("kind", ""))
    target_iteration = str(target_document.metadata.get("iteration", ""))
    finding_iteration = str(document.metadata.get("iteration", ""))
    if classification == "iteration-design":
        if target_kind not in {"development-slice", "project-decision"}:
            errors.append(
                f"{label}: iteration-design target must be a development-slice or project-decision"
            )
        elif target_iteration != finding_iteration:
            errors.append(f"{label}: iteration-design target belongs to another iteration")
    elif classification == "system-contract":
        if (
            not target_document.relative_path.startswith("docs/system/")
            or target_kind.endswith("-index")
        ):
            errors.append(
                f"{label}: system-contract target must be a non-index System document"
            )
    elif classification == "verification":
        is_system_quality = (
            target_document.relative_path.startswith("docs/system/")
            and target_kind == "system-quality"
        )
        is_iteration_verification = (
            target_kind == "iteration-verification"
            and target_iteration == finding_iteration
        )
        if not (is_system_quality or is_iteration_verification):
            errors.append(
                f"{label}: verification target must be System Quality or this "
                "iteration's Verification Matrix"
            )
    elif classification == "roadmap":
        if target_kind != "roadmap-candidate":
            errors.append(f"{label}: roadmap target must be a roadmap-candidate")
    return errors


def validate_findings(
    documents: list[Document],
    by_id: dict[str, Document],
    iteration_indexes: dict[str, Document],
) -> list[str]:
    errors: list[str] = []
    allowed_classifications = FINDING_CLASSIFICATIONS | {"unclassified"}

    for document in documents:
        if document.metadata.get("kind") != "implementation-finding":
            continue
        label = document.relative_path
        status = str(document.metadata.get("status", ""))
        iteration = document.metadata.get("iteration", "")
        classification = document.metadata.get("classification", "")
        disposition = document.metadata.get("disposition", "")
        target = document.metadata.get("target", "")

        if not isinstance(iteration, str) or not iteration:
            errors.append(f"{label}: finding is missing iteration")
            iteration = ""
        elif iteration not in iteration_indexes:
            errors.append(f"{label}: finding references unknown iteration: {iteration}")

        if status not in {"open", "dispositioned", "rejected", "superseded"}:
            errors.append(f"{label}: invalid finding status: {status}")
        if not isinstance(classification, str) or classification not in allowed_classifications:
            errors.append(f"{label}: invalid finding classification: {classification}")
        if classification == "invalid" and status != "rejected":
            errors.append(f"{label}: invalid classification requires rejected status")
        if classification == "unclassified" and status != "open":
            errors.append(f"{label}: closed finding must be classified")
        if not isinstance(disposition, str):
            errors.append(f"{label}: disposition must be a single scalar")
        if not isinstance(target, str):
            errors.append(f"{label}: target must be a single scalar")

        if status == "dispositioned":
            if classification not in FINDING_CLASSIFICATIONS - {"invalid"}:
                errors.append(f"{label}: dispositioned finding has invalid classification")
            if not isinstance(disposition, str) or is_pending(disposition):
                errors.append(f"{label}: dispositioned finding has pending disposition")
            if not isinstance(target, str) or is_pending(target):
                errors.append(f"{label}: dispositioned finding has pending target")
            elif isinstance(classification, str):
                errors.extend(
                    _validate_finding_target(document, classification, target, by_id)
                )
        elif status == "open":
            if (
                isinstance(target, str)
                and not is_pending(target)
                and classification in FINDING_CLASSIFICATIONS - {"invalid"}
            ):
                errors.extend(
                    _validate_finding_target(document, classification, target, by_id)
                )
        elif status == "rejected":
            if classification != "invalid":
                errors.append(f"{label}: rejected finding classification must be invalid")
            if not isinstance(disposition, str) or is_pending(disposition):
                errors.append(f"{label}: rejected finding has pending disposition")
            if not isinstance(target, str) or target.strip().lower() != "none":
                errors.append(f"{label}: rejected finding target must be the scalar none")
        elif status == "superseded":
            superseded_by = document.metadata.get("superseded_by", "")
            if not isinstance(superseded_by, str):
                errors.append(f"{label}: superseded_by must be a single scalar")
            elif is_pending(superseded_by):
                errors.append(f"{label}: superseded finding is missing superseded_by")
            elif superseded_by == document.identifier:
                errors.append(f"{label}: superseded_by cannot reference the finding itself")
            else:
                replacement = by_id.get(superseded_by)
                if (
                    replacement is None
                    or replacement.metadata.get("kind") != "implementation-finding"
                ):
                    errors.append(
                        f"{label}: superseded_by must reference an existing Finding"
                    )
                elif replacement.metadata.get("iteration") != iteration:
                    errors.append(
                        f"{label}: superseded_by must reference a Finding in the same iteration"
                    )
    return errors


def validate_completed_acceptance(document: Document) -> list[str]:
    errors: list[str] = []
    for field in ("id", "iteration", *COMPLETED_ACCEPTANCE_FIELDS):
        value = document.metadata.get(field)
        if (
            not isinstance(value, str)
            or is_pending(value)
            or has_unresolved_placeholder(value)
        ):
            errors.append(
                f"{document.relative_path}: completed acceptance field '{field}' "
                "is pending or a placeholder"
            )
    baseline_commit = document.metadata.get("baseline_commit")
    if (
        isinstance(baseline_commit, str)
        and not is_pending(baseline_commit)
        and HEX_COMMIT_RE.fullmatch(baseline_commit) is None
    ):
        errors.append(
            f"{document.relative_path}: completed acceptance baseline_commit must "
            "be an exact 40-character lowercase Git commit"
        )
    for section in empty_required_sections(document, COMPLETED_ACCEPTANCE_SECTIONS):
        errors.append(
            f"{document.relative_path}: completed acceptance section is missing or empty: {section}"
        )
    return errors


def validate(documents: list[Document]) -> list[str]:
    errors: list[str] = []
    by_id: dict[str, Document] = {}

    for document in documents:
        identifier = document.identifier
        if not identifier:
            errors.append(f"{document.relative_path}: empty id")
        elif identifier in by_id:
            errors.append(
                f"duplicate id {identifier}: {by_id[identifier].relative_path}, {document.relative_path}"
            )
        else:
            by_id[identifier] = document

    for document in documents:
        dependencies = document.metadata.get("depends_on", [])
        if isinstance(dependencies, list):
            for dependency in dependencies:
                if dependency not in by_id:
                    errors.append(f"{document.relative_path}: unknown dependency id: {dependency}")
                if dependency == document.identifier:
                    errors.append(f"{document.relative_path}: self dependency: {dependency}")
                if (
                    document.relative_path.startswith("docs/system/")
                    and dependency in by_id
                    and not by_id[dependency].relative_path.startswith("docs/system/")
                ):
                    errors.append(
                        f"{document.relative_path}: system document depends on project document: {dependency}"
                    )

        for field in ("code", "tests"):
            references = document.metadata.get(field, [])
            if not isinstance(references, list):
                continue
            for reference in references:
                if not (REPOSITORY / reference).exists():
                    errors.append(f"{document.relative_path}: missing {field} reference: {reference}")

        relative = document.path.relative_to(DOCS).as_posix()
        if relative.startswith("system/") and document.metadata.get("authority") not in {
            "normative",
            "operational",
        }:
            errors.append(
                f"{document.relative_path}: system authority must be normative or operational"
            )
        if relative.startswith("project/roadmap/"):
            if document.metadata.get("authority") != "planning-only":
                errors.append(f"{document.relative_path}: roadmap authority must be planning-only")
            if str(document.metadata.get("coding_input", "")).lower() != "false":
                errors.append(f"{document.relative_path}: roadmap coding_input must be false")

        errors.extend(validate_links(document))

    for path in PLAIN_LINK_FILES:
        if not path.exists():
            errors.append(f"missing navigation document: {path.relative_to(REPOSITORY)}")
        else:
            errors.extend(validate_markdown_links(path, path.read_text(encoding="utf-8")))

    open_findings: dict[str, list[str]] = {}
    accepted_iterations: set[str] = set()
    iteration_indexes: dict[str, Document] = {}
    acceptance_by_iteration: dict[str, list[Document]] = {}
    for document in documents:
        kind = document.metadata.get("kind")
        status = str(document.metadata.get("status", ""))
        iteration = str(document.metadata.get("iteration", ""))
        if kind == "iteration-index" and iteration:
            if iteration in iteration_indexes:
                errors.append(
                    f"{document.relative_path}: duplicate iteration index for {iteration}"
                )
            else:
                iteration_indexes[iteration] = document
        if kind == "implementation-finding" and status == "open":
            open_findings.setdefault(iteration, []).append(document.identifier)
        if kind == "iteration-acceptance" and status in {"accepted", "completed"}:
            accepted_iterations.add(iteration)
            errors.extend(validate_completed_acceptance(document))
        if kind == "iteration-acceptance" and iteration:
            acceptance_by_iteration.setdefault(iteration, []).append(document)

    errors.extend(validate_findings(documents, by_id, iteration_indexes))

    for iteration in sorted(accepted_iterations):
        if open_findings.get(iteration):
            errors.append(
                f"{iteration}: accepted/completed with open findings: "
                + ", ".join(sorted(open_findings[iteration]))
            )

    for iteration, index in sorted(iteration_indexes.items()):
        if str(index.metadata.get("status", "")) not in FINAL_ITERATION_STATUSES:
            continue
        accepted = [
            document
            for document in acceptance_by_iteration.get(iteration, [])
            if str(document.metadata.get("status", "")) in FINAL_ITERATION_STATUSES
        ]
        if not accepted:
            errors.append(
                f"{index.relative_path}: completed iteration has no accepted/completed acceptance"
            )

    current = by_id.get("PROJECT-CURRENT")
    if current is None:
        errors.append("missing PROJECT-CURRENT document")
    else:
        active_iteration = str(current.metadata.get("active_iteration", ""))
        active_slice = str(current.metadata.get("active_slice", ""))
        if active_iteration == "none" and active_slice != "none":
            errors.append("PROJECT-CURRENT: active_slice must be none when active_iteration is none")
        if active_iteration != "none":
            current_dependencies = current.metadata.get("depends_on", [])
            if isinstance(current_dependencies, list):
                if active_iteration not in current_dependencies:
                    errors.append("PROJECT-CURRENT: active iteration must be in depends_on")
                if active_slice not in current_dependencies:
                    errors.append("PROJECT-CURRENT: active slice must be in depends_on")
            iteration_document = by_id.get(active_iteration)
            if iteration_document is None or iteration_document.metadata.get("kind") != "iteration-index":
                errors.append(
                    "PROJECT-CURRENT: active_iteration must be an existing iteration-index ID"
                )
            slice_document = by_id.get(active_slice)
            if slice_document is None or slice_document.metadata.get("kind") != "development-slice":
                errors.append(
                    "PROJECT-CURRENT: active_slice must be an existing development-slice ID"
                )
            if iteration_document is not None and iteration_document.metadata.get("kind") == "iteration-index":
                iteration = str(iteration_document.metadata.get("iteration", ""))
                if not iteration:
                    errors.append("PROJECT-CURRENT: active iteration index is missing iteration")
                if str(iteration_document.metadata.get("status", "")) not in ACTIVE_ITERATION_STATUSES:
                    errors.append("PROJECT-CURRENT: active iteration is not authorized/in-progress")
                if not is_true(iteration_document.metadata.get("coding_input", "")):
                    errors.append("PROJECT-CURRENT: active iteration coding_input must be true")

                if slice_document is not None and slice_document.metadata.get("kind") == "development-slice":
                    if str(slice_document.metadata.get("iteration", "")) != iteration:
                        errors.append("PROJECT-CURRENT: active slice belongs to another iteration")
                    if str(slice_document.metadata.get("status", "")) not in ACTIVE_SLICE_STATUSES:
                        errors.append("PROJECT-CURRENT: active slice is not authorized/in-progress")
                    if slice_document.metadata.get("authority") != "current-development":
                        errors.append("PROJECT-CURRENT: active slice authority must be current-development")
                    if not is_true(slice_document.metadata.get("coding_input", "")):
                        errors.append("PROJECT-CURRENT: active slice coding_input must be true")

                iteration_directory = iteration_document.path.parent
                required_paths = {
                    Path("proposal.md"): "iteration-proposal",
                    Path("verification-matrix.md"): "iteration-verification",
                    Path("readiness-review.md"): "iteration-readiness",
                    Path("development-design/README.md"): "development-design-index",
                    Path("findings/README.md"): "iteration-findings-index",
                }
                documents_by_path = {document.path: document for document in documents}
                active_required_documents: list[Document] = [iteration_document]
                if (
                    slice_document is not None
                    and slice_document.metadata.get("kind") == "development-slice"
                ):
                    active_required_documents.append(slice_document)
                for relative_path, expected_kind in required_paths.items():
                    required_path = iteration_directory / relative_path
                    required_document = documents_by_path.get(required_path)
                    if required_document is None:
                        errors.append(
                            f"PROJECT-CURRENT: active iteration is missing {required_path.relative_to(REPOSITORY)}"
                        )
                        continue
                    if required_document.metadata.get("kind") != expected_kind:
                        errors.append(
                            f"{required_document.relative_path}: expected kind {expected_kind}"
                        )
                    if str(required_document.metadata.get("iteration", "")) != iteration:
                        errors.append(
                            f"{required_document.relative_path}: iteration does not match active iteration"
                        )
                    active_required_documents.append(required_document)

                for required_document in {
                    document.path: document for document in active_required_documents
                }.values():
                    if not has_substantive_body(required_document):
                        errors.append(
                            f"{required_document.relative_path}: active required "
                            "document has no substantive body"
                        )
                    if (
                        has_unresolved_placeholder(required_document.metadata)
                        or has_pending_marker(required_document.metadata)
                        or has_unresolved_placeholder(required_document.body)
                    ):
                        errors.append(
                            f"{required_document.relative_path}: active required "
                            "document contains unresolved template placeholders"
                        )
                    for section in empty_active_required_sections(required_document):
                        errors.append(
                            f"{required_document.relative_path}: active required "
                            f"section is missing or empty: {section}"
                        )

                proposal = documents_by_path.get(iteration_directory / "proposal.md")
                if proposal is not None and str(proposal.metadata.get("status", "")) not in ACCEPTED_PROPOSAL_STATUSES:
                    errors.append("PROJECT-CURRENT: active iteration proposal is not accepted")

                readiness = documents_by_path.get(iteration_directory / "readiness-review.md")
                if readiness is not None:
                    if str(readiness.metadata.get("status", "")) not in ACCEPTED_READINESS_STATUSES:
                        errors.append("PROJECT-CURRENT: active iteration readiness is not accepted")
                    if is_pending(readiness.metadata.get("authorized_by", "")):
                        errors.append("PROJECT-CURRENT: readiness authorized_by is pending")
                    if is_pending(readiness.metadata.get("authorized_at", "")):
                        errors.append("PROJECT-CURRENT: readiness authorized_at is pending")

                manifest = iteration_directory / "manifest.yaml"
                if not manifest.exists():
                    errors.append(
                        f"PROJECT-CURRENT: active iteration is missing {manifest.relative_to(REPOSITORY)}"
                    )
                else:
                    errors.extend(validate_active_manifest(manifest, iteration))

    errors.extend(validate_dependency_cycles(by_id))
    return sorted(set(errors))


def render_outputs(documents: list[Document]) -> dict[Path, str]:
    ordered = sorted(documents, key=lambda document: document.identifier)
    catalog = [
        {
            "id": document.identifier,
            "kind": document.metadata["kind"],
            "status": document.metadata["status"],
            "authority": document.metadata["authority"],
            "owners": document.metadata["owners"],
            "derived_from": document.metadata.get("derived_from", []),
            "path": document.relative_path,
        }
        for document in ordered
    ]
    dependencies = {
        document.identifier: document.metadata["depends_on"] for document in ordered
    }
    traceability = {
        document.identifier: {
            "path": document.relative_path,
            "code": document.metadata["code"],
            "tests": document.metadata["tests"],
        }
        for document in ordered
        if document.metadata["code"] or document.metadata["tests"]
    }

    current = next((doc for doc in ordered if doc.identifier == "PROJECT-CURRENT"), None)
    active_iteration = "unknown" if current is None else current.metadata.get("active_iteration", "unknown")
    active_slice = "unknown" if current is None else current.metadata.get("active_slice", "unknown")
    worktree_status = "unknown" if current is None else current.metadata.get("worktree_status", "unknown")
    strategy_relation = "unknown" if current is None else current.metadata.get("strategy_relation", "unknown")
    live_model_path = "unknown" if current is None else current.metadata.get("live_model_path", "unknown")
    context_lines = [
        "# Generated current context",
        "",
        "> Derived from current document front matter. Do not edit manually or treat as normative.",
        "",
        f"- Active iteration: `{active_iteration}`",
        f"- Active slice: `{active_slice}`",
        f"- Worktree status: `{worktree_status}`",
        f"- Strategy relation: `{strategy_relation}`",
        f"- Live model path: `{live_model_path}`",
        "- Normative source: `docs/system/`",
        "- Current development source: `docs/project/current.md`",
        "- Roadmap authority: planning-only",
        "- Archive authority: historical",
        "",
        "## Agent reading route",
        "",
        "1. Read `docs/project/current.md` and stop if it does not authorize development.",
        "2. If active, read only the named Iteration and Development Slice inputs.",
        "3. Follow their exact System IDs; use `catalog.json` to resolve paths.",
        "4. Record implementation discoveries under the active Iteration before changing System truth.",
        "",
        "## Stable entry points",
        "",
    ]
    by_identifier = {document.identifier: document for document in ordered}
    entry_ids = (
        "PROJECT-CURRENT",
        "SYS-PRODUCT-VISION",
        "SYS-ARCH-INVARIANTS",
        "SYS-CONTRACT-INDEX",
        "SYS-QUALITY-INDEX",
        "PROJECT-GOVERNANCE-ITERATION-LIFECYCLE",
        "PROJECT-GOVERNANCE-IMPLEMENTATION-FEEDBACK",
    )
    for identifier in entry_ids:
        document = by_identifier.get(identifier)
        if document is not None:
            context_lines.append(
                f"- `{document.identifier}` — `{document.metadata['authority']}` — `{document.relative_path}`"
            )
    context_lines.extend(
        [
            "",
            "The complete document catalog, dependency graph, and code/test traceability are in the adjacent JSON files.",
            "",
        ]
    )

    return {
        GENERATED / "catalog.json": json.dumps(catalog, ensure_ascii=False, indent=2) + "\n",
        GENERATED / "dependency-graph.json": json.dumps(dependencies, ensure_ascii=False, indent=2) + "\n",
        GENERATED / "traceability.json": json.dumps(traceability, ensure_ascii=False, indent=2) + "\n",
        GENERATED / "current-context.md": "\n".join(context_lines),
    }


def generate(outputs: dict[Path, str]) -> None:
    GENERATED.mkdir(parents=True, exist_ok=True)
    for path, content in outputs.items():
        path.write_text(content, encoding="utf-8")


def check_generated(outputs: dict[Path, str]) -> list[str]:
    errors: list[str] = []
    for path, expected in outputs.items():
        if not path.exists():
            errors.append(f"missing generated file: {path.relative_to(REPOSITORY)}")
        elif path.read_text(encoding="utf-8") != expected:
            errors.append(f"stale generated file: {path.relative_to(REPOSITORY)}")
    return errors


def main(argv: list[str]) -> int:
    command = argv[1] if len(argv) > 1 else "check"
    if command not in {"check", "generate"}:
        print("usage: python3 scripts/docs.py [check|generate]", file=sys.stderr)
        return 2

    documents, errors = load_documents()
    errors.extend(validate(documents))
    if errors:
        for error in sorted(set(errors)):
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    outputs = render_outputs(documents)
    if command == "generate":
        generate(outputs)
        print(f"generated {len(outputs)} files from {len(documents)} current documents")
        return 0

    errors = check_generated(outputs)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print("run: python3 scripts/docs.py generate", file=sys.stderr)
        return 1
    print(f"documentation check passed: {len(documents)} current documents")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
