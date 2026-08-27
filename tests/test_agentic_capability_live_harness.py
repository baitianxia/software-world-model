from __future__ import annotations

from io import StringIO
import json
from pathlib import Path
import tempfile
import unittest

from software_world_model.ai_infrastructure import (
    AdapterConformanceLevel,
    AdapterResponse,
    AgenticEvaluationRole,
    AgenticModelStrategyConfiguration,
    ModelGateway,
    DEFAULT_VOLCENGINE_ARK_ACTUAL_MODEL_FINGERPRINT,
    ProviderHTTPResponse,
    ProviderOutputRejected,
    ProviderAdapterCapabilities,
    ReplayClassification,
    VolcengineArkModelConfiguration,
    load_ark_chat_conformance_qualification,
)
from software_world_model.cross_cutting import Digest, DomainError, ErrorCode, digest_of
from software_world_model.infrastructure import (
    SqliteDatabase,
    SqliteModelGatewayRepository,
)
from validation.agentic_capability_iteration_001 import (
    CAPABILITY_REVIEW_DRAFT_SCHEMA,
    LiveCapabilityCaseRunner,
    build_capability_definition,
    load_capability_output_document,
    load_capability_review_document,
    load_capability_suite,
    save_capability_output_document,
    seal_capability_review_draft,
)
from validation.agentic_capability_iteration_001.cli import main as capability_main
from software_world_model.interface.provider_cli import main as provider_main


class ScriptedRoleAdapter:
    provider_type = "TEST_LIVE"
    adapter_version = "1"
    capabilities = ProviderAdapterCapabilities(
        no_external_access=True,
        hidden_context_disabled=True,
        stateless_session=True,
        structured_output=True,
        actual_fingerprint_reported=True,
        conformance_level=AdapterConformanceLevel.LIVE_CURRENT,
        conformance_result_ref="conformance:test",
        qualified_model_fingerprints=("model-fingerprint",),
    )

    def __init__(
        self,
        actual_model_fingerprint="model-fingerprint",
        conformance_result_ref="conformance:test",
        reject_once_schema_ref=None,
    ) -> None:
        self.calls = 0
        self.actual_model_fingerprint = actual_model_fingerprint
        self.reject_once_schema_ref = reject_once_schema_ref
        self.rejected = False
        self.capabilities = ProviderAdapterCapabilities(
            no_external_access=True,
            hidden_context_disabled=True,
            stateless_session=True,
            structured_output=True,
            actual_fingerprint_reported=True,
            conformance_level=AdapterConformanceLevel.LIVE_CURRENT,
            conformance_result_ref=conformance_result_ref,
            qualified_model_fingerprints=(actual_model_fingerprint,),
        )

    def invoke(self, request):
        self.calls += 1
        if (
            request.output_schema_ref == self.reject_once_schema_ref
            and not self.rejected
        ):
            self.rejected = True
            response = AdapterResponse.create(
                provider_request_id=f"provider:{self.calls}",
                actual_model_fingerprint=self.actual_model_fingerprint,
                replay_classification=ReplayClassification.PINNED,
                output_text="{}",
                input_tokens=100,
                output_tokens=2,
                usage_complete=True,
                termination_reason="stop",
            )
            raise ProviderOutputRejected(
                DomainError(
                    ErrorCode.STRUCTURED_OUTPUT_INVALID,
                    "scripted first output violates the schema",
                ),
                response,
            )
        output = self.output(request)
        return AdapterResponse.create(
            provider_request_id=f"provider:{self.calls}",
            actual_model_fingerprint=self.actual_model_fingerprint,
            replay_classification=ReplayClassification.PINNED,
            output_text=json.dumps(output),
            input_tokens=100,
            output_tokens=25,
            usage_complete=True,
            termination_reason="stop",
        )

    @staticmethod
    def state(request, item_id="authorized-state"):
        message = next(item for item in request.messages if item.input_item_id == item_id)
        return json.loads(message.content)

    def output(self, request):
        schema = request.output_schema_ref
        if schema == "agentic-requirement-planner@1":
            return {
                "needs": [
                    {
                        "need_id": "need:request",
                        "question": (
                            "Explain when RetryClient retries a request, state the "
                            "maximum attempt limit, and do not infer behavior outside "
                            "the supplied source boundary."
                        ),
                        "required_kinds": ["FACT"],
                        "required_type_names": [],
                        "retrieval_terms": ["RetryClient", "retry", "MAX_ATTEMPTS"],
                        "minimum_support_count": 1,
                    },
                ],
                "joint_constraints": [],
                "rationale": "Preserve the complete request as one deliverable.",
            }
        if schema == "agentic-requirement-reviewer@1":
            return {
                "decision": "ACCEPT",
                "accepted_need_ids": ["need:request"],
                "original_request_preserved": True,
                "all_material_questions_covered": True,
                "findings": [],
            }
        if schema == "agentic-source-planner@1":
            state = self.state(request, "task-state")
            return {
                "decision": "EXECUTE",
                "tool": "READ",
                "revision": state["target"]["identity"]["revision"],
                "base": "",
                "path": "src/RetryClient.java",
                "query": "",
                "cursor": "",
                "offset": "",
                "max_bytes": "4096",
                "page_size": "",
                "rationale": "Read the exact bounded declaration.",
            }
        if schema == "agentic-fact-proposer@5":
            artifact = self.state(request)["artifacts"][0]
            return {
                "candidates": [
                    {
                        "candidate_key": "maximum-attempts",
                        "need_ids": ["OBJECTIVE"],
                        "artifact_id": artifact["artifact_id"],
                        "line_start": 2,
                        "line_end": 2,
                        "entity_type": "CONFIGURATION",
                        "predicate": "HAS_VALUE",
                        "statement": "RetryClient declares a maximum attempt count of 3.",
                        "condition": None,
                        "limitation": None,
                    }
                ],
                "limitations": [],
            }
        if schema == "agentic-fact-reviewer@4":
            return {
                "decision": "ACCEPT",
                "accepted_candidate_keys": ["maximum-attempts"],
                "all_supported_objective_aspects_covered": True,
                "findings": [],
            }
        if schema == "agentic-sequence-analyzer@10":
            state = self.state(request)
            return {
                "edges": [],
                "call_return_spans": [],
                "atomic_references": [
                    {
                        "need_id": item["need_id"],
                        "reference_ids": [
                            reference["reference_id"]
                            for reference in item["references"]
                        ],
                    }
                    for item in state["reference_sets"]
                ],
                "rationale": "AUDITED",
            }
        if schema == "agentic-sufficiency-reviewer@1":
            record = self.state(request)["read_set"]["records"][0]
            return {
                "status": "SATISFIED",
                "supporting_reference_ids": [record["object_id"]],
                "gap": None,
                "counterexample_reference_ids": [],
                "conflict_reference_ids": [],
                "unknowns": [],
                "limitations": [
                    "This is a source declaration, not proof of every runtime path."
                ],
                "rationale": "The exact formal fact answers the need.",
            }
        if schema == "agentic-answer-drafter@1":
            state = self.state(request)
            return {
                "selections": [
                    {
                        "need_id": state["needs"][0]["need_id"],
                        "formal_reference_ids": [
                            state["needs"][0]["formal_records"][0]["object_id"]
                        ],
                    }
                ],
                "rationale": "Select only the authorized fact.",
            }
        if schema == "agentic-answer-reviewer@1":
            return {"decision": "APPROVE", "failed_dimensions": [], "findings": []}
        raise AssertionError(schema)


class EchoingConformanceTransport:
    def __init__(self) -> None:
        self.calls = 0

    def post_json(self, **arguments):
        self.calls += 1
        body = json.loads(arguments["body"])
        schema = json.loads(
            body["messages"][0]["content"].rsplit("Schema: ", 1)[1]
        )
        properties = schema["properties"]
        content = json.dumps(
            {
                "case": properties["case"]["enum"][0],
                "nonce": properties["nonce"]["enum"][0],
                "status": "ok",
            }
        )
        return ProviderHTTPResponse(
            status_code=200,
            headers={"x-tt-logid": f"ark-capability-test-{self.calls}"},
            body=json.dumps(
                {
                    "id": f"chatcmpl-capability-test-{self.calls}",
                    "object": "chat.completion",
                    "model": DEFAULT_VOLCENGINE_ARK_ACTUAL_MODEL_FINGERPRINT,
                    "choices": [
                        {
                            "index": 0,
                            "message": {"role": "assistant", "content": content},
                            "finish_reason": "stop",
                        }
                    ],
                    "usage": {
                        "prompt_tokens": 10,
                        "completion_tokens": 5,
                        "total_tokens": 15,
                    },
                }
            ).encode(),
        )

    def session_audit(self):
        return {
            "schema": "SWM-VOLCENGINE-ARK-TRANSPORT-SESSION-AUDIT@1",
            "connection_policy": (
                "DIRECT_VERIFIED_TLS_HTTP11_ONE_REQUEST_PER_SESSION@1"
            ),
            "maximum_pre_dispatch_tls_handshake_attempts_per_request": 1,
            "maximum_http_dispatches_per_tls_session": 1,
            "tls_handshake_attempt_count": self.calls,
            "tls_handshake_success_count": self.calls,
            "pre_dispatch_tls_handshake_failure_count": 0,
            "pre_dispatch_tls_failure_codes": [],
            "http_dispatch_count": self.calls,
            "connection_reuse_count": 0,
            "verified_peer_certificate_sha256s": [
                "sha256:" + f"{ordinal:064x}"
                for ordinal in range(1, self.calls + 1)
            ],
            "post_dispatch_outcome_unknown_count": 0,
            "post_dispatch_failure_codes": [],
            "request_retry_count": 0,
            "credential_resolution_count": self.calls,
            "credential_resolution_success_count": self.calls,
            "credential_resolution_policy": (
                "AFTER_VERIFIED_TLS_BEFORE_EACH_HTTP_DISPATCH"
            ),
        }


class AgenticCapabilityLiveHarnessTests(unittest.TestCase):
    def setUp(self) -> None:
        self.suite = load_capability_suite()
        self.configuration = AgenticModelStrategyConfiguration(
            provider_type="TEST_LIVE",
            adapter_version="1",
            model_ref="model-alias",
            provider_configuration_fingerprint=Digest("sha256:" + "0" * 64),
            qualification_ref="evaluation-only:test",
            max_output_tokens=1200,
            timeout_milliseconds=180000,
            classification="INTERNAL",
        )

    def test_sealed_suite_builds_current_six_role_definition(self) -> None:
        definition = build_capability_definition(
            self.suite,
            conformance_result_ref="conformance:test",
            provider_configuration_fingerprint=Digest("sha256:" + "0" * 64),
            actual_model_fingerprint="model-fingerprint",
            adapter_version="1",
            valid_for_seconds=3600,
        )

        self.assertEqual(len(definition.cases), 6)
        self.assertEqual(definition.model_ref, "model-fingerprint")
        self.assertEqual(
            {item.case_id.split(":", 1)[0] for item in definition.cases},
            {item.value.lower() for item in AgenticEvaluationRole},
        )

    def test_every_live_role_produces_recoverable_source_closed_output(self) -> None:
        for role in AgenticEvaluationRole:
            with self.subTest(role=role), tempfile.TemporaryDirectory() as directory:
                adapter = ScriptedRoleAdapter()
                with SqliteDatabase() as database:
                    runner = LiveCapabilityCaseRunner(
                        database=database,
                        gateway=ModelGateway(
                            SqliteModelGatewayRepository(database), (adapter,)
                        ),
                        configuration=self.configuration,
                        expected_model_fingerprint="model-fingerprint",
                    )
                    output, document = runner.execute(suite=self.suite, role=role)
                path = save_capability_output_document(document, directory)
                recovered, recovered_document = load_capability_output_document(path)

                self.assertEqual(recovered, output)
                self.assertEqual(recovered_document["role"], role.value)
                self.assertTrue(recovered.usage_complete)
                self.assertTrue(recovered_document["authorized_manifests"])
                if role is AgenticEvaluationRole.NEED_SUFFICIENCY:
                    serialized_inputs = json.dumps(
                        recovered_document["authorized_manifests"]
                    )
                    self.assertIn(self.suite["cases"][3]["fixture"]["limitation"], serialized_inputs)

    def test_complete_structured_rejection_is_audited_before_bounded_role_retry(self) -> None:
        adapter = ScriptedRoleAdapter(
            reject_once_schema_ref="agentic-requirement-planner@1"
        )
        with SqliteDatabase() as database:
            _, document = LiveCapabilityCaseRunner(
                database=database,
                gateway=ModelGateway(
                    SqliteModelGatewayRepository(database), (adapter,)
                ),
                configuration=self.configuration,
                expected_model_fingerprint="model-fingerprint",
            ).execute(
                suite=self.suite,
                role=AgenticEvaluationRole.REQUIREMENT_FIDELITY,
            )

        self.assertEqual(adapter.calls, 3)
        self.assertEqual(len(document["authorized_manifests"]), 3)
        self.assertEqual(len(document["isolation_receipts"]), 3)
        self.assertEqual(
            [item["failure_code"] for item in document["model_call_outcomes"]],
            [ErrorCode.STRUCTURED_OUTPUT_INVALID.value, None, None],
        )

    def test_codex_review_draft_is_bound_to_exact_output_and_oracle(self) -> None:
        role = AgenticEvaluationRole.SOURCE_INVESTIGATION
        with tempfile.TemporaryDirectory() as directory:
            adapter = ScriptedRoleAdapter()
            with SqliteDatabase() as database:
                runner = LiveCapabilityCaseRunner(
                    database=database,
                    gateway=ModelGateway(
                        SqliteModelGatewayRepository(database), (adapter,)
                    ),
                    configuration=self.configuration,
                    expected_model_fingerprint="model-fingerprint",
                )
                output, document = runner.execute(suite=self.suite, role=role)
            output_path = save_capability_output_document(document, directory)
            prepared_output = StringIO()
            self.assertEqual(
                capability_main(
                    (
                        "prepare-review",
                        "--output",
                        str(output_path),
                        "--result-directory",
                        directory,
                    ),
                    stdout=prepared_output,
                ),
                0,
            )
            prepared = json.loads(prepared_output.getvalue())
            self.assertFalse(prepared["judgement_recorded"])
            draft_path = Path(prepared["review_draft_path"])
            draft = json.loads(draft_path.read_text(encoding="utf-8"))
            draft.update(
                {
                    "reviewer_identity": "Codex review session 2026-08-07",
                    "reviewer_origin": "codex-independent-review",
                    "platform_contract_valid": True,
                    "oracle_match": True,
                    "unauthorized_reference_count": 0,
                    "material_omission_count": 0,
                    "material_error_count": 0,
                    "reviewed_at": "2026-08-07T00:00:00+00:00",
                }
            )
            draft_path.write_text(json.dumps(draft), encoding="utf-8")
            review_path = seal_capability_review_draft(
                draft_path,
                output_path=output_path,
                suite=self.suite,
                result_directory=directory,
            )
            review, _ = load_capability_review_document(
                review_path, output_path=output_path, suite=self.suite
            )

            self.assertTrue(review.verify_digest())
            self.assertNotEqual(review.reviewer_origin, output.generator_origin)

            forged = dict(document)
            forged["suite_id"] = "different-suite"
            forged["oracle_ref"] = "different-suite:oracle:source"
            forged_core = {
                key: value
                for key, value in forged.items()
                if key != "document_digest"
            }
            forged["document_digest"] = digest_of(forged_core).value
            forged_path = Path(directory) / "forged-output.json"
            forged_path.write_text(json.dumps(forged), encoding="utf-8")
            rejected_output = StringIO()
            self.assertEqual(
                capability_main(
                    (
                        "prepare-review",
                        "--output",
                        str(forged_path),
                        "--result-directory",
                        str(Path(directory) / "forged-review"),
                    ),
                    stdout=rejected_output,
                ),
                2,
            )

    def test_full_offline_flow_records_qualification_for_actual_model_identity(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            conformance_output = StringIO()
            self.assertEqual(
                provider_main(
                    (
                        "conformance",
                        "--result-directory",
                        str(root / "conformance"),
                        "--operator",
                        "offline-test-operator",
                    ),
                    stdout=conformance_output,
                    environment={"ARK_API_KEY": "offline-fixture-secret"},
                    transport=EchoingConformanceTransport(),
                ),
                0,
            )
            conformance_path = json.loads(conformance_output.getvalue())[
                "result_path"
            ]
            evidence = root / "evidence"
            configuration = VolcengineArkModelConfiguration()
            conformance = load_ark_chat_conformance_qualification(
                conformance_path, configuration
            )
            adapter = ScriptedRoleAdapter(
                configuration.actual_model_fingerprint,
                conformance.result_ref,
            )
            adapter.provider_type = configuration.provider_type
            adapter.adapter_version = configuration.adapter_version
            model_configuration = AgenticModelStrategyConfiguration(
                provider_type=adapter.provider_type,
                adapter_version=adapter.adapter_version,
                model_ref=configuration.model_ref,
                provider_configuration_fingerprint=configuration.fingerprint,
                qualification_ref=f"evaluation-only:{conformance.result_ref}",
                max_output_tokens=1200,
                timeout_milliseconds=180000,
                classification="INTERNAL",
            )
            (root / "runtime").mkdir(parents=True, exist_ok=True)
            for role in AgenticEvaluationRole:
                with SqliteDatabase(
                    root / "runtime" / f"{role.value.lower()}.sqlite3"
                ) as database:
                    output, document = LiveCapabilityCaseRunner(
                        database=database,
                        gateway=ModelGateway(
                            SqliteModelGatewayRepository(database), (adapter,)
                        ),
                        configuration=model_configuration,
                        expected_model_fingerprint=(
                            configuration.actual_model_fingerprint
                        ),
                    ).execute(suite=self.suite, role=role)
                output_path = save_capability_output_document(
                    document, evidence / "outputs"
                )
                draft = {
                    "schema": CAPABILITY_REVIEW_DRAFT_SCHEMA,
                    "suite_digest": self.suite["suite_digest"],
                    "case_id": output.case_id,
                    "output_digest": output.output_digest.value,
                    "reviewer_identity": "Codex offline integration test",
                    "reviewer_origin": "codex-independent-review",
                    "platform_contract_valid": True,
                    "oracle_match": True,
                    "unauthorized_reference_count": 0,
                    "material_omission_count": 0,
                    "material_error_count": 0,
                    "findings": [],
                    "reviewed_at": "2026-08-07T00:00:00+00:00",
                }
                draft_path = root / "drafts" / f"{role.value.lower()}.json"
                draft_path.parent.mkdir(parents=True, exist_ok=True)
                draft_path.write_text(json.dumps(draft), encoding="utf-8")
                seal_capability_review_draft(
                    draft_path,
                    output_path=output_path,
                    suite=self.suite,
                    result_directory=evidence / "reviews",
                )

            finalize_output = StringIO()
            exit_code = capability_main(
                (
                    "finalize",
                    "--conformance-result",
                    conformance_path,
                    "--evidence-directory",
                    str(evidence),
                    "--evaluation-database",
                    str(root / "evaluation.sqlite3"),
                    "--result-directory",
                    str(evidence),
                ),
                stdout=finalize_output,
            )
            result = json.loads(finalize_output.getvalue())

            self.assertEqual(exit_code, 0, result)
            self.assertEqual(result["status"], "CAPABILITY_EVALUATION_PASS")
            self.assertTrue(Path(result["qualification_path"]).is_file())


if __name__ == "__main__":
    unittest.main()
