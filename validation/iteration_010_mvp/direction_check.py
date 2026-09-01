#!/usr/bin/env python3
"""Lightweight PDR-014 direction guard and capability progress reporter.

The guard deliberately checks repository direction, not answer semantics.  It
prevents growth of the two frozen prompt-heavy implementation surfaces,
rejects newly-added legacy protocol versions and obvious evaluation-specific
branches, and reports the four PDR-014 progress dimensions.  A
``NO_PRODUCT_PROGRESS`` result is informational: it resets the next task to
the earliest missing phase without stopping development.
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


TRUSTED_PDR014_BASELINE = "8131caecea912ae60c68e20bd4e241c03a0efe2c"
REPORT_SCHEMA = "ITER_010_CAPABILITY_DIRECTION_REPORT@1"
EVIDENCE_SCHEMA = "ITER_010_CAPABILITY_PROGRESS_EVIDENCE@1"

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


def _line_count(value: bytes) -> int:
    return len(value.decode("utf-8", errors="strict").splitlines())


def _current_line_count(repository: Path, path: str) -> int:
    candidate = repository / path
    if not candidate.exists():
        return 0
    return len(candidate.read_text(encoding="utf-8").splitlines())


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


def _added_line_violations(delta: RepositoryDelta) -> list[dict[str, str]]:
    violations: list[dict[str, str]] = []
    for path, lines in sorted(delta.added_lines.items()):
        for ordinal, line in enumerate(lines, start=1):
            if PROTOCOL_VERSION_RE.search(line):
                violations.append(
                    {
                        "code": "NEW_LEGACY_PROTOCOL_VERSION",
                        "path": path,
                        "detail": f"added-line ordinal {ordinal}",
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


def _next_phase(evidence: CapabilityEvidence) -> str:
    if not evidence.agent:
        return "PHASE_A_SOURCE_ONLY_AGENT"
    if not evidence.knowledge:
        return "PHASE_B_WORLD_MODEL_COGNITION"
    if not evidence.browser:
        return "PHASE_C_INTEGRATED_BROWSER_ALPHA"
    return "PHASE_D_QUALITY_GATE"


def _non_product_only(paths: Sequence[str]) -> bool:
    if not paths:
        return True
    return all(
        path.startswith(("docs/", "tests/", "validation/"))
        or path in PROMPT_SCHEMA_PATHS
        or "/prompts/" in f"/{path}"
        or "/schemas/" in f"/{path}"
        for path in paths
    )


def build_direction_report(
    repository: Path,
    base: str,
    delta: RepositoryDelta,
    evidence: CapabilityEvidence,
) -> dict[str, object]:
    repository = repository.resolve()
    counts, violations = _legacy_growth(repository, base)
    violations.extend(_added_line_violations(delta))
    prompt_schema_paths = _prompt_schema_delta(delta.changed_paths)
    if prompt_schema_paths and (
        not evidence.trajectory or not evidence.replacement_experiment
    ):
        violations.append(
            {
                "code": "PROMPT_SCHEMA_WITHOUT_LAYER_EVIDENCE",
                "path": ",".join(prompt_schema_paths),
                "detail": "trajectory and replacement experiment are required",
            }
        )
    capability_present = bool(evidence.knowledge or evidence.agent or evidence.browser)
    if _non_product_only(delta.changed_paths) and not capability_present:
        progress_verdict = "NO_PRODUCT_PROGRESS"
    elif capability_present:
        progress_verdict = "CAPABILITY_EVIDENCE_PRESENT"
    else:
        progress_verdict = "CAPABILITY_EVIDENCE_PENDING"
    delta_material = json.dumps(
        {
            "paths": delta.changed_paths,
            "added_lines": {
                path: lines for path, lines in sorted(delta.added_lines.items())
            },
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return {
        "schema": REPORT_SCHEMA,
        "baseline": base,
        "head": _git(repository, "rev-parse", "HEAD").decode("ascii").strip(),
        "repository": str(repository),
        "direction_verdict": "FAIL" if violations else "PASS",
        "progress_verdict": progress_verdict,
        "next_phase": _next_phase(evidence),
        "changed_paths": list(delta.changed_paths),
        "untracked_paths": list(delta.untracked_paths),
        "candidate_delta_digest": "sha256:"
        + hashlib.sha256(delta_material).hexdigest(),
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
        "violations": violations,
    }


def check_repository(
    repository: Path,
    *,
    base: str = TRUSTED_PDR014_BASELINE,
    evidence_path: Path | None = None,
) -> dict[str, object]:
    repository = repository.resolve()
    delta = collect_repository_delta(repository, base)
    evidence = load_capability_evidence(evidence_path)
    return build_direction_report(repository, base, delta, evidence)


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
    parser.add_argument("--base", default=TRUSTED_PDR014_BASELINE)
    parser.add_argument("--progress-evidence", type=Path)
    parser.add_argument("--output", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    try:
        report = check_repository(
            arguments.repository,
            base=arguments.base,
            evidence_path=arguments.progress_evidence,
        )
        if arguments.output is not None:
            _write_private_json(arguments.output, report)
    except (DirectionCheckError, OSError, UnicodeError) as exc:
        print(f"direction check input error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if report["direction_verdict"] == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
