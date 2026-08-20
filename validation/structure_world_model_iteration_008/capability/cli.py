"""Verify or execute authorized ITER-008 DeepSeek evaluation phases."""

from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
from typing import Mapping, Sequence

from software_world_model.ai_infrastructure import (
    BOUNDED_JAVA_SOURCE_SEMANTICS_EVALUATION_METRIC_CONTRACT,
    DeepSeekChatCompletionsNoToolsAdapter,
    DeepSeekChatCompletionsTransport,
    DeepSeekModelConfiguration,
    PersistentDeepSeekChatTransport,
    ModelGateway,
    ProviderHTTPResponse,
    ProviderOutcomeUnknown,
    RecordingDeepSeekChatCompletionsTransport,
    ReviewedWorldModelEvaluationCaseExecutor,
    WorldModelStrategyConfiguration,
    bounded_java_source_semantics_world_model_capability_registry,
    deepseek_transport_session_audit,
    load_deepseek_chat_conformance_qualification,
    world_model_answer_output_schemas,
)
from software_world_model.ai_infrastructure.deepseek_chat_conformance import (
    current_deepseek_implementation_manifest,
    run_deepseek_chat_conformance,
    seal_deepseek_chat_conformance_result,
)
from software_world_model.ai_infrastructure.bounded_java_source_semantics_model_egress_qualification import (
    BOUNDED_JAVA_SOURCE_SEMANTICS_CAPABILITY_CLOSED_RESULT_SCHEMA,
    BOUNDED_JAVA_SOURCE_SEMANTICS_CAPABILITY_QUALIFICATION_DOCUMENT_SCHEMA,
)
from software_world_model.application_services import (
    CapabilityEvaluationRunner,
    CapabilityEvaluationService,
)
from software_world_model.cross_cutting import (
    CorrelationRef,
    Digest,
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
from software_world_model.interface.deepseek_provider_cli import (
    run_deepseek_model_probe,
)

from . import authorize
from .freeze import (
    CAPABILITY_FREEZE_SCHEMA,
    EVALUATOR_PATH,
    MODEL_DIAGNOSTIC_FREEZE_SCHEMA,
    _capability_scope,
    _candidate_identity,
    _closed_inputs,
    _conformance_completed_at,
    _load_document,
    _model_diagnostic_scope,
    _package_manifest,
    _parse_time,
    _proposal_contract,
    verify_preflight,
)
from .live_runner import LiveBoundedJavaSourceSemanticsCapabilityCaseRunner
from .manifest import (
    PINNED_ORACLE_FILE_DIGEST,
    PINNED_ORACLE_REF,
    PINNED_PROVIDER_REQUEST_COUNT,
    PINNED_REQUIRED_CASE_IDS,
    PINNED_RESOURCE_POLICY_REF,
    PINNED_SUITE_FILE_DIGEST,
    PINNED_SUITE_REF,
    build_evaluation_definition,
    case_pairs,
    load_capability_inputs,
)


MODEL_DIAGNOSTIC_INVOCATION_SCHEMA = (
    "swm.iter-008.deepseek-model-diagnostic-authorized-invocation@1"
)
CONFORMANCE_INVOCATION_SCHEMA = (
    "swm.iter-008.deepseek-conformance-authorized-invocation@1"
)
CAPABILITY_INVOCATION_SCHEMA = (
    "swm.iter-008.bounded-java-source-semantics-ce-invocation@1"
)


class _ProviderDispatchAudit:
    """Preserve request evidence and the reason hidden by ModelGateway."""

    def __init__(self, delegate: DeepSeekChatCompletionsTransport) -> None:
        self._recording = RecordingDeepSeekChatCompletionsTransport(delegate)
        self.requests = self._recording.requests
        self.outcome_unknown_reason_codes: list[str] = []

    def post_json(
        self,
        *,
        endpoint: str,
        body: bytes,
        client_request_id: str,
        timeout_milliseconds: int,
    ) -> ProviderHTTPResponse:
        try:
            return self._recording.post_json(
                endpoint=endpoint,
                body=body,
                client_request_id=client_request_id,
                timeout_milliseconds=timeout_milliseconds,
            )
        except ProviderOutcomeUnknown as exc:
            self.outcome_unknown_reason_codes.append(exc.reason_code)
            raise

    def session_audit(self) -> dict[str, object]:
        return deepseek_transport_session_audit(self._recording)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    verify_diagnostic = commands.add_parser("verify-model-diagnostic-freeze")
    verify_diagnostic.add_argument("--freeze", required=True)
    run_diagnostic = commands.add_parser("run-model-diagnostic")
    run_diagnostic.add_argument("--freeze", required=True)
    run_diagnostic.add_argument("--authorization", required=True)
    verify_pre = commands.add_parser("verify-preflight")
    verify_pre.add_argument("--preflight", required=True)
    run_conformance = commands.add_parser("run-conformance")
    run_conformance.add_argument("--preflight", required=True)
    run_conformance.add_argument("--authorization", required=True)
    verify_capability = commands.add_parser("verify-capability-freeze")
    verify_capability.add_argument("--freeze", required=True)
    verify_capability.add_argument("--conformance-result", required=True)
    run_capability = commands.add_parser("run-capability")
    run_capability.add_argument("--freeze", required=True)
    run_capability.add_argument("--authorization", required=True)
    run_capability.add_argument("--conformance-result", required=True)
    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    environment: Mapping[str, str] | None = None,
    transport: DeepSeekChatCompletionsTransport | None = None,
) -> int:
    arguments = _parser().parse_args(argv)
    env = os.environ if environment is None else environment
    try:
        if arguments.command == "verify-model-diagnostic-freeze":
            freeze = _verify_model_diagnostic_freeze(Path(arguments.freeze))
            payload = {
                "status": "PASS_AWAITING_MODEL_DIAGNOSTIC_AUTHORIZATION",
                "freeze_digest": freeze["document_digest"],
                "planned_provider_call_count": 1,
                "external_model_called": False,
                "hidden_canary_disclosed": False,
                "production_activation": "NOT_EXECUTED",
            }
            code = 0
        elif arguments.command == "run-model-diagnostic":
            payload, code = _run_authorized_model_diagnostic(
                freeze_path=Path(arguments.freeze),
                authorization_path=Path(arguments.authorization),
                environment=env,
                transport=transport,
            )
        elif arguments.command == "verify-preflight":
            preflight = verify_preflight(Path(arguments.preflight))
            payload = {
                "status": "PASS_AWAITING_CONFORMANCE_AUTHORIZATION",
                "freeze_digest": preflight["document_digest"],
                "planned_provider_call_count": 2,
                "external_model_called": False,
                "hidden_canary_disclosed": False,
                "production_activation": "NOT_EXECUTED",
            }
            code = 0
        elif arguments.command == "run-conformance":
            payload, code = _run_authorized_conformance(
                preflight_path=Path(arguments.preflight),
                authorization_path=Path(arguments.authorization),
                environment=env,
                transport=transport,
            )
        elif arguments.command == "verify-capability-freeze":
            freeze = _verify_capability_freeze(
                Path(arguments.freeze),
                Path(arguments.conformance_result),
            )
            payload = {
                "status": "PASS_AWAITING_CAPABILITY_AUTHORIZATION",
                "freeze_digest": freeze["document_digest"],
                "suite_digest": PINNED_SUITE_FILE_DIGEST,
                "planned_provider_call_count": PINNED_PROVIDER_REQUEST_COUNT,
                "external_model_called": False,
                "hidden_canary_disclosed": False,
                "production_activation": "NOT_EXECUTED",
            }
            code = 0
        else:
            freeze = _verify_capability_freeze(
                Path(arguments.freeze),
                Path(arguments.conformance_result),
            )
            payload, code = _run_authorized_capability(
                freeze=freeze,
                freeze_path=Path(arguments.freeze),
                authorization_path=Path(arguments.authorization),
                conformance_result_path=Path(arguments.conformance_result),
                environment=env,
                transport=transport,
            )
    except (DomainError, ProviderOutcomeUnknown, OSError, ValueError, RuntimeError) as exc:
        payload = {
            "status": "ERROR",
            "error": (
                exc.code.value
                if isinstance(exc, DomainError)
                else "PROVIDER_OUTCOME_UNKNOWN"
                if isinstance(exc, ProviderOutcomeUnknown)
                else "INVALID_ARGUMENT"
            ),
            "message": exc.message if isinstance(exc, DomainError) else str(exc),
            "hidden_canary_disclosed": False,
            "production_activation": "NOT_EXECUTED",
        }
        if isinstance(exc, ProviderOutcomeUnknown):
            payload.update(
                {
                    "reason_code": exc.reason_code,
                    "authorization_consumed": True,
                    "retry_permitted_with_same_authorization": False,
                }
            )
        code = 2
    print(canonical_json_bytes(payload).decode("utf-8"))
    return code


def _run_authorized_model_diagnostic(
    *,
    freeze_path: Path,
    authorization_path: Path,
    environment: Mapping[str, str],
    transport: DeepSeekChatCompletionsTransport | None,
) -> tuple[dict[str, object], int]:
    freeze = _verify_model_diagnostic_freeze(freeze_path)
    request = authorize._load_request(
        freeze_path.parent / "model-diagnostic-authorization-request.json"
    )
    _verify_request_binding(
        request,
        freeze=freeze,
        phase="DEEPSEEK_MODEL_DIAGNOSTIC",
        scope_owner="dispatch_contract",
    )
    authorization = authorize.load_authorization(authorization_path, request)
    result_directory = _new_result_directory(authorization)
    invocation_core = {
        "schema": MODEL_DIAGNOSTIC_INVOCATION_SCHEMA,
        "freeze_digest": freeze["document_digest"],
        "authorization_digest": authorization["document_digest"],
        "authorization_ref": authorization["authorization_ref"],
        "authorization_scope": authorization["authorization_scope"],
        "evidence_policy": "PERSIST_BEFORE_ONLY_PROVIDER_DISPATCH",
        "hidden_canary_disclosed": False,
        "production_activation": "NOT_EXECUTED",
    }
    _write_once(
        result_directory / "invocation.json", _document(invocation_core)
    )
    configuration = DeepSeekModelConfiguration()
    active_transport = transport or PersistentDeepSeekChatTransport(
        api_key_resolver=lambda: configuration.resolve_api_key(environment)
    )
    dispatch_audit = _ProviderDispatchAudit(active_transport)
    try:
        response = run_deepseek_model_probe(
            configuration,
            dispatch_audit,
            timeout_milliseconds=30_000,
            max_output_tokens=64,
        )
        if (
            response.actual_model_fingerprint
            != configuration.actual_model_fingerprint
        ):
            raise DomainError(
                ErrorCode.QUALIFICATION_INVALID,
                "DeepSeek model diagnostic returned another model identity",
            )
        if not response.usage_complete:
            raise DomainError(
                ErrorCode.QUALIFICATION_INVALID,
                "DeepSeek model diagnostic returned incomplete token usage",
            )
    except ProviderOutcomeUnknown as exc:
        _seal_model_diagnostic_failure(
            result_directory=result_directory,
            freeze=freeze,
            authorization=authorization,
            dispatch_audit=dispatch_audit,
            status="PROVIDER_OUTCOME_UNKNOWN",
            failure_code=exc.reason_code,
            safe_details={},
        )
        raise
    except DomainError as exc:
        safe_details = {
            key: value
            for key, value in exc.details.items()
            if key
            in {
                "http_status",
                "provider_error_code",
                "provider_error_type",
                "provider_request_id",
                "finish_reason",
            }
        }
        failure_path = _seal_model_diagnostic_failure(
            result_directory=result_directory,
            freeze=freeze,
            authorization=authorization,
            dispatch_audit=dispatch_audit,
            status="MODEL_DIAGNOSTIC_FAIL",
            failure_code=exc.code.value,
            safe_details=safe_details,
        )
        return (
            {
                "status": "MODEL_DIAGNOSTIC_FAIL",
                "failure_path": str(failure_path),
                "provider_request_count": len(dispatch_audit.requests),
                "authorization_consumed": True,
                "hidden_canary_disclosed": False,
                "production_activation": "NOT_EXECUTED",
            },
            4,
        )
    if len(dispatch_audit.requests) != 1:
        failure_path = _seal_model_diagnostic_failure(
            result_directory=result_directory,
            freeze=freeze,
            authorization=authorization,
            dispatch_audit=dispatch_audit,
            status="MODEL_DIAGNOSTIC_FAIL",
            failure_code="PROVIDER_REQUEST_COUNT_MISMATCH",
            safe_details={},
        )
        return (
            {
                "status": "MODEL_DIAGNOSTIC_FAIL",
                "failure_path": str(failure_path),
                "provider_request_count": len(dispatch_audit.requests),
                "authorization_consumed": True,
                "hidden_canary_disclosed": False,
                "production_activation": "NOT_EXECUTED",
            },
            4,
        )
    recorded = dispatch_audit.requests[0]
    result_core = {
        "schema": "swm.iter-008.deepseek-model-diagnostic-result@1",
        "status": "PASS",
        "freeze_digest": freeze["document_digest"],
        "authorization_digest": authorization["document_digest"],
        "provider": {
            "provider_type": configuration.provider_type,
            "endpoint": configuration.endpoint,
            "adapter_version": configuration.adapter_version,
            "configuration_fingerprint": configuration.fingerprint.value,
            "requested_model_ref": configuration.model_ref,
            "actual_model_fingerprint": response.actual_model_fingerprint,
            "provider_request_id": response.provider_request_id,
        },
        "execution": {
            "provider_request_count": 1,
            "request_body_digest": (
                "sha256:" + hashlib.sha256(recorded.body).hexdigest()
            ),
            "input_tokens": response.input_tokens,
            "output_tokens": response.output_tokens,
            "usage_complete": response.usage_complete,
            "termination_reason": response.termination_reason,
            "output_normalization": response.output_normalization,
            "strict_json_probe_valid": True,
            "raw_prompt_persisted": False,
            "raw_response_persisted": False,
            "transport_session": dispatch_audit.session_audit(),
        },
        "authorization_consumed": True,
        "retry_permitted_with_same_authorization": False,
        "capability_qualification": "NOT_EXECUTED",
        "hidden_canary_disclosed": False,
        "production_activation": "NOT_EXECUTED",
    }
    result_path = result_directory / "result.json"
    result = _document(result_core)
    _write_once(result_path, result)
    terminal_core = {
        "schema": "swm.iter-008.deepseek-model-diagnostic-terminal@1",
        "status": "PASS",
        "freeze_digest": freeze["document_digest"],
        "authorization_digest": authorization["document_digest"],
        "result_path": str(result_path),
        "result_digest": result["document_digest"],
        "provider_request_count": 1,
        "authorization_consumed": True,
        "retry_permitted_with_same_authorization": False,
        "hidden_canary_disclosed": False,
        "production_activation": "NOT_EXECUTED",
    }
    _write_once(
        result_directory / "terminal.json", _document(terminal_core)
    )
    return (
        {
            "status": "MODEL_DIAGNOSTIC_PASS",
            "result_path": str(result_path),
            "result_digest": result["document_digest"],
            "actual_model_fingerprint": response.actual_model_fingerprint,
            "provider_request_id": response.provider_request_id,
            "provider_request_count": 1,
            "input_tokens": response.input_tokens,
            "output_tokens": response.output_tokens,
            "authorization_consumed": True,
            "hidden_canary_disclosed": False,
            "production_activation": "NOT_EXECUTED",
        },
        0,
    )


def _seal_model_diagnostic_failure(
    *,
    result_directory: Path,
    freeze: Mapping[str, object],
    authorization: Mapping[str, object],
    dispatch_audit: _ProviderDispatchAudit,
    status: str,
    failure_code: str,
    safe_details: Mapping[str, object],
) -> Path:
    failure_core = {
        "schema": "swm.iter-008.deepseek-model-diagnostic-failure@1",
        "status": status,
        "freeze_digest": freeze["document_digest"],
        "authorization_digest": authorization["document_digest"],
        "failure_code": failure_code,
        "safe_provider_details": dict(safe_details),
        "attempted_provider_request_count": len(dispatch_audit.requests),
        "attempted_request_body_digests": [
            "sha256:" + hashlib.sha256(item.body).hexdigest()
            for item in dispatch_audit.requests
        ],
        "transport_session": dispatch_audit.session_audit(),
        "raw_prompt_persisted": False,
        "raw_response_persisted": False,
        "authorization_consumed": True,
        "retry_permitted_with_same_authorization": False,
        "hidden_canary_disclosed": False,
        "production_activation": "NOT_EXECUTED",
    }
    failure_path = result_directory / "failure.json"
    _write_once(failure_path, _document(failure_core))
    terminal_core = {
        "schema": "swm.iter-008.deepseek-model-diagnostic-terminal@1",
        "status": status,
        "freeze_digest": freeze["document_digest"],
        "authorization_digest": authorization["document_digest"],
        "failure_path": str(failure_path),
        "provider_request_count": len(dispatch_audit.requests),
        "authorization_consumed": True,
        "retry_permitted_with_same_authorization": False,
        "hidden_canary_disclosed": False,
        "production_activation": "NOT_EXECUTED",
    }
    _write_once(
        result_directory / "terminal.json", _document(terminal_core)
    )
    return failure_path


def _verify_model_diagnostic_freeze(
    freeze_path: Path,
) -> dict[str, object]:
    freeze = _load_document(freeze_path, MODEL_DIAGNOSTIC_FREEZE_SCHEMA)
    configuration = DeepSeekModelConfiguration()
    implementation = current_deepseek_implementation_manifest()
    scope = _model_diagnostic_scope(configuration, implementation)
    expected_fields = {
        "schema",
        "freeze_ref",
        "created_at",
        "environment",
        "candidate_identity",
        "package_manifest",
        "provider",
        "dispatch_contract",
        "external_model_called_during_freeze",
        "raw_prompt_persisted",
        "raw_response_persisted",
        "hidden_canary_disclosed",
        "production_activation",
        "git_stage_commit_push",
        "document_digest",
    }
    if (
        set(freeze) != expected_fields
        or freeze.get("freeze_ref")
        != "ITER-008-DEEPSEEK-MODEL-DIAGNOSTIC-RUN-CANDIDATE@1"
        or freeze.get("environment") != "EVALUATION_ONLY"
        or freeze.get("candidate_identity")
        != _candidate_identity(require_clean=True)
        or freeze.get("package_manifest") != _package_manifest()
        or freeze.get("provider")
        != {
            "authorization_scope": scope,
            "implementation_manifest": implementation,
            "credential_reference": configuration.secret_reference,
        }
        or freeze.get("dispatch_contract")
        != {
            "status": "HELD_AWAITING_EXACT_USER_AUTHORIZATION",
            "authorization_scope": scope,
            "credential_read_before_authorization": False,
            "provider_socket_before_authorization": False,
        }
        or freeze.get("external_model_called_during_freeze") is not False
        or freeze.get("raw_prompt_persisted") is not False
        or freeze.get("raw_response_persisted") is not False
        or freeze.get("hidden_canary_disclosed") is not False
        or freeze.get("production_activation") != "NOT_EXECUTED"
        or freeze.get("git_stage_commit_push") != "NOT_EXECUTED"
    ):
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "DeepSeek model diagnostic freeze drifted from the candidate",
        )
    _parse_time(freeze.get("created_at"), "model diagnostic freeze time")
    return freeze


def _run_authorized_conformance(
    *,
    preflight_path: Path,
    authorization_path: Path,
    environment: Mapping[str, str],
    transport: DeepSeekChatCompletionsTransport | None,
) -> tuple[dict[str, object], int]:
    preflight = verify_preflight(preflight_path)
    request = authorize._load_request(
        preflight_path.parent / "conformance-authorization-request.json"
    )
    _verify_request_binding(
        request,
        freeze=preflight,
        phase="DEEPSEEK_CONFORMANCE",
        scope_owner="deepseek_conformance",
    )
    authorization = authorize.load_authorization(authorization_path, request)
    result_directory = _new_result_directory(authorization)
    invocation_core = {
        "schema": CONFORMANCE_INVOCATION_SCHEMA,
        "preflight_digest": preflight["document_digest"],
        "authorization_digest": authorization["document_digest"],
        "authorization_ref": authorization["authorization_ref"],
        "authorization_scope": authorization["authorization_scope"],
        "evidence_policy": "PERSIST_BEFORE_FIRST_PROVIDER_DISPATCH",
        "hidden_canary_disclosed": False,
        "production_activation": "NOT_EXECUTED",
    }
    _write_once(
        result_directory / "invocation.json",
        _document(invocation_core),
    )
    configuration = DeepSeekModelConfiguration()
    active_transport = transport or PersistentDeepSeekChatTransport(
        api_key_resolver=lambda: configuration.resolve_api_key(environment)
    )
    dispatch_audit = _ProviderDispatchAudit(active_transport)
    try:
        result = run_deepseek_chat_conformance(
            configuration=configuration,
            transport=dispatch_audit,
            environment=environment,
            operator="iter-008-capability-owner",
            timeout_milliseconds=180_000,
            max_output_tokens=256,
        )
    except ProviderOutcomeUnknown as exc:
        attempted_request_digests = [
            "sha256:" + hashlib.sha256(item.body).hexdigest()
            for item in dispatch_audit.requests
        ]
        failure_core = {
            "schema": "swm.iter-008.deepseek-conformance-failure@1",
            "status": "PROVIDER_OUTCOME_UNKNOWN",
            "preflight_digest": preflight["document_digest"],
            "authorization_digest": authorization["document_digest"],
            "provider_outcome_reason_code": exc.reason_code,
            "attempted_provider_request_count": len(dispatch_audit.requests),
            "attempted_request_body_digests": attempted_request_digests,
            "transport_session": dispatch_audit.session_audit(),
            "raw_prompt_persisted": False,
            "raw_response_persisted": False,
            "authorization_consumed": True,
            "retry_permitted_with_same_authorization": False,
            "hidden_canary_disclosed": False,
            "production_activation": "NOT_EXECUTED",
        }
        failure_path = result_directory / "failure.json"
        _write_once(failure_path, _document(failure_core))
        terminal_core = {
            "schema": "swm.iter-008.deepseek-conformance-terminal@1",
            "status": "PROVIDER_OUTCOME_UNKNOWN",
            "preflight_digest": preflight["document_digest"],
            "authorization_digest": authorization["document_digest"],
            "failure_path": str(failure_path),
            "provider_request_count": len(dispatch_audit.requests),
            "authorization_consumed": True,
            "retry_permitted_with_same_authorization": False,
            "hidden_canary_disclosed": False,
            "production_activation": "NOT_EXECUTED",
        }
        _write_once(
            result_directory / "terminal.json", _document(terminal_core)
        )
        raise
    result_path = seal_deepseek_chat_conformance_result(
        result, result_directory
    )
    passed = (
        result["outcome"] == "PASS"
        and result["execution"]["request_count"] == 2
        and result["execution"]["transport_session"]["http_dispatch_count"]
        == 2
    )
    terminal_core = {
        "schema": "swm.iter-008.deepseek-conformance-terminal@1",
        "status": "PASS" if passed else "FAIL",
        "preflight_digest": preflight["document_digest"],
        "authorization_digest": authorization["document_digest"],
        "result_path": str(result_path),
        "result_digest": result["result_digest"],
        "provider_request_count": result["execution"]["request_count"],
        "authorization_consumed": True,
        "retry_permitted_with_same_authorization": False,
        "hidden_canary_disclosed": False,
        "production_activation": "NOT_EXECUTED",
    }
    _write_once(result_directory / "terminal.json", _document(terminal_core))
    return (
        {
            "status": "CONFORMANCE_PASS" if passed else "CONFORMANCE_FAIL",
            "result_path": str(result_path),
            "result_digest": result["result_digest"],
            "provider_request_count": result["execution"]["request_count"],
            "authorization_consumed": True,
            "hidden_canary_disclosed": False,
            "production_activation": "NOT_EXECUTED",
        },
        0 if passed else 4,
    )


def _run_authorized_capability(
    *,
    freeze: Mapping[str, object],
    freeze_path: Path,
    authorization_path: Path,
    conformance_result_path: Path,
    environment: Mapping[str, str],
    transport: DeepSeekChatCompletionsTransport | None,
) -> tuple[dict[str, object], int]:
    request = authorize._load_request(
        freeze_path.parent / "capability-authorization-request.json"
    )
    _verify_request_binding(
        request,
        freeze=freeze,
        phase="BOUNDED_CAPABILITY_QUALIFICATION",
        scope_owner="dispatch_contract",
    )
    authorization = authorize.load_authorization(authorization_path, request)
    result_directory = _new_result_directory(authorization)
    (result_directory / "runtime").mkdir(mode=0o700)
    invocation_core = {
        "schema": CAPABILITY_INVOCATION_SCHEMA,
        "freeze_digest": freeze["document_digest"],
        "authorization_digest": authorization["document_digest"],
        "authorization_ref": authorization["authorization_ref"],
        "suite_digest": PINNED_SUITE_FILE_DIGEST,
        "oracle_digest": PINNED_ORACLE_FILE_DIGEST,
        "planned_provider_call_count": PINNED_PROVIDER_REQUEST_COUNT,
        "payload_boundary": request["authorization_scope"]["payload_boundary"],
        "evidence_policy": "PERSIST_BEFORE_FIRST_PROVIDER_DISPATCH",
        "hidden_canary_disclosed": False,
        "production_activation": "NOT_EXECUTED",
    }
    _write_once(result_directory / "invocation.json", _document(invocation_core))

    configuration = DeepSeekModelConfiguration()
    conformance = load_deepseek_chat_conformance_qualification(
        conformance_result_path.resolve(strict=True), configuration
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
    active_transport = transport or PersistentDeepSeekChatTransport(
        api_key_resolver=lambda: configuration.resolve_api_key(environment)
    )
    dispatch_audit = _ProviderDispatchAudit(active_transport)
    adapter = DeepSeekChatCompletionsNoToolsAdapter(
        transport=dispatch_audit,
        configuration=configuration,
        output_schemas=world_model_answer_output_schemas(
            include_java_source_semantics=True
        ),
        live_qualification=conformance,
    )
    suite, oracle = load_capability_inputs()
    outputs = {}
    reviews = {}
    evidence_paths: list[str] = []
    case_evidence: list[dict[str, object]] = []
    try:
        for case, oracle_case in case_pairs(suite, oracle):
            case_id = str(case["case_id"])
            runtime_path = result_directory / "runtime" / f"{case_id}.sqlite3"
            with SqliteDatabase(runtime_path) as database:
                gateway = ModelGateway(
                    SqliteModelGatewayRepository(database), (adapter,)
                )
                output, review, evidence_path, summary = (
                    LiveBoundedJavaSourceSemanticsCapabilityCaseRunner(
                        database=database,
                        gateway=gateway,
                        configuration=strategy_configuration,
                        expected_model_fingerprint=(
                            configuration.actual_model_fingerprint
                        ),
                        result_directory=result_directory,
                    ).execute(
                        suite=suite,
                        oracle=oracle,
                        case=case,
                        oracle_case=oracle_case,
                    )
                )
            outputs[case_id] = output
            reviews[case_id] = review
            evidence_paths.append(str(evidence_path))
            case_evidence.append(summary)
    except Exception as exc:
        provider_outcome_unknown = isinstance(
            exc, ProviderOutcomeUnknown
        ) or bool(dispatch_audit.outcome_unknown_reason_codes)
        provider_outcome_reason = (
            exc.reason_code
            if isinstance(exc, ProviderOutcomeUnknown)
            else dispatch_audit.outcome_unknown_reason_codes[-1]
            if dispatch_audit.outcome_unknown_reason_codes
            else None
        )
        attempted_request_digests = [
            "sha256:" + hashlib.sha256(item.body).hexdigest()
            for item in dispatch_audit.requests
        ]
        failure_core = {
            "schema": "swm.iter-008.bounded-java-source-semantics-ce-failure@1",
            "status": (
                "PROVIDER_OUTCOME_UNKNOWN"
                if provider_outcome_unknown
                else "EXECUTION_FAILED"
            ),
            "freeze_digest": freeze["document_digest"],
            "authorization_digest": authorization["document_digest"],
            "completed_case_count": len(outputs),
            "completed_provider_request_count": sum(
                len(item.provider_request_ids) for item in outputs.values()
            ),
            "attempted_provider_request_count": len(dispatch_audit.requests),
            "attempted_request_body_digests": attempted_request_digests,
            "transport_session": dispatch_audit.session_audit(),
            "failure_type": type(exc).__name__,
            "failure_code": (
                provider_outcome_reason
                if provider_outcome_unknown
                else exc.code.value
                if isinstance(exc, DomainError)
                else "OUTCOME_UNKNOWN"
            ),
            "message": exc.message if isinstance(exc, DomainError) else str(exc),
            "raw_prompt_persisted": False,
            "raw_response_persisted": False,
            "authorization_consumed": True,
            "retry_permitted_with_same_authorization": False,
            "hidden_canary_disclosed": False,
            "production_activation": "NOT_EXECUTED",
        }
        failure_path = result_directory / "failure.json"
        _write_once(failure_path, _document(failure_core))
        terminal_core = {
            "schema": (
                "swm.iter-008.bounded-java-source-semantics-ce-terminal@1"
            ),
            "status": failure_core["status"],
            "freeze_digest": freeze["document_digest"],
            "authorization_digest": authorization["document_digest"],
            "failure_path": str(failure_path),
            "provider_request_count": len(dispatch_audit.requests),
            "authorization_consumed": True,
            "retry_permitted_with_same_authorization": False,
            "hidden_canary_disclosed": False,
            "production_activation": "NOT_EXECUTED",
        }
        _write_once(
            result_directory / "terminal.json", _document(terminal_core)
        )
        if provider_outcome_unknown and not isinstance(
            exc, ProviderOutcomeUnknown
        ):
            raise ProviderOutcomeUnknown(
                "DeepSeek Chat Completions outcome is unknown",
                reason_code=provider_outcome_reason or "UNKNOWN_NETWORK_FAILURE",
            ) from exc
        raise

    identity = freeze.get("candidate_identity")
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
        reference_strategy_ref=(
            "standalone-stdlib-evaluator:"
            f"{freeze['closed_inputs']['evaluator_digest']}"
        ),
        resource_policy_ref=PINNED_RESOURCE_POLICY_REF,
        valid_for_seconds=604800,
    )
    if definition.digest.value != freeze["evaluation_definition"]["definition_digest"]:
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "bounded capability definition drifted after authorization",
        )
    executor = ReviewedWorldModelEvaluationCaseExecutor(
        definition=definition,
        outputs=outputs,
        reviews=reviews,
    )
    with SqliteDatabase(
        result_directory / "capability-evaluation.sqlite3"
    ) as database:
        execution = CapabilityEvaluationRunner(
            CapabilityEvaluationService(
                SqliteCapabilityEvaluationRepository(database),
                bounded_java_source_semantics_world_model_capability_registry(),
                conformance,
            )
        ).run_suite(
            definition=definition,
            evaluation_sink_ref=f"files:{result_directory}",
            root_allocation_ref=(
                f"iter-008-bounded-ce:{freeze['document_digest']}"
            ),
            idempotency_key=IdempotencyKey(
                f"iter-008-bounded-ce:{authorization['document_digest']}"
            ),
            executor=executor,
            actor="iter-008-bounded-capability-owner",
            correlation_ref=CorrelationRef(
                f"iter-008-bounded-ce:{authorization['document_digest']}"
            ),
            completion_reason=(
                "all eighteen bounded source-semantics cases evaluated"
            ),
        )
    if execution.completion is None:
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "bounded capability evaluation did not reach a closed result",
        )
    completion = execution.completion
    result = completion.result
    validity = completion.validity
    proof = completion.qualification
    output_provider_request_count = sum(
        len(item.provider_request_ids) for item in outputs.values()
    )
    provider_request_count = len(dispatch_audit.requests)
    transport_session = dispatch_audit.session_audit()
    transport_session_passed = (
        transport_session["http_dispatch_count"] == PINNED_PROVIDER_REQUEST_COUNT
        and 1 <= transport_session["tls_handshake_success_count"] <= 3
        and transport_session["connection_reuse_count"]
        == (
            PINNED_PROVIDER_REQUEST_COUNT
            - transport_session["tls_handshake_success_count"]
        )
        and transport_session["post_dispatch_outcome_unknown_count"] == 0
        and transport_session["request_retry_count"] == 0
        and transport_session["credential_resolution_count"]
        == PINNED_PROVIDER_REQUEST_COUNT
        and transport_session["credential_resolution_success_count"]
        == PINNED_PROVIDER_REQUEST_COUNT
    )
    passed = (
        proof is not None
        and result.conclusion.value == "PASS"
        and validity.status.value == "VALID"
        and len(result.passed_case_ids) == len(PINNED_REQUIRED_CASE_IDS)
        and frozenset(result.passed_case_ids)
        == frozenset(PINNED_REQUIRED_CASE_IDS)
        and not result.failed_case_ids
        and not result.inconclusive_case_ids
        and output_provider_request_count == provider_request_count
        and provider_request_count == PINNED_PROVIDER_REQUEST_COUNT
        and transport_session_passed
        and all(item["status"] == "PASS" for item in case_evidence)
    )
    sealed_proof = proof if passed else None
    result_core = {
        "schema": BOUNDED_JAVA_SOURCE_SEMANTICS_CAPABILITY_CLOSED_RESULT_SCHEMA,
        "freeze_digest": freeze["document_digest"],
        "authorization_digest": authorization["document_digest"],
        "suite_ref": PINNED_SUITE_REF,
        "suite_digest": PINNED_SUITE_FILE_DIGEST,
        "oracle_ref": PINNED_ORACLE_REF,
        "oracle_digest": PINNED_ORACLE_FILE_DIGEST,
        "definition": _definition_document(definition),
        "case_evidence_paths": evidence_paths,
        "case_evidence": case_evidence,
        "attempts": [_attempt_document(item) for item in execution.attempts],
        "result": _result_document(result),
        "validity": _validity_document(validity),
        "qualification": (
            _qualification_document(sealed_proof) if sealed_proof else None
        ),
        "closed_result_status": "PASS_VALID" if passed else "FAIL_OR_INVALID",
        "failure_count": len(result.failed_case_ids),
        "unknown_count": len(result.inconclusive_case_ids),
        "required_case_count": len(PINNED_REQUIRED_CASE_IDS),
        "provider_request_count": provider_request_count,
        "transport_session": transport_session,
        "hidden_canary_disclosed": False,
        "production_activation": "NOT_EXECUTED",
    }
    result_path = result_directory / "closed-evaluation-result.json"
    _write_once(
        result_path,
        {**result_core, "document_digest": digest_of(result_core).value},
    )
    qualification_path = None
    if sealed_proof is not None:
        qualification_core = {
            "schema": BOUNDED_JAVA_SOURCE_SEMANTICS_CAPABILITY_QUALIFICATION_DOCUMENT_SCHEMA,
            "proof": _qualification_document(sealed_proof),
        }
        qualification_path = result_directory / "capability-qualification.json"
        _write_once(
            qualification_path,
            {
                **qualification_core,
                "document_digest": digest_of(qualification_core).value,
            },
        )
    terminal_core = {
        "schema": "swm.iter-008.bounded-java-source-semantics-ce-terminal@1",
        "status": "PASS" if passed else "FAIL",
        "freeze_digest": freeze["document_digest"],
        "authorization_digest": authorization["document_digest"],
        "closed_result_path": str(result_path),
        "qualification_path": str(qualification_path) if qualification_path else None,
        "provider_request_count": provider_request_count,
        "authorization_consumed": True,
        "retry_permitted_with_same_authorization": False,
        "hidden_canary_disclosed": False,
        "production_activation": "NOT_EXECUTED",
    }
    _write_once(result_directory / "terminal.json", _document(terminal_core))
    return (
        {
            "status": (
                "CAPABILITY_EVALUATION_PASS"
                if passed
                else "CAPABILITY_EVALUATION_FAIL"
            ),
            "result_path": str(result_path),
            "qualification_path": str(qualification_path) if qualification_path else None,
            "result_id": result.result_id.value,
            "result_digest": result.digest.value,
            "qualification_ref": (
                sealed_proof.proof_ref if sealed_proof else None
            ),
            "qualification_digest": (
                sealed_proof.digest.value if sealed_proof else None
            ),
            "case_count": len(execution.attempts),
            "provider_request_count": provider_request_count,
            "authorization_consumed": True,
            "hidden_canary_disclosed": False,
            "production_activation": "NOT_EXECUTED",
        },
        0 if passed else 4,
    )


def _verify_capability_freeze(
    freeze_path: Path,
    conformance_result_path: Path,
) -> dict[str, object]:
    freeze = _load_document(freeze_path, CAPABILITY_FREEZE_SCHEMA)
    expected_fields = {
        "schema",
        "freeze_ref",
        "created_at",
        "environment",
        "preflight_digest",
        "candidate_identity",
        "package_manifest",
        "proposal_contract",
        "closed_inputs",
        "evaluation_definition",
        "metric_contract_digest",
        "provider",
        "dispatch_contract",
        "external_model_called_during_freeze",
        "hidden_canary_disclosed",
        "production_activation",
        "git_stage_commit_push",
        "document_digest",
    }
    if (
        set(freeze) != expected_fields
        or freeze.get("freeze_ref")
        != (
            "ITER-008-BOUNDED-JAVA-SOURCE-SEMANTICS-CAPABILITY-"
            "QUALIFICATION-CANDIDATE@1"
        )
        or freeze.get("environment") != "EVALUATION_ONLY"
        or freeze.get("candidate_identity")
        != _candidate_identity(require_clean=True)
        or freeze.get("package_manifest") != _package_manifest()
        or freeze.get("proposal_contract") != _proposal_contract()
        or freeze.get("closed_inputs") != _closed_inputs()
        or freeze.get("external_model_called_during_freeze") is not False
        or freeze.get("hidden_canary_disclosed") is not False
        or freeze.get("production_activation") != "NOT_EXECUTED"
        or freeze.get("git_stage_commit_push") != "NOT_EXECUTED"
    ):
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "bounded capability freeze drifted from the candidate",
        )
    identity = freeze.get("candidate_identity")
    if not isinstance(identity, Mapping):
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "bounded capability candidate identity is invalid",
        )
    try:
        Digest(str(freeze["preflight_digest"]))
    except (TypeError, ValueError) as exc:
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "bounded capability preflight digest is invalid",
        ) from exc
    configuration = DeepSeekModelConfiguration()
    conformance = load_deepseek_chat_conformance_qualification(
        conformance_result_path.resolve(strict=True), configuration
    )
    suite, oracle = load_capability_inputs()
    evaluator_digest = (
        "sha256:" + hashlib.sha256(EVALUATOR_PATH.read_bytes()).hexdigest()
    )
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
        reference_strategy_ref=(
            f"standalone-stdlib-evaluator:{evaluator_digest}"
        ),
        resource_policy_ref=PINNED_RESOURCE_POLICY_REF,
        valid_for_seconds=604800,
    )
    scope = _capability_scope(configuration, conformance)
    provider = freeze.get("provider")
    dispatch = freeze.get("dispatch_contract")
    if (
        freeze.get("evaluation_definition") != _definition_document(definition)
        or freeze.get("metric_contract_digest")
        != digest_of(
            BOUNDED_JAVA_SOURCE_SEMANTICS_EVALUATION_METRIC_CONTRACT
        ).value
        or provider
        != {
            **scope,
            "credential_reference": configuration.secret_reference,
            "qualification_valid_until": conformance.valid_until.isoformat(),
        }
        or dispatch
        != {
            "status": "HELD_AWAITING_EXACT_USER_AUTHORIZATION",
            "authorization_scope": scope,
            "credential_read_before_authorization": False,
            "provider_socket_before_authorization": False,
        }
    ):
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "bounded capability Conformance binding drifted",
        )
    created_at = _parse_time(
        freeze.get("created_at"), "capability freeze creation time"
    )
    if created_at < _conformance_completed_at(
        conformance_result_path.resolve(strict=True)
    ):
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "bounded capability freeze predates Conformance completion",
        )
    return freeze


def _new_result_directory(authorization: Mapping[str, object]) -> Path:
    value = authorization.get("single_use_result_directory")
    if not isinstance(value, str):
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "authorized result directory is invalid",
        )
    result = Path(value)
    parent = result.parent.resolve(strict=True)
    if result != parent / result.name or result.exists() or result.is_symlink():
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "authorized result directory is not one new canonical path",
        )
    result.mkdir(mode=0o700)
    return result


def _verify_request_binding(
    request: Mapping[str, object],
    *,
    freeze: Mapping[str, object],
    phase: str,
    scope_owner: str,
) -> None:
    owner = freeze.get(scope_owner)
    scope = owner.get("authorization_scope") if isinstance(owner, Mapping) else None
    if (
        request.get("phase") != phase
        or request.get("freeze_ref") != freeze.get("freeze_ref")
        or request.get("freeze_digest") != freeze.get("document_digest")
        or not isinstance(scope, Mapping)
        or request.get("authorization_scope") != scope
    ):
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "external authorization request does not bind the exact freeze",
        )


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
        "sink_manifest_digest": (
            value.sink_manifest_digest.value
            if value.sink_manifest_digest
            else None
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


def _document(core: dict[str, object]) -> dict[str, object]:
    return {**core, "document_digest": digest_of([core["schema"], core]).value}


def _write_once(path: Path, value: object) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        remaining = memoryview(canonical_json_bytes(value))
        while remaining:
            remaining = remaining[os.write(descriptor, remaining) :]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


if __name__ == "__main__":
    raise SystemExit(main())
