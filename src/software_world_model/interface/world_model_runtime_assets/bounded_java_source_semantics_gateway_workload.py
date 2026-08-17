#!/usr/bin/env python3
"""Run one exact ITER-008 bounded source-semantics Model Egress Gateway."""

from __future__ import annotations

from pathlib import Path
import socket
from typing import Mapping

from software_world_model.ai_infrastructure import (
    ModelEgressGatewayServer,
    ModelGateway,
    PinnedIPVolcengineArkChatTransport,
    VolcengineArkChatCompletionsNoToolsAdapter,
    VolcengineArkModelConfiguration,
    load_ark_chat_conformance_qualification,
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
    if len(descriptors) != 6 or len(set(descriptors)) != 6:
        raise DomainError(
            ErrorCode.CONTROL_STATE_DENIED,
            "bounded source-semantics Gateway requires exactly six connected sockets",
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

    configuration = VolcengineArkModelConfiguration()
    conformance = load_ark_chat_conformance_qualification(
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

    transport = PinnedIPVolcengineArkChatTransport(
        numeric_address=arguments.numeric_provider_address,
        api_key_resolver=configuration.resolve_api_key,
        connected_socket_fds=descriptors,
        audit_writer=record_transport,
        maximum_calls=6,
    )
    adapter = VolcengineArkChatCompletionsNoToolsAdapter(
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
    unused_closed = transport.close_unused_connected_sockets()

    statuses = [str(item["status"]) for item in server_audits]
    dispatch_audits = [
        item for item in transport_audits if item.get("outcome") != "UNUSED_CLOSED"
    ]
    unused_audits = [
        item for item in transport_audits if item.get("outcome") == "UNUSED_CLOSED"
    ]
    sequence = policy.validated_stages
    protocol_valid = (
        4 <= request_count <= 6
        and 2 <= sequence.count("IMPLEMENTATION_INVESTIGATION") <= 4
        and sequence[-2:]
        == ("IMPLEMENTATION_ANSWER_DRAFTING", "IMPLEMENTATION_ANSWER_REVIEW")
    )
    summary_core = {
        "schema": "swm.iter-008.bounded-java-source-semantics-gateway-workload@1",
        "status": (
            "PASS"
            if protocol_valid
            and statuses == ["RESULT"] * request_count
            and len(dispatch_audits) == request_count
            and unused_closed == 6 - request_count
            and len(unused_audits) == unused_closed
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
        "provider_connection_capability": "INHERITED_EXACT_CONNECTED_SOCKET",
        "gateway_listener_capability": "INHERITED_EXACT_BOUND_AF_UNIX_LISTENER",
        "new_socket_syscall_capability": "DENIED_BY_SEATBELT",
        "provider_descriptor_provisioned_count": 6,
        "provider_descriptor_consumed_count": request_count,
        "provider_descriptor_unused_closed_count": unused_closed,
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
        != "model-snapshot-first-world-model-answer@1.4.0"
        or value.get("prompt_ref")
        != "java-source-semantics-world-model-prompt@7"
        or value.get("proposal_vocabulary_ref")
        != "java-source-semantics-world-model-vocabulary@7"
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
