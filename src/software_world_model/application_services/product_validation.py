"""Product holdout attestations required in addition to model capability evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Callable, Protocol

from software_world_model.cross_cutting import (
    Digest,
    DomainError,
    ErrorCode,
    IdempotencyKey,
    StableId,
    digest_of,
)

from .activation import QualificationProof, QualificationVerifier


@dataclass(frozen=True, slots=True)
class ProductHoldoutCaseComparison:
    comparison_ref: str
    case_id: str
    direct_output_ref: str
    direct_output_digest: Digest
    world_output_ref: str
    world_output_digest: Digest
    direct_origin: str
    world_origin: str
    evaluator_origin: str
    direct_model_fingerprint: str
    world_model_fingerprint: str
    direct_correctness_milli: int
    world_correctness_milli: int
    direct_completion_milli: int
    world_completion_milli: int
    material_error_count: int
    findings: tuple[str, ...]
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        comparison_ref: str,
        case_id: str,
        direct_output_ref: str,
        direct_output_digest: Digest,
        world_output_ref: str,
        world_output_digest: Digest,
        direct_origin: str,
        world_origin: str,
        evaluator_origin: str,
        direct_model_fingerprint: str,
        world_model_fingerprint: str,
        direct_correctness_milli: int,
        world_correctness_milli: int,
        direct_completion_milli: int,
        world_completion_milli: int,
        material_error_count: int,
        findings: tuple[str, ...] = (),
    ) -> "ProductHoldoutCaseComparison":
        direct = _text(direct_origin, "direct answer origin")
        world = _text(world_origin, "world answer origin")
        evaluator = _text(evaluator_origin, "comparison evaluator origin")
        if len({direct, world, evaluator}) != 3:
            raise DomainError(
                ErrorCode.QUALIFICATION_INVALID,
                "product comparison requires distinct direct, world, and evaluator origins",
            )
        direct_model = _text(
            direct_model_fingerprint, "direct model fingerprint"
        )
        world_model = _text(
            world_model_fingerprint, "world model fingerprint"
        )
        if direct_model != world_model:
            raise DomainError(
                ErrorCode.QUALIFICATION_INVALID,
                "product comparison must use the same model for direct and world answers",
            )
        values = {
            "comparison_ref": _text(comparison_ref, "comparison reference"),
            "case_id": _text(case_id, "holdout case ID"),
            "direct_output_ref": _text(
                direct_output_ref, "direct output reference"
            ),
            "direct_output_digest": direct_output_digest.value,
            "world_output_ref": _text(world_output_ref, "world output reference"),
            "world_output_digest": world_output_digest.value,
            "direct_origin": direct,
            "world_origin": world,
            "evaluator_origin": evaluator,
            "direct_model_fingerprint": direct_model,
            "world_model_fingerprint": world_model,
            "direct_correctness_milli": _metric(
                direct_correctness_milli, "direct correctness"
            ),
            "world_correctness_milli": _metric(
                world_correctness_milli, "world correctness"
            ),
            "direct_completion_milli": _metric(
                direct_completion_milli, "direct completion"
            ),
            "world_completion_milli": _metric(
                world_completion_milli, "world completion"
            ),
            "material_error_count": _nonnegative(
                material_error_count, "material error count"
            ),
            "findings": _text_tuple(findings, "comparison findings"),
        }
        passed = (
            values["world_correctness_milli"]
            >= values["direct_correctness_milli"]
            and values["world_completion_milli"]
            >= values["direct_completion_milli"]
            and values["material_error_count"] == 0
        )
        if not passed and not values["findings"]:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "a regressing product comparison requires findings",
            )
        return cls(
            comparison_ref=values["comparison_ref"],
            case_id=values["case_id"],
            direct_output_ref=values["direct_output_ref"],
            direct_output_digest=direct_output_digest,
            world_output_ref=values["world_output_ref"],
            world_output_digest=world_output_digest,
            direct_origin=direct,
            world_origin=world,
            evaluator_origin=evaluator,
            direct_model_fingerprint=direct_model,
            world_model_fingerprint=world_model,
            direct_correctness_milli=values["direct_correctness_milli"],
            world_correctness_milli=values["world_correctness_milli"],
            direct_completion_milli=values["direct_completion_milli"],
            world_completion_milli=values["world_completion_milli"],
            material_error_count=values["material_error_count"],
            findings=values["findings"],
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
        return digest_of(
            {
                "comparison_ref": self.comparison_ref,
                "case_id": self.case_id,
                "direct_output_ref": self.direct_output_ref,
                "direct_output_digest": self.direct_output_digest.value,
                "world_output_ref": self.world_output_ref,
                "world_output_digest": self.world_output_digest.value,
                "direct_origin": self.direct_origin,
                "world_origin": self.world_origin,
                "evaluator_origin": self.evaluator_origin,
                "direct_model_fingerprint": self.direct_model_fingerprint,
                "world_model_fingerprint": self.world_model_fingerprint,
                "direct_correctness_milli": self.direct_correctness_milli,
                "world_correctness_milli": self.world_correctness_milli,
                "direct_completion_milli": self.direct_completion_milli,
                "world_completion_milli": self.world_completion_milli,
                "material_error_count": self.material_error_count,
                "findings": self.findings,
            }
        ) == self.digest


@dataclass(frozen=True, slots=True)
class ProductValidationAttestation:
    attestation_id: StableId
    capability_id: str
    capability_contract_version: str
    strategy_id: str
    strategy_version: str
    strategy_implementation_digest: Digest
    qualification_digest: Digest
    holdout_suite_ref: str
    holdout_suite_digest: Digest
    case_ids: tuple[str, ...]
    direct_result_digest: Digest
    world_result_digest: Digest
    comparison_digest: Digest
    direct_origin: str
    world_origin: str
    evaluator_origin: str
    direct_correctness_milli: int
    world_correctness_milli: int
    direct_completion_milli: int
    world_completion_milli: int
    material_error_count: int
    recorded_at: datetime
    valid_until: datetime
    digest: Digest

    def core(self) -> dict[str, object]:
        return {
            "attestation_id": self.attestation_id.value,
            "capability_id": self.capability_id,
            "capability_contract_version": self.capability_contract_version,
            "strategy_id": self.strategy_id,
            "strategy_version": self.strategy_version,
            "strategy_implementation_digest": self.strategy_implementation_digest.value,
            "qualification_digest": self.qualification_digest.value,
            "holdout_suite_ref": self.holdout_suite_ref,
            "holdout_suite_digest": self.holdout_suite_digest.value,
            "case_ids": self.case_ids,
            "direct_result_digest": self.direct_result_digest.value,
            "world_result_digest": self.world_result_digest.value,
            "comparison_digest": self.comparison_digest.value,
            "direct_origin": self.direct_origin,
            "world_origin": self.world_origin,
            "evaluator_origin": self.evaluator_origin,
            "direct_correctness_milli": self.direct_correctness_milli,
            "world_correctness_milli": self.world_correctness_milli,
            "direct_completion_milli": self.direct_completion_milli,
            "world_completion_milli": self.world_completion_milli,
            "material_error_count": self.material_error_count,
            "recorded_at": self.recorded_at,
            "valid_until": self.valid_until,
        }

    def verify_digest(self) -> bool:
        return digest_of(self.core()) == self.digest


class ProductValidationRepository(Protocol):
    def save(
        self,
        *,
        idempotency_key: IdempotencyKey,
        request_digest: Digest,
        attestation: ProductValidationAttestation,
    ) -> ProductValidationAttestation: ...

    def has_current_pass(
        self,
        *,
        qualification: QualificationProof,
        strategy_implementation_digest: Digest,
        at: datetime,
    ) -> bool: ...


class ProductValidationService:
    def __init__(
        self,
        repository: ProductValidationRepository,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._repository = repository
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def record_reviewed_holdout(
        self,
        *,
        idempotency_key: IdempotencyKey,
        qualification: QualificationProof,
        strategy_implementation_digest: Digest,
        holdout_suite_ref: str,
        holdout_suite_digest: Digest,
        comparisons: tuple[ProductHoldoutCaseComparison, ...],
        valid_for_seconds: int,
    ) -> ProductValidationAttestation:
        if (
            not isinstance(comparisons, tuple)
            or not comparisons
            or any(not item.verify_digest() for item in comparisons)
            or len({item.case_id for item in comparisons}) != len(comparisons)
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "product holdout comparisons are incomplete, duplicated, or invalid",
            )
        direct_origins = {item.direct_origin for item in comparisons}
        world_origins = {item.world_origin for item in comparisons}
        evaluator_origins = {item.evaluator_origin for item in comparisons}
        if (
            len(direct_origins) != 1
            or len(world_origins) != 1
            or len(evaluator_origins) != 1
        ):
            raise DomainError(
                ErrorCode.QUALIFICATION_INVALID,
                "one holdout suite must use stable answer and evaluator origins",
            )
        if any(not item.passed for item in comparisons):
            raise DomainError(
                ErrorCode.QUALIFICATION_INVALID,
                "at least one holdout case regressed from the direct-answer baseline",
            )
        count = len(comparisons)
        return self.record_pass(
            idempotency_key=idempotency_key,
            qualification=qualification,
            strategy_implementation_digest=strategy_implementation_digest,
            holdout_suite_ref=holdout_suite_ref,
            holdout_suite_digest=holdout_suite_digest,
            case_ids=tuple(item.case_id for item in comparisons),
            direct_result_digest=digest_of(
                tuple(
                    (
                        item.case_id,
                        item.direct_output_ref,
                        item.direct_output_digest.value,
                        item.direct_origin,
                        item.direct_model_fingerprint,
                    )
                    for item in comparisons
                )
            ),
            world_result_digest=digest_of(
                tuple(
                    (
                        item.case_id,
                        item.world_output_ref,
                        item.world_output_digest.value,
                        item.world_origin,
                        item.world_model_fingerprint,
                    )
                    for item in comparisons
                )
            ),
            comparison_digest=digest_of(
                tuple(item.digest.value for item in comparisons)
            ),
            direct_origin=next(iter(direct_origins)),
            world_origin=next(iter(world_origins)),
            evaluator_origin=next(iter(evaluator_origins)),
            direct_correctness_milli=(
                sum(item.direct_correctness_milli for item in comparisons) // count
            ),
            world_correctness_milli=(
                sum(item.world_correctness_milli for item in comparisons) // count
            ),
            direct_completion_milli=(
                sum(item.direct_completion_milli for item in comparisons) // count
            ),
            world_completion_milli=(
                sum(item.world_completion_milli for item in comparisons) // count
            ),
            material_error_count=sum(
                item.material_error_count for item in comparisons
            ),
            valid_for_seconds=valid_for_seconds,
        )

    def record_pass(
        self,
        *,
        idempotency_key: IdempotencyKey,
        qualification: QualificationProof,
        strategy_implementation_digest: Digest,
        holdout_suite_ref: str,
        holdout_suite_digest: Digest,
        case_ids: tuple[str, ...],
        direct_result_digest: Digest,
        world_result_digest: Digest,
        comparison_digest: Digest,
        direct_origin: str,
        world_origin: str,
        evaluator_origin: str,
        direct_correctness_milli: int,
        world_correctness_milli: int,
        direct_completion_milli: int,
        world_completion_milli: int,
        material_error_count: int,
        valid_for_seconds: int,
    ) -> ProductValidationAttestation:
        for value, label in (
            (holdout_suite_ref, "holdout suite reference"),
            (direct_origin, "direct answer origin"),
            (world_origin, "world answer origin"),
            (evaluator_origin, "evaluator origin"),
        ):
            _text(value, label)
        if not qualification.verify_digest():
            raise DomainError(
                ErrorCode.QUALIFICATION_INVALID,
                "product validation must bind a valid capability evaluation proof",
            )
        if (
            evaluator_origin in {direct_origin, world_origin}
            or direct_origin == world_origin
        ):
            raise DomainError(
                ErrorCode.QUALIFICATION_INVALID,
                "product comparison evaluator must be independent from both answer origins",
            )
        if (
            not isinstance(case_ids, tuple)
            or not case_ids
            or any(
                not isinstance(case_id, str)
                or not case_id
                or case_id != case_id.strip()
                for case_id in case_ids
            )
            or len(set(case_ids)) != len(case_ids)
        ):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "product holdout must contain unique non-empty case IDs",
            )
        metrics = (
            direct_correctness_milli,
            world_correctness_milli,
            direct_completion_milli,
            world_completion_milli,
        )
        if any(
            isinstance(value, bool)
            or not isinstance(value, int)
            or not 0 <= value <= 1000
            for value in metrics
        ):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "product metrics must be integer thousandths between 0 and 1000",
            )
        if (
            isinstance(material_error_count, bool)
            or not isinstance(material_error_count, int)
            or material_error_count < 0
        ):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "material error count must be a non-negative integer",
            )
        if (
            world_correctness_milli < direct_correctness_milli
            or world_completion_milli < direct_completion_milli
            or material_error_count != 0
        ):
            raise DomainError(
                ErrorCode.QUALIFICATION_INVALID,
                "product holdout did not meet the direct-answer baseline",
            )
        if (
            isinstance(valid_for_seconds, bool)
            or not isinstance(valid_for_seconds, int)
            or valid_for_seconds < 1
        ):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "product validation duration must be positive",
            )
        recorded_at = self._now()
        valid_until = recorded_at + timedelta(seconds=valid_for_seconds)
        identity = digest_of(
            {
                "qualification_digest": qualification.digest.value,
                "strategy_implementation_digest": strategy_implementation_digest.value,
                "holdout_suite_digest": holdout_suite_digest.value,
                "comparison_digest": comparison_digest.value,
            }
        )
        attestation_id = StableId(
            f"product_validation_{identity.value[-32:]}"
        )
        values = {
            "attestation_id": attestation_id,
            "capability_id": qualification.capability_id,
            "capability_contract_version": qualification.capability_contract_version,
            "strategy_id": qualification.strategy_id,
            "strategy_version": qualification.strategy_version,
            "strategy_implementation_digest": strategy_implementation_digest,
            "qualification_digest": qualification.digest,
            "holdout_suite_ref": holdout_suite_ref,
            "holdout_suite_digest": holdout_suite_digest,
            "case_ids": case_ids,
            "direct_result_digest": direct_result_digest,
            "world_result_digest": world_result_digest,
            "comparison_digest": comparison_digest,
            "direct_origin": direct_origin,
            "world_origin": world_origin,
            "evaluator_origin": evaluator_origin,
            "direct_correctness_milli": direct_correctness_milli,
            "world_correctness_milli": world_correctness_milli,
            "direct_completion_milli": direct_completion_milli,
            "world_completion_milli": world_completion_milli,
            "material_error_count": material_error_count,
            "recorded_at": recorded_at,
            "valid_until": valid_until,
        }
        candidate = ProductValidationAttestation(
            **values,
            digest=digest_of(
                {
                    **values,
                    "attestation_id": attestation_id.value,
                    "strategy_implementation_digest": strategy_implementation_digest.value,
                    "qualification_digest": qualification.digest.value,
                    "holdout_suite_digest": holdout_suite_digest.value,
                    "direct_result_digest": direct_result_digest.value,
                    "world_result_digest": world_result_digest.value,
                    "comparison_digest": comparison_digest.value,
                }
            ),
        )
        request_digest = digest_of(
            {
                "command": "RecordProductValidationPass@1",
                "qualification_digest": qualification.digest.value,
                "strategy_implementation_digest": strategy_implementation_digest.value,
                "holdout_suite_ref": holdout_suite_ref,
                "holdout_suite_digest": holdout_suite_digest.value,
                "case_ids": case_ids,
                "direct_result_digest": direct_result_digest.value,
                "world_result_digest": world_result_digest.value,
                "comparison_digest": comparison_digest.value,
                "direct_origin": direct_origin,
                "world_origin": world_origin,
                "evaluator_origin": evaluator_origin,
                "direct_correctness_milli": direct_correctness_milli,
                "world_correctness_milli": world_correctness_milli,
                "direct_completion_milli": direct_completion_milli,
                "world_completion_milli": world_completion_milli,
                "material_error_count": material_error_count,
                "valid_for_seconds": valid_for_seconds,
            }
        )
        return self._repository.save(
            idempotency_key=idempotency_key,
            request_digest=request_digest,
            attestation=candidate,
        )

    def _now(self) -> datetime:
        value = self._clock()
        if value.tzinfo is None or value.utcoffset() is None:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "product validation clock must be timezone-aware",
            )
        return value.astimezone(timezone.utc)


class ProductValidatedQualificationVerifier:
    """Require both a current model evaluation and a current product holdout pass."""

    def __init__(
        self,
        evaluation_verifier: QualificationVerifier,
        repository: ProductValidationRepository,
        strategy_implementation_digest: Digest,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._evaluation = evaluation_verifier
        self._repository = repository
        self._implementation = strategy_implementation_digest
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def validate(self, proof: QualificationProof) -> bool:
        now = self._clock()
        if now.tzinfo is None or now.utcoffset() is None:
            return False
        return self._evaluation.validate(proof) and self._repository.has_current_pass(
            qualification=proof,
            strategy_implementation_digest=self._implementation,
            at=now.astimezone(timezone.utc),
        )


def _text(value: str, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} must be non-empty")
    return value


def _metric(value: int, label: str) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 1000
    ):
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            f"{label} must be integer thousandths between 0 and 1000",
        )
    return value


def _nonnegative(value: int, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            f"{label} must be a non-negative integer",
        )
    return value


def _text_tuple(value: tuple[str, ...], label: str) -> tuple[str, ...]:
    if (
        not isinstance(value, tuple)
        or any(
            not isinstance(item, str)
            or not item
            or item != item.strip()
            for item in value
        )
        or len(set(value)) != len(value)
    ):
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            f"{label} must be unique non-empty text values",
        )
    return value
