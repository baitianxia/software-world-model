from __future__ import annotations

import uuid

from swm_demo.agent_contract import AgentTask, AnswerReviewResult, FinalResponse
from swm_demo.answer_review_agent import AnswerReviewAgent
from swm_demo.model_gateway import ModelGateway, ModelPhase
from swm_demo.task_execution_agent import TaskExecutionAgent, TaskExecutionError


class AgentOrchestrator:
    """Understands the request and delegates; it performs no domain task itself."""

    def __init__(
        self,
        task_agent: TaskExecutionAgent,
        review_agent: AnswerReviewAgent,
        model_gateway: ModelGateway,
    ):
        self.task_agent = task_agent
        self.review_agent = review_agent
        self.model_gateway = model_gateway

    def handle(self, original_request: str, scope_id: str) -> FinalResponse:
        routing_context = self.model_gateway.open_context(
            f"routing:{uuid.uuid4()}", ModelPhase.ROUTING
        )
        try:
            routing = self.model_gateway.invoke(
                "route-task",
                {"request": original_request, "scope_id": scope_id},
                context=routing_context,
            )
        finally:
            self.model_gateway.close_context(routing_context)
        use_case = str(routing.output["use_case"])
        parameters = {
            key: value
            for key, value in routing.output.items()
            if key != "use_case"
        }
        task = AgentTask(
            task_id=f"agent-task:{uuid.uuid4()}",
            original_request=original_request,
            scope_id=scope_id,
            use_case=use_case,
            parameters=parameters,
            routing_model_call_id=routing.model_call_id,
        )
        try:
            candidate = self.task_agent.execute(task)
        except TaskExecutionError as error:
            review = AnswerReviewResult(
                decision=error.status,
                issues=(str(error),),
                review_model_call_id=None,
            )
            return FinalResponse(
                status=error.status,
                answer=None,
                snapshot_id=error.snapshot_id,
                knowledge_reference_ids=(),
                review=review,
            )
        review = self.review_agent.review(original_request, task, candidate)
        references = tuple(
            sorted(
                {
                    reference
                    for claim in candidate.claims
                    for reference in claim.knowledge_reference_ids
                }
            )
        )
        if review.decision == "PASS":
            return FinalResponse(
                status="ANSWERED",
                answer=candidate.answer,
                snapshot_id=candidate.snapshot_id,
                knowledge_reference_ids=references,
                review=review,
            )
        return FinalResponse(
            status=review.decision,
            answer=None,
            snapshot_id=candidate.snapshot_id,
            knowledge_reference_ids=references,
            review=review,
        )
