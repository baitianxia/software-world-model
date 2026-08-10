from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import subprocess
import tempfile
import unittest

from software_world_model.application_services import (
    AnswerSectionKind,
    BuildObjective,
    CanonicalBuildTarget,
    EvidenceAnswerDraft,
    EvidenceAnswerRequest,
    EvidenceAnswerReview,
    EvidenceAnswerSection,
    EvidenceAnswerService,
    EvidenceReviewDecision,
    EvidenceReviewFinding,
    EVIDENCE_REVIEW_DIMENSIONS,
    EvidenceResponseControlService,
    KnowledgeUpdateRequest,
    QuestionChecklist,
    SourceActionProposal,
)
from software_world_model.cross_cutting import (
    CorrelationRef,
    IdempotencyKey,
    Revision,
)
from software_world_model.infrastructure import (
    SqliteDatabase,
    SqliteKnowledgeScopeRepository,
    SqliteSourceConfigurationRepository,
    SqliteSourceOperationRepository,
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
    SourceOperationService,
    SourceTool,
)


class StepClock:
    def __init__(self) -> None:
        self.value = datetime(2026, 8, 10, tzinfo=timezone.utc)

    def __call__(self):
        value = self.value
        self.value += timedelta(microseconds=1)
        return value


class ScriptedSourcePlanner:
    def __init__(self, proposals):
        self.proposals = list(proposals)
        self.calls = []

    def propose(self, *, request, completed_operations, ordinal):
        self.calls.append(
            (request.idempotency_key.value, len(completed_operations), ordinal)
        )
        return self.proposals.pop(0)


class FixedChecklistPlanner:
    def plan(self, *, original_request, execution_ref):
        del execution_ref
        return QuestionChecklist.create(
            original_request=original_request,
            questions=("入口如何返回结果？",),
        )


class RecordingGenerator:
    def __init__(self):
        self.calls = []

    def generate(
        self,
        *,
        checklist,
        packet,
        revision,
        prior_draft,
        review_findings,
        execution_ref,
    ):
        del execution_ref
        self.calls.append(
            {
                "packet": packet.digest,
                "revision": revision,
                "prior": prior_draft,
                "findings": review_findings,
            }
        )
        text = (
            "入口类存在。"
            if prior_draft is None
            else "入口类的 run 方法直接返回 ok。"
        )
        return EvidenceAnswerDraft.create(
            revision=revision,
            checklist=checklist,
            packet=packet,
            sections=(
                EvidenceAnswerSection.create(
                    section_id="answer",
                    kind=AnswerSectionKind.SUPPORTED,
                    text=text,
                    checklist_item_ids=("check-1",),
                    evidence_ids=(packet.items[-1].evidence_id,),
                ),
            ),
        )


class RewriteThenApproveReviewer:
    def __init__(self):
        self.calls = []

    def review(self, *, checklist, packet, draft, execution_ref):
        del execution_ref
        self.calls.append((packet.digest, draft.digest))
        if len(self.calls) == 1:
            finding = EvidenceReviewFinding.create(
                checklist_item_id="check-1",
                category="MISSING_ANSWER",
                description="说明 run 方法的返回值。",
                evidence_ids=(packet.items[-1].evidence_id,),
            )
            return EvidenceAnswerReview.create(
                decision=EvidenceReviewDecision.REWRITE_REQUIRED,
                checks=tuple(
                    (item, item != "REQUEST_COMPLETENESS")
                    for item in EVIDENCE_REVIEW_DIMENSIONS
                ),
                checklist=checklist,
                packet=packet,
                draft=draft,
                findings=(finding,),
            )
        return EvidenceAnswerReview.create(
            decision=EvidenceReviewDecision.APPROVED,
            checks=tuple((item, True) for item in EVIDENCE_REVIEW_DIMENSIONS),
            checklist=checklist,
            packet=packet,
            draft=draft,
            findings=(),
        )


class RetrieveThenApproveReviewer:
    def __init__(self):
        self.calls = 0

    def review(self, *, checklist, packet, draft, execution_ref):
        del execution_ref
        self.calls += 1
        if self.calls == 1:
            finding = EvidenceReviewFinding.create(
                checklist_item_id="check-1",
                category="EVIDENCE_GAP",
                description="需要读取入口实现，而不只是路径列表。",
            )
            return EvidenceAnswerReview.create(
                decision=EvidenceReviewDecision.MORE_EVIDENCE_REQUIRED,
                checks=tuple(
                    (item, item != "EVIDENCE_GROUNDING")
                    for item in EVIDENCE_REVIEW_DIMENSIONS
                ),
                checklist=checklist,
                packet=packet,
                draft=draft,
                findings=(finding,),
            )
        return EvidenceAnswerReview.create(
            decision=EvidenceReviewDecision.APPROVED,
            checks=tuple((item, True) for item in EVIDENCE_REVIEW_DIMENSIONS),
            checklist=checklist,
            packet=packet,
            draft=draft,
            findings=(),
        )


class EvidenceAnswerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.repo = Path(self.temporary.name) / "repo"
        self.repo.mkdir()
        self._git("init", "-q")
        self._git("config", "user.email", "test@example.com")
        self._git("config", "user.name", "Test")
        (self.repo / "src").mkdir()
        (self.repo / "src" / "Entry.txt").write_text(
            "class Entry\nrun -> ok\n", encoding="utf-8"
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
            metadata={"display_name": "Evidence"},
            idempotency_key=IdempotencyKey("evidence-scope"),
            actor="test",
            reason="test",
            correlation_ref=CorrelationRef("evidence"),
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
            source_target=str(self.repo),
            provider_configuration={"read_mode": "read_only"},
            secret_reference=None,
            idempotency_key=IdempotencyKey("evidence-source"),
            actor="test",
            reason="test",
            correlation_ref=CorrelationRef("evidence"),
        )
        assertion = self.scopes.read_scope_state_assertion(
            scope_id=self.scope.scope_id,
            expected_revision=Revision(1),
            purpose=ScopePurpose.BIND_CONFIGURATION,
            caller_ref="test",
            request_ref="evidence-bind",
            classification="INTERNAL",
        )
        self.binding = self.sources.bind_source_to_scope(
            source_id=self.source.source_id,
            assertion=assertion,
            selector={"paths": "src"},
            context_constraint={"revision_policy": "exact"},
            context_hint="evidence",
            idempotency_key=IdempotencyKey("evidence-binding"),
            actor="test",
            reason="test",
            correlation_ref=CorrelationRef("evidence"),
        )
        self.operations = SourceOperationService(
            SqliteSourceOperationRepository(self.database),
            self.sources,
            clock=self.clock,
        )
        self.resolver = LocalGitTargetResolver(LocalGitConnector(str(self.repo)))

    def tearDown(self):
        self.database.close()
        self.temporary.cleanup()

    def _git(self, *args):
        return subprocess.run(
            ("git", "-C", str(self.repo), *args),
            check=True,
            stdout=subprocess.PIPE,
            text=True,
        ).stdout

    def _request(self, *, key, repository_target=False):
        receipt = (
            self.resolver.resolve_revision(self.commit)
            if repository_target
            else self.resolver.resolve_path(
                self.commit, "src/Entry.txt", allowed_paths=("src",)
            )
        )
        source_request = KnowledgeUpdateRequest(
            idempotency_key=IdempotencyKey(f"{key}:source"),
            objective=BuildObjective.create(
                objective_id=f"objective:{key}",
                description="Collect evidence",
                unacceptable_outcomes=("unsupported answer",),
            ),
            target=CanonicalBuildTarget.from_receipt(receipt),
            scope_id=self.scope.scope_id,
            scope_revision=Revision(1),
            source_id=self.source.source_id,
            source_revision=Revision(1),
            binding_id=self.binding.binding_id,
            binding_revision=Revision(1),
            expected_current_snapshot_id=None,
            max_steps=4,
            max_items_per_step=100,
            max_bytes_per_step=4096,
            classification="INTERNAL",
            actor="test",
            correlation_ref=CorrelationRef(key),
        )
        return EvidenceAnswerRequest(
            idempotency_key=IdempotencyKey(key),
            original_request="入口如何返回结果？",
            source_request=source_request,
            classification="INTERNAL",
            caller_ref="test",
            correlation_ref=CorrelationRef(key),
        )

    def test_rewrite_reuses_the_exact_packet_without_new_source_reads(self):
        planner = ScriptedSourcePlanner(
            [
                SourceActionProposal.execute(
                    SourceTool.READ,
                    {"revision": self.commit, "path": "src/Entry.txt"},
                    rationale="read exact entry",
                ),
                SourceActionProposal.finish(rationale="evidence collected"),
            ]
        )
        generator = RecordingGenerator()
        reviewer = RewriteThenApproveReviewer()
        service = EvidenceAnswerService(
            scopes=self.scopes,
            configurations=self.sources,
            operations=self.operations,
            source_planner=planner,
            checklist_planner=FixedChecklistPlanner(),
            responses=EvidenceResponseControlService(
                answer_generator=generator,
                answer_reviewer=reviewer,
            ),
        )

        result = service.execute(self._request(key="rewrite"))

        self.assertEqual(result.source_operation_count, 1)
        self.assertEqual(len(planner.calls), 2)
        self.assertEqual(len(generator.calls), 2)
        self.assertEqual(generator.calls[0]["packet"], generator.calls[1]["packet"])
        self.assertIsNone(generator.calls[0]["prior"])
        self.assertIsNotNone(generator.calls[1]["prior"])
        self.assertEqual(len(generator.calls[1]["findings"]), 1)
        self.assertEqual(result.draft.body, "入口类的 run 方法直接返回 ok。")

    def test_review_evidence_gap_runs_targeted_retrieval_before_regeneration(self):
        planner = ScriptedSourcePlanner(
            [
                SourceActionProposal.execute(
                    SourceTool.LIST,
                    {"revision": self.commit},
                    rationale="locate relevant paths",
                ),
                SourceActionProposal.finish(rationale="initial evidence collected"),
                SourceActionProposal.execute(
                    SourceTool.READ,
                    {"revision": self.commit, "path": "src/Entry.txt"},
                    rationale="read reviewer-requested implementation",
                ),
                SourceActionProposal.finish(rationale="targeted evidence collected"),
            ]
        )
        generator = RecordingGenerator()
        reviewer = RetrieveThenApproveReviewer()
        service = EvidenceAnswerService(
            scopes=self.scopes,
            configurations=self.sources,
            operations=self.operations,
            source_planner=planner,
            checklist_planner=FixedChecklistPlanner(),
            responses=EvidenceResponseControlService(
                answer_generator=generator,
                answer_reviewer=reviewer,
            ),
        )

        result = service.execute(
            self._request(key="retrieve", repository_target=True)
        )

        self.assertEqual(result.source_operation_count, 2)
        self.assertEqual(len(generator.calls), 2)
        self.assertNotEqual(generator.calls[0]["packet"], generator.calls[1]["packet"])
        self.assertIsNone(generator.calls[1]["prior"])
        self.assertEqual(reviewer.calls, 2)


if __name__ == "__main__":
    unittest.main()
