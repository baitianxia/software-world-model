from __future__ import annotations

from dataclasses import dataclass


SATISFIED = "SATISFIED"
GAP = "GAP"
_ASSESSMENT_STATUSES = frozenset({SATISFIED, GAP})
FACT = "FACT"
INFERENCE = "INFERENCE"
_FORMAL_KNOWLEDGE_KINDS = frozenset({FACT, INFERENCE})


def _require_text(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must not be empty")


@dataclass(frozen=True)
class KnowledgeNeed:
    """One question whose formal-knowledge sufficiency must be established."""

    need_id: str
    question: str
    sufficiency_criterion: str

    def __post_init__(self) -> None:
        _require_text(self.need_id, "need_id")
        _require_text(self.question, "question")
        _require_text(self.sufficiency_criterion, "sufficiency_criterion")


@dataclass(frozen=True)
class KnowledgeRequirement:
    """An immutable task-level knowledge sufficiency contract.

    It is intentionally not bound to a Snapshot: after a Knowledge Update, the
    same requirement must be reassessed against the newly published Snapshot
    instead of weakening or silently replacing the completion criteria.
    """

    requirement_id: str
    task_id: str
    scope_id: str
    knowledge_context_reference: str
    needs: tuple[KnowledgeNeed, ...]
    formation_model_call_id: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.requirement_id, "requirement_id")
        _require_text(self.task_id, "task_id")
        _require_text(self.scope_id, "scope_id")
        _require_text(
            self.knowledge_context_reference, "knowledge_context_reference"
        )
        if self.formation_model_call_id is not None:
            _require_text(self.formation_model_call_id, "formation_model_call_id")

        needs = tuple(self.needs)
        if not needs:
            raise ValueError("KnowledgeRequirement must contain at least one need")
        if not all(isinstance(item, KnowledgeNeed) for item in needs):
            raise TypeError("needs must contain only KnowledgeNeed values")
        need_ids = tuple(item.need_id for item in needs)
        if len(set(need_ids)) != len(need_ids):
            raise ValueError("KnowledgeRequirement need_id values must be unique")
        object.__setattr__(self, "needs", needs)


@dataclass(frozen=True)
class FormalKnowledgeReference:
    """A typed reference to one formal Fact or Inference."""

    kind: str
    reference_id: str

    def __post_init__(self) -> None:
        if self.kind not in _FORMAL_KNOWLEDGE_KINDS:
            raise ValueError(
                "kind must be one of "
                f"{sorted(_FORMAL_KNOWLEDGE_KINDS)}"
            )
        _require_text(self.reference_id, "reference_id")


@dataclass(frozen=True)
class KnowledgeSufficiencyItem:
    """The independent sufficiency decision for one KnowledgeNeed."""

    need_id: str
    status: str
    formal_knowledge_references: tuple[FormalKnowledgeReference, ...] = ()
    rationale: str = ""

    def __post_init__(self) -> None:
        _require_text(self.need_id, "need_id")
        if self.status not in _ASSESSMENT_STATUSES:
            raise ValueError(
                f"status must be one of {sorted(_ASSESSMENT_STATUSES)}"
            )

        references = tuple(self.formal_knowledge_references)
        if not all(isinstance(item, FormalKnowledgeReference) for item in references):
            raise TypeError(
                "formal knowledge references must contain only "
                "FormalKnowledgeReference values"
            )
        reference_keys = tuple(
            (item.kind, item.reference_id) for item in references
        )
        if len(set(reference_keys)) != len(reference_keys):
            raise ValueError(
                "formal knowledge references must be unique by kind and reference_id"
            )
        if self.status == SATISFIED and not references:
            raise ValueError("SATISFIED needs must cite formal knowledge")
        object.__setattr__(self, "formal_knowledge_references", references)

    @property
    def formal_knowledge_reference_ids(self) -> tuple[str, ...]:
        """Compatibility view for callers that only need reference IDs."""

        return tuple(item.reference_id for item in self.formal_knowledge_references)


@dataclass(frozen=True)
class KnowledgeSufficiencyAssessment:
    """A complete, Snapshot-bound assessment of a KnowledgeRequirement."""

    assessment_id: str
    requirement: KnowledgeRequirement
    snapshot_id: str
    knowledge_context_reference: str
    items: tuple[KnowledgeSufficiencyItem, ...]
    assessment_model_call_id: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.assessment_id, "assessment_id")
        if not isinstance(self.requirement, KnowledgeRequirement):
            raise TypeError("requirement must be a KnowledgeRequirement")
        _require_text(self.snapshot_id, "snapshot_id")
        _require_text(
            self.knowledge_context_reference, "knowledge_context_reference"
        )
        if self.assessment_model_call_id is not None:
            _require_text(self.assessment_model_call_id, "assessment_model_call_id")
        if (
            self.knowledge_context_reference
            != self.requirement.knowledge_context_reference
        ):
            raise ValueError(
                "assessment and KnowledgeRequirement must bind the same "
                "KnowledgeContext"
            )

        items = tuple(self.items)
        if not all(isinstance(item, KnowledgeSufficiencyItem) for item in items):
            raise TypeError(
                "items must contain only KnowledgeSufficiencyItem values"
            )
        assessed_need_ids = tuple(item.need_id for item in items)
        if len(set(assessed_need_ids)) != len(assessed_need_ids):
            raise ValueError("each KnowledgeNeed may be assessed only once")
        required_need_ids = {item.need_id for item in self.requirement.needs}
        if set(assessed_need_ids) != required_need_ids:
            missing = sorted(required_need_ids - set(assessed_need_ids))
            unknown = sorted(set(assessed_need_ids) - required_need_ids)
            raise ValueError(
                "assessment must map every and only the requirement's needs; "
                f"missing={missing}, unknown={unknown}"
            )
        object.__setattr__(self, "items", items)

    @property
    def requirement_id(self) -> str:
        return self.requirement.requirement_id

    @property
    def complete(self) -> bool:
        """Completion is derived solely from the exhaustive item decisions."""

        return all(item.status == SATISFIED for item in self.items)
