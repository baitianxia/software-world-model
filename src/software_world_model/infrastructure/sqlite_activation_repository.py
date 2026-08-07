"""SQLite repository for immutable Strategy Activation decisions."""

from __future__ import annotations

from datetime import datetime
import json
import sqlite3

from software_world_model.application_services.activation import (
    ActivationDecision,
    ActivationDecisionType,
    ActivationScope,
    QualificationProof,
    StrategyDefinition,
)
from software_world_model.cross_cutting import (
    CorrelationRef,
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

from .sqlite_database import SqliteDatabase


_SCHEMA = """
CREATE TABLE IF NOT EXISTS app_activation_roots (
    control_key_digest TEXT PRIMARY KEY,
    capability_id TEXT NOT NULL,
    capability_contract_version TEXT NOT NULL,
    activation_scope_json TEXT NOT NULL,
    current_revision INTEGER NOT NULL CHECK (current_revision >= 1),
    current_decision_id TEXT NOT NULL,
    UNIQUE (capability_id, capability_contract_version, activation_scope_json)
);

CREATE TABLE IF NOT EXISTS app_activation_decisions (
    decision_id TEXT PRIMARY KEY,
    control_key_digest TEXT NOT NULL,
    activation_revision INTEGER NOT NULL CHECK (activation_revision >= 1),
    decision_type TEXT NOT NULL CHECK (decision_type IN ('ACTIVATE', 'REPLACE', 'DEACTIVATE')),
    strategy_id TEXT,
    strategy_version TEXT,
    qualification_json TEXT,
    qualification_digest TEXT,
    previous_decision_id TEXT,
    actor TEXT NOT NULL,
    reason TEXT NOT NULL,
    correlation_ref TEXT NOT NULL,
    decided_at TEXT NOT NULL,
    decision_digest TEXT NOT NULL,
    UNIQUE (control_key_digest, activation_revision),
    FOREIGN KEY (control_key_digest) REFERENCES app_activation_roots(control_key_digest)
        DEFERRABLE INITIALLY DEFERRED,
    FOREIGN KEY (previous_decision_id) REFERENCES app_activation_decisions(decision_id)
);

CREATE TABLE IF NOT EXISTS app_activation_idempotency (
    idempotency_key TEXT PRIMARY KEY,
    command_type TEXT NOT NULL,
    request_digest TEXT NOT NULL,
    decision_id TEXT NOT NULL,
    FOREIGN KEY (decision_id) REFERENCES app_activation_decisions(decision_id)
);

CREATE TABLE IF NOT EXISTS app_activation_outbox (
    event_id TEXT PRIMARY KEY,
    decision_id TEXT NOT NULL,
    control_key_digest TEXT NOT NULL,
    activation_revision INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    payload_digest TEXT NOT NULL,
    correlation_ref TEXT NOT NULL,
    occurred_at TEXT NOT NULL,
    delivered_at TEXT,
    UNIQUE (control_key_digest, activation_revision, event_type),
    FOREIGN KEY (decision_id) REFERENCES app_activation_decisions(decision_id)
);
"""


class SqliteStrategyActivationRepository:
    def __init__(self, database: SqliteDatabase, *, id_generator: IdGenerator | None = None) -> None:
        self._database = database
        self._ids = id_generator or Uuid4IdGenerator()
        self._database.executescript(_SCHEMA)

    def append_decision(
        self,
        *,
        capability_id: str,
        capability_contract_version: str,
        activation_scope: ActivationScope,
        decision_type: ActivationDecisionType,
        expected_revision: Revision | None,
        strategy: StrategyDefinition | None,
        qualification: QualificationProof | None,
        idempotency_key: IdempotencyKey,
        request_digest: Digest,
        actor: str,
        reason: str,
        correlation_ref: CorrelationRef,
        decided_at: datetime,
    ) -> ActivationDecision:
        command_type = f"StrategyActivation:{decision_type.value}@1"
        control_key_digest = digest_of(
            {
                "capability_id": capability_id,
                "capability_contract_version": capability_contract_version,
                "activation_scope": activation_scope,
            }
        )
        try:
            with self._database.transaction() as connection:
                replay = self._idempotent_result(
                    connection, idempotency_key, command_type, request_digest
                )
                if replay is not None:
                    return replay
                root = connection.execute(
                    """SELECT current_revision, current_decision_id
                       FROM app_activation_roots WHERE control_key_digest = ?""",
                    (control_key_digest.value,),
                ).fetchone()
                if decision_type is ActivationDecisionType.ACTIVATE and root is None:
                    if expected_revision is not None:
                        raise DomainError(
                            ErrorCode.ACTIVATION_CONFLICT,
                            "initial activation must not claim an existing revision",
                        )
                    new_revision = Revision(1)
                    previous_decision_id = None
                else:
                    if root is None or expected_revision is None:
                        raise DomainError(
                            ErrorCode.ACTIVATION_CONFLICT,
                            "replace/deactivate requires an existing exact activation revision",
                        )
                    actual_revision = Revision(root["current_revision"])
                    if actual_revision != expected_revision:
                        raise DomainError(
                            ErrorCode.ACTIVATION_CONFLICT,
                            "expected activation revision is stale",
                            {
                                "expected_revision": expected_revision.value,
                                "actual_revision": actual_revision.value,
                            },
                        )
                    current = self._load_decision(
                        connection, StableId(root["current_decision_id"])
                    )
                    if (
                        decision_type is ActivationDecisionType.ACTIVATE
                        and current.decision_type is not ActivationDecisionType.DEACTIVATE
                    ):
                        raise DomainError(
                            ErrorCode.ACTIVATION_CONFLICT,
                            "ACTIVATE can only re-enable a deactivated control key",
                        )
                    if (
                        decision_type is ActivationDecisionType.REPLACE
                        and current.decision_type is ActivationDecisionType.DEACTIVATE
                    ):
                        raise DomainError(
                            ErrorCode.ACTIVATION_CONFLICT,
                            "a deactivated scope requires a new ACTIVATE decision",
                        )
                    new_revision = actual_revision.next()
                    previous_decision_id = current.decision_id
                if decision_type is ActivationDecisionType.DEACTIVATE:
                    if strategy is not None or qualification is not None:
                        raise DomainError(
                            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                            "deactivation cannot carry a strategy or qualification",
                        )
                elif strategy is None or qualification is None:
                    raise DomainError(
                        ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                        "activation decision requires a strategy and qualification",
                    )
                decision_id = self._ids.new("activation_decision")
                core = {
                    "decision_id": decision_id.value,
                    "capability_id": capability_id,
                    "capability_contract_version": capability_contract_version,
                    "activation_scope": activation_scope,
                    "decision_type": decision_type.value,
                    "activation_revision": new_revision.value,
                    "strategy_id": strategy.strategy_id if strategy else None,
                    "strategy_version": strategy.strategy_version if strategy else None,
                    "qualification_digest": qualification.digest.value if qualification else None,
                    "previous_decision_id": (
                        previous_decision_id.value if previous_decision_id else None
                    ),
                    "actor": actor,
                    "reason": reason,
                    "decided_at": decided_at,
                }
                decision = ActivationDecision(
                    decision_id=decision_id,
                    capability_id=capability_id,
                    capability_contract_version=capability_contract_version,
                    activation_scope=activation_scope,
                    decision_type=decision_type,
                    activation_revision=new_revision,
                    strategy_id=strategy.strategy_id if strategy else None,
                    strategy_version=strategy.strategy_version if strategy else None,
                    qualification=qualification,
                    previous_decision_id=previous_decision_id,
                    actor=actor,
                    reason=reason,
                    decided_at=decided_at,
                    digest=digest_of(core),
                )
                if root is None:
                    connection.execute(
                        """INSERT INTO app_activation_roots
                           (control_key_digest, capability_id, capability_contract_version,
                            activation_scope_json, current_revision, current_decision_id)
                           VALUES (?, ?, ?, ?, ?, ?)""",
                        (
                            control_key_digest.value,
                            capability_id,
                            capability_contract_version,
                            canonical_json_bytes(activation_scope).decode("utf-8"),
                            new_revision.value,
                            decision_id.value,
                        ),
                    )
                self._insert_decision(connection, decision, control_key_digest, correlation_ref)
                if root is not None:
                    cursor = connection.execute(
                        """UPDATE app_activation_roots
                           SET current_revision = ?, current_decision_id = ?
                           WHERE control_key_digest = ? AND current_revision = ?""",
                        (
                            new_revision.value,
                            decision_id.value,
                            control_key_digest.value,
                            expected_revision.value,
                        ),
                    )
                    if cursor.rowcount != 1:
                        raise DomainError(
                            ErrorCode.ACTIVATION_CONFLICT,
                            "activation revision changed before commit",
                        )
                connection.execute(
                    "INSERT INTO app_activation_idempotency VALUES (?, ?, ?, ?)",
                    (
                        idempotency_key.value,
                        command_type,
                        request_digest.value,
                        decision_id.value,
                    ),
                )
                payload_digest = digest_of(
                    {
                        "owner": "APPLICATION_SERVICES",
                        "decision_id": decision_id.value,
                        "decision_digest": decision.digest.value,
                        "activation_revision": new_revision.value,
                    }
                )
                connection.execute(
                    """INSERT INTO app_activation_outbox
                       (event_id, decision_id, control_key_digest, activation_revision,
                        event_type, payload_digest, correlation_ref, occurred_at, delivered_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL)""",
                    (
                        self._ids.new("outbox_event").value,
                        decision_id.value,
                        control_key_digest.value,
                        new_revision.value,
                        f"STRATEGY_{decision_type.value}@1",
                        payload_digest.value,
                        correlation_ref.value,
                        _time(decided_at),
                    ),
                )
                return decision
        except DomainError:
            raise
        except sqlite3.IntegrityError as exc:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "activation transaction violated a store invariant",
                {"sqlite_error": str(exc)},
            ) from exc

    def get_current(
        self,
        *,
        capability_id: str,
        capability_contract_version: str,
        activation_scope: ActivationScope,
    ) -> ActivationDecision | None:
        control_key_digest = digest_of(
            {
                "capability_id": capability_id,
                "capability_contract_version": capability_contract_version,
                "activation_scope": activation_scope,
            }
        )
        with self._database.read() as connection:
            row = connection.execute(
                """SELECT current_decision_id FROM app_activation_roots
                   WHERE control_key_digest = ?""",
                (control_key_digest.value,),
            ).fetchone()
            if row is None:
                return None
            return self._load_decision(connection, StableId(row["current_decision_id"]))

    def _idempotent_result(
        self,
        connection: sqlite3.Connection,
        key: IdempotencyKey,
        command_type: str,
        request_digest: Digest,
    ) -> ActivationDecision | None:
        row = connection.execute(
            """SELECT command_type, request_digest, decision_id
               FROM app_activation_idempotency WHERE idempotency_key = ?""",
            (key.value,),
        ).fetchone()
        if row is None:
            return None
        if row["command_type"] != command_type or row["request_digest"] != request_digest.value:
            raise DomainError(
                ErrorCode.IDEMPOTENCY_MISMATCH,
                "activation idempotency key was used for a different decision request",
            )
        return self._load_decision(connection, StableId(row["decision_id"]))

    @staticmethod
    def _insert_decision(
        connection: sqlite3.Connection,
        decision: ActivationDecision,
        control_key_digest: Digest,
        correlation_ref: CorrelationRef,
    ) -> None:
        qualification_json = (
            canonical_json_bytes(decision.qualification.core()).decode("utf-8")
            if decision.qualification
            else None
        )
        connection.execute(
            """INSERT INTO app_activation_decisions
               (decision_id, control_key_digest, activation_revision, decision_type,
                strategy_id, strategy_version, qualification_json, qualification_digest,
                previous_decision_id, actor, reason, correlation_ref, decided_at,
                decision_digest)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                decision.decision_id.value,
                control_key_digest.value,
                decision.activation_revision.value,
                decision.decision_type.value,
                decision.strategy_id,
                decision.strategy_version,
                qualification_json,
                decision.qualification.digest.value if decision.qualification else None,
                decision.previous_decision_id.value if decision.previous_decision_id else None,
                decision.actor,
                decision.reason,
                correlation_ref.value,
                _time(decision.decided_at),
                decision.digest.value,
            ),
        )

    def _load_decision(
        self, connection: sqlite3.Connection, decision_id: StableId
    ) -> ActivationDecision:
        row = connection.execute(
            """SELECT d.*, root.capability_id, root.capability_contract_version,
                      root.activation_scope_json
               FROM app_activation_decisions d
               JOIN app_activation_roots root
                 ON root.control_key_digest = d.control_key_digest
               WHERE d.decision_id = ?""",
            (decision_id.value,),
        ).fetchone()
        if row is None:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "activation decision referenced by authority state does not exist",
            )
        qualification = None
        if row["qualification_json"] is not None:
            core = json.loads(row["qualification_json"])
            qualification = QualificationProof(
                proof_ref=core["proof_ref"],
                capability_id=core["capability_id"],
                capability_contract_version=core["capability_contract_version"],
                strategy_id=core["strategy_id"],
                strategy_version=core["strategy_version"],
                result_ref=core["result_ref"],
                validity_ref=core["validity_ref"],
                qualification_kind=core["qualification_kind"],
                digest=Digest(row["qualification_digest"]),
            )
        activation_scope = tuple(
            (item[0], item[1]) for item in json.loads(row["activation_scope_json"])
        )
        return ActivationDecision(
            decision_id=StableId(row["decision_id"]),
            capability_id=row["capability_id"],
            capability_contract_version=row["capability_contract_version"],
            activation_scope=activation_scope,
            decision_type=ActivationDecisionType(row["decision_type"]),
            activation_revision=Revision(row["activation_revision"]),
            strategy_id=row["strategy_id"],
            strategy_version=row["strategy_version"],
            qualification=qualification,
            previous_decision_id=(
                StableId(row["previous_decision_id"])
                if row["previous_decision_id"] is not None
                else None
            ),
            actor=row["actor"],
            reason=row["reason"],
            decided_at=_parse_time(row["decided_at"]),
            digest=Digest(row["decision_digest"]),
        )


def _time(value: datetime) -> str:
    return value.isoformat(timespec="microseconds").replace("+00:00", "Z")


def _parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))
