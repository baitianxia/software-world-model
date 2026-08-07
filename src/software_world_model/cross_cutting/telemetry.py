"""Minimal structured runtime telemetry contract."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from .identifiers import Digest, StableId


@dataclass(frozen=True, slots=True)
class TelemetryMetric:
    name: str
    value: int
    unit: str

    def __post_init__(self) -> None:
        if not self.name or not self.unit or self.value < 0:
            raise ValueError("telemetry metric requires a name, unit, and non-negative value")


@dataclass(frozen=True, slots=True)
class EstimatedCost:
    currency: str
    amount_microunits: int
    pricing_reference: str

    def __post_init__(self) -> None:
        if not self.currency or not self.pricing_reference or self.amount_microunits < 0:
            raise ValueError("estimated cost fields are invalid")


@dataclass(frozen=True, slots=True)
class RuntimeTelemetryEvent:
    event_id: StableId
    owner: str
    operation: str
    outcome: str
    correlation_reference: str
    causation_reference: str
    authority_references: tuple[str, ...]
    metrics: tuple[TelemetryMetric, ...]
    estimated_cost: EstimatedCost | None
    cost_status: str
    classification: str
    occurred_at: datetime
    digest: Digest


class TelemetryRecorder(Protocol):
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
    ) -> RuntimeTelemetryEvent | None: ...


class NullTelemetryRecorder:
    def record(self, **_: object) -> None:
        return None
