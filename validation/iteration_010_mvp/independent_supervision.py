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
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence


CONTROL_SCHEMA = "SWM_INDEPENDENT_SUPERVISION_CONTROL@2"
ASSESSMENT_SCHEMA = "SWM_INDEPENDENT_ASSESSMENT@2"
REPORT_SCHEMA = "SWM_INDEPENDENT_SUPERVISION_REPORT@2"
HEARTBEAT_SCHEMA = "SWM_SUPERVISION_HEARTBEAT@1"
VERDICTS = {"PASS", "REWORK", "NOT_RUN"}
SHA1_LENGTH = 40

CONTROL_KEYS = {
    "schema",
    "iteration",
    "candidate_branch",
    "supervision_branch",
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
    supervisor_branch: str | None,
    supervisor_commit: str | None = None,
) -> dict[str, Any]:
    control = validate_control(control)
    assessment = validate_assessment(assessment, control)
    candidate = capture_candidate(candidate_repository, control)
    source_commit = _git(
        source_repository.resolve(), "rev-parse", "HEAD^{commit}"
    ).decode("ascii").strip()
    source_clean = not bool(
        _git(source_repository.resolve(), "status", "--porcelain", "--untracked-files=all")
    )
    evidence = check_evidence(assessment, candidate_repository, source_repository)

    binding_errors: list[str] = []
    if candidate.branch != control["candidate_branch"]:
        binding_errors.append("candidate-branch-mismatch")
    if supervisor_branch != control["supervision_branch"]:
        binding_errors.append("supervision-branch-mismatch")
    if source_commit != control["source_commit"]:
        binding_errors.append("source-commit-mismatch")
    if not source_clean:
        binding_errors.append("source-worktree-not-clean")

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
    }
    if binding_errors:
        report["decision"] = "RECOVER_SUPERVISION"
        report["next_action"] = (
            "修复监督对唯一开发分支、监督分支或 exact Source 的绑定；开发继续当前阶段。"
        )
        return report
    if stale_reasons:
        report["next_action"] = (
            "立即对当前 HEAD 和工作树重新独立取证；开发继续，候选自报不能晋级。"
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
    parser.add_argument("--candidate-repository", type=Path, required=True)
    parser.add_argument("--source-repository", type=Path, required=True)
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
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    report: dict[str, Any]
    exit_code = 0
    try:
        supervision_repository = arguments.supervision_repository.resolve()
        candidate_repository = arguments.candidate_repository.resolve()
        source_repository = arguments.source_repository.resolve()
        if supervision_repository == candidate_repository:
            raise SupervisionInputError(
                "supervision and candidate repositories must be independent"
            )
        control = _read_trusted_json(
            supervision_repository, arguments.control, "control file"
        )
        assessment = _read_trusted_json(
            supervision_repository, arguments.assessment, "assessment file"
        )
        report = audit(
            control,
            assessment,
            candidate_repository,
            source_repository,
            supervisor_branch=_branch(supervision_repository),
            supervisor_commit=_git(
                supervision_repository, "rev-parse", "HEAD^{commit}"
            ).decode("ascii").strip(),
        )
    except (OSError, UnicodeError, SupervisionInputError) as exc:
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
        }
    try:
        write_heartbeat(arguments.heartbeat.resolve(), report)
    except OSError as exc:
        report["heartbeat_error"] = str(exc)
        exit_code = 2
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
