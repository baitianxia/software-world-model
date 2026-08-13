"""Seal an exact user grant for one Java capability qualification run."""

from __future__ import annotations

import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import re

from software_world_model.cross_cutting import canonical_json_bytes, digest_of

from .freeze import FREEZE_SCHEMA


AUTHORIZATION_SCHEMA = "SWM-ITER-006-JAVA-CAPABILITY-AUTHORIZATION@1"
_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
_AUTHORIZATION_REF = re.compile(r"^codex-user-message:sha256:[0-9a-f]{64}$")


class AuthorizationError(RuntimeError):
    pass


def create_authorization(
    *,
    freeze_path: Path,
    output_path: Path,
    result_directory: Path,
    authorized_at: str,
    authorization_ref: str,
    authorization_message_digest: str,
) -> dict[str, object]:
    freeze = _load_document(freeze_path, FREEZE_SCHEMA)
    dispatch = freeze.get("dispatch_contract")
    closed = freeze.get("closed_inputs")
    if (
        not isinstance(dispatch, dict)
        or not isinstance(closed, dict)
        or dispatch.get("status") != "HELD_AWAITING_EXACT_USER_AUTHORIZATION"
        or dispatch.get("planned_provider_call_count") != 8
        or dispatch.get("destination") != "VOLCENGINE_ARK"
        or freeze.get("external_model_called") is not False
        or freeze.get("production_activation") != "NOT_EXECUTED"
    ):
        raise AuthorizationError("capability freeze is not authorizable")
    try:
        parsed_at = datetime.fromisoformat(authorized_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise AuthorizationError("authorization time is invalid") from exc
    if parsed_at.tzinfo is None or parsed_at.utcoffset() is None:
        raise AuthorizationError("authorization time must include a timezone")
    if not _AUTHORIZATION_REF.fullmatch(authorization_ref):
        raise AuthorizationError("authorization reference is invalid")
    if not _DIGEST.fullmatch(authorization_message_digest):
        raise AuthorizationError("authorization message digest is invalid")
    if authorization_ref.removeprefix("codex-user-message:") != authorization_message_digest:
        raise AuthorizationError("authorization reference and message digest differ")
    result_parent = result_directory.parent.resolve(strict=True)
    exact_result = result_parent / result_directory.name
    if (
        result_directory != exact_result
        or result_directory.exists()
        or result_directory.is_symlink()
    ):
        raise AuthorizationError("authorized result directory must be one future path")
    core = {
        "schema": AUTHORIZATION_SCHEMA,
        "status": "AUTHORIZED",
        "authorized_by": "user",
        "authorized_at": parsed_at.isoformat(),
        "authorization_ref": authorization_ref,
        "authorization_message_digest": authorization_message_digest,
        "freeze_ref": freeze["freeze_ref"],
        "freeze_digest": freeze["document_digest"],
        "suite_ref": closed["suite_ref"],
        "suite_digest": closed["suite_digest"],
        "destination": dispatch["destination"],
        "planned_provider_call_count": dispatch["planned_provider_call_count"],
        "payload_boundary": dispatch["payload_boundary"],
        "single_use_result_directory": str(exact_result),
        "run_003_grant_reused": False,
        "production_activation": "NOT_EXECUTED",
        "git_stage_commit_push": "NOT_EXECUTED",
    }
    value = {
        **core,
        "document_digest": digest_of([AUTHORIZATION_SCHEMA, core]).value,
    }
    _write_once(output_path, value)
    return value


def _load_document(path: Path, schema: str) -> dict[str, object]:
    try:
        value = json.loads(path.read_bytes(), object_pairs_hook=_unique_object)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        raise AuthorizationError("sealed document cannot be loaded") from exc
    if not isinstance(value, dict) or value.get("schema") != schema:
        raise AuthorizationError("sealed document schema is invalid")
    core = {key: item for key, item in value.items() if key != "document_digest"}
    if value.get("document_digest") != digest_of([schema, core]).value:
        raise AuthorizationError("sealed document digest does not verify")
    return value


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def _write_once(path: Path, value: object) -> None:
    parent = path.parent.resolve(strict=True)
    exact = parent / path.name
    if path != exact or path.exists() or path.is_symlink():
        raise AuthorizationError("authorization output must be one new canonical file")
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
    parser.add_argument("--freeze", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--result-directory", required=True)
    parser.add_argument("--authorized-at", required=True)
    parser.add_argument("--authorization-ref", required=True)
    parser.add_argument("--authorization-message-digest", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    try:
        value = create_authorization(
            freeze_path=Path(arguments.freeze),
            output_path=Path(arguments.output),
            result_directory=Path(arguments.result_directory),
            authorized_at=arguments.authorized_at,
            authorization_ref=arguments.authorization_ref,
            authorization_message_digest=arguments.authorization_message_digest,
        )
        print(
            canonical_json_bytes(
                {
                    "status": "AUTHORIZED",
                    "authorization_digest": value["document_digest"],
                    "external_model_called": False,
                    "production_activation": "NOT_EXECUTED",
                }
            ).decode()
        )
        return 0
    except (AuthorizationError, OSError, ValueError) as exc:
        print(canonical_json_bytes({"status": "ERROR", "message": str(exc)}).decode())
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
