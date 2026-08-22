from __future__ import annotations

from io import BytesIO
import json
import unittest

from software_world_model.application_services.engineering_question_answering import (
    EngineeringQuestionResourceLimits,
)
from software_world_model.cross_cutting import DomainError
from software_world_model.interface.engineering_qa_browser import (
    EngineeringQuestionBrowserApplication,
    FixedEngineeringQuestionRequestFactory,
    InMemoryEngineeringQuestionWebProduct,
)
from tests import test_engineering_question_answering as fixtures


class EngineeringQuestionBrowserTests(unittest.TestCase):
    def setUp(self):
        exact = fixtures.request()
        factory = FixedEngineeringQuestionRequestFactory(
            response_language=exact.response_language,
            repository_id=exact.repository_id,
            binding_id=exact.binding_id,
            repository_revision=exact.repository_revision,
            source_profile_ref=exact.source_profile_ref,
            source_profile_digest=exact.source_profile_digest,
            world_model_read_authority_digest=exact.world_model_read_authority_digest,
            source_allowlist=exact.source_allowlist,
            registered_operations=exact.registered_operations,
            provider_disclosure_policy=exact.provider_disclosure_policy,
            limits=exact.limits,
        )
        product = InMemoryEngineeringQuestionWebProduct(
            service=fixtures.EngineeringQuestionAnsweringTests().service(
                request_more_evidence=False
            ),
            request_factory=factory,
        )
        self.app = EngineeringQuestionBrowserApplication(product)

    def call(
        self,
        method,
        path,
        payload=None,
        *,
        raw_body=None,
        environ_overrides=None,
        app=None,
    ):
        raw = (
            raw_body
            if raw_body is not None
            else b"" if payload is None else json.dumps(payload).encode("utf-8")
        )
        captured = {}

        def start_response(status, headers):
            captured["status"] = status
            captured["headers"] = dict(headers)

        environ = {
            "REQUEST_METHOD": method,
            "PATH_INFO": path,
            "REMOTE_ADDR": "127.0.0.1",
            "HTTP_HOST": "127.0.0.1:8765",
            "CONTENT_LENGTH": str(len(raw)),
            "wsgi.input": BytesIO(raw),
        }
        environ.update(environ_overrides or {})
        body = b"".join(
            (app or self.app)(
                environ,
                start_response,
            )
        )
        captured["body"] = body
        return captured

    def test_page_and_health_keep_preview_boundary_visible(self):
        page = self.call("GET", "/")
        self.assertEqual(page["status"], "200 OK")
        html = page["body"].decode("utf-8")
        self.assertIn("ENGINEERING_QA", html)
        self.assertIn("方向体验 · 非验收 · 非生产", html)
        self.assertIn("Broker", html)
        self.assertIn('id="result-eyebrow"', html)
        self.assertIn('approved?"REVIEWED RESULT":"FAIL CLOSED"', html)

        health = self.call("GET", "/health")
        value = json.loads(health["body"])
        self.assertEqual(value["mode"], "ENGINEERING_QA")
        self.assertEqual(value["listener_requirement"], "127.0.0.1")
        self.assertFalse(value["external_provider_dispatch"])
        self.assertEqual(value["production_activation"], "NOT_EXECUTED")

    def test_question_returns_direct_answer_and_result_scoped_citations(self):
        response = self.call(
            "POST",
            "/v1/engineering-qa/questions",
            {
                "request_id": "browser-request-1",
                "question": fixtures.request().original_question,
            },
        )
        self.assertEqual(response["status"], "200 OK")
        value = json.loads(response["body"])
        self.assertEqual(value["status"], "APPROVED")
        self.assertIn("documented entry point", value["answer"]["body"])
        self.assertTrue(value["citations"])
        self.assertEqual(
            value["developer_details"]["role_direct_source_authority"],
            {
                "answer": False,
                "initial_investigation": False,
                "review": False,
                "verification_investigation": False,
            },
        )
        citation = self.call("GET", value["citations"][0]["url"])
        self.assertEqual(citation["status"], "200 OK")
        projection = json.loads(citation["body"])
        self.assertEqual(
            projection["entry_id"], value["citations"][0]["entry_id"]
        )
        self.assertFalse(projection["projection_is_answer_input"])

    def test_budget_closed_result_is_labeled_and_explained_as_a_limitation(self):
        limits = EngineeringQuestionResourceLimits(
            maximum_total_model_role_calls=3
        )
        exact = fixtures.request(limits=limits)
        factory = FixedEngineeringQuestionRequestFactory(
            response_language=exact.response_language,
            repository_id=exact.repository_id,
            binding_id=exact.binding_id,
            repository_revision=exact.repository_revision,
            source_profile_ref=exact.source_profile_ref,
            source_profile_digest=exact.source_profile_digest,
            world_model_read_authority_digest=exact.world_model_read_authority_digest,
            source_allowlist=exact.source_allowlist,
            registered_operations=exact.registered_operations,
            provider_disclosure_policy=exact.provider_disclosure_policy,
            limits=limits,
        )
        app = EngineeringQuestionBrowserApplication(
            InMemoryEngineeringQuestionWebProduct(
                service=fixtures.EngineeringQuestionAnsweringTests().service(
                    request_more_evidence=False
                ),
                request_factory=factory,
            )
        )
        response = self.call(
            "POST",
            "/v1/engineering-qa/questions",
            {
                "request_id": "browser-budget-closed",
                "question": exact.original_question,
            },
            app=app,
        )

        value = json.loads(response["body"])
        self.assertEqual(value["status"], "FAILED_CLOSED")
        self.assertEqual(
            value["limitation"]["reason"],
            "INDEPENDENT_REVIEW_RESERVE_EXHAUSTED",
        )
        self.assertIn("预留独立审核", value["limitation"]["message"])
        self.assertFalse(value["limitation"]["delivery_authorized"])
        self.assertEqual(
            value["developer_details"]["terminal_reason"],
            "INDEPENDENT_REVIEW_RESERVE_EXHAUSTED",
        )
        self.assertFalse(value["developer_details"]["answer_reached"])
        self.assertFalse(value["developer_details"]["review_reached"])

    def test_request_id_replay_is_idempotent_and_mismatch_fails(self):
        payload = {
            "request_id": "browser-request-2",
            "question": fixtures.request().original_question,
        }
        first = self.call("POST", "/v1/engineering-qa/questions", payload)
        second = self.call("POST", "/v1/engineering-qa/questions", payload)
        self.assertEqual(first["body"], second["body"])

        mismatch = self.call(
            "POST",
            "/v1/engineering-qa/questions",
            {"request_id": "browser-request-2", "question": "Another question"},
        )
        self.assertEqual(mismatch["status"], "400 Bad Request")
        self.assertEqual(json.loads(mismatch["body"])["error"], "IDEMPOTENCY_MISMATCH")

    def test_closed_request_schema_rejects_extra_authority_fields(self):
        response = self.call(
            "POST",
            "/v1/engineering-qa/questions",
            {
                "request_id": "browser-request-3",
                "question": fixtures.request().original_question,
                "repository_path": "/tmp/escape",
            },
        )
        self.assertEqual(response["status"], "400 Bad Request")
        self.assertEqual(json.loads(response["body"])["error"], "INVALID_ARGUMENT")

    def test_request_json_rejects_duplicate_keys_and_incomplete_body(self):
        duplicate = self.call(
            "POST",
            "/v1/engineering-qa/questions",
            raw_body=(
                b'{"request_id":"browser-request-duplicate",'
                b'"request_id":"browser-request-replaced","question":"safe"}'
            ),
        )
        self.assertEqual(duplicate["status"], "400 Bad Request")
        self.assertEqual(json.loads(duplicate["body"])["error"], "INVALID_JSON")

        incomplete = self.call(
            "POST",
            "/v1/engineering-qa/questions",
            raw_body=b'{"request_id":"short","question":"safe"}',
            environ_overrides={"CONTENT_LENGTH": "512"},
        )
        self.assertEqual(incomplete["status"], "400 Bad Request")
        self.assertEqual(json.loads(incomplete["body"])["error"], "INVALID_JSON")

    def test_non_loopback_origin_is_rejected_before_routing(self):
        response = self.call(
            "GET",
            "/health",
            environ_overrides={
                "REMOTE_ADDR": "192.0.2.10",
                "HTTP_HOST": "preview.example.test",
            },
        )
        self.assertEqual(response["status"], "403 Forbidden")
        self.assertEqual(
            json.loads(response["body"])["error"], "CONTROL_STATE_DENIED"
        )

    def test_local_preview_factory_cannot_authorize_external_disclosure(self):
        exact = fixtures.request()
        with self.assertRaises(DomainError):
            FixedEngineeringQuestionRequestFactory(
                response_language=exact.response_language,
                repository_id=exact.repository_id,
                binding_id=exact.binding_id,
                repository_revision=exact.repository_revision,
                source_profile_ref=exact.source_profile_ref,
                source_profile_digest=exact.source_profile_digest,
                world_model_read_authority_digest=exact.world_model_read_authority_digest,
                source_allowlist=exact.source_allowlist,
                provider_disclosure_policy="EXTERNAL_PROVIDER_ALLOWED",
            )


if __name__ == "__main__":
    unittest.main()
