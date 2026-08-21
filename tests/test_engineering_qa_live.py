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
    SourceBroker,
)
from software_world_model.cross_cutting import Digest, StableId, digest_of
from software_world_model.infrastructure import SqliteDatabase, SqliteModelGatewayRepository
from software_world_model.interface.engineering_qa_live import (
    create_deepseek_engineering_question_browser_assembly,
    create_deepseek_engineering_question_role_runtime,
    engineering_question_deepseek_configuration,
)

from tests import test_engineering_question_answering as fixtures


_NOW = datetime(2026, 8, 21, 13, 0, tzinfo=timezone.utc)


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
                "requested_abstraction_level": "engineering overview",
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


if __name__ == "__main__":
    unittest.main()
