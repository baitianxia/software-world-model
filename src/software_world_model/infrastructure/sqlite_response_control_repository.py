"""SQLite Response Control store for candidates, review, authorization, and delivery."""

from __future__ import annotations

from datetime import datetime
import json

from software_world_model.application_services.response_control import (
    AdapterDeliveryReceipt,
    AnswerCandidate,
    AnswerClaim,
    AnswerClaimKind,
    AnswerReviewResult,
    DeliveryState,
    FinalResponseAuthorization,
    LogicalDelivery,
    RequirementCoverage,
    ResponseControlRepository,
    ResponseKind,
    ReviewDecision,
    ReviewDimension,
    ReviewMatrixCell,
    ReviewOutcome,
)
from software_world_model.application_services.task_control import ConversationalTask
from software_world_model.application_services.knowledge_use import NeedStatus
from software_world_model.cross_cutting import (
    Digest,
    DomainError,
    ErrorCode,
    IdGenerator,
    StableId,
    Uuid4IdGenerator,
    canonical_json_bytes,
    digest_of,
)

from .sqlite_database import SqliteDatabase


_SCHEMA = """
CREATE TABLE IF NOT EXISTS app_answer_candidates (
    candidate_id TEXT PRIMARY KEY,
    candidate_digest TEXT NOT NULL,
    payload_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS app_answer_reviews (
    review_id TEXT PRIMARY KEY,
    candidate_id TEXT NOT NULL UNIQUE,
    review_digest TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    FOREIGN KEY (candidate_id) REFERENCES app_answer_candidates(candidate_id)
);
CREATE TABLE IF NOT EXISTS app_response_authorizations (
    authorization_id TEXT PRIMARY KEY,
    candidate_id TEXT NOT NULL UNIQUE,
    authorization_digest TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    FOREIGN KEY (candidate_id) REFERENCES app_answer_candidates(candidate_id)
);
CREATE TABLE IF NOT EXISTS app_logical_deliveries (
    delivery_id TEXT PRIMARY KEY,
    conversation_ref TEXT NOT NULL,
    turn_ref TEXT NOT NULL,
    request_ref TEXT NOT NULL,
    adapter_idempotency_key TEXT NOT NULL UNIQUE,
    candidate_id TEXT NOT NULL,
    authorization_id TEXT NOT NULL,
    body_digest TEXT NOT NULL,
    revision INTEGER NOT NULL,
    state TEXT NOT NULL,
    receipt_json TEXT,
    failure_code TEXT,
    created_at TEXT NOT NULL,
    revised_at TEXT NOT NULL,
    UNIQUE (conversation_ref, turn_ref, request_ref),
    FOREIGN KEY (candidate_id) REFERENCES app_answer_candidates(candidate_id),
    FOREIGN KEY (authorization_id) REFERENCES app_response_authorizations(authorization_id)
);
"""


class SqliteResponseControlRepository(ResponseControlRepository):
    def __init__(self, database: SqliteDatabase, *, id_generator: IdGenerator | None = None) -> None:
        self._database = database
        self._ids = id_generator or Uuid4IdGenerator()
        self._database.executescript(_SCHEMA)

    def get_candidate(self, candidate_id: StableId) -> AnswerCandidate:
        with self._database.read() as connection:
            row = connection.execute(
                "SELECT payload_json FROM app_answer_candidates WHERE candidate_id = ?",
                (candidate_id.value,),
            ).fetchone()
            if row is None:
                raise DomainError(ErrorCode.INVALID_ARGUMENT, "answer candidate was not found")
            return _candidate(json.loads(row["payload_json"]))

    def get_review_for_candidate(
        self, candidate_id: StableId
    ) -> AnswerReviewResult | None:
        with self._database.read() as connection:
            row = connection.execute(
                "SELECT payload_json FROM app_answer_reviews WHERE candidate_id = ?",
                (candidate_id.value,),
            ).fetchone()
            return _review(json.loads(row["payload_json"])) if row else None

    def get_authorization_for_candidate(
        self, candidate_id: StableId
    ) -> FinalResponseAuthorization | None:
        with self._database.read() as connection:
            row = connection.execute(
                """SELECT payload_json FROM app_response_authorizations
                   WHERE candidate_id = ?""",
                (candidate_id.value,),
            ).fetchone()
            return _authorization(json.loads(row["payload_json"])) if row else None

    def save_candidate(self, candidate: AnswerCandidate) -> AnswerCandidate:
        with self._database.transaction() as connection:
            row = connection.execute(
                "SELECT * FROM app_answer_candidates WHERE candidate_id = ?",
                (candidate.candidate_id.value,),
            ).fetchone()
            if row is not None:
                if row["candidate_digest"] != candidate.digest.value:
                    raise DomainError(ErrorCode.AUTHORITY_RECORD_INCONSISTENT, "candidate identity conflict")
                return _candidate(json.loads(row["payload_json"]))
            connection.execute(
                "INSERT INTO app_answer_candidates VALUES (?, ?, ?)",
                (candidate.candidate_id.value, candidate.digest.value, _json(_candidate_payload(candidate))),
            )
            return candidate

    def save_review(self, review: AnswerReviewResult) -> AnswerReviewResult:
        with self._database.transaction() as connection:
            row = connection.execute(
                "SELECT * FROM app_answer_reviews WHERE candidate_id = ?", (review.candidate_id.value,)
            ).fetchone()
            if row is not None:
                if row["review_digest"] != review.digest.value:
                    raise DomainError(ErrorCode.AUTHORITY_RECORD_INCONSISTENT, "candidate has another review")
                return _review(json.loads(row["payload_json"]))
            connection.execute(
                "INSERT INTO app_answer_reviews VALUES (?, ?, ?, ?)",
                (review.review_id.value, review.candidate_id.value, review.digest.value, _json(_review_payload(review))),
            )
            return review

    def save_authorization(
        self, authorization: FinalResponseAuthorization
    ) -> FinalResponseAuthorization:
        with self._database.transaction() as connection:
            row = connection.execute(
                "SELECT * FROM app_response_authorizations WHERE candidate_id = ?",
                (authorization.candidate_id.value,),
            ).fetchone()
            if row is not None:
                if row["authorization_digest"] != authorization.digest.value:
                    raise DomainError(ErrorCode.AUTHORITY_RECORD_INCONSISTENT, "candidate has another authorization")
                return _authorization(json.loads(row["payload_json"]))
            connection.execute(
                "INSERT INTO app_response_authorizations VALUES (?, ?, ?, ?)",
                (
                    authorization.authorization_id.value,
                    authorization.candidate_id.value,
                    authorization.digest.value,
                    _json(_authorization_payload(authorization)),
                ),
            )
            return authorization

    def prepare_delivery(
        self,
        *,
        task: ConversationalTask,
        candidate: AnswerCandidate,
        authorization: FinalResponseAuthorization,
        occurred_at: datetime,
    ) -> LogicalDelivery:
        with self._database.transaction() as connection:
            row = connection.execute(
                """SELECT * FROM app_logical_deliveries
                   WHERE conversation_ref = ? AND turn_ref = ? AND request_ref = ?""",
                (task.conversation_ref, task.turn_ref, task.request_ref),
            ).fetchone()
            if row is not None:
                if (
                    row["candidate_id"] != candidate.candidate_id.value
                    or row["authorization_id"] != authorization.authorization_id.value
                    or row["body_digest"] != digest_of(candidate.body).value
                ):
                    raise DomainError(
                        ErrorCode.IDEMPOTENCY_MISMATCH,
                        "logical response already binds another immutable body",
                    )
                return _delivery(row)
            delivery_id = self._ids.new("logical_delivery")
            key_digest = digest_of(
                {
                    "conversation": task.conversation_ref,
                    "turn": task.turn_ref,
                    "request": task.request_ref,
                }
            )
            adapter_key = f"response:{key_digest.value[-32:]}"
            timestamp = _time(occurred_at)
            connection.execute(
                "INSERT INTO app_logical_deliveries VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?, NULL, NULL, ?, ?)",
                (
                    delivery_id.value,
                    task.conversation_ref,
                    task.turn_ref,
                    task.request_ref,
                    adapter_key,
                    candidate.candidate_id.value,
                    authorization.authorization_id.value,
                    digest_of(candidate.body).value,
                    DeliveryState.PREPARED.value,
                    timestamp,
                    timestamp,
                ),
            )
            return _delivery(connection.execute("SELECT * FROM app_logical_deliveries WHERE delivery_id = ?", (delivery_id.value,)).fetchone())

    def transition_delivery(
        self,
        *,
        delivery_id: StableId,
        expected_revision: int,
        target: DeliveryState,
        receipt: AdapterDeliveryReceipt | None,
        failure_code: str | None,
        occurred_at: datetime,
    ) -> LogicalDelivery:
        with self._database.transaction() as connection:
            row = connection.execute(
                "SELECT * FROM app_logical_deliveries WHERE delivery_id = ?", (delivery_id.value,)
            ).fetchone()
            if row is None or row["revision"] != expected_revision:
                raise DomainError(ErrorCode.REVISION_CONFLICT, "delivery revision is stale")
            current = DeliveryState(row["state"])
            if target not in _DELIVERY_TRANSITIONS[current]:
                raise DomainError(ErrorCode.MANAGEMENT_STATE_CONFLICT, "invalid delivery transition")
            if target is DeliveryState.DELIVERED and receipt is None:
                raise DomainError(ErrorCode.AUTHORITY_RECORD_INCONSISTENT, "delivered state requires receipt")
            connection.execute(
                """UPDATE app_logical_deliveries SET revision = revision + 1,
                   state = ?, receipt_json = ?, failure_code = ?, revised_at = ? WHERE delivery_id = ?""",
                (
                    target.value,
                    _json(_receipt_payload(receipt)) if receipt else None,
                    failure_code,
                    _time(occurred_at),
                    delivery_id.value,
                ),
            )
            return _delivery(connection.execute("SELECT * FROM app_logical_deliveries WHERE delivery_id = ?", (delivery_id.value,)).fetchone())


_DELIVERY_TRANSITIONS = {
    DeliveryState.PREPARED: {DeliveryState.SENDING, DeliveryState.CANCELED_BEFORE_DISPATCH},
    DeliveryState.SENDING: {DeliveryState.DELIVERED, DeliveryState.FAILED, DeliveryState.OUTCOME_PENDING},
    DeliveryState.OUTCOME_PENDING: {DeliveryState.DELIVERED, DeliveryState.FAILED},
    DeliveryState.DELIVERED: set(),
    DeliveryState.FAILED: set(),
    DeliveryState.CANCELED_BEFORE_DISPATCH: set(),
}


def _claim_payload(value: AnswerClaim) -> dict[str, object]:
    return {
        "claim_id": value.claim_id,
        "need_id": value.need_id,
        "kind": value.kind.value,
        "text": value.text,
        "formal_reference": value.formal_reference.value if value.formal_reference else None,
        "formal_digest": value.formal_digest.value if value.formal_digest else None,
        "support_proof_id": value.support_proof_id.value if value.support_proof_id else None,
        "gap": value.gap,
    }


def _candidate_payload(value: AnswerCandidate) -> dict[str, object]:
    return {
        "candidate_id": value.candidate_id.value,
        "revision": value.revision,
        "task_id": value.task_id.value,
        "source_task_revision": value.source_task_revision,
        "source_orchestration_revision": value.source_orchestration_revision,
        "requirement_id": value.requirement_id.value,
        "requirement_revision": value.requirement_revision,
        "assessment_id": value.assessment_id.value,
        "read_session_id": value.read_session_id.value,
        "snapshot_id": value.snapshot_id.value,
        "response_kind": value.response_kind.value,
        "body": value.body,
        "claims": [_claim_payload(item) for item in value.claims],
        "coverage": [
            {"need_id": item.need_id, "claim_ids": item.claim_ids, "decision": item.decision.value}
            for item in value.coverage
        ],
        "digest": value.digest.value,
        "sealed_at": _time(value.sealed_at),
    }


def _candidate(value: dict[str, object]) -> AnswerCandidate:
    return AnswerCandidate(
        candidate_id=StableId(value["candidate_id"]),
        revision=value["revision"],
        task_id=StableId(value["task_id"]),
        source_task_revision=value["source_task_revision"],
        source_orchestration_revision=value["source_orchestration_revision"],
        requirement_id=StableId(value["requirement_id"]),
        requirement_revision=value["requirement_revision"],
        assessment_id=StableId(value["assessment_id"]),
        read_session_id=StableId(value["read_session_id"]),
        snapshot_id=StableId(value["snapshot_id"]),
        response_kind=ResponseKind(value["response_kind"]),
        body=value["body"],
        claims=tuple(
            AnswerClaim(
                claim_id=item["claim_id"], need_id=item["need_id"], kind=AnswerClaimKind(item["kind"]),
                text=item["text"], formal_reference=StableId(item["formal_reference"]) if item["formal_reference"] else None,
                formal_digest=Digest(item["formal_digest"]) if item["formal_digest"] else None,
                support_proof_id=StableId(item["support_proof_id"]) if item["support_proof_id"] else None,
                gap=item["gap"],
            ) for item in value["claims"]
        ),
        coverage=tuple(
            RequirementCoverage(item["need_id"], tuple(item["claim_ids"]), NeedStatus(item["decision"]))
            for item in value["coverage"]
        ),
        digest=Digest(value["digest"]),
        sealed_at=_parse_time(value["sealed_at"]),
    )


def _review_payload(value: AnswerReviewResult) -> dict[str, object]:
    return {
        "review_id": value.review_id.value, "candidate_id": value.candidate_id.value,
        "candidate_digest": value.candidate_digest.value,
        "matrix": [
            {"claim_id": item.claim_id, "dimension": item.dimension.value, "outcome": item.outcome.value,
             "finding": item.finding, "authority_references": [ref.value for ref in item.authority_references]}
            for item in value.matrix
        ],
        "decision": value.decision.value, "task_validation_digest": value.task_validation_digest.value,
        "digest": value.digest.value, "reviewed_at": _time(value.reviewed_at),
    }


def _review(value: dict[str, object]) -> AnswerReviewResult:
    return AnswerReviewResult(
        review_id=StableId(value["review_id"]), candidate_id=StableId(value["candidate_id"]),
        candidate_digest=Digest(value["candidate_digest"]),
        matrix=tuple(ReviewMatrixCell(item["claim_id"], ReviewDimension(item["dimension"]), ReviewOutcome(item["outcome"]), item["finding"], tuple(StableId(ref) for ref in item["authority_references"])) for item in value["matrix"]),
        decision=ReviewDecision(value["decision"]), task_validation_digest=Digest(value["task_validation_digest"]),
        digest=Digest(value["digest"]), reviewed_at=_parse_time(value["reviewed_at"]),
    )


def _authorization_payload(value: FinalResponseAuthorization) -> dict[str, object]:
    return {
        "authorization_id": value.authorization_id.value, "task_id": value.task_id.value,
        "task_revision": value.task_revision, "orchestration_revision": value.orchestration_revision,
        "candidate_id": value.candidate_id.value, "candidate_digest": value.candidate_digest.value,
        "review_id": value.review_id.value, "review_digest": value.review_digest.value,
        "task_validation_digest": value.task_validation_digest.value, "classification": value.classification,
        "digest": value.digest.value, "authorized_at": _time(value.authorized_at),
    }


def _authorization(value: dict[str, object]) -> FinalResponseAuthorization:
    return FinalResponseAuthorization(
        authorization_id=StableId(value["authorization_id"]), task_id=StableId(value["task_id"]),
        task_revision=value["task_revision"], orchestration_revision=value["orchestration_revision"],
        candidate_id=StableId(value["candidate_id"]), candidate_digest=Digest(value["candidate_digest"]),
        review_id=StableId(value["review_id"]), review_digest=Digest(value["review_digest"]),
        task_validation_digest=Digest(value["task_validation_digest"]), classification=value["classification"],
        digest=Digest(value["digest"]), authorized_at=_parse_time(value["authorized_at"]),
    )


def _receipt_payload(value: AdapterDeliveryReceipt) -> dict[str, object]:
    return {
        "adapter_receipt_id": value.adapter_receipt_id,
        "adapter_idempotency_key": value.adapter_idempotency_key,
        "body_digest": value.body_digest.value,
        "accepted": value.accepted,
        "provider_reference": value.provider_reference,
        "digest": value.digest.value,
    }


def _receipt(value: dict[str, object]) -> AdapterDeliveryReceipt:
    return AdapterDeliveryReceipt(
        adapter_receipt_id=value["adapter_receipt_id"], adapter_idempotency_key=value["adapter_idempotency_key"],
        body_digest=Digest(value["body_digest"]), accepted=value["accepted"],
        provider_reference=value["provider_reference"], digest=Digest(value["digest"]),
    )


def _delivery(row: object) -> LogicalDelivery:
    return LogicalDelivery(
        delivery_id=StableId(row["delivery_id"]), conversation_ref=row["conversation_ref"],
        turn_ref=row["turn_ref"], request_ref=row["request_ref"],
        adapter_idempotency_key=row["adapter_idempotency_key"], candidate_id=StableId(row["candidate_id"]),
        authorization_id=StableId(row["authorization_id"]), body_digest=Digest(row["body_digest"]),
        revision=row["revision"], state=DeliveryState(row["state"]),
        receipt=_receipt(json.loads(row["receipt_json"])) if row["receipt_json"] else None,
        failure_code=row["failure_code"], created_at=_parse_time(row["created_at"]),
        revised_at=_parse_time(row["revised_at"]),
    )


def _json(value: object) -> str:
    return canonical_json_bytes(value).decode("utf-8")


def _time(value: datetime) -> str:
    return value.isoformat(timespec="microseconds")


def _parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value)
