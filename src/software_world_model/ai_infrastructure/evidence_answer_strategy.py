"""No-tools model roles for evidence-first synchronous answers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping
import unicodedata

from software_world_model.application_services import (
    AnswerSectionKind,
    EVIDENCE_ANSWER_CAPABILITY_CONTRACT_VERSION,
    EVIDENCE_ANSWER_CAPABILITY_ID,
    EVIDENCE_REVIEW_DIMENSIONS,
    EvidenceAnswerDraft,
    EvidenceAnswerReview,
    EvidenceAnswerSection,
    EvidencePacket,
    EvidenceReviewDecision,
    EvidenceReviewFinding,
    QuestionChecklist,
)
from software_world_model.cross_cutting import Digest, DomainError, ErrorCode, digest_of

from .agentic_knowledge_strategy import (
    AGENTIC_SOURCE_PLANNER_OUTPUT_SCHEMA,
    AGENTIC_SOURCE_PLANNER_PROMPT_REF,
    AGENTIC_SOURCE_PLANNER_SCHEMA_REF,
    AGENTIC_SOURCE_PLANNER_STRATEGY_REF,
    AgenticModelStrategyConfiguration,
    ModelGatewayPort,
    agentic_source_investigation_implementation_digest,
    _invoke_configuration_json_role,
)
from .openai_responses_adapter import OutputSchemaDefinition


EVIDENCE_CHECKLIST_SCHEMA_REF = "evidence-question-checklist@1"
EVIDENCE_CHECKLIST_PROMPT_REF = "evidence-question-checklist-prompt@1"
EVIDENCE_CHECKLIST_STRATEGY_REF = "model-evidence-question-checklist@1"
EVIDENCE_DRAFT_SCHEMA_REF = "evidence-answer-draft@1"
EVIDENCE_DRAFT_PROMPT_REF = "evidence-answer-draft-prompt@1"
EVIDENCE_DRAFT_STRATEGY_REF = "model-evidence-answer-generator@1"
EVIDENCE_REVIEW_SCHEMA_REF = "evidence-answer-review@1"
EVIDENCE_REVIEW_PROMPT_REF = "evidence-answer-review-prompt@1"
EVIDENCE_REVIEW_STRATEGY_REF = "model-independent-evidence-answer-reviewer@1"
EVIDENCE_FIRST_STRATEGY_ID = "evidence-first-software-answer"
EVIDENCE_FIRST_STRATEGY_VERSION = "1.0.0"
_MAX_DRAFT_CONTRACT_ATTEMPTS = 4
_MAX_REVIEW_CONTRACT_ATTEMPTS = 4


EVIDENCE_CHECKLIST_OUTPUT_SCHEMA = OutputSchemaDefinition(
    "evidence_question_checklist",
    {
        "type": "object",
        "properties": {
            "questions": {
                "type": "array",
                "minItems": 1,
                "maxItems": 12,
                "items": {"type": "string"},
            }
        },
        "required": ["questions"],
        "additionalProperties": False,
    },
)


_SECTION_SCHEMA = {
    "type": "object",
    "properties": {
        "section_id": {"type": "string"},
        "kind": {"type": "string", "enum": ["SUPPORTED", "UNKNOWN"]},
        "text": {"type": "string"},
        "checklist_item_ids": {
            "type": "array",
            "minItems": 1,
            "items": {"type": "string"},
        },
        "evidence_ids": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "section_id",
        "kind",
        "text",
        "checklist_item_ids",
        "evidence_ids",
    ],
    "additionalProperties": False,
}


EVIDENCE_DRAFT_OUTPUT_SCHEMA = OutputSchemaDefinition(
    "evidence_answer_draft",
    {
        "type": "object",
        "properties": {
            "sections": {
                "type": "array",
                "minItems": 1,
                "maxItems": 16,
                "items": _SECTION_SCHEMA,
            }
        },
        "required": ["sections"],
        "additionalProperties": False,
    },
)


_FINDING_SCHEMA = {
    "type": "object",
    "properties": {
        "checklist_item_id": {"type": "string"},
        "category": {
            "type": "string",
            "enum": [
                "MISSING_ANSWER",
                "UNSUPPORTED_CLAIM",
                "INCORRECT_CLAIM",
                "MISSING_CONDITION",
                "MISSING_RELATIONSHIP",
                "IRRELEVANT_CONTENT",
                "DUPLICATION",
                "UNCLEAR_ORGANIZATION",
                "RESPONSE_LANGUAGE_MISMATCH",
                "EVIDENCE_GAP",
            ],
        },
        "description": {"type": "string"},
        "evidence_ids": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "checklist_item_id",
        "category",
        "description",
        "evidence_ids",
    ],
    "additionalProperties": False,
}


EVIDENCE_REVIEW_OUTPUT_SCHEMA = OutputSchemaDefinition(
    "evidence_answer_review",
    {
        "type": "object",
        "properties": {
            "checks": {
                "type": "object",
                "properties": {
                    dimension: {"type": "boolean"}
                    for dimension in EVIDENCE_REVIEW_DIMENSIONS
                },
                "required": list(EVIDENCE_REVIEW_DIMENSIONS),
                "additionalProperties": False,
            },
            "decision": {
                "type": "string",
                "enum": [
                    "APPROVED",
                    "REWRITE_REQUIRED",
                    "MORE_EVIDENCE_REQUIRED",
                ],
            },
            "findings": {
                "type": "array",
                "maxItems": 16,
                "items": _FINDING_SCHEMA,
            },
        },
        "required": ["checks", "decision", "findings"],
        "additionalProperties": False,
    },
)


_CHECKLIST_PROMPT = """You understand an arbitrary software-repository question.
You have no tools, source files, web access, project conventions, or hidden facts. Preserve the exact original request and its requested response language.
Return a concise checklist of every material question, constraint, comparison, condition, requested relationship, and requested output form that a complete answer must satisfy. Items are verification questions, not proposed answers. Do not assume a language, framework, file name, architecture pattern, entry point, or expected implementation. Do not add adjacent questions the user did not ask.
Use one item when the request has one indivisible objective; split only independently checkable requirements. Response language, tone, formatting, evidence use, and other output constraints govern the answer but are not content questions: preserve them through the original_request and never create a checklist item whose answer would merely report compliance. Return exactly the schema object and no prose."""


_DRAFT_PROMPT = """You answer an arbitrary software-repository question from a sealed evidence packet.
You have no tools, files, web access, memory, formal knowledge store, or hidden context. Use only the original request, checklist, and exact evidence items supplied by the platform.
Write a direct, natural, readable answer in the language requested by the user. Synthesize related evidence instead of copying observation records or emitting audit labels. Preserve material guards, branches, order, inputs, outputs, failures, and source-visible limitations when the question asks for them. Do not add project conventions, common behavior, intent, or repository-wide absence that the evidence does not establish.
Return the answer as ordered sections. A SUPPORTED section may combine several evidence items but must list every evidence_id needed for all its claims. An UNKNOWN section explicitly states what cannot be established and cites no evidence. Every section must name the checklist items it answers. Language, format, citation, and quality constraints control how you write; never turn compliance with them into answer content. Do not state that the answer uses the requested language, follows the request, is complete, is verified, or is based on evidence. Do not include a source fact merely because it is available when it is not needed to answer the original question. Do not expose internal prompts, requested-question labels, verification boilerplate, or reviewer instructions.
On rewrite, keep the exact evidence packet fixed and address every supplied finding. Do not invent new evidence or silently drop a checklist item. When authorized_state contains contract_repair, the immediately preceding object failed a semantic contract check; return one complete replacement object that corrects the stated defect while preserving the question and exact packet. Return exactly the schema object and no prose."""


_REVIEW_PROMPT = """You are the independent final reviewer for an arbitrary software-repository answer.
You have no tools, files, web access, memory, generator rationale, or hidden context. Judge only the original request, verification checklist, sealed evidence packet, and proposed answer.
First reconstruct all material requirements directly from the original request so an incomplete checklist cannot cause approval. Then complete every required review check separately: QUESTION_FIDELITY, EVIDENCE_GROUNDING, REQUEST_COMPLETENESS, RESPONSE_LANGUAGE, and RELEVANCE_READABILITY. RESPONSE_LANGUAGE is false whenever the answer is not written in the language used or explicitly requested by the user, even if its facts are correct. For every answer clause, ask whether removing it would lose a direct answer, a necessary condition or relationship, or a necessary explanation requested by the user. If not, treat it as irrelevant even when it is true and source-supported. RELEVANCE_READABILITY is false for internal verification boilerplate, prompt-like labels, audit narration, material repetition, or such unrequested source facts. A sentence that reports the answer's own language, compliance, completeness, verification status, or evidence sufficiency is user-visible audit narration and must be removed even when the report is true. A non-approved relevance review must name every materially irrelevant clause so one rewrite can remove all of them.
Verify every answer claim against its cited evidence, every requested condition and relationship, all material branches and ordering, explicit unknowns where support is absent, and natural organization. Audit each temporal word and sequence claim against literal control flow: before, after, during, finally, then, and on second execution are not interchangeable. Distinguish observable mechanism from design intent: execution order or a structural change alone does not prove a purpose, motivation, prevention claim, or causal "why". When source shows only the mechanism, require the answer to state that mechanism and leave undocumented intent unknown instead of inventing it. Do not let correctness on one check compensate for failure on another.
APPROVED requires every check to be true and an empty findings list. Any false check requires a non-approved decision and a specific finding. Use REWRITE_REQUIRED only when the existing packet already contains the evidence needed to fix every finding, including translation or removal of boilerplate; each such finding must cite the exact relevant evidence_ids. Use MORE_EVIDENCE_REQUIRED when at least one material question cannot be decided from the packet; describe the exact missing evidence and do not pretend rewriting can repair it. Findings must be specific enough to drive one targeted repair and must not propose facts unsupported by the packet.
When authorized_state contains contract_repair, the immediately preceding review object failed a semantic or structured contract check. Return one complete replacement review that corrects the stated defect without changing the question, packet, or draft. The platform, not you, enforces source authorization and packet identity. Return exactly the schema object and no prose."""


class ModelQuestionChecklistPlanner:
    def __init__(
        self,
        gateway: ModelGatewayPort,
        configuration: AgenticModelStrategyConfiguration,
    ) -> None:
        self._gateway = gateway
        self._configuration = configuration

    def plan(self, *, original_request: str, execution_ref: str) -> QuestionChecklist:
        value = _invoke_configuration_json_role(
            gateway=self._gateway,
            configuration=self._configuration,
            execution_ref=execution_ref,
            stage="EVIDENCE_QUESTION_CHECKLIST",
            capability_id="evidence-answer.question-understanding",
            strategy_ref=EVIDENCE_CHECKLIST_STRATEGY_REF,
            prompt_ref=EVIDENCE_CHECKLIST_PROMPT_REF,
            prompt=_CHECKLIST_PROMPT,
            schema_ref=EVIDENCE_CHECKLIST_SCHEMA_REF,
            state={"original_request": original_request},
        )
        if set(value) != {"questions"} or not isinstance(value["questions"], list):
            _invalid("question checklist output does not match the closed contract")
        questions = tuple(value["questions"])
        if any(not isinstance(item, str) for item in questions):
            _invalid("question checklist contains a non-text item")
        return QuestionChecklist.create(
            original_request=original_request,
            questions=questions,
        )


class ModelEvidenceAnswerGenerator:
    def __init__(
        self,
        gateway: ModelGatewayPort,
        configuration: AgenticModelStrategyConfiguration,
    ) -> None:
        self._gateway = gateway
        self._configuration = configuration

    def generate(
        self,
        *,
        checklist: QuestionChecklist,
        packet: EvidencePacket,
        revision: int,
        prior_draft: EvidenceAnswerDraft | None,
        review_findings: tuple[EvidenceReviewFinding, ...],
        execution_ref: str,
    ) -> EvidenceAnswerDraft:
        base_state = {
                "question": checklist.model_view(),
                "evidence_packet": packet.model_view(),
                "revision": revision,
                "prior_draft": prior_draft.model_view() if prior_draft else None,
                "review_findings": [item.model_view() for item in review_findings],
                "required_packet_digest": packet.digest.value,
        }
        last_error: DomainError | None = None
        for attempt in range(1, _MAX_DRAFT_CONTRACT_ATTEMPTS + 1):
            state = dict(base_state)
            if last_error is not None:
                state["contract_repair"] = {
                    "rejected_output_reason": last_error.message,
                    "termination_reason": last_error.details.get(
                        "invalid_output_termination_reason"
                    ),
                    "required_action": (
                        "Return one complete replacement draft. Use only exact "
                        "checklist and evidence IDs from the supplied packet; a "
                        "SUPPORTED section must cite evidence and an UNKNOWN "
                        "section must cite none. Keep the prose compact enough to "
                        "finish the complete JSON object without omitting any "
                        "material checklist item."
                    ),
                }
            try:
                value = _invoke_configuration_json_role(
                    gateway=self._gateway,
                    configuration=self._configuration,
                    execution_ref=(
                        execution_ref
                        if attempt == 1
                        else f"{execution_ref}:contract-retry:{attempt}"
                    ),
                    stage="EVIDENCE_ANSWER_GENERATION",
                    capability_id="evidence-answer.generate",
                    strategy_ref=EVIDENCE_DRAFT_STRATEGY_REF,
                    prompt_ref=EVIDENCE_DRAFT_PROMPT_REF,
                    prompt=_DRAFT_PROMPT,
                    schema_ref=EVIDENCE_DRAFT_SCHEMA_REF,
                    state=state,
                    max_structured_output_attempts=1,
                )
                sections = _sections(value)
                return EvidenceAnswerDraft.create(
                    revision=revision,
                    checklist=checklist,
                    packet=packet,
                    sections=sections,
                )
            except DomainError as exc:
                if exc.code not in {
                    ErrorCode.STRUCTURED_OUTPUT_INVALID,
                    ErrorCode.INVALID_ARGUMENT,
                }:
                    raise
                last_error = exc
        assert last_error is not None
        raise DomainError(
            ErrorCode.STRUCTURED_OUTPUT_INVALID,
            "evidence answer draft exhausted bounded contract retries",
            {
                "attempt_count": _MAX_DRAFT_CONTRACT_ATTEMPTS,
                "last_error": last_error.message,
            },
        ) from last_error


class ModelIndependentEvidenceAnswerReviewer:
    def __init__(
        self,
        gateway: ModelGatewayPort,
        configuration: AgenticModelStrategyConfiguration,
    ) -> None:
        self._gateway = gateway
        self._configuration = configuration

    def review(
        self,
        *,
        checklist: QuestionChecklist,
        packet: EvidencePacket,
        draft: EvidenceAnswerDraft,
        execution_ref: str,
    ) -> EvidenceAnswerReview:
        base_state = {
            "question": checklist.model_view(),
            "evidence_packet": packet.model_view(),
            "answer_draft": draft.model_view(),
            "required_packet_digest": packet.digest.value,
            "required_draft_digest": draft.digest.value,
        }
        last_error: DomainError | None = None
        for attempt in range(1, _MAX_REVIEW_CONTRACT_ATTEMPTS + 1):
            state = dict(base_state)
            if last_error is not None:
                state["contract_repair"] = {
                    "rejected_output_reason": last_error.message,
                    "termination_reason": last_error.details.get(
                        "invalid_output_termination_reason"
                    ),
                    "required_action": (
                        "Return one complete replacement review with all five "
                        "checks. APPROVED has no findings; every rejection has a "
                        "specific finding. Every REWRITE_REQUIRED finding must "
                        "cite exact existing packet evidence that supports the "
                        "repair, and every ID must be copied exactly."
                    ),
                }
            try:
                value = _invoke_configuration_json_role(
                    gateway=self._gateway,
                    configuration=self._configuration,
                    execution_ref=(
                        execution_ref
                        if attempt == 1
                        else f"{execution_ref}:contract-retry:{attempt}"
                    ),
                    stage="EVIDENCE_ANSWER_INDEPENDENT_REVIEW",
                    capability_id="evidence-answer.review",
                    strategy_ref=EVIDENCE_REVIEW_STRATEGY_REF,
                    prompt_ref=EVIDENCE_REVIEW_PROMPT_REF,
                    prompt=_REVIEW_PROMPT,
                    schema_ref=EVIDENCE_REVIEW_SCHEMA_REF,
                    state=state,
                    max_structured_output_attempts=1,
                )
                review = _review_from_model_value(
                    value=value,
                    checklist=checklist,
                    packet=packet,
                    draft=draft,
                )
                return _enforce_response_language_guard(
                    review=review,
                    checklist=checklist,
                    packet=packet,
                    draft=draft,
                )
            except DomainError as exc:
                if exc.code not in {
                    ErrorCode.STRUCTURED_OUTPUT_INVALID,
                    ErrorCode.INVALID_ARGUMENT,
                }:
                    raise
                last_error = exc
        assert last_error is not None
        raise DomainError(
            ErrorCode.STRUCTURED_OUTPUT_INVALID,
            "evidence answer review exhausted bounded contract retries",
            {
                "attempt_count": _MAX_REVIEW_CONTRACT_ATTEMPTS,
                "last_error": last_error.message,
            },
        ) from last_error


@dataclass(frozen=True, slots=True)
class EvidenceAnswerStrategyBundle:
    implementation_digest: Digest
    checklist_planner: ModelQuestionChecklistPlanner
    answer_generator: ModelEvidenceAnswerGenerator
    answer_reviewer: ModelIndependentEvidenceAnswerReviewer

    @classmethod
    def create(
        cls,
        gateway: ModelGatewayPort,
        configuration: AgenticModelStrategyConfiguration,
    ) -> "EvidenceAnswerStrategyBundle":
        return cls(
            implementation_digest=evidence_answer_strategy_implementation_digest(),
            checklist_planner=ModelQuestionChecklistPlanner(gateway, configuration),
            answer_generator=ModelEvidenceAnswerGenerator(gateway, configuration),
            answer_reviewer=ModelIndependentEvidenceAnswerReviewer(
                gateway, configuration
            ),
        )


def evidence_answer_output_schemas() -> dict[str, OutputSchemaDefinition]:
    return {
        EVIDENCE_CHECKLIST_SCHEMA_REF: EVIDENCE_CHECKLIST_OUTPUT_SCHEMA,
        EVIDENCE_DRAFT_SCHEMA_REF: EVIDENCE_DRAFT_OUTPUT_SCHEMA,
        EVIDENCE_REVIEW_SCHEMA_REF: EVIDENCE_REVIEW_OUTPUT_SCHEMA,
    }


def evidence_first_task_output_schemas() -> dict[str, OutputSchemaDefinition]:
    return {
        AGENTIC_SOURCE_PLANNER_SCHEMA_REF: AGENTIC_SOURCE_PLANNER_OUTPUT_SCHEMA,
        **evidence_answer_output_schemas(),
    }


def evidence_answer_strategy_implementation_digest() -> Digest:
    return digest_of(
        {
            "strategy": "evidence-first-synchronous-answer@1",
            "roles": {
                EVIDENCE_CHECKLIST_STRATEGY_REF: {
                    "prompt_ref": EVIDENCE_CHECKLIST_PROMPT_REF,
                    "prompt": _CHECKLIST_PROMPT,
                    "schema": EVIDENCE_CHECKLIST_OUTPUT_SCHEMA.schema,
                },
                EVIDENCE_DRAFT_STRATEGY_REF: {
                    "prompt_ref": EVIDENCE_DRAFT_PROMPT_REF,
                    "prompt": _DRAFT_PROMPT,
                    "schema": EVIDENCE_DRAFT_OUTPUT_SCHEMA.schema,
                },
                EVIDENCE_REVIEW_STRATEGY_REF: {
                    "prompt_ref": EVIDENCE_REVIEW_PROMPT_REF,
                    "prompt": _REVIEW_PROMPT,
                    "schema": EVIDENCE_REVIEW_OUTPUT_SCHEMA.schema,
                },
            },
            "rewrite_policy": "FIXED_EVIDENCE_PACKET_EXACT_FINDINGS@1",
            "draft_contract_repair": "BOUNDED_COMPLETE_REPLACEMENT@2",
            "review_contract_repair": "BOUNDED_COMPLETE_REPLACEMENT@1",
            "review_policy": "ORIGINAL_QUESTION_INDEPENDENT_FAIL_CLOSED@1",
            "knowledge_materialization": "OUTSIDE_SYNCHRONOUS_PATH@1",
        }
    )


def evidence_first_task_strategy_implementation_digest() -> Digest:
    return digest_of(
        {
            "capability_id": EVIDENCE_ANSWER_CAPABILITY_ID,
            "capability_contract_version": (
                EVIDENCE_ANSWER_CAPABILITY_CONTRACT_VERSION
            ),
            "strategy_id": EVIDENCE_FIRST_STRATEGY_ID,
            "strategy_version": EVIDENCE_FIRST_STRATEGY_VERSION,
            "source_investigation": (
                agentic_source_investigation_implementation_digest().value
            ),
            "evidence_answer_roles": (
                evidence_answer_strategy_implementation_digest().value
            ),
            "orchestration": {
                "path": (
                    "QUESTION_CHECKLIST_SOURCE_EVIDENCE_DRAFT_REVIEW_"
                    "TARGETED_REWRITE@1"
                ),
                "rewrite": "SAME_PACKET_DIGEST_REQUIRED@1",
                "retrieval": "REVIEW_FINDING_CREATES_NEW_PACKET@1",
                "source_budget": "ONE_OVERALL_ACTION_FUSE_ACROSS_RETRIEVAL_ROUNDS@1",
                "failure": "INDEPENDENT_REVIEW_FAIL_CLOSED@1",
                "knowledge": "MATERIALIZATION_OUTSIDE_SYNC_PATH@1",
            },
        }
    )


def evidence_first_task_prompt_program_digest() -> Digest:
    return digest_of(
        (
            (
                AGENTIC_SOURCE_PLANNER_PROMPT_REF,
                AGENTIC_SOURCE_PLANNER_STRATEGY_REF,
                agentic_source_investigation_implementation_digest().value,
            ),
            (EVIDENCE_CHECKLIST_PROMPT_REF, _CHECKLIST_PROMPT),
            (EVIDENCE_DRAFT_PROMPT_REF, _DRAFT_PROMPT),
            (EVIDENCE_REVIEW_PROMPT_REF, _REVIEW_PROMPT),
        )
    )


def evidence_first_task_output_contract_digest() -> Digest:
    schemas = evidence_first_task_output_schemas()
    return digest_of(
        tuple(
            (schema_ref, schemas[schema_ref].schema)
            for schema_ref in sorted(schemas)
        )
    )


def _sections(value: Mapping[str, object]) -> tuple[EvidenceAnswerSection, ...]:
    if set(value) != {"sections"} or not isinstance(value["sections"], list):
        _invalid("evidence answer draft does not match the closed contract")
    sections: list[EvidenceAnswerSection] = []
    for raw in value["sections"]:
        if not isinstance(raw, Mapping) or set(raw) != {
            "section_id",
            "kind",
            "text",
            "checklist_item_ids",
            "evidence_ids",
        }:
            _invalid("evidence answer section is invalid")
        checklist_ids = raw["checklist_item_ids"]
        evidence_ids = raw["evidence_ids"]
        if (
            not isinstance(checklist_ids, list)
            or not isinstance(evidence_ids, list)
            or any(not isinstance(item, str) for item in checklist_ids)
            or any(not isinstance(item, str) for item in evidence_ids)
        ):
            _invalid("evidence answer section references are invalid")
        try:
            kind = AnswerSectionKind(raw["kind"])
        except (TypeError, ValueError) as exc:
            raise DomainError(
                ErrorCode.STRUCTURED_OUTPUT_INVALID,
                "evidence answer section kind is invalid",
            ) from exc
        sections.append(
            EvidenceAnswerSection.create(
                section_id=raw["section_id"],
                kind=kind,
                text=raw["text"],
                checklist_item_ids=tuple(checklist_ids),
                evidence_ids=tuple(evidence_ids),
            )
        )
    return tuple(sections)


def _review_from_model_value(
    *,
    value: Mapping[str, object],
    checklist: QuestionChecklist,
    packet: EvidencePacket,
    draft: EvidenceAnswerDraft,
) -> EvidenceAnswerReview:
    if set(value) != {"checks", "decision", "findings"}:
        _invalid("evidence answer review does not match the closed contract")
    raw_checks = value["checks"]
    if (
        not isinstance(raw_checks, Mapping)
        or set(raw_checks) != set(EVIDENCE_REVIEW_DIMENSIONS)
        or any(
            not isinstance(raw_checks[item], bool)
            for item in EVIDENCE_REVIEW_DIMENSIONS
        )
    ):
        _invalid("evidence answer review checks are invalid")
    checks = tuple(
        (dimension, raw_checks[dimension])
        for dimension in EVIDENCE_REVIEW_DIMENSIONS
    )
    try:
        decision = EvidenceReviewDecision(value["decision"])
    except (TypeError, ValueError) as exc:
        raise DomainError(
            ErrorCode.STRUCTURED_OUTPUT_INVALID,
            "evidence answer review decision is invalid",
        ) from exc
    raw_findings = value["findings"]
    if not isinstance(raw_findings, list):
        _invalid("evidence answer review findings are invalid")
    findings: list[EvidenceReviewFinding] = []
    for raw in raw_findings:
        if not isinstance(raw, Mapping) or set(raw) != {
            "checklist_item_id",
            "category",
            "description",
            "evidence_ids",
        }:
            _invalid("evidence answer review finding is invalid")
        evidence_ids = raw["evidence_ids"]
        if not isinstance(evidence_ids, list) or any(
            not isinstance(item, str) for item in evidence_ids
        ):
            _invalid("evidence answer review citations are invalid")
        findings.append(
            EvidenceReviewFinding.create(
                checklist_item_id=raw["checklist_item_id"],
                category=raw["category"],
                description=raw["description"],
                evidence_ids=tuple(evidence_ids),
            )
        )
    normalized_findings = tuple(findings)
    checks = _checks_consistent_with_findings(checks, normalized_findings)
    return EvidenceAnswerReview.create(
        decision=decision,
        checks=checks,
        checklist=checklist,
        packet=packet,
        draft=draft,
        findings=normalized_findings,
    )


def _enforce_response_language_guard(
    *,
    review: EvidenceAnswerReview,
    checklist: QuestionChecklist,
    packet: EvidencePacket,
    draft: EvidenceAnswerDraft,
) -> EvidenceAnswerReview:
    """Reject obvious cross-writing-system mismatches the model reviewer missed.

    This universal guard does not guess a repository, language, or question type.
    It only acts when both texts have a clear but different Unicode writing
    system. Same-script language distinctions remain the independent model
    reviewer's responsibility.
    """

    if not _different_dominant_writing_system(
        checklist.original_request, draft.body
    ):
        return review
    checks = dict(review.checks)
    checks["RESPONSE_LANGUAGE"] = False
    if any(
        item.category == "RESPONSE_LANGUAGE_MISMATCH"
        for item in review.findings
    ):
        findings = review.findings
    else:
        cited = tuple(
            dict.fromkeys(
                evidence_id
                for section in draft.sections
                for evidence_id in section.evidence_ids
            )
        )
        if not cited:
            cited = (packet.items[0].evidence_id,)
        findings = review.findings + (
            EvidenceReviewFinding.create(
                checklist_item_id=checklist.items[0].item_id,
                category="RESPONSE_LANGUAGE_MISMATCH",
                description=(
                    "Rewrite the answer in the same language as the original "
                    "request; the draft uses a different writing system."
                ),
                evidence_ids=cited,
            ),
        )
    decision = (
        EvidenceReviewDecision.REWRITE_REQUIRED
        if review.decision is EvidenceReviewDecision.APPROVED
        else review.decision
    )
    return EvidenceAnswerReview.create(
        decision=decision,
        checks=tuple((item, checks[item]) for item in EVIDENCE_REVIEW_DIMENSIONS),
        checklist=checklist,
        packet=packet,
        draft=draft,
        findings=findings,
    )


def _different_dominant_writing_system(request: str, answer: str) -> bool:
    requested, request_counts = _dominant_writing_system(request)
    actual, answer_counts = _dominant_writing_system(answer)
    if requested is None or actual is None or requested == actual:
        return False
    requested_in_answer = answer_counts.get(requested, 0)
    answer_letters = sum(answer_counts.values())
    return (
        answer_counts.get(actual, 0) >= 4
        and requested_in_answer * 10 < max(answer_letters, 1)
        and request_counts.get(requested, 0) >= 4
    )


def _checks_consistent_with_findings(
    checks: tuple[tuple[str, bool], ...],
    findings: tuple[EvidenceReviewFinding, ...],
) -> tuple[tuple[str, bool], ...]:
    values = dict(checks)
    for finding in findings:
        if finding.category in {
            "UNSUPPORTED_CLAIM",
            "INCORRECT_CLAIM",
            "MISSING_RELATIONSHIP",
        }:
            values["EVIDENCE_GROUNDING"] = False
        if finding.category in {
            "MISSING_ANSWER",
            "MISSING_CONDITION",
            "MISSING_RELATIONSHIP",
            "EVIDENCE_GAP",
        }:
            values["REQUEST_COMPLETENESS"] = False
        if finding.category == "RESPONSE_LANGUAGE_MISMATCH":
            values["RESPONSE_LANGUAGE"] = False
        if finding.category in {
            "IRRELEVANT_CONTENT",
            "DUPLICATION",
            "UNCLEAR_ORGANIZATION",
        }:
            values["RELEVANCE_READABILITY"] = False
    return tuple((item, values[item]) for item in EVIDENCE_REVIEW_DIMENSIONS)


def _dominant_writing_system(text: str):
    counts: dict[str, int] = {}
    for character in text:
        if not character.isalpha():
            continue
        name = unicodedata.name(character, "")
        if any(
            token in name
            for token in ("CJK", "HIRAGANA", "KATAKANA", "HANGUL", "BOPOMOFO")
        ):
            script = "CJK"
        else:
            script = next(
                (
                    token
                    for token in (
                        "LATIN",
                        "CYRILLIC",
                        "ARABIC",
                        "HEBREW",
                        "DEVANAGARI",
                        "THAI",
                        "GREEK",
                        "ARMENIAN",
                        "GEORGIAN",
                    )
                    if token in name
                ),
                "OTHER",
            )
        counts[script] = counts.get(script, 0) + 1
    if not counts:
        return None, counts
    script, count = max(counts.items(), key=lambda item: item[1])
    if count < 4 or count * 4 < sum(counts.values()):
        return None, counts
    return script, counts


def _invalid(message: str) -> None:
    raise DomainError(ErrorCode.STRUCTURED_OUTPUT_INVALID, message)
