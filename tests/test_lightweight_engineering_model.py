from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from software_world_model.ai_infrastructure.conversational_engineering_model import (
    EngineeringAgentModelConfiguration,
    EngineeringAgentSessionDisclosureAuthority,
    SealedEngineeringAgentLogicalTurnDispatchBudget,
)
from software_world_model.ai_infrastructure.lightweight_engineering_model import (
    LIGHTWEIGHT_REVIEW_SCHEMA_REF,
    LIGHTWEIGHT_STEP_SCHEMA_REF,
    LightweightDispatchBudget,
    ModelBackedLightweightEngineeringAgent,
)
from software_world_model.ai_infrastructure.model_gateway import (
    AdapterConformanceLevel,
    AdapterResponse,
    ModelGateway,
    ProviderAdapterCapabilities,
    ReplayClassification,
)
from software_world_model.application_services.conversational_engineering_agent import (
    EngineeringAgentModelFailureKind,
    EngineeringAgentModelRole,
)
from software_world_model.application_services.engineering_conversation import (
    EngineeringChatBinding,
    EngineeringTurnExecutionOutcome,
    InMemoryEngineeringConversationService,
    RuntimeCapabilityStatus,
)
from software_world_model.application_services.lightweight_engineering_agent import (
    LightweightAgentAction,
    LightweightAgentResponseKind,
    LightweightAgentStepRequest,
    LightweightModelCallFailure,
    LightweightReviewRequest,
)
from software_world_model.cross_cutting import StableId, digest_of
from software_world_model.infrastructure import (
    SqliteDatabase,
    SqliteModelGatewayRepository,
)
from software_world_model.interface.engineering_chat_session_artifact import (
    _provider_terminal_audit,
)


class SequenceIds:
    def __init__(self) -> None:
        self.value = 0

    def new(self, kind: str) -> StableId:
        self.value += 1
        return StableId(f"{kind}_{self.value:032x}")


class CapturingExecutor:
    def __init__(self) -> None:
        self.request = None

    def execute(self, request):
        self.request = request
        return EngineeringTurnExecutionOutcome.failed(
            request_digest=request.request_digest,
            assistant_content="fixture capture complete",
            included_user_message_ids=(request.user_message.message_id,),
            failure_code="FIXTURE_CAPTURE",
            failure_message="fixture capture complete",
        )


class LiveStructuredAdapter:
    provider_type = "LIGHTWEIGHT_TEST_PROVIDER"
    adapter_version = "1"
    model_ref = "lightweight-test-model@1"
    qualification_ref = "CC-LIGHTWEIGHT-TEST-CURRENT"

    def __init__(self, outputs: list[dict[str, object]]) -> None:
        self.capabilities = ProviderAdapterCapabilities(
            no_external_access=True,
            hidden_context_disabled=True,
            stateless_session=True,
            structured_output=True,
            actual_fingerprint_reported=True,
            conformance_level=AdapterConformanceLevel.LIVE_CURRENT,
            conformance_result_ref=self.qualification_ref,
            qualified_model_fingerprints=(self.model_ref,),
        )
        self.outputs = list(outputs)
        self.requests = []

    def invoke(self, request):
        self.requests.append(request)
        output = self.outputs.pop(0)
        return AdapterResponse.create(
            provider_request_id=f"lightweight-fixture-{len(self.requests)}",
            actual_model_fingerprint=self.model_ref,
            replay_classification=ReplayClassification.PINNED,
            output_text=json.dumps(output, ensure_ascii=False),
            input_tokens=64,
            output_tokens=32,
            usage_complete=True,
            termination_reason="stop",
        )


class LightweightEngineeringModelTest(unittest.TestCase):
    def setUp(self) -> None:
        self.now = datetime(2026, 9, 1, 1, tzinfo=timezone.utc)
        self.database = SqliteDatabase()
        self.addCleanup(self.database.close)

    def _runtime(self, outputs: list[dict[str, object]]):
        binding = EngineeringChatBinding.create(
            product_revision="a" * 40,
            project_name="fixture-project",
            repository_revision="b" * 40,
            world_model_status=RuntimeCapabilityStatus.READY,
            world_model_authority_digest=digest_of("fixture-world-model"),
            source_profile_ref="fixture-source-profile@1",
            source_access_status=RuntimeCapabilityStatus.READY,
            provider_status=RuntimeCapabilityStatus.READY,
            provider_route_ref="fixture-provider-route@1",
            known_limitations=("test fixture only",),
        )
        configuration = EngineeringAgentModelConfiguration(
            provider_type=LiveStructuredAdapter.provider_type,
            adapter_version=LiveStructuredAdapter.adapter_version,
            endpoint="https://provider.invalid/v1/chat",
            model_ref=LiveStructuredAdapter.model_ref,
            expected_actual_model_fingerprint=LiveStructuredAdapter.model_ref,
            provider_configuration_fingerprint=digest_of(
                "lightweight-test-provider-configuration"
            ),
            secret_reference="env:LIGHTWEIGHT_TEST_API_KEY",
            qualification_ref=LiveStructuredAdapter.qualification_ref,
            qualification_valid_until=self.now + timedelta(hours=2),
            maximum_calls=4,
        )
        standing_digest = digest_of("fixture-standing-authority")
        authority = EngineeringAgentSessionDisclosureAuthority.derive_from_public_source_session(
            session_ref="lightweight-test-session",
            product_candidate_digest=digest_of("fixture-product-candidate"),
            chat_binding_digest=binding.digest,
            configuration=configuration,
            maximum_turns=1,
            maximum_dispatches_per_turn=4,
            maximum_total_dispatches=4,
            authorized_at=self.now,
            expires_at=self.now + timedelta(hours=1),
            standing_authority_digest=standing_digest,
            public_source_session_authority_digest=digest_of(
                "fixture-public-source-session-authority"
            ),
        )
        parent = SealedEngineeringAgentLogicalTurnDispatchBudget(
            chat_binding_digest=binding.digest,
            authorization_message_digest=standing_digest,
            provider_binding_digests=(configuration.digest,),
            maximum_turns=1,
            maximum_dispatches_per_turn=4,
            maximum_total_dispatches=4,
        )
        budget = LightweightDispatchBudget(parent=parent)
        adapter = LiveStructuredAdapter(outputs)
        gateway = ModelGateway(
            SqliteModelGatewayRepository(
                self.database,
                id_generator=SequenceIds(),
            ),
            (adapter,),
            id_generator=SequenceIds(),
            clock=lambda: self.now,
        )
        model = ModelBackedLightweightEngineeringAgent(
            gateway=gateway,
            configuration=configuration,
            session_authority=authority,
            dispatch_budget=budget,
            clock=lambda: self.now,
        )
        capture = CapturingExecutor()
        service = InMemoryEngineeringConversationService(
            binding,
            turn_executor=capture,
            id_generator=SequenceIds(),
            clock=lambda: self.now,
        )
        conversation = service.create_conversation()
        service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=conversation.conversation.revision,
            message="How is the exact component selected?",
        )
        return model, budget, adapter, capture.request, configuration, authority

    @staticmethod
    def _step(request) -> LightweightAgentStepRequest:
        return LightweightAgentStepRequest(
            turn_request=request,
            step=1,
            goal="Find the selection behavior.",
            plan="Search for the selection entry point.",
            observations=(),
            read_candidates=(),
            tools_enabled=True,
        )

    def test_exact_disclosure_and_fresh_review_are_audited(self) -> None:
        model, budget, adapter, request, configuration, authority = self._runtime(
            [
                {
                    "goal": "Find the selection behavior.",
                    "plan": "Search for the selection entry point.",
                    "action": "SEARCH_SOURCE",
                    "query": "selectionStrategy",
                    "read_index": None,
                    "cognition_index": None,
                    "relation_kind": None,
                    "direction": None,
                    "maximum_depth": None,
                    "cursor": None,
                    "response_kind": None,
                    "answer": None,
                    "citations": [],
                },
                {"verdict": "APPROVED", "findings": []},
            ]
        )

        decision = model.decide(self._step(request))
        review = model.review(
            LightweightReviewRequest(
                turn_request=request,
                answer="Please identify which component you mean.",
                response_kind=LightweightAgentResponseKind.CLARIFICATION,
                observations=(),
                citations=(),
            )
        )

        self.assertIs(decision.decision.action, LightweightAgentAction.SEARCH_SOURCE)
        self.assertTrue(review.receipt.successful)
        self.assertEqual(
            [item.output_schema_ref for item in adapter.requests],
            [LIGHTWEIGHT_STEP_SCHEMA_REF, LIGHTWEIGHT_REVIEW_SCHEMA_REF],
        )
        self.assertTrue(all(item.tools == () for item in adapter.requests))
        self.assertTrue(all(len(item.messages) == 2 for item in adapter.requests))
        step_system_prompt = adapter.requests[0].messages[0].content
        self.assertIn(
            "lexical over source-derived identifiers and statements",
            step_system_prompt,
        )
        self.assertIn("interface or supertype", step_system_prompt)
        self.assertIn("one identifier or one exact phrase", step_system_prompt)
        self.assertIn("never concatenate separate search terms", step_system_prompt)
        disclosed_text = "\n".join(
            message.content
            for provider_request in adapter.requests
            for message in provider_request.messages
        )
        self.assertNotIn(configuration.secret_reference, disclosed_text)
        authorizations = budget.authorizations
        self.assertEqual(
            [item.role for item in authorizations],
            [
                EngineeringAgentModelRole.PRIMARY_AGENT,
                EngineeringAgentModelRole.INDEPENDENT_REVIEWER,
            ],
        )
        self.assertEqual([item.turn_dispatch_ordinal for item in authorizations], [1, 2])
        self.assertTrue(
            all(item.source_revision == request.binding.repository_revision for item in authorizations)
        )
        self.assertTrue(
            all(item.product_revision == request.binding.product_revision for item in authorizations)
        )
        self.assertTrue(
            all(item.secret_reference == configuration.secret_reference for item in authorizations)
        )
        self.assertTrue(
            all(item.session_authority_digest == authority.digest for item in authorizations)
        )
        for provider_request, authorization in zip(
            adapter.requests, authorizations, strict=True
        ):
            fragments = tuple(
                (message.input_item_id, message.input_item_digest.value)
                for message in provider_request.messages
            )
            self.assertEqual(
                authorization.disclosed_payload_digest,
                digest_of(["SWM-LIGHTWEIGHT-DISCLOSED-INPUT@1", fragments]),
            )
            self.assertEqual(
                authorization.disclosed_payload_bytes,
                sum(len(message.content.encode("utf-8")) for message in provider_request.messages),
            )
        self.assertEqual(
            [item.receipt.provider_dispatch_count for item in model.audits],
            [1, 1],
        )

        runtime = SimpleNamespace(
            provider_type="VOLCENGINE_ARK",
            configuration=configuration,
            session_authority=authority,
            model_boundary=SimpleNamespace(audits=()),
            authorizer=SimpleNamespace(
                disclosure_requests=(), issued_authorizations=()
            ),
            transport=object(),
            digest=digest_of("fixture-provider-runtime"),
        )
        with patch(
            "software_world_model.interface.engineering_chat_session_artifact.ark_transport_session_audit",
            return_value={"http_dispatch_count": 2},
        ):
            terminal = _provider_terminal_audit(
                runtime,
                lightweight_model=model,
            )
        self.assertEqual(terminal["provider_dispatch_count"], 2)
        self.assertEqual(
            terminal["disclosure_mode"],
            "LIGHTWEIGHT_EXACT_DISPATCH_AUTHORIZATION",
        )
        self.assertEqual(
            terminal["disclosure_authorization_digests"],
            tuple(item.digest.value for item in authorizations),
        )

    def test_branch_invalid_output_keeps_real_dispatch_and_rejected_audit(self) -> None:
        model, budget, adapter, request, _, _ = self._runtime(
            [
                {
                    "goal": "Find the selection behavior.",
                    "plan": "Search for the selection entry point.",
                    "action": "SEARCH_SOURCE",
                    "query": None,
                    "read_index": None,
                    "cognition_index": None,
                    "relation_kind": None,
                    "direction": None,
                    "maximum_depth": None,
                    "cursor": None,
                    "response_kind": None,
                    "answer": None,
                    "citations": [],
                }
            ]
        )

        with self.assertRaises(LightweightModelCallFailure) as raised:
            model.decide(self._step(request))

        self.assertEqual(len(adapter.requests), 1)
        self.assertEqual(len(budget.authorizations), 1)
        self.assertEqual(raised.exception.receipt.provider_dispatch_count, 1)
        self.assertIs(
            raised.exception.receipt.failure_kind,
            EngineeringAgentModelFailureKind.PROVIDER_OUTPUT_INVALID,
        )
        self.assertEqual(model.audits[-1].receipt, raised.exception.receipt)

    def test_cognition_action_schema_uses_application_numeric_identity(self) -> None:
        model, _, adapter, request, _, _ = self._runtime(
            [
                {
                    "goal": "Trace the entry behavior.",
                    "plan": "Search reusable cognition before reading Source.",
                    "action": "SEARCH_COGNITION",
                    "query": "CheckoutController",
                    "read_index": None,
                    "cognition_index": None,
                    "relation_kind": None,
                    "direction": None,
                    "maximum_depth": None,
                    "cursor": None,
                    "response_kind": None,
                    "answer": None,
                    "citations": [],
                }
            ]
        )

        decision = model.decide(self._step(request))

        self.assertIs(
            decision.decision.action,
            LightweightAgentAction.SEARCH_COGNITION,
        )
        self.assertIsNone(decision.decision.cognition_index)
        self.assertIn(
            "Application-issued numeric cognition_index",
            adapter.requests[0].messages[0].content,
        )


if __name__ == "__main__":
    unittest.main()
