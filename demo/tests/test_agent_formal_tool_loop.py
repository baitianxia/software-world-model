from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from swm_demo.agent_contract import AgentTask
from swm_demo.application import ApplicationServices
from swm_demo.artifact_contract import SourceArtifact, SourceCollection
from swm_demo.ids import content_hash
from swm_demo.knowledge_contract import (
    Evidence,
    FormalFact,
    FormalInference,
    KnowledgeEntity,
    KnowledgePackage,
)
from swm_demo.knowledge_requirement import FACT, GAP, INFERENCE, SATISFIED
from swm_demo.model_gateway import ModelGateway
from swm_demo.task_execution_agent import TaskExecutionAgent, TaskExecutionError


SCOPE_ID = "system:agent-formal-tool-loop"
REVISION = "revision:formal-tool-loop"


class _ScriptedToolProvider:
    provider_name = "formal-tool-loop-test"
    model_name = "scripted-tool-planner"
    model_version = "1"

    def __init__(self, mode: str):
        self.mode = mode
        self.calls: list[tuple[str, dict[str, object]]] = []
        self.actions: list[dict[str, object]] = []

    def invoke(
        self, capability: str, payload: dict[str, object]
    ) -> dict[str, object]:
        self.calls.append((capability, payload))
        if capability == "form-knowledge-requirement":
            needs = (
                [
                    {
                        "need_id": "need:fact",
                        "question": "Which direct call is present?",
                        "sufficiency_criterion": "A direct formal Fact answers it.",
                    },
                    {
                        "need_id": "need:inference",
                        "question": "What behavior follows?",
                        "sufficiency_criterion": "A formal Inference answers it.",
                    },
                ]
                if self.mode == "mixed"
                else [
                    {
                        "need_id": "need:answer",
                        "question": "What does Alpha#run call?",
                        "sufficiency_criterion": (
                            "A discovered formal proposition directly answers it."
                        ),
                    }
                ]
            )
            return {"needs": needs}

        if capability == "plan-formal-knowledge-step":
            trace = list(payload["tool_trace"])
            if self.mode == "recoverable-cross-shape":
                action = (
                    {
                        "action": "SEARCH",
                        "arguments": {
                            "kind": "INFERENCE",
                            "knowledge_ids": [],
                        },
                    }
                    if not trace
                    else {"action": "STOP", "arguments": {}}
                )
            elif self.mode == "recoverable-invalid":
                action = (
                    {
                        "action": "EXPLAIN",
                        "arguments": {
                            "kind": "INFERENCE",
                            "knowledge_ids": [],
                        },
                    }
                    if not trace
                    else {"action": "STOP", "arguments": {}}
                )
            elif self.mode == "limit":
                action = self._search_inference("not-present")
                action["arguments"]["cursor"] = len(trace)  # type: ignore[index]
            elif self.mode == "scope-forgery":
                action = self._search_inference("not-present")
                action["arguments"]["scope_id"] = "system:forged"  # type: ignore[index]
                action["arguments"]["snapshot_token"] = "snapshot:forged"  # type: ignore[index]
            elif self.mode == "repeat":
                action = self._search_inference("not-present")
            elif self.mode == "empty":
                action = (
                    self._search_inference("not-present")
                    if not trace
                    else {"action": "STOP", "arguments": {}}
                )
            elif self.mode == "fact":
                if not trace:
                    action = {
                        "action": "SEARCH",
                        "arguments": {
                            "kind": "ENTITY",
                            "query": "Alpha#run",
                            "match_mode": "EXACT",
                            "type_name": "java-method",
                        },
                    }
                elif len(trace) == 1:
                    entity_id = trace[-1]["result"]["items"][0]["entity_id"]
                    action = {
                        "action": "NEIGHBORHOOD",
                        "arguments": {
                            "entity_ids": [entity_id],
                            "direction": "OUTGOING",
                            "predicates": ["CALLS"],
                        },
                    }
                elif len(trace) == 2:
                    fact_id = trace[-1]["result"]["facts"][0]["fact_id"]
                    action = {
                        "action": "EXPLAIN",
                        "arguments": {
                            "kind": "FACT",
                            "knowledge_ids": [fact_id],
                        },
                    }
                else:
                    action = {"action": "STOP", "arguments": {}}
            else:
                if not trace:
                    action = self._search_inference("Alpha#run invokes")
                elif len(trace) == 1:
                    action = {
                        "action": "SEARCH",
                        "arguments": {
                            "kind": "ENTITY",
                            "query": "Alpha#run",
                            "match_mode": "EXACT",
                            "type_name": "java-method",
                        },
                    }
                elif len(trace) == 2:
                    entity_id = trace[-1]["result"]["items"][0]["entity_id"]
                    action = {
                        "action": "NEIGHBORHOOD",
                        "arguments": {
                            "entity_ids": [entity_id],
                            "direction": "OUTGOING",
                            "predicates": ["CALLS"],
                        },
                    }
                else:
                    action = {"action": "STOP", "arguments": {}}
            self.actions.append(action)
            return action

        if capability == "assess-knowledge-sufficiency":
            claims = list(payload["formal_claims"])
            references_by_kind: dict[str, list[dict[str, str]]] = {
                FACT: [],
                INFERENCE: [],
            }
            for claim in claims:
                for reference in claim["references"]:
                    references_by_kind[str(reference["kind"])].append(reference)
            if self.mode == "mixed":
                return {
                    "items": [
                        {
                            "need_id": "need:fact",
                            "status": SATISFIED,
                            "references": references_by_kind[FACT],
                        },
                        {
                            "need_id": "need:inference",
                            "status": SATISFIED,
                            "references": references_by_kind[INFERENCE],
                        },
                    ]
                }
            references = [
                reference
                for values in references_by_kind.values()
                for reference in values
            ]
            return {
                "items": [
                    {
                        "need_id": "need:answer",
                        "status": SATISFIED if references else GAP,
                        "references": references,
                        "rationale": "" if references else "no formal result found",
                    }
                ]
            }

        if capability == "draft-answer":
            return {"answer": "\n".join(str(item) for item in payload["claims"])}
        raise AssertionError(f"unexpected capability: {capability}")

    @staticmethod
    def _search_inference(query: str) -> dict[str, object]:
        return {
            "action": "SEARCH",
            "arguments": {
                "kind": "INFERENCE",
                "query": query,
                "match_mode": "CONTAINS",
            },
        }


class AgentFormalToolLoopTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.services = ApplicationServices(
            Path(self.temporary.name) / "formal-tool-loop.sqlite3"
        )
        self._publish_fixture()
        self.tool_contexts: list[tuple[str, str]] = []
        self._record_tool_contexts()

        def forbidden_view(*args: object, **kwargs: object):
            raise AssertionError("TaskExecutionAgent used a fixed Semantic View")

        self.services.query_structure = forbidden_view  # type: ignore[method-assign]
        self.services.query_endpoint_structure = forbidden_view  # type: ignore[method-assign]
        self.services.query_semantic_view = forbidden_view  # type: ignore[method-assign]

    def tearDown(self) -> None:
        self.services.close()
        self.temporary.cleanup()

    def test_agent_answers_with_search_neighborhood_and_explain_while_views_disabled(
        self,
    ) -> None:
        provider = _ScriptedToolProvider("fact")
        agent = TaskExecutionAgent(self.services, ModelGateway(provider))

        candidate = agent.execute(self._task("behavior-view"))

        self.assertEqual("Alpha#run calls Beta#save.", candidate.answer)
        self.assertEqual(
            ["SEARCH", "NEIGHBORHOOD", "EXPLAIN", "STOP"],
            [str(item["action"]) for item in provider.actions],
        )
        context = self.services.open_knowledge_context(SCOPE_ID)
        self.assertTrue(self.tool_contexts)
        self.assertEqual(
            {(SCOPE_ID, str(context["snapshot_token"]))},
            set(self.tool_contexts),
        )
        for action in provider.actions:
            arguments = action["arguments"]
            self.assertNotIn("scope_id", arguments)
            self.assertNotIn("snapshot_token", arguments)

    def test_typed_fact_and_inference_references_do_not_depend_on_use_case(self) -> None:
        provider = _ScriptedToolProvider("mixed")
        agent = TaskExecutionAgent(self.services, ModelGateway(provider))

        candidate = agent.execute(self._task("business-view"))

        assert candidate.assessment is not None
        references = {
            item.need_id: {
                (reference.kind, reference.reference_id)
                for reference in item.formal_knowledge_references
            }
            for item in candidate.assessment.items
        }
        self.assertEqual({(FACT, "fact:alpha-calls-beta")}, references["need:fact"])
        self.assertEqual(
            {(INFERENCE, "inference:alpha-flow")},
            references["need:inference"],
        )

    def test_empty_search_produces_gap_instead_of_a_negative_claim(self) -> None:
        provider = _ScriptedToolProvider("empty")
        agent = TaskExecutionAgent(self.services, ModelGateway(provider))
        task = self._task("history-view")
        context = self.services.open_knowledge_context(SCOPE_ID)
        requirement = agent._form_requirement(task, context)

        claims = agent._investigate_formal_knowledge(task, requirement, context)
        assessment = agent._assess_snapshot(
            task, requirement, context, claims
        )

        self.assertEqual((), claims)
        self.assertFalse(assessment.complete)
        self.assertEqual(GAP, assessment.items[0].status)
        self.assertEqual((), assessment.items[0].formal_knowledge_references)
        self.assertFalse(
            any(capability == "draft-answer" for capability, _ in provider.calls)
        )

    def test_repeated_action_stops_before_a_second_tool_execution(self) -> None:
        provider = _ScriptedToolProvider("repeat")
        agent = TaskExecutionAgent(self.services, ModelGateway(provider))
        task = self._task("history-view")
        context = self.services.open_knowledge_context(SCOPE_ID)
        requirement = agent._form_requirement(task, context)

        with self.assertRaisesRegex(
            TaskExecutionError, "repeated formal knowledge action"
        ) as raised:
            agent._investigate_formal_knowledge(task, requirement, context)

        self.assertEqual(
            "REPEATED_KNOWLEDGE_TOOL_ACTION", raised.exception.status
        )
        self.assertEqual(1, len(self.tool_contexts))
        self.assertFalse(
            any(capability == "draft-answer" for capability, _ in provider.calls)
        )

    def test_unique_actions_cannot_exceed_the_step_budget(self) -> None:
        provider = _ScriptedToolProvider("limit")
        agent = TaskExecutionAgent(self.services, ModelGateway(provider))
        task = self._task("history-view")
        context = self.services.open_knowledge_context(SCOPE_ID)
        requirement = agent._form_requirement(task, context)

        with self.assertRaisesRegex(
            TaskExecutionError, "exceeded 12 steps"
        ) as raised:
            agent._investigate_formal_knowledge(task, requirement, context)

        self.assertEqual("KNOWLEDGE_TOOL_STEP_LIMIT", raised.exception.status)
        self.assertEqual(12, len(self.tool_contexts))

    def test_model_cannot_override_agent_injected_scope_or_token(self) -> None:
        provider = _ScriptedToolProvider("scope-forgery")
        agent = TaskExecutionAgent(self.services, ModelGateway(provider))
        task = self._task("history-view")
        context = self.services.open_knowledge_context(SCOPE_ID)
        requirement = agent._form_requirement(task, context)

        with self.assertRaisesRegex(
            TaskExecutionError, "unknown fields"
        ) as raised:
            agent._investigate_formal_knowledge(task, requirement, context)

        self.assertEqual(
            "INVALID_KNOWLEDGE_TOOL_ACTION", raised.exception.status
        )
        self.assertEqual([], self.tool_contexts)

    def test_safe_invalid_action_is_rejected_then_replanned_without_tool_execution(
        self,
    ) -> None:
        provider = _ScriptedToolProvider("recoverable-invalid")
        agent = TaskExecutionAgent(self.services, ModelGateway(provider))
        task = self._task("history-view")
        context = self.services.open_knowledge_context(SCOPE_ID)
        requirement = agent._form_requirement(task, context)

        claims = agent._investigate_formal_knowledge(task, requirement, context)

        self.assertEqual((), claims)
        self.assertEqual(["EXPLAIN", "STOP"], [item["action"] for item in provider.actions])
        self.assertEqual([], self.tool_contexts)
        second_plan = [
            payload
            for capability, payload in provider.calls
            if capability == "plan-formal-knowledge-step"
        ][1]
        rejected = second_plan["tool_trace"][0]
        self.assertEqual("REJECTED", rejected["action"])
        self.assertEqual("INVALID_ACTION", rejected["result"]["status"])

    def test_cross_action_field_is_repairable_but_control_fields_are_not(self) -> None:
        provider = _ScriptedToolProvider("recoverable-cross-shape")
        agent = TaskExecutionAgent(self.services, ModelGateway(provider))
        task = self._task("history-view")
        context = self.services.open_knowledge_context(SCOPE_ID)
        requirement = agent._form_requirement(task, context)

        claims = agent._investigate_formal_knowledge(task, requirement, context)

        self.assertEqual((), claims)
        self.assertEqual(["SEARCH", "STOP"], [item["action"] for item in provider.actions])
        self.assertEqual([], self.tool_contexts)

    def _task(self, use_case: str) -> AgentTask:
        return AgentTask(
            task_id=f"task:{use_case}",
            original_request="What does Alpha#run do?",
            scope_id=SCOPE_ID,
            use_case=use_case,
            parameters={},
            routing_model_call_id="model-call:routing",
        )

    def _record_tool_contexts(self) -> None:
        original_search = self.services.search_knowledge
        original_neighborhood = self.services.query_knowledge_neighborhood
        original_explain = self.services.explain_knowledge_batch

        def search(scope_id: str, snapshot_token: str, *args: object, **kwargs: object):
            self.tool_contexts.append((scope_id, snapshot_token))
            return original_search(scope_id, snapshot_token, *args, **kwargs)

        def neighborhood(
            scope_id: str, snapshot_token: str, *args: object, **kwargs: object
        ):
            self.tool_contexts.append((scope_id, snapshot_token))
            return original_neighborhood(scope_id, snapshot_token, *args, **kwargs)

        def explain(scope_id: str, snapshot_token: str, *args: object, **kwargs: object):
            self.tool_contexts.append((scope_id, snapshot_token))
            return original_explain(scope_id, snapshot_token, *args, **kwargs)

        self.services.search_knowledge = search  # type: ignore[method-assign]
        self.services.query_knowledge_neighborhood = neighborhood  # type: ignore[method-assign]
        self.services.explain_knowledge_batch = explain  # type: ignore[method-assign]

    def _publish_fixture(self) -> None:
        self.services.store.upsert_scope(SCOPE_ID, "formal tool loop")
        content = "Alpha#run invokes Beta#save"
        artifact = SourceArtifact(
            artifact_id="artifact:formal-tool-loop",
            artifact_type="source-text",
            source_id="source:formal-tool-loop",
            scope_id=SCOPE_ID,
            relative_path="src/Alpha.java",
            revision=REVISION,
            content_hash=content_hash(content),
            content=content,
        )
        collection = SourceCollection(
            source_id=artifact.source_id,
            scope_id=SCOPE_ID,
            revision=REVISION,
            artifacts=(artifact,),
        )
        alpha = KnowledgeEntity(
            "entity:alpha", SCOPE_ID, "java-method", "Alpha#run"
        )
        beta = KnowledgeEntity(
            "entity:beta", SCOPE_ID, "java-method", "Beta#save"
        )
        evidence = Evidence(
            evidence_id="evidence:formal-tool-loop",
            artifact_id=artifact.artifact_id,
            scope_id=SCOPE_ID,
            revision=REVISION,
            line_start=1,
            line_end=1,
            quote=content,
            quote_hash=content_hash(content),
        )
        fact = FormalFact(
            fact_id="fact:alpha-calls-beta",
            scope_id=SCOPE_ID,
            revision=REVISION,
            subject_id=alpha.entity_id,
            predicate="CALLS",
            object_id=beta.entity_id,
            evidence_ids=(evidence.evidence_id,),
            proposition="Alpha#run calls Beta#save.",
        )
        inference = FormalInference(
            inference_id="inference:alpha-flow",
            scope_id=SCOPE_ID,
            revision=REVISION,
            inference_type="BEHAVIOR_FLOW",
            statement="Alpha#run invokes Beta#save as its behavior flow.",
            support_fact_ids=(fact.fact_id,),
        )
        snapshot_id = self.services.store.start_snapshot(SCOPE_ID, REVISION)
        self.services.store.save_source_artifacts(snapshot_id, collection)
        self.services.store.publish_knowledge(
            snapshot_id,
            KnowledgePackage(
                scope_id=SCOPE_ID,
                revision=REVISION,
                entities=(alpha, beta),
                evidence=(evidence,),
                facts=(fact,),
                inferences=(inference,),
            ),
        )


if __name__ == "__main__":
    unittest.main()
