"""Stable JSON projections shared by user-facing adapters."""

from __future__ import annotations


def management_execution_payload(execution: object) -> dict[str, object]:
    result = execution.result
    return {
        "attempt_id": execution.attempt.attempt_id.value,
        "attempt_revision": execution.attempt.revision.value,
        "state": execution.attempt.state.value,
        "result_id": result.result_id.value,
        "result_revision": result.revision.value,
        "result_digest": result.result_digest.value,
        "steps": [
            {
                "name": step.name,
                "state": step.state.value,
                "result_reference": step.result_reference,
                "failure_code": step.failure_code,
                "retryable": step.retryable,
            }
            for step in result.steps
        ],
    }


def target_resolution_payload(receipt: object) -> dict[str, object]:
    return {
        "receipt_id": receipt.receipt_id.value,
        "outcome": receipt.outcome.value,
        "target_kind": receipt.target_kind.value,
        "canonical_identity": dict(receipt.canonical_identity),
        "candidates": [dict(item) for item in receipt.candidates],
        "digest": receipt.digest.value,
    }


def knowledge_update_payload(result: object) -> dict[str, object]:
    return {
        "result_id": result.result_id.value,
        "attempt_id": result.attempt_id.value,
        "state": result.state.value,
        "stop_reason": result.stop_reason.value,
        "target_coverage_complete": result.target_coverage_complete,
        "published_snapshot_id": (
            result.published_snapshot_id.value if result.published_snapshot_id else None
        ),
        "source_operation_references": [item.value for item in result.source_operation_references],
        "artifact_references": [item.value for item in result.artifact_references],
        "limitations": result.limitations,
        "digest": result.digest.value,
    }


def sufficiency_assessment_payload(assessment: object) -> dict[str, object]:
    return {
        "assessment_id": assessment.assessment_id.value,
        "snapshot_id": assessment.snapshot_id.value,
        "sufficient": assessment.sufficient,
        "items": [
            {
                "need_id": item.need_id,
                "status": item.status.value,
                "gap": item.gap,
                "supporting_references": (
                    [ref.value for ref in item.proof.supporting_references] if item.proof else []
                ),
                "unknowns": item.unknowns,
                "limitations": item.limitations,
            }
            for item in assessment.items
        ],
        "joint_constraint_failures": assessment.joint_constraint_failures,
        "digest": assessment.digest.value,
    }


def authorized_task_answer_payload(result: object) -> dict[str, object]:
    """Project an authorized candidate without claiming adapter delivery."""

    return {
        "task_id": result.task.task_id.value,
        "task_revision": result.task.revision.value,
        "snapshot_id": result.assessment.snapshot_id.value,
        "requirement_id": result.requirement.requirement_id.value,
        "requirement": {
            "needs": [
                {
                    "need_id": need.need_id,
                    "question": need.question,
                }
                for need in getattr(result.requirement, "needs", ())
            ],
        },
        "assessment": sufficiency_assessment_payload(result.assessment),
        "candidate": {
            "candidate_id": result.candidate.candidate_id.value,
            "response_kind": result.candidate.response_kind.value,
            "body": result.candidate.body,
            "claims": [
                {
                    "claim_id": claim.claim_id,
                    "need_id": claim.need_id,
                    "kind": claim.kind.value,
                    "text": claim.text,
                    "formal_reference": (
                        claim.formal_reference.value
                        if claim.formal_reference
                        else None
                    ),
                    "gap": claim.gap,
                }
                for claim in result.candidate.claims
            ],
            "digest": result.candidate.digest.value,
        },
        "review": {
            "review_id": result.review.review_id.value,
            "decision": result.review.decision.value,
            "digest": result.review.digest.value,
        },
        "authorization": {
            "authorization_id": result.authorization.authorization_id.value,
            "digest": result.authorization.digest.value,
        },
        "delivery": {
            "performed": False,
            "message": "answer is authorized but no external delivery was claimed",
        },
        "digest": result.digest.value,
    }


def telemetry_events_payload(events: tuple[object, ...]) -> dict[str, object]:
    return {
        "events": [
            {
                "event_id": event.event_id.value,
                "owner": event.owner,
                "operation": event.operation,
                "outcome": event.outcome,
                "correlation_reference": event.correlation_reference,
                "causation_reference": event.causation_reference,
                "authority_references": event.authority_references,
                "metrics": [
                    {"name": metric.name, "value": metric.value, "unit": metric.unit}
                    for metric in event.metrics
                ],
                "cost_status": event.cost_status,
                "estimated_cost": (
                    {
                        "currency": event.estimated_cost.currency,
                        "amount_microunits": event.estimated_cost.amount_microunits,
                        "pricing_reference": event.estimated_cost.pricing_reference,
                    }
                    if event.estimated_cost
                    else None
                ),
                "classification": event.classification,
                "occurred_at": event.occurred_at.isoformat(),
                "digest": event.digest.value,
            }
            for event in events
        ]
    }
