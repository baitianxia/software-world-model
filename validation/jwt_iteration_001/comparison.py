"""Post-delivery cross-model review of Direct Oracle and World answers."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import Mapping, Sequence
import uuid

from software_world_model.ai_infrastructure import (
    ArkChatConformanceQualification,
    VolcengineArkModelConfiguration,
)
from software_world_model.cross_cutting import Digest, DomainError, ErrorCode, digest_of

from .manifest import (
    _time,
    _utc,
    _verify_qualification,
    verify_direct_oracle,
    verify_jwt_run_configuration,
)
from .world_model import verify_world_model_result


JWT_CAPABILITY_COMPARISON_SCHEMA = "swm.jwt-capability-comparison@2"
COMPARISON_REVIEW_ATTESTATION_SCHEMA = "swm.jwt-capability-review-attestation@1"
COMPARISON_REVIEW_POLICY_REF = "jwt-cross-model-obligation-review@1"
COMPARISON_REVIEW_POLICY = """Compare the frozen Direct Oracle and delivered World answer by obligation_id.
The evaluator origin must differ from both answer-generating model origins.
Claim wording and grouping may differ; semantic_key equality is not required.
For every registered obligation, judge meaning, condition, limitation, coverage, and factual correctness.
World passes only when it covers every obligation without an extra obligation, preserves every material boundary,
contains no factual error, is never worse than Direct on an obligation, and its overall score is not lower."""
COMPARISON_REVIEW_OUTPUT_SCHEMA_REF = "jwt-cross-model-review-attestation@1"
COMPARISON_REVIEW_OUTPUT_SCHEMA = {
    "schema": COMPARISON_REVIEW_ATTESTATION_SCHEMA,
    "required_fields": [
        "schema",
        "reviewer",
        "reviewed_at",
        "method",
        "oracle_ref",
        "oracle_digest",
        "world_model_result_ref",
        "world_model_result_digest",
        "run_configuration_ref",
        "run_configuration_digest",
        "obligation_findings",
        "direct_score",
        "world_model_score",
        "score_rationale",
    ],
    "finding_fields": [
        "obligation_id",
        "outcome",
        "meaning_preserved",
        "condition_preserved",
        "limitation_preserved",
        "coverage_preserved",
        "direct_factual_error",
        "world_factual_error",
        "finding",
    ],
}

_FINDING_FIELDS = set(COMPARISON_REVIEW_OUTPUT_SCHEMA["finding_fields"])
_REVIEW_FIELDS = set(COMPARISON_REVIEW_OUTPUT_SCHEMA["required_fields"])
_REVIEWER_FIELDS = {"identity", "origin", "model_ref"}
_OUTCOMES = {
    "EQUIVALENT",
    "DIRECT_BETTER",
    "WORLD_BETTER",
    "BOTH_INSUFFICIENT",
    "INCONCLUSIVE",
}
_REVIEW_USAGE = {
    "token_usage_applicable": False,
    "reason": "review attestation was supplied by a model-independent evaluator",
}


def seal_reviewed_capability_comparison(
    *,
    oracle_path: str | Path,
    run_configuration_path: str | Path,
    world_model_result_path: str | Path,
    review_attestation_path: str | Path,
    result_directory: str | Path,
    qualification: ArkChatConformanceQualification,
    configuration: VolcengineArkModelConfiguration,
    now: datetime | None = None,
) -> Path:
    """Validate an independent cross-model review and seal a CE case artifact."""

    sealed_at = _utc(now or datetime.now(timezone.utc))
    _verify_qualification(qualification, configuration, at=sealed_at)
    oracle = _load(oracle_path, "Direct Oracle")
    run_configuration = _load(run_configuration_path, "JWT run configuration")
    world = _load(world_model_result_path, "World Model result")
    attestation = _load(review_attestation_path, "comparison review attestation")
    verify_direct_oracle(
        oracle, qualification=qualification, configuration=configuration
    )
    verify_jwt_run_configuration(
        run_configuration,
        qualification,
        configuration,
        at=sealed_at,
        require_current_harness=False,
    )
    verify_world_model_result(world, run_configuration, qualification, configuration)
    _verify_comparison_boundary(oracle, world, run_configuration)
    evidence = _obligation_evidence(oracle, world, run_configuration)
    reviewer, findings = _verify_review_attestation(
        attestation, oracle, world, run_configuration, evidence
    )
    direct_origin = str(run_configuration["adapter"]["provider_type"])
    world_origin = str(run_configuration["adapter"]["provider_type"])
    evaluator_origin = reviewer["origin"]
    if evaluator_origin in {direct_origin, world_origin}:
        raise DomainError(
            ErrorCode.CONTROL_STATE_DENIED,
            "comparison evaluator must be model-independent from Direct and World generators",
        )

    passed = _passes(
        findings=findings,
        evidence=evidence,
        direct_score=attestation["direct_score"],
        world_score=attestation["world_model_score"],
    )
    core = {
        "schema": JWT_CAPABILITY_COMPARISON_SCHEMA,
        "comparison_id": f"jwtcmp_{uuid.uuid4().hex}",
        "comparison_mode": "CROSS_MODEL_REVIEW_ATTESTATION",
        "sealed_at": _time(sealed_at),
        "reviewed_at": attestation["reviewed_at"],
        "review_policy_ref": COMPARISON_REVIEW_POLICY_REF,
        "review_policy_digest": digest_of(COMPARISON_REVIEW_POLICY).value,
        "review_output_schema_ref": COMPARISON_REVIEW_OUTPUT_SCHEMA_REF,
        "review_output_schema_digest": digest_of(
            COMPARISON_REVIEW_OUTPUT_SCHEMA
        ).value,
        "review_attestation_digest": digest_of(attestation).value,
        "evaluator": reviewer,
        "generator_models": {
            "direct": {
                "origin": direct_origin,
                "model_ref": oracle["model_ref"],
                "actual_model_fingerprints": oracle["direct_run"][
                    "actual_model_fingerprints"
                ],
            },
            "world": {
                "origin": world_origin,
                "model_ref": world["model_ref"],
                "actual_model_fingerprints": sorted(
                    {
                        call["actual_model_fingerprint"]
                        for call in world["model_calls"]
                    }
                ),
            },
        },
        "independence": {
            "evaluator_origin": evaluator_origin,
            "independent_from_direct_generator": evaluator_origin != direct_origin,
            "independent_from_world_generator": evaluator_origin != world_origin,
            "oracle_reviewer_reused": reviewer["identity"]
            == oracle["independent_reviewer"],
        },
        "oracle_ref": oracle["oracle_id"],
        "oracle_digest": oracle["oracle_digest"],
        "world_model_result_ref": world["run_id"],
        "world_model_result_digest": world["result_digest"],
        "run_configuration_ref": run_configuration["run_configuration_id"],
        "run_configuration_digest": run_configuration["configuration_digest"],
        "conformance_result_ref": qualification.result_ref,
        "registered_obligation_ids": evidence["registered_obligation_ids"],
        "missing_direct_obligation_ids": evidence[
            "missing_direct_obligation_ids"
        ],
        "missing_world_obligation_ids": evidence["missing_world_obligation_ids"],
        "extra_direct_obligation_ids": evidence["extra_direct_obligation_ids"],
        "extra_world_obligation_ids": evidence["extra_world_obligation_ids"],
        "duplicate_direct_obligation_ids": evidence[
            "duplicate_direct_obligation_ids"
        ],
        "duplicate_world_obligation_ids": evidence[
            "duplicate_world_obligation_ids"
        ],
        "structural_mismatches": evidence["structural_mismatches"],
        "obligation_findings": findings,
        "direct_score": attestation["direct_score"],
        "world_model_score": attestation["world_model_score"],
        "score_rationale": attestation["score_rationale"],
        "review_usage": _REVIEW_USAGE,
        "conclusion": "PASS" if passed else "FAIL",
    }
    document = {**core, "comparison_digest": digest_of(core).value}
    verify_capability_comparison(document, oracle, world, run_configuration)
    return _seal(document, result_directory)


def verify_capability_comparison(
    document: Mapping[str, object],
    oracle: Mapping[str, object],
    world: Mapping[str, object],
    run_configuration: Mapping[str, object],
) -> None:
    """Verify a sealed cross-model obligation comparison."""

    supplied = document.get("comparison_digest")
    try:
        digest = Digest(str(supplied))
    except ValueError as exc:
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID, "comparison digest is invalid"
        ) from exc
    core = {key: value for key, value in document.items() if key != "comparison_digest"}
    if digest_of(core) != digest:
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID, "comparison digest does not verify"
        )
    if (
        document.get("schema") != JWT_CAPABILITY_COMPARISON_SCHEMA
        or document.get("comparison_mode") != "CROSS_MODEL_REVIEW_ATTESTATION"
        or document.get("oracle_ref") != oracle.get("oracle_id")
        or document.get("oracle_digest") != oracle.get("oracle_digest")
        or document.get("world_model_result_ref") != world.get("run_id")
        or document.get("world_model_result_digest") != world.get("result_digest")
        or document.get("run_configuration_ref")
        != run_configuration.get("run_configuration_id")
        or document.get("run_configuration_digest")
        != run_configuration.get("configuration_digest")
        or document.get("conformance_result_ref")
        != world.get("conformance_result_ref")
    ):
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID, "comparison dependencies are stale"
        )
    if (
        document.get("review_policy_ref") != COMPARISON_REVIEW_POLICY_REF
        or document.get("review_policy_digest")
        != digest_of(COMPARISON_REVIEW_POLICY).value
        or document.get("review_output_schema_ref")
        != COMPARISON_REVIEW_OUTPUT_SCHEMA_REF
        or document.get("review_output_schema_digest")
        != digest_of(COMPARISON_REVIEW_OUTPUT_SCHEMA).value
    ):
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID, "comparison review contract is stale"
        )

    evaluator = document.get("evaluator")
    generators = document.get("generator_models")
    independence = document.get("independence")
    if (
        not isinstance(evaluator, dict)
        or set(evaluator) != _REVIEWER_FIELDS
        or any(not _nonempty(evaluator.get(field)) for field in _REVIEWER_FIELDS)
        or not isinstance(generators, dict)
        or set(generators) != {"direct", "world"}
        or not isinstance(generators.get("direct"), dict)
        or not isinstance(generators.get("world"), dict)
        or not isinstance(independence, dict)
        or set(independence)
        != {
            "evaluator_origin",
            "independent_from_direct_generator",
            "independent_from_world_generator",
            "oracle_reviewer_reused",
        }
        or independence.get("evaluator_origin") != evaluator.get("origin")
        or independence.get("independent_from_direct_generator") is not True
        or independence.get("independent_from_world_generator") is not True
        or generators.get("direct", {}).get("origin") == evaluator.get("origin")
        or generators.get("world", {}).get("origin") == evaluator.get("origin")
        or independence.get("oracle_reviewer_reused")
        is not (evaluator.get("identity") == oracle.get("independent_reviewer"))
    ):
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "comparison evaluator independence evidence is invalid",
        )
    expected_generators = {
        "direct": {
            "origin": run_configuration["adapter"]["provider_type"],
            "model_ref": oracle["model_ref"],
            "actual_model_fingerprints": oracle["direct_run"][
                "actual_model_fingerprints"
            ],
        },
        "world": {
            "origin": run_configuration["adapter"]["provider_type"],
            "model_ref": world["model_ref"],
            "actual_model_fingerprints": sorted(
                {
                    call["actual_model_fingerprint"]
                    for call in world["model_calls"]
                }
            ),
        },
    }
    if generators != expected_generators:
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID, "comparison generator evidence is stale"
        )

    evidence = _obligation_evidence(oracle, world, run_configuration)
    for field in (
        "registered_obligation_ids",
        "missing_direct_obligation_ids",
        "missing_world_obligation_ids",
        "extra_direct_obligation_ids",
        "extra_world_obligation_ids",
        "duplicate_direct_obligation_ids",
        "duplicate_world_obligation_ids",
        "structural_mismatches",
    ):
        if document.get(field) != evidence[field]:
            raise DomainError(
                ErrorCode.QUALIFICATION_INVALID,
                "comparison obligation-set evidence is invalid",
            )
    findings = _validate_findings(
        document.get("obligation_findings"), evidence["registered_obligation_ids"]
    )
    direct_score = _score(document.get("direct_score"), "direct score")
    world_score = _score(document.get("world_model_score"), "World score")
    if not _nonempty(document.get("score_rationale")):
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID, "comparison score rationale is invalid"
        )
    expected_pass = _passes(
        findings=findings,
        evidence=evidence,
        direct_score=direct_score,
        world_score=world_score,
    )
    if (document.get("conclusion") == "PASS") != expected_pass:
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID, "comparison conclusion is inconsistent"
        )
    if document.get("review_usage") != _REVIEW_USAGE:
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID, "comparison review usage is invalid"
        )


def _verify_review_attestation(
    attestation: Mapping[str, object],
    oracle: Mapping[str, object],
    world: Mapping[str, object],
    run_configuration: Mapping[str, object],
    evidence: Mapping[str, object],
) -> tuple[dict[str, str], list[dict[str, object]]]:
    if set(attestation) != _REVIEW_FIELDS:
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            "comparison review attestation fields do not match the closed contract",
        )
    if (
        attestation.get("schema") != COMPARISON_REVIEW_ATTESTATION_SCHEMA
        or attestation.get("method") != "SOURCE_RECHECK_AND_CROSS_MODEL_COMPARISON"
        or attestation.get("oracle_ref") != oracle.get("oracle_id")
        or attestation.get("oracle_digest") != oracle.get("oracle_digest")
        or attestation.get("world_model_result_ref") != world.get("run_id")
        or attestation.get("world_model_result_digest") != world.get("result_digest")
        or attestation.get("run_configuration_ref")
        != run_configuration.get("run_configuration_id")
        or attestation.get("run_configuration_digest")
        != run_configuration.get("configuration_digest")
        or not _nonempty(attestation.get("reviewed_at"))
        or not _nonempty(attestation.get("score_rationale"))
    ):
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID, "comparison review binding is stale"
        )
    reviewer = attestation.get("reviewer")
    if (
        not isinstance(reviewer, dict)
        or set(reviewer) != _REVIEWER_FIELDS
        or any(not _nonempty(reviewer.get(field)) for field in _REVIEWER_FIELDS)
    ):
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT, "comparison reviewer identity is invalid"
        )
    findings = _validate_findings(
        attestation.get("obligation_findings"), evidence["registered_obligation_ids"]
    )
    _score(attestation.get("direct_score"), "direct score")
    _score(attestation.get("world_model_score"), "World score")
    return dict(reviewer), findings


def _verify_comparison_boundary(
    oracle: Mapping[str, object],
    world: Mapping[str, object],
    run_configuration: Mapping[str, object],
) -> None:
    if (
        world.get("oracle") != run_configuration.get("oracle")
        or oracle.get("oracle_id") != run_configuration["oracle"].get("oracle_ref")
        or oracle.get("oracle_digest")
        != run_configuration["oracle"].get("oracle_digest")
        or world.get("outcome") != "PASS"
        or world.get("delivery", {}).get("state") != "DELIVERED"
        or world.get("delivery", {}).get("comparison_authorized") is not True
    ):
        raise DomainError(
            ErrorCode.CONTROL_STATE_DENIED,
            "World result is not bound and authorized for comparison",
        )


def _obligation_evidence(
    oracle: Mapping[str, object],
    world: Mapping[str, object],
    run_configuration: Mapping[str, object],
) -> dict[str, object]:
    needs = run_configuration["requirement"]["needs"]
    registered_to_need = {
        obligation["obligation_id"]: need["need_id"]
        for need in needs
        for obligation in need["obligations"]
    }
    registered = sorted(registered_to_need)
    direct_claims = oracle["direct_run"]["claims"]
    world_claims = world["candidate"]["claims"]
    direct_index = _index_claims(direct_claims)
    world_index = _index_claims(world_claims)
    direct_ids = set(direct_index)
    world_ids = set(world_index)
    registered_ids = set(registered)
    structural = []
    for side, index in (("DIRECT", direct_index), ("WORLD", world_index)):
        for obligation_id in sorted(registered_ids & set(index)):
            expected_need = registered_to_need[obligation_id]
            for claim in index[obligation_id]:
                if claim.get("target") != run_configuration["source"]["target_commit"]:
                    structural.append(
                        {
                            "side": side,
                            "obligation_id": obligation_id,
                            "field": "target",
                            "expected_digest": digest_of(
                                run_configuration["source"]["target_commit"]
                            ).value,
                            "actual_digest": digest_of(claim.get("target")).value,
                        }
                    )
                if expected_need not in claim.get("need_ids", []):
                    structural.append(
                        {
                            "side": side,
                            "obligation_id": obligation_id,
                            "field": "need_ids",
                            "expected_digest": digest_of([expected_need]).value,
                            "actual_digest": digest_of(claim.get("need_ids")).value,
                        }
                    )
    return {
        "registered_obligation_ids": registered,
        "missing_direct_obligation_ids": sorted(registered_ids - direct_ids),
        "missing_world_obligation_ids": sorted(registered_ids - world_ids),
        "extra_direct_obligation_ids": sorted(direct_ids - registered_ids),
        "extra_world_obligation_ids": sorted(world_ids - registered_ids),
        "duplicate_direct_obligation_ids": sorted(
            key for key, claims in direct_index.items() if len(claims) != 1
        ),
        "duplicate_world_obligation_ids": sorted(
            key for key, claims in world_index.items() if len(claims) != 1
        ),
        "structural_mismatches": structural,
    }


def _index_claims(
    claims: Sequence[Mapping[str, object]],
) -> dict[str, list[Mapping[str, object]]]:
    index: dict[str, list[Mapping[str, object]]] = {}
    for claim in claims:
        for obligation_id in claim.get("obligation_ids", []):
            if isinstance(obligation_id, str):
                index.setdefault(obligation_id, []).append(claim)
    return index


def _validate_findings(
    raw_findings: object, registered_obligation_ids: object
) -> list[dict[str, object]]:
    registered = set(registered_obligation_ids)
    if not isinstance(raw_findings, list):
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT, "comparison obligation findings are missing"
        )
    findings = []
    seen = set()
    for item in raw_findings:
        if (
            not isinstance(item, dict)
            or set(item) != _FINDING_FIELDS
            or item.get("obligation_id") not in registered
            or item.get("obligation_id") in seen
            or item.get("outcome") not in _OUTCOMES
            or not _nonempty(item.get("finding"))
            or any(
                not isinstance(item.get(field), bool)
                for field in (
                    "meaning_preserved",
                    "condition_preserved",
                    "limitation_preserved",
                    "coverage_preserved",
                    "direct_factual_error",
                    "world_factual_error",
                )
            )
        ):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "comparison obligation finding is invalid",
            )
        seen.add(item["obligation_id"])
        findings.append(dict(item))
    if seen != registered:
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            "comparison obligation findings do not cover the registered contract",
        )
    return sorted(findings, key=lambda item: item["obligation_id"])


def _passes(
    *,
    findings: Sequence[Mapping[str, object]],
    evidence: Mapping[str, object],
    direct_score: int,
    world_score: int,
) -> bool:
    evidence_clear = all(
        not evidence[field]
        for field in (
            "missing_direct_obligation_ids",
            "missing_world_obligation_ids",
            "extra_direct_obligation_ids",
            "extra_world_obligation_ids",
            "duplicate_direct_obligation_ids",
            "duplicate_world_obligation_ids",
            "structural_mismatches",
        )
    )
    semantic_clear = all(
        item["outcome"] in {"EQUIVALENT", "WORLD_BETTER"}
        and item["meaning_preserved"] is True
        and item["condition_preserved"] is True
        and item["limitation_preserved"] is True
        and item["coverage_preserved"] is True
        and item["world_factual_error"] is False
        for item in findings
    )
    return evidence_clear and semantic_clear and world_score >= direct_score


def _score(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 10:
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} is invalid")
    return value


def _nonempty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip()) and value == value.strip()


def _load(path: str | Path, label: str) -> dict[str, object]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} cannot be read") from exc
    if not isinstance(value, dict):
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} must be an object")
    return value


def _seal(document: Mapping[str, object], directory: str | Path) -> Path:
    result_directory = Path(directory)
    result_directory.mkdir(parents=True, exist_ok=True)
    path = result_directory / f"JWT-CAPABILITY-COMPARISON-{document['comparison_id']}.json"
    payload = (
        json.dumps(document, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8")
        + b"\n"
    )
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "comparison result already exists and cannot be overwritten",
        ) from exc
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    return path
