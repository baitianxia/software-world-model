from __future__ import annotations

import copy
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from software_world_model.ai_infrastructure import (
    DEFAULT_DEEPSEEK_ACTUAL_MODEL_FINGERPRINT,
    JAVA_SOURCE_SEMANTICS_WORLD_MODEL_PROPOSAL_CONTRACT,
    ProviderHTTPResponse,
    ProviderOutcomeUnknown,
    load_bounded_java_source_semantics_gateway_qualification_binding,
)
from software_world_model.ai_infrastructure.bounded_java_source_semantics_model_egress_qualification import (
    BOUNDED_JAVA_SOURCE_SEMANTICS_CAPABILITY_ORACLE_DIGEST,
    BOUNDED_JAVA_SOURCE_SEMANTICS_CAPABILITY_SUITE_DIGEST,
)
from software_world_model.cross_cutting import (
    Digest,
    DomainError,
    canonical_json_bytes,
    digest_of,
)
from validation.structure_world_model_iteration_008.capability import (
    authorize,
    cli,
    evaluator,
    freeze,
)
from validation.structure_world_model_iteration_008.capability.manifest import (
    DEFAULT_ORACLE_PATH,
    DEFAULT_SUITE_PATH,
    PINNED_ORACLE_FILE_DIGEST,
    PINNED_PROVIDER_REQUEST_COUNT,
    PINNED_REQUIRED_CASE_CALLS,
    PINNED_REQUIRED_CASE_IDS,
    PINNED_SUITE_FILE_DIGEST,
    build_evaluation_definition,
    case_pairs,
    expected_step_projection,
    expected_step_projections,
    forbidden_events,
    load_capability_inputs,
    sealed_step_input,
    verify_capability_inputs,
)


def _passing_normalized(
    case: dict[str, object],
    step: dict[str, object],
    expected: dict[str, object],
) -> dict[str, object]:
    projection = expected_step_projection(_SUITE, case, step, expected)
    capability = case["capability"]
    constraints = step["semantic_constraints"]
    assert isinstance(constraints, dict)
    if capability == "IMPLEMENTATION_INVESTIGATION":
        result = {
            "step_index": projection["step_index"],
            "trace_digest": projection["trace_digest"],
            "operation": projection["operation"],
            "snapshot_id": projection["snapshot_id"],
            "search_terms": [],
            "limit": projection["limit"],
            "candidate_result_id": projection["candidate_result_id"],
            "candidate_result_digest": projection["candidate_result_digest"],
            "method_refs": projection["method_refs"],
            "entity_refs": projection["entity_refs"],
            "direction": projection["direction"],
            "predicate": projection["predicate"],
            "max_depth": projection["max_depth"],
            "max_paths": projection["max_paths"],
            "max_expansions": projection["max_expansions"],
            "finish_reason": None,
            "evidence_requests": projection["evidence_requests"],
        }
        search_groups = constraints.get("search_term_concept_groups", [])
        if search_groups:
            result["search_terms"] = [group[0] for group in search_groups]
        finish_groups = constraints.get("finish_reason_concept_groups", [])
        if finish_groups:
            result["finish_reason"] = " ".join(group[0] for group in finish_groups)
        return result
    if capability == "IMPLEMENTATION_ANSWER_DRAFTING":
        groups = constraints.get("answer_order_groups") or constraints.get(
            "answer_concept_groups"
        )
        return {
            **projection,
            "answer": " then ".join(group[0] for group in groups),
        }
    return projection


def _passing_model_output(
    case: dict[str, object],
    step: dict[str, object],
    expected: dict[str, object],
) -> dict[str, object]:
    if case["capability"] != "IMPLEMENTATION_INVESTIGATION":
        return _passing_normalized(case, step, expected)
    projection = expected_step_projection(_SUITE, case, step, expected)
    constraints = step["semantic_constraints"]
    assert isinstance(constraints, dict)
    search_groups = constraints.get("search_term_concept_groups", [])
    finish_groups = constraints.get("finish_reason_concept_groups", [])
    relation_intent = None
    if projection["operation"] == "direct_neighborhood":
        relation_intent = {
            ("OUTGOING", "CALLS"): "OUTGOING_CALLS",
            ("INCOMING", "CALLS"): "INCOMING_CALLS",
            ("BOTH", "CALLS"): "BOTH_CALLS",
            ("INCOMING", "DECLARES_METHOD"): "DECLARING_TYPE",
        }[(projection["direction"], projection["predicate"])]
    return {
        "operation": projection["operation"],
        "search_terms": [group[0] for group in search_groups],
        "relation_intent": relation_intent,
        "finish_reason": (
            " ".join(group[0] for group in finish_groups)
            if finish_groups
            else None
        ),
        "evidence_requests": (
            copy.deepcopy(case["evidence_requests"])
            if step["step_index"] == 1
            else []
        ),
    }


def _case_documents(
    case: dict[str, object], oracle_case: dict[str, object]
) -> tuple[dict[str, object], dict[str, object]]:
    packet_steps = []
    result_steps = []
    for call_index, (step, expected) in enumerate(
        zip(case["steps"], oracle_case["steps"]), start=1
    ):
        sealed = sealed_step_input(_SUITE, case, step)
        input_digest = digest_of(sealed).value
        normalized = _passing_normalized(case, step, expected)
        normalized_digest = digest_of(normalized).value
        call_id = f"{case['case_id']}:call-{call_index}"
        packet_steps.append(
            {
                "call_index": call_index,
                "case_call_id": call_id,
                "sealed_input": sealed,
                "sealed_input_digest": input_digest,
                "projection_fields": _SUITE["projection_sets"][
                    step["projection_ref"]
                ],
                "semantic_constraints": step["semantic_constraints"],
                "expected_projections": list(
                    expected_step_projections(
                        _SUITE, case, step, expected
                    )
                ),
                "forbidden_events": forbidden_events(_ORACLE, expected),
            }
        )
        result_steps.append(
            {
                "call_index": call_index,
                "case_call_id": call_id,
                "sealed_input_digest": input_digest,
                "normalized_result": normalized,
                "normalized_result_digest": normalized_digest,
                "evidence_trace_digest": evaluator._step_trace_digest(
                    str(case["case_id"]),
                    call_index,
                    input_digest,
                    normalized_digest,
                ),
            }
        )
    packet_core = {
        "schema": evaluator.PACKET_SCHEMA,
        "suite_ref": _SUITE["suite_ref"],
        "suite_digest": PINNED_SUITE_FILE_DIGEST,
        "oracle_ref": _ORACLE["oracle_ref"],
        "oracle_digest": PINNED_ORACLE_FILE_DIGEST,
        "case": {
            "case_id": case["case_id"],
            "capability": case["capability"],
            "steps": packet_steps,
        },
    }
    count = len(packet_steps)
    result_core = {
        "schema": evaluator.RESULT_SCHEMA,
        "suite_ref": _SUITE["suite_ref"],
        "suite_digest": PINNED_SUITE_FILE_DIGEST,
        "case_id": case["case_id"],
        "capability": case["capability"],
        "step_results": result_steps,
        "operation_audit": {
            "model_call_count": count,
            "provider_request_count": count,
            "unique_model_call_id_count": count,
            "hidden_retry_count": 0,
            "product_oracle_read_count": 0,
            "product_suite_read_count": 0,
            "repository_read_count": 0,
            "source_access_count": 0,
            "evidence_payload_access_count": 0,
            "project_dictionary_access_count": 0,
            "project_name_branch_count": 0,
            "self_review_count": 0,
            "observed_events": [],
            "model_input_item_ids": [
                ["instruction", "sealed-case-input", "qualification"]
                for _ in range(count)
            ],
        },
    }
    return (
        {
            **packet_core,
            "document_digest": evaluator._document_digest(packet_core),
        },
        {
            **result_core,
            "document_digest": evaluator._document_digest(result_core),
        },
    )


_SUITE, _ORACLE = load_capability_inputs()


def _transport_session_audit(calls: int, *, unknown: int = 0):
    return {
        "schema": "SWM-DEEPSEEK-TRANSPORT-SESSION-AUDIT@1",
        "connection_policy": "PERSISTENT_VERIFIED_TLS_HTTP11_KEEP_ALIVE@1",
        "maximum_pre_dispatch_tls_handshake_attempts": 3,
        "tls_handshake_attempt_count": 1 if calls else 0,
        "tls_handshake_success_count": 1 if calls else 0,
        "pre_dispatch_tls_handshake_failure_count": 0,
        "pre_dispatch_tls_failure_codes": [],
        "http_dispatch_count": calls,
        "connection_reuse_count": max(0, calls - 1),
        "verified_peer_certificate_sha256s": (
            ["sha256:" + "c" * 64] if calls else []
        ),
        "post_dispatch_outcome_unknown_count": unknown,
        "post_dispatch_failure_codes": ["TIMEOUT"] * unknown,
        "request_retry_count": 0,
        "credential_resolution_count": calls,
        "credential_resolution_success_count": calls,
        "credential_resolution_policy": (
            "AFTER_VERIFIED_TLS_BEFORE_EACH_HTTP_DISPATCH"
        ),
    }


class _EchoingDeepSeekTransport:
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
            },
            separators=(",", ":"),
        )
        return ProviderHTTPResponse(
            status_code=200,
            headers={"x-tt-logid": f"iter008-conformance-{self.calls}"},
            body=json.dumps(
                {
                    "id": f"chatcmpl_iter008_{self.calls}",
                    "object": "chat.completion",
                    "model": DEFAULT_DEEPSEEK_ACTUAL_MODEL_FINGERPRINT,
                    "choices": [
                        {
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": content,
                            },
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
        return _transport_session_audit(self.calls)


class _PassingCapabilityTransport:
    def __init__(self) -> None:
        self.calls = 0
        self._outputs = {}
        for case, oracle_case in case_pairs(_SUITE, _ORACLE):
            for call_index, (step, expected) in enumerate(
                zip(case["steps"], oracle_case["steps"]), start=1
            ):
                self._outputs[f"{case['case_id']}:call-{call_index}"] = (
                    _passing_model_output(case, step, expected)
                )
        self._outputs[
            "WM-JSS-I8-ALL-SIMPLE-PATHS-008:call-3"
        ]["relation_intent"] = "BOTH_CALLS"
        for call_id in (
            "WM-JSS-I8-MAX-FOUR-010:call-3",
            "WM-JSS-I8-BUDGET-EXHAUSTION-011:call-4",
        ):
            self._outputs[call_id].update(
                {
                    "operation": "FINISH",
                    "relation_intent": None,
                    "finish_reason": "typed support is sufficient",
                }
            )

    def post_json(self, **arguments):
        self.calls += 1
        body = json.loads(arguments["body"])
        state = None
        for message in body["messages"]:
            try:
                candidate = json.loads(message["content"])
            except json.JSONDecodeError:
                continue
            if isinstance(candidate, dict) and "case_id" in candidate:
                state = candidate
                break
        if state is None:
            raise ValueError("sealed case state is absent from provider request")
        content = json.dumps(
            self._outputs[state["case_id"]], separators=(",", ":")
        )
        return ProviderHTTPResponse(
            status_code=200,
            headers={"x-tt-logid": f"iter008-capability-{self.calls}"},
            body=json.dumps(
                {
                    "id": f"chatcmpl_iter008_capability_{self.calls}",
                    "object": "chat.completion",
                    "model": DEFAULT_DEEPSEEK_ACTUAL_MODEL_FINGERPRINT,
                    "choices": [
                        {
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": content,
                            },
                            "finish_reason": "stop",
                        }
                    ],
                    "usage": {
                        "prompt_tokens": 20,
                        "completion_tokens": 10,
                        "total_tokens": 30,
                    },
                }
            ).encode(),
        )

    def session_audit(self):
        return _transport_session_audit(self.calls)


class _UnknownDeepSeekTransport:
    def __init__(self) -> None:
        self.calls = 0

    def post_json(self, **_arguments):
        self.calls += 1
        raise ProviderOutcomeUnknown(
            "fixture outcome unknown", reason_code="TIMEOUT"
        )

    def session_audit(self):
        return _transport_session_audit(self.calls, unknown=self.calls)


class Iteration008CapabilityHarnessTests(unittest.TestCase):
    def test_pinned_inputs_bind_raw_files_and_product_loader(self) -> None:
        self.assertEqual(
            "sha256:" + hashlib.sha256(DEFAULT_SUITE_PATH.read_bytes()).hexdigest(),
            PINNED_SUITE_FILE_DIGEST,
        )
        self.assertEqual(
            "sha256:" + hashlib.sha256(DEFAULT_ORACLE_PATH.read_bytes()).hexdigest(),
            PINNED_ORACLE_FILE_DIGEST,
        )
        self.assertEqual(
            BOUNDED_JAVA_SOURCE_SEMANTICS_CAPABILITY_SUITE_DIGEST.value,
            PINNED_SUITE_FILE_DIGEST,
        )
        self.assertEqual(
            BOUNDED_JAVA_SOURCE_SEMANTICS_CAPABILITY_ORACLE_DIGEST.value,
            PINNED_ORACLE_FILE_DIGEST,
        )
        self.assertEqual(len(PINNED_REQUIRED_CASE_CALLS), 18)
        self.assertEqual(PINNED_PROVIDER_REQUEST_COUNT, 40)
        self.assertEqual(
            tuple(case["case_id"] for case in _SUITE["cases"]),
            PINNED_REQUIRED_CASE_IDS,
        )

    def test_definition_binds_exact_eighteen_case_contract(self) -> None:
        definition = build_evaluation_definition(
            _SUITE,
            _ORACLE,
            conformance_result_ref=(
                "CC-DEEPSEEK-CHAT-NO-TOOLS-001:sha256:" + "1" * 64
            ),
            provider_configuration_fingerprint=Digest("sha256:" + "2" * 64),
            actual_model_fingerprint="deepseek-v4-pro",
            adapter_version="deepseek-chat-completions-no-tools@3",
            exact_candidate_checkpoint_ref="git:" + "3" * 40,
            environment_ref="iter-008-bounded-capability@1",
            reference_strategy_ref="standalone-evaluator@1",
            resource_policy_ref="forty-no-retry@1",
            valid_for_seconds=3600,
        )
        self.assertEqual(definition.strategy_version, "1.5.2")
        self.assertEqual(len(definition.cases), 18)
        self.assertEqual(
            tuple(item.case_id for item in definition.cases),
            PINNED_REQUIRED_CASE_IDS,
        )
        self.assertEqual(
            JAVA_SOURCE_SEMANTICS_WORLD_MODEL_PROPOSAL_CONTRACT.available_operations,
            (
                "implementation_candidates",
                "method_implementations",
                "declared_method_inventory",
                "direct_neighborhood",
                "path_exists",
                "all_simple_paths",
                "FINISH",
            ),
        )

    def test_sealed_previous_result_uses_product_progress_boundary(self) -> None:
        case = next(
            item
            for item in _SUITE["cases"]
            if item["case_id"] == "WM-JSS-I8-DECLARED-INVENTORY-005"
        )
        sealed = sealed_step_input(_SUITE, case, case["steps"][1])
        previous = sealed["previous_result"]
        self.assertIsInstance(previous, dict)
        result = previous["results"][0]
        self.assertNotIn("query_result_completeness", result)
        self.assertNotIn("knowledge_representation", result)
        self.assertNotIn("business_discovery_recall", result)
        self.assertIn("entities", result["payload"])
        self.assertEqual(
            sealed["progress_receipt"]["completeness"],
            {
                "query_result": "COMPLETE",
                "knowledge_representation": "COMPLETE",
                "business_discovery_recall": "UNKNOWN",
                "bounded_absence_allowed": False,
                "missing_limitation_codes": [
                    "BUSINESS_DISCOVERY_RECALL_UNPROVEN"
                ],
            },
        )

    def test_all_eighteen_deterministic_evaluator_examples_pass(self) -> None:
        request_count = 0
        for case, oracle_case in case_pairs(_SUITE, _ORACLE):
            packet, result = _case_documents(dict(case), dict(oracle_case))
            review = evaluator.evaluate(packet, result)
            self.assertEqual(review["conclusion"], "PASS", case["case_id"])
            self.assertTrue(review["projection_exact"])
            self.assertTrue(review["semantic_constraints_satisfied"])
            self.assertEqual(
                len(set(review["evidence_trace_digests"])),
                len(review["evidence_trace_digests"]),
            )
            request_count += review["model_call_count"]
        self.assertEqual(request_count, PINNED_PROVIDER_REQUEST_COUNT)

    def test_frozen_transition_projection_is_singleton_and_exact(self) -> None:
        case, oracle_case = case_pairs(_SUITE, _ORACLE)[5]
        packet, result = _case_documents(dict(case), dict(oracle_case))
        accepted = expected_step_projections(
            _SUITE,
            case,
            case["steps"][1],
            oracle_case["steps"][1],
        )
        self.assertEqual(len(accepted), 1)
        normalized = result["step_results"][1]["normalized_result"]
        normalized["operation"] = "FINISH"
        normalized_digest = digest_of(normalized).value
        result["step_results"][1]["normalized_result_digest"] = normalized_digest
        result["step_results"][1]["evidence_trace_digest"] = (
            evaluator._step_trace_digest(
                str(case["case_id"]),
                2,
                result["step_results"][1]["sealed_input_digest"],
                normalized_digest,
            )
        )
        core = {
            key: value for key, value in result.items() if key != "document_digest"
        }
        result["document_digest"] = evaluator._document_digest(core)

        review = evaluator.evaluate(packet, result)

        self.assertEqual(review["conclusion"], "FAIL")
        self.assertIn("CALL_2:CONTRACT_PROJECTION_NOT_EXACT", review["findings"])

    def test_tampered_ref_fails_exact_oracle(self) -> None:
        case, oracle_case = case_pairs(_SUITE, _ORACLE)[2]
        packet, result = _case_documents(dict(case), dict(oracle_case))
        result["step_results"][0]["normalized_result"]["method_refs"][0][
            "entity_root_id"
        ] = "entity_root_ffffffffffffffffffffffffffffffff"
        normalized = result["step_results"][0]["normalized_result"]
        result["step_results"][0]["normalized_result_digest"] = digest_of(
            normalized
        ).value
        result["step_results"][0]["evidence_trace_digest"] = (
            evaluator._step_trace_digest(
                str(case["case_id"]),
                1,
                result["step_results"][0]["sealed_input_digest"],
                result["step_results"][0]["normalized_result_digest"],
            )
        )
        core = {key: value for key, value in result.items() if key != "document_digest"}
        result["document_digest"] = evaluator._document_digest(core)
        review = evaluator.evaluate(packet, result)
        self.assertEqual(review["conclusion"], "FAIL")
        self.assertFalse(review["projection_exact"])

    def test_tampered_per_call_trace_is_rejected(self) -> None:
        case, oracle_case = case_pairs(_SUITE, _ORACLE)[8]
        packet, result = _case_documents(dict(case), dict(oracle_case))
        result["step_results"][1]["evidence_trace_digest"] = "sha256:" + "f" * 64
        core = {key: value for key, value in result.items() if key != "document_digest"}
        result["document_digest"] = evaluator._document_digest(core)
        with self.assertRaisesRegex(ValueError, "evidence trace"):
            evaluator.evaluate(packet, result)

    def test_manifest_rejects_reordered_oracle(self) -> None:
        oracle = copy.deepcopy(_ORACLE)
        oracle["cases"][0], oracle["cases"][1] = (
            oracle["cases"][1],
            oracle["cases"][0],
        )
        with self.assertRaises(DomainError):
            verify_capability_inputs(_SUITE, oracle)

    def test_zero_provider_preflight_requests_only_two_conformance_calls(self) -> None:
        fake_identity = {
            "commit": "1" * 40,
            "tree": "2" * 40,
            "worktree_status": "CLEAN",
            "identity_scope": "EXACT_GIT_COMMIT_AND_TREE@1",
        }
        with tempfile.TemporaryDirectory() as directory, patch.object(
            freeze, "_candidate_identity", return_value=fake_identity
        ):
            root = Path(directory).resolve()
            preflight_path, request_path, preflight = freeze.create_preflight(
                output_directory=root / "preflight",
                created_at=datetime(2026, 8, 17, tzinfo=timezone.utc),
            )
            self.assertTrue(preflight_path.is_file())
            self.assertTrue(request_path.is_file())
            self.assertFalse(preflight["external_model_called"])
            self.assertFalse(preflight["hidden_canary_disclosed"])
            self.assertEqual(
                preflight["deepseek_conformance"]["authorization_scope"][
                    "planned_provider_call_count"
                ],
                2,
            )
            request = authorize._load_request(request_path)
            self.assertEqual(request["phase"], "DEEPSEEK_CONFORMANCE")
            self.assertEqual(
                request["authorization_scope"]["adapter_version"],
                "deepseek-chat-completions-no-tools@3",
            )
            self.assertEqual(
                request["authorization_scope"]["connection_policy"],
                "PERSISTENT_VERIFIED_TLS_HTTP11_KEEP_ALIVE@1",
            )
            self.assertEqual(
                request["authorization_scope"][
                    "maximum_pre_dispatch_tls_handshake_attempts"
                ],
                3,
            )
            self.assertEqual(
                request["authorization_scope"]["credential_resolution_policy"],
                "AFTER_VERIFIED_TLS_BEFORE_EACH_HTTP_DISPATCH",
            )
            self.assertFalse(
                request["authorization_scope"]["request_retry_allowed"]
            )
            verified = freeze.verify_preflight(preflight_path)
            self.assertEqual(
                verified["document_digest"], preflight["document_digest"]
            )

    def test_authorization_must_postdate_exact_request(self) -> None:
        fake_identity = {
            "commit": "1" * 40,
            "tree": "2" * 40,
            "worktree_status": "CLEAN",
            "identity_scope": "EXACT_GIT_COMMIT_AND_TREE@1",
        }
        created = datetime(2026, 8, 17, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as directory, patch.object(
            freeze, "_candidate_identity", return_value=fake_identity
        ):
            root = Path(directory).resolve()
            _, request_path, _ = freeze.create_preflight(
                output_directory=root / "preflight", created_at=created
            )
            with self.assertRaises(authorize.AuthorizationError):
                authorize.create_authorization(
                    request_path=request_path,
                    output_path=root / "authorization-too-early.json",
                    authorized_at=created - timedelta(seconds=1),
                    authorization_ref="codex-user-message:sha256:" + "a" * 64,
                    single_use_result_directory=root / "result-too-early",
                )
            with self.assertRaises(authorize.AuthorizationError):
                authorize.create_authorization(
                    request_path=request_path,
                    output_path=root / "authorization-malformed-ref.json",
                    authorized_at=created + timedelta(seconds=1),
                    authorization_ref=(
                        "codex-user-message:sha256:" + "z" * 64
                    ),
                    single_use_result_directory=root / "result-malformed-ref",
                )
            output, document = authorize.create_authorization(
                request_path=request_path,
                output_path=root / "authorization.json",
                authorized_at=created + timedelta(seconds=1),
                authorization_ref="codex-user-message:sha256:" + "b" * 64,
                single_use_result_directory=root / "result",
            )
            self.assertTrue(output.is_file())
            self.assertEqual(document["phase"], "DEEPSEEK_CONFORMANCE")
            self.assertFalse(document["hidden_canary_disclosure_authorized"])

    def test_authorization_request_must_bind_the_executed_preflight(self) -> None:
        fake_identity = {
            "commit": "1" * 40,
            "tree": "2" * 40,
            "worktree_status": "CLEAN",
            "identity_scope": "EXACT_GIT_COMMIT_AND_TREE@1",
        }
        created = datetime(2026, 8, 17, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as directory, patch.object(
            freeze, "_candidate_identity", return_value=fake_identity
        ):
            root = Path(directory).resolve()
            preflight_path, request_path, _ = freeze.create_preflight(
                output_directory=root / "preflight", created_at=created
            )
            request = authorize._load_request(request_path)
            request["authorization_scope"]["planned_provider_call_count"] = 3
            request_core = {
                key: value
                for key, value in request.items()
                if key != "document_digest"
            }
            request["document_digest"] = digest_of(
                [request["schema"], request_core]
            ).value
            request_path.write_bytes(canonical_json_bytes(request))
            authorization_path, _ = authorize.create_authorization(
                request_path=request_path,
                output_path=root / "authorization.json",
                authorized_at=created + timedelta(seconds=1),
                authorization_ref="codex-user-message:sha256:" + "f" * 64,
                single_use_result_directory=root / "result",
            )
            transport = _EchoingDeepSeekTransport()
            with self.assertRaisesRegex(DomainError, "exact freeze"):
                cli._run_authorized_conformance(
                    preflight_path=preflight_path,
                    authorization_path=authorization_path,
                    environment={"DEEPSEEK_API_KEY": "must-not-be-read"},
                    transport=transport,
                )
            self.assertEqual(transport.calls, 0)
            self.assertFalse((root / "result").exists())

    def test_authorized_conformance_wrapper_consumes_exactly_two_calls(self) -> None:
        fake_identity = {
            "commit": "1" * 40,
            "tree": "2" * 40,
            "worktree_status": "CLEAN",
            "identity_scope": "EXACT_GIT_COMMIT_AND_TREE@1",
        }
        created = datetime(2026, 8, 17, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as directory, patch.object(
            freeze, "_candidate_identity", return_value=fake_identity
        ):
            root = Path(directory).resolve()
            preflight_path, request_path, _ = freeze.create_preflight(
                output_directory=root / "preflight", created_at=created
            )
            authorization_path, _ = authorize.create_authorization(
                request_path=request_path,
                output_path=root / "authorization.json",
                authorized_at=created + timedelta(seconds=1),
                authorization_ref="codex-user-message:sha256:" + "c" * 64,
                single_use_result_directory=root / "result",
            )
            transport = _EchoingDeepSeekTransport()
            payload, code = cli._run_authorized_conformance(
                preflight_path=preflight_path,
                authorization_path=authorization_path,
                environment={
                    "DEEPSEEK_API_KEY": "fixture-secret-never-persist"
                },
                transport=transport,
            )
            self.assertEqual(code, 0)
            self.assertEqual(payload["status"], "CONFORMANCE_PASS")
            self.assertEqual(payload["provider_request_count"], 2)
            self.assertEqual(transport.calls, 2)
            self.assertTrue((root / "result" / "terminal.json").is_file())
            self.assertNotIn(
                "fixture-secret-never-persist",
                (root / "result" / "terminal.json").read_text(),
            )

    def test_unknown_conformance_outcome_is_sealed_without_retry(self) -> None:
        fake_identity = {
            "commit": "1" * 40,
            "tree": "2" * 40,
            "worktree_status": "CLEAN",
            "identity_scope": "EXACT_GIT_COMMIT_AND_TREE@1",
        }
        created = datetime(2026, 8, 17, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as directory, patch.object(
            freeze, "_candidate_identity", return_value=fake_identity
        ):
            root = Path(directory).resolve()
            preflight_path, request_path, _ = freeze.create_preflight(
                output_directory=root / "preflight", created_at=created
            )
            authorization_path, _ = authorize.create_authorization(
                request_path=request_path,
                output_path=root / "authorization.json",
                authorized_at=created + timedelta(seconds=1),
                authorization_ref="codex-user-message:sha256:" + "9" * 64,
                single_use_result_directory=root / "result",
            )
            transport = _UnknownDeepSeekTransport()
            with self.assertRaises(ProviderOutcomeUnknown):
                cli._run_authorized_conformance(
                    preflight_path=preflight_path,
                    authorization_path=authorization_path,
                    environment={
                        "DEEPSEEK_API_KEY": "fixture-secret-never-persist"
                    },
                    transport=transport,
                )
            self.assertEqual(transport.calls, 1)
            failure = json.loads((root / "result" / "failure.json").read_text())
            terminal = json.loads(
                (root / "result" / "terminal.json").read_text()
            )
            self.assertEqual(failure["status"], "PROVIDER_OUTCOME_UNKNOWN")
            self.assertEqual(failure["provider_outcome_reason_code"], "TIMEOUT")
            self.assertEqual(failure["attempted_provider_request_count"], 1)
            self.assertEqual(len(failure["attempted_request_body_digests"]), 1)
            self.assertEqual(terminal["status"], "PROVIDER_OUTCOME_UNKNOWN")
            self.assertEqual(terminal["provider_request_count"], 1)
            self.assertTrue(terminal["authorization_consumed"])
            self.assertFalse(terminal["retry_permitted_with_same_authorization"])
            self.assertNotIn(
                "fixture-secret-never-persist",
                (root / "result" / "failure.json").read_text(),
            )

    def test_unknown_capability_outcome_is_sealed_without_retry(self) -> None:
        fake_identity = {
            "commit": "1" * 40,
            "tree": "2" * 40,
            "worktree_status": "CLEAN",
            "identity_scope": "EXACT_GIT_COMMIT_AND_TREE@1",
        }
        created = datetime(2026, 8, 17, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as directory, patch.object(
            freeze, "_candidate_identity", return_value=fake_identity
        ):
            root = Path(directory).resolve()
            preflight_path, conformance_request, _ = freeze.create_preflight(
                output_directory=root / "preflight", created_at=created
            )
            conformance_authorization, _ = authorize.create_authorization(
                request_path=conformance_request,
                output_path=root / "conformance-authorization.json",
                authorized_at=created + timedelta(seconds=1),
                authorization_ref="codex-user-message:sha256:" + "8" * 64,
                single_use_result_directory=root / "conformance-result",
            )
            conformance_payload, conformance_code = (
                cli._run_authorized_conformance(
                    preflight_path=preflight_path,
                    authorization_path=conformance_authorization,
                    environment={
                        "DEEPSEEK_API_KEY": "fixture-secret-never-persist"
                    },
                    transport=_EchoingDeepSeekTransport(),
                )
            )
            self.assertEqual(conformance_code, 0)
            capability_created = datetime.now(timezone.utc) + timedelta(
                seconds=1
            )
            capability_freeze_path, capability_request, capability_freeze = (
                freeze.create_capability_freeze(
                    preflight_path=preflight_path,
                    conformance_result_path=Path(
                        conformance_payload["result_path"]
                    ),
                    output_directory=root / "capability-freeze",
                    created_at=capability_created,
                )
            )
            capability_authorization, _ = authorize.create_authorization(
                request_path=capability_request,
                output_path=root / "capability-authorization.json",
                authorized_at=capability_created + timedelta(seconds=1),
                authorization_ref="codex-user-message:sha256:" + "7" * 64,
                single_use_result_directory=root / "capability-result",
            )
            transport = _UnknownDeepSeekTransport()
            with self.assertRaises(ProviderOutcomeUnknown):
                cli._run_authorized_capability(
                    freeze=capability_freeze,
                    freeze_path=capability_freeze_path,
                    authorization_path=capability_authorization,
                    conformance_result_path=Path(
                        conformance_payload["result_path"]
                    ),
                    environment={
                        "DEEPSEEK_API_KEY": "fixture-secret-never-persist"
                    },
                    transport=transport,
                )
            self.assertEqual(transport.calls, 1)
            failure = json.loads(
                (root / "capability-result" / "failure.json").read_text()
            )
            terminal = json.loads(
                (root / "capability-result" / "terminal.json").read_text()
            )
            self.assertEqual(failure["status"], "PROVIDER_OUTCOME_UNKNOWN")
            self.assertEqual(failure["failure_code"], "TIMEOUT")
            self.assertEqual(failure["attempted_provider_request_count"], 1)
            self.assertEqual(terminal["status"], "PROVIDER_OUTCOME_UNKNOWN")
            self.assertEqual(terminal["provider_request_count"], 1)
            self.assertFalse(terminal["retry_permitted_with_same_authorization"])
            failure_text = (
                root / "capability-result" / "failure.json"
            ).read_text()
            self.assertNotIn("fixture-secret-never-persist", failure_text)
            self.assertFalse(failure["raw_prompt_persisted"])
            self.assertFalse(failure["raw_response_persisted"])

    def test_full_fake_transport_flow_closes_forty_call_result(self) -> None:
        fake_identity = {
            "commit": "1" * 40,
            "tree": "2" * 40,
            "worktree_status": "CLEAN",
            "identity_scope": "EXACT_GIT_COMMIT_AND_TREE@1",
        }
        created = datetime(2026, 8, 17, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as directory, patch.object(
            freeze, "_candidate_identity", return_value=fake_identity
        ):
            root = Path(directory).resolve()
            preflight_path, conformance_request, _ = freeze.create_preflight(
                output_directory=root / "preflight", created_at=created
            )
            conformance_authorization, _ = authorize.create_authorization(
                request_path=conformance_request,
                output_path=root / "conformance-authorization.json",
                authorized_at=created + timedelta(seconds=1),
                authorization_ref="codex-user-message:sha256:" + "d" * 64,
                single_use_result_directory=root / "conformance-result",
            )
            conformance_payload, conformance_code = (
                cli._run_authorized_conformance(
                    preflight_path=preflight_path,
                    authorization_path=conformance_authorization,
                    environment={
                        "DEEPSEEK_API_KEY": "fixture-secret-never-persist"
                    },
                    transport=_EchoingDeepSeekTransport(),
                )
            )
            self.assertEqual(conformance_code, 0)
            capability_created = datetime.now(timezone.utc) + timedelta(
                seconds=1
            )
            capability_freeze_path, capability_request, capability_freeze = (
                freeze.create_capability_freeze(
                    preflight_path=preflight_path,
                    conformance_result_path=Path(
                        conformance_payload["result_path"]
                    ),
                    output_directory=root / "capability-freeze",
                    created_at=capability_created,
                )
            )
            scope = capability_freeze["dispatch_contract"][
                "authorization_scope"
            ]
            self.assertEqual(scope["planned_provider_call_count"], 40)
            self.assertEqual(
                scope["connection_policy"],
                "PERSISTENT_VERIFIED_TLS_HTTP11_KEEP_ALIVE@1",
            )
            self.assertEqual(
                scope["maximum_pre_dispatch_tls_handshake_attempts"], 3
            )
            self.assertEqual(
                scope["credential_resolution_policy"],
                "AFTER_VERIFIED_TLS_BEFORE_EACH_HTTP_DISPATCH",
            )
            self.assertFalse(scope["request_retry_allowed"])
            self.assertEqual(
                scope["payload_boundary"],
                "FORTY_SYNTHETIC_BOUNDED_PROPOSAL_CALLS_ACROSS_"
                "EIGHTEEN_CASES_NO_PRODUCT_QUESTION_SOURCE_EVIDENCE_OR_"
                "HIDDEN_CANARY",
            )
            with patch.object(
                cli, "_candidate_identity", return_value=fake_identity
            ):
                self.assertEqual(
                    cli._verify_capability_freeze(
                        capability_freeze_path,
                        Path(conformance_payload["result_path"]),
                    ),
                    capability_freeze,
                )
            tampered_freeze = copy.deepcopy(capability_freeze)
            tampered_freeze["evaluation_definition"]["strategy_version"] = (
                "1.2.2"
            )
            tampered_core = {
                key: value
                for key, value in tampered_freeze.items()
                if key != "document_digest"
            }
            tampered_freeze["document_digest"] = digest_of(
                [tampered_freeze["schema"], tampered_core]
            ).value
            tampered_path = root / "tampered-capability-freeze.json"
            tampered_path.write_bytes(canonical_json_bytes(tampered_freeze))
            with patch.object(
                cli, "_candidate_identity", return_value=fake_identity
            ), self.assertRaises(DomainError):
                cli._verify_capability_freeze(
                    tampered_path,
                    Path(conformance_payload["result_path"]),
                )
            capability_authorization, _ = authorize.create_authorization(
                request_path=capability_request,
                output_path=root / "capability-authorization.json",
                authorized_at=capability_created + timedelta(seconds=1),
                authorization_ref="codex-user-message:sha256:" + "e" * 64,
                single_use_result_directory=root / "capability-result",
            )
            transport = _PassingCapabilityTransport()
            payload, code = cli._run_authorized_capability(
                freeze=capability_freeze,
                freeze_path=capability_freeze_path,
                authorization_path=capability_authorization,
                conformance_result_path=Path(conformance_payload["result_path"]),
                environment={
                    "DEEPSEEK_API_KEY": "fixture-secret-never-persist"
                },
                transport=transport,
            )
            if code:
                closed = json.loads(
                    (
                        root
                        / "capability-result"
                        / "closed-evaluation-result.json"
                    ).read_text()
                )
                self.fail(
                    json.dumps(
                        {
                            "payload": payload,
                            "result": closed.get("result"),
                            "case_evidence": [
                                {
                                    "case_id": item.get("case_id"),
                                    "status": item.get("status"),
                                    "reason_code": item.get("reason_code"),
                                }
                                for item in closed.get("case_evidence", [])
                            ],
                            "attempts": [
                                {
                                    "attempt_id": item.get("attempt_id"),
                                    "status": item.get("status"),
                                    "reason_code": item.get("reason_code"),
                                }
                                for item in closed.get("attempts", [])
                            ],
                        },
                        sort_keys=True,
                    )
                )
            self.assertEqual(code, 0)
            self.assertEqual(payload["status"], "CAPABILITY_EVALUATION_PASS")
            self.assertEqual(payload["case_count"], 18)
            self.assertEqual(payload["provider_request_count"], 40)
            self.assertEqual(transport.calls, 40)
            binding = load_bounded_java_source_semantics_gateway_qualification_binding(
                qualification_path=payload["qualification_path"],
                closed_result_path=payload["result_path"],
            )
            self.assertEqual(
                binding.capability_qualification_ref,
                payload["qualification_ref"],
            )
            self.assertEqual(
                binding.closed_capability_result_digest.value,
                json.loads(Path(payload["result_path"]).read_text())[
                    "document_digest"
                ],
            )


if __name__ == "__main__":
    unittest.main()
