from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json
from types import SimpleNamespace
import unittest

from software_world_model.ai_infrastructure.conversational_engineering_model import (
    ENGINEERING_AGENT_PRIMARY_OUTPUT_SCHEMA_REF,
    ENGINEERING_AGENT_ROLE_DISCLOSURE_AUTHORIZATION_SCHEMA_V2,
    EngineeringAgentModelConfiguration,
    EngineeringAgentSessionDisclosureAuthority,
    ModelBackedConversationalEngineeringAgent,
    PolicyEnforcingEngineeringAgentModelGateway,
    SealedEngineeringAgentRoleDisclosureAuthorizer,
    _boundary_relevance_allowed_dispositions,
    _output_preflight_view,
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
from software_world_model.ai_infrastructure.provider_http_failure_evidence import (
    ProviderHTTPFailureCapturingAdapter,
    ProviderHTTPFailureEvidenceGateway,
)
from software_world_model.application_services.conversational_engineering_agent import (
    ApplicationOwnedEngineeringAgentTurnExecutor,
    EngineeringAgentAnswerDraft,
    EngineeringAgentBoundaryRelevanceAssessmentDisposition,
    EngineeringAgentCitation,
    EngineeringAgentClaimProposal,
    EngineeringAgentDeliveryAuthorization,
    EngineeringAgentEvidenceBoundaryAssessmentDisposition,
    EngineeringAgentEvidenceDisposition,
    EngineeringAgentEvidencePackage,
    EngineeringAgentInvocation,
    EngineeringAgentInvocationMode,
    EngineeringAgentLedgerEntryReceipt,
    EngineeringAgentLoopLimits,
    EngineeringAgentModelCallFailure,
    EngineeringAgentModelDispatchState,
    EngineeringAgentModelFailureKind,
    EngineeringAgentModelRole,
    EngineeringAgentReviewFinding,
    EngineeringAgentReviewFocus,
    EngineeringAgentResponseKind,
    EngineeringAgentSourceReadOption,
    EngineeringAgentToolActionProposal,
    EngineeringAgentToolAuthorityKind,
    EngineeringAgentToolAuthorityReceipt,
    EngineeringAgentToolOperation,
    EngineeringAgentToolObservation,
    project_engineering_agent_draft_boundaries,
    project_engineering_agent_boundary_relevance_challenges,
    project_engineering_agent_evidence_boundary_challenges,
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
        failure_details: dict[str, str | int] | None = None,
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
        self.failure_details = failure_details or {}
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
            raise DomainError(
                self.failure_code,
                "fixture Provider failure",
                self.failure_details,
            )
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


class SequencedLiveAgentAdapter:
    provider_type = OfflineAgentAdapter.provider_type
    adapter_version = OfflineAgentAdapter.adapter_version

    def __init__(self, outputs=None) -> None:
        self.capabilities = ProviderAdapterCapabilities(
            no_external_access=True,
            hidden_context_disabled=True,
            stateless_session=True,
            structured_output=True,
            actual_fingerprint_reported=True,
            conformance_level=AdapterConformanceLevel.LIVE_CURRENT,
            conformance_result_ref="CC-AGENT-OFFLINE-FIXTURE",
            qualified_model_fingerprints=("agent-fixture-model@1",),
        )
        self.requests = []
        default_outputs = (
            "not-json",
            json.dumps(
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
            '{"decision":"APPROVED","claim_assessments":[],"evidence_boundary_assessments":[],"boundary_relevance_assessments":[],"findings":[]}',
        )
        self.outputs = tuple(outputs) if outputs is not None else default_outputs

    def invoke(self, request):
        self.requests.append(request)
        output = self.outputs[len(self.requests) - 1]
        return AdapterResponse.create(
            provider_request_id=f"agent-live-request-{len(self.requests)}",
            actual_model_fingerprint="agent-fixture-model@1",
            replay_classification=ReplayClassification.PINNED,
            output_text=output,
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
        failure_details: dict[str, str | int] | None = None,
        authority_binding_digest=None,
        standing_authority: bool = False,
        adapter=None,
    ):
        binding = _binding()
        configuration = _configuration(self.now)
        message_digest = digest_of("local deterministic disclosure fixture")
        authority_arguments = {
            "session_ref": "agent-session-fixture",
            "product_candidate_digest": digest_of("product-candidate"),
            "chat_binding_digest": (
                authority_binding_digest
                if authority_binding_digest is not None
                else binding.digest
            ),
            "configuration": configuration,
            "maximum_turns": 3,
            "maximum_dispatches_per_turn": 12,
            "maximum_total_dispatches": 12,
            "authorized_at": self.now,
            "expires_at": self.now + timedelta(hours=1),
        }
        if standing_authority:
            authority = EngineeringAgentSessionDisclosureAuthority.derive_from_public_source_session(
                **authority_arguments,
                standing_authority_digest=digest_of("standing-authority"),
                public_source_session_authority_digest=digest_of(
                    "public-source-session-authority"
                ),
            )
        else:
            authority = EngineeringAgentSessionDisclosureAuthority.create(
                **authority_arguments,
                authorization_ref=f"codex-user-message:{message_digest.value}",
                authorization_message_digest=message_digest,
            )
        authorizer = SealedEngineeringAgentRoleDisclosureAuthorizer(
            session_authority=authority,
            configuration=configuration,
            clock=lambda: self.now,
        )
        adapter = adapter or OfflineAgentAdapter(
            outcome_unknown=outcome_unknown,
            provider_unavailable=provider_unavailable,
            failure_code=failure_code,
            failure_details=failure_details,
        )
        repository = SqliteModelGatewayRepository(
            self.database,
            id_generator=SequenceIds(),
        )
        capturing_adapter = ProviderHTTPFailureCapturingAdapter(adapter)
        gateway = ProviderHTTPFailureEvidenceGateway(
            gateway=ModelGateway(
                repository,
                (capturing_adapter,),
                id_generator=SequenceIds(),
                clock=lambda: self.now,
            ),
            adapter=capturing_adapter,
            repository=repository,
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

    def test_authority_and_runtime_evidence_policy_is_question_agnostic(self) -> None:
        policies = []
        messages = (
            "缓存失效后，下一次请求何时看到新权限？",
            "事件发布后，另一个消费者何时观察到状态变化？",
            "远端文档写入后，后续查询何时能读取新版本？",
        )
        for message in messages:
            capture = CapturingTurnExecutor()
            service = InMemoryEngineeringConversationService(
                _binding(),
                turn_executor=capture,
                id_generator=SequenceIds(),
                clock=lambda: self.now,
            )
            conversation = service.create_conversation()
            service.submit_turn(
                conversation_id=conversation.conversation.conversation_id,
                expected_revision=Revision(1),
                message=message,
            )
            view = _primary_input_view(
                EngineeringAgentInvocation(
                    request=capture.request,
                    previous_work_state=None,
                    observations=(),
                    review_findings=(),
                    review_digest=None,
                    available_operations=(
                        EngineeringAgentToolOperation.WORLD_MODEL_QUERY,
                    ),
                )
            )
            policy = view["draft_reference_policy"]
            policies.append(
                {
                    "evidence_gap_is_not_authority_denial": policy[
                        "evidence_gap_is_not_authority_denial"
                    ],
                    "authorization_limitation_requires_exact_boundary": policy[
                        "authorization_limitation_requires_exact_boundary"
                    ],
                    "producer_invocation_is_not_consumer_visible_effect": policy[
                        "producer_invocation_is_not_consumer_visible_effect"
                    ],
                    "consumer_visible_effect_requires_consumer_path_support": policy[
                        "consumer_visible_effect_requires_consumer_path_support"
                    ],
                    "audit_retention_requires_answer_disclosure": policy[
                        "audit_retention_requires_answer_disclosure"
                    ],
                    "limitation_requires_at_least_one_boundary_reference": policy[
                        "limitation_requires_at_least_one_boundary_reference"
                    ],
                    "structured_boundary_reference_is_evidence_binding_not_full_text_disclosure": policy[
                        "structured_boundary_reference_is_evidence_binding_not_full_text_disclosure"
                    ],
                    "boundary_metadata_absent_from_draft_content_is_not_disclosed": policy[
                        "boundary_metadata_absent_from_draft_content_is_not_disclosed"
                    ],
                    "bound_boundary_id_need_not_be_named_or_raw_disclosed": policy[
                        "bound_boundary_id_need_not_be_named_or_raw_disclosed"
                    ],
                    "answer_boundary_requires_unresolved_material_requirement_or_explicit_diagnostic_request": policy[
                        "answer_boundary_requires_unresolved_material_requirement_or_explicit_diagnostic_request"
                    ],
                    "resolved_acquisition_candidate_requires_relevance_review": policy[
                        "resolved_acquisition_candidate_requires_relevance_review"
                    ],
                    "resolved_acquisition_candidate_is_automatic_exclusion": policy[
                        "resolved_acquisition_candidate_is_automatic_exclusion"
                    ],
                    "global_inventory_metrics_require_material_user_relevance": policy[
                        "global_inventory_metrics_require_material_user_relevance"
                    ],
                    "answer_detail_requires_material_user_relevance": policy[
                        "answer_detail_requires_material_user_relevance"
                    ],
                    "counterfactual_omission_preserving_requested_conclusions_means_omit": policy[
                        "counterfactual_omission_preserving_requested_conclusions_means_omit"
                    ],
                    "self_introduced_adjacent_detail_allows_evidence_expansion": policy[
                        "self_introduced_adjacent_detail_allows_evidence_expansion"
                    ],
                    "generation_or_tool_provenance_requires_direct_support": policy[
                        "generation_or_tool_provenance_requires_direct_support"
                    ],
                }
            )

        self.assertEqual(policies, [policies[0]] * len(messages))
        self.assertEqual(
            policies[0],
            {
                "evidence_gap_is_not_authority_denial": True,
                "authorization_limitation_requires_exact_boundary": True,
                "producer_invocation_is_not_consumer_visible_effect": True,
                "consumer_visible_effect_requires_consumer_path_support": True,
                "audit_retention_requires_answer_disclosure": False,
                "limitation_requires_at_least_one_boundary_reference": True,
                "structured_boundary_reference_is_evidence_binding_not_full_text_disclosure": True,
                "boundary_metadata_absent_from_draft_content_is_not_disclosed": True,
                "bound_boundary_id_need_not_be_named_or_raw_disclosed": True,
                "answer_boundary_requires_unresolved_material_requirement_or_explicit_diagnostic_request": True,
                "resolved_acquisition_candidate_requires_relevance_review": True,
                "resolved_acquisition_candidate_is_automatic_exclusion": False,
                "global_inventory_metrics_require_material_user_relevance": True,
                "answer_detail_requires_material_user_relevance": True,
                "counterfactual_omission_preserving_requested_conclusions_means_omit": True,
                "self_introduced_adjacent_detail_allows_evidence_expansion": False,
                "generation_or_tool_provenance_requires_direct_support": True,
            },
        )

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
            "$.tool_catalog[1].action_template.arguments[0].name",
            authorizer.disclosure_requests[0].disclosed_leaf_paths,
        )
        self.assertIn(
            "$.final_output_preflight.non_null_action."
            "effective_action_templates[1].operation",
            authorizer.disclosure_requests[0].disclosed_leaf_paths,
        )
        self.assertEqual(len(adapter.requests), 1)
        self.assertEqual(
            tuple(item.input_item_id for item in adapter.requests[0].messages),
            ("instruction", "sealed-role-input", "final-output-preflight"),
        )
        primary_payload = json.loads(adapter.requests[0].messages[1].content)
        self.assertEqual(
            primary_payload["tool_action_budget"],
            {
                "schema": "ENGINEERING_AGENT_TOOL_ACTION_BUDGET@1",
                "maximum": 8,
                "used": 0,
                "remaining": 8,
                "remaining_is_not_a_consumption_target": True,
                "zero_remaining_allows_new_tool_action": False,
            },
        )
        self.assertTrue(
            primary_payload["investigation_policy"][
                "world_model_first_before_source_required"
            ]
        )
        output_preflight = json.loads(adapter.requests[0].messages[-1].content)
        self.assertEqual(
            output_preflight["schema"],
            "ENGINEERING_AGENT_OUTPUT_PREFLIGHT@10",
        )
        self.assertTrue(output_preflight["shape_only"])
        self.assertFalse(output_preflight["semantic_or_tool_authority"])
        self.assertEqual(
            output_preflight["json_serialization"],
            {
                "parseable_json_object_required": True,
                "embedded_double_quote_rule": (
                    "Inside every JSON string value, encode each literal "
                    "double quote as backslash followed by double quote."
                ),
                "backslash_rule": (
                    "Inside every JSON string value, encode each literal "
                    "backslash as two backslashes."
                ),
                "line_break_rule": (
                    "Inside every JSON string value, encode each line break "
                    "as backslash followed by n."
                ),
                "copied_text_rule": (
                    "Apply the same escaping to copied user, conversation, "
                    "evidence, Draft, and review text."
                ),
                "parse_before_return": True,
            },
        )
        self.assertEqual(
            output_preflight["non_null_action"]["required_fields"],
            ["operation", "arguments", "evidence_need"],
        )
        self.assertEqual(
            output_preflight["non_null_action"][
                "argument_item_required_fields"
            ],
            ["name", "value"],
        )
        self.assertTrue(
            output_preflight["non_null_action"][
                "direct_keyed_arguments_object_forbidden"
            ]
        )
        self.assertEqual(
            output_preflight["closed_nested_object_fields"],
            {
                "$.action": ["operation", "arguments", "evidence_need"],
                "$.action.arguments[]": ["name", "value"],
                "$.draft": [
                    "response_kind",
                    "content",
                    "claims",
                    "boundary_observation_ids",
                ],
                "$.draft.claims[]": [
                    "statement",
                    "support_observation_ids",
                ],
            },
        )
        primary_branch = output_preflight["primary_branch_contract"]
        self.assertEqual(
            primary_branch["effective_required_branch"],
            "ACTION_OR_DRAFT",
        )
        self.assertEqual(
            primary_branch["action_branch"]["allowed_phases_exact"],
            ["PLANNING", "INVESTIGATING", "REVISING"],
        )
        self.assertEqual(
            primary_branch["draft_branch"]["required_phase"],
            "RESPONSE_READY",
        )
        self.assertEqual(
            primary_branch["response_kind_constraints"]["LIMITATION"][
                "boundary_observation_ids_minimum"
            ],
            1,
        )
        self.assertEqual(
            tuple(
                item["operation"]
                for item in output_preflight["non_null_action"][
                    "effective_action_templates"
                ]
            ),
            ("WORLD_MODEL_QUERY", "SOURCE_SEARCH"),
        )
        rendered = "\n".join(
            item.content for item in adapter.requests[0].messages
        )
        self.assertIn("登录流程是怎样的？", rendered)
        self.assertIn("locator_reference", rendered)
        self.assertIn("BUILD_CONFIGURATION", rendered)
        self.assertIn("one new short case-sensitive literal token", rendered)
        self.assertIn("semantic descriptions", rendered)
        self.assertIn("draft_reference_policy", rendered)
        self.assertIn("work_state_reference_policy", rendered)
        self.assertIn("tool_action_required", rendered)
        self.assertIn("tool_reference_policy", rendered)
        self.assertIn("answer_claim_support_observation_ids", rendered)
        self.assertIn("limitation_boundary_observation_ids", rendered)
        self.assertIn("cross_disposition_references_forbidden", rendered)
        self.assertIn(
            "claim_statement_required_inherited_material_qualifiers",
            rendered,
        )
        self.assertIn("source_read_options", rendered)
        self.assertIn("source_file_budget", rendered)
        self.assertIn("exact_action_repetition_forbidden", rendered)
        self.assertIn("forbidden_exact_values", rendered)
        self.assertIn("allowed_exact_values", rendered)
        self.assertIn(
            "The action object always contains exactly operation, arguments, and",
            rendered,
        )
        self.assertIn("action_template", rendered)
        self.assertIn("copy exactly one complete", rendered)
        self.assertIn("never infer that a sole", rendered)
        self.assertIn("arguments is always a JSON array", rendered)
        self.assertIn("Every LIMITATION must copy at least one", rendered)
        self.assertIn("evidence binding, not automatic disclosure", rendered)
        self.assertIn("exhaustive top-level allowlist", rendered)
        self.assertIn(
            "Never infer a type relationship or catch boundary",
            rendered,
        )
        self.assertIn(
            "A source line that directly contains a call expression",
            rendered,
        )
        self.assertIn(
            "A heading, table column header, list lead-in, label, or surrounding sentence",
            rendered,
        )
        self.assertIn(
            "source_read_options contains only opaque locators that are executable",
            rendered,
        )
        self.assertIn(
            "It is not evidence of the callee implementation",
            rendered,
        )
        self.assertIn("evidence_gap_is_not_authority_denial", rendered)
        self.assertIn(
            "A cognition gap, unread implementation, absent locator",
            rendered,
        )
        self.assertIn(
            "producer_invocation_is_not_consumer_visible_effect",
            rendered,
        )
        self.assertIn(
            "Separate a producer-side invocation from its consumer-visible runtime effect",
            rendered,
        )
        self.assertIn(
            "requires current SUPPORT for that consumer path",
            rendered,
        )
        self.assertIn("audit_retention_requires_answer_disclosure", rendered)
        self.assertIn(
            "Evidence Ledger audit retention and user-visible answer disclosure are different",
            rendered,
        )
        self.assertIn(
            "Global inventory counts and profile-wide",
            rendered,
        )
        self.assertIn(
            "coverage metrics are not answer content",
            rendered,
        )
        self.assertIn(
            "Apply a counterfactual relevance test before adding every user-visible",
            rendered,
        )
        self.assertIn(
            "Do not spend a tool action",
            rendered,
        )
        self.assertIn("code-generation or tool provenance", rendered)
        self.assertIn("Follow tool_action_budget exactly", rendered)
        self.assertIn("Rewording a prior semantic", rendered)
        self.assertIn("need does not make it new", rendered)
        self.assertIn("source-native type or member identifier", rendered)
        self.assertIn("prior_answer_restatement_requires_current_turn_evidence", rendered)
        self.assertIn(
            "source_follow_up_required_before_limitation", rendered
        )
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

    def test_standing_authority_is_carried_into_one_use_role_receipt(self) -> None:
        service, _, authorizer, _, _, _ = self._service(
            standing_authority=True
        )
        conversation = service.create_conversation()

        service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=Revision(1),
            message="登录流程是怎样的？",
        )

        self.assertEqual(len(authorizer.issued_authorizations), 1)
        authorization = authorizer.issued_authorizations[0]
        self.assertEqual(
            authorization.schema,
            ENGINEERING_AGENT_ROLE_DISCLOSURE_AUTHORIZATION_SCHEMA_V2,
        )
        self.assertEqual(
            authorization.standing_authority_digest,
            authorizer.session_authority.standing_authority_digest,
        )
        self.assertEqual(authorization.human_approval_request_count, 0)
        self.assertEqual(authorization.maximum_dispatches, 1)

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

    def test_invalid_output_gets_one_fresh_same_profile_format_repair_call(self) -> None:
        adapter = SequencedLiveAgentAdapter()
        service, model, authorizer, _, tool, response = self._service(
            adapter=adapter
        )
        conversation = service.create_conversation()

        submission = service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=Revision(1),
            message="登录流程是怎样的？",
        )

        self.assertEqual(submission.turn.state, ConversationTurnState.SUCCEEDED)
        self.assertEqual(submission.turn.provider_dispatch_count, 3)
        self.assertEqual(len(submission.turn.model_dispatch_receipt_refs), 3)
        self.assertEqual(submission.turn.retry_count, 0)
        self.assertEqual(len(model.audits), 3)
        self.assertEqual(len(authorizer.disclosure_requests), 3)
        self.assertEqual(len(adapter.requests), 3)
        self.assertIn(
            "Treat a path, package, import, symbol name, directory convention, or caller",
            adapter.requests[2].messages[0].content,
        )
        self.assertEqual(tool.requests, [])
        self.assertEqual(len(response.requests), 1)
        self.assertEqual(
            model.audits[0].receipt.failure_kind,
            EngineeringAgentModelFailureKind.PROVIDER_OUTPUT_INVALID,
        )
        self.assertTrue(model.audits[1].receipt.successful)
        self.assertTrue(model.audits[2].receipt.successful)
        self.assertNotEqual(adapter.requests[0].digest, adapter.requests[1].digest)
        first_payload = json.loads(
            next(
                item.content
                for item in adapter.requests[0].messages
                if item.input_item_id == "sealed-role-input"
            )
        )
        repair_payload = json.loads(
            next(
                item.content
                for item in adapter.requests[1].messages
                if item.input_item_id == "sealed-role-input"
            )
        )
        self.assertEqual(first_payload["format_repair_policy"]["attempt"], 0)
        self.assertEqual(repair_payload["format_repair_policy"]["attempt"], 1)
        self.assertEqual(
            repair_payload["format_repair_policy"]["prior_model_call_ref"],
            model.audits[0].receipt.model_call_ref,
        )
        self.assertEqual(
            repair_payload["format_repair_policy"][
                "prior_model_call_receipt_ref"
            ],
            model.audits[0].receipt.digest.value,
        )
        self.assertEqual(
            repair_payload["format_repair_policy"]["prior_output_text"],
            "not-json",
        )
        self.assertEqual(
            repair_payload["format_repair_policy"][
                "validation_failure_category"
            ],
            "NON_JSON_OBJECT_PREFIX",
        )
        self.assertEqual(
            repair_payload["format_repair_policy"][
                "validation_failure_code"
            ],
            ErrorCode.STRUCTURED_OUTPUT_INVALID.value,
        )
        self.assertEqual(
            repair_payload["format_repair_policy"][
                "validation_failure_message"
            ],
            "$ JSON object envelope is invalid "
            "(first_non_whitespace_character_class="
            "NON_JSON_OBJECT_PREFIX; "
            "required_first_non_whitespace_character={; "
            "text_before_object_forbidden=true)",
        )

    def test_analysis_prefix_gets_explicit_bounded_envelope_repair(self) -> None:
        valid_primary = SequencedLiveAgentAdapter().outputs[1]
        invalid_primary = "Let me analyze the evidence first.\n" + valid_primary
        adapter = SequencedLiveAgentAdapter(
            outputs=(
                invalid_primary,
                valid_primary,
                '{"decision":"APPROVED","claim_assessments":[],"evidence_boundary_assessments":[],"boundary_relevance_assessments":[],"findings":[]}',
            )
        )
        service, model, _, _, tool, response = self._service(adapter=adapter)
        conversation = service.create_conversation()

        submission = service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=Revision(1),
            message="登录流程是怎样的？",
        )

        self.assertEqual(submission.turn.state, ConversationTurnState.SUCCEEDED)
        self.assertEqual(submission.turn.provider_dispatch_count, 3)
        self.assertEqual(len(model.audits), 3)
        self.assertEqual(tool.requests, [])
        self.assertEqual(len(response.requests), 1)
        self.assertTrue(
            adapter.requests[1].messages[0].content.startswith(
                "OUTPUT ENVELOPE IS MANDATORY FOR THIS ROLE."
            )
        )
        repair_payload = json.loads(adapter.requests[1].messages[1].content)
        repair_policy = repair_payload["format_repair_policy"]
        self.assertEqual(
            repair_policy["validation_failure_category"],
            "NON_JSON_OBJECT_PREFIX",
        )
        self.assertIn(
            "first_non_whitespace_character_class=NON_JSON_OBJECT_PREFIX",
            repair_policy["validation_failure_message"],
        )
        self.assertNotIn(
            "Let me analyze",
            repair_policy["validation_failure_message"],
        )
        repair_preflight = json.loads(adapter.requests[1].messages[-1].content)
        self.assertEqual(
            repair_preflight["schema"],
            "ENGINEERING_AGENT_OUTPUT_PREFLIGHT@10",
        )
        self.assertEqual(
            repair_preflight["format_repair"][
                "validation_failure_category"
            ],
            "NON_JSON_OBJECT_PREFIX",
        )
        self.assertTrue(
            repair_preflight["format_repair"][
                "repeat_same_failure_forbidden"
            ]
        )
        self.assertEqual(
            repair_preflight["output_envelope"][
                "required_first_non_whitespace_character"
            ],
            "{",
        )
        self.assertTrue(
            repair_preflight["output_envelope"][
                "analysis_or_narration_outside_object_forbidden"
            ]
        )
        self.assertNotIn("Let me analyze", adapter.requests[1].messages[-1].content)

    def test_unescaped_draft_quote_gets_bounded_json_syntax_repair(self) -> None:
        repaired = json.loads(SequencedLiveAgentAdapter().outputs[1])
        repaired["draft"]["content"] = '请明确"登录入口"。'
        repaired_output = json.dumps(repaired, ensure_ascii=False)
        malformed_output = repaired_output.replace(
            '\\"登录入口\\"',
            '"登录入口"',
            1,
        )
        self.assertNotEqual(malformed_output, repaired_output)
        with self.assertRaises(json.JSONDecodeError) as syntax_failure:
            json.loads(malformed_output)
        adapter = SequencedLiveAgentAdapter(
            outputs=(
                malformed_output,
                repaired_output,
                '{"decision":"APPROVED","claim_assessments":[],"evidence_boundary_assessments":[],"boundary_relevance_assessments":[],"findings":[]}',
            )
        )
        service, model, _, _, tool, response = self._service(adapter=adapter)
        conversation = service.create_conversation()

        submission = service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=Revision(1),
            message="登录流程是怎样的？",
        )

        self.assertEqual(submission.turn.state, ConversationTurnState.SUCCEEDED)
        self.assertEqual(submission.turn.provider_dispatch_count, 3)
        self.assertEqual(len(model.audits), 3)
        self.assertEqual(tool.requests, [])
        self.assertEqual(len(response.requests), 1)
        repair_payload = json.loads(
            next(
                item.content
                for item in adapter.requests[1].messages
                if item.input_item_id == "sealed-role-input"
            )
        )
        diagnostic = repair_payload["format_repair_policy"][
            "validation_failure_message"
        ]
        self.assertEqual(
            repair_payload["format_repair_policy"][
                "validation_failure_category"
            ],
            "JSON_SYNTAX_ERROR",
        )
        error = syntax_failure.exception
        self.assertEqual(
            diagnostic,
            "$ JSON syntax is invalid at "
            f"line {error.lineno}, column {error.colno}, "
            f"character {error.pos}: {error.msg}",
        )
        self.assertNotIn("登录入口", diagnostic)
        self.assertNotIn(malformed_output, diagnostic)
        repair_preflight = json.loads(adapter.requests[1].messages[-1].content)
        self.assertEqual(
            repair_preflight["format_repair"]["validation_failure_message"],
            diagnostic,
        )
        self.assertTrue(
            repair_preflight["json_serialization"][
                "parseable_json_object_required"
            ]
        )
        self.assertIn(
            "double quote",
            repair_preflight["json_serialization"][
                "embedded_double_quote_rule"
            ],
        )
        self.assertTrue(
            repair_preflight["json_serialization"]["parse_before_return"]
        )
        self.assertNotIn("prior_output_text", repair_preflight)
        self.assertNotIn(malformed_output, adapter.requests[1].messages[-1].content)

    def test_format_repair_projects_exact_missing_action_operation_diagnostic(self) -> None:
        capture = CapturingTurnExecutor()
        capture_service = InMemoryEngineeringConversationService(
            _binding(),
            turn_executor=capture,
            id_generator=SequenceIds(),
            clock=lambda: self.now,
        )
        conversation = capture_service.create_conversation()
        capture_service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=Revision(1),
            message="登录流程是怎样的？",
        )
        malformed = {
            "goal": "解释登录调用链",
            "response_language": "zh-CN",
            "audience": "software engineer",
            "constraints": ["local deterministic candidate only"],
            "resolved_referents": [],
            "accepted_correction_message_ids": [],
            "superseded_conclusion_refs": [],
            "hypotheses": ["需要查询版本化世界模型认知"],
            "plan": ["查询登录调用关系"],
            "open_items": ["登录调用关系"],
            "phase": "INVESTIGATING",
            "action": {
                "arguments": [],
                "evidence_need": "Locate the login service call relation",
                "ignore_previous_instructions": "untrusted output field",
            },
            "draft": None,
        }
        repaired = {
            **malformed,
            "action": {
                "operation": "WORLD_MODEL_QUERY",
                "arguments": [],
                "evidence_need": "Locate the login service call relation",
            },
        }
        adapter = SequencedLiveAgentAdapter(
            outputs=(
                json.dumps(malformed, ensure_ascii=False),
                json.dumps(repaired, ensure_ascii=False),
            )
        )
        _, model, _, _, _, _ = self._service(adapter=adapter)

        result = model.propose(
            EngineeringAgentInvocation(
                request=capture.request,
                previous_work_state=None,
                observations=(),
                review_findings=(),
                review_digest=None,
                available_operations=(
                    EngineeringAgentToolOperation.WORLD_MODEL_QUERY,
                ),
            )
        )

        self.assertEqual(
            result.proposal.action.operation,
            EngineeringAgentToolOperation.WORLD_MODEL_QUERY,
        )
        self.assertEqual(len(result.prior_receipts), 1)
        self.assertEqual(len(adapter.requests), 2)
        repair_payload = json.loads(
            next(
                item.content
                for item in adapter.requests[1].messages
                if item.input_item_id == "sealed-role-input"
            )
        )
        repair_policy = repair_payload["format_repair_policy"]
        self.assertEqual(
            repair_policy["validation_failure_category"],
            "CLOSED_SCHEMA_SHAPE",
        )
        self.assertEqual(
            repair_policy["validation_failure_code"],
            ErrorCode.STRUCTURED_OUTPUT_INVALID.value,
        )
        self.assertIn("$.action", repair_policy["validation_failure_message"])
        self.assertIn("operation", repair_policy["validation_failure_message"])
        self.assertIn(
            "allowed_exact=[arguments,evidence_need,operation]",
            repair_policy["validation_failure_message"],
        )
        self.assertIn(
            "unexpected_count=1",
            repair_policy["validation_failure_message"],
        )
        self.assertIn(
            "additional_fields_forbidden=true",
            repair_policy["validation_failure_message"],
        )
        self.assertNotIn(
            "ignore_previous_instructions",
            repair_policy["validation_failure_message"],
        )
        self.assertEqual(
            tuple(item["operation"] for item in repair_payload["tool_catalog"]),
            ("WORLD_MODEL_QUERY",),
        )
        self.assertEqual(
            repair_payload["tool_catalog"][0]["action_template"],
            {
                "operation": "WORLD_MODEL_QUERY",
                "arguments": [],
                "evidence_need": "",
            },
        )
        self.assertEqual(
            adapter.requests[1].messages[-1].input_item_id,
            "final-output-preflight",
        )
        repair_preflight = json.loads(adapter.requests[1].messages[-1].content)
        self.assertEqual(repair_preflight["format_repair"]["attempt"], 1)
        self.assertEqual(
            repair_preflight["format_repair"]["validation_failure_code"],
            ErrorCode.STRUCTURED_OUTPUT_INVALID.value,
        )
        self.assertEqual(
            repair_preflight["format_repair"]["validation_failure_message"],
            repair_policy["validation_failure_message"],
        )
        self.assertEqual(
            repair_preflight["non_null_action"][
                "effective_action_templates"
            ],
            [
                {
                    "operation": "WORLD_MODEL_QUERY",
                    "arguments": [],
                    "evidence_need": "",
                }
            ],
        )
        self.assertNotIn("prior_output_text", repair_preflight)

    def test_format_repair_projects_root_and_nested_shape_mismatches(self) -> None:
        capture = CapturingTurnExecutor()
        capture_service = InMemoryEngineeringConversationService(
            _binding(),
            turn_executor=capture,
            id_generator=SequenceIds(),
            clock=lambda: self.now,
        )
        conversation = capture_service.create_conversation()
        capture_service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=Revision(1),
            message="修订当前结论。",
        )
        repaired = json.loads(SequencedLiveAgentAdapter().outputs[1])
        repaired["phase"] = "INVESTIGATING"
        repaired["action"] = {
            "operation": "SOURCE_SEARCH",
            "arguments": [
                {"name": "evidence_class", "value": "SOURCE"},
                {"name": "query", "value": "UmsAdminController"},
            ],
            "evidence_need": "Locate the exact login entry point",
        }
        repaired["draft"] = None
        malformed_action = {
            key: value
            for key, value in repaired["action"].items()
            if key != "operation"
        }
        malformed_action["arguments"] = [
            {"evidence_class": "SOURCE"},
            repaired["action"]["arguments"][1],
        ]
        malformed_action["input_owned_hint"] = None
        malformed = {
            **repaired,
            "action": malformed_action,
            "input_owned_identity": "must-not-cross-the-output-boundary",
        }
        adapter = SequencedLiveAgentAdapter(
            outputs=(
                json.dumps(malformed, ensure_ascii=False),
                json.dumps(repaired, ensure_ascii=False),
            )
        )
        _, model, _, _, _, _ = self._service(adapter=adapter)

        result = model.propose(
            EngineeringAgentInvocation(
                request=capture.request,
                previous_work_state=None,
                observations=(),
                review_findings=(),
                review_digest=None,
                available_operations=(
                    EngineeringAgentToolOperation.SOURCE_SEARCH,
                ),
            )
        )

        self.assertEqual(
            result.proposal.action.operation,
            EngineeringAgentToolOperation.SOURCE_SEARCH,
        )
        self.assertEqual(len(result.prior_receipts), 1)
        self.assertEqual(len(adapter.requests), 2)
        repair_payload = json.loads(adapter.requests[1].messages[1].content)
        diagnostic = repair_payload["format_repair_policy"][
            "validation_failure_message"
        ]
        expected_fields = sorted(repaired)
        self.assertIn(
            f"allowed_exact=[{','.join(expected_fields)}]",
            diagnostic,
        )
        self.assertIn("$ object fields do not match", diagnostic)
        self.assertIn("$.action object fields do not match", diagnostic)
        self.assertIn(
            "$.action.arguments[0] object fields do not match",
            diagnostic,
        )
        self.assertIn("missing=[operation]", diagnostic)
        self.assertIn("missing=[name,value]", diagnostic)
        self.assertEqual(diagnostic.count("unexpected_count=1"), 3)
        self.assertIn("additional_fields_forbidden=true", diagnostic)
        self.assertNotIn("input_owned_identity", diagnostic)
        self.assertNotIn("input_owned_hint", diagnostic)
        preflight = json.loads(adapter.requests[1].messages[-1].content)
        self.assertEqual(
            sorted(preflight["required_top_level_fields"]),
            expected_fields,
        )
        self.assertEqual(
            preflight["format_repair"]["validation_failure_message"],
            diagnostic,
        )
        copy_policy = preflight["format_repair"]
        self.assertTrue(copy_policy["existing_values_exact_copy_required"])
        self.assertEqual(
            copy_policy["existing_values_application_restoration"],
            "RESTORE_SCHEMA_MATCHING_ALLOWLISTED_VALUES_BEFORE_DECODE@1",
        )
        self.assertFalse(
            copy_policy["application_restoration_generates_missing_fields"]
        )
        self.assertFalse(
            copy_policy["application_restoration_rebuilds_schema_invalid_subtrees"]
        )
        self.assertFalse(copy_policy["raw_repair_value_drift_authorized"])
        self.assertTrue(
            copy_policy["array_length_and_order_exact_copy_required"]
        )
        self.assertEqual(
            copy_policy["permitted_mutations"],
            [
                "ADD_MISSING_ALLOWLISTED_FIELD",
                "REMOVE_UNEXPECTED_FIELD",
                "REBUILD_SCHEMA_INVALID_SUBTREE_WITH_NO_EXISTING_ALLOWLISTED_VALUES",
            ],
        )
        projection = copy_policy["existing_allowed_field_copy_projection"]
        self.assertEqual(projection["goal"], repaired["goal"])
        self.assertEqual(
            projection["action"],
            {
                "arguments": [
                    {},
                    {"name": "query", "value": "UmsAdminController"},
                ],
                "evidence_need": "Locate the exact login entry point",
            },
        )
        projection_text = json.dumps(projection, ensure_ascii=False)
        self.assertNotIn("input_owned_identity", projection_text)
        self.assertNotIn("input_owned_hint", projection_text)
        self.assertNotIn("evidence_class", projection_text)
        self.assertIn(
            "exhaustive top-level allowlist",
            adapter.requests[1].messages[0].content,
        )
        self.assertIn(
            "Copy every projected primitive value and array length/order",
            adapter.requests[1].messages[0].content,
        )
        self.assertIn(
            "no existing allowlisted value",
            adapter.requests[1].messages[0].content,
        )
        self.assertIn(
            "Never infer a type relationship or catch boundary",
            adapter.requests[1].messages[0].content,
        )
        self.assertIn(
            "material affirmative conclusion in draft.content",
            adapter.requests[1].messages[0].content,
        )

    def test_closed_shape_repair_restores_existing_allowed_fields(self) -> None:
        capture = CapturingTurnExecutor()
        capture_service = InMemoryEngineeringConversationService(
            _binding(),
            turn_executor=capture,
            id_generator=SequenceIds(),
            clock=lambda: self.now,
        )
        conversation = capture_service.create_conversation()
        capture_service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=Revision(1),
            message="修订当前结论。",
        )
        valid = json.loads(SequencedLiveAgentAdapter().outputs[1])
        malformed = {
            **valid,
            "input_owned_identity": "must-not-cross-the-output-boundary",
        }
        semantic_drift = {
            **valid,
            "goal": "repair must not replace the original semantic proposal",
        }
        adapter = SequencedLiveAgentAdapter(
            outputs=(
                json.dumps(malformed, ensure_ascii=False),
                json.dumps(semantic_drift, ensure_ascii=False),
            )
        )
        _, model, _, _, _, _ = self._service(adapter=adapter)

        result = model.propose(
            EngineeringAgentInvocation(
                request=capture.request,
                previous_work_state=None,
                observations=(),
                review_findings=(),
                review_digest=None,
                available_operations=(
                    EngineeringAgentToolOperation.WORLD_MODEL_QUERY,
                ),
            )
        )

        self.assertEqual(result.proposal.goal, valid["goal"])
        self.assertNotEqual(result.proposal.goal, semantic_drift["goal"])
        self.assertEqual(len(adapter.requests), 2)
        self.assertTrue(model.audits[-1].receipt.successful)

    def test_closed_shape_repair_cannot_change_existing_array_length(self) -> None:
        capture = CapturingTurnExecutor()
        capture_service = InMemoryEngineeringConversationService(
            _binding(),
            turn_executor=capture,
            id_generator=SequenceIds(),
            clock=lambda: self.now,
        )
        conversation = capture_service.create_conversation()
        capture_service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=Revision(1),
            message="修订当前结论。",
        )
        valid = json.loads(SequencedLiveAgentAdapter().outputs[1])
        malformed = {
            **valid,
            "input_owned_identity": "must-not-cross-the-output-boundary",
        }
        array_drift = {
            **valid,
            "plan": [*valid["plan"], "repair must not append a plan item"],
        }
        adapter = SequencedLiveAgentAdapter(
            outputs=(
                json.dumps(malformed, ensure_ascii=False),
                json.dumps(array_drift, ensure_ascii=False),
            )
        )
        _, model, _, _, _, _ = self._service(adapter=adapter)

        with self.assertRaises(EngineeringAgentModelCallFailure) as failure:
            model.propose(
                EngineeringAgentInvocation(
                    request=capture.request,
                    previous_work_state=None,
                    observations=(),
                    review_findings=(),
                    review_digest=None,
                    available_operations=(
                        EngineeringAgentToolOperation.WORLD_MODEL_QUERY,
                    ),
                )
            )

        self.assertEqual(
            failure.exception.code,
            ErrorCode.STRUCTURED_OUTPUT_INVALID,
        )
        self.assertEqual(len(adapter.requests), 2)
        self.assertEqual(
            model.audits[-1].receipt.failure_kind,
            EngineeringAgentModelFailureKind.PROVIDER_OUTPUT_INVALID,
        )

    def test_closed_shape_repair_rebuilds_argument_array_without_copy_obligation(self) -> None:
        capture = CapturingTurnExecutor()
        capture_service = InMemoryEngineeringConversationService(
            _binding(),
            turn_executor=capture,
            id_generator=SequenceIds(),
            clock=lambda: self.now,
        )
        conversation = capture_service.create_conversation()
        capture_service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=Revision(1),
            message="解释 mall-search 的构建和启动依赖。",
        )
        repaired = json.loads(SequencedLiveAgentAdapter().outputs[1])
        repaired["phase"] = "INVESTIGATING"
        repaired["open_items"] = [
            "mall-search Spring Boot entry point unknown - no Java type observed"
        ]
        repaired["action"] = {
            "operation": "SOURCE_SEARCH",
            "arguments": [
                {"name": "evidence_class", "value": "BUILD_CONFIGURATION"},
                {"name": "query", "value": "docker-maven-plugin"},
            ],
            "evidence_need": "Locate the exact build plugin declaration",
        }
        repaired["draft"] = None
        malformed = {
            **repaired,
            "open_items": [
                "mall-search Spring Boot entry point unknown — no Java type observed"
            ],
            "action": {
                **repaired["action"],
                "arguments": [
                    {
                        "evidence_class": "BUILD_CONFIGURATION",
                        "query": "docker-maven-plugin",
                    }
                ],
            },
        }
        adapter = SequencedLiveAgentAdapter(
            outputs=(
                json.dumps(malformed, ensure_ascii=False),
                json.dumps(repaired, ensure_ascii=False),
            )
        )
        _, model, _, _, _, _ = self._service(adapter=adapter)

        result = model.propose(
            EngineeringAgentInvocation(
                request=capture.request,
                previous_work_state=None,
                observations=(),
                review_findings=(),
                review_digest=None,
                available_operations=(
                    EngineeringAgentToolOperation.SOURCE_SEARCH,
                ),
            )
        )

        self.assertEqual(
            result.proposal.open_items,
            (
                "mall-search Spring Boot entry point unknown — no Java type observed",
            ),
        )
        self.assertEqual(
            result.proposal.action.arguments,
            (
                ("evidence_class", "BUILD_CONFIGURATION"),
                ("query", "docker-maven-plugin"),
            ),
        )
        repair_preflight = json.loads(adapter.requests[1].messages[-1].content)
        action_projection = repair_preflight["format_repair"][
            "existing_allowed_field_copy_projection"
        ]["action"]
        self.assertNotIn("arguments", action_projection)

    def test_layered_format_repair_reaches_cross_disposition_claim_reference(self) -> None:
        capture = CapturingTurnExecutor()
        capture_service = InMemoryEngineeringConversationService(
            _binding(),
            turn_executor=capture,
            id_generator=SequenceIds(),
            clock=lambda: self.now,
        )
        conversation = capture_service.create_conversation()
        capture_service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=Revision(1),
            message="说明登录链，并明确当前证据边界。",
        )
        support = EngineeringAgentToolObservation(
            observation_id=StableId(f"observation_{'1' * 32}"),
            tool_request_id=StableId(f"tool_request_{'2' * 32}"),
            operation=EngineeringAgentToolOperation.WORLD_MODEL_QUERY,
            result_ref="support-result",
            content="sealed affirmative support",
            disposition=EngineeringAgentEvidenceDisposition.SUPPORT,
            progress=True,
            citation_refs=(),
            authority_receipt=None,
            tool_evidence_digest=digest_of("support-evidence"),
            digest=digest_of("support-observation"),
        )
        boundary = EngineeringAgentToolObservation(
            observation_id=StableId(f"observation_{'3' * 32}"),
            tool_request_id=StableId(f"tool_request_{'4' * 32}"),
            operation=EngineeringAgentToolOperation.WORLD_MODEL_QUERY,
            result_ref="boundary-result",
            content="sealed evidence boundary",
            disposition=EngineeringAgentEvidenceDisposition.BOUNDARY,
            progress=False,
            citation_refs=(),
            authority_receipt=None,
            tool_evidence_digest=digest_of("boundary-evidence"),
            digest=digest_of("boundary-observation"),
        )
        base = {
            "goal": "说明登录链",
            "response_language": "zh-CN",
            "audience": "software engineer",
            "constraints": [],
            "resolved_referents": [],
            "accepted_correction_message_ids": [],
            "superseded_conclusion_refs": [],
            "hypotheses": [],
            "plan": [],
            "open_items": [],
            "phase": "RESPONSE_READY",
            "action": None,
            "draft": {
                "response_kind": "ANSWER",
                "content": "当前证据支持登录链；运行时边界仍未知。",
                "claims": [
                    {
                        "statement": "当前证据支持登录链。",
                        "support_observation_ids": [
                            boundary.observation_id.value
                        ],
                    }
                ],
                "boundary_observation_ids": [boundary.observation_id.value],
            },
        }
        repaired = json.loads(json.dumps(base))
        repaired["draft"]["claims"][0]["support_observation_ids"] = [
            support.observation_id.value
        ]
        semantic_invalid_output = json.dumps(base, ensure_ascii=False)
        syntax_invalid_output = semantic_invalid_output.replace(
            "当前证据支持登录链；运行时边界仍未知。",
            "当前证据支持登录链；\n运行时边界仍未知。",
            1,
        )
        with self.assertRaises(json.JSONDecodeError):
            json.loads(syntax_invalid_output)
        adapter = SequencedLiveAgentAdapter(
            outputs=(
                syntax_invalid_output,
                semantic_invalid_output,
                json.dumps(repaired, ensure_ascii=False),
            )
        )
        _, model, _, _, _, _ = self._service(adapter=adapter)

        result = model.propose(
            EngineeringAgentInvocation(
                request=capture.request,
                previous_work_state=None,
                observations=(support, boundary),
                review_findings=(),
                review_digest=None,
                available_operations=(
                    EngineeringAgentToolOperation.WORLD_MODEL_QUERY,
                ),
            )
        )

        self.assertEqual(
            result.proposal.draft.claims[0].support_observation_ids,
            (support.observation_id,),
        )
        self.assertEqual(
            result.proposal.observation_ids,
            (support.observation_id, boundary.observation_id),
        )
        self.assertEqual(len(result.prior_receipts), 2)
        first_repair_payload = json.loads(
            next(
                item.content
                for item in adapter.requests[1].messages
                if item.input_item_id == "sealed-role-input"
            )
        )
        self.assertEqual(
            first_repair_payload["format_repair_policy"]["attempt"],
            1,
        )
        self.assertEqual(
            first_repair_payload["format_repair_policy"][
                "validation_failure_category"
            ],
            "JSON_SYNTAX_ERROR",
        )
        repair_payload = json.loads(
            next(
                item.content
                for item in adapter.requests[2].messages
                if item.input_item_id == "sealed-role-input"
            )
        )
        self.assertEqual(repair_payload["format_repair_policy"]["attempt"], 2)
        self.assertEqual(
            repair_payload["format_repair_policy"][
                "validation_failure_category"
            ],
            "CLOSED_OUTPUT_CONTRACT",
        )
        self.assertEqual(
            repair_payload["format_repair_policy"]["prior_model_call_ref"],
            model.audits[1].receipt.model_call_ref,
        )
        diagnostic = repair_payload["format_repair_policy"][
            "validation_failure_message"
        ]
        self.assertIn(
            "$.draft.claims[0].support_observation_ids[0]",
            diagnostic,
        )
        self.assertIn("answer_claim_support_observation_ids", diagnostic)
        self.assertIn("BOUNDARY IDs belong only", diagnostic)
        self.assertEqual(
            tuple(
                item["observation_id"]
                for item in repair_payload["current_turn_evidence"][
                    "support_observations"
                ]
            ),
            (support.observation_id.value,),
        )
        self.assertEqual(
            tuple(
                item["observation_id"]
                for item in repair_payload["current_turn_evidence"][
                    "boundary_observations"
                ]
            ),
            (boundary.observation_id.value,),
        )

    def test_format_repair_exhaustion_fails_closed_without_request_retry(self) -> None:
        adapter = SequencedLiveAgentAdapter(
            outputs=("not-json", "still-not-json")
        )
        service, model, _, _, tool, response = self._service(adapter=adapter)
        conversation = service.create_conversation()

        submission = service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=Revision(1),
            message="登录流程是怎样的？",
        )

        self.assertEqual(submission.turn.state, ConversationTurnState.FAILED)
        self.assertEqual(submission.turn.provider_dispatch_count, 2)
        self.assertEqual(len(submission.turn.model_dispatch_receipt_refs), 2)
        self.assertEqual(submission.turn.retry_count, 0)
        self.assertEqual(submission.turn.fallback_provider_attempt_count, 0)
        self.assertEqual(
            submission.turn.provider_failure_classification,
            EngineeringProviderFailureClassification.PROVIDER_OUTPUT_INVALID,
        )
        self.assertEqual(len(model.audits), 2)
        self.assertEqual(len(adapter.requests), 2)
        self.assertNotEqual(adapter.requests[0].digest, adapter.requests[1].digest)
        self.assertEqual(tool.requests, [])
        self.assertEqual(response.requests, [])

    def test_reviewer_invalid_output_gets_fresh_same_profile_repair_call(self) -> None:
        primary_output = SequencedLiveAgentAdapter().outputs[1]
        adapter = SequencedLiveAgentAdapter(
            outputs=(
                primary_output,
                "Reviewer natural-language analysis",
                '{"decision":"APPROVED","claim_assessments":[],"evidence_boundary_assessments":[],"boundary_relevance_assessments":[],"findings":[]}',
            )
        )
        service, model, _, _, tool, response = self._service(adapter=adapter)
        conversation = service.create_conversation()

        submission = service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=Revision(1),
            message="登录流程是怎样的？",
        )

        self.assertEqual(submission.turn.state, ConversationTurnState.SUCCEEDED)
        self.assertEqual(submission.turn.provider_dispatch_count, 3)
        self.assertEqual(submission.turn.retry_count, 0)
        self.assertEqual(len(adapter.requests), 3)
        self.assertEqual(
            model.audits[1].receipt.failure_kind,
            EngineeringAgentModelFailureKind.PROVIDER_OUTPUT_INVALID,
        )
        self.assertTrue(model.audits[2].receipt.successful)
        self.assertNotEqual(adapter.requests[1].digest, adapter.requests[2].digest)
        reviewer_repair_payload = json.loads(
            next(
                item.content
                for item in adapter.requests[2].messages
                if item.input_item_id == "sealed-role-input"
            )
        )
        self.assertEqual(
            reviewer_repair_payload["format_repair_policy"]["attempt"], 1
        )
        self.assertEqual(
            reviewer_repair_payload["format_repair_policy"][
                "prior_output_text"
            ],
            "Reviewer natural-language analysis",
        )
        reviewer_preflight = json.loads(
            adapter.requests[2].messages[-1].content
        )
        self.assertEqual(
            reviewer_preflight["schema"],
            "ENGINEERING_AGENT_OUTPUT_PREFLIGHT@10",
        )
        self.assertEqual(
            reviewer_repair_payload["format_repair_policy"][
                "validation_failure_category"
            ],
            "NON_JSON_OBJECT_PREFIX",
        )
        self.assertTrue(
            reviewer_preflight["json_serialization"][
                "parseable_json_object_required"
            ]
        )
        self.assertTrue(
            reviewer_preflight["json_serialization"]["parse_before_return"]
        )
        self.assertTrue(
            reviewer_preflight["format_repair"][
                "authored_string_surrounding_whitespace_forbidden"
            ]
        )
        self.assertEqual(
            reviewer_preflight["closed_nested_object_fields"][
                "$.boundary_relevance_assessments[]"
            ],
            [
                "challenge_id",
                "user_requirement",
                "boundary_scope",
                "disposition",
                "finding_code",
            ],
        )
        self.assertEqual(
            reviewer_preflight["closed_nested_object_fields"]["$.findings[]"],
            ["code", "message", "requires_evidence", "claim_index"],
        )
        self.assertEqual(
            reviewer_preflight["review_output_contract"][
                "challenge_id_field_name_exact"
            ],
            "challenge_id",
        )
        self.assertTrue(
            reviewer_preflight["review_output_contract"][
                "existing_shape_repair_values_may_not_be_changed_for_consistency"
            ]
        )
        reviewer_policy = reviewer_repair_payload[
            "review_reference_policy"
        ]
        self.assertTrue(
            reviewer_policy[
                "container_context_is_part_of_contained_assertion"
            ]
        )
        self.assertTrue(
            reviewer_policy[
                "inherited_material_qualifier_omission_is_global_completeness_finding"
            ]
        )
        self.assertIsNone(
            reviewer_policy["global_completeness_finding_claim_index"]
        )
        self.assertTrue(
            reviewer_policy[
                "claim_coverage_is_semantic_not_one_entry_per_phrase"
            ]
        )
        self.assertTrue(
            reviewer_policy[
                "grouped_claim_may_cover_multiple_assertions_when_all_material_qualifiers_present"
            ]
        )
        self.assertTrue(
            reviewer_policy[
                "global_completeness_requires_no_semantically_covering_claim"
            ]
        )
        self.assertEqual(
            reviewer_policy["trusted_repository_revision_attribution"],
            _binding().repository_revision,
        )
        self.assertTrue(
            reviewer_policy[
                "matching_repository_revision_attribution_is_not_standalone_claim"
            ]
        )
        self.assertTrue(
            reviewer_policy[
                "pure_unresolved_boundary_statement_is_not_affirmative_claim"
            ]
        )
        self.assertTrue(
            reviewer_policy[
                "limitation_empty_claim_inventory_is_valid_for_pure_boundaries"
            ]
        )
        self.assertTrue(
            reviewer_policy["evidence_gap_is_not_authority_denial"]
        )
        self.assertTrue(
            reviewer_policy[
                "authorization_limitation_requires_exact_boundary"
            ]
        )
        self.assertTrue(
            reviewer_policy[
                "producer_invocation_is_not_consumer_visible_effect"
            ]
        )
        self.assertTrue(
            reviewer_policy[
                "consumer_visible_effect_requires_consumer_path_support"
            ]
        )
        self.assertFalse(
            reviewer_policy["audit_retention_requires_answer_disclosure"]
        )
        self.assertTrue(
            reviewer_policy[
                "structured_boundary_reference_is_evidence_binding_not_full_text_disclosure"
            ]
        )
        self.assertTrue(
            reviewer_policy[
                "boundary_metadata_absent_from_draft_content_is_not_disclosed"
            ]
        )
        self.assertTrue(
            reviewer_policy[
                "bound_boundary_id_need_not_be_named_or_raw_disclosed"
            ]
        )
        self.assertTrue(
            reviewer_policy[
                "limitation_requires_at_least_one_boundary_reference"
            ]
        )
        self.assertTrue(
            reviewer_policy[
                "removing_last_material_limitation_boundary_without_replacement_forbidden"
            ]
        )
        self.assertTrue(
            reviewer_policy[
                "answer_boundary_requires_unresolved_material_requirement_or_explicit_diagnostic_request"
            ]
        )
        self.assertFalse(
            reviewer_policy[
                "resolved_acquisition_candidate_is_automatic_exclusion"
            ]
        )
        self.assertTrue(
            reviewer_policy[
                "global_inventory_metrics_require_material_user_relevance"
            ]
        )
        self.assertTrue(
            reviewer_policy[
                "answer_detail_requires_material_user_relevance"
            ]
        )
        self.assertTrue(
            reviewer_policy[
                "counterfactual_omission_preserving_requested_conclusions_means_omit"
            ]
        )
        self.assertFalse(
            reviewer_policy[
                "self_introduced_adjacent_detail_allows_evidence_expansion"
            ]
        )
        self.assertTrue(
            reviewer_policy[
                "generation_or_tool_provenance_requires_direct_support"
            ]
        )
        reviewer_prompt = adapter.requests[2].messages[0].content
        self.assertIn(
            "Compare the complete draft.content against the enumerated claims",
            reviewer_prompt,
        )
        self.assertIn(
            "global completeness Finding",
            reviewer_prompt,
        )
        self.assertIn(
            "Perform this comparison semantically, not by requiring one Claim per phrase",
            reviewer_prompt,
        )
        self.assertIn(
            "exact repository_revision sealed in turn.binding is provenance context",
            reviewer_prompt,
        )
        self.assertIn(
            "does not make an otherwise valid LIMITATION with an empty",
            reviewer_prompt,
        )
        self.assertIn(
            "Reconstruct every content assertion with the category, scope, condition",
            reviewer_prompt,
        )
        self.assertIn(
            "Do not conflate an evidence or coverage gap with an authorization denial",
            reviewer_prompt,
        )
        self.assertIn(
            "Check producer-side calls and consumer-visible runtime effects separately",
            reviewer_prompt,
        )
        self.assertIn(
            "Audit retention does not make every BOUNDARY relevant",
            reviewer_prompt,
        )
        self.assertIn(
            "automatic user-visible disclosure",
            reviewer_prompt,
        )
        self.assertIn(
            "Never return a Finding merely because draft.content does not name an opaque",
            reviewer_prompt,
        )
        self.assertIn(
            "Irrelevant or resolved diagnostics are a relevance defect",
            reviewer_prompt,
        )
        self.assertIn(
            "Apply the same counterfactual relevance test to every affirmative detail",
            reviewer_prompt,
        )
        self.assertIn(
            "never expand the investigation merely to",
            reviewer_prompt,
        )
        self.assertIn("code-generation or tool", reviewer_prompt)
        self.assertIn(
            "approval of the narrower claim does not approve its container",
            reviewer_prompt,
        )
        self.assertIn(
            "claim_index null and preserve",
            reviewer_prompt,
        )
        self.assertIn(
            "set requires_evidence=true only when the current Package lacks",
            reviewer_prompt,
        )
        self.assertIn(
            "requires_evidence=false",
            reviewer_prompt,
        )
        self.assertIn(
            "when deleting, narrowing, qualifying, or reorganizing",
            reviewer_prompt,
        )
        self.assertIn(
            "Do not reject a Draft that states only",
            reviewer_prompt,
        )
        self.assertEqual(tool.requests, [])
        self.assertEqual(len(response.requests), 1)

    def test_sealed_http_failure_is_preserved_as_raw_route_evidence(self) -> None:
        service, model, _, adapter, _, _ = self._service(
            failure_code=ErrorCode.PROVIDER_HTTP_ERROR,
            failure_details={
                "http_status": 503,
                "provider_error_code": "service_unavailable",
                "provider_request_id": "safe-request-1",
            },
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
        self.assertEqual(submission.turn.provider_http_status, 503)
        self.assertIsNotNone(
            submission.turn.provider_http_failure_evidence_digest
        )
        self.assertEqual(model.audits[0].receipt.provider_http_status, 503)
        self.assertEqual(
            model.audits[0].receipt.provider_http_failure_evidence_digest,
            submission.turn.provider_http_failure_evidence_digest,
        )

    def test_typed_provider_unavailable_is_preserved_as_raw_route_evidence(self) -> None:
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

    def test_primary_input_projects_closed_tool_copy_domains_and_rejects_drift(self) -> None:
        capture = CapturingTurnExecutor()
        service = InMemoryEngineeringConversationService(
            _binding(),
            turn_executor=capture,
            id_generator=SequenceIds(),
            clock=lambda: self.now,
        )
        conversation = service.create_conversation()
        service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=Revision(1),
            message="登录失败时记录什么？",
        )
        locator_reference = "source_locator_" + "5" * 32
        same_resource_reference = "source_locator_" + "4" * 32
        other_resource_reference = "source_locator_" + "3" * 32
        citation = EngineeringAgentCitation.create(
            citation_ref=locator_reference,
            evidence_class="SOURCE",
            source_revision=capture.request.binding.repository_revision,
            locator="src/main/java/example/LoginService.java:L10",
            modality="JAVA_SOURCE",
            content_digest=digest_of("login-source"),
        )
        same_resource_citation = EngineeringAgentCitation.create(
            citation_ref=same_resource_reference,
            evidence_class="SOURCE",
            source_revision=capture.request.binding.repository_revision,
            locator="src/main/java/example/LoginService.java:L20-L24",
            modality="JAVA_SOURCE",
            content_digest=digest_of("same-login-source"),
        )
        other_resource_citation = EngineeringAgentCitation.create(
            citation_ref=other_resource_reference,
            evidence_class="SOURCE",
            source_revision=capture.request.binding.repository_revision,
            locator="src/main/java/example/AuthConfig.java:L5",
            modality="JAVA_SOURCE",
            content_digest=digest_of("auth-config-source"),
        )
        evidence_request_digest = digest_of("source-evidence-request")
        ledger_ref = "evidence_ledger_" + "9" * 32
        authority_receipt = EngineeringAgentToolAuthorityReceipt.create(
            authority_kind=EngineeringAgentToolAuthorityKind.SOURCE,
            turn_request_digest=capture.request.request_digest,
            tool_request_digest=digest_of("source-tool-request"),
            evidence_request_digest=evidence_request_digest,
            repository_revision=capture.request.binding.repository_revision,
            evidence_digest=digest_of("source-result"),
            ledger_ref=ledger_ref,
            ledger_generation=1,
            ledger_parent_seal_digest=None,
            ledger_prefix_digest=digest_of(
                [
                    "EVIDENCE_LEDGER_PREFIX@1",
                    ledger_ref,
                    evidence_request_digest.value,
                    1,
                    None,
                    (),
                ]
            ),
            ledger_entries=(),
            citations=(citation, same_resource_citation, other_resource_citation),
        )
        observation = EngineeringAgentToolObservation(
            observation_id=StableId(f"observation_{'6' * 32}"),
            tool_request_id=StableId(f"tool_request_{'7' * 32}"),
            operation=EngineeringAgentToolOperation.SOURCE_SEARCH,
            result_ref="search-support",
            content="sealed search evidence",
            disposition=EngineeringAgentEvidenceDisposition.SUPPORT,
            progress=True,
            citation_refs=(
                locator_reference,
                same_resource_reference,
                other_resource_reference,
            ),
            authority_receipt=authority_receipt,
            tool_evidence_digest=digest_of("search-evidence"),
            digest=digest_of("search-observation"),
        )
        prior_search = EngineeringAgentToolActionProposal.create(
            operation=EngineeringAgentToolOperation.SOURCE_SEARCH,
            arguments=(("evidence_class", "SOURCE"), ("query", "login")),
            evidence_need="locate login behavior",
        )
        invocation = EngineeringAgentInvocation(
            request=capture.request,
            previous_work_state=None,
            observations=(observation,),
            review_findings=(),
            review_digest=None,
            available_operations=(
                EngineeringAgentToolOperation.SOURCE_SEARCH,
                EngineeringAgentToolOperation.SOURCE_READ,
            ),
            action_history=(prior_search,),
        )
        rendered_invocation = _primary_input_view(invocation)
        policy = rendered_invocation["tool_reference_policy"]
        work_state_policy = rendered_invocation["work_state_reference_policy"]

        self.assertEqual(
            rendered_invocation["tool_action_budget"],
            {
                "schema": "ENGINEERING_AGENT_TOOL_ACTION_BUDGET@1",
                "maximum": 8,
                "used": 1,
                "remaining": 7,
                "remaining_is_not_a_consumption_target": True,
                "zero_remaining_allows_new_tool_action": False,
            },
        )
        self.assertEqual(policy["source_search_queries_already_attempted"], ("login",))
        self.assertEqual(
            work_state_policy["required_current_turn_observation_ids"],
            (observation.observation_id.value,),
        )
        self.assertFalse(
            work_state_policy["prior_turn_observation_ids_authorized"]
        )
        self.assertEqual(
            work_state_policy["current_user_message_id"],
            capture.request.user_message.message_id.value,
        )
        self.assertEqual(
            tuple(item["locator_reference"] for item in policy["source_read_options"]),
            (locator_reference, other_resource_reference),
        )
        self.assertIsNone(policy["source_file_budget"])
        self.assertEqual(
            tuple(item["resource_locator"] for item in policy["source_read_options"]),
            (
                "src/main/java/example/LoginService.java",
                "src/main/java/example/AuthConfig.java",
            ),
        )
        self.assertEqual(
            policy["source_read_options"][0]["content_digest"],
            citation.content_digest.value,
        )
        self.assertTrue(policy["exact_action_repetition_forbidden"])
        self.assertTrue(policy["unlisted_source_read_reference_forbidden"])
        self.assertEqual(
            tuple(item["operation"] for item in rendered_invocation["tool_catalog"]),
            ("SOURCE_SEARCH", "SOURCE_READ"),
        )
        rendered_tools = {
            item["operation"]: item for item in rendered_invocation["tool_catalog"]
        }
        self.assertEqual(
            rendered_tools["SOURCE_SEARCH"]["action_template"],
            {
                "operation": "SOURCE_SEARCH",
                "arguments": (
                    {"name": "evidence_class", "value": ""},
                    {"name": "query", "value": ""},
                ),
                "evidence_need": "",
            },
        )
        self.assertEqual(
            rendered_tools["SOURCE_READ"]["action_template"],
            {
                "operation": "SOURCE_READ",
                "arguments": (
                    {"name": "locator_reference", "value": ""},
                ),
                "evidence_need": "",
            },
        )
        self.assertEqual(
            rendered_invocation["completion_policy"]["allowed_response_kinds"],
            ("ANSWER", "CLARIFICATION"),
        )
        self.assertEqual(
            rendered_tools["SOURCE_SEARCH"]["value_constraints"][
                "forbidden_exact_values"
            ],
            ("login",),
        )
        self.assertEqual(
            rendered_tools["SOURCE_READ"]["value_constraints"][
                "allowed_exact_values"
            ],
            (locator_reference, other_resource_reference),
        )
        exhausted_invocation = replace(
            invocation,
            maximum_tool_actions=1,
        )
        exhausted_view = _primary_input_view(exhausted_invocation)
        self.assertEqual(exhausted_view["tool_catalog"], ())
        self.assertEqual(
            exhausted_view["tool_action_budget"]["remaining"],
            0,
        )
        self.assertFalse(
            exhausted_view["completion_policy"]["tool_action_allowed"]
        )
        self.assertTrue(
            exhausted_view["completion_policy"]["draft_required"]
        )
        exhausted_payload = {
            "goal": "确认登录失败记录",
            "response_language": "zh-CN",
            "audience": "software engineer",
            "constraints": [],
            "resolved_referents": [],
            "accepted_correction_message_ids": [],
            "superseded_conclusion_refs": [],
            "hypotheses": [],
            "plan": [],
            "open_items": [],
            "phase": "INVESTIGATING",
            "action": {
                "operation": "SOURCE_SEARCH",
                "arguments": [
                    {"name": "evidence_class", "value": "SOURCE"},
                    {"name": "query", "value": "UmsAdminServiceImpl"},
                ],
                "evidence_need": "locate the service implementation",
            },
            "draft": None,
        }
        with self.assertRaises(DomainError) as exhausted_without_draft:
            decode_engineering_agent_primary_output(
                output_text=json.dumps(exhausted_payload),
                invocation=exhausted_invocation,
                model_call_ref="exhausted-without-draft-call",
            )
        self.assertEqual(
            exhausted_without_draft.exception.code,
            ErrorCode.STRUCTURED_OUTPUT_INVALID,
        )
        unreceipted_view = _primary_input_view(
            replace(
                invocation,
                observations=(replace(observation, authority_receipt=None),),
            )
        )
        unreceipted_policy = unreceipted_view["tool_reference_policy"]
        self.assertEqual(unreceipted_policy["source_read_options"], ())
        self.assertEqual(
            tuple(item["operation"] for item in unreceipted_view["tool_catalog"]),
            ("SOURCE_SEARCH",),
        )

        preissued_reference = StableId(
            "required_path_locator_" + "2" * 32
        )
        preissued = EngineeringAgentSourceReadOption.create(
            locator_reference=preissued_reference,
            locator="src/main/java/example/LoginService.java",
            evidence_class="SOURCE",
            source_revision=capture.request.binding.repository_revision,
            modality="EXACT_STATIC_SOURCE_TEXT",
            content_digest=digest_of("prior-full-login-source"),
            origin_turn_id=StableId("turn_" + "1" * 32),
            origin_citation_digest=digest_of("prior-login-citation"),
        )
        preissued_invocation = replace(
            invocation,
            observations=(),
            action_history=(),
            preissued_source_read_options=(preissued,),
        )
        preissued_view = _primary_input_view(preissued_invocation)
        preissued_policy = preissued_view["tool_reference_policy"]
        self.assertEqual(
            preissued_policy["source_read_options"],
            (
                {
                    "locator_reference": preissued_reference.value,
                    "locator": "src/main/java/example/LoginService.java",
                    "resource_locator": (
                        "src/main/java/example/LoginService.java"
                    ),
                    "evidence_class": "SOURCE",
                    "modality": "EXACT_STATIC_SOURCE_TEXT",
                    "content_digest": preissued.content_digest.value,
                    "source_observation_id": None,
                    "origin": "PRIOR_TURN_EXACT_SOURCE_REVALIDATION",
                    "origin_turn_id": preissued.origin_turn_id.value,
                    "origin_citation_digest": (
                        preissued.origin_citation_digest.value
                    ),
                },
            ),
        )
        self.assertEqual(
            tuple(item["operation"] for item in preissued_view["tool_catalog"]),
            ("SOURCE_SEARCH", "SOURCE_READ"),
        )
        self.assertFalse(
            preissued_view["investigation_policy"][
                "world_model_first_before_source_required"
            ]
        )
        preissued_payload = {
            "goal": "确认登录失败记录",
            "response_language": "zh-CN",
            "audience": "software engineer",
            "constraints": [],
            "resolved_referents": [],
            "accepted_correction_message_ids": [],
            "superseded_conclusion_refs": [],
            "hypotheses": [],
            "plan": [],
            "open_items": [],
            "phase": "INVESTIGATING",
            "action": {
                "operation": "SOURCE_READ",
                "arguments": [
                    {
                        "name": "locator_reference",
                        "value": preissued_reference.value,
                    }
                ],
                "evidence_need": "revalidate the prior exact resource",
            },
            "draft": None,
        }
        preissued_proposal = decode_engineering_agent_primary_output(
            output_text=json.dumps(preissued_payload),
            invocation=preissued_invocation,
            model_call_ref="trusted-preissued-read-call",
        )
        self.assertEqual(
            dict(preissued_proposal.action.arguments)["locator_reference"],
            preissued_reference.value,
        )

        payload = {
            "goal": "确认登录失败记录",
            "response_language": "zh-CN",
            "audience": "software engineer",
            "constraints": [],
            "resolved_referents": [],
            "accepted_correction_message_ids": [],
            "superseded_conclusion_refs": [],
            "hypotheses": [],
            "plan": [],
            "open_items": [],
            "phase": "INVESTIGATING",
            "action": {
                "operation": "SOURCE_READ",
                "arguments": [
                    {"name": "locator_reference", "value": locator_reference}
                ],
                "evidence_need": "read the exact selected artifact",
            },
            "draft": None,
        }
        proposal = decode_engineering_agent_primary_output(
            output_text=json.dumps(payload),
            invocation=invocation,
            model_call_ref="trusted-read-call",
        )
        self.assertEqual(
            dict(proposal.action.arguments)["locator_reference"],
            locator_reference,
        )

        resource_details = tuple(
            sorted(
                {
                    "maximum_source_files": "64",
                    "source_files": "63",
                }.items()
            )
        )
        resource_subject_digest = digest_of(
            ["test-source-resource-receipt", resource_details]
        )
        resource_entry_core = {
            "ledger_id": ledger_ref,
            "sequence": 1,
            "kind": "RESOURCE_RECEIPT",
            "subject_id": "resource_receipt_" + "8" * 32,
            "subject_digest": resource_subject_digest.value,
            "references": (),
            "details": resource_details,
            "previous_entry_digest": None,
        }
        resource_source_digest = digest_of(
            ["EVIDENCE_LEDGER_ENTRY@1", resource_entry_core]
        )
        resource_entry = EngineeringAgentLedgerEntryReceipt.create(
            sequence=1,
            kind="RESOURCE_RECEIPT",
            subject_ref=resource_entry_core["subject_id"],
            subject_digest=resource_subject_digest,
            references=(),
            details=resource_details,
            previous_entry_digest=None,
            source_entry_digest=resource_source_digest,
        )
        budget_receipt = EngineeringAgentToolAuthorityReceipt.create(
            authority_kind=EngineeringAgentToolAuthorityKind.SOURCE,
            turn_request_digest=capture.request.request_digest,
            tool_request_digest=authority_receipt.tool_request_digest,
            evidence_request_digest=evidence_request_digest,
            repository_revision=capture.request.binding.repository_revision,
            evidence_digest=authority_receipt.evidence_digest,
            ledger_ref=ledger_ref,
            ledger_generation=1,
            ledger_parent_seal_digest=None,
            ledger_prefix_digest=digest_of(
                [
                    "EVIDENCE_LEDGER_PREFIX@1",
                    ledger_ref,
                    evidence_request_digest.value,
                    1,
                    None,
                    (resource_source_digest.value,),
                ]
            ),
            ledger_entries=(resource_entry,),
            citations=authority_receipt.citations,
        )
        reserved_invocation = replace(
            invocation,
            observations=(
                replace(observation, authority_receipt=budget_receipt),
            ),
        )
        reserved_view = _primary_input_view(reserved_invocation)
        self.assertEqual(
            reserved_view["tool_reference_policy"]["source_file_budget"],
            {
                "schema": "ENGINEERING_AGENT_SOURCE_FILE_BUDGET@1",
                "used": 63,
                "maximum": 64,
                "remaining": 1,
                "exhausted": False,
            },
        )
        self.assertEqual(
            tuple(item["operation"] for item in reserved_view["tool_catalog"]),
            ("SOURCE_READ",),
        )
        reserved_search_payload = {
            **payload,
            "action": {
                "operation": "SOURCE_SEARCH",
                "arguments": [
                    {"name": "evidence_class", "value": "SOURCE"},
                    {"name": "query", "value": "generateToken"},
                ],
                "evidence_need": "search after a locator is already available",
            },
        }
        with self.assertRaises(DomainError) as reserved_search:
            decode_engineering_agent_primary_output(
                output_text=json.dumps(reserved_search_payload),
                invocation=reserved_invocation,
                model_call_ref="reserved-source-read-slot-call",
            )
        self.assertEqual(
            reserved_search.exception.code,
            ErrorCode.STRUCTURED_OUTPUT_INVALID,
        )

        exhausted_resource_details = tuple(
            sorted(
                {
                    "maximum_source_files": "64",
                    "source_files": "64",
                }.items()
            )
        )
        exhausted_resource_subject_digest = digest_of(
            ["test-source-resource-receipt", exhausted_resource_details]
        )
        exhausted_resource_entry_core = {
            **resource_entry_core,
            "subject_id": "resource_receipt_" + "7" * 32,
            "subject_digest": exhausted_resource_subject_digest.value,
            "details": exhausted_resource_details,
        }
        exhausted_resource_source_digest = digest_of(
            ["EVIDENCE_LEDGER_ENTRY@1", exhausted_resource_entry_core]
        )
        exhausted_resource_entry = EngineeringAgentLedgerEntryReceipt.create(
            sequence=1,
            kind="RESOURCE_RECEIPT",
            subject_ref=exhausted_resource_entry_core["subject_id"],
            subject_digest=exhausted_resource_subject_digest,
            references=(),
            details=exhausted_resource_details,
            previous_entry_digest=None,
            source_entry_digest=exhausted_resource_source_digest,
        )
        exhausted_budget_receipt = EngineeringAgentToolAuthorityReceipt.create(
            authority_kind=EngineeringAgentToolAuthorityKind.SOURCE,
            turn_request_digest=capture.request.request_digest,
            tool_request_digest=authority_receipt.tool_request_digest,
            evidence_request_digest=evidence_request_digest,
            repository_revision=capture.request.binding.repository_revision,
            evidence_digest=authority_receipt.evidence_digest,
            ledger_ref=ledger_ref,
            ledger_generation=1,
            ledger_parent_seal_digest=None,
            ledger_prefix_digest=digest_of(
                [
                    "EVIDENCE_LEDGER_PREFIX@1",
                    ledger_ref,
                    evidence_request_digest.value,
                    1,
                    None,
                    (exhausted_resource_source_digest.value,),
                ]
            ),
            ledger_entries=(exhausted_resource_entry,),
            citations=authority_receipt.citations,
        )
        source_exhausted_invocation = replace(
            invocation,
            observations=(
                replace(
                    observation,
                    authority_receipt=exhausted_budget_receipt,
                ),
            ),
        )
        source_exhausted_view = _primary_input_view(
            source_exhausted_invocation
        )
        source_exhausted_policy = source_exhausted_view[
            "tool_reference_policy"
        ]
        self.assertEqual(
            source_exhausted_policy["source_file_budget"],
            {
                "schema": "ENGINEERING_AGENT_SOURCE_FILE_BUDGET@1",
                "used": 64,
                "maximum": 64,
                "remaining": 0,
                "exhausted": True,
            },
        )
        self.assertEqual(source_exhausted_policy["source_read_options"], ())
        self.assertIsNone(
            source_exhausted_policy["terminal_source_denial_reason"]
        )
        self.assertEqual(source_exhausted_view["tool_catalog"], ())
        with self.assertRaises(DomainError) as exhausted_source_read:
            decode_engineering_agent_primary_output(
                output_text=json.dumps(payload),
                invocation=source_exhausted_invocation,
                model_call_ref="exhausted-source-read-call",
            )
        self.assertEqual(
            exhausted_source_read.exception.code,
            ErrorCode.STRUCTURED_OUTPUT_INVALID,
        )

        prior_read = EngineeringAgentToolActionProposal.create(
            operation=EngineeringAgentToolOperation.SOURCE_READ,
            arguments=(("locator_reference", locator_reference),),
            evidence_need="read the selected login resource",
        )
        after_read_invocation = replace(
            invocation,
            action_history=(prior_search, prior_read),
        )
        after_read_policy = _primary_input_view(after_read_invocation)[
            "tool_reference_policy"
        ]
        self.assertEqual(
            after_read_policy["source_read_resource_locators_already_attempted"],
            ("src/main/java/example/LoginService.java",),
        )
        self.assertEqual(
            tuple(
                item["locator_reference"]
                for item in after_read_policy["source_read_options"]
            ),
            (other_resource_reference,),
        )
        payload["action"]["arguments"][0]["value"] = same_resource_reference
        with self.assertRaises(DomainError) as same_resource_read:
            decode_engineering_agent_primary_output(
                output_text=json.dumps(payload),
                invocation=after_read_invocation,
                model_call_ref="same-resource-read-call",
            )
        self.assertEqual(
            same_resource_read.exception.code,
            ErrorCode.STRUCTURED_OUTPUT_INVALID,
        )

        payload["action"]["arguments"][0]["value"] = (
            "source_locator_" + "8" * 32
        )
        with self.assertRaises(DomainError) as forged:
            decode_engineering_agent_primary_output(
                output_text=json.dumps(payload),
                invocation=invocation,
                model_call_ref="forged-read-call",
            )
        self.assertEqual(forged.exception.code, ErrorCode.STRUCTURED_OUTPUT_INVALID)

        payload["action"]["arguments"] = [
            {"name": "path", "value": "src/main/java/example/LoginService.java"}
        ]
        with self.assertRaises(DomainError) as argument_drift:
            decode_engineering_agent_primary_output(
                output_text=json.dumps(payload),
                invocation=invocation,
                model_call_ref="drifted-read-call",
            )
        self.assertEqual(
            argument_drift.exception.code,
            ErrorCode.STRUCTURED_OUTPUT_INVALID,
        )

        payload["action"] = {
            "operation": "SOURCE_SEARCH",
            "arguments": [
                {"name": "evidence_class", "value": "SOURCE"},
                {"name": "query", "value": "login"},
            ],
            "evidence_need": "repeat the same search",
        }
        with self.assertRaises(DomainError) as repeated:
            decode_engineering_agent_primary_output(
                output_text=json.dumps(payload),
                invocation=invocation,
                model_call_ref="repeated-search-call",
            )
        self.assertEqual(repeated.exception.code, ErrorCode.STRUCTURED_OUTPUT_INVALID)

        payload["action"]["arguments"][0]["value"] = "TEST"
        with self.assertRaises(DomainError) as repeated_query:
            decode_engineering_agent_primary_output(
                output_text=json.dumps(payload),
                invocation=invocation,
                model_call_ref="repeated-search-query-call",
            )
        self.assertEqual(
            repeated_query.exception.code,
            ErrorCode.STRUCTURED_OUTPUT_INVALID,
        )

        reviewed_work_state = SimpleNamespace(
            work_state_id=StableId(f"work_state_{'8' * 32}"),
            conversation_id=(
                capture.request.snapshot_before.conversation.conversation_id
            ),
            turn_id=capture.request.turn_id,
            revision=Revision(1),
            previous_digest=None,
            context_digest=capture.request.snapshot_before.context.digest,
            goal="确认登录失败记录",
            response_language="zh-CN",
            audience="software engineer",
            constraints=(),
            resolved_referents=(),
            accepted_correction_message_ids=(),
            superseded_conclusion_refs=(),
            hypotheses=(),
            plan=(),
            observation_ids=(observation.observation_id,),
            open_items=(),
            phase=SimpleNamespace(value="RESPONSE_READY"),
            review_input_digest=None,
            proposal_digest=digest_of("reviewed proposal"),
            digest=digest_of("reviewed work state"),
        )
        reviewed_claim = EngineeringAgentClaimProposal.create(
            statement="当前证据支持这一条登录结论。",
            support_observation_ids=(observation.observation_id,),
        )
        reviewed_answer_id = StableId(f"agent_answer_{'9' * 32}")
        reviewed_package_digest = digest_of("reviewed package")
        reviewed_draft_core = {
            "schema": "ENGINEERING_AGENT_ANSWER@1",
            "answer_id": reviewed_answer_id.value,
            "turn_id": capture.request.turn_id.value,
            "work_state_digest": reviewed_work_state.digest.value,
            "package_digest": reviewed_package_digest.value,
            "response_kind": "ANSWER",
            "content": "当前证据支持这一条登录结论。",
            "claims": (
                {
                    "statement": reviewed_claim.statement,
                    "support_observation_ids": (
                        observation.observation_id.value,
                    ),
                },
            ),
            "boundary_observation_ids": (),
        }
        reviewed_draft = EngineeringAgentAnswerDraft(
            answer_id=reviewed_answer_id,
            turn_id=capture.request.turn_id,
            work_state_digest=reviewed_work_state.digest,
            package_digest=reviewed_package_digest,
            response_kind=EngineeringAgentResponseKind.ANSWER,
            content="当前证据支持这一条登录结论。",
            claims=(reviewed_claim,),
            boundary_observation_ids=(),
            digest=digest_of(reviewed_draft_core),
        )
        evidence_required_invocation = replace(
            invocation,
            previous_work_state=reviewed_work_state,
            review_findings=(
                EngineeringAgentReviewFinding.create(
                    code="INCOMPLETE_EVIDENCE",
                    message="The current Package cannot support claim 0.",
                    requires_evidence=True,
                    claim_index=0,
                ),
            ),
            review_digest=digest_of("evidence-required-review"),
            reviewed_draft=reviewed_draft,
        )
        evidence_required_view = _primary_input_view(
            evidence_required_invocation
        )
        self.assertFalse(
            evidence_required_view["review_feedback"][
                "review_rewrite_contract"
            ]["active"]
        )
        with self.assertRaises(DomainError) as missing_reviewed_draft:
            _primary_input_view(
                replace(evidence_required_invocation, reviewed_draft=None)
            )
        self.assertEqual(
            missing_reviewed_draft.exception.code,
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
        )
        evidence_required_policy = evidence_required_view[
            "completion_policy"
        ]
        self.assertTrue(evidence_required_policy["tool_action_required"])
        self.assertFalse(evidence_required_policy["draft_required"])
        self.assertEqual(evidence_required_policy["allowed_response_kinds"], ())
        evidence_required_preflight = _output_preflight_view(
            role=EngineeringAgentModelRole.PRIMARY_AGENT,
            role_input_payload=evidence_required_view,
            output_schema_ref=ENGINEERING_AGENT_PRIMARY_OUTPUT_SCHEMA_REF,
        )
        self.assertEqual(
            evidence_required_preflight["primary_branch_contract"][
                "effective_required_branch"
            ],
            "ACTION",
        )
        self.assertEqual(
            evidence_required_preflight["draft_reference_contract"][
                "answer_claim_support_observation_ids_allowed_exact"
            ],
            (observation.observation_id.value,),
        )
        same_package_invocation = replace(
            evidence_required_invocation,
            review_findings=(
                EngineeringAgentReviewFinding.create(
                    code="DIRECTNESS",
                    message="直接回答后再解释。",
                    requires_evidence=False,
                    claim_index=0,
                ),
            ),
            review_digest=digest_of("same-package-review"),
        )
        same_package_view = _primary_input_view(same_package_invocation)
        same_package_feedback = same_package_view["review_feedback"]
        self.assertEqual(
            set(same_package_feedback["reviewed_draft"]),
            {
                "schema",
                "response_kind",
                "content",
                "claims",
                "boundary_observation_ids",
                "draft_digest",
            },
        )
        self.assertEqual(
            same_package_feedback["reviewed_draft"]["draft_digest"],
            reviewed_draft.digest.value,
        )
        self.assertEqual(
            same_package_feedback["reviewed_draft"]["claims"],
            (
                {
                    "claim_index": 0,
                    "statement": reviewed_claim.statement,
                    "support_observation_ids": (
                        observation.observation_id.value,
                    ),
                },
            ),
        )
        self.assertTrue(
            same_package_feedback["review_rewrite_contract"]["active"]
        )
        self.assertEqual(
            same_package_feedback["review_rewrite_contract"][
                "reviewed_response_kind"
            ],
            "ANSWER",
        )
        self.assertTrue(
            same_package_feedback["review_rewrite_contract"][
                "new_user_visible_material_assertions_forbidden"
            ]
        )
        self.assertTrue(
            same_package_feedback["review_rewrite_contract"][
                "global_completeness_claim_addition_requires_answer_response_kind"
            ]
        )
        self.assertTrue(
            same_package_feedback["review_rewrite_contract"][
                "limitation_claim_inventory_must_remain_empty"
            ]
        )
        with self.assertRaises(DomainError) as forged_reviewed_draft:
            _primary_input_view(
                replace(
                    same_package_invocation,
                    reviewed_draft=replace(
                        reviewed_draft,
                        digest=digest_of("forged reviewed draft"),
                    ),
                )
            )
        self.assertEqual(
            forged_reviewed_draft.exception.code,
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
        )
        same_package_preflight = _output_preflight_view(
            role=EngineeringAgentModelRole.PRIMARY_AGENT,
            role_input_payload=same_package_view,
            output_schema_ref=ENGINEERING_AGENT_PRIMARY_OUTPUT_SCHEMA_REF,
        )
        self.assertEqual(
            same_package_preflight["review_rewrite_contract"],
            same_package_feedback["review_rewrite_contract"],
        )
        evidence_required_draft = {
            "goal": "确认登录失败记录",
            "response_language": "zh-CN",
            "audience": "software engineer",
            "constraints": [],
            "resolved_referents": [],
            "accepted_correction_message_ids": [],
            "superseded_conclusion_refs": [],
            "hypotheses": [],
            "plan": [],
            "open_items": [],
            "phase": "RESPONSE_READY",
            "action": None,
            "draft": {
                "response_kind": "ANSWER",
                "content": "当前证据支持这一条登录结论。",
                "claims": [
                    {
                        "statement": "当前证据支持这一条登录结论。",
                        "support_observation_ids": [
                            observation.observation_id.value
                        ],
                    }
                ],
                "boundary_observation_ids": [],
            },
        }
        with self.assertRaises(DomainError) as review_redraft:
            decode_engineering_agent_primary_output(
                output_text=json.dumps(evidence_required_draft),
                invocation=evidence_required_invocation,
                model_call_ref="review-redraft-without-evidence-call",
            )
        self.assertEqual(
            review_redraft.exception.code,
            ErrorCode.STRUCTURED_OUTPUT_INVALID,
        )

        prior_observation_id = StableId(f"observation_{'2' * 32}")
        previous_work_state = SimpleNamespace(
            work_state_id=StableId(f"work_state_{'1' * 32}"),
            conversation_id=capture.request.snapshot_before.conversation.conversation_id,
            turn_id=StableId(f"turn_{'1' * 32}"),
            revision=Revision(1),
            previous_digest=None,
            context_digest=capture.request.snapshot_before.context.digest,
            goal="prior turn goal",
            response_language="zh-CN",
            audience="software engineer",
            constraints=(),
            resolved_referents=("登录流程",),
            accepted_correction_message_ids=(),
            superseded_conclusion_refs=(),
            hypotheses=(),
            plan=(),
            observation_ids=(prior_observation_id,),
            open_items=(),
            phase=SimpleNamespace(value="RESPONSE_READY"),
            review_input_digest=None,
            proposal_digest=digest_of("prior proposal"),
            digest=digest_of("prior work state"),
        )
        next_turn_view = _primary_input_view(
            replace(
                invocation,
                previous_work_state=previous_work_state,
                observations=(),
                action_history=(),
            )
        )
        self.assertNotIn(
            "observation_ids", next_turn_view["previous_work_state"]
        )
        self.assertEqual(
            next_turn_view["previous_work_state"][
                "prior_turn_observation_count"
            ],
            1,
        )
        self.assertFalse(
            next_turn_view["previous_work_state"][
                "prior_turn_observation_ids_disclosed"
            ]
        )
        self.assertEqual(
            next_turn_view["work_state_reference_policy"][
                "required_current_turn_observation_ids"
            ],
            (),
        )
        self.assertEqual(
            next_turn_view["completion_policy"]["allowed_response_kinds"],
            ("CLARIFICATION",),
        )
        self.assertTrue(
            next_turn_view["completion_policy"][
                "answer_requires_current_turn_support"
            ]
        )
        self.assertTrue(
            next_turn_view["completion_policy"][
                "prior_answer_restatement_requires_current_turn_evidence"
            ]
        )

    def test_fresh_investigation_requires_world_model_before_source(self) -> None:
        capture = CapturingTurnExecutor()
        service = InMemoryEngineeringConversationService(
            _binding(),
            turn_executor=capture,
            id_generator=SequenceIds(),
            clock=lambda: self.now,
        )
        conversation = service.create_conversation()
        service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=Revision(1),
            message="解释管理端登录调用链。",
        )
        invocation = EngineeringAgentInvocation(
            request=capture.request,
            previous_work_state=None,
            observations=(),
            review_findings=(),
            review_digest=None,
            available_operations=(
                EngineeringAgentToolOperation.WORLD_MODEL_QUERY,
                EngineeringAgentToolOperation.SOURCE_SEARCH,
            ),
        )
        rendered = _primary_input_view(invocation)
        self.assertTrue(
            rendered["investigation_policy"][
                "world_model_first_before_source_required"
            ]
        )
        self.assertEqual(
            tuple(item["operation"] for item in rendered["tool_catalog"]),
            ("WORLD_MODEL_QUERY", "SOURCE_SEARCH"),
        )
        payload = {
            "goal": "解释管理端登录调用链",
            "response_language": "zh-CN",
            "audience": "software engineer",
            "constraints": [],
            "resolved_referents": [],
            "accepted_correction_message_ids": [],
            "superseded_conclusion_refs": [],
            "hypotheses": [],
            "plan": [],
            "open_items": [],
            "phase": "INVESTIGATING",
            "action": {
                "operation": "SOURCE_SEARCH",
                "arguments": [
                    {"name": "evidence_class", "value": "SOURCE"},
                    {"name": "query", "value": "UmsAdminServiceImpl"},
                ],
                "evidence_need": "locate the login service implementation",
            },
            "draft": None,
        }
        with self.assertRaises(DomainError) as source_before_world_model:
            decode_engineering_agent_primary_output(
                output_text=json.dumps(payload),
                invocation=invocation,
                model_call_ref="source-before-world-model-call",
            )
        self.assertEqual(
            source_before_world_model.exception.code,
            ErrorCode.STRUCTURED_OUTPUT_INVALID,
        )

        payload["action"] = {
            "operation": "WORLD_MODEL_QUERY",
            "arguments": [],
            "evidence_need": "identify the login implementation target symbols",
        }
        proposal = decode_engineering_agent_primary_output(
            output_text=json.dumps(payload),
            invocation=invocation,
            model_call_ref="world-model-first-call",
        )
        self.assertEqual(
            proposal.action.operation,
            EngineeringAgentToolOperation.WORLD_MODEL_QUERY,
        )

    def test_first_source_search_copies_cognition_derived_declaring_type(
        self,
    ) -> None:
        capture = CapturingTurnExecutor()
        service = InMemoryEngineeringConversationService(
            _binding(),
            turn_executor=capture,
            id_generator=SequenceIds(),
            clock=lambda: self.now,
        )
        conversation = service.create_conversation()
        service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=Revision(1),
            message="解释凭据校验调用链。",
        )
        world_action = EngineeringAgentToolActionProposal.create(
            operation=EngineeringAgentToolOperation.WORLD_MODEL_QUERY,
            arguments=(),
            evidence_need="identify the credential verifier implementation target",
        )
        item_id = f"cognition_item_{'3' * 32}"
        item_digest = digest_of("credential-verifier-item").value
        world_support = EngineeringAgentToolObservation(
            observation_id=StableId(f"observation_{'1' * 32}"),
            tool_request_id=StableId(f"tool_request_{'2' * 32}"),
            operation=EngineeringAgentToolOperation.WORLD_MODEL_QUERY,
            result_ref="world-model-support",
            content=json.dumps(
                {
                    "schema": "ENGINEERING_AGENT_WORLD_MODEL_SUPPORT@4",
                    "source_search_target_projection": {
                        "schema": (
                            "ENGINEERING_AGENT_COGNITION_SOURCE_SEARCH_TARGETS@1"
                        ),
                        "kind": "JAVA_DECLARING_TYPE_LITERAL",
                        "options": [
                            {
                                "literal": "CredentialVerifier",
                                "resource_locators": [
                                    "src/main/java/example/CredentialVerifier.java"
                                ],
                                "source_revision": (
                                    capture.request.binding.repository_revision
                                ),
                                "cognition_item_ids": [item_id],
                                "cognition_item_digests": [item_digest],
                            }
                        ],
                        "truncated": False,
                        "grants_source_authority": False,
                    },
                }
            ),
            disposition=EngineeringAgentEvidenceDisposition.SUPPORT,
            progress=True,
            citation_refs=(item_id,),
            authority_receipt=None,
            tool_evidence_digest=digest_of("world-support-evidence"),
            digest=digest_of("world-support-observation"),
        )
        invocation = EngineeringAgentInvocation(
            request=capture.request,
            previous_work_state=None,
            observations=(world_support,),
            review_findings=(),
            review_digest=None,
            available_operations=(
                EngineeringAgentToolOperation.WORLD_MODEL_QUERY,
                EngineeringAgentToolOperation.SOURCE_SEARCH,
            ),
            action_history=(world_action,),
        )

        rendered = _primary_input_view(invocation)
        self.assertEqual(
            rendered["investigation_policy"]["schema"],
            "ENGINEERING_AGENT_INVESTIGATION_POLICY@2",
        )
        self.assertTrue(
            rendered["investigation_policy"]
            ["first_source_search_requires_cognition_target_copy"]
        )
        target_projection = rendered["tool_reference_policy"]
        target_projection = target_projection[
            "cognition_source_search_target_projection"
        ]
        self.assertEqual(
            tuple(item["literal"] for item in target_projection["options"]),
            ("CredentialVerifier",),
        )
        source_tool = next(
            item
            for item in rendered["tool_catalog"]
            if item["operation"] == "SOURCE_SEARCH"
        )
        self.assertEqual(
            source_tool["value_constraints"]["allowed_exact_values"],
            ("CredentialVerifier",),
        )

        payload = {
            "goal": "解释凭据校验调用链",
            "response_language": "zh-CN",
            "audience": "software engineer",
            "constraints": [],
            "resolved_referents": [],
            "accepted_correction_message_ids": [],
            "superseded_conclusion_refs": [],
            "hypotheses": [],
            "plan": [],
            "open_items": [],
            "phase": "INVESTIGATING",
            "action": {
                "operation": "SOURCE_SEARCH",
                "arguments": [
                    {"name": "evidence_class", "value": "SOURCE"},
                    {"name": "query", "value": "login"},
                ],
                "evidence_need": "locate the credential verifier implementation",
            },
            "draft": None,
        }
        with self.assertRaises(DomainError) as broad_member_word:
            decode_engineering_agent_primary_output(
                output_text=json.dumps(payload),
                invocation=invocation,
                model_call_ref="broad-source-target-call",
            )
        self.assertEqual(
            broad_member_word.exception.code,
            ErrorCode.STRUCTURED_OUTPUT_INVALID,
        )

        payload["action"]["arguments"][1]["value"] = "CredentialVerifier"
        proposal = decode_engineering_agent_primary_output(
            output_text=json.dumps(payload),
            invocation=invocation,
            model_call_ref="exact-source-target-call",
        )
        self.assertEqual(
            dict(proposal.action.arguments)["query"],
            "CredentialVerifier",
        )

        after_first_source = replace(
            invocation,
            action_history=(world_action, proposal.action),
        )
        later = _primary_input_view(after_first_source)
        self.assertFalse(
            later["investigation_policy"]
            ["first_source_search_requires_cognition_target_copy"]
        )
        later_source_tool = next(
            item
            for item in later["tool_catalog"]
            if item["operation"] == "SOURCE_SEARCH"
        )
        self.assertNotIn(
            "allowed_exact_values",
            later_source_tool["value_constraints"],
        )

    def test_world_model_boundary_requires_first_available_source_follow_up(self) -> None:
        capture = CapturingTurnExecutor()
        service = InMemoryEngineeringConversationService(
            _binding(),
            turn_executor=capture,
            id_generator=SequenceIds(),
            clock=lambda: self.now,
        )
        conversation = service.create_conversation()
        service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=Revision(1),
            message="确认当前源码中的失败副作用",
        )
        world_action = EngineeringAgentToolActionProposal.create(
            operation=EngineeringAgentToolOperation.WORLD_MODEL_QUERY,
            arguments=(),
            evidence_need="identify the failure-side-effect boundary",
        )
        world_boundary = EngineeringAgentToolObservation(
            observation_id=StableId(f"observation_{'1' * 32}"),
            tool_request_id=StableId(f"tool_request_{'2' * 32}"),
            operation=EngineeringAgentToolOperation.WORLD_MODEL_QUERY,
            result_ref="world-model-gap",
            content="The requested side effect is outside current cognition.",
            disposition=EngineeringAgentEvidenceDisposition.BOUNDARY,
            progress=False,
            citation_refs=(),
            authority_receipt=None,
            tool_evidence_digest=digest_of("world-boundary-evidence"),
            digest=digest_of("world-boundary-observation"),
        )
        invocation = EngineeringAgentInvocation(
            request=capture.request,
            previous_work_state=None,
            observations=(world_boundary,),
            review_findings=(),
            review_digest=None,
            available_operations=(
                EngineeringAgentToolOperation.WORLD_MODEL_QUERY,
                EngineeringAgentToolOperation.SOURCE_SEARCH,
                EngineeringAgentToolOperation.SOURCE_READ,
            ),
            action_history=(world_action,),
        )

        completion = _primary_input_view(invocation)["completion_policy"]
        self.assertTrue(
            completion["source_follow_up_required_before_limitation"]
        )
        self.assertEqual(completion["allowed_response_kinds"], ("CLARIFICATION",))

        limitation = {
            "goal": "确认当前源码中的失败副作用",
            "response_language": "zh-CN",
            "audience": "software engineer",
            "constraints": [],
            "resolved_referents": [],
            "accepted_correction_message_ids": [],
            "superseded_conclusion_refs": [],
            "hypotheses": [],
            "plan": [],
            "open_items": [],
            "phase": "RESPONSE_READY",
            "action": None,
            "draft": {
                "response_kind": "LIMITATION",
                "content": "当前 World Model 证据不足。",
                "claims": [],
                "boundary_observation_ids": [
                    world_boundary.observation_id.value
                ],
            },
        }
        with self.assertRaises(DomainError) as premature:
            decode_engineering_agent_primary_output(
                output_text=json.dumps(limitation),
                invocation=invocation,
                model_call_ref="premature-limitation",
            )
        self.assertEqual(
            premature.exception.code, ErrorCode.STRUCTURED_OUTPUT_INVALID
        )

        source_action = EngineeringAgentToolActionProposal.create(
            operation=EngineeringAgentToolOperation.SOURCE_SEARCH,
            arguments=(("evidence_class", "SOURCE"), ("query", "side effect")),
            evidence_need="locate exact source for the failure side effect",
        )
        source_boundary = replace(
            world_boundary,
            observation_id=StableId(f"observation_{'3' * 32}"),
            tool_request_id=StableId(f"tool_request_{'4' * 32}"),
            operation=EngineeringAgentToolOperation.SOURCE_SEARCH,
            result_ref="source-search-gap",
            content="The bounded Source search found no readable result.",
            tool_evidence_digest=digest_of("source-boundary-evidence"),
            digest=digest_of("source-boundary-observation"),
        )
        after_source_search = replace(
            invocation,
            observations=(world_boundary, source_boundary),
            action_history=(world_action, source_action),
        )
        completion = _primary_input_view(after_source_search)[
            "completion_policy"
        ]
        self.assertFalse(
            completion["source_follow_up_required_before_limitation"]
        )
        self.assertEqual(
            completion["allowed_response_kinds"],
            ("CLARIFICATION", "LIMITATION"),
        )
        empty_boundary_limitation = {
            **limitation,
            "draft": {
                **limitation["draft"],
                "boundary_observation_ids": [],
            },
        }
        with self.assertRaises(DomainError) as empty_boundary:
            decode_engineering_agent_primary_output(
                output_text=json.dumps(empty_boundary_limitation),
                invocation=after_source_search,
                model_call_ref="empty-boundary-limitation",
            )
        self.assertEqual(
            empty_boundary.exception.code,
            ErrorCode.STRUCTURED_OUTPUT_INVALID,
        )
        self.assertIn(
            "a limitation requires boundary evidence",
            str(empty_boundary.exception),
        )

        response_ready_action = {
            **limitation,
            "phase": "RESPONSE_READY",
            "action": {
                "operation": "WORLD_MODEL_QUERY",
                "arguments": [],
                "evidence_need": "identify one remaining implementation gap",
            },
            "draft": None,
        }
        with self.assertRaises(DomainError) as terminal_action_phase:
            decode_engineering_agent_primary_output(
                output_text=json.dumps(response_ready_action),
                invocation=after_source_search,
                model_call_ref="response-ready-action",
            )
        self.assertEqual(
            terminal_action_phase.exception.code,
            ErrorCode.STRUCTURED_OUTPUT_INVALID,
        )
        self.assertIn(
            "a tool action requires a non-terminal Work State phase",
            str(terminal_action_phase.exception),
        )

    def test_path_segment_source_rejection_requires_distinct_content_query(self) -> None:
        capture = CapturingTurnExecutor()
        service = InMemoryEngineeringConversationService(
            _binding(),
            turn_executor=capture,
            id_generator=SequenceIds(),
            clock=lambda: self.now,
        )
        conversation = service.create_conversation()
        service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=Revision(1),
            message="确认 mall-portal 的订单创建顺序",
        )
        world_action = EngineeringAgentToolActionProposal.create(
            operation=EngineeringAgentToolOperation.WORLD_MODEL_QUERY,
            arguments=(),
            evidence_need="identify the order creation boundary",
        )
        path_search = EngineeringAgentToolActionProposal.create(
            operation=EngineeringAgentToolOperation.SOURCE_SEARCH,
            arguments=(
                ("evidence_class", "SOURCE"),
                ("query", "mall-portal"),
            ),
            evidence_need="locate the order implementation",
        )
        world_boundary = EngineeringAgentToolObservation(
            observation_id=StableId(f"observation_{'1' * 32}"),
            tool_request_id=StableId(f"tool_request_{'2' * 32}"),
            operation=EngineeringAgentToolOperation.WORLD_MODEL_QUERY,
            result_ref="world-model-order-gap",
            content="The requested order behavior is outside current cognition.",
            disposition=EngineeringAgentEvidenceDisposition.BOUNDARY,
            progress=False,
            citation_refs=(),
            authority_receipt=None,
            tool_evidence_digest=digest_of("world-order-boundary-evidence"),
            digest=digest_of("world-order-boundary-observation"),
        )
        ledger_ref = "evidence_ledger_" + "3" * 32
        entry_details = (
            ("reason", "SOURCE_SEARCH_QUERY_EQUALS_PATH_SEGMENT"),
            ("status", "REJECTED"),
        )
        entry_core = {
            "ledger_id": ledger_ref,
            "sequence": 1,
            "kind": "BROKER_DECISION",
            "subject_id": "broker_decision_" + "4" * 32,
            "subject_digest": digest_of("path-query-rejection").value,
            "references": (),
            "details": entry_details,
            "previous_entry_digest": None,
        }
        source_entry_digest = digest_of(
            ["EVIDENCE_LEDGER_ENTRY@1", entry_core]
        )
        ledger_entry = EngineeringAgentLedgerEntryReceipt.create(
            sequence=1,
            kind="BROKER_DECISION",
            subject_ref=entry_core["subject_id"],
            subject_digest=digest_of("path-query-rejection"),
            references=(),
            details=entry_details,
            previous_entry_digest=None,
            source_entry_digest=source_entry_digest,
        )
        evidence_request_digest = digest_of("path-query-source-request")
        receipt = EngineeringAgentToolAuthorityReceipt.create(
            authority_kind=EngineeringAgentToolAuthorityKind.SOURCE,
            turn_request_digest=capture.request.request_digest,
            tool_request_digest=digest_of("path-query-tool-request"),
            evidence_request_digest=evidence_request_digest,
            repository_revision=capture.request.binding.repository_revision,
            evidence_digest=digest_of("path-query-source-evidence"),
            ledger_ref=ledger_ref,
            ledger_generation=1,
            ledger_parent_seal_digest=None,
            ledger_prefix_digest=digest_of(
                [
                    "EVIDENCE_LEDGER_PREFIX@1",
                    ledger_ref,
                    evidence_request_digest.value,
                    1,
                    None,
                    (source_entry_digest.value,),
                ]
            ),
            ledger_entries=(ledger_entry,),
        )
        source_boundary = EngineeringAgentToolObservation(
            observation_id=StableId(f"observation_{'5' * 32}"),
            tool_request_id=StableId(f"tool_request_{'6' * 32}"),
            operation=EngineeringAgentToolOperation.SOURCE_SEARCH,
            result_ref="path-query-rejected",
            content="The Source query equals an authorized directory segment.",
            disposition=EngineeringAgentEvidenceDisposition.BOUNDARY,
            progress=False,
            citation_refs=(),
            authority_receipt=receipt,
            tool_evidence_digest=digest_of("path-query-boundary-evidence"),
            digest=digest_of("path-query-boundary-observation"),
        )
        invocation = EngineeringAgentInvocation(
            request=capture.request,
            previous_work_state=None,
            observations=(world_boundary, source_boundary),
            review_findings=(),
            review_digest=None,
            available_operations=(
                EngineeringAgentToolOperation.WORLD_MODEL_QUERY,
                EngineeringAgentToolOperation.SOURCE_SEARCH,
                EngineeringAgentToolOperation.SOURCE_READ,
            ),
            action_history=(world_action, path_search),
        )

        rendered = _primary_input_view(invocation)
        self.assertEqual(
            rendered["tool_reference_policy"]["latest_source_broker_decision"],
            {
                "status": "REJECTED",
                "reason": "SOURCE_SEARCH_QUERY_EQUALS_PATH_SEGMENT",
            },
        )
        self.assertTrue(
            rendered["completion_policy"]
            ["source_follow_up_required_before_limitation"]
        )
        self.assertEqual(
            rendered["completion_policy"]["allowed_response_kinds"],
            ("CLARIFICATION",),
        )
        source_tool = next(
            item
            for item in rendered["tool_catalog"]
            if item["operation"] == "SOURCE_SEARCH"
        )
        self.assertEqual(
            source_tool["value_constraints"]["forbidden_exact_values"],
            ("mall-portal",),
        )

        limitation = {
            "goal": "确认 mall-portal 的订单创建顺序",
            "response_language": "zh-CN",
            "audience": "software engineer",
            "constraints": [],
            "resolved_referents": [],
            "accepted_correction_message_ids": [],
            "superseded_conclusion_refs": [],
            "hypotheses": [],
            "plan": [],
            "open_items": [],
            "phase": "RESPONSE_READY",
            "action": None,
            "draft": {
                "response_kind": "LIMITATION",
                "content": "当前 Source 证据不足。",
                "claims": [],
                "boundary_observation_ids": [
                    world_boundary.observation_id.value,
                    source_boundary.observation_id.value,
                ],
            },
        }
        with self.assertRaises(DomainError) as premature:
            decode_engineering_agent_primary_output(
                output_text=json.dumps(limitation),
                invocation=invocation,
                model_call_ref="path-query-premature-limitation",
            )
        self.assertEqual(
            premature.exception.code,
            ErrorCode.STRUCTURED_OUTPUT_INVALID,
        )

    def test_evidence_only_synthesis_is_a_response_only_model_contract(self) -> None:
        capture = CapturingTurnExecutor()
        service = InMemoryEngineeringConversationService(
            _binding(),
            turn_executor=capture,
            id_generator=SequenceIds(),
            clock=lambda: self.now,
        )
        conversation = service.create_conversation()
        service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=Revision(1),
            message="说明现有证据边界",
        )
        invocation = EngineeringAgentInvocation(
            request=capture.request,
            previous_work_state=None,
            observations=(),
            review_findings=(),
            review_digest=None,
            available_operations=(
                EngineeringAgentToolOperation.WORLD_MODEL_QUERY,
                EngineeringAgentToolOperation.SOURCE_SEARCH,
                EngineeringAgentToolOperation.SOURCE_READ,
            ),
            mode=EngineeringAgentInvocationMode.EVIDENCE_ONLY_SYNTHESIS,
        )

        rendered = _primary_input_view(invocation)
        self.assertEqual(rendered["tool_catalog"], ())
        self.assertEqual(
            rendered["completion_policy"],
            {
                "mode": "EVIDENCE_ONLY_SYNTHESIS",
                "tool_action_allowed": False,
                "tool_action_required": False,
                "draft_required": True,
                "allowed_response_kinds": (),
                "source_follow_up_required_before_limitation": False,
                "new_evidence_claim_forbidden": True,
                "answer_requires_current_turn_support": True,
                "limitation_requires_current_turn_boundary": True,
                "prior_answer_restatement_requires_current_turn_evidence": True,
            },
        )
        payload = {
            "goal": "说明现有证据边界",
            "response_language": "zh-CN",
            "audience": "software engineer",
            "constraints": [],
            "resolved_referents": [],
            "accepted_correction_message_ids": [],
            "superseded_conclusion_refs": [],
            "hypotheses": [],
            "plan": [],
            "open_items": [],
            "phase": "INVESTIGATING",
            "action": {
                "operation": "WORLD_MODEL_QUERY",
                "arguments": [{"name": "query", "value": "more evidence"}],
                "evidence_need": "continue investigating",
            },
            "draft": None,
        }
        with self.assertRaises(DomainError) as tool_action:
            decode_engineering_agent_primary_output(
                output_text=json.dumps(payload),
                invocation=invocation,
                model_call_ref="terminal-action-call",
            )
        self.assertEqual(
            tool_action.exception.code,
            ErrorCode.STRUCTURED_OUTPUT_INVALID,
        )

        payload["phase"] = "RESPONSE_READY"
        payload["action"] = None
        payload["draft"] = {
            "response_kind": "CLARIFICATION",
            "content": "你还希望我查哪一部分？",
            "claims": [],
            "boundary_observation_ids": [],
        }
        with self.assertRaises(DomainError) as clarification:
            decode_engineering_agent_primary_output(
                output_text=json.dumps(payload),
                invocation=invocation,
                model_call_ref="terminal-clarification-call",
            )
        self.assertEqual(
            clarification.exception.code,
            ErrorCode.STRUCTURED_OUTPUT_INVALID,
        )

    def test_world_model_action_uses_semantic_need_compiled_by_application(self) -> None:
        capture = CapturingTurnExecutor()
        service = InMemoryEngineeringConversationService(
            _binding(),
            turn_executor=capture,
            id_generator=SequenceIds(),
            clock=lambda: self.now,
        )
        conversation = service.create_conversation()
        service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=Revision(1),
            message="管理员登录从用户名和密码到 token 的流程是什么？",
        )
        invocation = EngineeringAgentInvocation(
            request=capture.request,
            previous_work_state=None,
            observations=(),
            review_findings=(),
            review_digest=None,
            available_operations=(
                EngineeringAgentToolOperation.WORLD_MODEL_QUERY,
            ),
        )
        rendered = _primary_input_view(invocation)
        world_model = rendered["tool_catalog"][0]
        self.assertEqual(world_model["operation"], "WORLD_MODEL_QUERY")
        self.assertEqual(
            world_model["action_template"],
            {
                "operation": "WORLD_MODEL_QUERY",
                "arguments": (),
                "evidence_need": "",
            },
        )
        self.assertIn("evidence_need", world_model["value_constraints"])

        payload = {
            "goal": "确认登录实现流程",
            "response_language": "zh-CN",
            "audience": "software engineer",
            "constraints": [],
            "resolved_referents": [],
            "accepted_correction_message_ids": [],
            "superseded_conclusion_refs": [],
            "hypotheses": [],
            "plan": [],
            "open_items": [],
            "phase": "INVESTIGATING",
            "action": {
                "operation": "WORLD_MODEL_QUERY",
                "arguments": [],
                "evidence_need": (
                    "Locate AdminService login credential verification and token generation"
                ),
            },
            "draft": None,
        }
        proposal = decode_engineering_agent_primary_output(
            output_text=json.dumps(payload),
            invocation=invocation,
            model_call_ref="semantic-world-model-call",
        )
        self.assertEqual(proposal.action.arguments, ())

        repeated = replace(invocation, action_history=(proposal.action,))
        with self.assertRaises(DomainError) as repeated_need:
            decode_engineering_agent_primary_output(
                output_text=json.dumps(payload),
                invocation=repeated,
                model_call_ref="repeated-semantic-world-model-call",
            )
        self.assertEqual(
            repeated_need.exception.code,
            ErrorCode.STRUCTURED_OUTPUT_INVALID,
        )

        payload["action"]["arguments"] = [
            {"name": "query", "value": "login"}
        ]
        with self.assertRaises(DomainError) as model_authored_query:
            decode_engineering_agent_primary_output(
                output_text=json.dumps(payload),
                invocation=invocation,
                model_call_ref="model-authored-world-model-query",
            )
        self.assertEqual(
            model_authored_query.exception.code,
            ErrorCode.STRUCTURED_OUTPUT_INVALID,
        )

    def test_terminal_source_fuse_denial_removes_source_operations(self) -> None:
        capture = CapturingTurnExecutor()
        service = InMemoryEngineeringConversationService(
            _binding(),
            turn_executor=capture,
            id_generator=SequenceIds(),
            clock=lambda: self.now,
        )
        conversation = service.create_conversation()
        service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=Revision(1),
            message="继续读取认证源码",
        )
        ledger_ref = "evidence_ledger_" + "2" * 32
        entry_details = (
            ("reason", "SOURCE_FILE_FUSE_EXHAUSTED"),
            ("status", "REJECTED"),
        )
        entry_core = {
            "ledger_id": ledger_ref,
            "sequence": 1,
            "kind": "BROKER_DECISION",
            "subject_id": "broker_decision_" + "1" * 32,
            "subject_digest": digest_of("broker-denial").value,
            "references": (),
            "details": entry_details,
            "previous_entry_digest": None,
        }
        source_entry_digest = digest_of(
            ["EVIDENCE_LEDGER_ENTRY@1", entry_core]
        )
        ledger_entry = EngineeringAgentLedgerEntryReceipt.create(
            sequence=1,
            kind="BROKER_DECISION",
            subject_ref=entry_core["subject_id"],
            subject_digest=digest_of("broker-denial"),
            references=(),
            details=entry_details,
            previous_entry_digest=None,
            source_entry_digest=source_entry_digest,
        )
        evidence_request_digest = digest_of("terminal-source-request")
        receipt = EngineeringAgentToolAuthorityReceipt.create(
            authority_kind=EngineeringAgentToolAuthorityKind.SOURCE,
            turn_request_digest=capture.request.request_digest,
            tool_request_digest=digest_of("terminal-source-tool-request"),
            evidence_request_digest=evidence_request_digest,
            repository_revision=capture.request.binding.repository_revision,
            evidence_digest=digest_of("terminal-source-evidence"),
            ledger_ref=ledger_ref,
            ledger_generation=1,
            ledger_parent_seal_digest=None,
            ledger_prefix_digest=digest_of(
                [
                    "EVIDENCE_LEDGER_PREFIX@1",
                    ledger_ref,
                    evidence_request_digest.value,
                    1,
                    None,
                    (source_entry_digest.value,),
                ]
            ),
            ledger_entries=(ledger_entry,),
        )
        observation = EngineeringAgentToolObservation(
            observation_id=StableId(f"observation_{'1' * 32}"),
            tool_request_id=StableId(f"tool_request_{'2' * 32}"),
            operation=EngineeringAgentToolOperation.SOURCE_SEARCH,
            result_ref="terminal-source-denial",
            content="Source file fuse is exhausted",
            disposition=EngineeringAgentEvidenceDisposition.BOUNDARY,
            progress=False,
            citation_refs=(),
            authority_receipt=receipt,
            tool_evidence_digest=digest_of("terminal-tool-evidence"),
            digest=digest_of("terminal-observation"),
        )
        invocation = EngineeringAgentInvocation(
            request=capture.request,
            previous_work_state=None,
            observations=(observation,),
            review_findings=(),
            review_digest=None,
            available_operations=(
                EngineeringAgentToolOperation.WORLD_MODEL_QUERY,
                EngineeringAgentToolOperation.SOURCE_SEARCH,
                EngineeringAgentToolOperation.SOURCE_READ,
            ),
        )

        rendered = _primary_input_view(invocation)
        self.assertEqual(
            rendered["tool_reference_policy"]["terminal_source_denial_reason"],
            "SOURCE_FILE_FUSE_EXHAUSTED",
        )
        self.assertIsNone(
            rendered["tool_reference_policy"]["source_file_budget"]
        )
        self.assertEqual(
            tuple(item["operation"] for item in rendered["tool_catalog"]),
            ("WORLD_MODEL_QUERY",),
        )
        self.assertEqual(
            rendered["completion_policy"]["allowed_response_kinds"],
            ("CLARIFICATION", "LIMITATION"),
        )

        unavailable_source_read = {
            "goal": "继续读取认证源码",
            "response_language": "zh-CN",
            "audience": "software engineer",
            "constraints": ["use only sealed evidence"],
            "resolved_referents": [],
            "accepted_correction_message_ids": [],
            "superseded_conclusion_refs": [],
            "hypotheses": ["需要继续调查"],
            "plan": ["读取另一个源码文件"],
            "open_items": ["认证实现"],
            "phase": "INVESTIGATING",
            "action": {
                "operation": "SOURCE_READ",
                "arguments": [
                    {
                        "name": "locator_reference",
                        "value": "source_locator_" + "3" * 32,
                    }
                ],
                "evidence_need": "read another authentication source file",
            },
            "draft": None,
        }
        repaired_world_model = {
            **unavailable_source_read,
            "plan": ["查询仍可用的世界模型认知"],
            "action": {
                "operation": "WORLD_MODEL_QUERY",
                "arguments": [],
                "evidence_need": "inspect remaining authentication semantics",
            },
        }
        adapter = SequencedLiveAgentAdapter(
            outputs=(
                json.dumps(unavailable_source_read, ensure_ascii=False),
                json.dumps(repaired_world_model, ensure_ascii=False),
            )
        )
        _, model, _, _, _, _ = self._service(adapter=adapter)

        result = model.propose(invocation)

        self.assertEqual(
            result.proposal.action.operation,
            EngineeringAgentToolOperation.WORLD_MODEL_QUERY,
        )
        self.assertEqual(len(result.prior_receipts), 1)
        repair_payload = json.loads(
            next(
                item.content
                for item in adapter.requests[1].messages
                if item.input_item_id == "sealed-role-input"
            )
        )
        repair_policy = repair_payload["format_repair_policy"]
        self.assertEqual(
            repair_policy["validation_failure_category"],
            "CLOSED_OUTPUT_CONTRACT",
        )
        self.assertEqual(
            repair_policy["validation_failure_message"],
            "$.action.operation must copy one operation from the current "
            "tool_catalog (allowed=[WORLD_MODEL_QUERY])",
        )
        self.assertEqual(
            tuple(item["operation"] for item in repair_payload["tool_catalog"]),
            ("WORLD_MODEL_QUERY",),
        )
        repair_preflight = json.loads(adapter.requests[1].messages[-1].content)
        self.assertEqual(
            repair_preflight["format_repair"]["validation_failure_category"],
            "CLOSED_OUTPUT_CONTRACT",
        )
        self.assertNotIn(
            "source_locator_",
            repair_preflight["format_repair"]["validation_failure_message"],
        )

    def test_review_decoder_requires_complete_consistent_claim_assessments(self) -> None:
        request = SimpleNamespace(
            draft=SimpleNamespace(claims=(object(), object()))
        )
        approved = decode_engineering_agent_review_output(
            output_text=json.dumps(
                {
                    "decision": "APPROVED",
                    "claim_assessments": [
                        {"claim_index": 0, "verdict": "SUPPORTED"},
                        {"claim_index": 1, "verdict": "SUPPORTED"},
                    ],
                    "evidence_boundary_assessments": [],
                    "boundary_relevance_assessments": [],
                    "findings": [],
                }
            ),
            request=request,
            model_call_ref="review-approved",
        )
        self.assertEqual(approved.decision.value, "APPROVED")

        contradictory = {
            "decision": "FINDINGS",
            "claim_assessments": [
                {"claim_index": 0, "verdict": "SUPPORTED"},
                {"claim_index": 1, "verdict": "SUPPORTED"},
            ],
            "evidence_boundary_assessments": [],
            "boundary_relevance_assessments": [],
            "findings": [
                {
                    "code": "UNSUPPORTED_CLAIM",
                    "message": "The cited evidence fully supports this claim.",
                    "requires_evidence": False,
                    "claim_index": 0,
                }
            ],
        }
        with self.assertRaises(DomainError) as mismatch:
            decode_engineering_agent_review_output(
                output_text=json.dumps(contradictory),
                request=request,
                model_call_ref="review-contradictory",
            )
        self.assertEqual(mismatch.exception.code, ErrorCode.STRUCTURED_OUTPUT_INVALID)

        contradictory["claim_assessments"][0]["verdict"] = "DEFECT"
        finding = decode_engineering_agent_review_output(
            output_text=json.dumps(contradictory),
            request=request,
            model_call_ref="review-finding",
        )
        self.assertEqual(finding.decision.value, "FINDINGS")

        global_completeness_finding = decode_engineering_agent_review_output(
            output_text=json.dumps(
                {
                    "decision": "FINDINGS",
                    "claim_assessments": [
                        {"claim_index": 0, "verdict": "SUPPORTED"},
                        {"claim_index": 1, "verdict": "SUPPORTED"},
                    ],
                    "evidence_boundary_assessments": [],
                    "boundary_relevance_assessments": [],
                    "findings": [
                        {
                            "code": "UNENUMERATED_MATERIAL_CONCLUSION",
                            "message": (
                                "Draft content asserts one material relation "
                                "that is absent from the claim inventory."
                            ),
                            "requires_evidence": True,
                            "claim_index": None,
                        }
                    ],
                }
            ),
            request=request,
            model_call_ref="review-global-completeness-finding",
        )
        self.assertEqual(
            global_completeness_finding.findings[0].claim_index,
            None,
        )

        defect_without_finding = {
            "decision": "APPROVED",
            "claim_assessments": contradictory["claim_assessments"],
            "findings": [],
        }
        with self.assertRaises(DomainError) as missing_finding:
            decode_engineering_agent_review_output(
                output_text=json.dumps(defect_without_finding),
                request=request,
                model_call_ref="review-missing-finding",
            )
        self.assertEqual(
            missing_finding.exception.code,
            ErrorCode.STRUCTURED_OUTPUT_INVALID,
        )

        contradictory["claim_assessments"] = [
            {"claim_index": 0, "verdict": "DEFECT"}
        ]
        with self.assertRaises(DomainError) as incomplete:
            decode_engineering_agent_review_output(
                output_text=json.dumps(contradictory),
                request=request,
                model_call_ref="review-incomplete",
            )
        self.assertEqual(incomplete.exception.code, ErrorCode.STRUCTURED_OUTPUT_INVALID)

        contradictory["claim_assessments"] = [
            {"claim_index": 0, "verdict": "DEFECT"},
            {"claim_index": 2, "verdict": "SUPPORTED"},
        ]
        with self.assertRaises(DomainError) as unknown:
            decode_engineering_agent_review_output(
                output_text=json.dumps(contradictory),
                request=request,
                model_call_ref="review-unknown-claim",
            )
        self.assertEqual(unknown.exception.code, ErrorCode.STRUCTURED_OUTPUT_INVALID)

        approved_with_extra = {
            "decision": "APPROVED",
            "claim_assessments": [
                {"claim_index": 0, "verdict": "SUPPORTED"},
                {"claim_index": 1, "verdict": "SUPPORTED"},
            ],
            "evidence_boundary_assessments": [],
            "boundary_relevance_assessments": [],
            "findings": [],
            "rationale": "not in the closed schema",
        }
        with self.assertRaises(DomainError) as extra:
            decode_engineering_agent_review_output(
                output_text=json.dumps(approved_with_extra),
                request=request,
                model_call_ref="review-extra-field",
            )
        self.assertEqual(extra.exception.code, ErrorCode.STRUCTURED_OUTPUT_INVALID)

    def test_structural_caller_challenge_requires_exact_focused_assessment(self) -> None:
        turn_id = StableId(f"turn_{'1' * 32}")
        observation_id = StableId(f"observation_{'2' * 32}")
        source_observation = EngineeringAgentToolObservation(
            observation_id=observation_id,
            tool_request_id=StableId(f"tool_request_{'3' * 32}"),
            operation=EngineeringAgentToolOperation.SOURCE_READ,
            result_ref="source-read-support",
            content=json.dumps(
                {
                    "schema": "ENGINEERING_AGENT_SOURCE_SUPPORT@1",
                    "retrieval_result": {
                        "items": [
                            {
                                "locator": "module/src/main/java/example/ProductService.java",
                                "modality": "EXACT_STATIC_SOURCE_TEXT",
                                "coverage_complete": True,
                                "content": (
                                    "package example;\n"
                                    "class ProductService {\n"
                                    "  private ProductRepository productRepository;\n"
                                    "  void importAll() { productRepository.saveAll(items); }\n"
                                    "}\n"
                                ),
                            }
                        ]
                    },
                }
            ),
            disposition=EngineeringAgentEvidenceDisposition.SUPPORT,
            progress=True,
            citation_refs=(f"source_locator_{'4' * 32}",),
            authority_receipt=None,
            tool_evidence_digest=digest_of("source-evidence"),
            digest=digest_of("source-observation"),
        )
        package_digest = digest_of("challenge-package")
        package = EngineeringAgentEvidencePackage(
            package_id=StableId(f"evidence_package_{'5' * 32}"),
            turn_id=turn_id,
            origin_work_state_digest=digest_of("origin-work-state"),
            support_observations=(source_observation,),
            boundary_observations=(),
            digest=package_digest,
        )
        claim = EngineeringAgentClaimProposal.create(
            statement=(
                "productRepository.saveAll(items) 将所有商品写入 Elasticsearch。"
            ),
            support_observation_ids=(observation_id,),
        )
        draft = EngineeringAgentAnswerDraft(
            answer_id=StableId(f"agent_answer_{'6' * 32}"),
            turn_id=turn_id,
            work_state_digest=digest_of("current-work-state"),
            package_digest=package_digest,
            response_kind=EngineeringAgentResponseKind.ANSWER,
            content=claim.statement,
            claims=(claim,),
            boundary_observation_ids=(),
            digest=digest_of("challenge-draft"),
        )
        challenges = project_engineering_agent_evidence_boundary_challenges(
            package,
            draft,
        )
        self.assertEqual(len(challenges), 1)
        challenge = challenges[0]
        self.assertEqual(challenge.call_expression, "productRepository.saveAll")
        self.assertEqual(challenge.receiver_declared_type, "ProductRepository")
        self.assertEqual(challenge.package_implementation_observation_ids, ())
        request = SimpleNamespace(
            draft=draft,
            package=package,
            focus=EngineeringAgentReviewFocus.EVIDENCE_BOUNDARY_CHALLENGE,
        )
        missing_assessment = {
            "decision": "APPROVED",
            "claim_assessments": [
                {"claim_index": 0, "verdict": "SUPPORTED"}
            ],
            "evidence_boundary_assessments": [],
            "boundary_relevance_assessments": [],
            "findings": [],
        }
        with self.assertRaises(DomainError) as missing:
            decode_engineering_agent_review_output(
                output_text=json.dumps(missing_assessment),
                request=request,
                model_call_ref="focused-review-missing-assessment",
            )
        self.assertEqual(missing.exception.code, ErrorCode.STRUCTURED_OUTPUT_INVALID)
        exceeded = {
            "decision": "FINDINGS",
            "claim_assessments": [
                {"claim_index": 0, "verdict": "DEFECT"}
            ],
            "evidence_boundary_assessments": [
                {
                    "challenge_id": challenge.challenge_id.value,
                    "evidence_boundary": (
                        "The source proves only that ProductService invokes "
                        "productRepository.saveAll in local order."
                    ),
                    "draft_scope": (
                        "The Claim attributes a completed Elasticsearch write."
                    ),
                    "draft_semantic_scopes": [
                        "CALLER_INVOCATION",
                        "DATABASE_OR_EXTERNAL_STATE_EFFECT",
                    ],
                    "disposition": (
                        EngineeringAgentEvidenceBoundaryAssessmentDisposition.CLAIM_EXCEEDS_CALLER_EVIDENCE.value
                    ),
                    "finding_code": "UNMOUNTED_CALLEE_EFFECT",
                }
            ],
            "boundary_relevance_assessments": [],
            "findings": [
                {
                    "code": "UNMOUNTED_CALLEE_EFFECT",
                    "message": "Narrow the Claim to the visible invocation.",
                    "requires_evidence": False,
                    "claim_index": 0,
                }
            ],
        }
        proposal = decode_engineering_agent_review_output(
            output_text=json.dumps(exceeded),
            request=request,
            model_call_ref="focused-review-finding",
        )
        self.assertEqual(proposal.decision.value, "FINDINGS")
        self.assertEqual(
            proposal.evidence_boundary_assessments[0].challenge_id,
            challenge.challenge_id,
        )
        forged_within = {
            "decision": "APPROVED",
            "claim_assessments": [
                {"claim_index": 0, "verdict": "SUPPORTED"}
            ],
            "evidence_boundary_assessments": [
                {
                    "challenge_id": challenge.challenge_id.value,
                    "evidence_boundary": (
                        "The source proves only the caller invocation."
                    ),
                    "draft_scope": (
                        "The Claim attributes a completed Elasticsearch write."
                    ),
                    "draft_semantic_scopes": [
                        "DATABASE_OR_EXTERNAL_STATE_EFFECT"
                    ],
                    "disposition": "WITHIN_CALLER_EVIDENCE",
                    "finding_code": None,
                }
            ],
            "boundary_relevance_assessments": [],
            "findings": [],
        }
        with self.assertRaises(DomainError) as inconsistent_scope:
            decode_engineering_agent_review_output(
                output_text=json.dumps(forged_within),
                request=request,
                model_call_ref="focused-review-inconsistent-scope",
            )
        self.assertEqual(
            inconsistent_scope.exception.code,
            ErrorCode.STRUCTURED_OUTPUT_INVALID,
        )

    def test_downstream_full_read_projects_search_boundary_relevance_challenge(self) -> None:
        locator_ref = f"source_locator_{'7' * 32}"
        full_read_locator_ref = f"source_locator_{'6' * 32}"
        resource_locator = "module/src/main/java/example/LoginService.java"
        search_request_id = StableId(f"tool_request_{'8' * 32}")
        search_support = EngineeringAgentToolObservation(
            observation_id=StableId(f"observation_{'9' * 32}"),
            tool_request_id=search_request_id,
            operation=EngineeringAgentToolOperation.SOURCE_SEARCH,
            result_ref="search-result-support",
            content=json.dumps(
                {
                    "retrieval_result": {
                        "items": [
                            {
                                "locator_reference": locator_ref,
                                "locator": f"{resource_locator}:L45-52",
                                "modality": "LITERAL_TEXT_SEARCH_HIT",
                                "coverage_complete": False,
                            }
                        ]
                    }
                }
            ),
            disposition=EngineeringAgentEvidenceDisposition.SUPPORT,
            progress=True,
            citation_refs=(locator_ref,),
            authority_receipt=None,
            tool_evidence_digest=digest_of("search-support-evidence"),
            digest=digest_of("search-support-observation"),
        )
        search_boundary = EngineeringAgentToolObservation(
            observation_id=StableId(f"observation_{'a' * 32}"),
            tool_request_id=search_request_id,
            operation=EngineeringAgentToolOperation.SOURCE_SEARCH,
            result_ref="search-result-boundary",
            content="partial acquisition diagnostic",
            disposition=EngineeringAgentEvidenceDisposition.BOUNDARY,
            progress=False,
            citation_refs=(),
            authority_receipt=None,
            tool_evidence_digest=digest_of("search-boundary-evidence"),
            digest=digest_of("search-boundary-observation"),
        )
        read_support = EngineeringAgentToolObservation(
            observation_id=StableId(f"observation_{'b' * 32}"),
            tool_request_id=StableId(f"tool_request_{'c' * 32}"),
            operation=EngineeringAgentToolOperation.SOURCE_READ,
            result_ref="read-result-support",
            content=json.dumps(
                {
                    "retrieval_result": {
                        "items": [
                            {
                                "locator_reference": full_read_locator_ref,
                                "locator": resource_locator,
                                "modality": "EXACT_STATIC_SOURCE_TEXT",
                                "coverage_complete": True,
                            }
                        ]
                    }
                }
            ),
            disposition=EngineeringAgentEvidenceDisposition.SUPPORT,
            progress=True,
            citation_refs=(full_read_locator_ref,),
            authority_receipt=None,
            tool_evidence_digest=digest_of("read-support-evidence"),
            digest=digest_of("read-support-observation"),
        )
        projection = project_engineering_agent_draft_boundaries(
            (search_support, search_boundary, read_support)
        )
        self.assertEqual(
            projection.reportable_boundary_observation_ids,
            (search_boundary.observation_id,),
        )
        self.assertEqual(
            projection.resolved_acquisition_candidate_observation_ids,
            (search_boundary.observation_id,),
        )
        wrong_search_modality = replace(
            search_support,
            content=search_support.content.replace(
                "LITERAL_TEXT_SEARCH_HIT",
                "EXACT_STATIC_SOURCE_TEXT",
            ),
            digest=digest_of("wrong-search-modality"),
        )
        self.assertEqual(
            project_engineering_agent_draft_boundaries(
                (wrong_search_modality, search_boundary, read_support)
            ).resolved_acquisition_candidate_observation_ids,
            (),
        )
        prior_read_projection = project_engineering_agent_draft_boundaries(
            (read_support, search_support, search_boundary)
        )
        self.assertEqual(
            prior_read_projection.resolved_acquisition_candidate_observation_ids,
            (),
        )
        package_digest = digest_of("boundary-relevance-package")
        turn_id = StableId(f"turn_{'d' * 32}")
        package = EngineeringAgentEvidencePackage(
            package_id=StableId(f"evidence_package_{'e' * 32}"),
            turn_id=turn_id,
            origin_work_state_digest=digest_of("boundary-relevance-work"),
            support_observations=(search_support, read_support),
            boundary_observations=(search_boundary,),
            digest=package_digest,
        )
        draft = EngineeringAgentAnswerDraft(
            answer_id=StableId(f"agent_answer_{'f' * 32}"),
            turn_id=turn_id,
            work_state_digest=digest_of("boundary-relevance-work"),
            package_digest=package_digest,
            response_kind=EngineeringAgentResponseKind.LIMITATION,
            content="搜索阶段只返回了部分候选。",
            claims=(),
            boundary_observation_ids=(search_boundary.observation_id,),
            digest=digest_of("boundary-relevance-draft"),
        )
        challenges = project_engineering_agent_boundary_relevance_challenges(
            package,
            draft,
        )
        self.assertEqual(len(challenges), 1)
        self.assertEqual(
            challenges[0].kind.value,
            "RESOLVED_ACQUISITION",
        )
        self.assertEqual(
            challenges[0].resolving_support_observation_ids,
            (read_support.observation_id,),
        )
        self.assertTrue(challenges[0].draft_declared_boundary_reference)
        self.assertEqual(
            _boundary_relevance_allowed_dispositions(challenges[0]),
            ("MATERIAL_TO_USER_REQUEST", "RESOLVED_AUDIT_ONLY"),
        )

        focused_request = SimpleNamespace(
            draft=draft,
            package=package,
            focus=EngineeringAgentReviewFocus.EVIDENCE_BOUNDARY_CHALLENGE,
        )
        audit_only = decode_engineering_agent_review_output(
            output_text=json.dumps(
                {
                    "decision": "FINDINGS",
                    "claim_assessments": [],
                    "evidence_boundary_assessments": [],
                    "boundary_relevance_assessments": [
                        {
                            "challenge_id": challenges[0].challenge_id.value,
                            "user_requirement": "Explain the resolved source path.",
                            "boundary_scope": "Partial acquisition diagnostic.",
                            "disposition": (
                                EngineeringAgentBoundaryRelevanceAssessmentDisposition
                                .RESOLVED_AUDIT_ONLY.value
                            ),
                            "finding_code": "RESOLVED_DIAGNOSTIC_LEAK",
                        }
                    ],
                    "findings": [
                        {
                            "code": "RESOLVED_DIAGNOSTIC_LEAK",
                            "message": "Remove the resolved acquisition diagnostic.",
                            "requires_evidence": False,
                            "claim_index": None,
                        }
                    ],
                }
            ),
            request=focused_request,
            model_call_ref="focused-boundary-relevance-finding",
        )
        self.assertEqual(audit_only.decision.value, "FINDINGS")

        material = decode_engineering_agent_review_output(
            output_text=json.dumps(
                {
                    "decision": "APPROVED",
                    "claim_assessments": [],
                    "evidence_boundary_assessments": [],
                    "boundary_relevance_assessments": [
                        {
                            "challenge_id": challenges[0].challenge_id.value,
                            "user_requirement": "Explain the search diagnostic itself.",
                            "boundary_scope": "Partial acquisition diagnostic.",
                            "disposition": (
                                EngineeringAgentBoundaryRelevanceAssessmentDisposition
                                .MATERIAL_TO_USER_REQUEST.value
                            ),
                            "finding_code": None,
                        }
                    ],
                    "findings": [],
                }
            ),
            request=focused_request,
            model_call_ref="focused-boundary-relevance-approved",
        )
        self.assertEqual(material.decision.value, "APPROVED")

        unbound_draft = EngineeringAgentAnswerDraft(
            answer_id=StableId(f"agent_answer_{'1' * 32}"),
            turn_id=turn_id,
            work_state_digest=digest_of("boundary-relevance-work"),
            package_digest=package_digest,
            response_kind=EngineeringAgentResponseKind.ANSWER,
            content="搜索阶段只返回了部分候选。",
            claims=(),
            boundary_observation_ids=(),
            digest=digest_of("unbound-boundary-relevance-draft"),
        )
        unbound_challenges = (
            project_engineering_agent_boundary_relevance_challenges(
                package,
                unbound_draft,
            )
        )
        self.assertEqual(len(unbound_challenges), 1)
        self.assertFalse(
            unbound_challenges[0].draft_declared_boundary_reference
        )
        unbound_request = SimpleNamespace(
            draft=unbound_draft,
            package=package,
            focus=EngineeringAgentReviewFocus.EVIDENCE_BOUNDARY_CHALLENGE,
        )
        with self.assertRaises(DomainError) as unbound_material:
            decode_engineering_agent_review_output(
                output_text=json.dumps(
                    {
                        "decision": "APPROVED",
                        "claim_assessments": [],
                        "evidence_boundary_assessments": [],
                        "boundary_relevance_assessments": [
                            {
                                "challenge_id": (
                                    unbound_challenges[0].challenge_id.value
                                ),
                                "user_requirement": "Explain the diagnostic.",
                                "boundary_scope": "Partial diagnostic.",
                                "disposition": "MATERIAL_TO_USER_REQUEST",
                                "finding_code": None,
                            }
                        ],
                        "findings": [],
                    }
                ),
                request=unbound_request,
                model_call_ref="unbound-material-diagnostic",
            )
        self.assertEqual(
            unbound_material.exception.code,
            ErrorCode.STRUCTURED_OUTPUT_INVALID,
        )
        self.assertIn(
            "allowed_exact=[NOT_DISCLOSED_IN_DRAFT,RESOLVED_AUDIT_ONLY]",
            str(unbound_material.exception),
        )
        not_disclosed = decode_engineering_agent_review_output(
            output_text=json.dumps(
                {
                    "decision": "APPROVED",
                    "claim_assessments": [],
                    "evidence_boundary_assessments": [],
                    "boundary_relevance_assessments": [
                        {
                            "challenge_id": (
                                unbound_challenges[0].challenge_id.value
                            ),
                            "user_requirement": "Explain the business flow.",
                            "boundary_scope": "Not present in the Draft.",
                            "disposition": "NOT_DISCLOSED_IN_DRAFT",
                            "finding_code": None,
                        }
                    ],
                    "findings": [],
                }
            ),
            request=unbound_request,
            model_call_ref="undisclosed-diagnostic-approved",
        )
        self.assertEqual(not_disclosed.decision.value, "APPROVED")

        materiality_boundary = EngineeringAgentToolObservation(
            observation_id=StableId(f"observation_{'2' * 32}"),
            tool_request_id=StableId(f"tool_request_{'3' * 32}"),
            operation=EngineeringAgentToolOperation.WORLD_MODEL_QUERY,
            result_ref="world-model-boundary",
            content="global inventory metrics and a material state gap",
            disposition=EngineeringAgentEvidenceDisposition.BOUNDARY,
            progress=False,
            citation_refs=(),
            authority_receipt=None,
            tool_evidence_digest=digest_of("world-model-boundary-evidence"),
            digest=digest_of("world-model-boundary-observation"),
        )
        materiality_package_digest = digest_of("materiality-package")
        materiality_package = EngineeringAgentEvidencePackage(
            package_id=StableId(f"evidence_package_{'4' * 32}"),
            turn_id=turn_id,
            origin_work_state_digest=digest_of("materiality-work"),
            support_observations=(),
            boundary_observations=(materiality_boundary,),
            digest=materiality_package_digest,
        )
        materiality_draft = EngineeringAgentAnswerDraft(
            answer_id=StableId(f"agent_answer_{'5' * 32}"),
            turn_id=turn_id,
            work_state_digest=digest_of("materiality-work"),
            package_digest=materiality_package_digest,
            response_kind=EngineeringAgentResponseKind.LIMITATION,
            content="状态缺口仍限制结论，并附带了无关全局清单数字。",
            claims=(),
            boundary_observation_ids=(materiality_boundary.observation_id,),
            digest=digest_of("materiality-draft"),
        )
        materiality_challenges = (
            project_engineering_agent_boundary_relevance_challenges(
                materiality_package,
                materiality_draft,
            )
        )
        self.assertEqual(len(materiality_challenges), 1)
        self.assertEqual(
            materiality_challenges[0].kind.value,
            "BOUNDARY_MATERIALITY",
        )
        self.assertEqual(
            _boundary_relevance_allowed_dispositions(
                materiality_challenges[0]
            ),
            ("MATERIAL_TO_USER_REQUEST", "NON_MATERIAL_AUDIT_ONLY"),
        )
        materiality_finding = decode_engineering_agent_review_output(
            output_text=json.dumps(
                {
                    "decision": "FINDINGS",
                    "claim_assessments": [],
                    "evidence_boundary_assessments": [],
                    "boundary_relevance_assessments": [
                        {
                            "challenge_id": (
                                materiality_challenges[0].challenge_id.value
                            ),
                            "user_requirement": "Explain the material state gap.",
                            "boundary_scope": "Includes unrelated global metrics.",
                            "disposition": "NON_MATERIAL_AUDIT_ONLY",
                            "finding_code": "REMOVE_NON_MATERIAL_METRICS",
                        }
                    ],
                    "findings": [
                        {
                            "code": "REMOVE_NON_MATERIAL_METRICS",
                            "message": "Keep the material gap but remove unrelated metrics.",
                            "requires_evidence": False,
                            "claim_index": None,
                        }
                    ],
                }
            ),
            request=SimpleNamespace(
                draft=materiality_draft,
                package=materiality_package,
                focus=EngineeringAgentReviewFocus.EVIDENCE_BOUNDARY_CHALLENGE,
            ),
            model_call_ref="focused-boundary-materiality-finding",
        )
        self.assertEqual(materiality_finding.decision.value, "FINDINGS")

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
        primary_view = _primary_input_view(
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
        )
        policy_view = primary_view["draft_reference_policy"]
        current_evidence = primary_view["current_turn_evidence"]
        self.assertTrue(
            policy_view[
                "container_context_is_part_of_contained_assertion"
            ]
        )
        self.assertEqual(
            policy_view[
                "claim_statement_required_inherited_material_qualifiers"
            ],
            ("category", "scope", "condition", "certainty", "negation"),
        )
        self.assertEqual(
            tuple(
                item["observation_id"]
                for item in current_evidence["support_observations"]
            ),
            (support_observation.observation_id.value,),
        )
        self.assertEqual(
            tuple(
                item["observation_id"]
                for item in current_evidence["boundary_observations"]
            ),
            (boundary_observation.observation_id.value,),
        )
        reference_preflight = _output_preflight_view(
            role=EngineeringAgentModelRole.PRIMARY_AGENT,
            role_input_payload=primary_view,
            output_schema_ref=ENGINEERING_AGENT_PRIMARY_OUTPUT_SCHEMA_REF,
        )["draft_reference_contract"]
        self.assertEqual(
            reference_preflight[
                "answer_claim_support_observation_ids_allowed_exact"
            ],
            (support_observation.observation_id.value,),
        )
        self.assertEqual(
            reference_preflight[
                "draft_boundary_observation_ids_allowed_exact"
            ],
            (boundary_observation.observation_id.value,),
        )
        self.assertTrue(
            reference_preflight[
                "boundary_ids_in_answer_claim_support_forbidden"
            ]
        )
        self.assertEqual(
            policy_view,
            {
                "answer_claim_support_observation_ids": (
                    support_observation.observation_id.value,
                ),
                "limitation_boundary_observation_ids": (
                    boundary_observation.observation_id.value,
                ),
                "resolved_acquisition_candidate_observation_ids": (),
                "boundary_projection_digest": digest_of(
                    {
                        "schema": "ENGINEERING_AGENT_DRAFT_BOUNDARY_PROJECTION@1",
                        "reportable_boundary_observation_ids": (
                            boundary_observation.observation_id.value,
                        ),
                        "resolved_acquisition_candidate_observation_ids": (),
                    }
                ).value,
                "cross_disposition_references_forbidden": True,
                "unknown_observation_references_forbidden": True,
                "answer_claims_are_affirmative_support_only": True,
                "answer_boundary_reporting_fields": (
                    "draft.content",
                    "draft.boundary_observation_ids",
                ),
                "boundary_statements_forbidden_in_claims": True,
                "limitation_requires_at_least_one_boundary_reference": True,
                "structured_boundary_reference_is_evidence_binding_not_full_text_disclosure": True,
                "boundary_metadata_absent_from_draft_content_is_not_disclosed": True,
                "bound_boundary_id_need_not_be_named_or_raw_disclosed": True,
                "container_context_is_part_of_contained_assertion": True,
                "claim_statement_required_inherited_material_qualifiers": (
                    "category",
                    "scope",
                    "condition",
                    "certainty",
                    "negation",
                ),
                "claim_coverage_is_semantic_not_one_entry_per_phrase": True,
                "grouped_claim_may_cover_multiple_assertions_when_all_material_qualifiers_present": True,
                "redundant_claim_for_semantically_covered_assertion_forbidden": True,
                "trusted_repository_revision_attribution": _binding().repository_revision,
                "matching_repository_revision_attribution_is_not_standalone_claim": True,
                "mismatched_or_invented_revision_attribution_is_defect": True,
                "pure_unresolved_boundary_statement_is_not_affirmative_claim": True,
                "limitation_affirmative_diagnostic_requires_support_or_omission": True,
                "limitation_claims_must_be_empty": True,
                "evidence_gap_is_not_authority_denial": True,
                "authorization_limitation_requires_exact_boundary": True,
                "producer_invocation_is_not_consumer_visible_effect": True,
                "consumer_visible_effect_requires_consumer_path_support": True,
                "audit_retention_requires_answer_disclosure": False,
                (
                    "answer_boundary_requires_unresolved_material_requirement_"
                    "or_explicit_diagnostic_request"
                ): True,
                "resolved_acquisition_candidate_requires_relevance_review": True,
                "resolved_acquisition_candidate_is_automatic_exclusion": False,
                "global_inventory_metrics_require_material_user_relevance": True,
                "answer_detail_requires_material_user_relevance": True,
                "counterfactual_omission_preserving_requested_conclusions_means_omit": True,
                "self_introduced_adjacent_detail_allows_evidence_expansion": False,
                "generation_or_tool_provenance_requires_direct_support": True,
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
            output_text=(
                '{"decision":"APPROVED","claim_assessments":[],"evidence_boundary_assessments":[],"boundary_relevance_assessments":[],"findings":[]}'
            ),
            request=SimpleNamespace(draft=SimpleNamespace(claims=())),
            model_call_ref="trusted-review-call",
        )

        self.assertEqual(proposal.model_call_ref, "trusted-gateway-call")
        self.assertEqual(review.model_call_ref, "trusted-review-call")
        payload["observation_ids"] = []
        with self.assertRaises(DomainError) as provider_owned_observation_ids:
            decode_engineering_agent_primary_output(
                output_text=json.dumps(payload, ensure_ascii=False),
                invocation=invocation,
                model_call_ref="trusted-gateway-call",
            )
        self.assertEqual(
            provider_owned_observation_ids.exception.code,
            ErrorCode.STRUCTURED_OUTPUT_INVALID,
        )
        payload.pop("observation_ids")
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
