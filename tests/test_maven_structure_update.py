from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from software_world_model.application_services.maven_structure import (
    MavenEvaluationInput,
    MavenStructureError,
    MavenStructureErrorCode,
    MavenStructureEvaluator,
)
from software_world_model.application_services.knowledge_update import (
    BuildObjective,
    CanonicalBuildTarget,
)
from software_world_model.application_services.maven_structure_update import (
    MavenStructureIndependentVerifier,
    MavenStructureUpdateRequest,
    MavenStructureUpdateService,
    MavenStructureUpdateState,
    parse_local_git_tree_jsonl,
)
from software_world_model.cross_cutting import (
    CorrelationRef,
    DomainError,
    ErrorCode,
    IdempotencyKey,
    Revision,
    canonical_json_bytes,
)
from software_world_model.infrastructure import (
    SqliteDatabase,
    SqliteArtifactUseAuthorityRepository,
    SqliteKnowledgeScopeRepository,
    SqliteSourceConfigurationRepository,
    SqliteSourceOperationRepository,
)
from software_world_model.infrastructure.sqlite_maven_structure_update_repository import (
    SqliteMavenStructureUpdateRepository,
)
from software_world_model.infrastructure.sqlite_structure_knowledge_repository import (
    SqliteStructureKnowledgeRepository,
)
from software_world_model.knowledge_engine import (
    KnowledgeScopeService,
    ScopePurpose,
    ScopeType,
)
from software_world_model.knowledge_engine.structure import (
    CompleteMemberManifest,
    CoverageMemberKind,
    CoverageRecord,
    CoverageState,
    RelationPredicate,
    StructureKnowledgeBatch,
)
from software_world_model.knowledge_engine.structure_publication import (
    StructurePublicationService,
)
from software_world_model.knowledge_engine.structure_authority import (
    StructureAdmissionOutcome,
    StructureAdmissionService,
    StructureSchemaDefinition,
    StructureSchemaRegistryService,
    StructureVerifierAssessmentOutcome,
    StructureVerifierAssessmentService,
)
from software_world_model.source_integration import (
    ArtifactUseAuthorityService,
    LocalGitConnector,
    LocalGitConfigurationProvider,
    LocalGitTargetResolver,
    ProviderRegistry,
    SourceConfigurationService,
    SourceOperationService,
    SourceTool,
)


class StepClock:
    def __init__(self) -> None:
        self.value = datetime(2026, 8, 10, tzinfo=timezone.utc)

    def __call__(self) -> datetime:
        current = self.value
        self.value += timedelta(microseconds=1)
        return current


class RecordingOperations:
    def __init__(self, delegate: SourceOperationService) -> None:
        self.delegate = delegate
        self.intents = []
        self.failure: DomainError | None = None

    def execute(self, intent):
        self.intents.append(intent)
        if self.failure is not None:
            raise self.failure
        return self.delegate.execute(intent)

    def current_authorized_replay_port(self):
        return self.delegate.current_authorized_replay_port()


class CapturingEvaluator:
    def __init__(self) -> None:
        self.delegate = MavenStructureEvaluator()
        self.inputs: list[MavenEvaluationInput] = []

    def evaluate(self, evaluation_input: MavenEvaluationInput):
        self.inputs.append(evaluation_input)
        return self.delegate.evaluate(evaluation_input)


class FailingAdmission:
    def __init__(self, delegate: StructureAdmissionService) -> None:
        self.delegate = delegate

    def __getattr__(self, name):
        return getattr(self.delegate, name)

    def accept(self, **_arguments):
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            "injected Admission rejection",
            {"reason_code": "INJECTED_ADMISSION_REJECTION"},
        )


class RejectingEvaluator:
    def evaluate(self, _evaluation_input):
        raise MavenStructureError(
            MavenStructureErrorCode.REACTOR_GA_AMBIGUOUS,
            "injected deterministic evaluator rejection",
            locator="pom.xml",
        )


class DroppingContainmentEvaluator:
    """Malicious generator that seals a mechanically self-consistent partial graph."""

    def __init__(self) -> None:
        self.delegate = MavenStructureEvaluator()

    def evaluate(self, evaluation_input: MavenEvaluationInput):
        evaluation = self.delegate.evaluate(evaluation_input)
        removed = next(
            relation
            for relation in evaluation.relations
            if relation.root.predicate is RelationPredicate.CONTAINS_MODULE
        )
        relations = tuple(
            relation for relation in evaluation.relations if relation != removed
        )
        manifest = CompleteMemberManifest.create(
            tuple(
                record.coverage_member
                for record in (*evaluation.entities, *relations)
            )
        )
        coverage = CoverageRecord(
            evaluation.coverage.root,
            CoverageState.create(
                root=evaluation.coverage.root,
                source_revision=evaluation.coverage.state.source_revision,
                knowledge_context_digest=(
                    evaluation.coverage.state.knowledge_context_digest
                ),
                complete_member_manifest=manifest,
                evidence_references=(
                    evaluation.coverage.state.evidence_references
                ),
            ),
        )
        lines = tuple(
            line
            for line in evaluation.report.lines
            if removed.root_id.value not in line and not line.startswith("COVERAGE ")
        ) + (
            (
                f"COVERAGE root={coverage.root_id.value} "
                f"state={coverage.state_id.value} "
                f"state_digest={coverage.state.state_digest.value} "
                f"status=COMPLETE members={len(manifest.members)} "
                "mode=REPLACE_COVERAGE"
            ),
        )
        report = replace(evaluation.report, lines=lines, complete=True)
        batch = StructureKnowledgeBatch.admit(
            evidence=evaluation.evidence,
            entities=evaluation.entities,
            relation_facts=relations,
            coverage=coverage,
            publication_mode=evaluation.batch.publication_mode,
            literal_facts=evaluation.batch.literal_facts,
            exact_upstream_entities=evaluation.batch.exact_upstream_entities,
        )
        return replace(
            evaluation,
            relations=relations,
            coverage=coverage,
            complete_member_manifest=manifest,
            report=report,
            batch=batch,
        )


class MutatingPersistedOperationEvaluator:
    """Mutate Source persistence after generation but before verifier replay."""

    def __init__(self, database: SqliteDatabase, mutation: str) -> None:
        self.database = database
        self.mutation = mutation
        self.delegate = MavenStructureEvaluator()
        self.operation_count_before: int | None = None
        self.dispatch_count_before: int | None = None
        self.operation_id: str | None = None

    def evaluate(self, evaluation_input: MavenEvaluationInput):
        evaluation = self.delegate.evaluate(evaluation_input)
        with self.database.read() as connection:
            self.operation_count_before = connection.execute(
                "SELECT COUNT(*) FROM src_operation_roots"
            ).fetchone()[0]
            self.dispatch_count_before = connection.execute(
                """SELECT COUNT(*) FROM src_operation_revisions
                   WHERE status = 'DISPATCHED'"""
            ).fetchone()[0]
            row = connection.execute(
                """SELECT operation_id FROM src_operation_roots
                   ORDER BY created_at, operation_id LIMIT 1"""
            ).fetchone()
            self.operation_id = row["operation_id"]
            if self.mutation == "DELETE":
                connection.execute("PRAGMA foreign_keys = OFF")
                try:
                    connection.execute(
                        "DELETE FROM src_operation_roots WHERE operation_id = ?",
                        (self.operation_id,),
                    )
                finally:
                    connection.execute("PRAGMA foreign_keys = ON")
            elif self.mutation == "NON_TERMINAL":
                connection.execute(
                    """UPDATE src_operation_roots SET current_status = 'DISPATCHED'
                       WHERE operation_id = ?""",
                    (self.operation_id,),
                )
            else:  # pragma: no cover - test fixture construction is closed
                raise AssertionError(f"unknown mutation {self.mutation}")
        return evaluation


class UnknownPublication:
    def __init__(self, delegate: StructurePublicationService) -> None:
        self.delegate = delegate

    def get_snapshot(self, snapshot_id):
        return self.delegate.get_snapshot(snapshot_id)

    def get_publication_by_idempotency_key(self, _idempotency_key):
        raise RuntimeError("publication outcome lookup is unavailable")

    def publish(self, **_arguments):
        raise RuntimeError("injected unknown publication outcome")


class AfterCommitResultFailureRepository:
    """Raise once after the Application PUBLISHED Result is already durable."""

    def __init__(self, delegate) -> None:
        self.delegate = delegate
        self.raised = False

    def __getattr__(self, name):
        return getattr(self.delegate, name)

    def finish_published(self, **arguments):
        result = self.delegate.finish_published(**arguments)
        if not self.raised:
            self.raised = True
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "injected failure after Application Result commit",
                {"reason_code": "POST_PUBLICATION_APP_FAILURE"},
            )
        return result


class BeforeCommitResultFailureRepository:
    """Fail Application Result sealing while Knowledge is already committed."""

    def __init__(self, delegate, *, failures: int) -> None:
        self.delegate = delegate
        self.remaining_failures = failures

    def __getattr__(self, name):
        return getattr(self.delegate, name)

    def finish_published(self, **arguments):
        if self.remaining_failures:
            self.remaining_failures -= 1
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "injected failure before Application Result commit",
                {"reason_code": "PRE_RESULT_COMMIT_FAILURE"},
            )
        return self.delegate.finish_published(**arguments)


class MavenStructureUpdateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.repository_path = Path(self.temporary.name) / "repository"
        self.repository_path.mkdir()
        self._git("init", "-q")
        self._git("config", "user.email", "test@example.com")
        self._git("config", "user.name", "Test")
        (self.repository_path / "alpha").mkdir()
        (self.repository_path / "README.md").write_text("fixture\n", encoding="utf-8")
        (self.repository_path / "linked-pom.xml").symlink_to("pom.xml")
        self._write_root(("alpha",))
        self._write_module("alpha")
        self._git("add", ".")
        self._git("commit", "-q", "-m", "revision a")
        self.revision_a = self._git("rev-parse", "HEAD").strip()

        (self.repository_path / "beta").mkdir()
        self._write_root(("alpha", "beta"))
        self._write_module("beta")
        self._git("add", ".")
        self._git("commit", "-q", "-m", "revision b")
        self.revision_b = self._git("rev-parse", "HEAD").strip()

        self.database = SqliteDatabase()
        self.clock = StepClock()
        self.scopes = KnowledgeScopeService(
            SqliteKnowledgeScopeRepository(self.database), clock=self.clock
        )
        self.configurations = SourceConfigurationService(
            SqliteSourceConfigurationRepository(self.database),
            ProviderRegistry((LocalGitConfigurationProvider(),)),
            self.scopes,
            clock=self.clock,
        )
        self.scope = self.scopes.create_scope(
            scope_type=ScopeType.SYSTEM,
            metadata={
                "display_name": "Maven fixture",
                "canonical_system_key": "fixture-system",
            },
            idempotency_key=IdempotencyKey("maven-update-scope"),
            actor="test",
            reason="Maven Structure update",
            correlation_ref=CorrelationRef("maven-update"),
        )
        self.source = self.configurations.register_data_source(
            provider_type="LOCAL_GIT",
            provider_contract_version="0.1.0",
            identity_domain="LOCAL",
            source_target=str(self.repository_path),
            provider_configuration={"read_mode": "read_only"},
            secret_reference=None,
            idempotency_key=IdempotencyKey("maven-update-source"),
            actor="test",
            reason="Maven Structure update",
            correlation_ref=CorrelationRef("maven-update"),
        )
        bind_assertion = self.scopes.read_scope_state_assertion(
            scope_id=self.scope.scope_id,
            expected_revision=Revision(1),
            purpose=ScopePurpose.BIND_CONFIGURATION,
            caller_ref="test",
            request_ref="maven-update-bind",
            classification="INTERNAL",
        )
        self.binding = self.configurations.bind_source_to_scope(
            source_id=self.source.source_id,
            assertion=bind_assertion,
            selector={"paths": "."},
            context_constraint={"revision_policy": "exact"},
            context_hint="Maven fixture",
            idempotency_key=IdempotencyKey("maven-update-binding"),
            actor="test",
            reason="Maven Structure update",
            correlation_ref=CorrelationRef("maven-update"),
        )
        raw_operations = SourceOperationService(
            SqliteSourceOperationRepository(self.database),
            self.configurations,
            clock=self.clock,
        )
        self.operations = RecordingOperations(raw_operations)
        self.artifact_use = ArtifactUseAuthorityService(
            SqliteArtifactUseAuthorityRepository(self.database),
            self.operations.current_authorized_replay_port(),
            clock=self.clock,
        )
        self.evaluator = CapturingEvaluator()
        self.structure_repository = SqliteStructureKnowledgeRepository(self.database)
        StructureSchemaRegistryService(
            self.structure_repository, clock=self.clock
        ).register(
            definition=StructureSchemaDefinition.maven_reactor_structure(),
            idempotency_key=IdempotencyKey("maven-structure-schema"),
            proposal_ref="ITER-003-PROPOSAL",
            review_ref="ITER-003-READINESS",
            registered_by="test",
            reason="Maven Structure update tests",
        )
        self.verifier_authority = (
            self.structure_repository.register_structure_verifier_authority(
                verifier_ref=MavenStructureIndependentVerifier.verifier_ref
            )
        )
        self.admission = StructureAdmissionService(
            self.structure_repository,
            self.scopes,
            self.artifact_use,
            verifier_authority=self.verifier_authority,
            clock=self.clock,
        )
        self.verifier = MavenStructureIndependentVerifier(
            self.scopes,
            self.configurations,
            self.artifact_use,
        )
        self.verifier_assessments = StructureVerifierAssessmentService(
            self.structure_repository,
            self.verifier,
            verifier_authority=self.verifier_authority,
            clock=self.clock,
        )
        self.publication = StructurePublicationService(
            self.structure_repository,
            self.scopes,
            self.artifact_use,
            verifier_authority=self.verifier_authority,
            clock=self.clock,
        )
        self.update_repository = SqliteMavenStructureUpdateRepository(
            self.database,
            self.structure_repository,
            self.artifact_use,
        )
        self.service = MavenStructureUpdateService(
            self.update_repository,
            self.scopes,
            self.configurations,
            self.operations,
            self.artifact_use,
            self.admission,
            self.verifier_assessments,
            self.verifier,
            self.publication,
            evaluator=self.evaluator,
            clock=self.clock,
        )
        self.resolver = LocalGitTargetResolver(
            LocalGitConnector(str(self.repository_path))
        )

    def tearDown(self) -> None:
        self.database.close()
        self.temporary.cleanup()

    def _git(self, *arguments: str) -> str:
        result = subprocess.run(
            ("git", "-C", str(self.repository_path), *arguments),
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return result.stdout

    def _write_root(self, modules: tuple[str, ...]) -> None:
        rendered_modules = "".join(f"<module>{item}</module>" for item in modules)
        (self.repository_path / "pom.xml").write_text(
            f"""<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>org.example</groupId>
  <artifactId>reactor</artifactId>
  <version>1.0.0</version>
  <packaging>pom</packaging>
  <modules>{rendered_modules}</modules>
</project>
""",
            encoding="utf-8",
        )

    def _write_module(self, name: str) -> None:
        (self.repository_path / name / "pom.xml").write_text(
            f"""<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>org.example</groupId>
  <artifactId>{name}</artifactId>
  <version>1.0.0</version>
</project>
""",
            encoding="utf-8",
        )

    def request(
        self,
        revision: str,
        *,
        key: str,
        expected_current=None,
        max_poms: int = 10,
        max_calls: int = 20,
        tree_page_size: int = 2,
        max_bytes_per_call: int = 8192,
    ) -> MavenStructureUpdateRequest:
        return MavenStructureUpdateRequest(
            idempotency_key=IdempotencyKey(key),
            objective=BuildObjective.create(
                objective_id=f"manual-maven:{key}",
                description="Build exact Maven Structure knowledge",
                unacceptable_outcomes=(
                    "target substitution",
                    "partial publication",
                ),
            ),
            target=CanonicalBuildTarget.from_receipt(
                self.resolver.resolve_revision(revision)
            ),
            requirement_binding=None,
            scope_id=self.scope.scope_id,
            scope_revision=Revision(1),
            source_id=self.source.source_id,
            source_revision=Revision(1),
            binding_id=self.binding.binding_id,
            binding_revision=Revision(1),
            repository_revision=revision,
            logical_reactor_root="pom.xml",
            canonical_system_key="fixture-system",
            expected_current_snapshot_id=expected_current,
            max_poms=max_poms,
            max_calls=max_calls,
            tree_page_size=tree_page_size,
            max_bytes_per_call=max_bytes_per_call,
            classification="INTERNAL",
            actor_ref="test/maven-structure-update",
            correlation_ref=CorrelationRef("maven-update"),
        )

    def test_manual_zero_question_build_paginates_tree_reads_all_poms_and_passes_symlink_metadata(self) -> None:
        result = self.service.execute(
            self.request(self.revision_a, key="update-a1", tree_page_size=2)
        )

        tools = tuple(intent.tool for intent in self.operations.intents)
        self.assertGreater(tools.count(SourceTool.TREE), 1)
        self.assertEqual(tools.count(SourceTool.READ), 2)
        with self.database.read() as connection:
            persisted_operation_count = connection.execute(
                "SELECT COUNT(*) FROM src_operation_roots"
            ).fetchone()[0]
            dispatched_revision_count = connection.execute(
                """SELECT COUNT(*) FROM src_operation_revisions
                   WHERE status = 'DISPATCHED'"""
            ).fetchone()[0]
        self.assertEqual(persisted_operation_count, len(tools))
        self.assertEqual(dispatched_revision_count, len(tools))
        self.assertEqual(
            result.verifier_assessment.outcome,
            StructureVerifierAssessmentOutcome.PASS,
        )
        self.assertEqual(
            result.verifier_assessment.verifier_ref,
            "MAVEN_STRUCTURE_INDEPENDENT_VERIFIER@1",
        )
        evaluation_input = self.evaluator.inputs[-1]
        self.assertEqual(set(evaluation_input.pom_bytes), {"pom.xml", "alpha/pom.xml"})
        self.assertEqual(evaluation_input.git_entries["linked-pom.xml"].mode, "120000")
        self.assertTrue(evaluation_input.git_entries["linked-pom.xml"].is_symlink)
        self.assertGreater(len(evaluation_input.tree_evidence), 1)
        tree_refs = {item.evidence_id for item in evaluation_input.tree_evidence}
        self.assertTrue(
            tree_refs
            <= set(result.evaluation.batch.coverage.state.evidence_references)
        )
        self.assertEqual(
            result.application_acceptance.report_digest,
            result.build_report_digest,
        )
        self.assertEqual(
            result.authority_result.artifact_use_confirmation_id,
            result.artifact_use_confirmation.confirmation_id,
        )
        self.assertEqual(
            result.authority_result.artifact_use_confirmation_digest,
            result.artifact_use_confirmation.digest,
        )
        self.assertEqual(
            result.artifact_use_confirmation.downstream_candidate_digest,
            result.verifier_assessment.candidate_digest,
        )
        admission = self.admission.get_admission(
            result.publication_receipt.admission_id
        )
        self.assertEqual(
            result.verifier_assessment.artifact_use_confirmation_id,
            result.artifact_use_confirmation.confirmation_id,
        )
        self.assertEqual(
            result.verifier_assessment.artifact_use_confirmation_digest,
            result.artifact_use_confirmation.digest,
        )
        self.assertEqual(
            admission.artifact_use_confirmation_id,
            result.artifact_use_confirmation.confirmation_id,
        )
        self.assertEqual(
            admission.artifact_use_confirmation_digest,
            result.artifact_use_confirmation.digest,
        )
        self.assertEqual(
            self.artifact_use.get_confirmation(
                result.artifact_use_confirmation.confirmation_id
            ),
            result.artifact_use_confirmation,
        )
        self.assertEqual(
            self.publication.current_snapshot(self.scope.scope_id).snapshot_id,
            result.publication_receipt.snapshot.snapshot_id,
        )
        self.assertIsNone(result.previous_snapshot)
        self.assertFalse(hasattr(self.request(self.revision_a, key="unused"), "question"))

    def test_same_top_level_request_replays_source_and_publication(self) -> None:
        request = self.request(self.revision_a, key="replay-a")
        first = self.service.execute(request)
        second = self.service.execute(request)

        self.assertEqual(first.source_operation_ids, second.source_operation_ids)
        self.assertEqual(
            first.publication_receipt.publication_id,
            second.publication_receipt.publication_id,
        )
        self.assertEqual(first.digest, second.digest)
        self.assertEqual(
            first.artifact_use_confirmation.confirmation_id,
            second.artifact_use_confirmation.confirmation_id,
        )

        with self.assertRaises(DomainError) as changed_budget:
            self.service.execute(replace(request, max_poms=request.max_poms + 1))
        self.assertEqual(
            changed_budget.exception.code,
            ErrorCode.IDEMPOTENCY_MISMATCH,
        )

    def test_artifact_package_cannot_reopen_after_binding_is_suspended(self) -> None:
        result = self.service.execute(
            self.request(self.revision_a, key="artifact-reopen-suspend")
        )
        confirmation = result.artifact_use_confirmation
        self.binding = self.configurations.suspend_binding(
            binding_id=self.binding.binding_id,
            expected_revision=self.binding.definition_revision,
            idempotency_key=IdempotencyKey("suspend-after-artifact-package"),
            actor="test",
            reason="prove Artifact Package does not preserve stale permission",
            correlation_ref=CorrelationRef("maven-update"),
        )
        assertion = self.scopes.read_scope_state_assertion(
            scope_id=self.scope.scope_id,
            expected_revision=self.scope.definition_revision,
            purpose=ScopePurpose.SOURCE_EXECUTION,
            caller_ref="test",
            request_ref="artifact-reopen-after-suspend",
            classification="INTERNAL",
        )

        with self.assertRaises(DomainError) as denied:
            self.artifact_use.reopen_authorized_read(
                package_id=confirmation.package_id,
                expected_package_digest=confirmation.package_digest,
                closure_id=confirmation.closure_id,
                expected_closure_digest=confirmation.closure_digest,
                protection_id=confirmation.protection_id,
                expected_protection_digest=confirmation.protection_digest,
                purpose=confirmation.purpose,
                downstream_request_ref=confirmation.downstream_request_ref,
                downstream_request_digest=confirmation.downstream_request_digest,
                scope_assertion=assertion,
            )

        self.assertIn(
            denied.exception.code,
            {ErrorCode.REVISION_CONFLICT, ErrorCode.CONTROL_STATE_DENIED},
        )

    def test_same_key_with_changed_correlation_fails_closed(self) -> None:
        request = self.request(self.revision_a, key="changed-correlation")
        self.service.execute(request)

        with self.assertRaises(DomainError) as mismatch:
            self.service.execute(
                replace(
                    request,
                    correlation_ref=CorrelationRef("maven-update-other"),
                )
            )

        self.assertEqual(mismatch.exception.code, ErrorCode.IDEMPOTENCY_MISMATCH)

    def test_a_to_b_to_a_reuses_exact_source_evidence_and_state_ids(self) -> None:
        a1 = self.service.execute(self.request(self.revision_a, key="update-a1"))
        b_request = self.request(
            self.revision_b,
            key="update-b",
            expected_current=a1.publication_receipt.snapshot.snapshot_id,
        )
        b = self.service.execute(b_request)
        self.assertEqual(
            b.previous_snapshot.snapshot_id,
            a1.publication_receipt.snapshot.snapshot_id,
        )
        a2 = self.service.execute(
            self.request(
                self.revision_a,
                key="update-a2",
                expected_current=b.publication_receipt.snapshot.snapshot_id,
            )
        )

        self.assertEqual(a1.source_operation_ids, a2.source_operation_ids)
        self.assertEqual(
            tuple((item.root_id, item.state_id) for item in a1.publication_receipt.snapshot.members),
            tuple((item.root_id, item.state_id) for item in a2.publication_receipt.snapshot.members),
        )
        self.assertNotEqual(
            a1.publication_receipt.snapshot.snapshot_id,
            a2.publication_receipt.snapshot.snapshot_id,
        )
        b_entity_roots = {
            item.root_id
            for item in b.publication_receipt.snapshot.members
            if item.kind is CoverageMemberKind.ENTITY
        }
        a2_entity_roots = {
            item.root_id
            for item in a2.publication_receipt.snapshot.members
            if item.kind is CoverageMemberKind.ENTITY
        }
        self.assertTrue(b_entity_roots - a2_entity_roots)
        removed_roots = {item.root_id for item in a2.deletions.removed_members}
        self.assertTrue((b_entity_roots - a2_entity_roots) <= removed_roots)
        self.assertTrue(a2.deletions.deleted_entity_state_ids)

        # Replaying B after CURRENT has moved back to A still derives deletions
        # from B's immutable receipt.previous_snapshot_id, never live CURRENT.
        b_replay = self.service.execute(b_request)
        self.assertEqual(
            b.publication_receipt.publication_id,
            b_replay.publication_receipt.publication_id,
        )
        self.assertEqual(b.deletions.digest, b_replay.deletions.digest)
        self.assertEqual(
            b.deletions.deleted_members,
            b_replay.deletions.deleted_members,
        )

    def test_source_failure_and_truncated_pom_never_publish(self) -> None:
        source_request = self.request(self.revision_a, key="source-failure")
        self.operations.failure = DomainError(
            ErrorCode.SOURCE_OPERATION_FAILED,
            "injected Source failure",
            {"reason_code": "INJECTED_SOURCE_FAILURE"},
        )
        with self.assertRaises(DomainError) as source_failure:
            self.service.execute(source_request)
        self.assertEqual(source_failure.exception.code, ErrorCode.SOURCE_OPERATION_FAILED)
        self.assertIsNone(self.publication.current_snapshot(self.scope.scope_id))
        self.assertEqual(
            self.service.get_result(idempotency_key=source_request.idempotency_key).state,
            MavenStructureUpdateState.FAILED,
        )
        operation_count = len(self.operations.intents)
        with self.assertRaises(DomainError):
            self.service.execute(source_request)
        self.assertEqual(len(self.operations.intents), operation_count)
        self.operations.failure = None

        with self.assertRaises(DomainError) as truncated:
            self.service.execute(
                self.request(
                    self.revision_a,
                    key="truncated-pom",
                    tree_page_size=1,
                    max_bytes_per_call=256,
                )
            )
        self.assertEqual(truncated.exception.code, ErrorCode.SOURCE_OPERATION_FAILED)
        self.assertEqual(truncated.exception.details["reason_code"], "POM_READ_TRUNCATED")
        self.assertIsNone(self.publication.current_snapshot(self.scope.scope_id))

    def test_admission_failure_and_unknown_publication_are_durable(self) -> None:
        rejected_service = MavenStructureUpdateService(
            self.update_repository,
            self.scopes,
            self.configurations,
            self.operations,
            self.artifact_use,
            FailingAdmission(self.admission),
            self.verifier_assessments,
            self.verifier,
            self.publication,
            evaluator=self.evaluator,
            clock=self.clock,
        )
        rejected_request = self.request(self.revision_a, key="admission-rejected")
        with self.assertRaises(DomainError):
            rejected_service.execute(rejected_request)
        rejected = rejected_service.get_result(
            idempotency_key=rejected_request.idempotency_key
        )
        self.assertEqual(rejected.state, MavenStructureUpdateState.FAILED)
        self.assertIsNotNone(rejected.source_collection_digest)
        self.assertIsNotNone(rejected.build_report_digest)
        self.assertIsNotNone(rejected.application_acceptance_digest)
        self.assertIsNone(rejected.admission_id)
        self.assertIsNotNone(rejected.artifact_use_confirmation_id)
        self.assertIsNotNone(rejected.artifact_use_confirmation_digest)
        self.assertIsNone(rejected.publication_id)

        pending_service = MavenStructureUpdateService(
            self.update_repository,
            self.scopes,
            self.configurations,
            self.operations,
            self.artifact_use,
            self.admission,
            self.verifier_assessments,
            self.verifier,
            UnknownPublication(self.publication),
            evaluator=self.evaluator,
            clock=self.clock,
        )
        pending_request = self.request(self.revision_a, key="publication-unknown")
        with self.assertRaises(RuntimeError):
            pending_service.execute(pending_request)
        pending = pending_service.get_result(
            idempotency_key=pending_request.idempotency_key
        )
        self.assertEqual(pending.state, MavenStructureUpdateState.OUTCOME_PENDING)
        self.assertIsNotNone(pending.admission_id)
        self.assertIsNotNone(pending.admission_digest)
        self.assertIsNone(pending.publication_id)
        self.assertEqual(
            dict(pending.failure_details)["stage"],
            "PUBLICATION_DISPATCHED",
        )
        operation_count = len(self.operations.intents)
        with self.assertRaises(DomainError) as unresolved:
            pending_service.execute(pending_request)
        self.assertEqual(
            unresolved.exception.code,
            ErrorCode.EVALUATION_OUTCOME_PENDING,
        )
        self.assertEqual(len(self.operations.intents), operation_count)

    def test_after_commit_application_failure_recovers_published_result(self) -> None:
        recovering_repository = AfterCommitResultFailureRepository(
            self.update_repository
        )
        service = MavenStructureUpdateService(
            recovering_repository,
            self.scopes,
            self.configurations,
            self.operations,
            self.artifact_use,
            self.admission,
            self.verifier_assessments,
            self.verifier,
            self.publication,
            evaluator=self.evaluator,
            clock=self.clock,
        )
        request = self.request(self.revision_a, key="after-app-result-commit")

        result = service.execute(request)

        self.assertTrue(recovering_repository.raised)
        self.assertEqual(
            result.authority_result.state,
            MavenStructureUpdateState.PUBLISHED,
        )
        self.assertEqual(
            self.publication.current_snapshot(self.scope.scope_id).snapshot_id,
            result.publication_receipt.snapshot.snapshot_id,
        )
        durable = self.update_repository.get_result(
            idempotency_key=request.idempotency_key
        )
        self.assertEqual(durable.state, MavenStructureUpdateState.PUBLISHED)
        self.assertEqual(
            durable.publication_id,
            result.publication_receipt.publication_id,
        )

    def test_outcome_pending_retry_reconciles_without_source_redispatch(self) -> None:
        recovering_repository = BeforeCommitResultFailureRepository(
            self.update_repository,
            failures=2,
        )
        service = MavenStructureUpdateService(
            recovering_repository,
            self.scopes,
            self.configurations,
            self.operations,
            self.artifact_use,
            self.admission,
            self.verifier_assessments,
            self.verifier,
            self.publication,
            evaluator=self.evaluator,
            clock=self.clock,
        )
        request = self.request(self.revision_a, key="pending-recovery")

        with self.assertRaises(DomainError):
            service.execute(request)
        pending = self.update_repository.get_result(
            idempotency_key=request.idempotency_key
        )
        self.assertEqual(pending.state, MavenStructureUpdateState.OUTCOME_PENDING)
        self.assertIsNotNone(pending.admission_id)
        committed = self.publication.current_snapshot(self.scope.scope_id)
        self.assertIsNotNone(committed)
        operation_count = len(self.operations.intents)

        recovered = service.execute(request)

        self.assertEqual(
            recovered.authority_result.state,
            MavenStructureUpdateState.PUBLISHED,
        )
        self.assertEqual(recovered.authority_result.result_id, pending.result_id)
        self.assertEqual(
            recovered.publication_receipt.snapshot.snapshot_id,
            committed.snapshot_id,
        )
        self.assertEqual(
            len(self.operations.intents),
            operation_count,
            "recovery must replay exact persisted Source Operations without dispatch",
        )

    def test_malicious_generator_dropping_contains_is_persistently_rejected(self) -> None:
        service = MavenStructureUpdateService(
            self.update_repository,
            self.scopes,
            self.configurations,
            self.operations,
            self.artifact_use,
            self.admission,
            self.verifier_assessments,
            self.verifier,
            self.publication,
            evaluator=DroppingContainmentEvaluator(),
            clock=self.clock,
        )
        request = self.request(self.revision_a, key="malicious-missing-containment")

        with self.assertRaises(DomainError) as rejected:
            service.execute(request)

        self.assertEqual(
            rejected.exception.details["reason_code"],
            "INDEPENDENT_VERIFIER_REJECTED",
        )
        result = service.get_result(idempotency_key=request.idempotency_key)
        self.assertEqual(result.state, MavenStructureUpdateState.FAILED)
        self.assertIsNotNone(result.admission_id)
        admission = self.admission.get(result.admission_id)
        assessment = self.admission.get_assessment(
            admission.verifier_assessment_id
        )
        self.assertEqual(admission.outcome, StructureAdmissionOutcome.REJECT)
        self.assertEqual(
            assessment.outcome, StructureVerifierAssessmentOutcome.FAIL
        )
        self.assertEqual(admission.verifier_assessment_digest, assessment.digest)
        self.assertEqual(
            admission.verifier_ref,
            "MAVEN_STRUCTURE_INDEPENDENT_VERIFIER@1",
        )
        finding_codes = {item.code for item in assessment.findings}
        self.assertIn("EVALUATION_DIGEST_MISMATCH", finding_codes)
        self.assertIn("CLOSURE_DIGEST_MISMATCH", finding_codes)
        self.assertIsNone(self.publication.current_snapshot(self.scope.scope_id))

        tools = tuple(intent.tool for intent in self.operations.intents)
        with self.database.read() as connection:
            self.assertEqual(
                connection.execute(
                    "SELECT COUNT(*) FROM src_operation_roots"
                ).fetchone()[0],
                len(tools),
            )
            self.assertEqual(
                connection.execute(
                    """SELECT COUNT(*) FROM src_operation_revisions
                       WHERE status = 'DISPATCHED'"""
                ).fetchone()[0],
                len(tools),
            )
            self.assertEqual(
                connection.execute(
                    """SELECT COUNT(*) FROM knw_structure_verifier_assessments
                       WHERE outcome = 'FAIL'"""
                ).fetchone()[0],
                1,
            )

    def test_verifier_replay_missing_operation_never_redispatches(self) -> None:
        self._assert_verifier_replay_fault(
            mutation="DELETE",
            expected_reason="SOURCE_OPERATION_AUTHORITY_MISSING",
            key="verifier-replay-missing",
        )

    def test_verifier_replay_non_terminal_operation_never_redispatches(self) -> None:
        self._assert_verifier_replay_fault(
            mutation="NON_TERMINAL",
            expected_reason="SOURCE_OPERATION_REPLAY_NOT_TERMINAL",
            key="verifier-replay-non-terminal",
        )

    def _assert_verifier_replay_fault(
        self,
        *,
        mutation: str,
        expected_reason: str,
        key: str,
    ) -> None:
        evaluator = MutatingPersistedOperationEvaluator(self.database, mutation)
        service = MavenStructureUpdateService(
            self.update_repository,
            self.scopes,
            self.configurations,
            self.operations,
            self.artifact_use,
            self.admission,
            self.verifier_assessments,
            self.verifier,
            self.publication,
            evaluator=evaluator,
            clock=self.clock,
        )
        request = self.request(self.revision_a, key=key)

        with self.assertRaises(DomainError) as failed:
            service.execute(request)

        self.assertEqual(failed.exception.details["reason_code"], expected_reason)
        result = service.get_result(idempotency_key=request.idempotency_key)
        self.assertEqual(result.state, MavenStructureUpdateState.FAILED)
        self.assertIsNone(result.admission_id)
        self.assertIsNone(self.publication.current_snapshot(self.scope.scope_id))
        self.assertIsNotNone(evaluator.operation_count_before)
        self.assertIsNotNone(evaluator.dispatch_count_before)
        self.assertEqual(
            len(self.operations.intents), evaluator.operation_count_before
        )
        with self.database.read() as connection:
            operation_count_after = connection.execute(
                "SELECT COUNT(*) FROM src_operation_roots"
            ).fetchone()[0]
            dispatch_count_after = connection.execute(
                """SELECT COUNT(*) FROM src_operation_revisions
                   WHERE status = 'DISPATCHED'"""
            ).fetchone()[0]
        self.assertLessEqual(operation_count_after, evaluator.operation_count_before)
        self.assertEqual(dispatch_count_after, evaluator.dispatch_count_before)

    def test_deterministic_evaluator_rejection_is_failed_not_unknown(self) -> None:
        service = MavenStructureUpdateService(
            self.update_repository,
            self.scopes,
            self.configurations,
            self.operations,
            self.artifact_use,
            self.admission,
            self.verifier_assessments,
            self.verifier,
            self.publication,
            evaluator=RejectingEvaluator(),
            clock=self.clock,
        )
        request = self.request(self.revision_a, key="evaluator-rejection")

        with self.assertRaises(DomainError) as rejected:
            service.execute(request)

        self.assertEqual(rejected.exception.code, ErrorCode.INVALID_ARGUMENT)
        self.assertEqual(
            rejected.exception.details["reason_code"],
            MavenStructureErrorCode.REACTOR_GA_AMBIGUOUS.value,
        )
        durable = service.get_result(idempotency_key=request.idempotency_key)
        self.assertEqual(durable.state, MavenStructureUpdateState.FAILED)
        self.assertEqual(dict(durable.failure_details)["locator"], "pom.xml")

    def test_pom_and_call_budgets_fail_before_publication(self) -> None:
        with self.assertRaises(DomainError) as pom_budget:
            self.service.execute(
                self.request(self.revision_b, key="pom-budget", max_poms=2)
            )
        self.assertEqual(pom_budget.exception.code, ErrorCode.BUDGET_EXHAUSTED)
        self.assertEqual(pom_budget.exception.details["reason_code"], "MAX_POMS_EXCEEDED")
        self.assertIsNone(self.publication.current_snapshot(self.scope.scope_id))

        with self.assertRaises(DomainError) as call_budget:
            self.service.execute(
                self.request(
                    self.revision_a,
                    key="call-budget",
                    max_calls=1,
                    tree_page_size=100,
                )
            )
        self.assertEqual(call_budget.exception.code, ErrorCode.BUDGET_EXHAUSTED)
        self.assertEqual(call_budget.exception.details["reason_code"], "MAX_CALLS_EXCEEDED")
        self.assertIsNone(self.publication.current_snapshot(self.scope.scope_id))

    def test_tree_jsonl_rejects_malformed_noncanonical_and_duplicate_records(self) -> None:
        record = {
            "is_symlink": False,
            "mode": "100644",
            "object_id": "a" * 40,
            "path": "pom.xml",
            "type": "blob",
        }
        canonical = canonical_json_bytes(record)
        parsed = parse_local_git_tree_jsonl(canonical)
        self.assertEqual(parsed[0][0], "pom.xml")

        cases = (
            b"{",
            json.dumps(record, sort_keys=False).encode("utf-8"),
            canonical + b"\n" + canonical,
            (
                b'{"is_symlink":false,"mode":"100644","mode":"100755",'
                b'"object_id":"' + b"a" * 40 + b'","path":"pom.xml","type":"blob"}'
            ),
        )
        for payload in cases:
            with self.subTest(payload=payload[:40]):
                with self.assertRaises(DomainError):
                    parse_local_git_tree_jsonl(payload)

    def test_request_rejects_short_revision_and_invalid_budgets(self) -> None:
        with self.assertRaises(DomainError):
            self.request("abc123", key="short")
        with self.assertRaises(DomainError):
            replace(self.request(self.revision_a, key="valid"), max_poms=0)


if __name__ == "__main__":
    unittest.main()
