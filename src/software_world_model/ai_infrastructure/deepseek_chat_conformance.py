"""Executable live conformance for the DeepSeek no-tools adapter.

The artifact is intentionally sanitized: it contains digests, counts, model
identities, and provider request identifiers, but never credentials, prompt
text, model output text, HTTP bodies, or the two synthetic canaries.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import secrets
import time
from typing import Callable, Mapping
import uuid

from software_world_model.cross_cutting import (
    Digest,
    DomainError,
    ErrorCode,
    canonical_json_bytes,
    digest_of,
)

from .deepseek_chat_adapter import (
    DeepSeekChatCompletionsNoToolsAdapter,
    DeepSeekChatCompletionsTransport,
    DeepSeekModelConfiguration,
    RecordingDeepSeekChatCompletionsTransport,
)
from .model_gateway import ProviderRequest, RenderedMessage
from .openai_responses_adapter import OutputSchemaDefinition, ProviderHTTPResponse


DEEPSEEK_CHAT_CONFORMANCE_FIXTURE_ID = "CC-DEEPSEEK-CHAT-NO-TOOLS-001"
DEEPSEEK_CHAT_CONFORMANCE_FIXTURE_VERSION = "1.0.0"
DEEPSEEK_CHAT_CONFORMANCE_RESULT_SCHEMA = "swm.deepseek-chat-conformance-result@1"
_RESULT_VALIDITY_DAYS = 30
_SCHEMA_PREFIX = "deepseek-conformance-live"
_WIRE_ALLOWLIST = frozenset(
    {
        "model",
        "messages",
        "stream",
        "max_tokens",
        "thinking",
        "response_format",
    }
)


@dataclass(frozen=True, slots=True)
class DeepSeekChatConformanceQualification:
    """Verified input required to construct a live-qualified DeepSeek adapter."""

    result_ref: str
    result_digest: Digest
    qualified_model_fingerprints: tuple[str, ...]
    adapter_version: str
    provider_configuration_fingerprint: Digest
    valid_until: datetime

    def validate(self, definition: object, at: datetime) -> bool:
        if at.tzinfo is None or at.utcoffset() is None:
            return False
        return (
            at.astimezone(timezone.utc) < self.valid_until
            and getattr(definition, "conformance_result_ref", None) == self.result_ref
            and getattr(definition, "adapter_version", None) == self.adapter_version
            and getattr(definition, "provider_configuration_fingerprint", None)
            == self.provider_configuration_fingerprint
            and getattr(definition, "model_ref", None)
            in self.qualified_model_fingerprints
        )


class _StaticTransport:
    def __init__(self, response: ProviderHTTPResponse) -> None:
        self.response = response
        self.calls = 0

    def post_json(self, **_: object) -> ProviderHTTPResponse:
        self.calls += 1
        return self.response


def run_deepseek_chat_conformance(
    *,
    configuration: DeepSeekModelConfiguration,
    transport: DeepSeekChatCompletionsTransport,
    environment: Mapping[str, str],
    operator: str,
    timeout_milliseconds: int,
    max_output_tokens: int,
    clock: Callable[[], datetime] | None = None,
    monotonic: Callable[[], float] | None = None,
    nonce_factory: Callable[[], str] | None = None,
    run_id_factory: Callable[[], str] | None = None,
) -> dict[str, object]:
    """Run exactly two synthetic calls and return a sanitized result candidate."""

    if not operator or operator != operator.strip():
        raise DomainError(ErrorCode.INVALID_ARGUMENT, "conformance operator is required")
    if timeout_milliseconds < 1 or max_output_tokens < 1:
        raise DomainError(ErrorCode.INVALID_ARGUMENT, "conformance resource bounds must be positive")
    secret = configuration.resolve_api_key(environment)
    now = clock or (lambda: datetime.now(timezone.utc))
    monotonic_clock = monotonic or time.monotonic
    nonce = nonce_factory or (lambda: secrets.token_hex(16))
    run_identifier = run_id_factory or (lambda: f"ccrun_{uuid.uuid4().hex}")
    run_id = run_identifier()
    if not isinstance(run_id, str) or not re.fullmatch(r"ccrun_[0-9a-f]{32}", run_id):
        raise DomainError(ErrorCode.INVALID_ARGUMENT, "conformance run ID is invalid")
    started_at = _aware_utc(now())
    started_tick = monotonic_clock()
    canaries = (nonce(), nonce())
    if any(not item or item != item.strip() for item in canaries) or canaries[0] == canaries[1]:
        raise DomainError(ErrorCode.INVALID_ARGUMENT, "conformance canaries must be distinct")

    schemas: dict[str, OutputSchemaDefinition] = {}
    for index, canary in enumerate(canaries, start=1):
        schema_ref = f"{_SCHEMA_PREFIX}-{index}@1"
        schemas[schema_ref] = OutputSchemaDefinition(
            f"deepseek_conformance_live_{index}",
            {
                "type": "object",
                "properties": {
                    "case": {"type": "string", "enum": [f"live-{index}"]},
                    "nonce": {"type": "string", "enum": [canary]},
                    "status": {"type": "string", "enum": ["ok"]},
                },
                "required": ["case", "nonce", "status"],
                "additionalProperties": False,
            },
        )
    recording = RecordingDeepSeekChatCompletionsTransport(transport)
    adapter = DeepSeekChatCompletionsNoToolsAdapter(
        transport=recording,
        configuration=configuration,
        output_schemas=schemas,
    )

    responses = []
    failure: DomainError | None = None
    for index, canary in enumerate(canaries, start=1):
        try:
            responses.append(
                adapter.invoke(
                    _live_request(
                        configuration=configuration,
                        schema_ref=f"{_SCHEMA_PREFIX}-{index}@1",
                        case_number=index,
                        canary=canary,
                        timeout_milliseconds=timeout_milliseconds,
                        max_output_tokens=max_output_tokens,
                    )
                )
            )
        except DomainError as exc:
            failure = exc
            break

    cases = _evaluate_cases(
        configuration=configuration,
        recording=recording,
        responses=tuple(responses),
        canaries=canaries,
        secret=secret,
        live_failure=failure,
    )
    outcome = "PASS" if all(item["outcome"] == "PASS" for item in cases) else "FAIL"
    completed_at = _aware_utc(now())
    implementation = current_deepseek_implementation_manifest()
    request_ids = [
        response.provider_request_id
        for response in responses
        if response.provider_request_id is not None
    ]
    actual_models = sorted(
        {
            response.actual_model_fingerprint
            for response in responses
            if response.actual_model_fingerprint is not None
        }
    )
    result_core: dict[str, object] = {
        "schema": DEEPSEEK_CHAT_CONFORMANCE_RESULT_SCHEMA,
        "fixture_id": DEEPSEEK_CHAT_CONFORMANCE_FIXTURE_ID,
        "fixture_version": DEEPSEEK_CHAT_CONFORMANCE_FIXTURE_VERSION,
        "fixture_digest": deepseek_chat_conformance_fixture_digest().value,
        "run_id": run_id,
        "outcome": outcome,
        "operator": operator,
        "started_at": _time(started_at),
        "completed_at": _time(completed_at),
        "duration_milliseconds": max(
            0, round((monotonic_clock() - started_tick) * 1000)
        ),
        "provider": {
            "provider_type": configuration.provider_type,
            "protocol": "DEEPSEEK_OPENAI_FORMAT_CHAT_COMPLETIONS",
            "endpoint": configuration.endpoint,
            "configuration_fingerprint": configuration.fingerprint.value,
            "secret_reference": configuration.secret_reference,
            "credential_configured": True,
        },
        "adapter": {
            "adapter_version": configuration.adapter_version,
            "implementation_digest": implementation["aggregate_digest"],
            "implementation_files": implementation["files"],
        },
        "model": {
            "requested_model_ref": configuration.model_ref,
            "expected_actual_model_fingerprint": configuration.actual_model_fingerprint,
            "actual_model_fingerprints": actual_models,
            "identity_policy": "REQUEST_MODEL_AND_EXACT_RESPONSE_MODEL_REQUIRED",
            "thinking_mode": "DISABLED",
        },
        "execution": {
            "request_count": len(recording.requests),
            "provider_request_ids": request_ids,
            "request_body_digests": [
                _raw_digest(item.body).value for item in recording.requests
            ],
            "input_tokens": sum(response.input_tokens or 0 for response in responses),
            "output_tokens": sum(response.output_tokens or 0 for response in responses),
            "usage_complete": bool(responses)
            and all(response.usage_complete for response in responses),
            "raw_prompt_persisted": False,
            "raw_response_persisted": False,
        },
        "environment": {
            "python_implementation": platform.python_implementation(),
            "python_version": platform.python_version(),
            "operating_system": platform.system(),
            "machine": platform.machine(),
            "network_mode": "DIRECT_HTTPS_PROXY_DISABLED",
            "tls_verification": "ENABLED",
        },
        "cases": cases,
        "validity": {
            "status": "VALID" if outcome == "PASS" else "NOT_ISSUED",
            "valid_until": (
                _time(completed_at + timedelta(days=_RESULT_VALIDITY_DAYS))
                if outcome == "PASS"
                else None
            ),
            "invalidated_by": [
                "fixture_digest_change",
                "implementation_digest_change",
                "configuration_fingerprint_change",
                "endpoint_change",
                "adapter_version_change",
                "model_identity_change",
                "thinking_mode_change",
                "provider_protocol_change",
                "valid_until_elapsed",
            ],
        },
        "failure": _safe_failure(failure),
    }
    return {**result_core, "result_digest": digest_of(result_core).value}


def seal_deepseek_chat_conformance_result(
    result: Mapping[str, object], result_directory: str | Path
) -> Path:
    verify_deepseek_chat_conformance_document(result, require_pass=False)
    directory = Path(result_directory)
    directory.mkdir(parents=True, exist_ok=True)
    run_id = result.get("run_id")
    if not isinstance(run_id, str) or not re.fullmatch(r"ccrun_[0-9a-f]{32}", run_id):
        raise DomainError(ErrorCode.INVALID_ARGUMENT, "conformance result has no run ID")
    path = directory / f"{DEEPSEEK_CHAT_CONFORMANCE_FIXTURE_ID}-{run_id}.json"
    payload = json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8") + b"\n"
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "conformance result path already exists and cannot be overwritten",
        ) from exc
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    return path


def load_deepseek_chat_conformance_qualification(
    path: str | Path,
    configuration: DeepSeekModelConfiguration,
    *,
    now: datetime | None = None,
) -> DeepSeekChatConformanceQualification:
    try:
        document = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "DeepSeek conformance result cannot be read",
        ) from exc
    if not isinstance(document, dict):
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "DeepSeek conformance result is not an object",
        )
    verify_deepseek_chat_conformance_document(document, require_pass=True)
    provider = document.get("provider")
    adapter = document.get("adapter")
    model = document.get("model")
    validity = document.get("validity")
    if not all(isinstance(item, dict) for item in (provider, adapter, model, validity)):
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "DeepSeek conformance dependencies are missing",
        )
    implementation = current_deepseek_implementation_manifest()
    if (
        provider.get("configuration_fingerprint") != configuration.fingerprint.value
        or provider.get("provider_type") != configuration.provider_type
        or adapter.get("adapter_version") != configuration.adapter_version
        or adapter.get("implementation_digest") != implementation["aggregate_digest"]
        or document.get("fixture_digest")
        != deepseek_chat_conformance_fixture_digest().value
        or model.get("requested_model_ref") != configuration.model_ref
        or model.get("expected_actual_model_fingerprint")
        != configuration.actual_model_fingerprint
        or model.get("thinking_mode") != "DISABLED"
    ):
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "DeepSeek conformance result is stale for the current implementation or configuration",
        )
    if model.get("actual_model_fingerprints") != [configuration.actual_model_fingerprint]:
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "DeepSeek conformance did not prove the configured exact response model identity",
        )
    valid_until_value = validity.get("valid_until")
    if validity.get("status") != "VALID" or not isinstance(valid_until_value, str):
        raise DomainError(ErrorCode.QUALIFICATION_INVALID, "DeepSeek conformance is not valid")
    try:
        valid_until = _parse_time(valid_until_value)
        started_at = _parse_time(str(document["started_at"]))
        completed_at = _parse_time(str(document["completed_at"]))
    except ValueError as exc:
        raise DomainError(ErrorCode.QUALIFICATION_INVALID, "DeepSeek validity time is invalid") from exc
    current = _aware_utc(now or datetime.now(timezone.utc))
    if completed_at < started_at or completed_at > current:
        raise DomainError(ErrorCode.QUALIFICATION_INVALID, "DeepSeek conformance run time is invalid")
    if valid_until != completed_at + timedelta(days=_RESULT_VALIDITY_DAYS):
        raise DomainError(ErrorCode.QUALIFICATION_INVALID, "DeepSeek conformance validity window is invalid")
    if current >= valid_until:
        raise DomainError(ErrorCode.QUALIFICATION_INVALID, "DeepSeek conformance result has expired")
    result_digest = Digest(str(document["result_digest"]))
    return DeepSeekChatConformanceQualification(
        result_ref=f"{DEEPSEEK_CHAT_CONFORMANCE_FIXTURE_ID}:{result_digest.value}",
        result_digest=result_digest,
        qualified_model_fingerprints=configuration.qualified_model_identities,
        adapter_version=configuration.adapter_version,
        provider_configuration_fingerprint=configuration.fingerprint,
        valid_until=valid_until,
    )


def verify_deepseek_chat_conformance_document(
    document: Mapping[str, object], *, require_pass: bool
) -> None:
    expected_keys = {
        "schema",
        "fixture_id",
        "fixture_version",
        "fixture_digest",
        "run_id",
        "outcome",
        "operator",
        "started_at",
        "completed_at",
        "duration_milliseconds",
        "provider",
        "adapter",
        "model",
        "execution",
        "environment",
        "cases",
        "validity",
        "failure",
        "result_digest",
    }
    if set(document) != expected_keys:
        _invalid("DeepSeek conformance result shape is invalid")
    if (
        document.get("schema") != DEEPSEEK_CHAT_CONFORMANCE_RESULT_SCHEMA
        or document.get("fixture_id") != DEEPSEEK_CHAT_CONFORMANCE_FIXTURE_ID
        or document.get("fixture_version") != DEEPSEEK_CHAT_CONFORMANCE_FIXTURE_VERSION
        or not isinstance(document.get("run_id"), str)
        or not re.fullmatch(r"ccrun_[0-9a-f]{32}", str(document.get("run_id")))
        or document.get("outcome") not in {"PASS", "FAIL"}
    ):
        _invalid("DeepSeek conformance identity is invalid")
    supplied = document.get("result_digest")
    try:
        supplied_digest = Digest(str(supplied))
    except ValueError as exc:
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "DeepSeek conformance digest is invalid",
        ) from exc
    core = {key: value for key, value in document.items() if key != "result_digest"}
    if digest_of(core) != supplied_digest:
        _invalid("DeepSeek conformance digest does not verify")
    cases = document.get("cases")
    expected_case_ids = [f"CC-DEEPSEEK-{number:02d}" for number in range(1, 13)]
    if (
        not isinstance(cases, list)
        or [item.get("case_id") for item in cases if isinstance(item, dict)]
        != expected_case_ids
    ):
        _invalid("DeepSeek conformance case set is incomplete")
    for item in cases:
        if (
            not isinstance(item, dict)
            or set(item) != {"case_id", "outcome", "evidence_kind", "evidence_digest"}
            or item.get("outcome") not in {"PASS", "FAIL"}
            or not isinstance(item.get("evidence_kind"), str)
        ):
            _invalid("DeepSeek conformance case is invalid")
        try:
            Digest(str(item.get("evidence_digest")))
        except ValueError as exc:
            raise DomainError(
                ErrorCode.QUALIFICATION_INVALID,
                "DeepSeek conformance case evidence digest is invalid",
            ) from exc
    case_pass = all(item["outcome"] == "PASS" for item in cases)
    validity = document.get("validity")
    if not isinstance(validity, dict):
        _invalid("DeepSeek conformance validity is missing")
    if document.get("outcome") == "PASS":
        if not case_pass or document.get("failure") is not None or validity.get("status") != "VALID":
            _invalid("DeepSeek PASS result is internally inconsistent")
    elif case_pass or validity.get("status") != "NOT_ISSUED":
        _invalid("DeepSeek FAIL result is internally inconsistent")
    if require_pass and (document.get("outcome") != "PASS" or not case_pass):
        _invalid("DeepSeek conformance did not pass")


def current_deepseek_implementation_manifest() -> dict[str, object]:
    package_root = Path(__file__).resolve().parents[1]
    relative_files = (
        "ai_infrastructure/deepseek_chat_adapter.py",
        "ai_infrastructure/deepseek_chat_conformance.py",
        "ai_infrastructure/direct_https.py",
        "ai_infrastructure/model_gateway.py",
        "ai_infrastructure/openai_responses_adapter.py",
        "interface/deepseek_provider_cli.py",
    )
    files = []
    for relative in relative_files:
        path = package_root / relative
        try:
            payload = path.read_bytes()
        except OSError as exc:
            raise DomainError(
                ErrorCode.QUALIFICATION_INVALID,
                f"qualified implementation file is unavailable: {relative}",
            ) from exc
        files.append({"path": relative, "digest": _raw_digest(payload).value})
    return {"files": files, "aggregate_digest": digest_of(files).value}


def deepseek_chat_conformance_fixture_digest() -> Digest:
    return digest_of(
        {
            "fixture_id": DEEPSEEK_CHAT_CONFORMANCE_FIXTURE_ID,
            "fixture_version": DEEPSEEK_CHAT_CONFORMANCE_FIXTURE_VERSION,
            "case_ids": [f"CC-DEEPSEEK-{number:02d}" for number in range(1, 13)],
            "live_call_count": 2,
            "wire_allowlist": sorted(_WIRE_ALLOWLIST),
            "result_schema": DEEPSEEK_CHAT_CONFORMANCE_RESULT_SCHEMA,
        }
    )


def _live_request(
    *,
    configuration: DeepSeekModelConfiguration,
    schema_ref: str,
    case_number: int,
    canary: str,
    timeout_milliseconds: int,
    max_output_tokens: int,
) -> ProviderRequest:
    system = "Return exactly one JSON object matching the supplied strict schema."
    user = f"Conformance case live-{case_number}; copy nonce exactly: {canary}"
    core = {
        "model_ref": configuration.model_ref,
        "messages": (system, user),
        "output_schema_ref": schema_ref,
        "max_output_tokens": max_output_tokens,
        "timeout_milliseconds": timeout_milliseconds,
    }
    return ProviderRequest(
        model_ref=configuration.model_ref,
        messages=(
            RenderedMessage("system", system, "cc-instruction", digest_of(system)),
            RenderedMessage("user", user, f"cc-live-{case_number}", digest_of(user)),
        ),
        output_schema_ref=schema_ref,
        tools=(),
        store=False,
        stream=False,
        max_output_tokens=max_output_tokens,
        timeout_milliseconds=timeout_milliseconds,
        metadata=(("purpose", "adapter-conformance"),),
        digest=digest_of(core),
    )


def _evaluate_cases(
    *,
    configuration: DeepSeekModelConfiguration,
    recording: RecordingDeepSeekChatCompletionsTransport,
    responses: tuple[object, ...],
    canaries: tuple[str, str],
    secret: str,
    live_failure: DomainError | None,
) -> list[dict[str, object]]:
    bodies = []
    for request in recording.requests:
        try:
            decoded = json.loads(request.body)
        except (UnicodeDecodeError, json.JSONDecodeError):
            decoded = {}
        bodies.append(decoded if isinstance(decoded, dict) else {})

    def case(number: int, passed: bool, evidence: str, payload: object) -> dict[str, object]:
        return {
            "case_id": f"CC-DEEPSEEK-{number:02d}",
            "outcome": "PASS" if passed else "FAIL",
            "evidence_kind": evidence,
            "evidence_digest": digest_of(payload).value,
        }

    two_live = len(recording.requests) == 2 and len(responses) == 2 and live_failure is None
    exact_endpoint = two_live and all(
        item.endpoint == configuration.endpoint for item in recording.requests
    )
    allowlisted = two_live and all(set(body) == _WIRE_ALLOWLIST for body in bodies)
    no_tools = two_live and all(
        not ({"tools", "tool_choice", "parallel_tool_calls"} & set(body))
        and all(
            isinstance(message, dict) and message.get("role") != "tool"
            for message in body.get("messages", [])
        )
        for body in bodies
    )
    stateless = two_live and all(
        not (
            {
                "conversation",
                "previous_response_id",
                "prompt",
                "context_management",
                "store",
                "user_id",
            }
            & set(body)
        )
        and body.get("stream") is False
        for body in bodies
    )
    strict = two_live and all(
        body.get("response_format") == {"type": "json_object"}
        and isinstance(body.get("messages"), list)
        and len(body["messages"]) >= 2
        and body["messages"][0].get("role") == "system"
        and "closed JSON Schema" in body["messages"][0].get("content", "")
        and '"additionalProperties":false' in body["messages"][0].get("content", "")
        and body.get("thinking") == {"type": "disabled"}
        for body in bodies
    )
    separated = (
        two_live
        and canaries[0].encode() in recording.requests[0].body
        and canaries[0].encode() not in recording.requests[1].body
    )
    local_denials = _negative_oracles(configuration)
    model_identity = two_live and all(
        getattr(response, "actual_model_fingerprint", None)
        == configuration.actual_model_fingerprint
        for response in responses
    )
    usage = two_live and all(getattr(response, "usage_complete", False) for response in responses)
    request_ids = (
        two_live
        and len({getattr(response, "provider_request_id", None) for response in responses}) == 2
        and all(getattr(response, "provider_request_id", None) for response in responses)
    )
    serialized_public = canonical_json_bytes(
        configuration.public_status(
            {configuration.api_key_environment_variable: secret}
        )
    )
    secret_clean = secret.encode() not in serialized_public and all(
        secret.encode() not in request.body for request in recording.requests
    )
    admission_held = _adapter_capabilities_offline(configuration) and all(
        local_denials.values()
    )
    return [
        case(1, exact_endpoint, "LIVE_WIRE", {"endpoint": configuration.endpoint, "count": len(recording.requests)}),
        case(2, allowlisted, "LIVE_WIRE", {"body_keys": [sorted(body) for body in bodies]}),
        case(3, no_tools, "LIVE_WIRE", {"tool_fields_absent": no_tools}),
        case(4, stateless, "LIVE_WIRE", {"state_fields_absent": stateless}),
        case(5, strict, "LIVE_WIRE_AND_RESPONSE", {"strict": strict, "responses": len(responses)}),
        case(6, separated, "LIVE_TWO_CALL_CANARY", {"first_absent_from_second": separated}),
        case(7, all(local_denials.values()), "OFFLINE_NEGATIVE_ORACLE", local_denials),
        case(8, model_identity, "LIVE_RESPONSE", {"exact_identity": model_identity}),
        case(9, usage, "LIVE_RESPONSE", {"usage_complete": usage}),
        case(10, bool(request_ids), "LIVE_RESPONSE", {"unique_request_ids": bool(request_ids)}),
        case(11, secret_clean, "LIVE_WIRE_AND_LOCAL_RESULT", {"secret_reference_only": secret_clean}),
        case(12, admission_held, "OFFLINE_ADMISSION_ORACLE", {"activation_held": admission_held}),
    ]


def _negative_oracles(configuration: DeepSeekModelConfiguration) -> dict[str, bool]:
    schema = OutputSchemaDefinition(
        "negative_oracle",
        {
            "type": "object",
            "properties": {"status": {"type": "string", "enum": ["ok"]}},
            "required": ["status"],
            "additionalProperties": False,
        },
    )
    valid_request = ProviderRequest(
        model_ref=configuration.model_ref,
        messages=(RenderedMessage("user", "fixture", "fixture", digest_of("fixture")),),
        output_schema_ref="negative@1",
        tools=(),
        store=False,
        stream=False,
        max_output_tokens=16,
        timeout_milliseconds=100,
        metadata=(),
        digest=digest_of({"negative": "oracle"}),
    )

    tool_input_transport = _StaticTransport(
        _fake_response(configuration.actual_model_fingerprint, '{"status":"ok"}')
    )
    input_adapter = _adapter(configuration, schema, tool_input_transport)
    try:
        input_adapter.invoke(
            ProviderRequest(
                model_ref=valid_request.model_ref,
                messages=valid_request.messages,
                output_schema_ref=valid_request.output_schema_ref,
                tools=({"type": "function"},),
                store=False,
                stream=False,
                max_output_tokens=valid_request.max_output_tokens,
                timeout_milliseconds=valid_request.timeout_milliseconds,
                metadata=(),
                digest=valid_request.digest,
            )
        )
        tool_input_denied = False
    except DomainError as exc:
        tool_input_denied = (
            exc.code is ErrorCode.PROVIDER_OUTPUT_FORBIDDEN
            and tool_input_transport.calls == 0
        )

    tool_payload = _fake_payload(configuration.actual_model_fingerprint, '{"status":"ok"}')
    tool_payload["choices"][0]["message"]["tool_calls"] = [{"id": "fixture-tool"}]
    tool_adapter = _adapter(
        configuration,
        schema,
        _StaticTransport(
            ProviderHTTPResponse(200, {"x-request-id": "fixture-tool"}, json.dumps(tool_payload).encode())
        ),
    )
    try:
        tool_adapter.invoke(valid_request)
        tool_output_denied = False
    except DomainError as exc:
        tool_output_denied = exc.code is ErrorCode.PROVIDER_OUTPUT_FORBIDDEN

    reasoning_payload = _fake_payload(configuration.actual_model_fingerprint, '{"status":"ok"}')
    reasoning_payload["choices"][0]["message"]["reasoning_content"] = "fixture reasoning"
    reasoning_adapter = _adapter(
        configuration,
        schema,
        _StaticTransport(
            ProviderHTTPResponse(200, {"x-request-id": "fixture-reasoning"}, json.dumps(reasoning_payload).encode())
        ),
    )
    try:
        reasoning_adapter.invoke(valid_request)
        reasoning_output_denied = False
    except DomainError as exc:
        reasoning_output_denied = exc.code is ErrorCode.PROVIDER_OUTPUT_FORBIDDEN

    schema_adapter = _adapter(
        configuration,
        schema,
        _StaticTransport(
            _fake_response(configuration.actual_model_fingerprint, '{"status":"wrong"}')
        ),
    )
    try:
        schema_adapter.invoke(valid_request)
        invalid_schema_denied = False
    except DomainError as exc:
        invalid_schema_denied = exc.code is ErrorCode.STRUCTURED_OUTPUT_INVALID

    fenced_adapter = _adapter(
        configuration,
        schema,
        _StaticTransport(
            _fake_response(configuration.actual_model_fingerprint, '```json\n{"status":"ok"}\n```')
        ),
    )
    try:
        fenced = fenced_adapter.invoke(valid_request)
        fenced_json_normalized = (
            fenced.output_text == '{"status":"ok"}'
            and fenced.output_normalization == "MARKDOWN_JSON_FENCE_V1"
        )
    except DomainError:
        fenced_json_normalized = False

    trailing_adapter = _adapter(
        configuration,
        schema,
        _StaticTransport(
            _fake_response(
                configuration.actual_model_fingerprint,
                '```json\n{"status":"ok"}\n```\nResult.',
            )
        ),
    )
    try:
        trailing_adapter.invoke(valid_request)
        trailing_text_denied = False
    except DomainError as exc:
        trailing_text_denied = exc.code is ErrorCode.STRUCTURED_OUTPUT_INVALID

    return {
        "tool_input_denied": tool_input_denied,
        "tool_output_denied": tool_output_denied,
        "reasoning_output_denied": reasoning_output_denied,
        "invalid_schema_denied": invalid_schema_denied,
        "fenced_json_normalized": fenced_json_normalized,
        "trailing_text_denied": trailing_text_denied,
    }


def _adapter(
    configuration: DeepSeekModelConfiguration,
    schema: OutputSchemaDefinition,
    transport: DeepSeekChatCompletionsTransport,
) -> DeepSeekChatCompletionsNoToolsAdapter:
    return DeepSeekChatCompletionsNoToolsAdapter(
        transport=transport,
        configuration=configuration,
        output_schemas={"negative@1": schema},
    )


def _adapter_capabilities_offline(configuration: DeepSeekModelConfiguration) -> bool:
    schema = OutputSchemaDefinition(
        "negative_oracle",
        {
            "type": "object",
            "properties": {"status": {"type": "string", "enum": ["ok"]}},
            "required": ["status"],
            "additionalProperties": False,
        },
    )
    adapter = _adapter(
        configuration,
        schema,
        _StaticTransport(
            _fake_response(configuration.actual_model_fingerprint, '{"status":"ok"}')
        ),
    )
    return adapter.capabilities.conformance_level.value == "OFFLINE_FIXTURE"


def _fake_payload(model: str, content: str) -> dict[str, object]:
    return {
        "id": "chatcmpl_fixture",
        "object": "chat.completion",
        "model": model,
        "system_fingerprint": "fp_fixture",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
    }


def _fake_response(model: str, content: str) -> ProviderHTTPResponse:
    return ProviderHTTPResponse(
        200,
        {"x-request-id": "fixture-request"},
        json.dumps(_fake_payload(model, content)).encode("utf-8"),
    )


def _safe_failure(failure: DomainError | None) -> dict[str, object] | None:
    if failure is None:
        return None
    details = {
        key: value
        for key, value in failure.details.items()
        if key in {"http_status", "provider_error_code", "provider_error_type", "provider_request_id"}
    }
    return {"code": failure.code.value, "details": details}


def _raw_digest(payload: bytes) -> Digest:
    return Digest(f"sha256:{hashlib.sha256(payload).hexdigest()}")


def _aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise DomainError(ErrorCode.INVALID_ARGUMENT, "conformance clock must be timezone-aware")
    return value.astimezone(timezone.utc)


def _time(value: datetime) -> str:
    return value.isoformat(timespec="microseconds").replace("+00:00", "Z")


def _parse_time(value: str) -> datetime:
    return _aware_utc(datetime.fromisoformat(value.replace("Z", "+00:00")))


def _invalid(message: str) -> None:
    raise DomainError(ErrorCode.QUALIFICATION_INVALID, message)


__all__ = [
    "DEEPSEEK_CHAT_CONFORMANCE_FIXTURE_ID",
    "DEEPSEEK_CHAT_CONFORMANCE_FIXTURE_VERSION",
    "DEEPSEEK_CHAT_CONFORMANCE_RESULT_SCHEMA",
    "DeepSeekChatConformanceQualification",
    "current_deepseek_implementation_manifest",
    "deepseek_chat_conformance_fixture_digest",
    "load_deepseek_chat_conformance_qualification",
    "run_deepseek_chat_conformance",
    "seal_deepseek_chat_conformance_result",
    "verify_deepseek_chat_conformance_document",
]
