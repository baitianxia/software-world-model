"""Engineering Chat Agent loop for architecture baseline V1.4.

One logical primary Agent per Turn plans, calls read-only tools over the exact
revision, observes, replans and drafts a cited answer.  A fresh independent
Reviewer checks the draft and may request bounded verification reads.  The
Application owns the tools, the evidence ledger, citation validation, budgets,
delivery authority and the Turn Trace; the model owns none of them.

Differences from the earlier lightweight loop (ADR-021):

* tool parity -- list/search/read/log/blame over any allowed path; reading does
  not require a previously issued candidate;
* several tool calls per model step, so breadth does not consume the shared
  per-Turn dispatch fuse;
* a citation is any evidence item actually returned in this Turn, identified
  by an Application-issued ``E<n>`` id and re-validated before delivery;
* when the budget is exhausted the same Agent drafts from existing evidence
  with explicit limits, and the draft is still independently reviewed;
* the Reviewer may run bounded verification reads that never enter the
  answer's evidence package.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Mapping, Protocol, Sequence

from software_world_model.cross_cutting import (
    Digest,
    DomainError,
    ErrorCode,
    Revision,
    digest_of,
)
from software_world_model.source_integration.exact_revision_tools import (
    ExactRevisionReadTools,
    SourceItem,
    SourceObservation,
)

from .conversational_engineering_agent import (
    EngineeringAgentCitation,
    EngineeringAgentModelCallReceipt,
    EngineeringAgentModelFailureKind,
)
from .engineering_conversation import (
    ConversationMessageKind,
    EngineeringConversationTurnExecutor,
    EngineeringProviderFailureClassification,
    EngineeringTurnCitation,
    EngineeringTurnExecutionOutcome,
    EngineeringTurnExecutionRequest,
)
from .lightweight_engineering_agent import (
    LightweightAgentResponseKind,
    LightweightAgentTraceStore,
    LightweightAgentTrajectory,
    LightweightDeliveryRequest,
    LightweightModelCallFailure,
    LightweightReview,
    LightweightReviewVerdict,
    SealedLightweightDeliveryControl,
)


CHAT_AGENT_MODE = "CHAT_AGENT_V14_SOURCE"
TOOL_OPERATIONS = ("LIST_PATHS", "SEARCH", "READ", "LOG", "BLAME")
FINAL_KINDS = ("ANSWER", "LIMITATION", "CLARIFICATION")
REVIEW_VERDICTS = ("APPROVED", "REWRITE", "MORE_EVIDENCE", "VERIFY")
VERIFY_OPERATIONS = ("READ", "SEARCH")


@dataclass(frozen=True, slots=True)
class ChatAgentLimits:
    """Per-Turn bounds; model calls must stay inside the standing dispatch fuse."""

    maximum_model_calls: int = 15
    reserved_review_calls: int = 3
    maximum_actions_per_step: int = 4
    maximum_tool_actions: int = 24
    maximum_observation_characters: int = 160_000
    maximum_item_characters: int = 6_000
    maximum_reviews: int = 2
    maximum_verification_reads: int = 4
    maximum_history_messages: int = 12
    maximum_history_characters: int = 2_000
    maximum_consecutive_rejections: int = 2

    def __post_init__(self) -> None:
        if self.maximum_model_calls <= self.reserved_review_calls or min(
            self.maximum_actions_per_step,
            self.maximum_tool_actions,
            self.maximum_reviews,
        ) < 1:
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "chat agent limits are inconsistent")


@dataclass(frozen=True, slots=True)
class ChatModelOutput:
    payload: Mapping[str, object]
    receipt: EngineeringAgentModelCallReceipt


class ChatAgentModel(Protocol):
    """Model boundary; implementations live in AI infrastructure."""

    @property
    def instance_ref(self) -> str: ...

    def step(
        self, *, turn_request: EngineeringTurnExecutionRequest, view: Mapping[str, object]
    ) -> ChatModelOutput: ...

    def review_draft(
        self, *, turn_request: EngineeringTurnExecutionRequest, view: Mapping[str, object]
    ) -> ChatModelOutput: ...


@dataclass(slots=True)
class _Evidence:
    evidence_id: str
    item: SourceItem
    observation_index: int


@dataclass(slots=True)
class _ObservationRecord:
    index: int
    operation: str
    arguments: Mapping[str, object]
    observation: SourceObservation | None
    error: str | None
    evidence_ids: tuple[str, ...] = ()


@dataclass(slots=True)
class _TurnState:
    observations: list[_ObservationRecord] = field(default_factory=list)
    evidence: dict[str, _Evidence] = field(default_factory=dict)
    action_keys: set[str] = field(default_factory=set)
    receipts: list[EngineeringAgentModelCallReceipt] = field(default_factory=list)
    events: list[dict[str, object]] = field(default_factory=list)
    tool_actions: int = 0
    reviews: int = 0
    rejections: int = 0
    feedback: list[str] = field(default_factory=list)
    review_findings: list[str] = field(default_factory=list)
    previous_draft: str | None = None
    plan: str = ""

    @property
    def model_calls(self) -> int:
        return len(self.receipts)


class _TurnFailure(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class ChatAgentTurnExecutor(EngineeringConversationTurnExecutor):
    """Run one Turn of the V1.4 engineering Chat Agent."""

    def __init__(
        self,
        *,
        model: ChatAgentModel,
        tools: ExactRevisionReadTools,
        delivery_control: SealedLightweightDeliveryControl,
        trace_store: LightweightAgentTraceStore,
        attempt_ref: str,
        limits: ChatAgentLimits = ChatAgentLimits(),
        trace_directory: Path | None = None,
    ) -> None:
        if not callable(getattr(model, "step", None)) or not callable(getattr(model, "review_draft", None)):
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "chat agent requires a model boundary")
        if not isinstance(tools, ExactRevisionReadTools):
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "chat agent requires exact-revision tools")
        self._model = model
        self._tools = tools
        self._delivery = delivery_control
        self._traces = trace_store
        self._attempt_ref = attempt_ref
        self._limits = limits
        self._trace_directory = trace_directory

    # ---------------------------------------------------------------- execute
    def execute(self, request: EngineeringTurnExecutionRequest) -> EngineeringTurnExecutionOutcome:
        if request.binding.repository_revision != self._tools.scope.revision:
            return self._finish_failure(
                request,
                _TurnState(),
                "AUTHORITY_RECORD_INCONSISTENT",
                "the read tools are bound to another revision",
                None,
            )
        state = _TurnState()
        try:
            while True:
                draft = self._agent_until_draft(request, state)
                outcome = self._review_and_deliver(request, state, draft)
                if outcome is not None:
                    return outcome
        except _TurnFailure as failure:
            return self._finish_failure(request, state, failure.code, failure.message, None)
        except LightweightModelCallFailure as failure:
            state.receipts.append(failure.receipt)
            return self._finish_failure(
                request, state, failure.code.value, failure.message, failure.receipt.failure_kind
            )

    # ------------------------------------------------------------- agent loop
    def _agent_until_draft(
        self, request: EngineeringTurnExecutionRequest, state: _TurnState
    ) -> dict[str, object]:
        while True:
            calls_left = self._limits.maximum_model_calls - state.model_calls
            agent_calls_left = calls_left - self._limits.reserved_review_calls
            if agent_calls_left < 1:
                raise _TurnFailure("BUDGET_EXHAUSTED", "no model calls remain for a draft")
            tools_enabled = (
                agent_calls_left > 1
                and state.tool_actions < self._limits.maximum_tool_actions
                and not (state.review_findings and state.previous_draft and not self._wants_evidence(state))
            )
            view = self._step_view(request, state, tools_enabled)
            output = self._model.step(turn_request=request, view=view)
            state.receipts.append(output.receipt)
            try:
                plan, actions, final = _parse_step(output.payload, self._limits)
            except DomainError as error:
                self._reject(state, f"output rejected: {error.message}")
                continue
            state.plan = plan
            if final is not None:
                problem = self._final_problem(final, state)
                if problem:
                    self._reject(state, problem)
                    continue
                state.rejections = 0
                state.events.append(
                    {"event": "DRAFT", "kind": final["kind"], "citations": list(final["citations"])}
                )
                return final
            if not tools_enabled:
                self._reject(
                    state,
                    "tools are disabled now: return a final response from the existing evidence, "
                    "stating clearly what remains unknown",
                )
                continue
            if not actions:
                self._reject(state, "choose at least one tool action or return a final response")
                continue
            state.rejections = 0
            state.feedback = []
            for action in actions:
                if state.tool_actions >= self._limits.maximum_tool_actions:
                    break
                self._run_action(state, action)

    def _reject(self, state: _TurnState, message: str) -> None:
        state.rejections += 1
        state.feedback = [message]
        state.events.append({"event": "REJECTED", "message": message})
        if state.rejections > self._limits.maximum_consecutive_rejections:
            raise _TurnFailure("STRUCTURED_OUTPUT_INVALID", "the Agent repeatedly produced unusable steps")

    @staticmethod
    def _wants_evidence(state: _TurnState) -> bool:
        return any(item.startswith("[MORE_EVIDENCE]") for item in state.review_findings)

    def _final_problem(self, final: Mapping[str, object], state: _TurnState) -> str | None:
        citations = final["citations"]
        unknown = [item for item in citations if item not in state.evidence]
        if unknown:
            return "citations must be evidence ids returned in this Turn; unknown: " + ", ".join(unknown[:8])
        if final["kind"] == "ANSWER" and not citations:
            return "an ANSWER must cite at least one evidence id; otherwise return a LIMITATION"
        return None

    def _run_action(self, state: _TurnState, action: Mapping[str, object]) -> None:
        operation = str(action["op"])
        arguments = {key: value for key, value in action.items() if key != "op" and value is not None}
        key = json.dumps([operation, arguments], sort_keys=True, ensure_ascii=False)
        index = len(state.observations) + 1
        if key in state.action_keys:
            state.observations.append(
                _ObservationRecord(index, operation, arguments, None, "duplicate of an earlier action; use its result")
            )
            return
        state.action_keys.add(key)
        state.tool_actions += 1
        try:
            observation = self._execute_tool(operation, arguments)
        except DomainError as error:
            state.observations.append(
                _ObservationRecord(index, operation, arguments, None, f"{error.code.value}: {error.message}")
            )
            state.events.append({"event": "TOOL_ERROR", "op": operation, "code": error.code.value})
            return
        ids: list[str] = []
        if operation != "LIST_PATHS":
            for item in observation.items:
                evidence_id = f"E{len(state.evidence) + 1}"
                state.evidence[evidence_id] = _Evidence(evidence_id, item, index)
                ids.append(evidence_id)
        state.observations.append(
            _ObservationRecord(index, operation, arguments, observation, None, tuple(ids))
        )
        state.events.append(
            {
                "event": "TOOL",
                "op": operation,
                "arguments": arguments,
                "status": observation.status.value,
                "items": len(observation.items),
                "omitted": observation.omitted_count,
                "digest": observation.digest.value,
            }
        )

    def _execute_tool(self, operation: str, arguments: Mapping[str, object]) -> SourceObservation:
        tools = self._tools
        if operation == "LIST_PATHS":
            return tools.list_paths(glob=_opt_str(arguments, "glob"), prefix=_opt_str(arguments, "prefix"))
        if operation == "SEARCH":
            return tools.search(
                _req_str(arguments, "pattern"),
                regex=bool(arguments.get("regex", False)),
                path_glob=_opt_str(arguments, "path_glob"),
                case_sensitive=arguments.get("case_sensitive", True) is not False,
                limit=60,
            )
        if operation == "READ":
            return tools.read(
                _req_str(arguments, "path"),
                start_line=_opt_int(arguments, "start_line") or 1,
                end_line=_opt_int(arguments, "end_line"),
            )
        if operation == "LOG":
            return tools.log(path=_opt_str(arguments, "path"), limit=20)
        if operation == "BLAME":
            start = _opt_int(arguments, "start_line") or 1
            end = _opt_int(arguments, "end_line") or start
            return tools.blame(_req_str(arguments, "path"), start_line=start, end_line=end)
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"unknown tool operation {operation}")

    # ----------------------------------------------------------------- review
    def _review_and_deliver(
        self,
        request: EngineeringTurnExecutionRequest,
        state: _TurnState,
        draft: Mapping[str, object],
    ) -> EngineeringTurnExecutionOutcome | None:
        verification: list[dict[str, object]] | None = None
        while True:
            if state.model_calls >= self._limits.maximum_model_calls:
                raise _TurnFailure("BUDGET_EXHAUSTED", "no model call remains for the independent review")
            view = self._review_view(request, state, draft, verification)
            output = self._model.review_draft(turn_request=request, view=view)
            state.receipts.append(output.receipt)
            try:
                verdict, findings, requests = _parse_review(output.payload)
            except DomainError as error:
                raise _TurnFailure("STRUCTURED_OUTPUT_INVALID", f"review output rejected: {error.message}")
            state.events.append({"event": "REVIEW", "verdict": verdict, "findings": list(findings)})
            if verdict == "VERIFY":
                if verification is not None or not requests:
                    raise _TurnFailure(
                        "STRUCTURED_OUTPUT_INVALID", "the reviewer may request one bounded verification round"
                    )
                verification = self._verify(requests)
                continue
            if verdict == "APPROVED":
                return self._deliver(request, state, draft, output.receipt)
            state.reviews += 1
            if state.reviews >= self._limits.maximum_reviews:
                raise _TurnFailure(
                    "REVIEW_NOT_APPROVED",
                    "the independent review did not approve the draft: " + "; ".join(findings[:5]),
                )
            prefix = "[MORE_EVIDENCE] " if verdict == "MORE_EVIDENCE" else "[REWRITE] "
            state.review_findings = [prefix + item for item in findings]
            state.previous_draft = str(draft["answer"])
            return None

    def _verify(self, requests: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
        results: list[dict[str, object]] = []
        for item in list(requests)[: self._limits.maximum_verification_reads]:
            operation = str(item["op"])
            arguments = {key: value for key, value in item.items() if key != "op" and value is not None}
            try:
                observation = self._execute_tool(operation, arguments)
                results.append(
                    {
                        "op": operation,
                        "arguments": arguments,
                        "status": observation.status.value,
                        "items": [
                            {"locator": entry.locator, "text": entry.text[: self._limits.maximum_item_characters]}
                            for entry in observation.items[:20]
                        ],
                    }
                )
            except DomainError as error:
                results.append({"op": operation, "arguments": arguments, "error": error.message})
        return results

    # ---------------------------------------------------------------- views
    def _history(self, request: EngineeringTurnExecutionRequest) -> list[dict[str, str]]:
        messages = request.snapshot_before.messages[-self._limits.maximum_history_messages :]
        return [
            {
                "role": item.role.value,
                "kind": item.kind.value,
                "content": item.content[: self._limits.maximum_history_characters],
            }
            for item in messages
        ]

    def _step_view(
        self, request: EngineeringTurnExecutionRequest, state: _TurnState, tools_enabled: bool
    ) -> dict[str, object]:
        remaining_calls = self._limits.maximum_model_calls - self._limits.reserved_review_calls - state.model_calls
        return {
            "schema": "SWM-CHAT-AGENT-STEP-INPUT@1",
            "project": {"name": request.binding.project_name, "revision": request.binding.repository_revision},
            "current_request": request.user_message.content,
            "conversation_history": self._history(request),
            "plan": state.plan,
            "tools_enabled": tools_enabled,
            "budget": {
                "model_steps_remaining": max(remaining_calls, 0),
                "tool_actions_remaining": self._limits.maximum_tool_actions - state.tool_actions,
                "maximum_actions_per_step": self._limits.maximum_actions_per_step,
            },
            "observations": self._observation_views(state),
            "feedback": list(state.feedback),
            "review_findings": list(state.review_findings),
            "previous_draft": state.previous_draft,
        }

    def _observation_views(self, state: _TurnState) -> list[dict[str, object]]:
        views: list[dict[str, object]] = []
        budget = self._limits.maximum_observation_characters
        for record in reversed(state.observations):
            view: dict[str, object] = {
                "index": record.index,
                "op": record.operation,
                "arguments": dict(record.arguments),
            }
            if record.error is not None:
                view["error"] = record.error
                views.append(view)
                continue
            observation = record.observation
            assert observation is not None
            view.update(
                {
                    "status": observation.status.value,
                    "coverage": observation.coverage,
                    "omitted_count": observation.omitted_count,
                    "notes": list(observation.notes),
                }
            )
            items: list[dict[str, object]] = []
            ids = list(record.evidence_ids) or [None] * len(observation.items)
            for evidence_id, item in zip(ids, observation.items):
                text = item.text[: self._limits.maximum_item_characters]
                entry: dict[str, object] = {"locator": item.locator}
                if evidence_id is not None:
                    entry["id"] = evidence_id
                if budget - len(text) > 0:
                    entry["text"] = text
                    budget -= len(text)
                elif text:
                    entry["text_elided"] = True
                items.append(entry)
            view["items"] = items
            views.append(view)
        return list(reversed(views))

    def _review_view(
        self,
        request: EngineeringTurnExecutionRequest,
        state: _TurnState,
        draft: Mapping[str, object],
        verification: list[dict[str, object]] | None,
    ) -> dict[str, object]:
        cited = [
            {
                "id": evidence_id,
                "locator": state.evidence[evidence_id].item.locator,
                "text": state.evidence[evidence_id].item.text[: self._limits.maximum_item_characters],
            }
            for evidence_id in draft["citations"]
        ]
        return {
            "schema": "SWM-CHAT-AGENT-REVIEW-INPUT@1",
            "project": {"name": request.binding.project_name, "revision": request.binding.repository_revision},
            "current_request": request.user_message.content,
            "conversation_history": self._history(request),
            "draft": {"kind": draft["kind"], "answer": draft["answer"]},
            "cited_evidence": cited,
            "investigation_summary": [
                {
                    "op": record.operation,
                    "arguments": dict(record.arguments),
                    "status": record.observation.status.value if record.observation else "ERROR",
                    "coverage": record.observation.coverage if record.observation else record.error,
                }
                for record in state.observations
            ],
            "verification_allowed": verification is None,
            "verification_results": verification,
        }

    # -------------------------------------------------------------- delivery
    def _deliver(
        self,
        request: EngineeringTurnExecutionRequest,
        state: _TurnState,
        draft: Mapping[str, object],
        review_receipt: EngineeringAgentModelCallReceipt,
    ) -> EngineeringTurnExecutionOutcome:
        revision = request.binding.repository_revision
        citations = tuple(
            EngineeringAgentCitation.create(
                citation_ref=f"{request.turn_id.value}:{evidence_id}",
                evidence_class="SOURCE",
                source_revision=revision,
                locator=state.evidence[evidence_id].item.locator,
                modality="EXACT_STATIC_SOURCE_TEXT",
                content_digest=Digest(state.evidence[evidence_id].item.content_digest),
            )
            for evidence_id in dict.fromkeys(draft["citations"])
        )
        answer = str(draft["answer"]).strip()
        kind = LightweightAgentResponseKind(str(draft["kind"]))
        evidence_ref = digest_of(
            ["SWM-CHAT-AGENT-EVIDENCE-PACKAGE@1", [item.digest.value for item in citations]]
        ).value
        answer_ref = digest_of(["SWM-CHAT-AGENT-ANSWER@1", request.request_digest.value, answer]).value
        review = LightweightReview(verdict=LightweightReviewVerdict.APPROVED, findings=())
        review_ref = digest_of(["SWM-CHAT-AGENT-REVIEW@1", answer_ref, review_receipt.digest.value]).value
        authorization = self._delivery.authorize(
            LightweightDeliveryRequest(
                turn_request=request,
                response_kind=kind,
                answer=answer,
                answer_ref=answer_ref,
                review=review,
                review_ref=review_ref,
                review_receipt=review_receipt,
                citations=citations,
            )
        )
        before = request.snapshot_before.context
        work_ref = before.work_state_ref or (
            "chat-agent-state:" + request.snapshot_before.conversation.conversation_id.value
        )
        work_revision = (
            Revision(1) if before.work_state_ref is None else Revision(before.work_state_revision.value + 1)
        )
        work_digest = digest_of(
            {
                "schema": "SWM-CHAT-AGENT-WORK-STATE@1",
                "work_ref": work_ref,
                "revision": work_revision.value,
                "plan": state.plan,
                "answer_ref": answer_ref,
                "delivery_authorization_ref": authorization.digest.value,
            }
        )
        message_kind = ConversationMessageKind(kind.value)
        reviewed_refs = before.reviewed_conclusion_refs
        if message_kind is ConversationMessageKind.ANSWER:
            reviewed_refs = (*reviewed_refs, answer_ref)
        state.events.append({"event": "DELIVERED", "kind": kind.value, "citations": len(citations)})
        self._record_trace(request, state, "DELIVERED", answer=answer, citations=citations)
        return EngineeringTurnExecutionOutcome.succeeded(
            request_digest=request.request_digest,
            assistant_kind=message_kind,
            assistant_content=answer,
            included_user_message_ids=(*before.included_user_message_ids, request.user_message.message_id),
            accepted_correction_message_ids=before.accepted_correction_message_ids,
            reviewed_conclusion_refs=reviewed_refs,
            superseded_conclusion_refs=before.superseded_conclusion_refs,
            reducer_status="CHAT_AGENT_CONTEXT_COMMITTED",
            work_state_ref=work_ref,
            work_state_revision=work_revision,
            work_state_digest=work_digest,
            evidence_package_ref=evidence_ref,
            answer_ref=answer_ref,
            review_ref=review_ref,
            delivery_authorization_ref=authorization.digest.value,
            provider_dispatch_count=sum(item.provider_dispatch_count for item in state.receipts),
            model_dispatch_receipt_refs=tuple(item.digest.value for item in state.receipts),
            citations=tuple(
                EngineeringTurnCitation.create(
                    citation_ref=item.citation_ref,
                    evidence_class=item.evidence_class,
                    source_revision=item.source_revision,
                    locator=item.locator,
                    modality=item.modality,
                    content_digest=item.content_digest,
                )
                for item in citations
            ),
            quality_status={
                ConversationMessageKind.ANSWER: "ACCEPTED",
                ConversationMessageKind.CLARIFICATION: "REVIEWED_CLARIFICATION",
                ConversationMessageKind.LIMITATION: "REVIEWED_LIMITATION",
            }[message_kind],
        )

    def _finish_failure(
        self,
        request: EngineeringTurnExecutionRequest,
        state: _TurnState,
        code: str,
        message: str,
        model_failure: EngineeringAgentModelFailureKind | None,
    ) -> EngineeringTurnExecutionOutcome:
        classification = {
            EngineeringAgentModelFailureKind.PROVIDER_UNAVAILABLE: EngineeringProviderFailureClassification.PROVIDER_UNAVAILABLE,
            EngineeringAgentModelFailureKind.PROVIDER_HTTP_ERROR: EngineeringProviderFailureClassification.PROVIDER_HTTP_ERROR,
            EngineeringAgentModelFailureKind.PROVIDER_OUTCOME_UNKNOWN: EngineeringProviderFailureClassification.PROVIDER_OUTCOME_UNKNOWN,
            EngineeringAgentModelFailureKind.PROVIDER_OUTPUT_INVALID: EngineeringProviderFailureClassification.PROVIDER_OUTPUT_INVALID,
        }.get(model_failure)
        state.events.append({"event": "FAILED", "code": code, "message": message})
        self._record_trace(request, state, "FAILED")
        before = request.snapshot_before.context
        return EngineeringTurnExecutionOutcome.failed(
            request_digest=request.request_digest,
            assistant_content=(
                "本轮未能形成经独立复核的答案（" + code + "）："
                + message
                + "。对话仍可继续，可以换个问法或缩小范围再问。"
            ),
            included_user_message_ids=(*before.included_user_message_ids, request.user_message.message_id),
            accepted_correction_message_ids=before.accepted_correction_message_ids,
            reviewed_conclusion_refs=before.reviewed_conclusion_refs,
            superseded_conclusion_refs=before.superseded_conclusion_refs,
            reducer_status="CHAT_AGENT_FAILED_CLOSED",
            work_state_ref=before.work_state_ref,
            work_state_revision=before.work_state_revision if before.work_state_ref else None,
            work_state_digest=before.work_state_digest,
            failure_code=code,
            failure_message=message,
            provider_dispatch_count=sum(item.provider_dispatch_count for item in state.receipts),
            model_dispatch_receipt_refs=tuple(item.digest.value for item in state.receipts),
            provider_failure_classification=classification,
            provider_failure_code=code if classification is not None else None,
            provider_http_status=None,
            provider_http_failure_evidence_digest=None,
        )

    # ------------------------------------------------------------ Turn Trace
    def _record_trace(
        self,
        request: EngineeringTurnExecutionRequest,
        state: _TurnState,
        terminal: str,
        *,
        answer: str | None = None,
        citations: Sequence[EngineeringAgentCitation] = (),
    ) -> None:
        events = tuple(state.events)
        trajectory = LightweightAgentTrajectory(
            attempt_ref=self._attempt_ref,
            turn_request_digest=request.request_digest,
            mode=CHAT_AGENT_MODE,
            events=events,
            terminal_status=terminal,
            digest=digest_of(
                ["SWM-CHAT-AGENT-TRAJECTORY@1", self._attempt_ref, request.request_digest.value, events, terminal]
            ),
        )
        self._traces.record(trajectory)
        if self._trace_directory is None:
            return
        # Non-authoritative Turn Trace (baseline 10.2): retained for audit,
        # evaluation replay and crystallization; never read by later Turns.
        record = {
            "schema": "SWM-TURN-TRACE@1",
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            "conversation_id": request.snapshot_before.conversation.conversation_id.value,
            "turn_id": request.turn_id.value,
            "request_digest": request.request_digest.value,
            "revision": request.binding.repository_revision,
            "question": request.user_message.content,
            "terminal": terminal,
            "answer": answer,
            "citations": [item.locator for item in citations],
            "events": list(events),
            "evidence": {
                key: {"locator": value.item.locator, "text": value.item.text}
                for key, value in state.evidence.items()
            },
            "model_calls": state.model_calls,
            "tool_actions": state.tool_actions,
        }
        try:
            directory = self._trace_directory / record["conversation_id"]
            directory.mkdir(parents=True, exist_ok=True)
            (directory / f"{record['turn_id']}.json").write_text(
                json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except OSError:
            # Trace retention is best effort and must never change the answer.
            pass


# ---------------------------------------------------------------- parsing
def _parse_step(
    payload: Mapping[str, object], limits: ChatAgentLimits
) -> tuple[str, list[dict[str, object]], dict[str, object] | None]:
    if not isinstance(payload, Mapping):
        raise DomainError(ErrorCode.STRUCTURED_OUTPUT_INVALID, "step must be an object")
    plan = payload.get("plan")
    if not isinstance(plan, str):
        raise DomainError(ErrorCode.STRUCTURED_OUTPUT_INVALID, "plan must be text")
    raw_actions = payload.get("actions")
    if not isinstance(raw_actions, list):
        raise DomainError(ErrorCode.STRUCTURED_OUTPUT_INVALID, "actions must be an array")
    actions: list[dict[str, object]] = []
    for raw in raw_actions:
        if not isinstance(raw, Mapping) or raw.get("op") not in TOOL_OPERATIONS:
            raise DomainError(ErrorCode.STRUCTURED_OUTPUT_INVALID, "each action needs a registered op")
        actions.append(dict(raw))
    if len(actions) > limits.maximum_actions_per_step:
        raise DomainError(
            ErrorCode.STRUCTURED_OUTPUT_INVALID,
            f"at most {limits.maximum_actions_per_step} actions per step",
        )
    raw_final = payload.get("final")
    final: dict[str, object] | None = None
    if raw_final is not None:
        if not isinstance(raw_final, Mapping) or raw_final.get("kind") not in FINAL_KINDS:
            raise DomainError(ErrorCode.STRUCTURED_OUTPUT_INVALID, "final needs a registered kind")
        answer = raw_final.get("answer")
        citations = raw_final.get("citations")
        if not isinstance(answer, str) or not answer.strip():
            raise DomainError(ErrorCode.STRUCTURED_OUTPUT_INVALID, "final answer must be non-empty text")
        if not isinstance(citations, list) or not all(isinstance(item, str) for item in citations):
            raise DomainError(ErrorCode.STRUCTURED_OUTPUT_INVALID, "citations must be evidence ids")
        if actions:
            raise DomainError(ErrorCode.STRUCTURED_OUTPUT_INVALID, "a final response cannot also request tools")
        final = {"kind": raw_final["kind"], "answer": answer.strip(), "citations": list(dict.fromkeys(citations))}
    return plan, actions, final


def _parse_review(
    payload: Mapping[str, object],
) -> tuple[str, list[str], list[dict[str, object]]]:
    if not isinstance(payload, Mapping) or payload.get("verdict") not in REVIEW_VERDICTS:
        raise DomainError(ErrorCode.STRUCTURED_OUTPUT_INVALID, "review verdict is not registered")
    findings = payload.get("findings")
    if not isinstance(findings, list) or not all(isinstance(item, str) and item.strip() for item in findings):
        raise DomainError(ErrorCode.STRUCTURED_OUTPUT_INVALID, "findings must be text")
    verdict = str(payload["verdict"])
    if (verdict == "APPROVED") != (not findings) and verdict != "VERIFY":
        raise DomainError(ErrorCode.STRUCTURED_OUTPUT_INVALID, "APPROVED requires no findings and vice versa")
    requests = payload.get("verification_requests") or []
    if not isinstance(requests, list):
        raise DomainError(ErrorCode.STRUCTURED_OUTPUT_INVALID, "verification requests must be an array")
    parsed: list[dict[str, object]] = []
    for item in requests:
        if not isinstance(item, Mapping) or item.get("op") not in VERIFY_OPERATIONS:
            raise DomainError(ErrorCode.STRUCTURED_OUTPUT_INVALID, "verification may only READ or SEARCH")
        parsed.append(dict(item))
    if verdict != "VERIFY" and parsed:
        raise DomainError(ErrorCode.STRUCTURED_OUTPUT_INVALID, "verification requests need the VERIFY verdict")
    return verdict, [item.strip() for item in findings], parsed


def _opt_str(arguments: Mapping[str, object], key: str) -> str | None:
    value = arguments.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{key} must be text")
    return value


def _req_str(arguments: Mapping[str, object], key: str) -> str:
    value = _opt_str(arguments, key)
    if value is None:
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{key} is required")
    return value


def _opt_int(arguments: Mapping[str, object], key: str) -> int | None:
    value = arguments.get(key)
    if value is None:
        return None
    if type(value) is not int:
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{key} must be an integer")
    return value


__all__ = [
    "CHAT_AGENT_MODE",
    "ChatAgentLimits",
    "ChatAgentModel",
    "ChatAgentTurnExecutor",
    "ChatModelOutput",
]
