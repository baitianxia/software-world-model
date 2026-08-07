from __future__ import annotations

from dataclasses import dataclass


KNOWLEDGE_SCHEMA_VERSION = "1.1"
CANDIDATE_ONLY_BUILD_PROFILE = "candidate-only"


@dataclass(frozen=True)
class KnowledgeBuildTarget:
    """Application-selected semantic goals; contains questions, not answers."""

    behavior_methods: tuple[tuple[str, str], ...] = ()
    business_constraint_methods: tuple[tuple[str, str], ...] = ()
    capability_modules: tuple[str, ...] = ()
    history_commits: tuple[str, ...] = ()
    required_inference_types: tuple[str, ...] = ()
    premise_fact_ids: tuple[str, ...] = ()
    premise_inference_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class KnowledgeEntity:
    entity_id: str
    scope_id: str
    entity_type: str
    name: str


@dataclass(frozen=True)
class Evidence:
    evidence_id: str
    artifact_id: str
    scope_id: str
    revision: str
    line_start: int
    line_end: int
    quote: str
    quote_hash: str


@dataclass(frozen=True)
class FactCandidate:
    fact_id: str
    scope_id: str
    revision: str
    subject_id: str
    predicate: str
    object_id: str
    evidence_ids: tuple[str, ...]
    proposition: str = ""
    model_call_id: str | None = None


@dataclass(frozen=True)
class FormalFact:
    fact_id: str
    scope_id: str
    revision: str
    subject_id: str
    predicate: str
    object_id: str
    evidence_ids: tuple[str, ...]
    proposition: str = ""
    model_call_id: str | None = None


@dataclass(frozen=True)
class InferenceCandidate:
    inference_id: str
    scope_id: str
    revision: str
    inference_type: str
    statement: str
    support_fact_ids: tuple[str, ...]
    dependency_inference_ids: tuple[str, ...] = ()
    model_call_id: str | None = None


@dataclass(frozen=True)
class FormalInference:
    inference_id: str
    scope_id: str
    revision: str
    inference_type: str
    statement: str
    support_fact_ids: tuple[str, ...]
    dependency_inference_ids: tuple[str, ...] = ()
    model_call_id: str | None = None


@dataclass(frozen=True)
class KnowledgePackage:
    scope_id: str
    revision: str
    entities: tuple[KnowledgeEntity, ...]
    evidence: tuple[Evidence, ...]
    facts: tuple[FormalFact, ...]
    inferences: tuple[FormalInference, ...] = ()


@dataclass(frozen=True)
class KnowledgeBuild:
    package: KnowledgePackage | None
    errors: tuple[str, ...]
    diagnostics: tuple[str, ...] = ()
