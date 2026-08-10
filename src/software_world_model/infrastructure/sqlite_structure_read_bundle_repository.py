"""SQLite Receipt authority for immutable Structure Read Bundles."""

from __future__ import annotations

from datetime import datetime
import sqlite3

from software_world_model.application_services.structure_read_bundle import (
    StoredStructureReadBundle,
    StructureReadBundleKind,
    StructureReadBundleReceipt,
    StructureReadBundleRepository,
)
from software_world_model.cross_cutting import (
    Digest,
    DomainError,
    ErrorCode,
    IdGenerator,
    IdempotencyKey,
    StableId,
    Uuid4IdGenerator,
)

from .sqlite_database import SqliteDatabase


_SCHEMA = """
CREATE TABLE IF NOT EXISTS app_structure_read_bundle_receipts (
    receipt_id TEXT PRIMARY KEY,
    idempotency_key TEXT NOT NULL UNIQUE,
    request_digest TEXT NOT NULL,
    bundle_kind TEXT NOT NULL CHECK (
        bundle_kind IN ('SNAPSHOT', 'ORDERED_READ_SET')
    ),
    scope_id TEXT NOT NULL,
    session_id TEXT,
    read_set_digest TEXT,
    bundle_locator TEXT NOT NULL,
    bundle_format_ref TEXT NOT NULL,
    bundle_digest TEXT NOT NULL,
    file_digest TEXT NOT NULL,
    created_at TEXT NOT NULL,
    receipt_digest TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS app_structure_read_bundle_receipt_snapshots (
    receipt_id TEXT NOT NULL,
    ordinal INTEGER NOT NULL CHECK (ordinal >= 0),
    snapshot_id TEXT NOT NULL,
    PRIMARY KEY (receipt_id, ordinal),
    UNIQUE (receipt_id, snapshot_id),
    FOREIGN KEY (receipt_id)
        REFERENCES app_structure_read_bundle_receipts(receipt_id)
);

CREATE INDEX IF NOT EXISTS idx_structure_read_bundle_snapshot_receipts
    ON app_structure_read_bundle_receipt_snapshots(snapshot_id, receipt_id);
"""


class SqliteStructureReadBundleRepository(StructureReadBundleRepository):
    """Persist separate post-publication Bundle Receipts, never Snapshot state."""

    def __init__(
        self,
        database: SqliteDatabase,
        *,
        id_generator: IdGenerator | None = None,
    ) -> None:
        self._database = database
        self._ids = id_generator or Uuid4IdGenerator()
        self._database.executescript(_SCHEMA)

    def replay(
        self, *, idempotency_key: IdempotencyKey, request_digest: Digest
    ) -> StructureReadBundleReceipt | None:
        with self._database.read() as connection:
            row = connection.execute(
                """SELECT receipt_id, request_digest
                   FROM app_structure_read_bundle_receipts
                   WHERE idempotency_key = ?""",
                (idempotency_key.value,),
            ).fetchone()
            if row is None:
                return None
            if row["request_digest"] != request_digest.value:
                raise DomainError(
                    ErrorCode.IDEMPOTENCY_MISMATCH,
                    "Structure Read Bundle idempotency key has a different request",
                )
            return self._load(connection, StableId(row["receipt_id"]))

    def save(
        self,
        *,
        idempotency_key: IdempotencyKey,
        request_digest: Digest,
        kind: StructureReadBundleKind,
        scope_id: StableId,
        snapshot_ids: tuple[StableId, ...],
        session_id: StableId | None,
        read_set_digest: Digest | None,
        stored_bundle: StoredStructureReadBundle,
        created_at: datetime,
    ) -> StructureReadBundleReceipt:
        receipt = StructureReadBundleReceipt.create(
            receipt_id=self._ids.new("read_bundle_receipt"),
            idempotency_key=idempotency_key,
            kind=kind,
            request_digest=request_digest,
            scope_id=scope_id,
            snapshot_ids=snapshot_ids,
            session_id=session_id,
            read_set_digest=read_set_digest,
            stored_bundle=stored_bundle,
            created_at=created_at,
        )
        try:
            with self._database.transaction() as connection:
                existing = connection.execute(
                    """SELECT receipt_id, request_digest
                       FROM app_structure_read_bundle_receipts
                       WHERE idempotency_key = ?""",
                    (idempotency_key.value,),
                ).fetchone()
                if existing is not None:
                    if existing["request_digest"] != request_digest.value:
                        raise DomainError(
                            ErrorCode.IDEMPOTENCY_MISMATCH,
                            "Structure Read Bundle idempotency key has a different request",
                        )
                    return self._load(
                        connection,
                        StableId(existing["receipt_id"]),
                    )
                self._insert(connection, idempotency_key, receipt)
                return self._load(connection, receipt.receipt_id)
        except DomainError:
            raise
        except sqlite3.IntegrityError as exc:
            # A concurrent writer may have won the same idempotent command.
            replay = self.replay(
                idempotency_key=idempotency_key,
                request_digest=request_digest,
            )
            if replay is not None:
                return replay
            raise _inconsistent(
                "Structure Read Bundle Receipt violated a persistence invariant"
            ) from exc

    def get(self, receipt_id: StableId) -> StructureReadBundleReceipt:
        with self._database.read() as connection:
            return self._load(connection, receipt_id)

    def latest_snapshot(
        self, snapshot_id: StableId
    ) -> StructureReadBundleReceipt | None:
        if snapshot_id.kind != "structure_snapshot":
            raise _invalid(
                "READ_BUNDLE_SNAPSHOT_ID_INVALID",
                "Bundle lookup requires a Structure Snapshot ID",
            )
        with self._database.read() as connection:
            row = connection.execute(
                """SELECT receipts.receipt_id
                   FROM app_structure_read_bundle_receipts AS receipts
                   JOIN app_structure_read_bundle_receipt_snapshots AS snapshots
                     ON snapshots.receipt_id = receipts.receipt_id
                   WHERE snapshots.snapshot_id = ?
                     AND snapshots.ordinal = 0
                     AND receipts.bundle_kind = 'SNAPSHOT'
                   ORDER BY receipts.created_at DESC, receipts.receipt_id DESC
                   LIMIT 1""",
                (snapshot_id.value,),
            ).fetchone()
            if row is None:
                return None
            receipt = self._load(connection, StableId(row["receipt_id"]))
            if receipt.snapshot_ids != (snapshot_id,):
                raise _inconsistent(
                    "latest Snapshot Bundle Receipt has another Snapshot binding"
                )
            return receipt

    @staticmethod
    def _insert(
        connection: sqlite3.Connection,
        idempotency_key: IdempotencyKey,
        receipt: StructureReadBundleReceipt,
    ) -> None:
        receipt.require_valid()
        connection.execute(
            """INSERT INTO app_structure_read_bundle_receipts (
                   receipt_id, idempotency_key, request_digest, bundle_kind,
                   scope_id, session_id, read_set_digest, bundle_locator,
                   bundle_format_ref, bundle_digest, file_digest, created_at,
                   receipt_digest
               ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                receipt.receipt_id.value,
                idempotency_key.value,
                receipt.request_digest.value,
                receipt.kind.value,
                receipt.scope_id.value,
                receipt.session_id.value if receipt.session_id is not None else None,
                (
                    receipt.read_set_digest.value
                    if receipt.read_set_digest is not None
                    else None
                ),
                receipt.stored_bundle.locator,
                receipt.stored_bundle.format_ref,
                receipt.stored_bundle.bundle_digest.value,
                receipt.stored_bundle.file_digest.value,
                _time(receipt.created_at),
                receipt.digest.value,
            ),
        )
        connection.executemany(
            """INSERT INTO app_structure_read_bundle_receipt_snapshots (
                   receipt_id, ordinal, snapshot_id
               ) VALUES (?, ?, ?)""",
            tuple(
                (receipt.receipt_id.value, ordinal, snapshot_id.value)
                for ordinal, snapshot_id in enumerate(receipt.snapshot_ids)
            ),
        )

    @staticmethod
    def _load(
        connection: sqlite3.Connection,
        receipt_id: StableId,
    ) -> StructureReadBundleReceipt:
        if receipt_id.kind != "read_bundle_receipt":
            raise _invalid(
                "READ_BUNDLE_RECEIPT_ID_INVALID",
                "Bundle Receipt lookup has the wrong ID kind",
            )
        row = connection.execute(
            """SELECT * FROM app_structure_read_bundle_receipts
               WHERE receipt_id = ?""",
            (receipt_id.value,),
        ).fetchone()
        if row is None:
            raise _invalid(
                "READ_BUNDLE_RECEIPT_NOT_FOUND",
                "Structure Read Bundle Receipt was not found",
            )
        try:
            snapshot_rows = connection.execute(
                """SELECT ordinal, snapshot_id
                   FROM app_structure_read_bundle_receipt_snapshots
                   WHERE receipt_id = ? ORDER BY ordinal""",
                (receipt_id.value,),
            ).fetchall()
            if [item["ordinal"] for item in snapshot_rows] != list(
                range(len(snapshot_rows))
            ):
                raise ValueError("Snapshot Receipt ordinals are not contiguous")
            receipt = StructureReadBundleReceipt(
                receipt_id=StableId(row["receipt_id"]),
                idempotency_key=IdempotencyKey(row["idempotency_key"]),
                kind=StructureReadBundleKind(row["bundle_kind"]),
                request_digest=Digest(row["request_digest"]),
                scope_id=StableId(row["scope_id"]),
                snapshot_ids=tuple(
                    StableId(item["snapshot_id"]) for item in snapshot_rows
                ),
                session_id=(
                    StableId(row["session_id"])
                    if row["session_id"] is not None
                    else None
                ),
                read_set_digest=(
                    Digest(row["read_set_digest"])
                    if row["read_set_digest"] is not None
                    else None
                ),
                stored_bundle=StoredStructureReadBundle(
                    locator=row["bundle_locator"],
                    format_ref=row["bundle_format_ref"],
                    bundle_digest=Digest(row["bundle_digest"]),
                    file_digest=Digest(row["file_digest"]),
                ),
                created_at=_parse_time(row["created_at"]),
                digest=Digest(row["receipt_digest"]),
            )
            receipt.require_valid()
            return receipt
        except DomainError as exc:
            raise _inconsistent(
                "persisted Structure Read Bundle Receipt failed canonical verification"
            ) from exc
        except (KeyError, TypeError, ValueError) as exc:
            raise _inconsistent(
                "persisted Structure Read Bundle Receipt has malformed authority fields"
            ) from exc


def _time(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Bundle Receipt time must include a timezone")
    return value.isoformat(timespec="microseconds")


def _parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("Bundle Receipt time has no timezone")
    if value != _time(parsed):
        raise ValueError("Bundle Receipt time is not canonical")
    return parsed


def _invalid(reason_code: str, message: str) -> DomainError:
    return DomainError(
        ErrorCode.INVALID_ARGUMENT,
        message,
        {"reason_code": reason_code},
    )


def _inconsistent(message: str) -> DomainError:
    return DomainError(ErrorCode.AUTHORITY_RECORD_INCONSISTENT, message)


__all__ = ["SqliteStructureReadBundleRepository"]
