#!/usr/bin/env python3
"""Validate current documentation and generate agent-oriented indexes."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path, PurePosixPath
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
REFLECTION_GATE_START_ITERATION = 8
DIRECTION_PREVIEW_START_ITERATION = 9
ENGINEERING_QA_HYBRID_START_ITERATION = 10
DIRECTION_PREVIEW_PRODUCT_ENTRIES = frozenset(
    {
        "loopback-product-owned-world-model-web",
        "loopback-product-owned-engineering-qa-web",
    }
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
PRODUCT_GOAL_ALIGNMENT_SECTIONS = {
    "iteration-proposal": ("Product-goal alignment and cumulative delta",),
    "iteration-readiness": ("Product-goal alignment gate",),
    "development-slice": (
        "Product-goal contribution and cumulative integration",
    ),
}
REFLECTION_GATE_REQUIRED_SECTIONS = {
    "iteration-proposal": ("Critical assumptions and falsification plan",),
    "iteration-readiness": ("Architecture reflection gate readiness",),
    "development-slice": ("Architecture reflection checkpoint",),
}
REFLECTION_RESULT_REQUIRED_SUBSECTIONS = (
    "Assumption verdicts",
    "Deviation and issue classification",
    "Layer diagnosis and mature-source-Agent comparison",
    "Findings, alternatives and next risk",
    "Decision and rationale",
)
REFLECTION_ISSUE_CLASSES = {
    "architecture",
    "implementation",
    "configuration-environment",
    "requirement-usage",
    "verification-design",
    "none",
}
REFLECTION_ISSUE_SCOPES = {"individual", "systemic", "none"}
REFLECTION_ASSUMPTION_VERDICTS = {"SUPPORTED", "FALSIFIED", "UNRESOLVED"}
PRODUCT_GOAL_ALIGNMENT_MANIFEST_SCALARS = (
    "capability_path_ref",
    "capability_path_step",
    "end_of_iteration_web_capability",
    "next_blocking_gap",
    "baseline_gap",
    "held_out_free_question_delta",
    "held_out_evaluation_owner",
    "implementation_question_visibility",
    "first_product_web_checkpoint",
    "live_ad_hoc_question_checkpoint",
)
PRODUCT_GOAL_ALIGNMENT_MANIFEST_SEQUENCES = (
    "predecessor_result_refs",
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
USER_HELD_LIVE_EVALUATION_MODE = "user-held-live-after-product-code-freeze"
USER_HELD_LIVE_UNDISCLOSED = "user-held-not-disclosed"
USER_HELD_LIVE_UNMEASURED = "measured-after-product-code-freeze"
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
    "rejected",
}
GOAL_ALIGNED_SLICE_STATUSES = {
    "authorized",
    "in-progress",
    "completed",
    "blocked",
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
ENGINEERING_QA_PRODUCT_GOAL_V000_CLAIM = (
    "本轮相对 rejected baseline 可测缩短通用工程问答差距并累计复用既有 World Model 能力"
)
ENGINEERING_QA_PRODUCT_GOAL_V000_FROZEN_INPUT = (
    "三个唯一 Slice Result；最终隐藏 10+2；现场题；成熟源码 Agent；预提交 reuse-value protocol"
)
ENGINEERING_QA_PRODUCT_GOAL_V000_EXPECTED = (
    "重大错误 0；逐结论不退步；价值阈值 PASS；同一 Web 直接回答、层级匹配、Citation 正确；"
    "Source 只在 retrieval worker"
)
ENGINEERING_QA_PRODUCT_GOAL_V000_METADATA = {
    "product_goal_gate": "V-000",
    "product_goal_outcome": "user-visible-general-engineering-qa-delta",
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


def markdown_subsection_body(text: str, name: str) -> str | None:
    lines: list[str] = []
    active = False
    for line in text.splitlines():
        heading = re.match(r"^#{1,3}\s+(.+?)\s*$", line)
        if heading:
            level = len(line) - len(line.lstrip("#"))
            heading_name = heading.group(1).rstrip("#").strip()
            if active and level <= 3:
                break
            if level == 3:
                active = heading_name == name
            continue
        if active:
            lines.append(line)
    return "\n".join(lines) if active else None


def has_substantive_markdown_content(text: str | None) -> bool:
    if text is None:
        return False
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if re.fullmatch(r"\|?(?:\s*:?-+:?\s*\|)+", stripped):
            continue
        return True
    return False


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


def requires_reflection_gate(identifier: object) -> bool:
    number = iteration_number(identifier)
    return number is not None and number >= REFLECTION_GATE_START_ITERATION


def requires_direction_preview(identifier: object) -> bool:
    number = iteration_number(identifier)
    return number is not None and number >= DIRECTION_PREVIEW_START_ITERATION


def supports_engineering_qa_hybrid(identifier: object) -> bool:
    number = iteration_number(identifier)
    return number is not None and number >= ENGINEERING_QA_HYBRID_START_ITERATION


def requires_engineering_qa_hybrid(identifier: object) -> bool:
    """Bind the accepted ITER-010 plan without constraining later iterations."""

    return iteration_number(identifier) == ENGINEERING_QA_HYBRID_START_ITERATION


def product_goal_v000_contract(
    iteration: object,
) -> tuple[dict[str, str], str, str, str]:
    """Return the exact user-visible product gate for the selected architecture."""

    if requires_engineering_qa_hybrid(iteration):
        return (
            ENGINEERING_QA_PRODUCT_GOAL_V000_METADATA,
            ENGINEERING_QA_PRODUCT_GOAL_V000_CLAIM,
            ENGINEERING_QA_PRODUCT_GOAL_V000_FROZEN_INPUT,
            ENGINEERING_QA_PRODUCT_GOAL_V000_EXPECTED,
        )
    return (
        PRODUCT_GOAL_V000_METADATA,
        PRODUCT_GOAL_V000_CLAIM,
        PRODUCT_GOAL_V000_FROZEN_INPUT,
        PRODUCT_GOAL_V000_EXPECTED,
    )


def active_required_sections(document: Document) -> tuple[str, ...]:
    kind = str(document.metadata.get("kind", ""))
    required = ACTIVE_REQUIRED_SECTIONS.get(kind, ())
    if requires_product_goal_alignment(document.metadata.get("iteration", "")):
        required += PRODUCT_GOAL_ALIGNMENT_SECTIONS.get(kind, ())
    if requires_reflection_gate(document.metadata.get("iteration", "")):
        required += REFLECTION_GATE_REQUIRED_SECTIONS.get(kind, ())
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


def reflection_gate_bindings_by_slice(
    alignment: dict[str, object],
) -> dict[str, dict[str, object]]:
    bindings = alignment.get("reflection_gate_bindings")
    if not isinstance(bindings, dict):
        return {}
    by_slice: dict[str, dict[str, object]] = {}
    for binding in bindings.values():
        if not isinstance(binding, dict):
            continue
        new_slice_ref = binding.get("new_slice_ref")
        if isinstance(new_slice_ref, str) and new_slice_ref not in by_slice:
            by_slice[new_slice_ref] = binding
    return by_slice


def critical_assumption_catalog(
    proposal: Document | None,
) -> tuple[str | None, dict[str, str], list[str]]:
    """Bind exact assumption statements to the proposal section that owns them."""

    if proposal is None:
        return None, {}, ["missing Proposal for critical assumption catalog"]
    heading_count = len(
        re.findall(
            r"(?m)^[ ]{0,3}##[ \t]+Critical assumptions and falsification plan[ \t]*#*[ \t]*$",
            proposal.body,
        )
    )
    if heading_count != 1:
        return None, {}, [
            f"{proposal.relative_path}: must contain exactly one Critical assumptions and falsification plan section"
        ]
    section = markdown_section_body(
        proposal, "Critical assumptions and falsification plan"
    )
    if not has_substantive_markdown_content(section):
        return None, {}, [
            f"{proposal.relative_path}: critical assumption catalog section is missing or empty"
        ]
    expectations: dict[str, str] = {}
    errors: list[str] = []
    for line in section.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or not stripped.endswith("|"):
            continue
        cells = [cell.strip() for cell in re.split(r"(?<!\\)\|", stripped[1:-1])]
        if not cells:
            continue
        match = re.fullmatch(r"(A[1-9][0-9]*)[：:]\s*(.+)", cells[0])
        if match is None:
            if re.match(r"A[0-9]+(?=[\s：:]|$)", cells[0]):
                errors.append(
                    f"{proposal.relative_path}: malformed critical assumption row: {cells[0]}"
                )
            continue
        assumption_id, statement = match.groups()
        if assumption_id in expectations:
            errors.append(
                f"{proposal.relative_path}: duplicate critical assumption {assumption_id}"
            )
        elif len(cells) != 3 or any(
            not value.strip()
            or is_pending(value)
            or is_absent_evidence(value)
            or has_unresolved_placeholder(value)
            for value in (statement, *cells[1:])
        ):
            errors.append(
                f"{proposal.relative_path}: {assumption_id} must use the exact resolved three-column assumption schema"
            )
        else:
            expectations[assumption_id] = statement.strip()
    if not expectations:
        errors.append(
            f"{proposal.relative_path}: critical assumption catalog must contain A-number rows"
        )
    digest = "sha256:" + hashlib.sha256(section.encode("utf-8")).hexdigest()
    return digest, expectations, errors


def validate_planned_assumption_catalog(
    proposal: Document | None,
    manifest: dict[str, object],
    label: str,
) -> list[str]:
    """Reject malformed or drifting assumptions while an iteration is still proposed."""

    digest, expectations, errors = critical_assumption_catalog(proposal)
    alignment = manifest.get("product_goal_alignment")
    if not isinstance(alignment, dict):
        return errors
    critical_assumption_ids = resolved_assumption_ids(
        alignment.get("critical_assumption_ids")
    )
    if critical_assumption_ids != list(expectations):
        errors.append(
            f"{label}: critical_assumption_ids must exactly match the Proposal assumption catalog order"
        )
    supplied_digest = alignment.get("critical_assumption_catalog_digest")
    if supplied_digest != "not-frozen-proposal-only" and supplied_digest != digest:
        errors.append(
            f"{label}: proposed critical_assumption_catalog_digest must match the exact Proposal catalog or remain the proposal-only marker"
        )
    return errors


def resolved_direction_preview_slice_ref(
    alignment: dict[str, object], new_refs: list[str]
) -> str | None:
    """Resolve only a fully formed first-Slice direction preview binding."""

    binding = alignment.get("direction_preview_binding")
    if not isinstance(binding, dict) or len(new_refs) < 2:
        return None
    case_id = binding.get("case_id")
    new_slice_ref = binding.get("new_slice_ref")
    representative_task_count = binding.get("representative_task_count")
    decision_owner = binding.get("decision_owner")
    if (
        not isinstance(case_id, str)
        or re.fullmatch(r"V-PREVIEW-[0-9]{3,}", case_id) is None
        or alignment.get("direction_preview_checkpoint") != case_id
        or new_slice_ref != new_refs[0]
        or binding.get("real_product_entry")
        not in DIRECTION_PREVIEW_PRODUCT_ENTRIES
        or isinstance(representative_task_count, bool)
        or not isinstance(representative_task_count, int)
        or representative_task_count < 1
        or binding.get("status_label") != "non-acceptance-non-production"
        or decision_owner != "user"
        or binding.get("allowed_decisions") != "CONTINUE,REDIRECT,REJECT"
        or binding.get("hardening_requires_continue") is not True
    ):
        return None
    return str(new_slice_ref)


def validate_direction_preview_binding(
    alignment: dict[str, object],
    new_refs: list[str],
    blocking_case_ids: list[str],
    label: str,
) -> list[str]:
    """Require an auditable, non-acceptance preview before hardening."""

    errors: list[str] = []
    binding = alignment.get("direction_preview_binding")
    if not isinstance(binding, dict):
        return [f"{label}: direction_preview_binding must be a mapping"]
    if len(new_refs) < 2:
        errors.append(
            f"{label}: direction preview requires a later hardening or final Slice"
        )
    case_id = binding.get("case_id")
    if (
        not isinstance(case_id, str)
        or re.fullmatch(r"V-PREVIEW-[0-9]{3,}", case_id) is None
    ):
        errors.append(
            f"{label}: direction_preview_binding.case_id must match V-PREVIEW-NNN"
        )
    else:
        if alignment.get("direction_preview_checkpoint") != case_id:
            errors.append(
                f"{label}: direction_preview_checkpoint must match direction_preview_binding.case_id"
            )
        if case_id not in blocking_case_ids:
            errors.append(f"{label}: direction preview Case must be blocking")
    new_slice_ref = binding.get("new_slice_ref")
    if not new_refs or new_slice_ref != new_refs[0]:
        errors.append(
            f"{label}: direction_preview_binding.new_slice_ref must equal the first new capability Slice"
        )
    real_product_entry = binding.get("real_product_entry")
    if real_product_entry not in DIRECTION_PREVIEW_PRODUCT_ENTRIES:
        errors.append(
            f"{label}: direction_preview_binding.real_product_entry must equal "
            "loopback-product-owned-world-model-web or "
            "loopback-product-owned-engineering-qa-web"
        )
    representative_task_count = binding.get("representative_task_count")
    if (
        isinstance(representative_task_count, bool)
        or not isinstance(representative_task_count, int)
        or representative_task_count < 1
    ):
        errors.append(
            f"{label}: direction preview representative_task_count must be positive"
        )
    if binding.get("status_label") != "non-acceptance-non-production":
        errors.append(
            f"{label}: direction preview status_label must equal non-acceptance-non-production"
        )
    decision_owner = binding.get("decision_owner")
    if decision_owner != "user":
        errors.append(
            f"{label}: direction preview decision_owner must equal user"
        )
    if binding.get("allowed_decisions") != "CONTINUE,REDIRECT,REJECT":
        errors.append(
            f"{label}: direction preview allowed_decisions must equal CONTINUE,REDIRECT,REJECT"
        )
    if binding.get("hardening_requires_continue") is not True:
        errors.append(
            f"{label}: direction preview must require CONTINUE before hardening"
        )
    return errors


def validate_direction_preview_answer_entry(
    alignment: dict[str, object],
    answer_protocol: dict[str, object],
    label: str,
) -> list[str]:
    """Keep the visible product identity aligned with the selected answer mode."""

    binding = alignment.get("direction_preview_binding")
    if not isinstance(binding, dict):
        return []
    expected = (
        "loopback-product-owned-engineering-qa-web"
        if answer_protocol.get("mode")
        == "upfront-engineering-qa-hybrid-evidence"
        else "loopback-product-owned-world-model-web"
    )
    if binding.get("real_product_entry") != expected:
        return [
            f"{label}: direction preview product entry must match answer_protocol.mode as {expected}"
        ]
    return []


def required_early_evaluation_slice_refs(
    alignment: dict[str, object],
    new_refs: list[str],
    *,
    direction_preview_enabled: bool = False,
) -> set[str]:
    """Place early hardening gates after, never on, a direction preview."""

    if not direction_preview_enabled:
        return set(new_refs[:-1])
    preview_ref = resolved_direction_preview_slice_ref(alignment, new_refs)
    if preview_ref is None:
        return set(new_refs[:-1])
    post_preview_refs = new_refs[1:]
    if len(post_preview_refs) == 1:
        # A combined hardening/final Slice still owns the deferred early gates.
        return set(post_preview_refs)
    return set(post_preview_refs[:-1])


def direction_preview_hardening_is_deferred(
    manifest: dict[str, object],
    alignment: dict[str, object],
    new_refs: list[str],
    *,
    direction_preview_enabled: bool = False,
) -> bool:
    """Return whether the explicit preview Slice has not completed yet."""

    if not direction_preview_enabled:
        return False
    preview_ref = resolved_direction_preview_slice_ref(alignment, new_refs)
    if preview_ref is None:
        return False
    development = manifest.get("development")
    slices = development.get("slices") if isinstance(development, dict) else None
    preview = slices.get(preview_ref) if isinstance(slices, dict) else None
    preview_status = preview.get("status") if isinstance(preview, dict) else None
    return preview_status in {"proposed", "authorized", "in-progress", "blocked"}


def validate_early_evaluation_bindings(
    alignment: dict[str, object],
    new_refs: list[str],
    blocking_case_ids: list[str],
    label: str,
    *,
    defer_until_post_preview: bool = False,
    direction_preview_enabled: bool = False,
) -> list[str]:
    """Freeze the first real falsification checkpoint before coding starts."""

    errors: list[str] = []
    expected_refs = required_early_evaluation_slice_refs(
        alignment,
        new_refs,
        direction_preview_enabled=direction_preview_enabled,
    )
    if not expected_refs:
        return errors
    preview_ref = (
        resolved_direction_preview_slice_ref(alignment, new_refs)
        if direction_preview_enabled
        else None
    )
    if defer_until_post_preview and preview_ref is not None:
        preview_owned_fields: list[str] = []
        canary_bindings = alignment.get("early_hidden_canary_bindings")
        if isinstance(canary_bindings, dict):
            for binding_name, binding in canary_bindings.items():
                if isinstance(binding, dict) and binding.get("new_slice_ref") == preview_ref:
                    preview_owned_fields.append(
                        f"early_hidden_canary_bindings.{binding_name}"
                    )
        for field in ("early_comparison_binding", "early_diagnostic_binding"):
            binding = alignment.get(field)
            if isinstance(binding, dict) and binding.get("new_slice_ref") == preview_ref:
                preview_owned_fields.append(field)
        if preview_owned_fields:
            errors.append(
                f"{label}: direction preview Slice must not own deferred early hidden canary, comparison or diagnostic Gates: "
                + ", ".join(preview_owned_fields)
            )
        if not any(
            field in alignment
            for field in (
                "early_hidden_canary_bindings",
                "early_comparison_binding",
                "early_diagnostic_binding",
            )
        ):
            return errors
    user_held_live = (
        alignment.get("evaluation_input_mode") == USER_HELD_LIVE_EVALUATION_MODE
    )
    bindings = alignment.get("early_hidden_canary_bindings")
    if not isinstance(bindings, dict) or not bindings:
        errors.append(
            f"{label}: early_hidden_canary_bindings must cover every pre-final Slice"
        )
        return errors

    canary_by_case: dict[str, tuple[str, dict[str, object]]] = {}
    seen_refs: list[str] = []
    for binding_name, binding in bindings.items():
        if not isinstance(binding, dict):
            errors.append(
                f"{label}: early_hidden_canary_bindings.{binding_name} must be a mapping"
            )
            continue
        new_ref = binding.get("new_slice_ref")
        case_id = binding.get("case_id")
        if not isinstance(new_ref, str) or new_ref not in expected_refs:
            errors.append(
                f"{label}: early hidden canary must bind a pre-final Slice"
            )
        else:
            seen_refs.append(new_ref)
        if (
            not isinstance(case_id, str)
            or re.fullmatch(r"V-CANARY-[0-9]{3,}", case_id) is None
        ):
            errors.append(
                f"{label}: early hidden canary case_id must match V-CANARY-NNN"
            )
        elif case_id in canary_by_case:
            errors.append(f"{label}: early hidden canary Case IDs must be unique")
        else:
            if case_id not in blocking_case_ids:
                errors.append(f"{label}: early hidden canary Case must be blocking")
            if isinstance(new_ref, str):
                canary_by_case[case_id] = (new_ref, binding)
        if binding.get("evaluation_owner") not in {"independent-evaluator", "user"}:
            errors.append(
                f"{label}: early hidden canary must have an independent evaluation owner"
            )
        if binding.get("implementation_visibility") != "hidden-until-slice-code-freeze":
            errors.append(
                f"{label}: early hidden canary must remain hidden until Slice code freeze"
            )
        if binding.get("burn_rule") != (
            "product-change-between-disclosure-and-slice-result-seal-"
            "burns-canary-and-preserves-result"
        ):
            errors.append(
                f"{label}: early hidden canary must freeze the disclosure-to-Result-seal burn rule"
            )
        for field in ("project_manifest_digest", "suite_digest"):
            value = binding.get(field)
            if not (
                user_held_live and value == USER_HELD_LIVE_UNDISCLOSED
            ) and (
                not isinstance(value, str)
                or re.fullmatch(r"sha256:[0-9a-f]{64}", value) is None
            ):
                errors.append(
                    f"{label}: early hidden canary {field} must be an exact sha256 digest or the closed user-held undisclosed marker"
                )

        count_fields = {
            "question_count": 3,
            "answerable_question_count": 1,
            "boundary_question_count": 2,
            "bounded_absence_question_count": 1,
            "coverage_limitation_question_count": 1,
        }
        for field, minimum in count_fields.items():
            value = binding.get(field)
            if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
                errors.append(
                    f"{label}: early hidden canary {field} must be at least {minimum}"
                )
        question_count = binding.get("question_count")
        answerable_count = binding.get("answerable_question_count")
        boundary_count = binding.get("boundary_question_count")
        if (
            isinstance(question_count, int)
            and not isinstance(question_count, bool)
            and isinstance(answerable_count, int)
            and not isinstance(answerable_count, bool)
            and isinstance(boundary_count, int)
            and not isinstance(boundary_count, bool)
            and question_count != answerable_count + boundary_count
        ):
            errors.append(
                f"{label}: early hidden canary question_count must equal answerable plus boundary counts"
            )
        negative_case_id = binding.get("negative_case_id")
        if (
            not isinstance(negative_case_id, str)
            or re.fullmatch(r"V-NEG-EARLY-[0-9]{3,}", negative_case_id) is None
            or negative_case_id not in blocking_case_ids
        ):
            errors.append(
                f"{label}: early hidden canary negative_case_id must be a blocking V-NEG-EARLY-NNN Case"
            )

    if set(seen_refs) != expected_refs or len(seen_refs) != len(set(seen_refs)):
        errors.append(
            f"{label}: early hidden canaries must bind each pre-final Slice exactly once"
        )

    comparison = alignment.get("early_comparison_binding")
    comparison_ref: str | None = None
    comparison_canary: str | None = None
    if not isinstance(comparison, dict):
        errors.append(f"{label}: early_comparison_binding must be a mapping")
    else:
        comparison_case = comparison.get("case_id")
        comparison_canary_value = comparison.get("canary_case_id")
        comparison_ref_value = comparison.get("new_slice_ref")
        if (
            not isinstance(comparison_case, str)
            or re.fullmatch(r"V-COMP-EARLY-[0-9]{3,}", comparison_case) is None
            or comparison_case not in blocking_case_ids
        ):
            errors.append(
                f"{label}: early comparison case_id must be a blocking V-COMP-EARLY-NNN Case"
            )
        if (
            not isinstance(comparison_canary_value, str)
            or comparison_canary_value not in canary_by_case
        ):
            errors.append(
                f"{label}: early comparison must reference a frozen early canary"
            )
        else:
            comparison_canary = comparison_canary_value
        if not isinstance(comparison_ref_value, str) or comparison_ref_value not in expected_refs:
            errors.append(
                f"{label}: early comparison must bind a pre-final Slice"
            )
        else:
            comparison_ref = comparison_ref_value
        if (
            comparison_canary is not None
            and comparison_ref is not None
            and canary_by_case[comparison_canary][0] != comparison_ref
        ):
            errors.append(
                f"{label}: early comparison and canary must bind the same Slice"
            )
        if comparison.get("protocol_digest_ref") != "mature_source_agent_protocol_digest":
            errors.append(
                f"{label}: early comparison protocol_digest_ref must equal mature_source_agent_protocol_digest"
            )
        if comparison.get("quality_rule") != "zero-major-error-and-no-need-claim-regression":
            errors.append(f"{label}: early comparison quality_rule is invalid")
        if comparison.get("positive_value_rule") != "precommitted-measurable-world-model-advantage-must-pass":
            errors.append(f"{label}: early comparison positive_value_rule is invalid")
        for reference_field, target_field in (
            ("positive_value_metric_ref", "positive_value_metric"),
            ("positive_value_unit_ref", "positive_value_unit"),
            ("positive_value_comparison_ref", "positive_value_comparison"),
            ("positive_value_threshold_ref", "positive_value_threshold"),
            (
                "positive_value_reuse_horizon_ref",
                "positive_value_reuse_horizon_questions",
            ),
            (
                "baseline_cache_policy_digest_ref",
                "mature_source_agent_cache_policy_digest",
            ),
            (
                "positive_value_protocol_digest_ref",
                "positive_value_protocol_digest",
            ),
            (
                "positive_value_adjudication_owner_ref",
                "positive_value_adjudication_owner",
            ),
        ):
            if comparison.get(reference_field) != target_field:
                errors.append(
                    f"{label}: early comparison {reference_field} must equal {target_field}"
                )
            if target_field not in alignment:
                errors.append(
                    f"{label}: early comparison referenced field is missing: {target_field}"
                )

    diagnostic = alignment.get("early_diagnostic_binding")
    if not isinstance(diagnostic, dict):
        errors.append(f"{label}: early_diagnostic_binding must be a mapping")
    else:
        diagnostic_case = diagnostic.get("case_id")
        diagnostic_ref = diagnostic.get("new_slice_ref")
        diagnostic_canary = diagnostic.get("canary_case_id")
        if (
            not isinstance(diagnostic_case, str)
            or re.fullmatch(r"V-DIAG-[0-9]{3,}", diagnostic_case) is None
            or diagnostic_case not in blocking_case_ids
        ):
            errors.append(
                f"{label}: early diagnostic case_id must be a blocking V-DIAG-NNN Case"
            )
        if diagnostic_canary != comparison_canary:
            errors.append(
                f"{label}: early diagnostic must reference the same canary as the comparison"
            )
        if diagnostic_ref != comparison_ref:
            errors.append(
                f"{label}: early diagnostic, comparison and canary must bind the same Slice"
            )
        if diagnostic.get("layer_chain") != "source-snapshot-query-trace-draft-review-web":
            errors.append(f"{label}: early diagnostic layer_chain is invalid")
    return errors


def resolved_assumption_ids(value: object) -> list[str]:
    if isinstance(value, str):
        values = [item.strip() for item in value.split(",")]
    elif isinstance(value, list):
        values = [str(item).strip() for item in value]
    else:
        return []
    if (
        not values
        or any(re.fullmatch(r"A[1-9][0-9]*", item) is None for item in values)
        or len(values) != len(set(values))
    ):
        return []
    return values


def validate_reflection_gate_bindings(
    alignment: dict[str, object],
    new_refs: list[str],
    blocking_case_ids: list[str],
    label: str,
) -> list[str]:
    """Require one auditable reflection gate for every ITER-008+ Slice."""

    errors: list[str] = []
    bindings = alignment.get("reflection_gate_bindings")
    if not isinstance(bindings, dict) or not bindings:
        return [f"{label}: reflection_gate_bindings must be a non-empty mapping"]

    critical_assumption_ids = resolved_assumption_ids(
        alignment.get("critical_assumption_ids")
    )
    if not critical_assumption_ids:
        errors.append(
            f"{label}: critical_assumption_ids must be a non-empty unique list of A-number IDs"
        )
        critical_assumption_ids = []

    seen_cases: set[str] = set()
    seen_slices: set[str] = set()
    assumptions_by_slice: dict[str, list[str]] = {}
    expected_success_decisions = {
        reference: "ACCEPT" if index == len(new_refs) - 1 else "CONTINUE"
        for index, reference in enumerate(new_refs)
    }
    for binding_name, binding in bindings.items():
        if not isinstance(binding, dict):
            errors.append(
                f"{label}: reflection_gate_bindings.{binding_name} must be a mapping"
            )
            continue
        case_id = binding.get("case_id")
        new_slice_ref = binding.get("new_slice_ref")
        success_decision = binding.get("success_decision")
        assumption_ids = resolved_assumption_ids(binding.get("assumption_ids"))
        if (
            not isinstance(case_id, str)
            or re.fullmatch(r"V-REFLECT-[0-9]{3,}", case_id) is None
        ):
            errors.append(
                f"{label}: reflection_gate_bindings.{binding_name}.case_id must match V-REFLECT-NNN"
            )
        elif case_id in seen_cases:
            errors.append(f"{label}: reflection Gate Case IDs must be unique: {case_id}")
        else:
            seen_cases.add(case_id)
            if case_id not in blocking_case_ids:
                errors.append(
                    f"{label}: reflection Gate Case must be included in blocking_case_ids: {case_id}"
                )

        if not isinstance(new_slice_ref, str) or new_slice_ref not in new_refs:
            errors.append(
                f"{label}: reflection_gate_bindings.{binding_name}.new_slice_ref must reference new_capability_slice_refs"
            )
        elif new_slice_ref in seen_slices:
            errors.append(
                f"{label}: each Slice must have exactly one reflection Gate: {new_slice_ref}"
            )
        else:
            seen_slices.add(new_slice_ref)
            expected_decision = expected_success_decisions[new_slice_ref]
            if success_decision != expected_decision:
                errors.append(
                    f"{label}: {new_slice_ref} reflection success_decision must equal {expected_decision}"
                )

        if binding.get("required_before_next_authorization_or_acceptance") is not True:
            errors.append(
                f"{label}: reflection_gate_bindings.{binding_name} must be required before next authorization or acceptance"
            )
        expected_order = [
            assumption_id
            for assumption_id in critical_assumption_ids
            if assumption_id in set(assumption_ids)
        ]
        if not assumption_ids:
            errors.append(
                f"{label}: reflection_gate_bindings.{binding_name}.assumption_ids must be non-empty"
            )
        elif (
            any(
                assumption_id not in critical_assumption_ids
                for assumption_id in assumption_ids
            )
            or assumption_ids != expected_order
        ):
            errors.append(
                f"{label}: reflection_gate_bindings.{binding_name}.assumption_ids must be an ordered subset of critical_assumption_ids"
            )
        elif isinstance(new_slice_ref, str) and new_slice_ref in new_refs:
            assumptions_by_slice[new_slice_ref] = assumption_ids
        deferred_assumptions = [
            assumption_id
            for assumption_id in critical_assumption_ids
            if assumption_id not in set(assumption_ids)
        ]
        conditional_falsifiers = binding.get("conditional_falsifier_bindings")
        if deferred_assumptions:
            if not isinstance(conditional_falsifiers, dict):
                errors.append(
                    f"{label}: reflection_gate_bindings.{binding_name} must map every deferred assumption to an early conditional falsifier"
                )
            else:
                mapped_deferred: list[str] = []
                seen_falsifier_cases: set[str] = set()
                for falsifier_name, falsifier in conditional_falsifiers.items():
                    if not isinstance(falsifier, dict):
                        errors.append(
                            f"{label}: conditional_falsifier_bindings.{falsifier_name} must be a mapping"
                        )
                        continue
                    assumption_id = falsifier.get("assumption_id")
                    falsifier_case_id = falsifier.get("case_id")
                    if assumption_id not in deferred_assumptions:
                        errors.append(
                            f"{label}: conditional falsifier assumption_id must reference a deferred critical assumption"
                        )
                    else:
                        mapped_deferred.append(str(assumption_id))
                    if (
                        not isinstance(falsifier_case_id, str)
                        or falsifier_case_id not in blocking_case_ids
                        or falsifier_case_id in seen_falsifier_cases
                    ):
                        errors.append(
                            f"{label}: conditional falsifier case_id must be a unique blocking Case"
                        )
                    else:
                        seen_falsifier_cases.add(falsifier_case_id)
                if (
                    set(mapped_deferred) != set(deferred_assumptions)
                    or len(mapped_deferred) != len(set(mapped_deferred))
                ):
                    errors.append(
                        f"{label}: conditional falsifiers must cover every deferred critical assumption exactly once"
                    )
        elif conditional_falsifiers is not None and conditional_falsifiers != {}:
            errors.append(
                f"{label}: final Slice must not define deferred conditional falsifiers"
            )
        decision_owner = binding.get("decision_owner")
        if (
            not isinstance(decision_owner, str)
            or is_pending(decision_owner)
            or is_absent_evidence(decision_owner)
            or has_unresolved_placeholder(decision_owner)
        ):
            errors.append(
                f"{label}: reflection_gate_bindings.{binding_name}.decision_owner must be resolved"
            )

    missing_slices = [reference for reference in new_refs if reference not in seen_slices]
    if missing_slices:
        errors.append(
            f"{label}: every Slice must have exactly one reflection Gate: "
            + ", ".join(missing_slices)
        )
    if len(bindings) != len(new_refs):
        errors.append(
            f"{label}: reflection_gate_bindings count must equal new_capability_slice_refs count"
        )
    previous_assumptions: set[str] = set()
    for index, reference in enumerate(new_refs):
        current_assumptions = assumptions_by_slice.get(reference, [])
        if not previous_assumptions.issubset(set(current_assumptions)):
            errors.append(
                f"{label}: {reference} reflection assumptions must retain every earlier Slice assumption"
            )
        if index == len(new_refs) - 1 and current_assumptions != critical_assumption_ids:
            errors.append(
                f"{label}: final Slice reflection assumptions must cover all critical_assumption_ids in frozen order"
            )
        previous_assumptions = set(current_assumptions)
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
    if requires_reflection_gate(iteration):
        catalog_digest = alignment.get("critical_assumption_catalog_digest")
        if catalog_digest != "not-frozen-proposal-only" and (
            not isinstance(catalog_digest, str)
            or re.fullmatch(r"sha256:[0-9a-f]{64}", catalog_digest) is None
        ):
            errors.append(
                f"{label}: critical_assumption_catalog_digest must be the proposal-only marker or an exact sha256 digest"
            )
    evaluation_input_mode = alignment.get(
        "evaluation_input_mode", "precommitted-hidden-suite"
    )
    if evaluation_input_mode not in {
        "precommitted-hidden-suite",
        USER_HELD_LIVE_EVALUATION_MODE,
    }:
        errors.append(
            f"{label}: product_goal_alignment.evaluation_input_mode is invalid"
        )
    user_held_live = evaluation_input_mode == USER_HELD_LIVE_EVALUATION_MODE
    if user_held_live and alignment.get("held_out_evaluation_owner") != "user":
        errors.append(
            f"{label}: user-held live evaluation must use held_out_evaluation_owner user"
        )
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
        valid_user_held_value = user_held_live and value == USER_HELD_LIVE_UNDISCLOSED
        if not valid_user_held_value and (
            not isinstance(value, str)
            or re.fullmatch(r"sha256:[0-9a-f]{64}", value) is None
        ):
            errors.append(
                f"{label}: product_goal_alignment.{field} must be an exact sha256 digest"
                " or the closed user-held undisclosed marker"
            )

    counts: dict[str, int] = {}
    for field in PRODUCT_GOAL_ALIGNMENT_MANIFEST_COUNTS:
        value = alignment.get(field)
        if (
            user_held_live
            and field
            in {"held_out_baseline_supported_count", "held_out_target_supported_count"}
            and value == USER_HELD_LIVE_UNMEASURED
        ):
            continue
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
            if len(items) != len(set(items)):
                errors.append(
                    f"{label}: product_goal_alignment.{field} must not contain duplicate items"
                )
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
    if requires_direction_preview(iteration):
        direction_preview_checkpoint = alignment.get("direction_preview_checkpoint")
        if isinstance(direction_preview_checkpoint, str):
            required_blocking_cases.add(direction_preview_checkpoint)
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
    checkpoint_fields = [
        ("first_product_web_checkpoint", r"V-WEB-[0-9]{3,}"),
        ("live_ad_hoc_question_checkpoint", r"V-ADHOC-[0-9]{3,}"),
    ]
    if requires_direction_preview(iteration):
        checkpoint_fields.append(
            ("direction_preview_checkpoint", r"V-PREVIEW-[0-9]{3,}")
        )
    for field, pattern in checkpoint_fields:
        value = alignment.get(field)
        if not isinstance(value, str) or re.fullmatch(pattern, value) is None:
            errors.append(
                f"{label}: product_goal_alignment.{field} must be a verification case ID"
            )
    new_refs = sequences.get("new_capability_slice_refs", [])
    if requires_direction_preview(iteration):
        errors.extend(
            validate_direction_preview_binding(
                alignment,
                new_refs,
                blocking_case_ids,
                label,
            )
        )
    if requires_reflection_gate(iteration):
        errors.extend(
            validate_reflection_gate_bindings(
                alignment,
                new_refs,
                blocking_case_ids,
                label,
            )
        )
        errors.extend(
            validate_early_evaluation_bindings(
                alignment,
                new_refs,
                blocking_case_ids,
                label,
                defer_until_post_preview=direction_preview_hardening_is_deferred(
                    manifest,
                    alignment,
                    new_refs,
                    direction_preview_enabled=requires_direction_preview(iteration),
                ),
                direction_preview_enabled=requires_direction_preview(iteration),
            )
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
    require_executed: bool = False,
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
    strict_status = requires_reflection_gate(
        str(verification.metadata.get("iteration", ""))
    ) or require_executed
    status_verdict = blocking_case_status_verdict(row[6])
    legacy_status_tokens: set[str] = set()
    if strict_status:
        if status_verdict is None:
            errors.append(
                f"{label}: {case_id} must remain blocking and use exact PASS, FAIL or NOT-RUN / blocking grammar"
            )
    else:
        legacy_status_tokens = set(
            re.findall(r"[A-Z]+(?:-[A-Z]+)*", row[6].upper())
        )
        if (
            "BLOCKING" not in legacy_status_tokens
            or "NON-BLOCKING" in legacy_status_tokens
        ):
            errors.append(f"{label}: {case_id} must remain blocking")
    if require_executed and status_verdict not in {"PASS", "FAIL"}:
        errors.append(
            f"{label}: {case_id} used as reflection evidence must be executed with exactly one PASS or FAIL verdict"
        )
    if require_pass or expected_evidence is not None:
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
    if require_pass:
        passed = (
            status_verdict == "PASS"
            if strict_status
            else "PASS" in legacy_status_tokens
            and "FAIL" not in legacy_status_tokens
            and "NOT-RUN" not in legacy_status_tokens
        )
        if not passed:
            errors.append(f"{label}: completed {case_id} must be PASS")
    joined = " ".join(row[1:5])
    for reference in required_references:
        if reference not in joined:
            errors.append(
                f"{label}: {case_id} must cite cumulative capability reference {reference}"
            )
    return errors


def blocking_case_status_verdict(value: str) -> str | None:
    """Parse only the frozen blocking status grammar, not loose word tokens."""

    normalized = value.strip().strip("*_`").strip().upper()
    match = re.fullmatch(
        r"(PASS|FAIL|NOT-RUN)\s*/\s*(?:READINESS\s+)?BLOCKING",
        normalized,
    )
    return match.group(1) if match is not None else None


def unique_json_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    """Build a JSON object while rejecting duplicate keys at every depth."""

    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def non_negative_metadata_integer(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if value >= 0 else None
    if isinstance(value, str) and re.fullmatch(r"0|[1-9][0-9]*", value):
        return int(value)
    return None


def validate_positive_value_result(
    result: Document,
    alignment: dict[str, object],
    label: str,
    *,
    require_pass: bool = True,
    expected_case_id: str | None = None,
) -> list[str]:
    """Validate the measured value verdict against its precommitted threshold."""

    errors: list[str] = []
    value_verdict = result.metadata.get("positive_value_verdict")
    if require_pass and value_verdict != "PASS":
        errors.append(f"{label}: positive_value_verdict must equal PASS")
    elif not require_pass and value_verdict not in {"PASS", "FAIL"}:
        errors.append(
            f"{label}: positive_value_verdict must equal PASS or FAIL for an executed early comparison"
        )
    for result_field, manifest_field in (
        ("positive_value_metric", "positive_value_metric"),
        ("positive_value_unit", "positive_value_unit"),
        ("positive_value_comparison", "positive_value_comparison"),
        ("positive_value_threshold", "positive_value_threshold"),
        (
            "positive_value_reuse_horizon_questions",
            "positive_value_reuse_horizon_questions",
        ),
        (
            "mature_source_agent_cache_policy_digest",
            "mature_source_agent_cache_policy_digest",
        ),
        (
            "mature_source_agent_protocol_digest",
            "mature_source_agent_protocol_digest",
        ),
        (
            "mature_source_agent_rubric_digest",
            "mature_source_agent_rubric_digest",
        ),
        ("positive_value_protocol_digest", "positive_value_protocol_digest"),
        (
            "positive_value_freeze_receipt_ref",
            "positive_value_freeze_receipt_ref",
        ),
    ):
        if result.metadata.get(result_field) != alignment.get(manifest_field):
            errors.append(f"{label}: {result_field} must match the frozen Manifest")
    raw_positive_value_actual = result.metadata.get("positive_value_actual")
    positive_value_actual = (
        raw_positive_value_actual
        if type(raw_positive_value_actual) is int
        and raw_positive_value_actual >= 0
        else None
    )
    if positive_value_actual is None:
        errors.append(f"{label}: positive_value_actual must be a non-negative integer")
    else:
        threshold = alignment.get("positive_value_threshold")
        comparison = alignment.get("positive_value_comparison")
        threshold_met: bool | None = None
        if isinstance(threshold, int) and not isinstance(threshold, bool):
            threshold_met = (
                positive_value_actual <= threshold
                if comparison == "at-most"
                else positive_value_actual >= threshold
                if comparison == "at-least"
                else None
            )
        if require_pass and threshold_met is False:
            errors.append(
                f"{label}: positive_value_actual does not satisfy the frozen threshold"
            )
        elif not require_pass and threshold_met is not None:
            expected_verdict = "PASS" if threshold_met else "FAIL"
            if value_verdict != expected_verdict:
                errors.append(
                    f"{label}: positive_value_verdict must match the measured frozen threshold"
                )
    positive_value_report_digest = result.metadata.get(
        "positive_value_report_digest"
    )
    if not isinstance(positive_value_report_digest, str) or re.fullmatch(
        r"sha256:[0-9a-f]{64}", positive_value_report_digest
    ) is None:
        errors.append(
            f"{label}: positive_value_report_digest must be an exact sha256 digest"
        )
    positive_value_case_id = result.metadata.get("positive_value_case_id")
    if (
        not isinstance(positive_value_case_id, str)
        or expected_case_id is not None
        and positive_value_case_id != expected_case_id
    ):
        errors.append(
            f"{label}: positive_value_case_id must match the executed value Case"
        )
    adjudication_owner = result.metadata.get(
        "positive_value_adjudication_owner"
    )
    if adjudication_owner != alignment.get("positive_value_adjudication_owner"):
        errors.append(
            f"{label}: positive_value_adjudication_owner must match the frozen Manifest"
        )
    adjudication_receipt = result.metadata.get(
        "positive_value_adjudication_receipt_ref"
    )
    if not isinstance(adjudication_receipt, str) or re.fullmatch(
        r"codex-user-message:sha256:[0-9a-f]{64}", adjudication_receipt
    ) is None:
        errors.append(
            f"{label}: positive_value_adjudication_receipt_ref must bind an exact independent adjudication message"
        )
    elif adjudication_receipt == result.metadata.get(
        "positive_value_freeze_receipt_ref"
    ):
        errors.append(
            f"{label}: positive value adjudication must use a new receipt after the frozen protocol"
        )

    expected_report_ref = f"{result.identifier}#positive-value-report"
    if result.metadata.get("positive_value_report_ref") != expected_report_ref:
        errors.append(
            f"{label}: positive_value_report_ref must equal {expected_report_ref}"
        )
    report_heading_count = len(
        re.findall(
            r"(?m)^[ ]{0,3}##[ \t]+Positive value report[ \t]*#*[ \t]*$",
            result.body,
        )
    )
    if report_heading_count != 1:
        errors.append(
            f"{label}: Result must contain exactly one Positive value report section"
        )
    report_section = markdown_section_body(result, "Positive value report")
    report_data: dict[str, object] | None = None
    if not has_substantive_markdown_content(report_section):
        errors.append(
            f"{label}: Result must contain a substantive Positive value report section"
        )
    else:
        try:
            loaded_report = json.loads(
                report_section,
                object_pairs_hook=unique_json_object,
            )
        except (json.JSONDecodeError, ValueError) as error:
            errors.append(f"{label}: Positive value report must be exact JSON: {error}")
        else:
            if not isinstance(loaded_report, dict):
                errors.append(f"{label}: positive value report must be a JSON object")
            else:
                report_data = loaded_report
                computed_digest = "sha256:" + hashlib.sha256(
                    report_section.encode("utf-8")
                ).hexdigest()
                if positive_value_report_digest != computed_digest:
                    errors.append(
                        f"{label}: positive_value_report_digest must bind the exact Positive value report section"
                    )

    if report_data is not None:
        expected_report_fields: dict[str, object] = {
            "schema": "software-world-model-positive-value-report/v1",
            "result_id": result.identifier,
            "verification_case_id": positive_value_case_id,
            "metric": result.metadata.get("positive_value_metric"),
            "unit": result.metadata.get("positive_value_unit"),
            "comparison": result.metadata.get("positive_value_comparison"),
            "threshold": result.metadata.get("positive_value_threshold"),
            "actual": result.metadata.get("positive_value_actual"),
            "reuse_horizon_questions": result.metadata.get(
                "positive_value_reuse_horizon_questions"
            ),
            "mature_source_agent_protocol_digest": result.metadata.get(
                "mature_source_agent_protocol_digest"
            ),
            "mature_source_agent_rubric_digest": result.metadata.get(
                "mature_source_agent_rubric_digest"
            ),
            "mature_source_agent_cache_policy_digest": result.metadata.get(
                "mature_source_agent_cache_policy_digest"
            ),
            "positive_value_protocol_digest": result.metadata.get(
                "positive_value_protocol_digest"
            ),
            "freeze_receipt_ref": result.metadata.get(
                "positive_value_freeze_receipt_ref"
            ),
            "adjudication_owner": adjudication_owner,
            "adjudication_receipt_ref": adjudication_receipt,
        }
        expected_report_field_names = {
            *expected_report_fields,
            "measurement_input_digest",
        }
        if set(report_data) != expected_report_field_names:
            errors.append(
                f"{label}: positive value report must use only the exact v1 schema fields"
            )
        for integer_field in ("actual", "threshold", "reuse_horizon_questions"):
            if type(report_data.get(integer_field)) is not int:
                errors.append(
                    f"{label}: positive value report {integer_field} must be an exact JSON integer"
                )
        for field, expected in expected_report_fields.items():
            if report_data.get(field) != expected:
                errors.append(
                    f"{label}: positive value report {field} must match its frozen input or Result"
                )
        measurement_input_digest = report_data.get("measurement_input_digest")
        if not isinstance(measurement_input_digest, str) or re.fullmatch(
            r"sha256:[0-9a-f]{64}", measurement_input_digest
        ) is None:
            errors.append(
                f"{label}: positive value report must bind an exact measurement_input_digest"
            )
    return errors


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

    if requires_engineering_qa_hybrid(iteration):
        for field in (
            "authorized_source_retrieval_count",
            "authorized_source_retrieval_bytes",
        ):
            value = non_negative_metadata_integer(result.metadata.get(field))
            if value is None or value < 1:
                errors.append(f"{label}: {field} must be a positive integer")
        for field in (
            "answer_direct_source_access_count",
            "reviewer_direct_source_access_count",
            "repository_write_count",
            "silent_mode_fallback_count",
        ):
            value = non_negative_metadata_integer(result.metadata.get(field))
            if value != 0:
                errors.append(f"{label}: {field} must equal zero")
        package_digest = result.metadata.get(
            "question_evidence_package_manifest_digest"
        )
        if not isinstance(package_digest, str) or re.fullmatch(
            r"sha256:[0-9a-f]{64}", package_digest
        ) is None:
            errors.append(
                f"{label}: question_evidence_package_manifest_digest must be an exact sha256 digest"
            )

    product_goal_metadata, _, _, _ = product_goal_v000_contract(iteration)
    for field, expected in {
        **product_goal_metadata,
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
            and counts[result_field] != minimum
        ):
            errors.append(f"{label}: {result_field} must equal the frozen Manifest count")
    if result.metadata.get("mature_source_agent_comparison") != "non-regression":
        errors.append(f"{label}: mature_source_agent_comparison must equal non-regression")
    if requires_reflection_gate(iteration):
        errors.extend(
            validate_positive_value_result(
                result,
                alignment,
                label,
                expected_case_id="V-000",
            )
        )
        adjudication_forbidden_refs: set[str] = set()
        top_authorization = manifest.get("authorization")
        if isinstance(top_authorization, dict):
            top_authorization_ref = top_authorization.get("authorization_ref")
            if isinstance(top_authorization_ref, str):
                adjudication_forbidden_refs.add(top_authorization_ref)
        for manifest_slice in development_slices.values():
            if isinstance(manifest_slice, dict):
                authorization_ref = manifest_slice.get("authorization_ref")
                if isinstance(authorization_ref, str):
                    adjudication_forbidden_refs.add(authorization_ref)
        if by_id is not None:
            for prior_slice_result_ref in slice_result_refs:
                prior_slice_result = by_id.get(prior_slice_result_ref)
                prior_decision_ref = (
                    prior_slice_result.metadata.get("reflection_decision_ref")
                    if prior_slice_result is not None
                    else None
                )
                if isinstance(prior_decision_ref, str):
                    adjudication_forbidden_refs.add(prior_decision_ref)
                prior_adjudication_ref = (
                    prior_slice_result.metadata.get(
                        "positive_value_adjudication_receipt_ref"
                    )
                    if prior_slice_result is not None
                    else None
                )
                if isinstance(prior_adjudication_ref, str):
                    adjudication_forbidden_refs.add(prior_adjudication_ref)
        if result.metadata.get(
            "positive_value_adjudication_receipt_ref"
        ) in adjudication_forbidden_refs:
            errors.append(
                f"{label}: final positive value adjudication must use a new message after all authorizations and prior Slice decisions"
            )
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
    (
        product_goal_metadata,
        product_goal_claim,
        product_goal_frozen_input,
        product_goal_expected,
    ) = product_goal_v000_contract(iteration)
    for field, expected in product_goal_metadata.items():
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
    frozen_input = product_goal_frozen_input
    expected_outcome = product_goal_expected
    if (
        requires_reflection_gate(iteration)
        and not requires_engineering_qa_hybrid(iteration)
    ):
        frozen_input += "；预提交差异化价值阈值"
        expected_outcome = (
            "支持率提高；重大错误为 0；逐题完整性不退步；差异化价值阈值 PASS；"
            "提问时 Source/Update/Direct fallback=0；同一正式 Web 可人工验证"
        )
    expected_contract = (
        product_goal_claim,
        PRODUCT_GOAL_V000_LEVEL,
        frozen_input,
        expected_outcome,
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

    strict_status = requires_reflection_gate(iteration)
    status_verdict = blocking_case_status_verdict(row[6])
    legacy_status_tokens: set[str] = set()
    if strict_status:
        if status_verdict is None:
            errors.append(
                f"{label}: V-000 status must remain blocking and use exact PASS, FAIL or NOT-RUN / blocking grammar"
            )
    else:
        legacy_status_tokens = set(
            re.findall(r"[A-Z]+(?:-[A-Z]+)*", row[6].upper())
        )
        if (
            "BLOCKING" not in legacy_status_tokens
            or "NON-BLOCKING" in legacy_status_tokens
        ):
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
        passed = (
            status_verdict == "PASS"
            if strict_status
            else "PASS" in legacy_status_tokens
            and "FAIL" not in legacy_status_tokens
            and "NOT-RUN" not in legacy_status_tokens
        )
        if not passed:
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
                != product_goal_metadata["product_goal_outcome"]
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
    elif isinstance(authorized_at, str):
        try:
            datetime.fromisoformat(authorized_at.replace("Z", "+00:00"))
        except ValueError:
            errors.append(
                f"{readiness.relative_path}: authorized_at must be a real ISO-8601 timestamp"
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
    expected_status: str | None = None,
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
        elif expected_status is not None and manifest_status != expected_status:
            errors.append(
                f"{label}: iteration.status must match the iteration index status {expected_status}"
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


def _execution_manifest_sequence(
    *,
    manifest: dict[str, object],
    manifest_text: str | None,
    section: str,
    field: str,
) -> list[str]:
    """Resolve a scalar sequence for the execution-readiness gate.

    ``safe_load_manifest`` deliberately validates block sequences without
    materializing their values.  File-backed validation therefore resolves
    those values from the already validated inert text, while unit callers may
    continue to provide an ordinary in-memory list.
    """

    section_value = manifest.get(section)
    if isinstance(section_value, dict):
        direct = section_value.get(field)
        if isinstance(direct, list):
            return [str(item) for item in direct]
    if manifest_text is None:
        return []
    return manifest_resolved_sequence_items(manifest_text, section, field) or []


def canonical_fileset_digest(
    schema: str,
    paths: list[str],
    *,
    repository: Path | None = None,
) -> str:
    """Digest a canonical, repository-relative ordered fileset."""

    root = REPOSITORY if repository is None else repository
    entries: list[dict[str, object]] = []
    for relative in paths:
        payload = (root / relative).read_bytes()
        entries.append(
            {
                "path": relative,
                "size": len(payload),
                "sha256": "sha256:" + hashlib.sha256(payload).hexdigest(),
            }
        )
    encoded = json.dumps(
        {"schema": schema, "entries": entries},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def canonical_raw_component_set_digest(
    paths: tuple[Path, ...],
) -> str:
    """Match a protocol that binds an ordered list of raw component digests."""

    raw_digests = [
        "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
        for path in paths
    ]
    encoded = json.dumps(
        raw_digests,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def canonical_mapping_digest(
    schema: str, field: str, value: dict[str, object]
) -> str:
    """Bind a frozen manifest mapping without relying on YAML presentation."""

    encoded = json.dumps(
        {"schema": schema, field: value},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def validate_engineering_qa_answer_protocol_execution_readiness(
    answer_protocol: dict[str, object], label: str
) -> list[str]:
    """Freeze the ITER-010+ answer/review path and all of its quality bounds."""

    errors: list[str] = []
    if (
        answer_protocol.get("schema")
        != "ENGINEERING_QA_HYBRID_EVIDENCE@1"
    ):
        errors.append(
            f"{label}: answer_protocol.schema must equal "
            "ENGINEERING_QA_HYBRID_EVIDENCE@1"
        )
    if (
        answer_protocol.get("contract_ref")
        != "SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING"
    ):
        errors.append(
            f"{label}: answer_protocol.contract_ref must equal "
            "SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING"
        )
    if answer_protocol.get("mode") != "upfront-engineering-qa-hybrid-evidence":
        errors.append(
            f"{label}: answer_protocol.mode must equal upfront-engineering-qa-hybrid-evidence"
        )

    required_question_fields = (
        "user-goal,audience,requested-abstraction-level,"
        "material-conclusion-checklist,evidence-needs,response-language-and-constraints"
    )
    if (
        answer_protocol.get("question_understanding_required_fields")
        != required_question_fields
    ):
        errors.append(
            f"{label}: answer_protocol.question_understanding_required_fields must "
            "freeze the user goal, audience, abstraction level, material-conclusion "
            "checklist, evidence needs, response language and constraints"
        )

    positive_integer_fields = (
        "question_understanding_model_call_upper_bound",
        "initial_retrieval_rounds",
        "targeted_reretrieval_round_upper_bound",
        "max_retrieval_steps_per_round",
        "max_source_files_per_question",
        "max_source_bytes_per_question",
        "max_repository_document_bytes_per_question",
        "max_build_configuration_bytes_per_question",
        "max_test_bytes_per_question",
        "max_world_model_result_bytes_per_question",
        "max_sealed_evidence_package_bytes_per_question",
        "max_support_items_per_question",
        "max_trace_bytes_per_question",
        "max_wall_time_milliseconds_per_question",
        "initial_answer_model_calls",
        "independent_review_model_calls_per_attempt",
        "same_package_targeted_rewrite_upper_bound",
        "answer_attempt_upper_bound",
        "review_attempt_upper_bound",
        "provider_output_complete-replacement_upper_bound_per_stage",
        "hard_safety_model_call_upper_bound_per_question",
    )
    numeric_fields: dict[str, int] = {}
    for field in positive_integer_fields:
        value = answer_protocol.get(field)
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            errors.append(
                f"{label}: answer_protocol.{field} must be a positive frozen integer upper bound"
            )
        else:
            numeric_fields[field] = value

    exact_numeric_values = {
        "question_understanding_model_call_upper_bound": 1,
        "initial_retrieval_rounds": 1,
        "targeted_reretrieval_round_upper_bound": 1,
        "initial_answer_model_calls": 1,
        "independent_review_model_calls_per_attempt": 1,
        "same_package_targeted_rewrite_upper_bound": 1,
        "answer_attempt_upper_bound": 3,
        "review_attempt_upper_bound": 3,
    }
    for field, expected in exact_numeric_values.items():
        value = numeric_fields.get(field)
        if value is not None and value != expected:
            errors.append(
                f"{label}: answer_protocol.{field} must equal {expected}"
            )

    answer_attempts = numeric_fields.get("answer_attempt_upper_bound")
    rewrite_bound = numeric_fields.get("same_package_targeted_rewrite_upper_bound")
    reretrieval_bound = numeric_fields.get("targeted_reretrieval_round_upper_bound")
    initial_answer_calls = numeric_fields.get("initial_answer_model_calls")
    if (
        answer_attempts is not None
        and rewrite_bound is not None
        and reretrieval_bound is not None
        and initial_answer_calls is not None
        and answer_attempts
        != initial_answer_calls + rewrite_bound + reretrieval_bound
    ):
        errors.append(
            f"{label}: answer_protocol.answer_attempt_upper_bound must cover the "
            "initial answer, the allowed same-package targeted rewrite and the "
            "post-reretrieval answer"
        )
    review_attempts = numeric_fields.get("review_attempt_upper_bound")
    if (
        review_attempts is not None
        and answer_attempts is not None
        and review_attempts != answer_attempts
    ):
        errors.append(
            f"{label}: answer_protocol.review_attempt_upper_bound must equal "
            "answer_attempt_upper_bound so every answer attempt is independently reviewed"
        )
    hard_call_bound = numeric_fields.get(
        "hard_safety_model_call_upper_bound_per_question"
    )
    question_calls = numeric_fields.get(
        "question_understanding_model_call_upper_bound"
    )
    calls_per_review = numeric_fields.get(
        "independent_review_model_calls_per_attempt"
    )
    if all(
        value is not None
        for value in (
            hard_call_bound,
            question_calls,
            answer_attempts,
            review_attempts,
            calls_per_review,
        )
    ):
        minimum_core_calls = (
            question_calls
            + answer_attempts
            + review_attempts * calls_per_review
        )
        if hard_call_bound < minimum_core_calls:
            errors.append(
                f"{label}: answer_protocol.hard_safety_model_call_upper_bound_per_question "
                "must cover question understanding, every answer attempt and every "
                "independent review"
            )

    for field in (
        "quality_checklist_reduction_due_to_remaining_calls_allowed",
        "evidence_requirement_reduction_due_to_remaining_calls_allowed",
        "review_skipping_due_to_remaining_calls_allowed",
        "provider_request_retries_allowed",
        "provider_switch_after_dispatch_allowed",
    ):
        if answer_protocol.get(field) is not False:
            errors.append(f"{label}: answer_protocol.{field} must be false")
    for field in (
        "targeted_reretrieval_requires_specific_reviewer_evidence_gap",
        "same_package_rewrite_requires_specific_reviewer_finding",
        "reseal_after_targeted_reretrieval_required",
        "independent_rereview_after_any_rewrite_or_reseal_required",
        "deterministic_grounding_authorization_revision-allowlist-and-package-seal_checks",
    ):
        if answer_protocol.get(field) is not True:
            errors.append(f"{label}: answer_protocol.{field} must be true")
    if (
        answer_protocol.get("resource_exhaustion_behavior")
        != "fail-closed-with-audited-user-visible-limitation-only-if-independently-approved"
    ):
        errors.append(
            f"{label}: answer_protocol.resource_exhaustion_behavior must equal "
            "fail-closed-with-audited-user-visible-limitation-only-if-independently-approved"
        )

    legacy_fields = (
        "planner_model_calls",
        "draft_model_calls",
        "independent_reviewer_model_calls",
        "exact_total_model_calls_per_question",
        "max_investigation_steps",
        "max_investigation_model_calls",
        "planner_model_call_upper_bound",
        "total_model_call_upper_bound_per_question",
        "max_query_bytes_per_step",
        "max_result_bytes_per_step",
        "max_total_query_bytes_per_question",
        "max_total_result_bytes_per_question",
        "budget_exhaustion_behavior",
        "deterministic_schema_grounding_and_authorization_checks",
        "retries_allowed",
    )
    for field in legacy_fields:
        if field in answer_protocol:
            errors.append(
                f"{label}: engineering QA answer_protocol must not mix legacy field {field}"
            )
    if answer_protocol.get("status") != "frozen":
        errors.append(f"{label}: answer_protocol.status must equal frozen")
    return errors


def validate_engineering_qa_hybrid_evidence_execution_readiness(
    source_scope: dict[str, object],
    hybrid_evidence_path: dict[str, object],
    answer_protocol: dict[str, object],
    label: str,
) -> list[str]:
    """Keep source retrieval isolated while allowing evidence-backed engineering QA."""

    errors: list[str] = []
    expected_source_values: dict[str, object] = {
        "provider": "LOCAL_GIT",
        "content_kind": (
            "exact-revision-java-source-repository-documents-build-configuration-"
            "tests-plus-prebuilt-world-model"
        ),
        "contract_ref": "SYS-CONTRACT-SOURCE-ARTIFACT",
        "question_or_suite_driven_update_allowed": False,
        "question_time_read_only_retrieval_allowed": True,
        "repository_write_allowed": False,
    }
    for field, expected in expected_source_values.items():
        if source_scope.get(field) != expected:
            errors.append(
                f"{label}: source_scope.{field} must equal {expected} for ENGINEERING_QA"
            )

    expected_hybrid_values: dict[str, object] = {
        "mode": "ENGINEERING_QA",
        "strict_world_model_mode_preserved": True,
        "direct_investigation_mode_preserved": True,
        "silent_mode_fallback_allowed": False,
        "world_model_role": "reusable-engineering-map-manual-and-retrieval-entry",
        "world_model_retrieval_hint_or_candidate_reduction_only": True,
        "world_model_as_question-time-source-recall_gate_allowed": False,
        "world_model_required_as_source_retrieval_gate": False,
        "retrieval_plan_inputs": (
            "immutable-original-question-checklist-and-snapshot-hints"
        ),
        "zero-irrelevant-or-insufficient-snapshot_blocks_exact-revision-retrieval": False,
        "snapshot_source_revision_compatibility": (
            "exact-match-or-explicit-partitioned-version-comparison-otherwise-"
            "unaligned-navigation-only"
        ),
        "model_role": (
            "question-understanding-investigation-control-answer-synthesis-and-"
            "independent-review-not-fact-authority"
        ),
        "fact_authority": "sealed-evidence-package",
        "retrieval_worker_sources": (
            "exact-revision-source-repository-documents-build-configuration-tests"
        ),
        "retrieval_worker_access": "read-only-allowlisted-audited",
        "source_trust": "untrusted-input",
        "live_provider_source-fragment-disclosure": (
            "separately-authorized-exact-provider-model-role-and-allowlist-only"
        ),
        "answer_repository_access": "denied",
        "reviewer_repository_access": "denied",
        "answer_input": "sealed-evidence-package-only",
        "reviewer_input": (
            "original-question-question-understanding-sealed-evidence-package-and-draft-only"
        ),
        "knowledge_persistence": (
            "asynchronous-after-delivery-through-normal-admission-and-publication"
        ),
        "status": "frozen",
    }
    for field, expected in expected_hybrid_values.items():
        if hybrid_evidence_path.get(field) != expected:
            errors.append(
                f"{label}: hybrid_evidence_path.{field} must equal {expected}"
            )

    errors.extend(
        validate_engineering_qa_answer_protocol_execution_readiness(
            answer_protocol, label
        )
    )
    return errors


def validate_answer_protocol_execution_readiness(
    answer_protocol: dict[str, object], label: str, iteration: str
) -> list[str]:
    """Validate the frozen answer protocol without reviving an earlier pipeline."""

    engineering_qa_mode = (
        answer_protocol.get("mode") == "upfront-engineering-qa-hybrid-evidence"
    )
    if requires_engineering_qa_hybrid(iteration) and not engineering_qa_mode:
        return [
            f"{label}: ITER-010 answer_protocol.mode must equal "
            "upfront-engineering-qa-hybrid-evidence"
        ]
    if engineering_qa_mode:
        if not supports_engineering_qa_hybrid(iteration):
            return [
                f"{label}: engineering QA answer_protocol is supported only from ITER-010"
            ]
        return validate_engineering_qa_answer_protocol_execution_readiness(
            answer_protocol, label
        )

    errors: list[str] = []
    if requires_reflection_gate(iteration):
        if (
            answer_protocol.get("mode")
            != "bounded-result-driven-world-model-investigation"
        ):
            errors.append(
                f"{label}: answer_protocol.mode must equal bounded-result-driven-world-model-investigation"
            )
        numeric_fields: dict[str, int] = {}
        for field in (
            "max_investigation_steps",
            "max_investigation_model_calls",
            "planner_model_call_upper_bound",
            "total_model_call_upper_bound_per_question",
            "max_query_bytes_per_step",
            "max_result_bytes_per_step",
            "max_total_query_bytes_per_question",
            "max_total_result_bytes_per_question",
            "max_wall_time_milliseconds_per_question",
            "max_support_items_per_question",
            "max_trace_bytes_per_question",
        ):
            value = answer_protocol.get(field)
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                errors.append(
                    f"{label}: answer_protocol.{field} must be a positive frozen integer"
                )
            else:
                numeric_fields[field] = value
        for field in (
            "max_investigation_steps",
            "max_investigation_model_calls",
            "planner_model_call_upper_bound",
        ):
            value = numeric_fields.get(field)
            if value is not None and value < 2:
                errors.append(
                    f"{label}: answer_protocol.{field} must be at least 2 so a result can drive a later investigation decision"
                )
        planner_upper_bound = numeric_fields.get("planner_model_call_upper_bound")
        investigation_call_bound = numeric_fields.get(
            "max_investigation_model_calls"
        )
        if (
            planner_upper_bound is not None
            and investigation_call_bound is not None
            and planner_upper_bound != investigation_call_bound
        ):
            errors.append(
                f"{label}: planner_model_call_upper_bound must equal max_investigation_model_calls"
            )
        total_upper_bound = numeric_fields.get(
            "total_model_call_upper_bound_per_question"
        )
        if (
            total_upper_bound is not None
            and planner_upper_bound is not None
            and total_upper_bound != planner_upper_bound + 2
        ):
            errors.append(
                f"{label}: total_model_call_upper_bound_per_question must equal planner upper bound plus one Draft and one Review call"
            )
        for per_step_field, total_field in (
            ("max_query_bytes_per_step", "max_total_query_bytes_per_question"),
            ("max_result_bytes_per_step", "max_total_result_bytes_per_question"),
        ):
            per_step = numeric_fields.get(per_step_field)
            total = numeric_fields.get(total_field)
            if per_step is not None and total is not None and total < per_step:
                errors.append(
                    f"{label}: answer_protocol.{total_field} must be at least {per_step_field}"
                )
        if (
            answer_protocol.get("budget_exhaustion_behavior")
            != "fail-closed-with-explicit-limitation"
        ):
            errors.append(
                f"{label}: answer_protocol.budget_exhaustion_behavior must equal fail-closed-with-explicit-limitation"
            )
        for field in (
            "planner_model_calls",
            "exact_total_model_calls_per_question",
        ):
            if field in answer_protocol:
                errors.append(
                    f"{label}: ITER-008+ answer_protocol must not use legacy fixed-call field {field}"
                )
    else:
        for field, expected in {
            "planner_model_calls": 1,
            "draft_model_calls": 1,
            "independent_reviewer_model_calls": 1,
            "exact_total_model_calls_per_question": 3,
        }.items():
            if answer_protocol.get(field) != expected:
                errors.append(
                    f"{label}: answer_protocol.{field} must equal {expected}"
                )
    for field in ("draft_model_calls", "independent_reviewer_model_calls"):
        if answer_protocol.get(field) != 1:
            errors.append(f"{label}: answer_protocol.{field} must equal 1")
    if (
        answer_protocol.get(
            "deterministic_schema_grounding_and_authorization_checks"
        )
        is not True
    ):
        errors.append(f"{label}: answer_protocol deterministic checks must be true")
    if answer_protocol.get("retries_allowed") is not False:
        errors.append(f"{label}: answer_protocol.retries_allowed must be false")
    if answer_protocol.get("status") != "frozen":
        errors.append(f"{label}: answer_protocol.status must equal frozen")
    return errors


def validate_positive_value_execution_readiness(
    alignment: dict[str, object], label: str
) -> list[str]:
    """Require a precommitted, replayable value comparison before coding."""

    errors: list[str] = []
    for field in ("positive_value_metric", "positive_value_unit"):
        value = alignment.get(field)
        if (
            not isinstance(value, str)
            or is_pending(value)
            or is_absent_evidence(value)
            or has_unresolved_placeholder(value)
        ):
            errors.append(
                f"{label}: product_goal_alignment.{field} must be frozen before Slice execution"
            )
    if alignment.get("positive_value_comparison") not in {"at-most", "at-least"}:
        errors.append(
            f"{label}: positive_value_comparison must equal at-most or at-least before Slice execution"
        )
    positive_value_threshold = alignment.get("positive_value_threshold")
    if (
        isinstance(positive_value_threshold, bool)
        or not isinstance(positive_value_threshold, int)
        or positive_value_threshold < 0
    ):
        errors.append(
            f"{label}: positive_value_threshold must be a non-negative integer before Slice execution"
        )
    reuse_horizon = alignment.get("positive_value_reuse_horizon_questions")
    if (
        isinstance(reuse_horizon, bool)
        or not isinstance(reuse_horizon, int)
        or reuse_horizon < 1
    ):
        errors.append(
            f"{label}: positive_value_reuse_horizon_questions must be a positive integer before Slice execution"
        )
    for field in (
        "mature_source_agent_protocol_digest",
        "mature_source_agent_rubric_digest",
        "mature_source_agent_cache_policy_digest",
        "positive_value_protocol_digest",
    ):
        digest = alignment.get(field)
        if not isinstance(digest, str) or re.fullmatch(
            r"sha256:[0-9a-f]{64}", digest
        ) is None:
            errors.append(
                f"{label}: {field} must be an exact sha256 digest before Slice execution"
            )
    freeze_receipt = alignment.get("positive_value_freeze_receipt_ref")
    if not isinstance(freeze_receipt, str) or re.fullmatch(
        r"codex-user-message:sha256:[0-9a-f]{64}", freeze_receipt
    ) is None:
        errors.append(
            f"{label}: positive_value_freeze_receipt_ref must bind an exact user message before Slice execution"
        )
    if alignment.get("positive_value_adjudication_owner") not in {
        "user",
        "independent-evaluator",
    }:
        errors.append(
            f"{label}: positive_value_adjudication_owner must be frozen as user or independent-evaluator before Slice execution"
        )
    return errors


def validate_product_goal_execution_readiness(
    manifest: dict[str, object],
    label: str,
    iteration: str,
    by_id: dict[str, Document],
    new_refs: list[str],
    verification: Document | None,
    *,
    manifest_text: str | None = None,
    verify_current_contract_fileset: bool = True,
) -> list[str]:
    """Validate inputs that must be frozen before the first product Slice runs."""

    errors: list[str] = []
    alignment = manifest.get("product_goal_alignment")
    if not isinstance(alignment, dict):
        return errors
    user_held_live = (
        alignment.get("evaluation_input_mode") == USER_HELD_LIVE_EVALUATION_MODE
    )

    if requires_reflection_gate(iteration):
        proposal = by_id.get(f"{iteration}-PROPOSAL")
        catalog_digest, assumption_expectations, catalog_errors = (
            critical_assumption_catalog(proposal)
        )
        errors.extend(catalog_errors)
        supplied_catalog_digest = alignment.get(
            "critical_assumption_catalog_digest"
        )
        if supplied_catalog_digest != catalog_digest:
            errors.append(
                f"{label}: critical_assumption_catalog_digest must match the exact Proposal assumption catalog"
            )
        critical_assumption_ids = resolved_assumption_ids(
            alignment.get("critical_assumption_ids")
        )
        if critical_assumption_ids != list(assumption_expectations):
            errors.append(
                f"{label}: critical_assumption_ids must exactly match the Proposal assumption catalog order"
            )
        readiness = by_id.get(f"{iteration}-READINESS")
        if readiness is None or readiness.metadata.get(
            "critical_assumption_catalog_digest"
        ) != catalog_digest:
            errors.append(
                f"{label}: accepted Readiness must bind the exact critical_assumption_catalog_digest"
            )

    blocking_case_ids = _execution_manifest_sequence(
        manifest=manifest,
        manifest_text=manifest_text,
        section="product_goal_alignment",
        field="blocking_case_ids",
    )
    readiness_case_ids = _execution_manifest_sequence(
        manifest=manifest,
        manifest_text=manifest_text,
        section="product_goal_alignment",
        field="readiness_blocking_case_ids",
    )
    if not readiness_case_ids:
        errors.append(
            f"{label}: readiness_blocking_case_ids must be a non-empty sequence before Slice execution"
        )
    else:
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

    defer_early_evaluation = direction_preview_hardening_is_deferred(
        manifest,
        alignment,
        new_refs,
        direction_preview_enabled=requires_direction_preview(iteration),
    )
    if (
        requires_reflection_gate(iteration)
        and len(new_refs) > 1
        and not defer_early_evaluation
    ):
        errors.extend(validate_positive_value_execution_readiness(alignment, label))

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
    source_case_ids = _execution_manifest_sequence(
        manifest=manifest,
        manifest_text=manifest_text,
        section="source_scope",
        field="verification_case_ids",
    )
    if not source_case_ids:
        errors.append(
            f"{label}: source_scope.verification_case_ids must bind update-without-question Cases"
        )
    else:
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
    engineering_qa_mode = (
        answer_protocol.get("mode") == "upfront-engineering-qa-hybrid-evidence"
    )
    if requires_engineering_qa_hybrid(iteration) or engineering_qa_mode:
        hybrid_evidence_path = manifest.get("hybrid_evidence_path")
        if not isinstance(hybrid_evidence_path, dict):
            errors.append(
                f"{label}: hybrid_evidence_path must be a mapping before ENGINEERING_QA Slice execution"
            )
            hybrid_evidence_path = {}
        errors.extend(
            validate_engineering_qa_hybrid_evidence_execution_readiness(
                source_scope,
                hybrid_evidence_path,
                answer_protocol,
                label,
            )
        )
        if engineering_qa_mode and not supports_engineering_qa_hybrid(iteration):
            errors.append(
                f"{label}: engineering QA hybrid evidence is supported only from ITER-010"
            )
    else:
        errors.extend(
            validate_answer_protocol_execution_readiness(
                answer_protocol, label, iteration
            )
        )
    if requires_direction_preview(iteration):
        errors.extend(
            validate_direction_preview_answer_entry(
                alignment, answer_protocol, label
            )
        )

    readiness_inputs = manifest.get("readiness_inputs")
    if not isinstance(readiness_inputs, dict):
        errors.append(f"{label}: readiness_inputs must be a mapping before Slice execution")
        readiness_inputs = {}
    if engineering_qa_mode:
        architecture_decision = readiness_inputs.get(
            "required_architecture_decision"
        )
        if architecture_decision != "SYS-ADR-016":
            errors.append(
                f"{label}: ENGINEERING_QA required_architecture_decision must equal SYS-ADR-016"
            )
        target_decision = (
            by_id.get(architecture_decision)
            if isinstance(architecture_decision, str)
            else None
        )
        if (
            target_decision is None
            or target_decision.metadata.get("kind") != "system-decision"
            or target_decision.metadata.get("status") != "accepted"
            or target_decision.metadata.get("authority") != "normative"
        ):
            errors.append(
                f"{label}: ENGINEERING_QA architecture decision must resolve to an accepted normative system-decision"
            )
        protocol_schema = answer_protocol.get("schema")
        supplied_budget_digest = readiness_inputs.get(
            "investigation_budget_digest"
        )
        if isinstance(protocol_schema, str):
            actual_budget_digest = canonical_mapping_digest(
                protocol_schema, "answer_protocol", answer_protocol
            )
            if supplied_budget_digest != actual_budget_digest:
                errors.append(
                    f"{label}: investigation_budget_digest must bind the exact ENGINEERING_QA answer_protocol"
                )
    contract_ids = _execution_manifest_sequence(
        manifest=manifest,
        manifest_text=manifest_text,
        section="readiness_inputs",
        field="required_system_contract_refs",
    )
    if not contract_ids:
        errors.append(
            f"{label}: readiness_inputs.required_system_contract_refs must be non-empty"
        )
    else:
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

    contract_set_schema = readiness_inputs.get("system_contract_set_schema")
    expected_contract_set_schema = f"{iteration}-SYSTEM-CONTRACT-SET@1"
    if contract_set_schema != expected_contract_set_schema:
        errors.append(
            f"{label}: system_contract_set_schema must equal {expected_contract_set_schema}"
        )
    contract_set_paths = _execution_manifest_sequence(
        manifest=manifest,
        manifest_text=manifest_text,
        section="readiness_inputs",
        field="system_contract_set_paths",
    )
    contract_set_paths_valid = True
    if not contract_set_paths:
        errors.append(f"{label}: system_contract_set_paths must be non-empty")
        contract_set_paths_valid = False
    elif len(contract_set_paths) != len(set(contract_set_paths)):
        errors.append(f"{label}: system_contract_set_paths must be unique")
        contract_set_paths_valid = False
    elif contract_set_paths != sorted(contract_set_paths):
        errors.append(
            f"{label}: system_contract_set_paths must use canonical lexical order"
        )
        contract_set_paths_valid = False

    system_root = (REPOSITORY / "docs/system").resolve()
    if contract_set_paths_valid:
        for relative in contract_set_paths:
            parsed = PurePosixPath(relative)
            target = REPOSITORY / relative
            canonical = (
                relative == parsed.as_posix()
                and not parsed.is_absolute()
                and all(part not in {"", ".", ".."} for part in parsed.parts)
            )
            try:
                target.resolve().relative_to(system_root)
            except (OSError, ValueError):
                canonical = False
            if (
                not canonical
                or target.is_symlink()
                or not target.is_file()
            ):
                errors.append(
                    f"{label}: system Contract set path is invalid: {relative}"
                )
                contract_set_paths_valid = False

    supplied_contract_set_digest = readiness_inputs.get(
        "system_contract_set_digest"
    )
    if (
        verify_current_contract_fileset
        and contract_set_paths_valid
        and contract_set_schema == expected_contract_set_schema
    ):
        actual_contract_set_digest = canonical_fileset_digest(
            expected_contract_set_schema,
            contract_set_paths,
        )
        if supplied_contract_set_digest != actual_contract_set_digest:
            errors.append(
                f"{label}: system_contract_set_digest does not match the exact fileset"
            )
    elif not isinstance(supplied_contract_set_digest, str) or re.fullmatch(
        r"sha256:[0-9a-f]{64}", supplied_contract_set_digest
    ) is None:
        errors.append(
            f"{label}: historical system_contract_set_digest must remain an exact sha256 digest"
        )

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
        elif contract_set_paths_valid:
            try:
                contract_path = target.path.resolve().relative_to(
                    REPOSITORY.resolve()
                ).as_posix()
            except ValueError:
                contract_path = ""
            if contract_path not in contract_set_paths:
                errors.append(
                    f"{label}: required Contract is absent from system_contract_set_paths: {reference}"
                )

    frontend = readiness_inputs.get("java_frontend")
    if not isinstance(frontend, dict):
        errors.append(f"{label}: readiness_inputs.java_frontend must be a mapping")
        frontend = {}
    expected_frontend_fields = {
        "artifact_ref",
        "version",
        "runtime_version",
        "grammar_version",
        "language_abi",
        "license_ref",
        "runtime_license_digest",
        "grammar_license_digest",
        "runtime_fileset_digest",
        "grammar_fileset_digest",
        "offline_artifact_digest",
        "canonicalization_oracle_digest",
        "information_preservation_oracle_digest",
        "information_boundary_oracle_digest",
        "legacy_calls_consistency_oracle_digest",
        "readiness_oracle_result_digest",
        "readiness_oracle_result_path",
    }
    if set(frontend) != expected_frontend_fields:
        errors.append(f"{label}: java_frontend fields must match the frozen schema")
    for field in (
        "artifact_ref",
        "version",
        "runtime_version",
        "grammar_version",
        "license_ref",
    ):
        value = frontend.get(field)
        if (
            not isinstance(value, str)
            or is_pending(value)
            or is_absent_evidence(value)
            or has_unresolved_placeholder(value)
        ):
            errors.append(f"{label}: java_frontend.{field} must be resolved")
    language_abi = frontend.get("language_abi")
    if (
        isinstance(language_abi, bool)
        or not isinstance(language_abi, int)
        or language_abi < 1
    ):
        errors.append(f"{label}: java_frontend.language_abi must be positive")
    for field in (
        "runtime_license_digest",
        "grammar_license_digest",
        "runtime_fileset_digest",
        "grammar_fileset_digest",
        "offline_artifact_digest",
        "canonicalization_oracle_digest",
        "information_preservation_oracle_digest",
        "information_boundary_oracle_digest",
        "legacy_calls_consistency_oracle_digest",
        "readiness_oracle_result_digest",
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
    result_path = frontend.get("readiness_oracle_result_path")
    if (
        not isinstance(result_path, str)
        or PurePosixPath(result_path).is_absolute()
        or result_path != PurePosixPath(result_path).as_posix()
        or any(
            part in {"", ".", ".."}
            for part in PurePosixPath(result_path).parts
        )
    ):
        errors.append(
            f"{label}: readiness_oracle_result_path must be repository-relative"
        )

    if iteration == "ITER-007":
        hidden_components = tuple(
            REPOSITORY
            / "validation/structure_world_model_iteration_007"
            / name
            for name in (
                "hidden_freeze_protocol.json",
                "hidden_freeze.py",
                "hidden_freeze_lifecycle.py",
            )
        )
        if all(path.is_file() and not path.is_symlink() for path in hidden_components):
            actual_hidden_digest = canonical_raw_component_set_digest(
                hidden_components
            )
            if (
                readiness_inputs.get("hidden_freeze_protocol_digest")
                != actual_hidden_digest
            ):
                errors.append(
                    f"{label}: hidden_freeze_protocol_digest does not match its public components"
                )
        else:
            errors.append(f"{label}: hidden-freeze protocol components are unavailable")
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
    expected_canary_refs = required_early_evaluation_slice_refs(
        alignment,
        new_refs,
        direction_preview_enabled=requires_direction_preview(iteration),
    )
    canary_refs: list[str] = []
    canary_cases: list[str] = []
    if defer_early_evaluation:
        expected_canary_refs = set()
    if expected_canary_refs and not isinstance(canary_bindings, dict):
        errors.append(
            f"{label}: early_hidden_canary_bindings must cover every pre-final Slice"
        )
    elif not defer_early_evaluation and isinstance(canary_bindings, dict):
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
            if binding.get("burn_rule") != (
                "product-change-between-disclosure-and-slice-result-seal-"
                "burns-canary-and-preserves-result"
            ):
                errors.append(
                    f"{label}: early hidden canary must freeze the disclosure-to-Result-seal burn rule"
                )
            for field in ("project_manifest_digest", "suite_digest"):
                value = binding.get(field)
                valid_user_held_value = (
                    user_held_live and value == USER_HELD_LIVE_UNDISCLOSED
                )
                if not valid_user_held_value and (
                    not isinstance(value, str)
                    or re.fullmatch(r"sha256:[0-9a-f]{64}", value) is None
                ):
                    errors.append(
                        f"{label}: early hidden canary {field} must be an exact sha256 digest"
                        " or the closed user-held undisclosed marker"
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
    require_rejected_slice_sequence: bool = False,
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
    if requires_reflection_gate(iteration):
        errors.extend(
            validate_planned_assumption_catalog(
                by_id.get(f"{iteration}-PROPOSAL"),
                manifest,
                label,
            )
        )
    capability_path_ref = alignment.get("capability_path_ref")
    if isinstance(capability_path_ref, str):
        capability_path = by_id.get(capability_path_ref)
        if (
            capability_path is None
            or capability_path.metadata.get("kind") != "roadmap-milestone"
            or capability_path.metadata.get("authority") != "planning-only"
        ):
            errors.append(
                f"{label}: capability_path_ref must reference a planning-only roadmap milestone"
            )
        else:
            capability_step = alignment.get("capability_path_step")
            registered_steps = set(
                re.findall(
                    r"(?m)^\|\s*`(step-[a-z0-9-]+)`\s*\|",
                    capability_path.body,
                )
            )
            if (
                not isinstance(capability_step, str)
                or capability_step not in registered_steps
            ):
                errors.append(
                    f"{label}: capability_path_step must reference a registered Step ID in {capability_path_ref}"
                )

    predecessor_refs = manifest_resolved_sequence_items(
        text, "product_goal_alignment", "predecessor_result_refs"
    ) or []
    current_number = iteration_number(iteration)
    for reference in predecessor_refs:
        target = by_id.get(reference)
        target_number = iteration_number(
            "" if target is None else target.metadata.get("iteration", "")
        )
        valid_acceptance = (
            target is not None
            and target.metadata.get("kind") == "iteration-acceptance"
            and str(target.metadata.get("status", "")) in FINAL_ITERATION_STATUSES
        )
        valid_failed_redirect = (
            target is not None
            and target.metadata.get("kind") == "iteration-result"
            and target.metadata.get("status") == "failed-preserved"
        )
        if not (
            (valid_acceptance or valid_failed_redirect)
            and current_number is not None
            and target_number is not None
            and target_number < current_number
        ):
            errors.append(
                f"{label}: predecessor_result_refs item must reference an earlier Acceptance or failed-preserved Result: {reference}"
            )

    accepted_refs = manifest_resolved_sequence_items(
        text, "product_goal_alignment", "accepted_capability_refs"
    ) or []
    if not set(accepted_refs).issubset(set(predecessor_refs)):
        errors.append(
            f"{label}: accepted_capability_refs must be included in predecessor_result_refs"
        )
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
        if valid_prior_acceptance:
            target_iteration = str(target.metadata.get("iteration", ""))
            target_index = by_id.get(f"{target_iteration}-INDEX")
            if (
                target_index is not None
                and target_index.metadata.get("kind") == "iteration-index"
                and str(target_index.metadata.get("status", "")) == "rejected"
            ):
                valid_prior_acceptance = False
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
                manifest_text=text,
                verify_current_contract_fileset=not (
                    require_completed_slice_sequence
                    or require_rejected_slice_sequence
                ),
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
    reflection_by_slice: dict[str, dict[str, object]] = {}
    if requires_reflection_gate(iteration):
        errors.extend(
            validate_reflection_gate_bindings(
                alignment, new_refs, blocking_case_ids, label
            )
        )
        reflection_by_slice = reflection_gate_bindings_by_slice(alignment)
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
        direction_preview_binding = alignment.get("direction_preview_binding")
        if (
            isinstance(direction_preview_binding, dict)
            and direction_preview_binding.get("new_slice_ref") == reference
        ):
            direction_preview_case = direction_preview_binding.get("case_id")
            if isinstance(direction_preview_case, str):
                required_owned.add(direction_preview_case)
                if (
                    target.metadata.get(
                        "product_goal_direction_preview_checkpoint_id"
                    )
                    != direction_preview_case
                ):
                    errors.append(
                        f"{target.relative_path}: product_goal_direction_preview_checkpoint_id must match the owned Manifest binding"
                    )
        if requires_reflection_gate(iteration):
            reflection_binding = reflection_by_slice.get(reference)
            reflection_case = (
                reflection_binding.get("case_id")
                if isinstance(reflection_binding, dict)
                else None
            )
            if not isinstance(reflection_case, str):
                errors.append(
                    f"{target.relative_path}: Slice is missing its Manifest reflection Gate binding"
                )
            else:
                required_owned.add(reflection_case)
                if (
                    target.metadata.get("product_goal_reflection_gate_case_id")
                    != reflection_case
                ):
                    errors.append(
                        f"{target.relative_path}: product_goal_reflection_gate_case_id must match the owned Manifest binding"
                    )
            if isinstance(reflection_binding, dict):
                conditional_falsifiers = reflection_binding.get(
                    "conditional_falsifier_bindings"
                )
                if isinstance(conditional_falsifiers, dict):
                    for conditional_falsifier in conditional_falsifiers.values():
                        if not isinstance(conditional_falsifier, dict):
                            continue
                        conditional_case = conditional_falsifier.get("case_id")
                        if isinstance(conditional_case, str):
                            required_owned.add(conditional_case)
            early_canary_bindings = alignment.get("early_hidden_canary_bindings")
            if isinstance(early_canary_bindings, dict):
                for early_binding in early_canary_bindings.values():
                    if (
                        isinstance(early_binding, dict)
                        and early_binding.get("new_slice_ref") == reference
                    ):
                        for field in ("case_id", "negative_case_id"):
                            early_case = early_binding.get(field)
                            if isinstance(early_case, str):
                                required_owned.add(early_case)
            for early_field in (
                "early_comparison_binding",
                "early_diagnostic_binding",
            ):
                early_binding = alignment.get(early_field)
                if (
                    isinstance(early_binding, dict)
                    and early_binding.get("new_slice_ref") == reference
                    and isinstance(early_binding.get("case_id"), str)
                ):
                    required_owned.add(str(early_binding["case_id"]))
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
                f"{target.relative_path}: Slice gate Cases must include its owned cross-domain, Web, ad-hoc, early-evaluation, conditional-falsifier and reflection Cases"
            )

    checkpoint_bindings: list[tuple[str, dict[str, object]]] = []
    for metadata_field, binding_field in (
        (
            "product_goal_direction_preview_checkpoint_id",
            "direction_preview_binding",
        ),
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
                require_rejected=require_rejected_slice_sequence,
            )
        )

    for case_id in blocking_case_ids:
        errors.extend(validate_blocking_verification_case(verification, case_id))
    return errors


def validate_slice_reflection_result(
    target: Document,
    result: Document,
    binding: dict[str, object] | None,
    manifest_slice: dict[str, object],
    verification: Document | None,
    label: str,
    *,
    blocked: bool,
    assumption_expectations: dict[str, str] | None = None,
    assumption_catalog_digest: str | None = None,
) -> list[str]:
    errors: list[str] = []
    reflection_catalog_required = requires_reflection_gate(
        str(target.metadata.get("iteration", ""))
    )
    if reflection_catalog_required and (
        not isinstance(assumption_expectations, dict)
        or not assumption_expectations
    ):
        errors.append(
            f"{label}: {target.identifier} reflection validation requires the frozen assumption catalog"
        )
    if reflection_catalog_required and (
        not isinstance(assumption_catalog_digest, str)
        or re.fullmatch(r"sha256:[0-9a-f]{64}", assumption_catalog_digest) is None
    ):
        errors.append(
            f"{label}: {target.identifier} reflection validation requires an exact critical_assumption_catalog_digest"
        )
    if not isinstance(binding, dict):
        return [f"{label}: {target.identifier} is missing its reflection Gate binding"]
    case_id = binding.get("case_id")
    if not isinstance(case_id, str):
        return [f"{label}: {target.identifier} reflection Gate has no valid case_id"]
    if result.metadata.get("reflection_gate_case_id") != case_id:
        errors.append(
            f"{label}: {target.identifier} Result reflection_gate_case_id must equal {case_id}"
        )
    if result.metadata.get("reflection_gate_status") != "PASS":
        errors.append(
            f"{label}: {target.identifier} Result reflection_gate_status must equal PASS"
        )
    if (
        assumption_catalog_digest is not None
        and result.metadata.get("critical_assumption_catalog_digest")
        != assumption_catalog_digest
    ):
        errors.append(
            f"{label}: {target.identifier} Result must bind the frozen critical_assumption_catalog_digest"
        )
    if result.metadata.get("reflection_decision_owner") != binding.get(
        "decision_owner"
    ):
        errors.append(
            f"{label}: {target.identifier} Result reflection_decision_owner must match the Manifest binding"
        )
    decision_ref = result.metadata.get("reflection_decision_ref")
    if not isinstance(decision_ref, str) or re.fullmatch(
        r"codex-user-message:sha256:[0-9a-f]{64}", decision_ref
    ) is None:
        errors.append(
            f"{label}: {target.identifier} Result reflection_decision_ref must bind an exact user message digest"
        )
    if result.metadata.get("reflection_issue_class") not in REFLECTION_ISSUE_CLASSES:
        errors.append(
            f"{label}: {target.identifier} Result reflection_issue_class is invalid"
        )
    if result.metadata.get("reflection_issue_scope") not in REFLECTION_ISSUE_SCOPES:
        errors.append(
            f"{label}: {target.identifier} Result reflection_issue_scope is invalid"
        )
    if blocked and result.metadata.get("reflection_issue_class") == "none":
        errors.append(
            f"{label}: blocked {target.identifier} reflection_issue_class must identify the failure class"
        )
    if blocked and result.metadata.get("reflection_issue_scope") == "none":
        errors.append(
            f"{label}: blocked {target.identifier} reflection_issue_scope must identify individual or systemic impact"
        )
    report_digest = result.metadata.get("reflection_report_digest")
    valid_report_digest = isinstance(report_digest, str) and re.fullmatch(
        r"sha256:[0-9a-f]{64}", report_digest
    ) is not None
    if not valid_report_digest:
        errors.append(
            f"{label}: {target.identifier} Result reflection_report_digest must be an exact sha256 digest"
        )
    decision = result.metadata.get("reflection_decision")
    if blocked:
        if decision not in {"REDIRECT", "REJECT"}:
            errors.append(
                f"{label}: blocked {target.identifier} reflection_decision must equal REDIRECT or REJECT"
            )
    elif decision != binding.get("success_decision"):
        errors.append(
            f"{label}: completed {target.identifier} reflection_decision must equal its Manifest success_decision"
        )
    if manifest_slice.get("reflection_decision") != decision:
        errors.append(
            f"{label}: development.slices.{target.identifier}.reflection_decision must match its Result"
        )
    reflection_heading_count = len(
        re.findall(
            r"(?m)^[ ]{0,3}##[ \t]+Architecture reflection and continuation decision[ \t]*#*[ \t]*$",
            result.body,
        )
    )
    if reflection_heading_count != 1:
        errors.append(
            f"{label}: {target.identifier} Result must contain exactly one Architecture reflection and continuation decision section"
        )
    section = markdown_section_body(
        result, "Architecture reflection and continuation decision"
    )
    if (
        section is not None
        and valid_report_digest
        and report_digest
        != "sha256:" + hashlib.sha256(section.encode("utf-8")).hexdigest()
    ):
        errors.append(
            f"{label}: {target.identifier} Result reflection_report_digest must bind the exact reflection section"
        )
    if not has_substantive_markdown_content(section):
        errors.append(
            f"{label}: {target.identifier} Result must contain a substantive Architecture reflection and continuation decision section"
        )
    else:
        assumption_verdicts: dict[str, str] = {}
        owned_case_ids = {
            str(item)
            for item in target.metadata.get("product_goal_slice_gate_case_ids", [])
        }
        for subsection_name in REFLECTION_RESULT_REQUIRED_SUBSECTIONS:
            subsection = markdown_subsection_body(section, subsection_name)
            if not has_substantive_markdown_content(subsection):
                errors.append(
                    f"{label}: {target.identifier} reflection subsection is missing or empty: {subsection_name}"
                )
        due_assumption_ids = resolved_assumption_ids(binding.get("assumption_ids"))
        assumption_ids = list(due_assumption_ids)
        triggered_falsifier_cases: dict[str, str] = {}
        conditional_falsifiers = binding.get("conditional_falsifier_bindings")
        if blocked and isinstance(conditional_falsifiers, dict):
            for conditional_falsifier in conditional_falsifiers.values():
                if not isinstance(conditional_falsifier, dict):
                    continue
                conditional_assumption = conditional_falsifier.get("assumption_id")
                conditional_case = conditional_falsifier.get("case_id")
                if not isinstance(conditional_assumption, str) or not isinstance(
                    conditional_case, str
                ):
                    continue
                conditional_rows = (
                    markdown_table_case_rows(verification.body, conditional_case)
                    if verification is not None
                    else []
                )
                conditional_verdict = (
                    blocking_case_status_verdict(conditional_rows[0][6])
                    if len(conditional_rows) == 1
                    and len(conditional_rows[0]) == 7
                    else None
                )
                if conditional_verdict == "FAIL":
                    assumption_ids.append(conditional_assumption)
                    triggered_falsifier_cases[
                        conditional_assumption
                    ] = conditional_case
        if assumption_ids:
            for assumption_id in assumption_ids:
                rows = markdown_table_case_rows(section, str(assumption_id))
                if len(rows) != 1 or len(rows[0]) != 5:
                    errors.append(
                        f"{label}: {target.identifier} must record exactly one five-column verdict row for {assumption_id}"
                    )
                    continue
                row = rows[0]
                if assumption_expectations is not None:
                    expected_statement = assumption_expectations.get(assumption_id)
                    if expected_statement is None or row[1] != expected_statement:
                        errors.append(
                            f"{label}: {target.identifier} {assumption_id} Expected must exactly match the frozen Proposal assumption statement"
                        )
                for column_name, value in zip(
                    ("expected", "evidence", "impact"),
                    (row[1], row[2], row[4]),
                    strict=True,
                ):
                    if (
                        not value
                        or is_pending(value)
                        or is_absent_evidence(value)
                        or has_unresolved_placeholder(value)
                    ):
                        errors.append(
                            f"{label}: {target.identifier} {assumption_id} {column_name} must be resolved"
                        )
                normalized_verdict = row[3].upper()
                if normalized_verdict not in REFLECTION_ASSUMPTION_VERDICTS:
                    errors.append(
                        f"{label}: {target.identifier} {assumption_id} verdict must be SUPPORTED, FALSIFIED or UNRESOLVED"
                    )
                else:
                    assumption_verdicts[assumption_id] = normalized_verdict
                evidence_case_ids = [
                    item.strip().strip("`") for item in row[2].split(",")
                ]
                triggered_case = triggered_falsifier_cases.get(assumption_id)
                if triggered_case is not None and (
                    normalized_verdict not in {"FALSIFIED", "UNRESOLVED"}
                    or triggered_case not in evidence_case_ids
                ):
                    errors.append(
                        f"{label}: {target.identifier} triggered early falsifier {triggered_case} requires a FALSIFIED or UNRESOLVED {assumption_id} row citing that Case"
                    )
                if (
                    not evidence_case_ids
                    or len(evidence_case_ids) != len(set(evidence_case_ids))
                    or any(
                        re.fullmatch(
                            r"V-(?:PRE-)?[A-Z0-9]+(?:-[A-Z0-9]+)*", item
                        )
                        is None
                        for item in evidence_case_ids
                    )
                ):
                    errors.append(
                        f"{label}: {target.identifier} {assumption_id} exact evidence must be unique Verification Case IDs"
                    )
                else:
                    evidence_has_fail = False
                    for evidence_case_id in evidence_case_ids:
                        if (
                            evidence_case_id == case_id
                            or evidence_case_id.startswith("V-REFLECT-")
                        ):
                            errors.append(
                                f"{label}: {target.identifier} {assumption_id} must not use a reflection Case as self-evidence"
                            )
                            continue
                        if evidence_case_id not in owned_case_ids:
                            errors.append(
                                f"{label}: {target.identifier} {assumption_id} evidence Case must be owned by the Slice: {evidence_case_id}"
                            )
                            continue
                        if verification is not None:
                            evidence_rows = markdown_table_case_rows(
                                verification.body, evidence_case_id
                            )
                            if len(evidence_rows) == 1 and len(evidence_rows[0]) == 7:
                                evidence_status_verdict = (
                                    blocking_case_status_verdict(
                                        evidence_rows[0][6]
                                    )
                                )
                                if evidence_status_verdict == "FAIL":
                                    evidence_has_fail = True
                        errors.extend(
                            validate_blocking_verification_case(
                                verification,
                                evidence_case_id,
                                require_pass=not blocked,
                                require_executed=True,
                                expected_evidence=(
                                    f"{result.identifier}#{evidence_case_id}"
                                ),
                            )
                        )
                    if (
                        blocked
                        and normalized_verdict in {"FALSIFIED", "UNRESOLVED"}
                        and not evidence_has_fail
                    ):
                        errors.append(
                            f"{label}: {target.identifier} {assumption_id} {normalized_verdict} must bind at least one executed FAIL Case"
                        )
        decision_subsection = markdown_subsection_body(
            section, "Decision and rationale"
        )
        body_decisions = (
            re.findall(
                r"(?m)^[ ]{0,3}Decision:\s*(CONTINUE|ACCEPT|REDIRECT|REJECT)\s*$",
                decision_subsection,
            )
            if decision_subsection is not None
            else []
        )
        if len(body_decisions) != 1:
            errors.append(
                f"{label}: {target.identifier} reflection Decision and rationale must contain exactly one Decision line"
            )
        elif body_decisions[0] != decision:
            errors.append(
                f"{label}: {target.identifier} reflection body Decision must match Result metadata and Manifest"
            )
        all_body_decisions = re.findall(
            r"(?m)^[ ]{0,3}Decision:\s*(CONTINUE|ACCEPT|REDIRECT|REJECT)\s*$",
            section,
        )
        if len(all_body_decisions) != 1:
            errors.append(
                f"{label}: {target.identifier} exact reflection section must contain exactly one Decision line in total"
            )
        decision_owner_subsection = decision_subsection or ""
        body_decision_owners = re.findall(
            r"(?m)^[ ]{0,3}Decision owner:\s*(\S(?:.*\S)?)\s*$",
            decision_owner_subsection,
        )
        if len(body_decision_owners) != 1:
            errors.append(
                f"{label}: {target.identifier} reflection Decision and rationale must contain exactly one Decision owner line"
            )
        elif body_decision_owners[0] != result.metadata.get(
            "reflection_decision_owner"
        ):
            errors.append(
                f"{label}: {target.identifier} reflection body Decision owner must match Result metadata and Manifest"
            )
        all_body_decision_owners = re.findall(
            r"(?m)^[ ]{0,3}Decision owner:\s*(\S(?:.*\S)?)\s*$",
            section,
        )
        if len(all_body_decision_owners) != 1:
            errors.append(
                f"{label}: {target.identifier} exact reflection section must contain exactly one Decision owner line in total"
            )
        body_decision_refs = re.findall(
            r"(?m)^[ ]{0,3}Decision ref:\s*(codex-user-message:sha256:[0-9a-f]{64})\s*$",
            decision_subsection or "",
        )
        all_body_decision_refs = re.findall(
            r"(?m)^[ ]{0,3}Decision ref:\s*(codex-user-message:sha256:[0-9a-f]{64})\s*$",
            section,
        )
        if len(body_decision_refs) != 1 or len(all_body_decision_refs) != 1:
            errors.append(
                f"{label}: {target.identifier} exact reflection section must contain exactly one Decision ref line in the decision subsection"
            )
        elif body_decision_refs[0] != decision_ref:
            errors.append(
                f"{label}: {target.identifier} reflection body Decision ref must match Result metadata"
            )
        if decision in {"CONTINUE", "ACCEPT"} and due_assumption_ids and any(
            assumption_verdicts.get(assumption_id) != "SUPPORTED"
            for assumption_id in due_assumption_ids
        ):
            errors.append(
                f"{label}: {target.identifier} {decision} requires every bound critical assumption verdict to be SUPPORTED"
            )
        if blocked and not any(
            assumption_verdicts.get(assumption_id) in {"FALSIFIED", "UNRESOLVED"}
            for assumption_id in assumption_ids
        ):
            errors.append(
                f"{label}: blocked {target.identifier} requires at least one FALSIFIED or UNRESOLVED assumption backed by an executed FAIL Case"
            )
    errors.extend(
        validate_blocking_verification_case(
            verification,
            case_id,
            require_pass=True,
            expected_evidence=f"{result.identifier}#{case_id}",
        )
    )
    return errors


def validate_product_goal_slice_sequence(
    new_refs: list[str],
    by_id: dict[str, Document],
    label: str,
    *,
    manifest: dict[str, object] | None = None,
    verification: Document | None = None,
    require_completed: bool = False,
    require_rejected: bool = False,
) -> list[str]:
    """Require an active sequence or one of the two closed terminal sequences."""

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
    early_comparison_by_slice: dict[str, dict[str, object]] = {}
    reflection_by_slice: dict[str, dict[str, object]] = {}
    if isinstance(alignment, dict):
        reflection_by_slice = reflection_gate_bindings_by_slice(alignment)
        canary_bindings = alignment.get("early_hidden_canary_bindings")
        if isinstance(canary_bindings, dict):
            for binding in canary_bindings.values():
                if not isinstance(binding, dict):
                    continue
                new_slice_ref = binding.get("new_slice_ref")
                if isinstance(new_slice_ref, str):
                    early_canary_by_slice[new_slice_ref] = binding
        comparison_binding = alignment.get("early_comparison_binding")
        if isinstance(comparison_binding, dict):
            new_slice_ref = comparison_binding.get("new_slice_ref")
            if isinstance(new_slice_ref, str):
                early_comparison_by_slice[new_slice_ref] = comparison_binding
    assumption_catalog_digest: str | None = None
    assumption_expectations: dict[str, str] | None = None
    if slices and requires_reflection_gate(
        str(slices[0].metadata.get("iteration", ""))
    ):
        proposal_id = f"{slices[0].metadata.get('iteration')}-PROPOSAL"
        (
            assumption_catalog_digest,
            parsed_assumption_expectations,
            catalog_errors,
        ) = critical_assumption_catalog(by_id.get(proposal_id))
        errors.extend(catalog_errors)
        assumption_expectations = parsed_assumption_expectations
        if not isinstance(alignment, dict) or alignment.get(
            "critical_assumption_catalog_digest"
        ) != assumption_catalog_digest:
            errors.append(
                f"{label}: critical_assumption_catalog_digest must match the exact Proposal assumption catalog"
            )
        critical_assumption_ids = (
            resolved_assumption_ids(alignment.get("critical_assumption_ids"))
            if isinstance(alignment, dict)
            else []
        )
        if critical_assumption_ids != list(parsed_assumption_expectations):
            errors.append(
                f"{label}: critical_assumption_ids must exactly match the Proposal assumption catalog order"
            )
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
    blocked_indexes = [
        index for index, status in enumerate(statuses) if status == "blocked"
    ]
    if require_completed and require_rejected:
        errors.append(f"{label}: iteration cannot be both completed and rejected")
    elif require_completed:
        if any(status != "completed" for status in statuses):
            errors.append(
                f"{label}: completed iteration requires every new capability slice to be completed"
            )
    elif require_rejected:
        if len(blocked_indexes) != 1:
            errors.append(
                f"{label}: rejected iteration requires exactly one blocked new capability slice"
            )
        else:
            blocked_index = blocked_indexes[0]
            if any(status != "completed" for status in statuses[:blocked_index]):
                errors.append(
                    f"{label}: slices before the blocked slice must be completed in Manifest order"
                )
            if any(status != "proposed" for status in statuses[blocked_index + 1 :]):
                errors.append(
                    f"{label}: slices after the blocked slice must remain proposed"
                )
        if active_indexes:
            errors.append(f"{label}: rejected iteration must not have an active slice")
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
                if require_completed or require_rejected or len(active_indexes) != 1
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

    seen_authorization_refs: set[str] = set()
    decision_forbidden_refs: set[str] = set()
    seen_reflection_decision_refs: set[str] = set()
    top_authorized_at_value: datetime | None = None
    previous_slice_authorized_at: datetime | None = None
    if isinstance(alignment, dict):
        positive_value_freeze_receipt = alignment.get(
            "positive_value_freeze_receipt_ref"
        )
        if isinstance(positive_value_freeze_receipt, str) and re.fullmatch(
            r"codex-user-message:sha256:[0-9a-f]{64}",
            positive_value_freeze_receipt,
        ) is not None:
            decision_forbidden_refs.add(positive_value_freeze_receipt)
    if manifest is not None:
        top_authorization = manifest.get("authorization")
        top_authorization_ref = (
            top_authorization.get("authorization_ref")
            if isinstance(top_authorization, dict)
            else None
        )
        if isinstance(top_authorization_ref, str) and re.fullmatch(
            r"codex-user-message:sha256:[0-9a-f]{64}", top_authorization_ref
        ) is not None:
            decision_forbidden_refs.add(top_authorization_ref)
        top_authorized_at = (
            top_authorization.get("authorized_at")
            if isinstance(top_authorization, dict)
            else None
        )
        if isinstance(top_authorized_at, str):
            try:
                top_authorized_at_value = datetime.fromisoformat(
                    top_authorized_at.replace("Z", "+00:00")
                )
            except ValueError:
                top_authorized_at_value = None
    for index, target in enumerate(slices):
        reflection_result: Document | None = None
        status = statuses[index]
        authority = target.metadata.get("authority")
        coding_input_value = target.metadata.get("coding_input", "")
        coding_input = is_true(coding_input_value)
        if (
            require_rejected
            and str(coding_input_value).strip().lower() != "false"
        ):
            errors.append(
                f"{target.relative_path}: rejected iteration slices must use coding_input false"
            )
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
        elif status == "blocked" and (
            authority != "development-evidence" or coding_input
        ):
            errors.append(
                f"{target.relative_path}: blocked slice must use development-evidence with coding_input false"
            )
        elif status not in {
            "proposed",
            "authorized",
            "in-progress",
            "completed",
            "blocked",
        }:
            errors.append(
                f"{target.relative_path}: slice status is invalid for sequential development"
            )

        manifest_slice = development_slices.get(target.identifier)
        if isinstance(manifest_slice, dict) and status in {
            "authorized",
            "in-progress",
            "completed",
            "blocked",
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
            else:
                try:
                    authorized_at_value = datetime.fromisoformat(
                        authorized_at.replace("Z", "+00:00")
                    )
                except ValueError:
                    errors.append(
                        f"{label}: {status} {target.identifier} authorized_at must be a real ISO-8601 timestamp"
                    )
                else:
                    if (
                        top_authorized_at_value is not None
                        and authorized_at_value < top_authorized_at_value
                    ):
                        errors.append(
                            f"{label}: {target.identifier} authorization cannot precede Readiness authorization"
                        )
                    if (
                        previous_slice_authorized_at is not None
                        and authorized_at_value <= previous_slice_authorized_at
                    ):
                        errors.append(
                            f"{label}: Slice authorization timestamps must be strictly increasing"
                        )
                    previous_slice_authorized_at = authorized_at_value
            authorization_ref = manifest_slice.get("authorization_ref")
            if not isinstance(authorization_ref, str) or re.fullmatch(
                r"codex-user-message:sha256:[0-9a-f]{64}", authorization_ref
            ) is None:
                errors.append(
                    f"{label}: {status} {target.identifier} authorization_ref must bind an exact user message digest"
                )
            elif authorization_ref in seen_authorization_refs:
                errors.append(
                    f"{label}: {target.identifier} must use a new user authorization message after the prior Slice reflection"
                )
            else:
                seen_authorization_refs.add(authorization_ref)
                decision_forbidden_refs.add(authorization_ref)

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
            if (
                require_rejected
                and str(manifest_coding_input).strip().lower() != "false"
            ):
                errors.append(
                    f"{label}: rejected development.slices.{target.identifier}.coding_input must be false"
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
                if (
                    requires_reflection_gate(target.metadata.get("iteration", ""))
                    and manifest_slice.get("reflection_decision") != "not-executed"
                ):
                    errors.append(
                        f"{label}: proposed {target.identifier} reflection_decision must be not-executed"
                    )
                if requires_reflection_gate(target.metadata.get("iteration", "")):
                    expected_prerequisite = (
                        "none-first-slice" if index == 0 else "not-executed"
                    )
                    if (
                        manifest_slice.get("reflection_prerequisite_result")
                        != expected_prerequisite
                    ):
                        errors.append(
                            f"{label}: proposed {target.identifier} reflection_prerequisite_result must equal {expected_prerequisite}"
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
                if (
                    requires_reflection_gate(target.metadata.get("iteration", ""))
                    and manifest_slice.get("reflection_decision")
                    not in {"not-executed", "in-progress"}
                ):
                    errors.append(
                        f"{label}: active {target.identifier} reflection_decision must be not-executed or in-progress"
                    )
                if (
                    requires_reflection_gate(target.metadata.get("iteration", ""))
                    and index == 0
                    and manifest_slice.get("reflection_prerequisite_result")
                    != "none-first-slice"
                ):
                    errors.append(
                        f"{label}: first active Slice reflection_prerequisite_result must equal none-first-slice"
                    )
            elif status == "blocked":
                result_ref = manifest_slice.get("result")
                result = by_id.get(result_ref) if isinstance(result_ref, str) else None
                reflection_result = result
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
                    or result.metadata.get("status") != "failed-preserved"
                    or result.metadata.get("authority") != "execution-evidence"
                    or target.identifier not in dependencies
                    or f"{target.metadata.get('iteration')}-VERIFICATION"
                    not in dependencies
                ):
                    errors.append(
                        f"{label}: blocked {target.identifier} must bind same-iteration failed-preserved execution evidence that depends on the Slice and Verification"
                    )
                else:
                    freeze_digest = manifest_slice.get("product_code_freeze_digest")
                    if not isinstance(freeze_digest, str) or re.fullmatch(
                        r"sha256:[0-9a-f]{64}", freeze_digest
                    ) is None:
                        errors.append(
                            f"{label}: blocked {target.identifier} must bind an exact product_code_freeze_digest"
                        )
                    elif result.metadata.get("product_code_freeze_digest") != freeze_digest:
                        errors.append(
                            f"{label}: blocked {target.identifier} Result must bind its exact product code freeze"
                        )
                    comparison_binding = early_comparison_by_slice.get(
                        target.identifier
                    )
                    comparison_case = (
                        comparison_binding.get("case_id")
                        if isinstance(comparison_binding, dict)
                        else None
                    )
                    comparison_rows = (
                        markdown_table_case_rows(verification.body, comparison_case)
                        if verification is not None
                        and isinstance(comparison_case, str)
                        else []
                    )
                    comparison_verdict = (
                        blocking_case_status_verdict(comparison_rows[0][6])
                        if len(comparison_rows) == 1
                        and len(comparison_rows[0]) == 7
                        else None
                    )
                    if (
                        isinstance(alignment, dict)
                        and comparison_verdict in {"PASS", "FAIL"}
                    ):
                        errors.extend(
                            validate_positive_value_result(
                                result,
                                alignment,
                                label,
                                require_pass=False,
                                expected_case_id=str(comparison_case),
                            )
                        )
                    if requires_reflection_gate(
                        target.metadata.get("iteration", "")
                    ):
                        errors.extend(
                            validate_slice_reflection_result(
                                target,
                                result,
                                reflection_by_slice.get(target.identifier),
                                manifest_slice,
                                verification,
                                label,
                                blocked=True,
                                assumption_expectations=assumption_expectations,
                                assumption_catalog_digest=assumption_catalog_digest,
                            )
                        )
            elif status == "completed":
                result_ref = manifest_slice.get("result")
                result = by_id.get(result_ref) if isinstance(result_ref, str) else None
                reflection_result = result
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
                        disclosure_receipt = result.metadata.get(
                            "canary_disclosure_receipt_digest"
                        )
                        if not isinstance(disclosure_receipt, str) or re.fullmatch(
                            r"sha256:[0-9a-f]{64}", disclosure_receipt
                        ) is None:
                            errors.append(
                                f"{label}: completed {target.identifier} Result must bind an exact canary disclosure receipt"
                            )
                        if result.metadata.get(
                            "canary_product_change_before_result_seal_count"
                        ) != 0:
                            errors.append(
                                f"{label}: completed {target.identifier} disclosure-to-Result-seal product change count must equal zero"
                            )
                        if result.metadata.get(
                            "canary_capsule_consumption_status"
                        ) != "CONSUMED_AFTER_RESULT_SEAL":
                            errors.append(
                                f"{label}: completed {target.identifier} must consume its canary after the Result seal"
                            )

                    if (
                        target.identifier in early_comparison_by_slice
                        and isinstance(alignment, dict)
                    ):
                        comparison_case = early_comparison_by_slice[
                            target.identifier
                        ].get("case_id")
                        errors.extend(
                            validate_positive_value_result(
                                result,
                                alignment,
                                label,
                                expected_case_id=(
                                    str(comparison_case)
                                    if isinstance(comparison_case, str)
                                    else None
                                ),
                            )
                        )

                    if requires_reflection_gate(
                        target.metadata.get("iteration", "")
                    ):
                        errors.extend(
                            validate_slice_reflection_result(
                                target,
                                result,
                                reflection_by_slice.get(target.identifier),
                                manifest_slice,
                                verification,
                                label,
                                blocked=False,
                                assumption_expectations=assumption_expectations,
                                assumption_catalog_digest=assumption_catalog_digest,
                            )
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

            if (
                requires_reflection_gate(target.metadata.get("iteration", ""))
                and status in {"completed", "blocked"}
                and reflection_result is not None
            ):
                if target.identifier in early_comparison_by_slice:
                    adjudication_receipt = reflection_result.metadata.get(
                        "positive_value_adjudication_receipt_ref"
                    )
                    if adjudication_receipt in decision_forbidden_refs or (
                        adjudication_receipt in seen_reflection_decision_refs
                    ):
                        errors.append(
                            f"{label}: {target.identifier} positive value adjudication must use a new message after prior authorizations and decisions"
                        )
                reflection_decision_ref = reflection_result.metadata.get(
                    "reflection_decision_ref"
                )
                if isinstance(reflection_decision_ref, str) and re.fullmatch(
                    r"codex-user-message:sha256:[0-9a-f]{64}",
                    reflection_decision_ref,
                ) is not None:
                    if reflection_decision_ref in decision_forbidden_refs:
                        errors.append(
                            f"{label}: {target.identifier} reflection_decision_ref must use a new user message after all prior authorizations"
                        )
                    if reflection_decision_ref in seen_reflection_decision_refs:
                        errors.append(
                            f"{label}: each Slice reflection_decision_ref must be unique"
                        )
                    seen_reflection_decision_refs.add(reflection_decision_ref)
                    decision_forbidden_refs.add(reflection_decision_ref)
                adjudication_receipt = reflection_result.metadata.get(
                    "positive_value_adjudication_receipt_ref"
                )
                if isinstance(adjudication_receipt, str) and re.fullmatch(
                    r"codex-user-message:sha256:[0-9a-f]{64}",
                    adjudication_receipt,
                ) is not None:
                    decision_forbidden_refs.add(adjudication_receipt)

        if index > 0:
            dependencies = target.metadata.get("depends_on", [])
            if not isinstance(dependencies, list) or new_refs[index - 1] not in dependencies:
                errors.append(
                    f"{target.relative_path}: sequential slice must depend on {new_refs[index - 1]}"
                )
            if (
                requires_reflection_gate(target.metadata.get("iteration", ""))
                and status != "proposed"
                and isinstance(manifest_slice, dict)
            ):
                previous_slice_ref = new_refs[index - 1]
                previous_manifest_slice = development_slices.get(previous_slice_ref)
                previous_result_ref = (
                    previous_manifest_slice.get("result")
                    if isinstance(previous_manifest_slice, dict)
                    else None
                )
                if (
                    not isinstance(previous_result_ref, str)
                    or is_pending(previous_result_ref)
                    or is_absent_evidence(previous_result_ref)
                    or previous_result_ref in {"not-executed", "in-progress"}
                ):
                    errors.append(
                        f"{label}: {target.identifier} requires the prior Slice exact reflection Result before authorization"
                    )
                else:
                    if (
                        manifest_slice.get("reflection_prerequisite_result")
                        != previous_result_ref
                    ):
                        errors.append(
                            f"{label}: {target.identifier} reflection_prerequisite_result must equal {previous_result_ref}"
                        )
                    if (
                        not isinstance(dependencies, list)
                        or previous_result_ref not in dependencies
                    ):
                        errors.append(
                            f"{target.relative_path}: authorized follow-up Slice must depend on prior reflection Result {previous_result_ref}"
                        )
                    previous_result = by_id.get(previous_result_ref)
                    if (
                        previous_result is None
                        or previous_result.metadata.get("reflection_gate_status")
                        != "PASS"
                        or previous_result.metadata.get("reflection_decision")
                        != "CONTINUE"
                    ):
                        errors.append(
                            f"{label}: {target.identifier} prior reflection Result must be PASS with decision CONTINUE"
                        )
                    elif manifest_slice.get("authorization_ref") != (
                        previous_result.metadata.get("reflection_decision_ref")
                    ):
                        errors.append(
                            f"{label}: {target.identifier} authorization_ref must equal the prior reflection decision_ref"
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
        iteration_rejected = (
            index is not None
            and str(index.metadata.get("status", "")) == "rejected"
        )
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
            if requires_reflection_gate(iteration):
                for planned_document in (
                    *(item for item in (proposal, readiness) if item is not None),
                    *slice_candidates,
                ):
                    kind = str(planned_document.metadata.get("kind", ""))
                    for section in empty_required_sections(
                        planned_document,
                        REFLECTION_GATE_REQUIRED_SECTIONS.get(kind, ()),
                    ):
                        errors.append(
                            f"{planned_document.relative_path}: planned reflection section is missing or empty: {section}"
                        )
                errors.extend(
                    validate_product_goal_alignment_documents(
                        proposal, verification, iteration
                    )
                )
                manifest = directory / "manifest.yaml"
                if not manifest.exists():
                    errors.append(
                        f"{iteration}: proposed reflection-gated iteration is missing manifest.yaml"
                    )
                else:
                    label = _path_label(manifest)
                    try:
                        manifest_text = manifest.read_text(encoding="utf-8")
                        manifest_data = safe_load_manifest(manifest_text)
                    except (OSError, UnicodeError, SafeYamlError) as error:
                        errors.append(
                            f"{label}: proposed reflection-gated Manifest cannot be loaded: {error}"
                        )
                    else:
                        errors.extend(
                            validate_product_goal_alignment_manifest(
                                manifest_data,
                                manifest_text,
                                label,
                                iteration,
                            )
                        )
                        errors.extend(
                            validate_product_goal_reference_targets(
                                manifest,
                                iteration,
                                documents_by_id,
                                verification=verification,
                            )
                        )
            continue

        if iteration_rejected:
            if (
                str(index.metadata.get("coding_input", "")).strip().lower()
                != "false"
            ):
                errors.append(
                    f"{index.relative_path}: rejected iteration must use coding_input false"
                )
            if acceptances:
                errors.append(
                    f"{index.relative_path}: rejected iteration must not have an accepted/completed Acceptance"
                )

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
                    manifest,
                    iteration,
                    allowed_statuses=allowed_statuses,
                    expected_status="rejected" if iteration_rejected else None,
                )
            )
            errors.extend(
                validate_product_goal_reference_targets(
                    manifest,
                    iteration,
                    documents_by_id,
                    require_execution_slice_sequence=requires_readiness,
                    require_completed_slice_sequence=(
                        not iteration_rejected
                        and bool(
                            acceptances
                            or (
                                index is not None
                                and str(index.metadata.get("status", ""))
                                in FINAL_ITERATION_STATUSES
                            )
                        )
                    ),
                    require_rejected_slice_sequence=iteration_rejected,
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
