from __future__ import annotations

from datetime import datetime, timezone
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


_CONFORMANCE_REF = (
    "CC-ARK-CHAT-NO-TOOLS-001:"
    "sha256:c86aad995802b8dcf687fafcbaf36bccb02768ba55b40151ec9aa4704518cade"
)
_QUALIFICATION_REF = f"evaluation-only:{_CONFORMANCE_REF}"
_PROVIDER_FINGERPRINT = Digest(
    "sha256:420f553a3ce0075818550e08cb1351ce69eaf9871c5a0257aecf88b7b32b88fd"
)
_CAPABILITY_QUALIFICATION_REF = (
    "capability-evaluation:evaluation_result_916b9000db544e92921ec1bdc02a3bc2"
)
_CAPABILITY_QUALIFICATION_DIGEST = Digest(
    "sha256:005b1bf43c76a64d123b0184cdac1a9e844331896e7ede6279875881d9bcc62c"
)


class _FixtureGateway:
    def __init__(self, *, conformance_result_ref: str = _CONFORMANCE_REF) -> None:
        self.contexts: list[ModelExecutionContext] = []
        self._conformance_result_ref = conformance_result_ref

    def invoke(self, context: ModelExecutionContext) -> ModelGatewayResult:
        self.contexts.append(context)
        ordinal = len(self.contexts)
        now = datetime(2026, 8, 11, 1, ordinal, tzinfo=timezone.utc)
        request_digest = digest_of(
            {"manifest_digest": context.manifest.digest.value, "ordinal": ordinal}
        )
        response = AdapterResponse.create(
            provider_request_id=f"provider-request-{ordinal}",
            actual_model_fingerprint="glm-5.2",
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
            "conformance_result_ref": self._conformance_result_ref,
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
            conformance_result_ref=self._conformance_result_ref,
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
