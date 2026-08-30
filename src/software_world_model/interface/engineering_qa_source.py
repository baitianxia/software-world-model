"""Isolated-style Local Git Retrieval Worker for ``ENGINEERING_QA``.

The worker receives only a Broker-compiled operation.  It uses a fixed Git argv
surface against immutable objects, never checks out files, follows links,
writes the repository, fetches remotes, opens the network, or resolves a
credential.  Model roles never receive this object.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath
import re
import subprocess
from typing import Mapping, Sequence

from software_world_model.application_services.engineering_question_answering import (
    ENGINEERING_QA_BROKER_POLICY,
    CompiledSourceOperation,
    EngineeringEvidenceClass,
    RetrievalItem,
    RetrievalResult,
    RetrievalStatus,
    SourceReadOperation,
)
from software_world_model.cross_cutting import (
    Digest,
    DomainError,
    ErrorCode,
    StableId,
    digest_of,
)
from software_world_model.source_integration import LocalGitConnector


_REGULAR_GIT_MODES = frozenset({"100644", "100755"})
_LOCAL_GIT_SOURCE_PROFILE_SCHEMA = "ENGINEERING_QA_LOCAL_GIT_SOURCE_PROFILE@1"
_PROFILE_REFERENCE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$")
_PROFILE_EVIDENCE_CLASSES = frozenset(
    {
        EngineeringEvidenceClass.SOURCE,
        EngineeringEvidenceClass.REPOSITORY_DOCUMENT,
        EngineeringEvidenceClass.BUILD_CONFIGURATION,
        EngineeringEvidenceClass.TEST,
    }
)
_LOCAL_GIT_MODALITY_POLICY = {
    EngineeringEvidenceClass.SOURCE: {
        SourceReadOperation.SEARCH: "LITERAL_TEXT_SEARCH_HIT",
        SourceReadOperation.READ: "EXACT_STATIC_SOURCE_TEXT",
        SourceReadOperation.PARSE: "UTF8_SOURCE_TEXT_PROJECTION",
    },
    EngineeringEvidenceClass.REPOSITORY_DOCUMENT: {
        SourceReadOperation.SEARCH: "LITERAL_TEXT_SEARCH_HIT",
        SourceReadOperation.READ: "EXACT_REPOSITORY_DOCUMENT_TEXT",
        SourceReadOperation.PARSE: "UTF8_REPOSITORY_DOCUMENT_PROJECTION",
    },
    EngineeringEvidenceClass.BUILD_CONFIGURATION: {
        SourceReadOperation.SEARCH: "LITERAL_TEXT_SEARCH_HIT",
        SourceReadOperation.READ: "EXACT_BUILD_CONFIGURATION_TEXT",
        SourceReadOperation.PARSE: "UTF8_BUILD_CONFIGURATION_PROJECTION",
    },
    EngineeringEvidenceClass.TEST: {
        SourceReadOperation.SEARCH: "LITERAL_TEXT_SEARCH_HIT",
        SourceReadOperation.READ: "EXACT_STATIC_TEST_TEXT",
        SourceReadOperation.PARSE: "UTF8_STATIC_TEST_PROJECTION",
    },
}


def _allowed(path: str, allowlist: tuple[str, ...]) -> bool:
    return any(
        prefix == "." or path == prefix or path.startswith(prefix + "/")
        for prefix in allowlist
    )


def _profile_path(value: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            "Local Git Source Profile path must be non-empty and canonical",
        )
    value = value.replace("\\", "/")
    if value == ".":
        return value
    if value.startswith("/") or "\x00" in value:
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            "Local Git Source Profile path must be repository-relative",
        )
    parts = tuple(part for part in value.split("/") if part not in {"", "."})
    if not parts or any(part == ".." for part in parts):
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            "Local Git Source Profile path cannot traverse parent directories",
        )
    return "/".join(parts)


def _paths_overlap(left: str, right: str) -> bool:
    return (
        left == "."
        or right == "."
        or left == right
        or left.startswith(right + "/")
        or right.startswith(left + "/")
    )


def _search_entry_rank(path: str, query: str) -> tuple[int, str]:
    """Prefer authorized path names that contain the literal search token.

    SEARCH remains a case-sensitive content operation.  This ordering only
    uses already-authorized tree metadata so a bounded scan can inspect the
    most plausible files before the file fuse, while preserving a canonical
    fallback order for every other entry.
    """

    folded_query = query.casefold()
    folded_path = path.casefold()
    name = PurePosixPath(path).name.casefold()
    stem = PurePosixPath(path).stem.casefold()
    if stem == folded_query or name == folded_query:
        priority = 0
    elif folded_query in name:
        priority = 1
    elif folded_query in folded_path:
        priority = 2
    else:
        priority = 3
    return priority, path


@dataclass(frozen=True, slots=True)
class LocalGitEvidenceClassProfile:
    """Versioned, Binding-scoped classification of repository paths."""

    schema: str
    profile_ref: str
    binding_id: StableId
    evidence_class_paths: tuple[
        tuple[EngineeringEvidenceClass, tuple[str, ...]], ...
    ]
    profile_digest: Digest

    @classmethod
    def create(
        cls,
        *,
        profile_ref: str,
        binding_id: StableId,
        evidence_class_paths: Mapping[
            EngineeringEvidenceClass, Sequence[str]
        ],
    ) -> "LocalGitEvidenceClassProfile":
        if (
            not isinstance(profile_ref, str)
            or not profile_ref
            or profile_ref != profile_ref.strip()
            or len(profile_ref.encode("utf-8")) > 256
            or not _PROFILE_REFERENCE.fullmatch(profile_ref)
        ):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "Local Git Source Profile reference is invalid",
            )
        normalized: list[tuple[EngineeringEvidenceClass, tuple[str, ...]]] = []
        for evidence_class, paths in evidence_class_paths.items():
            if evidence_class not in _PROFILE_EVIDENCE_CLASSES:
                raise DomainError(
                    ErrorCode.INVALID_ARGUMENT,
                    "Local Git Source Profile contains a non-retrieval evidence class",
                )
            canonical = tuple(sorted({_profile_path(path) for path in paths}))
            if not canonical:
                raise DomainError(
                    ErrorCode.INVALID_ARGUMENT,
                    "Local Git Source Profile class allowlist cannot be empty",
                )
            normalized.append((evidence_class, canonical))
        normalized.sort(key=lambda item: item[0].value)
        if not normalized:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "Local Git Source Profile must register an evidence class",
            )
        for index, (left_class, left_paths) in enumerate(normalized):
            for right_class, right_paths in normalized[index + 1 :]:
                if any(
                    _paths_overlap(left, right)
                    for left in left_paths
                    for right in right_paths
                ):
                    raise DomainError(
                        ErrorCode.INVALID_ARGUMENT,
                        "Local Git Source Profile evidence-class paths overlap",
                        {
                            "left_class": left_class.value,
                            "right_class": right_class.value,
                        },
                    )
        canonical_paths = tuple(normalized)
        core = {
            "schema": _LOCAL_GIT_SOURCE_PROFILE_SCHEMA,
            "profile_ref": profile_ref,
            "binding_id": binding_id.value,
            "evidence_class_paths": tuple(
                (evidence_class.value, paths)
                for evidence_class, paths in canonical_paths
            ),
            "operation_modalities": tuple(
                (
                    evidence_class.value,
                    tuple(
                        (operation.value, modality)
                        for operation, modality in sorted(
                            _LOCAL_GIT_MODALITY_POLICY[evidence_class].items(),
                            key=lambda item: item[0].value,
                        )
                    ),
                )
                for evidence_class in sorted(
                    _LOCAL_GIT_MODALITY_POLICY,
                    key=lambda item: item.value,
                )
            ),
        }
        return cls(
            schema=_LOCAL_GIT_SOURCE_PROFILE_SCHEMA,
            profile_ref=profile_ref,
            binding_id=binding_id,
            evidence_class_paths=canonical_paths,
            profile_digest=digest_of(
                [_LOCAL_GIT_SOURCE_PROFILE_SCHEMA, core]
            ),
        )

    def require_valid(self) -> None:
        expected = LocalGitEvidenceClassProfile.create(
            profile_ref=self.profile_ref,
            binding_id=self.binding_id,
            evidence_class_paths=dict(self.evidence_class_paths),
        )
        if self != expected:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Local Git Source Profile identity is invalid",
            )

    def paths_for(
        self, evidence_class: EngineeringEvidenceClass
    ) -> tuple[str, ...]:
        return dict(self.evidence_class_paths).get(evidence_class, ())

    def permits(
        self,
        *,
        evidence_class: EngineeringEvidenceClass,
        path: str | None = None,
    ) -> bool:
        paths = self.paths_for(evidence_class)
        if not paths:
            return False
        return path is None or _allowed(_profile_path(path), paths)

    def modality_for(
        self,
        *,
        evidence_class: EngineeringEvidenceClass,
        operation: SourceReadOperation,
    ) -> str:
        try:
            return _LOCAL_GIT_MODALITY_POLICY[evidence_class][operation]
        except (KeyError, TypeError) as exc:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "Local Git Source Profile has no modality for this class and operation",
            ) from exc


class LocalGitRetrievalWorker:
    """Execute exact-revision, allowlisted, bounded UTF-8 text observations."""

    contract_version = "ENGINEERING_QA_LOCAL_GIT_RETRIEVAL_WORKER@1"

    def __init__(
        self,
        repository: str | Path,
        *,
        repository_id: StableId,
        binding_id: StableId,
        source_profile: LocalGitEvidenceClassProfile,
    ) -> None:
        root = Path(repository)
        if not root.is_absolute():
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "Engineering QA Local Git repository must be an absolute path",
            )
        try:
            canonical = root.resolve(strict=True)
        except OSError as exc:
            raise DomainError(
                ErrorCode.SOURCE_TARGET_NOT_FOUND,
                "Engineering QA Local Git repository does not exist",
            ) from exc
        if not canonical.is_dir():
            raise DomainError(
                ErrorCode.SOURCE_TARGET_NOT_FOUND,
                "Engineering QA Local Git repository must be a directory",
            )
        source_profile.require_valid()
        if source_profile.binding_id != binding_id:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Local Git Source Profile binds another repository Binding",
            )
        self._repository = canonical
        self._repository_id = repository_id
        self._binding_id = binding_id
        self._source_profile = source_profile
        self._connector = LocalGitConnector(str(canonical))

    @property
    def repository_id(self) -> StableId:
        """Return the exact repository identity accepted by this Worker."""

        return self._repository_id

    @property
    def binding_id(self) -> StableId:
        """Return the exact Source Binding accepted by this Worker."""

        return self._binding_id

    @property
    def source_profile_ref(self) -> str:
        """Return the versioned Source Profile accepted by this Worker."""

        return self._source_profile.profile_ref

    @property
    def source_profile_digest(self) -> Digest:
        """Return the exact Source Profile digest accepted by this Worker."""

        return self._source_profile.profile_digest

    def execute(self, operation: CompiledSourceOperation) -> RetrievalResult:
        operation.validate_identity()
        self._source_profile.require_valid()
        if operation.broker_policy != ENGINEERING_QA_BROKER_POLICY:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Retrieval Worker requires an Engineering QA Broker operation",
            )
        if (
            operation.repository_id != self._repository_id
            or operation.binding_id != self._binding_id
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Retrieval Worker operation does not bind its configured repository identity",
            )
        profile_paths = self._source_profile.paths_for(operation.evidence_class)
        result_modality = self._source_profile.modality_for(
            evidence_class=operation.evidence_class,
            operation=operation.operation,
        )
        if (
            operation.source_profile_ref != self._source_profile.profile_ref
            or operation.source_profile_digest
            != self._source_profile.profile_digest
            or operation.evidence_class_allowlist != profile_paths
            or operation.result_modality != result_modality
            or not self._source_profile.permits(
                evidence_class=operation.evidence_class,
                path=operation.path,
            )
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Retrieval Worker operation does not bind its exact Source Profile class",
            )
        exact_revision = self._connector.resolve_revision(
            operation.repository_revision
        )
        if exact_revision != operation.repository_revision:
            raise DomainError(
                ErrorCode.SOURCE_REVISION_INCONSISTENT,
                "Retrieval Worker revision resolution drifted",
            )
        entries = tuple(
            item
            for item in self._connector.list_tree_entries(exact_revision)
            if _allowed(item.path, operation.source_allowlist)
            and _allowed(item.path, operation.evidence_class_allowlist)
        )
        if operation.operation is SourceReadOperation.SEARCH:
            return self._search(operation=operation, entries=entries)
        if operation.operation in {SourceReadOperation.READ, SourceReadOperation.PARSE}:
            return self._read(operation=operation, entries=entries)
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "Retrieval Worker received an unregistered operation",
        )

    def _search(self, *, operation: CompiledSourceOperation, entries) -> RetrievalResult:
        if operation.query is None or operation.path is not None:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "compiled search operation has an invalid shape",
            )
        bytes_read = 0
        files_read = 0
        items: list[RetrievalItem] = []
        unsafe_entries = 0
        binary_entries = 0
        truncated = False
        failure_code: str | None = None
        allowed_entry_count = len(entries)
        candidate_ordering = (
            "QUERY_PATH_RELEVANCE_THEN_ROTATING_CANONICAL_FALLBACK@2"
        )
        search_scope_coverage: dict[str, str] = {
            "search_path_scope_count": "0",
            "search_path_scope_digest": "NONE",
            "search_path_prefix_scope_count": "0",
            "search_path_prefix_scope_digest": "NONE",
            "search_scope": "AUTHORIZED_EVIDENCE_CLASS_ALLOWLIST",
        }
        if operation.search_path_scope:
            entries_by_path = {entry.path: entry for entry in entries}
            missing_paths = tuple(
                path
                for path in operation.search_path_scope
                if path not in entries_by_path
            )
            search_scope_coverage = {
                "search_path_scope_count": str(
                    len(operation.search_path_scope)
                ),
                "search_path_scope_digest": digest_of(
                    [
                        "ENGINEERING_QA_TRUSTED_SOURCE_SEARCH_PATH_SCOPE@1",
                        operation.query,
                        operation.search_path_scope,
                    ]
                ).value,
                "search_path_prefix_scope_count": "0",
                "search_path_prefix_scope_digest": "NONE",
                "search_scope": "TRUSTED_COGNITION_TARGET_PATHS",
            }
            candidate_ordering = "TRUSTED_TARGET_PATH_SCOPE_THEN_CANONICAL@2"
            if missing_paths:
                return RetrievalResult.create(
                    operation=operation,
                    status=RetrievalStatus.FAILED,
                    items=(),
                    bytes_read=0,
                    files_read=0,
                    truncated=False,
                    coverage=self._coverage(
                        operation,
                        {
                            "allowed_entry_count": str(allowed_entry_count),
                            "scoped_entry_count": str(
                                len(operation.search_path_scope)
                                - len(missing_paths)
                            ),
                            "examined_file_count": "0",
                            "match_count": "0",
                            "unsafe_entry_count": "0",
                            "binary_entry_count": "0",
                            "missing_search_path_scope_count": str(
                                len(missing_paths)
                            ),
                            "query_digest": digest_of(
                                [
                                    "ENGINEERING_QA_LITERAL_QUERY@1",
                                    operation.query,
                                ]
                            ).value,
                            "candidate_ordering": candidate_ordering,
                            "search_fallback_offset": str(
                                operation.search_fallback_offset
                            ),
                            "search_fallback_offset_applied": "0",
                            "fallback_examined_file_count": "0",
                            **search_scope_coverage,
                        },
                    ),
                    failure_code="SOURCE_SEARCH_PATH_SCOPE_INCONSISTENT",
                )
            entries = tuple(
                entries_by_path[path] for path in operation.search_path_scope
            )
        elif operation.search_path_prefix_scope:
            entries = tuple(
                entry
                for entry in entries
                if _allowed(entry.path, operation.search_path_prefix_scope)
            )
            search_scope_coverage = {
                "search_path_scope_count": "0",
                "search_path_scope_digest": "NONE",
                "search_path_prefix_scope_count": str(
                    len(operation.search_path_prefix_scope)
                ),
                "search_path_prefix_scope_digest": digest_of(
                    [
                        "ENGINEERING_QA_TRUSTED_SOURCE_SEARCH_PREFIX_SCOPE@1",
                        operation.search_path_prefix_scope,
                    ]
                ).value,
                "search_scope": "ORIGINAL_QUESTION_EXPLICIT_SOURCE_PREFIXES",
            }
            candidate_ordering = (
                "QUESTION_PREFIX_QUERY_PATH_THEN_ROTATING_CANONICAL_FALLBACK@1"
            )
        ranked_candidates = tuple(
            sorted(
                (
                    (_search_entry_rank(entry.path, operation.query), entry)
                    for entry in entries
                ),
                key=lambda candidate: candidate[0],
            )
        )
        path_candidates = tuple(
            candidate for candidate in ranked_candidates if candidate[0][0] <= 2
        )
        fallback_candidates = tuple(
            candidate for candidate in ranked_candidates if candidate[0][0] == 3
        )
        fallback_offset_applied = (
            operation.search_fallback_offset % len(fallback_candidates)
            if fallback_candidates
            else 0
        )
        ranked_entries = (
            *path_candidates,
            *fallback_candidates[fallback_offset_applied:],
            *fallback_candidates[:fallback_offset_applied],
        )
        folded_query = operation.query.casefold()
        exact_stem_candidate_count = sum(
            PurePosixPath(entry.path).stem.casefold() == folded_query
            for _, entry in ranked_entries
        )
        filename_candidate_count = sum(
            rank[0] <= 1 for rank, _ in ranked_entries
        )
        filename_candidates_processed = 0
        filename_content_match_count = 0
        filename_unsafe_count = 0
        filename_early_stop = False
        fallback_examined_file_count = 0
        for rank, entry in ranked_entries:
            filename_candidate = rank[0] <= 1
            if entry.object_type != "blob" or entry.mode not in _REGULAR_GIT_MODES:
                unsafe_entries += 1
                if filename_candidate:
                    filename_candidates_processed += 1
                    filename_unsafe_count += 1
                continue
            if files_read >= operation.maximum_files:
                truncated = True
                failure_code = "SOURCE_SEARCH_FILE_LIMIT_REACHED"
                break
            object_size = self._object_size(entry.object_id)
            remaining = operation.maximum_source_bytes - bytes_read
            if object_size > remaining:
                truncated = True
                failure_code = "SOURCE_SEARCH_BYTE_LIMIT_REACHED"
                break
            raw = self._connector.read_path(operation.repository_revision, entry.path)
            if len(raw) != object_size:
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "Local Git blob size changed during Retrieval Worker read",
                )
            bytes_read += len(raw)
            files_read += 1
            if rank[0] == 3:
                fallback_examined_file_count += 1
            if b"\x00" in raw:
                binary_entries += 1
                if filename_candidate:
                    filename_candidates_processed += 1
                    filename_unsafe_count += 1
                continue
            try:
                content = raw.decode("utf-8")
            except UnicodeDecodeError:
                binary_entries += 1
                if filename_candidate:
                    filename_candidates_processed += 1
                    filename_unsafe_count += 1
                continue
            matches_before_entry = len(items)
            for line_number, line in enumerate(content.splitlines(), 1):
                if operation.query not in line:
                    continue
                if len(items) >= operation.maximum_result_items:
                    truncated = True
                    failure_code = "SOURCE_RESULT_ITEM_FUSE_EXHAUSTED"
                    break
                items.append(
                    RetrievalItem.create(
                        operation_id=operation.operation_id,
                        ordinal=len(items) + 1,
                        evidence_class=operation.evidence_class,
                        path=entry.path,
                        line_start=line_number,
                        line_end=line_number,
                        content=line,
                        modality=operation.result_modality,
                        coverage_complete=True,
                    )
                )
            if truncated and failure_code == "SOURCE_RESULT_ITEM_FUSE_EXHAUSTED":
                break
            if filename_candidate:
                filename_candidates_processed += 1
                filename_content_match_count += len(items) - matches_before_entry
                if (
                    exact_stem_candidate_count > 0
                    and filename_candidates_processed
                    == filename_candidate_count
                    and filename_content_match_count > 0
                    and filename_unsafe_count == 0
                    and len(ranked_entries) > filename_candidate_count
                ):
                    # The exact-stem anchor and every related filename have
                    # yielded all of their case-sensitive content hits.  Keep
                    # the unexamined lower-ranked corpus explicit as PARTIAL
                    # instead of spending the whole-Turn file budget merely to
                    # rediscover a locator already present in this cohort.
                    truncated = True
                    filename_early_stop = True
                    failure_code = "SOURCE_SEARCH_FILENAME_MATCH_EARLY_STOP"
                    break
        if unsafe_entries or binary_entries:
            truncated = True
            failure_code = failure_code or "UNSUPPORTED_SOURCE_ENTRY"
        status = RetrievalStatus.PARTIAL if truncated else RetrievalStatus.COMPLETE
        return RetrievalResult.create(
            operation=operation,
            status=status,
            items=items,
            bytes_read=bytes_read,
            files_read=files_read,
            truncated=truncated,
            coverage=self._coverage(
                operation,
                {
                    "allowed_entry_count": str(allowed_entry_count),
                    "scoped_entry_count": str(len(entries)),
                    "examined_file_count": str(files_read),
                    "match_count": str(len(items)),
                    "unsafe_entry_count": str(unsafe_entries),
                    "binary_entry_count": str(binary_entries),
                    "exact_stem_candidate_count": str(
                        exact_stem_candidate_count
                    ),
                    "filename_candidate_count": str(filename_candidate_count),
                    "filename_content_match_count": str(
                        filename_content_match_count
                    ),
                    "filename_early_stop": str(filename_early_stop).lower(),
                    "query_digest": digest_of(
                        ["ENGINEERING_QA_LITERAL_QUERY@1", operation.query]
                    ).value,
                    "candidate_ordering": candidate_ordering,
                    "search_fallback_offset": str(
                        operation.search_fallback_offset
                    ),
                    "search_fallback_offset_applied": str(
                        fallback_offset_applied
                    ),
                    "fallback_examined_file_count": str(
                        fallback_examined_file_count
                    ),
                    **search_scope_coverage,
                },
            ),
            failure_code=failure_code,
        )

    def _read(self, *, operation: CompiledSourceOperation, entries) -> RetrievalResult:
        if operation.path is None or operation.query is not None:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "compiled read/parse operation has an invalid shape",
            )
        entry = next((item for item in entries if item.path == operation.path), None)
        if entry is None:
            return RetrievalResult.create(
                operation=operation,
                status=RetrievalStatus.FAILED,
                items=(),
                bytes_read=0,
                files_read=0,
                truncated=False,
                coverage=self._coverage(
                    operation,
                    {"path": operation.path, "resolved": "false"},
                ),
                failure_code="SOURCE_PATH_NOT_FOUND",
            )
        if entry.object_type != "blob" or entry.mode not in _REGULAR_GIT_MODES:
            return RetrievalResult.create(
                operation=operation,
                status=RetrievalStatus.FAILED,
                items=(),
                bytes_read=0,
                files_read=0,
                truncated=False,
                coverage=self._coverage(
                    operation,
                    {
                        "path": operation.path,
                        "object_type": entry.object_type,
                        "mode": entry.mode,
                    },
                ),
                failure_code="UNSAFE_SOURCE_ENTRY_KIND",
            )
        object_size = self._object_size(entry.object_id)
        if object_size > operation.maximum_source_bytes:
            return RetrievalResult.create(
                operation=operation,
                status=RetrievalStatus.PARTIAL,
                items=(),
                bytes_read=0,
                files_read=0,
                truncated=True,
                coverage=self._coverage(
                    operation,
                    {
                        "path": operation.path,
                        "object_bytes": str(object_size),
                        "read_bytes": "0",
                    },
                ),
                failure_code="SOURCE_BYTE_FUSE_WOULD_BE_EXCEEDED",
            )
        raw = self._connector.read_path(operation.repository_revision, operation.path)
        if len(raw) != object_size:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Local Git blob size changed during Retrieval Worker read",
            )
        if b"\x00" in raw:
            return RetrievalResult.create(
                operation=operation,
                status=RetrievalStatus.FAILED,
                items=(),
                bytes_read=len(raw),
                files_read=1,
                truncated=False,
                coverage=self._coverage(
                    operation,
                    {"path": operation.path, "read_bytes": str(len(raw))},
                ),
                failure_code="BINARY_SOURCE_REJECTED",
            )
        try:
            content = raw.decode("utf-8")
        except UnicodeDecodeError:
            return RetrievalResult.create(
                operation=operation,
                status=RetrievalStatus.FAILED,
                items=(),
                bytes_read=len(raw),
                files_read=1,
                truncated=False,
                coverage=self._coverage(
                    operation,
                    {"path": operation.path, "read_bytes": str(len(raw))},
                ),
                failure_code="NON_UTF8_SOURCE_REJECTED",
            )
        items = ()
        if content:
            items = (
                RetrievalItem.create(
                    operation_id=operation.operation_id,
                    ordinal=1,
                    evidence_class=operation.evidence_class,
                    path=operation.path,
                    content=content,
                    modality=operation.result_modality,
                    coverage_complete=True,
                ),
            )
        return RetrievalResult.create(
            operation=operation,
            status=RetrievalStatus.COMPLETE,
            items=items,
            bytes_read=len(raw),
            files_read=1,
            truncated=False,
            coverage=self._coverage(
                operation,
                {
                    "path": operation.path,
                    "read_bytes": str(len(raw)),
                    "total_bytes": str(object_size),
                    "complete": "true",
                },
            ),
        )

    @staticmethod
    def _coverage(
        operation: CompiledSourceOperation,
        values: Mapping[str, str],
    ) -> dict[str, str]:
        return {
            **values,
            "source_profile_ref": operation.source_profile_ref,
            "source_profile_digest": operation.source_profile_digest.value,
            "evidence_class": operation.evidence_class.value,
        }

    def _object_size(self, object_id: str) -> int:
        try:
            process = subprocess.run(
                ("git", "-C", str(self._repository), "cat-file", "-s", object_id),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=15,
                check=False,
                text=True,
            )
        except subprocess.TimeoutExpired as exc:
            raise DomainError(
                ErrorCode.SOURCE_OPERATION_FAILED,
                "Local Git object-size query timed out",
            ) from exc
        if process.returncode != 0:
            raise DomainError(
                ErrorCode.SOURCE_OPERATION_FAILED,
                "Local Git object-size query failed",
            )
        try:
            size = int(process.stdout.strip())
        except ValueError as exc:
            raise DomainError(
                ErrorCode.SOURCE_OPERATION_FAILED,
                "Local Git object-size query returned an invalid value",
            ) from exc
        if size < 0:
            raise DomainError(
                ErrorCode.SOURCE_OPERATION_FAILED,
                "Local Git object-size query returned a negative value",
            )
        return size


__all__ = ["LocalGitEvidenceClassProfile", "LocalGitRetrievalWorker"]
