"""Public lifecycle receipts for ITER-007 hidden evaluation capsules.

All inputs handled here are public commitments or product-code metadata.  This
module never accepts a hidden project, source file, question, answer, or secret.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
import stat
from typing import Mapping

from . import hidden_freeze as freeze


CODE_FREEZE_SCHEMA = "SWM-ITER-007-PRODUCT-CODE-FREEZE-RECEIPT@1"
DISCLOSURE_SCHEMA = "SWM-ITER-007-HIDDEN-DISCLOSURE-RECEIPT@1"
BURN_SCHEMA = "SWM-ITER-007-HIDDEN-BURN-RECEIPT@1"

CAPSULE_LABELS = {
    "CANARY_001": (
        "canary_001_project_manifest",
        "canary_001_suite",
    ),
    "CANARY_002": (
        "canary_002_project_manifest",
        "canary_002_suite",
    ),
    "HELD_OUT": (
        "held_out_project_manifest",
        "held_out_suite",
        "baseline_result",
        "authorized_software_sources",
    ),
}

_CODE_FREEZE_KEYS = {
    "schema",
    "status",
    "protocol_digest",
    "capsule",
    "generation",
    "commitment_receipt_digest",
    "freeze_scope",
    "canonical_fileset_digest",
    "external_evaluation_harness_digest",
    "created_before_disclosure",
    "pre_disclosure_shared_surface_count",
    "production_activation",
    "document_digest",
}
_FREEZE_SCOPE_KEYS = {
    "src",
    "prompt_and_role_package",
    "launcher_and_policy",
    "dependency_and_frontend_binding",
    "evaluation_harness",
}
_DISCLOSURE_KEYS = {
    "schema",
    "status",
    "protocol_digest",
    "capsule",
    "generation",
    "commitment_receipt_digest",
    "code_freeze_receipt_digest",
    "opening_evidence_digest",
    "opening_verification",
    "authorization_status",
    "first_exposure_sequence",
    "pre_exposure_shared_surface_count",
    "attempt_count",
    "execution_seal",
    "result_status",
    "result_digest",
    "pre_execution_freeze_recheck",
    "post_execution_freeze_recheck",
    "post_exposure_product_change_count",
    "result_seal_status",
    "capsule_consumption_status",
    "burn_status",
    "production_activation",
    "document_digest",
}
_BURN_KEYS = {
    "schema",
    "status",
    "protocol_digest",
    "capsule",
    "generation",
    "commitment_receipt_digest",
    "code_freeze_receipt_digest",
    "disclosure_receipt_digest",
    "trigger",
    "original_result_preservation",
    "original_result_digest",
    "replacement_rule",
    "minimum_next_generation",
    "production_activation",
    "document_digest",
}
_BURN_TRIGGERS = {
    "EARLY_DISCLOSURE",
    "SHARED_SURFACE_EXPOSURE",
    "COMMITMENT_MISMATCH",
    "PRODUCT_FREEZE_DRIFT",
    "UNSEALED_EXECUTION",
    "REPEATED_ATTEMPT",
    "PRODUCT_CHANGE_AFTER_DISCLOSURE",
}
_RESULT_STATUSES = {"PASS", "FAIL", "EXECUTION_FAILURE"}


def _seal(schema: str, core: Mapping[str, object]) -> dict[str, object]:
    if "document_digest" in core:
        raise freeze.HiddenFreezeFailure("receipt core already has a digest")
    copied = dict(core)
    return {**copied, "document_digest": freeze._sha256([schema, copied])}


def _validate_digest(value: object, label: str) -> str:
    if not isinstance(value, str) or freeze._SHA256.fullmatch(value) is None:
        raise freeze.HiddenFreezeFailure(f"{label} must be an exact sha256 digest")
    return value


def _validate_positive_int(value: object, label: str) -> int:
    parsed = freeze._require_nonnegative_int(value, label)
    if parsed < 1:
        raise freeze.HiddenFreezeFailure(f"{label} must be positive")
    return parsed


def _capsule_generation(
    commitment_receipt: Mapping[str, object], capsule: str
) -> int:
    labels = CAPSULE_LABELS.get(capsule)
    if labels is None:
        raise freeze.HiddenFreezeFailure("unknown hidden-evaluation capsule")
    generations = freeze._require_mapping(
        commitment_receipt["generations"], "commitment generations"
    )
    values = {_validate_positive_int(generations[label], label) for label in labels}
    if len(values) != 1:
        raise freeze.HiddenFreezeFailure("capsule has inconsistent generations")
    return values.pop()


def _validate_document_digest(
    receipt: Mapping[str, object], schema: str
) -> None:
    core = {key: value for key, value in receipt.items() if key != "document_digest"}
    if receipt.get("document_digest") != freeze._sha256([schema, core]):
        raise freeze.HiddenFreezeFailure("lifecycle receipt digest mismatch")


def _included_product_files(repository: Path) -> list[Path]:
    fixed = (
        repository / "src",
        repository / "pyproject.toml",
        repository / "docs/project/iterations/iteration-007/manifest.yaml",
        repository / "validation/structure_world_model_iteration_007",
    )
    files: list[Path] = []
    for path in fixed:
        if path.is_symlink() or not path.exists():
            raise freeze.HiddenFreezeFailure("product code-freeze input is unavailable")
        if path.is_file():
            files.append(path)
            continue
        for member in path.rglob("*"):
            relative_parts = member.relative_to(repository).parts
            if "__pycache__" in relative_parts or member.suffix in {
                ".pyc",
                ".pyo",
            }:
                continue
            metadata = member.lstat()
            if stat.S_ISLNK(metadata.st_mode):
                raise freeze.HiddenFreezeFailure("symlink in product code-freeze input")
            if stat.S_ISREG(metadata.st_mode):
                files.append(member)
            elif not stat.S_ISDIR(metadata.st_mode):
                raise freeze.HiddenFreezeFailure(
                    "unsupported product code-freeze input"
                )
    return sorted(set(files), key=lambda path: path.relative_to(repository).as_posix())


def product_fileset_digest(repository: Path) -> str:
    root = repository.resolve(strict=True)
    manifest: list[dict[str, object]] = []
    for path in _included_product_files(root):
        payload = path.read_bytes()
        manifest.append(
            {
                "path": path.relative_to(root).as_posix(),
                "size": len(payload),
                "digest": "sha256:" + hashlib.sha256(payload).hexdigest(),
            }
        )
    if not manifest:
        raise freeze.HiddenFreezeFailure("product code-freeze fileset is empty")
    return freeze._sha256(
        ["SWM-ITER-007-PRODUCT-CODE-FILESET@1", manifest]
    )


def build_product_code_freeze_receipt(
    *,
    repository: Path,
    capsule: str,
    commitment_receipt: object,
    external_evaluation_harness_digest: str,
) -> dict[str, object]:
    commitment = freeze.validate_public_receipt(commitment_receipt)
    if commitment["status"] != "FROZEN":
        raise freeze.HiddenFreezeFailure("code freeze requires a frozen commitment")
    generation = _capsule_generation(commitment, capsule)
    _validate_digest(
        external_evaluation_harness_digest,
        "external evaluation harness digest",
    )
    core: dict[str, object] = {
        "schema": CODE_FREEZE_SCHEMA,
        "status": "FROZEN",
        "protocol_digest": freeze.protocol_digest(),
        "capsule": capsule,
        "generation": generation,
        "commitment_receipt_digest": commitment["document_digest"],
        "freeze_scope": {key: True for key in sorted(_FREEZE_SCOPE_KEYS)},
        "canonical_fileset_digest": product_fileset_digest(repository),
        "external_evaluation_harness_digest": (
            external_evaluation_harness_digest
        ),
        "created_before_disclosure": True,
        "pre_disclosure_shared_surface_count": 0,
        "production_activation": "NOT_EXECUTED",
    }
    return _seal(CODE_FREEZE_SCHEMA, core)


def validate_product_code_freeze_receipt(receipt: object) -> Mapping[str, object]:
    value = freeze._require_mapping(receipt, "product code-freeze receipt")
    freeze._require_exact_keys(value, _CODE_FREEZE_KEYS, "code-freeze receipt")
    if value.get("schema") != CODE_FREEZE_SCHEMA or value.get("status") != "FROZEN":
        raise freeze.HiddenFreezeFailure("product code-freeze status is invalid")
    if value.get("protocol_digest") != freeze.protocol_digest():
        raise freeze.HiddenFreezeFailure("product code-freeze protocol drifted")
    if value.get("capsule") not in CAPSULE_LABELS:
        raise freeze.HiddenFreezeFailure("product code-freeze capsule is invalid")
    _validate_positive_int(value.get("generation"), "code-freeze generation")
    _validate_digest(value.get("commitment_receipt_digest"), "commitment receipt")
    scope = freeze._require_mapping(value.get("freeze_scope"), "freeze scope")
    freeze._require_exact_keys(scope, _FREEZE_SCOPE_KEYS, "freeze scope")
    if any(item is not True for item in scope.values()):
        raise freeze.HiddenFreezeFailure("product code-freeze scope is incomplete")
    _validate_digest(value.get("canonical_fileset_digest"), "product fileset")
    _validate_digest(
        value.get("external_evaluation_harness_digest"),
        "external evaluation harness",
    )
    if value.get("created_before_disclosure") is not True:
        raise freeze.HiddenFreezeFailure("code freeze was not created before disclosure")
    if value.get("pre_disclosure_shared_surface_count") != 0:
        raise freeze.HiddenFreezeFailure("hidden input reached a shared surface")
    if value.get("production_activation") != "NOT_EXECUTED":
        raise freeze.HiddenFreezeFailure("Production Activation must not execute")
    _validate_document_digest(value, CODE_FREEZE_SCHEMA)
    return value


def validate_code_freeze_chain(
    *,
    repository: Path,
    commitment_receipt: object,
    code_freeze_receipt: object,
) -> None:
    commitment = freeze.validate_public_receipt(commitment_receipt)
    code_freeze = validate_product_code_freeze_receipt(code_freeze_receipt)
    if commitment["status"] != "FROZEN":
        raise freeze.HiddenFreezeFailure("commitment receipt is not frozen")
    if code_freeze["commitment_receipt_digest"] != commitment["document_digest"]:
        raise freeze.HiddenFreezeFailure("code freeze binds another commitment")
    expected_generation = _capsule_generation(
        commitment, str(code_freeze["capsule"])
    )
    if code_freeze["generation"] != expected_generation:
        raise freeze.HiddenFreezeFailure("code freeze generation mismatch")
    if code_freeze["canonical_fileset_digest"] != product_fileset_digest(repository):
        raise freeze.HiddenFreezeFailure("product code freeze drifted")


def validate_disclosure_receipt(receipt: object) -> Mapping[str, object]:
    value = freeze._require_mapping(receipt, "disclosure receipt")
    freeze._require_exact_keys(value, _DISCLOSURE_KEYS, "disclosure receipt")
    if value.get("schema") != DISCLOSURE_SCHEMA or value.get("status") != "DISCLOSED":
        raise freeze.HiddenFreezeFailure("disclosure receipt status is invalid")
    if value.get("protocol_digest") != freeze.protocol_digest():
        raise freeze.HiddenFreezeFailure("disclosure protocol drifted")
    if value.get("capsule") not in CAPSULE_LABELS:
        raise freeze.HiddenFreezeFailure("disclosure capsule is invalid")
    _validate_positive_int(value.get("generation"), "disclosure generation")
    for field in (
        "commitment_receipt_digest",
        "code_freeze_receipt_digest",
        "opening_evidence_digest",
        "result_digest",
    ):
        _validate_digest(value.get(field), field)
    expected = {
        "opening_verification": "PASS",
        "authorization_status": "AUTHORIZED_AFTER_CODE_FREEZE",
        "first_exposure_sequence": 1,
        "pre_exposure_shared_surface_count": 0,
        "attempt_count": 1,
        "execution_seal": "SEALED_SINGLE_ATTEMPT",
        "pre_execution_freeze_recheck": "PASS",
        "post_execution_freeze_recheck": "PASS",
        "post_exposure_product_change_count": 0,
        "result_seal_status": "SEALED_BEFORE_NEXT_PRODUCT_CHANGE",
        "capsule_consumption_status": "CONSUMED_AFTER_RESULT_SEAL",
        "burn_status": "NOT_BURNED",
        "production_activation": "NOT_EXECUTED",
    }
    for field, expected_value in expected.items():
        if value.get(field) != expected_value:
            raise freeze.HiddenFreezeFailure(f"disclosure {field} is invalid")
    if value.get("result_status") not in _RESULT_STATUSES:
        raise freeze.HiddenFreezeFailure("disclosure result status is invalid")
    _validate_document_digest(value, DISCLOSURE_SCHEMA)
    return value


def validate_disclosure_chain(
    *,
    repository: Path,
    commitment_receipt: object,
    code_freeze_receipt: object,
    disclosure_receipt: object,
) -> None:
    commitment = freeze.validate_public_receipt(commitment_receipt)
    validate_code_freeze_chain(
        repository=repository,
        commitment_receipt=commitment,
        code_freeze_receipt=code_freeze_receipt,
    )
    code_freeze = validate_product_code_freeze_receipt(code_freeze_receipt)
    disclosure = validate_disclosure_receipt(disclosure_receipt)
    if commitment["status"] != "FROZEN":
        raise freeze.HiddenFreezeFailure("disclosure requires frozen commitments")
    if disclosure["commitment_receipt_digest"] != commitment["document_digest"]:
        raise freeze.HiddenFreezeFailure("disclosure binds another commitment")
    if disclosure["code_freeze_receipt_digest"] != code_freeze["document_digest"]:
        raise freeze.HiddenFreezeFailure("disclosure binds another code freeze")
    if disclosure["capsule"] != code_freeze["capsule"]:
        raise freeze.HiddenFreezeFailure("disclosure capsule mismatch")
    if disclosure["generation"] != code_freeze["generation"]:
        raise freeze.HiddenFreezeFailure("disclosure generation mismatch")


def validate_burn_receipt(receipt: object) -> Mapping[str, object]:
    value = freeze._require_mapping(receipt, "burn receipt")
    freeze._require_exact_keys(value, _BURN_KEYS, "burn receipt")
    if value.get("schema") != BURN_SCHEMA or value.get("status") != "BURNED":
        raise freeze.HiddenFreezeFailure("burn receipt status is invalid")
    if value.get("protocol_digest") != freeze.protocol_digest():
        raise freeze.HiddenFreezeFailure("burn protocol drifted")
    capsule = value.get("capsule")
    if capsule not in CAPSULE_LABELS:
        raise freeze.HiddenFreezeFailure("burn capsule is invalid")
    generation = _validate_positive_int(value.get("generation"), "burn generation")
    _validate_digest(value.get("commitment_receipt_digest"), "commitment receipt")
    for field in ("code_freeze_receipt_digest", "disclosure_receipt_digest"):
        item = value.get(field)
        if item != "NOT_AVAILABLE":
            _validate_digest(item, field)
    if value.get("trigger") not in _BURN_TRIGGERS:
        raise freeze.HiddenFreezeFailure("burn trigger is invalid")
    preservation = value.get("original_result_preservation")
    result_digest = value.get("original_result_digest")
    if preservation == "PRESERVED":
        _validate_digest(result_digest, "original result")
    elif preservation == "NO_RESULT_AVAILABLE":
        if result_digest != "NOT_AVAILABLE":
            raise freeze.HiddenFreezeFailure("absent burn result has a digest")
    else:
        raise freeze.HiddenFreezeFailure("burn result preservation is invalid")
    expected_rule = (
        "REPLACE_TWO_PROJECTS_COMPLETE_SUITE_BASELINE_AND_TARGET"
        if capsule == "HELD_OUT"
        else "REPLACE_PROJECT_AND_SUITE"
    )
    if value.get("replacement_rule") != expected_rule:
        raise freeze.HiddenFreezeFailure("burn replacement rule is invalid")
    if value.get("minimum_next_generation") != generation + 1:
        raise freeze.HiddenFreezeFailure("burn next generation is invalid")
    if value.get("production_activation") != "NOT_EXECUTED":
        raise freeze.HiddenFreezeFailure("Production Activation must not execute")
    _validate_document_digest(value, BURN_SCHEMA)
    return value


def validate_replacement_after_burn(
    *,
    burned_commitment_receipt: object,
    replacement_commitment_receipt: object,
    burn_receipt: object,
) -> None:
    burned = freeze.validate_public_receipt(burned_commitment_receipt)
    replacement = freeze.validate_public_receipt(replacement_commitment_receipt)
    burn = validate_burn_receipt(burn_receipt)
    if burned["status"] != "FROZEN" or replacement["status"] != "FROZEN":
        raise freeze.HiddenFreezeFailure("replacement requires frozen receipts")
    if burn["commitment_receipt_digest"] != burned["document_digest"]:
        raise freeze.HiddenFreezeFailure("burn binds another commitment receipt")
    capsule = str(burn["capsule"])
    old_generations = freeze._require_mapping(burned["generations"], "generations")
    new_generations = freeze._require_mapping(
        replacement["generations"], "generations"
    )
    old_commitments = freeze._require_mapping(
        burned["commitments"], "commitments"
    )
    new_commitments = freeze._require_mapping(
        replacement["commitments"], "commitments"
    )
    for label in CAPSULE_LABELS[capsule]:
        if new_generations[label] < burn["minimum_next_generation"]:
            raise freeze.HiddenFreezeFailure("replacement generation did not advance")
        if new_generations[label] <= old_generations[label]:
            raise freeze.HiddenFreezeFailure("replacement generation was reused")
        if new_commitments[label] == old_commitments[label]:
            raise freeze.HiddenFreezeFailure("burned hidden input was reused")
