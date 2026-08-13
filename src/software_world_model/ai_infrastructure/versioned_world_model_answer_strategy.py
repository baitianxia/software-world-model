"""Profile-versioned WORLD_MODEL proposal strategies.

The ITER-003 Maven strategy module is an exact qualified artifact whose file
digest must remain immutable.  This module preserves that legacy contract as
the default and owns all later profile-specific proposal contracts.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Mapping

from software_world_model.cross_cutting import Digest, DomainError, ErrorCode, digest_of

from .model_gateway import (
    AuthorizedInputItem,
    AuthorizedInputManifest,
    InputDisposition,
    ModelExecutionContext,
    PlatformProposalMode,
    RuntimeAccessMode,
)
from .world_model_answer_strategy import (
    GENERIC_QUERY_PLANNING,
    WORLD_MODEL_ANSWER_PROMPT_REF,
    WORLD_MODEL_ANSWER_STRATEGY_ID,
    WORLD_MODEL_ANSWER_STRATEGY_VERSION,
    WORLD_MODEL_ANSWER_TOOL_POLICY_REF,
    WORLD_MODEL_PROPOSAL_CAPABILITY_CONTRACT_VERSION,
    WORLD_MODEL_PROPOSAL_CAPABILITY_ID,
    WorldModelCapabilityProposal,
    WorldModelGatewayPort,
    WorldModelStrategyConfiguration,
    _SCHEMA_REF_BY_CAPABILITY,
    _WORLD_MODEL_PROMPT,
    _decode_closed_output,
    world_model_answer_output_contract_digest,
    world_model_answer_output_schemas,
    world_model_answer_prompt_program_digest as _legacy_prompt_program_digest,
    world_model_answer_strategy_implementation_digest as _legacy_strategy_digest,
)


WORLD_MODEL_PROPOSAL_VOCABULARY_REF = (
    "world-model-authority-proposal-vocabulary@1"
)
JAVA_WORLD_MODEL_PROPOSAL_CAPABILITY_CONTRACT_VERSION = "1.1.0"
JAVA_WORLD_MODEL_ANSWER_STRATEGY_VERSION = "1.1.0"
JAVA_WORLD_MODEL_ANSWER_PROMPT_REF = (
    "snapshot-first-world-model-proposal-prompt@4"
)
JAVA_WORLD_MODEL_PROPOSAL_VOCABULARY_REF = (
    "world-model-authority-proposal-vocabulary@2"
)


_JAVA_WORLD_MODEL_PROMPT = _WORLD_MODEL_PROMPT.replace(
    "GENERIC_QUERY_PLANNING: use only available_operations. Preserve the supplied needs order. inventory_left/right maps to inventory on the matching read_set snapshot. paths_left/right maps to all_simple_paths on that snapshot with the exact typed source_entity_ref and target_entity_ref. new_paths maps to ordered_snapshot_diff with read_set[0] as base and read_set[1] as target. Do not select a candidate, invent an operation, access Source, or branch on a project name.",
    "GENERIC_QUERY_PLANNING: use only available_operations and preserve the supplied needs order. inventory_left/right maps to inventory on the matching read_set snapshot. method_inventory_left/right maps to declared_method_inventory on the matching read_set snapshot. paths_left/right maps to all_simple_paths on that snapshot with the exact typed source_entity_ref and target_entity_ref. new_paths maps to ordered_snapshot_diff with read_set[0] as base and read_set[1] as target. Do not substitute inventory for declared_method_inventory, select a candidate, invent an operation, access Source, or branch on a project name.",
)


@dataclass(frozen=True, slots=True)
class WorldModelProposalContract:
    """Exact proposal identity and generic operation vocabulary for one profile."""

    capability_contract_version: str
    strategy_version: str
    prompt_ref: str
    prompt: str
    proposal_vocabulary_ref: str
    available_operations: tuple[str, ...]

    def __post_init__(self) -> None:
        for value, label in (
            (self.capability_contract_version, "capability contract version"),
            (self.strategy_version, "strategy version"),
            (self.prompt_ref, "prompt reference"),
            (self.prompt, "prompt"),
            (self.proposal_vocabulary_ref, "proposal vocabulary reference"),
        ):
            if not isinstance(value, str) or not value or value != value.strip():
                raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} is invalid")
        if (
            not self.available_operations
            or any(
                not isinstance(item, str) or not item or item != item.strip()
                for item in self.available_operations
            )
            or len(set(self.available_operations)) != len(self.available_operations)
        ):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "proposal contract operations must be unique non-empty strings",
            )

    @property
    def strategy_ref(self) -> str:
        return f"{WORLD_MODEL_ANSWER_STRATEGY_ID}@{self.strategy_version}"


MAVEN_WORLD_MODEL_PROPOSAL_CONTRACT = WorldModelProposalContract(
    capability_contract_version=WORLD_MODEL_PROPOSAL_CAPABILITY_CONTRACT_VERSION,
    strategy_version=WORLD_MODEL_ANSWER_STRATEGY_VERSION,
    prompt_ref=WORLD_MODEL_ANSWER_PROMPT_REF,
    prompt=_WORLD_MODEL_PROMPT,
    proposal_vocabulary_ref=WORLD_MODEL_PROPOSAL_VOCABULARY_REF,
    available_operations=(
        "inventory",
        "all_simple_paths",
        "ordered_snapshot_diff",
    ),
)


JAVA_WORLD_MODEL_PROPOSAL_CONTRACT = WorldModelProposalContract(
    capability_contract_version=(
        JAVA_WORLD_MODEL_PROPOSAL_CAPABILITY_CONTRACT_VERSION
    ),
    strategy_version=JAVA_WORLD_MODEL_ANSWER_STRATEGY_VERSION,
    prompt_ref=JAVA_WORLD_MODEL_ANSWER_PROMPT_REF,
    prompt=_JAVA_WORLD_MODEL_PROMPT,
    proposal_vocabulary_ref=JAVA_WORLD_MODEL_PROPOSAL_VOCABULARY_REF,
    available_operations=(
        "inventory",
        "declared_method_inventory",
        "all_simple_paths",
        "ordered_snapshot_diff",
    ),
)


class WorldModelCapabilityStrategy:
    """Invoke one closed proposal under an exact profile-versioned contract."""

    def __init__(
        self,
        gateway: WorldModelGatewayPort,
        configuration: WorldModelStrategyConfiguration,
        *,
        proposal_contract: WorldModelProposalContract = (
            MAVEN_WORLD_MODEL_PROPOSAL_CONTRACT
        ),
    ) -> None:
        self._gateway = gateway
        self._configuration = configuration
        self._proposal_contract = proposal_contract

    @property
    def proposal_contract(self) -> WorldModelProposalContract:
        return self._proposal_contract

    @property
    def strategy_ref(self) -> str:
        return self._proposal_contract.strategy_ref

    def for_proposal_contract(
        self, proposal_contract: WorldModelProposalContract
    ) -> "WorldModelCapabilityStrategy":
        return WorldModelCapabilityStrategy(
            self._gateway,
            self._configuration,
            proposal_contract=proposal_contract,
        )

    def propose(
        self,
        *,
        case_id: str,
        capability: str,
        sealed_input: object,
        available_operations: tuple[str, ...] = (),
    ) -> WorldModelCapabilityProposal:
        _text(case_id, "case ID")
        if capability not in _SCHEMA_REF_BY_CAPABILITY:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "world-model proposal capability is not registered",
            )
        if any(
            not isinstance(item, str) or not item or item != item.strip()
            for item in available_operations
        ) or len(set(available_operations)) != len(available_operations):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "available operations must be unique non-empty strings",
            )
        if capability == GENERIC_QUERY_PLANNING:
            if available_operations != self._proposal_contract.available_operations:
                raise DomainError(
                    ErrorCode.QUALIFICATION_INVALID,
                    "generic proposal operations are outside the versioned contract",
                )
        elif available_operations:
            raise DomainError(
                ErrorCode.QUALIFICATION_INVALID,
                "non-planning proposal cannot declare generic operations",
            )
        state: dict[str, object] = {
            "case_id": case_id,
            "capability": capability,
            "input": sealed_input,
        }
        if available_operations:
            state["available_operations"] = list(available_operations)
        try:
            state_text = json.dumps(
                state,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            )
        except (TypeError, ValueError) as exc:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "sealed world-model proposal input is not canonical JSON",
            ) from exc
        schema_ref = _SCHEMA_REF_BY_CAPABILITY[capability]
        execution_ref = f"world-model-capability:{case_id}"
        contract = self._proposal_contract
        manifest = AuthorizedInputManifest.create(
            capability_id=WORLD_MODEL_PROPOSAL_CAPABILITY_ID,
            strategy_ref=contract.strategy_ref,
            execution_stage=capability,
            calling_module="ai-infrastructure/world-model-capability-evaluation",
            proposal_vocabulary_ref=contract.proposal_vocabulary_ref,
            items=(
                AuthorizedInputItem.create(
                    item_id="instruction",
                    schema_ref="text@1",
                    classification=self._configuration.classification,
                    purpose="world-model authority proposal rules",
                    authority_reference=contract.prompt_ref,
                    disposition=InputDisposition.PROVIDED,
                    content=contract.prompt,
                ),
                AuthorizedInputItem.create(
                    item_id="sealed-case-input",
                    schema_ref="world-model-capability-case-input@1",
                    classification=self._configuration.classification,
                    purpose="closed capability case input without evaluator oracle",
                    authority_reference=case_id,
                    disposition=InputDisposition.PROVIDED,
                    content=state_text,
                ),
                AuthorizedInputItem.create(
                    item_id="qualification",
                    schema_ref="qualification-ref@1",
                    classification=self._configuration.classification,
                    purpose="bind adapter conformance during capability evaluation",
                    authority_reference=self._configuration.qualification_ref,
                    disposition=InputDisposition.PROVIDED,
                    content=self._configuration.qualification_ref,
                ),
            ),
        )
        gateway_result = self._gateway.invoke(
            ModelExecutionContext(
                execution_envelope_ref=execution_ref,
                manifest=manifest,
                prompt_program_ref=contract.prompt_ref,
                rendering_contract_version="manifest-messages@1",
                output_schema_ref=schema_ref,
                runtime_access_mode=RuntimeAccessMode.NO_EXTERNAL_ACCESS,
                platform_proposal_mode=PlatformProposalMode.NONE,
                requested_model_ref=self._configuration.model_ref,
                provider_type=self._configuration.provider_type,
                adapter_version=self._configuration.adapter_version,
                provider_configuration_fingerprint=(
                    self._configuration.provider_configuration_fingerprint
                ),
                max_output_tokens=self._configuration.max_output_tokens,
                timeout_milliseconds=self._configuration.timeout_milliseconds,
                classification=self._configuration.classification,
                required_exact_fingerprint=True,
            )
        )
        if (
            not gateway_result.eligibility.eligible_for_production_domain_output
            or gateway_result.response is None
        ):
            raise DomainError(
                ErrorCode.CONTROL_STATE_DENIED,
                "world-model capability proposal is not eligible for evaluation",
                {
                    "eligibility_reason": gateway_result.eligibility.reason,
                    "model_failure_code": gateway_result.call.failure_code or "NONE",
                },
            )
        normalized = _decode_closed_output(
            gateway_result.response.output_text,
            world_model_answer_output_schemas()[schema_ref],
        )
        core = {
            "case_id": case_id,
            "capability": capability,
            "normalized_result": normalized,
            "manifest_digest": manifest.digest.value,
            "model_call_id": gateway_result.call.model_call_id.value,
            "model_output_digest": gateway_result.response.output_digest.value,
        }
        return WorldModelCapabilityProposal(
            case_id=case_id,
            capability=capability,
            normalized_result=normalized,
            gateway_result=gateway_result,
            digest=digest_of(core),
        )


def world_model_answer_prompt_program_digest(
    proposal_contract: WorldModelProposalContract = MAVEN_WORLD_MODEL_PROPOSAL_CONTRACT,
) -> Digest:
    if proposal_contract == MAVEN_WORLD_MODEL_PROPOSAL_CONTRACT:
        return _legacy_prompt_program_digest()
    return digest_of(((proposal_contract.prompt_ref, proposal_contract.prompt),))


def world_model_answer_strategy_implementation_digest(
    proposal_contract: WorldModelProposalContract = MAVEN_WORLD_MODEL_PROPOSAL_CONTRACT,
) -> Digest:
    if proposal_contract == MAVEN_WORLD_MODEL_PROPOSAL_CONTRACT:
        return _legacy_strategy_digest()
    return digest_of(
        {
            "capability_id": WORLD_MODEL_PROPOSAL_CAPABILITY_ID,
            "capability_contract_version": (
                proposal_contract.capability_contract_version
            ),
            "strategy_id": WORLD_MODEL_ANSWER_STRATEGY_ID,
            "strategy_version": proposal_contract.strategy_version,
            "prompt_program_digest": world_model_answer_prompt_program_digest(
                proposal_contract
            ).value,
            "output_contract_digest": (
                world_model_answer_output_contract_digest().value
            ),
            "tool_policy_ref": WORLD_MODEL_ANSWER_TOOL_POLICY_REF,
            "manifest_items": (
                "instruction",
                "sealed-case-input",
                "qualification",
            ),
            "oracle_visibility": "FORBIDDEN",
            "source_visibility": "FORBIDDEN",
            "model_call_policy": "ONE_CALL_PER_CLOSED_CASE_NO_RETRY@1",
            "runtime_access_mode": RuntimeAccessMode.NO_EXTERNAL_ACCESS.value,
            "platform_proposal_mode": PlatformProposalMode.NONE.value,
            "proposal_vocabulary_ref": proposal_contract.proposal_vocabulary_ref,
            "available_operations": proposal_contract.available_operations,
        }
    )


def _text(value: str, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} must be non-empty")
    return value


__all__ = [
    "JAVA_WORLD_MODEL_ANSWER_PROMPT_REF",
    "JAVA_WORLD_MODEL_ANSWER_STRATEGY_VERSION",
    "JAVA_WORLD_MODEL_PROPOSAL_CAPABILITY_CONTRACT_VERSION",
    "JAVA_WORLD_MODEL_PROPOSAL_CONTRACT",
    "JAVA_WORLD_MODEL_PROPOSAL_VOCABULARY_REF",
    "MAVEN_WORLD_MODEL_PROPOSAL_CONTRACT",
    "WORLD_MODEL_PROPOSAL_VOCABULARY_REF",
    "WorldModelCapabilityStrategy",
    "WorldModelProposalContract",
    "world_model_answer_output_contract_digest",
    "world_model_answer_output_schemas",
    "world_model_answer_prompt_program_digest",
    "world_model_answer_strategy_implementation_digest",
]
