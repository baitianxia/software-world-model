from __future__ import annotations

from datetime import datetime, timedelta, timezone
import unittest

from software_world_model.ai_infrastructure import (
    AdapterConformanceLevel,
    AdapterResponse,
    AuthorizedInputItem,
    AuthorizedInputManifest,
    InputDisposition,
    ModelCallState,
    ModelExecutionContext,
    ModelGateway,
    PlatformProposalMode,
    ProviderAdapterCapabilities,
    ProviderOutputRejected,
    ProviderOutcomeUnknown,
    ReplayClassification,
    RuntimeAccessMode,
)
from software_world_model.cross_cutting import Digest, DomainError, ErrorCode, StableId, digest_of
from software_world_model.infrastructure import SqliteDatabase, SqliteModelGatewayRepository


class SequenceIds:
    def __init__(self) -> None:
        self.next_value = 1

    def new(self, kind: str) -> StableId:
        value = self.next_value
        self.next_value += 1
        return StableId(f"{kind}_{value:032x}")


class StepClock:
    def __init__(self) -> None:
        self.value = datetime(2026, 8, 6, tzinfo=timezone.utc)

    def __call__(self) -> datetime:
        current = self.value
        self.value += timedelta(microseconds=1)
        return current


class RecordingAdapter:
    provider_type = "TEST_NO_TOOLS"
    adapter_version = "1"

    def __init__(
        self,
        *,
        isolated: bool = True,
        outcome_unknown: bool = False,
        conformance_level: AdapterConformanceLevel = AdapterConformanceLevel.OFFLINE_FIXTURE,
        qualified_fingerprints: tuple[str, ...] = (),
        replay_classification: ReplayClassification = ReplayClassification.PINNED,
        usage_complete: bool = True,
        reject_output: bool = False,
    ) -> None:
        self.capabilities = ProviderAdapterCapabilities(
            no_external_access=isolated,
            hidden_context_disabled=isolated,
            stateless_session=isolated,
            structured_output=True,
            actual_fingerprint_reported=True,
            conformance_level=conformance_level,
            conformance_result_ref="CC-TEST-OFFLINE",
            qualified_model_fingerprints=qualified_fingerprints,
        )
        self.outcome_unknown = outcome_unknown
        self.requests = []
        self.replay_classification = replay_classification
        self.usage_complete = usage_complete
        self.reject_output = reject_output

    def invoke(self, request):
        self.requests.append(request)
        if self.outcome_unknown:
            raise ProviderOutcomeUnknown("response connection lost")
        response = AdapterResponse.create(
            provider_request_id="test-request-1",
            actual_model_fingerprint="fixture-model@1",
            replay_classification=self.replay_classification,
            output_text='{"answer":"fixture"}',
            input_tokens=10,
            output_tokens=4,
            usage_complete=self.usage_complete,
            termination_reason="stop",
        )
        if self.reject_output:
            raise ProviderOutputRejected(
                DomainError(
                    ErrorCode.STRUCTURED_OUTPUT_INVALID,
                    "fixture output violates the closed schema",
                ),
                response,
            )
        return response


class ModelGatewayTests(unittest.TestCase):
    def setUp(self) -> None:
        self.database = SqliteDatabase()
        self.ids = SequenceIds()
        self.clock = StepClock()
        self.repository = SqliteModelGatewayRepository(self.database, id_generator=self.ids)

    def tearDown(self) -> None:
        self.database.close()

    def manifest(self):
        return AuthorizedInputManifest.create(
            capability_id="CAP-ANSWER-DRAFT@1",
            strategy_ref="fixture@1",
            execution_stage="ANSWER",
            calling_module="application-services",
            proposal_vocabulary_ref=None,
            items=(
                AuthorizedInputItem.create(
                    item_id="instruction",
                    schema_ref="text@1",
                    classification="INTERNAL",
                    purpose="instruction",
                    authority_reference="prompt:answer@1",
                    disposition=InputDisposition.PROVIDED,
                    content="Use only the supplied formal claims.",
                ),
                AuthorizedInputItem.create(
                    item_id="missing-context",
                    schema_ref="formal-claims@1",
                    classification="INTERNAL",
                    purpose="explicit absence",
                    authority_reference="snapshot:none",
                    disposition=InputDisposition.NOT_PROVIDED,
                ),
            ),
            id_generator=self.ids,
        )

    def context(self, manifest, *, access=RuntimeAccessMode.NO_EXTERNAL_ACCESS):
        return ModelExecutionContext(
            execution_envelope_ref="execution:test",
            manifest=manifest,
            prompt_program_ref="prompt:answer@1",
            rendering_contract_version="render@1",
            output_schema_ref="answer-proposal@1",
            runtime_access_mode=access,
            platform_proposal_mode=PlatformProposalMode.NONE,
            requested_model_ref="fixture-model@1",
            provider_type="TEST_NO_TOOLS",
            adapter_version="1",
            provider_configuration_fingerprint=digest_of({"fixture": 1}),
            max_output_tokens=128,
            timeout_milliseconds=1000,
            classification="INTERNAL",
            required_exact_fingerprint=True,
        )

    def test_request_is_rendered_only_from_provided_manifest_items(self) -> None:
        adapter = RecordingAdapter()
        gateway = ModelGateway(
            self.repository, (adapter,), id_generator=self.ids, clock=self.clock
        )
        result = gateway.invoke(self.context(self.manifest()))

        self.assertEqual(result.call.state, ModelCallState.COMPLETED)
        self.assertEqual(len(adapter.requests), 1)
        request = adapter.requests[0]
        self.assertEqual(request.tools, ())
        self.assertEqual(len(request.messages), 1)
        self.assertNotIn("missing-context", request.messages[0].content)
        self.assertEqual(result.call.provider_request_digest, request.digest)
        self.assertEqual(result.isolation_receipt.provider_request_digest, request.digest)

    def test_authorized_input_and_completed_output_are_recoverable_by_call_id(self) -> None:
        adapter = RecordingAdapter()
        gateway = ModelGateway(
            self.repository, (adapter,), id_generator=self.ids, clock=self.clock
        )
        original = self.manifest()

        result = gateway.invoke(self.context(original))
        recovered = gateway.recover_call(result.call.model_call_id)
        manifest = gateway.authorized_manifest(result.call.model_call_id)

        self.assertEqual(recovered.call, result.call)
        self.assertEqual(recovered.response, result.response)
        self.assertEqual(manifest.manifest_id, original.manifest_id)
        self.assertEqual(manifest.digest, original.digest)
        self.assertEqual(manifest.items, original.items)

    def test_offline_fixture_never_signs_production_eligibility(self) -> None:
        adapter = RecordingAdapter()
        result = ModelGateway(
            self.repository, (adapter,), id_generator=self.ids, clock=self.clock
        ).invoke(self.context(self.manifest()))

        self.assertFalse(result.eligibility.eligible_for_production_domain_output)
        self.assertEqual(
            result.eligibility.reason, "OFFLINE_FIXTURE_CANNOT_SIGN_LIVE_ELIGIBILITY"
        )

    def test_isolation_failure_prevents_dispatch_and_record_creation(self) -> None:
        adapter = RecordingAdapter(isolated=False)
        gateway = ModelGateway(
            self.repository, (adapter,), id_generator=self.ids, clock=self.clock
        )
        with self.assertRaises(DomainError) as raised:
            gateway.invoke(self.context(self.manifest()))
        self.assertEqual(raised.exception.code, ErrorCode.LIVE_INTEGRATION_HELD)
        self.assertEqual(adapter.requests, [])

    def test_provider_tools_mode_is_not_available_in_no_tools_slice(self) -> None:
        adapter = RecordingAdapter()
        gateway = ModelGateway(
            self.repository, (adapter,), id_generator=self.ids, clock=self.clock
        )
        with self.assertRaises(DomainError):
            gateway.invoke(
                self.context(self.manifest(), access=RuntimeAccessMode.DECLARED_PROVIDER_TOOL_SET)
            )
        self.assertEqual(adapter.requests, [])

    def test_unknown_outcome_is_persisted_without_zero_usage_claim(self) -> None:
        adapter = RecordingAdapter(outcome_unknown=True)
        gateway = ModelGateway(
            self.repository, (adapter,), id_generator=self.ids, clock=self.clock
        )
        result = gateway.invoke(self.context(self.manifest()))
        loaded = self.repository.get(result.call.model_call_id)

        self.assertEqual(result.call.state, ModelCallState.OUTCOME_UNKNOWN)
        self.assertEqual(loaded.state, ModelCallState.OUTCOME_UNKNOWN)
        self.assertFalse(loaded.usage_complete)
        self.assertIsNone(loaded.input_tokens)
        self.assertFalse(result.eligibility.eligible_for_production_domain_output)

    def test_rejected_output_preserves_completed_response_and_usage_for_audit(self) -> None:
        adapter = RecordingAdapter(
            conformance_level=AdapterConformanceLevel.LIVE_CURRENT,
            qualified_fingerprints=("fixture-model@1",),
            reject_output=True,
        )
        gateway = ModelGateway(
            self.repository, (adapter,), id_generator=self.ids, clock=self.clock
        )

        result = gateway.invoke(self.context(self.manifest()))
        replay = gateway.invoke(self.context(self.manifest()))

        self.assertEqual(result.call.state, ModelCallState.COMPLETED)
        self.assertEqual(
            result.call.failure_code, ErrorCode.STRUCTURED_OUTPUT_INVALID.value
        )
        self.assertIsNotNone(result.response)
        self.assertEqual(result.response.input_tokens, 10)
        self.assertFalse(result.eligibility.eligible_for_production_domain_output)
        self.assertEqual(
            result.eligibility.reason,
            "MODEL_OUTPUT_REJECTED_STRUCTURED_OUTPUT_INVALID",
        )
        self.assertTrue(replay.replayed)
        self.assertEqual(len(adapter.requests), 1)

    def test_completed_logical_model_call_replays_without_second_dispatch(self) -> None:
        adapter = RecordingAdapter()
        gateway = ModelGateway(
            self.repository, (adapter,), id_generator=self.ids, clock=self.clock
        )

        first = gateway.invoke(self.context(self.manifest()))
        replay = gateway.invoke(self.context(self.manifest()))

        self.assertEqual(len(adapter.requests), 1)
        self.assertFalse(first.replayed)
        self.assertTrue(replay.replayed)
        self.assertEqual(replay.call.model_call_id, first.call.model_call_id)
        self.assertEqual(replay.response.output_text, first.response.output_text)
        self.assertEqual(
            replay.isolation_receipt.receipt_id,
            first.isolation_receipt.receipt_id,
        )

    def test_logical_model_call_rejects_changed_authorized_input(self) -> None:
        adapter = RecordingAdapter()
        gateway = ModelGateway(
            self.repository, (adapter,), id_generator=self.ids, clock=self.clock
        )
        gateway.invoke(self.context(self.manifest()))
        changed = AuthorizedInputManifest.create(
            capability_id="answer",
            strategy_ref="fixture@1",
            execution_stage="DRAFT",
            calling_module="tests",
            proposal_vocabulary_ref=None,
            items=(
                AuthorizedInputItem.create(
                    item_id="provided",
                    schema_ref="text@1",
                    classification="INTERNAL",
                    purpose="answer",
                    authority_reference="task:1",
                    disposition=InputDisposition.PROVIDED,
                    content="different authorized content",
                ),
            ),
            id_generator=self.ids,
        )

        with self.assertRaises(DomainError) as raised:
            gateway.invoke(self.context(changed))

        self.assertEqual(raised.exception.code, ErrorCode.IDEMPOTENCY_MISMATCH)
        self.assertEqual(len(adapter.requests), 1)

    def test_unknown_logical_outcome_does_not_dispatch_again(self) -> None:
        adapter = RecordingAdapter(outcome_unknown=True)
        gateway = ModelGateway(
            self.repository, (adapter,), id_generator=self.ids, clock=self.clock
        )

        first = gateway.invoke(self.context(self.manifest()))
        replay = gateway.invoke(self.context(self.manifest()))

        self.assertEqual(first.call.state, ModelCallState.OUTCOME_UNKNOWN)
        self.assertEqual(replay.call.model_call_id, first.call.model_call_id)
        self.assertEqual(len(adapter.requests), 1)

    def test_live_result_requires_complete_usage_and_resolved_model_identity(self) -> None:
        incomplete = RecordingAdapter(
            conformance_level=AdapterConformanceLevel.LIVE_CURRENT,
            qualified_fingerprints=("fixture-model@1",),
            usage_complete=False,
        )
        incomplete_result = ModelGateway(
            self.repository, (incomplete,), id_generator=self.ids, clock=self.clock
        ).invoke(self.context(self.manifest()))
        self.assertFalse(incomplete_result.eligibility.eligible_for_production_domain_output)
        self.assertEqual(incomplete_result.eligibility.reason, "MODEL_USAGE_INCOMPLETE")

        with SqliteDatabase() as second_database:
            unresolved = RecordingAdapter(
                conformance_level=AdapterConformanceLevel.LIVE_CURRENT,
                qualified_fingerprints=("fixture-model@1",),
                replay_classification=ReplayClassification.UNRESOLVED_MUTABLE,
            )
            unresolved_result = ModelGateway(
                SqliteModelGatewayRepository(second_database), (unresolved,)
            ).invoke(self.context(self.manifest()))
        self.assertFalse(unresolved_result.eligibility.eligible_for_production_domain_output)
        self.assertEqual(
            unresolved_result.eligibility.reason,
            "MODEL_FINGERPRINT_UNRESOLVED_MUTABLE",
        )


if __name__ == "__main__":
    unittest.main()
