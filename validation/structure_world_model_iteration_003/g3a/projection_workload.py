#!/usr/bin/env python3
"""Verify and summarize a one-way sealed G3a evaluation-page projection."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import stat

from software_world_model.cross_cutting import canonical_json_bytes, digest_of
from software_world_model.interface.world_model_evaluation import (
    read_world_model_evaluation_page,
)


AUTHORITY_STAGES = (
    "QUESTION",
    "REQUIREMENT_REVISION",
    "CANDIDATE_RESOLUTION_SET",
    "QUERY_PLAN",
    "QUERY_RESULT_SET",
    "ASSESSMENT",
    "ANSWER_DRAFT",
    "ANSWER_REVIEW",
    "RESPONSE_AUTHORIZATION",
    "DELIVERY",
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--authority-page", required=True)
    parser.add_argument("--expected-implementation-commit", required=True)
    parser.add_argument("--expected-page-digest", required=True)
    parser.add_argument("--summary-output", required=True)
    return parser


def _write_new(path_text: str, payload: bytes) -> None:
    path = Path(path_text)
    if not path.is_absolute() or path.resolve(strict=False) != path:
        raise ValueError("output path must be canonical and absolute")
    if path.parent.resolve(strict=True) != path.parent:
        raise ValueError("output parent must be canonical")
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
            raise RuntimeError("output is not a regular file")
    finally:
        os.close(descriptor)


def main(argv: list[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    page = read_world_model_evaluation_page(
        arguments.authority_page,
        expected_implementation_commit=(
            arguments.expected_implementation_commit
        ),
        expected_page_digest=arguments.expected_page_digest,
    )
    stages = page["authority_chain"]["stages"]
    observed_stages = tuple(item["stage"] for item in stages)
    boundary = page["execution_boundary"]
    if (
        page["evaluation_only"] is not True
        or page["mode"] != "WORLD_MODEL"
        or page["environment"] != "EVALUATION_ONLY"
        or observed_stages != AUTHORITY_STAGES
        or type(boundary["provider_call_count"]) is not int
        or boundary["provider_call_count"] != 0
        or type(boundary["network_operation_count"]) is not int
        or boundary["network_operation_count"] != 0
        or boundary["source_access_allowed"] is not False
        or boundary["evidence_payload_access_allowed"] is not False
    ):
        raise RuntimeError("sealed G3a evaluation page violates its offline boundary")
    summary = {
        "schema": "iteration-003-g3a-projection-workload@1",
        "status": "PASS",
        "mode": page["mode"],
        "environment": page["environment"],
        "implementation_commit": page["implementation_commit"],
        "question_id": page["request"]["question_id"],
        "read_set_digest": page["read_binding"]["read_set_digest"],
        "chain_digest": page["authority_chain"]["chain_digest"],
        "page_digest": arguments.expected_page_digest,
        "authority_stage_count": len(stages),
        "page_payload_digest": digest_of(page).value,
        "provider_call_count": boundary["provider_call_count"],
        "network_operation_count": boundary["network_operation_count"],
    }
    _write_new(arguments.summary_output, canonical_json_bytes(summary))
    print(canonical_json_bytes(summary).decode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
