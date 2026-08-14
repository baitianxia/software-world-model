"""Public commitment protocol for ITER-007 evaluator-owned hidden inputs.

This module deliberately has no CLI that accepts hidden payload or commitment
secrets.  Hidden values may only be committed inside an evaluator-owned external
environment.  The shared repository side validates the resulting public receipt,
which is restricted to fixed metadata, counts, keyed commitments, and digests.
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
from pathlib import Path
import re
import stat
from typing import Mapping, Sequence


PROTOCOL_SCHEMA = "SWM-ITER-007-HIDDEN-FREEZE-PROTOCOL@1"
RECEIPT_SCHEMA = "SWM-ITER-007-HIDDEN-FREEZE-PUBLIC-RECEIPT@1"
COMMITMENT_SCHEMA = "SWM-ITER-007-HIDDEN-COMMITMENT@1"
PROTOCOL_PATH = Path(__file__).with_name("hidden_freeze_protocol.json")
LIFECYCLE_VALIDATOR_PATH = Path(__file__).with_name("hidden_freeze_lifecycle.py")
ACCEPTED_BASELINE_COMMIT = "8f305ed396899c8f8e5d175fe7fcecb6ceb48f3f"
ACCEPTED_BASELINE_TREE = "89d645c17f739f40dcbfcc0c03a2d41a503b9611"
MAXIMUM_PUBLIC_RECEIPT_BYTES = 64 * 1024

COMMITMENT_DOMAINS = {
    "canary_001_project_manifest": "ITER-007/V-CANARY-001/PROJECT-MANIFEST@1",
    "canary_001_suite": "ITER-007/V-CANARY-001/SUITE@1",
    "canary_002_project_manifest": "ITER-007/V-CANARY-002/PROJECT-MANIFEST@1",
    "canary_002_suite": "ITER-007/V-CANARY-002/SUITE@1",
    "held_out_project_manifest": "ITER-007/HELD-OUT/PROJECT-MANIFEST@1",
    "held_out_suite": "ITER-007/HELD-OUT/SUITE@1",
    "baseline_result": "ITER-007/HELD-OUT/BASELINE-RESULT@1",
    "mature_source_agent_protocol": (
        "ITER-007/HELD-OUT/MATURE-SOURCE-AGENT-PROTOCOL@1"
    ),
    "authorized_software_sources": (
        "ITER-007/HELD-OUT/AUTHORIZED-SOFTWARE-SOURCES@1"
    ),
}

_SHA256 = re.compile(r"sha256:[0-9a-f]{64}")
_HMAC_SHA256 = re.compile(r"hmac-sha256:[0-9a-f]{64}")
_SHARED_SURFACE_KEYS = {
    "workspace_filesystem",
    "var_filesystem",
    "tmp_filesystem",
    "process_argv",
    "stdout_or_stderr",
    "agent_messages",
}
_FROZEN_TOP_LEVEL_KEYS = {
    "schema",
    "status",
    "protocol_digest",
    "holder",
    "generations",
    "commitment_scheme",
    "commitments",
    "public_digests",
    "counts",
    "baseline",
    "assertions",
    "disclosure",
    "production_activation",
    "document_digest",
}
_BLOCKED_TOP_LEVEL_KEYS = {
    "schema",
    "status",
    "protocol_digest",
    "blocker_code",
    "isolation_evidence_mode",
    "hidden_payload_materialized",
    "baseline_execution_status",
    "shared_surfaces_hidden_payload_touched",
    "v_pre_004",
    "production_activation",
    "document_digest",
}
_COUNT_KEYS = {
    "canary_001_project_count",
    "canary_001_answerable_count",
    "canary_001_without_symbol_count",
    "canary_001_cross_domain_count",
    "canary_002_project_count",
    "canary_002_answerable_count",
    "canary_002_without_symbol_count",
    "held_out_project_count",
    "held_out_question_count",
    "held_out_answerable_count",
    "held_out_boundary_count",
    "held_out_without_symbol_count",
    "held_out_without_symbol_per_project_minimum",
}
_ASSERTION_KEYS = {
    "canary_001_real_java_project",
    "canary_001_answerable_without_symbol",
    "canary_001_combines_legacy_calls_and_new_semantics",
    "canary_002_real_java_project",
    "canary_002_common_java_boundary",
    "canary_002_answerable_without_symbol",
    "held_out_real_java_maven_projects",
    "held_out_projects_not_used_for_implementation",
    "held_out_each_project_has_two_without_symbol",
    "held_out_four_question_classes_covered",
    "boundary_questions_source_insufficient_by_oracle",
    "canaries_and_held_out_mutually_distinct",
    "canaries_not_reused_as_held_out",
    "question_or_suite_driven_update_allowed",
    "burn_rule_frozen",
}


class HiddenFreezeFailure(RuntimeError):
    """The public hidden-freeze receipt is invalid or unsafe."""


def _canonical_json_bytes(value: object) -> bytes:
    _validate_json_value(value)
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _validate_json_value(value: object, *, location: str = "$") -> None:
    if value is None or isinstance(value, (bool, str)):
        return
    if isinstance(value, int):
        return
    if isinstance(value, float):
        raise HiddenFreezeFailure(f"floating-point value is forbidden at {location}")
    if isinstance(value, list):
        for index, item in enumerate(value):
            _validate_json_value(item, location=f"{location}[{index}]")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise HiddenFreezeFailure(f"non-string key is forbidden at {location}")
            _validate_json_value(item, location=f"{location}.{key}")
        return
    raise HiddenFreezeFailure(
        f"non-JSON value {type(value).__name__} is forbidden at {location}"
    )


def _sha256(value: object) -> str:
    return "sha256:" + hashlib.sha256(_canonical_json_bytes(value)).hexdigest()


def protocol_digest() -> str:
    """Bind the public protocol and both public validator implementations."""

    payload = PROTOCOL_PATH.read_bytes()
    loaded = _decode_json(payload, label="hidden-freeze protocol")
    if not isinstance(loaded, dict) or loaded.get("schema") != PROTOCOL_SCHEMA:
        raise HiddenFreezeFailure("hidden-freeze protocol schema is invalid")
    if loaded.get("commitment_domains") != COMMITMENT_DOMAINS:
        raise HiddenFreezeFailure("hidden-freeze commitment domains drifted")
    components = (
        PROTOCOL_PATH,
        Path(__file__),
        LIFECYCLE_VALIDATOR_PATH,
    )
    raw_digests: list[str] = []
    for component in components:
        if not component.is_file() or component.is_symlink():
            raise HiddenFreezeFailure("hidden-freeze protocol component is unavailable")
        raw_digests.append(
            "sha256:" + hashlib.sha256(component.read_bytes()).hexdigest()
        )
    return _sha256(raw_digests)


def commit_hidden_payload(
    secret: bytes, label: str, payload: object, *, generation: int = 1
) -> str:
    """Create a domain-separated commitment inside an evaluator-owned process.

    The caller must never invoke this with a real hidden payload in the shared
    workspace environment.  The function is exposed for copying/running in the
    required evaluator-owned external boundary and for public test vectors only.
    """

    if not isinstance(secret, bytes) or len(secret) < 32:
        raise HiddenFreezeFailure("commitment secret must contain at least 256 bits")
    domain = COMMITMENT_DOMAINS.get(label)
    if domain is None:
        raise HiddenFreezeFailure("unknown commitment label")
    if isinstance(generation, bool) or not isinstance(generation, int) or generation < 1:
        raise HiddenFreezeFailure("commitment generation must be a positive integer")
    payload_digest = "sha256:" + hashlib.sha256(
        _canonical_json_bytes(payload)
    ).hexdigest()
    message = _canonical_json_bytes(
        [
            COMMITMENT_SCHEMA,
            "ITER-007",
            label,
            domain,
            generation,
            protocol_digest(),
            payload_digest,
        ]
    )
    value = hmac.new(secret, message, hashlib.sha256).hexdigest()
    return "hmac-sha256:" + value


def public_commitment_digest(
    label: str, commitment: str, *, generation: int = 1
) -> str:
    """Derive the manifest-safe sha256 binding for a keyed commitment."""

    domain = COMMITMENT_DOMAINS.get(label)
    if domain is None:
        raise HiddenFreezeFailure("unknown commitment label")
    if _HMAC_SHA256.fullmatch(commitment) is None:
        raise HiddenFreezeFailure("commitment is not an HMAC-SHA-256 value")
    if isinstance(generation, bool) or not isinstance(generation, int) or generation < 1:
        raise HiddenFreezeFailure("commitment generation must be a positive integer")
    return _sha256(
        [
            COMMITMENT_SCHEMA,
            domain,
            generation,
            protocol_digest(),
            "HMAC-SHA-256",
            commitment,
        ]
    )


def verify_hidden_payload_opening(
    secret: bytes,
    label: str,
    payload: object,
    commitment: str,
    *,
    generation: int = 1,
) -> bool:
    """Verify a commitment opening inside the evaluator-owned boundary."""

    if not isinstance(commitment, str) or _HMAC_SHA256.fullmatch(commitment) is None:
        return False
    actual = commit_hidden_payload(
        secret,
        label,
        payload,
        generation=generation,
    )
    return hmac.compare_digest(actual, commitment)


def target_supported_count(baseline_supported_count: int) -> int:
    if isinstance(baseline_supported_count, bool) or not isinstance(
        baseline_supported_count, int
    ):
        raise HiddenFreezeFailure("baseline supported count must be an integer")
    if not 0 <= baseline_supported_count <= 12:
        raise HiddenFreezeFailure("baseline supported count must be between 0 and 12")
    return min(12, max(baseline_supported_count + 4, 8))


def build_blocked_receipt() -> dict[str, object]:
    """Build the only safe receipt when no evaluator-owned storage exists."""

    core: dict[str, object] = {
        "schema": RECEIPT_SCHEMA,
        "status": "BLOCKED",
        "protocol_digest": protocol_digest(),
        "blocker_code": "EVALUATOR_OWNED_STORAGE_UNAVAILABLE",
        "isolation_evidence_mode": "NONE",
        "hidden_payload_materialized": False,
        "baseline_execution_status": "NOT_EXECUTED",
        "shared_surfaces_hidden_payload_touched": {
            key: False for key in sorted(_SHARED_SURFACE_KEYS)
        },
        "v_pre_004": "BLOCKED",
        "production_activation": "NOT_EXECUTED",
    }
    return _seal_receipt(core)


def _seal_receipt(core: Mapping[str, object]) -> dict[str, object]:
    if "document_digest" in core:
        raise HiddenFreezeFailure("receipt core already has a document digest")
    copied = dict(core)
    return {**copied, "document_digest": _sha256([RECEIPT_SCHEMA, copied])}


def _require_mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, dict):
        raise HiddenFreezeFailure(f"{label} must be a mapping")
    return value


def _require_exact_keys(
    value: Mapping[str, object], expected: set[str], label: str
) -> None:
    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual)
        unknown = sorted(actual - expected)
        raise HiddenFreezeFailure(
            f"{label} fields are not closed: missing={missing}, unknown={unknown}"
        )


def _require_nonnegative_int(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise HiddenFreezeFailure(f"{label} must be a non-negative integer")
    return value


def _validate_document_digest(receipt: Mapping[str, object]) -> None:
    core = {key: value for key, value in receipt.items() if key != "document_digest"}
    expected = _sha256([RECEIPT_SCHEMA, core])
    if receipt.get("document_digest") != expected:
        raise HiddenFreezeFailure("public receipt document digest mismatch")


def _validate_shared_surfaces(value: object) -> None:
    surfaces = _require_mapping(value, "shared surface audit")
    _require_exact_keys(surfaces, _SHARED_SURFACE_KEYS, "shared surface audit")
    if any(item is not False for item in surfaces.values()):
        raise HiddenFreezeFailure("hidden payload touched a shared surface")


def _validate_blocked_receipt(receipt: Mapping[str, object]) -> None:
    _require_exact_keys(receipt, _BLOCKED_TOP_LEVEL_KEYS, "blocked receipt")
    expected = {
        "blocker_code": "EVALUATOR_OWNED_STORAGE_UNAVAILABLE",
        "isolation_evidence_mode": "NONE",
        "hidden_payload_materialized": False,
        "baseline_execution_status": "NOT_EXECUTED",
        "v_pre_004": "BLOCKED",
        "production_activation": "NOT_EXECUTED",
    }
    for field, value in expected.items():
        if receipt.get(field) != value:
            raise HiddenFreezeFailure(f"blocked receipt {field} is invalid")
    _validate_shared_surfaces(receipt["shared_surfaces_hidden_payload_touched"])


def _validate_holder(value: object) -> None:
    holder = _require_mapping(value, "holder")
    _require_exact_keys(
        holder,
        {
            "role",
            "implementation_actor",
            "holder_identity_digest",
            "storage_isolation",
            "assurance_ceiling",
            "isolation_evidence_status",
            "isolation_evidence_digest",
            "repository_validator_assurance",
            "cross_turn_recovery",
            "implementation_principal_access",
            "shared_surfaces_hidden_payload_touched",
        },
        "holder",
    )
    expected = {
        "role": "INDEPENDENT_EVALUATOR",
        "implementation_actor": "ROOT_IMPLEMENTATION_AGENT",
        "storage_isolation": "EXTERNAL_EVALUATOR_OWNED_ACL",
        "assurance_ceiling": "EXTERNAL_ACL_ATTESTED",
        "isolation_evidence_status": "EXTERNAL_ATTESTATION_PRESENT",
        "repository_validator_assurance": "SCHEMA_AND_BINDING_ONLY",
        "cross_turn_recovery": True,
        "implementation_principal_access": "DENIED",
    }
    for field, expected_value in expected.items():
        if holder.get(field) != expected_value:
            raise HiddenFreezeFailure(f"holder {field} is invalid")
    for field in ("holder_identity_digest", "isolation_evidence_digest"):
        evidence_digest = holder.get(field)
        if (
            not isinstance(evidence_digest, str)
            or _SHA256.fullmatch(evidence_digest) is None
        ):
            raise HiddenFreezeFailure(f"holder {field} is invalid")
    _validate_shared_surfaces(holder["shared_surfaces_hidden_payload_touched"])


def _validate_generations(value: object) -> Mapping[str, int]:
    generations = _require_mapping(value, "generations")
    labels = set(COMMITMENT_DOMAINS)
    _require_exact_keys(generations, labels, "generations")
    parsed: dict[str, int] = {}
    for label, generation in generations.items():
        parsed[label] = _require_nonnegative_int(
            generation, f"generations.{label}"
        )
        if parsed[label] < 1:
            raise HiddenFreezeFailure("commitment generation must be positive")
    groups = (
        ("canary_001_project_manifest", "canary_001_suite"),
        ("canary_002_project_manifest", "canary_002_suite"),
        (
            "held_out_project_manifest",
            "held_out_suite",
            "baseline_result",
            "authorized_software_sources",
        ),
    )
    for group in groups:
        if len({parsed[label] for label in group}) != 1:
            raise HiddenFreezeFailure("capsule commitment generations are inconsistent")
    return parsed


def _validate_commitment_scheme(value: object) -> None:
    scheme = _require_mapping(value, "commitment scheme")
    _require_exact_keys(
        scheme,
        {
            "algorithm",
            "secret_entropy_bits_minimum",
            "secret_generation",
            "domain_separated",
            "secret_storage",
            "secret_disclosed",
        },
        "commitment scheme",
    )
    expected = {
        "algorithm": "HMAC-SHA-256",
        "secret_entropy_bits_minimum": 256,
        "secret_generation": "CSPRNG_UNIQUE_PER_FREEZE",
        "domain_separated": True,
        "secret_storage": "EVALUATOR_OWNED_EXTERNAL_ONLY",
        "secret_disclosed": False,
    }
    for field, expected_value in expected.items():
        if scheme.get(field) != expected_value:
            raise HiddenFreezeFailure(f"commitment scheme {field} is invalid")


def _validate_commitments(
    commitments_value: object,
    public_digests_value: object,
    generations: Mapping[str, int],
) -> None:
    commitments = _require_mapping(commitments_value, "commitments")
    public_digests = _require_mapping(public_digests_value, "public digests")
    labels = set(COMMITMENT_DOMAINS)
    _require_exact_keys(commitments, labels, "commitments")
    _require_exact_keys(public_digests, labels, "public digests")
    for label in sorted(labels):
        commitment = commitments[label]
        if not isinstance(commitment, str) or _HMAC_SHA256.fullmatch(commitment) is None:
            raise HiddenFreezeFailure(f"{label} commitment is invalid")
        expected = public_commitment_digest(
            label, commitment, generation=generations[label]
        )
        if public_digests[label] != expected:
            raise HiddenFreezeFailure(f"{label} public digest mismatch")
    if len(set(commitments.values())) != len(commitments):
        raise HiddenFreezeFailure("commitment values must be distinct")


def _validate_counts(value: object) -> None:
    counts = _require_mapping(value, "counts")
    _require_exact_keys(counts, _COUNT_KEYS, "counts")
    parsed = {
        key: _require_nonnegative_int(item, f"counts.{key}")
        for key, item in counts.items()
    }
    exact = {
        "canary_001_project_count": 1,
        "canary_002_project_count": 1,
        "held_out_project_count": 2,
        "held_out_question_count": 16,
        "held_out_answerable_count": 12,
        "held_out_boundary_count": 4,
        "held_out_without_symbol_per_project_minimum": 2,
    }
    for field, expected in exact.items():
        if parsed[field] != expected:
            raise HiddenFreezeFailure(f"counts.{field} must equal {expected}")
    minimums = {
        "canary_001_answerable_count": 1,
        "canary_001_without_symbol_count": 1,
        "canary_001_cross_domain_count": 1,
        "canary_002_answerable_count": 1,
        "canary_002_without_symbol_count": 1,
        "held_out_without_symbol_count": 6,
    }
    for field, minimum in minimums.items():
        if parsed[field] < minimum:
            raise HiddenFreezeFailure(f"counts.{field} must be at least {minimum}")
    if parsed["canary_001_without_symbol_count"] > parsed[
        "canary_001_answerable_count"
    ]:
        raise HiddenFreezeFailure("canary 001 without-symbol count exceeds answerable")
    if parsed["canary_002_without_symbol_count"] > parsed[
        "canary_002_answerable_count"
    ]:
        raise HiddenFreezeFailure("canary 002 without-symbol count exceeds answerable")
    if parsed["held_out_without_symbol_count"] > 12:
        raise HiddenFreezeFailure("held-out without-symbol count exceeds answerable")


def _validate_baseline(value: object) -> None:
    baseline = _require_mapping(value, "baseline")
    _require_exact_keys(
        baseline,
        {
            "accepted_commit",
            "accepted_tree",
            "execution_status",
            "execution_evidence",
            "supported_answerable_count",
            "target_supported_count",
            "target_formula",
            "mature_source_agent_protocol_status",
        },
        "baseline",
    )
    expected = {
        "accepted_commit": ACCEPTED_BASELINE_COMMIT,
        "accepted_tree": ACCEPTED_BASELINE_TREE,
        "execution_status": "EXECUTED_ON_ACCEPTED_BASELINE",
        "execution_evidence": "EVALUATOR_ATTESTED_COMMITTED_RESULT",
        "target_formula": "min(12,max(baseline_supported+4,8))",
        "mature_source_agent_protocol_status": "FROZEN",
    }
    for field, expected_value in expected.items():
        if baseline.get(field) != expected_value:
            raise HiddenFreezeFailure(f"baseline {field} is invalid")
    supported = _require_nonnegative_int(
        baseline.get("supported_answerable_count"),
        "baseline.supported_answerable_count",
    )
    target = _require_nonnegative_int(
        baseline.get("target_supported_count"),
        "baseline.target_supported_count",
    )
    if target != target_supported_count(supported):
        raise HiddenFreezeFailure("baseline target does not match the frozen formula")


def _validate_assertions(value: object) -> None:
    assertions = _require_mapping(value, "assertions")
    _require_exact_keys(assertions, _ASSERTION_KEYS, "assertions")
    for key, item in assertions.items():
        expected = False if key == "question_or_suite_driven_update_allowed" else True
        if item is not expected:
            raise HiddenFreezeFailure(f"assertion {key} is invalid")


def _validate_disclosure(value: object) -> None:
    disclosure = _require_mapping(value, "disclosure")
    _require_exact_keys(
        disclosure,
        {
            "implementation_visibility",
            "canary_001",
            "canary_002",
            "held_out",
            "hidden_content_in_receipt",
        },
        "disclosure",
    )
    expected = {
        "implementation_visibility": "HIDDEN_UNTIL_APPLICABLE_CODE_FREEZE",
        "canary_001": "NOT_DISCLOSED",
        "canary_002": "NOT_DISCLOSED",
        "held_out": "NOT_DISCLOSED",
        "hidden_content_in_receipt": False,
    }
    for field, expected_value in expected.items():
        if disclosure.get(field) != expected_value:
            raise HiddenFreezeFailure(f"disclosure {field} is invalid")


def _validate_frozen_receipt(receipt: Mapping[str, object]) -> None:
    _require_exact_keys(receipt, _FROZEN_TOP_LEVEL_KEYS, "frozen receipt")
    _validate_holder(receipt["holder"])
    _validate_commitment_scheme(receipt["commitment_scheme"])
    generations = _validate_generations(receipt["generations"])
    _validate_commitments(
        receipt["commitments"], receipt["public_digests"], generations
    )
    _validate_counts(receipt["counts"])
    _validate_baseline(receipt["baseline"])
    _validate_assertions(receipt["assertions"])
    _validate_disclosure(receipt["disclosure"])
    if receipt.get("production_activation") != "NOT_EXECUTED":
        raise HiddenFreezeFailure("Production Activation must remain NOT_EXECUTED")


def validate_public_receipt(receipt: object) -> Mapping[str, object]:
    """Validate a closed public receipt without accessing any hidden payload."""

    value = _require_mapping(receipt, "public receipt")
    _validate_json_value(value)
    if value.get("schema") != RECEIPT_SCHEMA:
        raise HiddenFreezeFailure("public receipt schema is invalid")
    if value.get("protocol_digest") != protocol_digest():
        raise HiddenFreezeFailure("public receipt protocol digest mismatch")
    status = value.get("status")
    if status == "FROZEN":
        _validate_frozen_receipt(value)
    elif status == "BLOCKED":
        _validate_blocked_receipt(value)
    else:
        raise HiddenFreezeFailure("public receipt status is invalid")
    _validate_document_digest(value)
    return value


def manifest_bindings(receipt: object) -> dict[str, object]:
    """Return only the non-sensitive Manifest fields from a valid frozen receipt."""

    value = validate_public_receipt(receipt)
    if value["status"] != "FROZEN":
        raise HiddenFreezeFailure("blocked receipt has no hidden-input bindings")
    public = _require_mapping(value["public_digests"], "public digests")
    counts = _require_mapping(value["counts"], "counts")
    baseline = _require_mapping(value["baseline"], "baseline")
    return {
        "hidden_freeze_protocol_digest": value["protocol_digest"],
        "canary_001_project_manifest_digest": public[
            "canary_001_project_manifest"
        ],
        "canary_001_suite_digest": public["canary_001_suite"],
        "canary_002_project_manifest_digest": public[
            "canary_002_project_manifest"
        ],
        "canary_002_suite_digest": public["canary_002_suite"],
        "evaluation_project_manifest_digest": public[
            "held_out_project_manifest"
        ],
        "held_out_suite_digest": public["held_out_suite"],
        "baseline_result_digest": public["baseline_result"],
        "mature_source_agent_protocol_digest": public[
            "mature_source_agent_protocol"
        ],
        "authorized_software_sources_digest": public[
            "authorized_software_sources"
        ],
        "held_out_baseline_supported_count": baseline[
            "supported_answerable_count"
        ],
        "held_out_target_supported_count": baseline["target_supported_count"],
        "held_out_question_count": counts["held_out_question_count"],
        "held_out_answerable_question_count": counts[
            "held_out_answerable_count"
        ],
        "held_out_boundary_question_count": counts["held_out_boundary_count"],
        "held_out_answerable_without_symbol_count_minimum": counts[
            "held_out_without_symbol_count"
        ],
        "held_out_answerable_without_symbol_per_project_minimum": counts[
            "held_out_without_symbol_per_project_minimum"
        ],
    }


def evaluate_public_receipt(receipt: object) -> dict[str, object]:
    value = validate_public_receipt(receipt)
    if value["status"] == "BLOCKED":
        return {
            "schema": "SWM-ITER-007-HIDDEN-FREEZE-EVALUATION@1",
            "status": "BLOCKED",
            "v_pre_004": "NOT_PASS",
            "blocker_code": value["blocker_code"],
            "hidden_payload_materialized": False,
            "protocol_digest": value["protocol_digest"],
            "production_activation": "NOT_EXECUTED",
        }
    return {
        "schema": "SWM-ITER-007-HIDDEN-FREEZE-EVALUATION@1",
        "status": "PASS",
        "v_pre_004": "PASS",
        "manifest_bindings": manifest_bindings(value),
        "hidden_payload_disclosed": False,
        "baseline_execution": "EXECUTED",
        "isolation_evidence_mode": "EXTERNAL_EVALUATOR_OWNED_ACL_ATTESTED",
        "repository_validator_assurance": "SCHEMA_AND_BINDING_ONLY",
        "production_activation": "NOT_EXECUTED",
    }


def _reject_duplicate_keys(pairs: Sequence[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise HiddenFreezeFailure(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def _decode_json(payload: bytes, *, label: str) -> object:
    try:
        return json.loads(
            payload.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=lambda value: (_ for _ in ()).throw(
                HiddenFreezeFailure(f"invalid JSON constant in {label}: {value}")
            ),
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise HiddenFreezeFailure(f"{label} is not strict UTF-8 JSON") from error


def load_public_receipt(path: Path) -> Mapping[str, object]:
    if path.is_symlink():
        raise HiddenFreezeFailure("public receipt must not be a symlink")
    try:
        metadata = path.stat()
    except FileNotFoundError as error:
        raise HiddenFreezeFailure("public receipt does not exist") from error
    if not stat.S_ISREG(metadata.st_mode):
        raise HiddenFreezeFailure("public receipt must be a regular file")
    if metadata.st_size > MAXIMUM_PUBLIC_RECEIPT_BYTES:
        raise HiddenFreezeFailure("public receipt exceeds the size limit")
    payload = path.read_bytes()
    loaded = _decode_json(payload, label="public receipt")
    if _canonical_json_bytes(loaded) != payload:
        raise HiddenFreezeFailure("public receipt is not canonical JSON")
    return validate_public_receipt(loaded)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate only the public side of the ITER-007 hidden freeze."
    )
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--protocol-digest", action="store_true")
    action.add_argument("--print-blocked-receipt", action="store_true")
    action.add_argument("--validate-public-receipt", type=Path)
    arguments = parser.parse_args(argv)
    try:
        if arguments.protocol_digest:
            print(protocol_digest())
        elif arguments.print_blocked_receipt:
            print(_canonical_json_bytes(build_blocked_receipt()).decode("utf-8"))
        else:
            receipt = load_public_receipt(arguments.validate_public_receipt)
            print(_canonical_json_bytes(evaluate_public_receipt(receipt)).decode("utf-8"))
    except HiddenFreezeFailure as error:
        parser.exit(2, f"hidden-freeze validation failed: {error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
