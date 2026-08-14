from __future__ import annotations

import json
from types import SimpleNamespace
import unittest

from software_world_model.ai_infrastructure import (
    GENERIC_QUERY_PLANNING,
    IMPLEMENTATION_ANSWER_DRAFTING,
    IMPLEMENTATION_ANSWER_REVIEW,
    IMPLEMENTATION_QUERY_PLANNING,
    JAVA_SOURCE_SEMANTICS_REVIEW_FINDING_CODES,
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

    def test_java_source_semantics_contract_has_three_closed_role_schemas(self):
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
                JAVA_SOURCE_SEMANTICS_WORLD_MODEL_PROPOSAL_CONTRACT
            ),
        )

        plan = strategy.propose(
            case_id="product:semantic:plan",
            capability=IMPLEMENTATION_QUERY_PLANNING,
            sealed_input={"original_question": "How is this implemented?"},
            available_operations=(
                JAVA_SOURCE_SEMANTICS_WORLD_MODEL_PROPOSAL_CONTRACT.available_operations
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
            10,
        )
        self.assertNotEqual(
            java_source_semantics_world_model_output_contract_digest(),
            world_model_answer_output_contract_digest(),
        )

    def test_java_source_semantics_prompt_and_review_vocabulary_are_closed(self):
        contract = JAVA_SOURCE_SEMANTICS_WORLD_MODEL_PROPOSAL_CONTRACT
        schemas = world_model_answer_output_schemas(
            include_java_source_semantics=True
        )
        finding_schema = schemas[
            "java-implementation-answer-review@2"
        ].schema["properties"]["finding_codes"]

        self.assertIn(
            "return/returns/returned/returning or 返回 maps to the exact term return",
            contract.prompt,
        )
        self.assertIn(
            "an omission fault marker maps to MATERIAL_OMISSION",
            contract.prompt,
        )
        self.assertEqual(
            finding_schema["items"]["enum"],
            list(JAVA_SOURCE_SEMANTICS_REVIEW_FINDING_CODES),
        )
        self.assertTrue(finding_schema["uniqueItems"])

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
                sealed_input={"draft": {"body": "incomplete"}},
            )

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
