"""Validated stable identifiers and optimistic concurrency values."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Protocol
import uuid


_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]{1,31}_[0-9a-f]{32}$")
_KIND_PATTERN = re.compile(r"^[a-z][a-z0-9_]{1,31}$")
_DIGEST_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")


@dataclass(frozen=True, slots=True)
class StableId:
    value: str

    def __post_init__(self) -> None:
        if not _ID_PATTERN.fullmatch(self.value):
            raise ValueError("stable ID must be a kind prefix followed by 32 lowercase hex digits")

    @property
    def kind(self) -> str:
        return self.value.rsplit("_", 1)[0]

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class Digest:
    value: str

    def __post_init__(self) -> None:
        if not _DIGEST_PATTERN.fullmatch(self.value):
            raise ValueError("digest must use the sha256:<64 lowercase hex> form")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class Revision:
    value: int

    def __post_init__(self) -> None:
        if isinstance(self.value, bool) or self.value < 1:
            raise ValueError("revision must be a positive integer")

    def next(self) -> "Revision":
        return Revision(self.value + 1)


def _validate_reference(value: str, label: str) -> None:
    if not value or value != value.strip():
        raise ValueError(f"{label} must be non-empty and cannot have surrounding whitespace")
    if len(value.encode("utf-8")) > 256:
        raise ValueError(f"{label} cannot exceed 256 UTF-8 bytes")


@dataclass(frozen=True, slots=True)
class IdempotencyKey:
    value: str

    def __post_init__(self) -> None:
        _validate_reference(self.value, "idempotency key")


@dataclass(frozen=True, slots=True)
class CorrelationRef:
    value: str

    def __post_init__(self) -> None:
        _validate_reference(self.value, "correlation reference")


class IdGenerator(Protocol):
    def new(self, kind: str) -> StableId: ...


class Uuid4IdGenerator:
    def new(self, kind: str) -> StableId:
        if not _KIND_PATTERN.fullmatch(kind):
            raise ValueError("ID kind must be a lowercase stable token")
        return StableId(f"{kind}_{uuid.uuid4().hex}")
