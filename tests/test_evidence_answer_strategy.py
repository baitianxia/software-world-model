from __future__ import annotations

import json
from types import SimpleNamespace
import unittest

from software_world_model.ai_infrastructure import (
    AgenticModelStrategyConfiguration,
    ModelEvidenceAnswerGenerator,
    ModelIndependentEvidenceAnswerReviewer,
    ModelQuestionChecklistPlanner,
    evidence_answer_output_schemas,
    evidence_answer_strategy_implementation_digest,
)
from software_world_model.application_services import (
    EvidenceItem,
    EvidencePacket,
    QuestionChecklist,
)
from software_world_model.cross_cutting import Digest, StableId, digest_of


class SequencedGateway:
    def __init__(self, outputs):
        self.outputs = list(outputs)
        self.contexts = []

    def invoke(self, context):
        self.contexts.append(context)
        output = self.outputs.pop(0)
        if hasattr(output, "eligibility"):
            return output
        text = json.dumps(output, ensure_ascii=False)
        return SimpleNamespace(
            call=SimpleNamespace(failure_code=None),
            eligibility=SimpleNamespace(
                eligible_for_production_domain_output=True,
                reason="ELIGIBLE",
            ),
            response=SimpleNamespace(output_text=text),
        )


def configuration():
    return AgenticModelStrategyConfiguration(
        provider_type="TEST",
        adapter_version="test@1",
        model_ref="fixture",
        provider_configuration_fingerprint=Digest("sha256:" + "1" * 64),
        qualification_ref="qualification:test",
    )


def evidence_packet(checklist):
    item = EvidenceItem(
        evidence_id="evidence-1",
        operation_id=StableId("source_operation_" + "1" * 32),
        artifact_id=StableId("source_artifact_" + "2" * 32),
        tool="local-git.read@1",
        repository_revision="a" * 40,
        locator="src/App.py",
        coverage=(
            ("path", "src/App.py"),
            ("range", "bytes:0-30"),
            ("revision", "a" * 40),
        ),
        content="def run():\n    return 'ok'\n",
        content_digest=digest_of("def run():\n    return 'ok'\n"),
        digest=digest_of("evidence-1"),
    )
    return EvidencePacket(
        packet_id=StableId("evidence_packet_" + "3" * 32),
        checklist_digest=checklist.digest,
        target_digest=digest_of("target"),
        items=(item,),
        operation_references=(item.operation_id,),
        digest=digest_of("packet"),
    )


class EvidenceAnswerStrategyTests(unittest.TestCase):
    def test_question_planner_preserves_original_request_and_closed_role(self):
        gateway = SequencedGateway([{"questions": ["入口返回什么？"]}])
        planner = ModelQuestionChecklistPlanner(gateway, configuration())

        checklist = planner.plan(
            original_request="入口返回什么？", execution_ref="question:1"
        )

        self.assertEqual(checklist.original_request, "入口返回什么？")
        self.assertEqual(checklist.items[0].item_id, "check-1")
        context = gateway.contexts[0]
        self.assertEqual(context.manifest.capability_id, "evidence-answer.question-understanding")
        self.assertEqual(context.runtime_access_mode.value, "NO_EXTERNAL_ACCESS")
        self.assertIn("Do not assume", context.manifest.items[0].content)

    def test_generator_and_reviewer_bind_the_same_sealed_packet(self):
        checklist = QuestionChecklist.create(
            original_request="入口返回什么？", questions=("入口返回什么？",)
        )
        packet = evidence_packet(checklist)
        gateway = SequencedGateway(
            [
                {
                    "sections": [
                        {
                            "section_id": "result",
                            "kind": "SUPPORTED",
                            "text": "入口的 run 函数返回 ok。",
                            "checklist_item_ids": ["check-1"],
                            "evidence_ids": ["evidence-1"],
                        }
                    ]
                },
                {
                    "checks": {
                        "QUESTION_FIDELITY": True,
                        "EVIDENCE_GROUNDING": True,
                        "REQUEST_COMPLETENESS": True,
                        "RESPONSE_LANGUAGE": True,
                        "RELEVANCE_READABILITY": True,
                    },
                    "decision": "APPROVED",
                    "findings": [],
                },
            ]
        )
        generator = ModelEvidenceAnswerGenerator(gateway, configuration())
        reviewer = ModelIndependentEvidenceAnswerReviewer(gateway, configuration())

        draft = generator.generate(
            checklist=checklist,
            packet=packet,
            revision=1,
            prior_draft=None,
            review_findings=(),
            execution_ref="answer:1",
        )
        review = reviewer.review(
            checklist=checklist,
            packet=packet,
            draft=draft,
            execution_ref="review:1",
        )

        self.assertEqual(draft.evidence_packet_digest, packet.digest)
        self.assertEqual(review.evidence_packet_digest, packet.digest)
        self.assertEqual(review.draft_digest, draft.digest)
        generator_state = json.loads(gateway.contexts[0].manifest.items[1].content)
        reviewer_state = json.loads(gateway.contexts[1].manifest.items[1].content)
        self.assertEqual(generator_state["required_packet_digest"], packet.digest.value)
        self.assertEqual(reviewer_state["required_packet_digest"], packet.digest.value)
        self.assertNotIn("prior_draft", reviewer_state)

    def test_generator_repairs_semantically_invalid_section_contract(self):
        checklist = QuestionChecklist.create(
            original_request="入口返回什么？", questions=("入口返回什么？",)
        )
        packet = evidence_packet(checklist)
        gateway = SequencedGateway(
            [
                {
                    "sections": [
                        {
                            "section_id": "invalid-unknown",
                            "kind": "UNKNOWN",
                            "text": "无法确定。",
                            "checklist_item_ids": ["check-1"],
                            "evidence_ids": ["evidence-1"],
                        }
                    ]
                },
                {
                    "sections": [
                        {
                            "section_id": "result",
                            "kind": "SUPPORTED",
                            "text": "入口的 run 函数返回 ok。",
                            "checklist_item_ids": ["check-1"],
                            "evidence_ids": ["evidence-1"],
                        }
                    ]
                },
            ]
        )

        draft = ModelEvidenceAnswerGenerator(gateway, configuration()).generate(
            checklist=checklist,
            packet=packet,
            revision=1,
            prior_draft=None,
            review_findings=(),
            execution_ref="contract-repair:draft",
        )

        self.assertEqual(draft.sections[0].kind.value, "SUPPORTED")
        self.assertEqual(len(gateway.contexts), 2)
        repair_state = json.loads(gateway.contexts[1].manifest.items[1].content)
        self.assertIn("contract_repair", repair_state)
        self.assertEqual(
            repair_state["contract_repair"]["rejected_output_reason"],
            "unknown answer section cannot claim evidence",
        )

    def test_generator_repairs_completed_but_truncated_structured_output(self):
        checklist = QuestionChecklist.create(
            original_request="入口返回什么？", questions=("入口返回什么？",)
        )
        packet = evidence_packet(checklist)
        rejected = SimpleNamespace(
            call=SimpleNamespace(failure_code="STRUCTURED_OUTPUT_INVALID"),
            eligibility=SimpleNamespace(
                eligible_for_production_domain_output=False,
                reason="MODEL_OUTPUT_REJECTED_STRUCTURED_OUTPUT_INVALID",
            ),
            response=SimpleNamespace(
                output_text='{"sections":[',
                provider_request_id="provider-request-1",
                actual_model_fingerprint="fixture",
                usage_complete=True,
                input_tokens=100,
                output_tokens=1200,
                termination_reason="length",
            ),
        )
        gateway = SequencedGateway(
            [
                rejected,
                {
                    "sections": [
                        {
                            "section_id": "result",
                            "kind": "SUPPORTED",
                            "text": "入口的 run 函数返回 ok。",
                            "checklist_item_ids": ["check-1"],
                            "evidence_ids": ["evidence-1"],
                        }
                    ]
                },
            ]
        )

        draft = ModelEvidenceAnswerGenerator(gateway, configuration()).generate(
            checklist=checklist,
            packet=packet,
            revision=1,
            prior_draft=None,
            review_findings=(),
            execution_ref="truncated:draft",
        )

        self.assertEqual(draft.sections[0].kind.value, "SUPPORTED")
        repair_state = json.loads(gateway.contexts[1].manifest.items[1].content)
        self.assertEqual(
            repair_state["contract_repair"]["termination_reason"], "length"
        )

    def test_digest_and_schema_registry_cover_all_three_independent_roles(self):
        schemas = evidence_answer_output_schemas()

        self.assertEqual(len(schemas), 3)
        self.assertTrue(evidence_answer_strategy_implementation_digest().value.startswith("sha256:"))

    def test_reviewer_cannot_approve_a_failed_response_language_check(self):
        checklist = QuestionChecklist.create(
            original_request="请说明入口返回什么。", questions=("入口返回什么？",)
        )
        packet = evidence_packet(checklist)
        draft = ModelEvidenceAnswerGenerator(
            SequencedGateway(
                [
                    {
                        "sections": [
                            {
                                "section_id": "result",
                                "kind": "SUPPORTED",
                                "text": "The entry returns ok.",
                                "checklist_item_ids": ["check-1"],
                                "evidence_ids": ["evidence-1"],
                            }
                        ]
                    }
                ]
            ),
            configuration(),
        ).generate(
            checklist=checklist,
            packet=packet,
            revision=1,
            prior_draft=None,
            review_findings=(),
            execution_ref="language:draft",
        )
        gateway = SequencedGateway(
            [
                {
                    "checks": {
                        "QUESTION_FIDELITY": True,
                        "EVIDENCE_GROUNDING": True,
                        "REQUEST_COMPLETENESS": True,
                        "RESPONSE_LANGUAGE": True,
                        "RELEVANCE_READABILITY": True,
                    },
                    "decision": "APPROVED",
                    "findings": [],
                }
            ]
        )

        review = ModelIndependentEvidenceAnswerReviewer(
            gateway, configuration()
        ).review(
            checklist=checklist,
            packet=packet,
            draft=draft,
            execution_ref="language:review",
        )

        self.assertEqual(review.decision.value, "REWRITE_REQUIRED")
        self.assertFalse(dict(review.checks)["RESPONSE_LANGUAGE"])

    def test_reviewer_repairs_semantically_invalid_rewrite_finding(self):
        checklist = QuestionChecklist.create(
            original_request="入口返回什么？", questions=("入口返回什么？",)
        )
        packet = evidence_packet(checklist)
        draft = ModelEvidenceAnswerGenerator(
            SequencedGateway(
                [
                    {
                        "sections": [
                            {
                                "section_id": "result",
                                "kind": "SUPPORTED",
                                "text": "入口的 run 函数返回 ok，并附带题外说明。",
                                "checklist_item_ids": ["check-1"],
                                "evidence_ids": ["evidence-1"],
                            }
                        ]
                    }
                ]
            ),
            configuration(),
        ).generate(
            checklist=checklist,
            packet=packet,
            revision=1,
            prior_draft=None,
            review_findings=(),
            execution_ref="review-repair:draft",
        )
        invalid = {
            "checks": {
                "QUESTION_FIDELITY": True,
                "EVIDENCE_GROUNDING": True,
                "REQUEST_COMPLETENESS": True,
                "RESPONSE_LANGUAGE": True,
                "RELEVANCE_READABILITY": False,
            },
            "decision": "REWRITE_REQUIRED",
            "findings": [
                {
                    "checklist_item_id": "check-1",
                    "category": "IRRELEVANT_CONTENT",
                    "description": "Remove the unrequested explanation.",
                    "evidence_ids": [],
                }
            ],
        }
        repaired = json.loads(json.dumps(invalid))
        repaired["findings"][0]["evidence_ids"] = ["evidence-1"]
        gateway = SequencedGateway([invalid, repaired])

        review = ModelIndependentEvidenceAnswerReviewer(
            gateway, configuration()
        ).review(
            checklist=checklist,
            packet=packet,
            draft=draft,
            execution_ref="review-repair:review",
        )

        self.assertEqual(review.decision.value, "REWRITE_REQUIRED")
        self.assertEqual(review.findings[0].evidence_ids, ("evidence-1",))
        repair_state = json.loads(gateway.contexts[1].manifest.items[1].content)
        self.assertEqual(
            repair_state["contract_repair"]["rejected_output_reason"],
            "rewrite findings must identify existing evidence",
        )


if __name__ == "__main__":
    unittest.main()
