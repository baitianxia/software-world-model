"""Verify or execute the authorized ITER-006 Java capability qualification."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Mapping, Sequence

from software_world_model.ai_infrastructure import (
    JAVA_WORLD_MODEL_PROPOSAL_CONTRACT,
    ModelGateway,
    ReviewedWorldModelEvaluationCaseExecutor,
    UrllibVolcengineArkChatTransport,
    VolcengineArkChatCompletionsNoToolsAdapter,
    VolcengineArkModelConfiguration,
    WorldModelStrategyConfiguration,
    java_world_model_capability_registry,
    load_ark_chat_conformance_qualification,
    world_model_answer_output_schemas,
    world_model_answer_prompt_program_digest,
    world_model_answer_strategy_implementation_digest,
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
    canonical_json_bytes,
    digest_of,
)
from software_world_model.infrastructure import (
    SqliteCapabilityEvaluationRepository,
    SqliteDatabase,
    SqliteModelGatewayRepository,
)

from .authorize import AUTHORIZATION_SCHEMA
from .freeze import EVALUATOR_PATH, FREEZE_SCHEMA, _candidate_identity
from .live_runner import LiveJavaCapabilityCaseRunner
from .manifest import (
    PINNED_ORACLE_FILE_DIGEST,
    PINNED_ORACLE_REF,
    PINNED_SUITE_FILE_DIGEST,
    PINNED_SUITE_REF,
    build_evaluation_definition,
    case_pairs,
    load_capability_inputs,
)


CLOSED_RESULT_SCHEMA = "swm.iter-006.java-world-model-ce-closed-result@1"
QUALIFICATION_DOCUMENT_SCHEMA = "swm.capability-qualification-proof@1"
INVOCATION_SCHEMA = "swm.iter-006.java-world-model-ce-invocation@1"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    verify = commands.add_parser("verify-freeze")
    verify.add_argument("--freeze", required=True)
    verify.add_argument("--conformance-result", required=True)
    run = commands.add_parser("run")
    run.add_argument("--freeze", required=True)
    run.add_argument("--authorization", required=True)
    run.add_argument("--conformance-result", required=True)
    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    environment: Mapping[str, str] | None = None,
    transport: object | None = None,
) -> int:
    arguments = _parser().parse_args(argv)
    env = os.environ if environment is None else environment
    try:
        freeze = _verify_freeze(
            Path(arguments.freeze), Path(arguments.conformance_result)
        )
        configuration = VolcengineArkModelConfiguration()
        if arguments.command == "verify-freeze":
            payload = {
                "status": "PASS_AWAITING_USER_AUTHORIZATION",
                "freeze_digest": freeze["document_digest"],
                "suite_digest": PINNED_SUITE_FILE_DIGEST,
                "planned_provider_call_count": 8,
                "credential_configured": configuration.credential_configured(env),
                "external_model_called": False,
                "production_activation": "NOT_EXECUTED",
            }
            code = 0
        else:
            payload, code = _run_authorized(
                freeze=freeze,
                authorization_path=Path(arguments.authorization),
                conformance_result_path=Path(arguments.conformance_result),
                environment=env,
                transport=transport,
            )
    except (DomainError, OSError, ValueError, RuntimeError) as exc:
        payload = {
            "status": "ERROR",
            "error": exc.code.value if isinstance(exc, DomainError) else "INVALID_ARGUMENT",
            "message": exc.message if isinstance(exc, DomainError) else str(exc),
            "production_activation": "NOT_EXECUTED",
        }
        code = 2
    print(canonical_json_bytes(payload).decode("utf-8"))
    return code


def _run_authorized(
    *,
    freeze: Mapping[str, object],
    authorization_path: Path,
    conformance_result_path: Path,
    environment: Mapping[str, str],
    transport: object | None,
) -> tuple[dict[str, object], int]:
    authorization = _load_document(authorization_path, AUTHORIZATION_SCHEMA)
    closed = freeze["closed_inputs"]
    dispatch = freeze["dispatch_contract"]
    assert isinstance(closed, Mapping) and isinstance(dispatch, Mapping)
    expected_authorization = {
        "freeze_ref": freeze["freeze_ref"],
        "freeze_digest": freeze["document_digest"],
        "suite_ref": closed["suite_ref"],
        "suite_digest": closed["suite_digest"],
        "destination": dispatch["destination"],
        "planned_provider_call_count": 8,
        "payload_boundary": dispatch["payload_boundary"],
    }
    if (
        authorization.get("status") != "AUTHORIZED"
        or authorization.get("authorized_by") != "user"
        or any(authorization.get(key) != value for key, value in expected_authorization.items())
        or authorization.get("run_003_grant_reused") is not False
        or authorization.get("production_activation") != "NOT_EXECUTED"
        or authorization.get("git_stage_commit_push") != "NOT_EXECUTED"
    ):
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "Java capability authorization is stale or incomplete",
        )
    result_directory = Path(str(authorization["single_use_result_directory"]))
    parent = result_directory.parent.resolve(strict=True)
    if result_directory != parent / result_directory.name:
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "authorized result directory is not canonical",
        )
    result_directory.mkdir(mode=0o700)
    (result_directory / "runtime").mkdir(mode=0o700)
    invocation_core = {
        "schema": INVOCATION_SCHEMA,
        "freeze_digest": freeze["document_digest"],
        "authorization_digest": authorization["document_digest"],
        "authorization_ref": authorization["authorization_ref"],
        "suite_digest": PINNED_SUITE_FILE_DIGEST,
        "oracle_digest": PINNED_ORACLE_FILE_DIGEST,
        "planned_provider_call_count": 8,
        "payload_boundary": dispatch["payload_boundary"],
        "evidence_policy": "PERSIST_BEFORE_FIRST_PROVIDER_DISPATCH",
        "production_activation": "NOT_EXECUTED",
    }
    _write_once(result_directory / "invocation.json", _document(invocation_core))

    configuration = VolcengineArkModelConfiguration()
    conformance = load_ark_chat_conformance_qualification(
        conformance_result_path.resolve(strict=True), configuration
    )
    active_transport = transport or UrllibVolcengineArkChatTransport(
        api_key_resolver=lambda: configuration.resolve_api_key(environment)
    )
    adapter = VolcengineArkChatCompletionsNoToolsAdapter(
        transport=active_transport,
        configuration=configuration,
        output_schemas=world_model_answer_output_schemas(),
        live_qualification=conformance,
    )
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
    suite, oracle = load_capability_inputs()
    outputs = {}
    reviews = {}
    evidence_paths: list[str] = []
    try:
        for case, oracle_case in case_pairs(suite, oracle):
            case_id = str(case["case_id"])
            runtime_path = result_directory / "runtime" / f"{case_id}.sqlite3"
            with SqliteDatabase(runtime_path) as database:
                gateway = ModelGateway(
                    SqliteModelGatewayRepository(database), (adapter,)
                )
                output, review, evidence_path = LiveJavaCapabilityCaseRunner(
                    database=database,
                    gateway=gateway,
                    configuration=strategy_configuration,
                    expected_model_fingerprint=(
                        configuration.actual_model_fingerprint
                    ),
                    result_directory=result_directory,
                ).execute(case=case, oracle_case=oracle_case)
            outputs[case_id] = output
            reviews[case_id] = review
            evidence_paths.append(str(evidence_path))
    except Exception as exc:
        failure_core = {
            "schema": "swm.iter-006.java-world-model-ce-failure@1",
            "freeze_digest": freeze["document_digest"],
            "authorization_digest": authorization["document_digest"],
            "completed_case_count": len(outputs),
            "failure_type": type(exc).__name__,
            "failure_code": (
                exc.code.value if isinstance(exc, DomainError) else "OUTCOME_UNKNOWN"
            ),
            "message": exc.message if isinstance(exc, DomainError) else str(exc),
            "retry_permitted_with_same_authorization": False,
            "production_activation": "NOT_EXECUTED",
        }
        _write_once(result_directory / "failure.json", _document(failure_core))
        raise

    definition = build_evaluation_definition(
        suite,
        oracle,
        conformance_result_ref=conformance.result_ref,
        provider_configuration_fingerprint=configuration.fingerprint,
        actual_model_fingerprint=configuration.actual_model_fingerprint,
        adapter_version=configuration.adapter_version,
        exact_candidate_checkpoint_ref=(
            f"working-tree:{freeze['candidate_identity']['worktree_manifest_digest']}"
        ),
        environment_ref=(
            "iter-006-java-capability-evaluation:"
            f"{freeze['candidate_identity']['worktree_manifest_digest']}"
        ),
        reference_strategy_ref=(
            "standalone-stdlib-evaluator:"
            f"{freeze['closed_inputs']['evaluator_digest']}"
        ),
        resource_policy_ref=(
            "one-call-no-retry:" f"{strategy_configuration.digest.value}"
        ),
        valid_for_seconds=604800,
    )
    if definition.digest.value != freeze["evaluation_definition"]["definition_digest"]:
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "Java capability evaluation definition drifted after authorization",
        )
    executor = ReviewedWorldModelEvaluationCaseExecutor(
        definition=definition, outputs=outputs, reviews=reviews
    )
    with SqliteDatabase(result_directory / "capability-evaluation.sqlite3") as database:
        execution = CapabilityEvaluationRunner(
            CapabilityEvaluationService(
                SqliteCapabilityEvaluationRepository(database),
                java_world_model_capability_registry(),
                conformance,
            )
        ).run_suite(
            definition=definition,
            evaluation_sink_ref=f"files:{result_directory}",
            root_allocation_ref=(
                f"iter-006-java-ce:{freeze['document_digest']}"
            ),
            idempotency_key=IdempotencyKey(
                f"iter-006-java-ce:{authorization['document_digest']}"
            ),
            executor=executor,
            actor="iter-006-java-world-model-capability-owner",
            correlation_ref=CorrelationRef(
                f"iter-006-java-ce:{authorization['document_digest']}"
            ),
            completion_reason="all eight Java world-model capability cases evaluated",
        )
    if execution.completion is None:
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "Java capability evaluation did not reach a closed result",
        )
    completion = execution.completion
    result = completion.result
    validity = completion.validity
    proof = completion.qualification
    result_core = {
        "schema": CLOSED_RESULT_SCHEMA,
        "freeze_digest": freeze["document_digest"],
        "authorization_digest": authorization["document_digest"],
        "suite_ref": PINNED_SUITE_REF,
        "suite_digest": PINNED_SUITE_FILE_DIGEST,
        "oracle_ref": PINNED_ORACLE_REF,
        "oracle_digest": PINNED_ORACLE_FILE_DIGEST,
        "definition": _definition_document(definition),
        "case_evidence_paths": evidence_paths,
        "attempts": [_attempt_document(item) for item in execution.attempts],
        "result": _result_document(result),
        "validity": _validity_document(validity),
        "qualification": _qualification_document(proof) if proof else None,
        "closed_result_status": "PASS_VALID" if proof else "FAIL_OR_INVALID",
        "failure_count": len(result.failed_case_ids),
        "unknown_count": len(result.inconclusive_case_ids),
        "required_case_count": 8,
        "provider_request_count": sum(
            len(item.provider_request_ids) for item in outputs.values()
        ),
        "production_activation": "NOT_EXECUTED",
    }
    result_path = result_directory / "closed-evaluation-result.json"
    _write_once(result_path, _document(result_core, qualified=False))
    qualification_path = None
    if proof is not None:
        qualification_core = {
            "schema": QUALIFICATION_DOCUMENT_SCHEMA,
            "proof": _qualification_document(proof),
        }
        qualification_path = result_directory / "capability-qualification.json"
        _write_once(
            qualification_path,
            {
                **qualification_core,
                "document_digest": digest_of(qualification_core).value,
            },
        )
    passed = (
        proof is not None
        and result.conclusion.value == "PASS"
        and validity.status.value == "VALID"
        and not result.failed_case_ids
        and not result.inconclusive_case_ids
        and len(result.passed_case_ids) == 8
        and result_core["provider_request_count"] == 8
    )
    receipt_core = {
        "schema": "swm.iter-006.java-world-model-ce-terminal@1",
        "status": "PASS" if passed else "FAIL",
        "freeze_digest": freeze["document_digest"],
        "authorization_digest": authorization["document_digest"],
        "closed_result_path": str(result_path),
        "qualification_path": str(qualification_path) if qualification_path else None,
        "provider_request_count": result_core["provider_request_count"],
        "authorization_consumed": True,
        "retry_permitted_with_same_authorization": False,
        "production_activation": "NOT_EXECUTED",
    }
    _write_once(result_directory / "terminal.json", _document(receipt_core))
    return (
        {
            "status": "CAPABILITY_EVALUATION_PASS" if passed else "CAPABILITY_EVALUATION_FAIL",
            "result_path": str(result_path),
            "qualification_path": str(qualification_path) if qualification_path else None,
            "result_id": result.result_id.value,
            "result_digest": result.digest.value,
            "qualification_ref": proof.proof_ref if proof else None,
            "qualification_digest": proof.digest.value if proof else None,
            "case_count": len(execution.attempts),
            "provider_request_count": result_core["provider_request_count"],
            "authorization_consumed": True,
            "production_activation": "NOT_EXECUTED",
        },
        0 if passed else 4,
    )


def _verify_freeze(
    freeze_path: Path, conformance_result_path: Path
) -> dict[str, object]:
    freeze = _load_document(freeze_path, FREEZE_SCHEMA)
    if (
        freeze.get("candidate_identity") != _candidate_identity()
        or freeze.get("external_model_called") is not False
        or freeze.get("production_activation") != "NOT_EXECUTED"
        or freeze.get("closed_inputs", {}).get("suite_digest")
        != PINNED_SUITE_FILE_DIGEST
        or freeze.get("closed_inputs", {}).get("oracle_digest")
        != PINNED_ORACLE_FILE_DIGEST
        or freeze.get("closed_inputs", {}).get("evaluator_digest")
        != "sha256:" + hashlib.sha256(EVALUATOR_PATH.read_bytes()).hexdigest()
        or freeze.get("proposal_contract", {}).get("strategy_ref")
        != JAVA_WORLD_MODEL_PROPOSAL_CONTRACT.strategy_ref
        or freeze.get("proposal_contract", {}).get("strategy_implementation_digest")
        != world_model_answer_strategy_implementation_digest(
            JAVA_WORLD_MODEL_PROPOSAL_CONTRACT
        ).value
        or freeze.get("proposal_contract", {}).get("prompt_program_digest")
        != world_model_answer_prompt_program_digest(
            JAVA_WORLD_MODEL_PROPOSAL_CONTRACT
        ).value
    ):
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "Java capability freeze drifted from the current candidate",
        )
    configuration = VolcengineArkModelConfiguration()
    conformance = load_ark_chat_conformance_qualification(
        conformance_result_path.resolve(strict=True), configuration
    )
    provider = freeze.get("provider")
    if (
        not isinstance(provider, Mapping)
        or provider.get("conformance_result_ref") != conformance.result_ref
        or provider.get("conformance_result_digest")
        != conformance.result_digest.value
        or provider.get("configuration_fingerprint")
        != configuration.fingerprint.value
    ):
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "Java capability conformance binding drifted",
        )
    load_capability_inputs()
    return freeze


def _load_document(path: Path, schema: str) -> dict[str, object]:
    try:
        value = json.loads(path.read_bytes(), object_pairs_hook=_unique_object)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID, "sealed Java capability document cannot be loaded"
        ) from exc
    if not isinstance(value, dict) or value.get("schema") != schema:
        raise DomainError(ErrorCode.QUALIFICATION_INVALID, "sealed document schema is invalid")
    core = {key: item for key, item in value.items() if key != "document_digest"}
    if value.get("document_digest") != digest_of([schema, core]).value:
        raise DomainError(ErrorCode.QUALIFICATION_INVALID, "sealed document digest is invalid")
    return value


def _document(
    core: dict[str, object], *, qualified: bool = True
) -> dict[str, object]:
    digest = digest_of([core["schema"], core]) if qualified else digest_of(core)
    return {**core, "document_digest": digest.value}


def _write_once(path: Path, value: object) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        remaining = memoryview(canonical_json_bytes(value))
        while remaining:
            remaining = remaining[os.write(descriptor, remaining) :]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


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
        "provider_configuration_fingerprint": value.provider_configuration_fingerprint.value,
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
        "digest": value.digest.value,
        "definition_digest": value.digest.value,
    }


def _attempt_document(value) -> dict[str, object]:
    return {
        "attempt_id": value.attempt_id.value,
        "case_id": value.case_id,
        "state": value.state.value,
        "conclusion": value.conclusion.value if value.conclusion else None,
        "output_ref": value.output_ref,
        "output_digest": value.output_digest.value if value.output_digest else None,
        "sink_manifest_ref": value.sink_manifest_ref,
        "sink_manifest_digest": value.sink_manifest_digest.value if value.sink_manifest_digest else None,
        "oracle_ref": value.oracle_ref,
        "oracle_digest": value.oracle_digest.value if value.oracle_digest else None,
        "actual_model_fingerprint": value.actual_model_fingerprint,
        "provider_request_id": value.provider_request_id,
        "input_tokens": value.input_tokens,
        "output_tokens": value.output_tokens,
        "usage_complete": value.usage_complete,
        "failure_code": value.failure_code,
    }


def _result_document(value) -> dict[str, object]:
    return {
        "result_id": value.result_id.value,
        "run_id": value.run_id.value,
        "definition_digest": value.definition_digest.value,
        "conclusion": value.conclusion.value,
        "case_attempt_ids": [item.value for item in value.case_attempt_ids],
        "passed_case_ids": list(value.passed_case_ids),
        "failed_case_ids": list(value.failed_case_ids),
        "inconclusive_case_ids": list(value.inconclusive_case_ids),
        "actual_model_fingerprints": list(value.actual_model_fingerprints),
        "input_tokens": value.input_tokens,
        "output_tokens": value.output_tokens,
        "completed_at": value.completed_at.isoformat(),
        "digest": value.digest.value,
    }


def _validity_document(value) -> dict[str, object]:
    return {
        "validity_id": value.validity_id.value,
        "result_id": value.result_id.value,
        "revision": value.revision.value,
        "status": value.status.value,
        "dependency_digest": value.dependency_digest.value,
        "valid_until": value.valid_until.isoformat(),
        "authority": value.authority,
        "reason": value.reason,
        "decided_at": value.decided_at.isoformat(),
        "digest": value.digest.value,
    }


def _qualification_document(value) -> dict[str, object]:
    return {**value.core(), "digest": value.digest.value}


if __name__ == "__main__":
    raise SystemExit(main())
