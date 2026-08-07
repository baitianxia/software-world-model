from __future__ import annotations

from datetime import datetime, timedelta, timezone
import unittest

from software_world_model.cross_cutting import EstimatedCost, StableId, TelemetryMetric
from software_world_model.infrastructure import SqliteDatabase, SqliteTelemetryRepository


class SequenceIds:
    def __init__(self) -> None:
        self.value = 0

    def new(self, kind: str) -> StableId:
        self.value += 1
        return StableId(f"{kind}_{self.value:032x}")


class StepClock:
    def __init__(self) -> None:
        self.value = datetime(2026, 8, 6, tzinfo=timezone.utc)

    def __call__(self) -> datetime:
        value = self.value
        self.value += timedelta(microseconds=1)
        return value


class TelemetryTests(unittest.TestCase):
    def test_event_is_append_only_idempotent_and_queryable_by_correlation(self) -> None:
        with SqliteDatabase() as database:
            repository = SqliteTelemetryRepository(
                database, id_generator=SequenceIds(), clock=StepClock()
            )
            arguments = {
                "owner": "ai-infrastructure",
                "operation": "model-call@1",
                "outcome": "COMPLETED",
                "correlation_reference": "task:1",
                "causation_reference": "manifest:1",
                "authority_references": ("model-call:1", "receipt:1"),
                "metrics": (
                    TelemetryMetric("input_tokens", 10, "tokens"),
                    TelemetryMetric("output_tokens", 4, "tokens"),
                ),
                "estimated_cost": EstimatedCost("USD", 125, "pricing:test@1"),
                "classification": "INTERNAL",
            }
            first = repository.record(**arguments)
            replay = repository.record(**arguments)
            loaded = repository.get(first.event_id)
            correlated = repository.list_by_correlation("task:1")

        self.assertEqual(replay.event_id, first.event_id)
        self.assertEqual(loaded.digest, first.digest)
        self.assertEqual(correlated, (first,))
        self.assertEqual(first.cost_status, "ESTIMATED")
        self.assertEqual(first.estimated_cost.amount_microunits, 125)

    def test_missing_price_is_explicitly_not_estimated(self) -> None:
        with SqliteDatabase() as database:
            repository = SqliteTelemetryRepository(database)
            event = repository.record(
                owner="source-integration",
                operation="local-git.read@1",
                outcome="COMPLETED",
                correlation_reference="task:2",
                causation_reference="operation:2",
                authority_references=("artifact:2",),
                metrics=(TelemetryMetric("source_bytes", 12, "bytes"),),
                classification="INTERNAL",
            )
        self.assertEqual(event.cost_status, "NOT_ESTIMATED")
        self.assertIsNone(event.estimated_cost)


if __name__ == "__main__":
    unittest.main()
