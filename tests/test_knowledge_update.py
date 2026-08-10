from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
import subprocess
import tempfile
import unittest

from software_world_model.application_services import (
    BuildObjective,
    CanonicalBuildTarget,
    InvestigationStopReason,
    KnowledgeNeed,
    KnowledgeRequirementPlan,
    KnowledgeUpdateRequest,
    KnowledgeUpdateService,
    SourceActionProposal,
    UpdateAttemptState,
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
    SqliteFormalKnowledgeRepository,
    SqliteKnowledgeScopeRepository,
    SqliteKnowledgeUpdateRepository,
    SqliteSourceConfigurationRepository,
    SqliteSourceOperationRepository,
)
from software_world_model.knowledge_engine import (
    EntityProposal,
    EvidenceProposal,
    FactProposal,
    FormalKnowledgeService,
    InferenceProposal,
    KnowledgeCandidateBundle,
    KnowledgeContext,
    KnowledgeObjectKind,
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
    SourceOperationService,
    SourceTool,
)


class StepClock:
    def __init__(self) -> None:
        self.value = datetime(2026, 8, 6, tzinfo=timezone.utc)

    def __call__(self) -> datetime:
        current = self.value
        self.value += timedelta(microseconds=1)
        return current


class ScriptedPlanner:
    def __init__(self, proposals):
        self.proposals = list(proposals)
        self.observed_operation_counts = []

    def propose(self, *, request, completed_operations, ordinal):
        del request, ordinal
        self.observed_operation_counts.append(len(completed_operations))
        return self.proposals.pop(0)


class TwoStageInferenceBuilder:
    def build(self, *, request, target, artifacts, source_operations=()):
        del source_operations
        artifact = artifacts[0]
        context = KnowledgeContext.create(dict(target.canonical_identity))
        evidence = EvidenceProposal(
            evidence_key="evidence:source",
            artifact=artifact,
            byte_start=0,
            byte_end=len(artifact.payload),
            locator=artifact.source_native_identity,
        )
        entity = EntityProposal(
            candidate_key="entity:source",
            entity_type="SOURCE_FILE",
            natural_key=f"{target.digest.value}:source",
            label=artifact.source_native_identity,
            context=context,
            evidence_keys=(evidence.evidence_key,),
        )
        facts = (
            FactProposal(
                candidate_key="fact:package",
                subject_candidate_key=entity.candidate_key,
                subject_entity_id=None,
                predicate="DECLARES",
                object_value="package example;",
                context=context,
                evidence_keys=(evidence.evidence_key,),
            ),
            FactProposal(
                candidate_key="fact:class",
                subject_candidate_key=entity.candidate_key,
                subject_entity_id=None,
                predicate="DECLARES",
                object_value="public class App {}",
                context=context,
                evidence_keys=(evidence.evidence_key,),
            ),
        )
        return KnowledgeCandidateBundle("INITIAL@1", (evidence,), (entity,), facts, ())

    def build_inferences(self, *, request, target, premises):
        return KnowledgeCandidateBundle(
            "INITIAL@1",
            (),
            (),
            (),
            (
                InferenceProposal(
                    candidate_key="inference:relationship",
                    inference_type="STRUCTURE",
                    proposition="App is declared in the example package.",
                    premise_references=tuple(item.object_id for item in premises),
                    rule_ref="reviewed-test-inference@1",
                    context=KnowledgeContext.create(dict(target.canonical_identity)),
                    reviewed_need_ids=(request.requirement_plan.needs[0].need_id,),
                ),
            ),
        )


class KnowledgeUpdateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.repo_path = Path(self.temporary.name) / "repo"
        self.repo_path.mkdir()
        self._git("init", "-q")
        self._git("config", "user.email", "test@example.com")
        self._git("config", "user.name", "Test")
        (self.repo_path / "src").mkdir()
        (self.repo_path / "src" / "App.java").write_text(
            "package example;\npublic class App {}\n", encoding="utf-8"
        )
        (self.repo_path / "src" / "Other.java").write_text(
            "package example;\npublic class Other {}\n", encoding="utf-8"
        )
        self._git("add", ".")
        self._git("commit", "-q", "-m", "initial")
        self.commit = self._git("rev-parse", "HEAD").strip()

        self.database = SqliteDatabase()
        self.clock = StepClock()
        self.scopes = KnowledgeScopeService(
            SqliteKnowledgeScopeRepository(self.database), clock=self.clock
        )
        self.scope = self.scopes.create_scope(
            scope_type=ScopeType.SYSTEM,
            metadata={"display_name": "Update"},
            idempotency_key=IdempotencyKey("scope"),
            actor="test",
            reason="update",
            correlation_ref=CorrelationRef("update"),
        )
        self.sources = SourceConfigurationService(
            SqliteSourceConfigurationRepository(self.database),
            ProviderRegistry((LocalGitConfigurationProvider(),)),
            self.scopes,
            clock=self.clock,
        )
        self.source = self.sources.register_data_source(
            provider_type="LOCAL_GIT",
            provider_contract_version="0.1.0",
            identity_domain="LOCAL",
            source_target=str(self.repo_path),
            provider_configuration={"read_mode": "read_only"},
            secret_reference=None,
            idempotency_key=IdempotencyKey("source"),
            actor="test",
            reason="update",
            correlation_ref=CorrelationRef("update"),
        )
        assertion = self.scopes.read_scope_state_assertion(
            scope_id=self.scope.scope_id,
            expected_revision=Revision(1),
            purpose=ScopePurpose.BIND_CONFIGURATION,
            caller_ref="test",
            request_ref="bind",
            classification="INTERNAL",
        )
        self.binding = self.sources.bind_source_to_scope(
            source_id=self.source.source_id,
            assertion=assertion,
            selector={"paths": "src"},
            context_constraint={"revision_policy": "exact"},
            context_hint="update",
            idempotency_key=IdempotencyKey("binding"),
            actor="test",
            reason="update",
            correlation_ref=CorrelationRef("update"),
        )
        self.knowledge = FormalKnowledgeService(
            SqliteFormalKnowledgeRepository(self.database), self.scopes, clock=self.clock
        )
        self.service = KnowledgeUpdateService(
            SqliteKnowledgeUpdateRepository(self.database),
            self.scopes,
            self.sources,
            SourceOperationService(
                SqliteSourceOperationRepository(self.database), self.sources, clock=self.clock
            ),
            self.knowledge,
            clock=self.clock,
        )
        self.resolver = LocalGitTargetResolver(LocalGitConnector(str(self.repo_path)))

    def tearDown(self) -> None:
        self.database.close()
        self.temporary.cleanup()

    def _git(self, *arguments: str) -> str:
        result = subprocess.run(
            ("git", "-C", str(self.repo_path), *arguments),
            check=True,
            stdout=subprocess.PIPE,
            text=True,
        )
        return result.stdout

    def request(
        self,
        *,
        key: str,
        path: str = "src/App.java",
        max_steps: int = 2,
        max_bytes: int = 4096,
        expected=None,
    ) -> KnowledgeUpdateRequest:
        receipt = self.resolver.resolve_path(self.commit, path, allowed_paths=("src",))
        target = CanonicalBuildTarget.from_receipt(receipt)
        return KnowledgeUpdateRequest(
            idempotency_key=IdempotencyKey(key),
            objective=BuildObjective.create(
                objective_id=f"objective:{key}",
                description=f"Build exact knowledge for {path}",
                unacceptable_outcomes=("unrelated target substitution", "silent truncation"),
            ),
            target=target,
            scope_id=self.scope.scope_id,
            scope_revision=Revision(1),
            source_id=self.source.source_id,
            source_revision=Revision(1),
            binding_id=self.binding.binding_id,
            binding_revision=Revision(1),
            expected_current_snapshot_id=expected,
            max_steps=max_steps,
            max_items_per_step=10,
            max_bytes_per_step=max_bytes,
            classification="INTERNAL",
            actor="test",
            correlation_ref=CorrelationRef("update"),
        )

    def revision_request(self, *, key: str, max_steps: int = 4):
        receipt = self.resolver.resolve_revision(self.commit)
        target = CanonicalBuildTarget.from_receipt(receipt)
        base = self.request(key=key, max_steps=max_steps)
        return KnowledgeUpdateRequest(
            idempotency_key=base.idempotency_key,
            objective=base.objective,
            target=target,
            scope_id=base.scope_id,
            scope_revision=base.scope_revision,
            source_id=base.source_id,
            source_revision=base.source_revision,
            binding_id=base.binding_id,
            binding_revision=base.binding_revision,
            expected_current_snapshot_id=base.expected_current_snapshot_id,
            max_steps=max_steps,
            max_items_per_step=base.max_items_per_step,
            max_bytes_per_step=base.max_bytes_per_step,
            classification=base.classification,
            actor=base.actor,
            correlation_ref=base.correlation_ref,
        )

    def service_with_planner(self, planner):
        return KnowledgeUpdateService(
            SqliteKnowledgeUpdateRepository(self.database),
            self.scopes,
            self.sources,
            SourceOperationService(
                SqliteSourceOperationRepository(self.database),
                self.sources,
                clock=self.clock,
            ),
            self.knowledge,
            planner=planner,
            clock=self.clock,
        )

    def test_exact_path_update_publishes_and_replays_one_result(self) -> None:
        request = self.request(key="path-update")
        first = self.service.execute(request)
        replay = self.service.execute(request)

        self.assertEqual(first.state, UpdateAttemptState.COMPLETED)
        self.assertEqual(first.stop_reason, InvestigationStopReason.TARGET_COVERED)
        self.assertTrue(first.target_coverage_complete)
        self.assertIsNotNone(first.published_snapshot_id)
        self.assertEqual(replay.result_id, first.result_id)
        self.assertEqual(len(first.source_operation_references), 1)

    def test_requested_inference_is_published_after_formal_fact_snapshot(self) -> None:
        need = KnowledgeNeed(
            need_id="N1",
            question="How is App related to the example package?",
            required_kinds=(KnowledgeObjectKind.FACT, KnowledgeObjectKind.INFERENCE),
            required_type_names=(),
            required_terms=("App", "example"),
            minimum_support_count=1,
        )
        request = replace(
            self.request(key="two-stage-inference"),
            requirement_plan=KnowledgeRequirementPlan(needs=(need,)),
        )
        service = KnowledgeUpdateService(
            SqliteKnowledgeUpdateRepository(self.database),
            self.scopes,
            self.sources,
            SourceOperationService(
                SqliteSourceOperationRepository(self.database),
                self.sources,
                clock=self.clock,
            ),
            self.knowledge,
            builder=TwoStageInferenceBuilder(),
            clock=self.clock,
        )

        result = service.execute(request)

        self.assertEqual(result.state, UpdateAttemptState.COMPLETED)
        snapshot = self.knowledge.get_snapshot(result.published_snapshot_id)
        self.assertEqual(snapshot.snapshot_revision, Revision(2))
        self.assertIsNotNone(snapshot.previous_snapshot_id)
        records, cursor = self.knowledge.query_snapshot(
            snapshot_id=snapshot.snapshot_id,
            kinds=(KnowledgeObjectKind.INFERENCE,),
        )
        self.assertIsNone(cursor)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].reviewed_need_ids, ("N1",))
        self.assertEqual(len(records[0].support_references), 2)

    def test_truncated_exact_path_does_not_claim_coverage_or_publish(self) -> None:
        result = self.service.execute(
            self.request(key="truncated", max_steps=1, max_bytes=5)
        )

        self.assertEqual(result.state, UpdateAttemptState.FAILED)
        self.assertFalse(result.target_coverage_complete)
        self.assertIsNone(result.published_snapshot_id)
        self.assertEqual(result.stop_reason, InvestigationStopReason.RESOURCE_EXHAUSTED)
        self.assertIsNone(self.knowledge.current_snapshot(self.scope.scope_id))

    def test_stale_expected_current_preserves_existing_snapshot(self) -> None:
        first = self.service.execute(self.request(key="first"))
        stale = self.service.execute(self.request(key="stale", path="src/Other.java", expected=None))

        self.assertEqual(stale.state, UpdateAttemptState.FAILED)
        self.assertEqual(stale.stop_reason, InvestigationStopReason.PUBLICATION_CONFLICT)
        self.assertEqual(
            self.knowledge.current_snapshot(self.scope.scope_id).snapshot_id,
            first.published_snapshot_id,
        )

    def test_non_exact_target_cannot_enter_build_intent(self) -> None:
        ambiguous = self.resolver.resolve_revision(self.commit[:8])
        with self.assertRaises(DomainError):
            CanonicalBuildTarget.from_receipt(ambiguous)

    def test_injected_planner_can_list_then_read_before_stopping(self) -> None:
        planner = ScriptedPlanner(
            (
                SourceActionProposal.execute(
                    SourceTool.LIST,
                    {"revision": self.commit},
                    rationale="enumerate the exact revision",
                ),
                SourceActionProposal.execute(
                    SourceTool.READ,
                    {"revision": self.commit, "path": "src/App.java"},
                    rationale="read the relevant source file",
                ),
                SourceActionProposal.finish(
                    rationale="the requested repository evidence is observed"
                ),
            )
        )

        result = self.service_with_planner(planner).execute(
            self.revision_request(key="planned-revision")
        )

        self.assertEqual(result.state, UpdateAttemptState.COMPLETED)
        self.assertEqual(len(result.source_operation_references), 2)
        self.assertEqual(planner.observed_operation_counts, [0, 1, 2])

    def test_empty_repository_search_does_not_claim_target_coverage(self) -> None:
        planner = ScriptedPlanner(
            (
                SourceActionProposal.execute(
                    SourceTool.SEARCH,
                    {"revision": self.commit, "query": "does-not-exist"},
                    rationale="search for a missing term",
                ),
                SourceActionProposal.finish(
                    rationale="no evidence was found"
                ),
            )
        )

        result = self.service_with_planner(planner).execute(
            self.revision_request(key="empty-search", max_steps=2)
        )

        self.assertEqual(result.state, UpdateAttemptState.FAILED)
        self.assertFalse(result.target_coverage_complete)
        self.assertEqual(
            result.stop_reason, InvestigationStopReason.SOURCE_INCOMPLETE
        )
        self.assertIsNone(result.published_snapshot_id)

    def test_comparison_planner_can_read_exact_base_and_target_files(self) -> None:
        (self.repo_path / "src" / "App.java").write_text(
            "package example;\npublic class App { int value = 2; }\n",
            encoding="utf-8",
        )
        self._git("add", ".")
        self._git("commit", "-q", "-m", "change App")
        target_revision = self._git("rev-parse", "HEAD").strip()
        receipt = self.resolver.resolve_comparison(self.commit, target_revision)
        base_request = self.request(key="planned-comparison", max_steps=4)
        request = KnowledgeUpdateRequest(
            idempotency_key=base_request.idempotency_key,
            objective=base_request.objective,
            target=CanonicalBuildTarget.from_receipt(receipt),
            scope_id=base_request.scope_id,
            scope_revision=base_request.scope_revision,
            source_id=base_request.source_id,
            source_revision=base_request.source_revision,
            binding_id=base_request.binding_id,
            binding_revision=base_request.binding_revision,
            expected_current_snapshot_id=None,
            max_steps=4,
            max_items_per_step=base_request.max_items_per_step,
            max_bytes_per_step=base_request.max_bytes_per_step,
            classification=base_request.classification,
            actor=base_request.actor,
            correlation_ref=base_request.correlation_ref,
        )
        planner = ScriptedPlanner(
            (
                SourceActionProposal.execute(
                    SourceTool.COMPARE,
                    {"base": self.commit, "revision": target_revision},
                    rationale="observe the exact comparison",
                ),
                SourceActionProposal.execute(
                    SourceTool.READ,
                    {"revision": self.commit, "path": "src/App.java"},
                    rationale="read the exact base file",
                ),
                SourceActionProposal.execute(
                    SourceTool.READ,
                    {"revision": target_revision, "path": "src/App.java"},
                    rationale="read the exact target file",
                ),
                SourceActionProposal.finish(
                    rationale="the diff and both exact file versions are observed"
                ),
            )
        )

        result = self.service_with_planner(planner).execute(request)

        self.assertEqual(result.state, UpdateAttemptState.COMPLETED)
        self.assertEqual(len(result.source_operation_references), 3)
        self.assertEqual(planner.observed_operation_counts, [0, 1, 2, 3])

    def test_injected_planner_cannot_expand_the_exact_revision(self) -> None:
        planner = ScriptedPlanner(
            (
                SourceActionProposal.execute(
                    SourceTool.SEARCH,
                    {"revision": "0" * 40, "query": "class"},
                    rationale="attempt a different revision",
                ),
            )
        )

        result = self.service_with_planner(planner).execute(
            self.revision_request(key="planner-boundary", max_steps=1)
        )

        self.assertEqual(result.state, UpdateAttemptState.FAILED)
        self.assertEqual(result.stop_reason, InvestigationStopReason.SOURCE_FAILED)
        self.assertEqual(result.source_operation_references, ())
        self.assertIn(ErrorCode.CONTROL_STATE_DENIED.value, result.limitations[0])


if __name__ == "__main__":
    unittest.main()
