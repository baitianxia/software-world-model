from __future__ import annotations

import unittest

from software_world_model.application_services.conversational_engineering_routing import (
    ENGINEERING_PROVIDER_ATTEMPT_COMPONENTS,
    ApplicationOwnedEngineeringProviderRouter,
    EngineeringProviderAttemptRuntime,
    EngineeringProviderRoutePlan,
    EngineeringProviderRouteRole,
    EngineeringProviderRouteSpec,
    engineering_agent_dual_provider_route_ref,
)
from software_world_model.application_services.engineering_conversation import (
    ConversationMessageKind,
    ConversationTurnState,
    EngineeringChatBinding,
    EngineeringProviderFailureClassification,
    EngineeringTurnExecutionOutcome,
    InMemoryEngineeringConversationService,
    RuntimeCapabilityStatus,
)
from software_world_model.cross_cutting import (
    Digest,
    DomainError,
    Revision,
    StableId,
    digest_of,
)


class SequentialIdGenerator:
    def __init__(self, prefix: str) -> None:
        self.prefix = prefix
        self.value = 0

    def new(self, kind: str) -> StableId:
        self.value += 1
        _ = self.prefix
        return StableId(f"{kind[:31]}_{self.value:032x}")


class _Executor:
    def __init__(self, builder) -> None:
        self._builder = builder
        self.requests = []

    def execute(self, request):
        self.requests.append(request)
        return self._builder(request)


class _Factory:
    def __init__(self, builders, *, reuse_runtime: bool = False) -> None:
        self._builders = builders
        self._reuse_runtime = reuse_runtime
        self.authorities = []
        self.runtimes = []

    def create(self, authority):
        self.authorities.append(authority)
        if self._reuse_runtime and self.runtimes:
            prior = self.runtimes[0]
            runtime = EngineeringProviderAttemptRuntime.create(
                executor=prior.executor,
                authority=authority,
                component_instance_refs=prior.component_instance_refs,
            )
        else:
            executor = _Executor(self._builders[authority.role])
            components = tuple(
                (
                    name,
                    f"{authority.role.value.casefold()}-{authority.attempt_id.value}-{name}",
                )
                for name in ENGINEERING_PROVIDER_ATTEMPT_COMPONENTS
            )
            runtime = EngineeringProviderAttemptRuntime.create(
                executor=executor,
                authority=authority,
                component_instance_refs=components,
            )
        self.runtimes.append(runtime)
        return runtime


class _FailingFactory:
    def __init__(self) -> None:
        self.authorities = []

    def create(self, authority):
        self.authorities.append(authority)
        raise RuntimeError("route implementation is missing")


def _configuration_digest(provider: str) -> Digest:
    return digest_of(["provider-configuration", provider])


def _binding_and_plan(*, standing_authority: bool = False):
    ark = _configuration_digest("VOLCENGINE_ARK")
    deepseek = _configuration_digest("DEEPSEEK")
    route_ref = engineering_agent_dual_provider_route_ref(
        primary_configuration_digest=ark,
        fallback_configuration_digest=deepseek,
    )
    binding = EngineeringChatBinding.create(
        product_revision="a" * 40,
        project_name="mall",
        repository_revision="b" * 40,
        world_model_status=RuntimeCapabilityStatus.READY,
        world_model_authority_digest=digest_of("world-model"),
        source_profile_ref="mall-source-profile@1",
        source_access_status=RuntimeCapabilityStatus.READY,
        provider_status=RuntimeCapabilityStatus.READY,
        provider_route_ref=route_ref,
        known_limitations=("Direction Alpha only",),
    )
    standing_digest = (
        digest_of("public-source-standing-authority")
        if standing_authority
        else None
    )
    primary = EngineeringProviderRouteSpec.create(
        ordinal=1,
        role=EngineeringProviderRouteRole.PRIMARY,
        provider_type="VOLCENGINE_ARK",
        endpoint="https://ark.cn-beijing.volces.com/api/coding/v3/chat/completions",
        model_ref="ark-model",
        provider_configuration_digest=ark,
        session_disclosure_authority_digest=digest_of("ark-session"),
        standing_authority_digest=standing_digest,
        qualification_ref="CC-ARK:sha256:current",
        maximum_dispatches_per_turn=15,
    )
    fallback = EngineeringProviderRouteSpec.create(
        ordinal=2,
        role=EngineeringProviderRouteRole.FALLBACK,
        provider_type="DEEPSEEK",
        endpoint="https://api.deepseek.com/chat/completions",
        model_ref="deepseek-model",
        provider_configuration_digest=deepseek,
        session_disclosure_authority_digest=digest_of("deepseek-session"),
        standing_authority_digest=standing_digest,
        qualification_ref="CC-DEEPSEEK:sha256:current",
        maximum_dispatches_per_turn=15,
    )
    return binding, EngineeringProviderRoutePlan.create(
        binding=binding,
        primary=primary,
        fallback=fallback,
    )


def _failure(
    request,
    *,
    code: str,
    classification: EngineeringProviderFailureClassification | None = None,
    provider_code: str | None = None,
    dispatches: int = 0,
    receipt_ref: str | None = None,
):
    context = request.snapshot_before.context
    return EngineeringTurnExecutionOutcome.failed(
        request_digest=request.request_digest,
        assistant_content="本 Provider attempt 未形成可授权答案。",
        included_user_message_ids=(
            *context.included_user_message_ids,
            request.user_message.message_id,
        ),
        accepted_correction_message_ids=context.accepted_correction_message_ids,
        reviewed_conclusion_refs=context.reviewed_conclusion_refs,
        superseded_conclusion_refs=context.superseded_conclusion_refs,
        reducer_status="ATTEMPT_FAILED_CLOSED",
        work_state_ref=context.work_state_ref,
        work_state_revision=(context.work_state_revision if context.work_state_ref else None),
        work_state_digest=context.work_state_digest,
        failure_code=code,
        failure_message="本 Provider attempt 未形成可授权答案。",
        provider_dispatch_count=dispatches,
        model_dispatch_receipt_refs=((receipt_ref,) if receipt_ref else ()),
        provider_failure_classification=classification,
        provider_failure_code=provider_code,
    )


def _success(request, *, provider: str, dispatches: int, receipt_ref: str):
    context = request.snapshot_before.context
    answer_ref = f"{provider}-answer"
    work_state_ref = context.work_state_ref or f"{provider}-work-state"
    work_state_revision = (
        context.work_state_revision.next()
        if context.work_state_ref
        else Revision(1)
    )
    work_state_digest = digest_of(
        [provider, request.request_digest.value, work_state_revision.value]
    )
    return EngineeringTurnExecutionOutcome.succeeded(
        request_digest=request.request_digest,
        assistant_kind=ConversationMessageKind.ANSWER,
        assistant_content=f"{provider} 完整答案",
        included_user_message_ids=(
            *context.included_user_message_ids,
            request.user_message.message_id,
        ),
        accepted_correction_message_ids=context.accepted_correction_message_ids,
        reviewed_conclusion_refs=(*context.reviewed_conclusion_refs, answer_ref),
        superseded_conclusion_refs=context.superseded_conclusion_refs,
        reducer_status="EXECUTED_APPLICATION_SEALED",
        work_state_ref=work_state_ref,
        work_state_revision=work_state_revision,
        work_state_digest=work_state_digest,
        evidence_package_ref=f"{provider}-package",
        answer_ref=answer_ref,
        review_ref=f"{provider}-review",
        delivery_authorization_ref=f"{provider}-delivery",
        provider_dispatch_count=dispatches,
        model_dispatch_receipt_refs=(receipt_ref,),
        quality_status="ACCEPTED",
    )


def _service(factory, *, standing_authority: bool = False):
    binding, plan = _binding_and_plan(
        standing_authority=standing_authority
    )
    router = ApplicationOwnedEngineeringProviderRouter(
        plan=plan,
        attempt_factory=factory,
        id_generator=SequentialIdGenerator("route"),
    )
    service = InMemoryEngineeringConversationService(
        binding,
        turn_executor=router,
        id_generator=SequentialIdGenerator("chat"),
    )
    return service, router


class ConversationalEngineeringRoutingTests(unittest.TestCase):
    def test_turn_attempt_authority_binds_public_source_standing_parent(self) -> None:
        factory = _Factory(
            {
                EngineeringProviderRouteRole.PRIMARY: lambda request: _success(
                    request,
                    provider="ark",
                    dispatches=1,
                    receipt_ref="ark-model-receipt",
                ),
                EngineeringProviderRouteRole.FALLBACK: lambda request: _failure(
                    request,
                    code="NOT_USED",
                ),
            }
        )
        service, _ = _service(factory, standing_authority=True)
        conversation = service.create_conversation()

        service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=Revision(1),
            message="登录流程是怎样的？",
        )

        self.assertEqual(len(factory.authorities), 1)
        self.assertEqual(
            factory.authorities[0].standing_authority_digest,
            digest_of("public-source-standing-authority"),
        )
        self.assertEqual(
            factory.authorities[0].schema,
            "ENGINEERING_PROVIDER_ATTEMPT_AUTHORITY@2",
        )

    def test_primary_success_does_not_start_fallback(self) -> None:
        factory = _Factory(
            {
                EngineeringProviderRouteRole.PRIMARY: lambda request: _success(
                    request,
                    provider="ark",
                    dispatches=2,
                    receipt_ref="ark-model-receipt",
                ),
                EngineeringProviderRouteRole.FALLBACK: lambda request: _success(
                    request,
                    provider="deepseek",
                    dispatches=2,
                    receipt_ref="deepseek-model-receipt",
                ),
            }
        )
        service, router = _service(factory)
        conversation = service.create_conversation()
        submission = service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=Revision(1),
            message="登录流程是怎样的？",
        )

        self.assertEqual(submission.turn.state, ConversationTurnState.SUCCEEDED)
        self.assertEqual(submission.turn.provider_dispatch_count, 2)
        self.assertEqual(submission.turn.fallback_provider_attempt_count, 0)
        self.assertEqual(len(submission.turn.provider_attempt_receipt_refs), 1)
        self.assertFalse(submission.turn.provider_duplicate_cost_risk)
        self.assertEqual(len(factory.authorities), 1)
        audit = router.audit_for(submission.turn.request_digest)
        self.assertEqual(audit.route_receipt.selected_provider_type, "VOLCENGINE_ARK")

    def test_http_failure_starts_one_fresh_fallback_from_original_turn(self) -> None:
        factory = _Factory(
            {
                EngineeringProviderRouteRole.PRIMARY: lambda request: _failure(
                    request,
                    code="AGENT_MODEL_CALL_REJECTED",
                    classification=(
                        EngineeringProviderFailureClassification.PROVIDER_HTTP_ERROR
                    ),
                    provider_code="PROVIDER_HTTP_ERROR",
                    dispatches=1,
                    receipt_ref="ark-http-receipt",
                ),
                EngineeringProviderRouteRole.FALLBACK: lambda request: _success(
                    request,
                    provider="deepseek",
                    dispatches=3,
                    receipt_ref="deepseek-success-receipt",
                ),
            }
        )
        service, router = _service(factory)
        conversation = service.create_conversation()
        submission = service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=Revision(1),
            message="登录流程是怎样的？",
        )

        self.assertEqual(submission.turn.state, ConversationTurnState.SUCCEEDED)
        self.assertEqual(submission.turn.provider_dispatch_count, 4)
        self.assertEqual(
            submission.turn.model_dispatch_receipt_refs,
            ("ark-http-receipt", "deepseek-success-receipt"),
        )
        self.assertEqual(submission.turn.fallback_provider_attempt_count, 1)
        self.assertEqual(len(submission.turn.provider_attempt_receipt_refs), 2)
        self.assertFalse(submission.turn.provider_duplicate_cost_risk)
        self.assertEqual(len(factory.authorities), 2)
        primary, fallback = factory.authorities
        self.assertEqual(
            primary.logical_turn_request_digest,
            fallback.logical_turn_request_digest,
        )
        self.assertEqual(
            primary.original_user_message_digest,
            fallback.original_user_message_digest,
        )
        self.assertEqual(
            primary.conversation_context_digest,
            fallback.conversation_context_digest,
        )
        self.assertNotEqual(
            primary.provider_configuration_digest,
            fallback.provider_configuration_digest,
        )
        self.assertFalse(primary.primary_intermediate_reuse_allowed)
        self.assertFalse(fallback.primary_intermediate_reuse_allowed)
        audit = router.audit_for(submission.turn.request_digest)
        self.assertEqual(audit.route_receipt.selected_provider_type, "DEEPSEEK")

    def test_outcome_unknown_fallback_records_duplicate_cost_risk(self) -> None:
        factory = _Factory(
            {
                EngineeringProviderRouteRole.PRIMARY: lambda request: _failure(
                    request,
                    code="AGENT_MODEL_OUTCOME_UNKNOWN",
                    classification=(
                        EngineeringProviderFailureClassification.PROVIDER_OUTCOME_UNKNOWN
                    ),
                    provider_code="PROVIDER_OUTCOME_UNKNOWN",
                    dispatches=1,
                    receipt_ref="ark-unknown-receipt",
                ),
                EngineeringProviderRouteRole.FALLBACK: lambda request: _success(
                    request,
                    provider="deepseek",
                    dispatches=2,
                    receipt_ref="deepseek-success-receipt",
                ),
            }
        )
        service, _ = _service(factory)
        conversation = service.create_conversation()
        submission = service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=Revision(1),
            message="继续解释登录流程。",
        )

        self.assertTrue(submission.turn.provider_duplicate_cost_risk)
        self.assertEqual(submission.turn.provider_dispatch_count, 3)
        self.assertEqual(submission.turn.fallback_provider_attempt_count, 1)

    def test_application_failure_never_starts_fallback(self) -> None:
        factory = _Factory(
            {
                EngineeringProviderRouteRole.PRIMARY: lambda request: _failure(
                    request,
                    code="AGENT_PROTOCOL_VIOLATION",
                ),
                EngineeringProviderRouteRole.FALLBACK: lambda request: _success(
                    request,
                    provider="deepseek",
                    dispatches=1,
                    receipt_ref="must-not-run",
                ),
            }
        )
        service, _ = _service(factory)
        conversation = service.create_conversation()
        submission = service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=Revision(1),
            message="登录流程是怎样的？",
        )

        self.assertEqual(submission.turn.state, ConversationTurnState.FAILED)
        self.assertEqual(submission.turn.fallback_provider_attempt_count, 0)
        self.assertEqual(len(factory.authorities), 1)

    def test_model_review_rejection_is_eligible_for_one_fallback(self) -> None:
        factory = _Factory(
            {
                EngineeringProviderRouteRole.PRIMARY: lambda request: _failure(
                    request,
                    code="AGENT_REVIEW_LIMIT_REACHED",
                    classification=(
                        EngineeringProviderFailureClassification.MODEL_REVIEW_REJECTED
                    ),
                    provider_code="AGENT_REVIEW_LIMIT_REACHED",
                    dispatches=4,
                    receipt_ref="ark-review-receipt",
                ),
                EngineeringProviderRouteRole.FALLBACK: lambda request: _success(
                    request,
                    provider="deepseek",
                    dispatches=2,
                    receipt_ref="deepseek-review-pass",
                ),
            }
        )
        service, _ = _service(factory)
        conversation = service.create_conversation()
        submission = service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=Revision(1),
            message="登录流程是怎样的？",
        )

        self.assertEqual(submission.turn.state, ConversationTurnState.SUCCEEDED)
        self.assertEqual(submission.turn.fallback_provider_attempt_count, 1)
        self.assertEqual(submission.turn.provider_dispatch_count, 6)

    def test_implementation_gap_is_not_provider_unavailable(self) -> None:
        factory = _FailingFactory()
        service, _ = _service(factory)
        conversation = service.create_conversation()
        submission = service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=Revision(1),
            message="登录流程是怎样的？",
        )

        self.assertEqual(submission.turn.state, ConversationTurnState.FAILED)
        self.assertEqual(
            submission.turn.failure_code,
            "PROVIDER_ATTEMPT_INITIALIZATION_FAILED",
        )
        self.assertIsNone(submission.turn.provider_failure_classification)
        self.assertEqual(submission.turn.fallback_provider_attempt_count, 0)
        self.assertEqual(len(factory.authorities), 1)

    def test_fallback_reusing_primary_runtime_fails_before_fallback_execution(self) -> None:
        factory = _Factory(
            {
                EngineeringProviderRouteRole.PRIMARY: lambda request: _failure(
                    request,
                    code="AGENT_MODEL_CALL_REJECTED",
                    classification=(
                        EngineeringProviderFailureClassification.PROVIDER_OUTPUT_INVALID
                    ),
                    provider_code="STRUCTURED_OUTPUT_INVALID",
                    dispatches=1,
                    receipt_ref="ark-invalid-output",
                ),
                EngineeringProviderRouteRole.FALLBACK: lambda request: _success(
                    request,
                    provider="deepseek",
                    dispatches=1,
                    receipt_ref="must-not-dispatch",
                ),
            },
            reuse_runtime=True,
        )
        service, _ = _service(factory)
        conversation = service.create_conversation()
        submission = service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=Revision(1),
            message="登录流程是怎样的？",
        )

        self.assertEqual(submission.turn.state, ConversationTurnState.FAILED)
        self.assertEqual(
            submission.turn.failure_code,
            "PROVIDER_ATTEMPT_INITIALIZATION_FAILED",
        )
        self.assertEqual(submission.turn.provider_dispatch_count, 1)
        self.assertEqual(submission.turn.fallback_provider_attempt_count, 1)
        self.assertEqual(len(factory.runtimes[0].executor.requests), 1)

    def test_provider_failure_classification_requires_raw_code(self) -> None:
        binding, _ = _binding_and_plan()
        service = InMemoryEngineeringConversationService(
            binding,
            turn_executor=_Executor(
                lambda request: _failure(
                    request,
                    code="AGENT_MODEL_CALL_REJECTED",
                    classification=(
                        EngineeringProviderFailureClassification.PROVIDER_HTTP_ERROR
                    ),
                    provider_code=None,
                )
            ),
            id_generator=SequentialIdGenerator("invalid"),
        )
        conversation = service.create_conversation()
        submission = service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=Revision(1),
            message="登录流程是怎样的？",
        )

        self.assertEqual(submission.turn.state, ConversationTurnState.FAILED)
        self.assertEqual(
            submission.turn.failure_code,
            "TURN_EXECUTOR_PROTOCOL_VIOLATION",
        )
        self.assertIsNone(submission.turn.provider_failure_classification)

    def test_route_plan_rejects_non_ark_primary_order(self) -> None:
        binding, plan = _binding_and_plan()
        primary, fallback = plan.routes
        wrong = EngineeringProviderRouteSpec.create(
            ordinal=1,
            role=EngineeringProviderRouteRole.PRIMARY,
            provider_type="DEEPSEEK",
            endpoint=primary.endpoint,
            model_ref=primary.model_ref,
            provider_configuration_digest=primary.provider_configuration_digest,
            session_disclosure_authority_digest=(
                primary.session_disclosure_authority_digest
            ),
            qualification_ref=primary.qualification_ref,
            maximum_dispatches_per_turn=primary.maximum_dispatches_per_turn,
        )

        with self.assertRaises(DomainError):
            EngineeringProviderRoutePlan.create(
                binding=binding,
                primary=wrong,
                fallback=fallback,
            )


if __name__ == "__main__":
    unittest.main()
