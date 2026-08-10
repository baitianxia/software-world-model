from __future__ import annotations

from dataclasses import replace
from io import StringIO
import json
import os
from pathlib import Path
import tempfile
import unittest

from software_world_model.application_services.citation_projection import (
    CitationEvidenceReference,
    CitationObservation,
    CitationObservationBroker,
    CitationProjector,
    CitationStoreSnapshot,
    StructureViewResultSeal,
)
from software_world_model.cross_cutting import (
    Digest,
    DomainError,
    ErrorCode,
    StableId,
    canonical_json_bytes,
    digest_of,
)
from software_world_model.infrastructure.file_citation_observation_store import (
    FileCitationObservationStoreReader,
    FileCitationObservationStoreWriter,
    load_structure_view_result_seal,
    structure_view_result_seal_payload,
)
from software_world_model.interface.citation_projector_cli import main
from software_world_model.knowledge_engine.structure import StructureEvidence
from software_world_model.knowledge_engine.structure_publication import (
    StructureEvidenceMetadata,
)


class _KnowledgeOwner:
    def __init__(self, evidence: tuple[StructureEvidence, ...]) -> None:
        self.values = {item.evidence_id: item for item in evidence}
        self.calls: list[StableId] = []

    def get_evidence(self, evidence_id: StableId) -> StructureEvidence:
        self.calls.append(evidence_id)
        try:
            return self.values[evidence_id]
        except KeyError as exc:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "Evidence is not owned",
                {"reason_code": "TEST_EVIDENCE_UNKNOWN"},
            ) from exc


class _FixedReader:
    def __init__(self, snapshot: CitationStoreSnapshot) -> None:
        self.snapshot = snapshot

    def read_exact(self, _result: StructureViewResultSeal) -> CitationStoreSnapshot:
        return self.snapshot


class CitationProjectorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary.name).resolve()
        self.evidence = (
            self._evidence("a", "<project>alpha</project>"),
            self._evidence("b", "<dependency>beta</dependency>"),
        )
        self.owner = _KnowledgeOwner(self.evidence)
        references = tuple(
            sorted(
                (
                    CitationEvidenceReference.from_metadata(
                        StructureEvidenceMetadata.from_evidence(item)
                    )
                    for item in self.evidence
                ),
                key=lambda item: item.evidence_id.value,
            )
        )
        self.result = StructureViewResultSeal.seal(
            result_id=StableId("structure_view_result_" + "1" * 32),
            view_digest=digest_of({"structure_view": "fixture"}),
            evidence_allowlist=references,
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    @staticmethod
    def _evidence(marker: str, excerpt: str) -> StructureEvidence:
        encoded = excerpt.encode("utf-8")
        return StructureEvidence.create(
            artifact_id=StableId("source_artifact_" + marker * 32),
            source_context_id=StableId("source_context_" + marker * 32),
            byte_start=7,
            byte_end=7 + len(encoded),
            locator=f"{marker}/pom.xml:1",
            excerpt=excerpt,
            artifact_content_digest=digest_of(
                {"artifact": marker, "content": excerpt}
            ),
        )

    def _materialize(
        self,
        name: str,
        *,
        result: StructureViewResultSeal | None = None,
        owner: _KnowledgeOwner | None = None,
    ) -> FileCitationObservationStoreReader:
        active_result = result or self.result
        writer = FileCitationObservationStoreWriter(self.base / name)
        active_owner = owner or self.owner
        observations = tuple(
            CitationObservation.from_evidence(
                active_owner.get_evidence(reference.evidence_id)
            )
            for reference in active_result.evidence_allowlist
        )
        receipt = writer.create_disposable_store(
            result=active_result,
            observations=observations,
        )
        self.assertEqual(receipt.result_digest, active_result.digest)
        return FileCitationObservationStoreReader(writer.root)

    def _write_result(
        self,
        name: str = "result.json",
        *,
        result: StructureViewResultSeal | None = None,
    ) -> Path:
        path = self.base / name
        path.write_bytes(
            canonical_json_bytes(
                structure_view_result_seal_payload(result or self.result)
            )
        )
        return path

    def test_store_materializes_exact_allowlist_and_cli_projects_display(self) -> None:
        store = self._materialize("store")
        self.assertEqual(
            tuple(self.owner.calls),
            tuple(item.evidence_id for item in self.result.evidence_allowlist),
        )

        projection = CitationProjector(store).project(self.result)
        self.assertEqual(
            tuple(item.evidence_id for item in projection.citations),
            tuple(item.evidence_id for item in self.result.evidence_allowlist),
        )
        expected_by_id = {item.evidence_id: item for item in self.evidence}
        self.assertEqual(
            tuple(item.observation for item in projection.citations),
            tuple(
                expected_by_id[item.evidence_id].excerpt
                for item in self.result.evidence_allowlist
            ),
        )

        result_path = self._write_result()
        stdout = StringIO()
        stderr = StringIO()
        exit_code = main(
            ["--sealed-result", str(result_path), "--store", str(store.root)],
            stdout=stdout,
            stderr=stderr,
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr.getvalue(), "")
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["result_digest"], self.result.digest.value)
        self.assertEqual(len(payload["citations"]), 2)
        self.assertEqual(
            {item["observation"] for item in payload["citations"]},
            {item.excerpt for item in self.evidence},
        )

        projector = CitationProjector(store)
        self.assertFalse(hasattr(store, "create_disposable_store"))
        for forbidden in (
            "query",
            "update",
            "model",
            "network",
            "answer",
            "return_answer",
            "get_evidence",
        ):
            self.assertFalse(hasattr(projector, forbidden))
        self.assertEqual(set(vars(projector)), {"_store"})

    def test_seal_rejects_duplicate_and_noncanonical_allowlists(self) -> None:
        first, second = self.result.evidence_allowlist
        with self.assertRaises(DomainError) as duplicate:
            StructureViewResultSeal.seal(
                result_id=self.result.result_id,
                view_digest=self.result.view_digest,
                evidence_allowlist=(first, first),
            )
        self.assertEqual(
            duplicate.exception.details["reason_code"],
            "CITATION_ALLOWLIST_DUPLICATE",
        )

        with self.assertRaises(DomainError) as order:
            StructureViewResultSeal.seal(
                result_id=self.result.result_id,
                view_digest=self.result.view_digest,
                evidence_allowlist=(second, first),
            )
        self.assertEqual(
            order.exception.details["reason_code"],
            "CITATION_ALLOWLIST_NONCANONICAL_ORDER",
        )

    def test_broker_rejects_a_self_attested_seal_without_actual_view_result(self) -> None:
        with self.assertRaises(DomainError) as rejected:
            CitationObservationBroker(
                self.owner,
                FileCitationObservationStoreWriter(self.base / "forged-seal"),
            ).materialize(self.result)
        self.assertEqual(
            rejected.exception.details["reason_code"],
            "CITATION_VIEW_RESULT_REQUIRED",
        )
        self.assertFalse((self.base / "forged-seal").exists())

    def test_projector_rejects_missing_extra_and_tampered_observation_files(self) -> None:
        store = self._materialize("missing")
        first_name = f"{self.result.evidence_allowlist[0].evidence_id.value}.json"
        (store.root / "observations" / first_name).unlink()
        with self.assertRaises(DomainError) as missing:
            CitationProjector(store).project(self.result)
        self.assertEqual(
            missing.exception.details["reason_code"],
            "CITATION_STORE_OBSERVATION_FILES_MISMATCH",
        )

        store = self._materialize("extra")
        (store.root / "observations" / "unknown.json").write_bytes(b"{}")
        with self.assertRaises(DomainError) as extra:
            CitationProjector(store).project(self.result)
        self.assertEqual(
            extra.exception.details["reason_code"],
            "CITATION_STORE_OBSERVATION_FILES_MISMATCH",
        )

        store = self._materialize("tampered")
        observation_path = store.root / "observations" / first_name
        payload = json.loads(observation_path.read_text(encoding="utf-8"))
        payload["excerpt"] = "x" * len(payload["excerpt"].encode("utf-8"))
        observation_path.write_bytes(canonical_json_bytes(payload))
        with self.assertRaises(DomainError) as tampered:
            CitationProjector(store).project(self.result)
        self.assertEqual(
            tampered.exception.details["reason_code"],
            "CITATION_STORE_FILE_DIGEST_MISMATCH",
        )

    def test_store_rejects_duplicate_unknown_and_noncanonical_json(self) -> None:
        store = self._materialize("manifest-duplicate")
        manifest_path = store.root / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["entries"].append(manifest["entries"][0])
        manifest["observation_count"] += 1
        manifest_path.write_bytes(canonical_json_bytes(manifest))
        with self.assertRaises(DomainError) as duplicate:
            CitationProjector(store).project(self.result)
        self.assertEqual(
            duplicate.exception.details["reason_code"],
            "CITATION_STORE_DUPLICATE_EVIDENCE",
        )

        result_path = self._write_result("unknown-field.json")
        result_payload = json.loads(result_path.read_text(encoding="utf-8"))
        result_payload["unknown"] = "forbidden"
        result_path.write_bytes(canonical_json_bytes(result_payload))
        with self.assertRaises(DomainError) as unknown:
            load_structure_view_result_seal(result_path)
        self.assertEqual(
            unknown.exception.details["reason_code"],
            "CITATION_JSON_FIELDS_INVALID",
        )

        noncanonical_path = self._write_result("noncanonical.json")
        noncanonical_path.write_text(
            json.dumps(
                structure_view_result_seal_payload(self.result),
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        with self.assertRaises(DomainError) as noncanonical:
            load_structure_view_result_seal(noncanonical_path)
        self.assertEqual(
            noncanonical.exception.details["reason_code"],
            "CITATION_JSON_NONCANONICAL",
        )

        duplicate_key_path = self.base / "duplicate-key.json"
        duplicate_key_path.write_bytes(b'{"format_ref":"x","format_ref":"y"}')
        with self.assertRaises(DomainError) as duplicate_key:
            load_structure_view_result_seal(duplicate_key_path)
        self.assertEqual(
            duplicate_key.exception.details["reason_code"],
            "CITATION_JSON_INVALID",
        )

    def test_store_rejects_path_traversal_and_symlinks(self) -> None:
        store = self._materialize("traversal")
        manifest_path = store.root / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["entries"][0]["path"] = "observations/../outside.json"
        manifest_path.write_bytes(canonical_json_bytes(manifest))
        with self.assertRaises(DomainError) as traversal:
            CitationProjector(store).project(self.result)
        self.assertEqual(
            traversal.exception.details["reason_code"],
            "CITATION_STORE_PATH_TRAVERSAL",
        )

        store = self._materialize("file-symlink")
        first_name = f"{self.result.evidence_allowlist[0].evidence_id.value}.json"
        observation_path = store.root / "observations" / first_name
        outside = self.base / "outside.json"
        outside.write_bytes(observation_path.read_bytes())
        observation_path.unlink()
        observation_path.symlink_to(outside)
        with self.assertRaises(DomainError) as file_symlink:
            CitationProjector(store).project(self.result)
        self.assertEqual(
            file_symlink.exception.details["reason_code"],
            "CITATION_FILE_UNAVAILABLE",
        )

        store = self._materialize("root-real")
        root_link = self.base / "root-link"
        root_link.symlink_to(store.root, target_is_directory=True)
        with self.assertRaises(DomainError) as root_symlink:
            CitationProjector(FileCitationObservationStoreReader(root_link)).project(
                self.result
            )
        self.assertEqual(
            root_symlink.exception.details["reason_code"],
            "CITATION_DIRECTORY_UNSAFE",
        )

        result_path = self._write_result("result-real.json")
        result_link = self.base / "result-link.json"
        result_link.symlink_to(result_path)
        with self.assertRaises(DomainError) as result_symlink:
            load_structure_view_result_seal(result_link)
        self.assertEqual(
            result_symlink.exception.details["reason_code"],
            "CITATION_FILE_UNAVAILABLE",
        )

        with self.assertRaises(DomainError) as lexical_traversal:
            FileCitationObservationStoreReader(
                os.fspath(self.base / "child" / ".." / "store")
            )
        self.assertEqual(
            lexical_traversal.exception.details["reason_code"],
            "CITATION_PATH_NONCANONICAL",
        )

    def test_projector_rejects_other_result_and_typed_duplicate_snapshot(self) -> None:
        store = self._materialize("bound-result")
        other = StructureViewResultSeal.seal(
            result_id=StableId("structure_view_result_" + "3" * 32),
            view_digest=digest_of({"view": "other"}),
            evidence_allowlist=self.result.evidence_allowlist,
        )
        with self.assertRaises(DomainError) as wrong_result:
            CitationProjector(store).project(other)
        self.assertEqual(
            wrong_result.exception.details["reason_code"],
            "CITATION_STORE_RESULT_MISMATCH",
        )

        valid_snapshot = store.read_exact(self.result)
        duplicated = CitationStoreSnapshot(
            valid_snapshot.receipt,
            (
                valid_snapshot.observations[0],
                valid_snapshot.observations[0],
            ),
        )
        with self.assertRaises(DomainError) as duplicate:
            CitationProjector(_FixedReader(duplicated)).project(self.result)
        self.assertEqual(
            duplicate.exception.details["reason_code"],
            "CITATION_STORE_ALLOWLIST_MISMATCH",
        )

    def test_tampered_reference_and_seal_digest_are_rejected(self) -> None:
        reference = self.result.evidence_allowlist[0]
        with self.assertRaises(DomainError) as reference_tamper:
            replace(
                reference,
                locator="forged/pom.xml:1",
            ).require_valid()
        self.assertEqual(
            reference_tamper.exception.details["reason_code"],
            "CITATION_EVIDENCE_REFERENCE_NONCANONICAL",
        )

        tampered_result = replace(
            self.result,
            view_digest=Digest("sha256:" + "f" * 64),
        )
        with self.assertRaises(DomainError) as result_tamper:
            tampered_result.require_valid()
        self.assertEqual(
            result_tamper.exception.details["reason_code"],
            "CITATION_RESULT_SEAL_DIGEST_MISMATCH",
        )


if __name__ == "__main__":
    unittest.main()
