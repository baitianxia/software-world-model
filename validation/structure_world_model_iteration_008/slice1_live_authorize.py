"""Authorize one frozen ITER-008 SLICE-001 live run and seal a user verdict.

Both operations are file-only.  They never start the product, read credentials,
open a network connection, or infer a user's judgement.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
from typing import Mapping, Sequence

from software_world_model.cross_cutting import canonical_json_bytes, digest_of

from .slice1_live_evaluator import VERDICT_SCHEMA


DISCLOSURE_SCHEMA = "SWM-WORLD-MODEL-DISCLOSURE-AUTHORIZATION@1"
GRANT_SCHEMA = "SWM-WORLD-MODEL-EVALUATION-GRANT@2"
FREEZE_REPORT_SCHEMA = "SWM-ITER-008-SLICE-001-CANDIDATE-FREEZE@1"
_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
_AUTHORIZATION_REF = re.compile(r"^codex-user-message:sha256:[0-9a-f]{64}$")
_PAYLOAD_BOUNDARY = "ORIGINAL_QUESTION_AND_NO_PAYLOAD_PUBLISHED_STRUCTURE"
_EXPECTED_OUTCOMES = frozenset(
    {"SUPPORTED", "BOUNDED_ABSENCE", "LIMITATION"}
)


class LiveAuthorizationError(RuntimeError):
    pass


def authorize_grant(
    *,
    freeze_report_path: Path,
    pending_grant_path: Path,
    output_path: Path,
    authorized_at: str,
    authorization_ref: str,
    authorization_message_digest: str,
) -> dict[str, object]:
    report, _ = _load_document(freeze_report_path, FREEZE_REPORT_SCHEMA)
    pending, _ = _load_document(pending_grant_path, GRANT_SCHEMA)
    if (
        report.get("status") != "PASS"
        or report.get("evaluation_subject_status") != "CANDIDATE"
        or report.get("pending_evaluation_grant_digest")
        != pending.get("document_digest")
        or report.get("external_model_dispatch_during_freeze")
        != "NOT_EXECUTED"
        or report.get("live_question_status")
        != "AWAITING_USER_AFTER_CODE_FREEZE"
        or report.get("production_activation") != "NOT_EXECUTED"
        or pending.get("environment") != "EVALUATION_ONLY"
        or pending.get("live_dispatch_authorized") is not False
        or pending.get("production_activation") != "NOT_EXECUTED"
    ):
        raise LiveAuthorizationError("candidate freeze is not authorizable")
    disclosure = pending.get("disclosure_authorization")
    if not isinstance(disclosure, Mapping) or (
        disclosure.get("status") != "NOT_AUTHORIZED"
        or disclosure.get("authorized_by") != "user"
        or disclosure.get("authorization_ref")
        != "PENDING_POST_FREEZE_USER_AUTHORIZATION"
        or disclosure.get("payload_boundary") != _PAYLOAD_BOUNDARY
    ):
        raise LiveAuthorizationError("pending disclosure authorization drifted")
    frozen_at = _aware_time(str(report.get("frozen_at")), "freeze time")
    authorized = _aware_time(authorized_at, "authorization time")
    if authorized.astimezone(timezone.utc) <= frozen_at.astimezone(timezone.utc):
        raise LiveAuthorizationError(
            "live authorization must postdate the exact candidate freeze"
        )
    _require_user_message_binding(
        authorization_ref=authorization_ref,
        authorization_message_digest=authorization_message_digest,
    )
    disclosure_core = {
        "status": "AUTHORIZED",
        "authorized_by": "user",
        "authorized_at": authorized.isoformat(),
        "authorization_ref": authorization_ref,
        "payload_boundary": _PAYLOAD_BOUNDARY,
    }
    authorized_disclosure = {
        **disclosure_core,
        "document_digest": digest_of(
            [DISCLOSURE_SCHEMA, disclosure_core]
        ).value,
    }
    grant_core = {
        key: value
        for key, value in pending.items()
        if key
        not in {
            "document_digest",
            "live_dispatch_authorized",
            "disclosure_authorization",
        }
    }
    grant_core.update(
        {
            "live_dispatch_authorized": True,
            "disclosure_authorization": authorized_disclosure,
        }
    )
    ordered_core = {
        "schema": grant_core.pop("schema"),
        "environment": grant_core.pop("environment"),
        "live_dispatch_authorized": grant_core.pop(
            "live_dispatch_authorized"
        ),
        "disclosure_authorization": grant_core.pop(
            "disclosure_authorization"
        ),
        **grant_core,
    }
    authorized_grant = {
        **ordered_core,
        "document_digest": digest_of([GRANT_SCHEMA, ordered_core]).value,
    }
    _write_once(output_path, authorized_grant)
    return authorized_grant


def seal_verdict(
    *,
    result_path: Path,
    output_path: Path,
    status: str,
    expected_outcome: str,
    answer_correct: bool,
    cross_domain_calls_and_semantics: bool,
    boundary_honest: bool,
    citation_opened: bool,
    browser_console_clean: bool,
    authorization_ref: str,
    authorization_message_digest: str,
) -> dict[str, object]:
    result, raw = _load_canonical_json(result_path, "browser result")
    page = result.get("page")
    request = page.get("request") if isinstance(page, Mapping) else None
    question = (
        request.get("original_question")
        if isinstance(request, Mapping)
        else None
    )
    if not isinstance(question, str) or not question.strip():
        raise LiveAuthorizationError("browser result has no original question")
    if status not in {"PASS", "FAIL"}:
        raise LiveAuthorizationError("user verdict status is invalid")
    if expected_outcome not in _EXPECTED_OUTCOMES:
        raise LiveAuthorizationError("expected outcome is invalid")
    _require_user_message_binding(
        authorization_ref=authorization_ref,
        authorization_message_digest=authorization_message_digest,
    )
    if status == "PASS" and not (
        answer_correct and citation_opened and browser_console_clean
    ):
        raise LiveAuthorizationError(
            "a PASS verdict requires correctness, opened citation, and clean console"
        )
    if status == "PASS" and expected_outcome == "SUPPORTED" and not (
        cross_domain_calls_and_semantics and not boundary_honest
    ):
        raise LiveAuthorizationError(
            "a supported PASS must confirm the cross-domain answer"
        )
    if status == "PASS" and expected_outcome != "SUPPORTED" and not (
        boundary_honest and not cross_domain_calls_and_semantics
    ):
        raise LiveAuthorizationError(
            "a boundary PASS must confirm an honest bounded result"
        )
    core = {
        "schema": VERDICT_SCHEMA,
        "status": status,
        "expected_outcome": expected_outcome,
        "result_raw_sha256": "sha256:" + hashlib.sha256(raw).hexdigest(),
        "question_digest": digest_of(question).value,
        "answer_correct": answer_correct,
        "cross_domain_calls_and_semantics": (
            cross_domain_calls_and_semantics
        ),
        "boundary_honest": boundary_honest,
        "citation_opened": citation_opened,
        "browser_console_clean": browser_console_clean,
        "authorized_by": "user",
        "authorization_ref": authorization_ref,
        "production_activation": "NOT_EXECUTED",
    }
    verdict = {
        **core,
        "document_digest": digest_of([VERDICT_SCHEMA, core]).value,
    }
    _write_once(output_path, verdict)
    return verdict


def _load_document(path: Path, schema: str) -> tuple[dict[str, object], bytes]:
    value, raw = _load_canonical_json(path, "sealed document")
    if value.get("schema") != schema:
        raise LiveAuthorizationError("sealed document schema is invalid")
    core = {key: item for key, item in value.items() if key != "document_digest"}
    if value.get("document_digest") != digest_of([schema, core]).value:
        raise LiveAuthorizationError("sealed document digest does not verify")
    return value, raw


def _load_canonical_json(path: Path, label: str) -> tuple[dict[str, object], bytes]:
    try:
        exact = path.resolve(strict=True)
        if exact != path or path.is_symlink():
            raise LiveAuthorizationError(f"{label} path is not canonical")
        raw = exact.read_bytes()
        value = json.loads(raw, object_pairs_hook=_unique_object)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise LiveAuthorizationError(f"{label} cannot be loaded") from exc
    if not isinstance(value, dict) or canonical_json_bytes(value) != raw:
        raise LiveAuthorizationError(f"{label} is not canonical JSON")
    return value, raw


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _aware_time(value: str, label: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise LiveAuthorizationError(f"{label} is invalid") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise LiveAuthorizationError(f"{label} must be timezone-aware")
    return parsed


def _require_user_message_binding(
    *, authorization_ref: str, authorization_message_digest: str
) -> None:
    if (
        not _AUTHORIZATION_REF.fullmatch(authorization_ref)
        or not _DIGEST.fullmatch(authorization_message_digest)
        or authorization_ref.removeprefix("codex-user-message:")
        != authorization_message_digest
    ):
        raise LiveAuthorizationError("user message authorization binding is invalid")


def _write_once(path: Path, value: object) -> None:
    parent = path.parent.resolve(strict=True)
    exact = parent / path.name
    if path != exact or path.exists() or path.is_symlink():
        raise LiveAuthorizationError("output must be one new canonical file")
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        remaining = memoryview(canonical_json_bytes(value))
        while remaining:
            remaining = remaining[os.write(descriptor, remaining) :]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _bool(value: str) -> bool:
    if value == "true":
        return True
    if value == "false":
        return False
    raise argparse.ArgumentTypeError("expected true or false")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    authorize = commands.add_parser("authorize-grant")
    authorize.add_argument("--freeze-report", required=True)
    authorize.add_argument("--pending-grant", required=True)
    authorize.add_argument("--output", required=True)
    authorize.add_argument("--authorized-at", required=True)
    authorize.add_argument("--authorization-ref", required=True)
    authorize.add_argument("--authorization-message-digest", required=True)
    verdict = commands.add_parser("seal-verdict")
    verdict.add_argument("--result", required=True)
    verdict.add_argument("--output", required=True)
    verdict.add_argument("--status", choices=("PASS", "FAIL"), required=True)
    verdict.add_argument(
        "--expected-outcome",
        choices=tuple(sorted(_EXPECTED_OUTCOMES)),
        required=True,
    )
    verdict.add_argument("--answer-correct", type=_bool, required=True)
    verdict.add_argument(
        "--cross-domain-calls-and-semantics", type=_bool, required=True
    )
    verdict.add_argument("--boundary-honest", type=_bool, required=True)
    verdict.add_argument("--citation-opened", type=_bool, required=True)
    verdict.add_argument("--browser-console-clean", type=_bool, required=True)
    verdict.add_argument("--authorization-ref", required=True)
    verdict.add_argument("--authorization-message-digest", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    try:
        if arguments.command == "authorize-grant":
            value = authorize_grant(
                freeze_report_path=Path(arguments.freeze_report),
                pending_grant_path=Path(arguments.pending_grant),
                output_path=Path(arguments.output),
                authorized_at=arguments.authorized_at,
                authorization_ref=arguments.authorization_ref,
                authorization_message_digest=(
                    arguments.authorization_message_digest
                ),
            )
        else:
            value = seal_verdict(
                result_path=Path(arguments.result),
                output_path=Path(arguments.output),
                status=arguments.status,
                expected_outcome=arguments.expected_outcome,
                answer_correct=arguments.answer_correct,
                cross_domain_calls_and_semantics=(
                    arguments.cross_domain_calls_and_semantics
                ),
                boundary_honest=arguments.boundary_honest,
                citation_opened=arguments.citation_opened,
                browser_console_clean=arguments.browser_console_clean,
                authorization_ref=arguments.authorization_ref,
                authorization_message_digest=(
                    arguments.authorization_message_digest
                ),
            )
        print(canonical_json_bytes(value).decode("utf-8"))
        return 0
    except (LiveAuthorizationError, OSError, ValueError) as exc:
        print(
            canonical_json_bytes(
                {"status": "ERROR", "message": str(exc)}
            ).decode("utf-8")
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
