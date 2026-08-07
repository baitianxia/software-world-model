"""Append-only, idempotent SQLite telemetry event store."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from typing import Callable

from software_world_model.cross_cutting import (
    Digest,
    EstimatedCost,
    IdGenerator,
    RuntimeTelemetryEvent,
    StableId,
    TelemetryMetric,
    Uuid4IdGenerator,
    canonical_json_bytes,
    digest_of,
)

from .sqlite_database import SqliteDatabase


_SCHEMA = """
CREATE TABLE IF NOT EXISTS x_runtime_telemetry_events (
    event_id TEXT PRIMARY KEY,
    identity_digest TEXT NOT NULL UNIQUE,
    owner TEXT NOT NULL,
    operation TEXT NOT NULL,
    outcome TEXT NOT NULL,
    correlation_reference TEXT NOT NULL,
    causation_reference TEXT NOT NULL,
    authority_references_json TEXT NOT NULL,
    metrics_json TEXT NOT NULL,
    estimated_cost_json TEXT,
    cost_status TEXT NOT NULL,
    classification TEXT NOT NULL,
    occurred_at TEXT NOT NULL,
    event_digest TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS x_telemetry_by_correlation
    ON x_runtime_telemetry_events(correlation_reference, occurred_at, event_id);
"""


class SqliteTelemetryRepository:
    def __init__(
        self,
        database: SqliteDatabase,
        *,
        id_generator: IdGenerator | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._database = database
        self._ids = id_generator or Uuid4IdGenerator()
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._database.executescript(_SCHEMA)

    def record(
        self,
        *,
        owner: str,
        operation: str,
        outcome: str,
        correlation_reference: str,
        causation_reference: str,
        authority_references: tuple[str, ...],
        metrics: tuple[TelemetryMetric, ...] = (),
        estimated_cost: EstimatedCost | None = None,
        classification: str,
    ) -> RuntimeTelemetryEvent:
        for value in (
            owner,
            operation,
            outcome,
            correlation_reference,
            causation_reference,
            classification,
        ):
            if not value or value != value.strip():
                raise ValueError("telemetry identity fields must be non-empty")
        cost_status = "ESTIMATED" if estimated_cost else "NOT_ESTIMATED"
        identity = {
            "owner": owner,
            "operation": operation,
            "outcome": outcome,
            "correlation_reference": correlation_reference,
            "causation_reference": causation_reference,
            "authority_references": authority_references,
            "metrics": metrics,
            "estimated_cost": estimated_cost,
            "cost_status": cost_status,
            "classification": classification,
        }
        identity_digest = digest_of(identity)
        with self._database.transaction() as connection:
            existing = connection.execute(
                "SELECT * FROM x_runtime_telemetry_events WHERE identity_digest = ?",
                (identity_digest.value,),
            ).fetchone()
            if existing is not None:
                return _event(existing)
            event_id = self._ids.new("telemetry_event")
            occurred_at = self._now()
            event_digest = digest_of(
                {
                    "event_id": event_id.value,
                    "identity_digest": identity_digest.value,
                    "occurred_at": occurred_at,
                }
            )
            connection.execute(
                """INSERT INTO x_runtime_telemetry_events
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    event_id.value,
                    identity_digest.value,
                    owner,
                    operation,
                    outcome,
                    correlation_reference,
                    causation_reference,
                    _json(authority_references),
                    _json(
                        tuple(
                            {"name": item.name, "value": item.value, "unit": item.unit}
                            for item in metrics
                        )
                    ),
                    _json(
                        {
                            "currency": estimated_cost.currency,
                            "amount_microunits": estimated_cost.amount_microunits,
                            "pricing_reference": estimated_cost.pricing_reference,
                        }
                    )
                    if estimated_cost
                    else None,
                    cost_status,
                    classification,
                    _time(occurred_at),
                    event_digest.value,
                ),
            )
            return _event(
                connection.execute(
                    "SELECT * FROM x_runtime_telemetry_events WHERE event_id = ?",
                    (event_id.value,),
                ).fetchone()
            )

    def get(self, event_id: StableId) -> RuntimeTelemetryEvent:
        with self._database.read() as connection:
            row = connection.execute(
                "SELECT * FROM x_runtime_telemetry_events WHERE event_id = ?", (event_id.value,)
            ).fetchone()
            if row is None:
                raise ValueError("telemetry event was not found")
            return _event(row)

    def list_by_correlation(self, correlation_reference: str) -> tuple[RuntimeTelemetryEvent, ...]:
        with self._database.read() as connection:
            return tuple(
                _event(row)
                for row in connection.execute(
                    """SELECT * FROM x_runtime_telemetry_events
                       WHERE correlation_reference = ? ORDER BY occurred_at, event_id""",
                    (correlation_reference,),
                ).fetchall()
            )

    def _now(self) -> datetime:
        value = self._clock()
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("telemetry clock must return an aware datetime")
        return value.astimezone(timezone.utc)


def _event(row) -> RuntimeTelemetryEvent:
    metrics = tuple(TelemetryMetric(**item) for item in json.loads(row["metrics_json"]))
    cost_value = json.loads(row["estimated_cost_json"]) if row["estimated_cost_json"] else None
    return RuntimeTelemetryEvent(
        event_id=StableId(row["event_id"]),
        owner=row["owner"],
        operation=row["operation"],
        outcome=row["outcome"],
        correlation_reference=row["correlation_reference"],
        causation_reference=row["causation_reference"],
        authority_references=tuple(json.loads(row["authority_references_json"])),
        metrics=metrics,
        estimated_cost=EstimatedCost(**cost_value) if cost_value else None,
        cost_status=row["cost_status"],
        classification=row["classification"],
        occurred_at=_parse_time(row["occurred_at"]),
        digest=Digest(row["event_digest"]),
    )


def _json(value: object) -> str:
    return canonical_json_bytes(value).decode("utf-8")


def _time(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="microseconds")


def _parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value).astimezone(timezone.utc)
