from __future__ import annotations

import json
import os
import subprocess
import tempfile
import tomllib
from datetime import datetime, timedelta, timezone
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from software_world_model.ai_infrastructure.deepseek_chat_adapter import (
    DeepSeekModelConfiguration,
)
from software_world_model.ai_infrastructure.deepseek_chat_conformance import (
    DeepSeekChatConformanceQualification,
)
from software_world_model.application_services.structure_read_bundle import (
    StructureOrderedReadBundle,
    StructureSnapshotBundleReference,
)
from software_world_model.cross_cutting import Digest, DomainError, canonical_json_bytes
from software_world_model.infrastructure import SqliteDatabase
from software_world_model.infrastructure.file_structure_read_bundle import (
    FileStructureReadBundleStore,
)
from software_world_model.interface.engineering_qa_alpha_cli import (
    ENGINEERING_QA_ALPHA_PORT,
    ENGINEERING_QA_ALPHA_SESSION_CONFIG_SCHEMA,
    build_parser,
    engineering_question_alpha_subject_digest,
    load_engineering_question_alpha_session_config,
    main,
    prepare_engineering_question_alpha,
)

from tests import test_structure_view as structure_fixtures


def _digest(digit: str) -> Digest:
    return Digest("sha256:" + digit * 64)


class EngineeringQuestionAlphaCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.product_repository = self.root / "product"
        self.product_repository.mkdir()
        self.git("init", "-q")
        self.git("config", "user.email", "alpha@example.invalid")
        self.git("config", "user.name", "Alpha Test")
        (self.product_repository / "candidate.txt").write_text(
            "exact\n", encoding="utf-8"
        )
        self.git("add", "candidate.txt")
        self.git("commit", "-q", "-m", "candidate")
        self.commit = self.git("rev-parse", "HEAD")
        self.tree = self.git("rev-parse", "HEAD^{tree}")

    def git(self, *arguments: str) -> str:
        return subprocess.run(
            ("git", "-C", str(self.product_repository), *arguments),
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        ).stdout.strip()

    def base_document(self) -> dict[str, object]:
        now = datetime.now(timezone.utc).replace(microsecond=0)
        return {
            "schema": ENGINEERING_QA_ALPHA_SESSION_CONFIG_SCHEMA,
            "product_repository": str(self.product_repository),
            "product_commit": self.commit,
            "product_tree": self.tree,
            "repository": str(self.root / "source"),
            "repository_id": "repository_" + "1" * 32,
            "binding_id": "binding_" + "2" * 32,
            "repository_revision": "3" * 40,
            "source_profile_ref": "engineering-qa-alpha-test:1",
            "source_paths": ["src/main/java"],
            "document_paths": ["README.md"],
            "build_paths": ["pom.xml"],
            "test_paths": ["src/test/java"],
            "excluded_source_paths": ["src/main/resources"],
            "ordered_envelope": str(self.root / "ordered.json"),
            "snapshot_bundles": [str(self.root / "snapshot.json")],
            "cognition_snapshot_id": None,
            "response_language": "zh-CN",
            "session_ref": "engineering-qa-alpha-test",
            "authorization_message_digest": _digest("8").value,
            "authorized_at": (now - timedelta(minutes=1))
            .isoformat()
            .replace("+00:00", "Z"),
            "expires_at": (now + timedelta(hours=1))
            .isoformat()
            .replace("+00:00", "Z"),
            "conformance_result": str(self.root / "conformance.json"),
            "gateway_database": str(self.root / "gateway.sqlite3"),
            "launch_receipt": str(self.root / "launch.json"),
            "terminal_receipt": str(self.root / "terminal.json"),
            "maximum_questions": 3,
            "maximum_dispatches_per_question": 4,
            "maximum_total_dispatches": 12,
            "known_limitations": [
                "Alpha evaluation only",
                "src/main/resources is excluded",
            ],
        }

    def write_config(
        self,
        document: dict[str, object],
        *,
        name: str = "session.json",
    ) -> Path:
        path = self.root / name
        path.write_bytes(canonical_json_bytes(document) + b"\n")
        os.chmod(path, 0o600)
        return path

    def test_parser_exposes_only_the_frozen_session_config(self):
        parser = build_parser()
        self.assertEqual(parser.prog, "swm-engineering-qa-evaluation")
        destinations = {
            action.dest for action in parser._actions if action.dest != "help"
        }
        self.assertEqual(destinations, {"session_config"})

    def test_distribution_command_selects_the_sustained_alpha(self):
        project = tomllib.loads(
            (Path(__file__).parents[1] / "pyproject.toml").read_text(
                encoding="utf-8"
            )
        )
        scripts = project["project"]["scripts"]
        self.assertEqual(
            scripts["swm-engineering-qa-evaluation"],
            "software_world_model.interface.engineering_qa_alpha_cli:main",
        )
        self.assertEqual(
            scripts["swm-engineering-qa-preview-evaluation"],
            "software_world_model.interface.engineering_qa_preview_cli:main",
        )

    def test_config_is_private_closed_unique_key_json(self):
        path = self.write_config(self.base_document())
        loaded = load_engineering_question_alpha_session_config(path)
        self.assertEqual(loaded.maximum_questions, 3)
        self.assertEqual(loaded.excluded_source_paths, ("src/main/resources",))

        unknown = self.write_config(
            {**self.base_document(), "question": "client authority is forbidden"},
            name="unknown.json",
        )
        with self.assertRaises(DomainError):
            load_engineering_question_alpha_session_config(unknown)

        duplicate = self.root / "duplicate.json"
        duplicate.write_text('{"schema":"a","schema":"b"}', encoding="utf-8")
        os.chmod(duplicate, 0o600)
        with self.assertRaises(DomainError):
            load_engineering_question_alpha_session_config(duplicate)

        os.chmod(path, 0o644)
        with self.assertRaises(DomainError):
            load_engineering_question_alpha_session_config(path)

    def test_alpha_subject_binds_template_bundles_provider_and_config_file(self):
        inputs = {
            "product_commit": "a" * 40,
            "product_tree": "b" * 40,
            "request_template_digest": _digest("1"),
            "ordered_bundle_digest": _digest("2"),
            "ordered_file_digest": _digest("3"),
            "snapshot_bundle_digests": (_digest("4"),),
            "snapshot_file_digests": (_digest("5"),),
            "provider_binding_digest": _digest("6"),
            "conformance_result_digest": _digest("7"),
            "session_config_file_digest": _digest("8"),
        }
        subject = engineering_question_alpha_subject_digest(**inputs)
        changed = engineering_question_alpha_subject_digest(
            **{**inputs, "session_config_file_digest": _digest("9")}
        )

        self.assertNotEqual(subject, changed)
        with self.assertRaises(DomainError):
            engineering_question_alpha_subject_digest(
                **{**inputs, "snapshot_file_digests": ()}
            )

    def test_main_seals_launch_before_serving_and_terminal_after_stop(self):
        events = []
        session_config = SimpleNamespace(
            path=self.root / "session.json",
            gateway_database=str(self.root / "gateway.sqlite3"),
            launch_receipt=str(self.root / "launch.json"),
            terminal_receipt=str(self.root / "terminal.json"),
        )
        application = object()
        prepared = SimpleNamespace(
            assembly=SimpleNamespace(
                application=application,
                execution_factory=SimpleNamespace(transports=()),
            ),
            public_status=lambda: {"status": "READY"},
            launch_receipt=lambda: {"schema": "launch"},
            terminal_receipt=lambda: {"schema": "terminal"},
        )

        class FakeDatabase:
            def __enter__(self):
                return self

            def __exit__(self, *_):
                return False

        class FakeServer:
            server_port = ENGINEERING_QA_ALPHA_PORT

            def __enter__(self):
                return self

            def __exit__(self, *_):
                return False

            def serve_forever(self):
                events.append("serve")

        def write_receipt(path, value):
            events.append(("write", path.name, value["schema"]))

        stdout = StringIO()
        stderr = StringIO()
        with (
            patch(
                "software_world_model.interface.engineering_qa_alpha_cli.load_engineering_question_alpha_session_config",
                return_value=session_config,
            ),
            patch(
                "software_world_model.interface.engineering_qa_alpha_cli._new_database_path",
                return_value=self.root / "gateway.sqlite3",
            ),
            patch(
                "software_world_model.interface.engineering_qa_alpha_cli._new_private_output_path",
                side_effect=(self.root / "launch.json", self.root / "terminal.json"),
            ),
            patch(
                "software_world_model.interface.engineering_qa_alpha_cli.SqliteDatabase",
                return_value=FakeDatabase(),
            ),
            patch(
                "software_world_model.interface.engineering_qa_alpha_cli.prepare_engineering_question_alpha",
                return_value=prepared,
            ),
            patch(
                "software_world_model.interface.engineering_qa_alpha_cli.make_server",
                return_value=FakeServer(),
            ) as make_server,
            patch(
                "software_world_model.interface.engineering_qa_alpha_cli._write_new_private_json",
                side_effect=write_receipt,
            ),
        ):
            status = main(
                ["--session-config", str(session_config.path)],
                stdout=stdout,
                stderr=stderr,
            )

        self.assertEqual(status, 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(
            os.stat(self.root / "gateway.sqlite3").st_mode & 0o777,
            0o600,
        )
        self.assertIn('"status":"READY"', stdout.getvalue())
        self.assertEqual(
            events,
            [
                ("write", "launch.json", "launch"),
                "serve",
                ("write", "terminal.json", "terminal"),
            ],
        )
        self.assertEqual(make_server.call_args.args[:3], (
            "127.0.0.1",
            ENGINEERING_QA_ALPHA_PORT,
            application,
        ))

    def test_prepare_freezes_session_without_transport_or_dispatch(self):
        structure = structure_fixtures.StructureViewTests(methodName="runTest")
        structure.setUp()
        self.addCleanup(structure.doCleanups)
        store = FileStructureReadBundleStore()
        snapshot_paths = (self.root / "a.json", self.root / "b.json")
        stored = tuple(
            store.write_snapshot(str(path), bundle)
            for path, bundle in zip(
                snapshot_paths,
                (structure.a[1], structure.b[1]),
            )
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
        source_repository = self.root / "source"
        source_repository.mkdir()
        conformance_path = self.root / "conformance.json"
        conformance_path.write_text("{}\n", encoding="utf-8")
        now = datetime.now(timezone.utc).replace(microsecond=0)
        provider = DeepSeekModelConfiguration()
        qualification = DeepSeekChatConformanceQualification(
            result_ref="CC-DEEPSEEK-CHAT-NO-TOOLS-001:" + _digest("7").value,
            result_digest=_digest("7"),
            qualified_model_fingerprints=provider.qualified_model_identities,
            adapter_version=provider.adapter_version,
            provider_configuration_fingerprint=provider.fingerprint,
            valid_until=now + timedelta(days=1),
        )
        document = {
            **self.base_document(),
            "repository": str(source_repository),
            "binding_id": binding_id.value,
            "repository_revision": revision,
            "ordered_envelope": str(ordered_path),
            "snapshot_bundles": [str(path) for path in snapshot_paths],
            "cognition_snapshot_id": bundle.snapshot_id.value,
            "conformance_result": str(conformance_path),
            "authorized_at": (now - timedelta(minutes=1))
            .isoformat()
            .replace("+00:00", "Z"),
            "expires_at": (now + timedelta(hours=1))
            .isoformat()
            .replace("+00:00", "Z"),
        }
        session_config = load_engineering_question_alpha_session_config(
            self.write_config(document)
        )
        transport_factory_calls = 0

        def transport_factory():
            nonlocal transport_factory_calls
            transport_factory_calls += 1
            raise AssertionError("preparation must not construct a Provider transport")

        with (
            SqliteDatabase() as database,
            patch(
                "software_world_model.interface.engineering_qa_alpha_cli._verify_product_candidate",
                return_value=(self.commit, self.tree),
            ),
            patch(
                "software_world_model.interface.engineering_qa_alpha_cli._exact_source_revision",
                return_value=revision,
            ),
            patch(
                "software_world_model.interface.engineering_qa_alpha_cli.load_deepseek_chat_conformance_qualification",
                return_value=qualification,
            ),
        ):
            prepared = prepare_engineering_question_alpha(
                session_config,
                database=database,
                transport_factory=transport_factory,
                at=now,
            )

        self.assertEqual(transport_factory_calls, 0)
        self.assertEqual(prepared.assembly.execution_factory.transports, ())
        health = prepared.assembly.product.health()
        self.assertEqual(health["question_submission_mode"], "SESSION_AUTHORIZED")
        self.assertEqual(
            health["project"]["source_class_allowlist"]["SOURCE"],
            ["src/main/java"],
        )
        self.assertEqual(
            health["project"]["excluded_source_paths"],
            ["src/main/resources"],
        )
        launch = prepared.launch_receipt()
        self.assertEqual(launch["provider_dispatch_count_at_seal"], 0)
        self.assertEqual(launch["accepted_question_count_at_seal"], 0)
        terminal = prepared.terminal_receipt()
        self.assertEqual(terminal["status"], "STOPPED_WITHOUT_DISPATCH")
        self.assertEqual(terminal["accepted_question_count"], 0)


if __name__ == "__main__":
    unittest.main()
