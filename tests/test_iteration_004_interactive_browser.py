from __future__ import annotations

from io import BytesIO
import json
from pathlib import Path
import tempfile
import threading
import unittest

from software_world_model.cross_cutting import canonical_json_bytes
from software_world_model.interface.world_model_browser import PublicRunnerError
from validation.structure_world_model_iteration_004.interactive_browser import (
    AcceptedG3bInteractiveRunner,
    CitationRecord,
    RequestRecord,
    _document_digest,
    _sha256_file,
    _verified_file_reference,
)


RESULT_ID = "structure_view_result_" + "b" * 32


class InteractiveRunnerBoundaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name).resolve()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    @staticmethod
    def _runner_without_startup() -> AcceptedG3bInteractiveRunner:
        runner = object.__new__(AcceptedG3bInteractiveRunner)
        runner._records = {}
        runner._lock = threading.Lock()
        runner._ordinal = 0
        return runner

    def test_dataset_projection_exposes_only_three_fixed_read_sets(self) -> None:
        runner = self._runner_without_startup()
        runner._registry = {
            "selectors": {
                "ORDERED_A_B": {"resolved_snapshot_ids": ["a", "b"]},
                "EXACT_B": {"resolved_snapshot_ids": ["b"]},
                "EXACT_FIXTURE_VALID": {
                    "resolved_snapshot_ids": ["fixture"]
                },
                "METAMORPHIC_A_B": {
                    "resolved_snapshot_ids": ["meta-a", "meta-b"]
                },
            }
        }

        datasets = runner._build_datasets()

        self.assertEqual(
            [item["id"] for item in datasets],
            ["ORDERED_A_B", "EXACT_B", "EXACT_FIXTURE_VALID"],
        )
        self.assertTrue(all(item["read_only"] for item in datasets))
        self.assertNotIn("METAMORPHIC_A_B", [item["id"] for item in datasets])

    def test_request_id_is_reserved_once_without_replay(self) -> None:
        runner = self._runner_without_startup()
        record = RequestRecord("wm-once", "ORDERED_A_B", self.root, {})
        runner._execute = lambda **arguments: (
            {
                "request_id": arguments["request_id"],
                "mode": "WORLD_MODEL",
            },
            record,
        )

        first = runner.ask(
            request_id="wm-once",
            dataset_id="ORDERED_A_B",
            question="new question",
        )

        self.assertEqual(first["mode"], "WORLD_MODEL")
        with self.assertRaises(PublicRunnerError) as caught:
            runner.ask(
                request_id="wm-once",
                dataset_id="ORDERED_A_B",
                question="new question",
            )
        self.assertEqual(caught.exception.code, "REQUEST_ID_CONFLICT")

    def test_citation_get_reverifies_projection_and_request_binding(self) -> None:
        projection = {
            "schema": "swm.iter-003.g3b-citation-projection@1",
            "status": "PASS",
            "environment": "EVALUATION_ONLY",
            "production_activation": "NOT_EXECUTED",
            "network_operation_count": 0,
            "answer_return_port": False,
            "result_id": RESULT_ID,
            "seal_digest": "sha256:" + "c" * 64,
            "citation_projection": {"citations": []},
        }
        path = self.root / "projection.json"
        path.write_bytes(canonical_json_bytes(projection))
        citation = CitationRecord(
            result_id=RESULT_ID,
            seal_digest=projection["seal_digest"],
            projection_path=path,
            projection_digest=_sha256_file(path),
        )
        runner = self._runner_without_startup()
        runner._records["wm-citation"] = RequestRecord(
            "wm-citation", "ORDERED_A_B", self.root, {RESULT_ID: citation}
        )

        value = runner.citation(
            request_id="wm-citation", result_id=RESULT_ID
        )

        self.assertEqual(value["result_id"], RESULT_ID)
        self.assertEqual(value["environment"], "EVALUATION_ONLY")
        self.assertEqual(value["network_operation_count"], 0)
        with self.assertRaises(PublicRunnerError) as wrong_request:
            runner.citation(request_id="wm-other", result_id=RESULT_ID)
        self.assertEqual(wrong_request.exception.code, "RESULT_NOT_FOUND")

        with path.open("ab") as stream:
            stream.write(b"tamper")
        with self.assertRaises(PublicRunnerError) as tampered:
            runner.citation(request_id="wm-citation", result_id=RESULT_ID)
        self.assertEqual(tampered.exception.code, "CITATION_VERIFICATION_FAILED")

    def test_file_reference_must_be_exact_digest_and_stay_under_run_root(self) -> None:
        inside = self.root / "run"
        inside.mkdir()
        file = inside / "summary.json"
        file.write_bytes(b"{}")
        reference = {
            "path": str(file),
            "digest": _sha256_file(file),
            "size": 2,
        }

        self.assertEqual(_verified_file_reference(reference, inside), file)
        with self.assertRaises(ValueError):
            _verified_file_reference({**reference, "digest": "sha256:" + "0" * 64}, inside)
        with self.assertRaises(ValueError):
            _verified_file_reference(reference, self.root / "other")

    def test_document_digest_excludes_only_its_digest_field(self) -> None:
        value = {"schema": "example@1", "status": "PASS"}
        digest = _document_digest(value)
        with_digest = {**value, "document_digest": digest}

        self.assertEqual(_document_digest(with_digest), digest)
        self.assertTrue(digest.startswith("sha256:"))


if __name__ == "__main__":
    unittest.main()
