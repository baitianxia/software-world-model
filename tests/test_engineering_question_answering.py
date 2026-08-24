from __future__ import annotations

from dataclasses import replace
import unittest

from software_world_model.application_services.engineering_question_answering import (
    AnswerContentRole,
    AnswerDetailLevel,
    AnswerClaimKind,
    ChecklistDisposition,
    ChecklistDispositionReferenceEligibility,
    ChecklistOutcome,
    CognitionDimension,
    CognitionItem,
    EngineeringAnswerClaimProposal,
    EngineeringAnswerDraft,
    EngineeringAnswerProposal,
    EngineeringEvidenceBoundaryAssessment,
    EngineeringEvidenceBoundaryAssessmentDisposition,
    EngineeringEvidenceBoundaryChallengeKind,
    EngineeringMaterialEffectOmissionLayer,
    EngineeringQuestionAnsweringService,
    EngineeringQuestionRequest,
    EngineeringQuestionResourceLimits,
    EngineeringQuestionResourceUsage,
    EngineeringQuestionResultStatus,
    EngineeringReviewDecision,
    EngineeringReviewFocus,
    EngineeringReviewChecklistAssessment,
    EngineeringReviewFinding,
    EngineeringReviewMaterialObservation,
    EngineeringReviewProposal,
    EngineeringReviewQualityAssessment,
    EngineeringReviewQualityStatus,
    EngineeringReviewRemediation,
    EngineeringEvidenceClass,
    EvidenceLedger,
    InvestigationKind,
    InvestigationOperation,
    InvestigationStepProposal,
    LedgerEntryKind,
    LedgerTerminalStatus,
    MAXIMUM_MATERIAL_OBSERVATIONS_PER_DISPOSITION,
    MaterialObservation,
    MaterialObservationKind,
    PackageBoundaryKind,
    QuestionEvidencePackage,
    QuestionUnderstanding,
    QuestionUnderstandingProposal,
    RetrievalItem,
    RetrievalResult,
    RetrievalStatus,
    SourceBroker,
    SourceReadOperation,
    VerificationInvestigationInput,
    VerificationRequestProposal,
    WorldModelCognitionContext,
    _eligible_locator_references,
    _merge_verification_checklist_dispositions,
    _verification_disposition_reference_eligibility,
    project_evidence_boundary_challenges,
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


def passing_quality() -> EngineeringReviewQualityAssessment:
    return EngineeringReviewQualityAssessment.create(
        direct_answer=EngineeringReviewQualityStatus.PASS,
        abstraction_fit=EngineeringReviewQualityStatus.PASS,
        material_completeness=EngineeringReviewQualityStatus.PASS,
        claim_consistency=EngineeringReviewQualityStatus.PASS,
        implementation_detail_budget=EngineeringReviewQualityStatus.PASS,
    )


def matching_review_checklist(
    understanding: QuestionUnderstanding,
    package: QuestionEvidencePackage,
) -> EngineeringReviewChecklistAssessment:
    support_by_source = {
        item.source_reference: item.entry_id for item in package.support_citation
    }
    boundary_by_source = {
        item.source_reference: item.entry_id for item in package.boundary_audit
    }
    observations = tuple(
        EngineeringReviewMaterialObservation.create(
            checklist_item_id=observation.checklist_item_id,
            kind=observation.kind,
            statement=observation.statement,
            evidence_entry_ids=tuple(
                (
                    support_by_source
                    if disposition.outcome is ChecklistOutcome.SUPPORTED
                    else boundary_by_source
                )[reference]
                for reference in observation.evidence_references
            ),
        )
        for disposition in package.checklist_dispositions
        for observation in disposition.material_observations
    )
    return EngineeringReviewChecklistAssessment.create(
        independent_material_conclusions=tuple(
            item.conclusion for item in understanding.checklist
        ),
        application_checklist_omissions=(),
        independent_material_observations=observations,
        application_material_observation_omissions=(),
        draft_material_observation_omissions=(),
    )


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
            requested_abstraction_level=AnswerDetailLevel.USER_VISIBLE_EXPLANATION,
            material_conclusions=("Explain startup and the effective timeout control.",),
            evidence_needs=("published architecture and repository usage/configuration",),
            required_evidence_classes=(
                EngineeringEvidenceClass.REPOSITORY_DOCUMENT,
                EngineeringEvidenceClass.SOURCE,
            ),
            required_evidence_paths=("README.md",),
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
        assert evidence_reference is not None
        dispositions = (
            ChecklistDisposition.create(
                checklist_item_id="check-1",
                outcome=ChecklistOutcome.SUPPORTED,
                evidence_references=(evidence_reference,),
                explanation="The exact package contains the required evidence.",
                material_observations=(
                    MaterialObservation.create(
                        checklist_item_id="check-1",
                        kind=MaterialObservationKind.PROCESS_STAGE,
                        statement="The repository evidence establishes the documented startup entry point.",
                        evidence_references=(evidence_reference,),
                    ),
                    MaterialObservation.create(
                        checklist_item_id="check-1",
                        kind=MaterialObservationKind.SIDE_EFFECT,
                        statement="Starting the service also writes a local PID file.",
                        evidence_references=(evidence_reference,),
                    ),
                ),
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
                    "Use ./run-service to start the service. Startup also writes a local PID file."
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
            "Use ./run-service to start the service. Startup also writes a local PID file."
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
        observation_ids = tuple(
            observation.observation_id
            for disposition in package.checklist_dispositions
            for observation in disposition.material_observations
        )
        return EngineeringAnswerProposal.create(
            role_context_id=role_context_id,
            package_digest=package.digest,
            response_language=understanding.response_language,
            claims=(
                EngineeringAnswerClaimProposal.create(
                    claim_id="claim-1",
                    kind=AnswerClaimKind.AFFIRMATIVE,
                    content_role=AnswerContentRole.DIRECT_ANSWER,
                    checklist_item_ids=("check-1",),
                    material_observation_ids=observation_ids,
                    text=(
                        "Start the service through its documented entry point; "
                        "startup also writes a local PID file; "
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
        self.focuses = []

    def review(
        self,
        *,
        original_question,
        understanding,
        package,
        draft,
        role_context_id,
        review_focus=EngineeringReviewFocus.COMPREHENSIVE,
    ):
        self.calls += 1
        self.focuses.append(review_focus)
        boundary_assessments = ()
        if review_focus is EngineeringReviewFocus.EVIDENCE_BOUNDARY_CHALLENGE:
            boundary_assessments = tuple(
                EngineeringEvidenceBoundaryAssessment.create(
                    challenge_id=challenge.challenge_id,
                    evidence_boundary=(
                        "The complete cited entry contains no additional material "
                        "effect beyond the Draft."
                    ),
                    draft_scope="The Draft stays within the complete cited entry.",
                    disposition=(
                        EngineeringEvidenceBoundaryAssessmentDisposition.WITHIN_EVIDENCE_BOUNDARY
                    ),
                    finding_code=None,
                )
                for challenge in project_evidence_boundary_challenges(
                    package=package,
                    draft=draft,
                )
            )
        if self.request_more_evidence and self.calls == 1:
            finding = EngineeringReviewFinding.create(
                finding_code="CONFIGURATION_EVIDENCE_MISSING",
                checklist_item_id="check-1",
                claim_id="claim-1",
                description="The package does not yet contain configuration evidence.",
                remediation=(
                    EngineeringReviewRemediation.INVESTIGATE_MISSING_EVIDENCE
                ),
                evidence_class=EngineeringEvidenceClass.BUILD_CONFIGURATION,
                evidence_need=(
                    "Static build or runtime configuration defining the request timeout"
                ),
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
                quality_assessment=passing_quality(),
                checklist_assessment=matching_review_checklist(
                    understanding, package
                ),
                findings=(finding,),
                verification_request=verification,
            )
        return EngineeringReviewProposal.create(
            role_context_id=role_context_id,
            package_digest=package.digest,
            draft_digest=draft.digest,
            decision=EngineeringReviewDecision.APPROVED,
            quality_assessment=passing_quality(),
            checklist_assessment=matching_review_checklist(understanding, package),
            evidence_boundary_assessments=boundary_assessments,
        )


class ManualClock:
    def __init__(self):
        self.now_ns = 0

    def __call__(self):
        return self.now_ns

    def reach(self, milliseconds):
        self.now_ns = milliseconds * 1_000_000


class EngineeringQuestionAnsweringTests(unittest.TestCase):
    def test_question_understanding_rejects_more_than_four_required_paths(self):
        req = request()

        with self.assertRaises(DomainError) as caught:
            QuestionUnderstandingProposal.create(
                role_context_id=sid("role_context", "f"),
                request_digest=req.digest,
                preserved_original_question=req.original_question,
                user_goal="Trace the decisive implementation.",
                audience="maintainer",
                requested_abstraction_level=AnswerDetailLevel.IMPLEMENTATION_DETAIL,
                material_conclusions=("Explain the decisive behavior.",),
                evidence_needs=("Exact implementation behavior.",),
                required_evidence_classes=(EngineeringEvidenceClass.SOURCE,),
                required_evidence_paths=tuple(
                    f"src/Required{index}.java" for index in range(5)
                ),
                response_language=req.response_language,
            )

        self.assertEqual(caught.exception.code, ErrorCode.INVALID_ARGUMENT)
        self.assertIn("one to four", caught.exception.message)

    def test_checklist_disposition_preserves_sixteen_atomic_observations(self) -> None:
        reference = "retrieval_item_" + "1" * 32
        observations = tuple(
            MaterialObservation.create(
                checklist_item_id="check-1",
                kind=MaterialObservationKind.PROCESS_STAGE,
                statement=f"Material repository fact {index}.",
                evidence_references=(reference,),
            )
            for index in range(MAXIMUM_MATERIAL_OBSERVATIONS_PER_DISPOSITION)
        )

        disposition = ChecklistDisposition.create(
            checklist_item_id="check-1",
            outcome=ChecklistOutcome.SUPPORTED,
            evidence_references=(reference,),
            explanation="The retained source supports every atomic observation.",
            material_observations=observations,
        )

        self.assertEqual(len(disposition.material_observations), 16)
        with self.assertRaises(DomainError) as raised:
            ChecklistDisposition.create(
                checklist_item_id="check-1",
                outcome=ChecklistOutcome.SUPPORTED,
                evidence_references=(reference,),
                explanation="The retained source supports every atomic observation.",
                material_observations=observations
                + (
                    MaterialObservation.create(
                        checklist_item_id="check-1",
                        kind=MaterialObservationKind.PROCESS_STAGE,
                        statement="One material repository fact beyond the bound.",
                        evidence_references=(reference,),
                    ),
                ),
            )
        self.assertEqual(raised.exception.code, ErrorCode.INVALID_ARGUMENT)

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

    def test_evidence_boundary_challenge_can_block_provisional_approval(self):
        class ChallengeRejectingReviewer:
            def __init__(self):
                self.delegate = ReviewerRole(request_more_evidence=False)

            def review(self, *, review_focus, **kwargs):
                if review_focus is EngineeringReviewFocus.COMPREHENSIVE:
                    return self.delegate.review(
                        review_focus=review_focus,
                        **kwargs,
                    )
                finding = EngineeringReviewFinding.create(
                    finding_code="EVIDENCE_BOUNDARY_UNRECOVERABLE",
                    checklist_item_id="check-1",
                    claim_id="claim-1",
                    description=(
                        "The provisional answer crosses an unrecoverable evidence boundary."
                    ),
                    remediation=EngineeringReviewRemediation.REJECT_UNRECOVERABLE,
                )
                challenges = project_evidence_boundary_challenges(
                    kwargs["package"], kwargs["draft"]
                )
                return EngineeringReviewProposal.create(
                    role_context_id=kwargs["role_context_id"],
                    package_digest=kwargs["package"].digest,
                    draft_digest=kwargs["draft"].digest,
                    decision=EngineeringReviewDecision.REJECT,
                    quality_assessment=passing_quality(),
                    checklist_assessment=matching_review_checklist(
                        kwargs["understanding"],
                        kwargs["package"],
                    ),
                    evidence_boundary_assessments=tuple(
                        EngineeringEvidenceBoundaryAssessment.create(
                            challenge_id=item.challenge_id,
                            evidence_boundary=(
                                "The current evidence cannot satisfy the literal user goal."
                            ),
                            draft_scope=(
                                "The Draft omits a material requirement of that goal."
                            ),
                            disposition=(
                                EngineeringEvidenceBoundaryAssessmentDisposition.DRAFT_OMITS_MATERIAL_REQUIREMENT
                            ),
                            finding_code=finding.finding_code,
                        )
                        for item in challenges
                    ),
                    findings=(finding,),
                )

        profile = source_profile()
        service = EngineeringQuestionAnsweringService(
            question_understanding_role=UnderstandingRole(),
            cognition_projector=CognitionProjector(),
            initial_investigation_role=InitialInvestigator(),
            verification_investigation_role=VerificationInvestigator(),
            source_broker=SourceBroker(source_profile=profile),
            retrieval_worker=ScriptedWorker(),
            answer_role=AnswerRole(),
            reviewer_role=ChallengeRejectingReviewer(),
        )

        result = service.answer(request())

        self.assertEqual(
            result.status,
            EngineeringQuestionResultStatus.FAILED_CLOSED,
        )
        self.assertEqual(result.terminal_reason, "REVIEW_REJECTED")
        self.assertIsNone(result.authorized_answer)
        self.assertEqual(
            [review.focus for review in result.reviews],
            [
                EngineeringReviewFocus.COMPREHENSIVE,
                EngineeringReviewFocus.EVIDENCE_BOUNDARY_CHALLENGE,
            ],
        )

    def test_original_question_fulfillment_scan_rewrites_component_inventory(self):
        class InventoryThenActionableAnswer:
            def __init__(self):
                self.calls = 0

            def generate(self, **kwargs):
                self.calls += 1
                if self.calls > 1:
                    return AnswerRole().generate(**kwargs)
                package = kwargs["package"]
                observation_ids = tuple(
                    observation.observation_id
                    for disposition in package.checklist_dispositions
                    for observation in disposition.material_observations
                )
                return EngineeringAnswerProposal.create(
                    role_context_id=kwargs["role_context_id"],
                    package_digest=package.digest,
                    response_language=kwargs["understanding"].response_language,
                    claims=(
                        EngineeringAnswerClaimProposal.create(
                            claim_id="claim-1",
                            kind=AnswerClaimKind.AFFIRMATIVE,
                            content_role=AnswerContentRole.DIRECT_ANSWER,
                            checklist_item_ids=("check-1",),
                            material_observation_ids=observation_ids,
                            text=(
                                "The service has a startup entry point and uses "
                                "repository configuration."
                            ),
                            evidence_entry_ids=tuple(
                                item.entry_id for item in package.support_citation
                            ),
                        ),
                    ),
                )

        class FulfillmentReviewer:
            def __init__(self):
                self.challenge_calls = 0

            def review(
                self,
                *,
                original_question,
                understanding,
                package,
                draft,
                role_context_id,
                review_focus=EngineeringReviewFocus.COMPREHENSIVE,
            ):
                if review_focus is EngineeringReviewFocus.COMPREHENSIVE:
                    return EngineeringReviewProposal.create(
                        role_context_id=role_context_id,
                        package_digest=package.digest,
                        draft_digest=draft.digest,
                        decision=EngineeringReviewDecision.APPROVED,
                        quality_assessment=passing_quality(),
                        checklist_assessment=matching_review_checklist(
                            understanding, package
                        ),
                    )
                self.challenge_calls += 1
                challenges = project_evidence_boundary_challenges(package, draft)
                fulfillment = next(
                    item
                    for item in challenges
                    if item.kind
                    is EngineeringEvidenceBoundaryChallengeKind.ORIGINAL_QUESTION_FULFILLMENT_SCAN
                )
                if self.challenge_calls == 1:
                    finding = EngineeringReviewFinding.create(
                        finding_code="USER_ACTION_SEQUENCE_OMITTED",
                        checklist_item_id="check-1",
                        claim_id=fulfillment.claim_ids[0],
                        description=(
                            "The Draft lists participating concepts but does not "
                            "tell the user how to start the service or apply the control."
                        ),
                        remediation=(
                            EngineeringReviewRemediation.REWRITE_WITH_EXISTING_EVIDENCE
                        ),
                        existing_evidence_entry_ids=tuple(
                            item.entry_id for item in package.support_citation
                        ),
                    )
                    quality = EngineeringReviewQualityAssessment.create(
                        direct_answer=EngineeringReviewQualityStatus.PASS,
                        abstraction_fit=EngineeringReviewQualityStatus.PASS,
                        material_completeness=EngineeringReviewQualityStatus.FAIL,
                        claim_consistency=EngineeringReviewQualityStatus.PASS,
                        implementation_detail_budget=(
                            EngineeringReviewQualityStatus.PASS
                        ),
                    )
                    return EngineeringReviewProposal.create_from_findings(
                        role_context_id=role_context_id,
                        package_digest=package.digest,
                        draft_digest=draft.digest,
                        quality_assessment=quality,
                        checklist_assessment=matching_review_checklist(
                            understanding, package
                        ),
                        evidence_boundary_assessments=tuple(
                            EngineeringEvidenceBoundaryAssessment.create(
                                challenge_id=item.challenge_id,
                                evidence_boundary=(
                                    "The Package supports the requested user action."
                                ),
                                draft_scope=(
                                    "The Draft omits the executable action sequence."
                                    if item is fulfillment
                                    else "The Draft stays within the cited evidence."
                                ),
                                disposition=(
                                    EngineeringEvidenceBoundaryAssessmentDisposition.DRAFT_OMITS_MATERIAL_REQUIREMENT
                                    if item is fulfillment
                                    else EngineeringEvidenceBoundaryAssessmentDisposition.WITHIN_EVIDENCE_BOUNDARY
                                ),
                                finding_code=(
                                    finding.finding_code
                                    if item is fulfillment
                                    else None
                                ),
                            )
                            for item in challenges
                        ),
                        findings=(finding,),
                    )
                return EngineeringReviewProposal.create(
                    role_context_id=role_context_id,
                    package_digest=package.digest,
                    draft_digest=draft.digest,
                    decision=EngineeringReviewDecision.APPROVED,
                    quality_assessment=passing_quality(),
                    checklist_assessment=matching_review_checklist(
                        understanding, package
                    ),
                    evidence_boundary_assessments=tuple(
                        EngineeringEvidenceBoundaryAssessment.create(
                            challenge_id=item.challenge_id,
                            evidence_boundary=(
                                "The Package supports the requested user action."
                            ),
                            draft_scope=(
                                "The Draft now states the executable user action."
                            ),
                            disposition=(
                                EngineeringEvidenceBoundaryAssessmentDisposition.WITHIN_EVIDENCE_BOUNDARY
                            ),
                            finding_code=None,
                        )
                        for item in challenges
                    ),
                )

        answer = InventoryThenActionableAnswer()
        service = EngineeringQuestionAnsweringService(
            question_understanding_role=UnderstandingRole(),
            cognition_projector=CognitionProjector(),
            initial_investigation_role=InitialInvestigator(),
            verification_investigation_role=VerificationInvestigator(),
            source_broker=SourceBroker(source_profile=source_profile()),
            retrieval_worker=ScriptedWorker(),
            answer_role=answer,
            reviewer_role=FulfillmentReviewer(),
        )

        result = service.answer(request())

        self.assertEqual(result.status, EngineeringQuestionResultStatus.APPROVED)
        self.assertEqual(answer.calls, 2)
        self.assertEqual(len(result.packages), 1)
        self.assertEqual(result.usage.verification_investigations, 0)
        first_challenge = result.reviews[1]
        fulfillment_assessment = next(
            item
            for item in first_challenge.evidence_boundary_assessments
            if item.disposition
            is EngineeringEvidenceBoundaryAssessmentDisposition.DRAFT_OMITS_MATERIAL_REQUIREMENT
        )
        self.assertEqual(
            fulfillment_assessment.finding_code,
            "USER_ACTION_SEQUENCE_OMITTED",
        )
        self.assertIn("Start the service", result.authorized_answer.body)

    def test_non_supported_finish_reopens_untried_required_source_class(self):
        class PrematureFinishInvestigator:
            closure_state = None
            path_gap = None

            def propose(self, investigation_input):
                if investigation_input.step_index == 1:
                    return step_proposal(
                        investigation_input,
                        operation=InvestigationOperation.SEARCH,
                        evidence_class=EngineeringEvidenceClass.REPOSITORY_DOCUMENT,
                        query="start",
                    )
                if investigation_input.step_index in {2, 4}:
                    boundary = (
                        investigation_input.disposition_reference_eligibility
                        .boundary_references[0]
                    )
                    disposition = ChecklistDisposition.create(
                        checklist_item_id="check-1",
                        outcome=ChecklistOutcome.UNKNOWN,
                        evidence_references=(boundary,),
                        explanation="The repository document lacks the behavior.",
                        material_observations=(
                            MaterialObservation.create(
                                checklist_item_id="check-1",
                                kind=MaterialObservationKind.LIMITATION,
                                statement=(
                                    "The repository document does not establish "
                                    "the behavior."
                                ),
                                evidence_references=(boundary,),
                            ),
                        ),
                    )
                    ledger = investigation_input.ledger
                    return InvestigationStepProposal.create(
                        investigation_kind=InvestigationKind.INITIAL,
                        attempt_id=investigation_input.attempt_id,
                        role_context_id=investigation_input.role_context_id,
                        request_digest=investigation_input.request.digest,
                        step_index=investigation_input.step_index,
                        ledger_id=ledger.ledger_id,
                        ledger_generation=ledger.generation,
                        ledger_revision=len(ledger.entries),
                        ledger_prefix_digest=ledger.prefix_digest,
                        operation=InvestigationOperation.FINISH,
                        checklist_item_ids=("check-1",),
                        basis_entry_ids=(ledger.entries[-1].entry_id,),
                        unknown_to_reduce="No repository-document detail was found.",
                        finish_dispositions=(disposition,),
                    )
                if investigation_input.step_index == 3:
                    self.path_gap = investigation_input.ledger.entries[-1]
                    locator = (
                        investigation_input.retrieval_results[0]
                        .items[0]
                        .locator_reference
                    )
                    return step_proposal(
                        investigation_input,
                        operation=InvestigationOperation.READ,
                        evidence_class=EngineeringEvidenceClass.REPOSITORY_DOCUMENT,
                        locator_reference=locator,
                    )
                if investigation_input.step_index == 5:
                    self.closure_state = (
                        investigation_input.registered_evidence_classes,
                        investigation_input.required_evidence_classes,
                        investigation_input.investigated_evidence_classes,
                        investigation_input.untried_required_evidence_classes,
                        investigation_input.ledger.entries[-1],
                    )
                    return step_proposal(
                        investigation_input,
                        operation=InvestigationOperation.SEARCH,
                        evidence_class=EngineeringEvidenceClass.SOURCE,
                        query="start",
                    )
                if investigation_input.step_index == 6:
                    locator = (
                        investigation_input.retrieval_results[-1]
                        .items[0]
                        .locator_reference
                    )
                    return step_proposal(
                        investigation_input,
                        operation=InvestigationOperation.READ,
                        evidence_class=EngineeringEvidenceClass.SOURCE,
                        locator_reference=locator,
                    )
                evidence = (
                    investigation_input.retrieval_results[-1].items[0].item_id.value
                )
                return step_proposal(
                    investigation_input,
                    operation=InvestigationOperation.FINISH,
                    evidence_reference=evidence,
                )

        class SourceAwareWorker:
            def execute(self, operation):
                if operation.operation is SourceReadOperation.SEARCH:
                    path = (
                        "README.md"
                        if operation.evidence_class
                        is EngineeringEvidenceClass.REPOSITORY_DOCUMENT
                        else "src/Service.java"
                    )
                    item = RetrievalItem.create(
                        operation_id=operation.operation_id,
                        ordinal=1,
                        evidence_class=operation.evidence_class,
                        path=path,
                        line_start=1,
                        line_end=1,
                        content=(
                            "JWT is supported."
                            if path == "README.md"
                            else (
                                "Start through the documented entry point; "
                                "write a PID file and apply the timeout."
                            )
                        ),
                        modality=operation.result_modality,
                        coverage_complete=True,
                    )
                else:
                    item = RetrievalItem.create(
                        operation_id=operation.operation_id,
                        ordinal=1,
                        evidence_class=operation.evidence_class,
                        path=operation.path,
                        content=(
                            "Start through the documented entry point; "
                            "write a PID file and apply the timeout."
                        ),
                        modality=operation.result_modality,
                        coverage_complete=True,
                    )
                return RetrievalResult.create(
                    operation=operation,
                    status=RetrievalStatus.COMPLETE,
                    items=(item,),
                    bytes_read=len(item.content.encode()),
                    files_read=1,
                    truncated=False,
                    coverage={"complete": "true"},
                )

        investigator = PrematureFinishInvestigator()
        profile = source_profile()
        service = EngineeringQuestionAnsweringService(
            question_understanding_role=UnderstandingRole(),
            cognition_projector=CognitionProjector(),
            initial_investigation_role=investigator,
            verification_investigation_role=VerificationInvestigator(),
            source_broker=SourceBroker(source_profile=profile),
            retrieval_worker=SourceAwareWorker(),
            answer_role=AnswerRole(),
            reviewer_role=ReviewerRole(request_more_evidence=False),
        )

        result = service.answer(request())

        self.assertEqual(result.status, EngineeringQuestionResultStatus.APPROVED)
        self.assertEqual(investigator.path_gap.kind, LedgerEntryKind.GAP)
        self.assertEqual(
            dict(investigator.path_gap.details)["reason"],
            "FINISH_REQUIRES_DECLARED_EVIDENCE_PATH",
        )
        self.assertEqual(
            dict(investigator.path_gap.details)["required_evidence_path"],
            "README.md",
        )
        registered, required, investigated, untried, gap = investigator.closure_state
        self.assertEqual(
            registered,
            (
                EngineeringEvidenceClass.SOURCE,
                EngineeringEvidenceClass.REPOSITORY_DOCUMENT,
                EngineeringEvidenceClass.BUILD_CONFIGURATION,
                EngineeringEvidenceClass.TEST,
            ),
        )
        self.assertEqual(
            required,
            (
                EngineeringEvidenceClass.REPOSITORY_DOCUMENT,
                EngineeringEvidenceClass.SOURCE,
            ),
        )
        self.assertEqual(
            investigated,
            (EngineeringEvidenceClass.REPOSITORY_DOCUMENT,),
        )
        self.assertEqual(
            untried,
            (EngineeringEvidenceClass.SOURCE,),
        )
        self.assertEqual(gap.kind, LedgerEntryKind.GAP)
        self.assertEqual(dict(gap.details)["evidence_class"], "SOURCE")
        self.assertEqual(
            dict(gap.details)["reason"],
            "NON_SUPPORTED_FINISH_REQUIRES_DECLARED_EVIDENCE_CLASS",
        )
        self.assertEqual(result.usage.investigation_role_calls, 7)
        self.assertEqual(result.usage.source_operations, 4)

    def test_supported_finish_reopens_unread_required_delegate_path(self):
        class DelegateUnderstandingRole:
            def understand(self, *, request, role_context_id):
                return QuestionUnderstandingProposal.create(
                    role_context_id=role_context_id,
                    request_digest=request.digest,
                    preserved_original_question=request.original_question,
                    user_goal="Trace the delegated decision behavior.",
                    audience="maintainer",
                    requested_abstraction_level=(
                        AnswerDetailLevel.USER_VISIBLE_EXPLANATION
                    ),
                    material_conclusions=(
                        "Explain the delegated decision and its outcome.",
                    ),
                    evidence_needs=(
                        "The caller wiring and delegated implementation behavior.",
                    ),
                    required_evidence_classes=(EngineeringEvidenceClass.SOURCE,),
                    required_evidence_paths=("src/Delegate.java",),
                    response_language=request.response_language,
                )

        class PrematureSupportedInvestigator:
            path_gap = None
            eligible_locator_references = ()
            caller_locator = None
            delegate_locator = None

            def propose(self, investigation_input):
                if investigation_input.step_index == 1:
                    return step_proposal(
                        investigation_input,
                        operation=InvestigationOperation.SEARCH,
                        evidence_class=EngineeringEvidenceClass.SOURCE,
                        query="Delegate",
                    )
                if investigation_input.step_index == 2:
                    caller = next(
                        item
                        for item in investigation_input.retrieval_results[0].items
                        if item.path == "src/Caller.java"
                    )
                    delegate = next(
                        item
                        for item in investigation_input.retrieval_results[0].items
                        if item.path == "src/Delegate.java"
                    )
                    self.eligible_locator_references = (
                        investigation_input.eligible_locator_references
                    )
                    self.caller_locator = caller.locator_reference
                    self.delegate_locator = delegate.locator_reference
                    return step_proposal(
                        investigation_input,
                        operation=InvestigationOperation.FINISH,
                        evidence_reference=(
                            investigation_input.disposition_reference_eligibility
                            .support_references[0]
                        ),
                    )
                if investigation_input.step_index == 3:
                    self.path_gap = investigation_input.ledger.entries[-1]
                    delegate = next(
                        item
                        for item in investigation_input.retrieval_results[0].items
                        if item.path == "src/Delegate.java"
                    )
                    return step_proposal(
                        investigation_input,
                        operation=InvestigationOperation.READ,
                        evidence_class=EngineeringEvidenceClass.SOURCE,
                        locator_reference=delegate.locator_reference,
                    )
                evidence = (
                    investigation_input.retrieval_results[-1].items[0].item_id.value
                )
                return step_proposal(
                    investigation_input,
                    operation=InvestigationOperation.FINISH,
                    evidence_reference=evidence,
                )

        class DelegateWorker:
            def execute(self, operation):
                if operation.operation is SourceReadOperation.SEARCH:
                    paths = ("src/Caller.java", "src/Delegate.java")
                    items = tuple(
                        RetrievalItem.create(
                            operation_id=operation.operation_id,
                            ordinal=index,
                            evidence_class=operation.evidence_class,
                            path=path,
                            line_start=1,
                            line_end=1,
                            content=(
                                "Caller selects Delegate."
                                if path == "src/Caller.java"
                                else "Delegate compares authorities and denies a mismatch."
                            ),
                            modality=operation.result_modality,
                            coverage_complete=True,
                        )
                        for index, path in enumerate(paths, 1)
                    )
                else:
                    content = (
                        "Caller selects Delegate."
                        if operation.path == "src/Caller.java"
                        else "Delegate compares authorities and denies a mismatch."
                    )
                    items = (
                        RetrievalItem.create(
                            operation_id=operation.operation_id,
                            ordinal=1,
                            evidence_class=operation.evidence_class,
                            path=operation.path,
                            content=content,
                            modality=operation.result_modality,
                            coverage_complete=True,
                        ),
                    )
                return RetrievalResult.create(
                    operation=operation,
                    status=RetrievalStatus.COMPLETE,
                    items=items,
                    bytes_read=sum(len(item.content.encode()) for item in items),
                    files_read=len(items),
                    truncated=False,
                    coverage={"complete": "true"},
                )

        investigator = PrematureSupportedInvestigator()
        service = EngineeringQuestionAnsweringService(
            question_understanding_role=DelegateUnderstandingRole(),
            cognition_projector=CognitionProjector(),
            initial_investigation_role=investigator,
            verification_investigation_role=VerificationInvestigator(),
            source_broker=SourceBroker(source_profile=source_profile()),
            retrieval_worker=DelegateWorker(),
            answer_role=AnswerRole(),
            reviewer_role=ReviewerRole(request_more_evidence=False),
        )

        result = service.answer(request())

        self.assertEqual(result.status, EngineeringQuestionResultStatus.APPROVED)
        self.assertEqual(investigator.path_gap.kind, LedgerEntryKind.GAP)
        self.assertEqual(
            dict(investigator.path_gap.details)["reason"],
            "FINISH_REQUIRES_DECLARED_EVIDENCE_PATH",
        )
        self.assertEqual(
            dict(investigator.path_gap.details)["required_evidence_path"],
            "src/Delegate.java",
        )
        self.assertNotIn(
            investigator.caller_locator,
            investigator.eligible_locator_references,
        )
        self.assertIn(
            investigator.delegate_locator,
            investigator.eligible_locator_references,
        )
        self.assertEqual(result.usage.investigation_role_calls, 4)
        self.assertEqual(result.usage.source_operations, 2)

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
        self.assertEqual(len(result.reviews), 3)
        self.assertEqual(
            [review.focus for review in result.reviews],
            [
                EngineeringReviewFocus.COMPREHENSIVE,
                EngineeringReviewFocus.COMPREHENSIVE,
                EngineeringReviewFocus.EVIDENCE_BOUNDARY_CHALLENGE,
            ],
        )
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
                item.kind is PackageBoundaryKind.VERIFICATION_GAP
                for item in second.boundary_audit
            )
        )

    def test_material_effect_scan_can_add_missing_observation_in_successor(self):
        effect_statement = "The login helper persists an administrator login audit record."

        class EffectUnderstandingRole:
            def understand(self, *, request, role_context_id):
                return QuestionUnderstandingProposal.create(
                    role_context_id=role_context_id,
                    request_digest=request.digest,
                    preserved_original_question=request.original_question,
                    user_goal="Trace the complete login flow and its material effects.",
                    audience="maintainer",
                    requested_abstraction_level=(
                        AnswerDetailLevel.IMPLEMENTATION_DETAIL
                    ),
                    material_conclusions=(
                        "Explain the login flow and every material effect.",
                    ),
                    evidence_needs=(
                        "The complete implementation and its visible helper effects.",
                    ),
                    required_evidence_classes=(EngineeringEvidenceClass.SOURCE,),
                    required_evidence_paths=("src/Service.java",),
                    response_language=request.response_language,
                )

        class EffectInitialInvestigator:
            def propose(self, investigation_input):
                if investigation_input.step_index == 1:
                    return step_proposal(
                        investigation_input,
                        operation=InvestigationOperation.SEARCH,
                        evidence_class=EngineeringEvidenceClass.SOURCE,
                        query="login audit persistence",
                    )
                if investigation_input.step_index == 2:
                    return step_proposal(
                        investigation_input,
                        operation=InvestigationOperation.READ,
                        evidence_class=EngineeringEvidenceClass.SOURCE,
                        locator_reference=(
                            investigation_input.eligible_locator_references[0]
                        ),
                    )
                evidence = (
                    investigation_input.retrieval_results[-1].items[0].item_id.value
                )
                ledger = investigation_input.ledger
                disposition = ChecklistDisposition.create(
                    checklist_item_id="check-1",
                    outcome=ChecklistOutcome.SUPPORTED,
                    evidence_references=(evidence,),
                    explanation="The implementation establishes the login stage.",
                    material_observations=(
                        MaterialObservation.create(
                            checklist_item_id="check-1",
                            kind=MaterialObservationKind.PROCESS_STAGE,
                            statement="The service validates the administrator login.",
                            evidence_references=(evidence,),
                        ),
                    ),
                )
                return InvestigationStepProposal.create(
                    investigation_kind=InvestigationKind.INITIAL,
                    attempt_id=investigation_input.attempt_id,
                    role_context_id=investigation_input.role_context_id,
                    request_digest=investigation_input.request.digest,
                    step_index=investigation_input.step_index,
                    ledger_id=ledger.ledger_id,
                    ledger_generation=ledger.generation,
                    ledger_revision=len(ledger.entries),
                    ledger_prefix_digest=ledger.prefix_digest,
                    operation=InvestigationOperation.FINISH,
                    checklist_item_ids=("check-1",),
                    basis_entry_ids=(ledger.entries[-1].entry_id,),
                    unknown_to_reduce="The initial login evidence is dispositioned.",
                    finish_dispositions=(disposition,),
                )

        class EffectVerificationInvestigator:
            def propose(self, investigation_input):
                evidence = next(
                    item.source_reference
                    for item in investigation_input.current_package.support_citation
                    if item.locator == "src/Service.java"
                )
                ledger = investigation_input.ledger
                disposition = ChecklistDisposition.create(
                    checklist_item_id=(
                        investigation_input.verification_request.checklist_item_id
                    ),
                    outcome=ChecklistOutcome.SUPPORTED,
                    evidence_references=(evidence,),
                    explanation=(
                        "The retained full implementation supports both the flow "
                        "and the previously omitted effect."
                    ),
                    material_observations=(
                        MaterialObservation.create(
                            checklist_item_id="check-1",
                            kind=MaterialObservationKind.PROCESS_STAGE,
                            statement="The service validates the administrator login.",
                            evidence_references=(evidence,),
                        ),
                        MaterialObservation.create(
                            checklist_item_id="check-1",
                            kind=MaterialObservationKind.SIDE_EFFECT,
                            statement=effect_statement,
                            evidence_references=(evidence,),
                        ),
                    ),
                )
                return InvestigationStepProposal.create(
                    investigation_kind=InvestigationKind.VERIFICATION,
                    attempt_id=investigation_input.attempt_id,
                    role_context_id=investigation_input.role_context_id,
                    request_digest=(
                        investigation_input.current_package.request_digest
                    ),
                    step_index=investigation_input.step_index,
                    ledger_id=ledger.ledger_id,
                    ledger_generation=ledger.generation,
                    ledger_revision=len(ledger.entries),
                    ledger_prefix_digest=ledger.prefix_digest,
                    operation=InvestigationOperation.FINISH,
                    checklist_item_ids=("check-1",),
                    basis_entry_ids=(ledger.entries[-1].entry_id,),
                    unknown_to_reduce=(
                        "The missing material-effect observation is now explicit."
                    ),
                    finish_dispositions=(disposition,),
                )

        class EffectWorker:
            content = """\
class Service {
  void login(String username) {
    validate(username);
    insertLoginLog(username);
  }
  void insertLoginLog(String username) {
    loginLogMapper.insert(username);
  }
}
"""

            def execute(self, operation):
                is_search = operation.operation is SourceReadOperation.SEARCH
                item = RetrievalItem.create(
                    operation_id=operation.operation_id,
                    ordinal=1,
                    evidence_class=operation.evidence_class,
                    path="src/Service.java",
                    line_start=1 if is_search else None,
                    line_end=4 if is_search else None,
                    content=self.content,
                    modality=operation.result_modality,
                    coverage_complete=not is_search,
                )
                return RetrievalResult.create(
                    operation=operation,
                    status=RetrievalStatus.COMPLETE,
                    items=(item,),
                    bytes_read=len(self.content.encode()),
                    files_read=1,
                    truncated=False,
                    coverage={"complete": "true"},
                )

        class ObservationAnswerRole:
            def generate(
                self,
                *,
                original_question,
                understanding,
                package,
                role_context_id,
                rewrite_findings=(),
            ):
                observations = tuple(
                    observation
                    for disposition in package.checklist_dispositions
                    for observation in disposition.material_observations
                )
                return EngineeringAnswerProposal.create(
                    role_context_id=role_context_id,
                    package_digest=package.digest,
                    response_language=understanding.response_language,
                    claims=(
                        EngineeringAnswerClaimProposal.create(
                            claim_id="claim-1",
                            kind=AnswerClaimKind.AFFIRMATIVE,
                            content_role=AnswerContentRole.DIRECT_ANSWER,
                            checklist_item_ids=("check-1",),
                            material_observation_ids=tuple(
                                item.observation_id for item in observations
                            ),
                            text=" ".join(item.statement for item in observations),
                            evidence_entry_ids=tuple(
                                item.entry_id for item in package.support_citation
                            ),
                        ),
                    ),
                )

        class EffectReviewer:
            def __init__(self):
                self.challenge_calls = 0

            def review(
                self,
                *,
                original_question,
                understanding,
                package,
                draft,
                role_context_id,
                review_focus=EngineeringReviewFocus.COMPREHENSIVE,
            ):
                if review_focus is EngineeringReviewFocus.COMPREHENSIVE:
                    return EngineeringReviewProposal.create(
                        role_context_id=role_context_id,
                        package_digest=package.digest,
                        draft_digest=draft.digest,
                        decision=EngineeringReviewDecision.APPROVED,
                        quality_assessment=passing_quality(),
                        checklist_assessment=matching_review_checklist(
                            understanding,
                            package,
                        ),
                    )
                self.challenge_calls += 1
                challenges = project_evidence_boundary_challenges(package, draft)
                if self.challenge_calls == 1:
                    effect_challenge = next(
                        item
                        for item in challenges
                        if item.kind
                        is EngineeringEvidenceBoundaryChallengeKind.FULL_CONTENT_MATERIAL_EFFECT_SCAN
                    )
                    finding = EngineeringReviewFinding.create(
                        finding_code="LOGIN_AUDIT_EFFECT_OBSERVATION_MISSING",
                        checklist_item_id="check-1",
                        claim_id=effect_challenge.claim_ids[0],
                        description=(
                            "The complete implementation persists a login audit "
                            "record that the Package and Draft omit."
                        ),
                        remediation=(
                            EngineeringReviewRemediation.INVESTIGATE_MISSING_EVIDENCE
                        ),
                        evidence_class=EngineeringEvidenceClass.SOURCE,
                        evidence_need=(
                            "A typed observation for the retained implementation's "
                            "administrator login audit persistence"
                        ),
                    )
                    assessments = tuple(
                        EngineeringEvidenceBoundaryAssessment.create(
                            challenge_id=item.challenge_id,
                            evidence_boundary=(
                                "The full implementation persists a login audit "
                                "record through its visible helper."
                                if item is effect_challenge
                                else "The Draft stays within the cited evidence."
                            ),
                            draft_scope=(
                                "The Draft omits that persistence effect."
                                if item is effect_challenge
                                else "The Draft stays within the cited evidence."
                            ),
                            disposition=(
                                EngineeringEvidenceBoundaryAssessmentDisposition.DRAFT_OMITS_MATERIAL_EFFECT
                                if item is effect_challenge
                                else EngineeringEvidenceBoundaryAssessmentDisposition.WITHIN_EVIDENCE_BOUNDARY
                            ),
                            finding_code=(
                                finding.finding_code
                                if item is effect_challenge
                                else None
                            ),
                            material_effect_omission_layer=(
                                EngineeringMaterialEffectOmissionLayer.APPLICATION_PACKAGE
                                if item is effect_challenge
                                else None
                            ),
                            omitted_material_effect_statements=(
                                (effect_statement,)
                                if item is effect_challenge
                                else ()
                            ),
                        )
                        for item in challenges
                    )
                    base = matching_review_checklist(understanding, package)
                    checklist = EngineeringReviewChecklistAssessment.create(
                        independent_material_conclusions=(
                            base.independent_material_conclusions
                        ),
                        application_checklist_omissions=(),
                        independent_material_observations=(
                            *base.independent_material_observations,
                            EngineeringReviewMaterialObservation.create(
                                checklist_item_id="check-1",
                                kind=MaterialObservationKind.SIDE_EFFECT,
                                statement=effect_statement,
                                evidence_entry_ids=(
                                    effect_challenge.package_entry_ids[0],
                                ),
                            ),
                        ),
                        application_material_observation_omissions=(
                            effect_statement,
                        ),
                        draft_material_observation_omissions=(effect_statement,),
                    )
                    quality = EngineeringReviewQualityAssessment.create(
                        direct_answer=EngineeringReviewQualityStatus.PASS,
                        abstraction_fit=EngineeringReviewQualityStatus.PASS,
                        material_completeness=EngineeringReviewQualityStatus.FAIL,
                        claim_consistency=EngineeringReviewQualityStatus.PASS,
                        implementation_detail_budget=(
                            EngineeringReviewQualityStatus.PASS
                        ),
                    )
                    return EngineeringReviewProposal.create_from_findings(
                        role_context_id=role_context_id,
                        package_digest=package.digest,
                        draft_digest=draft.digest,
                        quality_assessment=quality,
                        checklist_assessment=checklist,
                        evidence_boundary_assessments=assessments,
                        findings=(finding,),
                    )
                return EngineeringReviewProposal.create(
                    role_context_id=role_context_id,
                    package_digest=package.digest,
                    draft_digest=draft.digest,
                    decision=EngineeringReviewDecision.APPROVED,
                    quality_assessment=passing_quality(),
                    checklist_assessment=matching_review_checklist(
                        understanding,
                        package,
                    ),
                    evidence_boundary_assessments=tuple(
                        EngineeringEvidenceBoundaryAssessment.create(
                            challenge_id=item.challenge_id,
                            evidence_boundary=(
                                "Every material effect in the full entry is now "
                                "represented by a Package observation."
                            ),
                            draft_scope=(
                                "The Draft states every Package material observation."
                            ),
                            disposition=(
                                EngineeringEvidenceBoundaryAssessmentDisposition.WITHIN_EVIDENCE_BOUNDARY
                            ),
                            finding_code=None,
                        )
                        for item in challenges
                    ),
                )

        reviewer = EffectReviewer()
        service = EngineeringQuestionAnsweringService(
            question_understanding_role=EffectUnderstandingRole(),
            cognition_projector=CognitionProjector(),
            initial_investigation_role=EffectInitialInvestigator(),
            verification_investigation_role=EffectVerificationInvestigator(),
            source_broker=SourceBroker(source_profile=source_profile()),
            retrieval_worker=EffectWorker(),
            answer_role=ObservationAnswerRole(),
            reviewer_role=reviewer,
        )

        result = service.answer(request())

        self.assertEqual(result.status, EngineeringQuestionResultStatus.APPROVED)
        self.assertEqual(len(result.packages), 2)
        first, second = result.packages
        self.assertEqual(
            len(first.checklist_dispositions[0].material_observations),
            1,
        )
        successor_observations = (
            second.checklist_dispositions[0].material_observations
        )
        self.assertEqual(len(successor_observations), 2)
        self.assertIn(
            effect_statement,
            tuple(item.statement for item in successor_observations),
        )
        first_challenge_review = result.reviews[1]
        self.assertEqual(
            first_challenge_review.decision,
            EngineeringReviewDecision.MORE_EVIDENCE_REQUIRED,
        )
        self.assertEqual(
            first_challenge_review.evidence_boundary_assessments[0].disposition,
            EngineeringEvidenceBoundaryAssessmentDisposition.DRAFT_OMITS_MATERIAL_EFFECT,
        )
        self.assertEqual(
            first_challenge_review.verification_request.evidence_class,
            EngineeringEvidenceClass.SOURCE,
        )
        self.assertEqual(result.usage.verification_investigations, 1)
        self.assertEqual(result.usage.source_operations, 2)
        self.assertIn(effect_statement, result.authorized_answer.body)

    def test_verification_finish_delta_replaces_only_authorized_gap(self):
        package = self.service(request_more_evidence=False).answer(
            request()
        ).current_package
        first = package.checklist_dispositions[0]
        second = ChecklistDisposition.create(
            checklist_item_id="check-2",
            outcome=first.outcome,
            evidence_references=first.evidence_references,
            explanation="The predecessor has a separate retained conclusion.",
            material_observations=(
                MaterialObservation.create(
                    checklist_item_id="check-2",
                    kind=MaterialObservationKind.OUTCOME,
                    statement="The predecessor retains a separate outcome.",
                    evidence_references=first.evidence_references,
                ),
            ),
        )
        package = replace(
            package,
            checklist_dispositions=(first, second),
            digest=Digest("sha256:" + "d" * 64),
        )
        verification = VerificationRequestProposal.create(
            package_digest=package.digest,
            checklist_item_id="check-2",
            evidence_class=EngineeringEvidenceClass.SOURCE,
            evidence_need="Exact implementation for the second conclusion",
        )
        replacement = ChecklistDisposition.create(
            checklist_item_id="check-2",
            outcome=ChecklistOutcome.SUPPORTED,
            evidence_references=first.evidence_references,
            explanation="The verification evidence resolves the second conclusion.",
            material_observations=(
                MaterialObservation.create(
                    checklist_item_id="check-2",
                    kind=MaterialObservationKind.OUTCOME,
                    statement="The verification evidence establishes the second outcome.",
                    evidence_references=first.evidence_references,
                ),
            ),
        )

        merged = _merge_verification_checklist_dispositions(
            current_package=package,
            verification_request=verification,
            verification_dispositions=(replacement,),
        )

        self.assertEqual(merged, (first, replacement))
        self.assertIs(merged[0], first)
        with self.assertRaises(DomainError) as caught:
            _merge_verification_checklist_dispositions(
                current_package=package,
                verification_request=verification,
                verification_dispositions=(first, replacement),
            )
        self.assertEqual(caught.exception.code, ErrorCode.PROVIDER_RESPONSE_INVALID)

    def test_verification_finish_validates_only_gap_checklist_scope(self):
        req = request()
        context = sid("role_context", "c")
        understanding = QuestionUnderstanding.accept(
            request=req,
            expected_role_context_id=context,
            proposal=QuestionUnderstandingProposal.create(
                role_context_id=context,
                request_digest=req.digest,
                preserved_original_question=req.original_question,
                user_goal="Confirm two independently supportable conclusions.",
                audience="maintainer",
                requested_abstraction_level=(
                    AnswerDetailLevel.USER_VISIBLE_EXPLANATION
                ),
                material_conclusions=(
                    "Explain the documented startup path.",
                    "Explain the separate timeout behavior.",
                ),
                evidence_needs=("Exact repository evidence.",),
                required_evidence_classes=(
                    EngineeringEvidenceClass.REPOSITORY_DOCUMENT,
                ),
                required_evidence_paths=("README.md",),
                response_language=req.response_language,
            ),
        )
        cognition = CognitionProjector().project(request=req)
        ledger = EvidenceLedger.start(request=req, cognition=cognition)
        support_reference = cognition.items[0].item_id.value
        target = understanding.checklist[1].item_id
        disposition = ChecklistDisposition.create(
            checklist_item_id=target,
            outcome=ChecklistOutcome.SUPPORTED,
            evidence_references=(support_reference,),
            explanation="The gap is supported by the retained cognition evidence.",
            material_observations=(
                MaterialObservation.create(
                    checklist_item_id=target,
                    kind=MaterialObservationKind.OUTCOME,
                    statement="The retained evidence establishes the timeout behavior.",
                    evidence_references=(support_reference,),
                ),
            ),
        )
        attempt = sid("verification_attempt", "d")
        role_context = sid("role_context", "e")
        proposal = InvestigationStepProposal.create(
            investigation_kind=InvestigationKind.VERIFICATION,
            attempt_id=attempt,
            role_context_id=role_context,
            request_digest=req.digest,
            step_index=1,
            ledger_id=ledger.ledger_id,
            ledger_generation=ledger.generation,
            ledger_revision=len(ledger.entries),
            ledger_prefix_digest=ledger.prefix_digest,
            operation=InvestigationOperation.FINISH,
            checklist_item_ids=(target,),
            basis_entry_ids=(ledger.entries[-1].entry_id,),
            unknown_to_reduce="The authorized verification gap is resolved.",
            finish_dispositions=(disposition,),
        )

        EngineeringQuestionAnsweringService._validate_investigation_proposal(
            request=req,
            understanding=understanding,
            ledger=ledger,
            proposal=proposal,
            expected_kind=InvestigationKind.VERIFICATION,
            expected_attempt_id=attempt,
            expected_role_context_id=role_context,
            expected_step_index=1,
            eligible_locator_references=(),
            disposition_reference_eligibility=(
                # A verification delta may cite retained Package support.
                ChecklistDispositionReferenceEligibility.create(
                    support_references=(support_reference,),
                    boundary_references=(),
                )
            ),
            authorized_checklist_item_ids=(target,),
        )

        unauthorized = InvestigationStepProposal.create(
            investigation_kind=InvestigationKind.VERIFICATION,
            attempt_id=attempt,
            role_context_id=role_context,
            request_digest=req.digest,
            step_index=1,
            ledger_id=ledger.ledger_id,
            ledger_generation=ledger.generation,
            ledger_revision=len(ledger.entries),
            ledger_prefix_digest=ledger.prefix_digest,
            operation=InvestigationOperation.SEARCH,
            checklist_item_ids=(understanding.checklist[0].item_id,),
            evidence_class=EngineeringEvidenceClass.REPOSITORY_DOCUMENT,
            query="startup",
            basis_entry_ids=(ledger.entries[-1].entry_id,),
            unknown_to_reduce="Search outside the authorized verification gap.",
        )
        with self.assertRaises(DomainError) as caught:
            EngineeringQuestionAnsweringService._validate_investigation_proposal(
                request=req,
                understanding=understanding,
                ledger=ledger,
                proposal=unauthorized,
                expected_kind=InvestigationKind.VERIFICATION,
                expected_attempt_id=attempt,
                expected_role_context_id=role_context,
                expected_step_index=1,
                eligible_locator_references=(),
                disposition_reference_eligibility=(
                    ChecklistDispositionReferenceEligibility.create(
                        support_references=(support_reference,),
                        boundary_references=(),
                    )
                ),
                authorized_checklist_item_ids=(target,),
            )
        self.assertEqual(caught.exception.code, ErrorCode.PROVIDER_RESPONSE_INVALID)
        self.assertIn("authorized Checklist scope", caught.exception.message)

    def test_predecessor_package_full_read_blocks_verification_reread_locator(self):
        result = self.service(request_more_evidence=False).answer(request())
        search_result = result.retrieval_results[0]

        self.assertTrue(_eligible_locator_references((search_result,)))
        self.assertEqual(
            _eligible_locator_references(
                (search_result,),
                preconsumed_full_content_paths=("README.md",),
            ),
            (),
        )

    def test_verification_boundary_eligibility_excludes_predecessor_unknowns(self):
        result = self.service(request_more_evidence=False).answer(request())
        package = result.current_package
        verification = VerificationRequestProposal.create(
            package_digest=package.digest,
            checklist_item_id="check-1",
            evidence_class=EngineeringEvidenceClass.SOURCE,
            evidence_need="The exact downstream implementation outcome",
        )
        ledger = result.ledgers[-1].successor(
            verification_request_id=verification.verification_request_id,
            verification_request_digest=verification.digest,
            prior_package_digest=package.digest,
            maximum_bytes=result.request.limits.maximum_ledger_bytes,
        )

        eligibility = _verification_disposition_reference_eligibility(
            cognition=result.cognition,
            ledger=ledger,
            retrieval_results=result.retrieval_results,
            broker_decisions=result.broker_decisions,
            current_package=package,
        )

        gap_reference = ledger.entries[-1].entry_id.value
        self.assertIn(gap_reference, eligibility.boundary_references)
        self.assertFalse(
            set(eligibility.boundary_references).intersection(
                item.source_reference for item in package.boundary_audit
            )
        )
        investigation_input = VerificationInvestigationInput(
            attempt_id=sid("verification_attempt", "b"),
            role_context_id=sid("role_context", "c"),
            step_index=1,
            verification_request=verification,
            current_package=package,
            ledger=ledger,
            retrieval_results=(),
            disposition_reference_eligibility=eligibility,
            registered_evidence_classes=(EngineeringEvidenceClass.SOURCE,),
            required_evidence_classes=(EngineeringEvidenceClass.SOURCE,),
        )
        investigation_input.validate_new_result_closure()

        predecessor_reference = package.boundary_audit[0].source_reference
        with self.assertRaises(DomainError) as caught:
            replace(
                investigation_input,
                disposition_reference_eligibility=(
                    ChecklistDispositionReferenceEligibility.create(
                        support_references=eligibility.support_references,
                        boundary_references=(
                            gap_reference,
                            predecessor_reference,
                        ),
                    )
                ),
            ).validate_new_result_closure()
        self.assertEqual(
            caught.exception.code,
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
        )

    def test_non_supported_verification_finish_must_retain_gap_boundary(self):
        result = self.service(request_more_evidence=False).answer(request())
        package = result.current_package
        verification = VerificationRequestProposal.create(
            package_digest=package.digest,
            checklist_item_id="check-1",
            evidence_class=EngineeringEvidenceClass.SOURCE,
            evidence_need="The exact downstream implementation outcome",
        )
        ledger = result.ledgers[-1].successor(
            verification_request_id=verification.verification_request_id,
            verification_request_digest=verification.digest,
            prior_package_digest=package.digest,
            maximum_bytes=result.request.limits.maximum_ledger_bytes,
        )
        attempt = sid("verification_attempt", "d")
        role_context = sid("role_context", "e")
        predecessor_reference = package.boundary_audit[0].source_reference
        observation = MaterialObservation.create(
            checklist_item_id="check-1",
            kind=MaterialObservationKind.LIMITATION,
            statement="The downstream result remains unknown.",
            evidence_references=(predecessor_reference,),
        )
        disposition = ChecklistDisposition.create(
            checklist_item_id="check-1",
            outcome=ChecklistOutcome.UNKNOWN,
            evidence_references=(predecessor_reference,),
            explanation="The current gap was not resolved.",
            material_observations=(observation,),
        )
        proposal = InvestigationStepProposal.create(
            investigation_kind=InvestigationKind.VERIFICATION,
            attempt_id=attempt,
            role_context_id=role_context,
            request_digest=result.request.digest,
            step_index=1,
            ledger_id=ledger.ledger_id,
            ledger_generation=ledger.generation,
            ledger_revision=len(ledger.entries),
            ledger_prefix_digest=ledger.prefix_digest,
            operation=InvestigationOperation.FINISH,
            checklist_item_ids=("check-1",),
            basis_entry_ids=(ledger.entries[-1].entry_id,),
            unknown_to_reduce="The exact downstream implementation outcome",
            finish_dispositions=(disposition,),
        )

        with self.assertRaises(DomainError) as caught:
            EngineeringQuestionAnsweringService._validate_investigation_proposal(
                request=result.request,
                understanding=result.understanding,
                ledger=ledger,
                proposal=proposal,
                expected_kind=InvestigationKind.VERIFICATION,
                expected_attempt_id=attempt,
                expected_role_context_id=role_context,
                expected_step_index=1,
                eligible_locator_references=(),
                disposition_reference_eligibility=(
                    ChecklistDispositionReferenceEligibility.create(
                        support_references=(),
                        boundary_references=(
                            predecessor_reference,
                            ledger.entries[-1].entry_id.value,
                        ),
                    )
                ),
                authorized_checklist_item_ids=("check-1",),
            )
        self.assertEqual(caught.exception.code, ErrorCode.PROVIDER_RESPONSE_INVALID)
        self.assertIn("current gap boundary", caught.exception.message)

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

    def test_broker_authorizes_request_bound_required_path_locator_without_search(self):
        req = request()
        cognition = CognitionProjector().project(request=req)
        ledger = EvidenceLedger.start(request=req, cognition=cognition)
        broker = SourceBroker(source_profile=source_profile())
        locator = broker.issue_required_path_locators(
            request=req,
            attempt_id=sid("investigation_attempt", "9"),
            paths=("README.md",),
        )[0]
        input_stub = type(
            "InitialInput",
            (),
            {
                "ledger": ledger,
                "attempt_id": sid("investigation_attempt", "9"),
                "role_context_id": sid("role_context", "a"),
                "step_index": 1,
                "request": req,
            },
        )()
        proposal = step_proposal(
            input_stub,
            operation=InvestigationOperation.READ,
            evidence_class=EngineeringEvidenceClass.REPOSITORY_DOCUMENT,
            locator_reference=locator.locator_reference,
        )

        compilation = broker.compile(
            request=req,
            proposal=proposal,
            ledger=ledger,
            locator_catalog={},
            required_path_locator_catalog={locator.locator_reference: locator},
            usage=EngineeringQuestionResourceUsage(),
        )

        self.assertEqual(compilation.decision.status.value, "AUTHORIZED")
        self.assertIsNotNone(compilation.operation)
        self.assertEqual(compilation.operation.path, "README.md")
        self.assertEqual(
            compilation.operation.locator_reference,
            locator.locator_reference,
        )
        compilation.operation.validate_identity()

    def test_broker_rejects_required_path_locator_from_another_attempt(self):
        req = request()
        cognition = CognitionProjector().project(request=req)
        ledger = EvidenceLedger.start(request=req, cognition=cognition)
        broker = SourceBroker(source_profile=source_profile())
        locator = broker.issue_required_path_locators(
            request=req,
            attempt_id=sid("investigation_attempt", "9"),
            paths=("README.md",),
        )[0]
        input_stub = type(
            "InitialInput",
            (),
            {
                "ledger": ledger,
                "attempt_id": sid("investigation_attempt", "8"),
                "role_context_id": sid("role_context", "a"),
                "step_index": 1,
                "request": req,
            },
        )()
        proposal = step_proposal(
            input_stub,
            operation=InvestigationOperation.READ,
            evidence_class=EngineeringEvidenceClass.REPOSITORY_DOCUMENT,
            locator_reference=locator.locator_reference,
        )

        compilation = broker.compile(
            request=req,
            proposal=proposal,
            ledger=ledger,
            locator_catalog={},
            required_path_locator_catalog={locator.locator_reference: locator},
            usage=EngineeringQuestionResourceUsage(),
        )

        self.assertEqual(compilation.decision.status.value, "REJECTED")
        self.assertEqual(
            compilation.decision.reason_code,
            "REQUIRED_PATH_LOCATOR_BINDING_MISMATCH",
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

    def test_broker_rejects_duplicate_search_intent_before_worker_execution(self):
        req = request()
        cognition = CognitionProjector().project(request=req)
        ledger = EvidenceLedger.start(request=req, cognition=cognition)
        attempt_id = sid("investigation_attempt", "c")
        first_input = type(
            "InitialInput",
            (),
            {
                "ledger": ledger,
                "attempt_id": attempt_id,
                "role_context_id": sid("role_context", "d"),
                "step_index": 1,
                "request": req,
            },
        )()
        first = step_proposal(
            first_input,
            operation=InvestigationOperation.SEARCH,
            evidence_class=EngineeringEvidenceClass.SOURCE,
            query="mall-security",
        )
        ledger = ledger.append(
            kind=LedgerEntryKind.INVESTIGATION_PROPOSAL,
            subject_id=first.proposal_id.value,
            subject_digest=first.digest,
            references=tuple(item.value for item in first.basis_entry_ids),
            details={
                "investigation_kind": InvestigationKind.INITIAL.value,
                "attempt_id": attempt_id.value,
                "operation": first.operation.value,
                "step_index": "1",
                "evidence_class": first.evidence_class.value,
                "query": first.query,
            },
        )
        second_input = type(
            "InitialInput",
            (),
            {
                "ledger": ledger,
                "attempt_id": attempt_id,
                "role_context_id": sid("role_context", "e"),
                "step_index": 2,
                "request": req,
            },
        )()
        duplicate = step_proposal(
            second_input,
            operation=InvestigationOperation.SEARCH,
            evidence_class=EngineeringEvidenceClass.SOURCE,
            query="mall-security",
        )

        compilation = SourceBroker(source_profile=source_profile()).compile(
            request=req,
            proposal=duplicate,
            ledger=ledger,
            locator_catalog={},
            usage=EngineeringQuestionResourceUsage(),
        )

        self.assertEqual(compilation.decision.status.value, "REJECTED")
        self.assertEqual(
            compilation.decision.reason_code,
            "DUPLICATE_ACTION_INTENT",
        )
        self.assertIsNone(compilation.operation)

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

    def test_repeated_identical_intent_is_rejected_before_repeated_worker_reads(self):
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
        self.assertEqual(result.usage.source_operations, 1)
        self.assertEqual(len(result.broker_decisions), 3)
        self.assertEqual(
            [item.reason_code for item in result.broker_decisions[1:]],
            ["DUPLICATE_ACTION_INTENT", "DUPLICATE_ACTION_INTENT"],
        )
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

    def test_finish_cannot_cite_latest_ledger_result_as_support(self):
        class LedgerResultCitingInvestigator:
            def __init__(self):
                self.delegate = InitialInvestigator()

            def propose(self, investigation_input):
                proposal = self.delegate.propose(investigation_input)
                if proposal.operation is not InvestigationOperation.FINISH:
                    return proposal
                return step_proposal(
                    investigation_input,
                    operation=InvestigationOperation.FINISH,
                    evidence_reference=(
                        investigation_input.ledger.entries[-1].entry_id.value
                    ),
                )

        service = EngineeringQuestionAnsweringService(
            question_understanding_role=UnderstandingRole(),
            cognition_projector=CognitionProjector(),
            initial_investigation_role=LedgerResultCitingInvestigator(),
            verification_investigation_role=VerificationInvestigator(),
            source_broker=SourceBroker(source_profile=source_profile()),
            retrieval_worker=ScriptedWorker(),
            answer_role=AnswerRole(),
            reviewer_role=ReviewerRole(request_more_evidence=False),
        )

        with self.assertRaises(DomainError) as caught:
            service.answer(request())

        self.assertEqual(caught.exception.code, ErrorCode.PROVIDER_RESPONSE_INVALID)
        self.assertIn("admissible support/citation", str(caught.exception))

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
                observation_ids = tuple(
                    observation.observation_id
                    for disposition in package.checklist_dispositions
                    for observation in disposition.material_observations
                )
                return EngineeringAnswerProposal.create(
                    role_context_id=kwargs["role_context_id"],
                    package_digest=package.digest,
                    response_language=kwargs["understanding"].response_language,
                    claims=(
                        EngineeringAnswerClaimProposal.create(
                            claim_id="claim-bad",
                            kind=AnswerClaimKind.AFFIRMATIVE,
                            content_role=AnswerContentRole.DIRECT_ANSWER,
                            checklist_item_ids=("check-1",),
                            material_observation_ids=observation_ids,
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

    def test_typed_answer_contract_requires_one_direct_answer_first(self):
        result = self.service(request_more_evidence=False).answer(request())
        support = tuple(
            item.entry_id for item in result.current_package.support_citation
        )
        observation_ids = tuple(
            observation.observation_id
            for disposition in result.current_package.checklist_dispositions
            for observation in disposition.material_observations
        )
        process = EngineeringAnswerClaimProposal.create(
            claim_id="claim-process",
            kind=AnswerClaimKind.AFFIRMATIVE,
            content_role=AnswerContentRole.USER_VISIBLE_PROCESS,
            checklist_item_ids=("check-1",),
            material_observation_ids=observation_ids,
            text="The user-visible process follows the documented entry point.",
            evidence_entry_ids=support,
        )
        direct = EngineeringAnswerClaimProposal.create(
            claim_id="claim-direct",
            kind=AnswerClaimKind.AFFIRMATIVE,
            content_role=AnswerContentRole.DIRECT_ANSWER,
            checklist_item_ids=("check-1",),
            material_observation_ids=observation_ids,
            text="Use the documented entry point.",
            evidence_entry_ids=support,
        )

        with self.assertRaises(DomainError):
            EngineeringAnswerProposal.create(
                role_context_id=sid("role_context", "e"),
                package_digest=result.current_package.digest,
                response_language=result.understanding.response_language,
                claims=(process, direct),
            )

    def test_answer_cannot_use_one_observation_as_a_proxy_for_a_side_effect(self):
        result = self.service(request_more_evidence=False).answer(request())
        package = result.current_package
        observations = tuple(
            observation
            for disposition in package.checklist_dispositions
            for observation in disposition.material_observations
        )
        self.assertEqual(
            tuple(item.kind for item in observations),
            (
                MaterialObservationKind.PROCESS_STAGE,
                MaterialObservationKind.SIDE_EFFECT,
            ),
        )
        proposal = EngineeringAnswerProposal.create(
            role_context_id=sid("role_context", "d"),
            package_digest=package.digest,
            response_language=result.understanding.response_language,
            claims=(
                EngineeringAnswerClaimProposal.create(
                    claim_id="claim-partial",
                    kind=AnswerClaimKind.AFFIRMATIVE,
                    content_role=AnswerContentRole.DIRECT_ANSWER,
                    checklist_item_ids=("check-1",),
                    material_observation_ids=(observations[0].observation_id,),
                    text="Start the service through its documented entry point.",
                    evidence_entry_ids=tuple(
                        item.entry_id for item in package.support_citation
                    ),
                ),
            ),
        )

        with self.assertRaises(DomainError) as caught:
            EngineeringAnswerDraft.accept(
                package=package,
                understanding=result.understanding,
                expected_role_context_id=sid("role_context", "d"),
                proposal=proposal,
                revision=1,
            )
        self.assertEqual(caught.exception.code, ErrorCode.CONTROL_STATE_DENIED)

    def test_wholly_redundant_user_visible_claim_moves_out_of_default_body(self):
        result = self.service(request_more_evidence=False).answer(request())
        package = result.current_package
        observations = tuple(
            observation.observation_id
            for disposition in package.checklist_dispositions
            for observation in disposition.material_observations
        )
        support = tuple(item.entry_id for item in package.support_citation)
        role_context = sid("role_context", "a")
        proposal = EngineeringAnswerProposal.create(
            role_context_id=role_context,
            package_digest=package.digest,
            response_language=result.understanding.response_language,
            claims=(
                EngineeringAnswerClaimProposal.create(
                    claim_id="claim-direct",
                    kind=AnswerClaimKind.AFFIRMATIVE,
                    content_role=AnswerContentRole.DIRECT_ANSWER,
                    checklist_item_ids=("check-1",),
                    material_observation_ids=observations,
                    text="Use the documented entry point and expect its startup effect.",
                    evidence_entry_ids=support,
                ),
                EngineeringAnswerClaimProposal.create(
                    claim_id="claim-repeated-process",
                    kind=AnswerClaimKind.AFFIRMATIVE,
                    content_role=AnswerContentRole.USER_VISIBLE_PROCESS,
                    checklist_item_ids=("check-1",),
                    material_observation_ids=(observations[0],),
                    text="Use the documented entry point.",
                    evidence_entry_ids=support,
                ),
            ),
        )

        draft = EngineeringAnswerDraft.accept(
            package=package,
            understanding=result.understanding,
            expected_role_context_id=role_context,
            proposal=proposal,
            revision=1,
        )

        self.assertEqual(draft.default_body_claim_ids, ("claim-direct",))
        self.assertEqual(
            draft.body,
            "Use the documented entry point and expect its startup effect.",
        )

    def test_partially_overlapping_user_visible_claim_is_rejected(self):
        result = self.service(request_more_evidence=False).answer(request())
        package = result.current_package
        observations = tuple(
            observation.observation_id
            for disposition in package.checklist_dispositions
            for observation in disposition.material_observations
        )
        support = tuple(item.entry_id for item in package.support_citation)
        role_context = sid("role_context", "9")
        proposal = EngineeringAnswerProposal.create(
            role_context_id=role_context,
            package_digest=package.digest,
            response_language=result.understanding.response_language,
            claims=(
                EngineeringAnswerClaimProposal.create(
                    claim_id="claim-direct",
                    kind=AnswerClaimKind.AFFIRMATIVE,
                    content_role=AnswerContentRole.DIRECT_ANSWER,
                    checklist_item_ids=("check-1",),
                    material_observation_ids=(observations[0],),
                    text="Use the documented entry point.",
                    evidence_entry_ids=support,
                ),
                EngineeringAnswerClaimProposal.create(
                    claim_id="claim-partial-overlap",
                    kind=AnswerClaimKind.AFFIRMATIVE,
                    content_role=AnswerContentRole.USER_VISIBLE_PROCESS,
                    checklist_item_ids=("check-1",),
                    material_observation_ids=observations,
                    text="Use the documented entry point and expect its startup effect.",
                    evidence_entry_ids=support,
                ),
            ),
        )

        with self.assertRaises(DomainError) as caught:
            EngineeringAnswerDraft.accept(
                package=package,
                understanding=result.understanding,
                expected_role_context_id=role_context,
                proposal=proposal,
                revision=1,
            )

        self.assertEqual(caught.exception.code, ErrorCode.CONTROL_STATE_DENIED)

    def test_direct_answer_can_be_an_honest_boundary_limitation(self):
        claim = EngineeringAnswerClaimProposal.create(
            claim_id="claim-direct-boundary",
            kind=AnswerClaimKind.LIMITATION,
            content_role=AnswerContentRole.DIRECT_ANSWER,
            checklist_item_ids=("check-1",),
            material_observation_ids=(sid("material_observation", "e"),),
            text="The available evidence cannot determine the requested behavior.",
            evidence_entry_ids=(sid("ledger_entry", "f"),),
        )

        self.assertEqual(claim.kind, AnswerClaimKind.LIMITATION)
        self.assertEqual(claim.content_role, AnswerContentRole.DIRECT_ANSWER)

    def test_coverage_only_limitation_can_omit_observation_links(self):
        result = self.service(request_more_evidence=False).answer(request())
        package = result.current_package
        observations = tuple(
            observation.observation_id
            for disposition in package.checklist_dispositions
            for observation in disposition.material_observations
        )
        support = tuple(item.entry_id for item in package.support_citation)
        boundary = tuple(item.entry_id for item in package.boundary_audit)
        self.assertTrue(boundary)
        role_context = sid("role_context", "b")
        proposal = EngineeringAnswerProposal.create(
            role_context_id=role_context,
            package_digest=package.digest,
            response_language=result.understanding.response_language,
            claims=(
                EngineeringAnswerClaimProposal.create(
                    claim_id="claim-direct",
                    kind=AnswerClaimKind.AFFIRMATIVE,
                    content_role=AnswerContentRole.DIRECT_ANSWER,
                    checklist_item_ids=("check-1",),
                    material_observation_ids=observations,
                    text=(
                        "Use the documented entry point; startup also writes "
                        "a local PID file."
                    ),
                    evidence_entry_ids=support,
                ),
                EngineeringAnswerClaimProposal.create(
                    claim_id="claim-coverage-boundary",
                    kind=AnswerClaimKind.LIMITATION,
                    content_role=AnswerContentRole.LIMITATION,
                    checklist_item_ids=("check-1",),
                    material_observation_ids=(),
                    text="The retained evidence does not establish deployment behavior.",
                    evidence_entry_ids=boundary,
                ),
            ),
        )

        draft = EngineeringAnswerDraft.accept(
            package=package,
            understanding=result.understanding,
            expected_role_context_id=role_context,
            proposal=proposal,
            revision=1,
        )

        self.assertIn("deployment behavior", draft.body)
        self.assertEqual(
            draft.claims[1].material_observation_ids,
            (),
        )

    def test_only_affirmative_direct_summary_can_omit_observation_links(self):
        summary = EngineeringAnswerClaimProposal.create(
            claim_id="claim-empty-summary",
            kind=AnswerClaimKind.AFFIRMATIVE,
            content_role=AnswerContentRole.DIRECT_ANSWER,
            checklist_item_ids=("check-1",),
            material_observation_ids=(),
            text="A concise summary expanded by later claims.",
            evidence_entry_ids=(sid("support_entry", "e"),),
        )

        self.assertEqual(summary.material_observation_ids, ())
        with self.assertRaises(DomainError) as caught:
            EngineeringAnswerClaimProposal.create(
                claim_id="claim-empty-observations",
                kind=AnswerClaimKind.AFFIRMATIVE,
                content_role=AnswerContentRole.USER_VISIBLE_PROCESS,
                checklist_item_ids=("check-1",),
                material_observation_ids=(),
                text="An unlinked fact.",
                evidence_entry_ids=(sid("support_entry", "e"),),
            )

        self.assertEqual(caught.exception.code, ErrorCode.INVALID_ARGUMENT)

    def test_empty_link_direct_summary_is_expanded_by_later_default_claim(self):
        result = self.service(request_more_evidence=False).answer(request())
        package = result.current_package
        observations = tuple(
            observation.observation_id
            for disposition in package.checklist_dispositions
            for observation in disposition.material_observations
        )
        support = tuple(item.entry_id for item in package.support_citation)
        role_context = sid("role_context", "8")
        proposal = EngineeringAnswerProposal.create(
            role_context_id=role_context,
            package_digest=package.digest,
            response_language=result.understanding.response_language,
            claims=(
                EngineeringAnswerClaimProposal.create(
                    claim_id="claim-direct-summary",
                    kind=AnswerClaimKind.AFFIRMATIVE,
                    content_role=AnswerContentRole.DIRECT_ANSWER,
                    checklist_item_ids=("check-1",),
                    material_observation_ids=(),
                    text="Use the documented startup flow and expect its effect.",
                    evidence_entry_ids=support,
                ),
                EngineeringAnswerClaimProposal.create(
                    claim_id="claim-expanded-process",
                    kind=AnswerClaimKind.AFFIRMATIVE,
                    content_role=AnswerContentRole.USER_VISIBLE_PROCESS,
                    checklist_item_ids=("check-1",),
                    material_observation_ids=observations,
                    text="Use the documented entry point; startup also writes a local PID file.",
                    evidence_entry_ids=support,
                ),
            ),
        )

        draft = EngineeringAnswerDraft.accept(
            package=package,
            understanding=result.understanding,
            expected_role_context_id=role_context,
            proposal=proposal,
            revision=1,
        )

        self.assertEqual(
            draft.default_body_claim_ids,
            ("claim-direct-summary", "claim-expanded-process"),
        )
        self.assertIn("\n\n", draft.body)

    def test_coverage_limitation_cannot_attach_supported_observations(self):
        result = self.service(request_more_evidence=False).answer(request())
        package = result.current_package
        observations = tuple(
            observation.observation_id
            for disposition in package.checklist_dispositions
            for observation in disposition.material_observations
        )
        role_context = sid("role_context", "c")
        proposal = EngineeringAnswerProposal.create(
            role_context_id=role_context,
            package_digest=package.digest,
            response_language=result.understanding.response_language,
            claims=(
                EngineeringAnswerClaimProposal.create(
                    claim_id="claim-direct",
                    kind=AnswerClaimKind.AFFIRMATIVE,
                    content_role=AnswerContentRole.DIRECT_ANSWER,
                    checklist_item_ids=("check-1",),
                    material_observation_ids=observations,
                    text=(
                        "Use the documented entry point; startup also writes "
                        "a local PID file."
                    ),
                    evidence_entry_ids=tuple(
                        item.entry_id for item in package.support_citation
                    ),
                ),
                EngineeringAnswerClaimProposal.create(
                    claim_id="claim-invalid-boundary",
                    kind=AnswerClaimKind.LIMITATION,
                    content_role=AnswerContentRole.LIMITATION,
                    checklist_item_ids=("check-1",),
                    material_observation_ids=observations,
                    text="The retained evidence has a deployment boundary.",
                    evidence_entry_ids=tuple(
                        item.entry_id for item in package.boundary_audit
                    ),
                ),
            ),
        )

        with self.assertRaises(DomainError) as caught:
            EngineeringAnswerDraft.accept(
                package=package,
                understanding=result.understanding,
                expected_role_context_id=role_context,
                proposal=proposal,
                revision=1,
            )

        self.assertEqual(caught.exception.code, ErrorCode.CONTROL_STATE_DENIED)

    def test_user_visible_answer_keeps_implementation_out_of_default_body(self):
        result = self.service(request_more_evidence=False).answer(request())
        package = result.current_package
        support = tuple(item.entry_id for item in package.support_citation)
        observation_ids = tuple(
            observation.observation_id
            for disposition in package.checklist_dispositions
            for observation in disposition.material_observations
        )
        role_context = sid("role_context", "f")
        proposal = EngineeringAnswerProposal.create(
            role_context_id=role_context,
            package_digest=package.digest,
            response_language=result.understanding.response_language,
            claims=(
                EngineeringAnswerClaimProposal.create(
                    claim_id="claim-direct",
                    kind=AnswerClaimKind.AFFIRMATIVE,
                    content_role=AnswerContentRole.DIRECT_ANSWER,
                    checklist_item_ids=("check-1",),
                    material_observation_ids=observation_ids,
                    text="Use the documented entry point.",
                    evidence_entry_ids=support,
                ),
                EngineeringAnswerClaimProposal.create(
                    claim_id="claim-implementation",
                    kind=AnswerClaimKind.AFFIRMATIVE,
                    content_role=AnswerContentRole.IMPLEMENTATION_EVIDENCE,
                    checklist_item_ids=("check-1",),
                    material_observation_ids=observation_ids,
                    text=" ".join("implementation-detail" for _ in range(20)),
                    evidence_entry_ids=support,
                ),
            ),
        )

        draft = EngineeringAnswerDraft.accept(
            package=package,
            understanding=result.understanding,
            expected_role_context_id=role_context,
            proposal=proposal,
            revision=1,
        )
        self.assertEqual(draft.default_body_claim_ids, ("claim-direct",))
        self.assertIn("documented entry point", draft.body)
        self.assertNotIn("implementation-detail", draft.body)
        self.assertEqual(
            draft.model_view()["claims"][1]["content_role"],
            "IMPLEMENTATION_EVIDENCE",
        )

    def test_user_visible_answer_keeps_uniquely_material_implementation_visible(self):
        result = self.service(request_more_evidence=False).answer(request())
        package = result.current_package
        support = tuple(item.entry_id for item in package.support_citation)
        observation_ids = tuple(
            observation.observation_id
            for disposition in package.checklist_dispositions
            for observation in disposition.material_observations
        )
        self.assertGreaterEqual(len(observation_ids), 2)
        role_context = sid("role_context", "0")
        proposal = EngineeringAnswerProposal.create(
            role_context_id=role_context,
            package_digest=package.digest,
            response_language=result.understanding.response_language,
            claims=(
                EngineeringAnswerClaimProposal.create(
                    claim_id="claim-direct-summary",
                    kind=AnswerClaimKind.AFFIRMATIVE,
                    content_role=AnswerContentRole.DIRECT_ANSWER,
                    checklist_item_ids=("check-1",),
                    material_observation_ids=(),
                    text="Use the supported repository entry point.",
                    evidence_entry_ids=support,
                ),
                EngineeringAnswerClaimProposal.create(
                    claim_id="claim-process",
                    kind=AnswerClaimKind.AFFIRMATIVE,
                    content_role=AnswerContentRole.USER_VISIBLE_PROCESS,
                    checklist_item_ids=("check-1",),
                    material_observation_ids=observation_ids[:1],
                    text="Follow the supported user-visible process.",
                    evidence_entry_ids=support,
                ),
                EngineeringAnswerClaimProposal.create(
                    claim_id="claim-requested-basis",
                    kind=AnswerClaimKind.AFFIRMATIVE,
                    content_role=AnswerContentRole.IMPLEMENTATION_EVIDENCE,
                    checklist_item_ids=("check-1",),
                    material_observation_ids=observation_ids[1:],
                    text="Verify the requested basis in the cited implementation.",
                    evidence_entry_ids=support,
                ),
            ),
        )

        draft = EngineeringAnswerDraft.accept(
            package=package,
            understanding=result.understanding,
            expected_role_context_id=role_context,
            proposal=proposal,
            revision=1,
        )

        self.assertEqual(
            draft.default_body_claim_ids,
            (
                "claim-direct-summary",
                "claim-process",
                "claim-requested-basis",
            ),
        )
        self.assertIn("requested basis", draft.body)

    def test_approved_review_requires_all_direction_quality_checks(self):
        failed_quality = EngineeringReviewQualityAssessment.create(
            direct_answer=EngineeringReviewQualityStatus.PASS,
            abstraction_fit=EngineeringReviewQualityStatus.PASS,
            material_completeness=EngineeringReviewQualityStatus.PASS,
            claim_consistency=EngineeringReviewQualityStatus.FAIL,
            implementation_detail_budget=EngineeringReviewQualityStatus.PASS,
        )
        with self.assertRaises(DomainError):
            EngineeringReviewProposal.create(
                role_context_id=sid("role_context", "9"),
                package_digest=Digest("sha256:" + "1" * 64),
                draft_digest=Digest("sha256:" + "2" * 64),
                decision=EngineeringReviewDecision.APPROVED,
                quality_assessment=failed_quality,
                checklist_assessment=EngineeringReviewChecklistAssessment.create(
                    independent_material_conclusions=("Explain the user goal.",),
                    application_checklist_omissions=(),
                    independent_material_observations=(
                        EngineeringReviewMaterialObservation.create(
                            checklist_item_id="check-1",
                            kind=MaterialObservationKind.OUTCOME,
                            statement="The user goal has one material outcome.",
                            evidence_entry_ids=(sid("package_entry", "8"),),
                        ),
                    ),
                    application_material_observation_omissions=(),
                    draft_material_observation_omissions=(),
                ),
            )

    def test_review_action_and_verification_request_are_derived_from_findings(self):
        result = self.service(request_more_evidence=False).answer(request())
        package = result.current_package
        draft = result.current_draft
        assessment = matching_review_checklist(result.understanding, package)
        evidence_gap = EngineeringReviewFinding.create(
            finding_code="AUTHORIZATION_IMPLEMENTATION_MISSING",
            checklist_item_id="check-1",
            claim_id="claim-1",
            description="The current Package lacks the decisive implementation.",
            remediation=(
                EngineeringReviewRemediation.INVESTIGATE_MISSING_EVIDENCE
            ),
            evidence_class=EngineeringEvidenceClass.SOURCE,
            evidence_need="Decisive authorization comparison and result behavior",
        )

        proposal = EngineeringReviewProposal.create_from_findings(
            role_context_id=sid("role_context", "6"),
            package_digest=package.digest,
            draft_digest=draft.digest,
            quality_assessment=passing_quality(),
            checklist_assessment=assessment,
            findings=(evidence_gap,),
        )

        self.assertEqual(
            proposal.decision,
            EngineeringReviewDecision.MORE_EVIDENCE_REQUIRED,
        )
        self.assertIsNotNone(proposal.verification_request)
        self.assertEqual(
            proposal.verification_request.evidence_need,
            evidence_gap.evidence_need,
        )
        with self.assertRaises(DomainError):
            EngineeringReviewProposal.create(
                role_context_id=sid("role_context", "6"),
                package_digest=package.digest,
                draft_digest=draft.digest,
                decision=EngineeringReviewDecision.REWRITE_REQUIRED,
                quality_assessment=passing_quality(),
                checklist_assessment=assessment,
                findings=(evidence_gap,),
                verification_request=None,
            )

        rewrite = EngineeringReviewFinding.create(
            finding_code="CLAIM_SCOPE_TOO_BROAD",
            checklist_item_id="check-1",
            claim_id="claim-1",
            description="Narrow the claim to the existing Package evidence.",
            remediation=(
                EngineeringReviewRemediation.REWRITE_WITH_EXISTING_EVIDENCE
            ),
            existing_evidence_entry_ids=(package.support_citation[0].entry_id,),
        )
        rewrite_proposal = EngineeringReviewProposal.create_from_findings(
            role_context_id=sid("role_context", "7"),
            package_digest=package.digest,
            draft_digest=draft.digest,
            quality_assessment=passing_quality(),
            checklist_assessment=assessment,
            findings=(rewrite,),
        )
        self.assertEqual(
            rewrite_proposal.decision,
            EngineeringReviewDecision.REWRITE_REQUIRED,
        )
        self.assertIsNone(rewrite_proposal.verification_request)

        unrecoverable = EngineeringReviewFinding.create(
            finding_code="BOUNDARY_CONFLICT",
            checklist_item_id="check-1",
            description="The requested conclusion conflicts with an explicit boundary.",
            remediation=EngineeringReviewRemediation.REJECT_UNRECOVERABLE,
        )
        rejected_proposal = EngineeringReviewProposal.create_from_findings(
            role_context_id=sid("role_context", "8"),
            package_digest=package.digest,
            draft_digest=draft.digest,
            quality_assessment=passing_quality(),
            checklist_assessment=assessment,
            findings=(evidence_gap, unrecoverable),
        )
        self.assertEqual(
            rejected_proposal.decision,
            EngineeringReviewDecision.REJECT,
        )
        self.assertIsNone(rejected_proposal.verification_request)

    def test_review_finding_remediation_fields_are_closed(self):
        with self.assertRaises(DomainError):
            EngineeringReviewFinding.create(
                finding_code="UNSUPPORTED_REWRITE",
                checklist_item_id="check-1",
                description="A rewrite cannot repair absent evidence.",
                remediation=(
                    EngineeringReviewRemediation.REWRITE_WITH_EXISTING_EVIDENCE
                ),
            )
        with self.assertRaises(DomainError) as caught:
            EngineeringReviewFinding.create(
                finding_code="EXECUTABLE_GAP",
                checklist_item_id="check-1",
                description="The Package lacks one implementation.",
                remediation=(
                    EngineeringReviewRemediation.INVESTIGATE_MISSING_EVIDENCE
                ),
                evidence_class=EngineeringEvidenceClass.SOURCE,
                evidence_need="read(src/Main.java)",
            )
        self.assertEqual(caught.exception.code, ErrorCode.PROVIDER_OUTPUT_FORBIDDEN)

    def test_review_cannot_approve_an_independently_observed_draft_omission(self):
        result = self.service(request_more_evidence=False).answer(request())
        assessment = matching_review_checklist(
            result.understanding, result.current_package
        )
        omitted_statement = next(
            item.statement
            for item in assessment.independent_material_observations
            if item.kind is MaterialObservationKind.SIDE_EFFECT
        )
        assessment_with_omission = EngineeringReviewChecklistAssessment.create(
            independent_material_conclusions=(
                assessment.independent_material_conclusions
            ),
            application_checklist_omissions=(),
            independent_material_observations=(
                assessment.independent_material_observations
            ),
            application_material_observation_omissions=(),
            draft_material_observation_omissions=(omitted_statement,),
        )

        with self.assertRaises(DomainError):
            EngineeringReviewProposal.create(
                role_context_id=sid("role_context", "7"),
                package_digest=result.current_package.digest,
                draft_digest=result.current_draft.digest,
                decision=EngineeringReviewDecision.APPROVED,
                quality_assessment=passing_quality(),
                checklist_assessment=assessment_with_omission,
            )

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
