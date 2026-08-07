"""Immutable answer-path results for the sealed product validation suite."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping

from software_world_model.cross_cutting import Digest, DomainError, ErrorCode, digest_of


class HoldoutAnswerPath(str, Enum):
    DIRECT = "DIRECT"
    WORLD_ASSISTED = "WORLD_ASSISTED"


@dataclass(frozen=True, slots=True)
class SealedAnswerClaim:
    claim: str
    support_references: tuple[str, ...]

    def __post_init__(self) -> None:
        _text(self.claim, "answer claim")
        _text_tuple(self.support_references, "claim support references")


@dataclass(frozen=True, slots=True)
class HoldoutPathResult:
    result_ref: str
    run_id: str
    path: HoldoutAnswerPath
    origin: str
    implementation_digest: Digest
    suite_id: str
    suite_version: str
    suite_digest: Digest
    task_id: str
    task_input_digest: Digest
    resource_policy_digest: Digest
    answer: str
    claims: tuple[SealedAnswerClaim, ...]
    output_digest: Digest
    actual_model_fingerprint: str
    provider_request_ids: tuple[str, ...]
    model_call_count: int
    source_action_count: int
    source_byte_count: int
    input_tokens: int
    output_tokens: int
    usage_complete: bool
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        result_ref: str,
        run_id: str,
        path: HoldoutAnswerPath,
        origin: str,
        implementation_digest: Digest,
        task_input: Mapping[str, object],
        answer: str,
        claims: tuple[SealedAnswerClaim, ...],
        actual_model_fingerprint: str,
        provider_request_ids: tuple[str, ...],
        model_call_count: int,
        source_action_count: int,
        source_byte_count: int,
        input_tokens: int,
        output_tokens: int,
        usage_complete: bool,
    ) -> "HoldoutPathResult":
        if not isinstance(path, HoldoutAnswerPath):
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "answer path is invalid")
        _verify_task_input(task_input)
        resource_policy = task_input["resource_policy"]
        counts = {
            "model_call_count": _nonnegative(model_call_count, "model call count"),
            "source_action_count": _nonnegative(
                source_action_count, "source action count"
            ),
            "source_byte_count": _nonnegative(source_byte_count, "source byte count"),
            "input_tokens": _nonnegative(input_tokens, "input token count"),
            "output_tokens": _nonnegative(output_tokens, "output token count"),
        }
        if counts["model_call_count"] < 1:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "an answer result must contain at least one model call",
            )
        if counts["model_call_count"] != len(provider_request_ids):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "every answer model call must have one provider request identity",
            )
        provider_ids = _text_tuple(provider_request_ids, "provider request IDs")
        if len(set(provider_ids)) != len(provider_ids):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "provider request identities must be unique within an answer path",
            )
        if not isinstance(usage_complete, bool) or not usage_complete:
            raise DomainError(
                ErrorCode.QUALIFICATION_INVALID,
                "answer path usage must be complete",
            )
        if not isinstance(claims, tuple) or not claims:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT, "answer path must contain source-bound claims"
            )
        answer_text = _text(answer, "answer text")
        if answer_text != "\n".join(item.claim for item in claims):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "answer text must be the exact ordered claim text",
            )
        _verify_limits(counts, resource_policy)
        output_digest = digest_of(
            {
                "answer": answer_text,
                "claims": tuple(
                    (item.claim, item.support_references) for item in claims
                ),
            }
        )
        values = {
            "result_ref": _text(result_ref, "answer result reference"),
            "run_id": _text(run_id, "answer run ID"),
            "path": path.value,
            "origin": _text(origin, "answer origin"),
            "implementation_digest": implementation_digest.value,
            "suite_id": task_input["suite_id"],
            "suite_version": task_input["suite_version"],
            "suite_digest": task_input["suite_digest"],
            "task_id": task_input["task_id"],
            "task_input_digest": task_input["task_input_digest"],
            "resource_policy_digest": digest_of(resource_policy).value,
            "answer": answer_text,
            "claims": tuple(
                (item.claim, item.support_references) for item in claims
            ),
            "output_digest": output_digest.value,
            "actual_model_fingerprint": _text(
                actual_model_fingerprint, "actual model fingerprint"
            ),
            "provider_request_ids": provider_ids,
            **counts,
            "usage_complete": usage_complete,
        }
        return cls(
            result_ref=values["result_ref"],
            run_id=values["run_id"],
            path=path,
            origin=values["origin"],
            implementation_digest=implementation_digest,
            suite_id=values["suite_id"],
            suite_version=values["suite_version"],
            suite_digest=Digest(values["suite_digest"]),
            task_id=values["task_id"],
            task_input_digest=Digest(values["task_input_digest"]),
            resource_policy_digest=Digest(values["resource_policy_digest"]),
            answer=answer_text,
            claims=claims,
            output_digest=output_digest,
            actual_model_fingerprint=values["actual_model_fingerprint"],
            provider_request_ids=provider_ids,
            model_call_count=counts["model_call_count"],
            source_action_count=counts["source_action_count"],
            source_byte_count=counts["source_byte_count"],
            input_tokens=counts["input_tokens"],
            output_tokens=counts["output_tokens"],
            usage_complete=usage_complete,
            digest=digest_of(values),
        )

    def verify_digest(self) -> bool:
        values = {
            "result_ref": self.result_ref,
            "run_id": self.run_id,
            "path": self.path.value,
            "origin": self.origin,
            "implementation_digest": self.implementation_digest.value,
            "suite_id": self.suite_id,
            "suite_version": self.suite_version,
            "suite_digest": self.suite_digest.value,
            "task_id": self.task_id,
            "task_input_digest": self.task_input_digest.value,
            "resource_policy_digest": self.resource_policy_digest.value,
            "answer": self.answer,
            "claims": tuple(
                (item.claim, item.support_references) for item in self.claims
            ),
            "output_digest": self.output_digest.value,
            "actual_model_fingerprint": self.actual_model_fingerprint,
            "provider_request_ids": self.provider_request_ids,
            "model_call_count": self.model_call_count,
            "source_action_count": self.source_action_count,
            "source_byte_count": self.source_byte_count,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "usage_complete": self.usage_complete,
        }
        return (
            digest_of(values) == self.digest
            and digest_of(
                {
                    "answer": self.answer,
                    "claims": tuple(
                        (item.claim, item.support_references)
                        for item in self.claims
                    ),
                }
            )
            == self.output_digest
        )


@dataclass(frozen=True, slots=True)
class HoldoutTaskAnswerPair:
    direct: HoldoutPathResult
    world_assisted: HoldoutPathResult
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        direct: HoldoutPathResult,
        world_assisted: HoldoutPathResult,
    ) -> "HoldoutTaskAnswerPair":
        if (
            not direct.verify_digest()
            or not world_assisted.verify_digest()
            or direct.path is not HoldoutAnswerPath.DIRECT
            or world_assisted.path is not HoldoutAnswerPath.WORLD_ASSISTED
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "answer pair contains an invalid path result",
            )
        exact_fields = (
            "suite_id",
            "suite_version",
            "suite_digest",
            "task_id",
            "task_input_digest",
            "resource_policy_digest",
            "actual_model_fingerprint",
        )
        if any(
            getattr(direct, field) != getattr(world_assisted, field)
            for field in exact_fields
        ):
            raise DomainError(
                ErrorCode.QUALIFICATION_INVALID,
                "answer paths did not use the same task, resources, and actual model",
            )
        if direct.origin == world_assisted.origin:
            raise DomainError(
                ErrorCode.QUALIFICATION_INVALID,
                "direct and system-assisted answers must use distinct origins",
            )
        return cls(
            direct=direct,
            world_assisted=world_assisted,
            digest=digest_of(
                {
                    "direct": direct.digest.value,
                    "world_assisted": world_assisted.digest.value,
                }
            ),
        )


def _verify_task_input(task_input: Mapping[str, object]) -> None:
    required = {
        "schema",
        "suite_id",
        "suite_version",
        "suite_digest",
        "task_id",
        "repository",
        "question",
        "revision_scope",
        "allowed_paths",
        "source_policy",
        "resource_policy",
        "task_input_digest",
    }
    if set(task_input) != required:
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "answer task input fields are incomplete",
        )
    core = {key: value for key, value in task_input.items() if key != "task_input_digest"}
    if task_input["task_input_digest"] != digest_of(core).value:
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "answer task input digest is invalid",
        )


def _verify_limits(
    counts: Mapping[str, int], resource_policy: Mapping[str, object]
) -> None:
    checks = (
        ("model_call_count", "maximum_model_calls"),
        ("source_action_count", "maximum_source_actions"),
        ("input_tokens", "maximum_total_input_tokens"),
        ("output_tokens", "maximum_total_output_tokens"),
    )
    for observed, limit in checks:
        maximum = resource_policy.get(limit)
        if not isinstance(maximum, int) or counts[observed] > maximum:
            raise DomainError(
                ErrorCode.BUDGET_EXHAUSTED,
                "answer path exceeded its sealed resource policy",
                {"resource": observed},
            )
    byte_limit = resource_policy.get("maximum_source_bytes_per_action")
    if (
        not isinstance(byte_limit, int)
        or counts["source_byte_count"]
        > counts["source_action_count"] * byte_limit
    ):
        raise DomainError(
            ErrorCode.BUDGET_EXHAUSTED,
            "answer path source bytes exceeded its sealed resource policy",
        )


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} must be non-empty")
    return value


def _text_tuple(values: object, label: str) -> tuple[str, ...]:
    if not isinstance(values, tuple) or not values:
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} must be non-empty")
    cleaned = tuple(_text(value, label) for value in values)
    return cleaned


def _nonnegative(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} must be non-negative")
    return value
