#!/usr/bin/env python3
"""Run one G3b WORLD_MODEL answer from projected input and exact Bundles."""

from __future__ import annotations

import argparse
import base64
from hashlib import sha256
import json
import os
from pathlib import Path
import stat
import time

from software_world_model.ai_infrastructure import (
    UnixSocketModelGatewayClient,
    WorldModelCapabilityStrategy,
    WorldModelStrategyConfiguration,
)
from software_world_model.cross_cutting import (
    Digest,
    DomainError,
    ErrorCode,
    StableId,
    canonical_json_bytes,
    digest_of,
)
from software_world_model.infrastructure.file_structure_read_bundle import (
    FileStructureReadBundleStore,
)
from software_world_model.application_services.structure_view import (
    StructureViewService,
)
from software_world_model.application_services.citation_projection import (
    citation_seal_for_result,
)
from software_world_model.infrastructure.file_citation_observation_store import (
    structure_view_result_seal_payload,
)
from software_world_model.interface.world_model_evaluation import (
    write_world_model_evaluation_page,
)
from software_world_model.interface.world_model_product import (
    WorldModelProductAnswerService,
)


_QUALIFICATION_REF = (
    "evaluation-only:CC-ARK-CHAT-NO-TOOLS-001:"
    "sha256:c86aad995802b8dcf687fafcbaf36bccb02768ba55b40151ec9aa4704518cade"
)
_PROVIDER_FINGERPRINT = Digest(
    "sha256:420f553a3ce0075818550e08cb1351ce69eaf9871c5a0257aecf88b7b32b88fd"
)
_PERMISSION_DIGEST = Digest(
    "sha256:d0a572d621a1163e8e9e41add704f682dcac2aabb3a3e99c0408ed188813a8a9"
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--product-payload-base64", required=True)
    parser.add_argument("--ordered-bundle", required=True)
    parser.add_argument("--snapshot-bundle", action="append", required=True)
    parser.add_argument("--gateway-socket", required=True)
    parser.add_argument("--run-ref", required=True)
    parser.add_argument("--implementation-commit", required=True)
    parser.add_argument("--authority-page-output", required=True)
    parser.add_argument("--citation-seal-output-directory", required=True)
    parser.add_argument("--summary-output", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    process_started_ns = time.monotonic_ns()
    arguments = _parser().parse_args(argv)
    request_received_ns = time.monotonic_ns()
    if os.environ.get("ARK_API_KEY") is not None:
        raise DomainError(
            ErrorCode.CONTROL_STATE_DENIED,
            "Answer worker must not receive the Ark credential",
        )
    payload = _decode_payload(arguments.product_payload_base64)
    payload_digest = digest_of(payload)
    implementation_commit = _commit(arguments.implementation_commit)
    run_ref = _text(arguments.run_ref, "run ref")

    files = FileStructureReadBundleStore()
    ordered, ordered_file_digest = files.read_ordered(arguments.ordered_bundle)
    loaded = tuple(
        files.read_snapshot(path) for path in arguments.snapshot_bundle
    )
    view = StructureViewService(ordered, loaded)
    expected_snapshot_ids = tuple(
        StableId(item) for item in payload["resolved_snapshot_ids"]
    )
    if (
        view.snapshot_ids != expected_snapshot_ids
        or len(loaded) != len(expected_snapshot_ids)
        or tuple(item[0].snapshot_id for item in loaded)
        != expected_snapshot_ids
    ):
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "projected product payload and mounted Bundles disagree",
        )

    client = UnixSocketModelGatewayClient(arguments.gateway_socket)
    strategy = WorldModelCapabilityStrategy(
        client,
        WorldModelStrategyConfiguration(
            provider_type="VOLCENGINE_ARK",
            adapter_version="openai-chat-completions-no-tools@8",
            model_ref="glm-5-2-260617",
            provider_configuration_fingerprint=_PROVIDER_FINGERPRINT,
            qualification_ref=_QUALIFICATION_REF,
            max_output_tokens=1000,
            timeout_milliseconds=180_000,
            classification="INTERNAL",
        ),
    )
    execution = WorldModelProductAnswerService(
        view=view,
        snapshot_bundles=tuple(item[0] for item in loaded),
        model_strategy=strategy,
        gateway_counters=client,
    ).execute(
        request_ref=f"{payload['case_id']}:{run_ref}",
        original_question=payload["question_variant"],
        response_language="zh-CN",
        classification="INTERNAL",
        permission_digest=_PERMISSION_DIGEST,
    )
    chain = execution.chain
    if (
        chain.provider_call_count != 1
        or chain.network_operation_count != 1
        or len(execution.model_proposals) != 1
        or len(client.audits) != 1
        or chain.question.permission_digest != _PERMISSION_DIGEST
        or chain.question.original_question != payload["question_variant"]
    ):
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "G3b product answer violates its exact live execution boundary",
        )
    chain.require_valid()
    page_digest = write_world_model_evaluation_page(
        arguments.authority_page_output,
        chain,
        implementation_commit,
    )
    citation_seals = _write_citation_seals(
        arguments.citation_seal_output_directory,
        chain,
    )
    proposal = execution.model_proposals[0]
    terminal_persisted_ns = time.monotonic_ns()
    cold_process_elapsed_ns = terminal_persisted_ns - process_started_ns
    request_elapsed_ns = terminal_persisted_ns - request_received_ns
    summary = {
        "schema": "swm.iter-003.g3b-answer-workload@1",
        "status": "PASS",
        "environment": "EVALUATION_ONLY",
        "mode": "WORLD_MODEL",
        "implementation_commit": implementation_commit,
        "run_ref": run_ref,
        "case_id": payload["case_id"],
        "product_payload_digest": payload_digest.value,
        "product_payload_fields": sorted(payload),
        "question_digest": digest_of(payload["question_variant"]).value,
        "resolved_snapshot_ids": payload["resolved_snapshot_ids"],
        "ordered_bundle_file_digest": ordered_file_digest.value,
        "ordered_bundle_digest": ordered.digest.value,
        "snapshot_bundle_file_digests": [item[1].value for item in loaded],
        "snapshot_bundle_digests": [item[0].digest.value for item in loaded],
        "read_set_digest": chain.question.read_authority.read_set_digest.value,
        "chain_digest": chain.digest.value,
        "page_digest": page_digest.value,
        "citation_seals": citation_seals,
        "question_id": chain.question.question_id.value,
        "model_capability": proposal.capability,
        "model_proposal_digest": proposal.digest.value,
        "model_manifest_digest": (
            proposal.gateway_result.call.manifest_digest.value
        ),
        "model_call_id": proposal.gateway_result.call.model_call_id.value,
        "model_output_digest": (
            proposal.gateway_result.response.output_digest.value
        ),
        "model_actual_fingerprint": (
            proposal.gateway_result.call.actual_model_fingerprint
        ),
        "model_eligibility_digest": (
            proposal.gateway_result.eligibility.digest.value
        ),
        "provider_call_count": chain.provider_call_count,
        "network_operation_count": chain.network_operation_count,
        "gateway_route": chain.question.model_route,
        "gateway_audits": [item.canonical_value() for item in client.audits],
        "source_access_count": 0,
        "evidence_payload_access_count": 0,
        "authority_database_access_count": 0,
        "product_suite_read_count": 0,
        "product_oracle_read_count": 0,
        "baseline_result_read_count": 0,
        "credential_visible": False,
        "request_elapsed_milliseconds": request_elapsed_ns // 1_000_000,
        "cold_process_elapsed_milliseconds": (
            cold_process_elapsed_ns // 1_000_000
        ),
        "production_activation": "NOT_EXECUTED",
    }
    _write_new(arguments.summary_output, canonical_json_bytes(summary))
    print(canonical_json_bytes(summary).decode("utf-8"))
    return 0


def _write_citation_seals(
    directory_text: str,
    chain,
) -> list[dict[str, object]]:
    directory = Path(directory_text)
    if (
        not directory.is_absolute()
        or directory.resolve(strict=True) != directory
        or not directory.is_dir()
        or directory.is_symlink()
        or any(directory.iterdir())
    ):
        raise ValueError(
            "Citation seal output must be a canonical empty directory"
        )
    results = {
        result.result_id.value: result
        for result in (
            *(
                item.candidate_result
                for item in chain.resolutions.resolutions
                if item.candidate_result is not None
            ),
            *(item.view_result for item in chain.result_set.step_results),
        )
    }
    index: list[dict[str, object]] = []
    for result_id in sorted(results):
        result = results[result_id]
        seal = citation_seal_for_result(result)
        path = directory / f"{result_id}.json"
        _write_new(
            str(path),
            canonical_json_bytes(structure_view_result_seal_payload(seal)),
        )
        index.append(
            {
                "result_id": result_id,
                "view_result_digest": result.digest.value,
                "seal_digest": seal.digest.value,
                "evidence_count": len(seal.evidence_allowlist),
                "file_name": path.name,
                "file_digest": "sha256:" + sha256(path.read_bytes()).hexdigest(),
            }
        )
    return index


def _decode_payload(value: str) -> dict[str, object]:
    try:
        raw = base64.b64decode(value.encode("ascii"), validate=True)
        payload = json.loads(raw, object_pairs_hook=_unique_object)
    except (
        UnicodeEncodeError,
        ValueError,
        json.JSONDecodeError,
    ) as exc:
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            "projected product payload is invalid",
        ) from exc
    if (
        not isinstance(payload, dict)
        or set(payload)
        != {"case_id", "question_variant", "resolved_snapshot_ids"}
        or canonical_json_bytes(payload) != raw
        or not isinstance(payload.get("resolved_snapshot_ids"), list)
        or len(payload["resolved_snapshot_ids"]) not in {1, 2}
        or len(set(payload["resolved_snapshot_ids"]))
        != len(payload["resolved_snapshot_ids"])
    ):
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            "projected product payload fields are not closed",
        )
    _text(payload.get("case_id"), "case ID")
    _text(payload.get("question_variant"), "question variant")
    for item in payload["resolved_snapshot_ids"]:
        if not isinstance(item, str) or StableId(item).kind != "structure_snapshot":
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "projected product Snapshot ID is invalid",
            )
    return payload


def _unique_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def _write_new(path_text: str, payload: bytes) -> None:
    path = Path(path_text)
    if not path.is_absolute() or path.resolve(strict=False) != path:
        raise ValueError("G3b output path must be canonical and absolute")
    if path.parent.resolve(strict=True) != path.parent:
        raise ValueError("G3b output parent must be canonical")
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
            raise RuntimeError("G3b output is not a regular file")
    finally:
        os.close(descriptor)


def _commit(value: object) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 40
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError("implementation commit must be exact lowercase 40-hex")
    return value


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} must be non-empty")
    return value


if __name__ == "__main__":
    raise SystemExit(main())
