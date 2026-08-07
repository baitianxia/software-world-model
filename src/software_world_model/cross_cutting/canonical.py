"""Strict canonical encoding used by request and authority digests."""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
from typing import Any, Mapping

from .identifiers import Digest


class CanonicalizationError(ValueError):
    """Raised when a value has no supported canonical representation."""


def _normalize(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        raise CanonicalizationError("floating-point values are not canonical")
    if isinstance(value, bytes):
        raise CanonicalizationError("bytes require an explicit domain codec")
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise CanonicalizationError("datetime values must include a timezone")
        utc_value = value.astimezone(timezone.utc)
        return utc_value.isoformat(timespec="microseconds").replace("+00:00", "Z")
    if isinstance(value, Enum):
        return _normalize(value.value)
    if isinstance(value, Mapping):
        if any(not isinstance(key, str) for key in value):
            raise CanonicalizationError("canonical mappings require string keys")
        return {key: _normalize(value[key]) for key in sorted(value)}
    if isinstance(value, (list, tuple)):
        return [_normalize(item) for item in value]
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _normalize(getattr(value, field.name)) for field in fields(value)}
    raise CanonicalizationError(f"unsupported canonical value type: {type(value).__name__}")


def canonical_json_bytes(value: Any) -> bytes:
    """Encode a supported value using deterministic UTF-8 JSON bytes."""

    normalized = _normalize(value)
    return json.dumps(
        normalized,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def digest_of(value: Any) -> Digest:
    """Return the named SHA-256 digest of a canonical value."""

    payload = canonical_json_bytes(value)
    return Digest(f"sha256:{hashlib.sha256(payload).hexdigest()}")
