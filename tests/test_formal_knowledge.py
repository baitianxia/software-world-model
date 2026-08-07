from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
import hashlib
import unittest

from software_world_model.cross_cutting import (
    CorrelationRef,
    Digest,
    DomainError,
    ErrorCode,
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
    AdmissionStatus,
    EntityProposal,
    EvidenceProposal,
    FactProposal,
    FormalKnowledgeService,
    InferenceProposal,
    KnowledgeCandidateBundle,
    KnowledgeContext,
    KnowledgeObjectKind,
    KnowledgeScopeService,
    ReviewedFactGrounding,
    ScopeType,
)
from software_world_model.source_integration import SourceArtifact


class StepClock:
    def __init__(self) -> None:
        self.value = datetime(2026, 8, 6, tzinfo=timezone.utc)

    def __call__(self) -> datetime:
        current = self.value
        self.value += timedelta(microseconds=1)
        return current


class GroundingVerifier:
    def __init__(self, accepted: bool = True) -> None:
        self.accepted = accepted
        self.proposals = []

    def verify(self, *, proposal, subject_proposal, evidence_proposals):
        self.proposals.append((proposal, subject_proposal, evidence_proposals))
        return self.accepted


class FormalKnowledgeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.database = SqliteDatabase()
        self.clock = StepClock()
        self.scopes = KnowledgeScopeService(
            SqliteKnowledgeScopeRepository(self.database), clock=self.clock
        )
        self.scope = self.scopes.create_scope(
            scope_type=ScopeType.SYSTEM,
            metadata={"display_name": "Mall"},
            idempotency_key=IdempotencyKey("scope"),
            actor="test",
            reason="formal knowledge",
            correlation_ref=CorrelationRef("formal-knowledge"),
        )
        self.repository = SqliteFormalKnowledgeRepository(self.database)
        self.knowledge = FormalKnowledgeService(
            self.repository, self.scopes, clock=self.clock
        )
        self.context = KnowledgeContext.create(
            {"repository_revision": "a" * 40, "environment": "source"}
        )

    def tearDown(self) -> None:
        self.database.close()

    def artifact(self, text: str = "public class OrderService {}") -> SourceArtifact:
        payload = text.encode("utf-8")
        content = Digest(f"sha256:{hashlib.sha256(payload).hexdigest()}")
        return SourceArtifact(
            artifact_id=StableId("source_artifact_00000000000000000000000000000001"),
            artifact_kind="LOCAL_GIT_FILE@1",
            payload_schema_version="1",
            source_id=StableId("source_00000000000000000000000000000001"),
            source_revision=Revision(1),
            source_context_id=StableId("source_context_00000000000000000000000000000001"),
            source_native_identity="src/OrderService.java",
            content_digest=content,
            payload=payload,
            classification="INTERNAL",
            truncated=False,
            truncation_offset=None,
            identity_digest=digest_of({"artifact": 1}),
        )

    def bundle(self, *, artifact: SourceArtifact | None = None, natural_key: str = "OrderService"):
        artifact = artifact or self.artifact()
        return KnowledgeCandidateBundle(
            schema_version="INITIAL@1",
            evidence=(
                EvidenceProposal(
                    evidence_key="evidence:class",
                    artifact=artifact,
                    byte_start=0,
                    byte_end=len(artifact.payload),
                    locator="src/OrderService.java:1",
                ),
            ),
            entities=(
                EntityProposal(
                    candidate_key="entity:service",
                    entity_type="CODE_SYMBOL",
                    natural_key=natural_key,
                    label=natural_key,
                    context=self.context,
                    evidence_keys=("evidence:class",),
                ),
            ),
            facts=(
                FactProposal(
                    candidate_key="fact:declares",
                    subject_candidate_key="entity:service",
                    subject_entity_id=None,
                    predicate="DECLARES",
                    object_value="OrderService",
                    context=self.context,
                    evidence_keys=("evidence:class",),
                ),
            ),
            inferences=(),
        )

    def publish(self, bundle, *, key: str, expected=None):
        return self.knowledge.admit_and_publish(
            scope_id=self.scope.scope_id,
            expected_scope_revision=Revision(1),
            expected_current_snapshot_id=expected,
            idempotency_key=IdempotencyKey(key),
            bundle=bundle,
            caller_ref="test",
            classification="INTERNAL",
        )

    def test_valid_batch_publishes_atomically_and_replays_same_admission(self) -> None:
        first = self.publish(self.bundle(), key="publish-1")
        replay = self.publish(self.bundle(), key="publish-1")

        self.assertEqual(first.status, AdmissionStatus.ADMITTED)
        self.assertEqual(replay.admission_id, first.admission_id)
        self.assertEqual(replay.snapshot.snapshot_id, first.snapshot.snapshot_id)
        self.assertEqual(len(first.snapshot.members), 2)
        self.assertEqual(
            self.knowledge.current_snapshot(self.scope.scope_id).snapshot_id,
            first.snapshot.snapshot_id,
        )
        fact_id = next(
            member.object_id
            for member in first.snapshot.members
            if member.kind is KnowledgeObjectKind.FACT
        )
        self.assertEqual(
            self.knowledge.source_locators(first.snapshot.snapshot_id, fact_id),
            ("src/OrderService.java:1",),
        )

    def test_same_semantic_fact_from_a_new_source_context_does_not_collide(self) -> None:
        first = self.publish(self.bundle(), key="publish-first-source")
        original = self.artifact()
        second_artifact = replace(
            original,
            artifact_id=StableId(
                "source_artifact_00000000000000000000000000000002"
            ),
            source_context_id=StableId(
                "source_context_00000000000000000000000000000002"
            ),
            identity_digest=digest_of({"artifact": 2}),
        )

        second = self.publish(
            self.bundle(artifact=second_artifact),
            key="publish-second-source",
            expected=first.snapshot.snapshot_id,
        )

        self.assertEqual(second.status, AdmissionStatus.ADMITTED)
        first_fact_ids = {
            member.object_id
            for member in first.snapshot.members
            if member.kind is KnowledgeObjectKind.FACT
        }
        second_fact_ids = {
            member.object_id
            for member in second.snapshot.members
            if member.kind is KnowledgeObjectKind.FACT
        }
        self.assertTrue(first_fact_ids < second_fact_ids)

    def test_evidence_out_of_range_rejects_batch_without_current_pollution(self) -> None:
        artifact = self.artifact()
        invalid = self.bundle(artifact=artifact)
        invalid = KnowledgeCandidateBundle(
            schema_version=invalid.schema_version,
            evidence=(
                EvidenceProposal(
                    evidence_key="evidence:class",
                    artifact=artifact,
                    byte_start=0,
                    byte_end=len(artifact.payload) + 1,
                    locator="invalid",
                ),
            ),
            entities=invalid.entities,
            facts=invalid.facts,
            inferences=(),
        )
        result = self.publish(invalid, key="invalid-range")

        self.assertEqual(result.status, AdmissionStatus.REJECTED)
        self.assertIn("EVIDENCE_RANGE_INVALID", {item.code for item in result.findings})
        self.assertIsNone(self.knowledge.current_snapshot(self.scope.scope_id))

    def test_fact_cannot_extend_beyond_exact_evidence(self) -> None:
        bundle = self.bundle()
        invalid = KnowledgeCandidateBundle(
            schema_version=bundle.schema_version,
            evidence=bundle.evidence,
            entities=bundle.entities,
            facts=(
                FactProposal(
                    candidate_key="fact:unsupported",
                    subject_candidate_key="entity:service",
                    subject_entity_id=None,
                    predicate="DECLARES",
                    object_value="PaymentService",
                    context=self.context,
                    evidence_keys=("evidence:class",),
                ),
            ),
            inferences=(),
        )
        result = self.publish(invalid, key="outside-evidence")

        self.assertEqual(result.status, AdmissionStatus.REJECTED)
        self.assertIn("FACT_OUTSIDE_EVIDENCE", {item.code for item in result.findings})
        self.assertIsNone(self.knowledge.current_snapshot(self.scope.scope_id))

    def test_reviewed_semantic_fact_requires_valid_grounding_and_is_persisted(self) -> None:
        bundle = self.bundle()
        grounding = ReviewedFactGrounding.create(
            candidate_key="semantic",
            proposer_model_call_id=StableId(
                "model_call_00000000000000000000000000000001"
            ),
            proposer_output_digest=digest_of("proposal"),
            reviewer_model_call_id=StableId(
                "model_call_00000000000000000000000000000002"
            ),
            reviewer_output_digest=digest_of("review"),
            actual_model_fingerprint="model@1",
        )
        semantic = KnowledgeCandidateBundle(
            schema_version=bundle.schema_version,
            evidence=bundle.evidence,
            entities=bundle.entities,
            facts=(
                FactProposal(
                    candidate_key="fact:semantic",
                    subject_candidate_key="entity:service",
                    subject_entity_id=None,
                    predicate="DECLARES",
                    object_value="OrderService is declared by this source file.",
                    context=self.context,
                    evidence_keys=("evidence:class",),
                    reviewed_grounding=grounding,
                ),
            ),
            inferences=(),
        )
        verifier = GroundingVerifier()
        self.knowledge = FormalKnowledgeService(
            self.repository,
            self.scopes,
            reviewed_fact_verifier=verifier,
            clock=self.clock,
        )

        result = self.publish(semantic, key="reviewed-semantic")

        self.assertEqual(result.status, AdmissionStatus.ADMITTED)
        self.assertEqual(len(verifier.proposals), 1)
        with self.database.read() as connection:
            row = connection.execute(
                "SELECT reviewed_grounding_json FROM knw_facts"
            ).fetchone()
        self.assertIn(grounding.digest.value, row["reviewed_grounding_json"])

        tampered = replace(grounding, candidate_key="changed")
        tampered_bundle = replace(
            semantic,
            facts=(replace(semantic.facts[0], reviewed_grounding=tampered),),
        )
        rejected = self.publish(
            tampered_bundle,
            key="reviewed-semantic-tampered",
            expected=result.snapshot.snapshot_id,
        )
        self.assertEqual(rejected.status, AdmissionStatus.REJECTED)
        self.assertIn(
            "FACT_REVIEW_GROUNDING_INVALID",
            {item.code for item in rejected.findings},
        )

    def test_inference_requires_premises_from_base_snapshot(self) -> None:
        first = self.publish(self.bundle(), key="base")
        fake_premise = StableId("knowledge_fact_ffffffffffffffffffffffffffffffff")
        invalid_bundle = KnowledgeCandidateBundle(
            schema_version="INITIAL@1",
            evidence=(),
            entities=(),
            facts=(),
            inferences=(
                InferenceProposal(
                    candidate_key="inference:bad",
                    inference_type="STRUCTURE",
                    proposition="The service is public.",
                    premise_references=(fake_premise,),
                    rule_ref="deterministic-rule@1",
                    context=self.context,
                ),
            ),
        )
        rejected = self.publish(
            invalid_bundle, key="bad-inference", expected=first.snapshot.snapshot_id
        )
        valid_bundle = KnowledgeCandidateBundle(
            schema_version="INITIAL@1",
            evidence=(),
            entities=(),
            facts=(),
            inferences=(
                InferenceProposal(
                    candidate_key="inference:good",
                    inference_type="STRUCTURE",
                    proposition="OrderService is declared in the source revision.",
                    premise_references=(first.fact_references[0],),
                    rule_ref="deterministic-rule@1",
                    context=self.context,
                ),
            ),
        )
        admitted = self.publish(
            valid_bundle, key="good-inference", expected=first.snapshot.snapshot_id
        )

        self.assertEqual(rejected.status, AdmissionStatus.REJECTED)
        self.assertEqual(
            self.knowledge.current_snapshot(self.scope.scope_id).snapshot_id,
            admitted.snapshot.snapshot_id,
        )
        self.assertEqual(admitted.status, AdmissionStatus.ADMITTED)

    def test_old_snapshot_remains_exact_after_new_publication(self) -> None:
        first = self.publish(self.bundle(), key="snapshot-1")
        inference_bundle = KnowledgeCandidateBundle(
            schema_version="INITIAL@1",
            evidence=(),
            entities=(),
            facts=(),
            inferences=(
                InferenceProposal(
                    candidate_key="inference:structure",
                    inference_type="STRUCTURE",
                    proposition="OrderService exists.",
                    premise_references=(first.fact_references[0],),
                    rule_ref="direct-entailment@1",
                    context=self.context,
                ),
            ),
        )
        second = self.publish(
            inference_bundle, key="snapshot-2", expected=first.snapshot.snapshot_id
        )
        reloaded_first = self.knowledge.get_snapshot(first.snapshot.snapshot_id)

        self.assertEqual(len(reloaded_first.members), 2)
        self.assertEqual(len(second.snapshot.members), 3)
        self.assertEqual(second.snapshot.previous_snapshot_id, first.snapshot.snapshot_id)

    def test_stale_current_pointer_fails_without_replacing_current(self) -> None:
        first = self.publish(self.bundle(), key="first")
        with self.assertRaises(DomainError) as raised:
            self.publish(self.bundle(natural_key="Other"), key="stale", expected=None)
        self.assertEqual(raised.exception.code, ErrorCode.REVISION_CONFLICT)
        self.assertEqual(
            self.knowledge.current_snapshot(self.scope.scope_id).snapshot_id,
            first.snapshot.snapshot_id,
        )


if __name__ == "__main__":
    unittest.main()
