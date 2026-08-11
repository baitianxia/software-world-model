#!/usr/bin/env python3
"""Trusted one-way broker from authority Evidence to one disposable G3b Store."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import stat

from software_world_model.application_services.citation_projection import (
    CitationObservation,
)
from software_world_model.cross_cutting import canonical_json_bytes
from software_world_model.infrastructure.sqlite_database import SqliteDatabase
from software_world_model.infrastructure.sqlite_structure_knowledge_repository import (
    SqliteStructureKnowledgeRepository,
)
from software_world_model.infrastructure.file_citation_observation_store import (
    FileCitationObservationStoreWriter,
    load_structure_view_result_seal,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--authority-database", required=True)
    parser.add_argument("--sealed-result", required=True)
    parser.add_argument("--store-root", required=True)
    parser.add_argument("--summary-output", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    database_path = _existing_file(arguments.authority_database)
    seal_path = _existing_file(arguments.sealed_result)
    store_root = Path(arguments.store_root)
    if (
        not store_root.is_absolute()
        or store_root.resolve(strict=False) != store_root
        or store_root.exists()
        or store_root.parent.resolve(strict=True) != store_root.parent
    ):
        raise ValueError("disposable Citation Store target is unsafe")
    seal = load_structure_view_result_seal(seal_path)
    with SqliteDatabase(database_path) as database:
        owner = SqliteStructureKnowledgeRepository(database)
        observations = tuple(
            CitationObservation.from_evidence(
                owner.get_evidence(reference.evidence_id)
            )
            for reference in seal.evidence_allowlist
        )
    if tuple(item.reference for item in observations) != seal.evidence_allowlist:
        raise RuntimeError("authority observations differ from the sealed allowlist")
    receipt = FileCitationObservationStoreWriter(
        store_root
    ).create_disposable_store(result=seal, observations=observations)
    summary = {
        "schema": "swm.iter-003.g3b-citation-materialization@1",
        "status": "PASS",
        "environment": "EVALUATOR_ONLY",
        "result_id": seal.result_id.value,
        "seal_digest": seal.digest.value,
        "store_id": receipt.store_id.value,
        "store_manifest_digest": receipt.manifest_digest.value,
        "observation_count": receipt.observation_count,
        "answer_process_evidence_payload_access_count": 0,
        "projector_store_is_disposable": receipt.disposable,
        "projector_answer_return_port": False,
        "production_activation": "NOT_EXECUTED",
    }
    _write_new(arguments.summary_output, canonical_json_bytes(summary))
    print(canonical_json_bytes(summary).decode("utf-8"))
    return 0


def _existing_file(path_text: str) -> Path:
    path = Path(path_text)
    if (
        not path.is_absolute()
        or path.resolve(strict=True) != path
        or not path.is_file()
        or path.is_symlink()
    ):
        raise ValueError("input must be a canonical regular file")
    return path


def _write_new(path_text: str, payload: bytes) -> None:
    path = Path(path_text)
    if not path.is_absolute() or path.resolve(strict=False) != path:
        raise ValueError("summary output path must be canonical and absolute")
    if path.parent.resolve(strict=True) != path.parent:
        raise ValueError("summary output parent must be canonical")
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
            raise RuntimeError("summary output is not a regular file")
    finally:
        os.close(descriptor)


if __name__ == "__main__":
    raise SystemExit(main())
