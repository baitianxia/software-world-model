"""Run, review, and finalize evidence-first capability evaluation."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

from software_world_model.ai_infrastructure import (
    EvidenceEvaluationRole,
    AgenticModelStrategyConfiguration,
    ModelGateway,
    ReviewedAgenticEvaluationCaseExecutor,
    UrllibVolcengineArkChatTransport,
    VolcengineArkChatCompletionsNoToolsAdapter,
    VolcengineArkModelConfiguration,
    evidence_first_task_output_schemas,
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
    evidence_task_capability_registry,
)
from validation.agentic_capability_iteration_001.cli import (
    QUALIFICATION_DOCUMENT_SCHEMA,
    _verify_runtime_binding,
)
from validation.agentic_capability_iteration_001.live_runner import (
    write_capability_document_once,
)

from .live_runner import (
    LiveCapabilityCaseRunner,
    load_capability_output_document,
    save_capability_output_document,
    verify_capability_output_against_suite,
)
from .manifest import build_capability_definition, load_capability_suite
from .review import (
    CAPABILITY_REVIEW_DRAFT_SCHEMA,
    load_capability_review_document,
    seal_capability_review_draft,
)


def parser():
    value = argparse.ArgumentParser(
        prog="python -m validation.evidence_answer_capability_iteration_002.cli"
    )
    commands = value.add_subparsers(dest="command", required=True)
    commands.add_parser("verify-inputs")
    run = commands.add_parser("run-case")
    run.add_argument("--role", required=True, choices=[x.value for x in EvidenceEvaluationRole])
    run.add_argument("--conformance-result", required=True)
    run.add_argument("--result-directory", required=True)
    run.add_argument("--timeout-milliseconds", type=int, default=180000)
    run.add_argument("--max-output-tokens", type=int, default=1600)
    run_all = commands.add_parser("run-all")
    run_all.add_argument("--conformance-result", required=True)
    run_all.add_argument("--result-directory", required=True)
    run_all.add_argument("--timeout-milliseconds", type=int, default=180000)
    run_all.add_argument("--max-output-tokens", type=int, default=1600)
    prepare = commands.add_parser("prepare-review")
    prepare.add_argument("--output", required=True)
    prepare.add_argument("--result-directory", required=True)
    seal = commands.add_parser("seal-review")
    seal.add_argument("--output", required=True)
    seal.add_argument("--review-draft", required=True)
    seal.add_argument("--result-directory", required=True)
    finalize = commands.add_parser("finalize")
    finalize.add_argument("--conformance-result", required=True)
    finalize.add_argument("--evidence-directory", required=True)
    finalize.add_argument("--evaluation-database", required=True)
    finalize.add_argument("--result-directory", required=True)
    finalize.add_argument("--valid-for-seconds", type=int, default=604800)
    return value


def main(argv=None, *, stdout=None, environment=None, transport=None):
    output = stdout or sys.stdout
    arguments = parser().parse_args(argv)
    environment_values = os.environ if environment is None else environment
    try:
        suite = load_capability_suite()
        if arguments.command == "verify-inputs":
            payload = {
                "status": "PASS",
                "suite_id": suite["suite_id"],
                "suite_digest": suite["suite_digest"],
                "role_count": len(suite["cases"]),
                "external_model_called": False,
            }
        elif arguments.command in {"run-case", "run-all"}:
            roles = (
                (EvidenceEvaluationRole(arguments.role),)
                if arguments.command == "run-case"
                else tuple(EvidenceEvaluationRole)
            )
            results = [
                _run_case(
                    arguments,
                    suite=suite,
                    role=role,
                    environment=environment_values,
                    transport=transport,
                )
                for role in roles
            ]
            payload = (
                results[0]
                if arguments.command == "run-case"
                else {
                    "status": "ALL_OUTPUTS_SEALED",
                    "case_count": len(results),
                    "cases": results,
                    "requires_independent_review": True,
                    "production_eligible": False,
                }
            )
        elif arguments.command == "prepare-review":
            case_output, _ = load_capability_output_document(arguments.output)
            target = Path(arguments.result_directory) / (
                case_output.case_id.replace(":", "--") + "--review-draft.json"
            )
            document = {
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
            write_capability_document_once(target, document)
            payload = {"status": "REVIEW_TEMPLATE_PREPARED", "review_draft_path": str(target)}
        elif arguments.command == "seal-review":
            target = seal_capability_review_draft(
                arguments.review_draft,
                output_path=arguments.output,
                suite=suite,
                result_directory=arguments.result_directory,
            )
            payload = {"status": "SEALED", "review_path": str(target)}
        else:
            payload = _finalize(arguments, suite)
        json.dump(payload, output, ensure_ascii=False, sort_keys=True)
        output.write("\n")
        return 0
    except (DomainError, OSError, ValueError) as exc:
        json.dump(
            {
                "error": exc.code.value if isinstance(exc, DomainError) else "INVALID_ARGUMENT",
                "message": exc.message if isinstance(exc, DomainError) else str(exc),
            },
            output,
            ensure_ascii=False,
            sort_keys=True,
        )
        output.write("\n")
        return 2


def _run_case(arguments, *, suite, role, environment, transport):
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
        output_schemas=evidence_first_task_output_schemas(),
        live_qualification=conformance,
    )
    case = next(item for item in suite["cases"] if item["role"] == role.value)
    runtime = Path(arguments.result_directory) / "runtime" / f"{role.value.lower()}--{case['case_id']}.sqlite3"
    runtime.parent.mkdir(parents=True, exist_ok=True)
    with SqliteDatabase(runtime) as database:
        gateway = ModelGateway(SqliteModelGatewayRepository(database), (adapter,))
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
    }


def _finalize(arguments, suite):
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
    for case in definition.cases:
        stem = case.case_id.replace(":", "--")
        output_path = evidence / "outputs" / f"{stem}.json"
        output, document = load_capability_output_document(output_path)
        verify_capability_output_against_suite(output, document, suite)
        _verify_runtime_binding(document, configuration=configuration, conformance=conformance)
        review, _ = load_capability_review_document(
            evidence / "reviews" / f"{stem}--review.json",
            output_path=output_path,
            suite=suite,
        )
        outputs[case.case_id] = output
        reviews[case.case_id] = review
    executor = ReviewedAgenticEvaluationCaseExecutor(
        definition=definition, outputs=outputs, reviews=reviews
    )
    with SqliteDatabase(arguments.evaluation_database) as database:
        result = CapabilityEvaluationRunner(
            CapabilityEvaluationService(
                SqliteCapabilityEvaluationRepository(database),
                evidence_task_capability_registry(),
                conformance,
            )
        ).run_suite(
            definition=definition,
            evaluation_sink_ref=f"files:{evidence.resolve()}",
            root_allocation_ref=f"evidence-capability:{suite['suite_digest']}",
            idempotency_key=IdempotencyKey(
                f"evidence-capability:{suite['suite_digest']}:{conformance.result_digest.value}"
            ),
            executor=executor,
            actor="evidence-capability-owner",
            correlation_ref=CorrelationRef(f"evidence-capability:{suite['suite_id']}"),
            completion_reason="all evidence-first roles independently reviewed",
        )
    completion = result.completion
    if completion is None or completion.qualification is None:
        raise DomainError(ErrorCode.QUALIFICATION_INVALID, "evidence capability did not qualify")
    proof = completion.qualification
    core = {"schema": QUALIFICATION_DOCUMENT_SCHEMA, "proof": {**proof.core(), "digest": proof.digest.value}}
    document = {**core, "document_digest": digest_of(core).value}
    path = Path(arguments.result_directory) / "capability-qualification.json"
    write_capability_document_once(path, document)
    return {
        "status": "CAPABILITY_EVALUATION_PASS",
        "result_id": completion.result.result_id.value,
        "qualification_ref": proof.proof_ref,
        "qualification_digest": proof.digest.value,
        "qualification_path": str(path),
        "valid_until": completion.validity.valid_until.isoformat(),
        "case_count": len(result.attempts),
    }


if __name__ == "__main__":
    raise SystemExit(main())
