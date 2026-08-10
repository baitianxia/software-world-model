"""SQLite authority store for cross-module Source Artifact use."""

from __future__ import annotations

from datetime import datetime
import json
import sqlite3

from software_world_model.cross_cutting import (
    Digest,
    DomainError,
    ErrorCode,
    IdGenerator,
    IdempotencyKey,
    StableId,
    Uuid4IdGenerator,
    canonical_json_bytes,
)
from software_world_model.source_integration.artifact_use import (
    ArtifactReadClosure,
    ArtifactReadOperationReference,
    ArtifactReadPackage,
    ArtifactReadProtection,
    ArtifactReadProtectionMode,
    ArtifactUseConfirmation,
    ArtifactUsePurpose,
    artifact_downstream_use_digest,
    artifact_read_package_digest,
    artifact_read_protection_digest,
    artifact_read_request_digest,
    artifact_use_confirmation_digest,
    artifact_use_identity_digest,
    artifact_use_request_digest,
)

from .sqlite_database import SqliteDatabase


_SCHEMA = """
CREATE TABLE IF NOT EXISTS src_artifact_read_packages (
    package_id TEXT PRIMARY KEY,
    idempotency_key TEXT NOT NULL UNIQUE,
    request_digest TEXT NOT NULL,
    operation_references_json TEXT NOT NULL,
    closure_id TEXT NOT NULL,
    closure_digest TEXT NOT NULL,
    purpose TEXT NOT NULL,
    downstream_request_ref TEXT NOT NULL,
    downstream_request_digest TEXT NOT NULL,
    created_at TEXT NOT NULL,
    package_digest TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS src_artifact_read_protections (
    protection_id TEXT PRIMARY KEY,
    package_id TEXT NOT NULL UNIQUE,
    package_digest TEXT NOT NULL,
    closure_id TEXT NOT NULL,
    closure_digest TEXT NOT NULL,
    protection_mode TEXT NOT NULL,
    guard_required INTEGER NOT NULL CHECK (guard_required IN (0, 1)),
    issued_at TEXT NOT NULL,
    protection_digest TEXT NOT NULL,
    FOREIGN KEY (package_id) REFERENCES src_artifact_read_packages(package_id)
);

CREATE TABLE IF NOT EXISTS src_artifact_use_confirmations (
    confirmation_id TEXT PRIMARY KEY,
    idempotency_key TEXT NOT NULL UNIQUE,
    downstream_use_digest TEXT NOT NULL UNIQUE,
    use_identity_digest TEXT NOT NULL UNIQUE,
    request_digest TEXT NOT NULL,
    package_id TEXT NOT NULL,
    package_digest TEXT NOT NULL,
    closure_id TEXT NOT NULL,
    closure_digest TEXT NOT NULL,
    protection_id TEXT NOT NULL,
    protection_digest TEXT NOT NULL,
    purpose TEXT NOT NULL,
    downstream_request_ref TEXT NOT NULL,
    downstream_request_digest TEXT NOT NULL,
    downstream_candidate_ref TEXT NOT NULL,
    downstream_candidate_digest TEXT NOT NULL,
    confirmed_at TEXT NOT NULL,
    confirmation_digest TEXT NOT NULL,
    FOREIGN KEY (package_id) REFERENCES src_artifact_read_packages(package_id),
    FOREIGN KEY (protection_id) REFERENCES src_artifact_read_protections(protection_id)
);
"""


class SqliteArtifactUseAuthorityRepository:
    """Durable, idempotent, digest-checked Source authority adapter."""

    def __init__(
        self,
        database: SqliteDatabase,
        *,
        id_generator: IdGenerator | None = None,
    ) -> None:
        self._database = database
        self._ids = id_generator or Uuid4IdGenerator()
        self._database.executescript(_SCHEMA)

    def save_read_authority(
        self,
        *,
        idempotency_key: IdempotencyKey,
        request_digest: Digest,
        operation_references: tuple[ArtifactReadOperationReference, ...],
        closure_id: StableId,
        closure_digest: Digest,
        purpose: ArtifactUsePurpose,
        downstream_request_ref: str,
        downstream_request_digest: Digest,
        protection_mode: ArtifactReadProtectionMode,
        occurred_at: datetime,
    ) -> tuple[ArtifactReadPackage, ArtifactReadProtection]:
        if protection_mode is not ArtifactReadProtectionMode.NO_EVICTION:
            _invalid(
                "ARTIFACT_READ_PROTECTION_UNSUPPORTED",
                "the current Source store only supports explicit NO_EVICTION",
            )
        try:
            with self._database.transaction() as connection:
                existing = connection.execute(
                    """SELECT package_id, request_digest
                       FROM src_artifact_read_packages
                       WHERE idempotency_key = ?""",
                    (idempotency_key.value,),
                ).fetchone()
                if existing is not None:
                    if existing["request_digest"] != request_digest.value:
                        _idempotency_mismatch(
                            "ARTIFACT_READ_PACKAGE_IDEMPOTENCY_MISMATCH",
                            "Artifact Read Package idempotency key has another request",
                        )
                    return self._load_read_authority(
                        connection, StableId(existing["package_id"])
                    )

                package_id = self._ids.new("artifact_package")
                package = ArtifactReadPackage(
                    package_id=package_id,
                    request_digest=request_digest,
                    operation_references=operation_references,
                    closure_id=closure_id,
                    closure_digest=closure_digest,
                    purpose=purpose,
                    downstream_request_ref=downstream_request_ref,
                    downstream_request_digest=downstream_request_digest,
                    created_at=occurred_at,
                    digest=Digest("sha256:" + "0" * 64),
                )
                package = _with_package_digest(package)
                protection = ArtifactReadProtection(
                    protection_id=self._ids.new("artifact_protection"),
                    package_id=package.package_id,
                    package_digest=package.digest,
                    closure_id=closure_id,
                    closure_digest=closure_digest,
                    mode=protection_mode,
                    guard_required=False,
                    issued_at=occurred_at,
                    digest=Digest("sha256:" + "0" * 64),
                )
                protection = _with_protection_digest(protection)
                connection.execute(
                    """INSERT INTO src_artifact_read_packages
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        package.package_id.value,
                        idempotency_key.value,
                        package.request_digest.value,
                        _refs_json(package.operation_references),
                        package.closure_id.value,
                        package.closure_digest.value,
                        package.purpose.value,
                        package.downstream_request_ref,
                        package.downstream_request_digest.value,
                        _time(package.created_at),
                        package.digest.value,
                    ),
                )
                connection.execute(
                    """INSERT INTO src_artifact_read_protections
                       VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?)""",
                    (
                        protection.protection_id.value,
                        protection.package_id.value,
                        protection.package_digest.value,
                        protection.closure_id.value,
                        protection.closure_digest.value,
                        protection.mode.value,
                        _time(protection.issued_at),
                        protection.digest.value,
                    ),
                )
                return self._load_read_authority(connection, package.package_id)
        except DomainError:
            raise
        except sqlite3.IntegrityError as exc:
            _store_error("ARTIFACT_READ_AUTHORITY_STORE_CONFLICT", exc)

    def get_read_authority(
        self, package_id: StableId
    ) -> tuple[ArtifactReadPackage, ArtifactReadProtection]:
        with self._database.read() as connection:
            return self._load_read_authority(connection, package_id)

    def save_confirmation(
        self,
        *,
        idempotency_key: IdempotencyKey,
        downstream_use_digest: Digest,
        use_identity_digest: Digest,
        request_digest: Digest,
        package: ArtifactReadPackage,
        closure: ArtifactReadClosure,
        protection: ArtifactReadProtection,
        downstream_candidate_ref: str,
        downstream_candidate_digest: Digest,
        occurred_at: datetime,
    ) -> ArtifactUseConfirmation:
        try:
            with self._database.transaction() as connection:
                persisted = self._load_read_authority(connection, package.package_id)
                if persisted != (package, protection) or (
                    package.closure_id != closure.closure_id
                    or package.closure_digest != closure.digest
                ):
                    _inconsistent(
                        "ARTIFACT_USE_READ_AUTHORITY_CHANGED",
                        "Artifact use cannot confirm a changed read authority",
                        package_id=package.package_id.value,
                    )
                existing = connection.execute(
                    """SELECT confirmation_id, request_digest
                       FROM src_artifact_use_confirmations
                       WHERE idempotency_key = ?""",
                    (idempotency_key.value,),
                ).fetchone()
                if existing is not None:
                    if existing["request_digest"] != request_digest.value:
                        _idempotency_mismatch(
                            "ARTIFACT_USE_IDEMPOTENCY_MISMATCH",
                            "Artifact use idempotency key has another request",
                        )
                    return self._load_confirmation(
                        connection, StableId(existing["confirmation_id"])
                    )
                already_used = connection.execute(
                    """SELECT confirmation_id
                       FROM src_artifact_use_confirmations
                       WHERE downstream_use_digest = ?""",
                    (downstream_use_digest.value,),
                ).fetchone()
                if already_used is not None:
                    _idempotency_mismatch(
                        "ARTIFACT_USE_ALREADY_CONFIRMED",
                        "the exact downstream Artifact use was already confirmed",
                        confirmation_id=already_used["confirmation_id"],
                    )

                confirmation = ArtifactUseConfirmation(
                    confirmation_id=self._ids.new("artifact_use"),
                    downstream_use_digest=downstream_use_digest,
                    use_identity_digest=use_identity_digest,
                    request_digest=request_digest,
                    package_id=package.package_id,
                    package_digest=package.digest,
                    closure_id=closure.closure_id,
                    closure_digest=closure.digest,
                    protection_id=protection.protection_id,
                    protection_digest=protection.digest,
                    purpose=package.purpose,
                    downstream_request_ref=package.downstream_request_ref,
                    downstream_request_digest=package.downstream_request_digest,
                    downstream_candidate_ref=downstream_candidate_ref,
                    downstream_candidate_digest=downstream_candidate_digest,
                    confirmed_at=occurred_at,
                    digest=Digest("sha256:" + "0" * 64),
                )
                confirmation = _with_confirmation_digest(confirmation)
                connection.execute(
                    """INSERT INTO src_artifact_use_confirmations
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        confirmation.confirmation_id.value,
                        idempotency_key.value,
                        confirmation.downstream_use_digest.value,
                        confirmation.use_identity_digest.value,
                        confirmation.request_digest.value,
                        confirmation.package_id.value,
                        confirmation.package_digest.value,
                        confirmation.closure_id.value,
                        confirmation.closure_digest.value,
                        confirmation.protection_id.value,
                        confirmation.protection_digest.value,
                        confirmation.purpose.value,
                        confirmation.downstream_request_ref,
                        confirmation.downstream_request_digest.value,
                        confirmation.downstream_candidate_ref,
                        confirmation.downstream_candidate_digest.value,
                        _time(confirmation.confirmed_at),
                        confirmation.digest.value,
                    ),
                )
                return self._load_confirmation(
                    connection, confirmation.confirmation_id
                )
        except DomainError:
            raise
        except sqlite3.IntegrityError as exc:
            _store_error("ARTIFACT_USE_CONFIRMATION_STORE_CONFLICT", exc)

    def get_confirmation(
        self, confirmation_id: StableId
    ) -> ArtifactUseConfirmation:
        with self._database.read() as connection:
            return self._load_confirmation(connection, confirmation_id)

    def _load_read_authority(
        self, connection: sqlite3.Connection, package_id: StableId
    ) -> tuple[ArtifactReadPackage, ArtifactReadProtection]:
        row = connection.execute(
            """SELECT package.*, protection.protection_id,
                      protection.package_digest AS protected_package_digest,
                      protection.closure_id AS protected_closure_id,
                      protection.closure_digest AS protected_closure_digest,
                      protection.protection_mode, protection.guard_required,
                      protection.issued_at, protection.protection_digest
               FROM src_artifact_read_packages AS package
               JOIN src_artifact_read_protections AS protection
                 ON protection.package_id = package.package_id
               WHERE package.package_id = ?""",
            (package_id.value,),
        ).fetchone()
        if row is None:
            _inconsistent(
                "ARTIFACT_READ_PACKAGE_NOT_FOUND",
                "Artifact Read Package or Protection is unavailable",
                package_id=package_id.value,
            )
        try:
            idempotency_key = IdempotencyKey(row["idempotency_key"])
            package = ArtifactReadPackage(
                package_id=StableId(row["package_id"]),
                request_digest=Digest(row["request_digest"]),
                operation_references=_refs(row["operation_references_json"]),
                closure_id=StableId(row["closure_id"]),
                closure_digest=Digest(row["closure_digest"]),
                purpose=ArtifactUsePurpose(row["purpose"]),
                downstream_request_ref=row["downstream_request_ref"],
                downstream_request_digest=Digest(row["downstream_request_digest"]),
                created_at=_parse_time(row["created_at"]),
                digest=Digest(row["package_digest"]),
            )
            protection = ArtifactReadProtection(
                protection_id=StableId(row["protection_id"]),
                package_id=package.package_id,
                package_digest=Digest(row["protected_package_digest"]),
                closure_id=StableId(row["protected_closure_id"]),
                closure_digest=Digest(row["protected_closure_digest"]),
                mode=ArtifactReadProtectionMode(row["protection_mode"]),
                guard_required=_bool(row["guard_required"]),
                issued_at=_parse_time(row["issued_at"]),
                digest=Digest(row["protection_digest"]),
            )
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Artifact Read authority cannot be decoded",
                {"reason_code": "ARTIFACT_READ_AUTHORITY_DECODE_INVALID"},
            ) from exc
        expected_request = artifact_read_request_digest(
            idempotency_key=idempotency_key,
            operation_references=package.operation_references,
            closure_id=package.closure_id,
            closure_digest=package.closure_digest,
            purpose=package.purpose,
            downstream_request_ref=package.downstream_request_ref,
            downstream_request_digest=package.downstream_request_digest,
            protection_mode=protection.mode,
        )
        expected_closure_id = StableId(
            "artifact_read_closure_"
            + package.closure_digest.value.removeprefix("sha256:")[-32:]
        )
        if (
            package.request_digest != expected_request
            or package.closure_id != expected_closure_id
            or package.digest != artifact_read_package_digest(package)
            or protection.digest != artifact_read_protection_digest(protection)
            or protection.package_id != package.package_id
            or protection.package_digest != package.digest
            or protection.closure_id != package.closure_id
            or protection.closure_digest != package.closure_digest
            or protection.mode is not ArtifactReadProtectionMode.NO_EVICTION
            or protection.guard_required
        ):
            _inconsistent(
                "ARTIFACT_READ_AUTHORITY_DIGEST_INVALID",
                "Artifact Read Package or Protection is not self-consistent",
                package_id=package.package_id.value,
            )
        return package, protection

    def _load_confirmation(
        self, connection: sqlite3.Connection, confirmation_id: StableId
    ) -> ArtifactUseConfirmation:
        row = connection.execute(
            "SELECT * FROM src_artifact_use_confirmations WHERE confirmation_id = ?",
            (confirmation_id.value,),
        ).fetchone()
        if row is None:
            _inconsistent(
                "ARTIFACT_USE_CONFIRMATION_NOT_FOUND",
                "Artifact use Confirmation is unavailable",
                confirmation_id=confirmation_id.value,
            )
        try:
            idempotency_key = IdempotencyKey(row["idempotency_key"])
            confirmation = ArtifactUseConfirmation(
                confirmation_id=StableId(row["confirmation_id"]),
                downstream_use_digest=Digest(row["downstream_use_digest"]),
                use_identity_digest=Digest(row["use_identity_digest"]),
                request_digest=Digest(row["request_digest"]),
                package_id=StableId(row["package_id"]),
                package_digest=Digest(row["package_digest"]),
                closure_id=StableId(row["closure_id"]),
                closure_digest=Digest(row["closure_digest"]),
                protection_id=StableId(row["protection_id"]),
                protection_digest=Digest(row["protection_digest"]),
                purpose=ArtifactUsePurpose(row["purpose"]),
                downstream_request_ref=row["downstream_request_ref"],
                downstream_request_digest=Digest(row["downstream_request_digest"]),
                downstream_candidate_ref=row["downstream_candidate_ref"],
                downstream_candidate_digest=Digest(row["downstream_candidate_digest"]),
                confirmed_at=_parse_time(row["confirmed_at"]),
                digest=Digest(row["confirmation_digest"]),
            )
        except (TypeError, ValueError) as exc:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Artifact use Confirmation cannot be decoded",
                {"reason_code": "ARTIFACT_USE_CONFIRMATION_DECODE_INVALID"},
            ) from exc
        package, protection = self._load_read_authority(
            connection, confirmation.package_id
        )
        downstream_use = artifact_downstream_use_digest(
            purpose=confirmation.purpose,
            downstream_request_ref=confirmation.downstream_request_ref,
            downstream_request_digest=confirmation.downstream_request_digest,
            downstream_candidate_ref=confirmation.downstream_candidate_ref,
            downstream_candidate_digest=confirmation.downstream_candidate_digest,
        )
        closure = ArtifactReadClosure(
            confirmation.closure_id, (), confirmation.closure_digest
        )
        use_identity = artifact_use_identity_digest(
            package=package,
            closure=closure,
            protection=protection,
            downstream_use_digest=downstream_use,
        )
        request_digest = artifact_use_request_digest(
            idempotency_key=idempotency_key,
            use_identity_digest=use_identity,
        )
        if (
            confirmation.downstream_use_digest != downstream_use
            or confirmation.use_identity_digest != use_identity
            or confirmation.request_digest != request_digest
            or confirmation.digest != artifact_use_confirmation_digest(confirmation)
            or confirmation.package_id != package.package_id
            or confirmation.package_digest != package.digest
            or confirmation.closure_id != package.closure_id
            or confirmation.closure_digest != package.closure_digest
            or confirmation.protection_id != protection.protection_id
            or confirmation.protection_digest != protection.digest
            or confirmation.purpose is not package.purpose
            or confirmation.downstream_request_ref != package.downstream_request_ref
            or confirmation.downstream_request_digest
            != package.downstream_request_digest
        ):
            _inconsistent(
                "ARTIFACT_USE_CONFIRMATION_DIGEST_INVALID",
                "Artifact use Confirmation is not self-consistent",
                confirmation_id=confirmation.confirmation_id.value,
            )
        return confirmation


def _with_package_digest(package: ArtifactReadPackage) -> ArtifactReadPackage:
    return ArtifactReadPackage(
        package.package_id,
        package.request_digest,
        package.operation_references,
        package.closure_id,
        package.closure_digest,
        package.purpose,
        package.downstream_request_ref,
        package.downstream_request_digest,
        package.created_at,
        artifact_read_package_digest(package),
    )


def _with_protection_digest(
    protection: ArtifactReadProtection,
) -> ArtifactReadProtection:
    return ArtifactReadProtection(
        protection.protection_id,
        protection.package_id,
        protection.package_digest,
        protection.closure_id,
        protection.closure_digest,
        protection.mode,
        protection.guard_required,
        protection.issued_at,
        artifact_read_protection_digest(protection),
    )


def _with_confirmation_digest(
    confirmation: ArtifactUseConfirmation,
) -> ArtifactUseConfirmation:
    return ArtifactUseConfirmation(
        confirmation.confirmation_id,
        confirmation.downstream_use_digest,
        confirmation.use_identity_digest,
        confirmation.request_digest,
        confirmation.package_id,
        confirmation.package_digest,
        confirmation.closure_id,
        confirmation.closure_digest,
        confirmation.protection_id,
        confirmation.protection_digest,
        confirmation.purpose,
        confirmation.downstream_request_ref,
        confirmation.downstream_request_digest,
        confirmation.downstream_candidate_ref,
        confirmation.downstream_candidate_digest,
        confirmation.confirmed_at,
        artifact_use_confirmation_digest(confirmation),
    )


def _refs_json(values: tuple[ArtifactReadOperationReference, ...]) -> str:
    return canonical_json_bytes(
        tuple(
            (
                item.operation_id.value,
                item.intent_digest.value,
                item.result_digest.value,
            )
            for item in values
        )
    ).decode("utf-8")


def _refs(raw: str) -> tuple[ArtifactReadOperationReference, ...]:
    values = json.loads(raw)
    if not isinstance(values, list) or not values:
        raise ValueError("Operation references must be a non-empty list")
    refs = tuple(
        ArtifactReadOperationReference(
            StableId(item[0]), Digest(item[1]), Digest(item[2])
        )
        for item in values
        if isinstance(item, list) and len(item) == 3
    )
    if len(refs) != len(values) or len({item.operation_id for item in refs}) != len(refs):
        raise ValueError("Operation references are malformed or duplicated")
    return refs


def _bool(value: object) -> bool:
    if value not in (0, 1) or isinstance(value, bool):
        raise ValueError("SQLite boolean must be 0 or 1")
    return bool(value)


def _time(value: datetime) -> str:
    return value.isoformat(timespec="microseconds")


def _parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("authority time must include a timezone")
    return parsed


def _invalid(reason_code: str, message: str) -> None:
    raise DomainError(ErrorCode.INVALID_ARGUMENT, message, {"reason_code": reason_code})


def _idempotency_mismatch(
    reason_code: str, message: str, **details: str | int
) -> None:
    raise DomainError(
        ErrorCode.IDEMPOTENCY_MISMATCH,
        message,
        {"reason_code": reason_code, **details},
    )


def _inconsistent(
    reason_code: str, message: str, **details: str | int
) -> None:
    raise DomainError(
        ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
        message,
        {"reason_code": reason_code, **details},
    )


def _store_error(reason_code: str, exc: sqlite3.IntegrityError) -> None:
    raise DomainError(
        ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
        "Artifact use authority violated a store invariant",
        {"reason_code": reason_code, "sqlite_error": str(exc)},
    ) from exc
