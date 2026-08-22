"""Closed role input/output boundaries for adaptive Engineering QA.

This module does not dispatch a Provider request.  It freezes the role-specific
input closures, versioned output schemas, receipt bindings, and domain Proposal
adapters consumed by qualified model strategies in a later, separately authorized
runtime.  It remains free of a Gateway, credential resolver, or network adapter,
so the Slice 1 development subject is mechanically local.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
import json
from types import MappingProxyType
from typing import Mapping, NoReturn, Protocol, Sequence, cast

from software_world_model.application_services.engineering_question_answering import (
    AnswerClaimKind,
    ChecklistDisposition,
    ChecklistOutcome,
    ENGINEERING_QA_PROTOCOL,
    EngineeringAnswerClaimProposal,
    EngineeringAnswerDraft,
    EngineeringAnswerProposal,
    EngineeringAnswerRole,
    EngineeringAnswerReviewerRole,
    EngineeringEvidenceClass,
    EngineeringQuestionRequest,
    EngineeringReviewDecision,
    EngineeringReviewFinding,
    EngineeringReviewProposal,
    InitialInvestigationInput,
    InitialInvestigationRole,
    InvestigationKind,
    InvestigationOperation,
    InvestigationStepProposal,
    QuestionEvidencePackage,
    QuestionUnderstanding,
    QuestionUnderstandingProposal,
    QuestionUnderstandingRole,
    VerificationInvestigationInput,
    VerificationInvestigationRole,
    VerificationRequestProposal,
)
from software_world_model.cross_cutting import (
    Digest,
    DomainError,
    ErrorCode,
    StableId,
    digest_of,
)

from .openai_responses_adapter import OutputSchemaDefinition


ENGINEERING_QUESTION_ROLE_INPUT_SCHEMA = "ENGINEERING_QA_ROLE_INPUT@1"
ENGINEERING_QUESTION_ROLE_OUTPUT_SCHEMA = "ENGINEERING_QA_ROLE_OUTPUT@1"
ENGINEERING_QUESTION_STRATEGY_REF = "engineering-qa-adaptive-investigation-local-contract@1"

ENGINEERING_QUESTION_UNDERSTANDING_OUTPUT_SCHEMA_REF = (
    "engineering-qa-question-understanding@1"
)
ENGINEERING_QUESTION_INITIAL_INVESTIGATION_OUTPUT_SCHEMA_REF = (
    "engineering-qa-initial-investigation@2"
)
ENGINEERING_QUESTION_VERIFICATION_INVESTIGATION_OUTPUT_SCHEMA_REF = (
    "engineering-qa-verification-investigation@2"
)
ENGINEERING_QUESTION_ANSWER_OUTPUT_SCHEMA_REF = "engineering-qa-answer@1"
ENGINEERING_QUESTION_REVIEW_OUTPUT_SCHEMA_REF = "engineering-qa-review@1"

_MAXIMUM_ROLE_OUTPUT_BYTES = 1_048_576


def _freeze(value: object) -> object:
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    return value


def _thaw(value: object) -> object:
    if isinstance(value, Mapping):
        return {key: _thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw(item) for item in value]
    return value


class EngineeringQuestionModelRole(str, Enum):
    QUESTION_UNDERSTANDING = "QUESTION_UNDERSTANDING"
    INITIAL_INVESTIGATION = "INITIAL_INVESTIGATION"
    VERIFICATION_INVESTIGATION = "VERIFICATION_INVESTIGATION"
    ANSWER = "ANSWER"
    REVIEW = "REVIEW"


_NULLABLE_STRING_SCHEMA = {"type": ["string", "null"]}
_STRING_ARRAY_SCHEMA = {"type": "array", "items": {"type": "string"}}
_NONEMPTY_UNIQUE_STRING_ARRAY_SCHEMA = {
    "type": "array",
    "items": {"type": "string"},
    "minItems": 1,
    "uniqueItems": True,
}
_EVIDENCE_CLASS_SCHEMA = {
    "type": ["string", "null"],
    "enum": [
        EngineeringEvidenceClass.SOURCE.value,
        EngineeringEvidenceClass.REPOSITORY_DOCUMENT.value,
        EngineeringEvidenceClass.BUILD_CONFIGURATION.value,
        EngineeringEvidenceClass.TEST.value,
        None,
    ],
}
_REQUIRED_EVIDENCE_CLASS_SCHEMA = {
    "type": "string",
    "enum": [
        EngineeringEvidenceClass.SOURCE.value,
        EngineeringEvidenceClass.REPOSITORY_DOCUMENT.value,
        EngineeringEvidenceClass.BUILD_CONFIGURATION.value,
        EngineeringEvidenceClass.TEST.value,
    ],
}
_FINISH_DISPOSITION_SCHEMA = {
    "type": "object",
    "properties": {
        "checklist_item_id": {"type": "string"},
        "outcome": {
            "type": "string",
            "enum": [item.value for item in ChecklistOutcome],
        },
        "evidence_references": _NONEMPTY_UNIQUE_STRING_ARRAY_SCHEMA,
        "explanation": {"type": "string"},
    },
    "required": [
        "checklist_item_id",
        "outcome",
        "evidence_references",
        "explanation",
    ],
    "additionalProperties": False,
}
_INVESTIGATION_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "operation": {
            "type": "string",
            "enum": [item.value for item in InvestigationOperation],
        },
        "checklist_item_ids": _STRING_ARRAY_SCHEMA,
        "evidence_class": _EVIDENCE_CLASS_SCHEMA,
        "query": _NULLABLE_STRING_SCHEMA,
        "locator_reference": _NULLABLE_STRING_SCHEMA,
        "basis_entry_ids": _STRING_ARRAY_SCHEMA,
        "unknown_to_reduce": {"type": "string"},
        "finish_dispositions": {
            "type": "array",
            "items": _FINISH_DISPOSITION_SCHEMA,
        },
    },
    "required": [
        "operation",
        "checklist_item_ids",
        "evidence_class",
        "query",
        "locator_reference",
        "basis_entry_ids",
        "unknown_to_reduce",
        "finish_dispositions",
    ],
    "additionalProperties": False,
}
_QUESTION_UNDERSTANDING_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "preserved_original_question": {"type": "string"},
        "user_goal": {"type": "string"},
        "audience": {"type": "string"},
        "requested_abstraction_level": {"type": "string"},
        "material_conclusions": _STRING_ARRAY_SCHEMA,
        "evidence_needs": _STRING_ARRAY_SCHEMA,
        "response_language": {"type": "string"},
        "response_constraints": _STRING_ARRAY_SCHEMA,
    },
    "required": [
        "preserved_original_question",
        "user_goal",
        "audience",
        "requested_abstraction_level",
        "material_conclusions",
        "evidence_needs",
        "response_language",
        "response_constraints",
    ],
    "additionalProperties": False,
}
_ANSWER_CLAIM_SCHEMA = {
    "type": "object",
    "properties": {
        "claim_id": {"type": "string"},
        "kind": {
            "type": "string",
            "enum": [item.value for item in AnswerClaimKind],
        },
        "text": {"type": "string"},
        "evidence_entry_ids": _STRING_ARRAY_SCHEMA,
    },
    "required": ["claim_id", "kind", "text", "evidence_entry_ids"],
    "additionalProperties": False,
}
_ANSWER_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "response_language": {"type": "string"},
        "claims": {"type": "array", "items": _ANSWER_CLAIM_SCHEMA},
    },
    "required": ["response_language", "claims"],
    "additionalProperties": False,
}
_REVIEW_FINDING_SCHEMA = {
    "type": "object",
    "properties": {
        "finding_code": {"type": "string"},
        "checklist_item_id": _NULLABLE_STRING_SCHEMA,
        "claim_id": _NULLABLE_STRING_SCHEMA,
        "description": {"type": "string"},
    },
    "required": [
        "finding_code",
        "checklist_item_id",
        "claim_id",
        "description",
    ],
    "additionalProperties": False,
}
_VERIFICATION_REQUEST_SCHEMA = {
    "type": "object",
    "properties": {
        "checklist_item_id": {"type": "string"},
        "claim_id": _NULLABLE_STRING_SCHEMA,
        "evidence_class": _REQUIRED_EVIDENCE_CLASS_SCHEMA,
        "evidence_need": {"type": "string"},
    },
    "required": [
        "checklist_item_id",
        "claim_id",
        "evidence_class",
        "evidence_need",
    ],
    "additionalProperties": False,
}
_REVIEW_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "decision": {
            "type": "string",
            "enum": [item.value for item in EngineeringReviewDecision],
        },
        "findings": {"type": "array", "items": _REVIEW_FINDING_SCHEMA},
        "verification_request": {
            "anyOf": [_VERIFICATION_REQUEST_SCHEMA, {"type": "null"}]
        },
    },
    "required": ["decision", "findings", "verification_request"],
    "additionalProperties": False,
}

_OUTPUT_SCHEMA_BY_REF: Mapping[str, tuple[str, Mapping[str, object]]] = {
    ENGINEERING_QUESTION_UNDERSTANDING_OUTPUT_SCHEMA_REF: (
        "engineering_qa_question_understanding",
        _QUESTION_UNDERSTANDING_OUTPUT_SCHEMA,
    ),
    ENGINEERING_QUESTION_INITIAL_INVESTIGATION_OUTPUT_SCHEMA_REF: (
        "engineering_qa_initial_investigation",
        _INVESTIGATION_OUTPUT_SCHEMA,
    ),
    ENGINEERING_QUESTION_VERIFICATION_INVESTIGATION_OUTPUT_SCHEMA_REF: (
        "engineering_qa_verification_investigation",
        _INVESTIGATION_OUTPUT_SCHEMA,
    ),
    ENGINEERING_QUESTION_ANSWER_OUTPUT_SCHEMA_REF: (
        "engineering_qa_answer",
        _ANSWER_OUTPUT_SCHEMA,
    ),
    ENGINEERING_QUESTION_REVIEW_OUTPUT_SCHEMA_REF: (
        "engineering_qa_review",
        _REVIEW_OUTPUT_SCHEMA,
    ),
}

_OUTPUT_SCHEMA_REF_BY_ROLE = {
    EngineeringQuestionModelRole.QUESTION_UNDERSTANDING: (
        ENGINEERING_QUESTION_UNDERSTANDING_OUTPUT_SCHEMA_REF
    ),
    EngineeringQuestionModelRole.INITIAL_INVESTIGATION: (
        ENGINEERING_QUESTION_INITIAL_INVESTIGATION_OUTPUT_SCHEMA_REF
    ),
    EngineeringQuestionModelRole.VERIFICATION_INVESTIGATION: (
        ENGINEERING_QUESTION_VERIFICATION_INVESTIGATION_OUTPUT_SCHEMA_REF
    ),
    EngineeringQuestionModelRole.ANSWER: ENGINEERING_QUESTION_ANSWER_OUTPUT_SCHEMA_REF,
    EngineeringQuestionModelRole.REVIEW: ENGINEERING_QUESTION_REVIEW_OUTPUT_SCHEMA_REF,
}


def engineering_question_output_schemas() -> dict[str, OutputSchemaDefinition]:
    """Return fresh closed output contracts for all five independent roles."""

    return {
        schema_ref: OutputSchemaDefinition(name, deepcopy(schema))
        for schema_ref, (name, schema) in _OUTPUT_SCHEMA_BY_REF.items()
    }


def engineering_question_output_contract_digest() -> Digest:
    schemas = engineering_question_output_schemas()
    return digest_of(
        tuple(
            (schema_ref, schemas[schema_ref].schema)
            for schema_ref in sorted(schemas)
        )
    )


def engineering_question_output_schema_digest(
    output_schema_ref: str,
    output_schema: OutputSchemaDefinition,
) -> Digest:
    expected = engineering_question_output_schemas().get(output_schema_ref)
    if expected != output_schema:
        raise DomainError(
            ErrorCode.STRATEGY_CONTRACT_MISMATCH,
            "Engineering QA output schema definition is not current",
        )
    return digest_of(
        ["ENGINEERING_QA_OUTPUT_SCHEMA@1", output_schema_ref, output_schema.schema]
    )


@dataclass(frozen=True, slots=True)
class EngineeringQuestionRoleInputManifest:
    schema: str
    strategy_ref: str
    protocol: str
    role: EngineeringQuestionModelRole
    role_context_id: StableId
    request_digest: Digest
    authority_digests: tuple[Digest, ...]
    body: Mapping[str, object]
    external_disclosure_status: str
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        role: EngineeringQuestionModelRole,
        role_context_id: StableId,
        request_digest: Digest,
        authority_digests: Sequence[Digest],
        body: Mapping[str, object],
    ) -> "EngineeringQuestionRoleInputManifest":
        digests = tuple(authority_digests)
        if not digests:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "Engineering QA role input requires an authority digest closure",
            )
        core = {
            "schema": ENGINEERING_QUESTION_ROLE_INPUT_SCHEMA,
            "strategy_ref": ENGINEERING_QUESTION_STRATEGY_REF,
            "protocol": ENGINEERING_QA_PROTOCOL,
            "role": role.value,
            "role_context_id": role_context_id.value,
            "request_digest": request_digest.value,
            "authority_digests": tuple(item.value for item in digests),
            "body": body,
            "external_disclosure_status": "NOT_AUTHORIZED",
        }
        return cls(
            schema=ENGINEERING_QUESTION_ROLE_INPUT_SCHEMA,
            strategy_ref=ENGINEERING_QUESTION_STRATEGY_REF,
            protocol=ENGINEERING_QA_PROTOCOL,
            role=role,
            role_context_id=role_context_id,
            request_digest=request_digest,
            authority_digests=digests,
            body=cast(Mapping[str, object], _freeze(body)),
            external_disclosure_status="NOT_AUTHORIZED",
            digest=digest_of([ENGINEERING_QUESTION_ROLE_INPUT_SCHEMA, core]),
        )

    def gateway_input(self) -> dict[str, object]:
        """Return the closed semantic input, not a dispatch authorization."""

        self.require_valid()
        return {
            "schema": self.schema,
            "strategy_ref": self.strategy_ref,
            "protocol": self.protocol,
            "role": self.role.value,
            "role_context_id": self.role_context_id.value,
            "request_digest": self.request_digest.value,
            "authority_digests": [item.value for item in self.authority_digests],
            "input": _thaw(self.body),
            "external_disclosure_status": self.external_disclosure_status,
            "manifest_digest": self.digest.value,
        }

    def require_valid(self) -> None:
        expected = EngineeringQuestionRoleInputManifest.create(
            role=self.role,
            role_context_id=self.role_context_id,
            request_digest=self.request_digest,
            authority_digests=self.authority_digests,
            body=cast(Mapping[str, object], _thaw(self.body)),
        )
        if self != expected:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Engineering QA role input Manifest identity is invalid",
            )


@dataclass(frozen=True, slots=True)
class EngineeringQuestionRoleOutput:
    """An immutable structured-output receipt bound to one exact role input.

    The receipt says nothing about Provider eligibility or disclosure authority.
    Slice 1 only supplies deterministic output sources; a later model-backed
    source must independently satisfy the live-dispatch contract before it can
    create one of these receipts.
    """

    schema: str
    role: EngineeringQuestionModelRole
    role_context_id: StableId
    input_manifest_digest: Digest
    output_schema_ref: str
    output_schema_digest: Digest
    output_text: str
    output_text_digest: Digest
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        manifest: EngineeringQuestionRoleInputManifest,
        output_schema_ref: str,
        output_schema: OutputSchemaDefinition,
        output_text: str,
    ) -> "EngineeringQuestionRoleOutput":
        manifest.require_valid()
        expected_ref = _OUTPUT_SCHEMA_REF_BY_ROLE.get(manifest.role)
        if expected_ref != output_schema_ref:
            raise DomainError(
                ErrorCode.STRATEGY_CONTRACT_MISMATCH,
                "Engineering QA output schema does not match the input role",
            )
        expected_definition = engineering_question_output_schemas().get(
            output_schema_ref
        )
        if expected_definition != output_schema:
            raise DomainError(
                ErrorCode.STRATEGY_CONTRACT_MISMATCH,
                "Engineering QA output schema definition is not current",
            )
        if not isinstance(output_text, str) or not output_text:
            raise DomainError(
                ErrorCode.STRUCTURED_OUTPUT_INVALID,
                "Engineering QA role output must be non-empty JSON text",
            )
        if len(output_text.encode("utf-8")) > _MAXIMUM_ROLE_OUTPUT_BYTES:
            raise DomainError(
                ErrorCode.STRUCTURED_OUTPUT_INVALID,
                "Engineering QA role output exceeds its byte limit",
            )
        schema_digest = engineering_question_output_schema_digest(
            output_schema_ref, output_schema
        )
        text_digest = digest_of(["ENGINEERING_QA_OUTPUT_TEXT@1", output_text])
        core = {
            "schema": ENGINEERING_QUESTION_ROLE_OUTPUT_SCHEMA,
            "role": manifest.role.value,
            "role_context_id": manifest.role_context_id.value,
            "input_manifest_digest": manifest.digest.value,
            "output_schema_ref": output_schema_ref,
            "output_schema_digest": schema_digest.value,
            "output_text_digest": text_digest.value,
        }
        return cls(
            schema=ENGINEERING_QUESTION_ROLE_OUTPUT_SCHEMA,
            role=manifest.role,
            role_context_id=manifest.role_context_id,
            input_manifest_digest=manifest.digest,
            output_schema_ref=output_schema_ref,
            output_schema_digest=schema_digest,
            output_text=output_text,
            output_text_digest=text_digest,
            digest=digest_of([ENGINEERING_QUESTION_ROLE_OUTPUT_SCHEMA, core]),
        )

    def require_valid(
        self,
        *,
        manifest: EngineeringQuestionRoleInputManifest,
        output_schema_ref: str,
        output_schema: OutputSchemaDefinition,
    ) -> None:
        expected = EngineeringQuestionRoleOutput.create(
            manifest=manifest,
            output_schema_ref=output_schema_ref,
            output_schema=output_schema,
            output_text=self.output_text,
        )
        if self != expected:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Engineering QA role output is not bound to the current manifest and schema",
            )


class EngineeringQuestionStructuredOutputSource(Protocol):
    """Provide one output receipt; this port is not dispatch authorization."""

    def output_for(
        self,
        *,
        manifest: EngineeringQuestionRoleInputManifest,
        output_schema_ref: str,
        output_schema: OutputSchemaDefinition,
    ) -> EngineeringQuestionRoleOutput: ...


class EngineeringQuestionRoleInputBuilder:
    """Construct the only model-visible fields allowed for each role."""

    @staticmethod
    def question_understanding(
        *,
        request: EngineeringQuestionRequest,
        role_context_id: StableId,
    ) -> EngineeringQuestionRoleInputManifest:
        body = {
            "original_question": request.original_question,
            "response_language": request.response_language,
            "required_output_fields": [
                "preserved_original_question",
                "user_goal",
                "audience",
                "requested_abstraction_level",
                "material_conclusions",
                "evidence_needs",
                "response_language",
                "response_constraints",
            ],
        }
        return EngineeringQuestionRoleInputManifest.create(
            role=EngineeringQuestionModelRole.QUESTION_UNDERSTANDING,
            role_context_id=role_context_id,
            request_digest=request.digest,
            authority_digests=(request.digest,),
            body=body,
        )

    @staticmethod
    def initial_investigation(
        investigation_input: InitialInvestigationInput,
    ) -> EngineeringQuestionRoleInputManifest:
        return EngineeringQuestionRoleInputManifest.create(
            role=EngineeringQuestionModelRole.INITIAL_INVESTIGATION,
            role_context_id=investigation_input.role_context_id,
            request_digest=investigation_input.request.digest,
            authority_digests=(
                investigation_input.request.digest,
                investigation_input.understanding.digest,
                investigation_input.cognition.digest,
                investigation_input.ledger.prefix_digest,
            ),
            body=investigation_input.model_view(),
        )

    @staticmethod
    def verification_investigation(
        investigation_input: VerificationInvestigationInput,
    ) -> EngineeringQuestionRoleInputManifest:
        return EngineeringQuestionRoleInputManifest.create(
            role=EngineeringQuestionModelRole.VERIFICATION_INVESTIGATION,
            role_context_id=investigation_input.role_context_id,
            request_digest=investigation_input.current_package.request_digest,
            authority_digests=(
                investigation_input.verification_request.digest,
                investigation_input.current_package.digest,
                investigation_input.ledger.prefix_digest,
            ),
            body=investigation_input.model_view(),
        )

    @staticmethod
    def answer(
        *,
        original_question: str,
        understanding: QuestionUnderstanding,
        package: QuestionEvidencePackage,
        role_context_id: StableId,
        rewrite_findings: Sequence[EngineeringReviewFinding] = (),
    ) -> EngineeringQuestionRoleInputManifest:
        if (
            understanding.request_digest != package.request_digest
            or original_question != package.original_question
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Engineering QA Answer input crosses Request identities",
            )
        body = {
            "original_question": original_question,
            "question_understanding": understanding.model_view(),
            "question_evidence_package": package.model_view(),
            "rewrite_findings": [
                {
                    "finding_code": item.finding_code,
                    "checklist_item_id": item.checklist_item_id,
                    "claim_id": item.claim_id,
                    "description": item.description,
                    "digest": item.digest.value,
                }
                for item in rewrite_findings
            ],
            "response_rule": "CONCLUSION_FIRST_WITH_PACKAGE_ENTRY_CITATIONS",
        }
        digests = [understanding.digest, package.digest]
        digests.extend(item.digest for item in rewrite_findings)
        return EngineeringQuestionRoleInputManifest.create(
            role=EngineeringQuestionModelRole.ANSWER,
            role_context_id=role_context_id,
            request_digest=package.request_digest,
            authority_digests=digests,
            body=body,
        )

    @staticmethod
    def review(
        *,
        original_question: str,
        understanding: QuestionUnderstanding,
        package: QuestionEvidencePackage,
        draft: EngineeringAnswerDraft,
        role_context_id: StableId,
    ) -> EngineeringQuestionRoleInputManifest:
        if (
            understanding.request_digest != package.request_digest
            or original_question != package.original_question
            or draft.package_digest != package.digest
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Engineering QA Review input crosses Request or Package identities",
            )
        body = {
            "original_question": original_question,
            "question_understanding": understanding.model_view(),
            "question_evidence_package": package.model_view(),
            "draft": draft.model_view(),
            "review_dimensions": [
                "direct_answer",
                "abstraction_level",
                "correctness",
                "completeness",
                "relevance",
                "actionability",
                "claim_citations",
                "unknown_and_limitation",
            ],
            "verification_request_rule": (
                "BIND_CHECKLIST_OR_CLAIM_EVIDENCE_CLASS_AND_NEED_NO_OPERATION"
            ),
        }
        return EngineeringQuestionRoleInputManifest.create(
            role=EngineeringQuestionModelRole.REVIEW,
            role_context_id=role_context_id,
            request_digest=package.request_digest,
            authority_digests=(understanding.digest, package.digest, draft.digest),
            body=body,
        )


class _StructuredRoleAdapter:
    def __init__(
        self, output_source: EngineeringQuestionStructuredOutputSource
    ) -> None:
        self._output_source = output_source

    def _output(
        self,
        manifest: EngineeringQuestionRoleInputManifest,
    ) -> dict[str, object]:
        schema_ref = _OUTPUT_SCHEMA_REF_BY_ROLE[manifest.role]
        schema = engineering_question_output_schemas()[schema_ref]
        output = self._output_source.output_for(
            manifest=manifest,
            output_schema_ref=schema_ref,
            output_schema=schema,
        )
        if not isinstance(output, EngineeringQuestionRoleOutput):
            raise DomainError(
                ErrorCode.STRUCTURED_OUTPUT_INVALID,
                "Engineering QA output source returned no role-output receipt",
            )
        output.require_valid(
            manifest=manifest,
            output_schema_ref=schema_ref,
            output_schema=schema,
        )
        try:
            decoded = json.loads(output.output_text, object_pairs_hook=_unique_object)
        except (json.JSONDecodeError, ValueError) as exc:
            raise DomainError(
                ErrorCode.STRUCTURED_OUTPUT_INVALID,
                "Engineering QA role output is not unique-key JSON",
            ) from exc
        if not isinstance(decoded, dict):
            raise DomainError(
                ErrorCode.STRUCTURED_OUTPUT_INVALID,
                "Engineering QA role output root must be an object",
            )
        schema.validate_output_text(output.output_text)
        return decoded


class StructuredQuestionUnderstandingRole(_StructuredRoleAdapter):
    """Decode one closed understanding output into an untrusted Proposal."""

    def understand(
        self,
        *,
        request: EngineeringQuestionRequest,
        role_context_id: StableId,
    ) -> QuestionUnderstandingProposal:
        manifest = EngineeringQuestionRoleInputBuilder.question_understanding(
            request=request,
            role_context_id=role_context_id,
        )
        value = self._output(manifest)
        try:
            return QuestionUnderstandingProposal.create(
                role_context_id=role_context_id,
                request_digest=request.digest,
                preserved_original_question=cast(
                    str, value["preserved_original_question"]
                ),
                user_goal=cast(str, value["user_goal"]),
                audience=cast(str, value["audience"]),
                requested_abstraction_level=cast(
                    str, value["requested_abstraction_level"]
                ),
                material_conclusions=cast(
                    Sequence[str], value["material_conclusions"]
                ),
                evidence_needs=cast(Sequence[str], value["evidence_needs"]),
                response_language=cast(str, value["response_language"]),
                response_constraints=cast(
                    Sequence[str], value["response_constraints"]
                ),
            )
        except (DomainError, TypeError, ValueError) as exc:
            _raise_output_contract_error(
                "question understanding", exc
            )


class StructuredInitialInvestigationRole(_StructuredRoleAdapter):
    """Bind semantic initial-investigation output to trusted Ledger coordinates."""

    def propose(
        self, investigation_input: InitialInvestigationInput
    ) -> InvestigationStepProposal:
        manifest = EngineeringQuestionRoleInputBuilder.initial_investigation(
            investigation_input
        )
        return _investigation_proposal(
            value=self._output(manifest),
            investigation_kind=InvestigationKind.INITIAL,
            investigation_input=investigation_input,
        )


class StructuredVerificationInvestigationRole(_StructuredRoleAdapter):
    """Bind gap-scoped output to a fresh verification context and Ledger prefix."""

    def propose(
        self, investigation_input: VerificationInvestigationInput
    ) -> InvestigationStepProposal:
        manifest = EngineeringQuestionRoleInputBuilder.verification_investigation(
            investigation_input
        )
        return _investigation_proposal(
            value=self._output(manifest),
            investigation_kind=InvestigationKind.VERIFICATION,
            investigation_input=investigation_input,
        )


class StructuredEngineeringAnswerRole(_StructuredRoleAdapter):
    """Decode Package-only answer output into claim-level Proposal objects."""

    def generate(
        self,
        *,
        original_question: str,
        understanding: QuestionUnderstanding,
        package: QuestionEvidencePackage,
        role_context_id: StableId,
        rewrite_findings: tuple[EngineeringReviewFinding, ...] = (),
    ) -> EngineeringAnswerProposal:
        manifest = EngineeringQuestionRoleInputBuilder.answer(
            original_question=original_question,
            understanding=understanding,
            package=package,
            role_context_id=role_context_id,
            rewrite_findings=rewrite_findings,
        )
        value = self._output(manifest)
        try:
            claims = tuple(
                EngineeringAnswerClaimProposal.create(
                    claim_id=cast(str, item["claim_id"]),
                    kind=AnswerClaimKind(cast(str, item["kind"])),
                    text=cast(str, item["text"]),
                    evidence_entry_ids=tuple(
                        StableId(reference)
                        for reference in cast(
                            Sequence[str], item["evidence_entry_ids"]
                        )
                    ),
                )
                for item in cast(Sequence[Mapping[str, object]], value["claims"])
            )
            return EngineeringAnswerProposal.create(
                role_context_id=role_context_id,
                package_digest=package.digest,
                response_language=cast(str, value["response_language"]),
                claims=claims,
            )
        except (DomainError, KeyError, TypeError, ValueError) as exc:
            _raise_output_contract_error("answer", exc)


class StructuredEngineeringAnswerReviewerRole(_StructuredRoleAdapter):
    """Decode a Package-and-Draft-only independent Review Proposal."""

    def review(
        self,
        *,
        original_question: str,
        understanding: QuestionUnderstanding,
        package: QuestionEvidencePackage,
        draft: EngineeringAnswerDraft,
        role_context_id: StableId,
    ) -> EngineeringReviewProposal:
        manifest = EngineeringQuestionRoleInputBuilder.review(
            original_question=original_question,
            understanding=understanding,
            package=package,
            draft=draft,
            role_context_id=role_context_id,
        )
        value = self._output(manifest)
        try:
            findings = tuple(
                EngineeringReviewFinding.create(
                    finding_code=cast(str, item["finding_code"]),
                    checklist_item_id=cast(str | None, item["checklist_item_id"]),
                    claim_id=cast(str | None, item["claim_id"]),
                    description=cast(str, item["description"]),
                )
                for item in cast(Sequence[Mapping[str, object]], value["findings"])
            )
            request_value = value["verification_request"]
            verification_request = None
            if request_value is not None:
                request_body = cast(Mapping[str, object], request_value)
                verification_request = VerificationRequestProposal.create(
                    package_digest=package.digest,
                    checklist_item_id=cast(
                        str, request_body["checklist_item_id"]
                    ),
                    claim_id=cast(str | None, request_body["claim_id"]),
                    evidence_class=EngineeringEvidenceClass(
                        cast(str, request_body["evidence_class"])
                    ),
                    evidence_need=cast(str, request_body["evidence_need"]),
                )
            return EngineeringReviewProposal.create(
                role_context_id=role_context_id,
                package_digest=package.digest,
                draft_digest=draft.digest,
                decision=EngineeringReviewDecision(cast(str, value["decision"])),
                findings=findings,
                verification_request=verification_request,
            )
        except (DomainError, KeyError, TypeError, ValueError) as exc:
            _raise_output_contract_error("review", exc)


@dataclass(frozen=True, slots=True)
class EngineeringQuestionStructuredStrategyBundle:
    """Five independent role instances over one receipt-producing boundary."""

    output_contract_digest: Digest
    question_understanding: QuestionUnderstandingRole
    initial_investigation: InitialInvestigationRole
    verification_investigation: VerificationInvestigationRole
    answer: EngineeringAnswerRole
    reviewer: EngineeringAnswerReviewerRole

    @classmethod
    def create(
        cls,
        output_source: EngineeringQuestionStructuredOutputSource,
    ) -> "EngineeringQuestionStructuredStrategyBundle":
        roles = (
            StructuredQuestionUnderstandingRole(output_source),
            StructuredInitialInvestigationRole(output_source),
            StructuredVerificationInvestigationRole(output_source),
            StructuredEngineeringAnswerRole(output_source),
            StructuredEngineeringAnswerReviewerRole(output_source),
        )
        return cls(
            output_contract_digest=engineering_question_output_contract_digest(),
            question_understanding=roles[0],
            initial_investigation=roles[1],
            verification_investigation=roles[2],
            answer=roles[3],
            reviewer=roles[4],
        )


def _investigation_proposal(
    *,
    value: Mapping[str, object],
    investigation_kind: InvestigationKind,
    investigation_input: InitialInvestigationInput | VerificationInvestigationInput,
) -> InvestigationStepProposal:
    try:
        dispositions = tuple(
            ChecklistDisposition.create(
                checklist_item_id=cast(str, item["checklist_item_id"]),
                outcome=ChecklistOutcome(cast(str, item["outcome"])),
                evidence_references=cast(
                    Sequence[str], item["evidence_references"]
                ),
                explanation=cast(str, item["explanation"]),
            )
            for item in cast(
                Sequence[Mapping[str, object]], value["finish_dispositions"]
            )
        )
        evidence_class_value = cast(str | None, value["evidence_class"])
        locator_value = cast(str | None, value["locator_reference"])
        ledger = investigation_input.ledger
        request_digest = (
            investigation_input.request.digest
            if isinstance(investigation_input, InitialInvestigationInput)
            else investigation_input.current_package.request_digest
        )
        return InvestigationStepProposal.create(
            investigation_kind=investigation_kind,
            attempt_id=investigation_input.attempt_id,
            role_context_id=investigation_input.role_context_id,
            request_digest=request_digest,
            step_index=investigation_input.step_index,
            ledger_id=ledger.ledger_id,
            ledger_generation=ledger.generation,
            ledger_revision=len(ledger.entries),
            ledger_prefix_digest=ledger.prefix_digest,
            operation=InvestigationOperation(cast(str, value["operation"])),
            checklist_item_ids=cast(
                Sequence[str], value["checklist_item_ids"]
            ),
            evidence_class=(
                EngineeringEvidenceClass(evidence_class_value)
                if evidence_class_value is not None
                else None
            ),
            query=cast(str | None, value["query"]),
            locator_reference=(StableId(locator_value) if locator_value else None),
            basis_entry_ids=tuple(
                StableId(item)
                for item in cast(Sequence[str], value["basis_entry_ids"])
            ),
            unknown_to_reduce=cast(str, value["unknown_to_reduce"]),
            finish_dispositions=dispositions,
        )
    except (DomainError, KeyError, TypeError, ValueError) as exc:
        _raise_output_contract_error(
            f"{investigation_kind.value.casefold()} investigation", exc
        )


def _raise_output_contract_error(stage: str, exc: Exception) -> NoReturn:
    if isinstance(exc, DomainError):
        if exc.code in {
            ErrorCode.STRUCTURED_OUTPUT_INVALID,
            ErrorCode.PROVIDER_OUTPUT_FORBIDDEN,
        }:
            raise exc
        cause_code = exc.code.value
    else:
        cause_code = exc.__class__.__name__
    raise DomainError(
        ErrorCode.STRUCTURED_OUTPUT_INVALID,
        f"Engineering QA {stage} output violates the domain contract",
        {"cause_code": cause_code},
    ) from exc


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


__all__ = [
    "ENGINEERING_QUESTION_ROLE_INPUT_SCHEMA",
    "ENGINEERING_QUESTION_ROLE_OUTPUT_SCHEMA",
    "ENGINEERING_QUESTION_STRATEGY_REF",
    "ENGINEERING_QUESTION_ANSWER_OUTPUT_SCHEMA_REF",
    "ENGINEERING_QUESTION_INITIAL_INVESTIGATION_OUTPUT_SCHEMA_REF",
    "ENGINEERING_QUESTION_REVIEW_OUTPUT_SCHEMA_REF",
    "ENGINEERING_QUESTION_UNDERSTANDING_OUTPUT_SCHEMA_REF",
    "ENGINEERING_QUESTION_VERIFICATION_INVESTIGATION_OUTPUT_SCHEMA_REF",
    "EngineeringQuestionModelRole",
    "EngineeringQuestionRoleInputBuilder",
    "EngineeringQuestionRoleInputManifest",
    "EngineeringQuestionRoleOutput",
    "EngineeringQuestionStructuredOutputSource",
    "EngineeringQuestionStructuredStrategyBundle",
    "StructuredEngineeringAnswerReviewerRole",
    "StructuredEngineeringAnswerRole",
    "StructuredInitialInvestigationRole",
    "StructuredQuestionUnderstandingRole",
    "StructuredVerificationInvestigationRole",
    "engineering_question_output_contract_digest",
    "engineering_question_output_schemas",
]
