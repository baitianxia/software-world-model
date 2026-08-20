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
_JAVA_GATEWAY_SHA256 = (
    "72035f4499ea5273f79ad87a234f7dcdac4f39c6fdf7eaeab4a7b717e5fd7d31"
)
_JAVA_SOURCE_SEMANTICS_GATEWAY_SHA256 = (
    "2ca2f8f2e9b8ff3d352bdbb8f673f559723221b1f2d42bcbc7edf4d9372c6900"
)
_BOUNDED_JAVA_SOURCE_SEMANTICS_GATEWAY_SHA256 = (
    "35a6f9df90ff8193bb3d1211cd50d3a80914fa2e9c23144f3b1854b44ac37e83"
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
    baseline = _load_qualified_baseline(baseline_arguments)
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
    baseline_schema = baseline_summary.get("schema")
    bounded = (
        baseline_schema
        == "swm.iter-008.bounded-java-source-semantics-gateway-workload@2"
    )
    expected_calls = baseline_summary.get("provider_call_count") if bounded else (
        3
        if baseline_schema
        == "swm.iter-007.java-source-semantics-gateway-workload@1"
        else 1
    )
    if (
        baseline_summary.get("status") != "PASS"
        or baseline_summary.get("production_activation") != "NOT_EXECUTED"
        or (bounded and (not isinstance(expected_calls, int) or not 4 <= expected_calls <= 6))
        or baseline_summary.get("provider_call_count") != expected_calls
        or baseline_summary.get("https_dispatch_count") != expected_calls
        or (
            bounded
            and (
                baseline_summary.get("provider_connection_policy")
                != "PERSISTENT_VERIFIED_TLS_HTTP11_KEEP_ALIVE@2"
                or baseline_summary.get(
                    "maximum_pre_dispatch_tls_handshake_attempts"
                )
                != 3
                or baseline_summary.get(
                    "maximum_http_dispatches_per_tls_session"
                )
                != 20
                or baseline_summary.get("provider_descriptor_provisioned_count")
                != 3
                or type(
                    baseline_summary.get("provider_descriptor_consumed_count")
                )
                is not int
                or not 1
                <= baseline_summary["provider_descriptor_consumed_count"]
                <= 3
                or baseline_summary.get("provider_descriptor_unused_closed_count")
                != 3 - baseline_summary["provider_descriptor_consumed_count"]
                or baseline_summary.get("tls_handshake_attempt_count")
                != baseline_summary["provider_descriptor_consumed_count"]
                or type(baseline_summary.get("tls_handshake_success_count"))
                is not int
                or not 1
                <= baseline_summary["tls_handshake_success_count"]
                <= baseline_summary["tls_handshake_attempt_count"]
                or baseline_summary.get("connection_reuse_count")
                != expected_calls
                - baseline_summary["tls_handshake_success_count"]
                or baseline_summary.get("request_retry_count") != 0
                or baseline_summary.get("credential_resolution_count")
                != expected_calls
                or baseline_summary.get("credential_resolution_success_count")
                != expected_calls
                or not isinstance(
                    baseline_summary.get("pre_dispatch_tls_failure_codes"),
                    list,
                )
                or len(baseline_summary["pre_dispatch_tls_failure_codes"])
                != baseline_summary["pre_dispatch_tls_handshake_failure_count"]
                or not isinstance(
                    baseline_summary.get("verified_peer_certificate_sha256s"),
                    list,
                )
                or len(baseline_summary["verified_peer_certificate_sha256s"])
                != baseline_summary["tls_handshake_success_count"]
            )
        )
    ):
        raise RuntimeError("qualified Gateway baseline call protocol did not pass")
    if baseline_schema == "swm.iter-003.g3b-gateway-workload@1":
        baseline_sha256 = _LEGACY_GATEWAY_SHA256
        baseline_freeze_digest = baseline_summary["g3b_freeze_digest"]
        baseline_freeze_key = "legacy_freeze_digest"
    elif baseline_schema == "swm.iter-006.java-gateway-workload@1":
        baseline_sha256 = _JAVA_GATEWAY_SHA256
        baseline_freeze_digest = baseline_summary["java_gateway_freeze_digest"]
        baseline_freeze_key = "capability_freeze_digest"
    elif (
        baseline_schema
        == "swm.iter-007.java-source-semantics-gateway-workload@1"
    ):
        baseline_sha256 = _JAVA_SOURCE_SEMANTICS_GATEWAY_SHA256
        baseline_freeze_digest = baseline_summary[
            "java_source_semantics_gateway_freeze_digest"
        ]
        baseline_freeze_key = "source_semantics_capability_freeze_digest"
    elif bounded:
        baseline_sha256 = _BOUNDED_JAVA_SOURCE_SEMANTICS_GATEWAY_SHA256
        baseline_freeze_digest = baseline_summary[
            "bounded_java_source_semantics_gateway_freeze_digest"
        ]
        baseline_freeze_key = (
            "bounded_source_semantics_capability_freeze_digest"
        )
    else:
        raise RuntimeError("qualified Gateway baseline schema is invalid")
    summary_core = {
        key: value
        for key, value in baseline_summary.items()
        if key
        not in {
            "schema",
            "g3b_freeze_ref",
            "g3b_freeze_digest",
            "java_gateway_freeze_ref",
            "java_gateway_freeze_digest",
            "java_source_semantics_gateway_freeze_ref",
            "java_source_semantics_gateway_freeze_digest",
            "bounded_java_source_semantics_gateway_freeze_ref",
            "bounded_java_source_semantics_gateway_freeze_digest",
            "permission_digest",
            "document_digest",
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
                "entrypoint_sha256": baseline_sha256,
                baseline_freeze_key: baseline_freeze_digest,
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


def _load_qualified_baseline(baseline_arguments: list[str]) -> ModuleType:
    try:
        freeze_index = baseline_arguments.index("--g3b-freeze")
        freeze_path = _exact_file(
            Path(baseline_arguments[freeze_index + 1]),
            "qualified Gateway freeze",
        )
        freeze = _load_exact_document(freeze_path)
    except (ValueError, IndexError) as exc:
        raise RuntimeError("qualified Gateway freeze argument is missing") from exc
    if freeze.get("schema") == "swm.iter-003.g3b-input-freeze@1":
        filename = "gateway_workload.py"
        expected_sha256 = _LEGACY_GATEWAY_SHA256
        module_name = "_swm_qualified_legacy_gateway_baseline"
    elif freeze.get("schema") == "SWM-ITER-006-JAVA-GATEWAY-FREEZE@1":
        filename = "java_gateway_workload.py"
        expected_sha256 = _JAVA_GATEWAY_SHA256
        module_name = "_swm_qualified_java_gateway_baseline"
    elif (
        freeze.get("schema")
        == "SWM-ITER-007-JAVA-SOURCE-SEMANTICS-GATEWAY-FREEZE@1"
    ):
        filename = "java_source_semantics_gateway_workload.py"
        expected_sha256 = _JAVA_SOURCE_SEMANTICS_GATEWAY_SHA256
        module_name = "_swm_qualified_java_source_semantics_gateway_baseline"
    elif (
        freeze.get("schema")
        == "SWM-ITER-008-BOUNDED-JAVA-SOURCE-SEMANTICS-GATEWAY-FREEZE@1"
    ):
        filename = "bounded_java_source_semantics_gateway_workload.py"
        expected_sha256 = _BOUNDED_JAVA_SOURCE_SEMANTICS_GATEWAY_SHA256
        module_name = "_swm_qualified_bounded_java_source_semantics_gateway_baseline"
    else:
        raise RuntimeError("qualified Gateway freeze schema is unsupported")
    path = _exact_file(
        Path(__file__).with_name(filename),
        "qualified Gateway baseline",
    )
    if sha256(path.read_bytes()).hexdigest() != expected_sha256:
        raise RuntimeError("qualified Gateway baseline bytes drifted")
    specification = importlib.util.spec_from_file_location(
        module_name,
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
