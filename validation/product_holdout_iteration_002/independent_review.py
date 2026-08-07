"""Independent source-grounded review of an already sealed answer pair."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import json
from pathlib import Path
from typing import Mapping

from software_world_model.application_services import ProductHoldoutCaseComparison
from software_world_model.cross_cutting import Digest, DomainError, ErrorCode, digest_of

from .execution import HoldoutTaskAnswerPair
from .manifest import verify_holdout_suite
from .result_store import write_validation_document_once


INDEPENDENT_REVIEW_SCHEMA = "swm.product-holdout-independent-review@1"
INDEPENDENT_REVIEW_DRAFT_SCHEMA = (
    "swm.product-holdout-independent-review-draft@1"
)


class DimensionStatus(str, Enum):
    CORRECT_COMPLETE = "CORRECT_COMPLETE"
    CORRECT_PARTIAL = "CORRECT_PARTIAL"
    ABSENT = "ABSENT"
    INCORRECT = "INCORRECT"


@dataclass(frozen=True, slots=True)
class DimensionAssessment:
    dimension: str
    direct_status: DimensionStatus
    world_status: DimensionStatus
    finding: str

    def __post_init__(self) -> None:
        _text(self.dimension, "acceptance dimension")
        _text(self.finding, "dimension review finding")
        if not isinstance(self.direct_status, DimensionStatus) or not isinstance(
            self.world_status, DimensionStatus
        ):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "dimension review status is invalid",
            )


@dataclass(frozen=True, slots=True)
class IndependentCaseReview:
    schema: str
    review_ref: str
    suite_id: str
    suite_version: str
    suite_digest: Digest
    task_id: str
    pair_digest: Digest
    direct_result_digest: Digest
    world_result_digest: Digest
    direct_origin: str
    world_origin: str
    actual_model_fingerprint: str
    evaluator_identity: str
    evaluator_origin: str
    review_method: str
    assessments: tuple[DimensionAssessment, ...]
    direct_correctness_milli: int
    world_correctness_milli: int
    direct_completion_milli: int
    world_completion_milli: int
    material_error_count: int
    findings: tuple[str, ...]
    reviewed_at: datetime
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        suite: Mapping[str, object],
        pair: HoldoutTaskAnswerPair,
        evaluator_identity: str,
        evaluator_origin: str,
        assessments: tuple[DimensionAssessment, ...],
        findings: tuple[str, ...] = (),
        reviewed_at: datetime,
    ) -> "IndependentCaseReview":
        verify_holdout_suite(suite)
        if not pair.direct.verify_digest() or not pair.world_assisted.verify_digest():
            _invalid("independent review requires a valid sealed answer pair")
        task = next(
            (
                item
                for item in suite["tasks"]
                if item["task_id"] == pair.direct.task_id
            ),
            None,
        )
        if task is None:
            _invalid("answer pair task is not in the sealed suite")
        expected_dimensions = tuple(task["acceptance_dimensions"])
        if (
            not isinstance(assessments, tuple)
            or tuple(item.dimension for item in assessments) != expected_dimensions
            or len({item.dimension for item in assessments}) != len(assessments)
        ):
            _invalid(
                "independent review must assess every sealed dimension in order"
            )
        if (
            pair.direct.suite_id != suite["suite_id"]
            or pair.direct.suite_version != suite["suite_version"]
            or pair.direct.suite_digest.value != suite["suite_digest"]
        ):
            _invalid("answer pair does not belong to the sealed suite")
        evaluator = _text(evaluator_origin, "independent evaluator origin")
        if evaluator in {pair.direct.origin, pair.world_assisted.origin}:
            raise DomainError(
                ErrorCode.QUALIFICATION_INVALID,
                "independent evaluator must differ from both answer origins",
            )
        reviewed = _aware_time(reviewed_at)
        direct_correctness, direct_completion, _ = _metrics(
            tuple(item.direct_status for item in assessments)
        )
        world_correctness, world_completion, material_errors = _metrics(
            tuple(item.world_status for item in assessments)
        )
        cleaned_findings = _findings(findings)
        if (
            world_correctness < direct_correctness
            or world_completion < direct_completion
            or material_errors
        ) and not cleaned_findings:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "a regressing or incorrect system answer requires review findings",
            )
        values = {
            "schema": INDEPENDENT_REVIEW_SCHEMA,
            "review_ref": (
                f"independent-product-review:{pair.direct.task_id}:"
                f"{pair.digest.value[-16:]}"
            ),
            "suite_id": pair.direct.suite_id,
            "suite_version": pair.direct.suite_version,
            "suite_digest": pair.direct.suite_digest.value,
            "task_id": pair.direct.task_id,
            "pair_digest": pair.digest.value,
            "direct_result_digest": pair.direct.digest.value,
            "world_result_digest": pair.world_assisted.digest.value,
            "direct_origin": pair.direct.origin,
            "world_origin": pair.world_assisted.origin,
            "actual_model_fingerprint": pair.direct.actual_model_fingerprint,
            "evaluator_identity": _text(
                evaluator_identity, "independent evaluator identity"
            ),
            "evaluator_origin": evaluator,
            "review_method": "INDEPENDENT_SOURCE_GROUNDED_DIMENSION_REVIEW@1",
            "assessments": tuple(
                {
                    "dimension": item.dimension,
                    "direct_status": item.direct_status.value,
                    "world_status": item.world_status.value,
                    "finding": item.finding,
                }
                for item in assessments
            ),
            "direct_correctness_milli": direct_correctness,
            "world_correctness_milli": world_correctness,
            "direct_completion_milli": direct_completion,
            "world_completion_milli": world_completion,
            "material_error_count": material_errors,
            "findings": cleaned_findings,
            "reviewed_at": reviewed,
        }
        return cls(
            schema=INDEPENDENT_REVIEW_SCHEMA,
            review_ref=values["review_ref"],
            suite_id=values["suite_id"],
            suite_version=values["suite_version"],
            suite_digest=pair.direct.suite_digest,
            task_id=values["task_id"],
            pair_digest=pair.digest,
            direct_result_digest=pair.direct.digest,
            world_result_digest=pair.world_assisted.digest,
            direct_origin=pair.direct.origin,
            world_origin=pair.world_assisted.origin,
            actual_model_fingerprint=pair.direct.actual_model_fingerprint,
            evaluator_identity=values["evaluator_identity"],
            evaluator_origin=evaluator,
            review_method=values["review_method"],
            assessments=assessments,
            direct_correctness_milli=direct_correctness,
            world_correctness_milli=world_correctness,
            direct_completion_milli=direct_completion,
            world_completion_milli=world_completion,
            material_error_count=material_errors,
            findings=cleaned_findings,
            reviewed_at=reviewed,
            digest=digest_of(values),
        )

    @property
    def passed(self) -> bool:
        return (
            self.world_correctness_milli >= self.direct_correctness_milli
            and self.world_completion_milli >= self.direct_completion_milli
            and self.material_error_count == 0
        )

    def verify_digest(self) -> bool:
        values = {
            "schema": self.schema,
            "review_ref": self.review_ref,
            "suite_id": self.suite_id,
            "suite_version": self.suite_version,
            "suite_digest": self.suite_digest.value,
            "task_id": self.task_id,
            "pair_digest": self.pair_digest.value,
            "direct_result_digest": self.direct_result_digest.value,
            "world_result_digest": self.world_result_digest.value,
            "direct_origin": self.direct_origin,
            "world_origin": self.world_origin,
            "actual_model_fingerprint": self.actual_model_fingerprint,
            "evaluator_identity": self.evaluator_identity,
            "evaluator_origin": self.evaluator_origin,
            "review_method": self.review_method,
            "assessments": tuple(
                {
                    "dimension": item.dimension,
                    "direct_status": item.direct_status.value,
                    "world_status": item.world_status.value,
                    "finding": item.finding,
                }
                for item in self.assessments
            ),
            "direct_correctness_milli": self.direct_correctness_milli,
            "world_correctness_milli": self.world_correctness_milli,
            "direct_completion_milli": self.direct_completion_milli,
            "world_completion_milli": self.world_completion_milli,
            "material_error_count": self.material_error_count,
            "findings": self.findings,
            "reviewed_at": self.reviewed_at,
        }
        return self.schema == INDEPENDENT_REVIEW_SCHEMA and digest_of(values) == self.digest

    def to_product_comparison(self) -> ProductHoldoutCaseComparison:
        if not self.verify_digest():
            _invalid("independent review digest is invalid")
        return ProductHoldoutCaseComparison.create(
            comparison_ref=self.review_ref,
            case_id=self.task_id,
            direct_output_ref=f"sealed-answer:{self.direct_result_digest.value}",
            direct_output_digest=self.direct_result_digest,
            world_output_ref=f"sealed-answer:{self.world_result_digest.value}",
            world_output_digest=self.world_result_digest,
            direct_origin=self.direct_origin,
            world_origin=self.world_origin,
            evaluator_origin=self.evaluator_origin,
            direct_model_fingerprint=self.actual_model_fingerprint,
            world_model_fingerprint=self.actual_model_fingerprint,
            direct_correctness_milli=self.direct_correctness_milli,
            world_correctness_milli=self.world_correctness_milli,
            direct_completion_milli=self.direct_completion_milli,
            world_completion_milli=self.world_completion_milli,
            material_error_count=self.material_error_count,
            findings=self.findings,
        )


def seal_independent_review_draft(
    draft_path: str | Path,
    *,
    suite: Mapping[str, object],
    pair: HoldoutTaskAnswerPair,
    result_directory: str | Path,
) -> Path:
    try:
        draft = json.loads(Path(draft_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "independent review draft cannot be loaded",
        ) from exc
    required = {
        "schema",
        "suite_digest",
        "task_id",
        "pair_digest",
        "evaluator_identity",
        "evaluator_origin",
        "assessments",
        "findings",
        "reviewed_at",
    }
    if not isinstance(draft, dict) or set(draft) != required:
        _invalid("independent review draft fields are incomplete")
    if (
        draft.get("schema") != INDEPENDENT_REVIEW_DRAFT_SCHEMA
        or draft.get("suite_digest") != pair.direct.suite_digest.value
        or draft.get("task_id") != pair.direct.task_id
        or draft.get("pair_digest") != pair.digest.value
        or not isinstance(draft.get("assessments"), list)
        or not isinstance(draft.get("findings"), list)
    ):
        _invalid("independent review draft is not bound to the sealed answer pair")
    assessments = tuple(_assessment_from_document(item) for item in draft["assessments"])
    try:
        reviewed_at = datetime.fromisoformat(
            str(draft["reviewed_at"]).replace("Z", "+00:00")
        )
    except ValueError as exc:
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            "independent review draft timestamp is invalid",
        ) from exc
    review = IndependentCaseReview.create(
        suite=suite,
        pair=pair,
        evaluator_identity=draft["evaluator_identity"],
        evaluator_origin=draft["evaluator_origin"],
        assessments=assessments,
        findings=tuple(draft["findings"]),
        reviewed_at=reviewed_at,
    )
    return save_independent_review(
        review,
        suite=suite,
        pair=pair,
        result_directory=result_directory,
    )


def save_independent_review(
    review: IndependentCaseReview,
    *,
    suite: Mapping[str, object],
    pair: HoldoutTaskAnswerPair,
    result_directory: str | Path,
) -> Path:
    document = independent_review_document(review, suite=suite, pair=pair)
    target = Path(result_directory) / f"{review.task_id}--independent-review.json"
    write_validation_document_once(target, document)
    if load_independent_review(target, suite=suite, pair=pair) != review:
        _invalid("persisted independent review does not match the sealed review")
    return target


def load_independent_review(
    path: str | Path,
    *,
    suite: Mapping[str, object],
    pair: HoldoutTaskAnswerPair,
) -> IndependentCaseReview:
    try:
        document = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "sealed independent review cannot be loaded",
        ) from exc
    required = {
        "schema",
        "suite_digest",
        "task_id",
        "pair_digest",
        "evaluator_identity",
        "evaluator_origin",
        "assessments",
        "findings",
        "reviewed_at",
        "review_ref",
        "metrics",
        "review_digest",
        "document_digest",
    }
    if not isinstance(document, dict) or set(document) != required:
        _invalid("sealed independent review fields are incomplete")
    core = {key: value for key, value in document.items() if key != "document_digest"}
    if (
        document.get("schema") != INDEPENDENT_REVIEW_SCHEMA
        or document.get("document_digest") != digest_of(core).value
        or not isinstance(document.get("assessments"), list)
        or not isinstance(document.get("findings"), list)
        or not isinstance(document.get("metrics"), dict)
    ):
        _invalid("sealed independent review digest is invalid")
    assessments = tuple(
        _assessment_from_document(item) for item in document["assessments"]
    )
    try:
        reviewed_at = datetime.fromisoformat(
            str(document["reviewed_at"]).replace("Z", "+00:00")
        )
    except ValueError as exc:
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "sealed independent review timestamp is invalid",
        ) from exc
    review = IndependentCaseReview.create(
        suite=suite,
        pair=pair,
        evaluator_identity=document["evaluator_identity"],
        evaluator_origin=document["evaluator_origin"],
        assessments=assessments,
        findings=tuple(document["findings"]),
        reviewed_at=reviewed_at,
    )
    metrics = document["metrics"]
    if (
        document["suite_digest"] != review.suite_digest.value
        or document["task_id"] != review.task_id
        or document["pair_digest"] != review.pair_digest.value
        or document["review_ref"] != review.review_ref
        or document["review_digest"] != review.digest.value
        or metrics
        != {
            "direct_correctness_milli": review.direct_correctness_milli,
            "world_correctness_milli": review.world_correctness_milli,
            "direct_completion_milli": review.direct_completion_milli,
            "world_completion_milli": review.world_completion_milli,
            "material_error_count": review.material_error_count,
            "passed": review.passed,
        }
    ):
        _invalid("sealed independent review is inconsistent")
    return review


def independent_review_document(
    review: IndependentCaseReview,
    *,
    suite: Mapping[str, object],
    pair: HoldoutTaskAnswerPair,
) -> dict[str, object]:
    verify_holdout_suite(suite)
    if (
        not review.verify_digest()
        or review.suite_digest != pair.direct.suite_digest
        or review.task_id != pair.direct.task_id
        or review.pair_digest != pair.digest
    ):
        _invalid("independent review is not bound to the sealed suite and pair")
    core = {
        "schema": INDEPENDENT_REVIEW_SCHEMA,
        "suite_digest": review.suite_digest.value,
        "task_id": review.task_id,
        "pair_digest": review.pair_digest.value,
        "evaluator_identity": review.evaluator_identity,
        "evaluator_origin": review.evaluator_origin,
        "assessments": [
            {
                "dimension": item.dimension,
                "direct_status": item.direct_status.value,
                "world_status": item.world_status.value,
                "finding": item.finding,
            }
            for item in review.assessments
        ],
        "findings": list(review.findings),
        "reviewed_at": review.reviewed_at.isoformat(),
        "review_ref": review.review_ref,
        "metrics": {
            "direct_correctness_milli": review.direct_correctness_milli,
            "world_correctness_milli": review.world_correctness_milli,
            "direct_completion_milli": review.direct_completion_milli,
            "world_completion_milli": review.world_completion_milli,
            "material_error_count": review.material_error_count,
            "passed": review.passed,
        },
        "review_digest": review.digest.value,
    }
    return {**core, "document_digest": digest_of(core).value}


def _assessment_from_document(value: object) -> DimensionAssessment:
    if (
        not isinstance(value, dict)
        or set(value)
        != {"dimension", "direct_status", "world_status", "finding"}
    ):
        _invalid("independent dimension assessment is invalid")
    try:
        return DimensionAssessment(
            dimension=value["dimension"],
            direct_status=DimensionStatus(value["direct_status"]),
            world_status=DimensionStatus(value["world_status"]),
            finding=value["finding"],
        )
    except (TypeError, ValueError) as exc:
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            "independent dimension assessment value is invalid",
        ) from exc


def _metrics(statuses: tuple[DimensionStatus, ...]) -> tuple[int, int, int]:
    correctness = {
        DimensionStatus.CORRECT_COMPLETE: 1000,
        DimensionStatus.CORRECT_PARTIAL: 1000,
        DimensionStatus.ABSENT: 1000,
        DimensionStatus.INCORRECT: 0,
    }
    completion = {
        DimensionStatus.CORRECT_COMPLETE: 1000,
        DimensionStatus.CORRECT_PARTIAL: 500,
        DimensionStatus.ABSENT: 0,
        DimensionStatus.INCORRECT: 1000,
    }
    count = len(statuses)
    if count < 1:
        _invalid("independent review has no acceptance dimensions")
    return (
        sum(correctness[item] for item in statuses) // count,
        sum(completion[item] for item in statuses) // count,
        sum(item is DimensionStatus.INCORRECT for item in statuses),
    )


def _findings(values: tuple[str, ...]) -> tuple[str, ...]:
    if not isinstance(values, tuple):
        raise DomainError(ErrorCode.INVALID_ARGUMENT, "review findings must be a tuple")
    return tuple(_text(item, "review finding") for item in values)


def _aware_time(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT, "review timestamp must be timezone-aware"
        )
    return value.astimezone(timezone.utc)


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} must be non-empty")
    return value


def _invalid(message: str) -> None:
    raise DomainError(ErrorCode.AUTHORITY_RECORD_INCONSISTENT, message)
