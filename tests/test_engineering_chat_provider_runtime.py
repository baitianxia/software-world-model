from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from software_world_model.ai_infrastructure.ark_chat_conformance import (
    ARK_CHAT_CONFORMANCE_FIXTURE_ID,
    ArkChatConformanceQualification,
)
from software_world_model.ai_infrastructure.deepseek_chat_adapter import (
    DeepSeekChatCompletionsNoToolsAdapter,
    DeepSeekModelConfiguration,
    PersistentDeepSeekChatTransport,
)
from software_world_model.ai_infrastructure.deepseek_chat_conformance import (
    DEEPSEEK_CHAT_CONFORMANCE_FIXTURE_ID,
    DeepSeekChatConformanceQualification,
)
from software_world_model.ai_infrastructure.model_gateway import (
    AdapterConformanceLevel,
    AuthorizedInputItem,
    AuthorizedInputManifest,
    InputDisposition,
    ModelExecutionContext,
    PlatformProposalMode,
    RuntimeAccessMode,
)
from software_world_model.ai_infrastructure.volcengine_ark_chat_adapter import (
    UrllibVolcengineArkChatTransport,
    VolcengineArkChatCompletionsNoToolsAdapter,
    VolcengineArkModelConfiguration,
)
from software_world_model.application_services.conversational_engineering_routing import (
    EngineeringProviderRoutePlan,
    EngineeringProviderRouteRole,
    EngineeringProviderRouteSpec,
    engineering_agent_dual_provider_route_ref,
)
from software_world_model.application_services.conversational_engineering_tools import (
    EngineeringAgentEvidenceToolConfiguration,
)
from software_world_model.application_services.deepseek_dispatch_admission import (
    DEEPSEEK_PRICING_SOURCE,
    DeepSeekDispatchAdmissionController,
    DeepSeekDispatchAdmissionPlan,
    DeepSeekOfficialPricingCheck,
    DeepSeekPricingEffectiveStatus,
)
from software_world_model.application_services.engineering_question_answering import (
    EngineeringEvidenceClass,
    SourceBroker,
)
from software_world_model.application_services.engineering_conversation import (
    EngineeringChatBinding,
    RuntimeCapabilityStatus,
)
from software_world_model.cross_cutting import DomainError, StableId, digest_of
from software_world_model.interface.engineering_chat_candidate import (
    engineering_chat_product_candidate_digest,
)
from software_world_model.interface.engineering_chat_provider_runtime import (
    ENGINEERING_CHAT_ARK_TRANSPORT_REF,
    ENGINEERING_CHAT_DEEPSEEK_TRANSPORT_REF,
    ENGINEERING_CHAT_PROVIDER_MODEL_RUNTIME_STATUS,
    create_ark_engineering_chat_provider_model_runtime,
    create_deepseek_engineering_chat_provider_model_runtime,
    engineering_chat_ark_model_configuration,
    engineering_chat_deepseek_model_configuration,
)
from software_world_model.ai_infrastructure.conversational_engineering_model import (
    ENGINEERING_AGENT_DISCLOSURE_POLICY_REF,
    EngineeringAgentSessionDisclosureAuthority,
)
from software_world_model.interface.engineering_chat_provider_launcher import (
    EngineeringChatProviderAttemptFactory,
    prepare_engineering_chat_provider_launcher,
)
from software_world_model.interface.engineering_chat_session_runtime import (
    ENGINEERING_CHAT_SESSION_RUNTIME_STATUS,
    EngineeringChatEvidenceToolFactory,
    prepare_engineering_chat_session_runtime,
)
from software_world_model.interface.engineering_qa_source import (
    LocalGitEvidenceClassProfile,
    LocalGitRetrievalWorker,
)


class _UnusedModelGatewayRepository:
    """Expose the repository protocol while proving preparation performs no call."""

    def recover(self, **kwargs):
        raise AssertionError(f"preparation called recover: {kwargs}")

    def prepare(self, **kwargs):
        raise AssertionError(f"preparation called prepare: {kwargs}")

    def transition(self, **kwargs):
        raise AssertionError(f"preparation called transition: {kwargs}")

    def get(self, *args, **kwargs):
        raise AssertionError(f"preparation called get: {args!r} {kwargs!r}")

    def recover_by_id(self, *args, **kwargs):
        raise AssertionError(
            f"preparation called recover_by_id: {args!r} {kwargs!r}"
        )

    def get_manifest(self, *args, **kwargs):
        raise AssertionError(
            f"preparation called get_manifest: {args!r} {kwargs!r}"
        )

    def record_provider_http_failure_evidence(self, *args, **kwargs):
        raise AssertionError(
            f"preparation recorded HTTP evidence: {args!r} {kwargs!r}"
        )

    def get_provider_http_failure_evidence(self, *args, **kwargs):
        raise AssertionError(
            f"preparation read HTTP evidence: {args!r} {kwargs!r}"
        )


class _UnusedCognitionProjector:
    def __init__(self, *, authority, revision, binding_id):
        self.read_authority_digest = authority
        self.source_revision = revision
        self.binding_id = binding_id
        self.calls = 0

    def project(self, *, request):
        self.calls += 1
        raise AssertionError(f"Session preparation projected cognition: {request}")


class _UnusedSourceBroker:
    def registered_evidence_classes(self, *, request):
        raise AssertionError(f"Session preparation queried Broker: {request}")

    def compile(self, **kwargs):
        raise AssertionError(f"Session preparation compiled Source: {kwargs}")


class _UnusedRetrievalWorker:
    def execute(self, operation):
        raise AssertionError(f"Session preparation read Source: {operation}")


class EngineeringChatProviderRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.now = datetime(2026, 8, 25, 4, tzinfo=timezone.utc)
        self.valid_until = datetime(2099, 1, 1, tzinfo=timezone.utc)
        self.ark_provider = VolcengineArkModelConfiguration(
            api_key_environment_variable="ITER010_TEST_ARK_KEY"
        )
        self.deepseek_provider = DeepSeekModelConfiguration(
            api_key_environment_variable="ITER010_TEST_DEEPSEEK_KEY"
        )
        self.ark_qualification = self._ark_qualification()
        self.deepseek_qualification = self._deepseek_qualification()
        self.ark_configuration = engineering_chat_ark_model_configuration(
            provider_configuration=self.ark_provider,
            qualification=self.ark_qualification,
            at=self.now,
        )
        self.deepseek_configuration = (
            engineering_chat_deepseek_model_configuration(
                provider_configuration=self.deepseek_provider,
                qualification=self.deepseek_qualification,
                at=self.now,
            )
        )
        route_ref = engineering_agent_dual_provider_route_ref(
            primary_configuration_digest=self.ark_configuration.digest,
            fallback_configuration_digest=self.deepseek_configuration.digest,
        )
        self.binding = EngineeringChatBinding.create(
            product_revision="a" * 40,
            project_name="mall",
            repository_revision="b" * 40,
            world_model_status=RuntimeCapabilityStatus.READY,
            world_model_authority_digest=digest_of("world-model-authority"),
            source_profile_ref="mall-source-profile:1",
            source_access_status=RuntimeCapabilityStatus.READY,
            provider_status=RuntimeCapabilityStatus.READY,
            provider_route_ref=route_ref,
            known_limitations=("direction Alpha only",),
        )
        product_digest = engineering_chat_product_candidate_digest(
            product_revision=self.binding.product_revision,
            product_tree="c" * 40,
        )
        self.ark_authority = self._authority(
            label="ark",
            product_digest=product_digest,
            configuration=self.ark_configuration,
        )
        self.deepseek_authority = self._authority(
            label="deepseek",
            product_digest=product_digest,
            configuration=self.deepseek_configuration,
        )

    def _ark_qualification(self):
        result_digest = digest_of("ark-current-conformance")
        return ArkChatConformanceQualification(
            result_ref=(
                f"{ARK_CHAT_CONFORMANCE_FIXTURE_ID}:{result_digest.value}"
            ),
            result_digest=result_digest,
            qualified_model_fingerprints=(
                self.ark_provider.qualified_model_identities
            ),
            adapter_version=self.ark_provider.adapter_version,
            provider_configuration_fingerprint=self.ark_provider.fingerprint,
            valid_until=self.valid_until,
        )

    def _deepseek_qualification(self):
        result_digest = digest_of("deepseek-current-conformance")
        return DeepSeekChatConformanceQualification(
            result_ref=(
                f"{DEEPSEEK_CHAT_CONFORMANCE_FIXTURE_ID}:{result_digest.value}"
            ),
            result_digest=result_digest,
            qualified_model_fingerprints=(
                self.deepseek_provider.qualified_model_identities
            ),
            adapter_version=self.deepseek_provider.adapter_version,
            provider_configuration_fingerprint=(
                self.deepseek_provider.fingerprint
            ),
            valid_until=self.valid_until,
        )

    def _authority(self, *, label, product_digest, configuration):
        message_digest = digest_of([label, "runtime authorization"])
        return EngineeringAgentSessionDisclosureAuthority.create(
            session_ref=f"engineering-chat-{label}",
            product_candidate_digest=product_digest,
            chat_binding_digest=self.binding.digest,
            configuration=configuration,
            maximum_turns=5,
            maximum_dispatches_per_turn=15,
            maximum_total_dispatches=75,
            authorized_at=self.now,
            expires_at=self.now + timedelta(hours=1),
            authorization_ref=f"codex-user-message:{message_digest.value}",
            authorization_message_digest=message_digest,
        )

    def _deepseek_admission(self) -> DeepSeekDispatchAdmissionController:
        pricing_check = DeepSeekOfficialPricingCheck.create(
            source=DEEPSEEK_PRICING_SOURCE,
            checked_at=self.now - timedelta(seconds=30),
            content_digest=digest_of("provider-runtime-pricing-check"),
            content_summary="官方页面的峰谷时段已在本地测试输入中冻结。",
            effective_status=(
                DeepSeekPricingEffectiveStatus.NOT_YET_EFFECTIVE
            ),
        )
        plan = DeepSeekDispatchAdmissionPlan.create(
            run_type="LOCAL_RUNTIME_TEST",
            run_ref="test-engineering-chat-provider-runtime",
            turn_scope_digest=digest_of("provider-runtime-turn-scope"),
            product_revision=self.binding.product_revision,
            source_revision=self.binding.repository_revision,
            session_ref=self.deepseek_authority.session_ref,
            provider_configuration_digest=self.deepseek_configuration.digest,
            model_ref=self.deepseek_configuration.model_ref,
            authorization_message_digest=(
                self.deepseek_authority.authorization_message_digest
            ),
            authorized_at=self.deepseek_authority.authorized_at,
            expires_at=self.deepseek_authority.expires_at,
            maximum_calls=self.deepseek_authority.maximum_total_dispatches,
            maximum_input_tokens=10_000_000,
            maximum_output_tokens=75 * 8_192,
            maximum_duration_seconds=600,
            pricing_check=pricing_check,
        )
        return DeepSeekDispatchAdmissionController(
            plan=plan,
            admitted_at=self.now,
            clock=lambda: self.now,
        )

    def test_real_provider_runtimes_prepare_without_io_or_credentials(self) -> None:
        ark = create_ark_engineering_chat_provider_model_runtime(
            repository=_UnusedModelGatewayRepository(),
            gateway_repository_ref="ark-gateway-db:sha256:one",
            binding=self.binding,
            provider_configuration=self.ark_provider,
            qualification=self.ark_qualification,
            configuration=self.ark_configuration,
            session_authority=self.ark_authority,
            at=self.now,
            clock=lambda: self.now,
        )
        deepseek = create_deepseek_engineering_chat_provider_model_runtime(
            repository=_UnusedModelGatewayRepository(),
            gateway_repository_ref="deepseek-gateway-db:sha256:two",
            binding=self.binding,
            provider_configuration=self.deepseek_provider,
            qualification=self.deepseek_qualification,
            configuration=self.deepseek_configuration,
            session_authority=self.deepseek_authority,
            dispatch_admission_controller=self._deepseek_admission(),
            at=self.now,
            clock=lambda: self.now,
        )
        self.addCleanup(deepseek.transport.close)

        self.assertEqual(ark.status, ENGINEERING_CHAT_PROVIDER_MODEL_RUNTIME_STATUS)
        self.assertEqual(
            deepseek.status, ENGINEERING_CHAT_PROVIDER_MODEL_RUNTIME_STATUS
        )
        self.assertIsInstance(
            ark.adapter, VolcengineArkChatCompletionsNoToolsAdapter
        )
        self.assertIsInstance(ark.transport, UrllibVolcengineArkChatTransport)
        self.assertIsInstance(
            deepseek.adapter, DeepSeekChatCompletionsNoToolsAdapter
        )
        self.assertIsInstance(
            deepseek.transport, PersistentDeepSeekChatTransport
        )
        self.assertEqual(ark.transport_ref, ENGINEERING_CHAT_ARK_TRANSPORT_REF)
        self.assertEqual(
            deepseek.transport_ref, ENGINEERING_CHAT_DEEPSEEK_TRANSPORT_REF
        )
        self.assertIs(
            ark.adapter.capabilities.conformance_level,
            AdapterConformanceLevel.LIVE_CURRENT,
        )
        self.assertIs(
            deepseek.adapter.capabilities.conformance_level,
            AdapterConformanceLevel.LIVE_CURRENT,
        )
        self.assertEqual(ark.model_boundary.audits, ())
        self.assertEqual(deepseek.model_boundary.audits, ())
        self.assertEqual(ark.authorizer.disclosure_requests, ())
        self.assertEqual(deepseek.authorizer.disclosure_requests, ())
        self.assertEqual(deepseek.transport.tls_handshake_attempt_count, 0)
        self.assertEqual(deepseek.transport.credential_resolution_count, 0)
        status = json.dumps(
            [ark.public_status(), deepseek.public_status()], sort_keys=True
        )
        self.assertNotIn("ITER010_TEST_ARK_KEY", status)
        self.assertNotIn("ITER010_TEST_DEEPSEEK_KEY", status)
        self.assertNotIn("secret_reference", status)

    def test_runtime_dependencies_bind_two_distinct_live_boundaries(self) -> None:
        ark = create_ark_engineering_chat_provider_model_runtime(
            repository=_UnusedModelGatewayRepository(),
            gateway_repository_ref="ark-gateway-db:sha256:one",
            binding=self.binding,
            provider_configuration=self.ark_provider,
            qualification=self.ark_qualification,
            configuration=self.ark_configuration,
            session_authority=self.ark_authority,
            at=self.now,
            clock=lambda: self.now,
        )
        deepseek = create_deepseek_engineering_chat_provider_model_runtime(
            repository=_UnusedModelGatewayRepository(),
            gateway_repository_ref="deepseek-gateway-db:sha256:two",
            binding=self.binding,
            provider_configuration=self.deepseek_provider,
            qualification=self.deepseek_qualification,
            configuration=self.deepseek_configuration,
            session_authority=self.deepseek_authority,
            dispatch_admission_controller=self._deepseek_admission(),
            at=self.now,
            clock=lambda: self.now,
        )
        self.addCleanup(deepseek.transport.close)
        primary_route = self._route(
            ordinal=1,
            role=EngineeringProviderRouteRole.PREFERRED,
            configuration=self.ark_configuration,
            authority=self.ark_authority,
        )
        fallback_route = self._route(
            ordinal=2,
            role=EngineeringProviderRouteRole.FALLBACK,
            configuration=self.deepseek_configuration,
            authority=self.deepseek_authority,
        )
        unused_tool_factory = lambda authority: None
        unused_response_factory = lambda authority: None
        primary = ark.attempt_dependencies(
            route=primary_route,
            tool_factory=unused_tool_factory,
            response_control_factory=unused_response_factory,
            response_control_ref="response-control@1:ark",
        )
        fallback = deepseek.attempt_dependencies(
            route=fallback_route,
            tool_factory=unused_tool_factory,
            response_control_factory=unused_response_factory,
            response_control_ref="response-control@1:deepseek",
        )
        plan = EngineeringProviderRoutePlan.create(
            binding=self.binding,
            preferred=primary_route,
            fallback=fallback_route,
        )
        evidence_tools = EngineeringAgentEvidenceToolConfiguration.create(
            project_name=self.binding.project_name,
            response_language="zh-CN",
            repository_id=StableId("repository_" + "1" * 32),
            binding_id=StableId("binding_" + "2" * 32),
            repository_revision=self.binding.repository_revision,
            source_profile_ref=self.binding.source_profile_ref,
            source_profile_digest=digest_of("source-profile"),
            world_model_read_authority_digest=(
                self.binding.world_model_authority_digest
            ),
            source_allowlist=("README.md", "pom.xml", "src/main/java"),
            provider_disclosure_policy=(
                ENGINEERING_AGENT_DISCLOSURE_POLICY_REF
            ),
        )
        attempt_factory = EngineeringChatProviderAttemptFactory(
            plan=plan,
            evidence_tool_configuration_digest=evidence_tools.digest,
            primary=primary,
            fallback=fallback,
        )
        prepared = prepare_engineering_chat_provider_launcher(
            binding=self.binding,
            product_tree="c" * 40,
            evidence_tools=evidence_tools,
            primary_configuration=self.ark_configuration,
            fallback_configuration=self.deepseek_configuration,
            primary_session_authority=self.ark_authority,
            fallback_session_authority=self.deepseek_authority,
            route_plan=plan,
            attempt_factory=attempt_factory,
            checked_at=self.now,
        )

        self.assertIs(primary.driver, ark.model_boundary)
        self.assertIs(primary.reviewer, ark.model_boundary)
        self.assertIs(fallback.driver, deepseek.model_boundary)
        self.assertIs(fallback.reviewer, deepseek.model_boundary)
        self.assertIsNot(primary.driver, fallback.driver)
        self.assertNotEqual(
            primary.model_gateway_repository_ref,
            fallback.model_gateway_repository_ref,
        )
        self.assertEqual(prepared.service.statistics(), (0, 0))
        self.assertEqual(ark.model_boundary.audits, ())
        self.assertEqual(deepseek.model_boundary.audits, ())

    def test_peak_admission_rejects_before_credential_tls_or_http(self) -> None:
        peak = datetime(2026, 8, 25, 3, 30, tzinfo=timezone.utc)
        authority = EngineeringAgentSessionDisclosureAuthority.create(
            session_ref="engineering-chat-deepseek-peak-denial",
            product_candidate_digest=(
                self.deepseek_authority.product_candidate_digest
            ),
            chat_binding_digest=self.binding.digest,
            configuration=self.deepseek_configuration,
            maximum_turns=5,
            maximum_dispatches_per_turn=15,
            maximum_total_dispatches=75,
            authorized_at=peak - timedelta(hours=1),
            expires_at=peak + timedelta(hours=1),
            authorization_ref=(
                "codex-user-message:"
                + self.deepseek_authority.authorization_message_digest.value
            ),
            authorization_message_digest=(
                self.deepseek_authority.authorization_message_digest
            ),
        )
        controller = DeepSeekDispatchAdmissionController(
            plan=DeepSeekDispatchAdmissionPlan.create(
                run_type="LOCAL_RUNTIME_TEST",
                run_ref="test-peak-denial",
                turn_scope_digest=digest_of("peak-denial-turn-scope"),
                product_revision=self.binding.product_revision,
                source_revision=self.binding.repository_revision,
                session_ref=authority.session_ref,
                provider_configuration_digest=(
                    self.deepseek_configuration.digest
                ),
                model_ref=self.deepseek_configuration.model_ref,
                authorization_message_digest=(
                    authority.authorization_message_digest
                ),
                authorized_at=authority.authorized_at,
                expires_at=authority.expires_at,
                maximum_calls=authority.maximum_total_dispatches,
                maximum_input_tokens=10_000_000,
                maximum_output_tokens=75 * 8_192,
                maximum_duration_seconds=60,
                pricing_check=DeepSeekOfficialPricingCheck.create(
                    source=DEEPSEEK_PRICING_SOURCE,
                    checked_at=peak - timedelta(seconds=30),
                    content_digest=digest_of("peak-denial-pricing-check"),
                    content_summary="官方峰谷时段测试输入。",
                    effective_status=(
                        DeepSeekPricingEffectiveStatus.NOT_YET_EFFECTIVE
                    ),
                ),
            ),
            admitted_at=peak,
            clock=lambda: peak,
        )
        runtime = create_deepseek_engineering_chat_provider_model_runtime(
            repository=_UnusedModelGatewayRepository(),
            gateway_repository_ref="deepseek-gateway-db:sha256:peak-denial",
            binding=self.binding,
            provider_configuration=self.deepseek_provider,
            qualification=self.deepseek_qualification,
            configuration=self.deepseek_configuration,
            session_authority=authority,
            dispatch_admission_controller=controller,
            at=peak,
            clock=lambda: peak,
        )
        self.addCleanup(runtime.transport.close)
        manifest = AuthorizedInputManifest.create(
            capability_id="engineering-chat-test",
            strategy_ref="test@1",
            execution_stage="PRIMARY_AGENT",
            calling_module="tests",
            proposal_vocabulary_ref="test-output@1",
            items=(
                AuthorizedInputItem.create(
                    item_id="input",
                    schema_ref="text@1",
                    classification="INTERNAL",
                    purpose="test admission before transport",
                    authority_reference="test-authority",
                    disposition=InputDisposition.PROVIDED,
                    content="bounded input",
                ),
            ),
        )
        context = ModelExecutionContext(
            execution_envelope_ref="engineering-agent:test:1:peak",
            manifest=manifest,
            prompt_program_ref="test-prompt@1",
            rendering_contract_version="test-rendering@1",
            output_schema_ref="test-output@1",
            runtime_access_mode=RuntimeAccessMode.NO_EXTERNAL_ACCESS,
            platform_proposal_mode=PlatformProposalMode.NONE,
            requested_model_ref=self.deepseek_configuration.model_ref,
            provider_type=self.deepseek_configuration.provider_type,
            adapter_version=self.deepseek_configuration.adapter_version,
            provider_configuration_fingerprint=(
                self.deepseek_configuration.provider_configuration_fingerprint
            ),
            max_output_tokens=8_192,
            timeout_milliseconds=180_000,
            classification="INTERNAL",
            required_exact_fingerprint=True,
        )

        with self.assertRaises(DomainError):
            runtime.gateway.preflight(context)
        self.assertEqual(controller.public_audit()["authorized_dispatch_count"], 0)
        self.assertEqual(runtime.transport.credential_resolution_count, 0)
        self.assertEqual(runtime.transport.tls_handshake_attempt_count, 0)
        self.assertEqual(runtime.transport.http_dispatch_count, 0)

    def test_forged_or_drifted_qualification_is_rejected(self) -> None:
        forged = ArkChatConformanceQualification(
            result_ref=(
                f"{ARK_CHAT_CONFORMANCE_FIXTURE_ID}:"
                + digest_of("different-result").value
            ),
            result_digest=self.ark_qualification.result_digest,
            qualified_model_fingerprints=(
                self.ark_provider.qualified_model_identities
            ),
            adapter_version=self.ark_provider.adapter_version,
            provider_configuration_fingerprint=self.ark_provider.fingerprint,
            valid_until=self.valid_until,
        )

        with self.assertRaises(DomainError):
            engineering_chat_ark_model_configuration(
                provider_configuration=self.ark_provider,
                qualification=forged,
                at=self.now,
            )
        drifted = replace(
            self.ark_configuration,
            maximum_output_tokens=4_096,
        )
        with self.assertRaises(DomainError):
            create_ark_engineering_chat_provider_model_runtime(
                repository=_UnusedModelGatewayRepository(),
                gateway_repository_ref="ark-gateway-db:sha256:one",
                binding=self.binding,
                provider_configuration=self.ark_provider,
                qualification=self.ark_qualification,
                configuration=drifted,
                session_authority=self.ark_authority,
                at=self.now,
                clock=lambda: self.now,
            )

    def test_full_session_runtime_composes_without_attempt_or_source_read(self) -> None:
        ark = create_ark_engineering_chat_provider_model_runtime(
            repository=_UnusedModelGatewayRepository(),
            gateway_repository_ref="ark-gateway-db:sha256:one",
            binding=self.binding,
            provider_configuration=self.ark_provider,
            qualification=self.ark_qualification,
            configuration=self.ark_configuration,
            session_authority=self.ark_authority,
            at=self.now,
            clock=lambda: self.now,
        )
        deepseek = create_deepseek_engineering_chat_provider_model_runtime(
            repository=_UnusedModelGatewayRepository(),
            gateway_repository_ref="deepseek-gateway-db:sha256:two",
            binding=self.binding,
            provider_configuration=self.deepseek_provider,
            qualification=self.deepseek_qualification,
            configuration=self.deepseek_configuration,
            session_authority=self.deepseek_authority,
            dispatch_admission_controller=self._deepseek_admission(),
            at=self.now,
            clock=lambda: self.now,
        )
        self.addCleanup(deepseek.transport.close)
        primary_route = self._route(
            ordinal=1,
            role=EngineeringProviderRouteRole.PREFERRED,
            configuration=self.ark_configuration,
            authority=self.ark_authority,
        )
        fallback_route = self._route(
            ordinal=2,
            role=EngineeringProviderRouteRole.FALLBACK,
            configuration=self.deepseek_configuration,
            authority=self.deepseek_authority,
        )
        plan = EngineeringProviderRoutePlan.create(
            binding=self.binding,
            preferred=primary_route,
            fallback=fallback_route,
        )
        binding_id = StableId("binding_" + "2" * 32)
        profile = LocalGitEvidenceClassProfile.create(
            profile_ref=self.binding.source_profile_ref,
            binding_id=binding_id,
            evidence_class_paths={
                EngineeringEvidenceClass.SOURCE: ("src/main/java",),
                EngineeringEvidenceClass.REPOSITORY_DOCUMENT: ("README.md",),
                EngineeringEvidenceClass.BUILD_CONFIGURATION: ("pom.xml",),
                EngineeringEvidenceClass.TEST: ("src/test/java",),
            },
        )
        evidence_tools = EngineeringAgentEvidenceToolConfiguration.create(
            project_name=self.binding.project_name,
            response_language="zh-CN",
            repository_id=StableId("repository_" + "1" * 32),
            binding_id=binding_id,
            repository_revision=self.binding.repository_revision,
            source_profile_ref=profile.profile_ref,
            source_profile_digest=profile.profile_digest,
            world_model_read_authority_digest=(
                self.binding.world_model_authority_digest
            ),
            source_allowlist=(
                "README.md",
                "pom.xml",
                "src/main/java",
                "src/test/java",
            ),
            provider_disclosure_policy=(
                ENGINEERING_AGENT_DISCLOSURE_POLICY_REF
            ),
        )
        cognition = _UnusedCognitionProjector(
            authority=self.binding.world_model_authority_digest,
            revision=self.binding.repository_revision,
            binding_id=binding_id,
        )
        with TemporaryDirectory() as directory:
            worker = LocalGitRetrievalWorker(
                Path(directory),
                repository_id=evidence_tools.repository_id,
                binding_id=binding_id,
                source_profile=profile,
            )
            prepared = prepare_engineering_chat_session_runtime(
                binding=self.binding,
                product_tree="c" * 40,
                evidence_tools=evidence_tools,
                cognition_projector=cognition,
                source_broker=SourceBroker(source_profile=profile),
                retrieval_worker=worker,
                primary_provider_runtime=ark,
                fallback_provider_runtime=deepseek,
                route_plan=plan,
                checked_at=self.now,
            )
            drifted_profile = LocalGitEvidenceClassProfile.create(
                profile_ref=profile.profile_ref,
                binding_id=binding_id,
                evidence_class_paths={
                    EngineeringEvidenceClass.SOURCE: ("src/main/java",),
                },
            )
            with self.assertRaises(DomainError):
                EngineeringChatEvidenceToolFactory(
                    binding=self.binding,
                    configuration=evidence_tools,
                    cognition_projector=cognition,
                    source_broker=SourceBroker(
                        source_profile=drifted_profile
                    ),
                    retrieval_worker=worker,
                )
            with self.assertRaises(DomainError):
                prepare_engineering_chat_session_runtime(
                    binding=self.binding,
                    product_tree="c" * 40,
                    evidence_tools=evidence_tools,
                    cognition_projector=cognition,
                    source_broker=SourceBroker(source_profile=profile),
                    retrieval_worker=worker,
                    primary_provider_runtime=replace(
                        ark,
                        provider_dispatch_count_at_preparation=1,
                    ),
                    fallback_provider_runtime=deepseek,
                    route_plan=plan,
                    checked_at=self.now,
                )

        self.assertEqual(
            prepared.receipt.status, ENGINEERING_CHAT_SESSION_RUNTIME_STATUS
        )
        self.assertEqual(prepared.evidence_tool_factory.created_tool_count, 0)
        self.assertEqual(cognition.calls, 0)
        self.assertFalse(prepared.receipt.artifact_session_config_loaded)
        self.assertFalse(
            prepared.receipt.attempt_runtime_created_at_preparation
        )
        self.assertFalse(
            prepared.receipt.source_read_performed_at_preparation
        )
        self.assertFalse(
            prepared.receipt.credential_resolved_at_preparation
        )
        self.assertEqual(
            prepared.receipt.provider_dispatch_count_at_preparation, 0
        )
        self.assertFalse(prepared.receipt.listener_started_at_preparation)
        self.assertEqual(prepared.launcher.service.statistics(), (0, 0))
        self.assertEqual(ark.model_boundary.audits, ())
        self.assertEqual(deepseek.model_boundary.audits, ())
        status = json.dumps(prepared.receipt.public_status(), sort_keys=True)
        self.assertNotIn("ITER010_TEST_ARK_KEY", status)
        self.assertNotIn("ITER010_TEST_DEEPSEEK_KEY", status)
        self.assertNotIn("secret_reference", status)

    def test_session_runtime_rejects_drifted_cognition_before_attempt(self) -> None:
        binding_id = StableId("binding_" + "2" * 32)
        evidence_tools = EngineeringAgentEvidenceToolConfiguration.create(
            project_name=self.binding.project_name,
            response_language="zh-CN",
            repository_id=StableId("repository_" + "1" * 32),
            binding_id=binding_id,
            repository_revision=self.binding.repository_revision,
            source_profile_ref=self.binding.source_profile_ref,
            source_profile_digest=digest_of("source-profile"),
            world_model_read_authority_digest=(
                self.binding.world_model_authority_digest
            ),
            source_allowlist=("src/main/java",),
            provider_disclosure_policy=(
                ENGINEERING_AGENT_DISCLOSURE_POLICY_REF
            ),
        )
        cognition = _UnusedCognitionProjector(
            authority=digest_of("different-world-model"),
            revision=self.binding.repository_revision,
            binding_id=binding_id,
        )

        with self.assertRaises(DomainError):
            EngineeringChatEvidenceToolFactory(
                binding=self.binding,
                configuration=evidence_tools,
                cognition_projector=cognition,
                source_broker=_UnusedSourceBroker(),
                retrieval_worker=_UnusedRetrievalWorker(),
            )
        self.assertEqual(cognition.calls, 0)

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


if __name__ == "__main__":
    unittest.main()
