from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
import socket
import tempfile
import threading
import time
import unittest

from software_world_model.ai_infrastructure import (
    AdapterResponse,
    AuthorizedInputItem,
    AuthorizedInputManifest,
    InputDisposition,
    IsolationReceipt,
    ModelCallRecord,
    ModelCallState,
    ModelEgressGatewayPolicy,
    ModelEgressGatewayServer,
    ModelExecutionContext,
    ModelGatewayResult,
    ModelResultEligibility,
    PlatformProposalMode,
    ReplayClassification,
    RuntimeAccessMode,
    UnixSocketModelGatewayClient,
    QualifiedJavaModelEgressGatewayPolicy,
    QualifiedJavaSourceSemanticsModelEgressGatewayPolicy,
    BOUNDED_JAVA_SOURCE_SEMANTICS_MODEL_EGRESS_GATEWAY_POLICY_REF,
    JAVA_SOURCE_SEMANTICS_FIXED_WORLD_MODEL_PROPOSAL_CONTRACT,
    JAVA_SOURCE_SEMANTICS_WORLD_MODEL_PROPOSAL_CONTRACT,
    JAVA_WORLD_MODEL_PROPOSAL_CONTRACT,
    WorldModelCapabilityStrategy,
    WorldModelStrategyConfiguration,
)
from software_world_model.cross_cutting import (
    Digest,
    DomainError,
    ErrorCode,
    Revision,
    StableId,
    digest_of,
)
from validation.structure_world_model_iteration_008.capability.manifest import (
    available_operations_for_step,
    load_capability_inputs,
    sealed_step_input,
)


_CONFORMANCE_REF = (
    "CC-ARK-CHAT-NO-TOOLS-001:"
    "sha256:c86aad995802b8dcf687fafcbaf36bccb02768ba55b40151ec9aa4704518cade"
)
_QUALIFICATION_REF = f"evaluation-only:{_CONFORMANCE_REF}"
_PROVIDER_FINGERPRINT = Digest(
    "sha256:420f553a3ce0075818550e08cb1351ce69eaf9871c5a0257aecf88b7b32b88fd"
)
_DEEPSEEK_CONFORMANCE_REF = (
    "CC-DEEPSEEK-CHAT-NO-TOOLS-001:sha256:" + "a" * 64
)
_DEEPSEEK_QUALIFICATION_REF = f"evaluation-only:{_DEEPSEEK_CONFORMANCE_REF}"
_DEEPSEEK_PROVIDER_FINGERPRINT = Digest(
    "sha256:31dc8d9bd143ab4c5aee94a5e9cdafdbd19103a645ad40e30893348ab3c2640d"
)
_CAPABILITY_QUALIFICATION_REF = (
    "capability-evaluation:evaluation_result_916b9000db544e92921ec1bdc02a3bc2"
)
_CAPABILITY_QUALIFICATION_DIGEST = Digest(
    "sha256:005b1bf43c76a64d123b0184cdac1a9e844331896e7ede6279875881d9bcc62c"
)


class _FixtureGateway:
    def __init__(self, *, conformance_result_ref: str | None = None) -> None:
        self.contexts: list[ModelExecutionContext] = []
        self._conformance_result_ref = conformance_result_ref

    def invoke(self, context: ModelExecutionContext) -> ModelGatewayResult:
        self.contexts.append(context)
        ordinal = len(self.contexts)
        now = datetime(2026, 8, 11, 1, ordinal, tzinfo=timezone.utc)
        request_digest = digest_of(
            {"manifest_digest": context.manifest.digest.value, "ordinal": ordinal}
        )
        actual_model_fingerprint = (
            "deepseek-v4-pro"
            if context.provider_type == "DEEPSEEK"
            else "glm-5.2"
        )
        conformance_result_ref = self._conformance_result_ref or (
            _DEEPSEEK_CONFORMANCE_REF
            if context.provider_type == "DEEPSEEK"
            else _CONFORMANCE_REF
        )
        response = AdapterResponse.create(
            provider_request_id=f"provider-request-{ordinal}",
            actual_model_fingerprint=actual_model_fingerprint,
            replay_classification=ReplayClassification.PINNED,
            output_text='{"answer":"fixture"}',
            input_tokens=10,
            output_tokens=4,
            usage_complete=True,
            termination_reason="stop",
        )
        receipt_id = StableId(f"receipt_{ordinal:032x}")
        receipt_core = {
            "receipt_id": receipt_id.value,
            "manifest_digest": context.manifest.digest.value,
            "provider_request_digest": request_digest.value,
            "provider_type": context.provider_type,
            "adapter_version": context.adapter_version,
            "provider_configuration_fingerprint": (
                context.provider_configuration_fingerprint.value
            ),
            "runtime_access_mode": context.runtime_access_mode.value,
            "platform_proposal_mode": context.platform_proposal_mode.value,
            "conformance_result_ref": conformance_result_ref,
            "issued_at": now,
        }
        receipt = IsolationReceipt(
            receipt_id=receipt_id,
            manifest_digest=context.manifest.digest,
            provider_request_digest=request_digest,
            provider_type=context.provider_type,
            adapter_version=context.adapter_version,
            provider_configuration_fingerprint=(
                context.provider_configuration_fingerprint
            ),
            runtime_access_mode=context.runtime_access_mode,
            platform_proposal_mode=context.platform_proposal_mode,
            conformance_result_ref=conformance_result_ref,
            issued_at=now,
            digest=digest_of(receipt_core),
        )
        call_id = StableId(f"model_call_{ordinal:032x}")
        call = ModelCallRecord(
            model_call_id=call_id,
            revision=Revision(2),
            state=ModelCallState.COMPLETED,
            manifest_id=context.manifest.manifest_id,
            manifest_digest=context.manifest.digest,
            provider_request_digest=request_digest,
            isolation_receipt_id=receipt.receipt_id,
            isolation_receipt_digest=receipt.digest,
            provider_type=context.provider_type,
            adapter_version=context.adapter_version,
            requested_model_ref=context.requested_model_ref,
            actual_model_fingerprint=response.actual_model_fingerprint,
            provider_request_id=response.provider_request_id,
            output_digest=response.output_digest,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            usage_complete=response.usage_complete,
            failure_code=None,
            created_at=now,
            revised_at=now,
        )
        eligibility_core = {
            "eligible": True,
            "reason": "ELIGIBLE",
            "actual_model_fingerprint": response.actual_model_fingerprint,
            "isolation_receipt_id": receipt.receipt_id.value,
            "model_call_id": call_id.value,
        }
        eligibility = ModelResultEligibility(
            eligible_for_production_domain_output=True,
            reason="ELIGIBLE",
            actual_model_fingerprint=response.actual_model_fingerprint,
            isolation_receipt_id=receipt.receipt_id,
            model_call_id=call_id,
            digest=digest_of(eligibility_core),
        )
        return ModelGatewayResult(call, response, receipt, eligibility)


class ModelEgressGatewayTests(unittest.TestCase):
    def semantic_policy(
        self, *, valid_until=None
    ) -> QualifiedJavaSourceSemanticsModelEgressGatewayPolicy:
        return QualifiedJavaSourceSemanticsModelEgressGatewayPolicy(
            policy_ref=(
                "ITER-007-JAVA-SOURCE-SEMANTICS-MODEL-EGRESS-GATEWAY@1.0.2"
            ),
            policy_digest=Digest(
                "sha256:9e4e3dcbb0584b2574bfa71c5e31275e5496255e0ce41cdc5fc8f05e18e243b5"
            ),
            provider_type="VOLCENGINE_ARK",
            adapter_version="openai-chat-completions-no-tools@8",
            model_ref="glm-5-2-260617",
            provider_configuration_fingerprint=_PROVIDER_FINGERPRINT,
            endpoint=(
                "https://ark.cn-beijing.volces.com:443/"
                "api/coding/v3/chat/completions"
            ),
            credential_reference="env:ARK_API_KEY",
            conformance_result_ref=_CONFORMANCE_REF,
            capability_qualification_ref=(
                "capability-evaluation:evaluation_result_"
                "77777777777777777777777777777777"
            ),
            capability_qualification_digest=Digest("sha256:" + "7" * 64),
            closed_capability_result_digest=Digest("sha256:" + "8" * 64),
            qualification_valid_until=(
                valid_until or datetime.now(timezone.utc) + timedelta(days=1)
            ),
        )

    def bounded_semantic_policy(
        self, *, valid_until=None
    ) -> QualifiedJavaSourceSemanticsModelEgressGatewayPolicy:
        return QualifiedJavaSourceSemanticsModelEgressGatewayPolicy(
            policy_ref=(
                BOUNDED_JAVA_SOURCE_SEMANTICS_MODEL_EGRESS_GATEWAY_POLICY_REF
            ),
            policy_digest=Digest(
                "sha256:889afd1845f573ee0a9565d3fd2f6e69b6c824b72c20138c12cde93da7c407d0"
            ),
            provider_type="DEEPSEEK",
            adapter_version="deepseek-chat-completions-no-tools@5",
            model_ref="deepseek-v4-pro",
            provider_configuration_fingerprint=_DEEPSEEK_PROVIDER_FINGERPRINT,
            endpoint="https://api.deepseek.com/chat/completions",
            credential_reference="env:DEEPSEEK_API_KEY",
            conformance_result_ref=_DEEPSEEK_CONFORMANCE_REF,
            capability_qualification_ref=(
                "capability-evaluation:evaluation_result_"
                "88888888888888888888888888888888"
            ),
            capability_qualification_digest=Digest("sha256:" + "8" * 64),
            closed_capability_result_digest=Digest("sha256:" + "9" * 64),
            qualification_valid_until=(
                valid_until or datetime.now(timezone.utc) + timedelta(days=1)
            ),
            max_provider_calls=6,
        )

    def java_policy(self, *, valid_until=None) -> QualifiedJavaModelEgressGatewayPolicy:
        return QualifiedJavaModelEgressGatewayPolicy(
            policy_ref="ITER-006-JAVA-MODEL-EGRESS-GATEWAY@1.0.0",
            policy_digest=Digest(
                "sha256:63729ded35116ea47ee7fbe1c653b6a48e023e6307ffbace5e58c3fa778a7455"
            ),
            provider_type="VOLCENGINE_ARK",
            adapter_version="openai-chat-completions-no-tools@8",
            model_ref="glm-5-2-260617",
            provider_configuration_fingerprint=_PROVIDER_FINGERPRINT,
            endpoint=(
                "https://ark.cn-beijing.volces.com:443/"
                "api/coding/v3/chat/completions"
            ),
            credential_reference="env:ARK_API_KEY",
            conformance_result_ref=_CONFORMANCE_REF,
            capability_qualification_ref=(
                "capability-evaluation:evaluation_result_"
                "11111111111111111111111111111111"
            ),
            capability_qualification_digest=Digest("sha256:" + "2" * 64),
            closed_capability_result_digest=Digest("sha256:" + "3" * 64),
            qualification_valid_until=(
                valid_until or datetime.now(timezone.utc) + timedelta(days=1)
            ),
        )

    def policy(self) -> ModelEgressGatewayPolicy:
        return ModelEgressGatewayPolicy(
            policy_ref="ITER-003-MODEL-EGRESS-GATEWAY@1.0.0",
            policy_digest=Digest(
                "sha256:3e0bfcbf6f1b85d350db167d1bc71ff55f35a76546f15d4d7f14a871aa0326e0"
            ),
            provider_type="VOLCENGINE_ARK",
            adapter_version="openai-chat-completions-no-tools@8",
            model_ref="glm-5-2-260617",
            provider_configuration_fingerprint=_PROVIDER_FINGERPRINT,
            endpoint=(
                "https://ark.cn-beijing.volces.com:443/"
                "api/coding/v3/chat/completions"
            ),
            credential_reference="env:ARK_API_KEY",
            conformance_result_ref=_CONFORMANCE_REF,
            capability_qualification_ref=_CAPABILITY_QUALIFICATION_REF,
            capability_qualification_digest=_CAPABILITY_QUALIFICATION_DIGEST,
        )

    def context(
        self, *, provider_fingerprint=_PROVIDER_FINGERPRINT
    ) -> ModelExecutionContext:
        class Capture:
            context: ModelExecutionContext | None = None

            def invoke(self, context):
                self.context = context
                raise RuntimeError("captured")

        capture = Capture()
        strategy = WorldModelCapabilityStrategy(
            capture,
            WorldModelStrategyConfiguration(
                provider_type="VOLCENGINE_ARK",
                adapter_version="openai-chat-completions-no-tools@8",
                model_ref="glm-5-2-260617",
                provider_configuration_fingerprint=provider_fingerprint,
                qualification_ref=_QUALIFICATION_REF,
            ),
        )
        with self.assertRaisesRegex(RuntimeError, "captured"):
            strategy.propose(
                case_id="product:fixture",
                capability="GENERIC_QUERY_PLANNING",
                sealed_input={
                    "needs": ["inventory_left"],
                    "read_set": ["snapshot_left"],
                },
                available_operations=(
                    "inventory",
                    "all_simple_paths",
                    "ordered_snapshot_diff",
                ),
            )
        assert capture.context is not None
        return capture.context

    def java_context(self) -> ModelExecutionContext:
        class Capture:
            context: ModelExecutionContext | None = None

            def invoke(self, context):
                self.context = context
                raise RuntimeError("captured")

        capture = Capture()
        strategy = WorldModelCapabilityStrategy(
            capture,
            WorldModelStrategyConfiguration(
                provider_type="VOLCENGINE_ARK",
                adapter_version="openai-chat-completions-no-tools@8",
                model_ref="glm-5-2-260617",
                provider_configuration_fingerprint=_PROVIDER_FINGERPRINT,
                qualification_ref=_QUALIFICATION_REF,
            ),
            proposal_contract=JAVA_WORLD_MODEL_PROPOSAL_CONTRACT,
        )
        with self.assertRaisesRegex(RuntimeError, "captured"):
            strategy.propose(
                case_id="product:java-fixture",
                capability="GENERIC_QUERY_PLANNING",
                sealed_input={
                    "needs": ["method_inventory_left"],
                    "read_set": ["snapshot_java"],
                },
                available_operations=(
                    JAVA_WORLD_MODEL_PROPOSAL_CONTRACT.available_operations
                ),
            )
        assert capture.context is not None
        return capture.context

    def semantic_context(self, capability: str) -> ModelExecutionContext:
        class Capture:
            context: ModelExecutionContext | None = None

            def invoke(self, context):
                self.context = context
                raise RuntimeError("captured")

        capture = Capture()
        strategy = WorldModelCapabilityStrategy(
            capture,
            WorldModelStrategyConfiguration(
                provider_type="VOLCENGINE_ARK",
                adapter_version="openai-chat-completions-no-tools@8",
                model_ref="glm-5-2-260617",
                provider_configuration_fingerprint=_PROVIDER_FINGERPRINT,
                qualification_ref=_QUALIFICATION_REF,
            ),
            proposal_contract=(
                JAVA_SOURCE_SEMANTICS_FIXED_WORLD_MODEL_PROPOSAL_CONTRACT
            ),
        )
        available_operations = (
            JAVA_SOURCE_SEMANTICS_FIXED_WORLD_MODEL_PROPOSAL_CONTRACT.available_operations
            if capability == "IMPLEMENTATION_QUERY_PLANNING"
            else ()
        )
        with self.assertRaisesRegex(RuntimeError, "captured"):
            strategy.propose(
                case_id=f"product:semantic-{capability.casefold()}",
                capability=capability,
                sealed_input={"role": capability},
                available_operations=available_operations,
            )
        assert capture.context is not None
        return capture.context

    def bounded_semantic_context(
        self,
        capability: str,
        *,
        investigation_ordinal: int = 1,
        available_operations_override: tuple[str, ...] | None = None,
    ) -> ModelExecutionContext:
        class Capture:
            context: ModelExecutionContext | None = None

            def invoke(self, context):
                self.context = context
                raise RuntimeError("captured")

        capture = Capture()
        strategy = WorldModelCapabilityStrategy(
            capture,
            WorldModelStrategyConfiguration(
                provider_type="DEEPSEEK",
                adapter_version="deepseek-chat-completions-no-tools@5",
                model_ref="deepseek-v4-pro",
                provider_configuration_fingerprint=(
                    _DEEPSEEK_PROVIDER_FINGERPRINT
                ),
                qualification_ref=_DEEPSEEK_QUALIFICATION_REF,
            ),
            proposal_contract=(
                JAVA_SOURCE_SEMANTICS_WORLD_MODEL_PROPOSAL_CONTRACT
            ),
        )
        if capability == "IMPLEMENTATION_INVESTIGATION":
            suite, _ = load_capability_inputs()
            case = next(
                item
                for item in suite["cases"]
                if item["case_id"].endswith("BUDGET-EXHAUSTION-011")
            )
            step = case["steps"][min(investigation_ordinal, 4) - 1]
            sealed_input = sealed_step_input(suite, case, step)
            if investigation_ordinal <= 4:
                available_operations = available_operations_for_step(
                    suite, case, step
                )
            else:
                sealed_input["step_index"] = investigation_ordinal
                sealed_input["remaining_budget"] = {
                    "model_calls": 0,
                    "execution_steps": 0,
                }
                available_operations = ("FINISH",)
            if available_operations_override is not None:
                available_operations = available_operations_override
        else:
            sealed_input = {"role": capability}
            available_operations = ()
        with self.assertRaisesRegex(RuntimeError, "captured"):
            strategy.propose(
                case_id=f"product:bounded-{capability.casefold()}",
                capability=capability,
                sealed_input=sealed_input,
                available_operations=available_operations,
            )
        assert capture.context is not None
        return capture.context

    def test_java_policy_accepts_only_newly_qualified_contract(self) -> None:
        java_context = self.java_context()

        self.java_policy().validate_context(java_context)
        with self.assertRaises(DomainError) as legacy_rejection:
            self.policy().validate_context(java_context)
        with self.assertRaises(DomainError) as java_rejection:
            self.java_policy().validate_context(self.context())

        self.assertEqual(legacy_rejection.exception.code, ErrorCode.QUALIFICATION_INVALID)
        self.assertEqual(java_rejection.exception.code, ErrorCode.QUALIFICATION_INVALID)

    def test_expired_java_qualification_fails_before_dispatch(self) -> None:
        policy = self.java_policy(
            valid_until=datetime.now(timezone.utc) - timedelta(seconds=1)
        )

        with self.assertRaises(DomainError) as raised:
            policy.validate_context(self.java_context())

        self.assertEqual(raised.exception.code, ErrorCode.QUALIFICATION_INVALID)

    def test_java_source_semantics_policy_enforces_exact_three_call_order(self) -> None:
        policy = self.semantic_policy()
        for capability in (
            "IMPLEMENTATION_QUERY_PLANNING",
            "IMPLEMENTATION_ANSWER_DRAFTING",
            "IMPLEMENTATION_ANSWER_REVIEW",
        ):
            policy.validate_context(self.semantic_context(capability))

        with self.assertRaises(DomainError) as fourth:
            policy.validate_context(
                self.semantic_context("IMPLEMENTATION_ANSWER_REVIEW")
            )
        with self.assertRaises(DomainError) as out_of_order:
            self.semantic_policy().validate_context(
                self.semantic_context("IMPLEMENTATION_ANSWER_DRAFTING")
            )

        self.assertEqual(fourth.exception.code, ErrorCode.QUALIFICATION_INVALID)
        self.assertEqual(
            out_of_order.exception.code, ErrorCode.QUALIFICATION_INVALID
        )

    def test_bounded_semantics_policy_enforces_two_to_four_then_draft_review(self) -> None:
        policy = self.bounded_semantic_policy()
        with self.assertRaises(DomainError) as too_early:
            policy.validate_context(
                self.bounded_semantic_context("IMPLEMENTATION_ANSWER_DRAFTING")
            )

        policy.validate_context(
            self.bounded_semantic_context(
                "IMPLEMENTATION_INVESTIGATION", investigation_ordinal=1
            )
        )
        policy.validate_context(
            self.bounded_semantic_context(
                "IMPLEMENTATION_INVESTIGATION", investigation_ordinal=2
            )
        )
        policy.validate_context(
            self.bounded_semantic_context("IMPLEMENTATION_ANSWER_DRAFTING")
        )
        policy.validate_context(
            self.bounded_semantic_context("IMPLEMENTATION_ANSWER_REVIEW")
        )
        with self.assertRaises(DomainError) as after_review:
            policy.validate_context(
                self.bounded_semantic_context("IMPLEMENTATION_ANSWER_REVIEW")
            )

        maximum = self.bounded_semantic_policy()
        for ordinal in range(1, 5):
            maximum.validate_context(
                self.bounded_semantic_context(
                    "IMPLEMENTATION_INVESTIGATION",
                    investigation_ordinal=ordinal,
                )
            )
        with self.assertRaises(DomainError) as fifth_investigation:
            maximum.validate_context(
                self.bounded_semantic_context(
                    "IMPLEMENTATION_INVESTIGATION",
                    investigation_ordinal=5,
                )
            )

        self.assertEqual(too_early.exception.code, ErrorCode.QUALIFICATION_INVALID)
        self.assertEqual(after_review.exception.code, ErrorCode.QUALIFICATION_INVALID)
        self.assertEqual(
            fifth_investigation.exception.code,
            ErrorCode.QUALIFICATION_INVALID,
        )

    def test_bounded_semantics_policy_rejects_transition_expansion(self) -> None:
        context = self.bounded_semantic_context(
            "IMPLEMENTATION_INVESTIGATION",
            investigation_ordinal=1,
            available_operations_override=(
                JAVA_SOURCE_SEMANTICS_WORLD_MODEL_PROPOSAL_CONTRACT.available_operations
            ),
        )

        with self.assertRaises(DomainError) as raised:
            self.bounded_semantic_policy().validate_context(context)

        self.assertEqual(raised.exception.code, ErrorCode.QUALIFICATION_INVALID)

    def test_bounded_semantics_policy_binds_capability_selected_prompt(self) -> None:
        context = self.bounded_semantic_context(
            "IMPLEMENTATION_INVESTIGATION",
            investigation_ordinal=1,
        )
        instruction = context.manifest.items[0]
        self.assertEqual(
            instruction.transformation_ref,
            "capability-prompt-selection@1",
        )
        self.assertIn("IMPLEMENTATION_INVESTIGATION:", instruction.content)
        self.assertNotIn(
            "IMPLEMENTATION_ANSWER_DRAFTING:", instruction.content
        )
        self.assertNotIn("IMPLEMENTATION_ANSWER_REVIEW:", instruction.content)

        tampered_manifest = replace(
            context.manifest,
            items=(
                replace(instruction, transformation_ref="identity@1"),
                *context.manifest.items[1:],
            ),
        )
        with self.assertRaises(DomainError) as raised:
            self.bounded_semantic_policy().validate_context(
                replace(context, manifest=tampered_manifest)
            )

        self.assertEqual(raised.exception.code, ErrorCode.QUALIFICATION_INVALID)

    def test_bounded_policy_rejects_cross_provider_substitution(self) -> None:
        policy = self.bounded_semantic_policy()

        with self.assertRaises(DomainError) as raised:
            replace(
                policy,
                provider_type="VOLCENGINE_ARK",
                adapter_version="openai-chat-completions-no-tools@8",
                model_ref="glm-5-2-260617",
                provider_configuration_fingerprint=_PROVIDER_FINGERPRINT,
                endpoint=(
                    "https://ark.cn-beijing.volces.com:443/"
                    "api/coding/v3/chat/completions"
                ),
                credential_reference="env:ARK_API_KEY",
                conformance_result_ref=_CONFORMANCE_REF,
            )

        self.assertEqual(raised.exception.code, ErrorCode.QUALIFICATION_INVALID)

    def test_round_trip_binds_request_result_and_audits(self) -> None:
        fixture_gateway = _FixtureGateway()
        server_audits: list[dict[str, object]] = []
        with tempfile.TemporaryDirectory() as directory:
            socket_path = Path(directory).resolve() / "model-egress.sock"
            server = ModelEgressGatewayServer(
                socket_path,
                gateway=fixture_gateway,
                policy=self.policy(),
                audit_writer=lambda value: server_audits.append(dict(value)),
            )
            thread, failures = self._start_server(server, socket_path)
            client = UnixSocketModelGatewayClient(socket_path, timeout_seconds=2)

            result = client.invoke(self.context())
            thread.join(2)

            self.assertFalse(thread.is_alive())
            self.assertEqual(failures, [])
            self.assertEqual(result.call.state, ModelCallState.COMPLETED)
            self.assertEqual(result.response.output_text, '{"answer":"fixture"}')
            self.assertEqual(client.provider_call_count, 1)
            self.assertEqual(client.network_operation_count, 1)
            self.assertEqual(len(client.audits), 1)
            self.assertEqual(len(server_audits), 1)
            self.assertEqual(
                client.audits[0].response_digest.value,
                server_audits[0]["response_digest"],
            )
            self.assertFalse(socket_path.exists())

    def test_round_trip_uses_an_exact_prebound_listener(self) -> None:
        fixture_gateway = _FixtureGateway()
        with tempfile.TemporaryDirectory() as directory:
            socket_path = Path(directory).resolve() / "model-egress.sock"
            listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            listener.bind(str(socket_path))
            socket_path.chmod(0o600)
            listener.listen(1)
            server = ModelEgressGatewayServer(
                socket_path,
                gateway=fixture_gateway,
                policy=self.policy(),
                prebound_listener=listener,
            )
            thread, failures = self._start_server(server, socket_path)
            result = UnixSocketModelGatewayClient(
                socket_path, timeout_seconds=2
            ).invoke(self.context())
            thread.join(2)

            self.assertEqual(result.call.state, ModelCallState.COMPLETED)
            self.assertFalse(thread.is_alive())
            self.assertEqual(failures, [])
            self.assertFalse(socket_path.exists())

    def test_prebound_listener_must_match_the_exact_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            actual_path = root / "actual.sock"
            expected_path = root / "expected.sock"
            listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            listener.bind(str(actual_path))
            actual_path.chmod(0o600)
            listener.listen(1)
            server = ModelEgressGatewayServer(
                expected_path,
                gateway=_FixtureGateway(),
                policy=self.policy(),
                prebound_listener=listener,
            )

            with self.assertRaises(DomainError) as raised:
                server.serve(startup_timeout_seconds=0.01)

            self.assertEqual(raised.exception.code, ErrorCode.CONTROL_STATE_DENIED)
            self.assertEqual(listener.fileno(), -1)
            self.assertTrue(actual_path.exists())
            actual_path.unlink()

    def test_policy_drift_is_rejected_and_consumes_one_audited_call(self) -> None:
        fixture_gateway = _FixtureGateway()
        with tempfile.TemporaryDirectory() as directory:
            socket_path = Path(directory).resolve() / "model-egress.sock"
            server = ModelEgressGatewayServer(
                socket_path,
                gateway=fixture_gateway,
                policy=self.policy(),
            )
            thread, failures = self._start_server(server, socket_path)
            client = UnixSocketModelGatewayClient(socket_path, timeout_seconds=2)

            with self.assertRaises(DomainError) as raised:
                client.invoke(
                    self.context(provider_fingerprint=digest_of({"drift": True}))
                )
            thread.join(2)

            self.assertEqual(raised.exception.code, ErrorCode.LIVE_INTEGRATION_HELD)
            self.assertEqual(client.provider_call_count, 1)
            self.assertEqual(client.audits[0].model_call_state, "REJECTED")
            self.assertEqual(fixture_gateway.contexts, [])
            self.assertEqual(failures, [])

    def test_result_with_another_conformance_record_is_rejected(self) -> None:
        fixture_gateway = _FixtureGateway(conformance_result_ref="CC-OTHER")
        with tempfile.TemporaryDirectory() as directory:
            socket_path = Path(directory).resolve() / "model-egress.sock"
            server = ModelEgressGatewayServer(
                socket_path,
                gateway=fixture_gateway,
                policy=self.policy(),
            )
            thread, failures = self._start_server(server, socket_path)
            client = UnixSocketModelGatewayClient(socket_path, timeout_seconds=2)

            with self.assertRaises(DomainError):
                client.invoke(self.context())
            thread.join(2)

            self.assertEqual(client.audits[0].model_call_state, "REJECTED")
            self.assertEqual(len(fixture_gateway.contexts), 1)
            self.assertEqual(failures, [])

    def test_client_fuse_denies_a_sixth_call(self) -> None:
        fixture_gateway = _FixtureGateway()
        with tempfile.TemporaryDirectory() as directory:
            socket_path = Path(directory).resolve() / "model-egress.sock"
            server = ModelEgressGatewayServer(
                socket_path,
                gateway=fixture_gateway,
                policy=self.policy(),
            )
            thread, failures = self._start_server(server, socket_path)
            client = UnixSocketModelGatewayClient(socket_path, timeout_seconds=2)
            for _ in range(5):
                client.invoke(self.context())

            with self.assertRaises(DomainError) as raised:
                client.invoke(self.context())
            thread.join(2)

            self.assertEqual(raised.exception.code, ErrorCode.CONTROL_STATE_DENIED)
            self.assertEqual(client.provider_call_count, 5)
            self.assertEqual(len(fixture_gateway.contexts), 5)
            self.assertEqual(failures, [])

    def test_existing_socket_path_fails_closed_without_unlinking_it(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            socket_path = Path(directory).resolve() / "model-egress.sock"
            socket_path.write_text("do not replace", encoding="utf-8")
            server = ModelEgressGatewayServer(
                socket_path,
                gateway=_FixtureGateway(),
                policy=self.policy(),
            )

            with self.assertRaises(DomainError) as raised:
                server.serve(startup_timeout_seconds=0.01)

            self.assertEqual(raised.exception.code, ErrorCode.CONTROL_STATE_DENIED)
            self.assertEqual(
                socket_path.read_text(encoding="utf-8"), "do not replace"
            )

    @staticmethod
    def _start_server(server, socket_path: Path):
        failures: list[BaseException] = []

        def run() -> None:
            try:
                server.serve(
                    startup_timeout_seconds=2,
                    idle_timeout_seconds=0.05,
                )
            except BaseException as exc:  # pragma: no cover - asserted below
                failures.append(exc)

        thread = threading.Thread(target=run, daemon=True)
        thread.start()
        deadline = time.monotonic() + 2
        while not socket_path.exists() and thread.is_alive():
            if time.monotonic() >= deadline:
                break
            time.sleep(0.005)
        return thread, failures


if __name__ == "__main__":
    unittest.main()
