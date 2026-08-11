from __future__ import annotations

from dataclasses import replace
import unittest

from software_world_model.application_services.world_model_answering import (
    InMemoryWorldModelAuthorityStore,
    InMemoryWorldModelEvaluationSink,
    QUALIFIED_MODEL_STRATEGY_MODE,
    WorldModelAnsweringService,
    WorldModelResponseControlService,
)
from software_world_model.cross_cutting import DomainError, digest_of
from software_world_model.interface.world_model_evaluation import (
    world_model_evaluation_page_payload,
)
from tests import test_world_model_answering as fixtures


MODEL_ROUTE = "AF_UNIX:ITER-003-MODEL-EGRESS-GATEWAY@1.0.0"


class ModelInventoryQueryPlanner(fixtures.InventoryQueryPlanner):
    strategy_ref = "test-qualified-model-query-planner@1"
    execution_mode = QUALIFIED_MODEL_STRATEGY_MODE
    provider_route = MODEL_ROUTE


class ModelAnswerReviewer(fixtures.ApprovingAnswerReviewer):
    strategy_ref = "test-qualified-model-answer-reviewer@1"
    execution_mode = QUALIFIED_MODEL_STRATEGY_MODE
    provider_route = MODEL_ROUTE


class WrongRoutePlanner(ModelInventoryQueryPlanner):
    provider_route = "AF_UNIX:another-gateway"


class WorldModelLiveExecutionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.view_fixture = fixtures._structure_view_tests.StructureViewTests(
            methodName="runTest"
        )
        self.view_fixture.setUp()
        self.addCleanup(self.view_fixture.doCleanups)
        self.store = InMemoryWorldModelAuthorityStore()
        self.answering = WorldModelAnsweringService(
            self.store,
            self.view_fixture.service,
            model_route=MODEL_ROUTE,
        )
        self.responses = WorldModelResponseControlService(
            self.store, self.answering
        )

    def _execute(self, *, provider_calls: int = 2):
        question = self.answering.open_question(
            request_ref="world-model-live-test",
            original_question="列出 B 的全部 reactor child modules。",
            response_language="zh-CN",
            classification="INTERNAL",
            permission_digest=digest_of("world-model-live-test-permission"),
        )
        requirement = self.answering.seal_requirement(
            question_id=question.question_id,
            planner=fixtures.StaticRequirementPlanner(fixtures.INVENTORY_NEED),
            fidelity_reviewer=fixtures.ApprovingRequirementReviewer(),
        )
        plan = self.answering.seal_query_plan(
            requirement_id=requirement.requirement_id,
            planner=ModelInventoryQueryPlanner(self.view_fixture.b[0].snapshot_id),
        )
        result_set = self.answering.execute_query_plan(plan_id=plan.plan_id)
        assessment = self.answering.assess(
            result_set_id=result_set.result_set_id
        )
        draft = self.responses.seal_draft(
            assessment_id=assessment.assessment_id,
            generator=fixtures.ResultBoundDraftGenerator(),
        )
        review = self.responses.review(
            draft_id=draft.draft_id,
            reviewer=ModelAnswerReviewer(),
        )
        authorization = self.responses.authorize(review_id=review.review_id)
        delivery = self.responses.deliver(
            authorization_id=authorization.authorization_id,
            sink=InMemoryWorldModelEvaluationSink(),
        )
        return self.responses.authority_chain(
            delivery_id=delivery.delivery_id,
            provider_call_count=provider_calls,
            network_operation_count=provider_calls,
        )

    def test_mixed_offline_and_model_invocations_form_a_live_evaluation_chain(self):
        chain = self._execute()

        self.assertIs(chain.question.external_dispatch_allowed, True)
        self.assertEqual(chain.question.model_route, MODEL_ROUTE)
        self.assertEqual(chain.provider_call_count, 2)
        self.assertEqual(
            chain.plan.planning_invocation.execution_mode,
            QUALIFIED_MODEL_STRATEGY_MODE,
        )
        self.assertEqual(
            chain.review.review_invocation.execution_mode,
            QUALIFIED_MODEL_STRATEGY_MODE,
        )
        chain.require_valid()

        page = world_model_evaluation_page_payload(chain, "a" * 40)
        self.assertIs(
            page["execution_boundary"]["external_dispatch_allowed"], True
        )
        self.assertEqual(
            page["execution_boundary"]["provider_route"], MODEL_ROUTE
        )

    def test_model_strategy_cannot_change_the_question_route(self):
        question = self.answering.open_question(
            request_ref="world-model-live-wrong-route",
            original_question="列出 B 的全部 reactor child modules。",
            response_language="zh-CN",
            classification="INTERNAL",
            permission_digest=digest_of("world-model-live-test-permission"),
        )
        requirement = self.answering.seal_requirement(
            question_id=question.question_id,
            planner=fixtures.StaticRequirementPlanner(fixtures.INVENTORY_NEED),
            fidelity_reviewer=fixtures.ApprovingRequirementReviewer(),
        )

        with self.assertRaises(DomainError) as raised:
            self.answering.seal_query_plan(
                requirement_id=requirement.requirement_id,
                planner=WrongRoutePlanner(self.view_fixture.b[0].snapshot_id),
            )

        self.assertEqual(
            raised.exception.details.get("reason_code"),
            "MODEL_INVOCATION_ROUTE_DENIED",
        )

    def test_live_chain_requires_one_to_five_exact_gateway_calls(self):
        for provider_calls in (0, 6):
            with self.subTest(provider_calls=provider_calls):
                with self.assertRaises(DomainError) as raised:
                    self._execute(provider_calls=provider_calls)
                self.assertEqual(
                    raised.exception.details.get("reason_code"),
                    "WORLD_MODEL_CHAIN_EXECUTION_BOUNDARY_INVALID",
                )

    def test_live_chain_rejects_boolean_execution_counters(self):
        chain = self._execute()
        tampered = fixtures._redigest_chain(
            replace(
                chain,
                provider_call_count=True,
                network_operation_count=True,
            )
        )

        with self.assertRaises(DomainError) as raised:
            tampered.require_valid()

        self.assertEqual(
            raised.exception.details.get("reason_code"),
            "WORLD_MODEL_CHAIN_EXECUTION_BOUNDARY_INVALID",
        )


if __name__ == "__main__":
    unittest.main()
