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
    AnswerContentRole,
    AnswerDetailLevel,
    AnswerClaimKind,
    ChecklistDisposition,
    ChecklistOutcome,
    ENGINEERING_QA_PROTOCOL,
    EngineeringAnswerClaimProposal,
    EngineeringAnswerDraft,
    EngineeringAnswerProposal,
    EngineeringAnswerRole,
    EngineeringAnswerReviewerRole,
    EngineeringEvidenceBoundaryAssessment,
    EngineeringEvidenceBoundaryAssessmentDisposition,
    EngineeringEvidenceBoundaryChallengeKind,
    EngineeringEvidenceClass,
    EngineeringMaterialEffectOmissionLayer,
    EngineeringQuestionRequest,
    EngineeringReviewChecklistAssessment,
    EngineeringReviewMaterialObservation,
    EngineeringReviewFinding,
    EngineeringReviewFocus,
    EngineeringReviewProposal,
    EngineeringReviewQualityAssessment,
    EngineeringReviewQualityStatus,
    EngineeringReviewRemediation,
    InitialInvestigationInput,
    InitialInvestigationRole,
    InvestigationKind,
    InvestigationOperation,
    InvestigationStepProposal,
    MAXIMUM_MATERIAL_OBSERVATIONS_PER_DISPOSITION,
    MAXIMUM_REQUIRED_EVIDENCE_PATHS,
    MaterialObservation,
    MaterialObservationKind,
    PackageBoundaryKind,
    QuestionEvidencePackage,
    QuestionUnderstanding,
    QuestionUnderstandingProposal,
    QuestionUnderstandingRole,
    VerificationInvestigationInput,
    VerificationInvestigationRole,
    project_evidence_boundary_challenges,
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
ENGINEERING_QUESTION_STRATEGY_REF = "engineering-qa-adaptive-investigation-local-contract@26"

ENGINEERING_QUESTION_UNDERSTANDING_OUTPUT_SCHEMA_REF = (
    "engineering-qa-question-understanding@4"
)
ENGINEERING_QUESTION_INITIAL_INVESTIGATION_OUTPUT_SCHEMA_REF = (
    "engineering-qa-initial-investigation@10"
)
ENGINEERING_QUESTION_VERIFICATION_INVESTIGATION_OUTPUT_SCHEMA_REF = (
    "engineering-qa-verification-investigation@10"
)
ENGINEERING_QUESTION_ANSWER_OUTPUT_SCHEMA_REF = "engineering-qa-answer@5"
ENGINEERING_QUESTION_REVIEW_OUTPUT_SCHEMA_REF = "engineering-qa-review@9"

_MAXIMUM_ROLE_OUTPUT_BYTES = 1_048_576

_ANSWER_CONTENT_ROLE_ORDINAL = {
    role: ordinal for ordinal, role in enumerate(AnswerContentRole)
}


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


def _verified_gap_outcomes(
    package: QuestionEvidencePackage,
) -> list[dict[str, object]]:
    gap_entries = {
        item.source_reference: item
        for item in package.boundary_audit
        if item.kind is PackageBoundaryKind.VERIFICATION_GAP
    }
    outcomes: list[dict[str, object]] = []
    for disposition in package.checklist_dispositions:
        if disposition.outcome is ChecklistOutcome.SUPPORTED:
            continue
        retained_gap_references = tuple(
            reference
            for reference in disposition.evidence_references
            if reference in gap_entries
        )
        if not retained_gap_references:
            continue
        outcomes.append(
            {
                "checklist_item_id": disposition.checklist_item_id,
                "outcome": disposition.outcome.value,
                "explanation": disposition.explanation,
                "gap_boundary_entry_ids": [
                    gap_entries[reference].entry_id.value
                    for reference in retained_gap_references
                ],
                "terminal_under_current_authorization": True,
            }
        )
    return outcomes


def _evidence_boundary_challenges(
    package: QuestionEvidencePackage,
    draft: EngineeringAnswerDraft,
) -> list[dict[str, object]]:
    views: list[dict[str, object]] = []
    for challenge in project_evidence_boundary_challenges(package, draft):
        view = challenge.model_view()
        if (
            challenge.kind
            is EngineeringEvidenceBoundaryChallengeKind.FULL_CONTENT_MATERIAL_EFFECT_SCAN
        ):
            entry_id = challenge.package_entry_ids[0]
            view["application_material_observations_for_entry"] = [
                observation.model_view()
                for observation in package.material_observations_for_support_entry(
                    entry_id
                )
            ]
            view["material_effect_omission_layer_contract"] = {
                EngineeringMaterialEffectOmissionLayer.APPLICATION_PACKAGE.value: (
                    "effect is absent from the projected exact Application observations; "
                    "return only absent effects and use INVESTIGATE_MISSING_EVIDENCE"
                ),
                EngineeringMaterialEffectOmissionLayer.DEFAULT_DRAFT.value: (
                    "effect exactly exists in the projected Application observations but "
                    "is absent from the default Draft; use REWRITE_WITH_EXISTING_EVIDENCE"
                ),
            }
            view["material_effect_omission_layer_precedence"] = {
                "empty_projection_with_nonempty_omission": (
                    EngineeringMaterialEffectOmissionLayer.APPLICATION_PACKAGE.value
                ),
                "any_effect_absent_from_projection": (
                    "RETURN_ONLY_ABSENT_EFFECTS_AS_APPLICATION_PACKAGE"
                ),
                "all_omitted_effects_present_in_projection": (
                    "RETURN_EXACT_PROJECTED_EFFECTS_AS_DEFAULT_DRAFT"
                ),
            }
        views.append(view)
    return views


class EngineeringQuestionModelRole(str, Enum):
    QUESTION_UNDERSTANDING = "QUESTION_UNDERSTANDING"
    INITIAL_INVESTIGATION = "INITIAL_INVESTIGATION"
    VERIFICATION_INVESTIGATION = "VERIFICATION_INVESTIGATION"
    ANSWER = "ANSWER"
    REVIEW = "REVIEW"


_NULLABLE_STRING_SCHEMA = {"type": ["string", "null"]}
_STRING_ARRAY_SCHEMA = {"type": "array", "items": {"type": "string"}}
_UNIQUE_STRING_ARRAY_SCHEMA = {
    "type": "array",
    "items": {"type": "string"},
    "uniqueItems": True,
}
_NONEMPTY_UNIQUE_STRING_ARRAY_SCHEMA = {
    "type": "array",
    "items": {"type": "string"},
    "minItems": 1,
    "uniqueItems": True,
}
_INVESTIGATION_CHECKLIST_IDS_SCHEMA = {
    **_NONEMPTY_UNIQUE_STRING_ARRAY_SCHEMA,
    "description": (
        "One or more unique checklist_item_id values from the current role input "
        "that this action reduces or dispositions."
    ),
}
_INVESTIGATION_BASIS_ENTRY_IDS_SCHEMA = {
    **_NONEMPTY_UNIQUE_STRING_ARRAY_SCHEMA,
    "description": (
        "One or more unique current Ledger entry IDs, including the exact "
        "required_basis_entry_id."
    ),
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
_SUPPORTED_MATERIAL_OBSERVATION_SCHEMA = {
    "type": "object",
    "properties": {
        "kind": {
            "type": "string",
            "enum": [
                MaterialObservationKind.PROCESS_STAGE.value,
                MaterialObservationKind.OUTCOME.value,
                MaterialObservationKind.STATE_CHANGE.value,
                MaterialObservationKind.SIDE_EFFECT.value,
            ],
        },
        "statement": {"type": "string"},
        "evidence_references": _NONEMPTY_UNIQUE_STRING_ARRAY_SCHEMA,
    },
    "required": ["kind", "statement", "evidence_references"],
    "additionalProperties": False,
}
_LIMITATION_MATERIAL_OBSERVATION_SCHEMA = {
    "type": "object",
    "properties": {
        "kind": {
            "type": "string",
            "enum": [MaterialObservationKind.LIMITATION.value],
        },
        "statement": {"type": "string"},
        "evidence_references": _NONEMPTY_UNIQUE_STRING_ARRAY_SCHEMA,
    },
    "required": ["kind", "statement", "evidence_references"],
    "additionalProperties": False,
}


def _finish_disposition_variant(
    *,
    outcomes: Sequence[ChecklistOutcome],
    observation_schema: Mapping[str, object],
) -> dict[str, object]:
    return {
        "type": "object",
        "properties": {
            "checklist_item_id": {"type": "string"},
            "outcome": {
                "type": "string",
                "enum": [item.value for item in outcomes],
            },
            "explanation": {"type": "string"},
            "material_observations": {
                "type": "array",
                "items": observation_schema,
                "minItems": 1,
                "maxItems": MAXIMUM_MATERIAL_OBSERVATIONS_PER_DISPOSITION,
            },
        },
        "required": [
            "checklist_item_id",
            "outcome",
            "explanation",
            "material_observations",
        ],
        "additionalProperties": False,
    }


_SUPPORTED_FINISH_DISPOSITION_SCHEMA = _finish_disposition_variant(
    outcomes=(ChecklistOutcome.SUPPORTED,),
    observation_schema=_SUPPORTED_MATERIAL_OBSERVATION_SCHEMA,
)
_NON_SUPPORTED_FINISH_DISPOSITION_SCHEMA = _finish_disposition_variant(
    outcomes=(
        ChecklistOutcome.UNKNOWN,
        ChecklistOutcome.CONFLICT,
        ChecklistOutcome.FAILED,
    ),
    observation_schema=_LIMITATION_MATERIAL_OBSERVATION_SCHEMA,
)
_INVESTIGATION_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "operation": {
            "type": "string",
            "enum": [item.value for item in InvestigationOperation],
        },
        "checklist_item_ids": _INVESTIGATION_CHECKLIST_IDS_SCHEMA,
        "evidence_class": _EVIDENCE_CLASS_SCHEMA,
        "query": _NULLABLE_STRING_SCHEMA,
        "locator_reference": _NULLABLE_STRING_SCHEMA,
        "basis_entry_ids": _INVESTIGATION_BASIS_ENTRY_IDS_SCHEMA,
        "unknown_to_reduce": {"type": "string"},
        "finish_dispositions": {
            "type": "array",
            "description": (
                "The only FINISH disposition list. Each item in this role input's "
                "authorized checklist scope appears exactly once. Initial scope is "
                "the complete Question Checklist; Verification scope is its one "
                "requested gap. The outcome-tagged variant mechanically selects "
                "affirmative or limitation observations; parent evidence references "
                "are derived from child observations by the trusted adapter."
            ),
            "items": {
                "anyOf": [
                    _SUPPORTED_FINISH_DISPOSITION_SCHEMA,
                    _NON_SUPPORTED_FINISH_DISPOSITION_SCHEMA,
                ]
            },
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
        "requested_abstraction_level": {
            "type": "string",
            "enum": [item.value for item in AnswerDetailLevel],
        },
        "material_conclusions": _STRING_ARRAY_SCHEMA,
        "evidence_needs": _STRING_ARRAY_SCHEMA,
        "required_evidence_classes": {
            "type": "array",
            "items": _REQUIRED_EVIDENCE_CLASS_SCHEMA,
            "minItems": 1,
            "maxItems": 4,
            "uniqueItems": True,
        },
        "required_evidence_paths": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1,
            "maxItems": MAXIMUM_REQUIRED_EVIDENCE_PATHS,
            "uniqueItems": True,
        },
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
        "required_evidence_classes",
        "required_evidence_paths",
        "response_language",
        "response_constraints",
    ],
    "additionalProperties": False,
}
def _answer_claim_variant(
    *,
    kind: AnswerClaimKind,
    content_roles: Sequence[AnswerContentRole],
) -> dict[str, object]:
    return {
        "type": "object",
        "properties": {
            "claim_id": {"type": "string"},
            "kind": {"type": "string", "enum": [kind.value]},
            "content_role": {
                "type": "string",
                "enum": [item.value for item in content_roles],
            },
            "checklist_item_ids": _NONEMPTY_UNIQUE_STRING_ARRAY_SCHEMA,
            "material_observation_ids": _UNIQUE_STRING_ARRAY_SCHEMA,
            "text": {"type": "string"},
            "evidence_entry_ids": _NONEMPTY_UNIQUE_STRING_ARRAY_SCHEMA,
        },
        "required": [
            "claim_id",
            "kind",
            "content_role",
            "checklist_item_ids",
            "material_observation_ids",
            "text",
            "evidence_entry_ids",
        ],
        "additionalProperties": False,
    }


_ANSWER_DIRECT_CLAIM_SCHEMA = {
    "anyOf": [
        _answer_claim_variant(
            kind=AnswerClaimKind.AFFIRMATIVE,
            content_roles=(AnswerContentRole.DIRECT_ANSWER,),
        ),
        _answer_claim_variant(
            kind=AnswerClaimKind.LIMITATION,
            content_roles=(AnswerContentRole.DIRECT_ANSWER,),
        ),
    ]
}
_ANSWER_FOLLOWUP_CLAIM_SCHEMA = {
    "anyOf": [
        _answer_claim_variant(
            kind=AnswerClaimKind.AFFIRMATIVE,
            content_roles=(
                AnswerContentRole.USER_VISIBLE_PROCESS,
                AnswerContentRole.IMPACT_OR_SIDE_EFFECT,
                AnswerContentRole.IMPLEMENTATION_EVIDENCE,
            ),
        ),
        _answer_claim_variant(
            kind=AnswerClaimKind.LIMITATION,
            content_roles=(AnswerContentRole.LIMITATION,),
        ),
    ]
}
_ANSWER_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "response_language": {"type": "string"},
        "direct_answer": _ANSWER_DIRECT_CLAIM_SCHEMA,
        "claims": {
            "type": "array",
            "items": _ANSWER_FOLLOWUP_CLAIM_SCHEMA,
            "minItems": 0,
            "maxItems": 63,
        },
    },
    "required": ["response_language", "direct_answer", "claims"],
    "additionalProperties": False,
}
_EMPTY_UNIQUE_STRING_ARRAY_SCHEMA = {
    "type": "array",
    "items": {"type": "string"},
    "maxItems": 0,
    "uniqueItems": True,
}
_NULL_EVIDENCE_CLASS_SCHEMA = {"type": ["string", "null"], "enum": [None]}
_NULL_STRING_SCHEMA = {"type": ["string", "null"], "enum": [None]}


def _review_finding_variant(
    *,
    remediation: EngineeringReviewRemediation,
    checklist_item_schema: Mapping[str, object],
    existing_evidence_schema: Mapping[str, object],
    evidence_class_schema: Mapping[str, object],
    evidence_need_schema: Mapping[str, object],
) -> dict[str, object]:
    return {
        "type": "object",
        "properties": {
            "finding_code": {"type": "string"},
            "checklist_item_id": checklist_item_schema,
            "claim_id": _NULLABLE_STRING_SCHEMA,
            "description": {"type": "string"},
            "remediation": {
                "type": "string",
                "enum": [remediation.value],
            },
            "existing_evidence_entry_ids": existing_evidence_schema,
            "evidence_class": evidence_class_schema,
            "evidence_need": evidence_need_schema,
        },
        "required": [
            "finding_code",
            "checklist_item_id",
            "claim_id",
            "description",
            "remediation",
            "existing_evidence_entry_ids",
            "evidence_class",
            "evidence_need",
        ],
        "additionalProperties": False,
    }


_REVIEW_FINDING_SCHEMA = {
    "anyOf": [
        _review_finding_variant(
            remediation=(
                EngineeringReviewRemediation.REWRITE_WITH_EXISTING_EVIDENCE
            ),
            checklist_item_schema=_NULLABLE_STRING_SCHEMA,
            existing_evidence_schema=_NONEMPTY_UNIQUE_STRING_ARRAY_SCHEMA,
            evidence_class_schema=_NULL_EVIDENCE_CLASS_SCHEMA,
            evidence_need_schema=_NULL_STRING_SCHEMA,
        ),
        _review_finding_variant(
            remediation=(
                EngineeringReviewRemediation.INVESTIGATE_MISSING_EVIDENCE
            ),
            checklist_item_schema={"type": "string"},
            existing_evidence_schema=_EMPTY_UNIQUE_STRING_ARRAY_SCHEMA,
            evidence_class_schema=_REQUIRED_EVIDENCE_CLASS_SCHEMA,
            evidence_need_schema={"type": "string"},
        ),
        _review_finding_variant(
            remediation=EngineeringReviewRemediation.REJECT_UNRECOVERABLE,
            checklist_item_schema=_NULLABLE_STRING_SCHEMA,
            existing_evidence_schema=_EMPTY_UNIQUE_STRING_ARRAY_SCHEMA,
            evidence_class_schema=_NULL_EVIDENCE_CLASS_SCHEMA,
            evidence_need_schema=_NULL_STRING_SCHEMA,
        ),
    ]
}
_REVIEW_QUALITY_ASSESSMENT_SCHEMA = {
    "type": "object",
    "properties": {
        field: {
            "type": "string",
            "enum": [item.value for item in EngineeringReviewQualityStatus],
        }
        for field in (
            "direct_answer",
            "abstraction_fit",
            "material_completeness",
            "claim_consistency",
            "implementation_detail_budget",
        )
    },
    "required": [
        "direct_answer",
        "abstraction_fit",
        "material_completeness",
        "claim_consistency",
        "implementation_detail_budget",
    ],
    "additionalProperties": False,
}
_REVIEW_CHECKLIST_ASSESSMENT_SCHEMA = {
    "type": "object",
    "properties": {
        "independent_material_conclusions": _NONEMPTY_UNIQUE_STRING_ARRAY_SCHEMA,
        "application_checklist_omissions": {
            "type": "array",
            "items": {"type": "string"},
            "uniqueItems": True,
        },
        "independent_material_observations": {
            "type": "array",
            "minItems": 1,
            "maxItems": 64,
            "items": {
                "type": "object",
                "properties": {
                    "checklist_item_id": {"type": "string"},
                    "kind": {
                        "type": "string",
                        "enum": [
                            item.value for item in MaterialObservationKind
                        ],
                    },
                    "statement": {"type": "string"},
                    "evidence_entry_ids": (
                        _NONEMPTY_UNIQUE_STRING_ARRAY_SCHEMA
                    ),
                },
                "required": [
                    "checklist_item_id",
                    "kind",
                    "statement",
                    "evidence_entry_ids",
                ],
                "additionalProperties": False,
            },
        },
        "application_material_observation_omissions": {
            "type": "array",
            "items": {"type": "string"},
            "uniqueItems": True,
        },
        "draft_material_observation_omissions": {
            "type": "array",
            "items": {"type": "string"},
            "uniqueItems": True,
        },
    },
    "required": [
        "independent_material_conclusions",
        "application_checklist_omissions",
        "independent_material_observations",
        "application_material_observation_omissions",
        "draft_material_observation_omissions",
    ],
    "additionalProperties": False,
}
_REVIEW_EVIDENCE_BOUNDARY_ASSESSMENT_SCHEMA = {
    "anyOf": [
        {
            "type": "object",
            "properties": {
                "challenge_id": {"type": "string"},
                "evidence_boundary": {"type": "string"},
                "draft_scope": {"type": "string"},
                "disposition": {
                    "type": "string",
                    "enum": [
                        EngineeringEvidenceBoundaryAssessmentDisposition.WITHIN_EVIDENCE_BOUNDARY.value
                    ],
                },
                "finding_code": _NULL_STRING_SCHEMA,
            },
            "required": [
                "challenge_id",
                "evidence_boundary",
                "draft_scope",
                "disposition",
                "finding_code",
            ],
            "additionalProperties": False,
        },
        {
            "type": "object",
            "properties": {
                "challenge_id": {"type": "string"},
                "evidence_boundary": {"type": "string"},
                "draft_scope": {"type": "string"},
                "disposition": {
                    "type": "string",
                    "enum": [
                        EngineeringEvidenceBoundaryAssessmentDisposition.DRAFT_EXCEEDS_EVIDENCE_BOUNDARY.value
                    ],
                },
                "finding_code": {"type": "string"},
            },
            "required": [
                "challenge_id",
                "evidence_boundary",
                "draft_scope",
                "disposition",
                "finding_code",
            ],
            "additionalProperties": False,
        },
        {
            "type": "object",
            "properties": {
                "challenge_id": {"type": "string"},
                "evidence_boundary": {"type": "string"},
                "draft_scope": {"type": "string"},
                "disposition": {
                    "type": "string",
                    "enum": [
                        EngineeringEvidenceBoundaryAssessmentDisposition.DRAFT_OMITS_MATERIAL_EFFECT.value
                    ],
                },
                "finding_code": {"type": "string"},
                "material_effect_omission_layer": {
                    "type": "string",
                    "enum": [
                        item.value
                        for item in EngineeringMaterialEffectOmissionLayer
                    ],
                },
                "omitted_material_effect_statements": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 1,
                    "maxItems": 16,
                    "uniqueItems": True,
                },
            },
            "required": [
                "challenge_id",
                "evidence_boundary",
                "draft_scope",
                "disposition",
                "finding_code",
                "material_effect_omission_layer",
                "omitted_material_effect_statements",
            ],
            "additionalProperties": False,
        },
        {
            "type": "object",
            "properties": {
                "challenge_id": {"type": "string"},
                "evidence_boundary": {"type": "string"},
                "draft_scope": {"type": "string"},
                "disposition": {
                    "type": "string",
                    "enum": [
                        EngineeringEvidenceBoundaryAssessmentDisposition.DRAFT_OMITS_MATERIAL_REQUIREMENT.value
                    ],
                },
                "finding_code": {"type": "string"},
            },
            "required": [
                "challenge_id",
                "evidence_boundary",
                "draft_scope",
                "disposition",
                "finding_code",
            ],
            "additionalProperties": False,
        },
    ]
}
_REVIEW_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "quality_assessment": _REVIEW_QUALITY_ASSESSMENT_SCHEMA,
        "checklist_assessment": _REVIEW_CHECKLIST_ASSESSMENT_SCHEMA,
        "evidence_boundary_assessments": {
            "type": "array",
            "items": _REVIEW_EVIDENCE_BOUNDARY_ASSESSMENT_SCHEMA,
            "maxItems": 64,
            "uniqueItems": True,
        },
        "findings": {
            "type": "array",
            "items": _REVIEW_FINDING_SCHEMA,
            "maxItems": 64,
        },
    },
    "required": [
        "quality_assessment",
        "checklist_assessment",
        "evidence_boundary_assessments",
        "findings",
    ],
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
                "required_evidence_classes",
                "required_evidence_paths",
                "response_language",
                "response_constraints",
            ],
            "authorized_evidence_paths": list(request.source_allowlist),
            "required_evidence_path_policy": (
                "ONE_TO_FOUR_EXACT_AUTHORIZED_PATHS_WHOSE_FULL_CONTENT_IS_"
                "INDISPENSABLE_BEFORE_FINISH"
            ),
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
        support_by_source = {
            item.source_reference: item.entry_id
            for item in package.support_citation
        }
        boundary_by_source = {
            item.source_reference: item.entry_id
            for item in package.boundary_audit
        }
        observation_contract = tuple(
            {
                "observation_id": observation.observation_id.value,
                "checklist_item_id": observation.checklist_item_id,
                "kind": observation.kind.value,
                "statement": observation.statement,
                "required_evidence_entry_ids": [
                    (
                        support_by_source
                        if disposition.outcome is ChecklistOutcome.SUPPORTED
                        else boundary_by_source
                    )[reference].value
                    for reference in observation.evidence_references
                ],
            }
            for disposition in package.checklist_dispositions
            for observation in disposition.material_observations
        )
        body = {
            "original_question": original_question,
            "material_observation_coverage_contract": {
                "rewrite_mode": bool(rewrite_findings),
                "required_exact_observation_ids": [
                    item["observation_id"] for item in observation_contract
                ],
                "observations": observation_contract,
                "each_observation_covered_exactly_once_in_default_body": True,
                "claim_text_must_explicitly_state_every_linked_observation": True,
                "claim_must_cite_every_required_evidence_entry": True,
                "narrowing_one_unsafe_scope_must_preserve_every_safe_observation": True,
            },
            "rewrite_findings": [
                {
                    "finding_code": item.finding_code,
                    "checklist_item_id": item.checklist_item_id,
                    "claim_id": item.claim_id,
                    "description": item.description,
                    "remediation": item.remediation.value,
                    "existing_evidence_entry_ids": [
                        reference.value
                        for reference in item.existing_evidence_entry_ids
                    ],
                    "digest": item.digest.value,
                }
                for item in rewrite_findings
            ],
            "question_understanding": understanding.model_view(),
            "question_evidence_package": package.model_view(),
            "response_rule": (
                "ONE_DIRECT_ANSWER_FIRST_THEN_USER_VISIBLE_PROCESS_IMPACT_"
                "OPTIONAL_IMPLEMENTATION_EVIDENCE_AND_LIMITATION"
            ),
            "answer_structure_contract": {
                "detail_level": understanding.requested_abstraction_level.value,
                "required_first_role": AnswerContentRole.DIRECT_ANSWER.value,
                "maximum_direct_answer_claims": 1,
                "ordered_roles": [item.value for item in AnswerContentRole],
                "mixed_disposition_direct_answer_policy": (
                    "AFFIRMATIVE_DIRECT_SUMMARY_FOR_SUPPORTED_ITEMS_THEN_"
                    "FINAL_LIMITATION_CLAIMS_FOR_NON_SUPPORTED_ITEMS"
                ),
                "limitation_direct_answer_policy": (
                    "ALLOWED_ONLY_WHEN_EVERY_CHECKLIST_DISPOSITION_IS_NON_SUPPORTED"
                ),
                "every_claim_links_material_checklist": True,
                "every_material_checklist_item_covered": True,
                "every_material_fact_claim_links_material_observations": True,
                "every_package_material_observation_covered": True,
                "every_material_observation_visible_in_default_body": True,
                "observation_link_requires_explicit_claim_text_and_all_evidence": True,
                "coverage_only_limitation_empty_observation_links_allowed": True,
                "allowed_kind_by_content_role": {
                    AnswerContentRole.DIRECT_ANSWER.value: (
                        AnswerClaimKind.AFFIRMATIVE.value,
                        AnswerClaimKind.LIMITATION.value,
                    ),
                    AnswerContentRole.USER_VISIBLE_PROCESS.value: (
                        AnswerClaimKind.AFFIRMATIVE.value,
                    ),
                    AnswerContentRole.IMPACT_OR_SIDE_EFFECT.value: (
                        AnswerClaimKind.AFFIRMATIVE.value,
                    ),
                    AnswerContentRole.IMPLEMENTATION_EVIDENCE.value: (
                        AnswerClaimKind.AFFIRMATIVE.value,
                    ),
                    AnswerContentRole.LIMITATION.value: (
                        AnswerClaimKind.LIMITATION.value,
                    ),
                },
                "implementation_evidence_is_optional": True,
                "implementation_evidence_default_visible": (
                    understanding.requested_abstraction_level
                    is AnswerDetailLevel.IMPLEMENTATION_DETAIL
                ),
                "implementation_evidence_unique_material_observation_visible": True,
            },
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
        review_focus: EngineeringReviewFocus = EngineeringReviewFocus.COMPREHENSIVE,
    ) -> EngineeringQuestionRoleInputManifest:
        if not isinstance(review_focus, EngineeringReviewFocus):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "Engineering QA Review focus is outside the closed vocabulary",
            )
        if (
            understanding.request_digest != package.request_digest
            or original_question != package.original_question
            or draft.package_digest != package.digest
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Engineering QA Review input crosses Request or Package identities",
            )
        challenges = (
            project_evidence_boundary_challenges(package, draft)
            if review_focus
            is EngineeringReviewFocus.EVIDENCE_BOUNDARY_CHALLENGE
            else ()
        )
        challenge_views = (
            _evidence_boundary_challenges(package, draft)
            if review_focus
            is EngineeringReviewFocus.EVIDENCE_BOUNDARY_CHALLENGE
            else []
        )
        body = {
            "review_focus": review_focus.value,
            "verified_gap_outcomes": _verified_gap_outcomes(package),
            "evidence_boundary_challenges": challenge_views,
            "evidence_boundary_assessment_contract": {
                "required_challenge_ids": [
                    item.challenge_id.value for item in challenges
                ],
                "required_comparison_fields": [
                    "evidence_boundary",
                    "draft_scope",
                    "disposition",
                ],
                "within_boundary_disposition": (
                    EngineeringEvidenceBoundaryAssessmentDisposition.WITHIN_EVIDENCE_BOUNDARY.value
                ),
                "exceeded_boundary_disposition": (
                    EngineeringEvidenceBoundaryAssessmentDisposition.DRAFT_EXCEEDS_EVIDENCE_BOUNDARY.value
                ),
                "omitted_material_effect_disposition": (
                    EngineeringEvidenceBoundaryAssessmentDisposition.DRAFT_OMITS_MATERIAL_EFFECT.value
                ),
                "material_effect_omission_layers": [
                    item.value for item in EngineeringMaterialEffectOmissionLayer
                ],
                "material_effect_application_omission_requires_verification": True,
                "material_effect_draft_omission_requires_exact_projected_observation": True,
                "omitted_material_requirement_disposition": (
                    EngineeringEvidenceBoundaryAssessmentDisposition.DRAFT_OMITS_MATERIAL_REQUIREMENT.value
                ),
                "non_passing_assessment_requires_returned_finding_code": True,
                "finding_claim_id_must_be_one_of_challenge_claim_ids": True,
                "shared_finding_code_allowed_only_when_its_claim_id_is_in_every_bound_challenge": True,
                "comprehensive_review_requires_empty_assessments": True,
            },
            "original_question": original_question,
            "draft": draft.model_view(),
            "question_understanding": understanding.model_view(),
            "question_evidence_package": package.model_view(),
            "answer_structure": {
                "detail_level": understanding.requested_abstraction_level.value,
                "first_content_role": draft.claims[0].content_role.value,
                "default_body_claim_ids": list(draft.default_body_claim_ids),
                "content_role_counts": {
                    role.value: sum(
                        claim.content_role is role for claim in draft.claims
                    )
                    for role in AnswerContentRole
                },
                "material_checklist_coverage": {
                    item.item_id: [
                        claim.claim_id
                        for claim in draft.claims
                        if item.item_id in claim.checklist_item_ids
                    ]
                    for item in understanding.checklist
                },
                "material_observation_coverage": {
                    observation.observation_id.value: [
                        claim.claim_id
                        for claim in draft.claims
                        if observation.observation_id
                        in claim.material_observation_ids
                    ]
                    for disposition in package.checklist_dispositions
                    for observation in disposition.material_observations
                },
            },
            "review_dimensions": [
                "direct_answer",
                "abstraction_level",
                "material_process_and_side_effect_completeness",
                "cross_claim_and_observation_consistency",
                "implementation_detail_budget",
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
            "verified_gap_review_rule": (
                "DO_NOT_REPEAT_A_TERMINAL_VERIFIED_GAP_WHEN_THE_DRAFT_"
                "PRESERVES_ITS_HONEST_LIMITATION"
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
                requested_abstraction_level=AnswerDetailLevel(
                    cast(str, value["requested_abstraction_level"])
                ),
                material_conclusions=cast(
                    Sequence[str], value["material_conclusions"]
                ),
                evidence_needs=cast(Sequence[str], value["evidence_needs"]),
                required_evidence_classes=tuple(
                    EngineeringEvidenceClass(item)
                    for item in cast(
                        Sequence[str], value["required_evidence_classes"]
                    )
                ),
                required_evidence_paths=cast(
                    Sequence[str], value["required_evidence_paths"]
                ),
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
            claim_values = (
                cast(Mapping[str, object], value["direct_answer"]),
                *cast(Sequence[Mapping[str, object]], value["claims"]),
            )
            claims = tuple(
                EngineeringAnswerClaimProposal.create(
                    claim_id=cast(str, item["claim_id"]),
                    kind=AnswerClaimKind(cast(str, item["kind"])),
                    content_role=AnswerContentRole(
                        cast(str, item["content_role"])
                    ),
                    checklist_item_ids=cast(
                        Sequence[str], item["checklist_item_ids"]
                    ),
                    material_observation_ids=tuple(
                        StableId(reference)
                        for reference in cast(
                            Sequence[str], item["material_observation_ids"]
                        )
                    ),
                    text=cast(str, item["text"]),
                    evidence_entry_ids=tuple(
                        StableId(reference)
                        for reference in cast(
                            Sequence[str], item["evidence_entry_ids"]
                        )
                    ),
                )
                for item in claim_values
            )
            # The Provider output remains immutable in the Gateway audit.  The
            # adapter canonicalizes only the presentation order required by the
            # domain contract, preserving Provider order within each role.
            claims = (
                claims[0],
                *sorted(
                    claims[1:],
                    key=lambda claim: _ANSWER_CONTENT_ROLE_ORDINAL[
                        claim.content_role
                    ],
                ),
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
        review_focus: EngineeringReviewFocus = EngineeringReviewFocus.COMPREHENSIVE,
    ) -> EngineeringReviewProposal:
        manifest = EngineeringQuestionRoleInputBuilder.review(
            original_question=original_question,
            understanding=understanding,
            package=package,
            draft=draft,
            role_context_id=role_context_id,
            review_focus=review_focus,
        )
        value = self._output(manifest)
        try:
            quality_value = cast(
                Mapping[str, object], value["quality_assessment"]
            )
            quality_assessment = EngineeringReviewQualityAssessment.create(
                direct_answer=EngineeringReviewQualityStatus(
                    cast(str, quality_value["direct_answer"])
                ),
                abstraction_fit=EngineeringReviewQualityStatus(
                    cast(str, quality_value["abstraction_fit"])
                ),
                material_completeness=EngineeringReviewQualityStatus(
                    cast(str, quality_value["material_completeness"])
                ),
                claim_consistency=EngineeringReviewQualityStatus(
                    cast(str, quality_value["claim_consistency"])
                ),
                implementation_detail_budget=EngineeringReviewQualityStatus(
                    cast(str, quality_value["implementation_detail_budget"])
                ),
            )
            checklist_value = cast(
                Mapping[str, object], value["checklist_assessment"]
            )
            checklist_assessment = EngineeringReviewChecklistAssessment.create(
                independent_material_conclusions=cast(
                    Sequence[str],
                    checklist_value["independent_material_conclusions"],
                ),
                application_checklist_omissions=cast(
                    Sequence[str],
                    checklist_value["application_checklist_omissions"],
                ),
                independent_material_observations=tuple(
                    EngineeringReviewMaterialObservation.create(
                        checklist_item_id=cast(
                            str, item["checklist_item_id"]
                        ),
                        kind=MaterialObservationKind(cast(str, item["kind"])),
                        statement=cast(str, item["statement"]),
                        evidence_entry_ids=tuple(
                            StableId(reference)
                            for reference in cast(
                                Sequence[str], item["evidence_entry_ids"]
                            )
                        ),
                    )
                    for item in cast(
                        Sequence[Mapping[str, object]],
                        checklist_value["independent_material_observations"],
                    )
                ),
                application_material_observation_omissions=cast(
                    Sequence[str],
                    checklist_value[
                        "application_material_observation_omissions"
                    ],
                ),
                draft_material_observation_omissions=cast(
                    Sequence[str],
                    checklist_value["draft_material_observation_omissions"],
                ),
            )
            boundary_assessments = tuple(
                EngineeringEvidenceBoundaryAssessment.create(
                    challenge_id=StableId(cast(str, item["challenge_id"])),
                    evidence_boundary=cast(str, item["evidence_boundary"]),
                    draft_scope=cast(str, item["draft_scope"]),
                    disposition=(
                        EngineeringEvidenceBoundaryAssessmentDisposition(
                            cast(str, item["disposition"])
                        )
                    ),
                    finding_code=cast(str | None, item["finding_code"]),
                    material_effect_omission_layer=(
                        EngineeringMaterialEffectOmissionLayer(
                            cast(str, item["material_effect_omission_layer"])
                        )
                        if "material_effect_omission_layer" in item
                        else None
                    ),
                    omitted_material_effect_statements=cast(
                        Sequence[str],
                        item.get("omitted_material_effect_statements", ()),
                    ),
                )
                for item in cast(
                    Sequence[Mapping[str, object]],
                    value["evidence_boundary_assessments"],
                )
            )
            findings = tuple(
                EngineeringReviewFinding.create(
                    finding_code=cast(str, item["finding_code"]),
                    checklist_item_id=cast(str | None, item["checklist_item_id"]),
                    claim_id=cast(str | None, item["claim_id"]),
                    description=cast(str, item["description"]),
                    remediation=EngineeringReviewRemediation(
                        cast(str, item["remediation"])
                    ),
                    existing_evidence_entry_ids=tuple(
                        StableId(reference)
                        for reference in cast(
                            Sequence[str], item["existing_evidence_entry_ids"]
                        )
                    ),
                    evidence_class=(
                        EngineeringEvidenceClass(
                            cast(str, item["evidence_class"])
                        )
                        if item["evidence_class"] is not None
                        else None
                    ),
                    evidence_need=cast(str | None, item["evidence_need"]),
                )
                for item in cast(Sequence[Mapping[str, object]], value["findings"])
            )
            return EngineeringReviewProposal.create_from_findings(
                role_context_id=role_context_id,
                package_digest=package.digest,
                draft_digest=draft.digest,
                quality_assessment=quality_assessment,
                checklist_assessment=checklist_assessment,
                evidence_boundary_assessments=boundary_assessments,
                findings=findings,
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
            _provider_finish_disposition(item)
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


def _provider_finish_disposition(
    item: Mapping[str, object],
) -> ChecklistDisposition:
    """Build the Domain parent closure from the Provider's child observations."""

    checklist_item_id = cast(str, item["checklist_item_id"])
    observations = tuple(
        MaterialObservation.create(
            checklist_item_id=checklist_item_id,
            kind=MaterialObservationKind(cast(str, observation["kind"])),
            statement=cast(str, observation["statement"]),
            evidence_references=cast(
                Sequence[str], observation["evidence_references"]
            ),
        )
        for observation in cast(
            Sequence[Mapping[str, object]], item["material_observations"]
        )
    )
    parent_references = tuple(
        dict.fromkeys(
            reference
            for observation in observations
            for reference in observation.evidence_references
        )
    )
    return ChecklistDisposition.create(
        checklist_item_id=checklist_item_id,
        outcome=ChecklistOutcome(cast(str, item["outcome"])),
        evidence_references=parent_references,
        explanation=cast(str, item["explanation"]),
        material_observations=observations,
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
