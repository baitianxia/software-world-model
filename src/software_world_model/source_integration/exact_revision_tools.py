"""Read-only tools over one exact Git revision (architecture baseline V1.4, 7.7).

These tools give an engineering Agent reading capability comparable to a
mature coding agent -- path listing, literal/regex search, ranged reads,
history and blame -- while keeping the platform boundaries:

* every operation is bound to one exact commit; moving branches or later
  commits never change a result;
* paths are normalized and must stay inside the configured include prefixes
  and outside the exclude prefixes; nothing outside the repository is read;
* no write, network, credential or arbitrary command is ever executed: only
  fixed ``git`` plumbing commands with structured arguments;
* results are bounded and report what was *not* examined (``PARTIAL``), so a
  truncated search is never presented as "not found";
* every returned item carries a citation locator and a content digest.

The tools do not decide relevance or truth; they only return observations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import fnmatch
import hashlib
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
from typing import Mapping, Sequence

from software_world_model.cross_cutting import Digest, DomainError, ErrorCode, digest_of


_FULL_OID = re.compile(r"^[0-9a-f]{40}$")
_MAX_PATTERN_LENGTH = 512
_GIT_TIMEOUT_SECONDS = 20


class ObservationStatus(str, Enum):
    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"
    EMPTY = "EMPTY"


@dataclass(frozen=True, slots=True)
class ReadScope:
    """The fixed, Application-owned boundary of one Conversation's source reads."""

    repository: Path
    revision: str
    include_prefixes: tuple[str, ...] = ()
    exclude_prefixes: tuple[str, ...] = ()
    max_file_bytes: int = 512_000
    max_items: int = 200
    max_output_bytes: int = 64_000

    def __post_init__(self) -> None:
        if not _FULL_OID.fullmatch(self.revision):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "read scope revision must be an exact 40-hex commit id",
            )
        for prefix in (*self.include_prefixes, *self.exclude_prefixes):
            _normalize(prefix.rstrip("/") or ".", allow_root=True)
        if min(self.max_file_bytes, self.max_items, self.max_output_bytes) < 1:
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "read scope limits must be positive")

    def allows(self, path: str) -> bool:
        def under(prefix: str) -> bool:
            prefix = prefix.rstrip("/")
            return prefix in ("", ".") or path == prefix or path.startswith(prefix + "/")

        if self.include_prefixes and not any(under(prefix) for prefix in self.include_prefixes):
            return False
        return not any(under(prefix) for prefix in self.exclude_prefixes)


@dataclass(frozen=True, slots=True)
class SourceItem:
    path: str
    start_line: int | None
    end_line: int | None
    text: str
    revision: str

    @property
    def locator(self) -> str:
        if self.start_line is None:
            return f"{self.path}@{self.revision}"
        return f"{self.path}@{self.revision}#L{self.start_line}-L{self.end_line}"

    @property
    def content_digest(self) -> str:
        return "sha256:" + hashlib.sha256(self.text.encode("utf-8")).hexdigest()

    def to_payload(self) -> dict[str, object]:
        return {
            "path": self.path,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "locator": self.locator,
            "content_digest": self.content_digest,
            "text": self.text,
        }


@dataclass(frozen=True, slots=True)
class SourceObservation:
    operation: str
    arguments: Mapping[str, object]
    revision: str
    status: ObservationStatus
    items: tuple[SourceItem, ...]
    coverage: str
    examined_count: int
    omitted_count: int = 0
    notes: tuple[str, ...] = field(default=())

    def to_payload(self) -> dict[str, object]:
        return {
            "operation": self.operation,
            "arguments": dict(self.arguments),
            "revision": self.revision,
            "status": self.status.value,
            "coverage": self.coverage,
            "examined_count": self.examined_count,
            "omitted_count": self.omitted_count,
            "notes": list(self.notes),
            "items": [item.to_payload() for item in self.items],
        }

    @property
    def digest(self) -> Digest:
        return digest_of(self.to_payload())


class ExactRevisionReadTools:
    """Bounded, read-only Git operations bound to one :class:`ReadScope`."""

    def __init__(self, scope: ReadScope) -> None:
        self._scope = scope
        self._root = scope.repository.resolve()
        if not (self._root / ".git").exists():
            raise DomainError(ErrorCode.SOURCE_TARGET_NOT_FOUND, "repository is not a Git checkout")
        try:
            self._git("cat-file", "-e", f"{scope.revision}^{{commit}}")
        except DomainError as error:
            raise DomainError(
                ErrorCode.SOURCE_REVISION_INCONSISTENT,
                "exact revision is not present in the repository",
            ) from error
        self._paths: tuple[str, ...] | None = None

    @property
    def scope(self) -> ReadScope:
        return self._scope

    # ------------------------------------------------------------------ list
    def list_paths(
        self, *, glob: str | None = None, prefix: str | None = None, limit: int | None = None
    ) -> SourceObservation:
        arguments = {"glob": glob, "prefix": prefix}
        if glob is not None:
            _bounded_text(glob, "glob")
        normalized_prefix = _normalize(prefix.rstrip("/"), allow_root=True) if prefix else None
        candidates = [
            path
            for path in self._all_paths()
            if (normalized_prefix is None or normalized_prefix in ("", ".")
                or path == normalized_prefix or path.startswith(normalized_prefix + "/"))
            and (glob is None or fnmatch.fnmatchcase(path, glob)
                 or fnmatch.fnmatchcase(PurePosixPath(path).name, glob))
        ]
        cap = self._cap(limit)
        shown = candidates[:cap]
        items = tuple(SourceItem(path, None, None, "", self._scope.revision) for path in shown)
        return self._observation(
            "list_paths",
            arguments,
            items,
            examined=len(self._all_paths()),
            omitted=len(candidates) - len(shown),
            coverage="all allowed paths at the exact revision",
        )

    # ---------------------------------------------------------------- search
    def search(
        self,
        pattern: str,
        *,
        regex: bool = False,
        path_glob: str | None = None,
        case_sensitive: bool = True,
        limit: int | None = None,
    ) -> SourceObservation:
        _bounded_text(pattern, "search pattern")
        if path_glob is not None:
            _bounded_text(path_glob, "path glob")
        arguments = {
            "pattern": pattern,
            "regex": regex,
            "path_glob": path_glob,
            "case_sensitive": case_sensitive,
        }
        command = ["grep", "-n", "-I", "--no-color", "--full-name"]
        command.append("-E" if regex else "-F")
        if not case_sensitive:
            command.append("-i")
        command.extend(["-e", pattern, self._scope.revision, "--"])
        pathspecs = self._pathspecs(path_glob)
        command.extend(pathspecs)
        try:
            output = self._git(*command, ok_codes=(0, 1))
        except DomainError as error:
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "search pattern is invalid") from error
        prefix = f"{self._scope.revision}:"
        matches: list[SourceItem] = []
        for line in output.splitlines():
            if not line.startswith(prefix):
                continue
            remainder = line[len(prefix):]
            try:
                path, number, text = remainder.split(":", 2)
                line_number = int(number)
            except ValueError:
                continue
            if not self._scope.allows(path):
                continue
            matches.append(SourceItem(path, line_number, line_number, text, self._scope.revision))
        cap = self._cap(limit)
        shown = tuple(matches[:cap])
        files = sorted({item.path for item in matches})
        return self._observation(
            "search",
            arguments,
            shown,
            examined=len(self._allowed_for_glob(path_glob)),
            omitted=len(matches) - len(shown),
            coverage=(
                "all allowed text files matching the path glob at the exact revision"
                if path_glob
                else "all allowed text files at the exact revision"
            ),
            notes=(f"matched files: {len(files)}",),
        )

    # ------------------------------------------------------------------ read
    def read(
        self, path: str, *, start_line: int = 1, end_line: int | None = None
    ) -> SourceObservation:
        normalized = self._checked_path(path)
        if start_line < 1 or (end_line is not None and end_line < start_line):
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "line range is invalid")
        raw = self._git_bytes("show", f"{self._scope.revision}:{normalized}")
        if b"\0" in raw[:8000]:
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "binary files cannot be read as text")
        if len(raw) > self._scope.max_file_bytes:
            notes = (f"file has {len(raw)} bytes; only the requested line range is returned",)
        else:
            notes = ()
        lines = raw.decode("utf-8", errors="replace").splitlines()
        total = len(lines)
        last = total if end_line is None else min(end_line, total)
        selected: list[str] = []
        size = 0
        actual_end = start_line - 1
        for number in range(start_line, last + 1):
            line = lines[number - 1]
            size += len(line.encode("utf-8")) + 1
            if size > self._scope.max_output_bytes:
                break
            selected.append(line)
            actual_end = number
        items: tuple[SourceItem, ...] = ()
        if selected:
            items = (
                SourceItem(normalized, start_line, actual_end, "\n".join(selected), self._scope.revision),
            )
        omitted = max(0, last - actual_end)
        return self._observation(
            "read",
            {"path": normalized, "start_line": start_line, "end_line": end_line},
            items,
            examined=1,
            omitted=omitted,
            coverage=f"lines {start_line}-{actual_end} of {total}",
            notes=notes + ((f"{omitted} requested lines not returned (output limit)",) if omitted else ()),
        )

    # ------------------------------------------------------------------- log
    def log(self, *, path: str | None = None, limit: int | None = None) -> SourceObservation:
        cap = self._cap(limit)
        command = [
            "log",
            "--no-color",
            f"--max-count={cap + 1}",
            "--format=%H%x1f%ad%x1f%an%x1f%s",
            "--date=iso-strict",
            self._scope.revision,
        ]
        arguments: dict[str, object] = {"path": None}
        if path is not None:
            normalized = self._checked_path(path)
            command.extend(["--", normalized])
            arguments["path"] = normalized
        output = self._git(*command)
        records = [line.split("\x1f") for line in output.splitlines() if line]
        shown = records[:cap]
        items = tuple(
            SourceItem(
                arguments["path"] or ".",
                None,
                None,
                f"{commit} {date} {author}: {subject}",
                self._scope.revision,
            )
            for commit, date, author, subject in shown
        )
        return self._observation(
            "log",
            arguments,
            items,
            examined=len(shown),
            omitted=1 if len(records) > cap else 0,
            coverage="history reachable from the exact revision",
        )

    # ----------------------------------------------------------------- blame
    def blame(self, path: str, *, start_line: int, end_line: int) -> SourceObservation:
        normalized = self._checked_path(path)
        if start_line < 1 or end_line < start_line or end_line - start_line >= self._scope.max_items:
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "blame line range is invalid or too large")
        output = self._git(
            "blame", "--porcelain", "-L", f"{start_line},{end_line}", self._scope.revision, "--", normalized
        )
        items: list[SourceItem] = []
        commit = ""
        summaries: dict[str, str] = {}
        final_line = 0
        for line in output.splitlines():
            header = re.match(r"^([0-9a-f]{40}) \d+ (\d+)", line)
            if header:
                commit, final_line = header.group(1), int(header.group(2))
            elif line.startswith("summary "):
                summaries[commit] = line[len("summary "):]
            elif line.startswith("\t"):
                items.append(
                    SourceItem(
                        normalized,
                        final_line,
                        final_line,
                        f"{commit[:12]} {summaries.get(commit, '')}: {line[1:]}",
                        self._scope.revision,
                    )
                )
        return self._observation(
            "blame",
            {"path": normalized, "start_line": start_line, "end_line": end_line},
            tuple(items),
            examined=len(items),
            coverage="blame at the exact revision",
        )

    # --------------------------------------------------------------- helpers
    def _observation(
        self,
        operation: str,
        arguments: Mapping[str, object],
        items: tuple[SourceItem, ...],
        *,
        examined: int,
        coverage: str,
        omitted: int = 0,
        notes: Sequence[str] = (),
    ) -> SourceObservation:
        if omitted:
            status = ObservationStatus.PARTIAL
        elif items:
            status = ObservationStatus.COMPLETE
        else:
            status = ObservationStatus.EMPTY
        return SourceObservation(
            operation=operation,
            arguments=dict(arguments),
            revision=self._scope.revision,
            status=status,
            items=items,
            coverage=coverage,
            examined_count=examined,
            omitted_count=omitted,
            notes=tuple(notes),
        )

    def _cap(self, limit: int | None) -> int:
        if limit is None:
            return self._scope.max_items
        if limit < 1:
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "limit must be positive")
        return min(limit, self._scope.max_items)

    def _all_paths(self) -> tuple[str, ...]:
        if self._paths is None:
            output = self._git("ls-tree", "-r", "--name-only", "-z", self._scope.revision)
            self._paths = tuple(
                sorted(path for path in output.split("\0") if path and self._scope.allows(path))
            )
        return self._paths

    def _allowed_for_glob(self, path_glob: str | None) -> tuple[str, ...]:
        if path_glob is None:
            return self._all_paths()
        return tuple(
            path
            for path in self._all_paths()
            if fnmatch.fnmatchcase(path, path_glob)
            or fnmatch.fnmatchcase(PurePosixPath(path).name, path_glob)
        )

    def _pathspecs(self, path_glob: str | None) -> list[str]:
        specs: list[str] = []
        if self._scope.include_prefixes:
            specs.extend(
                ":(top)" + prefix.rstrip("/")
                for prefix in self._scope.include_prefixes
                if prefix.rstrip("/") not in ("", ".")
            )
        if path_glob is not None:
            glob = path_glob if "/" in path_glob else f"**/{path_glob}"
            specs.append(f":(top,glob){glob}")
        specs.extend(
            ":(top,exclude)" + prefix.rstrip("/")
            for prefix in self._scope.exclude_prefixes
            if prefix.rstrip("/") not in ("", ".")
        )
        return specs

    def _checked_path(self, path: str) -> str:
        normalized = _normalize(path)
        if not self._scope.allows(normalized):
            raise DomainError(ErrorCode.SOURCE_TARGET_OUT_OF_SCOPE, "path is outside the read scope")
        if normalized not in set(self._all_paths()):
            raise DomainError(ErrorCode.SOURCE_TARGET_NOT_FOUND, "path does not exist at the exact revision")
        return normalized

    def _git(self, *arguments: str, ok_codes: tuple[int, ...] = (0,)) -> str:
        return self._git_bytes(*arguments, ok_codes=ok_codes).decode("utf-8", errors="replace")

    def _git_bytes(self, *arguments: str, ok_codes: tuple[int, ...] = (0,)) -> bytes:
        try:
            completed = subprocess.run(
                ["git", "-C", str(self._root), "-c", "core.quotepath=off", *arguments],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=_GIT_TIMEOUT_SECONDS,
                check=False,
                env=_git_environment(),
            )
        except subprocess.TimeoutExpired as error:
            raise DomainError(ErrorCode.SOURCE_OPERATION_FAILED, "git operation timed out") from error
        if completed.returncode not in ok_codes:
            raise DomainError(ErrorCode.SOURCE_OPERATION_FAILED, "git operation failed")
        return completed.stdout


def _git_environment() -> dict[str, str]:
    environment = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("GIT_") or key in {"GIT_EXEC_PATH"}
    }
    environment.update({"GIT_TERMINAL_PROMPT": "0", "GIT_OPTIONAL_LOCKS": "0"})
    return environment


def _bounded_text(value: str, label: str) -> str:
    if not isinstance(value, str) or not value or len(value) > _MAX_PATTERN_LENGTH or "\0" in value:
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} must be non-empty and bounded")
    return value


def _normalize(path: str, *, allow_root: bool = False) -> str:
    if not isinstance(path, str) or not path or "\0" in path or "\\" in path:
        raise DomainError(ErrorCode.INVALID_ARGUMENT, "path must be a non-empty POSIX path")
    candidate = PurePosixPath(path)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise DomainError(ErrorCode.SOURCE_TARGET_OUT_OF_SCOPE, "path must stay inside the repository")
    normalized = candidate.as_posix()
    if normalized == "." and not allow_root:
        raise DomainError(ErrorCode.INVALID_ARGUMENT, "path must name a file")
    return normalized
