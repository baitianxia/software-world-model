from __future__ import annotations

import json
import hashlib
from dataclasses import replace
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from software_world_model.ai_infrastructure import (
    AgenticKnowledgeStrategyBundle,
    AgenticModelStrategyConfiguration,
    ModelNeedSufficiencyEvaluator,
    ModelReviewedKnowledgeBuilder,
    ModelReviewedKnowledgeRequirementPlanner,
    MAX_REQUIREMENT_NEEDS,
    ModelSemanticAnswerReviewer,
    ModelSourceClosedAnswerDraftPlanner,
    ModelSourceInvestigationPlanner,
    agentic_knowledge_strategy_implementation_digest,
    agentic_knowledge_output_schemas,
    PlatformProposalMode,
    RuntimeAccessMode,
)
from software_world_model.ai_infrastructure.agentic_knowledge_strategy import (
    _artifact_view,
    _authorized_artifact_view_matches,
    _candidate_patch_views,
    _candidate_contract_violations,
    _candidate_views,
    _coverage_audit_batches,
    _coverage_audit_plan,
    _coverage_audit_units,
    _fact_review_with_normalized_decision,
    _fact_text,
    _focused_sequence_audit_batches,
    _inference_review_decision,
    _need_coverage_consensus_anchor_findings,
    _need_coverage_decision,
    _reviewed_candidate_keys,
    _repair_artifact_views,
    _requires_completeness_challenge,
    _saturation_challenge_batch_index,
    _sequence_analysis,
    _validate_candidate_source_authority,
    _validate_sequence_split_repair,
)
from software_world_model.application_services import (
    AnswerNeedEvidence,
    JointConstraint,
    KnowledgeNeed,
    KnowledgeReadSet,
    KnowledgeRequirement,
    KnowledgeRequirementPlan,
    NeedStatus,
    RequirementFidelity,
    ReviewDimension,
)
from software_world_model.cross_cutting import (
    Digest,
    DomainError,
    ErrorCode,
    Revision,
    StableId,
    digest_of,
)
from software_world_model.knowledge_engine import FormalKnowledgeRecord, KnowledgeObjectKind
from software_world_model.source_integration import SourceArtifact, SourceTool, TargetKind


class FakeGateway:
    def __init__(self, output, *, eligible=True, reason="ELIGIBLE"):
        self.output = output
        self.eligible = eligible
        self.reason = reason
        self.contexts = []
        self.calls = 0

    def invoke(self, context):
        self.contexts.append(context)
        self.calls += 1
        output_text = json.dumps(self.output) if self.output is not None else None
        return SimpleNamespace(
            call=SimpleNamespace(
                model_call_id=StableId(f"model_call_{self.calls:032x}"),
                actual_model_fingerprint="fixture-fingerprint",
            ),
            eligibility=SimpleNamespace(
                eligible_for_production_domain_output=self.eligible,
                reason=self.reason,
            ),
            response=(
                SimpleNamespace(
                    output_text=output_text,
                    output_digest=digest_of(output_text),
                )
                if self.output is not None
                else None
            ),
        )


class SequencedGateway(FakeGateway):
    def __init__(self, outputs, *, replay_audits=True):
        super().__init__(None)
        self.outputs = list(outputs)
        self.replay_audits = replay_audits
        self.outputs_by_capability = {}

    def invoke(self, context):
        state = json.loads(context.manifest.items[1].content)
        capability_id = context.manifest.capability_id
        is_audit = any(
            key in state
            for key in (
                "grounding_approval_audit",
                "ordering_audit",
                "approval_audit",
                "completeness_audit",
            )
        )
        if (
            self.replay_audits
            and is_audit
            and capability_id in self.outputs_by_capability
        ):
            self.output = self.outputs_by_capability[capability_id]
        else:
            self.output = self.outputs.pop(0)
            if not isinstance(self.output, (DomainError, InvalidStructuredOutput)):
                self.outputs_by_capability[capability_id] = self.output
        if isinstance(self.output, DomainError):
            self.contexts.append(context)
            self.calls += 1
            raise self.output
        if isinstance(self.output, InvalidStructuredOutput):
            self.contexts.append(context)
            self.calls += 1
            output_text = str(self.output)
            return SimpleNamespace(
                call=SimpleNamespace(
                    model_call_id=StableId(f"model_call_{self.calls:032x}"),
                    actual_model_fingerprint="fixture-fingerprint",
                    failure_code=ErrorCode.STRUCTURED_OUTPUT_INVALID.value,
                ),
                eligibility=SimpleNamespace(
                    eligible_for_production_domain_output=False,
                    reason="MODEL_OUTPUT_REJECTED_STRUCTURED_OUTPUT_INVALID",
                ),
                response=SimpleNamespace(
                    output_text=output_text,
                    output_digest=digest_of(output_text),
                    provider_request_id=f"provider-request-{self.calls}",
                    actual_model_fingerprint="fixture-fingerprint",
                    usage_complete=True,
                    input_tokens=10,
                    output_tokens=10,
                    termination_reason="stop",
                ),
            )
        return super().invoke(context)


class InvalidStructuredOutput(str):
    """A complete provider response rejected only for invalid JSON syntax."""


def need_coverage_review(
    *,
    artifact_id: str,
    need_to_candidate_keys: dict[str, list[str]],
    decision: str = "ACCEPT",
    findings: list[str] | None = None,
    unsupported_need_ids: tuple[str, ...] = (),
):
    items = []
    mapped_keys = []
    for need_id, candidate_keys in need_to_candidate_keys.items():
        if need_id in unsupported_need_ids:
            items.append(
                {
                    "need_id": need_id,
                    "source_supported": False,
                    "artifact_id": "",
                    "line_start": 0,
                    "line_end": 0,
                    "source_detail": "The supplied source does not establish this Need.",
                    "required_terms": [],
                    "candidate_required_terms": [],
                    "candidate_keys": [],
                }
            )
            continue
        items.append(
            {
                "need_id": need_id,
                "source_supported": True,
                "artifact_id": artifact_id,
                "line_start": 2,
                "line_end": 2,
                "source_detail": "The declared initializer value is 3.",
                "required_terms": ["3"],
                "candidate_required_terms": [],
                "candidate_keys": candidate_keys,
            }
        )
        mapped_keys.extend(candidate_keys)
    return {
        "decision": decision,
        "accepted_candidate_keys": list(dict.fromkeys(mapped_keys)),
        "all_supported_objective_aspects_covered": decision == "ACCEPT",
        "coverage_items": items,
        "findings": findings or [],
    }


class AgenticKnowledgeStrategyTests(unittest.TestCase):
    def test_every_sequence_reference_gets_an_individual_focus_audit(self):
        references = tuple(f"c{index}" for index in range(1, 20))

        batches = _focused_sequence_audit_batches({"N1": references})

        self.assertEqual(
            batches,
            tuple(("N1", (reference,)) for reference in references),
        )
        self.assertEqual(
            _focused_sequence_audit_batches(
                {"N1": tuple(f"c{index}" for index in range(1, 13))}
            ),
            (),
        )
        self.assertEqual(_focused_sequence_audit_batches({"N1": ("c1",)}), ())

    def test_sequence_analysis_derives_complete_order_from_compact_edges(self):
        value = {
            "edges": [
                {
                    "need_id": "N1",
                    "predecessor_reference_id": "c1",
                    "successor_reference_id": "c2",
                    "relationship": "SOURCE_PRECEDENCE",
                }
            ],
            "call_return_spans": [],
            "atomic_references": [
                {"need_id": "N1", "reference_ids": ["c1", "c2"]}
            ],
            "rationale": "AUDITED",
        }

        orders, edges, unsplittable, spans = _sequence_analysis(
            value,
            {"N1": ("c2", "c1")},
            {"N1": {"c1": "First fact.", "c2": "Second fact."}},
        )

        self.assertEqual(orders, {"N1": ("c2", "c1")})
        self.assertEqual(
            edges, (("N1", "c1", "c2", "SOURCE_PRECEDENCE"),)
        )
        self.assertEqual(unsplittable, frozenset())
        self.assertEqual(spans, ())

    def test_sequence_analysis_rejects_an_unclassified_reference(self):
        value = {
            "orders": [
                {"need_id": "N1", "reference_ids": ["c1", "c2"]}
            ],
            "edges": [],
            "call_return_spans": [],
            "atomic_references": [
                {"need_id": "N1", "reference_ids": ["c1"]}
            ],
            "rationale": "AUDITED",
        }

        with self.assertRaises(DomainError) as raised:
            _sequence_analysis(
                value,
                {"N1": ("c1", "c2")},
                {"N1": {"c1": "First fact.", "c2": "Second fact."}},
            )

        self.assertEqual(
            raised.exception.message,
            "sequence analysis does not classify every required reference exactly once",
        )
        self.assertEqual(
            raised.exception.details["classification_violations"][0][
                "missing_reference_ids"
            ],
            ("c2",),
        )

    def test_sequence_analysis_valid_span_dominates_duplicate_atomic_label(self):
        value = {
            "edges": [],
            "call_return_spans": [
                {
                    "need_id": "N1",
                    "combined_reference_id": "c1",
                    "callee_internal_reference_id": "c2",
                    "callee_subject_fragment": "App.value computes result.",
                    "invocation_fragment": "calls App.value",
                    "temporal_connector_fragment": "; after App.value returns, ",
                    "post_return_fragment": "App.main logs result",
                }
            ],
            "atomic_references": [
                {"need_id": "N1", "reference_ids": ["c1", "c2"]}
            ],
            "rationale": "AUDITED",
        }

        _, _, unsplittable, spans = _sequence_analysis(
            value,
            {"N1": ("c1", "c2")},
            {
                "N1": {
                    "c1": (
                        "App.main calls App.value; after App.value returns, "
                        "App.main logs result."
                    ),
                    "c2": "App.value computes result.",
                }
            },
        )

        self.assertEqual(unsplittable, frozenset({"c1"}))
        self.assertEqual(spans[0][:3], ("N1", "c1", "c2"))

    def test_sequence_analysis_preserves_exact_connector_post_return_overlap(self):
        value = {
            "edges": [],
            "call_return_spans": [
                {
                    "need_id": "N1",
                    "combined_reference_id": "c1",
                    "callee_internal_reference_id": "c2",
                    "callee_subject_fragment": "App.value computes result.",
                    "invocation_fragment": "calls App.value",
                    "temporal_connector_fragment": "and then",
                    "post_return_fragment": "then records result",
                }
            ],
            "atomic_references": [
                {"need_id": "N1", "reference_ids": ["c1", "c2"]}
            ],
            "rationale": "AUDITED",
        }

        _, _, unsplittable, spans = _sequence_analysis(
            value,
            {"N1": ("c1", "c2")},
            {
                "N1": {
                    "c1": "App.main calls App.value and then records result.",
                    "c2": "App.value computes result.",
                }
            },
            ignore_invalid_evidence_spans=True,
        )

        self.assertEqual(unsplittable, frozenset({"c1"}))
        self.assertEqual(spans[0][:3], ("N1", "c1", "c2"))

    def test_restricted_sequence_positive_span_dominates_extra_atomic_labels(self):
        value = {
            "edges": [],
            "call_return_spans": [
                {
                    "need_id": "N1",
                    "combined_reference_id": "c1",
                    "callee_internal_reference_id": "c2",
                    "callee_subject_fragment": "App.value computes result.",
                    "invocation_fragment": "calls App.value",
                    "temporal_connector_fragment": "; after it returns, ",
                    "post_return_fragment": "App.main records result",
                }
            ],
            "atomic_references": [
                {
                    "need_id": "N1",
                    "reference_ids": ["c1", "c2", "c3"],
                }
            ],
            "rationale": "AUDITED",
        }

        _, _, unsplittable, spans = _sequence_analysis(
            value,
            {"N1": ("c1", "c2", "c3")},
            {
                "N1": {
                    "c1": (
                        "App.main calls App.value; after it returns, "
                        "App.main records result."
                    ),
                    "c2": "App.value computes result.",
                    "c3": "App.other prepares input.",
                }
            },
            required_classified_reference_ids_by_need={"N1": ("c1",)},
        )

        self.assertEqual(unsplittable, frozenset({"c1"}))
        self.assertEqual(spans[0][:3], ("N1", "c1", "c2"))

    def test_sequence_analysis_rejects_duplicate_atomic_annotations(self):
        value = {
            "edges": [],
            "call_return_spans": [],
            "atomic_references": [
                {"need_id": "N1", "reference_ids": ["c1", "c1"]},
                {"need_id": "N1", "reference_ids": ["c2", "c1"]},
            ],
            "rationale": "AUDITED",
        }

        with self.assertRaises(DomainError) as raised:
            _sequence_analysis(
                value,
                {"N1": ("c1", "c2")},
                {"N1": {"c1": "First fact.", "c2": "Second fact."}},
            )

        self.assertEqual(
            raised.exception.message,
            "sequence analysis repeats an atomic classification",
        )

    def test_sequence_analysis_reports_exact_atomic_item_shape(self):
        value = {
            "edges": [],
            "call_return_spans": [],
            "atomic_references": [
                {"need_id": "N1", "reference_id": "c1"}
            ],
            "rationale": "AUDITED",
        }

        with self.assertRaises(DomainError) as raised:
            _sequence_analysis(
                value,
                {"N1": ("c1",)},
                {"N1": {"c1": "First fact."}},
                required_classified_reference_ids_by_need={"N1": ("c1",)},
            )

        self.assertEqual(
            raised.exception.message,
            "sequence analysis atomic reference audit is invalid",
        )
        self.assertEqual(
            raised.exception.details["provided_keys"],
            ("need_id", "reference_id"),
        )
        self.assertEqual(
            raised.exception.details["expected_keys"],
            ("need_id", "reference_ids"),
        )
        self.assertIn(
            "do not use reference_id",
            raised.exception.details["required_action"],
        )

    def test_sequence_analysis_rejects_an_unknown_atomic_reference(self):
        value = {
            "edges": [],
            "call_return_spans": [],
            "atomic_references": [
                {"need_id": "N1", "reference_ids": ["c1", "unknown"]}
            ],
            "rationale": "AUDITED",
        }

        with self.assertRaises(DomainError) as raised:
            _sequence_analysis(
                value,
                {"N1": ("c1", "c2")},
                {"N1": {"c1": "First fact.", "c2": "Second fact."}},
            )

        self.assertEqual(
            raised.exception.details["unknown_reference_ids"],
            ("unknown",),
        )

    def test_sequence_analysis_requires_exact_focused_caller_classification(self):
        texts = {
            "N1": {
                "c1": "First fact.",
                "c2": "Second fact.",
                "c3": "Third fact.",
            }
        }
        focused_atomic = {
            "edges": [],
            "call_return_spans": [],
            "atomic_references": [
                {"need_id": "N1", "reference_ids": ["c2"]}
            ],
            "rationale": "AUDITED",
        }

        _, _, unsplittable, spans = _sequence_analysis(
            focused_atomic,
            {"N1": ("c1", "c2", "c3")},
            texts,
            required_classified_reference_ids_by_need={"N1": ("c2",)},
        )

        self.assertFalse(unsplittable)
        self.assertFalse(spans)
        with self.assertRaises(DomainError) as missing:
            _sequence_analysis(
                {**focused_atomic, "atomic_references": []},
                {"N1": ("c1", "c2", "c3")},
                texts,
                required_classified_reference_ids_by_need={"N1": ("c2",)},
            )
        self.assertEqual(
            missing.exception.details["classification_violations"][0][
                "missing_reference_ids"
            ],
            ("c2",),
        )
        with self.assertRaises(DomainError) as extra:
            _sequence_analysis(
                {
                    **focused_atomic,
                    "atomic_references": [
                        {"need_id": "N1", "reference_ids": ["c1", "c2"]}
                    ],
                },
                {"N1": ("c1", "c2", "c3")},
                texts,
                required_classified_reference_ids_by_need={"N1": ("c2",)},
            )
        self.assertEqual(
            extra.exception.details["classification_violations"][0][
                "unexpected_atomic_reference_ids"
            ],
            ("c1",),
        )

    def test_sequence_analysis_infers_uniquely_scoped_span_need(self):
        value = {
            "edges": [],
            "call_return_spans": [
                {
                    "combined_reference_id": "c1",
                    "callee_internal_reference_id": "c2",
                    "callee_subject_fragment": "App.value",
                    "invocation_fragment": "calls App.value",
                    "temporal_connector_fragment": "and then",
                    "post_return_fragment": "returns its result",
                }
            ],
            "atomic_references": [
                {"need_id": "N1", "reference_ids": ["c2"]}
            ],
            "rationale": "AUDITED",
        }
        texts = {
            "N1": {
                "c1": "App.main calls App.value and then returns its result.",
                "c2": "App.value computes the declared value.",
            }
        }

        _, _, unsplittable, spans = _sequence_analysis(
            value,
            {"N1": ("c1", "c2")},
            texts,
        )

        self.assertEqual(unsplittable, frozenset({"c1"}))
        self.assertEqual(spans[0][:3], ("N1", "c1", "c2"))

    def test_sequence_analysis_rejects_ambiguous_inferred_span_need(self):
        value = {
            "edges": [],
            "call_return_spans": [
                {
                    "combined_reference_id": "c1",
                    "callee_internal_reference_id": "c2",
                    "callee_subject_fragment": "App.value",
                    "invocation_fragment": "calls App.value",
                    "temporal_connector_fragment": "and then",
                    "post_return_fragment": "returns its result",
                }
            ],
            "atomic_references": [],
            "rationale": "AUDITED",
        }
        caller_text = "App.main calls App.value and then returns its result."
        callee_text = "App.value computes the declared value."

        with self.assertRaises(DomainError) as raised:
            _sequence_analysis(
                value,
                {"N1": ("c1", "c2"), "N2": ("c1", "c2")},
                {
                    "N1": {"c1": caller_text, "c2": callee_text},
                    "N2": {"c1": caller_text, "c2": callee_text},
                },
            )

        self.assertEqual(
            raised.exception.message,
            "sequence analysis call-return span has ambiguous Need scope",
        )

    def test_sequence_analysis_keeps_inference_atomic_after_selected_premise(self):
        value = {
            "orders": [
                {"need_id": "N1", "reference_ids": ["r2", "r1"]}
            ],
            "edges": [],
            "call_return_spans": [],
            "atomic_references": [
                {"need_id": "N1", "reference_ids": ["r1", "r2"]}
            ],
            "rationale": "AUDITED",
        }

        orders, edges, unsplittable, spans = _sequence_analysis(
            value,
            {"N1": ("r1", "r2")},
            {"N1": {"r1": "A formal fact.", "r2": "A derived relation."}},
            inference_reference_ids_by_need={"N1": frozenset({"r2"})},
            inference_premise_edges_by_need={"N1": (("r1", "r2"),)},
        )

        self.assertEqual(orders["N1"], ("r2", "r1"))
        self.assertIn(("N1", "r1", "r2", "SOURCE_PRECEDENCE"), edges)
        self.assertFalse(unsplittable)
        self.assertFalse(spans)

        invalid = {
            **value,
            "call_return_spans": [
                {
                    "need_id": "N1",
                    "combined_reference_id": "r2",
                    "callee_internal_reference_id": "r1",
                    "callee_subject_fragment": "formal fact",
                    "invocation_fragment": "derived",
                    "temporal_connector_fragment": " ",
                    "post_return_fragment": "relation",
                }
            ],
            "atomic_references": [
                {"need_id": "N1", "reference_ids": ["r1"]}
            ],
        }
        with self.assertRaises(DomainError):
            _sequence_analysis(
                invalid,
                {"N1": ("r1", "r2")},
                {"N1": {"r1": "A formal fact.", "r2": "A derived relation."}},
                inference_reference_ids_by_need={"N1": frozenset({"r2"})},
            )

    def test_fact_review_recovers_only_a_uniquely_implied_decision(self):
        accepted = _fact_review_with_normalized_decision(
            {
                "accepted_candidate_keys": ["c1"],
                "all_supported_objective_aspects_covered": True,
                "findings": [],
            }
        )
        rejected = _fact_review_with_normalized_decision(
            {
                "accepted_candidate_keys": ["c1"],
                "all_supported_objective_aspects_covered": False,
                "findings": ["c2 is not grounded."],
            }
        )
        ambiguous = {
            "accepted_candidate_keys": [],
            "all_supported_objective_aspects_covered": False,
            "findings": [],
        }

        self.assertEqual(accepted["decision"], "ACCEPT")
        self.assertEqual(rejected["decision"], "REJECT")
        self.assertEqual(
            _fact_review_with_normalized_decision(ambiguous),
            ambiguous,
        )

    def test_reviewed_candidate_validation_accepts_uniquely_recovered_decision(self):
        candidate = {
            "candidate_key": "c1",
            "need_ids": ["N1"],
        }
        review = _fact_review_with_normalized_decision(
            {
                "accepted_candidate_keys": ["c1"],
                "all_supported_objective_aspects_covered": True,
                "findings": [],
            }
        )

        self.assertEqual(
            _reviewed_candidate_keys(review, [candidate]),
            frozenset({"c1"}),
        )

    def test_fact_review_invalid_accept_lists_missing_candidate_keys(self):
        candidates = [
            {"candidate_key": "c1", "need_ids": ["N1"]},
            {"candidate_key": "c2", "need_ids": ["N1"]},
        ]
        review = {
            "decision": "ACCEPT",
            "accepted_candidate_keys": ["c1"],
            "all_supported_objective_aspects_covered": True,
            "findings": [],
        }

        with self.assertRaises(DomainError) as raised:
            _reviewed_candidate_keys(review, candidates)

        self.assertEqual(
            raised.exception.details["known_candidate_keys"],
            ("c1", "c2"),
        )
        self.assertEqual(
            raised.exception.details["missing_candidate_keys"],
            ("c2",),
        )
        self.assertEqual(
            raised.exception.details["unknown_candidate_keys"],
            (),
        )
        self.assertIn(
            "include every known candidate key exactly once",
            raised.exception.details["required_action"],
        )

    def request(self):
        return SimpleNamespace(
            idempotency_key=SimpleNamespace(value="agentic-test"),
            objective=SimpleNamespace(
                objective_id="objective:agentic-test",
                description="Find the exact declaration of App",
                unacceptable_outcomes=("invented source",),
                digest=digest_of("objective"),
            ),
            target=SimpleNamespace(
                target_kind=TargetKind.REPOSITORY_REVISION,
                canonical_identity=(("revision", "a" * 40),),
                boundary="EXACT",
                digest=digest_of("target"),
            ),
            max_steps=8,
            max_items_per_step=20,
            max_bytes_per_step=4096,
            classification="INTERNAL",
            allowed_source_paths=("src/App.java",),
        )

    def configuration(self):
        return AgenticModelStrategyConfiguration(
            provider_type="TEST_NO_TOOLS",
            adapter_version="1",
            model_ref="fixture@1",
            provider_configuration_fingerprint=Digest("sha256:" + "0" * 64),
            qualification_ref="capability-evaluation:test@1",
            sequence_analysis_enabled=False,
        )

    def test_every_model_role_binds_the_same_strategy_implementation(self):
        gateway = FakeGateway({"unused": True})
        configuration = self.configuration()
        bundle = AgenticKnowledgeStrategyBundle.create(gateway, configuration)
        components = (
            bundle.requirement_planner,
            bundle.source_planner,
            bundle.knowledge_builder,
            bundle.sufficiency_evaluator,
            bundle.answer_planner,
            bundle.answer_reviewer,
        )

        expected = agentic_knowledge_strategy_implementation_digest()
        self.assertEqual(bundle.implementation_digest, expected)
        self.assertEqual(len(agentic_knowledge_output_schemas()), 13)
        self.assertTrue(
            all(
                component.strategy_implementation_digest == expected
                for component in components
            )
        )

    def test_reviewed_inference_connects_only_published_formal_premises(self):
        need = KnowledgeNeed(
            need_id="N1",
            question="为什么特殊策略从普通阶段延后到后续阶段执行？",
            required_kinds=(KnowledgeObjectKind.FACT, KnowledgeObjectKind.INFERENCE),
            required_type_names=(),
            required_terms=("特殊策略", "普通阶段", "后续阶段"),
            minimum_support_count=1,
        )
        plan = KnowledgeRequirementPlan(needs=(need,))
        request = self.request()
        request.requirement_plan = plan
        request.objective.description = need.question
        premises = (
            FormalKnowledgeRecord(
                kind=KnowledgeObjectKind.FACT,
                object_id=StableId("knowledge_fact_00000000000000000000000000000001"),
                object_digest=digest_of("order"),
                type_name="CALLS",
                text="外层流程先调用普通阶段，随后调用后续阶段。",
                context_digest=digest_of("context"),
                support_references=(),
                reviewed_need_ids=("N1",),
            ),
            FormalKnowledgeRecord(
                kind=KnowledgeObjectKind.FACT,
                object_id=StableId("knowledge_fact_00000000000000000000000000000002"),
                object_digest=digest_of("skip"),
                type_name="DESCRIBED_AS",
                text="普通阶段遇到特殊策略时直接返回，不调用该策略。",
                context_digest=digest_of("context"),
                support_references=(),
                reviewed_need_ids=("N1",),
            ),
            FormalKnowledgeRecord(
                kind=KnowledgeObjectKind.FACT,
                object_id=StableId("knowledge_fact_00000000000000000000000000000003"),
                object_digest=digest_of("later"),
                type_name="DESCRIBED_AS",
                text="后续阶段检测特殊策略，重新加载状态后单独调用该策略。",
                context_digest=digest_of("context"),
                support_references=(),
                reviewed_need_ids=("N1",),
            ),
        )
        proposal = {
            "candidates": [
                {
                    "candidate_key": "i1",
                    "need_ids": ["N1"],
                    "inference_type": "BEHAVIOR",
                    "proposition": (
                        "特殊策略在普通阶段被跳过，因此延后到后续阶段检测并重新加载后单独执行。"
                    ),
                    "premise_reference_ids": [
                        item.object_id.value for item in premises
                    ],
                }
            ]
        }
        review = {
            "accepted_candidate_keys": ["i1"],
            "all_requested_relationships_covered": True,
            "findings": [],
        }
        malformed_review = dict(review)
        malformed_review.pop("findings")
        gateway = SequencedGateway(
            (proposal, malformed_review, review, review),
            replay_audits=False,
        )

        bundle = ModelReviewedKnowledgeBuilder(
            gateway, self.configuration()
        ).build_inferences(
            request=request,
            target=request.target,
            premises=premises,
        )

        self.assertEqual(gateway.calls, 4)
        self.assertEqual(len(bundle.inferences), 1)
        inference = bundle.inferences[0]
        self.assertEqual(inference.reviewed_need_ids, ("N1",))
        self.assertEqual(
            inference.premise_references,
            tuple(item.object_id for item in premises),
        )
        self.assertTrue(inference.rule_ref.startswith("reviewed-model-inference@2:"))
        self.assertIn(
            "do not demand an undocumented design rationale",
            gateway.contexts[1].manifest.items[0].content,
        )
        repair_state = json.loads(gateway.contexts[2].manifest.items[1].content)
        self.assertIn("contract_repair", repair_state)
        audit_state = json.loads(gateway.contexts[3].manifest.items[1].content)
        self.assertEqual(
            audit_state["review_phase"]["kind"],
            "INFERENCE_MINIMALITY_APPROVAL_AUDIT",
        )

    def test_inference_rejection_derives_decision_without_redundant_field(self):
        accepted, findings, complete = _inference_review_decision(
            {
                "accepted_candidate_keys": ["i1"],
                "all_requested_relationships_covered": False,
                "findings": ["i2 combines two independent connectors"],
            },
            ("i1", "i2"),
        )

        self.assertEqual(accepted, frozenset({"i1"}))
        self.assertEqual(
            findings, ("i2 combines two independent connectors",)
        )
        self.assertFalse(complete)

    def test_inference_proposer_repairs_proposition_to_request_script(self):
        need = KnowledgeNeed(
            need_id="N1",
            question="为什么后续阶段在普通阶段之后执行？",
            required_kinds=(KnowledgeObjectKind.FACT, KnowledgeObjectKind.INFERENCE),
            required_type_names=(),
            required_terms=("普通阶段", "后续阶段"),
            minimum_support_count=1,
        )
        request = self.request()
        request.requirement_plan = KnowledgeRequirementPlan(needs=(need,))
        request.objective.description = need.question
        premises = tuple(
            FormalKnowledgeRecord(
                kind=KnowledgeObjectKind.FACT,
                object_id=StableId(
                    f"knowledge_fact_{index:032d}"
                ),
                object_digest=digest_of(text),
                type_name="CALLS",
                text=text,
                context_digest=digest_of("context"),
                support_references=(),
                reviewed_need_ids=("N1",),
            )
            for index, text in enumerate(
                (
                    "外层流程先调用普通阶段。",
                    "普通阶段结束后调用后续阶段。",
                ),
                1,
            )
        )
        english = {
            "candidates": [
                {
                    "candidate_key": "i1",
                    "need_ids": ["N1"],
                    "inference_type": "STRUCTURE",
                    "proposition": "The later stage executes after the ordinary stage.",
                    "premise_reference_ids": [
                        item.object_id.value for item in premises
                    ],
                }
            ]
        }
        chinese = json.loads(json.dumps(english))
        chinese["candidates"][0]["proposition"] = (
            "后续阶段在普通阶段结束之后执行。"
        )
        review = {
            "accepted_candidate_keys": ["i1"],
            "all_requested_relationships_covered": True,
            "findings": [],
        }
        gateway = SequencedGateway(
            (english, chinese, review, review), replay_audits=False
        )

        bundle = ModelReviewedKnowledgeBuilder(
            gateway, self.configuration()
        ).build_inferences(
            request=request,
            target=request.target,
            premises=premises,
        )

        self.assertEqual(gateway.calls, 4)
        self.assertEqual(
            bundle.inferences[0].proposition,
            chinese["candidates"][0]["proposition"],
        )
        initial_state = json.loads(gateway.contexts[0].manifest.items[1].content)
        self.assertEqual(
            initial_state["response_language_contract"][
                "required_unicode_script"
            ],
            "CJK",
        )
        repair_state = json.loads(gateway.contexts[1].manifest.items[1].content)
        self.assertEqual(
            repair_state["repair"]["contract_error_details"][
                "required_response_script"
            ],
            "CJK",
        )

    def test_repair_artifact_authorization_verifies_exact_included_lines(self):
        artifact = self.artifact()
        complete_view = _artifact_view(artifact)
        candidate = {
            "artifact_id": artifact.artifact_id.value,
            "line_start": 2,
            "line_end": 2,
        }

        repair_view = _repair_artifact_views(
            [complete_view], [candidate], []
        )[0]

        self.assertTrue(
            _authorized_artifact_view_matches(
                repair_view,
                complete_view,
                line_start=2,
                line_end=2,
            )
        )
        self.assertFalse(
            _authorized_artifact_view_matches(
                repair_view,
                complete_view,
                line_start=1,
                line_end=2,
            )
        )
        tampered_view = {
            **repair_view,
            "numbered_content": "2:     int value = 4;",
        }
        self.assertFalse(
            _authorized_artifact_view_matches(
                tampered_view,
                complete_view,
                line_start=2,
                line_end=2,
            )
        )

    def test_repair_artifact_window_explicitly_includes_four_gap_lines(self):
        payload = b"first\nsecond\ngap-1\ngap-2\ngap-3\ngap-4\nseventh\neighth\n"
        artifact = replace(
            self.artifact(),
            payload=payload,
            content_digest=Digest(
                f"sha256:{hashlib.sha256(payload).hexdigest()}"
            ),
        )
        complete_view = _artifact_view(artifact)

        repair_view = _repair_artifact_views(
            [complete_view],
            [
                {
                    "artifact_id": artifact.artifact_id.value,
                    "line_start": 2,
                    "line_end": 2,
                }
            ],
            [(artifact.artifact_id.value, 7, 7)],
        )[0]

        self.assertEqual(
            repair_view["included_line_ranges"],
            ({"line_start": 2, "line_end": 7},),
        )
        self.assertEqual(
            repair_view["numbered_content"],
            "2: second\n3: gap-1\n4: gap-2\n5: gap-3\n6: gap-4\n7: seventh",
        )
        self.assertTrue(
            _authorized_artifact_view_matches(
                repair_view,
                complete_view,
                line_start=2,
                line_end=7,
            )
        )

    def test_candidate_cannot_span_lines_hidden_from_its_proposal(self):
        payload = b"first\nsecond\nhidden-1\nhidden-2\nhidden-3\nhidden-4\nhidden-5\neighth\n"
        artifact = replace(
            self.artifact(),
            payload=payload,
            content_digest=Digest(
                f"sha256:{hashlib.sha256(payload).hexdigest()}"
            ),
        )
        complete_view = _artifact_view(artifact)
        authorized_view = _repair_artifact_views(
            [complete_view],
            [
                {
                    "artifact_id": artifact.artifact_id.value,
                    "line_start": 2,
                    "line_end": 2,
                }
            ],
            [(artifact.artifact_id.value, 8, 8)],
        )[0]
        candidate = {
            "candidate_key": "c1",
            "artifact_id": artifact.artifact_id.value,
            "line_start": 2,
            "line_end": 8,
        }

        with self.assertRaises(DomainError) as raised:
            _validate_candidate_source_authority(
                [candidate],
                authorized_artifact_views=[authorized_view],
                complete_artifact_views=[complete_view],
            )

        self.assertEqual(
            raised.exception.details["validation_violations"],
            ("CANDIDATE_SOURCE_RANGE_NOT_AUTHORIZED",),
        )
        self.assertEqual(
            authorized_view["included_line_ranges"],
            (
                {"line_start": 2, "line_end": 2},
                {"line_start": 8, "line_end": 8},
            ),
        )

    def artifact(self):
        payload = b"public class App {\n    int value = 3;\n}\n"
        return SourceArtifact(
            artifact_id=StableId("artifact_00000000000000000000000000000001"),
            artifact_kind="LOCAL_GIT_FILE@1",
            payload_schema_version="LOCAL_GIT_FILE@1",
            source_id=StableId("source_00000000000000000000000000000001"),
            source_revision=SimpleNamespace(value=1),
            source_context_id=StableId(
                "context_00000000000000000000000000000001"
            ),
            source_native_identity="src/App.java",
            content_digest=Digest(f"sha256:{hashlib.sha256(payload).hexdigest()}"),
            payload=payload,
            classification="INTERNAL",
            truncated=False,
            truncation_offset=None,
            identity_digest=digest_of("artifact-identity"),
        )

    def completed_read(
        self, *, start=0, end=32, has_more=False, revision=None
    ):
        path = "src/App.java"
        revision = revision or "a" * 40
        observation = SimpleNamespace(
            tool=SourceTool.READ,
            source_context=SimpleNamespace(
                repository_revision=revision,
                subject=path,
            ),
            subject=path,
            coverage=(
                ("path", path),
                ("range", f"bytes:{start}-{end}"),
                ("revision", revision),
            ),
            item_count=1,
            byte_count=end - start,
            has_more=has_more,
            next_cursor=str(end) if has_more else None,
            artifacts=(),
        )
        return SimpleNamespace(
            operation_id=StableId(
                f"operation_{start + end + int(has_more):032x}"
            ),
            status=SimpleNamespace(value="PARTIAL" if has_more else "COMPLETED"),
            failure_code=None,
            observation=observation,
        )

    def completed_empty_search(self, ordinal: int, *, query: str | None = None):
        query = query or f"missing-{ordinal}"
        observation = SimpleNamespace(
            tool=SourceTool.SEARCH,
            source_context=SimpleNamespace(
                repository_revision="a" * 40,
                subject=f"search:{query}",
            ),
            subject=f"search:{query}",
            coverage=(("revision", "a" * 40),),
            item_count=0,
            byte_count=0,
            has_more=False,
            next_cursor=None,
            artifacts=(),
        )
        return SimpleNamespace(
            operation_id=StableId(f"operation_{ordinal:032x}"),
            status=SimpleNamespace(value="COMPLETED"),
            failure_code=None,
            observation=observation,
        )

    def formal_need_state(self):
        record = FormalKnowledgeRecord(
            kind=KnowledgeObjectKind.FACT,
            object_id=StableId("knowledge_fact_00000000000000000000000000000001"),
            object_digest=digest_of("App.value is initialized to 3."),
            type_name="HAS_VALUE",
            text="App.value is initialized to 3.",
            context_digest=digest_of({"revision": "a" * 40}),
            support_references=(
                StableId("evidence_00000000000000000000000000000001"),
            ),
        )
        need = KnowledgeNeed(
            need_id="need:initializer",
            question="What source initializer is declared for App.value?",
            required_kinds=(KnowledgeObjectKind.FACT,),
            required_type_names=("HAS_VALUE",),
            required_terms=("App.value",),
            minimum_support_count=1,
        )
        requirement = KnowledgeRequirement.create(
            requirement_id=StableId(
                "requirement_00000000000000000000000000000001"
            ),
            revision=Revision(1),
            fidelity=RequirementFidelity.ORIGINAL,
            original_request="What source initializer is declared for App.value?",
            needs=(need,),
        )
        read_set = KnowledgeReadSet(
            need_id=need.need_id,
            records=(record,),
            query_digest=digest_of("query"),
            complete=True,
            digest=digest_of(
                {
                    "need_id": need.need_id,
                    "records": ((record.object_id.value, record.object_digest.value),),
                }
            ),
        )
        return requirement, need, read_set, record

    def test_eligible_model_output_becomes_untrusted_read_proposal(self):
        gateway = FakeGateway(
            {
                "decision": "EXECUTE",
                "tool": "READ",
                "revision": "a" * 40,
                "base": "",
                "path": "src/App.java",
                "query": "",
                "cursor": "",
                "offset": "",
                "max_bytes": "4096",
                "page_size": "",
                "rationale": "Read the relevant declaration.",
            }
        )
        planner = ModelSourceInvestigationPlanner(gateway, self.configuration())

        proposal = planner.propose(
            request=self.request(), completed_operations=(), ordinal=1
        )

        self.assertEqual(proposal.tool, SourceTool.READ)
        self.assertEqual(
            dict(proposal.parameters),
            {
                "max_bytes": "4096",
                "path": "src/App.java",
                "revision": "a" * 40,
            },
        )
        context = gateway.contexts[0]
        self.assertEqual(context.runtime_access_mode, RuntimeAccessMode.NO_EXTERNAL_ACCESS)
        self.assertEqual(
            context.platform_proposal_mode,
            PlatformProposalMode.DECLARED_PLATFORM_PROPOSAL_ONLY,
        )
        state = json.loads(context.manifest.items[1].content)
        self.assertEqual(state["target"]["identity"]["revision"], "a" * 40)
        self.assertEqual(state["completed_operations"], [])

    def test_ineligible_model_output_never_becomes_a_proposal(self):
        gateway = FakeGateway(None, eligible=False, reason="MODEL_FINGERPRINT_NOT_EVALUATED")
        planner = ModelSourceInvestigationPlanner(gateway, self.configuration())

        with self.assertRaises(DomainError) as raised:
            planner.propose(request=self.request(), completed_operations=(), ordinal=1)

        self.assertEqual(raised.exception.code, ErrorCode.CONTROL_STATE_DENIED)
        self.assertEqual(gateway.calls, 1)

    def test_stop_output_ignores_exact_authorized_revision_echo(self):
        gateway = FakeGateway(
            {
                "decision": "STOP",
                "tool": "NONE",
                "revision": "a" * 40,
                "base": "",
                "path": "",
                "query": "",
                "cursor": "",
                "offset": "",
                "max_bytes": "",
                "page_size": "",
                "rationale": "Stop.",
            }
        )
        planner = ModelSourceInvestigationPlanner(gateway, self.configuration())

        proposal = planner.propose(
            request=self.request(), completed_operations=(), ordinal=1
        )

        self.assertTrue(proposal.stop)
        self.assertEqual(gateway.calls, 1)

    def test_stop_output_ignores_exact_authorized_comparison_echoes(self):
        request = self.request()
        request.target.canonical_identity = (
            ("base", "b" * 40),
            ("target", "a" * 40),
        )
        gateway = FakeGateway(
            {
                "decision": "STOP",
                "tool": "NONE",
                "revision": "a" * 40,
                "base": "b" * 40,
                "path": "",
                "query": "",
                "cursor": "",
                "offset": "",
                "max_bytes": "",
                "page_size": "",
                "rationale": "Stop.",
            }
        )
        planner = ModelSourceInvestigationPlanner(gateway, self.configuration())

        proposal = planner.propose(
            request=request, completed_operations=(), ordinal=1
        )

        self.assertTrue(proposal.stop)
        self.assertEqual(gateway.calls, 1)

    def test_compare_must_use_the_exact_authorized_base_to_target_direction(self):
        request = self.request()
        request.target.canonical_identity = (
            ("base", "b" * 40),
            ("target", "a" * 40),
        )
        invalid = {
            "decision": "EXECUTE",
            "tool": "COMPARE",
            "revision": "b" * 40,
            "base": "b" * 40,
            "path": "",
            "query": "",
            "cursor": "",
            "offset": "",
            "max_bytes": "",
            "page_size": "",
            "rationale": "Compare the parent to itself.",
        }
        corrected = {
            **invalid,
            "revision": "a" * 40,
            "rationale": "Compare the exact parent to the exact target.",
        }
        gateway = SequencedGateway((invalid, corrected))

        proposal = ModelSourceInvestigationPlanner(
            gateway, self.configuration()
        ).propose(request=request, completed_operations=(), ordinal=1)

        self.assertEqual(proposal.tool, SourceTool.COMPARE)
        self.assertEqual(
            dict(proposal.parameters),
            {"base": "b" * 40, "revision": "a" * 40},
        )
        repair = json.loads(gateway.contexts[1].manifest.items[-1].content)
        self.assertEqual(repair["last_error_details"]["expected_base"], "b" * 40)
        self.assertEqual(
            repair["last_error_details"]["expected_revision"], "a" * 40
        )

    def test_stop_output_rejects_unauthorized_revision(self):
        gateway = FakeGateway(
            {
                "decision": "STOP",
                "tool": "NONE",
                "revision": "b" * 40,
                "base": "",
                "path": "",
                "query": "",
                "cursor": "",
                "offset": "",
                "max_bytes": "",
                "page_size": "",
                "rationale": "Stop.",
            }
        )
        planner = ModelSourceInvestigationPlanner(gateway, self.configuration())

        with self.assertRaises(DomainError) as raised:
            planner.propose(request=self.request(), completed_operations=(), ordinal=1)

        self.assertEqual(raised.exception.code, ErrorCode.STRUCTURED_OUTPUT_INVALID)
        self.assertEqual(gateway.calls, 3)

    def test_source_planner_retries_contradictory_decision_and_tool(self):
        contradictory = {
            "decision": "EXECUTE",
            "tool": "NONE",
            "revision": "",
            "base": "",
            "path": "",
            "query": "",
            "cursor": "",
            "offset": "",
            "max_bytes": "",
            "page_size": "",
            "rationale": "The observations are sufficient, so stop.",
        }
        corrected = {**contradictory, "decision": "STOP"}
        gateway = SequencedGateway((contradictory, corrected))
        planner = ModelSourceInvestigationPlanner(gateway, self.configuration())

        proposal = planner.propose(
            request=self.request(), completed_operations=(), ordinal=1
        )

        self.assertTrue(proposal.stop)
        self.assertEqual(gateway.calls, 2)
        self.assertTrue(
            gateway.contexts[1].execution_envelope_ref.endswith(
                ":contract-retry:2"
            )
        )

    def test_source_planner_cannot_stop_before_required_path_is_fully_read(self):
        request = self.request()
        request.required_source_paths = ("src/App.java",)
        stop = {
            "decision": "STOP",
            "tool": "NONE",
            "revision": "",
            "base": "",
            "path": "",
            "query": "",
            "cursor": "",
            "offset": "",
            "max_bytes": "",
            "page_size": "",
            "rationale": "The source is sufficient.",
        }
        gateway = FakeGateway(stop)

        proposal = ModelSourceInvestigationPlanner(
            gateway, self.configuration()
        ).propose(
            request=request,
            completed_operations=(
                self.completed_read(start=0, end=12, has_more=True),
            ),
            ordinal=2,
        )

        self.assertEqual(proposal.tool, SourceTool.READ)
        self.assertEqual(dict(proposal.parameters)["offset"], "12")
        self.assertEqual(dict(proposal.parameters)["max_bytes"], "4096")
        self.assertEqual(gateway.calls, 0)

    def test_source_planner_can_stop_after_required_path_is_fully_read(self):
        request = self.request()
        request.required_source_paths = ("src/App.java",)
        gateway = FakeGateway(
            {
                "decision": "STOP",
                "tool": "NONE",
                "revision": "",
                "base": "",
                "path": "",
                "query": "",
                "cursor": "",
                "offset": "",
                "max_bytes": "",
                "page_size": "",
                "rationale": "Every required target path is fully observed.",
            }
        )

        proposal = ModelSourceInvestigationPlanner(
            gateway, self.configuration()
        ).propose(
            request=request,
            completed_operations=(self.completed_read(),),
            ordinal=2,
        )

        self.assertTrue(proposal.stop)
        self.assertEqual(gateway.calls, 0)

    def test_source_planner_cannot_stop_before_comparison_base_is_fully_read(self):
        request = self.request()
        request.required_source_paths = ("src/App.java",)
        request.target = SimpleNamespace(
            target_kind=TargetKind.REVISION_COMPARISON,
            canonical_identity=(("base", "b" * 40), ("target", "a" * 40)),
            boundary="EXACT",
            digest=digest_of("comparison-target"),
        )
        stop = {
            "decision": "STOP",
            "tool": "NONE",
            "revision": "",
            "base": "",
            "path": "",
            "query": "",
            "cursor": "",
            "offset": "",
            "max_bytes": "",
            "page_size": "",
            "rationale": "The target source is sufficient.",
        }
        gateway = FakeGateway(stop)

        proposal = ModelSourceInvestigationPlanner(
            gateway, self.configuration()
        ).propose(
            request=request,
            completed_operations=(self.completed_read(),),
            ordinal=2,
        )

        self.assertEqual(proposal.tool, SourceTool.READ)
        self.assertEqual(dict(proposal.parameters)["revision"], "b" * 40)
        self.assertEqual(dict(proposal.parameters)["path"], "src/App.java")
        self.assertEqual(gateway.calls, 0)

    def test_source_planner_compares_after_required_comparison_paths_are_read(self):
        request = self.request()
        request.required_source_paths = ("src/App.java",)
        request.target = SimpleNamespace(
            target_kind=TargetKind.REVISION_COMPARISON,
            canonical_identity=(("base", "b" * 40), ("target", "a" * 40)),
            boundary="EXACT",
            digest=digest_of("comparison-target"),
        )
        gateway = FakeGateway({"unused": True})

        proposal = ModelSourceInvestigationPlanner(
            gateway, self.configuration()
        ).propose(
            request=request,
            completed_operations=(
                self.completed_read(revision="b" * 40),
                self.completed_read(revision="a" * 40),
            ),
            ordinal=3,
        )

        self.assertEqual(proposal.tool, SourceTool.COMPARE)
        self.assertEqual(
            dict(proposal.parameters),
            {"base": "b" * 40, "revision": "a" * 40},
        )
        self.assertEqual(gateway.calls, 0)

    def test_source_planner_retries_missing_required_tool_parameter(self):
        missing_query = {
            "decision": "EXECUTE",
            "tool": "SEARCH",
            "revision": "a" * 40,
            "base": "",
            "path": "src/App.java",
            "query": "",
            "cursor": "",
            "offset": "",
            "max_bytes": "4096",
            "page_size": "",
            "rationale": "Search for unavailable metadata.",
        }
        corrected = {
            **missing_query,
            "tool": "READ",
            "query": "",
            "rationale": "Read the relevant source path instead.",
        }
        gateway = SequencedGateway((missing_query, corrected))
        planner = ModelSourceInvestigationPlanner(gateway, self.configuration())

        proposal = planner.propose(
            request=self.request(), completed_operations=(), ordinal=1
        )

        self.assertEqual(proposal.tool, SourceTool.READ)
        self.assertEqual(gateway.calls, 2)
        repair = gateway.contexts[1].manifest.items[-1]
        self.assertEqual(repair.schema_ref, "source-proposal-contract-repair@1")
        repair_state = json.loads(repair.content)
        self.assertIn("query", repair_state["last_error"])

    def test_source_planner_repairs_a_read_path_outside_the_allowlist(self):
        outside = {
            "decision": "EXECUTE",
            "tool": "READ",
            "revision": "a" * 40,
            "base": "",
            "path": "module/src/App.java",
            "query": "",
            "cursor": "",
            "offset": "",
            "max_bytes": "4096",
            "page_size": "",
            "rationale": "Guess a conventional module prefix.",
        }
        corrected = {**outside, "path": "src/App.java"}
        gateway = SequencedGateway((outside, corrected))
        planner = ModelSourceInvestigationPlanner(gateway, self.configuration())

        proposal = planner.propose(
            request=self.request(), completed_operations=(), ordinal=1
        )

        self.assertEqual(dict(proposal.parameters)["path"], "src/App.java")
        self.assertEqual(gateway.calls, 2)
        state = json.loads(gateway.contexts[0].manifest.items[1].content)
        self.assertEqual(state["target"]["allowed_paths"], ["src/App.java"])

    def test_source_planner_rejects_repeating_observed_exact_coverage(self):
        repeated_search = {
            "decision": "EXECUTE",
            "tool": "SEARCH",
            "revision": "a" * 40,
            "base": "",
            "path": "",
            "query": "another synonym",
            "cursor": "",
            "offset": "",
            "max_bytes": "",
            "page_size": "",
            "rationale": "Try another search term.",
        }
        corrected_read = {
            **repeated_search,
            "tool": "READ",
            "path": "src/App.java",
            "query": "",
            "max_bytes": "4096",
            "rationale": "Read an exact path from the earlier repository listing.",
        }
        gateway = SequencedGateway((repeated_search, corrected_read))

        proposal = ModelSourceInvestigationPlanner(
            gateway, self.configuration()
        ).propose(
            request=self.request(),
            completed_operations=(
                self.completed_empty_search(1),
                self.completed_empty_search(2, query="another synonym"),
            ),
            ordinal=3,
        )

        self.assertEqual(proposal.tool, SourceTool.READ)
        self.assertEqual(gateway.calls, 2)
        state = json.loads(gateway.contexts[0].manifest.items[1].content)
        self.assertEqual(
            state["investigation_progress"]["trailing_actions_without_evidence"],
            2,
        )
        repair = json.loads(gateway.contexts[1].manifest.items[-1].content)
        self.assertEqual(
            repair["last_error_details"]["repeated_action"]["tool"],
            "SEARCH",
        )

    def test_fact_builder_requires_independent_acceptance_before_sealing(self):
        artifact = self.artifact()
        candidate = {
            "candidate_key": "app-value",
            "need_ids": ["need:initializer"],
            "artifact_id": artifact.artifact_id.value,
            "line_start": 2,
            "line_end": 2,
            "entity_type": "CODE_SYMBOL",
            "predicate": "HAS_VALUE",
            "statement": "App.value is initialized to 3; this source initializer is not a runtime invariant.",
            "condition": None,
            "limitation": None,
        }
        gateway = SequencedGateway(
            (
                {"candidates": [candidate], "limitations": []},
                {
                    "decision": "ACCEPT",
                    "accepted_candidate_keys": ["app-value"],
                    "all_supported_objective_aspects_covered": True,
                    "findings": [],
                },
                need_coverage_review(
                    artifact_id=artifact.artifact_id.value,
                    need_to_candidate_keys={
                        "need:initializer": ["app-value"]
                    },
                ),
            )
        )
        builder = ModelReviewedKnowledgeBuilder(gateway, self.configuration())
        request = self.request()
        request.requirement_plan = KnowledgeRequirementPlan(
            needs=(
                KnowledgeNeed(
                    need_id="need:initializer",
                    question="What source initializer is declared for App.value?",
                    required_kinds=(KnowledgeObjectKind.FACT,),
                    required_type_names=(),
                    required_terms=("App.value",),
                    minimum_support_count=1,
                ),
            ),
            joint_constraints=(),
        )

        bundle = builder.build(
            request=request, target=request.target, artifacts=(artifact,)
        )

        self.assertEqual(len(bundle.evidence), 1)
        self.assertEqual(len(bundle.entities), 1)
        self.assertEqual(len(bundle.facts), 1)
        self.assertIn("App.value is initialized to 3", bundle.facts[0].object_value)

        self.assertIn("runtime invariant", bundle.facts[0].object_value)
        excerpt = artifact.payload[
            bundle.evidence[0].byte_start : bundle.evidence[0].byte_end
        ].decode("utf-8")
        self.assertEqual(excerpt, "    int value = 3;\n")
        self.assertEqual(len(gateway.contexts), 4)
        self.assertNotEqual(
            gateway.contexts[0].manifest.manifest_id,
            gateway.contexts[1].manifest.manifest_id,
        )
        self.assertNotEqual(
            gateway.contexts[0].manifest.strategy_ref,
            gateway.contexts[1].manifest.strategy_ref,
        )
        proposal_state = json.loads(gateway.contexts[0].manifest.items[1].content)
        review_state = json.loads(gateway.contexts[1].manifest.items[1].content)
        need_state = json.loads(gateway.contexts[2].manifest.items[1].content)
        approval_audit_state = json.loads(
            gateway.contexts[3].manifest.items[1].content
        )
        self.assertEqual(
            proposal_state["reviewed_requirement_plan"],
            review_state["reviewed_requirement_plan"],
        )
        self.assertNotIn("artifacts", review_state)
        self.assertEqual(review_state["review_phase"]["kind"], "CANDIDATE_GROUNDING")
        self.assertEqual(proposal_state["artifacts"], need_state["artifacts"])
        self.assertIn("int value = 3", need_state["artifacts"][0]["numbered_content"])
        self.assertEqual(need_state["review_phase"]["kind"], "NEED_ANSWER_COVERAGE")
        self.assertEqual(
            need_state["review_phase"]["focused_needs"][0]["need_id"],
            "need:initializer",
        )
        self.assertEqual(len(need_state["review_phase"]["focused_needs"]), 1)
        self.assertEqual(
            approval_audit_state["review_phase"]["kind"],
            "GROUNDING_APPROVAL_AUDIT",
        )
        self.assertEqual(
            approval_audit_state["grounding_approval_audit"][
                "prior_decision"
            ],
            "ACCEPT",
        )
        self.assertIn(
            "Preserve the focused Need's discriminator exactly",
            gateway.contexts[2].manifest.items[0].content,
        )
        self.assertIn(
            "never add a separate unsupported intent gap",
            gateway.contexts[2].manifest.items[0].content,
        )
        self.assertIn(
            "argument lookup, computation, or transformation",
            gateway.contexts[2].manifest.items[0].content,
        )
        self.assertIn(
            "do not compress the source-visible lookup or resolution",
            gateway.contexts[2].manifest.items[0].content,
        )
        self.assertIn(
            "candidate_required_terms must include at least one exact",
            gateway.contexts[2].manifest.items[0].content,
        )
        self.assertIn(
            "SINGLE_ARTIFACT_SHARD supplies one complete artifact contribution",
            gateway.contexts[2].manifest.items[0].content,
        )
        self.assertIn(
            "Do not add unrelated public methods, output or persistence paths",
            gateway.contexts[2].manifest.items[0].content,
        )
        self.assertIn(
            "An exception requested at a named boundary does not make every nested",
            gateway.contexts[2].manifest.items[0].content,
        )
        self.assertIn(
            "candidate_required_terms may localize explanatory prose but cannot replace",
            gateway.contexts[2].manifest.items[0].content,
        )
        self.assertIn(
            "Explicitly connect the assignment to that later use",
            gateway.contexts[2].manifest.items[0].content,
        )
        self.assertIn(
            "same complete source statement",
            gateway.contexts[2].manifest.items[0].content,
        )
        self.assertIn(
            "single patch may contain no more than 8 replacements",
            gateway.contexts[0].manifest.items[0].content,
        )
        self.assertIn(
            "condition and limitation are compatibility fields and must always be JSON null",
            gateway.contexts[0].manifest.items[0].content,
        )
        self.assertIn(
            "Reject every non-null compatibility field",
            gateway.contexts[1].manifest.items[0].content,
        )
        self.assertIn(
            "deterministic sequential outcome",
            gateway.contexts[0].manifest.items[0].content,
        )
        self.assertIn(
            "deterministic sequential result",
            gateway.contexts[1].manifest.items[0].content,
        )
        self.assertIn(
            "smallest contiguous range containing the complete transition",
            gateway.contexts[2].manifest.items[0].content,
        )
        self.assertIn(
            "Do not use any fallback token",
            gateway.contexts[0].manifest.items[0].content,
        )
        self.assertIn(
            "Final scope scan before serialization",
            gateway.contexts[0].manifest.items[0].content,
        )
        self.assertIn(
            "Reject every nested-branch candidate that uses a fallback token",
            gateway.contexts[1].manifest.items[0].content,
        )
        self.assertIn(
            "Final nested-scope audit before returning",
            gateway.contexts[1].manifest.items[0].content,
        )
        self.assertIn(
            "repeated fallback token is never a valid candidate anchor",
            gateway.contexts[2].manifest.items[0].content,
        )
        self.assertNotIn("objective", need_state)
        self.assertEqual(
            proposal_state["reviewed_requirement_plan"],
            need_state["reviewed_requirement_plan"],
        )
        self.assertEqual(
            proposal_state["reviewed_requirement_plan"]["needs"][0]["need_id"],
            "need:initializer",
        )
        self.assertIn(
            "every material subject, relationship, condition, alternative",
            gateway.contexts[0].manifest.items[0].content,
        )
        self.assertIn(
            "Candidate array order, adjacent stage facts",
            gateway.contexts[0].manifest.items[0].content,
        )
        self.assertIn(
            "Merely naming the selected result, a later type check",
            gateway.contexts[0].manifest.items[0].content,
        )
        self.assertIn(
            "complete resulting boundary",
            gateway.contexts[0].manifest.items[0].content,
        )
        self.assertIn(
            "generic disclaimers",
            gateway.contexts[0].manifest.items[0].content,
        )
        self.assertIn(
            "Test both boundaries of every proposed range",
            gateway.contexts[0].manifest.items[0].content,
        )
        self.assertIn(
            "Audit range precision independently from semantic grounding",
            gateway.contexts[1].manifest.items[0].content,
        )
        self.assertIn(
            "Return exactly four top-level fields: decision",
            gateway.contexts[1].manifest.items[0].content,
        )
        self.assertIn(
            "Do not reject an otherwise directly supported candidate solely "
            "because one boundary is a blank line",
            gateway.contexts[1].manifest.items[0].content,
        )
        self.assertIn(
            "unrelated substantive source content",
            gateway.contexts[1].manifest.items[0].content,
        )
        self.assertIn(
            "material helper invocation",
            gateway.contexts[2].manifest.items[0].content,
        )
        self.assertIn(
            "exact source-native terms or literal fragments",
            gateway.contexts[2].manifest.items[0].content,
        )
        self.assertIn(
            "one contiguous, ordered source-token sequence",
            gateway.contexts[2].manifest.items[0].content,
        )
        self.assertIn(
            "three independently orderable propositions",
            gateway.contexts[0].manifest.items[0].content,
        )
        self.assertIn(
            "A combined caller item cannot cover both boundaries",
            gateway.contexts[2].manifest.items[0].content,
        )

    def test_grounding_approval_audit_rejection_triggers_fact_repair(self):
        artifact = self.artifact()
        ambiguous = {
            "candidate_key": "c1",
            "need_ids": ["N1"],
            "artifact_id": artifact.artifact_id.value,
            "line_start": 2,
            "line_end": 2,
            "entity_type": "CODE_SYMBOL",
            "predicate": "HAS_VALUE",
            "statement": (
                "App.value is initialized to 3; otherwise it remains unchanged."
            ),
            "condition": None,
            "limitation": None,
        }
        repaired = {
            **ambiguous,
            "statement": "App.value is initialized to 3.",
        }
        acceptance = {
            "decision": "ACCEPT",
            "accepted_candidate_keys": ["c1"],
            "all_supported_objective_aspects_covered": True,
            "findings": [],
        }
        audit_rejection = {
            "decision": "REJECT",
            "accepted_candidate_keys": [],
            "all_supported_objective_aspects_covered": False,
            "findings": [
                "c1 adds an unqualified fallback outcome not established by its excerpt."
            ],
        }
        coverage = need_coverage_review(
            artifact_id=artifact.artifact_id.value,
            need_to_candidate_keys={"N1": ["c1"]},
        )
        gateway = SequencedGateway(
            (
                {"candidates": [ambiguous], "limitations": []},
                acceptance,
                coverage,
                audit_rejection,
                {
                    "retained_candidate_keys": [],
                    "replacements": [repaired],
                    "limitations": [],
                },
                acceptance,
                coverage,
                acceptance,
            ),
            replay_audits=False,
        )
        request = self.request()
        request.requirement_plan = KnowledgeRequirementPlan(
            needs=(
                KnowledgeNeed(
                    need_id="N1",
                    question="What exact initializer value is declared?",
                    required_kinds=(KnowledgeObjectKind.FACT,),
                    required_type_names=(),
                    required_terms=("App.value",),
                    minimum_support_count=1,
                ),
            ),
        )

        bundle = ModelReviewedKnowledgeBuilder(
            gateway, self.configuration()
        ).build(request=request, target=request.target, artifacts=(artifact,))

        self.assertEqual(gateway.calls, 8)
        self.assertEqual(bundle.facts[0].object_value, repaired["statement"])
        first_audit_state = json.loads(
            gateway.contexts[3].manifest.items[1].content
        )
        self.assertEqual(
            first_audit_state["review_phase"]["kind"],
            "GROUNDING_APPROVAL_AUDIT",
        )
        self.assertIn(
            "omit every individually defective candidate key",
            first_audit_state["review_phase"]["required_action"],
        )
        self.assertIn(
            "Try to falsify every candidate's self-contained meaning",
            gateway.contexts[3].manifest.items[0].content,
        )
        repair_state = json.loads(
            gateway.contexts[4].manifest.items[1].content
        )
        self.assertEqual(
            repair_state["prior_review_findings"],
            audit_rejection["findings"],
        )
        self.assertIn(
            "2:     int value = 3;",
            repair_state["artifacts"][0]["numbered_content"],
        )
        self.assertEqual(
            bundle.facts[0].reviewed_grounding.reviewer_model_call_id,
            StableId("model_call_00000000000000000000000000000008"),
        )

    def test_grounding_review_cannot_reject_all_individually_accepted_candidates_for_coverage(self):
        artifact = self.artifact()
        candidate = {
            "candidate_key": "c1",
            "need_ids": ["N1"],
            "artifact_id": artifact.artifact_id.value,
            "line_start": 2,
            "line_end": 2,
            "entity_type": "CODE_SYMBOL",
            "predicate": "HAS_VALUE",
            "statement": "App.value is initialized to 3.",
            "condition": None,
            "limitation": None,
        }
        invalid_grounding_review = {
            "decision": "REJECT",
            "accepted_candidate_keys": ["c1"],
            "all_supported_objective_aspects_covered": False,
            "findings": ["Another objective aspect is not covered."],
        }
        grounding_acceptance = {
            "decision": "ACCEPT",
            "accepted_candidate_keys": ["c1"],
            "all_supported_objective_aspects_covered": True,
            "findings": [],
        }
        gateway = SequencedGateway(
            (
                {"candidates": [candidate], "limitations": []},
                invalid_grounding_review,
                grounding_acceptance,
                need_coverage_review(
                    artifact_id=artifact.artifact_id.value,
                    need_to_candidate_keys={"N1": ["c1"]},
                ),
            )
        )
        request = self.request()
        request.requirement_plan = KnowledgeRequirementPlan(
            needs=(
                KnowledgeNeed(
                    need_id="N1",
                    question="What initializer value does App.value declare?",
                    required_kinds=(KnowledgeObjectKind.FACT,),
                    required_type_names=(),
                    required_terms=("App.value",),
                    minimum_support_count=1,
                ),
            ),
            joint_constraints=(),
        )

        bundle = ModelReviewedKnowledgeBuilder(
            gateway, self.configuration()
        ).build(request=request, target=request.target, artifacts=(artifact,))

        self.assertEqual(len(bundle.facts), 1)
        self.assertEqual(gateway.calls, 5)
        self.assertTrue(
            gateway.contexts[2].execution_envelope_ref.endswith(
                ":contract-retry:2"
            )
        )
        retry_state = json.loads(gateway.contexts[2].manifest.items[1].content)
        self.assertEqual(
            retry_state["contract_repair"]["last_error"],
            "candidate grounding review mixes grounding with whole-objective coverage",
        )
        self.assertIn(
            "Do not judge missing objective coverage",
            retry_state["contract_repair"]["required_action"],
        )
        self.assertIn(
            "never omit decision",
            retry_state["contract_repair"]["required_action"],
        )
        self.assertIn(
            "audit only each submitted candidate in isolation",
            gateway.contexts[1].manifest.items[0].content,
        )
        self.assertIn(
            "Do not strengthen a question asking why",
            gateway.contexts[3].manifest.items[0].content,
        )

    def test_fact_set_with_joint_constraints_requires_acceptance_audit(self):
        artifact = self.artifact()
        candidate = {
            "candidate_key": "c1",
            "need_ids": ["N1"],
            "artifact_id": artifact.artifact_id.value,
            "line_start": 2,
            "line_end": 2,
            "entity_type": "CODE_SYMBOL",
            "predicate": "HAS_VALUE",
            "statement": "App.value is initialized to 3.",
            "condition": None,
            "limitation": None,
        }
        acceptance = {
            "decision": "ACCEPT",
            "accepted_candidate_keys": ["c1"],
            "all_supported_objective_aspects_covered": True,
            "findings": [],
        }
        gateway = SequencedGateway(
            (
                {"candidates": [candidate], "limitations": []},
                acceptance,
                need_coverage_review(
                    artifact_id=artifact.artifact_id.value,
                    need_to_candidate_keys={"N1": ["c1"]},
                ),
            )
        )
        request = self.request()
        request.requirement_plan = KnowledgeRequirementPlan(
            needs=(
                KnowledgeNeed(
                    need_id="N1",
                    question="What value participates in the requested relationship?",
                    required_kinds=(KnowledgeObjectKind.FACT,),
                    required_type_names=(),
                    required_terms=("App.value",),
                    minimum_support_count=1,
                ),
            ),
            joint_constraints=(
                JointConstraint(
                    constraint_id="C1",
                    need_ids=("N1",),
                    description="Preserve the requested relationship.",
                ),
            ),
        )

        bundle = ModelReviewedKnowledgeBuilder(
            gateway, self.configuration()
        ).build(
            request=request,
            target=request.target,
            artifacts=(artifact,),
        )

        self.assertEqual(len(bundle.facts), 1)
        self.assertEqual(gateway.calls, 4)
        audit_state = json.loads(gateway.contexts[2].manifest.items[1].content)
        self.assertEqual(
            audit_state["review_phase"]["kind"], "NEED_ANSWER_COVERAGE"
        )
        self.assertIn(
            "do not demand content assigned to any other Need",
            gateway.contexts[2].manifest.items[0].content,
        )
        self.assertIn(
            "without relying on language-, framework-, symbol-, or question-specific rules",
            gateway.contexts[1].manifest.items[0].content,
        )

    def test_need_focused_audit_repairs_a_weakened_answer(self):
        artifact = self.artifact()
        weak = {
            "candidate_key": "c1",
            "need_ids": ["N1"],
            "artifact_id": artifact.artifact_id.value,
            "line_start": 2,
            "line_end": 2,
            "entity_type": "CODE_SYMBOL",
            "predicate": "HAS_VALUE",
            "statement": "App.value has a declared initializer.",
            "condition": None,
            "limitation": None,
        }
        complete = {
            **weak,
            "statement": "App.value is initialized to 3.",
        }
        acceptance = {
            "decision": "ACCEPT",
            "accepted_candidate_keys": ["c1"],
            "all_supported_objective_aspects_covered": True,
            "findings": ["c1 is directly supported by its exact source line."],
        }
        focused_rejection = need_coverage_review(
            artifact_id=artifact.artifact_id.value,
            need_to_candidate_keys={"N1": []},
            decision="REJECT",
            findings=["The statement omits the requested initializer value 3."],
        )
        focused_acceptance = need_coverage_review(
            artifact_id=artifact.artifact_id.value,
            need_to_candidate_keys={"N1": ["c1"]},
        )
        gateway = SequencedGateway(
            (
                {"candidates": [weak], "limitations": []},
                acceptance,
                focused_rejection,
                {
                    "retained_candidate_keys": [],
                    "replacements": [complete],
                    "limitations": [],
                },
                acceptance,
                focused_acceptance,
            )
        )
        request = self.request()
        request.requirement_plan = KnowledgeRequirementPlan(
            needs=(
                KnowledgeNeed(
                    need_id="N1",
                    question="What exact initializer value is declared for App.value?",
                    required_kinds=(KnowledgeObjectKind.FACT,),
                    required_type_names=(),
                    required_terms=("App.value",),
                    minimum_support_count=1,
                ),
            ),
        )

        bundle = ModelReviewedKnowledgeBuilder(
            gateway, self.configuration()
        ).build(request=request, target=request.target, artifacts=(artifact,))

        self.assertEqual(len(bundle.facts), 1)
        self.assertEqual(bundle.facts[0].object_value, "App.value is initialized to 3.")
        self.assertEqual(gateway.calls, 7)
        repair_state = json.loads(gateway.contexts[3].manifest.items[1].content)
        self.assertEqual(
            repair_state["prior_review_findings"],
            [
                f"Coverage for Need N1 at {artifact.artifact_id.value}:2-2 "
                "states 'The declared initializer value is 3.', but no "
                "individually grounded candidate maps it.",
            ],
        )
        self.assertEqual(len(repair_state["artifacts"]), 1)
        repair_artifact = repair_state["artifacts"][0]
        self.assertEqual(
            repair_artifact["content_scope"],
            "EXACT_LINE_RANGES_FOR_PATCH_REPAIR",
        )
        self.assertEqual(
            repair_artifact["included_line_ranges"],
            [{"line_start": 2, "line_end": 2}],
        )
        self.assertEqual(repair_artifact["numbered_content"], "2:     int value = 3;")
        self.assertNotIn("public class App", repair_artifact["numbered_content"])
        self.assertTrue(
            gateway.contexts[3].execution_envelope_ref.endswith(
                ":coverage-repair:2"
            )
        )

    def test_complete_coverage_dispatches_independent_challenge_and_repairs_gap(self):
        artifact = self.artifact()
        weak_candidates = [
            {
                "candidate_key": f"c{index}",
                "need_ids": ["N1"],
                "artifact_id": artifact.artifact_id.value,
                "line_start": 2,
                "line_end": 2,
                "entity_type": "CODE_SYMBOL",
                "predicate": "DESCRIBED_AS",
                "statement": "App.value has a declared initializer.",
                "condition": None,
                "limitation": None,
            }
            for index in range(1, 9)
        ]
        complete = {
            **weak_candidates[0],
            "statement": "App.value is initialized to 3.",
        }
        weak_acceptance = {
            "decision": "ACCEPT",
            "accepted_candidate_keys": [
                item["candidate_key"] for item in weak_candidates
            ],
            "all_supported_objective_aspects_covered": True,
            "findings": [],
        }
        complete_acceptance = {
            "decision": "ACCEPT",
            "accepted_candidate_keys": [
                item["candidate_key"] for item in weak_candidates
            ],
            "all_supported_objective_aspects_covered": True,
            "findings": [],
        }
        initial_coverage = need_coverage_review(
            artifact_id=artifact.artifact_id.value,
            need_to_candidate_keys={"N1": ["c1"]},
        )
        challenge_gap = need_coverage_review(
            artifact_id=artifact.artifact_id.value,
            need_to_candidate_keys={"N1": []},
        )
        initial_coverage["coverage_items"][0]["required_terms"] = [
            "value",
            "3",
        ]
        challenge_gap["coverage_items"][0]["required_terms"] = [
            "value",
            "3",
        ]
        final_coverage = need_coverage_review(
            artifact_id=artifact.artifact_id.value,
            need_to_candidate_keys={"N1": ["c1"]},
        )
        gateway = SequencedGateway(
            (
                {"candidates": weak_candidates, "limitations": []},
                weak_acceptance,
                initial_coverage,
                challenge_gap,
                {
                    "retained_candidate_keys": [
                        item["candidate_key"] for item in weak_candidates
                    ],
                    "replacements": [complete],
                    "limitations": [],
                },
                {
                    "retained_candidate_keys": [
                        item["candidate_key"] for item in weak_candidates[1:]
                    ],
                    "replacements": [complete],
                    "limitations": [],
                },
                complete_acceptance,
                final_coverage,
                final_coverage,
                complete_acceptance,
            )
        )
        request = self.request()
        request.requirement_plan = KnowledgeRequirementPlan(
            needs=(
                KnowledgeNeed(
                    need_id="N1",
                    question="What exact initializer value is declared?",
                    required_kinds=(KnowledgeObjectKind.FACT,),
                    required_type_names=(),
                    required_terms=("initializer",),
                    minimum_support_count=1,
                ),
            ),
        )

        bundle = ModelReviewedKnowledgeBuilder(
            gateway, self.configuration()
        ).build(request=request, target=request.target, artifacts=(artifact,))

        self.assertEqual(gateway.calls, 10)
        self.assertEqual(len(bundle.facts), 8)
        self.assertTrue(
            any(
                context.execution_envelope_ref.endswith(
                    ":completeness-challenge"
                )
                for context in gateway.contexts
            )
        )
        challenge_context = next(
            context
            for context in gateway.contexts
            if context.execution_envelope_ref.endswith(
                ":completeness-challenge"
            )
        )
        self.assertIn(
            "Independently scan the complete supplied artifact",
            challenge_context.manifest.items[0].content,
        )
        self.assertIn(
            "A candidate that merely says the helper is called cannot cover",
            challenge_context.manifest.items[0].content,
        )

    def test_complete_coverage_fails_closed_when_challenge_outcome_is_unknown(self):
        artifact = self.artifact()
        candidates = [
            {
                "candidate_key": f"c{index}",
                "need_ids": ["N1"],
                "artifact_id": artifact.artifact_id.value,
                "line_start": 2,
                "line_end": 2,
                "entity_type": "CODE_SYMBOL",
                "predicate": "HAS_VALUE",
                "statement": "App.value is initialized to 3.",
                "condition": None,
                "limitation": None,
            }
            for index in range(1, 9)
        ]
        acceptance = {
            "decision": "ACCEPT",
            "accepted_candidate_keys": [
                item["candidate_key"] for item in candidates
            ],
            "all_supported_objective_aspects_covered": True,
            "findings": [],
        }
        gateway = SequencedGateway(
            (
                {"candidates": candidates, "limitations": []},
                acceptance,
                need_coverage_review(
                    artifact_id=artifact.artifact_id.value,
                    need_to_candidate_keys={"N1": ["c1"]},
                ),
                DomainError(
                    ErrorCode.CONTROL_STATE_DENIED,
                    "optional challenge transport outcome is unknown",
                ),
            )
        )
        request = self.request()
        request.requirement_plan = KnowledgeRequirementPlan(
            needs=(
                KnowledgeNeed(
                    need_id="N1",
                    question="What exact initializer value is declared?",
                    required_kinds=(KnowledgeObjectKind.FACT,),
                    required_type_names=(),
                    required_terms=("initializer",),
                    minimum_support_count=1,
                ),
            ),
        )

        with self.assertRaises(DomainError) as raised:
            ModelReviewedKnowledgeBuilder(
                gateway, self.configuration()
            ).build(
                request=request,
                target=request.target,
                artifacts=(artifact,),
            )

        self.assertEqual(gateway.calls, 4)
        self.assertEqual(raised.exception.code, ErrorCode.CONTROL_STATE_DENIED)
        self.assertTrue(
            gateway.contexts[-1].execution_envelope_ref.endswith(
                ":completeness-challenge"
            )
        )

    def test_mandatory_need_coverage_retries_unknown_stateless_outcome(self):
        artifact = self.artifact()
        candidate = {
            "candidate_key": "c1",
            "need_ids": ["N1"],
            "artifact_id": artifact.artifact_id.value,
            "line_start": 2,
            "line_end": 2,
            "entity_type": "CODE_SYMBOL",
            "predicate": "HAS_VALUE",
            "statement": "App.value is initialized to 3.",
            "condition": None,
            "limitation": None,
        }
        acceptance = {
            "decision": "ACCEPT",
            "accepted_candidate_keys": ["c1"],
            "all_supported_objective_aspects_covered": True,
            "findings": [],
        }
        gateway = SequencedGateway(
            (
                {"candidates": [candidate], "limitations": []},
                acceptance,
                DomainError(
                    ErrorCode.CONTROL_STATE_DENIED,
                    "Need coverage model result is not eligible for domain output",
                    {
                        "model_failure_code": "PROVIDER_OUTCOME_UNKNOWN",
                        "eligibility_reason": "MODEL_CALL_OUTCOME_UNKNOWN",
                    },
                ),
                need_coverage_review(
                    artifact_id=artifact.artifact_id.value,
                    need_to_candidate_keys={"N1": ["c1"]},
                ),
            )
        )
        request = self.request()
        request.requirement_plan = KnowledgeRequirementPlan(
            needs=(
                KnowledgeNeed(
                    need_id="N1",
                    question="What exact initializer value is declared?",
                    required_kinds=(KnowledgeObjectKind.FACT,),
                    required_type_names=(),
                    required_terms=("initializer",),
                    minimum_support_count=1,
                ),
            ),
        )

        bundle = ModelReviewedKnowledgeBuilder(
            gateway, self.configuration()
        ).build(request=request, target=request.target, artifacts=(artifact,))

        self.assertEqual(len(bundle.facts), 1)
        self.assertEqual(gateway.calls, 5)
        self.assertTrue(
            gateway.contexts[3].execution_envelope_ref.endswith(
                ":coverage-contract-retry:2"
            )
        )

    def test_fact_repair_reuses_unchanged_need_coverage_review(self):
        artifact = self.artifact()
        second_artifact = replace(
            artifact,
            artifact_id=StableId(
                "artifact_00000000000000000000000000000002"
            ),
            source_native_identity="src/SecondApp.java",
        )
        candidates = [
            {
                "candidate_key": f"c{index}",
                "need_ids": ["N1" if index <= 4 else "N2"],
                "artifact_id": artifact.artifact_id.value,
                "line_start": 2,
                "line_end": 2,
                "entity_type": "CODE_SYMBOL",
                "predicate": "HAS_VALUE",
                "statement": "App.value is initialized to 3.",
                "condition": None,
                "limitation": None,
            }
            for index in range(1, 9)
        ]
        repaired = {
            **candidates[4],
            "artifact_id": second_artifact.artifact_id.value,
            "statement": "App.value is initialized to 3.",
        }
        acceptance = {
            "decision": "ACCEPT",
            "accepted_candidate_keys": [
                item["candidate_key"] for item in candidates
            ],
            "all_supported_objective_aspects_covered": True,
            "findings": [],
        }
        n1_coverage = need_coverage_review(
            artifact_id=artifact.artifact_id.value,
            need_to_candidate_keys={"N1": ["c1"]},
        )
        n2_gap = need_coverage_review(
            artifact_id=second_artifact.artifact_id.value,
            need_to_candidate_keys={"N2": ["c5", "c6"]},
        )
        n2_coverage = need_coverage_review(
            artifact_id=second_artifact.artifact_id.value,
            need_to_candidate_keys={"N2": ["c5"]},
        )
        gateway = SequencedGateway(
            (
                {"candidates": candidates, "limitations": []},
                acceptance,
                n1_coverage,
                n2_gap,
                {
                    "retained_candidate_keys": [
                        item["candidate_key"]
                        for item in candidates
                        if item["candidate_key"] != "c5"
                    ],
                    "replacements": [repaired],
                    "limitations": [],
                },
                acceptance,
                n2_coverage,
            )
        )
        request = self.request()
        request.requirement_plan = KnowledgeRequirementPlan(
            needs=tuple(
                KnowledgeNeed(
                    need_id=need_id,
                    question="What exact initializer value is declared?",
                    required_kinds=(KnowledgeObjectKind.FACT,),
                    required_type_names=(),
                    required_terms=("initializer",),
                    minimum_support_count=1,
                )
                for need_id in ("N1", "N2")
            ),
        )

        bundle = ModelReviewedKnowledgeBuilder(
            gateway, self.configuration()
        ).build(
            request=request,
            target=request.target,
            artifacts=(artifact, second_artifact),
        )

        self.assertEqual(len(bundle.facts), 8)
        self.assertEqual(gateway.calls, 8)
        final_state = json.loads(gateway.contexts[6].manifest.items[1].content)
        self.assertEqual(
            [item["need_id"] for item in final_state["review_phase"]["focused_needs"]],
            ["N2"],
        )

    def test_fact_repair_reuses_coverage_when_an_unrelated_candidate_was_rejected(self):
        artifact = self.artifact()
        c1 = {
            "candidate_key": "c1",
            "need_ids": ["N1"],
            "artifact_id": artifact.artifact_id.value,
            "line_start": 2,
            "line_end": 2,
            "entity_type": "CODE_SYMBOL",
            "predicate": "HAS_VALUE",
            "statement": "App.value is initialized to 3.",
            "condition": None,
            "limitation": None,
        }
        c2 = {**c1, "candidate_key": "c2", "need_ids": ["N2"]}
        rejected = {
            **c1,
            "candidate_key": "c3",
            "need_ids": ["N2"],
            "statement": "App.value is always safe at runtime.",
        }
        grounding_rejection = {
            "decision": "REJECT",
            "accepted_candidate_keys": ["c1", "c2"],
            "all_supported_objective_aspects_covered": False,
            "findings": ["c3 overclaims runtime behavior."],
        }
        grounding_acceptance = {
            "decision": "ACCEPT",
            "accepted_candidate_keys": ["c1", "c2"],
            "all_supported_objective_aspects_covered": True,
            "findings": [],
        }
        n1_coverage = need_coverage_review(
            artifact_id=artifact.artifact_id.value,
            need_to_candidate_keys={"N1": ["c1"]},
        )
        n2_coverage = need_coverage_review(
            artifact_id=artifact.artifact_id.value,
            need_to_candidate_keys={"N2": ["c2"]},
        )
        gateway = SequencedGateway(
            (
                {"candidates": [c1, c2, rejected], "limitations": []},
                grounding_rejection,
                n1_coverage,
                {
                    "retained_candidate_keys": ["c1", "c2"],
                    "replacements": [],
                    "limitations": [],
                },
                grounding_acceptance,
                n2_coverage,
            )
        )
        request = self.request()
        request.requirement_plan = KnowledgeRequirementPlan(
            needs=tuple(
                KnowledgeNeed(
                    need_id=need_id,
                    question="What source initializer is declared?",
                    required_kinds=(KnowledgeObjectKind.FACT,),
                    required_type_names=(),
                    required_terms=("initializer",),
                    minimum_support_count=1,
                )
                for need_id in ("N1", "N2")
            ),
        )

        bundle = ModelReviewedKnowledgeBuilder(
            gateway, self.configuration()
        ).build(request=request, target=request.target, artifacts=(artifact,))

        self.assertEqual(gateway.calls, 7)
        self.assertEqual(len(bundle.facts), 2)
        self.assertEqual(
            [context.manifest.execution_stage for context in gateway.contexts],
            [
                "FACT_CANDIDATE_PROPOSAL",
                "FACT_CANDIDATE_REVIEW",
                "NEED_COVERAGE_REVIEW",
                "FACT_CANDIDATE_PROPOSAL",
                "FACT_CANDIDATE_REVIEW",
                "NEED_COVERAGE_REVIEW",
                "FACT_CANDIDATE_REVIEW",
            ],
        )

    def test_fact_repair_reuses_unchanged_artifact_coverage_shard(self):
        first_artifact = self.artifact()
        second_artifact = replace(
            first_artifact,
            artifact_id=StableId(
                "artifact_00000000000000000000000000000002"
            ),
            source_native_identity="src/SecondApp.java",
        )
        candidates = [
            {
                "candidate_key": f"c{index}",
                "need_ids": ["N1"],
                "artifact_id": (
                    first_artifact.artifact_id.value
                    if index <= 4
                    else second_artifact.artifact_id.value
                ),
                "line_start": 1 if index <= 4 else 2,
                "line_end": 1 if index <= 4 else 2,
                "entity_type": "CODE_SYMBOL",
                "predicate": "DECLARES",
                "statement": (
                    "public class App declares the class."
                    if index <= 4
                    else "App.value is initialized to 3."
                ),
                "condition": None,
                "limitation": None,
            }
            for index in range(1, 9)
        ]
        added = {
            **candidates[4],
            "candidate_key": "c9",
            "line_start": 1,
            "line_end": 1,
            "statement": "public class App declares the class.",
        }
        initial_acceptance = {
            "decision": "ACCEPT",
            "accepted_candidate_keys": [
                candidate["candidate_key"] for candidate in candidates
            ],
            "all_supported_objective_aspects_covered": True,
            "findings": [],
        }
        repaired_acceptance = {
            **initial_acceptance,
            "accepted_candidate_keys": [
                *initial_acceptance["accepted_candidate_keys"],
                "c9",
            ],
        }
        first_coverage = need_coverage_review(
            artifact_id=first_artifact.artifact_id.value,
            need_to_candidate_keys={"N1": ["c1"]},
        )
        first_coverage["coverage_items"][0]["line_start"] = 1
        first_coverage["coverage_items"][0]["line_end"] = 1
        first_coverage["coverage_items"][0]["required_terms"] = [
            "public class"
        ]
        first_coverage["coverage_items"][0][
            "candidate_required_terms"
        ] = ["public class"]
        second_gap = need_coverage_review(
            artifact_id=second_artifact.artifact_id.value,
            need_to_candidate_keys={"N1": []},
        )
        second_gap["coverage_items"][0]["line_start"] = 1
        second_gap["coverage_items"][0]["line_end"] = 1
        second_gap["coverage_items"][0]["required_terms"] = ["public class"]
        second_gap["coverage_items"][0]["candidate_required_terms"] = []
        second_coverage = need_coverage_review(
            artifact_id=second_artifact.artifact_id.value,
            need_to_candidate_keys={"N1": ["c9"]},
        )
        second_coverage["coverage_items"][0]["line_start"] = 1
        second_coverage["coverage_items"][0]["line_end"] = 1
        second_coverage["coverage_items"][0]["required_terms"] = [
            "public class"
        ]
        second_coverage["coverage_items"][0][
            "candidate_required_terms"
        ] = ["public class"]
        gateway = SequencedGateway(
            (
                {"candidates": candidates, "limitations": []},
                initial_acceptance,
                first_coverage,
                first_coverage,
                second_gap,
                {
                    "retained_candidate_keys": [
                        candidate["candidate_key"] for candidate in candidates
                    ],
                    "replacements": [added],
                    "limitations": [],
                },
                repaired_acceptance,
                second_coverage,
                second_coverage,
                repaired_acceptance,
            )
        )
        request = self.request()
        request.requirement_plan = KnowledgeRequirementPlan(
            needs=(
                KnowledgeNeed(
                    need_id="N1",
                    question="Which class declaration is present?",
                    required_kinds=(KnowledgeObjectKind.FACT,),
                    required_type_names=(),
                    required_terms=("class declaration",),
                    minimum_support_count=1,
                ),
            ),
        )

        bundle = ModelReviewedKnowledgeBuilder(
            gateway, self.configuration()
        ).build(
            request=request,
            target=request.target,
            artifacts=(first_artifact, second_artifact),
        )

        self.assertEqual(len(bundle.facts), 9)
        coverage_states = [
            json.loads(context.manifest.items[1].content)
            for context in gateway.contexts
            if context.manifest.execution_stage == "NEED_COVERAGE_REVIEW"
        ]
        self.assertEqual(
            [state["artifacts"][0]["artifact_id"] for state in coverage_states],
            [
                first_artifact.artifact_id.value,
                first_artifact.artifact_id.value,
                second_artifact.artifact_id.value,
                second_artifact.artifact_id.value,
                second_artifact.artifact_id.value,
            ],
        )

    def test_fact_repair_patch_retains_and_replaces_without_repeating_full_set(self):
        artifact = self.artifact()
        initial = [
            {
                "candidate_key": "c1",
                "need_ids": ["N1"],
                "artifact_id": artifact.artifact_id.value,
                "line_start": 2,
                "line_end": 2,
                "entity_type": "CODE_SYMBOL",
                "predicate": "DECLARES",
                "statement": "App.value has a declared initializer.",
                "condition": None,
                "limitation": None,
            },
            {
                "candidate_key": "c2",
                "need_ids": ["N1"],
                "artifact_id": artifact.artifact_id.value,
                "line_start": 2,
                "line_end": 2,
                "entity_type": "CODE_SYMBOL",
                "predicate": "HAS_VALUE",
                "statement": "App.value has a value.",
                "condition": None,
                "limitation": None,
            },
        ]
        prior = _candidate_views(
            {"candidates": initial, "limitations": []},
            (artifact,),
            allowed_need_ids=frozenset({"N1"}),
        )
        replacement = {
            **initial[1],
            "statement": "App.value is initialized to 3.",
        }

        merged = _candidate_patch_views(
            {
                "retained_candidate_keys": ["c1"],
                "replacements": [replacement],
                "limitations": [],
            },
            prior,
            (artifact,),
            allowed_need_ids=frozenset({"N1"}),
        )

        self.assertEqual([item["candidate_key"] for item in merged], ["c1", "c2"])
        self.assertEqual(merged[0]["statement"], initial[0]["statement"])
        self.assertEqual(merged[1]["statement"], replacement["statement"])

    def test_fact_repair_safety_fuse_does_not_truncate_complex_need_at_twenty_four(self):
        artifact = self.artifact()

        def candidate(key: str) -> dict[str, object]:
            return {
                "candidate_key": key,
                "need_ids": ["N1"],
                "artifact_id": artifact.artifact_id.value,
                "line_start": 2,
                "line_end": 2,
                "entity_type": "CODE_SYMBOL",
                "predicate": "HAS_VALUE",
                "statement": f"App.value has declared value 3 ({key}).",
                "condition": None,
                "limitation": None,
            }

        initial = [candidate(f"c{index}") for index in range(1, 9)]
        prior = _candidate_views(
            {"candidates": initial, "limitations": []},
            (artifact,),
            allowed_need_ids=frozenset({"N1"}),
        )
        expanded = _candidate_patch_views(
            {
                "retained_candidate_keys": [
                    item["candidate_key"] for item in initial
                ],
                "replacements": [
                    candidate(f"c{index}") for index in range(9, 13)
                ],
                "limitations": [],
            },
            prior,
            (artifact,),
            allowed_need_ids=frozenset({"N1"}),
        )

        merged = _candidate_patch_views(
            {
                "retained_candidate_keys": [
                    item["candidate_key"] for item in expanded
                ],
                "replacements": [
                    candidate("c13"),
                    candidate("c14"),
                    candidate("c15"),
                    candidate("c16"),
                ],
                "limitations": [],
            },
            expanded,
            (artifact,),
            allowed_need_ids=frozenset({"N1"}),
        )

        merged = _candidate_patch_views(
            {
                "retained_candidate_keys": [
                    item["candidate_key"] for item in merged
                ],
                "replacements": [
                    candidate(f"c{index}") for index in range(17, 25)
                ],
                "limitations": [],
            },
            merged,
            (artifact,),
            allowed_need_ids=frozenset({"N1"}),
        )

        merged = _candidate_patch_views(
            {
                "retained_candidate_keys": [
                    item["candidate_key"] for item in merged
                ],
                "replacements": [candidate("c25"), candidate("c26")],
                "limitations": [],
            },
            merged,
            (artifact,),
            allowed_need_ids=frozenset({"N1"}),
        )

        self.assertEqual(len(merged), 26)
        self.assertEqual(merged[-1]["candidate_key"], "c26")

    def test_fact_repair_automatically_retains_a_previously_grounded_candidate(self):
        artifact = self.artifact()
        initial = [
            {
                "candidate_key": f"c{index}",
                "need_ids": ["N1"],
                "artifact_id": artifact.artifact_id.value,
                "line_start": 2,
                "line_end": 2,
                "entity_type": "CODE_SYMBOL",
                "predicate": "HAS_VALUE",
                "statement": f"App.value has declared value 3 ({index}).",
                "condition": None,
                "limitation": None,
            }
            for index in (1, 2)
        ]
        prior = _candidate_views(
            {"candidates": initial, "limitations": []},
            (artifact,),
            allowed_need_ids=frozenset({"N1"}),
        )

        merged = _candidate_patch_views(
            {
                "retained_candidate_keys": [],
                "replacements": [
                    {
                        **initial[0],
                        "statement": "App.value has the declared value 3 (repaired).",
                    }
                ],
                "limitations": [],
            },
            prior,
            (artifact,),
            allowed_need_ids=frozenset({"N1"}),
            required_prior_candidate_keys=frozenset({"c1", "c2"}),
        )

        self.assertEqual(
            [item["candidate_key"] for item in merged],
            ["c1", "c2"],
        )

    def test_fact_repair_limits_replacements_per_bounded_pass(self):
        artifact = self.artifact()
        replacements = [
            {
                "candidate_key": f"c{index}",
                "need_ids": ["N1"],
                "artifact_id": artifact.artifact_id.value,
                "line_start": 2,
                "line_end": 2,
                "entity_type": "CODE_SYMBOL",
                "predicate": "HAS_VALUE",
                "statement": f"App.value has declared value 3 ({index}).",
                "condition": None,
                "limitation": None,
            }
            for index in range(1, 10)
        ]

        with self.assertRaises(DomainError) as captured:
            _candidate_patch_views(
                {
                    "retained_candidate_keys": [],
                    "replacements": replacements,
                    "limitations": [],
                },
                [],
                (artifact,),
                allowed_need_ids=frozenset({"N1"}),
            )

        self.assertEqual(
            captured.exception.details["replacement_count"], 9
        )
        self.assertEqual(
            captured.exception.details["replacement_limit"], 8
        )

    def test_fact_candidate_reports_unknown_need_ids_and_allowed_values(self):
        artifact = self.artifact()
        candidate = {
            "candidate_key": "c1",
            "need_ids": ["N1", "unknown-need"],
            "artifact_id": artifact.artifact_id.value,
            "line_start": 2,
            "line_end": 2,
            "entity_type": "CODE_SYMBOL",
            "predicate": "HAS_VALUE",
            "statement": "App.value is initialized to 3.",
            "condition": None,
            "limitation": None,
        }

        with self.assertRaises(DomainError) as raised:
            _candidate_views(
                {"candidates": [candidate], "limitations": []},
                (artifact,),
                allowed_need_ids=frozenset({"N1"}),
            )

        self.assertEqual(
            raised.exception.details["validation_violations"],
            ("UNKNOWN_NEED_IDS",),
        )
        self.assertEqual(
            raised.exception.details["unknown_need_ids"],
            ("unknown-need",),
        )
        self.assertEqual(
            raised.exception.details["allowed_need_ids"],
            ("N1",),
        )

    def test_fact_repair_preserves_each_candidates_originating_proposal_call(self):
        artifact = self.artifact()
        first = {
            "candidate_key": "c1",
            "need_ids": ["OBJECTIVE"],
            "artifact_id": artifact.artifact_id.value,
            "line_start": 2,
            "line_end": 2,
            "entity_type": "CODE_SYMBOL",
            "predicate": "DECLARES",
            "statement": "App.value has a declared initializer.",
            "condition": None,
            "limitation": None,
        }
        second = {
            **first,
            "candidate_key": "c2",
            "predicate": "HAS_VALUE",
            "statement": "App.value has a value.",
        }
        repaired_second = {
            **second,
            "statement": "App.value is initialized to 3.",
        }
        gateway = SequencedGateway(
            (
                {"candidates": [first, second], "limitations": []},
                {
                    "decision": "REJECT",
                    "accepted_candidate_keys": ["c1"],
                    "all_supported_objective_aspects_covered": False,
                    "findings": ["c2 omits the declared value."],
                },
                {
                    "retained_candidate_keys": ["c1"],
                    "replacements": [repaired_second],
                    "limitations": [],
                },
                {
                    "decision": "ACCEPT",
                    "accepted_candidate_keys": ["c1", "c2"],
                    "all_supported_objective_aspects_covered": True,
                    "findings": [],
                },
            )
        )

        bundle = ModelReviewedKnowledgeBuilder(
            gateway, self.configuration()
        ).build(
            request=self.request(),
            target=self.request().target,
            artifacts=(artifact,),
        )

        facts = {fact.reviewed_grounding.candidate_key: fact for fact in bundle.facts}
        self.assertEqual(
            facts["c1"].reviewed_grounding.proposer_model_call_id.value,
            "model_call_00000000000000000000000000000001",
        )
        self.assertEqual(
            facts["c2"].reviewed_grounding.proposer_model_call_id.value,
            "model_call_00000000000000000000000000000003",
        )
        self.assertTrue(
            all(
                fact.reviewed_grounding.reviewer_model_call_id.value
                == "model_call_00000000000000000000000000000004"
                for fact in facts.values()
            )
        )

    def test_need_coverage_summary_fields_are_optional_platform_outputs(self):
        artifact = self.artifact()
        candidate = {
            "candidate_key": "c1",
            "need_ids": ["N1"],
            "artifact_id": artifact.artifact_id.value,
            "line_start": 2,
            "line_end": 2,
            "entity_type": "CODE_SYMBOL",
            "predicate": "HAS_VALUE",
            "statement": "App.value is initialized to 3.",
            "condition": None,
            "limitation": None,
        }
        review = need_coverage_review(
            artifact_id=artifact.artifact_id.value,
            need_to_candidate_keys={"N1": ["c1"]},
        )
        review = {
            "coverage_items": [
                {
                    key: value
                    for key, value in review["coverage_items"][0].items()
                    if key != "source_supported"
                }
            ],
            "findings": [],
        }
        need = KnowledgeNeed(
            need_id="N1",
            question="What exact initializer value is declared?",
            required_kinds=(KnowledgeObjectKind.FACT,),
            required_type_names=(),
            required_terms=("initializer",),
            minimum_support_count=1,
        )

        complete, accepted, findings = _need_coverage_decision(
            review, [candidate], (need,), (artifact,)
        )

        self.assertTrue(complete)
        self.assertEqual(accepted, frozenset({"c1"}))
        self.assertEqual(findings, ())

    def test_need_coverage_normalizes_duplicate_checklist_set_values(self):
        artifact = self.artifact()
        candidate = {
            "candidate_key": "c1",
            "need_ids": ["N1"],
            "artifact_id": artifact.artifact_id.value,
            "line_start": 2,
            "line_end": 2,
            "entity_type": "CODE_SYMBOL",
            "predicate": "HAS_VALUE",
            "statement": "App.value is initialized to 3.",
            "condition": None,
            "limitation": None,
        }
        review = need_coverage_review(
            artifact_id=artifact.artifact_id.value,
            need_to_candidate_keys={"N1": ["c1"]},
        )
        review["coverage_items"][0]["required_terms"] = ["3", "3"]
        review["coverage_items"][0]["candidate_keys"] = ["c1", "c1"]
        need = KnowledgeNeed(
            need_id="N1",
            question="What exact initializer value is declared?",
            required_kinds=(KnowledgeObjectKind.FACT,),
            required_type_names=(),
            required_terms=("initializer",),
            minimum_support_count=1,
        )

        complete, accepted, findings = _need_coverage_decision(
            review, [candidate], (need,), (artifact,)
        )

        self.assertTrue(complete)
        self.assertEqual(accepted, frozenset({"c1"}))
        self.assertEqual(findings, ())

    def test_need_coverage_clears_candidate_anchors_without_a_mapping(self):
        artifact = self.artifact()
        candidate = {
            "candidate_key": "c1",
            "need_ids": ["N1"],
            "artifact_id": artifact.artifact_id.value,
            "line_start": 2,
            "line_end": 2,
            "entity_type": "CODE_SYMBOL",
            "predicate": "HAS_VALUE",
            "statement": "App.value is initialized to 3.",
            "condition": None,
            "limitation": None,
        }
        review = need_coverage_review(
            artifact_id=artifact.artifact_id.value,
            need_to_candidate_keys={"N1": ["c1"]},
        )
        review["coverage_items"].append(
            {
                "need_id": "N1",
                "source_supported": True,
                "artifact_id": artifact.artifact_id.value,
                "line_start": 1,
                "line_end": 1,
                "source_detail": "The source also declares the App class.",
                "required_terms": ["public class"],
                "candidate_required_terms": ["App class"],
                "candidate_keys": [],
            }
        )
        need = KnowledgeNeed(
            need_id="N1",
            question="What exact initializer value is declared?",
            required_kinds=(KnowledgeObjectKind.FACT,),
            required_type_names=(),
            required_terms=("initializer",),
            minimum_support_count=1,
        )

        complete, accepted, findings = _need_coverage_decision(
            review, [candidate], (need,), (artifact,)
        )

        self.assertFalse(complete)
        self.assertEqual(accepted, frozenset({"c1"}))
        self.assertTrue(any("no individually grounded candidate" in item for item in findings))

    def test_need_coverage_ignores_empty_zero_range_shard_note(self):
        artifact = self.artifact()
        candidate = {
            "candidate_key": "c1",
            "need_ids": ["N1"],
            "artifact_id": artifact.artifact_id.value,
            "line_start": 2,
            "line_end": 2,
            "entity_type": "CODE_SYMBOL",
            "predicate": "HAS_VALUE",
            "statement": "App.value is initialized to 3.",
            "condition": None,
            "limitation": None,
        }
        review = need_coverage_review(
            artifact_id=artifact.artifact_id.value,
            need_to_candidate_keys={"N1": ["c1"]},
        )
        review["coverage_items"].append(
            {
                "need_id": "N1",
                "artifact_id": artifact.artifact_id.value,
                "line_start": 0,
                "line_end": 0,
                "source_detail": "Other stages are not visible in this shard.",
                "required_terms": [],
                "candidate_required_terms": [],
                "candidate_keys": [],
            }
        )
        need = KnowledgeNeed(
            need_id="N1",
            question="What exact initializer value is declared?",
            required_kinds=(KnowledgeObjectKind.FACT,),
            required_type_names=(),
            required_terms=("initializer",),
            minimum_support_count=1,
        )

        complete, accepted, findings = _need_coverage_decision(
            review, [candidate], (need,), (artifact,)
        )

        self.assertTrue(complete)
        self.assertEqual(accepted, frozenset({"c1"}))
        self.assertEqual(findings, ())

    def test_need_coverage_names_a_grounded_candidate_with_a_missing_need_link(self):
        artifact = self.artifact()
        candidate = {
            "candidate_key": "c1",
            "need_ids": ["N1"],
            "artifact_id": artifact.artifact_id.value,
            "line_start": 2,
            "line_end": 2,
            "entity_type": "CODE_SYMBOL",
            "predicate": "HAS_VALUE",
            "statement": "App.value is initialized to 3.",
            "condition": None,
            "limitation": None,
        }
        review = need_coverage_review(
            artifact_id=artifact.artifact_id.value,
            need_to_candidate_keys={"N2": []},
        )
        need = KnowledgeNeed(
            need_id="N2",
            question="What exact initializer value is declared?",
            required_kinds=(KnowledgeObjectKind.FACT,),
            required_type_names=(),
            required_terms=("initializer",),
            minimum_support_count=1,
        )

        complete, accepted, findings = _need_coverage_decision(
            review, [candidate], (need,), (artifact,)
        )

        self.assertFalse(complete)
        self.assertEqual(accepted, frozenset())
        self.assertTrue(
            any("c1" in finding and "Need N2" in finding for finding in findings)
        )

    def test_need_coverage_cannot_mutate_a_missing_fact_need_link(self):
        artifact = self.artifact()
        candidate = {
            "candidate_key": "c1",
            "need_ids": ["N1"],
            "artifact_id": artifact.artifact_id.value,
            "line_start": 2,
            "line_end": 2,
            "entity_type": "CODE_SYMBOL",
            "predicate": "HAS_VALUE",
            "statement": "App.value is initialized to 3.",
            "condition": None,
            "limitation": None,
        }
        review = need_coverage_review(
            artifact_id=artifact.artifact_id.value,
            need_to_candidate_keys={"N2": ["c1"]},
        )
        need = KnowledgeNeed(
            need_id="N2",
            question="What exact initializer value is declared?",
            required_kinds=(KnowledgeObjectKind.FACT,),
            required_type_names=(),
            required_terms=("initializer",),
            minimum_support_count=1,
        )
        complete, accepted, findings = _need_coverage_decision(
            review,
            [candidate],
            (need,),
            (artifact,),
        )

        self.assertFalse(complete)
        self.assertEqual(accepted, frozenset())
        self.assertTrue(
            any(
                "c1" in finding
                and "Need N2" in finding
                and "independent grounding review" in finding
                for finding in findings
            )
        )

    def test_fact_builder_reproposes_a_missing_need_link_before_publication(self):
        artifact = self.artifact()
        candidate = {
            "candidate_key": "c1",
            "need_ids": ["N1"],
            "artifact_id": artifact.artifact_id.value,
            "line_start": 2,
            "line_end": 2,
            "entity_type": "CODE_SYMBOL",
            "predicate": "HAS_VALUE",
            "statement": "App.value is initialized to 3.",
            "condition": None,
            "limitation": None,
        }
        acceptance = {
            "decision": "ACCEPT",
            "accepted_candidate_keys": ["c1"],
            "all_supported_objective_aspects_covered": True,
            "findings": [],
        }
        linked_candidate = {**candidate, "need_ids": ["N1", "N2"]}
        coverage = need_coverage_review(
            artifact_id=artifact.artifact_id.value,
            need_to_candidate_keys={"N1": ["c1"], "N2": ["c1"]},
        )
        gateway = SequencedGateway(
            (
                {"candidates": [candidate], "limitations": []},
                acceptance,
                coverage,
                {
                    "retained_candidate_keys": [],
                    "replacements": [linked_candidate],
                    "limitations": [],
                },
                acceptance,
                coverage,
            )
        )
        request = self.request()
        request.requirement_plan = KnowledgeRequirementPlan(
            needs=tuple(
                KnowledgeNeed(
                    need_id=need_id,
                    question="What exact initializer value is declared?",
                    required_kinds=(KnowledgeObjectKind.FACT,),
                    required_type_names=(),
                    required_terms=("initializer",),
                    minimum_support_count=1,
                )
                for need_id in ("N1", "N2")
            ),
        )

        bundle = ModelReviewedKnowledgeBuilder(
            gateway, self.configuration()
        ).build(request=request, target=request.target, artifacts=(artifact,))

        self.assertEqual(gateway.calls, 7)
        self.assertEqual(
            bundle.facts[0].reviewed_grounding.need_ids,
            ("N1", "N2"),
        )
        grounding = bundle.facts[0].reviewed_grounding
        self.assertIsNotNone(grounding)
        self.assertEqual(
            grounding.proposer_model_call_id,
            StableId(f"model_call_{4:032x}"),
        )
        repair_state = json.loads(gateway.contexts[3].manifest.items[1].content)
        self.assertTrue(
            any(
                "independent grounding review" in finding
                for finding in repair_state["prior_review_findings"]
            )
        )

    def test_need_coverage_does_not_attach_a_link_when_fact_omits_source_anchor(self):
        artifact = self.artifact()
        candidate = {
            "candidate_key": "c1",
            "need_ids": ["N1"],
            "artifact_id": artifact.artifact_id.value,
            "line_start": 2,
            "line_end": 2,
            "entity_type": "CODE_SYMBOL",
            "predicate": "DESCRIBED_AS",
            "statement": "App.value has a declared initializer.",
            "condition": None,
            "limitation": None,
        }
        review = need_coverage_review(
            artifact_id=artifact.artifact_id.value,
            need_to_candidate_keys={"N2": ["c1"]},
        )
        need = KnowledgeNeed(
            need_id="N2",
            question="What exact initializer value is declared?",
            required_kinds=(KnowledgeObjectKind.FACT,),
            required_type_names=(),
            required_terms=("initializer",),
            minimum_support_count=1,
        )
        complete, accepted, findings = _need_coverage_decision(
            review,
            [candidate],
            (need,),
            (artifact,),
        )

        self.assertFalse(complete)
        self.assertEqual(accepted, frozenset())
        self.assertTrue(
            any("none of the required source anchors" in item for item in findings)
        )

    def test_need_coverage_normalizes_to_a_better_linked_mapping(self):
        artifact = self.artifact()
        correct = {
            "candidate_key": "c1",
            "need_ids": ["N1"],
            "artifact_id": artifact.artifact_id.value,
            "line_start": 2,
            "line_end": 2,
            "entity_type": "CODE_SYMBOL",
            "predicate": "HAS_VALUE",
            "statement": "App.value is initialized to 3.",
            "condition": None,
            "limitation": None,
        }
        wrong = {
            **correct,
            "candidate_key": "c2",
            "statement": "App.value has an initializer.",
        }
        review = need_coverage_review(
            artifact_id=artifact.artifact_id.value,
            need_to_candidate_keys={"N1": ["c2"]},
        )
        need = KnowledgeNeed(
            need_id="N1",
            question="What exact initializer value is declared?",
            required_kinds=(KnowledgeObjectKind.FACT,),
            required_type_names=(),
            required_terms=("initializer",),
            minimum_support_count=1,
        )

        complete, accepted, findings = _need_coverage_decision(
            review, [correct, wrong], (need,), (artifact,)
        )

        self.assertTrue(complete)
        self.assertEqual(accepted, frozenset({"c1"}))
        self.assertEqual(findings, ())

    def test_need_coverage_adds_an_omitted_exact_grounded_mapping(self):
        artifact = self.artifact()
        candidate = {
            "candidate_key": "c1",
            "need_ids": ["N1"],
            "artifact_id": artifact.artifact_id.value,
            "line_start": 2,
            "line_end": 2,
            "entity_type": "CODE_SYMBOL",
            "predicate": "HAS_VALUE",
            "statement": "App.value is initialized to 3.",
            "condition": None,
            "limitation": None,
        }
        review = need_coverage_review(
            artifact_id=artifact.artifact_id.value,
            need_to_candidate_keys={"N1": []},
        )
        need = KnowledgeNeed(
            need_id="N1",
            question="What exact initializer value is declared?",
            required_kinds=(KnowledgeObjectKind.FACT,),
            required_type_names=(),
            required_terms=("initializer",),
            minimum_support_count=1,
        )

        complete, accepted, findings = _need_coverage_decision(
            review, [candidate], (need,), (artifact,)
        )

        self.assertTrue(complete)
        self.assertEqual(accepted, frozenset({"c1"}))
        self.assertEqual(findings, ())

    def test_need_coverage_routes_an_absent_candidate_anchor_to_fact_repair(self):
        artifact = self.artifact()
        candidate = {
            "candidate_key": "c1",
            "need_ids": ["N1"],
            "artifact_id": artifact.artifact_id.value,
            "line_start": 2,
            "line_end": 2,
            "entity_type": "CODE_SYMBOL",
            "predicate": "HAS_VALUE",
            "statement": "App.value has a declared initializer.",
            "condition": None,
            "limitation": None,
        }
        review = need_coverage_review(
            artifact_id=artifact.artifact_id.value,
            need_to_candidate_keys={"N1": ["c1"]},
        )
        review["coverage_items"][0]["required_terms"] = ["value", "3"]
        review["coverage_items"][0]["candidate_required_terms"] = ["3"]
        need = KnowledgeNeed(
            need_id="N1",
            question="What exact initializer value is declared?",
            required_kinds=(KnowledgeObjectKind.FACT,),
            required_type_names=(),
            required_terms=("initializer",),
            minimum_support_count=1,
        )

        complete, accepted, findings = _need_coverage_decision(
            review, [candidate], (need,), (artifact,)
        )

        self.assertFalse(complete)
        self.assertEqual(accepted, frozenset())
        self.assertTrue(any("omits candidate anchors: 3" in item for item in findings))

    def test_candidate_native_anchor_does_not_discard_extra_source_syntax(self):
        artifact = self.artifact()
        candidate = {
            "candidate_key": "c1",
            "need_ids": ["N1"],
            "artifact_id": artifact.artifact_id.value,
            "line_start": 2,
            "line_end": 2,
            "entity_type": "CODE_SYMBOL",
            "predicate": "HAS_VALUE",
            "statement": "App.value is initialized to 3.",
            "condition": None,
            "limitation": None,
        }
        review = need_coverage_review(
            artifact_id=artifact.artifact_id.value,
            need_to_candidate_keys={"N1": ["c1"]},
        )
        review["coverage_items"][0]["required_terms"] = ["3"]
        review["coverage_items"][0]["candidate_required_terms"] = [
            "initialized to",
            "return runnable",
        ]
        need = KnowledgeNeed(
            need_id="N1",
            question="What exact initializer value is declared?",
            required_kinds=(KnowledgeObjectKind.FACT,),
            required_type_names=(),
            required_terms=("initializer",),
            minimum_support_count=1,
        )

        complete, accepted, findings = _need_coverage_decision(
            review, [candidate], (need,), (artifact,)
        )

        self.assertFalse(complete)
        self.assertEqual(accepted, frozenset())
        self.assertTrue(
            any("omits candidate anchors: return runnable" in item for item in findings)
        )

    def test_need_coverage_accepts_localized_text_with_qualified_operation(self):
        payload = (
            b"public class App {\n"
            b"    renderDataCompute.compute(tagName);\n"
            b"}\n"
        )
        artifact = replace(
            self.artifact(),
            payload=payload,
            content_digest=Digest(
                f"sha256:{hashlib.sha256(payload).hexdigest()}"
            ),
        )
        candidate = {
            "candidate_key": "c1",
            "need_ids": ["N1"],
            "artifact_id": artifact.artifact_id.value,
            "line_start": 2,
            "line_end": 2,
            "entity_type": "CODE_SYMBOL",
            "predicate": "HAS_VALUE",
            "statement": (
                "renderDataCompute.compute is called; the render data is "
                "calculated before delegation."
            ),
            "condition": None,
            "limitation": None,
        }
        review = need_coverage_review(
            artifact_id=artifact.artifact_id.value,
            need_to_candidate_keys={"N1": ["c1"]},
        )
        review["coverage_items"][0]["required_terms"] = [
            "renderDataCompute.compute",
        ]
        review["coverage_items"][0]["candidate_required_terms"] = [
            "render data is calculated",
        ]
        need = KnowledgeNeed(
            need_id="N1",
            question="How is render data computed before delegation?",
            required_kinds=(KnowledgeObjectKind.FACT,),
            required_type_names=(),
            required_terms=("render data",),
            minimum_support_count=1,
        )

        complete, accepted, findings = _need_coverage_decision(
            review, [candidate], (need,), (artifact,)
        )

        self.assertTrue(complete)
        self.assertEqual(accepted, frozenset({"c1"}))
        self.assertEqual(findings, ())

    def test_need_coverage_requires_qualified_source_operation_in_mapped_fact(self):
        payload = (
            b"public void visit(ElementTemplate eleTemplate) {\n"
            b"    RenderPolicy policy = eleTemplate.findPolicy(template.getConfig());\n"
            b"    DelegatePolicy.invoke(policy, "
            b"renderDataCompute.compute(eleTemplate.getTagName()));\n"
            b"}\n"
        )
        artifact = replace(
            self.artifact(),
            payload=payload,
            content_digest=Digest(
                f"sha256:{hashlib.sha256(payload).hexdigest()}"
            ),
        )
        candidate = {
            "candidate_key": "c1",
            "need_ids": ["N1"],
            "artifact_id": artifact.artifact_id.value,
            "line_start": 2,
            "line_end": 3,
            "entity_type": "CODE_SYMBOL",
            "predicate": "DELEGATES_TO",
            "statement": (
                "The visitor uses eleTemplate.findPolicy and then calls "
                "DelegatePolicy.invoke."
            ),
            "condition": None,
            "limitation": None,
        }
        review = need_coverage_review(
            artifact_id=artifact.artifact_id.value,
            need_to_candidate_keys={"N1": ["c1"]},
        )
        review["coverage_items"][0]["line_start"] = 2
        review["coverage_items"][0]["line_end"] = 3
        review["coverage_items"][0]["required_terms"] = [
            "DelegatePolicy",
            "invoke",
        ]
        review["coverage_items"][0]["candidate_required_terms"] = [
            "DelegatePolicy.invoke",
        ]
        need = KnowledgeNeed(
            need_id="N1",
            question="How does the visitor resolve and invoke the policy?",
            required_kinds=(KnowledgeObjectKind.FACT,),
            required_type_names=(),
            required_terms=("policy",),
            minimum_support_count=1,
        )

        complete, accepted, findings = _need_coverage_decision(
            review, [candidate], (need,), (artifact,)
        )

        self.assertTrue(complete)
        self.assertEqual(accepted, frozenset({"c1"}))
        self.assertEqual(findings, ())

        review["coverage_items"][0]["required_terms"] = [
            "DelegatePolicy",
            "invoke",
            "renderDataCompute.compute",
        ]
        review["coverage_items"][0]["source_detail"] = (
            "The visitor invokes DelegatePolicy after "
            "renderDataCompute.compute resolves the element data."
        )
        complete, accepted, findings = _need_coverage_decision(
            review, [candidate], (need,), (artifact,)
        )

        self.assertTrue(complete)
        self.assertEqual(accepted, frozenset({"c1"}))
        self.assertEqual(findings, ())

        challenge = json.loads(json.dumps(review))
        review["coverage_items"][0]["source_detail"] = (
            "The visitor invokes DelegatePolicy with computed render data."
        )
        challenge["coverage_items"][0]["source_detail"] = (
            "The visitor invokes DelegatePolicy with computed render data."
        )
        findings = _need_coverage_consensus_anchor_findings(
            review, challenge, [candidate]
        )

        self.assertTrue(
            any(
                "operation renderDataCompute.compute" in item
                and "omits that operation" in item
                for item in findings
            )
        )

        challenge["coverage_items"][0]["required_terms"] = [
            "DelegatePolicy",
            "invoke",
            "LOGGER.info",
        ]
        self.assertEqual(
            _need_coverage_consensus_anchor_findings(
                review, challenge, [candidate]
            ),
            (),
        )

    def test_short_construct_ignores_calls_in_independent_statements(self):
        payload = (
            b"public void invoke() {\n"
            b"    LOGGER.info(eleTemplate.getSign());\n"
            b"    policy.render(eleTemplate, model, template);\n"
            b"}\n"
        )
        artifact = replace(
            self.artifact(),
            payload=payload,
            content_digest=Digest(
                f"sha256:{hashlib.sha256(payload).hexdigest()}"
            ),
        )
        candidate = {
            "candidate_key": "c1",
            "need_ids": ["N1"],
            "artifact_id": artifact.artifact_id.value,
            "line_start": 2,
            "line_end": 3,
            "entity_type": "CODE_SYMBOL",
            "predicate": "CALLS",
            "statement": "The delegate calls policy.render with the model.",
            "condition": None,
            "limitation": None,
        }
        review = need_coverage_review(
            artifact_id=artifact.artifact_id.value,
            need_to_candidate_keys={"N1": ["c1"]},
        )
        review["coverage_items"][0]["line_start"] = 2
        review["coverage_items"][0]["line_end"] = 3
        review["coverage_items"][0]["required_terms"] = ["policy.render"]
        review["coverage_items"][0]["candidate_required_terms"] = [
            "policy.render",
        ]
        need = KnowledgeNeed(
            need_id="N1",
            question="How is the selected policy invoked?",
            required_kinds=(KnowledgeObjectKind.FACT,),
            required_type_names=(),
            required_terms=("policy",),
            minimum_support_count=1,
        )

        complete, accepted, findings = _need_coverage_decision(
            review, [candidate], (need,), (artifact,)
        )

        self.assertTrue(complete)
        self.assertEqual(accepted, frozenset({"c1"}))
        self.assertEqual(findings, ())

        review["coverage_items"][0]["required_terms"] = [
            "policy.render",
            "LOGGER.info",
        ]
        review["coverage_items"][0]["candidate_required_terms"] = [
            "policy.render",
            "LOGGER.info",
        ]
        complete, accepted, findings = _need_coverage_decision(
            review, [candidate], (need,), (artifact,)
        )
        self.assertFalse(complete)
        self.assertEqual(accepted, frozenset())

        complete, accepted, findings = _need_coverage_decision(
            review,
            [candidate],
            (need,),
            (artifact,),
            enforce_candidate_anchors=False,
        )
        self.assertTrue(complete)
        self.assertEqual(accepted, frozenset({"c1"}))
        self.assertEqual(findings, ())

    def test_need_coverage_accepts_contiguous_source_tokens_across_punctuation(self):
        payload = (
            b"public class Processor {\n"
            b"    public void visit(PictureTemplate pictureTemplate) {\n"
            b"    }\n"
            b"}\n"
        )
        artifact = replace(
            self.artifact(),
            payload=payload,
            content_digest=Digest(
                f"sha256:{hashlib.sha256(payload).hexdigest()}"
            ),
        )
        candidate = {
            "candidate_key": "c1",
            "need_ids": ["N1"],
            "artifact_id": artifact.artifact_id.value,
            "line_start": 2,
            "line_end": 2,
            "entity_type": "CODE_SYMBOL",
            "predicate": "DECLARES",
            "statement": "Processor declares visit(PictureTemplate).",
            "condition": None,
            "limitation": None,
        }
        review = need_coverage_review(
            artifact_id=artifact.artifact_id.value,
            need_to_candidate_keys={"N1": ["c1"]},
        )
        review["coverage_items"][0]["required_terms"] = [
            "visit(PictureTemplate)",
        ]
        review["coverage_items"][0]["candidate_required_terms"] = [
            "visit(PictureTemplate)",
        ]
        need = KnowledgeNeed(
            need_id="N1",
            question="Which visitor overload is declared?",
            required_kinds=(KnowledgeObjectKind.FACT,),
            required_type_names=(),
            required_terms=("visitor",),
            minimum_support_count=1,
        )

        complete, accepted, findings = _need_coverage_decision(
            review, [candidate], (need,), (artifact,)
        )

        self.assertTrue(complete)
        self.assertEqual(accepted, frozenset({"c1"}))
        self.assertEqual(findings, ())

    def test_candidate_anchor_accepts_qualified_receiver_when_operation_remains(self):
        payload = (
            b"public void invoke() {\n"
            b"    preRenderDataCastor.preCast(policy, model);\n"
            b"}\n"
        )
        artifact = replace(
            self.artifact(),
            payload=payload,
            content_digest=Digest(
                f"sha256:{hashlib.sha256(payload).hexdigest()}"
            ),
        )
        candidate = {
            "candidate_key": "c1",
            "need_ids": ["N1"],
            "artifact_id": artifact.artifact_id.value,
            "line_start": 2,
            "line_end": 2,
            "entity_type": "CODE_SYMBOL",
            "predicate": "CALLS",
            "statement": "The delegate invokes preCast for the policy and model.",
            "condition": None,
            "limitation": None,
        }
        review = need_coverage_review(
            artifact_id=artifact.artifact_id.value,
            need_to_candidate_keys={"N1": ["c1"]},
        )
        review["coverage_items"][0]["required_terms"] = [
            "preRenderDataCastor.preCast"
        ]
        review["coverage_items"][0]["candidate_required_terms"] = [
            "preRenderDataCastor.preCast"
        ]
        need = KnowledgeNeed(
            need_id="N1",
            question="How is the pre-render conversion invoked?",
            required_kinds=(KnowledgeObjectKind.FACT,),
            required_type_names=(),
            required_terms=("pre-render conversion",),
            minimum_support_count=1,
        )

        complete, accepted, findings = _need_coverage_decision(
            review, [candidate], (need,), (artifact,)
        )

        self.assertTrue(complete)
        self.assertEqual(accepted, frozenset({"c1"}))
        self.assertEqual(findings, ())

    def test_need_coverage_ignores_free_text_without_a_checklist_gap(self):
        artifact = self.artifact()
        candidate = {
            "candidate_key": "c1",
            "need_ids": ["N1"],
            "artifact_id": artifact.artifact_id.value,
            "line_start": 2,
            "line_end": 2,
            "entity_type": "CODE_SYMBOL",
            "predicate": "HAS_VALUE",
            "statement": "App.value is initialized to 3.",
            "condition": None,
            "limitation": None,
        }
        review = need_coverage_review(
            artifact_id=artifact.artifact_id.value,
            need_to_candidate_keys={"N1": ["c1"]},
            findings=["An unrelated candidate is not present in the checklist."],
        )
        need = KnowledgeNeed(
            need_id="N1",
            question="What exact initializer value is declared?",
            required_kinds=(KnowledgeObjectKind.FACT,),
            required_type_names=(),
            required_terms=("initializer",),
            minimum_support_count=1,
        )

        complete, accepted, findings = _need_coverage_decision(
            review, [candidate], (need,), (artifact,)
        )

        self.assertTrue(complete)
        self.assertEqual(accepted, frozenset({"c1"}))
        self.assertEqual(findings, ())

    def test_need_coverage_retries_a_source_anchor_outside_its_range(self):
        artifact = self.artifact()
        candidate = {
            "candidate_key": "c1",
            "need_ids": ["N1"],
            "artifact_id": artifact.artifact_id.value,
            "line_start": 2,
            "line_end": 2,
            "entity_type": "CODE_SYMBOL",
            "predicate": "HAS_VALUE",
            "statement": "App.value is initialized to 3.",
            "condition": None,
            "limitation": None,
        }
        review = need_coverage_review(
            artifact_id=artifact.artifact_id.value,
            need_to_candidate_keys={"N1": ["c1"]},
        )
        review["coverage_items"][0]["required_terms"] = ["public class"]
        review["coverage_items"][0]["candidate_required_terms"] = []
        need = KnowledgeNeed(
            need_id="N1",
            question="What exact declaration is involved?",
            required_kinds=(KnowledgeObjectKind.FACT,),
            required_type_names=(),
            required_terms=("declaration",),
            minimum_support_count=1,
        )

        with self.assertRaises(DomainError) as raised:
            _need_coverage_decision(review, [candidate], (need,), (artifact,))

        self.assertEqual(raised.exception.code, ErrorCode.STRUCTURED_OUTPUT_INVALID)
        self.assertIn("outside the cited range", raised.exception.message)
        self.assertEqual(
            raised.exception.details["term_locations"]["public class"],
            ((artifact.artifact_id.value, 1),),
        )

    def test_need_coverage_recovers_adjacent_anchor_inside_mapped_evidence(self):
        artifact = self.artifact()
        candidate = {
            "candidate_key": "c1",
            "need_ids": ["N1"],
            "artifact_id": artifact.artifact_id.value,
            "line_start": 1,
            "line_end": 2,
            "entity_type": "CODE_SYMBOL",
            "predicate": "HAS_VALUE",
            "statement": "App declares value 3.",
            "condition": None,
            "limitation": None,
        }
        review = need_coverage_review(
            artifact_id=artifact.artifact_id.value,
            need_to_candidate_keys={"N1": ["c1"]},
        )
        review["coverage_items"][0]["line_start"] = 2
        review["coverage_items"][0]["line_end"] = 2
        review["coverage_items"][0]["required_terms"] = ["public class", "3"]
        review["coverage_items"][0]["candidate_required_terms"] = ["value 3"]
        need = KnowledgeNeed(
            need_id="N1",
            question="Which class declares the value?",
            required_kinds=(KnowledgeObjectKind.FACT,),
            required_type_names=(),
            required_terms=("declaration",),
            minimum_support_count=1,
        )

        complete, accepted, findings = _need_coverage_decision(
            review, [candidate], (need,), (artifact,)
        )

        self.assertTrue(complete)
        self.assertEqual(accepted, frozenset({"c1"}))
        self.assertEqual(findings, ())

    def test_need_coverage_retries_a_mapping_outside_the_cited_range(self):
        artifact = self.artifact()
        correct = {
            "candidate_key": "c1",
            "need_ids": ["N1"],
            "artifact_id": artifact.artifact_id.value,
            "line_start": 2,
            "line_end": 2,
            "entity_type": "CODE_SYMBOL",
            "predicate": "HAS_VALUE",
            "statement": "App.value is initialized to 3.",
            "condition": None,
            "limitation": None,
        }
        outside = {
            **correct,
            "candidate_key": "c2",
            "line_start": 1,
            "line_end": 1,
            "statement": "App is a public class.",
        }
        review = need_coverage_review(
            artifact_id=artifact.artifact_id.value,
            need_to_candidate_keys={"N1": ["c2"]},
        )
        need = KnowledgeNeed(
            need_id="N1",
            question="What exact initializer value is declared?",
            required_kinds=(KnowledgeObjectKind.FACT,),
            required_type_names=(),
            required_terms=("initializer",),
            minimum_support_count=1,
        )

        with self.assertRaises(DomainError) as raised:
            _need_coverage_decision(
                review, [correct, outside], (need,), (artifact,)
            )

        self.assertEqual(
            raised.exception.details["invalid_candidate_keys"], ("c2",)
        )
        self.assertEqual(
            raised.exception.details["suggested_candidate_keys"], ("c1",)
        )

    def test_need_coverage_turns_an_unreplaceable_range_mapping_into_a_fact_gap(self):
        artifact = self.artifact()
        outside = {
            "candidate_key": "c1",
            "need_ids": ["N1"],
            "artifact_id": artifact.artifact_id.value,
            "line_start": 1,
            "line_end": 1,
            "entity_type": "CODE_SYMBOL",
            "predicate": "HAS_VALUE",
            "statement": "App is a public class.",
            "condition": None,
            "limitation": None,
        }
        review = need_coverage_review(
            artifact_id=artifact.artifact_id.value,
            need_to_candidate_keys={"N1": ["c1"]},
        )
        need = KnowledgeNeed(
            need_id="N1",
            question="What exact initializer value is declared?",
            required_kinds=(KnowledgeObjectKind.FACT,),
            required_type_names=(),
            required_terms=("initializer",),
            minimum_support_count=1,
        )

        complete, accepted, findings = _need_coverage_decision(
            review, [outside], (need,), (artifact,)
        )

        self.assertFalse(complete)
        self.assertEqual(accepted, frozenset())
        self.assertTrue(any("non-overlapping evidence" in item for item in findings))
        self.assertTrue(any("no individually grounded candidate" in item for item in findings))

    def test_need_coverage_recovers_a_wrong_checklist_artifact_from_candidate_evidence(self):
        candidate_artifact = self.artifact()
        review_artifact = replace(
            candidate_artifact,
            artifact_id=StableId(
                "artifact_00000000000000000000000000000002"
            ),
            source_native_identity="src/Other.java",
            payload=b"class Other {}\n",
            content_digest=Digest(
                "sha256:"
                + hashlib.sha256(b"class Other {}\n").hexdigest()
            ),
            identity_digest=digest_of("other-artifact-identity"),
        )
        candidate = {
            "candidate_key": "c1",
            "need_ids": ["N1"],
            "artifact_id": candidate_artifact.artifact_id.value,
            "line_start": 2,
            "line_end": 2,
            "entity_type": "CODE_SYMBOL",
            "predicate": "HAS_VALUE",
            "statement": "App.value is initialized to 3.",
            "condition": None,
            "limitation": None,
        }
        review = need_coverage_review(
            artifact_id=review_artifact.artifact_id.value,
            need_to_candidate_keys={"N1": ["c1"]},
        )
        need = KnowledgeNeed(
            need_id="N1",
            question="What exact initializer value is declared?",
            required_kinds=(KnowledgeObjectKind.FACT,),
            required_type_names=(),
            required_terms=("initializer",),
            minimum_support_count=1,
        )

        complete, accepted, findings = _need_coverage_decision(
            review,
            [candidate],
            (need,),
            (candidate_artifact, review_artifact),
        )

        self.assertTrue(complete)
        self.assertEqual(accepted, frozenset({"c1"}))
        self.assertEqual(findings, ())

    def test_need_coverage_recovers_an_unknown_artifact_typo_from_candidate_evidence(self):
        artifact = self.artifact()
        candidate = {
            "candidate_key": "c1",
            "need_ids": ["N1"],
            "artifact_id": artifact.artifact_id.value,
            "line_start": 2,
            "line_end": 2,
            "entity_type": "CODE_SYMBOL",
            "predicate": "HAS_VALUE",
            "statement": "App.value is initialized to 3.",
            "condition": None,
            "limitation": None,
        }
        review = need_coverage_review(
            artifact_id="artifact_ffffffffffffffffffffffffffffffff",
            need_to_candidate_keys={"N1": ["c1"]},
        )
        need = KnowledgeNeed(
            need_id="N1",
            question="What exact initializer value is declared?",
            required_kinds=(KnowledgeObjectKind.FACT,),
            required_type_names=(),
            required_terms=("initializer",),
            minimum_support_count=1,
        )

        complete, accepted, findings = _need_coverage_decision(
            review, [candidate], (need,), (artifact,)
        )

        self.assertTrue(complete)
        self.assertEqual(accepted, frozenset({"c1"}))
        self.assertEqual(findings, ())

    def test_need_coverage_accepts_the_same_key_union_in_any_order(self):
        artifact = self.artifact()
        candidates = [
            {
                "candidate_key": key,
                "need_ids": [need_id],
                "artifact_id": artifact.artifact_id.value,
                "line_start": 2,
                "line_end": 2,
                "entity_type": "CODE_SYMBOL",
                "predicate": "HAS_VALUE",
                "statement": "App.value is initialized to 3.",
                "condition": None,
                "limitation": None,
            }
            for key, need_id in (("c1", "N1"), ("c2", "N2"))
        ]
        review = need_coverage_review(
            artifact_id=artifact.artifact_id.value,
            need_to_candidate_keys={"N1": ["c1"], "N2": ["c2"]},
        )
        review["accepted_candidate_keys"] = ["c2", "c1"]
        needs = tuple(
            KnowledgeNeed(
                need_id=need_id,
                question="What exact initializer value is declared?",
                required_kinds=(KnowledgeObjectKind.FACT,),
                required_type_names=(),
                required_terms=("initializer",),
                minimum_support_count=1,
            )
            for need_id in ("N1", "N2")
        )

        complete, accepted, findings = _need_coverage_decision(
            review, candidates, needs, (artifact,)
        )

        self.assertTrue(complete)
        self.assertEqual(accepted, frozenset({"c1", "c2"}))
        self.assertEqual(findings, ())

    def test_rejected_need_coverage_can_preserve_diagnostic_source_location(self):
        artifact = self.artifact()
        need = KnowledgeNeed(
            need_id="N1",
            question="What exact initializer value is declared?",
            required_kinds=(KnowledgeObjectKind.FACT,),
            required_type_names=(),
            required_terms=("initializer",),
            minimum_support_count=1,
        )
        review = {
            "decision": "REJECT",
            "accepted_candidate_keys": [],
            "all_supported_objective_aspects_covered": False,
            "coverage_items": [
                {
                    "need_id": "N1",
                    "source_supported": False,
                    "artifact_id": artifact.artifact_id.value,
                    "line_start": 2,
                    "line_end": 2,
                    "source_detail": (
                        "The source declares the value, but no candidate maps it."
                    ),
                    "required_terms": [],
                    "candidate_required_terms": [],
                    "candidate_keys": [],
                }
            ],
            "findings": ["No candidate covers the declared initializer value."],
        }

        complete, accepted, findings = _need_coverage_decision(
            review, [], (need,), (artifact,)
        )

        self.assertFalse(complete)
        self.assertEqual(accepted, frozenset())
        self.assertIn("without an accepted mapped candidate", findings[0])

    def test_need_coverage_contract_retry_does_not_repeat_grounding_review(self):
        artifact = self.artifact()
        candidate = {
            "candidate_key": "c1",
            "need_ids": ["N1"],
            "artifact_id": artifact.artifact_id.value,
            "line_start": 2,
            "line_end": 2,
            "entity_type": "CODE_SYMBOL",
            "predicate": "HAS_VALUE",
            "statement": "App.value is initialized to 3.",
            "condition": None,
            "limitation": None,
        }
        grounding_acceptance = {
            "decision": "ACCEPT",
            "accepted_candidate_keys": ["c1"],
            "all_supported_objective_aspects_covered": True,
            "findings": [],
        }
        invalid_coverage = need_coverage_review(
            artifact_id=artifact.artifact_id.value,
            need_to_candidate_keys={"N1": ["c1"]},
        )
        invalid_coverage["coverage_items"][0]["required_terms"] = [
            "term absent from source"
        ]
        invalid_coverage["coverage_items"][0]["candidate_required_terms"] = []
        valid_coverage = need_coverage_review(
            artifact_id=artifact.artifact_id.value,
            need_to_candidate_keys={"N1": ["c1"]},
        )
        gateway = SequencedGateway(
            (
                {"candidates": [candidate], "limitations": []},
                grounding_acceptance,
                invalid_coverage,
                valid_coverage,
            )
        )
        request = self.request()
        request.requirement_plan = KnowledgeRequirementPlan(
            needs=(
                KnowledgeNeed(
                    need_id="N1",
                    question="What exact initializer value is declared?",
                    required_kinds=(KnowledgeObjectKind.FACT,),
                    required_type_names=(),
                    required_terms=("initializer",),
                    minimum_support_count=1,
                ),
            ),
        )

        bundle = ModelReviewedKnowledgeBuilder(
            gateway, self.configuration()
        ).build(request=request, target=request.target, artifacts=(artifact,))

        self.assertEqual(len(bundle.facts), 1)
        self.assertEqual(gateway.calls, 5)
        self.assertEqual(
            [context.manifest.execution_stage for context in gateway.contexts],
            [
                "FACT_CANDIDATE_PROPOSAL",
                "FACT_CANDIDATE_REVIEW",
                "NEED_COVERAGE_REVIEW",
                "NEED_COVERAGE_REVIEW",
                "FACT_CANDIDATE_REVIEW",
            ],
        )
        retry_state = json.loads(gateway.contexts[3].manifest.items[1].content)
        self.assertEqual(
            retry_state["contract_repair"]["invalid_review"],
            invalid_coverage,
        )
        self.assertEqual(
            retry_state["contract_repair"]["last_error_details"],
            {
                "need_id": "N1",
                "artifact_id": artifact.artifact_id.value,
                "line_start": 2,
                "line_end": 2,
                "missing_terms": ["term absent from source"],
            },
        )
        self.assertTrue(
            gateway.contexts[3].execution_envelope_ref.endswith(
                ":coverage-contract-retry:2"
            )
        )

    def test_need_coverage_audit_batches_at_most_three_needs(self):
        artifact = self.artifact()
        keyed_needs = tuple(
            (f"c{index}", f"N{index}") for index in range(1, 6)
        )
        candidates = [
            {
                "candidate_key": key,
                "need_ids": [need_id],
                "artifact_id": artifact.artifact_id.value,
                "line_start": 2,
                "line_end": 2,
                "entity_type": "CODE_SYMBOL",
                "predicate": "HAS_VALUE",
                "statement": "App.value is initialized to 3.",
                "condition": None,
                "limitation": None,
            }
            for key, need_id in keyed_needs
        ]
        candidates[0]["need_ids"] = ["N1", "N5"]
        grounding_acceptance = {
            "decision": "ACCEPT",
            "accepted_candidate_keys": [key for key, _ in keyed_needs],
            "all_supported_objective_aspects_covered": True,
            "findings": [],
        }
        gateway = SequencedGateway(
            (
                {"candidates": candidates, "limitations": []},
                grounding_acceptance,
                need_coverage_review(
                    artifact_id=artifact.artifact_id.value,
                    need_to_candidate_keys={
                        need_id: [key]
                        for key, need_id in keyed_needs[:3]
                    },
                ),
                need_coverage_review(
                    artifact_id=artifact.artifact_id.value,
                    need_to_candidate_keys={
                        "N4": ["c4"],
                        "N5": ["c1", "c5"],
                    },
                ),
            )
        )
        request = self.request()
        request.requirement_plan = KnowledgeRequirementPlan(
            needs=tuple(
                KnowledgeNeed(
                    need_id=need_id,
                    question=question,
                    required_kinds=(KnowledgeObjectKind.FACT,),
                    required_type_names=(),
                    required_terms=("App.value",),
                    minimum_support_count=1,
                )
                for need_id, question in tuple(
                    (
                        need_id,
                        f"What initializer detail {index} is declared?",
                    )
                    for index, (_, need_id) in enumerate(keyed_needs, 1)
                )
            )
        )

        bundle = ModelReviewedKnowledgeBuilder(
            gateway, self.configuration()
        ).build(request=request, target=request.target, artifacts=(artifact,))

        self.assertEqual(len(bundle.facts), 5)
        self.assertEqual(gateway.calls, 5)
        states = [
            json.loads(context.manifest.items[1].content)
            for context in gateway.contexts[2:]
            if json.loads(context.manifest.items[1].content)
            .get("review_phase", {})
            .get("kind")
            == "NEED_ANSWER_COVERAGE"
        ]
        self.assertEqual(
            [
                [
                    item["need_id"]
                    for item in state["review_phase"]["focused_needs"]
                ]
                for state in states
            ],
            [["N1", "N2", "N3"], ["N4", "N5"]],
        )
        self.assertEqual([len(state["candidates"]) for state in states], [5, 5])
        self.assertEqual(
            [
                [candidate["need_ids"] for candidate in state["candidates"]]
                for state in states
            ],
            [
                [["N1", "N5"], ["N2"], ["N3"], ["N4"], ["N5"]],
                [["N1", "N5"], ["N2"], ["N3"], ["N4"], ["N5"]],
            ],
        )

    def test_truncated_multi_need_coverage_is_retried_as_smaller_batches(self):
        artifact = self.artifact()
        candidates = [
            {
                "candidate_key": f"c{index}",
                "need_ids": [f"N{index}"],
                "artifact_id": artifact.artifact_id.value,
                "line_start": 2,
                "line_end": 2,
                "entity_type": "CODE_SYMBOL",
                "predicate": "HAS_VALUE",
                "statement": "App.value is initialized to 3.",
                "condition": None,
                "limitation": None,
            }
            for index in range(1, 3)
        ]
        gateway = SequencedGateway(
            (
                {"candidates": candidates, "limitations": []},
                {
                    "decision": "ACCEPT",
                    "accepted_candidate_keys": ["c1", "c2"],
                    "all_supported_objective_aspects_covered": True,
                    "findings": [],
                },
                DomainError(
                    ErrorCode.STRUCTURED_OUTPUT_INVALID,
                    "coverage output reached the provider length limit",
                    {"invalid_output_termination_reason": "length"},
                ),
                need_coverage_review(
                    artifact_id=artifact.artifact_id.value,
                    need_to_candidate_keys={"N1": ["c1"]},
                ),
                need_coverage_review(
                    artifact_id=artifact.artifact_id.value,
                    need_to_candidate_keys={"N2": ["c2"]},
                ),
            )
        )
        request = self.request()
        request.requirement_plan = KnowledgeRequirementPlan(
            needs=tuple(
                KnowledgeNeed(
                    need_id=f"N{index}",
                    question=f"What initializer detail {index} is declared?",
                    required_kinds=(KnowledgeObjectKind.FACT,),
                    required_type_names=(),
                    required_terms=("initializer",),
                    minimum_support_count=1,
                )
                for index in range(1, 3)
            )
        )

        bundle = ModelReviewedKnowledgeBuilder(
            gateway, self.configuration()
        ).build(request=request, target=request.target, artifacts=(artifact,))

        self.assertEqual(len(bundle.facts), 2)
        coverage_states = [
            json.loads(context.manifest.items[1].content)
            for context in gateway.contexts
            if context.manifest.execution_stage == "NEED_COVERAGE_REVIEW"
        ]
        self.assertEqual(
            [
                [
                    item["need_id"]
                    for item in state["review_phase"]["focused_needs"]
                ]
                for state in coverage_states
            ],
            [["N1", "N2"], ["N1"], ["N2"]],
        )

    def test_truncated_single_need_coverage_is_retried_by_artifact(self):
        first_artifact = self.artifact()
        second_artifact = replace(
            first_artifact,
            artifact_id=StableId(
                "artifact_00000000000000000000000000000002"
            ),
            source_native_identity="src/SecondApp.java",
        )
        candidates = [
            {
                "candidate_key": key,
                "need_ids": ["N1"],
                "artifact_id": artifact.artifact_id.value,
                "line_start": 2,
                "line_end": 2,
                "entity_type": "CODE_SYMBOL",
                "predicate": "HAS_VALUE",
                "statement": "App.value is initialized to 3.",
                "condition": None,
                "limitation": None,
            }
            for key, artifact in (
                ("c1", first_artifact),
                ("c2", second_artifact),
            )
        ]
        gateway = SequencedGateway(
            (
                {"candidates": candidates, "limitations": []},
                {
                    "decision": "ACCEPT",
                    "accepted_candidate_keys": ["c1", "c2"],
                    "all_supported_objective_aspects_covered": True,
                    "findings": [],
                },
                DomainError(
                    ErrorCode.STRUCTURED_OUTPUT_INVALID,
                    "coverage output reached the provider length limit",
                    {"invalid_output_termination_reason": "length"},
                ),
                need_coverage_review(
                    artifact_id=first_artifact.artifact_id.value,
                    need_to_candidate_keys={"N1": ["c1"]},
                ),
                need_coverage_review(
                    artifact_id=second_artifact.artifact_id.value,
                    need_to_candidate_keys={"N1": ["c2"]},
                ),
            )
        )
        request = self.request()
        request.requirement_plan = KnowledgeRequirementPlan(
            needs=(
                KnowledgeNeed(
                    need_id="N1",
                    question="What complete declarations are present?",
                    required_kinds=(KnowledgeObjectKind.FACT,),
                    required_type_names=(),
                    required_terms=("initializer",),
                    minimum_support_count=1,
                ),
            )
        )

        bundle = ModelReviewedKnowledgeBuilder(
            gateway, self.configuration()
        ).build(
            request=request,
            target=request.target,
            artifacts=(first_artifact, second_artifact),
        )

        self.assertEqual(len(bundle.facts), 2)
        coverage_states = [
            json.loads(context.manifest.items[1].content)
            for context in gateway.contexts
            if context.manifest.execution_stage == "NEED_COVERAGE_REVIEW"
        ]
        self.assertEqual(
            [len(state["artifacts"]) for state in coverage_states],
            [2, 1, 1],
        )
        self.assertEqual(
            [
                state["review_phase"]["evidence_scope"]
                for state in coverage_states
            ],
            [
                "COMPLETE_FOCUSED_EVIDENCE",
                "SINGLE_ARTIFACT_SHARD",
                "SINGLE_ARTIFACT_SHARD",
            ],
        )
        self.assertIn(
            "Do not require this shard to answer the whole Need",
            coverage_states[1]["review_phase"]["required_action"],
        )
        self.assertEqual(
            [
                state["artifacts"][0]["artifact_id"]
                for state in coverage_states[1:]
            ],
            [
                first_artifact.artifact_id.value,
                second_artifact.artifact_id.value,
            ],
        )

    def test_need_coverage_receives_all_artifacts_even_when_candidates_omit_one(self):
        first_artifact = self.artifact()
        second_artifact = replace(
            first_artifact,
            artifact_id=StableId(
                "artifact_00000000000000000000000000000002"
            ),
            source_native_identity="src/SecondApp.java",
        )
        candidates = [
            {
                "candidate_key": f"c{index}",
                "need_ids": ["N1" if index <= 4 else "N2"],
                "artifact_id": (
                    first_artifact.artifact_id.value
                    if index <= 4
                    else second_artifact.artifact_id.value
                ),
                "line_start": 2,
                "line_end": 2,
                "entity_type": "CODE_SYMBOL",
                "predicate": "HAS_VALUE",
                "statement": "App.value is initialized to 3.",
                "condition": None,
                "limitation": None,
            }
            for index in range(1, 9)
        ]
        acceptance = {
            "decision": "ACCEPT",
            "accepted_candidate_keys": [
                item["candidate_key"] for item in candidates
            ],
            "all_supported_objective_aspects_covered": True,
            "findings": [],
        }
        gateway = SequencedGateway(
            (
                {"candidates": candidates, "limitations": []},
                acceptance,
                need_coverage_review(
                    artifact_id=first_artifact.artifact_id.value,
                    need_to_candidate_keys={"N1": ["c1"]},
                ),
                need_coverage_review(
                    artifact_id=second_artifact.artifact_id.value,
                    need_to_candidate_keys={"N2": ["c5"]},
                ),
            )
        )
        request = self.request()
        request.requirement_plan = KnowledgeRequirementPlan(
            needs=tuple(
                KnowledgeNeed(
                    need_id=need_id,
                    question="What exact initializer value is declared?",
                    required_kinds=(KnowledgeObjectKind.FACT,),
                    required_type_names=(),
                    required_terms=("initializer",),
                    minimum_support_count=1,
                )
                for need_id in ("N1", "N2")
            ),
        )

        bundle = ModelReviewedKnowledgeBuilder(
            gateway, self.configuration()
        ).build(
            request=request,
            target=request.target,
            artifacts=(first_artifact, second_artifact),
        )

        self.assertEqual(len(bundle.facts), 8)
        coverage_states = [
            json.loads(context.manifest.items[1].content)
            for context in gateway.contexts[2:]
            if "artifacts"
            in json.loads(context.manifest.items[1].content)
        ]
        self.assertEqual(
            [
                [candidate["candidate_key"] for candidate in state["candidates"]]
                for state in coverage_states
            ],
            [
                ["c1", "c2", "c3", "c4", "c5", "c6", "c7", "c8"],
                ["c1", "c2", "c3", "c4", "c5", "c6", "c7", "c8"],
            ],
        )
        self.assertEqual(
            [
                [artifact["artifact_id"] for artifact in state["artifacts"]]
                for state in coverage_states
            ],
            [
                [
                    first_artifact.artifact_id.value,
                    second_artifact.artifact_id.value,
                ],
                [
                    first_artifact.artifact_id.value,
                    second_artifact.artifact_id.value,
                ],
            ],
        )

    def test_need_coverage_batches_a_dense_need_separately(self):
        needs = tuple(
            KnowledgeNeed(
                need_id=f"N{index}",
                question=f"Question {index}",
                required_kinds=(KnowledgeObjectKind.FACT,),
                required_type_names=(),
                required_terms=(),
                minimum_support_count=1,
            )
            for index in range(1, 5)
        )
        entries = [
            (
                needs[0],
                [
                    {"candidate_key": f"dense-{index}"}
                    for index in range(1, 9)
                ],
            ),
            (needs[1], [{"candidate_key": "short-1"}]),
            (needs[2], [{"candidate_key": "short-2"}]),
            (needs[3], [{"candidate_key": "short-3"}]),
        ]

        batches = _coverage_audit_batches(entries)

        self.assertEqual(
            [[entry[0].need_id for entry in batch] for batch in batches],
            [["N1"], ["N2", "N3", "N4"]],
        )

    def test_single_need_coverage_is_sharded_by_evidence_artifact(self):
        need = KnowledgeNeed(
            need_id="N1",
            question="What is the complete flow?",
            required_kinds=(KnowledgeObjectKind.FACT,),
            required_type_names=(),
            required_terms=(),
            minimum_support_count=1,
        )
        candidates = [
            {
                "candidate_key": "c1",
                "need_ids": ["N1"],
                "artifact_id": "artifact-a",
            },
            {
                "candidate_key": "c2",
                "need_ids": ["N1"],
                "artifact_id": "artifact-b",
            },
        ]
        batch = ((need, candidates),)

        audits = _coverage_audit_units(
            (batch,), candidates, frozenset({"c1", "c2"})
        )

        self.assertEqual(len(audits), 2)
        self.assertEqual(
            [artifact_ids for _, artifact_ids in audits],
            [frozenset({"artifact-a"}), frozenset({"artifact-b"})],
        )

    def test_single_need_coverage_shards_include_artifact_without_candidate(self):
        need = KnowledgeNeed(
            need_id="N1",
            question="What is the complete flow?",
            required_kinds=(KnowledgeObjectKind.FACT,),
            required_type_names=(),
            required_terms=(),
            minimum_support_count=1,
        )
        candidates = [
            {
                "candidate_key": "c1",
                "need_ids": ["N1"],
                "artifact_id": "artifact-a",
            }
        ]
        batch = ((need, candidates),)

        audits = _coverage_audit_units(
            (batch,),
            candidates,
            frozenset({"c1"}),
            artifact_ids=("artifact-a", "artifact-b"),
        )

        self.assertEqual(
            [artifact_ids for _, artifact_ids in audits],
            [frozenset({"artifact-a"}), frozenset({"artifact-b"})],
        )

    def test_dense_single_need_coverage_is_pre_sharded_before_dispatch(self):
        need = KnowledgeNeed(
            need_id="N1",
            question="What is the complete flow?",
            required_kinds=(KnowledgeObjectKind.FACT,),
            required_type_names=(),
            required_terms=(),
            minimum_support_count=1,
        )
        candidates = [
            {
                "candidate_key": f"c{index}",
                "need_ids": ["N1"],
                "artifact_id": "artifact-a" if index < 5 else "artifact-b",
            }
            for index in range(1, 9)
        ]
        accepted = frozenset(
            str(candidate["candidate_key"]) for candidate in candidates
        )

        audits = _coverage_audit_plan(
            (((need, candidates),),),
            candidates,
            accepted,
            artifact_ids=("artifact-a", "artifact-b"),
        )

        self.assertEqual(
            [artifact_ids for _, artifact_ids in audits],
            [frozenset({"artifact-a"}), frozenset({"artifact-b"})],
        )

    def test_sparse_single_need_coverage_keeps_whole_evidence_audit(self):
        need = KnowledgeNeed(
            need_id="N1",
            question="What is the complete flow?",
            required_kinds=(KnowledgeObjectKind.FACT,),
            required_type_names=(),
            required_terms=(),
            minimum_support_count=1,
        )
        candidates = [
            {
                "candidate_key": "c1",
                "need_ids": ["N1"],
                "artifact_id": "artifact-a",
            },
            {
                "candidate_key": "c2",
                "need_ids": ["N1"],
                "artifact_id": "artifact-b",
            },
        ]

        audits = _coverage_audit_plan(
            (((need, candidates),),),
            candidates,
            frozenset({"c1", "c2"}),
            artifact_ids=("artifact-a", "artifact-b"),
        )

        self.assertEqual(audits, ((((need, candidates),), None),))

    def test_saturation_challenge_selects_one_highest_density_batch(self):
        needs = tuple(
            KnowledgeNeed(
                need_id=f"N{index}",
                question=f"Question {index}",
                required_kinds=(KnowledgeObjectKind.FACT,),
                required_type_names=(),
                required_terms=(f"term-{index}",),
                minimum_support_count=1,
            )
            for index in range(1, 4)
        )
        batches = (
            (
                (
                    needs[0],
                    [
                        {"candidate_key": "c1", "artifact_id": "a1"},
                        {"candidate_key": "c2", "artifact_id": "a1"},
                    ],
                ),
            ),
            (
                (
                    needs[1],
                    [
                        {"candidate_key": "c3", "artifact_id": "a2"},
                        {"candidate_key": "c4", "artifact_id": "a3"},
                        {"candidate_key": "c5", "artifact_id": "a3"},
                    ],
                ),
                (
                    needs[2],
                    [{"candidate_key": "c4", "artifact_id": "a3"}],
                ),
            ),
        )

        self.assertEqual(_saturation_challenge_batch_index(batches), 2)

    def test_completeness_challenge_uses_only_evidence_density(self):
        compact = [
            {"candidate_key": "c1", "artifact_id": "artifact-a"},
            {"candidate_key": "c2", "artifact_id": "artifact-a"},
            {"candidate_key": "c3", "artifact_id": "artifact-a"},
        ]
        dense = [
            *compact,
            {"candidate_key": "c4", "artifact_id": "artifact-a"},
        ]
        distributed = [
            {"candidate_key": "c1", "artifact_id": "artifact-a"},
            {"candidate_key": "c2", "artifact_id": "artifact-b"},
            {"candidate_key": "c3", "artifact_id": "artifact-c"},
        ]

        self.assertFalse(_requires_completeness_challenge(compact))
        self.assertTrue(_requires_completeness_challenge(dense))
        self.assertTrue(_requires_completeness_challenge(distributed))

    def test_fact_builder_repairs_candidate_prose_to_the_user_request_script(self):
        artifact = self.artifact()
        insufficient_language = {
            "candidate_key": "app-value",
            "need_ids": ["OBJECTIVE"],
            "artifact_id": artifact.artifact_id.value,
            "line_start": 2,
            "line_end": 2,
            "entity_type": "CODE_SYMBOL",
            "predicate": "HAS_VALUE",
            "statement": "App.value 设 3.",
            "condition": None,
            "limitation": None,
        }
        chinese = {
            **insufficient_language,
            "statement": "App.value 的初始值为 3。",
        }
        gateway = SequencedGateway(
            (
                {"candidates": [insufficient_language], "limitations": []},
                {"candidates": [chinese], "limitations": []},
                {
                    "decision": "ACCEPT",
                    "accepted_candidate_keys": ["app-value"],
                    "all_supported_objective_aspects_covered": True,
                    "findings": [],
                },
            )
        )
        request = self.request()
        request.objective.description = (
            "回答语言：简体中文。\n当前问题：App.value 的初始值是什么？"
        )

        bundle = ModelReviewedKnowledgeBuilder(
            gateway, self.configuration()
        ).build(
            request=request,
            target=request.target,
            artifacts=(artifact,),
        )

        self.assertEqual(gateway.calls, 3)
        self.assertEqual(bundle.facts[0].object_value, chinese["statement"])
        repair_state = json.loads(gateway.contexts[1].manifest.items[1].content)
        self.assertEqual(
            repair_state["contract_repair"]["last_error_details"][
                "required_response_script"
            ],
            "CJK",
        )
        self.assertEqual(
            repair_state["contract_repair"]["last_error_details"][
                "actual_script_character_count"
            ],
            1,
        )
        self.assertEqual(
            repair_state["contract_repair"]["last_error_details"][
                "minimum_required_script_characters"
            ],
            2,
        )
        proposal_state = json.loads(gateway.contexts[0].manifest.items[1].content)
        self.assertEqual(
            proposal_state["response_language_contract"][
                "required_unicode_script"
            ],
            "CJK",
        )
        self.assertIn(
            "Apply this rule uniformly to every language",
            gateway.contexts[0].manifest.items[0].content,
        )
        self.assertIn(
            "never return the offending statement unchanged",
            gateway.contexts[1].manifest.items[0].content,
        )
        self.assertIn(
            "source-language control-flow keywords",
            repair_state["contract_repair"]["required_action"],
        )
        self.assertIn(
            "minimum_required_script_characters is met",
            repair_state["contract_repair"]["required_action"],
        )

    def test_fact_builder_does_not_truncate_a_convergent_language_repair_at_five_calls(
        self,
    ):
        artifact = self.artifact()
        insufficient_language = {
            "candidate_key": "app-value",
            "need_ids": ["OBJECTIVE"],
            "artifact_id": artifact.artifact_id.value,
            "line_start": 2,
            "line_end": 2,
            "entity_type": "CODE_SYMBOL",
            "predicate": "HAS_VALUE",
            "statement": "App.value 设 3.",
            "condition": None,
            "limitation": None,
        }
        chinese = {
            **insufficient_language,
            "statement": "App.value 的初始值为 3。",
        }
        gateway = SequencedGateway(
            (
                *(({"candidates": [insufficient_language], "limitations": []},) * 5),
                {"candidates": [chinese], "limitations": []},
                {
                    "decision": "ACCEPT",
                    "accepted_candidate_keys": ["app-value"],
                    "all_supported_objective_aspects_covered": True,
                    "findings": [],
                },
            )
        )
        request = self.request()
        request.objective.description = (
            "回答语言：简体中文。\n当前问题：App.value 的初始值是什么？"
        )

        bundle = ModelReviewedKnowledgeBuilder(
            gateway, self.configuration()
        ).build(
            request=request,
            target=request.target,
            artifacts=(artifact,),
        )

        self.assertEqual(gateway.calls, 7)
        self.assertEqual(bundle.facts[0].object_value, chinese["statement"])
        final_repair_state = json.loads(
            gateway.contexts[5].manifest.items[1].content
        )
        self.assertIn(
            "RESPONSE_LANGUAGE_INVALID",
            final_repair_state["contract_repair"]["last_error_details"][
                "validation_violations"
            ],
        )

    def test_fact_builder_retries_statement_with_embedded_metadata_labels(self):
        artifact = self.artifact()
        candidate = {
            "candidate_key": "app-value",
            "need_ids": ["OBJECTIVE"],
            "artifact_id": artifact.artifact_id.value,
            "line_start": 2,
            "line_end": 2,
            "entity_type": "CODE_SYMBOL",
            "predicate": "HAS_VALUE",
            "statement": "App.value is initialized to 3.",
            "condition": None,
            "limitation": None,
        }
        invalid = {
            **candidate,
            "statement": "App.value is initialized to 3. Limitation: null",
        }
        gateway = SequencedGateway(
            (
                {"candidates": [invalid], "limitations": []},
                {"candidates": [candidate], "limitations": []},
                {
                    "decision": "ACCEPT",
                    "accepted_candidate_keys": ["app-value"],
                    "all_supported_objective_aspects_covered": True,
                    "findings": [],
                },
            )
        )

        bundle = ModelReviewedKnowledgeBuilder(
            gateway, self.configuration()
        ).build(
            request=self.request(),
            target=self.request().target,
            artifacts=(artifact,),
        )

        self.assertEqual(len(bundle.facts), 1)
        self.assertNotIn("Limitation: null", bundle.facts[0].object_value)
        self.assertEqual(gateway.calls, 3)
        self.assertTrue(
            gateway.contexts[1].execution_envelope_ref.endswith(
                ":contract-retry:2"
            )
        )
        repair_state = json.loads(gateway.contexts[1].manifest.items[1].content)
        self.assertIn("contract_repair", repair_state)
        self.assertIn(
            "replacement JSON",
            repair_state["contract_repair"]["required_action"],
        )

    def test_fact_text_uses_only_self_contained_statement(self):
        text = _fact_text(
            {
                "statement": "仅在模板有效时，该方法返回已渲染的文档；源码只证明该返回行为。",
                "condition": "仅在模板有效时",
                "limitation": "只证明源码中的返回行为",
            }
        )

        self.assertEqual(
            text,
            "仅在模板有效时，该方法返回已渲染的文档；源码只证明该返回行为。",
        )
        self.assertNotIn("Condition:", text)
        self.assertNotIn("Limitation:", text)

    def test_fact_candidate_contract_rejects_non_null_compatibility_metadata(self):
        artifact = self.artifact()
        candidate = {
            "candidate_key": "app-value",
            "need_ids": ["OBJECTIVE"],
            "artifact_id": artifact.artifact_id.value,
            "line_start": 2,
            "line_end": 2,
            "entity_type": "CODE_SYMBOL",
            "predicate": "HAS_VALUE",
            "statement": "App.value is initialized to 3.",
            "condition": "when configured",
            "limitation": None,
        }

        violations, _ = _candidate_contract_violations(
            candidate,
            existing_keys=set(),
            allowed_need_ids=frozenset({"OBJECTIVE"}),
            artifact_ids=frozenset({artifact.artifact_id.value}),
        )

        self.assertIn("CONDITION_MUST_BE_NULL", violations)

    def test_fact_builder_normalizes_textual_null_without_rewriting_candidates(self):
        artifact = self.artifact()
        candidate = {
            "candidate_key": "app-value",
            "need_ids": ["OBJECTIVE"],
            "artifact_id": artifact.artifact_id.value,
            "line_start": 2,
            "line_end": 2,
            "entity_type": "CODE_SYMBOL",
            "predicate": "HAS_VALUE",
            "statement": "App.value is initialized to 3.",
            "condition": None,
            "limitation": None,
        }
        gateway = SequencedGateway(
            (
                {
                    "candidates": [{**candidate, "limitation": "null"}],
                    "limitations": [],
                },
                {
                    "decision": "ACCEPT",
                    "accepted_candidate_keys": ["app-value"],
                    "all_supported_objective_aspects_covered": True,
                    "findings": [],
                },
            )
        )

        bundle = ModelReviewedKnowledgeBuilder(
            gateway, self.configuration()
        ).build(
            request=self.request(),
            target=self.request().target,
            artifacts=(artifact,),
        )

        self.assertEqual(len(bundle.facts), 1)
        self.assertEqual(gateway.calls, 2)

    def test_fact_builder_normalizes_omitted_nullable_candidate_fields(self):
        artifact = self.artifact()
        candidate = {
            "candidate_key": "app-value",
            "need_ids": ["OBJECTIVE"],
            "artifact_id": artifact.artifact_id.value,
            "line_start": 2,
            "line_end": 2,
            "entity_type": "CODE_SYMBOL",
            "predicate": "HAS_VALUE",
            "statement": "App.value is initialized to 3.",
        }
        gateway = SequencedGateway(
            (
                {"candidates": [candidate], "limitations": []},
                {
                    "decision": "ACCEPT",
                    "accepted_candidate_keys": ["app-value"],
                    "all_supported_objective_aspects_covered": True,
                    "findings": [],
                },
            )
        )

        bundle = ModelReviewedKnowledgeBuilder(
            gateway, self.configuration()
        ).build(
            request=self.request(),
            target=self.request().target,
            artifacts=(artifact,),
        )

        self.assertEqual(gateway.calls, 2)
        self.assertEqual(bundle.facts[0].object_value, candidate["statement"])

    def test_fact_builder_has_no_language_specific_constructor_parser(self):
        payload = (
            b"public final class Template {\n"
            b"  static Template compile(Input input) {\n"
            b"    Template value = new Template();\n"
            b"    value.document = new Document(input);\n"
            b"    value.resolver = new Resolver();\n"
            b"    return value;\n"
            b"  }\n"
            b"}\n"
        )
        artifact = SourceArtifact(
            artifact_id=StableId("artifact_00000000000000000000000000000002"),
            artifact_kind="LOCAL_GIT_FILE@1",
            payload_schema_version="LOCAL_GIT_FILE@1",
            source_id=StableId("source_00000000000000000000000000000002"),
            source_revision=SimpleNamespace(value=1),
            source_context_id=StableId(
                "context_00000000000000000000000000000002"
            ),
            source_native_identity="src/Template.java",
            content_digest=Digest(f"sha256:{hashlib.sha256(payload).hexdigest()}"),
            payload=payload,
            classification="INTERNAL",
            truncated=False,
            truncation_offset=None,
            identity_digest=digest_of("template-artifact-identity"),
        )
        candidate = {
            "candidate_key": "compile-flow",
            "need_ids": ["OBJECTIVE"],
            "artifact_id": artifact.artifact_id.value,
            "line_start": 2,
            "line_end": 6,
            "entity_type": "CODE_SYMBOL",
            "predicate": "CALLS",
            "statement": "Template.compile constructs a Resolver.",
            "condition": None,
            "limitation": None,
        }
        gateway = SequencedGateway(
            (
                {"candidates": [candidate], "limitations": []},
                {
                    "decision": "ACCEPT",
                    "accepted_candidate_keys": ["compile-flow"],
                    "all_supported_objective_aspects_covered": True,
                    "findings": [],
                },
            )
        )

        bundle = ModelReviewedKnowledgeBuilder(
            gateway, self.configuration()
        ).build(request=self.request(), target=self.request().target, artifacts=(artifact,))

        self.assertEqual(len(bundle.facts), 1)
        self.assertEqual(gateway.calls, 2)
        self.assertIn("constructs a Resolver", bundle.facts[0].object_value)
        self.assertNotIn("Limitation:", bundle.facts[0].object_value)
        self.assertIn(
            "configured output-token limit as a hard transport boundary",
            gateway.contexts[0].manifest.items[0].content,
        )
        self.assertIn(
            "terminology bridge must be inside the grounded statement",
            gateway.contexts[0].manifest.items[0].content,
        )
        self.assertIn(
            "atomic or conditional state changes",
            gateway.contexts[0].manifest.items[0].content,
        )
        self.assertIn(
            "no direct support is not a source-supported aspect",
            gateway.contexts[1].manifest.items[0].content,
        )
        self.assertIn(
            "unsupported Needs can be disclosed truthfully as gaps",
            gateway.contexts[1].manifest.items[0].content,
        )

    def test_fact_builder_preserves_a_final_generic_contract_repair(self):
        payload = (
            b"public final class Template {\n"
            b"  static Template compile(Input input) {\n"
            b"    Template value = new Template();\n"
            b"    value.document = new Document(input);\n"
            b"    value.resolver = new Resolver();\n"
            b"    return value;\n"
            b"  }\n"
            b"}\n"
        )
        artifact = SourceArtifact(
            artifact_id=StableId("artifact_00000000000000000000000000000002"),
            artifact_kind="LOCAL_GIT_FILE@1",
            payload_schema_version="LOCAL_GIT_FILE@1",
            source_id=StableId("source_00000000000000000000000000000002"),
            source_revision=SimpleNamespace(value=1),
            source_context_id=StableId(
                "context_00000000000000000000000000000002"
            ),
            source_native_identity="src/Template.java",
            content_digest=Digest(f"sha256:{hashlib.sha256(payload).hexdigest()}"),
            payload=payload,
            classification="INTERNAL",
            truncated=False,
            truncation_offset=None,
            identity_digest=digest_of("template-artifact-identity"),
        )
        valid = {
            "candidate_key": "compile-flow",
            "need_ids": ["OBJECTIVE"],
            "artifact_id": artifact.artifact_id.value,
            "line_start": 2,
            "line_end": 6,
            "entity_type": "CODE_SYMBOL",
            "predicate": "CALLS",
            "statement": (
                "Template.compile constructs a Template, a Document, and a Resolver."
            ),
            "condition": None,
            "limitation": None,
        }
        gateway = SequencedGateway(
            (
                "truncated output",
                "truncated output",
                "truncated output",
                {"candidates": [valid], "limitations": []},
                {
                    "decision": "ACCEPT",
                    "accepted_candidate_keys": ["compile-flow"],
                    "all_supported_objective_aspects_covered": True,
                    "findings": [],
                },
            )
        )

        bundle = ModelReviewedKnowledgeBuilder(
            gateway, self.configuration()
        ).build(request=self.request(), target=self.request().target, artifacts=(artifact,))

        self.assertEqual(len(bundle.facts), 1)
        self.assertEqual(gateway.calls, 5)
        repair = json.loads(gateway.contexts[3].manifest.items[1].content)[
            "contract_repair"
        ]
        self.assertIn("replacement JSON", repair["required_action"])

    def test_fact_builder_identifies_out_of_range_artifact_lines_during_repair(self):
        artifact = self.artifact()
        candidate = {
            "candidate_key": "app-value",
            "need_ids": ["OBJECTIVE"],
            "artifact_id": artifact.artifact_id.value,
            "line_start": 2,
            "line_end": 2,
            "entity_type": "CODE_SYMBOL",
            "predicate": "HAS_VALUE",
            "statement": "App.value is initialized to 3.",
            "condition": None,
            "limitation": None,
        }
        gateway = SequencedGateway(
            (
                {
                    "candidates": [{**candidate, "line_end": 99}],
                    "limitations": [],
                },
                {"candidates": [candidate], "limitations": []},
                {
                    "decision": "ACCEPT",
                    "accepted_candidate_keys": ["app-value"],
                    "all_supported_objective_aspects_covered": True,
                    "findings": [],
                },
            )
        )

        bundle = ModelReviewedKnowledgeBuilder(
            gateway, self.configuration()
        ).build(
            request=self.request(),
            target=self.request().target,
            artifacts=(artifact,),
        )

        self.assertEqual(len(bundle.facts), 1)
        repair = json.loads(gateway.contexts[1].manifest.items[1].content)[
            "contract_repair"
        ]
        details = repair["last_error_details"]
        self.assertEqual(details["candidate_key"], "app-value")
        self.assertEqual(details["line_end"], 99)
        self.assertEqual(details["artifact_line_count"], 3)

    def test_fact_builder_retries_locally_invalid_review_contract(self):
        artifact = self.artifact()
        candidate = {
            "candidate_key": "app-value",
            "need_ids": ["OBJECTIVE"],
            "artifact_id": artifact.artifact_id.value,
            "line_start": 2,
            "line_end": 2,
            "entity_type": "CODE_SYMBOL",
            "predicate": "HAS_VALUE",
            "statement": "App.value is initialized to 3.",
            "condition": None,
            "limitation": None,
        }
        gateway = SequencedGateway(
            (
                {"candidates": [candidate], "limitations": []},
                {
                    "decision": "ACCEPT",
                    "accepted_candidate_keys": [],
                    "all_supported_objective_aspects_covered": True,
                    "findings": [],
                },
                {
                    "decision": "ACCEPT",
                    "accepted_candidate_keys": ["app-value"],
                    "all_supported_objective_aspects_covered": True,
                    "findings": [],
                },
            )
        )

        bundle = ModelReviewedKnowledgeBuilder(
            gateway, self.configuration()
        ).build(
            request=self.request(),
            target=self.request().target,
            artifacts=(artifact,),
        )

        self.assertEqual(len(bundle.facts), 1)
        self.assertEqual(gateway.calls, 3)
        self.assertTrue(
            gateway.contexts[2].execution_envelope_ref.endswith(
                ":contract-retry:2"
            )
        )

    def test_fact_builder_cannot_claim_complete_coverage_after_rejecting_a_need(self):
        artifact = self.artifact()
        first = {
            "candidate_key": "unsupported-scope",
            "need_ids": ["need:scope"],
            "artifact_id": artifact.artifact_id.value,
            "line_start": 1,
            "line_end": 1,
            "entity_type": "CODE_SYMBOL",
            "predicate": "DESCRIBED_AS",
            "statement": "App is safe in every runtime.",
            "condition": None,
            "limitation": None,
        }
        second = {
            "candidate_key": "declared-value",
            "need_ids": ["need:value"],
            "artifact_id": artifact.artifact_id.value,
            "line_start": 2,
            "line_end": 2,
            "entity_type": "CODE_SYMBOL",
            "predicate": "HAS_VALUE",
            "statement": "App.value is initialized to 3.",
            "condition": None,
            "limitation": None,
        }
        incomplete_acceptance = {
            "decision": "ACCEPT",
            "accepted_candidate_keys": ["declared-value"],
            "all_supported_objective_aspects_covered": True,
            "findings": ["The source does not establish runtime safety."],
        }
        corrected_rejection = {
            **incomplete_acceptance,
            "decision": "REJECT",
            "all_supported_objective_aspects_covered": False,
        }
        value_coverage = need_coverage_review(
            artifact_id=artifact.artifact_id.value,
            need_to_candidate_keys={"need:value": ["declared-value"]},
        )
        unsupported_scope_coverage = need_coverage_review(
            artifact_id=artifact.artifact_id.value,
            need_to_candidate_keys={"need:scope": []},
            unsupported_need_ids=("need:scope",),
        )
        final_acceptance = {
            "decision": "ACCEPT",
            "accepted_candidate_keys": ["declared-value"],
            "all_supported_objective_aspects_covered": True,
            "findings": [],
        }
        gateway = SequencedGateway(
            (
                {"candidates": [first, second], "limitations": []},
                incomplete_acceptance,
                corrected_rejection,
                value_coverage,
                {
                    "retained_candidate_keys": ["declared-value"],
                    "replacements": [],
                    "limitations": [],
                },
                final_acceptance,
                unsupported_scope_coverage,
            )
        )
        request = self.request()
        request.requirement_plan = KnowledgeRequirementPlan(
            needs=(
                KnowledgeNeed(
                    need_id="need:scope",
                    question="What runtime-safety scope does the source establish?",
                    required_kinds=(KnowledgeObjectKind.FACT,),
                    required_type_names=(),
                    required_terms=("runtime safety",),
                    minimum_support_count=1,
                ),
                KnowledgeNeed(
                    need_id="need:value",
                    question="What source initializer is declared for App.value?",
                    required_kinds=(KnowledgeObjectKind.FACT,),
                    required_type_names=(),
                    required_terms=("App.value",),
                    minimum_support_count=1,
                ),
            ),
            joint_constraints=(),
        )

        bundle = ModelReviewedKnowledgeBuilder(
            gateway, self.configuration()
        ).build(request=request, target=request.target, artifacts=(artifact,))

        self.assertEqual(len(bundle.facts), 1)
        self.assertIn("initialized to 3", bundle.facts[0].object_value)
        self.assertEqual(gateway.calls, 8)
        self.assertTrue(
            gateway.contexts[2].execution_envelope_ref.endswith(
                ":contract-retry:2"
            )
        )
        repair_state = json.loads(gateway.contexts[4].manifest.items[1].content)
        self.assertEqual(
            repair_state["prior_review_findings"],
            ["The source does not establish runtime safety."],
        )
        self.assertIn(
            "every need_id present on any proposed candidate",
            gateway.contexts[1].manifest.items[0].content,
        )

    def test_fact_builder_publishes_grounded_facts_when_a_need_is_unsupported(self):
        artifact = self.artifact()
        candidate = {
            "candidate_key": "declared-value",
            "need_ids": ["need:value"],
            "artifact_id": artifact.artifact_id.value,
            "line_start": 2,
            "line_end": 2,
            "entity_type": "CODE_SYMBOL",
            "predicate": "HAS_VALUE",
            "statement": "App.value is initialized to 3.",
            "condition": None,
            "limitation": None,
        }
        gateway = SequencedGateway(
            (
                {"candidates": [candidate], "limitations": []},
                {
                    "decision": "ACCEPT",
                    "accepted_candidate_keys": ["declared-value"],
                    "all_supported_objective_aspects_covered": True,
                    "findings": [],
                },
                need_coverage_review(
                    artifact_id=artifact.artifact_id.value,
                    need_to_candidate_keys={
                        "need:value": ["declared-value"],
                        "need:rationale": [],
                    },
                    unsupported_need_ids=("need:rationale",),
                ),
            )
        )
        request = self.request()
        request.requirement_plan = KnowledgeRequirementPlan(
            needs=(
                KnowledgeNeed(
                    need_id="need:value",
                    question="What initializer value is declared?",
                    required_kinds=(KnowledgeObjectKind.FACT,),
                    required_type_names=(),
                    required_terms=("initializer",),
                    minimum_support_count=1,
                ),
                KnowledgeNeed(
                    need_id="need:rationale",
                    question="What design rationale does the source state?",
                    required_kinds=(KnowledgeObjectKind.FACT,),
                    required_type_names=(),
                    required_terms=("rationale",),
                    minimum_support_count=1,
                ),
            ),
            joint_constraints=(),
        )

        bundle = ModelReviewedKnowledgeBuilder(
            gateway, self.configuration()
        ).build(request=request, target=request.target, artifacts=(artifact,))

        self.assertEqual(gateway.calls, 4)
        self.assertEqual(len(bundle.facts), 1)
        self.assertEqual(
            bundle.facts[0].reviewed_grounding.need_ids,
            ("need:value",),
        )

    def test_fact_builder_does_not_publish_reviewer_rejected_candidates(self):
        artifact = self.artifact()
        candidate = {
            "candidate_key": "overclaim",
            "need_ids": ["N1"],
            "artifact_id": artifact.artifact_id.value,
            "line_start": 1,
            "line_end": 1,
            "entity_type": "CODE_SYMBOL",
            "predicate": "DESCRIBED_AS",
            "statement": "App is always safe in every runtime.",
            "condition": None,
            "limitation": None,
        }
        rejection = {
            "decision": "REJECT",
            "accepted_candidate_keys": [],
            "all_supported_objective_aspects_covered": False,
            "findings": ["The excerpt does not prove runtime safety."],
        }
        proposal = {"candidates": [candidate], "limitations": []}
        repairs = tuple(
            {
                "retained_candidate_keys": [],
                "replacements": [
                    {
                        **candidate,
                        "statement": (
                            "App is always safe in every runtime "
                            f"under unsupported variant {index}."
                        ),
                    }
                ],
                "limitations": [],
            }
            for index in range(2, 13)
        )
        gateway = SequencedGateway(
            (
                proposal,
                rejection,
                *(
                    item
                    for repair in repairs
                    for item in (repair, rejection)
                ),
            )
        )
        request = self.request()
        request.requirement_plan = KnowledgeRequirementPlan(
            needs=(
                KnowledgeNeed(
                    need_id="N1",
                    question="What safety behavior does the source prove?",
                    required_kinds=(KnowledgeObjectKind.FACT,),
                    required_type_names=(),
                    required_terms=("safety",),
                    minimum_support_count=1,
                ),
            )
        )

        bundle = ModelReviewedKnowledgeBuilder(
            gateway, self.configuration()
        ).build(request=request, target=request.target, artifacts=(artifact,))

        self.assertEqual(bundle.entities, ())
        self.assertEqual(bundle.facts, ())
        self.assertEqual(gateway.calls, 24)
        self.assertNotIn(
            "NEED_COVERAGE_REVIEW",
            [context.manifest.execution_stage for context in gateway.contexts],
        )

    def test_fact_builder_can_publish_a_complete_fifth_coverage_repair(self):
        artifact = self.artifact()
        candidate = {
            "candidate_key": "app-value",
            "need_ids": ["OBJECTIVE"],
            "artifact_id": artifact.artifact_id.value,
            "line_start": 2,
            "line_end": 2,
            "entity_type": "CODE_SYMBOL",
            "predicate": "HAS_VALUE",
            "statement": "App.value is initialized to 3.",
            "condition": None,
            "limitation": None,
        }
        proposal = {"candidates": [candidate], "limitations": []}
        repairs = tuple(
            {
                "retained_candidate_keys": [],
                "replacements": [
                    {
                        **candidate,
                        "statement": (
                            "App.value is initialized to 3; coverage repair "
                            f"{index} preserves the declaration."
                        ),
                    }
                ],
                "limitations": [],
            }
            for index in range(2, 6)
        )
        rejection = {
            "decision": "REJECT",
            "accepted_candidate_keys": ["app-value"],
            "all_supported_objective_aspects_covered": False,
            "findings": ["A material source-visible result is still omitted."],
        }
        acceptance = {
            "decision": "ACCEPT",
            "accepted_candidate_keys": ["app-value"],
            "all_supported_objective_aspects_covered": True,
            "findings": [],
        }
        gateway = SequencedGateway(
            (
                proposal,
                rejection,
                repairs[0],
                rejection,
                repairs[1],
                rejection,
                repairs[2],
                rejection,
                repairs[3],
                acceptance,
            )
        )

        bundle = ModelReviewedKnowledgeBuilder(
            gateway, self.configuration()
        ).build(request=self.request(), target=self.request().target, artifacts=(artifact,))

        self.assertEqual(len(bundle.facts), 1)
        self.assertEqual(gateway.calls, 10)
        self.assertTrue(
            gateway.contexts[8].execution_envelope_ref.endswith(
                ":coverage-repair:5"
            )
        )

    def test_fact_builder_repairs_a_reviewed_objective_coverage_gap(self):
        artifact = self.artifact()
        candidate = {
            "candidate_key": "app-value",
            "need_ids": ["OBJECTIVE"],
            "artifact_id": artifact.artifact_id.value,
            "line_start": 2,
            "line_end": 2,
            "entity_type": "CODE_SYMBOL",
            "predicate": "HAS_VALUE",
            "statement": "App.value is initialized to 3.",
            "condition": None,
            "limitation": None,
        }
        finding = "The proposed set omits a material supported objective branch."
        repaired_candidate = {
            **candidate,
            "statement": (
                "App.value is initialized to 3 in the material source branch."
            ),
        }
        gateway = SequencedGateway(
            (
                {"candidates": [candidate], "limitations": []},
                {
                    "decision": "REJECT",
                    "accepted_candidate_keys": ["app-value"],
                    "all_supported_objective_aspects_covered": False,
                    "findings": [finding],
                },
                {
                    "retained_candidate_keys": [],
                    "replacements": [repaired_candidate],
                    "limitations": [],
                },
                {
                    "decision": "ACCEPT",
                    "accepted_candidate_keys": ["app-value"],
                    "all_supported_objective_aspects_covered": True,
                    "findings": [],
                },
            )
        )

        bundle = ModelReviewedKnowledgeBuilder(
            gateway, self.configuration()
        ).build(
            request=self.request(), target=self.request().target, artifacts=(artifact,)
        )

        self.assertEqual(len(bundle.facts), 1)
        repair_state = json.loads(gateway.contexts[2].manifest.items[1].content)
        self.assertEqual(repair_state["prior_review_findings"], [finding])
        self.assertIn("previous_proposed_candidates", repair_state)
        self.assertTrue(
            gateway.contexts[2].execution_envelope_ref.endswith(
                ":coverage-repair:2"
            )
        )

    def test_fact_repair_cannot_repeat_a_grounding_rejected_candidate(self):
        artifact = self.artifact()
        rejected = {
            "candidate_key": "c1",
            "need_ids": ["N1"],
            "artifact_id": artifact.artifact_id.value,
            "line_start": 1,
            "line_end": 1,
            "entity_type": "CODE_SYMBOL",
            "predicate": "HAS_VALUE",
            "statement": "App.value is initialized to 3.",
            "condition": None,
            "limitation": None,
        }
        corrected = {
            **rejected,
            "line_start": 2,
            "line_end": 2,
        }
        accepted_candidate = {
            **corrected,
            "candidate_key": "c2",
            "statement": "App declares a value field initialized to 3.",
        }
        added_candidate = {
            **corrected,
            "candidate_key": "c3",
            "statement": "The declared initializer value is 3.",
        }
        grounding_rejection = {
            "decision": "REJECT",
            "accepted_candidate_keys": ["c2"],
            "all_supported_objective_aspects_covered": False,
            "findings": [
                "c1 cites the class declaration rather than the initializer."
            ],
        }
        grounding_acceptance = {
            "decision": "ACCEPT",
            "accepted_candidate_keys": ["c1", "c2", "c3"],
            "all_supported_objective_aspects_covered": True,
            "findings": [],
        }
        repeated_patch = {
            "retained_candidate_keys": ["c2"],
            "replacements": [rejected, added_candidate],
            "limitations": [],
        }
        corrected_patch = {
            **repeated_patch,
            "replacements": [corrected, added_candidate],
        }
        gateway = SequencedGateway(
            (
                {
                    "candidates": [rejected, accepted_candidate],
                    "limitations": [],
                },
                grounding_rejection,
                repeated_patch,
                corrected_patch,
                grounding_acceptance,
                need_coverage_review(
                    artifact_id=artifact.artifact_id.value,
                    need_to_candidate_keys={"N1": ["c1"]},
                ),
            )
        )
        request = self.request()
        request.requirement_plan = KnowledgeRequirementPlan(
            needs=(
                KnowledgeNeed(
                    need_id="N1",
                    question="What exact initializer is declared for App.value?",
                    required_kinds=(KnowledgeObjectKind.FACT,),
                    required_type_names=(),
                    required_terms=("App.value",),
                    minimum_support_count=1,
                ),
            ),
            joint_constraints=(),
        )

        bundle = ModelReviewedKnowledgeBuilder(
            gateway, self.configuration()
        ).build(request=request, target=request.target, artifacts=(artifact,))

        self.assertEqual(len(bundle.facts), 3)
        self.assertEqual(gateway.calls, 7)
        self.assertTrue(
            gateway.contexts[3].execution_envelope_ref.endswith(
                ":coverage-repair:2:contract-retry:2"
            )
        )
        repair = json.loads(gateway.contexts[3].manifest.items[1].content)[
            "contract_repair"
        ]
        self.assertEqual(
            repair["last_error_details"][
                "unchanged_rejected_candidate_keys"
            ],
            ["c1"],
        )

    def test_fact_repair_cannot_publish_last_candidate_after_all_attempts_fail(self):
        artifact = self.artifact()
        rejected = {
            "candidate_key": "c1",
            "need_ids": ["N1"],
            "artifact_id": artifact.artifact_id.value,
            "line_start": 1,
            "line_end": 1,
            "entity_type": "CODE_SYMBOL",
            "predicate": "HAS_VALUE",
            "statement": "App.value is initialized to 3.",
            "condition": None,
            "limitation": None,
        }
        accepted = {
            **rejected,
            "candidate_key": "c2",
            "line_start": 2,
            "line_end": 2,
            "statement": "App declares a value field initialized to 3.",
        }
        grounding_rejection = {
            "decision": "REJECT",
            "accepted_candidate_keys": ["c2"],
            "all_supported_objective_aspects_covered": False,
            "findings": ["c1 cites the wrong source line."],
        }
        repeated_patch = {
            "retained_candidate_keys": ["c2"],
            "replacements": [rejected],
            "limitations": [],
        }
        gateway = SequencedGateway(
            (
                {"candidates": [rejected, accepted], "limitations": []},
                grounding_rejection,
                *((repeated_patch,) * 8),
            )
        )
        request = self.request()
        request.requirement_plan = KnowledgeRequirementPlan(
            needs=(
                KnowledgeNeed(
                    need_id="N1",
                    question="What exact initializer is declared for App.value?",
                    required_kinds=(KnowledgeObjectKind.FACT,),
                    required_type_names=(),
                    required_terms=("App.value",),
                    minimum_support_count=1,
                ),
            ),
        )

        with self.assertRaises(DomainError) as raised:
            ModelReviewedKnowledgeBuilder(
                gateway, self.configuration()
            ).build(
                request=request,
                target=request.target,
                artifacts=(artifact,),
            )

        self.assertEqual(
            raised.exception.code, ErrorCode.STRUCTURED_OUTPUT_INVALID
        )
        self.assertEqual(
            raised.exception.message,
            "fact proposer exhausted bounded contract retries",
        )
        self.assertEqual(gateway.calls, 10)

    def test_fact_repair_drops_a_rejected_key_from_retained_keys(self):
        artifact = self.artifact()
        rejected = {
            "candidate_key": "c1",
            "need_ids": ["N1"],
            "artifact_id": artifact.artifact_id.value,
            "line_start": 1,
            "line_end": 1,
            "entity_type": "CODE_SYMBOL",
            "predicate": "DECLARES",
            "statement": "App.value is initialized to 3.",
            "condition": None,
            "limitation": None,
        }
        accepted = {
            **rejected,
            "candidate_key": "c2",
            "line_start": 2,
            "line_end": 2,
        }
        added = {
            **accepted,
            "candidate_key": "c3",
            "statement": "The declared initializer value is 3.",
        }
        grounding_rejection = {
            "decision": "REJECT",
            "accepted_candidate_keys": ["c2"],
            "all_supported_objective_aspects_covered": False,
            "findings": ["c1 cites the wrong source line."],
        }
        grounding_acceptance = {
            "decision": "ACCEPT",
            "accepted_candidate_keys": ["c2", "c3"],
            "all_supported_objective_aspects_covered": True,
            "findings": [],
        }
        gateway = SequencedGateway(
            (
                {
                    "candidates": [rejected, accepted],
                    "limitations": [],
                },
                grounding_rejection,
                {
                    "retained_candidate_keys": ["c1", "c2"],
                    "replacements": [added],
                    "limitations": [],
                },
                grounding_acceptance,
                need_coverage_review(
                    artifact_id=artifact.artifact_id.value,
                    need_to_candidate_keys={"N1": ["c2"]},
                ),
                grounding_acceptance,
            )
        )
        request = self.request()
        request.requirement_plan = KnowledgeRequirementPlan(
            needs=(
                KnowledgeNeed(
                    need_id="N1",
                    question="What initializer value is declared?",
                    required_kinds=(KnowledgeObjectKind.FACT,),
                    required_type_names=(),
                    required_terms=("initializer",),
                    minimum_support_count=1,
                ),
            ),
        )

        bundle = ModelReviewedKnowledgeBuilder(
            gateway, self.configuration()
        ).build(request=request, target=request.target, artifacts=(artifact,))

        self.assertEqual(len(bundle.facts), 2)
        self.assertEqual(gateway.calls, 6)
        repair_state = json.loads(gateway.contexts[2].manifest.items[1].content)
        self.assertEqual(
            repair_state["grounding_rejected_candidate_keys"], ["c1"]
        )
        self.assertFalse(
            gateway.contexts[2].execution_envelope_ref.endswith(
                ":contract-retry:2"
            )
        )

    def test_fact_sequence_analysis_repairs_a_combined_call_return_fact(self):
        artifact = self.artifact()
        combined = {
            "candidate_key": "c1",
            "need_ids": ["N1"],
            "artifact_id": artifact.artifact_id.value,
            "line_start": 1,
            "line_end": 2,
            "entity_type": "CODE_SYMBOL",
            "predicate": "CALLS",
            "statement": (
                "App.main calls App.value; if the result is valid, "
                "App.main returns it."
            ),
            "condition": None,
            "limitation": None,
        }
        callee = {
            **combined,
            "candidate_key": "c2",
            "line_start": 2,
            "line_end": 2,
            "statement": "App.value computes the declared value 3.",
        }
        caller = {
            **combined,
            "statement": "App.main calls App.value.",
        }
        post_return = {
            **combined,
            "candidate_key": "c3",
            "statement": "After App.value returns, App.main then returns its result.",
        }
        still_combined = {
            **combined,
            "statement": "App.main calls App.value; then returns its result.",
        }
        initial_acceptance = {
            "decision": "ACCEPT",
            "accepted_candidate_keys": ["c1", "c2"],
            "all_supported_objective_aspects_covered": True,
            "findings": [],
        }
        repaired_acceptance = {
            **initial_acceptance,
            "accepted_candidate_keys": ["c1", "c2", "c3"],
        }
        initial_sequence = {
            "orders": [
                {"need_id": "N1", "reference_ids": ["c1", "c2"]}
            ],
            "edges": [],
            "call_return_spans": [
                {
                    "need_id": "N1",
                    "combined_reference_id": "c1",
                    "callee_internal_reference_id": "c2",
                    "callee_subject_fragment": "App.value",
                    "invocation_fragment": "calls App.value",
                    "temporal_connector_fragment": "; if the result is valid,",
                    "post_return_fragment": "App.main returns it",
                }
            ],
            "atomic_references": [
                {"need_id": "N1", "reference_ids": ["c2"]}
            ],
            "rationale": "AUDITED",
        }
        invalid_sequence = {
            **initial_sequence,
            "call_return_spans": [
                {
                    "need_id": "N1",
                    "combined_reference_id": "c1",
                    "callee_internal_reference_id": "c2",
                    "callee_subject_fragment": "App.value",
                    "invocation_fragment": "App.value()",
                    "temporal_connector_fragment": "then",
                    "post_return_fragment": "return result;",
                }
            ],
            "rationale": "AUDITED",
        }
        repaired_sequence = {
            "orders": [
                {
                    "need_id": "N1",
                    "reference_ids": ["c1", "c2", "c3"],
                }
            ],
            "edges": [
                {
                    "need_id": "N1",
                    "predecessor_reference_id": "c1",
                    "successor_reference_id": "c2",
                    "relationship": "CALLER_BEFORE_CALLEE_INTERNALS",
                },
                {
                    "need_id": "N1",
                    "predecessor_reference_id": "c2",
                    "successor_reference_id": "c3",
                    "relationship": "CALLEE_INTERNALS_BEFORE_POST_RETURN",
                },
            ],
            "call_return_spans": [],
            "atomic_references": [
                {
                    "need_id": "N1",
                    "reference_ids": ["c1", "c2", "c3"],
                }
            ],
            "rationale": "AUDITED",
        }
        coverage = need_coverage_review(
            artifact_id=artifact.artifact_id.value,
            need_to_candidate_keys={"N1": ["c1"]},
        )
        gateway = SequencedGateway(
            (
                {"candidates": [combined, callee], "limitations": []},
                initial_acceptance,
                coverage,
                initial_acceptance,
                invalid_sequence,
                initial_sequence,
                initial_sequence,
                initial_sequence,
                {
                    "retained_candidate_keys": ["c2"],
                    "replacements": [still_combined],
                    "limitations": [],
                },
                {
                    "retained_candidate_keys": ["c2"],
                    "replacements": [caller, post_return],
                    "limitations": [],
                },
                repaired_acceptance,
                coverage,
                repaired_acceptance,
                repaired_sequence,
                repaired_sequence,
                repaired_sequence,
            ),
            replay_audits=False,
        )
        request = self.request()
        request.requirement_plan = KnowledgeRequirementPlan(
            needs=(
                KnowledgeNeed(
                    need_id="N1",
                    question="What is the actual call and return order?",
                    required_kinds=(KnowledgeObjectKind.FACT,),
                    required_type_names=(),
                    required_terms=("call order",),
                    minimum_support_count=1,
                ),
            ),
        )

        with patch(
            "software_world_model.ai_infrastructure.agentic_knowledge_strategy."
            "_MAX_FACT_COVERAGE_ATTEMPTS",
            1,
        ):
            bundle = ModelReviewedKnowledgeBuilder(
                gateway,
                replace(self.configuration(), sequence_analysis_enabled=True),
            ).build(request=request, target=request.target, artifacts=(artifact,))

        self.assertEqual(len(bundle.facts), 3)
        self.assertEqual(gateway.calls, 16)
        proposal_state = json.loads(gateway.contexts[0].manifest.items[1].content)
        self.assertIn("call_return_candidate_policy", proposal_state)
        self.assertIn(
            "returned or bound value",
            proposal_state["call_return_candidate_policy"]["required_action"],
        )
        audit_state = json.loads(gateway.contexts[6].manifest.items[1].content)
        self.assertIn("independent_audit", audit_state)
        repair_state = json.loads(gateway.contexts[8].manifest.items[1].content)
        self.assertEqual(
            repair_state["grounding_rejected_candidate_keys"], ["c1"]
        )
        self.assertIn("at least two distinct candidate keys", repair_state["prior_review_findings"][0])
        self.assertEqual(
            repair_state["sequence_split_requirements"][0][
                "rejected_candidate_key"
            ],
            "c1",
        )
        split_retry_state = json.loads(
            gateway.contexts[9].manifest.items[1].content
        )
        self.assertEqual(
            split_retry_state["contract_repair"]["last_error"],
            "fact repair did not split a call-return boundary",
        )
        self.assertIn(
            "do not copy that wording into the invocation fact",
            split_retry_state["contract_repair"]["required_action"],
        )

    def test_individual_focus_audits_catch_a_span_missed_by_all_full_passes(self):
        artifact = self.artifact()
        combined = {
            "candidate_key": "c1",
            "need_ids": ["N1"],
            "artifact_id": artifact.artifact_id.value,
            "line_start": 1,
            "line_end": 2,
            "entity_type": "CODE_SYMBOL",
            "predicate": "CALLS",
            "statement": (
                "App.main calls App.value; if the result is valid, "
                "App.main returns it."
            ),
            "condition": None,
            "limitation": None,
        }
        callee = {
            **combined,
            "candidate_key": "c2",
            "line_start": 2,
            "line_end": 2,
            "statement": "App.value computes the declared value 3.",
        }
        acceptance = {
            "decision": "ACCEPT",
            "accepted_candidate_keys": ["c1", "c2"],
            "all_supported_objective_aspects_covered": True,
            "findings": [],
        }
        full_atomic = {
            "edges": [],
            "call_return_spans": [],
            "atomic_references": [
                {"need_id": "N1", "reference_ids": ["c1", "c2"]}
            ],
            "rationale": "AUDITED",
        }
        focused_span = {
            "edges": [],
            "call_return_spans": [
                {
                    "need_id": "N1",
                    "combined_reference_id": "c1",
                    "callee_internal_reference_id": "c2",
                    "callee_subject_fragment": "App.value",
                    "invocation_fragment": "calls App.value",
                    "temporal_connector_fragment": "; if the result is valid,",
                    "post_return_fragment": "App.main returns it",
                }
            ],
            "atomic_references": [],
            "rationale": "AUDITED",
        }
        focused_callee_atomic = {
            "edges": [],
            "call_return_spans": [],
            "atomic_references": [
                {"need_id": "N1", "reference_ids": ["c2"]}
            ],
            "rationale": "AUDITED",
        }
        gateway = SequencedGateway(
            (
                {"candidates": [combined, callee], "limitations": []},
                acceptance,
                need_coverage_review(
                    artifact_id=artifact.artifact_id.value,
                    need_to_candidate_keys={"N1": ["c1"]},
                ),
                acceptance,
                full_atomic,
                full_atomic,
                full_atomic,
                focused_span,
                focused_span,
                focused_callee_atomic,
                focused_callee_atomic,
                DomainError(
                    ErrorCode.CONTROL_STATE_DENIED,
                    "stop after observing the requested sequence repair",
                ),
            ),
            replay_audits=False,
        )
        request = self.request()
        request.requirement_plan = KnowledgeRequirementPlan(
            needs=(
                KnowledgeNeed(
                    need_id="N1",
                    question="What is the actual call and return order?",
                    required_kinds=(KnowledgeObjectKind.FACT,),
                    required_type_names=(),
                    required_terms=("call order",),
                    minimum_support_count=1,
                ),
            ),
        )

        with (
            patch(
                "software_world_model.ai_infrastructure."
                "agentic_knowledge_strategy._SEQUENCE_FOCUSED_AUDIT_THRESHOLD",
                1,
            ),
            self.assertRaises(DomainError) as raised,
        ):
            ModelReviewedKnowledgeBuilder(
                gateway,
                replace(self.configuration(), sequence_analysis_enabled=True),
            ).build(request=request, target=request.target, artifacts=(artifact,))

        self.assertEqual(
            raised.exception.message,
            "stop after observing the requested sequence repair",
        )
        self.assertEqual(gateway.calls, 12)
        first_focus = json.loads(gateway.contexts[7].manifest.items[1].content)
        self.assertEqual(
            first_focus["call_return_focus"]["focus_reference_ids"],
            ["c1"],
        )
        self.assertIn(
            "exactly once as atomic",
            first_focus["call_return_focus"]["required_action"],
        )
        self.assertIn(
            "does not need to contain a word equivalent to",
            gateway.contexts[7].manifest.items[0].content,
        )
        self.assertIn(
            "fixed semantic order",
            gateway.contexts[7].manifest.items[0].content,
        )
        repair_state = json.loads(gateway.contexts[11].manifest.items[1].content)
        self.assertEqual(
            repair_state["sequence_split_requirements"][0][
                "rejected_candidate_key"
            ],
            "c1",
        )

    def test_sequence_split_repair_accepts_source_aligned_semantic_sides(self):
        artifact = self.artifact()
        combined = {
            "candidate_key": "c12",
            "need_ids": ["N1"],
            "artifact_id": artifact.artifact_id.value,
            "line_start": 1,
            "line_end": 2,
            "entity_type": "CODE_SYMBOL",
            "predicate": "CALLS",
            "statement": (
                "App.main 在 App.value 后检查结果，若结果有效则返回。"
            ),
            "condition": None,
            "limitation": None,
        }
        invocation = {
            **combined,
            "candidate_key": "c14",
            "line_end": 1,
            "statement": "App.main 调用 App.value()。",
        }
        post_return = {
            **combined,
            "candidate_key": "c15",
            "line_start": 2,
            "predicate": "HAS_VALUE",
            "statement": "App.main 检查结果，若结果有效则返回。",
        }

        _validate_sequence_split_repair(
            [invocation, post_return],
            {
                "c12": (
                    (
                        "N1",
                        "c11",
                        "App.value 后",
                        "若结果有效则返回",
                    ),
                )
            },
            replacement_candidate_keys=frozenset({"c14", "c15"}),
            prior_candidates=(combined,),
        )

    def test_sequence_split_repair_rejects_one_source_aligned_side(self):
        artifact = self.artifact()
        combined = {
            "candidate_key": "c1",
            "need_ids": ["N1"],
            "artifact_id": artifact.artifact_id.value,
            "line_start": 1,
            "line_end": 2,
            "entity_type": "CODE_SYMBOL",
            "predicate": "CALLS",
            "statement": "App.main calls App.value and then returns its result.",
            "condition": None,
            "limitation": None,
        }
        invocation_only = {
            **combined,
            "candidate_key": "c3",
            "line_end": 1,
            "statement": "App.main calls App.value.",
        }

        with self.assertRaises(DomainError) as raised:
            _validate_sequence_split_repair(
                [invocation_only],
                {
                    "c1": (
                        (
                            "N1",
                            "c2",
                            "calls App.value",
                            "returns its result",
                        ),
                    )
                },
                replacement_candidate_keys=frozenset({"c3"}),
                prior_candidates=(combined,),
            )

        self.assertEqual(
            raised.exception.message,
            "fact repair did not split a call-return boundary",
        )

    def test_fact_sequence_ignores_unsupported_span_claims(self):
        artifact = self.artifact()
        combined = {
            "candidate_key": "c1",
            "need_ids": ["N1"],
            "artifact_id": artifact.artifact_id.value,
            "line_start": 1,
            "line_end": 2,
            "entity_type": "CODE_SYMBOL",
            "predicate": "CALLS",
            "statement": "App.main calls App.value and then returns its result.",
            "condition": None,
            "limitation": None,
        }
        callee = {
            **combined,
            "candidate_key": "c2",
            "line_start": 2,
            "line_end": 2,
            "statement": "App.value computes the declared value 3.",
        }
        acceptance = {
            "decision": "ACCEPT",
            "accepted_candidate_keys": ["c1", "c2"],
            "all_supported_objective_aspects_covered": True,
            "findings": [],
        }
        invalid_sequence = {
            "orders": [
                {"need_id": "N1", "reference_ids": ["c1", "c2"]}
            ],
            "edges": [],
            "call_return_spans": [
                {
                    "need_id": "N1",
                    "combined_reference_id": "c1",
                    "callee_internal_reference_id": "c2",
                    "callee_subject_fragment": "App.value",
                    "invocation_fragment": "App.value()",
                    "temporal_connector_fragment": "then",
                    "post_return_fragment": "return result;",
                }
            ],
            "atomic_references": [
                {"need_id": "N1", "reference_ids": ["c1", "c2"]}
            ],
            "rationale": "AUDITED",
        }
        responses = [
            {"candidates": [combined, callee], "limitations": []},
            acceptance,
            need_coverage_review(
                artifact_id=artifact.artifact_id.value,
                need_to_candidate_keys={"N1": ["c1"]},
            ),
            acceptance,
            invalid_sequence,
            invalid_sequence,
            invalid_sequence,
        ]
        gateway = SequencedGateway(tuple(responses), replay_audits=False)
        request = self.request()
        request.requirement_plan = KnowledgeRequirementPlan(
            needs=(
                KnowledgeNeed(
                    need_id="N1",
                    question="What is the actual call and return order?",
                    required_kinds=(KnowledgeObjectKind.FACT,),
                    required_type_names=(),
                    required_terms=("call order",),
                    minimum_support_count=1,
                ),
            ),
        )

        bundle = ModelReviewedKnowledgeBuilder(
            gateway,
            replace(self.configuration(), sequence_analysis_enabled=True),
        ).build(request=request, target=request.target, artifacts=(artifact,))

        self.assertEqual(len(bundle.facts), 2)
        self.assertEqual(gateway.calls, 7)
        audit_state = json.loads(gateway.contexts[5].manifest.items[1].content)
        self.assertIn("independent_audit", audit_state)
        self.assertNotIn("contract_repair", audit_state)

    def test_fact_sequence_adjudicates_one_false_parallel_dispatch_span(self):
        artifact = self.artifact()
        parallel_dispatch = {
            "candidate_key": "c1",
            "need_ids": ["N1"],
            "artifact_id": artifact.artifact_id.value,
            "line_start": 1,
            "line_end": 2,
            "entity_type": "CODE_SYMBOL",
            "predicate": "CALLS",
            "statement": (
                "App.dispatch sends declared value 3 to App.handle and backup "
                "value to App.fallback."
            ),
            "condition": None,
            "limitation": None,
        }
        callee = {
            **parallel_dispatch,
            "candidate_key": "c2",
            "statement": "App.handle processes the declared value 3.",
        }
        acceptance = {
            "decision": "ACCEPT",
            "accepted_candidate_keys": ["c1", "c2"],
            "all_supported_objective_aspects_covered": True,
            "findings": [],
        }
        atomic_sequence = {
            "edges": [],
            "call_return_spans": [],
            "atomic_references": [
                {"need_id": "N1", "reference_ids": ["c1", "c2"]}
            ],
            "rationale": "AUDITED",
        }
        false_parallel_span = {
            "edges": [],
            "call_return_spans": [
                {
                    "need_id": "N1",
                    "combined_reference_id": "c1",
                    "callee_internal_reference_id": "c2",
                    "callee_subject_fragment": (
                        "App.handle processes the declared value 3"
                    ),
                    "invocation_fragment": "sends declared value 3 to App.handle",
                    "temporal_connector_fragment": "and",
                    "post_return_fragment": "backup value to App.fallback",
                }
            ],
            "atomic_references": [
                {"need_id": "N1", "reference_ids": ["c2"]}
            ],
            "rationale": "AUDITED",
        }
        adjudicated_atomic_sequence = {
            **atomic_sequence,
            "atomic_references": [
                {"need_id": "N1", "reference_ids": ["c1"]}
            ],
        }
        gateway = SequencedGateway(
            (
                {"candidates": [parallel_dispatch, callee], "limitations": []},
                acceptance,
                need_coverage_review(
                    artifact_id=artifact.artifact_id.value,
                    need_to_candidate_keys={"N1": ["c1", "c2"]},
                ),
                acceptance,
                atomic_sequence,
                atomic_sequence,
                false_parallel_span,
                adjudicated_atomic_sequence,
            ),
            replay_audits=False,
        )
        request = self.request()
        request.requirement_plan = KnowledgeRequirementPlan(
            needs=(
                KnowledgeNeed(
                    need_id="N1",
                    question="How does the dispatcher route the two alternatives?",
                    required_kinds=(KnowledgeObjectKind.FACT,),
                    required_type_names=(),
                    required_terms=("dispatch",),
                    minimum_support_count=1,
                ),
            )
        )

        bundle = ModelReviewedKnowledgeBuilder(
            gateway,
            replace(self.configuration(), sequence_analysis_enabled=True),
        ).build(request=request, target=request.target, artifacts=(artifact,))

        self.assertEqual(len(bundle.facts), 2)
        self.assertEqual(gateway.calls, 8)
        adjudication_state = json.loads(
            gateway.contexts[7].manifest.items[1].content
        )
        self.assertIn("disputed_span_adjudication", adjudication_state)
        self.assertIn(
            "sibling overloads",
            adjudication_state["disputed_span_adjudication"][
                "required_action"
            ],
        )
        self.assertIn(
            "parallel visitor dispatches",
            gateway.contexts[7].manifest.items[0].content,
        )
        self.assertIn(
            "does not assert that this reference performs the invocation",
            gateway.contexts[7].manifest.items[0].content,
        )

    def test_fact_contract_repair_preserves_invalid_output_for_syntax_repair(self):
        artifact = self.artifact()
        incomplete = {
            "candidate_key": "app-value",
            "need_ids": ["OBJECTIVE"],
            "artifact_id": artifact.artifact_id.value,
            "line_start": 2,
            "line_end": 2,
            "entity_type": "CODE_SYMBOL",
            "predicate": "HAS_VALUE",
            "statement": "App.value is declared.",
            "condition": None,
            "limitation": None,
        }
        complete = {
            **incomplete,
            "statement": "App.value is initialized to 3.",
        }
        repair = {
            "retained_candidate_keys": [],
            "replacements": [complete],
            "limitations": [],
        }
        malformed = InvalidStructuredOutput(
            json.dumps(repair).replace(
                '"condition": null, "limitation"',
                '"condition": null "limitation"',
            )
        )
        finding = "The initializer value is omitted."
        gateway = SequencedGateway(
            (
                {"candidates": [incomplete], "limitations": []},
                {
                    "decision": "REJECT",
                    "accepted_candidate_keys": ["app-value"],
                    "all_supported_objective_aspects_covered": False,
                    "findings": [finding],
                },
                malformed,
                repair,
                {
                    "decision": "ACCEPT",
                    "accepted_candidate_keys": ["app-value"],
                    "all_supported_objective_aspects_covered": True,
                    "findings": [],
                },
            )
        )

        bundle = ModelReviewedKnowledgeBuilder(
            gateway, self.configuration()
        ).build(
            request=self.request(), target=self.request().target, artifacts=(artifact,)
        )

        self.assertEqual(bundle.facts[0].object_value, complete["statement"])
        repair_state = json.loads(gateway.contexts[3].manifest.items[1].content)
        self.assertEqual(
            repair_state["contract_repair"]["last_error_details"][
                "invalid_output_text"
            ],
            malformed,
        )
        self.assertIn(
            "Preserve every complete candidate",
            repair_state["contract_repair"]["required_action"],
        )
        self.assertIn(
            "36 words",
            repair_state["contract_repair"]["required_action"],
        )
        self.assertEqual(repair_state["prior_review_findings"], [finding])

    def test_sufficiency_reviewer_selects_only_exact_formal_references(self):
        requirement, need, read_set, record = self.formal_need_state()
        gateway = FakeGateway(
            {
                "status": "SATISFIED",
                "supporting_reference_ids": [record.object_id.value],
                "gap": None,
                "counterexample_reference_ids": [],
                "conflict_reference_ids": [],
                "unknowns": [],
                "limitations": [],
                "rationale": "The formal proposition directly answers the Need.",
            }
        )

        decision = ModelNeedSufficiencyEvaluator(
            gateway, self.configuration()
        ).evaluate(requirement=requirement, need=need, read_set=read_set)

        self.assertEqual(decision.status, NeedStatus.SATISFIED)
        self.assertEqual(decision.supporting_references, (record.object_id,))
        state = json.loads(gateway.contexts[0].manifest.items[1].content)
        self.assertEqual(state["read_set"]["records"][0]["text"], record.text)
        self.assertNotIn("artifact", state)
        instruction = gateway.contexts[0].manifest.items[0].content
        self.assertIn(
            "Do not add requirements the user did not ask for",
            instruction,
        )
        self.assertIn(
            "every material subject, relationship, condition, alternative",
            instruction,
        )
        self.assertIn(
            "without adding unstated conclusions",
            instruction,
        )
        self.assertIn(
            "preserve that boundary in the returned limitations array",
            instruction,
        )
        self.assertIn(
            "Records may be combined when their literal statements establish every necessary relationship",
            instruction,
        )
        self.assertIn(
            "select the smallest non-redundant set",
            instruction,
        )
        self.assertIn(
            "Never trade completeness for brevity",
            instruction,
        )
        self.assertIn(
            "reconstruct the initial state",
            instruction,
        )
        self.assertIn(
            "SATISFIED cannot use a limitation to admit",
            instruction,
        )
        self.assertIn(
            "may be displayed verbatim to the end user",
            instruction,
        )
        self.assertIn(
            "never mention internal Needs, formal records, support proofs",
            instruction,
        )
        self.assertIn(
            "planner-generated Need question is internal",
            instruction,
        )
        self.assertIn(
            "keep rationale to at most two concise sentences",
            instruction,
        )
        self.assertIn(
            "never enumerate, quote, or restate the selected records",
            instruction,
        )

    def test_sufficiency_reviewer_repairs_unbounded_rationale(self):
        requirement, need, read_set, record = self.formal_need_state()
        verbose = {
            "status": "SATISFIED",
            "supporting_reference_ids": [record.object_id.value],
            "gap": None,
            "counterexample_reference_ids": [],
            "conflict_reference_ids": [],
            "unknowns": [],
            "limitations": [],
            "rationale": "x" * 241,
        }
        concise = {
            **verbose,
            "rationale": "The selected fact directly answers the question.",
        }
        gateway = SequencedGateway((verbose, concise))

        decision = ModelNeedSufficiencyEvaluator(
            gateway, self.configuration()
        ).evaluate(requirement=requirement, need=need, read_set=read_set)

        self.assertEqual(decision.status, NeedStatus.SATISFIED)
        self.assertEqual(gateway.calls, 4)
        repair = json.loads(gateway.contexts[1].manifest.items[-1].content)
        self.assertEqual(
            repair["last_error_details"]["maximum_characters"], 240
        )
        self.assertIn("do not enumerate", repair["required_action"])

    def test_sufficiency_omits_same_evidence_fact_strictly_contained_by_another(self):
        requirement, need, read_set, shorter = self.formal_need_state()
        longer_text = shorter.text.rstrip(".") + ", including the declared boundary."
        longer = replace(
            shorter,
            object_id=StableId(
                "knowledge_fact_00000000000000000000000000000002"
            ),
            object_digest=digest_of(longer_text),
            text=longer_text,
        )
        read_set = replace(
            read_set,
            records=(shorter, longer),
            digest=digest_of(
                (
                    shorter.object_id.value,
                    shorter.object_digest.value,
                    longer.object_id.value,
                    longer.object_digest.value,
                )
            ),
        )
        gateway = FakeGateway(
            {
                "status": "SATISFIED",
                "supporting_reference_ids": [
                    shorter.object_id.value,
                    longer.object_id.value,
                ],
                "gap": None,
                "counterexample_reference_ids": [],
                "conflict_reference_ids": [],
                "unknowns": [],
                "limitations": [],
                "rationale": "The longer fact contains the complete proposition.",
            }
        )

        decision = ModelNeedSufficiencyEvaluator(
            gateway, self.configuration()
        ).evaluate(requirement=requirement, need=need, read_set=read_set)

        self.assertEqual(decision.supporting_references, (longer.object_id,))

    def test_sufficiency_minimality_audit_removes_peripheral_support(self):
        requirement, need, read_set, required = self.formal_need_state()
        peripheral = replace(
            required,
            object_id=StableId(
                "knowledge_fact_00000000000000000000000000000002"
            ),
            object_digest=digest_of("The logger is configured separately."),
            text="The logger is configured separately.",
            support_references=(
                StableId("evidence_00000000000000000000000000000002"),
            ),
        )
        read_set = replace(
            read_set,
            records=(required, peripheral),
            digest=digest_of(
                (
                    required.object_id.value,
                    required.object_digest.value,
                    peripheral.object_id.value,
                    peripheral.object_digest.value,
                )
            ),
        )
        broad = {
            "status": "SATISFIED",
            "supporting_reference_ids": [
                required.object_id.value,
                peripheral.object_id.value,
            ],
            "gap": None,
            "counterexample_reference_ids": [],
            "conflict_reference_ids": [],
            "unknowns": [],
            "limitations": [],
            "rationale": "Both records were initially considered relevant.",
        }
        minimal = {
            **broad,
            "supporting_reference_ids": [required.object_id.value],
            "rationale": "The first record alone completely answers the question.",
        }
        gateway = SequencedGateway((broad, minimal))

        decision = ModelNeedSufficiencyEvaluator(
            gateway, self.configuration()
        ).evaluate(requirement=requirement, need=need, read_set=read_set)

        self.assertEqual(decision.supporting_references, (required.object_id,))
        self.assertEqual(gateway.calls, 4)
        audit_state = json.loads(gateway.contexts[1].manifest.items[1].content)
        self.assertEqual(
            audit_state["minimality_audit"][
                "prior_supporting_reference_ids"
            ],
            [required.object_id.value, peripheral.object_id.value],
        )
        self.assertIn(
            "record-by-record deletion test",
            audit_state["minimality_audit"]["required_action"],
        )

    def test_sufficiency_completeness_audits_restore_missing_requested_support(self):
        requirement, need, read_set, first = self.formal_need_state()
        second = replace(
            first,
            object_id=StableId(
                "knowledge_fact_00000000000000000000000000000002"
            ),
            object_digest=digest_of(
                "App.start invokes App.parse to produce the requested value."
            ),
            text="App.start invokes App.parse to produce the requested value.",
            support_references=(
                StableId("evidence_00000000000000000000000000000002"),
            ),
        )
        read_set = replace(
            read_set,
            records=(first, second),
            digest=digest_of(
                (
                    first.object_id.value,
                    first.object_digest.value,
                    second.object_id.value,
                    second.object_digest.value,
                )
            ),
        )

        def satisfied(*records: FormalKnowledgeRecord) -> dict[str, object]:
            return {
                "status": "SATISFIED",
                "supporting_reference_ids": [
                    record.object_id.value for record in records
                ],
                "gap": None,
                "counterexample_reference_ids": [],
                "conflict_reference_ids": [],
                "unknowns": [],
                "limitations": [],
                "rationale": "The literal selected facts answer the request.",
            }

        gateway = SequencedGateway(
            (
                satisfied(first),
                satisfied(first, second),
                satisfied(first, second),
            ),
            replay_audits=False,
        )

        decision = ModelNeedSufficiencyEvaluator(
            gateway, self.configuration()
        ).evaluate(requirement=requirement, need=need, read_set=read_set)

        self.assertEqual(
            decision.supporting_references,
            (first.object_id, second.object_id),
        )
        self.assertEqual(gateway.calls, 3)
        first_audit = json.loads(gateway.contexts[1].manifest.items[1].content)
        self.assertEqual(
            first_audit["completeness_audit"][
                "prior_supporting_reference_ids"
            ],
            [first.object_id.value],
        )
        self.assertIn(
            "INFERENCE covers only its proposition",
            first_audit["completeness_audit"]["required_action"],
        )
        self.assertEqual(
            gateway.contexts[1].manifest.execution_stage,
            "NEED_SUFFICIENCY_COMPLETENESS_AUDIT",
        )

    def test_sufficiency_minimality_audit_repairs_locally_with_unique_ref(self):
        requirement, need, read_set, required = self.formal_need_state()
        second = replace(
            required,
            object_id=StableId(
                "knowledge_fact_00000000000000000000000000000002"
            ),
            object_digest=digest_of("The second fact adds a distinct result."),
            text="The second fact adds a distinct result.",
            support_references=(
                StableId("evidence_00000000000000000000000000000002"),
            ),
        )
        third = replace(
            required,
            object_id=StableId(
                "knowledge_fact_00000000000000000000000000000003"
            ),
            object_digest=digest_of("The third fact is peripheral."),
            text="The third fact is peripheral.",
            support_references=(
                StableId("evidence_00000000000000000000000000000003"),
            ),
        )
        read_set = replace(
            read_set,
            records=(required, second, third),
            digest=digest_of(
                tuple(
                    (item.object_id.value, item.object_digest.value)
                    for item in (required, second, third)
                )
            ),
        )

        def satisfied(*records: FormalKnowledgeRecord) -> dict[str, object]:
            return {
                "status": "SATISFIED",
                "supporting_reference_ids": [
                    item.object_id.value for item in records
                ],
                "gap": None,
                "counterexample_reference_ids": [],
                "conflict_reference_ids": [],
                "unknowns": [],
                "limitations": [],
                "rationale": "The selected facts answer the question.",
            }

        invalid_audit = {
            **satisfied(required, second, third),
            "status": "GAP",
            "supporting_reference_ids": [],
            "gap": "The audit incorrectly changed the decision.",
        }
        gateway = SequencedGateway(
            (
                satisfied(required, second, third),
                invalid_audit,
                satisfied(required, second),
            )
        )

        decision = ModelNeedSufficiencyEvaluator(
            gateway, self.configuration()
        ).evaluate(requirement=requirement, need=need, read_set=read_set)

        self.assertEqual(
            decision.supporting_references,
            (required.object_id, second.object_id),
        )
        audit_refs = [
            context.execution_envelope_ref
            for context in gateway.contexts
            if context.manifest.execution_stage
            == "NEED_SUFFICIENCY_MINIMALITY_AUDIT"
        ]
        self.assertEqual(len(audit_refs), 2)
        self.assertNotEqual(audit_refs[0], audit_refs[1])
        self.assertTrue(audit_refs[0].endswith(":sufficiency:minimality-audit"))
        self.assertTrue(
            audit_refs[1].endswith(
                ":sufficiency:minimality-audit:contract-retry:2"
            )
        )
        repair_state = json.loads(gateway.contexts[2].manifest.items[1].content)
        self.assertEqual(
            repair_state["contract_repair"][
                "allowed_prior_supporting_reference_ids"
            ],
            [
                required.object_id.value,
                second.object_id.value,
                third.object_id.value,
            ],
        )

    def test_sufficiency_reviewer_follows_original_request_language(self):
        requirement, need, read_set, record = self.formal_need_state()
        need = replace(need, question="What initial value does source declare for App.value?")
        requirement = KnowledgeRequirement.create(
            requirement_id=requirement.requirement_id,
            revision=requirement.revision,
            fidelity=requirement.fidelity,
            original_request="源码为 App.value 声明了什么初始值？",
            needs=(need,),
        )
        read_set = replace(read_set, need_id=need.need_id)
        english = {
            "status": "SATISFIED",
            "supporting_reference_ids": [record.object_id.value],
            "gap": None,
            "counterexample_reference_ids": [],
            "conflict_reference_ids": [],
            "unknowns": [],
            "limitations": [],
            "rationale": "The formal proposition directly answers the Need.",
        }
        chinese = {
            **english,
            "limitations": [],
            "rationale": "该正式事实直接回答了这个问题。",
        }
        gateway = SequencedGateway((english, chinese))

        decision = ModelNeedSufficiencyEvaluator(
            gateway, self.configuration()
        ).evaluate(requirement=requirement, need=need, read_set=read_set)

        self.assertEqual(decision.limitations, tuple(chinese["limitations"]))
        self.assertEqual(gateway.calls, 4)
        repair = json.loads(gateway.contexts[1].manifest.items[-1].content)
        self.assertEqual(
            repair["last_error_details"]["required_response_script"], "CJK"
        )
        self.assertEqual(
            set(repair["last_error_details"]["invalid_language_fields"]),
            {"rationale"},
        )
        self.assertIn("same natural language", repair["required_action"])

    def test_sufficiency_language_allows_source_only_limitation_expression(self):
        requirement, need, read_set, record = self.formal_need_state()
        need = replace(need, question="源码声明了什么初始值？")
        requirement = KnowledgeRequirement.create(
            requirement_id=requirement.requirement_id,
            revision=requirement.revision,
            fidelity=requirement.fidelity,
            original_request=need.question,
            needs=(need,),
        )
        record_text = (
            "App.value is initialized to 3. Condition: docxCount >= 1"
        )
        record = replace(
            record,
            text=record_text,
            object_digest=digest_of(record_text),
        )
        read_set = replace(
            read_set,
            need_id=need.need_id,
            records=(record,),
            digest=digest_of(
                {
                    "need_id": need.need_id,
                    "records": (
                        (record.object_id.value, record.object_digest.value),
                    ),
                }
            ),
        )
        gateway = FakeGateway(
            {
                "status": "SATISFIED",
                "supporting_reference_ids": [record.object_id.value],
                "gap": None,
                "counterexample_reference_ids": [],
                "conflict_reference_ids": [],
                "unknowns": [],
                "limitations": ["docxCount >= 1"],
                "rationale": "该正式事实直接回答了这个问题。",
            }
        )

        decision = ModelNeedSufficiencyEvaluator(
            gateway, self.configuration()
        ).evaluate(requirement=requirement, need=need, read_set=read_set)

        self.assertEqual(decision.limitations, ("docxCount >= 1",))
        self.assertEqual(gateway.calls, 3)
        self.assertIn(
            "source-only identifier or expression",
            gateway.contexts[0].manifest.items[0].content,
        )

    def test_sufficiency_reviewer_cannot_use_entity_metadata_as_support(self):
        requirement, need, read_set, record = self.formal_need_state()
        entity = FormalKnowledgeRecord(
            kind=KnowledgeObjectKind.ENTITY,
            object_id=StableId(
                "knowledge_entity_00000000000000000000000000000001"
            ),
            object_digest=digest_of("internal source identity"),
            type_name="SOURCE_FILE",
            text="sha256:internal:src/App.java src/App.java",
            context_digest=record.context_digest,
            support_references=record.support_references,
        )
        expanded_read_set = KnowledgeReadSet(
            need_id=read_set.need_id,
            records=(entity, record),
            query_digest=read_set.query_digest,
            complete=True,
            digest=digest_of((entity.object_id.value, record.object_id.value)),
        )
        invalid = {
            "status": "SATISFIED",
            "supporting_reference_ids": [entity.object_id.value],
            "gap": None,
            "counterexample_reference_ids": [],
            "conflict_reference_ids": [],
            "unknowns": [],
            "limitations": [],
            "rationale": "The entity identifies a file.",
        }
        corrected = {
            **invalid,
            "supporting_reference_ids": [record.object_id.value],
            "rationale": "The fact directly answers the Need.",
        }
        gateway = SequencedGateway((invalid, corrected))

        decision = ModelNeedSufficiencyEvaluator(
            gateway, self.configuration()
        ).evaluate(
            requirement=requirement,
            need=need,
            read_set=expanded_read_set,
        )

        self.assertEqual(decision.supporting_references, (record.object_id,))
        repair = json.loads(gateway.contexts[1].manifest.items[-1].content)
        self.assertEqual(
            repair["allowed_reference_ids"], [record.object_id.value]
        )

    def test_sufficiency_reviewer_cannot_reference_unread_knowledge(self):
        requirement, need, read_set, _ = self.formal_need_state()
        gateway = FakeGateway(
            {
                "status": "SATISFIED",
                "supporting_reference_ids": [
                    "knowledge_fact_ffffffffffffffffffffffffffffffff"
                ],
                "gap": None,
                "counterexample_reference_ids": [],
                "conflict_reference_ids": [],
                "unknowns": [],
                "limitations": [],
                "rationale": "Unsupported reference.",
            }
        )

        with self.assertRaises(DomainError) as raised:
            ModelNeedSufficiencyEvaluator(
                gateway, self.configuration()
            ).evaluate(requirement=requirement, need=need, read_set=read_set)

        self.assertEqual(raised.exception.code, ErrorCode.CONTROL_STATE_DENIED)
        self.assertEqual(gateway.calls, 3)

    def test_sufficiency_reviewer_repairs_a_mistyped_formal_reference(self):
        requirement, need, read_set, record = self.formal_need_state()
        invalid = {
            "status": "SATISFIED",
            "supporting_reference_ids": [
                "knowledge_fact_ffffffffffffffffffffffffffffffff"
            ],
            "gap": None,
            "counterexample_reference_ids": [],
            "conflict_reference_ids": [],
            "unknowns": [],
            "limitations": [],
            "rationale": "The identifier was copied incorrectly.",
        }
        corrected = {
            **invalid,
            "supporting_reference_ids": [record.object_id.value],
            "rationale": "The exact supplied record directly supports the Need.",
        }
        gateway = SequencedGateway((invalid, corrected))

        decision = ModelNeedSufficiencyEvaluator(
            gateway, self.configuration()
        ).evaluate(requirement=requirement, need=need, read_set=read_set)

        self.assertEqual(decision.supporting_references, (record.object_id,))
        self.assertEqual(gateway.calls, 4)
        repair = gateway.contexts[1].manifest.items[-1]
        self.assertEqual(
            repair.schema_ref, "need-sufficiency-contract-repair@1"
        )
        repair_state = json.loads(repair.content)
        self.assertEqual(
            repair_state["allowed_reference_ids"], [record.object_id.value]
        )

    def test_sufficiency_reviewer_repairs_a_duplicate_formal_reference(self):
        requirement, need, read_set, record = self.formal_need_state()
        duplicate = {
            "status": "SATISFIED",
            "supporting_reference_ids": [
                record.object_id.value,
                record.object_id.value,
            ],
            "gap": None,
            "counterexample_reference_ids": [],
            "conflict_reference_ids": [],
            "unknowns": [],
            "limitations": [],
            "rationale": "The exact supplied record directly supports the Need.",
        }
        corrected = {
            **duplicate,
            "supporting_reference_ids": [record.object_id.value],
        }
        gateway = SequencedGateway((duplicate, corrected))

        decision = ModelNeedSufficiencyEvaluator(
            gateway, self.configuration()
        ).evaluate(requirement=requirement, need=need, read_set=read_set)

        self.assertEqual(decision.supporting_references, (record.object_id,))
        self.assertEqual(gateway.calls, 4)
        repair_state = json.loads(
            gateway.contexts[1].manifest.items[-1].content
        )
        self.assertEqual(
            repair_state["last_error_details"]["field"],
            "supporting_reference_ids",
        )
        self.assertEqual(
            repair_state["last_error_details"]["duplicate_reference_ids"],
            [record.object_id.value],
        )
        self.assertIn("at most once", repair_state["required_action"])

    def test_sufficiency_reviewer_explains_unsupported_limitation_repair(self):
        requirement, need, read_set, record = self.formal_need_state()
        unsupported = {
            "status": "SATISFIED",
            "supporting_reference_ids": [record.object_id.value],
            "gap": None,
            "counterexample_reference_ids": [],
            "conflict_reference_ids": [],
            "unknowns": [],
            "limitations": ["The source does not prove runtime behavior."],
            "rationale": "The exact supplied record directly supports the Need.",
        }
        corrected = {**unsupported, "limitations": []}
        gateway = SequencedGateway((unsupported, corrected))

        decision = ModelNeedSufficiencyEvaluator(
            gateway, self.configuration()
        ).evaluate(requirement=requirement, need=need, read_set=read_set)

        self.assertEqual(decision.limitations, ())
        repair_state = json.loads(
            gateway.contexts[1].manifest.items[-1].content
        )
        self.assertEqual(
            repair_state["last_error_details"]["unsupported_limitations"],
            ["The source does not prove runtime behavior."],
        )
        self.assertIn(
            "exact contiguous substring", repair_state["required_action"]
        )

    def test_sufficiency_reviewer_retries_contradictory_status_and_support(self):
        requirement, need, read_set, record = self.formal_need_state()
        contradictory = {
            "status": "GAP",
            "supporting_reference_ids": [record.object_id.value],
            "gap": "The source does not establish a runtime guarantee.",
            "counterexample_reference_ids": [],
            "conflict_reference_ids": [],
            "unknowns": [],
            "limitations": [],
            "rationale": "The formal record is relevant but not sufficient.",
        }
        corrected = {
            **contradictory,
            "supporting_reference_ids": [],
        }
        gateway = SequencedGateway((contradictory, corrected))

        decision = ModelNeedSufficiencyEvaluator(
            gateway, self.configuration()
        ).evaluate(requirement=requirement, need=need, read_set=read_set)

        self.assertEqual(decision.status, NeedStatus.GAP)
        self.assertEqual(decision.supporting_references, ())
        self.assertEqual(gateway.calls, 2)
        self.assertTrue(
            gateway.contexts[1].execution_envelope_ref.endswith(
                ":contract-retry:2"
            )
        )

    def test_sufficiency_reviewer_requires_semantic_not_lexical_matching(self):
        requirement, need, read_set, record = self.formal_need_state()
        gateway = FakeGateway(
            {
                "status": "SATISFIED",
                "supporting_reference_ids": [record.object_id.value],
                "gap": None,
                "counterexample_reference_ids": [],
                "conflict_reference_ids": [],
                "unknowns": [],
                "limitations": [],
                "rationale": "The formal record states the same behavior in source-native terms.",
            }
        )

        ModelNeedSufficiencyEvaluator(
            gateway, self.configuration()
        ).evaluate(requirement=requirement, need=need, read_set=read_set)

        prompt = gateway.contexts[0].manifest.items[0].content
        self.assertIn("Judge semantic meaning rather than exact vocabulary", prompt)
        self.assertIn("do not return GAP merely because", prompt)
        self.assertIn("semantic reading, not an external fact", prompt)
        self.assertIn("compare every limitation literally with every requested result", prompt)
        self.assertIn("Any fallback token such as", prompt)
        self.assertIn("Final nested-scope audit", prompt)
        self.assertIn("Do not add an exhaustive-catalog requirement", prompt)
        self.assertIn(
            "A record that only names the selected result",
            prompt,
        )
        self.assertIn("adjacent or peripheral facts", prompt)
        self.assertIn(
            "Do not recursively require the value's later execution lifecycle",
            prompt,
        )
        self.assertIn(
            "Do not generalize from one variant to the whole category",
            prompt,
        )

    def test_sufficiency_reviewer_reconsiders_gap_against_linked_reviewed_fact(self):
        requirement, need, read_set, record = self.formal_need_state()
        linked = replace(record, reviewed_need_ids=(need.need_id,))
        linked_read_set = replace(read_set, records=(linked,))
        gap = {
            "status": "GAP",
            "supporting_reference_ids": [],
            "gap": "No supplied record answers the Need.",
            "counterexample_reference_ids": [],
            "conflict_reference_ids": [],
            "unknowns": [],
            "limitations": [],
            "rationale": "The record was overlooked.",
        }
        satisfied = {
            **gap,
            "status": "SATISFIED",
            "supporting_reference_ids": [linked.object_id.value],
            "gap": None,
            "rationale": "The independently reviewed linked fact directly answers the Need.",
        }
        gateway = SequencedGateway((gap, satisfied))

        decision = ModelNeedSufficiencyEvaluator(
            gateway, self.configuration()
        ).evaluate(
            requirement=requirement,
            need=need,
            read_set=linked_read_set,
        )

        self.assertEqual(decision.status, NeedStatus.SATISFIED)
        self.assertEqual(decision.supporting_references, (linked.object_id,))
        self.assertEqual(gateway.calls, 4)
        retry_state = json.loads(
            gateway.contexts[1].manifest.items[-1].content
        )
        self.assertEqual(
            retry_state["last_error_details"][
                "reviewed_linked_reference_ids"
            ],
            [linked.object_id.value],
        )
        prompt = gateway.contexts[0].manifest.items[0].content
        self.assertIn(
            "do not recursively require the internal algorithm",
            prompt,
        )

    def test_sufficiency_retries_when_satisfied_omits_linked_inference(self):
        requirement, need, read_set, fact = self.formal_need_state()
        need = replace(
            need,
            required_kinds=(
                KnowledgeObjectKind.FACT,
                KnowledgeObjectKind.INFERENCE,
            ),
        )
        requirement = replace(requirement, needs=(need,))
        linked_fact = replace(fact, reviewed_need_ids=(need.need_id,))
        inference = FormalKnowledgeRecord(
            kind=KnowledgeObjectKind.INFERENCE,
            object_id=StableId(
                "knowledge_inference_00000000000000000000000000000001"
            ),
            object_digest=digest_of("The initializer precedes the later read."),
            type_name="STRUCTURE",
            text="The initializer precedes the later read.",
            context_digest=fact.context_digest,
            support_references=(linked_fact.object_id,),
            reviewed_need_ids=(need.need_id,),
        )
        read_set = replace(read_set, records=(linked_fact, inference))
        missing_relationship = {
            "status": "SATISFIED",
            "supporting_reference_ids": [linked_fact.object_id.value],
            "gap": None,
            "counterexample_reference_ids": [],
            "conflict_reference_ids": [],
            "unknowns": [],
            "limitations": [],
            "rationale": "The fact directly answers the Need.",
        }
        complete = {
            **missing_relationship,
            "supporting_reference_ids": [
                linked_fact.object_id.value,
                inference.object_id.value,
            ],
            "rationale": "The fact and reviewed relationship answer the Need.",
        }
        gateway = SequencedGateway(
            (missing_relationship, complete, complete)
        )

        decision = ModelNeedSufficiencyEvaluator(
            gateway, self.configuration()
        ).evaluate(
            requirement=requirement,
            need=need,
            read_set=read_set,
        )

        self.assertEqual(
            decision.supporting_references,
            (linked_fact.object_id, inference.object_id),
        )
        self.assertEqual(gateway.calls, 5)
        retry_state = json.loads(gateway.contexts[1].manifest.items[-1].content)
        self.assertEqual(
            retry_state["last_error_details"][
                "missing_linked_inference_reference_ids"
            ],
            [inference.object_id.value],
        )

    def test_sufficiency_can_omit_a_redundant_linked_inference(self):
        requirement, need, read_set, fact = self.formal_need_state()
        need = replace(
            need,
            required_kinds=(
                KnowledgeObjectKind.FACT,
                KnowledgeObjectKind.INFERENCE,
            ),
        )
        requirement = replace(requirement, needs=(need,))
        linked_fact = replace(fact, reviewed_need_ids=(need.need_id,))
        necessary = FormalKnowledgeRecord(
            kind=KnowledgeObjectKind.INFERENCE,
            object_id=StableId(
                "knowledge_inference_00000000000000000000000000000001"
            ),
            object_digest=digest_of("The initializer precedes the later read."),
            type_name="STRUCTURE",
            text="The initializer precedes the later read.",
            context_digest=fact.context_digest,
            support_references=(linked_fact.object_id,),
            reviewed_need_ids=(need.need_id,),
        )
        redundant = replace(
            necessary,
            object_id=StableId(
                "knowledge_inference_00000000000000000000000000000002"
            ),
            object_digest=digest_of("The declaration exists before use."),
            text="The declaration exists before use.",
        )
        read_set = replace(
            read_set, records=(linked_fact, necessary, redundant)
        )
        decision_output = {
            "status": "SATISFIED",
            "supporting_reference_ids": [
                linked_fact.object_id.value,
                necessary.object_id.value,
            ],
            "gap": None,
            "counterexample_reference_ids": [],
            "conflict_reference_ids": [],
            "unknowns": [],
            "limitations": [],
            "rationale": (
                "The fact and necessary relationship answer the question; "
                "the other relationship adds no required content."
            ),
        }
        gateway = SequencedGateway((decision_output, decision_output))

        decision = ModelNeedSufficiencyEvaluator(
            gateway, self.configuration()
        ).evaluate(
            requirement=requirement,
            need=need,
            read_set=read_set,
        )

        self.assertEqual(
            decision.supporting_references,
            (linked_fact.object_id, necessary.object_id),
        )
        self.assertEqual(gateway.calls, 4)

    def test_sufficiency_reviewer_uses_full_retry_bound_for_linked_gap(self):
        requirement, need, read_set, record = self.formal_need_state()
        linked = replace(record, reviewed_need_ids=(need.need_id,))
        linked_read_set = replace(read_set, records=(linked,))
        gap = {
            "status": "GAP",
            "supporting_reference_ids": [],
            "gap": "A precise requested proposition remains unsupported.",
            "counterexample_reference_ids": [],
            "conflict_reference_ids": [],
            "unknowns": [],
            "limitations": [],
            "rationale": "The linked fact covers only part of the Need.",
        }
        gateway = SequencedGateway((gap, gap, gap))

        decision = ModelNeedSufficiencyEvaluator(
            gateway, self.configuration()
        ).evaluate(
            requirement=requirement,
            need=need,
            read_set=linked_read_set,
        )

        self.assertEqual(decision.status, NeedStatus.GAP)
        self.assertEqual(gateway.calls, 3)
        final_retry_state = json.loads(
            gateway.contexts[2].manifest.items[-1].content
        )
        self.assertIn(
            "do not demand a called operation's internal algorithm",
            final_retry_state["last_error_details"]["required_action"],
        )

    def test_requirement_plan_must_pass_isolated_fidelity_review(self):
        proposed = {
            "needs": [
                {
                    "need_id": "need:initializer",
                    "question": "What source initializer is declared for App.value?",
                    "required_kinds": ["FACT"],
                    "required_type_names": [],
                    "retrieval_terms": ["App.value"],
                    "minimum_support_count": 1,
                }
            ],
            "joint_constraints": [],
            "rationale": "The request contains one material question.",
        }
        gateway = SequencedGateway(
            (
                proposed,
                {
                    "decision": "ACCEPT",
                    "accepted_need_ids": ["need:initializer"],
                    "original_request_preserved": True,
                    "all_material_questions_covered": True,
                    "findings": [],
                },
            )
        )

        plan = ModelReviewedKnowledgeRequirementPlanner(
            gateway, self.configuration()
        ).plan(original_request="What source initializer is declared for App.value?")

        self.assertEqual(len(plan.needs), 1)
        self.assertEqual(plan.needs[0].required_kinds, (KnowledgeObjectKind.FACT,))
        self.assertEqual(len(gateway.contexts), 2)
        self.assertNotEqual(
            gateway.contexts[0].manifest.strategy_ref,
            gateway.contexts[1].manifest.strategy_ref,
        )
        proposal_state = json.loads(gateway.contexts[0].manifest.items[1].content)
        review_state = json.loads(gateway.contexts[1].manifest.items[1].content)
        self.assertEqual(proposal_state["original_request"], review_state["original_request"])
        self.assertIn("proposed_plan", review_state)
        self.assertIn(
            "Preserve the user's subjects, relationships, conditions",
            gateway.contexts[0].manifest.items[0].content,
        )
        self.assertIn(
            "Every joint constraint must be a direct paraphrase",
            gateway.contexts[0].manifest.items[0].content,
        )
        self.assertIn(
            "presentation order, not evidence of runtime sequence",
            gateway.contexts[0].manifest.items[0].content,
        )
        self.assertIn(
            "Do not propagate the first clause's action",
            gateway.contexts[0].manifest.items[0].content,
        )
        self.assertIn(
            "preserves every material subject, relationship, condition",
            gateway.contexts[1].manifest.items[0].content,
        )
        self.assertIn(
            "Do not broaden, narrow, reinterpret, or answer the request",
            gateway.contexts[0].manifest.items[0].content,
        )
        self.assertIn(
            "not an independent information Need",
            gateway.contexts[0].manifest.items[0].content,
        )
        self.assertIn(
            "asks neither whether Y states X nor what X is",
            gateway.contexts[0].manifest.items[0].content,
        )
        self.assertIn(
            "merely select or bound the target",
            gateway.contexts[0].manifest.items[0].content,
        )
        self.assertIn(
            "inherits the nearest shared operation",
            gateway.contexts[0].manifest.items[0].content,
        )
        self.assertIn(
            "exceptional value supplied to it as coequal exclusions",
            gateway.contexts[0].manifest.items[0].content,
        )
        self.assertIn(
            "Never add illustrative examples, candidate properties, guarantees",
            gateway.contexts[0].manifest.items[0].content,
        )
        self.assertIn(
            "configured output-token limit as a hard transport boundary",
            gateway.contexts[0].manifest.items[0].content,
        )
        self.assertIn(
            "Do not add an umbrella or summary Need",
            gateway.contexts[0].manifest.items[0].content,
        )
        self.assertIn(
            "one requested answer with mandatory coverage dimensions",
            gateway.contexts[0].manifest.items[0].content,
        )
        self.assertIn(
            "compare each Need with the union of the others",
            gateway.contexts[0].manifest.items[0].content,
        )
        self.assertIn(
            "that connected relationship is not a redundant summary",
            gateway.contexts[0].manifest.items[0].content,
        )
        self.assertIn(
            "Judge semantic fidelity, not preferred wording or a catalog of question types",
            gateway.contexts[1].manifest.items[0].content,
        )
        self.assertIn(
            "Reject a redundant umbrella or summary Need",
            gateway.contexts[1].manifest.items[0].content,
        )
        self.assertIn(
            "Perform an explicit containment audit before ACCEPT",
            gateway.contexts[1].manifest.items[0].content,
        )
        self.assertIn(
            "Reject a rationale that preserves or splits a broad Need merely because",
            gateway.contexts[1].manifest.items[0].content,
        )
        self.assertIn(
            "Require a dedicated Need for that connected result",
            gateway.contexts[1].manifest.items[0].content,
        )
        self.assertIn(
            "Reject a separate Need created only from a negative instruction",
            gateway.contexts[1].manifest.items[0].content,
        )
        self.assertIn(
            "does not ask whether Y states X or what X is",
            gateway.contexts[1].manifest.items[0].content,
        )
        self.assertIn(
            "Scan every positive Need for an evidence qualifier",
            gateway.contexts[1].manifest.items[0].content,
        )
        self.assertIn(
            "used only to select or bound the target",
            gateway.contexts[1].manifest.items[0].content,
        )
        self.assertIn(
            "An open-ended request must remain open-ended",
            gateway.contexts[1].manifest.items[0].content,
        )
        self.assertIn(
            "Every joint_constraints object must contain exactly",
            gateway.contexts[0].manifest.items[0].content,
        )

    def test_requirement_plan_with_joint_constraints_requires_acceptance_audit(self):
        proposed = {
            "needs": [
                {
                    "need_id": "N1",
                    "question": (
                        "What is the declared retry condition and maximum "
                        "attempt limit?"
                    ),
                    "required_kinds": ["FACT"],
                    "required_type_names": [],
                    "retrieval_terms": ["retry condition", "maximum attempts"],
                    "minimum_support_count": 1,
                },
            ],
            "joint_constraints": [
                {
                    "constraint_id": "C1",
                    "need_ids": ["N1"],
                    "description": "Do not infer beyond the supplied source boundary.",
                }
            ],
            "rationale": "The complete message is one source-covered deliverable.",
        }
        acceptance = {
            "decision": "ACCEPT",
            "accepted_need_ids": ["N1"],
            "original_request_preserved": True,
            "all_material_questions_covered": True,
            "findings": [],
        }
        gateway = SequencedGateway((proposed, acceptance, acceptance))

        plan = ModelReviewedKnowledgeRequirementPlanner(
            gateway, self.configuration()
        ).plan(
            original_request=(
                "When does RetryClient retry and what is its maximum attempt "
                "limit? Do not infer beyond the supplied source boundary."
            )
        )

        self.assertEqual(len(plan.needs), 1)
        self.assertEqual(gateway.calls, 3)
        audit_state = json.loads(gateway.contexts[2].manifest.items[1].content)
        self.assertEqual(
            audit_state["acceptance_audit"]["prior_decision"],
            "ACCEPT",
        )
        self.assertIn(
            "cannot be the only representation",
            audit_state["acceptance_audit"]["required_action"],
        )
        self.assertIn(
            "must remain a joint boundary",
            audit_state["acceptance_audit"]["required_action"],
        )
        self.assertIn(
            "do not defer to the prior ACCEPT decision",
            gateway.contexts[2].manifest.items[0].content,
        )
        self.assertIn(
            "must not become a dedicated Need",
            gateway.contexts[2].manifest.items[0].content,
        )
        self.assertIn(
            "changes the grammatical relationship of the request",
            gateway.contexts[1].manifest.items[0].content,
        )

    def test_requirement_plan_rejects_entity_metadata_as_answer_support(self):
        proposed = {
            "needs": [
                {
                    "need_id": "need:file",
                    "question": "What behavior does App declare?",
                    "required_kinds": ["ENTITY"],
                    "required_type_names": [],
                    "retrieval_terms": ["App"],
                    "minimum_support_count": 1,
                }
            ],
            "joint_constraints": [],
            "rationale": "Use source identity metadata.",
        }
        gateway = FakeGateway(proposed)

        with self.assertRaises(DomainError) as raised:
            ModelReviewedKnowledgeRequirementPlanner(
                gateway, self.configuration()
            ).plan(original_request="What behavior does App declare?")

        self.assertEqual(raised.exception.code, ErrorCode.STRUCTURED_OUTPUT_INVALID)
        self.assertEqual(gateway.calls, 3)

    def test_requirement_plan_requires_fact_candidates_for_every_need(self):
        proposed = {
            "needs": [
                {
                    "need_id": "need:absence",
                    "question": "What retry capability is not supplied?",
                    "required_kinds": ["INFERENCE"],
                    "required_type_names": [],
                    "retrieval_terms": ["retry"],
                    "minimum_support_count": 1,
                }
            ],
            "joint_constraints": [],
            "rationale": "Treat a bounded source absence as inference-only.",
        }
        gateway = FakeGateway(proposed)

        with self.assertRaises(DomainError) as raised:
            ModelReviewedKnowledgeRequirementPlanner(
                gateway, self.configuration()
            ).plan(original_request="What retry capability is not supplied?")

        self.assertEqual(raised.exception.code, ErrorCode.STRUCTURED_OUTPUT_INVALID)
        self.assertEqual(gateway.calls, 3)

    def test_requirement_proposer_contract_retry_does_not_consume_fidelity_retry(self):
        proposed = {
            "needs": [
                {
                    "need_id": "need:initializer",
                    "question": "What source initializer is declared for App.value?",
                    "required_kinds": ["FACT"],
                    "required_type_names": [],
                    "retrieval_terms": ["App.value"],
                    "minimum_support_count": 1,
                }
            ],
            "joint_constraints": [],
            "rationale": "The request contains one material question.",
        }
        invalid = {
            **proposed,
            "needs": [
                {
                    **proposed["needs"][0],
                    "retrieval_terms": ["App.value", "App.value"],
                }
            ],
        }
        gateway = SequencedGateway(
            (
                invalid,
                proposed,
                {
                    "decision": "ACCEPT",
                    "accepted_need_ids": ["need:initializer"],
                    "original_request_preserved": True,
                    "all_material_questions_covered": True,
                    "findings": [],
                },
            )
        )

        plan = ModelReviewedKnowledgeRequirementPlanner(
            gateway, self.configuration()
        ).plan(original_request="What source initializer is declared for App.value?")

        self.assertEqual(plan.needs[0].need_id, "need:initializer")
        self.assertEqual(gateway.calls, 3)
        self.assertTrue(
            gateway.contexts[1].execution_envelope_ref.endswith(
                ":contract-retry:2"
            )
        )
        self.assertNotIn(
            "fidelity-repair", gateway.contexts[1].execution_envelope_ref
        )

    def test_requirement_proposer_repairs_stale_joint_constraint_need_reference(self):
        needs = [
            {
                "need_id": "N1",
                "question": "What are the first and second requested behaviors?",
                "required_kinds": ["FACT"],
                "required_type_names": [],
                "retrieval_terms": ["first behavior", "second behavior"],
                "minimum_support_count": 1,
            },
        ]
        invalid = {
            "needs": needs,
            "joint_constraints": [
                {
                    "constraint_id": "C1",
                    "need_ids": ["N1", "N2"],
                    "description": "Preserve the requested relationship.",
                }
            ],
            "rationale": "Two requested behaviors have an explicit relationship.",
        }
        corrected = {
            **invalid,
            "joint_constraints": [
                {
                    **invalid["joint_constraints"][0],
                    "need_ids": ["N1"],
                }
            ],
        }
        acceptance = {
            "decision": "ACCEPT",
            "accepted_need_ids": ["N1"],
            "original_request_preserved": True,
            "all_material_questions_covered": True,
            "findings": [],
        }
        gateway = SequencedGateway(
            (invalid, corrected, acceptance, acceptance)
        )

        plan = ModelReviewedKnowledgeRequirementPlanner(
            gateway, self.configuration()
        ).plan(
            original_request=(
                "Explain the first and second requested behaviors while preserving "
                "their stated relationship."
            )
        )

        self.assertEqual(plan.joint_constraints[0].need_ids, ("N1",))
        self.assertEqual(gateway.calls, 4)
        self.assertTrue(
            gateway.contexts[1].execution_envelope_ref.endswith(
                ":contract-retry:2"
            )
        )
        repair_state = json.loads(
            gateway.contexts[1].manifest.items[1].content
        )
        self.assertEqual(
            repair_state["contract_repair"]["last_error"],
            "planned joint constraint references an unknown Need",
        )
        self.assertEqual(
            repair_state["contract_repair"]["last_error_details"][
                "unknown_need_ids"
            ],
            ["N2"],
        )
        self.assertEqual(
            repair_state["contract_repair"]["last_error_details"][
                "allowed_need_ids"
            ],
            ["N1"],
        )

    def test_requirement_proposer_identifies_missing_joint_constraint_fields(self):
        need = {
            "need_id": "N1",
            "question": "What behavior is declared?",
            "required_kinds": ["FACT"],
            "required_type_names": [],
            "retrieval_terms": ["behavior"],
            "minimum_support_count": 1,
        }
        invalid = {
            "needs": [need],
            "joint_constraints": [
                {
                    "constraint_id": "C1",
                    "description": "Preserve the stated evidence boundary.",
                }
            ],
            "rationale": "The request is one complete deliverable.",
        }
        corrected = {
            **invalid,
            "joint_constraints": [
                {
                    **invalid["joint_constraints"][0],
                    "need_ids": ["N1"],
                }
            ],
        }
        acceptance = {
            "decision": "ACCEPT",
            "accepted_need_ids": ["N1"],
            "original_request_preserved": True,
            "all_material_questions_covered": True,
            "findings": [],
        }
        gateway = SequencedGateway((invalid, corrected, acceptance, acceptance))

        plan = ModelReviewedKnowledgeRequirementPlanner(
            gateway, self.configuration()
        ).plan(
            original_request=(
                "What behavior is declared? Preserve the stated evidence boundary."
            )
        )

        self.assertEqual(plan.joint_constraints[0].need_ids, ("N1",))
        repair_state = json.loads(gateway.contexts[1].manifest.items[1].content)
        details = repair_state["contract_repair"]["last_error_details"]
        self.assertEqual(details["constraint_index"], 1)
        self.assertEqual(
            details["required_fields"],
            ["constraint_id", "description", "need_ids"],
        )
        self.assertEqual(
            details["received_fields"],
            ["constraint_id", "description"],
        )

    def test_requirement_reviewer_contract_retry_keeps_the_same_plan(self):
        proposed = {
            "needs": [
                {
                    "need_id": "need:initializer",
                    "question": "What source initializer is declared for App.value?",
                    "required_kinds": ["FACT"],
                    "required_type_names": [],
                    "retrieval_terms": ["App.value"],
                    "minimum_support_count": 1,
                }
            ],
            "joint_constraints": [],
            "rationale": "The request contains one material question.",
        }
        invalid_review = {
            "decision": "ACCEPT",
            "accepted_need_ids": ["need:initializer"],
            "all_material_questions_covered": True,
            "findings": [],
        }
        corrected_review = {
            **invalid_review,
            "original_request_preserved": True,
        }
        gateway = SequencedGateway((proposed, invalid_review, corrected_review))

        plan = ModelReviewedKnowledgeRequirementPlanner(
            gateway, self.configuration()
        ).plan(original_request="What source initializer is declared for App.value?")

        self.assertEqual(plan.needs[0].need_id, "need:initializer")
        first_review_state = gateway.contexts[1].manifest.items[1].content
        second_review_state = gateway.contexts[2].manifest.items[1].content
        self.assertEqual(first_review_state, second_review_state)
        self.assertTrue(
            gateway.contexts[2].execution_envelope_ref.endswith(
                ":contract-retry:2"
            )
        )
        self.assertNotIn(
            "fidelity-repair", gateway.contexts[2].execution_envelope_ref
        )

    def test_requirement_plan_cannot_invent_a_formal_type_filter(self):
        gateway = FakeGateway(
            {
                "needs": [
                    {
                        "need_id": "need:initializer",
                        "question": "What source initializer is declared?",
                        "required_kinds": ["FACT"],
                        "required_type_names": ["App"],
                        "retrieval_terms": ["App.value"],
                        "minimum_support_count": 1,
                    }
                ],
                "joint_constraints": [],
                "rationale": "Use the class name as a guessed type.",
            }
        )

        with self.assertRaises(DomainError) as raised:
            ModelReviewedKnowledgeRequirementPlanner(
                gateway, self.configuration()
            ).plan(original_request="What source initializer is declared?")

        self.assertEqual(raised.exception.code, ErrorCode.STRUCTURED_OUTPUT_INVALID)

    def test_requirement_plan_rejection_cannot_enter_knowledge_use(self):
        proposed = {
            "needs": [
                {
                    "need_id": "need:partial",
                    "question": "What is App.value?",
                    "required_kinds": ["FACT"],
                    "required_type_names": [],
                    "retrieval_terms": [],
                    "minimum_support_count": 1,
                }
            ],
            "joint_constraints": [],
            "rationale": "Partial decomposition.",
        }
        gateway = SequencedGateway(
            (
                proposed,
                {
                    "decision": "REJECT",
                    "accepted_need_ids": [],
                    "original_request_preserved": False,
                    "all_material_questions_covered": False,
                    "findings": ["The source-initializer boundary was omitted."],
                },
                proposed,
                {
                    "decision": "REJECT",
                    "accepted_need_ids": [],
                    "original_request_preserved": False,
                    "all_material_questions_covered": False,
                    "findings": ["The source-initializer boundary was omitted."],
                },
                proposed,
                {
                    "decision": "REJECT",
                    "accepted_need_ids": [],
                    "original_request_preserved": False,
                    "all_material_questions_covered": False,
                    "findings": ["The source-initializer boundary was omitted."],
                },
            )
        )

        with self.assertRaises(DomainError) as raised:
            ModelReviewedKnowledgeRequirementPlanner(
                gateway, self.configuration()
            ).plan(
                original_request="What source initializer is declared for App.value?"
            )

        self.assertEqual(raised.exception.code, ErrorCode.CONTROL_STATE_DENIED)
        self.assertEqual(gateway.calls, 6)

    def test_requirement_plan_repairs_from_isolated_review_findings(self):
        partial = {
            "needs": [
                {
                    "need_id": "need:partial",
                    "question": "What is App.value?",
                    "required_kinds": ["FACT"],
                    "required_type_names": [],
                    "retrieval_terms": ["App.value"],
                    "minimum_support_count": 1,
                }
            ],
            "joint_constraints": [],
            "rationale": "The boundary was omitted.",
        }
        repaired = {
            "needs": [
                {
                    "need_id": "need:initializer",
                    "question": "What source initializer is declared for App.value?",
                    "required_kinds": ["FACT"],
                    "required_type_names": [],
                    "retrieval_terms": ["App.value"],
                    "minimum_support_count": 1,
                }
            ],
            "joint_constraints": [],
            "rationale": "The source-initializer boundary is now explicit.",
        }
        finding = "The source-initializer boundary was omitted."
        gateway = SequencedGateway(
            (
                partial,
                {
                    "decision": "REJECT",
                    "accepted_need_ids": [],
                    "original_request_preserved": False,
                    "all_material_questions_covered": False,
                    "findings": [finding],
                },
                repaired,
                {
                    "decision": "ACCEPT",
                    "accepted_need_ids": ["need:initializer"],
                    "original_request_preserved": True,
                    "all_material_questions_covered": True,
                    "findings": [],
                },
            )
        )

        plan = ModelReviewedKnowledgeRequirementPlanner(
            gateway, self.configuration()
        ).plan(
            original_request="What source initializer is declared for App.value?"
        )

        self.assertEqual(plan.needs[0].need_id, "need:initializer")
        self.assertEqual(gateway.calls, 4)
        repair_state = json.loads(gateway.contexts[2].manifest.items[1].content)
        self.assertEqual(repair_state["prior_review_findings"], [finding])
        self.assertEqual(
            repair_state["previous_proposed_plan"]["needs"][0]["need_id"],
            "need:partial",
        )

    def test_requirement_plan_cannot_expand_into_unbounded_model_calls(self):
        need = {
            "need_id": "need:bounded",
            "question": "What bounded behavior is required?",
            "required_kinds": ["FACT"],
            "required_type_names": [],
            "retrieval_terms": [],
            "minimum_support_count": 1,
        }
        proposed = {
            "needs": [
                {**need, "need_id": f"need:{index}"}
                for index in range(MAX_REQUIREMENT_NEEDS + 1)
            ],
            "joint_constraints": [],
            "rationale": "Too many independently evaluated needs.",
        }
        gateway = FakeGateway(proposed)

        with self.assertRaises(DomainError) as raised:
            ModelReviewedKnowledgeRequirementPlanner(
                gateway, self.configuration()
            ).plan(original_request="Explain the bounded behavior.")

        self.assertEqual(raised.exception.code, ErrorCode.STRUCTURED_OUTPUT_INVALID)
        self.assertEqual(len(gateway.contexts), 3)

    def test_answer_drafter_can_only_select_need_bound_formal_records(self):
        _, need, _, record = self.formal_need_state()
        evidence = AnswerNeedEvidence(
            need_id=need.need_id,
            question=need.question,
            status=NeedStatus.SATISFIED,
            formal_records=(record,),
            disclosure=None,
            limitations=("Source declaration only.",),
        )
        gateway = FakeGateway(
            {
                "selections": [
                    {
                        "need_id": need.need_id,
                        "formal_reference_ids": [record.object_id.value],
                    }
                ],
                "rationale": "The selected proposition directly answers the Need.",
            }
        )

        plan = ModelSourceClosedAnswerDraftPlanner(
            gateway, self.configuration()
        ).plan(original_request=need.question, needs=(evidence,))

        self.assertEqual(plan.selections[0].formal_references, (record.object_id,))
        state = json.loads(gateway.contexts[0].manifest.items[1].content)
        self.assertEqual(state["needs"][0]["formal_records"][0]["text"], record.text)
        self.assertIn(
            "every material subject, relationship, condition, alternative",
            gateway.contexts[0].manifest.items[0].content,
        )
        self.assertIn(
            "order of formal_reference_ids controls the visible answer order",
            gateway.contexts[0].manifest.items[0].content,
        )

    def test_answer_drafter_renders_a_minimal_subset_of_sealed_support(self):
        _, need, _, first = self.formal_need_state()
        second = FormalKnowledgeRecord(
            kind=KnowledgeObjectKind.FACT,
            object_id=StableId(
                "knowledge_fact_00000000000000000000000000000002"
            ),
            object_digest=digest_of("App.value is declared by App."),
            type_name="DECLARES",
            text="App.value is declared by App.",
            context_digest=first.context_digest,
            support_references=first.support_references,
        )
        evidence = AnswerNeedEvidence(
            need_id=need.need_id,
            question=need.question,
            status=NeedStatus.SATISFIED,
            formal_records=(first, second),
            disclosure=None,
            limitations=(),
        )
        complete = {
            "selections": [
                {
                    "need_id": need.need_id,
                    "formal_reference_ids": [
                        first.object_id.value,
                        second.object_id.value,
                    ],
                }
            ],
            "rationale": "The initial draft retained both authorized records.",
        }
        minimal = {
            "selections": [
                {
                    "need_id": need.need_id,
                    "formal_reference_ids": [first.object_id.value],
                }
            ],
            "rationale": "The second proof record repeats the requested proposition.",
        }
        gateway = SequencedGateway((complete, minimal, minimal, minimal))

        plan = ModelSourceClosedAnswerDraftPlanner(
            gateway, self.configuration()
        ).plan(original_request=need.question, needs=(evidence,))

        self.assertEqual(
            plan.selections[0].formal_references,
            (first.object_id,),
        )
        self.assertEqual(gateway.calls, 4)
        audit_state = json.loads(gateway.contexts[1].manifest.items[1].content)
        self.assertIn("minimality_audit", audit_state)
        self.assertIn(
            "deletion, pairwise, and summary-to-premise tests",
            audit_state["minimality_audit"]["required_action"],
        )
        completeness_state = json.loads(
            gateway.contexts[2].manifest.items[1].content
        )
        self.assertIn("completeness_challenge", completeness_state)

    def test_answer_drafter_does_not_force_every_proof_record_into_answer(self):
        _, need, _, first = self.formal_need_state()
        second = replace(
            first,
            object_id=StableId(
                "knowledge_fact_00000000000000000000000000000002"
            ),
            object_digest=digest_of("App.parse produces the requested value."),
            text="App.parse produces the requested value.",
        )
        evidence = AnswerNeedEvidence(
            need_id=need.need_id,
            question=need.question,
            status=NeedStatus.SATISFIED,
            formal_records=(first, second),
            disclosure=None,
            limitations=(),
        )

        def selection(*records: FormalKnowledgeRecord) -> dict[str, object]:
            return {
                "selections": [
                    {
                        "need_id": need.need_id,
                        "formal_reference_ids": [
                            record.object_id.value for record in records
                        ],
                    }
                ],
                "rationale": "The sealed support is preserved and ordered.",
            }

        minimal = selection(first)
        gateway = SequencedGateway((minimal, minimal, minimal, minimal))

        plan = ModelSourceClosedAnswerDraftPlanner(
            gateway, self.configuration()
        ).plan(original_request=need.question, needs=(evidence,))

        self.assertEqual(
            plan.selections[0].formal_references,
            (first.object_id,),
        )
        self.assertEqual(gateway.calls, 4)
        challenge_state = json.loads(
            gateway.contexts[2].manifest.items[1].content
        )
        self.assertIn(
            "literal ledger",
            challenge_state["completeness_challenge"]["required_action"],
        )

    def test_answer_drafter_completeness_challenge_restores_requested_connector(self):
        _, need, _, endpoint = self.formal_need_state()
        connector = FormalKnowledgeRecord(
            kind=KnowledgeObjectKind.INFERENCE,
            object_id=StableId(
                "knowledge_inference_00000000000000000000000000000002"
            ),
            object_digest=digest_of(
                "App.value is initialized before App.run reads it."
            ),
            type_name="STRUCTURE",
            text="App.value is initialized before App.run reads it.",
            context_digest=endpoint.context_digest,
            support_references=(endpoint.object_id,),
        )
        evidence = AnswerNeedEvidence(
            need_id=need.need_id,
            question="What is the actual order from initialization to App.run?",
            status=NeedStatus.SATISFIED,
            formal_records=(endpoint, connector),
            disclosure=None,
            limitations=(),
        )
        endpoint_only = {
            "selections": [
                {
                    "need_id": need.need_id,
                    "formal_reference_ids": [endpoint.object_id.value],
                }
            ],
            "rationale": "The endpoint was selected.",
        }
        complete = {
            "selections": [
                {
                    "need_id": need.need_id,
                    "formal_reference_ids": [
                        endpoint.object_id.value,
                        connector.object_id.value,
                    ],
                }
            ],
            "rationale": "The requested ordering connector is restored.",
        }
        gateway = SequencedGateway(
            (endpoint_only, endpoint_only, complete, complete)
        )

        plan = ModelSourceClosedAnswerDraftPlanner(
            gateway, self.configuration()
        ).plan(original_request=evidence.question, needs=(evidence,))

        self.assertEqual(
            plan.selections[0].formal_references,
            (endpoint.object_id, connector.object_id),
        )
        challenge = json.loads(gateway.contexts[2].manifest.items[1].content)
        self.assertIn(
            "literal ledger",
            challenge["completeness_challenge"]["required_action"],
        )

    def test_answer_drafter_uses_the_ordering_audits_reordered_reference_set(self):
        _, need, _, callee = self.formal_need_state()
        caller = FormalKnowledgeRecord(
            kind=KnowledgeObjectKind.FACT,
            object_id=StableId(
                "knowledge_fact_00000000000000000000000000000002"
            ),
            object_digest=digest_of("App.main invokes App.value."),
            type_name="INVOKES",
            text="App.main invokes App.value.",
            context_digest=callee.context_digest,
            support_references=callee.support_references,
        )
        evidence = AnswerNeedEvidence(
            need_id=need.need_id,
            question="What is the actual call order?",
            status=NeedStatus.SATISFIED,
            formal_records=(callee, caller),
            disclosure=None,
            limitations=(),
        )
        primary = {
            "selections": [
                {
                    "need_id": need.need_id,
                    "formal_reference_ids": [
                        callee.object_id.value,
                        caller.object_id.value,
                    ],
                }
            ],
            "rationale": "The supplied order was retained.",
        }
        reordered = {
            "orders": [
                {
                    "need_id": need.need_id,
                    "reference_ids": ["r1", "r2"],
                }
            ],
            "edges": [
                {
                    "need_id": need.need_id,
                    "predecessor_reference_id": "r2",
                    "successor_reference_id": "r1",
                    "relationship": "CALLER_BEFORE_CALLEE_INTERNALS",
                }
            ],
            "call_return_spans": [],
            "atomic_references": [
                {
                    "need_id": need.need_id,
                    "reference_ids": ["r1", "r2"],
                }
            ],
            "rationale": "AUDITED",
        }
        invalid_reordered = {
            **reordered,
            "call_return_spans": [
                {
                    "need_id": need.need_id,
                    "combined_reference_id": "r2",
                    "callee_internal_reference_id": "r1",
                    "callee_subject_fragment": "App.value",
                    "invocation_fragment": "App.value()",
                    "temporal_connector_fragment": "then",
                    "post_return_fragment": "return result;",
                }
            ],
            "rationale": "AUDITED",
        }
        focused_r1 = {
            "edges": [],
            "call_return_spans": [],
            "atomic_references": [
                {"need_id": need.need_id, "reference_ids": ["r1"]}
            ],
            "rationale": "AUDITED",
        }
        focused_r2 = {
            "edges": [],
            "call_return_spans": [],
            "atomic_references": [
                {"need_id": need.need_id, "reference_ids": ["r2"]}
            ],
            "rationale": "AUDITED",
        }
        gateway = SequencedGateway(
            (
                primary,
                primary,
                primary,
                primary,
                invalid_reordered,
                reordered,
                reordered,
                focused_r1,
                focused_r1,
                focused_r2,
                focused_r2,
            ),
            replay_audits=False,
        )

        plan = ModelSourceClosedAnswerDraftPlanner(
            gateway,
            replace(self.configuration(), sequence_analysis_enabled=True),
        ).plan(original_request="What is the actual call order?", needs=(evidence,))

        self.assertEqual(
            plan.selections[0].formal_references,
            (caller.object_id, callee.object_id),
        )
        self.assertEqual(gateway.calls, 11)
        retry_state = json.loads(
            gateway.contexts[5].manifest.items[1].content
        )
        self.assertIn("contract_repair", retry_state)
        ordering_state = json.loads(
            gateway.contexts[5].manifest.items[1].content
        )
        self.assertEqual(
            ordering_state["prior_orders"][0]["reference_ids"],
            ["r1", "r2"],
        )
        ordering_audit_state = json.loads(
            gateway.contexts[6].manifest.items[1].content
        )
        self.assertIn("ordering_audit", ordering_audit_state)

    def test_answer_drafter_focused_audits_reject_missed_call_return_span(self):
        _, need, _, base_record = self.formal_need_state()
        caller = replace(
            base_record,
            object_id=StableId(
                "knowledge_fact_00000000000000000000000000000002"
            ),
            object_digest=digest_of(
                "App.main calls App.value; if its result is valid, "
                "App.main returns it."
            ),
            type_name="CALLS",
            text=(
                "App.main calls App.value; if its result is valid, "
                "App.main returns it."
            ),
        )
        callee = replace(
            base_record,
            object_digest=digest_of("App.value computes 3."),
            text="App.value computes 3.",
        )
        evidence = AnswerNeedEvidence(
            need_id=need.need_id,
            question="What is the actual call and return order?",
            status=NeedStatus.SATISFIED,
            formal_records=(caller, callee),
            disclosure=None,
            limitations=(),
        )
        selection = {
            "selections": [
                {
                    "need_id": need.need_id,
                    "formal_reference_ids": [
                        caller.object_id.value,
                        callee.object_id.value,
                    ],
                }
            ],
            "rationale": "Both requested facts are selected.",
        }
        full_atomic = {
            "edges": [],
            "call_return_spans": [],
            "atomic_references": [
                {
                    "need_id": need.need_id,
                    "reference_ids": ["r1", "r2"],
                }
            ],
            "rationale": "AUDITED",
        }
        focused_span = {
            "edges": [],
            "call_return_spans": [
                {
                    "need_id": need.need_id,
                    "combined_reference_id": "r1",
                    "callee_internal_reference_id": "r2",
                    "callee_subject_fragment": "App.value computes 3.",
                    "invocation_fragment": "calls App.value",
                    "temporal_connector_fragment": (
                        "; if its result is valid, "
                    ),
                    "post_return_fragment": "App.main returns it",
                }
            ],
            "atomic_references": [],
            "rationale": "AUDITED",
        }
        focused_callee_atomic = {
            "edges": [],
            "call_return_spans": [],
            "atomic_references": [
                {"need_id": need.need_id, "reference_ids": ["r2"]}
            ],
            "rationale": "AUDITED",
        }
        gateway = SequencedGateway(
            (
                selection,
                selection,
                selection,
                selection,
                full_atomic,
                full_atomic,
                focused_span,
                focused_span,
                focused_callee_atomic,
                focused_callee_atomic,
            ),
            replay_audits=False,
        )

        with (
            patch(
                "software_world_model.ai_infrastructure."
                "agentic_knowledge_strategy._SEQUENCE_FOCUSED_AUDIT_THRESHOLD",
                1,
            ),
            patch(
                "software_world_model.ai_infrastructure."
                "agentic_knowledge_strategy._MAX_ANSWER_DRAFT_ATTEMPTS",
                1,
            ),
            self.assertRaises(DomainError) as raised,
        ):
            ModelSourceClosedAnswerDraftPlanner(
                gateway,
                replace(self.configuration(), sequence_analysis_enabled=True),
            ).plan(
                original_request="What is the actual call and return order?",
                needs=(evidence,),
            )

        self.assertEqual(
            raised.exception.message,
            "answer sequence contains an unsplittable call-return fact",
        )
        self.assertEqual(gateway.calls, 10)
        first_focus = json.loads(gateway.contexts[6].manifest.items[1].content)
        self.assertEqual(
            first_focus["call_return_focus"]["focus_reference_ids"],
            ["r1"],
        )
        self.assertIn(
            "later same-path behavior",
            first_focus["call_return_focus"]["required_action"],
        )

    def test_answer_sequence_requires_two_independent_positive_reports(self):
        _, need, _, base_record = self.formal_need_state()
        caller = replace(
            base_record,
            object_id=StableId(
                "knowledge_fact_00000000000000000000000000000002"
            ),
            object_digest=digest_of(
                "App.main calls App.value; after it returns, App.main logs it."
            ),
            text=(
                "App.main calls App.value; after it returns, App.main logs it."
            ),
        )
        callee = replace(
            base_record,
            object_digest=digest_of("App.value computes 3."),
            text="App.value computes 3.",
        )
        evidence = AnswerNeedEvidence(
            need_id=need.need_id,
            question="What is the actual call and return order?",
            status=NeedStatus.SATISFIED,
            formal_records=(caller, callee),
            disclosure=None,
            limitations=(),
        )
        selection = {
            "selections": [
                {
                    "need_id": need.need_id,
                    "formal_reference_ids": [
                        caller.object_id.value,
                        callee.object_id.value,
                    ],
                }
            ],
            "rationale": "Both requested records are selected.",
        }
        span = {
            "edges": [],
            "call_return_spans": [
                {
                    "need_id": need.need_id,
                    "combined_reference_id": "r1",
                    "callee_internal_reference_id": "r2",
                    "callee_subject_fragment": "App.value computes 3.",
                    "invocation_fragment": "calls App.value",
                    "temporal_connector_fragment": "; after it returns, ",
                    "post_return_fragment": "App.main logs it",
                }
            ],
            "atomic_references": [
                {"need_id": need.need_id, "reference_ids": ["r2"]}
            ],
            "rationale": "AUDITED",
        }
        full_atomic = {
            "edges": [],
            "call_return_spans": [],
            "atomic_references": [
                {"need_id": need.need_id, "reference_ids": ["r1", "r2"]}
            ],
            "rationale": "AUDITED",
        }
        focused_caller_atomic = {
            **full_atomic,
            "atomic_references": [
                {"need_id": need.need_id, "reference_ids": ["r1"]}
            ],
        }
        focused_callee_atomic = {
            **full_atomic,
            "atomic_references": [
                {"need_id": need.need_id, "reference_ids": ["r2"]}
            ],
        }
        gateway = SequencedGateway(
            (
                selection,
                selection,
                selection,
                selection,
                span,
                full_atomic,
                focused_caller_atomic,
                focused_caller_atomic,
                focused_callee_atomic,
                focused_callee_atomic,
            ),
            replay_audits=False,
        )

        plan = ModelSourceClosedAnswerDraftPlanner(
            gateway,
            replace(self.configuration(), sequence_analysis_enabled=True),
        ).plan(original_request=evidence.question, needs=(evidence,))

        self.assertEqual(
            plan.selections[0].formal_references,
            (caller.object_id, callee.object_id),
        )
        self.assertEqual(gateway.calls, 10)

    def test_answer_unsplittable_support_fails_without_deleting_a_claim(self):
        _, need, _, base_record = self.formal_need_state()
        caller = replace(
            base_record,
            object_id=StableId(
                "knowledge_fact_00000000000000000000000000000002"
            ),
            object_digest=digest_of(
                "App.main calls App.value; after it returns, App.main logs it."
            ),
            text=(
                "App.main calls App.value; after it returns, App.main logs it."
            ),
        )
        callee = replace(
            base_record,
            object_digest=digest_of("App.value computes 3."),
            text="App.value computes 3.",
        )
        evidence = AnswerNeedEvidence(
            need_id=need.need_id,
            question="What is the actual call and return order?",
            status=NeedStatus.SATISFIED,
            formal_records=(caller, callee),
            disclosure=None,
            limitations=(),
        )
        complete_selection = {
            "selections": [
                {
                    "need_id": need.need_id,
                    "formal_reference_ids": [
                        caller.object_id.value,
                        callee.object_id.value,
                    ],
                }
            ],
            "rationale": "Both requested records are selected.",
        }
        span = {
            "edges": [],
            "call_return_spans": [
                {
                    "need_id": need.need_id,
                    "combined_reference_id": "r1",
                    "callee_internal_reference_id": "r2",
                    "callee_subject_fragment": "App.value computes 3.",
                    "invocation_fragment": "calls App.value",
                    "temporal_connector_fragment": "; after it returns, ",
                    "post_return_fragment": "App.main logs it",
                }
            ],
            "atomic_references": [
                {"need_id": need.need_id, "reference_ids": ["r2"]}
            ],
            "rationale": "AUDITED",
        }
        focused_callee_atomic = {
            "edges": [],
            "call_return_spans": [],
            "atomic_references": [
                {"need_id": need.need_id, "reference_ids": ["r2"]}
            ],
            "rationale": "AUDITED",
        }
        gateway = SequencedGateway(
            (
                complete_selection,
                complete_selection,
                complete_selection,
                complete_selection,
                span,
                span,
                span,
                span,
                focused_callee_atomic,
                focused_callee_atomic,
            ),
            replay_audits=False,
        )

        with self.assertRaises(DomainError) as raised:
            ModelSourceClosedAnswerDraftPlanner(
                gateway,
                replace(self.configuration(), sequence_analysis_enabled=True),
            ).plan(original_request=evidence.question, needs=(evidence,))

        self.assertEqual(
            raised.exception.message,
            "answer sequence contains an unsplittable call-return fact",
        )
        self.assertEqual(
            raised.exception.details["unsplittable_reference_ids"],
            (caller.object_id.value,),
        )
        self.assertEqual(gateway.calls, 10)

    def test_answer_focused_audit_ignores_platform_derived_inference_edges(self):
        _, need, _, fact = self.formal_need_state()
        inference = FormalKnowledgeRecord(
            kind=KnowledgeObjectKind.INFERENCE,
            object_id=StableId(
                "knowledge_inference_00000000000000000000000000000002"
            ),
            object_digest=digest_of(
                "App.value initialization precedes the reported result."
            ),
            type_name="STRUCTURE",
            text="App.value initialization precedes the reported result.",
            context_digest=fact.context_digest,
            support_references=(fact.object_id,),
        )
        evidence = AnswerNeedEvidence(
            need_id=need.need_id,
            question="What is the actual declaration-to-result order?",
            status=NeedStatus.SATISFIED,
            formal_records=(fact, inference),
            disclosure=None,
            limitations=(),
        )
        selection = {
            "selections": [
                {
                    "need_id": need.need_id,
                    "formal_reference_ids": [
                        fact.object_id.value,
                        inference.object_id.value,
                    ],
                }
            ],
            "rationale": "Both distinct requested records are selected.",
        }
        full_atomic = {
            "edges": [],
            "call_return_spans": [],
            "atomic_references": [
                {
                    "need_id": need.need_id,
                    "reference_ids": ["r1", "r2"],
                }
            ],
            "rationale": "AUDITED",
        }
        focused_fact = {
            **full_atomic,
            "atomic_references": [
                {"need_id": need.need_id, "reference_ids": ["r1"]}
            ],
        }
        focused_inference = {
            **full_atomic,
            "atomic_references": [
                {"need_id": need.need_id, "reference_ids": ["r2"]}
            ],
        }
        gateway = SequencedGateway(
            (
                selection,
                selection,
                selection,
                selection,
                full_atomic,
                full_atomic,
                focused_fact,
                focused_fact,
                focused_inference,
                focused_inference,
            ),
            replay_audits=False,
        )

        with patch(
            "software_world_model.ai_infrastructure."
            "agentic_knowledge_strategy._SEQUENCE_FOCUSED_AUDIT_THRESHOLD",
            1,
        ):
            plan = ModelSourceClosedAnswerDraftPlanner(
                gateway,
                replace(self.configuration(), sequence_analysis_enabled=True),
            ).plan(original_request=evidence.question, needs=(evidence,))

        self.assertEqual(
            plan.selections[0].formal_references,
            (fact.object_id, inference.object_id),
        )
        self.assertEqual(gateway.calls, 10)

    def test_answer_drafter_never_renders_entity_identity_metadata(self):
        _, need, _, record = self.formal_need_state()
        entity = FormalKnowledgeRecord(
            kind=KnowledgeObjectKind.ENTITY,
            object_id=StableId(
                "knowledge_entity_00000000000000000000000000000001"
            ),
            object_digest=digest_of("internal source identity"),
            type_name="SOURCE_FILE",
            text="sha256:internal:src/App.java src/App.java",
            context_digest=record.context_digest,
            support_references=record.support_references,
        )
        evidence = AnswerNeedEvidence(
            need_id=need.need_id,
            question=need.question,
            status=NeedStatus.SATISFIED,
            formal_records=(entity, record),
            disclosure=None,
            limitations=(),
        )
        invalid = {
            "selections": [
                {
                    "need_id": need.need_id,
                    "formal_reference_ids": [entity.object_id.value],
                }
            ],
            "rationale": "Selected internal identity metadata.",
        }
        corrected = {
            "selections": [
                {
                    "need_id": need.need_id,
                    "formal_reference_ids": [record.object_id.value],
                }
            ],
            "rationale": "Selected the answer proposition only.",
        }
        gateway = SequencedGateway((invalid, corrected))

        plan = ModelSourceClosedAnswerDraftPlanner(
            gateway, self.configuration()
        ).plan(original_request=need.question, needs=(evidence,))

        self.assertEqual(plan.selections[0].formal_references, (record.object_id,))
        initial_state = json.loads(gateway.contexts[0].manifest.items[1].content)
        self.assertEqual(
            [item["kind"] for item in initial_state["needs"][0]["formal_records"]],
            ["FACT"],
        )

    def test_answer_drafter_cannot_invent_formal_reference(self):
        _, need, _, record = self.formal_need_state()
        evidence = AnswerNeedEvidence(
            need_id=need.need_id,
            question=need.question,
            status=NeedStatus.SATISFIED,
            formal_records=(record,),
            disclosure=None,
            limitations=(),
        )
        gateway = FakeGateway(
            {
                "selections": [
                    {
                        "need_id": need.need_id,
                        "formal_reference_ids": [
                            "knowledge_fact_ffffffffffffffffffffffffffffffff"
                        ],
                    }
                ],
                "rationale": "Invented selection.",
            }
        )

        with self.assertRaises(DomainError) as raised:
            ModelSourceClosedAnswerDraftPlanner(
                gateway, self.configuration()
            ).plan(original_request=need.question, needs=(evidence,))

        self.assertEqual(raised.exception.code, ErrorCode.CONTROL_STATE_DENIED)
        self.assertEqual(gateway.calls, 5)

    def test_answer_drafter_repairs_a_reference_from_another_need(self):
        _, need, _, record = self.formal_need_state()
        evidence = AnswerNeedEvidence(
            need_id=need.need_id,
            question=need.question,
            status=NeedStatus.SATISFIED,
            formal_records=(record,),
            disclosure=None,
            limitations=(),
        )
        invalid = {
            "selections": [
                {
                    "need_id": need.need_id,
                    "formal_reference_ids": [
                        "knowledge_fact_ffffffffffffffffffffffffffffffff"
                    ],
                }
            ],
            "rationale": "Selected a record from another Need.",
        }
        corrected = {
            "selections": [
                {
                    "need_id": need.need_id,
                    "formal_reference_ids": [record.object_id.value],
                }
            ],
            "rationale": "Selected only the exact Need-bound record.",
        }
        gateway = SequencedGateway((invalid, corrected))

        plan = ModelSourceClosedAnswerDraftPlanner(
            gateway, self.configuration()
        ).plan(original_request=need.question, needs=(evidence,))

        self.assertEqual(plan.selections[0].formal_references, (record.object_id,))
        repair_state = json.loads(gateway.contexts[1].manifest.items[1].content)
        self.assertEqual(
            repair_state["contract_repair"]["allowed_reference_ids_by_need"][
                need.need_id
            ],
            [record.object_id.value],
        )

    def test_answer_drafter_retries_incomplete_need_coverage_with_total_bound(self):
        _, need, _, record = self.formal_need_state()
        evidence = AnswerNeedEvidence(
            need_id=need.need_id,
            question=need.question,
            status=NeedStatus.SATISFIED,
            formal_records=(record,),
            disclosure=None,
            limitations=(),
        )
        gateway = SequencedGateway(
            [
                {
                    "selections": [],
                    "rationale": "The Need was accidentally omitted.",
                },
                {
                    "selections": [
                        {
                            "need_id": need.need_id,
                            "formal_reference_ids": [record.object_id.value],
                        }
                    ],
                    "rationale": "Every Need is now covered exactly once.",
                },
            ]
        )

        plan = ModelSourceClosedAnswerDraftPlanner(
            gateway, self.configuration()
        ).plan(original_request=need.question, needs=(evidence,))

        self.assertEqual(plan.selections[0].formal_references, (record.object_id,))
        self.assertEqual(gateway.calls, 2)
        self.assertNotEqual(
            gateway.contexts[0].execution_envelope_ref,
            gateway.contexts[1].execution_envelope_ref,
        )
        self.assertTrue(
            gateway.contexts[1].execution_envelope_ref.endswith(
                ":contract-retry:2"
            )
        )

    def test_answer_drafter_stops_after_five_incomplete_outputs(self):
        _, need, _, record = self.formal_need_state()
        evidence = AnswerNeedEvidence(
            need_id=need.need_id,
            question=need.question,
            status=NeedStatus.SATISFIED,
            formal_records=(record,),
            disclosure=None,
            limitations=(),
        )
        gateway = FakeGateway(
            {
                "selections": [],
                "rationale": "The Need was accidentally omitted.",
            }
        )

        with self.assertRaises(DomainError) as raised:
            ModelSourceClosedAnswerDraftPlanner(
                gateway, self.configuration()
            ).plan(original_request=need.question, needs=(evidence,))

        self.assertEqual(raised.exception.code, ErrorCode.STRUCTURED_OUTPUT_INVALID)
        self.assertEqual(raised.exception.details["attempt_count"], 5)
        self.assertEqual(gateway.calls, 5)

    def test_semantic_answer_reviewer_emits_closed_review_dimensions(self):
        requirement, need, _, record = self.formal_need_state()
        proof = SimpleNamespace(supporting_references=(record.object_id,))
        assessment = SimpleNamespace(
            assessment_id=StableId(
                "assessment_00000000000000000000000000000001"
            ),
            digest=digest_of("assessment"),
            sufficient=True,
            joint_constraint_failures=(),
            items=(
                SimpleNamespace(
                    need_id=need.need_id,
                    status=NeedStatus.SATISFIED,
                    proof=proof,
                    gap=None,
                    unknowns=(),
                    limitations=("Source declaration only.",),
                    conflicts=(),
                ),
            ),
        )
        candidate = SimpleNamespace(
            candidate_id=StableId(
                "answer_candidate_00000000000000000000000000000001"
            ),
            digest=digest_of("candidate"),
            response_kind=SimpleNamespace(value="KNOWLEDGE_COMPLETE"),
            body=record.text,
            claims=(
                SimpleNamespace(
                    claim_id="claim:1",
                    need_id=need.need_id,
                    kind=SimpleNamespace(value="FORMAL_KNOWLEDGE"),
                    text=record.text,
                    formal_reference=record.object_id,
                    gap=None,
                ),
            ),
        )
        gateway = FakeGateway(
            {
                "decision": "REJECT",
                "failed_dimensions": ["SAFETY_AND_DISCLOSURE"],
                "findings": ["The source-only limitation is not visible in the body."],
            }
        )

        decision = ModelSemanticAnswerReviewer(
            gateway, self.configuration()
        ).review(
            task=SimpleNamespace(original_request=requirement.original_request),
            requirement=requirement,
            candidate=candidate,
            assessment=assessment,
        )

        self.assertFalse(decision.approved)
        self.assertEqual(gateway.calls, 3)
        self.assertEqual(
            decision.failed_dimensions,
            (ReviewDimension.SAFETY_AND_DISCLOSURE,),
        )
        self.assertIn(
            "without imposing an unrequested question template or project convention",
            gateway.contexts[0].manifest.items[0].content,
        )
        self.assertIn(
            "The order of answer lines and adjacent stage descriptions",
            gateway.contexts[0].manifest.items[0].content,
        )
        self.assertIn(
            "source-visible causal mechanism",
            gateway.contexts[0].manifest.items[0].content,
        )
        self.assertIn(
            "already states the causal mechanism",
            gateway.contexts[0].manifest.items[0].content,
        )
        self.assertIn(
            "Naming only the selected result, a later type check",
            gateway.contexts[0].manifest.items[0].content,
        )
        reconsideration_state = json.loads(
            gateway.contexts[1].manifest.items[1].content
        )
        self.assertIn("reconsideration", reconsideration_state)
        self.assertIn(
            "Do not attribute a limitation or conclusion",
            reconsideration_state["reconsideration"]["required_action"],
        )
        self.assertIn(
            "any visible limitation disclaims, assumes",
            gateway.contexts[0].manifest.items[0].content,
        )
        self.assertIn(
            "presents a nested branch through any fallback token",
            gateway.contexts[0].manifest.items[0].content,
        )
        self.assertIn(
            "Final nested-scope audit before APPROVE",
            gateway.contexts[0].manifest.items[0].content,
        )
        self.assertIn(
            "caller invocation, helper internals, then caller post-return behavior",
            gateway.contexts[0].manifest.items[0].content,
        )

    def test_semantic_answer_approval_requires_adversarial_confirmation(self):
        requirement, need, _, record = self.formal_need_state()
        assessment = SimpleNamespace(
            assessment_id=StableId(
                "assessment_00000000000000000000000000000001"
            ),
            digest=digest_of("assessment"),
            sufficient=True,
            joint_constraint_failures=(),
            items=(
                SimpleNamespace(
                    need_id=need.need_id,
                    status=NeedStatus.SATISFIED,
                    proof=SimpleNamespace(
                        supporting_references=(record.object_id,)
                    ),
                    gap=None,
                    unknowns=(),
                    limitations=(),
                    conflicts=(),
                ),
            ),
        )
        candidate = SimpleNamespace(
            candidate_id=StableId(
                "answer_candidate_00000000000000000000000000000001"
            ),
            digest=digest_of("candidate"),
            response_kind=SimpleNamespace(value="KNOWLEDGE_COMPLETE"),
            body=record.text,
            claims=(
                SimpleNamespace(
                    claim_id="claim:1",
                    need_id=need.need_id,
                    kind=SimpleNamespace(value="FORMAL_KNOWLEDGE"),
                    text=record.text,
                    formal_reference=record.object_id,
                    gap=None,
                ),
            ),
        )
        approval = {
            "decision": "APPROVE",
            "failed_dimensions": [],
            "findings": [],
        }
        gateway = SequencedGateway((approval, approval))

        decision = ModelSemanticAnswerReviewer(
            gateway, self.configuration()
        ).review(
            task=SimpleNamespace(original_request=requirement.original_request),
            requirement=requirement,
            candidate=candidate,
            assessment=assessment,
        )

        self.assertTrue(decision.approved)
        self.assertEqual(gateway.calls, 2)
        audit_state = json.loads(
            gateway.contexts[1].manifest.items[1].content
        )
        self.assertIn("approval_audit", audit_state)
        self.assertIn(
            "nested branch outcome",
            audit_state["approval_audit"]["required_action"],
        )
        self.assertIn(
            "Final execution-order audit before APPROVE",
            gateway.contexts[1].manifest.items[0].content,
        )

        rejection = {
            "decision": "REJECT",
            "failed_dimensions": ["TASK_FIDELITY"],
            "findings": [
                "The approval audit found that the visible order contradicts the requested flow."
            ],
        }
        rejecting_gateway = SequencedGateway(
            (approval, rejection, rejection), replay_audits=False
        )

        rejected_decision = ModelSemanticAnswerReviewer(
            rejecting_gateway, self.configuration()
        ).review(
            task=SimpleNamespace(original_request=requirement.original_request),
            requirement=requirement,
            candidate=candidate,
            assessment=assessment,
        )

        self.assertFalse(rejected_decision.approved)
        self.assertEqual(
            rejected_decision.failed_dimensions,
            (ReviewDimension.TASK_FIDELITY,),
        )
        self.assertEqual(rejecting_gateway.calls, 3)
        dispute_state = json.loads(
            rejecting_gateway.contexts[2].manifest.items[1].content
        )
        self.assertEqual(
            dispute_state["review_dispute"]["adversarial_findings"],
            rejection["findings"],
        )
        self.assertIn(
            "do not count votes",
            dispute_state["review_dispute"]["required_action"],
        )

        recovering_gateway = SequencedGateway(
            (approval, rejection, approval), replay_audits=False
        )

        recovered_decision = ModelSemanticAnswerReviewer(
            recovering_gateway, self.configuration()
        ).review(
            task=SimpleNamespace(original_request=requirement.original_request),
            requirement=requirement,
            candidate=candidate,
            assessment=assessment,
        )

        self.assertTrue(recovered_decision.approved)
        self.assertEqual(recovering_gateway.calls, 3)


if __name__ == "__main__":
    unittest.main()
