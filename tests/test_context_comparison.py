from __future__ import annotations

from dataclasses import replace
import unittest

from software_world_model.cross_cutting import DomainError, StableId, digest_of
from software_world_model.knowledge_engine.context_comparison import (
    StructureContextComparisonCoverageInput,
    StructureContextComparisonInput,
    StructureContextComparisonOutcome,
    StructureContextComparisonPurpose,
    StructureContextComparisonService,
)


class StructureContextComparisonTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = StructureContextComparisonService()
        self.base = self._input("1", context="base")
        self.target = self._input("2", context="target")

    def test_assessment_is_deterministic_and_preserves_input_order(self) -> None:
        first = self.service.assess(
            ordinal=0,
            purpose=StructureContextComparisonPurpose.SNAPSHOT_COMPARISON,
            base=self.base,
            target=self.target,
        )
        replay = self.service.assess(
            ordinal=0,
            purpose=StructureContextComparisonPurpose.SNAPSHOT_COMPARISON.value,
            base=self.base,
            target=self.target,
        )
        reverse = self.service.assess(
            ordinal=0,
            purpose=StructureContextComparisonPurpose.SNAPSHOT_COMPARISON,
            base=self.target,
            target=self.base,
        )

        self.assertEqual(first, replay)
        self.assertEqual(first.outcome, StructureContextComparisonOutcome.COMPATIBLE)
        self.assertEqual(first.base_snapshot_id, self.base.snapshot_id)
        self.assertEqual(first.target_snapshot_id, self.target.snapshot_id)
        self.assertEqual(reverse.base_snapshot_id, self.target.snapshot_id)
        self.assertEqual(reverse.target_snapshot_id, self.base.snapshot_id)
        self.assertNotEqual(first.digest, reverse.digest)

    def test_assessment_validity_is_rebuilt_from_exact_inputs(self) -> None:
        assessment = self.service.assess(
            ordinal=0,
            purpose=StructureContextComparisonPurpose.SNAPSHOT_COMPARISON,
            base=self.base,
            target=self.target,
        )
        assessment.require_valid(ordinal=0, base=self.base, target=self.target)

        with self.assertRaises(DomainError) as raised:
            replace(assessment, digest=digest_of({"tampered": True})).require_valid(
                ordinal=0,
                base=self.base,
                target=self.target,
            )
        self.assertEqual(
            raised.exception.details["reason_code"],
            "READ_SET_CONTEXT_ASSESSMENT_INVALID",
        )

    def test_scope_schema_and_coverage_basis_are_independent_gates(self) -> None:
        cases = (
            (
                replace(self.target, scope_id=StableId("scope_" + "9" * 32)),
                "READ_SET_SCOPE_MISMATCH",
            ),
            (
                replace(
                    self.target,
                    schema_ref="OTHER-STRUCTURE@1",
                    schema_digest=digest_of({"schema": "other"}),
                ),
                "READ_SET_SCHEMA_INCOMPARABLE",
            ),
            (
                replace(
                    self.target,
                    coverages=(
                        replace(
                            self.target.coverages[0],
                            comparison_basis_digest=digest_of(
                                {"basis": "different"}
                            ),
                        ),
                    ),
                ),
                "READ_SET_COVERAGE_INCOMPARABLE",
            ),
        )
        for target, reason_code in cases:
            with self.subTest(reason_code=reason_code):
                with self.assertRaises(DomainError) as raised:
                    self.service.assess(
                        ordinal=0,
                        purpose=StructureContextComparisonPurpose.SNAPSHOT_COMPARISON,
                        base=self.base,
                        target=target,
                    )
                self.assertEqual(raised.exception.details["reason_code"], reason_code)

    @staticmethod
    def _input(marker: str, *, context: str) -> StructureContextComparisonInput:
        value = StructureContextComparisonInput(
            scope_id=StableId("scope_" + "a" * 32),
            snapshot_id=StableId("structure_snapshot_" + marker * 32),
            snapshot_binding_digest=digest_of({"binding": marker}),
            schema_ref="TEST-STRUCTURE@1",
            schema_digest=digest_of({"schema": "test"}),
            coverages=(
                StructureContextComparisonCoverageInput(
                    coverage_root_id=StableId("coverage_root_" + "b" * 32),
                    knowledge_context_digest=digest_of({"context": context}),
                    comparison_basis_digest=digest_of({"basis": "same"}),
                ),
            ),
        )
        value.require_valid()
        return value


if __name__ == "__main__":
    unittest.main()
