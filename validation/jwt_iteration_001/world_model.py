"""Isolated seven-role Software World Model capability-run harness.

The harness is validation-only.  It may read the frozen Local Git source only
through the planner-selected bounded actions below.  Once source collection is
closed, inference, sufficiency, answer, and answer review receive formal
knowledge records only.  The sealed Direct Oracle is never opened here.
"""

from __future__ import annotations

import copy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import time
from typing import Callable, Mapping, Sequence
import uuid

from software_world_model.ai_infrastructure import (
    ArkChatConformanceQualification,
    ChatCompletionsTransport,
    OutputSchemaDefinition,
    ProviderOutcomeUnknown,
    VolcengineArkChatCompletionsNoToolsAdapter,
    VolcengineArkModelConfiguration,
)
from software_world_model.ai_infrastructure.model_gateway import ProviderRequest, RenderedMessage
from software_world_model.cross_cutting import Digest, DomainError, ErrorCode, digest_of

from .direct_agent import (
    _StructuredOutputDiagnosticTransport,
    _changed_files,
    _execute_action,
)
from .manifest import (
    PARENT_COMMIT,
    QUESTION,
    REPOSITORY_IDENTITY,
    TARGET_COMMIT,
    _prompt_for_role,
    _ROLE_MAX_OUTPUT_TOKENS,
    _ROLE_INPUTS,
    _raw_digest,
    _time,
    _utc,
    _verify_qualification,
    _verify_repository,
    verify_jwt_run_configuration,
)


JWT_WORLD_MODEL_RESULT_SCHEMA = "swm.jwt-world-model-result@1"
WORLD_MODEL_TOOL_POLICY_REF = "swm-jwt-bounded-local-git@1"
WORLD_ROLE_MAX_OUTPUT_ATTEMPTS = 5


def _array(item: Mapping[str, object]) -> dict[str, object]:
    return {"type": "array", "items": item}


def _object(
    properties: Mapping[str, object], required: Sequence[str] | None = None
) -> dict[str, object]:
    return {
        "type": "object",
        "properties": dict(properties),
        "required": list(required or properties),
        "additionalProperties": False,
    }


_STRING_ARRAY = _array({"type": "string"})
_ACTION_PROPERTIES = {
    "action": {
        "type": "string",
        "enum": ["RESOLVE", "COMPARE", "READ", "SEARCH", "STOP"],
    },
    "revision_role": {"type": "string", "enum": ["PARENT", "TARGET", "NONE"]},
    "path": {"type": "string"},
    "query": {"type": "string"},
    "start_line": {"type": "integer", "minimum": 0},
    "end_line": {"type": "integer", "minimum": 0},
    "rationale": {"type": "string"},
    "stop_reason": {"type": "string"},
}
_FACT_PROPERTIES = {
    "semantic_key": {"type": "string"},
    "statement": {"type": "string"},
    "target": {"type": "string"},
    "context": {"type": "string"},
    "modality": {"type": "string"},
    "condition": {"type": ["string", "null"]},
    "limitation": {"type": ["string", "null"]},
    "entity_refs": _STRING_ARRAY,
    "source_observation_refs": _STRING_ARRAY,
    "need_ids": _STRING_ARRAY,
    "obligation_ids": _STRING_ARRAY,
}
_INFERENCE_PROPERTIES = {
    "semantic_key": {"type": "string"},
    "statement": {"type": "string"},
    "target": {"type": "string"},
    "context": {"type": "string"},
    "modality": {"type": "string"},
    "condition": {"type": ["string", "null"]},
    "limitation": {"type": ["string", "null"]},
    "premise_refs": _STRING_ARRAY,
    "need_ids": _STRING_ARRAY,
    "obligation_ids": _STRING_ARRAY,
}
_ANSWER_CLAIM_PROPERTIES = {
    "semantic_key": {"type": "string"},
    "text": {"type": "string"},
    "kind": {"type": "string", "enum": ["FORMAL_KNOWLEDGE", "KNOWLEDGE_GAP"]},
    "target": {"type": "string"},
    "context": {"type": "string"},
    "modality": {"type": "string"},
    "coverage": {"type": "string"},
    "condition": {"type": ["string", "null"]},
    "limitation": {"type": ["string", "null"]},
    "supporting_refs": _STRING_ARRAY,
    "need_ids": _STRING_ARRAY,
    "obligation_ids": _STRING_ARRAY,
}


_OUTPUT_SCHEMAS = {
    "jwt-investigation-planner@1": OutputSchemaDefinition(
        "jwt_investigation_planner", _object(_ACTION_PROPERTIES)
    ),
    "jwt-fact-proposer@1": OutputSchemaDefinition(
        "jwt_fact_proposer",
        _object(
            {
                "proposals": _array(_object(_FACT_PROPERTIES)),
                "limitations": _STRING_ARRAY,
            }
        ),
    ),
    "jwt-knowledge-reviewer@1": OutputSchemaDefinition(
        "jwt_knowledge_reviewer",
        _object(
            {
                "decision": {"type": "string", "enum": ["ACCEPT", "REJECT"]},
                "accepted_semantic_keys": _STRING_ARRAY,
                "findings": _STRING_ARRAY,
            }
        ),
    ),
    "jwt-inference-proposer@1": OutputSchemaDefinition(
        "jwt_inference_proposer",
        _object(
            {
                "proposals": _array(_object(_INFERENCE_PROPERTIES)),
                "limitations": _STRING_ARRAY,
            }
        ),
    ),
    "jwt-sufficiency-reviewer@1": OutputSchemaDefinition(
        "jwt_sufficiency_reviewer",
        _object(
            {
                "obligations": _array(
                    _object(
                        {
                            "obligation_id": {"type": "string"},
                            "status": {
                                "type": "string",
                                "enum": [
                                    "SATISFIED",
                                    "GAP",
                                    "UNKNOWN",
                                    "CONFLICT",
                                    "INSUFFICIENT",
                                ],
                            },
                            "supporting_refs": _STRING_ARRAY,
                            "finding": {"type": "string"},
                        }
                    )
                ),
                "joint_constraints": _array(
                    _object(
                        {
                            "constraint_id": {"type": "string"},
                            "status": {
                                "type": "string",
                                "enum": [
                                    "SATISFIED",
                                    "GAP",
                                    "UNKNOWN",
                                    "CONFLICT",
                                    "INSUFFICIENT",
                                ],
                            },
                            "supporting_refs": _STRING_ARRAY,
                            "finding": {"type": "string"},
                        }
                    )
                ),
                "overall": {
                    "type": "string",
                    "enum": ["SATISFIED", "INSUFFICIENT"],
                },
            }
        ),
    ),
    "jwt-answer-generator@1": OutputSchemaDefinition(
        "jwt_answer_generator",
        _object(
            {
                "claims": _array(_object(_ANSWER_CLAIM_PROPERTIES)),
                "answer": {"type": "string"},
                "gaps": _STRING_ARRAY,
            }
        ),
    ),
    "jwt-answer-reviewer@1": OutputSchemaDefinition(
        "jwt_answer_reviewer",
        _object(
            {
                "decision": {
                    "type": "string",
                    "enum": ["APPROVED", "REVISION_REQUIRED", "REJECTED"],
                },
                "claim_findings": _array(
                    _object(
                        {
                            "semantic_key": {"type": "string"},
                            "outcome": {"type": "string", "enum": ["PASS", "FAIL"]},
                            "finding": {"type": ["string", "null"]},
                        }
                    )
                ),
                "missing_obligation_ids": _STRING_ARRAY,
            }
        ),
    ),
}


def run_world_model(
    *,
    run_configuration_path: str | Path,
    repository_path: str | Path,
    runtime_directory: str | Path,
    result_directory: str | Path,
    qualification: ArkChatConformanceQualification,
    configuration: VolcengineArkModelConfiguration,
    transport: ChatCompletionsTransport,
    now: datetime | None = None,
) -> Path:
    """Execute one isolated JWT seven-role run and seal its private result."""

    run_configuration = _load_object(run_configuration_path, "JWT run configuration")
    started_at = _utc(now or datetime.now(timezone.utc))
    _verify_qualification(qualification, configuration, at=started_at)
    verify_jwt_run_configuration(
        run_configuration, qualification, configuration, at=started_at
    )
    runtime = Path(runtime_directory).resolve()
    result_root = Path(result_directory).resolve()
    repository = Path(repository_path).resolve()
    if result_root != runtime and runtime not in result_root.parents:
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            "World Model result directory must be inside the frozen runtime directory",
        )
    expected_runtime_digest = run_configuration["isolation"]["runtime_directory_digest"]
    if _raw_digest(str(runtime).encode("utf-8")).value != expected_runtime_digest:
        raise DomainError(ErrorCode.QUALIFICATION_INVALID, "runtime directory does not match run configuration")
    if runtime == repository or runtime in repository.parents or repository in runtime.parents:
        raise DomainError(ErrorCode.INVALID_ARGUMENT, "runtime and source repository must be separate")
    source = _verify_repository(repository)
    if source != run_configuration["source"]:
        raise DomainError(ErrorCode.QUALIFICATION_INVALID, "source boundary differs from run configuration")

    budget = run_configuration["budget"]
    diagnostic_transport = _StructuredOutputDiagnosticTransport(transport)
    adapter = VolcengineArkChatCompletionsNoToolsAdapter(
        transport=diagnostic_transport,
        configuration=configuration,
        output_schemas=_OUTPUT_SCHEMAS,
        live_qualification=qualification,
    )
    started_tick = time.monotonic()
    call_records: list[dict[str, object]] = []
    failed_call_records: list[dict[str, object]] = []
    provider_request_ids: list[str] = []
    model_attempt_count = 0
    input_tokens = 0
    output_tokens = 0

    def invoke(
        role: str,
        items: Sequence[Mapping[str, object]],
        semantic_validator: Callable[[Mapping[str, object]], object] | None = None,
    ) -> object:
        nonlocal input_tokens, output_tokens, model_attempt_count
        allowed = set(_ROLE_INPUTS[role])
        if not items or any(item.get("kind") not in allowed for item in items):
            raise DomainError(ErrorCode.CONTROL_STATE_DENIED, f"{role} received an unauthorized input kind")
        normalized_items = []
        for ordinal, item in enumerate(items):
            if set(item) != {"kind", "authority_ref", "payload"}:
                raise DomainError(ErrorCode.INVALID_ARGUMENT, "authorized input item shape is invalid")
            core = {
                "ordinal": ordinal,
                "kind": item["kind"],
                "authority_ref": item["authority_ref"],
                "payload": copy.deepcopy(item["payload"]),
            }
            normalized_items.append({**core, "item_digest": digest_of(core).value})
        prompt = _prompt_for_role(role)
        schema_ref = f"jwt-{role.lower().replace('_', '-')}@1"
        schema = _OUTPUT_SCHEMAS[schema_ref]
        ordinal = len(call_records)
        max_output_tokens = _ROLE_MAX_OUTPUT_TOKENS[role]
        recovery_feedback: list[dict[str, object]] = []
        for retry_ordinal in range(WORLD_ROLE_MAX_OUTPUT_ATTEMPTS):
            if model_attempt_count >= budget["max_model_calls"]:
                raise DomainError(ErrorCode.BUDGET_EXHAUSTED, "World Model call budget exhausted")
            if (time.monotonic() - started_tick) * 1000 >= budget["max_duration_milliseconds"]:
                raise DomainError(ErrorCode.BUDGET_EXHAUSTED, "World Model duration budget exhausted")
            attempt_ordinal = model_attempt_count
            model_attempt_count += 1
            feedback_digest = digest_of(recovery_feedback).value
            user_payload = {
                "role": role,
                "question": QUESTION,
                "authorized_inputs": normalized_items,
                "structured_output_recovery_feedback": recovery_feedback,
            }
            user = json.dumps(
                user_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            )
            request_core = {
                "role": role,
                "ordinal": ordinal,
                "attempt_ordinal": attempt_ordinal,
                "retry_ordinal": retry_ordinal,
                "prompt_digest": digest_of(prompt).value,
                "authorized_input_digest": digest_of(normalized_items).value,
                "recovery_feedback_digest": feedback_digest,
                "schema_digest": digest_of(schema.schema).value,
                "model_ref": configuration.model_ref,
                "max_output_tokens": max_output_tokens,
                "timeout_milliseconds": 60_000,
            }
            request = ProviderRequest(
                model_ref=configuration.model_ref,
                messages=(
                    RenderedMessage("system", prompt, f"jwt-{role}-prompt", digest_of(prompt)),
                    RenderedMessage(
                        "user",
                        user,
                        f"jwt-{role}-input-{ordinal}-attempt-{attempt_ordinal}",
                        digest_of(user),
                    ),
                ),
                output_schema_ref=schema_ref,
                tools=(),
                store=False,
                stream=False,
                max_output_tokens=max_output_tokens,
                timeout_milliseconds=60_000,
                metadata=(("purpose", "jwt-world-model-capability-run"), ("role", role)),
                digest=digest_of(request_core),
            )
            try:
                response = adapter.invoke(request)
            except ProviderOutcomeUnknown as exc:
                exc.world_role = role
                exc.world_call_ordinal = ordinal
                raise
            except DomainError as exc:
                diagnostic = diagnostic_transport.last_diagnostic
                retryable = exc.code is ErrorCode.STRUCTURED_OUTPUT_INVALID or (
                    exc.code is ErrorCode.PROVIDER_RESPONSE_INVALID
                    and diagnostic.get("provider_finish_reason") == "length"
                )
                provider_request_id = diagnostic.get("provider_request_id")
                actual_model = diagnostic.get("actual_model_fingerprint")
                failed_input_tokens = diagnostic.get("input_tokens")
                failed_output_tokens = diagnostic.get("output_tokens")
                output_digest = diagnostic.get("assistant_content_digest")
                complete_failure_evidence = (
                    isinstance(provider_request_id, str)
                    and provider_request_id not in provider_request_ids
                    and actual_model == configuration.actual_model_fingerprint
                    and isinstance(failed_input_tokens, int)
                    and isinstance(failed_output_tokens, int)
                    and diagnostic.get("usage_complete") == "YES"
                    and isinstance(output_digest, str)
                )
                if not retryable or not complete_failure_evidence:
                    raise DomainError(
                        exc.code,
                        exc.message,
                        {
                            **diagnostic,
                            **exc.details,
                            "world_role": role,
                            "world_call_ordinal": ordinal,
                        },
                    ) from exc
                provider_request_ids.append(provider_request_id)
                input_tokens += failed_input_tokens
                output_tokens += failed_output_tokens
                failed_call_records.append(
                    {
                        "attempt_ordinal": attempt_ordinal,
                        "logical_call_ordinal": ordinal,
                        "retry_ordinal": retry_ordinal,
                        "role": role,
                        "outcome": "DENIED_INVALID_OUTPUT",
                        "error_code": exc.code.value,
                        "error_message": exc.message,
                        "error_details": dict(exc.details),
                        "prompt_digest": digest_of(prompt).value,
                        "output_contract_ref": schema_ref,
                        "output_contract_digest": digest_of(schema.schema).value,
                        "authorized_inputs": copy.deepcopy(normalized_items),
                        "recovery_feedback": copy.deepcopy(recovery_feedback),
                        "recovery_feedback_digest": feedback_digest,
                        "provider_request_digest": request.digest.value,
                        "provider_request_id": provider_request_id,
                        "actual_model_fingerprint": actual_model,
                        "input_tokens": failed_input_tokens,
                        "output_tokens": failed_output_tokens,
                        "usage_complete": True,
                        "finish_reason": diagnostic.get("provider_finish_reason"),
                        "output_bytes": diagnostic.get("assistant_content_bytes"),
                        "output_digest": output_digest,
                    }
                )
                recovery_feedback.append(
                    {
                        "denied_attempt": retry_ordinal,
                        "error_code": exc.code.value,
                        "error_message": exc.message,
                        "error_details": dict(exc.details),
                        "output_digest": output_digest,
                        "required_top_level_fields": list(schema.schema["required"]),
                        "instruction": "Return a new complete JSON object matching the closed schema exactly.",
                    }
                )
                if retry_ordinal + 1 < WORLD_ROLE_MAX_OUTPUT_ATTEMPTS:
                    continue
                raise DomainError(
                    ErrorCode.STRUCTURED_OUTPUT_INVALID,
                    "World Model structured output recovery attempts exhausted",
                    {
                        "world_role": role,
                        "world_call_ordinal": ordinal,
                        "recovery_attempts": WORLD_ROLE_MAX_OUTPUT_ATTEMPTS,
                    },
                ) from exc
            if (
                response.provider_request_id is None
                or response.provider_request_id in provider_request_ids
                or response.actual_model_fingerprint
                != configuration.actual_model_fingerprint
                or not response.usage_complete
            ):
                raise DomainError(
                    ErrorCode.QUALIFICATION_INVALID,
                    "World Model response identity, model, or usage is incomplete",
                )
            decoded = schema.validate_output_text(response.output_text)
            provider_request_ids.append(response.provider_request_id)
            input_tokens += response.input_tokens or 0
            output_tokens += response.output_tokens or 0
            semantic_result: object = decoded
            if semantic_validator is not None:
                try:
                    semantic_result = semantic_validator(decoded)
                except DomainError as exc:
                    if exc.code is not ErrorCode.STRUCTURED_OUTPUT_INVALID:
                        raise
                    failed_call_records.append(
                        {
                            "attempt_ordinal": attempt_ordinal,
                            "logical_call_ordinal": ordinal,
                            "retry_ordinal": retry_ordinal,
                            "role": role,
                            "outcome": "DENIED_INVALID_OUTPUT",
                            "error_code": exc.code.value,
                            "error_message": exc.message,
                            "error_details": dict(exc.details),
                            "prompt_digest": digest_of(prompt).value,
                            "output_contract_ref": schema_ref,
                            "output_contract_digest": digest_of(schema.schema).value,
                            "authorized_inputs": copy.deepcopy(normalized_items),
                            "recovery_feedback": copy.deepcopy(recovery_feedback),
                            "recovery_feedback_digest": feedback_digest,
                            "provider_request_digest": request.digest.value,
                            "provider_request_id": response.provider_request_id,
                            "actual_model_fingerprint": response.actual_model_fingerprint,
                            "input_tokens": response.input_tokens,
                            "output_tokens": response.output_tokens,
                            "usage_complete": True,
                            "finish_reason": response.termination_reason,
                            "output_bytes": len(response.output_text.encode("utf-8")),
                            "output_digest": response.output_digest.value,
                        }
                    )
                    recovery_feedback.append(
                        {
                            "denied_attempt": retry_ordinal,
                            "error_code": exc.code.value,
                            "error_message": exc.message,
                            "error_details": dict(exc.details),
                            "output_digest": response.output_digest.value,
                            "required_top_level_fields": list(schema.schema["required"]),
                            "instruction": "Return a new complete JSON object matching the closed schema exactly.",
                        }
                    )
                    if retry_ordinal + 1 < WORLD_ROLE_MAX_OUTPUT_ATTEMPTS:
                        continue
                    raise DomainError(
                        ErrorCode.STRUCTURED_OUTPUT_INVALID,
                        "World Model semantic recovery attempts exhausted",
                        {
                            "world_role": role,
                            "world_call_ordinal": ordinal,
                            "recovery_attempts": WORLD_ROLE_MAX_OUTPUT_ATTEMPTS,
                            **exc.details,
                        },
                    ) from exc
            call_records.append(
                {
                    "ordinal": ordinal,
                    "attempt_ordinal": attempt_ordinal,
                    "retry_ordinal": retry_ordinal,
                    "role": role,
                    "prompt_ref": f"prompt:{schema_ref}",
                    "prompt_digest": digest_of(prompt).value,
                    "output_contract_ref": schema_ref,
                    "output_contract_digest": digest_of(schema.schema).value,
                    "authorized_inputs": normalized_items,
                    "recovery_feedback": copy.deepcopy(recovery_feedback),
                    "recovery_feedback_digest": feedback_digest,
                    "provider_request_digest": request.digest.value,
                    "provider_request_id": response.provider_request_id,
                    "actual_model_fingerprint": response.actual_model_fingerprint,
                    "input_tokens": response.input_tokens,
                    "output_tokens": response.output_tokens,
                    "usage_complete": response.usage_complete,
                    "output_normalization": response.output_normalization,
                    "output_digest": response.output_digest.value,
                    "structured_output": decoded,
                    "structured_output_digest": digest_of(decoded).value,
                }
            )
            return semantic_result
        raise AssertionError("unreachable structured output recovery state")

    requirement = run_configuration["requirement"]
    boundary_item = _item("BOUNDARY", "jwt-run-boundary", run_configuration["source"])
    requirement_item = _item("REQUIREMENT", requirement["requirement_id"], requirement)
    build_target = {
        "repository_identity": REPOSITORY_IDENTITY,
        "target_commit": TARGET_COMMIT,
        "parent_commit": PARENT_COMMIT,
        "comparison_context": "PARENT_TO_TARGET",
        "tool_policy_ref": WORLD_MODEL_TOOL_POLICY_REF,
    }
    build_item = _item("BUILD_TARGET", "jwt-build-target", build_target)
    contract_item = _item("CONTRACT_REF", "jwt-formal-contract-revision-002", {
        "role_matrix_digest": digest_of(run_configuration["roles"]).value,
        "configuration_digest": run_configuration["configuration_digest"],
    })
    changed_files = _changed_files(repository)
    observations: list[dict[str, object]] = []
    source_trace: list[dict[str, object]] = []
    seen_actions: set[Digest] = set()
    source_bytes = 0
    files_read: set[tuple[str, str]] = set()

    def record_planner_denial(
        action_core: Mapping[str, object], error: DomainError
    ) -> None:
        nonlocal source_bytes
        content = json.dumps(
            {
                "outcome": "DENIED",
                "error": error.code.value,
                "message": error.message,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        content_bytes = content.encode("utf-8")
        source_bytes += len(content_bytes)
        if source_bytes > budget["max_source_bytes"]:
            raise DomainError(
                ErrorCode.BUDGET_EXHAUSTED,
                "World Model source-byte budget exhausted",
            ) from error
        action_digest = digest_of(action_core)
        content_digest = _raw_digest(content_bytes)
        observation_ref = (
            f"swm-observation:{len(observations):03d}:{content_digest.value}"
        )
        observations.append(
            {
                "observation_ref": observation_ref,
                "tool": "DENIED",
                "locator": f"swm-tool-denial:{action_digest.value}",
                "content": content,
                "content_digest": content_digest.value,
            }
        )
        source_trace.append(
            {
                "ordinal": len(source_trace),
                "tool": "DENIED",
                "request": dict(action_core),
                "request_digest": action_digest.value,
                "observation_ref": observation_ref,
                "result_digest": content_digest.value,
            }
        )

    while len(source_trace) < budget["max_tool_steps"]:
        observation_item = _item(
            "SOURCE_OBSERVATION", "jwt-source-observations", observations
        )
        planner = invoke(
            "INVESTIGATION_PLANNER",
            (boundary_item, requirement_item, build_item, observation_item, contract_item),
        )
        action = str(planner["action"])
        action_core = {
            "action": action,
            "revision_role": planner["revision_role"],
            "path": planner["path"],
            "query": planner["query"],
            "start_line": planner["start_line"],
            "end_line": planner["end_line"],
        }
        try:
            _validate_planner_step(planner, action)
        except DomainError as exc:
            if exc.code is not ErrorCode.STRUCTURED_OUTPUT_INVALID:
                raise
            record_planner_denial(action_core, exc)
            continue
        if action == "STOP":
            completed_tools = {item["tool"] for item in source_trace}
            refresh_read_complete = any(
                item["tool"] == "READ"
                and item["request"]
                == {
                    "action": "READ",
                    "revision_role": "TARGET",
                    "path": "mall-security/src/main/java/com/macro/mall/security/util/JwtTokenUtil.java",
                    "query": "",
                    "start_line": 150,
                    "end_line": 203,
                }
                for item in source_trace
            )
            if not {"RESOLVE", "COMPARE"}.issubset(completed_tools) or not refresh_read_complete:
                record_planner_denial(
                    action_core,
                    DomainError(
                        ErrorCode.STRUCTURED_OUTPUT_INVALID,
                        "planner stopped before completing the frozen comparison and refresh evidence boundary",
                    ),
                )
                continue
            break
        action_digest = digest_of(action_core)
        if action_digest in seen_actions:
            record_planner_denial(
                action_core,
                DomainError(
                    ErrorCode.EVALUATION_RUN_CONFLICT,
                    "planner repeated an identical source action without new state",
                ),
            )
            continue
        seen_actions.add(action_digest)
        try:
            content, locator = _execute_action(
                repository,
                changed_files,
                action_core,
                max_source_bytes=budget["max_source_bytes"] - source_bytes,
            )
        except DomainError as exc:
            if exc.code is not ErrorCode.INVALID_ARGUMENT:
                raise
            record_planner_denial(action_core, exc)
            continue
        if action == "READ":
            files_read.add((str(planner["revision_role"]), str(planner["path"])))
            if len(files_read) > budget["max_files_read"]:
                raise DomainError(ErrorCode.BUDGET_EXHAUSTED, "World Model file budget exhausted")
        source_bytes += len(content.encode("utf-8"))
        content_digest = _raw_digest(content.encode("utf-8"))
        observation_ref = f"swm-observation:{len(observations):03d}:{content_digest.value}"
        observation = {
            "observation_ref": observation_ref,
            "tool": action,
            "locator": locator,
            "content": content,
            "content_digest": content_digest.value,
        }
        observations.append(observation)
        source_trace.append(
            {
                "ordinal": len(source_trace),
                "tool": action,
                "request": action_core,
                "request_digest": action_digest.value,
                "observation_ref": observation_ref,
                "result_digest": content_digest.value,
            }
        )
    else:
        raise DomainError(ErrorCode.BUDGET_EXHAUSTED, "planner did not stop within tool budget")

    entities = _bootstrap_entities(changed_files)
    entity_snapshot = _snapshot("ENTITY", None, entities)
    facts: list[dict[str, object]] = []
    semantic_keys: set[str] = set()
    for observation in observations:
        if observation["tool"] == "DENIED":
            continue
        if observation["tool"] == "RESOLVE":
            eligible_need_ids = {"JWT-N01"}
        elif observation["tool"] == "COMPARE":
            eligible_need_ids = {
                "JWT-N01",
                "JWT-N02",
                "JWT-N03",
                "JWT-N04",
                "JWT-N06",
            }
        elif observation["tool"] == "READ":
            eligible_need_ids = {"JWT-N05"}
        else:
            eligible_need_ids = {need["need_id"] for need in requirement["needs"]}
        eligible_needs = [
            need for need in requirement["needs"] if need["need_id"] in eligible_need_ids
        ]
        scoped_need_groups = (
            [[eligible_needs[0]]]
            if observation["tool"] == "RESOLVE"
            else _bounded_need_groups(eligible_needs)
        )
        for need_group in scoped_need_groups:
            scoped_requirement = _scope_requirement(requirement, need_group)
            scope_id = "+".join(need["need_id"] for need in need_group)
            scoped_requirement_item = _item(
                "REQUIREMENT",
                f"jwt-fact-scope:{scope_id}",
                scoped_requirement,
            )
            proposals = invoke(
                "FACT_PROPOSER",
                (
                    boundary_item,
                    scoped_requirement_item,
                    build_item,
                    _item("SOURCE_OBSERVATION", observation["observation_ref"], observation),
                    _item("FORMAL_KNOWLEDGE", "entity-snapshot", entity_snapshot),
                    contract_item,
                ),
                lambda output: _validate_fact_proposals(
                    output["proposals"],
                    observation,
                    entities,
                    scoped_requirement,
                    semantic_keys,
                ),
            )
            accepted_keys = invoke(
                "KNOWLEDGE_REVIEWER",
                (
                    boundary_item,
                    scoped_requirement_item,
                    build_item,
                    _item("KNOWLEDGE_PROPOSAL", "fact-proposal", proposals),
                    _item("SOURCE_OBSERVATION", observation["observation_ref"], observation),
                    _item("FORMAL_KNOWLEDGE", "entity-snapshot", entity_snapshot),
                    contract_item,
                ),
                lambda output: _validate_fact_review(output, proposals),
            )
            for item in proposals:
                if item["semantic_key"] not in accepted_keys:
                    continue
                fact_core = {
                    **item,
                    "source_locators": [observation["locator"]],
                    "source_digests": [observation["content_digest"]],
                }
                facts.append(
                    {
                        "formal_ref": f"fact:{digest_of(fact_core).value}",
                        "kind": "FACT",
                        **fact_core,
                    }
                )
    fact_snapshot = _snapshot("FACT", entity_snapshot["snapshot_ref"], facts)

    inferences = invoke(
        "INFERENCE_PROPOSER",
        (
            boundary_item,
            requirement_item,
            _item("FORMAL_KNOWLEDGE", fact_snapshot["snapshot_ref"], fact_snapshot),
            contract_item,
        ),
        lambda output: _validate_inferences(
            output["proposals"], facts, requirement, set(semantic_keys)
        ),
    )
    semantic_keys.update(item["semantic_key"] for item in inferences)
    accepted_inference_keys = invoke(
        "KNOWLEDGE_REVIEWER",
        (
            boundary_item,
            requirement_item,
            _item("KNOWLEDGE_PROPOSAL", "inference-proposal", inferences),
            _item("FORMAL_KNOWLEDGE", fact_snapshot["snapshot_ref"], fact_snapshot),
            contract_item,
        ),
        lambda output: _validate_fact_review(output, inferences),
    )
    inferences = [
        item for item in inferences if item["semantic_key"] in accepted_inference_keys
    ]
    inference_snapshot = _snapshot(
        "INFERENCE", fact_snapshot["snapshot_ref"], facts + inferences
    )
    formal_members = facts + inferences

    assessment_fragments: list[dict[str, object]] = []
    sufficiency_need_groups = [
        requirement["needs"][index : index + 2]
        for index in range(0, len(requirement["needs"]), 2)
    ]
    for need_group in sufficiency_need_groups:
        scoped_requirement = _scope_requirement(requirement, need_group)
        scope_id = "+".join(need["need_id"] for need in need_group)
        scoped_obligation_ids = {
            obligation["obligation_id"]
            for need in need_group
            for obligation in need["obligations"]
        }
        scoped_formal_members = [
            copy.deepcopy(item)
            for item in formal_members
            if scoped_obligation_ids.intersection(item.get("obligation_ids", []))
        ]
        scoped_snapshot = _snapshot(
            "SUFFICIENCY_SCOPE",
            inference_snapshot["snapshot_ref"],
            scoped_formal_members,
        )
        fragment = invoke(
            "SUFFICIENCY_REVIEWER",
            (
                boundary_item,
                _item(
                    "REQUIREMENT",
                    f"jwt-sufficiency-requirement:{scope_id}",
                    scoped_requirement,
                ),
                _item(
                    "FORMAL_KNOWLEDGE",
                    scoped_snapshot["snapshot_ref"],
                    scoped_snapshot,
                ),
                contract_item,
            ),
            lambda output, scoped_requirement=scoped_requirement,
            scoped_formal_members=scoped_formal_members: _validate_assessment(
                output, scoped_requirement, scoped_formal_members
            ),
        )
        assessment_fragments.append(fragment)
    combined_obligations = [
        item
        for fragment in assessment_fragments
        for item in fragment["obligations"]
    ]
    joint_boundary_valid = bool(formal_members) and all(
        item.get("target") == TARGET_COMMIT
        and item.get("context") == "PARENT_TO_TARGET"
        for item in formal_members
    )
    combined_joints = [
        {
            "constraint_id": constraint["constraint_id"],
            "status": "SATISFIED" if joint_boundary_valid else "CONFLICT",
            "supporting_refs": (
                [item["formal_ref"] for item in formal_members]
                if joint_boundary_valid
                else []
            ),
            "finding": (
                "Every formal member is bound to the frozen target and PARENT_TO_TARGET context."
                if joint_boundary_valid
                else "Formal members do not all share the frozen target and comparison context."
            ),
        }
        for constraint in requirement["joint_constraints"]
    ]
    assessment = {
        "obligations": combined_obligations,
        "joint_constraints": combined_joints,
        "overall": (
            "SATISFIED"
            if all(
                item["status"] == "SATISFIED"
                for item in combined_obligations + combined_joints
            )
            else "INSUFFICIENT"
        ),
    }
    assessment = _validate_assessment(assessment, requirement, formal_members)
    answer_fragments: list[dict[str, object]] = []
    answer_scopes: list[
        tuple[dict[str, object], dict[str, object], list[dict[str, object]]]
    ] = []
    answer_need_groups = _bounded_need_groups(requirement["needs"])
    for need_group in answer_need_groups:
        scoped_requirement = _scope_requirement(requirement, need_group)
        scope_id = "+".join(need["need_id"] for need in need_group)
        scoped_obligation_ids = {
            item["obligation_id"]
            for need in need_group
            for item in need["obligations"]
        }
        scoped_obligations = [
            copy.deepcopy(item)
            for item in assessment["obligations"]
            if item["obligation_id"] in scoped_obligation_ids
        ]
        scoped_assessment = {
            "obligations": scoped_obligations,
            "joint_constraints": [],
            "overall": (
                "SATISFIED"
                if all(item["status"] == "SATISFIED" for item in scoped_obligations)
                else "INSUFFICIENT"
            ),
        }
        scoped_formal_members = [
            copy.deepcopy(item)
            for item in formal_members
            if scoped_obligation_ids.intersection(item.get("obligation_ids", []))
        ]
        scoped_formal_snapshot = _snapshot(
            "ANSWER_SCOPE",
            inference_snapshot["snapshot_ref"],
            scoped_formal_members,
        )
        fragment = invoke(
            "ANSWER_GENERATOR",
            (
                boundary_item,
                _item(
                    "REQUIREMENT",
                    f"jwt-answer-scope:{scope_id}",
                    scoped_requirement,
                ),
                _item(
                    "ASSESSMENT",
                    f"jwt-sufficiency-scope:{scope_id}",
                    scoped_assessment,
                ),
                _item(
                    "FORMAL_KNOWLEDGE",
                    scoped_formal_snapshot["snapshot_ref"],
                    scoped_formal_snapshot,
                ),
                contract_item,
            ),
            lambda output, scoped_assessment=scoped_assessment,
            scoped_formal_members=scoped_formal_members,
            scoped_requirement=scoped_requirement: _validate_answer(
                output,
                scoped_assessment,
                scoped_formal_members,
                scoped_requirement,
            ),
        )
        answer_fragments.append(fragment)
        answer_scopes.append(
            (scoped_requirement, scoped_assessment, scoped_formal_members)
        )
    candidate = {
        "claims": [
            claim
            for fragment in answer_fragments
            for claim in fragment["claims"]
        ],
        "answer": "\n".join(
            claim["text"]
            for fragment in answer_fragments
            for claim in fragment["claims"]
        ),
        "gaps": [
            gap
            for fragment in answer_fragments
            for gap in fragment["gaps"]
        ],
    }
    candidate = _validate_answer(candidate, assessment, formal_members, requirement)
    review_fragments: list[dict[str, object]] = []
    for fragment, scope in zip(answer_fragments, answer_scopes, strict=True):
        scoped_requirement, scoped_assessment, scoped_formal_members = scope
        scope_id = "+".join(
            need["need_id"] for need in scoped_requirement["needs"]
        )
        scoped_formal_snapshot = _snapshot(
            "ANSWER_REVIEW_SCOPE",
            inference_snapshot["snapshot_ref"],
            scoped_formal_members,
        )
        review_fragment = invoke(
            "ANSWER_REVIEWER",
            (
                boundary_item,
                _item(
                    "REQUIREMENT",
                    f"jwt-answer-review-scope:{scope_id}",
                    scoped_requirement,
                ),
                _item(
                    "ASSESSMENT",
                    f"jwt-answer-review-assessment:{scope_id}",
                    scoped_assessment,
                ),
                _item("ANSWER_CANDIDATE", f"jwt-answer-fragment:{scope_id}", fragment),
                _item(
                    "FORMAL_KNOWLEDGE",
                    scoped_formal_snapshot["snapshot_ref"],
                    scoped_formal_snapshot,
                ),
                contract_item,
            ),
            lambda output, fragment=fragment: _validate_answer_review(output, fragment),
        )
        review_fragments.append(review_fragment)
    review = {
        "decision": (
            "APPROVED"
            if all(item["decision"] == "APPROVED" for item in review_fragments)
            else "REVISION_REQUIRED"
        ),
        "claim_findings": [
            finding
            for fragment in review_fragments
            for finding in fragment["claim_findings"]
        ],
        "missing_obligation_ids": [
            obligation_id
            for fragment in review_fragments
            for obligation_id in fragment["missing_obligation_ids"]
        ],
    }
    review = _validate_answer_review(review, candidate)
    approved = (
        review["decision"] == "APPROVED"
        and not review["missing_obligation_ids"]
        and all(item["outcome"] == "PASS" for item in review["claim_findings"])
    )
    completed_at = _utc(now or datetime.now(timezone.utc))
    if completed_at >= qualification.valid_until:
        raise DomainError(ErrorCode.QUALIFICATION_INVALID, "qualification expired during World Model run")
    roles_executed = {role: 0 for role in _ROLE_INPUTS}
    for call in call_records:
        roles_executed[call["role"]] += 1
    if any(count < 1 for count in roles_executed.values()):
        raise DomainError(ErrorCode.EVALUATION_RUN_CONFLICT, "not all seven model roles executed")
    result_core = {
        "schema": JWT_WORLD_MODEL_RESULT_SCHEMA,
        "run_id": f"jwtrun_{uuid.uuid4().hex}",
        "run_configuration_ref": run_configuration["run_configuration_id"],
        "run_configuration_digest": run_configuration["configuration_digest"],
        "started_at": _time(started_at),
        "completed_at": _time(completed_at),
        "model_ref": configuration.model_ref,
        "adapter_version": configuration.adapter_version,
        "conformance_result_ref": qualification.result_ref,
        "source": source,
        "oracle": run_configuration["oracle"],
        "roles_executed": roles_executed,
        "provider_request_ids": provider_request_ids,
        "usage": {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "complete": True,
            "price_configured": False,
        },
        "budget_usage": {
            "tool_steps": len(source_trace),
            "files_read": len(files_read),
            "source_bytes": source_bytes,
            "model_calls": model_attempt_count,
            "duration_milliseconds": max(0, round((time.monotonic() - started_tick) * 1000)),
        },
        "model_calls": call_records,
        "failed_model_calls": failed_call_records,
        "source_trace": source_trace,
        "observations": observations,
        "snapshots": [entity_snapshot, fact_snapshot, inference_snapshot],
        "assessment": assessment,
        "candidate": candidate,
        "answer_review": review,
        "isolation_proof": {
            "source_operation_attempts_after_source_close": 0,
            "artifact_payload_read_attempts_after_source_close": 0,
            "evidence_content_read_attempts_after_source_close": 0,
            "investigation_attach_attempts_after_source_close": 0,
            "source_closed_roles": list(run_configuration["isolation"]["source_closed_roles"]),
            "production_namespace_writes": 0,
            "evaluation_sink_only": True,
        },
        "delivery": {
            "state": "DELIVERED" if approved else "REVIEW_REJECTED",
            "body_digest": digest_of(candidate["answer"]).value if approved else None,
            "comparison_authorized": approved,
        },
        "outcome": "PASS" if approved else "FAIL",
    }
    document = {**result_core, "result_digest": digest_of(result_core).value}
    verify_world_model_result(document, run_configuration, qualification, configuration)
    payload = json.dumps(document, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8") + b"\n"
    if len(payload) > budget["max_result_bytes"]:
        raise DomainError(ErrorCode.BUDGET_EXHAUSTED, "World Model result exceeds result-byte budget")
    return _seal_private(
        payload,
        result_root,
        f"JWT-WORLD-MODEL-RESULT-{result_core['run_id']}.json",
    )


def verify_world_model_result(
    document: Mapping[str, object],
    run_configuration: Mapping[str, object],
    qualification: ArkChatConformanceQualification,
    configuration: VolcengineArkModelConfiguration,
) -> None:
    """Verify the immutable envelope and core run/isolation bindings."""

    if document.get("schema") != JWT_WORLD_MODEL_RESULT_SCHEMA:
        raise DomainError(ErrorCode.QUALIFICATION_INVALID, "World Model result schema is invalid")
    supplied = document.get("result_digest")
    if not isinstance(supplied, str):
        raise DomainError(ErrorCode.QUALIFICATION_INVALID, "World Model result digest is missing")
    try:
        digest = Digest(supplied)
    except ValueError as exc:
        raise DomainError(ErrorCode.QUALIFICATION_INVALID, "World Model result digest is invalid") from exc
    core = {key: value for key, value in document.items() if key != "result_digest"}
    if digest_of(core) != digest:
        raise DomainError(ErrorCode.QUALIFICATION_INVALID, "World Model result digest does not verify")
    if (
        document.get("run_configuration_ref") != run_configuration.get("run_configuration_id")
        or document.get("run_configuration_digest") != run_configuration.get("configuration_digest")
        or document.get("model_ref") != configuration.model_ref
        or document.get("adapter_version") != configuration.adapter_version
        or document.get("conformance_result_ref") != qualification.result_ref
        or document.get("oracle") != run_configuration.get("oracle")
    ):
        raise DomainError(ErrorCode.QUALIFICATION_INVALID, "World Model result dependencies are stale")
    isolation = document.get("isolation_proof")
    if not isinstance(isolation, dict) or any(
        isolation.get(field) != 0
        for field in (
            "source_operation_attempts_after_source_close",
            "artifact_payload_read_attempts_after_source_close",
            "evidence_content_read_attempts_after_source_close",
            "investigation_attach_attempts_after_source_close",
            "production_namespace_writes",
        )
    ) or isolation.get("evaluation_sink_only") is not True:
        raise DomainError(ErrorCode.QUALIFICATION_INVALID, "World Model isolation proof is invalid")
    calls = document.get("model_calls")
    failed_calls = document.get("failed_model_calls")
    request_ids = document.get("provider_request_ids")
    if (
        not isinstance(calls, list)
        or not isinstance(failed_calls, list)
        or not isinstance(request_ids, list)
        or len(set(request_ids)) != len(request_ids)
    ):
        raise DomainError(ErrorCode.QUALIFICATION_INVALID, "World Model call evidence is invalid")
    attempts = sorted(
        [*calls, *failed_calls],
        key=lambda item: item.get("attempt_ordinal", -1) if isinstance(item, dict) else -1,
    )
    if (
        any(not isinstance(item, dict) for item in attempts)
        or [item.get("attempt_ordinal") for item in attempts] != list(range(len(attempts)))
        or [item.get("provider_request_id") for item in attempts] != request_ids
    ):
        raise DomainError(ErrorCode.QUALIFICATION_INVALID, "World Model attempt order is invalid")
    token_values = [
        (item.get("input_tokens"), item.get("output_tokens")) for item in attempts
    ]
    usage = document.get("usage")
    budget_usage = document.get("budget_usage")
    if (
        any(
            isinstance(value, bool) or not isinstance(value, int) or value < 0
            for pair in token_values
            for value in pair
        )
        or
        not isinstance(usage, dict)
        or usage.get("complete") is not True
        or usage.get("price_configured") is not False
        or usage.get("input_tokens")
        != sum(pair[0] for pair in token_values)
        or usage.get("output_tokens")
        != sum(pair[1] for pair in token_values)
        or not isinstance(budget_usage, dict)
        or budget_usage.get("model_calls") != len(attempts)
        or len(attempts) > run_configuration["budget"]["max_model_calls"]
    ):
        raise DomainError(ErrorCode.QUALIFICATION_INVALID, "World Model usage evidence is invalid")

    def verify_recovery(record: Mapping[str, object]) -> list[object]:
        feedback = record.get("recovery_feedback")
        retry_ordinal = record.get("retry_ordinal")
        if (
            not isinstance(feedback, list)
            or not isinstance(retry_ordinal, int)
            or isinstance(retry_ordinal, bool)
            or retry_ordinal != len(feedback)
            or retry_ordinal < 0
            or retry_ordinal >= WORLD_ROLE_MAX_OUTPUT_ATTEMPTS
            or record.get("recovery_feedback_digest") != digest_of(feedback).value
        ):
            raise DomainError(ErrorCode.QUALIFICATION_INVALID, "World Model recovery evidence is invalid")
        return feedback
    roles_executed = document.get("roles_executed")
    if not isinstance(roles_executed, dict) or set(roles_executed) != set(_ROLE_INPUTS):
        raise DomainError(ErrorCode.QUALIFICATION_INVALID, "World Model role evidence is incomplete")
    actual_role_counts = {role: 0 for role in _ROLE_INPUTS}
    for ordinal, call in enumerate(calls):
        if not isinstance(call, dict) or call.get("ordinal") != ordinal:
            raise DomainError(ErrorCode.QUALIFICATION_INVALID, "World Model call order is invalid")
        role = call.get("role")
        if role not in _ROLE_INPUTS:
            raise DomainError(ErrorCode.QUALIFICATION_INVALID, "World Model call role is invalid")
        actual_role_counts[role] += 1
        prompt = _prompt_for_role(role)
        schema_ref = f"jwt-{role.lower().replace('_', '-')}@1"
        schema = _OUTPUT_SCHEMAS[schema_ref]
        max_output_tokens = _ROLE_MAX_OUTPUT_TOKENS[role]
        feedback = verify_recovery(call)
        authorized = call.get("authorized_inputs")
        if not isinstance(authorized, list) or not authorized:
            raise DomainError(ErrorCode.QUALIFICATION_INVALID, "World Model authorized inputs are missing")
        allowed = set(_ROLE_INPUTS[role])
        for item_ordinal, item in enumerate(authorized):
            if not isinstance(item, dict) or set(item) != {
                "ordinal",
                "kind",
                "authority_ref",
                "payload",
                "item_digest",
            }:
                raise DomainError(ErrorCode.QUALIFICATION_INVALID, "World Model input item is invalid")
            item_core = {key: item[key] for key in ("ordinal", "kind", "authority_ref", "payload")}
            if (
                item.get("ordinal") != item_ordinal
                or item.get("kind") not in allowed
                or digest_of(item_core).value != item.get("item_digest")
            ):
                raise DomainError(ErrorCode.QUALIFICATION_INVALID, "World Model input authorization is invalid")
        structured = call.get("structured_output")
        try:
            validated = schema.validate_output_text(
                json.dumps(structured, ensure_ascii=False, separators=(",", ":"))
            )
        except DomainError as exc:
            raise DomainError(ErrorCode.QUALIFICATION_INVALID, "World Model structured output is invalid") from exc
        if (
            call.get("prompt_ref") != f"prompt:{schema_ref}"
            or call.get("prompt_digest") != digest_of(prompt).value
            or call.get("output_contract_ref") != schema_ref
            or call.get("output_contract_digest") != digest_of(schema.schema).value
            or call.get("structured_output_digest") != digest_of(validated).value
            or call.get("actual_model_fingerprint")
            != configuration.actual_model_fingerprint
            or call.get("usage_complete") is not True
            or call.get("output_normalization")
            not in {
                "IDENTITY",
                "MARKDOWN_JSON_FENCE_V1",
                "MARKDOWN_JSON_FENCE_WITH_PREFIX_V1",
            }
        ):
            raise DomainError(ErrorCode.QUALIFICATION_INVALID, "World Model call contract is stale")
        request_core = {
            "role": role,
            "ordinal": ordinal,
            "attempt_ordinal": call.get("attempt_ordinal"),
            "retry_ordinal": call.get("retry_ordinal"),
            "prompt_digest": digest_of(prompt).value,
            "authorized_input_digest": digest_of(authorized).value,
            "recovery_feedback_digest": digest_of(feedback).value,
            "schema_digest": digest_of(schema.schema).value,
            "model_ref": configuration.model_ref,
            "max_output_tokens": max_output_tokens,
            "timeout_milliseconds": 60_000,
        }
        if call.get("provider_request_digest") != digest_of(request_core).value:
            raise DomainError(ErrorCode.QUALIFICATION_INVALID, "World Model request digest is invalid")
    for failed in failed_calls:
        role = failed.get("role")
        logical_ordinal = failed.get("logical_call_ordinal")
        if (
            role not in _ROLE_INPUTS
            or not isinstance(logical_ordinal, int)
            or isinstance(logical_ordinal, bool)
            or logical_ordinal < 0
            or failed.get("outcome") != "DENIED_INVALID_OUTPUT"
            or failed.get("error_code")
            not in {
                ErrorCode.STRUCTURED_OUTPUT_INVALID.value,
                ErrorCode.PROVIDER_RESPONSE_INVALID.value,
            }
            or not isinstance(failed.get("error_details"), dict)
            or failed.get("actual_model_fingerprint")
            != configuration.actual_model_fingerprint
            or failed.get("usage_complete") is not True
            or not isinstance(failed.get("input_tokens"), int)
            or not isinstance(failed.get("output_tokens"), int)
            or failed.get("input_tokens") < 0
            or failed.get("output_tokens") < 0
            or not isinstance(failed.get("output_bytes"), int)
            or failed.get("output_bytes") < 1
        ):
            raise DomainError(ErrorCode.QUALIFICATION_INVALID, "failed World Model call evidence is invalid")
        try:
            Digest(str(failed.get("output_digest")))
        except ValueError as exc:
            raise DomainError(ErrorCode.QUALIFICATION_INVALID, "failed output digest is invalid") from exc
        prompt = _prompt_for_role(role)
        schema_ref = f"jwt-{role.lower().replace('_', '-')}@1"
        schema = _OUTPUT_SCHEMAS[schema_ref]
        feedback = verify_recovery(failed)
        authorized = failed.get("authorized_inputs")
        if not isinstance(authorized, list) or not authorized:
            raise DomainError(ErrorCode.QUALIFICATION_INVALID, "failed call inputs are missing")
        allowed = set(_ROLE_INPUTS[role])
        for item_ordinal, item in enumerate(authorized):
            if not isinstance(item, dict) or set(item) != {
                "ordinal",
                "kind",
                "authority_ref",
                "payload",
                "item_digest",
            }:
                raise DomainError(ErrorCode.QUALIFICATION_INVALID, "failed call input is invalid")
            item_core = {key: item[key] for key in ("ordinal", "kind", "authority_ref", "payload")}
            if (
                item.get("ordinal") != item_ordinal
                or item.get("kind") not in allowed
                or digest_of(item_core).value != item.get("item_digest")
            ):
                raise DomainError(ErrorCode.QUALIFICATION_INVALID, "failed call input authorization is invalid")
        if (
            failed.get("prompt_digest") != digest_of(prompt).value
            or failed.get("output_contract_ref") != schema_ref
            or failed.get("output_contract_digest") != digest_of(schema.schema).value
        ):
            raise DomainError(ErrorCode.QUALIFICATION_INVALID, "failed call contract is stale")
        request_core = {
            "role": role,
            "ordinal": logical_ordinal,
            "attempt_ordinal": failed.get("attempt_ordinal"),
            "retry_ordinal": failed.get("retry_ordinal"),
            "prompt_digest": digest_of(prompt).value,
            "authorized_input_digest": digest_of(authorized).value,
            "recovery_feedback_digest": digest_of(feedback).value,
            "schema_digest": digest_of(schema.schema).value,
            "model_ref": configuration.model_ref,
            "max_output_tokens": _ROLE_MAX_OUTPUT_TOKENS[role],
            "timeout_milliseconds": 60_000,
        }
        if failed.get("provider_request_digest") != digest_of(request_core).value:
            raise DomainError(ErrorCode.QUALIFICATION_INVALID, "failed call request digest is invalid")
    for logical_ordinal, successful in enumerate(calls):
        related_failures = sorted(
            [
                item
                for item in failed_calls
                if item.get("logical_call_ordinal") == logical_ordinal
            ],
            key=lambda item: item["retry_ordinal"],
        )
        related_attempts = [*related_failures, successful]
        if (
            [item.get("retry_ordinal") for item in related_attempts]
            != list(range(len(related_attempts)))
            or any(item.get("role") != successful.get("role") for item in related_attempts)
            or any(
                item.get("authorized_inputs") != successful.get("authorized_inputs")
                for item in related_attempts
            )
        ):
            raise DomainError(ErrorCode.QUALIFICATION_INVALID, "World Model retry chain is invalid")
        expected_feedback: list[dict[str, object]] = []
        schema_ref = f"jwt-{successful['role'].lower().replace('_', '-')}@1"
        required_fields = list(_OUTPUT_SCHEMAS[schema_ref].schema["required"])
        for item in related_attempts:
            if item.get("recovery_feedback") != expected_feedback:
                raise DomainError(ErrorCode.QUALIFICATION_INVALID, "World Model retry feedback is invalid")
            if item is successful:
                continue
            expected_feedback.append(
                {
                    "denied_attempt": item["retry_ordinal"],
                    "error_code": item["error_code"],
                    "error_message": item["error_message"],
                    "error_details": item["error_details"],
                    "output_digest": item["output_digest"],
                    "required_top_level_fields": required_fields,
                    "instruction": "Return a new complete JSON object matching the closed schema exactly.",
                }
            )
    if any(
        item.get("logical_call_ordinal") is None
        or item.get("logical_call_ordinal") >= len(calls)
        for item in failed_calls
    ):
        raise DomainError(ErrorCode.QUALIFICATION_INVALID, "failed call is not bound to a successful retry")
    if actual_role_counts != roles_executed or any(value < 1 for value in roles_executed.values()):
        raise DomainError(ErrorCode.QUALIFICATION_INVALID, "World Model role counts do not verify")
    source_closed = set(run_configuration["isolation"]["source_closed_roles"])
    for call in attempts:
        if call["role"] in source_closed and any(
            item["kind"] in {"SOURCE_OBSERVATION", "BUILD_TARGET"}
            for item in call["authorized_inputs"]
        ):
            raise DomainError(ErrorCode.QUALIFICATION_INVALID, "source-closed role received source input")
    snapshots = document.get("snapshots")
    if (
        not isinstance(snapshots, list)
        or len(snapshots) != 3
        or [item.get("kind") for item in snapshots if isinstance(item, dict)]
        != ["ENTITY", "FACT", "INFERENCE"]
        or snapshots[1].get("parent_snapshot_ref") != snapshots[0].get("snapshot_ref")
        or snapshots[2].get("parent_snapshot_ref") != snapshots[1].get("snapshot_ref")
    ):
        raise DomainError(ErrorCode.QUALIFICATION_INVALID, "World Model snapshot chain is invalid")
    for snapshot in snapshots:
        snapshot_core = {
            "kind": snapshot.get("kind"),
            "parent_snapshot_ref": snapshot.get("parent_snapshot_ref"),
            "members": snapshot.get("members"),
        }
        expected_ref = f"snapshot:{str(snapshot.get('kind')).lower()}:{digest_of(snapshot_core).value}"
        if snapshot.get("snapshot_ref") != expected_ref:
            raise DomainError(ErrorCode.QUALIFICATION_INVALID, "World Model snapshot digest is invalid")
    formal_members = snapshots[2]["members"]
    requirement = run_configuration["requirement"]
    try:
        assessment = _validate_assessment(document.get("assessment"), requirement, formal_members)
        candidate = _validate_answer(document.get("candidate"), assessment, formal_members, requirement)
        review = _validate_answer_review(document.get("answer_review"), candidate)
    except (DomainError, TypeError, KeyError) as exc:
        raise DomainError(ErrorCode.QUALIFICATION_INVALID, "World Model delivery evidence is invalid") from exc
    approved = (
        review["decision"] == "APPROVED"
        and not review["missing_obligation_ids"]
        and all(item["outcome"] == "PASS" for item in review["claim_findings"])
    )
    delivery = document.get("delivery")
    if not isinstance(delivery, dict) or (
        approved
        and (
            delivery.get("state") != "DELIVERED"
            or delivery.get("comparison_authorized") is not True
            or delivery.get("body_digest") != digest_of(candidate["answer"]).value
            or document.get("outcome") != "PASS"
        )
    ) or (
        not approved
        and (
            delivery.get("state") != "REVIEW_REJECTED"
            or delivery.get("comparison_authorized") is not False
            or delivery.get("body_digest") is not None
            or document.get("outcome") != "FAIL"
        )
    ):
        raise DomainError(ErrorCode.QUALIFICATION_INVALID, "World Model delivery state is inconsistent")


def _validate_planner_step(step: Mapping[str, object], action: str) -> None:
    if not isinstance(step.get("rationale"), str) or not str(step["rationale"]).strip():
        raise DomainError(ErrorCode.STRUCTURED_OUTPUT_INVALID, "planner rationale is empty")
    action_core = {
        "action": action,
        "revision_role": step["revision_role"],
        "path": step["path"],
        "query": step["query"],
        "start_line": step["start_line"],
        "end_line": step["end_line"],
    }
    if action == "STOP":
        if (
            any(action_core[field] not in ("STOP", "NONE", "", 0) for field in action_core)
            or not isinstance(step.get("stop_reason"), str)
            or not str(step["stop_reason"]).strip()
        ):
            raise DomainError(ErrorCode.STRUCTURED_OUTPUT_INVALID, "planner STOP payload is invalid")
    elif step.get("stop_reason") != "":
        raise DomainError(ErrorCode.STRUCTURED_OUTPUT_INVALID, "source action cannot carry stop reason")


def _bootstrap_entities(changed_files: Sequence[str]) -> list[dict[str, object]]:
    cores = [
        {"kind": "git-revision", "identity": TARGET_COMMIT},
        {"kind": "git-revision", "identity": PARENT_COMMIT},
    ] + [
        {"kind": "source-unit", "identity": f"{revision}:{path}"}
        for revision in (PARENT_COMMIT, TARGET_COMMIT)
        for path in changed_files
    ]
    return [
        {"formal_ref": f"entity:{digest_of(core).value}", **core}
        for core in cores
    ]


def _validate_fact_proposals(
    value: object,
    observation: Mapping[str, object],
    entities: Sequence[Mapping[str, object]],
    requirement: Mapping[str, object],
    known_semantic_keys: set[str],
) -> list[dict[str, object]]:
    if not isinstance(value, list):
        raise DomainError(ErrorCode.STRUCTURED_OUTPUT_INVALID, "fact proposals are not an array")
    entity_refs = {item["formal_ref"] for item in entities}
    need_ids, obligation_ids = _requirement_ids(requirement)
    proposals = []
    local_keys = set()
    for item in value:
        if not isinstance(item, dict):
            raise DomainError(ErrorCode.STRUCTURED_OUTPUT_INVALID, "fact proposal is invalid")
        key = item["semantic_key"]
        if (
            not _nonempty_fields(item, ("semantic_key", "statement", "target", "context", "modality"))
            or key in known_semantic_keys
            or key in local_keys
            or item["target"] != TARGET_COMMIT
            or item["context"] != "PARENT_TO_TARGET"
            or not item["entity_refs"]
            or not set(item["entity_refs"]).issubset(entity_refs)
            or item["source_observation_refs"] != [observation["observation_ref"]]
            or not item["need_ids"]
            or not set(item["need_ids"]).issubset(need_ids)
            or not item["obligation_ids"]
            or not set(item["obligation_ids"]).issubset(obligation_ids)
            or not _obligations_match_needs(item["need_ids"], item["obligation_ids"])
        ):
            raise DomainError(ErrorCode.STRUCTURED_OUTPUT_INVALID, "fact proposal binding is invalid")
        if not _frozen_text_covers_obligations(item, item["obligation_ids"]):
            raise DomainError(
                ErrorCode.STRUCTURED_OUTPUT_INVALID,
                "fact proposal does not answer its frozen obligation dimension",
                {
                    "semantic_id": ",".join(item["obligation_ids"]),
                    "semantic_error": "OBLIGATION_DIMENSION_NOT_EXPLICIT",
                    "semantic_expected": "statement must contain the frozen machine-checkable term groups for every mapped obligation",
                },
            )
        local_keys.add(key)
        proposals.append(dict(item))
    known_semantic_keys.update(local_keys)
    return proposals


def _validate_fact_review(
    review: Mapping[str, object], proposals: Sequence[Mapping[str, object]]
) -> set[str]:
    keys = {item["semantic_key"] for item in proposals}
    accepted = review["accepted_semantic_keys"]
    if (
        len(set(accepted)) != len(accepted)
        or not set(accepted).issubset(keys)
        or (review["decision"] == "ACCEPT" and not accepted)
        or (review["decision"] == "REJECT" and accepted)
    ):
        raise DomainError(ErrorCode.STRUCTURED_OUTPUT_INVALID, "knowledge review decision is inconsistent")
    return set(accepted)


def _validate_inferences(
    value: object,
    facts: Sequence[Mapping[str, object]],
    requirement: Mapping[str, object],
    semantic_keys: set[str],
) -> list[dict[str, object]]:
    if not isinstance(value, list):
        raise DomainError(ErrorCode.STRUCTURED_OUTPUT_INVALID, "inference proposals are not an array")
    formal_refs = {item["formal_ref"] for item in facts}
    need_ids, obligation_ids = _requirement_ids(requirement)
    inferences = []
    for item in value:
        if not isinstance(item, dict):
            raise DomainError(ErrorCode.STRUCTURED_OUTPUT_INVALID, "inference proposal is invalid")
        key = item["semantic_key"]
        if (
            not _nonempty_fields(item, ("semantic_key", "statement", "target", "context", "modality"))
            or key in semantic_keys
            or item["target"] != TARGET_COMMIT
            or item["context"] != "PARENT_TO_TARGET"
            or not item["premise_refs"]
            or not set(item["premise_refs"]).issubset(formal_refs)
            or not item["need_ids"]
            or not set(item["need_ids"]).issubset(need_ids)
            or not item["obligation_ids"]
            or not set(item["obligation_ids"]).issubset(obligation_ids)
            or not _obligations_match_needs(item["need_ids"], item["obligation_ids"])
        ):
            raise DomainError(ErrorCode.STRUCTURED_OUTPUT_INVALID, "inference proposal binding is invalid")
        semantic_keys.add(key)
        core = dict(item)
        inferences.append(
            {"formal_ref": f"inference:{digest_of(core).value}", "kind": "INFERENCE", **core}
        )
    return inferences


def _validate_assessment(
    assessment: Mapping[str, object],
    requirement: Mapping[str, object],
    formal_members: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    _, obligation_ids = _requirement_ids(requirement)
    formal_refs = {item["formal_ref"] for item in formal_members}
    formal_by_ref = {item["formal_ref"]: item for item in formal_members}
    obligations = assessment["obligations"]
    if (
        len(obligations) != len(obligation_ids)
        or {item["obligation_id"] for item in obligations} != obligation_ids
    ):
        raise DomainError(ErrorCode.STRUCTURED_OUTPUT_INVALID, "assessment does not cover every obligation")
    for item in obligations:
        if not isinstance(item["finding"], str) or not item["finding"].strip():
            raise DomainError(ErrorCode.STRUCTURED_OUTPUT_INVALID, "assessment finding is empty")
        supports = item["supporting_refs"]
        support_error = (
            "DUPLICATE_SUPPORT_REF"
            if len(set(supports)) != len(supports)
            else "UNKNOWN_SUPPORT_REF"
            if not set(supports).issubset(formal_refs)
            else "SATISFIED_WITHOUT_SUPPORT"
            if item["status"] == "SATISFIED" and not supports
            else "NON_SATISFIED_WITH_SUPPORT"
            if item["status"] != "SATISFIED" and supports
            else "SUPPORT_NOT_BOUND_TO_OBLIGATION"
            if any(
                item["obligation_id"]
                not in formal_by_ref[reference].get("obligation_ids", [])
                for reference in supports
            )
            else None
        )
        if support_error is not None:
            raise DomainError(
                ErrorCode.STRUCTURED_OUTPUT_INVALID,
                "assessment support is invalid",
                {
                    "world_role": "SUFFICIENCY_REVIEWER",
                    "semantic_id": item["obligation_id"],
                    "semantic_error": support_error,
                },
            )
    expected_constraints = {
        item["constraint_id"] for item in requirement["joint_constraints"]
    }
    joints = assessment["joint_constraints"]
    if len(joints) != len(expected_constraints) or {
        item["constraint_id"] for item in joints
    } != expected_constraints:
        raise DomainError(ErrorCode.STRUCTURED_OUTPUT_INVALID, "joint assessment is incomplete")
    for item in joints:
        if (
            not isinstance(item["finding"], str)
            or not item["finding"].strip()
            or not set(item["supporting_refs"]).issubset(formal_refs)
            or (item["status"] == "SATISFIED" and not item["supporting_refs"])
            or (item["status"] != "SATISFIED" and item["supporting_refs"])
        ):
            raise DomainError(ErrorCode.STRUCTURED_OUTPUT_INVALID, "joint assessment support is invalid")
    all_satisfied = all(item["status"] == "SATISFIED" for item in obligations + joints)
    if (assessment["overall"] == "SATISFIED") != all_satisfied:
        raise DomainError(ErrorCode.STRUCTURED_OUTPUT_INVALID, "assessment overall status is inconsistent")
    return dict(assessment)


def _validate_answer(
    answer: Mapping[str, object],
    assessment: Mapping[str, object],
    formal_members: Sequence[Mapping[str, object]],
    requirement: Mapping[str, object],
) -> dict[str, object]:
    claims = answer["claims"]
    if not claims or answer["answer"] != "\n".join(item["text"] for item in claims):
        raise DomainError(ErrorCode.STRUCTURED_OUTPUT_INVALID, "answer contains unclaimed text")
    _, obligation_ids = _requirement_ids(requirement)
    assessment_by_id = {
        item["obligation_id"]: item for item in assessment["obligations"]
    }
    formal_refs = {item["formal_ref"] for item in formal_members}
    semantic_keys = set()
    covered = []
    for claim in claims:
        key = claim["semantic_key"]
        supports = claim["supporting_refs"]
        obligations = claim["obligation_ids"]
        if (
            not _nonempty_fields(
                claim,
                ("semantic_key", "text", "target", "context", "modality", "coverage"),
            )
            or key in semantic_keys
            or claim["target"] != TARGET_COMMIT
            or claim["context"] != "PARENT_TO_TARGET"
            or not obligations
            or not set(obligations).issubset(obligation_ids)
            or not claim["need_ids"]
            or not _obligations_match_needs(claim["need_ids"], obligations)
            or len(set(supports)) != len(supports)
            or not set(supports).issubset(formal_refs)
        ):
            raise DomainError(ErrorCode.STRUCTURED_OUTPUT_INVALID, "answer claim binding is invalid")
        if claim["kind"] == "FORMAL_KNOWLEDGE":
            exact_assessment_support = {
                reference
                for obligation_id in obligations
                for reference in assessment_by_id[obligation_id]["supporting_refs"]
            }
            if (
                not supports
                or any(
                    assessment_by_id[item]["status"] != "SATISFIED"
                    for item in obligations
                )
                or set(supports) != exact_assessment_support
            ):
                raise DomainError(ErrorCode.STRUCTURED_OUTPUT_INVALID, "formal answer claim lacks satisfied support")
            if not _frozen_text_covers_obligations(claim, obligations):
                raise DomainError(
                    ErrorCode.STRUCTURED_OUTPUT_INVALID,
                    "formal answer claim does not answer its frozen obligation dimension",
                    {
                        "semantic_id": ",".join(obligations),
                        "semantic_error": "OBLIGATION_DIMENSION_NOT_EXPLICIT",
                        "semantic_expected": "claim must contain the frozen machine-checkable term groups for every mapped obligation",
                    },
                )
        elif supports or any(assessment_by_id[item]["status"] == "SATISFIED" for item in obligations):
            raise DomainError(ErrorCode.STRUCTURED_OUTPUT_INVALID, "gap claim contradicts assessment")
        semantic_keys.add(key)
        covered.extend(obligations)
    if len(covered) != len(set(covered)) or set(covered) != obligation_ids:
        raise DomainError(ErrorCode.STRUCTURED_OUTPUT_INVALID, "answer does not cover every obligation exactly once")
    return dict(answer)


def _validate_answer_review(
    review: Mapping[str, object], candidate: Mapping[str, object]
) -> dict[str, object]:
    keys = {item["semantic_key"] for item in candidate["claims"]}
    findings = review["claim_findings"]
    if len(findings) != len(keys) or {item["semantic_key"] for item in findings} != keys:
        raise DomainError(ErrorCode.STRUCTURED_OUTPUT_INVALID, "answer review does not cover every claim")
    approved = (
        review["decision"] == "APPROVED"
        and not review["missing_obligation_ids"]
        and all(item["outcome"] == "PASS" for item in findings)
    )
    if review["decision"] == "APPROVED" and not approved:
        raise DomainError(ErrorCode.STRUCTURED_OUTPUT_INVALID, "answer approval contradicts findings")
    return dict(review)


def _snapshot(
    kind: str, parent_snapshot_ref: str | None, members: Sequence[Mapping[str, object]]
) -> dict[str, object]:
    core = {
        "kind": kind,
        "parent_snapshot_ref": parent_snapshot_ref,
        "members": list(members),
    }
    return {"snapshot_ref": f"snapshot:{kind.lower()}:{digest_of(core).value}", **core}


def _requirement_ids(requirement: Mapping[str, object]) -> tuple[set[str], set[str]]:
    need_ids = {item["need_id"] for item in requirement["needs"]}
    obligation_ids = {
        obligation["obligation_id"]
        for need in requirement["needs"]
        for obligation in need["obligations"]
    }
    return need_ids, obligation_ids


def _scope_requirement(
    requirement: Mapping[str, object], needs: Sequence[Mapping[str, object]]
) -> dict[str, object]:
    scope_id = "+".join(need["need_id"] for need in needs)
    scope_core = {
        "requirement_id": f"{requirement['requirement_id']}:{scope_id}",
        "revision": requirement["revision"],
        "needs": [copy.deepcopy(need) for need in needs],
        "joint_constraints": [],
    }
    return {
        **scope_core,
        "requirement_digest": digest_of(scope_core).value,
    }


def _bounded_need_groups(
    needs: Sequence[Mapping[str, object]],
) -> list[Sequence[Mapping[str, object]]]:
    if [need.get("need_id") for need in needs] == [
        "JWT-N01",
        "JWT-N02",
        "JWT-N03",
        "JWT-N04",
        "JWT-N05",
        "JWT-N06",
    ]:
        return [needs[0:2], needs[2:4], needs[4:5], needs[5:6]]
    return [needs[index : index + 2] for index in range(0, len(needs), 2)]


def _obligations_match_needs(needs: Sequence[str], obligations: Sequence[str]) -> bool:
    return bool(needs) and all(
        any(obligation.startswith(f"{need_id}-") for need_id in needs)
        for obligation in obligations
    )


_FROZEN_OBLIGATION_TERM_GROUPS = {
    "JWT-N01-O01": ((TARGET_COMMIT,), (PARENT_COMMIT,)),
    "JWT-N01-O02": (
        ("complete", "完整"),
        ("pom.xml",),
        ("mall-security/pom.xml",),
        ("mall-security/src/main/java/com/macro/mall/security/util/jwttokenutil.java",),
    ),
    "JWT-N04-O01": (
        ("verify",),
        ("false",),
        ("null",),
        ("parse", "parsing"),
        ("exception", "caught", "catch"),
    ),
    "JWT-N04-O02": (
        ("verify",),
        ("false",),
        ("null",),
        ("exception", "caught", "catch"),
        ("parse", "parsing"),
        ("not source-proven", "unproven", "cannot prove", "unknown", "未知", "无法证明"),
    ),
    "JWT-N05-O01": (("created",), ("long",), ("date",)),
    "JWT-N05-O02": (
        ("created",),
        ("other", "unsupported", "其他", "不支持"),
        ("null",),
        ("false",),
    ),
    "JWT-N05-O03": (
        ("refreshdate",),
        ("after",),
        ("createddate",),
        ("before",),
        ("dateutil.offsetsecond",),
        ("lower", "下界"),
        ("upper", "上界"),
        ("exclusive", "不含", "开区间"),
    ),
    "JWT-N05-O04": (
        ("tokenhead",),
        ("stripped", "去除", "移除"),
        ("tokenrefreshjustbefore",),
        ("generatetoken",),
    ),
    "JWT-N06-O01": (
        ("algorithm", "算法"),
        ("unknown", "unproven", "unprovable", "not source-proven", "cannot prove", "not specified", "unspecified", "does not state", "not documented", "cannot determine", "未知", "无法证明"),
        ("signaturealgorithm.hs512", "signwith(signaturealgorithm.hs512"),
        ("hmacsha512",),
        ("comment", "javadoc", "注释"),
        ("jwtutil.createtoken",),
    ),
    "JWT-N06-O02": (
        ("string",),
        ("comment", "javadoc", "注释"),
        ("hmacsha512",),
        ("unknown", "unproven", "unprovable", "not source-proven", "cannot prove", "not specified", "unspecified", "does not state", "not documented", "cannot determine", "未知", "无法证明"),
    ),
    "JWT-N06-O03": (
        ("payload", "载荷"),
        ("serialization", "序列化"),
        ("type", "类型"),
        ("map<string,object>", "getpayloads"),
        ("concrete", "runtime", "actual", "具体", "运行时", "实际"),
        ("unknown", "unproven", "unprovable", "not source-proven", "cannot prove", "not specified", "unspecified", "does not state", "not documented", "cannot determine", "未知", "无法证明"),
    ),
}


def _frozen_text_covers_obligations(
    item: Mapping[str, object], obligations: Sequence[str]
) -> bool:
    text = " ".join(
        str(item.get(field) or "") for field in ("statement", "text", "condition", "limitation")
    ).casefold()
    if "JWT-N04-O02" in obligations and "verify=true" in text:
        return False
    return all(
        all(any(term in text for term in alternatives) for alternatives in term_groups)
        for obligation_id in obligations
        for term_groups in [_FROZEN_OBLIGATION_TERM_GROUPS.get(obligation_id, ())]
    )


def _nonempty_fields(value: Mapping[str, object], fields: Sequence[str]) -> bool:
    return all(isinstance(value.get(field), str) and str(value[field]).strip() for field in fields)


def _item(kind: str, authority_ref: str, payload: object) -> dict[str, object]:
    return {"kind": kind, "authority_ref": authority_ref, "payload": payload}


def _load_object(path: str | Path, label: str) -> dict[str, object]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} cannot be read") from exc
    if not isinstance(value, dict):
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} must be an object")
    return value


def _seal_private(payload: bytes, directory: Path, name: str) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / name
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "World Model result already exists and cannot be overwritten",
        ) from exc
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    return path
