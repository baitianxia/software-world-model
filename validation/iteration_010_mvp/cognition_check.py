"""Independent five-task check for a capability-cognition artifact."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Mapping, Sequence

from software_world_model.cross_cutting import DomainError, ErrorCode, canonical_json_bytes, digest_of
from software_world_model.infrastructure.file_capability_cognition import load_capability_cognition
from software_world_model.knowledge_engine.capability_cognition import (
    CapabilityCognitionIndex,
    CognitionEntityKind,
    CognitionRelationKind,
    CognitionResolution,
)


REPORT_SCHEMA = "ITER_010_CAPABILITY_COGNITION_TASK_REPORT@1"
TASK_SET_SCHEMA = "ITER_010_CAPABILITY_COGNITION_TASK_SET@1"


def run(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check five independent cognition tasks")
    parser.add_argument("--artifact", required=True)
    parser.add_argument("--tasks", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    artifact = _absolute(args.artifact)
    task_path = _absolute(args.tasks)
    output = _absolute(args.output)
    snapshot = load_capability_cognition(artifact)
    task_document = _json_object(task_path)
    if task_document.get("schema") != TASK_SET_SCHEMA:
        raise DomainError(ErrorCode.INVALID_ARGUMENT, "cognition task-set schema is unsupported")
    tasks = task_document.get("tasks")
    if not isinstance(tasks, list) or len(tasks) < 5:
        raise DomainError(ErrorCode.INVALID_ARGUMENT, "at least five cognition tasks are required")
    task_ids = [item.get("task_id") for item in tasks if isinstance(item, Mapping)]
    if len(task_ids) != len(tasks) or len(set(task_ids)) != len(tasks):
        raise DomainError(ErrorCode.INVALID_ARGUMENT, "cognition task IDs must be unique")
    index = CapabilityCognitionIndex(snapshot)
    entity_by_id = {item.entity_id: item for item in snapshot.entities}
    outcomes = []
    for raw_task in tasks:
        task = _mapping(raw_task, "cognition task")
        failures: list[str] = []
        query = _required_text(task, "query")
        qualified = _required_text(task, "qualified_name")
        search = index.search(query, limit=64)
        entity = next(
            (
                item
                for item in snapshot.entities
                if item.qualified_name == qualified
                and any(result["entity_id"] == item.entity_id.value for result in search.items)
            ),
            None,
        )
        evidence: dict[str, object] = {
            "search_total": search.total,
            "search_snapshot_digest": search.snapshot_digest.value,
        }
        if entity is None:
            failures.append("expected entity was not returned by bounded cognition search")
        else:
            evidence.update(
                {
                    "entity_id": entity.entity_id.value,
                    "entity_kind": entity.kind.value,
                    "entity_provenance": entity.provenance.to_payload(),
                }
            )
            expected_kind = task.get("entity_kind")
            if expected_kind is not None and entity.kind is not CognitionEntityKind(expected_kind):
                failures.append("entity kind differs from the frozen task")
            operation = _required_text(task, "operation")
            if operation == "PARENT_CHAIN":
                actual = []
                current = entity
                while current.parent_id is not None:
                    current = entity_by_id[current.parent_id]
                    actual.append(current.kind.value)
                expected = task.get("expected_parent_kinds")
                if actual != expected:
                    failures.append(f"parent chain differs: {actual!r}")
                evidence["parent_kinds"] = actual
            elif operation == "RELATION":
                relation = _find_relation(snapshot, entity.entity_id, task, entity_by_id)
                if relation is None:
                    failures.append("expected relation was not found")
                else:
                    evidence["relation"] = relation.to_payload()
            elif operation == "BEHAVIOR":
                behaviors = [item for item in snapshot.behaviors if item.method_id == entity.entity_id]
                actual_kinds = sorted({item.kind.value for item in behaviors})
                expected_kinds = sorted(task.get("expected_behavior_kinds", ()))
                missing_kinds = sorted(set(expected_kinds).difference(actual_kinds))
                if missing_kinds:
                    failures.append(f"behavior kinds are missing: {missing_kinds!r}")
                statements = [item.statement for item in behaviors]
                missing_fragments = [
                    fragment
                    for fragment in task.get("expected_statement_fragments", ())
                    if not any(fragment in statement for statement in statements)
                ]
                if missing_fragments:
                    failures.append(f"behavior statements are missing: {missing_fragments!r}")
                if [item.ordinal for item in behaviors] != list(range(len(behaviors))):
                    failures.append("behavior sequence is not in exact Source order")
                evidence["behavior_kinds"] = actual_kinds
                evidence["behavior_count"] = len(behaviors)
                evidence["behavior_provenance"] = [item.provenance.to_payload() for item in behaviors]
            elif operation == "EPISTEMIC_RELATION":
                relation = _find_relation(snapshot, entity.entity_id, task, entity_by_id)
                if relation is None:
                    failures.append("expected epistemic relation was not found")
                else:
                    if not relation.epistemics.unknowns:
                        failures.append("partial relation failed to preserve its Unknown")
                    if relation.epistemics.coverage.value != "PARTIAL":
                        failures.append("epistemic relation falsely claims complete coverage")
                    evidence["relation"] = relation.to_payload()
            else:
                failures.append(f"unsupported cognition task operation: {operation}")
        outcomes.append(
            {
                "task_id": task["task_id"],
                "operation": task["operation"],
                "status": "PASS" if not failures else "FAIL",
                "failures": failures,
                "evidence": evidence,
            }
        )
    core = {
        "schema": REPORT_SCHEMA,
        "artifact": str(artifact),
        "artifact_digest": snapshot.digest.value,
        "snapshot_id": snapshot.snapshot_id.value,
        "source_revision": snapshot.source_revision,
        "source_tree": snapshot.source_tree,
        "task_set": str(task_path),
        "task_count": len(outcomes),
        "passed_count": sum(item["status"] == "PASS" for item in outcomes),
        "status": "PASS" if all(item["status"] == "PASS" for item in outcomes) else "FAIL",
        "same_snapshot_reused_for_every_task": all(
            item["evidence"].get("search_snapshot_digest") == snapshot.digest.value
            for item in outcomes
        ),
        "outcomes": outcomes,
    }
    report = {**core, "digest": digest_of(core).value}
    _write_new(output, report)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0 if report["status"] == "PASS" else 1


def _find_relation(snapshot, subject_id, task, entity_by_id):
    kind = CognitionRelationKind(_required_text(task, "relation_kind"))
    expected_resolution = CognitionResolution(_required_text(task, "expected_resolution"))
    object_qualified = task.get("object_qualified_name")
    symbol_fragment = task.get("object_symbol_contains")
    for relation in snapshot.relations:
        if relation.subject_id != subject_id or relation.kind is not kind:
            continue
        if relation.resolution is not expected_resolution:
            continue
        if object_qualified is not None:
            if relation.object_id is None or entity_by_id[relation.object_id].qualified_name != object_qualified:
                continue
        if symbol_fragment is not None and symbol_fragment not in relation.object_symbol:
            continue
        return relation
    return None


def _json_object(path: Path) -> Mapping[str, object]:
    if path.is_symlink() or not path.is_file():
        raise DomainError(ErrorCode.SOURCE_TARGET_NOT_FOUND, "cognition task file is absent")
    try:
        value = json.loads(path.read_bytes())
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DomainError(ErrorCode.STRUCTURED_OUTPUT_INVALID, "cognition task file is invalid JSON") from exc
    return _mapping(value, "cognition task set")


def _write_new(path: Path, value: Mapping[str, object]) -> None:
    payload = canonical_json_bytes(value) + b"\n"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags, 0o600)
    except OSError as exc:
        raise DomainError(ErrorCode.CONTROL_STATE_DENIED, "cognition report path is not new") from exc
    try:
        written = 0
        while written < len(payload):
            written += os.write(descriptor, payload[written:])
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _absolute(value: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        raise DomainError(ErrorCode.INVALID_ARGUMENT, "cognition check paths must be absolute")
    return path


def _mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping) or any(not isinstance(key, str) for key in value):
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} must be an object")
    return value


def _required_text(value: Mapping[str, object], key: str) -> str:
    item = value.get(key)
    if not isinstance(item, str) or not item or item != item.strip():
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{key} must be canonical text")
    return item


if __name__ == "__main__":
    raise SystemExit(run())
