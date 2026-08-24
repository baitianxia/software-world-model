from __future__ import annotations

from dataclasses import replace
import json
import unittest
from collections.abc import Mapping

from software_world_model.ai_infrastructure import (
    engineering_question_strategy as strategy_contract,
)
from software_world_model.ai_infrastructure.engineering_question_strategy import (
    ENGINEERING_QUESTION_ANSWER_OUTPUT_SCHEMA_REF,
    ENGINEERING_QUESTION_INITIAL_INVESTIGATION_OUTPUT_SCHEMA_REF,
    ENGINEERING_QUESTION_REVIEW_OUTPUT_SCHEMA_REF,
    ENGINEERING_QUESTION_UNDERSTANDING_OUTPUT_SCHEMA_REF,
    ENGINEERING_QUESTION_VERIFICATION_INVESTIGATION_OUTPUT_SCHEMA_REF,
    EngineeringQuestionModelRole,
    EngineeringQuestionRoleInputBuilder,
    EngineeringQuestionRoleOutput,
    EngineeringQuestionStructuredStrategyBundle,
    StructuredEngineeringAnswerRole,
    StructuredEngineeringAnswerReviewerRole,
    StructuredQuestionUnderstandingRole,
    engineering_question_output_contract_digest,
    engineering_question_output_schemas,
)
from software_world_model.application_services.engineering_question_answering import (
    ChecklistDispositionReferenceEligibility,
    EngineeringQuestionAnsweringService,
    EngineeringQuestionResultStatus,
    EvidenceLedger,
    InitialInvestigationInput,
    RequiredEvidencePathLocator,
    RetrievalItem,
    SourceBroker,
    VerificationInvestigationInput,
    VerificationRequestProposal,
    EngineeringEvidenceClass,
)
from software_world_model.cross_cutting import Digest, DomainError, ErrorCode, StableId
from tests import test_engineering_question_answering as fixtures


def sid(kind: str, digit: str) -> StableId:
    return StableId(f"{kind}_{digit * 32}")


def collect_keys(value):
    keys = set()
    if isinstance(value, Mapping):
        keys.update(value)
        for item in value.values():
            keys.update(collect_keys(item))
    elif isinstance(value, list):
        for item in value:
            keys.update(collect_keys(item))
    return keys


class AdaptiveStructuredOutputSource:
    """A no-network role-output source used to exercise the real adapters."""

    def __init__(self, *, request_more_evidence: bool = False):
        self.request_more_evidence = request_more_evidence
        self.review_calls = 0
        self.manifests = []

    def output_for(self, *, manifest, output_schema_ref, output_schema):
        self.manifests.append(manifest)
        body = manifest.body
        if manifest.role is EngineeringQuestionModelRole.QUESTION_UNDERSTANDING:
            output = {
                "preserved_original_question": body["original_question"],
                "user_goal": "Understand startup and timeout configuration.",
                "audience": "maintainer",
                "requested_abstraction_level": "USER_VISIBLE_EXPLANATION",
                "material_conclusions": [
                    "Explain startup and the effective timeout control."
                ],
                "evidence_needs": [
                    "published architecture and repository usage/configuration"
                ],
                "required_evidence_classes": ["REPOSITORY_DOCUMENT", "SOURCE"],
                "required_evidence_paths": ["README.md"],
                "response_language": body["response_language"],
                "response_constraints": ["conclusion first"],
            }
        elif manifest.role in {
            EngineeringQuestionModelRole.INITIAL_INVESTIGATION,
            EngineeringQuestionModelRole.VERIFICATION_INVESTIGATION,
        }:
            output = self._investigation_output(manifest)
        elif manifest.role is EngineeringQuestionModelRole.ANSWER:
            package = body["question_evidence_package"]
            support = package["support/citation"]
            observation_ids = [
                observation["observation_id"]
                for disposition in package["checklist_dispositions"]
                for observation in disposition["material_observations"]
            ]
            output = {
                "response_language": body["question_understanding"][
                    "response_language"
                ],
                "direct_answer": {
                    "claim_id": "claim-1",
                    "kind": "AFFIRMATIVE",
                    "content_role": "DIRECT_ANSWER",
                    "checklist_item_ids": ["check-1"],
                    "material_observation_ids": observation_ids,
                    "text": (
                        "Start the service through its documented entry point; "
                        "startup also writes a local PID file; "
                        "the request timeout is controlled by repository configuration."
                    ),
                    "evidence_entry_ids": [item["entry_id"] for item in support],
                },
                "claims": [],
            }
        else:
            self.review_calls += 1
            review_observations = self._review_observations(body)
            if self.request_more_evidence and self.review_calls == 1:
                output = {
                    "quality_assessment": {
                        "direct_answer": "PASS",
                        "abstraction_fit": "PASS",
                        "material_completeness": "PASS",
                        "claim_consistency": "PASS",
                        "implementation_detail_budget": "PASS",
                    },
                    "checklist_assessment": {
                        "independent_material_conclusions": [
                            "Explain startup and the effective timeout control."
                        ],
                        "application_checklist_omissions": [],
                        "independent_material_observations": review_observations,
                        "application_material_observation_omissions": [],
                        "draft_material_observation_omissions": [],
                    },
                    "findings": [
                        {
                            "finding_code": "CONFIGURATION_EVIDENCE_MISSING",
                            "checklist_item_id": "check-1",
                            "claim_id": "claim-1",
                            "description": (
                                "The package lacks static timeout configuration evidence."
                            ),
                            "remediation": "INVESTIGATE_MISSING_EVIDENCE",
                            "existing_evidence_entry_ids": [],
                            "evidence_class": "BUILD_CONFIGURATION",
                            "evidence_need": (
                                "Static configuration defining the request timeout"
                            ),
                        }
                    ],
                }
            else:
                output = {
                    "quality_assessment": {
                        "direct_answer": "PASS",
                        "abstraction_fit": "PASS",
                        "material_completeness": "PASS",
                        "claim_consistency": "PASS",
                        "implementation_detail_budget": "PASS",
                    },
                    "checklist_assessment": {
                        "independent_material_conclusions": [
                            "Explain startup and the effective timeout control."
                        ],
                        "application_checklist_omissions": [],
                        "independent_material_observations": review_observations,
                        "application_material_observation_omissions": [],
                        "draft_material_observation_omissions": [],
                    },
                    "findings": [],
                }
        return EngineeringQuestionRoleOutput.create(
            manifest=manifest,
            output_schema_ref=output_schema_ref,
            output_schema=output_schema,
            output_text=json.dumps(
                output,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ),
        )

    @staticmethod
    def _review_observations(body):
        package = body["question_evidence_package"]
        entry_by_source = {
            item["source_reference"]: item["entry_id"]
            for partition in ("support/citation", "boundary/audit")
            for item in package[partition]
        }
        return [
            {
                "checklist_item_id": observation["checklist_item_id"],
                "kind": observation["kind"],
                "statement": observation["statement"],
                "evidence_entry_ids": [
                    entry_by_source[reference]
                    for reference in observation["evidence_references"]
                ],
            }
            for disposition in package["checklist_dispositions"]
            for observation in disposition["material_observations"]
        ]

    @staticmethod
    def _investigation_output(manifest):
        body = manifest.body
        step = body["step_index"]
        ledger_key = (
            "evidence_ledger"
            if manifest.role is EngineeringQuestionModelRole.INITIAL_INVESTIGATION
            else "current_evidence_ledger"
        )
        last_entry_id = body[ledger_key]["entries"][-1]["entry_id"]
        results_key = (
            "typed_retrieval_results"
            if manifest.role is EngineeringQuestionModelRole.INITIAL_INVESTIGATION
            else "new_typed_retrieval_results"
        )
        results = body[results_key]
        if step == 1:
            evidence_class = (
                "REPOSITORY_DOCUMENT"
                if manifest.role is EngineeringQuestionModelRole.INITIAL_INVESTIGATION
                else "BUILD_CONFIGURATION"
            )
            return {
                "operation": "search",
                "checklist_item_ids": ["check-1"],
                "evidence_class": evidence_class,
                "query": "start" if evidence_class == "REPOSITORY_DOCUMENT" else "timeout",
                "locator_reference": None,
                "basis_entry_ids": [last_entry_id],
                "unknown_to_reduce": "Locate the next exact repository observation.",
                "finish_dispositions": [],
            }
        if step == 2:
            evidence_class = (
                "REPOSITORY_DOCUMENT"
                if manifest.role is EngineeringQuestionModelRole.INITIAL_INVESTIGATION
                else "BUILD_CONFIGURATION"
            )
            return {
                "operation": "read" if evidence_class == "REPOSITORY_DOCUMENT" else "parse",
                "checklist_item_ids": ["check-1"],
                "evidence_class": evidence_class,
                "query": None,
                "locator_reference": results[-1]["items"][0]["locator_reference"],
                "basis_entry_ids": [last_entry_id],
                "unknown_to_reduce": "Read the issued exact-revision locator.",
                "finish_dispositions": [],
            }
        evidence_reference = results[-1]["items"][0]["item_id"]
        if evidence_reference not in body["admissible_support_references"]:
            raise AssertionError("full-content item must be admissible support")
        return {
            "operation": "FINISH",
            "checklist_item_ids": ["check-1"],
            "evidence_class": None,
            "query": None,
            "locator_reference": None,
            "basis_entry_ids": [last_entry_id],
            "unknown_to_reduce": "All checklist items have an explicit disposition.",
            "finish_dispositions": [
                {
                    "checklist_item_id": "check-1",
                    "outcome": "SUPPORTED",
                    "explanation": "The exact package contains the required evidence.",
                    "material_observations": [
                        {
                            "kind": "PROCESS_STAGE",
                            "statement": (
                                "The repository evidence establishes the documented startup entry point."
                            ),
                            "evidence_references": [evidence_reference],
                        },
                        {
                            "kind": "SIDE_EFFECT",
                            "statement": (
                                "Starting the service also writes a local PID file."
                            ),
                            "evidence_references": [evidence_reference],
                        }
                    ],
                }
            ],
        }


class FixedOutputSource:
    def __init__(self, output_text):
        self.output_text = output_text

    def output_for(self, *, manifest, output_schema_ref, output_schema):
        return EngineeringQuestionRoleOutput.create(
            manifest=manifest,
            output_schema_ref=output_schema_ref,
            output_schema=output_schema,
            output_text=self.output_text,
        )


class EngineeringQuestionRoleInputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = fixtures.EngineeringQuestionAnsweringTests().service(
            request_more_evidence=False
        ).answer(fixtures.request())

    def test_question_understanding_has_no_source_authority(self):
        manifest = EngineeringQuestionRoleInputBuilder.question_understanding(
            request=self.result.request,
            role_context_id=sid("role_context", "1"),
        )
        self.assertEqual(
            manifest.role, EngineeringQuestionModelRole.QUESTION_UNDERSTANDING
        )
        self.assertEqual(
            set(manifest.body),
            {
                "original_question",
                "response_language",
                "required_output_fields",
                "authorized_evidence_paths",
                "required_evidence_path_policy",
            },
        )
        self.assertEqual(
            manifest.body["authorized_evidence_paths"],
            self.result.request.source_allowlist,
        )
        self.assertEqual(manifest.external_disclosure_status, "NOT_AUTHORIZED")
        with self.assertRaises(TypeError):
            manifest.body["original_question"] = "tampered"
        exported = manifest.gateway_input()
        exported["input"]["original_question"] = "changed copy"
        self.assertEqual(
            manifest.body["original_question"],
            self.result.request.original_question,
        )
        with self.assertRaises(DomainError) as caught:
            replace(manifest, digest=self.result.request.digest).gateway_input()
        self.assertEqual(caught.exception.code, ErrorCode.AUTHORITY_RECORD_INCONSISTENT)

    def test_initial_investigation_receives_cognition_and_sealed_prefix(self):
        ledger = EvidenceLedger.start(
            request=self.result.request, cognition=self.result.cognition
        )
        required_locator = RequiredEvidencePathLocator.create(
            attempt_id=sid("investigation_attempt", "2"),
            request_digest=self.result.request.digest,
            source_profile_digest=self.result.request.source_profile_digest,
            evidence_class=EngineeringEvidenceClass.REPOSITORY_DOCUMENT,
            path="README.md",
        )
        investigation_input = InitialInvestigationInput(
            attempt_id=sid("investigation_attempt", "2"),
            role_context_id=sid("role_context", "3"),
            step_index=1,
            request=self.result.request,
            understanding=self.result.understanding,
            cognition=self.result.cognition,
            ledger=ledger,
            retrieval_results=(),
            disposition_reference_eligibility=(
                ChecklistDispositionReferenceEligibility.create(
                    support_references=(
                        self.result.cognition.items[0].item_id.value,
                    ),
                    boundary_references=("cognition-unknown-1",),
                )
            ),
            registered_evidence_classes=(
                EngineeringEvidenceClass.SOURCE,
                EngineeringEvidenceClass.REPOSITORY_DOCUMENT,
            ),
            required_evidence_classes=(
                EngineeringEvidenceClass.SOURCE,
                EngineeringEvidenceClass.REPOSITORY_DOCUMENT,
            ),
            required_evidence_paths=("README.md",),
            required_path_locators=(required_locator,),
        )
        manifest = EngineeringQuestionRoleInputBuilder.initial_investigation(
            investigation_input
        )
        self.assertEqual(
            manifest.role, EngineeringQuestionModelRole.INITIAL_INVESTIGATION
        )
        self.assertIn("world_model_cognition_context", manifest.body)
        self.assertIn("evidence_ledger", manifest.body)
        self.assertNotIn("question_evidence_package", manifest.body)
        self.assertEqual(
            manifest.body["required_basis_entry_id"],
            ledger.entries[-1].entry_id.value,
        )
        self.assertEqual(
            manifest.body["eligible_locator_references"],
            (required_locator.locator_reference.value,),
        )
        self.assertEqual(
            manifest.body["eligible_required_path_locators"],
            (required_locator.model_view(),),
        )
        self.assertEqual(manifest.body["consumed_full_content_paths"], ())
        self.assertEqual(manifest.body["maximum_initial_investigation_calls"], 12)
        self.assertEqual(
            manifest.body[
                "remaining_initial_investigation_calls_including_current"
            ],
            12,
        )
        self.assertEqual(manifest.body["prior_action_intents"], ())
        self.assertEqual(
            manifest.body["registered_evidence_classes"],
            ("SOURCE", "REPOSITORY_DOCUMENT"),
        )
        self.assertEqual(manifest.body["investigated_evidence_classes"], ())
        self.assertEqual(
            manifest.body["required_evidence_classes"],
            ("SOURCE", "REPOSITORY_DOCUMENT"),
        )
        self.assertEqual(
            manifest.body["untried_required_evidence_classes"],
            ("SOURCE", "REPOSITORY_DOCUMENT"),
        )
        self.assertEqual(
            manifest.body["unregistered_required_evidence_classes"],
            (),
        )
        self.assertEqual(manifest.body["required_evidence_paths"], ("README.md",))
        self.assertEqual(
            manifest.body["unread_required_evidence_paths"],
            ("README.md",),
        )
        complete_result = self.result.retrieval_results[1]
        complete_item = complete_result.items[0]
        partial_item = RetrievalItem.create(
            operation_id=complete_item.operation_id,
            ordinal=complete_item.ordinal,
            evidence_class=complete_item.evidence_class,
            path=complete_item.path,
            content=complete_item.content,
            modality=complete_item.modality,
            coverage_complete=False,
        )
        partial_input = replace(
            investigation_input,
            retrieval_results=(replace(complete_result, items=(partial_item,)),),
        )
        self.assertEqual(partial_input.consumed_full_content_paths, ())
        self.assertEqual(
            partial_input.unread_required_evidence_paths,
            ("README.md",),
        )
        self.assertEqual(
            manifest.body["admissible_support_references"],
            (self.result.cognition.items[0].item_id.value,),
        )
        self.assertEqual(
            manifest.body["admissible_boundary_references"],
            ("cognition-unknown-1",),
        )
        self.assertEqual(
            manifest.body["request"]["source_profile_digest"],
            self.result.request.source_profile_digest.value,
        )

    def test_answer_and_review_only_receive_current_package(self):
        package = self.result.current_package
        draft = self.result.current_draft
        answer = EngineeringQuestionRoleInputBuilder.answer(
            original_question=self.result.request.original_question,
            understanding=self.result.understanding,
            package=package,
            role_context_id=sid("role_context", "4"),
        )
        review = EngineeringQuestionRoleInputBuilder.review(
            original_question=self.result.request.original_question,
            understanding=self.result.understanding,
            package=package,
            draft=draft,
            role_context_id=sid("role_context", "5"),
        )
        self.assertNotIn("evidence_ledger", answer.body)
        self.assertNotIn("world_model_cognition_context", answer.body)
        self.assertNotIn("evidence_ledger", review.body)
        self.assertEqual(
            answer.body["question_evidence_package"]["package_digest"],
            package.digest.value,
        )
        self.assertEqual(review.body["draft"]["digest"], draft.digest.value)
        self.assertEqual(
            answer.body["answer_structure_contract"]["required_first_role"],
            "DIRECT_ANSWER",
        )
        self.assertEqual(
            answer.body["answer_structure_contract"][
                "maximum_direct_answer_claims"
            ],
            1,
        )
        self.assertEqual(
            answer.body["answer_structure_contract"][
                "mixed_disposition_direct_answer_policy"
            ],
            "AFFIRMATIVE_DIRECT_SUMMARY_FOR_SUPPORTED_ITEMS_THEN_FINAL_LIMITATION_CLAIMS_FOR_NON_SUPPORTED_ITEMS",
        )
        self.assertEqual(
            answer.body["answer_structure_contract"][
                "allowed_kind_by_content_role"
            ],
            {
                "DIRECT_ANSWER": ("AFFIRMATIVE", "LIMITATION"),
                "USER_VISIBLE_PROCESS": ("AFFIRMATIVE",),
                "IMPACT_OR_SIDE_EFFECT": ("AFFIRMATIVE",),
                "IMPLEMENTATION_EVIDENCE": ("AFFIRMATIVE",),
                "LIMITATION": ("LIMITATION",),
            },
        )
        self.assertTrue(
            answer.body["answer_structure_contract"][
                "implementation_evidence_unique_material_observation_visible"
            ]
        )
        self.assertEqual(
            review.body["answer_structure"]["first_content_role"],
            "DIRECT_ANSWER",
        )
        self.assertEqual(
            review.body["answer_structure"]["material_checklist_coverage"],
            {"check-1": ("claim-1",)},
        )
        forbidden = {
            "repository_root",
            "credential",
            "secret",
            "shell",
            "network",
            "source_tool",
            "broker_dispatch",
            "ledger_write_port",
        }
        self.assertFalse(collect_keys(answer.gateway_input()) & forbidden)
        self.assertFalse(collect_keys(review.gateway_input()) & forbidden)

    def test_verification_input_is_gap_plus_current_package_and_ledger(self):
        package = self.result.current_package
        verification = VerificationRequestProposal.create(
            package_digest=package.digest,
            checklist_item_id="check-1",
            evidence_class=EngineeringEvidenceClass.TEST,
            evidence_need="Static test expectation for the documented behavior",
        )
        ledger = self.result.ledgers[-1].successor(
            verification_request_id=verification.verification_request_id,
            verification_request_digest=verification.digest,
            prior_package_digest=package.digest,
            maximum_bytes=self.result.request.limits.maximum_ledger_bytes,
        )
        investigation_input = VerificationInvestigationInput(
            attempt_id=sid("verification_attempt", "6"),
            role_context_id=sid("role_context", "7"),
            step_index=1,
            verification_request=verification,
            current_package=package,
            ledger=ledger,
            retrieval_results=(),
            disposition_reference_eligibility=(
                ChecklistDispositionReferenceEligibility.create(
                    support_references=tuple(
                        item.source_reference for item in package.support_citation
                    ),
                    boundary_references=tuple(
                        item.source_reference for item in package.boundary_audit
                    )
                    + (ledger.entries[-1].entry_id.value,),
                )
            ),
            registered_evidence_classes=(EngineeringEvidenceClass.TEST,),
            required_evidence_classes=(EngineeringEvidenceClass.TEST,),
        )
        manifest = EngineeringQuestionRoleInputBuilder.verification_investigation(
            investigation_input
        )
        self.assertEqual(
            manifest.role,
            EngineeringQuestionModelRole.VERIFICATION_INVESTIGATION,
        )
        self.assertEqual(
            set(manifest.body),
            {
                "role",
                "attempt_id",
                "role_context_id",
                "step_index",
                "required_basis_entry_id",
                "eligible_locator_references",
                "eligible_required_path_locators",
                "consumed_full_content_paths",
                "prior_action_intents",
                "registered_evidence_classes",
                "required_evidence_classes",
                "investigated_evidence_classes",
                "untried_required_evidence_classes",
                "unregistered_required_evidence_classes",
                "required_evidence_paths",
                "unread_required_evidence_paths",
                "admissible_support_references",
                "admissible_boundary_references",
                "verification_request",
                "current_question_evidence_package",
                "current_evidence_ledger",
                "new_typed_retrieval_results",
            },
        )
        self.assertNotIn("world_model_cognition_context", manifest.body)
        self.assertEqual(manifest.body["new_typed_retrieval_results"], ())
        self.assertEqual(
            manifest.body["required_basis_entry_id"],
            ledger.entries[-1].entry_id.value,
        )
        self.assertEqual(manifest.body["eligible_locator_references"], ())
        self.assertEqual(manifest.body["eligible_required_path_locators"], ())
        self.assertEqual(manifest.body["consumed_full_content_paths"], ())
        self.assertEqual(
            manifest.body["untried_required_evidence_classes"],
            ("TEST",),
        )
        self.assertEqual(manifest.body["unregistered_required_evidence_classes"], ())
        self.assertEqual(manifest.body["prior_action_intents"], ())
        self.assertEqual(
            set(manifest.body["admissible_support_references"]),
            {item.source_reference for item in package.support_citation},
        )
        self.assertIn(
            ledger.entries[-1].entry_id.value,
            manifest.body["admissible_boundary_references"],
        )

        with self.assertRaises(DomainError) as caught:
            EngineeringQuestionRoleInputBuilder.verification_investigation(
                replace(
                    investigation_input,
                    retrieval_results=self.result.retrieval_results,
                )
            )
        self.assertEqual(caught.exception.code, ErrorCode.AUTHORITY_RECORD_INCONSISTENT)

        with self.assertRaises(DomainError) as predecessor_error:
            EngineeringQuestionRoleInputBuilder.verification_investigation(
                replace(
                    investigation_input,
                    current_package=replace(
                        package,
                        digest=Digest("sha256:" + "f" * 64),
                    ),
                )
            )
        self.assertEqual(
            predecessor_error.exception.code,
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
        )

    def test_all_five_output_contracts_are_closed_and_fingerprinted(self):
        schemas = engineering_question_output_schemas()
        self.assertEqual(
            set(schemas),
            {
                ENGINEERING_QUESTION_UNDERSTANDING_OUTPUT_SCHEMA_REF,
                ENGINEERING_QUESTION_INITIAL_INVESTIGATION_OUTPUT_SCHEMA_REF,
                ENGINEERING_QUESTION_VERIFICATION_INVESTIGATION_OUTPUT_SCHEMA_REF,
                ENGINEERING_QUESTION_ANSWER_OUTPUT_SCHEMA_REF,
                ENGINEERING_QUESTION_REVIEW_OUTPUT_SCHEMA_REF,
            },
        )
        for definition in schemas.values():
            self.assertFalse(definition.schema["additionalProperties"])
        answer_claims = schemas[
            ENGINEERING_QUESTION_ANSWER_OUTPUT_SCHEMA_REF
        ].schema["properties"]["claims"]["items"]
        self.assertEqual(len(answer_claims["anyOf"]), 2)
        for answer_claim in answer_claims["anyOf"]:
            self.assertIn("content_role", answer_claim["required"])
            self.assertIn("checklist_item_ids", answer_claim["required"])
            self.assertIn("material_observation_ids", answer_claim["required"])
            observation_links = answer_claim["properties"][
                "material_observation_ids"
            ]
            self.assertTrue(observation_links["uniqueItems"])
            self.assertNotIn("minItems", observation_links)
            evidence_links = answer_claim["properties"]["evidence_entry_ids"]
            self.assertEqual(evidence_links["minItems"], 1)
            self.assertTrue(evidence_links["uniqueItems"])
        review = schemas[ENGINEERING_QUESTION_REVIEW_OUTPUT_SCHEMA_REF].schema
        self.assertIn("quality_assessment", review["required"])
        self.assertIn("checklist_assessment", review["required"])
        self.assertNotIn("decision", review["properties"])
        self.assertNotIn("verification_request", review["properties"])
        review_finding_variants = review["properties"]["findings"]["items"][
            "anyOf"
        ]
        self.assertEqual(len(review_finding_variants), 3)
        self.assertEqual(
            {
                item["properties"]["remediation"]["enum"][0]
                for item in review_finding_variants
            },
            {
                "REWRITE_WITH_EXISTING_EVIDENCE",
                "INVESTIGATE_MISSING_EVIDENCE",
                "REJECT_UNRECOVERABLE",
            },
        )
        self.assertEqual(
            set(
                review["properties"]["quality_assessment"]["properties"]
            ),
            {
                "direct_answer",
                "abstraction_fit",
                "material_completeness",
                "claim_consistency",
                "implementation_detail_budget",
            },
        )
        for schema_ref in (
            ENGINEERING_QUESTION_INITIAL_INVESTIGATION_OUTPUT_SCHEMA_REF,
            ENGINEERING_QUESTION_VERIFICATION_INVESTIGATION_OUTPUT_SCHEMA_REF,
        ):
            properties = schemas[schema_ref].schema["properties"]
            variants = properties["finish_dispositions"]["items"]["anyOf"]
            self.assertIn(
                "only FINISH disposition list",
                properties["finish_dispositions"]["description"],
            )
            for variant in variants:
                self.assertNotIn(
                    "evidence_references", variant["properties"]
                )
                observations = variant["properties"]["material_observations"]
                self.assertEqual(observations["minItems"], 1)
                self.assertEqual(observations["maxItems"], 16)
                references = observations["items"]["properties"][
                    "evidence_references"
                ]
                self.assertEqual(references["minItems"], 1)
                self.assertTrue(references["uniqueItems"])
            self.assertEqual(
                variants[0]["properties"]["outcome"]["enum"],
                ["SUPPORTED"],
            )
            self.assertEqual(
                variants[0]["properties"]["material_observations"]["items"]
                ["properties"]["kind"]["enum"],
                ["PROCESS_STAGE", "OUTCOME", "STATE_CHANGE", "SIDE_EFFECT"],
            )
            self.assertEqual(
                variants[1]["properties"]["outcome"]["enum"],
                ["UNKNOWN", "CONFLICT", "FAILED"],
            )
            self.assertEqual(
                variants[1]["properties"]["material_observations"]["items"]
                ["properties"]["kind"]["enum"],
                ["LIMITATION"],
            )
        understanding_required = schemas[
            ENGINEERING_QUESTION_UNDERSTANDING_OUTPUT_SCHEMA_REF
        ].schema["properties"]["required_evidence_classes"]
        self.assertEqual(understanding_required["minItems"], 1)
        self.assertEqual(understanding_required["maxItems"], 4)
        self.assertTrue(understanding_required["uniqueItems"])
        understanding_paths = schemas[
            ENGINEERING_QUESTION_UNDERSTANDING_OUTPUT_SCHEMA_REF
        ].schema["properties"]["required_evidence_paths"]
        self.assertEqual(understanding_paths["minItems"], 1)
        self.assertEqual(understanding_paths["maxItems"], 4)
        self.assertTrue(understanding_paths["uniqueItems"])
        review_checklist = review["properties"]["checklist_assessment"]
        self.assertIn(
            "independent_material_observations",
            review_checklist["required"],
        )
        self.assertIn(
            "draft_material_observation_omissions",
            review_checklist["required"],
        )
        self.assertEqual(
            engineering_question_output_contract_digest(),
            engineering_question_output_contract_digest(),
        )
        schemas[ENGINEERING_QUESTION_ANSWER_OUTPUT_SCHEMA_REF].schema[
            "properties"
        ]["unexpected"] = {"type": "string"}
        self.assertNotIn(
            "unexpected",
            engineering_question_output_schemas()[
                ENGINEERING_QUESTION_ANSWER_OUTPUT_SCHEMA_REF
            ].schema["properties"],
        )

    def test_finish_schema_rejects_outcome_observation_category_mixing(self):
        schema = engineering_question_output_schemas()[
            ENGINEERING_QUESTION_INITIAL_INVESTIGATION_OUTPUT_SCHEMA_REF
        ]

        def output(*, outcome, observation_kind):
            disposition = {
                "checklist_item_id": "check-1",
                "outcome": outcome,
                "explanation": "The disposition is explicit.",
                "material_observations": [
                    {
                        "kind": observation_kind,
                        "statement": "One atomic observation.",
                        "evidence_references": ["evidence-1"],
                    }
                ],
            }
            return json.dumps(
                {
                    "operation": "FINISH",
                    "checklist_item_ids": ["check-1"],
                    "evidence_class": None,
                    "query": None,
                    "locator_reference": None,
                    "basis_entry_ids": ["ledger-entry-1"],
                    "unknown_to_reduce": "The item has a final disposition.",
                    "finish_dispositions": [disposition],
                }
            )

        schema.validate_output_text(
            output(outcome="SUPPORTED", observation_kind="PROCESS_STAGE")
        )
        schema.validate_output_text(
            output(outcome="UNKNOWN", observation_kind="LIMITATION")
        )
        for outcome, observation_kind in (
            ("SUPPORTED", "LIMITATION"),
            ("UNKNOWN", "PROCESS_STAGE"),
        ):
            with self.assertRaises(DomainError) as caught:
                schema.validate_output_text(
                    output(outcome=outcome, observation_kind=observation_kind)
                )
            self.assertEqual(
                caught.exception.code, ErrorCode.STRUCTURED_OUTPUT_INVALID
            )

        legacy_partition = json.loads(
            output(outcome="UNKNOWN", observation_kind="LIMITATION")
        )
        legacy_partition["supported_finish_dispositions"] = []
        with self.assertRaises(DomainError) as caught:
            schema.validate_output_text(json.dumps(legacy_partition))
        self.assertEqual(caught.exception.code, ErrorCode.STRUCTURED_OUTPUT_INVALID)

    def test_finish_adapter_derives_parent_reference_closure_from_children(self):
        disposition = strategy_contract._provider_finish_disposition(
            {
                "checklist_item_id": "check-1",
                "outcome": "SUPPORTED",
                "explanation": "Two observations require two exact sources.",
                "material_observations": [
                    {
                        "kind": "PROCESS_STAGE",
                        "statement": "The first stage is established.",
                        "evidence_references": ["evidence-1"],
                    },
                    {
                        "kind": "OUTCOME",
                        "statement": "The outcome combines both sources.",
                        "evidence_references": ["evidence-2", "evidence-1"],
                    },
                ],
            }
        )

        self.assertEqual(
            disposition.evidence_references,
            ("evidence-1", "evidence-2"),
        )
        self.assertEqual(
            [item.evidence_references for item in disposition.material_observations],
            [("evidence-1",), ("evidence-2", "evidence-1")],
        )

    def test_investigation_schema_rejects_empty_or_duplicate_binding_arrays(self):
        valid = {
            "operation": "read",
            "checklist_item_ids": ["check-1"],
            "evidence_class": "SOURCE",
            "query": None,
            "locator_reference": "required-path-locator-1",
            "basis_entry_ids": ["ledger-entry-1"],
            "unknown_to_reduce": "Read one decisive implementation path.",
            "finish_dispositions": [],
        }
        for schema_ref in (
            ENGINEERING_QUESTION_INITIAL_INVESTIGATION_OUTPUT_SCHEMA_REF,
            ENGINEERING_QUESTION_VERIFICATION_INVESTIGATION_OUTPUT_SCHEMA_REF,
        ):
            schema = engineering_question_output_schemas()[schema_ref]
            schema.validate_output_text(json.dumps(valid))

            for field, value in (
                ("checklist_item_ids", []),
                ("checklist_item_ids", ["check-1", "check-1"]),
                ("basis_entry_ids", []),
                ("basis_entry_ids", ["ledger-entry-1", "ledger-entry-1"]),
            ):
                invalid = dict(valid)
                invalid[field] = value
                with self.assertRaises(DomainError) as caught:
                    schema.validate_output_text(json.dumps(invalid))
                self.assertEqual(
                    caught.exception.code,
                    ErrorCode.STRUCTURED_OUTPUT_INVALID,
                )

    def test_answer_schema_rejects_kind_and_content_role_mixing(self):
        schema = engineering_question_output_schemas()[
            ENGINEERING_QUESTION_ANSWER_OUTPUT_SCHEMA_REF
        ]

        def claim(*, kind, content_role):
            return {
                "claim_id": "claim-1",
                "kind": kind,
                "content_role": content_role,
                "checklist_item_ids": ["check-1"],
                "material_observation_ids": [],
                "text": "One closed claim.",
                "evidence_entry_ids": ["support-entry-1"],
            }

        def output(*, direct_kind="AFFIRMATIVE", followup=None):
            return json.dumps(
                {
                    "response_language": "en",
                    "direct_answer": claim(
                        kind=direct_kind,
                        content_role="DIRECT_ANSWER",
                    ),
                    "claims": [] if followup is None else [followup],
                }
            )

        schema.validate_output_text(output())
        schema.validate_output_text(output(direct_kind="LIMITATION"))
        schema.validate_output_text(output(followup=claim(
            kind="AFFIRMATIVE", content_role="USER_VISIBLE_PROCESS"
        )))
        schema.validate_output_text(output(followup=claim(
            kind="LIMITATION", content_role="LIMITATION"
        )))
        for kind, content_role in (
            ("LIMITATION", "USER_VISIBLE_PROCESS"),
            ("AFFIRMATIVE", "LIMITATION"),
            ("AFFIRMATIVE", "DIRECT_ANSWER"),
            ("LIMITATION", "DIRECT_ANSWER"),
        ):
            with self.assertRaises(DomainError) as caught:
                schema.validate_output_text(
                    output(followup=claim(kind=kind, content_role=content_role))
                )
            self.assertEqual(
                caught.exception.code, ErrorCode.STRUCTURED_OUTPUT_INVALID
            )

    def test_answer_adapter_stably_canonicalizes_supporting_role_order(self):
        support_entry_id = (
            self.result.current_package.support_citation[0].entry_id.value
        )

        def claim(claim_id, content_role, observation_digit):
            return {
                "claim_id": claim_id,
                "kind": "AFFIRMATIVE",
                "content_role": content_role,
                "checklist_item_ids": ["check-1"],
                "material_observation_ids": [
                    sid("material_observation", observation_digit).value
                ],
                "text": f"Evidence-bound {content_role} claim {claim_id}.",
                "evidence_entry_ids": [support_entry_id],
            }

        output = {
            "response_language": self.result.understanding.response_language,
            "direct_answer": {
                "claim_id": "direct-answer",
                "kind": "AFFIRMATIVE",
                "content_role": "DIRECT_ANSWER",
                "checklist_item_ids": ["check-1"],
                "material_observation_ids": [],
                "text": "Direct supported summary.",
                "evidence_entry_ids": [support_entry_id],
            },
            "claims": [
                claim("impact", "IMPACT_OR_SIDE_EFFECT", "1"),
                claim("process-a", "USER_VISIBLE_PROCESS", "2"),
                claim("process-b", "USER_VISIBLE_PROCESS", "3"),
            ],
        }
        role = StructuredEngineeringAnswerRole(
            FixedOutputSource(json.dumps(output))
        )

        proposal = role.generate(
            original_question=self.result.request.original_question,
            understanding=self.result.understanding,
            package=self.result.current_package,
            role_context_id=sid("role_context", "8"),
        )

        self.assertEqual(
            [item.claim_id for item in proposal.claims],
            ["direct-answer", "process-a", "process-b", "impact"],
        )
        self.assertEqual(
            [item.content_role.value for item in proposal.claims],
            [
                "DIRECT_ANSWER",
                "USER_VISIBLE_PROCESS",
                "USER_VISIBLE_PROCESS",
                "IMPACT_OR_SIDE_EFFECT",
            ],
        )

    def test_structured_roles_run_the_complete_local_state_machine(self):
        output_source = AdaptiveStructuredOutputSource(request_more_evidence=True)
        bundle = EngineeringQuestionStructuredStrategyBundle.create(output_source)
        service = EngineeringQuestionAnsweringService(
            question_understanding_role=bundle.question_understanding,
            cognition_projector=fixtures.CognitionProjector(),
            initial_investigation_role=bundle.initial_investigation,
            verification_investigation_role=bundle.verification_investigation,
            source_broker=SourceBroker(
                source_profile=fixtures.source_profile()
            ),
            retrieval_worker=fixtures.ScriptedWorker(),
            answer_role=bundle.answer,
            reviewer_role=bundle.reviewer,
        )

        result = service.answer(fixtures.request())

        self.assertEqual(result.status, EngineeringQuestionResultStatus.APPROVED)
        self.assertEqual(len(result.packages), 2)
        self.assertEqual(len(result.ledgers), 2)
        self.assertEqual(output_source.review_calls, 2)
        self.assertEqual(
            bundle.output_contract_digest,
            engineering_question_output_contract_digest(),
        )
        role_ids = {
            id(bundle.question_understanding),
            id(bundle.initial_investigation),
            id(bundle.verification_investigation),
            id(bundle.answer),
            id(bundle.reviewer),
        }
        self.assertEqual(len(role_ids), 5)
        self.assertTrue(
            all(
                manifest.external_disclosure_status == "NOT_AUTHORIZED"
                for manifest in output_source.manifests
            )
        )
        initial_manifests = [
            manifest
            for manifest in output_source.manifests
            if manifest.role is EngineeringQuestionModelRole.INITIAL_INVESTIGATION
        ]
        self.assertEqual(
            len(initial_manifests[0].body["eligible_locator_references"]),
            1,
        )
        self.assertEqual(
            len(initial_manifests[0].body["eligible_required_path_locators"]),
            1,
        )
        self.assertEqual(
            len(initial_manifests[1].body["eligible_locator_references"]),
            2,
        )
        self.assertEqual(
            initial_manifests[1].body["prior_action_intents"][0]["operation"],
            "search",
        )
        self.assertEqual(
            initial_manifests[1].body["prior_action_intents"][0]["query"],
            "start",
        )
        self.assertEqual(
            initial_manifests[1].body["prior_action_intents"][0][
                "evidence_class"
            ],
            "REPOSITORY_DOCUMENT",
        )
        self.assertEqual(initial_manifests[2].body["eligible_locator_references"], ())
        self.assertEqual(
            initial_manifests[2].body["consumed_full_content_paths"],
            ("README.md",),
        )
        initial_support = set(
            initial_manifests[2].body["admissible_support_references"]
        )
        full_content_item_id = initial_manifests[2].body[
            "typed_retrieval_results"
        ][-1]["items"][0]["item_id"]
        self.assertIn(full_content_item_id, initial_support)
        self.assertNotIn(
            initial_manifests[2].body["required_basis_entry_id"],
            initial_support,
        )
        verification_manifests = [
            manifest
            for manifest in output_source.manifests
            if manifest.role
            is EngineeringQuestionModelRole.VERIFICATION_INVESTIGATION
        ]
        self.assertEqual(
            verification_manifests[0].body["new_typed_retrieval_results"],
            (),
        )
        self.assertNotIn(
            "typed_retrieval_results", verification_manifests[0].body
        )

    def test_stale_role_output_receipt_is_rejected(self):
        req = fixtures.request()

        class StaleSource:
            receipt = None

            def output_for(
                self, *, manifest, output_schema_ref, output_schema
            ):
                if self.receipt is None:
                    body = {
                        "preserved_original_question": req.original_question,
                        "user_goal": "Understand startup.",
                        "audience": "maintainer",
                        "requested_abstraction_level": "DIRECT",
                        "material_conclusions": ["Explain startup."],
                        "evidence_needs": ["Exact startup evidence."],
                        "required_evidence_classes": ["SOURCE"],
                        "required_evidence_paths": ["src/Service.java"],
                        "response_language": req.response_language,
                        "response_constraints": [],
                    }
                    self.receipt = EngineeringQuestionRoleOutput.create(
                        manifest=manifest,
                        output_schema_ref=output_schema_ref,
                        output_schema=output_schema,
                        output_text=json.dumps(body),
                    )
                return self.receipt

        role = StructuredQuestionUnderstandingRole(StaleSource())
        role.understand(request=req, role_context_id=sid("role_context", "8"))
        with self.assertRaises(DomainError) as caught:
            role.understand(
                request=req,
                role_context_id=sid("role_context", "9"),
            )
        self.assertEqual(caught.exception.code, ErrorCode.AUTHORITY_RECORD_INCONSISTENT)

    def test_extra_or_duplicate_output_fields_fail_closed(self):
        req = fixtures.request()
        valid = {
            "preserved_original_question": req.original_question,
            "user_goal": "Understand startup.",
            "audience": "maintainer",
            "requested_abstraction_level": "DIRECT",
            "material_conclusions": ["Explain startup."],
            "evidence_needs": ["Exact startup evidence."],
            "required_evidence_classes": ["SOURCE"],
            "required_evidence_paths": ["src/Service.java"],
            "response_language": req.response_language,
            "response_constraints": [],
        }
        extra = dict(valid, repository_root="/tmp/repository")
        with self.assertRaises(DomainError) as extra_error:
            StructuredQuestionUnderstandingRole(
                FixedOutputSource(json.dumps(extra))
            ).understand(
                request=req,
                role_context_id=sid("role_context", "a"),
            )
        self.assertEqual(extra_error.exception.code, ErrorCode.STRUCTURED_OUTPUT_INVALID)

        duplicate = json.dumps(valid)[:-1] + ',"audience":"attacker"}'
        with self.assertRaises(DomainError) as duplicate_error:
            StructuredQuestionUnderstandingRole(
                FixedOutputSource(duplicate)
            ).understand(
                request=req,
                role_context_id=sid("role_context", "b"),
            )
        self.assertEqual(
            duplicate_error.exception.code,
            ErrorCode.STRUCTURED_OUTPUT_INVALID,
        )

    def test_review_verification_request_cannot_smuggle_an_operation(self):
        package = self.result.current_package
        draft = self.result.current_draft
        output = {
            "quality_assessment": {
                "direct_answer": "PASS",
                "abstraction_fit": "PASS",
                "material_completeness": "PASS",
                "claim_consistency": "PASS",
                "implementation_detail_budget": "PASS",
            },
            "checklist_assessment": {
                "independent_material_conclusions": ["Explain startup."],
                "application_checklist_omissions": [],
                "independent_material_observations": (
                    AdaptiveStructuredOutputSource._review_observations(
                        {
                            "question_evidence_package": package.model_view()
                        }
                    )
                ),
                "application_material_observation_omissions": [],
                "draft_material_observation_omissions": [],
            },
            "findings": [
                {
                    "finding_code": "EVIDENCE_MISSING",
                    "checklist_item_id": "check-1",
                    "claim_id": "claim-1",
                    "description": "The exact evidence is missing.",
                    "remediation": "INVESTIGATE_MISSING_EVIDENCE",
                    "existing_evidence_entry_ids": [],
                    "evidence_class": "SOURCE",
                    "evidence_need": "read(src/main.py)",
                }
            ],
        }
        role = StructuredEngineeringAnswerReviewerRole(
            FixedOutputSource(json.dumps(output))
        )
        with self.assertRaises(DomainError) as caught:
            role.review(
                original_question=self.result.request.original_question,
                understanding=self.result.understanding,
                package=package,
                draft=draft,
                role_context_id=sid("role_context", "c"),
            )
        self.assertEqual(caught.exception.code, ErrorCode.PROVIDER_OUTPUT_FORBIDDEN)

    def test_output_receipt_identity_tampering_is_rejected(self):
        req = fixtures.request()

        class TamperedSource(FixedOutputSource):
            def output_for(
                self, *, manifest, output_schema_ref, output_schema
            ):
                receipt = super().output_for(
                    manifest=manifest,
                    output_schema_ref=output_schema_ref,
                    output_schema=output_schema,
                )
                return replace(
                    receipt,
                    output_text_digest=receipt.input_manifest_digest,
                )

        output = {
            "preserved_original_question": req.original_question,
            "user_goal": "Understand startup.",
            "audience": "maintainer",
            "requested_abstraction_level": "DIRECT",
            "material_conclusions": ["Explain startup."],
            "evidence_needs": ["Exact startup evidence."],
            "required_evidence_classes": ["SOURCE"],
            "required_evidence_paths": ["src/Service.java"],
            "response_language": req.response_language,
            "response_constraints": [],
        }
        with self.assertRaises(DomainError) as caught:
            StructuredQuestionUnderstandingRole(
                TamperedSource(json.dumps(output))
            ).understand(
                request=req,
                role_context_id=sid("role_context", "d"),
            )
        self.assertEqual(caught.exception.code, ErrorCode.AUTHORITY_RECORD_INCONSISTENT)


if __name__ == "__main__":
    unittest.main()
