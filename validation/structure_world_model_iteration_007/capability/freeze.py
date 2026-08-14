"""Create a zero-provider freeze for ITER-007 semantic capability evaluation."""

from __future__ import annotations

import argparse
import ast
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import stat
import subprocess

from software_world_model.ai_infrastructure import (
    JAVA_SOURCE_SEMANTICS_WORLD_MODEL_EVALUATION_METRIC_CONTRACT,
    JAVA_SOURCE_SEMANTICS_WORLD_MODEL_PROPOSAL_CONTRACT,
    VolcengineArkModelConfiguration,
    WorldModelStrategyConfiguration,
    java_source_semantics_world_model_output_contract_digest,
    load_ark_chat_conformance_qualification,
    world_model_answer_prompt_program_digest,
    world_model_answer_strategy_implementation_digest,
)
from software_world_model.cross_cutting import canonical_json_bytes, digest_of

from . import evaluator
from .manifest import (
    PINNED_ORACLE_FILE_DIGEST,
    PINNED_ORACLE_REF,
    PINNED_REQUIRED_CASE_IDS,
    PINNED_SUITE_FILE_DIGEST,
    PINNED_SUITE_REF,
    build_evaluation_definition,
    load_capability_inputs,
)


FREEZE_SCHEMA = "SWM-ITER-007-JAVA-SOURCE-SEMANTICS-CAPABILITY-FREEZE@1"
AUTHORIZATION_REQUEST_SCHEMA = (
    "SWM-ITER-007-JAVA-SOURCE-SEMANTICS-CAPABILITY-AUTHORIZATION-REQUEST@1"
)
REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
EVALUATOR_PATH = Path(evaluator.__file__).resolve(strict=True)
_CANDIDATE_PATH_PREFIXES = ("src/", "tests/", "validation/")
_CANDIDATE_ROOT_FILES = frozenset({"pyproject.toml"})
_CANDIDATE_IDENTITY_SCOPE = (
    "EXACT_UNCOMMITTED_PRODUCT_VALIDATION_AND_TEST_CLOSURE@1"
)


class FreezeError(RuntimeError):
    pass


def create_freeze(
    *,
    output_directory: Path,
    conformance_result_path: Path,
    created_at: datetime | None = None,
) -> tuple[Path, Path, dict[str, object]]:
    output = _future_directory(output_directory)
    suite, oracle = load_capability_inputs()
    _verify_evaluator_source(EVALUATOR_PATH)
    configuration = VolcengineArkModelConfiguration()
    conformance = load_ark_chat_conformance_qualification(
        conformance_result_path.resolve(strict=True),
        configuration,
    )
    identity = _candidate_identity()
    strategy_configuration = WorldModelStrategyConfiguration(
        provider_type=configuration.provider_type,
        adapter_version=configuration.adapter_version,
        model_ref=configuration.model_ref,
        provider_configuration_fingerprint=configuration.fingerprint,
        qualification_ref=f"evaluation-only:{conformance.result_ref}",
        max_output_tokens=1000,
        timeout_milliseconds=180_000,
        classification="INTERNAL",
    )
    evaluator_digest = "sha256:" + hashlib.sha256(
        EVALUATOR_PATH.read_bytes()
    ).hexdigest()
    definition = build_evaluation_definition(
        suite,
        oracle,
        conformance_result_ref=conformance.result_ref,
        provider_configuration_fingerprint=configuration.fingerprint,
        actual_model_fingerprint=configuration.actual_model_fingerprint,
        adapter_version=configuration.adapter_version,
        exact_candidate_checkpoint_ref=(
            f"working-tree:{identity['worktree_manifest_digest']}"
        ),
        environment_ref=(
            "iter-007-java-source-semantics-capability-evaluation:"
            f"{identity['worktree_manifest_digest']}"
        ),
        reference_strategy_ref=f"standalone-stdlib-evaluator:{evaluator_digest}",
        resource_policy_ref=(
            "one-call-per-case-no-retry:"
            f"{strategy_configuration.digest.value}"
        ),
        valid_for_seconds=604800,
    )
    timestamp = (created_at or datetime.now(timezone.utc)).astimezone(timezone.utc)
    if timestamp.tzinfo is None:
        raise FreezeError("freeze timestamp must be timezone-aware")
    contract = JAVA_SOURCE_SEMANTICS_WORLD_MODEL_PROPOSAL_CONTRACT
    timestamp_text = timestamp.isoformat().replace("+00:00", "Z")
    core = {
        "schema": FREEZE_SCHEMA,
        "freeze_ref": (
            "ITER-007-JAVA-SOURCE-SEMANTICS-CAPABILITY-"
            "QUALIFICATION-CANDIDATE@1"
        ),
        "created_at": timestamp_text,
        "environment": "EVALUATION_ONLY",
        "candidate_identity": identity,
        "proposal_contract": {
            "capability_contract_version": contract.capability_contract_version,
            "strategy_ref": contract.strategy_ref,
            "strategy_implementation_digest": (
                world_model_answer_strategy_implementation_digest(contract).value
            ),
            "prompt_ref": contract.prompt_ref,
            "prompt_program_digest": (
                world_model_answer_prompt_program_digest(contract).value
            ),
            "output_contract_digest": (
                java_source_semantics_world_model_output_contract_digest().value
            ),
            "proposal_vocabulary_ref": contract.proposal_vocabulary_ref,
            "available_operations": list(contract.available_operations),
            "capabilities": list(contract.capabilities),
            "tool_policy_ref": "model-no-tools-no-source-no-evidence@1",
        },
        "closed_inputs": {
            "suite_ref": PINNED_SUITE_REF,
            "suite_digest": PINNED_SUITE_FILE_DIGEST,
            "oracle_ref": PINNED_ORACLE_REF,
            "oracle_digest": PINNED_ORACLE_FILE_DIGEST,
            "required_case_ids": list(PINNED_REQUIRED_CASE_IDS),
            "required_case_count": 12,
            "role_case_counts": {
                "IMPLEMENTATION_QUERY_PLANNING": 4,
                "IMPLEMENTATION_ANSWER_DRAFTING": 4,
                "IMPLEMENTATION_ANSWER_REVIEW": 4,
            },
            "evaluator_digest": evaluator_digest,
            "evaluator_origin": "SEPARATE_STDLIB_PROCESS",
            "oracle_visibility_to_model": "FORBIDDEN",
            "product_question_visibility": "FORBIDDEN",
        },
        "evaluation_definition": _definition_document(definition),
        "metric_contract_digest": digest_of(
            JAVA_SOURCE_SEMANTICS_WORLD_MODEL_EVALUATION_METRIC_CONTRACT
        ).value,
        "provider": {
            "provider_type": configuration.provider_type,
            "adapter_version": configuration.adapter_version,
            "requested_model_ref": configuration.model_ref,
            "actual_model_fingerprint": configuration.actual_model_fingerprint,
            "configuration_fingerprint": configuration.fingerprint.value,
            "endpoint": configuration.endpoint,
            "credential_reference": configuration.secret_reference,
            "conformance_result_ref": conformance.result_ref,
            "conformance_result_digest": conformance.result_digest.value,
        },
        "dispatch_contract": {
            "status": "HELD_AWAITING_EXACT_USER_AUTHORIZATION",
            "planned_provider_call_count": 12,
            "calls_per_case": 1,
            "hidden_retry_count": 0,
            "destination": "VOLCENGINE_ARK",
            "payload_boundary": (
                "TWELVE_SYNTHETIC_CLOSED_SOURCE_SEMANTICS_CASES_NO_"
                "PRODUCT_QUESTION_SOURCE_OR_EVIDENCE_PAYLOAD"
            ),
            "credential_read_before_authorization": False,
            "provider_socket_before_authorization": False,
        },
        "prior_run_relation": {
            "iter_006_grant_reusable": False,
            "iter_006_qualification_inherited": False,
            "new_contract_qualification_required": True,
        },
        "external_model_called": False,
        "production_activation": "NOT_EXECUTED",
        "git_stage_commit_push": "NOT_EXECUTED",
    }
    freeze = {**core, "document_digest": digest_of([FREEZE_SCHEMA, core]).value}
    freeze_path = output / "qualification-freeze.json"
    _write_once(freeze_path, freeze)
    authorization_core = {
        "schema": AUTHORIZATION_REQUEST_SCHEMA,
        "status": "AWAITING_USER_AUTHORIZATION",
        "freeze_ref": core["freeze_ref"],
        "freeze_digest": freeze["document_digest"],
        "suite_ref": PINNED_SUITE_REF,
        "suite_digest": PINNED_SUITE_FILE_DIGEST,
        "destination": "VOLCENGINE_ARK",
        "planned_provider_call_count": 12,
        "payload_boundary": core["dispatch_contract"]["payload_boundary"],
        "authorization_must_postdate_freeze": True,
        "iter_006_grant_reusable": False,
        "production_activation": "NOT_EXECUTED",
        "git_stage_commit_push": "NOT_EXECUTED",
    }
    authorization = {
        **authorization_core,
        "document_digest": digest_of(
            [AUTHORIZATION_REQUEST_SCHEMA, authorization_core]
        ).value,
    }
    authorization_path = output / "authorization-request.json"
    _write_once(authorization_path, authorization)
    return freeze_path, authorization_path, freeze


def _candidate_identity() -> dict[str, object]:
    head = _git("rev-parse", "HEAD")
    tree = _git("rev-parse", "HEAD^{tree}")
    raw = _git_bytes(
        "ls-files",
        "--modified",
        "--deleted",
        "--others",
        "--exclude-standard",
        "-z",
    )
    paths = sorted({item.decode("utf-8") for item in raw.split(b"\0") if item})
    entries: list[dict[str, object]] = []
    for relative in paths:
        if not (
            relative in _CANDIDATE_ROOT_FILES
            or relative.startswith(_CANDIDATE_PATH_PREFIXES)
        ):
            continue
        path = REPOSITORY_ROOT / relative
        if not path.exists():
            entries.append({"path": relative, "state": "DELETED"})
            continue
        metadata = path.lstat()
        if not stat.S_ISREG(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
            raise FreezeError(f"candidate path is not a regular file: {relative}")
        entries.append(
            {
                "path": relative,
                "state": "PRESENT",
                "size": metadata.st_size,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        )
    if not entries:
        raise FreezeError("candidate working tree manifest is empty")
    return {
        "baseline_commit": head,
        "baseline_tree": tree,
        "worktree_state": "UNCOMMITTED_CANDIDATE",
        "identity_scope": _CANDIDATE_IDENTITY_SCOPE,
        "changed_path_count": len(entries),
        "worktree_manifest_digest": digest_of(
            {"identity_scope": _CANDIDATE_IDENTITY_SCOPE, "paths": entries}
        ).value,
        "paths": entries,
    }


def _verify_evaluator_source(path: Path) -> None:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    allowed = {
        "__future__",
        "argparse",
        "hashlib",
        "json",
        "os",
        "pathlib",
        "typing",
    }
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.add((node.module or "").split(".", 1)[0])
    if imported - allowed:
        raise FreezeError("independent evaluator imports a non-stdlib module")
    for token in (
        "software_world_model",
        "WorldModelCapabilityStrategy",
        "world_model_product",
        "VolcengineArk",
    ):
        if token in source:
            raise FreezeError("independent evaluator references evaluated code")


def _definition_document(value) -> dict[str, object]:
    return {
        "evaluation_id": value.evaluation_id,
        "evaluation_version": value.evaluation_version,
        "capability_id": value.capability_id,
        "capability_contract_version": value.capability_contract_version,
        "strategy_id": value.strategy_id,
        "strategy_version": value.strategy_version,
        "implementation_digest": value.implementation_digest.value,
        "conformance_result_ref": value.conformance_result_ref,
        "provider_configuration_fingerprint": (
            value.provider_configuration_fingerprint.value
        ),
        "model_ref": value.model_ref,
        "adapter_version": value.adapter_version,
        "prompt_program_ref": value.prompt_program_ref,
        "prompt_program_digest": value.prompt_program_digest.value,
        "output_schema_ref": value.output_schema_ref,
        "output_schema_digest": value.output_schema_digest.value,
        "tool_policy_ref": value.tool_policy_ref,
        "data_source_revision_ref": value.data_source_revision_ref,
        "environment_ref": value.environment_ref,
        "reference_strategy_ref": value.reference_strategy_ref,
        "resource_policy_ref": value.resource_policy_ref,
        "metric_contract_digest": value.metric_contract_digest.value,
        "threshold_ref": value.threshold_ref,
        "case_count": len(value.cases),
        "valid_for_seconds": value.valid_for_seconds,
        "definition_digest": value.digest.value,
    }


def _future_directory(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    parent = path.parent.resolve(strict=True)
    resolved = parent / path.name
    if path != resolved or path.exists() or path.is_symlink():
        raise FreezeError("freeze output must be one new canonical directory")
    resolved.mkdir(mode=0o700)
    return resolved


def _write_once(path: Path, value: object) -> None:
    payload = canonical_json_bytes(value)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        remaining = memoryview(payload)
        while remaining:
            remaining = remaining[os.write(descriptor, remaining) :]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _git(*arguments: str) -> str:
    return _git_bytes(*arguments).decode("utf-8").strip()


def _git_bytes(*arguments: str) -> bytes:
    completed = subprocess.run(
        ("git", *arguments),
        cwd=REPOSITORY_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode:
        raise FreezeError(completed.stderr.decode("utf-8", errors="replace"))
    return completed.stdout


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-directory", required=True)
    parser.add_argument("--conformance-result", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    try:
        freeze_path, authorization_path, freeze = create_freeze(
            output_directory=Path(arguments.output_directory),
            conformance_result_path=Path(arguments.conformance_result),
        )
        print(
            canonical_json_bytes(
                {
                    "status": "FROZEN_AWAITING_USER_AUTHORIZATION",
                    "freeze_path": str(freeze_path),
                    "freeze_digest": freeze["document_digest"],
                    "authorization_request_path": str(authorization_path),
                    "suite_digest": PINNED_SUITE_FILE_DIGEST,
                    "planned_provider_call_count": 12,
                    "external_model_called": False,
                    "production_activation": "NOT_EXECUTED",
                }
            ).decode("utf-8")
        )
        return 0
    except (FreezeError, OSError, ValueError) as exc:
        print(canonical_json_bytes({"status": "ERROR", "message": str(exc)}).decode())
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
