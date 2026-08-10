from __future__ import annotations

from io import BytesIO
import json
from pathlib import Path
import subprocess
from types import SimpleNamespace
import tempfile
import unittest

from software_world_model.interface.http_api import (
    JsonHttpApplication,
    LoopbackWsgiRequestHandler,
    _browser_answer_projection,
    _browser_original_request,
)
from software_world_model.interface.runtime import ApplicationRuntime
from software_world_model.infrastructure import SqliteDatabase
from software_world_model.source_integration import TargetKind
from software_world_model.application_services import AnswerSectionKind


def _value(value):
    return SimpleNamespace(value=value)


class RecordingAnswerRuntime:
    natural_task_planning_configured = True
    reviewed_answer_preparation_configured = True

    def __init__(self) -> None:
        self.knowledge = SimpleNamespace(current_snapshot=lambda scope_id: None)
        self.update_arguments = None
        self.request = None

    def prepare_knowledge_update_request(self, **arguments):
        self.update_arguments = arguments
        return SimpleNamespace(
            request_id="prepared-update",
            scope_id=arguments["scope_id"],
            expected_current_snapshot_id=arguments[
                "expected_current_snapshot_id"
            ],
            classification=arguments["classification"],
            idempotency_key=arguments["idempotency_key"],
            digest=_value("sha256:prepared-update"),
        )

    def prepare_task_answer(self, request):
        self.request = request
        assessment = SimpleNamespace(
            assessment_id=_value("assessment-browser"),
            snapshot_id=_value("snapshot-browser"),
            sufficient=True,
            items=(),
            joint_constraint_failures=(),
            digest=_value("sha256:assessment"),
        )
        candidate = SimpleNamespace(
            candidate_id=_value("candidate-browser"),
            response_kind=_value("KNOWLEDGE_COMPLETE"),
            body="这是经过正式知识链复核的回答。",
            claims=(),
            digest=_value("sha256:candidate"),
        )
        return SimpleNamespace(
            task=SimpleNamespace(
                task_id=_value("task-browser"), revision=_value(1)
            ),
            assessment=assessment,
            requirement=SimpleNamespace(
                requirement_id=_value("requirement-browser")
            ),
            candidate=candidate,
            review=SimpleNamespace(
                review_id=_value("review-browser"),
                decision=_value("APPROVED"),
                digest=_value("sha256:review"),
            ),
            authorization=SimpleNamespace(
                authorization_id=_value("authorization-browser"),
                digest=_value("sha256:authorization"),
            ),
            digest=_value("sha256:answer"),
        )


class RecordingEvidenceRuntime:
    natural_task_planning_configured = False
    reviewed_answer_preparation_configured = True
    evidence_answer_preparation_configured = True

    def __init__(self) -> None:
        self.request_arguments = None
        self.request = None

    def prepare_evidence_answer_request(self, **arguments):
        self.request_arguments = arguments
        return SimpleNamespace(
            original_request=arguments["original_request"],
            idempotency_key=arguments["idempotency_key"],
        )

    def prepare_evidence_answer(self, request):
        self.request = request
        return SimpleNamespace(
            draft=SimpleNamespace(
                body="入口读取配置后启动服务。",
                sections=(
                    SimpleNamespace(kind=AnswerSectionKind.SUPPORTED),
                ),
            ),
            unresolved_count=0,
            sources=("src/Entry.py@" + "a" * 40 + " (bytes:0-120)",),
            evidence_packet=SimpleNamespace(
                packet_id=_value("evidence_packet_" + "1" * 32)
            ),
        )

class BrowserChatInterfaceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.repository = self.root / "sample-project"
        self.repository.mkdir()
        self._git("init", "-q")
        self._git("config", "user.email", "test@example.com")
        self._git("config", "user.name", "Test")
        (self.repository / "README.md").write_text(
            "Sample browser project.\n", encoding="utf-8"
        )
        self._git("add", ".")
        self._git("commit", "-q", "-m", "initial")
        self.commit = self._git("rev-parse", "HEAD").strip()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _git(self, *arguments: str) -> str:
        return subprocess.run(
            ("git", "-C", str(self.repository), *arguments),
            check=True,
            stdout=subprocess.PIPE,
            text=True,
        ).stdout

    @staticmethod
    def _http(application, method: str, path: str, payload=None):
        body = json.dumps(payload).encode("utf-8") if payload is not None else b""
        captured = {}

        def start_response(status, headers):
            captured["status"] = status
            captured["headers"] = dict(headers)

        response = b"".join(
            application(
                {
                    "REQUEST_METHOD": method,
                    "PATH_INFO": path,
                    "CONTENT_TYPE": "application/json" if payload is not None else "",
                    "CONTENT_LENGTH": str(len(body)),
                    "wsgi.input": BytesIO(body),
                },
                start_response,
            )
        )
        return captured["status"], captured["headers"], response

    def test_browser_page_and_assets_are_same_origin_and_hardened(self) -> None:
        database_path = self.root / "browser.sqlite3"
        with SqliteDatabase(database_path) as database:
            application = JsonHttpApplication(ApplicationRuntime(database))
            status, headers, html = self._http(application, "GET", "/")
            script_status, script_headers, script = self._http(
                application, "GET", "/assets/browser.js"
            )

        self.assertEqual(status, "200 OK")
        self.assertEqual(headers["Content-Type"], "text/html; charset=utf-8")
        self.assertIn("default-src 'self'", headers["Content-Security-Policy"])
        self.assertEqual(headers["X-Frame-Options"], "DENY")
        self.assertIn("软件世界模型", html.decode("utf-8"))
        self.assertEqual(script_status, "200 OK")
        self.assertEqual(
            script_headers["Content-Type"], "text/javascript; charset=utf-8"
        )
        self.assertIn(b"/v1/browser/chat", script)

    def test_http_handler_applies_server_request_timeout(self) -> None:
        connection = SimpleNamespace(
            settimeout=lambda value: setattr(connection, "timeout", value)
        )
        handler = object.__new__(LoopbackWsgiRequestHandler)
        handler.server = SimpleNamespace(request_timeout_seconds=4.5)
        handler.connection = connection

        handler._apply_request_timeout()

        self.assertEqual(connection.timeout, 4.5)

    def test_project_connection_freezes_revision_and_hides_owner_ids(self) -> None:
        database_path = self.root / "project.sqlite3"
        with SqliteDatabase(database_path) as database:
            application = JsonHttpApplication(ApplicationRuntime(database))
            status, _, raw = self._http(
                application,
                "POST",
                "/v1/browser/projects",
                {
                    "request_id": "connect-browser-project",
                    "repository_path": str(self.repository),
                    "revision": "HEAD",
                    "selected_paths": ".",
                    "comparison_base": None,
                },
            )
            project = json.loads(raw)["project"]
            chat_status, _, chat_raw = self._http(
                application,
                "POST",
                "/v1/browser/chat",
                {
                    "request_id": "browser-question-held",
                    "conversation_id": "conversation-one",
                    "turn_number": 1,
                    "message": "这个项目做什么？",
                    "project": project,
                },
            )

        self.assertEqual(status, "200 OK")
        self.assertEqual(project["display_name"], "sample-project")
        self.assertEqual(project["target_kind"], "REPOSITORY_REVISION")
        self.assertEqual(project["target_parameters"], {"revision": self.commit})
        self.assertNotIn("bootstrap_paths", project)
        self.assertNotIn("known_paths", project)
        self.assertTrue(project["scope_id"])
        self.assertTrue(project["source_id"])
        self.assertTrue(project["binding_id"])
        self.assertEqual(chat_status, "503 Service Unavailable")
        self.assertEqual(json.loads(chat_raw)["error"], "LIVE_INTEGRATION_HELD")

    def test_project_connection_rejects_non_absolute_path(self) -> None:
        database_path = self.root / "invalid.sqlite3"
        with SqliteDatabase(database_path) as database:
            application = JsonHttpApplication(ApplicationRuntime(database))
            status, _, raw = self._http(
                application,
                "POST",
                "/v1/browser/projects",
                {
                    "request_id": "relative-project",
                    "repository_path": "relative/project",
                    "revision": "HEAD",
                    "selected_paths": ".",
                    "comparison_base": None,
                },
            )

        self.assertEqual(status, "400 Bad Request")
        self.assertEqual(json.loads(raw)["error"], "INVALID_ARGUMENT")

    def test_browser_message_enters_reviewed_answer_preparation(self) -> None:
        runtime = RecordingAnswerRuntime()
        application = JsonHttpApplication(
            runtime, live_provider_configured=True
        )
        status, _, raw = self._http(
            application,
            "POST",
            "/v1/browser/chat",
            {
                "request_id": "question-one",
                "conversation_id": "conversation-one",
                "turn_number": 1,
                "message": "解释主要流程",
                "history": [
                    {"role": "user", "content": "这个服务做什么？"},
                    {
                        "role": "assistant",
                        "content": "它负责处理项目请求。",
                    },
                ],
                "project": {
                    "display_name": "sample-project",
                    "scope_id": "scope_" + "1" * 32,
                    "scope_revision": 1,
                    "source_id": "source_" + "2" * 32,
                    "source_revision": 1,
                    "binding_id": "binding_" + "3" * 32,
                    "binding_revision": 1,
                    "selected_paths": ".",
                    "target_kind": "REPOSITORY_REVISION",
                    "target_parameters": {"revision": "a" * 40},
                },
            },
        )
        payload = json.loads(raw)

        self.assertEqual(status, "200 OK")
        self.assertEqual(payload["message"], "这是经过正式知识链复核的回答。")
        self.assertEqual(payload["response_kind"], "KNOWLEDGE_COMPLETE")
        self.assertTrue(payload["reviewed"])
        self.assertEqual(
            runtime.update_arguments["target_kind"],
            TargetKind.REPOSITORY_REVISION,
        )
        self.assertIn("这个服务做什么？", runtime.request.original_request)
        self.assertIn("当前问题：解释主要流程", runtime.request.original_request)
        self.assertIn("不属于本轮回答目标", runtime.request.original_request)
        self.assertIn("使用与当前问题相同的语言", runtime.request.original_request)
        self.assertNotIn("它负责处理项目请求", runtime.request.original_request)
        self.assertEqual(
            runtime.request.knowledge_update_request.request_id,
            "prepared-update",
        )

    def test_browser_message_prefers_evidence_first_answering(self) -> None:
        runtime = RecordingEvidenceRuntime()
        application = JsonHttpApplication(runtime, live_provider_configured=True)

        status, _, raw = self._http(
            application,
            "POST",
            "/v1/browser/chat",
            {
                "request_id": "evidence-question-one",
                "conversation_id": "conversation-one",
                "turn_number": 1,
                "message": "入口如何启动服务？",
                "project": {
                    "display_name": "sample-project",
                    "scope_id": "scope_" + "1" * 32,
                    "scope_revision": 1,
                    "source_id": "source_" + "2" * 32,
                    "source_revision": 1,
                    "binding_id": "binding_" + "3" * 32,
                    "binding_revision": 1,
                    "selected_paths": ".",
                    "target_kind": "REPOSITORY_REVISION",
                    "target_parameters": {"revision": "a" * 40},
                },
            },
        )
        payload = json.loads(raw)

        self.assertEqual(status, "200 OK")
        self.assertEqual(payload["message"], "入口读取配置后启动服务。")
        self.assertEqual(payload["response_kind"], "EVIDENCE_COMPLETE")
        self.assertTrue(payload["reviewed"])
        self.assertEqual(payload["claim_count"], 1)
        self.assertEqual(payload["unresolved_count"], 0)
        self.assertEqual(len(payload["sources"]), 1)
        self.assertIn(
            "当前问题：入口如何启动服务？",
            runtime.request_arguments["original_request"],
        )
        self.assertEqual(
            runtime.request_arguments["target_kind"],
            TargetKind.REPOSITORY_REVISION,
        )

    def test_browser_request_limits_history_to_prior_user_questions(self) -> None:
        request = _browser_original_request(
            "主要组件如何协作？",
            [
                {"role": "user", "content": "介绍下这个工程"},
                {
                    "role": "assistant",
                    "content": "A very long generated project summary.",
                },
            ],
        )

        self.assertIn("用户先前问题：介绍下这个工程", request)
        self.assertIn("当前问题：主要组件如何协作？", request)
        self.assertNotIn("generated project summary", request)
        self.assertIn("忠实回答当前问题", request)
        self.assertIn("回答语言：简体中文", request)

    def test_browser_questions_share_one_pipeline_without_semantic_routing(self) -> None:
        runtime = RecordingAnswerRuntime()
        application = JsonHttpApplication(
            runtime, live_provider_configured=True
        )
        project = {
            "display_name": "unconventional-project",
            "scope_id": "scope_" + "1" * 32,
            "scope_revision": 1,
            "source_id": "source_" + "2" * 32,
            "source_revision": 1,
            "binding_id": "binding_" + "3" * 32,
            "binding_revision": 1,
            "selected_paths": ".",
            "target_kind": "REPOSITORY_REVISION",
            "target_parameters": {"revision": "a" * 40},
        }

        questions = (
            "概括这个仓库解决的问题。",
            "数据在三个文件之间怎样变化？",
            "如果源码没有说明设计原因，请指出证据缺口。",
            "Which configuration value controls startup?",
        )
        for index, question in enumerate(questions, 1):
            status, _, _ = self._http(
                application,
                "POST",
                "/v1/browser/chat",
                {
                    "request_id": f"generic-question-{index}",
                    "conversation_id": "generic-conversation",
                    "turn_number": index,
                    "message": question,
                    "project": project,
                },
            )

            self.assertEqual(status, "200 OK")
            self.assertEqual(runtime.update_arguments["allowed_source_paths"], ())
            self.assertEqual(runtime.update_arguments["required_source_paths"], ())
            self.assertIn(question, runtime.request.original_request)

    def test_browser_projection_hides_internal_gap_template(self) -> None:
        answer = {
            "requirement": {
                "needs": [
                    {"need_id": "overview", "question": "这个项目做什么？"},
                    {"need_id": "entry", "question": "入口文件是什么？"},
                    {"need_id": "usage", "question": "如何启动？"},
                ]
            },
            "assessment": {
                "items": [
                    {"need_id": "overview", "gap": None},
                    {"need_id": "entry", "gap": "尚未读取启动类。"},
                    {"need_id": "usage", "gap": None},
                ]
            },
            "candidate": {
                "body": "internal canonical body",
                "claims": [
                    {
                        "need_id": "overview",
                        "kind": "FORMAL_KNOWLEDGE",
                        "text": "这是一个电商系统。",
                    },
                    {
                        "need_id": "entry",
                        "kind": "KNOWLEDGE_GAP",
                        "text": "Requested question: 入口文件是什么？",
                    },
                    {
                        "need_id": "usage",
                        "kind": "FORMAL_KNOWLEDGE",
                        "text": "管理服务依赖 MySQL 和 Redis。",
                    },
                    {
                        "need_id": "usage",
                        "kind": "APPLICATION_LIMITATION",
                        "text": "现有源码只说明依赖条件，没有给出完整启动命令。",
                    },
                    {
                        "need_id": "usage",
                        "kind": "APPLICATION_LIMITATION",
                        "text": "管理服务依赖 MySQL 和 Redis",
                    },
                ],
            },
        }

        message, confirmed, unresolved = _browser_answer_projection(
            answer,
            "介绍下这个工程",
            sources=("README.md:23-31", "pom.xml:17-23"),
        )

        self.assertEqual(confirmed, 2)
        self.assertEqual(unresolved, 1)
        self.assertIn("已确认", message)
        self.assertIn("1. 这个项目做什么？", message)
        self.assertIn("2. 如何启动？", message)
        self.assertIn("尚未确认", message)
        self.assertIn("入口文件是什么？：尚未读取启动类。", message)
        self.assertIn("管理服务依赖 MySQL 和 Redis。", message)
        self.assertIn(
            "说明：现有源码只说明依赖条件，没有给出完整启动命令。",
            message,
        )
        self.assertEqual(message.count("管理服务依赖 MySQL 和 Redis"), 1)
        self.assertIn("源码位置", message)
        self.assertIn("README.md:23-31", message)
        self.assertIn("pom.xml:17-23", message)
        self.assertNotIn("Requested question", message)
        self.assertNotIn("Verified answer", message)
        self.assertNotIn("形式记录", message)


if __name__ == "__main__":
    unittest.main()
