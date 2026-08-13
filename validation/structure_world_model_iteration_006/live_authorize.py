"""Bind the explicit user grant to one already frozen ITER-006 live suite."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Mapping, Sequence

from . import live_comparison, live_evaluator


GRANT_SCHEMA = "SWM-WORLD-MODEL-EVALUATION-GRANT@2"
DISCLOSURE_SCHEMA = "SWM-WORLD-MODEL-DISCLOSURE-AUTHORIZATION@1"


class AuthorizationFailure(RuntimeError):
    """A frozen document cannot be safely bound to the supplied user grant."""


def _canonical(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _digest(schema: str, core: object) -> str:
    return "sha256:" + hashlib.sha256(_canonical([schema, core])).hexdigest()


def _document(schema: str, core: Mapping[str, object]) -> dict[str, object]:
    return {**core, "document_digest": _digest(schema, core)}


def _load(path: Path, schema: str) -> dict[str, object]:
    raw = path.read_bytes()
    value = json.loads(raw, object_pairs_hook=_unique_object)
    if not isinstance(value, dict) or _canonical(value) != raw:
        raise AuthorizationFailure(f"{path} is not one canonical JSON object")
    core = {key: item for key, item in value.items() if key != "document_digest"}
    if value.get("schema") != schema or value.get("document_digest") != _digest(
        schema, core
    ):
        raise AuthorizationFailure(f"{path} has an invalid document seal")
    return value


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise AuthorizationFailure("duplicate JSON key")
        value[key] = item
    return value


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() or path.is_symlink():
        raise AuthorizationFailure(f"authorization output already exists: {path}")
    path.write_bytes(_canonical(value))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", required=True)
    parser.add_argument("--pending-grant", required=True)
    parser.add_argument("--authorized-at", required=True)
    parser.add_argument("--authorization-ref", required=True)
    parser.add_argument("--comparison-output", required=True)
    parser.add_argument("--grant-output", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    suite = _load(Path(arguments.suite).resolve(strict=True), live_evaluator.SUITE_SCHEMA)
    live_evaluator.validate_suite(suite)
    pending = _load(
        Path(arguments.pending_grant).resolve(strict=True), GRANT_SCHEMA
    )
    if (
        pending.get("live_dispatch_authorized") is not False
        or pending.get("production_activation") != "NOT_EXECUTED"
        or not isinstance(pending.get("evaluation_subject"), dict)
        or pending["evaluation_subject"].get("held_out_suite", {}).get(
            "document_digest"
        )
        != suite["document_digest"]
    ):
        raise AuthorizationFailure("pending grant is not the exact frozen suite")

    comparison = live_comparison.authorized_document(
        suite,
        authorized_at=arguments.authorized_at,
        authorization_ref=arguments.authorization_ref,
    )
    disclosure = _document(
        DISCLOSURE_SCHEMA,
        {
            "status": "AUTHORIZED",
            "authorized_by": "user",
            "authorized_at": arguments.authorized_at,
            "authorization_ref": arguments.authorization_ref,
            "payload_boundary": "ORIGINAL_QUESTION_AND_NO_PAYLOAD_PUBLISHED_STRUCTURE",
        },
    )
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
            "disclosure_authorization": disclosure,
        }
    )
    # Preserve the exact schema-defined field order through canonical encoding.
    grant = _document(GRANT_SCHEMA, grant_core)
    _write(Path(arguments.comparison_output), comparison)
    _write(Path(arguments.grant_output), grant)
    print(
        json.dumps(
            {
                "suite_digest": suite["document_digest"],
                "comparison_authorization_digest": comparison["document_digest"],
                "disclosure_authorization_digest": disclosure["document_digest"],
                "evaluation_grant_digest": grant["document_digest"],
                "production_activation": "NOT_EXECUTED",
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
