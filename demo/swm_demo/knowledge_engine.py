from __future__ import annotations

from dataclasses import dataclass, field, replace
import re
from typing import Protocol
import xml.etree.ElementTree as ET

from swm_demo.artifact_contract import SourceArtifact, SourceCollection
from swm_demo.extended_knowledge import ExtendedKnowledgeBuilder
from swm_demo.ids import content_hash, stable_id
from swm_demo.knowledge_contract import (
    CANDIDATE_ONLY_BUILD_PROFILE,
    KNOWLEDGE_SCHEMA_VERSION,
    Evidence,
    FactCandidate,
    FormalFact,
    FormalInference,
    InferenceCandidate,
    KnowledgeBuild,
    KnowledgeBuildTarget,
    KnowledgeEntity,
    KnowledgePackage,
)
from swm_demo.knowledge_requirement import KnowledgeSufficiencyAssessment
from swm_demo.knowledge_update import CandidateBundle


class FormalKnowledgeRepository(Protocol):
    def upsert_scope(self, scope_id: str, name: str) -> None: ...

    def start_snapshot(
        self,
        scope_id: str,
        revision: str,
        knowledge_schema_version: str = KNOWLEDGE_SCHEMA_VERSION,
    ) -> str: ...

    def publish_knowledge(
        self,
        snapshot_id: str,
        package: KnowledgePackage,
        base_snapshot_id: str | None = None,
    ) -> None: ...

    def fail_snapshot(self, snapshot_id: str, errors: tuple[str, ...]) -> None: ...

    def current_snapshot(self, scope_id: str) -> dict[str, object]: ...

    def current_entities(self, scope_id: str) -> list[dict[str, object]]: ...

    def current_facts(self, scope_id: str) -> list[dict[str, object]]: ...

    def current_inferences(self, scope_id: str) -> list[dict[str, object]]: ...

    def assert_current_context(
        self, scope_id: str, snapshot_token: str
    ) -> dict[str, object]: ...

    def formal_knowledge_catalog(
        self, scope_id: str, snapshot_token: str
    ) -> dict[str, list[dict[str, object]]]: ...

    def search_formal_entities(
        self,
        scope_id: str,
        snapshot_token: str,
        query: str,
        match_mode: str,
        entity_type: str | None,
        limit: int,
        cursor: int = 0,
    ) -> list[dict[str, object]]: ...

    def search_formal_inferences(
        self,
        scope_id: str,
        snapshot_token: str,
        query: str,
        match_mode: str,
        inference_type: str | None,
        limit: int,
        cursor: int = 0,
    ) -> list[dict[str, object]]: ...

    def formal_fact_neighborhood(
        self,
        scope_id: str,
        snapshot_token: str,
        entity_ids: tuple[str, ...],
        direction: str,
        predicates: tuple[str, ...],
        limit: int,
        cursor: int = 0,
    ) -> list[dict[str, object]]: ...

    def explain_formal_facts(
        self,
        scope_id: str,
        snapshot_token: str,
        fact_ids: tuple[str, ...],
    ) -> tuple[list[dict[str, object]], list[str]]: ...

    def explain_formal_inferences(
        self,
        scope_id: str,
        snapshot_token: str,
        inference_ids: tuple[str, ...],
    ) -> tuple[list[dict[str, object]], list[str]]: ...

    def explain_fact(self, scope_id: str, fact_id: str) -> dict[str, object]: ...

    def explain_inference(
        self, scope_id: str, inference_id: str
    ) -> dict[str, object]: ...

    def missing_formal_references(
        self,
        scope_id: str,
        snapshot_token: str,
        references: tuple[tuple[str, str], ...],
    ) -> tuple[tuple[str, str], ...]: ...

    def snapshot_counts(self, snapshot_id: str) -> dict[str, int]: ...


@dataclass
class _CandidateAccumulator:
    fact_id: str
    scope_id: str
    revision: str
    subject_id: str
    predicate: str
    object_id: str
    evidence_ids: list[str] = field(default_factory=list)

    def freeze(self) -> FactCandidate:
        return FactCandidate(
            fact_id=self.fact_id,
            scope_id=self.scope_id,
            revision=self.revision,
            subject_id=self.subject_id,
            predicate=self.predicate,
            object_id=self.object_id,
            evidence_ids=tuple(sorted(set(self.evidence_ids))),
        )


class StructureKnowledgeBuilder:
    """Builds only source-anchored Maven structure candidates.

    POM and README observations intentionally converge on the same Fact Candidate
    so the slice tests Evidence aggregation without creating duplicate Facts.
    """

    _README_MODULE = re.compile(r"[├└]──\s+([A-Za-z0-9_.-]+)\s+--")

    def build(
        self, collection: SourceCollection
    ) -> tuple[
        tuple[KnowledgeEntity, ...],
        tuple[Evidence, ...],
        tuple[FactCandidate, ...],
    ]:
        artifacts_by_path = {
            artifact.relative_path: artifact for artifact in collection.artifacts
        }
        root_pom = artifacts_by_path.get("pom.xml")
        if root_pom is None:
            raise ValueError("root pom.xml Artifact is required for Structure slice")

        root_xml = ET.fromstring(root_pom.content)
        project_name = _direct_text(root_xml, "artifactId")
        if not project_name:
            raise ValueError("root pom.xml does not declare artifactId")

        modules_element = _direct_child(root_xml, "modules")
        module_names = (
            [text for child in modules_element for text in [_text(child)] if text]
            if modules_element is not None
            else []
        )
        local_modules = set(module_names)

        entities: dict[str, KnowledgeEntity] = {}
        evidence: dict[str, Evidence] = {}
        candidates: dict[tuple[str, str, str], _CandidateAccumulator] = {}

        root_entity = self._entity(
            collection.scope_id, "maven-project", project_name
        )
        entities[root_entity.entity_id] = root_entity

        module_entities: dict[str, KnowledgeEntity] = {}
        for module_name in module_names:
            module_entity = self._entity(
                collection.scope_id, "maven-module", module_name
            )
            module_entities[module_name] = module_entity
            entities[module_entity.entity_id] = module_entity

            observation = self._evidence_for_line(
                root_pom, f"<module>{module_name}</module>"
            )
            evidence[observation.evidence_id] = observation
            self._add_candidate(
                candidates,
                collection,
                root_entity.entity_id,
                "CONTAINS_MODULE",
                module_entity.entity_id,
                observation.evidence_id,
            )

        readme = artifacts_by_path.get("README.md")
        if readme is not None:
            for line_number, line in enumerate(readme.content.splitlines(), start=1):
                match = self._README_MODULE.search(line)
                if not match:
                    continue
                module_name = match.group(1)
                module_entity = module_entities.get(module_name)
                if module_entity is None:
                    continue
                observation = self._evidence(
                    readme, line_number, line_number, line.strip()
                )
                evidence[observation.evidence_id] = observation
                self._add_candidate(
                    candidates,
                    collection,
                    root_entity.entity_id,
                    "CONTAINS_MODULE",
                    module_entity.entity_id,
                    observation.evidence_id,
                )

        for artifact in collection.artifacts:
            if artifact.artifact_type != "maven-pom" or artifact.relative_path == "pom.xml":
                continue
            module_name = artifact.relative_path.split("/", maxsplit=1)[0]
            source_entity = module_entities.get(module_name)
            if source_entity is None:
                continue

            project_xml = ET.fromstring(artifact.content)
            dependencies = _direct_child(project_xml, "dependencies")
            if dependencies is None:
                continue
            for dependency in _children(dependencies, "dependency"):
                dependency_name = _direct_text(dependency, "artifactId")
                if dependency_name not in local_modules:
                    continue
                target_entity = module_entities[dependency_name]
                observation = self._evidence_for_line(
                    artifact, f"<artifactId>{dependency_name}</artifactId>"
                )
                evidence[observation.evidence_id] = observation
                self._add_candidate(
                    candidates,
                    collection,
                    source_entity.entity_id,
                    "DEPENDS_ON",
                    target_entity.entity_id,
                    observation.evidence_id,
                )

        return (
            tuple(sorted(entities.values(), key=lambda item: item.entity_id)),
            tuple(sorted(evidence.values(), key=lambda item: item.evidence_id)),
            tuple(
                sorted(
                    (candidate.freeze() for candidate in candidates.values()),
                    key=lambda item: item.fact_id,
                )
            ),
        )

    @staticmethod
    def _entity(scope_id: str, entity_type: str, name: str) -> KnowledgeEntity:
        return KnowledgeEntity(
            entity_id=stable_id("entity", scope_id, entity_type, name),
            scope_id=scope_id,
            entity_type=entity_type,
            name=name,
        )

    @staticmethod
    def _evidence_for_line(artifact: SourceArtifact, needle: str) -> Evidence:
        matches = [
            (number, line.strip())
            for number, line in enumerate(artifact.content.splitlines(), start=1)
            if needle in line
        ]
        if len(matches) != 1:
            raise ValueError(
                f"expected one locator for {needle!r} in {artifact.relative_path}, "
                f"found {len(matches)}"
            )
        line_number, quote = matches[0]
        return StructureKnowledgeBuilder._evidence(
            artifact, line_number, line_number, quote
        )

    @staticmethod
    def _evidence(
        artifact: SourceArtifact,
        line_start: int,
        line_end: int,
        quote: str,
    ) -> Evidence:
        quote_digest = content_hash(quote)
        return Evidence(
            evidence_id=stable_id(
                "evidence",
                artifact.artifact_id,
                line_start,
                line_end,
                quote_digest,
            ),
            artifact_id=artifact.artifact_id,
            scope_id=artifact.scope_id,
            revision=artifact.revision,
            line_start=line_start,
            line_end=line_end,
            quote=quote,
            quote_hash=quote_digest,
        )

    @staticmethod
    def _add_candidate(
        candidates: dict[tuple[str, str, str], _CandidateAccumulator],
        collection: SourceCollection,
        subject_id: str,
        predicate: str,
        object_id: str,
        evidence_id: str,
    ) -> None:
        key = (subject_id, predicate, object_id)
        accumulator = candidates.get(key)
        if accumulator is None:
            accumulator = _CandidateAccumulator(
                fact_id=stable_id(
                    "fact",
                    collection.scope_id,
                    subject_id,
                    predicate,
                    object_id,
                ),
                scope_id=collection.scope_id,
                revision=collection.revision,
                subject_id=subject_id,
                predicate=predicate,
                object_id=object_id,
            )
            candidates[key] = accumulator
        accumulator.evidence_ids.append(evidence_id)


class KnowledgeVerifier:
    """Independent admission check for formal Structure knowledge."""

    def verify(
        self,
        collection: SourceCollection,
        entities: tuple[KnowledgeEntity, ...],
        evidence: tuple[Evidence, ...],
        candidates: tuple[FactCandidate, ...],
    ) -> tuple[str, ...]:
        errors: list[str] = []
        artifacts = {
            artifact.artifact_id: artifact for artifact in collection.artifacts
        }
        entity_ids = {entity.entity_id for entity in entities}
        evidence_by_id = {item.evidence_id: item for item in evidence}
        entities_by_id = {item.entity_id: item for item in entities}

        for artifact in collection.artifacts:
            if content_hash(artifact.content) != artifact.content_hash:
                errors.append(f"Artifact content hash mismatch: {artifact.artifact_id}")

        for item in evidence:
            artifact = artifacts.get(item.artifact_id)
            if artifact is None:
                errors.append(f"Evidence has missing Artifact: {item.evidence_id}")
                continue
            if item.scope_id != collection.scope_id or item.revision != artifact.revision:
                errors.append(f"Evidence context mismatch: {item.evidence_id}")
            lines = artifact.content.splitlines()
            if item.line_start < 1 or item.line_end > len(lines):
                errors.append(f"Evidence locator out of range: {item.evidence_id}")
                continue
            actual_quote = "\n".join(
                line.strip() for line in lines[item.line_start - 1 : item.line_end]
            )
            if actual_quote != item.quote:
                errors.append(f"Evidence quote mismatch: {item.evidence_id}")
            if content_hash(item.quote) != item.quote_hash:
                errors.append(f"Evidence quote hash mismatch: {item.evidence_id}")

        seen_fact_ids: set[str] = set()
        for candidate in candidates:
            if candidate.fact_id in seen_fact_ids:
                errors.append(f"duplicate Fact Candidate: {candidate.fact_id}")
            seen_fact_ids.add(candidate.fact_id)
            if not candidate.evidence_ids:
                errors.append(f"Fact Candidate has no Evidence: {candidate.fact_id}")
            if candidate.subject_id not in entity_ids:
                errors.append(f"Fact subject is missing: {candidate.fact_id}")
            if candidate.object_id not in entity_ids:
                errors.append(f"Fact object is missing: {candidate.fact_id}")
            if not candidate.proposition.strip():
                errors.append(f"Fact proposition is empty: {candidate.fact_id}")
            if candidate.model_call_id is not None and not candidate.model_call_id.strip():
                errors.append(f"Fact model call identity is empty: {candidate.fact_id}")
            if (
                candidate.predicate == "DEPENDS_ON"
                and candidate.subject_id == candidate.object_id
            ):
                errors.append(f"self dependency is not admitted: {candidate.fact_id}")
            subject = entities_by_id.get(candidate.subject_id)
            object_ = entities_by_id.get(candidate.object_id)
            canonical_proposition = (
                f"{subject.entity_type} {subject.name!r} "
                f"--{candidate.predicate}--> "
                f"{object_.entity_type} {object_.name!r}"
                if subject is not None and object_ is not None
                else ""
            )
            identity_parts = (
                (
                    candidate.scope_id,
                    candidate.subject_id,
                    candidate.predicate,
                    candidate.object_id,
                )
                if candidate.proposition == canonical_proposition
                else (
                    candidate.scope_id,
                    candidate.subject_id,
                    candidate.predicate,
                    candidate.object_id,
                    candidate.proposition,
                )
            )
            expected_fact_id = stable_id("fact", *identity_parts)
            if candidate.fact_id != expected_fact_id:
                errors.append(f"Fact identity is unstable: {candidate.fact_id}")
            for evidence_id in candidate.evidence_ids:
                linked = evidence_by_id.get(evidence_id)
                if linked is None:
                    errors.append(
                        f"Fact Candidate links missing Evidence: {candidate.fact_id}"
                    )
                elif linked.scope_id != candidate.scope_id:
                    errors.append(
                        f"Fact and Evidence context mismatch: {candidate.fact_id}"
                    )

        return tuple(errors)


class FactSemanticReviewer:
    """Conservative semantic admission for model-proposed direct Facts.

    Deterministic builders have their own tested semantics. A model-proposed
    direct Fact is admitted by this default reviewer only when its proposition
    is literally present in one of its cited Evidence observations. Semantic
    abstraction belongs in an Inference Candidate with an explicit support
    chain and independent reviewer.
    """

    def review(
        self,
        evidence: tuple[Evidence, ...],
        candidates: tuple[FactCandidate, ...],
    ) -> dict[str, tuple[str, ...]]:
        evidence_by_id = {item.evidence_id: item for item in evidence}
        decisions: dict[str, tuple[str, ...]] = {}
        for candidate in candidates:
            issues: list[str] = []
            if candidate.model_call_id is not None:
                observations = [
                    evidence_by_id[item]
                    for item in candidate.evidence_ids
                    if item in evidence_by_id
                ]
                if not any(
                    candidate.proposition in observation.quote
                    for observation in observations
                ):
                    issues.append(
                        "model-proposed Fact proposition is not directly present "
                        "in its Evidence; semantic abstraction requires Inference"
                    )
            decisions[candidate.fact_id] = tuple(issues)
        return decisions


class InferenceVerifier:
    """Independent admission checks for a bounded two-level inference graph."""

    def verify(
        self,
        facts: tuple[FactCandidate, ...],
        candidates: tuple[InferenceCandidate, ...],
        available_inference_ids: frozenset[str] = frozenset(),
    ) -> tuple[str, ...]:
        errors: list[str] = []
        fact_ids = {item.fact_id for item in facts}
        by_id = {item.inference_id: item for item in candidates}
        if len(by_id) != len(candidates):
            errors.append("duplicate Inference Candidate identity")
        for candidate in candidates:
            if not candidate.support_fact_ids:
                errors.append(
                    f"Inference Candidate has no direct Fact support: {candidate.inference_id}"
                )
            for fact_id in candidate.support_fact_ids:
                if fact_id not in fact_ids:
                    errors.append(
                        f"Inference references missing Fact: {candidate.inference_id}"
                    )
            for dependency_id in candidate.dependency_inference_ids:
                dependency = by_id.get(dependency_id)
                if dependency is None and dependency_id not in available_inference_ids:
                    errors.append(
                        f"Inference references missing Inference: {candidate.inference_id}"
                    )
                elif dependency is not None and dependency.dependency_inference_ids:
                    errors.append(
                        f"Inference dependency exceeds MVP depth: {candidate.inference_id}"
                    )
            expected_id = stable_id(
                "inference",
                candidate.scope_id,
                candidate.inference_type,
                candidate.statement,
                *tuple(sorted(set(candidate.support_fact_ids))),
                *tuple(sorted(set(candidate.dependency_inference_ids))),
            )
            if expected_id != candidate.inference_id:
                errors.append(
                    f"Inference identity is unstable: {candidate.inference_id}"
                )
            if self._reaches(candidate.inference_id, candidate.inference_id, by_id, set()):
                errors.append(f"Inference dependency cycle: {candidate.inference_id}")
        return tuple(errors)

    @classmethod
    def _reaches(
        cls,
        origin: str,
        current: str,
        by_id: dict[str, InferenceCandidate],
        visited: set[str],
    ) -> bool:
        candidate = by_id.get(current)
        if candidate is None:
            return False
        for dependency in candidate.dependency_inference_ids:
            if dependency == origin:
                return True
            if dependency in visited:
                continue
            visited.add(dependency)
            if cls._reaches(origin, dependency, by_id, visited):
                return True
        return False


class InferenceSemanticReviewer:
    """Independently checks that each current inference is supported in scope.

    These deterministic checks cover the four validation inference types. A
    production implementation can additionally use a model through Model
    Gateway, but it must preserve the same candidate-by-candidate decision
    contract.
    """

    def review(
        self,
        entities: tuple[KnowledgeEntity, ...],
        facts: tuple[FactCandidate, ...],
        candidates: tuple[InferenceCandidate, ...],
    ) -> dict[str, tuple[str, ...]]:
        entities_by_id = {item.entity_id: item for item in entities}
        facts_by_id = {item.fact_id: item for item in facts}
        decisions: dict[str, tuple[str, ...]] = {}
        for candidate in candidates:
            supporting = [
                facts_by_id[item]
                for item in candidate.support_fact_ids
                if item in facts_by_id
            ]
            issues: list[str] = []
            if candidate.inference_type == "BEHAVIOR_FLOW":
                owner_ids = {fact.subject_id for fact in supporting}
                if len(owner_ids) != 1:
                    issues.append(
                        "Behavior support Facts have different method owners"
                    )
                steps = [
                    entities_by_id[fact.object_id].name.split(":", maxsplit=1)[-1]
                    for fact in supporting
                    if fact.predicate == "DECLARES_STEP"
                ]
                if not steps or not all(
                    step in candidate.statement for step in steps
                ):
                    issues.append("Behavior statement omits a supported step")
                if not any(
                    fact.predicate in {"CALLS", "CALLS_OPERATION"}
                    for fact in supporting
                ):
                    issues.append("Behavior statement has no implementation call support")
            elif candidate.inference_type == "BUSINESS_CONSTRAINT":
                guards = [
                    entities_by_id[fact.object_id].name.split(": IF ", maxsplit=1)[-1]
                    for fact in supporting
                    if fact.predicate == "HAS_FAILURE_GUARD"
                ]
                if len(guards) != 1 or guards[0] not in candidate.statement:
                    issues.append("Business constraint exceeds its failure-guard support")
            elif candidate.inference_type == "BUSINESS_CAPABILITY":
                capabilities = [
                    (entities_by_id[fact.subject_id].name, entities_by_id[fact.object_id].name)
                    for fact in supporting
                    if fact.predicate == "HAS_DECLARED_CAPABILITY"
                ]
                if len(capabilities) != 1 or not all(
                    value in candidate.statement for value in capabilities[0]
                ):
                    issues.append("Business capability exceeds its source declaration")
            elif candidate.inference_type == "HISTORY_IMPACT":
                required_values = [
                    entities_by_id[fact.object_id].name
                    for fact in supporting
                    if fact.predicate in {"AUTHORED_AT", "DECLARES_CHANGE"}
                ]
                if len(required_values) < 2 or not all(
                    value in candidate.statement for value in required_values
                ):
                    issues.append("History statement omits commit time or declaration")
                ordering = [
                    entities_by_id[fact.object_id].name
                    for fact in supporting
                    if fact.predicate == "CHANGED_ORDER"
                ]
                if 0 < len(ordering) <= 3 and not all(
                    value in candidate.statement for value in ordering
                ):
                    issues.append("History statement omits a bounded ordering change")
            else:
                issues.append(
                    f"no semantic reviewer registered for {candidate.inference_type}"
                )
            decisions[candidate.inference_id] = tuple(issues)
        return decisions


class KnowledgeEngine:
    _KNOWLEDGE_SCHEMA_VERSION = KNOWLEDGE_SCHEMA_VERSION
    _MAX_SEARCH_LIMIT = 100
    _MAX_NEIGHBORHOOD_LIMIT = 200
    _MAX_NEIGHBORHOOD_SEEDS = 20
    _MAX_PREDICATE_FILTERS = 20
    _MAX_EXPLAIN_BATCH = 50
    _COVERAGE = {
        "status": "UNDECLARED",
        "meaning": (
            "No completeness claim is published for this Snapshot; an empty "
            "result means only that no matching formal knowledge was found."
        ),
    }
    _PREDICATE_MEANINGS = {
        "CONTAINS_MODULE": "The subject project declares the object Maven module.",
        "DEPENDS_ON": "The subject Maven module declares a dependency on the object local module.",
        "CONTAINS_TYPE": "The subject module contains the object declared technical type.",
        "DECLARES_METHOD": "The subject technical type declares the object method.",
        "IMPLEMENTS_TYPE": "The subject technical type implements the object interface type.",
        "IMPLEMENTS_METHOD": "The subject method implements the object interface method.",
        "CALLS": "The subject method contains a call resolved to the object method.",
        "CALLS_OPERATION": "The subject method contains the object named operation call.",
        "EXPOSES_ENDPOINT": "The subject method exposes the object HTTP endpoint.",
        "DECLARES_STEP": "The subject method documentation declares the object behavior step.",
        "PRECEDES": "The subject declared step precedes the object declared step.",
        "HAS_FAILURE_GUARD": "The subject method contains the object source-anchored failure guard.",
        "HAS_DECLARED_CAPABILITY": "The subject module has the object source-declared capability.",
        "AUTHORED_AT": "The subject commit records the object authored timestamp.",
        "DECLARES_CHANGE": "The subject commit message declares the object change.",
        "CHANGED_FILE": "The subject commit changes the object file.",
        "HAS_LINE_REPLACEMENT": "The subject commit contains the object line replacement.",
        "HAS_DIFF_HUNK": "The subject commit contains the object diff hunk.",
        "CHANGED_ORDER": "The subject commit changes execution ordering as described by the object.",
    }

    def __init__(
        self,
        builder: StructureKnowledgeBuilder | None = None,
        verifier: KnowledgeVerifier | None = None,
        extended_builder: ExtendedKnowledgeBuilder | None = None,
        inference_verifier: InferenceVerifier | None = None,
        fact_semantic_reviewer: FactSemanticReviewer | None = None,
        inference_semantic_reviewer: InferenceSemanticReviewer | None = None,
        repository: FormalKnowledgeRepository | None = None,
    ):
        self.builder = builder or StructureKnowledgeBuilder()
        self.verifier = verifier or KnowledgeVerifier()
        self.extended_builder = extended_builder or ExtendedKnowledgeBuilder()
        self.inference_verifier = inference_verifier or InferenceVerifier()
        self.fact_semantic_reviewer = fact_semantic_reviewer or FactSemanticReviewer()
        self.inference_semantic_reviewer = (
            inference_semantic_reviewer or InferenceSemanticReviewer()
        )
        self.repository = repository

    def bind_repository(self, repository: FormalKnowledgeRepository) -> None:
        self.repository = repository

    def configure_scope(self, scope_id: str, name: str) -> None:
        self._repository().upsert_scope(scope_id, name)

    def begin_update(self, scope_id: str, revision: str) -> str:
        return self._repository().start_snapshot(
            scope_id, revision, self._KNOWLEDGE_SCHEMA_VERSION
        )

    def admit_and_publish(
        self,
        snapshot_id: str,
        collection: SourceCollection,
        target: KnowledgeBuildTarget | None = None,
        candidate_bundle: CandidateBundle | None = None,
        base_snapshot_id: str | None = None,
    ) -> KnowledgeBuild:
        base_entities: tuple[KnowledgeEntity, ...] = ()
        base_facts: tuple[FactCandidate, ...] = ()
        base_inference_ids: frozenset[str] = frozenset()
        if (
            base_snapshot_id is not None
            and collection.build_profile == CANDIDATE_ONLY_BUILD_PROFILE
        ):
            base_entities, base_facts, base_inference_ids = self._base_premises(
                collection.scope_id, base_snapshot_id
            )
        build = self.construct(
            collection,
            target,
            candidate_bundle,
            base_entities=base_entities,
            base_facts=base_facts,
            base_inference_ids=base_inference_ids,
        )
        if build.errors or build.package is None:
            errors = build.errors or ("Knowledge Engine returned no package",)
            self._repository().fail_snapshot(snapshot_id, errors)
            return KnowledgeBuild(package=None, errors=errors)
        try:
            self._repository().publish_knowledge(
                snapshot_id,
                build.package,
                base_snapshot_id=base_snapshot_id,
            )
        except Exception as error:
            self._repository().fail_snapshot(snapshot_id, (str(error),))
            raise
        return build

    def fail_update(self, snapshot_id: str, error: Exception) -> None:
        self._repository().fail_snapshot(snapshot_id, (str(error),))

    def current_snapshot(self, scope_id: str) -> dict[str, object]:
        return self._repository().current_snapshot(scope_id)

    def read_entities(self, scope_id: str) -> list[dict[str, object]]:
        return self._repository().current_entities(scope_id)

    def read_facts(self, scope_id: str) -> list[dict[str, object]]:
        return self._repository().current_facts(scope_id)

    def read_inferences(self, scope_id: str) -> list[dict[str, object]]:
        return self._repository().current_inferences(scope_id)

    def open_knowledge_context(self, scope_id: str) -> dict[str, object]:
        """Open a fixed formal-knowledge read context.

        `snapshot_token` is a consistency token only.  It deliberately equals
        the Snapshot ID in this demo and must never be treated as a security
        credential.
        """

        snapshot = self._repository().current_snapshot(scope_id)
        self._assert_supported_snapshot_schema(snapshot)
        snapshot_token = str(snapshot["snapshot_id"])
        catalog = self._repository().formal_knowledge_catalog(
            scope_id, snapshot_token
        )
        # Publication may supersede the Snapshot while its catalog is read.
        # Re-resolve immediately before exposing the context so callers never
        # start an investigation with a token already known to be stale.
        snapshot = self._repository().assert_current_context(
            scope_id, snapshot_token
        )
        return {
            "tool": "FormalKnowledge.OpenContext",
            **self._context_envelope(snapshot, snapshot_token),
            "schema": {
                "Entity": "Stable technical identity: entity_id, entity_type, name.",
                "Fact": (
                    "Evidence-backed formal proposition with a directed relation "
                    "projection: proposition, subject_id, predicate, object_id. "
                    "Read with Neighborhood and trace source location with Explain."
                ),
                "Inference": (
                    "Admitted conclusion: inference_type, statement, supporting "
                    "Fact IDs and optional Inference dependencies."
                ),
                "Evidence": (
                    "Source-anchored support metadata exposed through Fact Explain; "
                    "Evidence quote and Artifact payload are not part of the answer "
                    "read surface."
                ),
            },
            "query_contract": {
                "search_kinds": ["ENTITY", "INFERENCE"],
                "match_modes": ["EXACT", "CONTAINS"],
                "match_semantics": "case-sensitive text matching",
                "pagination": {
                    "cursor_type": "non-negative integer offset",
                    "continuation_field": "next_cursor",
                    "snapshot_bound": True,
                },
                "neighborhood_depth": 1,
                "neighborhood_directions": ["OUTGOING", "INCOMING", "BOTH"],
                "batch_explain_kinds": ["FACT", "INFERENCE"],
                "limits": {
                    "search_max": self._MAX_SEARCH_LIMIT,
                    "neighborhood_max": self._MAX_NEIGHBORHOOD_LIMIT,
                    "neighborhood_seed_max": self._MAX_NEIGHBORHOOD_SEEDS,
                    "explain_batch_max": self._MAX_EXPLAIN_BATCH,
                },
            },
            "catalog": self._semantic_catalog(catalog),
        }

    def search_formal_knowledge(
        self,
        scope_id: str,
        snapshot_token: str,
        kind: str,
        query: str,
        match_mode: str = "CONTAINS",
        type_name: str | None = None,
        limit: int = 20,
        cursor: int = 0,
    ) -> dict[str, object]:
        normalized_kind = kind.upper()
        normalized_mode = match_mode.upper()
        if normalized_kind not in {"ENTITY", "INFERENCE"}:
            raise ValueError("kind must be ENTITY or INFERENCE")
        if normalized_mode not in {"EXACT", "CONTAINS"}:
            raise ValueError("match_mode must be EXACT or CONTAINS")
        if not query:
            raise ValueError("query must not be empty")
        self._validate_limit("search", limit, self._MAX_SEARCH_LIMIT)
        self._validate_cursor(cursor)
        if normalized_kind == "ENTITY":
            fetched_items = self._repository().search_formal_entities(
                scope_id,
                snapshot_token,
                query,
                normalized_mode,
                type_name,
                limit,
                cursor,
            )
        else:
            fetched_items = self._repository().search_formal_inferences(
                scope_id,
                snapshot_token,
                query,
                normalized_mode,
                type_name,
                limit,
                cursor,
            )
        has_more = len(fetched_items) > limit
        items = fetched_items[:limit]
        snapshot = self._repository().assert_current_context(
            scope_id, snapshot_token
        )
        return {
            "tool": "FormalKnowledge.Search",
            **self._context_envelope(snapshot, snapshot_token),
            "kind": normalized_kind,
            "query": query,
            "match_mode": normalized_mode,
            "type_filter": type_name,
            "limit": limit,
            "cursor": cursor,
            "has_more": has_more,
            "next_cursor": cursor + len(items) if has_more else None,
            # Retained with its original "page is full" meaning for callers
            # that predate cursor pagination. Use has_more for continuation.
            "limit_reached": len(items) == limit,
            "items": items,
        }

    def read_formal_neighborhood(
        self,
        scope_id: str,
        snapshot_token: str,
        entity_ids: tuple[str, ...],
        direction: str = "BOTH",
        predicates: tuple[str, ...] = (),
        limit: int = 100,
        cursor: int = 0,
    ) -> dict[str, object]:
        normalized_direction = direction.upper()
        if normalized_direction not in {"OUTGOING", "INCOMING", "BOTH"}:
            raise ValueError("direction must be OUTGOING, INCOMING, or BOTH")
        seeds = tuple(sorted(set(entity_ids)))
        predicate_filter = tuple(sorted(set(predicates)))
        if not seeds:
            raise ValueError("at least one entity_id is required")
        if len(seeds) > self._MAX_NEIGHBORHOOD_SEEDS:
            raise ValueError(
                "entity_ids exceeds neighborhood seed limit "
                f"{self._MAX_NEIGHBORHOOD_SEEDS}"
            )
        if len(predicate_filter) > self._MAX_PREDICATE_FILTERS:
            raise ValueError(
                "predicates exceeds filter limit "
                f"{self._MAX_PREDICATE_FILTERS}"
            )
        self._validate_limit(
            "neighborhood", limit, self._MAX_NEIGHBORHOOD_LIMIT
        )
        self._validate_cursor(cursor)
        fetched_facts = self._repository().formal_fact_neighborhood(
            scope_id,
            snapshot_token,
            seeds,
            normalized_direction,
            predicate_filter,
            limit,
            cursor,
        )
        has_more = len(fetched_facts) > limit
        facts = fetched_facts[:limit]
        snapshot = self._repository().assert_current_context(
            scope_id, snapshot_token
        )
        observed_predicates = sorted(
            {str(item["predicate"]) for item in facts}
        )
        return {
            "tool": "FormalKnowledge.Neighborhood",
            **self._context_envelope(snapshot, snapshot_token),
            "depth": 1,
            "seed_entity_ids": list(seeds),
            "direction": normalized_direction,
            "predicate_filter": list(predicate_filter),
            "predicate_semantics": [
                self._predicate_semantics(predicate)
                for predicate in observed_predicates
            ],
            "limit": limit,
            "cursor": cursor,
            "has_more": has_more,
            "next_cursor": cursor + len(facts) if has_more else None,
            # Retained with its original "page is full" meaning for callers
            # that predate cursor pagination. Use has_more for continuation.
            "limit_reached": len(facts) == limit,
            "facts": facts,
        }

    def explain_formal_knowledge_batch(
        self,
        scope_id: str,
        snapshot_token: str,
        kind: str,
        knowledge_ids: tuple[str, ...],
    ) -> dict[str, object]:
        normalized_kind = kind.upper()
        if normalized_kind not in {"FACT", "INFERENCE"}:
            raise ValueError("kind must be FACT or INFERENCE")
        identifiers = tuple(sorted(set(knowledge_ids)))
        if not identifiers:
            raise ValueError("at least one knowledge ID is required")
        if len(identifiers) > self._MAX_EXPLAIN_BATCH:
            raise ValueError(
                f"knowledge_ids exceeds batch limit {self._MAX_EXPLAIN_BATCH}"
            )
        if normalized_kind == "FACT":
            items, missing = self._repository().explain_formal_facts(
                scope_id, snapshot_token, identifiers
            )
        else:
            items, missing = self._repository().explain_formal_inferences(
                scope_id, snapshot_token, identifiers
            )
        snapshot = self._repository().assert_current_context(
            scope_id, snapshot_token
        )
        return {
            "tool": "FormalKnowledge.ExplainBatch",
            **self._context_envelope(snapshot, snapshot_token),
            "kind": normalized_kind,
            "requested_ids": list(identifiers),
            "missing_ids": missing,
            "items": items,
        }

    def explain_fact(self, scope_id: str, fact_id: str) -> dict[str, object]:
        return self._repository().explain_fact(scope_id, fact_id)

    def explain_inference(
        self, scope_id: str, inference_id: str
    ) -> dict[str, object]:
        return self._repository().explain_inference(scope_id, inference_id)

    def snapshot_counts(self, snapshot_id: str) -> dict[str, int]:
        return self._repository().snapshot_counts(snapshot_id)

    def validate_sufficiency_assessment(
        self, assessment: KnowledgeSufficiencyAssessment
    ) -> dict[str, object]:
        """Mechanically validate a model-produced sufficiency decision.

        This checks identity, Snapshot and KnowledgeContext binding. Whether a
        proposition semantically satisfies a Need remains an independent model
        review concern; a syntactically valid ID alone never proves sufficiency.
        """

        snapshot = self._repository().assert_current_context(
            assessment.requirement.scope_id, assessment.snapshot_id
        )
        errors: list[str] = []
        if snapshot["scope_id"] != assessment.requirement.scope_id:
            errors.append("assessment Scope differs from its Snapshot")
        if snapshot["revision"] != assessment.knowledge_context_reference:
            errors.append("assessment KnowledgeContext differs from its Snapshot")
        references = tuple(
            (reference.kind, reference.reference_id)
            for item in assessment.items
            for reference in item.formal_knowledge_references
        )
        missing = self._repository().missing_formal_references(
            assessment.requirement.scope_id,
            assessment.snapshot_id,
            references,
        )
        errors.extend(
            f"formal reference is absent from the bound Snapshot: {kind}:{item_id}"
            for kind, item_id in missing
        )
        return {
            "assessment_id": assessment.assessment_id,
            "requirement_id": assessment.requirement_id,
            "scope_id": assessment.requirement.scope_id,
            "snapshot_id": assessment.snapshot_id,
            "knowledge_context_reference": assessment.knowledge_context_reference,
            "complete": assessment.complete,
            "mechanically_valid": not errors,
            "errors": errors,
        }

    @classmethod
    def _context_envelope(
        cls, snapshot: dict[str, object], snapshot_token: str
    ) -> dict[str, object]:
        cls._assert_supported_snapshot_schema(snapshot)
        return {
            "scope_id": snapshot["scope_id"],
            "snapshot_id": snapshot["snapshot_id"],
            "snapshot_token": snapshot_token,
            "revision": snapshot["revision"],
            "knowledge_schema_version": snapshot["knowledge_schema_version"],
            "coverage": dict(cls._COVERAGE),
        }

    @classmethod
    def _assert_supported_snapshot_schema(
        cls, snapshot: dict[str, object]
    ) -> None:
        actual = snapshot.get("knowledge_schema_version")
        if actual != cls._KNOWLEDGE_SCHEMA_VERSION:
            raise ValueError(
                "INCOMPATIBLE_KNOWLEDGE_SCHEMA: Snapshot "
                f"{snapshot.get('snapshot_id')} uses {actual!r}; reader requires "
                f"{cls._KNOWLEDGE_SCHEMA_VERSION!r}. Rebuild or explicitly "
                "revalidate the Snapshot before Knowledge Use."
            )

    @classmethod
    def _semantic_catalog(
        cls, catalog: dict[str, list[dict[str, object]]]
    ) -> dict[str, list[dict[str, object]]]:
        return {
            "entity_types": catalog["entity_types"],
            "predicates": [
                {
                    **item,
                    **cls._predicate_semantics(str(item["predicate"])),
                }
                for item in catalog["predicates"]
            ],
            "inference_types": catalog["inference_types"],
        }

    @classmethod
    def _predicate_semantics(cls, predicate: str) -> dict[str, str]:
        meaning = cls._PREDICATE_MEANINGS.get(predicate)
        return {
            "predicate": predicate,
            "semantic_status": "DECLARED" if meaning else "UNDECLARED",
            "meaning": meaning or "Predicate semantics are not declared by this reader.",
        }

    @staticmethod
    def _validate_limit(name: str, value: int, maximum: int) -> None:
        if value < 1 or value > maximum:
            raise ValueError(f"{name} limit must be between 1 and {maximum}")

    @staticmethod
    def _validate_cursor(value: int) -> None:
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError("cursor must be a non-negative integer")

    def construct(
        self,
        collection: SourceCollection,
        target: KnowledgeBuildTarget | None = None,
        candidate_bundle: CandidateBundle | None = None,
        *,
        base_entities: tuple[KnowledgeEntity, ...] = (),
        base_facts: tuple[FactCandidate, ...] = (),
        base_inference_ids: frozenset[str] = frozenset(),
    ) -> KnowledgeBuild:
        build_target = target or KnowledgeBuildTarget()
        candidate_only = collection.build_profile == CANDIDATE_ONLY_BUILD_PROFILE
        try:
            if candidate_only:
                if candidate_bundle is None:
                    raise ValueError(
                        "candidate-only build requires one Candidate Bundle"
                    )
                entities: tuple[KnowledgeEntity, ...] = ()
                evidence: tuple[Evidence, ...] = ()
                candidates: tuple[FactCandidate, ...] = ()
            else:
                entities, evidence, candidates = self.builder.build(collection)
                if collection.build_profile != "structure-core":
                    extra_entities, extra_evidence, extra_candidates = (
                        self.extended_builder.build(collection, entities)
                    )
                    entities = self._merge_entities(entities, extra_entities)
                    evidence = self._merge_evidence(evidence, extra_evidence)
                    candidates = self._merge_candidates(candidates, extra_candidates)
            if candidate_bundle is not None:
                artifact_ids = {item.artifact_id for item in collection.artifacts}
                unknown_artifacts = sorted(
                    set(candidate_bundle.source_artifact_ids) - artifact_ids
                )
                if unknown_artifacts:
                    raise ValueError(
                        "Candidate Bundle references Artifacts outside the "
                        f"Investigation collection: {unknown_artifacts}"
                    )
                if (
                    candidate_bundle.intent_id == ""
                    or candidate_bundle.scope_id != collection.scope_id
                ):
                    raise ValueError("Candidate Bundle and collection Scope differ")
                entities = self._merge_entities(
                    entities, candidate_bundle.entities
                )
                evidence = self._merge_evidence(
                    evidence, candidate_bundle.evidence
                )
                candidates = self._merge_candidates(
                    candidates, candidate_bundle.fact_candidates
                )
            candidates = self._normalize_fact_propositions(entities, candidates)
            if candidate_only:
                base_fact_ids = {item.fact_id for item in base_facts}
                base_candidate_inference_ids = set(base_inference_ids)
                missing_target_facts = sorted(
                    set(build_target.premise_fact_ids) - base_fact_ids
                )
                missing_target_inferences = sorted(
                    set(build_target.premise_inference_ids)
                    - base_candidate_inference_ids
                )
                if missing_target_facts or missing_target_inferences:
                    raise ValueError(
                        "candidate-only Build Target premises are not published in "
                        "the exact Base Snapshot: facts="
                        f"{missing_target_facts}, inferences="
                        f"{missing_target_inferences}"
                    )
                candidate_fact_ids = {item.fact_id for item in candidates}
                for inference in candidate_bundle.inference_candidates:
                    if set(inference.support_fact_ids) & candidate_fact_ids:
                        raise ValueError(
                            "candidate-only Inference cannot use a Fact Candidate "
                            "from the same Bundle as a premise"
                        )
                    if not set(inference.support_fact_ids).issubset(
                        set(build_target.premise_fact_ids)
                    ) or not set(inference.dependency_inference_ids).issubset(
                        set(build_target.premise_inference_ids)
                    ):
                        raise ValueError(
                            "candidate-only Inference references a premise outside "
                            "the frozen Build Target"
                        )
        except (ET.ParseError, ValueError) as error:
            return KnowledgeBuild(package=None, errors=(str(error),))

        errors = self.verifier.verify(
            collection, entities, evidence, candidates
        )
        if errors:
            return KnowledgeBuild(package=None, errors=errors)

        fact_semantic_decisions = self.fact_semantic_reviewer.review(
            evidence, candidates
        )
        fact_semantic_errors = tuple(
            f"{fact_id}: {'; '.join(issues)}"
            for fact_id, issues in fact_semantic_decisions.items()
            if issues
        )
        if fact_semantic_errors:
            return KnowledgeBuild(package=None, errors=fact_semantic_errors)

        inference_candidates: tuple[InferenceCandidate, ...] = ()
        diagnostics: tuple[str, ...] = ()
        if collection.build_profile != "structure-core":
            if candidate_only:
                assert candidate_bundle is not None
                inference_candidates = candidate_bundle.inference_candidates
                validation_entities = self._merge_entities(base_entities, entities)
                validation_facts = base_facts
                available_inference_ids = base_inference_ids
            else:
                inference_candidates = self.extended_builder.build_inferences(
                    collection, entities, candidates, build_target
                )
                if candidate_bundle is not None:
                    inference_candidates = self._merge_inference_candidates(
                        inference_candidates,
                        candidate_bundle.inference_candidates,
                    )
                validation_entities = entities
                validation_facts = candidates
                available_inference_ids = frozenset()
            inference_errors = self.inference_verifier.verify(
                validation_facts,
                inference_candidates,
                available_inference_ids,
            )
            if inference_errors:
                return KnowledgeBuild(package=None, errors=inference_errors)
            semantic_decisions = self.inference_semantic_reviewer.review(
                validation_entities, validation_facts, inference_candidates
            )
            admitted = tuple(
                item
                for item in inference_candidates
                if not semantic_decisions.get(item.inference_id, ())
            )
            rejected = {
                inference_id: issues
                for inference_id, issues in semantic_decisions.items()
                if issues
            }
            required_types = set(build_target.required_inference_types)
            admitted_types = {item.inference_type for item in admitted}
            missing_required = sorted(required_types - admitted_types)
            if missing_required:
                details = tuple(
                    f"{inference_id}: {'; '.join(issues)}"
                    for inference_id, issues in rejected.items()
                )
                return KnowledgeBuild(
                    package=None,
                    errors=(
                        "required inference types were not admitted: "
                        + ", ".join(missing_required),
                        *details,
                    ),
                )
            inference_candidates = admitted
            if candidate_only:
                target_errors = self._candidate_only_target_errors(
                    build_target,
                    validation_entities,
                    candidates,
                    validation_facts,
                    inference_candidates,
                )
                if target_errors:
                    return KnowledgeBuild(package=None, errors=target_errors)
            diagnostics = tuple(
                f"excluded optional Inference Candidate {inference_id}: "
                + "; ".join(issues)
                for inference_id, issues in rejected.items()
            )

        facts = tuple(
            FormalFact(
                fact_id=candidate.fact_id,
                scope_id=candidate.scope_id,
                revision=candidate.revision,
                subject_id=candidate.subject_id,
                predicate=candidate.predicate,
                object_id=candidate.object_id,
                evidence_ids=candidate.evidence_ids,
                proposition=candidate.proposition,
                model_call_id=candidate.model_call_id,
            )
            for candidate in candidates
        )
        inferences = tuple(
            FormalInference(
                inference_id=candidate.inference_id,
                scope_id=candidate.scope_id,
                revision=candidate.revision,
                inference_type=candidate.inference_type,
                statement=candidate.statement,
                support_fact_ids=candidate.support_fact_ids,
                dependency_inference_ids=candidate.dependency_inference_ids,
                model_call_id=candidate.model_call_id,
            )
            for candidate in inference_candidates
        )
        return KnowledgeBuild(
            package=KnowledgePackage(
                scope_id=collection.scope_id,
                revision=collection.revision,
                entities=entities,
                evidence=evidence,
                facts=facts,
                inferences=inferences,
            ),
            errors=(),
            diagnostics=diagnostics,
        )

    def _base_premises(
        self, scope_id: str, base_snapshot_id: str
    ) -> tuple[
        tuple[KnowledgeEntity, ...],
        tuple[FactCandidate, ...],
        frozenset[str],
    ]:
        repository = self._repository()
        current = repository.current_snapshot(scope_id)
        if current["snapshot_id"] != base_snapshot_id:
            raise ValueError(
                "candidate-only formal premises require the exact CURRENT Base Snapshot"
            )
        entities = tuple(
            KnowledgeEntity(
                entity_id=str(item["entity_id"]),
                scope_id=str(item["scope_id"]),
                entity_type=str(item["entity_type"]),
                name=str(item["name"]),
            )
            for item in repository.current_entities(scope_id)
        )
        facts = tuple(
            FactCandidate(
                fact_id=str(item["fact_id"]),
                scope_id=str(item["scope_id"]),
                revision=str(item["revision"]),
                subject_id=str(item["subject_id"]),
                predicate=str(item["predicate"]),
                object_id=str(item["object_id"]),
                evidence_ids=(),
                proposition=str(item["proposition"]),
                model_call_id=(
                    str(item["model_call_id"])
                    if item.get("model_call_id") is not None
                    else None
                ),
            )
            for item in repository.current_facts(scope_id)
        )
        inference_ids = frozenset(
            str(item["inference_id"])
            for item in repository.current_inferences(scope_id)
        )
        return entities, facts, inference_ids

    @staticmethod
    def _candidate_only_target_errors(
        target: KnowledgeBuildTarget,
        validation_entities: tuple[KnowledgeEntity, ...],
        delta_facts: tuple[FactCandidate, ...],
        premise_facts: tuple[FactCandidate, ...],
        inferences: tuple[InferenceCandidate, ...],
    ) -> tuple[str, ...]:
        """Bind candidate-only output to exact, application-selected targets."""

        target_specs = (
            *(
                (selector, "BEHAVIOR_FLOW")
                for selector, _ in target.behavior_methods
            ),
            *(
                (selector, "BUSINESS_CONSTRAINT")
                for selector, _ in target.business_constraint_methods
            ),
            *((module, "BUSINESS_CAPABILITY") for module in target.capability_modules),
            *((commit, "HISTORY_IMPACT") for commit in target.history_commits),
        )
        if not target_specs:
            return (
                "candidate-only Build Target must contain at least one exact "
                "semantic target",
            )

        entities_by_id = {item.entity_id: item for item in validation_entities}
        all_facts = {item.fact_id: item for item in (*premise_facts, *delta_facts)}
        delta_fact_ids = {item.fact_id for item in delta_facts}
        required_types = set(target.required_inference_types)
        errors: list[str] = []
        exact_selectors = {selector for selector, _ in target_specs}
        unauthorized_delta_fact_ids = tuple(
            sorted(
                fact.fact_id
                for fact in delta_facts
                if (
                    (subject := entities_by_id.get(fact.subject_id)) is None
                    or subject.name not in exact_selectors
                )
            )
        )
        if unauthorized_delta_fact_ids:
            errors.append(
                "candidate-only direct Facts fall outside the exact Build Target: "
                + ", ".join(unauthorized_delta_fact_ids)
            )

        def all_support_facts_match(
            inference: InferenceCandidate, selector: str
        ) -> bool:
            supporting = tuple(
                all_facts.get(fact_id)
                for fact_id in inference.support_fact_ids
            )
            if not supporting or any(fact is None for fact in supporting):
                return False
            return all(
                (
                    subject := entities_by_id.get(fact.subject_id)
                ) is not None
                and subject.name == selector
                for fact in supporting
                if fact is not None
            )

        for selector, inference_type in target_specs:
            aligned_fact_ids = {
                fact.fact_id
                for fact in all_facts.values()
                if (
                    (subject := entities_by_id.get(fact.subject_id)) is not None
                    and subject.name == selector
                )
            }
            if inference_type in required_types:
                if inference_type == "BEHAVIOR_FLOW":
                    aligned = any(
                        item.inference_type == inference_type
                        and all_support_facts_match(item, selector)
                        for item in inferences
                    )
                else:
                    aligned = any(
                        item.inference_type == inference_type
                        and bool(set(item.support_fact_ids) & aligned_fact_ids)
                        for item in inferences
                    )
                if not aligned:
                    errors.append(
                        "candidate-only Inference is not aligned to exact target "
                        f"{selector!r} for {inference_type}"
                    )
            elif not (aligned_fact_ids & delta_fact_ids):
                errors.append(
                    "candidate-only direct Facts are not aligned to exact target "
                    f"{selector!r}"
                )
        return tuple(errors)

    @staticmethod
    def _merge_entities(
        first: tuple[KnowledgeEntity, ...], second: tuple[KnowledgeEntity, ...]
    ) -> tuple[KnowledgeEntity, ...]:
        merged = {item.entity_id: item for item in first}
        for item in second:
            previous = merged.get(item.entity_id)
            if previous is not None and previous != item:
                raise ValueError(f"conflicting Entity identity: {item.entity_id}")
            merged[item.entity_id] = item
        return tuple(sorted(merged.values(), key=lambda item: item.entity_id))

    @staticmethod
    def _merge_evidence(
        first: tuple[Evidence, ...], second: tuple[Evidence, ...]
    ) -> tuple[Evidence, ...]:
        merged = {item.evidence_id: item for item in first}
        for item in second:
            previous = merged.get(item.evidence_id)
            if previous is not None and previous != item:
                raise ValueError(f"conflicting Evidence identity: {item.evidence_id}")
            merged[item.evidence_id] = item
        return tuple(sorted(merged.values(), key=lambda item: item.evidence_id))

    @staticmethod
    def _merge_candidates(
        first: tuple[FactCandidate, ...], second: tuple[FactCandidate, ...]
    ) -> tuple[FactCandidate, ...]:
        merged: dict[tuple[str, str, str], FactCandidate] = {}
        for item in (*first, *second):
            key = (item.subject_id, item.predicate, item.object_id)
            previous = merged.get(key)
            if previous is None:
                merged[key] = item
                continue
            if previous.fact_id != item.fact_id:
                raise ValueError(f"conflicting Fact identity: {item.fact_id}")
            merged[key] = FactCandidate(
                fact_id=item.fact_id,
                scope_id=item.scope_id,
                revision=item.revision,
                subject_id=item.subject_id,
                predicate=item.predicate,
                object_id=item.object_id,
                evidence_ids=tuple(
                    sorted(set((*previous.evidence_ids, *item.evidence_ids)))
                ),
                proposition=item.proposition or previous.proposition,
                model_call_id=item.model_call_id or previous.model_call_id,
            )
        return tuple(sorted(merged.values(), key=lambda item: item.fact_id))

    @staticmethod
    def _merge_inference_candidates(
        first: tuple[InferenceCandidate, ...],
        second: tuple[InferenceCandidate, ...],
    ) -> tuple[InferenceCandidate, ...]:
        merged = {item.inference_id: item for item in first}
        for item in second:
            previous = merged.get(item.inference_id)
            if previous is not None and previous != item:
                raise ValueError(
                    f"conflicting Inference identity: {item.inference_id}"
                )
            merged[item.inference_id] = item
        return tuple(sorted(merged.values(), key=lambda item: item.inference_id))

    @staticmethod
    def _normalize_fact_propositions(
        entities: tuple[KnowledgeEntity, ...],
        candidates: tuple[FactCandidate, ...],
    ) -> tuple[FactCandidate, ...]:
        """Make each admitted Fact's semantic boundary explicit.

        Existing deterministic relation builders use a canonical proposition
        that states exactly the projected triple. Model-led builders may supply
        a richer proposition, but the verifier still checks that proposition
        against the cited Evidence instead of treating the Evidence quote as
        implicit extra knowledge.
        """

        entities_by_id = {item.entity_id: item for item in entities}
        normalized: list[FactCandidate] = []
        for candidate in candidates:
            if candidate.proposition.strip():
                normalized.append(candidate)
                continue
            subject = entities_by_id.get(candidate.subject_id)
            object_ = entities_by_id.get(candidate.object_id)
            if subject is None or object_ is None:
                normalized.append(candidate)
                continue
            proposition = (
                f"{subject.entity_type} {subject.name!r} "
                f"--{candidate.predicate}--> "
                f"{object_.entity_type} {object_.name!r}"
            )
            normalized.append(replace(candidate, proposition=proposition))
        return tuple(normalized)

    def _repository(self) -> FormalKnowledgeRepository:
        if self.repository is None:
            raise RuntimeError("Knowledge Engine repository is not bound")
        return self.repository


def _local_name(tag: str) -> str:
    return tag.rsplit("}", maxsplit=1)[-1]


def _text(element: ET.Element) -> str | None:
    value = element.text.strip() if element.text else ""
    return value or None


def _direct_child(element: ET.Element, name: str) -> ET.Element | None:
    return next(
        (child for child in element if _local_name(child.tag) == name), None
    )


def _children(element: ET.Element, name: str) -> list[ET.Element]:
    return [child for child in element if _local_name(child.tag) == name]


def _direct_text(element: ET.Element, name: str) -> str | None:
    child = _direct_child(element, name)
    return _text(child) if child is not None else None
