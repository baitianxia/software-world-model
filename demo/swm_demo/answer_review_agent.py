from __future__ import annotations

from swm_demo.agent_contract import (
    AgentTask,
    AnswerCandidate,
    AnswerReviewResult,
    KnowledgeUseServices,
)
from swm_demo.knowledge_requirement import FACT, INFERENCE
from swm_demo.model_gateway import ModelGateway, ModelPhase


class AnswerReviewAgent:
    """Reviews Requirement, Assessment, formal propositions and rendered answer."""

    def __init__(
        self, application: KnowledgeUseServices, model_gateway: ModelGateway
    ):
        self.application = application
        self.model_gateway = model_gateway

    def review(
        self,
        original_request: str,
        task: AgentTask,
        candidate: AnswerCandidate,
    ) -> AnswerReviewResult:
        issues: list[str] = []
        if original_request != task.original_request:
            issues.append("review did not receive the original user request")
        if candidate.original_request != original_request:
            issues.append("Answer Candidate changed the original user request")
        if candidate.task_id != task.task_id or candidate.scope_id != task.scope_id:
            issues.append("Answer Candidate and Agent Task identity differ")

        requirement = candidate.requirement
        assessment = candidate.assessment
        if requirement is None or assessment is None:
            issues.append("Answer Candidate has no bound Requirement and Assessment")
        else:
            if requirement.task_id != task.task_id or requirement.scope_id != task.scope_id:
                issues.append("Knowledge Requirement and Agent Task identity differ")
            if assessment.requirement is not requirement:
                issues.append("Assessment does not bind the unchanged Requirement object")
            if candidate.assessment_reference != assessment.assessment_id:
                issues.append("Answer Candidate assessment reference is inconsistent")
            if not assessment.complete:
                issues.append("Knowledge Sufficiency Assessment is incomplete")
            try:
                validation = self.application.validate_sufficiency_assessment(
                    assessment
                )
            except Exception as error:
                issues.append(f"Assessment validation failed: {error}")
            else:
                if not validation["mechanically_valid"]:
                    issues.extend(str(item) for item in validation["errors"])

        current = self.application.current_snapshot(task.scope_id)
        if candidate.snapshot_id != current["snapshot_id"]:
            issues.append("Answer Candidate is bound to a stale Snapshot")
        if candidate.revision != current["revision"]:
            issues.append("Answer Candidate KnowledgeContext revision differs")
        if assessment is not None:
            if candidate.snapshot_id != assessment.snapshot_id:
                issues.append("Answer Candidate and Assessment Snapshot differ")
            if candidate.revision != assessment.knowledge_context_reference:
                issues.append("Answer Candidate and Assessment context differ")
        if not candidate.claims:
            issues.append("Answer Candidate contains no claims")
        if issues:
            return AnswerReviewResult(
                decision="REJECT", issues=tuple(issues), review_model_call_id=None
            )

        assert assessment is not None
        references_by_need = {
            item.need_id: set(item.formal_knowledge_reference_ids)
            for item in assessment.items
        }
        covered_need_ids: set[str] = set()
        for claim in candidate.claims:
            if not claim.knowledge_reference_ids:
                issues.append(f"claim has no knowledge reference: {claim.text}")
            if not claim.need_ids:
                issues.append(f"claim is not mapped to a Knowledge Need: {claim.text}")
            for need_id in claim.need_ids:
                allowed = references_by_need.get(need_id)
                if allowed is None:
                    issues.append(f"claim maps an unknown Knowledge Need: {need_id}")
                    continue
                covered_need_ids.add(need_id)
                if not set(claim.knowledge_reference_ids).issubset(allowed):
                    issues.append(
                        f"claim references knowledge outside Need {need_id}: {claim.text}"
                    )
        missing_needs = sorted(set(references_by_need) - covered_need_ids)
        if missing_needs:
            issues.append(f"Answer Candidate omits Knowledge Needs: {missing_needs}")

        formal_statements: dict[str, str] = {}
        for kind in (FACT, INFERENCE):
            identifiers = tuple(
                reference.reference_id
                for item in assessment.items
                for reference in item.formal_knowledge_references
                if reference.kind == kind
            )
            if not identifiers:
                continue
            explained = self.application.explain_knowledge_batch(
                task.scope_id,
                candidate.snapshot_id,
                kind,
                identifiers,
            )
            if explained["missing_ids"]:
                issues.append(
                    f"formal references disappeared during review: {explained['missing_ids']}"
                )
            for item in explained["items"]:
                item_id = str(
                    item["fact_id"] if kind == FACT else item["inference_id"]
                )
                formal_statements[item_id] = str(
                    item["proposition"] if kind == FACT else item["statement"]
                )
        for claim in candidate.claims:
            for reference_id in claim.knowledge_reference_ids:
                statement = formal_statements.get(reference_id)
                if statement is None or statement not in claim.text:
                    issues.append(
                        "claim is not directly entailed by its formal proposition: "
                        f"{claim.text}"
                    )

        expected_answer = "\n".join(item.text for item in candidate.claims)
        if candidate.answer != expected_answer:
            issues.append("rendered answer differs from its structured claims")
        authoritative_claims = [
            "；".join(
                formal_statements[reference_id]
                for reference_id in claim.knowledge_reference_ids
            )
            for claim in candidate.claims
        ]
        current_after_review_read = self.application.current_snapshot(task.scope_id)
        if current_after_review_read["snapshot_id"] != candidate.snapshot_id:
            issues.append("Snapshot changed while Answer Review was reading knowledge")
        if issues:
            return AnswerReviewResult(
                decision="REJECT", issues=tuple(issues), review_model_call_id=None
            )

        review_context = self.model_gateway.open_context(
            task.task_id, ModelPhase.REVIEW
        )
        try:
            reviewed = self.model_gateway.invoke(
                "review-answer",
                {
                    "original_request": original_request,
                    "requirement": [
                        {
                            "need_id": item.need_id,
                            "question": item.question,
                            "sufficiency_criterion": item.sufficiency_criterion,
                        }
                        for item in requirement.needs
                    ],
                    "candidate_claims": [item.text for item in candidate.claims],
                    "formal_propositions": list(formal_statements.values()),
                    "authoritative_claims": authoritative_claims,
                },
                context=review_context,
            )
        finally:
            self.model_gateway.close_context(review_context)
        decision = str(reviewed.output["decision"])
        unsupported = tuple(
            f"unsupported claim: {item}"
            for item in reviewed.output.get("unsupported_claims", [])
        )
        if decision == "PASS" and unsupported:
            decision = "REJECT"
        return AnswerReviewResult(
            decision=decision,
            issues=unsupported,
            review_model_call_id=reviewed.model_call_id,
        )
