#!/usr/bin/env python3
"""Run one exact ITER-007 source-semantics Model Egress Gateway."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import socket
import stat
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
from software_world_model.ai_infrastructure.java_source_semantics_model_egress_qualification import (
    JAVA_SOURCE_SEMANTICS_MODEL_EGRESS_POLICY_FILE_DIGEST,
    load_java_source_semantics_gateway_qualification_binding,
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


JAVA_SOURCE_SEMANTICS_GATEWAY_FREEZE_SCHEMA = (
    "SWM-ITER-007-JAVA-SOURCE-SEMANTICS-GATEWAY-FREEZE@1"
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--socket-path", required=True)
    parser.add_argument("--gateway-listener-socket-fd", type=int, required=True)
    parser.add_argument("--numeric-provider-address", required=True)
    parser.add_argument(
        "--connected-provider-socket-fd",
        action="append",
        type=int,
        required=True,
    )
    parser.add_argument("--database", required=True)
    parser.add_argument("--conformance-result", required=True)
    parser.add_argument("--capability-qualification", required=True)
    parser.add_argument("--closed-capability-result", required=True)
    parser.add_argument("--egress-policy", required=True)
    parser.add_argument("--g3b-freeze", required=True)
    parser.add_argument("--implementation-commit", required=True)
    parser.add_argument("--server-audit-output", required=True)
    parser.add_argument("--transport-audit-output", required=True)
    parser.add_argument("--summary-output", required=True)
    parser.add_argument("--startup-timeout-seconds", type=float, default=60.0)
    parser.add_argument("--idle-timeout-seconds", type=float, default=0.25)
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    if (
        len(arguments.connected_provider_socket_fd) != 3
        or len(set(arguments.connected_provider_socket_fd)) != 3
    ):
        raise DomainError(
            ErrorCode.CONTROL_STATE_DENIED,
            "source-semantics Gateway requires exactly three connected sockets",
        )
    implementation_commit = _commit(arguments.implementation_commit)
    freeze = _load_document(arguments.g3b_freeze)
    permission_digest = _verify_freeze(freeze)
    if (
        _sha256_file(Path(arguments.egress_policy))
        != JAVA_SOURCE_SEMANTICS_MODEL_EGRESS_POLICY_FILE_DIGEST
    ):
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "source-semantics Gateway policy file digest is not exact",
        )
    binding = load_java_source_semantics_gateway_qualification_binding(
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
            "source-semantics Gateway freeze uses another qualification",
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
            "source-semantics Gateway conformance binding drifted",
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
        connected_socket_fds=tuple(arguments.connected_provider_socket_fd),
        audit_writer=record_transport,
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

    statuses = [str(item["status"]) for item in server_audits]
    exact_statuses = ["RESULT", "RESULT", "RESULT"]
    summary_core = {
        "schema": "swm.iter-007.java-source-semantics-gateway-workload@1",
        "status": (
            "PASS"
            if request_count == 3
            and statuses == exact_statuses
            and len(transport_audits) == 3
            else "FAIL"
        ),
        "environment": "EVALUATION_ONLY",
        "implementation_commit": implementation_commit,
        "java_source_semantics_gateway_freeze_ref": freeze["freeze_ref"],
        "java_source_semantics_gateway_freeze_digest": freeze[
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
        "qualification_valid_until": (
            binding.qualification_valid_until.isoformat()
        ),
        "conformance_result_ref": conformance.result_ref,
        "numeric_provider_address": arguments.numeric_provider_address,
        "numeric_provider_address_scope": (
            transport_audits[0].get("address_scope")
            if len(transport_audits) == 3
            and len({item.get("address_scope") for item in transport_audits}) == 1
            else None
        ),
        "provider_connection_capability": "INHERITED_EXACT_CONNECTED_SOCKET",
        "gateway_listener_capability": "INHERITED_EXACT_BOUND_AF_UNIX_LISTENER",
        "new_socket_syscall_capability": "DENIED_BY_SEATBELT",
        "provider_call_count": request_count,
        "https_dispatch_count": len(transport_audits),
        "server_audit_count": len(server_audits),
        "server_statuses": statuses,
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
        or value.get("schema") != JAVA_SOURCE_SEMANTICS_GATEWAY_FREEZE_SCHEMA
        or value.get("freeze_ref")
        != "ITER-007-JAVA-SOURCE-SEMANTICS-PRODUCT-GATEWAY-CANDIDATE@1"
        or value.get("environment") != "EVALUATION_ONLY"
        or value.get("strategy_ref")
        != "model-snapshot-first-world-model-answer@1.2.2"
        or value.get("prompt_ref")
        != "java-source-semantics-world-model-prompt@3"
        or value.get("proposal_vocabulary_ref")
        != "java-source-semantics-world-model-vocabulary@3"
        or value.get("egress_policy_digest")
        != JAVA_SOURCE_SEMANTICS_MODEL_EGRESS_POLICY_FILE_DIGEST
        or value.get("production_activation") != "NOT_EXECUTED"
        or not isinstance(permission, str)
        or not permission.startswith("sha256:")
        or value.get("document_digest")
        != digest_of([JAVA_SOURCE_SEMANTICS_GATEWAY_FREEZE_SCHEMA, core]).value
    ):
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "source-semantics Gateway product freeze is invalid",
        )
    return permission


def _load_document(path_text: str) -> dict[str, object]:
    try:
        value = json.loads(
            Path(path_text).read_bytes(),
            object_pairs_hook=_unique_object,
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "source-semantics Gateway input cannot be loaded",
        ) from exc
    if not isinstance(value, dict):
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "source-semantics Gateway input must be an object",
        )
    return value


def _unique_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def _future_file(value: str) -> Path:
    path = Path(value)
    if not path.is_absolute() or path.resolve(strict=False) != path:
        raise ValueError(
            "source-semantics Gateway output must be canonical and absolute"
        )
    if path.parent.resolve(strict=True) != path.parent:
        raise ValueError("source-semantics Gateway output parent is not canonical")
    if path.exists() or path.is_symlink():
        raise FileExistsError(path)
    return path


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
            raise RuntimeError("source-semantics Gateway output is not regular")
    finally:
        os.close(descriptor)


def _append_document(path: Path, value: Mapping[str, object]) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags, 0o600)
    try:
        os.write(descriptor, canonical_json_bytes(dict(value)) + b"\n")
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _sha256_file(path: Path) -> str:
    return "sha256:" + __import__("hashlib").sha256(path.read_bytes()).hexdigest()


def _commit(value: object) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 40
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError("implementation commit must be exact lowercase 40-hex")
    return value


if __name__ == "__main__":
    raise SystemExit(main())
