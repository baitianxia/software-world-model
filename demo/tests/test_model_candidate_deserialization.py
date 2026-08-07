from __future__ import annotations

from pathlib import Path
import subprocess
import tempfile
import unittest

from swm_demo.agent_contract import AgentTask
from swm_demo.application import ApplicationServices
from swm_demo.ids import content_hash, stable_id
from swm_demo.knowledge_requirement import (
    GAP,
    KnowledgeNeed,
    KnowledgeRequirement,
    KnowledgeSufficiencyAssessment,
    KnowledgeSufficiencyItem,
)
from swm_demo.model_gateway import ModelGateway
from swm_demo.task_execution_agent import (
    TaskExecutionAgent,
    TaskExecutionError,
    _parse_knowledge_build_target,
)


SCOPE_ID = "system:model-candidate-deserialization"
NEED_ID = "need:direct-observation"
DIRECT_PROPOSITION = "service calls repository.save"


class _CandidateProvider:
    provider_name = "candidate-test"
    model_name = "candidate-test-double"
    model_version = "1"

    def __init__(
        self,
        *,
        base_revision: str,
        target_revision: str,
        proposition: str,
        line_end: int = 1,
        request_revision: str | None = None,
    ):
        self.base_revision = base_revision
        self.target_revision = target_revision
        self.proposition = proposition
        self.line_end = line_end
        self.request_revision = request_revision or target_revision
        self.proposal_payload: dict[str, object] | None = None
        self.observation_artifact_id: str | None = None

    def invoke(
        self, capability: str, payload: dict[str, object]
    ) -> dict[str, object]:
        if capability == "derive-build-intent":
            return {
                "target_revision": payload["target_revision"],
                "artifact_request": {
                    "build_profile": "structure-core",
                    "include_globs": ["pom.xml", "observation.txt"],
                    "git_commit_ids": [],
                    "derive_java_ast": False,
                    "revision": self.request_revision,
                    "commit_revisions": [self.target_revision],
                    "comparisons": [
                        {
                            "base_revision": self.base_revision,
                            "target_revision": self.target_revision,
                        }
                    ],
                },
                "knowledge_target": {},
            }
        if capability == "propose-knowledge-candidates":
            self.proposal_payload = payload
            source_artifacts = payload.get("source_artifacts")
            if not isinstance(source_artifacts, list):
                raise AssertionError("proposal did not receive Source Artifacts")
            by_path = {
                str(item["relative_path"]): item
                for item in source_artifacts
                if isinstance(item, dict)
            }
            observation = by_path.get("observation.txt")
            if observation is None:
                raise AssertionError("proposal did not receive observation.txt")
            if "content" in observation:
                raise AssertionError("proposal received unnumbered raw content")
            if observation.get("content_lines") != [
                {"line_number": 1, "text": DIRECT_PROPOSITION}
            ]:
                raise AssertionError("proposal did not receive stable numbered lines")
            if "pom.xml" not in by_path:
                raise AssertionError("proposal did not receive the collected POM")
            if not any(
                item.get("artifact_type") == "git-commit"
                for item in source_artifacts
                if isinstance(item, dict)
            ):
                raise AssertionError("commit_revisions was not collected")
            comparison = next(
                (
                    item
                    for item in source_artifacts
                    if isinstance(item, dict)
                    and item.get("artifact_type") == "git-diff"
                ),
                None,
            )
            if comparison is None or comparison.get("comparison") != {
                "base_revision": self.base_revision,
                "target_revision": self.target_revision,
            }:
                raise AssertionError("Revision comparison was not exposed")
            self.observation_artifact_id = str(observation["artifact_id"])
            return {
                "schema_version": "candidate-proposal.v1",
                "entities": [
                    {
                        "key": "service",
                        "entity_type": "service",
                        "name": "ExampleService",
                    },
                    {
                        "key": "operation",
                        "entity_type": "operation",
                        "name": "repository.save",
                    },
                ],
                "evidence": [
                    {
                        "key": "observation",
                        "artifact_id": self.observation_artifact_id,
                        "line_start": 1,
                        "line_end": self.line_end,
                    }
                ],
                "fact_candidates": [
                    {
                        "key": "direct-fact",
                        "subject": "service",
                        "predicate": "CALLS_OPERATION",
                        "object": "operation",
                        "evidence": ["observation"],
                        "proposition": self.proposition,
                    }
                ],
                "inference_candidates": [],
                "covered_need_ids": list(payload["gap_need_ids"]),
                "unresolved_need_ids": [],
            }
        raise AssertionError(f"unexpected capability: {capability}")


class _RepairingCandidateProvider(_CandidateProvider):
    def __init__(self, **kwargs: object):
        super().__init__(**kwargs)
        self.proposal_attempts = 0
        self.feedback_payload: dict[str, object] | None = None

    def invoke(
        self, capability: str, payload: dict[str, object]
    ) -> dict[str, object]:
        output = super().invoke(capability, payload)
        if capability != "propose-knowledge-candidates":
            return output
        self.proposal_attempts += 1
        fact_candidates = output["fact_candidates"]
        if self.proposal_attempts == 1:
            fact_candidates[0]["object"] = "unknown-local-key"  # type: ignore[index]
            return output
        self.feedback_payload = payload
        return output


class _AlwaysInvalidCandidateProvider(_CandidateProvider):
    def invoke(
        self, capability: str, payload: dict[str, object]
    ) -> dict[str, object]:
        output = super().invoke(capability, payload)
        if capability == "propose-knowledge-candidates":
            fact_candidates = output["fact_candidates"]
            fact_candidates[0]["object"] = "unknown-local-key"  # type: ignore[index]
        return output


class ModelCandidateDeserializationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        temporary_path = Path(self.temporary.name)
        self.repository = temporary_path / "repository"
        self.repository.mkdir()
        self._git("init", "--quiet")
        self._git("config", "user.name", "Candidate Test")
        self._git("config", "user.email", "candidate-test@example.com")
        (self.repository / "pom.xml").write_text(
            """<project>
  <modelVersion>4.0.0</modelVersion>
  <groupId>fixture</groupId>
  <artifactId>candidate-test</artifactId>
  <version>1</version>
</project>
""",
            encoding="utf-8",
        )
        (self.repository / "observation.txt").write_text(
            "placeholder observation\n", encoding="utf-8"
        )
        self._git("add", "pom.xml", "observation.txt")
        self._git("commit", "--quiet", "-m", "baseline")
        self.base_revision = self._git("rev-parse", "HEAD")
        (self.repository / "observation.txt").write_text(
            DIRECT_PROPOSITION + "\n", encoding="utf-8"
        )
        self._git("add", "observation.txt")
        self._git("commit", "--quiet", "-m", "add direct observation")
        self.target_revision = self._git("rev-parse", "HEAD")

        self.services = ApplicationServices(temporary_path / "knowledge.sqlite3")
        self.services.configure_scope(
            SCOPE_ID,
            "model candidate deserialization",
            self.repository,
            self.target_revision,
        )
        baseline = self.services.update_knowledge(SCOPE_ID, "structure-core")
        self.baseline_snapshot_id = str(baseline["snapshot_id"])
        self.context = self.services.open_knowledge_context(SCOPE_ID)
        self.task = AgentTask(
            task_id="task:model-candidate-deserialization",
            original_request="What direct operation is observed?",
            scope_id=SCOPE_ID,
            use_case="generic",
            parameters={},
            routing_model_call_id="model-call:routing",
        )
        requirement = KnowledgeRequirement(
            requirement_id="requirement:model-candidate-deserialization",
            task_id=self.task.task_id,
            scope_id=SCOPE_ID,
            knowledge_context_reference=str(self.context["revision"]),
            needs=(
                KnowledgeNeed(
                    need_id=NEED_ID,
                    question="What direct operation is observed?",
                    sufficiency_criterion="An admitted direct Fact answers it.",
                ),
            ),
            formation_model_call_id="model-call:requirement",
        )
        self.assessment = KnowledgeSufficiencyAssessment(
            assessment_id="assessment:model-candidate-deserialization",
            requirement=requirement,
            snapshot_id=str(self.context["snapshot_id"]),
            knowledge_context_reference=str(self.context["revision"]),
            items=(
                KnowledgeSufficiencyItem(
                    need_id=NEED_ID,
                    status=GAP,
                    rationale="the direct Fact is absent",
                ),
            ),
            assessment_model_call_id="model-call:assessment",
        )

    def tearDown(self) -> None:
        self.services.close()
        self.temporary.cleanup()

    def _git(self, *args: str) -> str:
        completed = subprocess.run(
            ["git", *args],
            cwd=self.repository,
            check=True,
            capture_output=True,
            text=True,
        )
        return completed.stdout.strip()

    def _run(
        self,
        proposition: str,
        *,
        line_end: int = 1,
        request_revision: str | None = None,
    ):
        provider = _CandidateProvider(
            base_revision=self.base_revision,
            target_revision=self.target_revision,
            proposition=proposition,
            line_end=line_end,
            request_revision=request_revision,
        )
        gateway = ModelGateway(provider, self.services.store)
        agent = TaskExecutionAgent(self.services, gateway)
        result = agent._run_investigation(
            self.task, self.assessment, self.context
        )
        return result, provider

    def test_model_direct_fact_is_deserialized_and_admitted(self) -> None:
        result, provider = self._run(DIRECT_PROPOSITION)

        self.assertEqual("PUBLISHED", result.status)
        self.assertNotEqual(
            self.baseline_snapshot_id,
            self.services.current_snapshot(SCOPE_ID)["snapshot_id"],
        )
        proposal_call = self.services.store.connection.execute(
            """
            SELECT model_call_id FROM model_calls
            WHERE capability = 'propose-knowledge-candidates'
            ORDER BY rowid DESC LIMIT 1
            """
        ).fetchone()
        subject_id = stable_id("entity", SCOPE_ID, "service", "ExampleService")
        object_id = stable_id(
            "entity", SCOPE_ID, "operation", "repository.save"
        )
        expected_fact_id = stable_id(
            "fact",
            SCOPE_ID,
            subject_id,
            "CALLS_OPERATION",
            object_id,
            DIRECT_PROPOSITION,
        )
        fact = next(
            item
            for item in self.services.knowledge_engine.read_facts(SCOPE_ID)
            if item["fact_id"] == expected_fact_id
        )
        self.assertEqual(proposal_call["model_call_id"], fact["model_call_id"])
        self.assertEqual(self.target_revision, fact["revision"])
        explanation = self.services.explain_fact(SCOPE_ID, expected_fact_id)
        observation = explanation["evidence"][0]
        quote_hash = content_hash(DIRECT_PROPOSITION)
        self.assertEqual(DIRECT_PROPOSITION, observation["quote"])
        self.assertEqual(quote_hash, observation["quote_hash"])
        self.assertEqual(
            stable_id(
                "evidence",
                provider.observation_artifact_id,
                1,
                1,
                quote_hash,
            ),
            observation["evidence_id"],
        )

    def test_knowledge_target_rejects_a_malformed_method_pair(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            r"exactly \[method_selector, human_readable_label\]",
        ):
            _parse_knowledge_build_target(
                {"behavior_methods": [["only-one-element"]]}
            )

    def test_knowledge_target_rejects_unknown_fields(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown fields"):
            _parse_knowledge_build_target({"scope_id": "model-controlled"})

    def test_invalid_local_reference_can_be_repaired_in_same_investigation(self) -> None:
        provider = _RepairingCandidateProvider(
            base_revision=self.base_revision,
            target_revision=self.target_revision,
            proposition=DIRECT_PROPOSITION,
        )
        gateway = ModelGateway(provider, self.services.store)
        result = TaskExecutionAgent(self.services, gateway)._run_investigation(
            self.task, self.assessment, self.context
        )

        self.assertEqual("PUBLISHED", result.status)
        self.assertEqual(2, provider.proposal_attempts)
        self.assertIsNotNone(provider.feedback_payload)
        feedback_payload = provider.feedback_payload
        assert feedback_payload is not None
        feedback = feedback_payload["validation_feedback"]
        self.assertIsInstance(feedback, dict)
        assert isinstance(feedback, dict)
        self.assertEqual("REJECTED", feedback["status"])
        self.assertIn("unknown Entity", str(feedback["error"]))
        self.assertIn("previous_proposal", feedback_payload)

    def test_repeated_invalid_candidate_fails_with_controlled_status(self) -> None:
        provider = _AlwaysInvalidCandidateProvider(
            base_revision=self.base_revision,
            target_revision=self.target_revision,
            proposition=DIRECT_PROPOSITION,
        )
        gateway = ModelGateway(provider, self.services.store)

        with self.assertRaises(TaskExecutionError) as raised:
            TaskExecutionAgent(self.services, gateway)._run_investigation(
                self.task, self.assessment, self.context
            )

        self.assertEqual("INVALID_CANDIDATE_PROPOSAL", raised.exception.status)
        self.assertIn("after 3 attempts", str(raised.exception))

    def test_model_fact_beyond_evidence_is_rejected(self) -> None:
        result, _ = self._run(
            "The service persists the value transactionally."
        )

        self.assertEqual("FAILED", result.status)
        self.assertEqual(
            self.baseline_snapshot_id,
            self.services.current_snapshot(SCOPE_ID)["snapshot_id"],
        )
        self.assertTrue(result.rejected_candidate_ids)
        self.assertFalse(
            any(
                item["proposition"]
                == "The service persists the value transactionally."
                for item in self.services.knowledge_engine.read_facts(SCOPE_ID)
            )
        )

    def test_model_evidence_locator_outside_collected_artifact_is_rejected(
        self,
    ) -> None:
        with self.assertRaises(TaskExecutionError) as raised:
            self._run(DIRECT_PROPOSITION, line_end=999)

        self.assertEqual("INVALID_CANDIDATE_PROPOSAL", raised.exception.status)
        self.assertIn("locator is outside Artifact", str(raised.exception))

        self.assertEqual(
            self.baseline_snapshot_id,
            self.services.current_snapshot(SCOPE_ID)["snapshot_id"],
        )

    def test_build_intent_rejects_request_revision_mismatch(self) -> None:
        with self.assertRaises(TaskExecutionError) as raised:
            self._run(
                DIRECT_PROPOSITION,
                request_revision=self.base_revision,
            )

        self.assertEqual("INVALID_BUILD_INTENT", raised.exception.status)
        self.assertIn(
            "ArtifactRequest revision must equal BuildIntent target_revision",
            str(raised.exception),
        )

        self.assertEqual(
            self.baseline_snapshot_id,
            self.services.current_snapshot(SCOPE_ID)["snapshot_id"],
        )


if __name__ == "__main__":
    unittest.main()
