from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
import subprocess
import tempfile
import unittest

from software_world_model.application_services.knowledge_update import (
    BuildObjective,
    CanonicalBuildTarget,
)
from software_world_model.application_services.maven_structure_update import (
    MavenStructureUpdateAuthorityService,
    MavenStructureUpdateRequest,
    MavenStructureUpdateState,
)
from software_world_model.cross_cutting import (
    CorrelationRef,
    Digest,
    DomainError,
    ErrorCode,
    IdempotencyKey,
    Revision,
    StableId,
    digest_of,
)
from software_world_model.infrastructure.sqlite_database import SqliteDatabase
from software_world_model.infrastructure.sqlite_maven_structure_update_repository import (
    SqliteMavenStructureUpdateRepository,
)
from software_world_model.infrastructure.sqlite_scope_repository import (
    SqliteKnowledgeScopeRepository,
)
from software_world_model.infrastructure.sqlite_source_repository import (
    SqliteSourceConfigurationRepository,
)
from software_world_model.knowledge_engine import (
    KnowledgeScopeService,
    ScopePurpose,
    ScopeType,
)
from software_world_model.knowledge_engine.structure import PublicationMode
from software_world_model.knowledge_engine.structure_authority import (
    StructureSchemaAdoptionMode,
)
from software_world_model.knowledge_engine.structure_publication import (
    StructurePublicationReceipt,
    StructureSnapshot,
)
from software_world_model.source_integration import (
    ArtifactUseConfirmation,
    ArtifactUsePurpose,
    LocalGitConfigurationProvider,
    LocalGitConnector,
    LocalGitTargetResolver,
    ProviderRegistry,
    SourceConfigurationService,
)


class StepClock:
    def __init__(self) -> None:
        self.value = datetime(2026, 8, 10, tzinfo=timezone.utc)

    def __call__(self) -> datetime:
        current = self.value
        self.value += timedelta(microseconds=1)
        return current


class FakePublicationAuthority:
    """Trusted Knowledge-owner port used only by the Application repo unit test."""

    def __init__(self) -> None:
        self.receipts: dict[StableId, StructurePublicationReceipt] = {}
        self.snapshots: dict[StableId, StructureSnapshot] = {}

    def persist(self, receipt: StructurePublicationReceipt) -> None:
        self.receipts[receipt.publication_id] = receipt
        self.snapshots[receipt.snapshot.snapshot_id] = receipt.snapshot

    def get_publication(
        self, publication_id: StableId
    ) -> StructurePublicationReceipt:
        try:
            return self.receipts[publication_id]
        except KeyError as exc:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Structure Publication Receipt is not persisted",
            ) from exc

    def get_snapshot(self, snapshot_id: StableId) -> StructureSnapshot:
        try:
            return self.snapshots[snapshot_id]
        except KeyError as exc:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Structure Snapshot is not persisted",
            ) from exc


class FakeArtifactUseAuthority:
    def __init__(self) -> None:
        self.confirmations: dict[StableId, ArtifactUseConfirmation] = {}

    def persist(self, confirmation: ArtifactUseConfirmation) -> None:
        self.confirmations[confirmation.confirmation_id] = confirmation

    def get_confirmation(
        self, confirmation_id: StableId
    ) -> ArtifactUseConfirmation:
        try:
            return self.confirmations[confirmation_id]
        except KeyError as exc:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Artifact use Confirmation is not persisted",
            ) from exc

class MavenStructureUpdateAuthorityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.git_path = self.root / "repository"
        self.git_path.mkdir()
        self._git("init", "-q")
        self._git("config", "user.email", "test@example.com")
        self._git("config", "user.name", "Test")
        (self.git_path / "pom.xml").write_text(
            """<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>org.example</groupId>
  <artifactId>authority</artifactId>
  <version>1</version>
</project>
""",
            encoding="utf-8",
        )
        self._git("add", ".")
        self._git("commit", "-q", "-m", "fixture")
        self.commit = self._git("rev-parse", "HEAD").strip()

        self.database_path = self.root / "authority.sqlite3"
        self.database = SqliteDatabase(self.database_path)
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
                "display_name": "Authority fixture",
                "canonical_system_key": "fixture-system",
            },
            idempotency_key=IdempotencyKey("authority-scope"),
            actor="test",
            reason="Maven authority test",
            correlation_ref=CorrelationRef("authority"),
        )
        self.source = self.configurations.register_data_source(
            provider_type="LOCAL_GIT",
            provider_contract_version="0.1.0",
            identity_domain="LOCAL",
            source_target=str(self.git_path),
            provider_configuration={"read_mode": "read_only"},
            secret_reference=None,
            idempotency_key=IdempotencyKey("authority-source"),
            actor="test",
            reason="Maven authority test",
            correlation_ref=CorrelationRef("authority"),
        )
        assertion = self.scopes.read_scope_state_assertion(
            scope_id=self.scope.scope_id,
            expected_revision=Revision(1),
            purpose=ScopePurpose.BIND_CONFIGURATION,
            caller_ref="test",
            request_ref="authority-binding",
            classification="INTERNAL",
        )
        self.binding = self.configurations.bind_source_to_scope(
            source_id=self.source.source_id,
            assertion=assertion,
            selector={"paths": "."},
            context_constraint={"revision_policy": "exact"},
            context_hint="Authority fixture",
            idempotency_key=IdempotencyKey("authority-binding"),
            actor="test",
            reason="Maven authority test",
            correlation_ref=CorrelationRef("authority"),
        )
        self.publications = FakePublicationAuthority()
        self.artifact_uses = FakeArtifactUseAuthority()
        self.repository = SqliteMavenStructureUpdateRepository(
            self.database,
            self.publications,
            self.artifact_uses,
        )
        self.service = MavenStructureUpdateAuthorityService(
            self.repository,
            self.scopes,
            self.configurations,
            clock=self.clock,
        )
        self.resolver = LocalGitTargetResolver(LocalGitConnector(str(self.git_path)))

    def tearDown(self) -> None:
        self.database.close()
        self.temporary.cleanup()

    def _git(self, *arguments: str) -> str:
        result = subprocess.run(
            ("git", "-C", str(self.git_path), *arguments),
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return result.stdout

    def request(
        self,
        *,
        key: str,
        canonical_system_key: str = "fixture-system",
        scope_revision: Revision = Revision(1),
        binding_revision: Revision = Revision(1),
        repository_revision: str | None = None,
        target: CanonicalBuildTarget | None = None,
    ) -> MavenStructureUpdateRequest:
        revision = repository_revision or self.commit
        exact_target = target or CanonicalBuildTarget.from_receipt(
            self.resolver.resolve_revision(revision)
        )
        return MavenStructureUpdateRequest(
            idempotency_key=IdempotencyKey(key),
            objective=BuildObjective.create(
                objective_id=f"manual-maven:{key}",
                description="Build exact Maven Structure knowledge",
                unacceptable_outcomes=(
                    "target substitution",
                    "forged Requirement binding",
                ),
            ),
            target=exact_target,
            requirement_binding=None,
            scope_id=self.scope.scope_id,
            scope_revision=scope_revision,
            source_id=self.source.source_id,
            source_revision=Revision(1),
            binding_id=self.binding.binding_id,
            binding_revision=binding_revision,
            repository_revision=revision,
            logical_reactor_root="pom.xml",
            canonical_system_key=canonical_system_key,
            expected_current_snapshot_id=None,
            max_poms=8,
            max_calls=16,
            tree_page_size=8,
            max_bytes_per_call=8192,
            classification="INTERNAL",
            actor_ref="test/maven-authority",
            correlation_ref=CorrelationRef("authority"),
        )

    def test_manual_request_requires_canonical_objective_target_and_no_requirement(self) -> None:
        request = self.request(key="valid")
        self.assertIsNone(request.requirement_binding)
        self.assertEqual(
            dict(request.target.canonical_identity)["revision"],
            request.repository_revision,
        )

        with self.assertRaises(DomainError) as forged_requirement:
            replace(request, requirement_binding=object())
        self.assertEqual(
            forged_requirement.exception.details["reason_code"],
            "MANUAL_REQUIREMENT_BINDING_FORBIDDEN",
        )

        with self.assertRaises(DomainError) as forged_objective:
            replace(
                request,
                objective=replace(
                    request.objective,
                    digest=Digest("sha256:" + "f" * 64),
                ),
            )
        self.assertEqual(
            forged_objective.exception.details["reason_code"],
            "BUILD_OBJECTIVE_INVALID",
        )

        other_commit = "f" * 40
        other_receipt = self.resolver.resolve_revision(other_commit)
        self.assertNotEqual(dict(request.target.canonical_identity)["revision"], other_commit)
        self.assertNotEqual(other_receipt.canonical_identity, request.target.canonical_identity)

    def test_public_resolver_receipt_mismatch_is_durable_failure(self) -> None:
        # Resolving HEAD and resolving its exact object ID have the same canonical
        # revision but distinct proposal-bound receipts.  The service requires
        # the exact-object receipt used by this manual command.
        alias_target = CanonicalBuildTarget.from_receipt(
            self.resolver.resolve_revision("HEAD")
        )
        request = self.request(key="receipt-mismatch", target=alias_target)

        with self.assertRaises(DomainError) as failure:
            self.service.prepare(request)

        self.assertEqual(failure.exception.code, ErrorCode.INVALID_ARGUMENT)
        self.assertEqual(
            failure.exception.details["reason_code"],
            "CANONICAL_BUILD_TARGET_RECEIPT_MISMATCH",
        )
        durable = self.repository.get_result(
            idempotency_key=request.idempotency_key
        )
        self.assertEqual(durable.state, MavenStructureUpdateState.FAILED)
        self.assertEqual(durable.target_id, alias_target.target_id)

    def test_target_authority_rejects_revision_outside_binding_selector(self) -> None:
        (self.git_path / "pom.xml").write_text(
            (self.git_path / "pom.xml").read_text(encoding="utf-8")
            .replace("<version>1</version>", "<version>2</version>"),
            encoding="utf-8",
        )
        self._git("add", ".")
        self._git("commit", "-q", "-m", "second revision")
        second = self._git("rev-parse", "HEAD").strip()
        assertion = self.scopes.read_scope_state_assertion(
            scope_id=self.scope.scope_id,
            expected_revision=Revision(1),
            purpose=ScopePurpose.BIND_CONFIGURATION,
            caller_ref="test",
            request_ref="pin-authority-binding",
            classification="INTERNAL",
        )
        revised_binding = self.configurations.revise_binding(
            binding_id=self.binding.binding_id,
            expected_revision=Revision(1),
            assertion=assertion,
            selector={"paths": ".", "commit": self.commit},
            context_constraint={"revision_policy": "exact"},
            context_hint="Authority fixture pinned to first commit",
            idempotency_key=IdempotencyKey("pin-authority-binding"),
            actor="test",
            reason="prove Target Authority consumes the Binding selector",
            correlation_ref=CorrelationRef("authority"),
        )
        target = CanonicalBuildTarget.from_receipt(
            self.resolver.resolve_revision(second)
        )
        request = self.request(
            key="selector-out-of-scope",
            binding_revision=revised_binding.definition_revision,
            repository_revision=second,
            target=target,
        )

        with self.assertRaises(DomainError) as failure:
            self.service.prepare(request)

        self.assertEqual(
            failure.exception.code,
            ErrorCode.SOURCE_TARGET_OUT_OF_SCOPE,
        )
        durable = self.repository.get_result(
            idempotency_key=request.idempotency_key
        )
        self.assertEqual(durable.state, MavenStructureUpdateState.FAILED)
        self.assertIsNone(durable.target_authority_id)

    def test_target_authority_cannot_revive_a_suspended_historical_binding(self) -> None:
        self.configurations.suspend_binding(
            binding_id=self.binding.binding_id,
            expected_revision=Revision(1),
            idempotency_key=IdempotencyKey("suspend-authority-binding"),
            actor="test",
            reason="prove historical Binding revisions cannot authorize targets",
            correlation_ref=CorrelationRef("authority"),
        )
        request = self.request(
            key="historical-binding-denied",
            binding_revision=Revision(1),
        )

        with self.assertRaises(DomainError) as failure:
            self.service.prepare(request)

        self.assertEqual(failure.exception.code, ErrorCode.REVISION_CONFLICT)
        durable = self.repository.get_result(
            idempotency_key=request.idempotency_key
        )
        self.assertEqual(durable.state, MavenStructureUpdateState.FAILED)
        self.assertIsNone(durable.target_authority_id)

    def test_scope_metadata_and_persistent_system_key_both_prevent_drift(self) -> None:
        first = self.service.prepare(self.request(key="first-authority"))
        self.assertIsNotNone(first.target_authority)
        self.assertEqual(
            first.target_authority.canonical_system_key,
            "fixture-system",
        )

        revised = self.scopes.update_scope_metadata(
            scope_id=self.scope.scope_id,
            expected_revision=Revision(1),
            metadata={
                "display_name": "Authority fixture",
                "canonical_system_key": "drifted-system",
            },
            idempotency_key=IdempotencyKey("scope-key-drift"),
            actor="test",
            reason="exercise persistent Maven identity",
            correlation_ref=CorrelationRef("authority"),
        )
        revised_assertion = self.scopes.read_scope_state_assertion(
            scope_id=self.scope.scope_id,
            expected_revision=revised.definition_revision,
            purpose=ScopePurpose.BIND_CONFIGURATION,
            caller_ref="test",
            request_ref="authority-binding-revision",
            classification="INTERNAL",
        )
        revised_binding = self.configurations.revise_binding(
            binding_id=self.binding.binding_id,
            expected_revision=Revision(1),
            assertion=revised_assertion,
            selector={"paths": "."},
            context_constraint={"revision_policy": "exact"},
            context_hint="Authority fixture",
            idempotency_key=IdempotencyKey("authority-binding-revision"),
            actor="test",
            reason="exercise persistent Maven identity",
            correlation_ref=CorrelationRef("authority"),
        )
        drift = self.request(
            key="second-authority",
            canonical_system_key="drifted-system",
            scope_revision=revised.definition_revision,
            binding_revision=revised_binding.definition_revision,
        )
        with self.assertRaises(DomainError) as failure:
            self.service.prepare(drift)
        self.assertEqual(
            failure.exception.details["reason_code"],
            "CANONICAL_SYSTEM_KEY_DRIFT",
        )
        durable = self.repository.get_result(idempotency_key=drift.idempotency_key)
        self.assertEqual(durable.state, MavenStructureUpdateState.FAILED)

    def test_scope_metadata_key_cannot_be_replaced_by_request_input(self) -> None:
        request = self.request(
            key="metadata-mismatch",
            canonical_system_key="request-only-key",
        )
        with self.assertRaises(DomainError) as failure:
            self.service.prepare(request)
        self.assertEqual(
            failure.exception.details["reason_code"],
            "CANONICAL_SYSTEM_KEY_METADATA_MISMATCH",
        )
        durable = self.repository.get_result(idempotency_key=request.idempotency_key)
        self.assertEqual(durable.state, MavenStructureUpdateState.FAILED)

    def test_scope_metadata_must_explicitly_own_system_key(self) -> None:
        revised = self.scopes.update_scope_metadata(
            scope_id=self.scope.scope_id,
            expected_revision=Revision(1),
            metadata={"display_name": "Authority fixture without identity"},
            idempotency_key=IdempotencyKey("scope-key-removed"),
            actor="test",
            reason="exercise missing Maven identity",
            correlation_ref=CorrelationRef("authority"),
        )
        assertion = self.scopes.read_scope_state_assertion(
            scope_id=self.scope.scope_id,
            expected_revision=revised.definition_revision,
            purpose=ScopePurpose.BIND_CONFIGURATION,
            caller_ref="test",
            request_ref="binding-after-key-removed",
            classification="INTERNAL",
        )
        revised_binding = self.configurations.revise_binding(
            binding_id=self.binding.binding_id,
            expected_revision=Revision(1),
            assertion=assertion,
            selector={"paths": "."},
            context_constraint={"revision_policy": "exact"},
            context_hint="Authority fixture",
            idempotency_key=IdempotencyKey("binding-after-key-removed"),
            actor="test",
            reason="exercise missing Maven identity",
            correlation_ref=CorrelationRef("authority"),
        )
        request = self.request(
            key="metadata-missing",
            scope_revision=revised.definition_revision,
            binding_revision=revised_binding.definition_revision,
        )

        with self.assertRaises(DomainError) as failure:
            self.service.prepare(request)

        self.assertEqual(
            failure.exception.details["reason_code"],
            "CANONICAL_SYSTEM_KEY_METADATA_REQUIRED",
        )
        durable = self.repository.get_result(idempotency_key=request.idempotency_key)
        self.assertEqual(durable.state, MavenStructureUpdateState.FAILED)

    def test_verified_publication_result_replays_and_survives_repository_restart(self) -> None:
        request = self.request(key="durable-success")
        preparation = self.service.prepare(request)
        attempt = preparation.attempt
        acceptance_ref = "MAVEN_STRUCTURE_APPLICATION_PASS@1:test"
        acceptance_digest = digest_of("acceptance")
        source_collection_digest = digest_of("source-collection")
        build_report_digest = digest_of("build-report")
        operation_ids = (_id("source_operation", "1"), _id("source_operation", "2"))
        self.repository.mark_admitting(
            attempt_id=attempt.attempt_id,
            source_collection_digest=source_collection_digest,
            source_operation_ids=operation_ids,
            build_report_digest=build_report_digest,
            application_acceptance_ref=acceptance_ref,
            application_acceptance_digest=acceptance_digest,
            occurred_at=self.clock(),
        )
        admission_id = _id("structure_admission", "3")
        admission_digest = digest_of("admission")
        self.repository.mark_admitted(
            attempt_id=attempt.attempt_id,
            admission_id=admission_id,
            admission_digest=admission_digest,
            occurred_at=self.clock(),
        )
        confirmation = ArtifactUseConfirmation(
            confirmation_id=_id("artifact_use", "a"),
            downstream_use_digest=digest_of("artifact-downstream-use"),
            use_identity_digest=digest_of("artifact-use-identity"),
            request_digest=digest_of("artifact-use-request"),
            package_id=_id("artifact_package", "b"),
            package_digest=digest_of("artifact-package"),
            closure_id=_id("artifact_read_closure", "c"),
            closure_digest=digest_of("artifact-closure"),
            protection_id=_id("artifact_protection", "d"),
            protection_digest=digest_of("artifact-protection"),
            purpose=ArtifactUsePurpose.MAVEN_STRUCTURE_EVIDENCE_PERSISTENCE,
            downstream_request_ref=attempt.attempt_id.value,
            downstream_request_digest=request.digest,
            downstream_candidate_ref="candidate:authority-test",
            downstream_candidate_digest=digest_of("candidate"),
            confirmed_at=self.clock(),
            digest=digest_of("artifact-confirmation"),
        )
        self.artifact_uses.persist(confirmation)
        self.repository.mark_artifact_use_confirmed(
            attempt_id=attempt.attempt_id,
            confirmation=confirmation,
            occurred_at=self.clock(),
        )
        published_at = self.clock()
        snapshot = StructureSnapshot.create(
            snapshot_id=_id("structure_snapshot", "5"),
            scope_id=self.scope.scope_id,
            snapshot_revision=Revision(1),
            previous_snapshot_id=None,
            schema_ref="MAVEN-REACTOR-STRUCTURE@1.0.0",
            schema_digest=digest_of("schema"),
            schema_adoption_mode=StructureSchemaAdoptionMode.INITIAL,
            schema_registration_digest=digest_of("registration"),
            schema_availability_digest=digest_of("availability"),
            schema_adoption_digest=digest_of("adoption"),
            publication_mode=PublicationMode.REPLACE_COVERAGE,
            members=(),
            coverages=(),
            upstream_entities=(),
            published_at=published_at,
        )
        receipt = StructurePublicationReceipt.create(
            publication_id=_id("structure_publication", "4"),
            request_digest=digest_of("publication-request"),
            batch_digest=digest_of("batch"),
            admission_id=admission_id,
            admission_digest=admission_digest,
            application_acceptance_digest=acceptance_digest,
            snapshot=snapshot,
            published_at=published_at,
        )
        self.publications.persist(receipt)
        pending = self.repository.finish_failed(
            attempt_id=attempt.attempt_id,
            error_code="OUTCOME_PENDING",
            error_message="injected uncertain Application finalization",
            error_details={"stage": "PUBLICATION_COMMITTED"},
            outcome_pending=True,
            occurred_at=self.clock(),
        )
        self.assertEqual(pending.state, MavenStructureUpdateState.OUTCOME_PENDING)
        result = self.repository.finish_published(
            attempt_id=attempt.attempt_id,
            publication_receipt=receipt,
            occurred_at=self.clock(),
        )

        self.assertEqual(result.state, MavenStructureUpdateState.PUBLISHED)
        self.assertEqual(result.result_id, pending.result_id)
        self.assertIsNone(result.failure_code)
        self.assertEqual(result.failure_details, ())
        self.assertEqual(result.objective_id, request.objective.objective_id)
        self.assertEqual(result.objective_digest, request.objective.digest)
        self.assertEqual(result.target_digest, request.target.digest)
        self.assertIsNone(result.requirement_binding_digest)
        self.assertEqual(result.source_collection_digest, source_collection_digest)
        self.assertEqual(result.source_operation_ids, operation_ids)
        self.assertEqual(result.build_report_digest, build_report_digest)
        self.assertEqual(result.application_acceptance_digest, acceptance_digest)
        self.assertIsNotNone(result.admission_id)
        self.assertIsNotNone(result.publication_id)

        replay_attempt, replay = self.repository.begin(
            request=request,
            occurred_at=self.clock(),
        )
        self.assertEqual(replay_attempt.attempt_id, attempt.attempt_id)
        self.assertEqual(replay, result)
        with self.assertRaises(DomainError) as mismatch:
            self.repository.begin(
                request=replace(request, max_calls=request.max_calls + 1),
                occurred_at=self.clock(),
            )
        self.assertEqual(mismatch.exception.code, ErrorCode.IDEMPOTENCY_MISMATCH)

        self.database.close()
        restarted_database = SqliteDatabase(self.database_path)
        try:
            restarted = SqliteMavenStructureUpdateRepository(
                restarted_database,
                self.publications,
                self.artifact_uses,
            )
            self.assertEqual(
                restarted.get_result(idempotency_key=request.idempotency_key),
                result,
            )
            restarted_attempt, restarted_result = restarted.begin(
                request=request,
                occurred_at=self.clock(),
            )
            self.assertEqual(restarted_attempt.attempt_id, attempt.attempt_id)
            self.assertEqual(restarted_result, result)
        finally:
            restarted_database.close()
        # tearDown must not close the already closed handle twice.
        self.database = SqliteDatabase()

    def test_unpersisted_publication_receipt_cannot_seal_published_result(self) -> None:
        request = self.request(key="fake-publication-denied")
        attempt = self.service.prepare(request).attempt
        acceptance_digest = digest_of("fake-publication-acceptance")
        self.repository.mark_admitting(
            attempt_id=attempt.attempt_id,
            source_collection_digest=digest_of("fake-source-collection"),
            source_operation_ids=(_id("source_operation", "8"),),
            build_report_digest=digest_of("fake-report"),
            application_acceptance_ref="MAVEN_STRUCTURE_APPLICATION_PASS@1:fake",
            application_acceptance_digest=acceptance_digest,
            occurred_at=self.clock(),
        )
        admission_id = _id("structure_admission", "9")
        admission_digest = digest_of("fake-admission")
        self.repository.mark_admitted(
            attempt_id=attempt.attempt_id,
            admission_id=admission_id,
            admission_digest=admission_digest,
            occurred_at=self.clock(),
        )
        published_at = self.clock()
        fake_snapshot = StructureSnapshot.create(
            snapshot_id=_id("structure_snapshot", "a"),
            scope_id=self.scope.scope_id,
            snapshot_revision=Revision(1),
            previous_snapshot_id=None,
            schema_ref="MAVEN-REACTOR-STRUCTURE@1.0.0",
            schema_digest=digest_of("fake-schema"),
            schema_adoption_mode=StructureSchemaAdoptionMode.INITIAL,
            schema_registration_digest=digest_of("fake-registration"),
            schema_availability_digest=digest_of("fake-availability"),
            schema_adoption_digest=digest_of("fake-adoption"),
            publication_mode=PublicationMode.REPLACE_COVERAGE,
            members=(),
            coverages=(),
            upstream_entities=(),
            published_at=published_at,
        )
        fake_receipt = StructurePublicationReceipt.create(
            publication_id=_id("structure_publication", "b"),
            request_digest=digest_of("fake-publication-request"),
            batch_digest=digest_of("fake-batch"),
            admission_id=admission_id,
            admission_digest=admission_digest,
            application_acceptance_digest=acceptance_digest,
            snapshot=fake_snapshot,
            published_at=published_at,
        )

        with self.assertRaises(DomainError) as failure:
            self.repository.finish_published(
                attempt_id=attempt.attempt_id,
                publication_receipt=fake_receipt,
                occurred_at=self.clock(),
            )

        self.assertEqual(
            failure.exception.code,
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
        )
        self.assertIsNone(
            self.repository.get_result(idempotency_key=request.idempotency_key)
        )
        self.assertEqual(
            self.repository.get_attempt(attempt.attempt_id).state,
            MavenStructureUpdateState.ADMITTING,
        )

    def test_source_failure_is_readable_and_exactly_replayed(self) -> None:
        request = self.request(key="durable-failure")
        preparation = self.service.prepare(request)
        failure = self.repository.finish_failed(
            attempt_id=preparation.attempt.attempt_id,
            error_code=ErrorCode.SOURCE_OPERATION_FAILED.value,
            error_message="tree read failed",
            error_details={"reason_code": "TREE_READ_FAILED", "ordinal": 1},
            outcome_pending=False,
            occurred_at=self.clock(),
        )
        self.assertEqual(failure.state, MavenStructureUpdateState.FAILED)
        self.assertEqual(
            failure.failure_details,
            (("ordinal", 1), ("reason_code", "TREE_READ_FAILED")),
        )
        replay = self.service.prepare(request)
        self.assertEqual(replay.terminal_result, failure)
        self.assertEqual(
            self.repository.get_attempt(preparation.attempt.attempt_id).state,
            MavenStructureUpdateState.FAILED,
        )


def _id(kind: str, digit: str) -> StableId:
    return StableId(f"{kind}_{digit * 32}")


if __name__ == "__main__":
    unittest.main()
