from __future__ import annotations

from datetime import datetime, timedelta, timezone
import unittest

from software_world_model.application_services import (
    CapabilityDefinition,
    CapabilityRegistry,
    LiveIntegrationPolicy,
    QualificationProof,
    StrategyActivationService,
    StrategyDefinition,
    StrategyKind,
)
from software_world_model.cross_cutting import (
    CorrelationRef,
    DomainError,
    ErrorCode,
    IdempotencyKey,
    Revision,
    StableId,
    digest_of,
)
from software_world_model.infrastructure import (
    SqliteDatabase,
    SqliteStrategyActivationRepository,
)


class SequenceIds:
    def __init__(self) -> None:
        self._next = 1

    def new(self, kind: str) -> StableId:
        value = self._next
        self._next += 1
        return StableId(f"{kind}_{value:032x}")


class StepClock:
    def __init__(self) -> None:
        self._value = datetime(2026, 8, 6, tzinfo=timezone.utc)

    def __call__(self) -> datetime:
        value = self._value
        self._value += timedelta(microseconds=1)
        return value


class DeterministicQualificationVerifier:
    def validate(self, proof: QualificationProof) -> bool:
        return proof.qualification_kind == "DETERMINISTIC_CONFORMANCE"


def qualification(strategy_id: str, strategy_version: str) -> QualificationProof:
    core = {
        "proof_ref": f"qualification:{strategy_id}:{strategy_version}",
        "capability_id": "scope.metadata.normalize",
        "capability_contract_version": "1.0.0",
        "strategy_id": strategy_id,
        "strategy_version": strategy_version,
        "result_ref": f"result:{strategy_id}:{strategy_version}",
        "validity_ref": f"validity:{strategy_id}:{strategy_version}:1",
        "qualification_kind": "DETERMINISTIC_CONFORMANCE",
    }
    return QualificationProof(**core, digest=digest_of(core))


class StrategyActivationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.database = SqliteDatabase()
        self.repository = SqliteStrategyActivationRepository(
            self.database, id_generator=SequenceIds()
        )
        self.registry = CapabilityRegistry()
        self.registry.register_capability(
            CapabilityDefinition(
                capability_id="scope.metadata.normalize",
                contract_version="1.0.0",
                purpose="Normalize display metadata",
                input_contract_digest=digest_of({"input": "metadata@1"}),
                output_contract_digest=digest_of({"output": "normalized-metadata@1"}),
            )
        )
        self.deterministic_v1 = StrategyDefinition(
            strategy_id="scope-metadata-deterministic",
            strategy_version="1.0.0",
            capability_id="scope.metadata.normalize",
            capability_contract_version="1.0.0",
            kind=StrategyKind.DETERMINISTIC,
            implementation_digest=digest_of({"implementation": "v1"}),
            requires_model=False,
        )
        self.deterministic_v2 = StrategyDefinition(
            strategy_id="scope-metadata-deterministic",
            strategy_version="1.1.0",
            capability_id="scope.metadata.normalize",
            capability_contract_version="1.0.0",
            kind=StrategyKind.DETERMINISTIC,
            implementation_digest=digest_of({"implementation": "v2"}),
            requires_model=False,
        )
        self.model_strategy = StrategyDefinition(
            strategy_id="scope-metadata-model",
            strategy_version="1.0.0",
            capability_id="scope.metadata.normalize",
            capability_contract_version="1.0.0",
            kind=StrategyKind.MODEL_PRIMARY,
            implementation_digest=digest_of({"implementation": "model-v1"}),
            requires_model=True,
        )
        for strategy in (
            self.deterministic_v1,
            self.deterministic_v2,
            self.model_strategy,
        ):
            self.registry.register_strategy(strategy)
        self.service = StrategyActivationService(
            self.repository,
            self.registry,
            DeterministicQualificationVerifier(),
            clock=StepClock(),
        )
        self.scope = {"environment": "offline-development"}

    def tearDown(self) -> None:
        self.database.close()

    def activation_arguments(self, strategy: StrategyDefinition, *, key: str):
        return {
            "capability_id": "scope.metadata.normalize",
            "capability_contract_version": "1.0.0",
            "activation_scope": self.scope,
            "strategy_id": strategy.strategy_id,
            "strategy_version": strategy.strategy_version,
            "qualification": qualification(strategy.strategy_id, strategy.strategy_version),
            "idempotency_key": IdempotencyKey(key),
            "actor": "test-operator",
            "reason": "activation contract test",
            "correlation_ref": CorrelationRef("activation-test"),
        }

    def test_deterministic_activation_replace_deactivate_and_reactivate_are_monotonic(self) -> None:
        activated = self.service.activate_strategy(
            expected_revision=None,
            **self.activation_arguments(self.deterministic_v1, key="activate-v1"),
        )
        resolved = self.service.resolve_strategy(
            capability_id="scope.metadata.normalize",
            capability_contract_version="1.0.0",
            activation_scope=self.scope,
        )
        replaced = self.service.replace_strategy(
            expected_revision=Revision(1),
            **self.activation_arguments(self.deterministic_v2, key="replace-v2"),
        )
        deactivated = self.service.deactivate_strategy(
            capability_id="scope.metadata.normalize",
            capability_contract_version="1.0.0",
            activation_scope=self.scope,
            expected_revision=Revision(2),
            idempotency_key=IdempotencyKey("deactivate"),
            actor="test-operator",
            reason="deactivate for test",
            correlation_ref=CorrelationRef("activation-test"),
        )

        self.assertEqual(activated.activation_revision, Revision(1))
        self.assertEqual(resolved.strategy, self.deterministic_v1)
        self.assertEqual(replaced.activation_revision, Revision(2))
        self.assertEqual(deactivated.activation_revision, Revision(3))
        with self.assertRaises(DomainError) as inactive:
            self.service.resolve_strategy(
                capability_id="scope.metadata.normalize",
                capability_contract_version="1.0.0",
                activation_scope=self.scope,
            )
        self.assertEqual(inactive.exception.code, ErrorCode.NO_ACTIVE_STRATEGY)

        reactivated = self.service.activate_strategy(
            expected_revision=Revision(3),
            **self.activation_arguments(self.deterministic_v1, key="reactivate-v1"),
        )
        self.assertEqual(reactivated.activation_revision, Revision(4))

    def test_model_strategy_cannot_activate_while_live_integration_is_held(self) -> None:
        with self.assertRaises(DomainError) as raised:
            self.service.activate_strategy(
                expected_revision=None,
                **self.activation_arguments(self.model_strategy, key="activate-model"),
            )

        self.assertEqual(raised.exception.code, ErrorCode.LIVE_INTEGRATION_HELD)
        with self.assertRaises(DomainError) as unresolved:
            self.service.resolve_strategy(
                capability_id="scope.metadata.normalize",
                capability_contract_version="1.0.0",
                activation_scope=self.scope,
            )
        self.assertEqual(unresolved.exception.code, ErrorCode.NO_ACTIVE_STRATEGY)

    def test_activation_replay_and_stale_revision_fail_closed(self) -> None:
        arguments = self.activation_arguments(self.deterministic_v1, key="activate-replay")
        activated = self.service.activate_strategy(expected_revision=None, **arguments)
        replay = self.service.activate_strategy(expected_revision=None, **arguments)
        self.assertEqual(replay, activated)

        with self.assertRaises(DomainError) as stale:
            self.service.replace_strategy(
                expected_revision=Revision(2),
                **self.activation_arguments(self.deterministic_v2, key="replace-stale"),
            )
        self.assertEqual(stale.exception.code, ErrorCode.ACTIVATION_CONFLICT)

        changed = dict(arguments)
        changed["reason"] = "different request"
        with self.assertRaises(DomainError) as mismatch:
            self.service.activate_strategy(expected_revision=None, **changed)
        self.assertEqual(mismatch.exception.code, ErrorCode.IDEMPOTENCY_MISMATCH)


if __name__ == "__main__":
    unittest.main()
