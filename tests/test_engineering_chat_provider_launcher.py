from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import unittest

from software_world_model.ai_infrastructure.conversational_engineering_model import (
    ENGINEERING_AGENT_DISCLOSURE_POLICY_REF,
    EngineeringAgentModelConfiguration,
    EngineeringAgentSessionDisclosureAuthority,
)
from software_world_model.application_services.conversational_engineering_routing import (
    EngineeringProviderRoutePlan,
    EngineeringProviderRouteRole,
    EngineeringProviderRouteSpec,
    SealedPreDispatchUnavailableAvailabilityBoundary,
    engineering_agent_dual_provider_route_ref,
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
    engineering_chat_product_candidate_digest,
)
from software_world_model.interface.engineering_chat_provider_launcher import (
    ENGINEERING_CHAT_PROVIDER_LAUNCHER_BLOCKING_GAPS,
    ENGINEERING_CHAT_PROVIDER_LAUNCHER_STATUS,
    EngineeringChatProviderAttemptDependencies,
    EngineeringChatProviderAttemptFactory,
    prepare_engineering_chat_provider_launcher,
)


class _UnusedModelBoundary:
    def propose(self, invocation):
        del invocation
        raise AssertionError("launcher preparation cannot invoke a model driver")

    def review(self, request):
        del request
        raise AssertionError("launcher preparation cannot invoke a Reviewer")


class EngineeringChatProviderLauncherTests(unittest.TestCase):
    def setUp(self) -> None:
        self.now = datetime(2026, 8, 25, 8, tzinfo=timezone.utc)
        self.product_revision = "a" * 40
        self.product_tree = "b" * 40
        self.repository_revision = "c" * 40
        self.world_authority = digest_of("world-model-authority")
        self.source_profile_ref = "mall-source-profile@1"
        self.primary_configuration = self._configuration(
            provider_type="VOLCENGINE_ARK",
            adapter_version="ark-chat-completions-no-tools@1",
            endpoint=(
                "https://ark.cn-beijing.volces.com/"
                "api/coding/v3/chat/completions"
            ),
            model_ref="ark-model@current",
            secret_reference="env:ARK_API_KEY",
        )
        self.fallback_configuration = self._configuration(
            provider_type="DEEPSEEK",
            adapter_version="deepseek-chat-completions-no-tools@1",
            endpoint="https://api.deepseek.com/chat/completions",
            model_ref="deepseek-model@current",
            secret_reference="env:DEEPSEEK_API_KEY",
        )
        route_ref = engineering_agent_dual_provider_route_ref(
            primary_configuration_digest=self.primary_configuration.digest,
            fallback_configuration_digest=self.fallback_configuration.digest,
        )
        self.binding = EngineeringChatBinding.create(
            product_revision=self.product_revision,
            project_name="mall",
            repository_revision=self.repository_revision,
            world_model_status=RuntimeCapabilityStatus.READY,
            world_model_authority_digest=self.world_authority,
            source_profile_ref=self.source_profile_ref,
            source_access_status=RuntimeCapabilityStatus.READY,
            provider_status=RuntimeCapabilityStatus.READY,
            provider_route_ref=route_ref,
            known_limitations=("direction Alpha only",),
        )
        product_digest = engineering_chat_product_candidate_digest(
            product_revision=self.product_revision,
            product_tree=self.product_tree,
        )
        self.primary_authority = self._authority(
            configuration=self.primary_configuration,
            product_digest=product_digest,
            label="ark",
        )
        self.fallback_authority = self._authority(
            configuration=self.fallback_configuration,
            product_digest=product_digest,
            label="deepseek",
        )
        primary_route = self._route(
            ordinal=1,
            role=EngineeringProviderRouteRole.PREFERRED,
            configuration=self.primary_configuration,
            authority=self.primary_authority,
        )
        fallback_route = self._route(
            ordinal=2,
            role=EngineeringProviderRouteRole.FALLBACK,
            configuration=self.fallback_configuration,
            authority=self.fallback_authority,
        )
        self.plan = EngineeringProviderRoutePlan.create(
            binding=self.binding,
            preferred=primary_route,
            fallback=fallback_route,
        )
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
        self.callback_calls = []
        self.factory = self._factory()

    def _configuration(
        self,
        *,
        provider_type,
        adapter_version,
        endpoint,
        model_ref,
        secret_reference,
    ):
        return EngineeringAgentModelConfiguration(
            provider_type=provider_type,
            adapter_version=adapter_version,
            endpoint=endpoint,
            model_ref=model_ref,
            expected_actual_model_fingerprint=model_ref,
            provider_configuration_fingerprint=digest_of(
                [provider_type, "configuration"]
            ),
            secret_reference=secret_reference,
            qualification_ref=f"CC-{provider_type}-CURRENT",
            qualification_valid_until=self.now + timedelta(hours=2),
            maximum_calls=20,
        )

    def _authority(
        self,
        *,
        configuration,
        product_digest,
        label,
        maximum_total_dispatches=75,
    ):
        message_digest = digest_of([label, "exact local authorization"])
        return EngineeringAgentSessionDisclosureAuthority.create(
            session_ref=f"engineering-chat-{label}",
            product_candidate_digest=product_digest,
            chat_binding_digest=self.binding.digest,
            configuration=configuration,
            maximum_turns=5,
            maximum_dispatches_per_turn=15,
            maximum_total_dispatches=maximum_total_dispatches,
            authorized_at=self.now,
            expires_at=self.now + timedelta(hours=1),
            authorization_ref=f"codex-user-message:{message_digest.value}",
            authorization_message_digest=message_digest,
        )

    @staticmethod
    def _route(*, ordinal, role, configuration, authority):
        return EngineeringProviderRouteSpec.create(
            ordinal=ordinal,
            role=role,
            execution_profile_ref=(
                "runtime-config:preferred-qualified-profile"
                if role is EngineeringProviderRouteRole.PREFERRED
                else "runtime-config:fallback-qualified-profile"
            ),
            execution_profile_digest=configuration.digest,
            session_disclosure_authority_digest=authority.digest,
            maximum_dispatches_per_turn=(
                authority.maximum_dispatches_per_turn
            ),
        )

    def _factory(self):
        primary_model = _UnusedModelBoundary()
        fallback_model = _UnusedModelBoundary()

        def tool_factory(authority):
            self.callback_calls.append((authority.role.value, "tool"))
            raise AssertionError("not used during preparation")

        def response_factory(authority):
            self.callback_calls.append((authority.role.value, "response"))
            raise AssertionError("not used during preparation")

        primary = EngineeringChatProviderAttemptDependencies.create(
            route=self.plan.routes[0],
            configuration=self.primary_configuration,
            session_authority=self.primary_authority,
            model_boundary_ref="ark-model-boundary@1",
            model_gateway_repository_ref="ark-gateway-repository@1",
            disclosure_authorizer_ref="ark-disclosure-authorizer@1",
            response_control_ref="response-control@1:ark",
            driver=primary_model,
            reviewer=primary_model,
            tool_factory=tool_factory,
            response_control_factory=response_factory,
        )
        fallback = EngineeringChatProviderAttemptDependencies.create(
            route=self.plan.routes[1],
            configuration=self.fallback_configuration,
            session_authority=self.fallback_authority,
            model_boundary_ref="deepseek-model-boundary@1",
            model_gateway_repository_ref="deepseek-gateway-repository@1",
            disclosure_authorizer_ref="deepseek-disclosure-authorizer@1",
            response_control_ref="response-control@1:deepseek",
            driver=fallback_model,
            reviewer=fallback_model,
            tool_factory=tool_factory,
            response_control_factory=response_factory,
        )
        return EngineeringChatProviderAttemptFactory(
            plan=self.plan,
            evidence_tool_configuration_digest=self.tools.digest,
            primary=primary,
            fallback=fallback,
        )

    def test_fixed_launcher_preparation_is_zero_io_and_wires_routed_browser(self) -> None:
        prepared = prepare_engineering_chat_provider_launcher(
            binding=self.binding,
            product_tree=self.product_tree,
            evidence_tools=self.tools,
            primary_configuration=self.primary_configuration,
            fallback_configuration=self.fallback_configuration,
            primary_session_authority=self.primary_authority,
            fallback_session_authority=self.fallback_authority,
            route_plan=self.plan,
            attempt_factory=self.factory,
            checked_at=self.now,
        )

        receipt = prepared.receipt
        self.assertEqual(receipt.status, ENGINEERING_CHAT_PROVIDER_LAUNCHER_STATUS)
        self.assertEqual(
            receipt.blocking_gaps,
            ENGINEERING_CHAT_PROVIDER_LAUNCHER_BLOCKING_GAPS,
        )
        self.assertEqual(
            receipt.ordered_provider_types,
            ("VOLCENGINE_ARK", "DEEPSEEK"),
        )
        self.assertFalse(receipt.ready_for_live)
        self.assertFalse(receipt.listener_started)
        self.assertFalse(receipt.credential_resolved)
        self.assertFalse(receipt.source_read_performed)
        self.assertEqual(receipt.provider_dispatch_count, 0)
        self.assertFalse(receipt.request_retry_allowed)
        self.assertEqual(receipt.production_activation, "NOT_EXECUTED")
        self.assertEqual(prepared.service.statistics(), (0, 0))
        self.assertIsInstance(
            prepared.router._availability_boundary,
            SealedPreDispatchUnavailableAvailabilityBoundary,
        )
        self.assertEqual(self.callback_calls, [])
        status = json.dumps(receipt.public_status(), sort_keys=True)
        self.assertNotIn("ARK_API_KEY", status)
        self.assertNotIn("DEEPSEEK_API_KEY", status)
        self.assertNotIn("secret_reference", status)

    def test_drifted_fallback_session_is_rejected(self) -> None:
        wrong_product = digest_of("different-product")
        drifted = self._authority(
            configuration=self.fallback_configuration,
            product_digest=wrong_product,
            label="deepseek-drifted",
        )

        with self.assertRaises(DomainError):
            prepare_engineering_chat_provider_launcher(
                binding=self.binding,
                product_tree=self.product_tree,
                evidence_tools=self.tools,
                primary_configuration=self.primary_configuration,
                fallback_configuration=self.fallback_configuration,
                primary_session_authority=self.primary_authority,
                fallback_session_authority=drifted,
                route_plan=self.plan,
                attempt_factory=self.factory,
                checked_at=self.now,
            )
        self.assertEqual(self.callback_calls, [])

    def test_each_provider_must_fund_five_turn_worst_case(self) -> None:
        product_digest = engineering_chat_product_candidate_digest(
            product_revision=self.product_revision,
            product_tree=self.product_tree,
        )
        insufficient = self._authority(
            configuration=self.fallback_configuration,
            product_digest=product_digest,
            label="deepseek-insufficient",
            maximum_total_dispatches=74,
        )
        fallback_route = self._route(
            ordinal=2,
            role=EngineeringProviderRouteRole.FALLBACK,
            configuration=self.fallback_configuration,
            authority=insufficient,
        )
        plan = EngineeringProviderRoutePlan.create(
            binding=self.binding,
            preferred=self.plan.routes[0],
            fallback=fallback_route,
        )
        model = _UnusedModelBoundary()
        fallback_dependencies = EngineeringChatProviderAttemptDependencies.create(
            route=fallback_route,
            configuration=self.fallback_configuration,
            session_authority=insufficient,
            model_boundary_ref="deepseek-insufficient-boundary@1",
            model_gateway_repository_ref="deepseek-insufficient-repository@1",
            disclosure_authorizer_ref="deepseek-insufficient-authorizer@1",
            response_control_ref="deepseek-insufficient-response@1",
            driver=model,
            reviewer=model,
            tool_factory=lambda authority: None,
            response_control_factory=lambda authority: None,
        )
        factory = EngineeringChatProviderAttemptFactory(
            plan=plan,
            evidence_tool_configuration_digest=self.tools.digest,
            primary=self.factory.primary,
            fallback=fallback_dependencies,
        )

        with self.assertRaises(DomainError):
            prepare_engineering_chat_provider_launcher(
                binding=self.binding,
                product_tree=self.product_tree,
                evidence_tools=self.tools,
                primary_configuration=self.primary_configuration,
                fallback_configuration=self.fallback_configuration,
                primary_session_authority=self.primary_authority,
                fallback_session_authority=insufficient,
                route_plan=plan,
                attempt_factory=factory,
                checked_at=self.now,
            )


if __name__ == "__main__":
    unittest.main()
