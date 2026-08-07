"""Recoverable natural-language task execution through activated owner services."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Mapping

from software_world_model.cross_cutting import (
    Digest,
    DomainError,
    ErrorCode,
    IdempotencyKey,
    Revision,
    StableId,
    digest_of,
)
from software_world_model.knowledge_engine import FormalKnowledgeService

from .activation import ResolvedStrategy, StrategyActivationService
from .knowledge_use import (
    KnowledgeRequirement,
    KnowledgeRequirementPlan,
    KnowledgeRequirementPlanner,
    KnowledgeUseService,
    RequirementFidelity,
    SufficiencyAssessment,
    TaskBoundary,
)
from .knowledge_update import (
    KnowledgeUpdateRequest,
    KnowledgeUpdateResult,
    KnowledgeUpdateService,
    UpdateAttemptState,
)
from .response_control import (
    AnswerCandidate,
    AnswerDraftPlanner,
    AnswerReviewResult,
    FinalResponseAuthorization,
    ResponseControlService,
    ReviewDecision,
)
from .task_control import (
    AgentCapability,
    AgentCapabilityCatalog,
    AgentInvocation,
    ApplicationCallState,
    ConversationalTask,
    ConversationalTaskControl,
    EffectClass,
    OrchestratorProposal,
    TaskRequestEnvelope,
    TaskState,
)


NATURAL_TASK_CAPABILITY_ID = "software-knowledge-task"
NATURAL_TASK_CAPABILITY_CONTRACT_VERSION = "1.1.0"


@dataclass(frozen=True, slots=True)
class NaturalLanguageTaskRequest:
    conversation_ref: str
    turn_ref: str
    request_ref: str
    idempotency_key: IdempotencyKey
    original_request: str
    caller_ref: str
    classification: str
    scope_id: StableId
    snapshot_id: StableId | None
    knowledge_update_request: KnowledgeUpdateRequest | None
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        conversation_ref: str,
        turn_ref: str,
        request_ref: str,
        idempotency_key: IdempotencyKey,
        original_request: str,
        caller_ref: str,
        classification: str,
        scope_id: StableId,
        snapshot_id: StableId | None,
        knowledge_update_request: KnowledgeUpdateRequest | None = None,
    ) -> "NaturalLanguageTaskRequest":
        if snapshot_id is None and knowledge_update_request is None:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "a task without a current snapshot must include an initial knowledge update",
            )
        if knowledge_update_request is not None and (
            knowledge_update_request.scope_id != scope_id
            or knowledge_update_request.expected_current_snapshot_id != snapshot_id
            or knowledge_update_request.classification != classification
            or knowledge_update_request.idempotency_key.value
            != f"{idempotency_key.value}:knowledge-update"
        ):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "knowledge update must bind the task scope, snapshot, classification, and derived key",
            )
        core = {
            "conversation_ref": _text(conversation_ref, "conversation reference"),
            "turn_ref": _text(turn_ref, "turn reference"),
            "request_ref": _text(request_ref, "request reference"),
            "idempotency_key": idempotency_key.value,
            "original_request": _text(original_request, "original request"),
            "caller_ref": _text(caller_ref, "caller reference"),
            "classification": _text(classification, "classification"),
            "scope_id": scope_id.value,
            "snapshot_id": snapshot_id.value if snapshot_id else None,
            "knowledge_update_digest": (
                knowledge_update_request.digest.value
                if knowledge_update_request
                else None
            ),
        }
        return cls(
            conversation_ref=core["conversation_ref"],
            turn_ref=core["turn_ref"],
            request_ref=core["request_ref"],
            idempotency_key=idempotency_key,
            original_request=core["original_request"],
            caller_ref=core["caller_ref"],
            classification=core["classification"],
            scope_id=scope_id,
            snapshot_id=snapshot_id,
            knowledge_update_request=knowledge_update_request,
            digest=digest_of(core),
        )


@dataclass(frozen=True, slots=True)
class AuthorizedTaskAnswer:
    task: ConversationalTask
    requirement: KnowledgeRequirement
    assessment: SufficiencyAssessment
    candidate: AnswerCandidate
    review: AnswerReviewResult
    authorization: FinalResponseAuthorization
    digest: Digest


class NaturalLanguageTaskService:
    """Run one exact-snapshot task and recover every durable completed stage."""

    def __init__(
        self,
        *,
        tasks: ConversationalTaskControl,
        knowledge: FormalKnowledgeService,
        knowledge_use: KnowledgeUseService,
        responses: ResponseControlService,
        requirement_planner: KnowledgeRequirementPlanner,
        answer_planner: AnswerDraftPlanner,
        activation: StrategyActivationService,
        activation_scope: Mapping[str, str],
        knowledge_updates: KnowledgeUpdateService | None = None,
    ) -> None:
        self._activation = activation
        self._activation_scope = dict(activation_scope)
        activated_strategy = self._resolve_active_strategy()
        component_digests = (
            getattr(requirement_planner, "strategy_implementation_digest", None),
            knowledge_use.strategy_implementation_digest,
            getattr(answer_planner, "strategy_implementation_digest", None),
            responses.strategy_implementation_digest,
        )
        if any(
            digest != activated_strategy.strategy.implementation_digest
            for digest in component_digests
        ):
            raise DomainError(
                ErrorCode.STRATEGY_CONTRACT_MISMATCH,
                "runtime task components do not match the evaluated strategy implementation",
            )
        qualification = activated_strategy.decision.qualification
        assert qualification is not None
        component_qualification_refs = (
            getattr(requirement_planner, "qualification_ref", None),
            knowledge_use.strategy_qualification_ref,
            getattr(answer_planner, "qualification_ref", None),
            responses.strategy_qualification_ref,
        )
        if any(
            reference != qualification.proof_ref
            for reference in component_qualification_refs
        ):
            raise DomainError(
                ErrorCode.QUALIFICATION_INVALID,
                "runtime task components do not bind the active evaluation proof",
            )
        component_classifications = (
            getattr(requirement_planner, "classification", None),
            knowledge_use.strategy_classification,
            getattr(answer_planner, "classification", None),
            responses.strategy_classification,
        )
        if (
            any(value is None for value in component_classifications)
            or len(set(component_classifications)) != 1
        ):
            raise DomainError(
                ErrorCode.STRATEGY_CONTRACT_MISMATCH,
                "runtime task components do not share one exact classification",
            )
        strategy_classification = component_classifications[0]
        assert strategy_classification is not None
        if knowledge_updates is not None and (
            knowledge_updates.strategy_implementation_digest
            != activated_strategy.strategy.implementation_digest
            or knowledge_updates.strategy_qualification_ref
            != qualification.proof_ref
            or knowledge_updates.strategy_classification
            != strategy_classification
        ):
            raise DomainError(
                ErrorCode.STRATEGY_CONTRACT_MISMATCH,
                "knowledge update runtime does not match the active evaluated strategy",
            )
        self._tasks = tasks
        self._knowledge = knowledge
        self._use = knowledge_use
        self._responses = responses
        self._requirement_planner = requirement_planner
        self._answer_planner = answer_planner
        self._knowledge_updates = knowledge_updates
        self._strategy_classification = strategy_classification
        self._strategy = activated_strategy
        catalog_digest = activated_strategy.decision.digest
        self._catalog = AgentCapabilityCatalog.create(
            catalog_id=StableId(f"agent_catalog_{catalog_digest.value[-32:]}"),
            revision=activated_strategy.decision.activation_revision,
            capabilities=(
                AgentCapability(
                    capability_id=NATURAL_TASK_CAPABILITY_ID,
                    contract_version=NATURAL_TASK_CAPABILITY_CONTRACT_VERSION,
                    allowed_use_cases=(
                        ("knowledge.query", "knowledge.update")
                        if knowledge_updates is not None
                        else ("knowledge.query",)
                    ),
                    allowed_effect_classes=(
                        (EffectClass.QUERY, EffectClass.COMMAND)
                        if knowledge_updates is not None
                        else (EffectClass.QUERY,)
                    ),
                    production_active=True,
                ),
            ),
        )

    def is_currently_active(self) -> bool:
        try:
            current = self._resolve_active_strategy()
        except DomainError:
            return False
        return current.decision.digest == self._strategy.decision.digest

    def execute(self, request: NaturalLanguageTaskRequest) -> AuthorizedTaskAnswer:
        current_strategy = self._resolve_active_strategy()
        if current_strategy.decision.digest != self._strategy.decision.digest:
            raise DomainError(
                ErrorCode.LIVE_INTEGRATION_HELD,
                "the configured natural-language task strategy is no longer current",
            )
        if request.classification != self._strategy_classification:
            raise DomainError(
                ErrorCode.CONTROL_STATE_DENIED,
                "task classification does not match the activated model strategy",
            )
        if request.snapshot_id is not None:
            snapshot = self._knowledge.get_snapshot(request.snapshot_id)
            if snapshot.scope_id != request.scope_id:
                raise DomainError(
                    ErrorCode.CONTROL_STATE_DENIED,
                    "task snapshot is outside its authorized scope",
                )
        envelope = TaskRequestEnvelope.create(
            conversation_ref=request.conversation_ref,
            turn_ref=request.turn_ref,
            request_ref=request.request_ref,
            idempotency_key=request.idempotency_key,
            original_request=request.original_request,
            caller_ref=request.caller_ref,
            classification=request.classification,
            scope_id=request.scope_id,
        )
        task = self._tasks.create_task(envelope, self._catalog)
        if task.state is TaskState.RECEIVED:
            task = self._tasks.accept_orchestrator_proposal(
                task_id=task.task_id,
                expected_revision=task.revision,
                proposal=OrchestratorProposal.create(
                    task_kind="SOFTWARE_KNOWLEDGE_QUERY",
                    capability_id=NATURAL_TASK_CAPABILITY_ID,
                    target_scope_id=request.scope_id,
                    response_kind="REVIEWED_KNOWLEDGE_ANSWER",
                ),
                catalog=self._catalog,
            )
        if task.state not in {
            TaskState.READY,
            TaskState.RUNNING,
            TaskState.RESPONSE_PENDING,
        }:
            raise DomainError(
                ErrorCode.MANAGEMENT_STATE_CONFLICT,
                "natural-language task is not recoverable from its current state",
            )

        plan = self._requirement_planner.plan(
            original_request=request.original_request
        )
        requirement = self._requirement(request, plan)

        if task.candidate_reference is not None:
            candidate = self._responses.get_candidate(task.candidate_reference)
            expected_snapshot_id = request.snapshot_id
            if expected_snapshot_id is None or candidate.snapshot_id != expected_snapshot_id:
                update_result = self._recover_knowledge_update(
                    request, task, requirement_plan=plan
                )
                expected_snapshot_id = self._completed_update_snapshot(update_result)
            if (
                candidate.snapshot_id != expected_snapshot_id
                or candidate.requirement_id != requirement.requirement_id
                or candidate.requirement_revision != requirement.revision.value
            ):
                raise DomainError(
                    ErrorCode.IDEMPOTENCY_MISMATCH,
                    "task retry changed its exact snapshot or requirement plan",
                )
            assessment = self._use.get_assessment(candidate.assessment_id)
            candidate, task = self._responses.draft_and_seal_candidate(
                task=task,
                requirement=requirement,
                assessment=assessment,
                planner=self._answer_planner,
                partial_allowed=True,
            )
        else:
            invocation = self._tasks.create_invocation(
                task_id=task.task_id,
                input_digest=request.digest,
                catalog=self._catalog,
            )
            task = self._tasks.get_task(task.task_id)
            if request.snapshot_id is None:
                update_result = self._run_knowledge_update(
                    request=request,
                    task=task,
                    invocation=invocation,
                    requirement_plan=plan,
                )
                updated_snapshot_id = self._completed_update_snapshot(update_result)
                assessment = self._assess_via_application_call(
                    request=request,
                    task=task,
                    invocation=invocation,
                    requirement=requirement,
                    snapshot_id=updated_snapshot_id,
                    logical_occurrence="knowledge-query:1",
                    key_suffix=":initialized",
                )
            else:
                assessment = self._assess_via_application_call(
                    request=request,
                    task=task,
                    invocation=invocation,
                    requirement=requirement,
                    snapshot_id=request.snapshot_id,
                    logical_occurrence="knowledge-query:1",
                    key_suffix="",
                )
                if not assessment.sufficient and request.knowledge_update_request:
                    update_result = self._run_knowledge_update(
                        request=request,
                        task=task,
                        invocation=invocation,
                        requirement_plan=plan,
                    )
                    updated_snapshot_id = self._completed_update_snapshot(update_result)
                    assessment = self._assess_via_application_call(
                        request=request,
                        task=task,
                        invocation=invocation,
                        requirement=requirement,
                        snapshot_id=updated_snapshot_id,
                        logical_occurrence="knowledge-query:2",
                        key_suffix=":refreshed",
                    )
            candidate, task = self._responses.draft_and_seal_candidate(
                task=task,
                requirement=requirement,
                assessment=assessment,
                planner=self._answer_planner,
                partial_allowed=True,
            )

        review = self._responses.review(
            task=task,
            requirement=requirement,
            candidate=candidate,
            assessment=assessment,
        )
        if review.decision is not ReviewDecision.APPROVED:
            raise DomainError(
                ErrorCode.CONTROL_STATE_DENIED,
                "natural-language answer failed semantic review",
            )
        authorization = self._responses.authorize(
            task=task,
            candidate=candidate,
            review=review,
        )
        core = {
            "task_id": task.task_id.value,
            "task_revision": task.revision.value,
            "requirement_digest": requirement.digest.value,
            "assessment_digest": assessment.digest.value,
            "candidate_digest": candidate.digest.value,
            "review_digest": review.digest.value,
            "authorization_digest": authorization.digest.value,
            "strategy_activation_digest": self._strategy.decision.digest.value,
        }
        return AuthorizedTaskAnswer(
            task=task,
            requirement=requirement,
            assessment=assessment,
            candidate=candidate,
            review=review,
            authorization=authorization,
            digest=digest_of(core),
        )

    def _assess_via_application_call(
        self,
        *,
        request: NaturalLanguageTaskRequest,
        task: ConversationalTask,
        invocation: AgentInvocation,
        requirement: KnowledgeRequirement,
        snapshot_id: StableId,
        logical_occurrence: str,
        key_suffix: str,
    ) -> SufficiencyAssessment:
        call = self._tasks.prepare_application_call(
            invocation=invocation,
            logical_occurrence=logical_occurrence,
            use_case="knowledge.query",
            effect_class=EffectClass.QUERY,
            request_digest=digest_of(
                {
                    "task_request": request.digest.value,
                    "requirement": requirement.digest.value,
                    "snapshot_id": snapshot_id.value,
                }
            ),
        )
        if call.state is ApplicationCallState.PREPARED:
            call = self._tasks.transition_application_call(
                call_id=call.call_id,
                expected_revision=call.revision,
                target=ApplicationCallState.DISPATCHED,
            )
        if call.state is ApplicationCallState.SUCCEEDED:
            if call.result_reference is None or call.result_digest is None:
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "successful knowledge query has no result proof",
                )
            assessment = self._use.get_assessment(StableId(call.result_reference))
            if assessment.digest != call.result_digest:
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "knowledge query result disagrees with its application call",
                )
            return assessment
        if call.state is not ApplicationCallState.DISPATCHED:
            raise DomainError(
                ErrorCode.MANAGEMENT_STATE_CONFLICT,
                "knowledge query call did not reach a recoverable outcome",
            )
        boundary = TaskBoundary.create(
            task_id=task.task_id,
            task_revision=task.revision,
            scope_id=request.scope_id,
            purpose="answer one exact-snapshot software question",
            classification=request.classification,
        )
        session = self._use.open_session(
            idempotency_key=IdempotencyKey(
                f"{request.idempotency_key.value}:session{key_suffix}"
            ),
            boundary=boundary,
            requirement=requirement,
            snapshot_id=snapshot_id,
        )
        assessment = self._use.assess(
            idempotency_key=IdempotencyKey(
                f"{request.idempotency_key.value}:assessment{key_suffix}"
            ),
            requirement=requirement,
            session=session,
        )
        self._tasks.transition_application_call(
            call_id=call.call_id,
            expected_revision=call.revision,
            target=ApplicationCallState.SUCCEEDED,
            result_reference=assessment.assessment_id.value,
            result_digest=assessment.digest,
        )
        return assessment

    def _run_knowledge_update(
        self,
        *,
        request: NaturalLanguageTaskRequest,
        task: ConversationalTask,
        invocation: AgentInvocation,
        requirement_plan: KnowledgeRequirementPlan,
    ) -> KnowledgeUpdateResult:
        update_request = self._planned_update_request(request, requirement_plan)
        if update_request is None or self._knowledge_updates is None:
            raise DomainError(
                ErrorCode.LIVE_INTEGRATION_HELD,
                "the task requested investigation but no activated knowledge update is configured",
            )
        call = self._tasks.prepare_application_call(
            invocation=invocation,
            logical_occurrence="knowledge-update:1",
            use_case="knowledge.update",
            effect_class=EffectClass.COMMAND,
            request_digest=update_request.digest,
        )
        if call.state is ApplicationCallState.PREPARED:
            call = self._tasks.transition_application_call(
                call_id=call.call_id,
                expected_revision=call.revision,
                target=ApplicationCallState.DISPATCHED,
            )
        if call.state is ApplicationCallState.SUCCEEDED:
            return self._recover_knowledge_update(
                request, task, requirement_plan=requirement_plan
            )
        if call.state is not ApplicationCallState.DISPATCHED:
            raise DomainError(
                ErrorCode.MANAGEMENT_STATE_CONFLICT,
                "knowledge update call did not reach a recoverable outcome",
            )
        result = self._knowledge_updates.execute(update_request)
        self._tasks.transition_application_call(
            call_id=call.call_id,
            expected_revision=call.revision,
            target=ApplicationCallState.SUCCEEDED,
            result_reference=result.result_id.value,
            result_digest=result.digest,
        )
        return result

    def _recover_knowledge_update(
        self,
        request: NaturalLanguageTaskRequest,
        task: ConversationalTask,
        *,
        requirement_plan: KnowledgeRequirementPlan,
    ) -> KnowledgeUpdateResult:
        update_request = self._planned_update_request(request, requirement_plan)
        if update_request is None or self._knowledge_updates is None:
            raise DomainError(
                ErrorCode.IDEMPOTENCY_MISMATCH,
                "task candidate uses an unrequested knowledge update snapshot",
            )
        call = self._tasks.get_application_call(
            task_id=task.task_id,
            logical_occurrence="knowledge-update:1",
        )
        if (
            call is None
            or call.state is not ApplicationCallState.SUCCEEDED
            or call.result_reference is None
            or call.result_digest is None
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "task candidate has no successful knowledge update proof",
            )
        result = self._knowledge_updates.execute(update_request)
        if (
            result.result_id.value != call.result_reference
            or result.digest != call.result_digest
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "knowledge update result disagrees with its application call",
            )
        return result

    @staticmethod
    def _planned_update_request(
        request: NaturalLanguageTaskRequest,
        requirement_plan: KnowledgeRequirementPlan,
    ) -> KnowledgeUpdateRequest | None:
        update_request = request.knowledge_update_request
        if update_request is None:
            return None
        if update_request.requirement_plan == requirement_plan:
            return update_request
        return replace(update_request, requirement_plan=requirement_plan)

    @staticmethod
    def _completed_update_snapshot(result: KnowledgeUpdateResult) -> StableId:
        if (
            result.state is not UpdateAttemptState.COMPLETED
            or not result.target_coverage_complete
            or result.published_snapshot_id is None
        ):
            raise DomainError(
                ErrorCode.CONTROL_STATE_DENIED,
                "authorized knowledge investigation did not publish a complete snapshot",
                {
                    "update_state": result.state.value,
                    "stop_reason": result.stop_reason.value,
                },
            )
        return result.published_snapshot_id

    @staticmethod
    def _requirement(
        request: NaturalLanguageTaskRequest,
        plan: KnowledgeRequirementPlan,
    ) -> KnowledgeRequirement:
        if not isinstance(plan, KnowledgeRequirementPlan):
            raise DomainError(
                ErrorCode.STRUCTURED_OUTPUT_INVALID,
                "requirement planner returned an invalid plan",
            )
        identity = digest_of(
            {
                "request_digest": request.digest.value,
                "requirement_plan": plan,
            }
        )
        return KnowledgeRequirement.create(
            requirement_id=StableId(f"requirement_{identity.value[-32:]}"),
            revision=Revision(1),
            fidelity=RequirementFidelity.ORIGINAL,
            original_request=request.original_request,
            needs=plan.needs,
            joint_constraints=plan.joint_constraints,
        )

    def _resolve_active_strategy(self) -> ResolvedStrategy:
        strategy = self._activation.resolve_strategy(
            capability_id=NATURAL_TASK_CAPABILITY_ID,
            capability_contract_version=NATURAL_TASK_CAPABILITY_CONTRACT_VERSION,
            activation_scope=self._activation_scope,
        )
        qualification = strategy.decision.qualification
        if (
            strategy.capability.capability_id != NATURAL_TASK_CAPABILITY_ID
            or strategy.capability.contract_version
            != NATURAL_TASK_CAPABILITY_CONTRACT_VERSION
            or strategy.strategy.capability_id != NATURAL_TASK_CAPABILITY_ID
            or strategy.strategy.capability_contract_version
            != NATURAL_TASK_CAPABILITY_CONTRACT_VERSION
            or qualification is None
            or qualification.qualification_kind != "CAPABILITY_EVALUATION"
            or not qualification.verify_digest()
            or qualification.capability_id != NATURAL_TASK_CAPABILITY_ID
            or qualification.capability_contract_version
            != NATURAL_TASK_CAPABILITY_CONTRACT_VERSION
            or qualification.strategy_id != strategy.strategy.strategy_id
            or qualification.strategy_version != strategy.strategy.strategy_version
        ):
            raise DomainError(
                ErrorCode.STRATEGY_CONTRACT_MISMATCH,
                "natural-language task service requires an activated evaluated strategy",
            )
        return strategy


def _text(value: str, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} must be non-empty")
    return value
