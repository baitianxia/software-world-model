"""Bounded validation-only Direct Agent for the frozen JWT comparison task."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
from typing import Mapping
import uuid

from software_world_model.ai_infrastructure import (
    ArkChatConformanceQualification,
    ChatCompletionsTransport,
    OutputSchemaDefinition,
    ProviderHTTPResponse,
    VolcengineArkChatCompletionsNoToolsAdapter,
    VolcengineArkModelConfiguration,
)
from software_world_model.ai_infrastructure.model_gateway import ProviderRequest, RenderedMessage
from software_world_model.cross_cutting import Digest, DomainError, ErrorCode, digest_of

from .manifest import (
    DIRECT_AGENT_PROMPT,
    DIRECT_AGENT_PROMPT_REF,
    DIRECT_AGENT_TOOL_POLICY_REF,
    DIRECT_ORACLE_DRAFT_SCHEMA,
    PARENT_COMMIT,
    QUESTION,
    REPOSITORY_IDENTITY,
    TARGET_COMMIT,
    _NEEDS,
    _direct_requirement_view,
    _raw_digest,
    _time,
    _utc,
    _validate_oracle_draft,
    _verify_qualification,
    _verify_repository,
)


DIRECT_AGENT_OUTPUT_SCHEMA_REF = "jwt-direct-agent-step@1"


_STEP_SCHEMA = OutputSchemaDefinition(
    "jwt_direct_agent_step",
    {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["RESOLVE", "COMPARE", "READ", "SEARCH", "FINISH"],
            },
            "revision_role": {"type": "string", "enum": ["PARENT", "TARGET", "NONE"]},
            "path": {"type": "string"},
            "query": {"type": "string"},
            "start_line": {"type": "integer", "minimum": 0},
            "end_line": {"type": "integer", "minimum": 0},
            "rationale": {"type": "string"},
            "answer": {"type": "string"},
            "claims": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "semantic_key": {"type": "string"},
                        "claim": {"type": "string"},
                        "target": {"type": "string"},
                        "context": {"type": "string"},
                        "modality": {"type": "string"},
                        "condition": {"type": ["string", "null"]},
                        "limitation": {"type": ["string", "null"]},
                        "coverage": {"type": "string"},
                        "source_observation_refs": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "need_ids": {"type": "array", "items": {"type": "string"}},
                        "obligation_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "material": {"type": "boolean"},
                    },
                    "required": [
                        "semantic_key",
                        "claim",
                        "target",
                        "context",
                        "modality",
                        "condition",
                        "limitation",
                        "coverage",
                        "source_observation_refs",
                        "need_ids",
                        "obligation_ids",
                        "material",
                    ],
                    "additionalProperties": False,
                },
            },
        },
        "required": [
            "action",
            "revision_role",
            "path",
            "query",
            "start_line",
            "end_line",
            "rationale",
            "answer",
            "claims",
        ],
        "additionalProperties": False,
    },
)


class _StructuredOutputDiagnosticTransport:
    """Capture only a sanitized response-shape diagnostic, never response text."""

    def __init__(self, delegate: ChatCompletionsTransport) -> None:
        self._delegate = delegate
        self.last_diagnostic: dict[str, str | int] = {}

    def post_json(
        self,
        *,
        endpoint: str,
        body: bytes,
        client_request_id: str,
        timeout_milliseconds: int,
    ) -> ProviderHTTPResponse:
        response = self._delegate.post_json(
            endpoint=endpoint,
            body=body,
            client_request_id=client_request_id,
            timeout_milliseconds=timeout_milliseconds,
        )
        self.last_diagnostic = _diagnose_structured_output_response(response)
        return response


def run_direct_agent(
    *,
    repository_path: str | Path,
    result_directory: str | Path,
    qualification: ArkChatConformanceQualification,
    configuration: VolcengineArkModelConfiguration,
    transport: ChatCompletionsTransport,
    max_tool_steps: int = 40,
    max_files_read: int = 16,
    max_source_bytes: int = 1_000_000,
    max_model_calls: int = 40,
    timeout_milliseconds: int = 60_000,
    max_output_tokens: int = 4096,
    now: datetime | None = None,
) -> Path:
    """Run the external Direct Agent and create an unreviewed oracle draft."""

    for value, label in (
        (max_tool_steps, "tool step budget"),
        (max_files_read, "file budget"),
        (max_source_bytes, "source byte budget"),
        (max_model_calls, "model call budget"),
        (timeout_milliseconds, "timeout"),
        (max_output_tokens, "output token budget"),
    ):
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} must be positive")
    started_at = _utc(now or datetime.now(timezone.utc))
    _verify_qualification(qualification, configuration, at=started_at)
    source_boundary = _verify_repository(repository_path)
    repository = Path(repository_path).resolve()
    changed_files = _changed_files(repository)
    diagnostic_transport = _StructuredOutputDiagnosticTransport(transport)
    adapter = VolcengineArkChatCompletionsNoToolsAdapter(
        transport=diagnostic_transport,
        configuration=configuration,
        output_schemas={DIRECT_AGENT_OUTPUT_SCHEMA_REF: _STEP_SCHEMA},
        live_qualification=qualification,
        enforce_output_schema=False,
    )
    observations: list[dict[str, object]] = []
    trace: list[dict[str, object]] = []
    request_ids: list[str] = []
    output_normalizations: list[str] = []
    seen_actions: set[Digest] = set()
    files_read: set[tuple[str, str]] = set()
    source_bytes = 0
    input_tokens = 0
    output_tokens = 0
    final: Mapping[str, object] | None = None
    requirement = _direct_requirement_view()

    for model_ordinal in range(max_model_calls):
        if model_ordinal > max_tool_steps:
            break
        if datetime.now(timezone.utc) >= qualification.valid_until:
            raise DomainError(ErrorCode.QUALIFICATION_INVALID, "adapter conformance expired during Direct run")
        state = {
            "question": QUESTION,
            "source_boundary": source_boundary,
            "changed_files": changed_files,
            "requirements": requirement,
            "budgets": {
                "remaining_tool_steps": max_tool_steps - len(trace),
                "remaining_files": max_files_read - len(files_read),
                "remaining_source_bytes": max_source_bytes - source_bytes,
                "remaining_model_calls": max_model_calls - model_ordinal,
            },
            "observations": observations,
        }
        user = json.dumps(state, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        request = _request(
            configuration,
            user,
            ordinal=model_ordinal,
            timeout_milliseconds=timeout_milliseconds,
            max_output_tokens=max_output_tokens,
        )
        try:
            response = adapter.invoke(request)
        except DomainError as exc:
            if exc.code is ErrorCode.STRUCTURED_OUTPUT_INVALID:
                raise DomainError(
                    ErrorCode.STRUCTURED_OUTPUT_INVALID,
                    f"Direct Agent model call {model_ordinal + 1} did not return one JSON object "
                    "matching the step schema; no draft was created",
                    diagnostic_transport.last_diagnostic,
                ) from exc
            raise
        if (
            response.actual_model_fingerprint
            != configuration.actual_model_fingerprint
            or not response.usage_complete
            or response.provider_request_id is None
        ):
            raise DomainError(
                ErrorCode.QUALIFICATION_INVALID,
                "Direct Agent model identity, request ID, or usage is incomplete",
            )
        request_ids.append(response.provider_request_id)
        output_normalizations.append(response.output_normalization)
        input_tokens += response.input_tokens or 0
        output_tokens += response.output_tokens or 0
        try:
            step = _STEP_SCHEMA.validate_output_text(response.output_text)
        except DomainError as exc:
            if exc.code is not ErrorCode.STRUCTURED_OUTPUT_INVALID:
                raise
            if len(trace) >= max_tool_steps:
                raise DomainError(
                    ErrorCode.BUDGET_EXHAUSTED,
                    "Direct Agent tool-step budget exhausted",
                ) from exc
            action_core = {
                "action": "INVALID_OUTPUT",
                "revision_role": "NONE",
                "path": "",
                "query": "",
                "start_line": 0,
                "end_line": 0,
            }
            action_digest = digest_of(action_core)
            content = json.dumps(
                {
                    "outcome": "DENIED",
                    "error": exc.code.value,
                    "message": exc.message,
                    "output_digest": response.output_digest.value,
                },
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            content_bytes = content.encode("utf-8")
            source_bytes += len(content_bytes)
            if source_bytes > max_source_bytes:
                raise DomainError(
                    ErrorCode.BUDGET_EXHAUSTED,
                    "Direct Agent source-byte budget exhausted",
                ) from exc
            result_digest = _raw_digest(content_bytes)
            observation_ref = (
                f"direct-observation:{len(observations):03d}:{result_digest.value}"
            )
            observations.append(
                {
                    "observation_ref": observation_ref,
                    "tool": "DENIED",
                    "locator": f"direct-tool-denial:{action_digest.value}",
                    "content": content,
                    "content_digest": result_digest.value,
                }
            )
            trace.append(
                {
                    "ordinal": len(trace),
                    "tool": "DENIED",
                    "request": action_core,
                    "request_digest": action_digest.value,
                    "observation_ref": observation_ref,
                    "result_digest": result_digest.value,
                }
            )
            continue
        action = str(step["action"])
        action_core = {
            "action": action,
            "revision_role": step["revision_role"],
            "path": step["path"],
            "query": step["query"],
            "start_line": step["start_line"],
            "end_line": step["end_line"],
        }
        try:
            _validate_step_shape(step, action)
        except DomainError as exc:
            if exc.code is not ErrorCode.STRUCTURED_OUTPUT_INVALID:
                raise
            if len(trace) >= max_tool_steps:
                raise DomainError(
                    ErrorCode.BUDGET_EXHAUSTED,
                    "Direct Agent tool-step budget exhausted",
                ) from exc
            action_digest = digest_of(action_core)
            seen_actions.add(action_digest)
            content = json.dumps(
                {
                    "outcome": "DENIED",
                    "error": exc.code.value,
                    "message": exc.message,
                },
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            content_bytes = content.encode("utf-8")
            source_bytes += len(content_bytes)
            if source_bytes > max_source_bytes:
                raise DomainError(
                    ErrorCode.BUDGET_EXHAUSTED,
                    "Direct Agent source-byte budget exhausted",
                ) from exc
            result_digest = _raw_digest(content_bytes)
            observation_ref = (
                f"direct-observation:{len(observations):03d}:{result_digest.value}"
            )
            locator = f"direct-tool-denial:{action_digest.value}"
            observations.append(
                {
                    "observation_ref": observation_ref,
                    "tool": "DENIED",
                    "locator": locator,
                    "content": content,
                    "content_digest": result_digest.value,
                }
            )
            trace.append(
                {
                    "ordinal": len(trace),
                    "tool": "DENIED",
                    "request": action_core,
                    "request_digest": action_digest.value,
                    "observation_ref": observation_ref,
                    "result_digest": result_digest.value,
                }
            )
            continue
        if action == "FINISH":
            final = step
            break
        if len(trace) >= max_tool_steps:
            raise DomainError(ErrorCode.BUDGET_EXHAUSTED, "Direct Agent tool-step budget exhausted")
        action_digest = digest_of(action_core)
        trace_tool = action
        if action_digest in seen_actions:
            trace_tool = "DENIED"
            content = json.dumps(
                {
                    "outcome": "DENIED",
                    "error": ErrorCode.EVALUATION_RUN_CONFLICT.value,
                    "message": "identical source action already has an observation",
                },
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            locator = f"direct-tool-denial:{action_digest.value}"
        else:
            seen_actions.add(action_digest)
            try:
                content, locator = _execute_action(
                    repository,
                    changed_files,
                    action_core,
                    max_source_bytes=max_source_bytes - source_bytes,
                )
            except DomainError as exc:
                if exc.code is not ErrorCode.INVALID_ARGUMENT:
                    raise
                trace_tool = "DENIED"
                content = json.dumps(
                    {
                        "outcome": "DENIED",
                        "error": exc.code.value,
                        "message": exc.message,
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
                locator = f"direct-tool-denial:{action_digest.value}"
        content_bytes = content.encode("utf-8")
        if trace_tool == "READ":
            files_read.add((str(step["revision_role"]), str(step["path"])))
            if len(files_read) > max_files_read:
                raise DomainError(ErrorCode.BUDGET_EXHAUSTED, "Direct Agent file budget exhausted")
        source_bytes += len(content_bytes)
        if source_bytes > max_source_bytes:
            raise DomainError(ErrorCode.BUDGET_EXHAUSTED, "Direct Agent source-byte budget exhausted")
        result_digest = _raw_digest(content_bytes)
        observation_ref = f"direct-observation:{len(observations):03d}:{result_digest.value}"
        observations.append(
            {
                "observation_ref": observation_ref,
                "tool": trace_tool,
                "locator": locator,
                "content": content,
                "content_digest": result_digest.value,
            }
        )
        trace.append(
            {
                "ordinal": len(trace),
                "tool": trace_tool,
                "request": action_core,
                "request_digest": action_digest.value,
                "observation_ref": observation_ref,
                "result_digest": result_digest.value,
            }
        )
    if final is None:
        raise DomainError(ErrorCode.BUDGET_EXHAUSTED, "Direct Agent did not finish within budget")
    claims = _project_claims(final["claims"], observations)
    if not claims:
        raise DomainError(ErrorCode.ORACLE_UNAVAILABLE, "Direct Agent returned no material claims")
    draft = {
        "schema": DIRECT_ORACLE_DRAFT_SCHEMA,
        "question": QUESTION,
        "repository_identity": REPOSITORY_IDENTITY,
        "target_commit": TARGET_COMMIT,
        "parent_commit": PARENT_COMMIT,
        "model_ref": configuration.model_ref,
        "adapter_version": configuration.adapter_version,
        "conformance_result_ref": qualification.result_ref,
        "prompt_ref": DIRECT_AGENT_PROMPT_REF,
        "prompt": DIRECT_AGENT_PROMPT,
        "prompt_digest": digest_of(DIRECT_AGENT_PROMPT).value,
        "tool_policy_ref": DIRECT_AGENT_TOOL_POLICY_REF,
        "requirement": requirement,
        "requirement_digest": digest_of(requirement).value,
        "budget": {
            "max_tool_steps": max_tool_steps,
            "max_files_read": max_files_read,
            "max_source_bytes": max_source_bytes,
            "max_model_calls": max_model_calls,
            "timeout_milliseconds": timeout_milliseconds,
            "max_output_tokens": max_output_tokens,
        },
        "started_at": _time(started_at),
        "completed_at": _time(_utc(now or datetime.now(timezone.utc))),
        "actual_model_fingerprints": [configuration.actual_model_fingerprint],
        "provider_request_ids": request_ids,
        "output_normalizations": output_normalizations,
        "usage": {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "complete": True,
        },
        "trace": trace,
        "observations": observations,
        "direct_answer": final["answer"],
        "claims": claims,
    }
    _validate_oracle_draft(draft, qualification, configuration)
    path = Path(result_directory)
    path.mkdir(parents=True, exist_ok=True)
    target = path / f"JWT-DIRECT-ORACLE-DRAFT-{uuid.uuid4().hex}.json"
    payload = json.dumps(draft, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8") + b"\n"
    try:
        descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "Direct Agent draft already exists and cannot be overwritten",
        ) from exc
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    return target


def _diagnose_structured_output_response(
    response: ProviderHTTPResponse,
) -> dict[str, str | int]:
    """Classify response shape without retaining or revealing assistant content."""

    diagnostic: dict[str, str | int] = {"provider_http_status": response.status_code}
    headers = {key.lower(): value for key, value in response.headers.items()}
    request_id = headers.get("x-request-id") or headers.get("x-tt-logid")
    if isinstance(request_id, str) and 0 < len(request_id) <= 256:
        diagnostic["provider_request_id"] = request_id
    try:
        envelope = json.loads(response.body)
    except (UnicodeDecodeError, json.JSONDecodeError):
        diagnostic["provider_envelope_class"] = "NON_JSON"
        return diagnostic
    if not isinstance(envelope, dict):
        diagnostic["provider_envelope_class"] = "NON_OBJECT"
        return diagnostic
    diagnostic["provider_envelope_class"] = "OBJECT"
    actual_model = envelope.get("model")
    if isinstance(actual_model, str) and actual_model:
        diagnostic["actual_model_fingerprint"] = actual_model
    usage = envelope.get("usage")
    if isinstance(usage, dict):
        prompt_tokens = usage.get("prompt_tokens")
        completion_tokens = usage.get("completion_tokens")
        total_tokens = usage.get("total_tokens")
        if (
            isinstance(prompt_tokens, int)
            and not isinstance(prompt_tokens, bool)
            and prompt_tokens >= 0
            and isinstance(completion_tokens, int)
            and not isinstance(completion_tokens, bool)
            and completion_tokens >= 0
            and isinstance(total_tokens, int)
            and not isinstance(total_tokens, bool)
            and total_tokens == prompt_tokens + completion_tokens
        ):
            diagnostic["input_tokens"] = prompt_tokens
            diagnostic["output_tokens"] = completion_tokens
            diagnostic["usage_complete"] = "YES"
    choices = envelope.get("choices")
    if not isinstance(choices, list) or len(choices) != 1 or not isinstance(choices[0], dict):
        diagnostic["provider_choice_class"] = "INVALID"
        return diagnostic
    choice = choices[0]
    finish_reason = choice.get("finish_reason")
    if finish_reason in {"stop", "length", "content_filter", "tool_calls"}:
        diagnostic["provider_finish_reason"] = str(finish_reason)
    message = choice.get("message")
    if not isinstance(message, dict):
        diagnostic["assistant_message_class"] = "INVALID"
        return diagnostic
    diagnostic["assistant_message_class"] = "OBJECT"
    reasoning = message.get("reasoning_content")
    if isinstance(reasoning, str) and reasoning:
        reasoning_bytes = reasoning.encode("utf-8")
        diagnostic["reasoning_content_present"] = "YES"
        diagnostic["reasoning_content_bytes"] = len(reasoning_bytes)
        diagnostic["reasoning_content_digest"] = _raw_digest(reasoning_bytes).value
    else:
        diagnostic["reasoning_content_present"] = "NO"
    content = message.get("content")
    if not isinstance(content, str):
        diagnostic["assistant_content_class"] = type(content).__name__.upper()
        return diagnostic
    content_bytes = content.encode("utf-8")
    diagnostic["assistant_content_class"] = "STRING"
    diagnostic["assistant_content_bytes"] = len(content_bytes)
    diagnostic["assistant_content_digest"] = _raw_digest(content_bytes).value
    stripped = content.strip()
    if not stripped:
        prefix_class = "EMPTY"
        suffix_class = "EMPTY"
    else:
        prefix_class = (
            "MARKDOWN_FENCE"
            if stripped.startswith("```")
            else "REASONING_TAG"
            if stripped.startswith(("<think", "<analysis"))
            else "OBJECT_LIKE"
            if stripped.startswith("{")
            else "ARRAY_LIKE"
            if stripped.startswith("[")
            else "OTHER"
        )
        suffix_class = (
            "MARKDOWN_FENCE"
            if stripped.endswith("```")
            else "OBJECT_LIKE"
            if stripped.endswith("}")
            else "ARRAY_LIKE"
            if stripped.endswith("]")
            else "OTHER"
        )
    diagnostic["assistant_content_prefix_class"] = prefix_class
    diagnostic["assistant_content_suffix_class"] = suffix_class
    try:
        decoded = json.loads(content)
    except json.JSONDecodeError as exc:
        diagnostic["content_json_parse"] = "INVALID"
        diagnostic["content_json_error_position"] = exc.pos
    else:
        diagnostic["content_json_parse"] = (
            "OBJECT" if isinstance(decoded, dict) else "NON_OBJECT"
        )
    return diagnostic


def _request(
    configuration: VolcengineArkModelConfiguration,
    user: str,
    *,
    ordinal: int,
    timeout_milliseconds: int,
    max_output_tokens: int,
) -> ProviderRequest:
    core = {
        "model_ref": configuration.model_ref,
        "prompt_ref": DIRECT_AGENT_PROMPT_REF,
        "prompt_digest": digest_of(DIRECT_AGENT_PROMPT).value,
        "user_digest": digest_of(user).value,
        "ordinal": ordinal,
        "output_schema_ref": DIRECT_AGENT_OUTPUT_SCHEMA_REF,
        "max_output_tokens": max_output_tokens,
        "timeout_milliseconds": timeout_milliseconds,
    }
    return ProviderRequest(
        model_ref=configuration.model_ref,
        messages=(
            RenderedMessage(
                "system", DIRECT_AGENT_PROMPT, "direct-agent-prompt", digest_of(DIRECT_AGENT_PROMPT)
            ),
            RenderedMessage("user", user, f"direct-agent-state-{ordinal}", digest_of(user)),
        ),
        output_schema_ref=DIRECT_AGENT_OUTPUT_SCHEMA_REF,
        tools=(),
        store=False,
        stream=False,
        max_output_tokens=max_output_tokens,
        timeout_milliseconds=timeout_milliseconds,
        metadata=(("purpose", "jwt-direct-agent-oracle"),),
        digest=digest_of(core),
    )


def _validate_step_shape(step: Mapping[str, object], action: str) -> None:
    if not isinstance(step.get("rationale"), str) or not str(step["rationale"]).strip():
        raise DomainError(ErrorCode.STRUCTURED_OUTPUT_INVALID, "Direct Agent rationale is empty")
    if action == "FINISH":
        if (
            step.get("revision_role") != "NONE"
            or step.get("path") != ""
            or step.get("query") != ""
            or step.get("start_line") != 0
            or step.get("end_line") != 0
            or not isinstance(step.get("answer"), str)
            or not str(step["answer"]).strip()
            or not isinstance(step.get("claims"), list)
            or not step["claims"]
        ):
            raise DomainError(ErrorCode.STRUCTURED_OUTPUT_INVALID, "Direct Agent FINISH payload is invalid")
    elif step.get("answer") != "" or step.get("claims") != []:
        raise DomainError(
            ErrorCode.STRUCTURED_OUTPUT_INVALID,
            "non-FINISH Direct Agent step cannot carry an answer or claims",
        )


def _execute_action(
    repository: Path,
    changed_files: tuple[str, ...],
    action: Mapping[str, object],
    *,
    max_source_bytes: int,
) -> tuple[str, str]:
    kind = action["action"]
    if kind == "RESOLVE":
        _empty_parameters(action)
        content = json.dumps(
            {"target_commit": TARGET_COMMIT, "parent_commit": PARENT_COMMIT},
            sort_keys=True,
        )
        return _bounded(content, max_source_bytes), f"git:{TARGET_COMMIT}:parents"
    if kind == "COMPARE":
        _empty_parameters(action)
        content = _git(
            repository,
            "diff",
            "--no-ext-diff",
            "--unified=3",
            PARENT_COMMIT,
            TARGET_COMMIT,
            "--",
            *changed_files,
        )
        return _bounded(content, max_source_bytes), f"git:compare:{PARENT_COMMIT}..{TARGET_COMMIT}"
    role = str(action["revision_role"])
    if role not in {"PARENT", "TARGET"}:
        raise DomainError(ErrorCode.INVALID_ARGUMENT, "source action requires a revision role")
    revision = PARENT_COMMIT if role == "PARENT" else TARGET_COMMIT
    path = _safe_changed_path(str(action["path"]), changed_files)
    if kind == "READ":
        if action["query"] != "":
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "READ cannot carry a search query")
        start = int(action["start_line"])
        end = int(action["end_line"])
        if start < 1 or end < start or end - start + 1 > 300:
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "READ line range is invalid or too large")
        blob = _git(repository, "show", f"{revision}:{path}")
        lines = blob.splitlines()
        selected = lines[start - 1 : min(end, len(lines))]
        numbered = "\n".join(f"{line_number}:{line}" for line_number, line in enumerate(selected, start=start))
        return _bounded(numbered, max_source_bytes), f"git:{revision}:{path}:L{start}-L{min(end, len(lines))}"
    if kind == "SEARCH":
        if action["start_line"] != 0 or action["end_line"] != 0:
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "SEARCH cannot carry a line range")
        query = str(action["query"])
        if not query or len(query) > 128 or "\x00" in query or "\n" in query:
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "SEARCH query is invalid")
        content = _git_grep(repository, revision, query, path)
        return _bounded(content, max_source_bytes), f"git:grep:{revision}:{path}:{digest_of(query).value}"
    raise DomainError(ErrorCode.INVALID_ARGUMENT, "Direct Agent proposed an unsupported action")


def _empty_parameters(action: Mapping[str, object]) -> None:
    if (
        action["revision_role"] != "NONE"
        or action["path"] != ""
        or action["query"] != ""
        or action["start_line"] != 0
        or action["end_line"] != 0
    ):
        raise DomainError(ErrorCode.INVALID_ARGUMENT, "source action carries forbidden parameters")


def _project_claims(
    raw_claims: object, observations: list[dict[str, object]]
) -> list[dict[str, object]]:
    if not isinstance(raw_claims, list):
        raise DomainError(ErrorCode.STRUCTURED_OUTPUT_INVALID, "Direct Agent claims are not an array")
    observation_by_ref = {item["observation_ref"]: item for item in observations}
    known_needs = {item[0] for item in _NEEDS}
    known_obligations = {
        f"{need_id}-O{ordinal:02d}"
        for need_id, _, dimensions in _NEEDS
        for ordinal in range(1, len(dimensions) + 1)
    }
    semantic_keys: set[str] = set()
    projected = []
    for item in raw_claims:
        if not isinstance(item, dict):
            raise DomainError(ErrorCode.STRUCTURED_OUTPUT_INVALID, "Direct Agent claim is not an object")
        key = item["semantic_key"]
        references = item["source_observation_refs"]
        needs = item["need_ids"]
        obligations = item["obligation_ids"]
        if (
            not isinstance(key, str)
            or not key
            or key in semantic_keys
            or item["material"] is not True
            or not isinstance(references, list)
            or not references
            or any(reference not in observation_by_ref for reference in references)
            or not isinstance(needs, list)
            or not needs
            or not set(needs).issubset(known_needs)
            or not isinstance(obligations, list)
            or not obligations
            or not set(obligations).issubset(known_obligations)
            or any(
                not isinstance(item.get(field), str) or not str(item[field]).strip()
                for field in ("claim", "target", "context", "modality", "coverage")
            )
        ):
            raise DomainError(ErrorCode.STRUCTURED_OUTPUT_INVALID, "Direct Agent claim binding is invalid")
        semantic_keys.add(key)
        supports = [observation_by_ref[reference] for reference in references]
        if any(support.get("tool") == "DENIED" for support in supports):
            raise DomainError(
                ErrorCode.STRUCTURED_OUTPUT_INVALID,
                "Direct Agent claim cannot cite a denied tool proposal",
            )
        projected.append(
            {
                "semantic_key": key,
                "claim": item["claim"],
                "target": item["target"],
                "context": item["context"],
                "modality": item["modality"],
                "condition": item["condition"],
                "limitation": item["limitation"],
                "coverage": item["coverage"],
                "source_locators": [support["locator"] for support in supports],
                "source_digests": [support["content_digest"] for support in supports],
                "need_ids": needs,
                "obligation_ids": obligations,
                "material": True,
            }
        )
    return projected


def _changed_files(repository: Path) -> tuple[str, ...]:
    output = _git(
        repository,
        "diff",
        "--no-ext-diff",
        "--name-only",
        PARENT_COMMIT,
        TARGET_COMMIT,
    )
    files = tuple(line for line in output.splitlines() if line)
    if not files or len(set(files)) != len(files):
        raise DomainError(ErrorCode.SOURCE_REVISION_INCONSISTENT, "frozen change set is invalid")
    return files


def _safe_changed_path(value: str, changed_files: tuple[str, ...]) -> str:
    path = PurePosixPath(value)
    if (
        not value
        or path.is_absolute()
        or ".." in path.parts
        or "\x00" in value
        or "\n" in value
        or value not in changed_files
    ):
        raise DomainError(ErrorCode.SOURCE_TARGET_OUT_OF_SCOPE, "path is outside the frozen change set")
    return value


def _bounded(content: str, remaining_bytes: int) -> str:
    payload = content.encode("utf-8")
    if remaining_bytes < 1 or len(payload) > remaining_bytes:
        raise DomainError(ErrorCode.BUDGET_EXHAUSTED, "source result exceeds remaining byte budget")
    return content


def _git(repository: Path, *arguments: str) -> str:
    try:
        result = subprocess.run(
            ("git", "-C", str(repository), *arguments),
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise DomainError(ErrorCode.SOURCE_OPERATION_FAILED, "Direct Agent Git action failed") from exc
    return result.stdout


def _git_grep(repository: Path, revision: str, query: str, path: str) -> str:
    try:
        result = subprocess.run(
            ("git", "-C", str(repository), "grep", "-n", "-F", "-e", query, revision, "--", path),
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise DomainError(ErrorCode.SOURCE_OPERATION_FAILED, "Direct Agent Git search failed") from exc
    if result.returncode not in {0, 1}:
        raise DomainError(ErrorCode.SOURCE_OPERATION_FAILED, "Direct Agent Git search failed")
    return result.stdout
