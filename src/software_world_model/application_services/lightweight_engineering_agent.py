"""Capability-oriented Application loop for an evidence-seeking Agent.

The model keeps a goal and plan, proposes one read-only action at a time, sees
the trusted observation, and either replans or finishes.  Source access and
delivery remain Application owned; the model receives neither a filesystem nor
opaque tool authority identifiers.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from threading import Lock
from typing import Mapping, Protocol, Sequence

from software_world_model.cross_cutting import (
    canonical_json_bytes,
    Digest,
    DomainError,
    ErrorCode,
    IdGenerator,
    Revision,
    StableId,
    Uuid4IdGenerator,
    digest_of,
)
from software_world_model.knowledge_engine.capability_cognition import (
    CapabilityCognitionIndex,
    CognitionDirection,
    CognitionEntityKind,
    CognitionPage,
    CognitionProvenance,
    CognitionRelationKind,
)

from .conversational_engineering_agent import (
    EngineeringAgentCitation,
    EngineeringAgentEvidenceDisposition,
    EngineeringAgentLoopLimits,
    EngineeringAgentModelCallReceipt,
    EngineeringAgentModelFailureKind,
    EngineeringAgentModelRole,
    EngineeringAgentToolActionProposal,
    EngineeringAgentToolOperation,
    EngineeringAgentToolPort,
    EngineeringAgentToolRequest,
)
from .engineering_conversation import (
    ConversationMessageKind,
    EngineeringConversationTurnExecutor,
    EngineeringProviderFailureClassification,
    EngineeringTurnCitation,
    EngineeringTurnExecutionOutcome,
    EngineeringTurnExecutionRequest,
)


class LightweightAgentAction(str, Enum):
    SEARCH_COGNITION = "SEARCH_COGNITION"
    TRAVERSE_RELATIONS = "TRAVERSE_RELATIONS"
    RETRIEVE_COGNITION_DETAIL = "RETRIEVE_COGNITION_DETAIL"
    SEARCH_SOURCE = "SEARCH_SOURCE"
    READ_SOURCE = "READ_SOURCE"
    FINISH = "FINISH"


class LightweightAgentResponseKind(str, Enum):
    ANSWER = "ANSWER"
    CLARIFICATION = "CLARIFICATION"
    LIMITATION = "LIMITATION"


class LightweightReviewVerdict(str, Enum):
    APPROVED = "APPROVED"
    REWRITE = "REWRITE"
    MORE_EVIDENCE = "MORE_EVIDENCE"


@dataclass(frozen=True, slots=True)
class LightweightCitationSelection:
    observation_index: int
    citation_index: int


@dataclass(frozen=True, slots=True)
class LightweightAgentDecision:
    goal: str
    plan: str
    action: LightweightAgentAction
    query: str | None
    read_index: int | None
    response_kind: LightweightAgentResponseKind | None
    answer: str | None
    citations: tuple[LightweightCitationSelection, ...]
    cognition_index: int | None = None
    relation_kind: CognitionRelationKind | None = None
    direction: CognitionDirection | None = None
    maximum_depth: int | None = None
    cursor: int | None = None

    @classmethod
    def from_payload(
        cls, payload: Mapping[str, object]
    ) -> "LightweightAgentDecision":
        fields = {
            "goal",
            "plan",
            "action",
            "query",
            "read_index",
            "cognition_index",
            "relation_kind",
            "direction",
            "maximum_depth",
            "cursor",
            "response_kind",
            "answer",
            "citations",
        }
        if set(payload) != fields:
            _invalid("lightweight Agent decision has an invalid field set")
        goal = _text(payload["goal"], "Agent goal")
        plan = _text(payload["plan"], "Agent plan")
        try:
            action = LightweightAgentAction(payload["action"])
        except (TypeError, ValueError) as exc:
            raise DomainError(
                ErrorCode.STRUCTURED_OUTPUT_INVALID,
                "lightweight Agent action is not registered",
            ) from exc
        query = _optional_text(payload["query"], "Source query")
        read_index = payload["read_index"]
        cognition_index = payload["cognition_index"]
        raw_relation_kind = payload["relation_kind"]
        raw_direction = payload["direction"]
        maximum_depth = payload["maximum_depth"]
        cursor = payload["cursor"]
        raw_kind = payload["response_kind"]
        answer = _optional_text(payload["answer"], "Agent answer")
        raw_citations = payload["citations"]
        if not isinstance(raw_citations, list):
            _invalid("lightweight Agent citations must be an array")
        citations: list[LightweightCitationSelection] = []
        for item in raw_citations:
            if (
                not isinstance(item, dict)
                or set(item) != {"observation_index", "citation_index"}
                or type(item["observation_index"]) is not int
                or item["observation_index"] < 1
                or type(item["citation_index"]) is not int
                or item["citation_index"] < 1
            ):
                _invalid("lightweight Agent citation selection is invalid")
            citations.append(
                LightweightCitationSelection(
                    item["observation_index"], item["citation_index"]
                )
            )
        if len(citations) != len(set(citations)):
            _invalid("lightweight Agent citation selections must be unique")
        response_kind: LightweightAgentResponseKind | None = None
        relation_kind = None
        if raw_relation_kind is not None:
            try:
                relation_kind = CognitionRelationKind(raw_relation_kind)
            except (TypeError, ValueError):
                _invalid("cognition relation kind is not registered")
        direction = None
        if raw_direction is not None:
            try:
                direction = CognitionDirection(raw_direction)
            except (TypeError, ValueError):
                _invalid("cognition direction is not registered")
        base_tool_fields = (
            raw_kind is None and answer is None and not citations
        )
        if action in {
            LightweightAgentAction.SEARCH_SOURCE,
            LightweightAgentAction.SEARCH_COGNITION,
        }:
            valid = (
                query is not None
                and read_index is None
                and cognition_index is None
                and relation_kind is None
                and direction is None
                and maximum_depth is None
                and (cursor is None or (type(cursor) is int and cursor >= 0))
                and base_tool_fields
            )
        elif action is LightweightAgentAction.READ_SOURCE:
            valid = (
                query is None
                and type(read_index) is int
                and read_index >= 1
                and cognition_index is None
                and relation_kind is None
                and direction is None
                and maximum_depth is None
                and cursor is None
                and base_tool_fields
            )
        elif action is LightweightAgentAction.TRAVERSE_RELATIONS:
            valid = (
                query is None
                and read_index is None
                and type(cognition_index) is int
                and cognition_index >= 1
                and direction is not None
                and type(maximum_depth) is int
                and 1 <= maximum_depth <= 4
                and (cursor is None or (type(cursor) is int and cursor >= 0))
                and base_tool_fields
            )
        elif action is LightweightAgentAction.RETRIEVE_COGNITION_DETAIL:
            valid = (
                query is None
                and read_index is None
                and type(cognition_index) is int
                and cognition_index >= 1
                and relation_kind is None
                and direction is None
                and maximum_depth is None
                and (cursor is None or (type(cursor) is int and cursor >= 0))
                and base_tool_fields
            )
        else:
            try:
                response_kind = LightweightAgentResponseKind(raw_kind)
            except (TypeError, ValueError):
                response_kind = None
            valid = (
                query is None
                and read_index is None
                and cognition_index is None
                and relation_kind is None
                and direction is None
                and maximum_depth is None
                and cursor is None
                and response_kind is not None
                and answer is not None
                and (
                    response_kind is not LightweightAgentResponseKind.ANSWER
                    or bool(citations)
                )
            )
        if not valid:
            raise LightweightAgentDecisionBranchError()
        return cls(
            goal=goal,
            plan=plan,
            action=action,
            query=query,
            read_index=read_index if type(read_index) is int else None,
            cognition_index=(
                cognition_index if type(cognition_index) is int else None
            ),
            relation_kind=relation_kind,
            direction=direction,
            maximum_depth=(
                maximum_depth if type(maximum_depth) is int else None
            ),
            cursor=cursor if type(cursor) is int else None,
            response_kind=response_kind,
            answer=answer,
            citations=tuple(citations),
        )


class LightweightAgentDecisionBranchError(DomainError):
    """A parseable decision whose fields do not match its selected action.

    The typed decoder remains strict. The executor may use this classification
    to give the same primary Agent one bounded next-step opportunity while
    retaining the rejected Provider receipt and raw output. Other structured
    output failures stay fail-closed.
    """

    def __init__(self) -> None:
        super().__init__(
            ErrorCode.STRUCTURED_OUTPUT_INVALID,
            "lightweight Agent decision branches are inconsistent",
        )


@dataclass(frozen=True, slots=True)
class LightweightReview:
    verdict: LightweightReviewVerdict
    findings: tuple[str, ...]

    @classmethod
    def from_payload(cls, payload: Mapping[str, object]) -> "LightweightReview":
        if set(payload) != {"verdict", "findings"}:
            _invalid("lightweight review has an invalid field set")
        try:
            verdict = LightweightReviewVerdict(payload["verdict"])
        except (TypeError, ValueError) as exc:
            raise DomainError(
                ErrorCode.STRUCTURED_OUTPUT_INVALID,
                "lightweight review verdict is not registered",
            ) from exc
        raw_findings = payload["findings"]
        if not isinstance(raw_findings, list):
            _invalid("lightweight review findings must be an array")
        findings = tuple(_text(item, "review finding") for item in raw_findings)
        if len(findings) != len(set(findings)) or (
            (verdict is LightweightReviewVerdict.APPROVED) != (not findings)
        ):
            _invalid("lightweight review verdict and findings disagree")
        return cls(verdict=verdict, findings=findings)


@dataclass(frozen=True, slots=True)
class LightweightReadCandidate:
    read_index: int
    citation: EngineeringAgentCitation
    resource_locator: str

    def model_view(self) -> dict[str, object]:
        return {
            "read_index": self.read_index,
            "locator": self.citation.locator,
            "modality": self.citation.modality,
            "source_revision": self.citation.source_revision,
        }


@dataclass(frozen=True, slots=True)
class LightweightCognitionCandidate:
    cognition_index: int
    entity_id: StableId
    kind: CognitionEntityKind
    name: str
    qualified_name: str
    coverage: str
    unknowns: tuple[str, ...]
    provenance: CognitionProvenance

    def model_view(self) -> dict[str, object]:
        return {
            "cognition_index": self.cognition_index,
            "kind": self.kind.value,
            "name": self.name,
            "qualified_name": self.qualified_name,
            "coverage": self.coverage,
            "unknowns": list(self.unknowns),
            "locator": self.provenance.locator,
        }


@dataclass(frozen=True, slots=True)
class LightweightObservation:
    observation_index: int
    operation: EngineeringAgentToolOperation | LightweightAgentAction
    disposition: EngineeringAgentEvidenceDisposition
    content: str
    progress: bool
    citations: tuple[EngineeringAgentCitation, ...]
    digest: Digest

    def model_view(self) -> dict[str, object]:
        return {
            "observation_index": self.observation_index,
            "operation": self.operation.value,
            "disposition": self.disposition.value,
            "progress": self.progress,
            "content": self.content,
            "citations": [
                {
                    "citation_index": index,
                    "locator": citation.locator,
                    "modality": citation.modality,
                    "source_revision": citation.source_revision,
                }
                for index, citation in enumerate(self.citations, 1)
            ],
        }


@dataclass(frozen=True, slots=True)
class LightweightAgentStepRequest:
    turn_request: EngineeringTurnExecutionRequest
    step: int
    goal: str
    plan: str
    observations: tuple[LightweightObservation, ...]
    read_candidates: tuple[LightweightReadCandidate, ...]
    tools_enabled: bool
    cognition_candidates: tuple[LightweightCognitionCandidate, ...] = ()
    cognition_enabled: bool = False
    rejected_answer: str | None = None
    review_findings: tuple[str, ...] = ()

    def model_view(self) -> dict[str, object]:
        return {
            "mode": (
                "WORLD_MODEL_PLUS_SOURCE"
                if self.cognition_enabled
                else "SOURCE_ONLY"
            ),
            "repository": {
                "project": self.turn_request.binding.project_name,
                "revision": self.turn_request.binding.repository_revision,
            },
            "current_request": self.turn_request.user_message.content,
            "conversation_history": [
                {
                    "role": item.role.value,
                    "kind": item.kind.value,
                    "content": item.content,
                }
                for item in self.turn_request.snapshot_before.messages
            ],
            "step": self.step,
            "goal": self.goal,
            "plan": self.plan,
            "tools_enabled": self.tools_enabled,
            "available_actions": (
                [
                    "SEARCH_COGNITION",
                    "TRAVERSE_RELATIONS",
                    "RETRIEVE_COGNITION_DETAIL",
                    "SEARCH_SOURCE",
                    "READ_SOURCE",
                    "FINISH",
                ]
                if self.tools_enabled and self.cognition_enabled
                else ["SEARCH_SOURCE", "READ_SOURCE", "FINISH"]
                if self.tools_enabled
                else ["FINISH"]
            ),
            "read_candidates": [item.model_view() for item in self.read_candidates],
            "cognition_candidates": [
                item.model_view() for item in self.cognition_candidates
            ],
            "observations": [item.model_view() for item in self.observations],
            "rejected_answer": self.rejected_answer,
            "review_findings": list(self.review_findings),
        }


@dataclass(frozen=True, slots=True)
class LightweightReviewRequest:
    turn_request: EngineeringTurnExecutionRequest
    answer: str
    response_kind: LightweightAgentResponseKind
    observations: tuple[LightweightObservation, ...]
    citations: tuple[EngineeringAgentCitation, ...]

    def model_view(self) -> dict[str, object]:
        selected = {item.citation_ref for item in self.citations}
        return {
            "repository_revision": self.turn_request.binding.repository_revision,
            "original_request": self.turn_request.user_message.content,
            "conversation_history": [
                {"role": item.role.value, "content": item.content}
                for item in self.turn_request.snapshot_before.messages
            ],
            "response_kind": self.response_kind.value,
            "answer": self.answer,
            "citations": [
                {
                    "locator": item.locator,
                    "modality": item.modality,
                    "source_revision": item.source_revision,
                }
                for item in self.citations
            ],
            "cited_evidence": [
                item.model_view()
                for item in self.observations
                if any(citation.citation_ref in selected for citation in item.citations)
            ],
        }


@dataclass(frozen=True, slots=True)
class LightweightDecisionResult:
    decision: LightweightAgentDecision
    receipt: EngineeringAgentModelCallReceipt
    disclosure_record_ref: str


@dataclass(frozen=True, slots=True)
class LightweightReviewResult:
    review: LightweightReview
    receipt: EngineeringAgentModelCallReceipt
    disclosure_record_ref: str


class LightweightModelCallFailure(DomainError):
    def __init__(
        self,
        *,
        receipt: EngineeringAgentModelCallReceipt,
        code: ErrorCode,
        message: str,
        disclosure_record_ref: str,
        bounded_replan_allowed: bool = False,
    ) -> None:
        super().__init__(code, message)
        self.receipt = receipt
        self.disclosure_record_ref = disclosure_record_ref
        self.bounded_replan_allowed = bounded_replan_allowed


class _CitationBindingRejection(DomainError):
    """A mechanical FINISH selection that is not in the current evidence domain.

    This remains an Application-owned rejection.  It carries only the selected
    ordinals and the size of the sealed observation domain so the primary Agent
    can replan once without turning a cognition observation into a Citation.
    """

    def __init__(
        self,
        *,
        observation_index: int,
        citation_index: int,
        available_citation_count: int,
    ) -> None:
        super().__init__(
            ErrorCode.CONTROL_STATE_DENIED,
            "response selected a Citation outside delivered evidence",
        )
        self.observation_index = observation_index
        self.citation_index = citation_index
        self.available_citation_count = available_citation_count


class LightweightEngineeringModel(Protocol):
    @property
    def instance_ref(self) -> str: ...

    def decide(self, request: LightweightAgentStepRequest) -> LightweightDecisionResult: ...

    def review(self, request: LightweightReviewRequest) -> LightweightReviewResult: ...


@dataclass(frozen=True, slots=True)
class LightweightDeliveryRequest:
    turn_request: EngineeringTurnExecutionRequest
    response_kind: LightweightAgentResponseKind
    answer: str
    answer_ref: str
    review: LightweightReview
    review_ref: str
    review_receipt: EngineeringAgentModelCallReceipt
    citations: tuple[EngineeringAgentCitation, ...]


@dataclass(frozen=True, slots=True)
class LightweightDeliveryAuthorization:
    request_digest: Digest
    answer_ref: str
    review_ref: str
    citation_digests: tuple[Digest, ...]
    digest: Digest


class SealedLightweightDeliveryControl:
    """One-use Application authority for a reviewed exact-revision response."""

    def __init__(self) -> None:
        self._authorized_turns: set[Digest] = set()
        self._lock = Lock()

    def authorize(
        self, request: LightweightDeliveryRequest
    ) -> LightweightDeliveryAuthorization:
        turn = request.turn_request
        receipt = request.review_receipt
        citations = tuple(request.citations)
        if (
            request.review.verdict is not LightweightReviewVerdict.APPROVED
            or request.review.findings
            or not receipt.successful
            or receipt.role is not EngineeringAgentModelRole.INDEPENDENT_REVIEWER
            or not request.answer.strip()
            or request.answer != request.answer.strip()
            or not request.answer_ref
            or not request.review_ref
            or (
                request.response_kind is LightweightAgentResponseKind.ANSWER
                and not citations
            )
        ):
            raise DomainError(
                ErrorCode.CONTROL_STATE_DENIED,
                "delivery requires a fresh approved review and grounded response",
            )
        for citation in citations:
            expected = EngineeringAgentCitation.create(
                citation_ref=citation.citation_ref,
                evidence_class=citation.evidence_class,
                source_revision=citation.source_revision,
                locator=citation.locator,
                modality=citation.modality,
                content_digest=citation.content_digest,
            )
            if citation != expected or citation.source_revision != (
                turn.binding.repository_revision
            ):
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "delivery Citation is not bound to the exact Source revision",
                )
        refs = tuple(item.citation_ref for item in citations)
        if len(refs) != len(set(refs)):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "delivery Citations must have unique authority identities",
            )
        core = {
            "schema": "SWM-LIGHTWEIGHT-DELIVERY-AUTHORIZATION@1",
            "turn_request_digest": turn.request_digest.value,
            "answer_ref": request.answer_ref,
            "review_ref": request.review_ref,
            "review_receipt_digest": receipt.digest.value,
            "citation_digests": tuple(item.digest.value for item in citations),
            "source_revision": turn.binding.repository_revision,
            "decision": "ALLOW",
        }
        with self._lock:
            if turn.request_digest in self._authorized_turns:
                raise DomainError(
                    ErrorCode.CONTROL_STATE_DENIED,
                    "a Turn cannot consume delivery authority twice",
                )
            self._authorized_turns.add(turn.request_digest)
        return LightweightDeliveryAuthorization(
            request_digest=turn.request_digest,
            answer_ref=request.answer_ref,
            review_ref=request.review_ref,
            citation_digests=tuple(item.digest for item in citations),
            digest=digest_of(core),
        )


@dataclass(frozen=True, slots=True)
class LightweightAgentTrajectory:
    attempt_ref: str
    turn_request_digest: Digest
    mode: str
    events: tuple[Mapping[str, object], ...]
    terminal_status: str
    digest: Digest

    def public_view(self) -> dict[str, object]:
        return {
            "attempt_ref": self.attempt_ref,
            "turn_request_digest": self.turn_request_digest.value,
            "mode": self.mode,
            "events": list(self.events),
            "terminal_status": self.terminal_status,
            "digest": self.digest.value,
        }


class LightweightAgentTraceStore:
    def __init__(self) -> None:
        self._items: dict[Digest, list[LightweightAgentTrajectory]] = {}
        self._lock = Lock()

    def record(self, trajectory: LightweightAgentTrajectory) -> None:
        with self._lock:
            self._items.setdefault(trajectory.turn_request_digest, []).append(
                trajectory
            )

    def for_turn(self, request_digest: Digest) -> tuple[LightweightAgentTrajectory, ...]:
        with self._lock:
            return tuple(self._items.get(request_digest, ()))


class ApplicationOwnedLightweightAgentTurnExecutor(
    EngineeringConversationTurnExecutor
):
    """Run one bounded source or cognition-plus-source investigation."""

    def __init__(
        self,
        *,
        model: LightweightEngineeringModel,
        tool_port: EngineeringAgentToolPort,
        delivery_control: SealedLightweightDeliveryControl,
        trace_store: LightweightAgentTraceStore,
        attempt_ref: str,
        capability_cognition: CapabilityCognitionIndex | None = None,
        limits: EngineeringAgentLoopLimits = EngineeringAgentLoopLimits(),
        id_generator: IdGenerator | None = None,
    ) -> None:
        if (
            not callable(getattr(model, "decide", None))
            or not callable(getattr(model, "review", None))
            or not callable(getattr(tool_port, "execute", None))
            or not callable(getattr(tool_port, "source_read_options", None))
            or (
                capability_cognition is not None
                and not callable(
                    getattr(tool_port, "cognition_source_read_options", None)
                )
            )
            or not callable(getattr(delivery_control, "authorize", None))
            or (
                capability_cognition is not None
                and not isinstance(capability_cognition, CapabilityCognitionIndex)
            )
        ):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "lightweight Agent requires model, read-only tool, and delivery ports",
            )
        self._model = model
        self._tool = tool_port
        self._delivery = delivery_control
        self._traces = trace_store
        self._attempt_ref = _text(attempt_ref, "attempt reference")
        self._cognition = capability_cognition
        self._limits = limits
        self._ids = id_generator or Uuid4IdGenerator()

    def execute(
        self, request: EngineeringTurnExecutionRequest
    ) -> EngineeringTurnExecutionOutcome:
        goal = request.user_message.content
        plan = "Investigate the exact request and stop when the evidence is sufficient."
        observations: list[LightweightObservation] = []
        read_candidates: list[LightweightReadCandidate] = []
        cognition_candidates: list[LightweightCognitionCandidate] = []
        receipts: list[EngineeringAgentModelCallReceipt] = []
        events: list[Mapping[str, object]] = []
        rejected_answer: str | None = None
        review_findings: tuple[str, ...] = ()
        tool_actions = 0
        reviews = 0
        rewrites = 0
        citation_binding_repairs = 0
        decision_shape_repairs = 0
        consecutive_no_progress = 0
        terminal = "FAILED"
        try:
            read_candidates.extend(self._prior_turn_read_candidates(request))
            for step in range(1, self._limits.maximum_agent_steps + 1):
                tools_enabled = tool_actions < self._limits.maximum_tool_actions
                try:
                    result = self._model.decide(
                        LightweightAgentStepRequest(
                            turn_request=request,
                            step=step,
                            goal=goal,
                            plan=plan,
                            observations=tuple(observations),
                            read_candidates=tuple(read_candidates),
                            cognition_candidates=tuple(cognition_candidates),
                            cognition_enabled=self._cognition is not None,
                            tools_enabled=tools_enabled,
                            rejected_answer=rejected_answer,
                            review_findings=review_findings,
                        )
                    )
                except LightweightModelCallFailure as exc:
                    if (
                        exc.bounded_replan_allowed
                        and decision_shape_repairs < 1
                    ):
                        self._record_receipt(receipts, exc.receipt)
                        decision_shape_repairs += 1
                        events.append(
                            {
                                "kind": "MODEL_DECISION_SHAPE_REJECTION",
                                "step": step,
                                "failure_code": exc.code.value,
                                "model_call_receipt_ref": exc.receipt.digest.value,
                                "disclosure_record_ref": exc.disclosure_record_ref,
                                "repair_ordinal": decision_shape_repairs,
                            }
                        )
                        # Preserve any answer and findings already rejected by
                        # Citation binding or an independent review.  The
                        # shape diagnosis is mechanical and is appended to
                        # that existing feedback so the next request can
                        # address every known defect in one pass.
                        review_findings = (
                            *review_findings,
                            "Application rejected the previous Agent decision "
                            "because fields unused by its selected action were "
                            "not null. Replan with the same observations and "
                            "set every field not used by the selected action to "
                            "null; do not alter evidence or answer semantics.",
                        )
                        continue
                    raise
                self._record_receipt(receipts, result.receipt)
                decision = result.decision
                if not tools_enabled and decision.action is not LightweightAgentAction.FINISH:
                    raise DomainError(
                        ErrorCode.BUDGET_EXHAUSTED,
                        "lightweight Agent did not stop after its tool budget closed",
                    )
                goal, plan = decision.goal, decision.plan
                events.append(
                    {
                        "kind": "MODEL_DECISION",
                        "step": step,
                        "goal": goal,
                        "plan": plan,
                        "action": decision.action.value,
                        "query": decision.query,
                        "read_index": decision.read_index,
                        "cognition_index": decision.cognition_index,
                        "relation_kind": (
                            decision.relation_kind.value
                            if decision.relation_kind is not None
                            else None
                        ),
                        "direction": (
                            decision.direction.value
                            if decision.direction is not None
                            else None
                        ),
                        "maximum_depth": decision.maximum_depth,
                        "cursor": decision.cursor,
                        "disclosure_record_ref": result.disclosure_record_ref,
                        "model_call_receipt_ref": result.receipt.digest.value,
                    }
                )
                if decision.action is not LightweightAgentAction.FINISH:
                    tool_actions += 1
                    before_count = len(observations)
                    self._execute_action(
                        request=request,
                        decision=decision,
                        observations=observations,
                        read_candidates=read_candidates,
                        cognition_candidates=cognition_candidates,
                        events=events,
                    )
                    progress = any(
                        item.progress for item in observations[before_count:]
                    )
                    consecutive_no_progress = (
                        0 if progress else consecutive_no_progress + 1
                    )
                    if (
                        consecutive_no_progress
                        >= self._limits.maximum_consecutive_no_progress
                    ):
                        tool_actions = self._limits.maximum_tool_actions
                    rejected_answer = None
                    review_findings = ()
                    continue

                assert decision.answer is not None
                assert decision.response_kind is not None
                try:
                    selected = self._resolve_citations(decision, observations)
                except _CitationBindingRejection as exc:
                    if citation_binding_repairs >= 1:
                        raise
                    citation_binding_repairs += 1
                    # Keep the rejected selection intact in the trajectory and
                    # give the same primary Agent one bounded replan.  The
                    # feedback is deliberately mechanical: all actual evidence
                    # remains in the sealed observations and no Citation is
                    # synthesized or silently removed.
                    events.append(
                        {
                            "kind": "CITATION_BINDING_REJECTION",
                            "step": step,
                            "observation_index": exc.observation_index,
                            "citation_index": exc.citation_index,
                            "available_citation_count": (
                                exc.available_citation_count
                            ),
                            "selected_pairs": tuple(
                                {
                                    "observation_index": item.observation_index,
                                    "citation_index": item.citation_index,
                                }
                                for item in decision.citations
                            ),
                            "repair_ordinal": citation_binding_repairs,
                        }
                    )
                    rejected_answer = decision.answer
                    review_findings = (
                        "Application rejected the previous FINISH citation "
                        "selection at observation index "
                        f"{exc.observation_index}, citation index "
                        f"{exc.citation_index}; the selected observation has "
                        f"{exc.available_citation_count} delivered Citation(s). "
                        "Replan and submit FINISH using only "
                        "observation/citation pairs present in the current "
                        "observations; do not invent evidence or alter the "
                        "observations.",
                    )
                    continue
                reviews += 1
                reviewed = self._model.review(
                    LightweightReviewRequest(
                        turn_request=request,
                        answer=decision.answer,
                        response_kind=decision.response_kind,
                        observations=tuple(observations),
                        citations=selected,
                    )
                )
                self._record_receipt(receipts, reviewed.receipt)
                review = reviewed.review
                events.append(
                    {
                        "kind": "INDEPENDENT_REVIEW",
                        "step": step,
                        "verdict": review.verdict.value,
                        "findings": list(review.findings),
                        "disclosure_record_ref": reviewed.disclosure_record_ref,
                        "model_call_receipt_ref": reviewed.receipt.digest.value,
                    }
                )
                if review.verdict is LightweightReviewVerdict.APPROVED:
                    outcome = self._success(
                        request=request,
                        goal=goal,
                        plan=plan,
                        answer=decision.answer,
                        response_kind=decision.response_kind,
                        observations=tuple(observations),
                        citations=selected,
                        review=review,
                        review_receipt=reviewed.receipt,
                        receipts=tuple(receipts),
                        events=tuple(events),
                    )
                    terminal = "SUCCEEDED"
                    return outcome
                if reviews >= self._limits.maximum_reviews:
                    raise DomainError(
                        ErrorCode.BUDGET_EXHAUSTED,
                        "lightweight independent review budget is exhausted",
                    )
                if (
                    review.verdict is LightweightReviewVerdict.MORE_EVIDENCE
                    and tool_actions >= self._limits.maximum_tool_actions
                ):
                    raise DomainError(
                        ErrorCode.BUDGET_EXHAUSTED,
                        "fresh review requested evidence after the read-only tool budget closed",
                    )
                rejected_answer = decision.answer
                review_findings = review.findings
                if review.verdict is LightweightReviewVerdict.REWRITE:
                    rewrites += 1
                    if rewrites > 1:
                        raise DomainError(
                            ErrorCode.CONTROL_STATE_DENIED,
                            "lightweight Agent permits at most one complete rewrite",
                        )
                    tool_actions = self._limits.maximum_tool_actions
                else:
                    rejected_answer = None
            raise DomainError(
                ErrorCode.BUDGET_EXHAUSTED,
                "lightweight Agent step budget is exhausted",
            )
        except LightweightModelCallFailure as exc:
            self._record_receipt(receipts, exc.receipt)
            events.append(
                {
                    "kind": "MODEL_FAILURE",
                    "failure_code": exc.code.value,
                    "disclosure_record_ref": exc.disclosure_record_ref,
                    "model_call_receipt_ref": exc.receipt.digest.value,
                }
            )
            return self._failure(
                request=request,
                receipts=tuple(receipts),
                code=exc.receipt.failure_code or exc.code.value,
                message=exc.message,
                model_failure=exc.receipt.failure_kind,
                http_status=exc.receipt.provider_http_status,
                http_evidence=exc.receipt.provider_http_failure_evidence_digest,
            )
        except DomainError as exc:
            events.append(
                {"kind": "APPLICATION_FAILURE", "failure_code": exc.code.value}
            )
            return self._failure(
                request=request,
                receipts=tuple(receipts),
                code=exc.code.value,
                message=exc.message,
                model_failure=None,
            )
        finally:
            core = {
                "schema": "SWM-LIGHTWEIGHT-AGENT-TRAJECTORY@1",
                "attempt_ref": self._attempt_ref,
                "turn_request_digest": request.request_digest.value,
                "mode": (
                    "WORLD_MODEL_PLUS_SOURCE"
                    if self._cognition is not None
                    else "SOURCE_ONLY"
                ),
                "events": tuple(events),
                "terminal_status": terminal,
            }
            self._traces.record(
                LightweightAgentTrajectory(
                    attempt_ref=self._attempt_ref,
                    turn_request_digest=request.request_digest,
                    mode=(
                        "WORLD_MODEL_PLUS_SOURCE"
                        if self._cognition is not None
                        else "SOURCE_ONLY"
                    ),
                    events=tuple(events),
                    terminal_status=terminal,
                    digest=digest_of(core),
                )
            )

    def _prior_turn_read_candidates(
        self, request: EngineeringTurnExecutionRequest
    ) -> tuple[LightweightReadCandidate, ...]:
        return tuple(
            LightweightReadCandidate(
                read_index=index,
                citation=EngineeringAgentCitation.create(
                    citation_ref=item.locator_reference.value,
                    evidence_class=item.evidence_class,
                    source_revision=item.source_revision,
                    locator=item.resource_locator,
                    modality=item.modality,
                    content_digest=item.content_digest,
                ),
                resource_locator=item.resource_locator,
            )
            for index, item in enumerate(
                self._tool.source_read_options(request), 1
            )
        )

    def _execute_action(
        self,
        *,
        request: EngineeringTurnExecutionRequest,
        decision: LightweightAgentDecision,
        observations: list[LightweightObservation],
        read_candidates: list[LightweightReadCandidate],
        cognition_candidates: list[LightweightCognitionCandidate],
        events: list[Mapping[str, object]],
    ) -> None:
        if decision.action in {
            LightweightAgentAction.SEARCH_COGNITION,
            LightweightAgentAction.TRAVERSE_RELATIONS,
            LightweightAgentAction.RETRIEVE_COGNITION_DETAIL,
        }:
            self._execute_cognition_action(
                request=request,
                decision=decision,
                observations=observations,
                read_candidates=read_candidates,
                cognition_candidates=cognition_candidates,
                events=events,
            )
            return
        if decision.action is LightweightAgentAction.SEARCH_SOURCE:
            assert decision.query is not None
            operation = EngineeringAgentToolOperation.SOURCE_SEARCH
            arguments = (("evidence_class", "SOURCE"), ("query", decision.query))
        else:
            assert decision.read_index is not None
            matches = [
                item
                for item in read_candidates
                if item.read_index == decision.read_index
            ]
            if len(matches) != 1:
                raise DomainError(
                    ErrorCode.CONTROL_STATE_DENIED,
                    "lightweight Agent selected an unavailable read candidate",
                )
            operation = EngineeringAgentToolOperation.SOURCE_READ
            arguments = (("locator_reference", matches[0].citation.citation_ref),)
        action = EngineeringAgentToolActionProposal.create(
            operation=operation,
            arguments=arguments,
            evidence_need=decision.plan,
        )
        tool_id = self._ids.new("source_agent_tool_request")
        work_digest = digest_of(
            {
                "goal": decision.goal,
                "plan": decision.plan,
                "observations": tuple(item.digest.value for item in observations),
            }
        )
        request_core = {
            "schema": "ENGINEERING_AGENT_TOOL_REQUEST@1",
            "tool_request_id": tool_id.value,
            "turn_request_digest": request.request_digest.value,
            "binding_digest": request.binding.digest.value,
            "work_state_digest": work_digest.value,
            "action_digest": action.digest.value,
        }
        tool_request = EngineeringAgentToolRequest(
            tool_request_id=tool_id,
            turn_request_digest=request.request_digest,
            binding_digest=request.binding.digest,
            work_state_digest=work_digest,
            turn_request=request,
            action=action,
            digest=digest_of(request_core),
        )
        result = self._tool.execute(tool_request)
        if result.tool_request_digest != tool_request.digest:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "read-only tool result binds another request",
            )
        for evidence in result.evidence:
            receipt = evidence.authority_receipt
            if receipt is None or receipt.tool_request_digest != tool_request.digest:
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "read-only observation lacks an exact authority receipt",
                )
            by_ref = {item.citation_ref: item for item in receipt.citations}
            try:
                citations = tuple(by_ref[item] for item in evidence.citation_refs)
            except KeyError as exc:
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "observation references an unavailable Citation",
                ) from exc
            index = len(observations) + 1
            observation_core = {
                "observation_index": index,
                "operation": operation.value,
                "disposition": evidence.disposition.value,
                "content": evidence.content,
                "progress": evidence.progress,
                "citations": tuple(item.digest.value for item in citations),
                "tool_evidence_digest": evidence.digest.value,
                "authority_receipt_digest": receipt.digest.value,
            }
            observation = LightweightObservation(
                observation_index=index,
                operation=operation,
                disposition=evidence.disposition,
                content=evidence.content,
                progress=evidence.progress,
                citations=citations,
                digest=digest_of(observation_core),
            )
            observations.append(observation)
            events.append(
                {
                    "kind": "TOOL_OBSERVATION",
                    "observation_index": index,
                    "operation": operation.value,
                    "disposition": evidence.disposition.value,
                    "progress": evidence.progress,
                    "citation_count": len(citations),
                    "observation_digest": observation.digest.value,
                }
            )
            known = {item.citation.citation_ref for item in read_candidates}
            for citation in citations:
                if citation.citation_ref not in known:
                    read_candidates.append(
                        LightweightReadCandidate(
                            read_index=len(read_candidates) + 1,
                            citation=citation,
                            resource_locator=_citation_resource_locator(
                                citation.locator
                            ),
                        )
                    )
                    known.add(citation.citation_ref)
        if sum(len(item.content.encode("utf-8")) for item in observations) > (
            self._limits.maximum_evidence_package_bytes
        ):
            raise DomainError(
                ErrorCode.BUDGET_EXHAUSTED,
                "lightweight Agent evidence byte budget is exhausted",
            )

    def _execute_cognition_action(
        self,
        *,
        request: EngineeringTurnExecutionRequest,
        decision: LightweightAgentDecision,
        observations: list[LightweightObservation],
        read_candidates: list[LightweightReadCandidate],
        cognition_candidates: list[LightweightCognitionCandidate],
        events: list[Mapping[str, object]],
    ) -> None:
        cognition = self._cognition
        if cognition is None or cognition.snapshot.source_revision != (
            request.binding.repository_revision
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "capability cognition is unavailable or binds another Source revision",
            )
        if decision.action is LightweightAgentAction.SEARCH_COGNITION:
            assert decision.query is not None
            page = cognition.search(
                decision.query,
                cursor=decision.cursor or 0,
                limit=12,
            )
        else:
            assert decision.cognition_index is not None
            matches = [
                item
                for item in cognition_candidates
                if item.cognition_index == decision.cognition_index
            ]
            if len(matches) != 1:
                raise DomainError(
                    ErrorCode.CONTROL_STATE_DENIED,
                    "lightweight Agent selected an unavailable cognition entity",
                )
            entity_id = matches[0].entity_id
            if decision.action is LightweightAgentAction.TRAVERSE_RELATIONS:
                assert decision.direction is not None
                assert decision.maximum_depth is not None
                page = cognition.traverse(
                    entity_id,
                    kinds=(
                        (decision.relation_kind,)
                        if decision.relation_kind is not None
                        else ()
                    ),
                    direction=decision.direction,
                    maximum_depth=decision.maximum_depth,
                    cursor=decision.cursor or 0,
                    limit=24,
                )
            else:
                page = cognition.detail(
                    entity_id,
                    cursor=decision.cursor or 0,
                    limit=32,
                )
        first_new_candidate = len(cognition_candidates)
        self._register_cognition_candidates(page, cognition_candidates)
        new_candidates = cognition_candidates[first_new_candidate:]
        index = len(observations) + 1
        content = canonical_json_bytes(page.to_payload()).decode("utf-8")
        page_digest = digest_of(page.to_payload())
        observation = LightweightObservation(
            observation_index=index,
            operation=decision.action,
            disposition=(
                EngineeringAgentEvidenceDisposition.SUPPORT
                if page.items
                else EngineeringAgentEvidenceDisposition.BOUNDARY
            ),
            content=content,
            progress=bool(page.items),
            citations=(),
            digest=digest_of(
                {
                    "schema": "SWM-LIGHTWEIGHT-COGNITION-OBSERVATION@1",
                    "observation_index": index,
                    "operation": decision.action.value,
                    "snapshot_digest": page.snapshot_digest.value,
                    "page_digest": page_digest.value,
                }
            ),
        )
        observations.append(observation)
        events.append(
            {
                "kind": "COGNITION_OBSERVATION",
                "observation_index": index,
                "operation": decision.action.value,
                "progress": observation.progress,
                "item_count": len(page.items),
                "total": page.total,
                "next_cursor": page.next_cursor,
                "snapshot_digest": page.snapshot_digest.value,
                "observation_digest": observation.digest.value,
            }
        )
        self._register_cognition_source_read_candidates(
            request=request,
            cognition=cognition,
            candidates=new_candidates,
            read_candidates=read_candidates,
            events=events,
            observation_index=index,
        )
        if sum(len(item.content.encode("utf-8")) for item in observations) > (
            self._limits.maximum_evidence_package_bytes
        ):
            raise DomainError(
                ErrorCode.BUDGET_EXHAUSTED,
                "lightweight Agent evidence byte budget is exhausted",
            )

    @staticmethod
    def _register_cognition_candidates(
        page: CognitionPage,
        candidates: list[LightweightCognitionCandidate],
    ) -> None:
        known = {item.entity_id for item in candidates}

        def visit(value: object) -> None:
            if isinstance(value, Mapping):
                raw_id = value.get("entity_id")
                raw_kind = value.get("kind")
                provenance = value.get("provenance")
                if (
                    isinstance(raw_id, str)
                    and isinstance(raw_kind, str)
                    and isinstance(value.get("name"), str)
                    and isinstance(value.get("qualified_name"), str)
                    and isinstance(value.get("coverage"), str)
                    and isinstance(value.get("unknowns"), list)
                    and isinstance(provenance, Mapping)
                    and isinstance(provenance.get("locator"), str)
                ):
                    parsed_provenance = CognitionProvenance.from_payload(
                        provenance
                    )
                    if (
                        set(provenance)
                        != {
                            "source_revision",
                            "source_tree",
                            "path",
                            "start_line",
                            "end_line",
                            "content_digest",
                            "evidence_kind",
                            "locator",
                        }
                        or provenance["locator"]
                        != parsed_provenance.locator
                    ):
                        raise DomainError(
                            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                            "cognition candidate provenance is inconsistent",
                        )
                    entity_id = StableId(raw_id)
                    if entity_id not in known:
                        candidates.append(
                            LightweightCognitionCandidate(
                                cognition_index=len(candidates) + 1,
                                entity_id=entity_id,
                                kind=CognitionEntityKind(raw_kind),
                                name=value["name"],
                                qualified_name=value["qualified_name"],
                                coverage=value["coverage"],
                                unknowns=tuple(
                                    item
                                    for item in value["unknowns"]
                                    if isinstance(item, str)
                                ),
                                provenance=parsed_provenance,
                            )
                        )
                        known.add(entity_id)
                for item in value.values():
                    visit(item)
            elif isinstance(value, (list, tuple)):
                for item in value:
                    visit(item)

        visit(page.items)

    def _register_cognition_source_read_candidates(
        self,
        *,
        request: EngineeringTurnExecutionRequest,
        cognition: CapabilityCognitionIndex,
        candidates: Sequence[LightweightCognitionCandidate],
        read_candidates: list[LightweightReadCandidate],
        events: list[Mapping[str, object]],
        observation_index: int,
    ) -> None:
        known_paths = {item.resource_locator for item in read_candidates}
        provenances: list[CognitionProvenance] = []
        selected_paths: set[str] = set()
        for candidate in candidates:
            provenance = candidate.provenance
            if (
                provenance.source_revision != cognition.snapshot.source_revision
                or provenance.source_tree != cognition.snapshot.source_tree
                or provenance.source_revision
                != request.binding.repository_revision
            ):
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "cognition read candidate binds another Source snapshot",
                )
            if (
                provenance.path not in known_paths
                and provenance.path not in selected_paths
            ):
                provenances.append(provenance)
                selected_paths.add(provenance.path)
        if not provenances:
            return

        # The existing bridge may return no option for a provenance that the
        # bound Source Profile classifies as a non-SOURCE resource.  Ask one
        # path at a time so that this controlled omission is distinguishable
        # from an option that binds the wrong path; the full cognition page is
        # still retained in its cognition Observation.
        candidates_by_path: dict[str, EngineeringAgentCitation] = {}
        skipped_non_source_paths: list[str] = []
        skipped_non_source_kinds: list[str] = []
        skipped_non_source_digests: list[str] = []
        for provenance in provenances:
            navigation_candidates = self._tool.cognition_source_read_options(
                request,
                (provenance,),
            )
            if not navigation_candidates:
                skipped_non_source_paths.append(provenance.path)
                skipped_non_source_kinds.append(provenance.evidence_kind)
                skipped_non_source_digests.append(
                    digest_of(provenance.to_payload()).value
                )
                continue
            if len(navigation_candidates) != 1:
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "cognition Source read options do not bind one path",
                )
            candidate = navigation_candidates[0]
            candidate_path = _citation_resource_locator(candidate.locator)
            if candidate_path in candidates_by_path:
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "cognition Source read options contain duplicate paths",
                )
            if candidate_path != provenance.path:
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "cognition Source read option binds another path",
                )
            candidates_by_path[candidate_path] = candidate
        known_references = {
            item.citation.citation_ref for item in read_candidates
        }
        added_indexes: list[int] = []
        candidate_digests: list[str] = []
        for provenance in provenances:
            candidate = candidates_by_path.get(provenance.path)
            if candidate is None:
                continue
            expected = EngineeringAgentCitation.create(
                citation_ref=candidate.citation_ref,
                evidence_class=candidate.evidence_class,
                source_revision=candidate.source_revision,
                locator=candidate.locator,
                modality=candidate.modality,
                content_digest=candidate.content_digest,
            )
            if (
                candidate != expected
                or candidate.locator != provenance.locator
                or candidate.evidence_class != "SOURCE"
                or candidate.source_revision != provenance.source_revision
                or candidate.modality
                != "JAVA_CAPABILITY_COGNITION_PROVENANCE_NAVIGATION"
                or candidate.content_digest != provenance.content_digest
                or candidate.citation_ref in known_references
            ):
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "cognition Source read option identity is invalid",
                )
            read_index = len(read_candidates) + 1
            read_candidates.append(
                LightweightReadCandidate(
                    read_index=read_index,
                    citation=candidate,
                    resource_locator=provenance.path,
                )
            )
            known_references.add(candidate.citation_ref)
            added_indexes.append(read_index)
            candidate_digests.append(candidate.digest.value)
        events.append(
            {
                "kind": "COGNITION_SOURCE_READ_OPTIONS",
                "observation_index": observation_index,
                "read_indexes": tuple(added_indexes),
                "option_count": len(added_indexes),
                "skipped_non_source_count": len(skipped_non_source_paths),
                "skipped_non_source_paths": tuple(skipped_non_source_paths),
                "skipped_non_source_evidence_kinds": tuple(
                    skipped_non_source_kinds
                ),
                "skipped_non_source_provenance_digests": tuple(
                    skipped_non_source_digests
                ),
                "source_revision": cognition.snapshot.source_revision,
                "source_tree": cognition.snapshot.source_tree,
                "navigation_candidate_digests": tuple(candidate_digests),
                "cognition_provenance_grants_source_evidence": False,
            }
        )

    @staticmethod
    def _resolve_citations(
        decision: LightweightAgentDecision,
        observations: Sequence[LightweightObservation],
    ) -> tuple[EngineeringAgentCitation, ...]:
        by_index = {item.observation_index: item for item in observations}
        selected: list[EngineeringAgentCitation] = []
        for choice in decision.citations:
            observation = by_index.get(choice.observation_index)
            if observation is None or not (
                1 <= choice.citation_index <= len(observation.citations)
            ):
                raise _CitationBindingRejection(
                    observation_index=choice.observation_index,
                    citation_index=choice.citation_index,
                    available_citation_count=(
                        len(observation.citations) if observation is not None else 0
                    ),
                )
            citation = observation.citations[choice.citation_index - 1]
            if citation.citation_ref not in {
                item.citation_ref for item in selected
            }:
                selected.append(citation)
        return tuple(selected)

    @staticmethod
    def _record_receipt(
        receipts: list[EngineeringAgentModelCallReceipt],
        receipt: EngineeringAgentModelCallReceipt,
    ) -> None:
        if any(item.digest == receipt.digest for item in receipts):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "lightweight model call receipt was replayed",
            )
        receipts.append(receipt)

    def _success(
        self,
        *,
        request: EngineeringTurnExecutionRequest,
        goal: str,
        plan: str,
        answer: str,
        response_kind: LightweightAgentResponseKind,
        observations: tuple[LightweightObservation, ...],
        citations: tuple[EngineeringAgentCitation, ...],
        review: LightweightReview,
        review_receipt: EngineeringAgentModelCallReceipt,
        receipts: tuple[EngineeringAgentModelCallReceipt, ...],
        events: tuple[Mapping[str, object], ...],
    ) -> EngineeringTurnExecutionOutcome:
        evidence_ref = digest_of(
            [
                "SWM-LIGHTWEIGHT-EVIDENCE-PACKAGE@1",
                tuple(item.digest.value for item in observations),
            ]
        ).value
        answer_ref = digest_of(
            [
                "SWM-LIGHTWEIGHT-ANSWER@1",
                request.request_digest.value,
                answer,
                tuple(item.digest.value for item in citations),
            ]
        ).value
        review_ref = digest_of(
            [
                "SWM-LIGHTWEIGHT-REVIEW@1",
                answer_ref,
                review.verdict.value,
                review.findings,
                review_receipt.digest.value,
            ]
        ).value
        authorization = self._delivery.authorize(
            LightweightDeliveryRequest(
                turn_request=request,
                response_kind=response_kind,
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
            "lightweight-agent-state:"
            + request.snapshot_before.conversation.conversation_id.value
        )
        work_revision = (
            Revision(1)
            if before.work_state_ref is None
            else Revision(before.work_state_revision.value + 1)
        )
        work_digest = digest_of(
            {
                "schema": "SWM-LIGHTWEIGHT-AGENT-WORK-STATE@1",
                "work_ref": work_ref,
                "revision": work_revision.value,
                "goal": goal,
                "plan": plan,
                "trajectory": events,
                "answer_ref": answer_ref,
                "review_ref": review_ref,
                "delivery_authorization_ref": authorization.digest.value,
            }
        )
        projected = tuple(
            EngineeringTurnCitation.create(
                citation_ref=item.citation_ref,
                evidence_class=item.evidence_class,
                source_revision=item.source_revision,
                locator=item.locator,
                modality=item.modality,
                content_digest=item.content_digest,
            )
            for item in citations
        )
        message_kind = ConversationMessageKind(response_kind.value)
        reviewed_refs = before.reviewed_conclusion_refs
        if message_kind is ConversationMessageKind.ANSWER:
            reviewed_refs = (*reviewed_refs, answer_ref)
        quality = {
            ConversationMessageKind.ANSWER: "ACCEPTED",
            ConversationMessageKind.CLARIFICATION: "REVIEWED_CLARIFICATION",
            ConversationMessageKind.LIMITATION: "REVIEWED_LIMITATION",
        }[message_kind]
        return EngineeringTurnExecutionOutcome.succeeded(
            request_digest=request.request_digest,
            assistant_kind=message_kind,
            assistant_content=answer,
            included_user_message_ids=(
                *before.included_user_message_ids,
                request.user_message.message_id,
            ),
            accepted_correction_message_ids=before.accepted_correction_message_ids,
            reviewed_conclusion_refs=reviewed_refs,
            superseded_conclusion_refs=before.superseded_conclusion_refs,
            reducer_status="LIGHTWEIGHT_AGENT_CONTEXT_COMMITTED",
            work_state_ref=work_ref,
            work_state_revision=work_revision,
            work_state_digest=work_digest,
            evidence_package_ref=evidence_ref,
            answer_ref=answer_ref,
            review_ref=review_ref,
            delivery_authorization_ref=authorization.digest.value,
            provider_dispatch_count=sum(item.provider_dispatch_count for item in receipts),
            model_dispatch_receipt_refs=tuple(item.digest.value for item in receipts),
            citations=projected,
            quality_status=quality,
        )

    @staticmethod
    def _failure(
        *,
        request: EngineeringTurnExecutionRequest,
        receipts: tuple[EngineeringAgentModelCallReceipt, ...],
        code: str,
        message: str,
        model_failure: EngineeringAgentModelFailureKind | None,
        http_status: int | None = None,
        http_evidence: Digest | None = None,
    ) -> EngineeringTurnExecutionOutcome:
        classification = {
            EngineeringAgentModelFailureKind.PROVIDER_UNAVAILABLE: (
                EngineeringProviderFailureClassification.PROVIDER_UNAVAILABLE
            ),
            EngineeringAgentModelFailureKind.PROVIDER_HTTP_ERROR: (
                EngineeringProviderFailureClassification.PROVIDER_HTTP_ERROR
            ),
            EngineeringAgentModelFailureKind.PROVIDER_OUTCOME_UNKNOWN: (
                EngineeringProviderFailureClassification.PROVIDER_OUTCOME_UNKNOWN
            ),
            EngineeringAgentModelFailureKind.PROVIDER_OUTPUT_INVALID: (
                EngineeringProviderFailureClassification.PROVIDER_OUTPUT_INVALID
            ),
        }.get(model_failure)
        before = request.snapshot_before.context
        user_message = (
            "本 Turn 的轻量工程 Agent 未能形成经独立审核的答案；"
            "已失败关闭，Conversation 仍可继续使用。"
        )
        return EngineeringTurnExecutionOutcome.failed(
            request_digest=request.request_digest,
            assistant_content=user_message,
            included_user_message_ids=(
                *before.included_user_message_ids,
                request.user_message.message_id,
            ),
            accepted_correction_message_ids=before.accepted_correction_message_ids,
            reviewed_conclusion_refs=before.reviewed_conclusion_refs,
            superseded_conclusion_refs=before.superseded_conclusion_refs,
            reducer_status="LIGHTWEIGHT_AGENT_FAILED_CLOSED",
            work_state_ref=before.work_state_ref,
            work_state_revision=(
                before.work_state_revision if before.work_state_ref else None
            ),
            work_state_digest=before.work_state_digest,
            failure_code=code,
            failure_message=message,
            provider_dispatch_count=sum(item.provider_dispatch_count for item in receipts),
            model_dispatch_receipt_refs=tuple(item.digest.value for item in receipts),
            provider_failure_classification=classification,
            provider_failure_code=code if classification is not None else None,
            provider_http_status=http_status,
            provider_http_failure_evidence_digest=http_evidence,
        )


def _invalid(message: str) -> None:
    raise DomainError(ErrorCode.STRUCTURED_OUTPUT_INVALID, message)


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise DomainError(
            ErrorCode.STRUCTURED_OUTPUT_INVALID,
            f"{label} must be non-empty trimmed text",
        )
    return value


def _optional_text(value: object, label: str) -> str | None:
    return None if value is None else _text(value, label)


def _citation_resource_locator(locator: str) -> str:
    resource, separator, line_range = locator.rpartition(":L")
    if separator == ":L" and resource and line_range:
        return resource
    return locator


__all__ = [
    "ApplicationOwnedLightweightAgentTurnExecutor",
    "LightweightAgentAction",
    "LightweightAgentDecision",
    "LightweightAgentDecisionBranchError",
    "LightweightAgentResponseKind",
    "LightweightAgentStepRequest",
    "LightweightAgentTraceStore",
    "LightweightAgentTrajectory",
    "LightweightCitationSelection",
    "LightweightDecisionResult",
    "LightweightDeliveryAuthorization",
    "LightweightDeliveryRequest",
    "LightweightEngineeringModel",
    "LightweightModelCallFailure",
    "LightweightObservation",
    "LightweightReadCandidate",
    "LightweightReview",
    "LightweightReviewRequest",
    "LightweightReviewResult",
    "LightweightReviewVerdict",
    "SealedLightweightDeliveryControl",
]
