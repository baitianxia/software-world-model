"""Generate the frozen ITER-002 SQLite compatibility input.

Run this script only with ``PYTHONPATH`` pointing at the exact implementation
recorded by ``--generation-commit``.  The fixture contains synthetic source text
and no provider output or credentials.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path

from software_world_model.cross_cutting import (
    CorrelationRef,
    Digest,
    IdempotencyKey,
    Revision,
    StableId,
    digest_of,
)
from software_world_model.infrastructure import (
    SqliteDatabase,
    SqliteFormalKnowledgeRepository,
    SqliteKnowledgeScopeRepository,
)
from software_world_model.knowledge_engine import (
    EntityProposal,
    EvidenceProposal,
    FactProposal,
    FormalKnowledgeService,
    KnowledgeCandidateBundle,
    KnowledgeContext,
    KnowledgeObjectKind,
    KnowledgeScopeService,
    ScopeType,
)
from software_world_model.source_integration import SourceArtifact


class SequenceIds:
    def __init__(self) -> None:
        self._next = 1

    def new(self, kind: str) -> StableId:
        value = self._next
        self._next += 1
        return StableId(f"{kind}_{value:032x}")


class StepClock:
    def __init__(self) -> None:
        self._value = datetime(2026, 8, 10, tzinfo=timezone.utc)

    def __call__(self) -> datetime:
        value = self._value
        self._value += timedelta(microseconds=1)
        return value


def generate(output_directory: Path, generation_commit: str) -> dict[str, object]:
    output_directory.mkdir(parents=True, exist_ok=True)
    database_path = output_directory / "iteration-002-legacy.sqlite3"
    report_path = output_directory / "iteration-002-legacy-report.json"
    sidecar_paths = tuple(
        Path(f"{database_path}{suffix}") for suffix in ("-shm", "-wal")
    )
    for path in (database_path, report_path, *sidecar_paths):
        if path.exists():
            path.unlink()

    clock = StepClock()
    database = SqliteDatabase(database_path)
    scope_service = KnowledgeScopeService(
        SqliteKnowledgeScopeRepository(database, id_generator=SequenceIds()),
        clock=clock,
    )
    scope = scope_service.create_scope(
        scope_type=ScopeType.SYSTEM,
        metadata={"display_name": "ITER-002 legacy compatibility fixture"},
        idempotency_key=IdempotencyKey("iteration-003-legacy-scope"),
        actor="iteration-003-fixture-generator",
        reason="freeze pre-Root-State persistence",
        correlation_ref=CorrelationRef("iteration-003-g0"),
    )
    knowledge = FormalKnowledgeService(
        SqliteFormalKnowledgeRepository(database, id_generator=SequenceIds()),
        scope_service,
        clock=clock,
    )

    payload = b"public final class LegacyOrderService {}\n"
    artifact = SourceArtifact(
        artifact_id=StableId("source_artifact_00000000000000000000000000000001"),
        artifact_kind="LOCAL_GIT_FILE@1",
        payload_schema_version="1",
        source_id=StableId("source_00000000000000000000000000000001"),
        source_revision=Revision(1),
        source_context_id=StableId("source_context_00000000000000000000000000000001"),
        source_native_identity="src/LegacyOrderService.java",
        content_digest=Digest(f"sha256:{hashlib.sha256(payload).hexdigest()}"),
        payload=payload,
        classification="PUBLIC",
        truncated=False,
        truncation_offset=None,
        identity_digest=digest_of({"fixture": "iteration-002-legacy-source@1"}),
    )
    context = KnowledgeContext.create(
        {
            "repository_revision": "a" * 40,
            "environment": "iteration-002-legacy-fixture",
        }
    )
    bundle = KnowledgeCandidateBundle(
        schema_version="INITIAL@1",
        evidence=(
            EvidenceProposal(
                evidence_key="evidence:legacy-class",
                artifact=artifact,
                byte_start=0,
                byte_end=len(payload),
                locator="src/LegacyOrderService.java:1",
            ),
        ),
        entities=(
            EntityProposal(
                candidate_key="entity:legacy-service",
                entity_type="CODE_SYMBOL",
                natural_key="LegacyOrderService",
                label="LegacyOrderService",
                context=context,
                evidence_keys=("evidence:legacy-class",),
            ),
        ),
        facts=(
            FactProposal(
                candidate_key="fact:legacy-declares",
                subject_candidate_key="entity:legacy-service",
                subject_entity_id=None,
                predicate="DECLARES",
                object_value="LegacyOrderService",
                context=context,
                evidence_keys=("evidence:legacy-class",),
            ),
        ),
        inferences=(),
    )
    result = knowledge.admit_and_publish(
        scope_id=scope.scope_id,
        expected_scope_revision=Revision(1),
        expected_current_snapshot_id=None,
        idempotency_key=IdempotencyKey("iteration-003-legacy-publication"),
        bundle=bundle,
        caller_ref="iteration-003-fixture-generator",
        classification="PUBLIC",
    )
    if result.snapshot is None:
        raise RuntimeError(f"legacy fixture publication failed: {result.findings}")
    records, next_cursor = knowledge.query_snapshot(
        snapshot_id=result.snapshot.snapshot_id,
        kinds=(KnowledgeObjectKind.ENTITY, KnowledgeObjectKind.FACT),
        limit=50,
    )
    if next_cursor is not None:
        raise RuntimeError("legacy fixture unexpectedly required pagination")
    record_report = [
        {
            "kind": record.kind.value,
            "object_id": record.object_id.value,
            "object_digest": record.object_digest.value,
            "type_name": record.type_name,
            "text": record.text,
            "context_digest": record.context_digest.value,
            "support_references": [item.value for item in record.support_references],
            "source_locators": list(
                knowledge.source_locators(result.snapshot.snapshot_id, record.object_id)
            ),
        }
        for record in sorted(records, key=lambda item: (item.kind.value, item.object_id.value))
    ]
    snapshot = result.snapshot
    database.close()
    for path in sidecar_paths:
        if path.exists() and path.name.endswith("-wal") and path.stat().st_size:
            raise RuntimeError("legacy database closed with an uncheckpointed WAL")
        if path.exists():
            path.unlink()

    report: dict[str, object] = {
        "fixture_ref": "ITER-002-LEGACY-SNAPSHOT@1",
        "generation_commit": generation_commit,
        "database_file": database_path.name,
        "database_sha256": hashlib.sha256(database_path.read_bytes()).hexdigest(),
        "scope_id": scope.scope_id.value,
        "snapshot_id": snapshot.snapshot_id.value,
        "snapshot_revision": snapshot.snapshot_revision.value,
        "schema_version": snapshot.schema_version,
        "manifest_digest": snapshot.manifest_digest.value,
        "member_count": len(snapshot.members),
        "records": record_report,
    }
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument("--generation-commit", required=True)
    args = parser.parse_args()
    report = generate(args.output_directory, args.generation_commit)
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
