"""Produce the human-reviewable ITER-005 SLICE-001 acceptance evidence.

The runner deliberately imports no ``software_world_model`` package.  It
generates a randomized Maven repository, invokes only the public management and
Source-off CLIs, and evaluates the returned documents with an independent
stdlib-only oracle.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import secrets
import shutil
import sqlite3
import stat
import subprocess
import sys
from typing import Any, Iterable, Mapping, Sequence


class GateFailure(RuntimeError):
    """One required SLICE-001 observation did not hold."""


def _json_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_json_bytes(value))


def _sha256_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _sha256(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _run(
    arguments: Sequence[str],
    *,
    cwd: Path,
    environment: Mapping[str, str] | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        tuple(arguments),
        cwd=cwd,
        env=dict(environment) if environment is not None else None,
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


class PublicCli:
    def __init__(
        self,
        *,
        workspace: Path,
        database: Path,
        bundle_root: Path,
        catalog_root: Path,
        producer_commit: str,
        producer_tree: str,
        raw_dir: Path,
    ) -> None:
        self.workspace = workspace
        self.database = database
        self.bundle_root = bundle_root
        self.catalog_root = catalog_root
        self.producer_commit = producer_commit
        self.producer_tree = producer_tree
        self.raw_dir = raw_dir
        self.commands: list[dict[str, object]] = []
        self.environment = dict(os.environ)
        self.environment["PYTHONPATH"] = f"{workspace / 'src'}:{workspace}"

    def management(
        self,
        name: str,
        arguments: Sequence[str],
        *,
        expect: int = 0,
    ) -> dict[str, Any]:
        command = (
            sys.executable,
            "-m",
            "software_world_model.interface.cli",
            "--database",
            str(self.database),
            "--bundle-root",
            str(self.bundle_root),
            "--catalog-root",
            str(self.catalog_root),
            "--producer-commit",
            self.producer_commit,
            "--producer-tree",
            self.producer_tree,
            *arguments,
        )
        return self._invoke(name, command, expect=expect, payload_stream="stdout")

    def source_off(
        self,
        name: str,
        arguments: Sequence[str],
        *,
        expect: int = 0,
        catalog_root: Path | None = None,
        bundle_root: Path | None = None,
    ) -> dict[str, Any]:
        command = (
            sys.executable,
            "-m",
            "software_world_model.interface.read_set_catalog_cli",
            "--catalog-root",
            str(catalog_root or self.catalog_root),
            "--bundle-root",
            str(bundle_root or self.bundle_root),
            *arguments,
        )
        return self._invoke(
            name,
            command,
            expect=expect,
            payload_stream="stdout" if expect == 0 else "stderr",
        )

    def _invoke(
        self,
        name: str,
        command: Sequence[str],
        *,
        expect: int,
        payload_stream: str,
    ) -> dict[str, Any]:
        completed = _run(
            command,
            cwd=self.workspace,
            environment=self.environment,
            check=False,
        )
        record = {
            "name": name,
            "argv": list(command),
            "exit_code": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        }
        self.commands.append(record)
        if completed.returncode != expect:
            raise GateFailure(
                f"{name}: expected exit {expect}, got {completed.returncode}; "
                f"stdout={completed.stdout!r}; stderr={completed.stderr!r}"
            )
        encoded = completed.stdout if payload_stream == "stdout" else completed.stderr
        try:
            payload = json.loads(encoded)
        except json.JSONDecodeError as error:
            raise GateFailure(f"{name}: CLI did not emit one JSON document") from error
        if not isinstance(payload, dict):
            raise GateFailure(f"{name}: CLI JSON result is not an object")
        _write_json(self.raw_dir / f"{name}.json", payload)
        return payload


def _product_snapshot(workspace: Path, destination: Path) -> dict[str, str]:
    source = workspace / "src"
    target = destination / "src"
    shutil.copytree(
        source,
        target,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
    )
    shutil.copy2(workspace / "pyproject.toml", destination / "pyproject.toml")
    original = _source_manifest((source, workspace / "pyproject.toml"), workspace)
    copied = _source_manifest((target, destination / "pyproject.toml"), destination)
    if original != copied:
        raise GateFailure("isolated producer snapshot differs from executed product source")
    _git(destination, "init", "-q")
    _git(destination, "config", "user.email", "iter005-validation@example.invalid")
    _git(destination, "config", "user.name", "ITER-005 Validation")
    _git(destination, "add", "src", "pyproject.toml")
    _git(destination, "commit", "-q", "-m", "freeze SLICE-001 product source")
    return {
        "commit": _git(destination, "rev-parse", "HEAD"),
        "tree": _git(destination, "rev-parse", "HEAD^{tree}"),
        "source_manifest_digest": _sha256_bytes(_json_bytes(original)),
    }


def _source_manifest(paths: Iterable[Path], root: Path) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    for path in paths:
        files = sorted(path.rglob("*")) if path.is_dir() else [path]
        for file in files:
            if file.is_file() and "__pycache__" not in file.parts and file.suffix not in {".pyc", ".pyo"}:
                result.append(
                    {
                        "path": file.relative_to(root).as_posix(),
                        "sha256": _sha256(file),
                    }
                )
    return result


def _root_pom(group: str, artifact: str, version: str, modules: Sequence[str]) -> str:
    module_xml = "".join(f"<module>{item}</module>" for item in modules)
    return f"""\
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>{group}</groupId>
  <artifactId>{artifact}</artifactId>
  <version>{version}</version>
  <packaging>pom</packaging>
  <modules>{module_xml}</modules>
</project>
"""


def _module_pom(
    group: str,
    root_artifact: str,
    artifact: str,
    version: str,
    dependencies: Sequence[str],
) -> str:
    dependencies_xml = "".join(
        f"""
    <dependency>
      <groupId>{group}</groupId>
      <artifactId>{dependency}</artifactId>
      <version>{version}</version>
    </dependency>"""
        for dependency in dependencies
    )
    dependency_block = (
        f"\n  <dependencies>{dependencies_xml}\n  </dependencies>"
        if dependencies
        else ""
    )
    return f"""\
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <parent>
    <groupId>{group}</groupId>
    <artifactId>{root_artifact}</artifactId>
    <version>{version}</version>
    <relativePath>../pom.xml</relativePath>
  </parent>
  <artifactId>{artifact}</artifactId>{dependency_block}
</project>
"""


def _write_revision(
    repository: Path,
    *,
    group: str,
    root_artifact: str,
    version: str,
    modules: Sequence[tuple[str, str, Sequence[str]]],
) -> None:
    active_paths = {path for path, _artifact, _dependencies in modules}
    for existing in repository.iterdir():
        if existing.is_dir() and existing.name != ".git" and existing.name not in active_paths:
            shutil.rmtree(existing)
    (repository / "pom.xml").write_text(
        _root_pom(group, root_artifact, version, tuple(path for path, _a, _d in modules)),
        encoding="utf-8",
    )
    for module_path, artifact, dependencies in modules:
        directory = repository / module_path
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "pom.xml").write_text(
            _module_pom(group, root_artifact, artifact, version, dependencies),
            encoding="utf-8",
        )


def _commit(repository: Path, message: str) -> str:
    _git(repository, "add", "-A")
    _git(repository, "commit", "-q", "-m", message)
    return _git(repository, "rev-parse", "HEAD")


def _entity(payload: Mapping[str, Any], entity_type: str, artifact: str | None = None) -> Mapping[str, Any]:
    matches = [
        item
        for item in payload["snapshot_owner_result"]["entities"]
        if item["entity_type"] == entity_type
        and (artifact is None or item["root_fields"].get("artifact_id") == artifact)
    ]
    if len(matches) != 1:
        raise GateFailure(f"expected one {entity_type}/{artifact}, found {len(matches)}")
    return matches[0]


def _assert_update(
    payload: Mapping[str, Any],
    *,
    revision: str,
    module_artifacts: Sequence[str],
) -> None:
    if payload.get("workflow") != "MAVEN_WORKSPACE_FULL_REBUILD@1":
        raise GateFailure("Workspace update did not disclose FULL_REBUILD")
    if payload.get("manual_zero_question_update") is not True:
        raise GateFailure("Workspace update did not disclose zero-question execution")
    if payload["attempt"]["state"] != "SUCCEEDED":
        raise GateFailure("Workspace Attempt did not succeed")
    if payload["version"]["repository_revision"] != revision:
        raise GateFailure("Workspace Version did not seal the exact Git revision")
    if payload["version"]["availability"] != "QUERYABLE":
        raise GateFailure("successful Workspace Version is not queryable")
    owner = payload["snapshot_owner_result"]
    if owner["coverage"]["completeness"] != "COMPLETE":
        raise GateFailure("Maven Structure Coverage is not COMPLETE")
    actual_modules = sorted(
        item["root_fields"]["artifact_id"]
        for item in owner["entities"]
        if item["entity_type"] == "MAVEN_MODULE"
    )
    if actual_modules != sorted(module_artifacts):
        raise GateFailure(f"module oracle mismatch: {actual_modules!r}")
    metrics = payload.get("execution_metrics")
    if not isinstance(metrics, dict) or metrics["source_calls"] <= 0 or metrics["source_bytes"] <= 0:
        raise GateFailure("Workspace update omitted positive Source call/byte metrics")
    if metrics["snapshot_elapsed_milliseconds"] < 0:
        raise GateFailure("Workspace elapsed time is negative")


def _zero_question_counts(database: Path) -> dict[str, object]:
    with sqlite3.connect(database) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        named: dict[str, int | str] = {}
        for name in (
            "app_questions",
            "app_tasks",
            "app_structure_read_sessions",
            "app_snapshot_read_sessions",
        ):
            named[name] = (
                connection.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0]
                if name in tables
                else "TABLE_ABSENT"
            )
    if any(value not in {0, "TABLE_ABSENT"} for value in named.values()):
        raise GateFailure(f"zero-question precondition failed: {named}")
    return {"captured_before_first_update": True, "counts": named}


def _current_snapshot(database: Path, scope_id: str) -> str:
    with sqlite3.connect(database) as connection:
        row = connection.execute(
            "SELECT current_snapshot_id FROM knw_structure_snapshot_roots WHERE scope_id = ?",
            (scope_id,),
        ).fetchone()
    if row is None:
        raise GateFailure("Workspace Scope has no CURRENT Snapshot")
    return str(row[0])


def _collect_keys(value: object) -> set[str]:
    result: set[str] = set()
    if isinstance(value, dict):
        result.update(str(key) for key in value)
        for nested in value.values():
            result.update(_collect_keys(nested))
    elif isinstance(value, list):
        for nested in value:
            result.update(_collect_keys(nested))
    return result


def _catalog_path(root: Path) -> tuple[Path, dict[str, Any]]:
    pointer = json.loads((root / "current.json").read_text(encoding="utf-8"))
    digest = str(pointer["catalog_digest"]).split(":", 1)[1]
    path = (
        root
        / "manifests"
        / str(pointer["catalog_id"])
        / f"{int(pointer['revision']):020d}-{digest}.json"
    )
    return path, pointer


def _graph_markdown(name: str, update: Mapping[str, Any]) -> str:
    owner = update["snapshot_owner_result"]
    identities = {
        item["root_id"]: item["root_fields"].get("artifact_id", item["root_id"])
        for item in owner["entities"]
    }
    nodes = []
    for index, item in enumerate(owner["entities"]):
        label = identities[item["root_id"]].replace('"', "'")
        nodes.append(f'  n{index}["{label}"]')
    node_ids = {item["root_id"]: f"n{index}" for index, item in enumerate(owner["entities"])}
    edges = [
        f'  {node_ids[item["source_root_id"]]} -->|"{item["predicate"]}"| {node_ids[item["target_root_id"]]}'
        for item in owner["relations"]
        if item["source_root_id"] in node_ids and item["target_root_id"] in node_ids
    ]
    return f"## {name}\n\n```mermaid\ngraph TD\n" + "\n".join(nodes + edges) + "\n```\n"


def _tamper_cases(cli: PublicCli, result_dir: Path) -> list[dict[str, object]]:
    cases: list[dict[str, object]] = []

    def prepare(name: str) -> tuple[Path, Path]:
        case_root = result_dir / "tamper" / name
        catalog = case_root / "catalog"
        bundles = case_root / "bundles"
        shutil.copytree(cli.catalog_root, catalog)
        shutil.copytree(cli.bundle_root, bundles, symlinks=True)
        return catalog, bundles

    for name in ("catalog", "receipt", "locator", "pointer", "bundle", "extra-file", "symlink"):
        catalog, bundles = prepare(name)
        manifest, pointer = _catalog_path(catalog)
        document = json.loads(manifest.read_text(encoding="utf-8"))
        if name == "catalog":
            document["producer_commit"] = "f" * 40
            manifest.write_bytes(_canonical_json_bytes(document))
        elif name == "receipt":
            document["entries"][0]["ordered_receipt"]["receipt_id"] = (
                "read_bundle_receipt_" + "f" * 32
            )
            manifest.write_bytes(_canonical_json_bytes(document))
        elif name == "locator":
            document["entries"][0]["bundle_locator"] = "../outside"
            manifest.write_bytes(_canonical_json_bytes(document))
        elif name == "pointer":
            pointer["catalog_digest"] = "sha256:" + "0" * 64
            (catalog / "current.json").write_bytes(_canonical_json_bytes(pointer))
        else:
            entry = document["entries"][0]
            if name == "bundle":
                locator = next(
                    item["locator"]
                    for item in entry["file_manifest"]
                    if item["role"] == "SNAPSHOT"
                )
                path = bundles / locator
                path.write_bytes(path.read_bytes() + b" ")
            elif name == "extra-file":
                (bundles / entry["bundle_locator"] / "extra.json").write_text(
                    "{}", encoding="utf-8"
                )
            else:
                directory = bundles / entry["bundle_locator"]
                target = next(path for path in directory.iterdir() if path.is_file())
                (directory / "linked.json").symlink_to(target)
        rejected = cli.source_off(
            f"tamper-{name}",
            ("verify-current",),
            expect=2,
            catalog_root=catalog,
            bundle_root=bundles,
        )
        cases.append(
            {
                "case": name,
                "result": "REJECTED",
                "error": rejected.get("error"),
                "reason_code": rejected.get("details", {}).get("reason_code"),
                "raw": f"raw/tamper-{name}.json",
            }
        )
    return cases


def run(*, workspace: Path, result_dir: Path) -> dict[str, object]:
    if result_dir.exists():
        raise GateFailure(f"result directory already exists: {result_dir}")
    result_dir.mkdir(parents=True)
    raw_dir = result_dir / "raw"
    raw_dir.mkdir()
    suffix = secrets.token_hex(4)
    group = f"org.iter005.{suffix}"
    root_artifact = f"atlas-{suffix}"
    core_artifact = f"core-{suffix}"
    api_artifact = f"api-{suffix}"
    cli_artifact = f"cli-{suffix}"
    worker_artifact = f"worker-{suffix}"
    core_path = f"m-{secrets.token_hex(3)}"
    api_path = f"m-{secrets.token_hex(3)}"
    cli_path = f"m-{secrets.token_hex(3)}"
    worker_path = f"m-{secrets.token_hex(3)}"

    producer = _product_snapshot(workspace, result_dir / "producer-source")
    repository = result_dir / "source-repository"
    repository.mkdir()
    _git(repository, "init", "-q")
    _git(repository, "config", "user.email", "iter005-fixture@example.invalid")
    _git(repository, "config", "user.name", "ITER-005 Metamorphic Fixture")
    _write_revision(
        repository,
        group=group,
        root_artifact=root_artifact,
        version="1.0.0",
        modules=(
            (core_path, core_artifact, ()),
            (api_path, api_artifact, (core_artifact,)),
            (cli_path, cli_artifact, (api_artifact,)),
        ),
    )
    r1 = _commit(repository, "R1: three-module chain")
    _write_revision(
        repository,
        group=group,
        root_artifact=root_artifact,
        version="2.0.0",
        modules=(
            (core_path, core_artifact, ()),
            (api_path, api_artifact, (core_artifact,)),
        ),
    )
    r2 = _commit(repository, "R2: remove terminal CLI module")
    _write_revision(
        repository,
        group=group,
        root_artifact=root_artifact,
        version="3.0.0",
        modules=(
            (core_path, core_artifact, ()),
            (api_path, api_artifact, (core_artifact,)),
            (worker_path, worker_artifact, (core_artifact,)),
        ),
    )
    r3 = _commit(repository, "R3: add recovery probe module")

    database = result_dir / "authority.sqlite3"
    bundles = result_dir / "bundles"
    catalog = result_dir / "catalog"
    cli = PublicCli(
        workspace=workspace,
        database=database,
        bundle_root=bundles,
        catalog_root=catalog,
        producer_commit=producer["commit"],
        producer_tree=producer["tree"],
        raw_dir=raw_dir,
    )
    registration = cli.management(
        "workspace-register",
        (
            "register-maven-workspace",
            "--idempotency-key",
            f"iter005:{suffix}:workspace",
            "--source-target",
            str(repository),
            "--display-name",
            f"ITER-005 Metamorphic {suffix}",
            "--canonical-system-key",
            f"iter005:{suffix}:main",
            "--root-pom",
            "pom.xml",
            "--actor",
            "iter005-slice1",
            "--correlation-ref",
            f"iter005:{suffix}:register",
        ),
    )
    workspace_id = registration["workspace"]["workspace_id"]
    scope_id = registration["workspace"]["scope"]["id"]
    zero_questions = _zero_question_counts(database)

    first = cli.management(
        "workspace-r1",
        (
            "update-maven-workspace",
            "--workspace-id",
            workspace_id,
            "--repository-revision",
            r1,
            "--idempotency-key",
            f"iter005:{suffix}:r1",
            "--correlation-ref",
            f"iter005:{suffix}:r1",
        ),
    )
    _assert_update(first, revision=r1, module_artifacts=(core_artifact, api_artifact, cli_artifact))
    replay = cli.management(
        "workspace-r1-replay",
        (
            "update-maven-workspace",
            "--workspace-id",
            workspace_id,
            "--repository-revision",
            r1,
            "--idempotency-key",
            f"iter005:{suffix}:r1",
            "--correlation-ref",
            f"iter005:{suffix}:r1-replay",
        ),
    )
    if replay["attempt"]["attempt_id"] != first["attempt"]["attempt_id"] or replay["version"]["version_id"] != first["version"]["version_id"]:
        raise GateFailure("idempotent R1 replay produced another Attempt or Version")

    second = cli.management(
        "workspace-r2",
        (
            "update-maven-workspace",
            "--workspace-id",
            workspace_id,
            "--repository-revision",
            r2,
            "--idempotency-key",
            f"iter005:{suffix}:r2",
            "--correlation-ref",
            f"iter005:{suffix}:r2",
        ),
    )
    _assert_update(second, revision=r2, module_artifacts=(core_artifact, api_artifact))
    first_system = _entity(first, "SOFTWARE_SYSTEM")
    second_system = _entity(second, "SOFTWARE_SYSTEM")
    if first_system["root_id"] != second_system["root_id"]:
        raise GateFailure("Software System Root did not remain stable")
    if first_system["state_id"] == second_system["state_id"]:
        raise GateFailure("Software System State did not change")
    if not second["snapshot_owner_result"]["deletions"]["removed_members"]:
        raise GateFailure("R2 did not report the removed module")
    if _current_snapshot(database, scope_id) != second["version"]["snapshot_id"]:
        raise GateFailure("CURRENT does not point at R2")

    versions = cli.management(
        "workspace-versions",
        ("list-maven-workspace-versions", "--workspace-id", workspace_id),
    )
    read_sets = cli.management(
        "workspace-read-sets",
        ("list-read-sets", "--workspace-id", workspace_id),
    )
    if [item["repository_revision"] for item in versions["versions"]] != [r1, r2]:
        raise GateFailure("Workspace history does not preserve exact R1 then R2")
    if len(read_sets["read_sets"]) != 3 or len(second["catalog"]["entries"]) != 3:
        raise GateFailure("R1, R2, and ordered R1->R2 Read Sets were not published")

    # A second Workspace provides a public-CLI Bundle failure/restart probe
    # without moving the main Workspace's R2 CURRENT.
    recovery_registration = cli.management(
        "recovery-register",
        (
            "register-maven-workspace",
            "--idempotency-key",
            f"iter005:{suffix}:recovery-workspace",
            "--source-target",
            str(repository),
            "--display-name",
            f"ITER-005 Recovery {suffix}",
            "--canonical-system-key",
            f"iter005:{suffix}:recovery",
            "--root-pom",
            "pom.xml",
            "--actor",
            "iter005-slice1",
            "--correlation-ref",
            f"iter005:{suffix}:recovery-register",
        ),
    )
    recovery_workspace_id = recovery_registration["workspace"]["workspace_id"]
    recovery_first = cli.management(
        "recovery-r2",
        (
            "update-maven-workspace",
            "--workspace-id",
            recovery_workspace_id,
            "--repository-revision",
            r2,
            "--idempotency-key",
            f"iter005:{suffix}:recovery-r2",
            "--correlation-ref",
            f"iter005:{suffix}:recovery-r2",
        ),
    )
    _assert_update(recovery_first, revision=r2, module_artifacts=(core_artifact, api_artifact))
    original_mode = stat.S_IMODE(bundles.stat().st_mode)
    bundles.chmod(0o500)
    try:
        failed = cli.management(
            "recovery-r3-failed",
            (
                "update-maven-workspace",
                "--workspace-id",
                recovery_workspace_id,
                "--repository-revision",
                r3,
                "--idempotency-key",
                f"iter005:{suffix}:recovery-r3",
                "--correlation-ref",
                f"iter005:{suffix}:recovery-r3",
            ),
            expect=2,
        )
    finally:
        bundles.chmod(original_mode)
    details = failed.get("details", {})
    if details.get("workspace_attempt_state") != "OUTCOME_PENDING":
        raise GateFailure(f"uncertain Bundle I/O interruption was not preserved: {failed}")
    failed_attempt_id = str(details.get("workspace_attempt_id"))
    failed_versions = cli.management(
        "recovery-versions-before-resume",
        (
            "list-maven-workspace-versions",
            "--workspace-id",
            recovery_workspace_id,
        ),
    )
    if [item["availability"] for item in failed_versions["versions"]] != [
        "QUERYABLE",
        "READ_BUNDLE_UNAVAILABLE",
    ]:
        raise GateFailure("failed recovery Workspace did not retain old queryable Version")
    during_failure_catalog = cli.source_off("source-off-during-failure", ("list-read-sets",))
    if any(
        item["workspace_version_ids"] == [failed_versions["versions"][1]["version_id"]]
        for item in during_failure_catalog["read_sets"]
    ):
        raise GateFailure("unavailable Version entered the queryable Catalog")
    resumed = cli.management(
        "recovery-r3-resumed",
        (
            "resume-maven-workspace",
            "--attempt-id",
            failed_attempt_id,
            "--correlation-ref",
            f"iter005:{suffix}:recovery-resume",
        ),
    )
    if resumed["attempt"]["attempt_id"] != failed_attempt_id or resumed["attempt"]["state"] != "SUCCEEDED":
        raise GateFailure("restart did not resume the same Workspace Attempt")
    snapshot_successes = [
        step
        for step in resumed["attempt"]["steps"]
        if step["name"] == "SNAPSHOT_PUBLICATION" and step["outcome"] == "SUCCEEDED"
    ]
    if len(snapshot_successes) != 1:
        raise GateFailure("resume duplicated Snapshot publication side effects")
    resumed_attempt = cli.management(
        "recovery-attempt",
        ("show-maven-workspace-attempt", "--attempt-id", failed_attempt_id),
    )

    manifest_path, pointer = _catalog_path(catalog)
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    forbidden_keys = {
        "entities",
        "relations",
        "facts",
        "evidence",
        "artifact_payload",
        "source_payload",
        "repository_locator",
        "database_path",
    }
    observed_forbidden = sorted(forbidden_keys & _collect_keys(manifest))
    if observed_forbidden or str(repository).encode() in manifest_bytes or str(database).encode() in manifest_bytes:
        raise GateFailure(f"Catalog contains forbidden payload/path data: {observed_forbidden}")
    catalog_audit = {
        "schema": manifest.get("schema"),
        "catalog_id": manifest.get("catalog_id"),
        "revision": manifest.get("revision"),
        "document_digest": manifest.get("document_digest"),
        "pointer": pointer,
        "manifest_file_digest": _sha256(manifest_path),
        "entry_count": len(manifest["entries"]),
        "forbidden_keys_found": observed_forbidden,
        "repository_path_found": False,
        "database_path_found": False,
        "payload_policy": "NO_ENTITY_FACT_EVIDENCE_PAYLOAD",
    }
    _write_json(result_dir / "catalog-audit.json", catalog_audit)

    tamper = _tamper_cases(cli, result_dir)

    unmounted_database = result_dir / "authority.unmounted.sqlite3"
    unmounted_repository = result_dir / "source-repository.unmounted"
    database.rename(unmounted_database)
    unmounted_database_files = [str(unmounted_database)]
    for suffix_name in ("-wal", "-shm"):
        sidecar = Path(str(database) + suffix_name)
        if sidecar.exists():
            unmounted_sidecar = Path(str(unmounted_database) + suffix_name)
            sidecar.rename(unmounted_sidecar)
            unmounted_database_files.append(str(unmounted_sidecar))
    repository.rename(unmounted_repository)
    mount_manifest = {
        "process": "software_world_model.interface.read_set_catalog_cli",
        "source_off": True,
        "mounted_read_only_inputs": [str(catalog), str(bundles)],
        "authority_database_original_path_exists": database.exists(),
        "repository_original_path_exists": repository.exists(),
        "unavailable_inputs": [*unmounted_database_files, str(unmounted_repository)],
        "accepted_cli_options": ["--catalog-root", "--bundle-root"],
        "forbidden_cli_options": ["--database", "--source-target"],
    }
    _write_json(result_dir / "source-off-mount-manifest.json", mount_manifest)
    verified = cli.source_off("source-off-verify", ("verify-current",))
    offline_sets = cli.source_off("source-off-list", ("list-read-sets",))

    r1_snapshot = first["version"]["snapshot_id"]
    r2_snapshot = second["version"]["snapshot_id"]
    r1_read_set = first["single_read_set"]["read_set_id"]
    comparison_read_set = second["comparison_read_set"]["read_set_id"]
    r1_system = first_system
    r1_core = _entity(first, "MAVEN_MODULE", core_artifact)
    r1_api = _entity(first, "MAVEN_MODULE", api_artifact)
    r1_cli = _entity(first, "MAVEN_MODULE", cli_artifact)
    view_specs = (
        (
            "source-off-candidates",
            r1_read_set,
            (
                "candidates",
                "--snapshot-id",
                r1_snapshot,
                "--mention",
                api_artifact,
                "--entity-type",
                "MAVEN_MODULE",
            ),
            "ENTITY_CANDIDATES",
        ),
        (
            "source-off-inventory",
            r1_read_set,
            (
                "inventory",
                "--system-snapshot-id",
                r1_snapshot,
                "--system-root-id",
                r1_system["root_id"],
                "--system-state-id",
                r1_system["state_id"],
            ),
            "CHILD_MODULE_INVENTORY",
        ),
        (
            "source-off-direct-dependency",
            r1_read_set,
            (
                "neighborhood",
                "--entity-snapshot-id",
                r1_snapshot,
                "--entity-root-id",
                r1_api["root_id"],
                "--entity-state-id",
                r1_api["state_id"],
                "--direction",
                "OUTGOING",
                "--predicate",
                "DEPENDS_ON",
            ),
            "DIRECT_NEIGHBORHOOD",
        ),
        (
            "source-off-path",
            r1_read_set,
            (
                "path-exists",
                "--source-snapshot-id",
                r1_snapshot,
                "--source-root-id",
                r1_cli["root_id"],
                "--source-state-id",
                r1_cli["state_id"],
                "--target-snapshot-id",
                r1_snapshot,
                "--target-root-id",
                r1_core["root_id"],
                "--target-state-id",
                r1_core["state_id"],
                "--predicate",
                "DEPENDS_ON",
            ),
            "PATH_EXISTS",
        ),
        (
            "source-off-diff",
            comparison_read_set,
            (
                "diff",
                "--base-snapshot-id",
                r1_snapshot,
                "--target-snapshot-id",
                r2_snapshot,
            ),
            "ORDERED_SNAPSHOT_DIFF",
        ),
    )
    views: dict[str, dict[str, Any]] = {}
    for name, read_set_id, arguments, expected_operation in view_specs:
        payload = cli.source_off(
            name,
            ("view", "--read-set-id", read_set_id, "--", *arguments),
        )
        if payload.get("operation") != expected_operation:
            raise GateFailure(f"{name}: expected {expected_operation}")
        views[name] = payload
    if views["source-off-path"].get("payload", {}).get("exists") is not True:
        raise GateFailure("Source-off R1 path oracle was not true")

    (result_dir / "graphs.md").write_text(
        "# R1/R2 Structure Graphs\n\n"
        + _graph_markdown("R1", first)
        + "\n"
        + _graph_markdown("R2", second),
        encoding="utf-8",
    )
    post_manifest = _source_manifest((workspace / "src", workspace / "pyproject.toml"), workspace)
    if producer["source_manifest_digest"] != _sha256_bytes(_json_bytes(post_manifest)):
        raise GateFailure("executed product source changed during validation")

    report: dict[str, object] = {
        "schema": "ITER-005-SLICE-001-REPORT@1",
        "status": "PASS",
        "gate_scope": ["V-003", "V-004", "V-005"],
        "metamorphic_input": {
            "suffix": suffix,
            "canonical_system_key": f"iter005:{suffix}:main",
            "group_id": group,
            "root_artifact": root_artifact,
            "module_artifacts": [core_artifact, api_artifact, cli_artifact],
            "module_paths": [core_path, api_path, cli_path],
        },
        "producer": producer,
        "fixture_git": {
            "r1": r1,
            "r2": r2,
            "recovery_r3": r3,
        },
        "zero_question": zero_questions,
        "workspace": {
            "workspace_id": workspace_id,
            "scope_id": scope_id,
            "update_mode": "FULL_REBUILD",
            "r1": _update_summary(first),
            "r2": _update_summary(second),
            "root_stable": first_system["root_id"] == second_system["root_id"],
            "state_changed": first_system["state_id"] != second_system["state_id"],
            "r2_removed_member_count": len(second["snapshot_owner_result"]["deletions"]["removed_members"]),
            "current_after_r2": r2_snapshot,
            "r1_exact_read_preserved": views["source-off-inventory"]["operation"] == "CHILD_MODULE_INVENTORY",
            "idempotent_replay_same_attempt": replay["attempt"]["attempt_id"] == first["attempt"]["attempt_id"],
        },
        "catalog": catalog_audit,
        "source_off": {
            "verified": verified.get("status") == "VERIFIED",
            "read_set_count": len(offline_sets["read_sets"]),
            "authority_database_available": database.exists(),
            "repository_available": repository.exists(),
            "operations": {
                name: value["operation"] for name, value in views.items()
            },
        },
        "recovery": {
            "failed_attempt_id": failed_attempt_id,
            "interruption_state": details.get("workspace_attempt_state"),
            "failed_version_availability": failed_versions["versions"][1]["availability"],
            "old_queryable_retained": failed_versions["versions"][0]["availability"] == "QUERYABLE",
            "failed_version_excluded_from_catalog": True,
            "same_attempt_resumed": resumed["attempt"]["attempt_id"] == failed_attempt_id,
            "snapshot_success_count": len(snapshot_successes),
            "final_state": resumed_attempt["state"],
        },
        "tamper_rejections": tamper,
        "artifacts": {
            "raw_cli": "raw/",
            "graphs": "graphs.md",
            "catalog_audit": "catalog-audit.json",
            "source_off_mount_manifest": "source-off-mount-manifest.json",
            "catalog_root": "catalog/",
            "bundle_root": "bundles/",
        },
    }
    _write_json(result_dir / "commands.json", cli.commands)
    _write_json(result_dir / "report.json", report)
    (result_dir / "report.md").write_text(_report_markdown(report), encoding="utf-8")
    return report


def _update_summary(value: Mapping[str, Any]) -> dict[str, object]:
    owner = value["snapshot_owner_result"]
    return {
        "repository_revision": value["version"]["repository_revision"],
        "snapshot_id": value["version"]["snapshot_id"],
        "snapshot_manifest_digest": value["version"]["snapshot_manifest_digest"],
        "version_digest": value["version"]["digest"],
        "availability": value["version"]["availability"],
        "coverage": owner["coverage"]["completeness"],
        "schema_ref": owner["coverage"]["schema_ref"],
        "profile_ref": owner["coverage"].get("profile_ref"),
        "entity_count": len(owner["entities"]),
        "relation_count": len(owner["relations"]),
        "removed_member_count": len(owner["deletions"]["removed_members"]),
        "single_read_set_id": value["single_read_set"]["read_set_id"],
        "single_bundle_digest": value["single_read_set"]["ordered_receipt"]["stored_bundle"]["bundle_digest"],
        "comparison_read_set_id": value["comparison_read_set"]["read_set_id"] if value["comparison_read_set"] else None,
        "metrics": value["execution_metrics"],
    }


def _report_markdown(report: Mapping[str, Any]) -> str:
    workspace = report["workspace"]
    r1 = workspace["r1"]
    r2 = workspace["r2"]
    rows = "\n".join(
        f"| {item['case']} | {item['result']} | `{item['error']}` | `{item['reason_code']}` |"
        for item in report["tamper_rejections"]
    )
    return f"""# ITER-005 SLICE-001 Acceptance Evidence

Status: **PASS** for the implemented Slice only. This report does not authorize SLICE-002 or accept ITER-005.

## Exact inputs and zero-question precondition

- Metamorphic system: `{report['metamorphic_input']['canonical_system_key']}`
- R1: `{report['fixture_git']['r1']}`
- R2: `{report['fixture_git']['r2']}`
- Producer snapshot commit/tree: `{report['producer']['commit']}` / `{report['producer']['tree']}`
- Questions/Tasks/Sessions before R1: `{json.dumps(report['zero_question']['counts'], sort_keys=True)}`

## Workspace R1 -> R2

| Revision | Coverage | Entities | Relations | Removed | Source calls | Source bytes | Time ms | Snapshot |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| R1 `{r1['repository_revision'][:12]}` | {r1['coverage']} | {r1['entity_count']} | {r1['relation_count']} | {r1['removed_member_count']} | {r1['metrics']['source_calls']} | {r1['metrics']['source_bytes']} | {r1['metrics']['snapshot_elapsed_milliseconds']} | `{r1['snapshot_id']}` |
| R2 `{r2['repository_revision'][:12]}` | {r2['coverage']} | {r2['entity_count']} | {r2['relation_count']} | {r2['removed_member_count']} | {r2['metrics']['source_calls']} | {r2['metrics']['source_bytes']} | {r2['metrics']['snapshot_elapsed_milliseconds']} | `{r2['snapshot_id']}` |

Update mode is `FULL_REBUILD`. Root stable: `{workspace['root_stable']}`; State changed: `{workspace['state_changed']}`;
CURRENT is R2: `{workspace['current_after_r2']}`; R1 exact Source-off read preserved: `{workspace['r1_exact_read_preserved']}`.

## Catalog and Source-off result

- Schema: `{report['catalog']['schema']}`
- Catalog revision/digest: `{report['catalog']['revision']}` / `{report['catalog']['document_digest']}`
- Entries: `{report['catalog']['entry_count']}`; forbidden payload keys: `{report['catalog']['forbidden_keys_found']}`
- Authority DB available: `{report['source_off']['authority_database_available']}`; Source repository available: `{report['source_off']['repository_available']}`
- Source-off operations: `{json.dumps(report['source_off']['operations'], sort_keys=True)}`

See `graphs.md`, `source-off-mount-manifest.json`, `catalog-audit.json`, and the exact public CLI documents under `raw/`.

## Failure, restart, and tamper

An uncertain Bundle I/O interruption produced `{report['recovery']['interruption_state']}` on Attempt
`{report['recovery']['failed_attempt_id']}` while the Version was marked `{report['recovery']['failed_version_availability']}`. The old Version stayed
queryable, the unavailable Version was absent from the Catalog, and restart resumed the same Attempt with exactly
`{report['recovery']['snapshot_success_count']}` successful Snapshot publication Step.

| Tamper | Result | Error | Reason |
|---|---|---|---|
{rows}

Stale CURRENT CAS and the Catalog-pointer/authority-receipt crash window are additionally exercised by the focused fault tests; their
append-only Step histories are not replaced by this report.
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--result-dir", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    workspace = arguments.workspace.resolve()
    result_dir = arguments.result_dir.resolve()
    try:
        run(workspace=workspace, result_dir=result_dir)
    except (GateFailure, OSError, ValueError, KeyError, TypeError, sqlite3.Error) as error:
        print(f"SLICE-001 FAIL: {error}", file=sys.stderr)
        return 1
    report_path = result_dir / "report.json"
    print(
        json.dumps(
            {
                "status": "PASS",
                "report": str(report_path),
                "report_digest": _sha256(report_path),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
