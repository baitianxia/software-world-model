from __future__ import annotations

from dataclasses import replace
import unittest

from software_world_model.application_services.engineering_question_answering import (
    AnswerClaimKind,
    ChecklistDisposition,
    ChecklistOutcome,
    CognitionDimension,
    CognitionItem,
    EngineeringAnswerClaimProposal,
    EngineeringAnswerProposal,
    EngineeringQuestionAnsweringService,
    EngineeringQuestionRequest,
    EngineeringQuestionResourceLimits,
    EngineeringQuestionResourceUsage,
    EngineeringQuestionResultStatus,
    EngineeringReviewDecision,
    EngineeringReviewFinding,
    EngineeringReviewProposal,
    EngineeringEvidenceClass,
    EvidenceLedger,
    InvestigationKind,
    InvestigationOperation,
    InvestigationStepProposal,
    LedgerEntryKind,
    LedgerTerminalStatus,
    PackageBoundaryKind,
    QuestionEvidencePackage,
    QuestionUnderstanding,
    QuestionUnderstandingProposal,
    RetrievalItem,
    RetrievalResult,
    RetrievalStatus,
    SourceBroker,
    SourceReadOperation,
    VerificationRequestProposal,
    WorldModelCognitionContext,
)
from software_world_model.cross_cutting import (
    Digest,
    DomainError,
    ErrorCode,
    StableId,
)
from software_world_model.interface.engineering_qa_source import (
    LocalGitEvidenceClassProfile,
)


REVISION = "a" * 40


def sid(kind: str, digit: str) -> StableId:
    return StableId(f"{kind}_{digit * 32}")


def source_profile() -> LocalGitEvidenceClassProfile:
    return LocalGitEvidenceClassProfile.create(
        profile_ref="engineering-qa-test-source-profile:1",
        binding_id=sid("binding", "2"),
        evidence_class_paths={
            EngineeringEvidenceClass.SOURCE: ("src",),
            EngineeringEvidenceClass.REPOSITORY_DOCUMENT: ("README.md",),
            EngineeringEvidenceClass.BUILD_CONFIGURATION: ("config",),
            EngineeringEvidenceClass.TEST: ("tests",),
        },
    )


def request(
    *, limits: EngineeringQuestionResourceLimits | None = None
) -> EngineeringQuestionRequest:
    profile = source_profile()
    return EngineeringQuestionRequest.create(
        request_ref="test-request",
        original_question="How is the service started and which timeout controls it?",
        response_language="en",
        repository_id=sid("repository", "1"),
        binding_id=sid("binding", "2"),
        repository_revision=REVISION,
        source_profile_ref=profile.profile_ref,
        source_profile_digest=profile.profile_digest,
        world_model_read_authority_digest=Digest("sha256:" + "3" * 64),
        source_allowlist=(".",),
        limits=limits,
    )


class UnderstandingRole:
    def understand(self, *, request, role_context_id):
        return QuestionUnderstandingProposal.create(
            role_context_id=role_context_id,
            request_digest=request.digest,
            preserved_original_question=request.original_question,
            user_goal="Understand startup and timeout configuration.",
            audience="maintainer",
            requested_abstraction_level="engineering overview",
            material_conclusions=("Explain startup and the effective timeout control.",),
            evidence_needs=("published architecture and repository usage/configuration",),
            response_language=request.response_language,
            response_constraints=("conclusion first",),
        )


class CognitionProjector:
    def project(self, *, request):
        item = CognitionItem.create(
            dimension=CognitionDimension.BEHAVIOR,
            statement="The application delegates startup to a product-owned entry point.",
            modality="PUBLISHED_BEHAVIOR",
            context_ref="context-main",
            source_revision=request.repository_revision,
            locator="snapshot:behavior:start",
            support_references=("fact-startup",),
            coverage="startup architecture only",
        )
        return WorldModelCognitionContext.create(
            request=request,
            scope_ref="scope-system",
            context_ref="context-main",
            schema_ref="schema-java",
            snapshot_ids=("snapshot-main",),
            read_authority_digest=request.world_model_read_authority_digest,
            source_revision=request.repository_revision,
            items=(item,),
            coverage=("published behavior",),
            unknowns=("effective timeout value is not modeled",),
        )


def step_proposal(
    investigation_input,
    *,
    operation: InvestigationOperation,
    evidence_class: EngineeringEvidenceClass | None = None,
    query: str | None = None,
    locator_reference: StableId | None = None,
    evidence_reference: str | None = None,
):
    ledger = investigation_input.ledger
    kind = (
        InvestigationKind.INITIAL
        if investigation_input.__class__.__name__.startswith("Initial")
        else InvestigationKind.VERIFICATION
    )
    dispositions = ()
    if operation is InvestigationOperation.FINISH:
        dispositions = (
            ChecklistDisposition.create(
                checklist_item_id="check-1",
                outcome=ChecklistOutcome.SUPPORTED,
                evidence_references=(evidence_reference,),
                explanation="The exact package contains the required evidence.",
            ),
        )
    return InvestigationStepProposal.create(
        investigation_kind=kind,
        attempt_id=investigation_input.attempt_id,
        role_context_id=investigation_input.role_context_id,
        request_digest=(
            investigation_input.request.digest
            if kind is InvestigationKind.INITIAL
            else investigation_input.current_package.request_digest
        ),
        step_index=investigation_input.step_index,
        ledger_id=ledger.ledger_id,
        ledger_generation=ledger.generation,
        ledger_revision=len(ledger.entries),
        ledger_prefix_digest=ledger.prefix_digest,
        operation=operation,
        checklist_item_ids=("check-1",),
        evidence_class=evidence_class,
        query=query,
        locator_reference=locator_reference,
        basis_entry_ids=(ledger.entries[-1].entry_id,),
        unknown_to_reduce=(
            "investigate the next repository observation"
            if operation is not InvestigationOperation.FINISH
            else "all checklist items have an explicit disposition"
        ),
        finish_dispositions=dispositions,
    )


class InitialInvestigator:
    def propose(self, investigation_input):
        if investigation_input.step_index == 1:
            return step_proposal(
                investigation_input,
                operation=InvestigationOperation.SEARCH,
                evidence_class=EngineeringEvidenceClass.REPOSITORY_DOCUMENT,
                query="start",
            )
        if investigation_input.step_index == 2:
            locator = investigation_input.retrieval_results[-1].items[0].locator_reference
            return step_proposal(
                investigation_input,
                operation=InvestigationOperation.READ,
                evidence_class=EngineeringEvidenceClass.REPOSITORY_DOCUMENT,
                locator_reference=locator,
            )
        evidence = investigation_input.retrieval_results[-1].items[0].item_id.value
        return step_proposal(
            investigation_input,
            operation=InvestigationOperation.FINISH,
            evidence_reference=evidence,
        )


class VerificationInvestigator:
    def propose(self, investigation_input):
        if investigation_input.step_index == 1:
            return step_proposal(
                investigation_input,
                operation=InvestigationOperation.SEARCH,
                evidence_class=EngineeringEvidenceClass.BUILD_CONFIGURATION,
                query="timeout",
            )
        if investigation_input.step_index == 2:
            locator = investigation_input.retrieval_results[-1].items[0].locator_reference
            return step_proposal(
                investigation_input,
                operation=InvestigationOperation.PARSE,
                evidence_class=EngineeringEvidenceClass.BUILD_CONFIGURATION,
                locator_reference=locator,
            )
        evidence = investigation_input.retrieval_results[-1].items[0].item_id.value
        return step_proposal(
            investigation_input,
            operation=InvestigationOperation.FINISH,
            evidence_reference=evidence,
        )


class ScriptedWorker:
    def execute(self, operation):
        if operation.operation is SourceReadOperation.SEARCH:
            path = (
                "README.md"
                if operation.evidence_class
                is EngineeringEvidenceClass.REPOSITORY_DOCUMENT
                else "config/application.properties"
            )
            item = RetrievalItem.create(
                operation_id=operation.operation_id,
                ordinal=1,
                evidence_class=operation.evidence_class,
                path=path,
                line_start=1,
                line_end=1,
                content=(
                    "Use ./run-service to start the service."
                    if path == "README.md"
                    else "request.timeout=30s"
                ),
                modality=operation.result_modality,
                coverage_complete=True,
            )
            return RetrievalResult.create(
                operation=operation,
                status=RetrievalStatus.COMPLETE,
                items=(item,),
                bytes_read=128,
                files_read=2,
                truncated=False,
                coverage={"complete": "true"},
            )
        content = (
            "Use ./run-service to start the service."
            if operation.path == "README.md"
            else "request.timeout=30s"
        )
        item = RetrievalItem.create(
            operation_id=operation.operation_id,
            ordinal=1,
            evidence_class=operation.evidence_class,
            path=operation.path,
            content=content,
            modality=operation.result_modality,
            coverage_complete=True,
        )
        return RetrievalResult.create(
            operation=operation,
            status=RetrievalStatus.COMPLETE,
            items=(item,),
            bytes_read=len(content.encode()),
            files_read=1,
            truncated=False,
            coverage={"complete": "true", "path": operation.path},
        )


class AnswerRole:
    def generate(
        self,
        *,
        original_question,
        understanding,
        package,
        role_context_id,
        rewrite_findings=(),
    ):
        support = tuple(item.entry_id for item in package.support_citation)
        return EngineeringAnswerProposal.create(
            role_context_id=role_context_id,
            package_digest=package.digest,
            response_language=understanding.response_language,
            claims=(
                EngineeringAnswerClaimProposal.create(
                    claim_id="claim-1",
                    kind=AnswerClaimKind.AFFIRMATIVE,
                    text=(
                        "Start the service through its documented entry point; "
                        "the request timeout is controlled by the repository configuration."
                    ),
                    evidence_entry_ids=support,
                ),
            ),
        )


class ReviewerRole:
    def __init__(self, *, request_more_evidence: bool):
        self.request_more_evidence = request_more_evidence
        self.calls = 0

    def review(
        self,
        *,
        original_question,
        understanding,
        package,
        draft,
        role_context_id,
    ):
        self.calls += 1
        if self.request_more_evidence and self.calls == 1:
            finding = EngineeringReviewFinding.create(
                finding_code="CONFIGURATION_EVIDENCE_MISSING",
                checklist_item_id="check-1",
                claim_id="claim-1",
                description="The package does not yet contain configuration evidence.",
            )
            verification = VerificationRequestProposal.create(
                package_digest=package.digest,
                checklist_item_id="check-1",
                claim_id="claim-1",
                evidence_class=EngineeringEvidenceClass.BUILD_CONFIGURATION,
                evidence_need="Static build or runtime configuration defining the request timeout",
            )
            return EngineeringReviewProposal.create(
                role_context_id=role_context_id,
                package_digest=package.digest,
                draft_digest=draft.digest,
                decision=EngineeringReviewDecision.MORE_EVIDENCE_REQUIRED,
                findings=(finding,),
                verification_request=verification,
            )
        return EngineeringReviewProposal.create(
            role_context_id=role_context_id,
            package_digest=package.digest,
            draft_digest=draft.digest,
            decision=EngineeringReviewDecision.APPROVED,
        )


class ManualClock:
    def __init__(self):
        self.now_ns = 0

    def __call__(self):
        return self.now_ns

    def reach(self, milliseconds):
        self.now_ns = milliseconds * 1_000_000


class EngineeringQuestionAnsweringTests(unittest.TestCase):
    def service(self, *, request_more_evidence: bool):
        profile = source_profile()
        return EngineeringQuestionAnsweringService(
            question_understanding_role=UnderstandingRole(),
            cognition_projector=CognitionProjector(),
            initial_investigation_role=InitialInvestigator(),
            verification_investigation_role=VerificationInvestigator(),
            source_broker=SourceBroker(source_profile=profile),
            retrieval_worker=ScriptedWorker(),
            answer_role=AnswerRole(),
            reviewer_role=ReviewerRole(
                request_more_evidence=request_more_evidence
            ),
        )

    def test_adaptive_investigation_seals_two_partition_package(self):
        result = self.service(request_more_evidence=False).answer(request())

        self.assertEqual(result.status, EngineeringQuestionResultStatus.APPROVED)
        self.assertEqual(len(result.packages), 1)
        package = result.current_package
        self.assertTrue(package.support_citation)
        self.assertTrue(package.boundary_audit)
        self.assertTrue(
            all(not item.affirmative_claim_support_allowed for item in package.boundary_audit)
        )
        self.assertEqual(result.usage.source_operations, 2)
        operation_entries = tuple(
            entry
            for entry in result.ledgers[0].entries
            if entry.kind is LedgerEntryKind.SOURCE_OPERATION
        )
        result_entries = tuple(
            entry
            for entry in result.ledgers[0].entries
            if entry.kind is LedgerEntryKind.SOURCE_RESULT
        )
        self.assertTrue(operation_entries)
        self.assertEqual(len(operation_entries), len(result_entries))
        for operation_entry, result_entry in zip(operation_entries, result_entries):
            operation_details = dict(operation_entry.details)
            result_details = dict(result_entry.details)
            self.assertEqual(
                result_details["evidence_class"],
                operation_details["evidence_class"],
            )
            self.assertEqual(
                result_details["result_modality"],
                operation_details["result_modality"],
            )
        self.assertEqual(
            [entry.kind for entry in result.ledgers[0].entries].count(
                LedgerEntryKind.INVESTIGATION_PROPOSAL
            ),
            3,
        )
        self.assertEqual(result.production_activation, "NOT_EXECUTED")

    def test_independent_verification_creates_successor_chain(self):
        result = self.service(request_more_evidence=True).answer(request())

        self.assertEqual(result.status, EngineeringQuestionResultStatus.APPROVED)
        self.assertEqual(len(result.ledgers), 2)
        self.assertEqual(len(result.packages), 2)
        first, second = result.packages
        self.assertEqual(second.prior_package_digest, first.digest)
        self.assertEqual(
            result.ledgers[1].parent_seal_digest,
            result.ledgers[0].seal_digest,
        )
        verification_entry = next(
            entry
            for entry in result.ledgers[1].entries
            if entry.kind is LedgerEntryKind.VERIFICATION_REQUEST
        )
        self.assertEqual(
            verification_entry.references,
            (result.ledgers[0].seal_digest.value, first.digest.value),
        )
        self.assertEqual(
            dict(verification_entry.details)["prior_package_digest"],
            first.digest.value,
        )
        self.assertNotEqual(second.digest, first.digest)
        self.assertEqual(second.ledger_generation, 2)
        self.assertEqual(len(result.drafts), 2)
        self.assertEqual(len(result.reviews), 2)
        self.assertEqual(
            result.authorized_answer.package_digest,
            second.digest,
        )
        self.assertTrue(
            any(
                item.evidence_class is EngineeringEvidenceClass.BUILD_CONFIGURATION
                for item in second.support_citation
            )
        )
        self.assertEqual(result.usage.verification_investigations, 1)
        self.assertTrue(
            any(
                item.kind is PackageBoundaryKind.GAP
                for item in second.boundary_audit
            )
        )

    def test_ledger_is_append_only_and_requires_terminal_entry(self):
        req = request()
        cognition = CognitionProjector().project(request=req)
        ledger = EvidenceLedger.start(request=req, cognition=cognition)
        original = ledger
        subject = Digest("sha256:" + "4" * 64)
        ledger = ledger.append(
            kind=LedgerEntryKind.GAP,
            subject_id="gap-1",
            subject_digest=subject,
        )
        self.assertEqual(len(original.entries), 1)
        self.assertEqual(len(ledger.entries), 2)
        with self.assertRaises(DomainError):
            ledger.seal(LedgerTerminalStatus.FINISHED)
        forged = replace(ledger, prefix_digest=Digest("sha256:" + "5" * 64))
        with self.assertRaises(DomainError):
            forged.append(
                kind=LedgerEntryKind.GAP,
                subject_id="gap-2",
                subject_digest=subject,
            )

    def test_broker_rejects_locator_not_recorded_in_ledger(self):
        req = request()
        cognition = CognitionProjector().project(request=req)
        ledger = EvidenceLedger.start(request=req, cognition=cognition)
        understanding_context = sid("role_context", "5")
        QuestionUnderstanding.accept(
            request=req,
            expected_role_context_id=understanding_context,
            proposal=UnderstandingRole().understand(
                request=req, role_context_id=understanding_context
            ),
        )
        fake_operation = sid("source_operation", "6")
        fake_item = RetrievalItem.create(
            operation_id=fake_operation,
            ordinal=1,
            evidence_class=EngineeringEvidenceClass.SOURCE,
            path="src/Foo.java",
            content="class Foo {}",
            modality="EXACT_STATIC_SOURCE_TEXT",
            coverage_complete=True,
        )
        input_stub = type(
            "InitialInput",
            (),
            {
                "ledger": ledger,
                "attempt_id": sid("investigation_attempt", "7"),
                "role_context_id": sid("role_context", "8"),
                "step_index": 1,
                "request": req,
            },
        )()
        proposal = step_proposal(
            input_stub,
            operation=InvestigationOperation.READ,
            evidence_class=EngineeringEvidenceClass.SOURCE,
            locator_reference=fake_item.locator_reference,
        )
        compilation = SourceBroker(source_profile=source_profile()).compile(
            request=req,
            proposal=proposal,
            ledger=ledger,
            locator_catalog={fake_item.locator_reference: fake_item},
            usage=EngineeringQuestionResourceUsage(),
        )
        self.assertEqual(compilation.decision.status.value, "REJECTED")
        self.assertEqual(
            compilation.decision.reason_code,
            "LOCATOR_NOT_ISSUED_BY_CURRENT_LEDGER",
        )
        self.assertIsNone(compilation.operation)

    def test_broker_rejects_world_model_as_a_source_evidence_class(self):
        req = request()
        cognition = CognitionProjector().project(request=req)
        ledger = EvidenceLedger.start(request=req, cognition=cognition)
        input_stub = type(
            "InitialInput",
            (),
            {
                "ledger": ledger,
                "attempt_id": sid("investigation_attempt", "a"),
                "role_context_id": sid("role_context", "b"),
                "step_index": 1,
                "request": req,
            },
        )()
        proposal = step_proposal(
            input_stub,
            operation=InvestigationOperation.SEARCH,
            evidence_class=EngineeringEvidenceClass.WORLD_MODEL,
            query="startup",
        )
        compilation = SourceBroker(source_profile=source_profile()).compile(
            request=req,
            proposal=proposal,
            ledger=ledger,
            locator_catalog={},
            usage=EngineeringQuestionResourceUsage(),
        )
        self.assertEqual(compilation.decision.status.value, "REJECTED")
        self.assertEqual(
            compilation.decision.reason_code, "EVIDENCE_CLASS_NOT_RETRIEVABLE"
        )

    def test_package_requires_the_complete_ledger_result_set(self):
        result = self.service(request_more_evidence=False).answer(request())
        with self.assertRaises(DomainError):
            QuestionEvidencePackage.seal(
                request=result.request,
                understanding=result.understanding,
                cognition=result.cognition,
                ledger=result.ledgers[0],
                retrieval_results=(),
                broker_decisions=result.broker_decisions,
                checklist_dispositions=result.packages[0].checklist_dispositions,
                package_revision=1,
            )

    def test_role_budget_reserves_answer_and_independent_review(self):
        limits = EngineeringQuestionResourceLimits(
            maximum_total_model_role_calls=3
        )
        result = self.service(request_more_evidence=False).answer(
            request(limits=limits)
        )
        self.assertEqual(result.status, EngineeringQuestionResultStatus.FAILED_CLOSED)
        self.assertEqual(
            result.terminal_reason, "INDEPENDENT_REVIEW_RESERVE_EXHAUSTED"
        )
        self.assertEqual(result.usage.total_role_calls, 1)
        self.assertFalse(result.drafts)
        self.assertFalse(result.reviews)

    def test_repeated_identical_observation_trips_no_progress_fuse(self):
        class RepeatingInvestigator:
            def propose(self, investigation_input):
                return step_proposal(
                    investigation_input,
                    operation=InvestigationOperation.SEARCH,
                    evidence_class=EngineeringEvidenceClass.REPOSITORY_DOCUMENT,
                    query="start",
                )

        service = EngineeringQuestionAnsweringService(
            question_understanding_role=UnderstandingRole(),
            cognition_projector=CognitionProjector(),
            initial_investigation_role=RepeatingInvestigator(),
            verification_investigation_role=VerificationInvestigator(),
            source_broker=SourceBroker(source_profile=source_profile()),
            retrieval_worker=ScriptedWorker(),
            answer_role=AnswerRole(),
            reviewer_role=ReviewerRole(request_more_evidence=False),
        )
        result = service.answer(request())
        self.assertEqual(
            result.status,
            EngineeringQuestionResultStatus.FAILED_CLOSED,
        )
        self.assertEqual(result.terminal_reason, "NO_PROGRESS_FUSE_EXHAUSTED")
        self.assertEqual(result.usage.source_operations, 3)
        self.assertEqual(
            len({item.progress_digest for item in result.retrieval_results}),
            1,
        )

    def test_full_content_locator_cannot_be_reused_for_another_read(self):
        class FullContentReusingInvestigator:
            def propose(self, investigation_input):
                if investigation_input.step_index == 1:
                    return step_proposal(
                        investigation_input,
                        operation=InvestigationOperation.SEARCH,
                        evidence_class=EngineeringEvidenceClass.REPOSITORY_DOCUMENT,
                        query="start",
                    )
                locator = investigation_input.retrieval_results[-1].items[0]
                return step_proposal(
                    investigation_input,
                    operation=InvestigationOperation.READ,
                    evidence_class=EngineeringEvidenceClass.REPOSITORY_DOCUMENT,
                    locator_reference=locator.locator_reference,
                )

        service = EngineeringQuestionAnsweringService(
            question_understanding_role=UnderstandingRole(),
            cognition_projector=CognitionProjector(),
            initial_investigation_role=FullContentReusingInvestigator(),
            verification_investigation_role=VerificationInvestigator(),
            source_broker=SourceBroker(source_profile=source_profile()),
            retrieval_worker=ScriptedWorker(),
            answer_role=AnswerRole(),
            reviewer_role=ReviewerRole(request_more_evidence=False),
        )

        with self.assertRaises(DomainError) as caught:
            service.answer(request())

        self.assertEqual(caught.exception.code, ErrorCode.PROVIDER_RESPONSE_INVALID)
        self.assertIn("single-use locator", str(caught.exception))

    def test_wall_time_fuse_rejects_finish_returned_at_the_deadline(self):
        clock = ManualClock()

        class DeadlineInitialInvestigator:
            def __init__(self):
                self.delegate = InitialInvestigator()

            def propose(self, investigation_input):
                proposal = self.delegate.propose(investigation_input)
                if proposal.operation is InvestigationOperation.FINISH:
                    clock.reach(1)
                return proposal

        service = EngineeringQuestionAnsweringService(
            question_understanding_role=UnderstandingRole(),
            cognition_projector=CognitionProjector(),
            initial_investigation_role=DeadlineInitialInvestigator(),
            verification_investigation_role=VerificationInvestigator(),
            source_broker=SourceBroker(source_profile=source_profile()),
            retrieval_worker=ScriptedWorker(),
            answer_role=AnswerRole(),
            reviewer_role=ReviewerRole(request_more_evidence=False),
            clock_ns=clock,
        )
        result = service.answer(
            request(
                limits=replace(
                    EngineeringQuestionResourceLimits(),
                    maximum_wall_time_milliseconds=1,
                )
            )
        )

        self.assertEqual(
            result.status,
            EngineeringQuestionResultStatus.FAILED_CLOSED,
        )
        self.assertEqual(result.terminal_reason, "WALL_TIME_FUSE_EXHAUSTED")
        self.assertEqual(result.elapsed_milliseconds, 1)
        self.assertFalse(
            any(
                entry.kind is LedgerEntryKind.FINISH
                for entry in result.ledgers[0].entries
            )
        )

    def test_wall_time_fuse_overrides_review_approval_at_the_deadline(self):
        clock = ManualClock()

        class DeadlineReviewer:
            def __init__(self):
                self.delegate = ReviewerRole(request_more_evidence=False)

            def review(self, **kwargs):
                proposal = self.delegate.review(**kwargs)
                clock.reach(1)
                return proposal

        service = EngineeringQuestionAnsweringService(
            question_understanding_role=UnderstandingRole(),
            cognition_projector=CognitionProjector(),
            initial_investigation_role=InitialInvestigator(),
            verification_investigation_role=VerificationInvestigator(),
            source_broker=SourceBroker(source_profile=source_profile()),
            retrieval_worker=ScriptedWorker(),
            answer_role=AnswerRole(),
            reviewer_role=DeadlineReviewer(),
            clock_ns=clock,
        )
        result = service.answer(
            request(
                limits=replace(
                    EngineeringQuestionResourceLimits(),
                    maximum_wall_time_milliseconds=1,
                )
            )
        )

        self.assertEqual(
            result.status,
            EngineeringQuestionResultStatus.FAILED_CLOSED,
        )
        self.assertEqual(result.terminal_reason, "WALL_TIME_FUSE_EXHAUSTED")
        self.assertIsNone(result.authorized_answer)
        self.assertEqual(result.reviews[-1].decision, EngineeringReviewDecision.APPROVED)

    def test_pre_ledger_wall_time_exhaustion_never_reaches_cognition(self):
        clock = ManualClock()

        class DeadlineUnderstanding(UnderstandingRole):
            def understand(self, **kwargs):
                proposal = super().understand(**kwargs)
                clock.reach(1)
                return proposal

        class ForbiddenCognition:
            def project(self, *, request):
                raise AssertionError(
                    "cognition must not run after the wall-time fuse is exhausted"
                )

        service = EngineeringQuestionAnsweringService(
            question_understanding_role=DeadlineUnderstanding(),
            cognition_projector=ForbiddenCognition(),
            initial_investigation_role=InitialInvestigator(),
            verification_investigation_role=VerificationInvestigator(),
            source_broker=SourceBroker(source_profile=source_profile()),
            retrieval_worker=ScriptedWorker(),
            answer_role=AnswerRole(),
            reviewer_role=ReviewerRole(request_more_evidence=False),
            clock_ns=clock,
        )
        with self.assertRaises(DomainError) as caught:
            service.answer(
                request(
                    limits=replace(
                        EngineeringQuestionResourceLimits(),
                        maximum_wall_time_milliseconds=1,
                    )
                )
            )
        self.assertEqual(caught.exception.code, ErrorCode.BUDGET_EXHAUSTED)

    def test_tampered_request_digest_is_rejected_before_any_role_call(self):
        forged = replace(
            request(),
            original_question="A different question under the old Request digest",
        )
        with self.assertRaises(DomainError):
            self.service(request_more_evidence=False).answer(forged)

    def test_tampered_investigation_proposal_is_rejected(self):
        class TamperedInvestigator(InitialInvestigator):
            def propose(self, investigation_input):
                proposal = super().propose(investigation_input)
                if proposal.operation is InvestigationOperation.SEARCH:
                    return replace(proposal, query="forged under the old digest")
                return proposal

        service = EngineeringQuestionAnsweringService(
            question_understanding_role=UnderstandingRole(),
            cognition_projector=CognitionProjector(),
            initial_investigation_role=TamperedInvestigator(),
            verification_investigation_role=VerificationInvestigator(),
            source_broker=SourceBroker(source_profile=source_profile()),
            retrieval_worker=ScriptedWorker(),
            answer_role=AnswerRole(),
            reviewer_role=ReviewerRole(request_more_evidence=False),
        )
        with self.assertRaises(DomainError):
            service.answer(request())

    def test_boundary_entry_cannot_support_affirmative_claim(self):
        class BadAnswerRole(AnswerRole):
            def generate(self, **kwargs):
                package = kwargs["package"]
                return EngineeringAnswerProposal.create(
                    role_context_id=kwargs["role_context_id"],
                    package_digest=package.digest,
                    response_language=kwargs["understanding"].response_language,
                    claims=(
                        EngineeringAnswerClaimProposal.create(
                            claim_id="claim-bad",
                            kind=AnswerClaimKind.AFFIRMATIVE,
                            text="This unsupported assertion must be rejected.",
                            evidence_entry_ids=(package.boundary_audit[0].entry_id,),
                        ),
                    ),
                )

        service = EngineeringQuestionAnsweringService(
            question_understanding_role=UnderstandingRole(),
            cognition_projector=CognitionProjector(),
            initial_investigation_role=InitialInvestigator(),
            verification_investigation_role=VerificationInvestigator(),
            source_broker=SourceBroker(source_profile=source_profile()),
            retrieval_worker=ScriptedWorker(),
            answer_role=BadAnswerRole(),
            reviewer_role=ReviewerRole(request_more_evidence=False),
        )
        with self.assertRaises(DomainError):
            service.answer(request())

    def test_worker_cannot_return_another_profile_class_path(self):
        class RelabelingWorker(ScriptedWorker):
            def execute(self, operation):
                if (
                    operation.evidence_class
                    is EngineeringEvidenceClass.BUILD_CONFIGURATION
                    and operation.operation is SourceReadOperation.PARSE
                ):
                    item = RetrievalItem.create(
                        operation_id=operation.operation_id,
                        ordinal=1,
                        evidence_class=operation.evidence_class,
                        path="README.md",
                        content="request.timeout=30s",
                        modality=operation.result_modality,
                        coverage_complete=True,
                    )
                    return RetrievalResult.create(
                        operation=operation,
                        status=RetrievalStatus.COMPLETE,
                        items=(item,),
                        bytes_read=19,
                        files_read=1,
                        truncated=False,
                        coverage={"complete": "true"},
                    )
                return super().execute(operation)

        service = EngineeringQuestionAnsweringService(
            question_understanding_role=UnderstandingRole(),
            cognition_projector=CognitionProjector(),
            initial_investigation_role=InitialInvestigator(),
            verification_investigation_role=VerificationInvestigator(),
            source_broker=SourceBroker(source_profile=source_profile()),
            retrieval_worker=RelabelingWorker(),
            answer_role=AnswerRole(),
            reviewer_role=ReviewerRole(request_more_evidence=True),
        )
        with self.assertRaises(DomainError) as caught:
            service.answer(request())
        self.assertEqual(caught.exception.code, ErrorCode.SOURCE_TARGET_OUT_OF_SCOPE)

    def test_worker_cannot_upgrade_static_text_to_another_modality(self):
        class ModalityRelabelingWorker(ScriptedWorker):
            def execute(self, operation):
                result = super().execute(operation)
                if operation.operation is SourceReadOperation.READ and result.items:
                    return replace(
                        result,
                        items=(
                            replace(
                                result.items[0],
                                modality="EXECUTED_RUNTIME_OBSERVATION",
                            ),
                        ),
                    )
                return result

        service = EngineeringQuestionAnsweringService(
            question_understanding_role=UnderstandingRole(),
            cognition_projector=CognitionProjector(),
            initial_investigation_role=InitialInvestigator(),
            verification_investigation_role=VerificationInvestigator(),
            source_broker=SourceBroker(source_profile=source_profile()),
            retrieval_worker=ModalityRelabelingWorker(),
            answer_role=AnswerRole(),
            reviewer_role=ReviewerRole(request_more_evidence=False),
        )
        with self.assertRaises(DomainError) as caught:
            service.answer(request())
        self.assertEqual(
            caught.exception.code,
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
        )

    def test_verification_request_rejects_executable_path(self):
        with self.assertRaises(DomainError):
            VerificationRequestProposal.create(
                package_digest=Digest("sha256:" + "9" * 64),
                checklist_item_id="check-1",
                evidence_class=EngineeringEvidenceClass.SOURCE,
                evidence_need="read(src/Main.java)",
            )


if __name__ == "__main__":
    unittest.main()
