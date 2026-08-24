"""Adaptive, cognition-guided engineering question answering.

This module owns the request-scoped authority chain accepted by ADR-016.  Model
roles only return proposals.  The application validates every proposal, a
``SourceBroker`` compiles the only executable read operation, and an injected
``RetrievalWorker`` executes it.  Answer and review roles only receive a sealed
``QuestionEvidencePackage``.

The first implementation deliberately keeps the ledger request-scoped.  Cross
process recovery and durable replay are ITER-010 Slice 2 concerns; immutability,
revision binding, package identity, and fail-closed behaviour are already part
of this Slice 1 value model.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
import re
from time import monotonic_ns
from typing import Mapping, Protocol, Sequence

from software_world_model.cross_cutting import (
    Digest,
    DomainError,
    ErrorCode,
    StableId,
    canonical_json_bytes,
    digest_of,
)


ENGINEERING_QA_MODE = "ENGINEERING_QA"
ENGINEERING_QA_PROTOCOL = "ENGINEERING_QA_ADAPTIVE_INVESTIGATION@3"
ENGINEERING_QA_PACKAGE_SCHEMA = "QUESTION_EVIDENCE_PACKAGE@2"
ENGINEERING_QA_VERIFICATION_REQUEST_SCHEMA = "ENGINEERING_QA_VERIFICATION_REQUEST@1"
ENGINEERING_QA_BROKER_POLICY = "ENGINEERING_QA_SOURCE_BROKER@2"
ENGINEERING_QA_REQUIRED_PATH_LOCATOR_SCHEMA = (
    "ENGINEERING_QA_REQUIRED_EVIDENCE_PATH_LOCATOR@1"
)
MAXIMUM_MATERIAL_OBSERVATIONS_PER_DISPOSITION = 16
MAXIMUM_REQUIRED_EVIDENCE_PATHS = 4

_FULL_GIT_OID = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
_SAFE_REFERENCE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:@-]{0,255}$")
_PATH_LIKE_EVIDENCE_NEED = re.compile(
    r"(?:https?://|file://|(?:^|\s)(?:\.{0,2}/|[A-Za-z]:\\)|"
    r"\b(?:search|read|parse)\s*\(|\b(?:curl|wget|git|cat|sed|grep|rg)\s+|"
    r"[;&|`$<>])",
    re.IGNORECASE,
)


def _text(value: str, label: str, *, maximum_bytes: int = 65_536) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            f"{label} must be non-empty and cannot have surrounding whitespace",
        )
    if len(value.encode("utf-8")) > maximum_bytes:
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            f"{label} exceeds its UTF-8 byte limit",
        )
    return value


def _reference(value: str, label: str) -> str:
    value = _text(value, label, maximum_bytes=256)
    if not _SAFE_REFERENCE.fullmatch(value):
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            f"{label} is not a canonical reference",
        )
    return value


def _content_text(value: str, label: str, *, maximum_bytes: int) -> str:
    """Validate untrusted observed text without rewriting exact whitespace."""

    if not isinstance(value, str) or not value:
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} must be non-empty")
    if len(value.encode("utf-8")) > maximum_bytes:
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            f"{label} exceeds its UTF-8 byte limit",
        )
    return value


def _stable_id(kind: str, value: object) -> StableId:
    digest = digest_of([kind, value]).value.removeprefix("sha256:")
    return StableId(f"{kind}_{digest[:32]}")


def _canonical_relative_path(value: str) -> str:
    value = _text(value, "source allowlist path", maximum_bytes=1_024).replace(
        "\\", "/"
    )
    if value == ".":
        return value
    if value.startswith("/") or "\x00" in value:
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            "source allowlist paths must be repository-relative",
        )
    parts = tuple(part for part in value.split("/") if part not in {"", "."})
    if not parts or any(part == ".." for part in parts):
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            "source allowlist paths cannot traverse parent directories",
        )
    return "/".join(parts)


def _path_allowed(path: str, allowlist: tuple[str, ...]) -> bool:
    normalized = _canonical_relative_path(path)
    return any(
        prefix == "." or normalized == prefix or normalized.startswith(prefix + "/")
        for prefix in allowlist
    )


def _unique_texts(
    values: Sequence[str],
    label: str,
    *,
    maximum_items: int,
    maximum_bytes: int = 8_192,
) -> tuple[str, ...]:
    if not values or len(values) > maximum_items:
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            f"{label} must contain one to {maximum_items} items",
        )
    normalized = tuple(
        _text(value, f"{label} item", maximum_bytes=maximum_bytes) for value in values
    )
    if len(set(normalized)) != len(normalized):
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            f"{label} contains duplicate items",
        )
    return normalized


class CognitionDimension(str, Enum):
    ENTITY = "ENTITY"
    RELATION = "RELATION"
    BEHAVIOR = "BEHAVIOR"
    CONSTRAINT = "CONSTRAINT"
    STATE = "STATE"
    EVIDENCE = "EVIDENCE"
    COVERAGE = "COVERAGE"
    UNKNOWN = "UNKNOWN"


class RevisionAlignment(str, Enum):
    ALIGNED = "ALIGNED"
    UNALIGNED_REVISION = "UNALIGNED_REVISION"


class EngineeringEvidenceClass(str, Enum):
    WORLD_MODEL = "WORLD_MODEL"
    SOURCE = "SOURCE"
    REPOSITORY_DOCUMENT = "REPOSITORY_DOCUMENT"
    BUILD_CONFIGURATION = "BUILD_CONFIGURATION"
    TEST = "TEST"


_RETRIEVAL_EVIDENCE_CLASS_ORDER = (
    EngineeringEvidenceClass.SOURCE,
    EngineeringEvidenceClass.REPOSITORY_DOCUMENT,
    EngineeringEvidenceClass.BUILD_CONFIGURATION,
    EngineeringEvidenceClass.TEST,
)
_RETRIEVAL_EVIDENCE_CLASSES = frozenset(_RETRIEVAL_EVIDENCE_CLASS_ORDER)


class SourceReadOperation(str, Enum):
    SEARCH = "search"
    READ = "read"
    PARSE = "parse"


class InvestigationOperation(str, Enum):
    SEARCH = "search"
    READ = "read"
    PARSE = "parse"
    FINISH = "FINISH"


class InvestigationKind(str, Enum):
    INITIAL = "INITIAL"
    VERIFICATION = "VERIFICATION"


class RetrievalStatus(str, Enum):
    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
    OUTCOME_UNKNOWN = "OUTCOME_UNKNOWN"


class BrokerDecisionStatus(str, Enum):
    AUTHORIZED = "AUTHORIZED"
    REJECTED = "REJECTED"


class LedgerEntryKind(str, Enum):
    COGNITION_CONTEXT = "COGNITION_CONTEXT"
    VERIFICATION_REQUEST = "VERIFICATION_REQUEST"
    INVESTIGATION_PROPOSAL = "INVESTIGATION_PROPOSAL"
    BROKER_DECISION = "BROKER_DECISION"
    SOURCE_OPERATION = "SOURCE_OPERATION"
    SOURCE_RESULT = "SOURCE_RESULT"
    GAP = "GAP"
    RESOURCE_RECEIPT = "RESOURCE_RECEIPT"
    FINISH = "FINISH"
    FAIL_CLOSED_STOP = "FAIL_CLOSED_STOP"


class LedgerTerminalStatus(str, Enum):
    ACTIVE = "ACTIVE"
    FINISHED = "FINISHED"
    FAILED_CLOSED = "FAILED_CLOSED"


class ChecklistOutcome(str, Enum):
    SUPPORTED = "SUPPORTED"
    UNKNOWN = "UNKNOWN"
    CONFLICT = "CONFLICT"
    FAILED = "FAILED"


class MaterialObservationKind(str, Enum):
    PROCESS_STAGE = "PROCESS_STAGE"
    OUTCOME = "OUTCOME"
    STATE_CHANGE = "STATE_CHANGE"
    SIDE_EFFECT = "SIDE_EFFECT"
    LIMITATION = "LIMITATION"


class PackageBoundaryKind(str, Enum):
    BOUNDARY = "BOUNDARY"
    GAP = "GAP"
    FAILURE = "FAILURE"
    PARTIAL = "PARTIAL"
    CONFLICT = "CONFLICT"
    UNKNOWN = "UNKNOWN"
    REJECTED_DECISION = "REJECTED_DECISION"
    RESOURCE_RECEIPT = "RESOURCE_RECEIPT"
    SEARCH_CANDIDATE = "SEARCH_CANDIDATE"
    UNALIGNED_REVISION = "UNALIGNED_REVISION"


class AnswerClaimKind(str, Enum):
    AFFIRMATIVE = "AFFIRMATIVE"
    LIMITATION = "LIMITATION"


class AnswerDetailLevel(str, Enum):
    DIRECT = "DIRECT"
    USER_VISIBLE_EXPLANATION = "USER_VISIBLE_EXPLANATION"
    IMPLEMENTATION_DETAIL = "IMPLEMENTATION_DETAIL"


class AnswerContentRole(str, Enum):
    DIRECT_ANSWER = "DIRECT_ANSWER"
    USER_VISIBLE_PROCESS = "USER_VISIBLE_PROCESS"
    IMPACT_OR_SIDE_EFFECT = "IMPACT_OR_SIDE_EFFECT"
    IMPLEMENTATION_EVIDENCE = "IMPLEMENTATION_EVIDENCE"
    LIMITATION = "LIMITATION"


class EngineeringReviewDecision(str, Enum):
    APPROVED = "APPROVED"
    REWRITE_REQUIRED = "REWRITE_REQUIRED"
    MORE_EVIDENCE_REQUIRED = "MORE_EVIDENCE_REQUIRED"
    REJECT = "REJECT"


class EngineeringReviewRemediation(str, Enum):
    REWRITE_WITH_EXISTING_EVIDENCE = "REWRITE_WITH_EXISTING_EVIDENCE"
    INVESTIGATE_MISSING_EVIDENCE = "INVESTIGATE_MISSING_EVIDENCE"
    REJECT_UNRECOVERABLE = "REJECT_UNRECOVERABLE"


class EngineeringQuestionResultStatus(str, Enum):
    APPROVED = "APPROVED"
    FAILED_CLOSED = "FAILED_CLOSED"


class EngineeringReviewQualityStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"


@dataclass(frozen=True, slots=True)
class EngineeringQuestionResourceLimits:
    """High safety fuses frozen by ITER-010 Slice 1."""

    maximum_question_understanding_calls: int = 1
    maximum_initial_investigation_calls: int = 12
    maximum_investigation_steps: int = 24
    maximum_total_model_role_calls: int = 24
    maximum_verification_investigations: int = 1
    maximum_source_operations: int = 128
    maximum_source_files: int = 64
    maximum_source_bytes: int = 2_097_152
    maximum_repository_document_bytes: int = 1_048_576
    maximum_build_configuration_bytes: int = 524_288
    maximum_test_bytes: int = 1_048_576
    maximum_world_model_bytes: int = 1_048_576
    maximum_ledger_bytes: int = 2_097_152
    maximum_package_bytes: int = 4_194_304
    maximum_support_items: int = 1_024
    maximum_answer_attempts: int = 3
    maximum_review_attempts: int = 3
    maximum_same_package_rewrites: int = 1
    maximum_no_progress_steps: int = 2
    maximum_wall_time_milliseconds: int = 900_000

    def __post_init__(self) -> None:
        values = tuple(getattr(self, field) for field in self.__dataclass_fields__)
        if any(isinstance(value, bool) or value < 1 for value in values):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "engineering question resource limits must all be positive",
            )

    @property
    def digest(self) -> Digest:
        return digest_of(["ENGINEERING_QA_RESOURCE_LIMITS@1", self])


@dataclass(frozen=True, slots=True)
class EngineeringQuestionRequest:
    request_id: StableId
    request_ref: str
    mode: str
    protocol: str
    original_question: str
    response_language: str
    repository_id: StableId
    binding_id: StableId
    repository_revision: str
    source_profile_ref: str
    source_profile_digest: Digest
    world_model_read_authority_digest: Digest
    source_allowlist: tuple[str, ...]
    registered_operations: tuple[SourceReadOperation, ...]
    provider_disclosure_policy: str
    limits: EngineeringQuestionResourceLimits
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        request_ref: str,
        original_question: str,
        response_language: str,
        repository_id: StableId,
        binding_id: StableId,
        repository_revision: str,
        source_profile_ref: str,
        source_profile_digest: Digest,
        world_model_read_authority_digest: Digest,
        source_allowlist: Sequence[str],
        registered_operations: Sequence[SourceReadOperation] = (
            SourceReadOperation.SEARCH,
            SourceReadOperation.READ,
            SourceReadOperation.PARSE,
        ),
        provider_disclosure_policy: str = "NO_EXTERNAL_DISCLOSURE",
        limits: EngineeringQuestionResourceLimits | None = None,
    ) -> "EngineeringQuestionRequest":
        request_ref = _reference(request_ref, "engineering question request reference")
        original_question = _text(
            original_question, "original engineering question", maximum_bytes=65_536
        )
        response_language = _text(
            response_language, "response language", maximum_bytes=128
        )
        repository_revision = _text(
            repository_revision, "repository revision", maximum_bytes=64
        ).casefold()
        if not _FULL_GIT_OID.fullmatch(repository_revision):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "engineering question repository revision must be a full Git object ID",
            )
        source_profile_ref = _reference(
            source_profile_ref, "source profile reference"
        )
        normalized_allowlist = tuple(
            sorted({_canonical_relative_path(path) for path in source_allowlist})
        )
        if not normalized_allowlist:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "engineering question source allowlist cannot be empty",
            )
        operations = tuple(registered_operations)
        if not operations or len(set(operations)) != len(operations):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "engineering question registered operations must be non-empty and unique",
            )
        if any(not isinstance(operation, SourceReadOperation) for operation in operations):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "engineering question operation set contains an unknown operation",
            )
        provider_disclosure_policy = _reference(
            provider_disclosure_policy, "provider disclosure policy"
        )
        limits = limits or EngineeringQuestionResourceLimits()
        core = {
            "schema": ENGINEERING_QA_PROTOCOL,
            "request_ref": request_ref,
            "mode": ENGINEERING_QA_MODE,
            "original_question": original_question,
            "response_language": response_language,
            "repository_id": repository_id.value,
            "binding_id": binding_id.value,
            "repository_revision": repository_revision,
            "source_profile_ref": source_profile_ref,
            "source_profile_digest": source_profile_digest.value,
            "world_model_read_authority_digest": world_model_read_authority_digest.value,
            "source_allowlist": normalized_allowlist,
            "registered_operations": tuple(item.value for item in operations),
            "provider_disclosure_policy": provider_disclosure_policy,
            "limits_digest": limits.digest.value,
        }
        digest = digest_of(core)
        return cls(
            request_id=_stable_id("engq_request", core),
            request_ref=request_ref,
            mode=ENGINEERING_QA_MODE,
            protocol=ENGINEERING_QA_PROTOCOL,
            original_question=original_question,
            response_language=response_language,
            repository_id=repository_id,
            binding_id=binding_id,
            repository_revision=repository_revision,
            source_profile_ref=source_profile_ref,
            source_profile_digest=source_profile_digest,
            world_model_read_authority_digest=world_model_read_authority_digest,
            source_allowlist=normalized_allowlist,
            registered_operations=operations,
            provider_disclosure_policy=provider_disclosure_policy,
            limits=limits,
            digest=digest,
        )

    def investigation_control_view(self) -> dict[str, object]:
        """Trusted controls visible to an investigation role, never a repo handle."""

        return {
            "mode": self.mode,
            "protocol": self.protocol,
            "request_id": self.request_id.value,
            "request_digest": self.digest.value,
            "original_question": self.original_question,
            "response_language": self.response_language,
            "repository_id": self.repository_id.value,
            "binding_id": self.binding_id.value,
            "repository_revision": self.repository_revision,
            "source_profile_ref": self.source_profile_ref,
            "source_profile_digest": self.source_profile_digest.value,
            "source_allowlist": list(self.source_allowlist),
            "registered_operations": [item.value for item in self.registered_operations],
            "provider_disclosure_policy": self.provider_disclosure_policy,
            "limits_digest": self.limits.digest.value,
        }


@dataclass(frozen=True, slots=True)
class QuestionUnderstandingProposal:
    role_context_id: StableId
    request_digest: Digest
    preserved_original_question: str
    user_goal: str
    audience: str
    requested_abstraction_level: AnswerDetailLevel
    material_conclusions: tuple[str, ...]
    evidence_needs: tuple[str, ...]
    required_evidence_classes: tuple[EngineeringEvidenceClass, ...]
    required_evidence_paths: tuple[str, ...]
    response_language: str
    response_constraints: tuple[str, ...]
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        role_context_id: StableId,
        request_digest: Digest,
        preserved_original_question: str,
        user_goal: str,
        audience: str,
        requested_abstraction_level: AnswerDetailLevel,
        material_conclusions: Sequence[str],
        evidence_needs: Sequence[str],
        required_evidence_classes: Sequence[EngineeringEvidenceClass],
        required_evidence_paths: Sequence[str],
        response_language: str,
        response_constraints: Sequence[str] = (),
    ) -> "QuestionUnderstandingProposal":
        conclusions = _unique_texts(
            material_conclusions, "material conclusion checklist", maximum_items=12
        )
        needs = _unique_texts(evidence_needs, "evidence needs", maximum_items=24)
        required_classes = tuple(required_evidence_classes)
        if (
            not required_classes
            or len(required_classes) > len(_RETRIEVAL_EVIDENCE_CLASS_ORDER)
            or len(set(required_classes)) != len(required_classes)
            or any(
                not isinstance(item, EngineeringEvidenceClass)
                or item not in _RETRIEVAL_EVIDENCE_CLASSES
                for item in required_classes
            )
        ):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "required evidence classes must be unique controlled retrieval classes",
            )
        required_paths = tuple(
            _canonical_relative_path(path) for path in required_evidence_paths
        )
        if (
            not required_paths
            or len(required_paths) > MAXIMUM_REQUIRED_EVIDENCE_PATHS
            or len(set(required_paths)) != len(required_paths)
        ):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "required evidence paths must contain one to four unique repository-relative paths",
            )
        constraints = tuple(
            _text(value, "response constraint", maximum_bytes=4_096)
            for value in response_constraints
        )
        if len(constraints) > 12 or len(set(constraints)) != len(constraints):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "response constraints must be unique and contain at most twelve items",
            )
        if not isinstance(requested_abstraction_level, AnswerDetailLevel):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "requested abstraction level must use the controlled answer-detail vocabulary",
            )
        core = {
            "role_context_id": role_context_id.value,
            "request_digest": request_digest.value,
            "preserved_original_question": _text(
                preserved_original_question,
                "preserved original question",
                maximum_bytes=65_536,
            ),
            "user_goal": _text(user_goal, "user goal", maximum_bytes=8_192),
            "audience": _text(audience, "audience", maximum_bytes=1_024),
            "requested_abstraction_level": requested_abstraction_level.value,
            "material_conclusions": conclusions,
            "evidence_needs": needs,
            "required_evidence_classes": tuple(
                item.value for item in required_classes
            ),
            "required_evidence_paths": required_paths,
            "response_language": _text(
                response_language, "proposal response language", maximum_bytes=128
            ),
            "response_constraints": constraints,
        }
        return cls(
            role_context_id=role_context_id,
            request_digest=request_digest,
            preserved_original_question=core["preserved_original_question"],
            user_goal=core["user_goal"],
            audience=core["audience"],
            requested_abstraction_level=requested_abstraction_level,
            material_conclusions=conclusions,
            evidence_needs=needs,
            required_evidence_classes=required_classes,
            required_evidence_paths=required_paths,
            response_language=core["response_language"],
            response_constraints=constraints,
            digest=digest_of(["QUESTION_UNDERSTANDING_PROPOSAL@5", core]),
        )


@dataclass(frozen=True, slots=True)
class QuestionChecklistItem:
    item_id: str
    conclusion: str
    digest: Digest


@dataclass(frozen=True, slots=True)
class QuestionUnderstanding:
    understanding_id: StableId
    request_digest: Digest
    original_question: str
    user_goal: str
    audience: str
    requested_abstraction_level: AnswerDetailLevel
    checklist: tuple[QuestionChecklistItem, ...]
    evidence_needs: tuple[str, ...]
    required_evidence_classes: tuple[EngineeringEvidenceClass, ...]
    required_evidence_paths: tuple[str, ...]
    response_language: str
    response_constraints: tuple[str, ...]
    proposal_digest: Digest
    digest: Digest

    @classmethod
    def accept(
        cls,
        *,
        request: EngineeringQuestionRequest,
        expected_role_context_id: StableId,
        proposal: QuestionUnderstandingProposal,
    ) -> "QuestionUnderstanding":
        expected_proposal = QuestionUnderstandingProposal.create(
            role_context_id=proposal.role_context_id,
            request_digest=proposal.request_digest,
            preserved_original_question=proposal.preserved_original_question,
            user_goal=proposal.user_goal,
            audience=proposal.audience,
            requested_abstraction_level=proposal.requested_abstraction_level,
            material_conclusions=proposal.material_conclusions,
            evidence_needs=proposal.evidence_needs,
            required_evidence_classes=proposal.required_evidence_classes,
            required_evidence_paths=proposal.required_evidence_paths,
            response_language=proposal.response_language,
            response_constraints=proposal.response_constraints,
        )
        if proposal != expected_proposal:
            raise DomainError(
                ErrorCode.PROVIDER_RESPONSE_INVALID,
                "question understanding Proposal identity is invalid",
            )
        if (
            proposal.role_context_id != expected_role_context_id
            or proposal.request_digest != request.digest
            or proposal.preserved_original_question != request.original_question
            or proposal.response_language != request.response_language
            or any(
                not _path_allowed(path, request.source_allowlist)
                for path in proposal.required_evidence_paths
            )
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "question understanding does not preserve the immutable request",
            )
        checklist = tuple(
            QuestionChecklistItem(
                item_id=f"check-{index}",
                conclusion=conclusion,
                digest=digest_of(
                    ["ENGINEERING_QA_CHECKLIST_ITEM@1", index, conclusion]
                ),
            )
            for index, conclusion in enumerate(proposal.material_conclusions, 1)
        )
        core = {
            "request_digest": request.digest.value,
            "original_question": request.original_question,
            "user_goal": proposal.user_goal,
            "audience": proposal.audience,
            "requested_abstraction_level": proposal.requested_abstraction_level.value,
            "checklist": tuple(
                (item.item_id, item.conclusion, item.digest.value) for item in checklist
            ),
            "evidence_needs": proposal.evidence_needs,
            "required_evidence_classes": tuple(
                item.value for item in proposal.required_evidence_classes
            ),
            "required_evidence_paths": proposal.required_evidence_paths,
            "response_language": proposal.response_language,
            "response_constraints": proposal.response_constraints,
            "proposal_digest": proposal.digest.value,
        }
        digest = digest_of(["QUESTION_UNDERSTANDING@5", core])
        return cls(
            understanding_id=_stable_id("question_understanding", core),
            request_digest=request.digest,
            original_question=request.original_question,
            user_goal=proposal.user_goal,
            audience=proposal.audience,
            requested_abstraction_level=proposal.requested_abstraction_level,
            checklist=checklist,
            evidence_needs=proposal.evidence_needs,
            required_evidence_classes=proposal.required_evidence_classes,
            required_evidence_paths=proposal.required_evidence_paths,
            response_language=proposal.response_language,
            response_constraints=proposal.response_constraints,
            proposal_digest=proposal.digest,
            digest=digest,
        )

    def model_view(self) -> dict[str, object]:
        return {
            "understanding_id": self.understanding_id.value,
            "understanding_digest": self.digest.value,
            "user_goal": self.user_goal,
            "audience": self.audience,
            "requested_abstraction_level": self.requested_abstraction_level.value,
            "material_conclusion_checklist": [
                {"item_id": item.item_id, "conclusion": item.conclusion}
                for item in self.checklist
            ],
            "evidence_needs": list(self.evidence_needs),
            "required_evidence_classes": [
                item.value for item in self.required_evidence_classes
            ],
            "required_evidence_paths": list(self.required_evidence_paths),
            "response_language": self.response_language,
            "response_constraints": list(self.response_constraints),
        }


class QuestionUnderstandingRole(Protocol):
    def understand(
        self,
        *,
        request: EngineeringQuestionRequest,
        role_context_id: StableId,
    ) -> QuestionUnderstandingProposal: ...


@dataclass(frozen=True, slots=True)
class CognitionItem:
    item_id: StableId
    dimension: CognitionDimension
    statement: str
    modality: str
    context_ref: str
    source_revision: str
    locator: str
    support_references: tuple[str, ...]
    coverage: str
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        dimension: CognitionDimension,
        statement: str,
        modality: str,
        context_ref: str,
        source_revision: str,
        locator: str,
        support_references: Sequence[str],
        coverage: str,
    ) -> "CognitionItem":
        supports = tuple(
            _reference(value, "cognition support reference")
            for value in support_references
        )
        if dimension not in {CognitionDimension.COVERAGE, CognitionDimension.UNKNOWN} and not supports:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "affirmative World Model cognition requires a formal support reference",
            )
        core = {
            "dimension": dimension.value,
            "statement": _text(statement, "cognition statement"),
            "modality": _reference(modality, "cognition modality"),
            "context_ref": _reference(context_ref, "cognition context reference"),
            "source_revision": _text(
                source_revision, "cognition source revision", maximum_bytes=64
            ).casefold(),
            "locator": _text(locator, "cognition locator", maximum_bytes=4_096),
            "support_references": supports,
            "coverage": _text(coverage, "cognition coverage", maximum_bytes=8_192),
        }
        if not _FULL_GIT_OID.fullmatch(core["source_revision"]):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "cognition source revision must be a full Git object ID",
            )
        digest = digest_of(["WORLD_MODEL_COGNITION_ITEM@1", core])
        return cls(
            item_id=_stable_id("cognition_item", core),
            dimension=dimension,
            statement=core["statement"],
            modality=core["modality"],
            context_ref=core["context_ref"],
            source_revision=core["source_revision"],
            locator=core["locator"],
            support_references=supports,
            coverage=core["coverage"],
            digest=digest,
        )

    def model_view(self, *, alignment: RevisionAlignment) -> dict[str, object]:
        return {
            "item_id": self.item_id.value,
            "dimension": self.dimension.value,
            "statement": self.statement,
            "modality": self.modality,
            "context_ref": self.context_ref,
            "source_revision": self.source_revision,
            "alignment": alignment.value,
            "locator": self.locator,
            "support_references": list(self.support_references),
            "coverage": self.coverage,
            "digest": self.digest.value,
        }


@dataclass(frozen=True, slots=True)
class WorldModelCognitionContext:
    cognition_context_id: StableId
    request_digest: Digest
    scope_ref: str
    context_ref: str
    schema_ref: str
    snapshot_ids: tuple[str, ...]
    read_authority_digest: Digest
    source_revision: str
    alignment: RevisionAlignment
    items: tuple[CognitionItem, ...]
    coverage: tuple[str, ...]
    conflicts: tuple[str, ...]
    unknowns: tuple[str, ...]
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        request: EngineeringQuestionRequest,
        scope_ref: str,
        context_ref: str,
        schema_ref: str,
        snapshot_ids: Sequence[str],
        read_authority_digest: Digest,
        source_revision: str,
        items: Sequence[CognitionItem],
        coverage: Sequence[str],
        conflicts: Sequence[str] = (),
        unknowns: Sequence[str] = (),
    ) -> "WorldModelCognitionContext":
        if read_authority_digest != request.world_model_read_authority_digest:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "World Model cognition does not bind the request read authority",
            )
        source_revision = _text(
            source_revision, "World Model source revision", maximum_bytes=64
        ).casefold()
        if not _FULL_GIT_OID.fullmatch(source_revision):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "World Model source revision must be a full Git object ID",
            )
        snapshots = _unique_texts(
            snapshot_ids, "World Model Snapshot IDs", maximum_items=32, maximum_bytes=256
        )
        cognition_items = tuple(items)
        if len(cognition_items) > 4_096 or len({item.item_id for item in cognition_items}) != len(cognition_items):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "World Model cognition items must be unique and bounded",
            )
        if any(item.source_revision != source_revision for item in cognition_items):
            raise DomainError(
                ErrorCode.SOURCE_REVISION_INCONSISTENT,
                "World Model cognition item revision differs from its Context revision",
            )
        alignment = (
            RevisionAlignment.ALIGNED
            if source_revision == request.repository_revision
            else RevisionAlignment.UNALIGNED_REVISION
        )
        normalized_coverage = tuple(
            _text(value, "World Model coverage", maximum_bytes=8_192)
            for value in coverage
        )
        if not normalized_coverage:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "World Model cognition must disclose its coverage",
            )
        normalized_conflicts = tuple(
            _text(value, "World Model conflict", maximum_bytes=8_192)
            for value in conflicts
        )
        normalized_unknowns = tuple(
            _text(value, "World Model unknown", maximum_bytes=8_192)
            for value in unknowns
        )
        core = {
            "request_digest": request.digest.value,
            "scope_ref": _reference(scope_ref, "World Model scope reference"),
            "context_ref": _reference(context_ref, "World Model Context reference"),
            "schema_ref": _reference(schema_ref, "World Model Schema reference"),
            "snapshot_ids": snapshots,
            "read_authority_digest": read_authority_digest.value,
            "source_revision": source_revision,
            "alignment": alignment.value,
            "items": tuple(item.digest.value for item in cognition_items),
            "coverage": normalized_coverage,
            "conflicts": normalized_conflicts,
            "unknowns": normalized_unknowns,
        }
        digest = digest_of(["WORLD_MODEL_COGNITION_CONTEXT@1", core])
        return cls(
            cognition_context_id=_stable_id("cognition_context", core),
            request_digest=request.digest,
            scope_ref=core["scope_ref"],
            context_ref=core["context_ref"],
            schema_ref=core["schema_ref"],
            snapshot_ids=snapshots,
            read_authority_digest=read_authority_digest,
            source_revision=source_revision,
            alignment=alignment,
            items=cognition_items,
            coverage=normalized_coverage,
            conflicts=normalized_conflicts,
            unknowns=normalized_unknowns,
            digest=digest,
        )

    def model_view(self) -> dict[str, object]:
        return {
            "cognition_context_id": self.cognition_context_id.value,
            "cognition_context_digest": self.digest.value,
            "scope_ref": self.scope_ref,
            "context_ref": self.context_ref,
            "schema_ref": self.schema_ref,
            "snapshot_ids": list(self.snapshot_ids),
            "read_authority_digest": self.read_authority_digest.value,
            "source_revision": self.source_revision,
            "alignment": self.alignment.value,
            "dimensions": [
                item.model_view(alignment=self.alignment) for item in self.items
            ],
            "coverage": list(self.coverage),
            "conflicts": list(self.conflicts),
            "unknowns": list(self.unknowns),
        }


class WorldModelCognitionProjector(Protocol):
    def project(
        self, *, request: EngineeringQuestionRequest
    ) -> WorldModelCognitionContext: ...


@dataclass(frozen=True, slots=True)
class EvidenceLedgerEntry:
    entry_id: StableId
    sequence: int
    kind: LedgerEntryKind
    subject_id: str
    subject_digest: Digest
    references: tuple[str, ...]
    details: tuple[tuple[str, str], ...]
    previous_entry_digest: Digest | None
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        ledger_id: StableId,
        sequence: int,
        kind: LedgerEntryKind,
        subject_id: str,
        subject_digest: Digest,
        references: Sequence[str] = (),
        details: Mapping[str, str] | None = None,
        previous_entry_digest: Digest | None,
    ) -> "EvidenceLedgerEntry":
        if sequence < 1:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT, "Evidence Ledger sequence must be positive"
            )
        canonical_references = tuple(
            _reference(value, "ledger entry reference") for value in references
        )
        if len(set(canonical_references)) != len(canonical_references):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT, "ledger entry references contain duplicates"
            )
        canonical_details = tuple(
            sorted(
                (
                    _reference(key, "ledger detail key"),
                    _text(value, "ledger detail value", maximum_bytes=8_192),
                )
                for key, value in (details or {}).items()
            )
        )
        core = {
            "ledger_id": ledger_id.value,
            "sequence": sequence,
            "kind": kind.value,
            "subject_id": _reference(subject_id, "ledger subject ID"),
            "subject_digest": subject_digest.value,
            "references": canonical_references,
            "details": canonical_details,
            "previous_entry_digest": (
                previous_entry_digest.value if previous_entry_digest else None
            ),
        }
        digest = digest_of(["EVIDENCE_LEDGER_ENTRY@1", core])
        return cls(
            entry_id=_stable_id("ledger_entry", core),
            sequence=sequence,
            kind=kind,
            subject_id=core["subject_id"],
            subject_digest=subject_digest,
            references=canonical_references,
            details=canonical_details,
            previous_entry_digest=previous_entry_digest,
            digest=digest,
        )

    def model_view(self) -> dict[str, object]:
        return {
            "entry_id": self.entry_id.value,
            "sequence": self.sequence,
            "kind": self.kind.value,
            "subject_id": self.subject_id,
            "subject_digest": self.subject_digest.value,
            "references": list(self.references),
            "details": dict(self.details),
            "previous_entry_digest": (
                self.previous_entry_digest.value if self.previous_entry_digest else None
            ),
            "digest": self.digest.value,
        }


@dataclass(frozen=True, slots=True)
class EvidenceLedger:
    ledger_id: StableId
    request_digest: Digest
    generation: int
    parent_seal_digest: Digest | None
    entries: tuple[EvidenceLedgerEntry, ...]
    terminal_status: LedgerTerminalStatus
    prefix_digest: Digest
    seal_digest: Digest | None

    def validate_integrity(self) -> None:
        if (
            self.generation < 1
            or self.ledger_id
            != _stable_id("evidence_ledger", self.request_digest.value)
            or (self.generation == 1) != (self.parent_seal_digest is None)
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Evidence Ledger generation identity is invalid",
            )
        previous: Digest | None = None
        for sequence, entry in enumerate(self.entries, 1):
            expected = EvidenceLedgerEntry.create(
                ledger_id=self.ledger_id,
                sequence=entry.sequence,
                kind=entry.kind,
                subject_id=entry.subject_id,
                subject_digest=entry.subject_digest,
                references=entry.references,
                details=dict(entry.details),
                previous_entry_digest=entry.previous_entry_digest,
            )
            if (
                entry != expected
                or entry.sequence != sequence
                or entry.previous_entry_digest != previous
            ):
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "Evidence Ledger entry chain identity is invalid",
                )
            previous = entry.digest
        expected_prefix = digest_of(
            [
                "EVIDENCE_LEDGER_PREFIX@1",
                self.ledger_id.value,
                self.request_digest.value,
                self.generation,
                self.parent_seal_digest.value if self.parent_seal_digest else None,
                tuple(item.digest.value for item in self.entries),
            ]
        )
        terminal_entries = sum(
            entry.kind
            in {LedgerEntryKind.FINISH, LedgerEntryKind.FAIL_CLOSED_STOP}
            for entry in self.entries
        )
        if self.terminal_status is LedgerTerminalStatus.ACTIVE:
            valid_terminal = (
                self.seal_digest is None
                and (
                    (
                        terminal_entries == self.generation - 1
                        and (
                            not self.entries
                            or self.entries[-1].kind
                            not in {
                                LedgerEntryKind.FINISH,
                                LedgerEntryKind.FAIL_CLOSED_STOP,
                            }
                            or (
                                self.generation > 1
                                and self.parent_seal_digest is not None
                            )
                        )
                    )
                    or (
                        terminal_entries == self.generation
                        and bool(self.entries)
                        and self.entries[-1].kind
                        in {
                            LedgerEntryKind.FINISH,
                            LedgerEntryKind.FAIL_CLOSED_STOP,
                        }
                    )
                )
            )
        else:
            expected_kind = (
                LedgerEntryKind.FINISH
                if self.terminal_status is LedgerTerminalStatus.FINISHED
                else LedgerEntryKind.FAIL_CLOSED_STOP
            )
            expected_seal = digest_of(
                [
                    "EVIDENCE_LEDGER_SEAL@1",
                    self.ledger_id.value,
                    self.generation,
                    self.prefix_digest.value,
                    self.terminal_status.value,
                ]
            )
            valid_terminal = (
                bool(self.entries)
                and self.entries[-1].kind is expected_kind
                and terminal_entries == self.generation
                and self.seal_digest == expected_seal
            )
        if self.prefix_digest != expected_prefix or not valid_terminal:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Evidence Ledger prefix or terminal seal identity is invalid",
            )

    @classmethod
    def start(
        cls,
        *,
        request: EngineeringQuestionRequest,
        cognition: WorldModelCognitionContext,
    ) -> "EvidenceLedger":
        ledger_id = _stable_id("evidence_ledger", request.digest.value)
        base = cls(
            ledger_id=ledger_id,
            request_digest=request.digest,
            generation=1,
            parent_seal_digest=None,
            entries=(),
            terminal_status=LedgerTerminalStatus.ACTIVE,
            prefix_digest=digest_of(
                [
                    "EVIDENCE_LEDGER_PREFIX@1",
                    ledger_id.value,
                    request.digest.value,
                    1,
                    None,
                    (),
                ]
            ),
            seal_digest=None,
        )
        return base.append(
            kind=LedgerEntryKind.COGNITION_CONTEXT,
            subject_id=cognition.cognition_context_id.value,
            subject_digest=cognition.digest,
            details={"alignment": cognition.alignment.value},
        )

    def append(
        self,
        *,
        kind: LedgerEntryKind,
        subject_id: str,
        subject_digest: Digest,
        references: Sequence[str] = (),
        details: Mapping[str, str] | None = None,
        maximum_bytes: int | None = None,
    ) -> "EvidenceLedger":
        self.validate_integrity()
        if (
            self.terminal_status is not LedgerTerminalStatus.ACTIVE
            or self.seal_digest
            or (
                self.entries
                and self.entries[-1].kind
                in {LedgerEntryKind.FINISH, LedgerEntryKind.FAIL_CLOSED_STOP}
                and not (
                    kind is LedgerEntryKind.VERIFICATION_REQUEST
                    and self.generation > 1
                    and sum(
                        entry.kind
                        in {
                            LedgerEntryKind.FINISH,
                            LedgerEntryKind.FAIL_CLOSED_STOP,
                        }
                        for entry in self.entries
                    )
                    == self.generation - 1
                )
            )
        ):
            raise DomainError(
                ErrorCode.CONTROL_STATE_DENIED,
                "sealed Evidence Ledger history cannot be appended",
            )
        previous = self.entries[-1].digest if self.entries else None
        entry = EvidenceLedgerEntry.create(
            ledger_id=self.ledger_id,
            sequence=len(self.entries) + 1,
            kind=kind,
            subject_id=subject_id,
            subject_digest=subject_digest,
            references=references,
            details=details,
            previous_entry_digest=previous,
        )
        entries = (*self.entries, entry)
        prefix = digest_of(
            [
                "EVIDENCE_LEDGER_PREFIX@1",
                self.ledger_id.value,
                self.request_digest.value,
                self.generation,
                self.parent_seal_digest.value if self.parent_seal_digest else None,
                tuple(item.digest.value for item in entries),
            ]
        )
        candidate = replace(self, entries=entries, prefix_digest=prefix)
        if maximum_bytes is not None and candidate.serialized_bytes > maximum_bytes:
            raise DomainError(
                ErrorCode.BUDGET_EXHAUSTED,
                "Evidence Ledger byte fuse is exhausted",
            )
        return candidate

    @property
    def serialized_bytes(self) -> int:
        return len(
            canonical_json_bytes(
                {
                    "ledger_id": self.ledger_id.value,
                    "request_digest": self.request_digest.value,
                    "generation": self.generation,
                    "parent_seal_digest": (
                        self.parent_seal_digest.value if self.parent_seal_digest else None
                    ),
                    "entries": tuple(item.model_view() for item in self.entries),
                    "terminal_status": self.terminal_status.value,
                    "prefix_digest": self.prefix_digest.value,
                }
            )
        )

    def seal(self, status: LedgerTerminalStatus) -> "EvidenceLedger":
        self.validate_integrity()
        if status is LedgerTerminalStatus.ACTIVE:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT, "active Evidence Ledger cannot be sealed"
            )
        if self.terminal_status is not LedgerTerminalStatus.ACTIVE or self.seal_digest:
            raise DomainError(
                ErrorCode.CONTROL_STATE_DENIED,
                "Evidence Ledger can be sealed exactly once",
            )
        if not self.entries or self.entries[-1].kind not in {
            LedgerEntryKind.FINISH,
            LedgerEntryKind.FAIL_CLOSED_STOP,
        }:
            raise DomainError(
                ErrorCode.CONTROL_STATE_DENIED,
                "Evidence Ledger requires a recorded terminal decision before sealing",
            )
        if (
            status is LedgerTerminalStatus.FINISHED
            and self.entries[-1].kind is not LedgerEntryKind.FINISH
        ) or (
            status is LedgerTerminalStatus.FAILED_CLOSED
            and self.entries[-1].kind is not LedgerEntryKind.FAIL_CLOSED_STOP
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Evidence Ledger terminal status disagrees with its final entry",
            )
        seal = digest_of(
            [
                "EVIDENCE_LEDGER_SEAL@1",
                self.ledger_id.value,
                self.generation,
                self.prefix_digest.value,
                status.value,
            ]
        )
        return replace(self, terminal_status=status, seal_digest=seal)

    def successor(
        self,
        *,
        verification_request_id: StableId,
        verification_request_digest: Digest,
        prior_package_digest: Digest,
        maximum_bytes: int,
        verification_details: Mapping[str, str] | None = None,
    ) -> "EvidenceLedger":
        self.validate_integrity()
        if self.terminal_status is not LedgerTerminalStatus.FINISHED or not self.seal_digest:
            raise DomainError(
                ErrorCode.CONTROL_STATE_DENIED,
                "verification requires a finished and sealed Evidence Ledger",
            )
        successor = EvidenceLedger(
            ledger_id=self.ledger_id,
            request_digest=self.request_digest,
            generation=self.generation + 1,
            parent_seal_digest=self.seal_digest,
            entries=self.entries,
            terminal_status=LedgerTerminalStatus.ACTIVE,
            prefix_digest=digest_of(
                [
                    "EVIDENCE_LEDGER_PREFIX@1",
                    self.ledger_id.value,
                    self.request_digest.value,
                    self.generation + 1,
                    self.seal_digest.value,
                    tuple(item.digest.value for item in self.entries),
                ]
            ),
            seal_digest=None,
        )
        supplied_details = dict(verification_details or {})
        reserved_details = {"parent_generation", "prior_package_digest"}
        if reserved_details & set(supplied_details):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "verification details cannot replace Ledger predecessor coordinates",
            )
        details = {
            "parent_generation": str(self.generation),
            "prior_package_digest": prior_package_digest.value,
            **supplied_details,
        }
        return successor.append(
            kind=LedgerEntryKind.VERIFICATION_REQUEST,
            subject_id=verification_request_id.value,
            subject_digest=verification_request_digest,
            references=(self.seal_digest.value, prior_package_digest.value),
            details=details,
            maximum_bytes=maximum_bytes,
        )

    def model_view(self) -> dict[str, object]:
        return {
            "ledger_id": self.ledger_id.value,
            "generation": self.generation,
            "revision": len(self.entries),
            "prefix_digest": self.prefix_digest.value,
            "parent_seal_digest": (
                self.parent_seal_digest.value if self.parent_seal_digest else None
            ),
            "terminal_status": self.terminal_status.value,
            "entries": [item.model_view() for item in self.entries],
        }


@dataclass(frozen=True, slots=True)
class MaterialObservation:
    observation_id: StableId
    checklist_item_id: str
    kind: MaterialObservationKind
    statement: str
    evidence_references: tuple[str, ...]
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        checklist_item_id: str,
        kind: MaterialObservationKind,
        statement: str,
        evidence_references: Sequence[str],
    ) -> "MaterialObservation":
        if not isinstance(kind, MaterialObservationKind):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "material observation kind must use the controlled vocabulary",
            )
        references = tuple(
            _reference(value, "material observation evidence reference")
            for value in evidence_references
        )
        if not references or len(references) != len(set(references)):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "material observation requires unique evidence references",
            )
        core = {
            "checklist_item_id": _reference(
                checklist_item_id, "material observation checklist item ID"
            ),
            "kind": kind.value,
            "statement": _text(
                statement, "material observation statement", maximum_bytes=8_192
            ),
            "evidence_references": references,
        }
        digest = digest_of(["MATERIAL_OBSERVATION@1", core])
        return cls(
            observation_id=_stable_id("material_observation", core),
            checklist_item_id=core["checklist_item_id"],
            kind=kind,
            statement=core["statement"],
            evidence_references=references,
            digest=digest,
        )

    def model_view(self) -> dict[str, object]:
        return {
            "observation_id": self.observation_id.value,
            "checklist_item_id": self.checklist_item_id,
            "kind": self.kind.value,
            "statement": self.statement,
            "evidence_references": list(self.evidence_references),
            "digest": self.digest.value,
        }


@dataclass(frozen=True, slots=True)
class ChecklistDisposition:
    checklist_item_id: str
    outcome: ChecklistOutcome
    evidence_references: tuple[str, ...]
    explanation: str
    material_observations: tuple[MaterialObservation, ...]
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        checklist_item_id: str,
        outcome: ChecklistOutcome,
        evidence_references: Sequence[str],
        explanation: str,
        material_observations: Sequence[MaterialObservation],
    ) -> "ChecklistDisposition":
        references = tuple(
            _reference(value, "checklist evidence reference")
            for value in evidence_references
        )
        if not references:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "every checklist disposition requires an evidence or boundary reference",
            )
        if len(set(references)) != len(references):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "checklist disposition contains duplicate references",
            )
        normalized_checklist_item_id = _reference(
            checklist_item_id, "checklist item ID"
        )
        observations = tuple(material_observations)
        if (
            not observations
            or len(observations) > MAXIMUM_MATERIAL_OBSERVATIONS_PER_DISPOSITION
        ):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "checklist disposition exceeds its material observation bounds",
            )
        if len({item.observation_id for item in observations}) != len(observations):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "checklist disposition contains duplicate material observations",
            )
        for observation in observations:
            expected_observation = MaterialObservation.create(
                checklist_item_id=observation.checklist_item_id,
                kind=observation.kind,
                statement=observation.statement,
                evidence_references=observation.evidence_references,
            )
            if observation != expected_observation:
                raise DomainError(
                    ErrorCode.PROVIDER_RESPONSE_INVALID,
                    "material observation identity is invalid",
                )
            if observation.checklist_item_id != normalized_checklist_item_id:
                raise DomainError(
                    ErrorCode.INVALID_ARGUMENT,
                    "material observation crosses its checklist disposition",
                )
            if not set(observation.evidence_references).issubset(references):
                raise DomainError(
                    ErrorCode.INVALID_ARGUMENT,
                    "material observation evidence must be retained by its disposition",
                )
            if (
                outcome is ChecklistOutcome.SUPPORTED
                and observation.kind is MaterialObservationKind.LIMITATION
            ) or (
                outcome is not ChecklistOutcome.SUPPORTED
                and observation.kind is not MaterialObservationKind.LIMITATION
            ):
                raise DomainError(
                    ErrorCode.INVALID_ARGUMENT,
                    "material observation kind must agree with its checklist outcome",
                )
        core = {
            "checklist_item_id": normalized_checklist_item_id,
            "outcome": outcome.value,
            "evidence_references": references,
            "explanation": _text(
                explanation, "checklist disposition explanation", maximum_bytes=8_192
            ),
            "material_observations": tuple(
                item.digest.value for item in observations
            ),
        }
        return cls(
            checklist_item_id=core["checklist_item_id"],
            outcome=outcome,
            evidence_references=references,
            explanation=core["explanation"],
            material_observations=observations,
            digest=digest_of(["CHECKLIST_DISPOSITION@2", core]),
        )


@dataclass(frozen=True, slots=True)
class InvestigationStepProposal:
    proposal_id: StableId
    investigation_kind: InvestigationKind
    attempt_id: StableId
    role_context_id: StableId
    request_digest: Digest
    step_index: int
    ledger_id: StableId
    ledger_generation: int
    ledger_revision: int
    ledger_prefix_digest: Digest
    operation: InvestigationOperation
    checklist_item_ids: tuple[str, ...]
    evidence_class: EngineeringEvidenceClass | None
    query: str | None
    locator_reference: StableId | None
    basis_entry_ids: tuple[StableId, ...]
    unknown_to_reduce: str
    finish_dispositions: tuple[ChecklistDisposition, ...]
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        investigation_kind: InvestigationKind,
        attempt_id: StableId,
        role_context_id: StableId,
        request_digest: Digest,
        step_index: int,
        ledger_id: StableId,
        ledger_generation: int,
        ledger_revision: int,
        ledger_prefix_digest: Digest,
        operation: InvestigationOperation,
        checklist_item_ids: Sequence[str],
        basis_entry_ids: Sequence[StableId],
        unknown_to_reduce: str,
        evidence_class: EngineeringEvidenceClass | None = None,
        query: str | None = None,
        locator_reference: StableId | None = None,
        finish_dispositions: Sequence[ChecklistDisposition] = (),
    ) -> "InvestigationStepProposal":
        if step_index < 1 or ledger_generation < 1 or ledger_revision < 1:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "investigation step and Ledger coordinates must be positive",
            )
        checklist = tuple(
            _reference(value, "proposal checklist item ID")
            for value in checklist_item_ids
        )
        if not checklist or len(set(checklist)) != len(checklist):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "investigation proposal checklist references must be non-empty and unique",
            )
        basis = tuple(basis_entry_ids)
        if not basis or len(set(basis)) != len(basis):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "investigation proposal must bind unique prior Ledger entries",
            )
        dispositions = tuple(finish_dispositions)
        if operation is InvestigationOperation.FINISH:
            if (
                evidence_class is not None
                or query is not None
                or locator_reference is not None
                or not dispositions
            ):
                raise DomainError(
                    ErrorCode.INVALID_ARGUMENT,
                    "FINISH may only carry complete checklist dispositions",
                )
        elif operation is InvestigationOperation.SEARCH:
            if evidence_class is None or query is None or locator_reference is not None or dispositions:
                raise DomainError(
                    ErrorCode.INVALID_ARGUMENT,
                    "search proposal requires an evidence class and query only",
                )
            query = _text(query, "source search query", maximum_bytes=2_048)
        elif operation in {InvestigationOperation.READ, InvestigationOperation.PARSE}:
            if evidence_class is None or query is not None or locator_reference is None or dispositions:
                raise DomainError(
                    ErrorCode.INVALID_ARGUMENT,
                    "read/parse proposal requires an evidence class and prior locator reference",
                )
        core = {
            "investigation_kind": investigation_kind.value,
            "attempt_id": attempt_id.value,
            "role_context_id": role_context_id.value,
            "request_digest": request_digest.value,
            "step_index": step_index,
            "ledger_id": ledger_id.value,
            "ledger_generation": ledger_generation,
            "ledger_revision": ledger_revision,
            "ledger_prefix_digest": ledger_prefix_digest.value,
            "operation": operation.value,
            "checklist_item_ids": checklist,
            "evidence_class": evidence_class.value if evidence_class else None,
            "query": query,
            "locator_reference": (
                locator_reference.value if locator_reference else None
            ),
            "basis_entry_ids": tuple(item.value for item in basis),
            "unknown_to_reduce": _text(
                unknown_to_reduce, "unknown to reduce", maximum_bytes=8_192
            ),
            "finish_dispositions": tuple(item.digest.value for item in dispositions),
        }
        digest = digest_of(["INVESTIGATION_STEP_PROPOSAL@1", core])
        return cls(
            proposal_id=_stable_id("investigation_proposal", core),
            investigation_kind=investigation_kind,
            attempt_id=attempt_id,
            role_context_id=role_context_id,
            request_digest=request_digest,
            step_index=step_index,
            ledger_id=ledger_id,
            ledger_generation=ledger_generation,
            ledger_revision=ledger_revision,
            ledger_prefix_digest=ledger_prefix_digest,
            operation=operation,
            checklist_item_ids=checklist,
            evidence_class=evidence_class,
            query=query,
            locator_reference=locator_reference,
            basis_entry_ids=basis,
            unknown_to_reduce=core["unknown_to_reduce"],
            finish_dispositions=dispositions,
            digest=digest,
        )


@dataclass(frozen=True, slots=True)
class RetrievalItem:
    item_id: StableId
    locator_reference: StableId
    operation_id: StableId
    ordinal: int
    evidence_class: EngineeringEvidenceClass
    path: str
    line_start: int | None
    line_end: int | None
    content: str
    content_digest: Digest
    modality: str
    coverage_complete: bool
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        operation_id: StableId,
        ordinal: int,
        evidence_class: EngineeringEvidenceClass,
        path: str,
        content: str,
        modality: str,
        coverage_complete: bool,
        line_start: int | None = None,
        line_end: int | None = None,
    ) -> "RetrievalItem":
        path = _canonical_relative_path(path)
        if ordinal < 1 or (line_start is None) != (line_end is None):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT, "retrieval item range is invalid"
            )
        if line_start is not None and (line_start < 1 or line_end < line_start):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT, "retrieval item line range is invalid"
            )
        content = _content_text(
            content, "retrieved content", maximum_bytes=2_097_152
        )
        content_digest = digest_of(["RETRIEVED_CONTENT@1", content])
        core = {
            "operation_id": operation_id.value,
            "ordinal": ordinal,
            "evidence_class": evidence_class.value,
            "path": path,
            "line_start": line_start,
            "line_end": line_end,
            "content_digest": content_digest.value,
            "modality": _reference(modality, "retrieval modality"),
            "coverage_complete": bool(coverage_complete),
        }
        item_id = _stable_id("retrieval_item", core)
        return cls(
            item_id=item_id,
            locator_reference=_stable_id(
                "source_locator", [operation_id.value, ordinal, path, line_start, line_end]
            ),
            operation_id=operation_id,
            ordinal=ordinal,
            evidence_class=evidence_class,
            path=path,
            line_start=line_start,
            line_end=line_end,
            content=content,
            content_digest=content_digest,
            modality=core["modality"],
            coverage_complete=bool(coverage_complete),
            digest=digest_of(["RETRIEVAL_ITEM@1", core]),
        )

    @property
    def display_locator(self) -> str:
        if self.line_start is None:
            return self.path
        suffix = (
            str(self.line_start)
            if self.line_start == self.line_end
            else f"{self.line_start}-{self.line_end}"
        )
        return f"{self.path}:L{suffix}"

    def model_view(self) -> dict[str, object]:
        return {
            "item_id": self.item_id.value,
            "locator_reference": self.locator_reference.value,
            "operation_id": self.operation_id.value,
            "ordinal": self.ordinal,
            "evidence_class": self.evidence_class.value,
            "locator": self.display_locator,
            "content": self.content,
            "content_digest": self.content_digest.value,
            "modality": self.modality,
            "coverage_complete": self.coverage_complete,
            "digest": self.digest.value,
        }


@dataclass(frozen=True, slots=True)
class RequiredEvidencePathLocator:
    """Application/Broker-issued authority for one already-validated exact path.

    Question Understanding may select only paths from the immutable Request
    allowlist.  Requiring the Investigation model to rediscover such a path by
    literal content search adds no authority and can strand a mandatory read.
    This locator lets the Broker expose that validated path as an opaque,
    single-use READ/PARSE capability without turning a model-supplied path into
    executable authority.
    """

    locator_reference: StableId
    attempt_id: StableId
    request_digest: Digest
    source_profile_digest: Digest
    evidence_class: EngineeringEvidenceClass
    path: str
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        attempt_id: StableId,
        request_digest: Digest,
        source_profile_digest: Digest,
        evidence_class: EngineeringEvidenceClass,
        path: str,
    ) -> "RequiredEvidencePathLocator":
        if evidence_class not in _RETRIEVAL_EVIDENCE_CLASSES:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "required evidence path locator needs a retrievable evidence class",
            )
        core = {
            "schema": ENGINEERING_QA_REQUIRED_PATH_LOCATOR_SCHEMA,
            "attempt_id": attempt_id.value,
            "request_digest": request_digest.value,
            "source_profile_digest": source_profile_digest.value,
            "evidence_class": evidence_class.value,
            "path": _canonical_relative_path(path),
        }
        return cls(
            locator_reference=_stable_id("required_path_locator", core),
            attempt_id=attempt_id,
            request_digest=request_digest,
            source_profile_digest=source_profile_digest,
            evidence_class=evidence_class,
            path=core["path"],
            digest=digest_of([ENGINEERING_QA_REQUIRED_PATH_LOCATOR_SCHEMA, core]),
        )

    def validate_identity(self) -> None:
        expected = self.create(
            attempt_id=self.attempt_id,
            request_digest=self.request_digest,
            source_profile_digest=self.source_profile_digest,
            evidence_class=self.evidence_class,
            path=self.path,
        )
        if self != expected:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "required evidence path locator identity is invalid",
            )

    def model_view(self) -> dict[str, object]:
        self.validate_identity()
        return {
            "locator_reference": self.locator_reference.value,
            "attempt_id": self.attempt_id.value,
            "evidence_class": self.evidence_class.value,
            "path": self.path,
            "digest": self.digest.value,
        }


@dataclass(frozen=True, slots=True)
class CompiledSourceOperation:
    operation_id: StableId
    broker_policy: str
    request_digest: Digest
    proposal_digest: Digest
    repository_id: StableId
    binding_id: StableId
    repository_revision: str
    source_profile_ref: str
    source_profile_digest: Digest
    operation: SourceReadOperation
    source_allowlist: tuple[str, ...]
    evidence_class_allowlist: tuple[str, ...]
    evidence_class: EngineeringEvidenceClass
    result_modality: str
    query: str | None
    path: str | None
    locator_reference: StableId | None
    maximum_files: int
    maximum_source_bytes: int
    maximum_result_items: int
    digest: Digest

    def validate_identity(self) -> None:
        if (
            not self.source_allowlist
            or self.source_allowlist
            != tuple(sorted({_canonical_relative_path(path) for path in self.source_allowlist}))
            or not self.evidence_class_allowlist
            or self.evidence_class_allowlist
            != tuple(
                sorted(
                    {
                        _canonical_relative_path(path)
                        for path in self.evidence_class_allowlist
                    }
                )
            )
            or self.evidence_class not in _RETRIEVAL_EVIDENCE_CLASSES
            or not isinstance(self.result_modality, str)
            or not _SAFE_REFERENCE.fullmatch(self.result_modality)
            or any(
                isinstance(value, bool) or not isinstance(value, int) or value < 1
                for value in (
                    self.maximum_files,
                    self.maximum_source_bytes,
                    self.maximum_result_items,
                )
            )
            or (
                self.operation is SourceReadOperation.SEARCH
                and (self.query is None or self.path is not None or self.locator_reference is not None)
            )
            or (
                self.operation in {SourceReadOperation.READ, SourceReadOperation.PARSE}
                and (self.query is not None or self.path is None or self.locator_reference is None)
            )
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "compiled Source Operation shape is invalid",
            )
        core = {
            "broker_policy": self.broker_policy,
            "request_digest": self.request_digest.value,
            "proposal_digest": self.proposal_digest.value,
            "repository_id": self.repository_id.value,
            "binding_id": self.binding_id.value,
            "repository_revision": self.repository_revision,
            "source_profile_ref": self.source_profile_ref,
            "source_profile_digest": self.source_profile_digest.value,
            "operation": self.operation.value,
            "source_allowlist": self.source_allowlist,
            "evidence_class_allowlist": self.evidence_class_allowlist,
            "evidence_class": self.evidence_class.value,
            "result_modality": self.result_modality,
            "query": self.query,
            "path": self.path,
            "locator_reference": (
                self.locator_reference.value if self.locator_reference else None
            ),
            "maximum_files": self.maximum_files,
            "maximum_source_bytes": self.maximum_source_bytes,
            "maximum_result_items": self.maximum_result_items,
        }
        if (
            self.broker_policy != ENGINEERING_QA_BROKER_POLICY
            or self.digest
            != digest_of(["COMPILED_SOURCE_OPERATION@1", core])
            or self.operation_id != _stable_id("source_operation", core)
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "compiled Source Operation identity is invalid",
            )


@dataclass(frozen=True, slots=True)
class SourceBrokerDecision:
    decision_id: StableId
    status: BrokerDecisionStatus
    request_digest: Digest
    proposal_digest: Digest
    ledger_prefix_digest: Digest
    operation_id: StableId | None
    reason_code: str
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        status: BrokerDecisionStatus,
        request_digest: Digest,
        proposal_digest: Digest,
        ledger_prefix_digest: Digest,
        operation_id: StableId | None,
        reason_code: str,
    ) -> "SourceBrokerDecision":
        if (status is BrokerDecisionStatus.AUTHORIZED) != (operation_id is not None):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Source Broker authorization and operation identity disagree",
            )
        reason_code = _reference(reason_code, "Source Broker reason code")
        core = {
            "status": status.value,
            "request_digest": request_digest.value,
            "proposal_digest": proposal_digest.value,
            "ledger_prefix_digest": ledger_prefix_digest.value,
            "operation_id": operation_id.value if operation_id else None,
            "reason_code": reason_code,
        }
        return cls(
            decision_id=_stable_id("broker_decision", core),
            status=status,
            request_digest=request_digest,
            proposal_digest=proposal_digest,
            ledger_prefix_digest=ledger_prefix_digest,
            operation_id=operation_id,
            reason_code=reason_code,
            digest=digest_of(["SOURCE_BROKER_DECISION@1", core]),
        )


@dataclass(frozen=True, slots=True)
class SourceBrokerCompilation:
    decision: SourceBrokerDecision
    operation: CompiledSourceOperation | None


@dataclass(frozen=True, slots=True)
class RetrievalResult:
    result_id: StableId
    operation_id: StableId
    operation_digest: Digest
    repository_revision: str
    status: RetrievalStatus
    items: tuple[RetrievalItem, ...]
    bytes_read: int
    files_read: int
    truncated: bool
    coverage: tuple[tuple[str, str], ...]
    failure_code: str | None
    progress_digest: Digest
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        operation: CompiledSourceOperation,
        status: RetrievalStatus,
        items: Sequence[RetrievalItem],
        bytes_read: int,
        files_read: int,
        truncated: bool,
        coverage: Mapping[str, str],
        failure_code: str | None = None,
    ) -> "RetrievalResult":
        item_tuple = tuple(items)
        if bytes_read < 0 or files_read < 0:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT, "retrieval resource usage cannot be negative"
            )
        if len({item.item_id for item in item_tuple}) != len(item_tuple):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT, "retrieval result contains duplicate items"
            )
        for item in item_tuple:
            expected_item = RetrievalItem.create(
                operation_id=item.operation_id,
                ordinal=item.ordinal,
                evidence_class=item.evidence_class,
                path=item.path,
                line_start=item.line_start,
                line_end=item.line_end,
                content=item.content,
                modality=item.modality,
                coverage_complete=item.coverage_complete,
            )
            if item != expected_item:
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "retrieval item identity is invalid",
                )
        if any(
            item.operation_id != operation.operation_id
            or item.evidence_class is not operation.evidence_class
            or item.modality != operation.result_modality
            for item in item_tuple
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "retrieval item identity, class, or modality differs from the Broker operation",
            )
        if status is RetrievalStatus.COMPLETE and (truncated or failure_code):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "complete retrieval cannot be truncated or failed",
            )
        if status in {RetrievalStatus.FAILED, RetrievalStatus.OUTCOME_UNKNOWN} and not failure_code:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "failed or unknown retrieval requires a failure code",
            )
        canonical_coverage = tuple(
            sorted(
                (
                    _reference(key, "retrieval coverage key"),
                    _text(value, "retrieval coverage value", maximum_bytes=8_192),
                )
                for key, value in coverage.items()
            )
        )
        progress_core = {
            "repository_revision": operation.repository_revision,
            "source_profile_digest": operation.source_profile_digest.value,
            "operation": operation.operation.value,
            "source_allowlist": operation.source_allowlist,
            "evidence_class_allowlist": operation.evidence_class_allowlist,
            "evidence_class": operation.evidence_class.value,
            "result_modality": operation.result_modality,
            "query": operation.query,
            "path": operation.path,
            "status": status.value,
            "items": tuple(
                {
                    "evidence_class": item.evidence_class.value,
                    "path": item.path,
                    "line_start": item.line_start,
                    "line_end": item.line_end,
                    "content_digest": item.content_digest.value,
                    "modality": item.modality,
                    "coverage_complete": item.coverage_complete,
                }
                for item in item_tuple
            ),
            "bytes_read": bytes_read,
            "files_read": files_read,
            "truncated": bool(truncated),
            "failure_code": (
                _reference(failure_code, "retrieval failure code")
                if failure_code
                else None
            ),
        }
        progress_digest = digest_of(["RETRIEVAL_PROGRESS@1", progress_core])
        core = {
            "operation_id": operation.operation_id.value,
            "operation_digest": operation.digest.value,
            "repository_revision": operation.repository_revision,
            "status": status.value,
            "items": tuple(item.digest.value for item in item_tuple),
            "bytes_read": bytes_read,
            "files_read": files_read,
            "truncated": bool(truncated),
            "coverage": canonical_coverage,
            "failure_code": progress_core["failure_code"],
            "progress_digest": progress_digest.value,
        }
        digest = digest_of(["RETRIEVAL_RESULT@1", core])
        return cls(
            result_id=_stable_id("retrieval_result", core),
            operation_id=operation.operation_id,
            operation_digest=operation.digest,
            repository_revision=operation.repository_revision,
            status=status,
            items=item_tuple,
            bytes_read=bytes_read,
            files_read=files_read,
            truncated=bool(truncated),
            coverage=canonical_coverage,
            failure_code=core["failure_code"],
            progress_digest=progress_digest,
            digest=digest,
        )

    def model_view(self) -> dict[str, object]:
        return {
            "result_id": self.result_id.value,
            "operation_id": self.operation_id.value,
            "repository_revision": self.repository_revision,
            "status": self.status.value,
            "items": [item.model_view() for item in self.items],
            "bytes_read": self.bytes_read,
            "files_read": self.files_read,
            "truncated": self.truncated,
            "coverage": dict(self.coverage),
            "failure_code": self.failure_code,
            "progress_digest": self.progress_digest.value,
            "digest": self.digest.value,
        }


class RetrievalWorker(Protocol):
    def execute(self, operation: CompiledSourceOperation) -> RetrievalResult: ...


@dataclass(frozen=True, slots=True)
class EngineeringQuestionResourceUsage:
    total_role_calls: int = 0
    investigation_role_calls: int = 0
    source_operations: int = 0
    source_files: int = 0
    source_bytes: int = 0
    repository_document_bytes: int = 0
    build_configuration_bytes: int = 0
    test_bytes: int = 0
    world_model_bytes: int = 0
    answer_attempts: int = 0
    review_attempts: int = 0
    verification_investigations: int = 0
    no_progress_steps: int = 0

    def __post_init__(self) -> None:
        values = tuple(getattr(self, field) for field in self.__dataclass_fields__)
        if any(isinstance(value, bool) or not isinstance(value, int) or value < 0 for value in values):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "Engineering QA resource usage must contain non-negative integers",
            )

    def with_retrieval(
        self,
        result: RetrievalResult,
        operation: CompiledSourceOperation,
    ) -> "EngineeringQuestionResourceUsage":
        updates = {
            "source_operations": self.source_operations + 1,
            "source_files": self.source_files + result.files_read,
            "source_bytes": self.source_bytes + result.bytes_read,
        }
        if operation.evidence_class is EngineeringEvidenceClass.REPOSITORY_DOCUMENT:
            updates["repository_document_bytes"] = (
                self.repository_document_bytes + result.bytes_read
            )
        elif operation.evidence_class is EngineeringEvidenceClass.BUILD_CONFIGURATION:
            updates["build_configuration_bytes"] = (
                self.build_configuration_bytes + result.bytes_read
            )
        elif operation.evidence_class is EngineeringEvidenceClass.TEST:
            updates["test_bytes"] = self.test_bytes + result.bytes_read
        return replace(self, **updates)


class SourceProfilePolicy(Protocol):
    binding_id: StableId
    profile_ref: str
    profile_digest: Digest

    def require_valid(self) -> None: ...

    def paths_for(
        self, evidence_class: EngineeringEvidenceClass
    ) -> tuple[str, ...]: ...

    def permits(
        self,
        *,
        evidence_class: EngineeringEvidenceClass,
        path: str | None = None,
    ) -> bool: ...

    def modality_for(
        self,
        *,
        evidence_class: EngineeringEvidenceClass,
        operation: SourceReadOperation,
    ) -> str: ...


class SourceBroker:
    """Compile an untrusted semantic proposal into one caller-proof read."""

    def __init__(self, *, source_profile: SourceProfilePolicy) -> None:
        source_profile.require_valid()
        self._source_profile = source_profile

    def registered_evidence_classes(
        self, *, request: EngineeringQuestionRequest
    ) -> tuple[EngineeringEvidenceClass, ...]:
        """Return the exact ordered retrieval registry bound to this Request."""

        self._source_profile.require_valid()
        if (
            self._source_profile.binding_id != request.binding_id
            or self._source_profile.profile_ref != request.source_profile_ref
            or self._source_profile.profile_digest != request.source_profile_digest
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Source Broker profile does not bind the current Request",
            )
        return tuple(
            evidence_class
            for evidence_class in _RETRIEVAL_EVIDENCE_CLASS_ORDER
            if self._source_profile.paths_for(evidence_class)
        )

    def evidence_class_for_path(
        self,
        *,
        request: EngineeringQuestionRequest,
        path: str,
    ) -> EngineeringEvidenceClass:
        """Resolve one required exact path through the bound Source Profile."""

        registered = self.registered_evidence_classes(request=request)
        normalized = _canonical_relative_path(path)
        matches = tuple(
            evidence_class
            for evidence_class in registered
            if self._source_profile.permits(
                evidence_class=evidence_class,
                path=normalized,
            )
        )
        if (
            not _path_allowed(normalized, request.source_allowlist)
            or len(matches) != 1
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "required evidence path is not bound to exactly one registered evidence class",
            )
        return matches[0]

    def issue_required_path_locators(
        self,
        *,
        request: EngineeringQuestionRequest,
        attempt_id: StableId,
        paths: Sequence[str],
    ) -> tuple[RequiredEvidencePathLocator, ...]:
        """Mint exact, Request-bound capabilities for mandatory read paths."""

        normalized_paths = tuple(_canonical_relative_path(path) for path in paths)
        if len(set(normalized_paths)) != len(normalized_paths):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "required evidence path locator input contains duplicate paths",
            )
        return tuple(
            RequiredEvidencePathLocator.create(
                attempt_id=attempt_id,
                request_digest=request.digest,
                source_profile_digest=request.source_profile_digest,
                evidence_class=self.evidence_class_for_path(
                    request=request,
                    path=path,
                ),
                path=path,
            )
            for path in normalized_paths
        )

    def compile(
        self,
        *,
        request: EngineeringQuestionRequest,
        proposal: InvestigationStepProposal,
        ledger: EvidenceLedger,
        locator_catalog: Mapping[StableId, RetrievalItem],
        usage: EngineeringQuestionResourceUsage,
        required_path_locator_catalog: Mapping[
            StableId, RequiredEvidencePathLocator
        ] | None = None,
    ) -> SourceBrokerCompilation:
        self._require_binding(request=request, proposal=proposal, ledger=ledger)
        self.registered_evidence_classes(request=request)
        if proposal.operation is InvestigationOperation.FINISH:
            return self._reject(
                request=request,
                proposal=proposal,
                ledger=ledger,
                reason="FINISH_IS_NOT_A_SOURCE_OPERATION",
            )
        source_operation = SourceReadOperation(proposal.operation.value)
        if proposal.evidence_class not in _RETRIEVAL_EVIDENCE_CLASSES:
            return self._reject(
                request=request,
                proposal=proposal,
                ledger=ledger,
                reason="EVIDENCE_CLASS_NOT_RETRIEVABLE",
            )
        evidence_class_allowlist = self._source_profile.paths_for(
            proposal.evidence_class
        )
        if not evidence_class_allowlist:
            return self._reject(
                request=request,
                proposal=proposal,
                ledger=ledger,
                reason="EVIDENCE_CLASS_NOT_REGISTERED_BY_SOURCE_PROFILE",
            )
        result_modality = self._source_profile.modality_for(
            evidence_class=proposal.evidence_class,
            operation=source_operation,
        )
        if source_operation not in request.registered_operations:
            return self._reject(
                request=request,
                proposal=proposal,
                ledger=ledger,
                reason="OPERATION_NOT_REGISTERED",
            )
        if _duplicates_prior_action_intent(proposal=proposal, ledger=ledger):
            return self._reject(
                request=request,
                proposal=proposal,
                ledger=ledger,
                reason="DUPLICATE_ACTION_INTENT",
            )
        if usage.source_operations >= request.limits.maximum_source_operations:
            return self._reject(
                request=request,
                proposal=proposal,
                ledger=ledger,
                reason="SOURCE_OPERATION_FUSE_EXHAUSTED",
            )
        if usage.source_files >= request.limits.maximum_source_files:
            return self._reject(
                request=request,
                proposal=proposal,
                ledger=ledger,
                reason="SOURCE_FILE_FUSE_EXHAUSTED",
            )
        remaining_bytes = request.limits.maximum_source_bytes - usage.source_bytes
        if remaining_bytes < 1:
            return self._reject(
                request=request,
                proposal=proposal,
                ledger=ledger,
                reason="SOURCE_BYTE_FUSE_EXHAUSTED",
            )
        path: str | None = None
        locator_reference: StableId | None = None
        if source_operation in {SourceReadOperation.READ, SourceReadOperation.PARSE}:
            locator_reference = proposal.locator_reference
            locator = locator_catalog.get(locator_reference) if locator_reference else None
            required_path_locator = (
                required_path_locator_catalog.get(locator_reference)
                if locator_reference and required_path_locator_catalog is not None
                else None
            )
            if locator is not None and required_path_locator is not None:
                return self._reject(
                    request=request,
                    proposal=proposal,
                    ledger=ledger,
                    reason="LOCATOR_AUTHORITY_AMBIGUOUS",
                )
            if locator is None and required_path_locator is None:
                return self._reject(
                    request=request,
                    proposal=proposal,
                    ledger=ledger,
                    reason="LOCATOR_NOT_ISSUED_BY_CURRENT_LEDGER",
                )
            if locator is not None:
                issued_item_references = {
                    reference
                    for entry in ledger.entries
                    if entry.kind is LedgerEntryKind.SOURCE_RESULT
                    for reference in entry.references
                }
                if locator.item_id.value not in issued_item_references:
                    return self._reject(
                        request=request,
                        proposal=proposal,
                        ledger=ledger,
                        reason="LOCATOR_NOT_ISSUED_BY_CURRENT_LEDGER",
                    )
                locator_evidence_class = locator.evidence_class
                path = locator.path
            else:
                assert required_path_locator is not None
                required_path_locator.validate_identity()
                expected_required_path_locator = RequiredEvidencePathLocator.create(
                    attempt_id=proposal.attempt_id,
                    request_digest=request.digest,
                    source_profile_digest=request.source_profile_digest,
                    evidence_class=required_path_locator.evidence_class,
                    path=required_path_locator.path,
                )
                if required_path_locator != expected_required_path_locator:
                    return self._reject(
                        request=request,
                        proposal=proposal,
                        ledger=ledger,
                        reason="REQUIRED_PATH_LOCATOR_BINDING_MISMATCH",
                    )
                locator_evidence_class = required_path_locator.evidence_class
                path = required_path_locator.path
            if locator_evidence_class is not proposal.evidence_class:
                return self._reject(
                    request=request,
                    proposal=proposal,
                    ledger=ledger,
                    reason="LOCATOR_EVIDENCE_CLASS_MISMATCH",
                )
            if not _path_allowed(path, request.source_allowlist):
                return self._reject(
                    request=request,
                    proposal=proposal,
                    ledger=ledger,
                    reason="LOCATOR_OUTSIDE_ALLOWLIST",
                )
            if not self._source_profile.permits(
                evidence_class=proposal.evidence_class,
                path=path,
            ):
                return self._reject(
                    request=request,
                    proposal=proposal,
                    ledger=ledger,
                    reason="LOCATOR_EVIDENCE_CLASS_PROFILE_MISMATCH",
                )
        per_class_limit = request.limits.maximum_source_bytes
        if proposal.evidence_class is EngineeringEvidenceClass.REPOSITORY_DOCUMENT:
            per_class_limit = (
                request.limits.maximum_repository_document_bytes
                - usage.repository_document_bytes
            )
        elif proposal.evidence_class is EngineeringEvidenceClass.BUILD_CONFIGURATION:
            per_class_limit = (
                request.limits.maximum_build_configuration_bytes
                - usage.build_configuration_bytes
            )
        elif proposal.evidence_class is EngineeringEvidenceClass.TEST:
            per_class_limit = request.limits.maximum_test_bytes - usage.test_bytes
        if per_class_limit < 1:
            return self._reject(
                request=request,
                proposal=proposal,
                ledger=ledger,
                reason="EVIDENCE_CLASS_BYTE_FUSE_EXHAUSTED",
            )
        operation_core = {
            "broker_policy": ENGINEERING_QA_BROKER_POLICY,
            "request_digest": request.digest.value,
            "proposal_digest": proposal.digest.value,
            "repository_id": request.repository_id.value,
            "binding_id": request.binding_id.value,
            "repository_revision": request.repository_revision,
            "source_profile_ref": request.source_profile_ref,
            "source_profile_digest": request.source_profile_digest.value,
            "operation": source_operation.value,
            "source_allowlist": request.source_allowlist,
            "evidence_class_allowlist": evidence_class_allowlist,
            "evidence_class": proposal.evidence_class.value,
            "result_modality": result_modality,
            "query": proposal.query,
            "path": path,
            "locator_reference": (
                locator_reference.value if locator_reference else None
            ),
            "maximum_files": min(
                request.limits.maximum_source_files - usage.source_files, 64
            ),
            "maximum_source_bytes": min(remaining_bytes, per_class_limit),
            "maximum_result_items": min(
                request.limits.maximum_support_items, 1_024
            ),
        }
        operation_digest = digest_of(["COMPILED_SOURCE_OPERATION@1", operation_core])
        operation = CompiledSourceOperation(
            operation_id=_stable_id("source_operation", operation_core),
            broker_policy=ENGINEERING_QA_BROKER_POLICY,
            request_digest=request.digest,
            proposal_digest=proposal.digest,
            repository_id=request.repository_id,
            binding_id=request.binding_id,
            repository_revision=request.repository_revision,
            source_profile_ref=request.source_profile_ref,
            source_profile_digest=request.source_profile_digest,
            operation=source_operation,
            source_allowlist=request.source_allowlist,
            evidence_class_allowlist=evidence_class_allowlist,
            evidence_class=proposal.evidence_class,
            result_modality=result_modality,
            query=proposal.query,
            path=path,
            locator_reference=locator_reference,
            maximum_files=operation_core["maximum_files"],
            maximum_source_bytes=operation_core["maximum_source_bytes"],
            maximum_result_items=operation_core["maximum_result_items"],
            digest=operation_digest,
        )
        decision = SourceBrokerDecision.create(
            status=BrokerDecisionStatus.AUTHORIZED,
            request_digest=request.digest,
            proposal_digest=proposal.digest,
            ledger_prefix_digest=ledger.prefix_digest,
            operation_id=operation.operation_id,
            reason_code="POLICY_COMPILED",
        )
        return SourceBrokerCompilation(decision, operation)

    @staticmethod
    def _require_binding(
        *,
        request: EngineeringQuestionRequest,
        proposal: InvestigationStepProposal,
        ledger: EvidenceLedger,
    ) -> None:
        ledger.validate_integrity()
        if (
            proposal.request_digest != request.digest
            or proposal.ledger_id != ledger.ledger_id
            or proposal.ledger_generation != ledger.generation
            or proposal.ledger_revision != len(ledger.entries)
            or proposal.ledger_prefix_digest != ledger.prefix_digest
            or ledger.request_digest != request.digest
            or ledger.terminal_status is not LedgerTerminalStatus.ACTIVE
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Source Broker proposal is not bound to the current request and Ledger prefix",
            )

    @staticmethod
    def _reject(
        *,
        request: EngineeringQuestionRequest,
        proposal: InvestigationStepProposal,
        ledger: EvidenceLedger,
        reason: str,
    ) -> SourceBrokerCompilation:
        return SourceBrokerCompilation(
            SourceBrokerDecision.create(
                status=BrokerDecisionStatus.REJECTED,
                request_digest=request.digest,
                proposal_digest=proposal.digest,
                ledger_prefix_digest=ledger.prefix_digest,
                operation_id=None,
                reason_code=reason,
            ),
            None,
        )


def _consumed_full_content_paths(
    retrieval_results: Sequence[RetrievalResult],
) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                item.path
                for result in retrieval_results
                for item in result.items
                if item.line_start is None and item.coverage_complete
            }
        )
    )


def _prior_action_intents(
    *,
    ledger: EvidenceLedger,
    attempt_id: StableId,
) -> tuple[dict[str, object], ...]:
    intents: list[dict[str, object]] = []
    for entry in ledger.entries:
        if entry.kind is not LedgerEntryKind.INVESTIGATION_PROPOSAL:
            continue
        details = dict(entry.details)
        if details.get("attempt_id") != attempt_id.value:
            continue
        try:
            step_index = int(details["step_index"])
            operation = details["operation"]
        except (KeyError, TypeError, ValueError) as exc:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "investigation Proposal Ledger entry lacks its action intent",
            ) from exc
        intents.append(
            {
                "proposal_id": entry.subject_id,
                "step_index": step_index,
                "operation": operation,
                "evidence_class": details.get("evidence_class"),
                "query": details.get("query"),
                "locator_reference": details.get("locator_reference"),
            }
        )
    return tuple(intents)


def _duplicates_prior_action_intent(
    *,
    proposal: InvestigationStepProposal,
    ledger: EvidenceLedger,
) -> bool:
    for intent in _prior_action_intents(
        ledger=ledger,
        attempt_id=proposal.attempt_id,
    ):
        prior_operation = intent["operation"]
        if (
            proposal.operation is InvestigationOperation.SEARCH
            and prior_operation == InvestigationOperation.SEARCH.value
            and intent["evidence_class"]
            == (proposal.evidence_class.value if proposal.evidence_class else None)
            and intent["query"] == proposal.query
        ):
            return True
        if (
            proposal.operation
            in {InvestigationOperation.READ, InvestigationOperation.PARSE}
            and prior_operation
            in {
                InvestigationOperation.READ.value,
                InvestigationOperation.PARSE.value,
            }
            and intent["locator_reference"]
            == (
                proposal.locator_reference.value
                if proposal.locator_reference
                else None
            )
        ):
            return True
    return False


def _eligible_locator_references(
    retrieval_results: Sequence[RetrievalResult],
    *,
    required_evidence_paths: Sequence[str] = (),
    required_path_locators: Sequence[RequiredEvidencePathLocator] = (),
    attempt_id: StableId | None = None,
    request_digest: Digest | None = None,
) -> tuple[StableId, ...]:
    consumed_paths = set(_consumed_full_content_paths(retrieval_results))
    eligible_items = tuple(
        item
        for result in retrieval_results
        for item in result.items
        if item.line_start is not None and item.path not in consumed_paths
    )
    unread_required_paths = {
        path for path in required_evidence_paths if path not in consumed_paths
    }
    direct_locators = tuple(required_path_locators)
    if required_evidence_paths:
        if attempt_id is None or request_digest is None:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "required evidence path locators lack their Request binding",
            )
        for locator in direct_locators:
            locator.validate_identity()
        if (
            len({item.locator_reference for item in direct_locators})
            != len(direct_locators)
            or len({item.path for item in direct_locators}) != len(direct_locators)
            or {item.path for item in direct_locators}
            != set(required_evidence_paths)
            or any(
                item.attempt_id != attempt_id
                or item.request_digest != request_digest
                for item in direct_locators
            )
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "required evidence path locators do not bind the exact mandatory-read set",
            )
    elif direct_locators:
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "required evidence path locators exist without mandatory-read paths",
        )
    if unread_required_paths:
        eligible_items = tuple(
            item for item in eligible_items if item.path in unread_required_paths
        )
        direct_references = tuple(
            item.locator_reference
            for item in direct_locators
            if item.path in unread_required_paths
        )
    else:
        direct_references = ()
    issued_references = tuple(item.locator_reference for item in eligible_items)
    return tuple(dict.fromkeys((*direct_references, *issued_references)))


def _evidence_class_closure(
    *,
    registered: Sequence[EngineeringEvidenceClass],
    required: Sequence[EngineeringEvidenceClass],
    investigated: Sequence[EngineeringEvidenceClass],
) -> tuple[
    tuple[EngineeringEvidenceClass, ...],
    tuple[EngineeringEvidenceClass, ...],
]:
    registered_tuple = tuple(registered)
    required_tuple = tuple(required)
    investigated_tuple = tuple(investigated)
    if (
        len(set(registered_tuple)) != len(registered_tuple)
        or len(set(required_tuple)) != len(required_tuple)
        or len(set(investigated_tuple)) != len(investigated_tuple)
        or any(
            not isinstance(item, EngineeringEvidenceClass)
            or item not in _RETRIEVAL_EVIDENCE_CLASSES
            for item in (
                *registered_tuple,
                *required_tuple,
                *investigated_tuple,
            )
        )
        or not set(investigated_tuple).issubset(registered_tuple)
    ):
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "investigation evidence-class closure inputs are invalid",
        )
    registered_set = set(registered_tuple)
    investigated_set = set(investigated_tuple)
    untried = tuple(
        item
        for item in required_tuple
        if item in registered_set and item not in investigated_set
    )
    unregistered = tuple(
        item for item in required_tuple if item not in registered_set
    )
    return untried, unregistered


@dataclass(frozen=True, slots=True)
class ChecklistDispositionReferenceEligibility:
    support_references: tuple[str, ...]
    boundary_references: tuple[str, ...]
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        support_references: Sequence[str],
        boundary_references: Sequence[str],
    ) -> "ChecklistDispositionReferenceEligibility":
        support = tuple(
            sorted(
                {
                    _reference(value, "admissible support disposition reference")
                    for value in support_references
                }
            )
        )
        boundary = tuple(
            sorted(
                {
                    _reference(value, "admissible boundary disposition reference")
                    for value in boundary_references
                }
            )
        )
        if set(support) & set(boundary):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "a disposition reference cannot be both support and boundary evidence",
            )
        core = {
            "support_references": support,
            "boundary_references": boundary,
        }
        return cls(
            support_references=support,
            boundary_references=boundary,
            digest=digest_of(
                ["CHECKLIST_DISPOSITION_REFERENCE_ELIGIBILITY@1", core]
            ),
        )


def _disposition_reference_eligibility(
    *,
    cognition: WorldModelCognitionContext,
    ledger: EvidenceLedger,
    retrieval_results: Sequence[RetrievalResult],
    broker_decisions: Sequence[SourceBrokerDecision],
) -> ChecklistDispositionReferenceEligibility:
    support: list[str] = []
    boundary: list[str] = []

    for item in cognition.items:
        if (
            cognition.alignment is RevisionAlignment.ALIGNED
            and item.dimension
            not in {CognitionDimension.COVERAGE, CognitionDimension.UNKNOWN}
            and item.support_references
        ):
            support.append(item.item_id.value)
        else:
            boundary.append(item.item_id.value)
    boundary.extend(
        f"cognition-conflict-{index}"
        for index, _ in enumerate(cognition.conflicts, 1)
    )
    boundary.extend(
        f"cognition-unknown-{index}"
        for index, _ in enumerate(cognition.unknowns, 1)
    )

    operation_names = {
        entry.subject_id: dict(entry.details).get("operation")
        for entry in ledger.entries
        if entry.kind is LedgerEntryKind.SOURCE_OPERATION
    }
    for result in retrieval_results:
        operation_name = operation_names.get(result.operation_id.value)
        can_support = (
            result.status is RetrievalStatus.COMPLETE
            and not result.truncated
            and operation_name
            in {SourceReadOperation.READ.value, SourceReadOperation.PARSE.value}
        )
        if can_support:
            if result.items:
                for item in result.items:
                    (support if item.coverage_complete else boundary).append(
                        item.item_id.value
                    )
            else:
                boundary.append(result.result_id.value)
        elif result.items:
            boundary.extend(item.item_id.value for item in result.items)
        else:
            boundary.append(result.result_id.value)

    boundary.extend(
        decision.decision_id.value
        for decision in broker_decisions
        if decision.status is BrokerDecisionStatus.REJECTED
    )
    boundary.extend(
        entry.entry_id.value
        for entry in ledger.entries
        if entry.kind
        in {
            LedgerEntryKind.GAP,
            LedgerEntryKind.VERIFICATION_REQUEST,
            LedgerEntryKind.RESOURCE_RECEIPT,
            LedgerEntryKind.FAIL_CLOSED_STOP,
        }
    )
    return ChecklistDispositionReferenceEligibility.create(
        support_references=support,
        boundary_references=boundary,
    )


@dataclass(frozen=True, slots=True)
class InitialInvestigationInput:
    attempt_id: StableId
    role_context_id: StableId
    step_index: int
    request: EngineeringQuestionRequest
    understanding: QuestionUnderstanding
    cognition: WorldModelCognitionContext
    ledger: EvidenceLedger
    retrieval_results: tuple[RetrievalResult, ...]
    disposition_reference_eligibility: ChecklistDispositionReferenceEligibility
    registered_evidence_classes: tuple[EngineeringEvidenceClass, ...] = ()
    required_evidence_classes: tuple[EngineeringEvidenceClass, ...] = ()
    investigated_evidence_classes: tuple[EngineeringEvidenceClass, ...] = ()
    required_evidence_paths: tuple[str, ...] = ()
    required_path_locators: tuple[RequiredEvidencePathLocator, ...] = ()

    @property
    def required_basis_entry_id(self) -> StableId:
        return self.ledger.entries[-1].entry_id

    @property
    def eligible_locator_references(self) -> tuple[StableId, ...]:
        return _eligible_locator_references(
            self.retrieval_results,
            required_evidence_paths=self.required_evidence_paths,
            required_path_locators=self.required_path_locators,
            attempt_id=self.attempt_id,
            request_digest=self.request.digest,
        )

    @property
    def eligible_required_path_locators(
        self,
    ) -> tuple[RequiredEvidencePathLocator, ...]:
        eligible = set(self.eligible_locator_references)
        return tuple(
            item
            for item in self.required_path_locators
            if item.locator_reference in eligible
        )

    @property
    def consumed_full_content_paths(self) -> tuple[str, ...]:
        return _consumed_full_content_paths(self.retrieval_results)

    @property
    def unread_required_evidence_paths(self) -> tuple[str, ...]:
        consumed = set(self.consumed_full_content_paths)
        return tuple(
            path for path in self.required_evidence_paths if path not in consumed
        )

    @property
    def remaining_initial_investigation_calls_including_current(self) -> int:
        return max(
            0,
            self.request.limits.maximum_initial_investigation_calls
            - self.step_index
            + 1,
        )

    @property
    def prior_action_intents(self) -> tuple[dict[str, object], ...]:
        return _prior_action_intents(
            ledger=self.ledger,
            attempt_id=self.attempt_id,
        )

    @property
    def untried_required_evidence_classes(
        self,
    ) -> tuple[EngineeringEvidenceClass, ...]:
        return _evidence_class_closure(
            registered=self.registered_evidence_classes,
            required=self.required_evidence_classes,
            investigated=self.investigated_evidence_classes,
        )[0]

    @property
    def unregistered_required_evidence_classes(
        self,
    ) -> tuple[EngineeringEvidenceClass, ...]:
        return _evidence_class_closure(
            registered=self.registered_evidence_classes,
            required=self.required_evidence_classes,
            investigated=self.investigated_evidence_classes,
        )[1]

    def model_view(self) -> dict[str, object]:
        return {
            "role": "INITIAL_INVESTIGATION",
            "attempt_id": self.attempt_id.value,
            "role_context_id": self.role_context_id.value,
            "step_index": self.step_index,
            "required_basis_entry_id": self.required_basis_entry_id.value,
            "eligible_locator_references": [
                item.value for item in self.eligible_locator_references
            ],
            "eligible_required_path_locators": [
                item.model_view()
                for item in self.eligible_required_path_locators
            ],
            "consumed_full_content_paths": list(self.consumed_full_content_paths),
            "prior_action_intents": list(self.prior_action_intents),
            "registered_evidence_classes": [
                item.value for item in self.registered_evidence_classes
            ],
            "required_evidence_classes": [
                item.value for item in self.required_evidence_classes
            ],
            "investigated_evidence_classes": [
                item.value for item in self.investigated_evidence_classes
            ],
            "untried_required_evidence_classes": [
                item.value for item in self.untried_required_evidence_classes
            ],
            "unregistered_required_evidence_classes": [
                item.value for item in self.unregistered_required_evidence_classes
            ],
            "required_evidence_paths": list(self.required_evidence_paths),
            "unread_required_evidence_paths": list(
                self.unread_required_evidence_paths
            ),
            "maximum_initial_investigation_calls": (
                self.request.limits.maximum_initial_investigation_calls
            ),
            "remaining_initial_investigation_calls_including_current": (
                self.remaining_initial_investigation_calls_including_current
            ),
            "admissible_support_references": list(
                self.disposition_reference_eligibility.support_references
            ),
            "admissible_boundary_references": list(
                self.disposition_reference_eligibility.boundary_references
            ),
            "request": self.request.investigation_control_view(),
            "question_understanding": self.understanding.model_view(),
            "world_model_cognition_context": self.cognition.model_view(),
            "evidence_ledger": self.ledger.model_view(),
            "typed_retrieval_results": [
                item.model_view() for item in self.retrieval_results
            ],
        }


class InitialInvestigationRole(Protocol):
    def propose(
        self, investigation_input: InitialInvestigationInput
    ) -> InvestigationStepProposal: ...


@dataclass(frozen=True, slots=True)
class SupportCitationEntry:
    entry_id: StableId
    source_reference: str
    origin_class: str
    evidence_class: EngineeringEvidenceClass
    modality: str
    context_ref: str
    repository_revision: str
    locator: str
    content: str
    content_digest: Digest
    support_references: tuple[str, ...]
    coverage: str
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        source_reference: str,
        origin_class: str,
        evidence_class: EngineeringEvidenceClass,
        modality: str,
        context_ref: str,
        repository_revision: str,
        locator: str,
        content: str,
        content_digest: Digest,
        support_references: Sequence[str],
        coverage: str,
    ) -> "SupportCitationEntry":
        supports = tuple(
            _reference(value, "support/citation reference")
            for value in support_references
        )
        if not supports:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "support/citation entry requires an actual support reference",
            )
        core = {
            "source_reference": _reference(
                source_reference, "support source reference"
            ),
            "origin_class": _reference(origin_class, "support origin class"),
            "evidence_class": evidence_class.value,
            "modality": _reference(modality, "support modality"),
            "context_ref": _text(
                context_ref, "support Context reference", maximum_bytes=4_096
            ),
            "repository_revision": _text(
                repository_revision, "support repository revision", maximum_bytes=64
            ).casefold(),
            "locator": _text(locator, "support locator", maximum_bytes=4_096),
            "content": _content_text(
                content, "support content", maximum_bytes=2_097_152
            ),
            "content_digest": content_digest.value,
            "support_references": supports,
            "coverage": _text(coverage, "support coverage", maximum_bytes=8_192),
        }
        if not _FULL_GIT_OID.fullmatch(core["repository_revision"]):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "support entry repository revision must be exact",
            )
        digest = digest_of(["SUPPORT_CITATION_ENTRY@1", core])
        return cls(
            entry_id=_stable_id("support_entry", core),
            source_reference=core["source_reference"],
            origin_class=core["origin_class"],
            evidence_class=evidence_class,
            modality=core["modality"],
            context_ref=core["context_ref"],
            repository_revision=core["repository_revision"],
            locator=core["locator"],
            content=core["content"],
            content_digest=content_digest,
            support_references=supports,
            coverage=core["coverage"],
            digest=digest,
        )

    def model_view(self) -> dict[str, object]:
        return {
            "entry_id": self.entry_id.value,
            "source_reference": self.source_reference,
            "origin_class": self.origin_class,
            "evidence_class": self.evidence_class.value,
            "modality": self.modality,
            "context_ref": self.context_ref,
            "repository_revision": self.repository_revision,
            "locator": self.locator,
            "content": self.content,
            "content_digest": self.content_digest.value,
            "support_references": list(self.support_references),
            "coverage": self.coverage,
            "digest": self.digest.value,
        }


@dataclass(frozen=True, slots=True)
class BoundaryAuditEntry:
    entry_id: StableId
    source_reference: str
    kind: PackageBoundaryKind
    evidence_class: EngineeringEvidenceClass | None
    repository_revision: str
    locator: str | None
    description: str
    content_digest: Digest | None
    affirmative_claim_support_allowed: bool
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        source_reference: str,
        kind: PackageBoundaryKind,
        repository_revision: str,
        description: str,
        evidence_class: EngineeringEvidenceClass | None = None,
        locator: str | None = None,
        content_digest: Digest | None = None,
    ) -> "BoundaryAuditEntry":
        core = {
            "source_reference": _reference(
                source_reference, "boundary source reference"
            ),
            "kind": kind.value,
            "evidence_class": evidence_class.value if evidence_class else None,
            "repository_revision": _text(
                repository_revision, "boundary repository revision", maximum_bytes=64
            ).casefold(),
            "locator": (
                _text(locator, "boundary locator", maximum_bytes=4_096)
                if locator
                else None
            ),
            "description": _text(
                description, "boundary description", maximum_bytes=16_384
            ),
            "content_digest": content_digest.value if content_digest else None,
            "affirmative_claim_support_allowed": False,
        }
        if not _FULL_GIT_OID.fullmatch(core["repository_revision"]):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "boundary entry repository revision must be exact",
            )
        digest = digest_of(["BOUNDARY_AUDIT_ENTRY@1", core])
        return cls(
            entry_id=_stable_id("boundary_entry", core),
            source_reference=core["source_reference"],
            kind=kind,
            evidence_class=evidence_class,
            repository_revision=core["repository_revision"],
            locator=core["locator"],
            description=core["description"],
            content_digest=content_digest,
            affirmative_claim_support_allowed=False,
            digest=digest,
        )

    def model_view(self) -> dict[str, object]:
        return {
            "entry_id": self.entry_id.value,
            "source_reference": self.source_reference,
            "kind": self.kind.value,
            "evidence_class": (
                self.evidence_class.value if self.evidence_class else None
            ),
            "repository_revision": self.repository_revision,
            "locator": self.locator,
            "description": self.description,
            "content_digest": (
                self.content_digest.value if self.content_digest else None
            ),
            "affirmative_claim_support_allowed": False,
            "digest": self.digest.value,
        }


@dataclass(frozen=True, slots=True)
class QuestionEvidencePackage:
    package_id: StableId
    package_revision: int
    schema: str
    protocol: str
    request_digest: Digest
    original_question: str
    understanding_digest: Digest
    checklist_digest: Digest
    cognition_context_digest: Digest
    repository_id: StableId
    binding_id: StableId
    repository_revision: str
    source_profile_ref: str
    source_profile_digest: Digest
    world_model_read_authority_digest: Digest
    source_revision_alignment: RevisionAlignment
    ledger_id: StableId
    ledger_generation: int
    ledger_final_prefix_digest: Digest
    ledger_seal_digest: Digest
    prior_package_digest: Digest | None
    checklist_dispositions: tuple[ChecklistDisposition, ...]
    support_citation: tuple[SupportCitationEntry, ...]
    boundary_audit: tuple[BoundaryAuditEntry, ...]
    digest: Digest
    seal_digest: Digest

    @classmethod
    def seal(
        cls,
        *,
        request: EngineeringQuestionRequest,
        understanding: QuestionUnderstanding,
        cognition: WorldModelCognitionContext,
        ledger: EvidenceLedger,
        retrieval_results: Sequence[RetrievalResult],
        broker_decisions: Sequence[SourceBrokerDecision],
        checklist_dispositions: Sequence[ChecklistDisposition],
        package_revision: int,
        prior_package_digest: Digest | None = None,
    ) -> "QuestionEvidencePackage":
        ledger.validate_integrity()
        if (
            ledger.request_digest != request.digest
            or ledger.terminal_status
            not in {LedgerTerminalStatus.FINISHED, LedgerTerminalStatus.FAILED_CLOSED}
            or ledger.seal_digest is None
        ):
            raise DomainError(
                ErrorCode.CONTROL_STATE_DENIED,
                "Question Evidence Package requires the current finished Ledger seal",
            )
        if (
            understanding.request_digest != request.digest
            or cognition.request_digest != request.digest
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Question Evidence Package inputs do not bind the same request",
            )
        if (
            not ledger.entries
            or ledger.entries[0].kind is not LedgerEntryKind.COGNITION_CONTEXT
            or ledger.entries[0].subject_id != cognition.cognition_context_id.value
            or ledger.entries[0].subject_digest != cognition.digest
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Question Evidence Package Ledger does not bind its Cognition Context",
            )
        if package_revision < 1 or package_revision != ledger.generation:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Question Evidence Package revision must match the Ledger generation",
            )
        if (
            package_revision == 1
            and (prior_package_digest is not None or ledger.parent_seal_digest is not None)
        ) or (
            package_revision > 1
            and (prior_package_digest is None or ledger.parent_seal_digest is None)
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Question Evidence Package predecessor identity is incomplete",
            )
        if package_revision > 1:
            verification_entries = tuple(
                entry
                for entry in ledger.entries
                if entry.kind is LedgerEntryKind.VERIFICATION_REQUEST
            )
            latest_verification = (
                verification_entries[-1] if verification_entries else None
            )
            if (
                latest_verification is None
                or dict(latest_verification.details).get("prior_package_digest")
                != prior_package_digest.value
                or latest_verification.references
                != (
                    ledger.parent_seal_digest.value,
                    prior_package_digest.value,
                )
            ):
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "Question Evidence Package predecessor differs from its verification Ledger",
                )
        results = tuple(retrieval_results)
        decisions = tuple(broker_decisions)
        if (
            len({item.result_id for item in results}) != len(results)
            or len({item.decision_id for item in decisions}) != len(decisions)
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Question Evidence Package inputs contain duplicate Results or Broker Decisions",
            )
        if any(result.repository_revision != request.repository_revision for result in results):
            raise DomainError(
                ErrorCode.SOURCE_REVISION_INCONSISTENT,
                "retrieval result revision differs from the Question Request",
            )
        ledger_decisions = {
            entry.subject_id: entry
            for entry in ledger.entries
            if entry.kind is LedgerEntryKind.BROKER_DECISION
        }
        ledger_operations = {
            entry.subject_id: entry
            for entry in ledger.entries
            if entry.kind is LedgerEntryKind.SOURCE_OPERATION
        }
        ledger_results = {
            entry.subject_id: entry
            for entry in ledger.entries
            if entry.kind is LedgerEntryKind.SOURCE_RESULT
        }
        if (
            len(ledger_decisions)
            != sum(
                entry.kind is LedgerEntryKind.BROKER_DECISION
                for entry in ledger.entries
            )
            or len(ledger_operations)
            != sum(
                entry.kind is LedgerEntryKind.SOURCE_OPERATION
                for entry in ledger.entries
            )
            or len(ledger_results)
            != sum(
                entry.kind is LedgerEntryKind.SOURCE_RESULT
                for entry in ledger.entries
            )
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Evidence Ledger repeats a Broker, Operation, or Result identity",
            )
        if (
            {item.decision_id.value for item in decisions} != set(ledger_decisions)
            or {item.result_id.value for item in results} != set(ledger_results)
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Question Evidence Package must retain every Ledger Decision and Result exactly once",
            )
        decision_by_operation = {
            item.operation_id: item
            for item in decisions
            if item.status is BrokerDecisionStatus.AUTHORIZED
            and item.operation_id is not None
        }
        authorized_decision_count = sum(
            item.status is BrokerDecisionStatus.AUTHORIZED for item in decisions
        )
        if (
            len(decision_by_operation) != authorized_decision_count
            or len(decision_by_operation) != len(ledger_operations)
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "authorized Broker Decisions do not match the Ledger operations",
            )
        for decision in decisions:
            expected_decision = SourceBrokerDecision.create(
                status=decision.status,
                request_digest=decision.request_digest,
                proposal_digest=decision.proposal_digest,
                ledger_prefix_digest=decision.ledger_prefix_digest,
                operation_id=decision.operation_id,
                reason_code=decision.reason_code,
            )
            decision_entry = ledger_decisions[decision.decision_id.value]
            if (
                decision != expected_decision
                or decision_entry.subject_digest != decision.digest
            ):
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "Broker Decision digest differs from the Evidence Ledger",
                )
            if decision.operation_id is not None:
                operation_entry = ledger_operations.get(decision.operation_id.value)
                if (
                    operation_entry is None
                    or operation_entry.references != (decision.decision_id.value,)
                ):
                    raise DomainError(
                        ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                        "authorized Broker Decision is not linked to its Ledger operation",
                    )
        for result in results:
            result_entry = ledger_results[result.result_id.value]
            operation_entry = ledger_operations.get(result.operation_id.value)
            if (
                result_entry.subject_digest != result.digest
                or operation_entry is None
                or operation_entry.subject_digest != result.operation_digest
                or decision_by_operation.get(result.operation_id) is None
                or result_entry.references
                != (
                    result.operation_id.value,
                    *(item.item_id.value for item in result.items),
                )
            ):
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "Retrieval Result provenance differs from the complete Evidence Ledger",
                )
        support: list[SupportCitationEntry] = []
        boundary: list[BoundaryAuditEntry] = []

        for item in cognition.items:
            if (
                cognition.alignment is RevisionAlignment.ALIGNED
                and item.dimension
                not in {CognitionDimension.COVERAGE, CognitionDimension.UNKNOWN}
                and item.support_references
            ):
                support.append(
                    SupportCitationEntry.create(
                        source_reference=item.item_id.value,
                        origin_class="WORLD_MODEL_COGNITION",
                        evidence_class=EngineeringEvidenceClass.WORLD_MODEL,
                        modality=item.modality,
                        context_ref=item.context_ref,
                        repository_revision=request.repository_revision,
                        locator=item.locator,
                        content=item.statement,
                        content_digest=digest_of(
                            ["WORLD_MODEL_COGNITION_CONTENT@1", item.statement]
                        ),
                        support_references=item.support_references,
                        coverage=item.coverage,
                    )
                )
            else:
                kind = (
                    PackageBoundaryKind.UNALIGNED_REVISION
                    if cognition.alignment is RevisionAlignment.UNALIGNED_REVISION
                    else PackageBoundaryKind.UNKNOWN
                )
                boundary.append(
                    BoundaryAuditEntry.create(
                        source_reference=item.item_id.value,
                        kind=kind,
                        evidence_class=EngineeringEvidenceClass.WORLD_MODEL,
                        repository_revision=request.repository_revision,
                        locator=item.locator,
                        description=item.statement,
                        content_digest=item.digest,
                    )
                )
        for index, value in enumerate(cognition.conflicts, 1):
            boundary.append(
                BoundaryAuditEntry.create(
                    source_reference=f"cognition-conflict-{index}",
                    kind=PackageBoundaryKind.CONFLICT,
                    evidence_class=EngineeringEvidenceClass.WORLD_MODEL,
                    repository_revision=request.repository_revision,
                    description=value,
                )
            )
        for index, value in enumerate(cognition.unknowns, 1):
            boundary.append(
                BoundaryAuditEntry.create(
                    source_reference=f"cognition-unknown-{index}",
                    kind=PackageBoundaryKind.UNKNOWN,
                    evidence_class=EngineeringEvidenceClass.WORLD_MODEL,
                    repository_revision=request.repository_revision,
                    description=value,
                )
            )

        for result in results:
            operation_entry = ledger_operations[result.operation_id.value]
            operation_name = (
                dict(operation_entry.details).get("operation")
                if operation_entry
                else None
            )
            can_support = (
                result.status is RetrievalStatus.COMPLETE
                and not result.truncated
                and operation_name
                in {SourceReadOperation.READ.value, SourceReadOperation.PARSE.value}
            )
            if can_support:
                for item in result.items:
                    if not item.coverage_complete:
                        boundary.append(
                            BoundaryAuditEntry.create(
                                source_reference=item.item_id.value,
                                kind=PackageBoundaryKind.PARTIAL,
                                evidence_class=item.evidence_class,
                                repository_revision=request.repository_revision,
                                locator=item.display_locator,
                                description="retrieved content has incomplete Coverage",
                                content_digest=item.content_digest,
                            )
                        )
                        continue
                    support.append(
                        SupportCitationEntry.create(
                            source_reference=item.item_id.value,
                            origin_class="EXACT_REVISION_SOURCE",
                            evidence_class=item.evidence_class,
                            modality=item.modality,
                            context_ref=request.binding_id.value,
                            repository_revision=request.repository_revision,
                            locator=item.display_locator,
                            content=item.content,
                            content_digest=item.content_digest,
                            support_references=(result.result_id.value,),
                            coverage=str(dict(result.coverage)),
                        )
                    )
                if not result.items:
                    boundary.append(
                        BoundaryAuditEntry.create(
                            source_reference=result.result_id.value,
                            kind=PackageBoundaryKind.UNKNOWN,
                            repository_revision=request.repository_revision,
                            description="complete read returned no affirmative content",
                            content_digest=result.digest,
                        )
                    )
            else:
                if operation_name == SourceReadOperation.SEARCH.value:
                    kind = PackageBoundaryKind.SEARCH_CANDIDATE
                elif result.status is RetrievalStatus.PARTIAL or result.truncated:
                    kind = PackageBoundaryKind.PARTIAL
                elif result.status is RetrievalStatus.OUTCOME_UNKNOWN:
                    kind = PackageBoundaryKind.UNKNOWN
                else:
                    kind = PackageBoundaryKind.FAILURE
                if result.items:
                    for item in result.items:
                        boundary.append(
                            BoundaryAuditEntry.create(
                                source_reference=item.item_id.value,
                                kind=kind,
                                evidence_class=item.evidence_class,
                                repository_revision=request.repository_revision,
                                locator=item.display_locator,
                                description=(
                                    "search hit is a navigation candidate, not affirmative support"
                                    if kind is PackageBoundaryKind.SEARCH_CANDIDATE
                                    else result.failure_code
                                    or "retrieval result is not admissible support"
                                ),
                                content_digest=item.content_digest,
                            )
                        )
                else:
                    boundary.append(
                        BoundaryAuditEntry.create(
                            source_reference=result.result_id.value,
                            kind=kind,
                            evidence_class=None,
                            repository_revision=request.repository_revision,
                            description=result.failure_code
                            or "retrieval produced no admissible support",
                            content_digest=result.digest,
                        )
                    )
        for decision in decisions:
            if decision.status is BrokerDecisionStatus.REJECTED:
                boundary.append(
                    BoundaryAuditEntry.create(
                        source_reference=decision.decision_id.value,
                        kind=PackageBoundaryKind.REJECTED_DECISION,
                        repository_revision=request.repository_revision,
                        description=decision.reason_code,
                        content_digest=decision.digest,
                    )
                )
        for entry in ledger.entries:
            if entry.kind in {
                LedgerEntryKind.GAP,
                LedgerEntryKind.VERIFICATION_REQUEST,
            }:
                details = dict(entry.details)
                evidence_class = None
                raw_evidence_class = details.get("evidence_class")
                if raw_evidence_class in EngineeringEvidenceClass._value2member_map_:
                    evidence_class = EngineeringEvidenceClass(raw_evidence_class)
                boundary.append(
                    BoundaryAuditEntry.create(
                        source_reference=entry.entry_id.value,
                        kind=PackageBoundaryKind.GAP,
                        evidence_class=evidence_class,
                        repository_revision=request.repository_revision,
                        description=details.get(
                            "evidence_need", f"retained gap {entry.subject_id}"
                        ),
                        content_digest=entry.subject_digest,
                    )
                )
            elif entry.kind is LedgerEntryKind.RESOURCE_RECEIPT:
                boundary.append(
                    BoundaryAuditEntry.create(
                        source_reference=entry.entry_id.value,
                        kind=PackageBoundaryKind.RESOURCE_RECEIPT,
                        repository_revision=request.repository_revision,
                        description=str(dict(entry.details)),
                        content_digest=entry.subject_digest,
                    )
                )
            elif entry.kind is LedgerEntryKind.FAIL_CLOSED_STOP:
                boundary.append(
                    BoundaryAuditEntry.create(
                        source_reference=entry.entry_id.value,
                        kind=PackageBoundaryKind.FAILURE,
                        repository_revision=request.repository_revision,
                        description=dict(entry.details).get(
                            "reason", "investigation failed closed"
                        ),
                        content_digest=entry.subject_digest,
                    )
                )

        disposition_reference_eligibility = _disposition_reference_eligibility(
            cognition=cognition,
            ledger=ledger,
            retrieval_results=results,
            broker_decisions=decisions,
        )
        if (
            {item.source_reference for item in support}
            != set(disposition_reference_eligibility.support_references)
            or {item.source_reference for item in boundary}
            != set(disposition_reference_eligibility.boundary_references)
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "package evidence partitions disagree with disposition eligibility",
            )
        if len(support) > request.limits.maximum_support_items:
            raise DomainError(
                ErrorCode.BUDGET_EXHAUSTED,
                "Question Evidence Package support item fuse is exhausted",
            )
        support_references = set(
            disposition_reference_eligibility.support_references
        )
        boundary_references = set(
            disposition_reference_eligibility.boundary_references
        )
        dispositions = tuple(checklist_dispositions)
        expected_checklist = {item.item_id for item in understanding.checklist}
        if {item.checklist_item_id for item in dispositions} != expected_checklist:
            raise DomainError(
                ErrorCode.CONTROL_STATE_DENIED,
                "FINISH must disposition every Question Checklist item exactly once",
            )
        if len(dispositions) != len(expected_checklist):
            raise DomainError(
                ErrorCode.CONTROL_STATE_DENIED,
                "FINISH contains duplicate checklist dispositions",
            )
        material_observations = tuple(
            observation
            for disposition in dispositions
            for observation in disposition.material_observations
        )
        if (
            len(material_observations) > 64
            or len({item.observation_id for item in material_observations})
            != len(material_observations)
        ):
            raise DomainError(
                ErrorCode.CONTROL_STATE_DENIED,
                "FINISH material observations must be globally unique and bounded",
            )
        for disposition in dispositions:
            references = set(disposition.evidence_references)
            if disposition.outcome is ChecklistOutcome.SUPPORTED:
                if not references or not references.issubset(support_references):
                    raise DomainError(
                        ErrorCode.CONTROL_STATE_DENIED,
                        "SUPPORTED checklist disposition requires admissible support/citation evidence",
                    )
            elif not references.issubset(boundary_references):
                raise DomainError(
                    ErrorCode.CONTROL_STATE_DENIED,
                    "non-supported checklist disposition requires retained boundary/audit evidence",
                )

        checklist_digest = digest_of(
            tuple(item.digest.value for item in understanding.checklist)
        )
        core = {
            "schema": ENGINEERING_QA_PACKAGE_SCHEMA,
            "protocol": ENGINEERING_QA_PROTOCOL,
            "package_revision": package_revision,
            "request_digest": request.digest.value,
            "original_question": request.original_question,
            "understanding_digest": understanding.digest.value,
            "checklist_digest": checklist_digest.value,
            "cognition_context_digest": cognition.digest.value,
            "repository_id": request.repository_id.value,
            "binding_id": request.binding_id.value,
            "repository_revision": request.repository_revision,
            "source_profile_ref": request.source_profile_ref,
            "source_profile_digest": request.source_profile_digest.value,
            "world_model_read_authority_digest": cognition.read_authority_digest.value,
            "source_revision_alignment": cognition.alignment.value,
            "ledger_id": ledger.ledger_id.value,
            "ledger_generation": ledger.generation,
            "ledger_final_prefix_digest": ledger.prefix_digest.value,
            "ledger_seal_digest": ledger.seal_digest.value,
            "prior_package_digest": (
                prior_package_digest.value if prior_package_digest else None
            ),
            "checklist_dispositions": tuple(item.digest.value for item in dispositions),
            "support_citation": tuple(item.digest.value for item in support),
            "boundary_audit": tuple(item.digest.value for item in boundary),
        }
        digest = digest_of([ENGINEERING_QA_PACKAGE_SCHEMA, core])
        seal = digest_of(
            [
                "QUESTION_EVIDENCE_PACKAGE_SEAL@1",
                digest.value,
                ledger.seal_digest.value,
                tuple(item.digest.value for item in support),
                tuple(item.digest.value for item in boundary),
            ]
        )
        package = cls(
            package_id=_stable_id("question_package", core),
            package_revision=package_revision,
            schema=ENGINEERING_QA_PACKAGE_SCHEMA,
            protocol=ENGINEERING_QA_PROTOCOL,
            request_digest=request.digest,
            original_question=request.original_question,
            understanding_digest=understanding.digest,
            checklist_digest=checklist_digest,
            cognition_context_digest=cognition.digest,
            repository_id=request.repository_id,
            binding_id=request.binding_id,
            repository_revision=request.repository_revision,
            source_profile_ref=request.source_profile_ref,
            source_profile_digest=request.source_profile_digest,
            world_model_read_authority_digest=cognition.read_authority_digest,
            source_revision_alignment=cognition.alignment,
            ledger_id=ledger.ledger_id,
            ledger_generation=ledger.generation,
            ledger_final_prefix_digest=ledger.prefix_digest,
            ledger_seal_digest=ledger.seal_digest,
            prior_package_digest=prior_package_digest,
            checklist_dispositions=dispositions,
            support_citation=tuple(support),
            boundary_audit=tuple(boundary),
            digest=digest,
            seal_digest=seal,
        )
        if package.serialized_bytes > request.limits.maximum_package_bytes:
            raise DomainError(
                ErrorCode.BUDGET_EXHAUSTED,
                "Question Evidence Package byte fuse is exhausted",
            )
        return package

    @property
    def serialized_bytes(self) -> int:
        return len(canonical_json_bytes(self.model_view()))

    def model_view(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "protocol": self.protocol,
            "package_id": self.package_id.value,
            "package_revision": self.package_revision,
            "package_digest": self.digest.value,
            "seal_digest": self.seal_digest.value,
            "request_digest": self.request_digest.value,
            "original_question": self.original_question,
            "understanding_digest": self.understanding_digest.value,
            "checklist_digest": self.checklist_digest.value,
            "cognition_context_digest": self.cognition_context_digest.value,
            "repository_id": self.repository_id.value,
            "binding_id": self.binding_id.value,
            "repository_revision": self.repository_revision,
            "source_profile_ref": self.source_profile_ref,
            "source_profile_digest": self.source_profile_digest.value,
            "world_model_read_authority_digest": self.world_model_read_authority_digest.value,
            "source_revision_alignment": self.source_revision_alignment.value,
            "ledger": {
                "ledger_id": self.ledger_id.value,
                "generation": self.ledger_generation,
                "final_prefix_digest": self.ledger_final_prefix_digest.value,
                "seal_digest": self.ledger_seal_digest.value,
            },
            "prior_package_digest": (
                self.prior_package_digest.value if self.prior_package_digest else None
            ),
            "checklist_dispositions": [
                {
                    "checklist_item_id": item.checklist_item_id,
                    "outcome": item.outcome.value,
                    "evidence_references": list(item.evidence_references),
                    "explanation": item.explanation,
                    "material_observations": [
                        observation.model_view()
                        for observation in item.material_observations
                    ],
                    "digest": item.digest.value,
                }
                for item in self.checklist_dispositions
            ],
            "support/citation": [item.model_view() for item in self.support_citation],
            "boundary/audit": [item.model_view() for item in self.boundary_audit],
            "seal_confers_truth": False,
        }


@dataclass(frozen=True, slots=True)
class VerificationRequestProposal:
    verification_request_id: StableId
    schema: str
    package_digest: Digest
    checklist_item_id: str
    claim_id: str | None
    evidence_class: EngineeringEvidenceClass
    evidence_need: str
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        package_digest: Digest,
        checklist_item_id: str,
        evidence_class: EngineeringEvidenceClass,
        evidence_need: str,
        claim_id: str | None = None,
    ) -> "VerificationRequestProposal":
        evidence_need = _text(
            evidence_need, "verification evidence need", maximum_bytes=8_192
        )
        if _PATH_LIKE_EVIDENCE_NEED.search(evidence_need):
            raise DomainError(
                ErrorCode.PROVIDER_OUTPUT_FORBIDDEN,
                "Reviewer verification request cannot contain an executable operation, path, URL, or command",
            )
        core = {
            "schema": ENGINEERING_QA_VERIFICATION_REQUEST_SCHEMA,
            "package_digest": package_digest.value,
            "checklist_item_id": _reference(
                checklist_item_id, "verification checklist item ID"
            ),
            "claim_id": (
                _reference(claim_id, "verification claim ID") if claim_id else None
            ),
            "evidence_class": evidence_class.value,
            "evidence_need": evidence_need,
        }
        digest = digest_of([ENGINEERING_QA_VERIFICATION_REQUEST_SCHEMA, core])
        return cls(
            verification_request_id=_stable_id("verification_request", core),
            schema=ENGINEERING_QA_VERIFICATION_REQUEST_SCHEMA,
            package_digest=package_digest,
            checklist_item_id=core["checklist_item_id"],
            claim_id=core["claim_id"],
            evidence_class=evidence_class,
            evidence_need=evidence_need,
            digest=digest,
        )

    def model_view(self) -> dict[str, object]:
        return {
            "verification_request_id": self.verification_request_id.value,
            "schema": self.schema,
            "package_digest": self.package_digest.value,
            "checklist_item_id": self.checklist_item_id,
            "claim_id": self.claim_id,
            "evidence_class": self.evidence_class.value,
            "evidence_need": self.evidence_need,
            "digest": self.digest.value,
        }


@dataclass(frozen=True, slots=True)
class VerificationInvestigationInput:
    attempt_id: StableId
    role_context_id: StableId
    step_index: int
    verification_request: VerificationRequestProposal
    current_package: QuestionEvidencePackage
    ledger: EvidenceLedger
    retrieval_results: tuple[RetrievalResult, ...]
    disposition_reference_eligibility: ChecklistDispositionReferenceEligibility
    registered_evidence_classes: tuple[EngineeringEvidenceClass, ...] = ()
    required_evidence_classes: tuple[EngineeringEvidenceClass, ...] = ()
    investigated_evidence_classes: tuple[EngineeringEvidenceClass, ...] = ()
    required_evidence_paths: tuple[str, ...] = ()
    required_path_locators: tuple[RequiredEvidencePathLocator, ...] = ()

    @property
    def required_basis_entry_id(self) -> StableId:
        return self.ledger.entries[-1].entry_id

    @property
    def eligible_locator_references(self) -> tuple[StableId, ...]:
        return _eligible_locator_references(
            self.retrieval_results,
            required_evidence_paths=self.required_evidence_paths,
            required_path_locators=self.required_path_locators,
            attempt_id=self.attempt_id,
            request_digest=self.current_package.request_digest,
        )

    @property
    def eligible_required_path_locators(
        self,
    ) -> tuple[RequiredEvidencePathLocator, ...]:
        eligible = set(self.eligible_locator_references)
        return tuple(
            item
            for item in self.required_path_locators
            if item.locator_reference in eligible
        )

    @property
    def consumed_full_content_paths(self) -> tuple[str, ...]:
        return _consumed_full_content_paths(self.retrieval_results)

    @property
    def unread_required_evidence_paths(self) -> tuple[str, ...]:
        consumed = set(self.consumed_full_content_paths)
        return tuple(
            path for path in self.required_evidence_paths if path not in consumed
        )

    @property
    def prior_action_intents(self) -> tuple[dict[str, object], ...]:
        return _prior_action_intents(
            ledger=self.ledger,
            attempt_id=self.attempt_id,
        )

    @property
    def untried_required_evidence_classes(
        self,
    ) -> tuple[EngineeringEvidenceClass, ...]:
        return _evidence_class_closure(
            registered=self.registered_evidence_classes,
            required=self.required_evidence_classes,
            investigated=self.investigated_evidence_classes,
        )[0]

    @property
    def unregistered_required_evidence_classes(
        self,
    ) -> tuple[EngineeringEvidenceClass, ...]:
        return _evidence_class_closure(
            registered=self.registered_evidence_classes,
            required=self.required_evidence_classes,
            investigated=self.investigated_evidence_classes,
        )[1]

    def validate_new_result_closure(self) -> None:
        verification_positions = tuple(
            index
            for index, entry in enumerate(self.ledger.entries)
            if entry.kind is LedgerEntryKind.VERIFICATION_REQUEST
        )
        if not verification_positions:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "verification investigation Ledger has no gap Request",
            )
        latest_verification = self.ledger.entries[verification_positions[-1]]
        if (
            self.verification_request.package_digest != self.current_package.digest
            or latest_verification.subject_id
            != self.verification_request.verification_request_id.value
            or latest_verification.subject_digest != self.verification_request.digest
            or self.ledger.generation != self.current_package.ledger_generation + 1
            or self.ledger.parent_seal_digest
            != self.current_package.ledger_seal_digest
            or latest_verification.references
            != (
                self.current_package.ledger_seal_digest.value,
                self.current_package.digest.value,
            )
            or dict(latest_verification.details).get("prior_package_digest")
            != self.current_package.digest.value
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "verification investigation gap, Package, and successor Ledger do not share one predecessor",
            )
        result_entries = tuple(
            entry
            for entry in self.ledger.entries[verification_positions[-1] + 1 :]
            if entry.kind is LedgerEntryKind.SOURCE_RESULT
        )
        supplied_results = tuple(
            (item.result_id.value, item.digest) for item in self.retrieval_results
        )
        ledger_results = tuple(
            (entry.subject_id, entry.subject_digest) for entry in result_entries
        )
        if supplied_results != ledger_results:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "verification investigation may only receive Results appended after its current gap Request",
            )

    def model_view(self) -> dict[str, object]:
        self.validate_new_result_closure()
        return {
            "role": "VERIFICATION_INVESTIGATION",
            "attempt_id": self.attempt_id.value,
            "role_context_id": self.role_context_id.value,
            "step_index": self.step_index,
            "required_basis_entry_id": self.required_basis_entry_id.value,
            "eligible_locator_references": [
                item.value for item in self.eligible_locator_references
            ],
            "eligible_required_path_locators": [
                item.model_view()
                for item in self.eligible_required_path_locators
            ],
            "consumed_full_content_paths": list(self.consumed_full_content_paths),
            "prior_action_intents": list(self.prior_action_intents),
            "registered_evidence_classes": [
                item.value for item in self.registered_evidence_classes
            ],
            "required_evidence_classes": [
                item.value for item in self.required_evidence_classes
            ],
            "investigated_evidence_classes": [
                item.value for item in self.investigated_evidence_classes
            ],
            "untried_required_evidence_classes": [
                item.value for item in self.untried_required_evidence_classes
            ],
            "unregistered_required_evidence_classes": [
                item.value for item in self.unregistered_required_evidence_classes
            ],
            "required_evidence_paths": list(self.required_evidence_paths),
            "unread_required_evidence_paths": list(
                self.unread_required_evidence_paths
            ),
            "admissible_support_references": list(
                self.disposition_reference_eligibility.support_references
            ),
            "admissible_boundary_references": list(
                self.disposition_reference_eligibility.boundary_references
            ),
            "verification_request": self.verification_request.model_view(),
            "current_question_evidence_package": self.current_package.model_view(),
            "current_evidence_ledger": self.ledger.model_view(),
            "new_typed_retrieval_results": [
                item.model_view() for item in self.retrieval_results
            ],
        }


class VerificationInvestigationRole(Protocol):
    def propose(
        self, investigation_input: VerificationInvestigationInput
    ) -> InvestigationStepProposal: ...


@dataclass(frozen=True, slots=True)
class EngineeringAnswerClaimProposal:
    claim_id: str
    kind: AnswerClaimKind
    content_role: AnswerContentRole
    checklist_item_ids: tuple[str, ...]
    material_observation_ids: tuple[StableId, ...]
    text: str
    evidence_entry_ids: tuple[StableId, ...]
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        claim_id: str,
        kind: AnswerClaimKind,
        content_role: AnswerContentRole,
        checklist_item_ids: Sequence[str],
        material_observation_ids: Sequence[StableId],
        text: str,
        evidence_entry_ids: Sequence[StableId],
    ) -> "EngineeringAnswerClaimProposal":
        if not isinstance(kind, AnswerClaimKind) or not isinstance(
            content_role, AnswerContentRole
        ):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "answer claim kind and content role must use the controlled vocabulary",
            )
        checklist = tuple(
            _reference(item, "answer claim checklist item")
            for item in checklist_item_ids
        )
        if not checklist or len(checklist) != len(set(checklist)):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "answer claim requires unique material checklist references",
            )
        observations = tuple(material_observation_ids)
        if len(observations) != len(set(observations)):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "answer claim material observation references must be unique",
            )
        coverage_only_limitation = (
            kind is AnswerClaimKind.LIMITATION
            and content_role is AnswerContentRole.LIMITATION
        )
        direct_answer_summary = (
            kind is AnswerClaimKind.AFFIRMATIVE
            and content_role is AnswerContentRole.DIRECT_ANSWER
        )
        if not observations and not (
            coverage_only_limitation or direct_answer_summary
        ):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "only a direct-answer summary or coverage-only limitation may omit material observation references",
            )
        if (
            content_role is AnswerContentRole.LIMITATION
            and kind is not AnswerClaimKind.LIMITATION
        ) or (
            kind is AnswerClaimKind.LIMITATION
            and content_role
            not in (
                AnswerContentRole.DIRECT_ANSWER,
                AnswerContentRole.LIMITATION,
            )
        ):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "answer limitation kind requires a direct-answer or limitation content role",
            )
        references = tuple(evidence_entry_ids)
        if not references or len(set(references)) != len(references):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "answer claim requires unique package evidence references",
            )
        core = {
            "claim_id": _reference(claim_id, "answer claim ID"),
            "kind": kind.value,
            "content_role": content_role.value,
            "checklist_item_ids": checklist,
            "material_observation_ids": tuple(
                item.value for item in observations
            ),
            "text": _text(text, "answer claim text", maximum_bytes=32_768),
            "evidence_entry_ids": tuple(item.value for item in references),
        }
        return cls(
            claim_id=core["claim_id"],
            kind=kind,
            content_role=content_role,
            checklist_item_ids=checklist,
            material_observation_ids=observations,
            text=core["text"],
            evidence_entry_ids=references,
            digest=digest_of(["ENGINEERING_ANSWER_CLAIM_PROPOSAL@4", core]),
        )


@dataclass(frozen=True, slots=True)
class EngineeringAnswerProposal:
    role_context_id: StableId
    package_digest: Digest
    response_language: str
    claims: tuple[EngineeringAnswerClaimProposal, ...]
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        role_context_id: StableId,
        package_digest: Digest,
        response_language: str,
        claims: Sequence[EngineeringAnswerClaimProposal],
    ) -> "EngineeringAnswerProposal":
        claim_tuple = tuple(claims)
        if not claim_tuple or len(claim_tuple) > 64:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "engineering answer must contain one to sixty-four claims",
            )
        if len({item.claim_id for item in claim_tuple}) != len(claim_tuple):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "engineering answer contains duplicate claim IDs",
            )
        direct = tuple(
            item
            for item in claim_tuple
            if item.content_role is AnswerContentRole.DIRECT_ANSWER
        )
        role_order = {
            AnswerContentRole.DIRECT_ANSWER: 0,
            AnswerContentRole.USER_VISIBLE_PROCESS: 1,
            AnswerContentRole.IMPACT_OR_SIDE_EFFECT: 2,
            AnswerContentRole.IMPLEMENTATION_EVIDENCE: 3,
            AnswerContentRole.LIMITATION: 4,
        }
        ordinals = tuple(role_order[item.content_role] for item in claim_tuple)
        if (
            len(direct) != 1
            or claim_tuple[0].content_role is not AnswerContentRole.DIRECT_ANSWER
            or ordinals != tuple(sorted(ordinals))
        ):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "engineering answer must contain one direct answer first and ordered supporting roles",
            )
        core = {
            "role_context_id": role_context_id.value,
            "package_digest": package_digest.value,
            "response_language": _text(
                response_language, "answer response language", maximum_bytes=128
            ),
            "claims": tuple(item.digest.value for item in claim_tuple),
        }
        return cls(
            role_context_id=role_context_id,
            package_digest=package_digest,
            response_language=core["response_language"],
            claims=claim_tuple,
            digest=digest_of(["ENGINEERING_ANSWER_PROPOSAL@4", core]),
        )


@dataclass(frozen=True, slots=True)
class EngineeringAnswerDraft:
    draft_id: StableId
    revision: int
    package_digest: Digest
    response_language: str
    claims: tuple[EngineeringAnswerClaimProposal, ...]
    default_body_claim_ids: tuple[str, ...]
    body: str
    proposal_digest: Digest
    digest: Digest

    @classmethod
    def accept(
        cls,
        *,
        package: QuestionEvidencePackage,
        understanding: QuestionUnderstanding,
        expected_role_context_id: StableId,
        proposal: EngineeringAnswerProposal,
        revision: int,
    ) -> "EngineeringAnswerDraft":
        expected_claims = tuple(
            EngineeringAnswerClaimProposal.create(
                claim_id=item.claim_id,
                kind=item.kind,
                content_role=item.content_role,
                checklist_item_ids=item.checklist_item_ids,
                material_observation_ids=item.material_observation_ids,
                text=item.text,
                evidence_entry_ids=item.evidence_entry_ids,
            )
            for item in proposal.claims
        )
        if expected_claims != proposal.claims:
            raise DomainError(
                ErrorCode.PROVIDER_RESPONSE_INVALID,
                "answer Claim identity is invalid",
            )
        expected_proposal = EngineeringAnswerProposal.create(
            role_context_id=proposal.role_context_id,
            package_digest=proposal.package_digest,
            response_language=proposal.response_language,
            claims=expected_claims,
        )
        if proposal != expected_proposal:
            raise DomainError(
                ErrorCode.PROVIDER_RESPONSE_INVALID,
                "answer Proposal identity is invalid",
            )
        if (
            proposal.role_context_id != expected_role_context_id
            or proposal.package_digest != package.digest
            or proposal.response_language != understanding.response_language
            or understanding.digest != package.understanding_digest
            or revision < 1
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "answer proposal does not bind the current Package and fresh role context",
            )
        checklist_ids = {item.item_id for item in understanding.checklist}
        if {
            checklist_item_id
            for claim in proposal.claims
            for checklist_item_id in claim.checklist_item_ids
        } != checklist_ids:
            raise DomainError(
                ErrorCode.CONTROL_STATE_DENIED,
                "answer claims must cover every material conclusion exactly through typed checklist links",
            )
        if any(
            not set(claim.checklist_item_ids).issubset(checklist_ids)
            for claim in proposal.claims
        ):
            raise DomainError(
                ErrorCode.PROVIDER_RESPONSE_INVALID,
                "answer claim refers to an unknown material checklist item",
            )
        disposition_by_checklist = {
            item.checklist_item_id: item for item in package.checklist_dispositions
        }
        for claim in proposal.claims:
            if (
                claim.kind is AnswerClaimKind.AFFIRMATIVE
                and not claim.material_observation_ids
                and any(
                    disposition_by_checklist[item].outcome
                    is not ChecklistOutcome.SUPPORTED
                    for item in claim.checklist_item_ids
                )
            ):
                raise DomainError(
                    ErrorCode.CONTROL_STATE_DENIED,
                    "an empty-link direct summary may cover only supported checklist items",
                )
        observation_by_id = {
            observation.observation_id: (disposition, observation)
            for disposition in package.checklist_dispositions
            for observation in disposition.material_observations
        }
        linked_observation_ids = {
            observation_id
            for claim in proposal.claims
            for observation_id in claim.material_observation_ids
        }
        if linked_observation_ids != set(observation_by_id):
            raise DomainError(
                ErrorCode.CONTROL_STATE_DENIED,
                "answer claims must cover every Package material observation",
            )
        for claim in proposal.claims:
            if not set(claim.material_observation_ids).issubset(observation_by_id):
                raise DomainError(
                    ErrorCode.PROVIDER_RESPONSE_INVALID,
                    "answer claim refers to an unknown material observation",
                )
            if any(
                observation.checklist_item_id not in claim.checklist_item_ids
                for _, observation in (
                    observation_by_id[observation_id]
                    for observation_id in claim.material_observation_ids
                )
            ):
                raise DomainError(
                    ErrorCode.CONTROL_STATE_DENIED,
                    "answer claim material observations cross checklist links",
                )
        implementation_claims = tuple(
            claim
            for claim in proposal.claims
            if claim.content_role is AnswerContentRole.IMPLEMENTATION_EVIDENCE
        )
        if (
            understanding.requested_abstraction_level is AnswerDetailLevel.DIRECT
            and implementation_claims
        ):
            raise DomainError(
                ErrorCode.CONTROL_STATE_DENIED,
                "implementation evidence exceeds the accepted answer-detail level",
            )
        if set(disposition_by_checklist) != checklist_ids:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "answer Package checklist differs from the accepted understanding",
            )
        for checklist_item_id, disposition in disposition_by_checklist.items():
            linked = tuple(
                claim
                for claim in proposal.claims
                if checklist_item_id in claim.checklist_item_ids
            )
            if (
                disposition.outcome is ChecklistOutcome.SUPPORTED
                and not any(
                    claim.kind is AnswerClaimKind.AFFIRMATIVE for claim in linked
                )
            ) or (
                disposition.outcome is not ChecklistOutcome.SUPPORTED
                and not any(
                    claim.kind is AnswerClaimKind.LIMITATION for claim in linked
                )
            ):
                raise DomainError(
                    ErrorCode.CONTROL_STATE_DENIED,
                    "answer claim role does not honestly represent its checklist disposition",
                )
        support_ids = {item.entry_id for item in package.support_citation}
        boundary_ids = {item.entry_id for item in package.boundary_audit}
        support_entry_by_source = {
            item.source_reference: item.entry_id for item in package.support_citation
        }
        boundary_entry_by_source = {
            item.source_reference: item.entry_id for item in package.boundary_audit
        }
        for claim in proposal.claims:
            references = set(claim.evidence_entry_ids)
            if claim.kind is AnswerClaimKind.AFFIRMATIVE:
                if not references.issubset(support_ids):
                    raise DomainError(
                        ErrorCode.CONTROL_STATE_DENIED,
                        "affirmative answer claim cites a non-support Package entry",
                    )
            elif not references.issubset(boundary_ids):
                raise DomainError(
                    ErrorCode.CONTROL_STATE_DENIED,
                    "limitation claim must cite retained boundary/audit entries",
                )
            for observation_id in claim.material_observation_ids:
                disposition, observation = observation_by_id[observation_id]
                expected_kind = (
                    AnswerClaimKind.AFFIRMATIVE
                    if disposition.outcome is ChecklistOutcome.SUPPORTED
                    else AnswerClaimKind.LIMITATION
                )
                if claim.kind is not expected_kind:
                    raise DomainError(
                        ErrorCode.CONTROL_STATE_DENIED,
                        "answer claim kind differs from its material observation",
                    )
                source_map = (
                    support_entry_by_source
                    if expected_kind is AnswerClaimKind.AFFIRMATIVE
                    else boundary_entry_by_source
                )
                required_entries = {
                    source_map[reference]
                    for reference in observation.evidence_references
                }
                if not required_entries.issubset(references):
                    raise DomainError(
                        ErrorCode.CONTROL_STATE_DENIED,
                        "answer claim does not cite every Package entry supporting its material observation",
                    )
        non_implementation_observation_ids = {
            observation_id
            for claim in proposal.claims
            if claim.content_role is not AnswerContentRole.IMPLEMENTATION_EVIDENCE
            for observation_id in claim.material_observation_ids
        }
        default_body_candidates = tuple(
            claim
            for claim in proposal.claims
            if (
                understanding.requested_abstraction_level
                is AnswerDetailLevel.IMPLEMENTATION_DETAIL
                or claim.content_role
                is not AnswerContentRole.IMPLEMENTATION_EVIDENCE
                or not set(claim.material_observation_ids).issubset(
                    non_implementation_observation_ids
                )
            )
        )
        projected_claims: list[EngineeringAnswerClaimProposal] = []
        projected_observation_ids: set[StableId] = set()
        for claim in default_body_candidates:
            claim_observation_ids = set(claim.material_observation_ids)
            if not claim_observation_ids:
                projected_claims.append(claim)
                continue
            overlap = claim_observation_ids.intersection(
                projected_observation_ids
            )
            if overlap == claim_observation_ids:
                continue
            if overlap:
                raise DomainError(
                    ErrorCode.CONTROL_STATE_DENIED,
                    "a user-visible answer claim partially repeats material observations",
                )
            projected_claims.append(claim)
            projected_observation_ids.update(claim_observation_ids)
        default_body_claims = tuple(projected_claims)
        default_body_claim_ids = tuple(
            claim.claim_id for claim in default_body_claims
        )
        default_body_observation_ids = {
            observation_id
            for claim in default_body_claims
            for observation_id in claim.material_observation_ids
        }
        if default_body_observation_ids != set(observation_by_id):
            raise DomainError(
                ErrorCode.CONTROL_STATE_DENIED,
                "every material observation must appear in the default user-visible answer",
            )
        body = "\n\n".join(item.text for item in default_body_claims)
        core = {
            "revision": revision,
            "package_digest": package.digest.value,
            "response_language": proposal.response_language,
            "claims": tuple(item.digest.value for item in proposal.claims),
            "default_body_claim_ids": default_body_claim_ids,
            "body": body,
            "proposal_digest": proposal.digest.value,
        }
        digest = digest_of(["ENGINEERING_ANSWER_DRAFT@5", core])
        return cls(
            draft_id=_stable_id("engineering_draft", core),
            revision=revision,
            package_digest=package.digest,
            response_language=proposal.response_language,
            claims=proposal.claims,
            default_body_claim_ids=default_body_claim_ids,
            body=body,
            proposal_digest=proposal.digest,
            digest=digest,
        )

    def model_view(self) -> dict[str, object]:
        return {
            "draft_id": self.draft_id.value,
            "revision": self.revision,
            "package_digest": self.package_digest.value,
            "response_language": self.response_language,
            "default_body_claim_ids": list(self.default_body_claim_ids),
            "body": self.body,
            "claims": [
                {
                    "claim_id": item.claim_id,
                    "kind": item.kind.value,
                    "content_role": item.content_role.value,
                    "checklist_item_ids": list(item.checklist_item_ids),
                    "material_observation_ids": [
                        reference.value
                        for reference in item.material_observation_ids
                    ],
                    "text": item.text,
                    "evidence_entry_ids": [
                        reference.value for reference in item.evidence_entry_ids
                    ],
                    "digest": item.digest.value,
                }
                for item in self.claims
            ],
            "digest": self.digest.value,
        }


class EngineeringAnswerRole(Protocol):
    def generate(
        self,
        *,
        original_question: str,
        understanding: QuestionUnderstanding,
        package: QuestionEvidencePackage,
        role_context_id: StableId,
        rewrite_findings: tuple["EngineeringReviewFinding", ...] = (),
    ) -> EngineeringAnswerProposal: ...


@dataclass(frozen=True, slots=True)
class EngineeringReviewFinding:
    finding_code: str
    checklist_item_id: str | None
    claim_id: str | None
    description: str
    remediation: EngineeringReviewRemediation
    existing_evidence_entry_ids: tuple[StableId, ...]
    evidence_class: EngineeringEvidenceClass | None
    evidence_need: str | None
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        finding_code: str,
        description: str,
        remediation: EngineeringReviewRemediation,
        checklist_item_id: str | None = None,
        claim_id: str | None = None,
        existing_evidence_entry_ids: Sequence[StableId] = (),
        evidence_class: EngineeringEvidenceClass | None = None,
        evidence_need: str | None = None,
    ) -> "EngineeringReviewFinding":
        if checklist_item_id is None and claim_id is None:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "Review Finding must bind a checklist item or answer Claim",
            )
        if not isinstance(remediation, EngineeringReviewRemediation):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "Review Finding remediation must use the controlled vocabulary",
            )
        evidence_entry_ids = tuple(existing_evidence_entry_ids)
        if len(evidence_entry_ids) != len(set(evidence_entry_ids)):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "Review Finding contains duplicate existing Package evidence entries",
            )
        if remediation is EngineeringReviewRemediation.REWRITE_WITH_EXISTING_EVIDENCE:
            if (
                not evidence_entry_ids
                or evidence_class is not None
                or evidence_need is not None
            ):
                raise DomainError(
                    ErrorCode.INVALID_ARGUMENT,
                    "rewrite Finding requires existing Package evidence and no evidence gap",
                )
        elif remediation is EngineeringReviewRemediation.INVESTIGATE_MISSING_EVIDENCE:
            if (
                evidence_entry_ids
                or evidence_class not in _RETRIEVAL_EVIDENCE_CLASSES
                or evidence_need is None
                or checklist_item_id is None
            ):
                raise DomainError(
                    ErrorCode.INVALID_ARGUMENT,
                    "evidence-gap Finding requires a checklist item, controlled evidence class, and need",
                )
            evidence_need = _text(
                evidence_need, "Review Finding evidence need", maximum_bytes=8_192
            )
            if _PATH_LIKE_EVIDENCE_NEED.search(evidence_need):
                raise DomainError(
                    ErrorCode.PROVIDER_OUTPUT_FORBIDDEN,
                    "Review Finding evidence need cannot contain an operation, path, URL, or command",
                )
        elif (
            evidence_entry_ids
            or evidence_class is not None
            or evidence_need is not None
        ):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "unrecoverable Finding cannot carry rewrite evidence or an evidence gap",
            )
        normalized_finding_code = _reference(finding_code, "Review Finding code")
        normalized_checklist_item_id = (
            _reference(checklist_item_id, "Review Finding checklist item")
            if checklist_item_id
            else None
        )
        normalized_claim_id = (
            _reference(claim_id, "Review Finding claim ID") if claim_id else None
        )
        normalized_description = _text(
            description, "Review Finding description", maximum_bytes=8_192
        )
        core = {
            "finding_code": normalized_finding_code,
            "checklist_item_id": normalized_checklist_item_id,
            "claim_id": normalized_claim_id,
            "description": normalized_description,
            "remediation": remediation.value,
            "existing_evidence_entry_ids": tuple(
                item.value for item in evidence_entry_ids
            ),
            "evidence_class": evidence_class.value if evidence_class else None,
            "evidence_need": evidence_need,
        }
        return cls(
            finding_code=normalized_finding_code,
            checklist_item_id=normalized_checklist_item_id,
            claim_id=normalized_claim_id,
            description=normalized_description,
            remediation=remediation,
            existing_evidence_entry_ids=evidence_entry_ids,
            evidence_class=evidence_class,
            evidence_need=evidence_need,
            digest=digest_of(["ENGINEERING_REVIEW_FINDING@2", core]),
        )


def _review_decision_from_findings(
    findings: Sequence[EngineeringReviewFinding],
) -> EngineeringReviewDecision:
    remediations = {item.remediation for item in findings}
    if EngineeringReviewRemediation.REJECT_UNRECOVERABLE in remediations:
        return EngineeringReviewDecision.REJECT
    if EngineeringReviewRemediation.INVESTIGATE_MISSING_EVIDENCE in remediations:
        return EngineeringReviewDecision.MORE_EVIDENCE_REQUIRED
    if findings:
        return EngineeringReviewDecision.REWRITE_REQUIRED
    return EngineeringReviewDecision.APPROVED


def _verification_request_from_findings(
    *,
    package_digest: Digest,
    findings: Sequence[EngineeringReviewFinding],
) -> VerificationRequestProposal | None:
    if (
        _review_decision_from_findings(findings)
        is not EngineeringReviewDecision.MORE_EVIDENCE_REQUIRED
    ):
        return None
    for finding in findings:
        if (
            finding.remediation
            is EngineeringReviewRemediation.INVESTIGATE_MISSING_EVIDENCE
        ):
            assert finding.checklist_item_id is not None
            assert finding.evidence_class is not None
            assert finding.evidence_need is not None
            return VerificationRequestProposal.create(
                package_digest=package_digest,
                checklist_item_id=finding.checklist_item_id,
                claim_id=finding.claim_id,
                evidence_class=finding.evidence_class,
                evidence_need=finding.evidence_need,
            )
    return None


@dataclass(frozen=True, slots=True)
class EngineeringReviewQualityAssessment:
    direct_answer: EngineeringReviewQualityStatus
    abstraction_fit: EngineeringReviewQualityStatus
    material_completeness: EngineeringReviewQualityStatus
    claim_consistency: EngineeringReviewQualityStatus
    implementation_detail_budget: EngineeringReviewQualityStatus
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        direct_answer: EngineeringReviewQualityStatus,
        abstraction_fit: EngineeringReviewQualityStatus,
        material_completeness: EngineeringReviewQualityStatus,
        claim_consistency: EngineeringReviewQualityStatus,
        implementation_detail_budget: EngineeringReviewQualityStatus,
    ) -> "EngineeringReviewQualityAssessment":
        values = (
            direct_answer,
            abstraction_fit,
            material_completeness,
            claim_consistency,
            implementation_detail_budget,
        )
        if any(not isinstance(item, EngineeringReviewQualityStatus) for item in values):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "Review quality assessment must use the closed PASS/FAIL vocabulary",
            )
        core = {
            "direct_answer": direct_answer.value,
            "abstraction_fit": abstraction_fit.value,
            "material_completeness": material_completeness.value,
            "claim_consistency": claim_consistency.value,
            "implementation_detail_budget": implementation_detail_budget.value,
        }
        return cls(
            direct_answer=direct_answer,
            abstraction_fit=abstraction_fit,
            material_completeness=material_completeness,
            claim_consistency=claim_consistency,
            implementation_detail_budget=implementation_detail_budget,
            digest=digest_of(["ENGINEERING_REVIEW_QUALITY_ASSESSMENT@2", core]),
        )

    @property
    def all_pass(self) -> bool:
        return all(
            item is EngineeringReviewQualityStatus.PASS
            for item in (
                self.direct_answer,
                self.abstraction_fit,
                self.material_completeness,
                self.claim_consistency,
                self.implementation_detail_budget,
            )
        )

    def model_view(self) -> dict[str, str]:
        return {
            "direct_answer": self.direct_answer.value,
            "abstraction_fit": self.abstraction_fit.value,
            "material_completeness": self.material_completeness.value,
            "claim_consistency": self.claim_consistency.value,
            "implementation_detail_budget": (
                self.implementation_detail_budget.value
            ),
            "digest": self.digest.value,
        }


@dataclass(frozen=True, slots=True)
class EngineeringReviewMaterialObservation:
    checklist_item_id: str
    kind: MaterialObservationKind
    statement: str
    evidence_entry_ids: tuple[StableId, ...]
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        checklist_item_id: str,
        kind: MaterialObservationKind,
        statement: str,
        evidence_entry_ids: Sequence[StableId],
    ) -> "EngineeringReviewMaterialObservation":
        if not isinstance(kind, MaterialObservationKind):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "Reviewer material observation kind must use the controlled vocabulary",
            )
        references = tuple(evidence_entry_ids)
        if not references or len(references) != len(set(references)):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "Reviewer material observation requires unique Package evidence entries",
            )
        core = {
            "checklist_item_id": _reference(
                checklist_item_id, "Reviewer material observation checklist item"
            ),
            "kind": kind.value,
            "statement": _text(
                statement,
                "Reviewer material observation statement",
                maximum_bytes=8_192,
            ),
            "evidence_entry_ids": tuple(item.value for item in references),
        }
        return cls(
            checklist_item_id=core["checklist_item_id"],
            kind=kind,
            statement=core["statement"],
            evidence_entry_ids=references,
            digest=digest_of(["ENGINEERING_REVIEW_MATERIAL_OBSERVATION@1", core]),
        )

    def model_view(self) -> dict[str, object]:
        return {
            "checklist_item_id": self.checklist_item_id,
            "kind": self.kind.value,
            "statement": self.statement,
            "evidence_entry_ids": [item.value for item in self.evidence_entry_ids],
            "digest": self.digest.value,
        }


@dataclass(frozen=True, slots=True)
class EngineeringReviewChecklistAssessment:
    independent_material_conclusions: tuple[str, ...]
    application_checklist_omissions: tuple[str, ...]
    independent_material_observations: tuple[
        EngineeringReviewMaterialObservation, ...
    ]
    application_material_observation_omissions: tuple[str, ...]
    draft_material_observation_omissions: tuple[str, ...]
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        independent_material_conclusions: Sequence[str],
        application_checklist_omissions: Sequence[str],
        independent_material_observations: Sequence[
            EngineeringReviewMaterialObservation
        ],
        application_material_observation_omissions: Sequence[str],
        draft_material_observation_omissions: Sequence[str],
    ) -> "EngineeringReviewChecklistAssessment":
        independent = _unique_texts(
            independent_material_conclusions,
            "Reviewer independent material conclusions",
            maximum_items=12,
        )
        omissions = tuple(
            _text(
                item,
                "Reviewer application checklist omission",
                maximum_bytes=8_192,
            )
            for item in application_checklist_omissions
        )
        if (
            len(omissions) > 12
            or len(omissions) != len(set(omissions))
            or not set(omissions).issubset(independent)
        ):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "Reviewer checklist omissions must be unique independent conclusions",
            )
        observations = tuple(independent_material_observations)
        if not observations or len(observations) > 64:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "Reviewer must return one to sixty-four independent material observations",
            )
        expected_observations = tuple(
            EngineeringReviewMaterialObservation.create(
                checklist_item_id=item.checklist_item_id,
                kind=item.kind,
                statement=item.statement,
                evidence_entry_ids=item.evidence_entry_ids,
            )
            for item in observations
        )
        if (
            observations != expected_observations
            or len({item.digest for item in observations}) != len(observations)
            or len({item.statement for item in observations}) != len(observations)
        ):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "Reviewer independent material observations must be valid and unique",
            )
        observation_statements = {item.statement for item in observations}

        def observation_omissions(
            values: Sequence[str], label: str
        ) -> tuple[str, ...]:
            normalized = tuple(
                _text(item, label, maximum_bytes=8_192) for item in values
            )
            if (
                len(normalized) > 64
                or len(normalized) != len(set(normalized))
                or not set(normalized).issubset(observation_statements)
            ):
                raise DomainError(
                    ErrorCode.INVALID_ARGUMENT,
                    f"{label} must be unique independent observation statements",
                )
            return normalized

        application_observation_omissions = observation_omissions(
            application_material_observation_omissions,
            "Reviewer Application observation omission",
        )
        draft_observation_omissions = observation_omissions(
            draft_material_observation_omissions,
            "Reviewer Draft observation omission",
        )
        core = {
            "independent_material_conclusions": independent,
            "application_checklist_omissions": omissions,
            "independent_material_observations": tuple(
                item.digest.value for item in observations
            ),
            "application_material_observation_omissions": (
                application_observation_omissions
            ),
            "draft_material_observation_omissions": draft_observation_omissions,
        }
        return cls(
            independent_material_conclusions=independent,
            application_checklist_omissions=omissions,
            independent_material_observations=observations,
            application_material_observation_omissions=(
                application_observation_omissions
            ),
            draft_material_observation_omissions=draft_observation_omissions,
            digest=digest_of(
                ["ENGINEERING_REVIEW_CHECKLIST_ASSESSMENT@2", core]
            ),
        )

    def model_view(self) -> dict[str, object]:
        return {
            "independent_material_conclusions": list(
                self.independent_material_conclusions
            ),
            "application_checklist_omissions": list(
                self.application_checklist_omissions
            ),
            "independent_material_observations": [
                item.model_view() for item in self.independent_material_observations
            ],
            "application_material_observation_omissions": list(
                self.application_material_observation_omissions
            ),
            "draft_material_observation_omissions": list(
                self.draft_material_observation_omissions
            ),
            "digest": self.digest.value,
        }


@dataclass(frozen=True, slots=True)
class EngineeringReviewProposal:
    role_context_id: StableId
    package_digest: Digest
    draft_digest: Digest
    decision: EngineeringReviewDecision
    quality_assessment: EngineeringReviewQualityAssessment
    checklist_assessment: EngineeringReviewChecklistAssessment
    findings: tuple[EngineeringReviewFinding, ...]
    verification_request: VerificationRequestProposal | None
    digest: Digest

    @classmethod
    def create_from_findings(
        cls,
        *,
        role_context_id: StableId,
        package_digest: Digest,
        draft_digest: Digest,
        quality_assessment: EngineeringReviewQualityAssessment,
        checklist_assessment: EngineeringReviewChecklistAssessment,
        findings: Sequence[EngineeringReviewFinding] = (),
    ) -> "EngineeringReviewProposal":
        finding_tuple = tuple(findings)
        return cls.create(
            role_context_id=role_context_id,
            package_digest=package_digest,
            draft_digest=draft_digest,
            decision=_review_decision_from_findings(finding_tuple),
            quality_assessment=quality_assessment,
            checklist_assessment=checklist_assessment,
            findings=finding_tuple,
            verification_request=_verification_request_from_findings(
                package_digest=package_digest,
                findings=finding_tuple,
            ),
        )

    @classmethod
    def create(
        cls,
        *,
        role_context_id: StableId,
        package_digest: Digest,
        draft_digest: Digest,
        decision: EngineeringReviewDecision,
        quality_assessment: EngineeringReviewQualityAssessment,
        checklist_assessment: EngineeringReviewChecklistAssessment,
        findings: Sequence[EngineeringReviewFinding] = (),
        verification_request: VerificationRequestProposal | None = None,
    ) -> "EngineeringReviewProposal":
        if not isinstance(
            quality_assessment, EngineeringReviewQualityAssessment
        ):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "Review Proposal requires one closed direction quality assessment",
            )
        expected_quality = EngineeringReviewQualityAssessment.create(
            direct_answer=quality_assessment.direct_answer,
            abstraction_fit=quality_assessment.abstraction_fit,
            material_completeness=quality_assessment.material_completeness,
            claim_consistency=quality_assessment.claim_consistency,
            implementation_detail_budget=(
                quality_assessment.implementation_detail_budget
            ),
        )
        if quality_assessment != expected_quality:
            raise DomainError(
                ErrorCode.PROVIDER_RESPONSE_INVALID,
                "Review quality assessment identity is invalid",
            )
        if not isinstance(
            checklist_assessment, EngineeringReviewChecklistAssessment
        ):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "Review Proposal requires one independent checklist assessment",
            )
        expected_checklist = EngineeringReviewChecklistAssessment.create(
            independent_material_conclusions=(
                checklist_assessment.independent_material_conclusions
            ),
            application_checklist_omissions=(
                checklist_assessment.application_checklist_omissions
            ),
            independent_material_observations=(
                checklist_assessment.independent_material_observations
            ),
            application_material_observation_omissions=(
                checklist_assessment.application_material_observation_omissions
            ),
            draft_material_observation_omissions=(
                checklist_assessment.draft_material_observation_omissions
            ),
        )
        if checklist_assessment != expected_checklist:
            raise DomainError(
                ErrorCode.PROVIDER_RESPONSE_INVALID,
                "Review checklist assessment identity is invalid",
            )
        if (
            (
                checklist_assessment.application_checklist_omissions
                or checklist_assessment.application_material_observation_omissions
                or checklist_assessment.draft_material_observation_omissions
            )
            and quality_assessment.material_completeness
            is not EngineeringReviewQualityStatus.FAIL
        ):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "Reviewer checklist omissions require a failed material-completeness check",
            )
        finding_tuple = tuple(findings)
        if len({item.digest for item in finding_tuple}) != len(finding_tuple):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT, "Review Proposal contains duplicate Findings"
            )
        expected_decision = _review_decision_from_findings(finding_tuple)
        expected_verification_request = _verification_request_from_findings(
            package_digest=package_digest,
            findings=finding_tuple,
        )
        if (
            decision is not expected_decision
            or verification_request != expected_verification_request
        ):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "Review decision and verification request must be derived from Finding remediations",
            )
        if decision is EngineeringReviewDecision.APPROVED:
            if (
                not quality_assessment.all_pass
                or checklist_assessment.application_checklist_omissions
                or checklist_assessment.application_material_observation_omissions
                or checklist_assessment.draft_material_observation_omissions
                or finding_tuple
                or verification_request
            ):
                raise DomainError(
                    ErrorCode.INVALID_ARGUMENT,
                    "APPROVED review requires all direction checks and no Finding or verification request",
                )
        core = {
            "role_context_id": role_context_id.value,
            "package_digest": package_digest.value,
            "draft_digest": draft_digest.value,
            "decision": decision.value,
            "quality_assessment": quality_assessment.digest.value,
            "checklist_assessment": checklist_assessment.digest.value,
            "findings": tuple(item.digest.value for item in finding_tuple),
            "verification_request": (
                verification_request.digest.value if verification_request else None
            ),
        }
        return cls(
            role_context_id=role_context_id,
            package_digest=package_digest,
            draft_digest=draft_digest,
            decision=decision,
            quality_assessment=quality_assessment,
            checklist_assessment=checklist_assessment,
            findings=finding_tuple,
            verification_request=verification_request,
            digest=digest_of(["ENGINEERING_REVIEW_PROPOSAL@4", core]),
        )


@dataclass(frozen=True, slots=True)
class EngineeringAnswerReview:
    review_id: StableId
    attempt: int
    package_digest: Digest
    draft_digest: Digest
    decision: EngineeringReviewDecision
    quality_assessment: EngineeringReviewQualityAssessment
    checklist_assessment: EngineeringReviewChecklistAssessment
    findings: tuple[EngineeringReviewFinding, ...]
    verification_request: VerificationRequestProposal | None
    proposal_digest: Digest
    digest: Digest

    @classmethod
    def accept(
        cls,
        *,
        package: QuestionEvidencePackage,
        draft: EngineeringAnswerDraft,
        understanding: QuestionUnderstanding,
        expected_role_context_id: StableId,
        proposal: EngineeringReviewProposal,
        attempt: int,
    ) -> "EngineeringAnswerReview":
        expected_findings = tuple(
            EngineeringReviewFinding.create(
                finding_code=item.finding_code,
                checklist_item_id=item.checklist_item_id,
                claim_id=item.claim_id,
                description=item.description,
                remediation=item.remediation,
                existing_evidence_entry_ids=item.existing_evidence_entry_ids,
                evidence_class=item.evidence_class,
                evidence_need=item.evidence_need,
            )
            for item in proposal.findings
        )
        if expected_findings != proposal.findings:
            raise DomainError(
                ErrorCode.PROVIDER_RESPONSE_INVALID,
                "Review Finding identity is invalid",
            )
        request = proposal.verification_request
        expected_request = None
        if request is not None:
            expected_request = VerificationRequestProposal.create(
                package_digest=request.package_digest,
                checklist_item_id=request.checklist_item_id,
                claim_id=request.claim_id,
                evidence_class=request.evidence_class,
                evidence_need=request.evidence_need,
            )
            if request != expected_request:
                raise DomainError(
                    ErrorCode.PROVIDER_RESPONSE_INVALID,
                    "verification Request identity is invalid",
                )
        expected_proposal = EngineeringReviewProposal.create(
            role_context_id=proposal.role_context_id,
            package_digest=proposal.package_digest,
            draft_digest=proposal.draft_digest,
            decision=proposal.decision,
            quality_assessment=proposal.quality_assessment,
            checklist_assessment=proposal.checklist_assessment,
            findings=expected_findings,
            verification_request=expected_request,
        )
        if proposal != expected_proposal:
            raise DomainError(
                ErrorCode.PROVIDER_RESPONSE_INVALID,
                "Review Proposal identity is invalid",
            )
        if (
            proposal.role_context_id != expected_role_context_id
            or proposal.package_digest != package.digest
            or proposal.draft_digest != draft.digest
            or draft.package_digest != package.digest
            or attempt < 1
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Review Proposal does not bind the current Package, Draft, and fresh context",
            )
        checklist_ids = {item.item_id for item in understanding.checklist}
        claim_ids = {item.claim_id for item in draft.claims}
        support_ids = {item.entry_id for item in package.support_citation}
        boundary_ids = {item.entry_id for item in package.boundary_audit}
        for observation in proposal.checklist_assessment.independent_material_observations:
            if observation.checklist_item_id not in checklist_ids:
                raise DomainError(
                    ErrorCode.PROVIDER_RESPONSE_INVALID,
                    "Reviewer material observation refers to an unknown checklist item",
                )
            references = set(observation.evidence_entry_ids)
            admissible = (
                boundary_ids
                if observation.kind is MaterialObservationKind.LIMITATION
                else support_ids
            )
            if not references.issubset(admissible):
                raise DomainError(
                    ErrorCode.CONTROL_STATE_DENIED,
                    "Reviewer material observation cites the wrong Package partition",
                )
        for finding in proposal.findings:
            if finding.checklist_item_id and finding.checklist_item_id not in checklist_ids:
                raise DomainError(
                    ErrorCode.PROVIDER_RESPONSE_INVALID,
                    "Review Finding refers to an unknown checklist item",
                )
            if finding.claim_id and finding.claim_id not in claim_ids:
                raise DomainError(
                    ErrorCode.PROVIDER_RESPONSE_INVALID,
                    "Review Finding refers to an unknown answer Claim",
                )
            if (
                finding.remediation
                is EngineeringReviewRemediation.REWRITE_WITH_EXISTING_EVIDENCE
                and not set(finding.existing_evidence_entry_ids).issubset(
                    support_ids | boundary_ids
                )
            ):
                raise DomainError(
                    ErrorCode.CONTROL_STATE_DENIED,
                    "rewrite Finding cites evidence outside the current Package",
                )
        if request is not None:
            if (
                request.package_digest != package.digest
                or request.checklist_item_id not in checklist_ids
                or (request.claim_id is not None and request.claim_id not in claim_ids)
            ):
                raise DomainError(
                    ErrorCode.PROVIDER_RESPONSE_INVALID,
                    "verification request is not a specific gap on the current Package",
                )
            if not any(
                finding.remediation
                is EngineeringReviewRemediation.INVESTIGATE_MISSING_EVIDENCE
                and finding.checklist_item_id == request.checklist_item_id
                and (
                    request.claim_id is None
                    or finding.claim_id == request.claim_id
                )
                and finding.evidence_class is request.evidence_class
                and finding.evidence_need == request.evidence_need
                for finding in proposal.findings
            ):
                raise DomainError(
                    ErrorCode.PROVIDER_RESPONSE_INVALID,
                    "verification Request is not bound to its concrete Review Finding",
                )
        core = {
            "attempt": attempt,
            "package_digest": package.digest.value,
            "draft_digest": draft.digest.value,
            "decision": proposal.decision.value,
            "quality_assessment": proposal.quality_assessment.digest.value,
            "checklist_assessment": proposal.checklist_assessment.digest.value,
            "findings": tuple(item.digest.value for item in proposal.findings),
            "verification_request": request.digest.value if request else None,
            "proposal_digest": proposal.digest.value,
        }
        digest = digest_of(["ENGINEERING_ANSWER_REVIEW@3", core])
        return cls(
            review_id=_stable_id("engineering_review", core),
            attempt=attempt,
            package_digest=package.digest,
            draft_digest=draft.digest,
            decision=proposal.decision,
            quality_assessment=proposal.quality_assessment,
            checklist_assessment=proposal.checklist_assessment,
            findings=proposal.findings,
            verification_request=request,
            proposal_digest=proposal.digest,
            digest=digest,
        )


class EngineeringAnswerReviewerRole(Protocol):
    def review(
        self,
        *,
        original_question: str,
        understanding: QuestionUnderstanding,
        package: QuestionEvidencePackage,
        draft: EngineeringAnswerDraft,
        role_context_id: StableId,
    ) -> EngineeringReviewProposal: ...


@dataclass(frozen=True, slots=True)
class AuthorizedEngineeringAnswer:
    authorization_id: StableId
    request_digest: Digest
    package_digest: Digest
    draft_digest: Digest
    review_digest: Digest
    body: str
    claim_ids: tuple[str, ...]
    citation_entry_ids: tuple[StableId, ...]
    digest: Digest

    @classmethod
    def authorize(
        cls,
        *,
        request: EngineeringQuestionRequest,
        package: QuestionEvidencePackage,
        draft: EngineeringAnswerDraft,
        review: EngineeringAnswerReview,
    ) -> "AuthorizedEngineeringAnswer":
        if (
            review.decision is not EngineeringReviewDecision.APPROVED
            or not review.quality_assessment.all_pass
            or review.checklist_assessment.application_checklist_omissions
            or review.checklist_assessment.application_material_observation_omissions
            or review.checklist_assessment.draft_material_observation_omissions
            or review.findings
            or review.package_digest != package.digest
            or review.draft_digest != draft.digest
            or draft.package_digest != package.digest
            or package.request_digest != request.digest
        ):
            raise DomainError(
                ErrorCode.CONTROL_STATE_DENIED,
                "only a finding-free Review of the current Package and Draft can authorize delivery",
            )
        citation_ids = tuple(
            dict.fromkeys(
                reference
                for claim in draft.claims
                if claim.claim_id in draft.default_body_claim_ids
                if claim.kind is AnswerClaimKind.AFFIRMATIVE
                for reference in claim.evidence_entry_ids
            )
        )
        core = {
            "request_digest": request.digest.value,
            "package_digest": package.digest.value,
            "draft_digest": draft.digest.value,
            "review_digest": review.digest.value,
            "body": draft.body,
            "claim_ids": tuple(item.claim_id for item in draft.claims),
            "citation_entry_ids": tuple(item.value for item in citation_ids),
        }
        digest = digest_of(["AUTHORIZED_ENGINEERING_ANSWER@2", core])
        return cls(
            authorization_id=_stable_id("engineering_answer", core),
            request_digest=request.digest,
            package_digest=package.digest,
            draft_digest=draft.digest,
            review_digest=review.digest,
            body=draft.body,
            claim_ids=core["claim_ids"],
            citation_entry_ids=citation_ids,
            digest=digest,
        )


@dataclass(frozen=True, slots=True)
class EngineeringQuestionExecutionResult:
    result_id: StableId
    status: EngineeringQuestionResultStatus
    request: EngineeringQuestionRequest
    understanding: QuestionUnderstanding
    cognition: WorldModelCognitionContext
    ledgers: tuple[EvidenceLedger, ...]
    packages: tuple[QuestionEvidencePackage, ...]
    retrieval_results: tuple[RetrievalResult, ...]
    broker_decisions: tuple[SourceBrokerDecision, ...]
    drafts: tuple[EngineeringAnswerDraft, ...]
    reviews: tuple[EngineeringAnswerReview, ...]
    authorized_answer: AuthorizedEngineeringAnswer | None
    usage: EngineeringQuestionResourceUsage
    terminal_reason: str
    elapsed_milliseconds: int
    production_activation: str
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        status: EngineeringQuestionResultStatus,
        request: EngineeringQuestionRequest,
        understanding: QuestionUnderstanding,
        cognition: WorldModelCognitionContext,
        ledgers: Sequence[EvidenceLedger],
        packages: Sequence[QuestionEvidencePackage],
        retrieval_results: Sequence[RetrievalResult],
        broker_decisions: Sequence[SourceBrokerDecision],
        drafts: Sequence[EngineeringAnswerDraft],
        reviews: Sequence[EngineeringAnswerReview],
        authorized_answer: AuthorizedEngineeringAnswer | None,
        usage: EngineeringQuestionResourceUsage,
        terminal_reason: str,
        elapsed_milliseconds: int,
    ) -> "EngineeringQuestionExecutionResult":
        if status is EngineeringQuestionResultStatus.APPROVED:
            if authorized_answer is None:
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "approved Engineering QA Result requires an authorized answer",
                )
        elif authorized_answer is not None:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "failed Engineering QA Result cannot carry an authorized answer",
            )
        if elapsed_milliseconds < 0:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT, "elapsed time cannot be negative"
            )
        ledger_tuple = tuple(ledgers)
        package_tuple = tuple(packages)
        result_tuple = tuple(retrieval_results)
        decision_tuple = tuple(broker_decisions)
        draft_tuple = tuple(drafts)
        review_tuple = tuple(reviews)
        if (
            not ledger_tuple
            or not package_tuple
            or len(ledger_tuple) != len(package_tuple)
            or understanding.request_digest != request.digest
            or cognition.request_digest != request.digest
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Engineering QA Result lacks one complete request-bound Ledger/Package chain",
            )
        for index, (ledger, package) in enumerate(
            zip(ledger_tuple, package_tuple), 1
        ):
            ledger.validate_integrity()
            prior_digest = package_tuple[index - 2].digest if index > 1 else None
            prior_ledger_seal = (
                ledger_tuple[index - 2].seal_digest if index > 1 else None
            )
            if (
                ledger.generation != index
                or ledger.request_digest != request.digest
                or ledger.seal_digest is None
                or ledger.parent_seal_digest != prior_ledger_seal
                or package.package_revision != index
                or package.request_digest != request.digest
                or package.understanding_digest != understanding.digest
                or package.cognition_context_digest != cognition.digest
                or package.ledger_id != ledger.ledger_id
                or package.ledger_generation != ledger.generation
                or package.ledger_final_prefix_digest != ledger.prefix_digest
                or package.ledger_seal_digest != ledger.seal_digest
                or package.prior_package_digest != prior_digest
            ):
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "Engineering QA Result Ledger/Package chain identity is invalid",
                )
        package_digests = {item.digest for item in package_tuple}
        draft_digests = {item.digest for item in draft_tuple}
        if any(item.package_digest not in package_digests for item in draft_tuple) or any(
            item.package_digest not in package_digests
            or item.draft_digest not in draft_digests
            for item in review_tuple
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Engineering QA Result contains a Draft or Review outside its Package chain",
            )
        if authorized_answer is not None:
            if (
                not draft_tuple
                or not review_tuple
                or authorized_answer.request_digest != request.digest
                or authorized_answer.package_digest != package_tuple[-1].digest
                or authorized_answer.draft_digest != draft_tuple[-1].digest
                or authorized_answer.review_digest != review_tuple[-1].digest
            ):
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "authorized answer does not bind the current Result chain",
                )
        core = {
            "status": status.value,
            "request_digest": request.digest.value,
            "understanding_digest": understanding.digest.value,
            "cognition_digest": cognition.digest.value,
            "ledgers": tuple(
                item.seal_digest.value if item.seal_digest else item.prefix_digest.value
                for item in ledger_tuple
            ),
            "packages": tuple(item.digest.value for item in package_tuple),
            "retrieval_results": tuple(item.digest.value for item in result_tuple),
            "broker_decisions": tuple(item.digest.value for item in decision_tuple),
            "drafts": tuple(item.digest.value for item in draft_tuple),
            "reviews": tuple(item.digest.value for item in review_tuple),
            "authorized_answer": (
                authorized_answer.digest.value if authorized_answer else None
            ),
            "usage": usage,
            "terminal_reason": _reference(
                terminal_reason, "Engineering QA terminal reason"
            ),
            "elapsed_milliseconds": elapsed_milliseconds,
            "production_activation": "NOT_EXECUTED",
        }
        digest = digest_of(["ENGINEERING_QUESTION_RESULT@1", core])
        return cls(
            result_id=_stable_id("engineering_result", core),
            status=status,
            request=request,
            understanding=understanding,
            cognition=cognition,
            ledgers=ledger_tuple,
            packages=package_tuple,
            retrieval_results=result_tuple,
            broker_decisions=decision_tuple,
            drafts=draft_tuple,
            reviews=review_tuple,
            authorized_answer=authorized_answer,
            usage=usage,
            terminal_reason=core["terminal_reason"],
            elapsed_milliseconds=elapsed_milliseconds,
            production_activation="NOT_EXECUTED",
            digest=digest,
        )

    @property
    def current_package(self) -> QuestionEvidencePackage | None:
        return self.packages[-1] if self.packages else None

    @property
    def current_draft(self) -> EngineeringAnswerDraft | None:
        return self.drafts[-1] if self.drafts else None

    @property
    def current_review(self) -> EngineeringAnswerReview | None:
        return self.reviews[-1] if self.reviews else None

    def citation(self, entry_id: StableId) -> SupportCitationEntry:
        package = self.current_package
        if package is None or self.authorized_answer is None:
            raise DomainError(
                ErrorCode.CONTROL_STATE_DENIED,
                "Engineering QA Result has no authorized answer citations",
            )
        if entry_id not in self.authorized_answer.citation_entry_ids:
            raise DomainError(
                ErrorCode.SOURCE_TARGET_NOT_FOUND,
                "citation is not referenced by the authorized answer",
            )
        for entry in package.support_citation:
            if entry.entry_id == entry_id:
                return entry
        raise DomainError(
            ErrorCode.SOURCE_TARGET_NOT_FOUND,
            "citation is not an admissible entry in the current Package",
        )

    def model_view(self) -> dict[str, object]:
        package = self.current_package
        draft = self.current_draft
        review = self.current_review
        authorized_citation_ids = (
            set(self.authorized_answer.citation_entry_ids)
            if self.authorized_answer
            else set()
        )
        return {
            "result_id": self.result_id.value,
            "result_digest": self.digest.value,
            "status": self.status.value,
            "mode": ENGINEERING_QA_MODE,
            "protocol": ENGINEERING_QA_PROTOCOL,
            "environment": "DIRECTION_PREVIEW",
            "acceptance": "NOT_ACCEPTANCE",
            "production_activation": self.production_activation,
            "request": {
                "request_id": self.request.request_id.value,
                "original_question": self.request.original_question,
                "repository_revision": self.request.repository_revision,
                "request_digest": self.request.digest.value,
            },
            "answer": (
                {
                    "authorization_id": self.authorized_answer.authorization_id.value,
                    "body": self.authorized_answer.body,
                    "draft": draft.model_view() if draft else None,
                }
                if self.authorized_answer
                else None
            ),
            "limitation": (
                None
                if self.authorized_answer
                else {
                    "reason": self.terminal_reason,
                    "delivery_authorized": False,
                }
            ),
            "citations": (
                [
                    {
                        "entry_id": item.entry_id.value,
                        "origin_class": item.origin_class,
                        "evidence_class": item.evidence_class.value,
                        "locator": item.locator,
                        "content_digest": item.content_digest.value,
                    }
                    for item in package.support_citation
                    if item.entry_id in authorized_citation_ids
                ]
                if package and self.authorized_answer
                else []
            ),
            "developer_details": {
                "terminal_reason": self.terminal_reason,
                "answer_reached": bool(self.drafts),
                "review_reached": bool(self.reviews),
                "question_understanding_digest": self.understanding.digest.value,
                "cognition_context": self.cognition.model_view(),
                "ledger_seals": [
                    item.seal_digest.value if item.seal_digest else None
                    for item in self.ledgers
                ],
                "package_digests": [item.digest.value for item in self.packages],
                "broker_decisions": [
                    {
                        "decision_id": item.decision_id.value,
                        "status": item.status.value,
                        "reason_code": item.reason_code,
                    }
                    for item in self.broker_decisions
                ],
                "retrieval_result_ids": [
                    item.result_id.value for item in self.retrieval_results
                ],
                "review": (
                    {
                        "review_id": review.review_id.value,
                        "decision": review.decision.value,
                        "quality_assessment": (
                            review.quality_assessment.model_view()
                        ),
                        "checklist_assessment": (
                            review.checklist_assessment.model_view()
                        ),
                        "findings": [
                            item.finding_code for item in review.findings
                        ],
                    }
                    if review
                    else None
                ),
                "usage": {
                    field: getattr(self.usage, field)
                    for field in self.usage.__dataclass_fields__
                },
                "elapsed_milliseconds": self.elapsed_milliseconds,
            },
        }


@dataclass(frozen=True, slots=True)
class _InvestigationRun:
    ledger: EvidenceLedger
    retrieval_results: tuple[RetrievalResult, ...]
    broker_decisions: tuple[SourceBrokerDecision, ...]
    dispositions: tuple[ChecklistDisposition, ...]
    usage: EngineeringQuestionResourceUsage
    terminal_reason: str


@dataclass(frozen=True, slots=True)
class _AnswerReviewRun:
    usage: EngineeringQuestionResourceUsage
    drafts: tuple[EngineeringAnswerDraft, ...]
    reviews: tuple[EngineeringAnswerReview, ...]
    authorized_answer: AuthorizedEngineeringAnswer | None
    verification_request: VerificationRequestProposal | None
    terminal_reason: str


class EngineeringQuestionAnsweringService:
    """Application-owned adaptive investigation and answer state machine."""

    def __init__(
        self,
        *,
        question_understanding_role: QuestionUnderstandingRole,
        cognition_projector: WorldModelCognitionProjector,
        initial_investigation_role: InitialInvestigationRole,
        verification_investigation_role: VerificationInvestigationRole,
        source_broker: SourceBroker,
        retrieval_worker: RetrievalWorker,
        answer_role: EngineeringAnswerRole,
        reviewer_role: EngineeringAnswerReviewerRole,
        clock_ns=monotonic_ns,
    ) -> None:
        roles = (
            question_understanding_role,
            initial_investigation_role,
            verification_investigation_role,
            answer_role,
            reviewer_role,
        )
        if len({id(role) for role in roles}) != len(roles):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "Engineering QA model roles require independent role instances",
            )
        self._question_understanding_role = question_understanding_role
        self._cognition_projector = cognition_projector
        self._initial_investigation_role = initial_investigation_role
        self._verification_investigation_role = verification_investigation_role
        self._source_broker = source_broker
        self._retrieval_worker = retrieval_worker
        self._answer_role = answer_role
        self._reviewer_role = reviewer_role
        self._clock_ns = clock_ns

    def answer(
        self, request: EngineeringQuestionRequest
    ) -> EngineeringQuestionExecutionResult:
        expected_request = EngineeringQuestionRequest.create(
            request_ref=request.request_ref,
            original_question=request.original_question,
            response_language=request.response_language,
            repository_id=request.repository_id,
            binding_id=request.binding_id,
            repository_revision=request.repository_revision,
            source_profile_ref=request.source_profile_ref,
            source_profile_digest=request.source_profile_digest,
            world_model_read_authority_digest=request.world_model_read_authority_digest,
            source_allowlist=request.source_allowlist,
            registered_operations=request.registered_operations,
            provider_disclosure_policy=request.provider_disclosure_policy,
            limits=request.limits,
        )
        if request != expected_request:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Engineering Question Request identity is invalid",
            )
        started_ns = self._clock_ns()
        used_contexts: set[StableId] = set()
        usage = EngineeringQuestionResourceUsage()

        understanding_context = self._fresh_context(
            request=request,
            role="question_understanding",
            ordinal=1,
            used_contexts=used_contexts,
        )
        self._require_role_budget(request=request, usage=usage)
        understanding_proposal = self._question_understanding_role.understand(
            request=request, role_context_id=understanding_context
        )
        usage = replace(usage, total_role_calls=usage.total_role_calls + 1)
        self._require_pre_ledger_wall_time_budget(
            request=request,
            started_ns=started_ns,
            stage="Question Understanding",
        )
        understanding = QuestionUnderstanding.accept(
            request=request,
            expected_role_context_id=understanding_context,
            proposal=understanding_proposal,
        )

        cognition = self._cognition_projector.project(request=request)
        self._require_pre_ledger_wall_time_budget(
            request=request,
            started_ns=started_ns,
            stage="World Model Cognition projection",
        )
        expected_cognition_items = tuple(
            CognitionItem.create(
                dimension=item.dimension,
                statement=item.statement,
                modality=item.modality,
                context_ref=item.context_ref,
                source_revision=item.source_revision,
                locator=item.locator,
                support_references=item.support_references,
                coverage=item.coverage,
            )
            for item in cognition.items
        )
        expected_cognition = WorldModelCognitionContext.create(
            request=request,
            scope_ref=cognition.scope_ref,
            context_ref=cognition.context_ref,
            schema_ref=cognition.schema_ref,
            snapshot_ids=cognition.snapshot_ids,
            read_authority_digest=cognition.read_authority_digest,
            source_revision=cognition.source_revision,
            items=expected_cognition_items,
            coverage=cognition.coverage,
            conflicts=cognition.conflicts,
            unknowns=cognition.unknowns,
        )
        if cognition != expected_cognition:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "World Model Cognition Context identity is invalid",
            )
        cognition_bytes = len(canonical_json_bytes(cognition.model_view()))
        if cognition_bytes > request.limits.maximum_world_model_bytes:
            raise DomainError(
                ErrorCode.BUDGET_EXHAUSTED,
                "World Model Cognition Context byte fuse is exhausted",
            )
        usage = replace(usage, world_model_bytes=cognition_bytes)

        ledger = EvidenceLedger.start(request=request, cognition=cognition)
        initial_attempt = _stable_id(
            "investigation_attempt",
            [request.digest.value, InvestigationKind.INITIAL.value, 1],
        )
        initial = self._run_investigation(
            request=request,
            understanding=understanding,
            cognition=cognition,
            ledger=ledger,
            investigation_kind=InvestigationKind.INITIAL,
            attempt_id=initial_attempt,
            current_package=None,
            verification_request=None,
            existing_results=(),
            existing_decisions=(),
            usage=usage,
            used_contexts=used_contexts,
            started_ns=started_ns,
        )
        ledgers: list[EvidenceLedger] = [initial.ledger]
        results = list(initial.retrieval_results)
        decisions = list(initial.broker_decisions)
        packages: list[QuestionEvidencePackage] = []
        drafts: list[EngineeringAnswerDraft] = []
        reviews: list[EngineeringAnswerReview] = []
        usage = initial.usage

        package = QuestionEvidencePackage.seal(
            request=request,
            understanding=understanding,
            cognition=cognition,
            ledger=initial.ledger,
            retrieval_results=results,
            broker_decisions=decisions,
            checklist_dispositions=initial.dispositions,
            package_revision=initial.ledger.generation,
        )
        packages.append(package)
        if initial.ledger.terminal_status is LedgerTerminalStatus.FAILED_CLOSED:
            return self._result(
                status=EngineeringQuestionResultStatus.FAILED_CLOSED,
                request=request,
                understanding=understanding,
                cognition=cognition,
                ledgers=ledgers,
                packages=packages,
                results=results,
                decisions=decisions,
                drafts=drafts,
                reviews=reviews,
                authorized_answer=None,
                usage=usage,
                terminal_reason=initial.terminal_reason,
                started_ns=started_ns,
            )

        rewrite_findings: tuple[EngineeringReviewFinding, ...] = ()
        verification_count = 0
        while True:
            answer_run = self._answer_and_review(
                request=request,
                understanding=understanding,
                package=package,
                usage=usage,
                used_contexts=used_contexts,
                initial_rewrite_findings=rewrite_findings,
                started_ns=started_ns,
            )
            drafts.extend(answer_run.drafts)
            reviews.extend(answer_run.reviews)
            usage = answer_run.usage
            if answer_run.authorized_answer is not None:
                return self._result(
                    status=EngineeringQuestionResultStatus.APPROVED,
                    request=request,
                    understanding=understanding,
                    cognition=cognition,
                    ledgers=ledgers,
                    packages=packages,
                    results=results,
                    decisions=decisions,
                    drafts=drafts,
                    reviews=reviews,
                    authorized_answer=answer_run.authorized_answer,
                    usage=usage,
                    terminal_reason="APPROVED",
                    started_ns=started_ns,
                )
            verification_request = answer_run.verification_request
            if verification_request is None:
                return self._result(
                    status=EngineeringQuestionResultStatus.FAILED_CLOSED,
                    request=request,
                    understanding=understanding,
                    cognition=cognition,
                    ledgers=ledgers,
                    packages=packages,
                    results=results,
                    decisions=decisions,
                    drafts=drafts,
                    reviews=reviews,
                    authorized_answer=None,
                    usage=usage,
                    terminal_reason=answer_run.terminal_reason,
                    started_ns=started_ns,
                )
            if verification_count >= request.limits.maximum_verification_investigations:
                return self._result(
                    status=EngineeringQuestionResultStatus.FAILED_CLOSED,
                    request=request,
                    understanding=understanding,
                    cognition=cognition,
                    ledgers=ledgers,
                    packages=packages,
                    results=results,
                    decisions=decisions,
                    drafts=drafts,
                    reviews=reviews,
                    authorized_answer=None,
                    usage=usage,
                    terminal_reason="VERIFICATION_INVESTIGATION_FUSE_EXHAUSTED",
                    started_ns=started_ns,
                )
            verification_count += 1
            usage = replace(
                usage,
                verification_investigations=usage.verification_investigations + 1,
            )
            successor = initial.ledger.successor(
                verification_request_id=verification_request.verification_request_id,
                verification_request_digest=verification_request.digest,
                prior_package_digest=package.digest,
                maximum_bytes=request.limits.maximum_ledger_bytes,
                verification_details={
                    "checklist_item_id": verification_request.checklist_item_id,
                    "evidence_class": verification_request.evidence_class.value,
                    "evidence_need": verification_request.evidence_need,
                    **(
                        {"claim_id": verification_request.claim_id}
                        if verification_request.claim_id
                        else {}
                    ),
                },
            )
            verification_attempt = _stable_id(
                "verification_attempt",
                [
                    request.digest.value,
                    package.digest.value,
                    verification_request.digest.value,
                    verification_count,
                ],
            )
            verification = self._run_investigation(
                request=request,
                understanding=understanding,
                cognition=cognition,
                ledger=successor,
                investigation_kind=InvestigationKind.VERIFICATION,
                attempt_id=verification_attempt,
                current_package=package,
                verification_request=verification_request,
                existing_results=tuple(results),
                existing_decisions=tuple(decisions),
                usage=usage,
                used_contexts=used_contexts,
                started_ns=started_ns,
            )
            ledgers.append(verification.ledger)
            results = list(verification.retrieval_results)
            decisions = list(verification.broker_decisions)
            usage = verification.usage
            next_package = QuestionEvidencePackage.seal(
                request=request,
                understanding=understanding,
                cognition=cognition,
                ledger=verification.ledger,
                retrieval_results=results,
                broker_decisions=decisions,
                checklist_dispositions=verification.dispositions,
                package_revision=verification.ledger.generation,
                prior_package_digest=package.digest,
            )
            packages.append(next_package)
            package = next_package
            initial = verification
            rewrite_findings = ()
            if verification.ledger.terminal_status is LedgerTerminalStatus.FAILED_CLOSED:
                return self._result(
                    status=EngineeringQuestionResultStatus.FAILED_CLOSED,
                    request=request,
                    understanding=understanding,
                    cognition=cognition,
                    ledgers=ledgers,
                    packages=packages,
                    results=results,
                    decisions=decisions,
                    drafts=drafts,
                    reviews=reviews,
                    authorized_answer=None,
                    usage=usage,
                    terminal_reason=verification.terminal_reason,
                    started_ns=started_ns,
                )

    def _run_investigation(
        self,
        *,
        request: EngineeringQuestionRequest,
        understanding: QuestionUnderstanding,
        cognition: WorldModelCognitionContext,
        ledger: EvidenceLedger,
        investigation_kind: InvestigationKind,
        attempt_id: StableId,
        current_package: QuestionEvidencePackage | None,
        verification_request: VerificationRequestProposal | None,
        existing_results: tuple[RetrievalResult, ...],
        existing_decisions: tuple[SourceBrokerDecision, ...],
        usage: EngineeringQuestionResourceUsage,
        used_contexts: set[StableId],
        started_ns: int,
    ) -> _InvestigationRun:
        usage = replace(usage, no_progress_steps=0)
        results = list(existing_results)
        attempt_result_start = len(results)
        decisions = list(existing_decisions)
        locator_catalog = {
            item.locator_reference: item
            for result in results
            for item in result.items
        }
        progress_digests = {result.progress_digest for result in results}
        registered_evidence_classes = (
            self._source_broker.registered_evidence_classes(request=request)
        )
        required_evidence_classes = understanding.required_evidence_classes
        required_evidence_paths = understanding.required_evidence_paths
        if (
            investigation_kind is InvestigationKind.VERIFICATION
            and verification_request is not None
        ):
            required_evidence_classes = (verification_request.evidence_class,)
            required_evidence_paths = ()
        required_path_classes = tuple(
            self._source_broker.evidence_class_for_path(
                request=request,
                path=path,
            )
            for path in required_evidence_paths
        )
        if any(
            evidence_class not in required_evidence_classes
            for evidence_class in required_path_classes
        ):
            raise DomainError(
                ErrorCode.PROVIDER_RESPONSE_INVALID,
                "question understanding required path lacks its registered evidence class",
            )
        required_path_locators = self._source_broker.issue_required_path_locators(
            request=request,
            attempt_id=attempt_id,
            paths=required_evidence_paths,
        )
        required_path_locator_catalog = {
            item.locator_reference: item for item in required_path_locators
        }
        investigated_evidence_classes: set[EngineeringEvidenceClass] = set()
        step_index = 0
        local_calls = 0
        while True:
            step_index += 1
            local_calls += 1
            if (
                usage.investigation_role_calls
                >= request.limits.maximum_investigation_steps
                or (
                    investigation_kind is InvestigationKind.INITIAL
                    and local_calls
                    > request.limits.maximum_initial_investigation_calls
                )
            ):
                return self._fail_investigation(
                    request=request,
                    understanding=understanding,
                    ledger=ledger,
                    retrieval_results=tuple(results),
                    broker_decisions=tuple(decisions),
                    usage=usage,
                    reason="INVESTIGATION_STEP_FUSE_EXHAUSTED",
                )
            if self._wall_time_exhausted(request=request, started_ns=started_ns):
                return self._fail_investigation(
                    request=request,
                    understanding=understanding,
                    ledger=ledger,
                    retrieval_results=tuple(results),
                    broker_decisions=tuple(decisions),
                    usage=usage,
                    reason="WALL_TIME_FUSE_EXHAUSTED",
                )
            if (
                usage.total_role_calls + 3
                > request.limits.maximum_total_model_role_calls
            ):
                return self._fail_investigation(
                    request=request,
                    understanding=understanding,
                    ledger=ledger,
                    retrieval_results=tuple(results),
                    broker_decisions=tuple(decisions),
                    usage=usage,
                    reason="INDEPENDENT_REVIEW_RESERVE_EXHAUSTED",
                )
            role = (
                "initial_investigation"
                if investigation_kind is InvestigationKind.INITIAL
                else "verification_investigation"
            )
            role_context = self._fresh_context(
                request=request,
                role=role,
                ordinal=usage.investigation_role_calls + 1,
                used_contexts=used_contexts,
            )
            disposition_reference_eligibility = _disposition_reference_eligibility(
                cognition=cognition,
                ledger=ledger,
                retrieval_results=tuple(results),
                broker_decisions=tuple(decisions),
            )
            if investigation_kind is InvestigationKind.INITIAL:
                investigation_input = InitialInvestigationInput(
                    attempt_id=attempt_id,
                    role_context_id=role_context,
                    step_index=step_index,
                    request=request,
                    understanding=understanding,
                    cognition=cognition,
                    ledger=ledger,
                    retrieval_results=tuple(results),
                    disposition_reference_eligibility=disposition_reference_eligibility,
                    registered_evidence_classes=registered_evidence_classes,
                    required_evidence_classes=required_evidence_classes,
                    investigated_evidence_classes=tuple(
                        item
                        for item in registered_evidence_classes
                        if item in investigated_evidence_classes
                    ),
                    required_evidence_paths=required_evidence_paths,
                    required_path_locators=required_path_locators,
                )
                proposal = self._initial_investigation_role.propose(
                    investigation_input
                )
            else:
                if current_package is None or verification_request is None:
                    raise DomainError(
                        ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                        "verification investigation lacks its immutable gap and current Package",
                    )
                verification_input = VerificationInvestigationInput(
                    attempt_id=attempt_id,
                    role_context_id=role_context,
                    step_index=step_index,
                    verification_request=verification_request,
                    current_package=current_package,
                    ledger=ledger,
                    retrieval_results=tuple(results[attempt_result_start:]),
                    disposition_reference_eligibility=disposition_reference_eligibility,
                    registered_evidence_classes=registered_evidence_classes,
                    required_evidence_classes=required_evidence_classes,
                    investigated_evidence_classes=tuple(
                        item
                        for item in registered_evidence_classes
                        if item in investigated_evidence_classes
                    ),
                    required_evidence_paths=required_evidence_paths,
                    required_path_locators=required_path_locators,
                )
                verification_input.validate_new_result_closure()
                proposal = self._verification_investigation_role.propose(
                    verification_input
                )
                investigation_input = verification_input
            usage = replace(
                usage,
                total_role_calls=usage.total_role_calls + 1,
                investigation_role_calls=usage.investigation_role_calls + 1,
            )
            if self._wall_time_exhausted(request=request, started_ns=started_ns):
                return self._fail_investigation(
                    request=request,
                    understanding=understanding,
                    ledger=ledger,
                    retrieval_results=tuple(results),
                    broker_decisions=tuple(decisions),
                    usage=usage,
                    reason="WALL_TIME_FUSE_EXHAUSTED",
                )
            self._validate_investigation_proposal(
                request=request,
                understanding=understanding,
                ledger=ledger,
                proposal=proposal,
                expected_kind=investigation_kind,
                expected_attempt_id=attempt_id,
                expected_role_context_id=role_context,
                expected_step_index=step_index,
                eligible_locator_references=(
                    investigation_input.eligible_locator_references
                ),
                disposition_reference_eligibility=disposition_reference_eligibility,
            )
            pre_proposal_ledger = ledger
            proposal_details = {
                "investigation_kind": investigation_kind.value,
                "attempt_id": proposal.attempt_id.value,
                "operation": proposal.operation.value,
                "step_index": str(step_index),
            }
            if proposal.evidence_class is not None:
                proposal_details["evidence_class"] = proposal.evidence_class.value
            if proposal.query is not None:
                proposal_details["query"] = proposal.query
            if proposal.locator_reference is not None:
                proposal_details["locator_reference"] = (
                    proposal.locator_reference.value
                )
            ledger = ledger.append(
                kind=LedgerEntryKind.INVESTIGATION_PROPOSAL,
                subject_id=proposal.proposal_id.value,
                subject_digest=proposal.digest,
                references=tuple(item.value for item in proposal.basis_entry_ids),
                details=proposal_details,
                maximum_bytes=request.limits.maximum_ledger_bytes,
            )
            if proposal.operation is InvestigationOperation.FINISH:
                unread_required_paths = (
                    investigation_input.unread_required_evidence_paths
                )
                if unread_required_paths:
                    required_path = unread_required_paths[0]
                    required_class = self._source_broker.evidence_class_for_path(
                        request=request,
                        path=required_path,
                    )
                    gap_core = {
                        "proposal_digest": proposal.digest.value,
                        "evidence_class": required_class.value,
                        "required_evidence_path": required_path,
                    }
                    gap_digest = digest_of(
                        [
                            "ENGINEERING_QA_REQUIRED_EVIDENCE_PATH_GAP@1",
                            gap_core,
                        ]
                    )
                    ledger = ledger.append(
                        kind=LedgerEntryKind.GAP,
                        subject_id=_stable_id(
                            "investigation_gap", gap_core
                        ).value,
                        subject_digest=gap_digest,
                        references=(proposal.proposal_id.value,),
                        details={
                            "reason": "FINISH_REQUIRES_DECLARED_EVIDENCE_PATH",
                            "evidence_class": required_class.value,
                            "required_evidence_path": required_path,
                            "evidence_need": (
                                "Read the declared, authorized evidence path "
                                f"{required_path} before FINISH."
                            ),
                        },
                        maximum_bytes=request.limits.maximum_ledger_bytes,
                    )
                    continue
                non_supported = tuple(
                    item
                    for item in proposal.finish_dispositions
                    if item.outcome is not ChecklistOutcome.SUPPORTED
                )
                untried = investigation_input.untried_required_evidence_classes
                if non_supported and untried:
                    required_class = untried[0]
                    gap_core = {
                        "proposal_digest": proposal.digest.value,
                        "evidence_class": required_class.value,
                        "checklist_item_ids": tuple(
                            item.checklist_item_id for item in non_supported
                        ),
                    }
                    gap_digest = digest_of(
                        [
                            "ENGINEERING_QA_NON_SUPPORTED_FINISH_GAP@2",
                            gap_core,
                        ]
                    )
                    ledger = ledger.append(
                        kind=LedgerEntryKind.GAP,
                        subject_id=_stable_id(
                            "investigation_gap", gap_core
                        ).value,
                        subject_digest=gap_digest,
                        references=(proposal.proposal_id.value,),
                        details={
                            "reason": "NON_SUPPORTED_FINISH_REQUIRES_DECLARED_EVIDENCE_CLASS",
                            "evidence_class": required_class.value,
                            "evidence_need": (
                                "Investigate the registered "
                                f"{required_class.value} evidence class before "
                                "a non-supported FINISH."
                            ),
                        },
                        maximum_bytes=request.limits.maximum_ledger_bytes,
                    )
                    continue
                ledger = self._append_resource_receipt(
                    request=request, ledger=ledger, usage=usage
                )
                ledger = ledger.append(
                    kind=LedgerEntryKind.FINISH,
                    subject_id=proposal.proposal_id.value,
                    subject_digest=proposal.digest,
                    references=tuple(
                        item.digest.value for item in proposal.finish_dispositions
                    ),
                    details={"reason": proposal.unknown_to_reduce},
                    maximum_bytes=request.limits.maximum_ledger_bytes,
                ).seal(LedgerTerminalStatus.FINISHED)
                return _InvestigationRun(
                    ledger=ledger,
                    retrieval_results=tuple(results),
                    broker_decisions=tuple(decisions),
                    dispositions=proposal.finish_dispositions,
                    usage=usage,
                    terminal_reason="INVESTIGATION_FINISHED",
                )

            compilation = self._source_broker.compile(
                request=request,
                proposal=proposal,
                ledger=pre_proposal_ledger,
                locator_catalog=locator_catalog,
                usage=usage,
                required_path_locator_catalog=required_path_locator_catalog,
            )
            decision = compilation.decision
            decisions.append(decision)
            ledger = ledger.append(
                kind=LedgerEntryKind.BROKER_DECISION,
                subject_id=decision.decision_id.value,
                subject_digest=decision.digest,
                references=(proposal.proposal_id.value,),
                details={
                    "status": decision.status.value,
                    "reason": decision.reason_code,
                },
                maximum_bytes=request.limits.maximum_ledger_bytes,
            )
            if decision.status is BrokerDecisionStatus.REJECTED:
                usage = replace(
                    usage, no_progress_steps=usage.no_progress_steps + 1
                )
                if usage.no_progress_steps >= request.limits.maximum_no_progress_steps:
                    return self._fail_investigation(
                        request=request,
                        understanding=understanding,
                        ledger=ledger,
                        retrieval_results=tuple(results),
                        broker_decisions=tuple(decisions),
                        usage=usage,
                        reason="NO_PROGRESS_FUSE_EXHAUSTED",
                    )
                continue
            operation = compilation.operation
            if operation is None or decision.operation_id != operation.operation_id:
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "authorized Broker decision has no exact compiled operation",
                )
            ledger = ledger.append(
                kind=LedgerEntryKind.SOURCE_OPERATION,
                subject_id=operation.operation_id.value,
                subject_digest=operation.digest,
                references=(decision.decision_id.value,),
                details={
                    "operation": operation.operation.value,
                    "repository_revision": operation.repository_revision,
                    "source_profile_ref": operation.source_profile_ref,
                    "source_profile_digest": operation.source_profile_digest.value,
                    "evidence_class_allowlist_digest": digest_of(
                        [
                            "ENGINEERING_QA_EVIDENCE_CLASS_ALLOWLIST@1",
                            operation.evidence_class.value,
                            operation.evidence_class_allowlist,
                        ]
                    ).value,
                    "evidence_class": operation.evidence_class.value,
                    "result_modality": operation.result_modality,
                },
                maximum_bytes=request.limits.maximum_ledger_bytes,
            )
            try:
                result = self._retrieval_worker.execute(operation)
            except DomainError as exc:
                if exc.code is not ErrorCode.SOURCE_OPERATION_FAILED:
                    raise
                result = RetrievalResult.create(
                    operation=operation,
                    status=RetrievalStatus.OUTCOME_UNKNOWN,
                    items=(),
                    bytes_read=0,
                    files_read=0,
                    truncated=False,
                    coverage={
                        "worker_outcome": "unknown",
                        "error_code": exc.code.value,
                        "source_profile_ref": operation.source_profile_ref,
                        "source_profile_digest": operation.source_profile_digest.value,
                    },
                    failure_code="SOURCE_WORKER_OUTCOME_UNKNOWN",
                )
            self._validate_retrieval_result(request=request, operation=operation, result=result)
            investigated_evidence_classes.add(operation.evidence_class)
            results.append(result)
            for item in result.items:
                locator_catalog[item.locator_reference] = item
            ledger = ledger.append(
                kind=LedgerEntryKind.SOURCE_RESULT,
                subject_id=result.result_id.value,
                subject_digest=result.digest,
                references=(
                    operation.operation_id.value,
                    *(item.item_id.value for item in result.items),
                ),
                details={
                    "status": result.status.value,
                    "bytes": str(result.bytes_read),
                    "files": str(result.files_read),
                    "truncated": str(result.truncated).lower(),
                    "progress_digest": result.progress_digest.value,
                    "evidence_class": operation.evidence_class.value,
                    "result_modality": operation.result_modality,
                },
                maximum_bytes=request.limits.maximum_ledger_bytes,
            )
            usage = usage.with_retrieval(result, operation)
            if self._wall_time_exhausted(request=request, started_ns=started_ns):
                return self._fail_investigation(
                    request=request,
                    understanding=understanding,
                    ledger=ledger,
                    retrieval_results=tuple(results),
                    broker_decisions=tuple(decisions),
                    usage=usage,
                    reason="WALL_TIME_FUSE_EXHAUSTED",
                )
            if (
                usage.source_operations > request.limits.maximum_source_operations
                or usage.source_files > request.limits.maximum_source_files
                or usage.source_bytes > request.limits.maximum_source_bytes
            ):
                return self._fail_investigation(
                    request=request,
                    understanding=understanding,
                    ledger=ledger,
                    retrieval_results=tuple(results),
                    broker_decisions=tuple(decisions),
                    usage=usage,
                    reason="SOURCE_RESOURCE_FUSE_EXHAUSTED",
                )
            progress = (
                result.progress_digest not in progress_digests
                and result.status in {RetrievalStatus.COMPLETE, RetrievalStatus.PARTIAL}
                and bool(result.items or dict(result.coverage))
            )
            progress_digests.add(result.progress_digest)
            usage = replace(
                usage,
                no_progress_steps=0
                if progress
                else usage.no_progress_steps + 1,
            )
            if usage.no_progress_steps >= request.limits.maximum_no_progress_steps:
                return self._fail_investigation(
                    request=request,
                    understanding=understanding,
                    ledger=ledger,
                    retrieval_results=tuple(results),
                    broker_decisions=tuple(decisions),
                    usage=usage,
                    reason="NO_PROGRESS_FUSE_EXHAUSTED",
                )

    def _answer_and_review(
        self,
        *,
        request: EngineeringQuestionRequest,
        understanding: QuestionUnderstanding,
        package: QuestionEvidencePackage,
        usage: EngineeringQuestionResourceUsage,
        used_contexts: set[StableId],
        initial_rewrite_findings: tuple[EngineeringReviewFinding, ...],
        started_ns: int,
    ) -> _AnswerReviewRun:
        drafts: list[EngineeringAnswerDraft] = []
        reviews: list[EngineeringAnswerReview] = []
        rewrite_findings = initial_rewrite_findings
        rewrite_count = 0
        while True:
            if self._wall_time_exhausted(request=request, started_ns=started_ns):
                return _AnswerReviewRun(
                    usage,
                    tuple(drafts),
                    tuple(reviews),
                    None,
                    None,
                    "WALL_TIME_FUSE_EXHAUSTED",
                )
            if usage.answer_attempts >= request.limits.maximum_answer_attempts:
                return _AnswerReviewRun(
                    usage,
                    tuple(drafts),
                    tuple(reviews),
                    None,
                    None,
                    "ANSWER_ATTEMPT_FUSE_EXHAUSTED",
                )
            if usage.review_attempts >= request.limits.maximum_review_attempts:
                return _AnswerReviewRun(
                    usage,
                    tuple(drafts),
                    tuple(reviews),
                    None,
                    None,
                    "REVIEW_ATTEMPT_FUSE_EXHAUSTED",
                )
            if (
                usage.total_role_calls + 2
                > request.limits.maximum_total_model_role_calls
            ):
                return _AnswerReviewRun(
                    usage,
                    tuple(drafts),
                    tuple(reviews),
                    None,
                    None,
                    "INDEPENDENT_REVIEW_RESERVE_EXHAUSTED",
                )
            answer_context = self._fresh_context(
                request=request,
                role="answer",
                ordinal=usage.answer_attempts + 1,
                used_contexts=used_contexts,
            )
            proposal = self._answer_role.generate(
                original_question=request.original_question,
                understanding=understanding,
                package=package,
                role_context_id=answer_context,
                rewrite_findings=rewrite_findings,
            )
            usage = replace(
                usage,
                total_role_calls=usage.total_role_calls + 1,
                answer_attempts=usage.answer_attempts + 1,
            )
            draft = EngineeringAnswerDraft.accept(
                package=package,
                understanding=understanding,
                expected_role_context_id=answer_context,
                proposal=proposal,
                revision=usage.answer_attempts,
            )
            drafts.append(draft)
            if self._wall_time_exhausted(request=request, started_ns=started_ns):
                return _AnswerReviewRun(
                    usage,
                    tuple(drafts),
                    tuple(reviews),
                    None,
                    None,
                    "WALL_TIME_FUSE_EXHAUSTED",
                )
            review_context = self._fresh_context(
                request=request,
                role="review",
                ordinal=usage.review_attempts + 1,
                used_contexts=used_contexts,
            )
            review_proposal = self._reviewer_role.review(
                original_question=request.original_question,
                understanding=understanding,
                package=package,
                draft=draft,
                role_context_id=review_context,
            )
            usage = replace(
                usage,
                total_role_calls=usage.total_role_calls + 1,
                review_attempts=usage.review_attempts + 1,
            )
            review = EngineeringAnswerReview.accept(
                package=package,
                draft=draft,
                understanding=understanding,
                expected_role_context_id=review_context,
                proposal=review_proposal,
                attempt=usage.review_attempts,
            )
            reviews.append(review)
            if self._wall_time_exhausted(request=request, started_ns=started_ns):
                return _AnswerReviewRun(
                    usage,
                    tuple(drafts),
                    tuple(reviews),
                    None,
                    None,
                    "WALL_TIME_FUSE_EXHAUSTED",
                )
            if review.decision is EngineeringReviewDecision.APPROVED:
                authorized = AuthorizedEngineeringAnswer.authorize(
                    request=request,
                    package=package,
                    draft=draft,
                    review=review,
                )
                return _AnswerReviewRun(
                    usage,
                    tuple(drafts),
                    tuple(reviews),
                    authorized,
                    None,
                    "APPROVED",
                )
            if review.decision is EngineeringReviewDecision.REWRITE_REQUIRED:
                rewrite_count += 1
                if rewrite_count > request.limits.maximum_same_package_rewrites:
                    return _AnswerReviewRun(
                        usage,
                        tuple(drafts),
                        tuple(reviews),
                        None,
                        None,
                        "SAME_PACKAGE_REWRITE_FUSE_EXHAUSTED",
                    )
                rewrite_findings = review.findings
                continue
            if review.decision is EngineeringReviewDecision.MORE_EVIDENCE_REQUIRED:
                return _AnswerReviewRun(
                    usage,
                    tuple(drafts),
                    tuple(reviews),
                    None,
                    review.verification_request,
                    "MORE_EVIDENCE_REQUIRED",
                )
            return _AnswerReviewRun(
                usage,
                tuple(drafts),
                tuple(reviews),
                None,
                None,
                "REVIEW_REJECTED",
            )

    @staticmethod
    def _validate_investigation_proposal(
        *,
        request: EngineeringQuestionRequest,
        understanding: QuestionUnderstanding,
        ledger: EvidenceLedger,
        proposal: InvestigationStepProposal,
        expected_kind: InvestigationKind,
        expected_attempt_id: StableId,
        expected_role_context_id: StableId,
        expected_step_index: int,
        eligible_locator_references: tuple[StableId, ...],
        disposition_reference_eligibility: ChecklistDispositionReferenceEligibility,
    ) -> None:
        expected_reference_eligibility = ChecklistDispositionReferenceEligibility.create(
            support_references=disposition_reference_eligibility.support_references,
            boundary_references=disposition_reference_eligibility.boundary_references,
        )
        if expected_reference_eligibility != disposition_reference_eligibility:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "investigation disposition reference eligibility is invalid",
            )
        expected_dispositions = tuple(
            ChecklistDisposition.create(
                checklist_item_id=item.checklist_item_id,
                outcome=item.outcome,
                evidence_references=item.evidence_references,
                explanation=item.explanation,
                material_observations=item.material_observations,
            )
            for item in proposal.finish_dispositions
        )
        if expected_dispositions != proposal.finish_dispositions:
            raise DomainError(
                ErrorCode.PROVIDER_RESPONSE_INVALID,
                "investigation checklist disposition identity is invalid",
            )
        expected_proposal = InvestigationStepProposal.create(
            investigation_kind=proposal.investigation_kind,
            attempt_id=proposal.attempt_id,
            role_context_id=proposal.role_context_id,
            request_digest=proposal.request_digest,
            step_index=proposal.step_index,
            ledger_id=proposal.ledger_id,
            ledger_generation=proposal.ledger_generation,
            ledger_revision=proposal.ledger_revision,
            ledger_prefix_digest=proposal.ledger_prefix_digest,
            operation=proposal.operation,
            checklist_item_ids=proposal.checklist_item_ids,
            evidence_class=proposal.evidence_class,
            query=proposal.query,
            locator_reference=proposal.locator_reference,
            basis_entry_ids=proposal.basis_entry_ids,
            unknown_to_reduce=proposal.unknown_to_reduce,
            finish_dispositions=expected_dispositions,
        )
        if proposal != expected_proposal:
            raise DomainError(
                ErrorCode.PROVIDER_RESPONSE_INVALID,
                "investigation Proposal identity is invalid",
            )
        if (
            proposal.investigation_kind is not expected_kind
            or proposal.attempt_id != expected_attempt_id
            or proposal.role_context_id != expected_role_context_id
            or proposal.request_digest != request.digest
            or proposal.step_index != expected_step_index
            or proposal.ledger_id != ledger.ledger_id
            or proposal.ledger_generation != ledger.generation
            or proposal.ledger_revision != len(ledger.entries)
            or proposal.ledger_prefix_digest != ledger.prefix_digest
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "investigation proposal does not bind its exact fresh context and Ledger prefix",
            )
        checklist_ids = {item.item_id for item in understanding.checklist}
        if not set(proposal.checklist_item_ids).issubset(checklist_ids):
            raise DomainError(
                ErrorCode.PROVIDER_RESPONSE_INVALID,
                "investigation proposal references an unknown Question Checklist item",
            )
        ledger_entry_ids = {item.entry_id for item in ledger.entries}
        if not set(proposal.basis_entry_ids).issubset(ledger_entry_ids):
            raise DomainError(
                ErrorCode.PROVIDER_RESPONSE_INVALID,
                "investigation proposal references an entry outside the current Ledger prefix",
            )
        if ledger.entries[-1].entry_id not in proposal.basis_entry_ids:
            raise DomainError(
                ErrorCode.PROVIDER_RESPONSE_INVALID,
                "investigation proposal must explicitly consume the immediately prior Ledger result",
            )
        if (
            proposal.operation
            in {InvestigationOperation.READ, InvestigationOperation.PARSE}
            and proposal.locator_reference not in eligible_locator_references
        ):
            raise DomainError(
                ErrorCode.PROVIDER_RESPONSE_INVALID,
                "investigation proposal must use a currently eligible single-use locator reference",
            )
        if proposal.operation is InvestigationOperation.FINISH:
            disposition_ids = {
                item.checklist_item_id for item in proposal.finish_dispositions
            }
            if (
                disposition_ids != checklist_ids
                or len(proposal.finish_dispositions) != len(checklist_ids)
            ):
                raise DomainError(
                    ErrorCode.PROVIDER_RESPONSE_INVALID,
                    "FINISH must disposition every Checklist item exactly once",
                )
            support_references = set(
                disposition_reference_eligibility.support_references
            )
            boundary_references = set(
                disposition_reference_eligibility.boundary_references
            )
            for disposition in proposal.finish_dispositions:
                references = set(disposition.evidence_references)
                admissible = (
                    support_references
                    if disposition.outcome is ChecklistOutcome.SUPPORTED
                    else boundary_references
                )
                if not references.issubset(admissible):
                    category = (
                        "support/citation"
                        if disposition.outcome is ChecklistOutcome.SUPPORTED
                        else "boundary/audit"
                    )
                    raise DomainError(
                        ErrorCode.PROVIDER_RESPONSE_INVALID,
                        f"FINISH disposition requires an admissible {category} reference",
                    )

    @staticmethod
    def _validate_retrieval_result(
        *,
        request: EngineeringQuestionRequest,
        operation: CompiledSourceOperation,
        result: RetrievalResult,
    ) -> None:
        operation.validate_identity()
        expected_result = RetrievalResult.create(
            operation=operation,
            status=result.status,
            items=result.items,
            bytes_read=result.bytes_read,
            files_read=result.files_read,
            truncated=result.truncated,
            coverage=dict(result.coverage),
            failure_code=result.failure_code,
        )
        if result != expected_result:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Retrieval Worker Result identity is invalid",
            )
        if (
            result.operation_id != operation.operation_id
            or result.operation_digest != operation.digest
            or result.repository_revision != request.repository_revision
            or result.bytes_read > operation.maximum_source_bytes
            or result.files_read > operation.maximum_files
            or len(result.items) > operation.maximum_result_items
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Retrieval Worker Result violates the compiled operation authority",
            )
        if any(
            not _path_allowed(item.path, operation.source_allowlist)
            or not _path_allowed(
                item.path, operation.evidence_class_allowlist
            )
            or item.evidence_class is not operation.evidence_class
            or item.modality != operation.result_modality
            or (
                operation.operation
                in {SourceReadOperation.READ, SourceReadOperation.PARSE}
                and item.path != operation.path
            )
            for item in result.items
        ):
            raise DomainError(
                ErrorCode.SOURCE_TARGET_OUT_OF_SCOPE,
                "Retrieval Worker returned an item outside the compiled path, class, or modality profile",
            )
        if len({item.locator_reference for item in result.items}) != len(result.items):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Retrieval Worker returned duplicate locator references",
            )

    def _fail_investigation(
        self,
        *,
        request: EngineeringQuestionRequest,
        understanding: QuestionUnderstanding,
        ledger: EvidenceLedger,
        retrieval_results: tuple[RetrievalResult, ...],
        broker_decisions: tuple[SourceBrokerDecision, ...],
        usage: EngineeringQuestionResourceUsage,
        reason: str,
    ) -> _InvestigationRun:
        ledger = self._append_resource_receipt(
            request=request, ledger=ledger, usage=usage
        )
        stop_digest = digest_of(
            ["ENGINEERING_QA_FAIL_CLOSED_STOP@1", reason, ledger.prefix_digest.value]
        )
        ledger = ledger.append(
            kind=LedgerEntryKind.FAIL_CLOSED_STOP,
            subject_id=_stable_id("fail_closed_stop", stop_digest.value).value,
            subject_digest=stop_digest,
            references=(ledger.entries[-1].entry_id.value,),
            details={"reason": reason},
            maximum_bytes=request.limits.maximum_ledger_bytes,
        ).seal(LedgerTerminalStatus.FAILED_CLOSED)
        stop_reference = ledger.entries[-1].entry_id.value
        dispositions = tuple(
            ChecklistDisposition.create(
                checklist_item_id=item.item_id,
                outcome=ChecklistOutcome.FAILED,
                evidence_references=(stop_reference,),
                explanation=reason,
                material_observations=(
                    MaterialObservation.create(
                        checklist_item_id=item.item_id,
                        kind=MaterialObservationKind.LIMITATION,
                        statement=reason,
                        evidence_references=(stop_reference,),
                    ),
                ),
            )
            for item in understanding.checklist
        )
        return _InvestigationRun(
            ledger=ledger,
            retrieval_results=retrieval_results,
            broker_decisions=broker_decisions,
            dispositions=dispositions,
            usage=usage,
            terminal_reason=reason,
        )

    @staticmethod
    def _append_resource_receipt(
        *,
        request: EngineeringQuestionRequest,
        ledger: EvidenceLedger,
        usage: EngineeringQuestionResourceUsage,
    ) -> EvidenceLedger:
        details = {
            field: str(getattr(usage, field))
            for field in usage.__dataclass_fields__
        }
        receipt_digest = digest_of(
            [
                "ENGINEERING_QA_RESOURCE_RECEIPT@1",
                request.limits.digest.value,
                details,
            ]
        )
        return ledger.append(
            kind=LedgerEntryKind.RESOURCE_RECEIPT,
            subject_id=_stable_id("resource_receipt", receipt_digest.value).value,
            subject_digest=receipt_digest,
            references=(ledger.entries[-1].entry_id.value,),
            details=details,
            maximum_bytes=request.limits.maximum_ledger_bytes,
        )

    @staticmethod
    def _fresh_context(
        *,
        request: EngineeringQuestionRequest,
        role: str,
        ordinal: int,
        used_contexts: set[StableId],
    ) -> StableId:
        context = _stable_id(
            "role_context", [request.digest.value, role, ordinal]
        )
        if context in used_contexts:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "model role context was reused",
            )
        used_contexts.add(context)
        return context

    @staticmethod
    def _require_role_budget(
        *,
        request: EngineeringQuestionRequest,
        usage: EngineeringQuestionResourceUsage,
    ) -> None:
        if usage.total_role_calls >= request.limits.maximum_total_model_role_calls:
            raise DomainError(
                ErrorCode.BUDGET_EXHAUSTED,
                "Engineering QA model-role call fuse is exhausted",
            )

    def _elapsed_ms(self, started_ns: int) -> int:
        return max(0, (self._clock_ns() - started_ns) // 1_000_000)

    def _wall_time_exhausted(
        self,
        *,
        request: EngineeringQuestionRequest,
        started_ns: int,
    ) -> bool:
        return (
            self._elapsed_ms(started_ns)
            >= request.limits.maximum_wall_time_milliseconds
        )

    def _require_pre_ledger_wall_time_budget(
        self,
        *,
        request: EngineeringQuestionRequest,
        started_ns: int,
        stage: str,
    ) -> None:
        if self._wall_time_exhausted(request=request, started_ns=started_ns):
            raise DomainError(
                ErrorCode.BUDGET_EXHAUSTED,
                f"Engineering QA wall-time fuse was exhausted during {stage}",
            )

    def _result(
        self,
        *,
        status: EngineeringQuestionResultStatus,
        request: EngineeringQuestionRequest,
        understanding: QuestionUnderstanding,
        cognition: WorldModelCognitionContext,
        ledgers: Sequence[EvidenceLedger],
        packages: Sequence[QuestionEvidencePackage],
        results: Sequence[RetrievalResult],
        decisions: Sequence[SourceBrokerDecision],
        drafts: Sequence[EngineeringAnswerDraft],
        reviews: Sequence[EngineeringAnswerReview],
        authorized_answer: AuthorizedEngineeringAnswer | None,
        usage: EngineeringQuestionResourceUsage,
        terminal_reason: str,
        started_ns: int,
    ) -> EngineeringQuestionExecutionResult:
        return EngineeringQuestionExecutionResult.create(
            status=status,
            request=request,
            understanding=understanding,
            cognition=cognition,
            ledgers=ledgers,
            packages=packages,
            retrieval_results=results,
            broker_decisions=decisions,
            drafts=drafts,
            reviews=reviews,
            authorized_answer=authorized_answer,
            usage=usage,
            terminal_reason=terminal_reason,
            elapsed_milliseconds=self._elapsed_ms(started_ns),
        )


__all__ = [
    "ENGINEERING_QA_BROKER_POLICY",
    "ENGINEERING_QA_MODE",
    "ENGINEERING_QA_PACKAGE_SCHEMA",
    "ENGINEERING_QA_PROTOCOL",
    "ENGINEERING_QA_REQUIRED_PATH_LOCATOR_SCHEMA",
    "ENGINEERING_QA_VERIFICATION_REQUEST_SCHEMA",
    "AnswerContentRole",
    "AnswerDetailLevel",
    "AnswerClaimKind",
    "AuthorizedEngineeringAnswer",
    "BoundaryAuditEntry",
    "BrokerDecisionStatus",
    "ChecklistDisposition",
    "ChecklistOutcome",
    "CognitionDimension",
    "CognitionItem",
    "CompiledSourceOperation",
    "EngineeringAnswerClaimProposal",
    "EngineeringAnswerDraft",
    "EngineeringAnswerProposal",
    "EngineeringAnswerReviewerRole",
    "EngineeringAnswerReview",
    "EngineeringAnswerRole",
    "EngineeringEvidenceClass",
    "EngineeringQuestionAnsweringService",
    "EngineeringQuestionExecutionResult",
    "EngineeringQuestionRequest",
    "EngineeringQuestionResourceLimits",
    "EngineeringQuestionResourceUsage",
    "EngineeringQuestionResultStatus",
    "EngineeringReviewDecision",
    "EngineeringReviewChecklistAssessment",
    "EngineeringReviewFinding",
    "EngineeringReviewMaterialObservation",
    "EngineeringReviewProposal",
    "EngineeringReviewQualityAssessment",
    "EngineeringReviewQualityStatus",
    "EngineeringReviewRemediation",
    "EvidenceLedger",
    "EvidenceLedgerEntry",
    "InitialInvestigationInput",
    "InitialInvestigationRole",
    "InvestigationKind",
    "InvestigationOperation",
    "InvestigationStepProposal",
    "LedgerEntryKind",
    "LedgerTerminalStatus",
    "MaterialObservation",
    "MaterialObservationKind",
    "PackageBoundaryKind",
    "QuestionChecklistItem",
    "QuestionEvidencePackage",
    "QuestionUnderstanding",
    "QuestionUnderstandingProposal",
    "QuestionUnderstandingRole",
    "RequiredEvidencePathLocator",
    "RetrievalItem",
    "RetrievalResult",
    "RetrievalStatus",
    "RetrievalWorker",
    "RevisionAlignment",
    "SourceBroker",
    "SourceBrokerCompilation",
    "SourceBrokerDecision",
    "SourceProfilePolicy",
    "SourceReadOperation",
    "SupportCitationEntry",
    "VerificationInvestigationInput",
    "VerificationInvestigationRole",
    "VerificationRequestProposal",
    "WorldModelCognitionContext",
    "WorldModelCognitionProjector",
]
