"""Load a new Java proposal qualification for the exact product gateway policy."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Mapping

from software_world_model.application_services import QualificationProof
from software_world_model.cross_cutting import Digest, DomainError, ErrorCode, digest_of

from .model_egress_gateway import QualifiedJavaModelEgressGatewayPolicy
from .volcengine_ark_chat_adapter import VolcengineArkModelConfiguration
from .world_model_answer_strategy import world_model_answer_output_contract_digest
from .versioned_world_model_answer_strategy import (
    JAVA_WORLD_MODEL_PROPOSAL_CONTRACT,
    world_model_answer_prompt_program_digest,
    world_model_answer_strategy_implementation_digest,
)
from .world_model_capability_evaluation import (
    JAVA_WORLD_MODEL_EVALUATION_METRIC_CONTRACT,
    JAVA_WORLD_MODEL_EVALUATION_THRESHOLD_REF,
)


JAVA_CAPABILITY_CLOSED_RESULT_SCHEMA = (
    "swm.iter-006.java-world-model-ce-closed-result@1"
)
JAVA_CAPABILITY_QUALIFICATION_DOCUMENT_SCHEMA = (
    "swm.capability-qualification-proof@1"
)
JAVA_CAPABILITY_SUITE_DIGEST = (
    "sha256:93be2f872fe8531d09ca220b67aa493d8f929cbca1b27309b2d05775684d6716"
)
JAVA_CAPABILITY_ORACLE_DIGEST = (
    "sha256:0d563879c5bf53606082d669b9f5650c7a07c7fb2f59d96d741c7a0cf84facb7"
)
JAVA_MODEL_EGRESS_POLICY_PATH = Path(__file__).resolve().with_name(
    "java_model_egress_policy.json"
)
JAVA_MODEL_EGRESS_POLICY_FILE_DIGEST = (
    "sha256:63729ded35116ea47ee7fbe1c653b6a48e023e6307ffbace5e58c3fa778a7455"
)


@dataclass(frozen=True, slots=True)
class JavaGatewayQualificationBinding:
    capability_qualification_ref: str
    capability_qualification_digest: Digest
    qualification_document_digest: Digest
    closed_capability_result_digest: Digest
    qualification_valid_until: datetime

    def create_policy(
        self,
        *,
        configuration: VolcengineArkModelConfiguration,
        conformance_result_ref: str,
    ) -> QualifiedJavaModelEgressGatewayPolicy:
        return QualifiedJavaModelEgressGatewayPolicy(
            policy_ref="ITER-006-JAVA-MODEL-EGRESS-GATEWAY@1.0.0",
            policy_digest=Digest(JAVA_MODEL_EGRESS_POLICY_FILE_DIGEST),
            provider_type=configuration.provider_type,
            adapter_version=configuration.adapter_version,
            model_ref=configuration.model_ref,
            provider_configuration_fingerprint=configuration.fingerprint,
            endpoint=(
                "https://ark.cn-beijing.volces.com:443/"
                "api/coding/v3/chat/completions"
            ),
            credential_reference=configuration.secret_reference,
            conformance_result_ref=conformance_result_ref,
            capability_qualification_ref=self.capability_qualification_ref,
            capability_qualification_digest=self.capability_qualification_digest,
            closed_capability_result_digest=self.closed_capability_result_digest,
            qualification_valid_until=self.qualification_valid_until,
        )


def load_java_gateway_qualification_binding(
    *,
    qualification_path: str | Path,
    closed_result_path: str | Path,
    policy_path: str | Path = JAVA_MODEL_EGRESS_POLICY_PATH,
    now: datetime | None = None,
) -> JavaGatewayQualificationBinding:
    policy_raw = Path(policy_path).resolve(strict=True).read_bytes()
    if (
        "sha256:" + hashlib.sha256(policy_raw).hexdigest()
        != JAVA_MODEL_EGRESS_POLICY_FILE_DIGEST
    ):
        _invalid("Java egress policy file digest drifted")
    _verify_policy(_unique_json(policy_raw, "Java egress policy"))
    qualification_document = _unique_json(
        Path(qualification_path).resolve(strict=True).read_bytes(),
        "Java capability qualification",
    )
    proof = _qualification_proof(qualification_document)
    closed = _unique_json(
        Path(closed_result_path).resolve(strict=True).read_bytes(),
        "Java closed capability result",
    )
    closed_core = {
        key: value for key, value in closed.items() if key != "document_digest"
    }
    if (
        closed.get("schema") != JAVA_CAPABILITY_CLOSED_RESULT_SCHEMA
        or closed.get("document_digest") != digest_of(closed_core).value
        or closed.get("closed_result_status") != "PASS_VALID"
        or closed.get("failure_count") != 0
        or closed.get("unknown_count") != 0
        or closed.get("required_case_count") != 8
        or closed.get("provider_request_count") != 8
        or closed.get("production_activation") != "NOT_EXECUTED"
        or closed.get("suite_digest") != JAVA_CAPABILITY_SUITE_DIGEST
        or closed.get("oracle_digest") != JAVA_CAPABILITY_ORACLE_DIGEST
    ):
        _invalid("Java closed capability result is not PASS_VALID")
    definition = closed.get("definition")
    result = closed.get("result")
    validity = closed.get("validity")
    qualification = closed.get("qualification")
    if not all(
        isinstance(item, Mapping)
        for item in (definition, result, validity, qualification)
    ):
        _invalid("Java closed capability authority chain is incomplete")
    assert isinstance(definition, Mapping)
    assert isinstance(result, Mapping)
    assert isinstance(validity, Mapping)
    assert isinstance(qualification, Mapping)
    if (
        definition.get("capability_id") != "world-model-authority-proposal"
        or definition.get("capability_contract_version")
        != JAVA_WORLD_MODEL_PROPOSAL_CONTRACT.capability_contract_version
        or definition.get("strategy_id")
        != "model-snapshot-first-world-model-answer"
        or definition.get("strategy_version")
        != JAVA_WORLD_MODEL_PROPOSAL_CONTRACT.strategy_version
        or definition.get("implementation_digest")
        != world_model_answer_strategy_implementation_digest(
            JAVA_WORLD_MODEL_PROPOSAL_CONTRACT
        ).value
        or definition.get("prompt_program_digest")
        != world_model_answer_prompt_program_digest(
            JAVA_WORLD_MODEL_PROPOSAL_CONTRACT
        ).value
        or definition.get("output_schema_digest")
        != world_model_answer_output_contract_digest().value
        or definition.get("metric_contract_digest")
        != digest_of(JAVA_WORLD_MODEL_EVALUATION_METRIC_CONTRACT).value
        or definition.get("threshold_ref")
        != JAVA_WORLD_MODEL_EVALUATION_THRESHOLD_REF
        or not isinstance(definition.get("cases"), list)
        or len(definition["cases"]) != 8
        or result.get("conclusion") != "PASS"
        or len(result.get("passed_case_ids", [])) != 8
        or result.get("failed_case_ids") != []
        or result.get("inconclusive_case_ids") != []
        or validity.get("status") != "VALID"
        or qualification.get("proof_ref") != proof.proof_ref
        or qualification.get("digest") != proof.digest.value
        or qualification.get("result_ref") != proof.result_ref
        or qualification.get("validity_ref") != proof.validity_ref
    ):
        _invalid("Java capability Result does not bind the exact proposal contract")
    if (
        proof.capability_id != "world-model-authority-proposal"
        or proof.capability_contract_version
        != JAVA_WORLD_MODEL_PROPOSAL_CONTRACT.capability_contract_version
        or proof.strategy_id != "model-snapshot-first-world-model-answer"
        or proof.strategy_version
        != JAVA_WORLD_MODEL_PROPOSAL_CONTRACT.strategy_version
        or proof.qualification_kind != "CAPABILITY_EVALUATION"
        or proof.result_ref != result.get("result_id")
    ):
        _invalid("Java capability qualification proof is outside the exact contract")
    try:
        valid_until = datetime.fromisoformat(
            str(validity["valid_until"]).replace("Z", "+00:00")
        )
    except (KeyError, ValueError) as exc:
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "Java capability validity expiration is invalid",
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
        _invalid("Java capability qualification is expired")
    return JavaGatewayQualificationBinding(
        capability_qualification_ref=proof.proof_ref,
        capability_qualification_digest=proof.digest,
        qualification_document_digest=Digest(
            str(qualification_document["document_digest"])
        ),
        closed_capability_result_digest=Digest(str(closed["document_digest"])),
        qualification_valid_until=valid_until,
    )


def _qualification_proof(document: Mapping[str, object]) -> QualificationProof:
    raw = document.get("proof")
    if (
        set(document) != {"schema", "proof", "document_digest"}
        or document.get("schema")
        != JAVA_CAPABILITY_QUALIFICATION_DOCUMENT_SCHEMA
        or not isinstance(raw, Mapping)
    ):
        _invalid("Java capability qualification document is invalid")
    core = {"schema": document["schema"], "proof": raw}
    if document.get("document_digest") != digest_of(core).value:
        _invalid("Java capability qualification document digest is invalid")
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
    if set(raw) != required or any(not isinstance(raw[key], str) for key in required):
        _invalid("Java capability qualification fields are invalid")
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
        _invalid("Java capability qualification proof digest is invalid")
    return proof


def _verify_policy(policy: Mapping[str, object]) -> None:
    contract = policy.get("proposal_contract")
    requirements = policy.get("qualification_requirements")
    if (
        policy.get("schema")
        != "swm.iter-006.java-model-egress-gateway-policy@1"
        or policy.get("policy_ref")
        != "ITER-006-JAVA-MODEL-EGRESS-GATEWAY@1.0.0"
        or policy.get("default_action") != "DENY"
        or policy.get("environment") != "EVALUATION_ONLY"
        or policy.get("production_activation") != "NOT_EXECUTED"
        or not isinstance(contract, Mapping)
        or contract.get("capability_contract_version") != "1.1.0"
        or contract.get("strategy_ref")
        != JAVA_WORLD_MODEL_PROPOSAL_CONTRACT.strategy_ref
        or contract.get("prompt_ref")
        != JAVA_WORLD_MODEL_PROPOSAL_CONTRACT.prompt_ref
        or contract.get("proposal_vocabulary_ref")
        != JAVA_WORLD_MODEL_PROPOSAL_CONTRACT.proposal_vocabulary_ref
        or contract.get("available_operations")
        != list(JAVA_WORLD_MODEL_PROPOSAL_CONTRACT.available_operations)
        or not isinstance(requirements, Mapping)
        or requirements.get("closed_result_status") != "PASS_VALID"
        or requirements.get("required_case_count") != 8
        or requirements.get("failure_count") != 0
        or requirements.get("unknown_count") != 0
    ):
        _invalid("Java egress policy content drifted")


def _unique_json(raw: bytes, label: str) -> dict[str, object]:
    try:
        value = json.loads(raw, object_pairs_hook=_unique_object)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID, f"{label} cannot be loaded"
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
    "JAVA_CAPABILITY_CLOSED_RESULT_SCHEMA",
    "JAVA_CAPABILITY_ORACLE_DIGEST",
    "JAVA_CAPABILITY_QUALIFICATION_DOCUMENT_SCHEMA",
    "JAVA_CAPABILITY_SUITE_DIGEST",
    "JAVA_MODEL_EGRESS_POLICY_FILE_DIGEST",
    "JAVA_MODEL_EGRESS_POLICY_PATH",
    "JavaGatewayQualificationBinding",
    "load_java_gateway_qualification_binding",
]
