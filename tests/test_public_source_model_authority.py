from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
import unittest

from software_world_model.ai_infrastructure.conversational_engineering_model import (
    ENGINEERING_AGENT_SESSION_AUTHORITY_SCHEMA_V2,
    EngineeringAgentModelConfiguration,
    EngineeringAgentSessionDisclosureAuthority,
)
from software_world_model.application_services.public_source_model_authority import (
    NO_DISPATCH_ADMISSION_POLICY,
    PublicSourceModelSessionAuthority,
    PublicSourceModelStandingAuthority,
    PublicSourceProviderScope,
)
from software_world_model.cross_cutting import (
    Digest,
    DomainError,
    StableId,
    digest_of,
)


class PublicSourceModelAuthorityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.now = datetime(2026, 8, 25, 8, tzinfo=timezone.utc)
        self.provider_scope = PublicSourceProviderScope.create(
            ordinal=1,
            route_role="PRIMARY",
            provider_type="TEST_PROVIDER",
            adapter_version="test-adapter@1",
            endpoint="https://provider.invalid/v1/chat",
            model_ref="test-model@1",
            expected_actual_model_fingerprint="test-model@1",
            provider_configuration_fingerprint=digest_of("provider-config"),
            secret_reference="env:TEST_PROVIDER_API_KEY",
            disclosure_policy_ref="exact-role-disclosure@1",
            dispatch_admission_policy_ref=NO_DISPATCH_ADMISSION_POLICY,
            maximum_calls=6,
            maximum_input_bytes=1_048_576,
            maximum_output_tokens=4_096,
            timeout_milliseconds=120_000,
        )
        human_digest = digest_of("standing human authority")
        self.standing = PublicSourceModelStandingAuthority.create(
            authority_ref="public-source-test-authority@1",
            human_authority_ref=(
                "local-user-message-utf8:" + human_digest.value
            ),
            human_authority_digest=human_digest,
            authority_evidence_refs=("SYS-ADR-019", "test-decision"),
            purpose="public Source loopback evaluation",
            source_authority_ref="test-source-authority@1",
            canonical_source_upstream="https://example.com/public/repo.git",
            source_license="Apache-2.0",
            source_license_path="LICENSE",
            source_revision_policy="EXACT_CLEAN_COMMIT",
            source_revision="a" * 40,
            source_tree="b" * 40,
            source_profile_ref="public-source-profile@1",
            source_allowlist=(
                "src/main/java",
                "README.md",
                "pom.xml",
                "src/test/java",
            ),
            excluded_source_paths=("src/main/resources",),
            route_policy_ref="qualified-primary@1",
            provider_scopes=(self.provider_scope,),
            maximum_turns=2,
            maximum_dispatches_per_turn=3,
            maximum_total_dispatches_per_provider=6,
            maximum_input_tokens=100_000,
            maximum_output_tokens=24_576,
            maximum_duration_seconds=300,
            authorized_at=self.now - timedelta(minutes=1),
            expires_at=self.now + timedelta(hours=1),
        )

    def derive(self, **overrides) -> PublicSourceModelSessionAuthority:
        values = {
            "standing_authority": self.standing,
            "session_ref": "public-source-session-001",
            "product_revision": "c" * 40,
            "product_tree": "d" * 40,
            "product_candidate_digest": digest_of("product-candidate"),
            "source_repository_ref": digest_of("local-mirror"),
            "observed_source_upstream": self.standing.canonical_source_upstream,
            "observed_source_revision": self.standing.source_revision,
            "observed_source_tree": self.standing.source_tree,
            "source_clean": True,
            "license_object_type": "blob",
            "source_profile_ref": self.standing.source_profile_ref,
            "source_profile_digest": digest_of("source-profile"),
            "source_allowlist": self.standing.source_allowlist,
            "excluded_source_paths": self.standing.excluded_source_paths,
            "repository_id": StableId("repository_" + "1" * 32),
            "binding_id": StableId("binding_" + "2" * 32),
            "world_model_read_authority_digest": digest_of("world-model"),
            "chat_binding_digest": digest_of("chat-binding"),
            "provider_route_ref": "qualified-primary-runtime@1",
            "provider_scopes": self.standing.provider_scopes,
            "provider_configuration_digests": (digest_of("exact-provider"),),
            "provider_qualification_refs": ("CC-TEST-PROVIDER",),
            "maximum_turns": 2,
            "maximum_dispatches_per_turn": 3,
            "maximum_total_dispatches_per_provider": 6,
            "maximum_input_tokens": 100_000,
            "maximum_output_tokens": 24_576,
            "maximum_duration_seconds": 300,
            "authorized_at": self.now - timedelta(seconds=30),
            "expires_at": self.now + timedelta(minutes=30),
            "derived_at": self.now,
        }
        values.update(overrides)
        return PublicSourceModelSessionAuthority.derive(**values)

    def test_exact_session_and_provider_authorities_bind_standing_parent(self) -> None:
        session = self.derive()
        configuration = EngineeringAgentModelConfiguration(
            provider_type=self.provider_scope.provider_type,
            adapter_version=self.provider_scope.adapter_version,
            endpoint=self.provider_scope.endpoint,
            model_ref=self.provider_scope.model_ref,
            expected_actual_model_fingerprint=(
                self.provider_scope.expected_actual_model_fingerprint
            ),
            provider_configuration_fingerprint=(
                self.provider_scope.provider_configuration_fingerprint
            ),
            secret_reference=self.provider_scope.secret_reference,
            qualification_ref="CC-TEST-PROVIDER",
            qualification_valid_until=self.now + timedelta(hours=1),
            provider_disclosure_policy_ref=(
                "engineering-agent-exact-role-disclosure@1"
            ),
            maximum_calls=6,
            maximum_input_bytes=1_048_576,
            maximum_output_tokens=4_096,
            timeout_milliseconds=120_000,
        )
        provider = (
            EngineeringAgentSessionDisclosureAuthority.derive_from_public_source_session(
                session_ref="public-source-session-001:test",
                product_candidate_digest=session.product_candidate_digest,
                chat_binding_digest=session.chat_binding_digest,
                configuration=configuration,
                maximum_turns=2,
                maximum_dispatches_per_turn=3,
                maximum_total_dispatches=6,
                authorized_at=session.authorized_at,
                expires_at=session.expires_at,
                standing_authority_digest=session.parent_authority_digest,
                public_source_session_authority_digest=session.digest,
            )
        )

        self.assertEqual(
            provider.schema, ENGINEERING_AGENT_SESSION_AUTHORITY_SCHEMA_V2
        )
        self.assertEqual(provider.standing_authority_digest, self.standing.digest)
        self.assertEqual(provider.public_source_session_authority_digest, session.digest)
        self.assertEqual(provider.human_approval_request_count, 0)
        provider.require_current(
            configuration=configuration,
            chat_binding_digest=session.chat_binding_digest,
            at=self.now,
        )

    def test_source_provider_budget_and_authority_drift_fail_closed(self) -> None:
        for overrides in (
            {"observed_source_upstream": "https://example.com/private/repo.git"},
            {"source_clean": False},
            {"observed_source_tree": "e" * 40},
            {"maximum_total_dispatches_per_provider": 7},
            {"provider_scopes": (replace(self.provider_scope, model_ref="drift"),)},
        ):
            with self.subTest(overrides=overrides):
                with self.assertRaises(DomainError):
                    self.derive(**overrides)

        forged = replace(self.standing, maximum_turns=3)
        with self.assertRaises(DomainError):
            forged.require_current(self.now)

    def test_human_evidence_and_expiration_cannot_be_self_widened(self) -> None:
        with self.assertRaises(DomainError):
            PublicSourceModelStandingAuthority.create(
                authority_ref=self.standing.authority_ref,
                human_authority_ref="local-user-message-utf8:" + "f" * 71,
                human_authority_digest=self.standing.human_authority_digest,
                authority_evidence_refs=self.standing.authority_evidence_refs,
                purpose=self.standing.purpose,
                source_authority_ref=self.standing.source_authority_ref,
                canonical_source_upstream=self.standing.canonical_source_upstream,
                source_license=self.standing.source_license,
                source_license_path=self.standing.source_license_path,
                source_revision_policy=self.standing.source_revision_policy,
                source_revision=self.standing.source_revision,
                source_tree=self.standing.source_tree,
                source_profile_ref=self.standing.source_profile_ref,
                source_allowlist=self.standing.source_allowlist,
                excluded_source_paths=self.standing.excluded_source_paths,
                route_policy_ref=self.standing.route_policy_ref,
                provider_scopes=self.standing.provider_scopes,
                maximum_turns=self.standing.maximum_turns,
                maximum_dispatches_per_turn=(
                    self.standing.maximum_dispatches_per_turn
                ),
                maximum_total_dispatches_per_provider=(
                    self.standing.maximum_total_dispatches_per_provider
                ),
                maximum_input_tokens=self.standing.maximum_input_tokens,
                maximum_output_tokens=self.standing.maximum_output_tokens,
                maximum_duration_seconds=self.standing.maximum_duration_seconds,
                authorized_at=self.standing.authorized_at,
                expires_at=self.standing.expires_at,
            )
        with self.assertRaises(DomainError):
            self.derive(derived_at=self.standing.expires_at)


if __name__ == "__main__":
    unittest.main()
