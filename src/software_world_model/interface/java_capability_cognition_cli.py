"""Build one pre-question Java capability-cognition artifact."""

from __future__ import annotations

import argparse
import json
from pathlib import Path, PurePosixPath
from typing import Sequence

from software_world_model.application_services.java_capability_cognition import (
    ExactJavaCognitionSource,
    JavaCognitionModuleSource,
    build_java_capability_cognition,
)
from software_world_model.cross_cutting import DomainError, ErrorCode
from software_world_model.infrastructure.file_capability_cognition import (
    write_new_capability_cognition,
)
from software_world_model.source_integration.operations import LocalGitConnector


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build exact-revision Java cognition before an Agent question"
    )
    parser.add_argument("--repository", required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--source-tree", required=True)
    parser.add_argument("--project-name", required=True)
    parser.add_argument("--source-root", action="append", required=True)
    parser.add_argument("--output", required=True)
    return parser


def run(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repository = Path(args.repository)
    output = Path(args.output)
    if not repository.is_absolute() or not output.is_absolute():
        raise DomainError(ErrorCode.INVALID_ARGUMENT, "repository and output must be absolute paths")
    roots = tuple(sorted(set(args.source_root)))
    connector = LocalGitConnector(str(repository))
    revision = connector.resolve_revision(args.revision)
    source_tree = connector.resolve_tree(revision)
    if source_tree != args.source_tree:
        raise DomainError(ErrorCode.SOURCE_REVISION_INCONSISTENT, "requested Source tree does not match revision")
    entries = connector.list_tree_entries(revision)
    entry_paths = {item.path for item in entries if item.object_type == "blob" and not item.is_symlink}
    java_paths = tuple(
        sorted(
            path
            for path in entry_paths
            if path.endswith(".java") and any(_under(path, root) for root in roots)
        )
    )
    if not java_paths:
        raise DomainError(ErrorCode.SOURCE_TARGET_NOT_FOUND, "selected roots contain no Java files")
    module_roots = tuple(sorted({_module_root(root) for root in roots}))
    modules: list[JavaCognitionModuleSource] = []
    for module_root in module_roots:
        descriptor = f"{module_root}/pom.xml"
        if descriptor not in entry_paths:
            raise DomainError(ErrorCode.SOURCE_TARGET_NOT_FOUND, f"module descriptor is absent: {descriptor}")
        modules.append(
            JavaCognitionModuleSource(
                module_root=module_root,
                module_name=PurePosixPath(module_root).name,
                descriptor_path=descriptor,
                descriptor_bytes=connector.read_path(revision, descriptor),
            )
        )
    snapshot = build_java_capability_cognition(
        ExactJavaCognitionSource(
            project_name=args.project_name,
            source_revision=revision,
            source_tree=source_tree,
            selected_roots=roots,
            modules=tuple(modules),
            source_files={path: connector.read_path(revision, path) for path in java_paths},
        )
    )
    write_new_capability_cognition(output, snapshot)
    print(
        json.dumps(
            {
                "schema": "JAVA-CAPABILITY-COGNITION-BUILD-RECEIPT@1",
                "snapshot_id": snapshot.snapshot_id.value,
                "snapshot_digest": snapshot.digest.value,
                "source_revision": snapshot.source_revision,
                "source_tree": snapshot.source_tree,
                "selected_roots": list(snapshot.selected_roots),
                "entity_count": len(snapshot.entities),
                "relation_count": len(snapshot.relations),
                "behavior_count": len(snapshot.behaviors),
                "parsed_file_count": snapshot.parsed_file_count,
                "partial_file_count": snapshot.partial_file_count,
                "conflict_count": len(snapshot.conflicts),
                "unknown_count": len(snapshot.unknowns),
                "output": str(output),
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    return 0


def _module_root(source_root: str) -> str:
    parts = PurePosixPath(source_root).parts
    try:
        source_index = parts.index("src")
    except ValueError as exc:
        raise DomainError(ErrorCode.INVALID_ARGUMENT, "Java source root must use a Maven src layout") from exc
    if source_index < 1 or parts[source_index : source_index + 3] != ("src", "main", "java"):
        raise DomainError(ErrorCode.INVALID_ARGUMENT, "Java source root must end at src/main/java")
    if source_index + 3 != len(parts):
        raise DomainError(ErrorCode.INVALID_ARGUMENT, "Java source root must end at src/main/java")
    return "/".join(parts[:source_index])


def _under(path: str, root: str) -> bool:
    path_parts = PurePosixPath(path).parts
    root_parts = PurePosixPath(root).parts
    return path_parts[: len(root_parts)] == root_parts


if __name__ == "__main__":
    raise SystemExit(run())
