"""Closed evaluation-page projection for sealed WORLD_MODEL answer chains.

The projection deliberately accepts only the final authority chain.  It has no
Source, repository, Evidence-observation, model, or network capability, and the
file codec only creates a new canonical JSON file.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import json
import os
from pathlib import Path
import re
import stat

from software_world_model.application_services.structure_view import (
    StructureEntityArgument,
    StructureViewResult,
)
from software_world_model.application_services.world_model_answering import (
    EVALUATION_ONLY_SINK,
    OFFLINE_STRATEGY_MODE,
    WORLD_MODEL_MODE,
    OfflineStage,
    OfflineStrategyInvocation,
    WorldModelAuthorityChain,
    WorldModelDeliveryState,
    WorldModelReviewDecision,
    WorldModelReviewDimension,
)
from software_world_model.cross_cutting import (
    Digest,
    DomainError,
    ErrorCode,
    StableId,
    canonical_json_bytes,
    digest_of,
)


WORLD_MODEL_EVALUATION_PAGE_FORMAT = "WORLD_MODEL_EVALUATION_PAGE@1"

_PAGE_DIGEST_DOMAIN = "WORLD_MODEL_EVALUATION_PAGE_PAYLOAD@1"
_MAXIMUM_PAGE_BYTES = 64 * 1024 * 1024
_COMMIT_PATTERN = re.compile(r"^[0-9a-f]{40}$")
_DIGEST_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
_FORBIDDEN_PAYLOAD_KEYS = frozenset(
    {
        "artifact_bytes",
        "excerpt",
        "observation",
        "provider_input",
        "source_bytes",
    }
)
_AUTHORITY_STAGES = (
    "QUESTION",
    "REQUIREMENT_REVISION",
    "CANDIDATE_RESOLUTION_SET",
    "QUERY_PLAN",
    "QUERY_RESULT_SET",
    "ASSESSMENT",
    "ANSWER_DRAFT",
    "ANSWER_REVIEW",
    "RESPONSE_AUTHORIZATION",
    "DELIVERY",
)
_PAGE_FIELDS = {
    "answer",
    "assessment",
    "authority_chain",
    "authorization",
    "candidate_resolutions",
    "delivery",
    "environment",
    "evaluation_only",
    "execution_boundary",
    "implementation_commit",
    "limitations",
    "mode",
    "query_plan",
    "query_results",
    "read_binding",
    "request",
    "requirements",
    "review",
    "views",
}


def world_model_evaluation_page_payload(
    chain: WorldModelAuthorityChain,
    implementation_commit: str,
) -> dict[str, object]:
    """Project one valid offline authority chain into a no-payload UI value."""

    chain.require_valid()
    commit = _implementation_commit(implementation_commit)
    _require_evaluation_boundary(chain)

    # Audit the complete sealed input, not merely the fields selected below.
    # This prevents a newly added nested DTO field from silently carrying a
    # forbidden payload through an otherwise innocuous projection change.
    _require_no_forbidden_payload_keys(chain.canonical_value(), path="chain")

    page: dict[str, object] = {
        "evaluation_only": True,
        "environment": EVALUATION_ONLY_SINK,
        "mode": WORLD_MODEL_MODE,
        "implementation_commit": commit,
        "request": _request_payload(chain),
        "authority_chain": _authority_chain_payload(chain),
        "read_binding": _read_binding_payload(chain),
        "requirements": _requirements_payload(chain),
        "candidate_resolutions": _candidate_resolutions_payload(chain),
        "query_plan": _query_plan_payload(chain),
        "query_results": _query_results_payload(chain),
        "views": _views_payload(chain),
        "assessment": _json_value(chain.assessment.canonical_value()),
        "answer": _answer_payload(chain),
        "review": _review_payload(chain),
        "authorization": _json_value(chain.authorization.canonical_value()),
        "delivery": _json_value(chain.delivery.canonical_value()),
        "execution_boundary": {
            "provider_call_count": chain.provider_call_count,
            "network_operation_count": chain.network_operation_count,
            "external_dispatch_allowed": False,
            "provider_route": None,
            "source_access_allowed": False,
            "evidence_payload_access_allowed": False,
        },
        "limitations": _limitations_payload(chain),
    }
    _require_no_forbidden_payload_keys(page, path="page")
    _validate_page(page)
    return page


def world_model_evaluation_page_envelope(
    chain: WorldModelAuthorityChain,
    implementation_commit: str,
) -> dict[str, object]:
    """Return the strict, digest-bound JSON document for an evaluation page."""

    page = world_model_evaluation_page_payload(chain, implementation_commit)
    page_digest = digest_of([_PAGE_DIGEST_DOMAIN, page])
    return {
        "format_ref": WORLD_MODEL_EVALUATION_PAGE_FORMAT,
        "page": page,
        "page_digest": page_digest.value,
    }


def write_world_model_evaluation_page(
    path: str | os.PathLike[str],
    chain: WorldModelAuthorityChain,
    implementation_commit: str,
) -> Digest:
    """Create one immutable canonical page file; existing paths are rejected."""

    destination = _canonical_absolute_path(path, "evaluation page")
    _require_existing_real_directory(destination.parent, "evaluation page parent")
    envelope = world_model_evaluation_page_envelope(chain, implementation_commit)
    encoded = canonical_json_bytes(envelope)
    if len(encoded) > _MAXIMUM_PAGE_BYTES:
        raise _invalid(
            "WORLD_MODEL_EVALUATION_PAGE_SIZE_LIMIT",
            "world-model evaluation page exceeds the file size limit",
        )
    _write_new_regular_file(destination, encoded)
    return Digest(str(envelope["page_digest"]))


def read_world_model_evaluation_page(
    path: str | os.PathLike[str],
    *,
    expected_implementation_commit: str,
    expected_page_digest: str,
) -> dict[str, object]:
    """Read and verify a canonical evaluation-page envelope.

    Both expected values are mandatory out-of-band provenance anchors.  Public
    hashes inside the file can prove structural consistency, but only a caller-
    frozen PAGE digest can reject a fully recomputed forged document.
    """

    source = _canonical_absolute_path(path, "evaluation page")
    encoded = _read_regular_file(source)
    value = _decode_canonical_json(encoded)
    envelope = _mapping(value, "evaluation page envelope")
    _exact_keys(
        envelope,
        {"format_ref", "page", "page_digest"},
        "evaluation page envelope",
    )
    if envelope["format_ref"] != WORLD_MODEL_EVALUATION_PAGE_FORMAT:
        raise _invalid(
            "WORLD_MODEL_EVALUATION_PAGE_FORMAT_INVALID",
            "world-model evaluation page format is unsupported",
        )
    page = _mapping(envelope["page"], "evaluation page")
    page_digest = _digest_text(envelope["page_digest"], "evaluation page digest")
    trusted_page_digest = _digest_text(
        expected_page_digest, "expected evaluation page digest"
    )
    if page_digest != trusted_page_digest:
        raise _inconsistent(
            "WORLD_MODEL_EVALUATION_EXPECTED_PAGE_DIGEST_MISMATCH",
            "evaluation page does not match the trusted PAGE digest",
        )
    expected_digest = digest_of([_PAGE_DIGEST_DOMAIN, page])
    if page_digest != expected_digest.value:
        raise _inconsistent(
            "WORLD_MODEL_EVALUATION_PAGE_DIGEST_MISMATCH",
            "world-model evaluation page digest does not match its payload",
        )
    _require_no_forbidden_payload_keys(page, path="page")
    _validate_page(page)
    expected_commit = _implementation_commit(expected_implementation_commit)
    if page["implementation_commit"] != expected_commit:
        raise _inconsistent(
            "WORLD_MODEL_EVALUATION_IMPLEMENTATION_COMMIT_MISMATCH",
            "evaluation page does not bind the expected implementation commit",
        )
    return dict(page)


def _request_payload(chain: WorldModelAuthorityChain) -> dict[str, object]:
    question = chain.question
    return {
        "question_id": question.question_id.value,
        "question_digest": question.digest.value,
        "revision": question.revision,
        "request_ref": question.request_ref,
        "mode": question.mode,
        "original_question": question.original_question,
        "response_language": question.response_language,
        "classification": question.classification,
        "permission_digest": question.permission_digest.value,
        "use_epoch": question.use_epoch,
        "resource_limits": _json_value(
            question.resource_limits.canonical_value()
        ),
        "resource_limits_digest": question.resource_limits.digest.value,
        "explicit_entity_refs": [
            _json_value(item.canonical_value())
            for item in question.explicit_entity_refs
        ],
        "external_dispatch_allowed": question.external_dispatch_allowed,
        "model_route": question.model_route,
    }


def _authority_chain_payload(chain: WorldModelAuthorityChain) -> dict[str, object]:
    records = (
        ("QUESTION", chain.question.question_id, chain.question.digest),
        (
            "REQUIREMENT_REVISION",
            chain.requirement.requirement_id,
            chain.requirement.digest,
        ),
        (
            "CANDIDATE_RESOLUTION_SET",
            chain.resolutions.resolution_set_id,
            chain.resolutions.digest,
        ),
        ("QUERY_PLAN", chain.plan.plan_id, chain.plan.digest),
        (
            "QUERY_RESULT_SET",
            chain.result_set.result_set_id,
            chain.result_set.digest,
        ),
        ("ASSESSMENT", chain.assessment.assessment_id, chain.assessment.digest),
        ("ANSWER_DRAFT", chain.draft.draft_id, chain.draft.digest),
        ("ANSWER_REVIEW", chain.review.review_id, chain.review.digest),
        (
            "RESPONSE_AUTHORIZATION",
            chain.authorization.authorization_id,
            chain.authorization.digest,
        ),
        ("DELIVERY", chain.delivery.delivery_id, chain.delivery.digest),
    )
    return {
        "stages": [
            {
                "stage": stage,
                "authority_id": identifier.value,
                "authority_digest": digest.value,
            }
            for stage, identifier, digest in records
        ],
        "chain_digest": chain.digest.value,
    }


def _read_binding_payload(chain: WorldModelAuthorityChain) -> dict[str, object]:
    authority = chain.question.read_authority
    snapshots = [
        {
            "snapshot_id": snapshot_id.value,
            "snapshot_bundle_digest": bundle_digest.value,
            "source_revision": source_revision,
        }
        for snapshot_id, bundle_digest, source_revision in zip(
            authority.snapshot_ids,
            authority.snapshot_bundle_digests,
            authority.source_revisions,
            strict=True,
        )
    ]
    return {
        "scope_id": authority.scope_id.value,
        "session_id": authority.session_id.value,
        "session_digest": authority.session_digest.value,
        "read_set_digest": authority.read_set_digest.value,
        "ordered_bundle_digest": authority.ordered_bundle_digest.value,
        "snapshots": snapshots,
        "profile_refs": list(authority.profile_refs),
        "read_authority_digest": authority.digest.value,
    }


def _requirements_payload(chain: WorldModelAuthorityChain) -> dict[str, object]:
    requirement = chain.requirement
    return {
        "requirement_id": requirement.requirement_id.value,
        "requirement_digest": requirement.digest.value,
        "revision": requirement.revision,
        "question_id": requirement.question_id.value,
        "question_digest": requirement.question_digest.value,
        "original_question": requirement.original_question,
        "response_language": requirement.response_language,
        "needs": [
            _json_value(item.canonical_value()) for item in requirement.needs
        ],
        "joint_constraints": [
            _json_value(item.canonical_value())
            for item in requirement.joint_constraints
        ],
        "planning_invocation": _invocation_payload(
            requirement.planning_invocation
        ),
        "fidelity_review_invocation": _invocation_payload(
            requirement.fidelity_review_invocation
        ),
        "fidelity_decision": requirement.fidelity_decision.value,
        "fidelity_accepted_need_ids": list(
            requirement.fidelity_accepted_need_ids
        ),
        "fidelity_accepted_constraint_ids": list(
            requirement.fidelity_accepted_constraint_ids
        ),
        "fidelity_original_question_preserved": (
            requirement.fidelity_original_question_preserved
        ),
        "fidelity_all_material_questions_covered": (
            requirement.fidelity_all_material_questions_covered
        ),
        "fidelity_findings": list(requirement.fidelity_findings),
        "read_authority_digest": requirement.read_authority.digest.value,
    }


def _candidate_resolutions_payload(
    chain: WorldModelAuthorityChain,
) -> dict[str, object]:
    resolutions = chain.resolutions
    return {
        "resolution_set_id": resolutions.resolution_set_id.value,
        "resolution_set_digest": resolutions.digest.value,
        "question_id": resolutions.question_id.value,
        "requirement_id": resolutions.requirement_id.value,
        "requirement_digest": resolutions.requirement_digest.value,
        "proposal_digest": resolutions.proposal_digest.value,
        "planning_invocation": _invocation_payload(
            resolutions.planning_invocation
        ),
        "resolutions": [
            {
                "resolution_id": item.resolution_id.value,
                "resolution_digest": item.digest.value,
                "selector": _json_value(item.selector.canonical_value()),
                "status": item.status.value,
                "candidate_view_result_id": (
                    item.candidate_result.result_id.value
                    if item.candidate_result is not None
                    else None
                ),
                "candidate_view_result_digest": (
                    item.candidate_result.digest.value
                    if item.candidate_result is not None
                    else None
                ),
                "argument": _entity_argument_payload(item.argument),
                "limitations": list(item.limitations),
                "read_authority_digest": item.read_authority_digest.value,
            }
            for item in resolutions.resolutions
        ],
        "read_authority_digest": resolutions.read_authority.digest.value,
    }


def _query_plan_payload(chain: WorldModelAuthorityChain) -> dict[str, object]:
    plan = chain.plan
    return {
        "plan_id": plan.plan_id.value,
        "plan_digest": plan.digest.value,
        "question_id": plan.question_id.value,
        "requirement_id": plan.requirement_id.value,
        "requirement_digest": plan.requirement_digest.value,
        "resolution_set_id": plan.resolution_set_id.value,
        "resolution_set_digest": plan.resolution_set_digest.value,
        "planning_invocation": _invocation_payload(plan.planning_invocation),
        "capability_registry_digest": plan.capability_registry_digest.value,
        "steps": [
            {
                "step_id": step.step_id,
                "step_digest": step.digest.value,
                "need_ids": list(step.need_ids),
                "operation": step.operation.value,
                "arguments": _json_value(step.arguments),
                "parameters": _json_value(step.parameters),
                "constraint_ids": list(step.constraint_ids),
                "state": step.state.value,
                "limitation_code": step.limitation_code,
            }
            for step in plan.steps
        ],
        "explicit_gaps": [
            _json_value(item.canonical_value()) for item in plan.explicit_gaps
        ],
        "read_authority_digest": plan.read_authority.digest.value,
    }


def _query_results_payload(chain: WorldModelAuthorityChain) -> dict[str, object]:
    result_set = chain.result_set
    return {
        "result_set_id": result_set.result_set_id.value,
        "result_set_digest": result_set.digest.value,
        "question_id": result_set.question_id.value,
        "requirement_id": result_set.requirement_id.value,
        "plan_id": result_set.plan_id.value,
        "plan_digest": result_set.plan_digest.value,
        "step_results": [
            {
                "step_result_id": item.step_result_id.value,
                "step_result_digest": item.digest.value,
                "step_id": item.step_id,
                "step_digest": item.step_digest.value,
                "view_result_id": item.view_result.result_id.value,
                "view_result_digest": item.view_result.digest.value,
            }
            for item in result_set.step_results
        ],
        "read_authority_digest": result_set.read_authority.digest.value,
        "support_map_digest": result_set.support_map_digest.value,
        "evidence_allowlist_digest": result_set.evidence_allowlist_digest.value,
    }


def _views_payload(chain: WorldModelAuthorityChain) -> dict[str, object]:
    return {
        "candidate_resolution_views": [
            {
                "resolution_id": resolution.resolution_id.value,
                "view": _view_result_payload(resolution.candidate_result),
            }
            for resolution in chain.resolutions.resolutions
            if resolution.candidate_result is not None
        ],
        "query_result_views": [
            {
                "step_result_id": result.step_result_id.value,
                "view": _view_result_payload(result.view_result),
            }
            for result in chain.result_set.step_results
        ],
    }


def _view_result_payload(result: StructureViewResult) -> dict[str, object]:
    result.require_valid()
    evidence_metadata = result.citation_evidence_metadata()
    return {
        "result_id": result.result_id.value,
        "result_digest": result.digest.value,
        "operation": result.operation.value,
        "read_binding": {
            "session_id": result.session_id.value,
            "session_digest": result.session_digest.value,
            "read_set_digest": result.read_set_digest.value,
            "ordered_bundle_digest": result.ordered_bundle_digest.value,
            "snapshots": [
                {
                    "snapshot_id": snapshot_id.value,
                    "snapshot_bundle_digest": bundle_digest.value,
                }
                for snapshot_id, bundle_digest in zip(
                    result.snapshot_ids,
                    result.snapshot_bundle_digests,
                    strict=True,
                )
            ],
        },
        "profile_refs": list(result.profile_refs),
        "relation_modalities": list(result.relation_modalities),
        "coverage": _json_value(result.coverage),
        "completeness": result.completeness.value,
        "truncated": result.truncated,
        "limitations": list(result.limitations),
        "result_payload": _json_value(result.payload),
        "support": [
            {
                "support_digest": support.digest.value,
                "snapshot_id": support.snapshot_id.value,
                "member_kind": support.member_kind,
                "root_id": support.root_id.value,
                "state_id": support.state_id.value,
                "state_digest": support.state_digest.value,
                "evidence_metadata_ids": [
                    item.evidence_id.value for item in support.evidence
                ],
            }
            for support in result.support_map
        ],
        "evidence_metadata_ids": [
            item.evidence_id.value for item in evidence_metadata
        ],
        "evidence_metadata": [
            {
                "evidence_id": item.evidence_id.value,
                "evidence_digest": item.digest.value,
                "artifact_id": item.artifact_id.value,
                "source_context_id": item.source_context_id.value,
                "byte_start": item.byte_start,
                "byte_end": item.byte_end,
                "locator": item.locator,
                "excerpt_digest": item.excerpt_digest.value,
                "artifact_content_digest": item.artifact_content_digest.value,
            }
            for item in evidence_metadata
        ],
    }


def _answer_payload(chain: WorldModelAuthorityChain) -> dict[str, object]:
    draft = chain.draft
    return {
        "draft_id": draft.draft_id.value,
        "draft_digest": draft.digest.value,
        "question_id": draft.question_id.value,
        "requirement_id": draft.requirement_id.value,
        "plan_id": draft.plan_id.value,
        "result_set_id": draft.result_set_id.value,
        "assessment_id": draft.assessment_id.value,
        "body": draft.body,
        "body_digest": draft.body_digest.value,
        "claims": [
            _json_value(claim.canonical_value()) for claim in draft.claims
        ],
        "generation_invocation": _invocation_payload(
            draft.generation_invocation
        ),
        "read_authority_digest": draft.read_authority.digest.value,
    }


def _review_payload(chain: WorldModelAuthorityChain) -> dict[str, object]:
    review = chain.review
    generation = chain.draft.generation_invocation
    reviewer = review.review_invocation
    return {
        "review_id": review.review_id.value,
        "review_digest": review.digest.value,
        "question_id": review.question_id.value,
        "draft_id": review.draft_id.value,
        "draft_digest": review.draft_digest.value,
        "decision": review.decision.value,
        "dimensions": [
            _json_value(item.canonical_value()) for item in review.dimensions
        ],
        "checked_need_ids": list(review.checked_need_ids),
        "checked_constraint_ids": list(review.checked_constraint_ids),
        "checked_step_result_ids": [
            item.value for item in review.checked_step_result_ids
        ],
        "finding_codes": list(review.finding_codes),
        "findings": list(review.findings),
        "invocation_separation": {
            "generation": _invocation_payload(generation),
            "review": _invocation_payload(reviewer),
            "invocations_separate": generation.invocation_id
            != reviewer.invocation_id,
        },
        "generation_invocation_id": review.generation_invocation_id.value,
        "read_authority_digest": review.read_authority.digest.value,
    }


def _invocation_payload(
    invocation: OfflineStrategyInvocation,
) -> dict[str, object]:
    invocation.require_valid()
    return _json_value(invocation.canonical_value())


def _entity_argument_payload(
    argument: StructureEntityArgument | None,
) -> dict[str, object] | None:
    if argument is None:
        return None
    return {
        "origin": argument.origin.value,
        "session_id": argument.session_id.value,
        "read_set_digest": argument.read_set_digest.value,
        "ordered_bundle_digest": argument.ordered_bundle_digest.value,
        "snapshot_id": argument.snapshot_id.value,
        "snapshot_bundle_digest": argument.snapshot_bundle_digest.value,
        "entity_root_id": argument.entity_root_id.value,
        "entity_state_id": argument.entity_state_id.value,
        "candidate_result_id": (
            argument.candidate_result_id.value
            if argument.candidate_result_id is not None
            else None
        ),
        "candidate_result_digest": (
            argument.candidate_result_digest.value
            if argument.candidate_result_digest is not None
            else None
        ),
        "argument_digest": argument.digest.value,
    }


def _limitations_payload(chain: WorldModelAuthorityChain) -> list[dict[str, object]]:
    entries: dict[tuple[str, str, str | None], dict[str, object]] = {}

    def add(source: str, code: str, detail: str | None = None) -> None:
        entries[(source, code, detail)] = {
            "source": source,
            "code": code,
            "detail": detail,
        }

    for resolution in chain.resolutions.resolutions:
        for limitation in resolution.limitations:
            add(f"resolution:{resolution.resolution_id.value}", limitation)
        if resolution.candidate_result is not None:
            for limitation in resolution.candidate_result.limitations:
                add(
                    f"view:{resolution.candidate_result.result_id.value}",
                    limitation,
                )
    for result in chain.result_set.step_results:
        for limitation in result.view_result.limitations:
            add(f"view:{result.view_result.result_id.value}", limitation)
    for gap in chain.plan.explicit_gaps:
        add(f"need:{gap.need_id}", gap.reason_code.value, gap.detail)
    for need in chain.assessment.needs:
        for limitation in need.limitations:
            add(f"need:{need.need_id}", limitation)
        if need.gap_code is not None:
            add(f"need:{need.need_id}", need.gap_code, need.gap_detail)
    return [entries[key] for key in sorted(entries)]


def _require_evaluation_boundary(chain: WorldModelAuthorityChain) -> None:
    question = chain.question
    authorization = chain.authorization
    delivery = chain.delivery
    receipt = delivery.receipt
    generation = chain.draft.generation_invocation
    reviewer = chain.review.review_invocation
    if (
        question.mode != WORLD_MODEL_MODE
        or question.external_dispatch_allowed
        or question.model_route is not None
        or authorization.sink_id != EVALUATION_ONLY_SINK
        or delivery.sink_id != EVALUATION_ONLY_SINK
        or delivery.state is not WorldModelDeliveryState.DELIVERED
        or chain.review.decision is not WorldModelReviewDecision.APPROVE
        or receipt is None
        or not receipt.accepted
        or receipt.sink_id != delivery.sink_id
        or receipt.delivery_key != delivery.delivery_key
        or receipt.body_digest != delivery.body_digest
        or receipt.projection_digest != delivery.projection_digest
    ):
        raise _invalid(
            "WORLD_MODEL_EVALUATION_BOUNDARY_INVALID",
            "evaluation page requires an approved EVALUATION_ONLY delivery",
        )
    generation.require_valid()
    reviewer.require_valid()
    if (
        generation.stage is not OfflineStage.ANSWER_DRAFTING
        or reviewer.stage is not OfflineStage.ANSWER_REVIEW
        or generation.invocation_id == reviewer.invocation_id
        or generation.digest == reviewer.digest
        or chain.review.generation_invocation_id != generation.invocation_id
    ):
        raise _invalid(
            "WORLD_MODEL_REVIEW_INVOCATION_NOT_SEPARATE",
            "answer generation and review require separate offline invocations",
        )


def _validate_page(page: Mapping[str, object]) -> None:
    _exact_keys(page, _PAGE_FIELDS, "evaluation page")
    if (
        page["evaluation_only"] is not True
        or page["environment"] != EVALUATION_ONLY_SINK
        or page["mode"] != WORLD_MODEL_MODE
    ):
        raise _invalid(
            "WORLD_MODEL_EVALUATION_MARKER_INVALID",
            "evaluation page must retain its EVALUATION_ONLY WORLD_MODEL marker",
        )
    _implementation_commit(page["implementation_commit"])

    authority_chain = _mapping(page["authority_chain"], "authority chain")
    _exact_keys(
        authority_chain,
        {"stages", "chain_digest"},
        "authority chain",
    )
    _digest_text(authority_chain["chain_digest"], "authority chain digest")
    stages = authority_chain["stages"]
    if not isinstance(stages, list) or len(stages) != len(_AUTHORITY_STAGES):
        raise _invalid(
            "WORLD_MODEL_EVALUATION_AUTHORITY_STAGES_INVALID",
            "evaluation page must contain the complete ordered authority chain",
        )
    for expected_stage, stage_value in zip(_AUTHORITY_STAGES, stages, strict=True):
        stage = _mapping(stage_value, f"authority stage {expected_stage}")
        _exact_keys(
            stage,
            {"stage", "authority_id", "authority_digest"},
            f"authority stage {expected_stage}",
        )
        if stage["stage"] != expected_stage:
            raise _invalid(
                "WORLD_MODEL_EVALUATION_AUTHORITY_ORDER_INVALID",
                "evaluation page authority stages are missing or reordered",
            )
        _stable_id_text(stage["authority_id"], f"{expected_stage} authority ID")
        _digest_text(
            stage["authority_digest"], f"{expected_stage} authority digest"
        )

    _validate_reconstructed_authority_chain(page, stages)

    request = _mapping(page["request"], "evaluation request")
    if (
        request.get("mode") != WORLD_MODEL_MODE
        or request.get("external_dispatch_allowed") is not False
        or request.get("model_route") is not None
        or request.get("question_id") != stages[0]["authority_id"]
        or request.get("question_digest") != stages[0]["authority_digest"]
    ):
        raise _invalid(
            "WORLD_MODEL_EVALUATION_REQUEST_INVALID",
            "evaluation request is not the exact offline WORLD_MODEL authority",
        )

    read_binding = _mapping(page["read_binding"], "read binding")
    for key in (
        "session_digest",
        "read_set_digest",
        "ordered_bundle_digest",
        "read_authority_digest",
    ):
        _digest_text(read_binding.get(key), f"read binding {key}")
    _stable_id_text(read_binding.get("scope_id"), "read binding Scope ID")
    _stable_id_text(read_binding.get("session_id"), "read binding Session ID")
    snapshots = read_binding.get("snapshots")
    if not isinstance(snapshots, list) or not snapshots:
        raise _invalid(
            "WORLD_MODEL_EVALUATION_READ_SET_EMPTY",
            "evaluation page requires a non-empty exact Snapshot Read Set",
        )

    review = _mapping(page["review"], "answer review")
    separation = _mapping(
        review.get("invocation_separation"), "review invocation separation"
    )
    generation = _mapping(separation.get("generation"), "generation invocation")
    reviewer = _mapping(separation.get("review"), "review invocation")
    if (
        review.get("decision") != WorldModelReviewDecision.APPROVE.value
        or separation.get("invocations_separate") is not True
        or generation.get("invocation_id") == reviewer.get("invocation_id")
        or generation.get("digest") == reviewer.get("digest")
        or generation.get("stage") != OfflineStage.ANSWER_DRAFTING.value
        or reviewer.get("stage") != OfflineStage.ANSWER_REVIEW.value
    ):
        raise _invalid(
            "WORLD_MODEL_EVALUATION_REVIEW_SEPARATION_INVALID",
            "evaluation page does not prove separate generation and review",
        )

    authorization = _mapping(page["authorization"], "authorization")
    delivery = _mapping(page["delivery"], "delivery")
    if (
        authorization.get("sink_id") != EVALUATION_ONLY_SINK
        or delivery.get("sink_id") != EVALUATION_ONLY_SINK
        or delivery.get("state") != WorldModelDeliveryState.DELIVERED.value
    ):
        raise _invalid(
            "WORLD_MODEL_EVALUATION_DELIVERY_INVALID",
            "evaluation page delivery is not EVALUATION_ONLY and complete",
        )

    boundary = _mapping(page["execution_boundary"], "execution boundary")
    _exact_keys(
        boundary,
        {
            "provider_call_count",
            "network_operation_count",
            "external_dispatch_allowed",
            "provider_route",
            "source_access_allowed",
            "evidence_payload_access_allowed",
        },
        "execution boundary",
    )
    if (
        type(boundary.get("provider_call_count")) is not int
        or boundary.get("provider_call_count") != 0
        or type(boundary.get("network_operation_count")) is not int
        or boundary.get("network_operation_count") != 0
        or boundary.get("external_dispatch_allowed") is not False
        or boundary.get("provider_route") is not None
        or boundary.get("source_access_allowed") is not False
        or boundary.get("evidence_payload_access_allowed") is not False
    ):
        raise _invalid(
            "WORLD_MODEL_EVALUATION_EXECUTION_BOUNDARY_INVALID",
            "evaluation page does not prove its offline no-payload boundary",
        )


def _validate_reconstructed_authority_chain(
    page: Mapping[str, object], stages: Sequence[object]
) -> None:
    """Rebuild every sealed record from the displayed page and verify it.

    The envelope digest detects accidental corruption, but it is deliberately
    unkeyed and therefore cannot be treated as authority.  The reader instead
    rebuilds the ten records, verifies their native ID/digest domains, and then
    replays the cross-links through Authorization, Delivery, and the final chain.
    """

    try:
        read_authority = _reconstruct_read_authority(page["read_binding"])
        question = _reconstruct_question(page["request"], read_authority)
        requirement = _reconstruct_requirement(
            page["requirements"], read_authority
        )
        candidate_views, query_views = _reconstruct_views(
            page["views"], read_authority
        )
        resolutions = _reconstruct_resolutions(
            page["candidate_resolutions"],
            read_authority,
            candidate_views,
        )
        plan = _reconstruct_plan(page["query_plan"], read_authority)
        result_set = _reconstruct_result_set(
            page["query_results"], read_authority, query_views
        )
        assessment = _reconstruct_assessment(
            page["assessment"], read_authority
        )
        draft = _reconstruct_draft(page["answer"], read_authority)
        review = _reconstruct_review(page["review"], read_authority, draft)
        authorization = _reconstruct_authorization(
            page["authorization"], read_authority
        )
        delivery = _reconstruct_delivery(page["delivery"])
        records = (
            question,
            requirement,
            resolutions,
            plan,
            result_set,
            assessment,
            draft,
            review,
            authorization,
            delivery,
        )
        _require_stage_records(stages, records)
        _require_authority_cross_links(
            page,
            records,
            read_authority=read_authority,
        )
    except DomainError:
        raise
    except (KeyError, TypeError, ValueError) as exc:
        raise _invalid(
            "WORLD_MODEL_EVALUATION_AUTHORITY_RECORD_INVALID",
            "evaluation page authority records cannot be reconstructed",
        ) from exc


def _reconstruct_read_authority(value: object) -> dict[str, object]:
    binding = _mapping(value, "read binding")
    _exact_keys(
        binding,
        {
            "scope_id",
            "session_id",
            "session_digest",
            "read_set_digest",
            "ordered_bundle_digest",
            "snapshots",
            "profile_refs",
            "read_authority_digest",
        },
        "read binding",
    )
    snapshots = _array(binding["snapshots"], "read binding snapshots")
    if not snapshots:
        raise _invalid(
            "WORLD_MODEL_EVALUATION_READ_SET_EMPTY",
            "evaluation page requires a non-empty exact Snapshot Read Set",
        )
    snapshot_ids: list[object] = []
    bundle_digests: list[object] = []
    source_revisions: list[object] = []
    for index, item in enumerate(snapshots):
        snapshot = _mapping(item, f"read binding snapshot {index}")
        _exact_keys(
            snapshot,
            {"snapshot_id", "snapshot_bundle_digest", "source_revision"},
            f"read binding snapshot {index}",
        )
        _stable_id_text(snapshot["snapshot_id"], "Snapshot ID")
        _digest_text(snapshot["snapshot_bundle_digest"], "Snapshot bundle digest")
        snapshot_ids.append(snapshot["snapshot_id"])
        bundle_digests.append(snapshot["snapshot_bundle_digest"])
        source_revisions.append(snapshot["source_revision"])
    record = {
        "scope_id": binding["scope_id"],
        "session_id": binding["session_id"],
        "session_digest": binding["session_digest"],
        "read_set_digest": binding["read_set_digest"],
        "ordered_bundle_digest": binding["ordered_bundle_digest"],
        "snapshot_ids": snapshot_ids,
        "snapshot_bundle_digests": bundle_digests,
        "source_revisions": source_revisions,
        "profile_refs": _array(binding["profile_refs"], "Profile refs"),
        "digest": binding["read_authority_digest"],
    }
    _stable_id_text(record["scope_id"], "read authority Scope ID")
    _stable_id_text(record["session_id"], "read authority Session ID")
    for key in (
        "session_digest",
        "read_set_digest",
        "ordered_bundle_digest",
        "digest",
    ):
        _digest_text(record[key], f"read authority {key}")
    _require_digest_mapping(
        record,
        "WORLD_MODEL_READ_AUTHORITY@1",
        "read authority",
    )
    return record


def _reconstruct_question(
    value: object, read_authority: Mapping[str, object]
) -> dict[str, object]:
    request = _mapping(value, "evaluation request")
    _exact_keys(
        request,
        {
            "question_id",
            "question_digest",
            "revision",
            "request_ref",
            "mode",
            "original_question",
            "response_language",
            "classification",
            "permission_digest",
            "use_epoch",
            "resource_limits",
            "resource_limits_digest",
            "explicit_entity_refs",
            "external_dispatch_allowed",
            "model_route",
        },
        "evaluation request",
    )
    limits = _mapping(request["resource_limits"], "resource limits")
    if request["resource_limits_digest"] != digest_of(
        ["WORLD_MODEL_RESOURCE_LIMITS@1", limits]
    ).value:
        raise _inconsistent(
            "WORLD_MODEL_EVALUATION_RESOURCE_LIMIT_DIGEST_MISMATCH",
            "evaluation request resource limits do not verify",
        )
    explicit_refs: list[object] = []
    for index, item in enumerate(
        _array(request["explicit_entity_refs"], "explicit Entity refs")
    ):
        reference = _mapping(item, f"explicit Entity ref {index}")
        _exact_keys(
            reference,
            {"snapshot_id", "entity_root_id", "entity_state_id", "digest"},
            f"explicit Entity ref {index}",
        )
        _require_digest_mapping(
            reference,
            "WORLD_MODEL_EXPLICIT_ENTITY_REF@1",
            f"explicit Entity ref {index}",
        )
        explicit_refs.append(dict(reference))
    record = {
        "question_id": request["question_id"],
        "revision": request["revision"],
        "request_ref": request["request_ref"],
        "mode": request["mode"],
        "original_question": request["original_question"],
        "response_language": request["response_language"],
        "classification": request["classification"],
        "permission_digest": request["permission_digest"],
        "use_epoch": request["use_epoch"],
        "resource_limits": dict(limits),
        "resource_limits_digest": request["resource_limits_digest"],
        "read_authority": dict(read_authority),
        "explicit_entity_refs": explicit_refs,
        "external_dispatch_allowed": request["external_dispatch_allowed"],
        "model_route": request["model_route"],
        "digest": request["question_digest"],
    }
    _require_stable_mapping(
        record,
        id_field="question_id",
        stable_kind="world_model_question",
        id_domain="WORLD_MODEL_QUESTION_ID@1",
        digest_domain="WORLD_MODEL_QUESTION@1",
        label="Question",
    )
    return record


def _reconstruct_requirement(
    value: object, read_authority: Mapping[str, object]
) -> dict[str, object]:
    projected = _mapping(value, "Requirement Revision")
    _exact_keys(
        projected,
        {
            "requirement_id",
            "requirement_digest",
            "revision",
            "question_id",
            "question_digest",
            "original_question",
            "response_language",
            "needs",
            "joint_constraints",
            "planning_invocation",
            "fidelity_review_invocation",
            "fidelity_decision",
            "fidelity_accepted_need_ids",
            "fidelity_accepted_constraint_ids",
            "fidelity_original_question_preserved",
            "fidelity_all_material_questions_covered",
            "fidelity_findings",
            "read_authority_digest",
        },
        "Requirement Revision",
    )
    needs = _array(projected["needs"], "Requirement Needs")
    for index, item in enumerate(needs):
        _exact_keys(
            _mapping(item, f"Need {index}"),
            {"need_id", "question"},
            f"Need {index}",
        )
    constraints = _array(
        projected["joint_constraints"], "Requirement joint constraints"
    )
    for index, item in enumerate(constraints):
        _exact_keys(
            _mapping(item, f"joint constraint {index}"),
            {
                "constraint_id",
                "need_ids",
                "kind",
                "description",
                "base_snapshot_id",
                "target_snapshot_id",
            },
            f"joint constraint {index}",
        )
    planning = _reconstruct_invocation(
        projected["planning_invocation"], "Requirement planning invocation"
    )
    fidelity = _reconstruct_invocation(
        projected["fidelity_review_invocation"],
        "Requirement fidelity invocation",
    )
    record = {
        "requirement_id": projected["requirement_id"],
        "revision": projected["revision"],
        "question_id": projected["question_id"],
        "question_digest": projected["question_digest"],
        "original_question": projected["original_question"],
        "response_language": projected["response_language"],
        "needs": needs,
        "joint_constraints": constraints,
        "planning_invocation": planning,
        "fidelity_review_invocation": fidelity,
        "fidelity_decision": projected["fidelity_decision"],
        "fidelity_accepted_need_ids": _array(
            projected["fidelity_accepted_need_ids"], "accepted Need IDs"
        ),
        "fidelity_accepted_constraint_ids": _array(
            projected["fidelity_accepted_constraint_ids"],
            "accepted constraint IDs",
        ),
        "fidelity_original_question_preserved": projected[
            "fidelity_original_question_preserved"
        ],
        "fidelity_all_material_questions_covered": projected[
            "fidelity_all_material_questions_covered"
        ],
        "fidelity_findings": _array(
            projected["fidelity_findings"], "Requirement fidelity findings"
        ),
        "read_authority": dict(read_authority),
        "digest": projected["requirement_digest"],
    }
    if projected["read_authority_digest"] != read_authority["digest"]:
        raise _authority_mismatch("Requirement Read Set")
    _require_stable_mapping(
        record,
        id_field="requirement_id",
        stable_kind="world_model_requirement",
        id_domain="WORLD_MODEL_REQUIREMENT_ID@1",
        digest_domain="WORLD_MODEL_REQUIREMENT@1",
        label="Requirement Revision",
    )
    return record


def _reconstruct_views(
    value: object, read_authority: Mapping[str, object]
) -> tuple[dict[object, dict[str, object]], dict[object, dict[str, object]]]:
    projected = _mapping(value, "Structure views")
    _exact_keys(
        projected,
        {"candidate_resolution_views", "query_result_views"},
        "Structure views",
    )
    candidate_views: dict[object, dict[str, object]] = {}
    for index, item in enumerate(
        _array(projected["candidate_resolution_views"], "candidate views")
    ):
        entry = _mapping(item, f"candidate view {index}")
        _exact_keys(entry, {"resolution_id", "view"}, f"candidate view {index}")
        key = entry["resolution_id"]
        if key in candidate_views:
            raise _authority_mismatch("duplicate candidate view")
        candidate_views[key] = _reconstruct_view_result(
            entry["view"], read_authority, f"candidate view {index}"
        )
    query_views: dict[object, dict[str, object]] = {}
    for index, item in enumerate(
        _array(projected["query_result_views"], "query result views")
    ):
        entry = _mapping(item, f"query result view {index}")
        _exact_keys(
            entry, {"step_result_id", "view"}, f"query result view {index}"
        )
        key = entry["step_result_id"]
        if key in query_views:
            raise _authority_mismatch("duplicate query result view")
        query_views[key] = _reconstruct_view_result(
            entry["view"], read_authority, f"query result view {index}"
        )
    return candidate_views, query_views


def _reconstruct_view_result(
    value: object,
    read_authority: Mapping[str, object],
    label: str,
) -> dict[str, object]:
    projected = _mapping(value, label)
    _exact_keys(
        projected,
        {
            "result_id",
            "result_digest",
            "operation",
            "read_binding",
            "profile_refs",
            "relation_modalities",
            "coverage",
            "completeness",
            "truncated",
            "limitations",
            "result_payload",
            "support",
            "evidence_metadata_ids",
            "evidence_metadata",
        },
        label,
    )
    binding = _mapping(projected["read_binding"], f"{label} read binding")
    _exact_keys(
        binding,
        {
            "session_id",
            "session_digest",
            "read_set_digest",
            "ordered_bundle_digest",
            "snapshots",
        },
        f"{label} read binding",
    )
    snapshots = _array(binding["snapshots"], f"{label} snapshots")
    snapshot_ids: list[object] = []
    bundle_digests: list[object] = []
    for index, item in enumerate(snapshots):
        snapshot = _mapping(item, f"{label} snapshot {index}")
        _exact_keys(
            snapshot,
            {"snapshot_id", "snapshot_bundle_digest"},
            f"{label} snapshot {index}",
        )
        snapshot_ids.append(snapshot["snapshot_id"])
        bundle_digests.append(snapshot["snapshot_bundle_digest"])

    evidence_by_id: dict[object, dict[str, object]] = {}
    for index, item in enumerate(
        _array(projected["evidence_metadata"], f"{label} Evidence metadata")
    ):
        metadata = _mapping(item, f"{label} Evidence metadata {index}")
        _exact_keys(
            metadata,
            {
                "evidence_id",
                "evidence_digest",
                "artifact_id",
                "source_context_id",
                "byte_start",
                "byte_end",
                "locator",
                "excerpt_digest",
                "artifact_content_digest",
            },
            f"{label} Evidence metadata {index}",
        )
        evidence_id = metadata["evidence_id"]
        if evidence_id in evidence_by_id:
            raise _authority_mismatch(f"{label} duplicate Evidence metadata")
        evidence_by_id[evidence_id] = {
            "evidence_id": evidence_id,
            "artifact_id": metadata["artifact_id"],
            "source_context_id": metadata["source_context_id"],
            "byte_start": metadata["byte_start"],
            "byte_end": metadata["byte_end"],
            "locator": metadata["locator"],
            "excerpt_digest": metadata["excerpt_digest"],
            "artifact_content_digest": metadata["artifact_content_digest"],
            "digest": metadata["evidence_digest"],
        }

    allowlist = _array(
        projected["evidence_metadata_ids"], f"{label} Evidence allowlist"
    )
    if allowlist != list(evidence_by_id):
        raise _authority_mismatch(f"{label} Evidence allowlist")
    supports: list[dict[str, object]] = []
    for index, item in enumerate(_array(projected["support"], f"{label} Support")):
        support = _mapping(item, f"{label} Support {index}")
        _exact_keys(
            support,
            {
                "support_digest",
                "snapshot_id",
                "member_kind",
                "root_id",
                "state_id",
                "state_digest",
                "evidence_metadata_ids",
            },
            f"{label} Support {index}",
        )
        evidence_ids = _array(
            support["evidence_metadata_ids"],
            f"{label} Support {index} Evidence IDs",
        )
        try:
            evidence = [evidence_by_id[item] for item in evidence_ids]
        except KeyError as exc:
            raise _authority_mismatch(
                f"{label} Support references unknown Evidence"
            ) from exc
        record = {
            "snapshot_id": support["snapshot_id"],
            "member_kind": support["member_kind"],
            "root_id": support["root_id"],
            "state_id": support["state_id"],
            "state_digest": support["state_digest"],
            "evidence": evidence,
            "digest": support["support_digest"],
        }
        _require_digest_mapping(
            record,
            "STRUCTURE_VIEW_SUPPORT@1",
            f"{label} Support {index}",
        )
        supports.append(record)

    if (
        binding["session_id"] != read_authority["session_id"]
        or binding["session_digest"] != read_authority["session_digest"]
        or binding["read_set_digest"] != read_authority["read_set_digest"]
        or binding["ordered_bundle_digest"]
        != read_authority["ordered_bundle_digest"]
    ):
        raise _authority_mismatch(f"{label} Read Set")
    allowed_snapshots = dict(
        zip(
            read_authority["snapshot_ids"],
            read_authority["snapshot_bundle_digests"],
            strict=True,
        )
    )
    if any(
        allowed_snapshots.get(snapshot_id) != bundle_digest
        for snapshot_id, bundle_digest in zip(
            snapshot_ids, bundle_digests, strict=True
        )
    ):
        raise _authority_mismatch(f"{label} Snapshot binding")
    record = {
        "result_id": projected["result_id"],
        "operation": projected["operation"],
        "session_id": binding["session_id"],
        "session_digest": binding["session_digest"],
        "read_set_digest": binding["read_set_digest"],
        "ordered_bundle_digest": binding["ordered_bundle_digest"],
        "snapshot_ids": snapshot_ids,
        "snapshot_bundle_digests": bundle_digests,
        "profile_refs": _array(projected["profile_refs"], f"{label} Profile refs"),
        "relation_modalities": _array(
            projected["relation_modalities"], f"{label} relation modalities"
        ),
        "coverage": _array(projected["coverage"], f"{label} coverage"),
        "completeness": projected["completeness"],
        "truncated": projected["truncated"],
        "limitations": _array(projected["limitations"], f"{label} limitations"),
        "payload": projected["result_payload"],
        "support_map": supports,
        "evidence_allowlist": allowlist,
        "digest": projected["result_digest"],
    }
    _require_stable_mapping(
        record,
        id_field="result_id",
        stable_kind="structure_view_result",
        id_domain="STRUCTURE_VIEW_RESULT_ID@1",
        digest_domain="STRUCTURE_VIEW_RESULT@1",
        label=label,
    )
    return record


def _reconstruct_resolutions(
    value: object,
    read_authority: Mapping[str, object],
    candidate_views: Mapping[object, Mapping[str, object]],
) -> dict[str, object]:
    projected = _mapping(value, "candidate resolution set")
    _exact_keys(
        projected,
        {
            "resolution_set_id",
            "resolution_set_digest",
            "question_id",
            "requirement_id",
            "requirement_digest",
            "proposal_digest",
            "planning_invocation",
            "resolutions",
            "read_authority_digest",
        },
        "candidate resolution set",
    )
    invocation = _reconstruct_invocation(
        projected["planning_invocation"], "Query planning invocation"
    )
    records: list[dict[str, object]] = []
    used_views: set[object] = set()
    for index, item in enumerate(
        _array(projected["resolutions"], "candidate resolutions")
    ):
        resolution = _mapping(item, f"candidate resolution {index}")
        _exact_keys(
            resolution,
            {
                "resolution_id",
                "resolution_digest",
                "selector",
                "status",
                "candidate_view_result_id",
                "candidate_view_result_digest",
                "argument",
                "limitations",
                "read_authority_digest",
            },
            f"candidate resolution {index}",
        )
        selector = _mapping(resolution["selector"], f"selector {index}")
        _exact_keys(
            selector,
            {
                "selector_id",
                "need_ids",
                "snapshot_id",
                "origin",
                "mention",
                "entity_type",
                "canonical_ga",
                "canonical_gav",
                "max_candidates",
                "entity_root_id",
                "entity_state_id",
            },
            f"selector {index}",
        )
        candidate = candidate_views.get(resolution["resolution_id"])
        if candidate is None:
            if (
                resolution["candidate_view_result_id"] is not None
                or resolution["candidate_view_result_digest"] is not None
            ):
                raise _authority_mismatch(f"candidate resolution {index} view")
        else:
            used_views.add(resolution["resolution_id"])
            if (
                resolution["candidate_view_result_id"] != candidate["result_id"]
                or resolution["candidate_view_result_digest"]
                != candidate["digest"]
            ):
                raise _authority_mismatch(f"candidate resolution {index} view")
        argument_value = resolution["argument"]
        argument: dict[str, object] | None = None
        if argument_value is not None:
            argument_projection = _mapping(
                argument_value, f"candidate resolution {index} argument"
            )
            _exact_keys(
                argument_projection,
                {
                    "origin",
                    "session_id",
                    "read_set_digest",
                    "ordered_bundle_digest",
                    "snapshot_id",
                    "snapshot_bundle_digest",
                    "entity_root_id",
                    "entity_state_id",
                    "candidate_result_id",
                    "candidate_result_digest",
                    "argument_digest",
                },
                f"candidate resolution {index} argument",
            )
            argument = {
                key: child
                for key, child in argument_projection.items()
                if key != "argument_digest"
            }
            argument["digest"] = argument_projection["argument_digest"]
            _require_digest_mapping(
                argument,
                "STRUCTURE_ENTITY_ARGUMENT@1",
                f"candidate resolution {index} argument",
            )
            if (
                argument["session_id"] != read_authority["session_id"]
                or argument["read_set_digest"]
                != read_authority["read_set_digest"]
                or argument["ordered_bundle_digest"]
                != read_authority["ordered_bundle_digest"]
            ):
                raise _authority_mismatch(
                    f"candidate resolution {index} argument Read Set"
                )
        if resolution["read_authority_digest"] != read_authority["digest"]:
            raise _authority_mismatch(f"candidate resolution {index} Read Set")
        record = {
            "resolution_id": resolution["resolution_id"],
            "selector": dict(selector),
            "status": resolution["status"],
            "candidate_result": dict(candidate) if candidate is not None else None,
            "argument": argument,
            "limitations": _array(
                resolution["limitations"], f"candidate resolution {index} limitations"
            ),
            "read_authority_digest": resolution["read_authority_digest"],
            "digest": resolution["resolution_digest"],
        }
        _require_stable_mapping(
            record,
            id_field="resolution_id",
            stable_kind="world_model_resolution",
            id_domain="WORLD_MODEL_ENTITY_RESOLUTION_ID@1",
            digest_domain="WORLD_MODEL_ENTITY_RESOLUTION@1",
            label=f"candidate resolution {index}",
        )
        records.append(record)
    if used_views != set(candidate_views):
        raise _authority_mismatch("orphan candidate view")
    if projected["read_authority_digest"] != read_authority["digest"]:
        raise _authority_mismatch("candidate resolution set Read Set")
    record = {
        "resolution_set_id": projected["resolution_set_id"],
        "question_id": projected["question_id"],
        "requirement_id": projected["requirement_id"],
        "requirement_digest": projected["requirement_digest"],
        "proposal_digest": projected["proposal_digest"],
        "planning_invocation": invocation,
        "resolutions": records,
        "read_authority": dict(read_authority),
        "digest": projected["resolution_set_digest"],
    }
    _require_stable_mapping(
        record,
        id_field="resolution_set_id",
        stable_kind="world_model_resolution_set",
        id_domain="WORLD_MODEL_RESOLUTION_SET_ID@1",
        digest_domain="WORLD_MODEL_RESOLUTION_SET@1",
        label="candidate resolution set",
    )
    return record


def _reconstruct_plan(
    value: object, read_authority: Mapping[str, object]
) -> dict[str, object]:
    projected = _mapping(value, "Query Plan")
    _exact_keys(
        projected,
        {
            "plan_id",
            "plan_digest",
            "question_id",
            "requirement_id",
            "requirement_digest",
            "resolution_set_id",
            "resolution_set_digest",
            "planning_invocation",
            "capability_registry_digest",
            "steps",
            "explicit_gaps",
            "read_authority_digest",
        },
        "Query Plan",
    )
    invocation = _reconstruct_invocation(
        projected["planning_invocation"], "Query Plan invocation"
    )
    steps: list[dict[str, object]] = []
    for index, item in enumerate(_array(projected["steps"], "Query steps")):
        step = _mapping(item, f"Query step {index}")
        _exact_keys(
            step,
            {
                "step_id",
                "step_digest",
                "need_ids",
                "operation",
                "arguments",
                "parameters",
                "constraint_ids",
                "state",
                "limitation_code",
            },
            f"Query step {index}",
        )
        record = {
            "step_id": step["step_id"],
            "need_ids": _array(step["need_ids"], f"Query step {index} Need IDs"),
            "operation": step["operation"],
            "arguments": step["arguments"],
            "parameters": step["parameters"],
            "constraint_ids": _array(
                step["constraint_ids"], f"Query step {index} constraint IDs"
            ),
            "state": step["state"],
            "limitation_code": step["limitation_code"],
            "digest": step["step_digest"],
        }
        _require_digest_mapping(
            record, "WORLD_MODEL_QUERY_STEP@1", f"Query step {index}"
        )
        steps.append(record)
    gaps = _array(projected["explicit_gaps"], "Query Plan gaps")
    for index, item in enumerate(gaps):
        _exact_keys(
            _mapping(item, f"Query Plan gap {index}"),
            {"need_id", "reason_code", "detail"},
            f"Query Plan gap {index}",
        )
    if projected["read_authority_digest"] != read_authority["digest"]:
        raise _authority_mismatch("Query Plan Read Set")
    record = {
        "plan_id": projected["plan_id"],
        "question_id": projected["question_id"],
        "requirement_id": projected["requirement_id"],
        "requirement_digest": projected["requirement_digest"],
        "resolution_set_id": projected["resolution_set_id"],
        "resolution_set_digest": projected["resolution_set_digest"],
        "planning_invocation": invocation,
        "capability_registry_digest": projected["capability_registry_digest"],
        "steps": steps,
        "explicit_gaps": gaps,
        "read_authority": dict(read_authority),
        "digest": projected["plan_digest"],
    }
    _require_stable_mapping(
        record,
        id_field="plan_id",
        stable_kind="world_model_query_plan",
        id_domain="WORLD_MODEL_QUERY_PLAN_ID@1",
        digest_domain="WORLD_MODEL_QUERY_PLAN@1",
        label="Query Plan",
    )
    return record


def _reconstruct_result_set(
    value: object,
    read_authority: Mapping[str, object],
    query_views: Mapping[object, Mapping[str, object]],
) -> dict[str, object]:
    projected = _mapping(value, "Query Result Set")
    _exact_keys(
        projected,
        {
            "result_set_id",
            "result_set_digest",
            "question_id",
            "requirement_id",
            "plan_id",
            "plan_digest",
            "step_results",
            "read_authority_digest",
            "support_map_digest",
            "evidence_allowlist_digest",
        },
        "Query Result Set",
    )
    results: list[dict[str, object]] = []
    used_views: set[object] = set()
    for index, item in enumerate(
        _array(projected["step_results"], "Query step Results")
    ):
        result = _mapping(item, f"Query step Result {index}")
        _exact_keys(
            result,
            {
                "step_result_id",
                "step_result_digest",
                "step_id",
                "step_digest",
                "view_result_id",
                "view_result_digest",
            },
            f"Query step Result {index}",
        )
        view = query_views.get(result["step_result_id"])
        if view is None:
            raise _authority_mismatch(f"Query step Result {index} view")
        used_views.add(result["step_result_id"])
        if (
            result["view_result_id"] != view["result_id"]
            or result["view_result_digest"] != view["digest"]
        ):
            raise _authority_mismatch(f"Query step Result {index} view")
        record = {
            "step_result_id": result["step_result_id"],
            "step_id": result["step_id"],
            "step_digest": result["step_digest"],
            "view_result": dict(view),
            "digest": result["step_result_digest"],
        }
        _require_stable_mapping(
            record,
            id_field="step_result_id",
            stable_kind="world_model_step_result",
            id_domain="WORLD_MODEL_QUERY_STEP_RESULT_ID@1",
            digest_domain="WORLD_MODEL_QUERY_STEP_RESULT@1",
            label=f"Query step Result {index}",
        )
        results.append(record)
    if used_views != set(query_views):
        raise _authority_mismatch("orphan Query Result view")
    if projected["read_authority_digest"] != read_authority["digest"]:
        raise _authority_mismatch("Query Result Set Read Set")
    support_digest = digest_of(
        [
            "WORLD_MODEL_QUERY_SUPPORT_MAP@1",
            [
                support
                for result in results
                for support in result["view_result"]["support_map"]
            ],
        ]
    ).value
    evidence_allowlist_digest = digest_of(
        [
            "WORLD_MODEL_QUERY_EVIDENCE_ALLOWLIST@1",
            sorted(
                {
                    evidence
                    for result in results
                    for evidence in result["view_result"]["evidence_allowlist"]
                }
            ),
        ]
    ).value
    if (
        projected["support_map_digest"] != support_digest
        or projected["evidence_allowlist_digest"] != evidence_allowlist_digest
    ):
        raise _authority_mismatch("Query Result support closure")
    record = {
        "result_set_id": projected["result_set_id"],
        "question_id": projected["question_id"],
        "requirement_id": projected["requirement_id"],
        "plan_id": projected["plan_id"],
        "plan_digest": projected["plan_digest"],
        "step_results": results,
        "read_authority": dict(read_authority),
        "support_map_digest": projected["support_map_digest"],
        "evidence_allowlist_digest": projected["evidence_allowlist_digest"],
        "digest": projected["result_set_digest"],
    }
    _require_stable_mapping(
        record,
        id_field="result_set_id",
        stable_kind="world_model_result_set",
        id_domain="WORLD_MODEL_QUERY_RESULT_SET_ID@1",
        digest_domain="WORLD_MODEL_QUERY_RESULT_SET@1",
        label="Query Result Set",
    )
    return record


def _reconstruct_assessment(
    value: object, read_authority: Mapping[str, object]
) -> dict[str, object]:
    projected = _mapping(value, "Need Assessment")
    _exact_keys(
        projected,
        {
            "assessment_id",
            "question_id",
            "requirement_id",
            "requirement_digest",
            "plan_id",
            "plan_digest",
            "result_set_id",
            "result_set_digest",
            "needs",
            "joint_constraints",
            "sufficient",
            "read_authority",
            "digest",
        },
        "Need Assessment",
    )
    needs = _array(projected["needs"], "Need Assessments")
    for index, item in enumerate(needs):
        need = _mapping(item, f"Need Assessment {index}")
        _exact_keys(
            need,
            {
                "need_id",
                "outcome",
                "step_result_ids",
                "view_result_ids",
                "support_digests",
                "gap_code",
                "gap_detail",
                "limitations",
                "digest",
            },
            f"Need Assessment {index}",
        )
        _require_digest_mapping(
            need,
            "WORLD_MODEL_NEED_ASSESSMENT@1",
            f"Need Assessment {index}",
        )
    joints = _array(projected["joint_constraints"], "Joint Assessments")
    for index, item in enumerate(joints):
        joint = _mapping(item, f"Joint Assessment {index}")
        _exact_keys(
            joint,
            {
                "constraint_id",
                "satisfied",
                "need_ids",
                "step_result_ids",
                "view_result_ids",
                "support_digests",
                "finding",
                "digest",
            },
            f"Joint Assessment {index}",
        )
        _require_digest_mapping(
            joint,
            "WORLD_MODEL_JOINT_ASSESSMENT@1",
            f"Joint Assessment {index}",
        )
    if projected["read_authority"] != read_authority:
        raise _authority_mismatch("Need Assessment Read Set")
    record = dict(projected)
    _require_stable_mapping(
        record,
        id_field="assessment_id",
        stable_kind="world_model_assessment",
        id_domain="WORLD_MODEL_ASSESSMENT_ID@1",
        digest_domain="WORLD_MODEL_ASSESSMENT@1",
        label="Need Assessment",
    )
    return record


def _reconstruct_draft(
    value: object, read_authority: Mapping[str, object]
) -> dict[str, object]:
    projected = _mapping(value, "Answer Draft")
    _exact_keys(
        projected,
        {
            "draft_id",
            "draft_digest",
            "question_id",
            "requirement_id",
            "plan_id",
            "result_set_id",
            "assessment_id",
            "body",
            "body_digest",
            "claims",
            "generation_invocation",
            "read_authority_digest",
        },
        "Answer Draft",
    )
    claims = _array(projected["claims"], "Answer Claims")
    for index, item in enumerate(claims):
        claim = _mapping(item, f"Answer Claim {index}")
        _exact_keys(
            claim,
            {
                "claim_id",
                "need_id",
                "kind",
                "text",
                "step_result_ids",
                "view_result_ids",
                "support_digests",
                "evidence_references",
                "gap_code",
                "limitation_codes",
                "digest",
            },
            f"Answer Claim {index}",
        )
        _require_digest_mapping(
            claim, "WORLD_MODEL_ANSWER_CLAIM@1", f"Answer Claim {index}"
        )
    invocation = _reconstruct_invocation(
        projected["generation_invocation"], "Answer generation invocation"
    )
    if not isinstance(projected["body"], str) or projected[
        "body_digest"
    ] != digest_of(projected["body"]).value:
        raise _authority_mismatch("Answer body digest")
    if projected["body"] != "\n".join(
        _mapping(item, "Answer Claim")["text"] for item in claims
    ):
        raise _authority_mismatch("Answer body/Claim binding")
    if projected["read_authority_digest"] != read_authority["digest"]:
        raise _authority_mismatch("Answer Draft Read Set")
    record = {
        "draft_id": projected["draft_id"],
        "question_id": projected["question_id"],
        "requirement_id": projected["requirement_id"],
        "plan_id": projected["plan_id"],
        "result_set_id": projected["result_set_id"],
        "assessment_id": projected["assessment_id"],
        "claims": claims,
        "body": projected["body"],
        "body_digest": projected["body_digest"],
        "generation_invocation": invocation,
        "read_authority": dict(read_authority),
        "digest": projected["draft_digest"],
    }
    _require_stable_mapping(
        record,
        id_field="draft_id",
        stable_kind="world_model_draft",
        id_domain="WORLD_MODEL_ANSWER_DRAFT_ID@1",
        digest_domain="WORLD_MODEL_ANSWER_DRAFT@1",
        label="Answer Draft",
    )
    return record


def _reconstruct_review(
    value: object,
    read_authority: Mapping[str, object],
    draft: Mapping[str, object],
) -> dict[str, object]:
    projected = _mapping(value, "Answer Review")
    _exact_keys(
        projected,
        {
            "review_id",
            "review_digest",
            "question_id",
            "draft_id",
            "draft_digest",
            "decision",
            "dimensions",
            "checked_need_ids",
            "checked_constraint_ids",
            "checked_step_result_ids",
            "finding_codes",
            "findings",
            "invocation_separation",
            "generation_invocation_id",
            "read_authority_digest",
        },
        "Answer Review",
    )
    dimensions = _array(projected["dimensions"], "review dimensions")
    expected_dimensions = [item.value for item in WorldModelReviewDimension]
    actual_dimensions: list[object] = []
    for index, item in enumerate(dimensions):
        dimension = _mapping(item, f"review dimension {index}")
        _exact_keys(
            dimension,
            {"dimension", "decision", "finding_codes"},
            f"review dimension {index}",
        )
        actual_dimensions.append(dimension["dimension"])
    if actual_dimensions != expected_dimensions:
        raise _authority_mismatch("review dimension closure")
    separation = _mapping(
        projected["invocation_separation"], "review invocation separation"
    )
    _exact_keys(
        separation,
        {"generation", "review", "invocations_separate"},
        "review invocation separation",
    )
    generation = _reconstruct_invocation(
        separation["generation"], "review generation invocation"
    )
    reviewer = _reconstruct_invocation(
        separation["review"], "review invocation"
    )
    if generation != draft["generation_invocation"]:
        raise _authority_mismatch("Review generation invocation")
    if projected["read_authority_digest"] != read_authority["digest"]:
        raise _authority_mismatch("Answer Review Read Set")
    record = {
        "review_id": projected["review_id"],
        "question_id": projected["question_id"],
        "draft_id": projected["draft_id"],
        "draft_digest": projected["draft_digest"],
        "decision": projected["decision"],
        "dimensions": dimensions,
        "checked_need_ids": _array(
            projected["checked_need_ids"], "review checked Need IDs"
        ),
        "checked_constraint_ids": _array(
            projected["checked_constraint_ids"],
            "review checked constraint IDs",
        ),
        "checked_step_result_ids": _array(
            projected["checked_step_result_ids"],
            "review checked step Result IDs",
        ),
        "finding_codes": _array(
            projected["finding_codes"], "review finding codes"
        ),
        "findings": _array(projected["findings"], "review findings"),
        "review_invocation": reviewer,
        "generation_invocation_id": projected["generation_invocation_id"],
        "read_authority": dict(read_authority),
        "digest": projected["review_digest"],
    }
    _require_stable_mapping(
        record,
        id_field="review_id",
        stable_kind="world_model_review",
        id_domain="WORLD_MODEL_ANSWER_REVIEW_ID@1",
        digest_domain="WORLD_MODEL_ANSWER_REVIEW@1",
        label="Answer Review",
    )
    return record


def _reconstruct_authorization(
    value: object, read_authority: Mapping[str, object]
) -> dict[str, object]:
    projected = _mapping(value, "Response Authorization")
    _exact_keys(
        projected,
        {
            "authorization_id",
            "question_id",
            "requirement_id",
            "plan_id",
            "result_set_id",
            "assessment_id",
            "draft_id",
            "draft_digest",
            "review_id",
            "review_digest",
            "permission_digest",
            "read_authority",
            "chain_digest",
            "sink_id",
            "digest",
        },
        "Response Authorization",
    )
    if projected["read_authority"] != read_authority:
        raise _authority_mismatch("Response Authorization Read Set")
    record = dict(projected)
    _require_stable_mapping(
        record,
        id_field="authorization_id",
        stable_kind="world_model_authorization",
        id_domain="WORLD_MODEL_AUTHORIZATION_ID@1",
        digest_domain="WORLD_MODEL_AUTHORIZATION@1",
        label="Response Authorization",
    )
    return record


def _reconstruct_delivery(value: object) -> dict[str, object]:
    projected = _mapping(value, "Delivery")
    _exact_keys(
        projected,
        {
            "delivery_id",
            "question_id",
            "authorization_id",
            "authorization_digest",
            "delivery_key",
            "sink_id",
            "body_digest",
            "projection_digest",
            "state",
            "receipt",
            "failure_code",
            "revision",
            "digest",
        },
        "Delivery",
    )
    receipt = _mapping(projected["receipt"], "Delivery receipt")
    _exact_keys(
        receipt,
        {
            "receipt_id",
            "sink_id",
            "delivery_key",
            "body_digest",
            "projection_digest",
            "accepted",
            "digest",
        },
        "Delivery receipt",
    )
    _require_digest_mapping(
        receipt, "WORLD_MODEL_DELIVERY_RECEIPT@1", "Delivery receipt"
    )
    expected_receipt_id = (
        "evaluation-receipt:"
        + digest_of(
            [
                "WORLD_MODEL_LOCAL_EVALUATION_RECEIPT_ID@1",
                projected["delivery_key"],
            ]
        ).value[-32:]
    )
    if receipt["receipt_id"] != expected_receipt_id:
        raise _authority_mismatch("Delivery receipt identity")
    record = dict(projected)
    core = {
        key: child
        for key, child in record.items()
        if key not in {"delivery_id", "digest"}
    }
    if record["digest"] != digest_of(["WORLD_MODEL_DELIVERY@1", core]).value:
        raise _authority_mismatch("Delivery digest")
    prepared_core = {
        **core,
        "state": WorldModelDeliveryState.PREPARED.value,
        "receipt": None,
        "failure_code": None,
        "revision": 1,
    }
    expected_id = _stable_value(
        "world_model_delivery",
        digest_of(["WORLD_MODEL_DELIVERY_ID@1", prepared_core]),
    )
    if record["delivery_id"] != expected_id:
        raise _authority_mismatch("Delivery identity")
    return record


def _reconstruct_invocation(value: object, label: str) -> dict[str, object]:
    invocation = _mapping(value, label)
    _exact_keys(
        invocation,
        {
            "invocation_id",
            "stage",
            "question_id",
            "question_digest",
            "input_digest",
            "strategy_ref",
            "execution_mode",
            "provider_route",
            "external_dispatch_allowed",
            "digest",
        },
        label,
    )
    _require_stable_mapping(
        invocation,
        id_field="invocation_id",
        stable_kind="offline_invocation",
        id_domain="OFFLINE_STRATEGY_INVOCATION_ID@1",
        digest_domain="OFFLINE_STRATEGY_INVOCATION@1",
        label=label,
    )
    if (
        invocation["execution_mode"] != OFFLINE_STRATEGY_MODE
        or invocation["provider_route"] is not None
        or invocation["external_dispatch_allowed"] is not False
    ):
        raise _authority_mismatch(f"{label} offline boundary")
    return dict(invocation)


def _require_stage_records(
    stages: Sequence[object], records: Sequence[Mapping[str, object]]
) -> None:
    identity_fields = (
        "question_id",
        "requirement_id",
        "resolution_set_id",
        "plan_id",
        "result_set_id",
        "assessment_id",
        "draft_id",
        "review_id",
        "authorization_id",
        "delivery_id",
    )
    for index, (stage_value, record, identity_field) in enumerate(
        zip(stages, records, identity_fields, strict=True)
    ):
        stage = _mapping(stage_value, f"authority stage {index}")
        if (
            stage["authority_id"] != record[identity_field]
            or stage["authority_digest"] != record["digest"]
        ):
            raise _authority_mismatch(f"authority stage {_AUTHORITY_STAGES[index]}")


def _require_authority_cross_links(
    page: Mapping[str, object],
    records: Sequence[Mapping[str, object]],
    *,
    read_authority: Mapping[str, object],
) -> None:
    (
        question,
        requirement,
        resolutions,
        plan,
        result_set,
        assessment,
        draft,
        review,
        authorization,
        delivery,
    ) = records
    question_id = question["question_id"]
    question_digest = question["digest"]
    if (
        type(question["revision"]) is not int
        or question["revision"] != 1
        or type(question["use_epoch"]) is not int
        or question["use_epoch"] != 1
        or question["mode"] != WORLD_MODEL_MODE
        or question["external_dispatch_allowed"] is not False
        or question["model_route"] is not None
    ):
        raise _authority_mismatch("Question offline boundary")

    invocations = (
        requirement["planning_invocation"],
        requirement["fidelity_review_invocation"],
        resolutions["planning_invocation"],
        plan["planning_invocation"],
        draft["generation_invocation"],
        review["review_invocation"],
    )
    if any(
        invocation["question_id"] != question_id
        or invocation["question_digest"] != question_digest
        for invocation in invocations
    ):
        raise _authority_mismatch("offline invocation Question binding")

    need_ids = [item["need_id"] for item in requirement["needs"]]
    constraint_ids = [
        item["constraint_id"] for item in requirement["joint_constraints"]
    ]
    requirement_proposal_digest = digest_of(
        [
            "WORLD_MODEL_REQUIREMENT_PROPOSAL@1",
            {
                "original_question": requirement["original_question"],
                "response_language": requirement["response_language"],
                "needs": requirement["needs"],
                "joint_constraints": requirement["joint_constraints"],
                "invocation_id": requirement["planning_invocation"][
                    "invocation_id"
                ],
                "invocation_digest": requirement["planning_invocation"]["digest"],
            },
        ]
    ).value
    if (
        requirement["question_id"] != question_id
        or requirement["question_digest"] != question_digest
        or requirement["original_question"] != question["original_question"]
        or requirement["response_language"] != question["response_language"]
        or requirement["revision"] != 1
        or requirement["planning_invocation"]["stage"]
        != OfflineStage.REQUIREMENT_PLANNING.value
        or requirement["planning_invocation"]["input_digest"] != question_digest
        or requirement["fidelity_review_invocation"]["stage"]
        != OfflineStage.REQUIREMENT_FIDELITY_REVIEW.value
        or requirement["fidelity_review_invocation"]["input_digest"]
        != requirement_proposal_digest
        or requirement["fidelity_decision"]
        != WorldModelReviewDecision.APPROVE.value
        or requirement["fidelity_accepted_need_ids"] != need_ids
        or requirement["fidelity_accepted_constraint_ids"] != constraint_ids
        or requirement["fidelity_original_question_preserved"] is not True
        or requirement["fidelity_all_material_questions_covered"] is not True
        or requirement["fidelity_findings"]
    ):
        raise _authority_mismatch("Requirement fidelity chain")

    if (
        resolutions["question_id"] != question_id
        or resolutions["requirement_id"] != requirement["requirement_id"]
        or resolutions["requirement_digest"] != requirement["digest"]
        or resolutions["planning_invocation"] != plan["planning_invocation"]
        or plan["question_id"] != question_id
        or plan["requirement_id"] != requirement["requirement_id"]
        or plan["requirement_digest"] != requirement["digest"]
        or plan["resolution_set_id"] != resolutions["resolution_set_id"]
        or plan["resolution_set_digest"] != resolutions["digest"]
        or plan["planning_invocation"]["stage"]
        != OfflineStage.QUERY_PLANNING.value
        or plan["planning_invocation"]["input_digest"] != requirement["digest"]
    ):
        raise _authority_mismatch("candidate resolution/Query Plan chain")
    proposal_steps = [
        {
            key: child
            for key, child in step.items()
            if key not in {"state", "limitation_code", "digest"}
        }
        for step in plan["steps"]
    ]
    plan_proposal_digest = digest_of(
        [
            "WORLD_MODEL_QUERY_PLAN_PROPOSAL@1",
            {
                "requirement_id": requirement["requirement_id"],
                "requirement_digest": requirement["digest"],
                "read_set_digest": read_authority["read_set_digest"],
                "ordered_bundle_digest": read_authority["ordered_bundle_digest"],
                "selectors": [
                    item["selector"] for item in resolutions["resolutions"]
                ],
                "steps": proposal_steps,
                "explicit_gaps": plan["explicit_gaps"],
                "invocation_id": plan["planning_invocation"]["invocation_id"],
                "invocation_digest": plan["planning_invocation"]["digest"],
            },
        ]
    ).value
    if resolutions["proposal_digest"] != plan_proposal_digest:
        raise _authority_mismatch("Query Plan proposal binding")

    ready_steps = [item for item in plan["steps"] if item["state"] == "READY"]
    if (
        result_set["question_id"] != question_id
        or result_set["requirement_id"] != requirement["requirement_id"]
        or result_set["plan_id"] != plan["plan_id"]
        or result_set["plan_digest"] != plan["digest"]
        or [
            (item["step_id"], item["step_digest"])
            for item in result_set["step_results"]
        ]
        != [(item["step_id"], item["digest"]) for item in ready_steps]
    ):
        raise _authority_mismatch("Query Result Set Plan binding")

    if (
        assessment["question_id"] != question_id
        or assessment["requirement_id"] != requirement["requirement_id"]
        or assessment["requirement_digest"] != requirement["digest"]
        or assessment["plan_id"] != plan["plan_id"]
        or assessment["plan_digest"] != plan["digest"]
        or assessment["result_set_id"] != result_set["result_set_id"]
        or assessment["result_set_digest"] != result_set["digest"]
        or [item["need_id"] for item in assessment["needs"]] != need_ids
        or [
            item["constraint_id"] for item in assessment["joint_constraints"]
        ]
        != constraint_ids
    ):
        raise _authority_mismatch("Need Assessment chain")
    _require_projected_limitations(
        page["limitations"],
        resolutions=resolutions,
        plan=plan,
        result_set=result_set,
        assessment=assessment,
    )

    draft_input_digest = digest_of(
        [
            "WORLD_MODEL_DRAFT_INPUT@1",
            question_digest,
            requirement["digest"],
            plan["digest"],
            result_set["digest"],
            assessment["digest"],
        ]
    ).value
    if (
        draft["question_id"] != question_id
        or draft["requirement_id"] != requirement["requirement_id"]
        or draft["plan_id"] != plan["plan_id"]
        or draft["result_set_id"] != result_set["result_set_id"]
        or draft["assessment_id"] != assessment["assessment_id"]
        or draft["generation_invocation"]["stage"]
        != OfflineStage.ANSWER_DRAFTING.value
        or draft["generation_invocation"]["input_digest"] != draft_input_digest
    ):
        raise _authority_mismatch("Answer Draft chain")

    review_input_digest = digest_of(
        [
            "WORLD_MODEL_REVIEW_INPUT@1",
            question_digest,
            requirement["digest"],
            plan["digest"],
            result_set["digest"],
            assessment["digest"],
            draft["digest"],
        ]
    ).value
    if (
        review["question_id"] != question_id
        or review["draft_id"] != draft["draft_id"]
        or review["draft_digest"] != draft["digest"]
        or review["decision"] != WorldModelReviewDecision.APPROVE.value
        or review["checked_need_ids"] != need_ids
        or review["checked_constraint_ids"] != constraint_ids
        or review["checked_step_result_ids"]
        != [item["step_result_id"] for item in result_set["step_results"]]
        or review["finding_codes"]
        or review["findings"]
        or review["review_invocation"]["stage"]
        != OfflineStage.ANSWER_REVIEW.value
        or review["review_invocation"]["input_digest"] != review_input_digest
        or review["review_invocation"]["invocation_id"]
        == draft["generation_invocation"]["invocation_id"]
        or review["generation_invocation_id"]
        != draft["generation_invocation"]["invocation_id"]
    ):
        raise _authority_mismatch("Answer Review chain")

    preauthority_digest = digest_of(
        [
            "WORLD_MODEL_PREAUTHORITY_CHAIN@1",
            question_digest,
            requirement["digest"],
            resolutions["digest"],
            plan["digest"],
            result_set["digest"],
            assessment["digest"],
            draft["digest"],
            review["digest"],
        ]
    ).value
    if (
        authorization["question_id"] != question_id
        or authorization["requirement_id"] != requirement["requirement_id"]
        or authorization["plan_id"] != plan["plan_id"]
        or authorization["result_set_id"] != result_set["result_set_id"]
        or authorization["assessment_id"] != assessment["assessment_id"]
        or authorization["draft_id"] != draft["draft_id"]
        or authorization["draft_digest"] != draft["digest"]
        or authorization["review_id"] != review["review_id"]
        or authorization["review_digest"] != review["digest"]
        or authorization["permission_digest"] != question["permission_digest"]
        or authorization["chain_digest"] != preauthority_digest
        or authorization["sink_id"] != EVALUATION_ONLY_SINK
    ):
        raise _authority_mismatch("Response Authorization chain")

    projection_digest = digest_of(
        [
            "WORLD_MODEL_EVALUATION_DELIVERY_PROJECTION@1",
            {
                "evaluation_only": True,
                "mode": WORLD_MODEL_MODE,
                "question_id": question_id,
                "requirement_id": requirement["requirement_id"],
                "read_set_digest": read_authority["read_set_digest"],
                "ordered_bundle_digest": read_authority[
                    "ordered_bundle_digest"
                ],
                "draft_id": draft["draft_id"],
                "draft_digest": draft["digest"],
                "authorization_id": authorization["authorization_id"],
                "authorization_digest": authorization["digest"],
            },
        ]
    ).value
    expected_delivery_key = (
        "world-model:" + digest_of(question["request_ref"]).value[-32:]
    )
    receipt = delivery["receipt"]
    if (
        delivery["question_id"] != question_id
        or delivery["authorization_id"] != authorization["authorization_id"]
        or delivery["authorization_digest"] != authorization["digest"]
        or delivery["delivery_key"] != expected_delivery_key
        or delivery["sink_id"] != EVALUATION_ONLY_SINK
        or delivery["body_digest"] != draft["body_digest"]
        or delivery["projection_digest"] != projection_digest
        or delivery["state"] != WorldModelDeliveryState.DELIVERED.value
        or delivery["failure_code"] is not None
        or type(delivery["revision"]) is not int
        or delivery["revision"] != 3
        or receipt["sink_id"] != delivery["sink_id"]
        or receipt["delivery_key"] != delivery["delivery_key"]
        or receipt["body_digest"] != delivery["body_digest"]
        or receipt["projection_digest"] != delivery["projection_digest"]
        or receipt["accepted"] is not True
    ):
        raise _authority_mismatch("Delivery chain")

    boundary = _mapping(page["execution_boundary"], "execution boundary")
    authority_chain = _mapping(page["authority_chain"], "authority chain")
    chain_core = {
        "question": question,
        "requirement": requirement,
        "resolutions": resolutions,
        "plan": plan,
        "result_set": result_set,
        "assessment": assessment,
        "draft": draft,
        "review": review,
        "authorization": authorization,
        "delivery": delivery,
        "provider_call_count": boundary.get("provider_call_count"),
        "network_operation_count": boundary.get("network_operation_count"),
    }
    expected_chain_digest = digest_of(
        ["WORLD_MODEL_AUTHORITY_CHAIN@1", chain_core]
    ).value
    if authority_chain["chain_digest"] != expected_chain_digest:
        raise _authority_mismatch("final authority chain digest")


def _require_projected_limitations(
    value: object,
    *,
    resolutions: Mapping[str, object],
    plan: Mapping[str, object],
    result_set: Mapping[str, object],
    assessment: Mapping[str, object],
) -> None:
    entries: dict[tuple[str, str, str | None], dict[str, object]] = {}

    def add(source: object, code: object, detail: object = None) -> None:
        if (
            not isinstance(source, str)
            or not isinstance(code, str)
            or (detail is not None and not isinstance(detail, str))
        ):
            raise _authority_mismatch("Limitation shape")
        entries[(source, code, detail)] = {
            "source": source,
            "code": code,
            "detail": detail,
        }

    for resolution in resolutions["resolutions"]:
        source = f"resolution:{resolution['resolution_id']}"
        for limitation in resolution["limitations"]:
            add(source, limitation)
        candidate = resolution["candidate_result"]
        if candidate is not None:
            for limitation in candidate["limitations"]:
                add(f"view:{candidate['result_id']}", limitation)
    for result in result_set["step_results"]:
        view = result["view_result"]
        for limitation in view["limitations"]:
            add(f"view:{view['result_id']}", limitation)
    for gap in plan["explicit_gaps"]:
        add(f"need:{gap['need_id']}", gap["reason_code"], gap["detail"])
    for need in assessment["needs"]:
        for limitation in need["limitations"]:
            add(f"need:{need['need_id']}", limitation)
        if need["gap_code"] is not None:
            add(f"need:{need['need_id']}", need["gap_code"], need["gap_detail"])

    projected = _array(value, "evaluation limitations")
    for index, item in enumerate(projected):
        limitation = _mapping(item, f"evaluation limitation {index}")
        _exact_keys(
            limitation,
            {"source", "code", "detail"},
            f"evaluation limitation {index}",
        )
        if (
            not isinstance(limitation["source"], str)
            or not isinstance(limitation["code"], str)
            or (
                limitation["detail"] is not None
                and not isinstance(limitation["detail"], str)
            )
        ):
            raise _authority_mismatch("Limitation shape")
    expected = [entries[key] for key in sorted(entries)]
    if projected != expected:
        raise _authority_mismatch("Limitation projection")


def _require_stable_mapping(
    record: Mapping[str, object],
    *,
    id_field: str,
    stable_kind: str,
    id_domain: str,
    digest_domain: str,
    label: str,
) -> None:
    identifier = _stable_id_text(record[id_field], f"{label} ID")
    digest = _digest_text(record["digest"], f"{label} digest")
    core = {
        key: value
        for key, value in record.items()
        if key not in {id_field, "digest"}
    }
    expected_id = _stable_value(stable_kind, digest_of([id_domain, core]))
    expected_digest = digest_of(
        [digest_domain, {id_field: expected_id, **core}]
    ).value
    if identifier != expected_id or digest != expected_digest:
        raise _authority_mismatch(f"{label} identity/digest")


def _require_digest_mapping(
    record: Mapping[str, object], digest_domain: str, label: str
) -> None:
    digest = _digest_text(record["digest"], f"{label} digest")
    core = {key: value for key, value in record.items() if key != "digest"}
    if digest != digest_of([digest_domain, core]).value:
        raise _authority_mismatch(f"{label} digest")


def _stable_value(kind: str, digest: Digest) -> str:
    return f"{kind}_{digest.value[-32:]}"


def _array(value: object, label: str) -> list[object]:
    if not isinstance(value, list):
        raise _invalid(
            "WORLD_MODEL_EVALUATION_ARRAY_REQUIRED",
            f"{label} must be a JSON array",
        )
    return value


def _authority_mismatch(label: str) -> DomainError:
    return _inconsistent(
        "WORLD_MODEL_EVALUATION_AUTHORITY_RECORD_MISMATCH",
        f"evaluation page {label} does not match its sealed authority chain",
    )


def _require_no_forbidden_payload_keys(value: object, *, path: str) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if key in _FORBIDDEN_PAYLOAD_KEYS:
                raise DomainError(
                    ErrorCode.CONTROL_STATE_DENIED,
                    "forbidden payload key cannot enter a world-model evaluation page",
                    {
                        "reason_code": "WORLD_MODEL_EVALUATION_FORBIDDEN_PAYLOAD_KEY",
                        "field": str(key),
                        "path": f"{path}.{key}",
                    },
                )
            _require_no_forbidden_payload_keys(child, path=f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            _require_no_forbidden_payload_keys(child, path=f"{path}[{index}]")


def _json_value(value: object) -> object:
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, Mapping):
        if any(not isinstance(key, str) for key in value):
            raise _invalid(
                "WORLD_MODEL_EVALUATION_JSON_KEY_INVALID",
                "evaluation page mappings require string keys",
            )
        return {key: _json_value(child) for key, child in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(child) for child in value]
    raise _invalid(
        "WORLD_MODEL_EVALUATION_JSON_VALUE_INVALID",
        "evaluation page contains a non-canonical value",
    )


def _implementation_commit(value: object) -> str:
    if not isinstance(value, str) or not _COMMIT_PATTERN.fullmatch(value):
        raise _invalid(
            "WORLD_MODEL_EVALUATION_COMMIT_INVALID",
            "implementation commit must be an exact lowercase 40-hex Git identity",
        )
    return value


def _canonical_absolute_path(
    value: str | os.PathLike[str], label: str
) -> Path:
    raw = os.fspath(value)
    if not isinstance(raw, str):
        raise _invalid(
            "WORLD_MODEL_EVALUATION_PATH_INVALID",
            f"{label} path must be text",
        )
    path = Path(raw)
    if (
        not path.is_absolute()
        or any(part in {".", ".."} for part in path.parts)
        or os.path.normpath(raw) != raw
    ):
        raise _invalid(
            "WORLD_MODEL_EVALUATION_PATH_NONCANONICAL",
            f"{label} path must be absolute, canonical, and traversal-free",
        )
    return path


def _require_existing_real_directory(path: Path, label: str) -> None:
    try:
        info = path.lstat()
    except FileNotFoundError as exc:
        raise _invalid(
            "WORLD_MODEL_EVALUATION_DIRECTORY_MISSING",
            f"{label} does not exist",
        ) from exc
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        raise _invalid(
            "WORLD_MODEL_EVALUATION_DIRECTORY_UNSAFE",
            f"{label} must be a real directory",
        )
    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise _invalid(
            "WORLD_MODEL_EVALUATION_DIRECTORY_UNAVAILABLE",
            f"{label} cannot be resolved",
        ) from exc
    if resolved != path:
        raise _invalid(
            "WORLD_MODEL_EVALUATION_DIRECTORY_SYMLINKED",
            f"{label} contains a symbolic-link component",
        )


def _write_new_regular_file(path: Path, payload: bytes) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor: int | None = None
    created = False
    try:
        descriptor = os.open(path, flags, 0o600)
        created = True
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise _invalid(
                "WORLD_MODEL_EVALUATION_FILE_UNSAFE",
                "evaluation page destination is not a private regular file",
            )
        remaining = memoryview(payload)
        while remaining:
            written = os.write(descriptor, remaining)
            if written <= 0:
                raise OSError("evaluation page write made no progress")
            remaining = remaining[written:]
        os.fsync(descriptor)
    except DomainError:
        if created:
            _unlink_created_file(path)
        raise
    except OSError as exc:
        if created:
            _unlink_created_file(path)
        raise _invalid(
            "WORLD_MODEL_EVALUATION_FILE_UNAVAILABLE",
            "evaluation page path exists, is unsafe, or cannot be written",
        ) from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)


def _unlink_created_file(path: Path) -> None:
    try:
        path.unlink()
    except OSError:
        pass


def _read_regular_file(path: Path) -> bytes:
    _require_existing_real_directory(path.parent, "evaluation page parent")
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise _invalid(
            "WORLD_MODEL_EVALUATION_FILE_UNAVAILABLE",
            "evaluation page is missing, inaccessible, or a symbolic link",
        ) from exc
    try:
        info = os.fstat(descriptor)
        if (
            not stat.S_ISREG(info.st_mode)
            or info.st_nlink != 1
            or info.st_size > _MAXIMUM_PAGE_BYTES
        ):
            raise _invalid(
                "WORLD_MODEL_EVALUATION_FILE_UNSAFE",
                "evaluation page must be a bounded unaliased regular file",
            )
        chunks: list[bytes] = []
        remaining = _MAXIMUM_PAGE_BYTES + 1
        while remaining:
            chunk = os.read(descriptor, min(65_536, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        payload = b"".join(chunks)
        if len(payload) > _MAXIMUM_PAGE_BYTES:
            raise _invalid(
                "WORLD_MODEL_EVALUATION_PAGE_SIZE_LIMIT",
                "world-model evaluation page exceeds the file size limit",
            )
        return payload
    finally:
        os.close(descriptor)


def _decode_canonical_json(payload: bytes) -> object:
    try:
        text = payload.decode("utf-8")
        value = json.loads(
            text,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_json_constant,
        )
        canonical = canonical_json_bytes(value)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise _invalid(
            "WORLD_MODEL_EVALUATION_JSON_INVALID",
            "evaluation page is not strict JSON",
        ) from exc
    if canonical != payload:
        raise _invalid(
            "WORLD_MODEL_EVALUATION_JSON_NONCANONICAL",
            "evaluation page is not canonical JSON",
        )
    return value


def _unique_object(pairs: Sequence[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> object:
    raise ValueError(f"non-finite JSON number: {value}")


def _mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        raise _invalid(
            "WORLD_MODEL_EVALUATION_OBJECT_REQUIRED",
            f"{label} must be a JSON object",
        )
    return value


def _exact_keys(
    value: Mapping[str, object], expected: set[str], label: str
) -> None:
    if set(value) != expected:
        raise _invalid(
            "WORLD_MODEL_EVALUATION_FIELDS_INVALID",
            f"{label} contains missing or unknown fields",
        )


def _stable_id_text(value: object, label: str) -> str:
    if not isinstance(value, str):
        raise _invalid(
            "WORLD_MODEL_EVALUATION_ID_INVALID", f"{label} is invalid"
        )
    try:
        StableId(value)
    except ValueError as exc:
        raise _invalid(
            "WORLD_MODEL_EVALUATION_ID_INVALID", f"{label} is invalid"
        ) from exc
    return value


def _digest_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not _DIGEST_PATTERN.fullmatch(value):
        raise _invalid(
            "WORLD_MODEL_EVALUATION_DIGEST_INVALID", f"{label} is invalid"
        )
    return value


def _invalid(reason_code: str, message: str) -> DomainError:
    return DomainError(
        ErrorCode.INVALID_ARGUMENT,
        message,
        {"reason_code": reason_code},
    )


def _inconsistent(reason_code: str, message: str) -> DomainError:
    return DomainError(
        ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
        message,
        {"reason_code": reason_code},
    )


__all__ = [
    "WORLD_MODEL_EVALUATION_PAGE_FORMAT",
    "read_world_model_evaluation_page",
    "world_model_evaluation_page_envelope",
    "world_model_evaluation_page_payload",
    "write_world_model_evaluation_page",
]
