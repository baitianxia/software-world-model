"""Verify and execute ITER-003 V-009 closed capability evaluation."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Mapping, Sequence, TextIO

from software_world_model.ai_infrastructure import (
    ModelGateway,
    ProviderOutcomeUnknown,
    ReviewedWorldModelEvaluationCaseExecutor,
    UrllibVolcengineArkChatTransport,
    VolcengineArkChatCompletionsNoToolsAdapter,
    VolcengineArkModelConfiguration,
    WorldModelStrategyConfiguration,
    load_ark_chat_conformance_qualification,
    run_ark_chat_conformance,
    seal_ark_chat_conformance_result,
    world_model_answer_output_schemas,
    world_model_capability_registry,
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

from .inputs import (
    DEFAULT_INPUT_FREEZE_PATH,
    load_input_freeze,
    verify_input_freeze_runtime,
)
from .live_runner import (
    LiveWorldModelCapabilityCaseRunner,
    write_document_once,
)
from .manifest import (
    PINNED_SUITE_FILE_DIGEST,
    build_evaluation_definition,
    load_capability_suite,
)


CLOSED_RESULT_SCHEMA = "swm.iter-003.world-model-ce-closed-result@1"
QUALIFICATION_DOCUMENT_SCHEMA = "swm.capability-qualification-proof@1"
CONFORMANCE_INVOCATION_SCHEMA = "swm.iter-003.v009-conformance-invocation@1"
CONFORMANCE_BINDING_SCHEMA = "swm.iter-003.v009-conformance-binding@1"
CONFORMANCE_UNKNOWN_SCHEMA = "swm.iter-003.v009-conformance-unknown@1"
REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(
        prog="python -m validation.structure_world_model_iteration_003.v009.cli"
    )
    commands = value.add_subparsers(dest="command", required=True)
    verify = commands.add_parser("verify-inputs")
    verify.add_argument("--input-freeze", default=str(DEFAULT_INPUT_FREEZE_PATH))
    conformance = commands.add_parser("run-conformance")
    conformance.add_argument(
        "--input-freeze", default=str(DEFAULT_INPUT_FREEZE_PATH)
    )
    conformance.add_argument("--result-directory", required=True)
    conformance.add_argument("--freeze-checkpoint", required=True)
    run = commands.add_parser("run-all")
    run.add_argument("--input-freeze", default=str(DEFAULT_INPUT_FREEZE_PATH))
    run.add_argument("--conformance-binding", required=True)
    run.add_argument("--result-directory", required=True)
    run.add_argument("--freeze-checkpoint", required=True)
    run.add_argument("--valid-for-seconds", type=int, default=604_800)
    return value


def main(
    argv: Sequence[str] | None = None,
    *,
    stdout: TextIO | None = None,
    environment: Mapping[str, str] | None = None,
    transport: object | None = None,
    repository_state: Mapping[str, object] | None = None,
) -> int:
    output = stdout or sys.stdout
    arguments = parser().parse_args(argv)
    environment_values = os.environ if environment is None else environment
    try:
        suite = load_capability_suite()
        frozen = load_input_freeze(arguments.input_freeze)
        configuration = VolcengineArkModelConfiguration()
        state = dict(repository_state or current_repository_state())
        verify_input_freeze_runtime(
            frozen,
            configuration=configuration,
            repository_state=state,
            environment=environment_values,
        )
        if arguments.command == "verify-inputs":
            payload = {
                "status": "PASS",
                "external_model_called": False,
                "disclosure_confirmation_ref": frozen["disclosure"][
                    "confirmation_ref"
                ],
                "g3a_checkpoint": frozen["g3a"]["commit"],
                "current_checkpoint": state["head"],
                "suite_ref": suite["suite_ref"],
                "suite_digest": PINNED_SUITE_FILE_DIGEST,
                "provider_type": configuration.provider_type,
                "adapter_version": configuration.adapter_version,
                "model_ref": configuration.model_ref,
                "actual_model_fingerprint": configuration.actual_model_fingerprint,
                "endpoint": configuration.endpoint,
                "credential_reference": configuration.secret_reference,
                "credential_configured": configuration.credential_configured(
                    environment_values
                ),
                "input_freeze_digest": frozen["_file_digest"],
            }
            exit_code = 0
        elif arguments.command == "run-conformance":
            _verify_freeze_checkpoint(arguments.freeze_checkpoint, state)
            payload, exit_code = _run_conformance(
                arguments,
                frozen=frozen,
                configuration=configuration,
                environment=environment_values,
                transport=transport,
                repository_state=state,
            )
        else:
            if arguments.valid_for_seconds != frozen["capability_evaluation"][
                "valid_for_seconds"
            ]:
                raise DomainError(
                    ErrorCode.QUALIFICATION_INVALID,
                    "capability validity duration differs from the frozen input",
                )
            _verify_freeze_checkpoint(arguments.freeze_checkpoint, state)
            payload, exit_code = _run_all(
                arguments,
                suite=suite,
                frozen=frozen,
                configuration=configuration,
                environment=environment_values,
                transport=transport,
                repository_state=state,
            )
        json.dump(payload, output, ensure_ascii=False, sort_keys=True)
        output.write("\n")
        return exit_code
    except (DomainError, OSError, ValueError, json.JSONDecodeError) as exc:
        payload = {
            "status": "ERROR",
            "error": exc.code.value if isinstance(exc, DomainError) else "INVALID_ARGUMENT",
            "message": exc.message if isinstance(exc, DomainError) else str(exc),
        }
        if isinstance(exc, DomainError):
            for key in (
                "eligibility_reason",
                "model_failure_code",
                "evaluator_exit_code",
            ):
                if key in exc.details:
                    payload[key] = exc.details[key]
        json.dump(payload, output, ensure_ascii=False, sort_keys=True)
        output.write("\n")
        return 2


def _run_all(
    arguments,
    *,
    suite: Mapping[str, object],
    frozen: Mapping[str, object],
    configuration: VolcengineArkModelConfiguration,
    environment: Mapping[str, str],
    transport: object | None,
    repository_state: Mapping[str, object],
) -> tuple[dict[str, object], int]:
    conformance, conformance_binding = _load_bound_conformance(
        arguments.conformance_binding,
        frozen=frozen,
        configuration=configuration,
        freeze_checkpoint=arguments.freeze_checkpoint,
        freeze_tree=str(repository_state["tree"]),
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
    result_directory = Path(arguments.result_directory).resolve()
    result_directory.mkdir(parents=True, exist_ok=False)
    (result_directory / "runtime").mkdir()
    strategy_settings = frozen["strategy"]["configuration"]
    strategy_configuration = WorldModelStrategyConfiguration(
        provider_type=configuration.provider_type,
        adapter_version=configuration.adapter_version,
        model_ref=configuration.model_ref,
        provider_configuration_fingerprint=configuration.fingerprint,
        qualification_ref=f"evaluation-only:{conformance.result_ref}",
        max_output_tokens=int(strategy_settings["max_output_tokens"]),
        timeout_milliseconds=int(strategy_settings["timeout_milliseconds"]),
        classification=str(strategy_settings["classification"]),
    )

    outputs = {}
    reviews = {}
    evidence_paths: list[str] = []
    raw_cases = suite["cases"]
    assert isinstance(raw_cases, list)
    for case in raw_cases:
        case_id = str(case["case_id"])
        runtime_path = result_directory / "runtime" / f"{case_id}.sqlite3"
        with SqliteDatabase(runtime_path) as database:
            gateway = ModelGateway(
                SqliteModelGatewayRepository(database),
                (adapter,),
            )
            runner = LiveWorldModelCapabilityCaseRunner(
                database=database,
                gateway=gateway,
                configuration=strategy_configuration,
                expected_model_fingerprint=configuration.actual_model_fingerprint,
                result_directory=result_directory,
            )
            evaluated_output, review, evidence_path = runner.execute(
                suite=suite,
                case=case,
            )
        outputs[case_id] = evaluated_output
        reviews[case_id] = review
        evidence_paths.append(str(evidence_path))

    definition = build_evaluation_definition(
        suite,
        conformance_result_ref=conformance.result_ref,
        provider_configuration_fingerprint=configuration.fingerprint,
        actual_model_fingerprint=configuration.actual_model_fingerprint,
        adapter_version=configuration.adapter_version,
        exact_g3a_checkpoint_ref=f"git:{frozen['g3a']['commit']}",
        environment_ref=(
            f"git:{arguments.freeze_checkpoint}:"
            f"egress:{frozen['egress_policy']['file_digest']}:"
            f"conformance-binding:{conformance_binding['document_digest']}"
        ),
        reference_strategy_ref=(
            "standalone-stdlib-evaluator:"
            f"{frozen['capability_evaluation']['evaluator_file_digest']}"
        ),
        resource_policy_ref=(
            "one-call-no-retry:"
            f"{strategy_configuration.digest.value}"
        ),
        valid_for_seconds=arguments.valid_for_seconds,
    )
    executor = ReviewedWorldModelEvaluationCaseExecutor(
        definition=definition,
        outputs=outputs,
        reviews=reviews,
    )
    evaluation_database = result_directory / "capability-evaluation.sqlite3"
    with SqliteDatabase(evaluation_database) as database:
        execution = CapabilityEvaluationRunner(
            CapabilityEvaluationService(
                SqliteCapabilityEvaluationRepository(database),
                world_model_capability_registry(),
                conformance,
            )
        ).run_suite(
            definition=definition,
            evaluation_sink_ref=f"files:{result_directory}",
            root_allocation_ref=(
                f"iter-003-v009:{arguments.freeze_checkpoint}:"
                f"{PINNED_SUITE_FILE_DIGEST}"
            ),
            idempotency_key=IdempotencyKey(
                "iter-003-v009:"
                f"{arguments.freeze_checkpoint}:"
                f"{conformance.result_digest.value}"
            ),
            executor=executor,
            actor="iter-003-world-model-capability-owner",
            correlation_ref=CorrelationRef(
                f"iter-003-v009:{arguments.freeze_checkpoint}"
            ),
            completion_reason="all seven closed world-model capability cases evaluated",
        )
    completion = execution.completion
    if completion is None:
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "world-model capability evaluation did not reach a closed Result",
        )
    result = completion.result
    validity = completion.validity
    proof = completion.qualification
    result_core = {
        "schema": CLOSED_RESULT_SCHEMA,
        "input_freeze_ref": frozen["freeze_ref"],
        "input_freeze_digest": frozen["_file_digest"],
        "freeze_checkpoint": arguments.freeze_checkpoint,
        "g3a_checkpoint": frozen["g3a"]["commit"],
        "disclosure_confirmation_ref": frozen["disclosure"]["confirmation_ref"],
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
            "conformance_binding_digest": conformance_binding["document_digest"],
        },
        "strategy_configuration_digest": strategy_configuration.digest.value,
        "definition": definition_document(definition),
        "case_evidence_paths": evidence_paths,
        "attempts": [attempt_document(item) for item in execution.attempts],
        "result": result_document(result),
        "validity": validity_document(validity),
        "qualification": qualification_document(proof) if proof else None,
        "closed_result_status": (
            "PASS_VALID" if proof is not None else "FAIL_OR_INVALID"
        ),
        "failure_count": len(result.failed_case_ids),
        "unknown_count": len(result.inconclusive_case_ids),
        "required_case_count": len(definition.cases),
    }
    result_document_value = {
        **result_core,
        "document_digest": digest_of(result_core).value,
    }
    result_path = result_directory / "closed-evaluation-result.json"
    write_document_once(result_path, result_document_value)
    qualification_path: Path | None = None
    if proof is not None:
        qualification_core = {
            "schema": QUALIFICATION_DOCUMENT_SCHEMA,
            "proof": qualification_document(proof),
        }
        qualification_value = {
            **qualification_core,
            "document_digest": digest_of(qualification_core).value,
        }
        qualification_path = result_directory / "capability-qualification.json"
        write_document_once(qualification_path, qualification_value)
    passed = (
        proof is not None
        and result.conclusion.value == "PASS"
        and validity.status.value == "VALID"
        and not result.failed_case_ids
        and not result.inconclusive_case_ids
        and len(result.passed_case_ids) == len(definition.cases)
    )
    return (
        {
            "status": (
                "CAPABILITY_EVALUATION_PASS"
                if passed
                else "CAPABILITY_EVALUATION_FAIL"
            ),
            "result_path": str(result_path),
            "qualification_path": (
                str(qualification_path) if qualification_path else None
            ),
            "result_id": result.result_id.value,
            "result_digest": result.digest.value,
            "validity_status": validity.status.value,
            "qualification_ref": proof.proof_ref if proof else None,
            "qualification_digest": proof.digest.value if proof else None,
            "case_count": len(execution.attempts),
            "passed_case_count": len(result.passed_case_ids),
            "failed_case_count": len(result.failed_case_ids),
            "unknown_case_count": len(result.inconclusive_case_ids),
            "provider_request_count": sum(
                len(item.provider_request_ids) for item in outputs.values()
            ),
            "input_tokens": result.input_tokens,
            "output_tokens": result.output_tokens,
            "production_eligible": False,
            "g3b_unblocked": passed,
        },
        0 if passed else 4,
    )


def _run_conformance(
    arguments,
    *,
    frozen: Mapping[str, object],
    configuration: VolcengineArkModelConfiguration,
    environment: Mapping[str, str],
    transport: object | None,
    repository_state: Mapping[str, object],
) -> tuple[dict[str, object], int]:
    result_directory = Path(arguments.result_directory).resolve()
    result_directory.mkdir(parents=True, exist_ok=False)
    invocation_core = _conformance_invocation_core(
        frozen,
        freeze_checkpoint=arguments.freeze_checkpoint,
        freeze_tree=str(repository_state["tree"]),
    )
    invocation = {
        **invocation_core,
        "document_digest": digest_of(invocation_core).value,
    }
    invocation_path = result_directory / "conformance-invocation.json"
    write_document_once(invocation_path, invocation)
    active_transport = transport or UrllibVolcengineArkChatTransport(
        api_key_resolver=lambda: configuration.resolve_api_key(environment)
    )
    frozen_conformance = frozen["conformance"]
    assert isinstance(frozen_conformance, Mapping)
    try:
        result = run_ark_chat_conformance(
            configuration=configuration,
            transport=active_transport,
            environment=environment,
            operator=str(frozen_conformance["operator"]),
            timeout_milliseconds=int(
                frozen_conformance["timeout_milliseconds"]
            ),
            max_output_tokens=int(frozen_conformance["max_output_tokens"]),
        )
    except ProviderOutcomeUnknown as exc:
        unknown_core = {
            "schema": CONFORMANCE_UNKNOWN_SCHEMA,
            "invocation_document_digest": invocation["document_digest"],
            "outcome": "UNKNOWN",
            "reason_code": exc.reason_code,
            "retry_policy": "DO_NOT_RETRY_WITHIN_THIS_FREEZE_RUN",
        }
        unknown = {
            **unknown_core,
            "document_digest": digest_of(unknown_core).value,
        }
        unknown_path = result_directory / "conformance-unknown.json"
        write_document_once(unknown_path, unknown)
        return (
            {
                "status": "PROVIDER_OUTCOME_UNKNOWN",
                "reason": exc.reason_code,
                "invocation_path": str(invocation_path),
                "unknown_path": str(unknown_path),
                "external_model_called": True,
                "g3b_unblocked": False,
            },
            3,
        )
    result_path = seal_ark_chat_conformance_result(result, result_directory)
    binding_core = {
        "schema": CONFORMANCE_BINDING_SCHEMA,
        "input_freeze_ref": frozen["freeze_ref"],
        "input_freeze_digest": frozen["_file_digest"],
        "freeze_checkpoint": arguments.freeze_checkpoint,
        "freeze_tree": repository_state["tree"],
        "invocation_file": invocation_path.name,
        "invocation_document_digest": invocation["document_digest"],
        "conformance_result_file": result_path.name,
        "conformance_result_digest": result["result_digest"],
        "outcome": result["outcome"],
    }
    binding = {
        **binding_core,
        "document_digest": digest_of(binding_core).value,
    }
    binding_path = result_directory / "conformance-binding.json"
    write_document_once(binding_path, binding)
    passed = (
        result["outcome"] == "PASS"
        and result["execution"]["request_count"]
        == frozen_conformance["required_request_count"]
    )
    return (
        {
            "status": "CONFORMANCE_PASS" if passed else "CONFORMANCE_FAIL",
            "binding_path": str(binding_path),
            "binding_digest": binding["document_digest"],
            "result_path": str(result_path),
            "result_digest": result["result_digest"],
            "provider_request_count": result["execution"]["request_count"],
            "provider_request_ids": result["execution"]["provider_request_ids"],
            "input_tokens": result["execution"]["input_tokens"],
            "output_tokens": result["execution"]["output_tokens"],
            "external_model_called": True,
            "production_eligible": False,
            "g3b_unblocked": False,
        },
        0 if passed else 4,
    )


def _load_bound_conformance(
    path: str | Path,
    *,
    frozen: Mapping[str, object],
    configuration: VolcengineArkModelConfiguration,
    freeze_checkpoint: str,
    freeze_tree: str,
):
    binding_path = Path(path).resolve()
    binding = _verified_document(binding_path, CONFORMANCE_BINDING_SCHEMA)
    expected_binding_fields = {
        "schema",
        "input_freeze_ref",
        "input_freeze_digest",
        "freeze_checkpoint",
        "freeze_tree",
        "invocation_file",
        "invocation_document_digest",
        "conformance_result_file",
        "conformance_result_digest",
        "outcome",
        "document_digest",
    }
    if (
        set(binding) != expected_binding_fields
        or binding.get("input_freeze_ref") != frozen["freeze_ref"]
        or binding.get("input_freeze_digest") != frozen["_file_digest"]
        or binding.get("freeze_checkpoint") != freeze_checkpoint
        or binding.get("freeze_tree") != freeze_tree
        or binding.get("outcome") != "PASS"
    ):
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "V-009 Conformance binding is stale or invalid",
        )
    invocation_path = _bound_sibling(
        binding_path, binding.get("invocation_file"), "Conformance invocation"
    )
    invocation = _verified_document(
        invocation_path, CONFORMANCE_INVOCATION_SCHEMA
    )
    expected_invocation = _conformance_invocation_core(
        frozen,
        freeze_checkpoint=freeze_checkpoint,
        freeze_tree=freeze_tree,
    )
    if (
        {key: value for key, value in invocation.items() if key != "document_digest"}
        != expected_invocation
        or binding.get("invocation_document_digest")
        != invocation.get("document_digest")
    ):
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "V-009 Conformance invocation is not the exact frozen invocation",
        )
    result_path = _bound_sibling(
        binding_path,
        binding.get("conformance_result_file"),
        "Conformance result",
    )
    result = _load_unique_document(result_path)
    frozen_conformance = frozen["conformance"]
    assert isinstance(frozen_conformance, Mapping)
    execution = result.get("execution")
    if (
        result.get("operator") != frozen_conformance["operator"]
        or not isinstance(execution, Mapping)
        or execution.get("request_count")
        != frozen_conformance["required_request_count"]
        or result.get("result_digest")
        != binding.get("conformance_result_digest")
    ):
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "V-009 Conformance Result does not match its exact binding",
        )
    qualification = load_ark_chat_conformance_qualification(
        result_path, configuration
    )
    if qualification.result_digest.value != binding["conformance_result_digest"]:
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "V-009 Conformance qualification digest is mismatched",
        )
    return qualification, binding


def _conformance_invocation_core(
    frozen: Mapping[str, object],
    *,
    freeze_checkpoint: str,
    freeze_tree: str,
) -> dict[str, object]:
    return {
        "schema": CONFORMANCE_INVOCATION_SCHEMA,
        "input_freeze_ref": frozen["freeze_ref"],
        "input_freeze_digest": frozen["_file_digest"],
        "freeze_checkpoint": freeze_checkpoint,
        "freeze_tree": freeze_tree,
        "disclosure_confirmation_ref": frozen["disclosure"]["confirmation_ref"],
        "provider": frozen["provider"],
        "conformance": frozen["conformance"],
        "external_model_call_count_planned": frozen["conformance"][
            "required_request_count"
        ],
        "evidence_policy": "WRITE_INVOCATION_BEFORE_FIRST_NETWORK_DISPATCH",
    }


def _verified_document(path: Path, schema: str) -> dict[str, object]:
    value = _load_unique_document(path)
    recorded = value.get("document_digest")
    core = {key: item for key, item in value.items() if key != "document_digest"}
    if value.get("schema") != schema or recorded != digest_of(core).value:
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "V-009 sealed evidence document is invalid",
        )
    return value


def _load_unique_document(path: Path) -> dict[str, object]:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_unique_object,
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "V-009 sealed evidence document cannot be loaded",
        ) from exc
    if not isinstance(value, dict):
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "V-009 sealed evidence document must contain one object",
        )
    return value


def _bound_sibling(binding_path: Path, name: object, label: str) -> Path:
    if (
        not isinstance(name, str)
        or not name
        or Path(name).name != name
        or name in {".", ".."}
    ):
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            f"V-009 {label} file binding is invalid",
        )
    candidate = binding_path.parent / name
    if candidate.is_symlink() or candidate.resolve().parent != binding_path.parent.resolve():
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            f"V-009 {label} file escapes its sealed result directory",
        )
    return candidate


def _verify_freeze_checkpoint(
    freeze_checkpoint: str, repository_state: Mapping[str, object]
) -> None:
    if freeze_checkpoint != repository_state.get("head"):
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "V-009 execution is not bound to the current clean freeze checkpoint",
        )


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def current_repository_state() -> dict[str, object]:
    head = _git("rev-parse", "HEAD")
    tree = _git("rev-parse", "HEAD^{tree}")
    status = _git("status", "--porcelain=v1", "--untracked-files=all")
    ancestor = subprocess.run(
        [
            "git",
            "merge-base",
            "--is-ancestor",
            "8caac3efaf97e169dac91a94a7c8ea2f8baa1b30",
            head,
        ],
        cwd=REPOSITORY_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    return {
        "head": head,
        "tree": tree,
        "clean": not bool(status),
        "g3a_result_is_ancestor": ancestor.returncode == 0,
    }


def _git(*arguments: str) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=REPOSITORY_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode:
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "V-009 cannot resolve the exact Git checkpoint",
        )
    return completed.stdout.strip()


def definition_document(value) -> dict[str, object]:
    return {
        "evaluation_id": value.evaluation_id,
        "evaluation_version": value.evaluation_version,
        "capability_id": value.capability_id,
        "capability_contract_version": value.capability_contract_version,
        "strategy_id": value.strategy_id,
        "strategy_version": value.strategy_version,
        "design_baseline_ref": value.design_baseline_ref,
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
    }


def attempt_document(value) -> dict[str, object]:
    return {
        "attempt_id": value.attempt_id.value,
        "case_id": value.case_id,
        "state": value.state.value,
        "conclusion": value.conclusion.value if value.conclusion else None,
        "output_ref": value.output_ref,
        "output_digest": value.output_digest.value if value.output_digest else None,
        "sink_manifest_ref": value.sink_manifest_ref,
        "sink_manifest_digest": (
            value.sink_manifest_digest.value if value.sink_manifest_digest else None
        ),
        "oracle_ref": value.oracle_ref,
        "oracle_digest": value.oracle_digest.value if value.oracle_digest else None,
        "actual_model_fingerprint": value.actual_model_fingerprint,
        "provider_request_id": value.provider_request_id,
        "input_tokens": value.input_tokens,
        "output_tokens": value.output_tokens,
        "usage_complete": value.usage_complete,
        "failure_code": value.failure_code,
    }


def result_document(value) -> dict[str, object]:
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


def validity_document(value) -> dict[str, object]:
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


def qualification_document(value) -> dict[str, object]:
    return {**value.core(), "digest": value.digest.value}


if __name__ == "__main__":
    raise SystemExit(main())
