from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
import hashlib
from io import BytesIO
import json
import unittest

from software_world_model.application_services import (
    CapabilityDefinition,
    CapabilityRegistry,
    BuildObjective,
    CanonicalBuildTarget,
    ConversationalTaskControl,
    CoverageObligation,
    DeterministicAnswerDraftPlanner,
    KnowledgeNeed,
    KnowledgeRequirementPlan,
    KnowledgeUpdateRequest,
    KnowledgeUpdateResult,
    KnowledgeUseService,
    LiveIntegrationPolicy,
    InvestigationStopReason,
    NATURAL_TASK_CAPABILITY_CONTRACT_VERSION,
    NATURAL_TASK_CAPABILITY_ID,
    NaturalLanguageTaskRequest,
    NaturalLanguageTaskService,
    QualificationProof,
    ResponseControlService,
    ReviewDecision,
    StrategyActivationService,
    StrategyDefinition,
    StrategyKind,
    UpdateAttemptState,
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
    SqliteStrategyActivationRepository,
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
from software_world_model.source_integration import TargetKind
from software_world_model.interface.http_api import JsonHttpApplication
from software_world_model.interface.runtime import ApplicationRuntime


FIXTURE_IMPLEMENTATION_DIGEST = digest_of({"implementation": "test@1"})
FIXTURE_QUALIFICATION_REF = "evaluation-proof:natural-task:1"


class StepClock:
    def __init__(self) -> None:
        self.value = datetime(2026, 8, 7, tzinfo=timezone.utc)

    def __call__(self) -> datetime:
        current = self.value
        self.value += timedelta(microseconds=1)
        return current


class CurrentEvaluationVerifier:
    def validate(self, proof: QualificationProof) -> bool:
        return proof.qualification_kind == "CAPABILITY_EVALUATION"


class MutableRequirementPlanner:
    def __init__(self) -> None:
        self.required_terms = ("OrderService",)
        self.strategy_implementation_digest = FIXTURE_IMPLEMENTATION_DIGEST
        self.qualification_ref = FIXTURE_QUALIFICATION_REF
        self.classification = "INTERNAL"

    def plan(self, *, original_request: str) -> KnowledgeRequirementPlan:
        return KnowledgeRequirementPlan(
            needs=(
                KnowledgeNeed(
                    need_id="need:declaration",
                    question=original_request,
                    required_kinds=(KnowledgeObjectKind.FACT,),
                    required_type_names=("DECLARES",),
                    required_terms=self.required_terms,
                    minimum_support_count=1,
                ),
            )
        )


class FixtureAnswerPlanner(DeterministicAnswerDraftPlanner):
    strategy_implementation_digest = FIXTURE_IMPLEMENTATION_DIGEST
    qualification_ref = FIXTURE_QUALIFICATION_REF
    classification = "INTERNAL"


class CompletedKnowledgeUpdate:
    strategy_implementation_digest = FIXTURE_IMPLEMENTATION_DIGEST
    strategy_qualification_ref = FIXTURE_QUALIFICATION_REF
    strategy_classification = "INTERNAL"

    def __init__(self, result: KnowledgeUpdateResult) -> None:
        self.result = result
        self.calls = 0
        self.last_request: KnowledgeUpdateRequest | None = None

    def execute(self, request: KnowledgeUpdateRequest) -> KnowledgeUpdateResult:
        self.calls += 1
        self.last_request = request
        base_request = replace(request, requirement_plan=None)
        if (
            request.requirement_plan is None
            or base_request.digest != self.result.request_digest
        ):
            raise AssertionError("unexpected knowledge update request")
        return self.result


def evaluation_proof(strategy: StrategyDefinition) -> QualificationProof:
    core = {
        "proof_ref": FIXTURE_QUALIFICATION_REF,
        "capability_id": NATURAL_TASK_CAPABILITY_ID,
        "capability_contract_version": NATURAL_TASK_CAPABILITY_CONTRACT_VERSION,
        "strategy_id": strategy.strategy_id,
        "strategy_version": strategy.strategy_version,
        "result_ref": "evaluation-result:natural-task:1",
        "validity_ref": "evaluation-validity:natural-task:1",
        "qualification_kind": "CAPABILITY_EVALUATION",
    }
    return QualificationProof(**core, digest=digest_of(core))


class NaturalLanguageTaskTests(unittest.TestCase):
    def setUp(self) -> None:
        self.database = SqliteDatabase()
        self.clock = StepClock()
        self.scopes = KnowledgeScopeService(
            SqliteKnowledgeScopeRepository(self.database), clock=self.clock
        )
        self.scope = self.scopes.create_scope(
            scope_type=ScopeType.SYSTEM,
            metadata={"display_name": "Natural task"},
            idempotency_key=IdempotencyKey("scope:natural-task"),
            actor="test",
            reason="natural task test",
            correlation_ref=CorrelationRef("natural-task-test"),
        )
        self.knowledge = FormalKnowledgeService(
            SqliteFormalKnowledgeRepository(self.database),
            self.scopes,
            clock=self.clock,
        )
        self.snapshot = self._publish()
        self.tasks = ConversationalTaskControl(
            SqliteTaskControlRepository(self.database), clock=self.clock
        )
        self.knowledge_use = KnowledgeUseService(
            SqliteKnowledgeUseRepository(self.database),
            self.knowledge,
            strategy_implementation_digest=FIXTURE_IMPLEMENTATION_DIGEST,
            strategy_qualification_ref=FIXTURE_QUALIFICATION_REF,
            strategy_classification="INTERNAL",
            clock=self.clock,
        )
        self.responses = ResponseControlService(
            SqliteResponseControlRepository(self.database),
            self.tasks,
            self.knowledge,
            strategy_implementation_digest=FIXTURE_IMPLEMENTATION_DIGEST,
            strategy_qualification_ref=FIXTURE_QUALIFICATION_REF,
            strategy_classification="INTERNAL",
            clock=self.clock,
        )
        self.registry = CapabilityRegistry()
        self.registry.register_capability(
            CapabilityDefinition(
                capability_id=NATURAL_TASK_CAPABILITY_ID,
                contract_version=NATURAL_TASK_CAPABILITY_CONTRACT_VERSION,
                purpose="Answer an exact-snapshot software knowledge task",
                input_contract_digest=digest_of({"input": "natural-task@1"}),
                output_contract_digest=digest_of({"output": "authorized-answer@1"}),
            )
        )
        self.strategy = StrategyDefinition(
            strategy_id="reviewed-model-natural-task",
            strategy_version="1.0.0",
            capability_id=NATURAL_TASK_CAPABILITY_ID,
            capability_contract_version=NATURAL_TASK_CAPABILITY_CONTRACT_VERSION,
            kind=StrategyKind.MODEL_PRIMARY,
            implementation_digest=FIXTURE_IMPLEMENTATION_DIGEST,
            requires_model=True,
        )
        self.registry.register_strategy(self.strategy)
        self.activation_scope = {"environment": "test"}
        self.activation = StrategyActivationService(
            SqliteStrategyActivationRepository(self.database),
            self.registry,
            CurrentEvaluationVerifier(),
            live_policy=LiveIntegrationPolicy(model_strategy_activation_enabled=True),
            clock=self.clock,
        )
        self.activation.activate_strategy(
            capability_id=NATURAL_TASK_CAPABILITY_ID,
            capability_contract_version=NATURAL_TASK_CAPABILITY_CONTRACT_VERSION,
            activation_scope=self.activation_scope,
            expected_revision=None,
            strategy_id=self.strategy.strategy_id,
            strategy_version=self.strategy.strategy_version,
            qualification=evaluation_proof(self.strategy),
            idempotency_key=IdempotencyKey("activate:natural-task"),
            actor="test",
            reason="exercise the authorized task path",
            correlation_ref=CorrelationRef("natural-task-test"),
        )
        self.requirements = MutableRequirementPlanner()
        self.service = NaturalLanguageTaskService(
            tasks=self.tasks,
            knowledge=self.knowledge,
            knowledge_use=self.knowledge_use,
            responses=self.responses,
            requirement_planner=self.requirements,
            answer_planner=FixtureAnswerPlanner(),
            activation=self.activation,
            activation_scope=self.activation_scope,
        )

    def tearDown(self) -> None:
        self.database.close()

    def _publish(
        self,
        *,
        name: str = "OrderService",
        index: int = 1,
        expected: StableId | None = None,
    ):
        payload = f"public class {name} {{}}".encode("utf-8")
        artifact = SourceArtifact(
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
        context = KnowledgeContext.create({"revision": "a" * 40})
        bundle = KnowledgeCandidateBundle(
            schema_version="INITIAL@1",
            evidence=(
                EvidenceProposal(
                    f"e:{index}", artifact, 0, len(payload), f"file:{index}"
                ),
            ),
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
            idempotency_key=IdempotencyKey(f"publish:natural-task:{index}"),
            bundle=bundle,
            caller_ref="test",
            classification="INTERNAL",
        ).snapshot

    def _request(self) -> NaturalLanguageTaskRequest:
        return NaturalLanguageTaskRequest.create(
            conversation_ref="conversation:1",
            turn_ref="turn:1",
            request_ref="request:1",
            idempotency_key=IdempotencyKey("task:natural:1"),
            original_request="What does OrderService declare?",
            caller_ref="user:test",
            classification="INTERNAL",
            scope_id=self.scope.scope_id,
            snapshot_id=self.snapshot.snapshot_id,
        )

    @staticmethod
    def _http(application, method: str, path: str, payload: object):
        body = json.dumps(payload).encode("utf-8")
        captured = {}

        def start_response(status, headers):
            captured["status"] = status
            captured["headers"] = dict(headers)

        response = b"".join(
            application(
                {
                    "REQUEST_METHOD": method,
                    "PATH_INFO": path,
                    "CONTENT_TYPE": "application/json",
                    "CONTENT_LENGTH": str(len(body)),
                    "wsgi.input": BytesIO(body),
                },
                start_response,
            )
        )
        return captured["status"], json.loads(response)

    def test_executes_and_recovers_one_authorized_answer(self) -> None:
        first = self.service.execute(self._request())
        replay = self.service.execute(self._request())

        self.assertTrue(first.assessment.sufficient)
        self.assertEqual(first.review.decision, ReviewDecision.APPROVED)
        self.assertEqual(replay.digest, first.digest)
        self.assertEqual(replay.candidate, first.candidate)
        self.assertEqual(replay.review, first.review)
        self.assertEqual(replay.authorization, first.authorization)
        with self.database.read() as connection:
            for table in (
                "app_tasks",
                "app_application_calls",
                "app_sufficiency_assessments",
                "app_answer_candidates",
                "app_answer_reviews",
                "app_response_authorizations",
            ):
                count = connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                self.assertEqual(count, 1, table)

    def test_retry_cannot_change_the_frozen_requirement(self) -> None:
        self.service.execute(self._request())
        self.requirements.required_terms = ("PaymentService",)

        with self.assertRaises(DomainError) as raised:
            self.service.execute(self._request())

        self.assertEqual(raised.exception.code, ErrorCode.IDEMPOTENCY_MISMATCH)

    def test_gap_can_run_one_authorized_update_and_reassess_every_need(self) -> None:
        refreshed_snapshot = self._publish(
            name="PaymentService",
            index=2,
            expected=self.snapshot.snapshot_id,
        )
        target = CanonicalBuildTarget(
            target_id=StableId("build_target_00000000000000000000000000000001"),
            target_kind=TargetKind.SOURCE_PATH,
            canonical_identity=(
                ("path", "src/PaymentService.java"),
                ("revision", "a" * 40),
            ),
            resolution_receipt_id=StableId(
                "resolution_receipt_00000000000000000000000000000001"
            ),
            resolution_receipt_digest=digest_of("resolution"),
            obligation=CoverageObligation.REQUIRED,
            boundary="EXACT",
            digest=digest_of("payment-target"),
        )
        update_request = KnowledgeUpdateRequest(
            idempotency_key=IdempotencyKey(
                "task:natural:investigate:knowledge-update"
            ),
            objective=BuildObjective.create(
                objective_id="objective:payment",
                description="Find the requested PaymentService declaration",
                unacceptable_outcomes=("invented source",),
            ),
            target=target,
            scope_id=self.scope.scope_id,
            scope_revision=Revision(1),
            source_id=StableId("source_00000000000000000000000000000001"),
            source_revision=Revision(1),
            binding_id=StableId("binding_00000000000000000000000000000001"),
            binding_revision=Revision(1),
            expected_current_snapshot_id=self.snapshot.snapshot_id,
            max_steps=4,
            max_items_per_step=20,
            max_bytes_per_step=4096,
            classification="INTERNAL",
            actor="user:test",
            correlation_ref=CorrelationRef("natural-task-investigation"),
        )
        result_core = {
            "request": update_request.digest.value,
            "snapshot": refreshed_snapshot.snapshot_id.value,
        }
        update_result = KnowledgeUpdateResult(
            result_id=StableId(
                "knowledge_update_result_00000000000000000000000000000001"
            ),
            attempt_id=StableId(
                "knowledge_update_00000000000000000000000000000001"
            ),
            request_digest=update_request.digest,
            state=UpdateAttemptState.COMPLETED,
            stop_reason=InvestigationStopReason.TARGET_COVERED,
            target_digest=target.digest,
            source_operation_references=(),
            artifact_references=(),
            target_coverage_complete=True,
            admission_id=None,
            admission_status=None,
            published_snapshot_id=refreshed_snapshot.snapshot_id,
            limitations=(),
            completed_at=self.clock(),
            digest=digest_of(result_core),
        )
        updater = CompletedKnowledgeUpdate(update_result)
        self.requirements.required_terms = ("PaymentService",)
        service = NaturalLanguageTaskService(
            tasks=self.tasks,
            knowledge=self.knowledge,
            knowledge_use=self.knowledge_use,
            responses=self.responses,
            requirement_planner=self.requirements,
            answer_planner=FixtureAnswerPlanner(),
            activation=self.activation,
            activation_scope=self.activation_scope,
            knowledge_updates=updater,
        )
        request = NaturalLanguageTaskRequest.create(
            conversation_ref="conversation:investigate",
            turn_ref="turn:1",
            request_ref="request:1",
            idempotency_key=IdempotencyKey("task:natural:investigate"),
            original_request="Is PaymentService declared?",
            caller_ref="user:test",
            classification="INTERNAL",
            scope_id=self.scope.scope_id,
            snapshot_id=self.snapshot.snapshot_id,
            knowledge_update_request=update_request,
        )

        first = service.execute(request)
        replay = service.execute(request)

        self.assertTrue(first.assessment.sufficient)
        self.assertEqual(first.assessment.snapshot_id, refreshed_snapshot.snapshot_id)
        self.assertIn("PaymentService", first.candidate.body)
        self.assertEqual(replay.digest, first.digest)
        self.assertEqual(updater.calls, 2)
        self.assertIsNotNone(updater.last_request)
        self.assertEqual(
            updater.last_request.requirement_plan.needs[0].need_id,
            "need:declaration",
        )
        with self.database.read() as connection:
            calls = connection.execute(
                "SELECT logical_occurrence FROM app_application_calls ORDER BY logical_occurrence"
            ).fetchall()
        self.assertEqual(
            [row[0] for row in calls],
            ["knowledge-query:1", "knowledge-query:2", "knowledge-update:1"],
        )

    def test_no_current_snapshot_runs_initial_update_before_assessment(self) -> None:
        target = CanonicalBuildTarget(
            target_id=StableId("build_target_00000000000000000000000000000002"),
            target_kind=TargetKind.REPOSITORY_REVISION,
            canonical_identity=(("revision", "a" * 40),),
            resolution_receipt_id=StableId(
                "resolution_receipt_00000000000000000000000000000002"
            ),
            resolution_receipt_digest=digest_of("initial-resolution"),
            obligation=CoverageObligation.REQUIRED,
            boundary="EXACT",
            digest=digest_of("initial-target"),
        )
        update_request = KnowledgeUpdateRequest(
            idempotency_key=IdempotencyKey(
                "task:natural:initial:knowledge-update"
            ),
            objective=BuildObjective.create(
                objective_id="objective:initial",
                description="Build the first exact repository snapshot",
                unacceptable_outcomes=("answer without source",),
            ),
            target=target,
            scope_id=self.scope.scope_id,
            scope_revision=Revision(1),
            source_id=StableId("source_00000000000000000000000000000002"),
            source_revision=Revision(1),
            binding_id=StableId("binding_00000000000000000000000000000002"),
            binding_revision=Revision(1),
            expected_current_snapshot_id=None,
            max_steps=4,
            max_items_per_step=20,
            max_bytes_per_step=4096,
            classification="INTERNAL",
            actor="user:test",
            correlation_ref=CorrelationRef("natural-task-initial"),
        )
        update_result = KnowledgeUpdateResult(
            result_id=StableId(
                "knowledge_update_result_00000000000000000000000000000002"
            ),
            attempt_id=StableId(
                "knowledge_update_00000000000000000000000000000002"
            ),
            request_digest=update_request.digest,
            state=UpdateAttemptState.COMPLETED,
            stop_reason=InvestigationStopReason.TARGET_COVERED,
            target_digest=target.digest,
            source_operation_references=(),
            artifact_references=(),
            target_coverage_complete=True,
            admission_id=None,
            admission_status=None,
            published_snapshot_id=self.snapshot.snapshot_id,
            limitations=(),
            completed_at=self.clock(),
            digest=digest_of("initial-result"),
        )
        updater = CompletedKnowledgeUpdate(update_result)
        service = NaturalLanguageTaskService(
            tasks=self.tasks,
            knowledge=self.knowledge,
            knowledge_use=self.knowledge_use,
            responses=self.responses,
            requirement_planner=self.requirements,
            answer_planner=FixtureAnswerPlanner(),
            activation=self.activation,
            activation_scope=self.activation_scope,
            knowledge_updates=updater,
        )
        request = NaturalLanguageTaskRequest.create(
            conversation_ref="conversation:initial",
            turn_ref="turn:1",
            request_ref="request:initial",
            idempotency_key=IdempotencyKey("task:natural:initial"),
            original_request="What does OrderService declare?",
            caller_ref="user:test",
            classification="INTERNAL",
            scope_id=self.scope.scope_id,
            snapshot_id=None,
            knowledge_update_request=update_request,
        )

        answer = service.execute(request)

        self.assertEqual(answer.candidate.snapshot_id, self.snapshot.snapshot_id)
        self.assertEqual(updater.calls, 1)
        with self.database.read() as connection:
            calls = connection.execute(
                "SELECT logical_occurrence FROM app_application_calls ORDER BY logical_occurrence"
            ).fetchall()
        self.assertEqual(
            [row[0] for row in calls],
            ["knowledge-query:1", "knowledge-update:1"],
        )

    def test_no_snapshot_without_initial_update_is_rejected(self) -> None:
        with self.assertRaises(DomainError) as raised:
            NaturalLanguageTaskRequest.create(
                conversation_ref="conversation:no-snapshot",
                turn_ref="turn:1",
                request_ref="request:no-snapshot",
                idempotency_key=IdempotencyKey("task:natural:no-snapshot"),
                original_request="What does OrderService declare?",
                caller_ref="user:test",
                classification="INTERNAL",
                scope_id=self.scope.scope_id,
                snapshot_id=None,
            )

        self.assertEqual(raised.exception.code, ErrorCode.INVALID_ARGUMENT)

    def test_deactivation_immediately_stops_new_or_replayed_execution(self) -> None:
        self.activation.deactivate_strategy(
            capability_id=NATURAL_TASK_CAPABILITY_ID,
            capability_contract_version=NATURAL_TASK_CAPABILITY_CONTRACT_VERSION,
            activation_scope=self.activation_scope,
            expected_revision=Revision(1),
            idempotency_key=IdempotencyKey("deactivate:natural-task"),
            actor="test",
            reason="stop the task strategy",
            correlation_ref=CorrelationRef("natural-task-test"),
        )

        with self.assertRaises(DomainError) as raised:
            self.service.execute(self._request())

        self.assertEqual(raised.exception.code, ErrorCode.NO_ACTIVE_STRATEGY)

    def test_unevaluated_runtime_component_cannot_use_the_activation(self) -> None:
        changed_planner = MutableRequirementPlanner()
        changed_planner.strategy_implementation_digest = digest_of(
            {"implementation": "changed"}
        )

        with self.assertRaises(DomainError) as raised:
            NaturalLanguageTaskService(
                tasks=self.tasks,
                knowledge=self.knowledge,
                knowledge_use=self.knowledge_use,
                responses=self.responses,
                requirement_planner=changed_planner,
                answer_planner=FixtureAnswerPlanner(),
                activation=self.activation,
                activation_scope=self.activation_scope,
            )

        self.assertEqual(
            raised.exception.code,
            ErrorCode.STRATEGY_CONTRACT_MISMATCH,
        )

    def test_task_cannot_cross_the_activated_classification_boundary(self) -> None:
        request = NaturalLanguageTaskRequest.create(
            conversation_ref="conversation:classified",
            turn_ref="turn:1",
            request_ref="request:1",
            idempotency_key=IdempotencyKey("task:natural:classified"),
            original_request="What does OrderService declare?",
            caller_ref="user:test",
            classification="CONFIDENTIAL",
            scope_id=self.scope.scope_id,
            snapshot_id=self.snapshot.snapshot_id,
        )

        with self.assertRaises(DomainError) as raised:
            self.service.execute(request)

        self.assertEqual(raised.exception.code, ErrorCode.CONTROL_STATE_DENIED)

    def test_http_prepares_but_does_not_claim_external_delivery(self) -> None:
        runtime = ApplicationRuntime(
            self.database,
            natural_task_service=self.service,
        )
        application = JsonHttpApplication(runtime, live_provider_configured=True)

        status, payload = self._http(
            application,
            "POST",
            "/v1/tasks/prepare-answer",
            {
                "conversation_ref": "conversation:http",
                "turn_ref": "turn:1",
                "request_ref": "request:1",
                "idempotency_key": "task:natural:http",
                "scope_id": self.scope.scope_id.value,
                "snapshot_id": self.snapshot.snapshot_id.value,
                "request": "What does OrderService declare?",
                "caller_ref": "user:test",
                "classification": "INTERNAL",
            },
        )

        self.assertEqual(status, "200 OK")
        self.assertEqual(payload["review"]["decision"], "APPROVED")
        self.assertFalse(payload["delivery"]["performed"])
        self.assertTrue(payload["candidate"]["body"])
        events = runtime.telemetry.list_by_correlation("request:1")
        self.assertEqual(len(events), 1)
        self.assertEqual(
            events[0].operation,
            "natural-task-answer-preparation@1",
        )


if __name__ == "__main__":
    unittest.main()
