from __future__ import annotations

import unittest

from software_world_model.ai_infrastructure.model_execution_runtime import (
    LogicalModelExecutionRequest,
    ModelExecutionCoordinator,
)
from software_world_model.cross_cutting import Digest


class ModelExecutionRuntimeTests(unittest.TestCase):
    def test_public_result_is_provider_neutral_and_opaque(self) -> None:
        interaction = Digest("sha256:" + "1" * 64)
        coordinator = ModelExecutionCoordinator(
            runner=lambda payload: {"answer": payload, "provider": "must-stay-private"},
            dispatch_counter=lambda _result: 2,
        )

        result = coordinator.execute(
            LogicalModelExecutionRequest.create(
                interaction_digest=interaction,
                payload="question",
            )
        )

        self.assertEqual(result.interaction_digest, interaction)
        self.assertEqual(result.result["answer"], "question")
        self.assertEqual(result.dispatch_count, 2)
        self.assertTrue(result.execution_audit_ref)
        self.assertNotIn("route", result.execution_audit_ref)
        self.assertNotIn("provider", result.execution_audit_ref)

    def test_runner_can_be_swapped_without_changing_port_contract(self) -> None:
        interaction = Digest("sha256:" + "2" * 64)
        first = ModelExecutionCoordinator(runner=lambda _payload: "first")
        second = ModelExecutionCoordinator(runner=lambda _payload: "second")
        request = LogicalModelExecutionRequest.create(
            interaction_digest=interaction,
            payload=object(),
        )

        self.assertEqual(first.execute(request).result, "first")
        self.assertEqual(second.execute(request).result, "second")


if __name__ == "__main__":
    unittest.main()
