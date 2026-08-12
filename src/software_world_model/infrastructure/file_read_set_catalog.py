"""Root-confined Bundle files and immutable sealed Read Set catalogs."""

from __future__ import annotations

import fcntl
import json
import os
from pathlib import Path
import stat
import tempfile
from typing import Mapping

from software_world_model.application_services.read_set_catalog import (
    ReadSetCatalog,
    ReadSetCatalogPointer,
    ReadSetCatalogStore,
    ReadSetFileRole,
    ReadSetRegistration,
    read_set_catalog_from_document,
    read_set_catalog_pointer_from_document,
)
from software_world_model.application_services.structure_read_bundle import (
    StoredStructureReadBundle,
    StructureOrderedReadBundle,
    StructureSnapshotReadBundle,
)
from software_world_model.cross_cutting import (
    CanonicalizationError,
    Digest,
    DomainError,
    ErrorCode,
    canonical_json_bytes,
)
from software_world_model.infrastructure.file_structure_read_bundle import (
    FileStructureReadBundleStore,
)


_MAX_CATALOG_BYTES = 16 * 1024 * 1024


class RootedStructureReadBundleStore:
    """Keep authority locators relative while confining I/O below one root."""

    def __init__(
        self,
        root: str | Path,
        *,
        delegate: FileStructureReadBundleStore | None = None,
    ) -> None:
        self.root = _absolute_root(root, "Bundle root")
        self._delegate = delegate or FileStructureReadBundleStore()

    def write_snapshot(
        self, locator: str, bundle: StructureSnapshotReadBundle
    ) -> StoredStructureReadBundle:
        destination = self._resolve(locator, create_parent=True)
        stored = self._delegate.write_snapshot(str(destination), bundle)
        self._verify_destination(destination)
        return StoredStructureReadBundle(
            locator=_relative_locator(locator),
            format_ref=stored.format_ref,
            bundle_digest=stored.bundle_digest,
            file_digest=stored.file_digest,
        )

    def read_snapshot(
        self, locator: str
    ) -> tuple[StructureSnapshotReadBundle, Digest]:
        source = self._resolve(locator, create_parent=False)
        self._verify_destination(source)
        return self._delegate.read_snapshot(str(source))

    def write_ordered(
        self, locator: str, bundle: StructureOrderedReadBundle
    ) -> StoredStructureReadBundle:
        destination = self._resolve(locator, create_parent=True)
        stored = self._delegate.write_ordered(str(destination), bundle)
        self._verify_destination(destination)
        return StoredStructureReadBundle(
            locator=_relative_locator(locator),
            format_ref=stored.format_ref,
            bundle_digest=stored.bundle_digest,
            file_digest=stored.file_digest,
        )

    def read_ordered(
        self, locator: str
    ) -> tuple[StructureOrderedReadBundle, Digest]:
        source = self._resolve(locator, create_parent=False)
        self._verify_destination(source)
        return self._delegate.read_ordered(str(source))

    def read_any(
        self, locator: str
    ) -> tuple[StructureSnapshotReadBundle | StructureOrderedReadBundle, Digest]:
        source = self._resolve(locator, create_parent=False)
        self._verify_destination(source)
        return self._delegate.read_any(str(source))

    def directory_entries(self, locator: str) -> tuple[str, ...]:
        directory = self._resolve(locator, create_parent=False, expect_directory=True)
        names: list[str] = []
        with os.scandir(directory) as entries:
            for entry in entries:
                if entry.is_symlink() or not entry.is_file(follow_symlinks=False):
                    raise _invalid(
                        "READ_SET_BUNDLE_DIRECTORY_INVALID",
                        "Read Set Bundle directory contains a symlink or non-file entry",
                    )
                names.append(entry.name)
        return tuple(sorted(names))

    def _resolve(
        self,
        locator: str,
        *,
        create_parent: bool,
        expect_directory: bool = False,
    ) -> Path:
        normalized = _relative_locator(locator)
        _ensure_root(self.root, create=create_parent)
        destination = self.root.joinpath(*normalized.split("/"))
        parent = destination if expect_directory else destination.parent
        if create_parent:
            _mkdir_without_symlinks(self.root, parent)
        _require_path_chain(self.root, parent, final_directory=True)
        if expect_directory:
            _require_path_chain(self.root, destination, final_directory=True)
        return destination

    @staticmethod
    def _verify_destination(path: Path) -> None:
        try:
            mode = path.lstat().st_mode
        except FileNotFoundError:
            raise
        if stat.S_ISLNK(mode) or not stat.S_ISREG(mode):
            raise _invalid(
                "READ_SET_BUNDLE_FILE_INVALID",
                "Read Set Bundle path is not a regular non-symlink file",
            )


class FileReadSetCatalogStore(ReadSetCatalogStore):
    """Publish immutable canonical manifests, then CAS one current pointer."""

    def __init__(
        self,
        catalog_root: str | Path,
        bundle_files: RootedStructureReadBundleStore,
        *,
        maximum_bytes: int = _MAX_CATALOG_BYTES,
    ) -> None:
        if type(maximum_bytes) is not int or maximum_bytes < 1024:
            raise ValueError("maximum Catalog size must be at least 1024 bytes")
        self.root = _absolute_root(catalog_root, "Catalog root")
        self._bundle_files = bundle_files
        self._maximum_bytes = maximum_bytes

    def read_pointer(self) -> ReadSetCatalogPointer | None:
        path = self.root / "current.json"
        if not path.exists() and not path.is_symlink():
            return None
        value = self._read_document(path)
        pointer = read_set_catalog_pointer_from_document(value)
        if canonical_json_bytes(pointer.document()) != _read_regular(path, self._maximum_bytes):
            raise _invalid(
                "READ_SET_CATALOG_POINTER_NONCANONICAL",
                "Catalog pointer is not canonical",
            )
        return pointer

    def read_catalog(
        self, pointer: ReadSetCatalogPointer, *, verify_files: bool
    ) -> ReadSetCatalog:
        pointer.require_valid()
        path = self._manifest_path(pointer)
        document = self._read_document(path)
        catalog = read_set_catalog_from_document(document)
        if (
            catalog.catalog_id != pointer.catalog_id
            or catalog.revision != pointer.revision
            or catalog.document_digest != pointer.catalog_digest
        ):
            raise _inconsistent("Catalog manifest differs from its exact current pointer")
        if canonical_json_bytes(catalog.document()) != _read_regular(path, self._maximum_bytes):
            raise _invalid(
                "READ_SET_CATALOG_NONCANONICAL",
                "Catalog manifest is not canonical",
            )
        if verify_files:
            for entry in catalog.entries:
                self._verify_entry_files(entry)
        return catalog

    def publish(
        self,
        catalog: ReadSetCatalog,
        *,
        expected: ReadSetCatalogPointer | None,
    ) -> ReadSetCatalogPointer:
        catalog.require_valid()
        _ensure_root(self.root, create=True)
        lock_path = self.root / ".catalog.lock"
        lock_descriptor = os.open(
            lock_path,
            os.O_CREAT | os.O_RDWR | getattr(os, "O_NOFOLLOW", 0),
            0o600,
        )
        try:
            with os.fdopen(lock_descriptor, "r+b", closefd=True) as lock:
                fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
                actual = self.read_pointer()
                if actual != expected:
                    raise DomainError(
                        ErrorCode.REVISION_CONFLICT,
                        "Read Set Catalog current pointer changed before publication",
                        {"reason_code": "READ_SET_CATALOG_CAS_CONFLICT"},
                    )
                pointer = ReadSetCatalogPointer.from_catalog(catalog)
                manifest = self._manifest_path(pointer)
                _mkdir_without_symlinks(self.root, manifest.parent)
                _write_immutable(manifest, canonical_json_bytes(catalog.document()))
                # Re-read before pointer movement; a file-store bug cannot publish corrupt bytes.
                loaded = self.read_catalog(pointer, verify_files=True)
                if loaded.document() != catalog.document():
                    raise _inconsistent("written Catalog does not re-read as the exact document")
                _replace_file(self.root / "current.json", canonical_json_bytes(pointer.document()))
                _fsync_directory(self.root)
                return pointer
        except BaseException:
            # fdopen owns the descriptor after successful construction.
            raise

    def _manifest_path(self, pointer: ReadSetCatalogPointer) -> Path:
        digest_hex = pointer.catalog_digest.value.split(":", 1)[1]
        directory = self.root / "manifests" / pointer.catalog_id.value
        return directory / f"{pointer.revision.value:020d}-{digest_hex}.json"

    def _read_document(self, path: Path) -> Mapping[str, object]:
        _ensure_root(self.root, create=False)
        _require_path_chain(self.root, path.parent, final_directory=True)
        payload = _read_regular(path, self._maximum_bytes)
        try:
            value = json.loads(
                payload.decode("utf-8", errors="strict"),
                object_pairs_hook=_strict_object,
            )
        except (UnicodeDecodeError, json.JSONDecodeError, _DuplicateKeyError) as error:
            raise _invalid(
                "READ_SET_CATALOG_JSON_INVALID",
                "Catalog file must be strict duplicate-free UTF-8 JSON",
            ) from error
        if not isinstance(value, dict):
            raise _invalid(
                "READ_SET_CATALOG_DOCUMENT_INVALID",
                "Catalog file top-level value must be an object",
            )
        try:
            canonical = canonical_json_bytes(value)
        except CanonicalizationError as error:
            raise _invalid(
                "READ_SET_CATALOG_NONCANONICAL",
                "Catalog file contains a non-canonical value",
            ) from error
        if canonical != payload:
            raise _invalid(
                "READ_SET_CATALOG_NONCANONICAL",
                "Catalog file bytes are not canonical",
            )
        return value

    def _verify_entry_files(self, entry: ReadSetRegistration) -> None:
        expected_names = tuple(
            sorted(item.locator.rsplit("/", 1)[1] for item in entry.file_manifest)
        )
        actual_names = self._bundle_files.directory_entries(entry.bundle_locator)
        if actual_names != expected_names:
            raise _invalid(
                "READ_SET_FILE_MANIFEST_INCOMPLETE",
                "Read Set Bundle directory has missing or extra files",
            )
        ordered: StructureOrderedReadBundle | None = None
        snapshots: list[tuple[StructureSnapshotReadBundle, Digest]] = []
        for item in entry.file_manifest:
            loaded, file_digest = self._bundle_files.read_any(item.locator)
            if (
                loaded.format_ref != item.format_ref
                or loaded.digest != item.bundle_digest
                or file_digest != item.file_digest
            ):
                raise _inconsistent("Catalog file manifest differs from loaded Bundle bytes")
            if item.role is ReadSetFileRole.ORDERED_ENVELOPE:
                if not isinstance(loaded, StructureOrderedReadBundle) or ordered is not None:
                    raise _invalid(
                        "READ_SET_ORDERED_ENVELOPE_INVALID",
                        "Read Set requires exactly one ordered Bundle envelope",
                    )
                ordered = loaded
            else:
                if not isinstance(loaded, StructureSnapshotReadBundle):
                    raise _invalid(
                        "READ_SET_SNAPSHOT_BUNDLE_INVALID",
                        "Read Set Snapshot file has the wrong Bundle kind",
                    )
                snapshots.append((loaded, file_digest))
        if ordered is None:
            raise _invalid(
                "READ_SET_ORDERED_ENVELOPE_REQUIRED",
                "Read Set ordered Bundle envelope is missing",
            )
        ordered.verify_snapshot_bundles(tuple(snapshots))
        if ordered.session.session_id != entry.session_id or ordered.session.read_set_digest != entry.read_set_digest:
            raise _inconsistent("Catalog Entry differs from loaded ordered Session")


class _DuplicateKeyError(ValueError):
    pass


def _strict_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateKeyError(key)
        result[key] = value
    return result


def _absolute_root(value: str | Path, label: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = Path.cwd() / path
    path = path.resolve(strict=False)
    if path == Path(path.anchor):
        raise ValueError(f"{label} cannot be a filesystem root")
    return path


def _relative_locator(value: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or "\\" in value
        or value.startswith("/")
        or value.endswith("/")
    ):
        raise _invalid(
            "READ_SET_LOCATOR_INVALID",
            "Read Set locator must be a normalized relative POSIX path",
        )
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise _invalid(
            "READ_SET_LOCATOR_INVALID",
            "Read Set locator must be a normalized relative POSIX path",
        )
    return value


def _ensure_root(root: Path, *, create: bool) -> None:
    if create:
        root.mkdir(parents=True, exist_ok=True)
    try:
        mode = root.lstat().st_mode
    except FileNotFoundError:
        raise
    if stat.S_ISLNK(mode) or not stat.S_ISDIR(mode):
        raise _invalid(
            "READ_SET_ROOT_INVALID",
            "Read Set root must be a non-symlink directory",
        )


def _mkdir_without_symlinks(root: Path, destination: Path) -> None:
    relative = destination.relative_to(root)
    current = root
    for part in relative.parts:
        current = current / part
        try:
            current.mkdir()
        except FileExistsError:
            pass
        mode = current.lstat().st_mode
        if stat.S_ISLNK(mode) or not stat.S_ISDIR(mode):
            raise _invalid(
                "READ_SET_DIRECTORY_INVALID",
                "Read Set directory path contains a symlink or non-directory",
            )


def _require_path_chain(
    root: Path,
    destination: Path,
    *,
    final_directory: bool,
) -> None:
    relative = destination.relative_to(root)
    current = root
    for index, part in enumerate(relative.parts):
        current = current / part
        mode = current.lstat().st_mode
        if stat.S_ISLNK(mode):
            raise _invalid(
                "READ_SET_SYMLINK_FORBIDDEN",
                "Read Set path cannot traverse a symbolic link",
            )
        if index < len(relative.parts) - 1 or final_directory:
            if not stat.S_ISDIR(mode):
                raise _invalid(
                    "READ_SET_DIRECTORY_INVALID",
                    "Read Set path component is not a directory",
                )


def _read_regular(path: Path, maximum_bytes: int) -> bytes:
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_size > maximum_bytes:
            raise _invalid(
                "READ_SET_FILE_INVALID",
                "Read Set file is not regular or exceeds the size limit",
            )
        chunks: list[bytes] = []
        remaining = maximum_bytes + 1
        while remaining > 0:
            chunk = os.read(descriptor, min(1024 * 1024, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        payload = b"".join(chunks)
        if len(payload) > maximum_bytes or os.read(descriptor, 1):
            raise _invalid("READ_SET_FILE_TOO_LARGE", "Read Set file exceeds the size limit")
        return payload
    finally:
        os.close(descriptor)


def _write_immutable(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() or path.is_symlink():
        if path.is_symlink() or _read_regular(path, len(payload)) != payload:
            raise _invalid(
                "READ_SET_CATALOG_MANIFEST_CONFLICT",
                "immutable Catalog manifest path contains different bytes",
            )
        return
    temporary: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as output:
            temporary = output.name
            os.fchmod(output.fileno(), 0o600)
            output.write(payload)
            output.flush()
            os.fsync(output.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError:
            if _read_regular(path, len(payload)) != payload:
                raise _invalid(
                    "READ_SET_CATALOG_MANIFEST_CONFLICT",
                    "concurrent Catalog writer published different bytes",
                )
        _fsync_directory(path.parent)
    finally:
        if temporary is not None:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass


def _replace_file(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as output:
            temporary = output.name
            os.fchmod(output.fileno(), 0o600)
            output.write(payload)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _invalid(reason_code: str, message: str) -> DomainError:
    return DomainError(ErrorCode.INVALID_ARGUMENT, message, {"reason_code": reason_code})


def _inconsistent(message: str) -> DomainError:
    return DomainError(ErrorCode.AUTHORITY_RECORD_INCONSISTENT, message)


__all__ = ["FileReadSetCatalogStore", "RootedStructureReadBundleStore"]
