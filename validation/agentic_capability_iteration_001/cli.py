"""Commands for live six-role capability evaluation and independent review."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
from typing import Mapping, Sequence, TextIO

from software_world_model.ai_infrastructure import (
    AgenticEvaluationRole,
    AgenticModelStrategyConfiguration,
    ModelGateway,
    ReviewedAgenticEvaluationCaseExecutor,
    UrllibVolcengineArkChatTransport,
    VolcengineArkChatCompletionsNoToolsAdapter,
    VolcengineArkModelConfiguration,
    agentic_knowledge_output_schemas,
    load_ark_chat_conformance_qualification,
)
from software_world_model.application_services import (
    CapabilityEvaluationRunner,
    CapabilityEvaluationService,
)
from software_world_model.cross_cutting import (
    CorrelationRef,
    DomainError,
    ErrorCode,
    IdempotencyKey,
    digest_of,
)
from software_world_model.infrastructure import (
    SqliteCapabilityEvaluationRepository,
    SqliteDatabase,
    SqliteModelGatewayRepository,
)
from software_world_model.interface.agentic_runtime import (
    agentic_task_capability_registry,
)

from .live_runner import (
    LiveCapabilityCaseRunner,
    load_capability_output_document,
    save_capability_output_document,
    verify_capability_output_against_suite,
    write_capability_document_once,
)
from .manifest import (
    build_capability_definition,
    load_capability_suite,
)
from .review import (
    CAPABILITY_REVIEW_DRAFT_SCHEMA,
    load_capability_review_document,
    seal_capability_review_draft,
)


QUALIFICATION_DOCUMENT_SCHEMA = "swm.capability-qualification-proof@1"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m validation.agentic_capability_iteration_001.cli",
        description="Run and independently review all six model strategy roles",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("verify-inputs")

    run = commands.add_parser("run-case")
    run.add_argument(
        "--role", required=True, choices=[item.value for item in AgenticEvaluationRole]
    )
    run.add_argument("--conformance-result", required=True)
    run.add_argument("--result-directory", required=True)
    run.add_argument("--timeout-milliseconds", type=int, default=180000)
    run.add_argument("--max-output-tokens", type=int, default=1200)

    run_all = commands.add_parser("run-all")
    run_all.add_argument("--conformance-result", required=True)
    run_all.add_argument("--result-directory", required=True)
    run_all.add_argument("--timeout-milliseconds", type=int, default=180000)
    run_all.add_argument("--max-output-tokens", type=int, default=1200)

    prepare_review = commands.add_parser("prepare-review")
    prepare_review.add_argument("--output", required=True)
    prepare_review.add_argument("--result-directory", required=True)

    review = commands.add_parser("seal-review")
    review.add_argument("--output", required=True)
    review.add_argument("--review-draft", required=True)
    review.add_argument("--result-directory", required=True)

    finalize = commands.add_parser("finalize")
    finalize.add_argument("--conformance-result", required=True)
    finalize.add_argument("--evidence-directory", required=True)
    finalize.add_argument("--evaluation-database", required=True)
    finalize.add_argument("--result-directory", required=True)
    finalize.add_argument("--valid-for-seconds", type=int, default=604800)
    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    stdout: TextIO | None = None,
    environment: Mapping[str, str] | None = None,
    transport: object | None = None,
) -> int:
    output = stdout or sys.stdout
    arguments = build_parser().parse_args(argv)
    environment_values = os.environ if environment is None else environment
    try:
        suite = load_capability_suite()
        if arguments.command == "verify-inputs":
            payload = {
                "status": "PASS",
                "suite_id": suite["suite_id"],
                "suite_version": suite["suite_version"],
                "suite_digest": suite["suite_digest"],
                "role_count": len(suite["cases"]),
                "external_model_called": False,
            }
        elif arguments.command == "run-case":
            payload = _run_case(
                arguments,
                suite=suite,
                environment=environment_values,
                transport=transport,
            )
        elif arguments.command == "run-all":
            results = []
            for role in AgenticEvaluationRole:
                role_arguments = argparse.Namespace(
                    **{**vars(arguments), "role": role.value}
                )
                results.append(
                    _run_case(
                        role_arguments,
                        suite=suite,
                        environment=environment_values,
                        transport=transport,
                    )
                )
            payload = {
                "status": "ALL_OUTPUTS_SEALED",
                "case_count": len(results),
                "cases": results,
                "requires_independent_review": True,
                "production_eligible": False,
            }
        elif arguments.command == "prepare-review":
            payload = _prepare_review(arguments, suite=suite)
        elif arguments.command == "seal-review":
            path = seal_capability_review_draft(
                arguments.review_draft,
                output_path=arguments.output,
                suite=suite,
                result_directory=arguments.result_directory,
            )
            payload = {
                "status": "SEALED",
                "review_path": str(path),
                "production_eligible": False,
            }
        else:
            payload = _finalize(arguments, suite=suite)
        json.dump(payload, output, ensure_ascii=False, sort_keys=True)
        output.write("\n")
        return 0
    except (DomainError, OSError, ValueError) as exc:
        payload = {
            "error": (
                exc.code.value if isinstance(exc, DomainError) else "INVALID_ARGUMENT"
            ),
            "message": exc.message if isinstance(exc, DomainError) else str(exc),
        }
        json.dump(payload, output, ensure_ascii=False, sort_keys=True)
        output.write("\n")
        return 2


def _run_case(
    arguments: argparse.Namespace,
    *,
    suite: Mapping[str, object],
    environment: Mapping[str, str],
    transport: object | None,
) -> dict[str, object]:
    if arguments.timeout_milliseconds < 1 or arguments.max_output_tokens < 1:
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            "capability case resource limits must be positive",
        )
    role = AgenticEvaluationRole(arguments.role)
    configuration = VolcengineArkModelConfiguration()
    conformance = load_ark_chat_conformance_qualification(
        arguments.conformance_result, configuration
    )
    active_transport = transport or UrllibVolcengineArkChatTransport(
        api_key_resolver=lambda: configuration.resolve_api_key(environment)
    )
    adapter = VolcengineArkChatCompletionsNoToolsAdapter(
        transport=active_transport,
        configuration=configuration,
        output_schemas=agentic_knowledge_output_schemas(),
        live_qualification=conformance,
    )
    case = next(item for item in suite["cases"] if item["role"] == role.value)
    runtime = (
        Path(arguments.result_directory)
        / "runtime"
        / f"{role.value.lower()}--{case['case_id']}.sqlite3"
    )
    runtime.parent.mkdir(parents=True, exist_ok=True)
    with SqliteDatabase(runtime) as database:
        gateway = ModelGateway(
            SqliteModelGatewayRepository(database), (adapter,)
        )
        runner = LiveCapabilityCaseRunner(
            database=database,
            gateway=gateway,
            configuration=AgenticModelStrategyConfiguration(
                provider_type=configuration.provider_type,
                adapter_version=configuration.adapter_version,
                model_ref=configuration.model_ref,
                provider_configuration_fingerprint=configuration.fingerprint,
                qualification_ref=f"evaluation-only:{conformance.result_ref}",
                max_output_tokens=arguments.max_output_tokens,
                timeout_milliseconds=arguments.timeout_milliseconds,
                classification="INTERNAL",
            ),
            expected_model_fingerprint=configuration.actual_model_fingerprint,
        )
        evaluation_output, document = runner.execute(suite=suite, role=role)
    path = save_capability_output_document(
        document, Path(arguments.result_directory) / "outputs"
    )
    return {
        "status": "SEALED_OUTPUT",
        "case_id": evaluation_output.case_id,
        "role": role.value,
        "output_path": str(path),
        "output_digest": evaluation_output.output_digest.value,
        "actual_model_fingerprint": evaluation_output.actual_model_fingerprint,
        "provider_request_ids": evaluation_output.provider_request_ids,
        "input_tokens": evaluation_output.input_tokens,
        "output_tokens": evaluation_output.output_tokens,
        "requires_independent_review": True,
        "production_eligible": False,
    }


def _prepare_review(
    arguments: argparse.Namespace, *, suite: Mapping[str, object]
) -> dict[str, object]:
    case_output, document = load_capability_output_document(arguments.output)
    verify_capability_output_against_suite(case_output, document, suite)
    template = {
        "schema": CAPABILITY_REVIEW_DRAFT_SCHEMA,
        "suite_digest": suite["suite_digest"],
        "case_id": case_output.case_id,
        "output_digest": case_output.output_digest.value,
        "reviewer_identity": None,
        "reviewer_origin": None,
        "platform_contract_valid": None,
        "oracle_match": None,
        "unauthorized_reference_count": None,
        "material_omission_count": None,
        "material_error_count": None,
        "findings": [],
        "reviewed_at": None,
    }
    target = Path(arguments.result_directory) / (
        f"{case_output.case_id.replace(':', '--')}--review-draft.json"
    )
    _write_same_or_new(target, template)
    return {
        "status": "REVIEW_TEMPLATE_PREPARED",
        "case_id": case_output.case_id,
        "review_draft_path": str(target),
        "judgement_recorded": False,
        "production_eligible": False,
    }


def _finalize(
    arguments: argparse.Namespace, *, suite: Mapping[str, object]
) -> dict[str, object]:
    configuration = VolcengineArkModelConfiguration()
    conformance = load_ark_chat_conformance_qualification(
        arguments.conformance_result, configuration
    )
    definition = build_capability_definition(
        suite,
        conformance_result_ref=conformance.result_ref,
        provider_configuration_fingerprint=configuration.fingerprint,
        actual_model_fingerprint=configuration.actual_model_fingerprint,
        adapter_version=configuration.adapter_version,
        valid_for_seconds=arguments.valid_for_seconds,
    )
    evidence = Path(arguments.evidence_directory)
    outputs = {}
    reviews = {}
    reviewer_origins = set()
    for frozen_case in definition.cases:
        output_path = evidence / "outputs" / f"{frozen_case.case_id.replace(':', '--')}.json"
        review_path = evidence / "reviews" / f"{frozen_case.case_id.replace(':', '--')}--review.json"
        output, output_document = load_capability_output_document(output_path)
        _verify_runtime_binding(
            output_document,
            configuration=configuration,
            conformance=conformance,
        )
        review, _ = load_capability_review_document(
            review_path,
            output_path=output_path,
            suite=suite,
        )
        outputs[frozen_case.case_id] = output
        reviews[frozen_case.case_id] = review
        reviewer_origins.add(review.reviewer_origin)
    if len(reviewer_origins) != 1:
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "one capability evaluation must use one stable independent reviewer origin",
        )
    executor = ReviewedAgenticEvaluationCaseExecutor(
        definition=definition,
        outputs=outputs,
        reviews=reviews,
    )
    with SqliteDatabase(arguments.evaluation_database) as database:
        result = CapabilityEvaluationRunner(
            CapabilityEvaluationService(
                SqliteCapabilityEvaluationRepository(database),
                agentic_task_capability_registry(),
                conformance,
            )
        ).run_suite(
            definition=definition,
            evaluation_sink_ref=f"files:{evidence.resolve()}",
            root_allocation_ref=f"capability-suite:{suite['suite_digest']}",
            idempotency_key=IdempotencyKey(
                f"agentic-capability:{suite['suite_digest']}:{conformance.result_digest.value}"
            ),
            executor=executor,
            actor="capability-evaluation-owner",
            correlation_ref=CorrelationRef(
                f"agentic-capability:{suite['suite_id']}"
            ),
            completion_reason="all six roles independently reviewed",
        )
    completion = result.completion
    if completion is None or completion.qualification is None:
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "capability evaluation did not produce a qualification",
        )
    proof = completion.qualification
    core = {
        "schema": QUALIFICATION_DOCUMENT_SCHEMA,
        "proof": {**proof.core(), "digest": proof.digest.value},
    }
    document = {**core, "document_digest": digest_of(core).value}
    qualification_path = Path(arguments.result_directory) / "capability-qualification.json"
    _write_same_or_new(qualification_path, document)
    return {
        "status": "CAPABILITY_EVALUATION_PASS",
        "result_id": completion.result.result_id.value,
        "qualification_ref": proof.proof_ref,
        "qualification_digest": proof.digest.value,
        "qualification_path": str(qualification_path),
        "valid_until": completion.validity.valid_until.isoformat(),
        "case_count": len(result.attempts),
        "production_eligible": False,
    }


def _verify_runtime_binding(
    document: Mapping[str, object],
    *,
    configuration: VolcengineArkModelConfiguration,
    conformance: object,
) -> None:
    manifests = document.get("authorized_manifests")
    receipts = document.get("isolation_receipts")
    outcomes = document.get("model_call_outcomes")
    if (
        not isinstance(manifests, list)
        or not isinstance(receipts, list)
        or not isinstance(outcomes, list)
        or len(manifests) != len(receipts)
        or len(manifests) != len(outcomes)
        or not manifests
    ):
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "capability output model-call audit is incomplete",
        )
    expected_qualification = f"evaluation-only:{conformance.result_ref}"
    request_ids = set()
    for manifest, receipt, outcome in zip(
        manifests, receipts, outcomes, strict=True
    ):
        if (
            not isinstance(manifest, dict)
            or not isinstance(receipt, dict)
            or not isinstance(outcome, dict)
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "capability output model-call audit entry is invalid",
            )
        qualification_items = [
            item
            for item in manifest.get("items", [])
            if isinstance(item, dict) and item.get("item_id") == "qualification"
        ]
        if (
            manifest.get("model_call_id") != receipt.get("model_call_id")
            or manifest.get("model_call_id") != outcome.get("model_call_id")
            or manifest.get("digest") != receipt.get("manifest_digest")
            or receipt.get("provider_type") != configuration.provider_type
            or receipt.get("adapter_version") != configuration.adapter_version
            or receipt.get("provider_configuration_fingerprint")
            != configuration.fingerprint.value
            or receipt.get("conformance_result_ref") != conformance.result_ref
            or receipt.get("runtime_access_mode") != "NO_EXTERNAL_ACCESS"
            or len(qualification_items) != 1
            or qualification_items[0].get("content") != expected_qualification
            or qualification_items[0].get("authority_reference")
            != expected_qualification
            or outcome.get("actual_model_fingerprint")
            != configuration.actual_model_fingerprint
            or not isinstance(outcome.get("provider_request_id"), str)
            or not outcome.get("provider_request_id")
            or outcome.get("provider_request_id") in request_ids
            or outcome.get("usage_complete") is not True
            or not isinstance(outcome.get("input_tokens"), int)
            or not isinstance(outcome.get("output_tokens"), int)
            or outcome.get("failure_code")
            not in (None, ErrorCode.STRUCTURED_OUTPUT_INVALID.value)
        ):
            raise DomainError(
                ErrorCode.QUALIFICATION_INVALID,
                "capability output was not produced under the current interface qualification",
            )
        request_ids.add(outcome["provider_request_id"])


def _write_same_or_new(path: Path, document: Mapping[str, object]) -> None:
    write_capability_document_once(path, document)


if __name__ == "__main__":
    raise SystemExit(main())
