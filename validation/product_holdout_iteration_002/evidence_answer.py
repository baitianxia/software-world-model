"""Evaluation-only executor for the production evidence-first answer path."""

from __future__ import annotations

from pathlib import Path
from typing import Mapping

from software_world_model.ai_infrastructure import (
    AgenticModelStrategyConfiguration,
    ModelGateway,
    evidence_first_task_strategy_implementation_digest,
)
from software_world_model.application_services import (
    BuildObjective,
    CanonicalBuildTarget,
    EVIDENCE_ANSWER_CAPABILITY_CONTRACT_VERSION,
    EVIDENCE_ANSWER_CAPABILITY_ID,
    EvidenceAnswerRequest,
    KnowledgeUpdateRequest,
    LiveIntegrationPolicy,
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
    assemble_activated_evidence_services,
    evidence_task_capability_registry,
    evidence_task_strategy_definition,
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
from .world_answer import (
    QualificationVerifier,
    _BudgetedModelGateway,
    _ExactEvaluationVerifier,
    _collect_usage,
    _text,
    _verify_task_input_digest,
)


class EvidenceFirstAnswerExecutor:
    """Run the exact synchronous evidence path under an isolated evaluation permit."""

    def __init__(
        self,
        *,
        database: SqliteDatabase,
        gateway: ModelGateway,
        configuration: AgenticModelStrategyConfiguration,
        qualification: QualificationProof,
        qualification_verifier: QualificationVerifier,
        expected_model_fingerprint: str,
        origin: str = "evidence-first-system-answer",
    ) -> None:
        self._database = database
        self._gateway = gateway
        self._configuration = configuration
        self._qualification = qualification
        self._verifier = qualification_verifier
        self._expected_model_fingerprint = _text(
            expected_model_fingerprint, "expected model fingerprint"
        )
        self._origin = _text(origin, "evidence-first answer origin")

    def execute(
        self,
        *,
        task_input: Mapping[str, object],
        checkout_path: str | Path,
        run_id: str,
    ) -> HoldoutPathResult:
        _verify_task_input_digest(task_input)
        run_id = _text(run_id, "evidence-first answer run ID")
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
                "evidence evaluation checkout does not contain the sealed revision",
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
                "evidence evaluation configuration or qualification is not current",
            )
        strategy = evidence_task_strategy_definition()
        if (
            self._qualification.capability_id != EVIDENCE_ANSWER_CAPABILITY_ID
            or self._qualification.capability_contract_version
            != EVIDENCE_ANSWER_CAPABILITY_CONTRACT_VERSION
            or self._qualification.strategy_id != strategy.strategy_id
            or self._qualification.strategy_version != strategy.strategy_version
            or strategy.implementation_digest
            != evidence_first_task_strategy_implementation_digest()
        ):
            raise DomainError(
                ErrorCode.QUALIFICATION_INVALID,
                "capability evaluation does not qualify the evidence-first strategy",
            )

        activation_scope = {
            "environment": "sealed-product-evaluation",
            "suite": str(task_input["suite_id"]),
            "task": str(task_input["task_id"]),
        }
        activation = StrategyActivationService(
            SqliteStrategyActivationRepository(self._database),
            evidence_task_capability_registry(),
            _ExactEvaluationVerifier(self._qualification, self._verifier),
            live_policy=LiveIntegrationPolicy(model_strategy_activation_enabled=True),
        )
        activation.activate_strategy(
            capability_id=EVIDENCE_ANSWER_CAPABILITY_ID,
            capability_contract_version=EVIDENCE_ANSWER_CAPABILITY_CONTRACT_VERSION,
            activation_scope=activation_scope,
            expected_revision=None,
            strategy_id=strategy.strategy_id,
            strategy_version=strategy.strategy_version,
            qualification=self._qualification,
            idempotency_key=IdempotencyKey(
                f"holdout-evidence-evaluation-permit:{run_id}"
            ),
            actor="product-validation-runner",
            reason="run one sealed evidence task without granting production activation",
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
            idempotency_key=IdempotencyKey(f"holdout-evidence-scope:{run_id}"),
            actor="product-validation-runner",
            reason="isolate one sealed evidence product validation task",
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
            idempotency_key=IdempotencyKey(f"holdout-evidence-source:{run_id}"),
            actor="product-validation-runner",
            reason="register the sealed read-only evidence checkout",
            correlation_ref=CorrelationRef(f"holdout-evaluation:{run_id}"),
        )
        assertion = scopes.read_scope_state_assertion(
            scope_id=scope.scope_id,
            expected_revision=Revision(1),
            purpose=ScopePurpose.BIND_CONFIGURATION,
            caller_ref="product-validation-runner",
            request_ref=f"holdout-evidence-binding:{run_id}",
            classification=self._configuration.classification,
        )
        binding = sources.bind_source_to_scope(
            source_id=source.source_id,
            assertion=assertion,
            selector={"paths": ",".join(task_input["allowed_paths"])},
            context_constraint={"revision_policy": "exact"},
            context_hint=f"sealed task {task_input['task_id']}",
            idempotency_key=IdempotencyKey(f"holdout-evidence-binding:{run_id}"),
            actor="product-validation-runner",
            reason="restrict evidence reads to the sealed task paths",
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
        task_key = f"holdout-evidence-task:{run_id}"
        source_request = KnowledgeUpdateRequest(
            idempotency_key=IdempotencyKey(f"{task_key}:source"),
            objective=BuildObjective.create(
                objective_id=f"holdout-evidence-objective:{task_input['task_id']}",
                description=str(task_input["question"]),
                unacceptable_outcomes=(
                    "answering from hidden model knowledge",
                    "reading a path or revision outside the sealed task",
                    "claiming source support not present in the sealed evidence packet",
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
        assembly = assemble_activated_evidence_services(
            database=self._database,
            gateway=budgeted_gateway,
            model_configuration=self._configuration,
            activation=activation,
            activation_scope=activation_scope,
        )
        try:
            answer = assembly.evidence_answering.execute(
                EvidenceAnswerRequest(
                    idempotency_key=IdempotencyKey(task_key),
                    original_request=str(task_input["question"]),
                    source_request=source_request,
                    classification=self._configuration.classification,
                    caller_ref="product-validation-runner",
                    correlation_ref=CorrelationRef(f"holdout-evaluation:{run_id}"),
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
                "evidence-first path used an unexpected actual model",
            )
        evidence_by_id = {
            item.evidence_id: item for item in answer.evidence_packet.items
        }
        claims = tuple(
            SealedAnswerClaim(
                section.text,
                tuple(
                    "source-artifact:"
                    f"{evidence_by_id[evidence_id].artifact_id.value}:"
                    f"{evidence_by_id[evidence_id].content_digest.value}"
                    for evidence_id in section.evidence_ids
                )
                or (f"reviewed-unknown:{answer.review.digest.value}",),
            )
            for section in answer.draft.sections
        )
        return HoldoutPathResult.create(
            result_ref=f"evidence-first-answer-result:{run_id}",
            run_id=run_id,
            path=HoldoutAnswerPath.WORLD_ASSISTED,
            origin=self._origin,
            implementation_digest=evidence_first_task_strategy_implementation_digest(),
            task_input=task_input,
            answer="\n".join(item.claim for item in claims),
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
