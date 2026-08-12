#!/usr/bin/env python3
"""Authorize one evaluation session before entering the qualified Gateway baseline."""

from __future__ import annotations

import argparse
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import re
import stat
from types import ModuleType

from software_world_model.cross_cutting import canonical_json_bytes, digest_of


_SCHEMA = "SWM-WORLD-MODEL-GATEWAY-AUTHORIZATION-RECEIPT@1"
_SUMMARY_SCHEMA = "SWM-WORLD-MODEL-AUTHORIZED-GATEWAY@1"
_LEGACY_GATEWAY_SHA256 = (
    "ec6c04e64be4d6fed8c1ef9992e2fa2a2e47025c85d7ca4f0e783493c6dfa67c"
)
_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evaluation-authorization-receipt", required=True)
    parser.add_argument("--expected-evaluation-grant-digest", required=True)
    parser.add_argument("--expected-disclosure-authorization-digest", required=True)
    parser.add_argument("--summary-output", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments, baseline_arguments = _parser().parse_known_args(argv)
    expected_grant = _digest(
        arguments.expected_evaluation_grant_digest,
        "expected evaluation grant digest",
    )
    expected_disclosure = _digest(
        arguments.expected_disclosure_authorization_digest,
        "expected disclosure authorization digest",
    )
    receipt_path = _exact_file(
        Path(arguments.evaluation_authorization_receipt),
        "evaluation authorization receipt",
    )
    receipt = _load_exact_document(receipt_path)
    expected_keys = {
        "schema",
        "status",
        "evaluation_grant_digest",
        "disclosure_authorization_digest",
        "authorized_by",
        "authorized_at",
        "authorization_ref",
        "payload_boundary",
        "production_activation",
        "document_digest",
    }
    if set(receipt) != expected_keys:
        raise RuntimeError("Gateway authorization receipt shape is not closed")
    receipt_core = {
        key: value for key, value in receipt.items() if key != "document_digest"
    }
    if (
        receipt.get("schema") != _SCHEMA
        or receipt.get("status") != "AUTHORIZED"
        or receipt.get("evaluation_grant_digest") != expected_grant
        or receipt.get("disclosure_authorization_digest") != expected_disclosure
        or receipt.get("authorized_by") != "user"
        or receipt.get("payload_boundary")
        != "ORIGINAL_QUESTION_AND_NO_PAYLOAD_PUBLISHED_STRUCTURE"
        or receipt.get("production_activation") != "NOT_EXECUTED"
        or receipt.get("document_digest")
        != digest_of([_SCHEMA, receipt_core]).value
    ):
        raise RuntimeError("Gateway authorization receipt is invalid")

    output_path = _future_file(Path(arguments.summary_output), "summary output")
    baseline_output = output_path.with_name("qualified-baseline-summary.json")
    if baseline_output.exists() or baseline_output.is_symlink():
        raise RuntimeError("qualified Gateway baseline summary already exists")
    baseline = _load_qualified_baseline()
    code = baseline.main(
        [
            *baseline_arguments,
            "--summary-output",
            str(baseline_output),
        ]
    )
    if code != 0:
        return code
    baseline_summary = _load_exact_document(baseline_output)
    if (
        baseline_summary.get("status") != "PASS"
        or baseline_summary.get("production_activation") != "NOT_EXECUTED"
        or baseline_summary.get("provider_call_count") != 1
        or baseline_summary.get("https_dispatch_count") != 1
    ):
        raise RuntimeError("qualified Gateway baseline did not pass exactly once")
    summary_core = {
        key: value
        for key, value in baseline_summary.items()
        if key
        not in {
            "schema",
            "g3b_freeze_ref",
            "g3b_freeze_digest",
            "permission_digest",
        }
    }
    summary_core.update(
        {
            "schema": _SUMMARY_SCHEMA,
            "evaluation_grant_digest": expected_grant,
            "disclosure_authorization_digest": expected_disclosure,
            "authorization_receipt_digest": receipt["document_digest"],
            "authorization_ref": receipt["authorization_ref"],
            "qualified_gateway_baseline": {
                "entrypoint_sha256": _LEGACY_GATEWAY_SHA256,
                "legacy_freeze_digest": baseline_summary["g3b_freeze_digest"],
                "role": "QUALIFIED_CAPABILITY_BASELINE_ONLY",
            },
        }
    )
    summary = {
        **summary_core,
        "document_digest": digest_of([_SUMMARY_SCHEMA, summary_core]).value,
    }
    _write_new(output_path, canonical_json_bytes(summary))
    print(canonical_json_bytes(summary).decode("utf-8"))
    return 0


def _load_qualified_baseline() -> ModuleType:
    path = _exact_file(
        Path(__file__).with_name("gateway_workload.py"),
        "qualified Gateway baseline",
    )
    if sha256(path.read_bytes()).hexdigest() != _LEGACY_GATEWAY_SHA256:
        raise RuntimeError("qualified Gateway baseline bytes drifted")
    specification = importlib.util.spec_from_file_location(
        "_swm_qualified_gateway_baseline",
        path,
    )
    if specification is None or specification.loader is None:
        raise RuntimeError("qualified Gateway baseline could not be loaded")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    if not callable(getattr(module, "main", None)):
        raise RuntimeError("qualified Gateway baseline has no main entrypoint")
    return module


def _load_exact_document(path: Path) -> dict[str, object]:
    raw = path.read_bytes()
    value = json.loads(raw, object_pairs_hook=_unique_object)
    if not isinstance(value, dict) or canonical_json_bytes(value) != raw:
        raise RuntimeError("Gateway input is not one canonical JSON object")
    return value


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise RuntimeError("Gateway input contains a duplicate JSON key")
        value[key] = item
    return value


def _exact_file(path: Path, label: str) -> Path:
    resolved = path.resolve(strict=True)
    if path != resolved or not resolved.is_file() or path.is_symlink():
        raise RuntimeError(f"{label} must be one canonical non-symlink file")
    return resolved


def _future_file(path: Path, label: str) -> Path:
    parent = path.parent.resolve(strict=True)
    resolved = parent / path.name
    if path != resolved or path.exists() or path.is_symlink():
        raise RuntimeError(f"{label} must be one new canonical file")
    return resolved


def _write_new(path: Path, payload: bytes) -> None:
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
            raise RuntimeError("Gateway summary is not a regular file")
    finally:
        os.close(descriptor)


def _digest(value: object, label: str) -> str:
    if not isinstance(value, str) or not _DIGEST.fullmatch(value):
        raise RuntimeError(f"{label} is invalid")
    return value


if __name__ == "__main__":
    raise SystemExit(main())
