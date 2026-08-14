"""Product-owned loopback entry for dynamic World Model Read Sets.

The trusted process may read the sealed Catalog and an authority database for
startup checks and post-result Citation materialization.  A question execution
receives only one verified no-payload Read Set plus the original question; it
cannot select a Source, update a Workspace, or fall back to Direct Investigation.
"""

from __future__ import annotations

import argparse
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import secrets
import sqlite3
import stat
import sys
import threading
from typing import Mapping, Protocol, Sequence
from urllib.parse import quote
from wsgiref.simple_server import WSGIRequestHandler, make_server

from software_world_model.application_services.read_set_catalog import (
    ReadSetCatalog,
    ReadSetCatalogPointer,
    ReadSetFileRole,
    ReadSetRegistration,
)
from software_world_model.cross_cutting import Digest, canonical_json_bytes, digest_of
from software_world_model.infrastructure.file_read_set_catalog import (
    FileReadSetCatalogStore,
    RootedStructureReadBundleStore,
)
from software_world_model.interface.world_model_browser import (
    PublicRunnerError,
    WorldModelBrowserApplication,
)
from software_world_model.knowledge_engine.structure import (
    JAVA_SOURCE_SEMANTICS_PROFILE_REF,
    JAVA_STATIC_CALL_PROFILE_REF,
    MAVEN_STRUCTURE_PROFILE_REF,
)


_REQUEST_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,159}$")
_RESULT_ID = re.compile(r"^structure_view_result_[0-9a-f]{32}$")
_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
_COMMIT = re.compile(r"^[0-9a-f]{40}$")
_DISPATCH_POLICIES = frozenset(
    {
        "ONE_CALL_PER_QUESTION_NO_HIDDEN_RETRY",
        "THREE_ORDERED_CALLS_PER_QUESTION_NO_HIDDEN_RETRY",
        "FOUR_TO_SIX_ORDERED_CALLS_PER_QUESTION_NO_HIDDEN_RETRY",
    }
)
_REQUIRED_AUTHORITY_TABLES = {
    "app_maven_workspace_attempts": (
        "attempt_id",
        "workspace_id",
        "repository_revision",
        "state",
        "revision",
        "attempt_digest",
    ),
    "app_maven_workspace_step_events": (
        "event_id",
        "attempt_id",
        "sequence",
        "step_name",
        "outcome",
        "reference_id",
        "reference_digest",
        "error_code",
        "event_digest",
    ),
    "app_maven_workspace_versions": (
        "version_id",
        "workspace_id",
        "repository_revision",
        "snapshot_id",
        "availability",
        "single_read_set_id",
        "comparison_read_set_id",
        "revision",
        "version_digest",
    ),
    "app_maven_read_set_registrations": (
        "read_set_id",
        "workspace_id",
        "registration_digest",
    ),
    "app_read_set_catalog_publications": (
        "catalog_id",
        "revision",
        "catalog_digest",
        "entry_set_digest",
        "publication_digest",
    ),
    "app_structure_read_bundle_receipts": (
        "receipt_id",
        "bundle_kind",
        "scope_id",
        "session_id",
        "read_set_digest",
        "bundle_digest",
        "file_digest",
        "receipt_digest",
    ),
    "knw_structure_snapshot_roots": (
        "scope_id",
        "current_snapshot_id",
        "current_revision",
    ),
    "src_operation_roots": (
        "operation_id",
        "current_revision",
        "current_status",
        "source_id",
        "binding_id",
    ),
    "src_operation_revisions": (
        "operation_id",
        "revision",
        "status",
        "observation_id",
        "failure_code",
        "result_digest",
    ),
}


@dataclass(frozen=True, slots=True)
class AuthorityState:
    """Read-only fence proving that a question did not mutate update truth."""

    digest: Digest
    update_attempt_count: int
    bundle_receipt_count: int
    source_operation_revision_count: int
    current_snapshot_count: int

    def public_value(self) -> dict[str, object]:
        return {
            "digest": self.digest.value,
            "update_attempt_count": self.update_attempt_count,
            "bundle_receipt_count": self.bundle_receipt_count,
            "source_operation_revision_count": self.source_operation_revision_count,
            "current_snapshot_count": self.current_snapshot_count,
        }


class AuthorityStateProbe(Protocol):
    def capture(self) -> AuthorityState: ...


@dataclass(frozen=True, slots=True)
class ResolvedReadSetInput:
    """Exact application input passed to the isolated execution boundary."""

    registration: ReadSetRegistration
    catalog_pointer: ReadSetCatalogPointer
    ordered_bundle: Path
    snapshot_bundles: tuple[Path, ...]

    def require_valid(self) -> None:
        self.registration.require_valid()
        self.catalog_pointer.require_valid()
        if len(self.snapshot_bundles) != len(self.registration.snapshot_bindings):
            raise ValueError("resolved Read Set Snapshot file count is invalid")
        for path in (self.ordered_bundle, *self.snapshot_bundles):
            if not path.is_absolute() or not path.is_file() or path.is_symlink():
                raise ValueError("resolved Read Set file is not canonical")


class WorldModelQuestionExecutor(Protocol):
    """Trusted process boundary; implementations must isolate all three roles."""

    def health(self) -> Mapping[str, object]: ...

    def execute(
        self,
        *,
        request_id: str,
        read_set: ResolvedReadSetInput,
        question: str,
    ) -> Mapping[str, object]: ...

    def citation(
        self,
        *,
        request_id: str,
        result_id: str,
    ) -> Mapping[str, object]: ...


@dataclass(frozen=True, slots=True)
class _RequestRecord:
    read_set_id: str
    result_ids: frozenset[str]


class SqliteAuthorityStateProbe:
    """Capture selected owner state through a read-only SQLite connection."""

    def __init__(self, database: str | Path) -> None:
        supplied = Path(database)
        lexical = supplied if supplied.is_absolute() else Path.cwd() / supplied
        path = lexical.resolve(strict=True)
        if path != lexical or not path.is_file() or lexical.is_symlink():
            raise ValueError("authority database must be a canonical regular file")
        self.database = path

    def capture(self) -> AuthorityState:
        uri = f"file:{quote(str(self.database), safe='/')}?mode=ro"
        try:
            with closing(
                sqlite3.connect(uri, uri=True, timeout=5.0)
            ) as connection:
                connection.row_factory = sqlite3.Row
                connection.execute("PRAGMA query_only = ON")
                present = {
                    str(row[0])
                    for row in connection.execute(
                        "SELECT name FROM sqlite_master WHERE type = 'table'"
                    ).fetchall()
                }
                missing = sorted(set(_REQUIRED_AUTHORITY_TABLES) - present)
                if missing:
                    raise ValueError(
                        f"authority database is missing required tables: {missing}"
                    )
                tables: dict[str, object] = {}
                counts: dict[str, int] = {}
                for table, columns in sorted(_REQUIRED_AUTHORITY_TABLES.items()):
                    projection = ", ".join(columns)
                    order = ", ".join(columns[:2])
                    rows = connection.execute(
                        f"SELECT {projection} FROM {table} ORDER BY {order}"
                    ).fetchall()
                    counts[table] = len(rows)
                    tables[table] = tuple(
                        {column: row[column] for column in columns} for row in rows
                    )
        except sqlite3.Error as exc:
            raise RuntimeError("authority database read-only fence failed") from exc
        return AuthorityState(
            digest=digest_of(["SWM-WORLD-MODEL-AUTHORITY-FENCE@1", tables]),
            update_attempt_count=counts["app_maven_workspace_attempts"],
            bundle_receipt_count=counts["app_structure_read_bundle_receipts"],
            source_operation_revision_count=counts["src_operation_revisions"],
            current_snapshot_count=counts["knw_structure_snapshot_roots"],
        )


class DynamicCatalogWorldModelRunner:
    """Expose verified dynamic Catalog entries without granting update access."""

    def __init__(
        self,
        *,
        catalog_store: FileReadSetCatalogStore,
        bundle_store: RootedStructureReadBundleStore,
        executor: WorldModelQuestionExecutor,
        authority_probe: AuthorityStateProbe,
    ) -> None:
        self._catalog_store = catalog_store
        self._bundle_store = bundle_store
        self._executor = executor
        self._authority_probe = authority_probe
        self._lock = threading.Lock()
        self._records: dict[str, _RequestRecord | None] = {}
        self._health = self._validated_health(executor.health())
        pointer, catalog = self._read_current_catalog()
        if not catalog.entries:
            raise ValueError("dynamic Read Set Catalog must contain a queryable entry")
        self._startup_catalog_pointer = pointer

    def health(self) -> Mapping[str, object]:
        pointer, catalog = self._read_current_catalog()
        return {
            **self._health,
            "catalog_id": pointer.catalog_id.value,
            "catalog_revision": pointer.revision.value,
            "catalog_digest": pointer.catalog_digest.value,
            "read_set_count": len(catalog.entries),
            "selector_field": "read_set_id",
            "question_authority": "READ_ONLY_NO_UPDATE_NO_DIRECT_FALLBACK",
        }

    def datasets(self) -> tuple[Mapping[str, object], ...]:
        pointer, catalog = self._read_current_catalog()
        return tuple(self._dataset(pointer, item) for item in catalog.entries)

    def ask(
        self,
        *,
        request_id: str,
        dataset_id: str,
        question: str,
    ) -> Mapping[str, object]:
        if not _REQUEST_ID.fullmatch(request_id):
            raise PublicRunnerError(
                "REQUEST_ID_INVALID", "request_id has an invalid format", status="400 Bad Request"
            )
        if (
            not question
            or question != question.strip()
            or "\x00" in question
            or len(question) > 8_000
        ):
            raise PublicRunnerError(
                "QUESTION_INVALID",
                "question must contain 1 to 8000 normalized characters",
                status="400 Bad Request",
            )
        with self._lock:
            if request_id in self._records:
                raise PublicRunnerError(
                    "REQUEST_ID_CONFLICT",
                    "request_id was already used and will not be replayed",
                    status="409 Conflict",
                )
            self._records[request_id] = None
            pointer, catalog = self._read_current_catalog()
            entry = next(
                (item for item in catalog.entries if item.read_set_id.value == dataset_id),
                None,
            )
            if entry is None:
                raise PublicRunnerError(
                    "READ_SET_NOT_FOUND",
                    "read_set_id is not present in the verified current Catalog",
                    status="404 Not Found",
                )
            resolved = self._resolve(pointer, entry)
            before = self._authority_probe.capture()
            execution_error: Exception | None = None
            raw_result: Mapping[str, object] | None = None
            try:
                raw_result = self._executor.execute(
                    request_id=request_id,
                    read_set=resolved,
                    question=question,
                )
            except Exception as exc:
                execution_error = exc
            after = self._authority_probe.capture()
            after_pointer, _ = self._read_current_catalog()
            if after != before or after_pointer != pointer:
                raise PublicRunnerError(
                    "QUESTION_MUTATED_AUTHORITY",
                    "update, CURRENT, Bundle, Catalog, or Source state changed during question execution",
                    status="409 Conflict",
                )
            if execution_error is not None:
                if isinstance(execution_error, PublicRunnerError):
                    raise execution_error
                raise PublicRunnerError(
                    "WORLD_MODEL_EXECUTION_FAILED",
                    "the isolated World Model run did not produce a verified result",
                ) from execution_error
            if raw_result is None:
                raise PublicRunnerError(
                    "WORLD_MODEL_EXECUTION_FAILED",
                    "the isolated World Model run returned no result",
                )
            result, result_ids = self._validated_result(
                raw_result,
                request_id=request_id,
                question=question,
                resolved=resolved,
                accepted_commit=str(self._health["evaluation_subject_commit"]),
                accepted_tree=str(self._health["evaluation_subject_tree"]),
            )
            result["authority_fence"] = {
                "before": before.public_value(),
                "after": after.public_value(),
                "unchanged": True,
            }
            result["read_set"] = self._dataset(pointer, entry)
            self._records[request_id] = _RequestRecord(
                read_set_id=dataset_id,
                result_ids=frozenset(result_ids),
            )
            return result

    def citation(
        self,
        *,
        request_id: str,
        result_id: str,
    ) -> Mapping[str, object]:
        record = self._records.get(request_id)
        if record is None:
            raise PublicRunnerError(
                "RESULT_NOT_FOUND",
                "request has no completed, verified result",
                status="404 Not Found",
            )
        if result_id not in record.result_ids:
            raise PublicRunnerError(
                "CITATION_BINDING_INVALID",
                "citation is not bound to this request and result",
                status="404 Not Found",
            )
        value = dict(
            self._executor.citation(request_id=request_id, result_id=result_id)
        )
        if (
            value.get("request_id") != request_id
            or value.get("result_id") != result_id
            or value.get("environment") != "EVALUATION_ONLY"
            or value.get("network_operation_count") != 0
            or value.get("answer_return_port") is not False
            or value.get("production_activation") != "NOT_EXECUTED"
            or not isinstance(value.get("citation_projection"), dict)
        ):
            raise PublicRunnerError(
                "CITATION_VERIFICATION_FAILED",
                "the independently projected citation failed verification",
                status="409 Conflict",
            )
        return value

    def _read_current_catalog(self) -> tuple[ReadSetCatalogPointer, ReadSetCatalog]:
        try:
            pointer = self._catalog_store.read_pointer()
            if pointer is None:
                raise ValueError("Read Set Catalog current pointer is missing")
            catalog = self._catalog_store.read_catalog(pointer, verify_files=True)
            catalog.require_valid()
            for entry in catalog.entries:
                profiles = {
                    coverage.profile_ref
                    for snapshot in entry.snapshot_bindings
                    for coverage in snapshot.coverages
                }
                if len(profiles) != 1 or not profiles.issubset(
                    {
                        MAVEN_STRUCTURE_PROFILE_REF,
                        JAVA_STATIC_CALL_PROFILE_REF,
                        JAVA_SOURCE_SEMANTICS_PROFILE_REF,
                    }
                ):
                    raise ValueError("Catalog contains an unsupported Structure Profile")
            return pointer, catalog
        except PublicRunnerError:
            raise
        except Exception as exc:
            raise PublicRunnerError(
                "READ_SET_CATALOG_INVALID",
                "the current Read Set Catalog or Bundle files failed verification",
                status="503 Service Unavailable",
            ) from exc

    def _resolve(
        self,
        pointer: ReadSetCatalogPointer,
        entry: ReadSetRegistration,
    ) -> ResolvedReadSetInput:
        ordered = [
            item for item in entry.file_manifest
            if item.role is ReadSetFileRole.ORDERED_ENVELOPE
        ]
        snapshots = sorted(
            (
                item for item in entry.file_manifest
                if item.role is ReadSetFileRole.SNAPSHOT
            ),
            key=lambda item: item.ordinal,
        )
        if len(ordered) != 1 or len(snapshots) != len(entry.snapshot_bindings):
            raise PublicRunnerError(
                "READ_SET_FILE_MANIFEST_INVALID",
                "verified Catalog entry has an invalid Bundle file layout",
                status="503 Service Unavailable",
            )
        value = ResolvedReadSetInput(
            registration=entry,
            catalog_pointer=pointer,
            ordered_bundle=self._bundle_path(ordered[0].locator),
            snapshot_bundles=tuple(
                self._bundle_path(item.locator) for item in snapshots
            ),
        )
        value.require_valid()
        return value

    def _bundle_path(self, locator: str) -> Path:
        candidate = self._bundle_store.root.joinpath(*locator.split("/"))
        resolved = candidate.resolve(strict=True)
        if (
            candidate != resolved
            or not resolved.is_file()
            or resolved.is_symlink()
            or not resolved.is_relative_to(self._bundle_store.root)
        ):
            raise ValueError("Catalog Bundle locator did not resolve to an exact file")
        return resolved

    @staticmethod
    def _validated_health(value: Mapping[str, object]) -> dict[str, object]:
        result = dict(value)
        commit = result.get("evaluation_subject_commit")
        tree = result.get("evaluation_subject_tree")
        digest_fields = (
            "evaluation_grant_digest",
            "deterministic_qualification_digest",
            "held_out_suite_digest",
            "independent_evaluator_digest",
            "startup_preflight_digest",
            "startup_receipt_digest",
            "stage_manifest_digest",
            "launcher_manifest_digest",
            "provider_subject_digest",
            "gateway_authorization_receipt_digest",
        )
        if (
            result.get("status") != "ready"
            or result.get("mode") != "WORLD_MODEL"
            or result.get("environment") != "EVALUATION_ONLY"
            or result.get("evaluation_subject_status") != "CANDIDATE"
            or result.get("production_activation") != "NOT_EXECUTED"
            or result.get("dispatch_policy") not in _DISPATCH_POLICIES
            or not isinstance(commit, str)
            or not _COMMIT.fullmatch(commit)
            or not isinstance(tree, str)
            or not _COMMIT.fullmatch(tree)
            or any(
                not isinstance(result.get(field), str)
                or not _DIGEST.fullmatch(str(result.get(field)))
                for field in digest_fields
            )
        ):
            raise ValueError("World Model executor did not pass its startup boundary")
        return result

    @staticmethod
    def _validated_result(
        value: Mapping[str, object],
        *,
        request_id: str,
        question: str,
        resolved: ResolvedReadSetInput,
        accepted_commit: str,
        accepted_tree: str,
    ) -> tuple[dict[str, object], tuple[str, ...]]:
        result = dict(value)
        entry = resolved.registration
        page = result.get("page")
        execution = result.get("execution")
        citations = result.get("citations")
        if not isinstance(page, dict) or not isinstance(execution, dict) or not isinstance(citations, list):
            raise PublicRunnerError(
                "WORLD_MODEL_RESULT_INVALID",
                "isolated execution returned an invalid public result",
            )
        snapshots = page.get("read_binding", {}).get("snapshots", [])
        observed_snapshot_ids = [
            item.get("snapshot_id") for item in snapshots if isinstance(item, dict)
        ]
        expected_snapshot_ids = [
            item.snapshot_id.value for item in entry.snapshot_bindings
        ]
        stages = page.get("authority_chain", {}).get("stages", [])
        selected = result.get("read_set_id", result.get("dataset_id"))
        profile_refs = tuple(
            sorted(
                {
                    coverage.profile_ref
                    for snapshot in entry.snapshot_bindings
                    for coverage in snapshot.coverages
                }
            )
        )
        expected_provider_calls = (
            3
            if profile_refs == (JAVA_SOURCE_SEMANTICS_PROFILE_REF,)
            else 1
        )
        if (
            result.get("request_id") != request_id
            or selected != entry.read_set_id.value
            or result.get("question") != question
            or result.get("mode") != "WORLD_MODEL"
            or result.get("environment") != "EVALUATION_ONLY"
            or result.get("evaluation_subject_status") != "CANDIDATE"
            or result.get("evaluation_subject_commit") != accepted_commit
            or result.get("evaluation_subject_tree") != accepted_tree
            or result.get("production_activation") != "NOT_EXECUTED"
            or page.get("mode") != "WORLD_MODEL"
            or page.get("environment") != "EVALUATION_ONLY"
            or page.get("evaluation_only") is not True
            or page.get("implementation_commit") != accepted_commit
            or page.get("request", {}).get("original_question") != question
            or page.get("read_binding", {}).get("read_set_digest")
            != entry.read_set_digest.value
            or observed_snapshot_ids != expected_snapshot_ids
            or not isinstance(stages, list)
            or len(stages) != 10
            or execution.get("attempt_count") != 1
            or execution.get("provider_call_count") != expected_provider_calls
            or execution.get("network_operation_count")
            != execution.get("provider_call_count")
            or execution.get("selective_retry_count") != 0
            or execution.get("source_access_count") != 0
            or execution.get("evidence_payload_access_count") != 0
        ):
            raise PublicRunnerError(
                "WORLD_MODEL_RESULT_INVALID",
                "isolated execution result violates the exact Read Set boundary",
            )
        result_ids: list[str] = []
        for item in citations:
            if not isinstance(item, dict):
                raise PublicRunnerError(
                    "WORLD_MODEL_RESULT_INVALID", "citation index is invalid"
                )
            result_id = item.get("result_id")
            if not isinstance(result_id, str) or not _RESULT_ID.fullmatch(result_id):
                raise PublicRunnerError(
                    "WORLD_MODEL_RESULT_INVALID", "citation Result ID is invalid"
                )
            for key in ("seal_digest", "projection_digest"):
                digest = item.get(key)
                if not isinstance(digest, str) or not _DIGEST.fullmatch(digest):
                    raise PublicRunnerError(
                        "WORLD_MODEL_RESULT_INVALID", "citation digest is invalid"
                    )
            result_ids.append(result_id)
        if len(set(result_ids)) != len(result_ids):
            raise PublicRunnerError(
                "WORLD_MODEL_RESULT_INVALID", "citation Result IDs are duplicated"
            )
        result.pop("dataset_id", None)
        result["read_set_id"] = entry.read_set_id.value
        result["catalog_binding"] = {
            "catalog_id": resolved.catalog_pointer.catalog_id.value,
            "revision": resolved.catalog_pointer.revision.value,
            "catalog_digest": resolved.catalog_pointer.catalog_digest.value,
            "registration_digest": entry.digest.value,
            "file_manifest_digest": entry.file_manifest_digest.value,
            "ordered_receipt_digest": entry.ordered_receipt.digest.value,
        }
        return result, tuple(result_ids)

    @staticmethod
    def _dataset(
        pointer: ReadSetCatalogPointer,
        entry: ReadSetRegistration,
    ) -> Mapping[str, object]:
        snapshots = entry.snapshot_bindings
        revisions = [item.source_revision for item in snapshots]
        snapshot_ids = [item.snapshot_id.value for item in snapshots]
        profiles = sorted(
            {
                coverage.profile_ref
                for snapshot in snapshots
                for coverage in snapshot.coverages
            }
        )
        schemas = sorted({item.schema_ref for item in snapshots})
        modality = "ORDERED_COMPARISON" if len(snapshots) == 2 else "EXACT_SNAPSHOT"
        java_profile = profiles == [JAVA_STATIC_CALL_PROFILE_REF]
        java_semantics_profile = profiles == [JAVA_SOURCE_SEMANTICS_PROFILE_REF]
        label = (
            f"{entry.workspace_id.value} · {revisions[0][:9]} → {revisions[-1][:9]}"
            if len(revisions) == 2
            else f"{entry.workspace_id.value} · {revisions[0][:9]}"
        )
        return {
            "id": entry.read_set_id.value,
            "read_set_id": entry.read_set_id.value,
            "label": label,
            "description": (
                (
                    "exact ordered Java source-semantics Snapshot comparison"
                    if len(snapshots) == 2
                    else "exact Java source-semantics Snapshot"
                )
                if java_semantics_profile
                else
                (
                    "exact ordered Java static-call Snapshot comparison"
                    if len(snapshots) == 2
                    else "exact Java static-call Snapshot"
                )
                if java_profile
                else (
                    "exact ordered Maven Structure Snapshot comparison"
                    if len(snapshots) == 2
                    else "exact Maven Structure Snapshot"
                )
            ),
            "workspace_id": entry.workspace_id.value,
            "workspace_version_ids": [
                item.value for item in entry.workspace_version_ids
            ],
            "scope_id": entry.scope_id.value,
            "snapshot_count": len(snapshot_ids),
            "snapshot_ids": snapshot_ids,
            "source_revisions": revisions,
            "profile_refs": profiles,
            "schema_refs": schemas,
            "coverage": (
                (
                    "Java declarations, frozen exact static CALLS, typed branch/"
                    "return/throw implementation atoms, and formal feature discovery; "
                    "unsupported Java constructs, runtime dispatch, reflection, "
                    "dependency injection, and design intent are outside Coverage"
                )
                if java_semantics_profile
                else
                (
                    "Java type and declared-method membership, frozen-subset static "
                    "CALLS, and exact ordered diff; runtime dispatch, reflection, "
                    "dependency injection, and design intent are outside Coverage"
                )
                if java_profile
                else (
                    "Maven reactor child membership, POM-local direct internal "
                    "dependencies, and exact ordered diff; plugins, properties, "
                    "Maven parent/effective/transitive/runtime relations are outside Coverage"
                )
            ),
            "modality": modality,
            "read_set_digest": entry.read_set_digest.value,
            "bundle_receipt_digest": entry.ordered_receipt.digest.value,
            "file_manifest_digest": entry.file_manifest_digest.value,
            "catalog_digest": pointer.catalog_digest.value,
            "read_only": True,
        }


class _LoopbackRequestHandler(WSGIRequestHandler):
    def setup(self) -> None:
        super().setup()
        self.connection.settimeout(300.0)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", required=True)
    parser.add_argument("--catalog-root", required=True)
    parser.add_argument("--bundle-root", required=True)
    parser.add_argument("--evaluation-grant", required=True)
    parser.add_argument("--session-root")
    parser.add_argument("--socket-root")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=55121)
    parser.add_argument("--timeout-seconds", type=float, default=240.0)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    if arguments.host != "127.0.0.1":
        raise ValueError("World Model evaluation service must bind 127.0.0.1")
    if not 1 <= arguments.port <= 65_535:
        raise ValueError("port must be in 1..65535")
    if arguments.timeout_seconds < 1:
        raise ValueError("timeout-seconds must be positive")
    # Imported lazily so catalog-only tests and tools never load the live
    # Provider execution implementation.
    from .world_model_runtime import SealedWorldModelExecutor

    token = secrets.token_hex(6)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    session_root = (
        Path(arguments.session_root)
        if arguments.session_root
        else Path("var/world-model/sessions") / f"{timestamp}-{token}"
    )
    socket_root = (
        Path(arguments.socket_root)
        if arguments.socket_root
        else Path("/private/tmp") / f"swm-{os.getpid()}-{token}"
    )
    bundle_store = RootedStructureReadBundleStore(arguments.bundle_root)
    catalog_store = FileReadSetCatalogStore(arguments.catalog_root, bundle_store)
    probe = SqliteAuthorityStateProbe(arguments.database)
    executor = SealedWorldModelExecutor.from_grant(
        grant_path=Path(arguments.evaluation_grant),
        authority_database=probe.database,
        session_root=session_root,
        socket_root=socket_root,
        timeout_seconds=arguments.timeout_seconds,
    )
    runner = DynamicCatalogWorldModelRunner(
        catalog_store=catalog_store,
        bundle_store=bundle_store,
        executor=executor,
        authority_probe=probe,
    )
    application = WorldModelBrowserApplication(
        runner,
        selector_field="read_set_id",
    )
    with make_server(
        arguments.host,
        arguments.port,
        application,
        handler_class=_LoopbackRequestHandler,
    ) as server:
        print(
            json.dumps(
                {
                    **runner.health(),
                    "url": f"http://{arguments.host}:{arguments.port}/",
                    "session_root": str(executor.session_root),
                },
                ensure_ascii=False,
                sort_keys=True,
            ),
            flush=True,
        )
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
    return 0


def _entrypoint(argv: Sequence[str] | None = None) -> int:
    try:
        return main(argv)
    except PublicRunnerError as exc:
        print(
            json.dumps(
                {
                    "error": exc.code,
                    "message": exc.message,
                    "production_activation": "NOT_EXECUTED",
                },
                ensure_ascii=False,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(_entrypoint())
