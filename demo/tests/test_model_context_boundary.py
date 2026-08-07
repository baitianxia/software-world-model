from __future__ import annotations

import unittest

from swm_demo.model_gateway import ModelGateway, ModelPhase


class _Provider:
    provider_name = "context-boundary-test"
    model_name = "recording-double"
    model_version = "1"

    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, object]]] = []

    def invoke(
        self, capability: str, payload: dict[str, object]
    ) -> dict[str, object]:
        self.calls.append((capability, payload))
        return {"answer": "ok"}


class ModelContextBoundaryTest(unittest.TestCase):
    def setUp(self) -> None:
        self.provider = _Provider()
        self.gateway = ModelGateway(self.provider)

    def test_capability_cannot_run_in_another_phase_context(self) -> None:
        context = self.gateway.open_context("task:phase", ModelPhase.ANSWER)

        with self.assertRaisesRegex(ValueError, "requires INVESTIGATION context"):
            self.gateway.invoke(
                "propose-knowledge-candidates", {}, context=context
            )

        self.assertEqual([], self.provider.calls)

    def test_registered_capability_requires_an_explicit_context(self) -> None:
        with self.assertRaisesRegex(
            ValueError, "draft-answer requires an explicit ANSWER context"
        ):
            self.gateway.invoke("draft-answer", {"claims": []})

        self.assertEqual([], self.provider.calls)

    def test_closed_context_cannot_be_reused(self) -> None:
        context = self.gateway.open_context("task:closed", ModelPhase.ANSWER)
        self.gateway.close_context(context)

        with self.assertRaisesRegex(ValueError, "model context is closed"):
            self.gateway.invoke("draft-answer", {"claims": []}, context=context)

        self.assertEqual([], self.provider.calls)

    def test_answer_context_rejects_nested_investigation_content(self) -> None:
        context = self.gateway.open_context("task:isolation", ModelPhase.ANSWER)

        with self.assertRaisesRegex(
            ValueError, "answer context contains investigation-only fields"
        ):
            self.gateway.invoke(
                "draft-answer",
                {
                    "claims": ["formal proposition"],
                    "debug": {"evidence_quote": "raw source text"},
                },
                context=context,
            )

        self.assertEqual([], self.provider.calls)

    def test_answer_context_accepts_only_formal_claim_payload(self) -> None:
        context = self.gateway.open_context("task:formal", ModelPhase.ANSWER)

        result = self.gateway.invoke(
            "draft-answer",
            {
                "requirement_id": "requirement:1",
                "assessment_id": "assessment:1",
                "claims": ["formal proposition"],
            },
            context=context,
        )

        self.assertEqual("ok", result.output["answer"])
        self.assertEqual(1, len(self.provider.calls))


if __name__ == "__main__":
    unittest.main()
