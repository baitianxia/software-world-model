from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest

from software_world_model.ai_infrastructure import (
    AdapterConformanceLevel,
    AdapterResponse,
    AgenticModelStrategyConfiguration,
    ModelGateway,
    ProviderAdapterCapabilities,
    ReplayClassification,
)
from software_world_model.application_services import (
    NATURAL_TASK_CAPABILITY_CONTRACT_VERSION,
    NATURAL_TASK_CAPABILITY_ID,
    QualificationProof,
)
from software_world_model.cross_cutting import Digest, digest_of
from software_world_model.infrastructure import (
    SqliteDatabase,
    SqliteModelGatewayRepository,
)
from software_world_model.interface.agentic_runtime import (
    agentic_task_strategy_definition,
)
from validation.product_holdout_iteration_002 import (
    HoldoutAnswerPath,
    WorldAssistedAnswerExecutor,
)
from validation.product_holdout_iteration_002.world_answer import _sealed_claims


class CurrentQualification:
    def validate(self, proof: QualificationProof) -> bool:
        return proof.verify_digest() and proof.qualification_kind == "CAPABILITY_EVALUATION"


class ScriptedLiveAdapter:
    provider_type = "TEST_LIVE"
    adapter_version = "1"
    capabilities = ProviderAdapterCapabilities(
        no_external_access=True,
        hidden_context_disabled=True,
        stateless_session=True,
        structured_output=True,
        actual_fingerprint_reported=True,
        conformance_level=AdapterConformanceLevel.LIVE_CURRENT,
        conformance_result_ref="conformance:test-live:1",
        qualified_model_fingerprints=("model-fingerprint",),
    )

    def __init__(self) -> None:
        self.calls = 0

    def invoke(self, request):
        self.calls += 1
        output = self._output(request)
        return AdapterResponse.create(
            provider_request_id=f"world-provider-request:{self.calls}",
            actual_model_fingerprint="model-fingerprint",
            replay_classification=ReplayClassification.PINNED,
            output_text=json.dumps(output),
            input_tokens=200,
            output_tokens=50,
            usage_complete=True,
            termination_reason="stop",
        )

    def _state(self, request, item_id: str = "authorized-state"):
        message = next(item for item in request.messages if item.input_item_id == item_id)
        return json.loads(message.content)

    def _output(self, request):
        schema = request.output_schema_ref
        if schema == "agentic-requirement-planner@1":
            return {
                "needs": [
                    {
                        "need_id": "need:initializer",
                        "question": "App.value 的源码初始值是什么？",
                        "required_kinds": ["FACT"],
                        "required_type_names": [],
                        "retrieval_terms": ["value"],
                        "minimum_support_count": 1,
                    }
                ],
                "joint_constraints": [],
                "rationale": "The request contains one material source question.",
            }
        if schema == "agentic-requirement-reviewer@1":
            return {
                "decision": "ACCEPT",
                "accepted_need_ids": ["need:initializer"],
                "original_request_preserved": True,
                "all_material_questions_covered": True,
                "findings": [],
            }
        if schema == "agentic-source-planner@1":
            state = self._state(request, "task-state")
            operations = state["completed_operations"]
            revision = state["target"]["identity"]["revision"]
            common = {
                "decision": "EXECUTE",
                "revision": revision,
                "base": "",
                "query": "",
                "cursor": "",
                "offset": "",
                "max_bytes": "",
                "page_size": "",
                "rationale": "Observe the exact bounded source.",
            }
            if not operations:
                return {**common, "tool": "READ", "path": "src/App.java", "max_bytes": "16000"}
            if len(operations) == 1:
                return {**common, "tool": "LIST", "path": "", "page_size": "200"}
            return {
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
                "rationale": "The source file and exact repository boundary are observed.",
            }
        if schema == "agentic-fact-proposer@1":
            state = self._state(request)
            artifact = next(
                item for item in state["artifacts"] if item["identity"] == "src/App.java"
            )
            return {
                "candidates": [
                    {
                        "candidate_key": "app-value",
                        "artifact_id": artifact["artifact_id"],
                        "line_start": 1,
                        "line_end": 1,
                        "entity_type": "CODE_SYMBOL",
                        "predicate": "HAS_VALUE",
                        "statement": "App.value is initialized to 3 in this source revision.",
                        "condition": None,
                        "limitation": "This describes the source initializer, not every runtime value.",
                    }
                ],
                "limitations": [],
            }
        if schema == "agentic-fact-reviewer@3":
            return {
                "decision": "ACCEPT",
                "accepted_candidate_keys": ["app-value"],
                "all_supported_objective_aspects_covered": True,
                "findings": [],
            }
        if schema == "agentic-sufficiency-reviewer@1":
            state = self._state(request)
            record = state["read_set"]["records"][0]
            return {
                "status": "SATISFIED",
                "supporting_reference_ids": [record["object_id"]],
                "gap": None,
                "counterexample_reference_ids": [],
                "conflict_reference_ids": [],
                "unknowns": [],
                "limitations": ["Source declaration only."],
                "rationale": "The exact formal fact answers the Need.",
            }
        if schema == "agentic-answer-drafter@1":
            state = self._state(request)
            record = state["needs"][0]["formal_records"][0]
            return {
                "selections": [
                    {
                        "need_id": "need:initializer",
                        "formal_reference_ids": [record["object_id"]],
                    }
                ],
                "rationale": "Select the exact source-closed fact.",
            }
        if schema == "agentic-answer-reviewer@1":
            return {
                "decision": "APPROVE",
                "failed_dimensions": [],
                "findings": [],
            }
        raise AssertionError(f"unexpected schema: {schema}")


def qualification() -> QualificationProof:
    strategy = agentic_task_strategy_definition()
    core = {
        "proof_ref": "capability-evaluation:current-agentic:1",
        "capability_id": NATURAL_TASK_CAPABILITY_ID,
        "capability_contract_version": NATURAL_TASK_CAPABILITY_CONTRACT_VERSION,
        "strategy_id": strategy.strategy_id,
        "strategy_version": strategy.strategy_version,
        "result_ref": "evaluation-result:current-agentic:1",
        "validity_ref": "evaluation-validity:current-agentic:1",
        "qualification_kind": "CAPABILITY_EVALUATION",
    }
    return QualificationProof(**core, digest=digest_of(core))


def task_input(commit: str) -> dict[str, object]:
    core = {
        "schema": "swm.product-holdout-task-input@1",
        "suite_id": "world-test-suite",
        "suite_version": "1.0.0",
        "suite_digest": "sha256:" + "1" * 64,
        "task_id": "world-read-app",
        "repository": {
            "repository_id": "test",
            "remote": "local",
            "frozen_tag": "test",
            "frozen_commit": commit,
            "frozen_tree": "2" * 40,
        },
        "question": "App.value 的源码初始值是什么？",
        "revision_scope": {
            "kind": "FROZEN_SNAPSHOT",
            "parent": None,
            "target": commit,
        },
        "allowed_paths": ["src/App.java"],
        "source_policy": "LOCAL_GIT_READ_ONLY_ALLOWED_PATHS_ONLY",
        "resource_policy": {
            "maximum_model_calls": 34,
            "maximum_source_actions": 12,
            "maximum_source_bytes_per_action": 16000,
            "maximum_total_input_tokens": 300000,
            "maximum_total_output_tokens": 48000,
            "maximum_output_tokens_per_call": 1200,
            "timeout_per_call_milliseconds": 180000,
        },
    }
    return {**core, "task_input_digest": digest_of(core).value}


class WorldAssistedAnswerExecutorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.repository = Path(self.temporary.name) / "repo"
        self.repository.mkdir()
        self.git("init", "-q")
        self.git("config", "user.email", "test@example.com")
        self.git("config", "user.name", "Test")
        (self.repository / "src").mkdir()
        (self.repository / "src/App.java").write_text(
            "public class App { int value = 3; }\n", encoding="utf-8"
        )
        self.git("add", ".")
        self.git("commit", "-q", "-m", "initial")
        self.commit = self.git("rev-parse", "HEAD")
        self.database = SqliteDatabase()
        self.adapter = ScriptedLiveAdapter()
        self.gateway = ModelGateway(
            SqliteModelGatewayRepository(self.database),
            (self.adapter,),
        )
        self.proof = qualification()

    def tearDown(self) -> None:
        self.database.close()
        self.temporary.cleanup()

    def git(self, *arguments: str) -> str:
        return subprocess.run(
            ("git", "-C", str(self.repository), *arguments),
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

    def test_empty_scope_runs_formal_path_and_seals_reviewed_answer(self) -> None:
        configuration = AgenticModelStrategyConfiguration(
            provider_type=self.adapter.provider_type,
            adapter_version=self.adapter.adapter_version,
            model_ref="model-alias",
            provider_configuration_fingerprint=Digest("sha256:" + "0" * 64),
            qualification_ref=self.proof.proof_ref,
            max_output_tokens=1200,
            timeout_milliseconds=180000,
            classification="INTERNAL",
        )

        result = WorldAssistedAnswerExecutor(
            database=self.database,
            gateway=self.gateway,
            configuration=configuration,
            qualification=self.proof,
            qualification_verifier=CurrentQualification(),
            expected_model_fingerprint="model-fingerprint",
        ).execute(
            task_input=task_input(self.commit),
            checkout_path=self.repository,
            run_id="world-test-run",
        )

        self.assertEqual(result.path, HoldoutAnswerPath.WORLD_ASSISTED)
        self.assertIn("App.value is initialized to 3", result.answer)
        self.assertIn("not every runtime value", result.answer)
        self.assertEqual(result.model_call_count, 10)
        self.assertEqual(result.source_action_count, 2)
        self.assertTrue(result.verify_digest())
        with self.database.read() as connection:
            decision = connection.execute(
                """SELECT roots.activation_scope_json, decisions.reason
                   FROM app_activation_decisions AS decisions
                   JOIN app_activation_roots AS roots
                     ON roots.control_key_digest = decisions.control_key_digest"""
            ).fetchone()
        self.assertIn("sealed-product-evaluation", decision["activation_scope_json"])
        self.assertIn("without granting production activation", decision["reason"])

    def test_repeated_formal_claim_merges_support_without_repeating_text(self) -> None:
        claims = (
            SimpleNamespace(
                text="One supported fact.",
                formal_reference=SimpleNamespace(value="knowledge:1"),
                support_proof_id=SimpleNamespace(value="proof:1"),
                need_id="need:1",
            ),
            SimpleNamespace(
                text="One supported fact.",
                formal_reference=SimpleNamespace(value="knowledge:1"),
                support_proof_id=SimpleNamespace(value="proof:2"),
                need_id="need:2",
            ),
        )

        sealed = _sealed_claims(claims, "assessment:1")

        self.assertEqual(len(sealed), 1)
        self.assertEqual(sealed[0].claim, "One supported fact.")
        self.assertEqual(
            sealed[0].support_references,
            ("knowledge:1", "proof:1", "proof:2"),
        )


if __name__ == "__main__":
    unittest.main()
