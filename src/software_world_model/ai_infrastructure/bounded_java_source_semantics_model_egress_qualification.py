"""Load the exact ITER-008 bounded-investigation Gateway qualification.

The ITER-007 fixed-plan qualification is deliberately incompatible with this
contract.  A bounded policy is created only from one closed result that binds
all investigation, negative-completeness, Draft, and Review cases and preserves
the exact input/result/trace digest for every model call.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Mapping

from software_world_model.application_services import QualificationProof
from software_world_model.cross_cutting import (
    Digest,
    DomainError,
    ErrorCode,
    digest_of,
)

from .model_egress_gateway import (
    BOUNDED_JAVA_SOURCE_SEMANTICS_MODEL_EGRESS_GATEWAY_POLICY_REF,
    QualifiedJavaSourceSemanticsModelEgressGatewayPolicy,
)
from .deepseek_chat_adapter import (
    DeepSeekModelConfiguration,
    verify_deepseek_transport_session_audit,
)
from .versioned_world_model_answer_strategy import (
    JAVA_SOURCE_SEMANTICS_INVESTIGATION_ARGUMENT_COMPILER_REF,
    JAVA_SOURCE_SEMANTICS_WORLD_MODEL_PROPOSAL_CONTRACT,
    java_source_semantics_world_model_output_contract_digest,
    world_model_answer_prompt_program_digest,
    world_model_answer_strategy_implementation_digest,
)


BOUNDED_JAVA_SOURCE_SEMANTICS_CAPABILITY_CLOSED_RESULT_SCHEMA = (
    "swm.iter-008.bounded-java-source-semantics-ce-closed-result@2"
)
BOUNDED_JAVA_SOURCE_SEMANTICS_CAPABILITY_QUALIFICATION_DOCUMENT_SCHEMA = (
    "swm.capability-qualification-proof@1"
)
BOUNDED_JAVA_SOURCE_SEMANTICS_EVALUATION_THRESHOLD_REF = (
    "all-eighteen-bounded-java-source-semantics-cases-exact-pass@1"
)
BOUNDED_JAVA_SOURCE_SEMANTICS_EVALUATION_METRIC_CONTRACT = {
    "metric_ref": "bounded-java-source-semantics-exact-case-verdict@1",
    "required_case_count": 18,
    "required_status": "PASS",
    "failure_count": 0,
    "unknown_count": 0,
    "per_call_trace_evidence_required": True,
    "transport_session_evidence_required": True,
    "maximum_pre_dispatch_tls_handshake_attempts": 3,
    "request_retry_count": 0,
}
BOUNDED_JAVA_SOURCE_SEMANTICS_QUALIFICATION_CASE_CALLS = (
    ("WM-JSS-I8-FIRST-CANDIDATES-001", 1),
    ("WM-JSS-I8-ZERO-CANDIDATES-002", 1),
    ("WM-JSS-I8-N-CANDIDATES-003", 1),
    ("WM-JSS-I8-RESULT-DRIVEN-BATCH-004", 2),
    ("WM-JSS-I8-DECLARED-INVENTORY-005", 4),
    ("WM-JSS-I8-DIRECT-NEIGHBORHOOD-006", 3),
    ("WM-JSS-I8-PATH-EXISTS-007", 3),
    ("WM-JSS-I8-ALL-SIMPLE-PATHS-008", 3),
    ("WM-JSS-I8-LEGAL-FINISH-009", 3),
    ("WM-JSS-I8-MAX-FOUR-010", 3),
    ("WM-JSS-I8-BUDGET-EXHAUSTION-011", 4),
    ("WM-JSS-I8-CYCLE-PROGRESS-012", 2),
    ("WM-JSS-I8-REF-PROVENANCE-013", 2),
    ("WM-JSS-I8-NEGATIVE-COMPLETE-014", 2),
    ("WM-JSS-I8-NEGATIVE-QUERY-UNKNOWN-015", 2),
    ("WM-JSS-I8-NEGATIVE-REPRESENTATION-UNKNOWN-016", 2),
    ("WM-JSS-I8-DRAFT-017", 1),
    ("WM-JSS-I8-REVIEW-018", 1),
)
BOUNDED_JAVA_SOURCE_SEMANTICS_CAPABILITY_SUITE_DIGEST = Digest(
    "sha256:68900e343fb04076ad9ceab99aea29eaa11cbdb254b28c28298169d791d8e6de"
)
BOUNDED_JAVA_SOURCE_SEMANTICS_CAPABILITY_ORACLE_DIGEST = Digest(
    "sha256:3c20ce70181fd6c9e974d34b7ff597afbf5cc0f149a1efe0541f6ff10ae669e7"
)
BOUNDED_JAVA_SOURCE_SEMANTICS_MODEL_EGRESS_POLICY_PATH = (
    Path(__file__).resolve().with_name(
        "bounded_java_source_semantics_model_egress_policy.json"
    )
)
BOUNDED_JAVA_SOURCE_SEMANTICS_MODEL_EGRESS_POLICY_FILE_DIGEST = (
    "sha256:889afd1845f573ee0a9565d3fd2f6e69b6c824b72c20138c12cde93da7c407d0"
)
_BOUNDED_JAVA_SOURCE_SEMANTICS_QUALIFICATION_RESOURCE_POLICY = {
    "schema": "swm.iter-008.bounded-qualification-resource-policy@1",
    "provider_type": "DEEPSEEK",
    "adapter_version": "deepseek-chat-completions-no-tools@5",
    "model_ref": "deepseek-v4-pro",
    "provider_configuration_fingerprint": (
        "sha256:31dc8d9bd143ab4c5aee94a5e9cdafdbd19103a645ad40e30893348ab3c2640d"
    ),
    "model_egress_policy_ref": (
        BOUNDED_JAVA_SOURCE_SEMANTICS_MODEL_EGRESS_GATEWAY_POLICY_REF
    ),
    "model_egress_policy_digest": (
        BOUNDED_JAVA_SOURCE_SEMANTICS_MODEL_EGRESS_POLICY_FILE_DIGEST
    ),
    "maximum_output_tokens": 1000,
    "timeout_milliseconds": 180_000,
    "classification": "INTERNAL",
    "required_case_count": 18,
    "provider_request_count": 40,
    "connection_policy": "PERSISTENT_VERIFIED_TLS_HTTP11_KEEP_ALIVE@1",
    "maximum_pre_dispatch_tls_handshake_attempts": 3,
    "credential_resolution_after_verified_tls": True,
    "transport_session_audit_schema": (
        "SWM-DEEPSEEK-TRANSPORT-SESSION-AUDIT@1"
    ),
    "retries_allowed": False,
}
BOUNDED_JAVA_SOURCE_SEMANTICS_QUALIFICATION_RESOURCE_POLICY_REF = (
    "ITER-008-BOUNDED-JAVA-SOURCE-SEMANTICS-QUALIFICATION-RESOURCE-POLICY@1:"
    f"{digest_of(_BOUNDED_JAVA_SOURCE_SEMANTICS_QUALIFICATION_RESOURCE_POLICY).value}"
)


@dataclass(frozen=True, slots=True)
class BoundedJavaSourceSemanticsGatewayQualificationBinding:
    capability_qualification_ref: str
    capability_qualification_digest: Digest
    qualification_document_digest: Digest
    closed_capability_result_digest: Digest
    qualification_valid_until: datetime
    conformance_result_ref: str

    def create_policy(
        self,
        *,
        configuration: DeepSeekModelConfiguration,
        conformance_result_ref: str,
    ) -> QualifiedJavaSourceSemanticsModelEgressGatewayPolicy:
        if conformance_result_ref != self.conformance_result_ref:
            raise DomainError(
                ErrorCode.QUALIFICATION_INVALID,
                "bounded capability and Conformance authorities differ",
            )
        return QualifiedJavaSourceSemanticsModelEgressGatewayPolicy(
            policy_ref=(
                BOUNDED_JAVA_SOURCE_SEMANTICS_MODEL_EGRESS_GATEWAY_POLICY_REF
            ),
            policy_digest=Digest(
                BOUNDED_JAVA_SOURCE_SEMANTICS_MODEL_EGRESS_POLICY_FILE_DIGEST
            ),
            provider_type=configuration.provider_type,
            adapter_version=configuration.adapter_version,
            model_ref=configuration.model_ref,
            provider_configuration_fingerprint=configuration.fingerprint,
            endpoint=configuration.endpoint,
            credential_reference=configuration.secret_reference,
            conformance_result_ref=conformance_result_ref,
            capability_qualification_ref=self.capability_qualification_ref,
            capability_qualification_digest=self.capability_qualification_digest,
            closed_capability_result_digest=self.closed_capability_result_digest,
            qualification_valid_until=self.qualification_valid_until,
            max_provider_calls=6,
        )


def load_bounded_java_source_semantics_gateway_qualification_binding(
    *,
    qualification_path: str | Path,
    closed_result_path: str | Path,
    policy_path: str | Path = (
        BOUNDED_JAVA_SOURCE_SEMANTICS_MODEL_EGRESS_POLICY_PATH
    ),
    now: datetime | None = None,
) -> BoundedJavaSourceSemanticsGatewayQualificationBinding:
    policy_raw = Path(policy_path).resolve(strict=True).read_bytes()
    if (
        "sha256:" + hashlib.sha256(policy_raw).hexdigest()
        != BOUNDED_JAVA_SOURCE_SEMANTICS_MODEL_EGRESS_POLICY_FILE_DIGEST
    ):
        _invalid("bounded source-semantics egress policy file digest drifted")
    _verify_policy(_unique_json(policy_raw, "bounded egress policy"))

    qualification_document = _unique_json(
        Path(qualification_path).resolve(strict=True).read_bytes(),
        "bounded capability qualification",
    )
    proof = _qualification_proof(qualification_document)
    closed = _unique_json(
        Path(closed_result_path).resolve(strict=True).read_bytes(),
        "bounded closed capability result",
    )
    closed_core = {
        key: value for key, value in closed.items() if key != "document_digest"
    }
    expected_cases = tuple(
        case_id
        for case_id, _ in BOUNDED_JAVA_SOURCE_SEMANTICS_QUALIFICATION_CASE_CALLS
    )
    expected_call_counts = dict(
        BOUNDED_JAVA_SOURCE_SEMANTICS_QUALIFICATION_CASE_CALLS
    )
    expected_provider_requests = sum(expected_call_counts.values())
    try:
        transport_session = verify_deepseek_transport_session_audit(
            closed.get("transport_session")
        )
    except DomainError as exc:
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "bounded source-semantics transport session evidence is invalid",
        ) from exc
    if (
        closed.get("schema")
        != BOUNDED_JAVA_SOURCE_SEMANTICS_CAPABILITY_CLOSED_RESULT_SCHEMA
        or closed.get("document_digest") != digest_of(closed_core).value
        or closed.get("closed_result_status") != "PASS_VALID"
        or closed.get("failure_count") != 0
        or closed.get("unknown_count") != 0
        or closed.get("required_case_count") != len(expected_cases)
        or closed.get("provider_request_count") != expected_provider_requests
        or transport_session["http_dispatch_count"]
        != expected_provider_requests
        or not 1 <= transport_session["tls_handshake_success_count"] <= 3
        or transport_session["connection_reuse_count"]
        != (
            expected_provider_requests
            - transport_session["tls_handshake_success_count"]
        )
        or transport_session["post_dispatch_outcome_unknown_count"] != 0
        or transport_session["credential_resolution_count"]
        != expected_provider_requests
        or transport_session["credential_resolution_success_count"]
        != expected_provider_requests
        or closed.get("production_activation") != "NOT_EXECUTED"
        or closed.get("suite_digest")
        != BOUNDED_JAVA_SOURCE_SEMANTICS_CAPABILITY_SUITE_DIGEST.value
        or closed.get("oracle_digest")
        != BOUNDED_JAVA_SOURCE_SEMANTICS_CAPABILITY_ORACLE_DIGEST.value
    ):
        _invalid("bounded source-semantics closed result is not PASS_VALID")

    definition = closed.get("definition")
    result = closed.get("result")
    validity = closed.get("validity")
    qualification = closed.get("qualification")
    case_evidence = closed.get("case_evidence")
    if not all(
        isinstance(item, Mapping)
        for item in (definition, result, validity, qualification)
    ) or not isinstance(case_evidence, list):
        _invalid("bounded capability authority chain is incomplete")
    assert isinstance(definition, Mapping)
    assert isinstance(result, Mapping)
    assert isinstance(validity, Mapping)
    assert isinstance(qualification, Mapping)
    contract = JAVA_SOURCE_SEMANTICS_WORLD_MODEL_PROPOSAL_CONTRACT
    definition_cases = definition.get("cases")
    if (
        definition.get("capability_id") != "world-model-authority-proposal"
        or definition.get("capability_contract_version")
        != contract.capability_contract_version
        or definition.get("strategy_id")
        != "model-snapshot-first-world-model-answer"
        or definition.get("strategy_version") != contract.strategy_version
        or definition.get("model_ref") != "deepseek-v4-pro"
        or definition.get("adapter_version")
        != "deepseek-chat-completions-no-tools@5"
        or definition.get("provider_configuration_fingerprint")
        != "sha256:31dc8d9bd143ab4c5aee94a5e9cdafdbd19103a645ad40e30893348ab3c2640d"
        or not str(definition.get("conformance_result_ref", "")).startswith(
            "CC-DEEPSEEK-CHAT-NO-TOOLS-001:sha256:"
        )
        or definition.get("implementation_digest")
        != world_model_answer_strategy_implementation_digest(contract).value
        or definition.get("prompt_program_digest")
        != world_model_answer_prompt_program_digest(contract).value
        or definition.get("output_schema_digest")
        != java_source_semantics_world_model_output_contract_digest(contract).value
        or definition.get("metric_contract_digest")
        != digest_of(
            BOUNDED_JAVA_SOURCE_SEMANTICS_EVALUATION_METRIC_CONTRACT
        ).value
        or definition.get("threshold_ref")
        != BOUNDED_JAVA_SOURCE_SEMANTICS_EVALUATION_THRESHOLD_REF
        or definition.get("resource_policy_ref")
        != BOUNDED_JAVA_SOURCE_SEMANTICS_QUALIFICATION_RESOURCE_POLICY_REF
        or definition.get("tool_policy_ref")
        != "model-no-tools-no-source-no-evidence@1"
        or not isinstance(definition_cases, list)
        or tuple(item.get("case_id") for item in definition_cases if isinstance(item, Mapping))
        != expected_cases
        or len(definition_cases) != len(expected_cases)
        or result.get("conclusion") != "PASS"
        or result.get("actual_model_fingerprints") != ["deepseek-v4-pro"]
        or not isinstance(result.get("passed_case_ids"), list)
        or len(result["passed_case_ids"]) != len(expected_cases)
        or any(
            not isinstance(case_id, str)
            for case_id in result["passed_case_ids"]
        )
        or frozenset(result["passed_case_ids"]) != frozenset(expected_cases)
        or result.get("failed_case_ids") != []
        or result.get("inconclusive_case_ids") != []
        or validity.get("status") != "VALID"
        or qualification.get("proof_ref") != proof.proof_ref
        or qualification.get("digest") != proof.digest.value
        or qualification.get("result_ref") != proof.result_ref
        or qualification.get("validity_ref") != proof.validity_ref
    ):
        _invalid("bounded source-semantics Result does not bind the exact contract")
    _verify_case_evidence(case_evidence, expected_call_counts)
    if (
        proof.capability_id != "world-model-authority-proposal"
        or proof.capability_contract_version
        != contract.capability_contract_version
        or proof.strategy_id != "model-snapshot-first-world-model-answer"
        or proof.strategy_version != contract.strategy_version
        or proof.qualification_kind != "CAPABILITY_EVALUATION"
        or proof.result_ref != result.get("result_id")
    ):
        _invalid("bounded source-semantics proof is outside the exact contract")
    try:
        valid_until = datetime.fromisoformat(
            str(validity["valid_until"]).replace("Z", "+00:00")
        )
    except (KeyError, ValueError) as exc:
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "bounded source-semantics qualification expiration is invalid",
        ) from exc
    checked_at = now or datetime.now(timezone.utc)
    if (
        valid_until.tzinfo is None
        or valid_until.utcoffset() is None
        or checked_at.tzinfo is None
        or checked_at.utcoffset() is None
        or valid_until.astimezone(timezone.utc)
        <= checked_at.astimezone(timezone.utc)
    ):
        _invalid("bounded source-semantics capability qualification is expired")
    return BoundedJavaSourceSemanticsGatewayQualificationBinding(
        capability_qualification_ref=proof.proof_ref,
        capability_qualification_digest=proof.digest,
        qualification_document_digest=Digest(
            str(qualification_document["document_digest"])
        ),
        closed_capability_result_digest=Digest(str(closed["document_digest"])),
        qualification_valid_until=valid_until,
        conformance_result_ref=str(definition["conformance_result_ref"]),
    )


def _verify_case_evidence(
    evidence: list[object],
    expected_call_counts: Mapping[str, int],
) -> None:
    if len(evidence) != len(expected_call_counts):
        _invalid("bounded qualification case evidence is incomplete")
    seen: list[str] = []
    for item in evidence:
        if not isinstance(item, Mapping) or set(item) != {
            "case_id",
            "status",
            "model_call_count",
            "step_input_digests",
            "step_result_digests",
            "trace_digests",
        }:
            _invalid("bounded qualification case evidence shape is invalid")
        case_id = item.get("case_id")
        count = item.get("model_call_count")
        if (
            not isinstance(case_id, str)
            or case_id not in expected_call_counts
            or case_id in seen
            or item.get("status") != "PASS"
            or count != expected_call_counts[case_id]
        ):
            _invalid("bounded qualification case evidence verdict is invalid")
        for field in (
            "step_input_digests",
            "step_result_digests",
            "trace_digests",
        ):
            values = item.get(field)
            if not isinstance(values, list) or len(values) != count:
                _invalid("bounded qualification per-call evidence is incomplete")
            try:
                digests = tuple(Digest(value) for value in values)
            except (TypeError, ValueError) as exc:
                raise DomainError(
                    ErrorCode.QUALIFICATION_INVALID,
                    "bounded qualification per-call digest is invalid",
                ) from exc
            if len(set(digests)) != len(digests):
                _invalid("bounded qualification per-call evidence repeats a digest")
        seen.append(case_id)
    if tuple(seen) != tuple(expected_call_counts):
        _invalid("bounded qualification case evidence order is not canonical")


def _qualification_proof(document: Mapping[str, object]) -> QualificationProof:
    raw = document.get("proof")
    if (
        set(document) != {"schema", "proof", "document_digest"}
        or document.get("schema")
        != BOUNDED_JAVA_SOURCE_SEMANTICS_CAPABILITY_QUALIFICATION_DOCUMENT_SCHEMA
        or not isinstance(raw, Mapping)
    ):
        _invalid("bounded qualification document is invalid")
    core = {"schema": document["schema"], "proof": raw}
    if document.get("document_digest") != digest_of(core).value:
        _invalid("bounded qualification document digest is invalid")
    required = {
        "proof_ref",
        "capability_id",
        "capability_contract_version",
        "strategy_id",
        "strategy_version",
        "result_ref",
        "validity_ref",
        "qualification_kind",
        "digest",
    }
    if set(raw) != required or any(
        not isinstance(raw[key], str) for key in required
    ):
        _invalid("bounded qualification fields are invalid")
    proof = QualificationProof(
        proof_ref=raw["proof_ref"],
        capability_id=raw["capability_id"],
        capability_contract_version=raw["capability_contract_version"],
        strategy_id=raw["strategy_id"],
        strategy_version=raw["strategy_version"],
        result_ref=raw["result_ref"],
        validity_ref=raw["validity_ref"],
        qualification_kind=raw["qualification_kind"],
        digest=Digest(raw["digest"]),
    )
    if not proof.verify_digest():
        _invalid("bounded qualification proof digest is invalid")
    return proof


def _verify_policy(policy: Mapping[str, object]) -> None:
    contract_value = policy.get("proposal_contract")
    requirements = policy.get("qualification_requirements")
    provider = policy.get("provider")
    roles = policy.get("roles")
    gateway_role = (
        roles.get("model_egress_gateway")
        if isinstance(roles, Mapping)
        else None
    )
    call_protocol = (
        contract_value.get("call_protocol")
        if isinstance(contract_value, Mapping)
        else None
    )
    contract = JAVA_SOURCE_SEMANTICS_WORLD_MODEL_PROPOSAL_CONTRACT
    if (
        policy.get("schema")
        != "swm.iter-008.bounded-java-source-semantics-model-egress-gateway-policy@1"
        or policy.get("policy_ref")
        != BOUNDED_JAVA_SOURCE_SEMANTICS_MODEL_EGRESS_GATEWAY_POLICY_REF
        or policy.get("default_action") != "DENY"
        or policy.get("environment") != "EVALUATION_ONLY"
        or policy.get("production_activation") != "NOT_EXECUTED"
        or not isinstance(provider, Mapping)
        or provider.get("selection_policy")
        != "PRE_DISPATCH_FIRST_CURRENTLY_QUALIFIED_NO_REQUEST_RETRY"
        or provider.get("preference_order") != ["VOLCENGINE_ARK", "DEEPSEEK"]
        or provider.get("selected_provider_type") != "DEEPSEEK"
        or provider.get("provider_type") != "DEEPSEEK"
        or provider.get("adapter_version")
        != "deepseek-chat-completions-no-tools@5"
        or provider.get("requested_model_ref") != "deepseek-v4-pro"
        or provider.get("actual_model_fingerprint") != "deepseek-v4-pro"
        or provider.get("configuration_fingerprint")
        != "sha256:31dc8d9bd143ab4c5aee94a5e9cdafdbd19103a645ad40e30893348ab3c2640d"
        or provider.get("endpoint")
        != "https://api.deepseek.com/chat/completions"
        or provider.get("credential_reference") != "env:DEEPSEEK_API_KEY"
        or provider.get("connection_policy")
        != "PERSISTENT_VERIFIED_TLS_HTTP11_KEEP_ALIVE@1"
        or provider.get("maximum_pre_dispatch_tls_handshake_attempts") != 3
        or provider.get("credential_resolution_after_verified_tls") is not True
        or provider.get("request_retry_allowed") is not False
        or provider.get("fallback_after_dispatch") is not False
        or not isinstance(contract_value, Mapping)
        or contract_value.get("capability_contract_version")
        != contract.capability_contract_version
        or contract_value.get("strategy_ref") != contract.strategy_ref
        or contract_value.get("prompt_ref") != contract.prompt_ref
        or contract_value.get("proposal_vocabulary_ref")
        != contract.proposal_vocabulary_ref
        or contract_value.get("instruction_transformation_ref")
        != contract.instruction_transformation_ref
        or contract_value.get("argument_compiler_ref")
        != JAVA_SOURCE_SEMANTICS_INVESTIGATION_ARGUMENT_COMPILER_REF
        or contract_value.get("available_operations")
        != list(contract.available_operations)
        or not isinstance(call_protocol, Mapping)
        or call_protocol.get("investigation_capability")
        != "IMPLEMENTATION_INVESTIGATION"
        or call_protocol.get("minimum_investigation_calls") != 2
        or call_protocol.get("maximum_investigation_calls") != 4
        or call_protocol.get("terminal_capabilities")
        != ["IMPLEMENTATION_ANSWER_DRAFTING", "IMPLEMENTATION_ANSWER_REVIEW"]
        or call_protocol.get("minimum_total_calls") != 4
        or call_protocol.get("maximum_total_calls") != 6
        or call_protocol.get("retries_allowed") is not False
        or not isinstance(requirements, Mapping)
        or requirements.get("closed_result_status") != "PASS_VALID"
        or requirements.get("required_case_count")
        != len(BOUNDED_JAVA_SOURCE_SEMANTICS_QUALIFICATION_CASE_CALLS)
        or requirements.get("failure_count") != 0
        or requirements.get("unknown_count") != 0
        or requirements.get("qualification_kind") != "CAPABILITY_EVALUATION"
        or requirements.get("validity_status") != "VALID"
        or requirements.get("step_evidence_required") is not True
        or requirements.get("transport_session_evidence_required") is not True
        or requirements.get("policy_drift_invalidates_qualification") is not True
        or not isinstance(gateway_role, Mapping)
        or gateway_role.get("credential_visibility")
        != "GATEWAY_ONLY_AT_FINAL_HTTPS_DISPATCH"
        or gateway_role.get("allowed_outbound")
        != "EXACT_INHERITED_CONNECTED_TLS_SOCKET_ONLY"
        or gateway_role.get("descriptor_policy")
        != "PROVISION_THREE_CONSUME_ONE_TO_THREE_CLOSE_UNUSED"
        or gateway_role.get("connection_policy")
        != "PERSISTENT_VERIFIED_TLS_HTTP11_KEEP_ALIVE@1"
        or gateway_role.get("pre_dispatch_tls_policy")
        != "MAXIMUM_THREE_BEFORE_CREDENTIAL_OR_HTTP_ONLY"
        or gateway_role.get("other_outbound") != "DENY"
    ):
        _invalid("bounded source-semantics egress policy content drifted")


def _unique_json(raw: bytes, label: str) -> dict[str, object]:
    try:
        value = json.loads(raw, object_pairs_hook=_unique_object)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            f"{label} cannot be loaded",
        ) from exc
    if not isinstance(value, dict):
        _invalid(f"{label} must contain one object")
    return value


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def _invalid(message: str) -> None:
    raise DomainError(ErrorCode.QUALIFICATION_INVALID, message)


__all__ = [
    "BOUNDED_JAVA_SOURCE_SEMANTICS_CAPABILITY_CLOSED_RESULT_SCHEMA",
    "BOUNDED_JAVA_SOURCE_SEMANTICS_CAPABILITY_ORACLE_DIGEST",
    "BOUNDED_JAVA_SOURCE_SEMANTICS_CAPABILITY_QUALIFICATION_DOCUMENT_SCHEMA",
    "BOUNDED_JAVA_SOURCE_SEMANTICS_CAPABILITY_SUITE_DIGEST",
    "BOUNDED_JAVA_SOURCE_SEMANTICS_EVALUATION_METRIC_CONTRACT",
    "BOUNDED_JAVA_SOURCE_SEMANTICS_EVALUATION_THRESHOLD_REF",
    "BOUNDED_JAVA_SOURCE_SEMANTICS_MODEL_EGRESS_POLICY_FILE_DIGEST",
    "BOUNDED_JAVA_SOURCE_SEMANTICS_MODEL_EGRESS_POLICY_PATH",
    "BOUNDED_JAVA_SOURCE_SEMANTICS_QUALIFICATION_CASE_CALLS",
    "BOUNDED_JAVA_SOURCE_SEMANTICS_QUALIFICATION_RESOURCE_POLICY_REF",
    "BoundedJavaSourceSemanticsGatewayQualificationBinding",
    "load_bounded_java_source_semantics_gateway_qualification_binding",
]
