"""SQLite authority for Maven Workspaces and queryable Read Set registration."""

from __future__ import annotations

from datetime import datetime
import json
import sqlite3

from software_world_model.application_services.maven_workspace import (
    MavenWorkspace,
    MavenWorkspaceAttempt,
    MavenWorkspaceRepository,
    MavenWorkspaceVersion,
    WorkspaceAttemptState,
    WorkspaceStepEvent,
    WorkspaceStepName,
    WorkspaceStepOutcome,
    WorkspaceVersionAvailability,
    workspace_attempt_core,
)
from software_world_model.application_services.read_set_catalog import (
    CatalogPublication,
    ReadSetCatalogRepository,
    ReadSetRegistration,
    read_set_registration_from_document,
)
from software_world_model.cross_cutting import (
    Digest,
    DomainError,
    ErrorCode,
    IdGenerator,
    IdempotencyKey,
    Revision,
    StableId,
    Uuid4IdGenerator,
    canonical_json_bytes,
    digest_of,
)
from software_world_model.knowledge_engine.structure import (
    MAVEN_STRUCTURE_PROFILE_REF,
)

from .sqlite_database import SqliteDatabase


_SCHEMA = """
CREATE TABLE IF NOT EXISTS app_maven_workspaces (
    workspace_id TEXT PRIMARY KEY,
    idempotency_key TEXT NOT NULL UNIQUE,
    request_digest TEXT NOT NULL,
    canonical_system_key TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    repository_locator TEXT NOT NULL,
    root_pom TEXT NOT NULL,
    knowledge_profile_ref TEXT NOT NULL DEFAULT 'MAVEN_REACTOR_STRUCTURE@1',
    scope_id TEXT NOT NULL,
    scope_revision INTEGER NOT NULL,
    source_id TEXT NOT NULL,
    source_revision INTEGER NOT NULL,
    binding_id TEXT NOT NULL,
    binding_revision INTEGER NOT NULL,
    management_attempt_id TEXT NOT NULL,
    management_result_digest TEXT NOT NULL,
    created_at TEXT NOT NULL,
    workspace_digest TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS app_maven_workspace_attempts (
    attempt_id TEXT PRIMARY KEY,
    idempotency_key TEXT NOT NULL UNIQUE,
    request_digest TEXT NOT NULL,
    workspace_id TEXT NOT NULL,
    repository_revision TEXT NOT NULL,
    expected_current_snapshot_id TEXT,
    state TEXT NOT NULL CHECK (state IN (
        'RUNNING', 'FAILED', 'OUTCOME_PENDING', 'READ_BUNDLE_UNAVAILABLE',
        'CATALOG_UNAVAILABLE', 'SUCCEEDED'
    )),
    revision INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    revised_at TEXT NOT NULL,
    attempt_digest TEXT NOT NULL,
    FOREIGN KEY (workspace_id) REFERENCES app_maven_workspaces(workspace_id)
);

CREATE INDEX IF NOT EXISTS idx_maven_workspace_attempts_workspace
    ON app_maven_workspace_attempts(workspace_id, created_at, attempt_id);

CREATE TABLE IF NOT EXISTS app_maven_workspace_step_events (
    event_id TEXT PRIMARY KEY,
    attempt_id TEXT NOT NULL,
    sequence INTEGER NOT NULL,
    step_name TEXT NOT NULL,
    outcome TEXT NOT NULL,
    reference_id TEXT,
    reference_digest TEXT,
    error_code TEXT,
    error_message TEXT,
    occurred_at TEXT NOT NULL,
    event_digest TEXT NOT NULL,
    UNIQUE (attempt_id, sequence),
    FOREIGN KEY (attempt_id) REFERENCES app_maven_workspace_attempts(attempt_id)
);

CREATE TABLE IF NOT EXISTS app_maven_workspace_versions (
    version_id TEXT PRIMARY KEY,
    attempt_id TEXT NOT NULL UNIQUE,
    workspace_id TEXT NOT NULL,
    ordinal INTEGER NOT NULL,
    repository_revision TEXT NOT NULL,
    snapshot_id TEXT NOT NULL,
    snapshot_manifest_digest TEXT NOT NULL,
    availability TEXT NOT NULL CHECK (availability IN (
        'READ_BUNDLE_UNAVAILABLE', 'CATALOG_UNAVAILABLE', 'QUERYABLE'
    )),
    single_read_set_id TEXT,
    comparison_read_set_id TEXT,
    created_at TEXT NOT NULL,
    revision INTEGER NOT NULL,
    version_digest TEXT NOT NULL,
    UNIQUE (workspace_id, ordinal),
    UNIQUE (workspace_id, repository_revision),
    UNIQUE (workspace_id, snapshot_id),
    FOREIGN KEY (attempt_id) REFERENCES app_maven_workspace_attempts(attempt_id),
    FOREIGN KEY (workspace_id) REFERENCES app_maven_workspaces(workspace_id)
);

CREATE TABLE IF NOT EXISTS app_maven_read_set_registrations (
    read_set_id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    session_id TEXT NOT NULL UNIQUE,
    ordered_receipt_id TEXT NOT NULL UNIQUE,
    bundle_locator TEXT NOT NULL UNIQUE,
    registration_document BLOB NOT NULL,
    registration_digest TEXT NOT NULL,
    ordered_receipt_created_at TEXT NOT NULL,
    FOREIGN KEY (workspace_id) REFERENCES app_maven_workspaces(workspace_id)
);

CREATE INDEX IF NOT EXISTS idx_maven_read_sets_workspace
    ON app_maven_read_set_registrations(workspace_id, ordered_receipt_created_at, read_set_id);

CREATE TABLE IF NOT EXISTS app_read_set_catalog_identity (
    singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
    catalog_id TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS app_read_set_catalog_publications (
    catalog_id TEXT NOT NULL,
    revision INTEGER NOT NULL,
    catalog_digest TEXT NOT NULL,
    entry_set_digest TEXT NOT NULL,
    published_at TEXT NOT NULL,
    publication_digest TEXT NOT NULL,
    PRIMARY KEY (catalog_id, revision)
);
"""


class SqliteMavenWorkspaceRepository(MavenWorkspaceRepository, ReadSetCatalogRepository):
    def __init__(
        self,
        database: SqliteDatabase,
        *,
        id_generator: IdGenerator | None = None,
    ) -> None:
        self._database = database
        self._ids = id_generator or Uuid4IdGenerator()
        self._database.executescript(_SCHEMA)
        with self._database.transaction() as connection:
            columns = {
                row["name"]
                for row in connection.execute(
                    "PRAGMA table_info(app_maven_workspaces)"
                ).fetchall()
            }
            if "knowledge_profile_ref" not in columns:
                connection.execute(
                    "ALTER TABLE app_maven_workspaces "
                    "ADD COLUMN knowledge_profile_ref TEXT NOT NULL "
                    "DEFAULT 'MAVEN_REACTOR_STRUCTURE@1'"
                )

    def save_workspace(self, workspace: MavenWorkspace) -> MavenWorkspace:
        workspace.require_valid()
        try:
            with self._database.transaction() as connection:
                row = connection.execute(
                    "SELECT workspace_id, request_digest FROM app_maven_workspaces WHERE idempotency_key = ?",
                    (workspace.idempotency_key.value,),
                ).fetchone()
                if row is not None:
                    if row["request_digest"] != workspace.request_digest.value:
                        raise _idempotency("Workspace idempotency key has another request")
                    return self._load_workspace(connection, StableId(row["workspace_id"]))
                key_row = connection.execute(
                    "SELECT workspace_id, request_digest FROM app_maven_workspaces WHERE canonical_system_key = ?",
                    (workspace.canonical_system_key,),
                ).fetchone()
                if key_row is not None:
                    raise _invalid(
                        "MAVEN_WORKSPACE_SYSTEM_KEY_CONFLICT",
                        "canonical system key is already registered by another Workspace request",
                    )
                connection.execute(
                    """INSERT INTO app_maven_workspaces (
                           workspace_id, idempotency_key, request_digest,
                           canonical_system_key, display_name, repository_locator,
                           root_pom, knowledge_profile_ref, scope_id, scope_revision, source_id,
                           source_revision, binding_id, binding_revision,
                           management_attempt_id, management_result_digest,
                           created_at, workspace_digest
                       ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        workspace.workspace_id.value,
                        workspace.idempotency_key.value,
                        workspace.request_digest.value,
                        workspace.canonical_system_key,
                        workspace.display_name,
                        workspace.repository_locator,
                        workspace.root_pom,
                        workspace.knowledge_profile_ref,
                        workspace.scope_id.value,
                        workspace.scope_revision.value,
                        workspace.source_id.value,
                        workspace.source_revision.value,
                        workspace.binding_id.value,
                        workspace.binding_revision.value,
                        workspace.management_attempt_id.value,
                        workspace.management_result_digest.value,
                        _time(workspace.created_at),
                        workspace.digest.value,
                    ),
                )
                return self._load_workspace(connection, workspace.workspace_id)
        except DomainError:
            raise
        except sqlite3.IntegrityError as error:
            raise _inconsistent("Workspace persistence invariant was violated") from error

    def get_workspace(self, workspace_id: StableId) -> MavenWorkspace:
        with self._database.read() as connection:
            return self._load_workspace(connection, workspace_id)

    def list_workspaces(self) -> tuple[MavenWorkspace, ...]:
        with self._database.read() as connection:
            rows = connection.execute(
                "SELECT workspace_id FROM app_maven_workspaces ORDER BY created_at, workspace_id"
            ).fetchall()
            return tuple(self._load_workspace(connection, StableId(row["workspace_id"])) for row in rows)

    def prepare_attempt(
        self,
        *,
        attempt_id: StableId,
        idempotency_key: IdempotencyKey,
        request_digest: Digest,
        workspace_id: StableId,
        repository_revision: str,
        expected_current_snapshot_id: StableId | None,
        occurred_at: datetime,
    ) -> MavenWorkspaceAttempt:
        with self._database.transaction() as connection:
            existing = connection.execute(
                "SELECT attempt_id, request_digest FROM app_maven_workspace_attempts WHERE idempotency_key = ?",
                (idempotency_key.value,),
            ).fetchone()
            if existing is not None:
                if existing["request_digest"] != request_digest.value:
                    raise _idempotency("Workspace Update idempotency key has another request")
                return self._load_attempt(connection, StableId(existing["attempt_id"]))
            open_row = connection.execute(
                """SELECT attempt_id, state FROM app_maven_workspace_attempts
                   WHERE workspace_id = ? AND state IN (
                       'RUNNING', 'OUTCOME_PENDING', 'READ_BUNDLE_UNAVAILABLE',
                       'CATALOG_UNAVAILABLE'
                   ) ORDER BY created_at DESC LIMIT 1""",
                (workspace_id.value,),
            ).fetchone()
            if open_row is not None:
                raise DomainError(
                    ErrorCode.OPEN_PUBLICATION_ATTEMPT,
                    "Workspace has an unfinished Update Attempt; resume it before starting another",
                    {"attempt_id": open_row["attempt_id"]},
                )
            self._load_workspace(connection, workspace_id)
            latest_version = connection.execute(
                """SELECT snapshot_id FROM app_maven_workspace_versions
                   WHERE workspace_id = ? ORDER BY ordinal DESC LIMIT 1""",
                (workspace_id.value,),
            ).fetchone()
            actual_current = (
                StableId(latest_version["snapshot_id"])
                if latest_version is not None
                else None
            )
            if actual_current != expected_current_snapshot_id:
                raise DomainError(
                    ErrorCode.REVISION_CONFLICT,
                    "Workspace Version changed before Update Attempt preparation",
                    {"reason_code": "MAVEN_WORKSPACE_EXPECTED_CURRENT_STALE"},
                )
            value = _attempt(
                attempt_id=attempt_id,
                idempotency_key=idempotency_key,
                request_digest=request_digest,
                workspace_id=workspace_id,
                repository_revision=repository_revision,
                expected_current_snapshot_id=expected_current_snapshot_id,
                state=WorkspaceAttemptState.RUNNING,
                revision=Revision(1),
                created_at=occurred_at,
                revised_at=occurred_at,
                steps=(),
            )
            connection.execute(
                """INSERT INTO app_maven_workspace_attempts (
                       attempt_id, idempotency_key, request_digest, workspace_id,
                       repository_revision, expected_current_snapshot_id, state,
                       revision, created_at, revised_at, attempt_digest
                   ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    value.attempt_id.value,
                    value.idempotency_key.value,
                    value.request_digest.value,
                    value.workspace_id.value,
                    value.repository_revision,
                    value.expected_current_snapshot_id.value if value.expected_current_snapshot_id else None,
                    value.state.value,
                    value.revision.value,
                    _time(value.created_at),
                    _time(value.revised_at),
                    value.digest.value,
                ),
            )
            return self._load_attempt(connection, value.attempt_id)

    def get_attempt(self, attempt_id: StableId) -> MavenWorkspaceAttempt:
        with self._database.read() as connection:
            return self._load_attempt(connection, attempt_id)

    def find_attempt_by_idempotency_key(
        self, idempotency_key: IdempotencyKey
    ) -> MavenWorkspaceAttempt | None:
        with self._database.read() as connection:
            row = connection.execute(
                "SELECT attempt_id FROM app_maven_workspace_attempts WHERE idempotency_key = ?",
                (idempotency_key.value,),
            ).fetchone()
            return (
                self._load_attempt(connection, StableId(row["attempt_id"]))
                if row is not None
                else None
            )

    def transition_attempt(
        self,
        *,
        attempt_id: StableId,
        expected_revision: Revision,
        state: WorkspaceAttemptState,
        occurred_at: datetime,
    ) -> MavenWorkspaceAttempt:
        with self._database.transaction() as connection:
            current = self._load_attempt(connection, attempt_id)
            if current.revision != expected_revision:
                raise DomainError(ErrorCode.REVISION_CONFLICT, "Workspace Attempt revision changed")
            if current.state is WorkspaceAttemptState.SUCCEEDED and state is not current.state:
                raise _invalid("MAVEN_WORKSPACE_ATTEMPT_FINAL", "successful Workspace Attempt is final")
            value = _attempt(
                attempt_id=current.attempt_id,
                idempotency_key=current.idempotency_key,
                request_digest=current.request_digest,
                workspace_id=current.workspace_id,
                repository_revision=current.repository_revision,
                expected_current_snapshot_id=current.expected_current_snapshot_id,
                state=state,
                revision=current.revision.next(),
                created_at=current.created_at,
                revised_at=occurred_at,
                steps=current.steps,
            )
            changed = connection.execute(
                """UPDATE app_maven_workspace_attempts
                   SET state = ?, revision = ?, revised_at = ?, attempt_digest = ?
                   WHERE attempt_id = ? AND revision = ?""",
                (
                    value.state.value,
                    value.revision.value,
                    _time(value.revised_at),
                    value.digest.value,
                    value.attempt_id.value,
                    expected_revision.value,
                ),
            ).rowcount
            if changed != 1:
                raise DomainError(ErrorCode.REVISION_CONFLICT, "Workspace Attempt CAS failed")
            return self._load_attempt(connection, attempt_id)

    def append_step(
        self,
        *,
        attempt_id: StableId,
        name: WorkspaceStepName,
        outcome: WorkspaceStepOutcome,
        reference_id: str | None,
        reference_digest: Digest | None,
        error_code: str | None,
        error_message: str | None,
        occurred_at: datetime,
    ) -> MavenWorkspaceAttempt:
        with self._database.transaction() as connection:
            current = self._load_attempt(connection, attempt_id)
            event = WorkspaceStepEvent.create(
                event_id=self._ids.new("workspace_step"),
                attempt_id=attempt_id,
                sequence=len(current.steps) + 1,
                name=name,
                outcome=outcome,
                reference_id=reference_id,
                reference_digest=reference_digest,
                error_code=error_code,
                error_message=error_message,
                occurred_at=occurred_at,
            )
            connection.execute(
                """INSERT INTO app_maven_workspace_step_events (
                       event_id, attempt_id, sequence, step_name, outcome,
                       reference_id, reference_digest, error_code, error_message,
                       occurred_at, event_digest
                   ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    event.event_id.value,
                    event.attempt_id.value,
                    event.sequence,
                    event.name.value,
                    event.outcome.value,
                    event.reference_id,
                    event.reference_digest.value if event.reference_digest else None,
                    event.error_code,
                    event.error_message,
                    _time(event.occurred_at),
                    event.digest.value,
                ),
            )
            value = _attempt(
                attempt_id=current.attempt_id,
                idempotency_key=current.idempotency_key,
                request_digest=current.request_digest,
                workspace_id=current.workspace_id,
                repository_revision=current.repository_revision,
                expected_current_snapshot_id=current.expected_current_snapshot_id,
                state=current.state,
                revision=current.revision.next(),
                created_at=current.created_at,
                revised_at=occurred_at,
                steps=(*current.steps, event),
            )
            changed = connection.execute(
                """UPDATE app_maven_workspace_attempts
                   SET revision = ?, revised_at = ?, attempt_digest = ?
                   WHERE attempt_id = ? AND revision = ?""",
                (
                    value.revision.value,
                    _time(value.revised_at),
                    value.digest.value,
                    value.attempt_id.value,
                    current.revision.value,
                ),
            ).rowcount
            if changed != 1:
                raise DomainError(ErrorCode.REVISION_CONFLICT, "Workspace Step append CAS failed")
            return self._load_attempt(connection, attempt_id)

    def save_version(
        self, version: MavenWorkspaceVersion, *, attempt_id: StableId
    ) -> MavenWorkspaceVersion:
        version.require_valid()
        try:
            with self._database.transaction() as connection:
                row = connection.execute(
                    "SELECT version_id FROM app_maven_workspace_versions WHERE attempt_id = ?",
                    (attempt_id.value,),
                ).fetchone()
                if row is not None:
                    existing = self._load_version(connection, StableId(row["version_id"]))
                    if (
                        existing.workspace_id != version.workspace_id
                        or existing.repository_revision != version.repository_revision
                        or existing.snapshot_id != version.snapshot_id
                        or existing.snapshot_manifest_digest != version.snapshot_manifest_digest
                    ):
                        raise _inconsistent("Workspace Attempt is bound to another Version result")
                    return existing
                attempt = self._load_attempt(connection, attempt_id)
                prior_rows = connection.execute(
                    """SELECT ordinal, snapshot_id FROM app_maven_workspace_versions
                       WHERE workspace_id = ? ORDER BY ordinal""",
                    (version.workspace_id.value,),
                ).fetchall()
                actual_previous = (
                    StableId(prior_rows[-1]["snapshot_id"]) if prior_rows else None
                )
                if (
                    attempt.workspace_id != version.workspace_id
                    or attempt.repository_revision != version.repository_revision
                    or attempt.expected_current_snapshot_id != actual_previous
                    or version.ordinal != len(prior_rows) + 1
                    or version.availability
                    is not WorkspaceVersionAvailability.READ_BUNDLE_UNAVAILABLE
                    or version.single_read_set_id is not None
                    or version.comparison_read_set_id is not None
                    or version.revision != Revision(1)
                ):
                    raise _inconsistent(
                        "Workspace Version does not match its exact Update Attempt fence"
                    )
                connection.execute(
                    """INSERT INTO app_maven_workspace_versions (
                           version_id, attempt_id, workspace_id, ordinal,
                           repository_revision, snapshot_id, snapshot_manifest_digest,
                           availability, single_read_set_id, comparison_read_set_id,
                           created_at, revision, version_digest
                       ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        version.version_id.value,
                        attempt_id.value,
                        version.workspace_id.value,
                        version.ordinal,
                        version.repository_revision,
                        version.snapshot_id.value,
                        version.snapshot_manifest_digest.value,
                        version.availability.value,
                        None,
                        None,
                        _time(version.created_at),
                        version.revision.value,
                        version.digest.value,
                    ),
                )
                return self._load_version(connection, version.version_id)
        except DomainError:
            raise
        except sqlite3.IntegrityError as error:
            raise _inconsistent(
                "Workspace Version persistence invariant was violated"
            ) from error

    def update_version(
        self, version: MavenWorkspaceVersion, *, expected_revision: Revision
    ) -> MavenWorkspaceVersion:
        version.require_valid()
        if version.revision != expected_revision.next():
            raise _invalid("MAVEN_WORKSPACE_VERSION_REVISION_INVALID", "Workspace Version update has the wrong next revision")
        with self._database.transaction() as connection:
            current = self._load_version(connection, version.version_id)
            if current.revision != expected_revision:
                raise DomainError(ErrorCode.REVISION_CONFLICT, "Workspace Version revision changed")
            if (
                version.workspace_id != current.workspace_id
                or version.ordinal != current.ordinal
                or version.repository_revision != current.repository_revision
                or version.snapshot_id != current.snapshot_id
                or version.snapshot_manifest_digest
                != current.snapshot_manifest_digest
                or version.created_at != current.created_at
            ):
                raise _inconsistent(
                    "Workspace Version update attempted to change immutable coordinates"
                )
            changed = connection.execute(
                """UPDATE app_maven_workspace_versions
                   SET availability = ?, single_read_set_id = ?,
                       comparison_read_set_id = ?, revision = ?, version_digest = ?
                   WHERE version_id = ? AND revision = ?""",
                (
                    version.availability.value,
                    version.single_read_set_id.value if version.single_read_set_id else None,
                    version.comparison_read_set_id.value if version.comparison_read_set_id else None,
                    version.revision.value,
                    version.digest.value,
                    version.version_id.value,
                    expected_revision.value,
                ),
            ).rowcount
            if changed != 1:
                raise DomainError(ErrorCode.REVISION_CONFLICT, "Workspace Version CAS failed")
            return self._load_version(connection, version.version_id)

    def find_version_for_attempt(
        self, attempt_id: StableId
    ) -> MavenWorkspaceVersion | None:
        with self._database.read() as connection:
            row = connection.execute(
                "SELECT version_id FROM app_maven_workspace_versions WHERE attempt_id = ?",
                (attempt_id.value,),
            ).fetchone()
            return self._load_version(connection, StableId(row["version_id"])) if row else None

    def list_versions(
        self, workspace_id: StableId
    ) -> tuple[MavenWorkspaceVersion, ...]:
        with self._database.read() as connection:
            rows = connection.execute(
                """SELECT version_id FROM app_maven_workspace_versions
                   WHERE workspace_id = ? ORDER BY ordinal""",
                (workspace_id.value,),
            ).fetchall()
            return tuple(self._load_version(connection, StableId(row["version_id"])) for row in rows)

    def save_read_set(self, registration: ReadSetRegistration) -> ReadSetRegistration:
        registration.require_valid()
        payload = canonical_json_bytes(registration.document())
        try:
            with self._database.transaction() as connection:
                row = connection.execute(
                    "SELECT registration_digest FROM app_maven_read_set_registrations WHERE read_set_id = ?",
                    (registration.read_set_id.value,),
                ).fetchone()
                if row is not None:
                    if row["registration_digest"] != registration.digest.value:
                        raise _inconsistent("Read Set ID is bound to another registration")
                    return self._load_read_set(connection, registration.read_set_id)
                connection.execute(
                    """INSERT INTO app_maven_read_set_registrations (
                           read_set_id, workspace_id, session_id, ordered_receipt_id,
                           bundle_locator, registration_document,
                           registration_digest, ordered_receipt_created_at
                       ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        registration.read_set_id.value,
                        registration.workspace_id.value,
                        registration.session_id.value,
                        registration.ordered_receipt.receipt_id.value,
                        registration.bundle_locator,
                        payload,
                        registration.digest.value,
                        _time(registration.ordered_receipt.created_at),
                    ),
                )
                return self._load_read_set(connection, registration.read_set_id)
        except DomainError:
            raise
        except sqlite3.IntegrityError as error:
            raise _inconsistent("Read Set registration persistence invariant was violated") from error

    def get_read_set(self, read_set_id: StableId) -> ReadSetRegistration:
        with self._database.read() as connection:
            return self._load_read_set(connection, read_set_id)

    def list_read_sets(
        self, workspace_id: StableId | None = None
    ) -> tuple[ReadSetRegistration, ...]:
        with self._database.read() as connection:
            if workspace_id is None:
                rows = connection.execute(
                    "SELECT read_set_id FROM app_maven_read_set_registrations ORDER BY read_set_id"
                ).fetchall()
            else:
                rows = connection.execute(
                    """SELECT read_set_id FROM app_maven_read_set_registrations
                       WHERE workspace_id = ? ORDER BY read_set_id""",
                    (workspace_id.value,),
                ).fetchall()
            return tuple(self._load_read_set(connection, StableId(row["read_set_id"])) for row in rows)

    def get_or_create_catalog_id(self) -> StableId:
        with self._database.transaction() as connection:
            row = connection.execute(
                "SELECT catalog_id FROM app_read_set_catalog_identity WHERE singleton = 1"
            ).fetchone()
            if row is not None:
                return StableId(row["catalog_id"])
            value = self._ids.new("read_set_catalog")
            connection.execute(
                "INSERT INTO app_read_set_catalog_identity (singleton, catalog_id) VALUES (1, ?)",
                (value.value,),
            )
            return value

    def latest_catalog_publication(self) -> CatalogPublication | None:
        with self._database.read() as connection:
            row = connection.execute(
                """SELECT * FROM app_read_set_catalog_publications
                   ORDER BY revision DESC LIMIT 1"""
            ).fetchone()
            return self._publication(row) if row else None

    def save_catalog_publication(
        self, publication: CatalogPublication
    ) -> CatalogPublication:
        publication.require_valid()
        with self._database.transaction() as connection:
            row = connection.execute(
                """SELECT * FROM app_read_set_catalog_publications
                   WHERE catalog_id = ? AND revision = ?""",
                (publication.catalog_id.value, publication.revision.value),
            ).fetchone()
            if row is not None:
                existing = self._publication(row)
                if existing != publication:
                    raise _inconsistent("Catalog revision is bound to another publication")
                return existing
            connection.execute(
                """INSERT INTO app_read_set_catalog_publications (
                       catalog_id, revision, catalog_digest, entry_set_digest,
                       published_at, publication_digest
                   ) VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    publication.catalog_id.value,
                    publication.revision.value,
                    publication.catalog_digest.value,
                    publication.entry_set_digest.value,
                    _time(publication.published_at),
                    publication.digest.value,
                ),
            )
            return publication

    @staticmethod
    def _load_workspace(
        connection: sqlite3.Connection, workspace_id: StableId
    ) -> MavenWorkspace:
        if workspace_id.kind != "maven_workspace":
            raise _invalid("MAVEN_WORKSPACE_ID_INVALID", "Workspace lookup ID is invalid")
        row = connection.execute(
            "SELECT * FROM app_maven_workspaces WHERE workspace_id = ?",
            (workspace_id.value,),
        ).fetchone()
        if row is None:
            raise _invalid("MAVEN_WORKSPACE_NOT_FOUND", "Maven Workspace was not found")
        try:
            value = MavenWorkspace(
                workspace_id=StableId(row["workspace_id"]),
                idempotency_key=IdempotencyKey(row["idempotency_key"]),
                request_digest=Digest(row["request_digest"]),
                canonical_system_key=row["canonical_system_key"],
                display_name=row["display_name"],
                repository_locator=row["repository_locator"],
                root_pom=row["root_pom"],
                scope_id=StableId(row["scope_id"]),
                scope_revision=Revision(row["scope_revision"]),
                source_id=StableId(row["source_id"]),
                source_revision=Revision(row["source_revision"]),
                binding_id=StableId(row["binding_id"]),
                binding_revision=Revision(row["binding_revision"]),
                management_attempt_id=StableId(row["management_attempt_id"]),
                management_result_digest=Digest(row["management_result_digest"]),
                knowledge_profile_ref=(
                    row["knowledge_profile_ref"]
                    if "knowledge_profile_ref" in row.keys()
                    else MAVEN_STRUCTURE_PROFILE_REF
                ),
                created_at=_parse_time(row["created_at"]),
                digest=Digest(row["workspace_digest"]),
            )
            value.require_valid()
            return value
        except (DomainError, TypeError, ValueError) as error:
            raise _inconsistent("persisted Workspace failed canonical verification") from error

    @classmethod
    def _load_attempt(
        cls, connection: sqlite3.Connection, attempt_id: StableId
    ) -> MavenWorkspaceAttempt:
        if attempt_id.kind != "workspace_attempt":
            raise _invalid("MAVEN_WORKSPACE_ATTEMPT_ID_INVALID", "Workspace Attempt lookup ID is invalid")
        row = connection.execute(
            "SELECT * FROM app_maven_workspace_attempts WHERE attempt_id = ?",
            (attempt_id.value,),
        ).fetchone()
        if row is None:
            raise _invalid("MAVEN_WORKSPACE_ATTEMPT_NOT_FOUND", "Workspace Attempt was not found")
        event_rows = connection.execute(
            """SELECT * FROM app_maven_workspace_step_events
               WHERE attempt_id = ? ORDER BY sequence""",
            (attempt_id.value,),
        ).fetchall()
        try:
            events = tuple(
                WorkspaceStepEvent(
                    event_id=StableId(item["event_id"]),
                    attempt_id=StableId(item["attempt_id"]),
                    sequence=item["sequence"],
                    name=WorkspaceStepName(item["step_name"]),
                    outcome=WorkspaceStepOutcome(item["outcome"]),
                    reference_id=item["reference_id"],
                    reference_digest=Digest(item["reference_digest"]) if item["reference_digest"] else None,
                    error_code=item["error_code"],
                    error_message=item["error_message"],
                    occurred_at=_parse_time(item["occurred_at"]),
                    digest=Digest(item["event_digest"]),
                )
                for item in event_rows
            )
            value = MavenWorkspaceAttempt(
                attempt_id=StableId(row["attempt_id"]),
                idempotency_key=IdempotencyKey(row["idempotency_key"]),
                request_digest=Digest(row["request_digest"]),
                workspace_id=StableId(row["workspace_id"]),
                repository_revision=row["repository_revision"],
                expected_current_snapshot_id=StableId(row["expected_current_snapshot_id"]) if row["expected_current_snapshot_id"] else None,
                state=WorkspaceAttemptState(row["state"]),
                revision=Revision(row["revision"]),
                created_at=_parse_time(row["created_at"]),
                revised_at=_parse_time(row["revised_at"]),
                steps=events,
                digest=Digest(row["attempt_digest"]),
            )
            value.require_valid()
            return value
        except (DomainError, TypeError, ValueError) as error:
            raise _inconsistent("persisted Workspace Attempt failed canonical verification") from error

    @staticmethod
    def _load_version(
        connection: sqlite3.Connection, version_id: StableId
    ) -> MavenWorkspaceVersion:
        if version_id.kind != "workspace_version":
            raise _invalid("MAVEN_WORKSPACE_VERSION_ID_INVALID", "Workspace Version lookup ID is invalid")
        row = connection.execute(
            "SELECT * FROM app_maven_workspace_versions WHERE version_id = ?",
            (version_id.value,),
        ).fetchone()
        if row is None:
            raise _invalid("MAVEN_WORKSPACE_VERSION_NOT_FOUND", "Workspace Version was not found")
        try:
            value = MavenWorkspaceVersion(
                version_id=StableId(row["version_id"]),
                workspace_id=StableId(row["workspace_id"]),
                ordinal=row["ordinal"],
                repository_revision=row["repository_revision"],
                snapshot_id=StableId(row["snapshot_id"]),
                snapshot_manifest_digest=Digest(row["snapshot_manifest_digest"]),
                availability=WorkspaceVersionAvailability(row["availability"]),
                single_read_set_id=StableId(row["single_read_set_id"]) if row["single_read_set_id"] else None,
                comparison_read_set_id=StableId(row["comparison_read_set_id"]) if row["comparison_read_set_id"] else None,
                created_at=_parse_time(row["created_at"]),
                revision=Revision(row["revision"]),
                digest=Digest(row["version_digest"]),
            )
            value.require_valid()
            return value
        except (DomainError, TypeError, ValueError) as error:
            raise _inconsistent("persisted Workspace Version failed canonical verification") from error

    @staticmethod
    def _load_read_set(
        connection: sqlite3.Connection, read_set_id: StableId
    ) -> ReadSetRegistration:
        if read_set_id.kind != "read_set":
            raise _invalid("READ_SET_REGISTRATION_ID_INVALID", "Read Set lookup ID is invalid")
        row = connection.execute(
            "SELECT * FROM app_maven_read_set_registrations WHERE read_set_id = ?",
            (read_set_id.value,),
        ).fetchone()
        if row is None:
            raise _invalid("READ_SET_REGISTRATION_NOT_FOUND", "Read Set registration was not found")
        try:
            payload = bytes(row["registration_document"])
            document = json.loads(payload.decode("utf-8"), object_pairs_hook=_strict_object)
            value = read_set_registration_from_document(document)
            if canonical_json_bytes(value.document()) != payload:
                raise ValueError("Read Set registration bytes are not canonical")
            if (
                value.read_set_id.value != row["read_set_id"]
                or value.workspace_id.value != row["workspace_id"]
                or value.session_id.value != row["session_id"]
                or value.ordered_receipt.receipt_id.value
                != row["ordered_receipt_id"]
                or value.bundle_locator != row["bundle_locator"]
                or value.digest.value != row["registration_digest"]
                or _time(value.ordered_receipt.created_at)
                != row["ordered_receipt_created_at"]
            ):
                raise ValueError("indexed Read Set fields differ from the document")
            return value
        except (DomainError, UnicodeError, json.JSONDecodeError, TypeError, ValueError, _DuplicateKeyError) as error:
            raise _inconsistent("persisted Read Set registration failed canonical verification") from error

    @staticmethod
    def _publication(row: sqlite3.Row) -> CatalogPublication:
        try:
            value = CatalogPublication(
                catalog_id=StableId(row["catalog_id"]),
                revision=Revision(row["revision"]),
                catalog_digest=Digest(row["catalog_digest"]),
                entry_set_digest=Digest(row["entry_set_digest"]),
                published_at=_parse_time(row["published_at"]),
                digest=Digest(row["publication_digest"]),
            )
            value.require_valid()
            return value
        except (DomainError, TypeError, ValueError) as error:
            raise _inconsistent("persisted Catalog Publication failed canonical verification") from error


class _DuplicateKeyError(ValueError):
    pass


def _strict_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise _DuplicateKeyError(key)
        value[key] = item
    return value


def _attempt(
    *,
    attempt_id: StableId,
    idempotency_key: IdempotencyKey,
    request_digest: Digest,
    workspace_id: StableId,
    repository_revision: str,
    expected_current_snapshot_id: StableId | None,
    state: WorkspaceAttemptState,
    revision: Revision,
    created_at: datetime,
    revised_at: datetime,
    steps: tuple[WorkspaceStepEvent, ...],
) -> MavenWorkspaceAttempt:
    placeholder = MavenWorkspaceAttempt(
        attempt_id=attempt_id,
        idempotency_key=idempotency_key,
        request_digest=request_digest,
        workspace_id=workspace_id,
        repository_revision=repository_revision,
        expected_current_snapshot_id=expected_current_snapshot_id,
        state=state,
        revision=revision,
        created_at=created_at,
        revised_at=revised_at,
        steps=steps,
        digest=Digest("sha256:" + "0" * 64),
    )
    value = MavenWorkspaceAttempt(
        attempt_id=attempt_id,
        idempotency_key=idempotency_key,
        request_digest=request_digest,
        workspace_id=workspace_id,
        repository_revision=repository_revision,
        expected_current_snapshot_id=expected_current_snapshot_id,
        state=state,
        revision=revision,
        created_at=created_at,
        revised_at=revised_at,
        steps=steps,
        digest=digest_of(["MAVEN_WORKSPACE_ATTEMPT@1", workspace_attempt_core(placeholder)]),
    )
    value.require_valid()
    return value


def _time(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("time must include a timezone")
    return value.isoformat(timespec="microseconds")


def _parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None or parsed.utcoffset() is None or _time(parsed) != value:
        raise ValueError("time is not canonical")
    return parsed


def _invalid(reason_code: str, message: str) -> DomainError:
    return DomainError(ErrorCode.INVALID_ARGUMENT, message, {"reason_code": reason_code})


def _idempotency(message: str) -> DomainError:
    return DomainError(ErrorCode.IDEMPOTENCY_MISMATCH, message)


def _inconsistent(message: str) -> DomainError:
    return DomainError(ErrorCode.AUTHORITY_RECORD_INCONSISTENT, message)


__all__ = ["SqliteMavenWorkspaceRepository"]
