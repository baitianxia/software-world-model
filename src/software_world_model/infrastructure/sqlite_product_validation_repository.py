"""SQLite authority store for independent product holdout attestations."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import sqlite3

from software_world_model.application_services.activation import QualificationProof
from software_world_model.application_services.product_validation import (
    ProductValidationAttestation,
    ProductValidationRepository,
)
from software_world_model.cross_cutting import (
    Digest,
    DomainError,
    ErrorCode,
    IdempotencyKey,
    StableId,
    canonical_json_bytes,
)

from .sqlite_database import SqliteDatabase


_SCHEMA = """
CREATE TABLE IF NOT EXISTS app_product_validation_attestations (
    attestation_id TEXT PRIMARY KEY,
    qualification_digest TEXT NOT NULL,
    strategy_implementation_digest TEXT NOT NULL,
    recorded_at TEXT NOT NULL,
    valid_until TEXT NOT NULL,
    attestation_digest TEXT NOT NULL UNIQUE,
    payload_json TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_product_validation_current
ON app_product_validation_attestations (
    qualification_digest,
    strategy_implementation_digest,
    valid_until
);

CREATE TABLE IF NOT EXISTS app_product_validation_commands (
    idempotency_key TEXT PRIMARY KEY,
    request_digest TEXT NOT NULL,
    attestation_id TEXT NOT NULL,
    FOREIGN KEY (attestation_id)
        REFERENCES app_product_validation_attestations(attestation_id)
);
"""


class SqliteProductValidationRepository(ProductValidationRepository):
    def __init__(self, database: SqliteDatabase) -> None:
        self._database = database
        self._database.executescript(_SCHEMA)

    def save(
        self,
        *,
        idempotency_key: IdempotencyKey,
        request_digest: Digest,
        attestation: ProductValidationAttestation,
    ) -> ProductValidationAttestation:
        if not attestation.verify_digest():
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "product validation attestation digest does not verify",
            )
        try:
            with self._database.transaction() as connection:
                replay = connection.execute(
                    """SELECT request_digest, attestation_id
                       FROM app_product_validation_commands
                       WHERE idempotency_key = ?""",
                    (idempotency_key.value,),
                ).fetchone()
                if replay is not None:
                    if replay["request_digest"] != request_digest.value:
                        raise DomainError(
                            ErrorCode.IDEMPOTENCY_MISMATCH,
                            "product validation key was reused for another request",
                        )
                    return self._load(
                        connection, StableId(replay["attestation_id"])
                    )

                existing = connection.execute(
                    """SELECT attestation_digest
                       FROM app_product_validation_attestations
                       WHERE attestation_id = ?""",
                    (attestation.attestation_id.value,),
                ).fetchone()
                if existing is not None:
                    if existing["attestation_digest"] != attestation.digest.value:
                        raise DomainError(
                            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                            "product validation identity already has different evidence",
                        )
                else:
                    connection.execute(
                        """INSERT INTO app_product_validation_attestations
                           VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (
                            attestation.attestation_id.value,
                            attestation.qualification_digest.value,
                            attestation.strategy_implementation_digest.value,
                            _time(attestation.recorded_at),
                            _time(attestation.valid_until),
                            attestation.digest.value,
                            _json(_payload(attestation)),
                        ),
                    )
                connection.execute(
                    "INSERT INTO app_product_validation_commands VALUES (?, ?, ?)",
                    (
                        idempotency_key.value,
                        request_digest.value,
                        attestation.attestation_id.value,
                    ),
                )
                return self._load(connection, attestation.attestation_id)
        except DomainError:
            raise
        except sqlite3.IntegrityError as exc:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "product validation violated a store invariant",
            ) from exc

    def has_current_pass(
        self,
        *,
        qualification: QualificationProof,
        strategy_implementation_digest: Digest,
        at: datetime,
    ) -> bool:
        if (
            at.tzinfo is None
            or at.utcoffset() is None
            or not qualification.verify_digest()
            or qualification.qualification_kind != "CAPABILITY_EVALUATION"
        ):
            return False
        checked_at = at.astimezone(timezone.utc)
        try:
            with self._database.read() as connection:
                rows = connection.execute(
                    """SELECT attestation_id
                       FROM app_product_validation_attestations
                       WHERE qualification_digest = ?
                         AND strategy_implementation_digest = ?
                       ORDER BY recorded_at DESC, attestation_id DESC""",
                    (
                        qualification.digest.value,
                        strategy_implementation_digest.value,
                    ),
                ).fetchall()
                attestations = tuple(
                    self._load(connection, StableId(row["attestation_id"]))
                    for row in rows
                )
            return any(
                _matches(
                    attestation,
                    qualification,
                    strategy_implementation_digest,
                    checked_at,
                )
                for attestation in attestations
            )
        except (DomainError, ValueError, TypeError):
            return False

    @staticmethod
    def _load(
        connection: sqlite3.Connection, attestation_id: StableId
    ) -> ProductValidationAttestation:
        row = connection.execute(
            """SELECT * FROM app_product_validation_attestations
               WHERE attestation_id = ?""",
            (attestation_id.value,),
        ).fetchone()
        if row is None:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "product validation attestation is missing",
            )
        attestation = _attestation(json.loads(row["payload_json"]))
        if (
            not attestation.verify_digest()
            or attestation.attestation_id.value != row["attestation_id"]
            or attestation.qualification_digest.value
            != row["qualification_digest"]
            or attestation.strategy_implementation_digest.value
            != row["strategy_implementation_digest"]
            or _time(attestation.recorded_at) != row["recorded_at"]
            or _time(attestation.valid_until) != row["valid_until"]
            or attestation.digest.value != row["attestation_digest"]
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "product validation authority record does not verify",
            )
        return attestation


def _matches(
    attestation: ProductValidationAttestation,
    qualification: QualificationProof,
    strategy_implementation_digest: Digest,
    at: datetime,
) -> bool:
    return (
        attestation.capability_id == qualification.capability_id
        and attestation.capability_contract_version
        == qualification.capability_contract_version
        and attestation.strategy_id == qualification.strategy_id
        and attestation.strategy_version == qualification.strategy_version
        and attestation.qualification_digest == qualification.digest
        and attestation.strategy_implementation_digest
        == strategy_implementation_digest
        and attestation.recorded_at <= at < attestation.valid_until
        and attestation.recorded_at < attestation.valid_until
        and attestation.direct_origin != attestation.world_origin
        and attestation.evaluator_origin
        not in {attestation.direct_origin, attestation.world_origin}
        and attestation.world_correctness_milli
        >= attestation.direct_correctness_milli
        and attestation.world_completion_milli
        >= attestation.direct_completion_milli
        and attestation.material_error_count == 0
    )


def _payload(attestation: ProductValidationAttestation) -> dict[str, object]:
    return {
        **attestation.core(),
        "recorded_at": _time(attestation.recorded_at),
        "valid_until": _time(attestation.valid_until),
        "digest": attestation.digest.value,
    }


def _attestation(value: dict[str, object]) -> ProductValidationAttestation:
    return ProductValidationAttestation(
        attestation_id=StableId(str(value["attestation_id"])),
        capability_id=str(value["capability_id"]),
        capability_contract_version=str(value["capability_contract_version"]),
        strategy_id=str(value["strategy_id"]),
        strategy_version=str(value["strategy_version"]),
        strategy_implementation_digest=Digest(
            str(value["strategy_implementation_digest"])
        ),
        qualification_digest=Digest(str(value["qualification_digest"])),
        holdout_suite_ref=str(value["holdout_suite_ref"]),
        holdout_suite_digest=Digest(str(value["holdout_suite_digest"])),
        case_ids=tuple(str(item) for item in value["case_ids"]),
        direct_result_digest=Digest(str(value["direct_result_digest"])),
        world_result_digest=Digest(str(value["world_result_digest"])),
        comparison_digest=Digest(str(value["comparison_digest"])),
        direct_origin=str(value["direct_origin"]),
        world_origin=str(value["world_origin"]),
        evaluator_origin=str(value["evaluator_origin"]),
        direct_correctness_milli=int(value["direct_correctness_milli"]),
        world_correctness_milli=int(value["world_correctness_milli"]),
        direct_completion_milli=int(value["direct_completion_milli"]),
        world_completion_milli=int(value["world_completion_milli"]),
        material_error_count=int(value["material_error_count"]),
        recorded_at=_parse_time(str(value["recorded_at"])),
        valid_until=_parse_time(str(value["valid_until"])),
        digest=Digest(str(value["digest"])),
    )


def _json(value: object) -> str:
    return canonical_json_bytes(value).decode("utf-8")


def _time(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "product validation timestamp must be timezone-aware",
        )
    return value.astimezone(timezone.utc).isoformat()


def _parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("product validation timestamp is naive")
    return parsed.astimezone(timezone.utc)
