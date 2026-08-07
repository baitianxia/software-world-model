from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import unittest

from software_world_model.application_services import (
    JointConstraint,
    KnowledgeNeed,
    KnowledgeRequirement,
    KnowledgeUseService,
    NeedSufficiencyDecision,
    NeedStatus,
    RequirementFidelity,
    TaskBoundary,
)
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
    SqliteKnowledgeUseRepository,
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


class StepClock:
    def __init__(self) -> None:
        self.value = datetime(2026, 8, 6, tzinfo=timezone.utc)

    def __call__(self) -> datetime:
        current = self.value
        self.value += timedelta(microseconds=1)
        return current


class RecordingSemanticEvaluator:
    semantic_zero_match_fallback_enabled = True

    def __init__(self) -> None:
        self.records_by_need = {}

    def evaluate(self, *, requirement, need, read_set):
        del requirement
        self.records_by_need[need.need_id] = tuple(
            item.text for item in read_set.records
        )
        return NeedSufficiencyDecision(
            status=NeedStatus.GAP,
            gap="The recording evaluator does not assert semantic support.",
        )


class KnowledgeUseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.database = SqliteDatabase()
        self.clock = StepClock()
        self.scopes = KnowledgeScopeService(
            SqliteKnowledgeScopeRepository(self.database), clock=self.clock
        )
        self.scope = self.scopes.create_scope(
            scope_type=ScopeType.SYSTEM,
            metadata={"display_name": "Use"},
            idempotency_key=IdempotencyKey("scope"),
            actor="test",
            reason="knowledge use",
            correlation_ref=CorrelationRef("knowledge-use"),
        )
        self.knowledge = FormalKnowledgeService(
            SqliteFormalKnowledgeRepository(self.database), self.scopes, clock=self.clock
        )
        first = self._publish("OrderService", 1, None)
        self.first_snapshot = first.snapshot
        self.use = KnowledgeUseService(
            SqliteKnowledgeUseRepository(self.database), self.knowledge, clock=self.clock
        )
        self.boundary = TaskBoundary.create(
            task_id=StableId("task_00000000000000000000000000000001"),
            task_revision=Revision(1),
            scope_id=self.scope.scope_id,
            purpose="answer software question",
            classification="INTERNAL",
        )
        self.requirement = KnowledgeRequirement.create(
            requirement_id=StableId("requirement_00000000000000000000000000000001"),
            revision=Revision(1),
            fidelity=RequirementFidelity.ORIGINAL,
            original_request="Which services are declared?",
            needs=(
                KnowledgeNeed(
                    need_id="need:order",
                    question="Is OrderService declared?",
                    required_kinds=(KnowledgeObjectKind.FACT,),
                    required_type_names=("DECLARES",),
                    required_terms=("OrderService",),
                    minimum_support_count=1,
                ),
                KnowledgeNeed(
                    need_id="need:payment",
                    question="Is PaymentService declared?",
                    required_kinds=(KnowledgeObjectKind.FACT,),
                    required_type_names=("DECLARES",),
                    required_terms=("PaymentService",),
                    minimum_support_count=1,
                ),
            ),
            joint_constraints=(
                JointConstraint(
                    constraint_id="joint:both",
                    need_ids=("need:order", "need:payment"),
                    description="both requested services must be supported",
                ),
            ),
        )

    def tearDown(self) -> None:
        self.database.close()

    def _artifact(self, name: str, index: int) -> SourceArtifact:
        payload = f"public class {name} {{}}".encode("utf-8")
        return SourceArtifact(
            artifact_id=StableId(f"source_artifact_{index:032x}"),
            artifact_kind="LOCAL_GIT_FILE@1",
            payload_schema_version="1",
            source_id=StableId("source_00000000000000000000000000000001"),
            source_revision=Revision(1),
            source_context_id=StableId(f"source_context_{index:032x}"),
            source_native_identity=f"src/{name}.java",
            content_digest=Digest(f"sha256:{hashlib.sha256(payload).hexdigest()}"),
            payload=payload,
            classification="INTERNAL",
            truncated=False,
            truncation_offset=None,
            identity_digest=digest_of({"artifact": index}),
        )

    def _publish(self, name: str, index: int, expected):
        artifact = self._artifact(name, index)
        context = KnowledgeContext.create({"revision": "a" * 40})
        bundle = KnowledgeCandidateBundle(
            schema_version="INITIAL@1",
            evidence=(EvidenceProposal(f"e:{index}", artifact, 0, len(artifact.payload), f"src/{name}.java:1"),),
            entities=(
                EntityProposal(
                    f"entity:{index}",
                    "CODE_SYMBOL",
                    name,
                    name,
                    context,
                    (f"e:{index}",),
                ),
            ),
            facts=(
                FactProposal(
                    f"fact:{index}",
                    f"entity:{index}",
                    None,
                    "DECLARES",
                    name,
                    context,
                    (f"e:{index}",),
                ),
            ),
            inferences=(),
        )
        return self.knowledge.admit_and_publish(
            scope_id=self.scope.scope_id,
            expected_scope_revision=Revision(1),
            expected_current_snapshot_id=expected,
            idempotency_key=IdempotencyKey(f"publish-{index}"),
            bundle=bundle,
            caller_ref="test",
            classification="INTERNAL",
        )

    def test_each_satisfied_need_has_same_snapshot_rebuildable_proof(self) -> None:
        session = self.use.open_session(
            idempotency_key=IdempotencyKey("session-1"),
            boundary=self.boundary,
            requirement=self.requirement,
            snapshot_id=self.first_snapshot.snapshot_id,
        )
        assessment = self.use.assess(
            idempotency_key=IdempotencyKey("assessment-1"),
            requirement=self.requirement,
            session=session,
        )

        order, payment = assessment.items
        self.assertEqual(order.status, NeedStatus.SATISFIED)
        self.assertEqual(order.proof.snapshot_id, session.snapshot_id)
        self.assertEqual(order.proof.snapshot_manifest_digest, session.snapshot_manifest_digest)
        self.assertTrue(order.proof.supporting_references)
        self.assertEqual(payment.status, NeedStatus.GAP)
        self.assertIsNone(payment.proof)
        self.assertFalse(assessment.sufficient)
        self.assertEqual(assessment.joint_constraint_failures, ("joint:both",))

    def test_semantic_evaluator_receives_bounded_fallback_when_terms_match_nothing(self) -> None:
        evaluator = RecordingSemanticEvaluator()
        use = KnowledgeUseService(
            SqliteKnowledgeUseRepository(self.database),
            self.knowledge,
            evaluator=evaluator,
            clock=self.clock,
        )
        session = use.open_session(
            idempotency_key=IdempotencyKey("semantic-fallback-session"),
            boundary=self.boundary,
            requirement=self.requirement,
            snapshot_id=self.first_snapshot.snapshot_id,
        )

        assessment = use.assess(
            idempotency_key=IdempotencyKey("semantic-fallback-assessment"),
            requirement=self.requirement,
            session=session,
        )

        self.assertEqual(
            evaluator.records_by_need["need:payment"],
            ("OrderService",),
        )
        self.assertEqual(assessment.items[1].status, NeedStatus.GAP)

    def test_semantic_evaluator_receives_complete_small_fact_set_after_partial_term_match(self) -> None:
        second = self._publish(
            "PaymentService", 2, self.first_snapshot.snapshot_id
        )
        evaluator = RecordingSemanticEvaluator()
        use = KnowledgeUseService(
            SqliteKnowledgeUseRepository(self.database),
            self.knowledge,
            evaluator=evaluator,
            clock=self.clock,
        )
        session = use.open_session(
            idempotency_key=IdempotencyKey("semantic-expansion-session"),
            boundary=self.boundary,
            requirement=self.requirement,
            snapshot_id=second.snapshot.snapshot_id,
        )

        use.assess(
            idempotency_key=IdempotencyKey("semantic-expansion-assessment"),
            requirement=self.requirement,
            session=session,
        )

        self.assertEqual(
            set(evaluator.records_by_need["need:order"]),
            {"OrderService", "PaymentService"},
        )

    def test_gap_resolution_rebinds_new_snapshot_and_reevaluates_all_needs(self) -> None:
        old_session = self.use.open_session(
            idempotency_key=IdempotencyKey("old-session"),
            boundary=self.boundary,
            requirement=self.requirement,
            snapshot_id=self.first_snapshot.snapshot_id,
        )
        old = self.use.assess(
            idempotency_key=IdempotencyKey("old-assessment"),
            requirement=self.requirement,
            session=old_session,
        )
        second = self._publish("PaymentService", 2, self.first_snapshot.snapshot_id)
        refreshed = self.use.rebind_and_reassess(
            session_key=IdempotencyKey("new-session"),
            assessment_key=IdempotencyKey("new-assessment"),
            boundary=self.boundary,
            requirement=self.requirement,
            new_snapshot_id=second.snapshot.snapshot_id,
        )
        old_again = self.use.assess(
            idempotency_key=IdempotencyKey("old-assessment-again"),
            requirement=self.requirement,
            session=old_session,
        )

        self.assertFalse(old.sufficient)
        self.assertTrue(refreshed.sufficient)
        self.assertTrue(all(item.proof.snapshot_id == second.snapshot.snapshot_id for item in refreshed.items))
        self.assertFalse(old_again.sufficient)
        self.assertEqual(old_again.snapshot_id, self.first_snapshot.snapshot_id)

    def test_query_cursor_is_bound_to_exact_snapshot_manifest(self) -> None:
        records, next_cursor = self.knowledge.query_snapshot(
            snapshot_id=self.first_snapshot.snapshot_id,
            kinds=(KnowledgeObjectKind.ENTITY, KnowledgeObjectKind.FACT),
            cursor=0,
            limit=1,
        )
        self.assertEqual(len(records), 1)
        self.assertEqual(next_cursor, 1)

    def test_query_terms_expand_candidates_when_any_hint_matches(self) -> None:
        records, next_cursor = self.knowledge.query_snapshot(
            snapshot_id=self.first_snapshot.snapshot_id,
            kinds=(KnowledgeObjectKind.FACT,),
            terms=("OrderService", "提示词并不存在于英文事实中"),
            cursor=0,
            limit=50,
        )

        self.assertEqual(tuple(item.text for item in records), ("OrderService",))
        self.assertIsNone(next_cursor)

        no_match, _ = self.knowledge.query_snapshot(
            snapshot_id=self.first_snapshot.snapshot_id,
            kinds=(KnowledgeObjectKind.FACT,),
            terms=("PaymentService", "另一个不存在的提示词"),
            cursor=0,
            limit=50,
        )
        self.assertEqual(no_match, ())


if __name__ == "__main__":
    unittest.main()
