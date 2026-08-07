from __future__ import annotations

from pathlib import Path
import re
import subprocess
import tempfile
import unittest
import uuid

from swm_demo.agent_contract import AgentTask
from swm_demo.answer_review_agent import AnswerReviewAgent
from swm_demo.application import ApplicationServices
from swm_demo.ids import stable_id
from swm_demo.knowledge_contract import KnowledgePackage
from swm_demo.knowledge_engine import KnowledgeEngine
from swm_demo.knowledge_requirement import (
    GAP,
    INFERENCE,
    SATISFIED,
    KnowledgeNeed,
    KnowledgeRequirement,
    KnowledgeSufficiencyAssessment,
    KnowledgeSufficiencyItem,
)
from swm_demo.model_gateway import ModelGateway
from swm_demo.task_execution_agent import TaskExecutionAgent, TaskExecutionError


NEED_ID = "need:runtime-cross-file-behavior"
FACT_NEED_ID = "need:runtime-direct-observations"


class _PoisonStructureBuilder:
    def build(self, *args: object, **kwargs: object):
        raise AssertionError("candidate-only path called StructureKnowledgeBuilder")


class _PoisonExtendedBuilder:
    def build(self, *args: object, **kwargs: object):
        raise AssertionError("candidate-only path called ExtendedKnowledgeBuilder.build")

    def build_inferences(self, *args: object, **kwargs: object):
        raise AssertionError(
            "candidate-only path called ExtendedKnowledgeBuilder.build_inferences"
        )


class _InvestigationProvider:
    provider_name = "candidate-only-witness"
    model_name = "runtime-project-investigator"
    model_version = "1"

    _REQUEST_METHOD = re.compile(r"behavior of ([A-Za-z0-9_.#-]+?)(?:\.$|$)")
    _STEP = re.compile(r"STEP ([A-Za-z0-9_.#-]+) validates ([A-Za-z0-9_.#-]+)\.")
    _CALL = re.compile(r"CALL ([A-Za-z0-9_.#-]+) invokes ([A-Za-z0-9_.#-]+)\.")

    def __init__(
        self,
        mode: str,
        premise_fact_ids: tuple[str, ...] = (),
        additional_behavior_targets: tuple[str, ...] = (),
    ):
        self.mode = mode
        self.premise_fact_ids = premise_fact_ids
        self.additional_behavior_targets = additional_behavior_targets
        self.calls: list[tuple[str, dict[str, object]]] = []
        self.proposal_attempts = 0
        self.proposed_statement: str | None = None
        self.observed_premise_ids: tuple[str, ...] = ()
        self.scope_id: str | None = None

    def invoke(
        self, capability: str, payload: dict[str, object]
    ) -> dict[str, object]:
        self.calls.append((capability, payload))
        if capability == "derive-build-intent":
            return self._build_intent(payload)
        if capability == "propose-knowledge-candidates":
            self.proposal_attempts += 1
            if self.mode == "empty":
                return self._empty_proposal(payload)
            if self.mode in {"inference", "mixed-inference"}:
                return self._inference_proposal(payload)
            return self._source_fact_proposal(payload)
        raise AssertionError(f"unexpected capability: {capability}")

    def _build_intent(self, payload: dict[str, object]) -> dict[str, object]:
        method = self._requested_method(str(payload["original_request"]))
        self.scope_id = str(payload["scope_id"])
        target_method = (
            f"unrelated-{method}" if self.mode == "wrong-target" else method
        )
        requires_inference = self.mode in {
            "inference",
            "mixed-inference",
            "same-bundle",
        }
        return {
            "target_revision": payload["target_revision"],
            "artifact_request": {
                "build_profile": "candidate-only",
                "include_globs": (
                    []
                    if self.mode in {"inference", "mixed-inference"}
                    else ["rules.witness", "calls.witness"]
                ),
                "git_commit_ids": [],
                "derive_java_ast": False,
                "revision": payload["target_revision"],
                "commit_revisions": [],
                "comparisons": [],
            },
            "knowledge_target": {
                "behavior_methods": [
                    [target_method, "runtime-selected method"],
                    *(
                        [selector, "explicit additional runtime method"]
                        for selector in self.additional_behavior_targets
                    ),
                ],
                "business_constraint_methods": [],
                "capability_modules": [],
                "history_commits": [],
                "required_inference_types": (
                    ["BEHAVIOR_FLOW"] if requires_inference else []
                ),
                "premise_fact_ids": list(self.premise_fact_ids),
                "premise_inference_ids": [],
            },
        }

    @staticmethod
    def _empty_proposal(payload: dict[str, object]) -> dict[str, object]:
        return {
            "schema_version": "candidate-proposal.v2",
            "entities": [],
            "evidence": [],
            "fact_candidates": [],
            "inference_candidates": [],
            "covered_need_ids": list(payload["gap_need_ids"]),
            "unresolved_need_ids": [],
        }

    def _source_fact_proposal(
        self, payload: dict[str, object]
    ) -> dict[str, object]:
        artifacts = payload.get("source_artifacts")
        if not isinstance(artifacts, list):
            raise AssertionError("candidate proposal did not receive source artifacts")
        by_path = {
            str(item["relative_path"]): item
            for item in artifacts
            if isinstance(item, dict)
        }
        if set(by_path) != {"rules.witness", "calls.witness"}:
            raise AssertionError(f"unexpected runtime source files: {sorted(by_path)}")

        rule_lines = self._numbered_lines(by_path["rules.witness"])
        call_lines = self._numbered_lines(by_path["calls.witness"])
        if len(rule_lines) != 1 or len(call_lines) != 2:
            raise AssertionError("runtime fixture has an unexpected line count")
        rule_text = rule_lines[0]
        call_line = (
            2
            if self.mode in {"mixed-base", "unauthorized-extra"}
            else 1
        )
        call_text = call_lines[call_line - 1]
        rule = self._STEP.fullmatch(rule_text)
        call = self._CALL.fullmatch(call_text)
        if rule is None or call is None:
            raise AssertionError("runtime source does not match the witness grammar")
        method, policy = rule.groups()
        call_method, sink = call.groups()
        if (
            self.mode not in {"mixed-base", "unauthorized-extra"}
            and method != call_method
        ):
            raise AssertionError("runtime source does not describe one cross-file method")
        call_subject = "method"
        extra_entities: list[dict[str, str]] = []
        if call_method != method:
            call_subject = "call-method"
            extra_entities.append(
                {
                    "key": call_subject,
                    "entity_type": "runtime-method",
                    "name": call_method,
                }
            )

        facts = [
            {
                "key": "declared-step",
                "subject": "method",
                "predicate": "DECLARES_STEP",
                "object": "policy",
                "evidence": ["rule-line"],
                "proposition": rule_text,
            },
            {
                "key": "implementation-call",
                "subject": call_subject,
                "predicate": "CALLS",
                "object": "sink",
                "evidence": ["call-line"],
                "proposition": call_text,
            },
        ]
        inferences: list[dict[str, object]] = []
        if self.mode == "same-bundle":
            if self.scope_id is None:
                raise AssertionError("derive-build-intent was not called first")
            subject_id = stable_id(
                "entity", self.scope_id, "runtime-method", method
            )
            policy_id = stable_id(
                "entity", self.scope_id, "runtime-policy", policy
            )
            sink_id = stable_id("entity", self.scope_id, "runtime-sink", sink)
            same_bundle_fact_ids = (
                stable_id(
                    "fact",
                    self.scope_id,
                    subject_id,
                    "DECLARES_STEP",
                    policy_id,
                    rule_text,
                ),
                stable_id(
                    "fact",
                    self.scope_id,
                    subject_id,
                    "CALLS",
                    sink_id,
                    call_text,
                ),
            )
            inferences.append(
                {
                    "key": "illegal-same-bundle-inference",
                    "inference_type": "BEHAVIOR_FLOW",
                    "statement": f"{method} validates {policy} and invokes {sink}.",
                    "premise_fact_ids": list(same_bundle_fact_ids),
                    "premise_inference_ids": [],
                }
            )

        return {
            "schema_version": "candidate-proposal.v2",
            "entities": [
                {
                    "key": "method",
                    "entity_type": "runtime-method",
                    "name": method,
                },
                {
                    "key": "policy",
                    "entity_type": "runtime-policy",
                    "name": policy,
                },
                {
                    "key": "sink",
                    "entity_type": "runtime-sink",
                    "name": sink,
                },
                *extra_entities,
            ],
            "evidence": [
                {
                    "key": "rule-line",
                    "artifact_id": by_path["rules.witness"]["artifact_id"],
                    "line_start": 1,
                    "line_end": 1,
                },
                {
                    "key": "call-line",
                    "artifact_id": by_path["calls.witness"]["artifact_id"],
                    "line_start": call_line,
                    "line_end": call_line,
                },
            ],
            "fact_candidates": facts,
            "inference_candidates": inferences,
            "covered_need_ids": list(payload["gap_need_ids"]),
            "unresolved_need_ids": [],
        }

    def _inference_proposal(
        self, payload: dict[str, object]
    ) -> dict[str, object]:
        if payload.get("source_artifacts") != []:
            raise AssertionError("Inference phase unexpectedly received source files")
        premises = payload.get("formal_premises")
        if not isinstance(premises, dict):
            raise AssertionError("Inference phase did not receive formal premises")
        facts = premises.get("facts")
        if not isinstance(facts, list) or len(facts) != 2:
            raise AssertionError("Inference phase requires exactly two Base Facts")
        premise_ids = tuple(str(item["fact_id"]) for item in facts)
        if set(premise_ids) != set(self.premise_fact_ids):
            raise AssertionError("Inference phase premises differ from frozen target")
        predicates = {str(item["predicate"]): item for item in facts}
        step = predicates.get("DECLARES_STEP")
        call = predicates.get("CALLS")
        if step is None or call is None:
            raise AssertionError("Base premises omit step or implementation call")
        if (
            self.mode != "mixed-inference"
            and step["subject_name"] != call["subject_name"]
        ):
            raise AssertionError("Base premises describe different methods")

        statement = (
            f"{step['subject_name']} validates {step['object_name']} and "
            f"invokes {call['object_name']}."
        )
        self.proposed_statement = statement
        self.observed_premise_ids = premise_ids
        return {
            "schema_version": "candidate-proposal.v2",
            "entities": [],
            "evidence": [],
            "fact_candidates": [],
            "inference_candidates": [
                {
                    "key": "cross-file-behavior",
                    "inference_type": "BEHAVIOR_FLOW",
                    "statement": statement,
                    "premise_fact_ids": list(premise_ids),
                    "premise_inference_ids": [],
                }
            ],
            "covered_need_ids": list(payload["gap_need_ids"]),
            "unresolved_need_ids": [],
        }

    @classmethod
    def _requested_method(cls, request: str) -> str:
        matched = cls._REQUEST_METHOD.search(request)
        if matched is None:
            raise AssertionError(f"request does not select a method: {request}")
        return matched.group(1)

    @staticmethod
    def _numbered_lines(artifact: dict[str, object]) -> list[str]:
        if "content" in artifact:
            raise AssertionError("provider received unnumbered raw source content")
        lines = artifact.get("content_lines")
        if not isinstance(lines, list) or not lines:
            raise AssertionError("runtime witness file has no numbered lines")
        result: list[str] = []
        for number, line in enumerate(lines, start=1):
            if not isinstance(line, dict) or line.get("line_number") != number:
                raise AssertionError("runtime witness line is not stably numbered")
            result.append(str(line["text"]))
        return result


class _FreshAnswerProvider:
    provider_name = "candidate-only-answer"
    model_name = "fresh-formal-only-answerer"
    model_version = "1"

    def __init__(self):
        self.calls: list[tuple[str, dict[str, object]]] = []

    def invoke(
        self, capability: str, payload: dict[str, object]
    ) -> dict[str, object]:
        self.calls.append((capability, payload))
        self._assert_formal_only(payload)
        if capability == "plan-formal-knowledge-step":
            trace = payload["tool_trace"]
            if trace:
                return {"action": "STOP", "arguments": {}}
            method = _InvestigationProvider._requested_method(
                str(payload["original_request"])
            )
            return {
                "action": "SEARCH",
                "arguments": {
                    "kind": "INFERENCE",
                    "query": method,
                    "match_mode": "CONTAINS",
                    "type_name": "BEHAVIOR_FLOW",
                    "limit": 10,
                    "cursor": 0,
                },
            }
        if capability == "assess-knowledge-sufficiency":
            references = [
                reference
                for claim in payload["formal_claims"]
                for reference in claim["references"]
                if reference["kind"] == INFERENCE
            ]
            if len(references) != 1:
                raise AssertionError(
                    "fresh answer Provider did not discover one formal Inference"
                )
            return {
                "items": [
                    {
                        "need_id": item["need_id"],
                        "status": SATISFIED,
                        "references": references,
                        "rationale": "published Inference satisfies the Need",
                    }
                    for item in payload["requirement"]
                ]
            }
        if capability == "draft-answer":
            return {"answer": "\n".join(str(item) for item in payload["claims"])}
        raise AssertionError(f"unexpected answer capability: {capability}")

    @staticmethod
    def _assert_formal_only(payload: dict[str, object]) -> None:
        forbidden = {
            "artifact",
            "artifacts",
            "artifact_content",
            "candidate_bundle",
            "content_lines",
            "evidence_quote",
            "formal_premises",
            "source_artifacts",
            "source_content",
        }

        def walk(value: object) -> None:
            if isinstance(value, dict):
                for key, nested in value.items():
                    if str(key).lower() in forbidden or "quote" in str(key).lower():
                        raise AssertionError(
                            f"fresh answer Provider received source field: {key}"
                        )
                    walk(nested)
            elif isinstance(value, (list, tuple)):
                for nested in value:
                    walk(nested)

        walk(payload)


class _IndependentReviewProvider:
    provider_name = "candidate-only-review"
    model_name = "independent-formal-reviewer"
    model_version = "1"

    def __init__(self):
        self.calls: list[tuple[str, dict[str, object]]] = []

    def invoke(
        self, capability: str, payload: dict[str, object]
    ) -> dict[str, object]:
        self.calls.append((capability, payload))
        _FreshAnswerProvider._assert_formal_only(payload)
        if capability != "review-answer":
            raise AssertionError(f"unexpected review capability: {capability}")
        claims = tuple(str(item) for item in payload["candidate_claims"])
        formal = set(str(item) for item in payload["formal_propositions"])
        authoritative = tuple(str(item) for item in payload["authoritative_claims"])
        if not claims or not set(claims).issubset(formal) or claims != authoritative:
            return {"decision": "REJECT", "unsupported_claims": list(claims)}
        return {"decision": "PASS", "unsupported_claims": []}


class CandidateOnlyCapabilityWitnessTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        self.repository = root / "runtime-unfamiliar-project"
        self.repository.mkdir()
        suffix = uuid.uuid4().hex[:12]
        self.scope_id = f"system:candidate-only-witness:{suffix}"
        self.method = f"FluxGate_{suffix}#transit"
        self.policy = f"Policy_{suffix}"
        self.sink = f"Vault_{suffix}#accept"
        self.decoy_method = f"DecoyGate_{suffix}#bypass"
        self.decoy_sink = f"DecoyVault_{suffix}#discard"
        self.request = f"Explain the behavior of {self.method}."

        self._git("init", "--quiet")
        self._git("config", "user.name", "Runtime Witness")
        self._git("config", "user.email", "runtime-witness@example.com")
        (self.repository / "rules.witness").write_text(
            f"STEP {self.method} validates {self.policy}.\n", encoding="utf-8"
        )
        (self.repository / "calls.witness").write_text(
            f"CALL {self.method} invokes {self.sink}.\n"
            f"CALL {self.decoy_method} invokes {self.decoy_sink}.\n",
            encoding="utf-8",
        )
        self._git("add", "rules.witness", "calls.witness")
        self._git("commit", "--quiet", "-m", "runtime unfamiliar behavior")
        self.revision = self._git("rev-parse", "HEAD")

        engine = KnowledgeEngine(
            builder=_PoisonStructureBuilder(),  # type: ignore[arg-type]
            extended_builder=_PoisonExtendedBuilder(),  # type: ignore[arg-type]
        )
        self.services = ApplicationServices(root / "knowledge.sqlite3", engine)
        self.services.configure_scope(
            self.scope_id,
            "runtime candidate-only witness",
            self.repository,
            self.revision,
        )
        empty_snapshot = self.services.knowledge_engine.begin_update(
            self.scope_id, self.revision
        )
        self.services.store.publish_knowledge(
            empty_snapshot,
            KnowledgePackage(
                scope_id=self.scope_id,
                revision=self.revision,
                entities=(),
                evidence=(),
                facts=(),
                inferences=(),
            ),
        )
        self.baseline_snapshot_id = empty_snapshot
        self.task = AgentTask(
            task_id=f"task:candidate-only-witness:{suffix}",
            original_request=self.request,
            scope_id=self.scope_id,
            use_case="runtime-behavior",
            parameters={},
            routing_model_call_id="model-call:test-routing",
        )
        self.requirement = KnowledgeRequirement(
            requirement_id=f"requirement:candidate-only-witness:{suffix}",
            task_id=self.task.task_id,
            scope_id=self.scope_id,
            knowledge_context_reference=self.revision,
            needs=(
                KnowledgeNeed(
                    need_id=NEED_ID,
                    question=self.request,
                    sufficiency_criterion=(
                        "An admitted BEHAVIOR_FLOW Inference combines direct Facts "
                        "from both runtime source files."
                    ),
                ),
            ),
            formation_model_call_id="model-call:test-requirement",
        )
        self.fact_requirement = KnowledgeRequirement(
            requirement_id=f"requirement:candidate-only-facts:{suffix}",
            task_id=self.task.task_id,
            scope_id=self.scope_id,
            knowledge_context_reference=self.revision,
            needs=(
                KnowledgeNeed(
                    need_id=FACT_NEED_ID,
                    question=(
                        f"Which direct observations describe {self.method} across "
                        "the runtime source files?"
                    ),
                    sufficiency_criterion=(
                        "Two admitted direct Facts are anchored independently to "
                        "the runtime rule and call files."
                    ),
                ),
            ),
            formation_model_call_id="model-call:test-fact-requirement",
        )

    def tearDown(self) -> None:
        self.services.close()
        self.temporary.cleanup()

    def test_two_phase_candidate_only_publication_answers_from_formal_snapshot(
        self,
    ) -> None:
        first_context = self.services.open_knowledge_context(self.scope_id)
        fact_provider = _InvestigationProvider("facts")
        first = self._run_investigation(
            fact_provider, first_context, self.fact_requirement
        )

        if first.status != "PUBLISHED":
            self.fail(self._last_failure_reason())
        self.assertEqual(self.baseline_snapshot_id, first.previous_snapshot_id)
        self._cleanup_investigation(first.run_id)
        facts = self.services.knowledge_engine.read_facts(self.scope_id)
        self.assertEqual({"DECLARES_STEP", "CALLS"}, {item["predicate"] for item in facts})
        fact_ids = tuple(sorted(str(item["fact_id"]) for item in facts))
        evidence_paths = {
            str(item["relative_path"])
            for fact_id in fact_ids
            for item in self.services.explain_fact(self.scope_id, fact_id)["evidence"]
        }
        self.assertEqual({"rules.witness", "calls.witness"}, evidence_paths)

        second_context = self.services.open_knowledge_context(self.scope_id)
        inference_provider = _InvestigationProvider("inference", fact_ids)
        second = self._run_investigation(inference_provider, second_context)

        if second.status != "PUBLISHED":
            self.fail(self._last_failure_reason())
        self.assertEqual(first.published_snapshot_id, second.previous_snapshot_id)
        self._cleanup_investigation(second.run_id)
        self.assertEqual(set(fact_ids), set(inference_provider.observed_premise_ids))
        inferences = self.services.knowledge_engine.read_inferences(self.scope_id)
        self.assertEqual(1, len(inferences))
        inference_id = str(inferences[0]["inference_id"])
        self.assertEqual(inference_provider.proposed_statement, inferences[0]["statement"])
        explanation = self.services.explain_inference(self.scope_id, inference_id)
        self.assertEqual(
            set(fact_ids),
            {str(item["fact_id"]) for item in explanation["supporting_facts"]},
        )
        self.assertIn(self.method, str(inferences[0]["statement"]))
        self.assertIn(self.policy, str(inferences[0]["statement"]))
        self.assertIn(self.sink, str(inferences[0]["statement"]))

        def source_forbidden(*args: object, **kwargs: object):
            raise AssertionError("formal-only answer attempted Source Integration")

        self.services.source_integration.collect_sources = source_forbidden  # type: ignore[method-assign]
        self.services.source_integration.collect_structure_sources = source_forbidden  # type: ignore[method-assign]
        self.services.source_integration.record_artifacts = source_forbidden  # type: ignore[method-assign]

        answer_provider = _FreshAnswerProvider()
        answer_agent = TaskExecutionAgent(
            self.services, ModelGateway(answer_provider, self.services.store)
        )
        candidate = answer_agent.answer_from_formal_snapshot(
            self.task, self.requirement
        )

        self.assertIs(candidate.requirement, self.requirement)
        self.assertTrue(candidate.assessment.complete)  # type: ignore[union-attr]
        assert candidate.assessment is not None
        for item in candidate.assessment.items:
            self.assertEqual(
                ((INFERENCE, inference_id),),
                tuple(
                    (reference.kind, reference.reference_id)
                    for reference in item.formal_knowledge_references
                ),
            )
        self.assertEqual((inference_id,), candidate.claims[0].knowledge_reference_ids)
        self.assertIn(self.method, candidate.answer)
        self.assertIn(self.policy, candidate.answer)
        self.assertIn(self.sink, candidate.answer)

        review_provider = _IndependentReviewProvider()
        self.assertIsNot(answer_provider, review_provider)
        review = AnswerReviewAgent(
            self.services, ModelGateway(review_provider, self.services.store)
        ).review(self.request, self.task, candidate)
        self.assertEqual("PASS", review.decision)
        self.assertEqual(
            {
                "plan-formal-knowledge-step",
                "assess-knowledge-sufficiency",
                "draft-answer",
            },
            {capability for capability, _ in answer_provider.calls},
        )
        self.assertEqual(
            ["review-answer"],
            [capability for capability, _ in review_provider.calls],
        )

    def test_empty_candidate_cannot_publish_or_satisfy_the_need(self) -> None:
        current = self.services.open_knowledge_context(self.scope_id)
        result = self._run_investigation(
            _InvestigationProvider("empty"), current, self.fact_requirement
        )
        self._cleanup_investigation(result.run_id)
        failure = self._last_failure_reason()

        self.assertEqual("FAILED", result.status)
        self.assertEqual(
            self.baseline_snapshot_id,
            self.services.current_snapshot(self.scope_id)["snapshot_id"],
        )
        self.assertIn("direct Facts are not aligned", failure)

    def test_wrong_target_and_mixed_owner_premises_cannot_publish(self) -> None:
        current = self.services.open_knowledge_context(self.scope_id)
        result = self._run_investigation(
            _InvestigationProvider("wrong-target"),
            current,
            self.fact_requirement,
        )
        self._cleanup_investigation(result.run_id)
        failure = self._last_failure_reason()

        self.assertEqual("FAILED", result.status)
        self.assertEqual(2, len(result.rejected_candidate_ids))
        self.assertEqual(
            self.baseline_snapshot_id,
            self.services.current_snapshot(self.scope_id)["snapshot_id"],
        )
        self.assertIn("direct Facts are not aligned", failure)
        self.assertIn("unrelated-", failure)

        unauthorized_context = self.services.open_knowledge_context(self.scope_id)
        unauthorized = self._run_investigation(
            _InvestigationProvider("unauthorized-extra"),
            unauthorized_context,
            self.fact_requirement,
        )
        self._cleanup_investigation(unauthorized.run_id)
        self.assertEqual("FAILED", unauthorized.status)
        self.assertEqual(
            self.baseline_snapshot_id,
            self.services.current_snapshot(self.scope_id)["snapshot_id"],
        )
        self.assertIn("outside the exact Build Target", self._last_failure_reason())

        mixed_base_context = self.services.open_knowledge_context(self.scope_id)
        mixed_base_provider = _InvestigationProvider(
            "mixed-base",
            additional_behavior_targets=(self.decoy_method,),
        )
        mixed_base = self._run_investigation(
            mixed_base_provider,
            mixed_base_context,
            self.fact_requirement,
        )
        if mixed_base.status != "PUBLISHED":
            self.fail(self._last_failure_reason())
        self._cleanup_investigation(mixed_base.run_id)
        mixed_facts = self.services.knowledge_engine.read_facts(self.scope_id)
        mixed_fact_ids = tuple(
            sorted(str(item["fact_id"]) for item in mixed_facts)
        )
        self.assertEqual(2, len(mixed_fact_ids))
        self.assertEqual(
            {self.method, self.decoy_method},
            {
                str(self.services.explain_fact(self.scope_id, fact_id)["subject_name"])
                for fact_id in mixed_fact_ids
            },
        )

        mixed_context = self.services.open_knowledge_context(self.scope_id)
        mixed_result = self._run_investigation(
            _InvestigationProvider("mixed-inference", mixed_fact_ids),
            mixed_context,
        )
        self._cleanup_investigation(mixed_result.run_id)
        self.assertEqual("FAILED", mixed_result.status)
        self.assertEqual(
            mixed_base.published_snapshot_id,
            self.services.current_snapshot(self.scope_id)["snapshot_id"],
        )
        self.assertIn("different method owners", self._last_failure_reason())

    def test_same_bundle_fact_cannot_be_an_inference_premise(self) -> None:
        current = self.services.open_knowledge_context(self.scope_id)
        provider = _InvestigationProvider("same-bundle")

        try:
            with self.assertRaises(TaskExecutionError) as raised:
                self._run_investigation(provider, current)
        finally:
            for run_id in tuple(self.services._investigations):  # type: ignore[attr-defined]
                self._cleanup_investigation(run_id)

        self.assertEqual("INVALID_CANDIDATE_PROPOSAL", raised.exception.status)
        self.assertIn("same Bundle", str(raised.exception))
        self.assertEqual(3, provider.proposal_attempts)
        self.assertEqual(
            self.baseline_snapshot_id,
            self.services.current_snapshot(self.scope_id)["snapshot_id"],
        )

    def _run_investigation(
        self,
        provider: _InvestigationProvider,
        context: dict[str, object],
        requirement: KnowledgeRequirement | None = None,
    ):
        active_requirement = requirement or self.requirement
        active_need_id = active_requirement.needs[0].need_id
        assessment = KnowledgeSufficiencyAssessment(
            assessment_id=f"assessment:{uuid.uuid4()}",
            requirement=active_requirement,
            snapshot_id=str(context["snapshot_id"]),
            knowledge_context_reference=str(context["revision"]),
            items=(
                KnowledgeSufficiencyItem(
                    need_id=active_need_id,
                    status=GAP,
                    rationale="the required formal knowledge is absent",
                ),
            ),
            assessment_model_call_id="model-call:test-gap-assessment",
        )
        return TaskExecutionAgent(
            self.services, ModelGateway(provider, self.services.store)
        )._run_investigation(self.task, assessment, context)

    def _cleanup_investigation(self, run_id: str) -> None:
        handle = self.services.investigation_handle(run_id)
        if handle.state.value == "OPEN":
            self.services.abort_investigation(run_id)
        self.services.release_investigation(run_id)

    def _last_failure_reason(self) -> str:
        row = self.services.store.connection.execute(
            """
            SELECT failure_reason FROM snapshots
            WHERE scope_id = ? AND status = 'FAILED'
            ORDER BY rowid DESC LIMIT 1
            """,
            (self.scope_id,),
        ).fetchone()
        self.assertIsNotNone(row)
        return str(row["failure_reason"])

    def _git(self, *args: str) -> str:
        completed = subprocess.run(
            ["git", *args],
            cwd=self.repository,
            check=True,
            capture_output=True,
            text=True,
        )
        return completed.stdout.strip()


if __name__ == "__main__":
    unittest.main()
