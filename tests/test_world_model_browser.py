from __future__ import annotations

from io import BytesIO
import json
import unittest

from software_world_model.interface.world_model_browser import (
    PublicRunnerError,
    WorldModelBrowserApplication,
)


RESULT_ID = "structure_view_result_" + "a" * 32


class RecordingRunner:
    def __init__(self) -> None:
        self.ask_arguments = None
        self.citation_arguments = None
        self.fail = False

    def health(self):
        return {
            "status": "ready",
            "mode": "WORLD_MODEL",
            "environment": "EVALUATION_ONLY",
            "accepted_product_commit": "b" * 40,
            "production_activation": "NOT_EXECUTED",
        }

    def datasets(self):
        return (
            {
                "id": "ORDERED_A_B",
                "label": "A/B",
                "snapshot_count": 2,
                "snapshot_ids": ["snapshot-a", "snapshot-b"],
                "read_only": True,
            },
        )

    def ask(self, *, request_id, dataset_id, question):
        if self.fail:
            raise PublicRunnerError("RUN_BLOCKED", "sealed run failed")
        self.ask_arguments = (request_id, dataset_id, question)
        return {
            "request_id": request_id,
            "dataset_id": dataset_id,
            "question": question,
            "mode": "WORLD_MODEL",
            "environment": "EVALUATION_ONLY",
            "page": {"answer": {"body": "verified"}},
            "citations": [
                {
                    "result_id": RESULT_ID,
                    "url": f"/v1/world-model/requests/{request_id}/citations/{RESULT_ID}",
                }
            ],
            "production_activation": "NOT_EXECUTED",
        }

    def citation(self, *, request_id, result_id):
        self.citation_arguments = (request_id, result_id)
        return {
            "request_id": request_id,
            "result_id": result_id,
            "citation_projection": {"citations": []},
            "network_operation_count": 0,
        }


class WorldModelBrowserTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = RecordingRunner()
        self.application = WorldModelBrowserApplication(self.runner)

    @staticmethod
    def _http(
        application,
        method: str,
        path: str,
        payload=None,
        *,
        raw: bytes | None = None,
        content_type: str | None = None,
    ):
        body = (
            raw
            if raw is not None
            else json.dumps(payload).encode("utf-8")
            if payload is not None
            else b""
        )
        captured = {}

        def start_response(status, headers):
            captured["status"] = status
            captured["headers"] = dict(headers)

        response = b"".join(
            application(
                {
                    "REQUEST_METHOD": method,
                    "PATH_INFO": path,
                    "CONTENT_TYPE": (
                        content_type
                        if content_type is not None
                        else "application/json"
                        if payload is not None or raw is not None
                        else ""
                    ),
                    "CONTENT_LENGTH": str(len(body)),
                    "wsgi.input": BytesIO(body),
                },
                start_response,
            )
        )
        return captured["status"], captured["headers"], response

    def test_page_is_explicit_world_model_evaluation_surface(self) -> None:
        status, headers, raw = self._http(self.application, "GET", "/")
        script_status, _, script = self._http(
            self.application, "GET", "/assets/world-model.js"
        )
        html = raw.decode("utf-8")
        javascript = script.decode("utf-8")

        self.assertEqual(status, "200 OK")
        self.assertEqual(script_status, "200 OK")
        self.assertEqual(headers["X-Frame-Options"], "DENY")
        self.assertIn("default-src 'self'", headers["Content-Security-Policy"])
        self.assertIn("WORLD_MODEL", html)
        self.assertIn("EVALUATION_ONLY", html)
        self.assertIn("自由提问", html)
        self.assertIn("Plan → Draft → Review · 3 次模型调用", html)
        self.assertNotIn("1 次模型调用", html)
        self.assertNotIn("repository_path", html)
        self.assertIn("/v1/world-model/questions", javascript)
        self.assertNotIn("/v1/browser/chat", javascript)
        self.assertNotIn("repository_path", javascript)

    def test_long_dynamic_read_set_identities_cannot_expand_grid_tracks(
        self,
    ) -> None:
        status, _, raw = self._http(
            self.application, "GET", "/assets/world-model.css"
        )
        stylesheet = raw.decode("utf-8")

        self.assertEqual(status, "200 OK")
        self.assertIn(
            ".dataset-grid{grid-template-columns:repeat(3,minmax(0,1fr))}",
            stylesheet,
        )
        self.assertIn(".dataset{min-width:0}", stylesheet)
        self.assertIn(
            ".dataset strong,.dataset small,.dataset span{overflow-wrap:anywhere}",
            stylesheet,
        )

    def test_health_and_datasets_keep_mode_and_allowlist_visible(self) -> None:
        health_status, _, health_raw = self._http(
            self.application, "GET", "/health"
        )
        datasets_status, _, datasets_raw = self._http(
            self.application, "GET", "/v1/world-model/datasets"
        )
        health = json.loads(health_raw)
        datasets = json.loads(datasets_raw)

        self.assertEqual(health_status, "200 OK")
        self.assertEqual(health["mode"], "WORLD_MODEL")
        self.assertEqual(health["environment"], "EVALUATION_ONLY")
        self.assertEqual(datasets_status, "200 OK")
        self.assertEqual(datasets["mode"], "WORLD_MODEL")
        self.assertEqual(
            [item["id"] for item in datasets["datasets"]], ["ORDERED_A_B"]
        )

    def test_question_routes_only_to_injected_world_model_runner(self) -> None:
        payload = {
            "request_id": "wm-request-1",
            "dataset_id": "ORDERED_A_B",
            "question": "B 比 A 多了哪个 reactor 模块？",
        }
        status, headers, raw = self._http(
            self.application, "POST", "/v1/world-model/questions", payload
        )
        value = json.loads(raw)

        self.assertEqual(status, "200 OK")
        self.assertEqual(headers["Cache-Control"], "no-store")
        self.assertEqual(
            self.runner.ask_arguments,
            ("wm-request-1", "ORDERED_A_B", payload["question"]),
        )
        self.assertEqual(value["mode"], "WORLD_MODEL")
        self.assertEqual(value["environment"], "EVALUATION_ONLY")
        self.assertEqual(value["page"]["answer"]["body"], "verified")

    def test_citation_is_a_separate_request_and_result_bound_get(self) -> None:
        path = f"/v1/world-model/requests/wm-request-1/citations/{RESULT_ID}"
        status, _, raw = self._http(self.application, "GET", path)

        self.assertEqual(status, "200 OK")
        self.assertEqual(
            self.runner.citation_arguments, ("wm-request-1", RESULT_ID)
        )
        self.assertEqual(json.loads(raw)["network_operation_count"], 0)

        invalid_status, _, _ = self._http(
            self.application,
            "GET",
            "/v1/world-model/requests/wm-request-1/citations/not-a-result",
        )
        self.assertEqual(invalid_status, "400 Bad Request")

    def test_input_contract_rejects_extra_duplicate_and_oversized_fields(self) -> None:
        extra_status, _, _ = self._http(
            self.application,
            "POST",
            "/v1/world-model/questions",
            {
                "request_id": "wm-1",
                "dataset_id": "ORDERED_A_B",
                "question": "question",
                "repository_path": "/tmp/project",
            },
        )
        duplicate_status, _, _ = self._http(
            self.application,
            "POST",
            "/v1/world-model/questions",
            raw=b'{"request_id":"a","request_id":"b","dataset_id":"ORDERED_A_B","question":"q"}',
        )
        long_status, _, _ = self._http(
            self.application,
            "POST",
            "/v1/world-model/questions",
            {
                "request_id": "wm-2",
                "dataset_id": "ORDERED_A_B",
                "question": "x" * 8_001,
            },
        )

        self.assertEqual(extra_status, "400 Bad Request")
        self.assertEqual(duplicate_status, "400 Bad Request")
        self.assertEqual(long_status, "400 Bad Request")
        self.assertIsNone(self.runner.ask_arguments)

    def test_runner_failure_is_public_but_fail_closed(self) -> None:
        self.runner.fail = True
        status, _, raw = self._http(
            self.application,
            "POST",
            "/v1/world-model/questions",
            {
                "request_id": "wm-failure",
                "dataset_id": "ORDERED_A_B",
                "question": "question",
            },
        )
        value = json.loads(raw)

        self.assertEqual(status, "502 Bad Gateway")
        self.assertEqual(value["error"], "RUN_BLOCKED")
        self.assertEqual(value["message"], "sealed run failed")


if __name__ == "__main__":
    unittest.main()
