"""Crash-safe sealed result files for product validation answer paths."""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import tempfile
from typing import Mapping

from software_world_model.cross_cutting import (
    Digest,
    DomainError,
    ErrorCode,
    canonical_json_bytes,
    digest_of,
)

from .execution import (
    HoldoutAnswerPath,
    HoldoutPathResult,
    HoldoutTaskAnswerPair,
    SealedAnswerClaim,
)


PATH_RESULT_DOCUMENT_SCHEMA = "swm.product-holdout-path-result@1"
ANSWER_PAIR_DOCUMENT_SCHEMA = "swm.product-holdout-answer-pair@1"
_SAFE_NAME = re.compile(r"[^a-zA-Z0-9._-]+")


def save_path_result(
    result: HoldoutPathResult,
    *,
    task_input: Mapping[str, object],
    result_directory: str | Path,
) -> Path:
    document = path_result_document(result, task_input=task_input)
    target = Path(result_directory) / (
        f"{_name(result.task_id)}--{result.path.value.casefold()}.json"
    )
    write_validation_document_once(target, document)
    loaded, loaded_task = load_path_result(target)
    if loaded != result or loaded_task != dict(task_input):
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "persisted answer path result does not match the sealed result",
        )
    return target


def load_path_result(
    path: str | Path,
) -> tuple[HoldoutPathResult, dict[str, object]]:
    document = _load_document(path, PATH_RESULT_DOCUMENT_SCHEMA)
    if set(document) != {"schema", "task_input", "result", "document_digest"}:
        _invalid("answer path result document fields are incomplete")
    task_input = document["task_input"]
    raw = document["result"]
    if not isinstance(task_input, dict) or not isinstance(raw, dict):
        _invalid("answer path result payload is invalid")
    required = {
        "result_ref",
        "run_id",
        "path",
        "origin",
        "implementation_digest",
        "answer",
        "claims",
        "output_digest",
        "actual_model_fingerprint",
        "provider_request_ids",
        "model_call_count",
        "source_action_count",
        "source_byte_count",
        "input_tokens",
        "output_tokens",
        "usage_complete",
        "result_digest",
    }
    if set(raw) != required or not isinstance(raw["claims"], list):
        _invalid("answer path sealed result fields are incomplete")
    claims = tuple(
        SealedAnswerClaim(
            claim=item["claim"],
            support_references=tuple(item["support_references"]),
        )
        for item in raw["claims"]
        if isinstance(item, dict)
        and set(item) == {"claim", "support_references"}
        and isinstance(item["support_references"], list)
    )
    if len(claims) != len(raw["claims"]):
        _invalid("answer path claims are invalid")
    try:
        result = HoldoutPathResult.create(
            result_ref=raw["result_ref"],
            run_id=raw["run_id"],
            path=HoldoutAnswerPath(raw["path"]),
            origin=raw["origin"],
            implementation_digest=Digest(raw["implementation_digest"]),
            task_input=task_input,
            answer=raw["answer"],
            claims=claims,
            actual_model_fingerprint=raw["actual_model_fingerprint"],
            provider_request_ids=tuple(raw["provider_request_ids"]),
            model_call_count=raw["model_call_count"],
            source_action_count=raw["source_action_count"],
            source_byte_count=raw["source_byte_count"],
            input_tokens=raw["input_tokens"],
            output_tokens=raw["output_tokens"],
            usage_complete=raw["usage_complete"],
        )
        recorded_output = Digest(raw["output_digest"])
        recorded_result = Digest(raw["result_digest"])
    except (KeyError, TypeError, ValueError) as exc:
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "answer path result cannot be reconstructed",
        ) from exc
    if result.output_digest != recorded_output or result.digest != recorded_result:
        _invalid("answer path result digest is invalid")
    return result, task_input


def save_answer_pair(
    pair: HoldoutTaskAnswerPair,
    *,
    direct_result_path: str | Path,
    world_result_path: str | Path,
    result_directory: str | Path,
) -> Path:
    direct, direct_task = load_path_result(direct_result_path)
    world, world_task = load_path_result(world_result_path)
    reconstructed = HoldoutTaskAnswerPair.create(
        direct=direct, world_assisted=world
    )
    if reconstructed != pair or direct_task != world_task:
        _invalid("answer pair does not match its persisted path results")
    core = {
        "schema": ANSWER_PAIR_DOCUMENT_SCHEMA,
        "suite_digest": pair.direct.suite_digest.value,
        "task_id": pair.direct.task_id,
        "task_input_digest": pair.direct.task_input_digest.value,
        "direct_result_path": str(Path(direct_result_path).resolve()),
        "direct_result_digest": pair.direct.digest.value,
        "world_result_path": str(Path(world_result_path).resolve()),
        "world_result_digest": pair.world_assisted.digest.value,
        "pair_digest": pair.digest.value,
    }
    document = {**core, "document_digest": digest_of(core).value}
    target = Path(result_directory) / f"{_name(pair.direct.task_id)}--pair.json"
    write_validation_document_once(target, document)
    verify_answer_pair_document(target)
    return target


def verify_answer_pair_document(path: str | Path) -> HoldoutTaskAnswerPair:
    document = _load_document(path, ANSWER_PAIR_DOCUMENT_SCHEMA)
    required = {
        "schema",
        "suite_digest",
        "task_id",
        "task_input_digest",
        "direct_result_path",
        "direct_result_digest",
        "world_result_path",
        "world_result_digest",
        "pair_digest",
        "document_digest",
    }
    if set(document) != required:
        _invalid("answer pair document fields are incomplete")
    direct, direct_task = load_path_result(document["direct_result_path"])
    world, world_task = load_path_result(document["world_result_path"])
    pair = HoldoutTaskAnswerPair.create(direct=direct, world_assisted=world)
    if (
        direct_task != world_task
        or pair.direct.suite_digest.value != document["suite_digest"]
        or pair.direct.task_id != document["task_id"]
        or pair.direct.task_input_digest.value != document["task_input_digest"]
        or pair.direct.digest.value != document["direct_result_digest"]
        or pair.world_assisted.digest.value != document["world_result_digest"]
        or pair.digest.value != document["pair_digest"]
    ):
        _invalid("answer pair document is inconsistent")
    return pair


def path_result_document(
    result: HoldoutPathResult, *, task_input: Mapping[str, object]
) -> dict[str, object]:
    if not result.verify_digest() or result.task_input_digest.value != task_input.get(
        "task_input_digest"
    ):
        _invalid("answer path result is not bound to the supplied sealed task")
    raw = {
        "result_ref": result.result_ref,
        "run_id": result.run_id,
        "path": result.path.value,
        "origin": result.origin,
        "implementation_digest": result.implementation_digest.value,
        "answer": result.answer,
        "claims": [
            {
                "claim": item.claim,
                "support_references": list(item.support_references),
            }
            for item in result.claims
        ],
        "output_digest": result.output_digest.value,
        "actual_model_fingerprint": result.actual_model_fingerprint,
        "provider_request_ids": list(result.provider_request_ids),
        "model_call_count": result.model_call_count,
        "source_action_count": result.source_action_count,
        "source_byte_count": result.source_byte_count,
        "input_tokens": result.input_tokens,
        "output_tokens": result.output_tokens,
        "usage_complete": result.usage_complete,
        "result_digest": result.digest.value,
    }
    core = {
        "schema": PATH_RESULT_DOCUMENT_SCHEMA,
        "task_input": dict(task_input),
        "result": raw,
    }
    return {**core, "document_digest": digest_of(core).value}


def _load_document(path: str | Path, schema: str) -> dict[str, object]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "sealed validation result cannot be loaded",
        ) from exc
    if not isinstance(value, dict) or value.get("schema") != schema:
        _invalid("sealed validation result schema is invalid")
    recorded = value.get("document_digest")
    core = {key: item for key, item in value.items() if key != "document_digest"}
    if not isinstance(recorded, str) or digest_of(core).value != recorded:
        _invalid("sealed validation result document digest is invalid")
    return value


def write_validation_document_once(
    target: str | Path, document: Mapping[str, object]
) -> None:
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = canonical_json_bytes(document) + b"\n"
    if target.exists():
        try:
            existing = target.read_bytes()
        except OSError as exc:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "existing sealed validation result cannot be read",
            ) from exc
        if existing != payload:
            raise DomainError(
                ErrorCode.IDEMPOTENCY_MISMATCH,
                "sealed validation result path already contains different evidence",
            )
        return
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", dir=target.parent, prefix=f".{target.name}.", delete=False
        ) as temporary:
            temporary_name = temporary.name
            temporary.write(payload)
            temporary.flush()
            os.fsync(temporary.fileno())
        try:
            os.link(temporary_name, target)
        except FileExistsError:
            if target.read_bytes() != payload:
                raise DomainError(
                    ErrorCode.IDEMPOTENCY_MISMATCH,
                    "sealed validation result was concurrently changed",
                )
    finally:
        if temporary_name is not None:
            try:
                Path(temporary_name).unlink()
            except FileNotFoundError:
                pass


def _name(value: str) -> str:
    cleaned = _SAFE_NAME.sub("-", value).strip("-.")
    if not cleaned:
        raise DomainError(ErrorCode.INVALID_ARGUMENT, "result file name is invalid")
    return cleaned


def _invalid(message: str) -> None:
    raise DomainError(ErrorCode.AUTHORITY_RECORD_INCONSISTENT, message)
