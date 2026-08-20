"""Exact AF_UNIX transport for the evaluation-only Model Egress Gateway.

The answer worker owns no Provider adapter, credential, DNS, or INET socket.
It sends one closed ``ModelExecutionContext`` to this client, while a distinct
gateway process validates and executes that context through ``ModelGateway``.
Only sanitized model-call authority records and the untrusted model output are
returned to the answer worker.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
import socket
import stat
import struct
from typing import Callable, Mapping, Protocol

from software_world_model.cross_cutting import (
    Digest,
    DomainError,
    ErrorCode,
    Revision,
    StableId,
    canonical_json_bytes,
    digest_of,
)
from software_world_model.application_services.bounded_world_model_investigation import (
    constrained_investigation_operations,
)

from .model_gateway import (
    AdapterResponse,
    AuthorizedInputItem,
    AuthorizedInputManifest,
    InputDisposition,
    IsolationReceipt,
    ModelCallRecord,
    ModelCallState,
    ModelExecutionContext,
    ModelGatewayResult,
    ModelResultEligibility,
    PlatformProposalMode,
    ReplayClassification,
    RuntimeAccessMode,
)


MODEL_EGRESS_GATEWAY_POLICY_REF = "ITER-003-MODEL-EGRESS-GATEWAY@1.0.0"
MODEL_EGRESS_GATEWAY_ROUTE = f"AF_UNIX:{MODEL_EGRESS_GATEWAY_POLICY_REF}"
JAVA_MODEL_EGRESS_GATEWAY_POLICY_REF = (
    "ITER-006-JAVA-MODEL-EGRESS-GATEWAY@1.0.0"
)
JAVA_MODEL_EGRESS_GATEWAY_ROUTE = (
    f"AF_UNIX:{JAVA_MODEL_EGRESS_GATEWAY_POLICY_REF}"
)
JAVA_SOURCE_SEMANTICS_MODEL_EGRESS_GATEWAY_POLICY_REF = (
    "ITER-007-JAVA-SOURCE-SEMANTICS-MODEL-EGRESS-GATEWAY@1.0.2"
)
JAVA_SOURCE_SEMANTICS_MODEL_EGRESS_GATEWAY_ROUTE = (
    f"AF_UNIX:{JAVA_SOURCE_SEMANTICS_MODEL_EGRESS_GATEWAY_POLICY_REF}"
)
BOUNDED_JAVA_SOURCE_SEMANTICS_MODEL_EGRESS_GATEWAY_POLICY_REF = (
    "ITER-008-BOUNDED-JAVA-SOURCE-SEMANTICS-MODEL-EGRESS-GATEWAY@1.4.6"
)
BOUNDED_JAVA_SOURCE_SEMANTICS_MODEL_EGRESS_GATEWAY_ROUTE = (
    f"AF_UNIX:{BOUNDED_JAVA_SOURCE_SEMANTICS_MODEL_EGRESS_GATEWAY_POLICY_REF}"
)
MODEL_EGRESS_REQUEST_SCHEMA = "swm.model-egress-request@1"
MODEL_EGRESS_RESPONSE_SCHEMA = "swm.model-egress-response@1"

_HEADER = struct.Struct("!I")
_MAX_FRAME_BYTES = 16 * 1024 * 1024
_MAX_PROVIDER_CALLS = 5
_EXACT_POLICY_DIGEST = Digest(
    "sha256:3e0bfcbf6f1b85d350db167d1bc71ff55f35a76546f15d4d7f14a871aa0326e0"
)
_EXACT_PROVIDER_TYPE = "VOLCENGINE_ARK"
_EXACT_ADAPTER_VERSION = "openai-chat-completions-no-tools@8"
_EXACT_MODEL_REF = "glm-5-2-260617"
_EXACT_PROVIDER_FINGERPRINT = Digest(
    "sha256:420f553a3ce0075818550e08cb1351ce69eaf9871c5a0257aecf88b7b32b88fd"
)
_EXACT_ENDPOINT = (
    "https://ark.cn-beijing.volces.com:443/api/coding/v3/chat/completions"
)
_EXACT_CREDENTIAL_REFERENCE = "env:ARK_API_KEY"
_EXACT_CONFORMANCE_RESULT_REF = (
    "CC-ARK-CHAT-NO-TOOLS-001:"
    "sha256:c86aad995802b8dcf687fafcbaf36bccb02768ba55b40151ec9aa4704518cade"
)
_EXACT_CAPABILITY_QUALIFICATION_REF = (
    "capability-evaluation:evaluation_result_916b9000db544e92921ec1bdc02a3bc2"
)
_EXACT_CAPABILITY_QUALIFICATION_DIGEST = Digest(
    "sha256:005b1bf43c76a64d123b0184cdac1a9e844331896e7ede6279875881d9bcc62c"
)
_EXACT_STRATEGY_REF = "model-snapshot-first-world-model-answer@1.0.2"
_EXACT_PROMPT_REF = "snapshot-first-world-model-proposal-prompt@3"
_EXACT_PROMPT_CONTENT_DIGEST = Digest(
    "sha256:04b61b9e63e4dc4ed94fb1374f2121b9551d16d40e9dcc2e4990cca56a259cdf"
)
_EXACT_CALLING_MODULE = "ai-infrastructure/world-model-capability-evaluation"
_EXACT_VOCABULARY_REF = "world-model-authority-proposal-vocabulary@1"
_EXACT_SCHEMA_BY_STAGE = {
    "REQUIREMENT_FIDELITY": "world-model-requirement-fidelity@1",
    "GENERIC_QUERY_PLANNING": "world-model-generic-query-plan@1",
    "COMPLETE_NEGATIVE_ANSWER": "world-model-complete-negative@1",
    "VIEW_LIMITATION_AND_KNOWLEDGE_GAP": "world-model-limitation-gap@1",
    "ORDERED_DIFF_EXPRESSION": "world-model-ordered-diff@1",
    "INDEPENDENT_ANSWER_REVIEW": "world-model-independent-review@1",
    "ENTITY_CANDIDATE_RESOLUTION": "world-model-entity-resolution@1",
    "IMPLEMENTATION_QUERY_PLANNING": "java-implementation-query-plan@1",
    "IMPLEMENTATION_INVESTIGATION": (
        "java-bounded-implementation-investigation-intent@2"
    ),
    "IMPLEMENTATION_ANSWER_DRAFTING": "java-implementation-answer-draft@1",
    "IMPLEMENTATION_ANSWER_REVIEW": "java-implementation-answer-review@2",
}
_JAVA_EXACT_POLICY_DIGEST = Digest(
    "sha256:63729ded35116ea47ee7fbe1c653b6a48e023e6307ffbace5e58c3fa778a7455"
)
_JAVA_SOURCE_SEMANTICS_EXACT_POLICY_DIGEST = Digest(
    "sha256:9e4e3dcbb0584b2574bfa71c5e31275e5496255e0ce41cdc5fc8f05e18e243b5"
)
_BOUNDED_JAVA_SOURCE_SEMANTICS_EXACT_POLICY_DIGEST = Digest(
    "sha256:889afd1845f573ee0a9565d3fd2f6e69b6c824b72c20138c12cde93da7c407d0"
)
_DEEPSEEK_PROVIDER_TYPE = "DEEPSEEK"
_DEEPSEEK_ADAPTER_VERSION = "deepseek-chat-completions-no-tools@5"
_DEEPSEEK_MODEL_REF = "deepseek-v4-pro"
_DEEPSEEK_ACTUAL_MODEL_FINGERPRINT = "deepseek-v4-pro"
_DEEPSEEK_PROVIDER_FINGERPRINT = Digest(
    "sha256:31dc8d9bd143ab4c5aee94a5e9cdafdbd19103a645ad40e30893348ab3c2640d"
)
_DEEPSEEK_ENDPOINT = "https://api.deepseek.com/chat/completions"
_DEEPSEEK_CREDENTIAL_REFERENCE = "env:DEEPSEEK_API_KEY"
_DEEPSEEK_CONFORMANCE_RESULT_PREFIX = (
    "CC-DEEPSEEK-CHAT-NO-TOOLS-001:sha256:"
)
_FORBIDDEN_MODEL_INPUT_KEYS = {
    "expected",
    "expected_result",
    "oracle",
    "oracle_assertions",
    "oracle_ref",
    "oracle_sha256",
    "forbidden_events",
    "baseline_result",
    "source_payload",
    "evidence_payload",
}


class ModelGatewayPort(Protocol):
    def invoke(self, context: ModelExecutionContext) -> ModelGatewayResult: ...


@dataclass(frozen=True, slots=True)
class ModelEgressGatewayPolicy:
    policy_ref: str
    policy_digest: Digest
    provider_type: str
    adapter_version: str
    model_ref: str
    provider_configuration_fingerprint: Digest
    endpoint: str
    credential_reference: str
    conformance_result_ref: str
    capability_qualification_ref: str
    capability_qualification_digest: Digest
    max_provider_calls: int = _MAX_PROVIDER_CALLS

    def __post_init__(self) -> None:
        for value, label in (
            (self.policy_ref, "policy reference"),
            (self.provider_type, "provider type"),
            (self.adapter_version, "adapter version"),
            (self.model_ref, "model reference"),
            (self.endpoint, "provider endpoint"),
            (self.credential_reference, "credential reference"),
            (self.conformance_result_ref, "conformance result reference"),
            (self.capability_qualification_ref, "capability qualification reference"),
        ):
            _text(value, label)
        if (
            self.policy_ref != MODEL_EGRESS_GATEWAY_POLICY_REF
            or self.policy_digest != _EXACT_POLICY_DIGEST
            or self.provider_type != _EXACT_PROVIDER_TYPE
            or self.adapter_version != _EXACT_ADAPTER_VERSION
            or self.model_ref != _EXACT_MODEL_REF
            or self.provider_configuration_fingerprint
            != _EXACT_PROVIDER_FINGERPRINT
            or self.endpoint != _EXACT_ENDPOINT
            or self.credential_reference != _EXACT_CREDENTIAL_REFERENCE
            or self.conformance_result_ref != _EXACT_CONFORMANCE_RESULT_REF
            or self.capability_qualification_ref
            != _EXACT_CAPABILITY_QUALIFICATION_REF
            or self.capability_qualification_digest
            != _EXACT_CAPABILITY_QUALIFICATION_DIGEST
        ):
            raise DomainError(
                ErrorCode.QUALIFICATION_INVALID,
                "Model Egress Gateway policy binding is not exact",
            )
        if (
            type(self.max_provider_calls) is not int
            or self.max_provider_calls != _MAX_PROVIDER_CALLS
        ):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "Model Egress Gateway call cap must be exactly five",
            )

    def validate_context(self, context: ModelExecutionContext) -> None:
        items = context.manifest.items
        sealed_authority = items[1].authority_reference if len(items) == 3 else None
        qualification_ref = f"evaluation-only:{self.conformance_result_ref}"
        if (
            context.provider_type != self.provider_type
            or context.adapter_version != self.adapter_version
            or context.requested_model_ref != self.model_ref
            or context.provider_configuration_fingerprint
            != self.provider_configuration_fingerprint
            or context.runtime_access_mode is not RuntimeAccessMode.NO_EXTERNAL_ACCESS
            or context.platform_proposal_mode is not PlatformProposalMode.NONE
            or context.required_exact_fingerprint is not True
            or context.max_output_tokens != 1000
            or context.timeout_milliseconds != 180_000
            or context.classification != "INTERNAL"
            or context.execution_envelope_ref
            != f"world-model-capability:{sealed_authority}"
            or context.prompt_program_ref != _EXACT_PROMPT_REF
            or context.rendering_contract_version != "manifest-messages@1"
            or context.output_schema_ref
            != _EXACT_SCHEMA_BY_STAGE.get(context.manifest.execution_stage)
            or context.manifest.version != Revision(1)
            or context.manifest.capability_id
            != "world-model-authority-proposal"
            or context.manifest.strategy_ref != _EXACT_STRATEGY_REF
            or context.manifest.calling_module != _EXACT_CALLING_MODULE
            or context.manifest.proposal_vocabulary_ref
            != _EXACT_VOCABULARY_REF
            or tuple(item.item_id for item in items)
            != ("instruction", "sealed-case-input", "qualification")
        ):
            raise DomainError(
                ErrorCode.QUALIFICATION_INVALID,
                "model request is outside the exact qualified gateway policy",
            )
        instruction, sealed, qualification = items
        if (
            instruction.schema_ref != "text@1"
            or instruction.classification != "INTERNAL"
            or instruction.purpose != "world-model authority proposal rules"
            or instruction.authority_reference != _EXACT_PROMPT_REF
            or instruction.disposition is not InputDisposition.PROVIDED
            or instruction.transformation_ref != "identity@1"
            or instruction.content_digest != _EXACT_PROMPT_CONTENT_DIGEST
            or sealed.schema_ref != "world-model-capability-case-input@1"
            or sealed.classification != "INTERNAL"
            or sealed.purpose
            != "closed capability case input without evaluator oracle"
            or sealed.disposition is not InputDisposition.PROVIDED
            or sealed.transformation_ref != "identity@1"
            or not sealed.authority_reference.startswith("product:")
            or qualification.schema_ref != "qualification-ref@1"
            or qualification.classification != "INTERNAL"
            or qualification.purpose
            != "bind adapter conformance during capability evaluation"
            or qualification.authority_reference != qualification_ref
            or qualification.content != qualification_ref
            or qualification.disposition is not InputDisposition.PROVIDED
            or qualification.transformation_ref != "identity@1"
        ):
            raise DomainError(
                ErrorCode.QUALIFICATION_INVALID,
                "model input manifest is outside the qualified product shape",
            )
        sealed_value = _unique_json_object(
            sealed.content.encode("utf-8"), "sealed product model input"
        )
        expected_keys = {"case_id", "capability", "input"}
        if context.manifest.execution_stage == "GENERIC_QUERY_PLANNING":
            expected_keys.add("available_operations")
        if (
            set(sealed_value) != expected_keys
            or sealed_value.get("case_id") != sealed.authority_reference
            or sealed_value.get("capability")
            != context.manifest.execution_stage
            or _contains_forbidden_model_key(sealed_value)
            or (
                context.manifest.execution_stage == "GENERIC_QUERY_PLANNING"
                and sealed_value.get("available_operations")
                != [
                    "inventory",
                    "all_simple_paths",
                    "ordered_snapshot_diff",
                ]
            )
        ):
            raise DomainError(
                ErrorCode.QUALIFICATION_INVALID,
                "sealed product model input violates its closed contract",
            )

    def validate_result(self, result: ModelGatewayResult) -> None:
        if (
            result.call.provider_type != self.provider_type
            or result.call.adapter_version != self.adapter_version
            or result.call.requested_model_ref != self.model_ref
            or result.isolation_receipt.provider_type != self.provider_type
            or result.isolation_receipt.adapter_version != self.adapter_version
            or result.isolation_receipt.provider_configuration_fingerprint
            != self.provider_configuration_fingerprint
            or result.isolation_receipt.conformance_result_ref
            != self.conformance_result_ref
            or result.call.state is not ModelCallState.COMPLETED
            or result.call.actual_model_fingerprint != "glm-5.2"
            or result.call.failure_code is not None
            or result.response is None
            or result.response.actual_model_fingerprint != "glm-5.2"
            or result.response.usage_complete is not True
            or result.eligibility.eligible_for_production_domain_output is not True
            or result.eligibility.reason != "ELIGIBLE"
            or result.eligibility.actual_model_fingerprint != "glm-5.2"
        ):
            raise DomainError(
                ErrorCode.QUALIFICATION_INVALID,
                "model result is outside the exact qualified gateway policy",
            )


@dataclass(frozen=True, slots=True)
class QualifiedJavaModelEgressGatewayPolicy:
    """Exact Java request policy backed by a newly verified qualification."""

    policy_ref: str
    policy_digest: Digest
    provider_type: str
    adapter_version: str
    model_ref: str
    provider_configuration_fingerprint: Digest
    endpoint: str
    credential_reference: str
    conformance_result_ref: str
    capability_qualification_ref: str
    capability_qualification_digest: Digest
    closed_capability_result_digest: Digest
    qualification_valid_until: datetime
    max_provider_calls: int = _MAX_PROVIDER_CALLS

    def __post_init__(self) -> None:
        for value, label in (
            (self.policy_ref, "policy reference"),
            (self.provider_type, "provider type"),
            (self.adapter_version, "adapter version"),
            (self.model_ref, "model reference"),
            (self.endpoint, "provider endpoint"),
            (self.credential_reference, "credential reference"),
            (self.conformance_result_ref, "conformance result reference"),
            (self.capability_qualification_ref, "capability qualification reference"),
        ):
            _text(value, label)
        if (
            self.policy_ref != JAVA_MODEL_EGRESS_GATEWAY_POLICY_REF
            or self.policy_digest != _JAVA_EXACT_POLICY_DIGEST
            or self.provider_type != _EXACT_PROVIDER_TYPE
            or self.adapter_version != _EXACT_ADAPTER_VERSION
            or self.model_ref != _EXACT_MODEL_REF
            or self.provider_configuration_fingerprint
            != _EXACT_PROVIDER_FINGERPRINT
            or self.endpoint != _EXACT_ENDPOINT
            or self.credential_reference != _EXACT_CREDENTIAL_REFERENCE
            or self.conformance_result_ref != _EXACT_CONFORMANCE_RESULT_REF
            or not self.capability_qualification_ref.startswith(
                "capability-evaluation:evaluation_result_"
            )
        ):
            raise DomainError(
                ErrorCode.QUALIFICATION_INVALID,
                "Java Model Egress Gateway policy binding is not exact",
            )
        if (
            self.qualification_valid_until.tzinfo is None
            or self.qualification_valid_until.utcoffset() is None
        ):
            raise DomainError(
                ErrorCode.QUALIFICATION_INVALID,
                "Java capability qualification expiration is invalid",
            )
        if (
            type(self.max_provider_calls) is not int
            or self.max_provider_calls != _MAX_PROVIDER_CALLS
        ):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "Java Model Egress Gateway call cap must be exactly five",
            )

    def validate_context(self, context: ModelExecutionContext) -> None:
        from .versioned_world_model_answer_strategy import (
            JAVA_WORLD_MODEL_PROPOSAL_CONTRACT,
        )

        if datetime.now(timezone.utc) >= self.qualification_valid_until.astimezone(
            timezone.utc
        ):
            raise DomainError(
                ErrorCode.QUALIFICATION_INVALID,
                "Java capability qualification expired before dispatch",
            )
        contract = JAVA_WORLD_MODEL_PROPOSAL_CONTRACT
        items = context.manifest.items
        sealed_authority = items[1].authority_reference if len(items) == 3 else None
        qualification_ref = f"evaluation-only:{self.conformance_result_ref}"
        if (
            context.provider_type != self.provider_type
            or context.adapter_version != self.adapter_version
            or context.requested_model_ref != self.model_ref
            or context.provider_configuration_fingerprint
            != self.provider_configuration_fingerprint
            or context.runtime_access_mode is not RuntimeAccessMode.NO_EXTERNAL_ACCESS
            or context.platform_proposal_mode is not PlatformProposalMode.NONE
            or context.required_exact_fingerprint is not True
            or context.max_output_tokens != 1000
            or context.timeout_milliseconds != 180_000
            or context.classification != "INTERNAL"
            or context.execution_envelope_ref
            != f"world-model-capability:{sealed_authority}"
            or context.prompt_program_ref != contract.prompt_ref
            or context.rendering_contract_version != "manifest-messages@1"
            or context.output_schema_ref
            != _EXACT_SCHEMA_BY_STAGE.get(context.manifest.execution_stage)
            or context.manifest.version != Revision(1)
            or context.manifest.capability_id
            != "world-model-authority-proposal"
            or context.manifest.strategy_ref != contract.strategy_ref
            or context.manifest.calling_module != _EXACT_CALLING_MODULE
            or context.manifest.proposal_vocabulary_ref
            != contract.proposal_vocabulary_ref
            or tuple(item.item_id for item in items)
            != ("instruction", "sealed-case-input", "qualification")
        ):
            raise DomainError(
                ErrorCode.QUALIFICATION_INVALID,
                "model request is outside the exact Java qualified policy",
            )
        instruction, sealed, qualification = items
        if (
            instruction.schema_ref != "text@1"
            or instruction.classification != "INTERNAL"
            or instruction.purpose != "world-model authority proposal rules"
            or instruction.authority_reference != contract.prompt_ref
            or instruction.disposition is not InputDisposition.PROVIDED
            or instruction.transformation_ref != "identity@1"
            or instruction.content_digest != digest_of(contract.prompt)
            or sealed.schema_ref != "world-model-capability-case-input@1"
            or sealed.classification != "INTERNAL"
            or sealed.purpose
            != "closed capability case input without evaluator oracle"
            or sealed.disposition is not InputDisposition.PROVIDED
            or sealed.transformation_ref != "identity@1"
            or not sealed.authority_reference.startswith("product:")
            or qualification.schema_ref != "qualification-ref@1"
            or qualification.classification != "INTERNAL"
            or qualification.purpose
            != "bind adapter conformance during capability evaluation"
            or qualification.authority_reference != qualification_ref
            or qualification.content != qualification_ref
            or qualification.disposition is not InputDisposition.PROVIDED
            or qualification.transformation_ref != "identity@1"
        ):
            raise DomainError(
                ErrorCode.QUALIFICATION_INVALID,
                "model input manifest is outside the qualified Java product shape",
            )
        sealed_value = _unique_json_object(
            sealed.content.encode("utf-8"), "sealed Java product model input"
        )
        expected_keys = {"case_id", "capability", "input"}
        if context.manifest.execution_stage == "GENERIC_QUERY_PLANNING":
            expected_keys.add("available_operations")
        if (
            set(sealed_value) != expected_keys
            or sealed_value.get("case_id") != sealed.authority_reference
            or sealed_value.get("capability")
            != context.manifest.execution_stage
            or _contains_forbidden_model_key(sealed_value)
            or (
                context.manifest.execution_stage == "GENERIC_QUERY_PLANNING"
                and sealed_value.get("available_operations")
                != list(contract.available_operations)
            )
        ):
            raise DomainError(
                ErrorCode.QUALIFICATION_INVALID,
                "sealed Java product model input violates its closed contract",
            )

    def validate_result(self, result: ModelGatewayResult) -> None:
        if (
            result.call.provider_type != self.provider_type
            or result.call.adapter_version != self.adapter_version
            or result.call.requested_model_ref != self.model_ref
            or result.isolation_receipt.provider_type != self.provider_type
            or result.isolation_receipt.adapter_version != self.adapter_version
            or result.isolation_receipt.provider_configuration_fingerprint
            != self.provider_configuration_fingerprint
            or result.isolation_receipt.conformance_result_ref
            != self.conformance_result_ref
            or result.call.state is not ModelCallState.COMPLETED
            or result.call.actual_model_fingerprint != "glm-5.2"
            or result.call.failure_code is not None
            or result.response is None
            or result.response.actual_model_fingerprint != "glm-5.2"
            or result.response.usage_complete is not True
            or result.eligibility.eligible_for_production_domain_output is not True
            or result.eligibility.reason != "ELIGIBLE"
            or result.eligibility.actual_model_fingerprint != "glm-5.2"
        ):
            raise DomainError(
                ErrorCode.QUALIFICATION_INVALID,
                "model result is outside the exact Java qualified gateway policy",
            )


@dataclass(slots=True)
class QualifiedJavaSourceSemanticsModelEgressGatewayPolicy:
    """Exact fixed or bounded Java implementation-answer Gateway policy."""

    policy_ref: str
    policy_digest: Digest
    provider_type: str
    adapter_version: str
    model_ref: str
    provider_configuration_fingerprint: Digest
    endpoint: str
    credential_reference: str
    conformance_result_ref: str
    capability_qualification_ref: str
    capability_qualification_digest: Digest
    closed_capability_result_digest: Digest
    qualification_valid_until: datetime
    max_provider_calls: int = 3
    _validated_stages: list[str] = field(
        default_factory=list,
        init=False,
        repr=False,
    )

    def __post_init__(self) -> None:
        for value, label in (
            (self.policy_ref, "policy reference"),
            (self.provider_type, "provider type"),
            (self.adapter_version, "adapter version"),
            (self.model_ref, "model reference"),
            (self.endpoint, "provider endpoint"),
            (self.credential_reference, "credential reference"),
            (self.conformance_result_ref, "conformance result reference"),
            (self.capability_qualification_ref, "capability qualification reference"),
        ):
            _text(value, label)
        exact_policy = (
            self.policy_ref,
            self.policy_digest,
            self.max_provider_calls,
        )
        bounded = (
            self.policy_ref
            == BOUNDED_JAVA_SOURCE_SEMANTICS_MODEL_EGRESS_GATEWAY_POLICY_REF
        )
        if bounded:
            provider_binding_is_exact = (
                self.provider_type == _DEEPSEEK_PROVIDER_TYPE
                and self.adapter_version == _DEEPSEEK_ADAPTER_VERSION
                and self.model_ref == _DEEPSEEK_MODEL_REF
                and self.provider_configuration_fingerprint
                == _DEEPSEEK_PROVIDER_FINGERPRINT
                and self.endpoint == _DEEPSEEK_ENDPOINT
                and self.credential_reference
                == _DEEPSEEK_CREDENTIAL_REFERENCE
                and _deepseek_conformance_ref_is_exact(
                    self.conformance_result_ref
                )
            )
        else:
            provider_binding_is_exact = (
                self.provider_type == _EXACT_PROVIDER_TYPE
                and self.adapter_version == _EXACT_ADAPTER_VERSION
                and self.model_ref == _EXACT_MODEL_REF
                and self.provider_configuration_fingerprint
                == _EXACT_PROVIDER_FINGERPRINT
                and self.endpoint == _EXACT_ENDPOINT
                and self.credential_reference == _EXACT_CREDENTIAL_REFERENCE
                and self.conformance_result_ref
                == _EXACT_CONFORMANCE_RESULT_REF
            )
        if (
            exact_policy
            not in {
                (
                    JAVA_SOURCE_SEMANTICS_MODEL_EGRESS_GATEWAY_POLICY_REF,
                    _JAVA_SOURCE_SEMANTICS_EXACT_POLICY_DIGEST,
                    3,
                ),
                (
                    BOUNDED_JAVA_SOURCE_SEMANTICS_MODEL_EGRESS_GATEWAY_POLICY_REF,
                    _BOUNDED_JAVA_SOURCE_SEMANTICS_EXACT_POLICY_DIGEST,
                    6,
                ),
            }
            or not provider_binding_is_exact
            or not self.capability_qualification_ref.startswith(
                "capability-evaluation:evaluation_result_"
            )
        ):
            raise DomainError(
                ErrorCode.QUALIFICATION_INVALID,
                "Java source-semantics Gateway policy binding is not exact",
            )
        if (
            self.qualification_valid_until.tzinfo is None
            or self.qualification_valid_until.utcoffset() is None
        ):
            raise DomainError(
                ErrorCode.QUALIFICATION_INVALID,
                "Java source-semantics qualification expiration is invalid",
            )

    @property
    def validated_stages(self) -> tuple[str, ...]:
        return tuple(self._validated_stages)

    def validate_context(self, context: ModelExecutionContext) -> None:
        from .versioned_world_model_answer_strategy import (
            JAVA_SOURCE_SEMANTICS_FIXED_WORLD_MODEL_PROPOSAL_CONTRACT,
            JAVA_SOURCE_SEMANTICS_WORLD_MODEL_PROPOSAL_CONTRACT,
        )

        if datetime.now(timezone.utc) >= self.qualification_valid_until.astimezone(
            timezone.utc
        ):
            raise DomainError(
                ErrorCode.QUALIFICATION_INVALID,
                "Java source-semantics capability qualification expired before dispatch",
            )
        bounded = (
            self.policy_ref
            == BOUNDED_JAVA_SOURCE_SEMANTICS_MODEL_EGRESS_GATEWAY_POLICY_REF
        )
        contract = (
            JAVA_SOURCE_SEMANTICS_WORLD_MODEL_PROPOSAL_CONTRACT
            if bounded
            else JAVA_SOURCE_SEMANTICS_FIXED_WORLD_MODEL_PROPOSAL_CONTRACT
        )
        actual_stage = context.manifest.execution_stage
        if bounded:
            investigation_count = self._validated_stages.count(
                "IMPLEMENTATION_INVESTIGATION"
            )
            if not self._validated_stages:
                allowed_stages = {"IMPLEMENTATION_INVESTIGATION"}
            elif all(
                item == "IMPLEMENTATION_INVESTIGATION"
                for item in self._validated_stages
            ):
                allowed_stages = (
                    {"IMPLEMENTATION_ANSWER_DRAFTING"}
                    if investigation_count >= 4
                    else {"IMPLEMENTATION_INVESTIGATION"}
                )
                if investigation_count >= 2:
                    allowed_stages.add("IMPLEMENTATION_ANSWER_DRAFTING")
            elif self._validated_stages[-1] == "IMPLEMENTATION_ANSWER_DRAFTING":
                allowed_stages = {"IMPLEMENTATION_ANSWER_REVIEW"}
            else:
                allowed_stages = set()
            if actual_stage not in allowed_stages:
                raise DomainError(
                    ErrorCode.QUALIFICATION_INVALID,
                    "bounded Java source-semantics Gateway role sequence is invalid",
                )
            expected_stage = actual_stage
        else:
            if len(self._validated_stages) >= len(contract.capabilities):
                raise DomainError(
                    ErrorCode.QUALIFICATION_INVALID,
                    "Java source-semantics Gateway received more than three calls",
                )
            expected_stage = contract.capabilities[len(self._validated_stages)]
        items = context.manifest.items
        sealed_authority = items[1].authority_reference if len(items) == 3 else None
        qualification_ref = f"evaluation-only:{self.conformance_result_ref}"
        if (
            context.provider_type != self.provider_type
            or context.adapter_version != self.adapter_version
            or context.requested_model_ref != self.model_ref
            or context.provider_configuration_fingerprint
            != self.provider_configuration_fingerprint
            or context.runtime_access_mode is not RuntimeAccessMode.NO_EXTERNAL_ACCESS
            or context.platform_proposal_mode is not PlatformProposalMode.NONE
            or context.required_exact_fingerprint is not True
            or context.max_output_tokens != 1000
            or context.timeout_milliseconds != 180_000
            or context.classification != "INTERNAL"
            or context.execution_envelope_ref
            != f"world-model-capability:{sealed_authority}"
            or context.prompt_program_ref != contract.prompt_ref
            or context.rendering_contract_version != "manifest-messages@1"
            or context.output_schema_ref
            != _EXACT_SCHEMA_BY_STAGE.get(context.manifest.execution_stage)
            or context.manifest.version != Revision(1)
            or context.manifest.capability_id
            != "world-model-authority-proposal"
            or context.manifest.strategy_ref != contract.strategy_ref
            or context.manifest.execution_stage != expected_stage
            or context.manifest.calling_module != _EXACT_CALLING_MODULE
            or context.manifest.proposal_vocabulary_ref
            != contract.proposal_vocabulary_ref
            or tuple(item.item_id for item in items)
            != ("instruction", "sealed-case-input", "qualification")
        ):
            raise DomainError(
                ErrorCode.QUALIFICATION_INVALID,
                "model request is outside the exact Java source-semantics policy",
            )
        instruction, sealed, qualification = items
        expected_instruction = contract.prompt_for(expected_stage)
        if (
            instruction.schema_ref != "text@1"
            or instruction.classification != "INTERNAL"
            or instruction.purpose != "world-model authority proposal rules"
            or instruction.authority_reference != contract.prompt_ref
            or instruction.disposition is not InputDisposition.PROVIDED
            or instruction.transformation_ref
            != contract.instruction_transformation_ref
            or instruction.content_digest != digest_of(expected_instruction)
            or sealed.schema_ref != "world-model-capability-case-input@1"
            or sealed.classification != "INTERNAL"
            or sealed.purpose
            != "closed capability case input without evaluator oracle"
            or sealed.disposition is not InputDisposition.PROVIDED
            or sealed.transformation_ref != "identity@1"
            or not sealed.authority_reference.startswith("product:")
            or qualification.schema_ref != "qualification-ref@1"
            or qualification.classification != "INTERNAL"
            or qualification.purpose
            != "bind adapter conformance during capability evaluation"
            or qualification.authority_reference != qualification_ref
            or qualification.content != qualification_ref
            or qualification.disposition is not InputDisposition.PROVIDED
            or qualification.transformation_ref != "identity@1"
        ):
            raise DomainError(
                ErrorCode.QUALIFICATION_INVALID,
                "model input manifest is outside the Java source-semantics product shape",
            )
        sealed_value = _unique_json_object(
            sealed.content.encode("utf-8"),
            "sealed Java source-semantics product model input",
        )
        expected_keys = {"case_id", "capability", "input"}
        if expected_stage in {
            "IMPLEMENTATION_QUERY_PLANNING",
            "IMPLEMENTATION_INVESTIGATION",
        }:
            expected_keys.add("available_operations")
        if (
            set(sealed_value) != expected_keys
            or sealed_value.get("case_id") != sealed.authority_reference
            or sealed_value.get("capability") != expected_stage
            or _contains_forbidden_model_key(sealed_value)
            or (
                expected_stage == "IMPLEMENTATION_QUERY_PLANNING"
                and sealed_value.get("available_operations")
                != list(contract.available_operations)
            )
        ):
            raise DomainError(
                ErrorCode.QUALIFICATION_INVALID,
                "sealed Java source-semantics input violates its closed role contract",
            )
        if bounded and expected_stage == "IMPLEMENTATION_INVESTIGATION":
            investigation_input = sealed_value.get("input")
            exact_input_keys = {
                "original_question",
                "response_language",
                "need_key",
                "read_authority",
                "profile_ref",
                "step_index",
                "trace_digest",
                "previous_result",
                "progress_receipt",
                "remaining_budget",
            }
            previous_count = len(self._validated_stages)
            if (
                not isinstance(investigation_input, Mapping)
                or set(investigation_input) != exact_input_keys
                or investigation_input.get("profile_ref")
                != "JAVA_SOURCE_SEMANTICS@1"
                or investigation_input.get("step_index") != previous_count + 1
                or not isinstance(investigation_input.get("read_authority"), Mapping)
                or not isinstance(investigation_input.get("trace_digest"), str)
                or (
                    previous_count == 0
                    and (
                        investigation_input.get("previous_result") is not None
                        or investigation_input.get("progress_receipt") is not None
                    )
                )
                or (
                    previous_count > 0
                    and (
                        not isinstance(
                            investigation_input.get("previous_result"), Mapping
                        )
                        or not isinstance(
                            investigation_input.get("progress_receipt"), Mapping
                        )
                    )
                )
                or investigation_input.get("remaining_budget")
                != {
                    "model_calls": 4 - previous_count,
                    "execution_steps": 4 - previous_count,
                }
                or sealed_value.get("available_operations")
                != list(
                    constrained_investigation_operations(
                        sealed_input=investigation_input
                    )
                )
            ):
                raise DomainError(
                    ErrorCode.QUALIFICATION_INVALID,
                    "bounded investigation input is outside the exact product trace shape",
                )
        self._validated_stages.append(expected_stage)

    def validate_result(self, result: ModelGatewayResult) -> None:
        expected_actual_model = (
            _DEEPSEEK_ACTUAL_MODEL_FINGERPRINT
            if self.policy_ref
            == BOUNDED_JAVA_SOURCE_SEMANTICS_MODEL_EGRESS_GATEWAY_POLICY_REF
            else "glm-5.2"
        )
        if (
            result.call.provider_type != self.provider_type
            or result.call.adapter_version != self.adapter_version
            or result.call.requested_model_ref != self.model_ref
            or result.isolation_receipt.provider_type != self.provider_type
            or result.isolation_receipt.adapter_version != self.adapter_version
            or result.isolation_receipt.provider_configuration_fingerprint
            != self.provider_configuration_fingerprint
            or result.isolation_receipt.conformance_result_ref
            != self.conformance_result_ref
            or result.call.state is not ModelCallState.COMPLETED
            or result.call.actual_model_fingerprint != expected_actual_model
            or result.call.failure_code is not None
            or result.response is None
            or result.response.actual_model_fingerprint != expected_actual_model
            or result.response.usage_complete is not True
            or result.eligibility.eligible_for_production_domain_output is not True
            or result.eligibility.reason != "ELIGIBLE"
            or result.eligibility.actual_model_fingerprint != expected_actual_model
        ):
            raise DomainError(
                ErrorCode.QUALIFICATION_INVALID,
                "model result is outside the exact Java source-semantics policy",
            )


def _deepseek_conformance_ref_is_exact(value: str) -> bool:
    if not value.startswith(_DEEPSEEK_CONFORMANCE_RESULT_PREFIX):
        return False
    try:
        Digest("sha256:" + value.removeprefix(_DEEPSEEK_CONFORMANCE_RESULT_PREFIX))
    except (TypeError, ValueError):
        return False
    return True


@dataclass(frozen=True, slots=True)
class ModelEgressCallAudit:
    ordinal: int
    request_digest: Digest
    manifest_digest: Digest
    model_call_id: StableId | None
    model_call_state: str
    provider_request_digest: Digest | None
    eligibility_digest: Digest | None
    actual_model_fingerprint: str | None
    failure_code: str | None
    response_digest: Digest

    def canonical_value(self) -> dict[str, object]:
        return {
            "ordinal": self.ordinal,
            "request_digest": self.request_digest.value,
            "manifest_digest": self.manifest_digest.value,
            "model_call_id": (
                self.model_call_id.value if self.model_call_id else None
            ),
            "model_call_state": self.model_call_state,
            "provider_request_digest": (
                self.provider_request_digest.value
                if self.provider_request_digest
                else None
            ),
            "eligibility_digest": (
                self.eligibility_digest.value if self.eligibility_digest else None
            ),
            "actual_model_fingerprint": self.actual_model_fingerprint,
            "failure_code": self.failure_code,
            "response_digest": self.response_digest.value,
        }


class UnixSocketModelGatewayClient:
    """Answer-side client; its only network capability is one AF_UNIX path."""

    def __init__(
        self,
        socket_path: str | Path,
        *,
        timeout_seconds: float = 190.0,
        maximum_calls: int = _MAX_PROVIDER_CALLS,
    ) -> None:
        self._socket_path = _canonical_socket_path(socket_path)
        if timeout_seconds <= 0:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT, "gateway timeout must be positive"
            )
        if type(maximum_calls) is not int or maximum_calls not in {5, 6}:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "answer-side gateway cap must be exactly five or six",
            )
        self._timeout = timeout_seconds
        self._maximum_calls = maximum_calls
        self._audits: list[ModelEgressCallAudit] = []

    @property
    def provider_call_count(self) -> int:
        return len(self._audits)

    @property
    def network_operation_count(self) -> int:
        return len(self._audits)

    @property
    def audits(self) -> tuple[ModelEgressCallAudit, ...]:
        return tuple(self._audits)

    def invoke(self, context: ModelExecutionContext) -> ModelGatewayResult:
        if len(self._audits) >= self._maximum_calls:
            raise DomainError(
                ErrorCode.CONTROL_STATE_DENIED,
                "world-model Provider call fuse exceeded its exact call cap",
            )
        request_core = {
            "schema": MODEL_EGRESS_REQUEST_SCHEMA,
            "context": _context_value(context),
        }
        request = {
            **request_core,
            "request_digest": digest_of(request_core).value,
        }
        request_payload = canonical_json_bytes(request)
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
                connection.settimeout(self._timeout)
                connection.connect(str(self._socket_path))
                _send_frame(connection, request_payload)
                response_payload = _receive_frame(connection)
        except (OSError, TimeoutError) as exc:
            raise DomainError(
                ErrorCode.LIVE_INTEGRATION_HELD,
                "Model Egress Gateway is unavailable or outcome is unknown",
            ) from exc
        response = _unique_json_object(response_payload, "gateway response")
        result, audit = _decode_response(
            response,
            ordinal=len(self._audits) + 1,
            expected_request_digest=Digest(str(request["request_digest"])),
            expected_manifest_digest=context.manifest.digest,
        )
        self._audits.append(audit)
        if result is None:
            raise DomainError(
                ErrorCode.LIVE_INTEGRATION_HELD,
                "Model Egress Gateway rejected the request",
                {"gateway_failure_code": audit.failure_code or "UNKNOWN"},
            )
        return result


class ModelEgressGatewayServer:
    """Gateway-side single-threaded server with an exact five-call fuse."""

    def __init__(
        self,
        socket_path: str | Path,
        *,
        gateway: ModelGatewayPort,
        policy: ModelEgressGatewayPolicy,
        audit_writer: Callable[[Mapping[str, object]], None] | None = None,
        prebound_listener: socket.socket | None = None,
    ) -> None:
        self._socket_path = _canonical_socket_path(socket_path)
        self._gateway = gateway
        self._policy = policy
        self._audit_writer = audit_writer or (lambda _: None)
        self._prebound_listener = prebound_listener

    def serve(
        self,
        *,
        startup_timeout_seconds: float = 60.0,
        idle_timeout_seconds: float = 5.0,
    ) -> int:
        self._socket_path.parent.resolve(strict=True)
        request_count = 0
        listener = self._take_or_create_listener()
        with listener:
            listener.settimeout(startup_timeout_seconds)
            try:
                while request_count < self._policy.max_provider_calls:
                    try:
                        connection, _ = listener.accept()
                    except TimeoutError:
                        break
                    with connection:
                        request_count += 1
                        response = self._handle(connection, request_count)
                        _send_frame(connection, canonical_json_bytes(response))
                    listener.settimeout(idle_timeout_seconds)
            finally:
                try:
                    self._socket_path.unlink()
                except FileNotFoundError:
                    pass
        return request_count

    def _take_or_create_listener(self) -> socket.socket:
        if self._prebound_listener is None:
            if self._socket_path.exists() or self._socket_path.is_symlink():
                raise DomainError(
                    ErrorCode.CONTROL_STATE_DENIED,
                    "Model Egress Gateway socket path already exists",
                )
            listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            try:
                listener.bind(str(self._socket_path))
                self._socket_path.chmod(0o600)
                listener.listen(1)
            except BaseException:
                listener.close()
                try:
                    self._socket_path.unlink()
                except FileNotFoundError:
                    pass
                raise
            return listener

        listener = self._prebound_listener
        self._prebound_listener = None
        try:
            path_status = self._socket_path.lstat()
            bound_path = listener.getsockname()
            if isinstance(bound_path, bytes):
                bound_path = bound_path.decode("utf-8")
            if (
                self._socket_path.is_symlink()
                or not stat.S_ISSOCK(path_status.st_mode)
                or stat.S_IMODE(path_status.st_mode) != 0o600
                or listener.family != socket.AF_UNIX
                or (listener.type & socket.SOCK_STREAM) != socket.SOCK_STREAM
                or bound_path != str(self._socket_path)
            ):
                raise DomainError(
                    ErrorCode.CONTROL_STATE_DENIED,
                    "prebound Model Egress Gateway listener is not exact",
                )
        except DomainError:
            listener.close()
            raise
        except (OSError, UnicodeError) as exc:
            listener.close()
            raise DomainError(
                ErrorCode.CONTROL_STATE_DENIED,
                "prebound Model Egress Gateway listener is not exact",
            ) from exc
        return listener

    def _handle(
        self, connection: socket.socket, ordinal: int
    ) -> dict[str, object]:
        request_digest: Digest | None = None
        manifest_digest: Digest | None = None
        try:
            request = _unique_json_object(
                _receive_frame(connection), "gateway request"
            )
            _exact_keys(
                request,
                {"schema", "context", "request_digest"},
                "gateway request",
            )
            if request["schema"] != MODEL_EGRESS_REQUEST_SCHEMA:
                raise DomainError(
                    ErrorCode.INVALID_ARGUMENT, "gateway request schema is invalid"
                )
            request_digest = Digest(
                _text_value(request["request_digest"], "request digest")
            )
            if request_digest != digest_of(
                {"schema": request["schema"], "context": request["context"]}
            ):
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "gateway request digest does not verify",
                )
            context = _context_from_value(request["context"])
            manifest_digest = context.manifest.digest
            self._policy.validate_context(context)
            result = self._gateway.invoke(context)
            self._policy.validate_result(result)
            response_core = {
                "schema": MODEL_EGRESS_RESPONSE_SCHEMA,
                "request_digest": request_digest.value,
                "status": "RESULT",
                "result": _result_value(result),
                "failure": None,
            }
        except DomainError as exc:
            response_core = {
                "schema": MODEL_EGRESS_RESPONSE_SCHEMA,
                "request_digest": (
                    request_digest.value if request_digest else None
                ),
                "status": "REJECTED",
                "result": None,
                "failure": {
                    "code": exc.code.value,
                    "reason_code": str(
                        exc.details.get("reason_code", exc.code.value)
                    ),
                },
            }
        except BaseException as exc:
            response_core = {
                "schema": MODEL_EGRESS_RESPONSE_SCHEMA,
                "request_digest": (
                    request_digest.value if request_digest else None
                ),
                "status": "REJECTED",
                "result": None,
                "failure": {
                    "code": "GATEWAY_INTERNAL_ERROR",
                    "reason_code": type(exc).__name__,
                },
            }
        response = {
            **response_core,
            "response_digest": digest_of(response_core).value,
        }
        audit = {
            "schema": "swm.model-egress-server-audit@1",
            "ordinal": ordinal,
            "policy_ref": self._policy.policy_ref,
            "policy_digest": self._policy.policy_digest.value,
            "capability_qualification_ref": (
                self._policy.capability_qualification_ref
            ),
            "capability_qualification_digest": (
                self._policy.capability_qualification_digest.value
            ),
            "request_digest": (
                request_digest.value if request_digest else None
            ),
            "manifest_digest": (
                manifest_digest.value if manifest_digest else None
            ),
            "response_digest": response["response_digest"],
            "status": response["status"],
        }
        self._audit_writer(audit)
        return response


def _context_value(context: ModelExecutionContext) -> dict[str, object]:
    manifest = context.manifest
    return {
        "execution_envelope_ref": context.execution_envelope_ref,
        "manifest": {
            "manifest_id": manifest.manifest_id.value,
            "version": manifest.version.value,
            "capability_id": manifest.capability_id,
            "strategy_ref": manifest.strategy_ref,
            "execution_stage": manifest.execution_stage,
            "calling_module": manifest.calling_module,
            "proposal_vocabulary_ref": manifest.proposal_vocabulary_ref,
            "items": [
                {
                    "item_id": item.item_id,
                    "schema_ref": item.schema_ref,
                    "classification": item.classification,
                    "purpose": item.purpose,
                    "authority_reference": item.authority_reference,
                    "disposition": item.disposition.value,
                    "content": item.content,
                    "transformation_ref": item.transformation_ref,
                    "content_digest": item.content_digest.value,
                }
                for item in manifest.items
            ],
            "digest": manifest.digest.value,
        },
        "prompt_program_ref": context.prompt_program_ref,
        "rendering_contract_version": context.rendering_contract_version,
        "output_schema_ref": context.output_schema_ref,
        "runtime_access_mode": context.runtime_access_mode.value,
        "platform_proposal_mode": context.platform_proposal_mode.value,
        "requested_model_ref": context.requested_model_ref,
        "provider_type": context.provider_type,
        "adapter_version": context.adapter_version,
        "provider_configuration_fingerprint": (
            context.provider_configuration_fingerprint.value
        ),
        "max_output_tokens": context.max_output_tokens,
        "timeout_milliseconds": context.timeout_milliseconds,
        "classification": context.classification,
        "required_exact_fingerprint": context.required_exact_fingerprint,
    }


def _context_from_value(value: object) -> ModelExecutionContext:
    context = _mapping(value, "model execution context")
    _exact_keys(
        context,
        {
            "execution_envelope_ref",
            "manifest",
            "prompt_program_ref",
            "rendering_contract_version",
            "output_schema_ref",
            "runtime_access_mode",
            "platform_proposal_mode",
            "requested_model_ref",
            "provider_type",
            "adapter_version",
            "provider_configuration_fingerprint",
            "max_output_tokens",
            "timeout_milliseconds",
            "classification",
            "required_exact_fingerprint",
        },
        "model execution context",
    )
    manifest_value = _mapping(context["manifest"], "authorized input manifest")
    _exact_keys(
        manifest_value,
        {
            "manifest_id",
            "version",
            "capability_id",
            "strategy_ref",
            "execution_stage",
            "calling_module",
            "proposal_vocabulary_ref",
            "items",
            "digest",
        },
        "authorized input manifest",
    )
    raw_items = manifest_value["items"]
    if not isinstance(raw_items, list) or not raw_items:
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT, "authorized input manifest is empty"
        )
    items: list[AuthorizedInputItem] = []
    for index, raw in enumerate(raw_items):
        item_value = _mapping(raw, f"authorized input item {index}")
        _exact_keys(
            item_value,
            {
                "item_id",
                "schema_ref",
                "classification",
                "purpose",
                "authority_reference",
                "disposition",
                "content",
                "transformation_ref",
                "content_digest",
            },
            f"authorized input item {index}",
        )
        item = AuthorizedInputItem.create(
            item_id=_text_value(item_value["item_id"], "item ID"),
            schema_ref=_text_value(item_value["schema_ref"], "schema ref"),
            classification=_text_value(
                item_value["classification"], "classification"
            ),
            purpose=_text_value(item_value["purpose"], "purpose"),
            authority_reference=_text_value(
                item_value["authority_reference"], "authority reference"
            ),
            disposition=InputDisposition(
                _text_value(item_value["disposition"], "input disposition")
            ),
            content=_string_value(item_value["content"], "authorized input content"),
            transformation_ref=_text_value(
                item_value["transformation_ref"], "transformation ref"
            ),
        )
        if item.content_digest.value != item_value["content_digest"]:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "authorized input item digest does not verify",
            )
        items.append(item)
    manifest = AuthorizedInputManifest(
        manifest_id=StableId(
            _text_value(manifest_value["manifest_id"], "manifest ID")
        ),
        version=Revision(
            _exact_positive_int(manifest_value["version"], "manifest version")
        ),
        capability_id=_text_value(
            manifest_value["capability_id"], "capability ID"
        ),
        strategy_ref=_text_value(manifest_value["strategy_ref"], "strategy ref"),
        execution_stage=_text_value(
            manifest_value["execution_stage"], "execution stage"
        ),
        calling_module=_text_value(
            manifest_value["calling_module"], "calling module"
        ),
        proposal_vocabulary_ref=(
            _text_value(
                manifest_value["proposal_vocabulary_ref"],
                "proposal vocabulary ref",
            )
            if manifest_value["proposal_vocabulary_ref"] is not None
            else None
        ),
        items=tuple(items),
        digest=Digest(_text_value(manifest_value["digest"], "manifest digest")),
    )
    manifest_core = {
        "manifest_id": manifest.manifest_id.value,
        "version": manifest.version.value,
        "capability_id": manifest.capability_id,
        "strategy_ref": manifest.strategy_ref,
        "execution_stage": manifest.execution_stage,
        "calling_module": manifest.calling_module,
        "proposal_vocabulary_ref": manifest.proposal_vocabulary_ref,
        "items": manifest.items,
    }
    if manifest.digest != digest_of(manifest_core):
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "authorized input manifest digest does not verify",
        )
    try:
        return ModelExecutionContext(
            execution_envelope_ref=_text_value(
                context["execution_envelope_ref"], "execution envelope ref"
            ),
            manifest=manifest,
            prompt_program_ref=_text_value(
                context["prompt_program_ref"], "prompt program ref"
            ),
            rendering_contract_version=_text_value(
                context["rendering_contract_version"],
                "rendering contract version",
            ),
            output_schema_ref=_text_value(
                context["output_schema_ref"], "output schema ref"
            ),
            runtime_access_mode=RuntimeAccessMode(
                _text_value(context["runtime_access_mode"], "runtime access mode")
            ),
            platform_proposal_mode=PlatformProposalMode(
                _text_value(
                    context["platform_proposal_mode"], "platform proposal mode"
                )
            ),
            requested_model_ref=_text_value(
                context["requested_model_ref"], "requested model ref"
            ),
            provider_type=_text_value(context["provider_type"], "provider type"),
            adapter_version=_text_value(
                context["adapter_version"], "adapter version"
            ),
            provider_configuration_fingerprint=Digest(
                _text_value(
                    context["provider_configuration_fingerprint"],
                    "provider configuration fingerprint",
                )
            ),
            max_output_tokens=_exact_positive_int(
                context["max_output_tokens"], "maximum output tokens"
            ),
            timeout_milliseconds=_exact_positive_int(
                context["timeout_milliseconds"], "timeout milliseconds"
            ),
            classification=_text_value(
                context["classification"], "classification"
            ),
            required_exact_fingerprint=_exact_bool(
                context["required_exact_fingerprint"],
                "required exact fingerprint",
            ),
        )
    except ValueError as exc:
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            "model execution context enum value is invalid",
        ) from exc


def _result_value(result: ModelGatewayResult) -> dict[str, object]:
    call = result.call
    receipt = result.isolation_receipt
    eligibility = result.eligibility
    response = result.response
    return {
        "call": {
            "model_call_id": call.model_call_id.value,
            "revision": call.revision.value,
            "state": call.state.value,
            "manifest_id": call.manifest_id.value,
            "manifest_digest": call.manifest_digest.value,
            "provider_request_digest": call.provider_request_digest.value,
            "isolation_receipt_id": call.isolation_receipt_id.value,
            "isolation_receipt_digest": call.isolation_receipt_digest.value,
            "provider_type": call.provider_type,
            "adapter_version": call.adapter_version,
            "requested_model_ref": call.requested_model_ref,
            "actual_model_fingerprint": call.actual_model_fingerprint,
            "provider_request_id": call.provider_request_id,
            "output_digest": call.output_digest.value if call.output_digest else None,
            "input_tokens": call.input_tokens,
            "output_tokens": call.output_tokens,
            "usage_complete": call.usage_complete,
            "failure_code": call.failure_code,
            "created_at": call.created_at.isoformat(),
            "revised_at": call.revised_at.isoformat(),
        },
        "response": (
            {
                "provider_request_id": response.provider_request_id,
                "actual_model_fingerprint": response.actual_model_fingerprint,
                "replay_classification": response.replay_classification.value,
                "output_text": response.output_text,
                "output_digest": response.output_digest.value,
                "input_tokens": response.input_tokens,
                "output_tokens": response.output_tokens,
                "usage_complete": response.usage_complete,
                "termination_reason": response.termination_reason,
                "output_normalization": response.output_normalization,
            }
            if response is not None
            else None
        ),
        "isolation_receipt": {
            "receipt_id": receipt.receipt_id.value,
            "manifest_digest": receipt.manifest_digest.value,
            "provider_request_digest": receipt.provider_request_digest.value,
            "provider_type": receipt.provider_type,
            "adapter_version": receipt.adapter_version,
            "provider_configuration_fingerprint": (
                receipt.provider_configuration_fingerprint.value
            ),
            "runtime_access_mode": receipt.runtime_access_mode.value,
            "platform_proposal_mode": receipt.platform_proposal_mode.value,
            "conformance_result_ref": receipt.conformance_result_ref,
            "issued_at": receipt.issued_at.isoformat(),
            "digest": receipt.digest.value,
        },
        "eligibility": {
            "eligible_for_production_domain_output": (
                eligibility.eligible_for_production_domain_output
            ),
            "reason": eligibility.reason,
            "actual_model_fingerprint": eligibility.actual_model_fingerprint,
            "isolation_receipt_id": eligibility.isolation_receipt_id.value,
            "model_call_id": eligibility.model_call_id.value,
            "digest": eligibility.digest.value,
        },
        "replayed": result.replayed,
    }


def _decode_response(
    response: Mapping[str, object],
    *,
    ordinal: int,
    expected_request_digest: Digest,
    expected_manifest_digest: Digest,
) -> tuple[ModelGatewayResult | None, ModelEgressCallAudit]:
    _exact_keys(
        response,
        {
            "schema",
            "request_digest",
            "status",
            "result",
            "failure",
            "response_digest",
        },
        "gateway response",
    )
    response_core = {
        key: response[key] for key in response if key != "response_digest"
    }
    response_digest = Digest(
        _text_value(response["response_digest"], "gateway response digest")
    )
    if (
        response["schema"] != MODEL_EGRESS_RESPONSE_SCHEMA
        or response_digest != digest_of(response_core)
        or response["request_digest"] != expected_request_digest.value
    ):
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "Model Egress Gateway response binding does not verify",
        )
    if response["status"] == "REJECTED":
        if response["result"] is not None:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "rejected gateway response carries a result",
            )
        failure = _mapping(response["failure"], "gateway failure")
        _exact_keys(failure, {"code", "reason_code"}, "gateway failure")
        failure_code = _text_value(failure["code"], "gateway failure code")
        _text_value(failure["reason_code"], "gateway failure reason code")
        audit = ModelEgressCallAudit(
            ordinal=ordinal,
            request_digest=expected_request_digest,
            manifest_digest=expected_manifest_digest,
            model_call_id=None,
            model_call_state="REJECTED",
            provider_request_digest=None,
            eligibility_digest=None,
            actual_model_fingerprint=None,
            failure_code=failure_code,
            response_digest=response_digest,
        )
        return None, audit
    if response["status"] != "RESULT" or response["failure"] is not None:
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "Model Egress Gateway response status is invalid",
        )
    result = _result_from_value(response["result"])
    if result.call.manifest_digest != expected_manifest_digest:
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "Model Egress Gateway result binds another manifest",
        )
    audit = ModelEgressCallAudit(
        ordinal=ordinal,
        request_digest=expected_request_digest,
        manifest_digest=expected_manifest_digest,
        model_call_id=result.call.model_call_id,
        model_call_state=result.call.state.value,
        provider_request_digest=result.call.provider_request_digest,
        eligibility_digest=result.eligibility.digest,
        actual_model_fingerprint=result.call.actual_model_fingerprint,
        failure_code=result.call.failure_code,
        response_digest=response_digest,
    )
    return result, audit


def _result_from_value(value: object) -> ModelGatewayResult:
    result = _mapping(value, "gateway result")
    _exact_keys(
        result,
        {"call", "response", "isolation_receipt", "eligibility", "replayed"},
        "gateway result",
    )
    call_value = _mapping(result["call"], "model call")
    receipt_value = _mapping(result["isolation_receipt"], "isolation receipt")
    eligibility_value = _mapping(result["eligibility"], "model eligibility")
    _exact_keys(
        call_value,
        {
            "model_call_id",
            "revision",
            "state",
            "manifest_id",
            "manifest_digest",
            "provider_request_digest",
            "isolation_receipt_id",
            "isolation_receipt_digest",
            "provider_type",
            "adapter_version",
            "requested_model_ref",
            "actual_model_fingerprint",
            "provider_request_id",
            "output_digest",
            "input_tokens",
            "output_tokens",
            "usage_complete",
            "failure_code",
            "created_at",
            "revised_at",
        },
        "model call",
    )
    _exact_keys(
        receipt_value,
        {
            "receipt_id",
            "manifest_digest",
            "provider_request_digest",
            "provider_type",
            "adapter_version",
            "provider_configuration_fingerprint",
            "runtime_access_mode",
            "platform_proposal_mode",
            "conformance_result_ref",
            "issued_at",
            "digest",
        },
        "isolation receipt",
    )
    _exact_keys(
        eligibility_value,
        {
            "eligible_for_production_domain_output",
            "reason",
            "actual_model_fingerprint",
            "isolation_receipt_id",
            "model_call_id",
            "digest",
        },
        "model eligibility",
    )
    call = ModelCallRecord(
        model_call_id=StableId(
            _text_value(call_value["model_call_id"], "model call ID")
        ),
        revision=Revision(
            _exact_positive_int(call_value["revision"], "model call revision")
        ),
        state=ModelCallState(
            _text_value(call_value["state"], "model call state")
        ),
        manifest_id=StableId(
            _text_value(call_value["manifest_id"], "manifest ID")
        ),
        manifest_digest=Digest(
            _text_value(call_value["manifest_digest"], "manifest digest")
        ),
        provider_request_digest=Digest(
            _text_value(
                call_value["provider_request_digest"],
                "provider request digest",
            )
        ),
        isolation_receipt_id=StableId(
            _text_value(
                call_value["isolation_receipt_id"], "isolation receipt ID"
            )
        ),
        isolation_receipt_digest=Digest(
            _text_value(
                call_value["isolation_receipt_digest"],
                "isolation receipt digest",
            )
        ),
        provider_type=_text_value(call_value["provider_type"], "provider type"),
        adapter_version=_text_value(
            call_value["adapter_version"], "adapter version"
        ),
        requested_model_ref=_text_value(
            call_value["requested_model_ref"], "requested model ref"
        ),
        actual_model_fingerprint=_optional_text(
            call_value["actual_model_fingerprint"]
        ),
        provider_request_id=_optional_text(call_value["provider_request_id"]),
        output_digest=(
            Digest(
                _text_value(call_value["output_digest"], "model output digest")
            )
            if call_value["output_digest"] is not None
            else None
        ),
        input_tokens=_optional_nonnegative_int(call_value["input_tokens"]),
        output_tokens=_optional_nonnegative_int(call_value["output_tokens"]),
        usage_complete=_exact_bool(call_value["usage_complete"], "usage complete"),
        failure_code=_optional_text(call_value["failure_code"]),
        created_at=_time_value(call_value["created_at"], "created at"),
        revised_at=_time_value(call_value["revised_at"], "revised at"),
    )
    response_value = result["response"]
    response: AdapterResponse | None
    if response_value is None:
        response = None
    else:
        raw = _mapping(response_value, "adapter response")
        _exact_keys(
            raw,
            {
                "provider_request_id",
                "actual_model_fingerprint",
                "replay_classification",
                "output_text",
                "output_digest",
                "input_tokens",
                "output_tokens",
                "usage_complete",
                "termination_reason",
                "output_normalization",
            },
            "adapter response",
        )
        response = AdapterResponse(
            provider_request_id=_optional_text(raw["provider_request_id"]),
            actual_model_fingerprint=_optional_text(
                raw["actual_model_fingerprint"]
            ),
            replay_classification=ReplayClassification(
                _text_value(raw["replay_classification"], "replay classification")
            ),
            output_text=_string_value(raw["output_text"], "model output text"),
            output_digest=Digest(
                _text_value(raw["output_digest"], "model output digest")
            ),
            input_tokens=_optional_nonnegative_int(raw["input_tokens"]),
            output_tokens=_optional_nonnegative_int(raw["output_tokens"]),
            usage_complete=_exact_bool(raw["usage_complete"], "usage complete"),
            termination_reason=_text_value(
                raw["termination_reason"], "termination reason"
            ),
            output_normalization=_text_value(
                raw["output_normalization"], "output normalization"
            ),
        )
        if response.output_digest != digest_of(response.output_text):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "adapter response output digest does not verify",
            )
    receipt = IsolationReceipt(
        receipt_id=StableId(
            _text_value(receipt_value["receipt_id"], "receipt ID")
        ),
        manifest_digest=Digest(
            _text_value(receipt_value["manifest_digest"], "manifest digest")
        ),
        provider_request_digest=Digest(
            _text_value(
                receipt_value["provider_request_digest"],
                "provider request digest",
            )
        ),
        provider_type=_text_value(
            receipt_value["provider_type"], "provider type"
        ),
        adapter_version=_text_value(
            receipt_value["adapter_version"], "adapter version"
        ),
        provider_configuration_fingerprint=Digest(
            _text_value(
                receipt_value["provider_configuration_fingerprint"],
                "provider configuration fingerprint",
            )
        ),
        runtime_access_mode=RuntimeAccessMode(
            _text_value(receipt_value["runtime_access_mode"], "runtime access mode")
        ),
        platform_proposal_mode=PlatformProposalMode(
            _text_value(
                receipt_value["platform_proposal_mode"],
                "platform proposal mode",
            )
        ),
        conformance_result_ref=_text_value(
            receipt_value["conformance_result_ref"], "conformance result ref"
        ),
        issued_at=_time_value(receipt_value["issued_at"], "issued at"),
        digest=Digest(str(receipt_value["digest"])),
    )
    receipt_core = {
        "receipt_id": receipt.receipt_id.value,
        "manifest_digest": receipt.manifest_digest.value,
        "provider_request_digest": receipt.provider_request_digest.value,
        "provider_type": receipt.provider_type,
        "adapter_version": receipt.adapter_version,
        "provider_configuration_fingerprint": (
            receipt.provider_configuration_fingerprint.value
        ),
        "runtime_access_mode": receipt.runtime_access_mode.value,
        "platform_proposal_mode": receipt.platform_proposal_mode.value,
        "conformance_result_ref": receipt.conformance_result_ref,
        "issued_at": receipt.issued_at,
    }
    if receipt.digest != digest_of(receipt_core):
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "isolation receipt digest does not verify",
        )
    eligibility = ModelResultEligibility(
        eligible_for_production_domain_output=_exact_bool(
            eligibility_value["eligible_for_production_domain_output"],
            "model eligibility",
        ),
        reason=_text_value(eligibility_value["reason"], "eligibility reason"),
        actual_model_fingerprint=_optional_text(
            eligibility_value["actual_model_fingerprint"]
        ),
        isolation_receipt_id=StableId(
            _text_value(
                eligibility_value["isolation_receipt_id"],
                "isolation receipt ID",
            )
        ),
        model_call_id=StableId(
            _text_value(eligibility_value["model_call_id"], "model call ID")
        ),
        digest=Digest(
            _text_value(eligibility_value["digest"], "eligibility digest")
        ),
    )
    eligibility_core = {
        "eligible": eligibility.eligible_for_production_domain_output,
        "reason": eligibility.reason,
        "actual_model_fingerprint": eligibility.actual_model_fingerprint,
        "isolation_receipt_id": eligibility.isolation_receipt_id.value,
        "model_call_id": eligibility.model_call_id.value,
    }
    if (
        eligibility.digest != digest_of(eligibility_core)
        or call.isolation_receipt_id != receipt.receipt_id
        or call.isolation_receipt_digest != receipt.digest
        or eligibility.isolation_receipt_id != receipt.receipt_id
        or eligibility.model_call_id != call.model_call_id
        or call.manifest_digest != receipt.manifest_digest
        or call.provider_request_digest != receipt.provider_request_digest
        or call.provider_type != receipt.provider_type
        or call.adapter_version != receipt.adapter_version
        or eligibility.actual_model_fingerprint != call.actual_model_fingerprint
        or (response is not None and call.output_digest != response.output_digest)
        or (
            response is not None
            and (
                call.provider_request_id != response.provider_request_id
                or call.actual_model_fingerprint
                != response.actual_model_fingerprint
                or call.input_tokens != response.input_tokens
                or call.output_tokens != response.output_tokens
                or call.usage_complete != response.usage_complete
            )
        )
    ):
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "gateway model result cross-links do not verify",
        )
    return ModelGatewayResult(
        call=call,
        response=response,
        isolation_receipt=receipt,
        eligibility=eligibility,
        replayed=_exact_bool(result["replayed"], "replayed marker"),
    )


def _send_frame(connection: socket.socket, payload: bytes) -> None:
    if not payload or len(payload) > _MAX_FRAME_BYTES:
        raise DomainError(ErrorCode.INVALID_ARGUMENT, "gateway frame size is invalid")
    connection.sendall(_HEADER.pack(len(payload)) + payload)


def _receive_frame(connection: socket.socket) -> bytes:
    header = _receive_exact(connection, _HEADER.size)
    (size,) = _HEADER.unpack(header)
    if size < 1 or size > _MAX_FRAME_BYTES:
        raise DomainError(ErrorCode.INVALID_ARGUMENT, "gateway frame size is invalid")
    return _receive_exact(connection, size)


def _receive_exact(connection: socket.socket, size: int) -> bytes:
    chunks: list[bytes] = []
    remaining = size
    while remaining:
        chunk = connection.recv(remaining)
        if not chunk:
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "gateway frame is truncated")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def _unique_json_object(payload: bytes, label: str) -> dict[str, object]:
    try:
        value = json.loads(
            payload,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} is not canonical JSON") from exc
    if not isinstance(value, dict) or canonical_json_bytes(value) != payload:
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} is not canonical JSON")
    return value


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def _reject_constant(value: str) -> object:
    raise ValueError(f"non-finite JSON value: {value}")


def _contains_forbidden_model_key(value: object) -> bool:
    if isinstance(value, dict):
        return any(
            key.casefold() in _FORBIDDEN_MODEL_INPUT_KEYS
            or _contains_forbidden_model_key(item)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return any(_contains_forbidden_model_key(item) for item in value)
    return False


def _canonical_socket_path(value: str | Path) -> Path:
    path = Path(value)
    if not path.is_absolute() or path.resolve(strict=False) != path:
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            "Model Egress Gateway socket path must be canonical and absolute",
        )
    if len(str(path).encode("utf-8")) >= 100:
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            "Model Egress Gateway socket path exceeds the AF_UNIX limit",
        )
    return path


def _mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, dict):
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} must be an object")
    return value


def _exact_keys(value: Mapping[str, object], keys: set[str], label: str) -> None:
    if set(value) != keys:
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} fields are invalid")


def _text(value: str, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} must be non-empty")
    return value


def _text_value(value: object, label: str) -> str:
    if not isinstance(value, str):
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} must be text")
    return _text(value, label)


def _string_value(value: object, label: str) -> str:
    if not isinstance(value, str):
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} must be text")
    return value


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    return _text_value(value, "optional text")


def _exact_bool(value: object, label: str) -> bool:
    if type(value) is not bool:
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} must be boolean")
    return value


def _exact_positive_int(value: object, label: str) -> int:
    if type(value) is not int or value < 1:
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} must be positive")
    return value


def _optional_nonnegative_int(value: object) -> int | None:
    if value is None:
        return None
    if type(value) is not int or value < 0:
        raise DomainError(ErrorCode.INVALID_ARGUMENT, "token count is invalid")
    return value


def _time_value(value: object, label: str) -> datetime:
    if not isinstance(value, str):
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} is invalid")
    try:
        result = datetime.fromisoformat(value)
    except ValueError as exc:
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} is invalid") from exc
    if result.tzinfo is None or result.utcoffset() is None:
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} is not aware")
    return result
