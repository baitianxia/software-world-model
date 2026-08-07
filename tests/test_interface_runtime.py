from __future__ import annotations

from io import BytesIO, StringIO
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from software_world_model.application_services import (
    KnowledgeNeed,
    KnowledgeRequirementPlan,
)
from software_world_model.interface.cli import main
from software_world_model.interface.http_api import JsonHttpApplication
from software_world_model.interface.runtime import ApplicationRuntime
from software_world_model.infrastructure import SqliteDatabase
from software_world_model.knowledge_engine import KnowledgeObjectKind


class StaticRequirementPlanner:
    def plan(self, *, original_request):
        return KnowledgeRequirementPlan(
            needs=(
                KnowledgeNeed(
                    need_id="need:planned",
                    question=original_request,
                    required_kinds=(KnowledgeObjectKind.FACT,),
                    required_type_names=("DESCRIBED_AS",),
                    required_terms=("OrderService", "submitted orders"),
                    minimum_support_count=1,
                ),
            )
        )


class InterfaceRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        self.database = root / "swm.sqlite3"
        self.repository = root / "repository"
        self.repository.mkdir()
        self._git("init", "-q")
        self._git("config", "user.email", "test@example.com")
        self._git("config", "user.name", "Test")
        (self.repository / "src").mkdir()
        (self.repository / "src" / "service.txt").write_text(
            "OrderService handles submitted orders.\n", encoding="utf-8"
        )
        self._git("add", ".")
        self._git("commit", "-q", "-m", "initial")
        self.commit = self._git("rev-parse", "HEAD").strip()
        configured = self._cli(
            "configure-system-source",
            "--idempotency-key",
            "configure",
            "--source-target",
            str(self.repository),
            "--paths",
            "src",
            "--display-name",
            "Fixture",
            "--actor",
            "test",
            "--reason",
            "interface test",
            "--correlation-ref",
            "interface-test",
        )
        steps = {item["name"]: item for item in configured[1]["steps"]}
        self.scope_id = steps["CREATE_SCOPE"]["result_reference"]
        self.source_id = steps["REGISTER_SOURCE"]["result_reference"]
        self.binding_id = steps["BIND_SOURCE"]["result_reference"]

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _git(self, *arguments: str) -> str:
        return subprocess.run(
            ("git", "-C", str(self.repository), *arguments),
            check=True,
            stdout=subprocess.PIPE,
            text=True,
        ).stdout

    def _cli(self, *arguments: str):
        output = StringIO()
        code = main(["--database", str(self.database), *arguments], stdout=output)
        return code, json.loads(output.getvalue())

    @staticmethod
    def _http(application, method: str, path: str, payload: object | None = None):
        body = json.dumps(payload).encode() if payload is not None else b""
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
        return captured["status"], json.loads(response)

    def test_resolve_update_and_query_share_one_durable_runtime(self) -> None:
        resolve_code, receipt = self._cli(
            "resolve-target",
            "--source-id",
            self.source_id,
            "--binding-id",
            self.binding_id,
            "--target-kind",
            "SOURCE_PATH",
            "--revision",
            self.commit,
            "--path",
            "src/service.txt",
        )
        update_code, update = self._cli(
            "update-knowledge",
            "--scope-id",
            self.scope_id,
            "--source-id",
            self.source_id,
            "--binding-id",
            self.binding_id,
            "--target-kind",
            "SOURCE_PATH",
            "--revision",
            self.commit,
            "--path",
            "src/service.txt",
            "--idempotency-key",
            "update-service",
            "--objective",
            "Build exact knowledge for the service file",
            "--actor",
            "test",
            "--correlation-ref",
            "interface-test",
        )
        query_code, assessment = self._cli(
            "query-knowledge",
            "--scope-id",
            self.scope_id,
            "--snapshot-id",
            update["published_snapshot_id"],
            "--idempotency-key",
            "query-service",
            "--request",
            "What handles submitted orders?",
            "--need-id",
            "need:service",
            "--question",
            "What handles submitted orders?",
            "--kinds",
            "FACT",
            "--types",
            "DESCRIBED_AS",
            "--terms",
            "OrderService,submitted orders",
        )
        telemetry_code, telemetry = self._cli(
            "show-telemetry", "--correlation-ref", "interface-test"
        )

        self.assertEqual(resolve_code, 0)
        self.assertEqual(receipt["outcome"], "EXACT")
        self.assertEqual(update_code, 0)
        self.assertEqual(update["state"], "COMPLETED")
        self.assertTrue(update["target_coverage_complete"])
        self.assertEqual(query_code, 0)
        self.assertTrue(assessment["sufficient"])
        self.assertEqual(assessment["items"][0]["status"], "SATISFIED")
        self.assertTrue(assessment["items"][0]["supporting_references"])
        self.assertEqual(telemetry_code, 0)
        self.assertEqual(
            {event["operation"] for event in telemetry["events"]},
            {"local-git.read@1", "knowledge-update@1"},
        )
        self.assertTrue(all(event["cost_status"] == "NOT_ESTIMATED" for event in telemetry["events"]))

    def test_ambiguous_short_revision_cannot_start_update(self) -> None:
        code, result = self._cli(
            "update-knowledge",
            "--scope-id",
            self.scope_id,
            "--source-id",
            self.source_id,
            "--binding-id",
            self.binding_id,
            "--target-kind",
            "SOURCE_PATH",
            "--revision",
            self.commit[:8],
            "--path",
            "src/service.txt",
            "--idempotency-key",
            "short-update",
            "--objective",
            "Must not expand an ambiguous target",
            "--actor",
            "test",
            "--correlation-ref",
            "interface-test",
        )
        self.assertEqual(code, 2)
        self.assertEqual(result["error"], "INVALID_ARGUMENT")

    def test_http_health_and_task_query_use_the_same_runtime(self) -> None:
        _, update = self._cli(
            "update-knowledge",
            "--scope-id",
            self.scope_id,
            "--source-id",
            self.source_id,
            "--binding-id",
            self.binding_id,
            "--target-kind",
            "SOURCE_PATH",
            "--revision",
            self.commit,
            "--path",
            "src/service.txt",
            "--idempotency-key",
            "http-update",
            "--objective",
            "Build knowledge for HTTP query",
            "--actor",
            "test",
            "--correlation-ref",
            "http-test",
        )
        with SqliteDatabase(self.database) as database:
            runtime = ApplicationRuntime(database)
            application = JsonHttpApplication(runtime)
            health_status, health = self._http(application, "GET", "/health")
            query_status, query = self._http(
                application,
                "POST",
                "/v1/tasks/query",
                {
                    "idempotency_key": "http-query",
                    "scope_id": self.scope_id,
                    "snapshot_id": update["published_snapshot_id"],
                    "request": "What handles submitted orders?",
                    "needs": [
                        {
                            "need_id": "need:http",
                            "question": "What handles submitted orders?",
                            "required_kinds": ["FACT"],
                            "required_type_names": [],
                            "required_terms": ["OrderService", "submitted orders"],
                            "minimum_support_count": 1,
                        }
                    ],
                },
            )
            query_events = runtime.telemetry.list_by_correlation("query:http-query")

        self.assertEqual(health_status, "200 OK")
        self.assertEqual(health["mode"], "OFFLINE")
        self.assertFalse(health["live_provider_configured"])
        self.assertEqual(query_status, "200 OK")
        self.assertTrue(query["sufficient"])
        self.assertEqual(len(query_events), 1)
        self.assertEqual(query_events[0].operation, "knowledge-use@1")

    def test_http_rejects_oversized_or_non_json_input(self) -> None:
        with SqliteDatabase(self.database) as database:
            application = JsonHttpApplication(ApplicationRuntime(database), max_request_bytes=4)
            status, result = self._http(application, "POST", "/v1/tasks/query", {"x": "large"})
        self.assertEqual(status, "400 Bad Request")
        self.assertEqual(result["error"], "INVALID_ARGUMENT")

    def test_task_query_without_needs_fails_closed_when_planner_is_inactive(self) -> None:
        with SqliteDatabase(self.database) as database:
            application = JsonHttpApplication(ApplicationRuntime(database))
            status, result = self._http(
                application,
                "POST",
                "/v1/tasks/query",
                {
                    "idempotency_key": "inactive-planner",
                    "scope_id": self.scope_id,
                    "request": "What handles submitted orders?",
                },
            )

        self.assertEqual(status, "503 Service Unavailable")
        self.assertEqual(result["error"], "LIVE_INTEGRATION_HELD")

    def test_reviewed_answer_preparation_fails_closed_when_not_activated(self) -> None:
        with SqliteDatabase(self.database) as database:
            application = JsonHttpApplication(ApplicationRuntime(database))
            status, result = self._http(
                application,
                "POST",
                "/v1/tasks/prepare-answer",
                {
                    "conversation_ref": "conversation:held",
                    "turn_ref": "turn:1",
                    "request_ref": "request:1",
                    "idempotency_key": "held-answer",
                    "scope_id": self.scope_id,
                    "snapshot_id": "snapshot_00000000000000000000000000000001",
                    "request": "What handles submitted orders?",
                    "caller_ref": "user:test",
                },
            )

        self.assertEqual(status, "503 Service Unavailable")
        self.assertEqual(result["error"], "LIVE_INTEGRATION_HELD")

    def test_task_query_can_plan_needs_without_caller_authored_contract(self) -> None:
        _, update = self._cli(
            "update-knowledge",
            "--scope-id",
            self.scope_id,
            "--source-id",
            self.source_id,
            "--binding-id",
            self.binding_id,
            "--target-kind",
            "SOURCE_PATH",
            "--revision",
            self.commit,
            "--path",
            "src/service.txt",
            "--idempotency-key",
            "planned-update",
            "--objective",
            "Build knowledge for a planned task",
            "--actor",
            "test",
            "--correlation-ref",
            "planned-test",
        )
        with SqliteDatabase(self.database) as database:
            runtime = ApplicationRuntime(
                database, requirement_planner=StaticRequirementPlanner()
            )
            application = JsonHttpApplication(runtime)
            capability_status, capabilities = self._http(
                application, "GET", "/v1/capabilities"
            )
            query_status, query = self._http(
                application,
                "POST",
                "/v1/tasks/query",
                {
                    "idempotency_key": "planned-query",
                    "scope_id": self.scope_id,
                    "snapshot_id": update["published_snapshot_id"],
                    "request": "What handles submitted orders?",
                },
            )

        self.assertEqual(capability_status, "200 OK")
        self.assertIn("natural-language-task-planning", capabilities["capabilities"])
        self.assertEqual(query_status, "200 OK")
        self.assertTrue(query["sufficient"])
        self.assertEqual(query["items"][0]["need_id"], "need:planned")


if __name__ == "__main__":
    unittest.main()
