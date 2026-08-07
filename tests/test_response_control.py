from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
import hashlib
import unittest

from software_world_model.application_services import (
    AdapterDeliveryReceipt,
    AgentCapability,
    AgentCapabilityCatalog,
    AnswerClaim,
    AnswerClaimKind,
    AnswerDraftPlan,
    AnswerDraftSelection,
    ApplicationCallState,
    ConversationalTaskControl,
    DeliveryOutcomePending,
    DeliveryState,
    EffectClass,
    KnowledgeNeed,
    KnowledgeRequirement,
    KnowledgeUseService,
    OrchestratorProposal,
    RequirementFidelity,
    ResponseControlService,
    ReviewDecision,
    ReviewDimension,
    SemanticAnswerReviewDecision,
    TaskBoundary,
    TaskRequestEnvelope,
)
from software_world_model.application_services.response_control import (
    _explicit_gap_text,
)
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
    SqliteKnowledgeUseRepository,
    SqliteResponseControlRepository,
    SqliteTaskControlRepository,
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


class GapDisclosureTests(unittest.TestCase):
    def test_gap_text_names_question_and_explicitly_marks_answer_unavailable(self):
        text = _explicit_gap_text(
            "Why is the scheduled task retained?",
            "The code shows retention but does not establish its cause.",
        )

        self.assertIn("Requested question: Why is the scheduled task retained?", text)
        self.assertIn("Verified answer: unavailable", text)
        self.assertIn("Evidence gap: The code shows retention", text)


class IdempotentAdapter:
    def __init__(self, *, lose_first_response: bool = False) -> None:
        self.lose_first_response = lose_first_response
        self.bodies: dict[str, tuple[Digest, str]] = {}
        self.attempts = 0

    def send(self, *, adapter_idempotency_key: str, body: str, body_digest: Digest):
        self.attempts += 1
        existing = self.bodies.get(adapter_idempotency_key)
        if existing is not None and existing != (body_digest, body):
            raise AssertionError("adapter key reused for another body")
        self.bodies[adapter_idempotency_key] = (body_digest, body)
        if self.lose_first_response and self.attempts == 1:
            raise DeliveryOutcomePending("adapter accepted body but response was lost")
        core = {
            "receipt": f"receipt:{adapter_idempotency_key}",
            "key": adapter_idempotency_key,
            "body_digest": body_digest.value,
            "accepted": True,
        }
        return AdapterDeliveryReceipt(
            adapter_receipt_id=core["receipt"],
            adapter_idempotency_key=adapter_idempotency_key,
            body_digest=body_digest,
            accepted=True,
            provider_reference="test-provider:1",
            digest=digest_of(core),
        )


class OutsideProofAnswerPlanner:
    def plan(self, *, original_request, needs):
        del original_request
        return AnswerDraftPlan(
            (
                AnswerDraftSelection(
                    need_id=needs[0].need_id,
                    formal_references=(
                        StableId("knowledge_fact_ffffffffffffffffffffffffffffffff"),
                    ),
                ),
            )
        )


class RejectSemanticReviewer:
    def review(self, *, task, requirement, candidate, assessment):
        del task, requirement, candidate, assessment
        return SemanticAnswerReviewDecision(
            approved=False,
            failed_dimensions=(ReviewDimension.COMPLETENESS,),
            findings=("The candidate omits a material requested boundary.",),
        )


class ResponseControlTests(unittest.TestCase):
    def setUp(self) -> None:
        self.database = SqliteDatabase()
        self.clock = StepClock()
        self.scopes = KnowledgeScopeService(
            SqliteKnowledgeScopeRepository(self.database), clock=self.clock
        )
        self.scope = self.scopes.create_scope(
            scope_type=ScopeType.SYSTEM,
            metadata={"display_name": "Response"},
            idempotency_key=IdempotencyKey("scope"),
            actor="test",
            reason="response",
            correlation_ref=CorrelationRef("response"),
        )
        self.knowledge = FormalKnowledgeService(
            SqliteFormalKnowledgeRepository(self.database), self.scopes, clock=self.clock
        )
        admission = self._publish()
        self.snapshot = admission.snapshot
        self.use = KnowledgeUseService(
            SqliteKnowledgeUseRepository(self.database), self.knowledge, clock=self.clock
        )
        self.task_repository = SqliteTaskControlRepository(self.database)
        self.tasks = ConversationalTaskControl(self.task_repository, clock=self.clock)
        self.response = ResponseControlService(
            SqliteResponseControlRepository(self.database), self.tasks, self.knowledge, clock=self.clock
        )
        self.catalog = AgentCapabilityCatalog.create(
            catalog_id=StableId("agent_catalog_00000000000000000000000000000001"),
            revision=Revision(1),
            capabilities=(
                AgentCapability(
                    capability_id="TASK_EXECUTION@1",
                    contract_version="1",
                    allowed_use_cases=("knowledge.query",),
                    allowed_effect_classes=(EffectClass.QUERY,),
                    production_active=True,
                ),
            ),
        )
        self.requirement = KnowledgeRequirement.create(
            requirement_id=StableId("requirement_00000000000000000000000000000001"),
            revision=Revision(1),
            fidelity=RequirementFidelity.ORIGINAL,
            original_request="What is declared?",
            needs=(
                KnowledgeNeed(
                    need_id="need:declaration",
                    question="What is declared?",
                    required_kinds=(KnowledgeObjectKind.FACT,),
                    required_type_names=("DECLARES",),
                    required_terms=("OrderService",),
                    minimum_support_count=1,
                ),
            ),
        )

    def tearDown(self) -> None:
        self.database.close()

    def _publish(self):
        payload = b"public class OrderService {}"
        artifact = SourceArtifact(
            artifact_id=StableId("source_artifact_00000000000000000000000000000001"),
            artifact_kind="LOCAL_GIT_FILE@1",
            payload_schema_version="1",
            source_id=StableId("source_00000000000000000000000000000001"),
            source_revision=Revision(1),
            source_context_id=StableId("source_context_00000000000000000000000000000001"),
            source_native_identity="src/OrderService.java",
            content_digest=Digest(f"sha256:{hashlib.sha256(payload).hexdigest()}"),
            payload=payload,
            classification="INTERNAL",
            truncated=False,
            truncation_offset=None,
            identity_digest=digest_of({"artifact": 1}),
        )
        context = KnowledgeContext.create({"revision": "a" * 40})
        bundle = KnowledgeCandidateBundle(
            schema_version="INITIAL@1",
            evidence=(EvidenceProposal("e:1", artifact, 0, len(payload), "file:1"),),
            entities=(EntityProposal("entity:1", "CODE_SYMBOL", "OrderService", "OrderService", context, ("e:1",)),),
            facts=(FactProposal("fact:1", "entity:1", None, "DECLARES", "OrderService", context, ("e:1",)),),
            inferences=(),
        )
        return self.knowledge.admit_and_publish(
            scope_id=self.scope.scope_id,
            expected_scope_revision=Revision(1),
            expected_current_snapshot_id=None,
            idempotency_key=IdempotencyKey("publish"),
            bundle=bundle,
            caller_ref="test",
            classification="INTERNAL",
        )

    def _task_and_assessment(self, suffix: str):
        envelope = TaskRequestEnvelope.create(
            conversation_ref=f"conversation:{suffix}",
            turn_ref="turn:1",
            request_ref="request:1",
            idempotency_key=IdempotencyKey(f"task:{suffix}"),
            original_request="What is declared?",
            caller_ref="user:test",
            classification="INTERNAL",
            scope_id=self.scope.scope_id,
        )
        task = self.tasks.create_task(envelope, self.catalog)
        proposal = OrchestratorProposal.create(
            task_kind="KNOWLEDGE_QUERY",
            capability_id="TASK_EXECUTION@1",
            target_scope_id=self.scope.scope_id,
            response_kind="KNOWLEDGE_COMPLETE",
        )
        task = self.tasks.accept_orchestrator_proposal(
            task_id=task.task_id,
            expected_revision=task.revision,
            proposal=proposal,
            catalog=self.catalog,
        )
        invocation = self.tasks.create_invocation(
            task_id=task.task_id,
            input_digest=envelope.digest,
            catalog=self.catalog,
        )
        task = self.tasks.get_task(task.task_id)
        boundary = TaskBoundary.create(
            task_id=task.task_id,
            task_revision=task.revision,
            scope_id=self.scope.scope_id,
            purpose="answer",
            classification="INTERNAL",
        )
        session = self.use.open_session(
            idempotency_key=IdempotencyKey(f"session:{suffix}"),
            boundary=boundary,
            requirement=self.requirement,
            snapshot_id=self.snapshot.snapshot_id,
        )
        assessment = self.use.assess(
            idempotency_key=IdempotencyKey(f"assessment:{suffix}"),
            requirement=self.requirement,
            session=session,
        )
        return task, invocation, assessment

    def _claim(self, assessment, *, text: str = "OrderService"):
        item = assessment.items[0]
        reference = item.proof.supporting_references[0]
        digest = item.proof.supporting_digests[0]
        return AnswerClaim(
            claim_id="claim:1",
            need_id="need:declaration",
            kind=AnswerClaimKind.FORMAL_KNOWLEDGE,
            text=text,
            formal_reference=reference,
            formal_digest=digest,
            support_proof_id=item.proof.proof_id,
            gap=None,
        )

    def test_delegated_grant_blocks_unapproved_command(self) -> None:
        task, invocation, _ = self._task_and_assessment("grant")
        query_call = self.tasks.prepare_application_call(
            invocation=invocation,
            logical_occurrence="query:1",
            use_case="knowledge.query",
            effect_class=EffectClass.QUERY,
            request_digest=digest_of({"query": 1}),
        )
        dispatched = self.tasks.transition_application_call(
            call_id=query_call.call_id,
            expected_revision=query_call.revision,
            target=ApplicationCallState.DISPATCHED,
        )
        completed = self.tasks.transition_application_call(
            call_id=dispatched.call_id,
            expected_revision=dispatched.revision,
            target=ApplicationCallState.SUCCEEDED,
            result_reference="query-result:1",
            result_digest=digest_of({"result": 1}),
        )
        self.assertEqual(completed.state, ApplicationCallState.SUCCEEDED)
        with self.assertRaises(DomainError) as raised:
            self.tasks.prepare_application_call(
                invocation=invocation,
                logical_occurrence="command:1",
                use_case="knowledge.update",
                effect_class=EffectClass.COMMAND,
                request_digest=digest_of({"command": 1}),
            )
        self.assertEqual(raised.exception.code, ErrorCode.CONTROL_STATE_DENIED)

    def test_approved_candidate_delivers_one_immutable_body(self) -> None:
        task, _, assessment = self._task_and_assessment("delivery")
        claim = self._claim(assessment)
        candidate, task = self.response.seal_candidate(
            task=task,
            requirement=self.requirement,
            assessment=assessment,
            claims=(claim,),
            body=claim.text,
        )
        review = self.response.review(task=task, candidate=candidate, assessment=assessment)
        authorization = self.response.authorize(task=task, candidate=candidate, review=review)
        adapter = IdempotentAdapter()
        first = self.response.deliver(
            task=task, candidate=candidate, authorization=authorization, adapter=adapter
        )
        replay = self.response.deliver(
            task=task, candidate=candidate, authorization=authorization, adapter=adapter
        )

        self.assertEqual(review.decision, ReviewDecision.APPROVED)
        self.assertEqual(first.state, DeliveryState.DELIVERED)
        self.assertEqual(replay.delivery_id, first.delivery_id)
        self.assertEqual(adapter.attempts, 1)
        self.assertEqual(len(adapter.bodies), 1)

    def test_draft_plan_is_reconstructed_as_exact_formal_claims(self) -> None:
        task, _, assessment = self._task_and_assessment("draft")

        candidate, task = self.response.draft_and_seal_candidate(
            task=task,
            requirement=self.requirement,
            assessment=assessment,
        )
        review = self.response.review(
            task=task, candidate=candidate, assessment=assessment
        )

        self.assertEqual(candidate.body, "OrderService")
        self.assertEqual(candidate.claims[0].formal_reference, assessment.items[0].proof.supporting_references[0])
        self.assertEqual(review.decision, ReviewDecision.APPROVED)

    def test_duplicate_supported_claim_text_is_rendered_once(self) -> None:
        task, _, assessment = self._task_and_assessment("deduplicated-body")
        first = self._claim(assessment)
        second = replace(first, claim_id="claim:2")

        candidate, task = self.response.seal_candidate(
            task=task,
            requirement=self.requirement,
            assessment=assessment,
            claims=(first, second),
            body=first.text,
        )
        review = self.response.review(
            task=task, candidate=candidate, assessment=assessment
        )

        self.assertEqual(candidate.body, "OrderService")
        self.assertEqual(len(candidate.claims), 2)
        self.assertEqual(
            candidate.coverage[0].claim_ids,
            ("claim:1", "claim:2"),
        )
        self.assertEqual(review.decision, ReviewDecision.APPROVED)

    def test_answer_stages_recover_existing_candidate_review_and_authorization(self) -> None:
        task, _, assessment = self._task_and_assessment("answer-recovery")
        first_candidate, task = self.response.draft_and_seal_candidate(
            task=task,
            requirement=self.requirement,
            assessment=assessment,
        )
        first_review = self.response.review(
            task=task,
            requirement=self.requirement,
            candidate=first_candidate,
            assessment=assessment,
        )
        first_authorization = self.response.authorize(
            task=task,
            candidate=first_candidate,
            review=first_review,
        )

        replay_candidate, replay_task = self.response.draft_and_seal_candidate(
            task=task,
            requirement=self.requirement,
            assessment=assessment,
        )
        replay_review = self.response.review(
            task=replay_task,
            requirement=self.requirement,
            candidate=replay_candidate,
            assessment=assessment,
        )
        replay_authorization = self.response.authorize(
            task=replay_task,
            candidate=replay_candidate,
            review=replay_review,
        )

        self.assertEqual(replay_candidate, first_candidate)
        self.assertEqual(replay_review, first_review)
        self.assertEqual(replay_authorization, first_authorization)

    def test_draft_plan_cannot_select_knowledge_outside_need_proof(self) -> None:
        task, _, assessment = self._task_and_assessment("outside-draft")

        with self.assertRaises(DomainError) as raised:
            self.response.draft_and_seal_candidate(
                task=task,
                requirement=self.requirement,
                assessment=assessment,
                planner=OutsideProofAnswerPlanner(),
            )

        self.assertEqual(raised.exception.code, ErrorCode.CONTROL_STATE_DENIED)

    def test_semantic_review_failure_overrides_mechanical_claim_pass(self) -> None:
        task, _, assessment = self._task_and_assessment("semantic-review")
        candidate, task = self.response.draft_and_seal_candidate(
            task=task,
            requirement=self.requirement,
            assessment=assessment,
        )
        response = ResponseControlService(
            SqliteResponseControlRepository(self.database),
            self.tasks,
            self.knowledge,
            semantic_reviewer=RejectSemanticReviewer(),
            clock=self.clock,
        )

        review = response.review(
            task=task,
            requirement=self.requirement,
            candidate=candidate,
            assessment=assessment,
        )

        self.assertEqual(review.decision, ReviewDecision.REVISION_REQUIRED)
        self.assertTrue(
            any(
                cell.dimension is ReviewDimension.COMPLETENESS
                and cell.outcome.value == "FAIL"
                for cell in review.matrix
            )
        )

    def test_review_rejects_text_that_adds_unentailed_uniqueness(self) -> None:
        task, _, assessment = self._task_and_assessment("review")
        claim = self._claim(assessment, text="OrderService is the only declared service")
        candidate, task = self.response.seal_candidate(
            task=task,
            requirement=self.requirement,
            assessment=assessment,
            claims=(claim,),
            body=claim.text,
        )
        review = self.response.review(task=task, candidate=candidate, assessment=assessment)

        self.assertEqual(review.decision, ReviewDecision.REVISION_REQUIRED)
        with self.assertRaises(DomainError):
            self.response.authorize(task=task, candidate=candidate, review=review)

    def test_lost_adapter_response_recovers_same_delivery_key_without_second_body(self) -> None:
        task, _, assessment = self._task_and_assessment("pending")
        claim = self._claim(assessment)
        candidate, task = self.response.seal_candidate(
            task=task,
            requirement=self.requirement,
            assessment=assessment,
            claims=(claim,),
            body=claim.text,
        )
        review = self.response.review(task=task, candidate=candidate, assessment=assessment)
        authorization = self.response.authorize(task=task, candidate=candidate, review=review)
        adapter = IdempotentAdapter(lose_first_response=True)

        pending = self.response.deliver(
            task=task, candidate=candidate, authorization=authorization, adapter=adapter
        )
        recovered = self.response.deliver(
            task=task, candidate=candidate, authorization=authorization, adapter=adapter
        )

        self.assertEqual(pending.state, DeliveryState.OUTCOME_PENDING)
        self.assertEqual(recovered.state, DeliveryState.DELIVERED)
        self.assertEqual(pending.adapter_idempotency_key, recovered.adapter_idempotency_key)
        self.assertEqual(len(adapter.bodies), 1)

    def test_task_revision_change_rejects_stale_authorization_delivery(self) -> None:
        task, _, assessment = self._task_and_assessment("stale")
        claim = self._claim(assessment)
        candidate, task = self.response.seal_candidate(
            task=task,
            requirement=self.requirement,
            assessment=assessment,
            claims=(claim,),
            body=claim.text,
        )
        review = self.response.review(task=task, candidate=candidate, assessment=assessment)
        authorization = self.response.authorize(task=task, candidate=candidate, review=review)
        self.tasks.bind_candidate(
            task_id=task.task_id,
            expected_revision=task.revision,
            candidate_id=candidate.candidate_id,
        )

        with self.assertRaises(DomainError) as raised:
            self.response.deliver(
                task=task,
                candidate=candidate,
                authorization=authorization,
                adapter=IdempotentAdapter(),
            )
        self.assertEqual(raised.exception.code, ErrorCode.CONTROL_STATE_DENIED)

    def test_cancel_is_idempotent_only_before_adapter_dispatch(self) -> None:
        task, _, assessment = self._task_and_assessment("cancel")
        claim = self._claim(assessment)
        candidate, task = self.response.seal_candidate(
            task=task,
            requirement=self.requirement,
            assessment=assessment,
            claims=(claim,),
            body=claim.text,
        )
        review = self.response.review(task=task, candidate=candidate, assessment=assessment)
        authorization = self.response.authorize(task=task, candidate=candidate, review=review)

        canceled = self.response.cancel_before_dispatch(
            task=task,
            candidate=candidate,
            authorization=authorization,
            reason="caller withdrew request",
        )
        replay = self.response.cancel_before_dispatch(
            task=task,
            candidate=candidate,
            authorization=authorization,
            reason="caller withdrew request",
        )

        self.assertEqual(canceled.state, DeliveryState.CANCELED_BEFORE_DISPATCH)
        self.assertEqual(replay.delivery_id, canceled.delivery_id)
        with self.assertRaises(DomainError) as raised:
            self.response.deliver(
                task=task,
                candidate=candidate,
                authorization=authorization,
                adapter=IdempotentAdapter(),
            )
        self.assertEqual(raised.exception.code, ErrorCode.MANAGEMENT_STATE_CONFLICT)


if __name__ == "__main__":
    unittest.main()
