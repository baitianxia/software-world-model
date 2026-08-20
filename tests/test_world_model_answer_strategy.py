from __future__ import annotations

import json
from types import SimpleNamespace
import unittest

from software_world_model.ai_infrastructure import (
    GENERIC_QUERY_PLANNING,
    IMPLEMENTATION_ANSWER_DRAFTING,
    IMPLEMENTATION_ANSWER_REVIEW,
    IMPLEMENTATION_INVESTIGATION,
    IMPLEMENTATION_QUERY_PLANNING,
    JAVA_SOURCE_SEMANTICS_INVESTIGATION_ARGUMENT_COMPILER_REF,
    JAVA_SOURCE_SEMANTICS_FIXED_WORLD_MODEL_PROPOSAL_CONTRACT,
    JAVA_SOURCE_SEMANTICS_REVIEW_FINDING_CODES,
    JAVA_SOURCE_SEMANTICS_TERMINAL_AUTHORITY_COMPILER_REF,
    JAVA_SOURCE_SEMANTICS_WORLD_MODEL_PROPOSAL_CONTRACT,
    JAVA_WORLD_MODEL_ANSWER_PROMPT_REF,
    JAVA_WORLD_MODEL_PROPOSAL_CONTRACT,
    MAVEN_WORLD_MODEL_PROPOSAL_CONTRACT,
    WORLD_MODEL_CAPABILITIES,
    WorldModelCapabilityStrategy,
    WorldModelStrategyConfiguration,
    world_model_answer_output_contract_digest,
    world_model_answer_output_schemas,
    java_source_semantics_world_model_output_contract_digest,
    world_model_answer_prompt_program_digest,
    world_model_answer_strategy_implementation_digest,
)
from software_world_model.cross_cutting import Digest, DomainError, StableId, digest_of
from validation.structure_world_model_iteration_003.v009.manifest import (
    load_capability_suite,
)


class SequencedGateway:
    def __init__(self, outputs):
        self.outputs = list(outputs)
        self.contexts = []

    def invoke(self, context):
        self.contexts.append(context)
        value = self.outputs.pop(0)
        if isinstance(value, SimpleNamespace):
            return value
        output_text = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        index = len(self.contexts)
        return SimpleNamespace(
            call=SimpleNamespace(
                model_call_id=StableId(f"model_call_{index:032x}"),
                failure_code=None,
            ),
            response=SimpleNamespace(
                output_text=output_text,
                output_digest=digest_of(output_text),
            ),
            isolation_receipt=SimpleNamespace(
                manifest_digest=context.manifest.digest,
                provider_request_digest=digest_of({"request": index}),
            ),
            eligibility=SimpleNamespace(
                eligible_for_production_domain_output=True,
                reason="ELIGIBLE",
            ),
        )


def configuration():
    return WorldModelStrategyConfiguration(
        provider_type="TEST",
        adapter_version="test-no-tools@1",
        model_ref="fixture-model",
        provider_configuration_fingerprint=Digest("sha256:" + "1" * 64),
        qualification_ref="evaluation-only:fixture-conformance",
    )


def ordered_behavior_query_results():
    return [
        {
            "operation": "METHOD_IMPLEMENTATION",
            "payload": {
                "canonical_signature": "dev.acme.auth.LoginService#authenticate(boolean)",
                "method": {"root_id": "method-authenticate"},
                "state_slots": [
                    {
                        "root_id": "slot-credentials-valid",
                        "root_fields": {
                            "canonical_identifier": "credentialsValid"
                        },
                    }
                ],
                "ordered_atoms": [
                    {
                        "root_id": "atom-branch",
                        "root_fields": {
                            "atom_kind": "BRANCH",
                            "structural_ordinal": 0,
                        },
                        "state_fields": {
                            "operator": "NOT",
                            "semantic_form": "BOOLEAN_SLOT_TEST",
                            "semantic_operands": [
                                {
                                    "kind": "ENTITY_REF",
                                    "value": "slot-credentials-valid",
                                }
                            ],
                            "referenced_entity_root_ids": [
                                "slot-credentials-valid"
                            ],
                            "source_order_ordinal": 0,
                            "value_category": "BOOLEAN",
                        },
                    },
                    {
                        "root_id": "atom-record-1",
                        "root_fields": {
                            "atom_kind": "CALL_SITE",
                            "structural_ordinal": 1,
                        },
                        "state_fields": {
                            "operator": "DIRECT_CALL",
                            "semantic_form": "STATIC_CALL",
                            "semantic_operands": [
                                {
                                    "kind": "ENTITY_REF",
                                    "value": "method-record-failure",
                                }
                            ],
                            "referenced_entity_root_ids": [
                                "method-record-failure"
                            ],
                            "source_order_ordinal": 1,
                            "value_category": "VOID",
                        },
                    },
                    {
                        "root_id": "atom-record-2",
                        "root_fields": {
                            "atom_kind": "CALL_SITE",
                            "structural_ordinal": 2,
                        },
                        "state_fields": {
                            "operator": "DIRECT_CALL",
                            "semantic_form": "STATIC_CALL",
                            "semantic_operands": [
                                {
                                    "kind": "ENTITY_REF",
                                    "value": "method-record-failure",
                                }
                            ],
                            "referenced_entity_root_ids": [
                                "method-record-failure"
                            ],
                            "source_order_ordinal": 2,
                            "value_category": "VOID",
                        },
                    },
                    {
                        "root_id": "atom-throw",
                        "root_fields": {
                            "atom_kind": "THROW",
                            "structural_ordinal": 3,
                        },
                        "state_fields": {
                            "operator": "THROW",
                            "semantic_form": "THROW_CONSTRUCTION",
                            "semantic_operands": [
                                {
                                    "kind": "TYPE_REF",
                                    "value": "java.lang.IllegalStateException",
                                },
                                {"kind": "CONSTRUCTOR_ARITY", "value": 0},
                            ],
                            "referenced_entity_root_ids": [],
                            "source_order_ordinal": 3,
                            "value_category": "EXCEPTION",
                        },
                    },
                    {
                        "root_id": "atom-issue-session",
                        "root_fields": {
                            "atom_kind": "CALL_SITE",
                            "structural_ordinal": 4,
                        },
                        "state_fields": {
                            "operator": "DIRECT_CALL",
                            "semantic_form": "STATIC_CALL",
                            "semantic_operands": [
                                {
                                    "kind": "ENTITY_REF",
                                    "value": "method-issue-session",
                                }
                            ],
                            "referenced_entity_root_ids": [
                                "method-issue-session"
                            ],
                            "source_order_ordinal": 4,
                            "value_category": "CALL_RESULT",
                        },
                    },
                    {
                        "root_id": "atom-authenticate-return",
                        "root_fields": {
                            "atom_kind": "RETURN",
                            "structural_ordinal": 5,
                        },
                        "state_fields": {
                            "operator": "RETURN",
                            "semantic_form": "RETURN_VALUE",
                            "semantic_operands": [
                                {
                                    "kind": "ENTITY_REF",
                                    "value": "atom-issue-session",
                                }
                            ],
                            "referenced_entity_root_ids": [
                                "atom-issue-session"
                            ],
                            "source_order_ordinal": 5,
                            "value_category": "CALL_RESULT",
                        },
                    },
                ],
                "legacy_calls": [
                    {
                        "object_entity_root_id": "method-record-failure",
                        "predicate_state_fields": {"call_site_count": 2},
                    },
                    {
                        "object_entity_root_id": "method-issue-session",
                        "predicate_state_fields": {"call_site_count": 1},
                    },
                ],
            },
        },
        {
            "operation": "METHOD_IMPLEMENTATION",
            "payload": {
                "canonical_signature": "dev.acme.auth.LoginService#issueSession()",
                "method": {"root_id": "method-issue-session"},
                "state_slots": [],
                "ordered_atoms": [
                    {
                        "root_id": "atom-issue-return",
                        "root_fields": {
                            "atom_kind": "RETURN",
                            "structural_ordinal": 0,
                        },
                        "state_fields": {
                            "operator": "RETURN",
                            "semantic_form": "RETURN_VALUE",
                            "semantic_operands": [
                                {"kind": "BOOLEAN_LITERAL", "value": True}
                            ],
                            "referenced_entity_root_ids": [],
                            "source_order_ordinal": 0,
                            "value_category": "BOOLEAN",
                        },
                    }
                ],
                "legacy_calls": [],
            },
        },
        {
            "operation": "METHOD_IMPLEMENTATION",
            "payload": {
                "canonical_signature": "dev.acme.auth.LoginService#recordFailure()",
                "method": {"root_id": "method-record-failure"},
                "state_slots": [],
                "ordered_atoms": [
                    {
                        "root_id": "atom-record-return",
                        "root_fields": {
                            "atom_kind": "RETURN",
                            "structural_ordinal": 0,
                        },
                        "state_fields": {
                            "operator": "RETURN",
                            "semantic_form": "RETURN_VALUE",
                            "semantic_operands": [],
                            "referenced_entity_root_ids": [],
                            "source_order_ordinal": 0,
                            "value_category": "VOID",
                        },
                    }
                ],
                "legacy_calls": [],
            },
        },
    ]


class WorldModelAnswerStrategyTests(unittest.TestCase):
    def test_profile_binding_returns_a_new_exact_strategy(self):
        original = WorldModelCapabilityStrategy(SequencedGateway([]), configuration())

        java = original.for_proposal_contract(JAVA_WORLD_MODEL_PROPOSAL_CONTRACT)

        self.assertEqual(original.strategy_ref, MAVEN_WORLD_MODEL_PROPOSAL_CONTRACT.strategy_ref)
        self.assertEqual(java.strategy_ref, JAVA_WORLD_MODEL_PROPOSAL_CONTRACT.strategy_ref)
        self.assertIsNot(original, java)

    def test_java_contract_is_versioned_and_binds_method_inventory_vocabulary(self):
        expected = {
            "operations": [
                {
                    "operation": "declared_method_inventory",
                    "snapshot": "snapshot_java",
                }
            ]
        }
        gateway = SequencedGateway([expected])
        strategy = WorldModelCapabilityStrategy(
            gateway,
            configuration(),
            proposal_contract=JAVA_WORLD_MODEL_PROPOSAL_CONTRACT,
        )

        proposal = strategy.propose(
            case_id="WM-JAVA-CE-PLAN-METHOD-001",
            capability=GENERIC_QUERY_PLANNING,
            sealed_input={
                "read_set": ["snapshot_java"],
                "needs": ["method_inventory_left"],
            },
            available_operations=(
                JAVA_WORLD_MODEL_PROPOSAL_CONTRACT.available_operations
            ),
        )

        self.assertEqual(dict(proposal.normalized_result), expected)
        context = gateway.contexts[0]
        self.assertEqual(context.manifest.strategy_ref, strategy.strategy_ref)
        self.assertEqual(context.prompt_program_ref, JAVA_WORLD_MODEL_ANSWER_PROMPT_REF)
        self.assertEqual(
            context.manifest.proposal_vocabulary_ref,
            "world-model-authority-proposal-vocabulary@2",
        )
        self.assertIn(
            "method_inventory_left/right maps to declared_method_inventory",
            context.manifest.items[0].content,
        )

    def test_contract_vocabulary_drift_is_rejected_before_gateway(self):
        gateway = SequencedGateway([])
        strategy = WorldModelCapabilityStrategy(
            gateway,
            configuration(),
            proposal_contract=JAVA_WORLD_MODEL_PROPOSAL_CONTRACT,
        )

        with self.assertRaises(DomainError):
            strategy.propose(
                case_id="WM-JAVA-CE-PLAN-DRIFT",
                capability=GENERIC_QUERY_PLANNING,
                sealed_input={"read_set": ["snapshot_java"], "needs": []},
                available_operations=(
                    MAVEN_WORLD_MODEL_PROPOSAL_CONTRACT.available_operations
                ),
            )

        self.assertEqual(gateway.contexts, [])

    def test_fixed_java_source_semantics_contract_has_three_closed_role_schemas(self):
        outputs = (
            {
                "need_key": "implementation-answer",
                "snapshot": "snapshot_java",
                "operations": [
                    "implementation_candidates",
                    "method_implementation",
                ],
                "search_terms": ["credentials"],
                "limit": 5,
            },
            {
                "disposition": "SUPPORTED",
                "answer": "The typed branch controls the recorded call and throw.",
                "step_result_ids": ["world_model_step_result_" + "1" * 32],
                "support_digests": ["sha256:" + "2" * 64],
                "gap_code": None,
                "limitation_codes": [],
            },
            {
                "decision": "APPROVE",
                "finding_codes": [],
                "checked_need_ids": ["implementation-answer"],
                "checked_step_result_ids": [
                    "world_model_step_result_" + "1" * 32
                ],
                "checked_support_digests": ["sha256:" + "2" * 64],
            },
        )
        gateway = SequencedGateway(outputs)
        strategy = WorldModelCapabilityStrategy(
            gateway,
            configuration(),
            proposal_contract=(
                JAVA_SOURCE_SEMANTICS_FIXED_WORLD_MODEL_PROPOSAL_CONTRACT
            ),
        )

        plan = strategy.propose(
            case_id="product:semantic:plan",
            capability=IMPLEMENTATION_QUERY_PLANNING,
            sealed_input={"original_question": "How is this implemented?"},
            available_operations=(
                JAVA_SOURCE_SEMANTICS_FIXED_WORLD_MODEL_PROPOSAL_CONTRACT.available_operations
            ),
        )
        draft = strategy.propose(
            case_id="product:semantic:draft",
            capability=IMPLEMENTATION_ANSWER_DRAFTING,
            sealed_input={"query_results": []},
        )
        review = strategy.propose(
            case_id="product:semantic:review",
            capability=IMPLEMENTATION_ANSWER_REVIEW,
            sealed_input={"draft": outputs[1]},
        )

        self.assertEqual(
            tuple(item.capability for item in (plan, draft, review)),
            (
                IMPLEMENTATION_QUERY_PLANNING,
                IMPLEMENTATION_ANSWER_DRAFTING,
                IMPLEMENTATION_ANSWER_REVIEW,
            ),
        )
        self.assertEqual(len(gateway.contexts), 3)
        self.assertEqual(
            {item.output_schema_ref for item in gateway.contexts},
            {
                "java-implementation-query-plan@1",
                "java-implementation-answer-draft@1",
                "java-implementation-answer-review@2",
            },
        )
        self.assertEqual(
            len(
                world_model_answer_output_schemas(
                    include_java_source_semantics=True
                )
            ),
            11,
        )
        self.assertNotEqual(
            java_source_semantics_world_model_output_contract_digest(
                JAVA_SOURCE_SEMANTICS_FIXED_WORLD_MODEL_PROPOSAL_CONTRACT
            ),
            world_model_answer_output_contract_digest(),
        )

    def test_active_java_source_semantics_contract_is_bounded_investigation(self):
        contract = JAVA_SOURCE_SEMANTICS_WORLD_MODEL_PROPOSAL_CONTRACT

        self.assertEqual(contract.strategy_version, "1.5.11")
        self.assertEqual(
            JAVA_SOURCE_SEMANTICS_INVESTIGATION_ARGUMENT_COMPILER_REF,
            "java-source-semantics-investigation-argument-compiler@7",
        )
        self.assertEqual(
            JAVA_SOURCE_SEMANTICS_TERMINAL_AUTHORITY_COMPILER_REF,
            "java-source-semantics-terminal-authority-compiler@3",
        )
        self.assertEqual(
            contract.capabilities,
            (
                IMPLEMENTATION_INVESTIGATION,
                IMPLEMENTATION_ANSWER_DRAFTING,
                IMPLEMENTATION_ANSWER_REVIEW,
            ),
        )
        self.assertEqual(
            contract.available_operations,
            (
                "implementation_candidates",
                "method_implementations",
                "declared_method_inventory",
                "direct_neighborhood",
                "path_exists",
                "all_simple_paths",
                "FINISH",
            ),
        )
        self.assertEqual(
            len(world_model_answer_output_schemas(include_java_source_semantics=True)),
            11,
        )
        self.assertNotEqual(
            java_source_semantics_world_model_output_contract_digest(contract),
            java_source_semantics_world_model_output_contract_digest(
                JAVA_SOURCE_SEMANTICS_FIXED_WORLD_MODEL_PROPOSAL_CONTRACT
            ),
        )

    def test_java_source_semantics_prompt_and_review_vocabulary_are_closed(self):
        contract = JAVA_SOURCE_SEMANTICS_WORLD_MODEL_PROPOSAL_CONTRACT
        capability_prompts = dict(contract.capability_prompts)
        investigation_prompt = contract.prompt_for(IMPLEMENTATION_INVESTIGATION)
        draft_prompt = contract.prompt_for(IMPLEMENTATION_ANSWER_DRAFTING)
        review_prompt = contract.prompt_for(IMPLEMENTATION_ANSWER_REVIEW)
        schemas = world_model_answer_output_schemas(
            include_java_source_semantics=True
        )
        finding_schema = schemas[
            "java-implementation-answer-review@2"
        ].schema["properties"]["finding_codes"]

        self.assertEqual(tuple(capability_prompts), contract.capabilities)
        self.assertEqual(
            contract.instruction_transformation_ref,
            "capability-prompt-selection@1",
        )
        self.assertNotIn(
            "return/returns/returned/returning or 返回 maps to the exact term return",
            investigation_prompt,
        )
        self.assertIn(
            "an omission fault marker maps to MATERIAL_OMISSION",
            review_prompt,
        )
        self.assertIn(
            "The platform, not you, owns the evidence ledger after step 1",
            investigation_prompt,
        )
        self.assertIn(
            "On later steps evidence_requests and search_terms must be empty",
            investigation_prompt,
        )
        self.assertIn(
            "available_operations contains only the platform transition",
            investigation_prompt,
        )
        self.assertIn(
            "Graph evidence already includes the method-result prerequisite",
            investigation_prompt,
        )
        self.assertIn(
            "declaring-type prerequisites",
            investigation_prompt,
        )
        self.assertIn(
            "a value of 1 still permits the final scheduled query",
            investigation_prompt,
        )
        self.assertIn(
            "Return each case-insensitively normalized term at most once",
            investigation_prompt,
        )
        self.assertIn(
            "derives the terminal reason from typed support and the completeness receipt",
            investigation_prompt,
        )
        self.assertIn(
            "declared_method_inventory only for a complete declaring-type method inventory",
            investigation_prompt,
        )
        self.assertIn(
            "all other capability sections are inactive for this call",
            investigation_prompt,
        )
        self.assertIn(
            "Use path_exists only when the question explicitly names reachability",
            investigation_prompt,
        )
        self.assertIn(
            "the word through alone is not reachability",
            investigation_prompt,
        )
        self.assertIn(
            "Determine origin from the original question rather than from vocabulary overlap",
            investigation_prompt,
        )
        self.assertIn(
            "Positively requested code-artifact, evidence-relation, or returned-set nouns",
            investigation_prompt,
        )
        self.assertIn(
            "concepts that occur only in a negated presentation, authority, or budget constraint",
            investigation_prompt,
        )
        self.assertIn(
            "delete every term that has no corresponding question concept",
            investigation_prompt,
        )
        self.assertIn(
            "never copy an instructional example or infer an unrequested concrete execution mechanism",
            investigation_prompt,
        )
        self.assertIn(
            "Never copy, reconstruct, abbreviate, or invent those authority values",
            investigation_prompt,
        )
        self.assertIn(
            "return one closed transition hint plus the semantic evidence obligations",
            investigation_prompt,
        )
        self.assertIn(
            "First obey the Application-owned review_completeness_scope",
            review_prompt,
        )
        self.assertIn(
            "Do not reconstruct an omitted third-layer state",
            review_prompt,
        )
        self.assertIn(
            "THREE_LAYER_REVIEW preserves the sealed third-layer fields",
            review_prompt,
        )
        self.assertIn(
            "FINISH is available only when the platform ledger says every evidence obligation is covered",
            investigation_prompt,
        )
        self.assertIn(
            "REJECT with QUERY_INCOMPLETE whenever a needed query-result",
            review_prompt,
        )
        self.assertIn(
            "is one QUERY_INCOMPLETE fault, not an UNSUPPORTED_RUNTIME_CLAIM",
            review_prompt,
        )
        self.assertIn("IMPLEMENTATION_INVESTIGATION:", investigation_prompt)
        self.assertIn(
            "When the question uses a non-Latin writing system",
            investigation_prompt,
        )
        self.assertIn(
            "common English source-identifier translation",
            investigation_prompt,
        )
        self.assertIn(
            "a broader topic synonym or the selected evidence operation never substitutes",
            investigation_prompt,
        )
        self.assertIn(
            "A generic interrogative such as whether, can, or does is not sufficient",
            investigation_prompt,
        )
        self.assertNotIn("IMPLEMENTATION_ANSWER_DRAFTING:", investigation_prompt)
        self.assertNotIn("IMPLEMENTATION_ANSWER_REVIEW:", investigation_prompt)
        self.assertNotIn("UNAVAILABLE_LEGACY", investigation_prompt)
        self.assertIn("IMPLEMENTATION_ANSWER_DRAFTING:", draft_prompt)
        self.assertIn(
            "Always return empty step_result_ids and support_digests arrays",
            draft_prompt,
        )
        self.assertIn("Application-owned behavior_obligation_scope", draft_prompt)
        self.assertIn("same_target_call_count", draft_prompt)
        self.assertNotIn("IMPLEMENTATION_INVESTIGATION:", draft_prompt)
        self.assertNotIn("IMPLEMENTATION_ANSWER_REVIEW:", draft_prompt)
        self.assertIn("IMPLEMENTATION_ANSWER_REVIEW:", review_prompt)
        self.assertIn(
            "Always return empty checked_need_ids, checked_step_result_ids, and checked_support_digests arrays",
            review_prompt,
        )
        self.assertIn("Distinct same-target CALL_SITE events cannot be merged", review_prompt)
        self.assertNotIn("IMPLEMENTATION_INVESTIGATION:", review_prompt)
        self.assertNotIn("IMPLEMENTATION_ANSWER_DRAFTING:", review_prompt)
        for case_or_provider_patch in (
            "DeepSeek",
            "WM-JSS-I8-",
            "LoginService",
            "purchase-order",
        ):
            for prompt in capability_prompts.values():
                self.assertNotIn(case_or_provider_patch, prompt)
        self.assertEqual(
            finding_schema["items"]["enum"],
            list(JAVA_SOURCE_SEMANTICS_REVIEW_FINDING_CODES),
        )
        self.assertTrue(finding_schema["uniqueItems"])
        intent_schema = schemas[
            "java-bounded-implementation-investigation-intent@2"
        ].schema
        self.assertEqual(
            set(intent_schema["properties"]),
            {
                "operation",
                "search_terms",
                "relation_intent",
                "finish_reason",
                "evidence_requests",
            },
        )
        self.assertTrue(
            intent_schema["properties"]["search_terms"]["uniqueItems"]
        )

    def test_active_terminal_compiler_hides_and_binds_draft_authority(self):
        step_result_ids = (
            "world_model_step_result_" + "1" * 32,
            "world_model_step_result_" + "2" * 32,
        )
        support_digests = (
            "sha256:" + "3" * 64,
            "sha256:" + "4" * 64,
        )
        gateway = SequencedGateway(
            [
                {
                    "disposition": "SUPPORTED",
                    "answer": "Failure is recorded before the exception is thrown.",
                    "step_result_ids": [],
                    "support_digests": [],
                    "gap_code": None,
                    "limitation_codes": [],
                }
            ]
        )
        strategy = WorldModelCapabilityStrategy(
            gateway,
            configuration(),
            proposal_contract=JAVA_SOURCE_SEMANTICS_WORLD_MODEL_PROPOSAL_CONTRACT,
        )

        proposal = strategy.propose(
            case_id="product:semantic:draft-authority",
            capability=IMPLEMENTATION_ANSWER_DRAFTING,
            sealed_input={
                "original_question": "How is failure handled?",
                "query_results": ordered_behavior_query_results(),
                "assessment_disposition": "SUPPORTED",
                "authorized_step_result_ids": step_result_ids,
                "authorized_support_digests": support_digests,
            },
        )

        self.assertEqual(
            proposal.normalized_result["step_result_ids"],
            list(step_result_ids),
        )
        self.assertEqual(
            proposal.normalized_result["support_digests"],
            list(support_digests),
        )
        model_state = json.loads(gateway.contexts[0].manifest.items[1].content)
        model_input = model_state["input"]
        self.assertEqual(model_input["assessment_disposition"], "SUPPORTED")
        scope = model_input["behavior_obligation_scope"]
        self.assertEqual(scope["mode"], "ORDERED_METHOD_BEHAVIOR")
        authenticate = scope["methods"][0]
        self.assertEqual(authenticate["ordered_event_count"], 6)
        first_call, second_call = authenticate["ordered_events"][1:3]
        self.assertEqual(first_call["same_target_call_ordinal"], 1)
        self.assertEqual(second_call["same_target_call_ordinal"], 2)
        self.assertEqual(first_call["same_target_call_count"], 2)
        self.assertEqual(second_call["same_target_call_count"], 2)
        self.assertEqual(first_call["legacy_static_call_site_count"], 2)
        self.assertEqual(
            authenticate["ordered_events"][4]["references"],
            [
                {
                    "kind": "METHOD",
                    "value": "dev.acme.auth.LoginService#issueSession()",
                }
            ],
        )
        self.assertEqual(
            authenticate["ordered_events"][5]["references"],
            [
                {
                    "kind": "ORDERED_EVENT",
                    "value": {
                        "method": "dev.acme.auth.LoginService#authenticate(boolean)",
                        "source_order_ordinal": 4,
                    },
                }
            ],
        )
        self.assertEqual(
            first_call["references"],
            [
                {
                    "kind": "METHOD",
                    "value": "dev.acme.auth.LoginService#recordFailure()",
                }
            ],
        )

    def test_active_terminal_compiler_hides_and_binds_review_authority(self):
        step_result_id = "world_model_step_result_" + "5" * 32
        support_digest = "sha256:" + "6" * 64
        gateway = SequencedGateway(
            [
                {
                    "decision": "REJECT",
                    "finding_codes": ["QUERY_INCOMPLETE"],
                    "checked_need_ids": [],
                    "checked_step_result_ids": [],
                    "checked_support_digests": [],
                }
            ]
        )
        strategy = WorldModelCapabilityStrategy(
            gateway,
            configuration(),
            proposal_contract=JAVA_SOURCE_SEMANTICS_WORLD_MODEL_PROPOSAL_CONTRACT,
        )

        proposal = strategy.propose(
            case_id="product:semantic:review-authority",
            capability=IMPLEMENTATION_ANSWER_REVIEW,
            sealed_input={
                "assessment": {
                    "needs": [
                        {
                            "need_id": "implementation-answer",
                            "outcome": "LIMITATION",
                        }
                    ]
                },
                "draft": {"answer": "Bounded absence."},
                "query_plan": {
                    "investigation_trace": {
                        "completeness": {
                            "query_result": "COMPLETE",
                            "knowledge_representation": "COMPLETE",
                            "business_discovery_recall": "UNKNOWN",
                            "bounded_absence_allowed": False,
                            "missing_limitation_codes": [
                                "BUSINESS_DISCOVERY_RECALL_UNPROVEN"
                            ],
                        }
                    }
                },
                "required_checked_need_ids": ("implementation-answer",),
                "required_checked_step_result_ids": (step_result_id,),
                "required_checked_support_digests": (support_digest,),
            },
        )

        self.assertEqual(
            proposal.normalized_result["checked_need_ids"],
            ["implementation-answer"],
        )
        self.assertEqual(
            proposal.normalized_result["checked_step_result_ids"],
            [step_result_id],
        )
        self.assertEqual(
            proposal.normalized_result["checked_support_digests"],
            [support_digest],
        )
        model_state = json.loads(gateway.contexts[0].manifest.items[1].content)
        self.assertEqual(
            model_state["input"]["review_completeness_scope"],
            {
                "compiler_ref": (
                    "java-source-semantics-terminal-authority-compiler@3"
                ),
                "mode": "THREE_LAYER_REVIEW",
                "need_outcomes": [
                    {
                        "need_id": "implementation-answer",
                        "outcome": "LIMITATION",
                    }
                ],
                "business_discovery_recall_applicability": (
                    "PRESERVED_FROM_SEALED_TRACE"
                ),
                "bounded_negative_claim_policy": (
                    "REQUIRE_COMPLETE_THREE_LAYER_AUTHORITY"
                ),
            },
        )
        self.assertEqual(
            model_state["input"]["query_plan"]["investigation_trace"][
                "completeness"
            ]["business_discovery_recall"],
            "UNKNOWN",
        )

    def test_active_terminal_compiler_removes_irrelevant_positive_recall(self):
        step_result_id = "world_model_step_result_" + "8" * 32
        support_digest = "sha256:" + "9" * 64
        gateway = SequencedGateway(
            [
                {
                    "decision": "APPROVE",
                    "finding_codes": [],
                    "checked_need_ids": [],
                    "checked_step_result_ids": [],
                    "checked_support_digests": [],
                }
            ]
        )
        strategy = WorldModelCapabilityStrategy(
            gateway,
            configuration(),
            proposal_contract=JAVA_SOURCE_SEMANTICS_WORLD_MODEL_PROPOSAL_CONTRACT,
        )

        proposal = strategy.propose(
            case_id="product:semantic:review-positive-scope",
            capability=IMPLEMENTATION_ANSWER_REVIEW,
            sealed_input={
                "assessment": {
                    "needs": [
                        {
                            "need_id": "implementation-answer",
                            "outcome": "SATISFIED",
                        }
                    ]
                },
                "draft": {"answer": "Failure is recorded before success."},
                "query_results": ordered_behavior_query_results(),
                "query_plan": {
                    "investigation_trace": {
                        "completeness": {
                            "query_result": "COMPLETE",
                            "knowledge_representation": "COMPLETE",
                            "business_discovery_recall": "UNKNOWN",
                            "bounded_absence_allowed": False,
                            "missing_limitation_codes": [
                                "BUSINESS_DISCOVERY_RECALL_UNPROVEN"
                            ],
                        }
                    }
                },
                "required_checked_need_ids": ("implementation-answer",),
                "required_checked_step_result_ids": (step_result_id,),
                "required_checked_support_digests": (support_digest,),
            },
        )

        self.assertEqual(proposal.normalized_result["decision"], "APPROVE")
        model_state = json.loads(gateway.contexts[0].manifest.items[1].content)
        model_input = model_state["input"]
        self.assertEqual(
            model_input["review_completeness_scope"]["mode"],
            "POSITIVE_SUPPORTED_ONLY",
        )
        self.assertEqual(
            model_input["review_completeness_scope"][
                "business_discovery_recall_applicability"
            ],
            "NOT_APPLICABLE",
        )
        self.assertEqual(
            model_input["review_completeness_scope"][
                "bounded_negative_claim_policy"
            ],
            "REJECT",
        )
        self.assertEqual(
            model_input["behavior_obligation_scope"]["mode"],
            "ORDERED_METHOD_BEHAVIOR",
        )
        self.assertEqual(
            model_input["behavior_obligation_scope"]["methods"][0][
                "ordered_events"
            ][2]["same_target_call_ordinal"],
            2,
        )
        projected = model_input["query_plan"]["investigation_trace"][
            "completeness"
        ]
        self.assertEqual(
            projected,
            {
                "query_result": "COMPLETE",
                "knowledge_representation": "COMPLETE",
            },
        )

    def test_active_terminal_compiler_rejects_model_owned_authority(self):
        gateway = SequencedGateway(
            [
                {
                    "disposition": "SUPPORTED",
                    "answer": "Failure is recorded.",
                    "step_result_ids": [
                        "world_model_step_result_" + "7" * 32
                    ],
                    "support_digests": [],
                    "gap_code": None,
                    "limitation_codes": [],
                }
            ]
        )
        strategy = WorldModelCapabilityStrategy(
            gateway,
            configuration(),
            proposal_contract=JAVA_SOURCE_SEMANTICS_WORLD_MODEL_PROPOSAL_CONTRACT,
        )

        with self.assertRaises(DomainError) as raised:
            strategy.propose(
                case_id="product:semantic:draft-model-authority",
                capability=IMPLEMENTATION_ANSWER_DRAFTING,
                sealed_input={
                    "assessment_disposition": "SUPPORTED",
                    "authorized_step_result_ids": (
                        "world_model_step_result_" + "7" * 32,
                    ),
                    "authorized_support_digests": (),
                },
            )

        self.assertEqual(
            raised.exception.details["reason_code"],
            "TERMINAL_AUTHORITY_MODEL_OUTPUT_INVALID",
        )
        self.assertEqual(len(gateway.contexts), 1)

    def test_active_terminal_authority_is_required_before_gateway(self):
        gateway = SequencedGateway([])
        strategy = WorldModelCapabilityStrategy(
            gateway,
            configuration(),
            proposal_contract=JAVA_SOURCE_SEMANTICS_WORLD_MODEL_PROPOSAL_CONTRACT,
        )

        with self.assertRaises(DomainError):
            strategy.propose(
                case_id="product:semantic:draft-missing-authority",
                capability=IMPLEMENTATION_ANSWER_DRAFTING,
                sealed_input={"assessment_disposition": "SUPPORTED"},
            )

        self.assertEqual(gateway.contexts, [])

    def test_java_source_semantics_review_rejects_unregistered_finding_code(self):
        gateway = SequencedGateway(
            [
                {
                    "decision": "REJECT",
                    "finding_codes": ["DRAFT_OMITS_QUERY_RESULT_ATOMS"],
                    "checked_need_ids": ["implementation-answer"],
                    "checked_step_result_ids": [],
                    "checked_support_digests": [],
                }
            ]
        )
        strategy = WorldModelCapabilityStrategy(
            gateway,
            configuration(),
            proposal_contract=(
                JAVA_SOURCE_SEMANTICS_WORLD_MODEL_PROPOSAL_CONTRACT
            ),
        )

        with self.assertRaises(DomainError):
            strategy.propose(
                case_id="product:semantic:review-invalid-code",
                capability=IMPLEMENTATION_ANSWER_REVIEW,
                sealed_input={
                    "assessment": {
                        "needs": [
                            {
                                "need_id": "implementation-answer",
                                "outcome": "SATISFIED",
                            }
                        ]
                    },
                    "draft": {"body": "incomplete"},
                    "query_plan": {
                        "investigation_trace": {
                            "completeness": {
                                "query_result": "COMPLETE",
                                "knowledge_representation": "COMPLETE",
                                "business_discovery_recall": "UNKNOWN",
                                "bounded_absence_allowed": False,
                                "missing_limitation_codes": [
                                    "BUSINESS_DISCOVERY_RECALL_UNPROVEN"
                                ],
                            }
                        }
                    },
                    "required_checked_need_ids": ("implementation-answer",),
                    "required_checked_step_result_ids": (),
                    "required_checked_support_digests": (),
                },
            )

    def test_active_terminal_compiler_rejects_caller_owned_review_scope(self):
        gateway = SequencedGateway([])
        strategy = WorldModelCapabilityStrategy(
            gateway,
            configuration(),
            proposal_contract=JAVA_SOURCE_SEMANTICS_WORLD_MODEL_PROPOSAL_CONTRACT,
        )

        with self.assertRaisesRegex(
            DomainError,
            "review completeness scope is application-owned",
        ):
            strategy.propose(
                case_id="product:semantic:review-caller-scope",
                capability=IMPLEMENTATION_ANSWER_REVIEW,
                sealed_input={
                    "assessment": {
                        "needs": [
                            {
                                "need_id": "implementation-answer",
                                "outcome": "SATISFIED",
                            }
                        ]
                    },
                    "draft": {"body": "supported"},
                    "query_plan": {
                        "investigation_trace": {
                            "completeness": {
                                "query_result": "COMPLETE",
                                "knowledge_representation": "COMPLETE",
                                "business_discovery_recall": "UNKNOWN",
                                "bounded_absence_allowed": False,
                                "missing_limitation_codes": [
                                    "BUSINESS_DISCOVERY_RECALL_UNPROVEN"
                                ],
                            }
                        }
                    },
                    "review_completeness_scope": {"mode": "FORGED"},
                    "required_checked_need_ids": ("implementation-answer",),
                    "required_checked_step_result_ids": (),
                    "required_checked_support_digests": (),
                },
            )

        self.assertEqual(gateway.contexts, [])

    def test_active_terminal_compiler_rejects_caller_owned_behavior_scope(self):
        gateway = SequencedGateway([])
        strategy = WorldModelCapabilityStrategy(
            gateway,
            configuration(),
            proposal_contract=JAVA_SOURCE_SEMANTICS_WORLD_MODEL_PROPOSAL_CONTRACT,
        )

        with self.assertRaisesRegex(
            DomainError,
            "behavior obligation scope is application-owned",
        ):
            strategy.propose(
                case_id="product:semantic:draft-caller-behavior-scope",
                capability=IMPLEMENTATION_ANSWER_DRAFTING,
                sealed_input={
                    "assessment_disposition": "SUPPORTED",
                    "behavior_obligation_scope": {"mode": "FORGED"},
                    "authorized_step_result_ids": (),
                    "authorized_support_digests": (),
                },
            )

        self.assertEqual(gateway.contexts, [])

    def test_all_closed_roles_use_one_oracle_free_no_tools_manifest(self):
        suite = load_capability_suite()
        cases = suite["cases"]
        gateway = SequencedGateway(
            [case["expected_normalized_result"] for case in cases]
        )
        strategy = WorldModelCapabilityStrategy(gateway, configuration())

        proposals = []
        for case in cases:
            proposals.append(
                strategy.propose(
                    case_id=case["case_id"],
                    capability=case["capability"],
                    sealed_input=case["input"],
                    available_operations=tuple(case.get("available_operations", [])),
                )
            )

        self.assertEqual(len(proposals), 7)
        self.assertEqual(len(gateway.contexts), 7)
        self.assertEqual(
            {proposal.capability for proposal in proposals},
            set(WORLD_MODEL_CAPABILITIES),
        )
        for case, proposal, context in zip(cases, proposals, gateway.contexts):
            self.assertEqual(
                dict(proposal.normalized_result),
                case["expected_normalized_result"],
            )
            self.assertEqual(context.runtime_access_mode.value, "NO_EXTERNAL_ACCESS")
            self.assertEqual(context.platform_proposal_mode.value, "NONE")
            self.assertEqual(
                [item.item_id for item in context.manifest.items],
                ["instruction", "sealed-case-input", "qualification"],
            )
            model_state = context.manifest.items[1].content
            self.assertNotIn("expected_normalized_result", model_state)
            self.assertNotIn("projection_fields", model_state)
            self.assertNotIn("forbidden_events", model_state)
            self.assertNotIn("WM-PRODUCT-", model_state)
            if case["capability"] == "VIEW_LIMITATION_AND_KNOWLEDGE_GAP":
                instruction = context.manifest.items[0].content
                self.assertIn("coverage is authoritative", instruction)
                self.assertIn("view_result.status exactly LIMITED", instruction)
                self.assertIn("view_result.owner exactly STRUCTURE_VIEW", instruction)
                self.assertIn(
                    "need_assessment.status exactly KNOWLEDGE_GAP", instruction
                )
                self.assertIn(
                    "need_assessment.owner exactly KNOWLEDGE_USE", instruction
                )
                self.assertIn(
                    "Never emit SATISFIED_SUPPORTED_NEGATIVE for PARTIAL coverage",
                    instruction,
                )

    def test_ineligible_or_duplicate_key_output_fails_closed_without_retry(self):
        ineligible = SimpleNamespace(
            call=SimpleNamespace(
                model_call_id=StableId("model_call_" + "1" * 32),
                failure_code="PROVIDER_OUTCOME_UNKNOWN",
            ),
            response=None,
            isolation_receipt=SimpleNamespace(
                manifest_digest=digest_of("manifest"),
                provider_request_digest=digest_of("request"),
            ),
            eligibility=SimpleNamespace(
                eligible_for_production_domain_output=False,
                reason="MODEL_CALL_OUTCOME_UNKNOWN",
            ),
        )
        gateway = SequencedGateway([ineligible])
        with self.assertRaises(DomainError):
            WorldModelCapabilityStrategy(gateway, configuration()).propose(
                case_id="WM-CE-NEGATIVE-003",
                capability="COMPLETE_NEGATIVE_ANSWER",
                sealed_input={"coverage": "COMPLETE"},
            )
        self.assertEqual(len(gateway.contexts), 1)

        duplicate_text = (
            '{"need_status":"SATISFIED_SUPPORTED_NEGATIVE",'
            '"need_status":"SATISFIED_SUPPORTED_NEGATIVE",'
            '"claim_scope":"NO_PATH_IN_X_FOR_EXACT_READ_SET"}'
        )
        duplicate = SimpleNamespace(
            call=SimpleNamespace(
                model_call_id=StableId("model_call_" + "2" * 32),
                failure_code=None,
            ),
            response=SimpleNamespace(
                output_text=duplicate_text,
                output_digest=digest_of(duplicate_text),
            ),
            isolation_receipt=SimpleNamespace(
                manifest_digest=digest_of("manifest-2"),
                provider_request_digest=digest_of("request-2"),
            ),
            eligibility=SimpleNamespace(
                eligible_for_production_domain_output=True,
                reason="ELIGIBLE",
            ),
        )
        gateway = SequencedGateway([duplicate])
        with self.assertRaises(DomainError):
            WorldModelCapabilityStrategy(gateway, configuration()).propose(
                case_id="WM-CE-NEGATIVE-003",
                capability="COMPLETE_NEGATIVE_ANSWER",
                sealed_input={"coverage": "COMPLETE"},
            )
        self.assertEqual(len(gateway.contexts), 1)

    def test_strategy_fingerprints_cover_prompt_and_all_seven_schemas(self):
        self.assertEqual(len(world_model_answer_output_schemas()), 7)
        self.assertTrue(
            world_model_answer_strategy_implementation_digest().value.startswith(
                "sha256:"
            )
        )
        self.assertNotEqual(
            world_model_answer_prompt_program_digest(),
            world_model_answer_output_contract_digest(),
        )
        self.assertEqual(
            world_model_answer_prompt_program_digest().value,
            "sha256:f6d93c9b2fcb4b953a7ddf35a787a5de8e6555397f49ad517cbf4d15681a24fc",
        )
        self.assertEqual(
            world_model_answer_strategy_implementation_digest().value,
            "sha256:4a83df22f535dc8fa1712b3fc04f7a6ee3960263070ed5366ab18b3692446fa0",
        )
        self.assertNotEqual(
            world_model_answer_strategy_implementation_digest(),
            world_model_answer_strategy_implementation_digest(
                JAVA_WORLD_MODEL_PROPOSAL_CONTRACT
            ),
        )


if __name__ == "__main__":
    unittest.main()
