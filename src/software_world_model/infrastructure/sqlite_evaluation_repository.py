"""SQLite authority store for Capability Evaluation evidence and validity."""

from __future__ import annotations

from datetime import datetime, timedelta
import json
import sqlite3

from software_world_model.application_services.activation import QualificationProof
from software_world_model.application_services.evaluation import (
    CaseExecutionEvidence,
    EvaluationAttemptState,
    EvaluationCaseAttempt,
    EvaluationCaseDefinition,
    EvaluationCompletion,
    EvaluationConclusion,
    EvaluationQualificationDependencies,
    EvaluationDefinition,
    EvaluationResult,
    EvaluationRun,
    EvaluationRunState,
    EvaluationValidityDecision,
    EvaluationValidityStatus,
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
CREATE TABLE IF NOT EXISTS app_evaluation_definitions (
    evaluation_id TEXT NOT NULL,
    evaluation_version TEXT NOT NULL,
    definition_digest TEXT NOT NULL UNIQUE,
    definition_json TEXT NOT NULL,
    PRIMARY KEY (evaluation_id, evaluation_version)
);

CREATE TABLE IF NOT EXISTS app_evaluation_runs (
    run_id TEXT PRIMARY KEY,
    definition_digest TEXT NOT NULL,
    evaluation_id TEXT NOT NULL,
    evaluation_version TEXT NOT NULL,
    strategy_id TEXT NOT NULL,
    strategy_version TEXT NOT NULL,
    evaluation_sink_ref TEXT NOT NULL,
    root_allocation_ref TEXT NOT NULL,
    qualification_json TEXT NOT NULL,
    qualification_digest TEXT NOT NULL,
    request_digest TEXT NOT NULL,
    current_revision INTEGER NOT NULL CHECK (current_revision >= 1),
    current_state TEXT NOT NULL,
    created_at TEXT NOT NULL,
    revised_at TEXT NOT NULL,
    FOREIGN KEY (definition_digest) REFERENCES app_evaluation_definitions(definition_digest)
);

CREATE TABLE IF NOT EXISTS app_evaluation_run_revisions (
    run_id TEXT NOT NULL,
    revision INTEGER NOT NULL CHECK (revision >= 1),
    state TEXT NOT NULL,
    occurred_at TEXT NOT NULL,
    PRIMARY KEY (run_id, revision),
    FOREIGN KEY (run_id) REFERENCES app_evaluation_runs(run_id)
);

CREATE TABLE IF NOT EXISTS app_evaluation_run_idempotency (
    idempotency_key TEXT PRIMARY KEY,
    command_type TEXT NOT NULL,
    request_digest TEXT NOT NULL,
    run_id TEXT NOT NULL,
    FOREIGN KEY (run_id) REFERENCES app_evaluation_runs(run_id)
);

CREATE TABLE IF NOT EXISTS app_evaluation_attempts (
    attempt_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    case_id TEXT NOT NULL,
    attempt_key TEXT NOT NULL UNIQUE,
    request_digest TEXT NOT NULL,
    current_revision INTEGER NOT NULL CHECK (current_revision >= 1),
    current_state TEXT NOT NULL,
    created_at TEXT NOT NULL,
    revised_at TEXT NOT NULL,
    FOREIGN KEY (run_id) REFERENCES app_evaluation_runs(run_id)
);

CREATE TABLE IF NOT EXISTS app_evaluation_attempt_revisions (
    attempt_id TEXT NOT NULL,
    revision INTEGER NOT NULL CHECK (revision >= 1),
    state TEXT NOT NULL,
    conclusion TEXT,
    output_ref TEXT,
    output_digest TEXT,
    sink_manifest_ref TEXT,
    sink_manifest_digest TEXT,
    oracle_ref TEXT,
    oracle_digest TEXT,
    actual_model_fingerprint TEXT,
    provider_request_id TEXT,
    input_tokens INTEGER,
    output_tokens INTEGER,
    usage_complete INTEGER NOT NULL CHECK (usage_complete IN (0, 1)),
    failure_code TEXT,
    occurred_at TEXT NOT NULL,
    PRIMARY KEY (attempt_id, revision),
    FOREIGN KEY (attempt_id) REFERENCES app_evaluation_attempts(attempt_id)
);

CREATE TABLE IF NOT EXISTS app_evaluation_results (
    result_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL UNIQUE,
    definition_digest TEXT NOT NULL,
    conclusion TEXT NOT NULL,
    case_attempt_ids_json TEXT NOT NULL,
    passed_case_ids_json TEXT NOT NULL,
    failed_case_ids_json TEXT NOT NULL,
    inconclusive_case_ids_json TEXT NOT NULL,
    actual_model_fingerprints_json TEXT NOT NULL,
    input_tokens INTEGER NOT NULL,
    output_tokens INTEGER NOT NULL,
    completed_at TEXT NOT NULL,
    result_digest TEXT NOT NULL UNIQUE,
    FOREIGN KEY (run_id) REFERENCES app_evaluation_runs(run_id)
);

CREATE TABLE IF NOT EXISTS app_evaluation_validity_roots (
    result_id TEXT PRIMARY KEY,
    validity_id TEXT NOT NULL UNIQUE,
    current_revision INTEGER NOT NULL CHECK (current_revision >= 1),
    current_status TEXT NOT NULL,
    FOREIGN KEY (result_id) REFERENCES app_evaluation_results(result_id)
);

CREATE TABLE IF NOT EXISTS app_evaluation_validity_decisions (
    validity_id TEXT NOT NULL,
    result_id TEXT NOT NULL,
    revision INTEGER NOT NULL CHECK (revision >= 1),
    status TEXT NOT NULL,
    dependency_digest TEXT NOT NULL,
    valid_until TEXT NOT NULL,
    authority TEXT NOT NULL,
    reason TEXT NOT NULL,
    decided_at TEXT NOT NULL,
    decision_digest TEXT NOT NULL,
    PRIMARY KEY (validity_id, revision),
    FOREIGN KEY (result_id) REFERENCES app_evaluation_results(result_id)
);
"""


class SqliteCapabilityEvaluationRepository:
    def __init__(self, database: SqliteDatabase, *, id_generator: IdGenerator | None = None) -> None:
        self._database = database
        self._ids = id_generator or Uuid4IdGenerator()
        self._database.executescript(_SCHEMA)

    def register_definition(self, definition: EvaluationDefinition) -> EvaluationDefinition:
        payload = canonical_json_bytes(_definition_core(definition)).decode("utf-8")
        try:
            with self._database.transaction() as connection:
                row = connection.execute(
                    """SELECT definition_digest, definition_json
                       FROM app_evaluation_definitions
                       WHERE evaluation_id = ? AND evaluation_version = ?""",
                    (definition.evaluation_id, definition.evaluation_version),
                ).fetchone()
                if row is not None:
                    if row["definition_digest"] != definition.digest.value:
                        raise DomainError(
                            ErrorCode.EVALUATION_DEFINITION_INVALID,
                            "evaluation version was registered with different semantics",
                        )
                    return self._decode_definition(row["definition_json"], row["definition_digest"])
                connection.execute(
                    "INSERT INTO app_evaluation_definitions VALUES (?, ?, ?, ?)",
                    (
                        definition.evaluation_id,
                        definition.evaluation_version,
                        definition.digest.value,
                        payload,
                    ),
                )
                return definition
        except DomainError:
            raise
        except sqlite3.IntegrityError as exc:
            raise DomainError(
                ErrorCode.EVALUATION_DEFINITION_INVALID,
                "evaluation definition violated a store invariant",
            ) from exc

    def prepare_run(
        self,
        *,
        definition: EvaluationDefinition,
        evaluation_sink_ref: str,
        root_allocation_ref: str,
        idempotency_key: IdempotencyKey,
        request_digest: Digest,
        actor: str,
        correlation_ref: CorrelationRef,
        occurred_at: datetime,
    ) -> EvaluationRun:
        with self._database.transaction() as connection:
            replay = connection.execute(
                """SELECT command_type, request_digest, run_id
                   FROM app_evaluation_run_idempotency WHERE idempotency_key = ?""",
                (idempotency_key.value,),
            ).fetchone()
            if replay is not None:
                if replay["command_type"] != "PrepareEvaluationRun@1" or replay["request_digest"] != request_digest.value:
                    raise DomainError(
                        ErrorCode.IDEMPOTENCY_MISMATCH,
                        "evaluation run idempotency key was reused for a different request",
                    )
                return self._load_run(connection, StableId(replay["run_id"]))
            registered = connection.execute(
                "SELECT definition_digest FROM app_evaluation_definitions WHERE evaluation_id = ? AND evaluation_version = ?",
                (definition.evaluation_id, definition.evaluation_version),
            ).fetchone()
            if registered is None or registered["definition_digest"] != definition.digest.value:
                raise DomainError(
                    ErrorCode.EVALUATION_DEFINITION_INVALID,
                    "exact evaluation definition is not registered",
                )
            run_id = self._ids.new("evaluation_run")
            proof_core = {
                "proof_ref": f"evaluation-only:{run_id.value}",
                "capability_id": definition.capability_id,
                "capability_contract_version": definition.capability_contract_version,
                "strategy_id": definition.strategy_id,
                "strategy_version": definition.strategy_version,
                "result_ref": run_id.value,
                "validity_ref": evaluation_sink_ref,
                "qualification_kind": "EVALUATION_ONLY",
            }
            proof = QualificationProof(**proof_core, digest=digest_of(proof_core))
            timestamp = _time(occurred_at)
            connection.execute(
                """INSERT INTO app_evaluation_runs
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?)""",
                (
                    run_id.value,
                    definition.digest.value,
                    definition.evaluation_id,
                    definition.evaluation_version,
                    definition.strategy_id,
                    definition.strategy_version,
                    evaluation_sink_ref,
                    root_allocation_ref,
                    canonical_json_bytes(proof.core()).decode("utf-8"),
                    proof.digest.value,
                    request_digest.value,
                    EvaluationRunState.PREPARED.value,
                    timestamp,
                    timestamp,
                ),
            )
            connection.execute(
                "INSERT INTO app_evaluation_run_revisions VALUES (?, 1, ?, ?)",
                (run_id.value, EvaluationRunState.PREPARED.value, timestamp),
            )
            connection.execute(
                "INSERT INTO app_evaluation_run_idempotency VALUES (?, ?, ?, ?)",
                (
                    idempotency_key.value,
                    "PrepareEvaluationRun@1",
                    request_digest.value,
                    run_id.value,
                ),
            )
            return self._load_run(connection, run_id)

    def start_run(
        self, *, run_id: StableId, expected_revision: Revision, occurred_at: datetime
    ) -> EvaluationRun:
        with self._database.transaction() as connection:
            run = self._load_run(connection, run_id)
            if run.revision != expected_revision or run.state is not EvaluationRunState.PREPARED:
                raise DomainError(ErrorCode.EVALUATION_RUN_CONFLICT, "evaluation run cannot start")
            return self._transition_run(
                connection, run, EvaluationRunState.RUNNING, occurred_at
            )

    def dispatch_case(
        self,
        *,
        run_id: StableId,
        expected_run_revision: Revision,
        case_id: str,
        attempt_key: str,
        request_digest: Digest,
        occurred_at: datetime,
    ) -> tuple[EvaluationRun, EvaluationCaseAttempt]:
        with self._database.transaction() as connection:
            replay = connection.execute(
                "SELECT attempt_id, run_id, request_digest FROM app_evaluation_attempts WHERE attempt_key = ?",
                (attempt_key,),
            ).fetchone()
            if replay is not None:
                if replay["run_id"] != run_id.value or replay["request_digest"] != request_digest.value:
                    raise DomainError(
                        ErrorCode.IDEMPOTENCY_MISMATCH,
                        "evaluation attempt key was reused for another request",
                    )
                return self._load_run(connection, run_id), self._load_attempt(
                    connection, StableId(replay["attempt_id"])
                )
            run = self._load_run(connection, run_id)
            if run.revision != expected_run_revision or run.state is not EvaluationRunState.RUNNING:
                raise DomainError(
                    ErrorCode.EVALUATION_RUN_CONFLICT,
                    "evaluation run is not dispatchable at the expected revision",
                )
            definition = self._load_definition_by_digest(connection, run.definition_digest)
            if case_id not in {item.case_id for item in definition.cases}:
                raise DomainError(
                    ErrorCode.EVALUATION_DEFINITION_INVALID,
                    "evaluation case is not part of the frozen definition",
                )
            succeeded = connection.execute(
                """SELECT 1 FROM app_evaluation_attempts
                   WHERE run_id = ? AND case_id = ? AND current_state = ?""",
                (run_id.value, case_id, EvaluationAttemptState.SUCCEEDED.value),
            ).fetchone()
            if succeeded is not None:
                raise DomainError(
                    ErrorCode.EVALUATION_RUN_CONFLICT,
                    "evaluation case already has a successful attempt",
                )
            attempt_id = self._ids.new("evaluation_attempt")
            timestamp = _time(occurred_at)
            connection.execute(
                """INSERT INTO app_evaluation_attempts
                   VALUES (?, ?, ?, ?, ?, 1, ?, ?, ?)""",
                (
                    attempt_id.value,
                    run_id.value,
                    case_id,
                    attempt_key,
                    request_digest.value,
                    EvaluationAttemptState.DISPATCHED.value,
                    timestamp,
                    timestamp,
                ),
            )
            self._insert_attempt_revision(
                connection,
                attempt_id=attempt_id,
                revision=Revision(1),
                state=EvaluationAttemptState.DISPATCHED,
                evidence=None,
                provider_request_id=None,
                failure_code=None,
                occurred_at=occurred_at,
            )
            revised_run = self._transition_run(
                connection, run, EvaluationRunState.RUNNING, occurred_at
            )
            return revised_run, self._load_attempt(connection, attempt_id)

    def complete_case(
        self,
        *,
        attempt_id: StableId,
        expected_attempt_revision: Revision,
        evidence: CaseExecutionEvidence,
        occurred_at: datetime,
    ) -> EvaluationCaseAttempt:
        with self._database.transaction() as connection:
            attempt = self._load_attempt(connection, attempt_id)
            if attempt.revision != expected_attempt_revision or attempt.state not in {
                EvaluationAttemptState.DISPATCHED,
                EvaluationAttemptState.OUTCOME_UNKNOWN,
            }:
                raise DomainError(ErrorCode.EVALUATION_RUN_CONFLICT, "case attempt cannot complete")
            run = self._load_run(connection, attempt.run_id)
            definition = self._load_definition_by_digest(connection, run.definition_digest)
            case = next(item for item in definition.cases if item.case_id == attempt.case_id)
            if evidence.oracle_ref != case.oracle_ref or evidence.oracle_digest != case.oracle_digest:
                raise DomainError(
                    ErrorCode.ORACLE_UNAVAILABLE,
                    "case evidence does not use the frozen independent oracle",
                )
            if evidence.actual_model_fingerprint != definition.model_ref:
                raise DomainError(
                    ErrorCode.QUALIFICATION_INVALID,
                    "case used a model fingerprint outside the frozen definition",
                )
            if not evidence.usage_complete:
                raise DomainError(
                    ErrorCode.EVALUATION_RUN_CONFLICT,
                    "case usage is incomplete",
                )
            revised = self._transition_attempt(
                connection,
                attempt,
                EvaluationAttemptState.SUCCEEDED,
                occurred_at,
                evidence=evidence,
            )
            if attempt.state is EvaluationAttemptState.OUTCOME_UNKNOWN:
                self._restore_run_after_unknown(connection, attempt.run_id, occurred_at)
            return revised

    def mark_case_outcome_unknown(
        self,
        *,
        attempt_id: StableId,
        expected_attempt_revision: Revision,
        provider_request_id: str | None,
        occurred_at: datetime,
    ) -> EvaluationCaseAttempt:
        with self._database.transaction() as connection:
            attempt = self._load_attempt(connection, attempt_id)
            if attempt.revision != expected_attempt_revision or attempt.state is not EvaluationAttemptState.DISPATCHED:
                raise DomainError(ErrorCode.EVALUATION_RUN_CONFLICT, "case outcome cannot become unknown")
            revised = self._transition_attempt(
                connection,
                attempt,
                EvaluationAttemptState.OUTCOME_UNKNOWN,
                occurred_at,
                provider_request_id=provider_request_id,
            )
            run = self._load_run(connection, attempt.run_id)
            if run.state is EvaluationRunState.RUNNING:
                self._transition_run(
                    connection, run, EvaluationRunState.OUTCOME_PENDING, occurred_at
                )
            return revised

    def resolve_case_failure(
        self,
        *,
        attempt_id: StableId,
        expected_attempt_revision: Revision,
        failure_code: str,
        occurred_at: datetime,
    ) -> EvaluationCaseAttempt:
        with self._database.transaction() as connection:
            attempt = self._load_attempt(connection, attempt_id)
            if attempt.revision != expected_attempt_revision or attempt.state not in {
                EvaluationAttemptState.DISPATCHED,
                EvaluationAttemptState.OUTCOME_UNKNOWN,
            }:
                raise DomainError(ErrorCode.EVALUATION_RUN_CONFLICT, "case attempt cannot fail")
            revised = self._transition_attempt(
                connection,
                attempt,
                EvaluationAttemptState.FAILED,
                occurred_at,
                failure_code=failure_code,
            )
            run = self._load_run(connection, attempt.run_id)
            if run.state in {EvaluationRunState.RUNNING, EvaluationRunState.OUTCOME_PENDING}:
                self._transition_run(connection, run, EvaluationRunState.FAILED, occurred_at)
            return revised

    def finalize_run(
        self,
        *,
        run_id: StableId,
        expected_run_revision: Revision,
        actor: str,
        reason: str,
        occurred_at: datetime,
    ) -> EvaluationCompletion:
        with self._database.transaction() as connection:
            run = self._load_run(connection, run_id)
            if run.revision != expected_run_revision:
                raise DomainError(ErrorCode.EVALUATION_RUN_CONFLICT, "evaluation run revision is stale")
            existing = connection.execute(
                "SELECT result_id FROM app_evaluation_results WHERE run_id = ?",
                (run_id.value,),
            ).fetchone()
            if existing is not None:
                return self._load_completion(connection, run_id)
            if run.state is EvaluationRunState.OUTCOME_PENDING:
                raise DomainError(
                    ErrorCode.EVALUATION_OUTCOME_PENDING,
                    "evaluation has an unresolved external outcome",
                )
            if run.state is not EvaluationRunState.RUNNING:
                raise DomainError(ErrorCode.EVALUATION_RUN_CONFLICT, "evaluation run cannot finalize")
            definition = self._load_definition_by_digest(connection, run.definition_digest)
            attempts = self._successful_attempts(connection, run_id)
            by_case = {item.case_id: item for item in attempts}
            missing = [item.case_id for item in definition.cases if item.required and item.case_id not in by_case]
            if missing:
                raise DomainError(
                    ErrorCode.EVALUATION_RUN_CONFLICT,
                    "required evaluation cases are incomplete",
                    {"missing_case_count": len(missing)},
                )
            required_outcomes = [
                by_case[item.case_id].conclusion
                for item in definition.cases
                if item.required
            ]
            if any(item is EvaluationConclusion.FAIL for item in required_outcomes):
                conclusion = EvaluationConclusion.FAIL
            elif any(item is EvaluationConclusion.INCONCLUSIVE for item in required_outcomes):
                conclusion = EvaluationConclusion.INCONCLUSIVE
            else:
                conclusion = EvaluationConclusion.PASS
            passed = tuple(sorted(item.case_id for item in attempts if item.conclusion is EvaluationConclusion.PASS))
            failed = tuple(sorted(item.case_id for item in attempts if item.conclusion is EvaluationConclusion.FAIL))
            inconclusive = tuple(
                sorted(item.case_id for item in attempts if item.conclusion is EvaluationConclusion.INCONCLUSIVE)
            )
            result_id = self._ids.new("evaluation_result")
            case_attempt_ids = tuple(item.attempt_id for item in attempts)
            actual_models = tuple(sorted({str(item.actual_model_fingerprint) for item in attempts}))
            result_core = {
                "result_id": result_id.value,
                "run_id": run_id.value,
                "definition_digest": definition.digest.value,
                "conclusion": conclusion.value,
                "case_attempt_ids": tuple(item.value for item in case_attempt_ids),
                "passed_case_ids": passed,
                "failed_case_ids": failed,
                "inconclusive_case_ids": inconclusive,
                "actual_model_fingerprints": actual_models,
                "input_tokens": sum(item.input_tokens or 0 for item in attempts),
                "output_tokens": sum(item.output_tokens or 0 for item in attempts),
                "completed_at": occurred_at,
            }
            result = EvaluationResult(
                result_id=result_id,
                run_id=run_id,
                definition_digest=definition.digest,
                conclusion=conclusion,
                case_attempt_ids=case_attempt_ids,
                passed_case_ids=passed,
                failed_case_ids=failed,
                inconclusive_case_ids=inconclusive,
                actual_model_fingerprints=actual_models,
                input_tokens=result_core["input_tokens"],
                output_tokens=result_core["output_tokens"],
                completed_at=occurred_at,
                digest=digest_of(result_core),
            )
            self._insert_result(connection, result)
            dependency_digest = digest_of(
                {
                    "definition_digest": definition.digest.value,
                    "implementation_digest": definition.implementation_digest.value,
                    "conformance_result_ref": definition.conformance_result_ref,
                    "configuration_fingerprint": definition.provider_configuration_fingerprint.value,
                    "model_ref": definition.model_ref,
                    "adapter_version": definition.adapter_version,
                    "threshold_ref": definition.threshold_ref,
                    "case_definitions": definition.cases,
                }
            )
            validity_id = self._ids.new("evaluation_validity")
            valid_until = occurred_at + timedelta(seconds=definition.valid_for_seconds)
            validity_core = {
                "validity_id": validity_id.value,
                "result_id": result_id.value,
                "revision": 1,
                "status": EvaluationValidityStatus.VALID.value,
                "dependency_digest": dependency_digest.value,
                "valid_until": valid_until,
                "authority": actor,
                "reason": reason,
                "decided_at": occurred_at,
            }
            validity = EvaluationValidityDecision(
                validity_id=validity_id,
                result_id=result_id,
                revision=Revision(1),
                status=EvaluationValidityStatus.VALID,
                dependency_digest=dependency_digest,
                valid_until=valid_until,
                authority=actor,
                reason=reason,
                decided_at=occurred_at,
                digest=digest_of(validity_core),
            )
            self._insert_initial_validity(connection, validity)
            qualification = None
            if conclusion is EvaluationConclusion.PASS:
                proof_core = {
                    "proof_ref": f"capability-evaluation:{result_id.value}",
                    "capability_id": definition.capability_id,
                    "capability_contract_version": definition.capability_contract_version,
                    "strategy_id": definition.strategy_id,
                    "strategy_version": definition.strategy_version,
                    "result_ref": result_id.value,
                    "validity_ref": f"{validity_id.value}@1",
                    "qualification_kind": "CAPABILITY_EVALUATION",
                }
                qualification = QualificationProof(**proof_core, digest=digest_of(proof_core))
            completed_run = self._transition_run(
                connection, run, EvaluationRunState.COMPLETED, occurred_at
            )
            return EvaluationCompletion(completed_run, result, validity, qualification)

    def invalidate_result(
        self,
        *,
        result_id: StableId,
        expected_validity_revision: Revision,
        status: EvaluationValidityStatus,
        authority: str,
        reason: str,
        occurred_at: datetime,
    ) -> EvaluationValidityDecision:
        with self._database.transaction() as connection:
            current = self._load_validity(connection, result_id)
            if current.revision != expected_validity_revision:
                raise DomainError(ErrorCode.REVISION_CONFLICT, "evaluation validity revision is stale")
            allowed = {
                EvaluationValidityStatus.VALID: {
                    EvaluationValidityStatus.STALE,
                    EvaluationValidityStatus.REVOKED,
                },
                EvaluationValidityStatus.STALE: {EvaluationValidityStatus.REVOKED},
                EvaluationValidityStatus.REVOKED: set(),
            }
            if status not in allowed[current.status]:
                raise DomainError(
                    ErrorCode.EVALUATION_RUN_CONFLICT,
                    "evaluation validity transition is not monotonic",
                )
            revision = current.revision.next()
            core = {
                "validity_id": current.validity_id.value,
                "result_id": result_id.value,
                "revision": revision.value,
                "status": status.value,
                "dependency_digest": current.dependency_digest.value,
                "valid_until": current.valid_until,
                "authority": authority,
                "reason": reason,
                "decided_at": occurred_at,
            }
            decision = EvaluationValidityDecision(
                validity_id=current.validity_id,
                result_id=result_id,
                revision=revision,
                status=status,
                dependency_digest=current.dependency_digest,
                valid_until=current.valid_until,
                authority=authority,
                reason=reason,
                decided_at=occurred_at,
                digest=digest_of(core),
            )
            self._insert_validity_decision(connection, decision)
            cursor = connection.execute(
                """UPDATE app_evaluation_validity_roots
                   SET current_revision = ?, current_status = ?
                   WHERE result_id = ? AND current_revision = ?""",
                (revision.value, status.value, result_id.value, expected_validity_revision.value),
            )
            if cursor.rowcount != 1:
                raise DomainError(ErrorCode.REVISION_CONFLICT, "evaluation validity changed before commit")
            return decision

    def validate_qualification(
        self,
        proof: QualificationProof,
        at: datetime,
        dependencies: EvaluationQualificationDependencies,
    ) -> bool:
        try:
            result_id = StableId(proof.result_ref)
            with self._database.read() as connection:
                result = self._load_result(connection, result_id)
                validity = self._load_validity(connection, result_id)
                run = self._load_run(connection, result.run_id)
                definition = self._load_definition_by_digest(connection, result.definition_digest)
            return (
                proof.verify_digest()
                and proof.qualification_kind == "CAPABILITY_EVALUATION"
                and result.conclusion is EvaluationConclusion.PASS
                and run.state is EvaluationRunState.COMPLETED
                and validity.status is EvaluationValidityStatus.VALID
                and at < validity.valid_until
                and proof.validity_ref == f"{validity.validity_id.value}@{validity.revision.value}"
                and proof.capability_id == definition.capability_id
                and proof.capability_contract_version == definition.capability_contract_version
                and proof.strategy_id == definition.strategy_id
                and proof.strategy_version == definition.strategy_version
                and definition.implementation_digest
                == dependencies.strategy_implementation_digest
                and definition.conformance_result_ref
                == dependencies.conformance_result_ref
                and definition.provider_configuration_fingerprint
                == dependencies.provider_configuration_fingerprint
                and definition.model_ref == dependencies.model_ref
                and definition.adapter_version == dependencies.adapter_version
            )
        except (DomainError, ValueError):
            return False

    def get_run(self, run_id: StableId) -> EvaluationRun:
        with self._database.read() as connection:
            return self._load_run(connection, run_id)

    def qualification_for_result(self, result_id: StableId) -> QualificationProof:
        with self._database.read() as connection:
            result = self._load_result(connection, result_id)
            validity = self._load_validity(connection, result_id)
            definition = self._load_definition_by_digest(
                connection, result.definition_digest
            )
        if result.conclusion is not EvaluationConclusion.PASS:
            raise DomainError(
                ErrorCode.QUALIFICATION_INVALID,
                "capability evaluation result did not pass",
            )
        core = {
            "proof_ref": f"capability-evaluation:{result.result_id.value}",
            "capability_id": definition.capability_id,
            "capability_contract_version": definition.capability_contract_version,
            "strategy_id": definition.strategy_id,
            "strategy_version": definition.strategy_version,
            "result_ref": result.result_id.value,
            "validity_ref": f"{validity.validity_id.value}@{validity.revision.value}",
            "qualification_kind": "CAPABILITY_EVALUATION",
        }
        return QualificationProof(**core, digest=digest_of(core))

    def get_attempt(self, attempt_id: StableId) -> EvaluationCaseAttempt:
        with self._database.read() as connection:
            return self._load_attempt(connection, attempt_id)

    def get_definition(self, digest: Digest) -> EvaluationDefinition:
        with self._database.read() as connection:
            return self._load_definition_by_digest(connection, digest)

    def _restore_run_after_unknown(
        self, connection: sqlite3.Connection, run_id: StableId, occurred_at: datetime
    ) -> None:
        remaining = connection.execute(
            "SELECT 1 FROM app_evaluation_attempts WHERE run_id = ? AND current_state = ?",
            (run_id.value, EvaluationAttemptState.OUTCOME_UNKNOWN.value),
        ).fetchone()
        run = self._load_run(connection, run_id)
        if remaining is None and run.state is EvaluationRunState.OUTCOME_PENDING:
            self._transition_run(connection, run, EvaluationRunState.RUNNING, occurred_at)

    def _transition_run(
        self,
        connection: sqlite3.Connection,
        run: EvaluationRun,
        state: EvaluationRunState,
        occurred_at: datetime,
    ) -> EvaluationRun:
        revision = run.revision.next()
        connection.execute(
            "INSERT INTO app_evaluation_run_revisions VALUES (?, ?, ?, ?)",
            (run.run_id.value, revision.value, state.value, _time(occurred_at)),
        )
        cursor = connection.execute(
            """UPDATE app_evaluation_runs SET current_revision = ?, current_state = ?, revised_at = ?
               WHERE run_id = ? AND current_revision = ?""",
            (
                revision.value,
                state.value,
                _time(occurred_at),
                run.run_id.value,
                run.revision.value,
            ),
        )
        if cursor.rowcount != 1:
            raise DomainError(ErrorCode.REVISION_CONFLICT, "evaluation run changed before commit")
        return self._load_run(connection, run.run_id)

    def _transition_attempt(
        self,
        connection: sqlite3.Connection,
        attempt: EvaluationCaseAttempt,
        state: EvaluationAttemptState,
        occurred_at: datetime,
        *,
        evidence: CaseExecutionEvidence | None = None,
        provider_request_id: str | None = None,
        failure_code: str | None = None,
    ) -> EvaluationCaseAttempt:
        allowed = {
            EvaluationAttemptState.DISPATCHED: {
                EvaluationAttemptState.SUCCEEDED,
                EvaluationAttemptState.FAILED,
                EvaluationAttemptState.OUTCOME_UNKNOWN,
            },
            EvaluationAttemptState.OUTCOME_UNKNOWN: {
                EvaluationAttemptState.SUCCEEDED,
                EvaluationAttemptState.FAILED,
            },
            EvaluationAttemptState.SUCCEEDED: set(),
            EvaluationAttemptState.FAILED: set(),
        }
        if state not in allowed[attempt.state]:
            raise DomainError(ErrorCode.EVALUATION_RUN_CONFLICT, "case attempt transition is invalid")
        revision = attempt.revision.next()
        self._insert_attempt_revision(
            connection,
            attempt_id=attempt.attempt_id,
            revision=revision,
            state=state,
            evidence=evidence,
            provider_request_id=provider_request_id,
            failure_code=failure_code,
            occurred_at=occurred_at,
        )
        cursor = connection.execute(
            """UPDATE app_evaluation_attempts
               SET current_revision = ?, current_state = ?, revised_at = ?
               WHERE attempt_id = ? AND current_revision = ?""",
            (
                revision.value,
                state.value,
                _time(occurred_at),
                attempt.attempt_id.value,
                attempt.revision.value,
            ),
        )
        if cursor.rowcount != 1:
            raise DomainError(ErrorCode.REVISION_CONFLICT, "case attempt changed before commit")
        return self._load_attempt(connection, attempt.attempt_id)

    @staticmethod
    def _insert_attempt_revision(
        connection: sqlite3.Connection,
        *,
        attempt_id: StableId,
        revision: Revision,
        state: EvaluationAttemptState,
        evidence: CaseExecutionEvidence | None,
        provider_request_id: str | None,
        failure_code: str | None,
        occurred_at: datetime,
    ) -> None:
        connection.execute(
            """INSERT INTO app_evaluation_attempt_revisions
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                attempt_id.value,
                revision.value,
                state.value,
                evidence.conclusion.value if evidence else None,
                evidence.output_ref if evidence else None,
                evidence.output_digest.value if evidence else None,
                evidence.sink_manifest_ref if evidence else None,
                evidence.sink_manifest_digest.value if evidence else None,
                evidence.oracle_ref if evidence else None,
                evidence.oracle_digest.value if evidence else None,
                evidence.actual_model_fingerprint if evidence else None,
                evidence.provider_request_id if evidence else provider_request_id,
                evidence.input_tokens if evidence else None,
                evidence.output_tokens if evidence else None,
                int(evidence.usage_complete) if evidence else 0,
                failure_code,
                _time(occurred_at),
            ),
        )

    def _successful_attempts(
        self, connection: sqlite3.Connection, run_id: StableId
    ) -> tuple[EvaluationCaseAttempt, ...]:
        rows = connection.execute(
            """SELECT attempt_id FROM app_evaluation_attempts
               WHERE run_id = ? AND current_state = ? ORDER BY case_id, attempt_id""",
            (run_id.value, EvaluationAttemptState.SUCCEEDED.value),
        ).fetchall()
        return tuple(self._load_attempt(connection, StableId(row["attempt_id"])) for row in rows)

    @staticmethod
    def _insert_result(connection: sqlite3.Connection, result: EvaluationResult) -> None:
        connection.execute(
            """INSERT INTO app_evaluation_results VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                result.result_id.value,
                result.run_id.value,
                result.definition_digest.value,
                result.conclusion.value,
                _json([item.value for item in result.case_attempt_ids]),
                _json(result.passed_case_ids),
                _json(result.failed_case_ids),
                _json(result.inconclusive_case_ids),
                _json(result.actual_model_fingerprints),
                result.input_tokens,
                result.output_tokens,
                _time(result.completed_at),
                result.digest.value,
            ),
        )

    def _insert_initial_validity(
        self, connection: sqlite3.Connection, validity: EvaluationValidityDecision
    ) -> None:
        connection.execute(
            "INSERT INTO app_evaluation_validity_roots VALUES (?, ?, 1, ?)",
            (validity.result_id.value, validity.validity_id.value, validity.status.value),
        )
        self._insert_validity_decision(connection, validity)

    @staticmethod
    def _insert_validity_decision(
        connection: sqlite3.Connection, validity: EvaluationValidityDecision
    ) -> None:
        connection.execute(
            """INSERT INTO app_evaluation_validity_decisions
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                validity.validity_id.value,
                validity.result_id.value,
                validity.revision.value,
                validity.status.value,
                validity.dependency_digest.value,
                _time(validity.valid_until),
                validity.authority,
                validity.reason,
                _time(validity.decided_at),
                validity.digest.value,
            ),
        )

    def _load_completion(
        self, connection: sqlite3.Connection, run_id: StableId
    ) -> EvaluationCompletion:
        row = connection.execute(
            "SELECT result_id FROM app_evaluation_results WHERE run_id = ?",
            (run_id.value,),
        ).fetchone()
        if row is None:
            raise DomainError(ErrorCode.AUTHORITY_RECORD_INCONSISTENT, "evaluation result is missing")
        result = self._load_result(connection, StableId(row["result_id"]))
        validity = self._load_validity(connection, result.result_id)
        run = self._load_run(connection, run_id)
        definition = self._load_definition_by_digest(connection, result.definition_digest)
        proof = None
        if result.conclusion is EvaluationConclusion.PASS:
            core = {
                "proof_ref": f"capability-evaluation:{result.result_id.value}",
                "capability_id": definition.capability_id,
                "capability_contract_version": definition.capability_contract_version,
                "strategy_id": definition.strategy_id,
                "strategy_version": definition.strategy_version,
                "result_ref": result.result_id.value,
                "validity_ref": f"{validity.validity_id.value}@1",
                "qualification_kind": "CAPABILITY_EVALUATION",
            }
            proof = QualificationProof(**core, digest=digest_of(core))
        return EvaluationCompletion(run, result, validity, proof)

    @staticmethod
    def _load_run(connection: sqlite3.Connection, run_id: StableId) -> EvaluationRun:
        row = connection.execute(
            "SELECT * FROM app_evaluation_runs WHERE run_id = ?", (run_id.value,)
        ).fetchone()
        if row is None:
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "evaluation run was not found")
        core = json.loads(row["qualification_json"])
        proof = QualificationProof(**core, digest=Digest(row["qualification_digest"]))
        if not proof.verify_digest():
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "evaluation-only qualification digest does not verify",
            )
        return EvaluationRun(
            run_id=run_id,
            revision=Revision(row["current_revision"]),
            state=EvaluationRunState(row["current_state"]),
            definition_digest=Digest(row["definition_digest"]),
            evaluation_id=row["evaluation_id"],
            evaluation_version=row["evaluation_version"],
            strategy_id=row["strategy_id"],
            strategy_version=row["strategy_version"],
            evaluation_sink_ref=row["evaluation_sink_ref"],
            root_allocation_ref=row["root_allocation_ref"],
            evaluation_only_qualification=proof,
            request_digest=Digest(row["request_digest"]),
            created_at=_parse_time(row["created_at"]),
            revised_at=_parse_time(row["revised_at"]),
        )

    @staticmethod
    def _load_attempt(
        connection: sqlite3.Connection, attempt_id: StableId
    ) -> EvaluationCaseAttempt:
        row = connection.execute(
            """SELECT root.*, revision.conclusion, revision.output_ref,
                      revision.output_digest, revision.sink_manifest_ref,
                      revision.sink_manifest_digest, revision.oracle_ref,
                      revision.oracle_digest, revision.actual_model_fingerprint,
                      revision.provider_request_id, revision.input_tokens,
                      revision.output_tokens, revision.usage_complete,
                      revision.failure_code
               FROM app_evaluation_attempts root
               JOIN app_evaluation_attempt_revisions revision
                 ON revision.attempt_id = root.attempt_id
                AND revision.revision = root.current_revision
               WHERE root.attempt_id = ?""",
            (attempt_id.value,),
        ).fetchone()
        if row is None:
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "evaluation attempt was not found")
        return EvaluationCaseAttempt(
            attempt_id=attempt_id,
            revision=Revision(row["current_revision"]),
            run_id=StableId(row["run_id"]),
            case_id=row["case_id"],
            attempt_key=row["attempt_key"],
            request_digest=Digest(row["request_digest"]),
            state=EvaluationAttemptState(row["current_state"]),
            conclusion=EvaluationConclusion(row["conclusion"]) if row["conclusion"] else None,
            output_ref=row["output_ref"],
            output_digest=Digest(row["output_digest"]) if row["output_digest"] else None,
            sink_manifest_ref=row["sink_manifest_ref"],
            sink_manifest_digest=(
                Digest(row["sink_manifest_digest"]) if row["sink_manifest_digest"] else None
            ),
            oracle_ref=row["oracle_ref"],
            oracle_digest=Digest(row["oracle_digest"]) if row["oracle_digest"] else None,
            actual_model_fingerprint=row["actual_model_fingerprint"],
            provider_request_id=row["provider_request_id"],
            input_tokens=row["input_tokens"],
            output_tokens=row["output_tokens"],
            usage_complete=bool(row["usage_complete"]),
            failure_code=row["failure_code"],
            created_at=_parse_time(row["created_at"]),
            revised_at=_parse_time(row["revised_at"]),
        )

    @staticmethod
    def _load_result(connection: sqlite3.Connection, result_id: StableId) -> EvaluationResult:
        row = connection.execute(
            "SELECT * FROM app_evaluation_results WHERE result_id = ?", (result_id.value,)
        ).fetchone()
        if row is None:
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "evaluation result was not found")
        result = EvaluationResult(
            result_id=result_id,
            run_id=StableId(row["run_id"]),
            definition_digest=Digest(row["definition_digest"]),
            conclusion=EvaluationConclusion(row["conclusion"]),
            case_attempt_ids=tuple(StableId(item) for item in json.loads(row["case_attempt_ids_json"])),
            passed_case_ids=tuple(json.loads(row["passed_case_ids_json"])),
            failed_case_ids=tuple(json.loads(row["failed_case_ids_json"])),
            inconclusive_case_ids=tuple(json.loads(row["inconclusive_case_ids_json"])),
            actual_model_fingerprints=tuple(json.loads(row["actual_model_fingerprints_json"])),
            input_tokens=row["input_tokens"],
            output_tokens=row["output_tokens"],
            completed_at=_parse_time(row["completed_at"]),
            digest=Digest(row["result_digest"]),
        )
        core = {
            "result_id": result.result_id.value,
            "run_id": result.run_id.value,
            "definition_digest": result.definition_digest.value,
            "conclusion": result.conclusion.value,
            "case_attempt_ids": tuple(item.value for item in result.case_attempt_ids),
            "passed_case_ids": result.passed_case_ids,
            "failed_case_ids": result.failed_case_ids,
            "inconclusive_case_ids": result.inconclusive_case_ids,
            "actual_model_fingerprints": result.actual_model_fingerprints,
            "input_tokens": result.input_tokens,
            "output_tokens": result.output_tokens,
            "completed_at": result.completed_at,
        }
        if digest_of(core) != result.digest:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "evaluation result digest does not verify",
            )
        return result

    @staticmethod
    def _load_validity(
        connection: sqlite3.Connection, result_id: StableId
    ) -> EvaluationValidityDecision:
        row = connection.execute(
            """SELECT decision.* FROM app_evaluation_validity_roots root
               JOIN app_evaluation_validity_decisions decision
                 ON decision.validity_id = root.validity_id
                AND decision.revision = root.current_revision
               WHERE root.result_id = ?""",
            (result_id.value,),
        ).fetchone()
        if row is None:
            raise DomainError(ErrorCode.AUTHORITY_RECORD_INCONSISTENT, "evaluation validity is missing")
        decision = EvaluationValidityDecision(
            validity_id=StableId(row["validity_id"]),
            result_id=result_id,
            revision=Revision(row["revision"]),
            status=EvaluationValidityStatus(row["status"]),
            dependency_digest=Digest(row["dependency_digest"]),
            valid_until=_parse_time(row["valid_until"]),
            authority=row["authority"],
            reason=row["reason"],
            decided_at=_parse_time(row["decided_at"]),
            digest=Digest(row["decision_digest"]),
        )
        core = {
            "validity_id": decision.validity_id.value,
            "result_id": decision.result_id.value,
            "revision": decision.revision.value,
            "status": decision.status.value,
            "dependency_digest": decision.dependency_digest.value,
            "valid_until": decision.valid_until,
            "authority": decision.authority,
            "reason": decision.reason,
            "decided_at": decision.decided_at,
        }
        if digest_of(core) != decision.digest:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "evaluation validity digest does not verify",
            )
        return decision

    def _load_definition_by_digest(
        self, connection: sqlite3.Connection, digest: Digest
    ) -> EvaluationDefinition:
        row = connection.execute(
            "SELECT definition_json, definition_digest FROM app_evaluation_definitions WHERE definition_digest = ?",
            (digest.value,),
        ).fetchone()
        if row is None:
            raise DomainError(ErrorCode.AUTHORITY_RECORD_INCONSISTENT, "evaluation definition is missing")
        return self._decode_definition(row["definition_json"], row["definition_digest"])

    @staticmethod
    def _decode_definition(payload: str, expected_digest: str) -> EvaluationDefinition:
        value = json.loads(payload)
        cases = tuple(
            EvaluationCaseDefinition(
                case_id=item["case_id"],
                case_version=item["case_version"],
                fixture_ref=item["fixture_ref"],
                fixture_digest=Digest(item["fixture_digest"]),
                oracle_ref=item["oracle_ref"],
                oracle_digest=Digest(item["oracle_digest"]),
                required=item["required"],
            )
            for item in value.pop("cases")
        )
        implementation_digest = Digest(value.pop("implementation_digest"))
        configuration_fingerprint = Digest(
            value.pop("provider_configuration_fingerprint")
        )
        prompt_program_digest = Digest(value.pop("prompt_program_digest"))
        output_schema_digest = Digest(value.pop("output_schema_digest"))
        metric_contract_digest = Digest(value.pop("metric_contract_digest"))
        definition = EvaluationDefinition.create(
            **value,
            implementation_digest=implementation_digest,
            provider_configuration_fingerprint=configuration_fingerprint,
            prompt_program_digest=prompt_program_digest,
            output_schema_digest=output_schema_digest,
            metric_contract_digest=metric_contract_digest,
            cases=cases,
        )
        if definition.digest.value != expected_digest:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "evaluation definition digest does not verify",
            )
        return definition


def _definition_core(definition: EvaluationDefinition) -> dict[str, object]:
    return {
        "evaluation_id": definition.evaluation_id,
        "evaluation_version": definition.evaluation_version,
        "capability_id": definition.capability_id,
        "capability_contract_version": definition.capability_contract_version,
        "strategy_id": definition.strategy_id,
        "strategy_version": definition.strategy_version,
        "design_baseline_ref": definition.design_baseline_ref,
        "implementation_digest": definition.implementation_digest.value,
        "conformance_result_ref": definition.conformance_result_ref,
        "provider_configuration_fingerprint": definition.provider_configuration_fingerprint.value,
        "model_ref": definition.model_ref,
        "adapter_version": definition.adapter_version,
        "prompt_program_ref": definition.prompt_program_ref,
        "prompt_program_digest": definition.prompt_program_digest.value,
        "output_schema_ref": definition.output_schema_ref,
        "output_schema_digest": definition.output_schema_digest.value,
        "tool_policy_ref": definition.tool_policy_ref,
        "data_source_revision_ref": definition.data_source_revision_ref,
        "environment_ref": definition.environment_ref,
        "reference_strategy_ref": definition.reference_strategy_ref,
        "resource_policy_ref": definition.resource_policy_ref,
        "metric_contract_digest": definition.metric_contract_digest.value,
        "threshold_ref": definition.threshold_ref,
        "cases": [
            {
                "case_id": item.case_id,
                "case_version": item.case_version,
                "fixture_ref": item.fixture_ref,
                "fixture_digest": item.fixture_digest.value,
                "oracle_ref": item.oracle_ref,
                "oracle_digest": item.oracle_digest.value,
                "required": item.required,
            }
            for item in definition.cases
        ],
        "valid_for_seconds": definition.valid_for_seconds,
    }


def _json(value: object) -> str:
    return canonical_json_bytes(value).decode("utf-8")


def _time(value: datetime) -> str:
    return value.isoformat(timespec="microseconds").replace("+00:00", "Z")


def _parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))
