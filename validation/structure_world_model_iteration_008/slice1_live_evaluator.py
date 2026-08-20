"""Independently close one ITER-008 SLICE-001 formal Web result.

The evaluator consumes only the public browser result and a separately sealed
user verdict.  It has no product, Source, Bundle, authority database, model, or
network dependency.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from typing import Mapping, Sequence


VERDICT_SCHEMA = "SWM-ITER-008-SLICE-001-USER-VERDICT@1"
REPORT_SCHEMA = "SWM-ITER-008-SLICE-001-LIVE-EVALUATION@1"
_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
_EXPECTED_OUTCOMES = frozenset(
    {"SUPPORTED", "BOUNDED_ABSENCE", "LIMITATION"}
)


class LiveEvaluationError(RuntimeError):
    pass


def _canonical(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _digest(value: object) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value)).hexdigest()


def _raw_digest(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _load(path: Path, label: str) -> tuple[dict[str, object], bytes]:
    try:
        exact = path.resolve(strict=True)
        if exact != path or path.is_symlink():
            raise LiveEvaluationError(f"{label} path is not exact")
        raw = exact.read_bytes()
        value = json.loads(raw, object_pairs_hook=_unique_object)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise LiveEvaluationError(f"{label} cannot be loaded") from exc
    if not isinstance(value, dict) or _canonical(value) != raw:
        raise LiveEvaluationError(f"{label} is not canonical JSON")
    return value, raw


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def evaluate(
    *,
    result: Mapping[str, object],
    result_raw_sha256: str,
    verdict: Mapping[str, object],
) -> dict[str, object]:
    expected_verdict_keys = {
        "schema",
        "status",
        "expected_outcome",
        "result_raw_sha256",
        "question_digest",
        "answer_correct",
        "cross_domain_calls_and_semantics",
        "boundary_honest",
        "citation_opened",
        "browser_console_clean",
        "authorized_by",
        "authorization_ref",
        "production_activation",
        "document_digest",
    }
    verdict_core = {
        key: value for key, value in verdict.items() if key != "document_digest"
    }
    if (
        set(verdict) != expected_verdict_keys
        or verdict.get("schema") != VERDICT_SCHEMA
        or verdict.get("status") != "PASS"
        or verdict.get("expected_outcome") not in _EXPECTED_OUTCOMES
        or verdict.get("result_raw_sha256") != result_raw_sha256
        or verdict.get("authorized_by") != "user"
        or not isinstance(verdict.get("authorization_ref"), str)
        or not verdict["authorization_ref"]
        or verdict.get("production_activation") != "NOT_EXECUTED"
        or verdict.get("document_digest")
        != _digest([VERDICT_SCHEMA, verdict_core])
    ):
        raise LiveEvaluationError("user verdict is not an exact PASS binding")

    page = result.get("page")
    execution = result.get("execution")
    citations = result.get("citations")
    if not isinstance(page, Mapping) or not isinstance(execution, Mapping):
        raise LiveEvaluationError("public result is incomplete")
    if not isinstance(citations, list):
        raise LiveEvaluationError("public Citation index is invalid")
    request = page.get("request")
    binding = page.get("read_binding")
    boundary = page.get("execution_boundary")
    review = page.get("review")
    assessment = page.get("assessment")
    answer = page.get("answer")
    authority_chain = page.get("authority_chain")
    stages = (
        authority_chain.get("stages")
        if isinstance(authority_chain, Mapping)
        else None
    )
    if not all(
        isinstance(item, Mapping)
        for item in (request, binding, boundary, review, assessment, answer)
    ):
        raise LiveEvaluationError("public authority page is incomplete")
    assert isinstance(request, Mapping)
    assert isinstance(binding, Mapping)
    assert isinstance(boundary, Mapping)
    assert isinstance(review, Mapping)
    assert isinstance(assessment, Mapping)
    assert isinstance(answer, Mapping)
    original_question = request.get("original_question")
    expected_question_digest = (
        _digest(original_question)
        if isinstance(original_question, str)
        else None
    )
    needs = assessment.get("needs")
    claims = answer.get("claims")
    provider_calls = execution.get("provider_call_count")
    expected_outcome = verdict["expected_outcome"]
    if (
        not isinstance(provider_calls, int)
        or not 4 <= provider_calls <= 6
        or result.get("mode") != "WORLD_MODEL"
        or result.get("environment") != "EVALUATION_ONLY"
        or result.get("evaluation_subject_status") != "CANDIDATE"
        or result.get("production_activation") != "NOT_EXECUTED"
        or page.get("mode") != "WORLD_MODEL"
        or page.get("environment") != "EVALUATION_ONLY"
        or page.get("evaluation_only") is not True
        or binding.get("profile_refs") != ["JAVA_SOURCE_SEMANTICS@1"]
        or boundary.get("provider_call_count") != provider_calls
        or boundary.get("network_operation_count") != provider_calls
        or boundary.get("source_access_allowed") is not False
        or boundary.get("evidence_payload_access_allowed") is not False
        or execution.get("attempt_count") != 1
        or execution.get("network_operation_count") != provider_calls
        or execution.get("selective_retry_count") != 0
        or execution.get("provider_type") != "DEEPSEEK"
        or execution.get("source_access_count") != 0
        or execution.get("evidence_payload_access_count") != 0
        or review.get("decision") != "APPROVE"
        or review.get("finding_codes") != []
        or not isinstance(stages, list)
        or len(stages) != 10
        or not isinstance(needs, list)
        or len(needs) != 1
        or not isinstance(needs[0], Mapping)
        or not isinstance(claims, list)
        or not isinstance(answer.get("body"), str)
        or not answer["body"].strip()
        or verdict.get("question_digest") != expected_question_digest
        or verdict.get("answer_correct") is not True
        or verdict.get("citation_opened") is not True
        or verdict.get("browser_console_clean") is not True
        or not citations
    ):
        raise LiveEvaluationError("formal Web result violates the Slice boundary")

    need = needs[0]
    assert isinstance(need, Mapping)
    page_text = _canonical(page).decode("utf-8")
    if expected_outcome == "SUPPORTED":
        if (
            need.get("outcome") != "SATISFIED"
            or len(claims) < 1
            or verdict.get("cross_domain_calls_and_semantics") is not True
            or verdict.get("boundary_honest") is not False
            or '"legacy_calls"' not in page_text
            or '"ordered_atoms"' not in page_text
        ):
            raise LiveEvaluationError(
                "supported cross-domain result did not close"
            )
    elif expected_outcome == "BOUNDED_ABSENCE":
        if (
            need.get("outcome") != "KNOWLEDGE_GAP"
            or need.get("gap_code") != "BOUNDED_ABSENCE"
            or verdict.get("boundary_honest") is not True
            or verdict.get("cross_domain_calls_and_semantics") is not False
        ):
            raise LiveEvaluationError("bounded absence result is not exact")
    elif (
        need.get("outcome") != "LIMITATION"
        or not need.get("limitations")
        or verdict.get("boundary_honest") is not True
        or verdict.get("cross_domain_calls_and_semantics") is not False
    ):
        raise LiveEvaluationError("coverage limitation result is not exact")

    core = {
        "schema": REPORT_SCHEMA,
        "status": "PASS",
        "expected_outcome": expected_outcome,
        "result_raw_sha256": result_raw_sha256,
        "question_digest": expected_question_digest,
        "verdict_digest": verdict["document_digest"],
        "provider_type": "DEEPSEEK",
        "provider_call_count": provider_calls,
        "network_operation_count": provider_calls,
        "selective_retry_count": 0,
        "source_access_count": 0,
        "evidence_payload_access_count": 0,
        "formal_web": "PASS",
        "production_activation": "NOT_EXECUTED",
    }
    return {**core, "document_digest": _digest([REPORT_SCHEMA, core])}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result", required=True)
    parser.add_argument("--user-verdict", required=True)
    parser.add_argument("--output", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    try:
        result, result_raw = _load(Path(arguments.result), "browser result")
        verdict, _ = _load(Path(arguments.user_verdict), "user verdict")
        report = evaluate(
            result=result,
            result_raw_sha256=_raw_digest(result_raw),
            verdict=verdict,
        )
        output = Path(arguments.output)
        if output.exists() or output.is_symlink():
            raise LiveEvaluationError("evaluation output already exists")
        output.write_bytes(_canonical(report))
        print(_canonical(report).decode("utf-8"))
        return 0
    except (LiveEvaluationError, OSError, ValueError) as exc:
        print(_canonical({"status": "ERROR", "message": str(exc)}).decode())
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
