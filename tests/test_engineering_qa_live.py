from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import unittest

from software_world_model.ai_infrastructure.deepseek_chat_adapter import (
    DeepSeekModelConfiguration,
)
from software_world_model.ai_infrastructure.deepseek_chat_conformance import (
    DeepSeekChatConformanceQualification,
)
from software_world_model.ai_infrastructure.engineering_question_model_source import (
    ENGINEERING_QUESTION_DISCLOSURE_POLICY_REF,
    EngineeringQuestionRunDisclosureAuthorization,
    EngineeringQuestionSessionAuthority,
)
from software_world_model.ai_infrastructure.engineering_question_strategy import (
    ENGINEERING_QUESTION_UNDERSTANDING_OUTPUT_SCHEMA_REF,
    EngineeringQuestionRoleInputBuilder,
    engineering_question_output_schemas,
)
from software_world_model.ai_infrastructure.openai_responses_adapter import (
    ProviderHTTPResponse,
)
from software_world_model.application_services.engineering_question_answering import (
    EngineeringQuestionRequest,
    EngineeringQuestionResourceLimits,
    SourceBroker,
)
from software_world_model.cross_cutting import (
    Digest,
    DomainError,
    ErrorCode,
    StableId,
    digest_of,
)
from software_world_model.infrastructure import SqliteDatabase, SqliteModelGatewayRepository
from software_world_model.interface.engineering_qa_live import (
    create_deepseek_engineering_question_browser_assembly,
    create_deepseek_engineering_question_role_runtime,
    create_deepseek_engineering_question_session_browser_assembly,
    engineering_question_deepseek_configuration,
)
from software_world_model.interface.engineering_qa_browser import (
    EngineeringQuestionSessionRequestTemplate,
)

from tests import test_engineering_question_answering as fixtures


_NOW = datetime(2099, 1, 1, 13, 0, tzinfo=timezone.utc)


class DeepSeekFixtureTransport:
    def __init__(self) -> None:
        self.calls = []

    def post_json(self, *, endpoint, body, client_request_id, timeout_milliseconds):
        self.calls.append(
            {
                "endpoint": endpoint,
                "body": body,
                "client_request_id": client_request_id,
                "timeout_milliseconds": timeout_milliseconds,
            }
        )
        role_payload = json.loads(json.loads(body)["messages"][1]["content"])
        output = json.dumps(
            {
                "preserved_original_question": role_payload["input"][
                    "original_question"
                ],
                "user_goal": "Understand the exact startup behavior.",
                "audience": "maintainer",
                "requested_abstraction_level": "USER_VISIBLE_EXPLANATION",
                "material_conclusions": ["Explain how startup works."],
                "evidence_needs": ["published cognition and exact repository evidence"],
                "response_language": role_payload["input"]["response_language"],
                "response_constraints": ["conclusion first"],
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        return ProviderHTTPResponse(
            status_code=200,
            headers={"X-Request-Id": "deepseek-engineering-qa-fixture"},
            body=json.dumps(
                {
                    "id": "chatcmpl-engineering-qa-fixture",
                    "object": "chat.completion",
                    "created": 1787290000,
                    "model": "deepseek-v4-pro",
                    "choices": [
                        {
                            "index": 0,
                            "message": {"role": "assistant", "content": output},
                            "finish_reason": "stop",
                        }
                    ],
                    "usage": {
                        "prompt_tokens": 500,
                        "completion_tokens": 100,
                        "total_tokens": 600,
                        "prompt_cache_hit_tokens": 0,
                        "prompt_cache_miss_tokens": 500,
                    },
                },
                separators=(",", ":"),
            ).encode("utf-8"),
        )


def engineering_request() -> EngineeringQuestionRequest:
    profile = fixtures.source_profile()
    return EngineeringQuestionRequest.create(
        request_ref="deepseek-engineering-qa-live-fixture",
        original_question="How does this system start?",
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


class EngineeringQALiveCompositionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.database = SqliteDatabase()
        self.provider_configuration = DeepSeekModelConfiguration()
        self.qualification = DeepSeekChatConformanceQualification(
            result_ref="CC-DEEPSEEK-CHAT-NO-TOOLS-001:sha256:" + "7" * 64,
            result_digest=Digest("sha256:" + "7" * 64),
            qualified_model_fingerprints=("deepseek-v4-pro",),
            adapter_version=self.provider_configuration.adapter_version,
            provider_configuration_fingerprint=(
                self.provider_configuration.fingerprint
            ),
            valid_until=_NOW + timedelta(days=1),
        )

    def tearDown(self) -> None:
        self.database.close()

    def test_exact_deepseek_adapter_gateway_and_policy_compose_without_secret_read(self):
        configuration = engineering_question_deepseek_configuration(
            provider_configuration=self.provider_configuration,
            qualification=self.qualification,
            maximum_calls=4,
            at=_NOW,
        )
        request = engineering_request()
        message_digest = digest_of("authorize exact DeepSeek Engineering QA fixture")
        run_grant = EngineeringQuestionRunDisclosureAuthorization.create(
            run_ref="engineering-qa-deepseek-fixture:run-001",
            request=request,
            evaluation_subject_digest=digest_of("exact DeepSeek product subject"),
            configuration=configuration,
            maximum_dispatches=4,
            authorized_at=_NOW - timedelta(minutes=1),
            expires_at=_NOW + timedelta(hours=1),
            authorization_ref=f"codex-user-message:{message_digest.value}",
            authorization_message_digest=message_digest,
        )
        transport = DeepSeekFixtureTransport()
        runtime = create_deepseek_engineering_question_role_runtime(
            repository=SqliteModelGatewayRepository(self.database),
            transport=transport,
            provider_configuration=self.provider_configuration,
            qualification=self.qualification,
            run_authorization=run_grant,
            configuration=configuration,
            clock=lambda: _NOW,
        )
        manifest = EngineeringQuestionRoleInputBuilder.question_understanding(
            request=request,
            role_context_id=StableId("role_context_" + "6" * 32),
        )
        schema_ref = ENGINEERING_QUESTION_UNDERSTANDING_OUTPUT_SCHEMA_REF

        output = runtime.output_source.output_for(
            manifest=manifest,
            output_schema_ref=schema_ref,
            output_schema=engineering_question_output_schemas()[schema_ref],
        )

        self.assertEqual(len(transport.calls), 1)
        self.assertEqual(runtime.policy.validated_roles, (manifest.role,))
        self.assertEqual(runtime.output_source.dispatch_attempt_count, 1)
        self.assertEqual(output.input_manifest_digest, manifest.digest)
        wire = transport.calls[0]["body"].decode("utf-8")
        self.assertNotIn("env:DEEPSEEK_API_KEY", wire)
        self.assertNotIn(run_grant.authorization_ref, wire)
        messages = json.loads(wire)["messages"]
        self.assertEqual([item["role"] for item in messages], ["system", "user"])
        self.assertIn("JSON Schema", messages[0]["content"])

        assembly = create_deepseek_engineering_question_browser_assembly(
            request=request,
            role_runtime=runtime,
            run_authorization=run_grant,
            cognition_projector=fixtures.CognitionProjector(),
            source_broker=SourceBroker(source_profile=fixtures.source_profile()),
            retrieval_worker=fixtures.ScriptedWorker(),
            at=_NOW,
        )
        health = assembly.product.health()
        self.assertTrue(health["external_provider_dispatch"])
        self.assertEqual(health["prepared_request_id"], request.request_ref)
        self.assertEqual(health["prepared_question"], request.original_question)
        self.assertEqual(
            health["run_authorization_digest"], run_grant.digest.value
        )
        self.assertEqual(health["production_activation"], "NOT_EXECUTED")

    def test_session_composition_creates_fresh_exact_run_without_dispatch(self):
        class RepeatingIds:
            def new(self, kind):
                return StableId(f"{kind}_" + "9" * 32)

        configuration = engineering_question_deepseek_configuration(
            provider_configuration=self.provider_configuration,
            qualification=self.qualification,
            maximum_calls=4,
            at=_NOW,
        )
        exact = engineering_request()
        source_profile = fixtures.source_profile()
        source_class_allowlist = tuple(
            (evidence_class.value, paths)
            for evidence_class, paths in source_profile.evidence_class_paths
        )
        template = EngineeringQuestionSessionRequestTemplate.create(
            response_language=exact.response_language,
            repository_id=exact.repository_id,
            binding_id=exact.binding_id,
            repository_revision=exact.repository_revision,
            source_profile_ref=exact.source_profile_ref,
            source_profile_digest=exact.source_profile_digest,
            world_model_read_authority_digest=exact.world_model_read_authority_digest,
            source_allowlist=tuple(
                path for _, paths in source_class_allowlist for path in paths
            ),
            registered_operations=exact.registered_operations,
            provider_disclosure_policy=configuration.provider_disclosure_policy_ref,
            limits=EngineeringQuestionResourceLimits(
                maximum_total_model_role_calls=4
            ),
            source_class_allowlist=source_class_allowlist,
        )
        product_digest = digest_of("exact sustained Alpha subject")
        message_digest = digest_of("authorize exact sustained Alpha session")
        authority = EngineeringQuestionSessionAuthority.create(
            session_ref="engineering-qa-alpha-live-fixture",
            product_candidate_digest=product_digest,
            request_template_digest=template.digest,
            configuration=configuration,
            maximum_questions=3,
            maximum_dispatches_per_question=4,
            maximum_total_dispatches=12,
            authorized_at=_NOW - timedelta(minutes=1),
            expires_at=_NOW + timedelta(hours=1),
            authorization_ref=f"codex-user-message:{message_digest.value}",
            authorization_message_digest=message_digest,
        )
        transports = []

        def transport_factory():
            transport = DeepSeekFixtureTransport()
            transports.append(transport)
            return transport

        assembly = create_deepseek_engineering_question_session_browser_assembly(
            repository=SqliteModelGatewayRepository(self.database),
            transport_factory=transport_factory,
            provider_configuration=self.provider_configuration,
            qualification=self.qualification,
            configuration=configuration,
            session_authority=authority,
            request_template=template,
            product_candidate_digest=product_digest,
            cognition_projector=fixtures.CognitionProjector(),
            source_broker=SourceBroker(source_profile=fixtures.source_profile()),
            retrieval_worker=fixtures.ScriptedWorker(),
            known_limitations=("Alpha evaluation only",),
            at=_NOW,
            clock=lambda: _NOW,
            id_generator=RepeatingIds(),
        )
        execution = assembly.execution_factory.create(
            question="How does this system start?",
            disclosure_acknowledged=True,
        )

        self.assertEqual(execution.request.original_question, "How does this system start?")
        self.assertEqual(
            execution.run_authorization.session_authority_digest,
            authority.digest,
        )
        self.assertEqual(len(transports), 1)
        self.assertEqual(transports[0].calls, [])
        health = assembly.product.health()
        self.assertEqual(health["question_submission_mode"], "SESSION_AUTHORIZED")
        self.assertEqual(health["project"]["repository_revision"], exact.repository_revision)
        with self.assertRaises(DomainError) as repeated:
            assembly.execution_factory.create(
                question="How does another part start?",
                disclosure_acknowledged=True,
            )
        self.assertEqual(
            repeated.exception.code,
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
        )
        self.assertEqual(len(transports), 1)


if __name__ == "__main__":
    unittest.main()
