"""Composition root shared by CLI and HTTP interfaces."""

from __future__ import annotations

from typing import Mapping

from software_world_model.application_services import (
    AuthorizedEvidenceAnswer,
    BuildObjective,
    CanonicalBuildTarget,
    AuthorizedTaskAnswer,
    ConfigureSystemSourceCommand,
    EvidenceAnswerRequest,
    EvidenceAnswerService,
    KnowledgeNeed,
    KnowledgeRequirement,
    KnowledgeRequirementPlanner,
    KnowledgeUpdateRequest,
    KnowledgeUpdateResult,
    KnowledgeUpdateService,
    KnowledgeUseService,
    ManagementApplicationService,
    ManagementExecution,
    NaturalLanguageTaskRequest,
    NaturalLanguageTaskService,
    NeedSufficiencyEvaluator,
    RequirementFidelity,
    SufficiencyAssessment,
    TaskBoundary,
)
from software_world_model.cross_cutting import (
    CorrelationRef,
    DomainError,
    ErrorCode,
    IdempotencyKey,
    Revision,
    StableId,
    TelemetryMetric,
    TelemetryRecorder,
    digest_of,
)
from software_world_model.infrastructure import (
    SqliteDatabase,
    SqliteFormalKnowledgeRepository,
    SqliteKnowledgeScopeRepository,
    SqliteKnowledgeUpdateRepository,
    SqliteKnowledgeUseRepository,
    SqliteManagementRepository,
    SqliteSourceConfigurationRepository,
    SqliteSourceOperationRepository,
    SqliteTelemetryRepository,
)
from software_world_model.knowledge_engine import (
    FormalKnowledgeService,
    KnowledgeScopeService,
    ScopeType,
)
from software_world_model.source_integration import (
    DataSourceBinding,
    LocalGitConfigurationProvider,
    LocalGitConnector,
    LocalGitTargetResolver,
    ProviderRegistry,
    SourceConfigurationService,
    SourceOperationService,
    SourceTargetResolutionReceipt,
    TargetKind,
)


class ApplicationRuntime:
    """Wire public owner services without granting interfaces direct table access."""

    def __init__(
        self,
        database: SqliteDatabase,
        *,
        telemetry: TelemetryRecorder | None = None,
        requirement_planner: KnowledgeRequirementPlanner | None = None,
        sufficiency_evaluator: NeedSufficiencyEvaluator | None = None,
        natural_task_service: NaturalLanguageTaskService | None = None,
        evidence_answer_service: EvidenceAnswerService | None = None,
    ) -> None:
        self.database = database
        self.telemetry = telemetry or SqliteTelemetryRepository(database)
        self.scopes = KnowledgeScopeService(SqliteKnowledgeScopeRepository(database))
        self.sources = SourceConfigurationService(
            SqliteSourceConfigurationRepository(database),
            ProviderRegistry((LocalGitConfigurationProvider(),)),
            self.scopes,
        )
        self.management = ManagementApplicationService(
            SqliteManagementRepository(database),
            self.scopes,
            self.sources,
        )
        self.source_operations = SourceOperationService(
            SqliteSourceOperationRepository(database), self.sources, telemetry=self.telemetry
        )
        self.knowledge = FormalKnowledgeService(
            SqliteFormalKnowledgeRepository(database), self.scopes
        )
        self.knowledge_updates = KnowledgeUpdateService(
            SqliteKnowledgeUpdateRepository(database),
            self.scopes,
            self.sources,
            self.source_operations,
            self.knowledge,
        )
        self._requirement_planner = requirement_planner
        self._natural_task_service = natural_task_service
        self._evidence_answer_service = evidence_answer_service
        self.knowledge_use = KnowledgeUseService(
            SqliteKnowledgeUseRepository(database),
            self.knowledge,
            evaluator=sufficiency_evaluator,
        )

    @property
    def natural_task_planning_configured(self) -> bool:
        return self._requirement_planner is not None

    @property
    def reviewed_answer_preparation_configured(self) -> bool:
        return (
            (
                self._evidence_answer_service is not None
                and self._evidence_answer_service.is_currently_active()
            )
            or (
                self._natural_task_service is not None
                and self._natural_task_service.is_currently_active()
            )
        )

    @property
    def evidence_answer_preparation_configured(self) -> bool:
        return (
            self._evidence_answer_service is not None
            and self._evidence_answer_service.is_currently_active()
        )

    def prepare_evidence_answer(
        self, request: EvidenceAnswerRequest
    ) -> AuthorizedEvidenceAnswer:
        if self._evidence_answer_service is None:
            raise DomainError(
                ErrorCode.LIVE_INTEGRATION_HELD,
                "evidence-first answer preparation is not activated",
            )
        result = self._evidence_answer_service.execute(request)
        self.telemetry.record(
            owner="application-services",
            operation="evidence-answer-preparation@1",
            outcome=result.review.decision.value,
            correlation_reference=request.correlation_ref.value,
            causation_reference=request.idempotency_key.value,
            authority_references=(
                result.checklist.digest.value,
                result.evidence_packet.digest.value,
                result.draft.digest.value,
                result.review.digest.value,
                result.digest.value,
            ),
            metrics=(
                TelemetryMetric(
                    "checklist_items", len(result.checklist.items), "items"
                ),
                TelemetryMetric(
                    "evidence_items", len(result.evidence_packet.items), "items"
                ),
                TelemetryMetric(
                    "answer_sections", len(result.draft.sections), "sections"
                ),
                TelemetryMetric(
                    "source_operations", result.source_operation_count, "operations"
                ),
            ),
            classification=request.classification,
        )
        return result

    def prepare_task_answer(
        self, request: NaturalLanguageTaskRequest
    ) -> AuthorizedTaskAnswer:
        """Prepare and authorize an answer without claiming transport delivery."""

        if self._natural_task_service is None:
            raise DomainError(
                ErrorCode.LIVE_INTEGRATION_HELD,
                "reviewed natural-language answer preparation is not activated",
            )
        result = self._natural_task_service.execute(request)
        self.telemetry.record(
            owner="application-services",
            operation="natural-task-answer-preparation@1",
            outcome=result.review.decision.value,
            correlation_reference=request.request_ref,
            causation_reference=request.idempotency_key.value,
            authority_references=(
                result.task.task_id.value,
                result.candidate.candidate_id.value,
                result.authorization.authorization_id.value,
                result.digest.value,
            ),
            metrics=(
                TelemetryMetric("needs", len(result.requirement.needs), "needs"),
                TelemetryMetric("claims", len(result.candidate.claims), "claims"),
            ),
            classification=request.classification,
        )
        return result

    def configure_local_git_project(
        self,
        *,
        idempotency_key: IdempotencyKey,
        source_target: str,
        selected_paths: str,
        display_name: str,
        actor: str,
        correlation_ref: CorrelationRef,
    ) -> ManagementExecution:
        """Configure one browser-visible project through the management owner path."""

        command = ConfigureSystemSourceCommand.create(
            idempotency_key=idempotency_key,
            caller="browser-chat",
            purpose="configure a local project for browser chat",
            classification="INTERNAL",
            request_context={"interface": "browser-chat"},
            scope_type=ScopeType.SYSTEM,
            scope_metadata={"display_name": display_name},
            provider_type=LocalGitConfigurationProvider.provider_type,
            provider_contract_version=(
                LocalGitConfigurationProvider.contract_version
            ),
            identity_domain="LOCAL",
            source_target=source_target,
            provider_configuration={"read_mode": "read_only"},
            secret_reference=None,
            selector={"paths": selected_paths},
            context_constraint={"revision_policy": "exact"},
            context_hint=display_name,
            actor=actor,
            reason="connect local project for browser chat",
            correlation_ref=correlation_ref,
        )
        return self.management.configure(command)

    def resolve_target(
        self,
        *,
        source_id: StableId,
        source_revision: Revision,
        binding_id: StableId,
        binding_revision: Revision,
        target_kind: TargetKind,
        parameters: Mapping[str, str],
    ) -> SourceTargetResolutionReceipt:
        source = self.sources.get_data_source(source_id, source_revision)
        binding = self.sources.get_binding(binding_id, binding_revision)
        if binding.source_id != source.source_id:
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "binding belongs to another source")
        allowed_paths = _allowed_paths(binding)
        resolver = LocalGitTargetResolver(LocalGitConnector(source.canonical_source_target))
        if target_kind is TargetKind.REPOSITORY_REVISION:
            return resolver.resolve_revision(_required(parameters, "revision"))
        if target_kind is TargetKind.REVISION_COMPARISON:
            return resolver.resolve_comparison(
                _required(parameters, "base"), _required(parameters, "target")
            )
        if target_kind is TargetKind.SOURCE_PATH:
            return resolver.resolve_path(
                _required(parameters, "revision"),
                _required(parameters, "path"),
                allowed_paths=allowed_paths,
            )
        if target_kind in {TargetKind.SYMBOL, TargetKind.JAVA_SYMBOL}:
            method = (
                resolver.resolve_symbol
                if target_kind is TargetKind.SYMBOL
                else resolver.resolve_java_symbol
            )
            return method(
                _required(parameters, "revision"),
                _required(parameters, "symbol"),
                allowed_paths=allowed_paths,
            )
        raise DomainError(ErrorCode.INVALID_ARGUMENT, "unsupported target kind")

    def update_knowledge(
        self,
        *,
        idempotency_key: IdempotencyKey,
        scope_id: StableId,
        scope_revision: Revision,
        source_id: StableId,
        source_revision: Revision,
        binding_id: StableId,
        binding_revision: Revision,
        target_kind: TargetKind,
        target_parameters: Mapping[str, str],
        objective_description: str,
        classification: str,
        actor: str,
        correlation_ref: CorrelationRef,
        max_steps: int = 8,
        max_items_per_step: int = 100,
        max_bytes_per_step: int = 256_000,
    ) -> KnowledgeUpdateResult:
        current = self.knowledge.current_snapshot(scope_id)
        request = self.prepare_knowledge_update_request(
            idempotency_key=idempotency_key,
            scope_id=scope_id,
            scope_revision=scope_revision,
            source_id=source_id,
            source_revision=source_revision,
            binding_id=binding_id,
            binding_revision=binding_revision,
            target_kind=target_kind,
            target_parameters=target_parameters,
            objective_description=objective_description,
            classification=classification,
            actor=actor,
            correlation_ref=correlation_ref,
            expected_current_snapshot_id=(
                current.snapshot_id if current else None
            ),
            max_steps=max_steps,
            max_items_per_step=max_items_per_step,
            max_bytes_per_step=max_bytes_per_step,
        )
        result = self.knowledge_updates.execute(request)
        self.telemetry.record(
            owner="application-services",
            operation="knowledge-update@1",
            outcome=result.state.value,
            correlation_reference=correlation_ref.value,
            causation_reference=idempotency_key.value,
            authority_references=(result.result_id.value, result.digest.value),
            metrics=(
                TelemetryMetric(
                    "source_operations", len(result.source_operation_references), "operations"
                ),
                TelemetryMetric("artifacts", len(result.artifact_references), "artifacts"),
            ),
            classification=classification,
        )
        return result

    def prepare_knowledge_update_request(
        self,
        *,
        idempotency_key: IdempotencyKey,
        scope_id: StableId,
        scope_revision: Revision,
        source_id: StableId,
        source_revision: Revision,
        binding_id: StableId,
        binding_revision: Revision,
        target_kind: TargetKind,
        target_parameters: Mapping[str, str],
        objective_description: str,
        classification: str,
        actor: str,
        correlation_ref: CorrelationRef,
        expected_current_snapshot_id: StableId | None,
        max_steps: int = 8,
        max_items_per_step: int = 100,
        max_bytes_per_step: int = 256_000,
        allowed_source_paths: tuple[str, ...] = (),
        required_source_paths: tuple[str, ...] = (),
    ) -> KnowledgeUpdateRequest:
        current = self.knowledge.current_snapshot(scope_id)
        current_id = current.snapshot_id if current else None
        if current_id != expected_current_snapshot_id:
            raise DomainError(
                ErrorCode.REVISION_CONFLICT,
                "knowledge investigation must start from the current exact snapshot",
            )
        receipt = self.resolve_target(
            source_id=source_id,
            source_revision=source_revision,
            binding_id=binding_id,
            binding_revision=binding_revision,
            target_kind=target_kind,
            parameters=target_parameters,
        )
        target = CanonicalBuildTarget.from_receipt(receipt)
        return KnowledgeUpdateRequest(
            idempotency_key=idempotency_key,
            objective=BuildObjective.create(
                objective_id=f"objective:{idempotency_key.value}",
                description=objective_description,
                unacceptable_outcomes=(
                    "source boundary expansion",
                    "incomplete target coverage reported as complete",
                ),
            ),
            target=target,
            scope_id=scope_id,
            scope_revision=scope_revision,
            source_id=source_id,
            source_revision=source_revision,
            binding_id=binding_id,
            binding_revision=binding_revision,
            expected_current_snapshot_id=expected_current_snapshot_id,
            max_steps=max_steps,
            max_items_per_step=max_items_per_step,
            max_bytes_per_step=max_bytes_per_step,
            classification=classification,
            actor=actor,
            correlation_ref=correlation_ref,
            allowed_source_paths=allowed_source_paths,
            required_source_paths=required_source_paths,
        )

    def prepare_evidence_answer_request(
        self,
        *,
        idempotency_key: IdempotencyKey,
        scope_id: StableId,
        scope_revision: Revision,
        source_id: StableId,
        source_revision: Revision,
        binding_id: StableId,
        binding_revision: Revision,
        target_kind: TargetKind,
        target_parameters: Mapping[str, str],
        original_request: str,
        classification: str,
        caller_ref: str,
        correlation_ref: CorrelationRef,
        max_steps: int = 16,
        max_items_per_step: int = 200,
        max_bytes_per_step: int = 24_000,
    ) -> EvidenceAnswerRequest:
        """Freeze one exact source boundary without depending on knowledge state."""

        receipt = self.resolve_target(
            source_id=source_id,
            source_revision=source_revision,
            binding_id=binding_id,
            binding_revision=binding_revision,
            target_kind=target_kind,
            parameters=target_parameters,
        )
        target = CanonicalBuildTarget.from_receipt(receipt)
        source_request = KnowledgeUpdateRequest(
            idempotency_key=IdempotencyKey(
                f"{idempotency_key.value}:source-authorization"
            ),
            objective=BuildObjective.create(
                objective_id=f"evidence-objective:{idempotency_key.value}",
                description=f"Collect evidence to answer: {original_request}",
                unacceptable_outcomes=(
                    "source boundary expansion",
                    "unsupported answer",
                ),
            ),
            target=target,
            scope_id=scope_id,
            scope_revision=scope_revision,
            source_id=source_id,
            source_revision=source_revision,
            binding_id=binding_id,
            binding_revision=binding_revision,
            expected_current_snapshot_id=None,
            max_steps=max_steps,
            max_items_per_step=max_items_per_step,
            max_bytes_per_step=max_bytes_per_step,
            classification=classification,
            actor=caller_ref,
            correlation_ref=correlation_ref,
        )
        return EvidenceAnswerRequest(
            idempotency_key=idempotency_key,
            original_request=original_request,
            source_request=source_request,
            classification=classification,
            caller_ref=caller_ref,
            correlation_ref=correlation_ref,
        )

    def query_knowledge(
        self,
        *,
        idempotency_key: IdempotencyKey,
        scope_id: StableId,
        snapshot_id: StableId | None,
        original_request: str,
        needs: tuple[KnowledgeNeed, ...],
        classification: str,
    ) -> SufficiencyAssessment:
        selected = (
            self.knowledge.get_snapshot(snapshot_id)
            if snapshot_id
            else self.knowledge.current_snapshot(scope_id)
        )
        if selected is None:
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "scope has no published knowledge snapshot")
        if selected.scope_id != scope_id:
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "snapshot belongs to another scope")
        identity = digest_of(
            {
                "idempotency_key": idempotency_key.value,
                "scope_id": scope_id.value,
                "snapshot_id": selected.snapshot_id.value,
                "original_request": original_request,
                "needs": needs,
                "classification": classification,
            }
        )
        requirement = KnowledgeRequirement.create(
            requirement_id=StableId(f"requirement_{identity.value[-32:]}"),
            revision=Revision(1),
            fidelity=RequirementFidelity.ORIGINAL,
            original_request=original_request,
            needs=needs,
        )
        boundary = TaskBoundary.create(
            task_id=StableId(f"cli_task_{identity.value[-32:]}"),
            task_revision=Revision(1),
            scope_id=scope_id,
            purpose="knowledge query",
            classification=classification,
        )
        session = self.knowledge_use.open_session(
            idempotency_key=IdempotencyKey(f"{idempotency_key.value}:session"),
            boundary=boundary,
            requirement=requirement,
            snapshot_id=selected.snapshot_id,
        )
        assessment = self.knowledge_use.assess(
            idempotency_key=IdempotencyKey(f"{idempotency_key.value}:assessment"),
            requirement=requirement,
            session=session,
        )
        self.telemetry.record(
            owner="application-services",
            operation="knowledge-use@1",
            outcome="SUFFICIENT" if assessment.sufficient else "INSUFFICIENT",
            correlation_reference=f"query:{idempotency_key.value}",
            causation_reference=idempotency_key.value,
            authority_references=(assessment.assessment_id.value, assessment.digest.value),
            metrics=(TelemetryMetric("needs", len(assessment.items), "needs"),),
            classification=classification,
        )
        return assessment

    def query_task(
        self,
        *,
        idempotency_key: IdempotencyKey,
        scope_id: StableId,
        snapshot_id: StableId | None,
        original_request: str,
        classification: str,
    ) -> SufficiencyAssessment:
        """Plan and assess a natural-language task without caller-authored Needs."""

        if self._requirement_planner is None:
            raise DomainError(
                ErrorCode.LIVE_INTEGRATION_HELD,
                "natural-language task planning is not configured or activated",
            )
        selected = (
            self.knowledge.get_snapshot(snapshot_id)
            if snapshot_id
            else self.knowledge.current_snapshot(scope_id)
        )
        if selected is None:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "scope has no published knowledge snapshot",
            )
        if selected.scope_id != scope_id:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT, "snapshot belongs to another scope"
            )
        plan = self._requirement_planner.plan(original_request=original_request)
        identity = digest_of(
            {
                "idempotency_key": idempotency_key.value,
                "scope_id": scope_id.value,
                "snapshot_id": selected.snapshot_id.value,
                "original_request": original_request,
                "requirement_plan": plan,
                "classification": classification,
            }
        )
        requirement = KnowledgeRequirement.create(
            requirement_id=StableId(f"requirement_{identity.value[-32:]}"),
            revision=Revision(1),
            fidelity=RequirementFidelity.ORIGINAL,
            original_request=original_request,
            needs=plan.needs,
            joint_constraints=plan.joint_constraints,
        )
        boundary = TaskBoundary.create(
            task_id=StableId(f"task_{identity.value[-32:]}"),
            task_revision=Revision(1),
            scope_id=scope_id,
            purpose="natural-language knowledge task",
            classification=classification,
        )
        session = self.knowledge_use.open_session(
            idempotency_key=IdempotencyKey(f"{idempotency_key.value}:session"),
            boundary=boundary,
            requirement=requirement,
            snapshot_id=selected.snapshot_id,
        )
        assessment = self.knowledge_use.assess(
            idempotency_key=IdempotencyKey(f"{idempotency_key.value}:assessment"),
            requirement=requirement,
            session=session,
        )
        self.telemetry.record(
            owner="application-services",
            operation="task-query@1",
            outcome="SUFFICIENT" if assessment.sufficient else "INSUFFICIENT",
            correlation_reference=f"task-query:{idempotency_key.value}",
            causation_reference=idempotency_key.value,
            authority_references=(
                requirement.requirement_id.value,
                requirement.digest.value,
                assessment.assessment_id.value,
                assessment.digest.value,
            ),
            metrics=(TelemetryMetric("needs", len(assessment.items), "needs"),),
            classification=classification,
        )
        return assessment


def _allowed_paths(binding: DataSourceBinding) -> tuple[str, ...]:
    value = dict(binding.selector).get("paths")
    if not value:
        raise DomainError(ErrorCode.SELECTOR_INVALID, "binding has no path selector")
    return tuple(item for item in value.split(",") if item)


def _required(parameters: Mapping[str, str], key: str) -> str:
    value = parameters.get(key)
    if not value:
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"target parameter {key} is required")
    return value
    EvidenceAnswerRequest,
    EvidenceAnswerService,
