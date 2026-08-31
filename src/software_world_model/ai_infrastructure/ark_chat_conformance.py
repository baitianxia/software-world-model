"""Executable live conformance for the Volcengine Ark no-tools adapter.

The result intentionally contains only digests and provider request identities.
Prompts, model output text, HTTP response bodies, and credentials are never
serialized into the conformance artifact.
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

from .model_gateway import ProviderOutputRejected, ProviderRequest, RenderedMessage
from .openai_responses_adapter import OutputSchemaDefinition, ProviderHTTPResponse
from .volcengine_ark_chat_adapter import (
    DEFAULT_VOLCENGINE_ARK_CHAT_COMPLETIONS_ENDPOINT,
    DEFAULT_VOLCENGINE_ARK_CONNECTION_POLICY,
    DEFAULT_VOLCENGINE_ARK_CREDENTIAL_RESOLUTION_POLICY,
    DEFAULT_VOLCENGINE_ARK_MAXIMUM_HTTP_DISPATCHES_PER_TLS_SESSION,
    DEFAULT_VOLCENGINE_ARK_MAXIMUM_PRE_DISPATCH_TLS_HANDSHAKES_PER_REQUEST,
    ChatCompletionsTransport,
    RecordingChatCompletionsTransport,
    VolcengineArkChatCompletionsNoToolsAdapter,
    VolcengineArkModelConfiguration,
    ark_transport_session_audit,
    verify_ark_transport_session_audit,
)


ARK_CHAT_CONFORMANCE_FIXTURE_ID = "CC-ARK-CHAT-NO-TOOLS-001"
ARK_CHAT_CONFORMANCE_FIXTURE_VERSION = "1.10.0"
ARK_CHAT_CONFORMANCE_RESULT_SCHEMA = "swm.ark-chat-conformance-result@2"
_RESULT_VALIDITY_DAYS = 30
_SCHEMA_PREFIX = "ark-conformance-live"
_WIRE_ALLOWLIST = frozenset(
    {
        "model",
        "messages",
        "tools",
        "tool_choice",
        "parallel_tool_calls",
        "stream",
        "stream_options",
        "n",
        "max_tokens",
        "response_format",
    }
)


@dataclass(frozen=True, slots=True)
class ArkChatConformanceQualification:
    """Verified input required to construct a live-qualified Ark adapter."""

    result_ref: str
    result_digest: Digest
    qualified_model_fingerprints: tuple[str, ...]
    adapter_version: str
    provider_configuration_fingerprint: Digest
    valid_until: datetime

    def validate(self, definition: object, at: datetime) -> bool:
        """Satisfy the Application adapter-conformance verifier boundary."""

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


def run_ark_chat_conformance(
    *,
    configuration: VolcengineArkModelConfiguration,
    transport: ChatCompletionsTransport,
    environment: Mapping[str, str],
    operator: str,
    timeout_milliseconds: int,
    max_output_tokens: int,
    clock: Callable[[], datetime] | None = None,
    monotonic: Callable[[], float] | None = None,
    nonce_factory: Callable[[], str] | None = None,
    run_id_factory: Callable[[], str] | None = None,
) -> dict[str, object]:
    """Run and return one sanitized immutable-result candidate.

    Provider transport exceptions deliberately escape this function: neither a
    known pre-HTTP unavailability nor an unknown dispatched outcome can be
    converted into PASS or FAIL evidence.
    """

    if not operator or operator != operator.strip():
        raise DomainError(ErrorCode.INVALID_ARGUMENT, "conformance operator is required")
    if timeout_milliseconds < 1 or max_output_tokens < 1:
        raise DomainError(ErrorCode.INVALID_ARGUMENT, "conformance resource bounds must be positive")
    # The credential map is intentionally not inspected here.  The live
    # transport owns credential resolution after each verified TLS handshake.
    _ = environment
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
            f"ark_conformance_live_{index}",
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
    recording = RecordingChatCompletionsTransport(transport)
    adapter = VolcengineArkChatCompletionsNoToolsAdapter(
        transport=recording,
        configuration=configuration,
        output_schemas=schemas,
    )

    responses = []
    rejected_responses = []
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
        except ProviderOutputRejected as exc:
            rejected_responses.append(exc.response)
            failure = exc
            break
        except DomainError as exc:
            failure = exc
            break

    transport_session = ark_transport_session_audit(transport)
    cases = _evaluate_cases(
        configuration=configuration,
        recording=recording,
        responses=tuple(responses),
        canaries=canaries,
        transport_session=transport_session,
        live_failure=failure,
    )
    outcome = "PASS" if all(item["outcome"] == "PASS" for item in cases) else "FAIL"
    completed_at = _aware_utc(now())
    implementation = current_ark_implementation_manifest()
    fixture = _fixture_manifest()
    completed_responses = (*responses, *rejected_responses)
    request_ids = [
        response.provider_request_id
        for response in completed_responses
        if response.provider_request_id is not None
    ]
    total_input_tokens = sum(
        response.input_tokens or 0 for response in completed_responses
    )
    total_output_tokens = sum(
        response.output_tokens or 0 for response in completed_responses
    )
    actual_models = sorted(
        {
            response.actual_model_fingerprint
            for response in completed_responses
            if response.actual_model_fingerprint is not None
        }
    )
    result_core: dict[str, object] = {
        "schema": ARK_CHAT_CONFORMANCE_RESULT_SCHEMA,
        "fixture_id": ARK_CHAT_CONFORMANCE_FIXTURE_ID,
        "fixture_version": ARK_CHAT_CONFORMANCE_FIXTURE_VERSION,
        "fixture_digest": fixture.value,
        "run_id": run_id,
        "outcome": outcome,
        "operator": operator,
        "started_at": _time(started_at),
        "completed_at": _time(completed_at),
        "duration_milliseconds": max(0, round((monotonic_clock() - started_tick) * 1000)),
        "provider": {
            "provider_type": configuration.provider_type,
            "protocol": "OPENAI_COMPATIBLE_CHAT_COMPLETIONS",
            "endpoint": configuration.endpoint,
            "configuration_fingerprint": configuration.fingerprint.value,
            "secret_reference": configuration.secret_reference,
            "credential_configured": (
                transport_session["credential_resolution_success_count"] > 0
            ),
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
            "identity_policy": "REQUEST_ALIAS_AND_EXACT_RESPONSE_ID_REQUIRED",
        },
        "execution": {
            "request_count": len(recording.requests),
            "provider_request_ids": request_ids,
            "request_body_digests": [
                _raw_digest(item.body).value for item in recording.requests
            ],
            "input_tokens": total_input_tokens,
            "output_tokens": total_output_tokens,
            "usage_complete": bool(completed_responses)
            and all(
                response.usage_complete for response in completed_responses
            ),
            "raw_prompt_persisted": False,
            "raw_response_persisted": False,
            "transport_session": transport_session,
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
                "provider_protocol_change",
                "valid_until_elapsed",
            ],
        },
        "failure": _safe_failure(failure),
    }
    result_digest = digest_of(result_core)
    return {**result_core, "result_digest": result_digest.value}


def seal_ark_chat_conformance_result(
    result: Mapping[str, object], result_directory: str | Path
) -> Path:
    """Create a new evidence file without ever replacing an existing file."""

    verify_ark_chat_conformance_document(result, require_pass=False)
    directory = Path(result_directory)
    directory.mkdir(parents=True, exist_ok=True)
    run_id = result.get("run_id")
    if not isinstance(run_id, str) or not re.fullmatch(r"ccrun_[0-9a-f]{32}", run_id):
        raise DomainError(ErrorCode.INVALID_ARGUMENT, "conformance result has no run ID")
    path = directory / f"{ARK_CHAT_CONFORMANCE_FIXTURE_ID}-{run_id}.json"
    payload = json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8") + b"\n"
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "conformance result path already exists and cannot be overwritten",
        ) from exc
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        # Preserve the partial file as evidence instead of hiding a failed seal.
        raise
    return path


def load_ark_chat_conformance_qualification(
    path: str | Path,
    configuration: VolcengineArkModelConfiguration,
    *,
    now: datetime | None = None,
) -> ArkChatConformanceQualification:
    """Verify a sealed PASS result and its current local dependencies."""

    try:
        document = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "Ark conformance result cannot be read",
        ) from exc
    if not isinstance(document, dict):
        raise DomainError(ErrorCode.QUALIFICATION_INVALID, "Ark conformance result is not an object")
    verify_ark_chat_conformance_document(document, require_pass=True)
    provider = document.get("provider")
    adapter = document.get("adapter")
    model = document.get("model")
    validity = document.get("validity")
    if not all(isinstance(item, dict) for item in (provider, adapter, model, validity)):
        raise DomainError(ErrorCode.QUALIFICATION_INVALID, "Ark conformance dependencies are missing")
    implementation = current_ark_implementation_manifest()
    if (
        provider.get("configuration_fingerprint") != configuration.fingerprint.value
        or adapter.get("adapter_version") != configuration.adapter_version
        or adapter.get("implementation_digest") != implementation["aggregate_digest"]
        or document.get("fixture_digest") != _fixture_manifest().value
        or model.get("requested_model_ref") != configuration.model_ref
        or model.get("expected_actual_model_fingerprint")
        != configuration.actual_model_fingerprint
    ):
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "Ark conformance result is stale for the current implementation or configuration",
        )
    actual_models = model.get("actual_model_fingerprints")
    if actual_models != [configuration.actual_model_fingerprint]:
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "Ark conformance did not prove the configured exact response model identity",
        )
    valid_until_value = validity.get("valid_until")
    if validity.get("status") != "VALID" or not isinstance(valid_until_value, str):
        raise DomainError(ErrorCode.QUALIFICATION_INVALID, "Ark conformance is not valid")
    try:
        valid_until = _parse_time(valid_until_value)
        started_at = _parse_time(str(document["started_at"]))
        completed_at = _parse_time(str(document["completed_at"]))
    except ValueError as exc:
        raise DomainError(ErrorCode.QUALIFICATION_INVALID, "Ark validity time is invalid") from exc
    current = _aware_utc(now or datetime.now(timezone.utc))
    if completed_at < started_at or completed_at > current:
        raise DomainError(ErrorCode.QUALIFICATION_INVALID, "Ark conformance run time is invalid")
    if valid_until != completed_at + timedelta(days=_RESULT_VALIDITY_DAYS):
        raise DomainError(ErrorCode.QUALIFICATION_INVALID, "Ark conformance validity window is invalid")
    if current >= valid_until:
        raise DomainError(ErrorCode.QUALIFICATION_INVALID, "Ark conformance result has expired")
    result_digest = Digest(str(document["result_digest"]))
    return ArkChatConformanceQualification(
        result_ref=f"{ARK_CHAT_CONFORMANCE_FIXTURE_ID}:{result_digest.value}",
        result_digest=result_digest,
        qualified_model_fingerprints=configuration.qualified_model_identities,
        adapter_version=configuration.adapter_version,
        provider_configuration_fingerprint=configuration.fingerprint,
        valid_until=valid_until,
    )


def verify_ark_chat_conformance_document(
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
        raise DomainError(ErrorCode.QUALIFICATION_INVALID, "Ark conformance result shape is invalid")
    if (
        document.get("schema") != ARK_CHAT_CONFORMANCE_RESULT_SCHEMA
        or document.get("fixture_id") != ARK_CHAT_CONFORMANCE_FIXTURE_ID
        or document.get("fixture_version") != ARK_CHAT_CONFORMANCE_FIXTURE_VERSION
        or not isinstance(document.get("run_id"), str)
        or not re.fullmatch(r"ccrun_[0-9a-f]{32}", str(document.get("run_id")))
        or document.get("outcome") not in {"PASS", "FAIL"}
    ):
        raise DomainError(ErrorCode.QUALIFICATION_INVALID, "Ark conformance identity is invalid")
    supplied = document.get("result_digest")
    if not isinstance(supplied, str):
        raise DomainError(ErrorCode.QUALIFICATION_INVALID, "Ark conformance digest is missing")
    try:
        supplied_digest = Digest(supplied)
    except ValueError as exc:
        raise DomainError(ErrorCode.QUALIFICATION_INVALID, "Ark conformance digest is invalid") from exc
    core = {key: value for key, value in document.items() if key != "result_digest"}
    if digest_of(core) != supplied_digest:
        raise DomainError(ErrorCode.QUALIFICATION_INVALID, "Ark conformance digest does not verify")
    cases = document.get("cases")
    if not isinstance(cases, list) or [item.get("case_id") for item in cases if isinstance(item, dict)] != [
        f"CC-ARK-{number:02d}" for number in range(1, 14)
    ]:
        raise DomainError(ErrorCode.QUALIFICATION_INVALID, "Ark conformance case set is incomplete")
    for item in cases:
        if (
            not isinstance(item, dict)
            or set(item) != {"case_id", "outcome", "evidence_kind", "evidence_digest"}
            or item.get("outcome") not in {"PASS", "FAIL"}
            or not isinstance(item.get("evidence_kind"), str)
        ):
            raise DomainError(ErrorCode.QUALIFICATION_INVALID, "Ark conformance case is invalid")
        try:
            Digest(str(item.get("evidence_digest")))
        except ValueError as exc:
            raise DomainError(
                ErrorCode.QUALIFICATION_INVALID,
                "Ark conformance case evidence digest is invalid",
            ) from exc
    case_pass = all(item["outcome"] == "PASS" for item in cases)
    provider = document.get("provider")
    if (
        not isinstance(provider, dict)
        or set(provider)
        != {
            "provider_type",
            "protocol",
            "endpoint",
            "configuration_fingerprint",
            "secret_reference",
            "credential_configured",
        }
        or provider.get("provider_type") != "VOLCENGINE_ARK"
        or provider.get("protocol") != "OPENAI_COMPATIBLE_CHAT_COMPLETIONS"
        or provider.get("endpoint")
        != DEFAULT_VOLCENGINE_ARK_CHAT_COMPLETIONS_ENDPOINT
        or not isinstance(provider.get("secret_reference"), str)
        or not re.fullmatch(
            r"env:[A-Z_][A-Z0-9_]*",
            str(provider.get("secret_reference")),
        )
        or type(provider.get("credential_configured")) is not bool
    ):
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "Ark conformance Provider evidence is invalid",
        )
    try:
        Digest(str(provider.get("configuration_fingerprint")))
    except ValueError as exc:
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "Ark conformance Provider configuration digest is invalid",
        ) from exc
    execution = document.get("execution")
    if not isinstance(execution, dict) or set(execution) != {
        "request_count",
        "provider_request_ids",
        "request_body_digests",
        "input_tokens",
        "output_tokens",
        "usage_complete",
        "raw_prompt_persisted",
        "raw_response_persisted",
        "transport_session",
    }:
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "Ark conformance execution evidence is invalid",
        )
    try:
        transport_session = verify_ark_transport_session_audit(
            execution.get("transport_session")
        )
    except DomainError as exc:
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "Ark conformance transport session evidence is invalid",
        ) from exc
    request_count = execution.get("request_count")
    provider_request_ids = execution.get("provider_request_ids")
    if (
        type(request_count) is not int
        or request_count < 0
        or not isinstance(provider_request_ids, list)
        or not isinstance(execution.get("request_body_digests"), list)
        or len(execution["request_body_digests"]) != request_count
        or execution.get("raw_prompt_persisted") is not False
        or execution.get("raw_response_persisted") is not False
    ):
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "Ark conformance request evidence is inconsistent",
        )
    try:
        tuple(Digest(str(item)) for item in execution["request_body_digests"])
    except ValueError as exc:
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "Ark conformance request digest is invalid",
        ) from exc
    if document.get("outcome") == "PASS" and (
        request_count != 2
        or provider.get("credential_configured") is not True
        or len(provider_request_ids) != 2
        or any(
            not isinstance(item, str) or not item
            for item in provider_request_ids
        )
        or len(set(provider_request_ids)) != 2
        or execution.get("usage_complete") is not True
        or transport_session["tls_handshake_attempt_count"] != 2
        or transport_session["tls_handshake_success_count"] != 2
        or transport_session["http_dispatch_count"] != 2
        or transport_session["connection_reuse_count"] != 0
        or transport_session["post_dispatch_outcome_unknown_count"] != 0
        or transport_session["credential_resolution_count"] != 2
        or transport_session["credential_resolution_success_count"] != 2
    ):
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "Ark PASS did not prove the one-request-per-TLS policy",
        )
    validity = document.get("validity")
    if not isinstance(validity, dict):
        raise DomainError(ErrorCode.QUALIFICATION_INVALID, "Ark conformance validity is missing")
    if document.get("outcome") == "PASS":
        if not case_pass or document.get("failure") is not None or validity.get("status") != "VALID":
            raise DomainError(ErrorCode.QUALIFICATION_INVALID, "Ark PASS result is internally inconsistent")
    elif case_pass or validity.get("status") != "NOT_ISSUED":
        raise DomainError(ErrorCode.QUALIFICATION_INVALID, "Ark FAIL result is internally inconsistent")
    if require_pass and (
        document.get("outcome") != "PASS"
        or any(not isinstance(item, dict) or item.get("outcome") != "PASS" for item in cases)
    ):
        raise DomainError(ErrorCode.QUALIFICATION_INVALID, "Ark conformance did not pass")


def current_ark_implementation_manifest() -> dict[str, object]:
    package_root = Path(__file__).resolve().parents[1]
    relative_files = (
        "ai_infrastructure/ark_chat_conformance.py",
        "ai_infrastructure/direct_https.py",
        "ai_infrastructure/model_gateway.py",
        "ai_infrastructure/openai_responses_adapter.py",
        "ai_infrastructure/volcengine_ark_chat_adapter.py",
        "interface/provider_cli.py",
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


def _live_request(
    *,
    configuration: VolcengineArkModelConfiguration,
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
    configuration: VolcengineArkModelConfiguration,
    recording: RecordingChatCompletionsTransport,
    responses: tuple[object, ...],
    canaries: tuple[str, str],
    transport_session: Mapping[str, object],
    live_failure: DomainError | None,
) -> list[dict[str, object]]:
    bodies: list[dict[str, object]] = []
    for request in recording.requests:
        try:
            decoded = json.loads(request.body)
        except (UnicodeDecodeError, json.JSONDecodeError):
            decoded = {}
        bodies.append(decoded if isinstance(decoded, dict) else {})

    def case(number: int, passed: bool, evidence: str, payload: object) -> dict[str, object]:
        return {
            "case_id": f"CC-ARK-{number:02d}",
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
        body.get("tools") == []
        and body.get("tool_choice") == "none"
        and body.get("parallel_tool_calls") is False
        for body in bodies
    )
    stateless = two_live and all(
        not ({"conversation", "previous_response_id", "prompt", "context_management", "store"} & set(body))
        and body.get("stream") is True
        and body.get("stream_options") == {"include_usage": True}
        and body.get("n") == 1
        for body in bodies
    )
    strict = two_live and all(
        isinstance(body.get("response_format"), dict)
        and body["response_format"] == {"type": "json_object"}
        and isinstance(body.get("messages"), list)
        and len(body["messages"]) >= 2
        and body["messages"][0].get("role") == "system"
        and "closed JSON Schema" in body["messages"][0].get("content", "")
        and '"additionalProperties":false' in body["messages"][0].get("content", "")
        and "thinking" not in body
        for body in bodies
    )
    separated = two_live and canaries[0].encode() in recording.requests[0].body and canaries[0].encode() not in recording.requests[1].body
    local_denials = _negative_oracles(configuration)
    model_identity = two_live and all(
        getattr(response, "actual_model_fingerprint", None)
        == configuration.actual_model_fingerprint
        for response in responses
    )
    usage = two_live and all(getattr(response, "usage_complete", False) for response in responses)
    request_ids = two_live and len(
        {getattr(response, "provider_request_id", None) for response in responses}
    ) == 2 and all(getattr(response, "provider_request_id", None) for response in responses)
    secret_sentinel = "conformance-secret-sentinel-never-persist"
    serialized_public = canonical_json_bytes(
        configuration.public_status(
            {configuration.api_key_environment_variable: secret_sentinel}
        )
    )
    secret_clean = secret_sentinel.encode() not in serialized_public and all(
        b"Authorization" not in request.body
        and b"Bearer " not in request.body
        and configuration.secret_reference.encode() not in request.body
        for request in recording.requests
    )
    admission_held = adapter_capabilities_offline(configuration) and all(
        local_denials.values()
    )
    transport_policy = (
        two_live
        and transport_session.get("tls_handshake_attempt_count") == 2
        and transport_session.get("tls_handshake_success_count") == 2
        and transport_session.get("pre_dispatch_tls_handshake_failure_count") == 0
        and transport_session.get("http_dispatch_count") == 2
        and transport_session.get("connection_reuse_count") == 0
        and transport_session.get("post_dispatch_outcome_unknown_count") == 0
        and transport_session.get("request_retry_count") == 0
        and transport_session.get("credential_resolution_count") == 2
        and transport_session.get("credential_resolution_success_count") == 2
    )
    return [
        case(1, exact_endpoint, "LIVE_WIRE", {"endpoint": configuration.endpoint, "count": len(recording.requests)}),
        case(2, allowlisted, "LIVE_WIRE", {"body_keys": [sorted(body) for body in bodies]}),
        case(3, no_tools, "LIVE_WIRE", {"tools": [body.get("tools") for body in bodies]}),
        case(4, stateless, "LIVE_WIRE", {"state_fields_absent": stateless}),
        case(5, strict, "LIVE_WIRE_AND_RESPONSE", {"strict": strict, "responses": len(responses)}),
        case(6, separated, "LIVE_TWO_CALL_CANARY", {"first_absent_from_second": separated}),
        case(7, all(local_denials.values()), "OFFLINE_NEGATIVE_ORACLE", local_denials),
        case(8, model_identity, "LIVE_RESPONSE", {"exact_identity": model_identity}),
        case(9, usage, "LIVE_RESPONSE", {"usage_complete": usage}),
        case(10, request_ids, "LIVE_RESPONSE", {"unique_request_ids": bool(request_ids)}),
        case(11, secret_clean, "LIVE_WIRE_AND_LOCAL_RESULT", {"secret_reference_only": secret_clean}),
        case(12, admission_held, "OFFLINE_ADMISSION_ORACLE", {"activation_held": admission_held}),
        case(13, transport_policy, "LIVE_TRANSPORT_SESSION_AUDIT", {"policy_proved": transport_policy}),
    ]


def _negative_oracles(configuration: VolcengineArkModelConfiguration) -> dict[str, bool]:
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
    input_adapter = VolcengineArkChatCompletionsNoToolsAdapter(
        transport=tool_input_transport,
        configuration=configuration,
        output_schemas={"negative@1": schema},
    )
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
        tool_input_denied = exc.code is ErrorCode.PROVIDER_OUTPUT_FORBIDDEN and tool_input_transport.calls == 0

    output_adapter = VolcengineArkChatCompletionsNoToolsAdapter(
        transport=_StaticTransport(
            _fake_response(
                configuration.actual_model_fingerprint,
                '{"status":"ok"}',
                delta_extra={"tool_calls": [{"id": "fixture-tool"}]},
                request_id="fixture-tool-output",
            )
        ),
        configuration=configuration,
        output_schemas={"negative@1": schema},
    )
    try:
        output_adapter.invoke(valid_request)
        tool_output_denied = False
    except DomainError as exc:
        tool_output_denied = exc.code is ErrorCode.PROVIDER_OUTPUT_FORBIDDEN

    schema_adapter = VolcengineArkChatCompletionsNoToolsAdapter(
        transport=_StaticTransport(
            _fake_response(configuration.actual_model_fingerprint, '{"status":"wrong"}')
        ),
        configuration=configuration,
        output_schemas={"negative@1": schema},
    )
    try:
        schema_adapter.invoke(valid_request)
        invalid_schema_denied = False
    except DomainError as exc:
        invalid_schema_denied = exc.code is ErrorCode.STRUCTURED_OUTPUT_INVALID

    fenced_adapter = VolcengineArkChatCompletionsNoToolsAdapter(
        transport=_StaticTransport(
            _fake_response(
                configuration.actual_model_fingerprint,
                '```json\n{"status":"ok"}\n```',
            )
        ),
        configuration=configuration,
        output_schemas={"negative@1": schema},
    )
    try:
        fenced_response = fenced_adapter.invoke(valid_request)
        fenced_json_normalized = (
            fenced_response.output_text == '{"status":"ok"}'
            and fenced_response.output_normalization == "MARKDOWN_JSON_FENCE_V1"
        )
    except DomainError:
        fenced_json_normalized = False

    prefix_adapter = VolcengineArkChatCompletionsNoToolsAdapter(
        transport=_StaticTransport(
            _fake_response(
                configuration.actual_model_fingerprint,
                'Result:\n```json\n{"status":"ok"}\n```',
            )
        ),
        configuration=configuration,
        output_schemas={"negative@1": schema},
    )
    try:
        prefix_response = prefix_adapter.invoke(valid_request)
        leading_text_fenced_json_normalized = (
            prefix_response.output_text == '{"status":"ok"}'
            and prefix_response.output_normalization
            == "MARKDOWN_JSON_FENCE_WITH_PREFIX_V1"
        )
    except DomainError:
        leading_text_fenced_json_normalized = False

    trailing_adapter = VolcengineArkChatCompletionsNoToolsAdapter(
        transport=_StaticTransport(
            _fake_response(
                configuration.model_ref,
                '```json\n{"status":"ok"}\n```\nResult.',
            )
        ),
        configuration=configuration,
        output_schemas={"negative@1": schema},
    )
    try:
        trailing_adapter.invoke(valid_request)
        trailing_text_denied = False
    except DomainError as exc:
        trailing_text_denied = exc.code is ErrorCode.STRUCTURED_OUTPUT_INVALID

    safe_http_error_adapter = VolcengineArkChatCompletionsNoToolsAdapter(
        transport=_StaticTransport(
            ProviderHTTPResponse(
                400,
                {"x-request-id": "fixture-http-error"},
                json.dumps(
                    {
                        "error": {
                            "code": "InvalidParameter",
                            "type": "BadRequest",
                            "param": "response_format",
                            "message": "sensitive diagnostic must not cross",
                        }
                    }
                ).encode(),
            )
        ),
        configuration=configuration,
        output_schemas={"negative@1": schema},
    )
    try:
        safe_http_error_adapter.invoke(valid_request)
        safe_http_error_parameter_projected = False
    except DomainError as exc:
        safe_http_error_parameter_projected = (
            exc.code is ErrorCode.PROVIDER_HTTP_ERROR
            and exc.details
            == {
                "provider_request_id": "fixture-http-error",
                "provider_error_code": "InvalidParameter",
                "provider_error_type": "BadRequest",
                "provider_error_parameter": "response_format",
                "http_status": 400,
            }
        )

    unsafe_http_error_adapter = VolcengineArkChatCompletionsNoToolsAdapter(
        transport=_StaticTransport(
            ProviderHTTPResponse(
                400,
                {},
                json.dumps(
                    {
                        "error": {
                            "code": "InvalidParameter",
                            "type": "BadRequest",
                            "param": "response format\nunsafe",
                        }
                    }
                ).encode(),
            )
        ),
        configuration=configuration,
        output_schemas={"negative@1": schema},
    )
    try:
        unsafe_http_error_adapter.invoke(valid_request)
        unsafe_http_error_parameter_rejected = False
    except DomainError as exc:
        unsafe_http_error_parameter_rejected = (
            exc.code is ErrorCode.PROVIDER_HTTP_ERROR
            and "provider_error_parameter" not in exc.details
        )
    return {
        "tool_input_denied": tool_input_denied,
        "tool_output_denied": tool_output_denied,
        "invalid_schema_denied": invalid_schema_denied,
        "fenced_json_normalized": fenced_json_normalized,
        "leading_text_fenced_json_normalized": leading_text_fenced_json_normalized,
        "trailing_text_denied": trailing_text_denied,
        "safe_http_error_parameter_projected": (
            safe_http_error_parameter_projected
        ),
        "unsafe_http_error_parameter_rejected": (
            unsafe_http_error_parameter_rejected
        ),
    }


def adapter_capabilities_offline(configuration: VolcengineArkModelConfiguration) -> bool:
    adapter = VolcengineArkChatCompletionsNoToolsAdapter(
        transport=_StaticTransport(_fake_response(configuration.model_ref, '{"status":"ok"}')),
        configuration=configuration,
        output_schemas={
            "negative@1": OutputSchemaDefinition(
                "negative_oracle",
                {
                    "type": "object",
                    "properties": {"status": {"type": "string", "enum": ["ok"]}},
                    "required": ["status"],
                    "additionalProperties": False,
                },
            )
        },
    )
    return adapter.capabilities.conformance_level.value == "OFFLINE_FIXTURE"


def _fake_response(
    model: str,
    content: str,
    *,
    delta_extra: Mapping[str, object] | None = None,
    request_id: str = "fixture-request",
) -> ProviderHTTPResponse:
    content_delta: dict[str, object] = {"content": content}
    content_delta.update(delta_extra or {})
    chunks = (
        {
            "id": "chatcmpl_fixture",
            "object": "chat.completion.chunk",
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "delta": {"role": "assistant", "content": ""},
                    "finish_reason": None,
                }
            ],
            "usage": None,
        },
        {
            "id": "chatcmpl_fixture",
            "object": "chat.completion.chunk",
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "delta": content_delta,
                    "finish_reason": None,
                }
            ],
            "usage": None,
        },
        {
            "id": "chatcmpl_fixture",
            "object": "chat.completion.chunk",
            "model": model,
            "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
            "usage": None,
        },
        {
            "id": "chatcmpl_fixture",
            "object": "chat.completion.chunk",
            "model": model,
            "choices": [],
            "usage": {
                "prompt_tokens": 1,
                "completion_tokens": 1,
                "total_tokens": 2,
            },
        },
    )
    body = b"".join(
        b"data: "
        + json.dumps(chunk, ensure_ascii=False, separators=(",", ":")).encode(
            "utf-8"
        )
        + b"\n\n"
        for chunk in chunks
    ) + b"data: [DONE]\n\n"
    return ProviderHTTPResponse(
        200,
        {
            "x-request-id": request_id,
            "content-type": "text/event-stream; charset=utf-8",
        },
        body,
    )


def _fixture_manifest() -> Digest:
    return digest_of(
        {
            "fixture_id": ARK_CHAT_CONFORMANCE_FIXTURE_ID,
            "fixture_version": ARK_CHAT_CONFORMANCE_FIXTURE_VERSION,
            "case_ids": [f"CC-ARK-{number:02d}" for number in range(1, 14)],
            "live_call_count": 2,
            "wire_allowlist": sorted(_WIRE_ALLOWLIST),
            "connection_policy": DEFAULT_VOLCENGINE_ARK_CONNECTION_POLICY,
            "maximum_pre_dispatch_tls_handshakes_per_request": (
                DEFAULT_VOLCENGINE_ARK_MAXIMUM_PRE_DISPATCH_TLS_HANDSHAKES_PER_REQUEST
            ),
            "maximum_http_dispatches_per_tls_session": (
                DEFAULT_VOLCENGINE_ARK_MAXIMUM_HTTP_DISPATCHES_PER_TLS_SESSION
            ),
            "credential_resolution_policy": (
                DEFAULT_VOLCENGINE_ARK_CREDENTIAL_RESOLUTION_POLICY
            ),
            "request_retry_allowed": False,
            "transport_session_audit_schema": (
                "SWM-VOLCENGINE-ARK-TRANSPORT-SESSION-AUDIT@1"
            ),
            "result_schema": ARK_CHAT_CONFORMANCE_RESULT_SCHEMA,
        }
    )


def _safe_failure(failure: DomainError | None) -> dict[str, object] | None:
    if failure is None:
        return None
    details = {
        key: value
        for key, value in failure.details.items()
        if key
        in {
            "http_status",
            "provider_error_code",
            "provider_error_type",
            "provider_error_parameter",
            "provider_request_id",
        }
    }
    if failure.code is ErrorCode.STRUCTURED_OUTPUT_INVALID:
        details["structured_output_failure_class"] = (
            _structured_output_failure_class(failure)
        )
    return {"code": failure.code.value, "details": details}


def _structured_output_failure_class(failure: DomainError) -> str:
    if "finish_reason" in failure.details:
        return "INCOMPLETE_TERMINATION"
    if failure.message == "output text is not JSON":
        return "JSON_SYNTAX_ERROR"
    if failure.message == "structured output root is not an object":
        return "NON_OBJECT_ROOT"
    return "CLOSED_SCHEMA_MISMATCH"


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
