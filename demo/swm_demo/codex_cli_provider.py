from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import subprocess
import tempfile
from typing import Mapping


class CodexCliProviderError(RuntimeError):
    """A fail-closed error at the validation-only Codex CLI boundary."""


@dataclass(frozen=True)
class _CapabilityContract:
    instruction: str
    output_schema: dict[str, object]


def _text(*, nullable: bool = False) -> dict[str, object]:
    if nullable:
        return {"type": ["string", "null"]}
    return {"type": "string", "minLength": 1}


def _integer(*, minimum: int = 0, maximum: int | None = None) -> dict[str, object]:
    schema: dict[str, object] = {"type": "integer", "minimum": minimum}
    if maximum is not None:
        schema["maximum"] = maximum
    return schema


def _array(
    items: dict[str, object],
    *,
    minimum: int = 0,
    maximum: int | None = None,
    unique: bool = False,
) -> dict[str, object]:
    schema: dict[str, object] = {
        "type": "array",
        "items": items,
        "minItems": minimum,
    }
    if maximum is not None:
        schema["maxItems"] = maximum
    if unique:
        schema["uniqueItems"] = True
    return schema


def _object(properties: Mapping[str, dict[str, object]]) -> dict[str, object]:
    """Build an object accepted by strict Structured Outputs.

    Every declared property is required. Optional values are represented as a
    required nullable field so the object shape never changes silently.
    """

    return {
        "type": "object",
        "properties": dict(properties),
        "required": list(properties),
        "additionalProperties": False,
    }


_TEXT_ARRAY = _array(_text(), unique=True)

_ROUTE_SCHEMA = _object(
    {
        "use_case": {
            "type": "string",
            "enum": [
                "history-view",
                "business-view",
                "behavior-view",
                "endpoint-structure",
                "structure-view",
            ],
        },
        "endpoint": _text(nullable=True),
    }
)

_REQUIREMENT_SCHEMA = _object(
    {
        "needs": _array(
            _object(
                {
                    "need_id": _text(),
                    "question": _text(),
                    "sufficiency_criterion": _text(),
                }
            ),
            minimum=1,
            unique=True,
        )
    }
)

_SEARCH_ARGUMENTS_SCHEMA = _object(
    {
        "kind": {"type": "string", "enum": ["ENTITY", "INFERENCE"]},
        "query": _text(),
        "match_mode": {"type": "string", "enum": ["EXACT", "CONTAINS"]},
        "type_name": _text(nullable=True),
        "limit": _integer(minimum=1, maximum=100),
        "cursor": _integer(minimum=0),
    }
)
_NEIGHBORHOOD_ARGUMENTS_SCHEMA = _object(
    {
        "entity_ids": _array(_text(), minimum=1, maximum=20, unique=True),
        "direction": {
            "type": "string",
            "enum": ["OUTGOING", "INCOMING", "BOTH"],
        },
        "predicates": _array(_text(), maximum=20, unique=True),
        "limit": _integer(minimum=1, maximum=200),
        "cursor": _integer(minimum=0),
    }
)
_EXPLAIN_ARGUMENTS_SCHEMA = _object(
    {
        "kind": {"type": "string", "enum": ["FACT", "INFERENCE"]},
        "knowledge_ids": _array(
            _text(), minimum=1, maximum=50, unique=True
        ),
    }
)
_STOP_ARGUMENTS_SCHEMA = _object({})
_FORMAL_STEP_SCHEMA = _object(
    {
        "action": {
            "type": "string",
            "enum": ["SEARCH", "NEIGHBORHOOD", "EXPLAIN", "STOP"],
        },
        "arguments": {
            "anyOf": [
                _SEARCH_ARGUMENTS_SCHEMA,
                _NEIGHBORHOOD_ARGUMENTS_SCHEMA,
                _EXPLAIN_ARGUMENTS_SCHEMA,
                _STOP_ARGUMENTS_SCHEMA,
            ]
        },
    }
)
_CODEX_FORMAL_STEP_SCHEMA = _object(
    {
        "selection": {
            "anyOf": [
                _object(
                    {
                        "action": {"type": "string", "enum": ["SEARCH"]},
                        "arguments": _SEARCH_ARGUMENTS_SCHEMA,
                    }
                ),
                _object(
                    {
                        "action": {
                            "type": "string",
                            "enum": ["NEIGHBORHOOD"],
                        },
                        "arguments": _NEIGHBORHOOD_ARGUMENTS_SCHEMA,
                    }
                ),
                _object(
                    {
                        "action": {"type": "string", "enum": ["EXPLAIN"]},
                        "arguments": _EXPLAIN_ARGUMENTS_SCHEMA,
                    }
                ),
                _object(
                    {
                        "action": {"type": "string", "enum": ["STOP"]},
                        "arguments": _STOP_ARGUMENTS_SCHEMA,
                    }
                ),
            ]
        }
    }
)

_REFERENCE_SCHEMA = _object(
    {
        "kind": {"type": "string", "enum": ["FACT", "INFERENCE"]},
        "reference_id": _text(),
    }
)
_SUFFICIENCY_SCHEMA = _object(
    {
        "items": _array(
            _object(
                {
                    "need_id": _text(),
                    "status": {
                        "type": "string",
                        "enum": ["SATISFIED", "GAP"],
                    },
                    "references": _array(_REFERENCE_SCHEMA, unique=True),
                    "rationale": {"type": "string"},
                }
            ),
            unique=True,
        )
    }
)

_COMPARISON_SCHEMA = _object(
    {"base_revision": _text(), "target_revision": _text()}
)
_ARTIFACT_REQUEST_SCHEMA = _object(
    {
        "build_profile": _text(),
        "include_globs": _TEXT_ARRAY,
        "git_commit_ids": _TEXT_ARRAY,
        "derive_java_ast": {"type": "boolean"},
        "revision": _text(nullable=True),
        "commit_revisions": _TEXT_ARRAY,
        "comparisons": _array(_COMPARISON_SCHEMA, unique=True),
    }
)
_METHOD_TARGET_SCHEMA = _array(
    _array(_text(), minimum=2, maximum=2), unique=True
)
_KNOWLEDGE_TARGET_SCHEMA = _object(
    {
        "behavior_methods": _METHOD_TARGET_SCHEMA,
        "business_constraint_methods": _METHOD_TARGET_SCHEMA,
        "capability_modules": _TEXT_ARRAY,
        "history_commits": _TEXT_ARRAY,
        "required_inference_types": _TEXT_ARRAY,
        "premise_fact_ids": _TEXT_ARRAY,
        "premise_inference_ids": _TEXT_ARRAY,
    }
)
_BUILD_INTENT_SCHEMA = _object(
    {
        "target_revision": _text(),
        "artifact_request": _ARTIFACT_REQUEST_SCHEMA,
        "knowledge_target": _KNOWLEDGE_TARGET_SCHEMA,
    }
)

_ENTITY_PROPOSAL_SCHEMA = _object(
    {"key": _text(), "entity_type": _text(), "name": _text()}
)
_EVIDENCE_PROPOSAL_SCHEMA = _object(
    {
        "key": _text(),
        "artifact_id": _text(),
        "line_start": _integer(minimum=1),
        "line_end": _integer(minimum=1),
    }
)
_FACT_PROPOSAL_SCHEMA = _object(
    {
        "key": _text(),
        "subject": _text(),
        "predicate": _text(),
        "object": _text(),
        "evidence": _array(_text(), minimum=1, unique=True),
        "proposition": _text(),
    }
)
_INFERENCE_PROPOSAL_SCHEMA = _object(
    {
        "key": _text(),
        "inference_type": _text(),
        "statement": _text(),
        "premise_fact_ids": _array(_text(), minimum=1, unique=True),
        "premise_inference_ids": _array(_text(), unique=True),
    }
)
_CANDIDATE_PROPOSAL_SCHEMA = _object(
    {
        "schema_version": {
            "type": "string",
            "enum": ["candidate-proposal.v2"],
        },
        "entities": _array(_ENTITY_PROPOSAL_SCHEMA, unique=True),
        "evidence": _array(_EVIDENCE_PROPOSAL_SCHEMA, unique=True),
        "fact_candidates": _array(_FACT_PROPOSAL_SCHEMA, unique=True),
        "inference_candidates": _array(
            _INFERENCE_PROPOSAL_SCHEMA, unique=True
        ),
        "covered_need_ids": _TEXT_ARRAY,
        "unresolved_need_ids": _TEXT_ARRAY,
    }
)

_DRAFT_ANSWER_SCHEMA = _object({"answer": {"type": "string"}})
_REVIEW_ANSWER_SCHEMA = _object(
    {
        "decision": {"type": "string", "enum": ["PASS", "REJECT"]},
        "unsupported_claims": _array(_text(), unique=True),
    }
)

_NO_EXTERNAL_ACTIONS = (
    "Use only the supplied payload. Do not invoke tools, shell commands, file "
    "or filesystem operations, web or network access, MCP, or any external "
    "resource. Return exactly one JSON object matching the output schema, with "
    "no Markdown, commentary, or surrounding text."
)


def _instruction(capability: str, task: str) -> str:
    return f"Capability: {capability}. {_NO_EXTERNAL_ACTIONS} Task: {task}"


_CAPABILITY_CONTRACTS: dict[str, _CapabilityContract] = {
    "route-task": _CapabilityContract(
        _instruction(
            "route-task",
            "Select exactly one registered use_case from the request. Set endpoint "
            "to the explicit HTTP method and path only for endpoint-structure; "
            "otherwise set endpoint to null. Do not answer the request.",
        ),
        _ROUTE_SCHEMA,
    ),
    "form-knowledge-requirement": _CapabilityContract(
        _instruction(
            "form-knowledge-requirement",
            "Turn the request into one or more non-overlapping knowledge needs. "
            "Each sufficiency criterion must be concrete enough to verify against "
            "formal Facts or Inferences and must be necessary and proportional to "
            "the user's wording. Do not make modules, per-step inputs/outputs, all "
            "failure branches, rollback, compensation, implementation depth, or "
            "other details mandatory unless the user explicitly requested them or "
            "they are essential to avoid an ambiguous answer. Do not claim that "
            "knowledge already exists and do not add optional follow-up topics as "
            "mandatory needs.",
        ),
        _REQUIREMENT_SCHEMA,
    ),
    "plan-formal-knowledge-step": _CapabilityContract(
        _instruction(
            "plan-formal-knowledge-step",
            "Plan one application-owned formal-knowledge action from the frozen "
            "context and tool_trace. SEARCH finds an Entity or Inference, "
            "NEIGHBORHOOD follows Entity relations, EXPLAIN resolves a Fact or "
            "Inference, and STOP ends the loop. Supply every field required by the "
            "selected argument shape; never EXPLAIN an empty ID list. If the latest "
            "trace item is REJECTED, repair that contract error. This is a plan, "
            "not permission to execute it. When a requirement names an exact "
            "immutable identifier such as a commit or version and both its exact "
            "and abbreviated searches are empty, STOP so Assessment can report a "
            "Gap; do not substitute entities or changes from another identifier, "
            "and do not exhaust the budget with unrelated keyword searches.",
        ),
        _FORMAL_STEP_SCHEMA,
    ),
    "assess-knowledge-sufficiency": _CapabilityContract(
        _instruction(
            "assess-knowledge-sufficiency",
            "Assess every requirement need exactly once using only formal_claims. "
            "SATISFIED must cite one or more references present in formal_claims. "
            "Use GAP when the criterion is not established and explain why in "
            "rationale. Never invent a reference.",
        ),
        _SUFFICIENCY_SCHEMA,
    ),
    "derive-build-intent": _CapabilityContract(
        _instruction(
            "derive-build-intent",
            "For the stated gaps, request the smallest useful source collection and "
            "declare semantic build targets. Preserve the supplied target revision. "
            "This output asks for observations; it must not contain source-derived "
            "Facts, Inferences, or an answer. For a requested Git commit, "
            "git_commit_ids collects its metadata and patch; prefer that bounded "
            "request and narrow file globs over all-source or **/*.java collection. "
            "Use commit_revisions only for metadata without a patch, and explicit "
            "comparisons only when both revisions are known. The current Demo "
            "build target supports only BEHAVIOR_FLOW, BUSINESS_CAPABILITY, "
            "BUSINESS_CONSTRAINT, and HISTORY_IMPACT. For a commit investigation, "
            "set history_commits to the requested commit and required_inference_types "
            "to HISTORY_IMPACT; leave behavior_methods, "
            "business_constraint_methods, and capability_modules empty unless their "
            "exact supported identifiers are already known. The current Demo legacy "
            "method-target shape, when used, is exactly "
            "[method_selector, human_readable_label]; the selector is a legacy "
            "builder-specific match string, not a canonical identity or class/method pair.",
        ),
        _BUILD_INTENT_SCHEMA,
    ),
    "propose-knowledge-candidates": _CapabilityContract(
        _instruction(
            "propose-knowledge-candidates",
            "Use source_artifacts to propose local-keyed Entities, one-Artifact "
            "Evidence locators, and evidence-backed Fact candidates. Inference "
            "candidates may use only the exact published formal_premises frozen in "
            "the Build Target; reference them by premise_fact_ids and "
            "premise_inference_ids. A Fact Candidate from this proposal can never be "
            "an Inference premise. Artifact text is supplied as content_lines with "
            "explicit line_number and text; locators must use those numbers and line "
            "ranges must exactly support the observation. For a direct Fact, use a "
            "proposition literally present in its Evidence; put interpretation or "
            "cross-line semantic conclusions in an Inference supported by Facts. "
            "Every Fact subject and object must be the local key of an Entity "
            "declared in the same proposal; represent literal values as Entities "
            "when they participate in a Fact. When previous_proposal and "
            "validation_feedback are present, return a complete corrected replacement "
            "proposal rather than a patch, and repair the reported contract error. "
            "Do not invent Artifact IDs, source text, revisions, or durable IDs. "
            "covered_need_ids and unresolved_need_ids must exactly partition the "
            "supplied gap_need_ids.",
        ),
        _CANDIDATE_PROPOSAL_SCHEMA,
    ),
    "draft-answer": _CapabilityContract(
        _instruction(
            "draft-answer",
            "Render the supplied claims in their existing order, joined by a single "
            "newline. Preserve their wording exactly and add no unsupported claim.",
        ),
        _DRAFT_ANSWER_SCHEMA,
    ),
    "review-answer": _CapabilityContract(
        _instruction(
            "review-answer",
            "Independently compare candidate_claims with the request, requirement, "
            "formal_propositions, and authoritative_claims. PASS only when every "
            "candidate claim is directly supported; otherwise REJECT and list the "
            "exact unsupported candidate claim strings.",
        ),
        _REVIEW_ANSWER_SCHEMA,
    ),
}


_LIFECYCLE_EVENTS = frozenset({"thread.started", "turn.started", "turn.completed"})
_ITEM_EVENTS = frozenset({"item.started", "item.updated", "item.completed"})
_INERT_ITEM_TYPES = frozenset({"reasoning"})
_FORBIDDEN_TYPE_MARKERS = (
    "tool",
    "command",
    "file",
    "web",
    "shell",
    "exec",
    "mcp",
    "browser",
    "function",
)

# Codex Structured Outputs intentionally supports only a JSON Schema subset.
# These validation keywords remain in the platform-owned contract and are
# enforced after parsing, but must not be sent to the provider API.
_PROVIDER_UNSUPPORTED_SCHEMA_KEYS = frozenset(
    {
        "maxItems",
        "maximum",
        "minItems",
        "minLength",
        "minimum",
        "uniqueItems",
    }
)


def _codex_output_schema(value: object) -> object:
    if isinstance(value, dict):
        return {
            key: _codex_output_schema(item)
            for key, item in value.items()
            if key not in _PROVIDER_UNSUPPORTED_SCHEMA_KEYS
        }
    if isinstance(value, list):
        return [_codex_output_schema(item) for item in value]
    return value


def _provider_output_schema(
    capability: str, contract: _CapabilityContract
) -> dict[str, object]:
    schema = (
        _CODEX_FORMAL_STEP_SCHEMA
        if capability == "plan-formal-knowledge-step"
        else contract.output_schema
    )
    portable = _codex_output_schema(schema)
    if not isinstance(portable, dict):
        raise CodexCliProviderError("Codex output schema is not an object")
    return portable


def _strict_json_loads(value: str) -> object:
    def reject_constant(token: str) -> object:
        raise ValueError(f"non-JSON numeric constant: {token}")

    def reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
        output: dict[str, object] = {}
        for key, item in pairs:
            if key in output:
                raise ValueError(f"duplicate object key: {key}")
            output[key] = item
        return output

    return json.loads(
        value,
        parse_constant=reject_constant,
        object_pairs_hook=reject_duplicate_keys,
    )


def _matches_type(value: object, expected: str) -> bool:
    if expected == "null":
        return value is None
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    return False


def _validate_schema(value: object, schema: Mapping[str, object], path: str = "$") -> None:
    alternatives = schema.get("anyOf")
    if alternatives is not None:
        errors: list[str] = []
        if not isinstance(alternatives, list):
            raise CodexCliProviderError(f"invalid adapter schema at {path}.anyOf")
        for alternative in alternatives:
            try:
                if not isinstance(alternative, dict):
                    raise CodexCliProviderError("invalid schema alternative")
                _validate_schema(value, alternative, path)
                break
            except CodexCliProviderError as error:
                errors.append(str(error))
        else:
            raise CodexCliProviderError(
                f"model output does not match any allowed shape at {path}: "
                + "; ".join(errors)
            )

    if "const" in schema and value != schema["const"]:
        raise CodexCliProviderError(f"model output has an invalid constant at {path}")
    enum = schema.get("enum")
    if isinstance(enum, list) and not any(value == candidate for candidate in enum):
        raise CodexCliProviderError(f"model output has an invalid value at {path}")

    expected_type = schema.get("type")
    if expected_type is not None:
        types = expected_type if isinstance(expected_type, list) else [expected_type]
        if not all(isinstance(item, str) for item in types) or not any(
            _matches_type(value, item) for item in types
        ):
            raise CodexCliProviderError(f"model output has an invalid type at {path}")

    if isinstance(value, dict) and expected_type == "object":
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        if not isinstance(properties, dict) or not isinstance(required, list):
            raise CodexCliProviderError(f"invalid adapter object schema at {path}")
        missing = [item for item in required if item not in value]
        if missing:
            raise CodexCliProviderError(
                f"model output is missing required fields at {path}: {missing}"
            )
        if schema.get("additionalProperties") is False:
            unknown = sorted(set(value) - set(properties))
            if unknown:
                raise CodexCliProviderError(
                    f"model output has unknown fields at {path}: {unknown}"
                )
        for key, item in value.items():
            property_schema = properties.get(key)
            if isinstance(property_schema, dict):
                _validate_schema(item, property_schema, f"{path}.{key}")

    if isinstance(value, list) and expected_type == "array":
        minimum = schema.get("minItems")
        maximum = schema.get("maxItems")
        if isinstance(minimum, int) and len(value) < minimum:
            raise CodexCliProviderError(f"model output array is too short at {path}")
        if isinstance(maximum, int) and len(value) > maximum:
            raise CodexCliProviderError(f"model output array is too long at {path}")
        if schema.get("uniqueItems") is True:
            canonical = [
                json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
                for item in value
            ]
            if len(set(canonical)) != len(canonical):
                raise CodexCliProviderError(
                    f"model output array contains duplicates at {path}"
                )
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(value):
                _validate_schema(item, item_schema, f"{path}[{index}]")

    if isinstance(value, str):
        minimum_length = schema.get("minLength")
        if isinstance(minimum_length, int) and len(value) < minimum_length:
            raise CodexCliProviderError(f"model output string is too short at {path}")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        minimum_value = schema.get("minimum")
        maximum_value = schema.get("maximum")
        if isinstance(minimum_value, (int, float)) and value < minimum_value:
            raise CodexCliProviderError(f"model output number is too small at {path}")
        if isinstance(maximum_value, (int, float)) and value > maximum_value:
            raise CodexCliProviderError(f"model output number is too large at {path}")


def _parse_jsonl_output(stdout: str) -> dict[str, object]:
    messages: list[str] = []
    for line_number, line in enumerate(stdout.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            event = _strict_json_loads(line)
        except (TypeError, ValueError, json.JSONDecodeError) as error:
            raise CodexCliProviderError(
                f"Codex CLI emitted invalid JSONL at line {line_number}"
            ) from error
        if not isinstance(event, dict):
            raise CodexCliProviderError(
                f"Codex CLI JSONL event is not an object at line {line_number}"
            )
        event_type = event.get("type")
        if not isinstance(event_type, str):
            raise CodexCliProviderError(
                f"Codex CLI JSONL event has no type at line {line_number}"
            )
        if event_type in _LIFECYCLE_EVENTS:
            continue
        if event_type in {"error", "turn.failed"}:
            raise CodexCliProviderError(f"Codex CLI reported {event_type}")
        if event_type not in _ITEM_EVENTS:
            marker = next(
                (item for item in _FORBIDDEN_TYPE_MARKERS if item in event_type.lower()),
                None,
            )
            description = "forbidden action" if marker else "unexpected event"
            raise CodexCliProviderError(
                f"Codex CLI emitted a {description}: {event_type}"
            )

        item = event.get("item")
        if not isinstance(item, dict) or not isinstance(item.get("type"), str):
            raise CodexCliProviderError(
                f"Codex CLI item event is malformed at line {line_number}"
            )
        item_type = str(item["type"])
        if item_type in _INERT_ITEM_TYPES:
            continue
        if item_type != "agent_message":
            raise CodexCliProviderError(
                f"Codex CLI emitted a forbidden item/action: {item_type}"
            )
        if event_type != "item.completed":
            continue
        text = item.get("text")
        if not isinstance(text, str):
            raise CodexCliProviderError("completed agent_message has no text")
        messages.append(text)

    if len(messages) != 1:
        raise CodexCliProviderError(
            "Codex CLI must emit exactly one completed agent_message; "
            f"received {len(messages)}"
        )
    try:
        output = _strict_json_loads(messages[0])
    except (TypeError, ValueError, json.JSONDecodeError) as error:
        raise CodexCliProviderError(
            "completed agent_message is not exactly one JSON value"
        ) from error
    if not isinstance(output, dict):
        raise CodexCliProviderError(
            "completed agent_message JSON value must be an object"
        )
    return output


class CodexCliProvider:
    """Validation-only, stateless real-model adapter for ``ModelProvider``.

    Every call gets an ephemeral Codex process in a new empty working directory.
    The prompt forbids Codex actions and any observed action event fails the call,
    but the CLI may already have executed that action. This adapter is therefore
    not a no-tools security boundary and is disabled without explicit opt-in.
    """

    provider_name = "codex-cli"

    def __init__(
        self,
        *,
        executable: str = "codex",
        model: str | None = None,
        model_version: str = "validation-adapter-v1",
        timeout_seconds: float = 300.0,
        max_input_characters: int = 1_048_576,
        allow_agent_runtime: bool = False,
    ) -> None:
        if not isinstance(executable, str) or not executable.strip():
            raise ValueError("executable must not be empty")
        if model is not None and (not isinstance(model, str) or not model.strip()):
            raise ValueError("model must be null or a non-empty string")
        if not isinstance(model_version, str) or not model_version.strip():
            raise ValueError("model_version must not be empty")
        if isinstance(timeout_seconds, bool) or not isinstance(
            timeout_seconds, (int, float)
        ) or timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if (
            isinstance(max_input_characters, bool)
            or not isinstance(max_input_characters, int)
            or max_input_characters < 1
        ):
            raise ValueError("max_input_characters must be a positive integer")
        self.executable = executable
        self.model = model
        self.model_name = model or "codex-configured-default"
        self.model_version = model_version
        self.timeout_seconds = float(timeout_seconds)
        self.max_input_characters = max_input_characters
        if not isinstance(allow_agent_runtime, bool):
            raise TypeError("allow_agent_runtime must be a boolean")
        self.allow_agent_runtime = allow_agent_runtime

    def invoke(
        self, capability: str, payload: dict[str, object]
    ) -> dict[str, object]:
        if not self.allow_agent_runtime:
            raise CodexCliProviderError(
                "CODEX_AGENT_RUNTIME_NOT_ISOLATED: Codex CLI can attempt tool "
                "actions before JSONL rejection. Use a mechanically no-tools "
                "provider, or explicitly acknowledge this validation-only risk."
            )
        contract = _CAPABILITY_CONTRACTS.get(capability)
        if contract is None:
            raise ValueError(f"unsupported Codex capability: {capability}")
        if not isinstance(payload, dict):
            raise TypeError("payload must be an object")
        try:
            prompt = json.dumps(
                {
                    "capability_contract": contract.instruction,
                    "payload": payload,
                },
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            )
        except (TypeError, ValueError) as error:
            raise CodexCliProviderError("payload is not strict JSON") from error
        if len(prompt) > self.max_input_characters:
            raise CodexCliProviderError(
                "MODEL_INPUT_BUDGET_EXCEEDED: serialized capability input has "
                f"{len(prompt)} characters; provider budget is "
                f"{self.max_input_characters}"
            )

        with tempfile.TemporaryDirectory(prefix="swm-codex-cli-") as temporary:
            root = Path(temporary)
            working_directory = root / "empty-workspace"
            working_directory.mkdir()
            schema_path = root / "output-schema.json"
            provider_schema = _provider_output_schema(capability, contract)
            schema_path.write_text(
                json.dumps(
                    provider_schema,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ),
                encoding="utf-8",
            )
            command = [
                self.executable,
                "exec",
                "--ephemeral",
                "--json",
                "--sandbox",
                "read-only",
                "--skip-git-repo-check",
                "--ignore-user-config",
                "--ignore-rules",
            ]
            if self.model is not None:
                command.extend(["--model", self.model])
            command.extend(["--output-schema", str(schema_path), "-"])
            try:
                completed = subprocess.run(
                    command,
                    cwd=str(working_directory),
                    input=prompt,
                    text=True,
                    capture_output=True,
                    check=False,
                    timeout=self.timeout_seconds,
                )
            except FileNotFoundError as error:
                raise CodexCliProviderError(
                    f"Codex CLI executable was not found: {self.executable}"
                ) from error
            except subprocess.TimeoutExpired as error:
                raise CodexCliProviderError(
                    f"Codex CLI timed out after {self.timeout_seconds:g} seconds"
                ) from error
            except OSError as error:
                raise CodexCliProviderError("Codex CLI could not be started") from error

            if completed.returncode != 0:
                stderr = completed.stderr if isinstance(completed.stderr, str) else ""
                stdout = completed.stdout if isinstance(completed.stdout, str) else ""
                diagnostic = "\n".join(
                    item for item in (stderr[-1500:], stdout[-1500:]) if item.strip()
                )
                detail = " ".join(diagnostic.strip().split())[-2000:]
                suffix = f": {detail}" if detail else ""
                raise CodexCliProviderError(
                    f"Codex CLI exited with status {completed.returncode}{suffix}"
                )
            if not isinstance(completed.stdout, str):
                raise CodexCliProviderError("Codex CLI stdout is not text")
            output = _parse_jsonl_output(completed.stdout)
            # Provider Structured Outputs guarantee the portable shape subset.
            # Capability owners apply the complete platform contract (bounds,
            # uniqueness, cross-field rules and references) after ModelGateway
            # has received the response.
            _validate_schema(output, provider_schema)
            if capability == "plan-formal-knowledge-step":
                selection = output.get("selection")
                if not isinstance(selection, dict):
                    raise CodexCliProviderError(
                        "Codex formal step selection is not an object"
                    )
                output = selection
            return output
