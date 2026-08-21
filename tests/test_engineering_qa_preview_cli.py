from __future__ import annotations

import subprocess
import tempfile
from argparse import Namespace
from datetime import datetime, timedelta, timezone
from pathlib import Path
import unittest
from unittest.mock import patch

from software_world_model.ai_infrastructure.deepseek_chat_adapter import (
    DeepSeekModelConfiguration,
)
from software_world_model.ai_infrastructure.deepseek_chat_conformance import (
    DeepSeekChatConformanceQualification,
)
from software_world_model.application_services.engineering_question_answering import (
    EngineeringQuestionRequest,
)
from software_world_model.application_services.structure_read_bundle import (
    StructureOrderedReadBundle,
    StructureSnapshotBundleReference,
)
from software_world_model.cross_cutting import Digest, DomainError
from software_world_model.infrastructure import SqliteDatabase
from software_world_model.infrastructure.file_structure_read_bundle import (
    FileStructureReadBundleStore,
)
from software_world_model.interface.engineering_qa_preview_cli import (
    _new_database_path,
    _verify_product_candidate,
    engineering_question_preview_subject_digest,
    prepare_engineering_question_preview,
)
from tests import test_engineering_question_answering as qa_fixtures
from tests import test_structure_view as structure_fixtures


def _digest(digit: str) -> Digest:
    return Digest("sha256:" + digit * 64)


class EngineeringQuestionPreviewCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.repository = self.root / "product"
        self.repository.mkdir()
        self.git("init", "-q")
        self.git("config", "user.email", "preview@example.invalid")
        self.git("config", "user.name", "Preview Test")
        (self.repository / "candidate.txt").write_text("exact\n", encoding="utf-8")
        self.git("add", "candidate.txt")
        self.git("commit", "-q", "-m", "candidate")
        self.commit = self.git("rev-parse", "HEAD")
        self.tree = self.git("rev-parse", "HEAD^{tree}")

    def git(self, *arguments: str) -> str:
        return subprocess.run(
            ("git", "-C", str(self.repository), *arguments),
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        ).stdout.strip()

    def test_product_candidate_must_be_clean_and_exact(self):
        self.assertEqual(
            (self.commit, self.tree),
            _verify_product_candidate(
                repository=self.repository,
                expected_commit=self.commit,
                expected_tree=self.tree,
                implementation_path=self.repository / "candidate.txt",
            ),
        )

        (self.repository / "candidate.txt").write_text("dirty\n", encoding="utf-8")
        with self.assertRaises(DomainError):
            _verify_product_candidate(
                repository=self.repository,
                expected_commit=self.commit,
                expected_tree=self.tree,
                implementation_path=self.repository / "candidate.txt",
            )

    def test_preview_subject_binds_candidate_request_bundles_and_provider(self):
        request: EngineeringQuestionRequest = qa_fixtures.request()
        inputs = {
            "product_commit": "a" * 40,
            "product_tree": "b" * 40,
            "request": request,
            "ordered_bundle_digest": _digest("1"),
            "ordered_file_digest": _digest("2"),
            "snapshot_bundle_digests": (_digest("3"),),
            "snapshot_file_digests": (_digest("4"),),
            "provider_binding_digest": _digest("5"),
            "conformance_result_digest": _digest("6"),
        }
        subject = engineering_question_preview_subject_digest(**inputs)
        changed = engineering_question_preview_subject_digest(
            **{**inputs, "product_tree": "c" * 40}
        )

        self.assertNotEqual(subject, changed)
        with self.assertRaises(DomainError):
            engineering_question_preview_subject_digest(
                **{**inputs, "snapshot_file_digests": ()}
            )

    def test_gateway_database_must_be_a_new_canonical_path(self):
        candidate = self.root / "gateway.sqlite3"
        self.assertEqual(candidate, _new_database_path(str(candidate)))

        candidate.write_bytes(b"existing")
        with self.assertRaises(DomainError):
            _new_database_path(str(candidate))

    def test_prepare_wires_exact_bundle_source_provider_and_run_authority(self):
        structure = structure_fixtures.StructureViewTests(methodName="runTest")
        structure.setUp()
        self.addCleanup(structure.doCleanups)
        store = FileStructureReadBundleStore()
        snapshot_paths = (self.root / "a.json", self.root / "b.json")
        stored = tuple(
            store.write_snapshot(str(path), bundle)
            for path, bundle in zip(snapshot_paths, (structure.a[1], structure.b[1]))
        )
        ordered = StructureOrderedReadBundle.create(
            session=structure.session,
            snapshots=tuple(
                StructureSnapshotBundleReference(
                    ordinal=ordinal,
                    snapshot_id=bundle.snapshot_id,
                    snapshot_binding_digest=binding.digest,
                    snapshot_manifest_digest=binding.snapshot_manifest_digest,
                    bundle_digest=bundle.digest,
                    file_digest=stored_bundle.file_digest,
                )
                for ordinal, (binding, bundle, stored_bundle) in enumerate(
                    zip(
                        structure.session.snapshots,
                        (structure.a[1], structure.b[1]),
                        stored,
                    )
                )
            ),
        )
        ordered_path = self.root / "ordered.json"
        store.write_ordered(str(ordered_path), ordered)
        bundle = structure.a[1]
        binding_id = next(
            coverage.root.source_binding_id for coverage in bundle.coverages
        )
        revision = next(
            entity.state.state_payload_fields["source_revision"]
            for entity in bundle.entities
        )
        now = datetime.now(timezone.utc)
        provider = DeepSeekModelConfiguration()
        qualification = DeepSeekChatConformanceQualification(
            result_ref="CC-DEEPSEEK-CHAT-NO-TOOLS-001:" + _digest("7").value,
            result_digest=_digest("7"),
            qualified_model_fingerprints=provider.qualified_model_identities,
            adapter_version=provider.adapter_version,
            provider_configuration_fingerprint=provider.fingerprint,
            valid_until=now + timedelta(days=1),
        )
        source_repository = self.root / "source"
        source_repository.mkdir()
        arguments = Namespace(
            product_repository=str(self.repository),
            product_commit=self.commit,
            product_tree=self.tree,
            repository=str(source_repository),
            repository_id="repository_" + "1" * 32,
            binding_id=binding_id.value,
            repository_revision=revision,
            source_profile_ref="engineering-qa-preview-test:1",
            source_path=["src/main"],
            document_path=["README.md"],
            build_path=["pom.xml"],
            test_path=["src/test"],
            ordered_envelope=str(ordered_path),
            snapshot_bundle=[str(path) for path in snapshot_paths],
            cognition_snapshot_id=bundle.snapshot_id.value,
            question="How does this system compose its modules?",
            response_language="en",
            request_ref="preview-test-request",
            run_ref="preview-test-run",
            authorization_message_digest=_digest("8").value,
            conformance_result=str(self.root / "conformance.json"),
            maximum_dispatches=20,
            authorization_ttl_seconds=3600,
        )

        with (
            SqliteDatabase() as database,
            patch(
                "software_world_model.interface.engineering_qa_preview_cli._verify_product_candidate",
                return_value=(self.commit, self.tree),
            ),
            patch(
                "software_world_model.interface.engineering_qa_preview_cli._exact_source_revision",
                return_value=revision,
            ),
            patch(
                "software_world_model.interface.engineering_qa_preview_cli.load_deepseek_chat_conformance_qualification",
                return_value=qualification,
            ),
        ):
            preview = prepare_engineering_question_preview(
                arguments,
                database=database,
                transport=_NoCallTransport(),
                at=now,
            )

        health = preview.assembly.product.health()
        self.assertTrue(health["external_provider_dispatch"])
        self.assertEqual(preview.request.binding_id, binding_id)
        self.assertEqual(preview.request.repository_revision, revision)
        self.assertEqual(
            preview.run_authorization.request_digest,
            preview.request.digest,
        )
        receipt = preview.launch_receipt(port=55120)
        self.assertEqual(receipt["provider_dispatch_count_at_seal"], 0)
        self.assertEqual(
            receipt["run_authorization"]["authorization_message_digest"],
            arguments.authorization_message_digest,
        )
        self.assertTrue(str(receipt["document_digest"]).startswith("sha256:"))


class _NoCallTransport:
    def post_json(self, **_: object):
        raise AssertionError("preparation must not dispatch a Provider request")


if __name__ == "__main__":
    unittest.main()
