"""Direct, source-only baseline executor for sealed product validation tasks."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Mapping, Protocol

from software_world_model.ai_infrastructure import (
    AgenticModelStrategyConfiguration,
    AuthorizedInputItem,
    AuthorizedInputManifest,
    InputDisposition,
    ModelExecutionContext,
    ModelGatewayResult,
    OutputSchemaDefinition,
    PlatformProposalMode,
    RuntimeAccessMode,
)
from software_world_model.cross_cutting import Digest, DomainError, ErrorCode, digest_of
from software_world_model.source_integration import (
    LocalGitConnector,
    OperationBudget,
    SourceTool,
)

from .execution import HoldoutAnswerPath, HoldoutPathResult, SealedAnswerClaim


DIRECT_ANSWER_SCHEMA_REF = "product-holdout-direct-answer-action@1"
DIRECT_ANSWER_PROMPT_REF = "product-holdout-direct-source-investigator@3"
DIRECT_ANSWER_STRATEGY_REF = "direct-source-answer-baseline@4"
_MAX_CLAIMS = 6
_MAX_CONTRACT_ATTEMPTS_PER_STATE = 3


DIRECT_ANSWER_OUTPUT_SCHEMA = OutputSchemaDefinition(
    "product_holdout_direct_answer_action",
    {
        "type": "object",
        "properties": {
            "decision": {"type": "string", "enum": ["EXECUTE", "FINISH"]},
            "tool": {
                "type": "string",
                "enum": ["LIST", "SEARCH", "READ", "COMPARE", "NONE"],
            },
            "revision": {"type": "string"},
            "base": {"type": "string"},
            "path": {"type": "string"},
            "query": {"type": "string"},
            "cursor": {"type": "string"},
            "offset": {"type": "string"},
            "max_bytes": {"type": "string"},
            "page_size": {"type": "string"},
            "rationale": {"type": "string"},
            "claims": {
                "type": "array",
                "maxItems": _MAX_CLAIMS,
                "items": {
                    "type": "object",
                    "properties": {
                        "claim": {"type": "string"},
                        "support_references": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                    "required": ["claim", "support_references"],
                    "additionalProperties": False,
                },
            },
        },
        "required": [
            "decision",
            "tool",
            "revision",
            "base",
            "path",
            "query",
            "cursor",
            "offset",
            "max_bytes",
            "page_size",
            "rationale",
            "claims",
        ],
        "additionalProperties": False,
    },
)


_DIRECT_ANSWER_PROMPT = f"""You are the direct source investigator in a sealed software-task comparison.
You have no files, tools, web, workspace, memory, reference answer, scoring dimensions, or hidden context. Use only the supplied task and source observations.
Choose exactly one action. EXECUTE proposes LIST, SEARCH, READ, or COMPARE and must return no claims. FINISH uses tool NONE and returns one to {_MAX_CLAIMS} concise claims in the same language as the question.
Use only the exact revision scope and allowed paths in the task. LIST uses revision and optional cursor/page_size. SEARCH uses revision/query and optional cursor/page_size. READ uses revision/path and optional offset/max_bytes. COMPARE uses the exact parent as base and exact target as revision. Leave every unused parameter as an empty string.
Each final claim must be fully supported by one or more exact supplied observation_ref values. Do not cite an identifier you were not given. Preserve conditions, exception paths, boundaries, source limitations, and unknowns. Do not turn comments or commit messages into stronger runtime facts. Do not claim repository-wide absence from a bounded read.
The supplied source-coverage record is a mandatory completeness contract. Before FINISH, fully READ every allowed path at the exact target revision, following next_cursor until the file is complete. For a parent-to-target task, also COMPARE the exact parent and target. These requirements expose the same sealed source boundary to every direct run; they are not answer hints or scoring criteria.
For FINISH, combine related facts into three to six compact claims and keep the complete JSON below 900 output tokens. Preserve every material branch while avoiding repeated explanations and repeated references.
FINISH only after enough authorized source has been observed to answer every material part of the question. Return exactly the JSON object required by the supplied schema and no additional prose."""


class ModelGatewayPort(Protocol):
    def invoke(self, context: ModelExecutionContext) -> ModelGatewayResult: ...


@dataclass(frozen=True, slots=True)
class DirectSourceObservation:
    observation_ref: str
    ordinal: int
    tool: str
    revision: str
    subject: str
    parameters: tuple[tuple[str, str], ...]
    content: str
    content_digest: Digest
    byte_count: int
    has_more: bool
    next_cursor: str | None
    truncated: bool
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        observation_ref: str,
        ordinal: int,
        tool: SourceTool,
        revision: str,
        subject: str,
        parameters: Mapping[str, str],
        payload: bytes,
        has_more: bool,
        next_cursor: str | None,
        truncated: bool,
    ) -> "DirectSourceObservation":
        try:
            content = payload.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise DomainError(
                ErrorCode.SOURCE_OPERATION_FAILED,
                "direct source observation is not UTF-8 text",
            ) from exc
        values = {
            "observation_ref": _text(observation_ref, "source observation reference"),
            "ordinal": _positive(ordinal, "source observation ordinal"),
            "tool": tool.value,
            "revision": _text(revision, "source observation revision"),
            "subject": _text(subject, "source observation subject"),
            "parameters": dict(sorted(parameters.items())),
            "content": content,
            "content_digest": "sha256:" + hashlib.sha256(payload).hexdigest(),
            "byte_count": len(payload),
            "has_more": has_more,
            "next_cursor": next_cursor,
            "truncated": truncated,
        }
        return cls(
            observation_ref=values["observation_ref"],
            ordinal=ordinal,
            tool=values["tool"],
            revision=values["revision"],
            subject=values["subject"],
            parameters=tuple(sorted(parameters.items())),
            content=content,
            content_digest=Digest(values["content_digest"]),
            byte_count=len(payload),
            has_more=has_more,
            next_cursor=next_cursor,
            truncated=truncated,
            digest=digest_of(values),
        )

    def model_view(self) -> dict[str, object]:
        return {
            "observation_ref": self.observation_ref,
            "tool": self.tool,
            "revision": self.revision,
            "subject": self.subject,
            "parameters": dict(self.parameters),
            "content": self.content,
            "content_digest": self.content_digest.value,
            "byte_count": self.byte_count,
            "has_more": self.has_more,
            "next_cursor": self.next_cursor,
            "truncated": self.truncated,
        }


@dataclass(frozen=True, slots=True)
class _DirectAction:
    finish: bool
    tool: SourceTool | None
    parameters: dict[str, str]
    rationale: str
    claims: tuple[SealedAnswerClaim, ...]


class DirectSourceAnswerExecutor:
    def __init__(
        self,
        *,
        gateway: ModelGatewayPort,
        configuration: AgenticModelStrategyConfiguration,
        expected_model_fingerprint: str,
        origin: str = "direct-source-answer",
    ) -> None:
        self._gateway = gateway
        self._configuration = configuration
        self._expected_model_fingerprint = _text(
            expected_model_fingerprint, "expected model fingerprint"
        )
        self._origin = _text(origin, "direct answer origin")

    def execute(
        self,
        *,
        task_input: Mapping[str, object],
        connector: LocalGitConnector,
        run_id: str,
    ) -> HoldoutPathResult:
        _verify_task_input_digest(task_input)
        run_id = _text(run_id, "direct answer run ID")
        policy = task_input["resource_policy"]
        if (
            self._configuration.max_output_tokens
            != policy["maximum_output_tokens_per_call"]
            or self._configuration.timeout_milliseconds
            != policy["timeout_per_call_milliseconds"]
        ):
            raise DomainError(
                ErrorCode.QUALIFICATION_INVALID,
                "direct answer configuration does not match the sealed task resources",
            )
        observations: list[DirectSourceObservation] = []
        results: list[ModelGatewayResult] = []
        state_attempts = 0
        contract_repair: str | None = None
        while len(results) < policy["maximum_model_calls"]:
            state_attempts += 1
            result = self._invoke(
                task_input=task_input,
                observations=tuple(observations),
                run_id=run_id,
                ordinal=len(results) + 1,
                contract_repair=contract_repair,
            )
            results.append(result)
            if _retryable_structured_rejection(
                result, self._expected_model_fingerprint
            ):
                if state_attempts >= _MAX_CONTRACT_ATTEMPTS_PER_STATE:
                    _require_eligible_result(
                        result, self._expected_model_fingerprint
                    )
                contract_repair = (
                    "The previous output violated the structured-output contract "
                    "or was truncated. Return one complete JSON object only. For "
                    "FINISH, use no more than six compact claims and stay below "
                    "900 output tokens."
                )
                continue
            _require_eligible_result(result, self._expected_model_fingerprint)
            assert result.response is not None
            try:
                value = json.loads(result.response.output_text)
            except json.JSONDecodeError as exc:
                raise DomainError(
                    ErrorCode.STRUCTURED_OUTPUT_INVALID,
                    "direct answer action is not JSON",
                ) from exc
            try:
                action = _parse_action(
                    value,
                    task_input=task_input,
                    observation_refs={
                        item.observation_ref for item in observations
                    },
                )
                if action.finish:
                    _require_complete_source_coverage(
                        task_input=task_input,
                        observations=tuple(observations),
                    )
            except DomainError as exc:
                if (
                    exc.code is ErrorCode.STRUCTURED_OUTPUT_INVALID
                    and state_attempts < _MAX_CONTRACT_ATTEMPTS_PER_STATE
                ):
                    missing = exc.details.get("missing", [])
                    contract_repair = (
                        f"Previous output rejected: {exc.message}. Return a complete "
                        "replacement JSON object only; for FINISH use no more than "
                        "six compact claims and stay below 900 output tokens. Execute "
                        "every exact missing source action before FINISH: "
                        + json.dumps(
                            missing,
                            ensure_ascii=False,
                            sort_keys=True,
                            separators=(",", ":"),
                        )
                    )
                    continue
                raise
            if action.finish:
                return _seal_result(
                    task_input=task_input,
                    run_id=run_id,
                    origin=self._origin,
                    action=action,
                    results=tuple(results),
                    observations=tuple(observations),
                )
            if len(observations) >= policy["maximum_source_actions"]:
                raise DomainError(
                    ErrorCode.BUDGET_EXHAUSTED,
                    "direct answer exhausted the sealed source action budget",
                )
            assert action.tool is not None
            outcome = connector.execute(
                tool=action.tool,
                parameters=action.parameters,
                allowed_paths=tuple(task_input["allowed_paths"]),
                budget=OperationBudget(
                    max_calls=1,
                    max_items=200,
                    max_bytes=policy["maximum_source_bytes_per_action"],
                ),
            )
            observations.append(
                DirectSourceObservation.create(
                    observation_ref=(
                        f"direct-observation:{run_id}:{len(observations) + 1}"
                    ),
                    ordinal=len(observations) + 1,
                    tool=action.tool,
                    revision=outcome.repository_revision,
                    subject=outcome.subject,
                    parameters=action.parameters,
                    payload=outcome.payload,
                    has_more=outcome.has_more,
                    next_cursor=outcome.next_cursor,
                    truncated=outcome.truncated,
                )
            )
            state_attempts = 0
            contract_repair = None
        raise DomainError(
            ErrorCode.BUDGET_EXHAUSTED,
            "direct answer exhausted the sealed model call budget",
        )

    def _invoke(
        self,
        *,
        task_input: Mapping[str, object],
        observations: tuple[DirectSourceObservation, ...],
        run_id: str,
        ordinal: int,
        contract_repair: str | None,
    ) -> ModelGatewayResult:
        items = (
                AuthorizedInputItem.create(
                    item_id="instruction",
                    schema_ref="text@1",
                    classification=self._configuration.classification,
                    purpose="direct source answer policy",
                    authority_reference=DIRECT_ANSWER_PROMPT_REF,
                    disposition=InputDisposition.PROVIDED,
                    content=_DIRECT_ANSWER_PROMPT,
                ),
                AuthorizedInputItem.create(
                    item_id="sealed-task",
                    schema_ref="swm.product-holdout-task-input@1",
                    classification=self._configuration.classification,
                    purpose="answer the exact sealed task",
                    authority_reference=str(task_input["task_input_digest"]),
                    disposition=InputDisposition.PROVIDED,
                    content=json.dumps(
                        task_input,
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                ),
                AuthorizedInputItem.create(
                    item_id="source-observations",
                    schema_ref="direct-source-observations@1",
                    classification=self._configuration.classification,
                    purpose="use only platform-authorized source observations",
                    authority_reference=f"direct-run:{run_id}:observations:{ordinal}",
                    disposition=InputDisposition.PROVIDED,
                    content=json.dumps(
                        [item.model_view() for item in observations],
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    )
                    if observations
                    else "[]",
                ),
                AuthorizedInputItem.create(
                    item_id="source-coverage",
                    schema_ref="direct-source-coverage@1",
                    classification=self._configuration.classification,
                    purpose="enforce complete use of the sealed source boundary",
                    authority_reference=f"direct-run:{run_id}:coverage:{ordinal}",
                    disposition=InputDisposition.PROVIDED,
                    content=json.dumps(
                        _source_coverage_view(
                            task_input=task_input,
                            observations=observations,
                        ),
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                ),
            )
        if contract_repair is not None:
            items += (
                AuthorizedInputItem.create(
                    item_id="contract-repair",
                    schema_ref="text@1",
                    classification=self._configuration.classification,
                    purpose="repair the last rejected action at the same state",
                    authority_reference=(
                        f"direct-run:{run_id}:contract-repair:{ordinal}"
                    ),
                    disposition=InputDisposition.PROVIDED,
                    content=contract_repair,
                ),
            )
        items += (
            AuthorizedInputItem.create(
                item_id="qualification",
                schema_ref="qualification-ref@1",
                classification=self._configuration.classification,
                purpose="bind the live no-tools model boundary",
                authority_reference=self._configuration.qualification_ref,
                disposition=InputDisposition.PROVIDED,
                content=self._configuration.qualification_ref,
            ),
        )
        manifest = AuthorizedInputManifest.create(
            capability_id="product-holdout.direct-source-answer",
            strategy_ref=DIRECT_ANSWER_STRATEGY_REF,
            execution_stage="DIRECT_SOURCE_INVESTIGATION",
            calling_module="validation/product-holdout",
            proposal_vocabulary_ref=DIRECT_ANSWER_SCHEMA_REF,
            items=items,
        )
        return self._gateway.invoke(
            ModelExecutionContext(
                execution_envelope_ref=f"direct-holdout:{run_id}:call:{ordinal}",
                manifest=manifest,
                prompt_program_ref=DIRECT_ANSWER_PROMPT_REF,
                rendering_contract_version="manifest-messages@1",
                output_schema_ref=DIRECT_ANSWER_SCHEMA_REF,
                runtime_access_mode=RuntimeAccessMode.NO_EXTERNAL_ACCESS,
                platform_proposal_mode=(
                    PlatformProposalMode.DECLARED_PLATFORM_PROPOSAL_ONLY
                ),
                requested_model_ref=self._configuration.model_ref,
                provider_type=self._configuration.provider_type,
                adapter_version=self._configuration.adapter_version,
                provider_configuration_fingerprint=(
                    self._configuration.provider_configuration_fingerprint
                ),
                max_output_tokens=self._configuration.max_output_tokens,
                timeout_milliseconds=self._configuration.timeout_milliseconds,
                classification=self._configuration.classification,
                required_exact_fingerprint=True,
            )
        )


def direct_answer_output_schemas() -> dict[str, OutputSchemaDefinition]:
    return {DIRECT_ANSWER_SCHEMA_REF: DIRECT_ANSWER_OUTPUT_SCHEMA}


def direct_answer_implementation_digest() -> Digest:
    return digest_of(
        {
            "strategy_ref": DIRECT_ANSWER_STRATEGY_REF,
            "prompt_ref": DIRECT_ANSWER_PROMPT_REF,
            "prompt": _DIRECT_ANSWER_PROMPT,
            "schema_ref": DIRECT_ANSWER_SCHEMA_REF,
            "schema": DIRECT_ANSWER_OUTPUT_SCHEMA.schema,
            "source_policy": "LOCAL_GIT_READ_ONLY_ALLOWED_PATHS_ONLY",
            "source_coverage_policy": (
                "FULL_TARGET_READ_FOR_EVERY_ALLOWED_PATH_AND_EXACT_COMPARE@2"
            ),
            "claim_policy": "EXACT_OBSERVATION_REFERENCES_ONLY",
            "structured_output_retry_policy": (
                "COMPLETE_AUDITED_WITH_EXACT_MISSING_ACTION_MAX_3_PER_STATE@4"
            ),
            "finish_output_budget_policy": "MAX_6_CLAIMS_UNDER_900_TOKENS@1",
            "finish_parameter_policy": (
                "NO_ACTION_FIELDS_EXCEPT_IGNORED_EXACT_TARGET_OR_COMPARISON_ECHO@3"
            ),
            "execute_parameter_echo_policy": (
                "IGNORE_ONLY_EXACT_PARENT_AND_ALLOWED_PATH_IN_UNUSED_FIELDS@1"
            ),
        }
    )


def _parse_action(
    value: object,
    *,
    task_input: Mapping[str, object],
    observation_refs: set[str],
) -> _DirectAction:
    fields = {
        "decision",
        "tool",
        "revision",
        "base",
        "path",
        "query",
        "cursor",
        "offset",
        "max_bytes",
        "page_size",
        "rationale",
        "claims",
    }
    if not isinstance(value, dict) or set(value) != fields:
        _invalid("direct answer action does not match the closed contract")
    if any(not isinstance(value[key], str) for key in fields - {"claims"}):
        _invalid("direct answer action text fields are invalid")
    rationale = value["rationale"]
    if not rationale or rationale != rationale.strip():
        _invalid("direct answer rationale must be non-empty")
    parameters = {
        key: value[key]
        for key in (
            "revision",
            "base",
            "path",
            "query",
            "cursor",
            "offset",
            "max_bytes",
            "page_size",
        )
        if value[key]
    }
    if value["decision"] == "FINISH":
        revision_scope = task_input["revision_scope"]
        target_revision = revision_scope["target"]
        parent_revision = revision_scope["parent"]
        exact_comparison = (
            f"{parent_revision}..{target_revision}"
            if revision_scope["kind"] == "PARENT_TO_TARGET"
            and parent_revision is not None
            else None
        )
        harmless_echoes = [
            {},
            {"revision": target_revision},
        ]
        if exact_comparison is not None:
            harmless_echoes.extend(
                (
                    {"revision": exact_comparison},
                    {
                        "base": parent_revision,
                        "revision": target_revision,
                    },
                    {
                        "base": parent_revision,
                        "revision": exact_comparison,
                    },
                )
            )
        harmless_target_echo = parameters in harmless_echoes
        if value["tool"] != "NONE" or not harmless_target_echo:
            _invalid("direct answer FINISH cannot carry a source action")
        raw_claims = value["claims"]
        if (
            not isinstance(raw_claims, list)
            or not raw_claims
            or len(raw_claims) > _MAX_CLAIMS
        ):
            _invalid("direct answer FINISH must contain bounded claims")
        claims = []
        for item in raw_claims:
            if (
                not isinstance(item, dict)
                or set(item) != {"claim", "support_references"}
                or not isinstance(item["support_references"], list)
                or not isinstance(item["claim"], str)
                or not item["claim"]
                or item["claim"] != item["claim"].strip()
            ):
                _invalid("direct answer claim does not match the closed contract")
            references = tuple(item["support_references"])
            if (
                not references
                or len(set(references)) != len(references)
                or any(reference not in observation_refs for reference in references)
            ):
                _invalid("direct answer claim cites an unauthorized observation")
            claims.append(SealedAnswerClaim(item["claim"], references))
        return _DirectAction(True, None, {}, rationale, tuple(claims))
    if value["decision"] != "EXECUTE" or value["claims"] != []:
        _invalid("direct answer executable action cannot carry final claims")
    tool_by_name = {
        "LIST": SourceTool.LIST,
        "SEARCH": SourceTool.SEARCH,
        "READ": SourceTool.READ,
        "COMPARE": SourceTool.COMPARE,
    }
    tool = tool_by_name.get(value["tool"])
    if tool is None:
        _invalid("direct answer executable action has no supported tool")
    allowed_by_tool = {
        SourceTool.LIST: {"revision", "cursor", "page_size"},
        SourceTool.SEARCH: {"revision", "query", "cursor", "page_size"},
        SourceTool.READ: {"revision", "path", "offset", "max_bytes"},
        SourceTool.COMPARE: {"base", "revision"},
    }
    extra_parameters = set(parameters) - allowed_by_tool[tool]
    harmless_extras = set()
    revision_scope = task_input["revision_scope"]
    if (
        "base" in extra_parameters
        and revision_scope["kind"] == "PARENT_TO_TARGET"
        and parameters["base"] == revision_scope["parent"]
    ):
        harmless_extras.add("base")
    if (
        tool is SourceTool.COMPARE
        and "path" in extra_parameters
        and parameters["path"] in task_input["allowed_paths"]
    ):
        harmless_extras.add("path")
    if extra_parameters != harmless_extras:
        _invalid("direct answer action contains parameters outside its tool contract")
    executable_parameters = {
        key: value
        for key, value in parameters.items()
        if key in allowed_by_tool[tool]
    }
    _validate_action_scope(tool, executable_parameters, task_input)
    return _DirectAction(False, tool, executable_parameters, rationale, ())


def _validate_action_scope(
    tool: SourceTool,
    parameters: Mapping[str, str],
    task_input: Mapping[str, object],
) -> None:
    scope = task_input["revision_scope"]
    target = scope["target"]
    parent = scope["parent"]
    revision = parameters.get("revision")
    if tool is SourceTool.COMPARE:
        if (
            scope["kind"] != "PARENT_TO_TARGET"
            or parameters != {"base": parent, "revision": target}
        ):
            _invalid("direct comparison must use the exact sealed parent and target")
        return
    allowed_revisions = {target} if parent is None else {parent, target}
    if revision not in allowed_revisions:
        _invalid("direct source action uses a revision outside the sealed task")
    if tool is SourceTool.READ and not parameters.get("path"):
        _invalid("direct source read has no path")
    if tool is SourceTool.SEARCH and not parameters.get("query"):
        _invalid("direct source search has no query")


def _source_coverage_view(
    *,
    task_input: Mapping[str, object],
    observations: tuple[DirectSourceObservation, ...],
) -> dict[str, object]:
    scope = task_input["revision_scope"]
    target = scope["target"]
    required = [
        {
            "tool": "READ",
            "revision": target,
            "path": path,
            "completion": "bytes:0-EOF",
        }
        for path in task_input["allowed_paths"]
    ]
    completed = []
    missing = []
    for item in required:
        references, next_offset = _read_progress(
            observations=observations,
            revision=item["revision"],
            path=item["path"],
        )
        if references and next_offset is None:
            completed.append({**item, "observation_refs": list(references)})
        else:
            missing.append(
                {
                    **item,
                    "next_action": {
                        "tool": "READ",
                        "revision": item["revision"],
                        "path": item["path"],
                        "offset": next_offset or "0",
                        "max_bytes": str(
                            task_input["resource_policy"][
                                "maximum_source_bytes_per_action"
                            ]
                        ),
                    },
                }
            )
    if scope["kind"] == "PARENT_TO_TARGET":
        comparison = {
            "tool": "COMPARE",
            "base": scope["parent"],
            "revision": target,
        }
        references = tuple(
            item.observation_ref
            for item in observations
            if item.tool == SourceTool.COMPARE.value
            and item.revision == target
            and dict(item.parameters)
            == {"base": scope["parent"], "revision": target}
            and not item.truncated
        )
        if references:
            completed.append(
                {**comparison, "observation_refs": list(references)}
            )
        else:
            missing.append({**comparison, "next_action": comparison})
    return {
        "policy": "FULL_TARGET_READ_FOR_EVERY_ALLOWED_PATH_AND_EXACT_COMPARE@2",
        "required": required
        + (
            [
                {
                    "tool": "COMPARE",
                    "base": scope["parent"],
                    "revision": target,
                }
            ]
            if scope["kind"] == "PARENT_TO_TARGET"
            else []
        ),
        "completed": completed,
        "missing": missing,
        "finish_allowed": not missing,
    }


def _read_progress(
    *,
    observations: tuple[DirectSourceObservation, ...],
    revision: str,
    path: str,
) -> tuple[tuple[str, ...], str | None]:
    reads = tuple(
        item
        for item in observations
        if item.tool == SourceTool.READ.value
        and item.revision == revision
        and item.subject == path
    )
    expected_offset = "0"
    references = []
    for item in reads:
        parameters = dict(item.parameters)
        if parameters.get("offset", "0") != expected_offset:
            continue
        references.append(item.observation_ref)
        if not item.has_more and not item.truncated:
            return tuple(references), None
        if not item.next_cursor:
            return (), expected_offset
        expected_offset = item.next_cursor
    return (), expected_offset


def _require_complete_source_coverage(
    *,
    task_input: Mapping[str, object],
    observations: tuple[DirectSourceObservation, ...],
) -> None:
    coverage = _source_coverage_view(
        task_input=task_input,
        observations=observations,
    )
    if coverage["missing"]:
        raise DomainError(
            ErrorCode.STRUCTURED_OUTPUT_INVALID,
            "direct answer cannot finish before required source coverage is complete",
            {"missing": coverage["missing"]},
        )


def _require_eligible_result(
    result: ModelGatewayResult, expected_model_fingerprint: str
) -> None:
    if (
        not result.eligibility.eligible_for_production_domain_output
        or result.response is None
    ):
        code = (
            ErrorCode.EVALUATION_OUTCOME_PENDING
            if result.eligibility.reason == "MODEL_CALL_OUTCOME_UNKNOWN"
            else ErrorCode.CONTROL_STATE_DENIED
        )
        raise DomainError(
            (
                ErrorCode.STRUCTURED_OUTPUT_INVALID
                if result.call.failure_code
                == ErrorCode.STRUCTURED_OUTPUT_INVALID.value
                else code
            ),
            "direct answer model result is not eligible for evaluation output",
            {
                "eligibility_reason": result.eligibility.reason,
                "model_failure_code": result.call.failure_code or "NONE",
            },
        )
    response = result.response
    if (
        response.actual_model_fingerprint != expected_model_fingerprint
        or not response.provider_request_id
        or not response.usage_complete
        or response.input_tokens is None
        or response.output_tokens is None
    ):
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "direct answer model identity or usage is incomplete",
        )


def _retryable_structured_rejection(
    result: ModelGatewayResult, expected_model_fingerprint: str
) -> bool:
    response = result.response
    call = getattr(result, "call", None)
    return (
        getattr(call, "failure_code", None)
        == ErrorCode.STRUCTURED_OUTPUT_INVALID.value
        and response is not None
        and response.actual_model_fingerprint == expected_model_fingerprint
        and bool(response.provider_request_id)
        and response.usage_complete
        and response.input_tokens is not None
        and response.output_tokens is not None
    )


def _seal_result(
    *,
    task_input: Mapping[str, object],
    run_id: str,
    origin: str,
    action: _DirectAction,
    results: tuple[ModelGatewayResult, ...],
    observations: tuple[DirectSourceObservation, ...],
) -> HoldoutPathResult:
    responses = tuple(result.response for result in results)
    assert all(response is not None for response in responses)
    return HoldoutPathResult.create(
        result_ref=f"direct-answer-result:{run_id}",
        run_id=run_id,
        path=HoldoutAnswerPath.DIRECT,
        origin=origin,
        implementation_digest=direct_answer_implementation_digest(),
        task_input=task_input,
        answer="\n".join(item.claim for item in action.claims),
        claims=action.claims,
        actual_model_fingerprint=responses[0].actual_model_fingerprint,
        provider_request_ids=tuple(response.provider_request_id for response in responses),
        model_call_count=len(results),
        source_action_count=len(observations),
        source_byte_count=sum(item.byte_count for item in observations),
        input_tokens=sum(response.input_tokens for response in responses),
        output_tokens=sum(response.output_tokens for response in responses),
        usage_complete=all(response.usage_complete for response in responses),
    )


def _verify_task_input_digest(task_input: Mapping[str, object]) -> None:
    digest = task_input.get("task_input_digest")
    if not isinstance(digest, str) or digest_of(
        {key: value for key, value in task_input.items() if key != "task_input_digest"}
    ).value != digest:
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "direct answer task input digest is invalid",
        )


def _invalid(message: str) -> None:
    raise DomainError(ErrorCode.STRUCTURED_OUTPUT_INVALID, message)


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} must be non-empty")
    return value


def _positive(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} must be positive")
    return value
