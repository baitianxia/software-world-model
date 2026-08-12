"""Database- and Source-free CLI for sealed Read Set Catalogs and Views."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Sequence, TextIO

from software_world_model.application_services.read_set_catalog import (
    ReadSetFileRole,
)
from software_world_model.cross_cutting import (
    DomainError,
    ErrorCode,
    StableId,
    canonical_json_bytes,
)
from software_world_model.infrastructure.file_read_set_catalog import (
    FileReadSetCatalogStore,
    RootedStructureReadBundleStore,
)

from .structure_view_cli import main as structure_view_main


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="swm-read-set-catalog",
        description=(
            "Verify and query a sealed SWM-READ-SET-CATALOG@1 using only "
            "Catalog and no-payload Bundle roots"
        ),
    )
    parser.add_argument("--catalog-root", required=True)
    parser.add_argument("--bundle-root", required=True)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("verify-current")
    commands.add_parser("list-read-sets")
    show = commands.add_parser("show-read-set")
    show.add_argument("--read-set-id", required=True)
    view = commands.add_parser(
        "view",
        help="verify a Catalog Read Set, then execute a Structure View command",
    )
    view.add_argument("--read-set-id", required=True)
    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> int:
    output = stdout or sys.stdout
    error_output = stderr or sys.stderr
    arguments, remaining = build_parser().parse_known_args(argv)
    try:
        if remaining and arguments.command != "view":
            raise _invalid(
                "READ_SET_CATALOG_ARGUMENT_INVALID",
                f"unexpected arguments: {' '.join(remaining)}",
            )
        bundle_files = RootedStructureReadBundleStore(arguments.bundle_root)
        store = FileReadSetCatalogStore(arguments.catalog_root, bundle_files)
        pointer = store.read_pointer()
        if pointer is None:
            raise _invalid(
                "READ_SET_CATALOG_POINTER_NOT_FOUND",
                "Read Set Catalog current pointer was not found",
            )
        catalog = store.read_catalog(pointer, verify_files=True)
        if arguments.command == "verify-current":
            payload = {
                "status": "VERIFIED",
                "source_off": True,
                "pointer": pointer.document(),
                "catalog": _plain(catalog.document()),
            }
        elif arguments.command == "list-read-sets":
            payload = {
                "status": "VERIFIED",
                "source_off": True,
                "catalog_id": catalog.catalog_id.value,
                "catalog_revision": catalog.revision.value,
                "catalog_digest": catalog.document_digest.value,
                "read_sets": [
                    {
                        "read_set_id": entry.read_set_id.value,
                        "workspace_id": entry.workspace_id.value,
                        "workspace_version_ids": [
                            item.value for item in entry.workspace_version_ids
                        ],
                        "snapshot_ids": [
                            item.snapshot_id.value
                            for item in entry.snapshot_bindings
                        ],
                        "source_revisions": [
                            item.source_revision for item in entry.snapshot_bindings
                        ],
                        "bundle_locator": entry.bundle_locator,
                        "file_manifest_digest": entry.file_manifest_digest.value,
                        "registration_digest": entry.digest.value,
                        "availability": entry.availability.value,
                    }
                    for entry in catalog.entries
                ],
            }
        else:
            requested = StableId(arguments.read_set_id)
            entry = next(
                (item for item in catalog.entries if item.read_set_id == requested),
                None,
            )
            if entry is None:
                raise _invalid(
                    "READ_SET_CATALOG_ENTRY_NOT_FOUND",
                    "Read Set is not present in the current verified Catalog",
                )
            if arguments.command == "show-read-set":
                payload = {
                    "status": "VERIFIED",
                    "source_off": True,
                    "catalog_digest": catalog.document_digest.value,
                    "read_set": _plain(entry.catalog_entry()),
                }
            else:
                view_arguments = list(remaining)
                if view_arguments[:1] == ["--"]:
                    view_arguments = view_arguments[1:]
                if not view_arguments:
                    raise _invalid(
                        "READ_SET_VIEW_COMMAND_REQUIRED",
                        "view requires a Structure View subcommand and arguments",
                    )
                ordered = next(
                    item
                    for item in entry.file_manifest
                    if item.role is ReadSetFileRole.ORDERED_ENVELOPE
                )
                snapshots = sorted(
                    (
                        item
                        for item in entry.file_manifest
                        if item.role is ReadSetFileRole.SNAPSHOT
                    ),
                    key=lambda item: item.ordinal,
                )
                delegated = ["--ordered-envelope", ordered.locator]
                for snapshot in snapshots:
                    delegated.extend(["--snapshot-bundle", snapshot.locator])
                delegated.extend(view_arguments)
                return structure_view_main(
                    delegated,
                    stdout=output,
                    stderr=error_output,
                    file_store=bundle_files,
                )
        output.write(canonical_json_bytes(payload).decode("utf-8"))
        output.write("\n")
        return 0
    except (DomainError, ValueError, OSError, StopIteration) as error:
        payload = _error_payload(error)
        error_output.write(canonical_json_bytes(payload).decode("utf-8"))
        error_output.write("\n")
        return 2


def _plain(value: object) -> dict[str, object]:
    loaded = json.loads(canonical_json_bytes(value).decode("utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError("Catalog projection must be an object")
    return loaded


def _error_payload(error: Exception) -> dict[str, object]:
    if isinstance(error, DomainError):
        return {
            "error": error.code.value,
            "message": error.message,
            "details": dict(error.details),
        }
    return {
        "error": ErrorCode.INVALID_ARGUMENT.value,
        "message": str(error) or type(error).__name__,
        "details": {"reason_code": "READ_SET_CATALOG_INPUT_INVALID"},
    }


def _invalid(reason_code: str, message: str) -> DomainError:
    return DomainError(
        ErrorCode.INVALID_ARGUMENT,
        message,
        {"reason_code": reason_code},
    )


if __name__ == "__main__":  # pragma: no cover - subprocess entry point
    raise SystemExit(main())


__all__ = ["build_parser", "main"]
