from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RevisionComparison:
    """An explicit, ordered comparison between two source revisions."""

    base_revision: str
    target_revision: str


@dataclass(frozen=True)
class SourceObjectRef:
    """A lightweight source discovery result without materialized content."""

    source_id: str
    scope_id: str
    object_type: str
    external_key: str
    revision: str
    content_id: str | None = None
    parent_revisions: tuple[str, ...] = ()


@dataclass(frozen=True)
class SourceArtifact:
    artifact_id: str
    artifact_type: str
    source_id: str
    scope_id: str
    relative_path: str
    revision: str
    content_hash: str
    content: str
    lineage_ids: tuple[str, ...] = ()
    comparison: RevisionComparison | None = None


@dataclass(frozen=True)
class SourceCollection:
    source_id: str
    scope_id: str
    revision: str
    artifacts: tuple[SourceArtifact, ...]
    build_profile: str = "structure-core"


@dataclass(frozen=True)
class ArtifactRequest:
    """Bounded source request selected by an Application Service.

    Revision, globs, commit ids and explicit comparisons describe information
    to collect; they do not contain domain conclusions and therefore do not
    move knowledge logic into Source Integration. ``git_commit_ids`` preserves
    the original combined commit-and-patch request during migration.
    """

    build_profile: str
    include_globs: tuple[str, ...]
    git_commit_ids: tuple[str, ...] = ()
    derive_java_ast: bool = False
    revision: str | None = None
    commit_revisions: tuple[str, ...] = ()
    comparisons: tuple[RevisionComparison, ...] = ()
