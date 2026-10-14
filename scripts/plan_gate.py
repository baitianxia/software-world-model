#!/usr/bin/env python3
"""Minimal mechanical gate for the active development plan.

Snapshot mode validates the fields of ``plan_execution_control.current_action``
that this gate enforces.  Diff mode uses the base tree's current action as the
only authority for the change: allowed/forbidden paths, gate files only under a
governance action, and no obvious secrets.  It does not interpret Results,
evidence, routes or iteration-specific state machines (simplified 2026-10-14;
the previous implementation is preserved in Git history).
"""

from __future__ import annotations
import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable, Mapping, Sequence


REPOSITORY = Path(__file__).resolve().parents[1]

BOOTSTRAP_ALLOWED_PATHS = (
    "AGENTS.md",
    ".githooks/plan-pre-commit",
    "scripts/docs.py",
    "scripts/plan_gate.py",
    "tests/test_docs_gate.py",
    "tests/test_plan_gate.py",
    ".github/workflows/plan-compliance.yml",
    "docs/system/",
    "docs/project/current.md",
    "docs/project/governance/",
    "docs/project/iterations/",
    "docs/_generated/",
)

BOOTSTRAP_FORBIDDEN_PATHS = ("src/software_world_model/",)

PROTECTED_GATE_PATHS = {
    ".githooks/plan-pre-commit",
    "scripts/docs.py",
    "scripts/plan_gate.py",
    "tests/test_docs_gate.py",
    "tests/test_plan_gate.py",
    ".github/workflows/plan-compliance.yml",
}

class PlanGateError(ValueError):
    """Raised when data cannot be parsed or inspected safely."""



@dataclass(frozen=True)
class _YamlLine:
    indentation: int
    content: str
    number: int



def _parse_scalar(value: str, line_number: int) -> object:
    value = value.strip()
    if value.startswith(("!", "&", "*", "|", ">")):
        raise PlanGateError(
            f"line {line_number}: tags, anchors, aliases, and block scalars are forbidden"
        )
    if value == "[]":
        return []
    if value == "{}":
        return {}
    if value.startswith(("[", "{")):
        raise PlanGateError(
            f"line {line_number}: non-empty inline collections are forbidden"
        )
    if value.startswith('"'):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError as error:
            raise PlanGateError(
                f"line {line_number}: invalid double-quoted scalar"
            ) from error
        if not isinstance(parsed, str):
            raise PlanGateError(f"line {line_number}: quoted scalar must be a string")
        return parsed
    if value.startswith("'"):
        if len(value) < 2 or not value.endswith("'"):
            raise PlanGateError(f"line {line_number}: invalid single-quoted scalar")
        return value[1:-1].replace("''", "'")
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    if lowered in {"null", "~"}:
        return None
    if re.fullmatch(r"-?(?:0|[1-9][0-9]*)", value):
        return int(value)
    return value



def load_safe_yaml(text: str) -> dict[str, object]:
    """Parse the inert YAML subset used by manifests, including scalar lists."""

    lines: list[_YamlLine] = []
    for number, raw in enumerate(text.splitlines(), 1):
        if "\t" in raw:
            raise PlanGateError(f"line {number}: tabs are forbidden")
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if re.search(r"\s+#", raw):
            raise PlanGateError(f"line {number}: inline comments are forbidden")
        indentation = len(raw) - len(raw.lstrip(" "))
        lines.append(_YamlLine(indentation, raw[indentation:].rstrip(), number))
    if not lines:
        raise PlanGateError("manifest is empty")

    def parse_block(index: int, indentation: int) -> tuple[object, int]:
        if lines[index].indentation != indentation:
            raise PlanGateError(
                f"line {lines[index].number}: inconsistent indentation"
            )
        is_sequence = lines[index].content == "-" or lines[index].content.startswith("- ")
        if is_sequence:
            values: list[object] = []
            while index < len(lines) and lines[index].indentation == indentation:
                line = lines[index]
                if not (line.content == "-" or line.content.startswith("- ")):
                    raise PlanGateError(
                        f"line {line.number}: cannot mix mappings and sequences"
                    )
                item = line.content[1:].strip()
                if not item:
                    raise PlanGateError(
                        f"line {line.number}: nested sequence items are unsupported"
                    )
                values.append(_parse_scalar(item, line.number))
                index += 1
                if index < len(lines) and lines[index].indentation > indentation:
                    raise PlanGateError(
                        f"line {lines[index].number}: scalar sequence item has children"
                    )
            return values, index

        values_map: dict[str, object] = {}
        while index < len(lines) and lines[index].indentation == indentation:
            line = lines[index]
            if line.content == "-" or line.content.startswith("- "):
                raise PlanGateError(
                    f"line {line.number}: cannot mix mappings and sequences"
                )
            if ":" not in line.content:
                raise PlanGateError(f"line {line.number}: expected mapping entry")
            key, raw_value = line.content.split(":", 1)
            key = key.strip()
            if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.-]*", key) or key == "<<":
                raise PlanGateError(f"line {line.number}: invalid mapping key")
            if key in values_map:
                raise PlanGateError(f"line {line.number}: duplicate key {key!r}")
            raw_value = raw_value.strip()
            index += 1
            if raw_value:
                values_map[key] = _parse_scalar(raw_value, line.number)
                if index < len(lines) and lines[index].indentation > indentation:
                    raise PlanGateError(
                        f"line {lines[index].number}: scalar mapping value has children"
                    )
                continue
            if index >= len(lines) or lines[index].indentation <= indentation:
                values_map[key] = {}
            else:
                values_map[key], index = parse_block(
                    index, lines[index].indentation
                )
        return values_map, index

    if lines[0].indentation != 0:
        raise PlanGateError(f"line {lines[0].number}: root indentation must be zero")
    parsed, index = parse_block(0, 0)
    if index != len(lines) or not isinstance(parsed, dict):
        raise PlanGateError("manifest root must be one mapping")
    return parsed



def parse_front_matter(text: str) -> dict[str, object]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise PlanGateError("document is missing front matter")
    try:
        end = next(index for index, line in enumerate(lines[1:], 1) if line.strip() == "---")
    except StopIteration as error:
        raise PlanGateError("document front matter is not closed") from error
    metadata: dict[str, object] = {}
    for number, raw in enumerate(lines[1:end], 2):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if ":" not in raw:
            raise PlanGateError(f"front matter line {number}: expected key:value")
        key, value = raw.split(":", 1)
        key = key.strip()
        if key in metadata:
            raise PlanGateError(f"front matter line {number}: duplicate key {key!r}")
        value = value.strip()
        if value.startswith("[") and value.endswith("]"):
            metadata[key] = [
                item.strip().strip("'\"")
                for item in value[1:-1].split(",")
                if item.strip()
            ]
        else:
            metadata[key] = value.strip("'\"")
    return metadata



def _validate_path_rule(value: object, label: str) -> list[str]:
    if not isinstance(value, str) or not value:
        return [f"{label} must be a non-empty repository-relative path"]
    if "\\" in value:
        return [f"{label} must not contain backslashes"]
    prefix_rule = value.endswith("/**")
    raw = value[:-3] if prefix_rule else value[:-1] if value.endswith("/") else value
    if any(character in raw for character in "*?[]"):
        return [f"{label} supports only a terminal /** prefix rule"]
    path = PurePosixPath(raw)
    if path.is_absolute() or raw in {"", "."} or ".." in path.parts:
        return [f"{label} must be a normalized repository-relative path"]
    if path.as_posix() != raw:
        return [f"{label} must be normalized"]
    return []



def _path_matches(path: str, rule: str) -> bool:
    if rule.endswith("/**"):
        directory = rule[:-3]
        return path == directory or path.startswith(directory + "/")
    return path.startswith(rule) if rule.endswith("/") else path == rule



def validate_changed_paths(
    action: Mapping[str, object], changed_paths: Iterable[str]
) -> list[str]:
    """Apply allow/deny policy from the base action; deny always wins."""

    errors: list[str] = []
    allowed = action.get("allowed_change_paths")
    forbidden = action.get("forbidden_change_paths")
    if not isinstance(allowed, list) or not all(isinstance(item, str) for item in allowed):
        return ["base current_action.allowed_change_paths must be a scalar list"]
    if not isinstance(forbidden, list) or not all(
        isinstance(item, str) for item in forbidden
    ):
        return ["base current_action.forbidden_change_paths must be a scalar list"]
    coding_allowed = action.get("coding_allowed") is True
    for path in sorted(set(changed_paths)):
        errors.extend(_validate_path_rule(path, f"changed path {path!r}"))
        if not any(_path_matches(path, rule) for rule in allowed):
            errors.append(f"changed path is not allowed by the base action: {path}")
        if any(_path_matches(path, rule) for rule in forbidden):
            errors.append(f"changed path is forbidden by the base action: {path}")
        if not coding_allowed and _path_matches(path, "src/software_world_model/"):
            errors.append(f"base action does not authorize product code changes: {path}")
    return errors



def validate_bootstrap_paths(changed_paths: Iterable[str]) -> list[str]:
    return validate_changed_paths(
        {
            "coding_allowed": False,
            "allowed_change_paths": list(BOOTSTRAP_ALLOWED_PATHS),
            "forbidden_change_paths": list(BOOTSTRAP_FORBIDDEN_PATHS),
        },
        changed_paths,
    )



def _control(manifest: Mapping[str, object]) -> dict[str, object] | None:
    value = manifest.get("plan_execution_control")
    return value if isinstance(value, dict) else None



def _run_git(repository: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=repository,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if completed.returncode != 0:
        raise PlanGateError(
            f"git {' '.join(arguments)} failed: {completed.stderr.strip()}"
        )
    return completed.stdout



def _read_text(repository: Path, reference: str, path: str) -> str:
    if reference == "WORKTREE":
        return (repository / path).read_text(encoding="utf-8")
    return _run_git(repository, "show", f"{reference}:{path}")



def _active_manifest_path(current_metadata: Mapping[str, object]) -> str:
    active = str(current_metadata.get("active_iteration", ""))
    match = re.fullmatch(r"ITER-([0-9]{3,})-INDEX", active)
    if match is None:
        raise PlanGateError(
            "PROJECT-CURRENT active_iteration must be an exact ITER-NNN-INDEX ID"
        )
    return f"docs/project/iterations/iteration-{match.group(1)}/manifest.yaml"



def _changed_paths(repository: Path, base: str, target: str) -> list[str]:
    if target == "WORKTREE":
        tracked = _run_git(repository, "diff", "--name-only", base, "--")
        untracked = _run_git(
            repository, "ls-files", "--others", "--exclude-standard"
        )
        output = tracked + untracked
    else:
        output = _run_git(repository, "diff", "--name-only", base, target, "--")
    return sorted({line.strip() for line in output.splitlines() if line.strip()})



def _print_errors(errors: Sequence[str]) -> int:
    if errors:
        for error in sorted(set(errors)):
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("plan compliance check passed")
    return 0





GOVERNANCE_KIND = "governance"
SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_\-]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"gh[pousr]_[A-Za-z0-9]{30,}"),
    re.compile(
        r"(?i)(?:api[_-]?key|secret|password|token)\s*[:=]\s*['\"][A-Za-z0-9_\-+/=]{20,}['\"]"
    ),
)


def validate_snapshot(manifest: Mapping[str, object]) -> list[str]:
    """Validate only the fields this gate enforces."""

    control = _control(manifest)
    if control is None:
        return ["manifest has no plan_execution_control mapping"]
    action = control.get("current_action")
    if not isinstance(action, dict):
        return ["plan_execution_control.current_action must be a mapping"]
    errors: list[str] = []
    for field in ("id", "kind", "status"):
        if not isinstance(action.get(field), str) or not action.get(field):
            errors.append(f"current_action.{field} must be a non-empty string")
    for field in ("allowed_change_paths", "forbidden_change_paths"):
        rules = action.get(field)
        if not isinstance(rules, list) or not all(isinstance(item, str) for item in rules):
            errors.append(f"current_action.{field} must be a list of path rules")
            continue
        for rule in rules:
            errors.extend(_validate_path_rule(rule, f"current_action.{field} {rule!r}"))
    if not isinstance(action.get("coding_allowed"), bool):
        errors.append("current_action.coding_allowed must be a boolean")
    return errors


def find_secrets(added_lines: Iterable[tuple[str, str]]) -> list[str]:
    errors: list[str] = []
    for path, line in added_lines:
        for pattern in SECRET_PATTERNS:
            if pattern.search(line):
                errors.append(f"possible secret added in {path}: matches {pattern.pattern!r}")
                break
    return errors


def validate_transition(
    base_manifest: Mapping[str, object] | None,
    target_manifest: Mapping[str, object],
    changed_paths: Sequence[str],
    added_lines: Iterable[tuple[str, str]] = (),
) -> list[str]:
    """Validate one base-to-target change using only the base action's authority.

    Rules (governance policy "最小机械边界"):
    1. changed paths stay inside the base action's allow-list and outside its deny-list;
    2. gate files change only under a governance base action;
    3. the target keeps a well-formed plan_execution_control;
    4. no obvious secret is added.
    """

    errors = list(validate_snapshot(target_manifest))
    errors.extend(find_secrets(added_lines))
    base_control = _control(base_manifest) if base_manifest is not None else None
    if base_control is None:
        return sorted(set(errors + validate_bootstrap_paths(changed_paths)))
    base_action = base_control.get("current_action")
    if not isinstance(base_action, dict):
        return sorted(set(errors + ["base current_action must be a mapping"]))
    errors.extend(validate_changed_paths(base_action, changed_paths))
    protected = PROTECTED_GATE_PATHS.intersection(changed_paths)
    if protected and base_action.get("kind") != GOVERNANCE_KIND:
        errors.append(
            "gate files may change only under a governance base action: "
            + ", ".join(sorted(protected))
        )
    return sorted(set(errors))


def _manifest_at(
    repository: Path, reference: str, explicit_manifest: str | None
) -> dict[str, object] | None:
    try:
        current = parse_front_matter(_read_text(repository, reference, "docs/project/current.md"))
        path = explicit_manifest or _active_manifest_path(current)
        return load_safe_yaml(_read_text(repository, reference, path))
    except (OSError, UnicodeError, PlanGateError):
        return None


def _added_lines(repository: Path, base: str, target: str) -> list[tuple[str, str]]:
    if target == "WORKTREE":
        diff = _run_git(repository, "diff", "-U0", "--no-color", base, "--")
    else:
        diff = _run_git(repository, "diff", "-U0", "--no-color", base, target, "--")
    added: list[tuple[str, str]] = []
    path = ""
    for line in diff.splitlines():
        if line.startswith("+++ "):
            path = line[6:] if line.startswith("+++ b/") else line[4:]
        elif line.startswith("+") and not line.startswith("+++"):
            added.append((path, line[1:]))
    if target == "WORKTREE":
        untracked = _run_git(repository, "ls-files", "--others", "--exclude-standard")
        for relative in untracked.splitlines():
            try:
                text = (repository / relative).read_text(encoding="utf-8")
            except (OSError, UnicodeError):
                continue
            added.extend((relative, line) for line in text.splitlines())
    return added


def _argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, default=REPOSITORY)
    commands = parser.add_subparsers(dest="command", required=True)
    snapshot = commands.add_parser("snapshot")
    snapshot.add_argument("--manifest")
    diff = commands.add_parser("diff")
    diff.add_argument("--base", required=True)
    diff.add_argument(
        "--target",
        default="WORKTREE",
        help="candidate git ref or tree; defaults to the current worktree",
    )
    diff.add_argument("--manifest")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _argument_parser().parse_args(argv)
    repository = args.repository.resolve()
    try:
        if args.command == "snapshot":
            manifest = _manifest_at(repository, "WORKTREE", args.manifest)
            if manifest is None:
                return _print_errors(["cannot load the active manifest"])
            return _print_errors(validate_snapshot(manifest))
        target_manifest = _manifest_at(repository, args.target, args.manifest)
        if target_manifest is None:
            return _print_errors(["cannot load the target manifest"])
        return _print_errors(
            validate_transition(
                _manifest_at(repository, args.base, args.manifest),
                target_manifest,
                _changed_paths(repository, args.base, args.target),
                _added_lines(repository, args.base, args.target),
            )
        )
    except (OSError, UnicodeError, PlanGateError) as error:
        return _print_errors([str(error)])


if __name__ == "__main__":
    raise SystemExit(main())
