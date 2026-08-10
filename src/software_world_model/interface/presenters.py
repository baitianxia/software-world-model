"""Stable JSON projections shared by user-facing adapters."""

from __future__ import annotations

import json


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


def _member_payload(member: object) -> dict[str, str]:
    return {
        "kind": member.kind.value,
        "root_id": member.root_id.value,
        "state_id": member.state_id.value,
        "state_digest": member.state_digest.value,
    }


def structure_snapshot_payload(snapshot: object) -> dict[str, object]:
    """Project only immutable, no-payload Structure Snapshot metadata."""

    return {
        "snapshot_id": snapshot.snapshot_id.value,
        "scope_id": snapshot.scope_id.value,
        "revision": snapshot.snapshot_revision.value,
        "previous_snapshot_id": (
            snapshot.previous_snapshot_id.value
            if snapshot.previous_snapshot_id is not None
            else None
        ),
        "schema_ref": snapshot.schema_ref,
        "schema_digest": snapshot.schema_digest.value,
        "schema_adoption_mode": snapshot.schema_adoption_mode.value,
        "schema_registration_digest": snapshot.schema_registration_digest.value,
        "schema_availability_digest": snapshot.schema_availability_digest.value,
        "schema_adoption_digest": snapshot.schema_adoption_digest.value,
        "publication_mode": snapshot.publication_mode.value,
        "manifest_digest": snapshot.manifest_digest.value,
        "published_at": snapshot.published_at.isoformat(),
        "manifest": [_member_payload(member) for member in snapshot.members],
        "coverages": [
            {
                "root_id": item.coverage_root_id.value,
                "state_id": item.coverage_state_id.value,
                "state_digest": item.coverage_state_digest.value,
            }
            for item in snapshot.coverages
        ],
        "upstream_entities": [
            {
                "snapshot_id": item.upstream_snapshot_id.value,
                "entity_root_id": item.entity_root_id.value,
                "entity_state_id": item.entity_state_id.value,
                "entity_state_digest": item.entity_state_digest.value,
            }
            for item in snapshot.upstream_entities
        ],
    }


def structure_read_bundle_receipt_payload(receipt: object) -> dict[str, object]:
    """Project the exact post-publication Bundle authority without file payload."""

    return {
        "receipt_id": receipt.receipt_id.value,
        "idempotency_key": receipt.idempotency_key.value,
        "kind": receipt.kind.value,
        "request_digest": receipt.request_digest.value,
        "scope_id": receipt.scope_id.value,
        "snapshot_ids": [item.value for item in receipt.snapshot_ids],
        "session_id": (
            receipt.session_id.value if receipt.session_id is not None else None
        ),
        "read_set_digest": (
            receipt.read_set_digest.value
            if receipt.read_set_digest is not None
            else None
        ),
        "stored_bundle": {
            "locator": receipt.stored_bundle.locator,
            "format_ref": receipt.stored_bundle.format_ref,
            "bundle_digest": receipt.stored_bundle.bundle_digest.value,
            "file_digest": receipt.stored_bundle.file_digest.value,
        },
        "created_at": receipt.created_at.isoformat(),
        "digest": receipt.digest.value,
    }


def structure_read_bundle_availability_payload(
    availability: object,
) -> dict[str, object]:
    """Project a mechanically revalidated Bundle availability decision."""

    return {
        "snapshot_id": availability.snapshot_id.value,
        "status": availability.status.value,
        "reason_code": availability.reason_code,
        "receipt": (
            structure_read_bundle_receipt_payload(availability.receipt)
            if availability.receipt is not None
            else None
        ),
    }


def structure_snapshot_query_payload(snapshot: object) -> dict[str, object]:
    """Return an independently executed exact historical Snapshot query."""

    projected = structure_snapshot_payload(snapshot)
    lines = [
        (
            f"HISTORICAL_SNAPSHOT_QUERY exact_id={snapshot.snapshot_id.value} "
            f"scope={snapshot.scope_id.value} revision={snapshot.snapshot_revision.value} "
            f"manifest_digest={snapshot.manifest_digest.value}"
        ),
        (
            f"SCHEMA ref={snapshot.schema_ref} digest={snapshot.schema_digest.value} "
            f"registration_digest={snapshot.schema_registration_digest.value} "
            f"availability_digest={snapshot.schema_availability_digest.value} "
            f"adoption_digest={snapshot.schema_adoption_digest.value} "
            f"adoption_mode={snapshot.schema_adoption_mode.value}"
        ),
    ]
    lines.extend(
        (
            f"COVERAGE root={item.coverage_root_id.value} "
            f"state={item.coverage_state_id.value} "
            f"state_digest={item.coverage_state_digest.value}"
        )
        for item in snapshot.coverages
    )
    lines.extend(
        (
            f"MEMBER kind={item.kind.value} root={item.root_id.value} "
            f"state={item.state_id.value} state_digest={item.state_digest.value}"
        )
        for item in snapshot.members
    )
    return {
        "query": {
            "mode": "EXACT_STRUCTURE_SNAPSHOT_ID",
            "snapshot_id": snapshot.snapshot_id.value,
            "read_only": True,
        },
        "snapshot": projected,
        "audit_lines": lines,
    }


def structure_read_session_payload(session: object) -> dict[str, object]:
    """Project an exact no-payload Structure Session and ordered Read Set."""

    snapshots = []
    for ordinal, snapshot in enumerate(session.snapshots):
        snapshots.append(
            {
                "ordinal": ordinal,
                "scope_id": snapshot.scope_id.value,
                "snapshot_id": snapshot.snapshot_id.value,
                "snapshot_revision": snapshot.snapshot_revision.value,
                "snapshot_manifest_digest": (
                    snapshot.snapshot_manifest_digest.value
                ),
                "schema_ref": snapshot.schema_ref,
                "schema_digest": snapshot.schema_digest.value,
                "schema_registration_digest": (
                    snapshot.schema_registration_digest.value
                ),
                "schema_availability_digest": (
                    snapshot.schema_availability_digest.value
                ),
                "schema_adoption_digest": snapshot.schema_adoption_digest.value,
                "coverage_set_digest": snapshot.coverage_set_digest.value,
                "digest": snapshot.digest.value,
                "coverages": [
                    {
                        "coverage_root_id": coverage.coverage_root_id.value,
                        "coverage_root_digest": coverage.coverage_root_digest.value,
                        "coverage_root_ref": coverage.coverage_root_ref,
                        "coverage_state_id": coverage.coverage_state_id.value,
                        "coverage_state_digest": (
                            coverage.coverage_state_digest.value
                        ),
                        "profile_ref": coverage.profile_ref,
                        "schema_ref": coverage.schema_ref,
                        "schema_digest": coverage.schema_digest.value,
                        "source_binding_id": coverage.source_binding_id.value,
                        "logical_reactor_root": coverage.logical_reactor_root,
                        "evaluation_context_ref": (
                            coverage.evaluation_context_ref
                        ),
                        "evaluation_context_digest": (
                            coverage.evaluation_context_digest.value
                        ),
                        "canonicalization_ref": coverage.canonicalization_ref,
                        "canonicalization_digest": (
                            coverage.canonicalization_digest.value
                        ),
                        "knowledge_context_digest": (
                            coverage.knowledge_context_digest.value
                        ),
                        "source_revision": coverage.source_revision,
                        "member_manifest_digest": (
                            coverage.member_manifest_digest.value
                        ),
                        "comparison_basis_digest": (
                            coverage.comparison_basis_digest.value
                        ),
                        "digest": coverage.digest.value,
                    }
                    for coverage in snapshot.coverages
                ],
            }
        )
    lines = [
        (
            f"STRUCTURE_READ_SESSION id={session.session_id.value} "
            f"scope={session.scope_id.value} scope_revision={session.scope_revision.value} "
            f"purpose={session.purpose.value} caller={session.caller_ref} "
            f"task={session.task_boundary.task_id.value} "
            f"task_revision={session.task_boundary.task_revision.value} "
            f"scope_assertion={session.scope_assertion.assertion_id.value} "
            f"mode={session.selection_mode.value} "
            f"order={session.order.value} read_set_digest={session.read_set_digest.value}"
        )
    ]
    lines.extend(
        (
            f"READ_SET_SNAPSHOT ordinal={item['ordinal']} "
            f"id={item['snapshot_id']} revision={item['snapshot_revision']} "
            f"manifest_digest={item['snapshot_manifest_digest']}"
        )
        for item in snapshots
    )
    comparisons = [
        {
            "assessment_id": item.assessment_id.value,
            "ordinal": item.ordinal,
            "purpose": item.purpose.value,
            "base_snapshot_id": item.base_snapshot_id.value,
            "base_snapshot_binding_digest": (
                item.base_snapshot_binding_digest.value
            ),
            "target_snapshot_id": item.target_snapshot_id.value,
            "target_snapshot_binding_digest": (
                item.target_snapshot_binding_digest.value
            ),
            "base_knowledge_context_digests": [
                value.value for value in item.base_knowledge_context_digests
            ],
            "target_knowledge_context_digests": [
                value.value for value in item.target_knowledge_context_digests
            ],
            "comparison_basis_digests": [
                value.value for value in item.comparison_basis_digests
            ],
            "outcome": item.outcome.value,
            "digest": item.digest.value,
        }
        for item in session.context_comparisons
    ]
    lines.extend(
        (
            f"CONTEXT_COMPARISON ordinal={item['ordinal']} "
            f"id={item['assessment_id']} outcome={item['outcome']} "
            f"base={item['base_snapshot_id']} target={item['target_snapshot_id']} "
            f"basis={','.join(item['comparison_basis_digests'])} "
            f"digest={item['digest']}"
        )
        for item in comparisons
    )
    return {
        "session_id": session.session_id.value,
        "request_digest": session.request_digest.value,
        "scope_id": session.scope_id.value,
        "scope_revision": session.scope_revision.value,
        "task_boundary": {
            "task_id": session.task_boundary.task_id.value,
            "task_revision": session.task_boundary.task_revision.value,
            "scope_id": session.task_boundary.scope_id.value,
            "purpose": session.task_boundary.purpose,
            "classification": session.task_boundary.classification,
            "digest": session.task_boundary.digest.value,
        },
        "scope_assertion": {
            "assertion_id": session.scope_assertion.assertion_id.value,
            "definition_revision": (
                session.scope_assertion.definition_revision.value
            ),
            "purpose": session.scope_assertion.purpose.value,
            "outcome": session.scope_assertion.outcome.value,
            "caller_ref": session.scope_assertion.caller_ref,
            "request_ref": session.scope_assertion.request_ref,
            "classification": session.scope_assertion.classification,
            "digest": session.scope_assertion.digest.value,
        },
        "caller_ref": session.caller_ref,
        "purpose": session.purpose.value,
        "selection_mode": session.selection_mode.value,
        "order": session.order.value,
        "read_set_digest": session.read_set_digest.value,
        "opened_at": session.opened_at.isoformat(),
        "digest": session.digest.value,
        "snapshots": snapshots,
        "context_comparisons": comparisons,
        "payload_policy": {
            "evidence_payload_fields": 0,
            "source_payload_fields": 0,
        },
        "audit_lines": lines,
    }


def maven_structure_update_payload(interface_result: object) -> dict[str, object]:
    """Project the full human-auditable result of one Maven Structure build."""

    result = interface_result.update
    evaluation = result.evaluation
    receipt = result.publication_receipt
    snapshot = receipt.snapshot
    evidence_locators = {
        item.evidence_id.value: item.locator for item in evaluation.evidence
    }

    def locators(references: object) -> list[str]:
        return [
            evidence_locators[
                reference.value if hasattr(reference, "value") else str(reference)
            ]
            for reference in references
        ]

    entities = []
    for record in evaluation.entities:
        entities.append(
            {
                "entity_type": record.root.entity_type.value,
                "root_id": record.root_id.value,
                "root_digest": record.root.allocation_key_digest.value,
                "state_id": record.state_id.value,
                "state_digest": record.state_digest.value,
                "root_fields": record.root.root_fields.as_dict(),
                "state_fields": record.state.state_payload_fields.as_dict(),
                "evidence_locators": locators(record.state.evidence_references),
            }
        )

    relations = []
    for record in evaluation.relations:
        relations.append(
            {
                "source_root_id": record.root.subject.entity_root_id.value,
                "predicate": record.root.predicate.value,
                "target_root_id": record.root.object.entity_root_id.value,
                "fact_root_id": record.root_id.value,
                "fact_root_digest": record.root.allocation_key_digest.value,
                "fact_state_id": record.state_id.value,
                "fact_state_digest": record.state_digest.value,
                "predicate_state_fields": (
                    record.state.predicate_state_payload_fields.as_dict()
                ),
                "evidence_locators": locators(record.state.evidence_references),
            }
        )

    dependencies = []
    for item in evaluation.report.dependency_declarations:
        resolved_gav = None
        if item.resolved_dependency_version_or_null is not None:
            resolved_gav = (
                f"{item.resolved_dependency_ga}:"
                f"{item.resolved_dependency_version_or_null}"
            )
        dependencies.append(
            {
                "consumer_pom_locator": item.consumer_pom_locator,
                "consumer_gav": item.consumer_gav,
                "declared_gav_expression": (
                    item.declared_dependency_gav_expression
                ),
                "resolved_ga": item.resolved_dependency_ga,
                "resolved_version": item.resolved_dependency_version_or_null,
                "resolved_gav": resolved_gav,
                "matched_reactor_target_gav": (
                    item.matched_reactor_target_gav_or_null
                ),
                "decision": item.decision,
                "excluded": item.decision == "EXCLUDED",
                "profile_ref": evaluation.coverage.root.profile_ref,
                "exclusion_reason": item.reason_code,
                "relation_root_id": item.relation_root_id,
                "relation_state_id": item.relation_state_id,
                "evidence_locators": locators(item.evidence_references),
            }
        )

    exclusions = [
        {
            "consumer_pom_locator": item.consumer_pom_locator,
            "declared_gav_expression": item.declared_dependency_gav_expression,
            "resolved_ga": item.resolved_dependency_ga,
            "resolved_version": item.resolved_dependency_version_or_null,
            "matched_reactor_target_gav": (
                item.matched_reactor_target_gav_or_null
            ),
            "decision": item.decision,
            "profile_ref": evaluation.coverage.root.profile_ref,
            "reason_code": item.reason_code,
            "evidence_locators": locators(item.evidence_references),
        }
        for item in evaluation.exclusions
    ]
    coverage = evaluation.coverage
    authority = result.authority_result
    objective = interface_result.objective
    target = interface_result.target
    attempt = interface_result.attempt
    target_authority = interface_result.target_authority
    admission = interface_result.admission
    verifier_assessment = result.verifier_assessment
    registration = interface_result.schema_registration
    availability = interface_result.schema_availability
    adoption = interface_result.schema_adoption
    payload = {
        "objective": {
            "objective_id": objective.objective_id,
            "description": objective.description,
            "unacceptable_outcomes": objective.unacceptable_outcomes,
            "digest": objective.digest.value,
        },
        "target": {
            "target_id": target.target_id.value,
            "target_kind": target.target_kind.value,
            "canonical_identity": dict(target.canonical_identity),
            "resolution_receipt_id": target.resolution_receipt_id.value,
            "resolution_receipt_digest": target.resolution_receipt_digest.value,
            "obligation": target.obligation.value,
            "boundary": target.boundary,
            "digest": target.digest.value,
        },
        "requirement": {
            "binding": None,
            "binding_digest": (
                authority.requirement_binding_digest.value
                if authority.requirement_binding_digest is not None
                else None
            ),
            "manual_zero_question_update": True,
        },
        "attempt": {
            "attempt_id": attempt.attempt_id.value,
            "state": attempt.state.value,
            "request_digest": attempt.request_digest.value,
            "objective_id": attempt.objective_id,
            "objective_digest": attempt.objective_digest.value,
            "target_id": attempt.target_id.value,
            "target_digest": attempt.target_digest.value,
            "target_resolution_receipt_id": (
                attempt.target_resolution_receipt_id.value
            ),
            "target_resolution_receipt_digest": (
                attempt.target_resolution_receipt_digest.value
            ),
            "requirement_binding_digest": (
                attempt.requirement_binding_digest.value
                if attempt.requirement_binding_digest is not None
                else None
            ),
            "target_authority_id": (
                attempt.target_authority_id.value
                if attempt.target_authority_id is not None
                else None
            ),
            "created_at": attempt.created_at.isoformat(),
            "revised_at": attempt.revised_at.isoformat(),
        },
        "result": {
            "result_id": authority.result_id.value,
            "attempt_id": authority.attempt_id.value,
            "state": authority.state.value,
            "request_digest": authority.request_digest.value,
            "objective_id": authority.objective_id,
            "objective_digest": authority.objective_digest.value,
            "target_id": authority.target_id.value,
            "target_digest": authority.target_digest.value,
            "target_authority_id": (
                authority.target_authority_id.value
                if authority.target_authority_id is not None
                else None
            ),
            "target_authority_digest": (
                authority.target_authority_digest.value
                if authority.target_authority_digest is not None
                else None
            ),
            "admission_id": (
                authority.admission_id.value
                if authority.admission_id is not None
                else None
            ),
            "admission_digest": (
                authority.admission_digest.value
                if authority.admission_digest is not None
                else None
            ),
            "application_acceptance_ref": (
                authority.application_acceptance_ref
            ),
            "application_acceptance_digest": (
                authority.application_acceptance_digest.value
                if authority.application_acceptance_digest is not None
                else None
            ),
            "artifact_read_package_id": (
                authority.artifact_read_package_id.value
                if authority.artifact_read_package_id is not None
                else None
            ),
            "artifact_read_package_digest": (
                authority.artifact_read_package_digest.value
                if authority.artifact_read_package_digest is not None
                else None
            ),
            "artifact_use_confirmation_id": (
                authority.artifact_use_confirmation_id.value
                if authority.artifact_use_confirmation_id is not None
                else None
            ),
            "artifact_use_confirmation_digest": (
                authority.artifact_use_confirmation_digest.value
                if authority.artifact_use_confirmation_digest is not None
                else None
            ),
            "publication_id": (
                authority.publication_id.value
                if authority.publication_id is not None
                else None
            ),
            "publication_digest": (
                authority.publication_digest.value
                if authority.publication_digest is not None
                else None
            ),
            "published_snapshot_id": (
                authority.published_snapshot_id.value
                if authority.published_snapshot_id is not None
                else None
            ),
            "previous_snapshot_id": (
                authority.previous_snapshot_id.value
                if authority.previous_snapshot_id is not None
                else None
            ),
            "replacement_deletions_digest": (
                authority.replacement_deletions_digest.value
                if authority.replacement_deletions_digest is not None
                else None
            ),
            "completed_at": authority.completed_at.isoformat(),
            "digest": authority.digest.value,
        },
        "target_authority": {
            "authority_id": target_authority.authority_id.value,
            "scope_id": target_authority.scope_id.value,
            "binding_id": target_authority.binding_id.value,
            "logical_reactor_root": target_authority.logical_reactor_root,
            "canonical_system_key": target_authority.canonical_system_key,
            "established_scope_revision": (
                target_authority.established_scope_revision.value
            ),
            "established_binding_revision": (
                target_authority.established_binding_revision.value
            ),
            "digest": target_authority.digest.value,
        },
        "admission": {
            "admission_id": admission.admission_id.value,
            "outcome": admission.outcome.value,
            "candidate_ref": admission.candidate_ref,
            "candidate_digest": admission.candidate_digest.value,
            "batch_digest": admission.batch_digest.value,
            "closure_digest": admission.closure_digest.value,
            "read_set_digest": admission.read_set_digest.value,
            "scope_assertion_digest": admission.scope_assertion_digest.value,
            "schema_ref": admission.schema_ref,
            "schema_digest": admission.schema_digest.value,
            "schema_registration_digest": (
                admission.schema_registration_digest.value
            ),
            "schema_availability_digest": (
                admission.schema_availability_digest.value
            ),
            "knowledge_context_digest": admission.knowledge_context_digest.value,
            "upstream_digest": admission.upstream_digest.value,
            "provenance_digest": admission.provenance_digest.value,
            "artifact_use_confirmation_id": (
                admission.artifact_use_confirmation_id.value
            ),
            "artifact_use_confirmation_digest": (
                admission.artifact_use_confirmation_digest.value
            ),
            "verifier_assessment_id": admission.verifier_assessment_id.value,
            "verifier_assessment_digest": (
                admission.verifier_assessment_digest.value
            ),
            "verifier_ref": admission.verifier_ref,
            "findings": [
                {"code": item.code, "message": item.message}
                for item in admission.findings
            ],
            "decided_at": admission.decided_at.isoformat(),
            "digest": admission.digest.value,
        },
        "verifier_assessment": {
            "assessment_id": verifier_assessment.assessment_id.value,
            "outcome": verifier_assessment.outcome.value,
            "candidate_digest": verifier_assessment.candidate_digest.value,
            "verified_candidate_digest": (
                verifier_assessment.verified_candidate_digest.value
            ),
            "candidate_evaluation_digest": (
                verifier_assessment.candidate_evaluation_digest.value
            ),
            "verified_evaluation_digest": (
                verifier_assessment.verified_evaluation_digest.value
            ),
            "candidate_report_digest": (
                verifier_assessment.candidate_report_digest.value
            ),
            "verified_report_digest": (
                verifier_assessment.verified_report_digest.value
            ),
            "batch_digest": verifier_assessment.batch_digest.value,
            "verified_batch_digest": (
                verifier_assessment.verified_batch_digest.value
            ),
            "closure_digest": verifier_assessment.closure_digest.value,
            "verified_closure_digest": (
                verifier_assessment.verified_closure_digest.value
            ),
            "read_set_digest": verifier_assessment.read_set_digest.value,
            "verified_read_set_digest": (
                verifier_assessment.verified_read_set_digest.value
            ),
            "provenance_digest": verifier_assessment.provenance_digest.value,
            "verification_context_digest": (
                verifier_assessment.verification_context_digest.value
            ),
            "artifact_use_confirmation_id": (
                verifier_assessment.artifact_use_confirmation_id.value
            ),
            "artifact_use_confirmation_digest": (
                verifier_assessment.artifact_use_confirmation_digest.value
            ),
            "verifier_ref": verifier_assessment.verifier_ref,
            "findings": [
                {"code": item.code, "message": item.message}
                for item in verifier_assessment.findings
            ],
            "assessed_at": verifier_assessment.assessed_at.isoformat(),
            "digest": verifier_assessment.digest.value,
        },
        "application_acceptance": {
            "acceptance_ref": result.application_acceptance.acceptance_ref,
            "decision": result.application_acceptance.decision.value,
            "batch_digest": result.application_acceptance.batch_digest.value,
            "report_digest": result.application_acceptance.report_digest.value,
            "digest": result.application_acceptance.digest.value,
        },
        "artifact_use": {
            "confirmation_id": (
                result.artifact_use_confirmation.confirmation_id.value
            ),
            "purpose": result.artifact_use_confirmation.purpose.value,
            "package_id": result.artifact_use_confirmation.package_id.value,
            "package_digest": result.artifact_use_confirmation.package_digest.value,
            "closure_id": result.artifact_use_confirmation.closure_id.value,
            "closure_digest": result.artifact_use_confirmation.closure_digest.value,
            "protection_id": (
                result.artifact_use_confirmation.protection_id.value
            ),
            "protection_digest": (
                result.artifact_use_confirmation.protection_digest.value
            ),
            "downstream_request_ref": (
                result.artifact_use_confirmation.downstream_request_ref
            ),
            "downstream_request_digest": (
                result.artifact_use_confirmation.downstream_request_digest.value
            ),
            "downstream_candidate_ref": (
                result.artifact_use_confirmation.downstream_candidate_ref
            ),
            "downstream_candidate_digest": (
                result.artifact_use_confirmation.downstream_candidate_digest.value
            ),
            "confirmed_at": (
                result.artifact_use_confirmation.confirmed_at.isoformat()
            ),
            "digest": result.artifact_use_confirmation.digest.value,
        },
        "schema": {
            "definition": {
                "schema_ref": registration.definition.schema_ref,
                "schema_digest": registration.definition.schema_digest.value,
                "definition_digest": registration.definition.digest.value,
            },
            "registration": {
                "registration_id": registration.registration_id.value,
                "proposal_ref": registration.proposal_ref,
                "review_ref": registration.review_ref,
                "registered_by": registration.registered_by,
                "digest": registration.digest.value,
            },
            "availability": {
                "availability_id": availability.availability_id.value,
                "revision": availability.availability_revision.value,
                "status": availability.status.value,
                "digest": availability.digest.value,
            },
            "adoption": {
                "scope_id": adoption.scope_id.value,
                "initial_snapshot_id": adoption.initial_snapshot_id.value,
                "registration_id": adoption.registration_id.value,
                "initial_availability_id": adoption.initial_availability_id.value,
                "digest": adoption.digest.value,
            },
        },
        "snapshot": structure_snapshot_payload(snapshot),
        "previous_snapshot_query": (
            structure_snapshot_payload(result.previous_snapshot)
            if result.previous_snapshot is not None
            else None
        ),
        "coverage": {
            "root_id": coverage.root_id.value,
            "root_digest": coverage.root.allocation_key_digest.value,
            "state_id": coverage.state_id.value,
            "state_digest": coverage.state.state_digest.value,
            "profile_ref": coverage.root.profile_ref,
            "schema_ref": coverage.root.schema_ref,
            "schema_digest": coverage.root.schema_digest.value,
            "evaluation_context_ref": (
                coverage.root.maven_evaluation_context_ref
            ),
            "evaluation_context_digest": (
                coverage.root.maven_evaluation_context_digest.value
            ),
            "canonicalization_ref": coverage.root.canonicalization_ref,
            "canonicalization_digest": coverage.root.canonicalization_digest.value,
            "completeness": (
                coverage.state.complete_member_manifest.completeness.value
            ),
            "member_manifest_digest": (
                coverage.state.complete_member_manifest.digest.value
            ),
            "evidence_locators": locators(coverage.state.evidence_references),
        },
        "entities": entities,
        "relations": relations,
        "dependencies": dependencies,
        "exclusions": exclusions,
        "deletions": {
            "removed_members": [
                _member_payload(item) for item in result.deletions.removed_members
            ],
            "replaced_members": [
                _member_payload(item) for item in result.deletions.replaced_members
            ],
            "deleted_entity_state_ids": [
                item.value for item in result.deletions.deleted_entity_state_ids
            ],
            "deleted_relation_state_ids": [
                item.value for item in result.deletions.deleted_relation_state_ids
            ],
            "deleted_literal_state_ids": [
                item.value for item in result.deletions.deleted_literal_state_ids
            ],
            "digest": result.deletions.digest.value,
        },
        "source_operations": {
            "count": len(result.source_operation_ids),
            "operation_ids": [item.value for item in result.source_operation_ids],
        },
        "maven_report": {
            "complete": evaluation.report.complete,
            "schema_ref": evaluation.report.schema_ref,
            "evaluation_context_ref": evaluation.report.evaluation_context_ref,
            "canonicalization_ref": evaluation.report.canonicalization_ref,
            "source_revision": evaluation.report.source_revision,
            "scanned_pom_locators": evaluation.report.scanned_pom_locators,
            "lines": evaluation.report.lines,
            "digest": result.build_report_digest.value,
        },
        "publication": {
            "publication_id": receipt.publication_id.value,
            "admission_id": receipt.admission_id.value,
            "admission_digest": receipt.admission_digest.value,
            "application_acceptance_digest": (
                receipt.application_acceptance_digest.value
            ),
            "published_at": receipt.published_at.isoformat(),
            "receipt_digest": receipt.digest.value,
        },
        "request_digest": result.request_digest.value,
        "source_collection_digest": result.source_collection_digest.value,
        "digest": result.digest.value,
    }
    payload["audit_lines"] = _maven_structure_audit_lines(payload)
    return payload


def _maven_structure_audit_lines(payload: dict[str, object]) -> list[str]:
    snapshot = payload["snapshot"]
    schema = payload["schema"]
    objective = payload["objective"]
    target = payload["target"]
    attempt = payload["attempt"]
    authority_result = payload["result"]
    admission = payload["admission"]
    verifier_assessment = payload["verifier_assessment"]
    artifact_use = payload["artifact_use"]
    coverage = payload["coverage"]
    lines = [
        (
            f"SNAPSHOT id={snapshot['snapshot_id']} revision={snapshot['revision']} "
            f"source_revision={payload['maven_report']['source_revision']} "
            f"manifest_digest={snapshot['manifest_digest']}"
        ),
        (
            f"SCHEMA ref={schema['definition']['schema_ref']} "
            f"digest={schema['definition']['schema_digest']} "
            f"registration={schema['registration']['registration_id']} "
            f"registration_digest={schema['registration']['digest']} "
            f"availability={schema['availability']['availability_id']} "
            f"availability_status={schema['availability']['status']} "
            f"adoption_digest={schema['adoption']['digest']} "
            f"adoption_mode={snapshot['schema_adoption_mode']}"
        ),
        (
            f"OBJECTIVE id={objective['objective_id']} digest={objective['digest']} "
            f"description={json.dumps(objective['description'], ensure_ascii=False)}"
        ),
        (
            f"TARGET id={target['target_id']} kind={target['target_kind']} "
            f"boundary={target['boundary']} receipt={target['resolution_receipt_id']} "
            f"identity={json.dumps(target['canonical_identity'], sort_keys=True, separators=(',', ':'))}"
        ),
        "REQUIREMENT binding=NONE manual_zero_question_update=true",
        (
            f"ATTEMPT id={attempt['attempt_id']} state={attempt['state']} "
            f"request_digest={attempt['request_digest']} "
            f"target_authority={attempt['target_authority_id']}"
        ),
        (
            f"RESULT id={authority_result['result_id']} "
            f"state={authority_result['state']} digest={authority_result['digest']}"
        ),
        (
            f"ADMISSION id={admission['admission_id']} outcome={admission['outcome']} "
            f"candidate_digest={admission['candidate_digest']} "
            f"closure_digest={admission['closure_digest']} "
            f"read_set_digest={admission['read_set_digest']} "
            f"provenance_digest={admission['provenance_digest']} "
            f"artifact_use_confirmation_id={admission['artifact_use_confirmation_id']} "
            f"artifact_use_confirmation_digest={admission['artifact_use_confirmation_digest']}"
        ),
        (
            f"VERIFIER_ASSESSMENT id={verifier_assessment['assessment_id']} "
            f"outcome={verifier_assessment['outcome']} "
            f"verifier={verifier_assessment['verifier_ref']} "
            f"candidate_digest={verifier_assessment['candidate_digest']} "
            f"verified_candidate_digest={verifier_assessment['verified_candidate_digest']} "
            f"evaluation_digest={verifier_assessment['candidate_evaluation_digest']} "
            f"verified_evaluation_digest={verifier_assessment['verified_evaluation_digest']} "
            f"report_digest={verifier_assessment['candidate_report_digest']} "
            f"verified_report_digest={verifier_assessment['verified_report_digest']} "
            f"batch_digest={verifier_assessment['batch_digest']} "
            f"verified_batch_digest={verifier_assessment['verified_batch_digest']} "
            f"closure_digest={verifier_assessment['closure_digest']} "
            f"verified_closure_digest={verifier_assessment['verified_closure_digest']} "
            f"read_set_digest={verifier_assessment['read_set_digest']} "
            f"verified_read_set_digest={verifier_assessment['verified_read_set_digest']} "
            f"context_digest={verifier_assessment['verification_context_digest']} "
            f"artifact_use_confirmation_id={verifier_assessment['artifact_use_confirmation_id']} "
            f"artifact_use_confirmation_digest={verifier_assessment['artifact_use_confirmation_digest']} "
            f"digest={verifier_assessment['digest']}"
        ),
        (
            f"ARTIFACT_USE confirmation={artifact_use['confirmation_id']} "
            f"purpose={artifact_use['purpose']} "
            f"package={artifact_use['package_id']} "
            f"package_digest={artifact_use['package_digest']} "
            f"closure={artifact_use['closure_id']} "
            f"closure_digest={artifact_use['closure_digest']} "
            f"protection={artifact_use['protection_id']} "
            f"protection_digest={artifact_use['protection_digest']} "
            f"candidate_digest={artifact_use['downstream_candidate_digest']} "
            f"digest={artifact_use['digest']}"
        ),
    ]
    for entity in payload["entities"]:
        lines.append(
            f"ENTITY type={entity['entity_type']} Root={entity['root_id']} "
            f"RootDigest={entity['root_digest']} State={entity['state_id']} "
            f"StateDigest={entity['state_digest']} "
            f"EvidenceLocator={','.join(entity['evidence_locators'])}"
        )
    for relation in payload["relations"]:
        lines.append(
            f"RELATION source={relation['source_root_id']} "
            f"predicate={relation['predicate']} target={relation['target_root_id']} "
            f"FactRoot={relation['fact_root_id']} "
            f"FactRootDigest={relation['fact_root_digest']} "
            f"FactState={relation['fact_state_id']} "
            f"FactStateDigest={relation['fact_state_digest']} "
            f"EvidenceLocator={','.join(relation['evidence_locators'])}"
        )
    lines.append(
        f"COVERAGE profile={coverage['profile_ref']} Root={coverage['root_id']} "
        f"RootDigest={coverage['root_digest']} State={coverage['state_id']} "
        f"StateDigest={coverage['state_digest']} "
        f"completeness={coverage['completeness']} "
        f"EvidenceLocator={','.join(coverage['evidence_locators'])}"
    )
    for dependency in payload["dependencies"]:
        lines.append(
            f"DEPENDENCY profile={dependency['profile_ref']} "
            f"consumer={dependency['consumer_gav']} "
            f"declared={dependency['declared_gav_expression']} "
            f"resolved_ga={dependency['resolved_ga']} "
            f"resolved_version={dependency['resolved_version'] or '-'} "
            f"resolved_gav={dependency['resolved_gav'] or '-'} "
            f"decision={dependency['decision']} excluded={str(dependency['excluded']).lower()} "
            f"exclusion_reason={dependency['exclusion_reason'] or '-'} "
            f"EvidenceLocator={','.join(dependency['evidence_locators'])}"
        )
    deletion_count = 0
    for disposition in ("removed_members", "replaced_members"):
        for member in payload["deletions"][disposition]:
            deletion_count += 1
            lines.append(
                f"DELETION disposition={disposition.removesuffix('_members').upper()} "
                f"kind={member['kind']} Root={member['root_id']} "
                f"State={member['state_id']} StateDigest={member['state_digest']}"
            )
    if deletion_count == 0:
        lines.append("DELETION none")
    previous = payload["previous_snapshot_query"]
    if previous is None:
        lines.append("OLD_SNAPSHOT_QUERY none")
    else:
        lines.append(
            f"OLD_SNAPSHOT_QUERY id={previous['snapshot_id']} "
            f"revision={previous['revision']} "
            f"manifest_digest={previous['manifest_digest']}"
        )
    return lines


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
