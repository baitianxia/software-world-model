#!/usr/bin/env python3
"""Run one exact ITER-008 bounded source-semantics Model Egress Gateway."""

from __future__ import annotations

from pathlib import Path
import socket
from typing import Mapping

from software_world_model.ai_infrastructure import (
    DeepSeekChatCompletionsNoToolsAdapter,
    DeepSeekModelConfiguration,
    ModelEgressGatewayServer,
    ModelGateway,
    PinnedIPDeepSeekChatTransport,
    load_deepseek_chat_conformance_qualification,
    world_model_answer_output_schemas,
)
from software_world_model.ai_infrastructure.bounded_java_source_semantics_model_egress_qualification import (
    BOUNDED_JAVA_SOURCE_SEMANTICS_MODEL_EGRESS_POLICY_FILE_DIGEST,
    load_bounded_java_source_semantics_gateway_qualification_binding,
)
from software_world_model.cross_cutting import (
    DomainError,
    ErrorCode,
    canonical_json_bytes,
    digest_of,
)
from software_world_model.infrastructure import (
    SqliteDatabase,
    SqliteModelGatewayRepository,
)

from software_world_model.interface.world_model_runtime_assets.java_source_semantics_gateway_workload import (
    _append_document,
    _commit,
    _future_file,
    _load_document,
    _parser,
    _sha256_file,
    _write_new,
)


BOUNDED_JAVA_SOURCE_SEMANTICS_GATEWAY_FREEZE_SCHEMA = (
    "SWM-ITER-008-BOUNDED-JAVA-SOURCE-SEMANTICS-GATEWAY-FREEZE@1"
)


def main(argv: list[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    descriptors = tuple(arguments.connected_provider_socket_fd)
    if len(descriptors) != 3 or len(set(descriptors)) != 3:
        raise DomainError(
            ErrorCode.CONTROL_STATE_DENIED,
            "bounded source-semantics Gateway requires exactly three connected sockets",
        )
    implementation_commit = _commit(arguments.implementation_commit)
    freeze = _load_document(arguments.g3b_freeze)
    permission_digest = _verify_freeze(freeze)
    if (
        _sha256_file(Path(arguments.egress_policy))
        != BOUNDED_JAVA_SOURCE_SEMANTICS_MODEL_EGRESS_POLICY_FILE_DIGEST
    ):
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "bounded source-semantics Gateway policy file digest is not exact",
        )
    binding = load_bounded_java_source_semantics_gateway_qualification_binding(
        qualification_path=arguments.capability_qualification,
        closed_result_path=arguments.closed_capability_result,
        policy_path=arguments.egress_policy,
    )
    if (
        freeze.get("capability_qualification_document_digest")
        != binding.qualification_document_digest.value
        or freeze.get("closed_capability_result_digest")
        != binding.closed_capability_result_digest.value
    ):
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "bounded source-semantics Gateway freeze uses another qualification",
        )

    configuration = DeepSeekModelConfiguration()
    conformance = load_deepseek_chat_conformance_qualification(
        arguments.conformance_result,
        configuration,
    )
    if (
        freeze.get("conformance_result_ref") != conformance.result_ref
        or freeze.get("conformance_result_digest")
        != conformance.result_digest.value
    ):
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "bounded source-semantics Gateway conformance binding drifted",
        )

    server_audits: list[dict[str, object]] = []
    transport_audits: list[dict[str, object]] = []
    server_audit_path = _future_file(arguments.server_audit_output)
    transport_audit_path = _future_file(arguments.transport_audit_output)

    def record_server(value: Mapping[str, object]) -> None:
        frozen = dict(value)
        server_audits.append(frozen)
        _append_document(server_audit_path, frozen)

    def record_transport(value: Mapping[str, object]) -> None:
        frozen = dict(value)
        transport_audits.append(frozen)
        _append_document(transport_audit_path, frozen)

    transport = PinnedIPDeepSeekChatTransport(
        numeric_address=arguments.numeric_provider_address,
        api_key_resolver=configuration.resolve_api_key,
        connected_socket_fds=descriptors,
        audit_writer=record_transport,
        maximum_calls=6,
    )
    adapter = DeepSeekChatCompletionsNoToolsAdapter(
        transport=transport,
        configuration=configuration,
        output_schemas=world_model_answer_output_schemas(
            include_java_source_semantics=True
        ),
        live_qualification=conformance,
    )
    policy = binding.create_policy(
        configuration=configuration,
        conformance_result_ref=conformance.result_ref,
    )
    prebound_listener = socket.socket(
        socket.AF_UNIX,
        socket.SOCK_STREAM,
        fileno=arguments.gateway_listener_socket_fd,
    )
    with SqliteDatabase(_future_file(arguments.database)) as database:
        gateway = ModelGateway(SqliteModelGatewayRepository(database), (adapter,))
        request_count = ModelEgressGatewayServer(
            arguments.socket_path,
            gateway=gateway,
            policy=policy,
            audit_writer=record_server,
            prebound_listener=prebound_listener,
        ).serve(
            startup_timeout_seconds=arguments.startup_timeout_seconds,
            idle_timeout_seconds=arguments.idle_timeout_seconds,
        )
    unused_closed = transport.close_session_and_unused_connected_sockets()

    statuses = [str(item["status"]) for item in server_audits]
    dispatch_audits = [
        item
        for item in transport_audits
        if item.get("schema") == "SWM-PINNED-DEEPSEEK-DISPATCH-AUDIT@2"
    ]
    unused_audits = [
        item for item in transport_audits if item.get("outcome") == "UNUSED_CLOSED"
    ]
    tls_audits = [
        item
        for item in transport_audits
        if item.get("schema")
        == "SWM-PINNED-DEEPSEEK-TLS-HANDSHAKE-AUDIT@1"
    ]
    tls_success_count = transport.tls_handshake_success_count
    tls_attempt_count = transport.tls_handshake_attempt_count
    connection_reuse_count = transport.connection_reuse_count
    verified_tls_audits = [
        item for item in tls_audits if item.get("outcome") == "VERIFIED"
    ]
    failed_tls_audits = [
        item
        for item in tls_audits
        if item.get("outcome") == "FAILED_BEFORE_CREDENTIAL"
    ]
    verified_connections = {
        item.get("ordinal"): item.get("peer_certificate_sha256")
        for item in verified_tls_audits
    }
    seen_connections: set[object] = set()
    dispatch_audits_valid = True
    for ordinal, item in enumerate(dispatch_audits, start=1):
        connection_ordinal = item.get("tls_connection_ordinal")
        expected_reuse = connection_ordinal in seen_connections
        dispatch_audits_valid = dispatch_audits_valid and (
            item.get("ordinal") == ordinal
            and item.get("outcome") == "HTTP_RESPONSE"
            and item.get("failure_code") is None
            and isinstance(item.get("status_code"), int)
            and 200 <= item["status_code"] < 300
            and item.get("response_body_digest") is not None
            and connection_ordinal in verified_connections
            and item.get("peer_certificate_sha256")
            == verified_connections.get(connection_ordinal)
            and item.get("connection_reused") is expected_reuse
        )
        seen_connections.add(connection_ordinal)
    tls_audits_valid = (
        [item.get("ordinal") for item in tls_audits]
        == list(range(1, tls_attempt_count + 1))
        and len(verified_tls_audits) == tls_success_count
        and len(failed_tls_audits) == tls_attempt_count - tls_success_count
        and all(
            item.get("failure_code") is None
            and item.get("peer_certificate_sha256") is not None
            for item in verified_tls_audits
        )
        and all(
            item.get("failure_code") is not None
            and item.get("peer_certificate_sha256") is None
            for item in failed_tls_audits
        )
    )
    sequence = policy.validated_stages
    protocol_valid = (
        4 <= request_count <= 6
        and 2 <= sequence.count("IMPLEMENTATION_INVESTIGATION") <= 4
        and sequence[-2:]
        == ("IMPLEMENTATION_ANSWER_DRAFTING", "IMPLEMENTATION_ANSWER_REVIEW")
    )
    summary_core = {
        "schema": "swm.iter-008.bounded-java-source-semantics-gateway-workload@2",
        "status": (
            "PASS"
            if protocol_valid
            and statuses == ["RESULT"] * request_count
            and len(dispatch_audits) == request_count
            and 1 <= tls_success_count <= 3
            and tls_success_count <= tls_attempt_count <= 3
            and connection_reuse_count == request_count - tls_success_count
            and transport.credential_resolution_count == request_count
            and transport.credential_resolution_success_count == request_count
            and unused_closed == 3 - tls_attempt_count
            and len(unused_audits) == unused_closed
            and len(tls_audits) == tls_attempt_count
            and tls_audits_valid
            and dispatch_audits_valid
            else "FAIL"
        ),
        "environment": "EVALUATION_ONLY",
        "implementation_commit": implementation_commit,
        "bounded_java_source_semantics_gateway_freeze_ref": freeze["freeze_ref"],
        "bounded_java_source_semantics_gateway_freeze_digest": freeze[
            "document_digest"
        ],
        "permission_digest": permission_digest,
        "policy_ref": policy.policy_ref,
        "policy_digest": policy.policy_digest.value,
        "capability_qualification_ref": binding.capability_qualification_ref,
        "capability_qualification_digest": (
            binding.capability_qualification_digest.value
        ),
        "closed_capability_result_digest": (
            binding.closed_capability_result_digest.value
        ),
        "qualification_valid_until": binding.qualification_valid_until.isoformat(),
        "conformance_result_ref": conformance.result_ref,
        "provider_selection_policy": (
            "PRE_DISPATCH_FIRST_CURRENTLY_QUALIFIED_NO_REQUEST_RETRY"
        ),
        "provider_preference_order": ["VOLCENGINE_ARK", "DEEPSEEK"],
        "selected_provider_type": configuration.provider_type,
        "provider_type": configuration.provider_type,
        "adapter_version": configuration.adapter_version,
        "requested_model_ref": configuration.model_ref,
        "expected_actual_model_fingerprint": (
            configuration.actual_model_fingerprint
        ),
        "fallback_after_dispatch": False,
        "numeric_provider_address": arguments.numeric_provider_address,
        "numeric_provider_address_scope": (
            dispatch_audits[0].get("address_scope")
            if dispatch_audits
            and len(
                {item.get("address_scope") for item in dispatch_audits}
            )
            == 1
            else None
        ),
        "provider_connection_capability": "INHERITED_EXACT_CONNECTED_SOCKET_SET",
        "provider_connection_policy": (
            "PERSISTENT_VERIFIED_TLS_HTTP11_KEEP_ALIVE@2"
        ),
        "maximum_pre_dispatch_tls_handshake_attempts": 3,
        "maximum_http_dispatches_per_tls_session": 20,
        "gateway_listener_capability": "INHERITED_EXACT_BOUND_AF_UNIX_LISTENER",
        "new_socket_syscall_capability": "DENIED_BY_SEATBELT",
        "provider_descriptor_provisioned_count": 3,
        "provider_descriptor_consumed_count": tls_attempt_count,
        "provider_descriptor_unused_closed_count": unused_closed,
        "tls_handshake_attempt_count": tls_attempt_count,
        "tls_handshake_success_count": tls_success_count,
        "pre_dispatch_tls_handshake_failure_count": (
            tls_attempt_count - tls_success_count
        ),
        "pre_dispatch_tls_failure_codes": [
            item["failure_code"] for item in failed_tls_audits
        ],
        "verified_peer_certificate_sha256s": [
            item["peer_certificate_sha256"] for item in verified_tls_audits
        ],
        "connection_reuse_count": connection_reuse_count,
        "request_retry_count": 0,
        "credential_resolution_count": transport.credential_resolution_count,
        "credential_resolution_success_count": (
            transport.credential_resolution_success_count
        ),
        "provider_call_count": request_count,
        "https_dispatch_count": len(dispatch_audits),
        "server_audit_count": len(server_audits),
        "server_statuses": statuses,
        "validated_role_sequence": sequence,
        "credential_reference": configuration.secret_reference,
        "credential_value_recorded": False,
        "dns_operation_count_in_dispatch_process": 0,
        "proxy_environment_used": False,
        "production_activation": "NOT_EXECUTED",
    }
    summary = {
        **summary_core,
        "document_digest": digest_of(summary_core).value,
    }
    _write_new(
        _future_file(arguments.summary_output),
        canonical_json_bytes(summary),
    )
    print(canonical_json_bytes(summary).decode("utf-8"))
    return 0 if summary["status"] == "PASS" else 2


def _verify_freeze(value: Mapping[str, object]) -> str:
    core = {key: item for key, item in value.items() if key != "document_digest"}
    required = {
        "schema",
        "freeze_ref",
        "environment",
        "strategy_ref",
        "prompt_ref",
        "proposal_vocabulary_ref",
        "capability_qualification_document_digest",
        "closed_capability_result_digest",
        "egress_policy_digest",
        "conformance_result_ref",
        "conformance_result_digest",
        "permission_digest",
        "production_activation",
        "document_digest",
    }
    permission = value.get("permission_digest")
    if (
        set(value) != required
        or value.get("schema")
        != BOUNDED_JAVA_SOURCE_SEMANTICS_GATEWAY_FREEZE_SCHEMA
        or value.get("freeze_ref")
        != "ITER-008-BOUNDED-JAVA-SOURCE-SEMANTICS-PRODUCT-GATEWAY-CANDIDATE@1"
        or value.get("environment") != "EVALUATION_ONLY"
        or value.get("strategy_ref")
        != "model-snapshot-first-world-model-answer@1.5.10"
        or value.get("prompt_ref")
        != "java-source-semantics-world-model-prompt@19"
        or value.get("proposal_vocabulary_ref")
        != "java-source-semantics-world-model-vocabulary@19"
        or value.get("egress_policy_digest")
        != BOUNDED_JAVA_SOURCE_SEMANTICS_MODEL_EGRESS_POLICY_FILE_DIGEST
        or value.get("production_activation") != "NOT_EXECUTED"
        or not isinstance(permission, str)
        or not permission.startswith("sha256:")
        or value.get("document_digest")
        != digest_of(
            [BOUNDED_JAVA_SOURCE_SEMANTICS_GATEWAY_FREEZE_SCHEMA, core]
        ).value
    ):
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "bounded source-semantics Gateway product freeze is invalid",
        )
    return permission


if __name__ == "__main__":
    raise SystemExit(main())
