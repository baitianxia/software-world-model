from __future__ import annotations

from datetime import datetime, timezone
from io import BytesIO
import json
import unittest

from software_world_model.application_services.engineering_conversation import (
    ConversationMessageKind,
    EngineeringChatBinding,
    EngineeringTurnCitation,
    EngineeringTurnExecutionOutcome,
    InMemoryEngineeringConversationService,
    RuntimeCapabilityStatus,
)
from software_world_model.cross_cutting import Revision, StableId, digest_of
from software_world_model.interface.engineering_chat_browser import (
    ENGINEERING_CHAT_MAXIMUM_REQUEST_BYTES,
    EngineeringChatBrowserApplication,
)


class SequentialIdGenerator:
    def __init__(self) -> None:
        self.value = 0

    def new(self, kind: str) -> StableId:
        self.value += 1
        return StableId(f"{kind}_{self.value:032x}")


class EngineeringChatBrowserTests(unittest.TestCase):
    def setUp(self) -> None:
        binding = EngineeringChatBinding.create(
            product_revision="a" * 40,
            project_name="mall",
            repository_revision="b" * 40,
            known_limitations=(
                "Chat Access only",
                "src/main/resources and credentials are excluded",
            ),
        )
        self.service = InMemoryEngineeringConversationService(
            binding,
            id_generator=SequentialIdGenerator(),
            clock=lambda: datetime(2026, 8, 25, 7, 30, tzinfo=timezone.utc),
        )
        self.app = EngineeringChatBrowserApplication(self.service)

    def call(
        self,
        method: str,
        path: str,
        payload=None,
        *,
        raw_body: bytes | None = None,
        environ_overrides: dict[str, object] | None = None,
    ) -> dict[str, object]:
        raw = (
            raw_body
            if raw_body is not None
            else b"" if payload is None else json.dumps(payload).encode("utf-8")
        )
        captured: dict[str, object] = {}

        def start_response(status, headers):
            captured["status"] = status
            captured["headers"] = dict(headers)

        environ: dict[str, object] = {
            "REQUEST_METHOD": method,
            "PATH_INFO": path,
            "REMOTE_ADDR": "127.0.0.1",
            "HTTP_HOST": "127.0.0.1:8765",
            "CONTENT_LENGTH": str(len(raw)),
            "wsgi.input": BytesIO(raw),
        }
        if method.upper() == "POST":
            environ.update(
                {
                    "CONTENT_TYPE": "application/json",
                    "HTTP_ORIGIN": "http://127.0.0.1:8765",
                    "HTTP_SEC_FETCH_SITE": "same-origin",
                }
            )
        environ.update(environ_overrides or {})
        captured["body"] = b"".join(self.app(environ, start_response))
        return captured

    @staticmethod
    def value(response: dict[str, object]) -> dict[str, object]:
        return json.loads(response["body"])

    def create_conversation(self) -> dict[str, object]:
        response = self.call(
            "POST", "/v1/engineering-chat/conversations", payload={}
        )
        self.assertEqual(response["status"], "201 Created")
        return self.value(response)

    def test_page_assets_and_health_expose_access_boundary(self) -> None:
        page = self.call("GET", "/")
        script = self.call("GET", "/assets/engineering-chat.js")
        health = self.call("GET", "/health")

        self.assertEqual(page["status"], "200 OK")
        self.assertIn("ENGINEERING_CHAT_EXPERIENCE@1", page["body"].decode())
        self.assertIn("质量未验收 · 非生产", page["body"].decode())
        self.assertIn("＋ 新对话", page["body"].decode())
        self.assertIn(
            "script-src 'self'",
            page["headers"]["Content-Security-Policy"],
        )
        self.assertNotIn(
            "script-src 'self' 'unsafe-inline'",
            page["headers"]["Content-Security-Policy"],
        )
        self.assertEqual(script["status"], "200 OK")
        self.assertIn(
            "/v1/engineering-chat/conversations", script["body"].decode()
        )
        self.assertIn('turn.state==="SUCCEEDED"', script["body"].decode())
        self.assertIn(
            "value.capabilities.semantic_agent_execution",
            script["body"].decode(),
        )
        self.assertIn("turnEvidenceNode", script["body"].decode())
        self.assertIn("fresh Review", script["body"].decode())
        self.assertIn("citation.locator", script["body"].decode())

        value = self.value(health)
        self.assertEqual(value["status"], "READY")
        self.assertEqual(value["implementation_scope"], "CHAT_ACCESS_ONLY")
        self.assertEqual(value["quality"], "NOT_ACCEPTED")
        self.assertEqual(value["production_activation"], "NOT_EXECUTED")
        self.assertEqual(value["provider"]["status"], "NOT_CONFIGURED")
        self.assertFalse(value["provider"]["external_dispatch"])
        self.assertEqual(value["statistics"]["provider_dispatch_count"], 0)

    def test_qualified_executor_projection_exposes_reviewed_success(self) -> None:
        class SuccessfulExecutor:
            def execute(self, request):
                work_state_digest = digest_of(
                    {"work_state": request.request_digest.value}
                )
                citation = EngineeringTurnCitation.create(
                    citation_ref="citation-ref",
                    evidence_class="SOURCE",
                    source_revision=request.binding.repository_revision,
                    locator="src/main/java/example/LoginService.java:L10-L18",
                    modality="JAVA_SOURCE",
                    content_digest=digest_of("exact-source-content"),
                )
                return EngineeringTurnExecutionOutcome.succeeded(
                    request_digest=request.request_digest,
                    assistant_kind=ConversationMessageKind.ANSWER,
                    assistant_content="当前答案经过独立审核和交付授权。",
                    included_user_message_ids=(request.user_message.message_id,),
                    accepted_correction_message_ids=(),
                    reviewed_conclusion_refs=("answer-ref",),
                    superseded_conclusion_refs=(),
                    reducer_status="EXECUTED_APPLICATION_SEALED",
                    work_state_ref="work-state-ref",
                    work_state_revision=Revision(1),
                    work_state_digest=work_state_digest,
                    evidence_package_ref="package-ref",
                    answer_ref="answer-ref",
                    review_ref="review-ref",
                    delivery_authorization_ref="delivery-ref",
                    provider_dispatch_count=2,
                    quality_status="ACCEPTED",
                    citations=(citation,),
                )

        binding = EngineeringChatBinding.create(
            product_revision="a" * 40,
            project_name="mall",
            repository_revision="b" * 40,
            world_model_status=RuntimeCapabilityStatus.READY,
            world_model_authority_digest=digest_of({"world_model": "exact"}),
            source_profile_ref="source-profile@1",
            source_access_status=RuntimeCapabilityStatus.READY,
            provider_status=RuntimeCapabilityStatus.READY,
            provider_route_ref="qualified-route@1",
            known_limitations=("Alpha only",),
        )
        service = InMemoryEngineeringConversationService(
            binding,
            turn_executor=SuccessfulExecutor(),
            id_generator=SequentialIdGenerator(),
        )
        self.app = EngineeringChatBrowserApplication(service)
        health = self.value(self.call("GET", "/health"))
        created = self.create_conversation()
        conversation_id = created["conversation"]["conversation_id"]
        response = self.call(
            "POST",
            f"/v1/engineering-chat/conversations/{conversation_id}/turns",
            {"conversation_revision": 1, "message": "当前行为是什么？"},
        )
        value = self.value(response)

        self.assertEqual(
            value["schema"], "ENGINEERING_CHAT_CONVERSATION_PROJECTION@2"
        )
        self.assertEqual(health["implementation_scope"], "CONVERSATIONAL_AGENT_EXECUTOR")
        self.assertTrue(health["capabilities"]["semantic_agent_execution"])
        self.assertTrue(health["provider"]["external_dispatch"])
        self.assertEqual(value["submitted_turn"]["state"], "SUCCEEDED")
        self.assertEqual(value["submitted_turn"]["quality_status"], "ACCEPTED")
        self.assertEqual(value["submitted_turn"]["delivery_state"], "AUTHORIZED")
        self.assertEqual(value["messages"][-1]["kind"], "ANSWER")
        self.assertEqual(value["context"]["work_state_ref"], "work-state-ref")
        self.assertEqual(value["submitted_turn"]["work_state_revision"], 1)
        self.assertEqual(
            value["submitted_turn"]["citations"],
            [
                {
                    "citation_ref": "citation-ref",
                    "evidence_class": "SOURCE",
                    "source_revision": "b" * 40,
                    "locator": "src/main/java/example/LoginService.java:L10-L18",
                    "modality": "JAVA_SOURCE",
                    "content_digest": digest_of(
                        "exact-source-content"
                    ).value,
                    "digest": EngineeringTurnCitation.create(
                        citation_ref="citation-ref",
                        evidence_class="SOURCE",
                        source_revision="b" * 40,
                        locator="src/main/java/example/LoginService.java:L10-L18",
                        modality="JAVA_SOURCE",
                        content_digest=digest_of("exact-source-content"),
                    ).digest.value,
                }
            ],
        )
        after = self.value(self.call("GET", "/health"))
        self.assertEqual(after["statistics"]["provider_dispatch_count"], 2)

    def test_server_creates_conversation_and_records_real_failed_turn(self) -> None:
        created = self.create_conversation()
        conversation = created["conversation"]
        self.assertTrue(conversation["conversation_id"].startswith("conversation_"))
        self.assertEqual(conversation["revision"], 1)
        self.assertEqual(created["messages"], [])

        response = self.call(
            "POST",
            f"/v1/engineering-chat/conversations/{conversation['conversation_id']}/turns",
            {
                "conversation_revision": conversation["revision"],
                "message": "登录流程是怎样的？",
            },
        )
        value = self.value(response)

        self.assertEqual(response["status"], "200 OK")
        self.assertEqual(value["conversation"]["revision"], 2)
        self.assertEqual(value["conversation"]["state"], "ACTIVE")
        self.assertEqual(len(value["messages"]), 2)
        self.assertEqual(value["messages"][0]["role"], "USER")
        self.assertEqual(value["messages"][1]["kind"], "LIMITATION")
        self.assertEqual(value["submitted_turn"]["state"], "FAILED")
        self.assertEqual(
            value["submitted_turn"]["failure"]["code"],
            "PROVIDER_NOT_CONFIGURED",
        )
        self.assertEqual(value["submitted_turn"]["provider_dispatch_count"], 0)
        self.assertEqual(value["submitted_turn"]["delivery_state"], "NOT_AUTHORIZED")
        self.assertEqual(value["submitted_turn"]["quality_status"], "NOT_ACCEPTED")

    def test_failure_does_not_stop_next_turn_and_get_returns_full_history(self) -> None:
        created = self.create_conversation()
        conversation_id = created["conversation"]["conversation_id"]
        first = self.value(
            self.call(
                "POST",
                f"/v1/engineering-chat/conversations/{conversation_id}/turns",
                {"conversation_revision": 1, "message": "先解释登录流程"},
            )
        )
        second_response = self.call(
            "POST",
            f"/v1/engineering-chat/conversations/{conversation_id}/turns",
            {"conversation_revision": 2, "message": "再说明失败分支"},
        )
        fetched = self.call(
            "GET", f"/v1/engineering-chat/conversations/{conversation_id}"
        )
        second = self.value(second_response)
        fetched_value = self.value(fetched)

        self.assertEqual(first["conversation"]["state"], "ACTIVE")
        self.assertEqual(second_response["status"], "200 OK")
        self.assertEqual(second["submitted_turn"]["sequence"], 2)
        self.assertEqual(second["conversation"]["state"], "ACTIVE")
        self.assertEqual(fetched["status"], "200 OK")
        self.assertEqual(fetched_value["conversation"]["revision"], 3)
        self.assertEqual(len(fetched_value["messages"]), 4)
        self.assertEqual(len(fetched_value["turns"]), 2)

    def test_new_conversation_has_no_old_messages_or_context_references(self) -> None:
        first = self.create_conversation()
        first_id = first["conversation"]["conversation_id"]
        self.call(
            "POST",
            f"/v1/engineering-chat/conversations/{first_id}/turns",
            {"conversation_revision": 1, "message": "保留在旧对话的问题"},
        )
        second = self.create_conversation()

        self.assertNotEqual(second["conversation"]["conversation_id"], first_id)
        self.assertEqual(second["conversation"]["revision"], 1)
        self.assertEqual(second["context"]["included_user_message_ids"], [])
        self.assertEqual(second["messages"], [])
        self.assertEqual(second["turns"], [])

    def test_origin_json_and_input_boundaries_fail_before_state_mutation(self) -> None:
        denied_loopback = self.call(
            "POST",
            "/v1/engineering-chat/conversations",
            payload={},
            environ_overrides={"REMOTE_ADDR": "192.0.2.1"},
        )
        denied_origin = self.call(
            "POST",
            "/v1/engineering-chat/conversations",
            payload={},
            environ_overrides={"HTTP_ORIGIN": "http://example.test"},
        )
        denied_type = self.call(
            "POST",
            "/v1/engineering-chat/conversations",
            payload={},
            environ_overrides={"CONTENT_TYPE": "text/plain"},
        )
        duplicate = self.call(
            "POST",
            "/v1/engineering-chat/conversations",
            raw_body=b'{"field":1,"field":2}',
        )
        oversized = self.call(
            "POST",
            "/v1/engineering-chat/conversations",
            raw_body=b"x" * (ENGINEERING_CHAT_MAXIMUM_REQUEST_BYTES + 1),
        )

        self.assertEqual(denied_loopback["status"], "403 Forbidden")
        self.assertEqual(denied_origin["status"], "403 Forbidden")
        self.assertEqual(denied_type["status"], "403 Forbidden")
        self.assertEqual(duplicate["status"], "400 Bad Request")
        self.assertEqual(self.value(duplicate)["error"], "INVALID_JSON")
        self.assertEqual(oversized["status"], "400 Bad Request")
        health = self.value(self.call("GET", "/health"))
        self.assertEqual(health["statistics"]["conversation_count"], 0)
        self.assertEqual(health["statistics"]["turn_count"], 0)

    def test_stale_revision_and_unknown_conversation_are_explicit(self) -> None:
        created = self.create_conversation()
        conversation_id = created["conversation"]["conversation_id"]
        stale = self.call(
            "POST",
            f"/v1/engineering-chat/conversations/{conversation_id}/turns",
            {"conversation_revision": 2, "message": "并发问题"},
        )
        missing = self.call(
            "GET",
            "/v1/engineering-chat/conversations/conversation_" + "f" * 32,
        )

        self.assertEqual(stale["status"], "409 Conflict")
        self.assertEqual(self.value(stale)["error"], "REVISION_CONFLICT")
        self.assertEqual(missing["status"], "404 Not Found")
        self.assertEqual(
            self.value(missing)["error"], "CONVERSATION_NOT_FOUND"
        )


if __name__ == "__main__":
    unittest.main()
