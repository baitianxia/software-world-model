from __future__ import annotations

import json
import uuid

from swm_demo.agent_contract import (
    AgentApplicationServices,
    AgentTask,
    AnswerCandidate,
    AnswerClaim,
)
from swm_demo.artifact_contract import ArtifactRequest, RevisionComparison
from swm_demo.knowledge_contract import KnowledgeBuildTarget
from swm_demo.knowledge_requirement import (
    FACT,
    GAP,
    INFERENCE,
    FormalKnowledgeReference,
    KnowledgeNeed,
    KnowledgeRequirement,
    KnowledgeSufficiencyAssessment,
    KnowledgeSufficiencyItem,
)
from swm_demo.knowledge_update import BuildIntent, parse_candidate_bundle
from swm_demo.model_gateway import ModelGateway, ModelPhase


class TaskExecutionError(RuntimeError):
    def __init__(
        self,
        status: str,
        message: str,
        snapshot_id: str | None = None,
    ):
        super().__init__(message)
        self.status = status
        self.snapshot_id = snapshot_id


_ARTIFACT_REQUEST_KEYS = frozenset(
    {
        "build_profile",
        "include_globs",
        "git_commit_ids",
        "derive_java_ast",
        "revision",
        "commit_revisions",
        "comparisons",
    }
)
_KNOWLEDGE_TARGET_KEYS = frozenset(
    {
        "behavior_methods",
        "business_constraint_methods",
        "capability_modules",
        "history_commits",
        "required_inference_types",
        "premise_fact_ids",
        "premise_inference_ids",
    }
)

_MAX_FORMAL_TOOL_STEPS = 12
_MAX_CANDIDATE_PROPOSAL_ATTEMPTS = 3
_FORMAL_TOOL_ACTIONS = frozenset({"SEARCH", "NEIGHBORHOOD", "EXPLAIN", "STOP"})
_FORMAL_TOOL_CONTRACT = {
    "SEARCH": {
        "kind": ["ENTITY", "INFERENCE"],
        "required": ["kind", "query"],
        "optional": ["match_mode", "type_name", "limit", "cursor"],
    },
    "NEIGHBORHOOD": {
        "required": ["entity_ids"],
        "optional": ["direction", "predicates", "limit", "cursor"],
    },
    "EXPLAIN": {
        "kind": ["FACT", "INFERENCE"],
        "required": ["kind", "knowledge_ids"],
    },
    "STOP": {"required": []},
}


def _strict_object(
    value: object,
    field_name: str,
    *,
    allowed_keys: frozenset[str] | None = None,
) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be an object")
    if not all(isinstance(key, str) for key in value):
        raise ValueError(f"{field_name} keys must be strings")
    if allowed_keys is not None:
        unknown = sorted(set(value) - allowed_keys)
        if unknown:
            raise ValueError(f"{field_name} contains unknown fields: {unknown}")
    return value


def _strict_text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _strict_text_array(value: object, field_name: str) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{field_name} must be an array")
    items = tuple(
        _strict_text(item, f"{field_name}[{index}]")
        for index, item in enumerate(value)
    )
    if len(set(items)) != len(items):
        raise ValueError(f"{field_name} values must be unique")
    return items


def _strict_integer(
    value: object,
    field_name: str,
    *,
    minimum: int,
    maximum: int | None = None,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be an integer")
    if value < minimum or (maximum is not None and value > maximum):
        boundary = (
            f"between {minimum} and {maximum}"
            if maximum is not None
            else f"at least {minimum}"
        )
        raise ValueError(f"{field_name} must be {boundary}")
    return value


def _parse_formal_tool_action(
    value: object,
) -> tuple[str, dict[str, object]]:
    output = _strict_object(
        value,
        "formal knowledge tool step",
        allowed_keys=frozenset({"action", "arguments"}),
    )
    action = _strict_text(
        output.get("action"), "formal knowledge tool step.action"
    ).upper()
    if action not in _FORMAL_TOOL_ACTIONS:
        raise ValueError(
            "formal knowledge tool step.action must be one of "
            f"{sorted(_FORMAL_TOOL_ACTIONS)}"
        )
    arguments = _strict_object(
        output.get("arguments", {}),
        "formal knowledge tool step.arguments",
    )

    if action == "STOP":
        if arguments:
            raise ValueError("STOP does not accept arguments")
        return action, {}

    if action == "SEARCH":
        allowed = frozenset(
            {"kind", "query", "match_mode", "type_name", "limit", "cursor"}
        )
        arguments = _strict_object(
            arguments,
            "SEARCH arguments",
            allowed_keys=allowed,
        )
        kind = _strict_text(arguments.get("kind"), "SEARCH.kind").upper()
        if kind not in {"ENTITY", "INFERENCE"}:
            raise ValueError("SEARCH.kind must be ENTITY or INFERENCE")
        match_mode = _strict_text(
            arguments.get("match_mode", "CONTAINS"), "SEARCH.match_mode"
        ).upper()
        if match_mode not in {"EXACT", "CONTAINS"}:
            raise ValueError("SEARCH.match_mode must be EXACT or CONTAINS")
        type_value = arguments.get("type_name")
        type_name = (
            None
            if type_value is None
            else _strict_text(type_value, "SEARCH.type_name")
        )
        return action, {
            "kind": kind,
            "query": _strict_text(arguments.get("query"), "SEARCH.query"),
            "match_mode": match_mode,
            "type_name": type_name,
            "limit": _strict_integer(
                arguments.get("limit", 20),
                "SEARCH.limit",
                minimum=1,
                maximum=100,
            ),
            "cursor": _strict_integer(
                arguments.get("cursor", 0),
                "SEARCH.cursor",
                minimum=0,
            ),
        }

    if action == "NEIGHBORHOOD":
        arguments = _strict_object(
            arguments,
            "NEIGHBORHOOD arguments",
            allowed_keys=frozenset(
                {"entity_ids", "direction", "predicates", "limit", "cursor"}
            ),
        )
        entity_ids = _strict_text_array(
            arguments.get("entity_ids"), "NEIGHBORHOOD.entity_ids"
        )
        if not entity_ids:
            raise ValueError("NEIGHBORHOOD.entity_ids must not be empty")
        if len(entity_ids) > 20:
            raise ValueError("NEIGHBORHOOD.entity_ids exceeds 20")
        predicates = _strict_text_array(
            arguments.get("predicates", []), "NEIGHBORHOOD.predicates"
        )
        if len(predicates) > 20:
            raise ValueError("NEIGHBORHOOD.predicates exceeds 20")
        direction = _strict_text(
            arguments.get("direction", "BOTH"), "NEIGHBORHOOD.direction"
        ).upper()
        if direction not in {"OUTGOING", "INCOMING", "BOTH"}:
            raise ValueError(
                "NEIGHBORHOOD.direction must be OUTGOING, INCOMING, or BOTH"
            )
        return action, {
            "entity_ids": entity_ids,
            "direction": direction,
            "predicates": predicates,
            "limit": _strict_integer(
                arguments.get("limit", 100),
                "NEIGHBORHOOD.limit",
                minimum=1,
                maximum=200,
            ),
            "cursor": _strict_integer(
                arguments.get("cursor", 0),
                "NEIGHBORHOOD.cursor",
                minimum=0,
            ),
        }

    arguments = _strict_object(
        arguments,
        "EXPLAIN arguments",
        allowed_keys=frozenset({"kind", "knowledge_ids"}),
    )
    kind = _strict_text(arguments.get("kind"), "EXPLAIN.kind").upper()
    if kind not in {FACT, INFERENCE}:
        raise ValueError("EXPLAIN.kind must be FACT or INFERENCE")
    identifiers = _strict_text_array(
        arguments.get("knowledge_ids"), "EXPLAIN.knowledge_ids"
    )
    if not identifiers:
        raise ValueError("EXPLAIN.knowledge_ids must not be empty")
    if len(identifiers) > 50:
        raise ValueError("EXPLAIN.knowledge_ids exceeds 50")
    return action, {"kind": kind, "knowledge_ids": identifiers}


def _recoverable_formal_tool_action_error(value: object) -> bool:
    """Allow the model to repair safe contract mistakes without executing them.

    Unknown fields are not recoverable because they may be an attempt to
    override platform-owned Scope, Snapshot or another control parameter.
    Recognized actions with only recognized fields can receive bounded error
    feedback for missing, empty or otherwise invalid values.
    """

    if not isinstance(value, dict) or set(value) != {"action", "arguments"}:
        return False
    action_value = value.get("action")
    arguments = value.get("arguments")
    if not isinstance(action_value, str) or not isinstance(arguments, dict):
        return False
    action = action_value.upper()
    allowed_by_action = {
        "SEARCH": {"kind", "query", "match_mode", "type_name", "limit", "cursor"},
        "NEIGHBORHOOD": {
            "entity_ids",
            "direction",
            "predicates",
            "limit",
            "cursor",
        },
        "EXPLAIN": {"kind", "knowledge_ids"},
        "STOP": set(),
    }
    allowed = allowed_by_action.get(action)
    if allowed is None:
        return False
    model_controlled_fields = set().union(*allowed_by_action.values())
    # A field from another known action is a repairable cross-shape mistake.
    # Anything outside the complete model-controlled vocabulary may target a
    # platform-owned control such as Scope or Snapshot and fails immediately.
    return set(arguments).issubset(model_controlled_fields)


def _parse_artifact_request(value: object) -> ArtifactRequest:
    artifact = _strict_object(
        value,
        "artifact_request",
        allowed_keys=_ARTIFACT_REQUEST_KEYS,
    )
    derive_java_ast = artifact.get("derive_java_ast", False)
    if not isinstance(derive_java_ast, bool):
        raise ValueError("artifact_request.derive_java_ast must be a boolean")
    revision_value = artifact.get("revision")
    revision = (
        None
        if revision_value is None
        else _strict_text(revision_value, "artifact_request.revision")
    )
    comparisons_value = artifact.get("comparisons", [])
    if not isinstance(comparisons_value, (list, tuple)):
        raise ValueError("artifact_request.comparisons must be an array")
    comparisons: list[RevisionComparison] = []
    comparison_keys: set[tuple[str, str]] = set()
    for index, value in enumerate(comparisons_value):
        field = f"artifact_request.comparisons[{index}]"
        item = _strict_object(
            value,
            field,
            allowed_keys=frozenset({"base_revision", "target_revision"}),
        )
        missing = sorted(
            {"base_revision", "target_revision"} - set(item)
        )
        if missing:
            raise ValueError(f"{field} is missing required fields: {missing}")
        base_revision = _strict_text(
            item["base_revision"], f"{field}.base_revision"
        )
        target_revision = _strict_text(
            item["target_revision"], f"{field}.target_revision"
        )
        comparison_key = (base_revision, target_revision)
        if comparison_key in comparison_keys:
            raise ValueError(f"duplicate Artifact comparison: {comparison_key}")
        comparison_keys.add(comparison_key)
        comparisons.append(
            RevisionComparison(
                base_revision=base_revision,
                target_revision=target_revision,
            )
        )
    return ArtifactRequest(
        build_profile=_strict_text(
            artifact.get("build_profile", "model-led"),
            "artifact_request.build_profile",
        ),
        include_globs=_strict_text_array(
            artifact.get("include_globs", []),
            "artifact_request.include_globs",
        ),
        git_commit_ids=_strict_text_array(
            artifact.get("git_commit_ids", []),
            "artifact_request.git_commit_ids",
        ),
        derive_java_ast=derive_java_ast,
        revision=revision,
        commit_revisions=_strict_text_array(
            artifact.get("commit_revisions", []),
            "artifact_request.commit_revisions",
        ),
        comparisons=tuple(comparisons),
    )


def _parse_method_targets(
    value: object, field_name: str
) -> tuple[tuple[str, str], ...]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{field_name} must be an array")
    targets: list[tuple[str, str]] = []
    for index, item in enumerate(value):
        item_field = f"{field_name}[{index}]"
        if not isinstance(item, (list, tuple)) or len(item) != 2:
            raise ValueError(
                f"{item_field} must contain exactly "
                "[method_selector, human_readable_label]"
            )
        targets.append(
            (
                _strict_text(item[0], f"{item_field}[0]"),
                _strict_text(item[1], f"{item_field}[1]"),
            )
        )
    if len(set(targets)) != len(targets):
        raise ValueError(f"{field_name} values must be unique")
    return tuple(targets)


def _parse_knowledge_build_target(value: object) -> KnowledgeBuildTarget:
    target = _strict_object(
        value,
        "knowledge_target",
        allowed_keys=_KNOWLEDGE_TARGET_KEYS,
    )
    return KnowledgeBuildTarget(
        behavior_methods=_parse_method_targets(
            target.get("behavior_methods", []),
            "knowledge_target.behavior_methods",
        ),
        business_constraint_methods=_parse_method_targets(
            target.get("business_constraint_methods", []),
            "knowledge_target.business_constraint_methods",
        ),
        capability_modules=_strict_text_array(
            target.get("capability_modules", []),
            "knowledge_target.capability_modules",
        ),
        history_commits=_strict_text_array(
            target.get("history_commits", []),
            "knowledge_target.history_commits",
        ),
        required_inference_types=_strict_text_array(
            target.get("required_inference_types", []),
            "knowledge_target.required_inference_types",
        ),
        premise_fact_ids=_strict_text_array(
            target.get("premise_fact_ids", []),
            "knowledge_target.premise_fact_ids",
        ),
        premise_inference_ids=_strict_text_array(
            target.get("premise_inference_ids", []),
            "knowledge_target.premise_inference_ids",
        ),
    )


class TaskExecutionAgent:
    """Executes one task through formal knowledge and Application Services.

    Requirement, formal Knowledge Use, source Investigation, Assessment and
    Answer use distinct model contexts. Raw source and Candidate state exist
    only inside Investigation; the answer phase is reconstructed from a newly
    opened formal Snapshot.
    """

    def __init__(
        self, application: AgentApplicationServices, model_gateway: ModelGateway
    ):
        self.application = application
        self.model_gateway = model_gateway

    def execute(self, task: AgentTask) -> AnswerCandidate:
        context = self.application.open_knowledge_context(task.scope_id)
        requirement = self._form_requirement(task, context)
        formal_claims = self._investigate_formal_knowledge(
            task, requirement, context
        )
        assessment = self._assess_snapshot(
            task, requirement, context, formal_claims
        )

        if not assessment.complete:
            update = self._run_investigation(task, assessment, context)
            if update.status != "PUBLISHED" or update.published_snapshot_id is None:
                raise TaskExecutionError(
                    "KNOWLEDGE_GAP",
                    "Knowledge Update did not publish sufficient formal knowledge",
                    str(context["snapshot_id"]),
                )
            context = self.application.open_knowledge_context(task.scope_id)
            if context["snapshot_id"] != update.published_snapshot_id:
                raise TaskExecutionError(
                    "STALE_CONTEXT",
                    "published Snapshot is not the newly opened formal context",
                    str(context["snapshot_id"]),
                )
            # A newly published Snapshot invalidates both the old token and all
            # observations gathered under it.  Re-run the unchanged Requirement
            # from an empty tool trace in a fresh KNOWLEDGE_USE model context.
            formal_claims = self._investigate_formal_knowledge(
                task, requirement, context
            )
            assessment = self._assess_snapshot(
                task, requirement, context, formal_claims
            )

        validation = self.application.validate_sufficiency_assessment(assessment)
        if not validation["mechanically_valid"] or not assessment.complete:
            raise TaskExecutionError(
                "KNOWLEDGE_GAP",
                "the unchanged Knowledge Requirement is not fully satisfied",
                assessment.snapshot_id,
            )
        return self._draft_answer(task, requirement, assessment, context)

    def _form_requirement(
        self, task: AgentTask, context: dict[str, object]
    ) -> KnowledgeRequirement:
        model_context = self.model_gateway.open_context(
            task.task_id, ModelPhase.REQUIREMENT
        )
        try:
            formed = self.model_gateway.invoke(
                "form-knowledge-requirement",
                {
                    "original_request": task.original_request,
                    "use_case": task.use_case,
                    "parameters": task.parameters,
                    "scope_id": task.scope_id,
                    "knowledge_context_reference": context["revision"],
                },
                context=model_context,
            )
        finally:
            self.model_gateway.close_context(model_context)
        needs = tuple(
            KnowledgeNeed(
                need_id=str(item["need_id"]),
                question=str(item["question"]),
                sufficiency_criterion=str(item["sufficiency_criterion"]),
            )
            for item in formed.output.get("needs", [])
        )
        return KnowledgeRequirement(
            requirement_id=f"knowledge-requirement:{uuid.uuid4()}",
            task_id=task.task_id,
            scope_id=task.scope_id,
            knowledge_context_reference=str(context["revision"]),
            needs=needs,
            formation_model_call_id=formed.model_call_id,
        )

    def _investigate_formal_knowledge(
        self,
        task: AgentTask,
        requirement: KnowledgeRequirement,
        context: dict[str, object],
    ) -> tuple[dict[str, object], ...]:
        """Let the model compose bounded formal Knowledge Use tools.

        Scope and Snapshot token are deliberately absent from model-controlled
        arguments.  The Agent injects both values into every Application Service
        invocation and rejects any result outside the frozen read context.
        """

        tool_trace: list[dict[str, object]] = []
        seen_actions: set[str] = set()
        seen_invalid_actions: set[str] = set()
        formal_claims: dict[tuple[str, str], dict[str, object]] = {}
        model_context = self.model_gateway.open_context(
            task.task_id, ModelPhase.KNOWLEDGE_USE
        )
        try:
            for step_number in range(1, _MAX_FORMAL_TOOL_STEPS + 1):
                planned = self.model_gateway.invoke(
                    "plan-formal-knowledge-step",
                    {
                        "original_request": task.original_request,
                        "task_hint": {
                            "use_case": task.use_case,
                            "parameters": task.parameters,
                        },
                        "requirement": [
                            {
                                "need_id": item.need_id,
                                "question": item.question,
                                "sufficiency_criterion": item.sufficiency_criterion,
                            }
                            for item in requirement.needs
                        ],
                        "knowledge_context": context,
                        "available_tools": _FORMAL_TOOL_CONTRACT,
                        "tool_trace": list(tool_trace),
                        "remaining_steps": _MAX_FORMAL_TOOL_STEPS - step_number + 1,
                    },
                    context=model_context,
                )
                try:
                    action, arguments = _parse_formal_tool_action(planned.output)
                except ValueError as error:
                    if _recoverable_formal_tool_action_error(planned.output):
                        invalid_fingerprint = json.dumps(
                            planned.output,
                            ensure_ascii=False,
                            sort_keys=True,
                            separators=(",", ":"),
                        )
                        if invalid_fingerprint in seen_invalid_actions:
                            raise TaskExecutionError(
                                "REPEATED_KNOWLEDGE_TOOL_ACTION",
                                "model repeated an invalid formal knowledge action",
                                str(context["snapshot_id"]),
                            ) from error
                        seen_invalid_actions.add(invalid_fingerprint)
                        tool_trace.append(
                            {
                                "step": step_number,
                                "action": "REJECTED",
                                "arguments": planned.output,
                                "result": {
                                    "status": "INVALID_ACTION",
                                    "error": str(error),
                                },
                            }
                        )
                        continue
                    raise TaskExecutionError(
                        "INVALID_KNOWLEDGE_TOOL_ACTION",
                        str(error),
                        str(context["snapshot_id"]),
                    ) from error

                fingerprint = json.dumps(
                    {"action": action, "arguments": arguments},
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
                if fingerprint in seen_actions:
                    raise TaskExecutionError(
                        "REPEATED_KNOWLEDGE_TOOL_ACTION",
                        f"model repeated formal knowledge action: {action}",
                        str(context["snapshot_id"]),
                    )
                seen_actions.add(fingerprint)

                if action == "STOP":
                    return tuple(
                        formal_claims[key] for key in sorted(formal_claims)
                    )

                result = self._execute_formal_tool(
                    task, context, action, arguments
                )
                self._validate_formal_tool_context(task, context, result)
                self._collect_formal_claims(
                    action, arguments, result, formal_claims
                )
                tool_trace.append(
                    {
                        "step": step_number,
                        "action": action,
                        "arguments": arguments,
                        "result": result,
                    }
                )
        finally:
            self.model_gateway.close_context(model_context)

        raise TaskExecutionError(
            "KNOWLEDGE_TOOL_STEP_LIMIT",
            f"formal knowledge investigation exceeded {_MAX_FORMAL_TOOL_STEPS} steps",
            str(context["snapshot_id"]),
        )

    def _execute_formal_tool(
        self,
        task: AgentTask,
        context: dict[str, object],
        action: str,
        arguments: dict[str, object],
    ) -> dict[str, object]:
        scope_id = task.scope_id
        snapshot_token = str(context["snapshot_token"])
        try:
            if action == "SEARCH":
                return self.application.search_knowledge(
                    scope_id,
                    snapshot_token,
                    str(arguments["kind"]),
                    str(arguments["query"]),
                    str(arguments["match_mode"]),
                    (
                        None
                        if arguments["type_name"] is None
                        else str(arguments["type_name"])
                    ),
                    int(arguments["limit"]),
                    int(arguments["cursor"]),
                )
            if action == "NEIGHBORHOOD":
                return self.application.query_knowledge_neighborhood(
                    scope_id,
                    snapshot_token,
                    tuple(str(item) for item in arguments["entity_ids"]),
                    str(arguments["direction"]),
                    tuple(str(item) for item in arguments["predicates"]),
                    int(arguments["limit"]),
                    int(arguments["cursor"]),
                )
            if action == "EXPLAIN":
                return self.application.explain_knowledge_batch(
                    scope_id,
                    snapshot_token,
                    str(arguments["kind"]),
                    tuple(str(item) for item in arguments["knowledge_ids"]),
                )
        except Exception as error:
            status = (
                "STALE_CONTEXT"
                if "STALE_CONTEXT" in str(error)
                else "KNOWLEDGE_TOOL_ERROR"
            )
            raise TaskExecutionError(
                status, str(error), str(context["snapshot_id"])
            ) from error
        raise AssertionError(f"unhandled formal knowledge action: {action}")

    @staticmethod
    def _validate_formal_tool_context(
        task: AgentTask,
        context: dict[str, object],
        result: dict[str, object],
    ) -> None:
        expected = {
            "scope_id": task.scope_id,
            "snapshot_id": context["snapshot_id"],
            "snapshot_token": context["snapshot_token"],
            "revision": context["revision"],
        }
        mismatches = [
            key for key, value in expected.items() if result.get(key) != value
        ]
        if mismatches:
            raise TaskExecutionError(
                "STALE_CONTEXT",
                "formal knowledge tool returned a different context: "
                + ", ".join(mismatches),
                str(context["snapshot_id"]),
            )

    @classmethod
    def _collect_formal_claims(
        cls,
        action: str,
        arguments: dict[str, object],
        result: dict[str, object],
        target: dict[tuple[str, str], dict[str, object]],
    ) -> None:
        if action == "SEARCH" and arguments["kind"] == INFERENCE:
            for item in result.get("items", []):
                cls._add_formal_claim(
                    target,
                    INFERENCE,
                    item,
                    "inference_id",
                    "statement",
                )
            return
        if action == "NEIGHBORHOOD":
            for item in result.get("facts", []):
                cls._add_formal_claim(
                    target, FACT, item, "fact_id", "proposition"
                )
            return
        if action != "EXPLAIN":
            return

        kind = str(arguments["kind"])
        identifier_field = "fact_id" if kind == FACT else "inference_id"
        statement_field = "proposition" if kind == FACT else "statement"
        for item in result.get("items", []):
            cls._add_formal_claim(
                target, kind, item, identifier_field, statement_field
            )
            if kind == INFERENCE:
                for supporting_fact in item.get("supporting_facts", []):
                    cls._add_formal_claim(
                        target,
                        FACT,
                        supporting_fact,
                        "fact_id",
                        "proposition",
                    )

    @staticmethod
    def _add_formal_claim(
        target: dict[tuple[str, str], dict[str, object]],
        kind: str,
        item: object,
        identifier_field: str,
        statement_field: str,
    ) -> None:
        if not isinstance(item, dict):
            raise TaskExecutionError(
                "INVALID_KNOWLEDGE_TOOL_RESULT",
                "formal knowledge result item must be an object",
            )
        identifier = _strict_text(
            item.get(identifier_field),
            f"formal knowledge result.{identifier_field}",
        )
        statement = _strict_text(
            item.get(statement_field),
            f"formal knowledge result.{statement_field}",
        )
        key = (kind, identifier)
        claim = {
            "text": statement,
            "references": [
                {"kind": kind, "reference_id": identifier}
            ],
        }
        previous = target.get(key)
        if previous is not None and previous != claim:
            raise TaskExecutionError(
                "INVALID_KNOWLEDGE_TOOL_RESULT",
                f"conflicting formal proposition for {kind}:{identifier}",
            )
        target[key] = claim

    def _assess_snapshot(
        self,
        task: AgentTask,
        requirement: KnowledgeRequirement,
        context: dict[str, object],
        formal_claims: tuple[dict[str, object], ...],
    ) -> KnowledgeSufficiencyAssessment:
        model_context = self.model_gateway.open_context(
            task.task_id, ModelPhase.ASSESSMENT
        )
        try:
            assessed = self.model_gateway.invoke(
                "assess-knowledge-sufficiency",
                {
                    "original_request": task.original_request,
                    "requirement": [
                        {
                            "need_id": item.need_id,
                            "question": item.question,
                            "sufficiency_criterion": item.sufficiency_criterion,
                        }
                        for item in requirement.needs
                    ],
                    "formal_claims": list(formal_claims),
                    "snapshot_id": context["snapshot_id"],
                    "knowledge_context_reference": context["revision"],
                },
                context=model_context,
            )
        finally:
            self.model_gateway.close_context(model_context)
        items = tuple(
            KnowledgeSufficiencyItem(
                need_id=str(item["need_id"]),
                status=str(item["status"]),
                formal_knowledge_references=tuple(
                    FormalKnowledgeReference(
                        kind=str(reference["kind"]),
                        reference_id=str(reference["reference_id"]),
                    )
                    for reference in item.get("references", [])
                ),
                rationale=str(item.get("rationale", "")),
            )
            for item in assessed.output.get("items", [])
        )
        assessment = KnowledgeSufficiencyAssessment(
            assessment_id=f"knowledge-assessment:{uuid.uuid4()}",
            requirement=requirement,
            snapshot_id=str(context["snapshot_id"]),
            knowledge_context_reference=str(context["revision"]),
            items=items,
            assessment_model_call_id=assessed.model_call_id,
        )
        discovered_references = {
            (str(reference["kind"]), str(reference["reference_id"]))
            for claim in formal_claims
            for reference in claim.get("references", [])
        }
        undiscovered = sorted(
            {
                (reference.kind, reference.reference_id)
                for item in assessment.items
                for reference in item.formal_knowledge_references
                if (reference.kind, reference.reference_id)
                not in discovered_references
            }
        )
        if undiscovered:
            raise TaskExecutionError(
                "INVALID_ASSESSMENT",
                "Assessment cites formal knowledge that was not discovered by "
                f"the fixed-context tool loop: {undiscovered}",
                assessment.snapshot_id,
            )
        validation = self.application.validate_sufficiency_assessment(assessment)
        if not validation["mechanically_valid"]:
            raise TaskExecutionError(
                "INVALID_ASSESSMENT",
                "; ".join(str(item) for item in validation["errors"]),
                assessment.snapshot_id,
            )
        return assessment

    def _run_investigation(
        self,
        task: AgentTask,
        assessment: KnowledgeSufficiencyAssessment,
        context: dict[str, object],
    ):
        investigation_context = self.model_gateway.open_context(
            task.task_id, ModelPhase.INVESTIGATION
        )
        try:
            planned = self.model_gateway.invoke(
                "derive-build-intent",
                {
                    "original_request": task.original_request,
                    "scope_id": task.scope_id,
                    "target_revision": context["revision"],
                    "gap_needs": [
                        {
                            "need_id": item.need_id,
                            "question": next(
                                need.question
                                for need in assessment.requirement.needs
                                if need.need_id == item.need_id
                            ),
                            "rationale": item.rationale,
                        }
                        for item in assessment.items
                        if item.status == GAP
                    ],
                },
                context=investigation_context,
            )
            output = planned.output
            gap_ids = tuple(
                item.need_id for item in assessment.items if item.status == GAP
            )
            try:
                artifact_request = _parse_artifact_request(
                    output.get("artifact_request", {})
                )
                build_target = _parse_knowledge_build_target(
                    output.get("knowledge_target", {})
                )
                intent = BuildIntent(
                    intent_id=f"build-intent:{uuid.uuid4()}",
                    requirement_id=assessment.requirement_id,
                    scope_id=task.scope_id,
                    assessment=assessment,
                    gap_need_ids=gap_ids,
                    artifact_request=artifact_request,
                    build_target=build_target,
                    target_revision=_strict_text(
                        output.get("target_revision", context["revision"]),
                        "target_revision",
                    ),
                    minimum_result_need_ids=gap_ids,
                    formation_model_call_id=planned.model_call_id,
                )
            except (TypeError, ValueError) as error:
                raise TaskExecutionError(
                    "INVALID_BUILD_INTENT",
                    str(error),
                    str(context["snapshot_id"]),
                ) from error
            handle = self.application.start_model_led_update(
                intent, investigation_context.context_id
            )
            collection = self.application.collect_investigation_sources(handle.run_id)
            formal_premises = self.application.investigation_formal_premises(
                handle.run_id
            )
            model_visible_artifacts = [
                {
                    "artifact_id": item.artifact_id,
                    "artifact_type": item.artifact_type,
                    "source_id": item.source_id,
                    "scope_id": item.scope_id,
                    "relative_path": item.relative_path,
                    "revision": item.revision,
                    "content_hash": item.content_hash,
                    "content_character_count": len(item.content),
                    "content_lines": [
                        {"line_number": index, "text": line}
                        for index, line in enumerate(
                            item.content.splitlines(), start=1
                        )
                    ],
                    "lineage_ids": list(item.lineage_ids),
                    "comparison": (
                        {
                            "base_revision": item.comparison.base_revision,
                            "target_revision": item.comparison.target_revision,
                        }
                        if item.comparison is not None
                        else None
                    ),
                }
                for item in collection.artifacts
            ]
            proposal_payload: dict[str, object] = {
                "intent_id": intent.intent_id,
                "gap_need_ids": list(gap_ids),
                "source_artifacts": model_visible_artifacts,
                "formal_premises": formal_premises,
            }
            for attempt in range(1, _MAX_CANDIDATE_PROPOSAL_ATTEMPTS + 1):
                proposed = self.model_gateway.invoke(
                    "propose-knowledge-candidates",
                    proposal_payload,
                    context=investigation_context,
                )
                try:
                    bundle = parse_candidate_bundle(
                        proposed.output,
                        intent=intent,
                        collection=collection,
                        proposal_model_call_id=proposed.model_call_id,
                    )
                except (TypeError, ValueError) as error:
                    if attempt == _MAX_CANDIDATE_PROPOSAL_ATTEMPTS:
                        raise TaskExecutionError(
                            "INVALID_CANDIDATE_PROPOSAL",
                            "model could not produce a valid Candidate proposal "
                            f"after {attempt} attempts: {error}",
                            str(context["snapshot_id"]),
                        ) from error
                    # The correction remains inside the isolated Investigation
                    # phase. The model returns a complete replacement proposal;
                    # platform-owned identity, context and provenance are rebuilt
                    # and validated again from the frozen sources.
                    proposal_payload = {
                        "intent_id": intent.intent_id,
                        "gap_need_ids": list(gap_ids),
                        "source_artifacts": model_visible_artifacts,
                        "formal_premises": formal_premises,
                        "previous_proposal": proposed.output,
                        "validation_feedback": {
                            "status": "REJECTED",
                            "attempt": attempt,
                            "error": str(error),
                        },
                    }
                    continue
                return self.application.submit_investigation_candidates(
                    handle.run_id, bundle
                )
            raise AssertionError("Candidate proposal loop ended unexpectedly")
        finally:
            self.model_gateway.close_context(investigation_context)

    def answer_from_formal_snapshot(
        self,
        task: AgentTask,
        requirement: KnowledgeRequirement,
    ) -> AnswerCandidate:
        """Answer an unchanged Requirement without opening a source investigation.

        A caller can construct this Agent with a fresh Provider after publication;
        this method has no Knowledge Update branch and therefore cannot fall back
        to Source Integration when the formal Snapshot is insufficient.
        """

        if requirement.task_id != task.task_id:
            raise TaskExecutionError(
                "INVALID_REQUIREMENT",
                "Knowledge Requirement and Agent Task identity differ",
            )
        if requirement.scope_id != task.scope_id:
            raise TaskExecutionError(
                "INVALID_REQUIREMENT",
                "Knowledge Requirement and Agent Task Scope differ",
            )
        context = self.application.open_knowledge_context(task.scope_id)
        if context["revision"] != requirement.knowledge_context_reference:
            raise TaskExecutionError(
                "STALE_CONTEXT",
                "Knowledge Requirement context differs from the current Snapshot",
                str(context["snapshot_id"]),
            )
        formal_claims = self._investigate_formal_knowledge(
            task, requirement, context
        )
        assessment = self._assess_snapshot(
            task, requirement, context, formal_claims
        )
        validation = self.application.validate_sufficiency_assessment(assessment)
        if not validation["mechanically_valid"] or not assessment.complete:
            raise TaskExecutionError(
                "KNOWLEDGE_GAP",
                "the unchanged Knowledge Requirement is not fully satisfied",
                assessment.snapshot_id,
            )
        return self._draft_answer(task, requirement, assessment, context)

    def _draft_answer(
        self,
        task: AgentTask,
        requirement: KnowledgeRequirement,
        assessment: KnowledgeSufficiencyAssessment,
        context: dict[str, object],
    ) -> AnswerCandidate:
        formal_by_id: dict[str, str] = {}
        for kind in (FACT, INFERENCE):
            identifiers = tuple(
                reference.reference_id
                for item in assessment.items
                for reference in item.formal_knowledge_references
                if reference.kind == kind
            )
            if not identifiers:
                continue
            explained = self.application.explain_knowledge_batch(
                task.scope_id,
                str(context["snapshot_token"]),
                kind,
                identifiers,
            )
            if explained["missing_ids"]:
                raise TaskExecutionError(
                    "INVALID_ASSESSMENT",
                    "Assessment references disappeared before answer drafting",
                    assessment.snapshot_id,
                )
            for item in explained["items"]:
                identifier = str(
                    item["fact_id"] if kind == FACT else item["inference_id"]
                )
                formal_by_id[identifier] = str(
                    item["proposition"] if kind == FACT else item["statement"]
                )
        claims: list[AnswerClaim] = []
        for item in assessment.items:
            references = item.formal_knowledge_reference_ids
            statements = [formal_by_id[reference] for reference in references]
            claims.append(
                AnswerClaim(
                    text="；".join(statements),
                    knowledge_reference_ids=references,
                    need_ids=(item.need_id,),
                )
            )
        answer_context = self.model_gateway.open_context(
            task.task_id, ModelPhase.ANSWER
        )
        try:
            drafted = self.model_gateway.invoke(
                "draft-answer",
                {
                    "requirement_id": requirement.requirement_id,
                    "assessment_id": assessment.assessment_id,
                    "claims": [item.text for item in claims],
                },
                context=answer_context,
            )
        finally:
            self.model_gateway.close_context(answer_context)
        return AnswerCandidate(
            candidate_id=f"answer-candidate:{uuid.uuid4()}",
            task_id=task.task_id,
            original_request=task.original_request,
            scope_id=task.scope_id,
            snapshot_id=assessment.snapshot_id,
            revision=assessment.knowledge_context_reference,
            claims=tuple(claims),
            answer=str(drafted.output["answer"]),
            drafting_model_call_id=drafted.model_call_id,
            assessment_reference=assessment.assessment_id,
            requirement=requirement,
            assessment=assessment,
            answer_model_context_id=answer_context.context_id,
        )
