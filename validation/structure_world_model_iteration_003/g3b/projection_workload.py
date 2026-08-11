#!/usr/bin/env python3
"""Project one sealed G3b View citation set without any network capability."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import stat

from software_world_model.application_services.citation_projection import (
    CitationProjector,
)
from software_world_model.cross_cutting import Digest, StableId, canonical_json_bytes
from software_world_model.infrastructure.file_citation_observation_store import (
    FileCitationObservationStoreReader,
    load_structure_view_result_seal,
)
from software_world_model.interface.citation_projector_cli import (
    citation_projection_payload,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sealed-result", required=True)
    parser.add_argument("--store", required=True)
    parser.add_argument("--expected-result-id", required=True)
    parser.add_argument("--expected-seal-digest", required=True)
    parser.add_argument("--projection-output", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    expected_id = StableId(arguments.expected_result_id)
    expected_digest = Digest(arguments.expected_seal_digest)
    seal = load_structure_view_result_seal(arguments.sealed_result)
    if seal.result_id != expected_id or seal.digest != expected_digest:
        raise RuntimeError("Citation seal differs from its out-of-band anchors")
    projection = CitationProjector(
        FileCitationObservationStoreReader(arguments.store)
    ).project(seal)
    payload = {
        "schema": "swm.iter-003.g3b-citation-projection@1",
        "status": "PASS",
        "environment": "EVALUATION_ONLY",
        "result_id": projection.result_id.value,
        "seal_digest": seal.digest.value,
        "citation_projection": citation_projection_payload(projection),
        "network_operation_count": 0,
        "answer_return_port": False,
        "production_activation": "NOT_EXECUTED",
    }
    _write_new(arguments.projection_output, canonical_json_bytes(payload))
    print(canonical_json_bytes(payload).decode("utf-8"))
    return 0


def _write_new(path_text: str, payload: bytes) -> None:
    path = Path(path_text)
    if not path.is_absolute() or path.resolve(strict=False) != path:
        raise ValueError("projection output path must be canonical and absolute")
    if path.parent.resolve(strict=True) != path.parent:
        raise ValueError("projection output parent must be canonical")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags, 0o600)
    try:
        remaining = memoryview(payload)
        while remaining:
            remaining = remaining[os.write(descriptor, remaining) :]
        os.fsync(descriptor)
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise RuntimeError("projection output is not a regular file")
    finally:
        os.close(descriptor)


if __name__ == "__main__":
    raise SystemExit(main())
