from __future__ import annotations

from dataclasses import replace
import unittest

from software_world_model.application_services.engineering_question_answering import (
    CognitionDimension,
    EngineeringQuestionAnsweringService,
    EngineeringQuestionRequest,
    EngineeringQuestionResourceLimits,
    RevisionAlignment,
    SourceBroker,
)
from software_world_model.application_services.engineering_question_cognition import (
    StructureBundleWorldModelCognitionProjector,
)
from software_world_model.cross_cutting import (
    DomainError,
    ErrorCode,
    StableId,
    canonical_json_bytes,
)
from software_world_model.interface.engineering_qa_source import (
    LocalGitEvidenceClassProfile,
)
from software_world_model.application_services.engineering_question_answering import (
    EngineeringEvidenceClass,
)
from tests import test_engineering_question_answering as qa_fixtures
from tests import test_structure_view as structure_fixtures


class EngineeringQuestionCognitionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.structure = structure_fixtures.StructureViewTests(methodName="runTest")
        self.structure.setUp()
        self.addCleanup(self.structure.doCleanups)
        self.bundle = self.structure.a[1]
        self.projector = StructureBundleWorldModelCognitionProjector(
            view=self.structure.service,
            snapshot_bundle=self.bundle,
        )
        self.profile = LocalGitEvidenceClassProfile.create(
            profile_ref="engineering-qa-structure-integration:1",
            binding_id=self.projector.binding_id,
            evidence_class_paths={
                EngineeringEvidenceClass.SOURCE: ("src",),
                EngineeringEvidenceClass.REPOSITORY_DOCUMENT: ("README.md",),
                EngineeringEvidenceClass.BUILD_CONFIGURATION: ("config",),
                EngineeringEvidenceClass.TEST: ("tests",),
            },
        )

    def request(
        self,
        *,
        binding_id: StableId | None = None,
        limits: EngineeringQuestionResourceLimits | None = None,
    ) -> EngineeringQuestionRequest:
        return EngineeringQuestionRequest.create(
            request_ref="structure-cognition-question",
            original_question=qa_fixtures.request().original_question,
            response_language="en",
            repository_id=StableId("repository_" + "d" * 32),
            binding_id=binding_id or self.projector.binding_id,
            repository_revision=self.projector.source_revision,
            source_profile_ref=self.profile.profile_ref,
            source_profile_digest=self.profile.profile_digest,
            world_model_read_authority_digest=(
                self.projector.read_authority_digest
            ),
            source_allowlist=(".",),
            limits=limits,
        )

    def test_exact_structure_bundle_projects_typed_supported_cognition(self):
        request = self.request()
        context = self.projector.project(request=request)

        self.assertEqual(context.alignment, RevisionAlignment.ALIGNED)
        self.assertEqual(
            context.snapshot_ids,
            (self.bundle.snapshot_id.value,),
        )
        self.assertEqual(context.schema_ref, self.bundle.snapshot.schema_ref)
        self.assertEqual(
            {
                CognitionDimension.COVERAGE,
                CognitionDimension.ENTITY,
                CognitionDimension.RELATION,
                CognitionDimension.EVIDENCE,
            },
            {item.dimension for item in context.items},
        )
        self.assertTrue(
            all(
                item.support_references
                for item in context.items
                if item.dimension is not CognitionDimension.COVERAGE
            )
        )
        self.assertLessEqual(
            len(canonical_json_bytes(context.model_view())),
            request.limits.maximum_world_model_bytes,
        )

    def test_projection_discloses_deterministic_byte_bound_truncation(self):
        request = self.request(
            limits=replace(
                EngineeringQuestionResourceLimits(),
                maximum_world_model_bytes=8_192,
            )
        )
        context = self.projector.project(request=request)

        self.assertLess(len(context.items), 16)
        self.assertTrue(
            any("retained" in unknown for unknown in context.unknowns)
        )
        self.assertLessEqual(
            len(canonical_json_bytes(context.model_view())),
            request.limits.maximum_world_model_bytes,
        )

    def test_projection_rejects_another_source_binding(self):
        with self.assertRaises(DomainError) as caught:
            self.projector.project(
                request=self.request(
                    binding_id=StableId("binding_" + "e" * 32)
                )
            )
        self.assertEqual(
            caught.exception.code,
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
        )

    def test_structure_cognition_and_query_time_source_share_one_package(self):
        service = EngineeringQuestionAnsweringService(
            question_understanding_role=qa_fixtures.UnderstandingRole(),
            cognition_projector=self.projector,
            initial_investigation_role=qa_fixtures.InitialInvestigator(),
            verification_investigation_role=qa_fixtures.VerificationInvestigator(),
            source_broker=SourceBroker(source_profile=self.profile),
            retrieval_worker=qa_fixtures.ScriptedWorker(),
            answer_role=qa_fixtures.AnswerRole(),
            reviewer_role=qa_fixtures.ReviewerRole(
                request_more_evidence=False
            ),
        )
        result = service.answer(self.request())

        origins = {item.origin_class for item in result.current_package.support_citation}
        self.assertIn("WORLD_MODEL_COGNITION", origins)
        self.assertIn("EXACT_REVISION_SOURCE", origins)
        self.assertEqual(result.authorized_answer.package_digest, result.current_package.digest)


if __name__ == "__main__":
    unittest.main()
