"""Bounded, read-only Local Git target resolution and source operations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import hashlib
from pathlib import PurePosixPath
import re
import subprocess
from typing import Callable, Mapping, Protocol

from software_world_model.cross_cutting import (
    CorrelationRef,
    Digest,
    DomainError,
    ErrorCode,
    IdempotencyKey,
    Revision,
    StableId,
    NullTelemetryRecorder,
    TelemetryMetric,
    TelemetryRecorder,
    digest_of,
)
from software_world_model.knowledge_engine import ScopeStateAssertion

from .configuration import BindingEligibilityAssertion, SourceConfigurationService


_FULL_OID = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
_SHORT_OID = re.compile(r"^[0-9a-fA-F]{4,39}$")


class TargetKind(str, Enum):
    REPOSITORY_REVISION = "REPOSITORY_REVISION"
    REVISION_COMPARISON = "REVISION_COMPARISON"
    SOURCE_PATH = "SOURCE_PATH"
    SYMBOL = "SYMBOL"
    # Kept as an input compatibility name. Resolution is language-neutral.
    JAVA_SYMBOL = "JAVA_SYMBOL"


class ResolutionOutcome(str, Enum):
    EXACT = "EXACT"
    NOT_FOUND = "NOT_FOUND"
    AMBIGUOUS = "AMBIGUOUS"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"
    UNSUPPORTED = "UNSUPPORTED"
    EXECUTION_FAILED = "EXECUTION_FAILED"


class SourceOperationStatus(str, Enum):
    PREPARED = "PREPARED"
    DISPATCHED = "DISPATCHED"
    COMPLETED = "COMPLETED"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
    BUDGET_EXHAUSTED = "BUDGET_EXHAUSTED"
    OUTCOME_UNKNOWN = "OUTCOME_UNKNOWN"
    CANCELED = "CANCELED"


class SourceTool(str, Enum):
    LIST = "local-git.list@1"
    SEARCH = "local-git.search@1"
    READ = "local-git.read@1"
    COMPARE = "local-git.compare@1"


@dataclass(frozen=True, slots=True)
class SourceTargetResolutionReceipt:
    receipt_id: StableId
    target_kind: TargetKind
    proposal_digest: Digest
    outcome: ResolutionOutcome
    canonical_identity: tuple[tuple[str, str], ...]
    display_label: str
    candidates: tuple[tuple[tuple[str, str], ...], ...]
    resolver_contract_version: str
    digest: Digest


@dataclass(frozen=True, slots=True)
class OperationBudget:
    max_calls: int
    max_items: int
    max_bytes: int

    def __post_init__(self) -> None:
        if min(self.max_calls, self.max_items, self.max_bytes) < 1:
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "source operation budgets must be positive")


@dataclass(frozen=True, slots=True)
class SourceOperationIntent:
    idempotency_key: IdempotencyKey
    causation_reference: str
    source_id: StableId
    source_revision: Revision
    binding_id: StableId
    binding_revision: Revision
    scope_assertion: ScopeStateAssertion
    binding_eligibility: BindingEligibilityAssertion
    tool: SourceTool
    parameters: tuple[tuple[str, str], ...]
    budget: OperationBudget
    classification: str
    correlation_ref: CorrelationRef

    @classmethod
    def create(
        cls,
        *,
        idempotency_key: IdempotencyKey,
        causation_reference: str,
        source_id: StableId,
        source_revision: Revision,
        binding_id: StableId,
        binding_revision: Revision,
        scope_assertion: ScopeStateAssertion,
        binding_eligibility: BindingEligibilityAssertion,
        tool: SourceTool,
        parameters: Mapping[str, str],
        budget: OperationBudget,
        classification: str,
        correlation_ref: CorrelationRef,
    ) -> "SourceOperationIntent":
        return cls(
            idempotency_key=idempotency_key,
            causation_reference=_text(causation_reference, "causation reference"),
            source_id=source_id,
            source_revision=source_revision,
            binding_id=binding_id,
            binding_revision=binding_revision,
            scope_assertion=scope_assertion,
            binding_eligibility=binding_eligibility,
            tool=tool,
            parameters=tuple(sorted((_text(k, "parameter key"), v) for k, v in parameters.items())),
            budget=budget,
            classification=_text(classification, "classification"),
            correlation_ref=correlation_ref,
        )

    @property
    def digest(self) -> Digest:
        # Assertion digests are the authority closure; transient read timestamps
        # are intentionally not duplicated into the operation identity.
        return digest_of(
            {
                "command": "SourceOperationIntent@1",
                "idempotency_key": self.idempotency_key.value,
                "causation_reference": self.causation_reference,
                "source_id": self.source_id.value,
                "source_revision": self.source_revision.value,
                "binding_id": self.binding_id.value,
                "binding_revision": self.binding_revision.value,
                "scope_assertion_digest": self.scope_assertion.digest.value,
                "binding_eligibility_digest": self.binding_eligibility.digest.value,
                "tool": self.tool.value,
                "parameters": self.parameters,
                "budget": self.budget,
                "classification": self.classification,
            }
        )


@dataclass(frozen=True, slots=True)
class SourceContext:
    context_id: StableId
    source_id: StableId
    source_revision: Revision
    repository_revision: str
    subject: str
    observed_at: datetime
    digest: Digest


@dataclass(frozen=True, slots=True)
class SourceArtifact:
    artifact_id: StableId
    artifact_kind: str
    payload_schema_version: str
    source_id: StableId
    source_revision: Revision
    source_context_id: StableId
    source_native_identity: str
    content_digest: Digest
    payload: bytes
    classification: str
    truncated: bool
    truncation_offset: int | None
    identity_digest: Digest


@dataclass(frozen=True, slots=True)
class SourceObservation:
    observation_id: StableId
    operation_id: StableId
    tool: SourceTool
    source_context: SourceContext
    artifacts: tuple[SourceArtifact, ...]
    item_count: int
    byte_count: int
    next_cursor: str | None
    has_more: bool
    coverage: tuple[tuple[str, str], ...]
    observed_at: datetime
    digest: Digest


@dataclass(frozen=True, slots=True)
class SourceOperationResult:
    operation_id: StableId
    revision: Revision
    status: SourceOperationStatus
    intent_digest: Digest
    observation: SourceObservation | None
    failure_code: str | None
    failure_message: str | None
    created_at: datetime
    revised_at: datetime
    digest: Digest


@dataclass(frozen=True, slots=True)
class ConnectorOutcome:
    repository_revision: str
    subject: str
    artifact_kind: str
    payload: bytes
    item_count: int
    total_bytes: int
    next_cursor: str | None
    has_more: bool
    truncated: bool
    truncation_offset: int | None
    coverage: tuple[tuple[str, str], ...]


class SourceOperationRepository(Protocol):
    def prepare(self, *, intent: SourceOperationIntent, occurred_at: datetime) -> SourceOperationResult: ...

    def mark_dispatched(
        self, *, operation_id: StableId, expected_revision: Revision, occurred_at: datetime
    ) -> SourceOperationResult: ...

    def complete(
        self,
        *,
        operation_id: StableId,
        expected_revision: Revision,
        status: SourceOperationStatus,
        outcome: ConnectorOutcome | None,
        classification: str,
        failure_code: str | None,
        failure_message: str | None,
        occurred_at: datetime,
    ) -> SourceOperationResult: ...

    def get(self, operation_id: StableId) -> SourceOperationResult: ...


class LocalGitConnector:
    """Runs a fixed argv allowlist against immutable Git objects only."""

    contract_version = "local-git-connector@1"

    def __init__(self, repository: str) -> None:
        self.repository = repository
        self._git("rev-parse", "--git-dir")

    def resolve_revision(self, proposal: str) -> str:
        proposal = _text(proposal, "revision proposal")
        if proposal.startswith("-"):
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "Git revision cannot be an option")
        if _SHORT_OID.fullmatch(proposal):
            raise DomainError(
                ErrorCode.SOURCE_TARGET_AMBIGUOUS,
                "abbreviated Git object IDs are not canonical targets",
            )
        resolved = self._git("rev-parse", "--verify", f"{proposal}^{{commit}}").strip()
        if not _FULL_OID.fullmatch(resolved):
            raise DomainError(ErrorCode.SOURCE_TARGET_NOT_FOUND, "Git commit did not resolve exactly")
        return resolved

    def list_paths(self, revision: str) -> tuple[str, ...]:
        exact = self.resolve_revision(revision)
        payload = self._git_bytes("ls-tree", "-r", "--name-only", "-z", exact)
        return tuple(sorted(item.decode("utf-8") for item in payload.split(b"\0") if item))

    def read_path(self, revision: str, path: str) -> bytes:
        exact = self.resolve_revision(revision)
        normalized = _path(path)
        try:
            return self._git_bytes("show", f"{exact}:{normalized}")
        except DomainError as exc:
            raise DomainError(ErrorCode.SOURCE_TARGET_NOT_FOUND, "path does not exist at revision") from exc

    def execute(
        self,
        *,
        tool: SourceTool,
        parameters: Mapping[str, str],
        allowed_paths: tuple[str, ...],
        budget: OperationBudget,
    ) -> ConnectorOutcome:
        if budget.max_calls < 1:
            raise DomainError(ErrorCode.BUDGET_EXHAUSTED, "source call budget is exhausted")
        revision = self.resolve_revision(parameters.get("revision", ""))
        if tool is SourceTool.LIST:
            paths = tuple(path for path in self.list_paths(revision) if _allowed(path, allowed_paths))
            return self._paged_text_outcome(
                revision, "repository-tree", "LOCAL_GIT_PATH_LIST@1", paths, parameters, budget
            )
        if tool is SourceTool.SEARCH:
            query = _text(parameters.get("query", ""), "search query")
            matches: list[str] = []
            for path in self.list_paths(revision):
                if not _allowed(path, allowed_paths):
                    continue
                raw = self.read_path(revision, path)
                try:
                    content = raw.decode("utf-8")
                except UnicodeDecodeError:
                    continue
                for line_number, line in enumerate(content.splitlines(), 1):
                    if query in line:
                        matches.append(f"{path}:{line_number}:{line}")
            return self._paged_text_outcome(
                revision, f"search:{query}", "LOCAL_GIT_SEARCH_RESULT@1", tuple(matches), parameters, budget
            )
        if tool is SourceTool.READ:
            path = _path(parameters.get("path", ""))
            if not _allowed(path, allowed_paths):
                raise DomainError(ErrorCode.SOURCE_TARGET_OUT_OF_SCOPE, "path is outside binding selector")
            raw = self.read_path(revision, path)
            offset = _nonnegative_int(parameters.get("offset", "0"), "offset")
            requested = _positive_int(
                parameters.get("max_bytes", str(budget.max_bytes)), "max_bytes"
            )
            limit = min(requested, budget.max_bytes)
            payload = raw[offset : offset + limit]
            truncated = offset + len(payload) < len(raw)
            return ConnectorOutcome(
                repository_revision=revision,
                subject=path,
                artifact_kind="LOCAL_GIT_FILE@1",
                payload=payload,
                item_count=1,
                total_bytes=len(raw),
                next_cursor=str(offset + len(payload)) if truncated else None,
                has_more=truncated,
                truncated=truncated,
                truncation_offset=offset + len(payload) if truncated else None,
                coverage=(
                    ("path", path),
                    ("range", f"bytes:{offset}-{offset + len(payload)}"),
                    ("revision", revision),
                ),
            )
        if tool is SourceTool.COMPARE:
            base = self.resolve_revision(parameters.get("base", ""))
            path_args = self._pathspec_args(allowed_paths)
            raw = self._git_bytes("diff", "--no-ext-diff", "--unified=3", base, revision, *path_args)
            payload = raw[: budget.max_bytes]
            truncated = len(payload) < len(raw)
            return ConnectorOutcome(
                repository_revision=revision,
                subject=f"{base}..{revision}",
                artifact_kind="LOCAL_GIT_DIFF@1",
                payload=payload,
                item_count=1,
                total_bytes=len(raw),
                next_cursor=None,
                has_more=False,
                truncated=truncated,
                truncation_offset=len(payload) if truncated else None,
                coverage=(
                    ("base", base),
                    ("target", revision),
                    ("paths", ",".join(allowed_paths)),
                ),
            )
        raise DomainError(ErrorCode.PROVIDER_CONTRACT_UNAVAILABLE, "unsupported Local Git tool")

    def _paged_text_outcome(
        self,
        revision: str,
        subject: str,
        kind: str,
        items: tuple[str, ...],
        parameters: Mapping[str, str],
        budget: OperationBudget,
    ) -> ConnectorOutcome:
        cursor = _nonnegative_int(parameters.get("cursor", "0"), "cursor")
        requested_page = _positive_int(
            parameters.get("page_size", str(budget.max_items)), "page_size"
        )
        page_size = min(requested_page, budget.max_items)
        selected: list[str] = []
        byte_count = 0
        truncated_by_bytes = False
        for item in items[cursor : cursor + page_size]:
            encoded = (item + "\n").encode("utf-8")
            if byte_count + len(encoded) > budget.max_bytes:
                truncated_by_bytes = True
                break
            selected.append(item)
            byte_count += len(encoded)
        next_index = cursor + len(selected)
        has_more = next_index < len(items)
        payload = "\n".join(selected).encode("utf-8")
        return ConnectorOutcome(
            repository_revision=revision,
            subject=subject,
            artifact_kind=kind,
            payload=payload,
            item_count=len(selected),
            total_bytes=sum(len((item + "\n").encode("utf-8")) for item in items),
            next_cursor=str(next_index) if has_more else None,
            has_more=has_more,
            truncated=truncated_by_bytes,
            truncation_offset=len(payload) if truncated_by_bytes else None,
            coverage=(
                ("cursor_start", str(cursor)),
                ("cursor_end", str(next_index)),
                ("matched_total", str(len(items))),
                ("revision", revision),
            ),
        )

    def _pathspec_args(self, allowed_paths: tuple[str, ...]) -> tuple[str, ...]:
        if allowed_paths == (".",):
            return ()
        return ("--", *allowed_paths)

    def _git(self, *arguments: str) -> str:
        return self._git_bytes(*arguments).decode("utf-8", errors="strict")

    def _git_bytes(self, *arguments: str) -> bytes:
        try:
            process = subprocess.run(
                ("git", "-C", self.repository, *arguments),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=15,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise DomainError(
                ErrorCode.SOURCE_OPERATION_FAILED,
                "Local Git command timed out",
                {"timeout_seconds": 15},
            ) from exc
        if process.returncode != 0:
            diagnostic = process.stderr.decode("utf-8", errors="replace").strip()[:512]
            raise DomainError(
                ErrorCode.SOURCE_OPERATION_FAILED,
                "Local Git command failed",
                {"diagnostic": diagnostic},
            )
        return process.stdout


class LocalGitTargetResolver:
    resolver_contract_version = "local-git-target-resolver@1"

    def __init__(self, connector: LocalGitConnector) -> None:
        self._connector = connector

    def resolve_revision(self, proposal: str) -> SourceTargetResolutionReceipt:
        proposal_digest = digest_of({"kind": TargetKind.REPOSITORY_REVISION.value, "proposal": proposal})
        try:
            revision = self._connector.resolve_revision(proposal)
        except DomainError as exc:
            outcome = (
                ResolutionOutcome.AMBIGUOUS
                if exc.code is ErrorCode.SOURCE_TARGET_AMBIGUOUS
                else ResolutionOutcome.NOT_FOUND
            )
            return self._receipt(TargetKind.REPOSITORY_REVISION, proposal_digest, outcome, (), proposal, ())
        identity = (("revision", revision),)
        return self._receipt(
            TargetKind.REPOSITORY_REVISION, proposal_digest, ResolutionOutcome.EXACT, identity, revision, ()
        )

    def resolve_comparison(self, base: str, target: str) -> SourceTargetResolutionReceipt:
        proposal_digest = digest_of(
            {"kind": TargetKind.REVISION_COMPARISON.value, "base": base, "target": target}
        )
        try:
            exact_base = self._connector.resolve_revision(base)
            exact_target = self._connector.resolve_revision(target)
        except DomainError:
            return self._receipt(
                TargetKind.REVISION_COMPARISON,
                proposal_digest,
                ResolutionOutcome.NOT_FOUND,
                (),
                f"{base}..{target}",
                (),
            )
        identity = (("base", exact_base), ("target", exact_target))
        return self._receipt(
            TargetKind.REVISION_COMPARISON,
            proposal_digest,
            ResolutionOutcome.EXACT,
            identity,
            f"{exact_base}..{exact_target}",
            (),
        )

    def resolve_path(
        self, revision: str, proposal: str, *, allowed_paths: tuple[str, ...]
    ) -> SourceTargetResolutionReceipt:
        proposal_digest = digest_of(
            {"kind": TargetKind.SOURCE_PATH.value, "revision": revision, "proposal": proposal}
        )
        try:
            exact = self._connector.resolve_revision(revision)
            path = _path(proposal)
            if not _allowed(path, allowed_paths):
                return self._receipt(
                    TargetKind.SOURCE_PATH,
                    proposal_digest,
                    ResolutionOutcome.OUT_OF_SCOPE,
                    (),
                    proposal,
                    (),
                )
            self._connector.read_path(exact, path)
        except DomainError:
            return self._receipt(
                TargetKind.SOURCE_PATH, proposal_digest, ResolutionOutcome.NOT_FOUND, (), proposal, ()
            )
        identity = (("path", path), ("revision", exact))
        return self._receipt(
            TargetKind.SOURCE_PATH, proposal_digest, ResolutionOutcome.EXACT, identity, path, ()
        )

    def resolve_symbol(
        self,
        revision: str,
        proposal: str,
        *,
        allowed_paths: tuple[str, ...],
        max_files: int = 1000,
    ) -> SourceTargetResolutionReceipt:
        return self._resolve_symbol(
            revision,
            proposal,
            allowed_paths=allowed_paths,
            max_files=max_files,
            target_kind=TargetKind.SYMBOL,
        )

    def resolve_java_symbol(
        self,
        revision: str,
        proposal: str,
        *,
        allowed_paths: tuple[str, ...],
        max_files: int = 1000,
    ) -> SourceTargetResolutionReceipt:
        """Compatibility entry point backed by the language-neutral resolver."""

        return self._resolve_symbol(
            revision,
            proposal,
            allowed_paths=allowed_paths,
            max_files=max_files,
            target_kind=TargetKind.JAVA_SYMBOL,
        )

    def _resolve_symbol(
        self,
        revision: str,
        proposal: str,
        *,
        allowed_paths: tuple[str, ...],
        max_files: int,
        target_kind: TargetKind,
    ) -> SourceTargetResolutionReceipt:
        proposal = _text(proposal, "symbol proposal")
        proposal_digest = digest_of(
            {"kind": target_kind.value, "revision": revision, "proposal": proposal}
        )
        exact = self._connector.resolve_revision(revision)
        candidates: list[tuple[tuple[str, str], ...]] = []
        for path in self._connector.list_paths(exact)[:max_files]:
            if not _allowed(path, allowed_paths):
                continue
            try:
                source = self._connector.read_path(exact, path).decode("utf-8")
            except (DomainError, UnicodeDecodeError):
                continue
            for line_number, line in enumerate(source.splitlines(), 1):
                start = 0
                while (column := line.find(proposal, start)) >= 0:
                    candidates.append(
                        (
                            ("column", str(column + 1)),
                            ("line", str(line_number)),
                            ("path", path),
                            ("revision", exact),
                            ("symbol", proposal),
                        )
                    )
                    if len(candidates) > 20:
                        break
                    start = column + len(proposal)
                if len(candidates) > 20:
                    break
            if len(candidates) > 20:
                break
        if not candidates:
            outcome = ResolutionOutcome.NOT_FOUND
            identity: tuple[tuple[str, str], ...] = ()
        elif len(candidates) > 1:
            outcome = ResolutionOutcome.AMBIGUOUS
            identity = ()
        else:
            outcome = ResolutionOutcome.EXACT
            identity = candidates[0]
        return self._receipt(
            target_kind,
            proposal_digest,
            outcome,
            identity,
            proposal,
            tuple(candidates[:20]),
        )

    def _receipt(
        self,
        kind: TargetKind,
        proposal_digest: Digest,
        outcome: ResolutionOutcome,
        identity: tuple[tuple[str, str], ...],
        label: str,
        candidates: tuple[tuple[tuple[str, str], ...], ...],
    ) -> SourceTargetResolutionReceipt:
        core = {
            "target_kind": kind.value,
            "proposal_digest": proposal_digest.value,
            "outcome": outcome.value,
            "canonical_identity": identity,
            "candidates": candidates,
            "resolver_contract_version": self.resolver_contract_version,
        }
        digest = digest_of(core)
        return SourceTargetResolutionReceipt(
            receipt_id=StableId(f"target_receipt_{digest.value[-32:]}"),
            target_kind=kind,
            proposal_digest=proposal_digest,
            outcome=outcome,
            canonical_identity=identity,
            display_label=label,
            candidates=candidates,
            resolver_contract_version=self.resolver_contract_version,
            digest=digest,
        )


class SourceOperationService:
    def __init__(
        self,
        repository: SourceOperationRepository,
        configurations: SourceConfigurationService,
        *,
        clock: Callable[[], datetime] | None = None,
        telemetry: TelemetryRecorder | None = None,
    ) -> None:
        self._repository = repository
        self._configurations = configurations
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._telemetry = telemetry or NullTelemetryRecorder()

    def execute(self, intent: SourceOperationIntent) -> SourceOperationResult:
        prepared = self._repository.prepare(intent=intent, occurred_at=self._now())
        if prepared.status not in {SourceOperationStatus.PREPARED}:
            return self._record_telemetry(intent, prepared)
        if (
            intent.binding_eligibility.source_id != intent.source_id
            or intent.binding_eligibility.source_revision != intent.source_revision
            or intent.binding_eligibility.binding_id != intent.binding_id
            or intent.binding_eligibility.binding_revision != intent.binding_revision
            or intent.binding_eligibility.tool_id != intent.tool.value
        ):
            return self._record_telemetry(
                intent,
                self._fail(prepared, "ELIGIBILITY_MISMATCH", "intent authority closure mismatches"),
            )
        if not self._configurations.validate_binding_eligibility(
            intent.binding_eligibility, intent.scope_assertion
        ):
            return self._record_telemetry(
                intent,
                self._fail(prepared, "ELIGIBILITY_STALE", "binding eligibility is no longer valid"),
            )
        source = self._configurations.get_data_source(intent.source_id, intent.source_revision)
        connector = LocalGitConnector(source.canonical_source_target)
        dispatched = self._repository.mark_dispatched(
            operation_id=prepared.operation_id,
            expected_revision=prepared.revision,
            occurred_at=self._now(),
        )
        # This is the local dispatch fence: eligibility is checked after the
        # DISPATCHED record and immediately before the read-only process call.
        if not self._configurations.validate_binding_eligibility(
            intent.binding_eligibility, intent.scope_assertion
        ):
            return self._record_telemetry(
                intent,
                self._fail(dispatched, "ELIGIBILITY_STALE", "dispatch fence revalidation failed"),
            )
        try:
            outcome = connector.execute(
                tool=intent.tool,
                parameters=dict(intent.parameters),
                allowed_paths=_selector_paths(intent.binding_eligibility.selector),
                budget=intent.budget,
            )
        except DomainError as exc:
            failed = self._repository.complete(
                operation_id=dispatched.operation_id,
                expected_revision=dispatched.revision,
                status=SourceOperationStatus.FAILED,
                outcome=None,
                classification=intent.classification,
                failure_code=exc.code.value,
                failure_message=exc.message,
                occurred_at=self._now(),
            )
            return self._record_telemetry(intent, failed)
        status = (
            SourceOperationStatus.PARTIAL
            if outcome.has_more or outcome.truncated
            else SourceOperationStatus.COMPLETED
        )
        result = self._repository.complete(
            operation_id=dispatched.operation_id,
            expected_revision=dispatched.revision,
            status=status,
            outcome=outcome,
            classification=intent.classification,
            failure_code=None,
            failure_message=None,
            occurred_at=self._now(),
        )
        return self._record_telemetry(intent, result)

    def _record_telemetry(
        self, intent: SourceOperationIntent, result: SourceOperationResult
    ) -> SourceOperationResult:
        observation = result.observation
        metrics = ()
        if observation is not None:
            metrics = (
                TelemetryMetric("source_items", observation.item_count, "items"),
                TelemetryMetric("source_bytes", observation.byte_count, "bytes"),
            )
        self._telemetry.record(
            owner="source-integration",
            operation=intent.tool.value,
            outcome=result.status.value,
            correlation_reference=intent.correlation_ref.value,
            causation_reference=intent.causation_reference,
            authority_references=(result.operation_id.value, result.digest.value),
            metrics=metrics,
            classification=intent.classification,
        )
        return result

    def _fail(
        self, result: SourceOperationResult, code: str, message: str
    ) -> SourceOperationResult:
        return self._repository.complete(
            operation_id=result.operation_id,
            expected_revision=result.revision,
            status=SourceOperationStatus.FAILED,
            outcome=None,
            classification="INTERNAL",
            failure_code=code,
            failure_message=message,
            occurred_at=self._now(),
        )

    def _now(self) -> datetime:
        value = self._clock()
        if value.tzinfo is None or value.utcoffset() is None:
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "clock must return an aware datetime")
        return value.astimezone(timezone.utc)


def content_digest(payload: bytes) -> Digest:
    return Digest(f"sha256:{hashlib.sha256(payload).hexdigest()}")


def _selector_paths(selector: tuple[tuple[str, str], ...]) -> tuple[str, ...]:
    value = dict(selector).get("paths")
    if value is None:
        raise DomainError(ErrorCode.SELECTOR_INVALID, "binding has no path selector")
    return tuple(_path(item) for item in value.split(","))


def _allowed(path: str, allowed_paths: tuple[str, ...]) -> bool:
    return any(root == "." or path == root or path.startswith(root + "/") for root in allowed_paths)


def _path(value: str) -> str:
    clean = value.strip().replace("\\", "/")
    parsed = PurePosixPath(clean)
    if not clean or parsed.is_absolute() or ".." in parsed.parts:
        raise DomainError(ErrorCode.INVALID_ARGUMENT, "Git path must be repository-relative")
    return parsed.as_posix().rstrip("/") or "."


def _positive_int(value: str, label: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} must be an integer") from exc
    if parsed < 1:
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} must be positive")
    return parsed


def _nonnegative_int(value: str, label: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} must be an integer") from exc
    if parsed < 0:
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} cannot be negative")
    return parsed


def _text(value: str, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} must be non-empty")
    return value
