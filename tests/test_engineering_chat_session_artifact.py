from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
from types import SimpleNamespace
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from software_world_model.ai_infrastructure.ark_chat_conformance import (
    ARK_CHAT_CONFORMANCE_FIXTURE_ID,
    ArkChatConformanceQualification,
)
from software_world_model.ai_infrastructure.deepseek_chat_adapter import (
    DeepSeekModelConfiguration,
)
from software_world_model.ai_infrastructure.deepseek_chat_conformance import (
    DEEPSEEK_CHAT_CONFORMANCE_FIXTURE_ID,
    DeepSeekChatConformanceQualification,
)
from software_world_model.ai_infrastructure.volcengine_ark_chat_adapter import (
    VolcengineArkModelConfiguration,
)
from software_world_model.cross_cutting import (
    Digest,
    DomainError,
    StableId,
    canonical_json_bytes,
    digest_of,
)
from software_world_model.interface.engineering_chat_session_artifact import (
    ENGINEERING_CHAT_ARTIFACT_SESSION_CONFIG_SCHEMA,
    ENGINEERING_CHAT_ARTIFACT_SESSION_PREPARATION_STATUS,
    load_engineering_chat_artifact_session_config,
    prepare_engineering_chat_artifact_session,
)
from software_world_model.interface.engineering_chat_session_runtime import (
    ENGINEERING_CHAT_FIXED_ARTIFACT_SESSION_RUNTIME_STATUS,
)


class _UnusedModelGatewayRepository:
    def recover(self, **kwargs):
        raise AssertionError(f"artifact preparation called recover: {kwargs}")

    def prepare(self, **kwargs):
        raise AssertionError(f"artifact preparation called prepare: {kwargs}")

    def transition(self, **kwargs):
        raise AssertionError(f"artifact preparation called transition: {kwargs}")

    def get(self, *args, **kwargs):
        raise AssertionError(
            f"artifact preparation called get: {args!r} {kwargs!r}"
        )

    def recover_by_id(self, *args, **kwargs):
        raise AssertionError(
            f"artifact preparation called recover_by_id: {args!r} {kwargs!r}"
        )

    def get_manifest(self, *args, **kwargs):
        raise AssertionError(
            f"artifact preparation called get_manifest: {args!r} {kwargs!r}"
        )


class _UnusedCognitionProjector:
    def __init__(self, *, binding_id, revision, authority):
        self.binding_id = binding_id
        self.source_revision = revision
        self.read_authority_digest = authority
        self.calls = 0

    def project(self, *, request):
        self.calls += 1
        raise AssertionError(f"artifact preparation projected cognition: {request}")


class EngineeringChatSessionArtifactTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.product = self.root / "product"
        self.source = self.root / "source"
        self.product.mkdir()
        self.source.mkdir()
        self.ordered = self.root / "ordered.json"
        self.snapshot = self.root / "snapshot.json"
        self.ark_conformance = self.root / "ark-conformance.json"
        self.deepseek_conformance = self.root / "deepseek-conformance.json"
        for path in (
            self.ordered,
            self.snapshot,
            self.ark_conformance,
            self.deepseek_conformance,
        ):
            path.write_text("{}\n", encoding="utf-8")
        self.now = datetime(2026, 8, 25, 10, tzinfo=timezone.utc)
        self.product_commit = "a" * 40
        self.product_tree = "b" * 40
        self.source_revision = "c" * 40
        self.binding_id = StableId("binding_" + "2" * 32)

    def document(self) -> dict[str, object]:
        return {
            "schema": ENGINEERING_CHAT_ARTIFACT_SESSION_CONFIG_SCHEMA,
            "product_repository": str(self.product),
            "product_commit": self.product_commit,
            "product_tree": self.product_tree,
            "project_name": "mall",
            "repository": str(self.source),
            "repository_id": "repository_" + "1" * 32,
            "binding_id": self.binding_id.value,
            "repository_revision": self.source_revision,
            "source_profile_ref": "mall-chat-source-profile:1",
            "source_paths": ["src/main/java"],
            "document_paths": ["README.md"],
            "build_paths": ["pom.xml"],
            "test_paths": ["src/test/java"],
            "excluded_source_paths": ["src/main/resources"],
            "ordered_envelope": str(self.ordered),
            "snapshot_bundles": [str(self.snapshot)],
            "cognition_snapshot_id": "snapshot_" + "3" * 32,
            "response_language": "zh-CN",
            "session_ref": "iteration-010-chat-alpha",
            "authorization_message_digest": digest_of(
                "artifact-session-authorization"
            ).value,
            "authorized_at": (self.now - timedelta(minutes=1))
            .isoformat()
            .replace("+00:00", "Z"),
            "expires_at": (self.now + timedelta(hours=1))
            .isoformat()
            .replace("+00:00", "Z"),
            "provider_routes": [
                {
                    "ordinal": 1,
                    "provider_type": "VOLCENGINE_ARK",
                    "conformance_result": str(self.ark_conformance),
                    "gateway_database": str(self.root / "ark-gateway.sqlite3"),
                },
                {
                    "ordinal": 2,
                    "provider_type": "DEEPSEEK",
                    "conformance_result": str(self.deepseek_conformance),
                    "gateway_database": str(
                        self.root / "deepseek-gateway.sqlite3"
                    ),
                },
            ],
            "launch_receipt": str(self.root / "launch.json"),
            "terminal_receipt": str(self.root / "terminal.json"),
            "required_conversation_turns": 5,
            "maximum_dispatches_per_turn": 15,
            "maximum_total_dispatches_per_provider": 75,
            "known_limitations": [
                "Direction Alpha only; answer quality is not accepted",
                "src/main/resources and configuration credentials are excluded",
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

    def test_loader_requires_private_closed_ordered_route_document(self) -> None:
        path = self.write_config(self.document())
        loaded = load_engineering_chat_artifact_session_config(path)

        self.assertEqual(
            tuple(item.provider_type for item in loaded.provider_routes),
            ("VOLCENGINE_ARK", "DEEPSEEK"),
        )
        self.assertEqual(loaded.required_conversation_turns, 5)
        self.assertEqual(loaded.maximum_total_dispatches_per_provider, 75)

        unknown = self.write_config(
            {**self.document(), "question": "client scope is forbidden"},
            name="unknown.json",
        )
        with self.assertRaises(DomainError):
            load_engineering_chat_artifact_session_config(unknown)

        reversed_routes = self.document()
        reversed_routes["provider_routes"] = list(
            reversed(reversed_routes["provider_routes"])
        )
        with self.assertRaises(DomainError):
            load_engineering_chat_artifact_session_config(
                self.write_config(reversed_routes, name="reversed.json")
            )

        boolean_ordinal = self.document()
        boolean_ordinal["provider_routes"][0]["ordinal"] = True
        with self.assertRaises(DomainError):
            load_engineering_chat_artifact_session_config(
                self.write_config(boolean_ordinal, name="boolean-ordinal.json")
            )

        duplicate = self.root / "duplicate.json"
        duplicate.write_text('{"schema":"a","schema":"b"}', encoding="utf-8")
        os.chmod(duplicate, 0o600)
        with self.assertRaises(DomainError):
            load_engineering_chat_artifact_session_config(duplicate)

        os.chmod(path, 0o644)
        with self.assertRaises(DomainError):
            load_engineering_chat_artifact_session_config(path)
        os.chmod(path, 0o400)
        with self.assertRaises(DomainError):
            load_engineering_chat_artifact_session_config(path)

    def test_prepare_loads_artifact_identities_without_runtime_io(self) -> None:
        session_config = load_engineering_chat_artifact_session_config(
            self.write_config(self.document())
        )
        ark_provider = VolcengineArkModelConfiguration()
        deepseek_provider = DeepSeekModelConfiguration()
        ark_digest = digest_of("current-ark-conformance")
        deepseek_digest = digest_of("current-deepseek-conformance")
        ark_qualification = ArkChatConformanceQualification(
            result_ref=(
                f"{ARK_CHAT_CONFORMANCE_FIXTURE_ID}:{ark_digest.value}"
            ),
            result_digest=ark_digest,
            qualified_model_fingerprints=(
                ark_provider.qualified_model_identities
            ),
            adapter_version=ark_provider.adapter_version,
            provider_configuration_fingerprint=ark_provider.fingerprint,
            valid_until=self.now + timedelta(days=1),
        )
        deepseek_qualification = DeepSeekChatConformanceQualification(
            result_ref=(
                f"{DEEPSEEK_CHAT_CONFORMANCE_FIXTURE_ID}:"
                f"{deepseek_digest.value}"
            ),
            result_digest=deepseek_digest,
            qualified_model_fingerprints=(
                deepseek_provider.qualified_model_identities
            ),
            adapter_version=deepseek_provider.adapter_version,
            provider_configuration_fingerprint=deepseek_provider.fingerprint,
            valid_until=self.now + timedelta(days=1),
        )
        ordered_bundle_digest = digest_of("ordered-bundle")
        ordered_file_digest = digest_of("ordered-file")
        snapshot_bundle_digest = digest_of("snapshot-bundle")
        snapshot_file_digest = digest_of("snapshot-file")
        snapshot = SimpleNamespace(
            snapshot_id=StableId("snapshot_" + "3" * 32)
        )
        store = SimpleNamespace(
            read_ordered=lambda path: (object(), ordered_file_digest),
            read_snapshot=lambda path: (snapshot, snapshot_file_digest),
        )
        view = SimpleNamespace(
            ordered_bundle_digest=ordered_bundle_digest,
            snapshot_bundle_digests=(snapshot_bundle_digest,),
        )
        cognition = _UnusedCognitionProjector(
            binding_id=self.binding_id,
            revision=self.source_revision,
            authority=digest_of("world-model-authority"),
        )

        with (
            patch(
                "software_world_model.interface.engineering_chat_session_artifact._verify_product_candidate",
                return_value=(self.product_commit, self.product_tree),
            ),
            patch(
                "software_world_model.interface.engineering_chat_session_artifact._exact_source_revision",
                return_value=self.source_revision,
            ),
            patch(
                "software_world_model.interface.engineering_chat_session_artifact.FileStructureReadBundleStore",
                return_value=store,
            ),
            patch(
                "software_world_model.interface.engineering_chat_session_artifact.StructureViewService",
                return_value=view,
            ),
            patch(
                "software_world_model.interface.engineering_chat_session_artifact._select_cognition_snapshot",
                return_value=snapshot,
            ),
            patch(
                "software_world_model.interface.engineering_chat_session_artifact.StructureBundleWorldModelCognitionProjector",
                return_value=cognition,
            ),
            patch(
                "software_world_model.interface.engineering_chat_session_artifact.load_ark_chat_conformance_qualification",
                return_value=ark_qualification,
            ),
            patch(
                "software_world_model.interface.engineering_chat_session_artifact.load_deepseek_chat_conformance_qualification",
                return_value=deepseek_qualification,
            ),
        ):
            prepared = prepare_engineering_chat_artifact_session(
                session_config,
                ark_gateway_repository=_UnusedModelGatewayRepository(),
                deepseek_gateway_repository=_UnusedModelGatewayRepository(),
                at=self.now,
            )
        self.addCleanup(
            prepared.runtime.fallback_provider_runtime.transport.close
        )

        self.assertEqual(
            prepared.runtime.receipt.status,
            ENGINEERING_CHAT_FIXED_ARTIFACT_SESSION_RUNTIME_STATUS,
        )
        self.assertEqual(
            prepared.public_status()["status"],
            ENGINEERING_CHAT_ARTIFACT_SESSION_PREPARATION_STATUS,
        )
        self.assertTrue(prepared.runtime.receipt.artifact_session_config_loaded)
        self.assertTrue(prepared.runtime.receipt.fixed_command_wired)
        self.assertEqual(
            prepared.runtime.receipt.blocking_gaps,
            ("LIVE_PROVIDER_AND_BROWSER_NOT_EXECUTED",),
        )
        self.assertEqual(
            prepared.runtime.receipt.artifact_session_config_digest,
            session_config.file_digest,
        )
        self.assertEqual(cognition.calls, 0)
        self.assertEqual(prepared.runtime.launcher.service.statistics(), (0, 0))
        self.assertEqual(
            prepared.runtime.launcher.service.provider_dispatch_count(), 0
        )
        self.assertEqual(
            prepared.runtime.evidence_tool_factory.created_tool_count, 0
        )
        self.assertEqual(
            prepared.runtime.primary_provider_runtime.model_boundary.audits,
            (),
        )
        self.assertEqual(
            prepared.runtime.fallback_provider_runtime.model_boundary.audits,
            (),
        )
        launch = prepared.launch_receipt()
        self.assertEqual(
            launch["status"], "ARTIFACT_SESSION_PREPARED_NOT_STARTED"
        )
        self.assertEqual(launch["provider_dispatch_count_at_seal"], 0)
        terminal = prepared.terminal_receipt()
        self.assertEqual(terminal["status"], "STOPPED_WITHOUT_DISPATCH")
        self.assertEqual(terminal["provider_dispatch_count"], 0)
        ark_audit, deepseek_audit = terminal["provider_audits"]
        self.assertEqual(
            ark_audit["transport_session_audit"]["http_dispatch_count"],
            0,
        )
        self.assertEqual(
            ark_audit["transport_session_audit"]["request_retry_count"],
            0,
        )
        self.assertEqual(
            deepseek_audit["transport_session_audit"]["http_dispatch_count"],
            0,
        )
        self.assertEqual(
            deepseek_audit["transport_session_audit"]["request_retry_count"],
            0,
        )
        public = json.dumps(prepared.public_status(), sort_keys=True)
        self.assertNotIn(str(self.root / "ark-gateway.sqlite3"), public)
        self.assertNotIn(str(self.root / "deepseek-gateway.sqlite3"), public)
        self.assertNotIn("ARK_API_KEY", public)
        self.assertNotIn("DEEPSEEK_API_KEY", public)
        self.assertNotIn("secret_reference", public)


if __name__ == "__main__":
    unittest.main()
