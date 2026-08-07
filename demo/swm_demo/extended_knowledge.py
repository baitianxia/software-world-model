from __future__ import annotations

from dataclasses import dataclass, field
from collections import Counter
import json
import re
from typing import Iterable

from swm_demo.artifact_contract import SourceArtifact, SourceCollection
from swm_demo.ids import content_hash, stable_id
from swm_demo.knowledge_contract import (
    Evidence,
    FactCandidate,
    InferenceCandidate,
    KnowledgeBuildTarget,
    KnowledgeEntity,
)


@dataclass
class _FactAccumulator:
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


@dataclass
class _TypeRecord:
    data: dict[str, object]
    ast_artifact: SourceArtifact
    source_artifact: SourceArtifact
    module_name: str | None
    entity: KnowledgeEntity


@dataclass
class _MethodRecord:
    data: dict[str, object]
    owner: _TypeRecord
    entity: KnowledgeEntity

    @property
    def name(self) -> str:
        return str(self.data["name"])

    @property
    def arity(self) -> int:
        return int(self.data["arity"])


class ExtendedKnowledgeBuilder:
    """Builds Java, Behavior source observations, Business declarations and Git history.

    It intentionally consumes only Artifacts. The Java AST summary is a Derived
    Artifact produced by Source Integration; all admitted Evidence remains
    anchored to the original Java Source Artifact.
    """

    _README_CAPABILITY = re.compile(r"^[├└]──\s+(\S+)\s+--\s+(.+?)\s*$")
    _MAPPING_ANNOTATIONS = {
        "RequestMapping": "ANY",
        "GetMapping": "GET",
        "PostMapping": "POST",
        "PutMapping": "PUT",
        "DeleteMapping": "DELETE",
        "PatchMapping": "PATCH",
    }

    def build(
        self,
        collection: SourceCollection,
        existing_entities: tuple[KnowledgeEntity, ...],
    ) -> tuple[
        tuple[KnowledgeEntity, ...],
        tuple[Evidence, ...],
        tuple[FactCandidate, ...],
    ]:
        entities: dict[str, KnowledgeEntity] = {}
        evidence: dict[str, Evidence] = {}
        candidates: dict[tuple[str, str, str], _FactAccumulator] = {}
        existing_by_name = {
            (item.entity_type, item.name): item for item in existing_entities
        }
        source_by_id = {
            artifact.artifact_id: artifact
            for artifact in collection.artifacts
            if not artifact.lineage_ids
        }

        type_records = self._type_records(
            collection, source_by_id, entities, evidence, candidates, existing_by_name
        )
        methods = self._method_records(
            collection, type_records, entities, evidence, candidates
        )
        self._link_types_and_methods(
            collection, type_records, methods, entities, evidence, candidates
        )
        self._add_readme_capabilities(
            collection, existing_by_name, entities, evidence, candidates
        )
        self._add_git_history(collection, entities, evidence, candidates)

        return (
            tuple(sorted(entities.values(), key=lambda item: item.entity_id)),
            tuple(sorted(evidence.values(), key=lambda item: item.evidence_id)),
            tuple(
                sorted(
                    (item.freeze() for item in candidates.values()),
                    key=lambda item: item.fact_id,
                )
            ),
        )

    def build_inferences(
        self,
        collection: SourceCollection,
        entities: tuple[KnowledgeEntity, ...],
        facts: tuple[FactCandidate, ...],
        target: KnowledgeBuildTarget,
    ) -> tuple[InferenceCandidate, ...]:
        entities_by_id = {item.entity_id: item for item in entities}
        facts_by_subject: dict[str, list[FactCandidate]] = {}
        for fact in facts:
            facts_by_subject.setdefault(fact.subject_id, []).append(fact)

        candidates: list[InferenceCandidate] = []
        candidates.extend(
            self._behavior_inferences(
                collection, entities_by_id, facts_by_subject, target
            )
        )
        candidates.extend(
            self._business_inferences(
                collection, entities_by_id, facts_by_subject, target
            )
        )
        candidates.extend(
            self._history_inferences(
                collection, entities_by_id, facts_by_subject, target
            )
        )
        return tuple(sorted(candidates, key=lambda item: item.inference_id))

    def _type_records(
        self,
        collection: SourceCollection,
        source_by_id: dict[str, SourceArtifact],
        entities: dict[str, KnowledgeEntity],
        evidence: dict[str, Evidence],
        candidates: dict[tuple[str, str, str], _FactAccumulator],
        existing_by_name: dict[tuple[str, str], KnowledgeEntity],
    ) -> list[_TypeRecord]:
        records: list[_TypeRecord] = []
        module_names = {
            name for entity_type, name in existing_by_name if entity_type == "maven-module"
        }
        for ast_artifact in collection.artifacts:
            if ast_artifact.artifact_type != "java-ast-summary":
                continue
            if len(ast_artifact.lineage_ids) != 1:
                raise ValueError(
                    f"Java Derived Artifact must have one source lineage: {ast_artifact.artifact_id}"
                )
            source = source_by_id.get(ast_artifact.lineage_ids[0])
            if source is None:
                raise ValueError(
                    f"Java Derived Artifact source is absent: {ast_artifact.artifact_id}"
                )
            payload = json.loads(ast_artifact.content)
            path_root = source.relative_path.split("/", maxsplit=1)[0]
            module_name = path_root if path_root in module_names else None
            for type_data in self._flatten_types(payload.get("types", [])):
                qualified_name = str(type_data["qualified_name"])
                entity = self._entity(
                    collection.scope_id,
                    f"java-{type_data['kind']}",
                    qualified_name,
                )
                entities[entity.entity_id] = entity
                record = _TypeRecord(
                    data=type_data,
                    ast_artifact=ast_artifact,
                    source_artifact=source,
                    module_name=module_name,
                    entity=entity,
                )
                records.append(record)
                if module_name is not None:
                    module = existing_by_name[("maven-module", module_name)]
                    observation = self._evidence_for_range(
                        source,
                        int(type_data["declaration_line"]),
                        int(type_data["declaration_line"]),
                    )
                    evidence[observation.evidence_id] = observation
                    self._add_fact(
                        candidates,
                        collection,
                        module.entity_id,
                        "CONTAINS_TYPE",
                        entity.entity_id,
                        observation.evidence_id,
                    )
        return records

    def _method_records(
        self,
        collection: SourceCollection,
        type_records: list[_TypeRecord],
        entities: dict[str, KnowledgeEntity],
        evidence: dict[str, Evidence],
        candidates: dict[tuple[str, str, str], _FactAccumulator],
    ) -> list[_MethodRecord]:
        methods: list[_MethodRecord] = []
        for owner in type_records:
            qualified_name = str(owner.data["qualified_name"])
            for method_data in owner.data.get("methods", []):
                parameter_types = ",".join(
                    str(value) for value in method_data.get("parameter_types", [])
                )
                identity = (
                    f"{qualified_name}#{method_data['name']}({parameter_types})"
                )
                entity = self._entity(
                    collection.scope_id, "java-method", identity
                )
                entities[entity.entity_id] = entity
                method = _MethodRecord(data=method_data, owner=owner, entity=entity)
                methods.append(method)
                observation = self._evidence_for_range(
                    owner.source_artifact,
                    int(method_data["signature_line"]),
                    int(method_data["signature_line"]),
                )
                evidence[observation.evidence_id] = observation
                self._add_fact(
                    candidates,
                    collection,
                    owner.entity.entity_id,
                    "DECLARES_METHOD",
                    entity.entity_id,
                    observation.evidence_id,
                )

                self._add_endpoint(
                    collection, method, entities, evidence, candidates
                )
                self._add_method_observations(
                    collection, method, entities, evidence, candidates
                )
        return methods

    def _link_types_and_methods(
        self,
        collection: SourceCollection,
        types: list[_TypeRecord],
        methods: list[_MethodRecord],
        entities: dict[str, KnowledgeEntity],
        evidence: dict[str, Evidence],
        candidates: dict[tuple[str, str, str], _FactAccumulator],
    ) -> None:
        types_by_qname = {
            str(record.data["qualified_name"]): record for record in types
        }
        types_by_simple: dict[str, list[_TypeRecord]] = {}
        for record in types:
            types_by_simple.setdefault(str(record.data["name"]), []).append(record)
        methods_by_key: dict[tuple[str, str, int], list[_MethodRecord]] = {}
        for method in methods:
            key = (
                str(method.owner.data["qualified_name"]),
                method.name,
                method.arity,
            )
            methods_by_key.setdefault(key, []).append(method)

        implemented_interfaces: dict[str, list[_TypeRecord]] = {}
        for record in types:
            for interface_name in record.data.get("interfaces", []):
                target = self._resolve_type(
                    str(interface_name), record, types_by_qname, types_by_simple
                )
                if target is None:
                    continue
                implemented_interfaces.setdefault(record.entity.entity_id, []).append(target)
                observation = self._evidence_for_range(
                    record.source_artifact,
                    int(record.data["declaration_line"]),
                    int(record.data["declaration_line"]),
                )
                evidence[observation.evidence_id] = observation
                self._add_fact(
                    candidates,
                    collection,
                    record.entity.entity_id,
                    "IMPLEMENTS_TYPE",
                    target.entity.entity_id,
                    observation.evidence_id,
                )

        for method in methods:
            for interface in implemented_interfaces.get(
                method.owner.entity.entity_id, []
            ):
                matches = methods_by_key.get(
                    (
                        str(interface.data["qualified_name"]),
                        method.name,
                        method.arity,
                    ),
                    [],
                )
                if len(matches) != 1:
                    continue
                target = matches[0]
                implementation_evidence = self._evidence_for_range(
                    method.owner.source_artifact,
                    int(method.data["signature_line"]),
                    int(method.data["signature_line"]),
                )
                interface_evidence = self._evidence_for_range(
                    target.owner.source_artifact,
                    int(target.data["signature_line"]),
                    int(target.data["signature_line"]),
                )
                for observation in (implementation_evidence, interface_evidence):
                    evidence[observation.evidence_id] = observation
                    self._add_fact(
                        candidates,
                        collection,
                        method.entity.entity_id,
                        "IMPLEMENTS_METHOD",
                        target.entity.entity_id,
                        observation.evidence_id,
                    )

        for method in methods:
            fields = {
                str(item["name"]): str(item["type"])
                for item in method.owner.data.get("fields", [])
            }
            for call in method.data.get("calls", []):
                target = self._resolve_call(
                    call,
                    method,
                    fields,
                    types_by_qname,
                    types_by_simple,
                    methods_by_key,
                )
                predicate = "CALLS"
                if target is None:
                    owner_hint = str(call.get("object") or method.owner.data["qualified_name"])
                    operation_name = (
                        f"{owner_hint}#{call['name']}/{int(call['arity'])}"
                    )
                    operation = self._entity(
                        collection.scope_id,
                        "operation-mention",
                        operation_name,
                    )
                    entities[operation.entity_id] = operation
                    target_entity = operation
                    predicate = "CALLS_OPERATION"
                else:
                    target_entity = target.entity
                observation = self._evidence_for_range(
                    method.owner.source_artifact,
                    int(call["line"]),
                    int(call["line"]),
                )
                evidence[observation.evidence_id] = observation
                self._add_fact(
                    candidates,
                    collection,
                    method.entity.entity_id,
                    predicate,
                    target_entity.entity_id,
                    observation.evidence_id,
                )

    def _add_endpoint(
        self,
        collection: SourceCollection,
        method: _MethodRecord,
        entities: dict[str, KnowledgeEntity],
        evidence: dict[str, Evidence],
        candidates: dict[tuple[str, str, str], _FactAccumulator],
    ) -> None:
        class_mapping = self._mapping(method.owner.data.get("annotations", []))
        method_mapping = self._mapping(method.data.get("annotations", []))
        if method_mapping is None:
            return
        base_path = class_mapping[1] if class_mapping is not None else ""
        http_method, method_path, line_start, line_end = method_mapping
        path = self._join_route(base_path, method_path)
        endpoint = self._entity(
            collection.scope_id, "web-endpoint", f"{http_method} {path}"
        )
        entities[endpoint.entity_id] = endpoint
        method_observation = self._evidence_for_range(
            method.owner.source_artifact, line_start, line_end
        )
        evidence[method_observation.evidence_id] = method_observation
        self._add_fact(
            candidates,
            collection,
            method.entity.entity_id,
            "EXPOSES_ENDPOINT",
            endpoint.entity_id,
            method_observation.evidence_id,
        )
        if class_mapping is not None:
            _, _, class_line_start, class_line_end = class_mapping
            class_observation = self._evidence_for_range(
                method.owner.source_artifact,
                class_line_start,
                class_line_end,
            )
            evidence[class_observation.evidence_id] = class_observation
            self._add_fact(
                candidates,
                collection,
                method.entity.entity_id,
                "EXPOSES_ENDPOINT",
                endpoint.entity_id,
                class_observation.evidence_id,
            )

    def _add_method_observations(
        self,
        collection: SourceCollection,
        method: _MethodRecord,
        entities: dict[str, KnowledgeEntity],
        evidence: dict[str, Evidence],
        candidates: dict[tuple[str, str, str], _FactAccumulator],
    ) -> None:
        steps: list[tuple[KnowledgeEntity, Evidence]] = []
        for comment in method.data.get("comments", []):
            text = self._clean_comment(str(comment["text"]))
            if not text or text.startswith("TODO:"):
                continue
            line_start = int(comment["line_start"])
            step = self._entity(
                collection.scope_id,
                "source-step-declaration",
                f"{method.entity.name}@{line_start}:{text}",
            )
            entities[step.entity_id] = step
            observation = self._evidence_for_range(
                method.owner.source_artifact,
                line_start,
                int(comment["line_end"]),
            )
            evidence[observation.evidence_id] = observation
            self._add_fact(
                candidates,
                collection,
                method.entity.entity_id,
                "DECLARES_STEP",
                step.entity_id,
                observation.evidence_id,
            )
            steps.append((step, observation))
        for (before, before_evidence), (after, after_evidence) in zip(
            steps, steps[1:]
        ):
            for observation in (before_evidence, after_evidence):
                self._add_fact(
                    candidates,
                    collection,
                    before.entity_id,
                    "PRECEDES",
                    after.entity_id,
                    observation.evidence_id,
                )

        for guard in method.data.get("failure_guards", []):
            condition = str(guard["condition"])
            message = str(guard.get("message") or "unknown failure")
            guard_entity = self._entity(
                collection.scope_id,
                "failure-guard",
                f"{method.entity.name}: IF {condition} THEN FAIL {message}",
            )
            entities[guard_entity.entity_id] = guard_entity
            observation = self._evidence_for_range(
                method.owner.source_artifact,
                int(guard["line_start"]),
                int(guard["line_end"]),
            )
            evidence[observation.evidence_id] = observation
            self._add_fact(
                candidates,
                collection,
                method.entity.entity_id,
                "HAS_FAILURE_GUARD",
                guard_entity.entity_id,
                observation.evidence_id,
            )

    def _add_readme_capabilities(
        self,
        collection: SourceCollection,
        existing_by_name: dict[tuple[str, str], KnowledgeEntity],
        entities: dict[str, KnowledgeEntity],
        evidence: dict[str, Evidence],
        candidates: dict[tuple[str, str, str], _FactAccumulator],
    ) -> None:
        readme = next(
            (
                artifact
                for artifact in collection.artifacts
                if artifact.relative_path == "README.md"
                and artifact.artifact_type == "markdown-document"
            ),
            None,
        )
        if readme is None:
            return
        for line_number, line in enumerate(readme.content.splitlines(), start=1):
            match = self._README_CAPABILITY.match(line.strip())
            if match is None:
                continue
            module_name, description = match.groups()
            module = existing_by_name.get(("maven-module", module_name))
            if module is None:
                continue
            capability = self._entity(
                collection.scope_id,
                "declared-capability",
                description,
            )
            entities[capability.entity_id] = capability
            observation = self._evidence_for_range(
                readme, line_number, line_number
            )
            evidence[observation.evidence_id] = observation
            self._add_fact(
                candidates,
                collection,
                module.entity_id,
                "HAS_DECLARED_CAPABILITY",
                capability.entity_id,
                observation.evidence_id,
            )

    def _add_git_history(
        self,
        collection: SourceCollection,
        entities: dict[str, KnowledgeEntity],
        evidence: dict[str, Evidence],
        candidates: dict[tuple[str, str, str], _FactAccumulator],
    ) -> None:
        for artifact in collection.artifacts:
            if artifact.artifact_type != "git-commit":
                continue
            lines = artifact.content.splitlines()
            commit_hash = next(
                (line.split(maxsplit=1)[1] for line in lines if line.startswith("commit ")),
                artifact.revision,
            )
            commit = self._entity(
                collection.scope_id, "git-commit", commit_hash
            )
            entities[commit.entity_id] = commit
            for line_number, line in enumerate(lines, start=1):
                if not line.startswith("AuthorDate:"):
                    continue
                authored_at = line.split(":", maxsplit=1)[1].strip()
                time_point = self._entity(
                    collection.scope_id, "time-point", authored_at
                )
                entities[time_point.entity_id] = time_point
                observation = self._evidence_for_range(
                    artifact, line_number, line_number
                )
                evidence[observation.evidence_id] = observation
                self._add_fact(
                    candidates,
                    collection,
                    commit.entity_id,
                    "AUTHORED_AT",
                    time_point.entity_id,
                    observation.evidence_id,
                    revision=artifact.revision,
                )
                break
            message_line = self._commit_message_line(lines)
            if message_line is not None:
                message = lines[message_line - 1].strip()
                declaration = self._entity(
                    collection.scope_id,
                    "change-declaration",
                    message,
                )
                entities[declaration.entity_id] = declaration
                observation = self._evidence_for_range(
                    artifact, message_line, message_line
                )
                evidence[observation.evidence_id] = observation
                self._add_fact(
                    candidates,
                    collection,
                    commit.entity_id,
                    "DECLARES_CHANGE",
                    declaration.entity_id,
                    observation.evidence_id,
                    revision=artifact.revision,
                )

            for line_number, line in enumerate(lines, start=1):
                if not line.startswith("diff --git a/"):
                    continue
                match = re.match(r"diff --git a/(.+?) b/(.+)$", line)
                if match is None:
                    continue
                changed_file = self._entity(
                    collection.scope_id, "source-file", match.group(2)
                )
                entities[changed_file.entity_id] = changed_file
                observation = self._evidence_for_range(
                    artifact, line_number, line_number
                )
                evidence[observation.evidence_id] = observation
                self._add_fact(
                    candidates,
                    collection,
                    commit.entity_id,
                    "CHANGED_FILE",
                    changed_file.entity_id,
                    observation.evidence_id,
                    revision=artifact.revision,
                )

            for old_line, new_line in self._adjacent_diff_replacements(lines):
                change = self._entity(
                    collection.scope_id,
                    "line-change",
                    f"{lines[old_line - 1]} => {lines[new_line - 1]}",
                )
                entities[change.entity_id] = change
                observation = self._evidence_for_range(
                    artifact, old_line, new_line
                )
                evidence[observation.evidence_id] = observation
                self._add_fact(
                    candidates,
                    collection,
                    commit.entity_id,
                    "HAS_LINE_REPLACEMENT",
                    change.entity_id,
                    observation.evidence_id,
                    revision=artifact.revision,
                )

            for hunk_start, hunk_end in self._diff_hunks(lines):
                header = lines[hunk_start - 1]
                hunk = self._entity(
                    collection.scope_id,
                    "diff-hunk",
                    f"{commit_hash}:{hunk_start}:{header}",
                )
                entities[hunk.entity_id] = hunk
                observation = self._evidence_for_range(
                    artifact, hunk_start, hunk_end
                )
                evidence[observation.evidence_id] = observation
                self._add_fact(
                    candidates,
                    collection,
                    commit.entity_id,
                    "HAS_DIFF_HUNK",
                    hunk.entity_id,
                    observation.evidence_id,
                    revision=artifact.revision,
                )
                for before, after in self._ordering_changes(
                    lines, hunk_start, hunk_end
                ):
                    ordering = self._entity(
                        collection.scope_id,
                        "ordering-change",
                        f"{before} now precedes {after}",
                    )
                    entities[ordering.entity_id] = ordering
                    self._add_fact(
                        candidates,
                        collection,
                        commit.entity_id,
                        "CHANGED_ORDER",
                        ordering.entity_id,
                        observation.evidence_id,
                        revision=artifact.revision,
                    )

    def _behavior_inferences(
        self,
        collection: SourceCollection,
        entities_by_id: dict[str, KnowledgeEntity],
        facts_by_subject: dict[str, list[FactCandidate]],
        target: KnowledgeBuildTarget,
    ) -> list[InferenceCandidate]:
        result: list[InferenceCandidate] = []
        focus = dict(target.behavior_methods)
        for method in entities_by_id.values():
            if method.entity_type != "java-method":
                continue
            title = next(
                (label for marker, label in focus.items() if marker in method.name),
                None,
            )
            if title is None:
                continue
            step_facts = [
                fact
                for fact in facts_by_subject.get(method.entity_id, [])
                if fact.predicate == "DECLARES_STEP"
            ]
            step_facts.sort(
                key=lambda fact: self._step_line(
                    entities_by_id[fact.object_id].name
                )
            )
            if not step_facts:
                continue
            steps = [
                self._step_text(entities_by_id[fact.object_id].name)
                for fact in step_facts
            ]
            implementation_facts = [
                fact
                for fact in facts_by_subject.get(method.entity_id, [])
                if fact.predicate
                in {"CALLS", "CALLS_OPERATION", "HAS_FAILURE_GUARD"}
            ]
            statement = (
                f"{title}综合实际调用、失败条件与内联注释归纳的流程包括："
                + "；".join(steps)
            )
            result.append(
                self._inference(
                    collection,
                    "BEHAVIOR_FLOW",
                    statement,
                    tuple(
                        fact.fact_id
                        for fact in (*step_facts, *implementation_facts)
                    ),
                )
            )
        return result

    def _business_inferences(
        self,
        collection: SourceCollection,
        entities_by_id: dict[str, KnowledgeEntity],
        facts_by_subject: dict[str, list[FactCandidate]],
        target: KnowledgeBuildTarget,
    ) -> list[InferenceCandidate]:
        result: list[InferenceCandidate] = []
        constraint_focus = dict(target.business_constraint_methods)
        for subject_id, facts in facts_by_subject.items():
            subject = entities_by_id.get(subject_id)
            if subject is None:
                continue
            constraint_label = next(
                (
                    label
                    for marker, label in constraint_focus.items()
                    if marker in subject.name
                ),
                None,
            )
            if subject.entity_type == "java-method" and constraint_label:
                for fact in facts:
                    if fact.predicate != "HAS_FAILURE_GUARD":
                        continue
                    guard = entities_by_id[fact.object_id]
                    detail = guard.name.split(": IF ", maxsplit=1)[-1]
                    result.append(
                        self._inference(
                            collection,
                            "BUSINESS_CONSTRAINT",
                            f"{constraint_label}业务约束候选：{detail}",
                            (fact.fact_id,),
                        )
                    )
            if subject.entity_type == "maven-module" and (
                "*" in target.capability_modules
                or subject.name in target.capability_modules
            ):
                for fact in facts:
                    if fact.predicate != "HAS_DECLARED_CAPABILITY":
                        continue
                    capability = entities_by_id[fact.object_id]
                    result.append(
                        self._inference(
                            collection,
                            "BUSINESS_CAPABILITY",
                            f"{subject.name} 承载的业务能力可概括为：{capability.name}",
                            (fact.fact_id,),
                        )
                    )
        return result

    def _history_inferences(
        self,
        collection: SourceCollection,
        entities_by_id: dict[str, KnowledgeEntity],
        facts_by_subject: dict[str, list[FactCandidate]],
        target: KnowledgeBuildTarget,
    ) -> list[InferenceCandidate]:
        result: list[InferenceCandidate] = []
        for commit in entities_by_id.values():
            if commit.entity_type != "git-commit":
                continue
            if target.history_commits and not any(
                commit.name.startswith(value) for value in target.history_commits
            ):
                continue
            facts = facts_by_subject.get(commit.entity_id, [])
            declarations = [
                entities_by_id[fact.object_id].name
                for fact in facts
                if fact.predicate == "DECLARES_CHANGE"
            ]
            changed_files = [
                entities_by_id[fact.object_id].name
                for fact in facts
                if fact.predicate == "CHANGED_FILE"
            ]
            authored_at = [
                entities_by_id[fact.object_id].name
                for fact in facts
                if fact.predicate == "AUTHORED_AT"
            ]
            ordering_changes = [
                entities_by_id[fact.object_id].name
                for fact in facts
                if fact.predicate == "CHANGED_ORDER"
            ]
            support_ids = tuple(
                fact.fact_id
                for fact in facts
                if fact.predicate
                in {
                    "AUTHORED_AT",
                    "DECLARES_CHANGE",
                    "CHANGED_FILE",
                    "HAS_LINE_REPLACEMENT",
                    "HAS_DIFF_HUNK",
                    "CHANGED_ORDER",
                }
            )
            if not declarations or not support_ids:
                continue
            areas = self._change_areas(changed_files)
            time_clause = f"于 {authored_at[0]} " if authored_at else ""
            ordering_clause = (
                f" 可确认的执行顺序变化为：{'；'.join(ordering_changes)}。"
                if 0 < len(ordering_changes) <= 3
                else ""
            )
            statement = (
                f"提交 {commit.name[:7]} {time_clause}声明“{declarations[0]}”；"
                f"可确认影响区域为 {', '.join(areas)}。"
                f"{ordering_clause}"
                "该结论不补写提交信息之外的作者动机。"
            )
            result.append(
                self._inference(
                    collection,
                    "HISTORY_IMPACT",
                    statement,
                    support_ids,
                    revision=commit.name,
                )
            )
        return result

    @staticmethod
    def _resolve_call(
        call: dict[str, object],
        method: _MethodRecord,
        fields: dict[str, str],
        types_by_qname: dict[str, _TypeRecord],
        types_by_simple: dict[str, list[_TypeRecord]],
        methods_by_key: dict[tuple[str, str, int], list[_MethodRecord]],
    ) -> _MethodRecord | None:
        object_name = call.get("object")
        owner: _TypeRecord | None = None
        if object_name is None or object_name in {"this", "super"}:
            owner = method.owner
        elif str(object_name) in fields:
            owner = ExtendedKnowledgeBuilder._resolve_type(
                fields[str(object_name)],
                method.owner,
                types_by_qname,
                types_by_simple,
            )
        elif re.fullmatch(r"[A-Za-z_$][\w$]*", str(object_name)):
            owner = ExtendedKnowledgeBuilder._resolve_type(
                str(object_name),
                method.owner,
                types_by_qname,
                types_by_simple,
            )
        if owner is None:
            return None
        matches = methods_by_key.get(
            (
                str(owner.data["qualified_name"]),
                str(call["name"]),
                int(call["arity"]),
            ),
            [],
        )
        return matches[0] if len(matches) == 1 else None

    @staticmethod
    def _resolve_type(
        raw_name: str,
        context: _TypeRecord,
        types_by_qname: dict[str, _TypeRecord],
        types_by_simple: dict[str, list[_TypeRecord]],
    ) -> _TypeRecord | None:
        name = re.sub(r"<.*>", "", raw_name).replace("[]", "").strip()
        if name in types_by_qname:
            return types_by_qname[name]
        simple = name.rsplit(".", maxsplit=1)[-1]
        payload = json.loads(context.ast_artifact.content)
        for imported in payload.get("imports", []):
            if imported.get("static"):
                continue
            import_name = str(imported["name"])
            candidate = (
                f"{import_name}.{simple}"
                if imported.get("wildcard")
                else import_name
            )
            if candidate.rsplit(".", maxsplit=1)[-1] == simple and candidate in types_by_qname:
                return types_by_qname[candidate]
        package = str(payload.get("package") or "")
        same_package = f"{package}.{simple}" if package else simple
        if same_package in types_by_qname:
            return types_by_qname[same_package]
        matches = types_by_simple.get(simple, [])
        return matches[0] if len(matches) == 1 else None

    @classmethod
    def _mapping(
        cls, annotations: Iterable[dict[str, object]]
    ) -> tuple[str, str, int, int] | None:
        for annotation in annotations:
            name = str(annotation["name"]).rsplit(".", maxsplit=1)[-1]
            default_method = cls._MAPPING_ANNOTATIONS.get(name)
            if default_method is None:
                continue
            text = str(annotation["text"])
            quoted = re.findall(r'"([^"\\]*(?:\\.[^"\\]*)*)"', text)
            path = quoted[0] if quoted else ""
            method_match = re.search(r"RequestMethod\.([A-Z]+)", text)
            http_method = method_match.group(1) if method_match else default_method
            return (
                http_method,
                path,
                int(annotation["line_start"]),
                int(annotation["line_end"]),
            )
        return None

    @staticmethod
    def _join_route(base: str, path: str) -> str:
        segments = [item.strip("/") for item in (base, path) if item.strip("/")]
        return "/" + "/".join(segments)

    @staticmethod
    def _flatten_types(values: Iterable[dict[str, object]]) -> Iterable[dict[str, object]]:
        for item in values:
            yield item
            yield from ExtendedKnowledgeBuilder._flatten_types(
                item.get("nested_types", [])
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
    def _evidence_for_range(
        artifact: SourceArtifact, line_start: int, line_end: int
    ) -> Evidence:
        lines = artifact.content.splitlines()
        if line_start < 1 or line_end > len(lines) or line_start > line_end:
            raise ValueError(
                f"invalid Evidence range {line_start}-{line_end} for {artifact.relative_path}"
            )
        quote = "\n".join(line.strip() for line in lines[line_start - 1 : line_end])
        digest = content_hash(quote)
        return Evidence(
            evidence_id=stable_id(
                "evidence", artifact.artifact_id, line_start, line_end, digest
            ),
            artifact_id=artifact.artifact_id,
            scope_id=artifact.scope_id,
            revision=artifact.revision,
            line_start=line_start,
            line_end=line_end,
            quote=quote,
            quote_hash=digest,
        )

    @staticmethod
    def _add_fact(
        candidates: dict[tuple[str, str, str], _FactAccumulator],
        collection: SourceCollection,
        subject_id: str,
        predicate: str,
        object_id: str,
        evidence_id: str,
        revision: str | None = None,
    ) -> None:
        key = (subject_id, predicate, object_id)
        candidate = candidates.get(key)
        if candidate is None:
            candidate = _FactAccumulator(
                fact_id=stable_id(
                    "fact", collection.scope_id, subject_id, predicate, object_id
                ),
                scope_id=collection.scope_id,
                revision=revision or collection.revision,
                subject_id=subject_id,
                predicate=predicate,
                object_id=object_id,
            )
            candidates[key] = candidate
        candidate.evidence_ids.append(evidence_id)

    @staticmethod
    def _inference(
        collection: SourceCollection,
        inference_type: str,
        statement: str,
        support_fact_ids: tuple[str, ...],
        dependency_inference_ids: tuple[str, ...] = (),
        revision: str | None = None,
    ) -> InferenceCandidate:
        support = tuple(sorted(set(support_fact_ids)))
        dependencies = tuple(sorted(set(dependency_inference_ids)))
        return InferenceCandidate(
            inference_id=stable_id(
                "inference",
                collection.scope_id,
                inference_type,
                statement,
                *support,
                *dependencies,
            ),
            scope_id=collection.scope_id,
            revision=revision or collection.revision,
            inference_type=inference_type,
            statement=statement,
            support_fact_ids=support,
            dependency_inference_ids=dependencies,
            model_call_id=None,
        )

    @staticmethod
    def _clean_comment(value: str) -> str:
        text = value.strip()
        if text.startswith("//"):
            return text[2:].strip()
        if text.startswith("/*"):
            text = text.removeprefix("/*").removesuffix("*/")
            return " ".join(
                line.strip().lstrip("*").strip()
                for line in text.splitlines()
                if line.strip().lstrip("*").strip()
            )
        return text

    @staticmethod
    def _step_text(name: str) -> str:
        return name.split(":", maxsplit=1)[-1]

    @staticmethod
    def _step_line(name: str) -> int:
        match = re.search(r"@(\d+):", name)
        return int(match.group(1)) if match else 0

    @staticmethod
    def _commit_message_line(lines: list[str]) -> int | None:
        for index, line in enumerate(lines, start=1):
            if line.startswith("diff --git "):
                break
            if line.startswith("    ") and line.strip():
                return index
        return None

    @staticmethod
    def _adjacent_diff_replacements(lines: list[str]) -> Iterable[tuple[int, int]]:
        index = 0
        while index < len(lines) - 1:
            current = lines[index]
            following = lines[index + 1]
            if (
                current.startswith("-")
                and not current.startswith("---")
                and following.startswith("+")
                and not following.startswith("+++")
            ):
                yield index + 1, index + 2
                index += 2
                continue
            index += 1

    @staticmethod
    def _diff_hunks(lines: list[str]) -> Iterable[tuple[int, int]]:
        starts = [
            index
            for index, line in enumerate(lines, start=1)
            if line.startswith("@@ ")
        ]
        for start in starts:
            end = start
            while end < len(lines):
                following = lines[end]
                if following.startswith("@@ ") or following.startswith("diff --git "):
                    break
                end += 1
            yield start, end

    @staticmethod
    def _ordering_changes(
        lines: list[str], start: int, end: int
    ) -> Iterable[tuple[str, str]]:
        old: list[str] = []
        new: list[str] = []
        for line in lines[start:end]:
            if not line or line.startswith("\\ No newline"):
                continue
            marker, content = line[0], line[1:].strip()
            if not content:
                continue
            if marker in {" ", "-"}:
                old.append(content)
            if marker in {" ", "+"}:
                new.append(content)
        if old == new or Counter(old) != Counter(new):
            return
        common = [
            item
            for item in old
            if old.count(item) == 1 and new.count(item) == 1
        ]
        for left_index, left in enumerate(common):
            for right in common[left_index + 1 :]:
                old_order = old.index(left) < old.index(right)
                new_order = new.index(left) < new.index(right)
                if old_order == new_order:
                    continue
                yield (left, right) if new_order else (right, left)

    @staticmethod
    def _change_areas(paths: list[str]) -> list[str]:
        areas: list[str] = []
        if any(path.endswith("pom.xml") for path in paths):
            areas.append("构建与依赖")
        if any("/config/" in path or path.endswith((".yml", ".yaml")) for path in paths):
            areas.append("配置")
        if any("/controller/" in path for path in paths):
            areas.append("接口层")
        if any("/service/" in path for path in paths):
            areas.append("服务实现")
        if any(path == "README.md" or path.startswith("document/") for path in paths):
            areas.append("文档")
        if not areas:
            areas.append("源代码")
        return areas
