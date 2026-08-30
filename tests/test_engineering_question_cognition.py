from __future__ import annotations

from dataclasses import replace
import json
import unittest
from unittest.mock import patch

from software_world_model.application_services.engineering_question_answering import (
    CognitionDimension,
    CognitionItem,
    EngineeringQuestionAnsweringService,
    EngineeringQuestionRequest,
    EngineeringQuestionResourceLimits,
    RevisionAlignment,
    SourceBroker,
)
from software_world_model.application_services.engineering_question_cognition import (
    MultiProfileWorldModelCognitionProjector,
    StructureBundleWorldModelCognitionProjector,
    _rank_relevant_cognition_items,
    _statement_feature_tokens,
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
from tests import test_java_source_semantics as java_fixtures
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
        self.repository_id = StableId("repository_" + "d" * 32)
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
            repository_id=self.repository_id,
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


class MultiProfileEngineeringQuestionCognitionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.structure = structure_fixtures.StructureViewTests(methodName="runTest")
        self.structure.setUp()
        self.addCleanup(self.structure.doCleanups)
        structure_projector = StructureBundleWorldModelCognitionProjector(
            view=self.structure.service,
            snapshot_bundle=self.structure.a[1],
        )
        self.java = java_fixtures.JavaImplementationViewTests(methodName="runTest")
        original_fixture_input = java_fixtures._fixture_input
        with patch.object(
            java_fixtures,
            "_fixture_input",
            side_effect=lambda *args, **kwargs: original_fixture_input(
                structure_projector.source_revision,
                *args,
                **kwargs,
            ),
        ):
            self.java.setUp()
        self.addCleanup(self.java.doCleanups)
        java_projector = StructureBundleWorldModelCognitionProjector(
            view=self.java.service,
            snapshot_bundle=self.java.bundle,
        )
        self.repository_id = StableId("repository_" + "8" * 32)
        self.structure_projector = structure_projector
        self.java_projector = java_projector
        self.multi = MultiProfileWorldModelCognitionProjector(
            repository_id=self.repository_id,
            binding_id=structure_projector.binding_id,
            projectors=(structure_projector, java_projector),
        )

    def request(
        self,
        *,
        question: str,
        projector=None,
        source_allowlist: tuple[str, ...] = ("src",),
    ):
        projector = projector or self.multi
        return EngineeringQuestionRequest.create(
            request_ref="multi-profile-cognition-question",
            original_question=question,
            response_language="en",
            repository_id=self.repository_id,
            binding_id=projector.binding_id,
            repository_revision=projector.source_revision,
            source_profile_ref="multi-profile-cognition-source:1",
            source_profile_digest=self.multi.manifest.digest,
            world_model_read_authority_digest=projector.read_authority_digest,
            source_allowlist=source_allowlist,
        )

    def test_maven_only_is_ineligible_for_behavior_question(self) -> None:
        maven_only = MultiProfileWorldModelCognitionProjector(
            repository_id=self.repository_id,
            binding_id=self.structure_projector.binding_id,
            projectors=(self.structure_projector,),
        )
        context = maven_only.project(
            request=self.request(
                question="How does authentication behavior work?",
                projector=maven_only,
            )
        )

        self.assertNotIn(CognitionDimension.BEHAVIOR, maven_only.manifest.dimensions)
        self.assertTrue(
            any("missing dimensions: BEHAVIOR" in item for item in context.unknowns)
        )

    def test_same_revision_manifest_combines_structure_and_behavior_authorities(self) -> None:
        self.assertEqual(len(self.multi.manifest.profiles), 2)
        self.assertEqual(
            {item.source_revision for item in self.multi.manifest.profiles},
            {self.multi.source_revision},
        )
        self.assertIn(CognitionDimension.RELATION, self.multi.manifest.dimensions)
        self.assertIn(CognitionDimension.BEHAVIOR, self.multi.manifest.dimensions)
        self.assertEqual(
            len(
                {
                    item.read_authority_digest
                    for item in self.multi.manifest.profiles
                }
            ),
            2,
        )

        assessment = next(
            item
            for item in self.multi.project(
                request=self.request(
                    question="How does authentication behavior work?"
                )
            ).items
            if item.modality == "COGNITION_QUESTION_ELIGIBILITY"
        )
        self.assertIn('"dimension":"BEHAVIOR"', assessment.statement)
        self.assertIn(
            self.java_projector.snapshot_bundle.coverages[0].root.profile_ref,
            assessment.statement,
        )
        self.assertIn('"query_capability":"method_implementations@1"', assessment.statement)

    def test_different_questions_receive_different_relevant_projections(self) -> None:
        structure = self.multi.project_for_query(
            request=self.request(
                question="Which module dependencies connect admin and common?"
            ),
            query="admin dependency common module",
        )
        behavior = self.multi.project_for_query(
            request=self.request(
                question="How does authentication behavior work?"
            ),
            query="authenticate credentials session",
        )
        structure_support = {
            item.item_id
            for item in structure.items
            if item.dimension not in {
                CognitionDimension.COVERAGE,
                CognitionDimension.UNKNOWN,
            }
        }
        behavior_support = {
            item.item_id
            for item in behavior.items
            if item.dimension not in {
                CognitionDimension.COVERAGE,
                CognitionDimension.UNKNOWN,
            }
        }

        self.assertTrue(structure_support)
        self.assertTrue(behavior_support)
        self.assertNotEqual(structure_support, behavior_support)
        self.assertTrue(
            any(
                item.dimension is CognitionDimension.BEHAVIOR
                and "authenticate" in item.statement
                for item in behavior.items
            )
        )
        self.assertTrue(
            any(
                '"predicate":"CALL_SITE_TARGETS"' in item.statement
                and "authenticate" in item.statement
                and "issueSession" in item.statement
                for item in behavior.items
            )
        )

    def test_explicit_source_scope_excludes_other_profile_items(self) -> None:
        source_allowlist = (
            "src/main/java",
            "search/src/main/java",
        )
        query = "search authenticate credentials session"
        unscoped = self.multi.project_for_query(
            request=self.request(
                question="How does authentication behavior work?",
                source_allowlist=source_allowlist,
            ),
            query=query,
        )
        context = self.multi.project_for_query(
            request=self.request(
                question="How does the search module authenticate credentials?",
                source_allowlist=source_allowlist,
            ),
            query=query,
        )
        unscoped_affirmative = tuple(
            item
            for item in unscoped.items
            if item.dimension
            not in {
                CognitionDimension.COVERAGE,
                CognitionDimension.EVIDENCE,
                CognitionDimension.UNKNOWN,
            }
        )
        affirmative = tuple(
            item
            for item in context.items
            if item.dimension
            not in {
                CognitionDimension.COVERAGE,
                CognitionDimension.EVIDENCE,
                CognitionDimension.UNKNOWN,
            }
        )

        self.assertTrue(
            any('"source_path":' in item.statement for item in unscoped_affirmative)
        )
        self.assertTrue(
            any('"module_path":"search"' in item.statement for item in affirmative)
        )
        self.assertFalse(
            any('"source_path":' in item.statement for item in affirmative)
        )
        self.assertTrue(
            any(
                "explicit Source scope(s) search are outside Profile root scope(s) src"
                in item
                for item in context.unknowns
            )
        )
        self.assertFalse(
            any("INCOMPLETE_IMPLEMENTATION_METHODS" in item for item in context.unknowns)
        )

    def test_relevance_ranking_ignores_common_and_structural_noise(self) -> None:
        relevant = CognitionItem.create(
            dimension=CognitionDimension.ENTITY,
            statement=json.dumps(
                {
                    "kind": "STRUCTURE_ENTITY",
                    "entity_type": "JAVA_METHOD",
                    "root_fields": {
                        "declaring_type_qualified_name": (
                            "com.macro.mall.controller.UmsAdminController"
                        ),
                        "method_name": "updateRole",
                        "parameter_types": [
                            "jakarta.servlet.http.HttpServletRequest"
                        ],
                    },
                },
                sort_keys=True,
                separators=(",", ":"),
            ),
            modality="STRUCTURE_ENTITY_STATE",
            context_ref="relevance-fixture",
            source_revision=self.multi.source_revision,
            locator="world-model:relevance:update-role",
            support_references=("relevance-update-role",),
            coverage="Exact updateRole entity.",
        )
        unrelated = CognitionItem.create(
            dimension=CognitionDimension.BEHAVIOR,
            statement=json.dumps(
                {
                    "kind": "STRUCTURE_RELATION",
                    "subject_entity_root_id": "entity_root_admin_noise",
                    "predicate": "CALL_SITE_TARGETS",
                    "subject_identity": {
                        "owning_method": {
                            "declaring_type_qualified_name": (
                                "com.macro.mall.service.impl.PmsProductServiceImpl"
                            ),
                            "method_name": "create",
                            "source_path": (
                                "mall-admin/src/main/java/com/macro/mall/service/"
                                "impl/PmsProductServiceImpl.java"
                            ),
                        }
                    },
                    "object_identity": {
                        "declaring_type_qualified_name": (
                            "com.macro.mall.service.impl.PmsProductServiceImpl"
                        ),
                        "method_name": "relateAndInsertList",
                    },
                    "state_fields": {
                        "disposition": "UNSUPPORTED_EXCLUDED",
                        "evidence_references": ["evidence_admin_noise"],
                    },
                },
                sort_keys=True,
                separators=(",", ":"),
            ),
            modality="STRUCTURE_BEHAVIOR_RELATION",
            context_ref="relevance-fixture",
            source_revision=self.multi.source_revision,
            locator="world-model:relevance:product-relation",
            support_references=("relevance-product-relation",),
            coverage="Exact unrelated product relation.",
        )
        weak_tail = CognitionItem.create(
            dimension=CognitionDimension.ENTITY,
            statement=json.dumps(
                {
                    "kind": "STRUCTURE_ENTITY",
                    "entity_type": "JAVA_SOURCE_FILE",
                    "root_fields": {
                        "source_path": (
                            "mall-admin/src/main/java/com/macro/mall/controller/"
                            "SmsHomeNewProductController.java"
                        ),
                    },
                },
                sort_keys=True,
                separators=(",", ":"),
            ),
            modality="STRUCTURE_ENTITY_STATE",
            context_ref="relevance-fixture",
            source_revision=self.multi.source_revision,
            locator="world-model:relevance:weak-tail",
            support_references=("relevance-weak-tail",),
            coverage="Exact unrelated weak-tail Controller.",
        )

        self.assertNotIn(
            "structure",
            _statement_feature_tokens(unrelated.statement),
        )
        self.assertNotIn(
            "admin",
            _statement_feature_tokens(unrelated.statement),
        )
        self.assertNotIn(
            "unsupported",
            _statement_feature_tokens(unrelated.statement),
        )
        self.assertNotIn(
            "evidence",
            _statement_feature_tokens(unrelated.statement),
        )
        self.assertNotIn(
            "admin",
            _statement_feature_tokens(weak_tail.statement),
        )
        ranked = _rank_relevant_cognition_items(
            (
                "mall admin backend HTTP controller role relation insertion "
                "and new permission cache refresh"
            ),
            (relevant, unrelated, weak_tail),
            maximum_items=32,
        )

        self.assertEqual(ranked, (relevant,))

    def test_relevance_ranking_keeps_prefix_only_match_without_exact_anchor(self) -> None:
        authenticate = CognitionItem.create(
            dimension=CognitionDimension.ENTITY,
            statement=json.dumps(
                {
                    "kind": "STRUCTURE_ENTITY",
                    "entity_type": "JAVA_METHOD",
                    "root_fields": {
                        "declaring_type_qualified_name": "example.CredentialService",
                        "method_name": "authenticate",
                    },
                },
                sort_keys=True,
                separators=(",", ":"),
            ),
            modality="STRUCTURE_ENTITY_STATE",
            context_ref="relevance-fixture",
            source_revision=self.multi.source_revision,
            locator="world-model:relevance:authenticate",
            support_references=("relevance-authenticate",),
            coverage="Exact authenticate entity.",
        )

        self.assertEqual(
            _rank_relevant_cognition_items(
                "authenticated",
                (authenticate,),
                maximum_items=32,
            ),
            (authenticate,),
        )

    def test_relevance_ranking_keeps_direct_relation_endpoint_entity(self) -> None:
        context_ref = "relation-endpoint-closure-fixture"
        source_revision = self.multi.source_revision
        endpoint = CognitionItem.create(
            dimension=CognitionDimension.ENTITY,
            statement=json.dumps(
                {
                    "kind": "STRUCTURE_ENTITY",
                    "entity_type": "JAVA_METHOD",
                    "root_fields": {
                        "declaring_type_qualified_name": (
                            "example.permission.RoleRefreshService"
                        ),
                        "method_name": "refreshRole",
                        "parameter_types": ["java.lang.Long"],
                    },
                    "state_fields": {
                        "source_path": (
                            "src/main/java/example/permission/"
                            "RoleRefreshService.java"
                        ),
                        "source_revision": source_revision,
                    },
                },
                sort_keys=True,
                separators=(",", ":"),
            ),
            modality="STRUCTURE_ENTITY_STATE",
            context_ref=context_ref,
            source_revision=source_revision,
            locator=(
                f"world-model:snapshot:{context_ref}:"
                "entity:entity_root_refresh_role"
            ),
            support_references=("relation-endpoint-entity-evidence",),
            coverage="Exact relation endpoint Entity state.",
        )
        relation = CognitionItem.create(
            dimension=CognitionDimension.BEHAVIOR,
            statement=json.dumps(
                {
                    "kind": "STRUCTURE_RELATION",
                    "subject_entity_root_id": "entity_root_refresh_call",
                    "predicate": "CALL_SITE_TARGETS",
                    "object_entity_root_id": "entity_root_refresh_role",
                    "subject_identity": {
                        "owning_method": {
                            "declaring_type_qualified_name": (
                                "example.permission.RoleAssignmentService"
                            ),
                            "method_name": "assignRole",
                        }
                    },
                    "object_identity": {
                        "declaring_type_qualified_name": (
                            "example.permission.RoleRefreshService"
                        ),
                        "method_name": "refreshRole",
                    },
                    "state_fields": {
                        "effect": "permission cache refresh after role write"
                    },
                },
                sort_keys=True,
                separators=(",", ":"),
            ),
            modality="STRUCTURE_BEHAVIOR_RELATION",
            context_ref=context_ref,
            source_revision=source_revision,
            locator=(
                f"world-model:snapshot:{context_ref}:"
                "relation:relation_root_refresh_role"
            ),
            support_references=("relation-endpoint-relation-evidence",),
            coverage="Exact behavior relation.",
        )

        ranked = _rank_relevant_cognition_items(
            "role write permission cache refresh effect",
            (endpoint, relation),
            maximum_items=32,
        )

        self.assertEqual(ranked, (relation, endpoint))
        self.assertEqual(
            _rank_relevant_cognition_items(
                "role write permission cache refresh effect",
                (endpoint, relation),
                maximum_items=1,
            ),
            (relation,),
        )

    def test_failure_boundary_need_preserves_constraint_gap(self) -> None:
        context = self.multi.project_for_query(
            request=self.request(
                question="What are the failure responsibility and state boundaries?"
            ),
            query="failure responsibility state boundary",
        )

        self.assertTrue(
            any("missing dimensions: CONSTRAINT" in item for item in context.unknowns)
        )


if __name__ == "__main__":
    unittest.main()
