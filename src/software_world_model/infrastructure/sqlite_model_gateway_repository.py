"""Append-only SQLite Model Call Record store."""

from __future__ import annotations

from datetime import datetime
import sqlite3

from software_world_model.ai_infrastructure.model_gateway import (
    AdapterResponse,
    AuthorizedInputItem,
    AuthorizedInputManifest,
    InputDisposition,
    IsolationReceipt,
    ModelCallRecord,
    ModelCallState,
    ModelProviderHTTPFailureEvidence,
    PlatformProposalMode,
    ProviderRequest,
    RecoveredModelCall,
    ReplayClassification,
    RuntimeAccessMode,
)
from software_world_model.cross_cutting import (
    Digest,
    DomainError,
    ErrorCode,
    IdGenerator,
    Revision,
    StableId,
    Uuid4IdGenerator,
    digest_of,
)

from .sqlite_database import SqliteDatabase


_SCHEMA = """
CREATE TABLE IF NOT EXISTS ai_model_call_roots (
    model_call_id TEXT PRIMARY KEY,
    current_revision INTEGER NOT NULL CHECK (current_revision >= 1),
    current_state TEXT NOT NULL,
    manifest_id TEXT NOT NULL,
    manifest_digest TEXT NOT NULL,
    provider_request_digest TEXT NOT NULL,
    isolation_receipt_id TEXT NOT NULL,
    isolation_receipt_digest TEXT NOT NULL,
    provider_type TEXT NOT NULL,
    adapter_version TEXT NOT NULL,
    requested_model_ref TEXT NOT NULL,
    created_at TEXT NOT NULL,
    revised_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ai_model_call_revisions (
    model_call_id TEXT NOT NULL,
    revision INTEGER NOT NULL CHECK (revision >= 1),
    state TEXT NOT NULL,
    actual_model_fingerprint TEXT,
    provider_request_id TEXT,
    output_digest TEXT,
    input_tokens INTEGER,
    output_tokens INTEGER,
    usage_complete INTEGER NOT NULL CHECK (usage_complete IN (0, 1)),
    failure_code TEXT,
    occurred_at TEXT NOT NULL,
    PRIMARY KEY (model_call_id, revision),
    FOREIGN KEY (model_call_id) REFERENCES ai_model_call_roots(model_call_id)
);

CREATE TABLE IF NOT EXISTS ai_model_call_http_failure_evidence (
    model_call_id TEXT PRIMARY KEY,
    schema_ref TEXT NOT NULL,
    provider_request_digest TEXT NOT NULL,
    isolation_receipt_digest TEXT NOT NULL,
    failure_code TEXT NOT NULL,
    http_status INTEGER NOT NULL CHECK (http_status BETWEEN 100 AND 599),
    provider_error_code TEXT,
    provider_error_type TEXT,
    provider_request_id TEXT,
    evidence_digest TEXT NOT NULL,
    FOREIGN KEY (model_call_id) REFERENCES ai_model_call_roots(model_call_id)
);

CREATE TABLE IF NOT EXISTS ai_isolation_receipts (
    receipt_id TEXT PRIMARY KEY,
    manifest_digest TEXT NOT NULL,
    provider_request_digest TEXT NOT NULL,
    provider_type TEXT NOT NULL,
    adapter_version TEXT NOT NULL,
    configuration_fingerprint TEXT NOT NULL,
    runtime_access_mode TEXT NOT NULL,
    platform_proposal_mode TEXT NOT NULL,
    conformance_result_ref TEXT NOT NULL,
    issued_at TEXT NOT NULL,
    receipt_digest TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ai_model_call_execution_keys (
    execution_envelope_ref TEXT PRIMARY KEY,
    logical_request_digest TEXT NOT NULL,
    model_call_id TEXT NOT NULL UNIQUE,
    FOREIGN KEY (model_call_id) REFERENCES ai_model_call_roots(model_call_id)
);

CREATE TABLE IF NOT EXISTS ai_model_call_outputs (
    model_call_id TEXT PRIMARY KEY,
    provider_request_id TEXT,
    actual_model_fingerprint TEXT,
    replay_classification TEXT NOT NULL,
    output_text TEXT NOT NULL,
    output_digest TEXT NOT NULL,
    input_tokens INTEGER,
    output_tokens INTEGER,
    usage_complete INTEGER NOT NULL CHECK (usage_complete IN (0, 1)),
    termination_reason TEXT NOT NULL,
    output_normalization TEXT NOT NULL,
    FOREIGN KEY (model_call_id) REFERENCES ai_model_call_roots(model_call_id)
);

CREATE TABLE IF NOT EXISTS ai_model_call_manifests (
    model_call_id TEXT PRIMARY KEY,
    manifest_id TEXT NOT NULL UNIQUE,
    version INTEGER NOT NULL CHECK (version >= 1),
    capability_id TEXT NOT NULL,
    strategy_ref TEXT NOT NULL,
    execution_stage TEXT NOT NULL,
    calling_module TEXT NOT NULL,
    proposal_vocabulary_ref TEXT,
    manifest_digest TEXT NOT NULL,
    FOREIGN KEY (model_call_id) REFERENCES ai_model_call_roots(model_call_id)
);

CREATE TABLE IF NOT EXISTS ai_model_call_manifest_items (
    model_call_id TEXT NOT NULL,
    ordinal INTEGER NOT NULL CHECK (ordinal >= 0),
    item_id TEXT NOT NULL,
    schema_ref TEXT NOT NULL,
    classification TEXT NOT NULL,
    purpose TEXT NOT NULL,
    authority_reference TEXT NOT NULL,
    disposition TEXT NOT NULL,
    content TEXT NOT NULL,
    transformation_ref TEXT NOT NULL,
    content_digest TEXT NOT NULL,
    PRIMARY KEY (model_call_id, item_id),
    UNIQUE (model_call_id, ordinal),
    FOREIGN KEY (model_call_id) REFERENCES ai_model_call_manifests(model_call_id)
);
"""


class SqliteModelGatewayRepository:
    def __init__(self, database: SqliteDatabase, *, id_generator: IdGenerator | None = None) -> None:
        self._database = database
        self._ids = id_generator or Uuid4IdGenerator()
        self._database.executescript(_SCHEMA)

    def recover(
        self,
        *,
        execution_envelope_ref: str,
        logical_request_digest: Digest,
    ) -> RecoveredModelCall | None:
        with self._database.read() as connection:
            row = connection.execute(
                "SELECT * FROM ai_model_call_execution_keys WHERE execution_envelope_ref = ?",
                (execution_envelope_ref,),
            ).fetchone()
            if row is None:
                return None
            if row["logical_request_digest"] != logical_request_digest.value:
                raise DomainError(
                    ErrorCode.IDEMPOTENCY_MISMATCH,
                    "model execution reference was reused for different authorized input",
                )
            call = self._load(connection, StableId(row["model_call_id"]))
            receipt = self._load_receipt(connection, call.isolation_receipt_id)
            output = connection.execute(
                "SELECT * FROM ai_model_call_outputs WHERE model_call_id = ?",
                (call.model_call_id.value,),
            ).fetchone()
            if call.state is ModelCallState.COMPLETED and output is None:
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "completed model call is missing its recoverable output",
                )
            if call.state is not ModelCallState.COMPLETED and output is not None:
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "non-completed model call carries recoverable output",
                )
            response = self._response(output) if output is not None else None
            if response is not None and (
                call.output_digest != response.output_digest
                or call.provider_request_id != response.provider_request_id
                or call.actual_model_fingerprint != response.actual_model_fingerprint
                or call.input_tokens != response.input_tokens
                or call.output_tokens != response.output_tokens
                or call.usage_complete != response.usage_complete
            ):
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "recoverable model output disagrees with its call record",
                )
            return RecoveredModelCall(
                call=call,
                response=response,
                isolation_receipt=receipt,
            )

    def prepare(
        self,
        *,
        manifest: AuthorizedInputManifest,
        request: ProviderRequest,
        receipt: IsolationReceipt,
        provider_type: str,
        adapter_version: str,
        requested_model_ref: str,
        execution_envelope_ref: str,
        logical_request_digest: Digest,
        occurred_at: datetime,
    ) -> ModelCallRecord:
        model_call_id = self._ids.new("model_call")
        timestamp = _time(occurred_at)
        try:
            with self._database.transaction() as connection:
                connection.execute(
                    """INSERT INTO ai_isolation_receipts
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        receipt.receipt_id.value,
                        receipt.manifest_digest.value,
                        receipt.provider_request_digest.value,
                        receipt.provider_type,
                        receipt.adapter_version,
                        receipt.provider_configuration_fingerprint.value,
                        receipt.runtime_access_mode.value,
                        receipt.platform_proposal_mode.value,
                        receipt.conformance_result_ref,
                        _time(receipt.issued_at),
                        receipt.digest.value,
                    ),
                )
                connection.execute(
                    """INSERT INTO ai_model_call_roots
                       VALUES (?, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        model_call_id.value,
                        ModelCallState.PREPARED.value,
                        manifest.manifest_id.value,
                        manifest.digest.value,
                        request.digest.value,
                        receipt.receipt_id.value,
                        receipt.digest.value,
                        provider_type,
                        adapter_version,
                        requested_model_ref,
                        timestamp,
                        timestamp,
                    ),
                )
                connection.execute(
                    """INSERT INTO ai_model_call_manifests
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        model_call_id.value,
                        manifest.manifest_id.value,
                        manifest.version.value,
                        manifest.capability_id,
                        manifest.strategy_ref,
                        manifest.execution_stage,
                        manifest.calling_module,
                        manifest.proposal_vocabulary_ref,
                        manifest.digest.value,
                    ),
                )
                connection.executemany(
                    """INSERT INTO ai_model_call_manifest_items
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        (
                            model_call_id.value,
                            ordinal,
                            item.item_id,
                            item.schema_ref,
                            item.classification,
                            item.purpose,
                            item.authority_reference,
                            item.disposition.value,
                            item.content,
                            item.transformation_ref,
                            item.content_digest.value,
                        )
                        for ordinal, item in enumerate(manifest.items)
                    ),
                )
                connection.execute(
                    """INSERT INTO ai_model_call_revisions
                       VALUES (?, 1, ?, NULL, NULL, NULL, NULL, NULL, 0, NULL, ?)""",
                    (model_call_id.value, ModelCallState.PREPARED.value, timestamp),
                )
                connection.execute(
                    "INSERT INTO ai_model_call_execution_keys VALUES (?, ?, ?)",
                    (
                        execution_envelope_ref,
                        logical_request_digest.value,
                        model_call_id.value,
                    ),
                )
                return self._load(connection, model_call_id)
        except sqlite3.IntegrityError as exc:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "model call preparation violated a store invariant",
                {"sqlite_error": str(exc)},
            ) from exc

    def transition(
        self,
        *,
        model_call_id: StableId,
        expected_revision: Revision,
        target: ModelCallState,
        response: AdapterResponse | None,
        failure_code: str | None,
        provider_http_failure_evidence: ModelProviderHTTPFailureEvidence | None,
        occurred_at: datetime,
    ) -> ModelCallRecord:
        with self._database.transaction() as connection:
            root = connection.execute(
                """SELECT current_revision, current_state,
                          provider_request_digest, isolation_receipt_digest
                   FROM ai_model_call_roots WHERE model_call_id = ?""",
                (model_call_id.value,),
            ).fetchone()
            if root is None:
                raise DomainError(ErrorCode.INVALID_ARGUMENT, "model call was not found")
            if root["current_revision"] != expected_revision.value:
                raise DomainError(ErrorCode.REVISION_CONFLICT, "model call revision is stale")
            current = ModelCallState(root["current_state"])
            if target not in _ALLOWED[current]:
                raise DomainError(
                    ErrorCode.MANAGEMENT_STATE_CONFLICT,
                    f"model call cannot transition from {current.value} to {target.value}",
                )
            if target is ModelCallState.COMPLETED and response is None:
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "completed model call requires a response",
                )
            if target is not ModelCallState.COMPLETED and response is not None:
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "only a completed model call can record response fields",
                )
            if provider_http_failure_evidence is not None:
                provider_http_failure_evidence.require_exact()
            if provider_http_failure_evidence is not None and (
                target is not ModelCallState.FAILED
                or failure_code != ErrorCode.PROVIDER_HTTP_ERROR.value
                or provider_http_failure_evidence.model_call_id != model_call_id
                or provider_http_failure_evidence.provider_request_digest.value
                != root["provider_request_digest"]
                or provider_http_failure_evidence.isolation_receipt_digest.value
                != root["isolation_receipt_digest"]
            ):
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "Provider HTTP failure evidence does not bind the model call",
                )
            revision = expected_revision.next()
            if response is not None:
                connection.execute(
                    """INSERT INTO ai_model_call_outputs
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        model_call_id.value,
                        response.provider_request_id,
                        response.actual_model_fingerprint,
                        response.replay_classification.value,
                        response.output_text,
                        response.output_digest.value,
                        response.input_tokens,
                        response.output_tokens,
                        int(response.usage_complete),
                        response.termination_reason,
                        response.output_normalization,
                    ),
                )
            if provider_http_failure_evidence is not None:
                evidence = provider_http_failure_evidence
                connection.execute(
                    """INSERT INTO ai_model_call_http_failure_evidence
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        model_call_id.value,
                        evidence.schema,
                        evidence.provider_request_digest.value,
                        evidence.isolation_receipt_digest.value,
                        evidence.failure_code,
                        evidence.http_status,
                        evidence.provider_error_code,
                        evidence.provider_error_type,
                        evidence.provider_request_id,
                        evidence.digest.value,
                    ),
                )
            connection.execute(
                """INSERT INTO ai_model_call_revisions
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    model_call_id.value,
                    revision.value,
                    target.value,
                    response.actual_model_fingerprint if response else None,
                    response.provider_request_id if response else None,
                    response.output_digest.value if response else None,
                    response.input_tokens if response else None,
                    response.output_tokens if response else None,
                    int(response.usage_complete) if response else 0,
                    failure_code,
                    _time(occurred_at),
                ),
            )
            cursor = connection.execute(
                """UPDATE ai_model_call_roots
                   SET current_revision = ?, current_state = ?, revised_at = ?
                   WHERE model_call_id = ? AND current_revision = ?""",
                (
                    revision.value,
                    target.value,
                    _time(occurred_at),
                    model_call_id.value,
                    expected_revision.value,
                ),
            )
            if cursor.rowcount != 1:
                raise DomainError(ErrorCode.REVISION_CONFLICT, "model call changed before commit")
            return self._load(connection, model_call_id)

    def get(self, model_call_id: StableId) -> ModelCallRecord:
        with self._database.read() as connection:
            return self._load(connection, model_call_id)

    def recover_by_id(self, model_call_id: StableId) -> RecoveredModelCall:
        with self._database.read() as connection:
            call = self._load(connection, model_call_id)
            receipt = self._load_receipt(connection, call.isolation_receipt_id)
            row = connection.execute(
                "SELECT * FROM ai_model_call_outputs WHERE model_call_id = ?",
                (model_call_id.value,),
            ).fetchone()
            response = self._response(row) if row is not None else None
            if call.state is ModelCallState.COMPLETED and response is None:
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "completed model call is missing its recoverable output",
                )
            if call.state is not ModelCallState.COMPLETED and response is not None:
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "non-completed model call carries recoverable output",
                )
            if response is not None and (
                call.output_digest != response.output_digest
                or call.provider_request_id != response.provider_request_id
                or call.actual_model_fingerprint != response.actual_model_fingerprint
                or call.input_tokens != response.input_tokens
                or call.output_tokens != response.output_tokens
                or call.usage_complete != response.usage_complete
            ):
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "recoverable model output disagrees with its call record",
                )
            return RecoveredModelCall(call, response, receipt)

    def get_manifest(self, model_call_id: StableId) -> AuthorizedInputManifest:
        with self._database.read() as connection:
            call = self._load(connection, model_call_id)
            row = connection.execute(
                "SELECT * FROM ai_model_call_manifests WHERE model_call_id = ?",
                (model_call_id.value,),
            ).fetchone()
            if row is None:
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "model call is missing its authorized input manifest",
                )
            item_rows = connection.execute(
                """SELECT * FROM ai_model_call_manifest_items
                   WHERE model_call_id = ? ORDER BY ordinal""",
                (model_call_id.value,),
            ).fetchall()
            items = tuple(
                AuthorizedInputItem(
                    item_id=item["item_id"],
                    schema_ref=item["schema_ref"],
                    classification=item["classification"],
                    purpose=item["purpose"],
                    authority_reference=item["authority_reference"],
                    disposition=InputDisposition(item["disposition"]),
                    content=item["content"],
                    transformation_ref=item["transformation_ref"],
                    content_digest=Digest(item["content_digest"]),
                )
                for item in item_rows
            )
            manifest = AuthorizedInputManifest(
                manifest_id=StableId(row["manifest_id"]),
                version=Revision(row["version"]),
                capability_id=row["capability_id"],
                strategy_ref=row["strategy_ref"],
                execution_stage=row["execution_stage"],
                calling_module=row["calling_module"],
                proposal_vocabulary_ref=row["proposal_vocabulary_ref"],
                items=items,
                digest=Digest(row["manifest_digest"]),
            )
            core = {
                "manifest_id": manifest.manifest_id.value,
                "version": manifest.version.value,
                "capability_id": manifest.capability_id,
                "strategy_ref": manifest.strategy_ref,
                "execution_stage": manifest.execution_stage,
                "calling_module": manifest.calling_module,
                "proposal_vocabulary_ref": manifest.proposal_vocabulary_ref,
                "items": manifest.items,
            }
            if (
                manifest.manifest_id != call.manifest_id
                or manifest.digest != call.manifest_digest
                or digest_of(core) != manifest.digest
                or any(digest_of(item.content) != item.content_digest for item in items)
            ):
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "persisted authorized input manifest is inconsistent",
                )
            return manifest

    @staticmethod
    def _load_receipt(
        connection: sqlite3.Connection, receipt_id: StableId
    ) -> IsolationReceipt:
        row = connection.execute(
            "SELECT * FROM ai_isolation_receipts WHERE receipt_id = ?",
            (receipt_id.value,),
        ).fetchone()
        if row is None:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "model call isolation receipt was not found",
            )
        return IsolationReceipt(
            receipt_id=receipt_id,
            manifest_digest=Digest(row["manifest_digest"]),
            provider_request_digest=Digest(row["provider_request_digest"]),
            provider_type=row["provider_type"],
            adapter_version=row["adapter_version"],
            provider_configuration_fingerprint=Digest(
                row["configuration_fingerprint"]
            ),
            runtime_access_mode=RuntimeAccessMode(row["runtime_access_mode"]),
            platform_proposal_mode=PlatformProposalMode(
                row["platform_proposal_mode"]
            ),
            conformance_result_ref=row["conformance_result_ref"],
            issued_at=_parse_time(row["issued_at"]),
            digest=Digest(row["receipt_digest"]),
        )

    @staticmethod
    def _response(row: sqlite3.Row) -> AdapterResponse:
        response = AdapterResponse(
            provider_request_id=row["provider_request_id"],
            actual_model_fingerprint=row["actual_model_fingerprint"],
            replay_classification=ReplayClassification(
                row["replay_classification"]
            ),
            output_text=row["output_text"],
            output_digest=Digest(row["output_digest"]),
            input_tokens=row["input_tokens"],
            output_tokens=row["output_tokens"],
            usage_complete=bool(row["usage_complete"]),
            termination_reason=row["termination_reason"],
            output_normalization=row["output_normalization"],
        )
        if digest_of(response.output_text) != response.output_digest:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "recovered model output digest is inconsistent",
            )
        return response

    @staticmethod
    def _load(connection: sqlite3.Connection, model_call_id: StableId) -> ModelCallRecord:
        row = connection.execute(
            """SELECT root.*, revision.actual_model_fingerprint,
                      revision.provider_request_id, revision.output_digest,
                      revision.input_tokens, revision.output_tokens,
                      revision.usage_complete, revision.failure_code
               FROM ai_model_call_roots AS root
               JOIN ai_model_call_revisions AS revision
                 ON revision.model_call_id = root.model_call_id
                AND revision.revision = root.current_revision
               WHERE root.model_call_id = ?""",
            (model_call_id.value,),
        ).fetchone()
        if row is None:
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "model call was not found")
        evidence_row = connection.execute(
            "SELECT * FROM ai_model_call_http_failure_evidence WHERE model_call_id = ?",
            (model_call_id.value,),
        ).fetchone()
        evidence = None
        if evidence_row is not None:
            evidence = ModelProviderHTTPFailureEvidence(
                schema=evidence_row["schema_ref"],
                model_call_id=model_call_id,
                provider_request_digest=Digest(
                    evidence_row["provider_request_digest"]
                ),
                isolation_receipt_digest=Digest(
                    evidence_row["isolation_receipt_digest"]
                ),
                failure_code=evidence_row["failure_code"],
                http_status=evidence_row["http_status"],
                provider_error_code=evidence_row["provider_error_code"],
                provider_error_type=evidence_row["provider_error_type"],
                provider_request_id=evidence_row["provider_request_id"],
                digest=Digest(evidence_row["evidence_digest"]),
            )
            evidence.require_exact()
            if (
                row["current_state"] != ModelCallState.FAILED.value
                or row["failure_code"] != ErrorCode.PROVIDER_HTTP_ERROR.value
                or evidence.provider_request_digest.value
                != row["provider_request_digest"]
                or evidence.isolation_receipt_digest.value
                != row["isolation_receipt_digest"]
            ):
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "stored Provider HTTP failure evidence does not bind its model call",
                )
        return ModelCallRecord(
            model_call_id=model_call_id,
            revision=Revision(row["current_revision"]),
            state=ModelCallState(row["current_state"]),
            manifest_id=StableId(row["manifest_id"]),
            manifest_digest=Digest(row["manifest_digest"]),
            provider_request_digest=Digest(row["provider_request_digest"]),
            isolation_receipt_id=StableId(row["isolation_receipt_id"]),
            isolation_receipt_digest=Digest(row["isolation_receipt_digest"]),
            provider_type=row["provider_type"],
            adapter_version=row["adapter_version"],
            requested_model_ref=row["requested_model_ref"],
            actual_model_fingerprint=row["actual_model_fingerprint"],
            provider_request_id=row["provider_request_id"],
            output_digest=Digest(row["output_digest"]) if row["output_digest"] else None,
            input_tokens=row["input_tokens"],
            output_tokens=row["output_tokens"],
            usage_complete=bool(row["usage_complete"]),
            failure_code=row["failure_code"],
            provider_http_failure_evidence=evidence,
            created_at=_parse_time(row["created_at"]),
            revised_at=_parse_time(row["revised_at"]),
        )


_ALLOWED = {
    ModelCallState.PREPARED: {
        ModelCallState.DISPATCHED,
        ModelCallState.CANCELLED_BEFORE_DISPATCH,
    },
    ModelCallState.DISPATCHED: {
        ModelCallState.COMPLETED,
        ModelCallState.FAILED,
        ModelCallState.OUTCOME_UNKNOWN,
    },
    ModelCallState.OUTCOME_UNKNOWN: {ModelCallState.COMPLETED, ModelCallState.FAILED},
    ModelCallState.COMPLETED: set(),
    ModelCallState.FAILED: set(),
    ModelCallState.CANCELLED_BEFORE_DISPATCH: set(),
}


def _time(value: datetime) -> str:
    return value.isoformat(timespec="microseconds")


def _parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value)
