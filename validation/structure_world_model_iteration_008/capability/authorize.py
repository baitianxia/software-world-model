"""Seal one explicit user authorization for an ITER-008 external phase."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
from typing import Mapping

from software_world_model.cross_cutting import canonical_json_bytes, digest_of


MODEL_DIAGNOSTIC_REQUEST_SCHEMA = (
    "SWM-ITER-008-DEEPSEEK-MODEL-DIAGNOSTIC-AUTHORIZATION-REQUEST@1"
)
CONFORMANCE_REQUEST_SCHEMA = (
    "SWM-ITER-008-DEEPSEEK-CONFORMANCE-AUTHORIZATION-REQUEST@1"
)
CAPABILITY_REQUEST_SCHEMA = (
    "SWM-ITER-008-BOUNDED-CAPABILITY-AUTHORIZATION-REQUEST@1"
)
AUTHORIZATION_SCHEMA = "SWM-ITER-008-EXTERNAL-EVALUATION-AUTHORIZATION@1"


class AuthorizationError(RuntimeError):
    pass


def create_authorization(
    *,
    request_path: Path,
    output_path: Path,
    authorized_at: datetime,
    authorization_ref: str,
    single_use_result_directory: Path,
) -> tuple[Path, dict[str, object]]:
    request = _load_request(request_path)
    if authorized_at.tzinfo is None or authorized_at.utcoffset() is None:
        raise AuthorizationError("authorization timestamp must be timezone-aware")
    timestamp = authorized_at.astimezone(timezone.utc)
    if not re.fullmatch(
        r"codex-user-message:sha256:[0-9a-f]{64}", authorization_ref
    ):
        raise AuthorizationError("authorization ref must bind one exact user message")
    created_at = _time(str(request["created_at"]))
    if timestamp < created_at:
        raise AuthorizationError("authorization must postdate the exact request")
    result_parent = single_use_result_directory.parent.resolve(strict=True)
    canonical_result = result_parent / single_use_result_directory.name
    if (
        single_use_result_directory != canonical_result
        or canonical_result.exists()
        or canonical_result.is_symlink()
    ):
        raise AuthorizationError("result directory must be one new canonical path")
    phase = request.get("phase")
    if phase not in {
        "DEEPSEEK_MODEL_DIAGNOSTIC",
        "DEEPSEEK_CONFORMANCE",
        "BOUNDED_CAPABILITY_QUALIFICATION",
    }:
        raise AuthorizationError("authorization request phase is invalid")
    scope = request.get("authorization_scope")
    if not isinstance(scope, Mapping):
        raise AuthorizationError("authorization request scope is invalid")
    core = {
        "schema": AUTHORIZATION_SCHEMA,
        "status": "AUTHORIZED",
        "phase": phase,
        "request_schema": request["schema"],
        "request_digest": request["document_digest"],
        "freeze_ref": request["freeze_ref"],
        "freeze_digest": request["freeze_digest"],
        "authorized_by": "user",
        "authorized_at": timestamp.isoformat().replace("+00:00", "Z"),
        "authorization_ref": authorization_ref,
        "authorization_scope": dict(scope),
        "single_use_result_directory": str(canonical_result),
        "authorization_consumed": False,
        "retry_permitted": False,
        "hidden_canary_disclosure_authorized": False,
        "production_activation": "NOT_EXECUTED",
        "git_stage_commit_push": "NOT_EXECUTED",
    }
    document = {
        **core,
        "document_digest": digest_of([AUTHORIZATION_SCHEMA, core]).value,
    }
    _write_once(output_path, document)
    return output_path, document


def load_authorization(path: Path, request: Mapping[str, object]) -> dict[str, object]:
    value = _load_document(path, AUTHORIZATION_SCHEMA)
    expected_fields = {
        "schema",
        "status",
        "phase",
        "request_schema",
        "request_digest",
        "freeze_ref",
        "freeze_digest",
        "authorized_by",
        "authorized_at",
        "authorization_ref",
        "authorization_scope",
        "single_use_result_directory",
        "authorization_consumed",
        "retry_permitted",
        "hidden_canary_disclosure_authorized",
        "production_activation",
        "git_stage_commit_push",
        "document_digest",
    }
    if (
        set(value) != expected_fields
        or value.get("status") != "AUTHORIZED"
        or value.get("phase") != request.get("phase")
        or value.get("request_schema") != request.get("schema")
        or value.get("request_digest") != request.get("document_digest")
        or value.get("freeze_ref") != request.get("freeze_ref")
        or value.get("freeze_digest") != request.get("freeze_digest")
        or value.get("authorization_scope") != request.get("authorization_scope")
        or value.get("authorized_by") != "user"
        or value.get("authorization_consumed") is not False
        or value.get("retry_permitted") is not False
        or value.get("hidden_canary_disclosure_authorized") is not False
        or value.get("production_activation") != "NOT_EXECUTED"
        or value.get("git_stage_commit_push") != "NOT_EXECUTED"
        or not isinstance(value.get("single_use_result_directory"), str)
        or not re.fullmatch(
            r"codex-user-message:sha256:[0-9a-f]{64}",
            str(value.get("authorization_ref")),
        )
    ):
        raise AuthorizationError("authorization is stale or outside the request")
    if _time(str(value["authorized_at"])) < _time(str(request["created_at"])):
        raise AuthorizationError("authorization predates the exact request")
    return value


def _load_request(path: Path) -> dict[str, object]:
    try:
        raw = json.loads(path.read_bytes(), object_pairs_hook=_unique_object)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        raise AuthorizationError("authorization request cannot be loaded") from exc
    if not isinstance(raw, dict) or raw.get("schema") not in {
        MODEL_DIAGNOSTIC_REQUEST_SCHEMA,
        CONFORMANCE_REQUEST_SCHEMA,
        CAPABILITY_REQUEST_SCHEMA,
    }:
        raise AuthorizationError("authorization request schema is invalid")
    schema = str(raw["schema"])
    expected_fields = {
        "schema",
        "status",
        "phase",
        "created_at",
        "freeze_ref",
        "freeze_digest",
        "authorization_scope",
        "authorization_must_postdate_freeze",
        "single_use",
        "retry_permitted",
        "hidden_canary_disclosure_requested",
        "production_activation",
        "git_stage_commit_push",
        "document_digest",
    }
    core = {key: value for key, value in raw.items() if key != "document_digest"}
    if (
        set(raw) != expected_fields
        or raw.get("document_digest") != digest_of([schema, core]).value
    ):
        raise AuthorizationError("authorization request digest is invalid")
    expected_phase = {
        MODEL_DIAGNOSTIC_REQUEST_SCHEMA: "DEEPSEEK_MODEL_DIAGNOSTIC",
        CONFORMANCE_REQUEST_SCHEMA: "DEEPSEEK_CONFORMANCE",
        CAPABILITY_REQUEST_SCHEMA: "BOUNDED_CAPABILITY_QUALIFICATION",
    }[schema]
    if (
        raw.get("status") != "AWAITING_USER_AUTHORIZATION"
        or raw.get("phase") != expected_phase
        or not isinstance(raw.get("freeze_ref"), str)
        or not isinstance(raw.get("freeze_digest"), str)
        or not isinstance(raw.get("authorization_scope"), Mapping)
        or raw.get("authorization_must_postdate_freeze") is not True
        or raw.get("single_use") is not True
        or raw.get("retry_permitted") is not False
        or raw.get("production_activation") != "NOT_EXECUTED"
        or raw.get("hidden_canary_disclosure_requested") is not False
        or raw.get("git_stage_commit_push") != "NOT_EXECUTED"
    ):
        raise AuthorizationError("authorization request boundary is invalid")
    _time(str(raw.get("created_at")))
    return raw


def _load_document(path: Path, schema: str) -> dict[str, object]:
    try:
        value = json.loads(path.read_bytes(), object_pairs_hook=_unique_object)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        raise AuthorizationError("authorization document cannot be loaded") from exc
    if not isinstance(value, dict) or value.get("schema") != schema:
        raise AuthorizationError("authorization document schema is invalid")
    core = {key: item for key, item in value.items() if key != "document_digest"}
    if value.get("document_digest") != digest_of([schema, core]).value:
        raise AuthorizationError("authorization document digest is invalid")
    return value


def _time(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise AuthorizationError("authorization request time is invalid") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise AuthorizationError("authorization request time is naive")
    return parsed.astimezone(timezone.utc)


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def _write_once(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        remaining = memoryview(canonical_json_bytes(value))
        while remaining:
            remaining = remaining[os.write(descriptor, remaining) :]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--authorized-at", required=True)
    parser.add_argument("--authorization-ref", required=True)
    parser.add_argument("--single-use-result-directory", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    try:
        output, document = create_authorization(
            request_path=Path(arguments.request),
            output_path=Path(arguments.output),
            authorized_at=_time(arguments.authorized_at),
            authorization_ref=arguments.authorization_ref,
            single_use_result_directory=Path(
                arguments.single_use_result_directory
            ),
        )
        print(
            canonical_json_bytes(
                {
                    "status": "AUTHORIZED",
                    "phase": document["phase"],
                    "authorization_path": str(output),
                    "authorization_digest": document["document_digest"],
                    "production_activation": "NOT_EXECUTED",
                }
            ).decode()
        )
        return 0
    except (AuthorizationError, OSError, ValueError) as exc:
        print(
            canonical_json_bytes(
                {"status": "ERROR", "message": str(exc)}
            ).decode()
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
