"""Create zero-provider diagnostic, Conformance, and capability freezes."""

from __future__ import annotations

import argparse
import ast
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
from typing import Mapping

from software_world_model.ai_infrastructure import (
    BOUNDED_JAVA_SOURCE_SEMANTICS_EVALUATION_METRIC_CONTRACT,
    DEFAULT_DEEPSEEK_CONNECTION_POLICY,
    DEFAULT_DEEPSEEK_CREDENTIAL_RESOLUTION_POLICY,
    DEFAULT_DEEPSEEK_MAXIMUM_PRE_DISPATCH_TLS_HANDSHAKES,
    DeepSeekChatConformanceQualification,
    DeepSeekModelConfiguration,
    JAVA_SOURCE_SEMANTICS_WORLD_MODEL_PROPOSAL_CONTRACT,
    java_source_semantics_world_model_output_contract_digest,
    load_deepseek_chat_conformance_qualification,
    world_model_answer_prompt_program_digest,
    world_model_answer_strategy_implementation_digest,
)
from software_world_model.ai_infrastructure.deepseek_chat_conformance import (
    DEEPSEEK_CHAT_CONFORMANCE_FIXTURE_ID,
    DEEPSEEK_CHAT_CONFORMANCE_FIXTURE_VERSION,
    current_deepseek_implementation_manifest,
    deepseek_chat_conformance_fixture_digest,
)
from software_world_model.cross_cutting import canonical_json_bytes, digest_of
from software_world_model.interface.deepseek_provider_cli import (
    deepseek_model_probe_contract_digest,
)

from . import authorize, evaluator
from .manifest import (
    PINNED_ORACLE_FILE_DIGEST,
    PINNED_ORACLE_REF,
    PINNED_PROVIDER_REQUEST_COUNT,
    PINNED_REQUIRED_CASE_CALLS,
    PINNED_RESOURCE_POLICY_REF,
    PINNED_SUITE_FILE_DIGEST,
    PINNED_SUITE_REF,
    build_evaluation_definition,
    load_capability_inputs,
)


MODEL_DIAGNOSTIC_FREEZE_SCHEMA = (
    "SWM-ITER-008-DEEPSEEK-MODEL-DIAGNOSTIC-FREEZE@1"
)
PREFLIGHT_SCHEMA = "SWM-ITER-008-BOUNDED-CAPABILITY-PREFLIGHT@1"
CAPABILITY_FREEZE_SCHEMA = (
    "SWM-ITER-008-BOUNDED-JAVA-SOURCE-SEMANTICS-CAPABILITY-FREEZE@1"
)
REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
EVALUATOR_PATH = Path(evaluator.__file__).resolve(strict=True)
PACKAGE_ROOT = Path(__file__).resolve().parent
PACKAGE_FILE_NAMES = (
    "__init__.py",
    "authorize.py",
    "cli.py",
    "evaluator.py",
    "freeze.py",
    "live_runner.py",
    "manifest.py",
    "oracle-1.5.4.json",
    "suite-1.5.4.json",
)


class FreezeError(RuntimeError):
    pass


def create_model_diagnostic_freeze(
    *,
    output_directory: Path,
    created_at: datetime | None = None,
) -> tuple[Path, Path, dict[str, object]]:
    identity = _candidate_identity(require_clean=True)
    package = _package_manifest()
    configuration = DeepSeekModelConfiguration()
    implementation = current_deepseek_implementation_manifest()
    timestamp = _aware(created_at or datetime.now(timezone.utc))
    timestamp_text = timestamp.isoformat().replace("+00:00", "Z")
    scope = _model_diagnostic_scope(configuration, implementation)
    core = {
        "schema": MODEL_DIAGNOSTIC_FREEZE_SCHEMA,
        "freeze_ref": "ITER-008-DEEPSEEK-MODEL-DIAGNOSTIC-RUN-CANDIDATE@1",
        "created_at": timestamp_text,
        "environment": "EVALUATION_ONLY",
        "candidate_identity": identity,
        "package_manifest": package,
        "provider": {
            "authorization_scope": scope,
            "implementation_manifest": implementation,
            "credential_reference": configuration.secret_reference,
        },
        "dispatch_contract": {
            "status": "HELD_AWAITING_EXACT_USER_AUTHORIZATION",
            "authorization_scope": scope,
            "credential_read_before_authorization": False,
            "provider_socket_before_authorization": False,
        },
        "external_model_called_during_freeze": False,
        "raw_prompt_persisted": False,
        "raw_response_persisted": False,
        "hidden_canary_disclosed": False,
        "production_activation": "NOT_EXECUTED",
        "git_stage_commit_push": "NOT_EXECUTED",
    }
    freeze = {
        **core,
        "document_digest": digest_of(
            [MODEL_DIAGNOSTIC_FREEZE_SCHEMA, core]
        ).value,
    }
    output = _future_directory(output_directory)
    freeze_path = output / "model-diagnostic-freeze.json"
    _write_once(freeze_path, freeze)
    request_core = {
        "schema": authorize.MODEL_DIAGNOSTIC_REQUEST_SCHEMA,
        "status": "AWAITING_USER_AUTHORIZATION",
        "phase": "DEEPSEEK_MODEL_DIAGNOSTIC",
        "created_at": timestamp_text,
        "freeze_ref": core["freeze_ref"],
        "freeze_digest": freeze["document_digest"],
        "authorization_scope": scope,
        "authorization_must_postdate_freeze": True,
        "single_use": True,
        "retry_permitted": False,
        "hidden_canary_disclosure_requested": False,
        "production_activation": "NOT_EXECUTED",
        "git_stage_commit_push": "NOT_EXECUTED",
    }
    request = {
        **request_core,
        "document_digest": digest_of(
            [authorize.MODEL_DIAGNOSTIC_REQUEST_SCHEMA, request_core]
        ).value,
    }
    request_path = output / "model-diagnostic-authorization-request.json"
    _write_once(request_path, request)
    return freeze_path, request_path, freeze


def create_preflight(
    *,
    output_directory: Path,
    created_at: datetime | None = None,
) -> tuple[Path, Path, dict[str, object]]:
    load_capability_inputs()
    _verify_evaluator_source(EVALUATOR_PATH)
    identity = _candidate_identity(require_clean=True)
    package = _package_manifest()
    configuration = DeepSeekModelConfiguration()
    timestamp = _aware(created_at or datetime.now(timezone.utc))
    timestamp_text = timestamp.isoformat().replace("+00:00", "Z")
    deepseek_implementation = current_deepseek_implementation_manifest()
    conformance_scope = _conformance_scope(
        configuration, deepseek_implementation
    )
    core = {
        "schema": PREFLIGHT_SCHEMA,
        "freeze_ref": "ITER-008-BOUNDED-CAPABILITY-PREFLIGHT@1",
        "created_at": timestamp_text,
        "environment": "EVALUATION_ONLY",
        "candidate_identity": identity,
        "package_manifest": package,
        "proposal_contract": _proposal_contract(),
        "closed_inputs": _closed_inputs(),
        "deepseek_conformance": {
            "status": "NOT_EXECUTED_AWAITING_EXACT_USER_AUTHORIZATION",
            "authorization_scope": conformance_scope,
            "implementation_manifest": deepseek_implementation,
            "credential_read_before_authorization": False,
            "provider_socket_before_authorization": False,
        },
        "capability_qualification": {
            "status": "BLOCKED_BY_CURRENT_ADAPTER_CONFORMANCE",
            "planned_provider_call_count": PINNED_PROVIDER_REQUEST_COUNT,
            "authorization_status": "NOT_REQUESTED_UNTIL_CONFORMANCE_PASS",
        },
        "external_model_called": False,
        "hidden_canary_disclosed": False,
        "production_activation": "NOT_EXECUTED",
        "git_stage_commit_push": "NOT_EXECUTED",
    }
    preflight = {
        **core,
        "document_digest": digest_of([PREFLIGHT_SCHEMA, core]).value,
    }
    output = _future_directory(output_directory)
    preflight_path = output / "preflight-freeze.json"
    _write_once(preflight_path, preflight)
    request_core = {
        "schema": authorize.CONFORMANCE_REQUEST_SCHEMA,
        "status": "AWAITING_USER_AUTHORIZATION",
        "phase": "DEEPSEEK_CONFORMANCE",
        "created_at": timestamp_text,
        "freeze_ref": core["freeze_ref"],
        "freeze_digest": preflight["document_digest"],
        "authorization_scope": conformance_scope,
        "authorization_must_postdate_freeze": True,
        "single_use": True,
        "retry_permitted": False,
        "hidden_canary_disclosure_requested": False,
        "production_activation": "NOT_EXECUTED",
        "git_stage_commit_push": "NOT_EXECUTED",
    }
    request = {
        **request_core,
        "document_digest": digest_of(
            [authorize.CONFORMANCE_REQUEST_SCHEMA, request_core]
        ).value,
    }
    request_path = output / "conformance-authorization-request.json"
    _write_once(request_path, request)
    return preflight_path, request_path, preflight


def create_capability_freeze(
    *,
    preflight_path: Path,
    conformance_result_path: Path,
    output_directory: Path,
    created_at: datetime | None = None,
) -> tuple[Path, Path, dict[str, object]]:
    preflight = verify_preflight(preflight_path)
    configuration = DeepSeekModelConfiguration()
    conformance_path = conformance_result_path.resolve(strict=True)
    conformance = load_deepseek_chat_conformance_qualification(
        conformance_path,
        configuration,
    )
    suite, oracle = load_capability_inputs()
    evaluator_digest = _raw_sha(EVALUATOR_PATH)
    identity = preflight["candidate_identity"]
    assert isinstance(identity, Mapping)
    definition = build_evaluation_definition(
        suite,
        oracle,
        conformance_result_ref=conformance.result_ref,
        provider_configuration_fingerprint=configuration.fingerprint,
        actual_model_fingerprint=configuration.actual_model_fingerprint,
        adapter_version=configuration.adapter_version,
        exact_candidate_checkpoint_ref=f"git:{identity['commit']}",
        environment_ref=(
            "iter-008-bounded-capability-evaluation:"
            f"git:{identity['commit']}"
        ),
        reference_strategy_ref=f"standalone-stdlib-evaluator:{evaluator_digest}",
        resource_policy_ref=PINNED_RESOURCE_POLICY_REF,
        valid_for_seconds=604800,
    )
    timestamp = _aware(created_at or datetime.now(timezone.utc))
    if timestamp < _parse_time(
        preflight.get("created_at"), "preflight creation time"
    ) or timestamp < _conformance_completed_at(conformance_path):
        raise FreezeError(
            "capability freeze must postdate preflight and Conformance"
        )
    timestamp_text = timestamp.isoformat().replace("+00:00", "Z")
    capability_scope = _capability_scope(configuration, conformance)
    core = {
        "schema": CAPABILITY_FREEZE_SCHEMA,
        "freeze_ref": (
            "ITER-008-BOUNDED-JAVA-SOURCE-SEMANTICS-CAPABILITY-"
            "QUALIFICATION-CANDIDATE@1"
        ),
        "created_at": timestamp_text,
        "environment": "EVALUATION_ONLY",
        "preflight_digest": preflight["document_digest"],
        "candidate_identity": dict(identity),
        "package_manifest": preflight["package_manifest"],
        "proposal_contract": preflight["proposal_contract"],
        "closed_inputs": preflight["closed_inputs"],
        "evaluation_definition": _definition_document(definition),
        "metric_contract_digest": digest_of(
            BOUNDED_JAVA_SOURCE_SEMANTICS_EVALUATION_METRIC_CONTRACT
        ).value,
        "provider": {
            **capability_scope,
            "credential_reference": configuration.secret_reference,
            "qualification_valid_until": conformance.valid_until.isoformat(),
        },
        "dispatch_contract": {
            "status": "HELD_AWAITING_EXACT_USER_AUTHORIZATION",
            "authorization_scope": capability_scope,
            "credential_read_before_authorization": False,
            "provider_socket_before_authorization": False,
        },
        "external_model_called_during_freeze": False,
        "hidden_canary_disclosed": False,
        "production_activation": "NOT_EXECUTED",
        "git_stage_commit_push": "NOT_EXECUTED",
    }
    freeze = {
        **core,
        "document_digest": digest_of([CAPABILITY_FREEZE_SCHEMA, core]).value,
    }
    output = _future_directory(output_directory)
    freeze_path = output / "qualification-freeze.json"
    _write_once(freeze_path, freeze)
    request_core = {
        "schema": authorize.CAPABILITY_REQUEST_SCHEMA,
        "status": "AWAITING_USER_AUTHORIZATION",
        "phase": "BOUNDED_CAPABILITY_QUALIFICATION",
        "created_at": timestamp_text,
        "freeze_ref": core["freeze_ref"],
        "freeze_digest": freeze["document_digest"],
        "authorization_scope": capability_scope,
        "authorization_must_postdate_freeze": True,
        "single_use": True,
        "retry_permitted": False,
        "hidden_canary_disclosure_requested": False,
        "production_activation": "NOT_EXECUTED",
        "git_stage_commit_push": "NOT_EXECUTED",
    }
    request = {
        **request_core,
        "document_digest": digest_of(
            [authorize.CAPABILITY_REQUEST_SCHEMA, request_core]
        ).value,
    }
    request_path = output / "capability-authorization-request.json"
    _write_once(request_path, request)
    return freeze_path, request_path, freeze


def verify_preflight(path: Path) -> dict[str, object]:
    value = _load_document(path, PREFLIGHT_SCHEMA)
    configuration = DeepSeekModelConfiguration()
    deepseek_implementation = current_deepseek_implementation_manifest()
    expected_fields = {
        "schema",
        "freeze_ref",
        "created_at",
        "environment",
        "candidate_identity",
        "package_manifest",
        "proposal_contract",
        "closed_inputs",
        "deepseek_conformance",
        "capability_qualification",
        "external_model_called",
        "hidden_canary_disclosed",
        "production_activation",
        "git_stage_commit_push",
        "document_digest",
    }
    if (
        set(value) != expected_fields
        or value.get("freeze_ref")
        != "ITER-008-BOUNDED-CAPABILITY-PREFLIGHT@1"
        or value.get("environment") != "EVALUATION_ONLY"
        or value.get("candidate_identity")
        != _candidate_identity(require_clean=True)
        or value.get("package_manifest") != _package_manifest()
        or value.get("proposal_contract") != _proposal_contract()
        or value.get("closed_inputs") != _closed_inputs()
        or value.get("deepseek_conformance")
        != {
            "status": "NOT_EXECUTED_AWAITING_EXACT_USER_AUTHORIZATION",
            "authorization_scope": _conformance_scope(
                configuration, deepseek_implementation
            ),
            "implementation_manifest": deepseek_implementation,
            "credential_read_before_authorization": False,
            "provider_socket_before_authorization": False,
        }
        or value.get("capability_qualification")
        != {
            "status": "BLOCKED_BY_CURRENT_ADAPTER_CONFORMANCE",
            "planned_provider_call_count": PINNED_PROVIDER_REQUEST_COUNT,
            "authorization_status": "NOT_REQUESTED_UNTIL_CONFORMANCE_PASS",
        }
        or value.get("external_model_called") is not False
        or value.get("hidden_canary_disclosed") is not False
        or value.get("production_activation") != "NOT_EXECUTED"
        or value.get("git_stage_commit_push") != "NOT_EXECUTED"
    ):
        raise FreezeError("bounded capability preflight drifted from the candidate")
    _parse_time(value.get("created_at"), "preflight creation time")
    load_capability_inputs()
    _verify_evaluator_source(EVALUATOR_PATH)
    return value


def _proposal_contract() -> dict[str, object]:
    contract = JAVA_SOURCE_SEMANTICS_WORLD_MODEL_PROPOSAL_CONTRACT
    return {
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
            java_source_semantics_world_model_output_contract_digest(
                contract
            ).value
        ),
        "proposal_vocabulary_ref": contract.proposal_vocabulary_ref,
        "instruction_transformation_ref": (
            contract.instruction_transformation_ref
        ),
        "available_operations": list(contract.available_operations),
        "capabilities": list(contract.capabilities),
        "tool_policy_ref": "model-no-tools-no-source-no-evidence@1",
    }


def _closed_inputs() -> dict[str, object]:
    return {
        "suite_ref": PINNED_SUITE_REF,
        "suite_digest": PINNED_SUITE_FILE_DIGEST,
        "oracle_ref": PINNED_ORACLE_REF,
        "oracle_digest": PINNED_ORACLE_FILE_DIGEST,
        "required_case_calls": [list(item) for item in PINNED_REQUIRED_CASE_CALLS],
        "required_case_count": len(PINNED_REQUIRED_CASE_CALLS),
        "planned_provider_call_count": PINNED_PROVIDER_REQUEST_COUNT,
        "evaluator_digest": _raw_sha(EVALUATOR_PATH),
        "evaluator_origin": "SEPARATE_STDLIB_PROCESS",
        "oracle_visibility_to_model": "FORBIDDEN",
        "product_question_visibility": "FORBIDDEN",
    }


def _model_diagnostic_scope(
    configuration: DeepSeekModelConfiguration,
    deepseek_implementation: Mapping[str, object],
) -> dict[str, object]:
    return {
        "destination": "DEEPSEEK",
        "provider_type": configuration.provider_type,
        "endpoint": configuration.endpoint,
        "adapter_version": configuration.adapter_version,
        "requested_model_ref": configuration.model_ref,
        "expected_actual_model_fingerprint": (
            configuration.actual_model_fingerprint
        ),
        "configuration_fingerprint": configuration.fingerprint.value,
        **_deepseek_transport_scope(),
        "deepseek_implementation_digest": deepseek_implementation[
            "aggregate_digest"
        ],
        "probe_contract_digest": deepseek_model_probe_contract_digest().value,
        "timeout_milliseconds": 30_000,
        "max_output_tokens": 64,
        "planned_provider_call_count": 1,
        "hidden_retry_count": 0,
        "payload_boundary": (
            "ONE_STATIC_STRICT_JSON_STATUS_PROBE_NO_PRODUCT_QUESTION_"
            "SOURCE_EVIDENCE_OR_HIDDEN_CANARY"
        ),
    }


def _conformance_scope(
    configuration: DeepSeekModelConfiguration,
    deepseek_implementation: Mapping[str, object],
) -> dict[str, object]:
    return {
        "destination": "DEEPSEEK",
        "provider_type": configuration.provider_type,
        "endpoint": configuration.endpoint,
        "adapter_version": configuration.adapter_version,
        "requested_model_ref": configuration.model_ref,
        "expected_actual_model_fingerprint": (
            configuration.actual_model_fingerprint
        ),
        "configuration_fingerprint": configuration.fingerprint.value,
        **_deepseek_transport_scope(),
        "conformance_fixture_id": DEEPSEEK_CHAT_CONFORMANCE_FIXTURE_ID,
        "conformance_fixture_version": (
            DEEPSEEK_CHAT_CONFORMANCE_FIXTURE_VERSION
        ),
        "conformance_fixture_digest": (
            deepseek_chat_conformance_fixture_digest().value
        ),
        "deepseek_implementation_digest": deepseek_implementation[
            "aggregate_digest"
        ],
        "planned_provider_call_count": 2,
        "hidden_retry_count": 0,
        "payload_boundary": (
            "TWO_SYNTHETIC_CONFORMANCE_NONCES_NO_PRODUCT_QUESTION_"
            "SOURCE_EVIDENCE_OR_HIDDEN_CANARY"
        ),
    }


def _capability_scope(
    configuration: DeepSeekModelConfiguration,
    conformance: DeepSeekChatConformanceQualification,
) -> dict[str, object]:
    return {
        "destination": "DEEPSEEK",
        "provider_type": configuration.provider_type,
        "endpoint": configuration.endpoint,
        "adapter_version": configuration.adapter_version,
        "requested_model_ref": configuration.model_ref,
        "expected_actual_model_fingerprint": (
            configuration.actual_model_fingerprint
        ),
        "configuration_fingerprint": configuration.fingerprint.value,
        **_deepseek_transport_scope(),
        "conformance_result_ref": conformance.result_ref,
        "conformance_result_digest": conformance.result_digest.value,
        "suite_ref": PINNED_SUITE_REF,
        "suite_digest": PINNED_SUITE_FILE_DIGEST,
        "oracle_ref": PINNED_ORACLE_REF,
        "oracle_digest": PINNED_ORACLE_FILE_DIGEST,
        "planned_provider_call_count": PINNED_PROVIDER_REQUEST_COUNT,
        "hidden_retry_count": 0,
        "payload_boundary": (
            "FORTY_SYNTHETIC_BOUNDED_PROPOSAL_CALLS_ACROSS_"
            "EIGHTEEN_CASES_NO_PRODUCT_QUESTION_SOURCE_EVIDENCE_OR_"
            "HIDDEN_CANARY"
        ),
    }


def _deepseek_transport_scope() -> dict[str, object]:
    return {
        "connection_policy": DEFAULT_DEEPSEEK_CONNECTION_POLICY,
        "maximum_pre_dispatch_tls_handshake_attempts": (
            DEFAULT_DEEPSEEK_MAXIMUM_PRE_DISPATCH_TLS_HANDSHAKES
        ),
        "credential_resolution_policy": (
            DEFAULT_DEEPSEEK_CREDENTIAL_RESOLUTION_POLICY
        ),
        "request_retry_allowed": False,
        "transport_session_audit_schema": (
            "SWM-DEEPSEEK-TRANSPORT-SESSION-AUDIT@1"
        ),
    }


def _candidate_identity(*, require_clean: bool) -> dict[str, object]:
    status = _git("status", "--porcelain=v1", "--untracked-files=all")
    if require_clean and status:
        raise FreezeError("candidate worktree must be clean before preflight")
    return {
        "commit": _git("rev-parse", "HEAD"),
        "tree": _git("rev-parse", "HEAD^{tree}"),
        "worktree_status": "CLEAN" if not status else "DIRTY",
        "identity_scope": "EXACT_GIT_COMMIT_AND_TREE@1",
    }


def _package_manifest() -> dict[str, object]:
    files: list[dict[str, object]] = []
    for name in PACKAGE_FILE_NAMES:
        path = PACKAGE_ROOT / name
        if not path.is_file() or path.is_symlink():
            raise FreezeError(f"capability package file is unavailable: {name}")
        payload = path.read_bytes()
        files.append(
            {
                "path": str(path.relative_to(REPOSITORY_ROOT)),
                "size": len(payload),
                "digest": "sha256:" + hashlib.sha256(payload).hexdigest(),
            }
        )
    return {
        "files": files,
        "aggregate_digest": digest_of(files).value,
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
        "DeepSeek",
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
        "cases": [
            {
                "case_id": item.case_id,
                "case_version": item.case_version,
                "fixture_ref": item.fixture_ref,
                "fixture_digest": item.fixture_digest.value,
                "oracle_ref": item.oracle_ref,
                "oracle_digest": item.oracle_digest.value,
                "required": item.required,
            }
            for item in value.cases
        ],
        "valid_for_seconds": value.valid_for_seconds,
        "definition_digest": value.digest.value,
    }


def _load_document(path: Path, schema: str) -> dict[str, object]:
    try:
        value = json.loads(path.read_bytes(), object_pairs_hook=_unique_object)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        raise FreezeError("sealed freeze document cannot be loaded") from exc
    if not isinstance(value, dict) or value.get("schema") != schema:
        raise FreezeError("sealed freeze schema is invalid")
    core = {key: item for key, item in value.items() if key != "document_digest"}
    if value.get("document_digest") != digest_of([schema, core]).value:
        raise FreezeError("sealed freeze digest is invalid")
    return value


def _future_directory(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    parent = path.parent.resolve(strict=True)
    resolved = parent / path.name
    if path != resolved or path.exists() or path.is_symlink():
        raise FreezeError("freeze output must be one new canonical directory")
    resolved.mkdir(mode=0o700)
    return resolved


def _write_once(path: Path, value: object) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        remaining = memoryview(canonical_json_bytes(value))
        while remaining:
            remaining = remaining[os.write(descriptor, remaining) :]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _raw_sha(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _git(*arguments: str) -> str:
    completed = subprocess.run(
        ("git", *arguments),
        cwd=REPOSITORY_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode:
        raise FreezeError(completed.stderr.decode("utf-8", errors="replace"))
    return completed.stdout.decode("utf-8").strip()


def _aware(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise FreezeError("freeze timestamp must be timezone-aware")
    return value.astimezone(timezone.utc)


def _parse_time(value: object, label: str) -> datetime:
    if not isinstance(value, str):
        raise FreezeError(f"{label} is invalid")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise FreezeError(f"{label} is invalid") from exc
    return _aware(parsed)


def _conformance_completed_at(path: Path) -> datetime:
    try:
        value = json.loads(path.read_bytes(), object_pairs_hook=_unique_object)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        raise FreezeError("Conformance completion time cannot be loaded") from exc
    if not isinstance(value, Mapping):
        raise FreezeError("Conformance result is invalid")
    return _parse_time(value.get("completed_at"), "Conformance completion time")


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    diagnostic = commands.add_parser("model-diagnostic")
    diagnostic.add_argument("--output-directory", required=True)
    preflight = commands.add_parser("preflight")
    preflight.add_argument("--output-directory", required=True)
    capability = commands.add_parser("capability")
    capability.add_argument("--preflight", required=True)
    capability.add_argument("--conformance-result", required=True)
    capability.add_argument("--output-directory", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    try:
        if arguments.command == "model-diagnostic":
            freeze_path, request_path, freeze = create_model_diagnostic_freeze(
                output_directory=Path(arguments.output_directory)
            )
            status = "MODEL_DIAGNOSTIC_FROZEN_AWAITING_USER_AUTHORIZATION"
            phase = "DEEPSEEK_MODEL_DIAGNOSTIC"
            planned_calls = 1
        elif arguments.command == "preflight":
            freeze_path, request_path, freeze = create_preflight(
                output_directory=Path(arguments.output_directory)
            )
            status = "PREFLIGHT_FROZEN_AWAITING_CONFORMANCE_AUTHORIZATION"
            phase = "DEEPSEEK_CONFORMANCE"
            planned_calls = 2
        else:
            freeze_path, request_path, freeze = create_capability_freeze(
                preflight_path=Path(arguments.preflight),
                conformance_result_path=Path(arguments.conformance_result),
                output_directory=Path(arguments.output_directory),
            )
            status = "CAPABILITY_FROZEN_AWAITING_USER_AUTHORIZATION"
            phase = "BOUNDED_CAPABILITY_QUALIFICATION"
            planned_calls = PINNED_PROVIDER_REQUEST_COUNT
        print(
            canonical_json_bytes(
                {
                    "status": status,
                    "phase": phase,
                    "freeze_path": str(freeze_path),
                    "freeze_digest": freeze["document_digest"],
                    "authorization_request_path": str(request_path),
                    "planned_provider_call_count": planned_calls,
                    "external_model_called": False,
                    "hidden_canary_disclosed": False,
                    "production_activation": "NOT_EXECUTED",
                }
            ).decode()
        )
        return 0
    except (FreezeError, OSError, ValueError) as exc:
        print(
            canonical_json_bytes(
                {"status": "ERROR", "message": str(exc)}
            ).decode()
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
