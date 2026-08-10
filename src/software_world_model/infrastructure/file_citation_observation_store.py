"""Digest-bound disposable file store for isolated Citation Projectors."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
from typing import Any, Mapping, Sequence

from software_world_model.application_services.citation_projection import (
    CitationEvidenceReference,
    CitationObservation,
    CitationStoreReceipt,
    CitationStoreSnapshot,
    StructureViewResultSeal,
)
from software_world_model.cross_cutting import (
    Digest,
    DomainError,
    ErrorCode,
    StableId,
    canonical_json_bytes,
    digest_of,
)


_STORE_FORMAT = "CITATION_OBSERVATION_STORE@1"
_OBSERVATION_FORMAT = "CITATION_OBSERVATION_FILE@1"
_RESULT_FORMAT = "STRUCTURE_VIEW_RESULT_CITATION_SEAL@1"
_MANIFEST_NAME = "manifest.json"
_OBSERVATIONS_NAME = "observations"


class _FileCitationObservationStoreBackend:
    """Private codec shared by capability-narrow public adapters."""

    def __init__(self, root: str | os.PathLike[str]) -> None:
        self._root = _canonical_absolute_path(root, "Citation Store root")

    @property
    def root(self) -> Path:
        return self._root

    def create_disposable_store(
        self,
        *,
        result: StructureViewResultSeal,
        observations: tuple[CitationObservation, ...],
    ) -> CitationStoreReceipt:
        if not isinstance(result, StructureViewResultSeal):
            _invalid(
                "CITATION_RESULT_SEAL_REQUIRED",
                "Citation Store requires a typed sealed Structure View Result",
            )
        result.require_valid()
        if not isinstance(observations, tuple):
            _invalid(
                "CITATION_STORE_OBSERVATIONS_MUTABLE",
                "Citation Store observations must be immutable",
            )
        for observation in observations:
            if not isinstance(observation, CitationObservation):
                _invalid(
                    "CITATION_STORE_OBSERVATION_INVALID",
                    "Citation Store received an untyped observation",
                )
            observation.require_valid()
        if tuple(item.reference for item in observations) != result.evidence_allowlist:
            _inconsistent(
                "CITATION_STORE_ALLOWLIST_MISMATCH",
                "Citation Store input is missing, extra, duplicated, or reordered",
            )

        parent = self._root.parent
        _require_existing_directory(parent, "Citation Store parent")
        if _lexists(self._root):
            _invalid(
                "CITATION_STORE_ALREADY_EXISTS",
                "Disposable Citation Store target must not already exist",
            )
        os.mkdir(self._root, 0o700)
        observations_directory = self._root / _OBSERVATIONS_NAME
        os.mkdir(observations_directory, 0o700)

        manifest_entries: list[dict[str, str]] = []
        for observation in observations:
            evidence_id = observation.reference.evidence_id.value
            relative_path = f"{_OBSERVATIONS_NAME}/{evidence_id}.json"
            payload = _observation_payload(observation)
            encoded = canonical_json_bytes(payload)
            file_digest = _raw_digest(encoded)
            _write_new_regular_file(
                observations_directory / f"{evidence_id}.json",
                encoded,
            )
            manifest_entries.append(
                {
                    "evidence_id": evidence_id,
                    "evidence_digest": observation.reference.evidence_digest.value,
                    "observation_digest": observation.digest.value,
                    "path": relative_path,
                    "file_digest": file_digest.value,
                }
            )

        entries = tuple(manifest_entries)
        store_binding_digest = digest_of(
            [
                "CITATION_STORE_BINDING@1",
                {
                    "result_id": result.result_id.value,
                    "result_digest": result.digest.value,
                    "allowlist_digest": result.allowlist_digest.value,
                    "entries": entries,
                },
            ]
        )
        store_id = StableId(
            "citation_store_"
            + store_binding_digest.value.removeprefix("sha256:")[-32:]
        )
        manifest_core: dict[str, object] = {
            "format_ref": _STORE_FORMAT,
            "store_id": store_id.value,
            "disposable": True,
            "result_id": result.result_id.value,
            "result_digest": result.digest.value,
            "view_digest": result.view_digest.value,
            "allowlist_digest": result.allowlist_digest.value,
            "observation_count": len(entries),
            "entries": entries,
        }
        manifest_digest = digest_of(["CITATION_STORE_MANIFEST@1", manifest_core])
        manifest = {**manifest_core, "manifest_digest": manifest_digest.value}
        _write_new_regular_file(
            self._root / _MANIFEST_NAME,
            canonical_json_bytes(manifest),
        )
        receipt = CitationStoreReceipt(
            store_id=store_id,
            result_id=result.result_id,
            result_digest=result.digest,
            allowlist_digest=result.allowlist_digest,
            manifest_digest=manifest_digest,
            observation_count=len(entries),
            disposable=True,
        )
        receipt.require_valid()
        return receipt

    def read_exact(
        self, result: StructureViewResultSeal
    ) -> CitationStoreSnapshot:
        if not isinstance(result, StructureViewResultSeal):
            _invalid(
                "CITATION_RESULT_SEAL_REQUIRED",
                "Citation Store requires a typed sealed Structure View Result",
            )
        result.require_valid()
        _require_existing_directory(self._root, "Citation Store root")
        root_names = {item.name for item in self._root.iterdir()}
        if root_names != {_MANIFEST_NAME, _OBSERVATIONS_NAME}:
            _inconsistent(
                "CITATION_STORE_ROOT_ENTRIES_INVALID",
                "Citation Store contains missing or unknown root entries",
            )
        observations_directory = self._root / _OBSERVATIONS_NAME
        _require_existing_directory(
            observations_directory, "Citation observations directory"
        )
        manifest_value = _read_canonical_json(
            self._root / _MANIFEST_NAME, "Citation Store manifest"
        )
        manifest = _mapping(manifest_value, "Citation Store manifest")
        _exact_keys(
            manifest,
            {
                "format_ref",
                "store_id",
                "disposable",
                "result_id",
                "result_digest",
                "view_digest",
                "allowlist_digest",
                "observation_count",
                "entries",
                "manifest_digest",
            },
            "Citation Store manifest",
        )
        if manifest["format_ref"] != _STORE_FORMAT or manifest["disposable"] is not True:
            _invalid(
                "CITATION_STORE_FORMAT_INVALID",
                "Citation Store format or disposable marker is invalid",
            )
        entries_value = manifest["entries"]
        if not isinstance(entries_value, list):
            _invalid(
                "CITATION_STORE_ENTRIES_INVALID",
                "Citation Store manifest entries must be a list",
            )
        entries = tuple(
            _parse_manifest_entry(item, index)
            for index, item in enumerate(entries_value)
        )
        entry_ids = tuple(item["evidence_id"] for item in entries)
        if len(entry_ids) != len(set(entry_ids)):
            _invalid(
                "CITATION_STORE_DUPLICATE_EVIDENCE",
                "Citation Store manifest duplicates an Evidence identity",
            )
        if entry_ids != tuple(sorted(entry_ids)):
            _invalid(
                "CITATION_STORE_NONCANONICAL_ORDER",
                "Citation Store manifest entries are not canonically ordered",
            )
        if type(manifest["observation_count"]) is not int or (
            manifest["observation_count"] != len(entries)
        ):
            _inconsistent(
                "CITATION_STORE_COUNT_MISMATCH",
                "Citation Store manifest count does not match its entries",
            )
        manifest_core = {
            key: manifest[key]
            for key in (
                "format_ref",
                "store_id",
                "disposable",
                "result_id",
                "result_digest",
                "view_digest",
                "allowlist_digest",
                "observation_count",
                "entries",
            )
        }
        expected_manifest_digest = digest_of(
            ["CITATION_STORE_MANIFEST@1", manifest_core]
        )
        manifest_digest = _digest(
            manifest["manifest_digest"], "Citation Store manifest digest"
        )
        if manifest_digest != expected_manifest_digest:
            _inconsistent(
                "CITATION_STORE_MANIFEST_DIGEST_MISMATCH",
                "Citation Store manifest digest is not canonical",
            )
        store_binding_digest = digest_of(
            [
                "CITATION_STORE_BINDING@1",
                {
                    "result_id": manifest["result_id"],
                    "result_digest": manifest["result_digest"],
                    "allowlist_digest": manifest["allowlist_digest"],
                    "entries": entries,
                },
            ]
        )
        expected_store_id = StableId(
            "citation_store_"
            + store_binding_digest.value.removeprefix("sha256:")[-32:]
        )
        store_id = _stable_id(manifest["store_id"], "Citation Store ID")
        if store_id != expected_store_id:
            _inconsistent(
                "CITATION_STORE_ID_MISMATCH",
                "Citation Store ID is not canonical",
            )
        if (
            manifest["result_id"] != result.result_id.value
            or manifest["result_digest"] != result.digest.value
            or manifest["view_digest"] != result.view_digest.value
            or manifest["allowlist_digest"] != result.allowlist_digest.value
        ):
            _inconsistent(
                "CITATION_STORE_RESULT_MISMATCH",
                "Citation Store belongs to another sealed Structure View Result",
            )
        expected_ids = tuple(
            entry.evidence_id.value for entry in result.evidence_allowlist
        )
        if entry_ids != expected_ids:
            _inconsistent(
                "CITATION_STORE_ALLOWLIST_MISMATCH",
                "Citation Store manifest is not the Result's exact Evidence allowlist",
            )
        expected_file_names = {f"{evidence_id}.json" for evidence_id in expected_ids}
        actual_file_names = {item.name for item in observations_directory.iterdir()}
        if actual_file_names != expected_file_names:
            _inconsistent(
                "CITATION_STORE_OBSERVATION_FILES_MISMATCH",
                "Citation Store observation files are missing or extra",
            )

        observations: list[CitationObservation] = []
        for expected_reference, entry in zip(result.evidence_allowlist, entries):
            expected_relative = (
                f"{_OBSERVATIONS_NAME}/{expected_reference.evidence_id.value}.json"
            )
            if entry["path"] != expected_relative:
                _invalid(
                    "CITATION_STORE_PATH_NONCANONICAL",
                    "Citation Store observation path is not canonical",
                )
            relative = _safe_relative_path(entry["path"])
            observation_path = self._root.joinpath(*relative.parts)
            encoded = _read_regular_file(
                observation_path, "Citation observation file"
            )
            if _raw_digest(encoded).value != entry["file_digest"]:
                _inconsistent(
                    "CITATION_STORE_FILE_DIGEST_MISMATCH",
                    "Citation observation file digest differs from the manifest",
                    evidence_id=expected_reference.evidence_id.value,
                )
            observation = _parse_observation(
                _decode_canonical_json(encoded, "Citation observation file")
            )
            if (
                observation.reference != expected_reference
                or observation.reference.evidence_id.value != entry["evidence_id"]
                or observation.reference.evidence_digest.value
                != entry["evidence_digest"]
                or observation.digest.value != entry["observation_digest"]
            ):
                _inconsistent(
                    "CITATION_STORE_OBSERVATION_BINDING_MISMATCH",
                    "Citation observation differs from Result or Store manifest",
                    evidence_id=expected_reference.evidence_id.value,
                )
            observations.append(observation)

        receipt = CitationStoreReceipt(
            store_id=store_id,
            result_id=result.result_id,
            result_digest=result.digest,
            allowlist_digest=result.allowlist_digest,
            manifest_digest=manifest_digest,
            observation_count=len(observations),
            disposable=True,
        )
        snapshot = CitationStoreSnapshot(receipt, tuple(observations))
        snapshot.require_exact(result)
        return snapshot


class FileCitationObservationStoreWriter:
    """Trusted broker capability that can create one new disposable Store."""

    def __init__(self, root: str | os.PathLike[str]) -> None:
        self._backend = _FileCitationObservationStoreBackend(root)

    @property
    def root(self) -> Path:
        return self._backend.root

    def create_disposable_store(
        self,
        *,
        result: StructureViewResultSeal,
        observations: tuple[CitationObservation, ...],
    ) -> CitationStoreReceipt:
        return self._backend.create_disposable_store(
            result=result,
            observations=observations,
        )


class FileCitationObservationStoreReader:
    """Projector capability: exact read only, with no Store creation method."""

    def __init__(self, root: str | os.PathLike[str]) -> None:
        self._backend = _FileCitationObservationStoreBackend(root)

    @property
    def root(self) -> Path:
        return self._backend.root

    def read_exact(
        self, result: StructureViewResultSeal
    ) -> CitationStoreSnapshot:
        return self._backend.read_exact(result)


def structure_view_result_seal_payload(
    result: StructureViewResultSeal,
) -> dict[str, object]:
    result.require_valid()
    return {
        "format_ref": _RESULT_FORMAT,
        "result_id": result.result_id.value,
        "result_kind": result.result_kind,
        "view_digest": result.view_digest.value,
        "evidence_allowlist": [
            _reference_payload(entry) for entry in result.evidence_allowlist
        ],
        "allowlist_digest": result.allowlist_digest.value,
        "result_digest": result.digest.value,
    }


def load_structure_view_result_seal(
    path: str | os.PathLike[str],
) -> StructureViewResultSeal:
    result_path = _canonical_absolute_path(path, "Structure View Result seal")
    value = _read_canonical_json(result_path, "Structure View Result seal")
    mapping = _mapping(value, "Structure View Result seal")
    _exact_keys(
        mapping,
        {
            "format_ref",
            "result_id",
            "result_kind",
            "view_digest",
            "evidence_allowlist",
            "allowlist_digest",
            "result_digest",
        },
        "Structure View Result seal",
    )
    if mapping["format_ref"] != _RESULT_FORMAT:
        _invalid(
            "CITATION_RESULT_FORMAT_INVALID",
            "Structure View Result citation seal format is unsupported",
        )
    allowlist_value = mapping["evidence_allowlist"]
    if not isinstance(allowlist_value, list):
        _invalid(
            "CITATION_ALLOWLIST_INVALID",
            "Citation Evidence allowlist must be a list",
        )
    result = StructureViewResultSeal(
        result_id=_stable_id(mapping["result_id"], "Structure View Result ID"),
        result_kind=_string(mapping["result_kind"], "Structure View Result kind"),
        view_digest=_digest(mapping["view_digest"], "Structure View digest"),
        evidence_allowlist=tuple(
            _parse_reference(item) for item in allowlist_value
        ),
        allowlist_digest=_digest(
            mapping["allowlist_digest"], "Citation allowlist digest"
        ),
        digest=_digest(mapping["result_digest"], "Structure View Result digest"),
    )
    result.require_valid()
    return result


def _observation_payload(observation: CitationObservation) -> dict[str, object]:
    return {
        "format_ref": _OBSERVATION_FORMAT,
        "reference": _reference_payload(observation.reference),
        "excerpt": observation.excerpt,
        "observation_digest": observation.digest.value,
    }


def _reference_payload(reference: CitationEvidenceReference) -> dict[str, object]:
    return {
        "evidence_id": reference.evidence_id.value,
        "artifact_id": reference.artifact_id.value,
        "source_context_id": reference.source_context_id.value,
        "byte_start": reference.byte_start,
        "byte_end": reference.byte_end,
        "locator": reference.locator,
        "excerpt_digest": reference.excerpt_digest.value,
        "artifact_content_digest": reference.artifact_content_digest.value,
        "evidence_digest": reference.evidence_digest.value,
    }


def _parse_observation(value: object) -> CitationObservation:
    mapping = _mapping(value, "Citation observation")
    _exact_keys(
        mapping,
        {"format_ref", "reference", "excerpt", "observation_digest"},
        "Citation observation",
    )
    if mapping["format_ref"] != _OBSERVATION_FORMAT:
        _invalid(
            "CITATION_OBSERVATION_FORMAT_INVALID",
            "Citation observation format is unsupported",
        )
    observation = CitationObservation(
        reference=_parse_reference(mapping["reference"]),
        excerpt=_string(mapping["excerpt"], "Citation observation excerpt", allow_empty=True),
        digest=_digest(mapping["observation_digest"], "Citation observation digest"),
    )
    observation.require_valid()
    return observation


def _parse_reference(value: object) -> CitationEvidenceReference:
    mapping = _mapping(value, "Citation Evidence reference")
    _exact_keys(
        mapping,
        {
            "evidence_id",
            "artifact_id",
            "source_context_id",
            "byte_start",
            "byte_end",
            "locator",
            "excerpt_digest",
            "artifact_content_digest",
            "evidence_digest",
        },
        "Citation Evidence reference",
    )
    reference = CitationEvidenceReference(
        evidence_id=_stable_id(mapping["evidence_id"], "Citation Evidence ID"),
        artifact_id=_stable_id(mapping["artifact_id"], "Citation Artifact ID"),
        source_context_id=_stable_id(
            mapping["source_context_id"], "Citation Source Context ID"
        ),
        byte_start=_integer(mapping["byte_start"], "Citation byte_start"),
        byte_end=_integer(mapping["byte_end"], "Citation byte_end"),
        locator=_string(mapping["locator"], "Citation locator"),
        excerpt_digest=_digest(mapping["excerpt_digest"], "Citation excerpt digest"),
        artifact_content_digest=_digest(
            mapping["artifact_content_digest"], "Citation Artifact content digest"
        ),
        evidence_digest=_digest(mapping["evidence_digest"], "Citation Evidence digest"),
    )
    reference.require_valid()
    return reference


def _parse_manifest_entry(value: object, index: int) -> dict[str, str]:
    mapping = _mapping(value, f"Citation Store entry {index}")
    keys = {
        "evidence_id",
        "evidence_digest",
        "observation_digest",
        "path",
        "file_digest",
    }
    _exact_keys(mapping, keys, f"Citation Store entry {index}")
    parsed = {key: _string(mapping[key], f"Citation Store entry {key}") for key in keys}
    _stable_id(parsed["evidence_id"], "Citation Store Evidence ID")
    _digest(parsed["evidence_digest"], "Citation Store Evidence digest")
    _digest(parsed["observation_digest"], "Citation Store observation digest")
    _digest(parsed["file_digest"], "Citation Store file digest")
    _safe_relative_path(parsed["path"])
    return parsed


def _canonical_absolute_path(
    value: str | os.PathLike[str], label: str
) -> Path:
    path = Path(value)
    if (
        not path.is_absolute()
        or any(part in {".", ".."} for part in path.parts)
        or os.path.normpath(os.fspath(path)) != os.fspath(path)
    ):
        _invalid(
            "CITATION_PATH_NONCANONICAL",
            f"{label} must be an absolute canonical path without traversal",
        )
    return path


def _safe_relative_path(value: object) -> PurePosixPath:
    text = _string(value, "Citation Store relative path")
    path = PurePosixPath(text)
    if (
        path.is_absolute()
        or len(path.parts) != 2
        or path.parts[0] != _OBSERVATIONS_NAME
        or any(part in {"", ".", ".."} for part in path.parts)
        or str(path) != text
    ):
        _invalid(
            "CITATION_STORE_PATH_TRAVERSAL",
            "Citation Store observation path is outside the fixed observations directory",
        )
    return path


def _require_existing_directory(path: Path, label: str) -> None:
    try:
        info = path.lstat()
    except FileNotFoundError as exc:
        raise _invalid_error(
            "CITATION_DIRECTORY_MISSING", f"{label} does not exist"
        ) from exc
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        _invalid(
            "CITATION_DIRECTORY_UNSAFE",
            f"{label} must be a real directory, not a symlink",
        )
    resolved = path.resolve(strict=True)
    if resolved != path:
        _invalid(
            "CITATION_PATH_SYMLINK_COMPONENT",
            f"{label} contains a symlink component",
        )


def _write_new_regular_file(path: Path, payload: bytes) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(path, flags, 0o600)
    try:
        view = memoryview(payload)
        while view:
            written = os.write(fd, view)
            view = view[written:]
        os.fsync(fd)
    finally:
        os.close(fd)


def _read_regular_file(path: Path, label: str) -> bytes:
    if not path.is_absolute():
        _invalid(
            "CITATION_PATH_NONCANONICAL", f"{label} path must be absolute"
        )
    _require_existing_directory(path.parent, f"{label} parent")
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        fd = os.open(path, flags)
    except (FileNotFoundError, OSError) as exc:
        raise _invalid_error(
            "CITATION_FILE_UNAVAILABLE",
            f"{label} is missing, inaccessible, or a symlink",
        ) from exc
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            _invalid(
                "CITATION_FILE_NOT_REGULAR",
                f"{label} must be a regular file",
            )
        chunks: list[bytes] = []
        while True:
            chunk = os.read(fd, 65_536)
            if not chunk:
                break
            chunks.append(chunk)
        return b"".join(chunks)
    finally:
        os.close(fd)


def _read_canonical_json(path: Path, label: str) -> object:
    return _decode_canonical_json(_read_regular_file(path, label), label)


def _decode_canonical_json(payload: bytes, label: str) -> object:
    try:
        text = payload.decode("utf-8")
        value = json.loads(text, object_pairs_hook=_unique_object)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise _invalid_error(
            "CITATION_JSON_INVALID", f"{label} is not strict JSON"
        ) from exc
    if canonical_json_bytes(value) != payload:
        _invalid(
            "CITATION_JSON_NONCANONICAL",
            f"{label} is not canonical JSON",
        )
    return value


def _unique_object(pairs: Sequence[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _exact_keys(value: Mapping[str, object], expected: set[str], label: str) -> None:
    actual = set(value)
    if actual != expected:
        _invalid(
            "CITATION_JSON_FIELDS_INVALID",
            f"{label} contains missing or unknown fields",
        )


def _mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        _invalid("CITATION_JSON_OBJECT_REQUIRED", f"{label} must be an object")
    return value


def _string(value: object, label: str, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str) or (not allow_empty and not value):
        _invalid("CITATION_JSON_STRING_REQUIRED", f"{label} must be a string")
    if not allow_empty and value != value.strip():
        _invalid("CITATION_JSON_STRING_NONCANONICAL", f"{label} is not canonical")
    return value


def _integer(value: object, label: str) -> int:
    if type(value) is not int:
        _invalid("CITATION_JSON_INTEGER_REQUIRED", f"{label} must be an integer")
    return value


def _stable_id(value: object, label: str) -> StableId:
    text = _string(value, label)
    try:
        return StableId(text)
    except ValueError as exc:
        raise _invalid_error("CITATION_STABLE_ID_INVALID", f"{label} is invalid") from exc


def _digest(value: object, label: str) -> Digest:
    text = _string(value, label)
    try:
        return Digest(text)
    except ValueError as exc:
        raise _invalid_error("CITATION_DIGEST_INVALID", f"{label} is invalid") from exc


def _raw_digest(payload: bytes) -> Digest:
    return Digest("sha256:" + hashlib.sha256(payload).hexdigest())


def _lexists(path: Path) -> bool:
    return os.path.lexists(os.fspath(path))


def _invalid(reason_code: str, message: str) -> None:
    raise _invalid_error(reason_code, message)


def _invalid_error(reason_code: str, message: str) -> DomainError:
    return DomainError(
        ErrorCode.INVALID_ARGUMENT,
        message,
        {"reason_code": reason_code},
    )


def _inconsistent(reason_code: str, message: str, **details: str) -> None:
    raise DomainError(
        ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
        message,
        {"reason_code": reason_code, **details},
    )


__all__ = [
    "FileCitationObservationStoreReader",
    "FileCitationObservationStoreWriter",
    "load_structure_view_result_seal",
    "structure_view_result_seal_payload",
]
