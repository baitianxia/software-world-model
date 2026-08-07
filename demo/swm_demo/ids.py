from __future__ import annotations

import hashlib


def stable_id(prefix: str, *parts: object) -> str:
    """Create a readable, deterministic identity without embedding source content."""

    canonical = "\x1f".join(str(part) for part in parts)
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:24]
    return f"{prefix}:{digest}"


def content_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()

