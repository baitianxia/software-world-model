"""Live one-call-per-case runner for ITER-003 V-009."""

from __future__ import annotations

import ast
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Mapping

from software_world_model.ai_infrastructure import (
    WorldModelCapabilityStrategy,
    WorldModelEvaluationOutput,
    WorldModelEvaluationReview,
    WorldModelStrategyConfiguration,
    world_model_answer_strategy_implementation_digest,
)
from software_world_model.cross_cutting import (
    Digest,
    DomainError,
    ErrorCode,
    canonical_json_bytes,
    digest_of,
)
from software_world_model.infrastructure import SqliteDatabase
from validation.agentic_capability_iteration_001.live_runner import _usage

from .manifest import (
    PINNED_SUITE_FILE_DIGEST,
    PINNED_SUITE_REF,
    case_fixture_digest,
    case_oracle_digest,
    sealed_case_input,
    verify_capability_suite,
)


EVALUATOR_PACKET_SCHEMA = "swm.iter-003.world-model-ce-evaluator-packet@1"
NORMALIZED_RESULT_SCHEMA = "swm.iter-003.world-model-ce-normalized-result@1"
INDEPENDENT_REVIEW_SCHEMA = "swm.iter-003.world-model-ce-independent-review@1"
CASE_EVIDENCE_SCHEMA = "swm.iter-003.world-model-ce-case-evidence@1"
EVALUATOR_SCRIPT = Path(__file__).with_name("evaluator.py")


class LiveWorldModelCapabilityCaseRunner:
    def __init__(
        self,
        *,
        database: SqliteDatabase,
        gateway: object,
        configuration: WorldModelStrategyConfiguration,
        expected_model_fingerprint: str,
        result_directory: str | Path,
    ) -> None:
        self._database = database
        self._strategy = WorldModelCapabilityStrategy(gateway, configuration)
        self._configuration = configuration
        self._expected_model_fingerprint = expected_model_fingerprint
        self._result_directory = Path(result_directory).resolve()

    def execute(
        self,
        *,
        suite: Mapping[str, object],
        case: Mapping[str, object],
    ) -> tuple[WorldModelEvaluationOutput, WorldModelEvaluationReview, Path]:
        verify_capability_suite(suite)
        case_id = _text(case.get("case_id"), "case ID")
        capability = _text(case.get("capability"), "capability")
        operations = case.get("available_operations", [])
        assert isinstance(operations, list)

        # The model call happens before this runner touches any evaluator-only
        # projection, expected value, or forbidden-event field.
        proposal = self._strategy.propose(
            case_id=case_id,
            capability=capability,
            sealed_input=case["input"],
            available_operations=tuple(operations),
        )
        usage = _usage(self._database)
        self._verify_one_call_input_closure(
            usage,
            case_id=case_id,
            capability=capability,
            sealed_input=case["input"],
            available_operations=operations,
        )
        if usage["actual_model_fingerprint"] != self._expected_model_fingerprint:
            raise DomainError(
                ErrorCode.QUALIFICATION_INVALID,
                "world-model capability case used an unexpected actual model",
            )

        case_directory = self._result_directory / "cases" / case_id
        case_directory.mkdir(parents=True, exist_ok=False)
        sealed_input_value = sealed_case_input(case)
        case_input_digest = digest_of(sealed_input_value)
        normalized_result = dict(proposal.normalized_result)
        normalized_result_digest = digest_of(normalized_result)
        operation_audit = {
            "model_call_count": 1,
            "hidden_retry_count": 0,
            "product_oracle_read_count": 0,
            "product_suite_read_count": 0,
            "repository_read_count": 0,
            "source_access_count": 0,
            "evidence_payload_access_count": 0,
            "project_name_branch_count": 0,
            "self_review_count": 0,
            "observed_events": [],
            "model_input_item_ids": [
                "instruction",
                "sealed-case-input",
                "qualification",
            ],
        }
        normalized_core = {
            "schema": NORMALIZED_RESULT_SCHEMA,
            "suite_ref": PINNED_SUITE_REF,
            "suite_digest": PINNED_SUITE_FILE_DIGEST,
            "case_id": case_id,
            "capability": capability,
            "case_input_digest": case_input_digest.value,
            "normalized_result": normalized_result,
            "normalized_result_digest": normalized_result_digest.value,
            "proposal_digest": proposal.digest.value,
            "strategy_implementation_digest": (
                world_model_answer_strategy_implementation_digest().value
            ),
            "strategy_configuration_digest": self._configuration.digest.value,
            "authorized_manifest_digest": (
                proposal.gateway_result.isolation_receipt.manifest_digest.value
            ),
            "provider_request_digest": (
                proposal.gateway_result.isolation_receipt.provider_request_digest.value
            ),
            "provider_request_id": (
                proposal.gateway_result.response.provider_request_id
                if proposal.gateway_result.response is not None
                else None
            ),
            "actual_model_fingerprint": usage["actual_model_fingerprint"],
            "operation_audit": operation_audit,
        }
        normalized_document = {
            **normalized_core,
            "document_digest": digest_of(normalized_core).value,
        }
        normalized_path = case_directory / "normalized-result.json"
        write_document_once(normalized_path, normalized_document)

        packet_core = {
            "schema": EVALUATOR_PACKET_SCHEMA,
            "suite_ref": PINNED_SUITE_REF,
            "suite_digest": PINNED_SUITE_FILE_DIGEST,
            "case": {
                "case_id": case_id,
                "capability": capability,
                "sealed_input": sealed_input_value,
                "case_input_digest": case_input_digest.value,
                "projection_fields": case["projection_fields"],
                "expected_normalized_result": case["expected_normalized_result"],
                "forbidden_events": case["forbidden_events"],
            },
        }
        packet_document = {
            **packet_core,
            "document_digest": digest_of(packet_core).value,
        }
        packet_path = case_directory / "evaluator-packet.json"
        write_document_once(packet_path, packet_document)

        review_path, evaluator_process = run_independent_evaluator(
            packet_path=packet_path,
            normalized_result_path=normalized_path,
            case_directory=case_directory,
        )
        review_document = load_document(review_path)
        verify_review_document(
            review_document,
            case=case,
            normalized_result_digest=normalized_result_digest,
            evaluator_process=evaluator_process,
        )

        provider_request_ids = usage["provider_request_ids"]
        assert isinstance(provider_request_ids, tuple)
        sink_manifest = {
            "suite_digest": PINNED_SUITE_FILE_DIGEST,
            "case_id": case_id,
            "fixture_digest": case_fixture_digest(case).value,
            "oracle_digest": case_oracle_digest(case).value,
            "normalized_result_document_digest": normalized_document["document_digest"],
            "evaluator_packet_document_digest": packet_document["document_digest"],
            "independent_review_document_digest": review_document["document_digest"],
            "strategy_implementation_digest": (
                world_model_answer_strategy_implementation_digest().value
            ),
            "strategy_configuration_digest": self._configuration.digest.value,
            "authorized_manifests_digest": digest_of(
                usage["authorized_manifests"]
            ).value,
            "isolation_receipts_digest": digest_of(
                usage["isolation_receipts"]
            ).value,
            "model_call_outcomes_digest": digest_of(
                usage["model_call_outcomes"]
            ).value,
            "provider_request_ids": list(provider_request_ids),
            "operation_audit": operation_audit,
            "evaluator_pid": review_document["evaluator_pid"],
            "generator_pid": os.getpid(),
        }
        evaluation_output = WorldModelEvaluationOutput.create(
            case_id=case_id,
            fixture_digest=case_fixture_digest(case),
            output_ref=f"world-model-capability-output:{case_id}:{normalized_result_digest.value}",
            output_digest=normalized_result_digest,
            sink_manifest_ref=f"world-model-capability-sink:{case_id}",
            sink_manifest_digest=digest_of(sink_manifest),
            generator_origin="volcengine-ark-world-model-proposal",
            actual_model_fingerprint=str(usage["actual_model_fingerprint"]),
            provider_request_ids=provider_request_ids,
            input_tokens=int(usage["input_tokens"]),
            output_tokens=int(usage["output_tokens"]),
            usage_complete=True,
        )
        findings = tuple(str(item) for item in review_document["findings"])
        evaluation_review = WorldModelEvaluationReview.create(
            review_ref=(
                f"world-model-independent-review:{case_id}:"
                f"{review_document['document_digest']}"
            ),
            case_id=case_id,
            output_digest=normalized_result_digest,
            oracle_ref=f"{PINNED_SUITE_REF}:oracle:{case_id}",
            oracle_digest=case_oracle_digest(case),
            generator_origin=evaluation_output.generator_origin,
            reviewer_origin="standalone-stdlib-v009-evaluator",
            platform_contract_valid=bool(
                review_document["platform_contract_valid"]
            ),
            oracle_match=bool(review_document["oracle_match"]),
            unauthorized_reference_count=int(
                review_document["unauthorized_reference_count"]
            ),
            material_omission_count=int(
                review_document["material_omission_count"]
            ),
            material_error_count=int(review_document["material_error_count"]),
            findings=findings,
        )
        evidence_core = {
            "schema": CASE_EVIDENCE_SCHEMA,
            "suite_ref": PINNED_SUITE_REF,
            "suite_digest": PINNED_SUITE_FILE_DIGEST,
            "case_id": case_id,
            "capability": capability,
            "fixture_digest": case_fixture_digest(case).value,
            "oracle_ref": f"{PINNED_SUITE_REF}:oracle:{case_id}",
            "oracle_digest": case_oracle_digest(case).value,
            "normalized_result_document": normalized_document,
            "authorized_manifests": usage["authorized_manifests"],
            "isolation_receipts": usage["isolation_receipts"],
            "model_call_outcomes": usage["model_call_outcomes"],
            "sink_manifest": sink_manifest,
            "evaluation_output": evaluation_output_document(evaluation_output),
            "independent_review": review_document,
            "evaluation_review": evaluation_review_document(evaluation_review),
        }
        evidence_document = {
            **evidence_core,
            "document_digest": digest_of(evidence_core).value,
        }
        evidence_path = case_directory / "case-evidence.json"
        write_document_once(evidence_path, evidence_document)
        return evaluation_output, evaluation_review, evidence_path

    @staticmethod
    def _verify_one_call_input_closure(
        usage: Mapping[str, object],
        *,
        case_id: str,
        capability: str,
        sealed_input: object,
        available_operations: list[object],
    ) -> None:
        request_ids = usage.get("provider_request_ids")
        manifests = usage.get("authorized_manifests")
        outcomes = usage.get("model_call_outcomes")
        if (
            not isinstance(request_ids, tuple)
            or len(request_ids) != 1
            or not isinstance(manifests, list)
            or len(manifests) != 1
            or not isinstance(outcomes, list)
            or len(outcomes) != 1
        ):
            raise DomainError(
                ErrorCode.QUALIFICATION_INVALID,
                "world-model capability case must use exactly one model call",
            )
        manifest = manifests[0]
        if not isinstance(manifest, dict):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "world-model capability manifest is invalid",
            )
        items = manifest.get("items")
        if (
            manifest.get("capability_id") != "world-model-authority-proposal"
            or manifest.get("execution_stage") != capability
            or not isinstance(items, list)
            or [item.get("item_id") for item in items]
            != ["instruction", "sealed-case-input", "qualification"]
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "world-model capability authorized input closure is invalid",
            )
        state_item = items[1]
        assert isinstance(state_item, dict)
        try:
            state = json.loads(str(state_item["content"]), object_pairs_hook=_unique_object)
        except (KeyError, json.JSONDecodeError, ValueError) as exc:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "world-model sealed model input is invalid",
            ) from exc
        expected_state: dict[str, object] = {
            "case_id": case_id,
            "capability": capability,
            "input": sealed_input,
        }
        if available_operations:
            expected_state["available_operations"] = available_operations
        serialized_state = json.dumps(state, ensure_ascii=False, sort_keys=True)
        if (
            state != expected_state
            or any(
                forbidden in serialized_state
                for forbidden in (
                    "expected_normalized_result",
                    "projection_fields",
                    "forbidden_events",
                    "WM-PRODUCT-",
                )
            )
        ):
            raise DomainError(
                ErrorCode.QUALIFICATION_INVALID,
                "world-model model input contains evaluator-only material",
            )


def run_independent_evaluator(
    *,
    packet_path: Path,
    normalized_result_path: Path,
    case_directory: Path,
) -> tuple[Path, subprocess.CompletedProcess[str]]:
    verify_evaluator_source(EVALUATOR_SCRIPT)
    staged_evaluator = case_directory / "independent-evaluator.py"
    write_bytes_once(staged_evaluator, EVALUATOR_SCRIPT.read_bytes(), mode=0o500)
    review_path = case_directory / "independent-review.json"
    environment = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "LC_ALL": "C",
        "PYTHONHASHSEED": "0",
    }
    completed = subprocess.run(
        [
            sys.executable,
            "-I",
            "-S",
            "-B",
            str(staged_evaluator),
            "--packet",
            str(packet_path),
            "--result",
            str(normalized_result_path),
            "--output",
            str(review_path),
        ],
        cwd=case_directory,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )
    write_bytes_once(
        case_directory / "evaluator-stdout.log",
        completed.stdout.encode("utf-8"),
    )
    write_bytes_once(
        case_directory / "evaluator-stderr.log",
        completed.stderr.encode("utf-8"),
    )
    if completed.returncode not in {0, 1} or not review_path.is_file():
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "independent world-model evaluator did not produce a closed review",
            {"evaluator_exit_code": completed.returncode},
        )
    return review_path, completed


def verify_evaluator_source(path: Path) -> None:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    allowed = {
        "__future__",
        "argparse",
        "hashlib",
        "json",
        "os",
        "pathlib",
        "sys",
    }
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.add((node.module or "").split(".", 1)[0])
    if imported - allowed:
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "independent evaluator imports a non-standard or evaluated module",
            {"unexpected_import_count": len(imported - allowed)},
        )
    forbidden_tokens = (
        "software_world_model",
        "product-suite",
        "product_input_suite",
        "VolcengineArk",
        "WorldModelCapabilityStrategy",
    )
    if any(token in source for token in forbidden_tokens):
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "independent evaluator references forbidden product or strategy material",
        )


def verify_review_document(
    review: Mapping[str, object],
    *,
    case: Mapping[str, object],
    normalized_result_digest: Digest,
    evaluator_process: subprocess.CompletedProcess[str],
) -> None:
    required = {
        "schema",
        "suite_ref",
        "suite_digest",
        "case_id",
        "capability",
        "case_input_digest",
        "normalized_result_digest",
        "projection",
        "projection_digest",
        "expected_projection_digest",
        "projection_exact",
        "forbidden_events_observed",
        "platform_contract_valid",
        "oracle_match",
        "unauthorized_reference_count",
        "material_omission_count",
        "material_error_count",
        "findings",
        "conclusion",
        "evaluator_pid",
        "evaluator_origin",
        "evaluator_implementation_digest",
        "evaluated_strategy_import_count",
        "document_digest",
    }
    core = {key: value for key, value in review.items() if key != "document_digest"}
    if (
        set(review) != required
        or review.get("schema") != INDEPENDENT_REVIEW_SCHEMA
        or review.get("suite_ref") != PINNED_SUITE_REF
        or review.get("suite_digest") != PINNED_SUITE_FILE_DIGEST
        or review.get("case_id") != case.get("case_id")
        or review.get("capability") != case.get("capability")
        or review.get("normalized_result_digest") != normalized_result_digest.value
        or review.get("evaluated_strategy_import_count") != 0
        or review.get("evaluator_origin") != "standalone-stdlib-v009-evaluator"
        or review.get("evaluator_implementation_digest")
        != "sha256:" + hashlib.sha256(EVALUATOR_SCRIPT.read_bytes()).hexdigest()
        or review.get("document_digest") != digest_of(core).value
        or not isinstance(review.get("evaluator_pid"), int)
        or review.get("evaluator_pid") == os.getpid()
        or evaluator_process.returncode
        != (0 if review.get("conclusion") == "PASS" else 1)
    ):
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "independent world-model review is invalid or mismatched",
        )


def evaluation_output_document(output: WorldModelEvaluationOutput) -> dict[str, object]:
    return {
        "case_id": output.case_id,
        "fixture_digest": output.fixture_digest.value,
        "output_ref": output.output_ref,
        "output_digest": output.output_digest.value,
        "sink_manifest_ref": output.sink_manifest_ref,
        "sink_manifest_digest": output.sink_manifest_digest.value,
        "generator_origin": output.generator_origin,
        "actual_model_fingerprint": output.actual_model_fingerprint,
        "provider_request_ids": list(output.provider_request_ids),
        "input_tokens": output.input_tokens,
        "output_tokens": output.output_tokens,
        "usage_complete": output.usage_complete,
        "digest": output.digest.value,
    }


def evaluation_review_document(review: WorldModelEvaluationReview) -> dict[str, object]:
    return {
        "review_ref": review.review_ref,
        "case_id": review.case_id,
        "output_digest": review.output_digest.value,
        "oracle_ref": review.oracle_ref,
        "oracle_digest": review.oracle_digest.value,
        "generator_origin": review.generator_origin,
        "reviewer_origin": review.reviewer_origin,
        "platform_contract_valid": review.platform_contract_valid,
        "oracle_match": review.oracle_match,
        "unauthorized_reference_count": review.unauthorized_reference_count,
        "material_omission_count": review.material_omission_count,
        "material_error_count": review.material_error_count,
        "findings": list(review.findings),
        "conclusion": review.conclusion.value,
        "digest": review.digest.value,
    }


def load_document(path: str | Path) -> dict[str, object]:
    try:
        value = json.loads(
            Path(path).read_text(encoding="utf-8"),
            object_pairs_hook=_unique_object,
        )
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "V-009 evidence document cannot be loaded",
        ) from exc
    if not isinstance(value, dict):
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "V-009 evidence document must contain one object",
        )
    return value


def write_document_once(path: str | Path, value: object) -> None:
    write_bytes_once(Path(path), canonical_json_bytes(value) + b"\n")


def write_bytes_once(path: Path, payload: bytes, *, mode: int = 0o600) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
    except FileExistsError as exc:
        raise DomainError(
            ErrorCode.IDEMPOTENCY_MISMATCH,
            "V-009 evidence path already exists",
        ) from exc
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    except Exception:
        try:
            path.unlink()
        except OSError:
            pass
        raise


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} must be non-empty")
    return value


__all__ = [
    "CASE_EVIDENCE_SCHEMA",
    "EVALUATOR_PACKET_SCHEMA",
    "INDEPENDENT_REVIEW_SCHEMA",
    "LiveWorldModelCapabilityCaseRunner",
    "NORMALIZED_RESULT_SCHEMA",
    "evaluation_output_document",
    "evaluation_review_document",
    "load_document",
    "run_independent_evaluator",
    "verify_evaluator_source",
    "verify_review_document",
    "write_bytes_once",
    "write_document_once",
]
