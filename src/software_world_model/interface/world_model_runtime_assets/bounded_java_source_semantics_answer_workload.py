#!/usr/bin/env python3
"""Run one formal bounded source-off Java source-semantics product answer."""

from __future__ import annotations

import os
import time

from software_world_model.ai_infrastructure import (
    DeepSeekModelConfiguration,
    IMPLEMENTATION_ANSWER_DRAFTING,
    IMPLEMENTATION_ANSWER_REVIEW,
    IMPLEMENTATION_INVESTIGATION,
    JAVA_SOURCE_SEMANTICS_WORLD_MODEL_PROPOSAL_CONTRACT,
    UnixSocketModelGatewayClient,
    WorldModelCapabilityStrategy,
    WorldModelStrategyConfiguration,
)
from software_world_model.application_services.structure_view import (
    StructureViewService,
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
from software_world_model.interface.world_model_evaluation import (
    write_world_model_evaluation_page,
)
from software_world_model.interface.world_model_product import (
    WorldModelProductAnswerService,
)
from software_world_model.interface.world_model_runtime_assets import (
    java_source_semantics_answer_workload as _shared,
)


_PERMISSION_DIGEST = digest_of(
    "ITER-008-BOUNDED-JAVA-SOURCE-SEMANTICS-FORMAL-WEB-PERMISSION@1"
)


def main(argv: list[str] | None = None) -> int:
    process_started_ns = time.monotonic_ns()
    arguments = _shared._parser().parse_args(argv)
    request_received_ns = time.monotonic_ns()
    if any(
        os.environ.get(name) is not None
        for name in ("ARK_API_KEY", "DEEPSEEK_API_KEY")
    ):
        raise DomainError(
            ErrorCode.CONTROL_STATE_DENIED,
            "Answer worker must not receive a Provider credential",
        )
    conformance_result_ref = arguments.conformance_result_ref
    prefix = "CC-DEEPSEEK-CHAT-NO-TOOLS-001:sha256:"
    if (
        not isinstance(conformance_result_ref, str)
        or not conformance_result_ref.startswith(prefix)
    ):
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "Answer worker requires the exact frozen DeepSeek Conformance reference",
        )
    try:
        Digest("sha256:" + conformance_result_ref.removeprefix(prefix))
    except (TypeError, ValueError) as exc:
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "Answer worker DeepSeek Conformance digest is invalid",
        ) from exc
    configuration = DeepSeekModelConfiguration()
    payload = _shared._decode_payload(arguments.product_payload_base64)
    payload_digest = digest_of(payload)
    implementation_commit = _shared._commit(arguments.implementation_commit)
    run_ref = _shared._text(arguments.run_ref, "run ref")

    files = FileStructureReadBundleStore()
    ordered, ordered_file_digest = files.read_ordered(arguments.ordered_bundle)
    loaded = tuple(files.read_snapshot(path) for path in arguments.snapshot_bundle)
    view = StructureViewService(ordered, loaded)
    mounted_profiles = tuple(
        sorted(
            {
                coverage.root.profile_ref
                for bundle, _ in loaded
                for coverage in bundle.coverages
            }
        )
    )
    expected_snapshot_ids = tuple(
        StableId(item) for item in payload["resolved_snapshot_ids"]
    )
    if (
        view.snapshot_ids != expected_snapshot_ids
        or len(loaded) != len(expected_snapshot_ids)
        or tuple(item[0].snapshot_id for item in loaded) != expected_snapshot_ids
        or mounted_profiles != ("JAVA_SOURCE_SEMANTICS@1",)
    ):
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "projected payload and semantic Bundles disagree",
        )

    client = UnixSocketModelGatewayClient(
        arguments.gateway_socket,
        maximum_calls=6,
    )
    strategy = WorldModelCapabilityStrategy(
        client,
        WorldModelStrategyConfiguration(
            provider_type=configuration.provider_type,
            adapter_version=configuration.adapter_version,
            model_ref=configuration.model_ref,
            provider_configuration_fingerprint=configuration.fingerprint,
            qualification_ref=f"evaluation-only:{conformance_result_ref}",
            max_output_tokens=1000,
            timeout_milliseconds=180_000,
            classification="INTERNAL",
        ),
        proposal_contract=JAVA_SOURCE_SEMANTICS_WORLD_MODEL_PROPOSAL_CONTRACT,
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
    proposals = execution.model_proposals
    proposal_count = len(proposals)
    investigation_count = proposal_count - 2
    expected_capabilities = (
        (IMPLEMENTATION_INVESTIGATION,) * investigation_count
        + (
            IMPLEMENTATION_ANSWER_DRAFTING,
            IMPLEMENTATION_ANSWER_REVIEW,
        )
    )
    if (
        not 4 <= proposal_count <= 6
        or chain.provider_call_count != proposal_count
        or chain.network_operation_count != proposal_count
        or tuple(item.capability for item in proposals) != expected_capabilities
        or len(client.audits) != proposal_count
        or chain.question.permission_digest != _PERMISSION_DIGEST
        or chain.question.original_question != payload["question_variant"]
    ):
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "semantic answer violates its bounded four-to-six-call execution boundary",
        )
    chain.require_valid()
    page_digest = write_world_model_evaluation_page(
        arguments.authority_page_output,
        chain,
        implementation_commit,
    )
    citation_seals = _shared._write_citation_seals(
        arguments.citation_seal_output_directory,
        chain,
    )
    terminal_persisted_ns = time.monotonic_ns()
    request_elapsed_ns = terminal_persisted_ns - request_received_ns
    summary = {
        "schema": "swm.iter-008.bounded-java-source-semantics-answer-workload@1",
        "status": "PASS",
        "environment": "EVALUATION_ONLY",
        "mode": "WORLD_MODEL",
        "knowledge_profile_ref": "JAVA_SOURCE_SEMANTICS@1",
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
        "model_capabilities": [item.capability for item in proposals],
        "model_proposal_digests": [item.digest.value for item in proposals],
        "model_manifest_digests": [
            item.gateway_result.call.manifest_digest.value for item in proposals
        ],
        "model_call_ids": [
            item.gateway_result.call.model_call_id.value for item in proposals
        ],
        "model_output_digests": [
            item.gateway_result.response.output_digest.value for item in proposals
        ],
        "model_actual_fingerprints": [
            item.gateway_result.call.actual_model_fingerprint for item in proposals
        ],
        "provider_type": configuration.provider_type,
        "adapter_version": configuration.adapter_version,
        "requested_model_ref": configuration.model_ref,
        "conformance_result_ref": conformance_result_ref,
        "model_eligibility_digests": [
            item.gateway_result.eligibility.digest.value for item in proposals
        ],
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
            terminal_persisted_ns - process_started_ns
        )
        // 1_000_000,
        "production_activation": "NOT_EXECUTED",
    }
    _shared._write_new(arguments.summary_output, canonical_json_bytes(summary))
    print(canonical_json_bytes(summary).decode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
