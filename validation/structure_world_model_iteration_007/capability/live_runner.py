"""One-call-per-case runner for source-semantics capability qualification."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Mapping

from software_world_model.ai_infrastructure import (
    JAVA_SOURCE_SEMANTICS_FIXED_WORLD_MODEL_PROPOSAL_CONTRACT,
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

from . import evaluator
from .manifest import (
    PINNED_ORACLE_FILE_DIGEST,
    PINNED_ORACLE_REF,
    PINNED_SUITE_FILE_DIGEST,
    PINNED_SUITE_REF,
    case_fixture_digest,
    case_oracle_digest,
    sealed_case_input,
)


CASE_EVIDENCE_SCHEMA = (
    "swm.iter-007.java-source-semantics-ce-case-evidence@1"
)
EVALUATOR_SCRIPT = Path(evaluator.__file__).resolve(strict=True)


class LiveJavaSourceSemanticsCapabilityCaseRunner:
    def __init__(
        self,
        *,
        database: SqliteDatabase,
        gateway: object,
        configuration: WorldModelStrategyConfiguration,
        expected_model_fingerprint: str,
        result_directory: Path,
    ) -> None:
        self._database = database
        self._strategy = WorldModelCapabilityStrategy(
            gateway,
            configuration,
            proposal_contract=(
                JAVA_SOURCE_SEMANTICS_FIXED_WORLD_MODEL_PROPOSAL_CONTRACT
            ),
        )
        self._configuration = configuration
        self._expected_model_fingerprint = expected_model_fingerprint
        self._result_directory = result_directory.resolve()

    def execute(
        self,
        *,
        case: Mapping[str, object],
        oracle_case: Mapping[str, object],
    ) -> tuple[WorldModelEvaluationOutput, WorldModelEvaluationReview, Path]:
        case_id = _text(case.get("case_id"), "case ID")
        capability = _text(case.get("capability"), "capability")
        operations = case.get("available_operations", [])
        if not isinstance(operations, list):
            raise DomainError(
                ErrorCode.EVALUATION_DEFINITION_INVALID,
                "source-semantics capability operations are invalid",
            )

        # Oracle and evaluator constraints are not materialized until this call ends.
        proposal = self._strategy.propose(
            case_id=case_id,
            capability=capability,
            sealed_input=case["input"],
            available_operations=tuple(str(item) for item in operations),
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
                "source-semantics case used an unexpected actual model",
            )

        case_directory = self._result_directory / "cases" / case_id
        case_directory.mkdir(parents=True, exist_ok=False)
        sealed = sealed_case_input(case)
        case_input_digest = digest_of(sealed)
        normalized = dict(proposal.normalized_result)
        normalized_digest = digest_of(normalized)
        operation_audit = {
            "model_call_count": 1,
            "hidden_retry_count": 0,
            "product_oracle_read_count": 0,
            "product_suite_read_count": 0,
            "repository_read_count": 0,
            "source_access_count": 0,
            "evidence_payload_access_count": 0,
            "project_dictionary_access_count": 0,
            "project_name_branch_count": 0,
            "self_review_count": 0,
            "observed_events": [],
            "model_input_item_ids": [
                "instruction",
                "sealed-case-input",
                "qualification",
            ],
        }
        result_core = {
            "schema": evaluator.RESULT_SCHEMA,
            "suite_ref": PINNED_SUITE_REF,
            "suite_digest": PINNED_SUITE_FILE_DIGEST,
            "case_id": case_id,
            "capability": capability,
            "case_input_digest": case_input_digest.value,
            "normalized_result": normalized,
            "normalized_result_digest": normalized_digest.value,
            "operation_audit": operation_audit,
        }
        result_document = _document(result_core)
        result_path = case_directory / "normalized-result.json"
        _write_once(result_path, result_document)

        packet_core = {
            "schema": evaluator.PACKET_SCHEMA,
            "suite_ref": PINNED_SUITE_REF,
            "suite_digest": PINNED_SUITE_FILE_DIGEST,
            "oracle_ref": PINNED_ORACLE_REF,
            "oracle_digest": PINNED_ORACLE_FILE_DIGEST,
            "case": {
                "case_id": case_id,
                "capability": capability,
                "sealed_input": sealed,
                "case_input_digest": case_input_digest.value,
                "projection_fields": case["projection_fields"],
                "semantic_constraints": case["semantic_constraints"],
                "expected_normalized_result": oracle_case[
                    "expected_normalized_result"
                ],
                "forbidden_events": oracle_case["forbidden_events"],
            },
        }
        packet_document = _document(packet_core)
        packet_path = case_directory / "evaluator-packet.json"
        _write_once(packet_path, packet_document)
        review_path, completed = _run_independent_evaluator(
            case_directory=case_directory,
            packet_path=packet_path,
            result_path=result_path,
        )
        review = _load(review_path)
        _verify_review(
            review,
            case_id=case_id,
            normalized_result_digest=normalized_digest,
            completed=completed,
        )

        request_ids = usage["provider_request_ids"]
        assert isinstance(request_ids, tuple)
        oracle_digest = case_oracle_digest(case, oracle_case)
        sink_manifest = {
            "suite_digest": PINNED_SUITE_FILE_DIGEST,
            "oracle_digest": PINNED_ORACLE_FILE_DIGEST,
            "case_id": case_id,
            "fixture_digest": case_fixture_digest(case).value,
            "case_oracle_digest": oracle_digest.value,
            "normalized_result_document_digest": result_document[
                "document_digest"
            ],
            "evaluator_packet_document_digest": packet_document[
                "document_digest"
            ],
            "independent_review_document_digest": review["document_digest"],
            "strategy_implementation_digest": (
                world_model_answer_strategy_implementation_digest(
                    JAVA_SOURCE_SEMANTICS_FIXED_WORLD_MODEL_PROPOSAL_CONTRACT
                ).value
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
            "provider_request_ids": list(request_ids),
            "operation_audit": operation_audit,
            "evaluator_pid": review["evaluator_pid"],
            "generator_pid": os.getpid(),
        }
        output = WorldModelEvaluationOutput.create(
            case_id=case_id,
            fixture_digest=case_fixture_digest(case),
            output_ref=(
                "java-source-semantics-capability-output:"
                f"{case_id}:{normalized_digest.value}"
            ),
            output_digest=normalized_digest,
            sink_manifest_ref=f"java-source-semantics-capability-sink:{case_id}",
            sink_manifest_digest=digest_of(sink_manifest),
            generator_origin="volcengine-ark-java-source-semantics-proposal",
            actual_model_fingerprint=str(usage["actual_model_fingerprint"]),
            provider_request_ids=request_ids,
            input_tokens=int(usage["input_tokens"]),
            output_tokens=int(usage["output_tokens"]),
            usage_complete=True,
        )
        evaluation_review = WorldModelEvaluationReview.create(
            review_ref=(
                f"java-source-semantics-independent-review:{case_id}:"
                f"{review['document_digest']}"
            ),
            case_id=case_id,
            output_digest=normalized_digest,
            oracle_ref=f"{PINNED_ORACLE_REF}:case:{case_id}",
            oracle_digest=oracle_digest,
            generator_origin=output.generator_origin,
            reviewer_origin="standalone-stdlib-iter007-source-semantics",
            platform_contract_valid=bool(review["platform_contract_valid"]),
            oracle_match=bool(review["oracle_match"]),
            unauthorized_reference_count=int(
                review["unauthorized_reference_count"]
            ),
            material_omission_count=int(review["material_omission_count"]),
            material_error_count=int(review["material_error_count"]),
            findings=tuple(str(item) for item in review["findings"]),
        )
        evidence_core = {
            "schema": CASE_EVIDENCE_SCHEMA,
            "suite_ref": PINNED_SUITE_REF,
            "suite_digest": PINNED_SUITE_FILE_DIGEST,
            "oracle_ref": PINNED_ORACLE_REF,
            "oracle_digest": PINNED_ORACLE_FILE_DIGEST,
            "case_id": case_id,
            "capability": capability,
            "fixture_digest": case_fixture_digest(case).value,
            "case_oracle_digest": oracle_digest.value,
            "normalized_result_document": result_document,
            "authorized_manifests": usage["authorized_manifests"],
            "isolation_receipts": usage["isolation_receipts"],
            "model_call_outcomes": usage["model_call_outcomes"],
            "sink_manifest": sink_manifest,
            "independent_review": review,
        }
        evidence_path = case_directory / "case-evidence.json"
        _write_once(evidence_path, _document(evidence_core))
        return output, evaluation_review, evidence_path

    @staticmethod
    def _verify_one_call_input_closure(
        usage: Mapping[str, object],
        *,
        case_id: str,
        capability: str,
        sealed_input: object,
        available_operations: list[object],
    ) -> None:
        manifests = usage.get("authorized_manifests")
        request_ids = usage.get("provider_request_ids")
        if (
            not isinstance(manifests, list)
            or len(manifests) != 1
            or not isinstance(request_ids, tuple)
            or len(request_ids) != 1
        ):
            raise DomainError(
                ErrorCode.QUALIFICATION_INVALID,
                "source-semantics case must use exactly one model call",
            )
        manifest = manifests[0]
        if not isinstance(manifest, Mapping):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "source-semantics capability manifest is invalid",
            )
        contract = JAVA_SOURCE_SEMANTICS_FIXED_WORLD_MODEL_PROPOSAL_CONTRACT
        items = manifest.get("items")
        if (
            manifest.get("strategy_ref") != contract.strategy_ref
            or manifest.get("proposal_vocabulary_ref")
            != contract.proposal_vocabulary_ref
            or manifest.get("execution_stage") != capability
            or not isinstance(items, list)
            or [item.get("item_id") for item in items]
            != ["instruction", "sealed-case-input", "qualification"]
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "source-semantics authorized input closure is invalid",
            )
        instruction = items[0]
        state_item = items[1]
        if (
            instruction.get("authority_reference") != contract.prompt_ref
            or instruction.get("content_digest")
            != digest_of(contract.prompt).value
        ):
            raise DomainError(
                ErrorCode.QUALIFICATION_INVALID,
                "source-semantics capability prompt binding drifted",
            )
        try:
            state = json.loads(
                str(state_item["content"]),
                object_pairs_hook=_unique_object,
            )
        except (KeyError, json.JSONDecodeError, ValueError) as exc:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "source-semantics sealed model input is invalid",
            ) from exc
        expected: dict[str, object] = {
            "case_id": case_id,
            "capability": capability,
            "input": sealed_input,
        }
        if available_operations:
            expected["available_operations"] = available_operations
        serialized = json.dumps(state, ensure_ascii=False, sort_keys=True)
        if state != expected or any(
            token in serialized
            for token in (
                "expected_normalized_result",
                "projection_fields",
                "semantic_constraints",
                "forbidden_events",
                "PINNED_REQUIRED_CASE_IDS",
                "oracle_ref",
            )
        ):
            raise DomainError(
                ErrorCode.QUALIFICATION_INVALID,
                "source-semantics model input contains evaluator-only material",
            )


def _run_independent_evaluator(
    *, case_directory: Path, packet_path: Path, result_path: Path
) -> tuple[Path, subprocess.CompletedProcess[str]]:
    staged = case_directory / "independent-evaluator.py"
    _write_bytes_once(staged, EVALUATOR_SCRIPT.read_bytes(), 0o500)
    review_path = case_directory / "independent-review.json"
    completed = subprocess.run(
        (
            sys.executable,
            "-I",
            "-S",
            "-B",
            str(staged),
            "--packet",
            str(packet_path),
            "--result",
            str(result_path),
            "--output",
            str(review_path),
        ),
        cwd=case_directory,
        env={
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "LC_ALL": "C",
            "PYTHONHASHSEED": "0",
        },
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    _write_bytes_once(
        case_directory / "evaluator-stdout.log",
        completed.stdout.encode(),
        0o600,
    )
    _write_bytes_once(
        case_directory / "evaluator-stderr.log",
        completed.stderr.encode(),
        0o600,
    )
    if completed.returncode not in {0, 1} or not review_path.is_file():
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "independent source-semantics evaluator did not return a review",
            {"evaluator_exit_code": completed.returncode},
        )
    return review_path, completed


def _verify_review(
    review: Mapping[str, object],
    *,
    case_id: str,
    normalized_result_digest: Digest,
    completed: subprocess.CompletedProcess[str],
) -> None:
    core = {key: value for key, value in review.items() if key != "document_digest"}
    if (
        review.get("schema") != evaluator.REVIEW_SCHEMA
        or review.get("suite_ref") != PINNED_SUITE_REF
        or review.get("suite_digest") != PINNED_SUITE_FILE_DIGEST
        or review.get("oracle_ref") != PINNED_ORACLE_REF
        or review.get("oracle_digest") != PINNED_ORACLE_FILE_DIGEST
        or review.get("case_id") != case_id
        or review.get("normalized_result_digest")
        != normalized_result_digest.value
        or review.get("evaluated_strategy_import_count") != 0
        or review.get("product_import_count") != 0
        or review.get("evaluator_implementation_digest")
        != "sha256:" + hashlib.sha256(EVALUATOR_SCRIPT.read_bytes()).hexdigest()
        or review.get("document_digest") != evaluator._document_digest(core)
        or review.get("evaluator_pid") == os.getpid()
        or completed.returncode
        != (0 if review.get("conclusion") == "PASS" else 1)
    ):
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "independent source-semantics review is invalid",
        )


def _document(core: dict[str, object]) -> dict[str, object]:
    return {**core, "document_digest": evaluator._document_digest(core)}


def _load(path: Path) -> dict[str, object]:
    try:
        value = json.loads(path.read_bytes(), object_pairs_hook=_unique_object)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "source-semantics capability evidence cannot be loaded",
        ) from exc
    if not isinstance(value, dict):
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "source-semantics capability evidence must be an object",
        )
    return value


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def _write_once(path: Path, value: object) -> None:
    _write_bytes_once(path, canonical_json_bytes(value), 0o600)


def _write_bytes_once(path: Path, value: bytes, mode: int) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
    try:
        remaining = memoryview(value)
        while remaining:
            remaining = remaining[os.write(descriptor, remaining) :]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} is invalid")
    return value


__all__ = [
    "CASE_EVIDENCE_SCHEMA",
    "LiveJavaSourceSemanticsCapabilityCaseRunner",
]
