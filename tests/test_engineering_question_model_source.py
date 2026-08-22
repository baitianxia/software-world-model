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
    ModelBackedEngineeringQuestionStructuredOutputSource,
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
    ReplayClassification,
)
from software_world_model.application_services.engineering_question_answering import (
    EngineeringQuestionRequest,
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
        self.requests = []

    def invoke(self, request):
        self.requests.append(request)
        if self.outcome_unknown:
            raise ProviderOutcomeUnknown("fixture response boundary lost")
        role_input = json.loads(request.messages[1].content)
        question = role_input["input"]["original_question"]
        language = role_input["input"]["response_language"]
        output = json.dumps(
            {
                "preserved_original_question": question,
                "user_goal": "Understand the system behavior.",
                "audience": "maintainer",
                "requested_abstraction_level": "engineering overview",
                "material_conclusions": ["Explain the requested behavior."],
                "evidence_needs": ["published cognition and exact source evidence"],
                "response_language": language,
                "response_constraints": ["conclusion first"],
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        return AdapterResponse.create(
            provider_request_id="engineering-qa-fixture-request",
            actual_model_fingerprint="engineering-qa-model@1",
            replay_classification=ReplayClassification.PINNED,
            output_text=output,
            input_tokens=100,
            output_tokens=40,
            usage_complete=True,
            termination_reason="stop",
        )


class PolicyGateway:
    def __init__(self, *, delegate, policy) -> None:
        self.delegate = delegate
        self.policy = policy

    def invoke(self, context):
        self.policy.validate_context(context)
        result = self.delegate.invoke(context)
        self.policy.validate_result(result)
        return result


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

    def source(self, adapter, *, grant=None):
        gateway = ModelGateway(
            SqliteModelGatewayRepository(self.database),
            (adapter,),
            clock=lambda: _NOW,
        )
        run_grant = grant or self.grant()
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

    def test_current_investigation_prompt_requires_finish_boundary_references(self) -> None:
        self.assertEqual(
            ENGINEERING_QUESTION_MODEL_PROMPT_REF,
            "engineering-qa-adaptive-investigation-prompt@4",
        )
        for role in (
            EngineeringQuestionModelRole.INITIAL_INVESTIGATION,
            EngineeringQuestionModelRole.VERIFICATION_INVESTIGATION,
        ):
            prompt = " ".join(engineering_question_role_prompt(role).split())
            self.assertIn(
                "never return an empty evidence_references array",
                prompt,
            )
            self.assertIn(
                "short literal token likely to occur verbatim",
                prompt,
            )
            self.assertIn("exact opaque locator_reference ID", prompt)
            self.assertIn("never use", prompt)
            self.assertIn("locator/path or an allowlisted path", prompt)
            self.assertIn("Never repeat an earlier query or locator intent", prompt)
            self.assertIn("path already returned as exact full content", prompt)
            self.assertIn("progress_digest", prompt)

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
        source, _ = self.source(adapter)
        arguments = self.output_arguments()

        with self.assertRaises(DomainError):
            source.output_for(**arguments)
        with self.assertRaises(DomainError) as replay:
            source.output_for(**arguments)

        self.assertEqual(replay.exception.code, ErrorCode.CONTROL_STATE_DENIED)
        self.assertEqual(len(adapter.requests), 1)
        self.assertEqual(source.dispatch_attempt_count, 1)
        self.assertEqual(source.audits[0].model_call_state, "OUTCOME_UNKNOWN")
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
            gateway=PolicyGateway(delegate=gateway, policy=policy),
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
