from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile
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
    EVIDENCE_ANSWER_CAPABILITY_CONTRACT_VERSION,
    EVIDENCE_ANSWER_CAPABILITY_ID,
    QualificationProof,
)
from software_world_model.cross_cutting import Digest, DomainError, ErrorCode, digest_of
from software_world_model.infrastructure import SqliteDatabase, SqliteModelGatewayRepository
from software_world_model.interface.agentic_runtime import evidence_task_strategy_definition
from validation.product_holdout_iteration_002 import (
    EvidenceFirstAnswerExecutor,
    HoldoutAnswerPath,
)


class CurrentQualification:
    def validate(self, proof: QualificationProof) -> bool:
        return proof.verify_digest() and proof.qualification_kind == "CAPABILITY_EVALUATION"


class ScriptedEvidenceAdapter:
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
        if request.output_schema_ref == "evidence-question-checklist@1":
            output = {"questions": ["App.value 的源码初始值是什么？"]}
        elif request.output_schema_ref == "evidence-answer-draft@1":
            output = {
                "sections": [
                    {
                        "section_id": "value",
                        "kind": "SUPPORTED",
                        "text": "当前源码中，App.value 的初始值是 3。",
                        "checklist_item_ids": ["check-1"],
                        "evidence_ids": ["evidence-1"],
                    }
                ]
            }
        elif request.output_schema_ref == "evidence-answer-review@1":
            output = {
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
        else:
            raise AssertionError(f"unexpected schema: {request.output_schema_ref}")
        return AdapterResponse.create(
            provider_request_id=f"evidence-provider-request:{self.calls}",
            actual_model_fingerprint="model-fingerprint",
            replay_classification=ReplayClassification.PINNED,
            output_text=json.dumps(output, ensure_ascii=False),
            input_tokens=200,
            output_tokens=50,
            usage_complete=True,
            termination_reason="stop",
        )


def qualification() -> QualificationProof:
    strategy = evidence_task_strategy_definition()
    core = {
        "proof_ref": "capability-evaluation:current-evidence:1",
        "capability_id": EVIDENCE_ANSWER_CAPABILITY_ID,
        "capability_contract_version": EVIDENCE_ANSWER_CAPABILITY_CONTRACT_VERSION,
        "strategy_id": strategy.strategy_id,
        "strategy_version": strategy.strategy_version,
        "result_ref": "evaluation-result:current-evidence:1",
        "validity_ref": "evaluation-validity:current-evidence:1",
        "qualification_kind": "CAPABILITY_EVALUATION",
    }
    return QualificationProof(**core, digest=digest_of(core))


def task_input(commit: str, *, maximum_model_calls: int = 20) -> dict[str, object]:
    core = {
        "schema": "swm.product-holdout-task-input@1",
        "suite_id": "evidence-test-suite",
        "suite_version": "1.0.0",
        "suite_digest": "sha256:" + "1" * 64,
        "task_id": "evidence-read-app",
        "repository": {
            "repository_id": "test",
            "remote": "local",
            "frozen_tag": "test",
            "frozen_commit": commit,
            "frozen_tree": "2" * 40,
        },
        "question": "App.value 的源码初始值是什么？",
        "revision_scope": {"kind": "FROZEN_SNAPSHOT", "parent": None, "target": commit},
        "allowed_paths": ["src/App.java"],
        "source_policy": "LOCAL_GIT_READ_ONLY_ALLOWED_PATHS_ONLY",
        "resource_policy": {
            "maximum_model_calls": maximum_model_calls,
            "maximum_source_actions": 12,
            "maximum_source_bytes_per_action": 16000,
            "maximum_total_input_tokens": 300000,
            "maximum_total_output_tokens": 48000,
            "maximum_output_tokens_per_call": 1200,
            "timeout_per_call_milliseconds": 180000,
        },
    }
    return {**core, "task_input_digest": digest_of(core).value}


class EvidenceFirstAnswerExecutorTests(unittest.TestCase):
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
        self.adapter = ScriptedEvidenceAdapter()
        self.gateway = ModelGateway(
            SqliteModelGatewayRepository(self.database), (self.adapter,)
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

    def configuration(self) -> AgenticModelStrategyConfiguration:
        return AgenticModelStrategyConfiguration(
            provider_type=self.adapter.provider_type,
            adapter_version=self.adapter.adapter_version,
            model_ref="model-alias",
            provider_configuration_fingerprint=Digest("sha256:" + "0" * 64),
            qualification_ref=self.proof.proof_ref,
            max_output_tokens=1200,
            timeout_milliseconds=180000,
            classification="INTERNAL",
        )

    def test_executes_production_evidence_path_and_seals_cited_answer(self) -> None:
        result = EvidenceFirstAnswerExecutor(
            database=self.database,
            gateway=self.gateway,
            configuration=self.configuration(),
            qualification=self.proof,
            qualification_verifier=CurrentQualification(),
            expected_model_fingerprint="model-fingerprint",
        ).execute(
            task_input=task_input(self.commit),
            checkout_path=self.repository,
            run_id="evidence-test-run",
        )

        self.assertEqual(result.path, HoldoutAnswerPath.WORLD_ASSISTED)
        self.assertEqual(result.answer, "当前源码中，App.value 的初始值是 3。")
        self.assertEqual(result.model_call_count, 3)
        self.assertEqual(result.source_action_count, 1)
        self.assertTrue(result.claims[0].support_references[0].startswith("source-artifact:"))
        self.assertTrue(result.verify_digest())

    def test_model_budget_fails_closed_before_answer_generation(self) -> None:
        with self.assertRaises(DomainError) as raised:
            EvidenceFirstAnswerExecutor(
                database=self.database,
                gateway=self.gateway,
                configuration=self.configuration(),
                qualification=self.proof,
                qualification_verifier=CurrentQualification(),
                expected_model_fingerprint="model-fingerprint",
            ).execute(
                task_input=task_input(self.commit, maximum_model_calls=1),
                checkout_path=self.repository,
                run_id="evidence-budget-test-run",
            )

        self.assertEqual(raised.exception.code, ErrorCode.BUDGET_EXHAUSTED)
        self.assertEqual(self.adapter.calls, 1)


if __name__ == "__main__":
    unittest.main()
