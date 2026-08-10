"""Run evidence-first production model roles against sealed fixtures."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping

from software_world_model.ai_infrastructure import (
    AgenticEvaluationOutput,
    AgenticModelStrategyConfiguration,
    EvidenceAnswerStrategyBundle,
    EvidenceEvaluationRole,
    ModelSourceInvestigationPlanner,
    evidence_first_task_strategy_implementation_digest,
)
from software_world_model.application_services import (
    AnswerSectionKind,
    BuildObjective,
    CanonicalBuildTarget,
    CoverageObligation,
    EvidenceAnswerDraft,
    EvidenceAnswerSection,
    EvidenceItem,
    EvidencePacket,
    EvidenceReviewFinding,
    KnowledgeUpdateRequest,
    QuestionChecklist,
)
from software_world_model.cross_cutting import (
    CorrelationRef,
    Digest,
    DomainError,
    ErrorCode,
    IdempotencyKey,
    Revision,
    StableId,
    digest_of,
)
from software_world_model.infrastructure import SqliteDatabase
from software_world_model.source_integration import TargetKind
from validation.agentic_capability_iteration_001.live_runner import (
    CAPABILITY_OUTPUT_DOCUMENT_SCHEMA,
    _evaluation_output_document,
    _usage,
    load_capability_output_document,
    save_capability_output_document,
)

from .manifest import case_entry, verify_capability_suite


class LiveCapabilityCaseRunner:
    def __init__(
        self,
        *,
        database: SqliteDatabase,
        gateway: object,
        configuration: AgenticModelStrategyConfiguration,
        expected_model_fingerprint: str,
    ) -> None:
        self._database = database
        self._roles = EvidenceAnswerStrategyBundle.create(gateway, configuration)
        self._source = ModelSourceInvestigationPlanner(gateway, configuration)
        self._expected_model_fingerprint = expected_model_fingerprint

    def execute(self, *, suite, role: EvidenceEvaluationRole):
        verify_capability_suite(suite)
        case = case_entry(suite, role)
        frozen_case_id = f"{role.value.lower()}:{case['case_id']}"
        output = self._execute_role(role, case["fixture"], frozen_case_id)
        usage = _usage(self._database)
        if usage["actual_model_fingerprint"] != self._expected_model_fingerprint:
            raise DomainError(
                ErrorCode.QUALIFICATION_INVALID,
                "evidence capability case used an unexpected actual model",
            )
        fixture_digest = digest_of(case["fixture"])
        output_digest = digest_of(output)
        sink = {
            "suite_digest": suite["suite_digest"],
            "case_id": frozen_case_id,
            "role": role.value,
            "fixture_digest": fixture_digest.value,
            "output_digest": output_digest.value,
            "strategy_implementation_digest": (
                evidence_first_task_strategy_implementation_digest().value
            ),
            "provider_request_ids": usage["provider_request_ids"],
            "authorized_manifests_digest": digest_of(
                usage["authorized_manifests"]
            ).value,
            "isolation_receipts_digest": digest_of(
                usage["isolation_receipts"]
            ).value,
            "model_call_outcomes_digest": digest_of(
                usage["model_call_outcomes"]
            ).value,
        }
        evaluation_output = AgenticEvaluationOutput.create(
            case_id=frozen_case_id,
            fixture_digest=fixture_digest,
            output_ref=f"evidence-capability-output:{frozen_case_id}:{output_digest.value}",
            output_digest=output_digest,
            sink_manifest_ref=f"evidence-capability-sink:{frozen_case_id}",
            sink_manifest_digest=digest_of(sink),
            generator_origin="volcengine-ark-evidence-answer-role-output",
            actual_model_fingerprint=usage["actual_model_fingerprint"],
            provider_request_ids=usage["provider_request_ids"],
            input_tokens=usage["input_tokens"],
            output_tokens=usage["output_tokens"],
            usage_complete=True,
        )
        core = {
            "schema": CAPABILITY_OUTPUT_DOCUMENT_SCHEMA,
            "suite_id": suite["suite_id"],
            "suite_version": suite["suite_version"],
            "suite_digest": suite["suite_digest"],
            "case_id": frozen_case_id,
            "role": role.value,
            "fixture": case["fixture"],
            "fixture_digest": fixture_digest.value,
            "oracle_ref": f"{suite['suite_id']}:oracle:{role.value}:{case['case_id']}",
            "oracle_digest": digest_of(case["oracle"]).value,
            "domain_output": output,
            "authorized_manifests": usage["authorized_manifests"],
            "isolation_receipts": usage["isolation_receipts"],
            "model_call_outcomes": usage["model_call_outcomes"],
            "sink_manifest": sink,
            "evaluation_output": _evaluation_output_document(evaluation_output),
        }
        return evaluation_output, {**core, "document_digest": digest_of(core).value}

    def _execute_role(self, role, fixture, case_id):
        if role is EvidenceEvaluationRole.QUESTION_FIDELITY:
            checklist = self._roles.checklist_planner.plan(
                original_request=fixture["original_request"],
                execution_ref=f"evidence-capability:{case_id}:question",
            )
            return checklist.model_view()
        if role is EvidenceEvaluationRole.SOURCE_INVESTIGATION:
            request = _source_request(fixture, case_id)
            proposal = self._source.propose(
                request=request, completed_operations=(), ordinal=1
            )
            return {
                "stop": proposal.stop,
                "tool": proposal.tool.value if proposal.tool else None,
                "parameters": dict(proposal.parameters),
                "rationale": proposal.rationale,
            }
        checklist, packet = _question_and_packet(fixture)
        if role is EvidenceEvaluationRole.CITED_ANSWER_GENERATION:
            draft = self._roles.answer_generator.generate(
                checklist=checklist,
                packet=packet,
                revision=1,
                prior_draft=None,
                review_findings=(),
                execution_ref=f"evidence-capability:{case_id}:draft",
            )
            return draft.model_view()
        prior = _draft(fixture, checklist, packet)
        if role is EvidenceEvaluationRole.FIXED_PACKET_REWRITE:
            raw = fixture["finding"]
            finding = EvidenceReviewFinding.create(
                checklist_item_id=raw["checklist_item_id"],
                category=raw["category"],
                description=raw["description"],
                evidence_ids=tuple(raw["evidence_ids"]),
            )
            rewritten = self._roles.answer_generator.generate(
                checklist=checklist,
                packet=packet,
                revision=2,
                prior_draft=prior,
                review_findings=(finding,),
                execution_ref=f"evidence-capability:{case_id}:rewrite",
            )
            return {
                **rewritten.model_view(),
                "prior_draft_digest": prior.digest.value,
                "evidence_packet_digest": packet.digest.value,
            }
        review = self._roles.answer_reviewer.review(
            checklist=checklist,
            packet=packet,
            draft=prior,
            execution_ref=f"evidence-capability:{case_id}:review",
        )
        return {
            "decision": review.decision.value,
            "checks": dict(review.checks),
            "findings": [item.model_view() for item in review.findings],
            "evidence_packet_digest": review.evidence_packet_digest.value,
            "draft_digest": review.draft_digest.value,
        }


def verify_capability_output_against_suite(output, document, suite) -> None:
    verify_capability_suite(suite)
    expected = next(
        (
            case
            for case in suite["cases"]
            if f"{case['role'].lower()}:{case['case_id']}" == output.case_id
        ),
        None,
    )
    if (
        expected is None
        or document.get("suite_digest") != suite["suite_digest"]
        or document.get("role") != expected["role"]
        or document.get("fixture") != expected["fixture"]
        or output.fixture_digest != digest_of(expected["fixture"])
        or document.get("oracle_digest") != digest_of(expected["oracle"]).value
        or document.get("sink_manifest", {}).get("strategy_implementation_digest")
        != evidence_first_task_strategy_implementation_digest().value
    ):
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "evidence capability output does not match the pinned suite",
        )


def _source_request(fixture, case_id):
    revision = fixture["revision"]
    target_digest = digest_of(
        {"kind": TargetKind.REPOSITORY_REVISION.value, "revision": revision}
    )
    target = CanonicalBuildTarget(
        target_id=StableId(f"build_target_{target_digest.value[-32:]}"),
        target_kind=TargetKind.REPOSITORY_REVISION,
        canonical_identity=(("revision", revision),),
        resolution_receipt_id=StableId("target_receipt_" + "1" * 32),
        resolution_receipt_digest=digest_of({"revision": revision}),
        obligation=CoverageObligation.REQUIRED,
        boundary="EXACT",
        digest=target_digest,
    )
    return KnowledgeUpdateRequest(
        idempotency_key=IdempotencyKey(f"evidence-capability:{case_id}"),
        objective=BuildObjective.create(
            objective_id=f"evidence-capability:{case_id}",
            description=fixture["question"],
            unacceptable_outcomes=("invented source result",),
        ),
        target=target,
        scope_id=StableId("scope_" + "1" * 32),
        scope_revision=Revision(1),
        source_id=StableId("source_" + "1" * 32),
        source_revision=Revision(1),
        binding_id=StableId("binding_" + "1" * 32),
        binding_revision=Revision(1),
        expected_current_snapshot_id=None,
        max_steps=4,
        max_items_per_step=20,
        max_bytes_per_step=4096,
        classification="INTERNAL",
        actor="capability-evaluation",
        correlation_ref=CorrelationRef(f"evidence-capability:{case_id}"),
        allowed_source_paths=(fixture["allowed_path"],),
    )


def _question_and_packet(fixture):
    checklist = QuestionChecklist.create(
        original_request=fixture["question"],
        questions=tuple(fixture["checklist"]),
    )
    items = []
    for index, raw in enumerate(fixture["evidence"], 1):
        content_digest = digest_of(raw["content"])
        items.append(
            EvidenceItem(
                evidence_id=f"evidence-{index}",
                operation_id=StableId(f"source_operation_{index:032x}"),
                artifact_id=StableId(f"source_artifact_{index:032x}"),
                tool="local-git.read@1",
                repository_revision="a" * 40,
                locator=raw["locator"],
                coverage=(("path", raw["locator"]), ("revision", "a" * 40)),
                content=raw["content"],
                content_digest=content_digest,
                digest=digest_of(
                    {"evidence_id": f"evidence-{index}", "content": raw["content"]}
                ),
            )
        )
    packet_digest = digest_of(
        {"checklist": checklist.digest.value, "items": [x.digest.value for x in items]}
    )
    packet = EvidencePacket(
        packet_id=StableId(f"evidence_packet_{packet_digest.value[-32:]}"),
        checklist_digest=checklist.digest,
        target_digest=digest_of("fixture-target"),
        items=tuple(items),
        operation_references=tuple(item.operation_id for item in items),
        digest=packet_digest,
    )
    return checklist, packet


def _draft(fixture, checklist, packet):
    sections = tuple(
        EvidenceAnswerSection.create(
            section_id=raw["section_id"],
            kind=AnswerSectionKind(raw["kind"]),
            text=raw["text"],
            checklist_item_ids=tuple(raw["checklist_item_ids"]),
            evidence_ids=tuple(raw["evidence_ids"]),
        )
        for raw in fixture["draft_sections"]
    )
    return EvidenceAnswerDraft.create(
        revision=1, checklist=checklist, packet=packet, sections=sections
    )


__all__ = [
    "LiveCapabilityCaseRunner",
    "load_capability_output_document",
    "save_capability_output_document",
    "verify_capability_output_against_suite",
]
