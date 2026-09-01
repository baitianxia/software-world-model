#!/usr/bin/env python3
"""Lightweight independent supervision for the active development lane.

The supervisor binds one development branch, one supervision branch, one
product baseline, one plan commit and one exact source revision.  It observes
both commits and uncommitted work.  A developer-authored phase label is never
used.  Only a fresh independent assessment of a clean candidate can advance a
phase; every other outcome keeps development active.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence

from validation.iteration_010_mvp import direction_check


CONTROL_SCHEMA = "SWM_INDEPENDENT_SUPERVISION_CONTROL@3"
ASSESSMENT_SCHEMA = "SWM_INDEPENDENT_ASSESSMENT@2"
REPORT_SCHEMA = "SWM_INDEPENDENT_SUPERVISION_REPORT@3"
HEARTBEAT_SCHEMA = "SWM_SUPERVISION_HEARTBEAT@2"
DIRECTIVE_SCHEMA = "SWM_SUPERVISION_DIRECTIVE@1"
VERDICTS = {"PASS", "REWORK", "NOT_RUN"}
SHA1_LENGTH = 40

HARD_DIRECTION_VIOLATION_CODES = frozenset(
    {
        "LEGACY_PROTOCOL_NET_GROWTH",
        "NEW_LEGACY_PROTOCOL_VERSION",
        "ANSWER_TEXT_SEMANTIC_RULE",
        "EVALUATION_SPECIFIC_PRODUCT_LITERAL",
    }
)
SEMANTIC_SUPERVISION_FOCUS = (
    "目标一致：当前改动直接推进 active phase 的唯一产品目标，未改写目标。",
    "实现方式：能力增长发生在世界模型认知、同一主 Agent 的观察重规划或完整浏览器纵切，而非提示词、协议、题面规则或测试计数。",
    "体验进展：当前改动缩短到首个可操作 cognition→Source Gap→Answer/Citation→fresh review→Web 链的距离。",
    "根因与通用性：失败定位到最早责任层，修复不针对单题且至少能解释两个异质邻近任务。",
)
_DIRECTION_ACTIONS = {
    "LEGACY_PROTOCOL_NET_GROWTH": (
        "撤销旧回答协议表面的净增长，只保留删除、简化或薄适配。"
    ),
    "NEW_LEGACY_PROTOCOL_VERSION": (
        "移除新增版本化回答/Agent 协议；把本阶段能力实现为现有同一 Agent 的内部状态和工具循环。"
    ),
    "ANSWER_TEXT_SEMANTIC_RULE": (
        "移除针对答案正文形式或词法的判定规则，回到可观察的 Agent 能力和证据链实现。"
    ),
    "EVALUATION_SPECIFIC_PRODUCT_LITERAL": (
        "移除工程、题面或已知样例专用分支，以通用能力实现当前阶段目标。"
    ),
}
_SUPERVISION_MODULE_PATHS = {
    "independent_supervision": (
        "validation/iteration_010_mvp/independent_supervision.py",
        Path(__file__).read_bytes(),
    ),
    "direction_check": (
        "validation/iteration_010_mvp/direction_check.py",
        Path(direction_check.__file__).read_bytes(),
    ),
}
_MONITOR_STARTED_AT = datetime.now(timezone.utc).astimezone().isoformat(
    timespec="seconds"
)

CONTROL_KEYS = {
    "schema",
    "iteration",
    "candidate_branch",
    "candidate_repository",
    "supervision_branch",
    "supervision_repository",
    "source_repository",
    "trusted_product_baseline_commit",
    "trusted_plan_commit",
    "source_commit",
    "active_phase",
    "next_phase",
    "phase_exit_case_id",
    "phase_exit_requirements",
    "objective",
    "check_interval_minutes",
}
ASSESSMENT_KEYS = {
    "schema",
    "iteration",
    "candidate_branch",
    "candidate_commit",
    "candidate_tree",
    "candidate_worktree_digest",
    "source_commit",
    "phase",
    "verdict",
    "assessor",
    "assessed_at",
    "evidence",
    "completed_requirements",
    "unresolved_requirements",
    "defects",
    "earliest_divergence",
    "next_action",
}
EVIDENCE_KEYS = {"id", "scope", "path", "sha256"}
DEFECT_KEYS = {"severity", "owner_layer", "summary", "evidence_ids"}


class SupervisionInputError(ValueError):
    """Raised when an exact supervision input cannot be trusted."""


@dataclass(frozen=True)
class CandidateState:
    branch: str | None
    head: str
    tree: str
    clean: bool
    worktree_digest: str
    changed_paths: tuple[str, ...]


@dataclass(frozen=True)
class EvidenceState:
    valid: bool
    missing: tuple[str, ...]
    mismatched: tuple[str, ...]


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _git(repository: Path, *arguments: str) -> bytes:
    completed = subprocess.run(
        ["git", "-C", str(repository), *arguments],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        raise SupervisionInputError(detail or "git command failed")
    return completed.stdout


def _git_result(repository: Path, *arguments: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", "-C", str(repository), *arguments],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _sha256_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _canonical_digest(value: object) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return _sha256_bytes(encoded)


def capture_monitor_identity(repository: Path) -> dict[str, Any]:
    """Bind the running Python code, not merely the repository's current HEAD."""

    loaded: dict[str, str] = {}
    committed: dict[str, str] = {}
    matches = True
    for name, (relative, loaded_bytes) in _SUPERVISION_MODULE_PATHS.items():
        committed_bytes = _git(repository, "show", f"HEAD:{relative}")
        loaded[name] = _sha256_bytes(loaded_bytes)
        committed[name] = _sha256_bytes(committed_bytes)
        if loaded_bytes != committed_bytes:
            matches = False
    return {
        "monitor_started_at": _MONITOR_STARTED_AT,
        "monitor_loaded_code_digests": loaded,
        "monitor_head_code_digests": committed,
        "monitor_code_matches_head": matches,
    }


def _direction_findings(
    report: Mapping[str, Any] | None,
) -> tuple[tuple[dict[str, str], ...], tuple[str, ...], str | None]:
    if report is None:
        return (), (), None
    if report.get("schema") != direction_check.REPORT_SCHEMA:
        raise SupervisionInputError("direction report schema is invalid")
    violations = report.get("violations")
    if type(violations) is not list:
        raise SupervisionInputError("direction report violations must be an array")
    hard: list[dict[str, str]] = []
    advisories: list[str] = []
    for index, item in enumerate(violations):
        if type(item) is not dict:
            raise SupervisionInputError(
                f"direction report violations[{index}] must be an object"
            )
        code = _string(item.get("code"), f"direction violation[{index}].code")
        path = _string(item.get("path"), f"direction violation[{index}].path")
        detail = _string(item.get("detail"), f"direction violation[{index}].detail")
        if code in HARD_DIRECTION_VIOLATION_CODES:
            hard.append({"code": code, "path": path, "detail": detail})
        else:
            advisories.append(code)
    return tuple(hard), tuple(sorted(set(advisories))), _canonical_digest(report)


def _build_correction(
    control: Mapping[str, Any],
    candidate: CandidateState,
    violations: Sequence[Mapping[str, str]],
) -> dict[str, Any]:
    actions = tuple(
        dict.fromkeys(_DIRECTION_ACTIONS[item["code"]] for item in violations)
    )
    identity = {
        "iteration": control["iteration"],
        "phase": control["active_phase"],
        "candidate_commit": candidate.head,
        "candidate_worktree_digest": candidate.worktree_digest,
        "violations": list(violations),
    }
    return {
        "correction_id": _canonical_digest(identity),
        "earliest_divergence": "plan-direction",
        "required_actions": list(actions),
        "violation_codes": sorted({item["code"] for item in violations}),
        "evidence": list(violations),
        "continue_objective": control["objective"],
        "task_should_stop": False,
        "authorization_required": False,
    }


def _file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return "sha256:" + digest.hexdigest()


def _exact_keys(value: Mapping[str, Any], expected: set[str], label: str) -> None:
    missing = sorted(expected.difference(value))
    unexpected = sorted(set(value).difference(expected))
    if missing or unexpected:
        parts: list[str] = []
        if missing:
            parts.append("missing " + ", ".join(missing))
        if unexpected:
            parts.append("unexpected " + ", ".join(unexpected))
        raise SupervisionInputError(f"{label} has " + "; ".join(parts))


def _string(value: Any, label: str) -> str:
    if type(value) is not str or not value.strip():
        raise SupervisionInputError(f"{label} must be a non-empty string")
    return value.strip()


def _string_list(value: Any, label: str) -> tuple[str, ...]:
    if type(value) is not list or any(type(item) is not str for item in value):
        raise SupervisionInputError(f"{label} must be a JSON string array")
    normalized = tuple(item.strip() for item in value)
    if any(not item for item in normalized) or len(set(normalized)) != len(normalized):
        raise SupervisionInputError(f"{label} must contain unique non-empty strings")
    return normalized


def _git_id(value: Any, label: str) -> str:
    text = _string(value, label)
    if len(text) != SHA1_LENGTH or any(character not in "0123456789abcdef" for character in text):
        raise SupervisionInputError(f"{label} must be an exact SHA-1 Git ID")
    return text


def _safe_relative_path(value: Any, label: str) -> str:
    text = _string(value, label)
    path = PurePosixPath(text)
    if path.is_absolute() or "." in path.parts or ".." in path.parts:
        raise SupervisionInputError(f"{label} must be a safe relative path")
    return path.as_posix()


def _canonical_absolute_path(value: Any, label: str) -> Path:
    text = _string(value, label)
    path = Path(text)
    if not path.is_absolute():
        raise SupervisionInputError(f"{label} must be an absolute path")
    resolved = path.resolve()
    if str(resolved) != text:
        raise SupervisionInputError(f"{label} must be a canonical absolute path")
    return resolved


def _branch(repository: Path) -> str | None:
    completed = _git_result(repository, "symbolic-ref", "--quiet", "--short", "HEAD")
    if completed.returncode == 1:
        return None
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        raise SupervisionInputError(detail or "cannot determine Git branch")
    return completed.stdout.decode("utf-8", errors="strict").strip()


def _decode_paths(raw: bytes) -> tuple[str, ...]:
    return tuple(
        item.decode("utf-8", errors="strict") for item in raw.split(b"\0") if item
    )


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SupervisionInputError(f"cannot read strict JSON from {path}") from exc
    if type(value) is not dict:
        raise SupervisionInputError(f"{path} must contain one JSON object")
    return value


def validate_control(value: Mapping[str, Any]) -> dict[str, Any]:
    _exact_keys(value, CONTROL_KEYS, "supervision control")
    if value.get("schema") != CONTROL_SCHEMA:
        raise SupervisionInputError("unsupported supervision control schema")
    _string(value.get("iteration"), "control iteration")
    for field in (
        "candidate_branch",
        "supervision_branch",
        "active_phase",
        "next_phase",
        "phase_exit_case_id",
        "objective",
    ):
        _string(value.get(field), f"control {field}")
    for field in (
        "candidate_repository",
        "supervision_repository",
        "source_repository",
    ):
        _canonical_absolute_path(value.get(field), f"control {field}")
    for field in (
        "trusted_product_baseline_commit",
        "trusted_plan_commit",
        "source_commit",
    ):
        _git_id(value.get(field), f"control {field}")
    requirements = _string_list(
        value.get("phase_exit_requirements"), "control phase_exit_requirements"
    )
    if not requirements:
        raise SupervisionInputError("control phase_exit_requirements must not be empty")
    interval = value.get("check_interval_minutes")
    if type(interval) is not int or interval <= 0:
        raise SupervisionInputError("control check_interval_minutes must be positive")
    return dict(value)


def validate_assessment(
    value: Mapping[str, Any], control: Mapping[str, Any]
) -> dict[str, Any]:
    _exact_keys(value, ASSESSMENT_KEYS, "independent assessment")
    if value.get("schema") != ASSESSMENT_SCHEMA:
        raise SupervisionInputError("unsupported independent assessment schema")
    if value.get("iteration") != control.get("iteration"):
        raise SupervisionInputError("assessment iteration does not match control")
    if value.get("candidate_branch") != control.get("candidate_branch"):
        raise SupervisionInputError("assessment candidate branch does not match control")
    for field in ("candidate_commit", "candidate_tree", "source_commit"):
        _git_id(value.get(field), f"assessment {field}")
    digest = _string(value.get("candidate_worktree_digest"), "assessment worktree digest")
    if not digest.startswith("sha256:") or len(digest) != 71:
        raise SupervisionInputError("assessment candidate_worktree_digest is invalid")
    if value.get("source_commit") != control.get("source_commit"):
        raise SupervisionInputError("assessment source commit does not match control")
    if value.get("phase") != control.get("active_phase"):
        raise SupervisionInputError("assessment does not own the active phase")
    if value.get("verdict") not in VERDICTS:
        raise SupervisionInputError("assessment verdict is invalid")
    for field in ("assessor", "assessed_at", "earliest_divergence", "next_action"):
        _string(value.get(field), f"assessment {field}")

    evidence = value.get("evidence")
    if type(evidence) is not list or not evidence:
        raise SupervisionInputError("assessment evidence must be non-empty")
    evidence_ids: set[str] = set()
    for index, item in enumerate(evidence):
        label = f"assessment evidence[{index}]"
        if type(item) is not dict:
            raise SupervisionInputError(f"{label} must be an object")
        _exact_keys(item, EVIDENCE_KEYS, label)
        identifier = _string(item.get("id"), f"{label}.id")
        if identifier in evidence_ids:
            raise SupervisionInputError(f"{label}.id must be unique")
        evidence_ids.add(identifier)
        if item.get("scope") not in {"candidate", "source"}:
            raise SupervisionInputError(f"{label}.scope is invalid")
        _safe_relative_path(item.get("path"), f"{label}.path")
        item_digest = _string(item.get("sha256"), f"{label}.sha256")
        if not item_digest.startswith("sha256:") or len(item_digest) != 71:
            raise SupervisionInputError(f"{label}.sha256 is invalid")

    completed = _string_list(
        value.get("completed_requirements"), "assessment completed_requirements"
    )
    unresolved = _string_list(
        value.get("unresolved_requirements"), "assessment unresolved_requirements"
    )
    requirements = set(control["phase_exit_requirements"])
    if not set(completed).issubset(requirements):
        raise SupervisionInputError("assessment completed unknown requirements")
    if not set(unresolved).issubset(requirements):
        raise SupervisionInputError("assessment unresolved unknown requirements")
    if set(completed).intersection(unresolved):
        raise SupervisionInputError("a requirement cannot be complete and unresolved")

    defects = value.get("defects")
    if type(defects) is not list:
        raise SupervisionInputError("assessment defects must be an array")
    for index, defect in enumerate(defects):
        label = f"assessment defects[{index}]"
        if type(defect) is not dict:
            raise SupervisionInputError(f"{label} must be an object")
        _exact_keys(defect, DEFECT_KEYS, label)
        if defect.get("severity") not in {"MAJOR", "MINOR"}:
            raise SupervisionInputError(f"{label}.severity is invalid")
        _string(defect.get("owner_layer"), f"{label}.owner_layer")
        _string(defect.get("summary"), f"{label}.summary")
        references = _string_list(defect.get("evidence_ids"), f"{label}.evidence_ids")
        if not references or not set(references).issubset(evidence_ids):
            raise SupervisionInputError(f"{label} references unknown evidence")

    if value["verdict"] == "PASS":
        if defects or unresolved or set(completed) != requirements:
            raise SupervisionInputError("PASS requires every exit requirement and no defect")
        if value["earliest_divergence"] != "none":
            raise SupervisionInputError("PASS cannot name a divergence")
    elif value["verdict"] == "REWORK":
        if not defects and not unresolved:
            raise SupervisionInputError("REWORK requires a defect or unresolved requirement")
        if value["earliest_divergence"] == "none":
            raise SupervisionInputError("REWORK requires the earliest divergence")
    return dict(value)


def _is_ancestor(repository: Path, ancestor: str, descendant: str) -> bool:
    completed = _git_result(
        repository, "merge-base", "--is-ancestor", ancestor, descendant
    )
    if completed.returncode not in {0, 1}:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        raise SupervisionInputError(detail or "cannot verify Git ancestry")
    return completed.returncode == 0


def capture_candidate(
    repository: Path, control: Mapping[str, Any]
) -> CandidateState:
    repository = repository.resolve()
    head = _git(repository, "rev-parse", "HEAD^{commit}").decode("ascii").strip()
    tree = _git(repository, "rev-parse", "HEAD^{tree}").decode("ascii").strip()
    product_base = control["trusted_product_baseline_commit"]
    plan_commit = control["trusted_plan_commit"]
    for commit in (product_base, plan_commit):
        _git(repository, "cat-file", "-e", f"{commit}^{{commit}}")
    if not _is_ancestor(repository, product_base, plan_commit):
        raise SupervisionInputError("trusted plan does not descend from product baseline")
    if not _is_ancestor(repository, plan_commit, head):
        raise SupervisionInputError("candidate does not descend from trusted plan")

    status = _git(repository, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    unstaged = _git(repository, "diff", "--no-ext-diff", "--binary", "--")
    staged = _git(repository, "diff", "--cached", "--no-ext-diff", "--binary", "--")
    untracked = _decode_paths(
        _git(repository, "ls-files", "--others", "--exclude-standard", "-z")
    )
    untracked_digests: list[tuple[str, str]] = []
    for relative in sorted(untracked):
        path = repository / relative
        if path.is_symlink():
            digest = _sha256_bytes(path.readlink().as_posix().encode("utf-8"))
        elif path.is_file():
            digest = _file_digest(path)
        else:
            digest = "missing"
        untracked_digests.append((relative, digest))

    changed_paths = set(
        _decode_paths(
            _git(repository, "diff", "--name-only", "-z", f"{plan_commit}..{head}", "--")
        )
    )
    changed_paths.update(
        _decode_paths(_git(repository, "diff", "--name-only", "-z", "--"))
    )
    changed_paths.update(
        _decode_paths(_git(repository, "diff", "--cached", "--name-only", "-z", "--"))
    )
    changed_paths.update(untracked)
    worktree_digest = _canonical_digest(
        {
            "head": head,
            "tree": tree,
            "status": _sha256_bytes(status),
            "unstaged": _sha256_bytes(unstaged),
            "staged": _sha256_bytes(staged),
            "untracked": untracked_digests,
        }
    )
    return CandidateState(
        branch=_branch(repository),
        head=head,
        tree=tree,
        clean=not bool(status),
        worktree_digest=worktree_digest,
        changed_paths=tuple(sorted(changed_paths)),
    )


def check_evidence(
    assessment: Mapping[str, Any],
    candidate_repository: Path,
    source_repository: Path,
) -> EvidenceState:
    roots = {
        "candidate": candidate_repository.resolve(),
        "source": source_repository.resolve(),
    }
    missing: list[str] = []
    mismatched: list[str] = []
    for item in assessment["evidence"]:
        root = roots[item["scope"]]
        path = (root / item["path"]).resolve()
        try:
            path.relative_to(root)
        except ValueError:
            mismatched.append(item["id"])
            continue
        if path.is_symlink() or not path.is_file():
            missing.append(item["id"])
        elif _file_digest(path) != item["sha256"]:
            mismatched.append(item["id"])
    return EvidenceState(
        valid=not missing and not mismatched,
        missing=tuple(sorted(missing)),
        mismatched=tuple(sorted(mismatched)),
    )


def audit(
    control: Mapping[str, Any],
    assessment: Mapping[str, Any],
    candidate_repository: Path,
    source_repository: Path,
    *,
    supervision_repository: Path,
    supervisor_branch: str | None,
    supervisor_commit: str | None = None,
    direction_report: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    control = validate_control(control)
    assessment = validate_assessment(assessment, control)
    candidate_repository = candidate_repository.resolve()
    supervision_repository = supervision_repository.resolve()
    source_repository = source_repository.resolve()
    candidate = capture_candidate(candidate_repository, control)
    source_commit = _git(
        source_repository.resolve(), "rev-parse", "HEAD^{commit}"
    ).decode("ascii").strip()
    source_clean = not bool(
        _git(source_repository.resolve(), "status", "--porcelain", "--untracked-files=all")
    )
    evidence = check_evidence(assessment, candidate_repository, source_repository)
    direction_violations, direction_advisories, direction_report_digest = (
        _direction_findings(direction_report)
    )

    binding_errors: list[str] = []
    if candidate_repository != Path(control["candidate_repository"]):
        binding_errors.append("candidate-repository-mismatch")
    if supervision_repository != Path(control["supervision_repository"]):
        binding_errors.append("supervision-repository-mismatch")
    if source_repository != Path(control["source_repository"]):
        binding_errors.append("source-repository-mismatch")
    if candidate.branch != control["candidate_branch"]:
        binding_errors.append("candidate-branch-mismatch")
    if supervisor_branch != control["supervision_branch"]:
        binding_errors.append("supervision-branch-mismatch")
    if source_commit != control["source_commit"]:
        binding_errors.append("source-commit-mismatch")
    if not source_clean:
        binding_errors.append("source-worktree-not-clean")
    if direction_report is not None:
        if direction_report.get("repository") != str(candidate_repository):
            binding_errors.append("direction-report-repository-mismatch")
        if direction_report.get("head") != candidate.head:
            binding_errors.append("direction-report-head-mismatch")

    stale_reasons: list[str] = []
    if assessment["candidate_commit"] != candidate.head:
        stale_reasons.append("candidate-commit-changed")
    if assessment["candidate_tree"] != candidate.tree:
        stale_reasons.append("candidate-tree-changed")
    if assessment["candidate_worktree_digest"] != candidate.worktree_digest:
        stale_reasons.append("candidate-worktree-changed")
    if not evidence.valid:
        stale_reasons.append("assessment-evidence-missing-or-changed")

    report: dict[str, Any] = {
        "schema": REPORT_SCHEMA,
        "observed_at": _now(),
        "iteration": control["iteration"],
        "objective": control["objective"],
        "supervisor_branch": supervisor_branch,
        "supervisor_commit": supervisor_commit,
        "supervision_repository": str(supervision_repository),
        "candidate_repository": str(candidate_repository),
        "source_repository": str(source_repository),
        "candidate_branch": candidate.branch,
        "candidate_commit": candidate.head,
        "candidate_tree": candidate.tree,
        "candidate_clean": candidate.clean,
        "candidate_worktree_digest": candidate.worktree_digest,
        "candidate_changed_paths": list(candidate.changed_paths),
        "candidate_self_report_used": False,
        "active_phase": control["active_phase"],
        "phase_exit_case_id": control["phase_exit_case_id"],
        "assessment_verdict": assessment["verdict"],
        "assessment_status": "STALE" if stale_reasons else "FRESH",
        "binding_errors": binding_errors,
        "stale_reasons": stale_reasons,
        "evidence_missing": list(evidence.missing),
        "evidence_mismatched": list(evidence.mismatched),
        "direction_check_status": (
            "CORRECT"
            if direction_violations
            else "ADVISORY"
            if direction_advisories
            else "PASS"
        )
        if direction_report is not None
        else "NOT_RUN",
        "direction_report_digest": direction_report_digest,
        "direction_violations": list(direction_violations),
        "direction_advisories": list(direction_advisories),
        "direction_progress_verdict": (
            direction_report.get("progress_verdict")
            if direction_report is not None
            else None
        ),
        "direction_next_phase": (
            direction_report.get("next_phase")
            if direction_report is not None
            and direction_report.get("progress_verdict")
            == "CAPABILITY_EVIDENCE_PRESENT"
            else None
        ),
        "semantic_assessment_required": False,
        "semantic_supervision_focus": list(SEMANTIC_SUPERVISION_FOCUS),
        "correction": None,
        "defects": assessment["defects"],
        "unresolved_requirements": assessment["unresolved_requirements"],
        "decision": "CONTINUE",
        "advance_to": None,
        "phase_change_allowed": False,
        "next_action": assessment["next_action"],
        "task_should_stop": False,
        "authorization_required": False,
        "requires_result": False,
        "check_interval_minutes": control["check_interval_minutes"],
        "attention_required": True,
    }
    if binding_errors:
        report["decision"] = "RECOVER_SUPERVISION"
        report["next_action"] = (
            "修复监督对唯一开发分支、监督分支或 exact Source 的绑定；开发继续当前阶段。"
        )
        return report
    if direction_violations:
        correction = _build_correction(control, candidate, direction_violations)
        report["decision"] = "CORRECT"
        report["correction"] = correction
        report["next_action"] = " ".join(correction["required_actions"])
        return report
    if stale_reasons:
        report["semantic_assessment_required"] = True
        report["next_action"] = (
            "立即按目标一致、实现方式、体验进展和通用根因四项复核当前 HEAD/工作树；"
            "若任一项偏离则直接 CORRECT，开发继续且候选自报不能晋级。"
        )
        return report
    if assessment["verdict"] == "REWORK":
        report["decision"] = "CORRECT"
        return report
    if assessment["verdict"] == "NOT_RUN":
        return report
    if not candidate.clean:
        report["stale_reasons"] = ["candidate-worktree-not-clean-for-advance"]
        report["assessment_status"] = "FRESH-NOT-ADVANCEABLE"
        report["next_action"] = (
            "独立评估已完成，但只有 clean commit 可以晋级；开发继续整理当前阶段候选。"
        )
        return report

    report["decision"] = "ADVANCE"
    report["advance_to"] = control["next_phase"]
    report["phase_change_allowed"] = True
    report["attention_required"] = False
    report["next_action"] = (
        f"独立证据允许从 Phase {control['active_phase']} 推进到 "
        f"{control['next_phase']}；开发继续。"
    )
    return report


def _read_trusted_json(repository: Path, path: Path, label: str) -> dict[str, Any]:
    repository = repository.resolve()
    resolved = path.resolve()
    try:
        relative = resolved.relative_to(repository).as_posix()
    except ValueError as exc:
        raise SupervisionInputError(f"{label} must be inside supervision repository") from exc
    if resolved.is_symlink():
        raise SupervisionInputError(f"{label} must not be a symlink")
    _git(repository, "ls-files", "--error-unmatch", "--", relative)
    if _git(repository, "status", "--porcelain", "--", relative):
        raise SupervisionInputError(f"{label} must be clean and committed")
    if _git(repository, "show", f"HEAD:{relative}") != resolved.read_bytes():
        raise SupervisionInputError(f"{label} bytes do not match supervision HEAD")
    return load_json(resolved)


def _supervision_output_path(repository: Path, path: Path, label: str) -> Path:
    """Keep every monitor-owned record inside the supervision worktree."""

    repository = repository.resolve()
    resolved = path.resolve()
    try:
        resolved.relative_to(repository)
    except ValueError as exc:
        raise SupervisionInputError(
            f"{label} must be inside supervision repository"
        ) from exc
    if resolved.is_symlink():
        raise SupervisionInputError(f"{label} must not be a symlink")
    return resolved


def write_heartbeat(path: Path, report: Mapping[str, Any]) -> None:
    payload = {
        "schema": HEARTBEAT_SCHEMA,
        "observed_at": report.get("observed_at", _now()),
        "decision": report.get("decision", "RECOVER_SUPERVISION"),
        "supervisor_branch": report.get("supervisor_branch"),
        "supervisor_commit": report.get("supervisor_commit"),
        "candidate_branch": report.get("candidate_branch"),
        "candidate_commit": report.get("candidate_commit"),
        "candidate_tree": report.get("candidate_tree"),
        "candidate_clean": report.get("candidate_clean"),
        "candidate_worktree_digest": report.get("candidate_worktree_digest"),
        "assessment_status": report.get("assessment_status"),
        "direction_check_status": report.get("direction_check_status"),
        "direction_report_digest": report.get("direction_report_digest"),
        "direction_violations": report.get("direction_violations", []),
        "semantic_assessment_required": report.get(
            "semantic_assessment_required", False
        ),
        "correction_id": (
            report.get("correction", {}).get("correction_id")
            if isinstance(report.get("correction"), dict)
            else None
        ),
        "directive_path": report.get("directive_path"),
        "monitor_started_at": report.get("monitor_started_at"),
        "monitor_loaded_code_digests": report.get(
            "monitor_loaded_code_digests", {}
        ),
        "monitor_head_code_digests": report.get("monitor_head_code_digests", {}),
        "monitor_code_matches_head": report.get("monitor_code_matches_head"),
        "attention_required": report.get("attention_required", True),
        "task_should_stop": False,
        "authorization_required": False,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def write_directive(path: Path, report: Mapping[str, Any]) -> None:
    correction = report.get("correction")
    if not isinstance(correction, dict):
        correction = None
    payload = {
        "schema": DIRECTIVE_SCHEMA,
        "observed_at": report.get("observed_at", _now()),
        "decision": report.get("decision", "RECOVER_SUPERVISION"),
        "objective": report.get("objective"),
        "active_phase": report.get("active_phase"),
        "candidate_branch": report.get("candidate_branch"),
        "candidate_commit": report.get("candidate_commit"),
        "candidate_worktree_digest": report.get("candidate_worktree_digest"),
        "direction_check_status": report.get("direction_check_status"),
        "direction_violations": report.get("direction_violations", []),
        "semantic_assessment_required": report.get(
            "semantic_assessment_required", False
        ),
        "semantic_supervision_focus": report.get(
            "semantic_supervision_focus", list(SEMANTIC_SUPERVISION_FOCUS)
        ),
        "correction": correction,
        "next_action": report.get("next_action"),
        "monitor_code_matches_head": report.get("monitor_code_matches_head"),
        "task_should_stop": False,
        "authorization_required": False,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def build_parser() -> argparse.ArgumentParser:
    root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--supervision-repository", type=Path, default=root)
    parser.add_argument("--candidate-repository", type=Path)
    parser.add_argument("--source-repository", type=Path)
    parser.add_argument(
        "--control",
        type=Path,
        default=root / "docs/project/iterations/iteration-010/supervision/control.json",
    )
    parser.add_argument(
        "--assessment",
        type=Path,
        default=root
        / "docs/project/iterations/iteration-010/supervision/assessment-001.json",
    )
    parser.add_argument(
        "--heartbeat",
        type=Path,
        default=root / "var/supervision/heartbeat.json",
    )
    parser.add_argument(
        "--directive",
        type=Path,
        help=(
            "current machine-readable instruction for the development task; "
            "defaults to <supervision>/var/supervision/directive.json and "
            "must remain inside the supervision repository"
        ),
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="continuously recheck the exact candidate and refresh the heartbeat",
    )
    parser.add_argument(
        "--poll-seconds",
        type=int,
        default=30,
        help="watch polling interval; must be positive and no longer than the control interval",
    )
    return parser


def _run_once(arguments: argparse.Namespace) -> tuple[dict[str, Any], int]:
    report: dict[str, Any]
    exit_code = 0
    supervision_repository: Path | None = None
    candidate_repository: Path | None = None
    try:
        supervision_repository = arguments.supervision_repository.resolve()
        control = _read_trusted_json(
            supervision_repository, arguments.control, "control file"
        )
        control = validate_control(control)
        candidate_repository = (
            arguments.candidate_repository
            or Path(control["candidate_repository"])
        ).resolve()
        source_repository = (
            arguments.source_repository
            or Path(control["source_repository"])
        ).resolve()
        if supervision_repository == candidate_repository:
            raise SupervisionInputError(
                "supervision and candidate repositories must be independent"
            )
        if arguments.poll_seconds <= 0:
            raise SupervisionInputError("poll seconds must be positive")
        if arguments.poll_seconds > control["check_interval_minutes"] * 60:
            raise SupervisionInputError(
                "poll seconds must not exceed the trusted control interval"
            )
        assessment = _read_trusted_json(
            supervision_repository, arguments.assessment, "assessment file"
        )
        direction_report = direction_check.check_repository(candidate_repository)
        report = audit(
            control,
            assessment,
            candidate_repository,
            source_repository,
            supervision_repository=supervision_repository,
            supervisor_branch=_branch(supervision_repository),
            supervisor_commit=_git(
                supervision_repository, "rev-parse", "HEAD^{commit}"
            ).decode("ascii").strip(),
            direction_report=direction_report,
        )
        monitor_identity = capture_monitor_identity(supervision_repository)
        report.update(monitor_identity)
        if not monitor_identity["monitor_code_matches_head"]:
            report["decision"] = "RECOVER_SUPERVISION"
            report["correction"] = None
            report["attention_required"] = True
            report["next_action"] = (
                "监督进程加载的代码与监督 HEAD 不一致；立即重启 watcher，开发继续。"
            )
            exit_code = 2
    except (
        OSError,
        UnicodeError,
        SupervisionInputError,
        direction_check.DirectionCheckError,
    ) as exc:
        exit_code = 2
        report = {
            "schema": REPORT_SCHEMA,
            "observed_at": _now(),
            "decision": "RECOVER_SUPERVISION",
            "error": str(exc),
            "next_action": "修复监督输入或目标绑定；开发任务继续当前阶段。",
            "task_should_stop": False,
            "authorization_required": False,
            "requires_result": False,
            "attention_required": True,
        }
    if supervision_repository is not None:
        requested_directive_path = (
            arguments.directive
            if getattr(arguments, "directive", None) is not None
            else supervision_repository / "var/supervision/directive.json"
        )
        try:
            directive_path = _supervision_output_path(
                supervision_repository,
                requested_directive_path,
                "directive path",
            )
            report["directive_path"] = str(directive_path)
            write_directive(directive_path, report)
        except (OSError, SupervisionInputError) as exc:
            report["directive_error"] = str(exc)
            report["decision"] = "RECOVER_SUPERVISION"
            report["next_action"] = (
                "修复监督分支内的指令记录写入；开发继续当前阶段。"
            )
            exit_code = 2
        try:
            heartbeat_path = _supervision_output_path(
                supervision_repository,
                arguments.heartbeat,
                "heartbeat path",
            )
            write_heartbeat(heartbeat_path, report)
        except (OSError, SupervisionInputError) as exc:
            report["heartbeat_error"] = str(exc)
            report["decision"] = "RECOVER_SUPERVISION"
            report["next_action"] = (
                "修复监督分支内的 heartbeat 记录写入；开发继续当前阶段。"
            )
            exit_code = 2
    return report, exit_code


def run_supervision(
    arguments: argparse.Namespace,
    *,
    maximum_cycles: int | None = None,
    sleep: Any = time.sleep,
    emit: Any = print,
) -> int:
    """Run once or continuously; bounded cycles exist only for deterministic tests."""

    cycle = 0
    last_exit_code = 0
    while True:
        report, last_exit_code = _run_once(arguments)
        report["watch_active"] = bool(arguments.watch)
        report["poll_seconds"] = arguments.poll_seconds
        emit(
            json.dumps(
                report,
                ensure_ascii=False,
                indent=None if arguments.watch else 2,
                sort_keys=True,
            )
        )
        cycle += 1
        if not arguments.watch or (
            maximum_cycles is not None and cycle >= maximum_cycles
        ):
            return last_exit_code
        sleep(arguments.poll_seconds)


def main(argv: Sequence[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    try:
        return run_supervision(arguments)
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
