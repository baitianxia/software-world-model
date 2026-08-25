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
PAUSED_ITERATION_STATUSES = {"paused"}
PAUSED_SLICE_STATUSES = {"paused"}
ACCEPTED_PROPOSAL_STATUSES = {"accepted", "authorized"}
ACCEPTED_READINESS_STATUSES = {"accepted", "authorized"}
FINAL_ITERATION_STATUSES = {"completed", "accepted"}
REFLECTION_DECISIONS = {"CONTINUE", "ACCEPT", "REWORK", "REDIRECT", "REJECT"}
DIRECTION_DECISION_SETS = {
    "CONTINUE,REDIRECT,REJECT",  # Historical manifests before REWORK existed.
    "CONTINUE,REWORK,REDIRECT,REJECT",
}
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
REWORK_LIFECYCLE_START_ITERATION = 10
STRICT_CODEX_BASELINE_START_ITERATION = 12
EXPERIENCE_FIRST_DELIVERY_START_ITERATION = 12
PROVIDER_ROUTE_POLICY_START_ITERATION = 12
EXPERIENCE_FIRST_DELIVERY_SCHEMA = "EXPERIENCE_FIRST_DELIVERY@1"
PROVIDER_ROUTE_POLICY_SCHEMA = "QUALIFIED_PROVIDER_PREFERENCE@1"
ENGINEERING_CHAT_EXPERIENCE_SCHEMA = "ENGINEERING_CHAT_EXPERIENCE@1"
CONVERSATIONAL_ENGINEERING_AGENT_SCHEMA = "CONVERSATIONAL_ENGINEERING_AGENT@1"
EXPERIENCE_FIRST_FAILURE_DIAGNOSIS_ORDER = (
    "source-truth-world-model-cognition-conversation-or-task-understanding-"
    "agent-work-state-and-plan-tool-observation-and-evidence-answer-"
    "independent-review-web"
)
EXPERIENCE_FIRST_DELIVERY_PRE_ACCESS_WORK = (
    "targeted-impact-startup-safety-failure-truth-one-qualification-one-smoke-only"
)
EXPERIENCE_FIRST_DELIVERY_LIVE_ATTEMPT_UNIT = (
    "one-sealed-version-bounded-user-interaction-unit-reaching-any-external-"
    "dispatch-chat-counts-each-turn"
)
EXPERIENCE_FIRST_DELIVERY_HARD_STOP_ACTION = (
    "stop-scope-expansion-and-external-calls-narrow-and-review"
)
EXPERIENCE_FIRST_DELIVERY_NO_INCREMENT_ACTION = (
    "stop-external-reruns-and-return-to-local-diagnosis"
)
PROVIDER_ROUTE_PREFERENCE = ("VOLCENGINE_ARK", "DEEPSEEK")
PROVIDER_FALLBACK_ELIGIBLE_OUTCOMES = (
    "provider-unavailable",
    "provider-http-error",
    "provider-outcome-unknown",
    "provider-output-invalid",
    "model-review-rejected",
)
DEEPSEEK_PREFERRED_WINDOWS = (
    "00:00-09:00",
    "12:00-14:00",
    "18:00-24:00",
)
STRICT_CODEX_BASELINE_ROLE = (
    "strong-external-baseline-not-oracle-not-adjudicator"
)
STRICT_CODEX_BASELINE_EXECUTION_MODE = (
    "fresh-isolated-same-question-answer-sealed-before-disclosure"
)
STRICT_CODEX_QUALITY_METRIC = "blind-paired-answer-quality-margin"
STRICT_CODEX_QUALITY_UNIT = "quality-basis-points"
STRICT_CODEX_QUALITY_COMPARISON = "at-least"
STRICT_CODEX_ALPHA_PASS_RULE = (
    "system-absolute-pass-no-per-question-regression-and-positive-blind-quality-margin"
)
STRICT_CODEX_RESULT_COMPARISON = "strict-answer-quality-superiority"
ENGINEERING_QA_ADAPTIVE_PROTOCOL_SCHEMA = (
    "ENGINEERING_QA_ADAPTIVE_INVESTIGATION@3"
)
ENGINEERING_QA_ADAPTIVE_PROTOCOL_MODE = (
    "adaptive-cognition-guided-engineering-investigation"
)
ENGINEERING_QA_REVIEWER_VERIFICATION_SCHEMA = (
    "ENGINEERING_QA_REVIEWER_VERIFICATION_INVESTIGATION@1"
)
ENGINEERING_QA_ANSWER_HIERARCHY_SCHEMA = "ENGINEERING_QA_ANSWER_HIERARCHY@3"
ENGINEERING_QA_ABLATION_SCHEMA = "ENGINEERING_QA_COGNITION_ABLATION@1"
CONVERSATIONAL_AGENT_ABLATION_SCHEMA = "CONVERSATIONAL_AGENT_ABLATION@1"
CRITICAL_ASSUMPTION_CUTOVER_SCHEMA = (
    "ITERATION_CRITICAL_ASSUMPTION_CATALOG_CUTOVER@1"
)
CRITICAL_ASSUMPTION_CURRENT_SCHEMA = (
    "ITERATION_CRITICAL_ASSUMPTION_CATALOG@1"
)
ENGINEERING_QA_NOT_AUTHORIZED = "not-authorized"
DIRECTION_PREVIEW_PRODUCT_ENTRIES = frozenset(
    {
        "loopback-product-owned-world-model-web",
        "loopback-product-owned-engineering-qa-web",
    }
)

ITER010_CURRENT_ASSUMPTIONS: dict[str, str] = {
    "A1": "软件世界模型保持为持久、版本化、可验证、可更新的软件外部认知，提问期 Source 调查只核实、补充或纠正本 Turn 认知",
    "A2": "主工程 Agent 能持续维护目标、假设、子任务和计划，依据每次观察选择 World Model/Source 受控工具并重规划，不取得直接权限",
    "A3": "每个 Turn 的 Evidence Package、自然答案与 fresh independent Review 同时保证直接答案、Citation、失败关闭和可返工性，Reviewer Finding 只回到主 Agent",
    "A4": "相同 Conversation—主 Agent—受控工具—逐 Turn Evidence/Review 协议能跨第二工程、来源组合和复杂失败泛化",
    "A5": "产品外部比较与 World Model 因果消融必须分开；current Codex 保留其真实客户端、model、reasoning、tools 和权限，只有系统的 source-only 与 full-cognition 两臂使用同一主 Agent/model/tool/budget/cache/Reviewer",
    "A6": "产品具有真正语义多轮 Conversation，而不是同 Session 的独立问答",
}
ITER010_HISTORICAL_ASSUMPTION_DIGEST = (
    "sha256:26769498135692067597a1f59e0fbbc8b82502ebd5336f7fdb033a80e3baff82"
)
ITER010_HISTORICAL_ASSUMPTIONS: dict[str, str] = {
    "A1": "保持软件世界模型作为持久、版本化外部认知而非手册或缓存，同时可让提问期 Source 调查核实、补充或纠正本题认知，并能证明完整认知不只是 locator 装饰",
    "A2": "独立 Investigation LLM 可以依据不可变原问题、exact World Model Cognition Context 和先前 Ledger 结果自适应提出下一步，而 Source Broker/Worker 能在不授予模型直接权限的情况下执行",
    "A3": "调查后密封、包内 Answer 和 Reviewer 独立补证可以同时保证直接答案、正确 Citation、失败关闭与真实首版体验",
    "A4": "相同认知—调查—Broker—Ledger—Package 协议能跨第二工程、来源组合和复杂失败模式泛化，不依赖问题、项目、关键词、符号、类、方法、fixture 或 Oracle 路由",
    "A5": "在不因调用次数裁剪调查或审核质量的前提下，完整认知与成熟源码 Agent 先通过零重大错误、boundary 正确且完整认知逐结论不退步的质量门；再以 locator-only/empty 同链为消融 control，证明完整认知有预提交质量或非 locator 调查成本增益，并计入建模成本与复用周期",
}
ITER010_HISTORICAL_GATE_CASES: dict[str, str] = {
    "V-ANSWER-001": "FAIL",
    "V-REVIEW-001": "FAIL",
    "V-XD-001": "FAIL",
    "V-EXPERIENCE-001": "FAIL",
    "V-WEB-000": "PASS",
    "V-WEB-001": "PASS",
    "V-PREVIEW-001": "FAIL",
    "V-REFLECT-001": "PASS",
}
IMMUTABLE_HISTORICAL_CASE_EVIDENCE: dict[tuple[str, str], str] = {
    (
        "ITER-010-RESULT-SLICE-001-STOP-REDIRECT",
        "V-REVIEW-001",
    ): (
        "run-028 证明仅投影/focus 仍可跳过 lead；"
        "`FINDING-010-077/078` deterministic regression closed，fresh live pending"
    ),
}
ITER010_CURRENT_CHAT_GATE_CASES = frozenset(
    {
        "V-CHAT-EXPERIENCE-001",
        "V-TIMEBOX-CHAT-001",
        "V-CHAT-QUALITY-001",
    }
)
ITER010_CURRENT_VERIFICATION_REQUIRED_PHRASES: dict[
    str, dict[str, tuple[str, ...]]
] = {
    "V-TIMEBOX-CHAT-001": {
        "Claim": ("逐 Turn live-attempt",),
        "Frozen input / oracle": ("Conversation/Turn/provider dispatch",),
        "Expected": (
            "首个 live canary 是五轮 Conversation",
            "每个 Provider-dispatched Turn 分别计 live attempt",
        ),
    },
    "V-COMP-ALPHA-001": {
        "Claim": ("主 Agent/World Model 方向信号",),
        "Frozen input / oracle": (
            "current Codex external baseline",
            "same-agent source-only",
            "same-agent full World Model cognition + source",
        ),
        "Expected": (
            "Codex 保留实际客户端/model/reasoning/tools/权限",
            "只作强外部基线，不是 Oracle/裁判",
            "只有 source-only/full-cognition 两系统臂共享同一主 Agent/model/tool/budget/cache/Reviewer",
            "独立评估者",
        ),
    },
    "V-PREVIEW-002": {
        "Claim": (
            "用户基于 A1—A3/A6 复盘、多轮 Chat 和三臂方向信号决定是否进入夯实",
        ),
        "Frozen input / oracle": ("真实 Result、限制、Findings 和假设证据",),
        "Expected": (
            "独立技术复核给出 A1—A3/A6 exact Verdict 与 A4/A5 early signal",
            "用户实际追问、纠正、深入、总结并查看三臂方向信号后决定 CONTINUE/REWORK/REDIRECT/REJECT",
        ),
    },
}
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
    "paused",
    "superseded",
}
GOAL_ALIGNED_SLICE_STATUSES = {
    "authorized",
    "in-progress",
    "completed",
    "blocked",
    "paused",
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
    "本轮相对 rejected baseline 可测缩短通用工程问答差距并证明完整 World Model Cognition 的独立价值"
)
ENGINEERING_QA_PRODUCT_GOAL_V000_FROZEN_INPUT = (
    "三个唯一 Slice Result；最终隐藏 10+2；现场题；完整认知、locator-only/empty 同链、成熟源码 Agent 三臂；新收据预提交 protocol"
)
ENGINEERING_QA_PRODUCT_GOAL_V000_EXPECTED = (
    "完整认知与成熟 Agent 先过零重大错误/boundary/逐结论质量门；完整认知再相对 locator control 达到预提交质量或非 locator 调查成本增益；"
    "计建模成本/复用周期；同一 Web/Citation/Source 隔离成立"
)
ENGINEERING_QA_PRODUCT_GOAL_V000_METADATA = {
    "product_goal_gate": "V-000",
    "product_goal_outcome": "user-visible-general-engineering-qa-delta",
    "product_goal_evaluation": "independent-hidden-plus-live-ad-hoc",
}
STRICT_CODEX_PRODUCT_GOAL_V000_CLAIM = (
    "本轮相对 baseline 可测缩短通用源码问答 MVP 差距，并在答案质量上严格超过 current Codex"
)
STRICT_CODEX_PRODUCT_GOAL_V000_FROZEN_INPUT = (
    "未参与实现的真实工程；独立持有的 held-out 和现场问题；exact current Codex identity/protocol；"
    "双方密封答案；随机匿名映射；独立盲评量表"
)
STRICT_CODEX_PRODUCT_GOAL_V000_EXPECTED = (
    "系统绝对质量 PASS；逐题无物质退步；总体答案质量差值严格为正；全体打平 FAIL；"
    "次级效率指标不得补偿；同一正式 Web 可人工验证"
)
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


def requires_strict_codex_baseline(identifier: object) -> bool:
    """Apply the strong external Codex baseline contract to new iterations only."""

    number = iteration_number(identifier)
    return number is not None and number >= STRICT_CODEX_BASELINE_START_ITERATION


def requires_experience_first_delivery_policy(identifier: object) -> bool:
    """Require the experience-first timebox for newly planned product iterations."""

    number = iteration_number(identifier)
    return (
        number is not None
        and number >= EXPERIENCE_FIRST_DELIVERY_START_ITERATION
    )


def requires_provider_route_policy(identifier: object) -> bool:
    """Require a qualified Ark-first provider route for newly planned iterations."""

    number = iteration_number(identifier)
    return number is not None and number >= PROVIDER_ROUTE_POLICY_START_ITERATION


def is_engineering_qa_adaptive_protocol(
    answer_protocol: dict[str, object],
) -> bool:
    """Identify the explicit adaptive engineering-QA protocol only."""

    return (
        answer_protocol.get("mode")
        == ENGINEERING_QA_ADAPTIVE_PROTOCOL_MODE
    )


def product_goal_v000_contract(
    iteration: object,
) -> tuple[dict[str, str], str, str, str]:
    """Return the exact user-visible product gate for the selected architecture."""

    if requires_strict_codex_baseline(iteration):
        return (
            PRODUCT_GOAL_V000_METADATA,
            STRICT_CODEX_PRODUCT_GOAL_V000_CLAIM,
            STRICT_CODEX_PRODUCT_GOAL_V000_FROZEN_INPUT,
            STRICT_CODEX_PRODUCT_GOAL_V000_EXPECTED,
        )
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


def manifest_resolved_nested_sequence_items(
    text: str, keys: tuple[str, ...]
) -> list[str] | None:
    """Resolve a scalar block sequence at an exact nested safe-YAML key path."""

    lines = text.splitlines()
    search_start = 0
    parent_indent = -1
    field_index: int | None = None
    field_indent: int | None = None
    for key_index, key in enumerate(keys):
        found = False
        for index in range(search_start, len(lines)):
            raw_line = lines[index]
            if not raw_line.strip() or raw_line.lstrip().startswith("#"):
                continue
            indentation = len(raw_line) - len(raw_line.lstrip(" "))
            if parent_indent >= 0 and indentation <= parent_indent:
                break
            match = re.fullmatch(rf"{re.escape(key)}\s*:\s*(.*)", raw_line.strip())
            if match is None or indentation <= parent_indent:
                continue
            if match.group(1):
                return None
            found = True
            search_start = index + 1
            parent_indent = indentation
            if key_index == len(keys) - 1:
                field_index = index
                field_indent = indentation
            break
        if not found:
            return None
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
        try:
            value = _parse_yaml_scalar(content[2:].strip(), 0)
        except SafeYamlError:
            return None
        if not isinstance(value, str) or has_unresolved_placeholder(value):
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


def conversational_agent_cutover_active(manifest: dict[str, object]) -> bool:
    policy = manifest.get("conversational_engineering_agent")
    return (
        isinstance(policy, dict)
        and policy.get("schema") == CONVERSATIONAL_ENGINEERING_AGENT_SCHEMA
        and policy.get("architecture_decision_ref") == "SYS-ADR-018"
    )


def resolved_csv_values(value: object) -> list[str]:
    if isinstance(value, str):
        values = [item.strip() for item in value.split(",")]
    elif isinstance(value, list):
        values = [str(item).strip() for item in value]
    else:
        return []
    if not values or any(not item for item in values) or len(values) != len(set(values)):
        return []
    return values


def critical_assumption_catalogs(
    proposal: Document | None,
    manifest: dict[str, object],
    label: str,
) -> tuple[
    str | None,
    dict[str, str],
    str | None,
    dict[str, str],
    list[str],
]:
    """Resolve current and historical catalogs without rewriting prior evidence."""

    proposal_digest, proposal_expectations, errors = critical_assumption_catalog(proposal)
    cutover = manifest.get("critical_assumption_catalog_cutover")
    if cutover is None:
        return (
            proposal_digest,
            proposal_expectations,
            proposal_digest,
            proposal_expectations,
            errors,
        )
    if not isinstance(cutover, dict):
        errors.append(
            f"{label}: critical_assumption_catalog_cutover must be a mapping"
        )
        return None, {}, proposal_digest, proposal_expectations, errors

    expected_keys = {
        "schema",
        "current_catalog_schema",
        "current_owner_ref",
        "current_assumption_ids",
        "current_assumptions",
        "current_catalog_digest",
        "historical_owner_ref",
        "historical_assumption_ids",
        "historical_assumptions",
        "historical_catalog_digest",
        "historical_readiness_ref",
        "historical_result_ref",
        "historical_case_ids",
        "historical_documents_immutable",
        "current_gate_reuses_historical_case_ids",
        "status",
    }
    errors.extend(
        validate_exact_mapping_keys(
            cutover,
            expected_keys,
            f"{label}: critical_assumption_catalog_cutover",
        )
    )
    exact_values: tuple[tuple[str, object], ...] = (
        ("schema", CRITICAL_ASSUMPTION_CUTOVER_SCHEMA),
        ("current_catalog_schema", CRITICAL_ASSUMPTION_CURRENT_SCHEMA),
        ("current_owner_ref", "SYS-ADR-018"),
        ("historical_owner_ref", "ITER-010-PROPOSAL@pre-PDR-004"),
        ("historical_readiness_ref", "ITER-010-READINESS"),
        (
            "historical_result_ref",
            "ITER-010-RESULT-SLICE-001-STOP-REDIRECT",
        ),
        ("historical_documents_immutable", True),
        ("current_gate_reuses_historical_case_ids", False),
        ("status", "current-catalog-active-history-preserved"),
    )
    for field, expected in exact_values:
        if cutover.get(field) != expected:
            errors.append(
                f"{label}: critical_assumption_catalog_cutover.{field} must equal {expected}"
            )

    current_assumptions = cutover.get("current_assumptions")
    if not isinstance(current_assumptions, dict):
        errors.append(
            f"{label}: critical_assumption_catalog_cutover.current_assumptions must be a mapping"
        )
        parsed_current: dict[str, str] = {}
    else:
        parsed_current = {
            str(key): str(value) for key, value in current_assumptions.items()
        }
        if (
            parsed_current != ITER010_CURRENT_ASSUMPTIONS
            or parsed_current != proposal_expectations
        ):
            errors.append(
                f"{label}: current assumption catalog must equal the frozen A1-A6 conversational architecture catalog"
            )
    current_ids = resolved_assumption_ids(cutover.get("current_assumption_ids"))
    if current_ids != list(ITER010_CURRENT_ASSUMPTIONS):
        errors.append(
            f"{label}: critical_assumption_catalog_cutover.current_assumption_ids must equal A1,A2,A3,A4,A5,A6"
        )
    current_digest = proposal_digest
    if cutover.get("current_catalog_digest") != current_digest:
        errors.append(
            f"{label}: critical_assumption_catalog_cutover.current_catalog_digest must bind the exact current A1-A6 catalog"
        )

    historical_assumptions = cutover.get("historical_assumptions")
    if not isinstance(historical_assumptions, dict) or {
        str(key): str(value) for key, value in historical_assumptions.items()
    } != ITER010_HISTORICAL_ASSUMPTIONS:
        errors.append(
            f"{label}: historical_assumptions must preserve the exact pre-PDR-004 A1-A5 catalog"
        )
    historical_ids = resolved_assumption_ids(
        cutover.get("historical_assumption_ids")
    )
    if historical_ids != list(ITER010_HISTORICAL_ASSUMPTIONS):
        errors.append(
            f"{label}: historical_assumption_ids must exactly match the preserved Proposal catalog"
        )
    if (
        cutover.get("historical_catalog_digest")
        != ITER010_HISTORICAL_ASSUMPTION_DIGEST
    ):
        errors.append(
            f"{label}: historical_catalog_digest must exactly match the preserved Proposal catalog"
        )
    historical_case_ids = resolved_csv_values(cutover.get("historical_case_ids"))
    if historical_case_ids != list(ITER010_HISTORICAL_GATE_CASES):
        errors.append(
            f"{label}: historical_case_ids must preserve the exact executed ITER-010 Case catalog"
        )
    return (
        current_digest,
        ITER010_CURRENT_ASSUMPTIONS.copy(),
        ITER010_HISTORICAL_ASSUMPTION_DIGEST,
        ITER010_HISTORICAL_ASSUMPTIONS.copy(),
        errors,
    )


def validate_planned_assumption_catalog(
    proposal: Document | None,
    manifest: dict[str, object],
    label: str,
) -> list[str]:
    """Reject malformed or drifting assumptions while an iteration is still proposed."""

    digest, expectations, _, _, errors = critical_assumption_catalogs(
        proposal, manifest, label
    )
    alignment = manifest.get("product_goal_alignment")
    if not isinstance(alignment, dict):
        return errors
    critical_assumption_ids = resolved_assumption_ids(
        alignment.get("critical_assumption_ids")
    )
    if critical_assumption_ids != list(expectations):
        errors.append(
            f"{label}: critical_assumption_ids must exactly match the current assumption catalog order"
        )
    supplied_digest = alignment.get("critical_assumption_catalog_digest")
    if supplied_digest != "not-frozen-proposal-only" and supplied_digest != digest:
        errors.append(
            f"{label}: proposed critical_assumption_catalog_digest must match the exact current catalog or remain the proposal-only marker"
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
    has_alpha = isinstance(alignment.get("alpha_direction_binding"), dict)
    status_label = (
        "direction-probe-non-acceptance-non-production"
        if has_alpha
        else "non-acceptance-non-production"
    )
    continuation_field = (
        "next_slice_requires_continue" if has_alpha else "hardening_requires_continue"
    )
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
        or binding.get("status_label") != status_label
        or decision_owner != "user"
        or binding.get("allowed_decisions") not in DIRECTION_DECISION_SETS
        or binding.get(continuation_field) is not True
    ):
        return None
    return str(new_slice_ref)


def resolved_alpha_direction_slice_ref(
    alignment: dict[str, object], new_refs: list[str]
) -> str | None:
    """Resolve an optional second feedback checkpoint before hardening."""

    binding = alignment.get("alpha_direction_binding")
    preview_ref = resolved_direction_preview_slice_ref(alignment, new_refs)
    if not isinstance(binding, dict) or preview_ref is None:
        return None
    preview_index = new_refs.index(preview_ref)
    alpha_ref = binding.get("new_slice_ref")
    case_id = binding.get("case_id")
    if (
        preview_index + 2 >= len(new_refs)
        or alpha_ref != new_refs[preview_index + 1]
        or not isinstance(case_id, str)
        or re.fullmatch(r"V-PREVIEW-[0-9]{3,}", case_id) is None
        or alignment.get("alpha_direction_checkpoint") != case_id
        or binding.get("decision_owner") != "user"
        or binding.get("allowed_decisions") not in DIRECTION_DECISION_SETS
        or binding.get("engineering_hardening_requires_continue") is not True
    ):
        return None
    return str(alpha_ref)


def resolved_sustained_alpha_slice_ref(
    alignment: dict[str, object], new_refs: list[str]
) -> str | None:
    """Resolve the first sustained Web Alpha that owns the Codex comparison."""

    alpha_ref = resolved_alpha_direction_slice_ref(alignment, new_refs)
    if alpha_ref is not None:
        return alpha_ref
    experience_binding = alignment.get("experience_version_binding")
    if isinstance(experience_binding, dict):
        experience_ref = experience_binding.get("new_slice_ref")
        if isinstance(experience_ref, str) and experience_ref in new_refs:
            return experience_ref
    return resolved_direction_preview_slice_ref(alignment, new_refs)


def validate_experience_first_delivery_policy(
    manifest: dict[str, object],
    alignment: dict[str, object],
    new_refs: list[str],
    blocking_case_ids: list[str],
    label: str,
    *,
    required: bool,
) -> list[str]:
    """Freeze an experience-first clock without confusing access and quality."""

    policy = manifest.get("experience_delivery_policy")
    if policy is None:
        return (
            [f"{label}: experience_delivery_policy is required"]
            if required
            else []
        )
    if not isinstance(policy, dict):
        return [f"{label}: experience_delivery_policy must be a mapping"]

    errors: list[str] = []
    if policy.get("schema") != EXPERIENCE_FIRST_DELIVERY_SCHEMA:
        errors.append(
            f"{label}: experience_delivery_policy.schema must equal "
            f"{EXPERIENCE_FIRST_DELIVERY_SCHEMA}"
        )

    historical_refs = policy.get("historical_pre_policy_result_refs")
    if isinstance(historical_refs, dict):
        # ``safe_load_manifest`` validates block-sequence syntax but leaves its
        # values opaque. File-backed validation resolves them from inert text
        # before the Result boundary is evaluated.
        pass
    elif not isinstance(historical_refs, list):
        errors.append(
            f"{label}: experience_delivery_policy.historical_pre_policy_result_refs "
            "must be a sequence"
        )
    elif len(historical_refs) != len(set(map(str, historical_refs))):
        errors.append(
            f"{label}: experience_delivery_policy.historical_pre_policy_result_refs "
            "must be unique"
        )
    else:
        for reference in historical_refs:
            if not isinstance(reference, str) or re.fullmatch(
                r"ITER-[0-9]{3}-RESULT-[A-Z0-9]+(?:-[A-Z0-9]+)*", reference
            ) is None:
                errors.append(
                    f"{label}: experience_delivery_policy.historical_pre_policy_result_refs "
                    "must contain exact Iteration Result IDs"
                )
                break
    if policy.get("historical_results_do_not_satisfy_experience_gate") is not True:
        errors.append(
            f"{label}: experience_delivery_policy."
            "historical_results_do_not_satisfy_experience_gate must be true"
        )

    alpha_ref = resolved_sustained_alpha_slice_ref(alignment, new_refs)
    if alpha_ref is None or policy.get("owner_slice_ref") != alpha_ref:
        errors.append(
            f"{label}: experience_delivery_policy.owner_slice_ref must equal "
            "the first sustained Web Alpha Slice"
        )

    chat_cutover = conversational_agent_cutover_active(manifest)
    case_contracts = (
        ("access_case_id", r"V-ALPHA-ACCESS-[0-9]{3,}"),
        (
            "timebox_case_id",
            r"V-TIMEBOX-CHAT-[0-9]{3,}" if chat_cutover else r"V-TIMEBOX-[0-9]{3,}",
        ),
        (
            "quality_case_id",
            r"V-CHAT-QUALITY-[0-9]{3,}"
            if chat_cutover
            else r"V-(?:PRE-)?[A-Z0-9]+(?:-[A-Z0-9]+)*",
        ),
    )
    resolved_cases: dict[str, str] = {}
    for field, pattern in case_contracts:
        case_id = policy.get(field)
        if (
            not isinstance(case_id, str)
            or re.fullmatch(pattern, case_id) is None
            or case_id not in blocking_case_ids
        ):
            errors.append(
                f"{label}: experience_delivery_policy.{field} must be a "
                "matching blocking Case"
            )
        else:
            resolved_cases[field] = case_id
    if len(set(resolved_cases.values())) != len(resolved_cases):
        errors.append(
            f"{label}: experience access, timebox and quality Cases must be distinct"
        )

    exact_values: tuple[tuple[str, object], ...] = (
        (
            "start_event",
            "first-product-code-change-after-slice-authorization",
        ),
        ("page_launchable_deadline_minutes", 60),
        ("sustained_user_operable_alpha_deadline_minutes", 180),
        ("hard_stop_deadline_minutes", 240),
        ("hard_stop_action", EXPERIENCE_FIRST_DELIVERY_HARD_STOP_ACTION),
        ("access_gate_scope", "user-operable-web-and-request-path-only"),
        ("quality_gate_scope", "user-visible-answer-quality-only"),
        ("access_pass_cannot_satisfy_quality_gate", True),
        ("availability_requires_quality_pass", False),
        ("hardening_requires_quality_pass", True),
        (
            "pre_first_experience_allowed_checks",
            EXPERIENCE_FIRST_DELIVERY_PRE_ACCESS_WORK,
        ),
        ("pre_first_experience_qualification_limit", 1),
        ("pre_first_experience_smoke_question_limit", 1),
        ("pre_first_experience_full_regression_allowed", False),
        ("live_attempt_unit", EXPERIENCE_FIRST_DELIVERY_LIVE_ATTEMPT_UNIT),
        ("same_failure_signature_retry_limit", 1),
        ("consecutive_no_user_visible_increment_limit", 2),
        ("no_increment_action", EXPERIENCE_FIRST_DELIVERY_NO_INCREMENT_ACTION),
        (
            "failure_diagnosis_order",
            EXPERIENCE_FIRST_FAILURE_DIAGNOSIS_ORDER,
        ),
        ("earliest_divergence_required", True),
        (
            "falsifiable_root_cause_hypothesis_required_before_prompt_schema_or_contract_change",
            True,
        ),
        ("local_minimal_reproduction_required_before_live_retry", True),
        ("unseen_adjacent_local_case_count", 2),
        (
            "live_canary_turn_count_after_local_pass"
            if chat_cutover
            else "live_canary_question_count_after_local_pass",
            1,
        ),
        (
            "same_failure_signature_fix_limit_before_architecture_responsibility_review",
            1,
        ),
        (
            "same_failure_signature_recurrence_action",
            "stop-rule-accumulation-and-review-architecture-responsibilities",
        ),
        (
            "pre_first_experience_test_scope",
            "targeted-impact-startup-and-safety-only",
        ),
        ("full_regression_before_alpha_continue_allowed", False),
        (
            "full_regression_allowed_stages",
            "alpha-continue-hardening-and-before-formal-acceptance",
        ),
    )
    for field, expected in exact_values:
        if policy.get(field) != expected:
            errors.append(
                f"{label}: experience_delivery_policy.{field} must equal {expected}"
            )
    if chat_cutover:
        for field, pattern in (
            ("chat_case_id", r"V-CHAT-[0-9]{3,}"),
            ("alpha_comparison_case_id", r"V-COMP-ALPHA-[0-9]{3,}"),
        ):
            case_id = policy.get(field)
            if (
                not isinstance(case_id, str)
                or re.fullmatch(pattern, case_id) is None
                or case_id not in blocking_case_ids
            ):
                errors.append(
                    f"{label}: experience_delivery_policy.{field} must be a matching blocking Case"
                )
        if "live_canary_question_count_after_local_pass" in policy:
            errors.append(
                f"{label}: live_canary_question_count_after_local_pass cannot define a Chat live-attempt unit"
            )
    return errors


def validate_provider_route_policy(
    manifest: dict[str, object],
    text_or_label: str,
    label: str | None = None,
    *,
    required: bool,
) -> list[str]:
    """Require an Ark-first route with isolated transparent fallback attempts."""

    text = text_or_label if label is not None else None
    label = label if label is not None else text_or_label

    policy = manifest.get("provider_route_policy")
    if policy is None:
        return [f"{label}: provider_route_policy is required"] if required else []
    if not isinstance(policy, dict):
        return [f"{label}: provider_route_policy must be a mapping"]

    errors: list[str] = []
    if policy.get("schema") != PROVIDER_ROUTE_POLICY_SCHEMA:
        errors.append(
            f"{label}: provider_route_policy.schema must equal "
            f"{PROVIDER_ROUTE_POLICY_SCHEMA}"
        )
    preference_order = policy.get("preference_order")
    if not isinstance(preference_order, list) and text is not None:
        preference_order = manifest_resolved_sequence_items(
            text, "provider_route_policy", "preference_order"
        )
    if preference_order != list(PROVIDER_ROUTE_PREFERENCE):
        errors.append(
            f"{label}: provider_route_policy.preference_order must equal "
            "VOLCENGINE_ARK then DEEPSEEK"
        )

    exact_values: tuple[tuple[str, object], ...] = (
        ("primary_provider", "VOLCENGINE_ARK"),
        ("fallback_provider", "DEEPSEEK"),
        (
            "fallback_requires_primary_attempt_terminal_without_authorized_answer",
            True,
        ),
        ("primary_unavailable_evidence_required", True),
        ("implementation_gap_counts_as_primary_unavailable", False),
        (
            "primary_availability_requires",
            "credential-reference-configured-current-exact-conformance-current-exact-strategy-capability-qualification-and-no-active-provider-account-or-model-hold",
        ),
        (
            "fallback_trigger",
            "sealed-primary-attempt-terminal-without-authorized-answer-for-provider-or-model-capability-reason",
        ),
        ("application_source_security_failure_allows_fallback", False),
        ("fallback_reason_classification_required", True),
        (
            "capability_failure_must_not_be_misclassified_as_unavailable",
            True,
        ),
        (
            "route_freeze_time",
            "before-conversation-start-and-before-any-interaction-unit-dispatch",
        ),
        ("ordered_routes_preauthorized_at_session_start", True),
        (
            "ordered_route_disclosure_scopes_preauthorized_at_session_start",
            True,
        ),
        ("transparent_logical_interaction_fallback_allowed", True),
        ("user_resubmission_or_new_session_required", False),
        ("fallback_attempt_restarts_full_chain", True),
        (
            "fallback_attempt_inputs",
            "immutable-original-interaction-input-exact-relevant-application-sealed-conversation-context-when-chat-and-exact-cognition",
        ),
        ("cross_attempt_intermediate_state_reuse_allowed", False),
        ("late_primary_result_policy", "quarantine-audit-only"),
        ("late_primary_result_overwrite_allowed", False),
        ("maximum_fallback_provider_attempts", 1),
        ("same_provider_retry_allowed", False),
        ("outcome_unknown_duplicate_cost_risk_recorded", True),
        (
            "post_dispatch_provider_switch_requires",
            "new-provider-attempt-under-same-logical-interaction-unit-and-preauthorized-route",
        ),
        ("deepseek_batch_start_policy", "provider-declared-non-peak-preferred"),
        ("deepseek_schedule_timezone", "Asia/Shanghai"),
        ("peak_urgent_override_requires", "audited-explicit-override"),
        ("cost_can_reduce_answer_quality", False),
        ("cost_gate_scope", "before-interaction-unit-start-only"),
        ("current_started_interaction_unit_must_keep_full_quality_chain", True),
        ("unchanged_current_conformance_reuse_required", True),
    )
    for field, expected in exact_values:
        if policy.get(field) != expected:
            errors.append(
                f"{label}: provider_route_policy.{field} must equal {expected}"
            )
    for legacy_field in (
        "fallback_requires_primary_unavailable",
        "quality_or_schema_failure_counts_as_primary_unavailable",
        "selection_time",
        "request_level_failover_allowed",
        "same_question_redispatch_to_fallback_allowed",
        "transparent_logical_question_fallback_allowed",
        "transparent_logical_turn_fallback_allowed",
        "current_started_question_must_keep_full_quality_chain",
        "current_started_turn_must_keep_full_quality_chain",
    ):
        if legacy_field in policy:
            errors.append(
                f"{label}: provider_route_policy.{legacy_field} is incompatible "
                "with isolated transparent fallback attempts"
            )

    preferred_windows = policy.get("deepseek_current_preferred_windows")
    if not isinstance(preferred_windows, list) and text is not None:
        preferred_windows = manifest_resolved_sequence_items(
            text, "provider_route_policy", "deepseek_current_preferred_windows"
        )
    if preferred_windows != list(DEEPSEEK_PREFERRED_WINDOWS):
        errors.append(
            f"{label}: provider_route_policy.deepseek_current_preferred_windows "
            "must equal the frozen provider-declared windows"
        )
    fallback_eligible_outcomes = policy.get("fallback_eligible_outcomes")
    if not isinstance(fallback_eligible_outcomes, list) and text is not None:
        fallback_eligible_outcomes = manifest_resolved_sequence_items(
            text, "provider_route_policy", "fallback_eligible_outcomes"
        )
    if fallback_eligible_outcomes != list(PROVIDER_FALLBACK_ELIGIBLE_OUTCOMES):
        errors.append(
            f"{label}: provider_route_policy.fallback_eligible_outcomes must "
            "equal the frozen provider/model availability and capability outcomes"
        )
    schedule_source = policy.get("deepseek_schedule_source")
    if not isinstance(schedule_source, str) or re.fullmatch(
        r"https://api-docs\.deepseek\.com(?:/.*)?", schedule_source
    ) is None:
        errors.append(
            f"{label}: provider_route_policy.deepseek_schedule_source must use "
            "the official api-docs.deepseek.com domain"
        )
    checked_at = policy.get("deepseek_schedule_checked_at")
    if not isinstance(checked_at, str) or re.fullmatch(
        r"[0-9]{4}-[0-9]{2}-[0-9]{2}", checked_at
    ) is None:
        errors.append(
            f"{label}: provider_route_policy.deepseek_schedule_checked_at must "
            "be an ISO date"
        )
    else:
        try:
            datetime.strptime(checked_at, "%Y-%m-%d")
        except ValueError:
            errors.append(
                f"{label}: provider_route_policy.deepseek_schedule_checked_at "
                "must be a real ISO date"
            )
    if policy.get("deepseek_schedule_effective_status") not in {
        "announced-not-yet-effective",
        "effective",
    }:
        errors.append(
            f"{label}: provider_route_policy.deepseek_schedule_effective_status "
            "must record whether the provider-declared schedule is effective"
        )
    return errors


def validate_strict_codex_baseline_alignment(
    alignment: dict[str, object], label: str
) -> list[str]:
    """Freeze a blind answer-quality gate that secondary metrics cannot replace."""

    errors: list[str] = []
    identity_digest = alignment.get("mature_source_agent_identity_digest")
    if not isinstance(identity_digest, str) or re.fullmatch(
        r"sha256:[0-9a-f]{64}", identity_digest
    ) is None:
        errors.append(
            f"{label}: mature_source_agent_identity_digest must be an exact sha256 digest"
        )
    for field, expected in (
        ("mature_source_agent_role", STRICT_CODEX_BASELINE_ROLE),
        (
            "mature_source_agent_execution_mode",
            STRICT_CODEX_BASELINE_EXECUTION_MODE,
        ),
        ("positive_value_metric", STRICT_CODEX_QUALITY_METRIC),
        ("positive_value_unit", STRICT_CODEX_QUALITY_UNIT),
        ("positive_value_comparison", STRICT_CODEX_QUALITY_COMPARISON),
        ("held_out_evaluation_owner", "independent-evaluator"),
        ("positive_value_adjudication_owner", "independent-evaluator"),
    ):
        if alignment.get(field) != expected:
            errors.append(f"{label}: {field} must equal {expected}")
    threshold = alignment.get("positive_value_threshold")
    if (
        isinstance(threshold, bool)
        or not isinstance(threshold, int)
        or threshold < 1
    ):
        errors.append(
            f"{label}: positive_value_threshold must be a positive integer so a tie cannot pass"
        )
    if alignment.get("secondary_metrics_can_compensate_answer_quality") is not False:
        errors.append(
            f"{label}: secondary_metrics_can_compensate_answer_quality must be false"
        )
    return errors


def validate_alpha_agent_comparison_binding(
    alignment: dict[str, object],
    new_refs: list[str],
    blocking_case_ids: list[str],
    label: str,
) -> list[str]:
    """Bind a blocking blind Codex comparison to the first sustained Web Alpha."""

    binding = alignment.get("alpha_agent_comparison_binding")
    if not isinstance(binding, dict):
        return [f"{label}: alpha_agent_comparison_binding must be a mapping"]
    errors: list[str] = []
    case_id = binding.get("case_id")
    if (
        not isinstance(case_id, str)
        or re.fullmatch(r"V-COMP-ALPHA-[0-9]{3,}", case_id) is None
        or case_id not in blocking_case_ids
    ):
        errors.append(
            f"{label}: Alpha Agent comparison case_id must be a blocking V-COMP-ALPHA-NNN Case"
        )
    alpha_ref = resolved_sustained_alpha_slice_ref(alignment, new_refs)
    if alpha_ref is None or binding.get("new_slice_ref") != alpha_ref:
        errors.append(
            f"{label}: Alpha Agent comparison must belong to the first sustained Web Alpha"
        )
    if binding.get("result_role") == (
        "direction-signal-not-iteration-012-strict-superiority-gate"
    ):
        exact_values: tuple[tuple[str, object], ...] = (
            ("occurs_after_chat_access_and_five_turn_canary", True),
            (
                "arms",
                "same-agent-source-only,same-agent-full-world-model-cognition-and-source,current-codex-external-baseline",
            ),
            ("current_codex_is_oracle_or_reviewer", False),
            (
                "system_arm_shared_runtime",
                "same-lead-agent-model-tools-permissions-budget-cache-policy-and-state",
            ),
            (
                "external_codex_runtime",
                "preserve-actual-model-reasoning-tools-permissions-and-budget",
            ),
            (
                "shared_evaluation_inputs",
                "same-exact-revision-questions-authorized-source-scope-output-constraints-and-blind-rubric",
            ),
            ("forced_runtime_identity_across_all_three_arms", False),
            (
                "technical_adjudication_owner",
                "independent-evaluator-not-answer-generator",
            ),
            ("product_direction_decision_owner", "user"),
        )
        for field, expected in exact_values:
            if binding.get(field) != expected:
                errors.append(
                    f"{label}: alpha_agent_comparison_binding.{field} must equal {expected}"
                )
        return errors
    question_count = binding.get("question_count")
    if (
        isinstance(question_count, bool)
        or not isinstance(question_count, int)
        or question_count < 3
    ):
        errors.append(
            f"{label}: Alpha Agent comparison question_count must be at least 3"
        )
    for field, expected in (
        (
            "question_set_rule",
            "original-failure-plus-two-heterogeneous-including-post-freeze-live",
        ),
        ("protocol_digest_ref", "mature_source_agent_protocol_digest"),
        ("rubric_digest_ref", "mature_source_agent_rubric_digest"),
        ("identity_digest_ref", "mature_source_agent_identity_digest"),
        ("pass_rule", STRICT_CODEX_ALPHA_PASS_RULE),
        ("all_tie_outcome", "FAIL"),
    ):
        if binding.get(field) != expected:
            errors.append(
                f"{label}: alpha_agent_comparison_binding.{field} must equal {expected}"
            )
    if "tie_outcome" in binding:
        errors.append(
            f"{label}: alpha_agent_comparison_binding.tie_outcome is ambiguous; "
            "use all_tie_outcome only"
        )
    post_freeze_live_question_count = binding.get(
        "post_freeze_live_question_count"
    )
    if (
        isinstance(post_freeze_live_question_count, bool)
        or not isinstance(post_freeze_live_question_count, int)
        or post_freeze_live_question_count < 1
        or not isinstance(question_count, int)
        or isinstance(question_count, bool)
        or post_freeze_live_question_count > question_count
    ):
        errors.append(
            f"{label}: alpha_agent_comparison_binding.post_freeze_live_question_count "
            "must be a positive integer no greater than question_count"
        )
    if binding.get("secondary_metric_compensation_allowed") is not False:
        errors.append(
            f"{label}: Alpha Agent comparison cannot allow secondary metrics to compensate answer quality"
        )
    return errors


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
    has_alpha = isinstance(alignment.get("alpha_direction_binding"), dict)
    status_label = (
        "direction-probe-non-acceptance-non-production"
        if has_alpha
        else "non-acceptance-non-production"
    )
    if binding.get("status_label") != status_label:
        errors.append(
            f"{label}: direction preview status_label must equal {status_label}"
        )
    decision_owner = binding.get("decision_owner")
    if decision_owner != "user":
        errors.append(
            f"{label}: direction preview decision_owner must equal user"
        )
    if binding.get("allowed_decisions") not in DIRECTION_DECISION_SETS:
        errors.append(
            f"{label}: direction preview allowed_decisions must include CONTINUE, REWORK, REDIRECT and REJECT (legacy manifests may omit REWORK)"
        )
    continuation_field = (
        "next_slice_requires_continue" if has_alpha else "hardening_requires_continue"
    )
    if binding.get(continuation_field) is not True:
        errors.append(
            f"{label}: direction preview must require CONTINUE before its next Slice"
        )
    return errors


def validate_alpha_direction_binding(
    alignment: dict[str, object],
    new_refs: list[str],
    blocking_case_ids: list[str],
    label: str,
) -> list[str]:
    """Validate an optional user-visible checkpoint between probe and hardening."""

    binding = alignment.get("alpha_direction_binding")
    if binding is None:
        return []
    if not isinstance(binding, dict):
        return [f"{label}: alpha_direction_binding must be a mapping"]
    errors: list[str] = []
    if resolved_alpha_direction_slice_ref(alignment, new_refs) is None:
        errors.append(f"{label}: Alpha checkpoint must immediately follow the direction probe and precede hardening")
    for field, pattern in (
        ("case_id", r"V-PREVIEW-[0-9]{3,}"),
        ("web_case_id", r"V-WEB-[0-9]{3,}"),
        ("live_ad_hoc_case_id", r"V-ADHOC-[0-9]{3,}"),
    ):
        value = binding.get(field)
        if not isinstance(value, str) or re.fullmatch(pattern, value) is None or value not in blocking_case_ids:
            errors.append(f"{label}: Alpha {field} must be a blocking Case matching {pattern}")
    return errors


def validate_experience_version_binding(
    alignment: dict[str, object],
    new_refs: list[str],
    blocking_case_ids: list[str],
    label: str,
    *,
    required: bool = False,
) -> list[str]:
    """Validate the opt-in contract that distinguishes a usable Web version from a one-shot run."""

    binding = alignment.get("experience_version_binding")
    if binding is None:  # Historical manifests predate this contract.
        return [f"{label}: experience_version_binding is required"] if required else []
    if not isinstance(binding, dict):
        return [f"{label}: experience_version_binding must be a mapping"]
    errors: list[str] = []
    schema = binding.get("schema")
    if schema not in {"USER_EXPERIENCE_VERSION@1", ENGINEERING_CHAT_EXPERIENCE_SCHEMA}:
        errors.append(
            f"{label}: experience_version_binding.schema must equal "
            "USER_EXPERIENCE_VERSION@1 or ENGINEERING_CHAT_EXPERIENCE@1"
        )
    case_id = binding.get("case_id")
    case_pattern = (
        r"V-CHAT-EXPERIENCE-[0-9]{3,}"
        if schema == ENGINEERING_CHAT_EXPERIENCE_SCHEMA
        else r"V-EXPERIENCE-[0-9]{3,}"
    )
    if (
        not isinstance(case_id, str)
        or re.fullmatch(case_pattern, case_id) is None
        or case_id not in blocking_case_ids
    ):
        errors.append(
            f"{label}: experience version case_id must be a matching blocking experience Case"
        )
    if not new_refs or binding.get("new_slice_ref") != new_refs[0]:
        errors.append(
            f"{label}: experience version must be delivered by the first new capability Slice"
        )
    for field in ("exact_version_visible", "repeatable_start", "limitations_visible"):
        if binding.get(field) is not True:
            errors.append(f"{label}: experience version {field} must equal true")
    if schema == "USER_EXPERIENCE_VERSION@1":
        if binding.get("continuous_same_session_free_questions") is not True:
            errors.append(
                f"{label}: experience version continuous_same_session_free_questions must equal true"
            )
    elif schema == ENGINEERING_CHAT_EXPERIENCE_SCHEMA:
        for field in (
            "message_history_visible",
            "new_conversation_control",
            "semantic_follow_up",
            "user_correction_updates_context",
            "summary_honors_current_context",
            "per_turn_evidence_and_review",
            "new_conversation_context_isolation",
        ):
            if binding.get(field) is not True:
                errors.append(
                    f"{label}: engineering Chat experience {field} must equal true"
                )
        if binding.get("minimum_conversation_turns") != 5:
            errors.append(
                f"{label}: engineering Chat experience minimum_conversation_turns must equal 5"
            )
        if binding.get("long_term_memory_required") is not False:
            errors.append(
                f"{label}: engineering Chat Alpha must not require long-term memory"
            )
    address = binding.get("fixed_loopback_address")
    address_match = (
        re.fullmatch(r"http://127\.0\.0\.1:([1-9][0-9]{0,4})/?", address)
        if isinstance(address, str)
        else None
    )
    if address_match is None or not (1 <= int(address_match.group(1)) <= 65535):
        errors.append(
            f"{label}: experience version fixed_loopback_address must be an explicit 127.0.0.1 HTTP address"
        )
    if schema == ENGINEERING_CHAT_EXPERIENCE_SCHEMA:
        if (
            binding.get("turn_failure_scope")
            != "current-turn-only-conversation-remains-usable"
        ):
            errors.append(
                f"{label}: engineering Chat experience must isolate a failed turn without closing the conversation"
            )
    elif (
        binding.get("question_failure_scope")
        != "current-question-only-service-remains-available"
    ):
        errors.append(
            f"{label}: experience version must isolate a bad question without stopping the service"
        )
    return errors


def validate_conversational_engineering_agent(
    manifest: dict[str, object],
    alignment: dict[str, object],
    new_refs: list[str],
    blocking_case_ids: list[str],
    label: str,
    *,
    required: bool = False,
) -> list[str]:
    """Validate the opt-in semantic Chat and lead engineering-Agent boundary."""

    policy = manifest.get("conversational_engineering_agent")
    if policy is None:
        return [f"{label}: conversational_engineering_agent is required"] if required else []
    if not isinstance(policy, dict):
        return [f"{label}: conversational_engineering_agent must be a mapping"]

    errors: list[str] = []
    exact_values: tuple[tuple[str, object], ...] = (
        ("schema", CONVERSATIONAL_ENGINEERING_AGENT_SCHEMA),
        ("architecture_decision_ref", "SYS-ADR-018"),
        (
            "conversation_contract_ref",
            "SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION",
        ),
        ("interaction_model", "semantic-multi-turn-chat"),
        ("fixed_multi_role_content_workflow_is_target_agent", False),
        (
            "world_model_role",
            "persistent-versioned-verifiable-software-cognition",
        ),
        (
            "lead_agent_owns",
            "user-goal-hypotheses-subtasks-plan-revisions-context-selection-"
            "tool-choice-observation-interpretation-replanning-completion-and-"
            "answer-synthesis",
        ),
        (
            "control_plane_owns",
            "exact-version-authorization-read-only-tool-execution-evidence-"
            "identity-budget-and-audit",
        ),
        ("independent_reviewer_required", True),
        (
            "lead_agent_direct_repository_filesystem_shell_network_or_write_access",
            False,
        ),
        (
            "tool_families_before_direction_confirmation",
            "world-model-query-and-controlled-source-search-read",
        ),
        (
            "conversation_identity_pinned_to",
            "exact-project-revision-world-model-authority-source-profile-and-"
            "session-authority",
        ),
        (
            "turn_intent_kinds",
            "new,follow-up,correction,clarification,deepen,summary",
        ),
        (
            "context_required_fields",
            "confirmed-goal-and-constraints,referenced-entities-and-topics,"
            "open-questions,reviewed-conclusions,contested-or-superseded-"
            "conclusions,exact-provenance",
        ),
        ("application_sealed_context_projection_required", True),
        ("provider_hidden_memory_is_authority", False),
        (
            "ambiguous_reference_action",
            "clarify-before-source-or-provider-dispatch",
        ),
        ("user_statement_becomes_source_truth", False),
        ("prior_answer_or_review_reuse_as_fact_allowed", False),
        (
            "reused_evidence_status",
            "candidate-only-until-rebound-and-reviewed-for-current-turn",
        ),
        (
            "evidence_reuse_requires",
            "exact-revision-binding-world-model-authority-source-profile-"
            "allowlist-content-digest-and-coverage-match",
        ),
        (
            "evidence_reuse_forbidden_inputs",
            "prior-answer-authorization,prior-review-decision,prior-limitation,"
            "unsealed-tool-result,provider-memory",
        ),
        ("reused_evidence_rebound_to_current_turn_package_required", True),
        (
            "per_turn_request_evidence_answer_review_and_delivery_identity_required",
            True,
        ),
        ("new_conversation_context_isolation_required", True),
        ("failed_turn_closes_conversation", False),
        ("first_chat_canary_conversation_count", 1),
        ("first_chat_canary_turn_count", 5),
        ("new_conversation_leakage_probe_required", True),
        (
            "alpha_comparison_arms",
            "same-agent-source-only,same-agent-full-world-model-cognition-and-"
            "source,current-codex-external-baseline",
        ),
        ("knowledge_admission_from_conversation", "asynchronous-reviewed-only"),
        ("long_term_memory_before_direction_confirmation_required", False),
        ("multi_agent_before_direction_confirmation_required", False),
        ("skill_market_before_direction_confirmation_required", False),
        (
            "persistence_across_restart_before_direction_confirmation_required",
            False,
        ),
        ("full_regression_before_direction_confirmation_allowed", False),
    )
    for field, expected in exact_values:
        if policy.get(field) != expected:
            errors.append(
                f"{label}: conversational_engineering_agent.{field} must equal {expected}"
            )

    if not new_refs or policy.get("owner_slice_ref") != new_refs[0]:
        errors.append(
            f"{label}: conversational engineering Agent must belong to the first capability Slice"
        )
    chat_case_id = policy.get("chat_case_id")
    if (
        not isinstance(chat_case_id, str)
        or re.fullmatch(r"V-CHAT-[0-9]{3,}", chat_case_id) is None
        or chat_case_id not in blocking_case_ids
    ):
        errors.append(
            f"{label}: conversational engineering Agent chat_case_id must be a blocking V-CHAT-NNN Case"
        )
    if policy.get("status") not in {
        "target-not-implemented-not-qualified",
        "implemented-not-qualified",
        "qualified-candidate",
    }:
        errors.append(
            f"{label}: conversational_engineering_agent.status must be a closed pre-production state"
        )
    experience = alignment.get("experience_version_binding")
    if (
        not isinstance(experience, dict)
        or experience.get("schema") != ENGINEERING_CHAT_EXPERIENCE_SCHEMA
    ):
        errors.append(
            f"{label}: conversational engineering Agent requires ENGINEERING_CHAT_EXPERIENCE@1"
        )
    return errors


def validate_conversational_architecture_cutover(
    manifest: dict[str, object], label: str
) -> list[str]:
    """Keep the @3 workflow auditable without authorizing it as the current Agent."""

    if not conversational_agent_cutover_active(manifest):
        return []
    errors: list[str] = []
    legacy_markers: tuple[tuple[str, str], ...] = (
        ("hybrid_evidence_path", "ENGINEERING_QA_ADAPTIVE_INVESTIGATION@3"),
        (
            "reviewer_verification_investigation",
            "ENGINEERING_QA_ADAPTIVE_INVESTIGATION@3",
        ),
        (
            "answer_hierarchy_protocol",
            "ENGINEERING_QA_ADAPTIVE_INVESTIGATION@3",
        ),
        ("answer_protocol", "ENGINEERING_QA_ADAPTIVE_INVESTIGATION@3"),
    )
    for section_name, schema in legacy_markers:
        section = manifest.get(section_name)
        if not isinstance(section, dict):
            errors.append(f"{label}: {section_name} must remain a legacy mapping")
            continue
        for field, expected in (
            ("protocol_role", "legacy-compatibility"),
            ("legacy_protocol_schema", schema),
            ("superseded_as_default_by", "SYS-ADR-018"),
            ("current_delivery_authorization_allowed", False),
            (
                "historical_result_ref",
                "ITER-010-RESULT-SLICE-001-STOP-REDIRECT",
            ),
        ):
            if section.get(field) != expected:
                errors.append(
                    f"{label}: {section_name}.{field} must equal {expected}"
                )

    readiness = manifest.get("readiness_inputs")
    if not isinstance(readiness, dict):
        return errors + [f"{label}: readiness_inputs must be a mapping"]
    for field, expected in (
        ("required_architecture_decision", "SYS-ADR-018"),
        ("current_architecture_decision", "SYS-ADR-018"),
        ("architecture_change_target", "SYS-ADR-018"),
        ("legacy_compatibility_architecture_decision", "SYS-ADR-016"),
        ("legacy_architecture_amended_by", "SYS-ADR-018"),
        (
            "answer_protocol_contract_ref",
            "SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION",
        ),
        (
            "legacy_answer_protocol_contract_ref",
            "SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING",
        ),
        ("current_protocol_schema", CONVERSATIONAL_ENGINEERING_AGENT_SCHEMA),
        ("legacy_protocol_schema", ENGINEERING_QA_ADAPTIVE_PROTOCOL_SCHEMA),
        ("current_readiness_status", "refresh-required-not-accepted"),
        ("historical_readiness_ref", "ITER-010-READINESS"),
        (
            "historical_readiness_catalog_digest",
            "sha256:26769498135692067597a1f59e0fbbc8b82502ebd5336f7fdb033a80e3baff82",
        ),
    ):
        if readiness.get(field) != expected:
            errors.append(f"{label}: readiness_inputs.{field} must equal {expected}")
    for forbidden_field in (
        "amended_architecture_decision",
        "investigation_budget_status",
    ):
        if forbidden_field in readiness:
            errors.append(
                f"{label}: readiness_inputs.{forbidden_field} ambiguously presents a legacy input as current"
            )
    return errors


def validate_historical_gate_catalog(
    manifest: dict[str, object],
    blocking_case_ids: list[str],
    verification: Document | None,
    label: str,
) -> list[str]:
    """Separate immutable executed Case semantics from the current Chat gates."""

    cutover = manifest.get("critical_assumption_catalog_cutover")
    if not isinstance(cutover, dict):
        return []
    errors: list[str] = []
    historical_ids = resolved_csv_values(cutover.get("historical_case_ids"))
    reused = sorted(set(historical_ids).intersection(blocking_case_ids))
    if reused:
        errors.append(
            f"{label}: current blocking_case_ids must not reuse historical executed Cases: "
            + ", ".join(reused)
        )
    missing_current = sorted(ITER010_CURRENT_CHAT_GATE_CASES - set(blocking_case_ids))
    if missing_current:
        errors.append(
            f"{label}: current blocking_case_ids must include the new Chat Gate catalog: "
            + ", ".join(missing_current)
        )
    if verification is None:
        return errors + [f"{label}: historical Gate cutover requires Verification"]
    for case_id, expected_verdict in ITER010_HISTORICAL_GATE_CASES.items():
        rows = markdown_table_case_rows(verification.body, case_id)
        if len(rows) != 1 or len(rows[0]) != 7:
            errors.append(
                f"{label}: historical Case {case_id} must remain exactly once in Verification"
            )
            continue
        verdict = blocking_case_status_verdict(rows[0][6])
        if verdict != expected_verdict:
            errors.append(
                f"{label}: historical Case {case_id} must preserve verdict {expected_verdict}"
            )
    errors.extend(
        validate_iter010_current_verification_semantics(verification, label)
    )
    return errors


def validate_iter010_current_verification_semantics(
    verification: Document | None, label: str
) -> list[str]:
    """Freeze the non-interchangeable semantics of the current ITER-010 gates."""

    if verification is None:
        return [f"{label}: current ITER-010 Gate contracts require Verification"]
    verification_label = verification.relative_path
    column_indexes = {"Claim": 1, "Frozen input / oracle": 3, "Expected": 4}
    errors: list[str] = []
    for case_id, field_contracts in (
        ITER010_CURRENT_VERIFICATION_REQUIRED_PHRASES.items()
    ):
        rows = markdown_table_case_rows(verification.body, case_id)
        if len(rows) != 1 or len(rows[0]) != 7:
            errors.append(
                f"{verification_label}: {case_id} must remain exactly once with the seven-column schema"
            )
            continue
        row = rows[0]
        for field_name, required_phrases in field_contracts.items():
            value = row[column_indexes[field_name]]
            for phrase in required_phrases:
                if phrase not in value:
                    errors.append(
                        f"{verification_label}: {case_id} {field_name} must preserve current semantic phrase {phrase!r}"
                    )
    return errors


def validate_rework_policy(
    manifest: dict[str, object], label: str, *, required: bool = False
) -> list[str]:
    """Validate the opt-in same-Slice repair policy used by new plans."""

    policy = manifest.get("rework_policy")
    if policy is None:  # Historical manifests predate this contract.
        return [f"{label}: rework_policy is required"] if required else []
    if not isinstance(policy, dict):
        return [f"{label}: rework_policy must be a mapping"]
    errors: list[str] = []
    expected = {
        "schema": "SAME_SLICE_REWORK@1",
        "failed_attempt_default_decision": "REWORK",
        "failed_attempt_blocks": "slice-promotion-only",
        "same_slice_reauthorization_allowed": True,
        "problem_report_or_review_request_implies_redirect": False,
        "redirect_bases": (
            "explicit-user-direction-change,core-architecture-falsified,"
            "precommitted-no-progress-limit-reached"
        ),
    }
    for field, value in expected.items():
        if policy.get(field) != value:
            errors.append(f"{label}: rework_policy.{field} must equal {value}")
    measure = policy.get("no_progress_measure")
    if (
        not isinstance(measure, str)
        or is_pending(measure)
        or has_unresolved_placeholder(measure)
    ):
        errors.append(
            f"{label}: rework_policy.no_progress_measure must be a resolved measurable outcome"
        )
    limit = policy.get("no_progress_attempt_limit")
    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 2:
        errors.append(
            f"{label}: rework_policy.no_progress_attempt_limit must be an integer of at least two"
        )
    return errors


def validate_answer_hierarchy_protocol(
    manifest: dict[str, object], label: str, *, require_frozen: bool = False
) -> list[str]:
    """Validate the optional, general answer-level and review-quality contract."""

    protocol = manifest.get("answer_hierarchy_protocol")
    if protocol is None:
        return []
    if not isinstance(protocol, dict):
        return [f"{label}: answer_hierarchy_protocol must be a mapping"]
    expected: dict[str, object] = {
        "contract_ref": "SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING",
        "direct_user_goal_answer_required": True,
        "user_visible_flow_behavior_or_impact_condition": "required-by-original-question-or-material-conclusion-checklist",
        "implementation_explanation_condition": "explicitly-requested-or-necessary-to-support-a-material-conclusion",
        "limitations_and_unknowns_condition": "evidence-gap-conflict-or-coverage-boundary-exists",
        "every_material_affirmative_claim_requires_citation": True,
        "fixed-heading-or-word-ratio-required": False,
        "material-conclusion-checklist_required": True,
        "application_acceptance_required": True,
        "shared_versioned_quality_contract_and_schema": True,
        "application_uses_accepted_question_understanding_checklist": True,
        "reviewer_reconstructs_checklist_from_immutable_original_question": True,
        "reviewer_compares_independent_and_application_checklists_for_omissions": True,
        "operational_question_checklist_required_for_start-call-use-integrate-diagnose": True,
        "component_or_dependency_inventory_satisfies_user-action-or-handoff": False,
        "finish_material_observations_required": True,
        "material_observation_kinds": "process-stage,outcome,state-change,side-effect,limitation",
        "answer_claim_material_observation_links_required": True,
        "coverage_only_limitation_empty_observation_links_allowed": True,
        "all_material_observations_default_visible_required": True,
        "reviewer_independent_evidence_observation_audit_required": True,
        "package_and_draft_observation_omissions_block_approval": True,
        "reviewer_context_and_verdict_independent": True,
        "question-project-keyword-symbol-class-method-fixture-or-oracle-routing_allowed": False,
    }
    marker_fields = {
        "protocol_role",
        "legacy_protocol_schema",
        "superseded_as_default_by",
        "current_delivery_authorization_allowed",
        "historical_result_ref",
    }
    allowed_fields = {"status", *expected}
    if protocol.get("protocol_role") == "legacy-compatibility":
        allowed_fields.update(marker_fields)
    errors = validate_exact_mapping_keys(
        protocol, allowed_fields, f"{label}: answer_hierarchy_protocol"
    )
    for field, value in expected.items():
        if protocol.get(field) != value:
            errors.append(f"{label}: answer_hierarchy_protocol.{field} must equal {value}")
    allowed_status = {"frozen"} if require_frozen else {"proposed-not-frozen", "frozen"}
    if protocol.get("status") not in allowed_status:
        errors.append(f"{label}: answer_hierarchy_protocol.status is invalid")
    if require_frozen:
        readiness = manifest.get("readiness_inputs")
        supplied = readiness.get("answer_hierarchy_protocol_digest") if isinstance(readiness, dict) else None
        expected_digest = canonical_mapping_digest(
            ENGINEERING_QA_ANSWER_HIERARCHY_SCHEMA,
            "answer_hierarchy_protocol",
            protocol,
        )
        if supplied != expected_digest:
            errors.append(f"{label}: answer_hierarchy_protocol_digest must bind the frozen protocol")
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
        if is_engineering_qa_adaptive_protocol(answer_protocol)
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
    checkpoint_ref = resolved_alpha_direction_slice_ref(alignment, new_refs) or preview_ref
    post_checkpoint_refs = new_refs[new_refs.index(checkpoint_ref) + 1 :]
    if len(post_checkpoint_refs) == 1:
        # A combined hardening/final Slice still owns the deferred early gates.
        return set(post_checkpoint_refs)
    return set(post_checkpoint_refs[:-1])


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
    checkpoint_ref = resolved_alpha_direction_slice_ref(alignment, new_refs) or preview_ref
    development = manifest.get("development")
    slices = development.get("slices") if isinstance(development, dict) else None
    checkpoint = slices.get(checkpoint_ref) if isinstance(slices, dict) else None
    checkpoint_status = checkpoint.get("status") if isinstance(checkpoint, dict) else None
    return checkpoint_status in {"proposed", "authorized", "in-progress", "blocked"}


def validate_early_evaluation_bindings(
    alignment: dict[str, object],
    new_refs: list[str],
    blocking_case_ids: list[str],
    label: str,
    *,
    defer_until_post_preview: bool = False,
    direction_preview_enabled: bool = False,
    adaptive_engineering_qa: bool = False,
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
    alpha_ref = resolved_alpha_direction_slice_ref(alignment, new_refs)
    if defer_until_post_preview and preview_ref is not None:
        preview_owned_fields: list[str] = []
        canary_bindings = alignment.get("early_hidden_canary_bindings")
        if isinstance(canary_bindings, dict):
            for binding_name, binding in canary_bindings.items():
                if isinstance(binding, dict) and binding.get("new_slice_ref") in {preview_ref, alpha_ref}:
                    preview_owned_fields.append(
                        f"early_hidden_canary_bindings.{binding_name}"
                    )
        for field in ("early_comparison_binding", "early_diagnostic_binding"):
            binding = alignment.get(field)
            if isinstance(binding, dict) and binding.get("new_slice_ref") in {preview_ref, alpha_ref}:
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
        ):
            if comparison.get(reference_field) != target_field:
                errors.append(
                    f"{label}: early comparison {reference_field} must equal {target_field}"
                )
            if target_field not in alignment:
                errors.append(
                    f"{label}: early comparison referenced field is missing: {target_field}"
                )
        if "technical_adjudication_owner" in comparison:
            for field, expected in (
                (
                    "technical_adjudication_owner",
                    "independent-evaluator-not-answer-generator",
                ),
                ("product_direction_decision_owner", "user"),
                (
                    "legacy_positive_value_adjudication_owner_ref",
                    "positive_value_adjudication_owner",
                ),
            ):
                if comparison.get(field) != expected:
                    errors.append(
                        f"{label}: early comparison {field} must equal {expected}"
                    )
        elif comparison.get("positive_value_adjudication_owner_ref") != (
            "positive_value_adjudication_owner"
        ):
            errors.append(
                f"{label}: early comparison positive_value_adjudication_owner_ref "
                "must equal positive_value_adjudication_owner"
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
        expected_layer_chains = (
            {
                "source-observation-world-model-cognition-question-understanding-"
                "investigation-source-broker-retrieval-worker-evidence-ledger-"
                "question-evidence-package-answer-review-web",
                "source-observation-world-model-cognition-conversation-or-task-"
                "understanding-agent-work-state-and-plan-source-broker-retrieval-"
                "worker-evidence-ledger-question-evidence-package-answer-"
                "independent-review-web",
            }
            if adaptive_engineering_qa
            else {"source-snapshot-query-trace-draft-review-web"}
        )
        if diagnostic.get("layer_chain") not in expected_layer_chains:
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
        if "historical_owned_case_ids" in binding:
            errors.append(
                f"{label}: reflection_gate_bindings.{binding_name} cannot declare historical Case ownership"
            )
        if (
            not isinstance(case_id, str)
            or re.fullmatch(r"V-(?:REFLECT|PREVIEW)-[0-9]{3,}", case_id) is None
        ):
            errors.append(
                f"{label}: reflection_gate_bindings.{binding_name}.case_id must match V-REFLECT-NNN or a combined V-PREVIEW-NNN decision Gate"
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
    errors.extend(
        validate_provider_route_policy(
            manifest,
            text,
            label,
            required=requires_provider_route_policy(iteration),
        )
    )
    if requires_strict_codex_baseline(iteration):
        errors.extend(validate_strict_codex_baseline_alignment(alignment, label))
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
    if user_held_live:
        input_owner = alignment.get("held_out_input_owner")
        evaluation_owner = alignment.get("held_out_evaluation_owner")
        if input_owner is None:
            if evaluation_owner != "user":
                errors.append(
                    f"{label}: legacy user-held live evaluation must use held_out_evaluation_owner user"
                )
        elif input_owner != "user" or evaluation_owner != "independent-evaluator":
            errors.append(
                f"{label}: user-held input must use held_out_input_owner user and held_out_evaluation_owner independent-evaluator"
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
        if re.fullmatch(r"V-(?:CHAT-)?XD-[0-9]{3,}", case_id) is None:
            errors.append(
                f"{label}: cross_domain_cases item must match V-XD-NNN or V-CHAT-XD-NNN: {case_id}"
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
    iteration_data = manifest.get("iteration")
    iteration_status = (
        iteration_data.get("status") if isinstance(iteration_data, dict) else None
    )
    development = manifest.get("development")
    raw_slices = development.get("slices") if isinstance(development, dict) else None
    has_rework_state = iteration_status == "paused" or (
        isinstance(raw_slices, dict)
        and any(
            isinstance(slice_state, dict)
            and any(
                field in slice_state
                for field in (
                    "project_decision_ref",
                    "rework_result_refs",
                    "rework_attempt_number",
                )
            )
            for slice_state in raw_slices.values()
        )
    )
    # Iterations written after the repair-loop contract was introduced cannot
    # opt back into the legacy three-way decision model merely by deleting the
    # rework fields after a failed attempt.  Superseded, never-executed plans
    # remain historical planning records and are validated separately.
    rework_lifecycle_required = has_rework_state or (
        isinstance(iteration_data, dict)
        and (iteration_number(iteration) or -1) >= REWORK_LIFECYCLE_START_ITERATION
        and iteration_status != "superseded"
    )
    errors.extend(validate_answer_hierarchy_protocol(manifest, label))
    errors.extend(
        validate_rework_policy(manifest, label, required=rework_lifecycle_required)
    )
    for case_id in blocking_case_ids:
        if re.fullmatch(r"V-(?:PRE-)?[A-Z0-9]+(?:-[A-Z0-9]+)*", case_id) is None:
            errors.append(
                f"{label}: blocking_case_ids item is not a valid verification case ID: {case_id}"
            )
    checkpoint_fields = [
        (
            "first_product_web_checkpoint",
            r"V-(?:ALPHA-ACCESS|CHAT-EXPERIENCE)-[0-9]{3,}"
            if conversational_agent_cutover_active(manifest)
            else r"V-WEB-[0-9]{3,}",
        ),
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
    errors.extend(
        validate_experience_first_delivery_policy(
            manifest,
            alignment,
            new_refs,
            blocking_case_ids,
            label,
            required=requires_experience_first_delivery_policy(iteration),
        )
    )
    errors.extend(
        validate_experience_version_binding(
            alignment,
            new_refs,
            blocking_case_ids,
            label,
            required=rework_lifecycle_required,
        )
    )
    experience_binding = alignment.get("experience_version_binding")
    chat_required = (
        isinstance(experience_binding, dict)
        and experience_binding.get("schema") == ENGINEERING_CHAT_EXPERIENCE_SCHEMA
    )
    errors.extend(
        validate_conversational_engineering_agent(
            manifest,
            alignment,
            new_refs,
            blocking_case_ids,
            label,
            required=chat_required,
        )
    )
    errors.extend(validate_conversational_architecture_cutover(manifest, label))
    if requires_direction_preview(iteration):
        errors.extend(
            validate_direction_preview_binding(
                alignment,
                new_refs,
                blocking_case_ids,
                label,
            )
        )
        errors.extend(
            validate_alpha_direction_binding(
                alignment,
                new_refs,
                blocking_case_ids,
                label,
            )
        )
        if rework_lifecycle_required:
            direction_binding = alignment.get("direction_preview_binding")
            experience_binding = alignment.get("experience_version_binding")
            if isinstance(direction_binding, dict) and isinstance(
                experience_binding, dict
            ):
                if direction_binding.get("web_case_id") != experience_binding.get(
                    "case_id"
                ):
                    errors.append(
                        f"{label}: rework direction preview must use the sustained experience version Case"
                    )
                if (
                    direction_binding.get("allowed_decisions")
                    != "CONTINUE,REWORK,REDIRECT,REJECT"
                ):
                    errors.append(
                        f"{label}: rework direction preview must include CONTINUE, REWORK, REDIRECT and REJECT"
                )
        if requires_strict_codex_baseline(iteration) or chat_required:
            errors.extend(
                validate_alpha_agent_comparison_binding(
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
                adaptive_engineering_qa=(
                    isinstance(manifest.get("answer_protocol"), dict)
                    and is_engineering_qa_adaptive_protocol(
                        manifest["answer_protocol"]
                    )
                ),
            )
        )
    answer_protocol = manifest.get("answer_protocol")
    if (
        supports_engineering_qa_hybrid(iteration)
        and isinstance(answer_protocol, dict)
        and is_engineering_qa_adaptive_protocol(answer_protocol)
    ):
        errors.extend(validate_engineering_qa_adaptive_gate(manifest, label))
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


def expected_verification_case_evidence(
    result_identifier: str, case_id: str
) -> str:
    """Return immutable historical evidence or the normal Result anchor."""

    return IMMUTABLE_HISTORICAL_CASE_EVIDENCE.get(
        (result_identifier, case_id), f"{result_identifier}#{case_id}"
    )


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


def strict_codex_frozen_question_count(
    alignment: dict[str, object], case_id: object
) -> int | None:
    """Resolve the precommitted question count for a strict Codex comparison."""

    raw_count: object = None
    if case_id == "V-000":
        raw_count = alignment.get("held_out_question_count")
    else:
        alpha_binding = alignment.get("alpha_agent_comparison_binding")
        if (
            isinstance(alpha_binding, dict)
            and alpha_binding.get("case_id") == case_id
        ):
            raw_count = alpha_binding.get("question_count")
        else:
            early_binding = alignment.get("early_comparison_binding")
            if (
                isinstance(early_binding, dict)
                and early_binding.get("case_id") == case_id
            ):
                canary_case_id = early_binding.get("canary_case_id")
                canary_bindings = alignment.get("early_hidden_canary_bindings")
                if isinstance(canary_bindings, dict):
                    for canary in canary_bindings.values():
                        if (
                            isinstance(canary, dict)
                            and canary.get("case_id") == canary_case_id
                        ):
                            raw_count = canary.get("question_count")
                            break
    return (
        raw_count
        if type(raw_count) is int and raw_count >= 1
        else None
    )


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
    strict_codex_baseline = requires_strict_codex_baseline(
        result.metadata.get("iteration", "")
    )
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
    positive_value_case_id = result.metadata.get("positive_value_case_id")
    strict_quality_gate_met: bool | None = None
    if strict_codex_baseline:
        if result.metadata.get(
            "mature_source_agent_comparison"
        ) != STRICT_CODEX_RESULT_COMPARISON:
            errors.append(
                f"{label}: mature_source_agent_comparison must equal {STRICT_CODEX_RESULT_COMPARISON}"
            )
        absolute_verdict = result.metadata.get("system_absolute_quality_verdict")
        if absolute_verdict not in {"PASS", "FAIL"}:
            errors.append(
                f"{label}: system_absolute_quality_verdict must equal PASS or FAIL"
            )
        frozen_question_count = strict_codex_frozen_question_count(
            alignment, positive_value_case_id
        )
        if frozen_question_count is None:
            errors.append(
                f"{label}: strict comparison Case must resolve an exact frozen question count"
            )
        raw_evaluated_question_count = result.metadata.get(
            "evaluated_question_count"
        )
        evaluated_question_count = (
            raw_evaluated_question_count
            if type(raw_evaluated_question_count) is int
            and raw_evaluated_question_count >= 1
            else None
        )
        if evaluated_question_count is None:
            errors.append(
                f"{label}: evaluated_question_count must be a positive integer"
            )
        elif (
            frozen_question_count is not None
            and evaluated_question_count != frozen_question_count
        ):
            errors.append(
                f"{label}: evaluated_question_count must equal the frozen question count"
            )
        count_values: dict[str, int | None] = {}
        for field in (
            "system_better_question_count",
            "tie_question_count",
            "codex_better_question_count",
            "both_fail_question_count",
            "unresolved_or_invalid_question_count",
        ):
            raw_value = result.metadata.get(field)
            value = (
                raw_value
                if type(raw_value) is int and raw_value >= 0
                else None
            )
            count_values[field] = value
            if value is None:
                errors.append(f"{label}: {field} must be a non-negative integer")
        classification_count_matches = (
            evaluated_question_count is not None
            and all(value is not None for value in count_values.values())
            and sum(
                value for value in count_values.values() if value is not None
            )
            == evaluated_question_count
        )
        if not classification_count_matches:
            errors.append(
                f"{label}: five answer-quality classification counts must sum to evaluated_question_count"
            )
        strict_quality_gate_met = (
            absolute_verdict == "PASS"
            and frozen_question_count is not None
            and evaluated_question_count == frozen_question_count
            and classification_count_matches
            and count_values["system_better_question_count"] is not None
            and count_values["system_better_question_count"] >= 1
            and count_values["codex_better_question_count"] == 0
            and count_values["both_fail_question_count"] == 0
            and count_values["unresolved_or_invalid_question_count"] == 0
        )
        if require_pass and absolute_verdict != "PASS":
            errors.append(
                f"{label}: system_absolute_quality_verdict must equal PASS for a passing comparison"
            )
        if require_pass and count_values["system_better_question_count"] in {None, 0}:
            errors.append(
                f"{label}: system_better_question_count must be at least 1 so an all-tie comparison cannot pass"
            )
        for field in (
            "codex_better_question_count",
            "both_fail_question_count",
            "unresolved_or_invalid_question_count",
        ):
            if require_pass and count_values[field] not in {None, 0}:
                errors.append(f"{label}: {field} must equal 0 for PASS")
    raw_positive_value_actual = result.metadata.get("positive_value_actual")
    positive_value_actual = (
        raw_positive_value_actual
        if type(raw_positive_value_actual) is int
        and (strict_codex_baseline or raw_positive_value_actual >= 0)
        else None
    )
    if positive_value_actual is None:
        errors.append(
            f"{label}: positive_value_actual must be an exact integer"
            if strict_codex_baseline
            else f"{label}: positive_value_actual must be a non-negative integer"
        )
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
        if strict_codex_baseline and threshold_met is not None:
            threshold_met = bool(threshold_met and strict_quality_gate_met)
        if require_pass and threshold_met is False:
            errors.append(
                f"{label}: answer quality must satisfy the positive frozen margin; the frozen comparison protocol separately forbids per-question regression"
                if strict_codex_baseline
                else f"{label}: positive_value_actual does not satisfy the frozen threshold"
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
    if strict_codex_baseline:
        if result.metadata.get(
            "mature_source_agent_identity_digest"
        ) != alignment.get("mature_source_agent_identity_digest"):
            errors.append(
                f"{label}: mature_source_agent_identity_digest must match the frozen Manifest"
            )
    adjudication_receipt = result.metadata.get(
        "positive_value_adjudication_receipt_ref"
    )
    adjudication_receipt_pattern = (
        r"independent-evaluator-result:sha256:[0-9a-f]{64}"
        if strict_codex_baseline
        else r"codex-user-message:sha256:[0-9a-f]{64}"
    )
    if not isinstance(adjudication_receipt, str) or re.fullmatch(
        adjudication_receipt_pattern, adjudication_receipt
    ) is None:
        errors.append(
            f"{label}: positive_value_adjudication_receipt_ref must bind an exact "
            + (
                "independent-evaluator-result digest"
                if strict_codex_baseline
                else "independent adjudication message"
            )
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
            "schema": (
                "software-world-model-positive-value-report/v2"
                if strict_codex_baseline
                else "software-world-model-positive-value-report/v1"
            ),
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
        if strict_codex_baseline:
            expected_report_fields.update(
                {
                    "mature_source_agent_identity_digest": result.metadata.get(
                        "mature_source_agent_identity_digest"
                    ),
                    "system_absolute_quality_verdict": result.metadata.get(
                        "system_absolute_quality_verdict"
                    ),
                    "evaluated_question_count": result.metadata.get(
                        "evaluated_question_count"
                    ),
                    "system_better_question_count": result.metadata.get(
                        "system_better_question_count"
                    ),
                    "tie_question_count": result.metadata.get(
                        "tie_question_count"
                    ),
                    "codex_better_question_count": result.metadata.get(
                        "codex_better_question_count"
                    ),
                    "both_fail_question_count": result.metadata.get(
                        "both_fail_question_count"
                    ),
                    "unresolved_or_invalid_question_count": result.metadata.get(
                        "unresolved_or_invalid_question_count"
                    ),
                }
            )
        expected_report_field_names = {
            *expected_report_fields,
            "measurement_input_digest",
        }
        if set(report_data) != expected_report_field_names:
            errors.append(
                f"{label}: positive value report must use only the exact "
                f"{'v2' if strict_codex_baseline else 'v1'} schema fields"
            )
        integer_fields = ["actual", "threshold", "reuse_horizon_questions"]
        if strict_codex_baseline:
            integer_fields.extend(
                (
                    "system_better_question_count",
                    "evaluated_question_count",
                    "tie_question_count",
                    "codex_better_question_count",
                    "both_fail_question_count",
                    "unresolved_or_invalid_question_count",
                )
            )
        for integer_field in integer_fields:
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


def validate_experience_delivery_result(
    result: Document,
    experience_policy: dict[str, object],
    provider_policy: dict[str, object],
    *,
    require_success: bool,
) -> list[str]:
    """Audit the first Alpha timebox and transparent Provider attempts."""

    label = result.relative_path
    errors: list[str] = []
    for field, expected in (
        ("experience_delivery_policy_schema", experience_policy.get("schema")),
        ("experience_delivery_access_case_id", experience_policy.get("access_case_id")),
        (
            "experience_delivery_timebox_case_id",
            experience_policy.get("timebox_case_id"),
        ),
        (
            "experience_delivery_quality_case_id",
            experience_policy.get("quality_case_id"),
        ),
        ("provider_route_policy_schema", provider_policy.get("schema")),
    ):
        if result.metadata.get(field) != expected:
            errors.append(f"{label}: {field} must match the frozen Manifest policy")

    started_at = result.metadata.get("experience_timebox_started_at")
    if not isinstance(started_at, str) or re.fullmatch(
        r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[^\s]+(?:Z|[+-][0-9]{2}:[0-9]{2})",
        started_at,
    ) is None:
        errors.append(
            f"{label}: experience_timebox_started_at must be an ISO-8601 timestamp with timezone"
        )
    else:
        try:
            datetime.fromisoformat(started_at.replace("Z", "+00:00"))
        except ValueError:
            errors.append(
                f"{label}: experience_timebox_started_at must be a real ISO-8601 timestamp"
            )

    elapsed_at_seal = non_negative_metadata_integer(
        result.metadata.get("experience_elapsed_minutes_at_result_seal")
    )
    if elapsed_at_seal is None:
        errors.append(
            f"{label}: experience_elapsed_minutes_at_result_seal must be a non-negative integer"
        )

    milestone_values: dict[str, int | None] = {}
    for field in (
        "page_launchable_elapsed_minutes",
        "sustained_user_operable_alpha_elapsed_minutes",
    ):
        raw_value = result.metadata.get(field)
        value = non_negative_metadata_integer(raw_value)
        if value is None and raw_value != "NOT_ACHIEVED":
            errors.append(
                f"{label}: {field} must be a non-negative integer or NOT_ACHIEVED"
            )
        milestone_values[field] = value

    delivery_verdict = result.metadata.get("experience_delivery_verdict")
    access_verdict = result.metadata.get("experience_access_gate_verdict")
    quality_verdict = result.metadata.get("experience_quality_gate_verdict")
    if delivery_verdict not in {"PASS", "FAIL"}:
        errors.append(f"{label}: experience_delivery_verdict must equal PASS or FAIL")
    if access_verdict not in {"PASS", "FAIL", "NOT_RUN"}:
        errors.append(
            f"{label}: experience_access_gate_verdict must equal PASS, FAIL or NOT_RUN"
        )
    if quality_verdict not in {"PASS", "FAIL", "NOT_RUN"}:
        errors.append(
            f"{label}: experience_quality_gate_verdict must equal PASS, FAIL or NOT_RUN"
        )

    page_elapsed = milestone_values.get("page_launchable_elapsed_minutes")
    alpha_elapsed = milestone_values.get(
        "sustained_user_operable_alpha_elapsed_minutes"
    )
    if delivery_verdict == "PASS" or require_success:
        if delivery_verdict != "PASS":
            errors.append(
                f"{label}: successful Alpha Result experience_delivery_verdict must equal PASS"
            )
        if page_elapsed is None or page_elapsed > 60:
            errors.append(
                f"{label}: successful Alpha Result must make the page launchable within 60 minutes"
            )
        if alpha_elapsed is None or alpha_elapsed > 180:
            errors.append(
                f"{label}: successful Alpha Result must be user-operable within 180 minutes"
            )
        if access_verdict != "PASS":
            errors.append(
                f"{label}: successful Alpha Result experience_access_gate_verdict must equal PASS"
            )
        if quality_verdict != "PASS":
            errors.append(
                f"{label}: successful Alpha Result experience_quality_gate_verdict must equal PASS before hardening"
            )

    hard_stop_triggered = result.metadata.get("experience_hard_stop_triggered")
    if not isinstance(hard_stop_triggered, bool):
        errors.append(f"{label}: experience_hard_stop_triggered must be a boolean")
    elif (
        elapsed_at_seal is not None
        and elapsed_at_seal >= 240
        and alpha_elapsed is None
        and not hard_stop_triggered
    ):
        errors.append(
            f"{label}: missing Alpha at 240 minutes must trigger the hard stop"
        )

    bounded_counts = (
        ("pre_first_experience_qualification_count", 1),
        ("pre_first_experience_smoke_question_count", 1),
        ("same_failure_signature_maximum_retry_count", 1),
        ("maximum_consecutive_no_user_visible_increment_count", 2),
        ("fallback_provider_attempt_count", 1),
    )
    for field, upper_bound in bounded_counts:
        value = non_negative_metadata_integer(result.metadata.get(field))
        if value is None or value > upper_bound:
            errors.append(
                f"{label}: {field} must be a non-negative integer no greater than {upper_bound}"
            )
    for field in (
        "pre_first_experience_full_regression_count",
        "external_dispatch_after_required_stop_count",
        "started_question_quality_chain_truncation_count",
        "same_provider_retry_count",
        "cross_attempt_intermediate_artifact_reuse_count",
        "user_resubmission_or_new_session_count",
        "late_primary_result_overwrite_count",
        "capability_failure_misclassified_as_unavailable_count",
        "application_source_security_failure_fallback_count",
    ):
        if non_negative_metadata_integer(result.metadata.get(field)) != 0:
            errors.append(f"{label}: {field} must equal zero")
    if non_negative_metadata_integer(result.metadata.get("live_attempt_count")) is None:
        errors.append(f"{label}: live_attempt_count must be a non-negative integer")

    provider_report_digest = result.metadata.get("provider_route_report_digest")
    if not isinstance(provider_report_digest, str) or re.fullmatch(
        r"sha256:[0-9a-f]{64}", provider_report_digest
    ) is None:
        errors.append(
            f"{label}: provider_route_report_digest must be an exact sha256 digest"
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
    answer_protocol = manifest.get("answer_protocol")
    engineering_qa_result = requires_engineering_qa_hybrid(iteration) or (
        isinstance(answer_protocol, dict)
        and is_engineering_qa_adaptive_protocol(answer_protocol)
    )
    if engineering_qa_result:
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
    expected_agent_comparison = (
        STRICT_CODEX_RESULT_COMPARISON
        if requires_strict_codex_baseline(iteration)
        else "non-regression"
    )
    if result.metadata.get("mature_source_agent_comparison") != expected_agent_comparison:
        errors.append(
            f"{label}: mature_source_agent_comparison must equal {expected_agent_comparison}"
        )
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
        and not requires_strict_codex_baseline(iteration)
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
    allow_unresolved_planning: bool = False,
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

    if not allow_unresolved_planning and (
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


def validate_exact_mapping_keys(
    value: dict[str, object], expected: set[str], label: str
) -> list[str]:
    """Fail closed when a frozen protocol silently drops or invents fields."""

    errors: list[str] = []
    missing = sorted(expected.difference(value))
    extra = sorted(set(value).difference(expected))
    if missing:
        errors.append(f"{label}: missing exact fields: {', '.join(missing)}")
    if extra:
        errors.append(f"{label}: unexpected fields: {', '.join(extra)}")
    return errors


def validate_engineering_qa_question_evidence_package_classes(
    package_classes: dict[str, object], label: str
) -> list[str]:
    """Separate affirmative support from retained boundary and audit evidence."""

    section_label = f"{label}: question_evidence_package_classes"
    errors = validate_exact_mapping_keys(
        package_classes,
        {
            "support_and_citation",
            "retained_non_support",
            "single_package_identity",
            "seal_confers_truth",
            "status",
        },
        section_label,
    )
    support = package_classes.get("support_and_citation")
    retained = package_classes.get("retained_non_support")
    if not isinstance(support, dict):
        errors.append(f"{section_label}.support_and_citation must be a mapping")
    else:
        errors.extend(
            validate_exact_mapping_keys(
                support,
                {
                    "admission",
                    "affirmative_claim_support_allowed",
                    "claim_citation_allowed",
                },
                f"{section_label}.support_and_citation",
            )
        )
        expected_support: dict[str, object] = {
            "admission": "modality-context-coverage-and-support-validated-only",
            "affirmative_claim_support_allowed": True,
            "claim_citation_allowed": True,
        }
        for field, expected in expected_support.items():
            if support.get(field) != expected:
                errors.append(
                    f"{section_label}.support_and_citation.{field} must equal {expected}"
                )
    if not isinstance(retained, dict):
        errors.append(f"{section_label}.retained_non_support must be a mapping")
    else:
        errors.extend(
            validate_exact_mapping_keys(
                retained,
                {
                    "required_entry_kinds",
                    "retention",
                    "affirmative_claim_support_allowed",
                    "affirmative_claim_citation_allowed",
                    "labeled_boundary_or_audit_reference_allowed",
                },
                f"{section_label}.retained_non_support",
            )
        )
        expected_retained: dict[str, object] = {
            "required_entry_kinds": (
                "boundary,audit-gap,failure,partial,conflict,unknown,"
                "rejected-decision-and-resource-receipt"
            ),
            "retention": "mandatory-in-ledger-and-current-sealed-package",
            "affirmative_claim_support_allowed": False,
            "affirmative_claim_citation_allowed": False,
            "labeled_boundary_or_audit_reference_allowed": True,
        }
        for field, expected in expected_retained.items():
            if retained.get(field) != expected:
                errors.append(
                    f"{section_label}.retained_non_support.{field} must equal {expected}"
                )
    for field, expected in (
        ("single_package_identity", True),
        ("seal_confers_truth", False),
        ("status", "frozen"),
    ):
        if package_classes.get(field) != expected:
            errors.append(f"{section_label}.{field} must equal {expected}")
    return errors


def engineering_qa_hardening_slice_ref(manifest: dict[str, object]) -> str | None:
    """Resolve the first engineering-hardening Slice after all feedback checkpoints."""

    development = manifest.get("development")
    slices = development.get("slices") if isinstance(development, dict) else None
    alignment = manifest.get("product_goal_alignment")
    if not isinstance(slices, dict) or not isinstance(alignment, dict):
        return None
    refs = [str(reference) for reference in slices]
    preview_binding = alignment.get("direction_preview_binding")
    preview_ref = (
        preview_binding.get("new_slice_ref")
        if isinstance(preview_binding, dict)
        else None
    )
    checkpoint = resolved_alpha_direction_slice_ref(alignment, refs) or preview_ref
    if checkpoint not in refs:
        return None
    index = refs.index(checkpoint)
    return refs[index + 1] if index + 1 < len(refs) else None


def engineering_qa_hardening_has_started(manifest: dict[str, object]) -> bool:
    """Return true only when the resolved hardening Slice has started."""

    hardening_ref = engineering_qa_hardening_slice_ref(manifest)
    development = manifest.get("development")
    slices = development.get("slices") if isinstance(development, dict) else None
    hardening = slices.get(hardening_ref) if isinstance(slices, dict) else None
    return not isinstance(hardening, dict) or hardening.get("status") != "proposed"


def _engineering_qa_new_freeze_receipt_errors(
    value: object,
    alignment: dict[str, object],
    field_label: str,
    *,
    hardening_authorization_ref: object,
    hardening_ref: str,
) -> list[str]:
    errors: list[str] = []
    if not isinstance(value, str) or re.fullmatch(
        r"codex-user-message:sha256:[0-9a-f]{64}", value
    ) is None:
        errors.append(f"{field_label} must bind an exact new user freeze receipt")
    elif value == alignment.get("positive_value_freeze_receipt_ref"):
        errors.append(
            f"{field_label} must not reuse positive_value_freeze_receipt_ref"
        )
    if value != hardening_authorization_ref:
        authorization_label = (
            "the current Slice 002"
            if hardening_ref == "ITER-010-SLICE-002"
            else hardening_ref
        )
        errors.append(
            f"{field_label} must equal {authorization_label} authorization_ref"
        )
    return errors


def validate_engineering_qa_reviewer_verification_investigation(
    verification: dict[str, object],
    answer_protocol: dict[str, object],
    alignment: dict[str, object],
    label: str,
    *,
    hardening_started: bool,
    hardening_authorization_ref: object,
    hardening_ref: str = "ITER-010-SLICE-002",
) -> list[str]:
    """Freeze an independent multi-step reviewer verification investigation."""

    section_label = f"{label}: reviewer_verification_investigation"
    expected_keys = {
        "role",
        "context",
        "inputs",
        "reviewer_operation_proposal_allowed",
        "adaptive_multi_step_required",
        "prior_verification_result_must_drive_next_step",
        "application_source_broker_worker_route_required",
        "direct_source_filesystem_shell_network_credential_or_tool_access",
        "returns_to_initial_investigation_model",
        "creates_new_ledger_revision_package_answer_and_review",
        "slice_001_preview_upper_bound",
        "slice_001_bound_scope",
        "hardening_fixed_round_upper_bound_allowed",
        "hardening_package_revision_fuse",
        "hardening_model_call_fuse",
        "hardening_source_broker_operation_fuse",
        "hardening_source_byte_fuse",
        "hardening_wall_time_fuse",
        "hardening_no_progress_fuse",
        "answerable_fuse_exhaustion_outcome",
        "boundary_fuse_exhaustion_outcome",
        "hardening_protocol_status",
        "hardening_authorization_status",
        "hardening_protocol_digest",
        "hardening_freeze_receipt_ref",
        "status",
    }
    if verification.get("protocol_role") == "legacy-compatibility":
        expected_keys.update(
            {
                "protocol_role",
                "legacy_protocol_schema",
                "superseded_as_default_by",
                "current_delivery_authorization_allowed",
                "historical_result_ref",
            }
        )
    errors = validate_exact_mapping_keys(verification, expected_keys, section_label)
    expected_values: dict[str, object] = {
        "role": "independent-verification-investigation-llm",
        "context": "fresh-context-without-initial-investigation-answer-or-review-session-state",
        "inputs": "immutable-specific-review-gap-current-package-and-current-ledger-prefix",
        "reviewer_operation_proposal_allowed": False,
        "adaptive_multi_step_required": True,
        "prior_verification_result_must_drive_next_step": True,
        "application_source_broker_worker_route_required": True,
        "direct_source_filesystem_shell_network_credential_or_tool_access": "denied",
        "returns_to_initial_investigation_model": False,
        "creates_new_ledger_revision_package_answer_and_review": True,
        "slice_001_preview_upper_bound": 1,
        "slice_001_bound_scope": (
            "direction-preview-only-not-a-permanent-protocol-round-cap"
        ),
        "hardening_fixed_round_upper_bound_allowed": False,
        "answerable_fuse_exhaustion_outcome": "fail",
        "boundary_fuse_exhaustion_outcome": (
            "independently-reviewed-honest-limitation-or-fail"
        ),
        "status": "frozen-slice-001-preview-boundary",
    }
    for field, expected in expected_values.items():
        if verification.get(field) != expected:
            errors.append(f"{section_label}.{field} must equal {expected}")

    preview_bound = answer_protocol.get(
        "slice_001_reviewer_verification_investigation_upper_bound"
    )
    if preview_bound != verification.get("slice_001_preview_upper_bound"):
        errors.append(
            f"{section_label}.slice_001_preview_upper_bound must match "
            "answer_protocol.slice_001_reviewer_verification_investigation_upper_bound"
        )

    fuse_fields = (
        "hardening_package_revision_fuse",
        "hardening_model_call_fuse",
        "hardening_source_broker_operation_fuse",
        "hardening_source_byte_fuse",
        "hardening_wall_time_fuse",
        "hardening_no_progress_fuse",
    )
    hardening_ordinal = hardening_ref.rsplit("-", 1)[-1]
    proposed_fuse = (
        "must-be-presealed-positive-high-safety-bound-before-slice-"
        f"{hardening_ordinal}-authorization"
    )
    if not hardening_started:
        for field in fuse_fields:
            if verification.get(field) != proposed_fuse:
                errors.append(
                    f"{section_label}.{field} must remain the explicit proposed fuse marker before hardening authorization"
                )
        for field, expected in (
            (
                "hardening_protocol_status",
                "proposed-not-frozen-requires-new-user-receipt-before-slice-"
                + hardening_ordinal,
            ),
            ("hardening_authorization_status", ENGINEERING_QA_NOT_AUTHORIZED),
            ("hardening_protocol_digest", ENGINEERING_QA_NOT_AUTHORIZED),
            ("hardening_freeze_receipt_ref", ENGINEERING_QA_NOT_AUTHORIZED),
        ):
            if verification.get(field) != expected:
                errors.append(f"{section_label}.{field} must equal {expected}")
        return errors

    numeric_fuses: dict[str, int] = {}
    for field in fuse_fields:
        value = verification.get(field)
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            errors.append(
                f"{section_label}.{field} must be an exact positive integer before hardening authorization"
            )
        else:
            numeric_fuses[field] = value
    model_calls = numeric_fuses.get("hardening_model_call_fuse")
    if model_calls is not None and model_calls < 2:
        errors.append(
            f"{section_label}.hardening_model_call_fuse must be at least 2 for multi-step verification"
        )
    revisions = numeric_fuses.get("hardening_package_revision_fuse")
    if revisions is not None and revisions < 2:
        errors.append(
            f"{section_label}.hardening_package_revision_fuse must be at least 2 so hardening is not a permanent one-round protocol"
        )
    if verification.get("hardening_protocol_status") != "frozen":
        errors.append(f"{section_label}.hardening_protocol_status must equal frozen")
    if verification.get("hardening_authorization_status") != "user-authorized":
        errors.append(
            f"{section_label}.hardening_authorization_status must equal user-authorized"
        )
    errors.extend(
        _engineering_qa_new_freeze_receipt_errors(
            verification.get("hardening_freeze_receipt_ref"),
            alignment,
            f"{section_label}.hardening_freeze_receipt_ref",
            hardening_authorization_ref=hardening_authorization_ref,
            hardening_ref=hardening_ref,
        )
    )
    frozen_protocol = {
        field: verification.get(field) for field in fuse_fields
    }
    actual_digest = canonical_mapping_digest(
        ENGINEERING_QA_REVIEWER_VERIFICATION_SCHEMA,
        "hardening_fuses",
        frozen_protocol,
    )
    if verification.get("hardening_protocol_digest") != actual_digest:
        errors.append(
            f"{section_label}.hardening_protocol_digest must bind the exact hardening fuses"
        )

    answer_attempts = answer_protocol.get("answer_attempt_upper_bound")
    rewrite_bound = answer_protocol.get("same_package_targeted_rewrite_upper_bound")
    if (
        isinstance(answer_attempts, int)
        and not isinstance(answer_attempts, bool)
        and isinstance(rewrite_bound, int)
        and not isinstance(rewrite_bound, bool)
        and revisions is not None
        and answer_attempts < 1 + rewrite_bound + revisions
    ):
        errors.append(
            f"{section_label}: answer_attempt_upper_bound must cover one new answer per allowed package revision"
        )
    hard_call_bound = answer_protocol.get(
        "hard_safety_model_call_upper_bound_per_question"
    )
    initial_investigation = answer_protocol.get("investigation_model_call_upper_bound")
    review_attempts = answer_protocol.get("review_attempt_upper_bound")
    question_calls = answer_protocol.get("question_understanding_model_call_upper_bound")
    if all(
        isinstance(value, int) and not isinstance(value, bool)
        for value in (
            hard_call_bound,
            initial_investigation,
            model_calls,
            answer_attempts,
            review_attempts,
            question_calls,
        )
    ):
        minimum_calls = (
            question_calls
            + initial_investigation
            + model_calls
            + answer_attempts
            + review_attempts
        )
        if hard_call_bound < minimum_calls:
            errors.append(
                f"{section_label}: hard_safety_model_call_upper_bound_per_question must reserve every verification investigation call, answer and comprehensive/challenge review"
            )
    return errors


def validate_engineering_qa_ablation(
    ablation: dict[str, object],
    alignment: dict[str, object],
    label: str,
    *,
    hardening_started: bool,
    hardening_authorization_ref: object,
    hardening_ref: str = "ITER-010-SLICE-002",
    final_ref: str = "ITER-010-SLICE-003",
) -> list[str]:
    """Freeze a fair three-arm cognition ablation before hardening starts."""

    section_label = f"{label}: engineering_qa_ablation"
    if ablation.get("schema") == CONVERSATIONAL_AGENT_ABLATION_SCHEMA:
        expected_keys = {
            "schema",
            "status",
            "authorization_required_before",
            "authorization_ref",
            "frozen_protocol_digest",
            "full_cognition_system_arm",
            "source_only_system_arm",
            "current_codex_external_baseline_arm",
            "system_arm_shared_runtime",
            "shared_evaluation_inputs",
            "forced_runtime_identity_across_all_three_arms",
            "technical_adjudication_owner",
            "product_direction_decision_owner",
            "quality_gate",
            "gain_gate",
            "cost_dimensions",
            "modeling_cost_accounting",
            "proposed_reuse_horizon_questions",
            "slice_001_required",
            "slice_001_case_id",
            "slice_002_case_id",
            "slice_003_case_id",
        }
        errors = validate_exact_mapping_keys(ablation, expected_keys, section_label)
        arm_expectations: dict[str, dict[str, object]] = {
            "full_cognition_system_arm": {
                "agent_runtime": "shared-system-arm-runtime",
                "cognition_input": "full-exact-world-model-cognition-context",
                "source_access": "controlled-read-only-source-tools",
            },
            "source_only_system_arm": {
                "agent_runtime": "shared-system-arm-runtime",
                "cognition_input": "none",
                "source_access": "controlled-read-only-source-tools",
            },
            "current_codex_external_baseline_arm": {
                "runtime": (
                    "preserve-actual-model-reasoning-tools-permissions-and-budget"
                ),
                "cognition_input": "none",
                "role": "external-baseline-not-oracle-not-reviewer",
            },
        }
        for arm, expected in arm_expectations.items():
            supplied = ablation.get(arm)
            if not isinstance(supplied, dict):
                errors.append(f"{section_label}.{arm} must be a mapping")
                continue
            errors.extend(
                validate_exact_mapping_keys(
                    supplied, set(expected), f"{section_label}.{arm}"
                )
            )
            for field, expected_value in expected.items():
                if supplied.get(field) != expected_value:
                    errors.append(
                        f"{section_label}.{arm}.{field} must equal {expected_value}"
                    )
        for field, expected in (
            (
                "authorization_required_before",
                "ITER-010-SLICE-001-live-comparison",
            ),
            (
                "system_arm_shared_runtime",
                "same-lead-agent-model-tools-permissions-budget-cache-policy-and-state",
            ),
            (
                "shared_evaluation_inputs",
                "same-exact-revision-questions-authorized-source-scope-output-constraints-and-blind-rubric",
            ),
            ("forced_runtime_identity_across_all_three_arms", False),
            (
                "technical_adjudication_owner",
                "independent-evaluator-not-answer-generator",
            ),
            ("product_direction_decision_owner", "user"),
            (
                "quality_gate",
                "each-arm-zero-major-error-boundary-correct-and-full-cognition-no-material-claim-regression",
            ),
            (
                "gain_gate",
                "full-cognition-must-have-precommitted-quality-or-normalized-cost-gain-versus-source-only-system-arm",
            ),
            (
                "cost_dimensions",
                "source-bytes-source-broker-operations-model-tokens-wall-time-provider-cost-and-world-model-build-update-storage-cost",
            ),
            (
                "modeling_cost_accounting",
                "exact-world-model-build-update-storage-and-provider-cost-amortized-over-frozen-reuse-horizon",
            ),
            ("slice_001_required", True),
            ("slice_001_case_id", "V-COMP-ALPHA-001"),
            ("slice_002_case_id", "V-COMP-EARLY-002"),
            ("slice_003_case_id", "V-COMP-001"),
        ):
            if ablation.get(field) != expected:
                errors.append(f"{section_label}.{field} must equal {expected}")
        reuse_horizon = ablation.get("proposed_reuse_horizon_questions")
        if type(reuse_horizon) is not int or reuse_horizon < 1:
            errors.append(
                f"{section_label}.proposed_reuse_horizon_questions must be a positive integer"
            )
        if not hardening_started:
            for field, expected in (
                ("status", "proposed-not-authorized"),
                ("authorization_ref", ENGINEERING_QA_NOT_AUTHORIZED),
                ("frozen_protocol_digest", ENGINEERING_QA_NOT_AUTHORIZED),
            ):
                if ablation.get(field) != expected:
                    errors.append(f"{section_label}.{field} must equal {expected}")
        else:
            if ablation.get("status") != "frozen":
                errors.append(f"{section_label}.status must equal frozen before hardening")
            authorization_ref = ablation.get("authorization_ref")
            if not isinstance(authorization_ref, str) or re.fullmatch(
                r"codex-user-message:sha256:[0-9a-f]{64}", authorization_ref
            ) is None:
                errors.append(
                    f"{section_label}.authorization_ref must bind an exact user receipt before hardening"
                )
            frozen_protocol = {
                field: value
                for field, value in ablation.items()
                if field not in {"status", "authorization_ref", "frozen_protocol_digest"}
            }
            expected_digest = canonical_mapping_digest(
                CONVERSATIONAL_AGENT_ABLATION_SCHEMA,
                "engineering_qa_ablation",
                frozen_protocol,
            )
            if ablation.get("frozen_protocol_digest") != expected_digest:
                errors.append(
                    f"{section_label}.frozen_protocol_digest must bind the exact conversational three-arm protocol"
                )
        return errors

    hardening_case_field = f"slice_{hardening_ref.rsplit('-', 1)[-1]}_case_id"
    final_case_field = f"slice_{final_ref.rsplit('-', 1)[-1]}_case_id"
    expected_keys = {
        "status",
        "authorization_required_before",
        "authorization_ref",
        "frozen_protocol_digest",
        "full_cognition_arm",
        "locator_only_or_empty_arm",
        "mature_source_agent_arm",
        "controlled_inputs",
        "quality_gate",
        "locator_control_quality_failure_effect",
        "gain_gate",
        "proposed_quality_gain_threshold",
        "proposed_non_locator_cost_ratio_threshold_ppm",
        "cost_dimensions",
        "modeling_cost_accounting",
        "proposed_reuse_horizon_questions",
        "slice_001_required",
        hardening_case_field,
        final_case_field,
    }
    errors = validate_exact_mapping_keys(ablation, expected_keys, section_label)
    arm_expectations: dict[str, dict[str, object]] = {
        "full_cognition_arm": {
            "cognition_input": "full-exact-world-model-cognition-context",
            "investigation_chain": (
                "shared-adaptive-investigation-source-broker-worker-ledger-package-answer-review"
            ),
        },
        "locator_only_or_empty_arm": {
            "cognition_input": (
                "predeclared-locator-only-projection-or-canonical-empty-when-no-locator-exists"
            ),
            "investigation_chain": "same-as-full-cognition-arm",
        },
        "mature_source_agent_arm": {
            "protocol_ref": "mature_source_agent_protocol_digest",
            "cognition_input": "none",
            "investigation_chain": "frozen-mature-source-agent",
        },
    }
    for arm, expected in arm_expectations.items():
        value = ablation.get(arm)
        if not isinstance(value, dict):
            errors.append(f"{section_label}.{arm} must be a mapping")
            continue
        errors.extend(
            validate_exact_mapping_keys(value, set(expected), f"{section_label}.{arm}")
        )
        for field, expected_value in expected.items():
            if value.get(field) != expected_value:
                errors.append(
                    f"{section_label}.{arm}.{field} must equal {expected_value}"
                )

    expected_scalars: dict[str, object] = {
        "authorization_required_before": f"{hardening_ref}-coding-or-execution",
        "controlled_inputs": (
            "same-exact-revision-model-questions-model-call-and-resource-budget-"
            "cache-policy-and-state-rubric-and-evaluator"
        ),
        "quality_gate": (
            "full-cognition-and-mature-source-agent-zero-major-error-boundary-correct-"
            "and-full-cognition-no-material-claim-regression-versus-mature-source-agent"
        ),
        "locator_control_quality_failure_effect": (
            "may-prove-quality-gain-but-cannot-lower-full-cognition-acceptance-threshold"
        ),
        "gain_gate": (
            "full-cognition-must-have-precommitted-quality-gain-or-precommitted-"
            "normalized-non-locator-investigation-cost-gain-versus-locator-only-or-empty-arm"
        ),
        "proposed_quality_gain_threshold": (
            "at-least-one-predeclared-material-checklist-gain-with-no-regression"
        ),
        "cost_dimensions": (
            "source-bytes-source-broker-operations-model-tokens-wall-time-provider-cost-"
            "and-world-model-build-update-storage-cost"
        ),
        "modeling_cost_accounting": (
            "exact-world-model-build-update-storage-and-provider-cost-amortized-over-"
            "frozen-reuse-horizon"
        ),
        "slice_001_required": False,
    }
    for field, expected in expected_scalars.items():
        if ablation.get(field) != expected:
            errors.append(f"{section_label}.{field} must equal {expected}")
    cost_ratio = ablation.get("proposed_non_locator_cost_ratio_threshold_ppm")
    if (
        isinstance(cost_ratio, bool)
        or not isinstance(cost_ratio, int)
        or not 1 <= cost_ratio < 1_000_000
    ):
        errors.append(
            f"{section_label}.proposed_non_locator_cost_ratio_threshold_ppm must be between 1 and 999999"
        )
    reuse_horizon = ablation.get("proposed_reuse_horizon_questions")
    if (
        isinstance(reuse_horizon, bool)
        or not isinstance(reuse_horizon, int)
        or reuse_horizon < 1
    ):
        errors.append(
            f"{section_label}.proposed_reuse_horizon_questions must be a positive integer"
        )
    for field, pattern in (
        (hardening_case_field, r"V-COMP-EARLY-[0-9]{3,}"),
        (final_case_field, r"V-COMP-[0-9]{3,}"),
    ):
        value = ablation.get(field)
        if not isinstance(value, str) or re.fullmatch(pattern, value) is None:
            errors.append(f"{section_label}.{field} must match {pattern}")

    if not hardening_started:
        for field, expected in (
            ("status", "proposed-not-authorized"),
            ("authorization_ref", ENGINEERING_QA_NOT_AUTHORIZED),
            ("frozen_protocol_digest", ENGINEERING_QA_NOT_AUTHORIZED),
        ):
            if ablation.get(field) != expected:
                errors.append(f"{section_label}.{field} must equal {expected}")
        return errors

    if ablation.get("status") != "frozen":
        errors.append(f"{section_label}.status must equal frozen before hardening")
    errors.extend(
        _engineering_qa_new_freeze_receipt_errors(
            ablation.get("authorization_ref"),
            alignment,
            f"{section_label}.authorization_ref",
            hardening_authorization_ref=hardening_authorization_ref,
            hardening_ref=hardening_ref,
        )
    )
    frozen_protocol = {
        field: value
        for field, value in ablation.items()
        if field not in {"status", "authorization_ref", "frozen_protocol_digest"}
    }
    actual_digest = canonical_mapping_digest(
        ENGINEERING_QA_ABLATION_SCHEMA,
        "engineering_qa_ablation",
        frozen_protocol,
    )
    if ablation.get("frozen_protocol_digest") != actual_digest:
        errors.append(
            f"{section_label}.frozen_protocol_digest must bind the exact three-arm protocol"
        )
    return errors


def validate_engineering_qa_adaptive_gate(
    manifest: dict[str, object], label: str
) -> list[str]:
    """Validate the three adaptive engineering-QA planning and hardening gates."""

    errors: list[str] = []
    alignment = manifest.get("product_goal_alignment")
    answer_protocol = manifest.get("answer_protocol")
    hybrid = manifest.get("hybrid_evidence_path")
    alignment = alignment if isinstance(alignment, dict) else {}
    answer_protocol = answer_protocol if isinstance(answer_protocol, dict) else {}
    hardening_started = engineering_qa_hardening_has_started(manifest)
    hardening_ref = engineering_qa_hardening_slice_ref(manifest)
    hardening_authorization_ref: object = None
    development = manifest.get("development")
    slices = development.get("slices") if isinstance(development, dict) else None
    refs = [str(reference) for reference in slices] if isinstance(slices, dict) else []
    if isinstance(slices, dict) and isinstance(hardening_ref, str):
        hardening_slice = slices.get(hardening_ref)
        if isinstance(hardening_slice, dict):
            hardening_authorization_ref = hardening_slice.get("authorization_ref")
    if hardening_ref is None:
        errors.append(f"{label}: engineering QA hardening Slice cannot be resolved")
        hardening_ref = "unresolved-hardening-slice"

    package_classes = manifest.get("question_evidence_package_classes")
    if not isinstance(package_classes, dict):
        errors.append(
            f"{label}: question_evidence_package_classes must be a mapping"
        )
    else:
        errors.extend(
            validate_engineering_qa_question_evidence_package_classes(
                package_classes, label
            )
        )
        if isinstance(hybrid, dict):
            if (
                hybrid.get("question_evidence_package_role")
                != "sealed-two-partition-support-citation-and-boundary-audit-set-not-truth-authority"
            ):
                errors.append(
                    f"{label}: hybrid_evidence_path.question_evidence_package_role must bind the two-partition package"
                )
            if hybrid.get("package_seal_confers_truth") is not False:
                errors.append(
                    f"{label}: hybrid_evidence_path.package_seal_confers_truth must remain false"
                )

    reviewer_verification = manifest.get("reviewer_verification_investigation")
    if not isinstance(reviewer_verification, dict):
        errors.append(
            f"{label}: reviewer_verification_investigation must be a mapping"
        )
    else:
        errors.extend(
            validate_engineering_qa_reviewer_verification_investigation(
                reviewer_verification,
                answer_protocol,
                alignment,
                label,
                hardening_started=hardening_started,
                hardening_authorization_ref=hardening_authorization_ref,
                hardening_ref=hardening_ref,
            )
        )

    ablation = manifest.get("engineering_qa_ablation")
    if not isinstance(ablation, dict):
        errors.append(f"{label}: engineering_qa_ablation must be a mapping")
    else:
        errors.extend(
            validate_engineering_qa_ablation(
                ablation,
                alignment,
                label,
                hardening_started=hardening_started,
                hardening_authorization_ref=hardening_authorization_ref,
                hardening_ref=hardening_ref,
                final_ref=refs[-1] if refs else "unresolved-final-slice",
            )
        )
    return errors


def validate_engineering_qa_answer_protocol_execution_readiness(
    answer_protocol: dict[str, object], label: str
) -> list[str]:
    """Freeze adaptive investigation, evidence sealing, answer and review bounds."""

    errors: list[str] = []
    if answer_protocol.get("schema") != ENGINEERING_QA_ADAPTIVE_PROTOCOL_SCHEMA:
        errors.append(
            f"{label}: answer_protocol.schema must equal "
            f"{ENGINEERING_QA_ADAPTIVE_PROTOCOL_SCHEMA}"
        )
    if (
        answer_protocol.get("contract_ref")
        != "SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING"
    ):
        errors.append(
            f"{label}: answer_protocol.contract_ref must equal "
            "SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING"
        )
    if not is_engineering_qa_adaptive_protocol(answer_protocol):
        errors.append(
            f"{label}: answer_protocol.mode must equal "
            f"{ENGINEERING_QA_ADAPTIVE_PROTOCOL_MODE}"
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
        "investigation_model_call_upper_bound",
        "max_investigation_steps_per_question",
        "slice_001_reviewer_verification_investigation_upper_bound",
        "max_source_broker_operations_per_question",
        "max_source_files_per_question",
        "max_source_bytes_per_question",
        "max_repository_document_bytes_per_question",
        "max_build_configuration_bytes_per_question",
        "max_test_bytes_per_question",
        "max_world_model_result_bytes_per_question",
        "max_sealed_evidence_package_bytes_per_question",
        "max_support_items_per_question",
        "max_evidence_ledger_bytes_per_question",
        "max_wall_time_milliseconds_per_question",
        "initial_answer_model_calls",
        "independent_review_model_calls_per_authorizable_draft",
        "final_answer_role_call_reserve",
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
        "slice_001_reviewer_verification_investigation_upper_bound": 1,
        "initial_answer_model_calls": 1,
        "independent_review_model_calls_per_authorizable_draft": 2,
        "final_answer_role_call_reserve": 3,
        "same_package_targeted_rewrite_upper_bound": 1,
    }
    for field, expected in exact_numeric_values.items():
        value = numeric_fields.get(field)
        if value is not None and value != expected:
            errors.append(
                f"{label}: answer_protocol.{field} must equal {expected}"
            )
    for field in (
        "investigation_model_call_upper_bound",
        "max_investigation_steps_per_question",
    ):
        value = numeric_fields.get(field)
        if value is not None and value < 2:
            errors.append(
                f"{label}: answer_protocol.{field} must be at least 2 for adaptive result-driven investigation"
            )
    investigation_calls_bound = numeric_fields.get(
        "investigation_model_call_upper_bound"
    )
    investigation_steps_bound = numeric_fields.get(
        "max_investigation_steps_per_question"
    )
    if (
        investigation_calls_bound is not None
        and investigation_steps_bound is not None
        and investigation_steps_bound < investigation_calls_bound
    ):
        errors.append(
            f"{label}: answer_protocol.max_investigation_steps_per_question must cover every allowed investigation model call"
        )

    answer_attempts = numeric_fields.get("answer_attempt_upper_bound")
    rewrite_bound = numeric_fields.get("same_package_targeted_rewrite_upper_bound")
    verification_bound = numeric_fields.get(
        "slice_001_reviewer_verification_investigation_upper_bound"
    )
    initial_answer_calls = numeric_fields.get("initial_answer_model_calls")
    if (
        answer_attempts is not None
        and rewrite_bound is not None
        and verification_bound is not None
        and initial_answer_calls is not None
        and answer_attempts
        < initial_answer_calls + rewrite_bound + verification_bound
    ):
        errors.append(
            f"{label}: answer_protocol.answer_attempt_upper_bound must cover at least "
            "the initial answer, the allowed same-package targeted rewrite and the "
            "Slice 001 new answer after reviewer verification investigation"
        )
    review_attempts = numeric_fields.get("review_attempt_upper_bound")
    if (
        review_attempts is not None
        and answer_attempts is not None
        and review_attempts < answer_attempts + 1
    ):
        errors.append(
            f"{label}: answer_protocol.review_attempt_upper_bound must cover "
            "every answer attempt plus the final evidence-boundary challenge"
        )
    hard_call_bound = numeric_fields.get(
        "hard_safety_model_call_upper_bound_per_question"
    )
    question_calls = numeric_fields.get(
        "question_understanding_model_call_upper_bound"
    )
    investigation_calls = numeric_fields.get(
        "investigation_model_call_upper_bound"
    )
    if all(
        value is not None
        for value in (
            hard_call_bound,
            question_calls,
            investigation_calls,
            answer_attempts,
            review_attempts,
        )
    ):
        minimum_core_calls = (
            question_calls
            + investigation_calls
            + answer_attempts
            + review_attempts
        )
        if hard_call_bound < minimum_core_calls:
            errors.append(
                f"{label}: answer_protocol.hard_safety_model_call_upper_bound_per_question "
                "must cover question understanding, adaptive investigation, every "
                "answer attempt and every independent review"
            )

    for field in (
        "upfront_complete_retrieval_plan_required",
        "sealed_package_mutation_allowed",
        "quality_checklist_reduction_due_to_remaining_calls_allowed",
        "evidence_requirement_reduction_due_to_remaining_calls_allowed",
        "review_skipping_due_to_remaining_calls_allowed",
        "reviewer_verification_returns_to_initial_investigation_model",
        "reviewer_verification_fixed_round_cap_after_slice_001_allowed",
        "question_or_project_keyword_symbol_class_method_fixture_or_oracle_special_routing_allowed",
        "provider_request_retries_allowed",
        "provider_switch_after_dispatch_allowed",
        "provider_finish_parent-evidence-references-returned-by-provider",
        "provider_review_returns-independent-decision-or-verification-request",
        "reviewer_draft-only-scope-expansion-may-trigger-new-evidence-investigation",
        "reviewer_evidence_boundary_projection_is-semantic-verdict",
        "configuration_placeholder_proves_concrete_runtime_value",
        "caller-import-or-registration-proves-unmounted-fields-validation-or-output",
    ):
        if answer_protocol.get(field) is not False:
            errors.append(f"{label}: answer_protocol.{field} must be false")
    for field in (
        "investigation_proposal_must_consider_prior_results",
        "source_broker_policy_compilation_required",
        "evidence_ledger_append_only",
        "question_evidence_package_sealed_after_investigation",
        "finish_material_observations_required",
        "material_observation_identity_application_owned",
        "answer_claim_material_observation_and_evidence_closure_required",
        "reviewer_independent_package_and_draft_observation_audit_required",
        "safety_budget_reserves_answer-comprehensive-review-and-challenge-review",
        "reviewer_more_evidence_requires_specific_verifiable_gap",
        "reviewer_verification_request_requires_application_and_source_broker_revalidation",
        "reviewer_verification_uses_independent_fresh_context_adaptive_investigation",
        "reviewer_verification_creates_new_ledger_revision",
        "reviewer_verification_creates_new_package",
        "new_answer_after_new_package_required",
        "same_package_rewrite_requires_specific_reviewer_finding",
        "independent_rereview_after_any_answer_or_package_change_required",
        "deterministic_grounding_authorization_revision-allowlist-and-package-seal_checks",
        "reviewer_rewrite-finding-requires-current-package-entry-ids",
        "reviewer_missing-evidence-finding-requires-material-checklist-class-and-need",
        "answer_rewrite_preserves_every-supported-material-observation",
        "challenge_review_non-passing-disposition-requires-finding-on-exact-challenged-claim",
        "challenge_review_shared-finding-code-requires-claim-in-every-bound-challenge",
        "verification-successor-may-reuse-predecessor-support",
        "reviewer_original-question-fulfillment-scan-required",
        "challenge_review_specialized-disposition-kind-match-required",
        "reviewer_full-content-material-effect-application-observations-projected",
        "challenge_review_material-effect-layer-binding-application-verified",
    ):
        if answer_protocol.get(field) is not True:
            errors.append(f"{label}: answer_protocol.{field} must be true")
    expected_structured_protocol_values = {
        "provider_finish_disposition_shape": (
            "single-outcome-tagged-finish-dispositions-array"
        ),
        "provider_finish_disposition_partition": (
            "one-list-covers-each-checklist-item-exactly-once"
        ),
        "provider_finish_parent-evidence-reference-derivation": (
            "trusted-stable-first-occurrence-union-of-child-observation-references"
        ),
        "provider_review_finding-remediation-vocabulary": (
            "rewrite-with-existing-evidence,investigate-missing-evidence,"
            "reject-unrecoverable"
        ),
        "reviewer_action-and-verification-request-derivation": (
            "application-owned-reject-then-missing-evidence-then-rewrite-"
            "then-empty-approved"
        ),
        "review_focus_order": (
            "comprehensive-then-evidence-boundary-challenge"
        ),
        "reviewer_evidence_boundary_challenge_projection": (
            "cited-configuration-placeholders-plus-claim-status-literals-"
            "absent-from-cited-content-plus-mentioned-same-application-types-"
            "without-mounted-implementation-plus-cited-full-content-java-entry-"
            "material-effect-scans-plus-original-question-fulfillment-scan"
        ),
        "answer_material_observation_coverage_contract": (
            "exact-id-statement-kind-checklist-and-required-evidence-entry-"
            "table-before-large-role-inputs"
        ),
        "reviewer_full-content-material-effect-scan-unit": (
            "each-cited-full-content-java-entry"
        ),
        "reviewer_full-content-material-effect-categories": (
            "persistence-write,audit-write,cache-mutation,notification,"
            "external-interaction"
        ),
        "challenge_review_assessment_fields": (
            "evidence-boundary,draft-scope,disposition,finding-code-plus-"
            "material-effect-layer-and-exact-statements-for-effect-omission"
        ),
        "challenge_review_material-effect-omission-layer-vocabulary": (
            "application-package,default-draft"
        ),
        "challenge_review_material-effect-application-package-remediation": (
            "same-evidence-class-verification-and-effect-absent-from-exact-"
            "package-observations"
        ),
        "challenge_review_material-effect-default-draft-remediation": (
            "challenged-entry-rewrite-and-effect-present-in-exact-package-"
            "observations"
        ),
        "reviewer_original-question-fulfillment-dimensions": (
            "direct-user-goal,ordered-user-actions,input-output-handoffs,"
            "known-unknown-boundary,material-outcomes"
        ),
        "challenge_review_disposition_vocabulary": (
            "within-evidence-boundary,draft-exceeds-evidence-boundary,"
            "draft-omits-material-effect,draft-omits-material-requirement"
        ),
        "package-material-effect-observation-omission-remediation": (
            "successor-gap-delta-with-predecessor-support-reuse"
        ),
    }
    for field, expected in expected_structured_protocol_values.items():
        if answer_protocol.get(field) != expected:
            errors.append(
                f"{label}: answer_protocol.{field} must equal {expected}"
            )
    if (
        answer_protocol.get("resource_exhaustion_behavior")
        != "answerable-fail-boundary-limitation-only-if-independently-approved-otherwise-fail-closed"
    ):
        errors.append(
            f"{label}: answer_protocol.resource_exhaustion_behavior must equal "
            "answerable-fail-boundary-limitation-only-if-independently-approved-otherwise-fail-closed"
        )

    legacy_fields = (
        "planner_model_calls",
        "draft_model_calls",
        "independent_reviewer_model_calls",
        "exact_total_model_calls_per_question",
        "initial_retrieval_rounds",
        "targeted_reretrieval_round_upper_bound",
        "reviewer_verification_request_round_upper_bound",
        "max_retrieval_steps_per_round",
        "max_investigation_steps",
        "max_investigation_model_calls",
        "planner_model_call_upper_bound",
        "total_model_call_upper_bound_per_question",
        "independent_review_model_calls_per_attempt",
        "safety_budget_reserves_independent_review",
        "max_query_bytes_per_step",
        "max_result_bytes_per_step",
        "max_total_query_bytes_per_question",
        "max_total_result_bytes_per_question",
        "max_trace_bytes_per_question",
        "targeted_reretrieval_requires_specific_reviewer_evidence_gap",
        "reseal_after_targeted_reretrieval_required",
        "independent_rereview_after_any_rewrite_or_reseal_required",
        "reviewer_verification_uses_source_broker",
        "budget_exhaustion_behavior",
        "deterministic_schema_grounding_and_authorization_checks",
        "retries_allowed",
    )
    for field in legacy_fields:
        if field in answer_protocol:
            errors.append(
                f"{label}: engineering QA answer_protocol.{field} is a legacy field"
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
    """Keep adaptive source investigation isolated and evidence-backed."""

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
        "world_model_role": (
            "persistent-versioned-verifiable-updatable-external-software-cognition"
        ),
        "world_model_cognition_dimensions": (
            "context-entities-relations-behavior-constraints-state-evidence-"
            "coverage-and-unknown-boundaries"
        ),
        "world_model_is_only_manual_map_cache_or_retrieval_hints": False,
        "world_model_as_question-time-source-recall_gate_allowed": False,
        "world_model_required_as_source_retrieval_gate": False,
        "investigation_inputs": (
            "immutable-original-question-exact-world-model-cognition-and-prior-"
            "ledger-results"
        ),
        "zero-irrelevant-or-insufficient-snapshot_blocks_exact-revision-retrieval": False,
        "snapshot_source_revision_compatibility": (
            "exact-match-or-explicit-partitioned-version-comparison-otherwise-"
            "unaligned-navigation-only"
        ),
        "investigation_model_role": (
            "independent-adaptive-result-driven-read-operation-proposal"
        ),
        "investigation_model_direct_source_access": "denied",
        "source_broker_role": (
            "policy-compile-and-authorize-allowlisted-read-only-exact-revision-"
            "operations"
        ),
        "retrieval_worker_role": "isolated-execution-only",
        "retrieval_worker_sources": (
            "exact-revision-source-repository-documents-build-configuration-tests"
        ),
        "retrieval_worker_access": "read-only-allowlisted-audited",
        "source_trust": "untrusted-input",
        "live_provider_source-fragment-disclosure": (
            "separately-authorized-exact-provider-model-role-and-allowlist-only"
        ),
        "evidence_ledger": "append-only-per-question-until-seal",
        "evidence_ledger_seal_trigger": (
            "investigation-finish-or-fail-closed-stop"
        ),
        "question_evidence_package_role": (
            "sealed-two-partition-support-citation-and-boundary-audit-set-not-"
            "truth-authority"
        ),
        "package_seal_confers_truth": False,
        "sealed_package_mutation_allowed": False,
        "answer_repository_access": "denied",
        "answer_direct_source_authority": "denied",
        "reviewer_repository_access": "denied",
        "reviewer_direct_source_authority": "denied",
        "reviewer_direct_shell_network_credential_or_tool_access": "denied",
        "answer_input": (
            "immutable-original-question-question-understanding-and-sealed-"
            "question-evidence-package-only"
        ),
        "reviewer_input": (
            "immutable-original-question-question-understanding-sealed-question-"
            "evidence-package-and-draft-only"
        ),
        "reviewer_more_evidence_route": (
            "specific-verifiable-gap-through-independent-verification-"
            "investigation-application-source-broker-worker-new-ledger-revision-"
            "new-package-new-answer-new-review"
        ),
        "reviewer_verification_request_role": (
            "application-derived-versioned-gap-request-from-typed-finding-binding-"
            "checklist-claim-evidence-class-and-need"
        ),
        "reviewer_verification_returns_to_initial_investigation_model": False,
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
    for field in (
        "world_model_retrieval_hint_or_candidate_reduction_only",
        "retrieval_plan_inputs",
        "model_role",
        "fact_authority",
    ):
        if field in hybrid_evidence_path:
            errors.append(
                f"{label}: adaptive hybrid_evidence_path.{field} is a replaced field"
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

    engineering_qa_mode = is_engineering_qa_adaptive_protocol(answer_protocol)
    if requires_engineering_qa_hybrid(iteration) and not engineering_qa_mode:
        return [
            f"{label}: ITER-010 answer_protocol.mode must equal "
            f"{ENGINEERING_QA_ADAPTIVE_PROTOCOL_MODE}"
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
    alignment: dict[str, object], label: str, iteration: object = ""
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
    if requires_strict_codex_baseline(iteration):
        errors.extend(validate_strict_codex_baseline_alignment(alignment, label))
    return errors


def validate_alpha_staged_execution_inputs(
    manifest: dict[str, object],
    alignment: dict[str, object],
    new_refs: list[str],
    label: str,
    iteration: object = "",
) -> list[str]:
    """Defer Alpha-only corpora and hidden/comparison freezes until their Slice."""

    alpha_ref = resolved_alpha_direction_slice_ref(alignment, new_refs)
    if alpha_ref is None:
        return []
    errors: list[str] = []
    development = manifest.get("development")
    slices = development.get("slices") if isinstance(development, dict) else None
    alpha_slice = slices.get(alpha_ref) if isinstance(slices, dict) else None
    alpha_started = not isinstance(alpha_slice, dict) or alpha_slice.get("status") != "proposed"
    alpha_corpus = alignment.get("alpha_visible_development_corpus_digest")
    if alpha_started:
        if not isinstance(alpha_corpus, str) or re.fullmatch(r"sha256:[0-9a-f]{64}", alpha_corpus) is None:
            errors.append(f"{label}: alpha_visible_development_corpus_digest must be exact once Alpha starts")
    elif alpha_corpus != (
        "not-frozen-requires-slice-" + alpha_ref.rsplit("-", 1)[-1] + "-authorization"
    ):
        errors.append(f"{label}: alpha_visible_development_corpus_digest must remain deferred before Alpha")

    hardening_ref = engineering_qa_hardening_slice_ref(manifest)
    hardening_started = engineering_qa_hardening_has_started(manifest)
    readiness = manifest.get("readiness_inputs")
    readiness = readiness if isinstance(readiness, dict) else {}
    hardening_ordinal = (
        hardening_ref.rsplit("-", 1)[-1] if isinstance(hardening_ref, str) else "unknown"
    )
    strict_codex_baseline = requires_strict_codex_baseline(iteration)
    if not hardening_started:
        deferred_value = (
            "not-frozen-requires-new-user-receipt-before-slice-" + hardening_ordinal
        )
        if strict_codex_baseline:
            errors.extend(
                validate_positive_value_execution_readiness(
                    alignment, label, iteration
                )
            )
        else:
            for field in (
                "positive_value_metric",
                "positive_value_unit",
                "positive_value_comparison",
                "positive_value_threshold",
                "positive_value_reuse_horizon_questions",
            ):
                if alignment.get(field) != deferred_value:
                    errors.append(f"{label}: {field} must remain deferred before hardening")
        if readiness.get("hidden_freeze_protocol_digest") != f"pending-until-slice-{hardening_ordinal}-freeze":
            errors.append(f"{label}: hidden_freeze_protocol_digest must remain deferred before hardening")
        if readiness.get("hidden_freeze_receipt_ref") != ENGINEERING_QA_NOT_AUTHORIZED:
            errors.append(f"{label}: hidden_freeze_receipt_ref must remain not-authorized before hardening")
        return errors

    errors.extend(
        validate_positive_value_execution_readiness(alignment, label, iteration)
    )
    hidden_digest = readiness.get("hidden_freeze_protocol_digest")
    if not isinstance(hidden_digest, str) or re.fullmatch(r"sha256:[0-9a-f]{64}", hidden_digest) is None:
        errors.append(f"{label}: hidden_freeze_protocol_digest must be exact once hardening starts")
    hardening_slice = slices.get(hardening_ref) if isinstance(slices, dict) else None
    authorization_ref = hardening_slice.get("authorization_ref") if isinstance(hardening_slice, dict) else None
    errors.extend(
        _engineering_qa_new_freeze_receipt_errors(
            readiness.get("hidden_freeze_receipt_ref"),
            alignment,
            f"{label}: hidden_freeze_receipt_ref",
            hardening_authorization_ref=authorization_ref,
            hardening_ref=hardening_ref or "unresolved-hardening-slice",
        )
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
        (
            catalog_digest,
            assumption_expectations,
            historical_catalog_digest,
            _,
            catalog_errors,
        ) = critical_assumption_catalogs(
            proposal,
            manifest,
            label,
        )
        errors.extend(catalog_errors)
        supplied_catalog_digest = alignment.get(
            "critical_assumption_catalog_digest"
        )
        if supplied_catalog_digest != catalog_digest:
            errors.append(
                f"{label}: critical_assumption_catalog_digest must match the exact current assumption catalog"
            )
        critical_assumption_ids = resolved_assumption_ids(
            alignment.get("critical_assumption_ids")
        )
        if critical_assumption_ids != list(assumption_expectations):
            errors.append(
                f"{label}: critical_assumption_ids must exactly match the current assumption catalog order"
            )
        readiness = by_id.get(f"{iteration}-READINESS")
        iteration_data = manifest.get("iteration")
        paused_cutover = (
            conversational_agent_cutover_active(manifest)
            and isinstance(iteration_data, dict)
            and iteration_data.get("status") == "paused"
        )
        expected_readiness_catalog = (
            historical_catalog_digest if paused_cutover else catalog_digest
        )
        if readiness is None or readiness.metadata.get(
            "critical_assumption_catalog_digest"
        ) != expected_readiness_catalog:
            errors.append(
                f"{label}: Readiness must bind the catalog applicable to its historical or current authorization"
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

    if requires_strict_codex_baseline(iteration):
        errors.extend(
            validate_positive_value_execution_readiness(
                alignment, label, iteration
            )
        )

    defer_early_evaluation = direction_preview_hardening_is_deferred(
        manifest,
        alignment,
        new_refs,
        direction_preview_enabled=requires_direction_preview(iteration),
    )
    alpha_ref = resolved_alpha_direction_slice_ref(alignment, new_refs)
    if alpha_ref is not None:
        errors.extend(
            validate_alpha_staged_execution_inputs(
                manifest, alignment, new_refs, label, iteration
            )
        )
    elif (
        requires_reflection_gate(iteration)
        and len(new_refs) > 1
        and not defer_early_evaluation
    ):
        errors.extend(
            validate_positive_value_execution_readiness(
                alignment, label, iteration
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
    engineering_qa_mode = is_engineering_qa_adaptive_protocol(answer_protocol)
    chat_mode = conversational_agent_cutover_active(manifest)
    if chat_mode:
        errors.extend(validate_conversational_architecture_cutover(manifest, label))
        errors.extend(
            validate_conversational_engineering_agent(
                manifest,
                alignment,
                new_refs,
                blocking_case_ids,
                label,
                required=True,
            )
        )
    elif requires_engineering_qa_hybrid(iteration) or engineering_qa_mode:
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
    if requires_direction_preview(iteration) and not chat_mode:
        errors.extend(
            validate_direction_preview_answer_entry(
                alignment, answer_protocol, label
            )
        )

    readiness_inputs = manifest.get("readiness_inputs")
    if not isinstance(readiness_inputs, dict):
        errors.append(f"{label}: readiness_inputs must be a mapping before Slice execution")
        readiness_inputs = {}
    if chat_mode:
        architecture_decision = readiness_inputs.get(
            "required_architecture_decision"
        )
        if architecture_decision != "SYS-ADR-018":
            errors.append(
                f"{label}: conversational Agent required_architecture_decision must equal SYS-ADR-018"
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
                f"{label}: conversational Agent architecture decision must resolve to an accepted normative system-decision"
            )
    elif engineering_qa_mode:
        errors.extend(
            validate_answer_hierarchy_protocol(manifest, label, require_frozen=True)
        )
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
    current_answer_contract = (
        readiness_inputs.get("answer_protocol_contract_ref")
        if chat_mode
        else answer_protocol.get("contract_ref")
    )
    for reference in (source_scope.get("contract_ref"), current_answer_contract):
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
        "system_contract_set_digest",
    ):
        value = (
            frontend.get(field)
            if field
            != "system_contract_set_digest"
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
    elif alpha_ref is None:
        hidden_digest = readiness_inputs.get("hidden_freeze_protocol_digest")
        if not isinstance(hidden_digest, str) or re.fullmatch(
            r"sha256:[0-9a-f]{64}", hidden_digest
        ) is None:
            errors.append(f"{label}: hidden_freeze_protocol_digest must be an exact sha256 digest")
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
    require_paused_slice_sequence: bool = False,
    require_superseded_slice_sequence: bool = False,
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
    experience_delivery_policy = manifest.get("experience_delivery_policy")
    if (
        isinstance(experience_delivery_policy, dict)
        and isinstance(
            experience_delivery_policy.get("historical_pre_policy_result_refs"),
            dict,
        )
    ):
        experience_delivery_policy["historical_pre_policy_result_refs"] = (
            manifest_resolved_sequence_items(
                text,
                "experience_delivery_policy",
                "historical_pre_policy_result_refs",
            )
            or []
        )
    development = manifest.get("development")
    raw_slices = development.get("slices") if isinstance(development, dict) else None
    if isinstance(raw_slices, dict):
        for reference in new_refs:
            state = raw_slices.get(reference)
            if not isinstance(state, dict):
                continue
            for sequence_field in (
                "rework_result_refs",
                "prior_authorization_refs",
            ):
                if not isinstance(state.get(sequence_field), dict):
                    continue
                resolved_items = manifest_resolved_nested_sequence_items(
                    text,
                    ("development", "slices", reference, sequence_field),
                )
                if resolved_items is not None:
                    state[sequence_field] = resolved_items
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
                    or require_paused_slice_sequence
                ),
            )
        )
    if require_superseded_slice_sequence:
        errors.extend(
            validate_superseded_iteration_plan(
                new_refs,
                by_id,
                manifest,
                label,
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
    errors.extend(
        validate_historical_gate_catalog(
            manifest,
            blocking_case_ids,
            verification,
            label,
        )
    )
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
        experience_delivery_policy = manifest.get("experience_delivery_policy")
        delivery_owner_ref = resolved_sustained_alpha_slice_ref(
            alignment, new_refs
        )
        if (
            isinstance(experience_delivery_policy, dict)
            and reference == delivery_owner_ref
        ):
            for field in (
                "access_case_id",
                "timebox_case_id",
                "quality_case_id",
            ):
                delivery_case = experience_delivery_policy.get(field)
                if isinstance(delivery_case, str):
                    required_owned.add(delivery_case)
        experience_binding = alignment.get("experience_version_binding")
        if (
            isinstance(experience_binding, dict)
            and experience_binding.get("new_slice_ref") == reference
        ):
            experience_case = experience_binding.get("case_id")
            if isinstance(experience_case, str):
                required_owned.add(experience_case)
        conversational_agent = manifest.get("conversational_engineering_agent")
        if (
            isinstance(conversational_agent, dict)
            and conversational_agent.get("owner_slice_ref") == reference
            and isinstance(conversational_agent.get("chat_case_id"), str)
        ):
            required_owned.add(str(conversational_agent["chat_case_id"]))
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
                "alpha_agent_comparison_binding",
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
                f"{target.relative_path}: Slice gate Cases must include its owned cross-domain, Web, ad-hoc, experience access/timebox/quality, Alpha Agent comparison, early-evaluation, conditional-falsifier and reflection Cases"
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
                require_paused=require_paused_slice_sequence,
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
    rework_policy: dict[str, object] | None = None,
    enforce_manifest_decision: bool = True,
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
        if decision not in {"REWORK", "REDIRECT", "REJECT"}:
            errors.append(
                f"{label}: non-success {target.identifier} reflection_decision must equal REWORK, REDIRECT or REJECT"
            )
    elif decision != binding.get("success_decision"):
        errors.append(
            f"{label}: completed {target.identifier} reflection_decision must equal its Manifest success_decision"
        )
    if rework_policy is not None and decision == "REDIRECT":
        redirect_basis = result.metadata.get("reflection_redirect_basis")
        if redirect_basis not in {
            "explicit-user-direction-change",
            "core-architecture-falsified",
            "precommitted-no-progress-limit-reached",
        }:
            errors.append(
                f"{label}: {target.identifier} REDIRECT must bind an allowed explicit redirect basis"
            )
        elif redirect_basis == "core-architecture-falsified" and (
            result.metadata.get("reflection_issue_class") != "architecture"
            or result.metadata.get("reflection_issue_scope") != "systemic"
        ):
            errors.append(
                f"{label}: {target.identifier} core-architecture REDIRECT requires an architecture/systemic diagnosis"
            )
        elif redirect_basis == "precommitted-no-progress-limit-reached":
            attempt = result.metadata.get("rework_attempt_number")
            limit = rework_policy.get("no_progress_attempt_limit")
            history = manifest_slice.get("rework_result_refs")
            history_count = len(history) if isinstance(history, list) else 0
            if (
                isinstance(attempt, bool)
                or not isinstance(attempt, int)
                or isinstance(limit, bool)
                or not isinstance(limit, int)
                or attempt < limit
            ):
                errors.append(
                    f"{label}: {target.identifier} no-progress REDIRECT must reach the precommitted attempt limit"
                )
            if not isinstance(attempt, bool) and isinstance(attempt, int) and (
                not isinstance(history, list)
                or not history
                or attempt != history_count
            ):
                errors.append(
                    f"{label}: {target.identifier} no-progress REDIRECT attempt must equal its complete failed-Result history count"
                )
            progress = result.metadata.get("rework_progress_measure")
            if progress != rework_policy.get("no_progress_measure"):
                errors.append(
                    f"{label}: {target.identifier} no-progress REDIRECT must bind the frozen no_progress_measure"
                )
    if rework_policy is not None and decision == "REWORK":
        attempt = result.metadata.get("rework_attempt_number")
        if isinstance(attempt, bool) or not isinstance(attempt, int) or attempt < 1:
            errors.append(
                f"{label}: {target.identifier} REWORK must record a positive rework_attempt_number"
            )
        progress = result.metadata.get("rework_progress_measure")
        if (
            not isinstance(progress, str)
            or is_pending(progress)
            or has_unresolved_placeholder(progress)
        ):
            errors.append(
                f"{label}: {target.identifier} REWORK must record its measurable progress outcome"
            )
    if enforce_manifest_decision and manifest_slice.get("reflection_decision") != decision:
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
        historical_owned_case_ids = binding.get("historical_owned_case_ids")
        if isinstance(historical_owned_case_ids, list):
            owned_case_ids.update(str(item) for item in historical_owned_case_ids)
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
                                expected_evidence=expected_verification_case_evidence(
                                    result.identifier, evidence_case_id
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
                r"(?m)^[ ]{0,3}Decision:\s*(CONTINUE|ACCEPT|REWORK|REDIRECT|REJECT)\s*$",
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
            r"(?m)^[ ]{0,3}Decision:\s*(CONTINUE|ACCEPT|REWORK|REDIRECT|REJECT)\s*$",
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
            expected_evidence=expected_verification_case_evidence(
                result.identifier, case_id
            ),
        )
    )
    return errors


def validate_paused_rework_slice(
    target: Document,
    manifest_slice: dict[str, object],
    by_id: dict[str, Document],
    reflection_binding: dict[str, object] | None,
    verification: Document | None,
    label: str,
    *,
    assumption_expectations: dict[str, str] | None = None,
    assumption_catalog_digest: str | None = None,
    rework_policy: dict[str, object] | None = None,
) -> list[str]:
    """Validate a non-coding same-Slice REWORK state without rewriting history."""

    errors: list[str] = []
    iteration = str(target.metadata.get("iteration", ""))
    result_ref = manifest_slice.get("result")
    result = by_id.get(result_ref) if isinstance(result_ref, str) else None
    result_dependencies = (
        result.metadata.get("depends_on", [])
        if result is not None and isinstance(result.metadata.get("depends_on", []), list)
        else []
    )
    valid_result = not (
        result is None
        or result.metadata.get("kind") != "iteration-result"
        or str(result.metadata.get("iteration", "")) != iteration
        or result.metadata.get("status") != "failed-preserved"
        or result.metadata.get("authority") != "execution-evidence"
        or target.identifier not in result_dependencies
        or f"{iteration}-VERIFICATION" not in result_dependencies
    )
    if not valid_result:
        errors.append(
            f"{label}: paused {target.identifier} must preserve same-iteration failed execution evidence"
        )
    else:
        assert result is not None
        freeze_digest = manifest_slice.get("product_code_freeze_digest")
        if not isinstance(freeze_digest, str) or re.fullmatch(
            r"sha256:[0-9a-f]{64}", freeze_digest
        ) is None:
            errors.append(
                f"{label}: paused {target.identifier} must bind an exact product_code_freeze_digest"
            )
        elif result.metadata.get("product_code_freeze_digest") != freeze_digest:
            errors.append(
                f"{label}: paused {target.identifier} must preserve the failed Result product code freeze"
            )
        errors.extend(
            validate_slice_reflection_result(
                target,
                result,
                reflection_binding,
                manifest_slice,
                verification,
                label,
                blocked=True,
                assumption_expectations=assumption_expectations,
                assumption_catalog_digest=assumption_catalog_digest,
                rework_policy=None,
                enforce_manifest_decision=False,
            )
        )
        if (
            manifest_slice.get("historical_reflection_decision")
            != result.metadata.get("reflection_decision")
            or manifest_slice.get("historical_reflection_decision_ref")
            != result.metadata.get("reflection_decision_ref")
        ):
            errors.append(
                f"{label}: paused {target.identifier} must preserve the historical Result decision and receipt separately from REWORK"
            )

    if manifest_slice.get("reflection_decision") != "REWORK":
        errors.append(
            f"{label}: paused {target.identifier} reflection_decision must equal REWORK"
        )
    decision_ref = manifest_slice.get("reflection_decision_ref")
    if not isinstance(decision_ref, str) or re.fullmatch(
        r"codex-user-message:sha256:[0-9a-f]{64}", decision_ref
    ) is None:
        errors.append(
            f"{label}: paused {target.identifier} must bind an exact REWORK decision receipt"
        )

    errors.extend(
        validate_rework_result_history(target, manifest_slice, by_id, label)
    )
    rework_refs = manifest_slice.get("rework_result_refs")
    if not isinstance(rework_refs, list) or not rework_refs or rework_refs[-1] != result_ref:
        errors.append(
            f"{label}: paused {target.identifier} must retain its failed Result as the latest rework prerequisite"
        )
    attempt = manifest_slice.get("rework_attempt_number")
    progress = manifest_slice.get("rework_progress_measure")
    if isinstance(attempt, bool) or not isinstance(attempt, int) or attempt < 1:
        errors.append(
            f"{label}: paused {target.identifier} must record a positive rework_attempt_number"
        )
    if (
        not isinstance(progress, str)
        or is_pending(progress)
        or has_unresolved_placeholder(progress)
    ):
        errors.append(
            f"{label}: paused {target.identifier} must freeze a measurable rework progress measure"
        )
    if isinstance(rework_policy, dict):
        limit = rework_policy.get("no_progress_attempt_limit")
        if (
            isinstance(attempt, int)
            and not isinstance(attempt, bool)
            and isinstance(limit, int)
            and not isinstance(limit, bool)
            and attempt > limit
        ):
            errors.append(
                f"{label}: paused {target.identifier} rework attempt cannot exceed the frozen no-progress limit without a direction review"
            )

    project_decision_ref = manifest_slice.get("project_decision_ref")
    project_decision = (
        by_id.get(project_decision_ref)
        if isinstance(project_decision_ref, str)
        else None
    )
    project_dependencies = (
        project_decision.metadata.get("depends_on", [])
        if project_decision is not None
        and isinstance(project_decision.metadata.get("depends_on", []), list)
        else []
    )
    if (
        project_decision is None
        or project_decision.metadata.get("kind") != "project-decision"
        or str(project_decision.metadata.get("iteration", "")) != iteration
        or project_decision.metadata.get("status") not in {"accepted", "completed"}
        or project_decision.metadata.get("decision") != "REWORK"
        or project_decision.metadata.get("decision_ref") != decision_ref
        or project_decision.metadata.get("coding_input") not in {False, "false"}
        or result_ref not in project_dependencies
        or project_decision.metadata.get("decision_ref")
        == (result.metadata.get("reflection_decision_ref") if result is not None else None)
    ):
        errors.append(
            f"{label}: paused {target.identifier} must bind an accepted non-coding REWORK project decision that preserves its failed Result"
        )
    return errors


def validate_historical_rework_result_integrity(
    target: Document,
    result: Document,
    label: str,
    *,
    expected_product_freeze: object = None,
    expected_reflection_digest: object = None,
) -> list[str]:
    """Recompute the immutable digests for every failed attempt in a repair loop."""

    errors: list[str] = []
    product_freeze = result.metadata.get("product_code_freeze_digest")
    if not isinstance(product_freeze, str) or re.fullmatch(
        r"sha256:[0-9a-f]{64}", product_freeze
    ) is None:
        errors.append(
            f"{label}: historical {result.identifier} must bind an exact product_code_freeze_digest"
        )
    elif expected_product_freeze is not None and product_freeze != expected_product_freeze:
        errors.append(
            f"{label}: historical {result.identifier} product code freeze must match the frozen rework history"
        )

    report_digest = result.metadata.get("reflection_report_digest")
    valid_report_digest = isinstance(report_digest, str) and re.fullmatch(
        r"sha256:[0-9a-f]{64}", report_digest
    ) is not None
    if not valid_report_digest:
        errors.append(
            f"{label}: historical {result.identifier} must bind an exact reflection_report_digest"
        )
    elif (
        expected_reflection_digest is not None
        and report_digest != expected_reflection_digest
    ):
        errors.append(
            f"{label}: historical {result.identifier} reflection digest must match the frozen rework history"
        )

    heading_count = len(
        re.findall(
            r"(?m)^[ ]{0,3}##[ \t]+Architecture reflection and continuation decision[ \t]*#*[ \t]*$",
            result.body,
        )
    )
    section = markdown_section_body(
        result, "Architecture reflection and continuation decision"
    )
    if heading_count != 1 or not has_substantive_markdown_content(section):
        errors.append(
            f"{label}: historical {result.identifier} must retain one substantive reflection section"
        )
    elif valid_report_digest and report_digest != "sha256:" + hashlib.sha256(
        section.encode("utf-8")
    ).hexdigest():
        errors.append(
            f"{label}: historical {result.identifier} reflection_report_digest must bind the exact reflection section"
        )

    decision = result.metadata.get("reflection_decision")
    if decision not in {"REWORK", "REDIRECT", "REJECT"}:
        errors.append(
            f"{label}: historical {result.identifier} must retain its failed reflection decision"
        )
    decision_ref = result.metadata.get("reflection_decision_ref")
    if not isinstance(decision_ref, str) or re.fullmatch(
        r"codex-user-message:sha256:[0-9a-f]{64}", decision_ref
    ) is None:
        errors.append(
            f"{label}: historical {result.identifier} must retain an exact reflection decision receipt"
        )
    return errors


def validate_rework_result_history(
    target: Document,
    manifest_slice: dict[str, object],
    by_id: dict[str, Document],
    label: str,
) -> list[str]:
    """Preserve prior failed attempts when the same Slice is reauthorized."""

    refs = manifest_slice.get("rework_result_refs")
    history_required = any(
        field in manifest_slice
        for field in (
            "project_decision_ref",
            "rework_attempt_number",
            "rework_prerequisite_result",
        )
    )
    if refs is None:
        return (
            [
                f"{label}: development.slices.{target.identifier}.rework_result_refs is required for same-Slice reauthorization"
            ]
            if history_required
            else []
        )
    if not isinstance(refs, list):
        return [
            f"{label}: development.slices.{target.identifier}.rework_result_refs must be a sequence"
        ]
    normalized = [str(item) for item in refs]
    errors: list[str] = []
    if len(normalized) != len(set(normalized)):
        errors.append(
            f"{label}: development.slices.{target.identifier}.rework_result_refs must be unique"
        )
    attempt = manifest_slice.get("rework_attempt_number")
    if (
        isinstance(attempt, bool)
        or not isinstance(attempt, int)
        or attempt != len(normalized)
    ):
        errors.append(
            f"{label}: development.slices.{target.identifier}.rework_attempt_number must equal the complete failed-Result history count"
        )

    history_freezes = manifest_slice.get("rework_history_freezes")
    if len(normalized) > 1 and (
        not isinstance(history_freezes, dict)
        or set(history_freezes) != set(normalized)
    ):
        errors.append(
            f"{label}: multi-attempt {target.identifier} must freeze every Result product and reflection digest"
        )
        history_freezes = None

    iteration = str(target.metadata.get("iteration", ""))
    for reference in normalized:
        result = by_id.get(reference)
        dependencies = (
            result.metadata.get("depends_on", [])
            if result is not None
            and isinstance(result.metadata.get("depends_on", []), list)
            else []
        )
        if (
            result is None
            or result.metadata.get("kind") != "iteration-result"
            or result.metadata.get("status") != "failed-preserved"
            or str(result.metadata.get("iteration", "")) != iteration
            or target.identifier not in dependencies
            or f"{iteration}-VERIFICATION" not in dependencies
        ):
            errors.append(
                f"{label}: rework_result_refs item must preserve a failed attempt for the same Slice: {reference}"
            )
            continue
        freeze_entry = (
            history_freezes.get(reference)
            if isinstance(history_freezes, dict)
            else None
        )
        if len(normalized) > 1 and not isinstance(freeze_entry, dict):
            errors.append(
                f"{label}: multi-attempt {target.identifier} is missing frozen digests for {reference}"
            )
            freeze_entry = {}
        errors.extend(
            validate_historical_rework_result_integrity(
                target,
                result,
                label,
                expected_product_freeze=(
                    freeze_entry.get("product_code_freeze_digest")
                    if isinstance(freeze_entry, dict)
                    else None
                ),
                expected_reflection_digest=(
                    freeze_entry.get("reflection_report_digest")
                    if isinstance(freeze_entry, dict)
                    else None
                ),
            )
        )
    expected_prerequisite = normalized[-1] if normalized else "none"
    if manifest_slice.get("rework_prerequisite_result") != expected_prerequisite:
        errors.append(
            f"{label}: development.slices.{target.identifier}.rework_prerequisite_result must equal {expected_prerequisite}"
        )
    return errors


def validate_rework_authorization_receipt(
    target: Document,
    manifest_slice: dict[str, object],
    by_id: dict[str, Document],
    label: str,
) -> list[str]:
    """Require a new authorization after both the failed attempt and REWORK decision."""

    rework_refs = manifest_slice.get("rework_result_refs")
    if not isinstance(rework_refs, list) or not rework_refs:
        return []
    errors: list[str] = []
    forbidden_receipts: set[str] = set()
    iteration = str(target.metadata.get("iteration", ""))
    readiness = by_id.get(f"{iteration}-READINESS")
    initial_authorization = (
        readiness.metadata.get("product_goal_alignment_review_ref")
        if readiness is not None
        else None
    )
    if isinstance(initial_authorization, str):
        forbidden_receipts.add(initial_authorization)
    project_decision_ref = manifest_slice.get("project_decision_ref")
    project_decision = (
        by_id.get(project_decision_ref)
        if isinstance(project_decision_ref, str)
        else None
    )
    if project_decision is not None and isinstance(
        project_decision.metadata.get("decision_ref"), str
    ):
        forbidden_receipts.add(str(project_decision.metadata["decision_ref"]))
    for rework_ref in rework_refs:
        prior_result = by_id.get(str(rework_ref))
        if prior_result is not None and isinstance(
            prior_result.metadata.get("reflection_decision_ref"), str
        ):
            forbidden_receipts.add(
                str(prior_result.metadata["reflection_decision_ref"])
            )
        if prior_result is not None and isinstance(
            prior_result.metadata.get("slice_authorization_ref"), str
        ):
            forbidden_receipts.add(str(prior_result.metadata["slice_authorization_ref"]))

    prior_authorizations = manifest_slice.get("prior_authorization_refs")
    if (
        not isinstance(prior_authorizations, list)
        or len(prior_authorizations) != len(rework_refs)
        or len(prior_authorizations) != len(set(map(str, prior_authorizations)))
        or any(
            not isinstance(reference, str)
            or re.fullmatch(r"codex-user-message:sha256:[0-9a-f]{64}", reference)
            is None
            for reference in prior_authorizations
        )
    ):
        errors.append(
            f"{label}: reauthorized {target.identifier} must freeze one unique prior authorization receipt per failed Result"
        )
        prior_authorizations = []
    if (
        isinstance(initial_authorization, str)
        and prior_authorizations
        and prior_authorizations[0] != initial_authorization
    ):
        errors.append(
            f"{label}: reauthorized {target.identifier} must preserve its initial Readiness authorization as the first prior receipt"
        )
    for index, rework_ref in enumerate(rework_refs[1:], start=1):
        prior_result = by_id.get(str(rework_ref))
        expected_authorization = (
            prior_authorizations[index]
            if index < len(prior_authorizations)
            else None
        )
        if (
            prior_result is None
            or prior_result.metadata.get("slice_authorization_ref")
            != expected_authorization
        ):
            errors.append(
                f"{label}: reauthorized {target.identifier} must bind every later failed Result to its frozen prior authorization receipt"
            )

    authorization_ref = manifest_slice.get("authorization_ref")
    if not isinstance(authorization_ref, str) or re.fullmatch(
        r"codex-user-message:sha256:[0-9a-f]{64}", authorization_ref
    ) is None:
        errors.append(
            f"{label}: reauthorized {target.identifier} must bind an exact new user authorization receipt"
        )
    elif authorization_ref in forbidden_receipts or authorization_ref in set(
        map(str, prior_authorizations)
    ):
        errors.append(
            f"{label}: reauthorized {target.identifier} must use a new user authorization receipt after the failed Result and REWORK decision"
        )
    return errors


def rework_project_decision_refs_for_slice(
    target: Document, by_id: dict[str, Document]
) -> set[str]:
    """Return accepted REWORK decisions whose preserved Result belongs to this Slice."""

    iteration = str(target.metadata.get("iteration", ""))
    references: set[str] = set()
    for document in by_id.values():
        if (
            document.metadata.get("kind") != "project-decision"
            or str(document.metadata.get("iteration", "")) != iteration
            or document.metadata.get("decision") != "REWORK"
            or document.metadata.get("status") not in {"accepted", "completed"}
        ):
            continue
        dependencies = document.metadata.get("depends_on", [])
        if not isinstance(dependencies, list):
            continue
        for dependency in dependencies:
            result = by_id.get(str(dependency))
            result_dependencies = (
                result.metadata.get("depends_on", [])
                if result is not None
                and isinstance(result.metadata.get("depends_on", []), list)
                else []
            )
            if (
                result is not None
                and result.metadata.get("kind") == "iteration-result"
                and target.identifier in result_dependencies
            ):
                references.add(document.identifier)
                break
    return references


def validate_superseded_iteration_plan(
    new_refs: list[str],
    by_id: dict[str, Document],
    manifest: dict[str, object],
    label: str,
) -> list[str]:
    """Ensure a pre-execution replacement cannot hide authorized or completed work."""

    errors: list[str] = []
    iteration_data = manifest.get("iteration")
    iteration = (
        str(iteration_data.get("id")) if isinstance(iteration_data, dict) else ""
    )
    development = manifest.get("development")
    raw_slices = development.get("slices") if isinstance(development, dict) else None
    if not isinstance(raw_slices, dict):
        return [f"{label}: superseded iteration must preserve its planned Slice mapping"]
    if set(raw_slices) != set(new_refs):
        errors.append(
            f"{label}: superseded iteration Slice mapping must exactly match new_capability_slice_refs"
        )
    for reference in new_refs:
        target = by_id.get(reference)
        state = raw_slices.get(reference)
        if (
            target is None
            or target.metadata.get("kind") != "development-slice"
            or str(target.metadata.get("iteration", "")) != iteration
            or target.metadata.get("status") != "proposed"
            or target.metadata.get("authority") != "proposed-development"
            or is_true(target.metadata.get("coding_input", ""))
        ):
            errors.append(
                f"{label}: superseded pre-execution Slice must remain proposed and non-coding: {reference}"
            )
        if not isinstance(state, dict):
            errors.append(
                f"{label}: superseded iteration is missing planned Slice state: {reference}"
            )
            continue
        expected = {
            "status": "proposed",
            "coding_input": False,
            "result": "not-executed",
            "product_code_freeze_digest": "not-executed",
            "authorized_by": "not-authorized",
            "authorized_at": "not-authorized",
            "authorization_ref": "not-authorized",
        }
        for field, value in expected.items():
            if state.get(field) != value:
                errors.append(
                    f"{label}: superseded {reference} {field} must equal {value}"
                )
    authorization = manifest.get("authorization")
    if not isinstance(authorization, dict) or authorization.get("active_slice") != "none":
        errors.append(
            f"{label}: superseded iteration must have authorization.active_slice none"
        )
    if not isinstance(authorization, dict) or (
        authorization.get("authorized_by"),
        authorization.get("authorized_at"),
        authorization.get("authorization_ref"),
    ) not in {
        ("pending", "pending", "pending"),
        ("not-authorized", "not-authorized", "not-authorized"),
    }:
        errors.append(
            f"{label}: superseded pre-execution iteration must retain an unresolved top-level authorization"
        )
    if not isinstance(iteration_data, dict) or is_true(
        iteration_data.get("coding_input", "")
    ):
        errors.append(
            f"{label}: superseded pre-execution iteration must remain non-coding"
        )
    for document in by_id.values():
        if str(document.metadata.get("iteration", "")) != iteration:
            continue
        kind = document.metadata.get("kind")
        if kind not in {"iteration-result", "iteration-acceptance"}:
            continue
        if (
            document.metadata.get("authority") == "execution-evidence"
            or document.metadata.get("status")
            in {"accepted", "completed", "failed-preserved"}
            or kind == "iteration-acceptance"
        ):
            errors.append(
                f"{label}: superseded pre-execution iteration must not contain execution or accepted Result evidence: {document.identifier}"
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
    require_paused: bool = False,
) -> list[str]:
    """Require an active, paused, or terminal sequential-development state."""

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
    raw_rework_policy = manifest.get("rework_policy") if manifest is not None else None
    rework_policy = raw_rework_policy if isinstance(raw_rework_policy, dict) else None
    raw_experience_policy = (
        manifest.get("experience_delivery_policy") if manifest is not None else None
    )
    experience_policy = (
        raw_experience_policy if isinstance(raw_experience_policy, dict) else None
    )
    raw_provider_policy = (
        manifest.get("provider_route_policy") if manifest is not None else None
    )
    provider_policy = (
        raw_provider_policy if isinstance(raw_provider_policy, dict) else None
    )
    historical_pre_policy_result_refs: set[str] = set()
    if experience_policy is not None:
        raw_historical_refs = experience_policy.get(
            "historical_pre_policy_result_refs"
        )
        if isinstance(raw_historical_refs, list):
            historical_pre_policy_result_refs = {
                str(reference) for reference in raw_historical_refs
            }
            owner_slice_ref = experience_policy.get("owner_slice_ref")
            for reference in historical_pre_policy_result_refs:
                historical_result = by_id.get(reference)
                historical_dependencies = (
                    historical_result.metadata.get("depends_on", [])
                    if historical_result is not None
                    and isinstance(
                        historical_result.metadata.get("depends_on", []), list
                    )
                    else []
                )
                if (
                    historical_result is None
                    or historical_result.metadata.get("kind") != "iteration-result"
                    or historical_result.metadata.get("status") != "failed-preserved"
                    or owner_slice_ref not in historical_dependencies
                    or "experience_delivery_policy_schema"
                    in historical_result.metadata
                ):
                    errors.append(
                        f"{label}: historical pre-policy experience Result "
                        f"{reference} must be a failed-preserved Result for the owner "
                        "Slice without successor-policy audit fields"
                    )
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
        alpha_comparison_binding = alignment.get("alpha_agent_comparison_binding")
        if isinstance(alpha_comparison_binding, dict):
            new_slice_ref = alpha_comparison_binding.get("new_slice_ref")
            if isinstance(new_slice_ref, str):
                if new_slice_ref in early_comparison_by_slice:
                    errors.append(
                        f"{label}: a Slice cannot own both Alpha and hidden Agent comparison bindings"
                    )
                else:
                    early_comparison_by_slice[new_slice_ref] = alpha_comparison_binding
    assumption_catalog_digest: str | None = None
    assumption_expectations: dict[str, str] | None = None
    historical_assumption_catalog_digest: str | None = None
    historical_assumption_expectations: dict[str, str] | None = None
    historical_result_ref: str | None = None
    if slices and requires_reflection_gate(
        str(slices[0].metadata.get("iteration", ""))
    ):
        proposal_id = f"{slices[0].metadata.get('iteration')}-PROPOSAL"
        if manifest is not None:
            (
                assumption_catalog_digest,
                parsed_assumption_expectations,
                historical_assumption_catalog_digest,
                parsed_historical_expectations,
                catalog_errors,
            ) = critical_assumption_catalogs(
                by_id.get(proposal_id), manifest, label
            )
            cutover = manifest.get("critical_assumption_catalog_cutover")
            if isinstance(cutover, dict) and isinstance(
                cutover.get("historical_result_ref"), str
            ):
                historical_result_ref = str(cutover["historical_result_ref"])
        else:
            (
                assumption_catalog_digest,
                parsed_assumption_expectations,
                catalog_errors,
            ) = critical_assumption_catalog(by_id.get(proposal_id))
            historical_assumption_catalog_digest = assumption_catalog_digest
            parsed_historical_expectations = parsed_assumption_expectations
        errors.extend(catalog_errors)
        assumption_expectations = parsed_assumption_expectations
        historical_assumption_expectations = parsed_historical_expectations
        if not isinstance(alignment, dict) or alignment.get(
            "critical_assumption_catalog_digest"
        ) != assumption_catalog_digest:
            errors.append(
                f"{label}: critical_assumption_catalog_digest must match the exact current assumption catalog"
            )
        critical_assumption_ids = (
            resolved_assumption_ids(alignment.get("critical_assumption_ids"))
            if isinstance(alignment, dict)
            else []
        )
        if critical_assumption_ids != list(parsed_assumption_expectations):
            errors.append(
                f"{label}: critical_assumption_ids must exactly match the current assumption catalog order"
            )

    def reflection_inputs_for_result(
        slice_ref: str, result_ref: object
    ) -> tuple[dict[str, object] | None, dict[str, str] | None, str | None]:
        binding = reflection_by_slice.get(slice_ref)
        if result_ref != historical_result_ref:
            return binding, assumption_expectations, assumption_catalog_digest
        historical_binding = dict(binding) if isinstance(binding, dict) else None
        if historical_binding is not None and historical_assumption_expectations:
            historical_result = (
                by_id.get(historical_result_ref)
                if isinstance(historical_result_ref, str)
                else None
            )
            historical_case_id = (
                historical_result.metadata.get("reflection_gate_case_id")
                if historical_result is not None
                else None
            )
            if isinstance(historical_case_id, str):
                historical_binding["case_id"] = historical_case_id
            historical_binding["historical_owned_case_ids"] = list(
                ITER010_HISTORICAL_GATE_CASES
            )
            current_ids = resolved_assumption_ids(
                historical_binding.get("assumption_ids")
            )
            historical_binding["assumption_ids"] = ",".join(
                assumption_id
                for assumption_id in current_ids
                if assumption_id in historical_assumption_expectations
            )
            conditional = historical_binding.get("conditional_falsifier_bindings")
            if isinstance(conditional, dict):
                historical_binding["conditional_falsifier_bindings"] = {
                    "cross_project_generalization": {
                        "assumption_id": "A4",
                        "case_id": "V-XD-001",
                    },
                    "final_quality_and_value": {
                        "assumption_id": "A5",
                        "case_id": "V-ANSWER-001",
                    },
                }
        return (
            historical_binding,
            historical_assumption_expectations,
            historical_assumption_catalog_digest,
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
    paused_indexes = [
        index for index, status in enumerate(statuses) if status == "paused"
    ]
    terminal_mode_count = sum(
        bool(item) for item in (require_completed, require_rejected, require_paused)
    )
    if terminal_mode_count > 1:
        errors.append(
            f"{label}: iteration cannot be completed, rejected and paused at the same time"
        )
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
    elif require_paused:
        if len(paused_indexes) != 1:
            errors.append(
                f"{label}: paused iteration requires exactly one paused new capability slice"
            )
        else:
            paused_index = paused_indexes[0]
            if any(status != "completed" for status in statuses[:paused_index]):
                errors.append(
                    f"{label}: slices before the paused slice must be completed in Manifest order"
                )
            if any(status != "proposed" for status in statuses[paused_index + 1 :]):
                errors.append(
                    f"{label}: slices after the paused slice must remain proposed"
                )
        if active_indexes or blocked_indexes:
            errors.append(
                f"{label}: paused iteration must not have an active or rejected slice"
            )
    elif paused_indexes:
        errors.append(
            f"{label}: a paused Slice requires the iteration index and Manifest to be paused"
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
                if require_completed
                or require_rejected
                or require_paused
                or len(active_indexes) != 1
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
        elif status == "paused" and (
            authority not in {"development-evidence", "project-decision"}
            or coding_input
        ):
            errors.append(
                f"{target.relative_path}: paused slice must use non-coding evidence or project-decision authority"
            )
        elif status not in {
            "proposed",
            "authorized",
            "in-progress",
            "completed",
            "blocked",
            "paused",
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
            "paused",
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
            slice_rework_decisions = rework_project_decision_refs_for_slice(
                target, by_id
            )
            if slice_rework_decisions:
                if manifest_slice.get("project_decision_ref") not in slice_rework_decisions:
                    errors.append(
                        f"{label}: {target.identifier} must retain its irreversible REWORK project decision"
                    )
                if not isinstance(
                    manifest_slice.get("rework_result_refs"), list
                ) or not manifest_slice.get("rework_result_refs"):
                    errors.append(
                        f"{label}: {target.identifier} must retain all failed rework Results"
                    )
                elif status in {"blocked", "completed"}:
                    errors.extend(
                        validate_rework_result_history(
                            target,
                            manifest_slice,
                            by_id,
                            label,
                        )
                    )
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
                iteration_state = manifest.get("iteration") if manifest is not None else None
                manifest_rework_required = (
                    isinstance(iteration_state, dict)
                    and iteration_state.get("current_decision") == "REWORK"
                ) or bool(slice_rework_decisions)
                if manifest_rework_required:
                    project_decision_ref = manifest_slice.get("project_decision_ref")
                    project_decision = (
                        by_id.get(project_decision_ref)
                        if isinstance(project_decision_ref, str)
                        else None
                    )
                    if (
                        project_decision is None
                        or project_decision.metadata.get("kind") != "project-decision"
                        or project_decision.metadata.get("decision") != "REWORK"
                        or project_decision_ref not in slice_rework_decisions
                    ):
                        errors.append(
                            f"{label}: reauthorized {target.identifier} must retain its REWORK project decision"
                        )
                    if not isinstance(manifest_slice.get("rework_result_refs"), list) or not manifest_slice.get("rework_result_refs"):
                        errors.append(
                            f"{label}: reauthorized {target.identifier} must retain all failed rework Results"
                        )
                errors.extend(
                    validate_rework_result_history(
                        target,
                        manifest_slice,
                        by_id,
                        label,
                    )
                )
                errors.extend(
                    validate_rework_authorization_receipt(
                        target,
                        manifest_slice,
                        by_id,
                        label,
                    )
                )
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
                        (
                            result_binding,
                            result_assumptions,
                            result_catalog_digest,
                        ) = reflection_inputs_for_result(
                            target.identifier,
                            manifest_slice.get("result"),
                        )
                        errors.extend(
                            validate_slice_reflection_result(
                                target,
                                result,
                                result_binding,
                                manifest_slice,
                                verification,
                                label,
                                blocked=True,
                                assumption_expectations=result_assumptions,
                                assumption_catalog_digest=result_catalog_digest,
                                rework_policy=rework_policy,
                            )
                        )
            elif status == "paused":
                (
                    paused_binding,
                    paused_assumptions,
                    paused_catalog_digest,
                ) = reflection_inputs_for_result(
                    target.identifier,
                    manifest_slice.get("result"),
                )
                errors.extend(
                    validate_paused_rework_slice(
                        target,
                        manifest_slice,
                        by_id,
                        paused_binding,
                        verification,
                        label,
                        assumption_expectations=paused_assumptions,
                        assumption_catalog_digest=paused_catalog_digest,
                        rework_policy=rework_policy,
                    )
                )
                comparison_binding = early_comparison_by_slice.get(
                    target.identifier
                )
                comparison_case = (
                    comparison_binding.get("case_id")
                    if isinstance(comparison_binding, dict)
                    else None
                )
                result_ref = manifest_slice.get("result")
                result = by_id.get(result_ref) if isinstance(result_ref, str) else None
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
                    result is not None
                    and isinstance(alignment, dict)
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
                        (
                            result_binding,
                            result_assumptions,
                            result_catalog_digest,
                        ) = reflection_inputs_for_result(
                            target.identifier,
                            manifest_slice.get("result"),
                        )
                        errors.extend(
                            validate_slice_reflection_result(
                                target,
                                result,
                                result_binding,
                                manifest_slice,
                                verification,
                                label,
                                blocked=False,
                                assumption_expectations=result_assumptions,
                                assumption_catalog_digest=result_catalog_digest,
                                rework_policy=rework_policy,
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
                                expected_evidence=expected_verification_case_evidence(
                                    result.identifier, str(case_id)
                                ),
                            )
                        )

            if (
                status in {"blocked", "paused", "completed"}
                and experience_policy is not None
                and provider_policy is not None
                and target.identifier == experience_policy.get("owner_slice_ref")
                and isinstance(manifest_slice, dict)
            ):
                delivery_result_ref = manifest_slice.get("result")
                delivery_result = (
                    by_id.get(delivery_result_ref)
                    if isinstance(delivery_result_ref, str)
                    else None
                )
                if delivery_result is None:
                    errors.append(
                        f"{label}: {target.identifier} must bind an experience-first delivery Result"
                    )
                elif not (
                    status == "paused"
                    and delivery_result_ref in historical_pre_policy_result_refs
                    and experience_policy.get(
                        "historical_results_do_not_satisfy_experience_gate"
                    )
                    is True
                ):
                    errors.extend(
                        validate_experience_delivery_result(
                            delivery_result,
                            experience_policy,
                            provider_policy,
                            require_success=status == "completed",
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
                    r"(?:codex-user-message|independent-evaluator-result):sha256:[0-9a-f]{64}",
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
        iteration_paused = (
            index is not None
            and str(index.metadata.get("status", "")) == "paused"
        )
        iteration_superseded = (
            index is not None
            and str(index.metadata.get("status", "")) == "superseded"
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
        if iteration_paused:
            if str(index.metadata.get("coding_input", "")).strip().lower() != "false":
                errors.append(
                    f"{index.relative_path}: paused iteration must use coding_input false"
                )
            if acceptances:
                errors.append(
                    f"{index.relative_path}: paused iteration must not have an accepted/completed Acceptance"
                )
        if iteration_superseded:
            if str(index.metadata.get("coding_input", "")).strip().lower() != "false":
                errors.append(
                    f"{index.relative_path}: superseded iteration must use coding_input false"
                )
            if acceptances:
                errors.append(
                    f"{index.relative_path}: superseded iteration must not have an accepted/completed Acceptance"
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
            if not proposal_selected and not (
                iteration_superseded
                and str(proposal.metadata.get("status", ""))
                in {"proposed", "superseded"}
            ):
                errors.append(
                    f"{proposal.relative_path}: selected iteration proposal must be accepted/authorized/completed"
                )
            errors.extend(validate_goal_aligned_required_document(proposal))

        requires_readiness = bool(
            readiness_selected or iteration_selected or selected_slices or acceptances
        ) and not iteration_superseded
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
                    expected_status=(
                        "rejected"
                        if iteration_rejected
                        else "paused"
                        if iteration_paused
                        else "superseded"
                        if iteration_superseded
                        else None
                    ),
                    allow_unresolved_planning=iteration_superseded,
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
                    require_paused_slice_sequence=iteration_paused,
                    require_superseded_slice_sequence=iteration_superseded,
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
