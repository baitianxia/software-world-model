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
from software_world_model.application_services.engineering_conversation import (
    ENGINEERING_CHAT_EMPTY_CONTEXT_REFERENT_POLICY_ZH_CN,
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
    ENGINEERING_CHAT_ARTIFACT_SESSION_CONFIG_SCHEMA_V1,
    ENGINEERING_CHAT_ARTIFACT_SESSION_CONFIG_SCHEMA_V2,
    ENGINEERING_CHAT_ARTIFACT_SESSION_CONFIG_SCHEMA_V3,
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

    def record_provider_http_failure_evidence(self, *args, **kwargs):
        raise AssertionError(
            f"artifact preparation recorded HTTP evidence: {args!r} {kwargs!r}"
        )

    def get_provider_http_failure_evidence(self, *args, **kwargs):
        raise AssertionError(
            f"artifact preparation read HTTP evidence: {args!r} {kwargs!r}"
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
        self.java_ordered = self.root / "java-ordered.json"
        self.java_snapshot = self.root / "java-snapshot.json"
        self.ark_conformance = self.root / "ark-conformance.json"
        self.deepseek_conformance = self.root / "deepseek-conformance.json"
        for path in (
            self.ordered,
            self.snapshot,
            self.java_ordered,
            self.java_snapshot,
            self.ark_conformance,
            self.deepseek_conformance,
        ):
            path.write_text("{}\n", encoding="utf-8")
        self.now = datetime(2026, 8, 25, 10, tzinfo=timezone.utc)
        self.product_commit = "a" * 40
        self.product_tree = "b" * 40
        self.source_revision = "c" * 40
        self.source_tree = "d" * 40
        self.binding_id = StableId("binding_" + "2" * 32)

    def document(self) -> dict[str, object]:
        return {
            "schema": ENGINEERING_CHAT_ARTIFACT_SESSION_CONFIG_SCHEMA_V1,
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

    def document_v2(self) -> dict[str, object]:
        document = self.document()
        document["schema"] = ENGINEERING_CHAT_ARTIFACT_SESSION_CONFIG_SCHEMA_V2
        document.pop("ordered_envelope")
        document.pop("snapshot_bundles")
        document.pop("cognition_snapshot_id")
        document["cognition_profiles"] = [
            {
                "ordinal": 0,
                "profile_ref": "MAVEN_STRUCTURE@1",
                "schema_ref": "MAVEN-STRUCTURE@1.0.0",
                "source_binding_id": self.binding_id.value,
                "ordered_envelope": str(self.ordered),
                "ordered_bundle_digest": digest_of(
                    "maven-ordered-bundle"
                ).value,
                "ordered_file_digest": digest_of("maven-ordered-file").value,
                "snapshot_bundles": [str(self.snapshot)],
                "snapshot_bundle_digests": [
                    digest_of("maven-snapshot-bundle").value
                ],
                "snapshot_file_digests": [
                    digest_of("maven-snapshot-file").value
                ],
                "cognition_snapshot_id": "snapshot_" + "3" * 32,
            },
            {
                "ordinal": 1,
                "profile_ref": "JAVA_SOURCE_SEMANTICS@1",
                "schema_ref": "JAVA-SOURCE-SEMANTICS@1.0.0",
                "source_binding_id": "binding_" + "4" * 32,
                "ordered_envelope": str(self.java_ordered),
                "ordered_bundle_digest": digest_of(
                    "java-ordered-bundle"
                ).value,
                "ordered_file_digest": digest_of("java-ordered-file").value,
                "snapshot_bundles": [str(self.java_snapshot)],
                "snapshot_bundle_digests": [
                    digest_of("java-snapshot-bundle").value
                ],
                "snapshot_file_digests": [
                    digest_of("java-snapshot-file").value
                ],
                "cognition_snapshot_id": "snapshot_" + "5" * 32,
            },
        ]
        return document

    def document_v3(self) -> dict[str, object]:
        document = self.document_v2()
        document["schema"] = ENGINEERING_CHAT_ARTIFACT_SESSION_CONFIG_SCHEMA_V3
        document["deepseek_dispatch_admission"] = {
            "schema": "DEEPSEEK_DISPATCH_ADMISSION_INPUT@1",
            "policy_ref": "ITER-010-PDR-007@2",
            "run_type": "LOCAL_ARTIFACT_TEST",
            "run_ref": "test-engineering-chat-session-artifact",
            "turn_scope_digest": digest_of(
                "artifact-test-turn-scope"
            ).value,
            "official_pricing_source": (
                "https://api-docs.deepseek.com/quick_start/pricing/"
            ),
            "official_pricing_checked_at": (
                self.now - timedelta(seconds=30)
            ).isoformat().replace("+00:00", "Z"),
            "official_pricing_content_digest": digest_of(
                "artifact-test-pricing-page"
            ).value,
            "official_pricing_content_summary": (
                "官方页面的工作日峰时和周末全天闲时已在测试输入中冻结。"
            ),
            "official_pricing_effective_status": "EFFECTIVE",
            "maximum_input_tokens": 10_000_000,
            "maximum_output_tokens": 75 * 8_192,
            "maximum_duration_seconds": 600,
            "peak_override": None,
        }
        return document

    def document_v4(self) -> dict[str, object]:
        document = self.document_v3()
        document["schema"] = ENGINEERING_CHAT_ARTIFACT_SESSION_CONFIG_SCHEMA
        document.pop("authorization_message_digest")
        human_digest = digest_of("standing-human-authority")
        ark = VolcengineArkModelConfiguration()
        deepseek = DeepSeekModelConfiguration()
        document["standing_authority"] = {
            "schema": "PUBLIC_SOURCE_MODEL_STANDING_AUTHORITY@1",
            "authority_ref": "test-public-source-standing-authority@1",
            "human_authority_ref": (
                "local-user-message-utf8:" + human_digest.value
            ),
            "human_authority_digest": human_digest.value,
            "authority_evidence_refs": ["SYS-ADR-019", "test-authority"],
            "purpose": "public-open-source-loopback-evaluation",
            "source_authority_ref": "test-public-source-authority@1",
            "canonical_source_upstream": "https://example.com/public/repo.git",
            "source_license": "Apache-2.0",
            "source_license_path": "LICENSE",
            "source_revision_policy": "EXACT_CLEAN_COMMIT",
            "source_tree": self.source_tree,
            "route_policy_ref": "qualified-primary-fallback@1",
            "provider_scopes": [
                {
                    "ordinal": 1,
                    "route_role": "PRIMARY",
                    "provider_type": ark.provider_type,
                    "adapter_version": ark.adapter_version,
                    "endpoint": ark.endpoint,
                    "model_ref": ark.model_ref,
                    "expected_actual_model_fingerprint": (
                        ark.actual_model_fingerprint
                    ),
                    "provider_configuration_fingerprint": ark.fingerprint.value,
                    "secret_reference": ark.secret_reference,
                    "disclosure_policy_ref": (
                        "engineering-agent-exact-role-disclosure@1"
                    ),
                    "dispatch_admission_policy_ref": "NONE",
                    "maximum_calls": 75,
                    "maximum_input_bytes": 4_194_304,
                    "maximum_output_tokens": 8_192,
                    "timeout_milliseconds": 180_000,
                },
                {
                    "ordinal": 2,
                    "route_role": "FALLBACK",
                    "provider_type": deepseek.provider_type,
                    "adapter_version": deepseek.adapter_version,
                    "endpoint": deepseek.endpoint,
                    "model_ref": deepseek.model_ref,
                    "expected_actual_model_fingerprint": (
                        deepseek.actual_model_fingerprint
                    ),
                    "provider_configuration_fingerprint": (
                        deepseek.fingerprint.value
                    ),
                    "secret_reference": deepseek.secret_reference,
                    "disclosure_policy_ref": (
                        "engineering-agent-exact-role-disclosure@1"
                    ),
                    "dispatch_admission_policy_ref": "ITER-010-PDR-007@2",
                    "maximum_calls": 75,
                    "maximum_input_bytes": 4_194_304,
                    "maximum_output_tokens": 8_192,
                    "timeout_milliseconds": 180_000,
                },
            ],
            "maximum_turns": 5,
            "maximum_dispatches_per_turn": 15,
            "maximum_total_dispatches_per_provider": 75,
            "maximum_input_tokens": 10_000_000,
            "maximum_output_tokens": 75 * 8_192,
            "maximum_duration_seconds": 600,
            "authorized_at": (self.now - timedelta(minutes=1))
            .isoformat()
            .replace("+00:00", "Z"),
            "expires_at": (self.now + timedelta(hours=1))
            .isoformat()
            .replace("+00:00", "Z"),
            "sink": "EVALUATION_ONLY",
            "loopback_origin": "http://127.0.0.1:8765/",
        }
        return document

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

    def provider_qualifications(self):
        ark_provider = VolcengineArkModelConfiguration()
        deepseek_provider = DeepSeekModelConfiguration()
        ark_digest = digest_of("current-ark-conformance")
        deepseek_digest = digest_of("current-deepseek-conformance")
        return (
            ArkChatConformanceQualification(
                result_ref=(
                    f"{ARK_CHAT_CONFORMANCE_FIXTURE_ID}:{ark_digest.value}"
                ),
                result_digest=ark_digest,
                qualified_model_fingerprints=(
                    ark_provider.qualified_model_identities
                ),
                adapter_version=ark_provider.adapter_version,
                provider_configuration_fingerprint=ark_provider.fingerprint,
                valid_until=datetime.now(timezone.utc) + timedelta(days=1),
            ),
            DeepSeekChatConformanceQualification(
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
                valid_until=datetime.now(timezone.utc) + timedelta(days=1),
            ),
        )

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

    def test_v2_loader_seals_ordered_multi_profile_artifact_identities(self) -> None:
        loaded = load_engineering_chat_artifact_session_config(
            self.write_config(self.document_v2(), name="session-v2.json")
        )

        self.assertEqual(
            tuple(item.ordinal for item in loaded.cognition_profiles),
            (0, 1),
        )
        self.assertEqual(
            tuple(item.profile_ref for item in loaded.cognition_profiles),
            ("MAVEN_STRUCTURE@1", "JAVA_SOURCE_SEMANTICS@1"),
        )
        self.assertNotEqual(
            loaded.cognition_profiles[0].source_binding_id,
            loaded.cognition_profiles[1].source_binding_id,
        )

        reordered = self.document_v2()
        reordered["cognition_profiles"] = list(
            reversed(reordered["cognition_profiles"])
        )
        with self.assertRaises(DomainError):
            load_engineering_chat_artifact_session_config(
                self.write_config(reordered, name="v2-reordered.json")
            )

        unsealed = self.document_v2()
        unsealed["cognition_profiles"][1]["snapshot_file_digests"] = []
        with self.assertRaises(DomainError):
            load_engineering_chat_artifact_session_config(
                self.write_config(unsealed, name="v2-unsealed.json")
            )

    def test_v4_loader_replaces_message_grant_with_closed_standing_scope(self) -> None:
        document = self.document_v4()
        loaded = load_engineering_chat_artifact_session_config(
            self.write_config(document, name="session-v4.json")
        )

        self.assertIsNone(loaded.authorization_message_digest)
        self.assertIsNotNone(loaded.standing_authority)
        self.assertEqual(
            loaded.standing_authority.source_revision,
            self.source_revision,
        )
        self.assertEqual(
            loaded.standing_authority.source_tree,
            self.source_tree,
        )

        mismatched_human = self.document_v4()
        mismatched_human["standing_authority"]["human_authority_ref"] = (
            "local-user-message-utf8:" + digest_of("different-human").value
        )
        with self.assertRaises(DomainError):
            load_engineering_chat_artifact_session_config(
                self.write_config(
                    mismatched_human,
                    name="v4-mismatched-human.json",
                )
            )

        widened = self.document_v4()
        widened["standing_authority"]["maximum_turns"] = 129
        with self.assertRaises(DomainError):
            load_engineering_chat_artifact_session_config(
                self.write_config(widened, name="v4-widened.json")
            )

    def test_prepare_loads_artifact_identities_without_runtime_io(self) -> None:
        document = self.document_v4()
        document["cognition_profiles"] = document["cognition_profiles"][:1]
        profile_document = document["cognition_profiles"][0]
        session_config = load_engineering_chat_artifact_session_config(
            self.write_config(document)
        )
        ark_qualification, deepseek_qualification = (
            self.provider_qualifications()
        )
        ordered_bundle_digest = Digest(profile_document["ordered_bundle_digest"])
        ordered_file_digest = Digest(profile_document["ordered_file_digest"])
        snapshot_bundle_digest = Digest(
            profile_document["snapshot_bundle_digests"][0]
        )
        snapshot_file_digest = Digest(
            profile_document["snapshot_file_digests"][0]
        )
        snapshot = SimpleNamespace(
            snapshot_id=StableId("snapshot_" + "3" * 32),
            digest=snapshot_bundle_digest,
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
        cognition.snapshot_bundle = snapshot
        capability = SimpleNamespace(
            ordinal=0,
            profile_ref="MAVEN_STRUCTURE@1",
            schema_ref="MAVEN-STRUCTURE@1.0.0",
            source_binding_id=self.binding_id,
            snapshot_id=snapshot.snapshot_id,
            snapshot_bundle_digest=snapshot_bundle_digest,
            read_authority_digest=cognition.read_authority_digest,
            ordered_bundle_digest=ordered_bundle_digest,
        )
        cognition.manifest = SimpleNamespace(profiles=(capability,))

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
                "software_world_model.interface.engineering_chat_session_artifact._verify_public_source_mirror",
                return_value=(
                    "https://example.com/public/repo.git",
                    self.source_tree,
                    True,
                    "blob",
                    digest_of("test-public-source-mirror"),
                ),
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
                "software_world_model.interface.engineering_chat_session_artifact.MultiProfileWorldModelCognitionProjector",
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
        self.assertIsNotNone(prepared.public_source_session_authority)
        authority_status = prepared.public_status()["authority_chain"]
        self.assertEqual(authority_status["human_approval_request_count"], 0)
        self.assertEqual(
            prepared.runtime.primary_provider_runtime.session_authority.standing_authority_digest,
            session_config.standing_authority.digest,
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
            prepared.runtime.launcher.service.binding.conversation_input_policy_ref,
            ENGINEERING_CHAT_EMPTY_CONTEXT_REFERENT_POLICY_ZH_CN,
        )
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
        self.assertEqual(launch["human_approval_request_count"], 0)
        self.assertEqual(
            launch["standing_authority_digest"],
            session_config.standing_authority.digest.value,
        )
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

    def test_prepare_v3_composes_two_exact_profile_authorities(self) -> None:
        document = self.document_v3()
        session_config = load_engineering_chat_artifact_session_config(
            self.write_config(document, name="prepare-v3.json")
        )
        ark_qualification, deepseek_qualification = (
            self.provider_qualifications()
        )
        profile_documents = document["cognition_profiles"]
        ordered_bundle_digests = tuple(
            Digest(item["ordered_bundle_digest"])
            for item in profile_documents
        )
        ordered_file_digests = tuple(
            Digest(item["ordered_file_digest"])
            for item in profile_documents
        )
        snapshot_bundle_digests = tuple(
            Digest(item["snapshot_bundle_digests"][0])
            for item in profile_documents
        )
        snapshot_file_digests = tuple(
            Digest(item["snapshot_file_digests"][0])
            for item in profile_documents
        )
        snapshots = tuple(
            SimpleNamespace(
                snapshot_id=StableId(item["cognition_snapshot_id"]),
                digest=snapshot_bundle_digest,
            )
            for item, snapshot_bundle_digest in zip(
                profile_documents,
                snapshot_bundle_digests,
                strict=True,
            )
        )
        ordered_results = iter(
            (object(), digest) for digest in ordered_file_digests
        )
        snapshot_results = iter(
            zip(snapshots, snapshot_file_digests, strict=True)
        )
        store = SimpleNamespace(
            read_ordered=lambda path: next(ordered_results),
            read_snapshot=lambda path: next(snapshot_results),
        )
        views = tuple(
            SimpleNamespace(
                ordered_bundle_digest=ordered_digest,
                snapshot_bundle_digests=(snapshot_digest,),
            )
            for ordered_digest, snapshot_digest in zip(
                ordered_bundle_digests,
                snapshot_bundle_digests,
                strict=True,
            )
        )
        projectors = (
            _UnusedCognitionProjector(
                binding_id=self.binding_id,
                revision=self.source_revision,
                authority=digest_of("maven-world-model-authority"),
            ),
            _UnusedCognitionProjector(
                binding_id=StableId("binding_" + "4" * 32),
                revision=self.source_revision,
                authority=digest_of("java-world-model-authority"),
            ),
        )
        capabilities = []
        for ordinal, (profile_document, projector, snapshot, ordered_digest) in enumerate(
            zip(
                profile_documents,
                projectors,
                snapshots,
                ordered_bundle_digests,
                strict=True,
            )
        ):
            projector.snapshot_bundle = snapshot
            capabilities.append(
                SimpleNamespace(
                    ordinal=ordinal,
                    profile_ref=profile_document["profile_ref"],
                    schema_ref=profile_document["schema_ref"],
                    source_binding_id=projector.binding_id,
                    snapshot_id=snapshot.snapshot_id,
                    snapshot_bundle_digest=snapshot.digest,
                    read_authority_digest=projector.read_authority_digest,
                    ordered_bundle_digest=ordered_digest,
                )
            )
        cognition = _UnusedCognitionProjector(
            binding_id=self.binding_id,
            revision=self.source_revision,
            authority=digest_of("multi-profile-manifest"),
        )
        cognition.manifest = SimpleNamespace(profiles=tuple(capabilities))

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
                side_effect=views,
            ),
            patch(
                "software_world_model.interface.engineering_chat_session_artifact._select_cognition_snapshot",
                side_effect=snapshots,
            ),
            patch(
                "software_world_model.interface.engineering_chat_session_artifact.StructureBundleWorldModelCognitionProjector",
                side_effect=projectors,
            ),
            patch(
                "software_world_model.interface.engineering_chat_session_artifact.MultiProfileWorldModelCognitionProjector",
                return_value=cognition,
            ) as multi_factory,
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
            multi_factory.call_args.kwargs["projectors"],
            projectors,
        )
        self.assertEqual(len(prepared.cognition_profiles), 2)
        self.assertEqual(
            prepared.world_model_read_authority_digest,
            cognition.read_authority_digest,
        )
        world_model = prepared.public_status()["world_model_artifacts"]
        self.assertEqual(len(world_model["profiles"]), 2)
        self.assertEqual(
            world_model["read_authority_digest"],
            cognition.read_authority_digest.value,
        )
        self.assertEqual(cognition.calls, 0)
        self.assertEqual(
            prepared.runtime.launcher.service.provider_dispatch_count(), 0
        )


if __name__ == "__main__":
    unittest.main()
