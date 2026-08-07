from __future__ import annotations

from fnmatch import fnmatchcase
from pathlib import Path, PurePosixPath
import subprocess
from typing import Protocol

from swm_demo.artifact_contract import (
    ArtifactRequest,
    RevisionComparison,
    SourceArtifact,
    SourceCollection,
    SourceObjectRef,
)
from swm_demo.ids import content_hash, stable_id
from swm_demo.java_artifact_processor import JavaArtifactProcessor


class SourceAccessError(RuntimeError):
    pass


class ArtifactRepository(Protocol):
    def bind_source(
        self,
        scope_id: str,
        source_type: str,
        source_path: Path,
        expected_revision: str | None,
    ) -> None: ...

    def get_binding(self, scope_id: str) -> dict[str, str | None]: ...

    def save_source_artifacts(
        self, snapshot_id: str, collection: SourceCollection
    ) -> None: ...


class SourceIntegration:
    """Source Integration facade used by Application Services."""

    def __init__(
        self,
        repository: ArtifactRepository,
        providers: tuple["ConnectorProvider", ...] | None = None,
    ):
        self.repository = repository
        configured = providers or (LocalGitConnectorProvider(),)
        self.providers = {provider.source_type: provider for provider in configured}

    def register_provider(self, provider: "ConnectorProvider") -> None:
        if provider.source_type in self.providers:
            raise ValueError(f"Connector Provider already exists: {provider.source_type}")
        self.providers[provider.source_type] = provider

    def bind_source(
        self,
        scope_id: str,
        source_type: str,
        source_path: Path,
        expected_revision: str | None,
    ) -> None:
        provider = self.providers.get(source_type)
        if provider is None:
            raise SourceAccessError(f"Connector Provider is not registered: {source_type}")
        provider.validate_configuration(source_path)
        self.repository.bind_source(
            scope_id=scope_id,
            source_type=source_type,
            source_path=source_path,
            expected_revision=expected_revision,
        )

    def bind_local_git(
        self,
        scope_id: str,
        source_path: Path,
        expected_revision: str | None,
    ) -> None:
        self.bind_source(
            scope_id=scope_id,
            source_type="local-git",
            source_path=source_path,
            expected_revision=expected_revision,
        )

    def collect_structure_sources(self, scope_id: str) -> SourceCollection:
        return self.collect_sources(
            scope_id,
            ArtifactRequest(
                build_profile="structure-core",
                include_globs=("README.md", "pom.xml", "*/pom.xml"),
            ),
        )

    def collect_sources(
        self, scope_id: str, request: ArtifactRequest
    ) -> SourceCollection:
        binding = self.repository.get_binding(scope_id)
        source_type = str(binding.get("source_type") or "local-git")
        provider = self.providers.get(source_type)
        if provider is None:
            raise SourceAccessError(f"Connector Provider is not registered: {source_type}")
        connector = provider.create_tool(Path(str(binding["source_path"])))
        return connector.collect_sources(
            scope_id=scope_id,
            request=request,
            expected_revision=(
                str(binding["expected_revision"])
                if binding["expected_revision"]
                else None
            ),
        )

    def record_artifacts(
        self, snapshot_id: str, collection: SourceCollection
    ) -> None:
        self.repository.save_source_artifacts(snapshot_id, collection)


class ConnectorTool(Protocol):
    def resolve_revision(
        self, scope_id: str, revision: str
    ) -> SourceObjectRef: ...

    def search_at_revision(
        self,
        scope_id: str,
        revision: str,
        query: str | None = None,
        include_globs: tuple[str, ...] = (),
    ) -> tuple[SourceObjectRef, ...]: ...

    def read_files_at_revision(
        self,
        scope_id: str,
        revision: str,
        paths: tuple[str | SourceObjectRef, ...],
    ) -> tuple[SourceArtifact, ...]: ...

    def read_commit(self, scope_id: str, revision: str) -> SourceArtifact: ...

    def compare_revisions(
        self,
        scope_id: str,
        comparison: RevisionComparison,
        include_globs: tuple[str, ...] = (),
    ) -> SourceArtifact: ...

    def collect_sources(
        self,
        scope_id: str,
        request: ArtifactRequest,
        expected_revision: str | None = None,
    ) -> SourceCollection: ...


class ConnectorProvider(Protocol):
    source_type: str

    def validate_configuration(self, source_path: Path) -> None: ...

    def capabilities(self) -> tuple[str, ...]: ...

    def create_tool(self, source_path: Path) -> ConnectorTool: ...


class LocalGitConnectorProvider:
    """Provider SPI: configuration, discovery and Tool creation."""

    source_type = "local-git"

    def validate_configuration(self, source_path: Path) -> None:
        resolved = source_path.resolve()
        if not resolved.is_dir() or not (resolved / ".git").is_dir():
            raise SourceAccessError(f"not a full local Git checkout: {resolved}")

    def capabilities(self) -> tuple[str, ...]:
        return (
            "collect-text",
            "resolve-revision",
            "search-at-revision",
            "read-files-at-revision",
            "read-commit",
            "compare-revisions",
            "derive-java-ast",
        )

    def create_tool(self, source_path: Path) -> ConnectorTool:
        return LocalGitConnector(source_path)


class LocalGitConnector:
    """Deterministic Connector Tool for the first validation slice.

    It emits information-bearing files as Source Artifacts. Git commands used for
    repository health and revision discovery are control results, not Artifacts.
    """

    def __init__(self, repository: Path):
        self.repository = repository.resolve()

    def collect_structure_sources(
        self,
        scope_id: str,
        expected_revision: str | None = None,
    ) -> SourceCollection:
        return self.collect_sources(
            scope_id=scope_id,
            request=ArtifactRequest(
                build_profile="structure-core",
                include_globs=("README.md", "pom.xml", "*/pom.xml"),
            ),
            expected_revision=expected_revision,
        )

    def collect_sources(
        self,
        scope_id: str,
        request: ArtifactRequest,
        expected_revision: str | None = None,
    ) -> SourceCollection:
        requested_revision = request.revision or expected_revision or "HEAD"
        revision = self.resolve_revision(scope_id, requested_revision).revision
        # ArtifactRequest is an explicit materialization request. An empty file
        # selector therefore means "no repository files", not "the whole tree";
        # commit and comparison artifacts below remain independently selectable.
        # ``search_at_revision`` keeps its broader discovery semantics when used
        # directly through the Connector Tool API.
        if request.include_globs:
            refs = tuple(
                item
                for item in self.search_at_revision(
                    scope_id,
                    revision,
                    include_globs=request.include_globs,
                )
                if "target" not in PurePosixPath(item.external_key).parts
            )
            artifacts = list(
                self.read_files_at_revision(scope_id, revision, refs)
            )
        else:
            artifacts = []

        if request.derive_java_ast:
            processor = JavaArtifactProcessor()
            derived: list[SourceArtifact] = []
            for artifact in artifacts:
                if artifact.artifact_type == "java-source":
                    try:
                        derived.append(processor.derive(artifact))
                    except ValueError as error:
                        raise SourceAccessError(str(error)) from error
            artifacts.extend(derived)

        legacy_commit_ids = {
            self.resolve_revision(scope_id, item).revision
            for item in request.git_commit_ids
        }
        commit_ids = {
            self.resolve_revision(scope_id, item).revision
            for item in request.commit_revisions
        }
        for commit_id in sorted(commit_ids - legacy_commit_ids):
            artifacts.append(self.read_commit(scope_id, commit_id))
        for commit_id in sorted(legacy_commit_ids):
            artifacts.append(self._read_legacy_commit(scope_id, commit_id))

        for comparison in request.comparisons:
            artifacts.append(
                self.compare_revisions(
                    scope_id,
                    comparison,
                    include_globs=request.include_globs,
                )
            )

        artifacts_by_id: dict[str, SourceArtifact] = {}
        for artifact in artifacts:
            previous = artifacts_by_id.get(artifact.artifact_id)
            if previous is not None and previous != artifact:
                raise SourceAccessError(
                    f"conflicting Artifact identity: {artifact.artifact_id}"
                )
            artifacts_by_id[artifact.artifact_id] = artifact

        return SourceCollection(
            source_id=self._source_id(scope_id),
            scope_id=scope_id,
            revision=revision,
            artifacts=tuple(
                sorted(artifacts_by_id.values(), key=lambda item: item.artifact_id)
            ),
            build_profile=request.build_profile,
        )

    def resolve_revision(self, scope_id: str, revision: str) -> SourceObjectRef:
        """Resolve a Git revision and discover its ordered parent revisions."""

        self._assert_repository()
        if not revision or revision.startswith("-"):
            raise SourceAccessError(f"invalid Git revision: {revision!r}")
        resolved = self._git("rev-parse", "--verify", f"{revision}^{{commit}}")
        parents = tuple(
            item
            for item in self._git("show", "-s", "--format=%P", resolved).split()
            if item
        )
        return SourceObjectRef(
            source_id=self._source_id(scope_id),
            scope_id=scope_id,
            object_type="git-commit",
            external_key=resolved,
            revision=resolved,
            content_id=resolved,
            parent_revisions=parents,
        )

    def search_at_revision(
        self,
        scope_id: str,
        revision: str,
        query: str | None = None,
        include_globs: tuple[str, ...] = (),
    ) -> tuple[SourceObjectRef, ...]:
        """Discover matching blobs without turning search hits into Artifacts."""

        resolved = self.resolve_revision(scope_id, revision).revision
        for pattern in include_globs:
            self._validate_tree_pattern(pattern)
        results: list[SourceObjectRef] = []
        for relative_path, (_, object_id) in self._tree_entries(resolved).items():
            if not self._matches_globs(relative_path, include_globs):
                continue
            if query is not None:
                raw = self._git_bytes("cat-file", "blob", object_id)
                try:
                    searchable = raw.decode("utf-8")
                except UnicodeDecodeError:
                    continue
                if query not in searchable:
                    continue
            results.append(
                SourceObjectRef(
                    source_id=self._source_id(scope_id),
                    scope_id=scope_id,
                    object_type="git-blob",
                    external_key=relative_path,
                    revision=resolved,
                    content_id=object_id,
                )
            )
        return tuple(sorted(results, key=lambda item: item.external_key))

    def read_files_at_revision(
        self,
        scope_id: str,
        revision: str,
        paths: tuple[str | SourceObjectRef, ...],
    ) -> tuple[SourceArtifact, ...]:
        """Materialize selected tracked files directly from the Git object database."""

        resolved = self.resolve_revision(scope_id, revision).revision
        entries = self._tree_entries(resolved)
        requested_paths: set[str] = set()
        for item in paths:
            if isinstance(item, SourceObjectRef):
                if item.object_type != "git-blob":
                    raise SourceAccessError(
                        f"source reference is not a Git blob: {item.external_key}"
                    )
                if item.scope_id != scope_id or item.revision != resolved:
                    raise SourceAccessError(
                        f"source reference context differs: {item.external_key}"
                    )
                relative_path = item.external_key
            else:
                relative_path = item
            self._validate_relative_path(relative_path)
            requested_paths.add(relative_path)

        artifacts: list[SourceArtifact] = []
        for relative_path in sorted(requested_paths):
            entry = entries.get(relative_path)
            if entry is None:
                raise SourceAccessError(
                    f"path is not a tracked file at {resolved}: {relative_path}"
                )
            _, object_id = entry
            raw = self._git_bytes("cat-file", "blob", object_id)
            try:
                content = raw.decode("utf-8")
            except UnicodeDecodeError as error:
                raise SourceAccessError(
                    f"requested source is not UTF-8 text: {relative_path}"
                ) from error
            digest = content_hash(content)
            artifacts.append(
                SourceArtifact(
                    artifact_id=stable_id(
                        "artifact", scope_id, relative_path, resolved, digest
                    ),
                    artifact_type=self._artifact_type(Path(relative_path)),
                    source_id=self._source_id(scope_id),
                    scope_id=scope_id,
                    relative_path=relative_path,
                    revision=resolved,
                    content_hash=digest,
                    content=content,
                )
            )
        return tuple(artifacts)

    def read_commit(self, scope_id: str, revision: str) -> SourceArtifact:
        """Materialize immutable commit metadata without an implicit diff."""

        commit_id = self.resolve_revision(scope_id, revision).revision
        raw = self._git_bytes(
            "show", "--no-patch", "--format=fuller", "--no-color", commit_id
        )
        try:
            content = raw.decode("utf-8")
        except UnicodeDecodeError as error:
            raise SourceAccessError(
                f"commit metadata is not UTF-8 text: {commit_id}"
            ) from error
        digest = content_hash(content)
        return SourceArtifact(
            artifact_id=stable_id(
                "artifact", scope_id, "git-commit", commit_id, digest
            ),
            artifact_type="git-commit",
            source_id=self._source_id(scope_id),
            scope_id=scope_id,
            relative_path=f".git/commits/{commit_id}.commit",
            revision=commit_id,
            content_hash=digest,
            content=content,
        )

    def compare_revisions(
        self,
        scope_id: str,
        comparison: RevisionComparison,
        include_globs: tuple[str, ...] = (),
    ) -> SourceArtifact:
        """Materialize one explicit and reproducible base-to-target Git diff."""

        base = self.resolve_revision(scope_id, comparison.base_revision).revision
        target = self.resolve_revision(scope_id, comparison.target_revision).revision
        for pattern in include_globs:
            self._validate_tree_pattern(pattern)
        args = [
            "diff",
            "--no-ext-diff",
            "--no-color",
            "--no-renames",
            "--find-copies=0",
            base,
            target,
        ]
        if include_globs:
            args.extend(("--", *include_globs))
        raw = self._git_bytes(*args)
        try:
            content = raw.decode("utf-8")
        except UnicodeDecodeError as error:
            raise SourceAccessError(
                f"revision diff is not UTF-8 text: {base}..{target}"
            ) from error
        digest = content_hash(content)
        resolved_comparison = RevisionComparison(
            base_revision=base,
            target_revision=target,
        )
        return SourceArtifact(
            artifact_id=stable_id(
                "artifact",
                scope_id,
                "git-diff",
                base,
                target,
                *tuple(sorted(include_globs)),
                digest,
            ),
            artifact_type="git-diff",
            source_id=self._source_id(scope_id),
            scope_id=scope_id,
            relative_path=f".git/diffs/{base}..{target}.patch",
            revision=target,
            content_hash=digest,
            content=content,
            comparison=resolved_comparison,
        )

    def _read_legacy_commit(
        self, scope_id: str, revision: str
    ) -> SourceArtifact:
        """Preserve the original combined commit-and-patch request semantics."""

        commit_id = self.resolve_revision(scope_id, revision).revision
        content = self._git(
            "show",
            "--format=fuller",
            "--no-ext-diff",
            "--no-renames",
            "--find-copies=0",
            commit_id,
        )
        digest = content_hash(content)
        return SourceArtifact(
            artifact_id=stable_id(
                "artifact", scope_id, "git-commit", commit_id, digest
            ),
            artifact_type="git-commit",
            source_id=self._source_id(scope_id),
            scope_id=scope_id,
            relative_path=f".git/commits/{commit_id}.patch",
            revision=commit_id,
            content_hash=digest,
            content=content,
        )

    @staticmethod
    def _source_id(scope_id: str) -> str:
        return stable_id("source", scope_id, "local-git")

    def _tree_entries(self, revision: str) -> dict[str, tuple[str, str]]:
        raw = self._git_bytes("ls-tree", "-r", "-z", "--full-tree", revision)
        entries: dict[str, tuple[str, str]] = {}
        for record in raw.split(b"\0"):
            if not record:
                continue
            try:
                metadata, encoded_path = record.split(b"\t", maxsplit=1)
                mode, object_type, object_id = metadata.decode("ascii").split()
                relative_path = encoded_path.decode("utf-8")
            except (UnicodeDecodeError, ValueError) as error:
                raise SourceAccessError(
                    f"invalid Git tree entry at revision {revision}"
                ) from error
            if object_type != "blob":
                continue
            self._validate_relative_path(relative_path)
            entries[relative_path] = (mode, object_id)
        return entries

    @classmethod
    def _matches_globs(
        cls, relative_path: str, patterns: tuple[str, ...]
    ) -> bool:
        if not patterns:
            return True
        path_parts = PurePosixPath(relative_path).parts
        return any(
            cls._matches_parts(path_parts, PurePosixPath(pattern).parts)
            for pattern in patterns
        )

    @classmethod
    def _matches_parts(
        cls, path_parts: tuple[str, ...], pattern_parts: tuple[str, ...]
    ) -> bool:
        if not pattern_parts:
            return not path_parts
        pattern = pattern_parts[0]
        if pattern == "**":
            return cls._matches_parts(path_parts, pattern_parts[1:]) or (
                bool(path_parts)
                and cls._matches_parts(path_parts[1:], pattern_parts)
            )
        return bool(path_parts) and fnmatchcase(path_parts[0], pattern) and (
            cls._matches_parts(path_parts[1:], pattern_parts[1:])
        )

    @staticmethod
    def _validate_relative_path(relative_path: str) -> None:
        if (
            not relative_path
            or relative_path.startswith("/")
            or "\0" in relative_path
            or any(
                part in {"", ".", ".."} for part in relative_path.split("/")
            )
        ):
            raise SourceAccessError(
                f"invalid repository-relative path: {relative_path!r}"
            )

    @staticmethod
    def _validate_tree_pattern(pattern: str) -> None:
        if (
            not pattern
            or pattern.startswith("/")
            or "\0" in pattern
            or ".." in pattern.split("/")
        ):
            raise SourceAccessError(f"invalid Git tree pattern: {pattern!r}")

    @staticmethod
    def _artifact_type(path: Path) -> str:
        if path.name == "pom.xml":
            return "maven-pom"
        suffix = path.suffix.lower()
        return {
            ".java": "java-source",
            ".md": "markdown-document",
            ".xml": "xml-document",
            ".yml": "yaml-document",
            ".yaml": "yaml-document",
            ".properties": "properties-document",
        }.get(suffix, "text-document")

    def _assert_repository(self) -> None:
        if not self.repository.is_dir():
            raise SourceAccessError(f"source directory does not exist: {self.repository}")
        if not (self.repository / ".git").is_dir():
            raise SourceAccessError(
                f"source directory is not a full Git checkout: {self.repository}"
            )

    def _git(self, *args: str) -> str:
        raw = self._git_bytes(*args)
        try:
            return raw.decode("utf-8").strip()
        except UnicodeDecodeError as error:
            raise SourceAccessError(
                f"git {' '.join(args)} returned non-UTF-8 text"
            ) from error

    def _git_bytes(self, *args: str) -> bytes:
        completed = subprocess.run(
            ["git", *args],
            cwd=self.repository,
            check=False,
            capture_output=True,
        )
        if completed.returncode != 0:
            message = (
                completed.stderr.decode("utf-8", errors="replace").strip()
                or completed.stdout.decode("utf-8", errors="replace").strip()
            )
            raise SourceAccessError(f"git {' '.join(args)} failed: {message}")
        return completed.stdout
