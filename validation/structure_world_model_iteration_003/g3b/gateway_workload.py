#!/usr/bin/env python3
"""Run one distinct, policy-closed ITER-003 G3b Model Egress Gateway."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import stat
from typing import Mapping

from software_world_model.ai_infrastructure import (
    ModelEgressGatewayPolicy,
    ModelEgressGatewayServer,
    ModelGateway,
    PinnedIPVolcengineArkChatTransport,
    VolcengineArkChatCompletionsNoToolsAdapter,
    VolcengineArkModelConfiguration,
    load_ark_chat_conformance_qualification,
    world_model_answer_output_schemas,
)
from software_world_model.cross_cutting import (
    Digest,
    DomainError,
    ErrorCode,
    canonical_json_bytes,
    digest_of,
)
from software_world_model.infrastructure import (
    SqliteDatabase,
    SqliteModelGatewayRepository,
)
from software_world_model.interface.agentic_runtime import (
    load_capability_qualification_proof,
)


_POLICY_DIGEST = (
    "sha256:3e0bfcbf6f1b85d350db167d1bc71ff55f35a76546f15d4d7f14a871aa0326e0"
)
_CONFORMANCE_REF = (
    "CC-ARK-CHAT-NO-TOOLS-001:"
    "sha256:c86aad995802b8dcf687fafcbaf36bccb02768ba55b40151ec9aa4704518cade"
)
_QUALIFICATION_REF = (
    "capability-evaluation:evaluation_result_916b9000db544e92921ec1bdc02a3bc2"
)
_QUALIFICATION_DIGEST = (
    "sha256:005b1bf43c76a64d123b0184cdac1a9e844331896e7ede6279875881d9bcc62c"
)
_PROVIDER_FINGERPRINT = (
    "sha256:420f553a3ce0075818550e08cb1351ce69eaf9871c5a0257aecf88b7b32b88fd"
)
_G3B_FREEZE_REF = "ITER-003-G3B-EXACT-INPUTS@1.0.0"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--socket-path", required=True)
    parser.add_argument("--numeric-provider-address", required=True)
    parser.add_argument("--connected-provider-socket-fd", type=int, required=True)
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
    implementation_commit = _commit(arguments.implementation_commit)
    policy_document = _load_exact_document(arguments.egress_policy)
    if _sha256_file(Path(arguments.egress_policy)) != _POLICY_DIGEST:
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "G3b egress policy file digest is not exact",
        )
    _verify_policy_document(policy_document)
    freeze = _load_exact_document(arguments.g3b_freeze)
    permission_digest = _verify_g3b_freeze(freeze)
    proof = load_capability_qualification_proof(
        arguments.capability_qualification
    )
    if (
        proof.proof_ref != _QUALIFICATION_REF
        or proof.digest.value != _QUALIFICATION_DIGEST
        or proof.capability_id != "world-model-authority-proposal"
        or proof.capability_contract_version != "1.0.0"
        or proof.strategy_id != "model-snapshot-first-world-model-answer"
        or proof.strategy_version != "1.0.2"
        or proof.qualification_kind != "CAPABILITY_EVALUATION"
    ):
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "G3b capability qualification proof is not exact",
        )
    closed = _load_exact_document(arguments.closed_capability_result)
    _verify_closed_result(closed, proof)

    configuration = VolcengineArkModelConfiguration()
    if (
        configuration.fingerprint.value != _PROVIDER_FINGERPRINT
        or configuration.secret_reference != "env:ARK_API_KEY"
    ):
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "G3b Ark configuration drifted from V-009",
        )
    conformance = load_ark_chat_conformance_qualification(
        arguments.conformance_result,
        configuration,
    )
    if conformance.result_ref != _CONFORMANCE_REF:
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "G3b Ark Conformance Result is not exact",
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
        connected_socket_fd=arguments.connected_provider_socket_fd,
        audit_writer=record_transport,
    )
    adapter = VolcengineArkChatCompletionsNoToolsAdapter(
        transport=transport,
        configuration=configuration,
        output_schemas=world_model_answer_output_schemas(),
        live_qualification=conformance,
    )
    policy = ModelEgressGatewayPolicy(
        policy_ref="ITER-003-MODEL-EGRESS-GATEWAY@1.0.0",
        policy_digest=Digest(_POLICY_DIGEST),
        provider_type=configuration.provider_type,
        adapter_version=configuration.adapter_version,
        model_ref=configuration.model_ref,
        provider_configuration_fingerprint=configuration.fingerprint,
        endpoint=(
            "https://ark.cn-beijing.volces.com:443/"
            "api/coding/v3/chat/completions"
        ),
        credential_reference=configuration.secret_reference,
        conformance_result_ref=conformance.result_ref,
        capability_qualification_ref=proof.proof_ref,
        capability_qualification_digest=proof.digest,
    )
    database_path = _future_file(arguments.database)
    with SqliteDatabase(database_path) as database:
        gateway = ModelGateway(
            SqliteModelGatewayRepository(database),
            (adapter,),
        )
        request_count = ModelEgressGatewayServer(
            arguments.socket_path,
            gateway=gateway,
            policy=policy,
            audit_writer=record_server,
        ).serve(
            startup_timeout_seconds=arguments.startup_timeout_seconds,
            idle_timeout_seconds=arguments.idle_timeout_seconds,
        )

    statuses = [str(item["status"]) for item in server_audits]
    summary = {
        "schema": "swm.iter-003.g3b-gateway-workload@1",
        "status": (
            "PASS"
            if request_count == 1
            and statuses == ["RESULT"]
            and len(transport_audits) == 1
            else "FAIL"
        ),
        "environment": "EVALUATION_ONLY",
        "implementation_commit": implementation_commit,
        "g3b_freeze_ref": freeze["freeze_ref"],
        "g3b_freeze_digest": freeze["document_digest"],
        "permission_digest": permission_digest,
        "policy_ref": policy.policy_ref,
        "policy_digest": policy.policy_digest.value,
        "capability_qualification_ref": proof.proof_ref,
        "capability_qualification_digest": proof.digest.value,
        "conformance_result_ref": conformance.result_ref,
        "numeric_provider_address": arguments.numeric_provider_address,
        "numeric_provider_address_scope": (
            transport_audits[0].get("address_scope")
            if len(transport_audits) == 1
            else None
        ),
        "provider_connection_capability": "INHERITED_EXACT_CONNECTED_SOCKET",
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
    _write_new(_future_file(arguments.summary_output), canonical_json_bytes(summary))
    print(canonical_json_bytes(summary).decode("utf-8"))
    return 0 if summary["status"] == "PASS" else 2


def _verify_policy_document(value: Mapping[str, object]) -> None:
    provider = value.get("provider")
    roles = value.get("roles")
    if (
        value.get("policy_ref") != "ITER-003-MODEL-EGRESS-GATEWAY@1.0.0"
        or value.get("default_action") != "DENY"
        or not isinstance(provider, dict)
        or provider.get("provider_type") != "VOLCENGINE_ARK"
        or provider.get("adapter_version")
        != "openai-chat-completions-no-tools@8"
        or provider.get("model_ref") != "glm-5-2-260617"
        or provider.get("credential_reference") != "env:ARK_API_KEY"
        or not isinstance(roles, dict)
        or roles.get("answer", {}).get("dns") != "DENY"
        or roles.get("answer", {}).get("inet") != "DENY"
        or roles.get("answer", {}).get("inet6") != "DENY"
        or roles.get("citation_projector", {}).get("all_outbound") != "DENY"
        or roles.get("model_egress_gateway", {}).get("other_outbound")
        != "DENY"
    ):
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "G3b egress policy document is not exact",
        )


def _verify_g3b_freeze(value: Mapping[str, object]) -> str:
    core = {key: item for key, item in value.items() if key != "document_digest"}
    disclosure = value.get("disclosure")
    activation = value.get("activation")
    v009 = value.get("v009")
    if (
        value.get("schema") != "swm.iter-003.g3b-input-freeze@1"
        or value.get("freeze_ref") != _G3B_FREEZE_REF
        or value.get("document_digest") != digest_of(core).value
        or not isinstance(disclosure, dict)
        or disclosure.get("confirmed") is not True
        or disclosure.get("repeat_confirmation_required") is not False
        or disclosure.get("production_activation_included") is not False
        or disclosure.get("permission_digest")
        != "sha256:d0a572d621a1163e8e9e41add704f682dcac2aabb3a3e99c0408ed188813a8a9"
        or not isinstance(activation, dict)
        or activation.get("environment") != "EVALUATION_ONLY"
        or activation.get("production_activation") != "NOT_EXECUTED"
        or not isinstance(v009, dict)
        or v009.get("capability_qualification_ref") != _QUALIFICATION_REF
        or v009.get("capability_qualification_digest")
        != _QUALIFICATION_DIGEST
        or v009.get("conformance_result_ref") != _CONFORMANCE_REF
        or v009.get("baseline_seal_digest")
        != "sha256:7be049fe746a71cb3b9c3941d81e8e51076256d0f8dac61ba5a5c88c873ecbdd"
    ):
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "G3b disclosure/freeze authority is invalid",
        )
    return str(disclosure["permission_digest"])


def _verify_closed_result(value: Mapping[str, object], proof) -> None:
    core = {key: item for key, item in value.items() if key != "document_digest"}
    result = value.get("result")
    validity = value.get("validity")
    qualification = value.get("qualification")
    definition = value.get("definition")
    provider = value.get("provider")
    try:
        valid_until = datetime.fromisoformat(str(validity["valid_until"]))
    except (KeyError, TypeError, ValueError) as exc:
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "G3b capability validity time is invalid",
        ) from exc
    if (
        value.get("schema")
        != "swm.iter-003.world-model-ce-closed-result@1"
        or value.get("document_digest") != digest_of(core).value
        or value.get("freeze_checkpoint")
        != "019f9fced69110c6a7e357a4ea2394ec6742fd2e"
        or value.get("closed_result_status") != "PASS_VALID"
        or value.get("failure_count") != 0
        or value.get("unknown_count") != 0
        or value.get("required_case_count") != 7
        or not isinstance(result, dict)
        or result.get("result_id") != proof.result_ref
        or result.get("conclusion") != "PASS"
        or result.get("failed_case_ids") != []
        or result.get("inconclusive_case_ids") != []
        or len(result.get("passed_case_ids", [])) != 7
        or not isinstance(validity, dict)
        or validity.get("status") != "VALID"
        or validity.get("result_id") != proof.result_ref
        or valid_until.tzinfo is None
        or datetime.now(timezone.utc) >= valid_until
        or qualification != {
            "proof_ref": proof.proof_ref,
            "capability_id": proof.capability_id,
            "capability_contract_version": proof.capability_contract_version,
            "strategy_id": proof.strategy_id,
            "strategy_version": proof.strategy_version,
            "result_ref": proof.result_ref,
            "validity_ref": proof.validity_ref,
            "qualification_kind": proof.qualification_kind,
            "digest": proof.digest.value,
        }
        or not isinstance(definition, dict)
        or definition.get("strategy_id")
        != "model-snapshot-first-world-model-answer"
        or definition.get("strategy_version") != "1.0.2"
        or definition.get("implementation_digest")
        != "sha256:4a83df22f535dc8fa1712b3fc04f7a6ee3960263070ed5366ab18b3692446fa0"
        or not isinstance(provider, dict)
        or provider.get("conformance_result_ref") != _CONFORMANCE_REF
        or provider.get("configuration_fingerprint")
        != _PROVIDER_FINGERPRINT
        or provider.get("actual_model_fingerprint") != "glm-5.2"
    ):
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "G3b closed capability Result is invalid or stale",
        )


def _load_exact_document(path_text: str) -> dict[str, object]:
    path = Path(path_text)
    raw = path.read_bytes()
    try:
        value = json.loads(raw, object_pairs_hook=_unique_object)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "G3b input document is invalid",
        ) from exc
    if not isinstance(value, dict):
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "G3b input document must be an object",
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
        raise ValueError("G3b output path must be canonical and absolute")
    if path.parent.resolve(strict=True) != path.parent:
        raise ValueError("G3b output parent must be canonical")
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
            raise RuntimeError("G3b output is not a regular file")
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
    return "sha256:" + sha256(path.read_bytes()).hexdigest()


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
