"""Isolated Citation Projector CLI.

This process accepts only a sealed Structure View Result and its disposable
observation store.  It intentionally composes no Bundle query, Knowledge
update, Source, model, network, or answer-return capability.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Sequence, TextIO

from software_world_model.application_services.citation_projection import (
    CitationProjection,
    CitationProjector,
)
from software_world_model.cross_cutting import DomainError
from software_world_model.infrastructure.file_citation_observation_store import (
    FileCitationObservationStoreReader,
    load_structure_view_result_seal,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="swm-citation-projector",
        description="Project allowlisted Evidence observations for browser display",
    )
    parser.add_argument("--sealed-result", required=True)
    parser.add_argument("--store", required=True)
    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> int:
    output = stdout or sys.stdout
    error_output = stderr or sys.stderr
    arguments = build_parser().parse_args(argv)
    try:
        result = load_structure_view_result_seal(arguments.sealed_result)
        projection = CitationProjector(
            FileCitationObservationStoreReader(arguments.store)
        ).project(result)
    except DomainError as error:
        json.dump(
            {
                "error": error.code.value,
                "message": error.message,
                "details": dict(error.details),
            },
            error_output,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        error_output.write("\n")
        return 2
    json.dump(
        citation_projection_payload(projection),
        output,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    output.write("\n")
    return 0


def citation_projection_payload(
    projection: CitationProjection,
) -> dict[str, object]:
    return {
        "result_id": projection.result_id.value,
        "result_digest": projection.result_digest.value,
        "store_id": projection.store_id.value,
        "store_manifest_digest": projection.store_manifest_digest.value,
        "citations": [
            {
                "evidence_id": item.evidence_id.value,
                "artifact_id": item.artifact_id.value,
                "source_context_id": item.source_context_id.value,
                "locator": item.locator,
                "byte_start": item.byte_start,
                "byte_end": item.byte_end,
                "observation": item.observation,
                "excerpt_digest": item.excerpt_digest.value,
                "evidence_digest": item.evidence_digest.value,
                "digest": item.digest.value,
            }
            for item in projection.citations
        ],
        "digest": projection.digest.value,
    }


if __name__ == "__main__":  # pragma: no cover - subprocess entry point
    raise SystemExit(main())


__all__ = ["build_parser", "citation_projection_payload", "main"]
