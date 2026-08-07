"""Cross-cutting value types shared without taking domain ownership."""

from .canonical import CanonicalizationError, canonical_json_bytes, digest_of
from .errors import DomainError, ErrorCode
from .identifiers import (
    CorrelationRef,
    Digest,
    IdGenerator,
    IdempotencyKey,
    Revision,
    StableId,
    Uuid4IdGenerator,
)
from .telemetry import (
    EstimatedCost,
    NullTelemetryRecorder,
    RuntimeTelemetryEvent,
    TelemetryMetric,
    TelemetryRecorder,
)

__all__ = [
    "CanonicalizationError",
    "CorrelationRef",
    "Digest",
    "DomainError",
    "ErrorCode",
    "EstimatedCost",
    "IdGenerator",
    "IdempotencyKey",
    "NullTelemetryRecorder",
    "Revision",
    "RuntimeTelemetryEvent",
    "StableId",
    "TelemetryMetric",
    "TelemetryRecorder",
    "Uuid4IdGenerator",
    "canonical_json_bytes",
    "digest_of",
]
