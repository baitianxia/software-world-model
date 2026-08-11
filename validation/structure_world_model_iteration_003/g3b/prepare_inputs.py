#!/usr/bin/env python3
"""Prepare exact source-off G3b Bundles and the evaluator-only run plan."""

from __future__ import annotations

import argparse
from hashlib import sha256
from io import StringIO
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
from typing import Mapping, Sequence

from software_world_model.cross_cutting import canonical_json_bytes, digest_of
from software_world_model.interface.cli import main as swm_main
from validation.structure_world_model_iteration_003.metamorphic.generate_reactor import (
    generate,
)
from validation.structure_world_model_iteration_003.g3b.evaluate_results import (
    IDENTITY_ORACLE,
    MALL_ORACLE,
    build_baseline_comparison_preflight,
)


PROJECT_ROOT = Path(__file__).resolve().parents[3]
VALIDATION_ROOT = PROJECT_ROOT / "validation" / "structure_world_model_iteration_003"
V009_ROOT = (
    PROJECT_ROOT
    / "var"
    / "iteration-003"
    / "v009"
    / "019f9fced69110c6a7e357a4ea2394ec6742fd2e"
)
MALL_REPOSITORY = PROJECT_ROOT / "validation-projects" / "mall"
PRODUCT_INPUT = VALIDATION_ROOT / "questions" / "product-input-suite-1.0.0.json"
PRODUCT_SUITE = VALIDATION_ROOT / "questions" / "product-suite-1.0.0.json"
BASELINE_PLAN = V009_ROOT / "baselines" / "operator" / "product-plan.json"
BASELINE_SEAL = V009_ROOT / "baselines" / "baseline-seal.json"
BASELINE_SEED = V009_ROOT / "baselines" / "evaluator" / "seed.json"
BASELINE_GENERATION = (
    V009_ROOT / "baselines" / "evaluator" / "generation-report.json"
)
PRODUCT_INPUT_SHA256 = (
    "15bb9a72b68d69f8077ba95bd87b4c54861b0bc08e26ed38fb54221d71d1bfd4"
)
PRODUCT_SUITE_SHA256 = (
    "c165af6beb5ce66d45f035c3155ef4cb7d39b488fb6fe29af4b61e77217aaf2c"
)
BASELINE_SEAL_DIGEST = (
    "sha256:7be049fe746a71cb3b9c3941d81e8e51076256d0f8dac61ba5a5c88c873ecbdd"
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--implementation-commit", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    implementation_commit = _commit(arguments.implementation_commit)
    _require_clean_exact_checkpoint(implementation_commit)
    output_root = _new_directory_path(arguments.output_root)
    output_root.mkdir(mode=0o700, parents=True)
    product_root = output_root / "product"
    evaluator_root = output_root / "evaluator"
    authority_root = output_root / "authority"
    for directory in (product_root, evaluator_root, authority_root):
        directory.mkdir(mode=0o700)

    product_input = _load_exact(PRODUCT_INPUT)
    product_suite = _load_exact(PRODUCT_SUITE)
    baseline_plan = _load_exact(BASELINE_PLAN)
    baseline_seal = _load_exact(BASELINE_SEAL)
    seed_record = _load_exact(BASELINE_SEED)
    baseline_generation = _load_exact(BASELINE_GENERATION)
    _verify_frozen_inputs(
        product_input,
        product_suite,
        baseline_plan,
        baseline_seal,
        seed_record,
    )
    baseline_comparison = build_baseline_comparison_preflight(
        product_plan=baseline_plan,
        mall=_load_exact(MALL_ORACLE),
        identity=_load_exact(IDENTITY_ORACLE),
        generation=baseline_generation,
    )
    _write_new(
        evaluator_root / "baseline-comparison-preflight.json",
        canonical_json_bytes(baseline_comparison),
    )

    ready_root = product_root / "ready"
    ready_package = ready_root / "package"
    ready_root.mkdir()
    shutil.copytree(
        PROJECT_ROOT / "src" / "software_world_model",
        ready_package / "software_world_model",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
    )
    ready_receipt = _product_ready(ready_package)
    _write_new(
        evaluator_root / "product-ready.json",
        canonical_json_bytes(ready_receipt),
    )

    meta_product = product_root / "metamorphic"
    meta_evaluator = evaluator_root / "metamorphic"
    generated = generate(
        meta_product,
        meta_evaluator,
        _text(seed_record.get("seed"), "metamorphic seed"),
    )
    _verify_generated_graph(generated, baseline_generation)
    _write_new(
        evaluator_root / "generation-report.json",
        canonical_json_bytes(
            {
                "schema": "swm.iter-003.g3b-generation@1",
                "after_product_ready": digest_of(ready_receipt).value,
                **generated,
            }
        ),
    )

    mall_database = authority_root / "mall.sqlite3"
    mall_bundles = product_root / "bundles" / "mall"
    mall = _prepare_mall(
        database=mall_database,
        bundle_root=mall_bundles,
    )
    fixture_database = authority_root / "fixture.sqlite3"
    fixture_bundles = product_root / "bundles" / "fixture"
    fixture = _prepare_fixture(
        database=fixture_database,
        bundle_root=fixture_bundles,
        implementation_commit=implementation_commit,
    )
    meta_database = authority_root / "metamorphic.sqlite3"
    meta_bundles = product_root / "bundles" / "metamorphic"
    metamorphic = _prepare_metamorphic(
        database=meta_database,
        bundle_root=meta_bundles,
        repository=meta_product / "repository",
        generation=generated,
    )

    selectors = {
        "ORDERED_A_B": {
            **mall["ordered_a_b"],
            "authority_database": str(mall_database),
        },
        "EXACT_B": {
            **mall["exact_b"],
            "authority_database": str(mall_database),
        },
        "EXACT_FIXTURE_VALID": {
            **fixture,
            "authority_database": str(fixture_database),
        },
        "METAMORPHIC_A_B": {
            **metamorphic,
            "authority_database": str(meta_database),
        },
    }
    runs = _run_plan(product_input, baseline_plan, selectors)
    registry_core = {
        "schema": "swm.iter-003.g3b-prepared-inputs@1",
        "implementation_commit": implementation_commit,
        "product_input_suite_ref": product_input["suite_ref"],
        "product_input_suite_sha256": "sha256:" + PRODUCT_INPUT_SHA256,
        "product_suite_ref": product_suite["suite_ref"],
        "product_suite_sha256": "sha256:" + PRODUCT_SUITE_SHA256,
        "baseline_plan_document_digest": baseline_plan["document_digest"],
        "baseline_seal_digest": baseline_seal["document_digest"],
        "baseline_comparison_preflight_digest": baseline_comparison[
            "document_digest"
        ],
        "product_ready_digest": digest_of(ready_receipt).value,
        "metamorphic_generation_digest": digest_of(generated).value,
        "selectors": selectors,
        "runs_per_case": 5,
        "parity_run_count": 55,
        "gap_run_count": 5,
        "run_count": len(runs),
        "cold_process_per_run": True,
        "runs": runs,
        "product_oracle_paths_mounted": False,
        "baseline_result_paths_mounted": False,
        "production_activation": "NOT_EXECUTED",
    }
    registry = {**registry_core, "document_digest": digest_of(registry_core).value}
    registry_path = output_root / "prepared-inputs.json"
    _write_new(registry_path, canonical_json_bytes(registry))
    print(canonical_json_bytes(registry).decode("utf-8"))
    return 0


def _prepare_mall(*, database: Path, bundle_root: Path) -> dict[str, object]:
    bundle_root.mkdir(parents=True)
    configured = _configure(
        database,
        name="mall",
        target=MALL_REPOSITORY,
        canonical_key="https://github.com/macrozheng/mall.git",
    )
    revision_a = "a50870fba92d59021f07cacbe947442b1871e78f"
    revision_b = "cfaadb201bb7aa6425de069fab5e57bf8b5048f3"
    a = _build(
        database,
        configured,
        name="mall-a",
        revision=revision_a,
        root_pom="pom.xml",
        expected_current=None,
        max_poms=32,
    )
    b = _build(
        database,
        configured,
        name="mall-b",
        revision=revision_b,
        root_pom="pom.xml",
        expected_current=a,
        max_poms=32,
    )
    ordered = _export_set(
        database,
        configured,
        name="mall-a-b",
        snapshot_ids=(a, b),
        bundle_root=bundle_root / "ordered-a-b",
    )
    exact_b = _export_set(
        database,
        configured,
        name="mall-exact-b",
        snapshot_ids=(b,),
        bundle_root=bundle_root / "exact-b",
    )
    return {"ordered_a_b": ordered, "exact_b": exact_b}


def _prepare_fixture(
    *, database: Path, bundle_root: Path, implementation_commit: str
) -> dict[str, object]:
    bundle_root.mkdir(parents=True)
    configured = _configure(
        database,
        name="fixture",
        target=PROJECT_ROOT,
        canonical_key="frozen:maven-identity-anti-name-stitch@1",
    )
    snapshot = _build(
        database,
        configured,
        name="fixture-valid",
        revision=implementation_commit,
        root_pom=(
            "validation/structure_world_model_iteration_003/fixtures/"
            "maven-identity/valid/pom.xml"
        ),
        expected_current=None,
        max_poms=768,
    )
    return _export_set(
        database,
        configured,
        name="fixture-exact-valid",
        snapshot_ids=(snapshot,),
        bundle_root=bundle_root / "exact-valid",
    )


def _prepare_metamorphic(
    *,
    database: Path,
    bundle_root: Path,
    repository: Path,
    generation: Mapping[str, object],
) -> dict[str, object]:
    bundle_root.mkdir(parents=True)
    configured = _configure(
        database,
        name="metamorphic",
        target=repository,
        canonical_key="runtime:iter-003-metamorphic-reactor",
    )
    a = _build(
        database,
        configured,
        name="metamorphic-a",
        revision=_text(generation.get("revision_a"), "metamorphic revision A"),
        root_pom="pom.xml",
        expected_current=None,
        max_poms=32,
    )
    b = _build(
        database,
        configured,
        name="metamorphic-b",
        revision=_text(generation.get("revision_b"), "metamorphic revision B"),
        root_pom="pom.xml",
        expected_current=a,
        max_poms=32,
    )
    return _export_set(
        database,
        configured,
        name="metamorphic-a-b",
        snapshot_ids=(a, b),
        bundle_root=bundle_root / "ordered-a-b",
    )


def _configure(
    database: Path,
    *,
    name: str,
    target: Path,
    canonical_key: str,
) -> dict[str, str]:
    result = _cli(
        database,
        (
            "configure-system-source",
            "--idempotency-key",
            f"iter003-g3b-configure-{name}",
            "--source-target",
            str(target.resolve(strict=True)),
            "--paths",
            ".",
            "--display-name",
            f"ITER-003 G3b {name}",
            "--canonical-system-key",
            canonical_key,
            "--classification",
            "INTERNAL",
            "--actor",
            "iter003-g3b-preparer",
            "--reason",
            "prepare exact source-off G3b Structure Bundles",
            "--correlation-ref",
            f"iter003-g3b-{name}",
        ),
    )
    steps = {item["name"]: item for item in result["steps"]}
    return {
        "scope_id": steps["CREATE_SCOPE"]["result_reference"],
        "source_id": steps["REGISTER_SOURCE"]["result_reference"],
        "binding_id": steps["BIND_SOURCE"]["result_reference"],
    }


def _build(
    database: Path,
    configured: Mapping[str, str],
    *,
    name: str,
    revision: str,
    root_pom: str,
    expected_current: str | None,
    max_poms: int,
) -> str:
    arguments = [
        "build-maven-structure",
        "--scope-id",
        configured["scope_id"],
        "--scope-revision",
        "1",
        "--source-id",
        configured["source_id"],
        "--source-revision",
        "1",
        "--binding-id",
        configured["binding_id"],
        "--binding-revision",
        "1",
        "--repository-revision",
        revision,
        "--root-pom",
        root_pom,
        "--objective",
        "Build exact ITER-003 G3b Maven Structure knowledge",
        "--idempotency-key",
        f"iter003-g3b-build-{name}",
        "--classification",
        "INTERNAL",
        "--actor-ref",
        "iter003-g3b-preparer",
        "--correlation-ref",
        f"iter003-g3b-{name}",
        "--max-poms",
        str(max_poms),
        "--max-calls",
        str(max(64, max_poms * 2)),
        "--tree-page-size",
        "500",
        "--max-bytes-per-call",
        "1000000",
    ]
    if expected_current is not None:
        arguments.extend(("--expected-current-snapshot-id", expected_current))
    result = _cli(database, arguments)
    if (
        result.get("maven_report", {}).get("complete") is not True
        or result.get("application_acceptance", {}).get("decision") != "PASS"
    ):
        raise RuntimeError(f"Structure build {name} is incomplete")
    return _text(result.get("snapshot", {}).get("snapshot_id"), "Snapshot ID")


def _export_set(
    database: Path,
    configured: Mapping[str, str],
    *,
    name: str,
    snapshot_ids: tuple[str, ...],
    bundle_root: Path,
) -> dict[str, object]:
    bundle_root.mkdir(parents=True)
    task_suffix = sha256(name.encode("utf-8")).hexdigest()[:32]
    arguments = [
        "open-structure-read-session",
        "--scope-id",
        configured["scope_id"],
        "--scope-revision",
        "1",
        "--task-id",
        "task_" + task_suffix,
        "--task-revision",
        "1",
        "--caller-ref",
        "iter003-g3b-preparer",
        "--classification",
        "INTERNAL",
        "--idempotency-key",
        f"iter003-g3b-session-{name}",
    ]
    for snapshot_id in snapshot_ids:
        arguments.extend(("--snapshot-id", snapshot_id))
    session = _cli(database, arguments)
    if [item["snapshot_id"] for item in session["snapshots"]] != list(
        snapshot_ids
    ):
        raise RuntimeError(f"read Session {name} reordered Snapshots")
    snapshot_paths: list[str] = []
    snapshot_file_digests: list[str] = []
    for index, snapshot_id in enumerate(snapshot_ids):
        path = bundle_root / f"snapshot-{index + 1}.json"
        receipt = _cli(
            database,
            (
                "build-structure-snapshot-read-bundle",
                "--snapshot-id",
                snapshot_id,
                "--idempotency-key",
                f"iter003-g3b-bundle-{name}-{index + 1}",
                "--destination",
                str(path),
            ),
        )
        snapshot_paths.append(str(path))
        snapshot_file_digests.append(receipt["stored_bundle"]["file_digest"])
    ordered_path = bundle_root / "ordered.json"
    ordered = _cli(
        database,
        (
            "build-structure-ordered-read-bundle",
            "--session-id",
            session["session_id"],
            "--idempotency-key",
            f"iter003-g3b-ordered-{name}",
            "--destination",
            str(ordered_path),
        ),
    )
    return {
        "session_id": session["session_id"],
        "read_set_digest": session["read_set_digest"],
        "resolved_snapshot_ids": list(snapshot_ids),
        "ordered_bundle": str(ordered_path),
        "ordered_bundle_file_digest": ordered["stored_bundle"]["file_digest"],
        "snapshot_bundles": snapshot_paths,
        "snapshot_bundle_file_digests": snapshot_file_digests,
    }


def _run_plan(
    product_input: Mapping[str, object],
    baseline_plan: Mapping[str, object],
    selectors: Mapping[str, Mapping[str, object]],
) -> list[dict[str, object]]:
    static_cases = product_input.get("cases")
    if not isinstance(static_cases, list) or len(static_cases) != 8:
        raise RuntimeError("frozen product input case set drifted")
    runs: list[dict[str, object]] = []
    for case in static_cases:
        selector = _text(case.get("snapshot_selector"), "Snapshot selector")
        if selector not in selectors:
            raise RuntimeError(f"unknown Snapshot selector: {selector}")
        for number in range(1, 6):
            variant = "question" if number % 2 else "paraphrase"
            runs.append(
                {
                    "run_key": (
                        f"static-{case['case_id']}-run-{number:02d}-"
                        + ("canonical" if variant == "question" else "paraphrase")
                    ),
                    "case_id": case["case_id"],
                    "case_kind": "STATIC",
                    "question_variant": (
                        "canonical" if variant == "question" else "paraphrase"
                    ),
                    "question": case[variant],
                    "selector": selector,
                    "resolved_snapshot_ids": selectors[selector][
                        "resolved_snapshot_ids"
                    ],
                    "run_number": number,
                }
            )
    meta_questions: dict[str, str] = {}
    for run in baseline_plan.get("runs", []):
        if run.get("case_kind") == "RUNTIME_METAMORPHIC":
            case_id = _text(run.get("case_id"), "metamorphic case ID")
            question = _text(run.get("question"), "metamorphic question")
            previous = meta_questions.setdefault(case_id, question)
            if previous != question:
                raise RuntimeError("baseline metamorphic question drifted across runs")
    if tuple(sorted(meta_questions)) != tuple(
        f"WM-META-{index:03d}" for index in range(1, 5)
    ):
        raise RuntimeError("baseline metamorphic case set drifted")
    for case_id in sorted(meta_questions):
        for number in range(1, 6):
            runs.append(
                {
                    "run_key": f"meta-{case_id}-run-{number:02d}-template",
                    "case_id": case_id,
                    "case_kind": "RUNTIME_METAMORPHIC",
                    "question_variant": "template",
                    "question": meta_questions[case_id],
                    "selector": "METAMORPHIC_A_B",
                    "resolved_snapshot_ids": selectors["METAMORPHIC_A_B"][
                        "resolved_snapshot_ids"
                    ],
                    "run_number": number,
                }
            )
    if len(runs) != 60 or len({item["run_key"] for item in runs}) != 60:
        raise RuntimeError("G3b run plan must contain 60 unique runs")
    return runs


def _verify_frozen_inputs(
    product_input: Mapping[str, object],
    product_suite: Mapping[str, object],
    baseline_plan: Mapping[str, object],
    baseline_seal: Mapping[str, object],
    seed: Mapping[str, object],
) -> None:
    if (
        _sha256(PRODUCT_INPUT) != PRODUCT_INPUT_SHA256
        or _sha256(PRODUCT_SUITE) != PRODUCT_SUITE_SHA256
        or product_input.get("suite_ref")
        != "ITER-003-WORLD-MODEL-PRODUCT-INPUT-SUITE@1.0.0"
        or product_suite.get("suite_ref")
        != "ITER-003-WORLD-MODEL-PRODUCT-SUITE@1.0.0"
        or baseline_plan.get("checkpoint")
        != "019f9fced69110c6a7e357a4ea2394ec6742fd2e"
        or baseline_plan.get("run_count") != 55
        or baseline_seal.get("document_digest") != BASELINE_SEAL_DIGEST
        or seed.get("external_model_called") is not False
    ):
        raise RuntimeError("frozen Product/V-009 inputs are not exact")
    for document, label in (
        (baseline_plan, "baseline plan"),
        (baseline_seal, "baseline seal"),
        (seed, "baseline seed"),
    ):
        core = {key: value for key, value in document.items() if key != "document_digest"}
        if document.get("document_digest") != digest_of(core).value:
            raise RuntimeError(f"{label} document digest is invalid")


def _verify_generated_graph(
    generated: Mapping[str, object], baseline: Mapping[str, object]
) -> None:
    for key, value in generated.items():
        if baseline.get(key) != value:
            raise RuntimeError(f"metamorphic regeneration drifted at {key}")


def _product_ready(package_root: Path) -> dict[str, object]:
    script = Path(__file__).resolve().parent / "product_ready.py"
    completed = subprocess.run(
        (
            str(Path(sys.executable).resolve(strict=True)),
            "-I",
            "-S",
            "-B",
            str(script),
            "--package-root",
            str(package_root),
        ),
        check=False,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={
            "PATH": "/usr/bin:/bin",
            "LANG": "C",
            "LC_ALL": "C",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONNOUSERSITE": "1",
        },
        timeout=60,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            "product-ready process failed: "
            + completed.stderr.decode("utf-8", errors="replace")[:1000]
        )
    value = json.loads(completed.stdout, object_pairs_hook=_unique_object)
    if (
        not isinstance(value, dict)
        or value.get("external_model_called") is not False
        or value.get("metamorphic_seed_visible") is not False
    ):
        raise RuntimeError("product-ready receipt is invalid")
    return value


def _cli(database: Path, arguments: Sequence[str]) -> dict[str, object]:
    output = StringIO()
    code = swm_main(
        ["--database", str(database), *arguments],
        stdout=output,
    )
    try:
        value = json.loads(output.getvalue(), object_pairs_hook=_unique_object)
    except (json.JSONDecodeError, ValueError) as exc:
        raise RuntimeError("SWM CLI returned invalid JSON") from exc
    if code != 0 or not isinstance(value, dict) or "error" in value:
        raise RuntimeError(f"SWM CLI failed for {arguments[0]}: {value}")
    return value


def _require_clean_exact_checkpoint(expected: str) -> None:
    head = subprocess.run(
        ("git", "rev-parse", "HEAD"),
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    status = subprocess.run(
        ("git", "status", "--porcelain=v1"),
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    if head != expected or status:
        raise RuntimeError("G3b preparation requires the exact clean implementation commit")


def _load_exact(path: Path) -> dict[str, object]:
    try:
        value = json.loads(path.read_bytes(), object_pairs_hook=_unique_object)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise RuntimeError(f"invalid frozen JSON document: {path}") from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"frozen JSON document is not an object: {path}")
    return value


def _unique_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def _new_directory_path(path_text: str) -> Path:
    path = Path(path_text)
    if (
        not path.is_absolute()
        or path.resolve(strict=False) != path
        or path.exists()
        or path.is_symlink()
        or path.parent.resolve(strict=True) != path.parent
    ):
        raise ValueError("output root must be a new canonical absolute path")
    return path


def _write_new(path: Path, payload: bytes) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags, 0o600)
    try:
        remaining = memoryview(payload)
        while remaining:
            remaining = remaining[os.write(descriptor, remaining) :]
        os.fsync(descriptor)
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise RuntimeError("prepared output is not a regular file")
    finally:
        os.close(descriptor)


def _sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _commit(value: object) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 40
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError("implementation commit must be exact lowercase 40-hex")
    return value


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError(f"{label} must be non-empty canonical text")
    return value


if __name__ == "__main__":
    raise SystemExit(main())
