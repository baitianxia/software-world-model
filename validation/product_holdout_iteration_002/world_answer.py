"""Evaluation-only assembly of the production formal-knowledge answer path."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Protocol

from software_world_model.ai_infrastructure import (
    AgenticModelStrategyConfiguration,
    ModelGateway,
    agentic_knowledge_strategy_implementation_digest,
)
from software_world_model.application_services import (
    BuildObjective,
    CanonicalBuildTarget,
    KnowledgeUpdateRequest,
    LiveIntegrationPolicy,
    NATURAL_TASK_CAPABILITY_CONTRACT_VERSION,
    NATURAL_TASK_CAPABILITY_ID,
    NaturalLanguageTaskRequest,
    QualificationProof,
    StrategyActivationService,
)
from software_world_model.cross_cutting import (
    CorrelationRef,
    DomainError,
    ErrorCode,
    IdempotencyKey,
    Revision,
)
from software_world_model.infrastructure import (
    SqliteDatabase,
    SqliteKnowledgeScopeRepository,
    SqliteSourceConfigurationRepository,
    SqliteStrategyActivationRepository,
)
from software_world_model.interface.agentic_runtime import (
    agentic_task_capability_registry,
    agentic_task_strategy_definition,
    assemble_activated_task_services,
)
from software_world_model.knowledge_engine import (
    KnowledgeScopeService,
    ScopePurpose,
    ScopeType,
)
from software_world_model.source_integration import (
    LocalGitConfigurationProvider,
    LocalGitConnector,
    LocalGitTargetResolver,
    ProviderRegistry,
    SourceConfigurationService,
)

from .execution import HoldoutAnswerPath, HoldoutPathResult, SealedAnswerClaim


class QualificationVerifier(Protocol):
    def validate(self, proof: QualificationProof) -> bool: ...


@dataclass(frozen=True, slots=True)
class _ExactEvaluationVerifier:
    expected: QualificationProof
    current: QualificationVerifier

    def validate(self, proof: QualificationProof) -> bool:
        return (
            proof == self.expected
            and proof.verify_digest()
            and self.current.validate(proof)
        )


@dataclass(frozen=True, slots=True)
class _Usage:
    actual_model_fingerprint: str
    provider_request_ids: tuple[str, ...]
    model_call_count: int
    source_action_count: int
    source_byte_count: int
    input_tokens: int
    output_tokens: int
    usage_complete: bool


class _BudgetedModelGateway:
    """Enforce the sealed task budget before every model dispatch attempt."""

    def __init__(self, delegate: ModelGateway, policy: Mapping[str, object]) -> None:
        self._delegate = delegate
        self._maximum_calls = _positive_limit(
            policy, "maximum_model_calls"
        )
        self._maximum_input_tokens = _positive_limit(
            policy, "maximum_total_input_tokens"
        )
        self._maximum_output_tokens = _positive_limit(
            policy, "maximum_total_output_tokens"
        )
        self._calls = 0
        self._input_tokens = 0
        self._output_tokens = 0
        self._exhaustion: DomainError | None = None

    @property
    def exhaustion(self) -> DomainError | None:
        return self._exhaustion

    def invoke(self, context: object) -> object:
        if self._calls >= self._maximum_calls:
            self._exhaustion = DomainError(
                ErrorCode.BUDGET_EXHAUSTED,
                "system-assisted model call budget is exhausted",
                {
                    "maximum_model_calls": self._maximum_calls,
                    "attempted_model_call": self._calls + 1,
                },
            )
            raise self._exhaustion
        self._calls += 1
        result = self._delegate.invoke(context)
        response = getattr(result, "response", None)
        input_tokens = getattr(response, "input_tokens", None)
        output_tokens = getattr(response, "output_tokens", None)
        if isinstance(input_tokens, int) and not isinstance(input_tokens, bool):
            self._input_tokens += input_tokens
        if isinstance(output_tokens, int) and not isinstance(output_tokens, bool):
            self._output_tokens += output_tokens
        if (
            self._input_tokens > self._maximum_input_tokens
            or self._output_tokens > self._maximum_output_tokens
        ):
            self._exhaustion = DomainError(
                ErrorCode.BUDGET_EXHAUSTED,
                "system-assisted model token budget is exhausted",
                {
                    "maximum_total_input_tokens": self._maximum_input_tokens,
                    "actual_input_tokens": self._input_tokens,
                    "maximum_total_output_tokens": self._maximum_output_tokens,
                    "actual_output_tokens": self._output_tokens,
                },
            )
            raise self._exhaustion
        return result

    def recover_call(self, model_call_id: object) -> object:
        return self._delegate.recover_call(model_call_id)

    def authorized_manifest(self, model_call_id: object) -> object:
        return self._delegate.authorized_manifest(model_call_id)


class WorldAssistedAnswerExecutor:
    """Run the exact production services under an isolated evaluation permit.

    The permit is scoped to one suite and task.  It is not a product validation
    attestation and must never be copied into the production activation store.
    """

    def __init__(
        self,
        *,
        database: SqliteDatabase,
        gateway: ModelGateway,
        configuration: AgenticModelStrategyConfiguration,
        qualification: QualificationProof,
        qualification_verifier: QualificationVerifier,
        expected_model_fingerprint: str,
        origin: str = "formal-knowledge-system-answer",
    ) -> None:
        self._database = database
        self._gateway = gateway
        self._configuration = configuration
        self._qualification = qualification
        self._verifier = qualification_verifier
        self._expected_model_fingerprint = _text(
            expected_model_fingerprint, "expected model fingerprint"
        )
        self._origin = _text(origin, "system-assisted answer origin")

    def execute(
        self,
        *,
        task_input: Mapping[str, object],
        checkout_path: str | Path,
        run_id: str,
    ) -> HoldoutPathResult:
        _verify_task_input_digest(task_input)
        run_id = _text(run_id, "system-assisted answer run ID")
        checkout = Path(checkout_path).resolve()
        if not checkout.is_dir():
            raise DomainError(
                ErrorCode.SOURCE_TARGET_NOT_FOUND,
                "sealed evaluation checkout does not exist",
            )
        connector = LocalGitConnector(str(checkout))
        frozen = task_input["repository"]["frozen_commit"]
        if connector.resolve_revision(frozen) != frozen:
            raise DomainError(
                ErrorCode.SOURCE_REVISION_INCONSISTENT,
                "system-assisted checkout does not contain the sealed revision",
            )
        policy = task_input["resource_policy"]
        if (
            self._configuration.max_output_tokens
            != policy["maximum_output_tokens_per_call"]
            or self._configuration.timeout_milliseconds
            != policy["timeout_per_call_milliseconds"]
            or self._configuration.qualification_ref != self._qualification.proof_ref
            or not self._verifier.validate(self._qualification)
        ):
            raise DomainError(
                ErrorCode.QUALIFICATION_INVALID,
                "system-assisted evaluation configuration or qualification is not current",
            )
        strategy = agentic_task_strategy_definition()
        if (
            self._qualification.capability_id != NATURAL_TASK_CAPABILITY_ID
            or self._qualification.capability_contract_version
            != NATURAL_TASK_CAPABILITY_CONTRACT_VERSION
            or self._qualification.strategy_id != strategy.strategy_id
            or self._qualification.strategy_version != strategy.strategy_version
        ):
            raise DomainError(
                ErrorCode.QUALIFICATION_INVALID,
                "capability evaluation does not qualify the current system-assisted strategy",
            )

        activation_scope = {
            "environment": "sealed-product-evaluation",
            "suite": str(task_input["suite_id"]),
            "task": str(task_input["task_id"]),
        }
        activation = StrategyActivationService(
            SqliteStrategyActivationRepository(self._database),
            agentic_task_capability_registry(),
            _ExactEvaluationVerifier(self._qualification, self._verifier),
            live_policy=LiveIntegrationPolicy(model_strategy_activation_enabled=True),
        )
        activation.activate_strategy(
            capability_id=NATURAL_TASK_CAPABILITY_ID,
            capability_contract_version=NATURAL_TASK_CAPABILITY_CONTRACT_VERSION,
            activation_scope=activation_scope,
            expected_revision=None,
            strategy_id=strategy.strategy_id,
            strategy_version=strategy.strategy_version,
            qualification=self._qualification,
            idempotency_key=IdempotencyKey(f"holdout-evaluation-permit:{run_id}"),
            actor="product-validation-runner",
            reason="run one sealed task without granting production activation",
            correlation_ref=CorrelationRef(f"holdout-evaluation:{run_id}"),
        )

        scopes = KnowledgeScopeService(
            SqliteKnowledgeScopeRepository(self._database)
        )
        scope = scopes.create_scope(
            scope_type=ScopeType.SYSTEM,
            metadata={
                "display_name": f"sealed product evaluation {task_input['task_id']}",
                "suite_id": str(task_input["suite_id"]),
                "task_input_digest": str(task_input["task_input_digest"]),
            },
            idempotency_key=IdempotencyKey(f"holdout-scope:{run_id}"),
            actor="product-validation-runner",
            reason="isolate one sealed product validation task",
            correlation_ref=CorrelationRef(f"holdout-evaluation:{run_id}"),
        )
        sources = SourceConfigurationService(
            SqliteSourceConfigurationRepository(self._database),
            ProviderRegistry((LocalGitConfigurationProvider(),)),
            scopes,
        )
        source = sources.register_data_source(
            provider_type="LOCAL_GIT",
            provider_contract_version="0.1.0",
            identity_domain=f"product-evaluation:{task_input['suite_id']}",
            source_target=str(checkout),
            provider_configuration={"read_mode": "read_only"},
            secret_reference=None,
            idempotency_key=IdempotencyKey(f"holdout-source:{run_id}"),
            actor="product-validation-runner",
            reason="register the sealed read-only validation checkout",
            correlation_ref=CorrelationRef(f"holdout-evaluation:{run_id}"),
        )
        assertion = scopes.read_scope_state_assertion(
            scope_id=scope.scope_id,
            expected_revision=Revision(1),
            purpose=ScopePurpose.BIND_CONFIGURATION,
            caller_ref="product-validation-runner",
            request_ref=f"holdout-binding:{run_id}",
            classification=self._configuration.classification,
        )
        binding = sources.bind_source_to_scope(
            source_id=source.source_id,
            assertion=assertion,
            selector={"paths": ",".join(task_input["allowed_paths"])},
            context_constraint={"revision_policy": "exact"},
            context_hint=f"sealed task {task_input['task_id']}",
            idempotency_key=IdempotencyKey(f"holdout-binding:{run_id}"),
            actor="product-validation-runner",
            reason="restrict source access to the sealed task paths",
            correlation_ref=CorrelationRef(f"holdout-evaluation:{run_id}"),
        )

        resolver = LocalGitTargetResolver(connector)
        revision_scope = task_input["revision_scope"]
        receipt = (
            resolver.resolve_revision(revision_scope["target"])
            if revision_scope["kind"] == "FROZEN_SNAPSHOT"
            else resolver.resolve_comparison(
                revision_scope["parent"], revision_scope["target"]
            )
        )
        target = CanonicalBuildTarget.from_receipt(receipt)
        task_key = f"holdout-task:{run_id}"
        update_request = KnowledgeUpdateRequest(
            idempotency_key=IdempotencyKey(f"{task_key}:knowledge-update"),
            objective=BuildObjective.create(
                objective_id=f"holdout-objective:{task_input['task_id']}",
                description=str(task_input["question"]),
                unacceptable_outcomes=(
                    "answering from hidden model knowledge",
                    "reading a path or revision outside the sealed task",
                    "claiming complete source support from incomplete observations",
                ),
            ),
            target=target,
            allowed_source_paths=tuple(task_input["allowed_paths"]),
            required_source_paths=tuple(task_input["allowed_paths"]),
            scope_id=scope.scope_id,
            scope_revision=Revision(1),
            source_id=source.source_id,
            source_revision=source.definition_revision,
            binding_id=binding.binding_id,
            binding_revision=binding.definition_revision,
            expected_current_snapshot_id=None,
            max_steps=policy["maximum_source_actions"],
            max_items_per_step=200,
            max_bytes_per_step=policy["maximum_source_bytes_per_action"],
            classification=self._configuration.classification,
            actor="product-validation-runner",
            correlation_ref=CorrelationRef(f"holdout-evaluation:{run_id}"),
        )
        budgeted_gateway = _BudgetedModelGateway(self._gateway, policy)
        assembly = assemble_activated_task_services(
            database=self._database,
            gateway=budgeted_gateway,
            model_configuration=self._configuration,
            activation=activation,
            activation_scope=activation_scope,
        )
        try:
            answer = assembly.natural_tasks.execute(
                NaturalLanguageTaskRequest.create(
                    conversation_ref=f"holdout-conversation:{run_id}",
                    turn_ref="turn:1",
                    request_ref=f"holdout-request:{run_id}",
                    idempotency_key=IdempotencyKey(task_key),
                    original_request=str(task_input["question"]),
                    caller_ref="product-validation-runner",
                    classification=self._configuration.classification,
                    scope_id=scope.scope_id,
                    snapshot_id=None,
                    knowledge_update_request=update_request,
                )
            )
        except DomainError as exc:
            if budgeted_gateway.exhaustion is not None:
                raise budgeted_gateway.exhaustion from exc
            raise
        usage = _collect_usage(self._database)
        if usage.actual_model_fingerprint != self._expected_model_fingerprint:
            raise DomainError(
                ErrorCode.QUALIFICATION_INVALID,
                "system-assisted path used an unexpected actual model",
            )
        claims = _sealed_claims(
            answer.candidate.claims, answer.assessment.assessment_id.value
        )
        return HoldoutPathResult.create(
            result_ref=f"world-assisted-answer-result:{run_id}",
            run_id=run_id,
            path=HoldoutAnswerPath.WORLD_ASSISTED,
            origin=self._origin,
            implementation_digest=agentic_knowledge_strategy_implementation_digest(),
            task_input=task_input,
            answer=answer.candidate.body,
            claims=claims,
            actual_model_fingerprint=usage.actual_model_fingerprint,
            provider_request_ids=usage.provider_request_ids,
            model_call_count=usage.model_call_count,
            source_action_count=usage.source_action_count,
            source_byte_count=usage.source_byte_count,
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            usage_complete=usage.usage_complete,
        )


def _sealed_claim(claim: object, assessment_id: str) -> SealedAnswerClaim:
    references: list[str] = []
    if claim.formal_reference is not None:
        references.append(claim.formal_reference.value)
    if claim.support_proof_id is not None:
        references.append(claim.support_proof_id.value)
    if not references:
        references.append(f"assessment:{assessment_id}:need:{claim.need_id}")
    return SealedAnswerClaim(claim.text, tuple(references))


def _sealed_claims(
    claims: tuple[object, ...], assessment_id: str
) -> tuple[SealedAnswerClaim, ...]:
    ordered: list[SealedAnswerClaim] = []
    positions: dict[str, int] = {}
    for claim in claims:
        sealed = _sealed_claim(claim, assessment_id)
        position = positions.get(sealed.claim)
        if position is None:
            positions[sealed.claim] = len(ordered)
            ordered.append(sealed)
            continue
        existing = ordered[position]
        merged_references = tuple(
            dict.fromkeys(existing.support_references + sealed.support_references)
        )
        ordered[position] = SealedAnswerClaim(existing.claim, merged_references)
    return tuple(ordered)


def _collect_usage(database: SqliteDatabase) -> _Usage:
    with database.read() as connection:
        roots = connection.execute(
            "SELECT current_state FROM ai_model_call_roots"
        ).fetchall()
        outputs = connection.execute(
            """SELECT provider_request_id, actual_model_fingerprint,
                      input_tokens, output_tokens, usage_complete
               FROM ai_model_call_outputs ORDER BY model_call_id"""
        ).fetchall()
        source = connection.execute(
            "SELECT COUNT(*) AS calls, COALESCE(SUM(byte_count), 0) AS bytes FROM src_observations"
        ).fetchone()
    if (
        not roots
        or len(outputs) != len(roots)
        or any(row["current_state"] != "COMPLETED" for row in roots)
        or any(
            not row["provider_request_id"]
            or not row["actual_model_fingerprint"]
            or row["input_tokens"] is None
            or row["output_tokens"] is None
            or row["usage_complete"] != 1
            for row in outputs
        )
    ):
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "system-assisted model usage is incomplete",
        )
    fingerprints = {row["actual_model_fingerprint"] for row in outputs}
    request_ids = tuple(row["provider_request_id"] for row in outputs)
    if len(fingerprints) != 1 or len(set(request_ids)) != len(request_ids):
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "system-assisted path changed model identity or reused a provider request",
        )
    return _Usage(
        actual_model_fingerprint=next(iter(fingerprints)),
        provider_request_ids=request_ids,
        model_call_count=len(outputs),
        source_action_count=source["calls"],
        source_byte_count=source["bytes"],
        input_tokens=sum(row["input_tokens"] for row in outputs),
        output_tokens=sum(row["output_tokens"] for row in outputs),
        usage_complete=True,
    )


def _verify_task_input_digest(task_input: Mapping[str, object]) -> None:
    from software_world_model.cross_cutting import digest_of

    digest = task_input.get("task_input_digest")
    if not isinstance(digest, str) or digest_of(
        {key: value for key, value in task_input.items() if key != "task_input_digest"}
    ).value != digest:
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "system-assisted task input digest is invalid",
        )


def _positive_limit(policy: Mapping[str, object], field: str) -> int:
    value = policy.get(field)
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            f"system-assisted resource policy {field} must be positive",
        )
    return value


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} must be non-empty")
    return value
