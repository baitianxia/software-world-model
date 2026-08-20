"""Multi-call case runner for bounded source-semantics qualification."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Mapping

from software_world_model.ai_infrastructure import (
    JAVA_SOURCE_SEMANTICS_WORLD_MODEL_PROPOSAL_CONTRACT,
    WorldModelCapabilityStrategy,
    WorldModelEvaluationOutput,
    WorldModelEvaluationReview,
    WorldModelStrategyConfiguration,
    world_model_answer_strategy_implementation_digest,
)
from software_world_model.cross_cutting import (
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
    available_operations_for_step,
    case_fixture_digest,
    case_oracle_digest,
    expected_step_projections,
    forbidden_events,
    sealed_step_input,
)


CASE_EVIDENCE_SCHEMA = (
    "swm.iter-008.bounded-java-source-semantics-ce-case-evidence@1"
)
EVALUATOR_SCRIPT = Path(evaluator.__file__).resolve(strict=True)
_APPLICATION_OWNED_TERMINAL_INPUT_FIELDS = {
    "IMPLEMENTATION_ANSWER_DRAFTING": (
        "authorized_step_result_ids",
        "authorized_support_digests",
    ),
    "IMPLEMENTATION_ANSWER_REVIEW": (
        "required_checked_need_ids",
        "required_checked_step_result_ids",
        "required_checked_support_digests",
    ),
}


class LiveBoundedJavaSourceSemanticsCapabilityCaseRunner:
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
            proposal_contract=JAVA_SOURCE_SEMANTICS_WORLD_MODEL_PROPOSAL_CONTRACT,
        )
        self._configuration = configuration
        self._expected_model_fingerprint = expected_model_fingerprint
        self._result_directory = result_directory.resolve()

    def execute(
        self,
        *,
        suite: Mapping[str, object],
        oracle: Mapping[str, object],
        case: Mapping[str, object],
        oracle_case: Mapping[str, object],
    ) -> tuple[
        WorldModelEvaluationOutput,
        WorldModelEvaluationReview,
        Path,
        dict[str, object],
    ]:
        case_id = _text(case.get("case_id"), "case ID")
        capability = _text(case.get("capability"), "capability")
        steps = case.get("steps")
        oracle_steps = oracle_case.get("steps")
        if (
            not isinstance(steps, list)
            or not isinstance(oracle_steps, list)
            or len(steps) != len(oracle_steps)
        ):
            raise DomainError(
                ErrorCode.EVALUATION_DEFINITION_INVALID,
                "bounded capability case steps are invalid",
            )
        normalized_results: list[dict[str, object]] = []
        sealed_inputs: list[dict[str, object]] = []
        available_operation_sets: list[tuple[str, ...]] = []
        case_call_ids: list[str] = []
        for call_index, step in enumerate(steps, start=1):
            if not isinstance(step, Mapping):
                raise DomainError(
                    ErrorCode.EVALUATION_DEFINITION_INVALID,
                    "bounded capability step is invalid",
                )
            sealed_input = sealed_step_input(suite, case, step)
            available_operations = available_operations_for_step(
                suite, case, step
            )
            call_id = f"{case_id}:call-{call_index}"
            proposal = self._strategy.propose(
                case_id=call_id,
                capability=capability,
                sealed_input=sealed_input,
                available_operations=available_operations,
            )
            if (
                capability == "IMPLEMENTATION_INVESTIGATION"
                and proposal.normalized_result.get("evidence_requests")
                != case.get("evidence_requests")
            ):
                raise DomainError(
                    ErrorCode.QUALIFICATION_INVALID,
                    "bounded capability call did not preserve the frozen evidence obligations",
                )
            sealed_inputs.append(sealed_input)
            available_operation_sets.append(available_operations)
            case_call_ids.append(call_id)
            normalized_results.append(dict(proposal.normalized_result))

        usage = _usage(self._database)
        self._verify_input_closure(
            usage,
            capability=capability,
            case_call_ids=case_call_ids,
            sealed_inputs=sealed_inputs,
            available_operation_sets=available_operation_sets,
            qualification_ref=self._configuration.qualification_ref,
        )
        if usage["actual_model_fingerprint"] != self._expected_model_fingerprint:
            raise DomainError(
                ErrorCode.QUALIFICATION_INVALID,
                "bounded capability case used an unexpected actual model",
            )

        case_directory = self._result_directory / "cases" / case_id
        case_directory.mkdir(parents=True, exist_ok=False)
        result_steps: list[dict[str, object]] = []
        packet_steps: list[dict[str, object]] = []
        input_digests: list[str] = []
        output_digests: list[str] = []
        trace_digests: list[str] = []
        projection_sets = suite.get("projection_sets")
        assert isinstance(projection_sets, Mapping)
        for call_index, (
            step,
            oracle_step,
            sealed_input,
            call_id,
            normalized,
        ) in enumerate(
            zip(
                steps,
                oracle_steps,
                sealed_inputs,
                case_call_ids,
                normalized_results,
            ),
            start=1,
        ):
            assert isinstance(step, Mapping) and isinstance(oracle_step, Mapping)
            input_digest = digest_of(sealed_input).value
            normalized_digest = digest_of(normalized).value
            trace_digest = evaluator._step_trace_digest(
                case_id,
                call_index,
                input_digest,
                normalized_digest,
            )
            input_digests.append(input_digest)
            output_digests.append(normalized_digest)
            trace_digests.append(trace_digest)
            result_steps.append(
                {
                    "call_index": call_index,
                    "case_call_id": call_id,
                    "sealed_input_digest": input_digest,
                    "normalized_result": normalized,
                    "normalized_result_digest": normalized_digest,
                    "evidence_trace_digest": trace_digest,
                }
            )
            packet_steps.append(
                {
                    "call_index": call_index,
                    "case_call_id": call_id,
                    "sealed_input": sealed_input,
                    "sealed_input_digest": input_digest,
                    "projection_fields": projection_sets[step["projection_ref"]],
                    "semantic_constraints": step["semantic_constraints"],
                    "expected_projections": list(
                        expected_step_projections(
                            suite, case, step, oracle_step
                        )
                    ),
                    "forbidden_events": forbidden_events(oracle, oracle_step),
                }
            )
        outcomes = usage.get("model_call_outcomes")
        request_ids = usage.get("provider_request_ids")
        assert isinstance(outcomes, list) and isinstance(request_ids, tuple)
        operation_audit = {
            "model_call_count": len(steps),
            "provider_request_count": len(request_ids),
            "unique_model_call_id_count": len(
                {item["model_call_id"] for item in outcomes}
            ),
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
                ["instruction", "sealed-case-input", "qualification"]
                for _ in steps
            ],
        }
        result_core = {
            "schema": evaluator.RESULT_SCHEMA,
            "suite_ref": PINNED_SUITE_REF,
            "suite_digest": PINNED_SUITE_FILE_DIGEST,
            "case_id": case_id,
            "capability": capability,
            "step_results": result_steps,
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
                "steps": packet_steps,
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
        aggregate_output_digest = digest_of(normalized_results)
        _verify_review(
            review,
            case_id=case_id,
            model_call_count=len(steps),
            completed=completed,
        )

        oracle_digest = case_oracle_digest(
            suite, oracle, case, oracle_case
        )
        fixture_digest = case_fixture_digest(suite, case)
        sink_manifest = {
            "suite_digest": PINNED_SUITE_FILE_DIGEST,
            "oracle_digest": PINNED_ORACLE_FILE_DIGEST,
            "case_id": case_id,
            "fixture_digest": fixture_digest.value,
            "case_oracle_digest": oracle_digest.value,
            "normalized_result_document_digest": result_document[
                "document_digest"
            ],
            "evaluator_packet_document_digest": packet_document[
                "document_digest"
            ],
            "independent_review_document_digest": review["document_digest"],
            "step_input_digests": input_digests,
            "step_result_digests": output_digests,
            "trace_digests": trace_digests,
            "strategy_implementation_digest": (
                world_model_answer_strategy_implementation_digest(
                    JAVA_SOURCE_SEMANTICS_WORLD_MODEL_PROPOSAL_CONTRACT
                ).value
            ),
            "strategy_configuration_digest": self._configuration.digest.value,
            "authorized_manifests_digest": digest_of(
                usage["authorized_manifests"]
            ).value,
            "isolation_receipts_digest": digest_of(
                usage["isolation_receipts"]
            ).value,
            "model_call_outcomes_digest": digest_of(outcomes).value,
            "provider_request_ids": list(request_ids),
            "operation_audit": operation_audit,
            "evaluator_pid": review["evaluator_pid"],
            "generator_pid": os.getpid(),
        }
        output = WorldModelEvaluationOutput.create(
            case_id=case_id,
            fixture_digest=fixture_digest,
            output_ref=(
                "bounded-java-source-semantics-capability-output:"
                f"{case_id}:{aggregate_output_digest.value}"
            ),
            output_digest=aggregate_output_digest,
            sink_manifest_ref=(
                f"bounded-java-source-semantics-capability-sink:{case_id}"
            ),
            sink_manifest_digest=digest_of(sink_manifest),
            generator_origin="deepseek-bounded-source-semantics-proposal",
            actual_model_fingerprint=str(usage["actual_model_fingerprint"]),
            provider_request_ids=request_ids,
            input_tokens=int(usage["input_tokens"]),
            output_tokens=int(usage["output_tokens"]),
            usage_complete=True,
        )
        evaluation_review = WorldModelEvaluationReview.create(
            review_ref=(
                f"bounded-source-semantics-independent-review:{case_id}:"
                f"{review['document_digest']}"
            ),
            case_id=case_id,
            output_digest=aggregate_output_digest,
            oracle_ref=f"{PINNED_ORACLE_REF}:case:{case_id}",
            oracle_digest=oracle_digest,
            generator_origin=output.generator_origin,
            reviewer_origin="standalone-stdlib-iter008-bounded-source-semantics",
            platform_contract_valid=bool(review["platform_contract_valid"]),
            oracle_match=bool(review["oracle_match"]),
            unauthorized_reference_count=int(
                review["unauthorized_reference_count"]
            ),
            material_omission_count=int(review["material_omission_count"]),
            material_error_count=int(review["material_error_count"]),
            findings=tuple(str(item) for item in review["findings"]),
        )
        case_evidence_summary = {
            "case_id": case_id,
            "status": "PASS" if review["conclusion"] == "PASS" else "FAIL",
            "model_call_count": len(steps),
            "step_input_digests": input_digests,
            "step_result_digests": output_digests,
            "trace_digests": trace_digests,
        }
        evidence_core = {
            "schema": CASE_EVIDENCE_SCHEMA,
            "suite_ref": PINNED_SUITE_REF,
            "suite_digest": PINNED_SUITE_FILE_DIGEST,
            "oracle_ref": PINNED_ORACLE_REF,
            "oracle_digest": PINNED_ORACLE_FILE_DIGEST,
            "case_id": case_id,
            "capability": capability,
            "fixture_digest": fixture_digest.value,
            "case_oracle_digest": oracle_digest.value,
            "case_evidence_summary": case_evidence_summary,
            "normalized_result_document": result_document,
            "authorized_manifests": usage["authorized_manifests"],
            "isolation_receipts": usage["isolation_receipts"],
            "model_call_outcomes": outcomes,
            "sink_manifest": sink_manifest,
            "independent_review": review,
        }
        evidence_path = case_directory / "case-evidence.json"
        _write_once(evidence_path, _document(evidence_core))
        return output, evaluation_review, evidence_path, case_evidence_summary

    @staticmethod
    def _verify_input_closure(
        usage: Mapping[str, object],
        *,
        capability: str,
        case_call_ids: list[str],
        sealed_inputs: list[dict[str, object]],
        available_operation_sets: list[tuple[str, ...]],
        qualification_ref: str,
    ) -> None:
        manifests = usage.get("authorized_manifests")
        request_ids = usage.get("provider_request_ids")
        outcomes = usage.get("model_call_outcomes")
        count = len(case_call_ids)
        if (
            not isinstance(manifests, list)
            or len(manifests) != count
            or not isinstance(request_ids, tuple)
            or len(request_ids) != count
            or len(set(request_ids)) != count
            or not isinstance(outcomes, list)
            or len(outcomes) != count
            or len({item.get("model_call_id") for item in outcomes}) != count
        ):
            raise DomainError(
                ErrorCode.QUALIFICATION_INVALID,
                "bounded capability case must use its exact model call count",
            )
        contract = JAVA_SOURCE_SEMANTICS_WORLD_MODEL_PROPOSAL_CONTRACT
        for manifest, call_id, sealed_input, available_operations in zip(
            manifests,
            case_call_ids,
            sealed_inputs,
            available_operation_sets,
        ):
            if not isinstance(manifest, Mapping):
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "bounded capability manifest is invalid",
                )
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
                    "bounded authorized input closure is invalid",
                )
            instruction = items[0]
            state_item = items[1]
            qualification = items[2]
            if (
                instruction.get("authority_reference") != contract.prompt_ref
                or instruction.get("transformation_ref")
                != contract.instruction_transformation_ref
                or instruction.get("content_digest")
                != digest_of(contract.prompt_for(capability)).value
            ):
                raise DomainError(
                    ErrorCode.QUALIFICATION_INVALID,
                    "bounded capability prompt binding drifted",
                )
            if (
                qualification.get("schema_ref") != "qualification-ref@1"
                or qualification.get("authority_reference")
                != qualification_ref
                or qualification.get("content") != qualification_ref
                or qualification.get("content_digest")
                != digest_of(qualification_ref).value
            ):
                raise DomainError(
                    ErrorCode.QUALIFICATION_INVALID,
                    "bounded capability qualification input drifted",
                )
            try:
                state = json.loads(
                    str(state_item["content"]),
                    object_pairs_hook=_unique_object,
                )
            except (KeyError, json.JSONDecodeError, ValueError) as exc:
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "bounded sealed model input is invalid",
                ) from exc
            expected_input = dict(sealed_input)
            for field in _APPLICATION_OWNED_TERMINAL_INPUT_FIELDS.get(
                capability, ()
            ):
                expected_input.pop(field)
            expected: dict[str, object] = {
                "case_id": call_id,
                "capability": capability,
                "input": expected_input,
            }
            if capability == "IMPLEMENTATION_INVESTIGATION":
                expected["available_operations"] = list(available_operations)
            serialized = json.dumps(state, ensure_ascii=False, sort_keys=True)
            if (
                state_item.get("content_digest")
                != digest_of(state_item.get("content")).value
                or state != expected
                or any(
                token in serialized
                for token in (
                    "expected_projection",
                    "expected_projections",
                    "projection_fields",
                    "semantic_constraints",
                    "forbidden_events",
                    "PINNED_REQUIRED_CASE_IDS",
                    "oracle_ref",
                )
                )
            ):
                raise DomainError(
                    ErrorCode.QUALIFICATION_INVALID,
                    "bounded model input contains evaluator-only material",
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
            "independent bounded evaluator did not return a review",
            {"evaluator_exit_code": completed.returncode},
        )
    return review_path, completed


def _verify_review(
    review: Mapping[str, object],
    *,
    case_id: str,
    model_call_count: int,
    completed: subprocess.CompletedProcess[str],
) -> None:
    core = {
        key: value for key, value in review.items() if key != "document_digest"
    }
    if (
        review.get("schema") != evaluator.REVIEW_SCHEMA
        or review.get("suite_ref") != PINNED_SUITE_REF
        or review.get("suite_digest") != PINNED_SUITE_FILE_DIGEST
        or review.get("oracle_ref") != PINNED_ORACLE_REF
        or review.get("oracle_digest") != PINNED_ORACLE_FILE_DIGEST
        or review.get("case_id") != case_id
        or review.get("model_call_count") != model_call_count
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
            "independent bounded source-semantics review is invalid",
        )


def _document(core: dict[str, object]) -> dict[str, object]:
    return {**core, "document_digest": evaluator._document_digest(core)}


def _load(path: Path) -> dict[str, object]:
    try:
        value = json.loads(path.read_bytes(), object_pairs_hook=_unique_object)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "bounded capability evidence cannot be loaded",
        ) from exc
    if not isinstance(value, dict):
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "bounded capability evidence must be an object",
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
    "LiveBoundedJavaSourceSemanticsCapabilityCaseRunner",
]
