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
LIST_FIELDS = {
    "owners",
    "depends_on",
    "code",
    "tests",
    "derived_from",
    "product_goal_accepted_capability_refs",
    "product_goal_cross_domain_case_ids",
    "product_goal_slice_gate_case_ids",
}
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
PRODUCT_GOAL_ALIGNMENT_START_ITERATION = 7
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
PRODUCT_GOAL_ALIGNMENT_SECTIONS = {
    "iteration-proposal": ("Product-goal alignment and cumulative delta",),
    "iteration-readiness": ("Product-goal alignment gate",),
    "development-slice": (
        "Product-goal contribution and cumulative integration",
    ),
}
PRODUCT_GOAL_ALIGNMENT_MANIFEST_SCALARS = (
    "baseline_gap",
    "held_out_free_question_delta",
    "held_out_evaluation_owner",
    "implementation_question_visibility",
    "first_product_web_checkpoint",
    "live_ad_hoc_question_checkpoint",
)
PRODUCT_GOAL_ALIGNMENT_MANIFEST_SEQUENCES = (
    "accepted_capability_refs",
    "new_capability_slice_refs",
    "cross_domain_cases",
    "blocking_case_ids",
    "stop_or_redirect_conditions",
)
PRODUCT_GOAL_ALIGNMENT_MANIFEST_COUNTS = (
    "held_out_question_count",
    "held_out_answerable_question_count",
    "held_out_boundary_question_count",
    "held_out_answerable_without_symbol_count_minimum",
    "held_out_answerable_without_symbol_per_project_minimum",
    "held_out_baseline_supported_count",
    "held_out_target_supported_count",
    "cross_domain_case_count",
    "live_ad_hoc_question_count",
    "live_ad_hoc_without_symbol_count_minimum",
)
PRODUCT_GOAL_ALIGNMENT_MANIFEST_DIGESTS = (
    "evaluation_project_manifest_digest",
    "held_out_suite_digest",
    "baseline_result_digest",
    "mature_source_agent_protocol_digest",
    "authorized_software_sources_digest",
)
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
PRODUCT_GOAL_ALIGNMENT_ACCEPTANCE_SECTIONS = (
    "Product-goal delta and cumulative evidence",
)
PRODUCT_GOAL_ACCEPTANCE_PLACEHOLDERS = (
    "<exact-measures-and-evidence>",
    "<exact-cases-and-evidence>",
    "<exact-evidence>",
)
GOAL_ALIGNED_PROPOSAL_STATUSES = {"accepted", "authorized", "completed"}
GOAL_ALIGNED_READINESS_STATUSES = {"accepted", "authorized", "completed"}
GOAL_ALIGNED_ITERATION_STATUSES = {
    "authorized",
    "in-progress",
    "accepted",
    "completed",
}
GOAL_ALIGNED_SLICE_STATUSES = {
    "authorized",
    "in-progress",
    "completed",
}
PRODUCT_GOAL_V000_CLAIM = (
    "本轮相对 baseline 可测缩短通用源码问答 MVP 差距，并与既有能力完成跨域组合"
)
PRODUCT_GOAL_V000_LEVEL = "product / comparison"
PRODUCT_GOAL_V000_FROZEN_INPUT = (
    "未参与实现的真实工程；独立评测方/用户持有且实现阶段不可见的 held-out 自由问题；"
    "验收现场临时问题；旧+新知识跨域问题；成熟源码 Agent protocol"
)
PRODUCT_GOAL_V000_EXPECTED = (
    "支持率提高；重大错误为 0；逐题完整性不退步；提问时 "
    "Source/Update/Direct fallback=0；同一正式 Web 可人工验证"
)
PRODUCT_GOAL_V000_METADATA = {
    "product_goal_gate": "V-000",
    "product_goal_outcome": "user-visible-general-source-qa-delta",
    "product_goal_evaluation": "independent-hidden-plus-live-ad-hoc",
}
PRODUCT_GOAL_RESULT_DIGEST_FIELDS = (
    "evaluation_project_manifest_digest",
    "held_out_suite_digest",
    "baseline_result_digest",
    "mature_source_agent_protocol_digest",
    "authorized_software_sources_digest",
)
PRODUCT_GOAL_RESULT_COUNT_FIELDS = (
    "held_out_question_count",
    "held_out_baseline_supported_count",
    "held_out_actual_supported_count",
    "held_out_boundary_correct_gap_count",
    "held_out_answerable_without_symbol_supported_count",
    "live_ad_hoc_without_symbol_pass_count",
    "major_error_count",
    "source_fallback_count",
    "update_fallback_count",
    "direct_fallback_count",
    "cross_domain_pass_count",
    "live_ad_hoc_pass_count",
)
PRODUCT_GOAL_RESULT_REQUIRED_SECTIONS = (
    "Claim and scope",
    "Exact inputs / baseline",
    "Execution and evidence",
    "Result, failures and limitations",
    "Findings and system write-back",
    "Validity / supersession",
)
ABSENT_EVIDENCE_VALUES = {
    "none",
    "n/a",
    "na",
    "not-applicable",
    "no-change",
    "no-evidence",
    "unknown",
    "tbd",
}


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


def is_absent_evidence(value: object) -> bool:
    return str(value).strip().lower() in ABSENT_EVIDENCE_VALUES


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


def markdown_section_body(document: Document, name: str) -> str | None:
    lines: list[str] = []
    active = False
    for line in document.body.splitlines():
        heading = re.match(r"^##\s+(.+?)\s*$", line)
        if heading:
            heading_name = heading.group(1).rstrip("#").strip()
            if active:
                break
            active = heading_name == name
            continue
        if active:
            lines.append(line)
    return "\n".join(lines) if active else None


def iteration_number(identifier: object) -> int | None:
    match = re.fullmatch(r"ITER-([0-9]{3,})", str(identifier).strip())
    return int(match.group(1)) if match else None


def iteration_from_document_path(path: Path) -> str | None:
    try:
        relative = path.relative_to(REPOSITORY).as_posix()
    except ValueError:
        return None
    match = re.match(
        r"^docs/project/iterations/iteration-([0-9]{3,})(?:/|$)", relative
    )
    return None if match is None else f"ITER-{match.group(1)}"


def validate_iteration_document_identity(document: Document) -> list[str]:
    try:
        relative = document.path.relative_to(REPOSITORY).as_posix()
    except ValueError:
        return []
    directory_match = re.match(
        r"^docs/project/iterations/iteration-([^/]+)(?:/|$)", relative
    )
    if directory_match is not None and re.fullmatch(
        r"[0-9]{3,}", directory_match.group(1)
    ) is None:
        return [
            f"{document.relative_path}: iteration directory must use at least three digits"
        ]

    expected = iteration_from_document_path(document.path)
    if expected is None:
        return []

    errors: list[str] = []
    actual = str(document.metadata.get("iteration", ""))
    if actual != expected:
        errors.append(
            f"{document.relative_path}: iteration must match directory {expected}"
        )
    if (
        document.metadata.get("kind") == "iteration-index"
        and document.identifier != f"{expected}-INDEX"
    ):
        errors.append(
            f"{document.relative_path}: iteration-index id must equal {expected}-INDEX"
        )
    return errors


def requires_product_goal_alignment(identifier: object) -> bool:
    number = iteration_number(identifier)
    return number is not None and number >= PRODUCT_GOAL_ALIGNMENT_START_ITERATION


def active_required_sections(document: Document) -> tuple[str, ...]:
    kind = str(document.metadata.get("kind", ""))
    required = ACTIVE_REQUIRED_SECTIONS.get(kind, ())
    if requires_product_goal_alignment(document.metadata.get("iteration", "")):
        required += PRODUCT_GOAL_ALIGNMENT_SECTIONS.get(kind, ())
    return required


def empty_active_required_sections(document: Document) -> list[str]:
    required = active_required_sections(document)
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


def manifest_resolved_sequence_items(
    text: str, section: str, field: str
) -> list[str] | None:
    """Return a direct safe-YAML scalar sequence, or None when invalid/empty."""

    lines = text.splitlines()
    section_index: int | None = None
    for index, raw_line in enumerate(lines):
        if re.fullmatch(rf"{re.escape(section)}\s*:\s*", raw_line):
            section_index = index
            break
    if section_index is None:
        return None

    direct_indent: int | None = None
    field_index: int | None = None
    field_indent: int | None = None
    for index in range(section_index + 1, len(lines)):
        raw_line = lines[index]
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        indentation = len(raw_line) - len(raw_line.lstrip(" "))
        if indentation == 0:
            break
        if direct_indent is None:
            direct_indent = indentation
        if indentation != direct_indent:
            continue
        match = re.fullmatch(
            rf"{re.escape(field)}\s*:\s*(.*)", raw_line.strip()
        )
        if match is None:
            continue
        if match.group(1):
            return None
        field_index = index
        field_indent = indentation
        break
    if field_index is None or field_indent is None:
        return None

    item_indent: int | None = None
    items: list[str] = []
    for raw_line in lines[field_index + 1 :]:
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        indentation = len(raw_line) - len(raw_line.lstrip(" "))
        if indentation <= field_indent:
            break
        content = raw_line.strip()
        if item_indent is None:
            item_indent = indentation
        if indentation != item_indent or not content.startswith("- "):
            return None
        raw_value = content[2:].strip()
        try:
            value = _parse_yaml_scalar(raw_value, 0)
        except SafeYamlError:
            return None
        if (
            not isinstance(value, str)
            or is_pending(value)
            or is_absent_evidence(value)
            or has_unresolved_placeholder(value)
        ):
            return None
        items.append(value)
    return items or None


def validate_product_goal_structured_bindings(
    alignment: dict[str, object],
    sequences: dict[str, list[str]],
    label: str,
) -> list[str]:
    errors: list[str] = []
    accepted_refs = sequences.get("accepted_capability_refs", [])
    new_refs = sequences.get("new_capability_slice_refs", [])
    cross_cases = sequences.get("cross_domain_cases", [])

    bindings = alignment.get("cross_domain_bindings")
    bound_cases: dict[str, tuple[str, str]] = {}
    if not isinstance(bindings, dict) or not bindings:
        errors.append(f"{label}: cross_domain_bindings must be a non-empty mapping")
    else:
        for binding_name, binding in bindings.items():
            if not isinstance(binding, dict):
                errors.append(
                    f"{label}: cross_domain_bindings.{binding_name} must be a mapping"
                )
                continue
            case_id = binding.get("case_id")
            accepted_ref = binding.get("accepted_capability_ref")
            new_ref = binding.get("new_slice_ref")
            if not isinstance(case_id, str) or case_id not in cross_cases:
                errors.append(
                    f"{label}: cross_domain_bindings.{binding_name}.case_id must reference cross_domain_cases"
                )
                continue
            if case_id in bound_cases:
                errors.append(
                    f"{label}: cross-domain case must have exactly one structured binding: {case_id}"
                )
            if not isinstance(accepted_ref, str) or accepted_ref not in accepted_refs:
                errors.append(
                    f"{label}: cross_domain_bindings.{binding_name}.accepted_capability_ref must reference accepted_capability_refs"
                )
            if not isinstance(new_ref, str) or new_ref not in new_refs:
                errors.append(
                    f"{label}: cross_domain_bindings.{binding_name}.new_slice_ref must reference new_capability_slice_refs"
                )
            if (
                isinstance(accepted_ref, str)
                and accepted_ref in accepted_refs
                and isinstance(new_ref, str)
                and new_ref in new_refs
            ):
                bound_cases[case_id] = (accepted_ref, new_ref)
    for case_id in cross_cases:
        if case_id not in bound_cases:
            errors.append(
                f"{label}: cross-domain case is missing a valid structured binding: {case_id}"
            )
    for new_ref in new_refs:
        if not any(bound_new_ref == new_ref for _, bound_new_ref in bound_cases.values()):
            errors.append(
                f"{label}: new slice must participate in a structured cross-domain binding: {new_ref}"
            )

    for field, expected_case_field in (
        ("web_checkpoint_binding", "first_product_web_checkpoint"),
        ("live_ad_hoc_checkpoint_binding", "live_ad_hoc_question_checkpoint"),
    ):
        binding = alignment.get(field)
        if not isinstance(binding, dict):
            errors.append(f"{label}: {field} must be a mapping")
            continue
        case_id = binding.get("case_id")
        new_ref = binding.get("new_slice_ref")
        cross_case_id = binding.get("executes_cross_domain_case_id")
        if case_id != alignment.get(expected_case_field):
            errors.append(f"{label}: {field}.case_id must match {expected_case_field}")
        if not isinstance(new_ref, str) or new_ref not in new_refs:
            errors.append(f"{label}: {field}.new_slice_ref must reference a new slice")
        if (
            not isinstance(cross_case_id, str)
            or cross_case_id not in bound_cases
        ):
            errors.append(
                f"{label}: {field}.executes_cross_domain_case_id must reference a structured cross-domain binding"
            )
        elif isinstance(new_ref, str) and bound_cases[cross_case_id][1] != new_ref:
            errors.append(
                f"{label}: {field} must execute a cross-domain case bound to the same new slice"
            )

    additional_web_bindings = alignment.get("additional_web_checkpoint_bindings")
    if additional_web_bindings is not None:
        if not isinstance(additional_web_bindings, dict):
            errors.append(
                f"{label}: additional_web_checkpoint_bindings must be a mapping"
            )
        else:
            seen_additional_cases: set[str] = set()
            for binding_name, binding in additional_web_bindings.items():
                if not isinstance(binding, dict):
                    errors.append(
                        f"{label}: additional_web_checkpoint_bindings.{binding_name} must be a mapping"
                    )
                    continue
                case_id = binding.get("case_id")
                new_ref = binding.get("new_slice_ref")
                cross_case_id = binding.get("executes_cross_domain_case_id")
                if (
                    not isinstance(case_id, str)
                    or re.fullmatch(r"V-WEB-[0-9]{3,}", case_id) is None
                    or case_id in seen_additional_cases
                    or case_id == alignment.get("first_product_web_checkpoint")
                ):
                    errors.append(
                        f"{label}: additional Web checkpoint case IDs must be unique V-WEB cases"
                    )
                else:
                    seen_additional_cases.add(case_id)
                if not isinstance(new_ref, str) or new_ref not in new_refs:
                    errors.append(
                        f"{label}: additional Web checkpoint must reference a new slice"
                    )
                if (
                    not isinstance(cross_case_id, str)
                    or cross_case_id not in bound_cases
                ):
                    errors.append(
                        f"{label}: additional Web checkpoint must execute a structured cross-domain case"
                    )
                elif (
                    isinstance(new_ref, str)
                    and bound_cases[cross_case_id][1] != new_ref
                ):
                    errors.append(
                        f"{label}: additional Web checkpoint and cross-domain case must bind the same slice"
                    )
    return errors


def validate_product_goal_alignment_manifest(
    manifest: dict[str, object], text: str, label: str, iteration: str
) -> list[str]:
    if not requires_product_goal_alignment(iteration):
        return []

    alignment = manifest.get("product_goal_alignment")
    if not isinstance(alignment, dict):
        return [f"{label}: product_goal_alignment must be a mapping from ITER-007 onward"]

    errors: list[str] = []
    if alignment.get("target_ref") != "SYS-PRODUCT-SUCCESS":
        errors.append(
            f"{label}: product_goal_alignment.target_ref must equal SYS-PRODUCT-SUCCESS"
        )
    for field in PRODUCT_GOAL_ALIGNMENT_MANIFEST_SCALARS:
        value = alignment.get(field)
        if (
            not isinstance(value, str)
            or is_pending(value)
            or is_absent_evidence(value)
            or has_unresolved_placeholder(value)
        ):
            errors.append(
                f"{label}: product_goal_alignment.{field} must be a resolved scalar"
            )
    if alignment.get("implementation_question_visibility") != "hidden":
        errors.append(
            f"{label}: product_goal_alignment.implementation_question_visibility must equal hidden"
        )
    if (
        alignment.get("implementation_project_identity_and_source_visibility")
        != "hidden-until-product-code-freeze"
    ):
        errors.append(
            f"{label}: implementation project identity and source must remain hidden until product code freeze"
        )
    if alignment.get("supported_count_denominator") != "answerable-only":
        errors.append(
            f"{label}: supported_count_denominator must equal answerable-only"
        )
    if alignment.get("boundary_gap_counted_as_supported") is not False:
        errors.append(
            f"{label}: boundary_gap_counted_as_supported must be false"
        )
    if alignment.get("held_out_evaluation_owner") not in {
        "independent-evaluator",
        "user",
    }:
        errors.append(
            f"{label}: product_goal_alignment.held_out_evaluation_owner must equal independent-evaluator or user"
        )
    for field in PRODUCT_GOAL_ALIGNMENT_MANIFEST_DIGESTS:
        value = alignment.get(field)
        if not isinstance(value, str) or re.fullmatch(
            r"sha256:[0-9a-f]{64}", value
        ) is None:
            errors.append(
                f"{label}: product_goal_alignment.{field} must be an exact sha256 digest"
            )

    counts: dict[str, int] = {}
    for field in PRODUCT_GOAL_ALIGNMENT_MANIFEST_COUNTS:
        value = alignment.get(field)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            errors.append(
                f"{label}: product_goal_alignment.{field} must be a non-negative integer"
            )
        else:
            counts[field] = value
    total = counts.get("held_out_question_count")
    answerable = counts.get("held_out_answerable_question_count")
    boundary = counts.get("held_out_boundary_question_count")
    without_symbol = counts.get(
        "held_out_answerable_without_symbol_count_minimum"
    )
    without_symbol_per_project = counts.get(
        "held_out_answerable_without_symbol_per_project_minimum"
    )
    baseline_supported = counts.get("held_out_baseline_supported_count")
    target_supported = counts.get("held_out_target_supported_count")
    if (
        total is not None
        and answerable is not None
        and boundary is not None
        and total != answerable + boundary
    ):
        errors.append(
            f"{label}: held_out_question_count must equal answerable plus boundary counts"
        )
    if (
        answerable is not None
        and without_symbol is not None
        and not (0 < without_symbol <= answerable)
    ):
        errors.append(
            f"{label}: held-out no-symbol minimum must be positive and no greater than answerable count"
        )
    if (
        without_symbol is not None
        and without_symbol_per_project is not None
        and not (0 < without_symbol_per_project * 2 <= without_symbol)
    ):
        errors.append(
            f"{label}: per-project no-symbol minimum must fit the two-project total minimum"
        )
    if (
        answerable is not None
        and baseline_supported is not None
        and not (0 <= baseline_supported < answerable)
    ):
        errors.append(
            f"{label}: held-out baseline supported count must be lower than answerable count"
        )
    if (
        boundary is not None
        and boundary == 0
    ):
        errors.append(
            f"{label}: held_out_boundary_question_count must be greater than zero"
        )
    live_count = counts.get("live_ad_hoc_question_count")
    live_without_symbol = counts.get(
        "live_ad_hoc_without_symbol_count_minimum"
    )
    if (
        live_count is not None
        and live_without_symbol is not None
        and not (0 < live_without_symbol <= live_count)
    ):
        errors.append(
            f"{label}: live no-symbol minimum must be positive and no greater than live question count"
        )
    if (
        answerable is not None
        and baseline_supported is not None
        and target_supported is not None
    ):
        minimum_target = min(answerable, max(baseline_supported + 4, 8))
        if not (
            baseline_supported < target_supported <= answerable
            and target_supported >= minimum_target
        ):
            errors.append(
                f"{label}: held-out target must be above baseline, no greater than answerable, "
                "and at least min(answerable, max(baseline + 4, 8))"
            )
    for field in ("cross_domain_case_count", "live_ad_hoc_question_count"):
        if counts.get(field) == 0:
            errors.append(
                f"{label}: product_goal_alignment.{field} must be greater than zero"
            )

    sequences: dict[str, list[str]] = {}
    for field in PRODUCT_GOAL_ALIGNMENT_MANIFEST_SEQUENCES:
        items = (
            manifest_resolved_sequence_items(text, "product_goal_alignment", field)
            if field in alignment
            else None
        )
        if items is None:
            errors.append(
                f"{label}: product_goal_alignment.{field} must contain at least one item"
            )
        else:
            sequences[field] = items
    cross_domain_count = counts.get("cross_domain_case_count")
    if (
        cross_domain_count is not None
        and "cross_domain_cases" in sequences
        and len(sequences["cross_domain_cases"]) != cross_domain_count
    ):
        errors.append(
            f"{label}: cross_domain_cases count must equal cross_domain_case_count"
        )
    for case_id in sequences.get("cross_domain_cases", []):
        if re.fullmatch(r"V-XD-[0-9]{3,}", case_id) is None:
            errors.append(
                f"{label}: cross_domain_cases item must match V-XD-NNN: {case_id}"
            )
    blocking_case_ids = sequences.get("blocking_case_ids", [])
    required_blocking_cases = set(sequences.get("cross_domain_cases", []))
    for field in (
        "first_product_web_checkpoint",
        "live_ad_hoc_question_checkpoint",
    ):
        value = alignment.get(field)
        if isinstance(value, str):
            required_blocking_cases.add(value)
    additional_web_bindings = alignment.get("additional_web_checkpoint_bindings")
    if isinstance(additional_web_bindings, dict):
        for binding in additional_web_bindings.values():
            if isinstance(binding, dict) and isinstance(binding.get("case_id"), str):
                required_blocking_cases.add(str(binding["case_id"]))
    if not required_blocking_cases.issubset(set(blocking_case_ids)):
        errors.append(
            f"{label}: blocking_case_ids must include every cross-domain, Web and ad-hoc Case"
        )
    for case_id in blocking_case_ids:
        if re.fullmatch(r"V-(?:PRE-)?[A-Z0-9]+(?:-[A-Z0-9]+)*", case_id) is None:
            errors.append(
                f"{label}: blocking_case_ids item is not a valid verification case ID: {case_id}"
            )
    for field, pattern in (
        ("first_product_web_checkpoint", r"V-WEB-[0-9]{3,}"),
        ("live_ad_hoc_question_checkpoint", r"V-ADHOC-[0-9]{3,}"),
    ):
        value = alignment.get(field)
        if not isinstance(value, str) or re.fullmatch(pattern, value) is None:
            errors.append(
                f"{label}: product_goal_alignment.{field} must be a verification case ID"
            )
    errors.extend(validate_product_goal_structured_bindings(alignment, sequences, label))
    return errors


def validate_product_goal_alignment_documents(
    proposal: Document | None,
    verification: Document | None,
    iteration: str,
) -> list[str]:
    if not requires_product_goal_alignment(iteration):
        return []

    errors: list[str] = []
    if proposal is None:
        errors.append(f"{iteration}: selected iteration is missing proposal.md")
    else:
        dependencies = proposal.metadata.get("depends_on", [])
        if (
            not isinstance(dependencies, list)
            or "SYS-PRODUCT-SUCCESS" not in dependencies
        ):
            errors.append(
                f"{proposal.relative_path}: product-goal-aligned proposal must depend on SYS-PRODUCT-SUCCESS"
            )
    errors.extend(validate_product_goal_v000(verification, iteration))
    return errors


def markdown_table_case_rows(body: str, case_id: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or not stripped.endswith("|"):
            continue
        cells = [cell.strip() for cell in re.split(r"(?<!\\)\|", stripped[1:-1])]
        if cells and cells[0] == case_id:
            rows.append(cells)
    return rows


def validate_blocking_verification_case(
    verification: Document | None,
    case_id: str,
    *,
    required_references: tuple[str, ...] = (),
    require_pass: bool = False,
    expected_evidence: str | None = None,
) -> list[str]:
    if verification is None:
        return [f"missing verification matrix for {case_id}"]
    label = verification.relative_path
    rows = markdown_table_case_rows(verification.body, case_id)
    if len(rows) != 1:
        return [f"{label}: must define exactly one {case_id} row"]
    row = rows[0]
    if len(row) != 7:
        return [f"{label}: {case_id} must use the exact seven-column schema"]

    errors: list[str] = []
    for index, field in enumerate(
        ("claim", "level", "frozen input / oracle", "expected"), start=1
    ):
        value = row[index]
        if (
            not value
            or is_pending(value)
            or is_absent_evidence(value)
            or has_unresolved_placeholder(value)
        ):
            errors.append(f"{label}: {case_id} {field} must be resolved")
    status_tokens = set(re.findall(r"[A-Z]+(?:-[A-Z]+)*", row[6].upper()))
    if "BLOCKING" not in status_tokens or "NON-BLOCKING" in status_tokens:
        errors.append(f"{label}: {case_id} must remain blocking")
    if require_pass:
        evidence = row[5]
        if (
            not evidence
            or is_pending(evidence)
            or is_absent_evidence(evidence)
            or has_unresolved_placeholder(evidence)
        ):
            errors.append(f"{label}: completed {case_id} must bind resolved evidence")
        elif expected_evidence is not None and evidence != expected_evidence:
            errors.append(
                f"{label}: completed {case_id} Evidence must equal {expected_evidence}"
            )
        if (
            "PASS" not in status_tokens
            or "FAIL" in status_tokens
            or "NOT-RUN" in status_tokens
        ):
            errors.append(f"{label}: completed {case_id} must be PASS")
    joined = " ".join(row[1:5])
    for reference in required_references:
        if reference not in joined:
            errors.append(
                f"{label}: {case_id} must cite cumulative capability reference {reference}"
            )
    return errors


def non_negative_metadata_integer(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if value >= 0 else None
    if isinstance(value, str) and re.fullmatch(r"0|[1-9][0-9]*", value):
        return int(value)
    return None


def validate_product_goal_result(
    result: Document,
    iteration: str,
    manifest_path: Path,
    verification: Document,
    by_id: dict[str, Document] | None = None,
) -> list[str]:
    label = result.relative_path
    errors: list[str] = []
    expected_result_prefix = (
        f"docs/project/iterations/iteration-{iteration.removeprefix('ITER-')}/results/"
    )
    if not label.startswith(expected_result_prefix) or "/" in label.removeprefix(
        expected_result_prefix
    ):
        errors.append(f"{label}: product-goal Result must be in this iteration's results directory")
    if result.metadata.get("kind") != "iteration-result":
        errors.append(f"{label}: product-goal Result kind must be iteration-result")
    if result.metadata.get("status") != "product-goal-pass":
        errors.append(f"{label}: product-goal PASS Result status must be product-goal-pass")
    if result.metadata.get("authority") != "execution-evidence":
        errors.append(f"{label}: product-goal PASS Result authority must be execution-evidence")
    owners = result.metadata.get("owners", [])
    if not isinstance(owners, list) or "quality" not in owners:
        errors.append(f"{label}: product-goal PASS Result must be owned by quality")

    for field, expected in {
        **PRODUCT_GOAL_V000_METADATA,
        "product_goal_verdict": "PASS",
    }.items():
        if result.metadata.get(field) != expected:
            errors.append(f"{label}: {field} must equal {expected}")
    for field in ("product_goal_subject_digest", "product_goal_report_digest"):
        value = result.metadata.get(field)
        if not isinstance(value, str) or re.fullmatch(
            r"sha256:[0-9a-f]{64}", value
        ) is None:
            errors.append(f"{label}: {field} must be an exact sha256 digest")

    try:
        manifest_text = manifest_path.read_text(encoding="utf-8")
        manifest = safe_load_manifest(manifest_text)
    except (OSError, UnicodeError, SafeYamlError) as error:
        return errors + [f"{label}: cannot load product-goal Manifest: {error}"]
    alignment = manifest.get("product_goal_alignment")
    if not isinstance(alignment, dict):
        return errors + [f"{label}: Manifest has no product_goal_alignment"]

    completed_case_ids = manifest_resolved_sequence_items(
        manifest_text, "product_goal_alignment", "blocking_case_ids"
    ) or []
    for case_id in completed_case_ids:
        errors.extend(
            validate_blocking_verification_case(
                verification,
                case_id,
                require_pass=True,
            )
        )

    new_slice_refs = manifest_resolved_sequence_items(
        manifest_text, "product_goal_alignment", "new_capability_slice_refs"
    ) or []
    development = manifest.get("development")
    development_slices = (
        development.get("slices") if isinstance(development, dict) else None
    )
    if not isinstance(development_slices, dict):
        development_slices = {}
    slice_result_refs: list[str] = []
    for slice_ref in new_slice_refs:
        manifest_slice = development_slices.get(slice_ref)
        slice_result_ref = (
            manifest_slice.get("result") if isinstance(manifest_slice, dict) else None
        )
        if (
            not isinstance(slice_result_ref, str)
            or is_pending(slice_result_ref)
            or is_absent_evidence(slice_result_ref)
            or has_unresolved_placeholder(slice_result_ref)
        ):
            errors.append(
                f"{label}: completed product Result requires a resolved Slice Result for {slice_ref}"
            )
            continue
        slice_result_refs.append(slice_result_ref)
        if by_id is not None:
            slice_document = by_id.get(slice_ref)
            slice_result = by_id.get(slice_result_ref)
            if slice_document is None or slice_result is None:
                errors.append(
                    f"{label}: completed product Result must aggregate existing Slice and Slice Result {slice_ref}"
                )
                continue
            case_ids = slice_document.metadata.get(
                "product_goal_slice_gate_case_ids", []
            )
            if not isinstance(case_ids, list):
                case_ids = []
            for case_id in case_ids:
                errors.extend(
                    validate_blocking_verification_case(
                        verification,
                        str(case_id),
                        require_pass=True,
                        expected_evidence=f"{slice_result_ref}#{case_id}",
                    )
                )

    for field in PRODUCT_GOAL_RESULT_DIGEST_FIELDS:
        if result.metadata.get(field) != alignment.get(field):
            errors.append(f"{label}: {field} must match the frozen Manifest")

    counts: dict[str, int] = {}
    for field in PRODUCT_GOAL_RESULT_COUNT_FIELDS:
        value = non_negative_metadata_integer(result.metadata.get(field))
        if value is None:
            errors.append(f"{label}: {field} must be a non-negative integer")
        else:
            counts[field] = value
    for result_field, manifest_field in (
        ("held_out_question_count", "held_out_question_count"),
        ("held_out_baseline_supported_count", "held_out_baseline_supported_count"),
    ):
        if result_field in counts and counts[result_field] != alignment.get(manifest_field):
            errors.append(f"{label}: {result_field} must match the frozen Manifest")
    actual = counts.get("held_out_actual_supported_count")
    answerable = alignment.get("held_out_answerable_question_count")
    target = alignment.get("held_out_target_supported_count")
    if (
        actual is not None
        and isinstance(answerable, int)
        and isinstance(target, int)
        and not (target <= actual <= answerable)
    ):
        errors.append(
            f"{label}: held_out_actual_supported_count must reach target without exceeding answerable count"
        )
    boundary_correct = counts.get("held_out_boundary_correct_gap_count")
    if boundary_correct != alignment.get("held_out_boundary_question_count"):
        errors.append(
            f"{label}: held_out_boundary_correct_gap_count must equal the frozen boundary count"
        )
    no_symbol_supported = counts.get(
        "held_out_answerable_without_symbol_supported_count"
    )
    no_symbol_minimum = alignment.get(
        "held_out_answerable_without_symbol_count_minimum"
    )
    if (
        not isinstance(no_symbol_supported, int)
        or not isinstance(no_symbol_minimum, int)
        or no_symbol_supported < no_symbol_minimum
    ):
        errors.append(
            f"{label}: held_out_answerable_without_symbol_supported_count must reach the frozen minimum"
        )
    live_no_symbol_pass = counts.get("live_ad_hoc_without_symbol_pass_count")
    live_no_symbol_minimum = alignment.get(
        "live_ad_hoc_without_symbol_count_minimum"
    )
    if (
        not isinstance(live_no_symbol_pass, int)
        or not isinstance(live_no_symbol_minimum, int)
        or live_no_symbol_pass < live_no_symbol_minimum
    ):
        errors.append(
            f"{label}: live_ad_hoc_without_symbol_pass_count must reach the frozen minimum"
        )
    for field in (
        "major_error_count",
        "source_fallback_count",
        "update_fallback_count",
        "direct_fallback_count",
    ):
        if counts.get(field) != 0:
            errors.append(f"{label}: {field} must equal zero")
    for result_field, manifest_field in (
        ("cross_domain_pass_count", "cross_domain_case_count"),
        ("live_ad_hoc_pass_count", "live_ad_hoc_question_count"),
    ):
        minimum = alignment.get(manifest_field)
        if (
            result_field in counts
            and isinstance(minimum, int)
            and counts[result_field] < minimum
        ):
            errors.append(f"{label}: {result_field} must reach the frozen Manifest count")
    if result.metadata.get("mature_source_agent_comparison") != "non-regression":
        errors.append(f"{label}: mature_source_agent_comparison must equal non-regression")
    if result.metadata.get("product_web_manual_verification") != "passed":
        errors.append(f"{label}: product_web_manual_verification must equal passed")

    dependencies = result.metadata.get("depends_on", [])
    required_dependencies = [
        verification.identifier,
        *new_slice_refs,
        *slice_result_refs,
    ]
    if not isinstance(dependencies, list):
        dependencies = []
    for reference in required_dependencies:
        if reference not in dependencies:
            errors.append(f"{label}: product-goal Result must depend on {reference}")
    for section in empty_required_sections(
        result, PRODUCT_GOAL_RESULT_REQUIRED_SECTIONS
    ):
        errors.append(f"{label}: product-goal Result section is missing or empty: {section}")
    return errors


def validate_product_goal_v000(
    verification: Document | None,
    iteration: str,
    *,
    require_pass: bool = False,
    by_id: dict[str, Document] | None = None,
) -> list[str]:
    if not requires_product_goal_alignment(iteration):
        return []
    if verification is None:
        return [f"{iteration}: selected iteration is missing verification-matrix.md"]

    label = verification.relative_path
    for field, expected in PRODUCT_GOAL_V000_METADATA.items():
        if verification.metadata.get(field) != expected:
            errors = [
                f"{label}: {field} must equal {expected} for the V-000 product gate"
            ]
            return errors
    rows = markdown_table_case_rows(verification.body, "V-000")
    if len(rows) != 1:
        return [f"{label}: must define exactly one V-000 row"]
    row = rows[0]
    if len(row) != 7:
        return [f"{label}: V-000 must use the exact seven-column verification schema"]

    errors: list[str] = []
    expected_contract = (
        PRODUCT_GOAL_V000_CLAIM,
        PRODUCT_GOAL_V000_LEVEL,
        PRODUCT_GOAL_V000_FROZEN_INPUT,
        PRODUCT_GOAL_V000_EXPECTED,
    )
    for index, (field, expected) in enumerate(
        zip(
            ("claim", "level", "frozen input / oracle", "expected"),
            expected_contract,
        ),
        start=1,
    ):
        if row[index] != expected:
            errors.append(
                f"{label}: V-000 {field} must match the product-goal contract"
            )

    status = row[6]
    status_tokens = set(re.findall(r"[A-Z]+(?:-[A-Z]+)*", status.upper()))
    if "BLOCKING" not in status_tokens or "NON-BLOCKING" in status_tokens:
        errors.append(f"{label}: V-000 status must remain blocking")

    if require_pass:
        evidence = row[5]
        if (
            not evidence
            or is_pending(evidence)
            or is_absent_evidence(evidence)
            or has_unresolved_placeholder(evidence)
        ):
            errors.append(f"{label}: completed V-000 must bind resolved evidence")
        if (
            "PASS" not in status_tokens
            or "FAIL" in status_tokens
            or "NOT-RUN" in status_tokens
        ):
            errors.append(f"{label}: completed iteration requires V-000 PASS")
        result_id = verification.metadata.get("product_goal_result_id")
        if (
            not isinstance(result_id, str)
            or is_pending(result_id)
            or is_absent_evidence(result_id)
            or has_unresolved_placeholder(result_id)
        ):
            errors.append(f"{label}: completed V-000 must bind product_goal_result_id")
        elif by_id is not None:
            result = by_id.get(result_id)
            if (
                result is None
                or result.metadata.get("kind") != "iteration-result"
                or str(result.metadata.get("iteration", "")) != iteration
                or result.metadata.get("product_goal_gate") != "V-000"
                or result.metadata.get("product_goal_outcome")
                != "user-visible-general-source-qa-delta"
                or result.metadata.get("product_goal_evaluation")
                != "independent-hidden-plus-live-ad-hoc"
                or result.metadata.get("product_goal_verdict") != "PASS"
            ):
                errors.append(
                    f"{label}: product_goal_result_id must reference a same-iteration PASS product result"
                )
            else:
                if evidence != result_id:
                    errors.append(
                        f"{label}: completed V-000 Evidence must equal product_goal_result_id"
                    )
                errors.extend(
                    validate_product_goal_result(
                        result,
                        iteration,
                        verification.path.parent / "manifest.yaml",
                        verification,
                        by_id,
                    )
                )
    return errors


def validate_goal_aligned_required_document(document: Document) -> list[str]:
    errors: list[str] = []
    if not has_substantive_body(document):
        errors.append(
            f"{document.relative_path}: selected iteration document has no substantive body"
        )
    if (
        has_unresolved_placeholder(document.metadata)
        or has_pending_marker(document.metadata)
        or has_unresolved_placeholder(document.body)
    ):
        errors.append(
            f"{document.relative_path}: selected iteration document contains unresolved template placeholders"
        )
    for section in empty_active_required_sections(document):
        errors.append(
            f"{document.relative_path}: selected iteration section is missing or empty: {section}"
        )
    return errors


def validate_product_goal_readiness_authorization(
    readiness: Document,
) -> list[str]:
    errors: list[str] = []
    for field in ("authorized_by", "authorized_at"):
        value = readiness.metadata.get(field, "")
        if (
            not isinstance(value, str)
            or is_pending(value)
            or is_absent_evidence(value)
            or has_unresolved_placeholder(value)
        ):
            errors.append(f"{readiness.relative_path}: selected iteration {field} is unresolved")
    authorized_at = readiness.metadata.get("authorized_at", "")
    if isinstance(authorized_at, str) and re.fullmatch(
        r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:Z|[+-][0-9]{2}:[0-9]{2})",
        authorized_at,
    ) is None:
        errors.append(
            f"{readiness.relative_path}: authorized_at must be an ISO-8601 timestamp with timezone"
        )
    for field, expected in (
        ("product_goal_alignment_verdict", "accepted"),
        ("product_goal_alignment_reviewed_by", "user"),
    ):
        if readiness.metadata.get(field) != expected:
            errors.append(f"{readiness.relative_path}: {field} must equal {expected}")
    review_ref = readiness.metadata.get("product_goal_alignment_review_ref", "")
    if not isinstance(review_ref, str) or re.fullmatch(
        r"codex-user-message:sha256:[0-9a-f]{64}", review_ref
    ) is None:
        errors.append(
            f"{readiness.relative_path}: product_goal_alignment_review_ref must bind an exact user message digest"
        )
    return errors


def validate_active_manifest(
    path: Path,
    iteration: str,
    *,
    allowed_statuses: set[str] | None = None,
) -> list[str]:
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
        valid_statuses = ACTIVE_ITERATION_STATUSES if allowed_statuses is None else allowed_statuses
        if not isinstance(manifest_status, str) or manifest_status not in valid_statuses:
            errors.append(
                f"{label}: iteration.status must be one of "
                + ", ".join(sorted(valid_statuses))
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

    errors.extend(
        validate_product_goal_alignment_manifest(
            manifest, manifest_text, label, iteration
        )
    )

    if (
        has_unresolved_placeholder(manifest_text)
        or has_pending_marker(manifest)
        or MANIFEST_PENDING_RE.search(manifest_text)
    ):
        errors.append(f"{label}: contains unresolved template placeholders")
    return errors


def validate_product_goal_execution_readiness(
    manifest: dict[str, object],
    label: str,
    iteration: str,
    by_id: dict[str, Document],
    new_refs: list[str],
    verification: Document | None,
) -> list[str]:
    """Validate inputs that must be frozen before the first product Slice runs."""

    errors: list[str] = []
    alignment = manifest.get("product_goal_alignment")
    if not isinstance(alignment, dict):
        return errors

    blocking_cases = alignment.get("blocking_case_ids")
    blocking_case_ids = (
        [str(item) for item in blocking_cases]
        if isinstance(blocking_cases, list)
        else []
    )
    readiness_cases = alignment.get("readiness_blocking_case_ids")
    if not isinstance(readiness_cases, list) or not readiness_cases:
        errors.append(
            f"{label}: readiness_blocking_case_ids must be a non-empty sequence before Slice execution"
        )
        readiness_case_ids: list[str] = []
    else:
        readiness_case_ids = [str(item) for item in readiness_cases]
        if set(readiness_case_ids).intersection(blocking_case_ids):
            errors.append(
                f"{label}: readiness_blocking_case_ids must remain separate from Slice-owned blocking_case_ids"
            )
        for case_id in readiness_case_ids:
            errors.extend(
                validate_blocking_verification_case(
                    verification, case_id, require_pass=True
                )
            )

    source_scope = manifest.get("source_scope")
    if not isinstance(source_scope, dict):
        errors.append(f"{label}: source_scope must be a mapping before Slice execution")
        source_scope = {}
    for field in ("provider", "content_kind", "contract_ref"):
        value = source_scope.get(field)
        if (
            not isinstance(value, str)
            or is_pending(value)
            or is_absent_evidence(value)
            or has_unresolved_placeholder(value)
        ):
            errors.append(f"{label}: source_scope.{field} must be resolved")
    if source_scope.get("question_or_suite_driven_update_allowed") is not False:
        errors.append(
            f"{label}: source_scope.question_or_suite_driven_update_allowed must be false"
        )
    source_digest = source_scope.get("authorized_software_sources_digest")
    if source_digest != alignment.get("authorized_software_sources_digest"):
        errors.append(
            f"{label}: source_scope.authorized_software_sources_digest must match product_goal_alignment"
        )
    source_cases = source_scope.get("verification_case_ids")
    if not isinstance(source_cases, list) or not source_cases:
        errors.append(
            f"{label}: source_scope.verification_case_ids must bind update-without-question Cases"
        )
    else:
        source_case_ids = [str(item) for item in source_cases]
        if not set(source_case_ids).issubset(set(blocking_case_ids)):
            errors.append(
                f"{label}: source_scope verification Cases must be blocking Cases"
            )
        for case_id in source_case_ids:
            errors.extend(validate_blocking_verification_case(verification, case_id))

    answer_protocol = manifest.get("answer_protocol")
    if not isinstance(answer_protocol, dict):
        errors.append(f"{label}: answer_protocol must be a mapping before Slice execution")
        answer_protocol = {}
    expected_calls = {
        "planner_model_calls": 1,
        "draft_model_calls": 1,
        "independent_reviewer_model_calls": 1,
        "exact_total_model_calls_per_question": 3,
    }
    for field, expected in expected_calls.items():
        if answer_protocol.get(field) != expected:
            errors.append(f"{label}: answer_protocol.{field} must equal {expected}")
    if answer_protocol.get("deterministic_schema_grounding_and_authorization_checks") is not True:
        errors.append(
            f"{label}: answer_protocol deterministic checks must be true"
        )
    if answer_protocol.get("retries_allowed") is not False:
        errors.append(f"{label}: answer_protocol.retries_allowed must be false")
    if answer_protocol.get("status") != "frozen":
        errors.append(f"{label}: answer_protocol.status must equal frozen")

    readiness_inputs = manifest.get("readiness_inputs")
    if not isinstance(readiness_inputs, dict):
        errors.append(f"{label}: readiness_inputs must be a mapping before Slice execution")
        readiness_inputs = {}
    contract_refs = readiness_inputs.get("required_system_contract_refs")
    if not isinstance(contract_refs, list) or not contract_refs:
        errors.append(
            f"{label}: readiness_inputs.required_system_contract_refs must be non-empty"
        )
        contract_ids: list[str] = []
    else:
        contract_ids = [str(item) for item in contract_refs]
        if len(contract_ids) != len(set(contract_ids)):
            errors.append(f"{label}: required_system_contract_refs must be unique")

    named_contract_fields = (
        "source_semantics_contract_ref",
        "implementation_query_contract_ref",
        "no_payload_contract_ref",
        "answer_protocol_contract_ref",
    )
    for field in named_contract_fields:
        reference = readiness_inputs.get(field)
        if not isinstance(reference, str) or reference not in contract_ids:
            errors.append(
                f"{label}: readiness_inputs.{field} must reference required_system_contract_refs"
            )
    for reference in (source_scope.get("contract_ref"), answer_protocol.get("contract_ref")):
        if not isinstance(reference, str) or reference not in contract_ids:
            errors.append(
                f"{label}: source and answer protocol Contracts must be listed in required_system_contract_refs"
            )

    system_root = (REPOSITORY / "docs/system").resolve()
    for reference in contract_ids:
        target = by_id.get(reference)
        in_system_root = False
        if target is not None:
            try:
                target.path.resolve().relative_to(system_root)
                in_system_root = True
            except ValueError:
                pass
        if (
            target is None
            or not in_system_root
            or target.metadata.get("kind") != "system-contract"
            or target.metadata.get("status") != "current"
            or target.metadata.get("authority") != "normative"
        ):
            errors.append(
                f"{label}: readiness Contract must resolve to a current normative system-contract: {reference}"
            )

    frontend = readiness_inputs.get("java_frontend")
    if not isinstance(frontend, dict):
        errors.append(f"{label}: readiness_inputs.java_frontend must be a mapping")
        frontend = {}
    for field in ("artifact_ref", "version", "license_ref"):
        value = frontend.get(field)
        if (
            not isinstance(value, str)
            or is_pending(value)
            or is_absent_evidence(value)
            or has_unresolved_placeholder(value)
        ):
            errors.append(f"{label}: java_frontend.{field} must be resolved")
    for field in (
        "offline_artifact_digest",
        "canonicalization_oracle_digest",
        "information_preservation_oracle_digest",
        "information_boundary_oracle_digest",
        "hidden_freeze_protocol_digest",
        "system_contract_set_digest",
    ):
        value = (
            frontend.get(field)
            if field
            not in {"hidden_freeze_protocol_digest", "system_contract_set_digest"}
            else readiness_inputs.get(field)
        )
        if not isinstance(value, str) or re.fullmatch(
            r"sha256:[0-9a-f]{64}", value
        ) is None:
            errors.append(f"{label}: {field} must be an exact sha256 digest")
    visible_corpus_digest = alignment.get("visible_development_corpus_digest")
    if not isinstance(visible_corpus_digest, str) or re.fullmatch(
        r"sha256:[0-9a-f]{64}", visible_corpus_digest
    ) is None:
        errors.append(
            f"{label}: visible_development_corpus_digest must be an exact sha256 digest"
        )

    readiness = by_id.get(f"{iteration}-READINESS")
    readiness_dependencies = (
        readiness.metadata.get("depends_on", []) if readiness is not None else []
    )
    if not isinstance(readiness_dependencies, list):
        readiness_dependencies = []
    for reference in contract_ids:
        if reference not in readiness_dependencies:
            errors.append(
                f"{label}: accepted Readiness must depend on frozen Contract {reference}"
            )
    if new_refs:
        first_slice = by_id.get(new_refs[0])
        first_dependencies = (
            first_slice.metadata.get("depends_on", []) if first_slice is not None else []
        )
        if not isinstance(first_dependencies, list) or f"{iteration}-READINESS" not in first_dependencies:
            errors.append(
                f"{label}: first executable Slice must depend on accepted Readiness"
            )

    canary_bindings = alignment.get("early_hidden_canary_bindings")
    expected_canary_refs = set(new_refs[:-1])
    canary_refs: list[str] = []
    canary_cases: list[str] = []
    if expected_canary_refs and not isinstance(canary_bindings, dict):
        errors.append(
            f"{label}: early_hidden_canary_bindings must cover every pre-final Slice"
        )
    elif isinstance(canary_bindings, dict):
        for binding_name, binding in canary_bindings.items():
            if not isinstance(binding, dict):
                errors.append(
                    f"{label}: early_hidden_canary_bindings.{binding_name} must be a mapping"
                )
                continue
            new_ref = binding.get("new_slice_ref")
            case_id = binding.get("case_id")
            if not isinstance(new_ref, str) or new_ref not in expected_canary_refs:
                errors.append(
                    f"{label}: early hidden canary must bind a pre-final Slice"
                )
            else:
                canary_refs.append(new_ref)
            if not isinstance(case_id, str) or re.fullmatch(
                r"V-CANARY-[0-9]{3,}", case_id
            ) is None:
                errors.append(
                    f"{label}: early hidden canary case_id must match V-CANARY-NNN"
                )
            else:
                canary_cases.append(case_id)
                if case_id not in blocking_case_ids:
                    errors.append(
                        f"{label}: early hidden canary Case must be blocking"
                    )
                bound_slice = by_id.get(new_ref) if isinstance(new_ref, str) else None
                slice_gate_cases = (
                    bound_slice.metadata.get("product_goal_slice_gate_case_ids", [])
                    if bound_slice is not None
                    else []
                )
                if not isinstance(slice_gate_cases, list) or case_id not in {
                    str(item) for item in slice_gate_cases
                }:
                    errors.append(
                        f"{label}: early hidden canary Case must be owned by its bound Slice"
                    )
            if binding.get("evaluation_owner") not in {"independent-evaluator", "user"}:
                errors.append(
                    f"{label}: early hidden canary must have an independent evaluation owner"
                )
            if binding.get("implementation_visibility") != "hidden-until-slice-code-freeze":
                errors.append(
                    f"{label}: early hidden canary must remain hidden until Slice code freeze"
                )
            if binding.get("burn_rule") != "product-change-after-exposure-burns-canary-and-preserves-failure":
                errors.append(
                    f"{label}: early hidden canary must freeze the burn-and-preserve-failure rule"
                )
            for field in ("project_manifest_digest", "suite_digest"):
                value = binding.get(field)
                if not isinstance(value, str) or re.fullmatch(
                    r"sha256:[0-9a-f]{64}", value
                ) is None:
                    errors.append(
                        f"{label}: early hidden canary {field} must be an exact sha256 digest"
                    )
        if set(canary_refs) != expected_canary_refs or len(canary_refs) != len(set(canary_refs)):
            errors.append(
                f"{label}: early hidden canaries must bind each pre-final Slice exactly once"
            )
        if len(canary_cases) != len(set(canary_cases)):
            errors.append(f"{label}: early hidden canary Case IDs must be unique")

    return errors


def validate_product_goal_reference_targets(
    manifest_path: Path,
    iteration: str,
    by_id: dict[str, Document],
    *,
    require_execution_slice_sequence: bool = False,
    require_completed_slice_sequence: bool = False,
    verification: Document | None = None,
) -> list[str]:
    if not requires_product_goal_alignment(iteration):
        return []
    label = _path_label(manifest_path)
    try:
        text = manifest_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return []
    try:
        manifest = safe_load_manifest(text)
    except SafeYamlError:
        return []
    alignment = manifest.get("product_goal_alignment")
    if not isinstance(alignment, dict):
        return []

    errors: list[str] = []
    accepted_refs = manifest_resolved_sequence_items(
        text, "product_goal_alignment", "accepted_capability_refs"
    ) or []
    for reference in accepted_refs:
        target = by_id.get(reference)
        current_number = iteration_number(iteration)
        target_number = iteration_number(
            "" if target is None else target.metadata.get("iteration", "")
        )
        valid_prior_acceptance = (
            target is not None
            and target.metadata.get("kind") == "iteration-acceptance"
            and str(target.metadata.get("status", "")) in FINAL_ITERATION_STATUSES
            and current_number is not None
            and target_number is not None
            and target_number < current_number
        )
        if not valid_prior_acceptance:
            errors.append(
                f"{label}: accepted_capability_refs item must reference an earlier accepted iteration: {reference}"
            )

    new_refs = manifest_resolved_sequence_items(
        text, "product_goal_alignment", "new_capability_slice_refs"
    ) or []
    if require_execution_slice_sequence:
        errors.extend(
            validate_product_goal_execution_readiness(
                manifest,
                label,
                iteration,
                by_id,
                new_refs,
                verification,
            )
        )
    cross_cases = manifest_resolved_sequence_items(
        text, "product_goal_alignment", "cross_domain_cases"
    ) or []
    cases_by_new_ref: dict[str, list[str]] = {reference: [] for reference in new_refs}
    slice_gate_cases_by_ref: dict[str, list[str]] = {}
    bindings = alignment.get("cross_domain_bindings")
    if isinstance(bindings, dict):
        for binding in bindings.values():
            if not isinstance(binding, dict):
                continue
            case_id = binding.get("case_id")
            new_ref = binding.get("new_slice_ref")
            if (
                isinstance(case_id, str)
                and case_id in cross_cases
                and isinstance(new_ref, str)
                and new_ref in cases_by_new_ref
            ):
                cases_by_new_ref[new_ref].append(case_id)
    for reference in new_refs:
        target = by_id.get(reference)
        if (
            target is None
            or target.metadata.get("kind") != "development-slice"
            or str(target.metadata.get("iteration", "")) != iteration
        ):
            errors.append(
                f"{label}: new_capability_slice_refs item must reference a development slice in {iteration}: {reference}"
            )
            continue

        accepted_metadata = target.metadata.get(
            "product_goal_accepted_capability_refs", []
        )
        cross_metadata = target.metadata.get("product_goal_cross_domain_case_ids", [])
        slice_gate_metadata = target.metadata.get("product_goal_slice_gate_case_ids", [])
        if target.metadata.get("product_goal_gate") != "V-000":
            errors.append(f"{target.relative_path}: product_goal_gate must equal V-000")
        if not isinstance(accepted_metadata, list) or set(accepted_metadata) != set(
            accepted_refs
        ):
            errors.append(
                f"{target.relative_path}: product_goal_accepted_capability_refs must match the Manifest"
            )
        if not isinstance(cross_metadata, list) or set(cross_metadata) != set(
            cases_by_new_ref.get(reference, [])
        ):
            errors.append(
                f"{target.relative_path}: product_goal_cross_domain_case_ids must match the Manifest"
            )
        if not isinstance(slice_gate_metadata, list) or not slice_gate_metadata:
            errors.append(
                f"{target.relative_path}: product_goal_slice_gate_case_ids must be non-empty"
            )
            slice_gate_cases_by_ref[reference] = []
        else:
            slice_gate_cases_by_ref[reference] = [str(item) for item in slice_gate_metadata]
        dependencies = target.metadata.get("depends_on", [])
        if not isinstance(dependencies, list):
            dependencies = []
        for required_dependency in (f"{iteration}-PROPOSAL", *accepted_refs):
            if required_dependency not in dependencies:
                errors.append(
                    f"{target.relative_path}: cumulative product slice must depend on {required_dependency}"
                )

    blocking_case_ids = manifest_resolved_sequence_items(
        text, "product_goal_alignment", "blocking_case_ids"
    ) or []
    assigned_gate_cases = [
        case_id
        for reference in new_refs
        for case_id in slice_gate_cases_by_ref.get(reference, [])
    ]
    if (
        len(assigned_gate_cases) != len(set(assigned_gate_cases))
        or set(assigned_gate_cases) != set(blocking_case_ids)
    ):
        errors.append(
            f"{label}: Slice gate Case IDs must uniquely partition blocking_case_ids"
        )
    for reference in new_refs:
        target = by_id.get(reference)
        if target is None:
            continue
        owned = set(slice_gate_cases_by_ref.get(reference, []))
        required_owned = set(cases_by_new_ref.get(reference, []))
        web_case = target.metadata.get("product_goal_web_checkpoint_id")
        if isinstance(web_case, str):
            required_owned.add(web_case)
        if reference == alignment.get("live_ad_hoc_checkpoint_binding", {}).get(
            "new_slice_ref"
        ):
            ad_hoc_case = target.metadata.get(
                "product_goal_live_ad_hoc_checkpoint_id"
            )
            if isinstance(ad_hoc_case, str):
                required_owned.add(ad_hoc_case)
        if not required_owned.issubset(owned):
            errors.append(
                f"{target.relative_path}: Slice gate Cases must include its owned cross-domain, Web and ad-hoc Cases"
            )

    checkpoint_bindings: list[tuple[str, dict[str, object]]] = []
    for metadata_field, binding_field in (
        ("product_goal_web_checkpoint_id", "web_checkpoint_binding"),
        ("product_goal_live_ad_hoc_checkpoint_id", "live_ad_hoc_checkpoint_binding"),
    ):
        binding = alignment.get(binding_field)
        if isinstance(binding, dict):
            checkpoint_bindings.append((metadata_field, binding))
    additional_web_bindings = alignment.get("additional_web_checkpoint_bindings")
    if isinstance(additional_web_bindings, dict):
        checkpoint_bindings.extend(
            ("product_goal_web_checkpoint_id", binding)
            for binding in additional_web_bindings.values()
            if isinstance(binding, dict)
        )

    for metadata_field, binding in checkpoint_bindings:
        owner_ref = binding.get("new_slice_ref")
        owner = by_id.get(owner_ref) if isinstance(owner_ref, str) else None
        expected_case = binding.get("case_id")
        if owner is not None and owner.metadata.get(metadata_field) != expected_case:
            errors.append(
                f"{owner.relative_path}: {metadata_field} must match the owned Manifest binding"
            )

    if require_execution_slice_sequence:
        errors.extend(
            validate_product_goal_slice_sequence(
                new_refs,
                by_id,
                label,
                manifest=manifest,
                verification=verification,
                require_completed=require_completed_slice_sequence,
            )
        )

    for case_id in blocking_case_ids:
        errors.extend(validate_blocking_verification_case(verification, case_id))
    return errors


def validate_product_goal_slice_sequence(
    new_refs: list[str],
    by_id: dict[str, Document],
    label: str,
    *,
    manifest: dict[str, object] | None = None,
    verification: Document | None = None,
    require_completed: bool = False,
) -> list[str]:
    """Require a sequential execution state, or all completed at finalization."""

    errors: list[str] = []
    slices: list[Document] = []
    for reference in new_refs:
        target = by_id.get(reference)
        if target is None or target.metadata.get("kind") != "development-slice":
            continue
        slices.append(target)
    if len(slices) != len(new_refs):
        return errors

    statuses = [str(item.metadata.get("status", "")) for item in slices]
    development_slices: dict[str, object] = {}
    if manifest is not None:
        development = manifest.get("development")
        if isinstance(development, dict):
            raw_slices = development.get("slices")
            if isinstance(raw_slices, dict):
                development_slices = raw_slices
    alignment = manifest.get("product_goal_alignment") if manifest is not None else None
    early_canary_by_slice: dict[str, dict[str, object]] = {}
    if isinstance(alignment, dict):
        canary_bindings = alignment.get("early_hidden_canary_bindings")
        if isinstance(canary_bindings, dict):
            for binding in canary_bindings.values():
                if not isinstance(binding, dict):
                    continue
                new_slice_ref = binding.get("new_slice_ref")
                if isinstance(new_slice_ref, str):
                    early_canary_by_slice[new_slice_ref] = binding
    completed_result_refs = [
        manifest_slice.get("result")
        for target, status in zip(slices, statuses, strict=True)
        if status == "completed"
        and isinstance(
            (manifest_slice := development_slices.get(target.identifier)), dict
        )
        and isinstance(manifest_slice.get("result"), str)
    ]
    if len(completed_result_refs) != len(set(completed_result_refs)):
        errors.append(
            f"{label}: each completed Slice must bind a unique Slice Result"
        )
    active_indexes = [
        index for index, status in enumerate(statuses) if status in ACTIVE_SLICE_STATUSES
    ]
    if require_completed:
        if any(status != "completed" for status in statuses):
            errors.append(
                f"{label}: completed iteration requires every new capability slice to be completed"
            )
    elif len(active_indexes) != 1:
        errors.append(
            f"{label}: execution requires exactly one authorized/in-progress new capability slice"
        )
    else:
        active_index = active_indexes[0]
        if any(status != "completed" for status in statuses[:active_index]):
            errors.append(
                f"{label}: slices before the active slice must be completed in Manifest order"
            )
        if any(status != "proposed" for status in statuses[active_index + 1 :]):
            errors.append(
                f"{label}: slices after the active slice must remain proposed"
            )

    if manifest is not None:
        authorization = manifest.get("authorization")
        if not isinstance(authorization, dict):
            errors.append(f"{label}: authorization must be a mapping")
        else:
            expected_active_slice = (
                "none"
                if require_completed or len(active_indexes) != 1
                else slices[active_indexes[0]].identifier
            )
            if authorization.get("active_slice") != expected_active_slice:
                errors.append(
                    f"{label}: authorization.active_slice must equal the unique active Slice or none after completion"
                )
            readiness = by_id.get(
                f"{slices[0].metadata.get('iteration')}-READINESS"
            )
            if readiness is not None:
                for manifest_field, readiness_field in (
                    ("authorized_by", "authorized_by"),
                    ("authorized_at", "authorized_at"),
                    ("authorization_ref", "product_goal_alignment_review_ref"),
                ):
                    if authorization.get(manifest_field) != readiness.metadata.get(
                        readiness_field
                    ):
                        errors.append(
                            f"{label}: authorization.{manifest_field} must match the accepted Readiness"
                        )

    for index, target in enumerate(slices):
        status = statuses[index]
        authority = target.metadata.get("authority")
        coding_input = is_true(target.metadata.get("coding_input", ""))
        if status == "proposed" and (
            authority != "proposed-development" or coding_input
        ):
            errors.append(
                f"{target.relative_path}: proposed slice must use proposed-development with coding_input false"
            )
        elif status in ACTIVE_SLICE_STATUSES and (
            authority != "current-development" or not coding_input
        ):
            errors.append(
                f"{target.relative_path}: active slice must use current-development with coding_input true"
            )
        elif status == "completed" and (
            authority != "historical-development" or coding_input
        ):
            errors.append(
                f"{target.relative_path}: completed slice must use historical-development with coding_input false"
            )
        elif status not in {"proposed", "authorized", "in-progress", "completed"}:
            errors.append(
                f"{target.relative_path}: slice status is invalid for sequential development"
            )

        manifest_slice = development_slices.get(target.identifier)
        if isinstance(manifest_slice, dict) and status in {
            "authorized",
            "in-progress",
            "completed",
        }:
            if manifest_slice.get("authorized_by") != "user":
                errors.append(
                    f"{label}: {status} {target.identifier} authorized_by must equal user"
                )
            authorized_at = manifest_slice.get("authorized_at")
            if not isinstance(authorized_at, str) or re.fullmatch(
                r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:Z|[+-][0-9]{2}:[0-9]{2})",
                authorized_at,
            ) is None:
                errors.append(
                    f"{label}: {status} {target.identifier} authorized_at must be an ISO-8601 timestamp with timezone"
                )
            authorization_ref = manifest_slice.get("authorization_ref")
            if not isinstance(authorization_ref, str) or re.fullmatch(
                r"codex-user-message:sha256:[0-9a-f]{64}", authorization_ref
            ) is None:
                errors.append(
                    f"{label}: {status} {target.identifier} authorization_ref must bind an exact user message digest"
                )

        if manifest is not None and not isinstance(manifest_slice, dict):
            errors.append(
                f"{label}: development.slices must define {target.identifier}"
            )
        elif isinstance(manifest_slice, dict):
            if manifest_slice.get("status") != status:
                errors.append(
                    f"{label}: development.slices.{target.identifier}.status must match the Slice document"
                )
            manifest_coding_input = manifest_slice.get("coding_input")
            if isinstance(manifest_coding_input, bool):
                manifest_coding = manifest_coding_input
            else:
                manifest_coding = is_true(manifest_coding_input)
            if manifest_coding != coding_input:
                errors.append(
                    f"{label}: development.slices.{target.identifier}.coding_input must match the Slice document"
                )

            if status == "proposed":
                for field in ("result", "authorized_by", "authorized_at", "authorization_ref"):
                    if manifest_slice.get(field) != (
                        "not-executed" if field == "result" else "not-authorized"
                    ):
                        errors.append(
                            f"{label}: proposed {target.identifier} {field} must remain unresolved without fabricating authorization"
                        )
                if manifest_slice.get("product_code_freeze_digest") != "not-executed":
                    errors.append(
                        f"{label}: proposed {target.identifier} product_code_freeze_digest must be not-executed"
                    )
            elif status in ACTIVE_SLICE_STATUSES:
                result_ref = manifest_slice.get("result")
                if result_ref not in {"not-executed", "in-progress"}:
                    errors.append(
                        f"{label}: active {target.identifier} result must be not-executed or in-progress"
                    )
                freeze_digest = manifest_slice.get("product_code_freeze_digest")
                if freeze_digest != "not-executed" and (
                    not isinstance(freeze_digest, str)
                    or re.fullmatch(r"sha256:[0-9a-f]{64}", freeze_digest) is None
                ):
                    errors.append(
                        f"{label}: active {target.identifier} product_code_freeze_digest must be not-executed or an exact sha256 digest"
                    )
            elif status == "completed":
                result_ref = manifest_slice.get("result")
                result = by_id.get(result_ref) if isinstance(result_ref, str) else None
                dependencies: list[object] = []
                if result is not None and isinstance(
                    result.metadata.get("depends_on", []), list
                ):
                    dependencies = result.metadata.get("depends_on", [])  # type: ignore[assignment]
                if (
                    result is None
                    or result.metadata.get("kind") != "iteration-result"
                    or str(result.metadata.get("iteration", ""))
                    != str(target.metadata.get("iteration", ""))
                    or result.metadata.get("status") not in {"accepted", "completed"}
                    or result.metadata.get("authority") != "execution-evidence"
                    or target.identifier not in dependencies
                    or f"{target.metadata.get('iteration')}-VERIFICATION" not in dependencies
                ):
                    errors.append(
                        f"{label}: completed {target.identifier} must bind accepted execution evidence that depends on the Slice and Verification"
                    )
                else:
                    freeze_digest = manifest_slice.get("product_code_freeze_digest")
                    if not isinstance(freeze_digest, str) or re.fullmatch(
                        r"sha256:[0-9a-f]{64}", freeze_digest
                    ) is None:
                        errors.append(
                            f"{label}: completed {target.identifier} must bind an exact product_code_freeze_digest"
                        )
                    elif result.metadata.get("product_code_freeze_digest") != freeze_digest:
                        errors.append(
                            f"{label}: completed {target.identifier} Result must bind its exact product code freeze"
                        )

                    canary_binding = early_canary_by_slice.get(target.identifier)
                    if canary_binding is not None:
                        for result_field, binding_field in (
                            ("canary_project_manifest_digest", "project_manifest_digest"),
                            ("canary_suite_digest", "suite_digest"),
                        ):
                            if result.metadata.get(result_field) != canary_binding.get(
                                binding_field
                            ):
                                errors.append(
                                    f"{label}: completed {target.identifier} Result {result_field} must match its frozen canary"
                                )
                        exposure_receipt = result.metadata.get(
                            "canary_exposure_receipt_digest"
                        )
                        if not isinstance(exposure_receipt, str) or re.fullmatch(
                            r"sha256:[0-9a-f]{64}", exposure_receipt
                        ) is None:
                            errors.append(
                                f"{label}: completed {target.identifier} Result must bind an exact canary exposure receipt"
                            )
                        if result.metadata.get(
                            "canary_product_change_after_exposure_count"
                        ) != 0:
                            errors.append(
                                f"{label}: completed {target.identifier} canary product change count must equal zero"
                            )

                if result is not None and verification is not None:
                    case_ids = target.metadata.get("product_goal_slice_gate_case_ids", [])
                    if not isinstance(case_ids, list):
                        case_ids = []
                    for case_id in dict.fromkeys(case_ids):
                        errors.extend(
                            validate_blocking_verification_case(
                                verification,
                                str(case_id),
                                require_pass=True,
                                expected_evidence=f"{result.identifier}#{case_id}",
                            )
                        )

        if index > 0:
            dependencies = target.metadata.get("depends_on", [])
            if not isinstance(dependencies, list) or new_refs[index - 1] not in dependencies:
                errors.append(
                    f"{target.relative_path}: sequential slice must depend on {new_refs[index - 1]}"
                )
    return errors


def validate_product_goal_alignment_state(documents: list[Document]) -> list[str]:
    """Enforce the product-goal gate when an ITER-007+ proposal is selected."""

    errors: list[str] = []
    documents_by_path = {document.path: document for document in documents}
    documents_by_id = {document.identifier: document for document in documents}
    iteration_directories: dict[str, Path] = {}
    for document in documents:
        expected = iteration_from_document_path(document.path)
        if expected is not None:
            iteration_directories.setdefault(
                expected,
                REPOSITORY
                / "docs/project/iterations"
                / f"iteration-{expected.removeprefix('ITER-')}",
            )

    for iteration, directory in sorted(iteration_directories.items()):
        if not requires_product_goal_alignment(iteration):
            continue
        proposal = documents_by_path.get(directory / "proposal.md")
        readiness = documents_by_path.get(directory / "readiness-review.md")
        verification = documents_by_path.get(directory / "verification-matrix.md")
        index = documents_by_path.get(directory / "README.md")
        slice_candidates = [
            document
            for document in documents
            if document.path.parent == directory / "development-design"
            and document.path.name != "README.md"
        ]
        acceptances = [
            document
            for document in documents
            if document.path.parent == directory / "results"
            and document.metadata.get("kind") == "iteration-acceptance"
            and str(document.metadata.get("status", "")) in FINAL_ITERATION_STATUSES
        ]

        proposal_selected = proposal is not None and str(
            proposal.metadata.get("status", "")
        ) in GOAL_ALIGNED_PROPOSAL_STATUSES
        readiness_selected = readiness is not None and str(
            readiness.metadata.get("status", "")
        ) in GOAL_ALIGNED_READINESS_STATUSES
        iteration_selected = index is not None and str(
            index.metadata.get("status", "")
        ) in GOAL_ALIGNED_ITERATION_STATUSES
        selected_slices = [
            document
            for document in slice_candidates
            if str(document.metadata.get("status", ""))
            in GOAL_ALIGNED_SLICE_STATUSES
        ]
        selected = bool(
            proposal_selected
            or readiness_selected
            or iteration_selected
            or selected_slices
            or acceptances
        )
        if not selected:
            continue

        for required_document, expected_kind in (
            (proposal, "iteration-proposal"),
            (readiness, "iteration-readiness"),
            (verification, "iteration-verification"),
            (index, "iteration-index"),
        ):
            if (
                required_document is not None
                and required_document.metadata.get("kind") != expected_kind
            ):
                errors.append(
                    f"{required_document.relative_path}: expected kind {expected_kind}"
                )
        for slice_document in selected_slices:
            if slice_document.metadata.get("kind") != "development-slice":
                errors.append(
                    f"{slice_document.relative_path}: selected slice must have kind development-slice"
                )

        errors.extend(
            validate_product_goal_alignment_documents(
                proposal, verification, iteration
            )
        )
        if proposal is not None:
            if not proposal_selected:
                errors.append(
                    f"{proposal.relative_path}: selected iteration proposal must be accepted/authorized/completed"
                )
            errors.extend(validate_goal_aligned_required_document(proposal))

        requires_readiness = bool(
            readiness_selected or iteration_selected or selected_slices or acceptances
        )
        if requires_readiness:
            if readiness is None:
                errors.append(f"{iteration}: selected iteration is missing readiness-review.md")
            else:
                if not readiness_selected:
                    errors.append(
                        f"{readiness.relative_path}: selected iteration readiness must be accepted/authorized/completed"
                    )
                errors.extend(validate_goal_aligned_required_document(readiness))
                errors.extend(
                    validate_product_goal_readiness_authorization(readiness)
                )
            if verification is not None:
                errors.extend(validate_goal_aligned_required_document(verification))

        if index is not None and iteration_selected:
            errors.extend(validate_goal_aligned_required_document(index))
        for slice_document in selected_slices:
            errors.extend(validate_goal_aligned_required_document(slice_document))

        manifest = directory / "manifest.yaml"
        if not manifest.exists():
            errors.append(f"{iteration}: selected iteration is missing manifest.yaml")
        else:
            allowed_statuses = (
                GOAL_ALIGNED_ITERATION_STATUSES
                if requires_readiness
                else GOAL_ALIGNED_ITERATION_STATUSES | {"proposed"}
            )
            errors.extend(
                validate_active_manifest(
                    manifest, iteration, allowed_statuses=allowed_statuses
                )
            )
            errors.extend(
                validate_product_goal_reference_targets(
                    manifest,
                    iteration,
                    documents_by_id,
                    require_execution_slice_sequence=requires_readiness,
                    require_completed_slice_sequence=bool(
                        acceptances
                        or (
                            index is not None
                            and str(index.metadata.get("status", ""))
                            in FINAL_ITERATION_STATUSES
                        )
                    ),
                    verification=verification,
                )
            )
            if requires_readiness:
                try:
                    manifest_text = manifest.read_text(encoding="utf-8")
                except (OSError, UnicodeError):
                    manifest_text = ""
                for reference in manifest_resolved_sequence_items(
                    manifest_text,
                    "product_goal_alignment",
                    "new_capability_slice_refs",
                ) or []:
                    target = documents_by_id.get(reference)
                    if (
                        target is not None
                        and target.metadata.get("kind") == "development-slice"
                        and str(target.metadata.get("iteration", "")) == iteration
                    ):
                        errors.extend(validate_goal_aligned_required_document(target))
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


def validate_completed_acceptance(
    document: Document,
    verification: Document | None = None,
    by_id: dict[str, Document] | None = None,
) -> list[str]:
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
    required_sections = COMPLETED_ACCEPTANCE_SECTIONS
    if requires_product_goal_alignment(document.metadata.get("iteration", "")):
        required_sections += PRODUCT_GOAL_ALIGNMENT_ACCEPTANCE_SECTIONS
        product_goal_body = markdown_section_body(
            document, "Product-goal delta and cumulative evidence"
        )
        if product_goal_body is not None and any(
            placeholder in product_goal_body
            for placeholder in PRODUCT_GOAL_ACCEPTANCE_PLACEHOLDERS
        ):
            errors.append(
                f"{document.relative_path}: completed acceptance contains unresolved product-goal placeholders"
            )
        errors.extend(
            validate_product_goal_v000(
                verification,
                str(document.metadata.get("iteration", "")),
                require_pass=True,
                by_id=by_id,
            )
        )
        if verification is not None and by_id is not None:
            result_id = verification.metadata.get("product_goal_result_id")
            result = by_id.get(result_id) if isinstance(result_id, str) else None
            if result is not None and document.metadata.get(
                "subject_identity"
            ) != result.metadata.get("product_goal_subject_digest"):
                errors.append(
                    f"{document.relative_path}: acceptance subject_identity must equal the product Result subject digest"
                )
            try:
                manifest = safe_load_manifest(
                    (verification.path.parent / "manifest.yaml").read_text(
                        encoding="utf-8"
                    )
                )
            except (OSError, UnicodeError, SafeYamlError):
                manifest = {}
            baseline = manifest.get("baseline")
            if isinstance(baseline, dict) and document.metadata.get(
                "baseline_commit"
            ) != baseline.get("commit"):
                errors.append(
                    f"{document.relative_path}: acceptance baseline_commit must equal the product-goal Manifest baseline"
                )
    for section in empty_required_sections(document, required_sections):
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
        errors.extend(validate_iteration_document_identity(document))
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

    errors.extend(validate_product_goal_alignment_state(documents))

    for path in PLAIN_LINK_FILES:
        if not path.exists():
            errors.append(f"missing navigation document: {path.relative_to(REPOSITORY)}")
        else:
            errors.extend(validate_markdown_links(path, path.read_text(encoding="utf-8")))

    open_findings: dict[str, list[str]] = {}
    accepted_iterations: set[str] = set()
    iteration_indexes: dict[str, Document] = {}
    acceptance_by_iteration: dict[str, list[Document]] = {}
    verification_by_iteration: dict[str, Document] = {}
    for document in documents:
        kind = document.metadata.get("kind")
        status = str(document.metadata.get("status", ""))
        iteration = str(document.metadata.get("iteration", ""))
        expected_iteration = iteration_from_document_path(document.path)
        iteration_key = expected_iteration or iteration
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
            accepted_iterations.add(iteration_key)
        if kind == "iteration-acceptance" and iteration:
            acceptance_by_iteration.setdefault(iteration_key, []).append(document)
        if kind == "iteration-verification" and iteration_key:
            if iteration_key in verification_by_iteration:
                errors.append(
                    f"{document.relative_path}: duplicate verification matrix for {iteration_key}"
                )
            else:
                verification_by_iteration[iteration_key] = document

    for iteration, acceptances in acceptance_by_iteration.items():
        for acceptance in acceptances:
            if str(acceptance.metadata.get("status", "")) in FINAL_ITERATION_STATUSES:
                errors.extend(
                    validate_completed_acceptance(
                        acceptance,
                        verification_by_iteration.get(iteration),
                        by_id,
                    )
                )

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
                elif iteration_number(iteration) is None:
                    errors.append(
                        "PROJECT-CURRENT: active iteration must match ITER followed by at least three digits"
                    )
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

                if requires_product_goal_alignment(iteration):
                    verification = documents_by_path.get(
                        iteration_directory / "verification-matrix.md"
                    )
                    errors.extend(
                        validate_product_goal_alignment_documents(
                            proposal, verification, iteration
                        )
                    )
                    manifest_path = iteration_directory / "manifest.yaml"
                    try:
                        manifest_text = manifest_path.read_text(encoding="utf-8")
                    except (OSError, UnicodeError):
                        manifest_text = ""
                    manifest_slice_refs = manifest_resolved_sequence_items(
                        manifest_text,
                        "product_goal_alignment",
                        "new_capability_slice_refs",
                    ) or []
                    active_product_slices = [
                        document
                        for reference in manifest_slice_refs
                        if (document := by_id.get(reference)) is not None
                        and str(document.metadata.get("status", ""))
                        in ACTIVE_SLICE_STATUSES
                    ]
                    if (
                        len(active_product_slices) != 1
                        or active_product_slices[0].identifier != active_slice
                    ):
                        errors.append(
                            "PROJECT-CURRENT: active_slice must equal the unique active "
                            "product-goal Slice in Manifest order"
                        )

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
