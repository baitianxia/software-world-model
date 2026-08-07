"""Register a verified JWT comparison in the Capability Evaluation authority."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import Mapping

from software_world_model.application_services import (
    CapabilityDefinition,
    CapabilityEvaluationService,
    CapabilityRegistry,
    CaseExecutionEvidence,
    EvaluationCaseDefinition,
    EvaluationConclusion,
    EvaluationQualificationDependencies,
    EvaluationDefinition,
    EvaluationAttemptState,
    EvaluationRunState,
    CurrentEvaluationQualificationVerifier,
    LiveIntegrationPolicy,
    QualificationProof,
    StrategyActivationService,
    StrategyDefinition,
    StrategyKind,
)
from software_world_model.cross_cutting import (
    CorrelationRef,
    Digest,
    DomainError,
    ErrorCode,
    IdempotencyKey,
    digest_of,
)
from software_world_model.infrastructure import (
    SqliteCapabilityEvaluationRepository,
    SqliteDatabase,
    SqliteStrategyActivationRepository,
)

from .comparison import (
    COMPARISON_REVIEW_OUTPUT_SCHEMA,
    COMPARISON_REVIEW_OUTPUT_SCHEMA_REF,
    COMPARISON_REVIEW_POLICY,
    COMPARISON_REVIEW_POLICY_REF,
    verify_capability_comparison,
)
from .manifest import (
    _time,
    _utc,
    _verify_qualification,
    verify_direct_oracle,
    verify_jwt_run_configuration,
)
from .world_model import verify_world_model_result


CAPABILITY_ID = "knowledge.jwt-impact"
CAPABILITY_CONTRACT_VERSION = "1.0.0"
STRATEGY_ID = "jwt-impact-ark-world-model"
STRATEGY_VERSION_BASE = "1.0.0"
EVALUATION_ID = "CE-JWT-ARK-001"
EVALUATION_VERSION_BASE = "2.0.0"
EVALUATION_CASE_ID = "CE-JWT-CLAIM-CONSERVATION-001"
EVALUATION_REGISTRATION_SCHEMA = "swm.jwt-capability-evaluation-registration@2"
_CE_VALID_FOR_SECONDS = 3600


def register_capability_evaluation(
    *,
    oracle_path: str | Path,
    run_configuration_path: str | Path,
    world_model_result_path: str | Path,
    comparison_path: str | Path,
    database_path: str | Path,
    result_directory: str | Path,
    qualification: object,
    configuration: object,
    actor: str,
    now: datetime | None = None,
) -> Path:
    """Persist one immutable CE result and optional PASS qualification proof."""

    if not isinstance(actor, str) or not actor.strip() or actor != actor.strip():
        raise DomainError(ErrorCode.INVALID_ARGUMENT, "evaluation actor identity is invalid")
    occurred_at = _utc(now or datetime.now(timezone.utc))
    _verify_qualification(qualification, configuration, at=occurred_at)
    oracle = _load(oracle_path, "Direct Oracle")
    run_configuration = _load(run_configuration_path, "JWT run configuration")
    world = _load(world_model_result_path, "World Model result")
    comparison = _load(comparison_path, "capability comparison")
    verify_direct_oracle(
        oracle, qualification=qualification, configuration=configuration
    )
    verify_jwt_run_configuration(
        run_configuration,
        qualification,
        configuration,
        at=occurred_at,
        require_current_harness=False,
    )
    verify_world_model_result(world, run_configuration, qualification, configuration)
    verify_capability_comparison(comparison, oracle, world, run_configuration)
    remaining_seconds = int((qualification.valid_until - occurred_at).total_seconds())
    if remaining_seconds <= _CE_VALID_FOR_SECONDS:
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "adapter conformance expires too soon for the fixed CE validity period",
        )
    implementation_digest = _world_runtime_implementation_digest(run_configuration)
    strategy_version = _strategy_version(run_configuration)
    evaluation_version = _evaluation_version(run_configuration)
    capability, strategy = _capability_and_strategy(
        run_configuration, implementation_digest, world["schema"], comparison["schema"]
    )
    registry = CapabilityRegistry()
    registry.register_capability(capability)
    registry.register_strategy(strategy)
    definition = EvaluationDefinition.create(
        evaluation_id=EVALUATION_ID,
        evaluation_version=evaluation_version,
        capability_id=CAPABILITY_ID,
        capability_contract_version=CAPABILITY_CONTRACT_VERSION,
        strategy_id=STRATEGY_ID,
        strategy_version=strategy_version,
        design_baseline_ref="SWM-DBM-ITER-001-REV-002",
        implementation_digest=implementation_digest,
        conformance_result_ref=qualification.result_ref,
        provider_configuration_fingerprint=configuration.fingerprint,
        model_ref=configuration.actual_model_fingerprint,
        adapter_version=configuration.adapter_version,
        prompt_program_ref=COMPARISON_REVIEW_POLICY_REF,
        prompt_program_digest=digest_of(
            {
                "world_roles": run_configuration["roles"],
                "comparison_review_policy": COMPARISON_REVIEW_POLICY,
            }
        ),
        output_schema_ref=COMPARISON_REVIEW_OUTPUT_SCHEMA_REF,
        output_schema_digest=digest_of(COMPARISON_REVIEW_OUTPUT_SCHEMA),
        tool_policy_ref="bounded-local-git-then-formal-knowledge-only@1",
        data_source_revision_ref=f"mall:{run_configuration['source']['target_commit']}",
        environment_ref="isolated-local-validation@1",
        reference_strategy_ref="direct-source-investigation@1",
        resource_policy_ref="jwt-capability-run-budget@1",
        metric_contract_digest=digest_of(
            {
                "missing_direct_obligations": 0,
                "missing_world_obligations": 0,
                "extra_direct_obligations": 0,
                "extra_world_obligations": 0,
                "duplicate_obligations": 0,
                "structural_mismatch": 0,
                "allowed_semantic_outcomes": ["EQUIVALENT", "WORLD_BETTER"],
                "world_factual_error": False,
                "world_score_gte_direct": True,
            }
        ),
        threshold_ref="all-obligations-covered-cross-model-no-extra-error@2",
        cases=(
            EvaluationCaseDefinition(
                case_id=EVALUATION_CASE_ID,
                case_version=evaluation_version,
                fixture_ref=run_configuration["run_configuration_id"],
                fixture_digest=Digest(run_configuration["configuration_digest"]),
                oracle_ref=oracle["oracle_id"],
                oracle_digest=Digest(oracle["oracle_digest"]),
            ),
        ),
        valid_for_seconds=_CE_VALID_FOR_SECONDS,
    )
    database_file = Path(database_path).resolve()
    database_file.parent.mkdir(parents=True, exist_ok=True)
    with SqliteDatabase(database_file) as database:
        repository = SqliteCapabilityEvaluationRepository(database)
        service = CapabilityEvaluationService(
            repository,
            registry,
            qualification,
            clock=lambda: occurred_at,
        )
        definition = service.register_definition(definition)
        idempotency_suffix = comparison["comparison_digest"].removeprefix("sha256:")[:32]
        prepared = service.prepare_run(
            definition=definition,
            evaluation_sink_ref=f"sqlite:{digest_of(str(database_file)).value}",
            root_allocation_ref=f"jwt-evaluation-budget:{run_configuration['run_configuration_id']}",
            idempotency_key=IdempotencyKey(f"jwt-ce-{idempotency_suffix}"),
            actor=actor,
            correlation_ref=CorrelationRef(f"jwt-ce-{idempotency_suffix}"),
        )
        running = (
            service.start_run(prepared)
            if prepared.state is EvaluationRunState.PREPARED
            else prepared
        )
        running, attempt = service.dispatch_case(
            run=running,
            case_id=EVALUATION_CASE_ID,
            attempt_key=f"jwt-claim-comparison-{idempotency_suffix}",
            request_digest=Digest(comparison["comparison_digest"]),
        )
        direct_usage = oracle["direct_run"]["usage"]
        world_usage = world["usage"]
        all_request_ids = (
            oracle["direct_run"]["provider_request_ids"]
            + world["provider_request_ids"]
        )
        evidence = CaseExecutionEvidence(
            conclusion=(
                EvaluationConclusion.PASS
                if comparison["conclusion"] == "PASS"
                else EvaluationConclusion.FAIL
            ),
            output_ref=comparison["comparison_id"],
            output_digest=Digest(comparison["comparison_digest"]),
            sink_manifest_ref=world["run_id"],
            sink_manifest_digest=Digest(world["result_digest"]),
            oracle_ref=oracle["oracle_id"],
            oracle_digest=Digest(oracle["oracle_digest"]),
            actual_model_fingerprint=configuration.actual_model_fingerprint,
            provider_request_id=f"aggregate:{digest_of({'model_request_ids': all_request_ids, 'review_attestation_digest': comparison['review_attestation_digest']}).value}",
            input_tokens=(
                direct_usage["input_tokens"]
                + world_usage["input_tokens"]
            ),
            output_tokens=(
                direct_usage["output_tokens"]
                + world_usage["output_tokens"]
            ),
            usage_complete=(
                direct_usage["complete"] is True
                and world_usage["complete"] is True
            ),
        )
        if attempt.state in {
            EvaluationAttemptState.DISPATCHED,
            EvaluationAttemptState.OUTCOME_UNKNOWN,
        }:
            service.complete_case(attempt, evidence)
        elif attempt.state is not EvaluationAttemptState.SUCCEEDED:
            raise DomainError(
                ErrorCode.EVALUATION_RUN_CONFLICT,
                "existing JWT evaluation attempt did not succeed",
            )
        running = service.get_run(running.run_id)
        completion = service.finalize_run(
            running,
            actor=actor,
            reason="sealed JWT cross-model obligation comparison",
        )
    proof = completion.qualification
    core = {
        "schema": EVALUATION_REGISTRATION_SCHEMA,
        "recorded_at": _time(completion.result.completed_at),
        "database_ref": f"sqlite:{digest_of(str(database_file)).value}",
        "definition_digest": definition.digest.value,
        "implementation_digest": definition.implementation_digest.value,
        "strategy_version": strategy_version,
        "evaluation_version": evaluation_version,
        "run_configuration_digest": run_configuration["configuration_digest"],
        "run_id": completion.run.run_id.value,
        "result_id": completion.result.result_id.value,
        "result_digest": completion.result.digest.value,
        "conclusion": completion.result.conclusion.value,
        "validity_id": completion.validity.validity_id.value,
        "validity_status": completion.validity.status.value,
        "valid_until": _time(completion.validity.valid_until),
        "qualification": (
            None
            if proof is None
            else {
                **proof.core(),
                "digest": proof.digest.value,
            }
        ),
        "production_activation": "NOT_RUN",
    }
    document = {**core, "registration_digest": digest_of(core).value}
    return _seal(
        document,
        result_directory,
        f"JWT-CE-REGISTRATION-{completion.run.run_id.value}",
    )


def verify_evaluation_registration(document: Mapping[str, object]) -> QualificationProof | None:
    if document.get("schema") != EVALUATION_REGISTRATION_SCHEMA:
        raise DomainError(ErrorCode.QUALIFICATION_INVALID, "CE registration schema is invalid")
    supplied = document.get("registration_digest")
    try:
        digest = Digest(str(supplied))
    except ValueError as exc:
        raise DomainError(ErrorCode.QUALIFICATION_INVALID, "CE registration digest is invalid") from exc
    core = {key: value for key, value in document.items() if key != "registration_digest"}
    if digest_of(core) != digest:
        raise DomainError(ErrorCode.QUALIFICATION_INVALID, "CE registration digest does not verify")
    qualification = document.get("qualification")
    if qualification is None:
        if document.get("conclusion") == "PASS":
            raise DomainError(ErrorCode.QUALIFICATION_INVALID, "PASS CE registration lacks qualification")
        return None
    if not isinstance(qualification, dict) or set(qualification) != {
        "proof_ref",
        "capability_id",
        "capability_contract_version",
        "strategy_id",
        "strategy_version",
        "result_ref",
        "validity_ref",
        "qualification_kind",
        "digest",
    }:
        raise DomainError(ErrorCode.QUALIFICATION_INVALID, "CE qualification shape is invalid")
    try:
        proof = QualificationProof(
            proof_ref=qualification["proof_ref"],
            capability_id=qualification["capability_id"],
            capability_contract_version=qualification["capability_contract_version"],
            strategy_id=qualification["strategy_id"],
            strategy_version=qualification["strategy_version"],
            result_ref=qualification["result_ref"],
            validity_ref=qualification["validity_ref"],
            qualification_kind=qualification["qualification_kind"],
            digest=Digest(qualification["digest"]),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise DomainError(ErrorCode.QUALIFICATION_INVALID, "CE qualification is invalid") from exc
    if (
        not proof.verify_digest()
        or proof.qualification_kind != "CAPABILITY_EVALUATION"
        or proof.capability_id != CAPABILITY_ID
        or proof.capability_contract_version != CAPABILITY_CONTRACT_VERSION
        or proof.strategy_id != STRATEGY_ID
        or proof.strategy_version != document.get("strategy_version")
        or document.get("conclusion") != "PASS"
    ):
        raise DomainError(ErrorCode.QUALIFICATION_INVALID, "CE qualification does not verify")
    return proof


def activate_evaluated_strategy(
    *,
    registration_path: str | Path,
    run_configuration_path: str | Path,
    database_path: str | Path,
    result_directory: str | Path,
    activation_scope: Mapping[str, str],
    actor: str,
    reason: str,
    idempotency_key: str,
    now: datetime | None = None,
) -> Path:
    """Explicitly activate a still-current CE-qualified model strategy."""

    for value, label in (
        (actor, "activation actor"),
        (reason, "activation reason"),
        (idempotency_key, "activation idempotency key"),
    ):
        if not isinstance(value, str) or not value.strip() or value != value.strip():
            raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} is invalid")
    decided_at = _utc(now or datetime.now(timezone.utc))
    registration = _load(registration_path, "CE registration")
    proof = verify_evaluation_registration(registration)
    if proof is None:
        raise DomainError(ErrorCode.ACTIVATION_WITHOUT_PASS, "CE did not issue a PASS qualification")
    run_configuration = _load(run_configuration_path, "JWT run configuration")
    database_file = Path(database_path).resolve()
    if registration.get("database_ref") != f"sqlite:{digest_of(str(database_file)).value}":
        raise DomainError(ErrorCode.QUALIFICATION_INVALID, "activation database differs from CE authority")
    implementation_digest = _world_runtime_implementation_digest(run_configuration)
    strategy_version = _strategy_version(run_configuration)
    if (
        registration.get("implementation_digest") != implementation_digest.value
        or registration.get("strategy_version") != strategy_version
        or registration.get("run_configuration_digest")
        != run_configuration.get("configuration_digest")
    ):
        raise DomainError(
            ErrorCode.STRATEGY_CONTRACT_MISMATCH,
            "current run harness differs from the evaluated implementation",
        )
    capability, strategy = _capability_and_strategy(
        run_configuration,
        implementation_digest,
        "swm.jwt-world-model-result@1",
        "swm.jwt-capability-comparison@2",
    )
    registry = CapabilityRegistry()
    registry.register_capability(capability)
    registry.register_strategy(strategy)
    with SqliteDatabase(database_file) as database:
        evaluation_repository = SqliteCapabilityEvaluationRepository(database)
        evaluated_definition = evaluation_repository.get_definition(
            Digest(registration["definition_digest"])
        )
        if (
            evaluated_definition.implementation_digest != implementation_digest
            or evaluated_definition.capability_id != CAPABILITY_ID
            or evaluated_definition.capability_contract_version
            != CAPABILITY_CONTRACT_VERSION
            or evaluated_definition.strategy_id != STRATEGY_ID
            or evaluated_definition.strategy_version != strategy_version
        ):
            raise DomainError(
                ErrorCode.STRATEGY_CONTRACT_MISMATCH,
                "CE Definition does not match the strategy being activated",
            )
        verifier = CurrentEvaluationQualificationVerifier(
            evaluation_repository,
            EvaluationQualificationDependencies.from_definition(
                evaluated_definition
            ),
            clock=lambda: decided_at,
        )
        if not verifier.validate(proof):
            raise DomainError(
                ErrorCode.QUALIFICATION_INVALID,
                "CE qualification is stale, revoked, expired, or for another implementation",
            )
        activation_repository = SqliteStrategyActivationRepository(database)
        service = StrategyActivationService(
            activation_repository,
            registry,
            verifier,
            live_policy=LiveIntegrationPolicy(model_strategy_activation_enabled=True),
            clock=lambda: decided_at,
        )
        decision = service.activate_strategy(
            capability_id=CAPABILITY_ID,
            capability_contract_version=CAPABILITY_CONTRACT_VERSION,
            activation_scope=activation_scope,
            expected_revision=None,
            strategy_id=STRATEGY_ID,
            strategy_version=strategy_version,
            qualification=proof,
            idempotency_key=IdempotencyKey(idempotency_key),
            actor=actor,
            reason=reason,
            correlation_ref=CorrelationRef(idempotency_key),
        )
    core = {
        "schema": "swm.jwt-strategy-activation@1",
        "decision_id": decision.decision_id.value,
        "decision_type": decision.decision_type.value,
        "activation_revision": decision.activation_revision.value,
        "capability_id": decision.capability_id,
        "capability_contract_version": decision.capability_contract_version,
        "strategy_id": decision.strategy_id,
        "strategy_version": decision.strategy_version,
        "activation_scope": list(decision.activation_scope),
        "qualification_digest": proof.digest.value,
        "actor": actor,
        "reason": reason,
        "decided_at": _time(decision.decided_at),
        "decision_digest": decision.digest.value,
    }
    document = {**core, "activation_evidence_digest": digest_of(core).value}
    return _seal(
        document,
        result_directory,
        f"JWT-STRATEGY-ACTIVATION-{decision.decision_id.value}",
    )


def _capability_and_strategy(
    run_configuration: Mapping[str, object],
    implementation_digest: Digest,
    world_schema: str,
    comparison_schema: str,
) -> tuple[CapabilityDefinition, StrategyDefinition]:
    capability = CapabilityDefinition(
        capability_id=CAPABILITY_ID,
        contract_version=CAPABILITY_CONTRACT_VERSION,
        purpose="Evaluate exact JWT commit impact through formal knowledge",
        input_contract_digest=Digest(run_configuration["requirement"]["requirement_digest"]),
        output_contract_digest=digest_of(
            {
                "world_model_result_schema": world_schema,
                "comparison_schema": comparison_schema,
            }
        ),
    )
    strategy = StrategyDefinition(
        strategy_id=STRATEGY_ID,
        strategy_version=_strategy_version(run_configuration),
        capability_id=CAPABILITY_ID,
        capability_contract_version=CAPABILITY_CONTRACT_VERSION,
        kind=StrategyKind.MODEL_PRIMARY,
        implementation_digest=implementation_digest,
        requires_model=True,
    )
    return capability, strategy


_WORLD_RUNTIME_HARNESS_PATHS = {
    "validation/jwt_iteration_001/manifest.py",
    "validation/jwt_iteration_001/direct_agent.py",
    "validation/jwt_iteration_001/world_model.py",
    "src/software_world_model/ai_infrastructure/ark_chat_conformance.py",
    "src/software_world_model/ai_infrastructure/volcengine_ark_chat_adapter.py",
}


def _world_runtime_implementation_digest(
    run_configuration: Mapping[str, object],
) -> Digest:
    files = run_configuration.get("harness", {}).get("files", [])
    runtime_files = [
        item
        for item in files
        if isinstance(item, dict)
        and item.get("path") in _WORLD_RUNTIME_HARNESS_PATHS
    ]
    if {item["path"] for item in runtime_files} != _WORLD_RUNTIME_HARNESS_PATHS:
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "run configuration does not bind every World runtime implementation file",
        )
    return digest_of(runtime_files)


def _strategy_version(run_configuration: Mapping[str, object]) -> str:
    suffix = _world_runtime_implementation_digest(run_configuration).value.removeprefix(
        "sha256:"
    )[:12]
    return f"{STRATEGY_VERSION_BASE}+{suffix}"


def _evaluation_version(run_configuration: Mapping[str, object]) -> str:
    suffix = str(run_configuration["configuration_digest"]).removeprefix("sha256:")[:12]
    return f"{EVALUATION_VERSION_BASE}+{suffix}"


def _load(path: str | Path, label: str) -> dict[str, object]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} cannot be read") from exc
    if not isinstance(value, dict):
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} must be an object")
    return value


def _seal(document: Mapping[str, object], directory: str | Path, name: str) -> Path:
    result_directory = Path(directory)
    result_directory.mkdir(parents=True, exist_ok=True)
    path = result_directory / f"{name}.json"
    payload = json.dumps(document, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8") + b"\n"
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        try:
            if path.read_bytes() == payload:
                return path
        except OSError:
            pass
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "CE evidence path exists with different content",
        ) from exc
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    return path
