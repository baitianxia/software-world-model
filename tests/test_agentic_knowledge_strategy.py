from __future__ import annotations

import json
import hashlib
from types import SimpleNamespace
import unittest

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
from software_world_model.application_services import (
    AnswerNeedEvidence,
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
    def __init__(self, outputs):
        super().__init__(None)
        self.outputs = list(outputs)

    def invoke(self, context):
        self.output = self.outputs.pop(0)
        return super().invoke(context)


class AgenticKnowledgeStrategyTests(unittest.TestCase):
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
        self.assertEqual(len(agentic_knowledge_output_schemas()), 8)
        self.assertTrue(
            all(
                component.strategy_implementation_digest == expected
                for component in components
            )
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

    def completed_read(self, *, start=0, end=32, has_more=False):
        path = "src/App.java"
        observation = SimpleNamespace(
            tool=SourceTool.READ,
            source_context=SimpleNamespace(
                repository_revision="a" * 40,
                subject=path,
            ),
            subject=path,
            coverage=(
                ("path", path),
                ("range", f"bytes:{start}-{end}"),
                ("revision", "a" * 40),
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

    def completed_empty_search(self, ordinal: int):
        observation = SimpleNamespace(
            tool=SourceTool.SEARCH,
            source_context=SimpleNamespace(
                repository_revision="a" * 40,
                subject=f"missing-{ordinal}",
            ),
            subject=f"missing-{ordinal}",
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
        read = {
            **stop,
            "decision": "EXECUTE",
            "tool": "READ",
            "revision": "a" * 40,
            "path": "src/App.java",
            "offset": "12",
            "max_bytes": "4096",
            "rationale": "Continue the required target file from the next byte.",
        }
        gateway = SequencedGateway((stop, read))

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
        repair = json.loads(gateway.contexts[1].manifest.items[-1].content)
        self.assertEqual(
            repair["last_error_details"]["missing_required_paths"],
            [
                {
                    "revision": "a" * 40,
                    "path": "src/App.java",
                    "next_offset": 12,
                }
            ],
        )

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
        read_base = {
            **stop,
            "decision": "EXECUTE",
            "tool": "READ",
            "revision": "b" * 40,
            "path": "src/App.java",
            "offset": "0",
            "max_bytes": "4096",
            "rationale": "Read the required base-revision file.",
        }
        gateway = SequencedGateway((stop, read_base))

        proposal = ModelSourceInvestigationPlanner(
            gateway, self.configuration()
        ).propose(
            request=request,
            completed_operations=(self.completed_read(),),
            ordinal=2,
        )

        self.assertEqual(proposal.tool, SourceTool.READ)
        self.assertEqual(dict(proposal.parameters)["revision"], "b" * 40)
        repair = json.loads(gateway.contexts[1].manifest.items[-1].content)
        self.assertEqual(
            repair["last_error_details"]["missing_required_paths"],
            [
                {
                    "revision": "b" * 40,
                    "path": "src/App.java",
                    "next_offset": 0,
                }
            ],
        )

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

    def test_source_planner_stops_repeating_empty_searches(self):
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
                self.completed_empty_search(2),
            ),
            ordinal=3,
        )

        self.assertEqual(proposal.tool, SourceTool.READ)
        self.assertEqual(gateway.calls, 2)
        state = json.loads(gateway.contexts[0].manifest.items[1].content)
        self.assertFalse(state["recovery_guidance"]["search_allowed"])
        repair = json.loads(gateway.contexts[1].manifest.items[-1].content)
        self.assertEqual(
            repair["last_error_details"]["consecutive_empty_searches"], 2
        )

    def test_fact_builder_requires_independent_acceptance_before_sealing(self):
        artifact = self.artifact()
        candidate = {
            "candidate_key": "app-value",
            "artifact_id": artifact.artifact_id.value,
            "line_start": 2,
            "line_end": 2,
            "entity_type": "CODE_SYMBOL",
            "predicate": "HAS_VALUE",
            "statement": "App.value is initialized to 3.",
            "condition": None,
            "limitation": "This states the source initializer, not a runtime invariant.",
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
        self.assertIn("App.value is initialized to 3.", bundle.facts[0].object_value)

        self.assertIn("runtime invariant", bundle.facts[0].object_value)
        excerpt = artifact.payload[
            bundle.evidence[0].byte_start : bundle.evidence[0].byte_end
        ].decode("utf-8")
        self.assertEqual(excerpt, "    int value = 3;\n")
        self.assertEqual(len(gateway.contexts), 2)
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
        self.assertEqual(
            proposal_state["reviewed_requirement_plan"],
            review_state["reviewed_requirement_plan"],
        )
        self.assertEqual(
            proposal_state["reviewed_requirement_plan"]["needs"][0]["need_id"],
            "need:initializer",
        )
        self.assertIn(
            "trace the visible state chronologically",
            gateway.contexts[0].manifest.items[0].content,
        )
        self.assertIn(
            "independently simulate the cited control flow",
            gateway.contexts[1].manifest.items[0].content,
        )
        self.assertIn(
            "keep every edge explicit",
            gateway.contexts[0].manifest.items[0].content,
        )
        self.assertIn(
            "complete coverage requires both the exact caller-to-helper edge",
            gateway.contexts[1].manifest.items[0].content,
        )
        self.assertIn(
            "the entry fact must preserve each material construction",
            gateway.contexts[0].manifest.items[0].content,
        )
        self.assertIn(
            "state both the user's category and the exact source expression",
            gateway.contexts[0].manifest.items[0].content,
        )
        self.assertIn(
            "accepted entry fact omits a visible construction",
            gateway.contexts[1].manifest.items[0].content,
        )

    def test_fact_builder_repairs_language_for_chinese_browser_request(self):
        artifact = self.artifact()
        english = {
            "candidate_key": "app-value",
            "artifact_id": artifact.artifact_id.value,
            "line_start": 2,
            "line_end": 2,
            "entity_type": "CODE_SYMBOL",
            "predicate": "HAS_VALUE",
            "statement": "App.value is initialized to 3.",
            "condition": None,
            "limitation": None,
        }
        chinese = {
            **english,
            "statement": "App.value 的源码初始值为 3。",
        }
        gateway = SequencedGateway(
            (
                {"candidates": [english], "limitations": []},
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
        self.assertIn("初始值为 3", bundle.facts[0].object_value)
        repair = json.loads(gateway.contexts[1].manifest.items[1].content)[
            "contract_repair"
        ]
        self.assertEqual(
            repair["last_error_details"]["response_language"], "zh-CN"
        )

    def test_fact_builder_retries_statement_with_embedded_metadata_labels(self):
        artifact = self.artifact()
        candidate = {
            "candidate_key": "app-value",
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

    def test_fact_builder_normalizes_textual_null_without_rewriting_candidates(self):
        artifact = self.artifact()
        candidate = {
            "candidate_key": "app-value",
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

    def test_fact_builder_repairs_omitted_constructor_from_minimal_excerpt(self):
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
        invalid = {
            **candidate,
            "statement": "Template.compile constructs a Resolver.",
        }
        gateway = SequencedGateway(
            (
                {"candidates": [invalid], "limitations": []},
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
        repair = json.loads(gateway.contexts[1].manifest.items[1].content)[
            "contract_repair"
        ]
        self.assertEqual(
            repair["last_error_details"]["missing_constructor_types"],
            ["Document"],
        )
        self.assertNotIn("Limitation:", bundle.facts[0].object_value)

    def test_fact_builder_preserves_a_final_repair_after_three_truncated_outputs(self):
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
                {
                    "candidates": [
                        {**valid, "statement": "Template.compile constructs a Resolver."}
                    ],
                    "limitations": [],
                },
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
        self.assertEqual(gateway.calls, 6)
        repair = json.loads(gateway.contexts[4].manifest.items[1].content)[
            "contract_repair"
        ]
        self.assertEqual(
            repair["last_error_details"]["missing_constructor_types"],
            ["Document"],
        )

    def test_fact_builder_identifies_out_of_range_artifact_lines_during_repair(self):
        artifact = self.artifact()
        candidate = {
            "candidate_key": "app-value",
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

    def test_fact_builder_does_not_publish_reviewer_rejected_candidates(self):
        artifact = self.artifact()
        candidate = {
            "candidate_key": "overclaim",
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
        gateway = SequencedGateway(
            (proposal, rejection, proposal, rejection, proposal, rejection)
        )

        bundle = ModelReviewedKnowledgeBuilder(
            gateway, self.configuration()
        ).build(request=self.request(), target=self.request().target, artifacts=(artifact,))

        self.assertEqual(bundle.entities, ())
        self.assertEqual(bundle.facts, ())
        self.assertEqual(gateway.calls, 6)

    def test_fact_builder_repairs_a_reviewed_objective_coverage_gap(self):
        artifact = self.artifact()
        candidate = {
            "candidate_key": "app-value",
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
        gateway = SequencedGateway(
            (
                {"candidates": [candidate], "limitations": []},
                {
                    "decision": "REJECT",
                    "accepted_candidate_keys": ["app-value"],
                    "all_supported_objective_aspects_covered": False,
                    "findings": [finding],
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
                "limitations": ["This proves the source initializer only."],
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
            "Do not add a completion criterion that the Need and original request do not ask for",
            instruction,
        )
        self.assertIn(
            "enumerate every explicit clause, condition, alternative, comparison side, or requested result",
            instruction,
        )
        self.assertIn(
            "explicit control flow that states the guard or early return",
            instruction,
        )
        self.assertIn(
            "preserve that boundary in the returned limitations array",
            instruction,
        )
        self.assertIn(
            "Explicit formal records may be combined to prove one cross-component mechanism",
            instruction,
        )
        self.assertIn(
            "SATISFIED cannot use a limitation to admit",
            instruction,
        )
        self.assertIn(
            "explicit return behavior for every requested input branch is the guarantee",
            instruction,
        )
        self.assertIn(
            "Do not create a terminology GAP for that direct mapping",
            instruction,
        )
        self.assertIn(
            "A later validate-or-render catch cannot replace",
            instruction,
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
        self.assertEqual(gateway.calls, 2)
        repair = gateway.contexts[1].manifest.items[-1]
        self.assertEqual(
            repair.schema_ref, "need-sufficiency-contract-repair@1"
        )
        repair_state = json.loads(repair.content)
        self.assertEqual(
            repair_state["allowed_reference_ids"], [record.object_id.value]
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
            "Preserve grammatical scope",
            gateway.contexts[0].manifest.items[0].content,
        )
        self.assertIn(
            "Reject grammatical scope expansion",
            gateway.contexts[1].manifest.items[0].content,
        )
        self.assertIn(
            "ordinary why questions about source-visible branches as mechanism questions",
            gateway.contexts[0].manifest.items[0].content,
        )
        self.assertIn(
            "Never upgrade why into an unavailable design-motivation requirement",
            gateway.contexts[0].manifest.items[0].content,
        )
        self.assertIn(
            "type conversion must include how conversion failure is handled",
            gateway.contexts[0].manifest.items[0].content,
        )
        self.assertIn(
            "turns an ordinary source-code why question into a design-intent",
            gateway.contexts[1].manifest.items[0].content,
        )
        self.assertIn(
            "loses a distinct failure outcome of a separately named processing stage",
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
            "map every explicit clause, condition, alternative, comparison side",
            gateway.contexts[0].manifest.items[0].content,
        )

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
        self.assertEqual(gateway.calls, 3)

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

    def test_answer_drafter_stops_after_three_incomplete_outputs(self):
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
        self.assertEqual(raised.exception.details["attempt_count"], 3)
        self.assertEqual(gateway.calls, 3)

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
        self.assertEqual(
            decision.failed_dimensions,
            (ReviewDimension.SAFETY_AND_DISCLOSURE,),
        )
        self.assertIn(
            "verify every explicit guard, condition, alternative, phase",
            gateway.contexts[0].manifest.items[0].content,
        )


if __name__ == "__main__":
    unittest.main()
