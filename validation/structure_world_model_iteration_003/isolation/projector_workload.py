#!/usr/bin/env python3
"""Citation-only G2 workload executed inside the projector Seatbelt process."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from software_world_model.infrastructure.file_citation_observation_store import (
    FileCitationObservationStoreReader,
    load_structure_view_result_seal,
)
from software_world_model.application_services.citation_projection import (
    CitationProjector,
)
from software_world_model.cross_cutting import canonical_json_bytes
from software_world_model.interface.citation_projector_cli import (
    citation_projection_payload,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sealed-result", required=True)
    parser.add_argument("--store", required=True)
    parser.add_argument("--projection-output", required=True)
    return parser


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
        view = memoryview(payload)
        while view:
            view = view[os.write(descriptor, view) :]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def main(argv: list[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    seal = load_structure_view_result_seal(arguments.sealed_result)
    projection = CitationProjector(
        FileCitationObservationStoreReader(arguments.store)
    ).project(seal)
    _write_new(
        arguments.projection_output,
        canonical_json_bytes(citation_projection_payload(projection)),
    )
    print(
        canonical_json_bytes(
            {
                "status": "PASS",
                "result_id": projection.result_id.value,
                "store_id": projection.store_id.value,
                "citation_count": len(projection.citations),
                "projection_digest": projection.digest.value,
            }
        ).decode("utf-8")
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
