from __future__ import annotations

import ast
from datetime import datetime, timezone
from pathlib import Path
import unittest

from software_world_model.application_services.conversational_engineering_routing import (
    ENGINEERING_PROVIDER_ATTEMPT_COMPONENTS,
    ApplicationOwnedEngineeringProviderRouter,
    EngineeringExecutionProfileAvailabilityVerdict,
    EngineeringProviderAttemptRuntime,
    EngineeringProviderRoutePlan,
    EngineeringProviderRouteRole,
    EngineeringProviderRouteSpec,
    SealedExecutionProfileAvailabilityBoundary,
    engineering_agent_execution_profile_route_ref,
    engineering_agent_preferred_execution_profile_route_ref,
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


_PREFERRED_PROFILE_REF = "runtime-config:preferred-qualified-profile"
_FALLBACK_PROFILE_REF = "runtime-config:fallback-qualified-profile"
class SequentialIdGenerator:
    def __init__(self) -> None:
        self.value = 0

    def new(self, kind: str) -> StableId:
        self.value += 1
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


class _SealingAvailabilityBoundary:
    availability_owner_ref = "provider-availability-boundary"

    def __init__(self, *, enabled: bool = True) -> None:
        self.enabled = enabled
        self.calls = []

    def assess_preferred(
        self, *, request, route, preferred_attempt_receipt
    ):
        self.calls.append(
            (request.request_digest, route.digest, preferred_attempt_receipt.digest)
        )
        if not self.enabled:
            return None
        return EngineeringExecutionProfileAvailabilityVerdict.seal(
            availability_owner_ref=self.availability_owner_ref,
            request=request,
            route=route,
            preferred_attempt_receipt=preferred_attempt_receipt,
            assessed_at=request.requested_at,
        )


def _profile_digest(identity: str) -> Digest:
    return digest_of(["qualified-execution-profile", identity])


def _binding_and_plan(
    *,
    preferred_identity: str = "virtual-model-a",
    fallback_identity: str = "virtual-model-b",
    standing_authority: bool = False,
):
    preferred_digest = _profile_digest(preferred_identity)
    fallback_digest = _profile_digest(fallback_identity)
    route_ref = engineering_agent_execution_profile_route_ref(
        preferred_execution_profile_ref=_PREFERRED_PROFILE_REF,
        preferred_execution_profile_digest=preferred_digest,
        fallback_execution_profile_ref=_FALLBACK_PROFILE_REF,
        fallback_execution_profile_digest=fallback_digest,
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
    preferred = EngineeringProviderRouteSpec.create(
        ordinal=1,
        role=EngineeringProviderRouteRole.PREFERRED,
        execution_profile_ref=_PREFERRED_PROFILE_REF,
        execution_profile_digest=preferred_digest,
        session_disclosure_authority_digest=digest_of("preferred-session"),
        standing_authority_digest=standing_digest,
        maximum_dispatches_per_turn=15,
    )
    fallback = EngineeringProviderRouteSpec.create(
        ordinal=2,
        role=EngineeringProviderRouteRole.FALLBACK,
        execution_profile_ref=_FALLBACK_PROFILE_REF,
        execution_profile_digest=fallback_digest,
        session_disclosure_authority_digest=digest_of("fallback-session"),
        standing_authority_digest=standing_digest,
        maximum_dispatches_per_turn=15,
    )
    return binding, EngineeringProviderRoutePlan.create(
        binding=binding,
        preferred=preferred,
        fallback=fallback,
    )


def _preferred_only_binding_and_plan():
    preferred_digest = _profile_digest("virtual-model-a")
    route_ref = engineering_agent_preferred_execution_profile_route_ref(
        preferred_execution_profile_ref=_PREFERRED_PROFILE_REF,
        preferred_execution_profile_digest=preferred_digest,
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
        known_limitations=("Preferred-only experimental route",),
    )
    preferred = EngineeringProviderRouteSpec.create(
        ordinal=1,
        role=EngineeringProviderRouteRole.PREFERRED,
        execution_profile_ref=_PREFERRED_PROFILE_REF,
        execution_profile_digest=preferred_digest,
        session_disclosure_authority_digest=digest_of("preferred-session"),
        maximum_dispatches_per_turn=15,
    )
    return binding, EngineeringProviderRoutePlan.create(
        binding=binding,
        preferred=preferred,
    )


def _failure(
    request,
    *,
    code: str,
    classification: EngineeringProviderFailureClassification | None = None,
    provider_code: str | None = None,
    provider_http_status: int | None = None,
    provider_http_failure_evidence_digest: Digest | None = None,
    dispatches: int = 0,
    receipt_ref: str | None = None,
):
    context = request.snapshot_before.context
    return EngineeringTurnExecutionOutcome.failed(
        request_digest=request.request_digest,
        assistant_content="本执行配置未形成可授权答案。",
        included_user_message_ids=(
            *context.included_user_message_ids,
            request.user_message.message_id,
        ),
        accepted_correction_message_ids=context.accepted_correction_message_ids,
        reviewed_conclusion_refs=context.reviewed_conclusion_refs,
        superseded_conclusion_refs=context.superseded_conclusion_refs,
        reducer_status="ATTEMPT_FAILED_CLOSED",
        work_state_ref=context.work_state_ref,
        work_state_revision=(
            context.work_state_revision if context.work_state_ref else None
        ),
        work_state_digest=context.work_state_digest,
        failure_code=code,
        failure_message="本执行配置未形成可授权答案。",
        provider_dispatch_count=dispatches,
        model_dispatch_receipt_refs=((receipt_ref,) if receipt_ref else ()),
        provider_failure_classification=classification,
        provider_failure_code=provider_code,
        provider_http_status=provider_http_status,
        provider_http_failure_evidence_digest=(
            provider_http_failure_evidence_digest
        ),
    )


def _success(request, *, label: str, dispatches: int, receipt_ref: str):
    context = request.snapshot_before.context
    answer_ref = f"{label}-answer"
    work_state_ref = context.work_state_ref or f"{label}-work-state"
    work_state_revision = (
        context.work_state_revision.next()
        if context.work_state_ref
        else Revision(1)
    )
    work_state_digest = digest_of(
        [label, request.request_digest.value, work_state_revision.value]
    )
    return EngineeringTurnExecutionOutcome.succeeded(
        request_digest=request.request_digest,
        assistant_kind=ConversationMessageKind.ANSWER,
        assistant_content=f"{label} 完整答案",
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
        evidence_package_ref=f"{label}-package",
        answer_ref=answer_ref,
        review_ref=f"{label}-review",
        delivery_authorization_ref=f"{label}-delivery",
        provider_dispatch_count=dispatches,
        model_dispatch_receipt_refs=(receipt_ref,),
        quality_status="ACCEPTED",
    )


def _service(
    factory,
    *,
    availability_boundary=None,
    preferred_identity: str = "virtual-model-a",
    fallback_identity: str = "virtual-model-b",
    standing_authority: bool = False,
):
    binding, plan = _binding_and_plan(
        preferred_identity=preferred_identity,
        fallback_identity=fallback_identity,
        standing_authority=standing_authority,
    )
    router = ApplicationOwnedEngineeringProviderRouter(
        plan=plan,
        attempt_factory=factory,
        availability_boundary=availability_boundary,
        id_generator=SequentialIdGenerator(),
    )
    service = InMemoryEngineeringConversationService(
        binding,
        turn_executor=router,
        id_generator=SequentialIdGenerator(),
    )
    return service, router


def _submit(service):
    conversation = service.create_conversation()
    return service.submit_turn(
        conversation_id=conversation.conversation.conversation_id,
        expected_revision=Revision(1),
        message="登录流程是怎样的？",
    )


def _preferred_failure(
    classification,
    code,
    *,
    receipt_ref="preferred-failure",
    provider_http_status=None,
    provider_http_failure_evidence_digest=None,
):
    return {
        EngineeringProviderRouteRole.PREFERRED: lambda request: _failure(
            request,
            code="AGENT_MODEL_CALL_REJECTED",
            classification=classification,
            provider_code=code,
            provider_http_status=provider_http_status,
            provider_http_failure_evidence_digest=(
                provider_http_failure_evidence_digest
            ),
            dispatches=1,
            receipt_ref=receipt_ref,
        ),
        EngineeringProviderRouteRole.FALLBACK: lambda request: _success(
            request,
            label="fallback",
            dispatches=2,
            receipt_ref="fallback-success",
        ),
    }


class ConversationalEngineeringRoutingTests(unittest.TestCase):
    def test_preferred_only_route_executes_without_constructing_fallback(self) -> None:
        binding, plan = _preferred_only_binding_and_plan()
        factory = _Factory(
            {
                EngineeringProviderRouteRole.PREFERRED: lambda request: _success(
                    request,
                    label="preferred-only",
                    dispatches=1,
                    receipt_ref="preferred-only-success",
                ),
                EngineeringProviderRouteRole.FALLBACK: lambda request: self.fail(
                    "preferred-only route must not construct a fallback"
                ),
            }
        )
        router = ApplicationOwnedEngineeringProviderRouter(
            plan=plan,
            attempt_factory=factory,
            id_generator=SequentialIdGenerator(),
        )
        service = InMemoryEngineeringConversationService(
            binding,
            turn_executor=router,
            id_generator=SequentialIdGenerator(),
        )
        submission = _submit(service)

        self.assertEqual(submission.turn.state, ConversationTurnState.SUCCEEDED)
        self.assertEqual(submission.turn.fallback_provider_attempt_count, 0)
        self.assertEqual(len(plan.routes), 1)
        self.assertEqual(len(factory.authorities), 1)

    def test_preferred_only_unavailable_fails_closed_without_fallback_verdict(self) -> None:
        boundary = _SealingAvailabilityBoundary()
        factory = _Factory(
            {
                EngineeringProviderRouteRole.PREFERRED: lambda request: _failure(
                    request,
                    code="PROFILE_TEMPORARILY_UNAVAILABLE",
                    classification=(
                        EngineeringProviderFailureClassification.PROVIDER_UNAVAILABLE
                    ),
                    dispatches=0,
                    receipt_ref="preferred-only-unavailable",
                ),
                EngineeringProviderRouteRole.FALLBACK: lambda request: self.fail(
                    "preferred-only unavailable route must remain fail-closed"
                ),
            }
        )
        binding, plan = _preferred_only_binding_and_plan()
        router = ApplicationOwnedEngineeringProviderRouter(
            plan=plan,
            attempt_factory=factory,
            availability_boundary=boundary,
            id_generator=SequentialIdGenerator(),
        )
        service = InMemoryEngineeringConversationService(
            binding,
            turn_executor=router,
            id_generator=SequentialIdGenerator(),
        )
        submission = _submit(service)

        self.assertEqual(submission.turn.state, ConversationTurnState.FAILED)
        self.assertEqual(submission.turn.fallback_provider_attempt_count, 0)
        self.assertIsNone(submission.turn.provider_availability_verdict_ref)
        self.assertEqual(len(factory.authorities), 1)
        self.assertEqual(boundary.calls, [])

    def test_attempt_authority_binds_public_source_standing_parent(self) -> None:
        factory = _Factory(
            {
                EngineeringProviderRouteRole.PREFERRED: lambda request: _success(
                    request,
                    label="preferred",
                    dispatches=1,
                    receipt_ref="preferred-success",
                ),
                EngineeringProviderRouteRole.FALLBACK: lambda request: _failure(
                    request,
                    code="NOT_USED",
                ),
            }
        )
        service, _ = _service(factory, standing_authority=True)
        _submit(service)

        self.assertEqual(len(factory.authorities), 1)
        self.assertEqual(
            factory.authorities[0].standing_authority_digest,
            digest_of("public-source-standing-authority"),
        )
        self.assertEqual(
            factory.authorities[0].schema,
            "ENGINEERING_EXECUTION_PROFILE_ATTEMPT_AUTHORITY@2",
        )

    def test_preferred_success_does_not_start_fallback(self) -> None:
        factory = _Factory(
            {
                EngineeringProviderRouteRole.PREFERRED: lambda request: _success(
                    request,
                    label="preferred",
                    dispatches=2,
                    receipt_ref="preferred-success",
                ),
                EngineeringProviderRouteRole.FALLBACK: lambda request: _success(
                    request,
                    label="fallback",
                    dispatches=2,
                    receipt_ref="must-not-run",
                ),
            }
        )
        service, router = _service(factory)
        submission = _submit(service)

        self.assertEqual(submission.turn.state, ConversationTurnState.SUCCEEDED)
        self.assertEqual(submission.turn.provider_dispatch_count, 2)
        self.assertEqual(submission.turn.fallback_provider_attempt_count, 0)
        self.assertIsNone(submission.turn.provider_availability_verdict_ref)
        self.assertEqual(len(factory.authorities), 1)
        audit = router.audit_for(submission.turn.request_digest)
        self.assertEqual(
            audit.route_receipt.selected_execution_profile_ref,
            _PREFERRED_PROFILE_REF,
        )

    def test_raw_http_failure_without_availability_verdict_fails_closed(self) -> None:
        boundary = _SealingAvailabilityBoundary(enabled=False)
        factory = _Factory(
            _preferred_failure(
                EngineeringProviderFailureClassification.PROVIDER_HTTP_ERROR,
                "HTTP_503",
            )
        )
        service, _ = _service(factory, availability_boundary=boundary)
        submission = _submit(service)

        self.assertEqual(submission.turn.state, ConversationTurnState.FAILED)
        self.assertEqual(submission.turn.fallback_provider_attempt_count, 0)
        self.assertIsNone(submission.turn.provider_availability_verdict_ref)
        self.assertEqual(len(factory.authorities), 1)
        self.assertEqual(len(boundary.calls), 1)

    def test_unregistered_availability_owner_is_rejected_at_composition(self) -> None:
        factory = _Factory(
            _preferred_failure(
                EngineeringProviderFailureClassification.PROVIDER_UNAVAILABLE,
                "PROFILE_TEMPORARILY_UNAVAILABLE",
            )
        )
        boundary = _SealingAvailabilityBoundary()
        boundary.availability_owner_ref = "unregistered-owner"

        with self.assertRaises(DomainError):
            _service(factory, availability_boundary=boundary)

    def test_raw_outcome_unknown_without_verdict_fails_closed(self) -> None:
        factory = _Factory(
            _preferred_failure(
                EngineeringProviderFailureClassification.PROVIDER_OUTCOME_UNKNOWN,
                "CONNECTION_CLOSED_AFTER_SEND",
            )
        )
        service, _ = _service(factory)
        submission = _submit(service)

        self.assertEqual(submission.turn.fallback_provider_attempt_count, 0)
        self.assertFalse(submission.turn.provider_duplicate_cost_risk)
        self.assertIsNone(submission.turn.provider_availability_verdict_ref)

    def test_exact_sealed_unavailable_verdict_permits_one_fallback(self) -> None:
        boundary = _SealingAvailabilityBoundary()
        factory = _Factory(
            _preferred_failure(
                EngineeringProviderFailureClassification.PROVIDER_UNAVAILABLE,
                "ACCOUNT_MODEL_TEMPORARILY_UNAVAILABLE",
            )
        )
        service, router = _service(factory, availability_boundary=boundary)
        submission = _submit(service)

        self.assertEqual(submission.turn.state, ConversationTurnState.SUCCEEDED)
        self.assertEqual(submission.turn.provider_dispatch_count, 3)
        self.assertEqual(submission.turn.fallback_provider_attempt_count, 1)
        self.assertIsNotNone(submission.turn.provider_availability_verdict_ref)
        self.assertEqual(len(factory.authorities), 2)
        preferred, fallback = factory.authorities
        self.assertEqual(
            preferred.logical_turn_request_digest,
            fallback.logical_turn_request_digest,
        )
        self.assertNotEqual(
            preferred.execution_profile_digest,
            fallback.execution_profile_digest,
        )
        audit = router.audit_for(submission.turn.request_digest)
        self.assertEqual(
            submission.turn.provider_availability_verdict_ref,
            audit.preferred_availability_verdict.digest.value,
        )
        self.assertEqual(
            audit.route_receipt.selected_execution_profile_ref,
            _FALLBACK_PROFILE_REF,
        )

    def test_route_receipt_rejects_combined_dispatches_above_turn_fuse(
        self,
    ) -> None:
        boundary = _SealingAvailabilityBoundary()
        builders = _preferred_failure(
            EngineeringProviderFailureClassification.PROVIDER_UNAVAILABLE,
            "ACCOUNT_MODEL_TEMPORARILY_UNAVAILABLE",
        )
        builders[EngineeringProviderRouteRole.FALLBACK] = (
            lambda request: _success(
                request,
                label="fallback",
                dispatches=15,
                receipt_ref="fallback-success",
            )
        )
        factory = _Factory(builders)
        service, _ = _service(factory, availability_boundary=boundary)

        submission = _submit(service)

        self.assertEqual(submission.turn.state, ConversationTurnState.FAILED)
        self.assertEqual(submission.turn.failure_code, "AGENT_EXECUTION_FAILED")
        self.assertEqual(submission.turn.provider_dispatch_count, 0)
        self.assertEqual(len(factory.authorities), 2)

    def test_real_owner_promotes_only_gateway_sealed_pre_dispatch_unavailability(self) -> None:
        boundary = SealedExecutionProfileAvailabilityBoundary(
            clock=lambda: datetime(2099, 1, 1, tzinfo=timezone.utc),
        )
        factory = _Factory(
            _preferred_failure(
                EngineeringProviderFailureClassification.PROVIDER_UNAVAILABLE,
                "PROVIDER_UNAVAILABLE",
            )
        )
        service, router = _service(
            factory,
            availability_boundary=boundary,
        )
        submission = _submit(service)

        self.assertEqual(submission.turn.state, ConversationTurnState.SUCCEEDED)
        self.assertEqual(submission.turn.fallback_provider_attempt_count, 1)
        self.assertEqual(len(factory.authorities), 2)
        audit = router.audit_for(submission.turn.request_digest)
        self.assertIsNotNone(audit.preferred_availability_verdict)
        self.assertEqual(
            audit.preferred_availability_verdict.raw_failure_code,
            "PROVIDER_UNAVAILABLE",
        )
        self.assertFalse(
            audit.preferred_availability_verdict.potential_duplicate_cost_risk
        )

    def test_real_owner_promotes_gateway_sealed_unavailable_http_status(self) -> None:
        evidence_digest = digest_of("gateway-sealed-http-503")
        boundary = SealedExecutionProfileAvailabilityBoundary(
            clock=lambda: datetime(2099, 1, 1, tzinfo=timezone.utc),
        )
        factory = _Factory(
            _preferred_failure(
                EngineeringProviderFailureClassification.PROVIDER_HTTP_ERROR,
                "PROVIDER_HTTP_ERROR",
                provider_http_status=503,
                provider_http_failure_evidence_digest=evidence_digest,
            )
        )
        service, router = _service(factory, availability_boundary=boundary)

        submission = _submit(service)

        self.assertEqual(submission.turn.state, ConversationTurnState.SUCCEEDED)
        self.assertEqual(submission.turn.fallback_provider_attempt_count, 1)
        self.assertEqual(len(factory.authorities), 2)
        verdict = router.audit_for(
            submission.turn.request_digest
        ).preferred_availability_verdict
        self.assertIsNotNone(verdict)
        assert verdict is not None
        self.assertEqual(verdict.raw_http_status, 503)
        self.assertEqual(verdict.raw_failure_evidence_digest, evidence_digest)
        self.assertFalse(verdict.potential_duplicate_cost_risk)

    def test_real_owner_treats_current_profile_payment_required_as_unavailable(self) -> None:
        boundary = SealedExecutionProfileAvailabilityBoundary(
            clock=lambda: datetime(2099, 1, 1, tzinfo=timezone.utc),
        )
        factory = _Factory(
            _preferred_failure(
                EngineeringProviderFailureClassification.PROVIDER_HTTP_ERROR,
                "PROVIDER_HTTP_ERROR",
                provider_http_status=402,
                provider_http_failure_evidence_digest=digest_of(
                    "gateway-sealed-http-402"
                ),
            )
        )
        service, _ = _service(factory, availability_boundary=boundary)

        submission = _submit(service)

        self.assertEqual(submission.turn.state, ConversationTurnState.SUCCEEDED)
        self.assertEqual(submission.turn.fallback_provider_attempt_count, 1)
        self.assertEqual(len(factory.authorities), 2)

    def test_real_owner_rejects_auth_config_and_unsealed_http_failures(self) -> None:
        cases = (
            (400, digest_of("http-400")),
            (401, digest_of("http-401")),
            (403, digest_of("http-403")),
            (404, digest_of("http-404")),
            (409, digest_of("http-409")),
            (422, digest_of("http-422")),
            (503, None),
        )
        for status, evidence_digest in cases:
            with self.subTest(status=status, sealed=evidence_digest is not None):
                factory = _Factory(
                    _preferred_failure(
                        EngineeringProviderFailureClassification.PROVIDER_HTTP_ERROR,
                        "PROVIDER_HTTP_ERROR",
                        provider_http_status=(
                            status if evidence_digest is not None else None
                        ),
                        provider_http_failure_evidence_digest=evidence_digest,
                    )
                )
                service, _ = _service(
                    factory,
                    availability_boundary=(
                        SealedExecutionProfileAvailabilityBoundary(
                            clock=lambda: datetime(
                                2099, 1, 1, tzinfo=timezone.utc
                            )
                        )
                    ),
                )

                submission = _submit(service)

                self.assertEqual(
                    submission.turn.state,
                    ConversationTurnState.FAILED,
                )
                self.assertEqual(
                    submission.turn.fallback_provider_attempt_count,
                    0,
                )
                self.assertEqual(len(factory.authorities), 1)

    def test_real_owner_rejects_noncanonical_or_non_predispatch_raw_evidence(self) -> None:
        cases = (
            (
                EngineeringProviderFailureClassification.PROVIDER_UNAVAILABLE,
                "TLS_FAILURE",
                1,
                "untrusted-unavailable-code",
            ),
            (
                EngineeringProviderFailureClassification.PROVIDER_HTTP_ERROR,
                "PROVIDER_UNAVAILABLE",
                1,
                "http-error",
            ),
            (
                EngineeringProviderFailureClassification.PROVIDER_OUTCOME_UNKNOWN,
                "PROVIDER_UNAVAILABLE",
                1,
                "outcome-unknown",
            ),
            (
                EngineeringProviderFailureClassification.PROVIDER_UNAVAILABLE,
                "PROVIDER_UNAVAILABLE",
                0,
                None,
            ),
        )
        for classification, code, dispatches, receipt_ref in cases:
            with self.subTest(
                classification=classification,
                code=code,
                dispatches=dispatches,
            ):
                factory = _Factory(
                    {
                        EngineeringProviderRouteRole.PREFERRED: (
                            lambda request,
                            classification=classification,
                            code=code,
                            dispatches=dispatches,
                            receipt_ref=receipt_ref: _failure(
                                request,
                                code="AGENT_MODEL_CALL_REJECTED",
                                classification=classification,
                                provider_code=code,
                                dispatches=dispatches,
                                receipt_ref=receipt_ref,
                            )
                        ),
                        EngineeringProviderRouteRole.FALLBACK: lambda request: _success(
                            request,
                            label="must-not-run",
                            dispatches=1,
                            receipt_ref="must-not-run",
                        ),
                    }
                )
                service, _ = _service(
                    factory,
                    availability_boundary=(
                        SealedExecutionProfileAvailabilityBoundary(
                            clock=lambda: datetime(
                                2099, 1, 1, tzinfo=timezone.utc
                            ),
                        )
                    ),
                )
                submission = _submit(service)

                self.assertEqual(
                    submission.turn.state,
                    ConversationTurnState.FAILED,
                )
                self.assertEqual(
                    submission.turn.fallback_provider_attempt_count,
                    0,
                )
                self.assertEqual(len(factory.authorities), 1)

    def test_outcome_unknown_verdict_records_duplicate_cost_risk(self) -> None:
        factory = _Factory(
            _preferred_failure(
                EngineeringProviderFailureClassification.PROVIDER_OUTCOME_UNKNOWN,
                "CONNECTION_CLOSED_AFTER_SEND",
            )
        )
        service, _ = _service(
            factory,
            availability_boundary=_SealingAvailabilityBoundary(),
        )
        submission = _submit(service)

        self.assertTrue(submission.turn.provider_duplicate_cost_risk)
        self.assertEqual(submission.turn.fallback_provider_attempt_count, 1)

    def test_structured_output_invalid_never_authorizes_fallback(self) -> None:
        boundary = _SealingAvailabilityBoundary()
        factory = _Factory(
            _preferred_failure(
                EngineeringProviderFailureClassification.PROVIDER_OUTPUT_INVALID,
                "STRUCTURED_OUTPUT_INVALID",
            )
        )
        service, _ = _service(factory, availability_boundary=boundary)
        submission = _submit(service)

        self.assertEqual(submission.turn.state, ConversationTurnState.FAILED)
        self.assertEqual(submission.turn.fallback_provider_attempt_count, 0)
        self.assertIsNone(submission.turn.provider_availability_verdict_ref)
        self.assertEqual(len(factory.authorities), 1)

    def test_reviewer_rejection_never_authorizes_fallback(self) -> None:
        factory = _Factory(
            _preferred_failure(
                EngineeringProviderFailureClassification.MODEL_REVIEW_REJECTED,
                "AGENT_REVIEW_LIMIT_REACHED",
            )
        )
        service, _ = _service(
            factory,
            availability_boundary=_SealingAvailabilityBoundary(),
        )
        submission = _submit(service)

        self.assertEqual(submission.turn.state, ConversationTurnState.FAILED)
        self.assertEqual(submission.turn.fallback_provider_attempt_count, 0)
        self.assertEqual(len(factory.authorities), 1)

    def test_swapping_virtual_profile_identities_does_not_change_branch(self) -> None:
        outcomes = []
        for preferred_identity, fallback_identity in (
            ("virtual-model-a", "virtual-model-b"),
            ("virtual-model-b", "virtual-model-a"),
        ):
            factory = _Factory(
                _preferred_failure(
                    EngineeringProviderFailureClassification.PROVIDER_UNAVAILABLE,
                    "PROFILE_TEMPORARILY_UNAVAILABLE",
                )
            )
            service, _ = _service(
                factory,
                availability_boundary=_SealingAvailabilityBoundary(),
                preferred_identity=preferred_identity,
                fallback_identity=fallback_identity,
            )
            submission = _submit(service)
            outcomes.append(
                (
                    submission.turn.state,
                    submission.turn.fallback_provider_attempt_count,
                    submission.turn.provider_dispatch_count,
                    tuple(item.role for item in factory.authorities),
                )
            )

        self.assertEqual(outcomes[0], outcomes[1])

    def test_fallback_must_use_a_fresh_complete_runtime(self) -> None:
        factory = _Factory(
            _preferred_failure(
                EngineeringProviderFailureClassification.PROVIDER_UNAVAILABLE,
                "PROFILE_TEMPORARILY_UNAVAILABLE",
            ),
            reuse_runtime=True,
        )
        service, _ = _service(
            factory,
            availability_boundary=_SealingAvailabilityBoundary(),
        )
        submission = _submit(service)

        self.assertEqual(submission.turn.state, ConversationTurnState.FAILED)
        self.assertEqual(
            submission.turn.failure_code,
            "PROVIDER_ATTEMPT_INITIALIZATION_FAILED",
        )
        self.assertEqual(submission.turn.fallback_provider_attempt_count, 1)
        self.assertEqual(len(factory.runtimes[0].executor.requests), 1)

    def test_implementation_gap_is_not_profile_unavailable(self) -> None:
        factory = _FailingFactory()
        service, _ = _service(
            factory,
            availability_boundary=_SealingAvailabilityBoundary(),
        )
        submission = _submit(service)

        self.assertEqual(submission.turn.state, ConversationTurnState.FAILED)
        self.assertEqual(
            submission.turn.failure_code,
            "PROVIDER_ATTEMPT_INITIALIZATION_FAILED",
        )
        self.assertIsNone(submission.turn.provider_failure_classification)
        self.assertEqual(submission.turn.fallback_provider_attempt_count, 0)

    def test_route_plan_rejects_duplicate_or_misordered_profiles(self) -> None:
        binding, plan = _binding_and_plan()
        preferred, fallback = plan.routes
        duplicate = EngineeringProviderRouteSpec.create(
            ordinal=2,
            role=EngineeringProviderRouteRole.FALLBACK,
            execution_profile_ref=preferred.execution_profile_ref,
            execution_profile_digest=preferred.execution_profile_digest,
            session_disclosure_authority_digest=(
                fallback.session_disclosure_authority_digest
            ),
            maximum_dispatches_per_turn=15,
        )

        with self.assertRaises(DomainError):
            EngineeringProviderRoutePlan.create(
                binding=binding,
                preferred=preferred,
                fallback=duplicate,
            )

    def test_product_router_has_no_concrete_provider_or_model_branch(self) -> None:
        source_path = Path(
            "src/software_world_model/application_services/"
            "conversational_engineering_routing.py"
        )
        source = source_path.read_text(encoding="utf-8")
        tree = ast.parse(source)

        forbidden_literals = {
            "VOLCENGINE_ARK",
            "DEEPSEEK",
            "ark-model",
            "deepseek-model",
        }
        self.assertFalse(
            any(
                isinstance(node, ast.Constant)
                and isinstance(node.value, str)
                and node.value in forbidden_literals
                for node in ast.walk(tree)
            )
        )
        forbidden_attributes = {
            "provider_type",
            "model_ref",
            "provider_identity",
            "model_identity",
        }
        self.assertFalse(
            any(
                isinstance(node, ast.Attribute)
                and node.attr in forbidden_attributes
                for node in ast.walk(tree)
            )
        )


if __name__ == "__main__":
    unittest.main()
