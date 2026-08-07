"""Seal Codex-authored reviews of live capability case outputs."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Mapping

from software_world_model.ai_infrastructure import AgenticEvaluationReview
from software_world_model.cross_cutting import (
    Digest,
    DomainError,
    ErrorCode,
    digest_of,
)

from .live_runner import (
    load_capability_output_document,
    verify_capability_output_against_suite,
    write_capability_document_once,
)
from .manifest import verify_capability_suite


CAPABILITY_REVIEW_DRAFT_SCHEMA = "swm.agentic-capability-review-draft@1"
CAPABILITY_REVIEW_DOCUMENT_SCHEMA = "swm.agentic-capability-review@1"


def seal_capability_review_draft(
    draft_path: str | Path,
    *,
    output_path: str | Path,
    suite: Mapping[str, object],
    result_directory: str | Path,
) -> Path:
    verify_capability_suite(suite)
    output, output_document = load_capability_output_document(output_path)
    verify_capability_output_against_suite(output, output_document, suite)
    try:
        draft = json.loads(Path(draft_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "capability review draft cannot be loaded",
        ) from exc
    required = {
        "schema",
        "suite_digest",
        "case_id",
        "output_digest",
        "reviewer_identity",
        "reviewer_origin",
        "platform_contract_valid",
        "oracle_match",
        "unauthorized_reference_count",
        "material_omission_count",
        "material_error_count",
        "findings",
        "reviewed_at",
    }
    if (
        not isinstance(draft, dict)
        or set(draft) != required
        or draft.get("schema") != CAPABILITY_REVIEW_DRAFT_SCHEMA
        or draft.get("suite_digest") != suite["suite_digest"]
        or draft.get("case_id") != output.case_id
        or draft.get("output_digest") != output.output_digest.value
        or not isinstance(draft.get("findings"), list)
    ):
        _invalid("capability review draft is not bound to the sealed output")
    reviewed_at = _parse_time(draft["reviewed_at"])
    review = AgenticEvaluationReview.create(
        review_ref=f"codex-capability-review:{output.case_id}:{output.digest.value}",
        case_id=output.case_id,
        output_digest=output.output_digest,
        oracle_ref=output_document["oracle_ref"],
        oracle_digest=Digest(output_document["oracle_digest"]),
        generator_origin=output.generator_origin,
        reviewer_origin=draft["reviewer_origin"],
        platform_contract_valid=draft["platform_contract_valid"],
        oracle_match=draft["oracle_match"],
        unauthorized_reference_count=draft["unauthorized_reference_count"],
        material_omission_count=draft["material_omission_count"],
        material_error_count=draft["material_error_count"],
        findings=tuple(draft["findings"]),
    )
    core = {
        "schema": CAPABILITY_REVIEW_DOCUMENT_SCHEMA,
        "suite_digest": suite["suite_digest"],
        "case_id": output.case_id,
        "output_document_digest": output_document["document_digest"],
        "reviewer_identity": _text(
            draft["reviewer_identity"], "capability reviewer identity"
        ),
        "reviewer_origin": review.reviewer_origin,
        "reviewed_at": reviewed_at.isoformat(),
        "review": _review_document(review),
    }
    document = {**core, "document_digest": digest_of(core).value}
    target = Path(result_directory) / f"{output.case_id.replace(':', '--')}--review.json"
    _write_same_or_new(target, document)
    loaded, _ = load_capability_review_document(
        target, output_path=output_path, suite=suite
    )
    if loaded != review:
        _invalid("sealed capability review cannot be recovered")
    return target


def load_capability_review_document(
    path: str | Path,
    *,
    output_path: str | Path,
    suite: Mapping[str, object],
) -> tuple[AgenticEvaluationReview, dict[str, object]]:
    verify_capability_suite(suite)
    output, output_document = load_capability_output_document(output_path)
    verify_capability_output_against_suite(output, output_document, suite)
    try:
        document = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "capability review document cannot be loaded",
        ) from exc
    required = {
        "schema",
        "suite_digest",
        "case_id",
        "output_document_digest",
        "reviewer_identity",
        "reviewer_origin",
        "reviewed_at",
        "review",
        "document_digest",
    }
    if not isinstance(document, dict) or set(document) != required:
        _invalid("capability review document fields are invalid")
    core = {key: value for key, value in document.items() if key != "document_digest"}
    if (
        document.get("schema") != CAPABILITY_REVIEW_DOCUMENT_SCHEMA
        or document.get("suite_digest") != suite["suite_digest"]
        or document.get("case_id") != output.case_id
        or document.get("output_document_digest")
        != output_document["document_digest"]
        or document.get("document_digest") != digest_of(core).value
        or not isinstance(document.get("review"), dict)
    ):
        _invalid("capability review document digest is invalid")
    _parse_time(document["reviewed_at"])
    raw = document["review"]
    try:
        review = AgenticEvaluationReview(
            review_ref=raw["review_ref"],
            case_id=raw["case_id"],
            output_digest=Digest(raw["output_digest"]),
            oracle_ref=raw["oracle_ref"],
            oracle_digest=Digest(raw["oracle_digest"]),
            generator_origin=raw["generator_origin"],
            reviewer_origin=raw["reviewer_origin"],
            platform_contract_valid=raw["platform_contract_valid"],
            oracle_match=raw["oracle_match"],
            unauthorized_reference_count=raw["unauthorized_reference_count"],
            material_omission_count=raw["material_omission_count"],
            material_error_count=raw["material_error_count"],
            findings=tuple(raw["findings"]),
            digest=Digest(raw["digest"]),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "capability review values are invalid",
        ) from exc
    if (
        not review.verify_digest()
        or review.case_id != output.case_id
        or review.output_digest != output.output_digest
        or review.generator_origin != output.generator_origin
        or document["reviewer_origin"] != review.reviewer_origin
        or review.oracle_ref != output_document["oracle_ref"]
        or review.oracle_digest.value != output_document["oracle_digest"]
    ):
        _invalid("capability review is inconsistent with its output and oracle")
    return review, document


def _review_document(review: AgenticEvaluationReview) -> dict[str, object]:
    return {
        "review_ref": review.review_ref,
        "case_id": review.case_id,
        "output_digest": review.output_digest.value,
        "oracle_ref": review.oracle_ref,
        "oracle_digest": review.oracle_digest.value,
        "generator_origin": review.generator_origin,
        "reviewer_origin": review.reviewer_origin,
        "platform_contract_valid": review.platform_contract_valid,
        "oracle_match": review.oracle_match,
        "unauthorized_reference_count": review.unauthorized_reference_count,
        "material_omission_count": review.material_omission_count,
        "material_error_count": review.material_error_count,
        "findings": list(review.findings),
        "digest": review.digest.value,
    }


def _write_same_or_new(path: Path, document: Mapping[str, object]) -> None:
    write_capability_document_once(path, document)


def _parse_time(value: object) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError as exc:
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            "capability review timestamp is invalid",
        ) from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            "capability review timestamp must be timezone-aware",
        )
    return parsed.astimezone(timezone.utc)


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} must be non-empty")
    return value


def _invalid(message: str) -> None:
    raise DomainError(ErrorCode.AUTHORITY_RECORD_INCONSISTENT, message)
