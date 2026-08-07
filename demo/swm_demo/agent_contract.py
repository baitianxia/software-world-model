from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from swm_demo.artifact_contract import SourceCollection
from swm_demo.knowledge_requirement import (
    GAP,
    SATISFIED,
    KnowledgeNeed,
    KnowledgeRequirement,
    KnowledgeSufficiencyAssessment,
    KnowledgeSufficiencyItem,
)
from swm_demo.knowledge_update import (
    BuildIntent,
    CandidateBundle,
    InvestigationHandle,
    KnowledgeUpdateResult,
)


class KnowledgeUseServices(Protocol):
    def current_snapshot(self, scope_id: str) -> dict[str, object]: ...

    def query_structure(self, scope_id: str) -> dict[str, object]: ...

    def query_endpoint_structure(
        self, scope_id: str, endpoint_name: str
    ) -> dict[str, object]: ...

    def query_semantic_view(
        self, scope_id: str, view_name: str
    ) -> dict[str, object]: ...

    def open_knowledge_context(self, scope_id: str) -> dict[str, object]: ...

    def search_knowledge(
        self,
        scope_id: str,
        snapshot_token: str,
        kind: str,
        query: str,
        match_mode: str = "CONTAINS",
        type_name: str | None = None,
        limit: int = 20,
        cursor: int = 0,
    ) -> dict[str, object]: ...

    def query_knowledge_neighborhood(
        self,
        scope_id: str,
        snapshot_token: str,
        entity_ids: tuple[str, ...],
        direction: str = "BOTH",
        predicates: tuple[str, ...] = (),
        limit: int = 100,
        cursor: int = 0,
    ) -> dict[str, object]: ...

    def explain_knowledge_batch(
        self,
        scope_id: str,
        snapshot_token: str,
        kind: str,
        knowledge_ids: tuple[str, ...],
    ) -> dict[str, object]: ...

    def validate_sufficiency_assessment(
        self, assessment: KnowledgeSufficiencyAssessment
    ) -> dict[str, object]: ...


class AgentApplicationServices(KnowledgeUseServices, Protocol):
    def update_knowledge(
        self, scope_id: str, build_profile: str = "structure-core"
    ) -> dict[str, object]: ...

    def start_model_led_update(
        self, intent: BuildIntent, model_context_id: str
    ) -> InvestigationHandle: ...

    def collect_investigation_sources(self, run_id: str) -> SourceCollection: ...

    def investigation_formal_premises(
        self, run_id: str
    ) -> dict[str, object]: ...

    def submit_investigation_candidates(
        self, run_id: str, bundle: CandidateBundle
    ) -> KnowledgeUpdateResult: ...


@dataclass(frozen=True)
class AgentTask:
    task_id: str
    original_request: str
    scope_id: str
    use_case: str
    parameters: dict[str, object]
    routing_model_call_id: str


@dataclass(frozen=True)
class AnswerClaim:
    text: str
    knowledge_reference_ids: tuple[str, ...]
    need_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class AnswerCandidate:
    candidate_id: str
    task_id: str
    original_request: str
    scope_id: str
    snapshot_id: str
    revision: str
    claims: tuple[AnswerClaim, ...]
    answer: str
    drafting_model_call_id: str
    assessment_reference: str | None = None
    requirement: KnowledgeRequirement | None = None
    assessment: KnowledgeSufficiencyAssessment | None = None
    answer_model_context_id: str | None = None


@dataclass(frozen=True)
class AnswerReviewResult:
    decision: str
    issues: tuple[str, ...]
    review_model_call_id: str | None


@dataclass(frozen=True)
class FinalResponse:
    status: str
    answer: str | None
    snapshot_id: str | None
    knowledge_reference_ids: tuple[str, ...]
    review: AnswerReviewResult
