"""File-only CLI for deterministic Structure View operations.

The CLI composes only the strict Bundle file loader and StructureViewService.
It has no database, ApplicationRuntime, Source, Evidence payload, model, or
network capability.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import stat
import sys
from typing import Sequence, TextIO

from software_world_model.application_services.structure_view import (
    EntityResolutionStatus,
    StructureEntityArgument,
    StructureViewResult,
    StructureViewService,
)
from software_world_model.application_services.citation_projection import (
    citation_seal_for_result,
)
from software_world_model.cross_cutting import (
    DomainError,
    ErrorCode,
    StableId,
    canonical_json_bytes,
)
from software_world_model.infrastructure.file_structure_read_bundle import (
    FileStructureReadBundleStore,
)
from software_world_model.infrastructure.file_citation_observation_store import (
    structure_view_result_seal_payload,
)
from software_world_model.knowledge_engine.structure import (
    EntityType,
    RelationPredicate,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="swm-structure-view",
        description="Query exact no-payload Structure Read Bundle files",
    )
    parser.add_argument("--ordered-envelope", required=True)
    parser.add_argument(
        "--snapshot-bundle",
        action="append",
        required=True,
        help="exact Snapshot Bundle path; repeat in caller-declared order",
    )
    parser.add_argument(
        "--result-path",
        help="write canonical JSON to a new explicit file instead of stdout",
    )
    parser.add_argument(
        "--citation-seal-path",
        help="also write a new no-payload Citation seal for this exact View Result",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    candidates = commands.add_parser("candidates")
    candidates.add_argument("--snapshot-id", required=True)
    candidates.add_argument("--mention", required=True)
    candidates.add_argument("--entity-type", choices=tuple(item.value for item in EntityType))
    candidates.add_argument("--exact-root-id")
    candidates.add_argument("--canonical-ga")
    candidates.add_argument("--canonical-gav")
    candidates.add_argument("--max-candidates", type=int, default=100)

    inventory = commands.add_parser("inventory")
    _add_entity_selector(inventory, "system")

    neighborhood = commands.add_parser("neighborhood")
    _add_entity_selector(neighborhood, "entity")
    neighborhood.add_argument(
        "--direction",
        choices=("OUTGOING", "INCOMING", "BOTH"),
        default="BOTH",
    )
    neighborhood.add_argument(
        "--predicate", choices=tuple(item.value for item in RelationPredicate)
    )

    path_exists = commands.add_parser("path-exists")
    _add_path_arguments(path_exists)

    all_paths = commands.add_parser("all-simple-paths")
    _add_path_arguments(all_paths)
    all_paths.add_argument("--max-paths", type=int, default=1000)

    diff = commands.add_parser("diff")
    diff.add_argument("--base-snapshot-id", required=True)
    diff.add_argument("--target-snapshot-id", required=True)
    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
    file_store: FileStructureReadBundleStore | None = None,
) -> int:
    output = stdout or sys.stdout
    error_output = stderr or sys.stderr
    arguments = build_parser().parse_args(argv)
    store = file_store or FileStructureReadBundleStore()
    try:
        ordered, _ordered_file_digest = store.read_ordered(
            arguments.ordered_envelope
        )
        loaded = tuple(
            store.read_snapshot(locator)
            for locator in arguments.snapshot_bundle
        )
        service = StructureViewService(ordered, loaded)
        result, limited = _execute(service, arguments)
        encoded = canonical_json_bytes(result.canonical_value())
        citation_seal = citation_seal_for_result(result)
        encoded_seal = canonical_json_bytes(
            structure_view_result_seal_payload(citation_seal)
        )
        if (
            arguments.result_path is not None
            and arguments.citation_seal_path is not None
            and Path(arguments.result_path) == Path(arguments.citation_seal_path)
        ):
            raise _invalid(
                "VIEW_CLI_OUTPUT_PATH_CONFLICT",
                "View Result and Citation seal require different output files",
            )
        if arguments.result_path is None:
            output.write(encoded.decode("utf-8"))
        else:
            _write_new_result(arguments.result_path, encoded)
        if arguments.citation_seal_path is not None:
            _write_new_result(arguments.citation_seal_path, encoded_seal)
        return 3 if limited else 0
    except (DomainError, ValueError, OSError) as error:
        payload = _error_payload(error)
        error_output.write(canonical_json_bytes(payload).decode("utf-8"))
        return 2


def _execute(
    service: StructureViewService,
    arguments: argparse.Namespace,
) -> tuple[StructureViewResult, bool]:
    if arguments.command == "candidates":
        result = service.entity_candidates(
            snapshot_id=_stable_id(arguments.snapshot_id, "Snapshot ID"),
            mention=arguments.mention,
            entity_type=arguments.entity_type,
            exact_root_id=(
                _stable_id(arguments.exact_root_id, "exact Entity Root ID")
                if arguments.exact_root_id is not None
                else None
            ),
            canonical_ga=arguments.canonical_ga,
            canonical_gav=arguments.canonical_gav,
            max_candidates=arguments.max_candidates,
        )
        return result, False
    if arguments.command == "inventory":
        system, limitation = _entity_argument(service, arguments, "system")
        if limitation is not None:
            return limitation, True
        assert system is not None
        return service.child_module_inventory(system=system), False
    if arguments.command == "neighborhood":
        entity, limitation = _entity_argument(service, arguments, "entity")
        if limitation is not None:
            return limitation, True
        assert entity is not None
        return (
            service.direct_neighborhood(
                entity=entity,
                direction=arguments.direction,
                predicate=arguments.predicate,
            ),
            False,
        )
    if arguments.command in {"path-exists", "all-simple-paths"}:
        source, source_limitation = _entity_argument(service, arguments, "source")
        if source_limitation is not None:
            return source_limitation, True
        target, target_limitation = _entity_argument(service, arguments, "target")
        if target_limitation is not None:
            return target_limitation, True
        assert source is not None and target is not None
        if arguments.command == "path-exists":
            return (
                service.path_exists(
                    source=source,
                    target=target,
                    predicate=arguments.predicate,
                    max_depth=arguments.max_depth,
                    max_expansions=arguments.max_expansions,
                ),
                False,
            )
        return (
            service.all_simple_paths(
                source=source,
                target=target,
                predicate=arguments.predicate,
                max_depth=arguments.max_depth,
                max_paths=arguments.max_paths,
                max_expansions=arguments.max_expansions,
            ),
            False,
        )
    if arguments.command == "diff":
        return (
            service.ordered_snapshot_diff(
                base_snapshot_id=_stable_id(
                    arguments.base_snapshot_id, "base Snapshot ID"
                ),
                target_snapshot_id=_stable_id(
                    arguments.target_snapshot_id, "target Snapshot ID"
                ),
            ),
            False,
        )
    raise AssertionError(f"unsupported parser command: {arguments.command}")


def _entity_argument(
    service: StructureViewService,
    arguments: argparse.Namespace,
    prefix: str,
) -> tuple[StructureEntityArgument | None, StructureViewResult | None]:
    root_text = getattr(arguments, f"{prefix}_root_id")
    state_text = getattr(arguments, f"{prefix}_state_id")
    mention = getattr(arguments, f"{prefix}_mention")
    exact = root_text is not None or state_text is not None
    requested_candidate = mention is not None
    if exact and requested_candidate:
        raise _invalid(
            "VIEW_CLI_ENTITY_SELECTOR_CONFLICT",
            f"{prefix} must use either an exact Root/State pair or same-call candidates",
        )
    if exact:
        if root_text is None or state_text is None:
            raise _invalid(
                "VIEW_CLI_EXACT_ENTITY_PAIR_REQUIRED",
                f"{prefix} exact selector requires both Root and State IDs",
            )
        snapshot_id = _stable_id(
            getattr(arguments, f"{prefix}_snapshot_id"),
            f"{prefix} Snapshot ID",
        )
        return (
            StructureEntityArgument.caller_exact_ref(
                service=service,
                snapshot_id=snapshot_id,
                entity_root_id=_stable_id(root_text, f"{prefix} Entity Root ID"),
                entity_state_id=_stable_id(state_text, f"{prefix} Entity State ID"),
            ),
            None,
        )
    if not requested_candidate:
        raise _invalid(
            "VIEW_CLI_ENTITY_SELECTOR_REQUIRED",
            f"{prefix} requires an exact Root/State pair or a mention",
        )
    candidate_result = service.entity_candidates(
        snapshot_id=_stable_id(
            getattr(arguments, f"{prefix}_snapshot_id"),
            f"{prefix} Snapshot ID",
        ),
        mention=mention,
        entity_type=getattr(arguments, f"{prefix}_entity_type"),
        canonical_ga=getattr(arguments, f"{prefix}_canonical_ga"),
        canonical_gav=getattr(arguments, f"{prefix}_canonical_gav"),
        max_candidates=getattr(arguments, f"{prefix}_max_candidates"),
    )
    if (
        candidate_result.payload["resolution_status"]
        != EntityResolutionStatus.UNIQUE.value
    ):
        return None, candidate_result
    return StructureEntityArgument.from_unique_candidate(candidate_result), None


def _add_entity_selector(parser: argparse.ArgumentParser, prefix: str) -> None:
    parser.add_argument(f"--{prefix}-snapshot-id", required=True)
    parser.add_argument(f"--{prefix}-root-id")
    parser.add_argument(f"--{prefix}-state-id")
    parser.add_argument(f"--{prefix}-mention")
    parser.add_argument(
        f"--{prefix}-entity-type",
        choices=tuple(item.value for item in EntityType),
    )
    parser.add_argument(f"--{prefix}-canonical-ga")
    parser.add_argument(f"--{prefix}-canonical-gav")
    parser.add_argument(f"--{prefix}-max-candidates", type=int, default=100)


def _add_path_arguments(parser: argparse.ArgumentParser) -> None:
    _add_entity_selector(parser, "source")
    _add_entity_selector(parser, "target")
    parser.add_argument(
        "--predicate",
        choices=tuple(item.value for item in RelationPredicate),
        default=RelationPredicate.DEPENDS_ON.value,
    )
    parser.add_argument("--max-depth", type=int, default=64)
    parser.add_argument("--max-expansions", type=int, default=100_000)


def _write_new_result(value: str, payload: bytes) -> None:
    path = Path(value)
    if (
        not path.is_absolute()
        or any(part in {".", ".."} for part in path.parts)
        or os.path.normpath(os.fspath(path)) != os.fspath(path)
    ):
        raise _invalid(
            "VIEW_CLI_RESULT_PATH_NONCANONICAL",
            "result path must be absolute, canonical, and traversal-free",
        )
    try:
        parent_info = path.parent.lstat()
    except FileNotFoundError as exc:
        raise _invalid(
            "VIEW_CLI_RESULT_PARENT_MISSING",
            "result path parent does not exist",
        ) from exc
    if (
        stat.S_ISLNK(parent_info.st_mode)
        or not stat.S_ISDIR(parent_info.st_mode)
        or path.parent.resolve(strict=True) != path.parent
    ):
        raise _invalid(
            "VIEW_CLI_RESULT_PARENT_UNSAFE",
            "result path parent must be a real symlink-free directory",
        )
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags, 0o600)
    except OSError as exc:
        raise _invalid(
            "VIEW_CLI_RESULT_PATH_UNAVAILABLE",
            "result path already exists, is a symlink, or is unavailable",
        ) from exc
    try:
        view = memoryview(payload)
        while view:
            count = os.write(descriptor, view)
            view = view[count:]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _stable_id(value: object, label: str) -> StableId:
    if not isinstance(value, str):
        raise _invalid("VIEW_CLI_ID_REQUIRED", f"{label} is required")
    try:
        return StableId(value)
    except ValueError as exc:
        raise _invalid("VIEW_CLI_ID_INVALID", f"{label} is invalid") from exc


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
        "details": {"reason_code": "VIEW_CLI_INPUT_INVALID"},
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
