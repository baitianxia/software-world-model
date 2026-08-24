from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import unittest

from software_world_model.ai_infrastructure.engineering_question_model_source import (
    ENGINEERING_QUESTION_DISCLOSURE_POLICY_REF,
    ENGINEERING_QUESTION_MODEL_PROMPT_REF,
    EngineeringQuestionModelConfiguration,
    EngineeringQuestionModelEgressPolicy,
    EngineeringQuestionRunDisclosureAuthorization,
    EngineeringQuestionSessionAuthority,
    EngineeringQuestionSessionRunDisclosureAuthorization,
    EngineeringQuestionSubmissionReceipt,
    ModelBackedEngineeringQuestionStructuredOutputSource,
    PolicyEnforcingEngineeringQuestionModelGateway,
    SealedEngineeringQuestionRoleDisclosureAuthorizer,
    engineering_question_role_prompt,
)
from software_world_model.ai_infrastructure.engineering_question_strategy import (
    ENGINEERING_QUESTION_UNDERSTANDING_OUTPUT_SCHEMA_REF,
    EngineeringQuestionModelRole,
    EngineeringQuestionRoleInputBuilder,
    engineering_question_output_schemas,
)
from software_world_model.ai_infrastructure.model_gateway import (
    AdapterConformanceLevel,
    AdapterResponse,
    ModelGateway,
    ProviderAdapterCapabilities,
    ProviderOutcomeUnknown,
    ProviderOutputRejected,
    ReplayClassification,
)
from software_world_model.application_services.engineering_question_answering import (
    EngineeringQuestionRequest,
    EngineeringQuestionResourceLimits,
    EngineeringReviewFocus,
    InvestigationOperation,
)
from software_world_model.cross_cutting import Digest, DomainError, ErrorCode, StableId, digest_of
from software_world_model.infrastructure import SqliteDatabase, SqliteModelGatewayRepository

from tests import test_engineering_question_answering as fixtures


_NOW = datetime(2026, 8, 21, 12, 0, tzinfo=timezone.utc)
_QUALIFICATION_REF = "CC-ENGINEERING-QA-FIXTURE:sha256:" + "9" * 64
_CONFIGURATION_FINGERPRINT = Digest("sha256:" + "8" * 64)


class LiveRoleAdapter:
    provider_type = "ENGINEERING_QA_FIXTURE"
    adapter_version = "engineering-qa-fixture@1"

    def __init__(
        self,
        *,
        qualification_ref: str = _QUALIFICATION_REF,
        outcome_unknown: bool = False,
        failure_code: ErrorCode | None = None,
        reject_output: bool = False,
    ) -> None:
        self.capabilities = ProviderAdapterCapabilities(
            no_external_access=True,
            hidden_context_disabled=True,
            stateless_session=True,
            structured_output=True,
            actual_fingerprint_reported=True,
            conformance_level=AdapterConformanceLevel.LIVE_CURRENT,
            conformance_result_ref=qualification_ref,
            qualified_model_fingerprints=("engineering-qa-model@1",),
        )
        self.outcome_unknown = outcome_unknown
        self.failure_code = failure_code
        self.reject_output = reject_output
        self.requests = []

    def invoke(self, request):
        self.requests.append(request)
        if self.outcome_unknown:
            raise ProviderOutcomeUnknown("fixture response boundary lost")
        if self.failure_code is not None:
            raise DomainError(self.failure_code, "fixture Provider failure")
        role_input = json.loads(request.messages[1].content)
        question = role_input["input"]["original_question"]
        language = role_input["input"]["response_language"]
        output = json.dumps(
            {
                "preserved_original_question": question,
                "user_goal": "Understand the system behavior.",
                "audience": "maintainer",
                "requested_abstraction_level": "USER_VISIBLE_EXPLANATION",
                "material_conclusions": ["Explain the requested behavior."],
                "evidence_needs": ["published cognition and exact source evidence"],
                "required_evidence_classes": ["SOURCE"],
                "required_evidence_paths": ["src/Service.java"],
                "response_language": language,
                "response_constraints": ["conclusion first"],
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        response = AdapterResponse.create(
            provider_request_id="engineering-qa-fixture-request",
            actual_model_fingerprint="engineering-qa-model@1",
            replay_classification=ReplayClassification.PINNED,
            output_text=output,
            input_tokens=100,
            output_tokens=40,
            usage_complete=True,
            termination_reason="stop",
        )
        if self.reject_output:
            raise ProviderOutputRejected(
                DomainError(
                    ErrorCode.STRUCTURED_OUTPUT_INVALID,
                    "fixture output exceeds the closed schema",
                ),
                response,
            )
        return response


def request(*, question: str = "How does this system start?") -> EngineeringQuestionRequest:
    profile = fixtures.source_profile()
    return EngineeringQuestionRequest.create(
        request_ref="engineering-qa-model-source-test",
        original_question=question,
        response_language="en",
        repository_id=fixtures.sid("repository", "1"),
        binding_id=fixtures.sid("binding", "2"),
        repository_revision=fixtures.REVISION,
        source_profile_ref=profile.profile_ref,
        source_profile_digest=profile.profile_digest,
        world_model_read_authority_digest=Digest("sha256:" + "3" * 64),
        source_allowlist=(".",),
        provider_disclosure_policy=ENGINEERING_QUESTION_DISCLOSURE_POLICY_REF,
    )


class EngineeringQuestionModelSourceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.database = SqliteDatabase()
        self.configuration = EngineeringQuestionModelConfiguration(
            provider_type=LiveRoleAdapter.provider_type,
            adapter_version=LiveRoleAdapter.adapter_version,
            endpoint="https://provider.example.test/v1/engineering-qa",
            model_ref="engineering-qa-model@1",
            expected_actual_model_fingerprint="engineering-qa-model@1",
            provider_configuration_fingerprint=_CONFIGURATION_FINGERPRINT,
            secret_reference="env:ENGINEERING_QA_FIXTURE_API_KEY",
            qualification_ref=_QUALIFICATION_REF,
            qualification_valid_until=_NOW + timedelta(days=1),
            maximum_calls=4,
        )
        self.request = request()

    def tearDown(self) -> None:
        self.database.close()

    def grant(
        self,
        *,
        request_value: EngineeringQuestionRequest | None = None,
        authorized_at: datetime | None = None,
        expires_at: datetime | None = None,
    ) -> EngineeringQuestionRunDisclosureAuthorization:
        message_digest = digest_of("user authorizes the exact fixture run")
        return EngineeringQuestionRunDisclosureAuthorization.create(
            run_ref="engineering-qa-preview:run-001",
            request=request_value or self.request,
            evaluation_subject_digest=digest_of("exact product tree"),
            configuration=self.configuration,
            maximum_dispatches=4,
            authorized_at=authorized_at or (_NOW - timedelta(minutes=1)),
            expires_at=expires_at or (_NOW + timedelta(hours=1)),
            authorization_ref=f"codex-user-message:{message_digest.value}",
            authorization_message_digest=message_digest,
        )

    def source(self, adapter, *, grant=None, policy_enforced=False):
        gateway = ModelGateway(
            SqliteModelGatewayRepository(self.database),
            (adapter,),
            clock=lambda: _NOW,
        )
        run_grant = grant or self.grant()
        if policy_enforced:
            gateway = PolicyEnforcingEngineeringQuestionModelGateway(
                gateway=gateway,
                policy=EngineeringQuestionModelEgressPolicy(
                    run_authorization=run_grant,
                    configuration=self.configuration,
                    clock=lambda: _NOW,
                ),
            )
        authorizer = SealedEngineeringQuestionRoleDisclosureAuthorizer(
            run_authorization=run_grant,
            configuration=self.configuration,
            clock=lambda: _NOW,
        )
        source = ModelBackedEngineeringQuestionStructuredOutputSource(
            gateway=gateway,
            configuration=self.configuration,
            authorizer=authorizer,
            clock=lambda: _NOW,
        )
        return source, authorizer

    def role_input(self, request_value=None):
        return EngineeringQuestionRoleInputBuilder.question_understanding(
            request=request_value or self.request,
            role_context_id=StableId("role_context_" + "4" * 32),
        )

    def output_arguments(self, request_value=None):
        schema_ref = ENGINEERING_QUESTION_UNDERSTANDING_OUTPUT_SCHEMA_REF
        return {
            "manifest": self.role_input(request_value),
            "output_schema_ref": schema_ref,
            "output_schema": engineering_question_output_schemas()[schema_ref],
        }

    def test_exact_dynamic_input_is_authorized_then_dispatched_once(self) -> None:
        adapter = LiveRoleAdapter()
        source, authorizer = self.source(adapter)

        output = source.output_for(**self.output_arguments())

        self.assertEqual(len(adapter.requests), 1)
        self.assertEqual(source.dispatch_attempt_count, 1)
        self.assertEqual(len(authorizer.disclosure_requests), 1)
        disclosure = authorizer.disclosure_requests[0]
        authorization = authorizer.issued_authorizations[0]
        self.assertEqual(disclosure.request_digest, self.request.digest)
        self.assertIn("/input/original_question", disclosure.disclosed_leaf_paths)
        self.assertEqual(
            authorization.full_model_input_digest,
            disclosure.full_model_input_digest,
        )
        self.assertEqual(output.input_manifest_digest, self.role_input().digest)
        wire_text = "\n".join(
            message.content for message in adapter.requests[0].messages
        )
        self.assertNotIn(self.configuration.secret_reference, wire_text)
        self.assertNotIn(authorization.authorization_ref, wire_text)
        self.assertEqual(source.audits[0].outcome, "COMPLETED")

    def test_session_authority_requires_exact_user_submission_before_run(self) -> None:
        template_digest = digest_of("fixed session request template")
        product_digest = digest_of("fixed alpha product subject")
        message_digest = digest_of("authorize sustained Engineering QA session")
        session = EngineeringQuestionSessionAuthority.create(
            session_ref="engineering-qa-alpha-session-001",
            product_candidate_digest=product_digest,
            request_template_digest=template_digest,
            configuration=self.configuration,
            maximum_questions=3,
            maximum_dispatches_per_question=4,
            maximum_total_dispatches=12,
            authorized_at=_NOW - timedelta(minutes=1),
            expires_at=_NOW + timedelta(hours=1),
            authorization_ref=f"codex-user-message:{message_digest.value}",
            authorization_message_digest=message_digest,
        )
        question = "How does this system start?"
        receipt = EngineeringQuestionSubmissionReceipt.create(
            receipt_id=StableId("engq_submission_" + "5" * 32),
            session_authority=session,
            question=question,
            disclosure_acknowledged=True,
            submitted_at=_NOW,
        )
        source_profile = fixtures.source_profile()
        submitted_request = EngineeringQuestionRequest.create(
            request_ref=receipt.receipt_id.value,
            original_question=question,
            response_language="en",
            repository_id=fixtures.sid("repository", "1"),
            binding_id=fixtures.sid("binding", "2"),
            repository_revision=fixtures.REVISION,
            source_profile_ref=source_profile.profile_ref,
            source_profile_digest=source_profile.profile_digest,
            world_model_read_authority_digest=Digest("sha256:" + "3" * 64),
            source_allowlist=(".",),
            provider_disclosure_policy=ENGINEERING_QUESTION_DISCLOSURE_POLICY_REF,
            limits=EngineeringQuestionResourceLimits(
                maximum_total_model_role_calls=4
            ),
        )
        run = EngineeringQuestionSessionRunDisclosureAuthorization.create_from_session(
            run_ref="engq_run_" + "6" * 32,
            request=submitted_request,
            evaluation_subject_digest=digest_of("submitted question subject"),
            configuration=self.configuration,
            session_authority=session,
            question_submission_receipt=receipt,
            request_template_digest=template_digest,
            product_candidate_digest=product_digest,
        )

        run.require_current(configuration=self.configuration, at=_NOW)
        self.assertEqual(run.session_authority_digest, session.digest)
        self.assertEqual(run.question_submission_receipt_digest, receipt.digest)
        with self.assertRaises(DomainError):
            EngineeringQuestionSubmissionReceipt.create(
                receipt_id=StableId("engq_submission_" + "7" * 32),
                session_authority=session,
                question="Another question",
                disclosure_acknowledged=False,
                submitted_at=_NOW,
            )

    def test_gateway_role_progress_accepts_investigation_schema_enum_values(self) -> None:
        for role in (
            EngineeringQuestionModelRole.INITIAL_INVESTIGATION,
            EngineeringQuestionModelRole.VERIFICATION_INVESTIGATION,
        ):
            for operation in (
                InvestigationOperation.SEARCH,
                InvestigationOperation.READ,
                InvestigationOperation.PARSE,
            ):
                self.assertEqual(
                    EngineeringQuestionModelEgressPolicy._next_roles(
                        role, {"operation": operation.value}
                    ),
                    {role},
                )
            self.assertEqual(
                EngineeringQuestionModelEgressPolicy._next_roles(
                    role, {"operation": InvestigationOperation.FINISH.value}
                ),
                {EngineeringQuestionModelRole.ANSWER},
            )

    def test_gateway_derives_review_progress_from_finding_remediation(self) -> None:
        review = EngineeringQuestionModelRole.REVIEW
        self.assertEqual(
            EngineeringQuestionModelEgressPolicy._next_roles(
                review,
                {"findings": []},
                review_focus=EngineeringReviewFocus.COMPREHENSIVE,
            ),
            {EngineeringQuestionModelRole.REVIEW},
        )
        self.assertEqual(
            EngineeringQuestionModelEgressPolicy._next_roles(
                review,
                {"findings": []},
                review_focus=(
                    EngineeringReviewFocus.EVIDENCE_BOUNDARY_CHALLENGE
                ),
            ),
            set(),
        )
        self.assertEqual(
            EngineeringQuestionModelEgressPolicy._next_roles(
                review,
                {
                    "findings": [
                        {"remediation": "REWRITE_WITH_EXISTING_EVIDENCE"}
                    ]
                },
                review_focus=EngineeringReviewFocus.COMPREHENSIVE,
            ),
            {EngineeringQuestionModelRole.ANSWER},
        )
        self.assertEqual(
            EngineeringQuestionModelEgressPolicy._next_roles(
                review,
                {
                    "findings": [
                        {"remediation": "INVESTIGATE_MISSING_EVIDENCE"}
                    ]
                },
                review_focus=EngineeringReviewFocus.COMPREHENSIVE,
            ),
            {EngineeringQuestionModelRole.VERIFICATION_INVESTIGATION},
        )
        self.assertEqual(
            EngineeringQuestionModelEgressPolicy._next_roles(
                review,
                {
                    "findings": [
                        {"remediation": "INVESTIGATE_MISSING_EVIDENCE"},
                        {"remediation": "REJECT_UNRECOVERABLE"},
                    ]
                },
                review_focus=EngineeringReviewFocus.COMPREHENSIVE,
            ),
            set(),
        )

    def test_current_investigation_prompt_requires_closed_operation_fields(self) -> None:
        self.assertEqual(
            ENGINEERING_QUESTION_MODEL_PROMPT_REF,
            "engineering-qa-adaptive-investigation-prompt@34",
        )
        for role in (
            EngineeringQuestionModelRole.INITIAL_INVESTIGATION,
            EngineeringQuestionModelRole.VERIFICATION_INVESTIGATION,
        ):
            prompt = " ".join(engineering_question_role_prompt(role).split())
            self.assertIn(
                "must return non-empty unique evidence_references",
                prompt,
            )
            self.assertIn(
                "short literal token likely to occur verbatim",
                prompt,
            )
            self.assertIn("required_basis_entry_id", prompt)
            self.assertIn("basis_entry_ids MUST include", prompt)
            self.assertIn("eligible_locator_references", prompt)
            self.assertIn("eligible_required_path_locators", prompt)
            self.assertIn("checklist_item_ids", prompt)
            self.assertIn("non-empty and unique", prompt)
            self.assertIn("never use", prompt)
            self.assertIn("a human locator/path, or an allowlisted path", prompt)
            self.assertIn(
                "Never repeat the same SEARCH evidence_class plus query pair",
                prompt,
            )
            self.assertIn("consumed_full_content_paths", prompt)
            self.assertIn("prior_action_intents", prompt)
            self.assertIn("progress_digest", prompt)
            self.assertIn("the newest action made no progress", prompt)
            self.assertIn("SEARCH requires a non-null evidence_class and query", prompt)
            self.assertIn("READ or PARSE requires a non-null evidence_class", prompt)
            self.assertIn(
                "FINISH requires evidence_class, query, and locator_reference all to be null",
                prompt,
            )
            self.assertIn("single finish_dispositions array", prompt)
            self.assertNotIn("supported_finish_dispositions", prompt)
            self.assertNotIn("non_supported_finish_dispositions", prompt)
            self.assertIn("Never duplicate a checklist item", prompt)
            self.assertIn(
                "Do not carry an evidence_class from the preceding action into FINISH",
                prompt,
            )
            self.assertIn("admissible_support_references", prompt)
            self.assertIn("admissible_boundary_references", prompt)
            self.assertIn("required_basis_entry_id binds the next action", prompt)
            self.assertIn("it is not observation evidence", prompt)
            self.assertIn(
                "lack of detail in one modality is not global absence",
                prompt,
            )
            self.assertIn("untried_required_evidence_classes", prompt)
            self.assertIn("unregistered_required_evidence_classes", prompt)
            self.assertIn("unread_required_evidence_paths", prompt)
            self.assertIn("SEARCH alone does not consume a path", prompt)
            self.assertIn("is rejected into a GAP", prompt)
            self.assertIn("one to 16 atomic material_observations", prompt)
            self.assertIn("A setup statement supports setup only", prompt)
            self.assertIn("wiring statement supports only that relationship", prompt)
            self.assertIn("final HTTP or API status", prompt)
            self.assertIn("framework default", prompt)
            self.assertIn("transport status", prompt)
            self.assertIn("configuration key and injection point", prompt)
            self.assertIn("do not infer DTO fields", prompt)
        verification_prompt = " ".join(
            engineering_question_role_prompt(
                EngineeringQuestionModelRole.VERIFICATION_INVESTIGATION
            ).split()
        )
        self.assertIn("last_broker_rejection", verification_prompt)
        self.assertIn("verification_gap_boundary_reference", verification_prompt)
        self.assertIn("excludes all predecessor-Package boundaries", verification_prompt)
        self.assertIn("preserves every non-gap disposition", verification_prompt)
        self.assertIn("entire authorized checklist scope", verification_prompt)
        understanding_prompt = " ".join(
            engineering_question_role_prompt(
                EngineeringQuestionModelRole.QUESTION_UNDERSTANDING
            ).split()
        )
        self.assertIn(
            "abstraction level controls the delivered answer, not which evidence",
            understanding_prompt,
        )
        self.assertIn("normally needs exact SOURCE behavior evidence", understanding_prompt)
        self.assertIn("smallest unique set directly needed", understanding_prompt)
        self.assertIn("required_evidence_paths", understanding_prompt)
        self.assertIn("mandatory-read set", understanding_prompt)
        self.assertIn("one to four exact strings", understanding_prompt)
        self.assertIn(
            "remain executable within the sealed investigation fuse",
            understanding_prompt,
        )
        self.assertIn(
            "Do not introduce TEST, logs, configuration, or another evidence modality",
            understanding_prompt,
        )
        self.assertIn(
            "minimum closure set, not the maximum investigation scope",
            understanding_prompt,
        )
        self.assertIn("separate checklist items", understanding_prompt)
        self.assertIn("audit, cache, notification", understanding_prompt)
        self.assertIn("externally visible error category", understanding_prompt)
        self.assertIn("response or exception mapper", understanding_prompt)
        self.assertIn("transport status", understanding_prompt)
        self.assertIn("concrete header name, token prefix", understanding_prompt)
        self.assertIn("unmounted DTO's fields", understanding_prompt)
        self.assertIn("make the checklist operational rather than inventory-shaped", understanding_prompt)
        self.assertIn("input/output handoff", understanding_prompt)
        initial_prompt = " ".join(
            engineering_question_role_prompt(
                EngineeringQuestionModelRole.INITIAL_INVESTIGATION
            ).split()
        )
        self.assertIn("one or more unique", initial_prompt)
        self.assertIn(
            "mandatory minimum, not the maximum investigation plan",
            initial_prompt,
        )
        self.assertIn("Do not FINISH merely because", initial_prompt)
        self.assertIn(
            "remaining_initial_investigation_calls_including_current",
            initial_prompt,
        )
        self.assertIn("mechanically restricted to issued locators", initial_prompt)
        answer_prompt = " ".join(
            engineering_question_role_prompt(
                EngineeringQuestionModelRole.ANSWER
            ).split()
        )
        self.assertIn(
            "coverage-only LIMITATION claim may use an empty material_observation_ids array",
            answer_prompt,
        )
        self.assertIn(
            "never attach supported observation IDs to such a limitation",
            answer_prompt,
        )
        self.assertIn(
            "Never assign LIMITATION kind to a USER_VISIBLE_PROCESS",
            answer_prompt,
        )
        self.assertIn(
            "each Package material-observation ID must appear exactly once",
            answer_prompt,
        )
        self.assertIn(
            "DIRECT_ANSWER may instead use an empty material_observation_ids array",
            answer_prompt,
        )
        self.assertIn("a partial overlap is rejected", answer_prompt)
        self.assertIn(
            "put their limitation observations in the one DIRECT_ANSWER limitation",
            answer_prompt,
        )
        self.assertIn("direct_answer object", answer_prompt)
        self.assertIn(
            "do not hide a requested verification basis in developer details",
            answer_prompt,
        )
        self.assertIn("claims array must never contain DIRECT_ANSWER", answer_prompt)
        self.assertIn("exactly one DIRECT_ANSWER in the entire output", answer_prompt)
        self.assertIn("For a mixed Package", answer_prompt)
        self.assertIn("final HTTP or API status", answer_prompt)
        self.assertIn("framework default", answer_prompt)
        self.assertIn("transport status", answer_prompt)
        self.assertIn("configuration key and injection point", answer_prompt)
        self.assertIn("unmounted DTO's fields", answer_prompt)
        self.assertIn(
            "material_observation_coverage_contract is an exact output checklist",
            answer_prompt,
        )
        self.assertIn(
            "removing one unsafe inference from a Claim never authorizes dropping",
            answer_prompt,
        )
        self.assertIn("organize the supported observations into an executable user sequence", answer_prompt)
        review_prompt = " ".join(
            engineering_question_role_prompt(
                EngineeringQuestionModelRole.REVIEW
            ).split()
        )
        self.assertIn(
            "do not call that empty link an Application observation omission",
            review_prompt,
        )
        self.assertIn("delegation-only evidence", review_prompt)
        self.assertIn("multiple mechanisms, participants, or checking surfaces", review_prompt)
        self.assertIn("explicitly scan every relevant full-content", review_prompt)
        self.assertIn("empty-link affirmative DIRECT_ANSWER", review_prompt)
        self.assertIn("cross-Claim and observation consistency", review_prompt)
        self.assertIn("Approval is represented only by PASS for all five", review_prompt)
        self.assertIn("REWRITE_WITH_EXISTING_EVIDENCE", review_prompt)
        self.assertIn("INVESTIGATE_MISSING_EVIDENCE", review_prompt)
        self.assertIn("REJECT_UNRECOVERABLE", review_prompt)
        self.assertIn("do not return a separate decision", review_prompt)
        self.assertIn("merely because the Draft mentions", review_prompt)
        self.assertIn("mapping owner's implementation", review_prompt)
        self.assertIn("verified_gap_outcomes", review_prompt)
        self.assertIn("MUST NOT request the same missing evidence again", review_prompt)
        self.assertIn("If the Draft introduced the status", review_prompt)
        self.assertIn("same local condition", review_prompt)
        self.assertIn("transport status", review_prompt)
        self.assertIn("EVIDENCE_BOUNDARY_CHALLENGE", review_prompt)
        self.assertIn("evidence_boundary_challenges", review_prompt)
        self.assertIn("projected items are review leads", review_prompt)
        self.assertIn("concrete runtime configuration value", review_prompt)
        self.assertIn("exactly one assessment for every required challenge_id", review_prompt)
        self.assertIn("evidence_boundary and the scope asserted", review_prompt)
        self.assertIn("DRAFT_EXCEEDS_EVIDENCE_BOUNDARY", review_prompt)
        self.assertIn("getter invocation in caller content", review_prompt)
        self.assertIn("FULL_CONTENT_MATERIAL_EFFECT_SCAN", review_prompt)
        self.assertIn("DRAFT_OMITS_MATERIAL_EFFECT", review_prompt)
        self.assertIn("omitted_material_effect_statements", review_prompt)
        self.assertIn("material_effect_omission_layer", review_prompt)
        self.assertIn("application_material_observations_for_entry", review_prompt)
        self.assertIn("same-Package rewrite cannot invent or substitute", review_prompt)
        self.assertIn("ORIGINAL_QUESTION_FULFILLMENT_SCAN", review_prompt)
        self.assertIn("DRAFT_OMITS_MATERIAL_REQUIREMENT", review_prompt)
        self.assertIn("input/output handoff", review_prompt)
        self.assertIn("required_effect_category", review_prompt)
        self.assertIn(
            "claim_id is one of that exact challenge's default_claim_ids",
            review_prompt,
        )

    def test_request_with_no_external_disclosure_cannot_receive_run_grant(self) -> None:
        with self.assertRaises(DomainError) as raised:
            self.grant(request_value=fixtures.request())

        self.assertEqual(raised.exception.code, ErrorCode.CONTROL_STATE_DENIED)

    def test_another_request_is_rejected_before_gateway_dispatch(self) -> None:
        adapter = LiveRoleAdapter()
        source, _ = self.source(adapter)
        another = request(question="Which configuration controls shutdown?")

        with self.assertRaises(DomainError) as raised:
            source.output_for(**self.output_arguments(another))

        self.assertEqual(raised.exception.code, ErrorCode.CONTROL_STATE_DENIED)
        self.assertEqual(adapter.requests, [])
        self.assertEqual(source.dispatch_attempt_count, 0)

    def test_expired_run_grant_is_rejected_before_source_construction(self) -> None:
        expired = self.grant(
            authorized_at=_NOW - timedelta(hours=2),
            expires_at=_NOW - timedelta(hours=1),
        )

        with self.assertRaises(DomainError) as raised:
            self.source(LiveRoleAdapter(), grant=expired)

        self.assertEqual(raised.exception.code, ErrorCode.CONTROL_STATE_DENIED)

    def test_unknown_provider_outcome_is_audited_and_never_retried(self) -> None:
        adapter = LiveRoleAdapter(outcome_unknown=True)
        source, _ = self.source(adapter, policy_enforced=True)
        arguments = self.output_arguments()

        with self.assertRaises(DomainError) as first:
            source.output_for(**arguments)
        with self.assertRaises(DomainError) as replay:
            source.output_for(**arguments)

        self.assertEqual(first.exception.code, ErrorCode.LIVE_INTEGRATION_HELD)
        self.assertIn("outcome is unknown", first.exception.message)
        self.assertIn("closed without retry", first.exception.message)
        self.assertEqual(
            first.exception.details["reason_code"],
            "PROVIDER_OUTCOME_UNKNOWN",
        )
        self.assertEqual(replay.exception.code, ErrorCode.CONTROL_STATE_DENIED)
        self.assertEqual(len(adapter.requests), 1)
        self.assertEqual(source.dispatch_attempt_count, 1)
        self.assertEqual(source.audits[0].model_call_state, "OUTCOME_UNKNOWN")
        self.assertEqual(source.audits[0].failure_code, "LIVE_INTEGRATION_HELD")
        self.assertEqual(source.audits[0].outcome, "REJECTED")

    def test_exact_provider_http_failure_is_not_reclassified_as_binding_drift(self) -> None:
        adapter = LiveRoleAdapter(failure_code=ErrorCode.PROVIDER_HTTP_ERROR)
        source, _ = self.source(adapter, policy_enforced=True)

        with self.assertRaises(DomainError) as raised:
            source.output_for(**self.output_arguments())

        self.assertEqual(raised.exception.code, ErrorCode.PROVIDER_HTTP_ERROR)
        self.assertIn(
            "current question was closed without retry", raised.exception.message
        )
        self.assertEqual(len(adapter.requests), 1)
        self.assertEqual(source.dispatch_attempt_count, 1)
        self.assertIsNotNone(source.audits[0].model_call_id)
        self.assertEqual(source.audits[0].model_call_state, "FAILED")
        self.assertEqual(source.audits[0].failure_code, "PROVIDER_HTTP_ERROR")
        self.assertEqual(source.audits[0].outcome, "REJECTED")

    def test_exact_rejected_output_is_not_reclassified_as_binding_drift(self) -> None:
        adapter = LiveRoleAdapter(reject_output=True)
        source, _ = self.source(adapter, policy_enforced=True)

        with self.assertRaises(DomainError) as raised:
            source.output_for(**self.output_arguments())

        self.assertEqual(raised.exception.code, ErrorCode.STRUCTURED_OUTPUT_INVALID)
        self.assertIn(
            "current question was closed without retry", raised.exception.message
        )
        self.assertEqual(len(adapter.requests), 1)
        self.assertEqual(source.dispatch_attempt_count, 1)
        self.assertIsNotNone(source.audits[0].model_call_id)
        self.assertEqual(source.audits[0].model_call_state, "COMPLETED")
        self.assertEqual(source.audits[0].failure_code, "STRUCTURED_OUTPUT_INVALID")
        self.assertEqual(source.audits[0].outcome, "REJECTED")

    def test_conformance_identity_drift_is_rejected_after_one_dispatch(self) -> None:
        adapter = LiveRoleAdapter(
            qualification_ref="CC-ENGINEERING-QA-FIXTURE:sha256:" + "7" * 64
        )
        source, _ = self.source(adapter)

        with self.assertRaises(DomainError) as raised:
            source.output_for(**self.output_arguments())

        self.assertEqual(raised.exception.code, ErrorCode.QUALIFICATION_INVALID)
        self.assertEqual(len(adapter.requests), 1)
        self.assertEqual(source.dispatch_attempt_count, 1)
        self.assertEqual(source.audits[0].outcome, "REJECTED")

    def test_gateway_side_policy_revalidates_grant_input_and_role_order(self) -> None:
        adapter = LiveRoleAdapter()
        gateway = ModelGateway(
            SqliteModelGatewayRepository(self.database),
            (adapter,),
            clock=lambda: _NOW,
        )
        run_grant = self.grant()
        policy = EngineeringQuestionModelEgressPolicy(
            run_authorization=run_grant,
            configuration=self.configuration,
            clock=lambda: _NOW,
        )
        authorizer = SealedEngineeringQuestionRoleDisclosureAuthorizer(
            run_authorization=run_grant,
            configuration=self.configuration,
            clock=lambda: _NOW,
        )
        source = ModelBackedEngineeringQuestionStructuredOutputSource(
            gateway=PolicyEnforcingEngineeringQuestionModelGateway(
                gateway=gateway,
                policy=policy,
            ),
            configuration=self.configuration,
            authorizer=authorizer,
            clock=lambda: _NOW,
        )

        source.output_for(**self.output_arguments())
        second = self.output_arguments()
        second["manifest"] = EngineeringQuestionRoleInputBuilder.question_understanding(
            request=self.request,
            role_context_id=StableId("role_context_" + "5" * 32),
        )
        with self.assertRaises(DomainError) as raised:
            source.output_for(**second)

        self.assertEqual(raised.exception.code, ErrorCode.QUALIFICATION_INVALID)
        self.assertEqual(policy.validated_roles, (second["manifest"].role,))
        self.assertEqual(len(adapter.requests), 1)
        self.assertEqual(source.dispatch_attempt_count, 2)


if __name__ == "__main__":
    unittest.main()
