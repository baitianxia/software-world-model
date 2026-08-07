from __future__ import annotations

from dataclasses import FrozenInstanceError
import unittest

from swm_demo.agent_contract import (
    GAP,
    SATISFIED,
    KnowledgeNeed,
    KnowledgeRequirement,
    KnowledgeSufficiencyAssessment,
    KnowledgeSufficiencyItem,
)
from swm_demo.knowledge_requirement import FACT, INFERENCE, FormalKnowledgeReference


def _formal_reference(kind: str, reference_id: str) -> FormalKnowledgeReference:
    return FormalKnowledgeReference(kind, reference_id)


def _requirement() -> KnowledgeRequirement:
    return KnowledgeRequirement(
        requirement_id="knowledge-requirement:1",
        task_id="agent-task:1",
        scope_id="system:mall",
        knowledge_context_reference="revision:1",
        needs=(
            KnowledgeNeed(
                "need:entry",
                "Which request entry point handles the task?",
                "A formal endpoint relation identifies the entry and its composite path evidence.",
            ),
            KnowledgeNeed(
                "need:flow",
                "Which formal relations establish the downstream call chain?",
                "Every reported hop has a formal Fact and all ambiguous alternatives are addressed.",
            ),
        ),
        formation_model_call_id="model-call:requirement",
    )


class KnowledgeRequirementTest(unittest.TestCase):
    def test_requirement_is_immutable_and_needs_are_unique(self) -> None:
        requirement = _requirement()
        with self.assertRaises(FrozenInstanceError):
            requirement.scope_id = "system:changed"  # type: ignore[misc]

        with self.assertRaisesRegex(ValueError, "need_id values must be unique"):
            KnowledgeRequirement(
                requirement_id="knowledge-requirement:duplicate",
                task_id="agent-task:1",
                scope_id="system:mall",
                knowledge_context_reference="revision:1",
                needs=(
                    KnowledgeNeed("need:same", "First question", "First criterion"),
                    KnowledgeNeed("need:same", "Second question", "Second criterion"),
                ),
            )

    def test_complete_is_mechanically_derived_from_all_items(self) -> None:
        requirement = _requirement()
        complete = KnowledgeSufficiencyAssessment(
            assessment_id="knowledge-assessment:complete",
            requirement=requirement,
            snapshot_id="snapshot:1",
            knowledge_context_reference="revision:1",
            items=(
                KnowledgeSufficiencyItem(
                    "need:entry", SATISFIED, (_formal_reference(FACT, "fact:controller"),)
                ),
                KnowledgeSufficiencyItem(
                    "need:flow",
                    SATISFIED,
                    (_formal_reference(FACT, "fact:calls-service"),),
                ),
            ),
        )
        self.assertTrue(complete.complete)
        self.assertEqual(requirement.requirement_id, complete.requirement_id)
        self.assertEqual(
            ("fact:controller",),
            complete.items[0].formal_knowledge_reference_ids,
        )

        gap = KnowledgeSufficiencyAssessment(
            assessment_id="knowledge-assessment:gap",
            requirement=requirement,
            snapshot_id="snapshot:1",
            knowledge_context_reference="revision:1",
            items=(
                KnowledgeSufficiencyItem(
                    "need:entry", SATISFIED, (_formal_reference(FACT, "fact:controller"),)
                ),
                KnowledgeSufficiencyItem(
                    "need:flow", GAP, (), "downstream relation is absent"
                ),
            ),
        )
        self.assertFalse(gap.complete)

    def test_satisfied_item_requires_formal_knowledge_references(self) -> None:
        with self.assertRaisesRegex(ValueError, "must cite formal knowledge"):
            KnowledgeSufficiencyItem("need:entry", SATISFIED)

    def test_formal_knowledge_references_require_valid_kind_and_unique_pair(self) -> None:
        with self.assertRaisesRegex(ValueError, "kind must be one of"):
            FormalKnowledgeReference("EVIDENCE", "evidence:source")
        with self.assertRaisesRegex(ValueError, "reference_id must not be empty"):
            FormalKnowledgeReference(FACT, " ")
        with self.assertRaisesRegex(ValueError, "unique by kind and reference_id"):
            KnowledgeSufficiencyItem(
                "need:entry",
                SATISFIED,
                (
                    _formal_reference(FACT, "fact:controller"),
                    _formal_reference(FACT, "fact:controller"),
                ),
            )
        item = KnowledgeSufficiencyItem("need:gap", GAP)
        self.assertEqual((), item.formal_knowledge_references)

    def test_assessment_must_map_every_need_exactly_once(self) -> None:
        requirement = _requirement()
        with self.assertRaisesRegex(ValueError, "missing=.*need:flow"):
            KnowledgeSufficiencyAssessment(
                assessment_id="knowledge-assessment:missing",
                requirement=requirement,
                snapshot_id="snapshot:1",
                knowledge_context_reference="revision:1",
                items=(
                    KnowledgeSufficiencyItem(
                        "need:entry",
                        SATISFIED,
                        (_formal_reference(FACT, "fact:controller"),),
                    ),
                ),
            )

        with self.assertRaisesRegex(ValueError, "only once"):
            KnowledgeSufficiencyAssessment(
                assessment_id="knowledge-assessment:duplicate",
                requirement=requirement,
                snapshot_id="snapshot:1",
                knowledge_context_reference="revision:1",
                items=(
                    KnowledgeSufficiencyItem(
                        "need:entry",
                        SATISFIED,
                        (_formal_reference(FACT, "fact:controller"),),
                    ),
                    KnowledgeSufficiencyItem("need:entry", GAP),
                ),
            )

    def test_same_requirement_can_be_reassessed_on_a_new_snapshot(self) -> None:
        requirement = _requirement()
        items = (
            KnowledgeSufficiencyItem(
                "need:entry", SATISFIED, (_formal_reference(FACT, "fact:controller"),)
            ),
            KnowledgeSufficiencyItem("need:flow", GAP),
        )
        reassessed = KnowledgeSufficiencyAssessment(
            assessment_id="knowledge-assessment:new-snapshot",
            requirement=requirement,
            snapshot_id="snapshot:2",
            knowledge_context_reference="revision:1",
            items=items,
        )
        self.assertEqual("snapshot:2", reassessed.snapshot_id)

    def test_assessment_is_bound_to_requirement_context(self) -> None:
        requirement = _requirement()
        items = (
            KnowledgeSufficiencyItem(
                "need:entry", SATISFIED, (_formal_reference(INFERENCE, "inference:flow"),)
            ),
            KnowledgeSufficiencyItem("need:flow", GAP),
        )
        with self.assertRaisesRegex(ValueError, "same KnowledgeContext"):
            KnowledgeSufficiencyAssessment(
                assessment_id="knowledge-assessment:wrong-context",
                requirement=requirement,
                snapshot_id="snapshot:1",
                knowledge_context_reference="revision:other",
                items=items,
            )


if __name__ == "__main__":
    unittest.main()
