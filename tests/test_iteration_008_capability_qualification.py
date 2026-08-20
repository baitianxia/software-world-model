from __future__ import annotations

import copy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import tempfile
import unittest

from software_world_model.ai_infrastructure import (
    BoundedJavaSourceSemanticsWorldModelEvaluationCase,
    BoundedJavaSourceSemanticsWorldModelEvaluationRole,
    JAVA_SOURCE_SEMANTICS_WORLD_MODEL_PROPOSAL_CONTRACT,
    bounded_java_source_semantics_world_model_capability_registry,
    create_bounded_java_source_semantics_world_model_evaluation_definition,
    java_source_semantics_world_model_output_contract_digest,
    world_model_answer_prompt_program_digest,
    world_model_answer_strategy_implementation_digest,
)
from software_world_model.ai_infrastructure.bounded_java_source_semantics_model_egress_qualification import (
    BOUNDED_JAVA_SOURCE_SEMANTICS_CAPABILITY_CLOSED_RESULT_SCHEMA,
    BOUNDED_JAVA_SOURCE_SEMANTICS_CAPABILITY_ORACLE_DIGEST,
    BOUNDED_JAVA_SOURCE_SEMANTICS_CAPABILITY_QUALIFICATION_DOCUMENT_SCHEMA,
    BOUNDED_JAVA_SOURCE_SEMANTICS_CAPABILITY_SUITE_DIGEST,
    BOUNDED_JAVA_SOURCE_SEMANTICS_EVALUATION_METRIC_CONTRACT,
    BOUNDED_JAVA_SOURCE_SEMANTICS_EVALUATION_THRESHOLD_REF,
    BOUNDED_JAVA_SOURCE_SEMANTICS_QUALIFICATION_CASE_CALLS,
    BOUNDED_JAVA_SOURCE_SEMANTICS_QUALIFICATION_RESOURCE_POLICY_REF,
    load_bounded_java_source_semantics_gateway_qualification_binding,
)
from software_world_model.ai_infrastructure import (
    bounded_java_source_semantics_model_egress_qualification as qualification_module,
)
from software_world_model.ai_infrastructure.deepseek_chat_adapter import (
    DeepSeekModelConfiguration,
)
from software_world_model.cross_cutting import (
    DomainError,
    canonical_json_bytes,
    digest_of,
)
from software_world_model.interface import world_model_runtime


def _documents() -> tuple[dict[str, object], dict[str, object]]:
    contract = JAVA_SOURCE_SEMANTICS_WORLD_MODEL_PROPOSAL_CONTRACT
    configuration = DeepSeekModelConfiguration()
    conformance_result_ref = (
        "CC-DEEPSEEK-CHAT-NO-TOOLS-001:sha256:" + "a" * 64
    )
    result_id = "evaluation_result_" + "1" * 32
    proof_core = {
        "proof_ref": f"capability-evaluation:{result_id}",
        "capability_id": "world-model-authority-proposal",
        "capability_contract_version": contract.capability_contract_version,
        "strategy_id": "model-snapshot-first-world-model-answer",
        "strategy_version": contract.strategy_version,
        "result_ref": result_id,
        "validity_ref": "evaluation_validity_" + "2" * 32 + "@1",
        "qualification_kind": "CAPABILITY_EVALUATION",
    }
    proof = {**proof_core, "digest": digest_of(proof_core).value}
    qualification_core = {
        "schema": (
            BOUNDED_JAVA_SOURCE_SEMANTICS_CAPABILITY_QUALIFICATION_DOCUMENT_SCHEMA
        ),
        "proof": proof,
    }
    qualification = {
        **qualification_core,
        "document_digest": digest_of(qualification_core).value,
    }
    cases = [
        {"case_id": case_id}
        for case_id, _ in BOUNDED_JAVA_SOURCE_SEMANTICS_QUALIFICATION_CASE_CALLS
    ]
    case_evidence = []
    for case_id, call_count in BOUNDED_JAVA_SOURCE_SEMANTICS_QUALIFICATION_CASE_CALLS:
        case_evidence.append(
            {
                "case_id": case_id,
                "status": "PASS",
                "model_call_count": call_count,
                "step_input_digests": [
                    digest_of([case_id, "input", index]).value
                    for index in range(call_count)
                ],
                "step_result_digests": [
                    digest_of([case_id, "result", index]).value
                    for index in range(call_count)
                ],
                "trace_digests": [
                    digest_of([case_id, "trace", index]).value
                    for index in range(call_count)
                ],
            }
        )
    case_ids = [item["case_id"] for item in cases]
    closed_core = {
        "schema": BOUNDED_JAVA_SOURCE_SEMANTICS_CAPABILITY_CLOSED_RESULT_SCHEMA,
        "suite_digest": (
            BOUNDED_JAVA_SOURCE_SEMANTICS_CAPABILITY_SUITE_DIGEST.value
        ),
        "oracle_digest": (
            BOUNDED_JAVA_SOURCE_SEMANTICS_CAPABILITY_ORACLE_DIGEST.value
        ),
        "definition": {
            "capability_id": "world-model-authority-proposal",
            "capability_contract_version": contract.capability_contract_version,
            "strategy_id": "model-snapshot-first-world-model-answer",
            "strategy_version": contract.strategy_version,
            "model_ref": configuration.model_ref,
            "adapter_version": configuration.adapter_version,
            "provider_configuration_fingerprint": (
                configuration.fingerprint.value
            ),
            "conformance_result_ref": conformance_result_ref,
            "implementation_digest": (
                world_model_answer_strategy_implementation_digest(contract).value
            ),
            "prompt_program_digest": (
                world_model_answer_prompt_program_digest(contract).value
            ),
            "output_schema_digest": (
                java_source_semantics_world_model_output_contract_digest(
                    contract
                ).value
            ),
            "metric_contract_digest": digest_of(
                BOUNDED_JAVA_SOURCE_SEMANTICS_EVALUATION_METRIC_CONTRACT
            ).value,
            "threshold_ref": (
                BOUNDED_JAVA_SOURCE_SEMANTICS_EVALUATION_THRESHOLD_REF
            ),
            "resource_policy_ref": (
                BOUNDED_JAVA_SOURCE_SEMANTICS_QUALIFICATION_RESOURCE_POLICY_REF
            ),
            "tool_policy_ref": "model-no-tools-no-source-no-evidence@1",
            "cases": cases,
        },
        "result": {
            "result_id": result_id,
            "conclusion": "PASS",
            "actual_model_fingerprints": [
                configuration.actual_model_fingerprint
            ],
            "passed_case_ids": case_ids,
            "failed_case_ids": [],
            "inconclusive_case_ids": [],
        },
        "validity": {
            "status": "VALID",
            "valid_until": (
                datetime.now(timezone.utc) + timedelta(days=1)
            ).isoformat(),
        },
        "qualification": proof,
        "case_evidence": case_evidence,
        "closed_result_status": "PASS_VALID",
        "failure_count": 0,
        "unknown_count": 0,
        "required_case_count": len(cases),
        "provider_request_count": sum(
            count
            for _, count in BOUNDED_JAVA_SOURCE_SEMANTICS_QUALIFICATION_CASE_CALLS
        ),
        "transport_session": {
            "schema": "SWM-DEEPSEEK-TRANSPORT-SESSION-AUDIT@2",
            "connection_policy": (
                "PERSISTENT_VERIFIED_TLS_HTTP11_KEEP_ALIVE@2"
            ),
            "maximum_pre_dispatch_tls_handshake_attempts": 3,
            "maximum_http_dispatches_per_tls_session": 20,
            "tls_handshake_attempt_count": 2,
            "tls_handshake_success_count": 2,
            "pre_dispatch_tls_handshake_failure_count": 0,
            "pre_dispatch_tls_failure_codes": [],
            "http_dispatch_count": 40,
            "connection_reuse_count": 38,
            "verified_peer_certificate_sha256s": [
                "sha256:" + "c" * 64,
                "sha256:" + "d" * 64,
            ],
            "post_dispatch_outcome_unknown_count": 0,
            "post_dispatch_failure_codes": [],
            "request_retry_count": 0,
            "credential_resolution_count": 40,
            "credential_resolution_success_count": 40,
            "credential_resolution_policy": (
                "AFTER_VERIFIED_TLS_BEFORE_EACH_HTTP_DISPATCH"
            ),
        },
        "production_activation": "NOT_EXECUTED",
    }
    closed = {**closed_core, "document_digest": digest_of(closed_core).value}
    return qualification, closed


class Iteration008CapabilityQualificationTests(unittest.TestCase):
    def _load(
        self,
        qualification: dict[str, object],
        closed: dict[str, object],
    ):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            qualification_path = root / "qualification.json"
            closed_path = root / "closed.json"
            qualification_path.write_bytes(canonical_json_bytes(qualification))
            closed_path.write_bytes(canonical_json_bytes(closed))
            return load_bounded_java_source_semantics_gateway_qualification_binding(
                qualification_path=qualification_path,
                closed_result_path=closed_path,
            )

    def test_exact_eighteen_case_result_creates_six_call_policy(self) -> None:
        qualification, closed = _documents()

        binding = self._load(qualification, closed)
        policy = binding.create_policy(
            configuration=DeepSeekModelConfiguration(),
            conformance_result_ref=binding.conformance_result_ref,
        )

        self.assertEqual(policy.max_provider_calls, 6)
        self.assertEqual(
            policy.policy_ref,
            "ITER-008-BOUNDED-JAVA-SOURCE-SEMANTICS-MODEL-EGRESS-GATEWAY@1.4.10",
        )

    def test_evaluation_definition_and_registry_bind_active_contract(self) -> None:
        cases = tuple(
            BoundedJavaSourceSemanticsWorldModelEvaluationCase(
                role=(
                    BoundedJavaSourceSemanticsWorldModelEvaluationRole.IMPLEMENTATION_ANSWER_DRAFTING
                    if case_id.endswith("DRAFT-017")
                    else BoundedJavaSourceSemanticsWorldModelEvaluationRole.IMPLEMENTATION_ANSWER_REVIEW
                    if case_id.endswith("REVIEW-018")
                    else BoundedJavaSourceSemanticsWorldModelEvaluationRole.IMPLEMENTATION_INVESTIGATION
                ),
                case_id=case_id,
                case_version="1.0.0",
                fixture_ref=f"fixture:{case_id}",
                fixture_digest=digest_of(["fixture", case_id]),
                oracle_ref=f"oracle:{case_id}",
                oracle_digest=digest_of(["oracle", case_id]),
            )
            for case_id, _ in BOUNDED_JAVA_SOURCE_SEMANTICS_QUALIFICATION_CASE_CALLS
        )
        definition = (
            create_bounded_java_source_semantics_world_model_evaluation_definition(
                evaluation_version="1.0.0",
                conformance_result_ref=(
                    "CC-DEEPSEEK-CHAT-NO-TOOLS-001:sha256:" + "1" * 64
                ),
                provider_configuration_fingerprint=(
                    DeepSeekModelConfiguration().fingerprint
                ),
                model_ref="deepseek-v4-pro",
                adapter_version="deepseek-chat-completions-no-tools@7",
                exact_candidate_checkpoint_ref="git:" + "3" * 40,
                environment_ref="iter-008-bounded-capability-evaluation@1",
                reference_strategy_ref="standalone-evaluator@1",
                resource_policy_ref="bounded-two-to-four-no-retry@1",
                cases=cases,
                valid_for_seconds=3600,
            )
        )

        self.assertEqual(len(definition.cases), 18)
        self.assertEqual(definition.strategy_version, "1.5.9")
        self.assertEqual(
            definition.output_schema_digest,
            java_source_semantics_world_model_output_contract_digest(
                JAVA_SOURCE_SEMANTICS_WORLD_MODEL_PROPOSAL_CONTRACT
            ),
        )
        registry = bounded_java_source_semantics_world_model_capability_registry()
        strategy = registry.resolve_strategy(
            definition.strategy_id,
            definition.strategy_version,
        )
        self.assertEqual(
            strategy.implementation_digest,
            definition.implementation_digest,
        )

        with self.assertRaises(DomainError):
            create_bounded_java_source_semantics_world_model_evaluation_definition(
                evaluation_version="1.0.0",
                conformance_result_ref=(
                    "CC-DEEPSEEK-CHAT-NO-TOOLS-001:sha256:" + "1" * 64
                ),
                provider_configuration_fingerprint=(
                    DeepSeekModelConfiguration().fingerprint
                ),
                model_ref="deepseek-v4-pro",
                adapter_version="deepseek-chat-completions-no-tools@7",
                exact_candidate_checkpoint_ref="git:" + "3" * 40,
                environment_ref="iter-008-bounded-capability-evaluation@1",
                reference_strategy_ref="standalone-evaluator@1",
                resource_policy_ref="bounded-two-to-four-no-retry@1",
                cases=tuple(reversed(cases)),
                valid_for_seconds=3600,
            )

    def test_fixed_or_incomplete_evidence_cannot_authorize_bounded_policy(self) -> None:
        qualification, closed = _documents()
        fixed = copy.deepcopy(closed)
        fixed["definition"]["strategy_version"] = "1.2.2"
        fixed_core = {
            key: value for key, value in fixed.items() if key != "document_digest"
        }
        fixed["document_digest"] = digest_of(fixed_core).value

        with self.assertRaises(DomainError):
            self._load(qualification, fixed)

        incomplete = copy.deepcopy(closed)
        incomplete["case_evidence"][3]["trace_digests"].pop()
        incomplete_core = {
            key: value
            for key, value in incomplete.items()
            if key != "document_digest"
        }
        incomplete["document_digest"] = digest_of(incomplete_core).value

        with self.assertRaises(DomainError):
            self._load(qualification, incomplete)

        retried = copy.deepcopy(closed)
        retried["transport_session"]["request_retry_count"] = 1
        retried_core = {
            key: value
            for key, value in retried.items()
            if key != "document_digest"
        }
        retried["document_digest"] = digest_of(retried_core).value

        with self.assertRaises(DomainError):
            self._load(qualification, retried)

    def test_old_provider_resource_policy_or_adapter_cannot_be_reused(self) -> None:
        qualification, closed = _documents()
        for field, value in (
            (
                "resource_policy_ref",
                "forty-calls-across-eighteen-cases-no-retry:"
                "sha256:2c238c532213e1b4c90e7d0ec7aad3f32a07d1d75f475cc3947353f5d622a6f5",
            ),
            ("adapter_version", "openai-chat-completions-no-tools@8"),
        ):
            drifted = copy.deepcopy(closed)
            drifted["definition"][field] = value
            drifted_core = {
                key: item
                for key, item in drifted.items()
                if key != "document_digest"
            }
            drifted["document_digest"] = digest_of(drifted_core).value

            with self.assertRaises(DomainError):
                self._load(qualification, drifted)

    def test_gateway_role_connection_or_credential_drift_is_rejected(self) -> None:
        policy = json.loads(
            qualification_module.BOUNDED_JAVA_SOURCE_SEMANTICS_MODEL_EGRESS_POLICY_PATH.read_text()
        )
        for field, value in (
            ("credential_visibility", "GATEWAY_ONLY"),
            ("descriptor_policy", "PROVISION_SIX_CONSUME_SIX"),
            ("connection_policy", "ONE_REQUEST_ONE_CONNECTION"),
            ("pre_dispatch_tls_policy", "UNBOUNDED"),
        ):
            drifted = copy.deepcopy(policy)
            drifted["roles"]["model_egress_gateway"][field] = value
            with self.subTest(field=field), self.assertRaises(DomainError):
                qualification_module._verify_policy(drifted)

    def test_runtime_provisions_three_tls_candidates_for_four_to_six_calls(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "g3b-freeze.json").write_bytes(
                canonical_json_bytes(
                    {
                        "schema": (
                            world_model_runtime._BOUNDED_JAVA_SOURCE_SEMANTICS_GATEWAY_FREEZE_SCHEMA
                        )
                    }
                )
            )
            self.assertEqual(world_model_runtime._gateway_call_count(root), 6)
            self.assertEqual(world_model_runtime._gateway_descriptor_count(root), 3)
            self.assertEqual(
                world_model_runtime._gateway_qualification_binding_field(root),
                "bounded_java_source_semantics_capability_qualification",
            )
            self.assertEqual(
                world_model_runtime._dispatch_policy(6),
                "FOUR_TO_SIX_ORDERED_CALLS_PER_QUESTION_NO_HIDDEN_RETRY",
            )

        grant_digest = "sha256:" + "3" * 64
        disclosure_digest = "sha256:" + "4" * 64
        receipt_digest = "sha256:" + "5" * 64
        answer = {
            "status": "PASS",
            "run_ref": "run-1",
            "provider_call_count": 5,
            "network_operation_count": 5,
            "source_access_count": 0,
            "evidence_payload_access_count": 0,
            "authority_database_access_count": 0,
            "product_oracle_read_count": 0,
            "baseline_result_read_count": 0,
            "credential_visible": False,
            "provider_type": "DEEPSEEK",
            "adapter_version": "deepseek-chat-completions-no-tools@7",
            "requested_model_ref": "deepseek-v4-pro",
            "conformance_result_ref": (
                "CC-DEEPSEEK-CHAT-NO-TOOLS-001:sha256:" + "a" * 64
            ),
            "resolved_snapshot_ids": ["structure_snapshot_" + "6" * 32],
        }
        gateway_core = {
            "schema": "SWM-WORLD-MODEL-AUTHORIZED-GATEWAY@1",
            "qualified_gateway_baseline": {
                "role": "QUALIFIED_CAPABILITY_BASELINE_ONLY",
                "bounded_source_semantics_capability_freeze_digest": (
                    "sha256:" + "7" * 64
                ),
            },
            "evaluation_grant_digest": grant_digest,
            "disclosure_authorization_digest": disclosure_digest,
            "authorization_receipt_digest": receipt_digest,
            "status": "PASS",
            "provider_call_count": 5,
            "https_dispatch_count": 5,
            "server_statuses": ["RESULT"] * 5,
            "provider_selection_policy": (
                "PRE_DISPATCH_FIRST_CURRENTLY_QUALIFIED_NO_REQUEST_RETRY"
            ),
            "provider_preference_order": ["VOLCENGINE_ARK", "DEEPSEEK"],
            "selected_provider_type": "DEEPSEEK",
            "provider_type": "DEEPSEEK",
            "adapter_version": "deepseek-chat-completions-no-tools@7",
            "requested_model_ref": "deepseek-v4-pro",
            "expected_actual_model_fingerprint": "deepseek-v4-pro",
            "credential_reference": "env:DEEPSEEK_API_KEY",
            "fallback_after_dispatch": False,
            "provider_connection_policy": (
                "PERSISTENT_VERIFIED_TLS_HTTP11_KEEP_ALIVE@2"
            ),
            "maximum_http_dispatches_per_tls_session": 20,
            "maximum_pre_dispatch_tls_handshake_attempts": 3,
            "provider_descriptor_provisioned_count": 3,
            "provider_descriptor_consumed_count": 1,
            "provider_descriptor_unused_closed_count": 2,
            "tls_handshake_attempt_count": 1,
            "tls_handshake_success_count": 1,
            "pre_dispatch_tls_handshake_failure_count": 0,
            "pre_dispatch_tls_failure_codes": [],
            "verified_peer_certificate_sha256s": [
                "sha256:" + "c" * 64
            ],
            "connection_reuse_count": 4,
            "request_retry_count": 0,
            "credential_resolution_count": 5,
            "credential_resolution_success_count": 5,
            "dns_operation_count_in_dispatch_process": 0,
            "credential_value_recorded": False,
            "provider_connection_capability": (
                "INHERITED_EXACT_CONNECTED_SOCKET_SET"
            ),
            "gateway_listener_capability": (
                "INHERITED_EXACT_BOUND_AF_UNIX_LISTENER"
            ),
            "new_socket_syscall_capability": "DENIED_BY_SEATBELT",
            "numeric_provider_address": "8.8.8.8",
            "numeric_provider_address_scope": "PUBLIC_UNICAST",
        }
        gateway = {
            **gateway_core,
            "document_digest": digest_of(
                ["SWM-WORLD-MODEL-AUTHORIZED-GATEWAY@1", gateway_core]
            ).value,
        }

        world_model_runtime._verify_answer_gateway(
            answer,
            gateway,
            {"resolved_snapshot_ids": answer["resolved_snapshot_ids"]},
            "run-1",
            evaluation_grant_digest=grant_digest,
            disclosure_authorization_digest=disclosure_digest,
            authorization_receipt_digest=receipt_digest,
            provider_type="DEEPSEEK",
        )

    def test_bounded_launcher_extension_preserves_historical_closure(self) -> None:
        historical = world_model_runtime._launcher_files()
        bounded = world_model_runtime._launcher_files(include_bounded=True)

        self.assertEqual(
            historical,
            {name: bounded[name] for name in historical},
        )
        self.assertEqual(
            set(bounded).difference(historical),
            {
                "runtime_assets/bounded_java_source_semantics_answer_workload.py",
                "runtime_assets/bounded_java_source_semantics_gateway_workload.py",
            },
        )
        self.assertTrue(all(path.is_file() for path in bounded.values()))


if __name__ == "__main__":
    unittest.main()
