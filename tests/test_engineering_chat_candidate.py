from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import unittest

from software_world_model.ai_infrastructure.conversational_engineering_model import (
    ENGINEERING_AGENT_DISCLOSURE_POLICY_REF,
    EngineeringAgentModelConfiguration,
    EngineeringAgentSessionDisclosureAuthority,
)
from software_world_model.application_services.conversational_engineering_tools import (
    EngineeringAgentEvidenceToolConfiguration,
)
from software_world_model.application_services.engineering_conversation import (
    EngineeringChatBinding,
    RuntimeCapabilityStatus,
)
from software_world_model.cross_cutting import DomainError, StableId, digest_of
from software_world_model.interface.engineering_chat_candidate import (
    ENGINEERING_CHAT_CANDIDATE_BLOCKING_GAPS,
    ENGINEERING_CHAT_MODEL_BOUNDARY_CANDIDATE_STATUS,
    engineering_chat_product_candidate_digest,
    engineering_chat_single_provider_route_ref,
    prepare_engineering_chat_candidate_preflight,
)


class EngineeringChatCandidatePreflightTests(unittest.TestCase):
    def setUp(self) -> None:
        self.now = datetime(2026, 8, 25, 8, 0, tzinfo=timezone.utc)
        self.product_revision = "a" * 40
        self.product_tree = "b" * 40
        self.repository_revision = "c" * 40
        self.world_authority = digest_of("world-model-authority")
        self.source_profile_ref = "mall-source-profile@1"
        self.configuration = EngineeringAgentModelConfiguration(
            provider_type="VOLCENGINE_ARK",
            adapter_version="ark-chat-completions-no-tools@1",
            endpoint="https://ark.cn-beijing.volces.com/api/v3/chat/completions",
            model_ref="ark-model-fixture@1",
            expected_actual_model_fingerprint="ark-model-fixture@1",
            provider_configuration_fingerprint=digest_of("ark-configuration"),
            secret_reference="env:ARK_API_KEY",
            qualification_ref="CC-ARK-CURRENT-FIXTURE",
            qualification_valid_until=self.now + timedelta(hours=2),
        )
        self.binding = self._binding()
        self.tools = EngineeringAgentEvidenceToolConfiguration.create(
            project_name="mall",
            response_language="zh-CN",
            repository_id=StableId("repository_" + "1" * 32),
            binding_id=StableId("binding_" + "2" * 32),
            repository_revision=self.repository_revision,
            source_profile_ref=self.source_profile_ref,
            source_profile_digest=digest_of("source-profile"),
            world_model_read_authority_digest=self.world_authority,
            source_allowlist=("README.md", "pom.xml", "src/main/java"),
            provider_disclosure_policy=ENGINEERING_AGENT_DISCLOSURE_POLICY_REF,
        )
        self.authority = self._authority(
            engineering_chat_product_candidate_digest(
                product_revision=self.product_revision,
                product_tree=self.product_tree,
            )
        )

    def _binding(self, **overrides) -> EngineeringChatBinding:
        values = {
            "product_revision": self.product_revision,
            "project_name": "mall",
            "repository_revision": self.repository_revision,
            "world_model_status": RuntimeCapabilityStatus.READY,
            "world_model_authority_digest": self.world_authority,
            "source_profile_ref": self.source_profile_ref,
            "source_access_status": RuntimeCapabilityStatus.READY,
            "provider_status": RuntimeCapabilityStatus.READY,
            "provider_route_ref": engineering_chat_single_provider_route_ref(
                self.configuration
            ),
            "known_limitations": (
                "single Provider local candidate only",
                "fallback and live launcher are not integrated",
            ),
        }
        values.update(overrides)
        return EngineeringChatBinding.create(**values)

    def _authority(
        self,
        product_candidate_digest,
        *,
        binding=None,
        maximum_turns=5,
        maximum_dispatches_per_turn=15,
        maximum_total_dispatches=75,
    ) -> EngineeringAgentSessionDisclosureAuthority:
        message_digest = digest_of("exact local session authorization")
        return EngineeringAgentSessionDisclosureAuthority.create(
            session_ref="engineering-chat-candidate-fixture",
            product_candidate_digest=product_candidate_digest,
            chat_binding_digest=(binding or self.binding).digest,
            configuration=self.configuration,
            maximum_turns=maximum_turns,
            maximum_dispatches_per_turn=maximum_dispatches_per_turn,
            maximum_total_dispatches=maximum_total_dispatches,
            authorized_at=self.now,
            expires_at=self.now + timedelta(hours=1),
            authorization_ref=f"codex-user-message:{message_digest.value}",
            authorization_message_digest=message_digest,
        )

    def test_preflight_is_non_live_and_public_status_excludes_secret_reference(self) -> None:
        receipt = prepare_engineering_chat_candidate_preflight(
            binding=self.binding,
            product_tree=self.product_tree,
            evidence_tools=self.tools,
            provider_configuration=self.configuration,
            session_authority=self.authority,
            checked_at=self.now,
        )

        self.assertEqual(
            receipt.status, ENGINEERING_CHAT_MODEL_BOUNDARY_CANDIDATE_STATUS
        )
        self.assertEqual(receipt.blocking_gaps, ENGINEERING_CHAT_CANDIDATE_BLOCKING_GAPS)
        self.assertFalse(receipt.ready_for_live)
        self.assertFalse(receipt.listener_started)
        self.assertFalse(receipt.credential_resolved)
        self.assertFalse(receipt.source_read_performed)
        self.assertEqual(receipt.provider_dispatch_count, 0)
        self.assertFalse(receipt.request_retry_allowed)
        self.assertEqual(receipt.production_activation, "NOT_EXECUTED")
        status_json = json.dumps(receipt.public_status(), sort_keys=True)
        self.assertNotIn("ARK_API_KEY", status_json)
        self.assertNotIn("secret_reference", status_json)

    def test_product_candidate_drift_is_rejected(self) -> None:
        wrong = self._authority(digest_of("different-product-candidate"))

        with self.assertRaises(DomainError):
            prepare_engineering_chat_candidate_preflight(
                binding=self.binding,
                product_tree=self.product_tree,
                evidence_tools=self.tools,
                provider_configuration=self.configuration,
                session_authority=wrong,
                checked_at=self.now,
            )

    def test_evidence_tool_binding_drift_is_rejected(self) -> None:
        drifted_binding = self._binding(
            world_model_authority_digest=digest_of("different-world-model")
        )
        authority = self._authority(
            engineering_chat_product_candidate_digest(
                product_revision=self.product_revision,
                product_tree=self.product_tree,
            ),
            binding=drifted_binding,
        )

        with self.assertRaises(DomainError):
            prepare_engineering_chat_candidate_preflight(
                binding=drifted_binding,
                product_tree=self.product_tree,
                evidence_tools=self.tools,
                provider_configuration=self.configuration,
                session_authority=authority,
                checked_at=self.now,
            )

    def test_five_turn_worst_case_model_fuse_is_required(self) -> None:
        insufficient = self._authority(
            engineering_chat_product_candidate_digest(
                product_revision=self.product_revision,
                product_tree=self.product_tree,
            ),
            maximum_total_dispatches=74,
        )

        with self.assertRaises(DomainError):
            prepare_engineering_chat_candidate_preflight(
                binding=self.binding,
                product_tree=self.product_tree,
                evidence_tools=self.tools,
                provider_configuration=self.configuration,
                session_authority=insufficient,
                checked_at=self.now,
            )


if __name__ == "__main__":
    unittest.main()
