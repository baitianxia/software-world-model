"""Canonical file transport for exact capability-cognition snapshots."""

from __future__ import annotations

import json
import os
from pathlib import Path

from software_world_model.cross_cutting import Digest, DomainError, ErrorCode, canonical_json_bytes
from software_world_model.knowledge_engine.capability_cognition import CapabilityCognitionSnapshot


MAXIMUM_COGNITION_ARTIFACT_BYTES = 128 * 1024 * 1024


def write_new_capability_cognition(
    path: str | Path,
    snapshot: CapabilityCognitionSnapshot,
) -> Digest:
    target = _absolute(path)
    if not isinstance(snapshot, CapabilityCognitionSnapshot):
        raise DomainError(ErrorCode.INVALID_ARGUMENT, "cognition writer needs a snapshot")
    payload = canonical_json_bytes(snapshot.to_payload()) + b"\n"
    if len(payload) > MAXIMUM_COGNITION_ARTIFACT_BYTES:
        raise DomainError(ErrorCode.BUDGET_EXHAUSTED, "cognition artifact exceeds its file budget")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(target, flags, 0o600)
    except OSError as exc:
        raise DomainError(
            ErrorCode.CONTROL_STATE_DENIED,
            "cognition artifact path cannot be created exactly once",
        ) from exc
    try:
        written = 0
        while written < len(payload):
            written += os.write(descriptor, payload[written:])
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    return snapshot.digest


def load_capability_cognition(
    path: str | Path,
    *,
    expected_revision: str | None = None,
    expected_tree: str | None = None,
    expected_digest: Digest | None = None,
) -> CapabilityCognitionSnapshot:
    target = _absolute(path)
    if target.is_symlink() or not target.is_file():
        raise DomainError(ErrorCode.SOURCE_TARGET_NOT_FOUND, "cognition artifact is not a regular file")
    size = target.stat().st_size
    if not 1 <= size <= MAXIMUM_COGNITION_ARTIFACT_BYTES:
        raise DomainError(ErrorCode.BUDGET_EXHAUSTED, "cognition artifact file size is invalid")
    payload = target.read_bytes()
    try:
        document = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DomainError(ErrorCode.STRUCTURED_OUTPUT_INVALID, "cognition artifact is not canonical JSON") from exc
    if canonical_json_bytes(document) + b"\n" != payload:
        raise DomainError(ErrorCode.AUTHORITY_RECORD_INCONSISTENT, "cognition artifact bytes are not canonical")
    snapshot = CapabilityCognitionSnapshot.from_payload(document)
    if expected_revision is not None and snapshot.source_revision != expected_revision:
        raise DomainError(ErrorCode.SOURCE_REVISION_INCONSISTENT, "cognition artifact revision drifted")
    if expected_tree is not None and snapshot.source_tree != expected_tree:
        raise DomainError(ErrorCode.SOURCE_REVISION_INCONSISTENT, "cognition artifact tree drifted")
    if expected_digest is not None and snapshot.digest != expected_digest:
        raise DomainError(ErrorCode.AUTHORITY_RECORD_INCONSISTENT, "cognition artifact digest drifted")
    return snapshot


def _absolute(value: str | Path) -> Path:
    path = Path(value)
    if not path.is_absolute():
        raise DomainError(ErrorCode.INVALID_ARGUMENT, "cognition artifact path must be absolute")
    return path


__all__ = [
    "MAXIMUM_COGNITION_ARTIFACT_BYTES",
    "load_capability_cognition",
    "write_new_capability_cognition",
]
