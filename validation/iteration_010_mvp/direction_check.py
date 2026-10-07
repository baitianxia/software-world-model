#!/usr/bin/env python3
"""Report static repository risk signals without judging product correctness.

Line counts and regex matches are review hints, not proof of a direction or
answer defect. Evidence references are declarations, not verified capability.
The current task comes only from project/current.md; this helper never advances
it or diagnoses a root cause. Reports can be checked for freshness, not truth.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence


REPORT_SCHEMA = "ITER_010_CAPABILITY_DIRECTION_REPORT@2"
EVIDENCE_SCHEMA = "ITER_010_CAPABILITY_PROGRESS_EVIDENCE@1"
TASK_1 = "TASK-1-MINIMUM-COMPLETE-EXPERIENCE"
TASK_2 = "TASK-2-DIRECTION-AND-ATTRIBUTION"
# These are repository documents, not frozen baselines.  The current task is
# read from the document on every run so that this helper cannot become a
# second task state machine.
CURRENT_CONTEXT_PATH = Path("docs/project/current.md")
CURRENT_PLAN_PATH = Path(
    "docs/project/iterations/iteration-010/development-design/"
    "EXECUTION-PLAN-CURRENT.md"
)

FROZEN_LEGACY_GROWTH_PATHS = (
    "src/software_world_model/ai_infrastructure/"
    "conversational_engineering_model.py",
    "tests/test_conversational_engineering_model.py",
)

PROMPT_SCHEMA_PATHS = frozenset(
    {
        "src/software_world_model/ai_infrastructure/"
        "conversational_engineering_model.py",
        "docs/system/contracts/application/engineering-conversation.md",
    }
)

PROTOCOL_VERSION_RE = re.compile(
    r"\bENGINEERING_AGENT_[A-Z][A-Z0-9_]*@[1-9][0-9]*\b"
)
ANSWER_TEXT_RULE_RE = re.compile(
    r"(?i)(?:answer|draft|review).{0,80}"
    r"(?:markdown|heading|inline[_ -]?code|substring|content[_ -]?unit)"
    r"|(?:markdown|heading|inline[_ -]?code|substring|content[_ -]?unit)"
    r".{0,80}(?:answer|draft|review)"
)
EVALUATION_SPECIFIC_RE = re.compile(
    r"\b(?:mall-(?:admin|portal|search)|UmsAdminService|generateOrder|"
    r"CommonResult)\b"
)

EVIDENCE_KEYS = {
    "schema",
    "knowledge_evidence",
    "agent_behavior_evidence",
    "browser_evidence",
    "trajectory_evidence",
    "replacement_experiment_evidence",
    "verification_cases",
}


class DirectionCheckError(ValueError):
    """Raised when inputs cannot support a trustworthy direction report."""


@dataclass(frozen=True)
class CapabilityEvidence:
    knowledge: tuple[str, ...] = ()
    agent: tuple[str, ...] = ()
    browser: tuple[str, ...] = ()
    trajectory: tuple[str, ...] = ()
    replacement_experiment: tuple[str, ...] = ()
    verification_cases: tuple[str, ...] = ()


@dataclass(frozen=True)
class RepositoryDelta:
    changed_paths: tuple[str, ...]
    added_lines: Mapping[str, tuple[str, ...]]
    untracked_paths: tuple[str, ...]


def _git(repository: Path, *arguments: str) -> bytes:
    completed = subprocess.run(
        ["git", "-C", str(repository), *arguments],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        raise DirectionCheckError(detail or "git command failed")
    return completed.stdout


def _decode_paths(raw: bytes) -> tuple[str, ...]:
    values = raw.split(b"\0")
    return tuple(
        value.decode("utf-8", errors="strict")
        for value in values
        if value
    )


def _parse_added_lines(diff: str) -> dict[str, tuple[str, ...]]:
    current_path: str | None = None
    additions: dict[str, list[str]] = {}
    for line in diff.splitlines():
        if line.startswith("+++ b/"):
            current_path = line[6:]
            additions.setdefault(current_path, [])
            continue
        if line.startswith("+++ /dev/null"):
            current_path = None
            continue
        if current_path is not None and line.startswith("+"):
            additions[current_path].append(line[1:])
    return {path: tuple(lines) for path, lines in additions.items()}


def collect_repository_delta(repository: Path, base: str) -> RepositoryDelta:
    repository = repository.resolve()
    _git(repository, "cat-file", "-e", f"{base}^{{commit}}")
    changed = _decode_paths(
        _git(repository, "diff", "--name-only", "-z", base, "--")
    )
    untracked = _decode_paths(
        _git(repository, "ls-files", "--others", "--exclude-standard", "-z")
    )
    raw_diff = _git(
        repository,
        "diff",
        "--no-ext-diff",
        "--unified=0",
        base,
        "--",
    ).decode("utf-8", errors="strict")
    additions: dict[str, tuple[str, ...]] = _parse_added_lines(raw_diff)
    for path in untracked:
        candidate = (repository / path).resolve()
        try:
            candidate.relative_to(repository)
            lines = candidate.read_text(encoding="utf-8").splitlines()
        except (UnicodeDecodeError, OSError, ValueError):
            lines = []
        additions[path] = tuple(lines)
    paths = tuple(sorted(set(changed) | set(untracked)))
    return RepositoryDelta(
        changed_paths=paths,
        added_lines=additions,
        untracked_paths=tuple(sorted(untracked)),
    )


def _workspace_digest(
    repository: Path,
    base: str,
    delta: RepositoryDelta,
    *,
    ignored_paths: frozenset[str] = frozenset(),
) -> str:
    """Digest the complete local delta, including deletions and untracked bytes."""

    diff = _git(
        repository, "diff", "--no-ext-diff", "--no-textconv", "--binary", base, "--"
    )
    untracked: list[tuple[str, bytes]] = []
    for path in delta.untracked_paths:
        if path in ignored_paths:
            continue
        candidate = repository / path
        value = (
            os.readlink(candidate).encode("utf-8")
            if candidate.is_symlink()
            else candidate.read_bytes()
        )
        untracked.append((path, value))
    material = bytearray(diff)
    for path, value in untracked:
        material.extend(b"\0UNTRACKED\0")
        material.extend(path.encode("utf-8"))
        material.extend(b"\0")
        material.extend(value)
    return "sha256:" + hashlib.sha256(bytes(material)).hexdigest()


def _line_count(value: bytes) -> int:
    return len(value.decode("utf-8", errors="strict").splitlines())


def _current_line_count(repository: Path, path: str) -> int:
    candidate = repository / path
    if not candidate.exists():
        return 0
    return len(candidate.read_text(encoding="utf-8").splitlines())


def _file_digest(repository: Path, path: Path) -> str:
    return "sha256:" + hashlib.sha256((repository / path).read_bytes()).hexdigest()


def _legacy_growth(
    repository: Path, base: str
) -> tuple[dict[str, dict[str, int]], list[dict[str, str]]]:
    counts: dict[str, dict[str, int]] = {}
    violations: list[dict[str, str]] = []
    for path in FROZEN_LEGACY_GROWTH_PATHS:
        baseline = _line_count(_git(repository, "show", f"{base}:{path}"))
        current = _current_line_count(repository, path)
        counts[path] = {
            "baseline_lines": baseline,
            "current_lines": current,
            "net_lines": current - baseline,
        }
        if current > baseline:
            violations.append(
                {
                    "code": "LEGACY_PROTOCOL_NET_GROWTH",
                    "path": path,
                    "detail": f"current {current} > baseline {baseline}",
                }
            )
    return counts, violations


def _protocol_exists_at_base(repository: Path, base: str, token: str) -> bool:
    completed = subprocess.run(
        ["git", "-C", str(repository), "grep", "-F", "-q", token, base, "--"],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    if completed.returncode not in {0, 1}:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        raise DirectionCheckError(detail or "git grep failed")
    return completed.returncode == 0


def _added_line_violations(
    repository: Path, base: str, delta: RepositoryDelta
) -> list[dict[str, str]]:
    violations: list[dict[str, str]] = []
    baseline_protocol_cache: dict[str, bool] = {}
    for path, lines in sorted(delta.added_lines.items()):
        for ordinal, line in enumerate(lines, start=1):
            for match in PROTOCOL_VERSION_RE.finditer(line):
                token = match.group(0)
                if token not in baseline_protocol_cache:
                    baseline_protocol_cache[token] = _protocol_exists_at_base(
                        repository, base, token
                    )
                exists = baseline_protocol_cache[token]
                if not exists:
                    violations.append(
                        {
                            "code": "NEW_LEGACY_PROTOCOL_VERSION",
                            "path": path,
                            "detail": (
                                f"added-line ordinal {ordinal}: {token}"
                            ),
                        }
                    )
            if path.startswith("src/software_world_model/") and (
                ANSWER_TEXT_RULE_RE.search(line)
            ):
                violations.append(
                    {
                        "code": "ANSWER_TEXT_SEMANTIC_RULE",
                        "path": path,
                        "detail": f"added-line ordinal {ordinal}",
                    }
                )
            if path.startswith("src/software_world_model/") and (
                EVALUATION_SPECIFIC_RE.search(line)
            ):
                violations.append(
                    {
                        "code": "EVALUATION_SPECIFIC_PRODUCT_LITERAL",
                        "path": path,
                        "detail": f"added-line ordinal {ordinal}",
                    }
                )
    return violations


def _unique_string_list(value: Any, label: str) -> tuple[str, ...]:
    if type(value) is not list or any(type(item) is not str for item in value):
        raise DirectionCheckError(f"{label} must be a JSON string array")
    normalized = tuple(item.strip() for item in value)
    if any(not item for item in normalized) or len(set(normalized)) != len(normalized):
        raise DirectionCheckError(f"{label} must contain unique non-empty values")
    return normalized


def load_capability_evidence(path: Path | None) -> CapabilityEvidence:
    if path is None:
        return CapabilityEvidence()
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DirectionCheckError("progress evidence must be UTF-8 JSON") from exc
    if type(value) is not dict or set(value) != EVIDENCE_KEYS:
        raise DirectionCheckError("progress evidence must use its exact schema")
    if value["schema"] != EVIDENCE_SCHEMA:
        raise DirectionCheckError("unsupported progress evidence schema")
    return CapabilityEvidence(
        knowledge=_unique_string_list(
            value["knowledge_evidence"], "knowledge_evidence"
        ),
        agent=_unique_string_list(
            value["agent_behavior_evidence"], "agent_behavior_evidence"
        ),
        browser=_unique_string_list(
            value["browser_evidence"], "browser_evidence"
        ),
        trajectory=_unique_string_list(
            value["trajectory_evidence"], "trajectory_evidence"
        ),
        replacement_experiment=_unique_string_list(
            value["replacement_experiment_evidence"],
            "replacement_experiment_evidence",
        ),
        verification_cases=_unique_string_list(
            value["verification_cases"], "verification_cases"
        ),
    )


def _prompt_schema_delta(paths: Sequence[str]) -> tuple[str, ...]:
    return tuple(
        path
        for path in paths
        if path in PROMPT_SCHEMA_PATHS
        or "/prompts/" in f"/{path}"
        or "/schemas/" in f"/{path}"
    )


def _current_task(repository: Path) -> str:
    """Read the one task declared by the current project context."""

    text = (repository / CURRENT_CONTEXT_PATH).read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0] != "---" or "---" not in lines[1:]:
        raise DirectionCheckError("PROJECT-CURRENT must have frontmatter")
    frontmatter = lines[1:lines.index("---", 1)]
    declarations = [line for line in frontmatter if line.startswith("current_task:")]
    match = (
        re.fullmatch(r"current_task:[ \t]*(TASK-[0-9]+-[A-Z0-9-]+)[ \t]*", declarations[0])
        if len(declarations) == 1 else None
    )
    if match is None:
        raise DirectionCheckError("PROJECT-CURRENT must declare one exact current_task")
    return match.group(1)


def build_direction_report(
    repository: Path,
    base: str,
    delta: RepositoryDelta,
    evidence: CapabilityEvidence,
) -> dict[str, object]:
    repository = repository.resolve()
    counts, violations = _legacy_growth(repository, base)
    violations.extend(_added_line_violations(repository, base, delta))
    prompt_schema_paths = _prompt_schema_delta(delta.changed_paths)
    if prompt_schema_paths and (
        not evidence.trajectory or not evidence.replacement_experiment
    ):
        violations.append(
            {
                "code": "PROMPT_SCHEMA_WITHOUT_LAYER_EVIDENCE",
                "path": ",".join(prompt_schema_paths),
                "detail": "no trajectory/replacement references declared; inspect the change",
            }
        )
    delta_digest = _workspace_digest(repository, base, delta)
    decision = "REVIEW_STATIC_SIGNALS" if violations else "NO_STATIC_RISK_SIGNALS"
    current_task = _current_task(repository)
    current_plan_digest = _file_digest(repository, CURRENT_PLAN_PATH)
    current_context_digest = _file_digest(repository, CURRENT_CONTEXT_PATH)
    return {
        "schema": REPORT_SCHEMA,
        "baseline": base,
        "head": _git(repository, "rev-parse", "HEAD").decode("ascii").strip(),
        "repository": str(repository),
        "decision": decision,
        "direction_verdict": "STATIC_RISK" if violations else "NO_STATIC_RISK",
        "progress_verdict": "NOT_ASSESSED",
        "earliest_layer": "not-assessed",
        "current_task": current_task,
        "next_action": current_task,
        "current_plan_digest": current_plan_digest,
        "current_context_digest": current_context_digest,
        "changed_paths": list(delta.changed_paths),
        "untracked_paths": list(delta.untracked_paths),
        "candidate_delta_digest": delta_digest,
        "workspace_digest": delta_digest,
        "report_semantics": {
            "direction_verdict": "static-risk-signal-only",
            "progress_verdict": "not-assessed",
            "evidence_references": "unverified-declarations",
        },
        "legacy_line_counts": counts,
        "progress": {
            "knowledge_evidence": {
                "present": bool(evidence.knowledge),
                "refs": list(evidence.knowledge),
            },
            "agent_behavior_evidence": {
                "present": bool(evidence.agent),
                "refs": list(evidence.agent),
            },
            "browser_evidence": {
                "present": bool(evidence.browser),
                "refs": list(evidence.browser),
            },
            "prompt_schema_delta": {
                "present": bool(prompt_schema_paths),
                "paths": list(prompt_schema_paths),
            },
        },
        "layer_evidence": {
            "trajectory_refs": list(evidence.trajectory),
            "replacement_experiment_refs": list(evidence.replacement_experiment),
            "verification_cases": list(evidence.verification_cases),
        },
        "evidence": {
            "candidate_delta_digest": delta_digest,
            "changed_paths": list(delta.changed_paths),
            "untracked_paths": list(delta.untracked_paths),
            "verified": False,
            "source": "static-diff-only",
            "violations": violations,
            "capability_references_are_unverified": True,
        },
        "violations": violations,
    }


def check_repository(
    repository: Path,
    *,
    base: str | None = None,
    evidence_path: Path | None = None,
) -> dict[str, object]:
    repository = repository.resolve()
    effective_base = _git(
        repository, "rev-parse", "--verify", f"{base or 'HEAD'}^{{commit}}"
    ).decode("ascii").strip()
    delta = collect_repository_delta(repository, effective_base)
    evidence = load_capability_evidence(evidence_path)
    return build_direction_report(repository, effective_base, delta, evidence)


def validate_report(repository: Path, report_path: Path) -> dict[str, object]:
    """Reject reports tied to another HEAD or another current plan/context."""

    repository = repository.resolve()
    report_path = report_path.resolve()
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DirectionCheckError("direction report must be UTF-8 JSON") from exc
    if type(report) is not dict:
        raise DirectionCheckError("direction report must be a JSON object")
    head = _git(repository, "rev-parse", "HEAD").decode("ascii").strip()
    current_plan_digest = "sha256:" + hashlib.sha256(
        (repository / CURRENT_PLAN_PATH).read_bytes()
    ).hexdigest()
    current_context_digest = "sha256:" + hashlib.sha256(
        (repository / CURRENT_CONTEXT_PATH).read_bytes()
    ).hexdigest()
    baseline = report.get("baseline")
    workspace_digest = None
    if isinstance(baseline, str):
        delta = collect_repository_delta(repository, baseline)
        report_relative: frozenset[str] = frozenset()
        try:
            report_relative = frozenset(
                {str(report_path.resolve().relative_to(repository))}
            )
        except ValueError:
            pass
        workspace_digest = _workspace_digest(
            repository, baseline, delta, ignored_paths=report_relative
        )
    mismatches: list[str] = []
    if report.get("schema") != REPORT_SCHEMA:
        mismatches.append("schema")
    if report.get("head") != head:
        mismatches.append("head")
    if report.get("current_plan_digest") != current_plan_digest:
        mismatches.append("current_plan_digest")
    if report.get("current_context_digest") != current_context_digest:
        mismatches.append("current_context_digest")
    if workspace_digest is None or report.get("workspace_digest") != workspace_digest:
        mismatches.append("workspace_digest")
    return {
        "schema": "ITER_010_DIRECTION_REPORT_VALIDATION@1",
        "valid": not mismatches,
        "mismatches": mismatches,
        "report_path": str(report_path.resolve()),
        "current_head": head,
        "current_plan_digest": current_plan_digest,
        "current_context_digest": current_context_digest,
        "current_workspace_digest": workspace_digest,
    }


def _write_private_json(path: Path, value: Mapping[str, object]) -> None:
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "wb") as output:
        output.write(payload)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, default=Path.cwd())
    parser.add_argument(
        "--base",
        help="trusted parent commit for a committed candidate; defaults to current HEAD for local changes",
    )
    parser.add_argument("--progress-evidence", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--validate-report", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    try:
        repository = arguments.repository.resolve()
        if arguments.validate_report is not None:
            result = validate_report(repository, arguments.validate_report)
            print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
            return 0 if result["valid"] else 1
        report = check_repository(
            repository,
            base=arguments.base,
            evidence_path=arguments.progress_evidence,
        )
        if arguments.output is not None:
            _write_private_json(arguments.output, report)
    except (DirectionCheckError, OSError, UnicodeError) as exc:
        print(f"direction check input error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    # Static signals are review output, never a product/plan gate.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
