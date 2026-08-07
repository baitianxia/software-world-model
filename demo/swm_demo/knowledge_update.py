from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable, TypeVar

from swm_demo.artifact_contract import ArtifactRequest, SourceCollection
from swm_demo.ids import content_hash, stable_id
from swm_demo.knowledge_contract import (
    Evidence,
    FactCandidate,
    InferenceCandidate,
    KnowledgeBuildTarget,
    KnowledgeEntity,
)
from swm_demo.knowledge_requirement import (
    GAP,
    KnowledgeSufficiencyAssessment,
)


_T = TypeVar("_T")


def _require_text(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must not be empty")


def _unique_text_tuple(values: tuple[str, ...], field_name: str) -> tuple[str, ...]:
    items = tuple(values)
    for item in items:
        _require_text(item, f"{field_name} item")
    if len(set(items)) != len(items):
        raise ValueError(f"{field_name} values must be unique")
    return items


def _typed_tuple(
    values: tuple[_T, ...], expected_type: type[_T], field_name: str
) -> tuple[_T, ...]:
    items = tuple(values)
    if not all(isinstance(item, expected_type) for item in items):
        raise TypeError(
            f"{field_name} must contain only {expected_type.__name__} values"
        )
    return items


def _require_unique_objects(
    values: tuple[_T, ...], key: Callable[[_T], str], field_name: str
) -> None:
    identifiers = tuple(key(item) for item in values)
    for identifier in identifiers:
        _require_text(identifier, f"{field_name} ID")
    if len(set(identifiers)) != len(identifiers):
        raise ValueError(f"{field_name} IDs must be unique")


@dataclass(frozen=True)
class BuildIntent:
    """Frozen bridge from one Snapshot-bound gap to a Knowledge Update.

    This is task-time application state.  It identifies knowledge that must be
    constructed, but carries no proposed answer or source-derived conclusion.
    """

    intent_id: str
    requirement_id: str
    scope_id: str
    assessment: KnowledgeSufficiencyAssessment
    gap_need_ids: tuple[str, ...]
    artifact_request: ArtifactRequest
    build_target: KnowledgeBuildTarget
    target_revision: str
    minimum_result_need_ids: tuple[str, ...]
    formation_model_call_id: str

    def __post_init__(self) -> None:
        _require_text(self.intent_id, "intent_id")
        _require_text(self.requirement_id, "requirement_id")
        _require_text(self.scope_id, "scope_id")
        _require_text(self.target_revision, "target_revision")
        _require_text(self.formation_model_call_id, "formation_model_call_id")

        if not isinstance(self.assessment, KnowledgeSufficiencyAssessment):
            raise TypeError("assessment must be a KnowledgeSufficiencyAssessment")
        if not isinstance(self.artifact_request, ArtifactRequest):
            raise TypeError("artifact_request must be an ArtifactRequest")
        if not isinstance(self.build_target, KnowledgeBuildTarget):
            raise TypeError("build_target must be a KnowledgeBuildTarget")
        if self.assessment.complete:
            raise ValueError("BuildIntent requires an incomplete GAP assessment")
        if self.requirement_id != self.assessment.requirement_id:
            raise ValueError("BuildIntent and assessment Requirement differ")
        if self.scope_id != self.assessment.requirement.scope_id:
            raise ValueError("BuildIntent and assessment Scope differ")
        if (
            self.artifact_request.revision is not None
            and self.artifact_request.revision != self.target_revision
        ):
            raise ValueError(
                "ArtifactRequest revision must equal BuildIntent target_revision"
            )

        gap_need_ids = _unique_text_tuple(self.gap_need_ids, "gap_need_ids")
        assessed_gap_need_ids = tuple(
            item.need_id for item in self.assessment.items if item.status == GAP
        )
        if set(gap_need_ids) != set(assessed_gap_need_ids):
            raise ValueError(
                "gap_need_ids must exactly match every GAP in the assessment"
            )

        minimum_result_need_ids = _unique_text_tuple(
            self.minimum_result_need_ids, "minimum_result_need_ids"
        )
        if set(minimum_result_need_ids) != set(gap_need_ids):
            raise ValueError(
                "minimum_result_need_ids must exactly cover all gap_need_ids"
            )

        object.__setattr__(self, "gap_need_ids", gap_need_ids)
        object.__setattr__(
            self, "minimum_result_need_ids", minimum_result_need_ids
        )


@dataclass(frozen=True)
class CandidateBundle:
    """One model proposal submitted to the existing knowledge-admission path."""

    bundle_id: str
    intent_id: str
    scope_id: str
    source_artifact_ids: tuple[str, ...]
    entities: tuple[KnowledgeEntity, ...]
    evidence: tuple[Evidence, ...]
    fact_candidates: tuple[FactCandidate, ...]
    inference_candidates: tuple[InferenceCandidate, ...]
    covered_need_ids: tuple[str, ...]
    unresolved_need_ids: tuple[str, ...]
    proposal_model_call_id: str

    def __post_init__(self) -> None:
        _require_text(self.bundle_id, "bundle_id")
        _require_text(self.intent_id, "intent_id")
        _require_text(self.scope_id, "scope_id")
        _require_text(self.proposal_model_call_id, "proposal_model_call_id")

        source_artifact_ids = _unique_text_tuple(
            self.source_artifact_ids, "source_artifact_ids"
        )
        entities = _typed_tuple(self.entities, KnowledgeEntity, "entities")
        evidence = _typed_tuple(self.evidence, Evidence, "evidence")
        fact_candidates = _typed_tuple(
            self.fact_candidates, FactCandidate, "fact_candidates"
        )
        inference_candidates = _typed_tuple(
            self.inference_candidates,
            InferenceCandidate,
            "inference_candidates",
        )
        covered_need_ids = _unique_text_tuple(
            self.covered_need_ids, "covered_need_ids"
        )
        unresolved_need_ids = _unique_text_tuple(
            self.unresolved_need_ids, "unresolved_need_ids"
        )

        _require_unique_objects(entities, lambda item: item.entity_id, "Entity")
        _require_unique_objects(evidence, lambda item: item.evidence_id, "Evidence")
        _require_unique_objects(
            fact_candidates, lambda item: item.fact_id, "Fact Candidate"
        )
        _require_unique_objects(
            inference_candidates,
            lambda item: item.inference_id,
            "Inference Candidate",
        )

        if set(covered_need_ids) & set(unresolved_need_ids):
            raise ValueError(
                "covered_need_ids and unresolved_need_ids must not overlap"
            )

        content = (*entities, *evidence, *fact_candidates, *inference_candidates)
        for item in content:
            if item.scope_id != self.scope_id:
                raise ValueError("all CandidateBundle content must share its Scope")

        source_artifact_id_set = set(source_artifact_ids)
        for item in evidence:
            _require_text(item.artifact_id, "Evidence artifact_id")
            if item.artifact_id not in source_artifact_id_set:
                raise ValueError(
                    f"Evidence references an Artifact outside the bundle: "
                    f"{item.evidence_id}"
                )

        evidence_ids = {item.evidence_id for item in evidence}
        for candidate in fact_candidates:
            if candidate.model_call_id != self.proposal_model_call_id:
                raise ValueError(
                    "Fact Candidate model_call_id must match the Candidate "
                    "Bundle proposal_model_call_id"
                )
            _require_text(candidate.subject_id, "Fact Candidate subject_id")
            _require_text(candidate.object_id, "Fact Candidate object_id")
            candidate_evidence_ids = _unique_text_tuple(
                candidate.evidence_ids,
                f"Fact Candidate {candidate.fact_id} evidence_ids",
            )
            if not candidate_evidence_ids:
                raise ValueError(
                    f"Fact Candidate has no Evidence: {candidate.fact_id}"
                )
            missing = sorted(set(candidate_evidence_ids) - evidence_ids)
            if missing:
                raise ValueError(
                    f"Fact Candidate references Evidence outside the bundle: "
                    f"{candidate.fact_id}; missing={missing}"
                )

        for candidate in inference_candidates:
            if candidate.model_call_id != self.proposal_model_call_id:
                raise ValueError(
                    "Inference Candidate model_call_id must match the Candidate "
                    "Bundle proposal_model_call_id"
                )
            _unique_text_tuple(
                candidate.support_fact_ids,
                f"Inference Candidate {candidate.inference_id} support_fact_ids",
            )
            _unique_text_tuple(
                candidate.dependency_inference_ids,
                (
                    f"Inference Candidate {candidate.inference_id} "
                    "dependency_inference_ids"
                ),
            )
            if candidate.model_call_id is not None:
                _require_text(
                    candidate.model_call_id,
                    f"Inference Candidate {candidate.inference_id} model_call_id",
                )

        object.__setattr__(self, "source_artifact_ids", source_artifact_ids)
        object.__setattr__(self, "entities", entities)
        object.__setattr__(self, "evidence", evidence)
        object.__setattr__(self, "fact_candidates", fact_candidates)
        object.__setattr__(self, "inference_candidates", inference_candidates)
        object.__setattr__(self, "covered_need_ids", covered_need_ids)
        object.__setattr__(self, "unresolved_need_ids", unresolved_need_ids)


_PROPOSAL_KEYS = frozenset(
    {
        "schema_version",
        "entities",
        "evidence",
        "fact_candidates",
        "inference_candidates",
        "covered_need_ids",
        "unresolved_need_ids",
    }
)


def _proposal_object(
    value: object,
    field_name: str,
    *,
    allowed_keys: frozenset[str],
    required_keys: frozenset[str] = frozenset(),
) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be an object")
    if not all(isinstance(key, str) for key in value):
        raise ValueError(f"{field_name} keys must be strings")
    unknown = sorted(set(value) - allowed_keys)
    if unknown:
        raise ValueError(f"{field_name} contains unknown fields: {unknown}")
    missing = sorted(required_keys - set(value))
    if missing:
        raise ValueError(f"{field_name} is missing required fields: {missing}")
    return value


def _proposal_array(value: object, field_name: str) -> tuple[object, ...]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{field_name} must be an array")
    return tuple(value)


def _proposal_text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _proposal_text_array(value: object, field_name: str) -> tuple[str, ...]:
    values = _proposal_array(value, field_name)
    items = tuple(
        _proposal_text(item, f"{field_name}[{index}]")
        for index, item in enumerate(values)
    )
    if len(set(items)) != len(items):
        raise ValueError(f"{field_name} values must be unique")
    return items


def _proposal_line(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{field_name} must be a positive integer")
    return value


def _register_proposal_key(
    key: str, seen: set[str], field_name: str
) -> None:
    if key in seen:
        raise ValueError(f"duplicate {field_name}: {key}")
    seen.add(key)


def parse_candidate_bundle(
    proposal: object,
    *,
    intent: BuildIntent,
    collection: SourceCollection,
    proposal_model_call_id: str,
) -> CandidateBundle:
    """Strictly turn a model proposal into platform-owned candidates.

    Model output contains semantic values, local ``key`` references and
    Evidence locators only. Source text, hashes, revisions, durable identities
    and model-call provenance are reconstructed from this run's frozen
    ``SourceCollection`` so a proposal cannot forge them.
    """

    if not isinstance(intent, BuildIntent):
        raise TypeError("intent must be a BuildIntent")
    if not isinstance(collection, SourceCollection):
        raise TypeError("collection must be a SourceCollection")
    model_call_id = _proposal_text(
        proposal_model_call_id, "proposal_model_call_id"
    )
    if collection.scope_id != intent.scope_id:
        raise ValueError("SourceCollection and BuildIntent Scope differ")

    output = _proposal_object(
        proposal,
        "candidate proposal",
        allowed_keys=_PROPOSAL_KEYS,
        required_keys=frozenset({"covered_need_ids", "unresolved_need_ids"}),
    )
    schema_version = "candidate-proposal.v1"
    if "schema_version" in output:
        schema_version = _proposal_text(
            output["schema_version"], "candidate proposal.schema_version"
        )
        if schema_version not in {
            "candidate-proposal.v1",
            "candidate-proposal.v2",
        }:
            raise ValueError(
                f"unsupported candidate proposal schema_version: {schema_version}"
            )

    covered_need_ids = _proposal_text_array(
        output["covered_need_ids"], "candidate proposal.covered_need_ids"
    )
    unresolved_need_ids = _proposal_text_array(
        output["unresolved_need_ids"], "candidate proposal.unresolved_need_ids"
    )
    if set(covered_need_ids) & set(unresolved_need_ids):
        raise ValueError("covered and unresolved Need IDs must not overlap")
    if set((*covered_need_ids, *unresolved_need_ids)) != set(intent.gap_need_ids):
        raise ValueError(
            "covered and unresolved Need IDs must exactly partition BuildIntent gaps"
        )

    entity_values = _proposal_array(
        output.get("entities", []), "candidate proposal.entities"
    )
    entity_keys: set[str] = set()
    entities_by_key: dict[str, KnowledgeEntity] = {}
    for index, value in enumerate(entity_values):
        field = f"candidate proposal.entities[{index}]"
        item = _proposal_object(
            value,
            field,
            allowed_keys=frozenset({"key", "entity_type", "name"}),
            required_keys=frozenset({"key", "entity_type", "name"}),
        )
        key = _proposal_text(item["key"], f"{field}.key")
        _register_proposal_key(key, entity_keys, "Entity key")
        entity_type = _proposal_text(
            item["entity_type"], f"{field}.entity_type"
        )
        name = _proposal_text(item["name"], f"{field}.name")
        entities_by_key[key] = KnowledgeEntity(
            entity_id=stable_id("entity", intent.scope_id, entity_type, name),
            scope_id=intent.scope_id,
            entity_type=entity_type,
            name=name,
        )

    artifacts_by_id = {
        artifact.artifact_id: artifact for artifact in collection.artifacts
    }
    if len(artifacts_by_id) != len(collection.artifacts):
        raise ValueError("SourceCollection Artifact IDs must be unique")

    evidence_values = _proposal_array(
        output.get("evidence", []), "candidate proposal.evidence"
    )
    evidence_keys: set[str] = set()
    evidence_by_key: dict[str, Evidence] = {}
    for index, value in enumerate(evidence_values):
        field = f"candidate proposal.evidence[{index}]"
        item = _proposal_object(
            value,
            field,
            allowed_keys=frozenset(
                {"key", "artifact_id", "line_start", "line_end"}
            ),
            required_keys=frozenset(
                {"key", "artifact_id", "line_start", "line_end"}
            ),
        )
        key = _proposal_text(item["key"], f"{field}.key")
        _register_proposal_key(key, evidence_keys, "Evidence key")
        artifact_id = _proposal_text(
            item["artifact_id"], f"{field}.artifact_id"
        )
        artifact = artifacts_by_id.get(artifact_id)
        if artifact is None:
            raise ValueError(
                f"{field}.artifact_id is outside this SourceCollection: "
                f"{artifact_id}"
            )
        if artifact.scope_id != intent.scope_id:
            raise ValueError(f"{field}.artifact_id has a different Scope")
        line_start = _proposal_line(item["line_start"], f"{field}.line_start")
        line_end = _proposal_line(item["line_end"], f"{field}.line_end")
        lines = artifact.content.splitlines()
        if line_end < line_start or line_end > len(lines):
            raise ValueError(
                f"{field} locator is outside Artifact {artifact_id}: "
                f"{line_start}-{line_end}"
            )
        quote = "\n".join(
            line.strip() for line in lines[line_start - 1 : line_end]
        )
        quote_hash = content_hash(quote)
        evidence_by_key[key] = Evidence(
            evidence_id=stable_id(
                "evidence", artifact_id, line_start, line_end, quote_hash
            ),
            artifact_id=artifact_id,
            scope_id=intent.scope_id,
            revision=artifact.revision,
            line_start=line_start,
            line_end=line_end,
            quote=quote,
            quote_hash=quote_hash,
        )

    fact_values = _proposal_array(
        output.get("fact_candidates", []),
        "candidate proposal.fact_candidates",
    )
    fact_keys: set[str] = set()
    facts_by_key: dict[str, FactCandidate] = {}
    for index, value in enumerate(fact_values):
        field = f"candidate proposal.fact_candidates[{index}]"
        item = _proposal_object(
            value,
            field,
            allowed_keys=frozenset(
                {
                    "key",
                    "subject",
                    "predicate",
                    "object",
                    "evidence",
                    "proposition",
                }
            ),
            required_keys=frozenset(
                {
                    "key",
                    "subject",
                    "predicate",
                    "object",
                    "evidence",
                    "proposition",
                }
            ),
        )
        key = _proposal_text(item["key"], f"{field}.key")
        _register_proposal_key(key, fact_keys, "Fact key")
        subject_key = _proposal_text(item["subject"], f"{field}.subject")
        object_key = _proposal_text(item["object"], f"{field}.object")
        subject = entities_by_key.get(subject_key)
        object_ = entities_by_key.get(object_key)
        if subject is None:
            raise ValueError(f"{field}.subject references unknown Entity: {subject_key}")
        if object_ is None:
            raise ValueError(f"{field}.object references unknown Entity: {object_key}")
        evidence_keys_for_fact = _proposal_text_array(
            item["evidence"], f"{field}.evidence"
        )
        if not evidence_keys_for_fact:
            raise ValueError(f"{field}.evidence must not be empty")
        linked_evidence: list[Evidence] = []
        for evidence_key in evidence_keys_for_fact:
            evidence = evidence_by_key.get(evidence_key)
            if evidence is None:
                raise ValueError(
                    f"{field}.evidence references unknown Evidence: {evidence_key}"
                )
            linked_evidence.append(evidence)
        revisions = {evidence.revision for evidence in linked_evidence}
        if len(revisions) != 1:
            raise ValueError(f"{field}.evidence spans multiple source revisions")
        revision = next(iter(revisions))
        predicate = _proposal_text(item["predicate"], f"{field}.predicate")
        proposition = _proposal_text(
            item["proposition"], f"{field}.proposition"
        )
        canonical_proposition = (
            f"{subject.entity_type} {subject.name!r} "
            f"--{predicate}--> {object_.entity_type} {object_.name!r}"
        )
        identity_parts: tuple[object, ...] = (
            intent.scope_id,
            subject.entity_id,
            predicate,
            object_.entity_id,
        )
        if proposition != canonical_proposition:
            identity_parts = (*identity_parts, proposition)
        facts_by_key[key] = FactCandidate(
            fact_id=stable_id("fact", *identity_parts),
            scope_id=intent.scope_id,
            revision=revision,
            subject_id=subject.entity_id,
            predicate=predicate,
            object_id=object_.entity_id,
            evidence_ids=tuple(item.evidence_id for item in linked_evidence),
            proposition=proposition,
            model_call_id=model_call_id,
        )

    inference_values = _proposal_array(
        output.get("inference_candidates", []),
        "candidate proposal.inference_candidates",
    )
    inference_keys: set[str] = set()
    inferences: tuple[InferenceCandidate, ...]
    if schema_version == "candidate-proposal.v2":
        allowed_fact_ids = set(intent.build_target.premise_fact_ids)
        allowed_inference_ids = set(intent.build_target.premise_inference_ids)
        candidate_fact_ids = {item.fact_id for item in facts_by_key.values()}
        parsed: list[InferenceCandidate] = []
        for index, value in enumerate(inference_values):
            field = f"candidate proposal.inference_candidates[{index}]"
            item = _proposal_object(
                value,
                field,
                allowed_keys=frozenset(
                    {
                        "key",
                        "inference_type",
                        "statement",
                        "premise_fact_ids",
                        "premise_inference_ids",
                    }
                ),
                required_keys=frozenset(
                    {
                        "key",
                        "inference_type",
                        "statement",
                        "premise_fact_ids",
                        "premise_inference_ids",
                    }
                ),
            )
            key = _proposal_text(item["key"], f"{field}.key")
            _register_proposal_key(key, inference_keys, "Inference key")
            inference_type = _proposal_text(
                item["inference_type"], f"{field}.inference_type"
            )
            statement = _proposal_text(item["statement"], f"{field}.statement")
            support_ids = _proposal_text_array(
                item["premise_fact_ids"], f"{field}.premise_fact_ids"
            )
            dependency_ids = _proposal_text_array(
                item["premise_inference_ids"],
                f"{field}.premise_inference_ids",
            )
            if not support_ids:
                raise ValueError(f"{field}.premise_fact_ids must not be empty")
            if set(support_ids) & candidate_fact_ids:
                raise ValueError(
                    f"{field} cannot use a Fact Candidate from the same Bundle "
                    "as an Inference premise"
                )
            unknown_facts = sorted(set(support_ids) - allowed_fact_ids)
            unknown_inferences = sorted(
                set(dependency_ids) - allowed_inference_ids
            )
            if unknown_facts or unknown_inferences:
                raise ValueError(
                    f"{field} references formal premises outside the frozen "
                    "Build Target: facts="
                    f"{unknown_facts}, inferences={unknown_inferences}"
                )
            parsed.append(
                InferenceCandidate(
                    inference_id=stable_id(
                        "inference",
                        intent.scope_id,
                        inference_type,
                        statement,
                        *tuple(sorted(set(support_ids))),
                        *tuple(sorted(set(dependency_ids))),
                    ),
                    scope_id=intent.scope_id,
                    revision=intent.target_revision,
                    inference_type=inference_type,
                    statement=statement,
                    support_fact_ids=support_ids,
                    dependency_inference_ids=dependency_ids,
                    model_call_id=model_call_id,
                )
            )
        inferences = tuple(parsed)
    else:
        inference_specs: dict[
            str, tuple[str, str, tuple[str, ...], tuple[str, ...]]
        ] = {}
        inference_order: list[str] = []
        for index, value in enumerate(inference_values):
            field = f"candidate proposal.inference_candidates[{index}]"
            item = _proposal_object(
                value,
                field,
                allowed_keys=frozenset(
                    {
                        "key",
                        "inference_type",
                        "statement",
                        "support_facts",
                        "dependencies",
                    }
                ),
                required_keys=frozenset(
                    {"key", "inference_type", "statement", "support_facts"}
                ),
            )
            key = _proposal_text(item["key"], f"{field}.key")
            _register_proposal_key(key, inference_keys, "Inference key")
            inference_type = _proposal_text(
                item["inference_type"], f"{field}.inference_type"
            )
            statement = _proposal_text(item["statement"], f"{field}.statement")
            support_fact_keys = _proposal_text_array(
                item["support_facts"], f"{field}.support_facts"
            )
            if not support_fact_keys:
                raise ValueError(f"{field}.support_facts must not be empty")
            dependency_keys = _proposal_text_array(
                item.get("dependencies", []), f"{field}.dependencies"
            )
            inference_specs[key] = (
                inference_type,
                statement,
                support_fact_keys,
                dependency_keys,
            )
            inference_order.append(key)

        inferences_by_key: dict[str, InferenceCandidate] = {}
        resolving: set[str] = set()

        def resolve_inference(key: str) -> InferenceCandidate:
            existing = inferences_by_key.get(key)
            if existing is not None:
                return existing
            spec = inference_specs.get(key)
            if spec is None:
                raise ValueError(f"Inference dependency references unknown key: {key}")
            if key in resolving:
                raise ValueError(f"Inference dependency cycle at key: {key}")
            resolving.add(key)
            inference_type, statement, support_keys, dependency_keys = spec
            support_facts: list[FactCandidate] = []
            for support_key in support_keys:
                support = facts_by_key.get(support_key)
                if support is None:
                    raise ValueError(
                        f"Inference {key} references unknown Fact: {support_key}"
                    )
                support_facts.append(support)
            dependencies = [resolve_inference(item) for item in dependency_keys]
            revisions = {
                *(item.revision for item in support_facts),
                *(item.revision for item in dependencies),
            }
            if len(revisions) != 1:
                raise ValueError(f"Inference {key} support spans multiple revisions")
            revision = next(iter(revisions))
            support_ids = tuple(item.fact_id for item in support_facts)
            dependency_ids = tuple(item.inference_id for item in dependencies)
            inference = InferenceCandidate(
                inference_id=stable_id(
                    "inference",
                    intent.scope_id,
                    inference_type,
                    statement,
                    *tuple(sorted(set(support_ids))),
                    *tuple(sorted(set(dependency_ids))),
                ),
                scope_id=intent.scope_id,
                revision=revision,
                inference_type=inference_type,
                statement=statement,
                support_fact_ids=support_ids,
                dependency_inference_ids=dependency_ids,
                model_call_id=model_call_id,
            )
            resolving.remove(key)
            inferences_by_key[key] = inference
            return inference

        inferences = tuple(resolve_inference(key) for key in inference_order)
    entities = tuple(entities_by_key.values())
    evidence = tuple(evidence_by_key.values())
    facts = tuple(facts_by_key.values())
    source_artifact_ids = tuple(
        sorted({item.artifact_id for item in evidence})
    )
    return CandidateBundle(
        bundle_id=stable_id("candidate-bundle", intent.intent_id, model_call_id),
        intent_id=intent.intent_id,
        scope_id=intent.scope_id,
        source_artifact_ids=source_artifact_ids,
        entities=entities,
        evidence=evidence,
        fact_candidates=facts,
        inference_candidates=inferences,
        covered_need_ids=covered_need_ids,
        unresolved_need_ids=unresolved_need_ids,
        proposal_model_call_id=model_call_id,
    )


class InvestigationState(str, Enum):
    OPEN = "OPEN"
    PUBLISHING = "PUBLISHING"
    PUBLISHED = "PUBLISHED"
    FAILED = "FAILED"
    ABORTED = "ABORTED"


@dataclass(frozen=True)
class InvestigationHandle:
    run_id: str
    intent_id: str
    model_context_id: str
    state: InvestigationState

    def __post_init__(self) -> None:
        _require_text(self.run_id, "run_id")
        _require_text(self.intent_id, "intent_id")
        _require_text(self.model_context_id, "model_context_id")
        if not isinstance(self.state, InvestigationState):
            raise TypeError("state must be an InvestigationState")


@dataclass(frozen=True)
class KnowledgeUpdateResult:
    """Content-free result allowed to cross from investigation to answer use."""

    intent_id: str
    run_id: str
    previous_snapshot_id: str | None
    published_snapshot_id: str | None
    status: str
    admitted_reference_ids: tuple[str, ...]
    rejected_candidate_ids: tuple[str, ...]
    unresolved_need_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_text(self.intent_id, "intent_id")
        _require_text(self.run_id, "run_id")
        if self.previous_snapshot_id is not None:
            _require_text(self.previous_snapshot_id, "previous_snapshot_id")
        if self.published_snapshot_id is not None:
            _require_text(self.published_snapshot_id, "published_snapshot_id")
        _require_text(self.status, "status")

        object.__setattr__(
            self,
            "admitted_reference_ids",
            _unique_text_tuple(
                self.admitted_reference_ids, "admitted_reference_ids"
            ),
        )
        object.__setattr__(
            self,
            "rejected_candidate_ids",
            _unique_text_tuple(
                self.rejected_candidate_ids, "rejected_candidate_ids"
            ),
        )
        object.__setattr__(
            self,
            "unresolved_need_ids",
            _unique_text_tuple(self.unresolved_need_ids, "unresolved_need_ids"),
        )
