from __future__ import annotations

from io import BytesIO
from datetime import datetime, timedelta, timezone
import json
import unittest

from software_world_model.ai_infrastructure.engineering_question_model_source import (
    EngineeringQuestionModelConfiguration,
    EngineeringQuestionSessionAuthority,
    EngineeringQuestionSessionRunDisclosureAuthorization,
    EngineeringQuestionSubmissionReceipt,
)
from software_world_model.application_services.engineering_question_answering import (
    EngineeringQuestionResourceLimits,
)
from software_world_model.cross_cutting import (
    Digest,
    DomainError,
    ErrorCode,
    StableId,
    digest_of,
)
from software_world_model.interface.engineering_qa_browser import (
    EngineeringQuestionBrowserApplication,
    EngineeringQuestionSessionExecution,
    EngineeringQuestionSessionRequestTemplate,
    EngineeringQuestionWebRuntimeStatus,
    FixedEngineeringQuestionRequestFactory,
    InMemoryEngineeringQuestionWebProduct,
    InMemoryEngineeringQuestionSessionWebProduct,
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
        if method.upper() == "POST":
            environ.update(
                {
                    "CONTENT_TYPE": "application/json",
                    "HTTP_ORIGIN": "http://127.0.0.1:8765",
                    "HTTP_SEC_FETCH_SITE": "same-origin",
                }
            )
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

    def test_cross_origin_or_non_json_submission_is_rejected_before_session_creation(self):
        session_factory, runtime_status = self.session_factory()
        app = EngineeringQuestionBrowserApplication(
            InMemoryEngineeringQuestionSessionWebProduct(
                execution_factory=session_factory,
                runtime_status=runtime_status,
                known_limitations=("Alpha evaluation only",),
            )
        )
        payload = {
            "question": "How does startup work?",
            "disclosure_acknowledged": True,
        }
        cross_origin = self.call(
            "POST",
            "/v1/engineering-qa/questions",
            payload,
            environ_overrides={
                "HTTP_ORIGIN": "https://attacker.example",
                "HTTP_SEC_FETCH_SITE": "cross-site",
            },
            app=app,
        )
        non_json = self.call(
            "POST",
            "/v1/engineering-qa/questions",
            payload,
            environ_overrides={"CONTENT_TYPE": "text/plain"},
            app=app,
        )

        self.assertEqual(cross_origin["status"], "403 Forbidden")
        self.assertEqual(non_json["status"], "403 Forbidden")
        self.assertEqual(session_factory.created_questions, 0)

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

    def test_session_web_accepts_multiple_questions_with_server_owned_ids(self):
        session_factory, runtime_status = self.session_factory()
        app = EngineeringQuestionBrowserApplication(
            InMemoryEngineeringQuestionSessionWebProduct(
                execution_factory=session_factory,
                runtime_status=runtime_status,
                known_limitations=(
                    "Alpha evaluation only",
                    "fixed Java project and revision",
                ),
            )
        )
        health = self.call("GET", "/health", app=app)
        health_value = json.loads(health["body"])
        self.assertEqual(
            health_value["question_submission_mode"], "SESSION_AUTHORIZED"
        )
        self.assertEqual(health_value["project"]["repository_revision"], fixtures.REVISION)
        self.assertEqual(
            set(health_value["project"]["source_class_allowlist"]),
            {"SOURCE", "REPOSITORY_DOCUMENT", "BUILD_CONFIGURATION", "TEST"},
        )
        self.assertTrue(health_value["known_limitations"])

        pages = []
        for question in ("How does startup work?", "What controls timeout?"):
            response = self.call(
                "POST",
                "/v1/engineering-qa/questions",
                {"question": question, "disclosure_acknowledged": True},
                app=app,
            )
            self.assertEqual(response["status"], "200 OK")
            pages.append(json.loads(response["body"]))
        self.assertNotEqual(
            pages[0]["submission"]["request_id"],
            pages[1]["submission"]["request_id"],
        )
        self.assertNotEqual(
            pages[0]["submission"]["receipt_digest"],
            pages[1]["submission"]["receipt_digest"],
        )
        self.assertEqual(session_factory.created_questions, 2)

        client_authority = self.call(
            "POST",
            "/v1/engineering-qa/questions",
            {
                "request_id": "client-controlled",
                "question": "unsafe",
                "disclosure_acknowledged": True,
            },
            app=app,
        )
        self.assertEqual(client_authority["status"], "400 Bad Request")

    def test_session_question_failure_does_not_stop_the_next_question(self):
        session_factory, runtime_status = self.session_factory(fail_first=True)
        app = EngineeringQuestionBrowserApplication(
            InMemoryEngineeringQuestionSessionWebProduct(
                execution_factory=session_factory,
                runtime_status=runtime_status,
                known_limitations=("Alpha evaluation only",),
            )
        )
        first = self.call(
            "POST",
            "/v1/engineering-qa/questions",
            {"question": "controlled failure", "disclosure_acknowledged": True},
            app=app,
        )
        self.assertEqual(first["status"], "409 Conflict")
        second = self.call(
            "POST",
            "/v1/engineering-qa/questions",
            {"question": "How does startup work?", "disclosure_acknowledged": True},
            app=app,
        )
        self.assertEqual(second["status"], "200 OK")
        self.assertEqual(json.loads(second["body"])["status"], "APPROVED")
        health = json.loads(self.call("GET", "/health", app=app)["body"])
        self.assertEqual(health["session"]["accepted_question_count"], 2)

    def test_session_rejects_a_replayed_submission_and_closes_its_execution(self):
        base_factory, runtime_status = self.session_factory()
        question = "How does startup work?"
        first_execution = base_factory.create(
            question=question,
            disclosure_acknowledged=True,
        )
        close_count = 0

        def close():
            nonlocal close_count
            close_count += 1

        repeated_execution = EngineeringQuestionSessionExecution(
            request=first_execution.request,
            submission_receipt=first_execution.submission_receipt,
            run_authorization=first_execution.run_authorization,
            service=first_execution.service,
            dispatch_attempt_count=first_execution.dispatch_attempt_count,
            close=close,
        )

        class RepeatingFactory:
            session_authority = base_factory.session_authority
            request_template = base_factory.request_template

            def create(self, **_):
                return repeated_execution

        product = InMemoryEngineeringQuestionSessionWebProduct(
            execution_factory=RepeatingFactory(),
            runtime_status=runtime_status,
            known_limitations=("Alpha evaluation only",),
        )
        product.answer(
            request_ref=None,
            question=question,
            disclosure_acknowledged=True,
        )
        with self.assertRaises(DomainError) as replay:
            product.answer(
                request_ref=None,
                question=question,
                disclosure_acknowledged=True,
            )

        self.assertEqual(replay.exception.code, ErrorCode.CONTROL_STATE_DENIED)
        self.assertEqual(close_count, 2)

    def session_factory(self, *, fail_first: bool = False):
        now = datetime.now(timezone.utc)
        exact = fixtures.request(
            limits=EngineeringQuestionResourceLimits(
                maximum_total_model_role_calls=24
            )
        )
        source_profile = fixtures.source_profile()
        source_class_allowlist = tuple(
            (evidence_class.value, paths)
            for evidence_class, paths in source_profile.evidence_class_paths
        )
        source_allowlist = tuple(
            path for _, paths in source_class_allowlist for path in paths
        )
        configuration = EngineeringQuestionModelConfiguration(
            provider_type="FIXTURE",
            adapter_version="fixture@1",
            endpoint="https://provider.example.test/v1/chat",
            model_ref="fixture-model@1",
            expected_actual_model_fingerprint="fixture-model@1",
            provider_configuration_fingerprint=Digest("sha256:" + "8" * 64),
            secret_reference="env:FIXTURE_API_KEY",
            qualification_ref="fixture-qualification",
            qualification_valid_until=now + timedelta(days=1),
            maximum_calls=24,
        )
        template = EngineeringQuestionSessionRequestTemplate.create(
            response_language=exact.response_language,
            repository_id=exact.repository_id,
            binding_id=exact.binding_id,
            repository_revision=exact.repository_revision,
            source_profile_ref=exact.source_profile_ref,
            source_profile_digest=exact.source_profile_digest,
            world_model_read_authority_digest=exact.world_model_read_authority_digest,
            source_allowlist=source_allowlist,
            registered_operations=exact.registered_operations,
            provider_disclosure_policy=configuration.provider_disclosure_policy_ref,
            limits=exact.limits,
            source_class_allowlist=source_class_allowlist,
        )
        product_digest = digest_of("session browser product")
        message_digest = digest_of("authorize browser session")
        authority = EngineeringQuestionSessionAuthority.create(
            session_ref="browser-session-fixture",
            product_candidate_digest=product_digest,
            request_template_digest=template.digest,
            configuration=configuration,
            maximum_questions=3,
            maximum_dispatches_per_question=24,
            maximum_total_dispatches=72,
            authorized_at=now - timedelta(minutes=1),
            expires_at=now + timedelta(hours=1),
            authorization_ref=f"codex-user-message:{message_digest.value}",
            authorization_message_digest=message_digest,
        )
        factory = _FixtureSessionExecutionFactory(
            session_authority=authority,
            request_template=template,
            configuration=configuration,
            product_digest=product_digest,
            now=now,
            fail_first=fail_first,
        )
        runtime = EngineeringQuestionWebRuntimeStatus.session_authorized(
            template=template,
            configuration=configuration,
            session_authority=authority,
            product_candidate_digest=product_digest,
            at=now,
        )
        return factory, runtime


class _FailingService:
    def answer(self, request):
        raise DomainError(
            ErrorCode.STRUCTURED_OUTPUT_INVALID,
            "controlled request failure",
        )


class _FixtureSessionExecutionFactory:
    def __init__(
        self,
        *,
        session_authority,
        request_template,
        configuration,
        product_digest,
        now,
        fail_first,
    ):
        self.session_authority = session_authority
        self.request_template = request_template
        self.configuration = configuration
        self.product_digest = product_digest
        self.now = now
        self.fail_first = fail_first
        self.created_questions = 0

    def create(self, *, question, disclosure_acknowledged):
        self.created_questions += 1
        digit = f"{self.created_questions:032x}"
        receipt = EngineeringQuestionSubmissionReceipt.create(
            receipt_id=StableId("engq_submission_" + digit),
            session_authority=self.session_authority,
            question=question,
            disclosure_acknowledged=disclosure_acknowledged,
            submitted_at=self.now,
        )
        request = self.request_template.create_request(
            receipt=receipt,
            question=question,
        )
        run = EngineeringQuestionSessionRunDisclosureAuthorization.create_from_session(
            run_ref="engq_run_" + digit,
            request=request,
            evaluation_subject_digest=digest_of(["session question", digit]),
            configuration=self.configuration,
            session_authority=self.session_authority,
            question_submission_receipt=receipt,
            request_template_digest=self.request_template.digest,
            product_candidate_digest=self.product_digest,
        )
        service = (
            _FailingService()
            if self.fail_first and self.created_questions == 1
            else fixtures.EngineeringQuestionAnsweringTests().service(
                request_more_evidence=False
            )
        )
        return EngineeringQuestionSessionExecution(
            request=request,
            submission_receipt=receipt,
            run_authorization=run,
            service=service,
            dispatch_attempt_count=lambda: 0,
            close=lambda: None,
        )


if __name__ == "__main__":
    unittest.main()
