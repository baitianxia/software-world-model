from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from types import SimpleNamespace
import unittest

from software_world_model.ai_infrastructure.conversational_engineering_model import (
    EngineeringAgentModelConfiguration,
    EngineeringAgentSessionDisclosureAuthority,
    ModelBackedConversationalEngineeringAgent,
    PolicyEnforcingEngineeringAgentModelGateway,
    SealedEngineeringAgentRoleDisclosureAuthorizer,
    _primary_input_view,
    decode_engineering_agent_primary_output,
    decode_engineering_agent_review_output,
)
from software_world_model.ai_infrastructure.model_gateway import (
    AdapterConformanceLevel,
    AdapterResponse,
    ModelGateway,
    ProviderAdapterCapabilities,
    ProviderOutcomeUnknown,
    ProviderUnavailable,
    ReplayClassification,
)
from software_world_model.application_services.conversational_engineering_agent import (
    ApplicationOwnedEngineeringAgentTurnExecutor,
    EngineeringAgentDeliveryAuthorization,
    EngineeringAgentEvidenceDisposition,
    EngineeringAgentInvocation,
    EngineeringAgentLoopLimits,
    EngineeringAgentModelDispatchState,
    EngineeringAgentModelFailureKind,
    EngineeringAgentToolOperation,
    EngineeringAgentToolObservation,
)
from software_world_model.application_services.engineering_conversation import (
    ConversationTurnState,
    EngineeringChatBinding,
    EngineeringProviderFailureClassification,
    EngineeringTurnExecutionOutcome,
    InMemoryEngineeringConversationService,
    RuntimeCapabilityStatus,
)
from software_world_model.cross_cutting import (
    DomainError,
    ErrorCode,
    Revision,
    StableId,
    digest_of,
)
from software_world_model.infrastructure import (
    SqliteDatabase,
    SqliteModelGatewayRepository,
)


class SequenceIds:
    def __init__(self) -> None:
        self.value = 0

    def new(self, kind: str) -> StableId:
        self.value += 1
        return StableId(f"{kind}_{self.value:032x}")


class OfflineAgentAdapter:
    provider_type = "AGENT_OFFLINE_FIXTURE"
    adapter_version = "1"

    def __init__(
        self,
        *,
        outcome_unknown: bool = False,
        provider_unavailable: bool = False,
        failure_code: ErrorCode | None = None,
    ) -> None:
        self.capabilities = ProviderAdapterCapabilities(
            no_external_access=True,
            hidden_context_disabled=True,
            stateless_session=True,
            structured_output=True,
            actual_fingerprint_reported=True,
            conformance_level=AdapterConformanceLevel.OFFLINE_FIXTURE,
            conformance_result_ref="CC-AGENT-OFFLINE-FIXTURE",
            qualified_model_fingerprints=(),
        )
        self.outcome_unknown = outcome_unknown
        self.provider_unavailable = provider_unavailable
        self.failure_code = failure_code
        self.requests = []

    def invoke(self, request):
        self.requests.append(request)
        if self.outcome_unknown:
            raise ProviderOutcomeUnknown("fixture connection outcome unknown")
        if self.provider_unavailable:
            raise ProviderUnavailable(
                "fixture provider unavailable",
                reason_code="CONNECTION_REFUSED",
            )
        if self.failure_code is not None:
            raise DomainError(self.failure_code, "fixture Provider failure")
        return AdapterResponse.create(
            provider_request_id="agent-fixture-request-1",
            actual_model_fingerprint="agent-fixture-model@1",
            replay_classification=ReplayClassification.PINNED,
            output_text=json.dumps(
                {
                    "goal": "登录流程是怎样的？",
                    "response_language": "zh-CN",
                    "audience": "software engineer",
                    "constraints": [],
                    "resolved_referents": [],
                    "accepted_correction_message_ids": [],
                    "superseded_conclusion_refs": [],
                    "hypotheses": [],
                    "plan": [],
                    "observation_ids": [],
                    "open_items": [],
                    "phase": "RESPONSE_READY",
                    "action": None,
                    "draft": {
                        "response_kind": "CLARIFICATION",
                        "content": "请明确登录入口。",
                        "claims": [],
                        "boundary_observation_ids": [],
                    },
                },
                ensure_ascii=False,
            ),
            input_tokens=20,
            output_tokens=12,
            usage_complete=True,
            termination_reason="stop",
        )


class UnusedToolPort:
    def __init__(self) -> None:
        self.requests = []

    def execute(self, request):
        self.requests.append(request)
        raise AssertionError("model failure must precede tool execution")


class UnusedResponseControl:
    def __init__(self) -> None:
        self.requests = []

    def authorize(self, request):
        self.requests.append(request)
        return EngineeringAgentDeliveryAuthorization.create(
            authorization_ref="unused-delivery",
            turn_request_digest=request.turn_request_digest,
            work_state_digest=request.work_state.digest,
            package_digest=request.package.digest,
            answer_digest=request.draft.digest,
            review_digest=request.review.digest,
        )


class CapturingTurnExecutor:
    def __init__(self) -> None:
        self.request = None

    def execute(self, request):
        self.request = request
        return EngineeringTurnExecutionOutcome.failed(
            request_digest=request.request_digest,
            assistant_content="captured",
            included_user_message_ids=(request.user_message.message_id,),
            failure_code="CAPTURED",
            failure_message="captured",
        )


def _binding() -> EngineeringChatBinding:
    return EngineeringChatBinding.create(
        product_revision="a" * 40,
        project_name="mall",
        repository_revision="b" * 40,
        world_model_status=RuntimeCapabilityStatus.READY,
        world_model_authority_digest=digest_of("world-model"),
        source_profile_ref="source-profile@1",
        source_access_status=RuntimeCapabilityStatus.READY,
        provider_status=RuntimeCapabilityStatus.READY,
        provider_route_ref="offline-agent-route@1",
        known_limitations=("local deterministic candidate only",),
    )


def _configuration(now: datetime) -> EngineeringAgentModelConfiguration:
    return EngineeringAgentModelConfiguration(
        provider_type=OfflineAgentAdapter.provider_type,
        adapter_version=OfflineAgentAdapter.adapter_version,
        endpoint="https://provider.invalid/v1/chat",
        model_ref="agent-fixture-model@1",
        expected_actual_model_fingerprint="agent-fixture-model@1",
        provider_configuration_fingerprint=digest_of("agent-fixture-config"),
        secret_reference="env:AGENT_FIXTURE_API_KEY",
        qualification_ref="CC-AGENT-OFFLINE-FIXTURE",
        qualification_valid_until=now + timedelta(hours=2),
        maximum_calls=12,
    )


class ConversationalEngineeringModelTests(unittest.TestCase):
    def setUp(self) -> None:
        self.now = datetime(2026, 8, 25, 8, tzinfo=timezone.utc)
        self.database = SqliteDatabase()
        self.addCleanup(self.database.close)

    def _service(
        self,
        *,
        outcome_unknown: bool = False,
        provider_unavailable: bool = False,
        failure_code: ErrorCode | None = None,
        authority_binding_digest=None,
    ):
        binding = _binding()
        configuration = _configuration(self.now)
        message_digest = digest_of("local deterministic disclosure fixture")
        authority = EngineeringAgentSessionDisclosureAuthority.create(
            session_ref="agent-session-fixture",
            product_candidate_digest=digest_of("product-candidate"),
            chat_binding_digest=(
                authority_binding_digest
                if authority_binding_digest is not None
                else binding.digest
            ),
            configuration=configuration,
            maximum_turns=3,
            maximum_dispatches_per_turn=12,
            maximum_total_dispatches=12,
            authorized_at=self.now,
            expires_at=self.now + timedelta(hours=1),
            authorization_ref=f"codex-user-message:{message_digest.value}",
            authorization_message_digest=message_digest,
        )
        authorizer = SealedEngineeringAgentRoleDisclosureAuthorizer(
            session_authority=authority,
            configuration=configuration,
            clock=lambda: self.now,
        )
        adapter = OfflineAgentAdapter(
            outcome_unknown=outcome_unknown,
            provider_unavailable=provider_unavailable,
            failure_code=failure_code,
        )
        gateway = ModelGateway(
            SqliteModelGatewayRepository(
                self.database,
                id_generator=SequenceIds(),
            ),
            (adapter,),
            id_generator=SequenceIds(),
            clock=lambda: self.now,
        )
        model = ModelBackedConversationalEngineeringAgent(
            gateway=PolicyEnforcingEngineeringAgentModelGateway(
                gateway=gateway,
                configuration=configuration,
                authorizer=authorizer,
            ),
            configuration=configuration,
            authorizer=authorizer,
            clock=lambda: self.now,
        )
        tool = UnusedToolPort()
        response = UnusedResponseControl()
        executor = ApplicationOwnedEngineeringAgentTurnExecutor(
            driver=model,
            tool_port=tool,
            reviewer=model,
            response_control=response,
            available_operations=(
                EngineeringAgentToolOperation.WORLD_MODEL_QUERY,
                EngineeringAgentToolOperation.SOURCE_SEARCH,
                EngineeringAgentToolOperation.SOURCE_READ,
            ),
            limits=EngineeringAgentLoopLimits(),
            require_model_call_receipts=True,
            id_generator=SequenceIds(),
        )
        service = InMemoryEngineeringConversationService(
            binding,
            turn_executor=executor,
            id_generator=SequenceIds(),
            clock=lambda: self.now,
        )
        return service, model, authorizer, adapter, tool, response

    def test_offline_gateway_dispatch_is_audited_but_cannot_qualify_output(self) -> None:
        service, model, authorizer, adapter, tool, response = self._service()
        conversation = service.create_conversation()

        submission = service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=Revision(1),
            message="登录流程是怎样的？",
        )

        self.assertEqual(submission.turn.state, ConversationTurnState.FAILED)
        self.assertEqual(
            submission.turn.failure_code, "AGENT_MODEL_CALL_REJECTED"
        )
        self.assertEqual(submission.turn.provider_dispatch_count, 1)
        self.assertEqual(len(submission.turn.model_dispatch_receipt_refs), 1)
        self.assertEqual(len(model.audits), 1)
        self.assertEqual(
            model.audits[0].receipt.state,
            EngineeringAgentModelDispatchState.DISPATCHED_REJECTED,
        )
        self.assertEqual(
            model.audits[0].receipt.failure_code,
            ErrorCode.QUALIFICATION_INVALID.value,
        )
        self.assertEqual(
            model.audits[0].receipt.failure_kind,
            EngineeringAgentModelFailureKind.QUALIFICATION_REJECTED,
        )
        self.assertIsNone(submission.turn.provider_failure_classification)
        self.assertEqual(len(authorizer.disclosure_requests), 1)
        self.assertIn(
            "$.turn.user_message.content",
            authorizer.disclosure_requests[0].disclosed_leaf_paths,
        )
        self.assertIn(
            "$.tool_catalog[1].arguments[0]",
            authorizer.disclosure_requests[0].disclosed_leaf_paths,
        )
        self.assertEqual(len(adapter.requests), 1)
        rendered = "\n".join(
            item.content for item in adapter.requests[0].messages
        )
        self.assertIn("登录流程是怎样的？", rendered)
        self.assertIn("locator_reference", rendered)
        self.assertIn("BUILD_CONFIGURATION", rendered)
        self.assertIn("one short case-sensitive literal token", rendered)
        self.assertIn("semantic descriptions", rendered)
        self.assertIn("draft_reference_policy", rendered)
        self.assertIn("answer_claim_support_observation_ids", rendered)
        self.assertIn("limitation_boundary_observation_ids", rendered)
        self.assertIn("cross_disposition_references_forbidden", rendered)
        self.assertNotIn("literal or semantic search proposal", rendered)
        self.assertNotIn("AGENT_FIXTURE_API_KEY", rendered)
        self.assertNotIn(authorizer.session_authority.digest.value, rendered)
        self.assertEqual(tool.requests, [])
        self.assertEqual(response.requests, [])

    def test_session_binding_drift_rejects_before_gateway_dispatch(self) -> None:
        service, model, _, adapter, _, _ = self._service(
            authority_binding_digest=digest_of("different-binding")
        )
        conversation = service.create_conversation()

        submission = service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=Revision(1),
            message="登录流程是怎样的？",
        )

        self.assertEqual(submission.turn.state, ConversationTurnState.FAILED)
        self.assertEqual(
            submission.turn.failure_code, "AGENT_PRE_DISPATCH_REJECTED"
        )
        self.assertEqual(submission.turn.provider_dispatch_count, 0)
        self.assertEqual(adapter.requests, [])
        self.assertEqual(
            model.audits[0].receipt.state,
            EngineeringAgentModelDispatchState.PRE_DISPATCH_REJECTED,
        )
        self.assertEqual(
            model.audits[0].receipt.failure_kind,
            EngineeringAgentModelFailureKind.PRE_DISPATCH_REJECTED,
        )
        self.assertIsNone(submission.turn.provider_failure_classification)
        self.assertIsNone(model.audits[0].disclosure_authorization_digest)

    def test_outcome_unknown_is_one_dispatch_and_zero_retry(self) -> None:
        service, model, _, adapter, _, _ = self._service(outcome_unknown=True)
        conversation = service.create_conversation()

        submission = service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=Revision(1),
            message="登录流程是怎样的？",
        )

        self.assertEqual(submission.turn.state, ConversationTurnState.FAILED)
        self.assertEqual(
            submission.turn.failure_code, "AGENT_MODEL_OUTCOME_UNKNOWN"
        )
        self.assertEqual(submission.turn.provider_dispatch_count, 1)
        self.assertEqual(submission.turn.retry_count, 0)
        self.assertEqual(len(adapter.requests), 1)
        self.assertEqual(
            model.audits[0].receipt.state,
            EngineeringAgentModelDispatchState.DISPATCHED_OUTCOME_UNKNOWN,
        )
        self.assertEqual(
            model.audits[0].receipt.failure_kind,
            EngineeringAgentModelFailureKind.PROVIDER_OUTCOME_UNKNOWN,
        )
        self.assertEqual(
            submission.turn.provider_failure_classification,
            EngineeringProviderFailureClassification.PROVIDER_OUTCOME_UNKNOWN,
        )
        self.assertEqual(
            submission.turn.provider_failure_code,
            "PROVIDER_OUTCOME_UNKNOWN",
        )

    def test_sealed_http_failure_is_fallback_eligible(self) -> None:
        service, model, _, adapter, _, _ = self._service(
            failure_code=ErrorCode.PROVIDER_HTTP_ERROR
        )
        conversation = service.create_conversation()

        submission = service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=Revision(1),
            message="登录流程是怎样的？",
        )

        self.assertEqual(submission.turn.state, ConversationTurnState.FAILED)
        self.assertEqual(submission.turn.provider_dispatch_count, 1)
        self.assertEqual(len(adapter.requests), 1)
        self.assertEqual(
            model.audits[0].receipt.failure_kind,
            EngineeringAgentModelFailureKind.PROVIDER_HTTP_ERROR,
        )
        self.assertEqual(
            submission.turn.provider_failure_classification,
            EngineeringProviderFailureClassification.PROVIDER_HTTP_ERROR,
        )
        self.assertEqual(
            submission.turn.provider_failure_code,
            ErrorCode.PROVIDER_HTTP_ERROR.value,
        )

    def test_typed_provider_unavailable_is_fallback_eligible(self) -> None:
        service, model, _, adapter, _, _ = self._service(
            provider_unavailable=True
        )
        conversation = service.create_conversation()

        submission = service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=Revision(1),
            message="登录流程是怎样的？",
        )

        self.assertEqual(submission.turn.state, ConversationTurnState.FAILED)
        self.assertEqual(submission.turn.provider_dispatch_count, 1)
        self.assertEqual(len(adapter.requests), 1)
        self.assertEqual(
            model.audits[0].receipt.failure_kind,
            EngineeringAgentModelFailureKind.PROVIDER_UNAVAILABLE,
        )
        self.assertEqual(
            submission.turn.provider_failure_classification,
            EngineeringProviderFailureClassification.PROVIDER_UNAVAILABLE,
        )
        self.assertEqual(
            submission.turn.provider_failure_code,
            "PROVIDER_UNAVAILABLE",
        )

    def test_gateway_owned_failure_cannot_masquerade_as_provider_unavailable(self) -> None:
        service, model, _, adapter, _, _ = self._service(
            failure_code=ErrorCode.AUTHORITY_RECORD_INCONSISTENT
        )
        conversation = service.create_conversation()

        submission = service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=Revision(1),
            message="登录流程是怎样的？",
        )

        self.assertEqual(submission.turn.state, ConversationTurnState.FAILED)
        self.assertEqual(submission.turn.provider_dispatch_count, 1)
        self.assertEqual(len(adapter.requests), 1)
        self.assertEqual(
            model.audits[0].receipt.failure_kind,
            EngineeringAgentModelFailureKind.GATEWAY_FAILURE,
        )
        self.assertIsNone(submission.turn.provider_failure_classification)

    def test_closed_decoders_inject_trusted_call_identity_and_reject_extra_fields(self) -> None:
        binding = _binding()
        capture = CapturingTurnExecutor()
        service = InMemoryEngineeringConversationService(
            binding,
            turn_executor=capture,
            id_generator=SequenceIds(),
            clock=lambda: self.now,
        )
        conversation = service.create_conversation()
        service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=Revision(1),
            message="它是怎样登录的？",
        )
        invocation = EngineeringAgentInvocation(
            request=capture.request,
            previous_work_state=None,
            observations=(),
            review_findings=(),
            review_digest=None,
            available_operations=(EngineeringAgentToolOperation.WORLD_MODEL_QUERY,),
        )
        support_observation = EngineeringAgentToolObservation(
            observation_id=StableId(f"observation_{'1' * 32}"),
            tool_request_id=StableId(f"tool_request_{'2' * 32}"),
            operation=EngineeringAgentToolOperation.WORLD_MODEL_QUERY,
            result_ref="support-result",
            content="supported current-Turn evidence",
            disposition=EngineeringAgentEvidenceDisposition.SUPPORT,
            progress=True,
            citation_refs=(),
            authority_receipt=None,
            tool_evidence_digest=digest_of("support-evidence"),
            digest=digest_of("support-observation"),
        )
        boundary_observation = EngineeringAgentToolObservation(
            observation_id=StableId(f"observation_{'3' * 32}"),
            tool_request_id=StableId(f"tool_request_{'4' * 32}"),
            operation=EngineeringAgentToolOperation.WORLD_MODEL_QUERY,
            result_ref="boundary-result",
            content="current-Turn evidence boundary",
            disposition=EngineeringAgentEvidenceDisposition.BOUNDARY,
            progress=False,
            citation_refs=(),
            authority_receipt=None,
            tool_evidence_digest=digest_of("boundary-evidence"),
            digest=digest_of("boundary-observation"),
        )
        policy_view = _primary_input_view(
            EngineeringAgentInvocation(
                request=capture.request,
                previous_work_state=None,
                observations=(support_observation, boundary_observation),
                review_findings=(),
                review_digest=None,
                available_operations=(
                    EngineeringAgentToolOperation.WORLD_MODEL_QUERY,
                ),
            )
        )["draft_reference_policy"]
        self.assertEqual(
            policy_view,
            {
                "answer_claim_support_observation_ids": (
                    support_observation.observation_id.value,
                ),
                "limitation_boundary_observation_ids": (
                    boundary_observation.observation_id.value,
                ),
                "cross_disposition_references_forbidden": True,
                "unknown_observation_references_forbidden": True,
            },
        )
        payload = {
            "goal": "澄清登录入口",
            "response_language": "zh-CN",
            "audience": "software engineer",
            "constraints": [],
            "resolved_referents": [],
            "accepted_correction_message_ids": [],
            "superseded_conclusion_refs": [],
            "hypotheses": [],
            "plan": [],
            "observation_ids": [],
            "open_items": [],
            "phase": "RESPONSE_READY",
            "action": None,
            "draft": {
                "response_kind": "CLARIFICATION",
                "content": "请明确登录入口。",
                "claims": [],
                "boundary_observation_ids": [],
            },
        }

        proposal = decode_engineering_agent_primary_output(
            output_text=json.dumps(payload, ensure_ascii=False),
            invocation=invocation,
            model_call_ref="trusted-gateway-call",
        )
        review = decode_engineering_agent_review_output(
            output_text='{"decision":"APPROVED","findings":[]}',
            request=SimpleNamespace(draft=SimpleNamespace(claims=())),
            model_call_ref="trusted-review-call",
        )

        self.assertEqual(proposal.model_call_ref, "trusted-gateway-call")
        self.assertEqual(review.model_call_ref, "trusted-review-call")
        payload["model_call_ref"] = "forged-provider-call"
        with self.assertRaises(DomainError) as raised:
            decode_engineering_agent_primary_output(
                output_text=json.dumps(payload, ensure_ascii=False),
                invocation=invocation,
                model_call_ref="trusted-gateway-call",
            )
        self.assertEqual(
            raised.exception.code, ErrorCode.STRUCTURED_OUTPUT_INVALID
        )


if __name__ == "__main__":
    unittest.main()
