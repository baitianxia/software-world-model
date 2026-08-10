"""Composition root shared by CLI and HTTP interfaces."""

from __future__ import annotations

from dataclasses import dataclass
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
from software_world_model.application_services.maven_structure_update import (
    MavenStructureIndependentVerifier,
    MavenStructureTargetAuthority,
    MavenStructureUpdateAttempt,
    MavenStructureUpdateRequest,
    MavenStructureUpdateResult,
    MavenStructureUpdateService,
)
from software_world_model.application_services.structure_read_session import (
    StructureReadSession,
    StructureReadSessionService,
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
    SqliteArtifactUseAuthorityRepository,
    SqliteFormalKnowledgeRepository,
    SqliteKnowledgeScopeRepository,
    SqliteKnowledgeUpdateRepository,
    SqliteKnowledgeUseRepository,
    SqliteManagementRepository,
    SqliteSourceConfigurationRepository,
    SqliteSourceOperationRepository,
    SqliteTelemetryRepository,
)
from software_world_model.infrastructure.sqlite_structure_knowledge_repository import (
    SqliteStructureKnowledgeRepository,
)
from software_world_model.infrastructure.sqlite_maven_structure_update_repository import (
    SqliteMavenStructureUpdateRepository,
)
from software_world_model.infrastructure.sqlite_structure_read_session_repository import (
    SqliteStructureReadSessionRepository,
)
from software_world_model.knowledge_engine import (
    FormalKnowledgeService,
    KnowledgeScopeService,
    ScopeLifecycle,
    ScopeType,
    StructureContextComparisonService,
)
from software_world_model.knowledge_engine.structure_publication import (
    StructurePublicationService,
    StructureSnapshot,
)
from software_world_model.knowledge_engine.structure_authority import (
    StructureAdmissionDecision,
    StructureAdmissionService,
    StructureSchemaAdoption,
    StructureSchemaAvailability,
    StructureSchemaDefinition,
    StructureSchemaRegistration,
    StructureSchemaRegistryService,
    StructureVerifierAssessmentService,
)
from software_world_model.source_integration import (
    ArtifactUseAuthorityService,
    LocalGitConfigurationProvider,
    LocalGitConnector,
    ProviderRegistry,
    SourceConfigurationService,
    SourceOperationService,
    SourceTargetResolutionReceipt,
    TargetKind,
    resolve_local_git_binding_target,
)


@dataclass(frozen=True, slots=True)
class MavenStructureInterfaceResult:
    """Application result plus the exact authorities needed for CLI audit."""

    update: MavenStructureUpdateResult
    objective: BuildObjective
    target: CanonicalBuildTarget
    requirement_binding: None
    attempt: MavenStructureUpdateAttempt
    target_authority: MavenStructureTargetAuthority
    admission: StructureAdmissionDecision
    schema_registration: StructureSchemaRegistration
    schema_availability: StructureSchemaAvailability
    schema_adoption: StructureSchemaAdoption


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
        self.artifact_use = ArtifactUseAuthorityService(
            SqliteArtifactUseAuthorityRepository(database),
            self.source_operations.current_authorized_replay_port(),
        )
        self.structure_repository = SqliteStructureKnowledgeRepository(database)
        self.structure_schema_registry = StructureSchemaRegistryService(
            self.structure_repository
        )
        (
            self.maven_structure_schema_registration,
            self.maven_structure_schema_availability,
        ) = self.structure_schema_registry.register(
            definition=StructureSchemaDefinition.maven_reactor_structure(),
            idempotency_key=IdempotencyKey(
                "iter-003:maven-reactor-structure-schema:register"
            ),
            proposal_ref="ITER-003-PROPOSAL",
            review_ref="ITER-003-READINESS",
            registered_by="application-runtime",
            reason="register the frozen ITER-003 Maven Structure schema",
        )
        self.maven_structure_verifier = MavenStructureIndependentVerifier(
            self.scopes,
            self.sources,
            self.artifact_use,
        )
        self.structure_verifier_authority = (
            self.structure_repository.register_structure_verifier_authority(
                verifier_ref=self.maven_structure_verifier.verifier_ref
            )
        )
        self.structure_verifier_assessments = StructureVerifierAssessmentService(
            self.structure_repository,
            self.maven_structure_verifier,
            verifier_authority=self.structure_verifier_authority,
        )
        self.structure_admission = StructureAdmissionService(
            self.structure_repository,
            self.scopes,
            self.artifact_use,
            verifier_authority=self.structure_verifier_authority,
        )
        self.structure_publication = StructurePublicationService(
            self.structure_repository,
            self.scopes,
            self.artifact_use,
            verifier_authority=self.structure_verifier_authority,
        )
        self.structure_context_comparisons = StructureContextComparisonService()
        self.structure_read_sessions = StructureReadSessionService(
            SqliteStructureReadSessionRepository(database),
            self.structure_repository,
            self.scopes,
            self.structure_context_comparisons,
        )
        self.maven_structure_update_repository = (
            SqliteMavenStructureUpdateRepository(
                database,
                self.structure_repository,
                self.artifact_use,
            )
        )
        self.maven_structure_updates = MavenStructureUpdateService(
            self.maven_structure_update_repository,
            self.scopes,
            self.sources,
            self.source_operations,
            self.artifact_use,
            self.structure_admission,
            self.structure_verifier_assessments,
            self.maven_structure_verifier,
            self.structure_publication,
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

    def build_maven_structure(
        self,
        *,
        idempotency_key: IdempotencyKey,
        scope_id: StableId,
        scope_revision: Revision,
        source_id: StableId,
        source_revision: Revision,
        binding_id: StableId,
        binding_revision: Revision,
        repository_revision: str,
        logical_reactor_root: str,
        objective_description: str,
        expected_current_snapshot_id: StableId | None,
        classification: str,
        actor_ref: str,
        correlation_ref: CorrelationRef,
        max_poms: int,
        max_calls: int,
        tree_page_size: int,
        max_bytes_per_call: int,
    ) -> MavenStructureInterfaceResult:
        """Build and atomically publish one exact Maven Structure Snapshot."""

        scope = self.scopes.get_scope(scope_id, scope_revision)
        canonical_system_key = dict(scope.metadata).get("canonical_system_key")
        if canonical_system_key is None or not canonical_system_key.strip():
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "Maven Structure Scope metadata must define canonical_system_key",
                {"reason_code": "CANONICAL_SYSTEM_KEY_METADATA_REQUIRED"},
            )
        receipt = self.resolve_target(
            source_id=source_id,
            source_revision=source_revision,
            binding_id=binding_id,
            binding_revision=binding_revision,
            target_kind=TargetKind.REPOSITORY_REVISION,
            parameters={"revision": repository_revision},
        )
        objective = BuildObjective.create(
            objective_id=f"maven-objective:{idempotency_key.value}",
            description=objective_description,
            unacceptable_outcomes=(
                "source boundary expansion",
                "incomplete Maven reactor Coverage reported as complete",
                "name, path, or GA heuristic stitching",
            ),
        )
        target = CanonicalBuildTarget.from_receipt(receipt)
        request = MavenStructureUpdateRequest(
            idempotency_key=idempotency_key,
            objective=objective,
            target=target,
            requirement_binding=None,
            scope_id=scope_id,
            scope_revision=scope_revision,
            source_id=source_id,
            source_revision=source_revision,
            binding_id=binding_id,
            binding_revision=binding_revision,
            repository_revision=repository_revision,
            logical_reactor_root=logical_reactor_root,
            canonical_system_key=canonical_system_key,
            expected_current_snapshot_id=expected_current_snapshot_id,
            max_poms=max_poms,
            max_calls=max_calls,
            tree_page_size=tree_page_size,
            max_bytes_per_call=max_bytes_per_call,
            classification=classification,
            actor_ref=actor_ref,
            correlation_ref=correlation_ref,
        )
        update = self.maven_structure_updates.execute(request)
        attempt = self.maven_structure_update_repository.get_attempt(
            update.authority_result.attempt_id
        )
        target_authority = self.maven_structure_update_repository.get_target_authority(
            scope_id=scope_id,
            binding_id=binding_id,
            logical_reactor_root=logical_reactor_root,
        )
        if target_authority is None:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "published Maven Structure update has no target authority",
            )
        admission = self.structure_admission.get(
            update.publication_receipt.admission_id
        )
        schema_adoption = self.structure_schema_registry.get_adoption(scope_id)
        if schema_adoption is None:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "published Maven Structure Snapshot has no Schema adoption",
            )
        return MavenStructureInterfaceResult(
            update=update,
            objective=objective,
            target=target,
            requirement_binding=None,
            attempt=attempt,
            target_authority=target_authority,
            admission=admission,
            schema_registration=self.maven_structure_schema_registration,
            schema_availability=self.maven_structure_schema_availability,
            schema_adoption=schema_adoption,
        )

    def read_structure_snapshot(self, snapshot_id: StableId) -> StructureSnapshot:
        """Read one immutable Structure Snapshot by its exact identity."""

        return self.structure_publication.get_snapshot(snapshot_id)

    def open_current_structure_read_session(
        self,
        *,
        scope_id: StableId,
        scope_revision: Revision,
        task_boundary: TaskBoundary,
        caller_ref: str,
        idempotency_key: IdempotencyKey,
    ) -> StructureReadSession:
        """Resolve CURRENT once and persist its exact Structure Snapshot binding."""

        return self.structure_read_sessions.open_current(
            scope_id=scope_id,
            scope_revision=scope_revision,
            task_boundary=task_boundary,
            caller_ref=caller_ref,
            idempotency_key=idempotency_key,
        )

    def open_ordered_structure_read_session(
        self,
        *,
        scope_id: StableId,
        scope_revision: Revision,
        task_boundary: TaskBoundary,
        caller_ref: str,
        snapshot_ids: tuple[StableId, ...],
        idempotency_key: IdempotencyKey,
    ) -> StructureReadSession:
        """Persist a caller-ordered exact comparable Structure Snapshot set."""

        return self.structure_read_sessions.open_ordered(
            scope_id=scope_id,
            scope_revision=scope_revision,
            task_boundary=task_boundary,
            caller_ref=caller_ref,
            snapshot_ids=snapshot_ids,
            idempotency_key=idempotency_key,
        )

    def read_structure_read_session(
        self, session_id: StableId
    ) -> StructureReadSession:
        """Re-read and revalidate one immutable Structure read Session."""

        return self.structure_read_sessions.get_session(session_id)

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
        canonical_system_key: str | None = None,
        actor: str,
        correlation_ref: CorrelationRef,
    ) -> ManagementExecution:
        """Configure one browser-visible project through the management owner path."""

        scope_metadata = {"display_name": display_name}
        if canonical_system_key is not None:
            scope_metadata["canonical_system_key"] = canonical_system_key
        command = ConfigureSystemSourceCommand.create(
            idempotency_key=idempotency_key,
            caller="browser-chat",
            purpose="configure a local project for browser chat",
            classification="INTERNAL",
            request_context={"interface": "browser-chat"},
            scope_type=ScopeType.SYSTEM,
            scope_metadata=scope_metadata,
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
        source, binding = self.sources.require_current_active_binding(
            source_id=source_id,
            expected_source_revision=source_revision,
            binding_id=binding_id,
            expected_binding_revision=binding_revision,
        )
        scope = self.scopes.get_scope(binding.scope_id)
        if (
            scope.lifecycle is not ScopeLifecycle.ACTIVE
            or scope.definition_revision != binding.observed_scope_revision
        ):
            raise DomainError(
                ErrorCode.CONTROL_STATE_DENIED,
                "binding Scope is not current and active for target resolution",
            )
        try:
            return resolve_local_git_binding_target(
                connector=LocalGitConnector(source.canonical_source_target),
                selector=binding.selector,
                target_kind=target_kind,
                parameters=parameters,
            )
        except DomainError as exc:
            if exc.code not in {
                ErrorCode.SOURCE_TARGET_AMBIGUOUS,
                ErrorCode.SOURCE_TARGET_NOT_FOUND,
                ErrorCode.SOURCE_TARGET_OUT_OF_SCOPE,
            }:
                raise
            # Interface callers historically consume non-exact target
            # proposals as invalid build input.  Preserve that boundary while
            # Source Integration retains its more precise diagnostic code.
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "source target did not resolve to one authorized exact identity",
                {
                    "reason_code": "SOURCE_TARGET_NOT_EXACT",
                    "cause_code": exc.code.value,
                },
            ) from exc

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


    EvidenceAnswerRequest,
    EvidenceAnswerService,
