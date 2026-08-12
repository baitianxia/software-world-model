"""Run the ITER-005 pre-coding generalization gate through the public CLI.

This module deliberately imports no ``software_world_model`` package.  The
expected graph is a separately frozen, human-reviewable oracle; product code is
invoked only as an external CLI process.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Mapping, Sequence


PACKAGE_ROOT = Path(__file__).resolve().parent
DEFAULT_INPUTS = PACKAGE_ROOT / "g0_inputs.json"


class GateFailure(RuntimeError):
    """One frozen G0 assertion did not hold."""


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode(
        "utf-8"
    )


def _write_json(path: Path, value: object) -> None:
    path.write_bytes(_json_bytes(value))


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _run(arguments: Sequence[str], *, cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        tuple(arguments),
        cwd=cwd,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if check and completed.returncode != 0:
        raise GateFailure(
            f"command failed ({completed.returncode}): {' '.join(arguments)}\n"
            f"stdout={completed.stdout}\nstderr={completed.stderr}"
        )
    return completed


def _git(repository: Path, *arguments: str) -> str:
    return _run(("git", "-C", str(repository), *arguments), cwd=repository).stdout.strip()


def _load_json_output(completed: subprocess.CompletedProcess[str]) -> dict[str, Any]:
    try:
        value = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise GateFailure(
            f"CLI did not emit one JSON document: {error}; stdout={completed.stdout!r}; "
            f"stderr={completed.stderr!r}"
        ) from error
    if not isinstance(value, dict):
        raise GateFailure("CLI JSON result must be an object")
    return value


def _cli(workspace: Path, database: Path, arguments: Sequence[str]) -> subprocess.CompletedProcess[str]:
    environment = dict(os.environ)
    environment["PYTHONPATH"] = f"{workspace / 'src'}:{workspace}"
    return subprocess.run(
        (
            sys.executable,
            "-m",
            "software_world_model.interface.cli",
            "--database",
            str(database),
            *arguments,
        ),
        cwd=workspace,
        env=environment,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def _configure(
    *, workspace: Path, database: Path, case: Mapping[str, Any], result_dir: Path
) -> tuple[str, str, str]:
    case_id = str(case["case_id"])
    completed = _cli(
        workspace,
        database,
        (
            "configure-system-source",
            "--idempotency-key",
            f"iter-005-g0:{case_id}:configure",
            "--source-target",
            str((workspace / str(case["repository_path"])).resolve()),
            "--paths",
            ".",
            "--display-name",
            case_id,
            "--canonical-system-key",
            str(case["canonical_system_key"]),
            "--actor",
            "iter-005-g0",
            "--reason",
            "ITER-005 frozen generalization preflight",
            "--correlation-ref",
            f"iter-005-g0:{case_id}",
        ),
    )
    payload = _load_json_output(completed)
    _write_json(result_dir / "configure.json", payload)
    if completed.returncode != 0:
        raise GateFailure(f"{case_id}: source configuration failed: {payload}")
    steps = {item["name"]: item for item in payload.get("steps", [])}
    try:
        return (
            str(steps["CREATE_SCOPE"]["result_reference"]),
            str(steps["REGISTER_SOURCE"]["result_reference"]),
            str(steps["BIND_SOURCE"]["result_reference"]),
        )
    except (KeyError, TypeError) as error:
        raise GateFailure(f"{case_id}: incomplete configuration result") from error


def _build(
    *,
    workspace: Path,
    database: Path,
    case_id: str,
    root_pom: str,
    revision: str,
    scope_id: str,
    source_id: str,
    binding_id: str,
    idempotency_suffix: str,
    expected_current: str | None = None,
) -> subprocess.CompletedProcess[str]:
    arguments = [
        "build-maven-structure",
        "--scope-id",
        scope_id,
        "--scope-revision",
        "1",
        "--source-id",
        source_id,
        "--source-revision",
        "1",
        "--binding-id",
        binding_id,
        "--binding-revision",
        "1",
        "--repository-revision",
        revision,
        "--root-pom",
        root_pom,
        "--objective",
        f"ITER-005 G0 exact Maven structure for {case_id}",
        "--idempotency-key",
        f"iter-005-g0:{case_id}:{idempotency_suffix}",
        "--classification",
        "INTERNAL",
        "--actor-ref",
        "iter-005-g0",
        "--correlation-ref",
        f"iter-005-g0:{case_id}:{idempotency_suffix}",
        "--max-poms",
        "256",
        "--max-calls",
        "512",
        "--tree-page-size",
        "500",
        "--max-bytes-per-call",
        "1000000",
    ]
    if expected_current is not None:
        arguments.extend(("--expected-current-snapshot-id", expected_current))
    return _cli(workspace, database, arguments)


def _ga(entity: Mapping[str, Any]) -> str:
    root_fields = entity["root_fields"]
    return f"{root_fields['effective_group_id']}:{root_fields['artifact_id']}"


def _module_projection(payload: Mapping[str, Any]) -> set[tuple[str, str, str, str, str]]:
    projected: set[tuple[str, str, str, str, str]] = set()
    for entity in payload["entities"]:
        if entity["entity_type"] != "MAVEN_MODULE":
            continue
        root_fields = entity["root_fields"]
        state_fields = entity["state_fields"]
        projected.add(
            (
                str(root_fields["effective_group_id"]),
                str(root_fields["artifact_id"]),
                str(state_fields["effective_version"]),
                str(state_fields["module_path"]),
                str(state_fields["packaging"]),
            )
        )
    return projected


def _dependency_projection(payload: Mapping[str, Any]) -> set[tuple[str, str]]:
    identities = {
        str(entity["root_id"]): _ga(entity)
        for entity in payload["entities"]
        if entity["entity_type"] == "MAVEN_MODULE"
    }
    projected: set[tuple[str, str]] = set()
    for relation in payload["relations"]:
        if relation["predicate"] != "DEPENDS_ON":
            continue
        try:
            projected.add(
                (
                    identities[str(relation["source_root_id"])],
                    identities[str(relation["target_root_id"])],
                )
            )
        except KeyError as error:
            raise GateFailure("DEPENDS_ON relation has a non-module endpoint") from error
    return projected


def _expected_modules(oracle: Mapping[str, Any]) -> set[tuple[str, str, str, str, str]]:
    return {
        (
            str(item["group_id"]),
            str(item["artifact_id"]),
            str(item["version"]),
            str(item["path"]),
            str(item["packaging"]),
        )
        for item in oracle["modules"]
    }


def _expected_edges(oracle: Mapping[str, Any], field: str) -> set[tuple[str, str]]:
    return {(str(item["consumer"]), str(item["target"])) for item in oracle[field]}


def _assert_graph(case_id: str, payload: Mapping[str, Any], oracle: Mapping[str, Any]) -> dict[str, Any]:
    if payload.get("attempt", {}).get("state") != "PUBLISHED":
        raise GateFailure(f"{case_id}: attempt was not PUBLISHED")
    if payload.get("result", {}).get("state") != "PUBLISHED":
        raise GateFailure(f"{case_id}: result was not PUBLISHED")
    if payload.get("coverage", {}).get("completeness") != "COMPLETE":
        raise GateFailure(f"{case_id}: coverage was not COMPLETE")

    systems = [item for item in payload["entities"] if item["entity_type"] == "SOFTWARE_SYSTEM"]
    if len(systems) != 1:
        raise GateFailure(f"{case_id}: expected exactly one SOFTWARE_SYSTEM")
    root = oracle["root"]
    system_state = systems[0]["state_fields"]
    actual_root = (
        system_state["effective_group_id"],
        system_state["artifact_id"],
        system_state["effective_version"],
        system_state["packaging"],
    )
    expected_root = (
        root["group_id"],
        root["artifact_id"],
        root["version"],
        root["packaging"],
    )
    if actual_root != expected_root:
        raise GateFailure(f"{case_id}: root mismatch: {actual_root!r} != {expected_root!r}")

    modules = _module_projection(payload)
    expected_modules = _expected_modules(oracle)
    if modules != expected_modules:
        raise GateFailure(
            f"{case_id}: module mismatch; missing={sorted(expected_modules - modules)!r}; "
            f"extra={sorted(modules - expected_modules)!r}"
        )
    dependencies = _dependency_projection(payload)
    expected_dependencies = _expected_edges(oracle, "internal_dependencies")
    if dependencies != expected_dependencies:
        raise GateFailure(
            f"{case_id}: dependency mismatch; missing={sorted(expected_dependencies - dependencies)!r}; "
            f"extra={sorted(dependencies - expected_dependencies)!r}"
        )
    forbidden = _expected_edges(oracle, "absent_dependencies")
    present_forbidden = forbidden & dependencies
    if present_forbidden:
        raise GateFailure(f"{case_id}: absence oracle violated: {sorted(present_forbidden)!r}")

    contains = [item for item in payload["relations"] if item["predicate"] == "CONTAINS_MODULE"]
    if len(contains) != len(expected_modules):
        raise GateFailure(f"{case_id}: recursive reactor membership count mismatch")
    return {
        "case_id": case_id,
        "status": "PASS",
        "snapshot_id": payload["snapshot"]["snapshot_id"],
        "snapshot_manifest_digest": payload["snapshot"]["manifest_digest"],
        "coverage_state_digest": payload["coverage"]["state_digest"],
        "modules": len(modules),
        "contains_relations": len(contains),
        "dependency_relations": len(dependencies),
        "absence_checks": len(forbidden),
        "source_operations": payload["source_operations"]["count"],
    }


def _verify_repository(workspace: Path, case: Mapping[str, Any], revisions: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    repository = workspace / str(case["repository_path"])
    if not (repository / ".git").is_dir():
        raise GateFailure(f"missing independent Git repository: {repository}")
    actual_remote = _git(repository, "remote", "get-url", "origin")
    if actual_remote != case["remote"]:
        raise GateFailure(f"{case['case_id']}: remote mismatch: {actual_remote!r}")
    if _git(repository, "status", "--porcelain"):
        raise GateFailure(f"{case['case_id']}: validation repository is dirty")
    verified = []
    for item in revisions:
        commit = str(item["commit"])
        actual_commit = _git(repository, "rev-parse", f"{commit}^{{commit}}")
        actual_tree = _git(repository, "rev-parse", f"{commit}^{{tree}}")
        if actual_commit != commit or actual_tree != item["tree"]:
            raise GateFailure(f"{case['case_id']}: exact Git identity mismatch for {commit}")
        verified.append({"commit": actual_commit, "tree": actual_tree})
    return {
        "case_id": case["case_id"],
        "repository_path": case["repository_path"],
        "remote": actual_remote,
        "revisions": verified,
    }


def _open_current(
    *, workspace: Path, database: Path, case_id: str, scope_id: str, suffix: str
) -> dict[str, Any]:
    task_suffix = hashlib.sha256(f"{case_id}:{suffix}".encode()).hexdigest()[:32]
    completed = _cli(
        workspace,
        database,
        (
            "open-structure-read-session",
            "--scope-id",
            scope_id,
            "--scope-revision",
            "1",
            "--task-id",
            f"task_{task_suffix}",
            "--task-revision",
            "1",
            "--caller-ref",
            "iter-005-g0",
            "--classification",
            "INTERNAL",
            "--idempotency-key",
            f"iter-005-g0:{case_id}:current:{suffix}",
            "--current",
        ),
    )
    payload = _load_json_output(completed)
    if completed.returncode != 0:
        raise GateFailure(f"{case_id}: CURRENT read failed: {payload}")
    return payload


def _run_supported(workspace: Path, result_root: Path, case: Mapping[str, Any]) -> dict[str, Any]:
    case_id = str(case["case_id"])
    case_dir = result_root / case_id.lower()
    case_dir.mkdir()
    database = case_dir / "swm.sqlite3"
    scope_id, source_id, binding_id = _configure(
        workspace=workspace, database=database, case=case, result_dir=case_dir
    )
    completed = _build(
        workspace=workspace,
        database=database,
        case_id=case_id,
        root_pom=str(case["root_pom"]),
        revision=str(case["commit"]),
        scope_id=scope_id,
        source_id=source_id,
        binding_id=binding_id,
        idempotency_suffix="build",
    )
    payload = _load_json_output(completed)
    _write_json(case_dir / "build.json", payload)
    if completed.returncode != 0:
        raise GateFailure(f"{case_id}: supported build was rejected: {payload}")
    return _assert_graph(case_id, payload, case)


def _run_unsupported_sequence(
    workspace: Path, result_root: Path, case: Mapping[str, Any]
) -> dict[str, Any]:
    case_id = str(case["case_id"])
    case_dir = result_root / case_id.lower()
    case_dir.mkdir()
    database = case_dir / "swm.sqlite3"
    scope_id, source_id, binding_id = _configure(
        workspace=workspace, database=database, case=case, result_dir=case_dir
    )
    valid = case["valid"]
    valid_completed = _build(
        workspace=workspace,
        database=database,
        case_id=case_id,
        root_pom=str(case["root_pom"]),
        revision=str(valid["commit"]),
        scope_id=scope_id,
        source_id=source_id,
        binding_id=binding_id,
        idempotency_suffix="valid",
    )
    valid_payload = _load_json_output(valid_completed)
    _write_json(case_dir / "valid-build.json", valid_payload)
    if valid_completed.returncode != 0:
        raise GateFailure(f"{case_id}: valid baseline was rejected: {valid_payload}")
    valid_summary = _assert_graph(case_id + "_VALID", valid_payload, valid)
    snapshot_id = str(valid_payload["snapshot"]["snapshot_id"])
    before = _open_current(
        workspace=workspace,
        database=database,
        case_id=case_id,
        scope_id=scope_id,
        suffix="before",
    )
    _write_json(case_dir / "current-before.json", before)

    unsupported = case["unsupported"]
    rejected_completed = _build(
        workspace=workspace,
        database=database,
        case_id=case_id,
        root_pom=str(case["root_pom"]),
        revision=str(unsupported["commit"]),
        scope_id=scope_id,
        source_id=source_id,
        binding_id=binding_id,
        idempotency_suffix="unsupported",
        expected_current=snapshot_id,
    )
    rejected_payload = _load_json_output(rejected_completed)
    _write_json(case_dir / "unsupported-build.json", rejected_payload)
    if rejected_completed.returncode == 0:
        raise GateFailure(f"{case_id}: unsupported revision was accepted")
    if rejected_payload.get("error") != unsupported["error"]:
        raise GateFailure(f"{case_id}: wrong rejection code: {rejected_payload}")
    if str(unsupported["message_contains"]) not in str(rejected_payload.get("message", "")):
        raise GateFailure(f"{case_id}: wrong rejection reason: {rejected_payload}")

    after = _open_current(
        workspace=workspace,
        database=database,
        case_id=case_id,
        scope_id=scope_id,
        suffix="after",
    )
    _write_json(case_dir / "current-after.json", after)
    before_ids = [item["snapshot_id"] for item in before["snapshots"]]
    after_ids = [item["snapshot_id"] for item in after["snapshots"]]
    if before_ids != [snapshot_id] or after_ids != [snapshot_id]:
        raise GateFailure(
            f"{case_id}: CURRENT moved across rejected revision: before={before_ids}, after={after_ids}"
        )
    return {
        "case_id": case_id,
        "status": "PASS",
        "valid": valid_summary,
        "unsupported_commit": unsupported["commit"],
        "rejection_error": rejected_payload["error"],
        "rejection_message": rejected_payload["message"],
        "current_before": before_ids[0],
        "current_after": after_ids[0],
        "current_unchanged": True,
    }


def _report_markdown(report: Mapping[str, Any]) -> str:
    rows = [
        "| Case | Exact revision | Expected | Outcome | Graph / rejection evidence |",
        "|---|---|---|---|---|",
    ]
    for item in report["supported"]:
        rows.append(
            f"| `{item['case_id']}` | `{item['commit']}` | COMPLETE | PASS | "
            f"{item['modules']} modules; {item['dependency_relations']} direct internal edges; "
            f"{item['absence_checks']} absence checks |"
        )
    rejected = report["unsupported_sequence"]
    rows.append(
        f"| `{rejected['case_id']}` | `{rejected['valid_commit']}` → "
        f"`{rejected['unsupported_commit']}` | valid COMPLETE, then explicit rejection | PASS | "
        f"`{rejected['rejection_error']}`; CURRENT unchanged at "
        f"`{rejected['current_after']}` |"
    )
    return "\n".join(
        (
            "# ITER-005 G0 compatibility report",
            "",
            f"Overall: **{report['status']}**",
            "",
            *rows,
            "",
            "The oracle is static, human-reviewable, and imported no product package. "
            "The system under test was invoked only through "
            "`software_world_model.interface.cli` in a subprocess.",
            "",
            "Profile boundary retained: Maven reactor membership, POM-local direct internal "
            "dependencies, and exact Snapshot identity only. The rejected `type=pom` internal "
            "dependency was not guessed or weakened.",
            "",
        )
    )


def run(*, workspace: Path, result_directory: Path, inputs_path: Path = DEFAULT_INPUTS) -> dict[str, Any]:
    workspace = workspace.resolve()
    result_directory = result_directory.resolve()
    if result_directory.exists() and any(result_directory.iterdir()):
        raise GateFailure(f"result directory must be absent or empty: {result_directory}")
    result_directory.mkdir(parents=True, exist_ok=True)
    inputs = json.loads(inputs_path.read_text(encoding="utf-8"))
    _write_json(result_directory / "frozen-inputs.json", inputs)

    baseline = inputs["product_baseline"]
    actual_commit = _git(workspace, "rev-parse", "HEAD")
    actual_tree = _git(workspace, "rev-parse", "HEAD^{tree}")
    if actual_commit != baseline["commit"] or actual_tree != baseline["tree"]:
        raise GateFailure(
            f"product baseline mismatch: {(actual_commit, actual_tree)!r} != "
            f"{(baseline['commit'], baseline['tree'])!r}"
        )
    tracked_product_changes = _git(
        workspace,
        "status",
        "--porcelain",
        "--untracked-files=no",
        "--",
        "src/software_world_model",
        "tests",
    )
    if tracked_product_changes:
        raise GateFailure(f"tracked product/test changes precede G0: {tracked_product_changes}")

    repository_checks = []
    for case in inputs["supported_cases"]:
        repository_checks.append(_verify_repository(workspace, case, (case,)))
    sequence = inputs["unsupported_sequence"]
    repository_checks.append(
        _verify_repository(workspace, sequence, (sequence["valid"], sequence["unsupported"]))
    )
    _write_json(result_directory / "repository-identities.json", repository_checks)

    supported = []
    for case in inputs["supported_cases"]:
        summary = _run_supported(workspace, result_directory, case)
        summary["commit"] = case["commit"]
        summary["tree"] = case["tree"]
        supported.append(summary)
    sequence_summary = _run_unsupported_sequence(workspace, result_directory, sequence)
    sequence_summary["valid_commit"] = sequence["valid"]["commit"]
    sequence_summary["valid_tree"] = sequence["valid"]["tree"]
    sequence_summary["unsupported_tree"] = sequence["unsupported"]["tree"]

    report = {
        "schema": "ITER-005-G0-REPORT@1",
        "status": "PASS",
        "product_baseline": baseline,
        "oracle": {
            "path": str(inputs_path.relative_to(workspace)),
            "digest": _sha256(inputs_path),
            "imports_product_code": False,
        },
        "repository_checks": repository_checks,
        "supported": supported,
        "unsupported_sequence": sequence_summary,
        "gate_decision": "PROCEED_TO_SLICE_001_AUTHORIZATION",
    }
    _write_json(result_directory / "report.json", report)
    (result_directory / "report.md").write_text(_report_markdown(report), encoding="utf-8")
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run ITER-005 G0 generalization preflight")
    parser.add_argument("--workspace-root", type=Path, default=Path.cwd())
    parser.add_argument("--result-directory", type=Path, required=True)
    parser.add_argument("--inputs", type=Path, default=DEFAULT_INPUTS)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    try:
        report = run(
            workspace=arguments.workspace_root,
            result_directory=arguments.result_directory,
            inputs_path=arguments.inputs.resolve(),
        )
    except GateFailure as error:
        print(json.dumps({"status": "FAIL", "message": str(error)}, ensure_ascii=False))
        return 1
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
