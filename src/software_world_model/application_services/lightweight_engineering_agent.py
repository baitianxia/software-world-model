"""Capability-oriented Application loop for an evidence-seeking Agent.

The model keeps a goal and plan, proposes one read-only action at a time, sees
the trusted observation, and either replans or finishes.  Source access and
delivery remain Application owned; the model receives neither a filesystem nor
opaque tool authority identifiers.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from threading import Lock
from typing import Collection, Mapping, Protocol, Sequence

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


_COGNITION_NAVIGATION_MODALITY = (
    "JAVA_CAPABILITY_COGNITION_PROVENANCE_NAVIGATION"
)
_FULL_SOURCE_MODALITIES = frozenset({"EXACT_STATIC_SOURCE_TEXT", "SOURCE_TEXT"})


@dataclass(frozen=True, slots=True)
class _LightweightReadNavigationMetadata:
    """Application-only ordering sidecar for an existing read option."""

    origin_observation_index: int = 0
    cognition_kind: CognitionEntityKind | None = None
    cognition_attributes: tuple[tuple[str, str], ...] = ()
    origin_cognition_index: int | None = None
    current_source_search_hit: bool = False


def _ordered_read_candidates(
    candidates: Sequence[LightweightReadCandidate],
    observations: Sequence[LightweightObservation],
    *,
    remaining_tool_actions: int | None = None,
    metadata_by_read_index: Mapping[
        int, _LightweightReadNavigationMetadata
    ] | None = None,
) -> tuple[LightweightReadCandidate, ...]:
    """Present existing read options in a bounded, breadth-first order.

    This is a presentation projection only.  Numeric indexes and citation
    identities remain untouched, and every candidate remains visible.  A
    resource is treated as covered for ordering once any option for that
    resource has been fully read; this prevents a second line hit from
    crowding out an unread resource while preserving the existing authority
    checks in the executor.  When the fixed remaining Tool budget is smaller
    than the number of distinct resources, budget pressure changes only the
    presentation strategy: the strongest typed/source option is presented
    first instead of spending the first positions on breadth.  It never
    removes an option or authorizes an automatic read.
    """

    if not candidates:
        return ()
    if remaining_tool_actions is None:
        # Direct unit fixtures predating the internal budget projection do not
        # have a loop counter.  Permit one candidate per known resource so
        # their historical breadth-first ordering remains deterministic;
        # production dispatches always pass the exact Application-computed
        # value below.
        remaining = len(
            {
                item.resource_locator or item.citation.citation_ref
                for item in candidates
            }
        )
    elif type(remaining_tool_actions) is int and remaining_tool_actions >= 0:
        remaining = remaining_tool_actions
    else:
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "lightweight Agent remaining Tool budget is invalid",
        )
    navigation_metadata = metadata_by_read_index or {}
    read_citation_refs = {
        citation.citation_ref
        for observation in observations
        if observation.operation is EngineeringAgentToolOperation.SOURCE_READ
        for citation in observation.citations
    }
    # A cognition navigation option carries a RequiredPathLocator reference,
    # while the subsequent SOURCE_READ observation carries the Source Broker's
    # retrieval citation reference.  Those opaque references are intentionally
    # different capabilities.  Coverage therefore binds on the trusted
    # citation's exact source revision plus canonical resource locator, not on
    # an equality that can never hold across the navigation/read boundary.
    read_resources = {
        (citation.source_revision, _citation_resource_locator(citation.locator))
        for observation in observations
        if observation.operation is EngineeringAgentToolOperation.SOURCE_READ
        for citation in observation.citations
    }

    def candidate_key(candidate: LightweightReadCandidate) -> tuple[int, ...]:
        metadata = navigation_metadata.get(candidate.read_index)
        candidate_resources = {
            (
                candidate.citation.source_revision,
                _citation_resource_locator(candidate.resource_locator),
            ),
            (
                candidate.citation.source_revision,
                _citation_resource_locator(candidate.citation.locator),
            ),
        }
        resource_read = int(bool(candidate_resources & read_resources))
        citation_read = int(
            candidate.citation.citation_ref in read_citation_refs
        )
        modality = candidate.citation.modality
        modality_rank = (
            0
            if modality in _FULL_SOURCE_MODALITIES
            else 1
            if modality == "LITERAL_TEXT_SEARCH_HIT"
            else 2
            if modality == _COGNITION_NAVIGATION_MODALITY
            else 3
        )
        typed_origin = int(
            metadata is None or metadata.cognition_kind is None
        )
        # The executor marks exact citations from the latest Source-search
        # invocation, including when it emits multiple observations. Prefer
        # those hits for navigation; this does not establish answer support.
        direct_search_origin = int(
            not (
                metadata is not None
                and metadata.current_source_search_hit
                and modality in _FULL_SOURCE_MODALITIES | {"LITERAL_TEXT_SEARCH_HIT"}
            )
        )
        role_rank = (
            _cognition_entity_role_rank(
                metadata.cognition_kind,
                metadata.cognition_attributes,
            )
            if metadata is not None and metadata.cognition_kind is not None
            else 3
        )
        return (
            resource_read,
            citation_read,
            direct_search_origin,
            # A cognition-issued typed origin is the Application's strongest
            # generic signal for a known declaration/effect gap.  Keep that
            # signal ahead of broad literal/search noise; modality remains a
            # tie-breaker within each origin class.
            typed_origin,
            role_rank,
            modality_rank,
            # Keep the first trusted cognition page's candidate ahead of a
            # later sibling page when roles are otherwise equal.  A later
            # page often contributes a new, but less directly relevant,
            # declaration/effect candidate; retaining the earlier unread
            # option gives the same Agent a stable path to close the original
            # evidence gap after a Reviewer asks for more evidence.
            metadata.origin_observation_index
            if metadata is not None
            else 0,
            metadata.origin_cognition_index
            if metadata is not None
            else 1_000_000,
            candidate.read_index,
        )

    groups: dict[str, list[LightweightReadCandidate]] = {}
    for candidate in candidates:
        # resource_locator is an authority-owned canonical resource identity;
        # it is used only to interleave duplicate line options, never for
        # lexical relevance or path matching.
        groups.setdefault(
            candidate.resource_locator or candidate.citation.citation_ref,
            [],
        ).append(candidate)
    ordered_groups = sorted(
        groups.values(),
        key=lambda group: min(candidate_key(item) for item in group),
    )
    for group in ordered_groups:
        group.sort(key=candidate_key)
    if remaining < len(ordered_groups):
        # With fewer remaining actions than resource groups, a breadth-first
        # presentation would spend the scarce prefix on arbitrary siblings.
        # Use the same typed key globally so the prefix is deterministic while
        # retaining every candidate in the model input.
        return tuple(sorted(candidates, key=candidate_key))
    ordered: list[LightweightReadCandidate] = []
    maximum = max(len(group) for group in ordered_groups)
    for ordinal in range(maximum):
        for group in ordered_groups:
            if ordinal < len(group):
                ordered.append(group[ordinal])
    return tuple(ordered)


def _unread_read_candidates(
    candidates: Sequence[LightweightReadCandidate],
    observations: Sequence[LightweightObservation],
    consumed_read_indexes: Collection[int] = (),
) -> tuple[LightweightReadCandidate, ...]:
    """Return existing Source candidates whose resource is not yet read.

    This is an application-owned Gap check.  It deliberately compares only
    trusted Source identity (revision plus canonical resource locator), never
    query text or model output, so a Reviewer request can reserve the fixed
    budget for an already available unread candidate without creating a new
    Agent-facing protocol field.
    """

    if not candidates:
        return ()
    read_citation_refs = {
        citation.citation_ref
        for observation in observations
        if observation.operation is EngineeringAgentToolOperation.SOURCE_READ
        for citation in observation.citations
    }
    read_resources = {
        (citation.source_revision, _citation_resource_locator(citation.locator))
        for observation in observations
        if observation.operation is EngineeringAgentToolOperation.SOURCE_READ
        for citation in observation.citations
    }
    unread: list[LightweightReadCandidate] = []
    for candidate in candidates:
        if candidate.read_index in consumed_read_indexes:
            continue
        if candidate.citation.citation_ref in read_citation_refs:
            continue
        resources = {
            (
                candidate.citation.source_revision,
                _citation_resource_locator(candidate.resource_locator),
            ),
            (
                candidate.citation.source_revision,
                _citation_resource_locator(candidate.citation.locator),
            ),
        }
        if resources & read_resources:
            continue
        unread.append(candidate)
    return tuple(unread)


def _reserved_unread_cognition_candidates(
    candidates: Sequence[LightweightReadCandidate],
    observations: Sequence[LightweightObservation],
    metadata: Mapping[int, _LightweightReadNavigationMetadata],
    findings: Sequence[str],
) -> tuple[LightweightReadCandidate, ...]:
    """Share the existing execution restriction with action presentation.

    These are Application-owned feedback markers, not answer or question
    semantics. Source eligibility still comes from trusted candidate identity.
    """
    duplicate_feedback = any(
        finding.startswith(
            "Application blocked the selected action because it repeats a completed investigation action."
        )
        for finding in findings
    )
    # A no-progress observation alone cannot establish that existing unread
    # candidates cover the gap. Preserve a distinct Source search in that case.
    if not duplicate_feedback and not any(
        finding.startswith("Independent review requested more evidence.")
        for finding in findings
    ):
        return ()
    unread = _unread_read_candidates(candidates, observations)
    if duplicate_feedback:
        return tuple(unread)
    return tuple(
        candidate
        for candidate in unread
        if candidate.read_index in metadata
        and metadata[candidate.read_index].cognition_kind is not None
    )


def _cognition_entity_role_rank(
    kind: CognitionEntityKind | None,
    attributes: Sequence[tuple[str, str]],
) -> int:
    if kind is None:
        return 1_000_000
    if kind is CognitionEntityKind.METHOD:
        values = dict(attributes)
        if (
            values.get("owner_declaration_kind") == "INTERFACE"
            or values.get("has_body") == "false"
        ):
            return 0
        if (
            values.get("owner_declaration_kind") == "CLASS"
            and values.get("has_body") == "true"
        ):
            return 1
        if values.get("has_body") == "true":
            return 2
        return 3
    return {
        CognitionEntityKind.TYPE: 4,
        CognitionEntityKind.FILE: 5,
        CognitionEntityKind.PACKAGE: 6,
        CognitionEntityKind.MODULE: 7,
    }[kind]


def _lightweight_action_fingerprint(
    decision: LightweightAgentDecision,
) -> tuple[object, ...]:
    """Identify a repeated investigation action without inspecting content."""

    return (
        decision.action.value,
        decision.query,
        decision.read_index,
        decision.cognition_index,
        (
            decision.relation_kind.value
            if decision.relation_kind is not None
            else None
        ),
        decision.direction.value if decision.direction is not None else None,
        decision.maximum_depth,
        decision.cursor,
    )


def _navigation_metadata_key(
    metadata: _LightweightReadNavigationMetadata,
) -> tuple[int, int]:
    return (
        (
            _cognition_entity_role_rank(
                metadata.cognition_kind,
                metadata.cognition_attributes,
            )
            if metadata.cognition_kind is not None
            else 1_000_000
        ),
        metadata.origin_cognition_index
        if metadata.origin_cognition_index is not None
        else 1_000_000,
    )


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
        # Navigation hits locate a resource but are not delivered Source
        # evidence. Do not expose their locator list as Citation ordinals:
        # the executor will correctly reject those ordinals.
        delivered_citations = tuple(
            citation
            for citation in self.citations
            if "NAVIGATION" not in citation.modality.upper()
        )
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
                for index, citation in enumerate(delivered_citations, 1)
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
    # Application-owned bookkeeping only.  It is intentionally omitted from
    # model_view and therefore does not add an Agent protocol/schema field.
    remaining_tool_actions: int | None = None
    source_tools_enabled: bool = True
    consumed_source_read_indexes: tuple[int, ...] = ()
    blocked_source_read_indexes: tuple[int, ...] = ()
    read_candidate_metadata: tuple[
        tuple[int, _LightweightReadNavigationMetadata], ...
    ] = ()

    def model_view(self) -> dict[str, object]:
        # Keep the immutable candidate registry for provenance, while exposing
        # only executable unread resources after a Source READ.  This prevents
        # the Agent from selecting a consumed line/full-file candidate again.
        visible_read_candidates = (
            () if not self.source_tools_enabled else
            _unread_read_candidates(
                self.read_candidates,
                self.observations,
                self.consumed_source_read_indexes,
            )
            if any(
                item.operation is EngineeringAgentToolOperation.SOURCE_READ
                for item in self.observations
            )
            else self.read_candidates
        )
        if self.blocked_source_read_indexes:
            blocked = set(self.blocked_source_read_indexes)
            visible_read_candidates = tuple(
                candidate
                for candidate in visible_read_candidates
                if candidate.read_index not in blocked
            )
        reserved_reads = _reserved_unread_cognition_candidates(
            visible_read_candidates,
            self.observations,
            dict(self.read_candidate_metadata),
            self.review_findings,
        )
        available_actions = ["FINISH"]
        if self.tools_enabled:
            if self.cognition_enabled:
                available_actions = [
                    "SEARCH_COGNITION", "TRAVERSE_RELATIONS",
                    "RETRIEVE_COGNITION_DETAIL", *available_actions,
                ]
            if self.source_tools_enabled:
                available_actions[-1:-1] = (
                    ["READ_SOURCE"] if reserved_reads
                    else ["SEARCH_SOURCE", "READ_SOURCE"]
                )
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
            "available_actions": available_actions,
            "read_candidates": [
                item.model_view()
                for item in _ordered_read_candidates(
                    visible_read_candidates,
                    self.observations,
                    remaining_tool_actions=self.remaining_tool_actions,
                    metadata_by_read_index=dict(self.read_candidate_metadata),
                )
            ],
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
        read_candidate_metadata: dict[
            int, _LightweightReadNavigationMetadata
        ] = {}
        cognition_candidates: list[LightweightCognitionCandidate] = []
        receipts: list[EngineeringAgentModelCallReceipt] = []
        events: list[Mapping[str, object]] = []
        rejected_answer: str | None = None
        review_findings: tuple[str, ...] = ()
        tool_actions = 0
        source_tools_enabled = True
        reviews = 0
        rewrites = 0
        # Citation selections are local to an immutable Observation prefix.
        # Keep the prefixes that have already received the one bounded
        # Application-owned binding replan.  A later Reviewer-driven Source
        # read creates a new prefix and therefore gets its own single repair;
        # repeating an invalid selection against the same prefix remains
        # fail-closed.
        citation_binding_repair_prefixes: set[tuple[tuple[int, str], ...]] = set()
        citation_binding_repair_count = 0
        decision_shape_repairs = 0
        consecutive_no_progress = 0
        executed_action_fingerprints: set[tuple[object, ...]] = set()
        executed_source_read_indexes: set[int] = set()
        blocked_source_read_indexes: set[int] = set()
        terminal = "FAILED"
        try:
            read_candidates.extend(self._prior_turn_read_candidates(request))
            for candidate in read_candidates:
                read_candidate_metadata.setdefault(
                    candidate.read_index,
                    _LightweightReadNavigationMetadata(),
                )
            for step in range(1, self._limits.maximum_agent_steps + 1):
                tools_enabled = (
                    tool_actions < self._limits.maximum_tool_actions
                    and (source_tools_enabled or self._cognition is not None)
                )
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
                            source_tools_enabled=source_tools_enabled,
                            consumed_source_read_indexes=tuple(
                                sorted(executed_source_read_indexes)
                            ),
                            blocked_source_read_indexes=tuple(
                                sorted(blocked_source_read_indexes)
                            ),
                            rejected_answer=rejected_answer,
                            review_findings=review_findings,
                            remaining_tool_actions=(
                                self._limits.maximum_tool_actions - tool_actions
                            ),
                            read_candidate_metadata=tuple(
                                sorted(read_candidate_metadata.items())
                            ),
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
                    if not source_tools_enabled and decision.action in {
                        LightweightAgentAction.SEARCH_SOURCE,
                        LightweightAgentAction.READ_SOURCE,
                    }:
                        raise DomainError(
                            ErrorCode.BUDGET_EXHAUSTED,
                            "lightweight Agent selected Source after its Broker fuse closed",
                        )
                    unread_cognition_candidates = _reserved_unread_cognition_candidates(
                        read_candidates,
                        observations,
                        read_candidate_metadata,
                        review_findings,
                    ) if source_tools_enabled else ()
                    cognition_replan_action = decision.action in {
                        LightweightAgentAction.SEARCH_COGNITION,
                        LightweightAgentAction.TRAVERSE_RELATIONS,
                        LightweightAgentAction.RETRIEVE_COGNITION_DETAIL,
                    }
                    unread_candidates = _unread_read_candidates(
                        read_candidates, observations, executed_source_read_indexes
                    )
                    unread_read_selected = (
                        decision.action is LightweightAgentAction.READ_SOURCE
                        and decision.read_index
                        in {
                            candidate.read_index for candidate in unread_candidates
                        }
                    )
                    action_fingerprint = _lightweight_action_fingerprint(decision)
                    action_repeated = action_fingerprint in executed_action_fingerprints
                    if unread_cognition_candidates and not (
                        cognition_replan_action or unread_read_selected
                    ) and not action_repeated:
                        # A Reviewer identified a gap while the trusted
                        # Application already has an unread Source option.
                        # Do not spend the fixed Tool budget on another search
                        # or cognition detour; let the same Agent replan from
                        # the existing candidate.  This is internal evidence
                        # planning, not a new model-facing action/protocol.
                        events.append(
                            {
                                "kind": "ACTION_REPLAN_REQUIRED",
                                "step": step,
                                "reason": "REVIEW_GAP_UNREAD_SOURCE",
                                "action": decision.action.value,
                                "read_index": decision.read_index,
                                "query": decision.query,
                                "candidate_read_indexes": tuple(
                                    candidate.read_index
                                    for candidate in unread_cognition_candidates
                                ),
                            }
                        )
                        review_findings = (
                            *review_findings,
                            "Application reserved the fixed Tool budget for an "
                            "existing unread Source candidate required by the "
                            "review gap. Choose READ_SOURCE for one of the "
                            "presented unread candidates; do not search or "
                            "navigate again.",
                        )
                        # This proposal was rejected before Tool execution;
                        # it therefore produced neither a tool action nor a
                        # no-progress observation. Do not let repeated
                        # planning corrections close the execution fuse
                        # needed to consume the remaining unread evidence.
                        consecutive_no_progress = 0
                        continue
                    if action_repeated:
                        # A repeated proposal is a planning failure, not a
                        # reason to dispatch the same read/search again. Keep
                        # the fixed action fuse, record the bounded recovery,
                        # and let the same Agent choose another legal action
                        # from the unchanged trusted state.
                        # A rejected duplicate never reached a Tool and must
                        # not consume the fixed Tool budget.  Charging it
                        # here lets an Agent exhaust the fuse on planning
                        # mistakes, preventing the unread evidence candidate
                        # requested by an independent Reviewer from being
                        # consumed.  Keep the duplicate in the trajectory,
                        # but reserve the budget for a distinct legal action.
                        events.append(
                            {
                                "kind": "ACTION_REPLAN_REQUIRED",
                                "step": step,
                                "reason": "REPEATED_ACTION",
                                "action": decision.action.value,
                                "read_index": decision.read_index,
                                "query": decision.query,
                            }
                        )
                        repeated_finding = (
                            "Application blocked the selected Source read because "
                            "its read_index is stale or already covered. Choose "
                            "a currently presented unread candidate; do not reuse "
                            "the stale read_index."
                            if decision.action is LightweightAgentAction.READ_SOURCE
                            and decision.read_index not in {candidate.read_index for candidate in unread_candidates}
                            and decision.read_index not in executed_source_read_indexes
                            else
                            "Application blocked the selected action because "
                            "it repeats a completed investigation action. "
                            "Update the plan and choose a different legal "
                            "action that advances the evidence; do not "
                            "repeat the same action."
                        )
                        review_findings = (*review_findings, repeated_finding)
                        # A rejected proposal is not the current executable
                        # plan. Keep it in the immutable trajectory, but do
                        # not feed the same stale plan back as active state.
                        plan = ""
                        if (
                            decision.action is LightweightAgentAction.READ_SOURCE
                            and decision.read_index is not None
                        ):
                            blocked_source_read_indexes.add(decision.read_index)
                        if unread_cognition_candidates:
                            review_findings = (
                                *review_findings,
                                "Application reserved the fixed Tool budget for an "
                                "existing unread Source candidate required by the "
                                "review gap. Choose READ_SOURCE for one of the "
                                "presented unread candidates; do not search or "
                                "navigate again.",
                            )
                        # A proposal rejected before Tool dispatch did not
                        # consume a Tool slot.  Keep the bounded planning
                        # fuse in the Agent-step loop, but never manufacture
                        # exhausted Tool budget from an application-side
                        # duplicate; unread evidence must remain executable.
                        consecutive_no_progress += 1
                        continue
                    executed_action_fingerprints.add(action_fingerprint)
                    before_count = len(observations)
                    tool_executed, source_exhausted = self._execute_action(
                        request=request,
                        decision=decision,
                        observations=observations,
                        read_candidates=read_candidates,
                        read_candidate_metadata=read_candidate_metadata,
                        cognition_candidates=cognition_candidates,
                        events=events,
                    )
                    source_tools_enabled = source_tools_enabled and not source_exhausted
                    if (
                        tool_executed
                        and decision.action is LightweightAgentAction.READ_SOURCE
                        and decision.read_index is not None
                    ):
                        executed_source_read_indexes.add(decision.read_index)
                    # A Broker rejection is a trusted boundary observation,
                    # not a consumed Source operation.  Keep the fixed tool
                    # fuse aligned with actual execution so a reserved READ
                    # slot remains available to the same Agent.
                    if tool_executed:
                        tool_actions += 1
                    progress = any(
                        item.progress for item in observations[before_count:]
                    )
                    if progress:
                        consecutive_no_progress = 0
                    elif not tool_executed:
                        consecutive_no_progress = 0
                    elif decision.action in {
                        LightweightAgentAction.SEARCH_COGNITION,
                        LightweightAgentAction.TRAVERSE_RELATIONS,
                        LightweightAgentAction.RETRIEVE_COGNITION_DETAIL,
                    }:
                        # A cognition lookup may legitimately yield no new
                        # observation when the request's entity is outside
                        # the prebuilt snapshot. Preserve one transition to
                        # the already-authorized Source search path instead
                        # of closing the whole tool fuse before the Agent can
                        # investigate the same gap in Source.
                        consecutive_no_progress = 0
                    else:
                        consecutive_no_progress += 1
                    if not progress:
                        events.append(
                            {
                                "kind": "ACTION_REPLAN_REQUIRED",
                                "step": step,
                                "reason": "NO_PROGRESS",
                                "action": decision.action.value,
                                "read_index": decision.read_index,
                                "query": decision.query,
                            }
                        )
                        review_findings = (
                            *review_findings,
                            "Application observed that the selected action "
                            "produced no new evidence. Update the plan and "
                            "choose a different legal action; do not repeat "
                            "an action that made no progress.",
                        )
                    if (
                        consecutive_no_progress
                        >= self._limits.maximum_consecutive_no_progress
                    ):
                        tool_actions = self._limits.maximum_tool_actions
                    # Keep any mechanical Citation/reviewer/shape feedback
                    # while the same Agent gathers the evidence it was asked
                    # to obtain.  Ordinary investigation starts with empty
                    # feedback, so this does not alter the normal path.
                    continue

                assert decision.answer is not None
                assert decision.response_kind is not None
                try:
                    selected = self._resolve_citations(decision, observations)
                except _CitationBindingRejection as exc:
                    observation_prefix = tuple(
                        (item.observation_index, item.digest.value)
                        for item in observations
                    )
                    if observation_prefix in citation_binding_repair_prefixes:
                        raise
                    citation_binding_repair_prefixes.add(observation_prefix)
                    citation_binding_repair_count += 1
                    # As with a rejected investigation action, the rejected
                    # FINISH proposal is not an executable current plan. Its
                    # original plan remains in MODEL_DECISION; keep the answer
                    # and binding diagnosis below as rejected state only.
                    plan = ""
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
                            "repair_ordinal": citation_binding_repair_count,
                        }
                    )
                    rejected_answer = decision.answer
                    review_findings = (
                        *review_findings,
                        "Application rejected the previous FINISH citation "
                        "selection at observation index "
                        f"{exc.observation_index}, citation index "
                        f"{exc.citation_index}; the selected observation has "
                        f"{exc.available_citation_count} delivered Citation(s). "
                        "Citation indexes are 1-based within each selected "
                        "Observation and are not global. Replan and submit "
                        "FINISH using only "
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
                if review.verdict is LightweightReviewVerdict.MORE_EVIDENCE:
                    review_findings = (
                        *review_findings,
                        "Independent review requested more evidence. Prefer "
                        "an existing unread Source candidate that directly "
                        "addresses the evidence gap before searching again; "
                        "do not repeat a completed action.",
                        *review.findings,
                    )
                else:
                    review_findings = (*review_findings, *review.findings)
                if review.verdict is LightweightReviewVerdict.REWRITE:
                    rewrites += 1
                    if rewrites > 1:
                        raise DomainError(
                            ErrorCode.CONTROL_STATE_DENIED,
                            "lightweight Agent permits at most one complete rewrite",
                        )
                    tool_actions = self._limits.maximum_tool_actions
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
        read_candidate_metadata: dict[
            int, _LightweightReadNavigationMetadata
        ],
        cognition_candidates: list[LightweightCognitionCandidate],
        events: list[Mapping[str, object]],
    ) -> tuple[bool, bool]:
        """Return execution accounting and current Broker Source-fuse state."""
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
                read_candidate_metadata=read_candidate_metadata,
                cognition_candidates=cognition_candidates,
                events=events,
            )
            return True, False
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
        current_search_citation_digests: set[Digest] = set()
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
            if (
                operation is EngineeringAgentToolOperation.SOURCE_SEARCH
                and evidence.disposition is EngineeringAgentEvidenceDisposition.SUPPORT
            ):
                current_search_citation_digests.update(item.digest for item in citations)
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
                    read_index = len(read_candidates) + 1
                    read_candidates.append(
                        LightweightReadCandidate(
                            read_index=read_index,
                            citation=citation,
                            resource_locator=_citation_resource_locator(
                                citation.locator
                            ),
                        )
                    )
                    read_candidate_metadata[read_index] = (
                        _LightweightReadNavigationMetadata(
                            origin_observation_index=index,
                        )
                    )
                    known.add(citation.citation_ref)
        if operation is EngineeringAgentToolOperation.SOURCE_SEARCH:
            # One ToolResult binds every SUPPORT/BOUNDARY receipt to this
            # exact invocation. Refresh the entire sidecar, even for an empty
            # or rejected search, so historical hits cannot retain priority.
            for candidate in read_candidates:
                metadata = read_candidate_metadata.get(
                    candidate.read_index, _LightweightReadNavigationMetadata()
                )
                read_candidate_metadata[candidate.read_index] = replace(
                    metadata,
                    current_source_search_hit=(
                        candidate.citation.digest in current_search_citation_digests
                    ),
                )
        if sum(len(item.content.encode("utf-8")) for item in observations) > (
            self._limits.maximum_evidence_package_bytes
        ):
            raise DomainError(
                ErrorCode.BUDGET_EXHAUSTED,
                "lightweight Agent evidence byte budget is exhausted",
            )
        # The authority receipt retains the typed Broker decision ledger entry;
        # use it to distinguish pre-dispatch rejection from an executed Source
        # action that legitimately returned no evidence. No model-facing protocol or
        # new versioned schema is introduced here.
        if operation in {
            EngineeringAgentToolOperation.SOURCE_SEARCH,
            EngineeringAgentToolOperation.SOURCE_READ,
        }:
            # Receipts contain the cumulative Turn ledger.  Bind the decision
            # to this result's subject and evidence digest before inspecting
            # its typed status; historical authorized entries must not charge
            # or mask the current pre-dispatch rejection.
            rejected = bool(result.evidence)
            source_exhausted = False
            for evidence in result.evidence:
                receipt = evidence.authority_receipt
                if receipt is None:
                    rejected = False
                    break
                current = [
                    entry for entry in receipt.ledger_entries
                    if entry.kind == "BROKER_DECISION"
                    and entry.subject_ref == evidence.result_ref
                    and entry.subject_digest == receipt.evidence_digest
                ]
                if not (current and all(
                    dict(entry.details).get("status") == "REJECTED"
                    for entry in current
                )):
                    rejected = False
                    break
                source_exhausted = source_exhausted or (
                    evidence.disposition is EngineeringAgentEvidenceDisposition.BOUNDARY
                    and any(
                        dict(entry.details).get("reason") in {
                            "SOURCE_OPERATION_FUSE_EXHAUSTED",
                            "SOURCE_FILE_FUSE_EXHAUSTED",
                            "SOURCE_BYTE_FUSE_EXHAUSTED",
                        }
                        for entry in current
                    )
                )
            if rejected:
                return False, source_exhausted
        return True, False

    def _execute_cognition_action(
        self,
        *,
        request: EngineeringTurnExecutionRequest,
        decision: LightweightAgentDecision,
        observations: list[LightweightObservation],
        read_candidates: list[LightweightReadCandidate],
        read_candidate_metadata: dict[
            int, _LightweightReadNavigationMetadata
        ],
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
        cognition_metadata: dict[
            int, _LightweightReadNavigationMetadata
        ] = {}
        page_entity_ids: set[StableId] = set()
        self._register_cognition_candidates(
            page,
            cognition_candidates,
            cognition_metadata,
            encountered_entity_ids=page_entity_ids,
        )
        index = len(observations) + 1
        # Keep the existing page payload (and its digest) intact, while making
        # the Application-owned invocation provenance observable to the same
        # Agent.  This is navigation metadata, not cognition evidence.
        content_payload = page.to_payload()
        content_payload["execution_provenance"] = {
            "action": decision.action.value,
            "query": decision.query,
            "cursor": decision.cursor or 0,
            "cognition_index": decision.cognition_index,
            "relation_kind": (
                decision.relation_kind.value
                if decision.relation_kind is not None
                else None
            ),
            "direction": (
                decision.direction.value if decision.direction is not None else None
            ),
            "maximum_depth": decision.maximum_depth,
        }
        content = canonical_json_bytes(content_payload).decode("utf-8")
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
            # A detail/traversal page can revisit an already registered
            # cognition entity.  Its provenance still represents a newly
            # relevant evidence gap even though candidate de-duplication
            # means it is not newly appended to the registry.  Bridge every
            # candidate
            # encountered on this page through the existing Source adapter;
            # the adapter and bridge retain their path/revision caps and
            # opaque identity checks.
            candidates=tuple(
                item
                for item in cognition_candidates
                if item.entity_id in page_entity_ids
            ),
            read_candidates=read_candidates,
            read_candidate_metadata=read_candidate_metadata,
            cognition_metadata=cognition_metadata,
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
        cognition_metadata: dict[
            int, _LightweightReadNavigationMetadata
        ] | None = None,
        encountered_entity_ids: set[StableId] | None = None,
    ) -> None:
        known_indexes = {
            item.entity_id: item.cognition_index for item in candidates
        }
        metadata = cognition_metadata if cognition_metadata is not None else {}

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
                    if encountered_entity_ids is not None:
                        encountered_entity_ids.add(entity_id)
                    parsed_kind = CognitionEntityKind(raw_kind)
                    parsed_attributes = _cognition_attributes_from_payload(
                        value.get("attributes", ())
                    )
                    cognition_index = known_indexes.get(entity_id)
                    if cognition_index is None:
                        cognition_index = len(candidates) + 1
                        candidates.append(
                            LightweightCognitionCandidate(
                                cognition_index=cognition_index,
                                entity_id=entity_id,
                                kind=parsed_kind,
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
                        known_indexes[entity_id] = cognition_index
                    candidate_metadata = _LightweightReadNavigationMetadata(
                        cognition_kind=parsed_kind,
                        cognition_attributes=parsed_attributes,
                        origin_cognition_index=cognition_index,
                    )
                    current_metadata = metadata.get(cognition_index)
                    if (
                        current_metadata is None
                        or _navigation_metadata_key(candidate_metadata)
                        < _navigation_metadata_key(current_metadata)
                    ):
                        metadata[cognition_index] = candidate_metadata
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
        read_candidate_metadata: dict[
            int, _LightweightReadNavigationMetadata
        ] | None = None,
        cognition_metadata: Mapping[
            int, _LightweightReadNavigationMetadata
        ] | None = None,
    ) -> None:
        navigation_metadata = (
            read_candidate_metadata
            if read_candidate_metadata is not None
            else {}
        )
        # Only a prior full-resource Source read covers a path.  A line hit,
        # literal hit, or navigation option in the same file is a different
        # evidence identity and must not suppress the exact cognition locator
        # that still needs a controlled Source read.
        known_full_source_paths = {
            (
                item.citation.source_revision,
                _citation_resource_locator(item.resource_locator),
            )
            for item in read_candidates
            if _is_full_source_read_candidate(item)
        }
        # A cognition navigation option is already a controlled, current-Turn
        # path capability.  The Source adapter intentionally keys that
        # capability by canonical path and returns the same opaque binding
        # when a later cognition page discovers another entity in the file.
        # Keep this suppression domain separate from full-resource coverage:
        # a line/literal/search candidate for the same path is not a
        # navigation capability and must still be bridged below.
        existing_navigation_paths: set[tuple[str, str]] = {
            (
                item.citation.source_revision,
                _citation_resource_locator(item.resource_locator),
            )
            for item in read_candidates
            if (
                item.citation.evidence_class == "SOURCE"
                and item.citation.modality == _COGNITION_NAVIGATION_MODALITY
            )
        }
        provenances: list[CognitionProvenance] = []
        selected_paths: set[str] = set()
        metadata_by_locator: dict[
            str, _LightweightReadNavigationMetadata
        ] = {}
        metadata_by_path: dict[
            tuple[str, str], _LightweightReadNavigationMetadata
        ] = {}
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
            provenance_key = (provenance.source_revision, provenance.path)
            if (
                provenance_key not in known_full_source_paths
                and provenance_key not in existing_navigation_paths
                and provenance.path not in selected_paths
            ):
                provenances.append(provenance)
                selected_paths.add(provenance.path)
            candidate_metadata = (cognition_metadata or {}).get(
                candidate.cognition_index
            )
            if candidate_metadata is None:
                candidate_metadata = _LightweightReadNavigationMetadata(
                    cognition_kind=candidate.kind,
                    origin_cognition_index=candidate.cognition_index,
                )
            current_locator = metadata_by_locator.get(provenance.locator)
            if (
                current_locator is None
                or _navigation_metadata_key(candidate_metadata)
                < _navigation_metadata_key(current_locator)
            ):
                metadata_by_locator[provenance.locator] = candidate_metadata
            current_path = metadata_by_path.get(provenance_key)
            if (
                current_path is None
                or _navigation_metadata_key(candidate_metadata)
                < _navigation_metadata_key(current_path)
            ):
                metadata_by_path[provenance_key] = candidate_metadata

        # A Source search may have issued an option before cognition discovers
        # the same exact locator.  Keep the existing candidate object and its
        # equality/value contract untouched; only record an Application-owned
        # sidecar priority keyed by the stable read_index.  Path-only matches
        # are intentionally ignored because one file can contain many
        # declarations.  If a prior cognition navigation capability already
        # represents this path, however, its opaque binding is reusable for a
        # later entity/detail even when that entity has a different exact
        # locator.  Attach the strongest typed metadata to that existing
        # candidate without changing its citation value or authority.
        for existing in read_candidates:
            metadata = metadata_by_locator.get(existing.citation.locator)
            if (
                metadata is None
                and existing.citation.evidence_class == "SOURCE"
                and existing.citation.modality == _COGNITION_NAVIGATION_MODALITY
            ):
                existing_key = (
                    existing.citation.source_revision,
                    _citation_resource_locator(existing.resource_locator),
                )
                metadata = metadata_by_path.get(existing_key)
            if metadata is None:
                continue
            current = navigation_metadata.get(existing.read_index)
            if (
                current is None
                or _navigation_metadata_key(metadata)
                < _navigation_metadata_key(current)
            ):
                navigation_metadata[existing.read_index] = (
                    _LightweightReadNavigationMetadata(
                        origin_observation_index=(
                            current.origin_observation_index
                            if current is not None
                            else 0
                        ),
                        cognition_kind=metadata.cognition_kind,
                        cognition_attributes=metadata.cognition_attributes,
                        origin_cognition_index=metadata.origin_cognition_index,
                    )
                )
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
            metadata = metadata_by_locator.get(provenance.locator)
            if metadata is not None:
                navigation_metadata[read_index] = _LightweightReadNavigationMetadata(
                    origin_observation_index=observation_index,
                    cognition_kind=metadata.cognition_kind,
                    cognition_attributes=metadata.cognition_attributes,
                    origin_cognition_index=metadata.origin_cognition_index,
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


def _is_full_source_read_candidate(candidate: LightweightReadCandidate) -> bool:
    """Return whether an existing candidate is a complete Source resource.

    Modality alone is insufficient: a SOURCE_TEXT line/fragment candidate is
    still an unresolved declaration gap.  The authority-owned resource and
    citation locator must both identify the same canonical, line-free path.
    """

    if (
        candidate.citation.evidence_class != "SOURCE"
        or candidate.citation.modality not in _FULL_SOURCE_MODALITIES
    ):
        return False
    resource = _citation_resource_locator(candidate.resource_locator)
    locator = _citation_resource_locator(candidate.citation.locator)
    return (
        resource == candidate.resource_locator
        and locator == candidate.resource_locator
        and candidate.citation.locator == candidate.resource_locator
    )


def _cognition_attributes_from_payload(
    value: object,
) -> tuple[tuple[str, str], ...]:
    """Normalize existing cognition attributes for internal navigation only."""

    if value in (None, (), []):
        return ()
    pairs: list[tuple[str, str]] = []
    if isinstance(value, Mapping):
        entries = value.items()
        for key, item in entries:
            if not isinstance(key, str) or not isinstance(item, str):
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "cognition candidate attributes are malformed",
                )
            pairs.append((key, item))
    elif isinstance(value, (list, tuple)):
        for item in value:
            if not isinstance(item, Mapping):
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "cognition candidate attributes are malformed",
                )
            key = item.get("name")
            attribute_value = item.get("value")
            if not isinstance(key, str) or not isinstance(attribute_value, str):
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "cognition candidate attributes are malformed",
                )
            pairs.append((key, attribute_value))
    else:
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "cognition candidate attributes are malformed",
        )
    normalized = tuple(sorted(pairs))
    if len({key for key, _ in normalized}) != len(normalized):
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "cognition candidate attributes are duplicated",
        )
    return normalized


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
