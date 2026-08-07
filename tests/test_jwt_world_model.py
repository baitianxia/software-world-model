from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from software_world_model.ai_infrastructure import (
    ArkChatConformanceQualification,
    ProviderHTTPResponse,
    VolcengineArkModelConfiguration,
)
from software_world_model.cross_cutting import Digest, DomainError, ErrorCode, digest_of
from validation.jwt_iteration_001.manifest import (
    DIRECT_AGENT_PROMPT,
    DIRECT_AGENT_PROMPT_REF,
    DIRECT_AGENT_TOOL_POLICY_REF,
    DIRECT_ORACLE_DRAFT_SCHEMA,
    PARENT_COMMIT,
    QUESTION,
    REPOSITORY_IDENTITY,
    TARGET_COMMIT,
    _NEEDS,
    _direct_requirement_view,
    freeze_jwt_run_configuration,
    seal_direct_oracle,
)
from validation.jwt_iteration_001.comparison import (
    COMPARISON_REVIEW_ATTESTATION_SCHEMA,
    seal_reviewed_capability_comparison,
    verify_capability_comparison,
)
from validation.jwt_iteration_001.evaluation_bridge import (
    activate_evaluated_strategy,
    register_capability_evaluation,
)
from validation.jwt_iteration_001.world_model import (
    _frozen_text_covers_obligations,
    run_world_model,
    verify_world_model_result,
)


class WorldModelTransport:
    def __init__(self, *, stop_immediately=False):
        self.calls = []
        self.stop_immediately = stop_immediately

    def post_json(self, **arguments):
        self.calls.append(arguments)
        wire = json.loads(arguments["body"])
        authorized = json.loads(wire["messages"][-1]["content"])
        role = authorized["role"]
        items = authorized["authorized_inputs"]
        output = self._output(role, items)
        ordinal = len(self.calls)
        return ProviderHTTPResponse(
            status_code=200,
            headers={"x-tt-logid": f"ark-world-{ordinal}"},
            body=json.dumps(
                {
                    "id": f"chatcmpl-world-{ordinal}",
                    "object": "chat.completion",
                    "model": "glm-5.2",
                    "choices": [
                        {
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": json.dumps(output),
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
            ).encode("utf-8"),
        )

    def _output(self, role, items):
        by_kind = {}
        for item in items:
            by_kind.setdefault(item["kind"], []).append(item["payload"])
        if role == "INVESTIGATION_PLANNER":
            observations = by_kind["SOURCE_OBSERVATION"][0]
            if self.stop_immediately:
                return _planner("STOP")
            if len(observations) == 0:
                return _planner("RESOLVE")
            if len(observations) == 1:
                return _planner("COMPARE")
            if len(observations) == 2:
                return _planner("READ")
            return _planner("STOP")
        if role == "FACT_PROPOSER":
            observation = by_kind["SOURCE_OBSERVATION"][0]
            entity_snapshot = by_kind["FORMAL_KNOWLEDGE"][0]
            scoped_need = by_kind["REQUIREMENT"][0]["needs"][0]
            need_id = scoped_need["need_id"]
            if need_id != "JWT-N01":
                return {
                    "proposals": [],
                    "limitations": ["fixture provides no formal support for this Need"],
                }
            if observation["tool"] == "RESOLVE":
                semantic_key = f"fact:resolve:{need_id.lower()}"
                obligation_id = "JWT-N01-O01"
                statement = (
                    f"the exact target is {TARGET_COMMIT} and its unique parent is "
                    f"{PARENT_COMMIT}"
                )
            else:
                semantic_key = f"fact:compare:{need_id.lower()}"
                obligation_id = scoped_need["obligations"][1]["obligation_id"]
                statement = (
                    "the complete changed-file set is pom.xml, mall-security/pom.xml, "
                    "and mall-security/src/main/java/com/macro/mall/security/util/JwtTokenUtil.java"
                )
            return {
                "proposals": [
                    {
                        "semantic_key": semantic_key,
                        "statement": statement,
                        "target": TARGET_COMMIT,
                        "context": "PARENT_TO_TARGET",
                        "modality": "ESTABLISHED",
                        "condition": None,
                        "limitation": None,
                        "entity_refs": [entity_snapshot["members"][0]["formal_ref"]],
                        "source_observation_refs": [observation["observation_ref"]],
                        "need_ids": [need_id],
                        "obligation_ids": [obligation_id],
                    }
                ],
                "limitations": [],
            }
        if role == "KNOWLEDGE_REVIEWER":
            proposals = by_kind["KNOWLEDGE_PROPOSAL"][0]
            return {
                "decision": "ACCEPT" if proposals else "REJECT",
                "accepted_semantic_keys": [item["semantic_key"] for item in proposals],
                "findings": [],
            }
        if role == "INFERENCE_PROPOSER":
            return {"proposals": [], "limitations": ["no additional inference required"]}
        if role == "SUFFICIENCY_REVIEWER":
            requirement = by_kind["REQUIREMENT"][0]
            snapshot = by_kind["FORMAL_KNOWLEDGE"][0]
            formal_members = snapshot["members"]
            obligations = []
            for need in requirement["needs"]:
                for obligation in need["obligations"]:
                    obligation_id = obligation["obligation_id"]
                    supporting = [
                        member["formal_ref"]
                        for member in formal_members
                        if obligation_id in member.get("obligation_ids", [])
                    ]
                    obligations.append(
                        {
                            "obligation_id": obligation_id,
                            "status": "SATISFIED" if supporting else "GAP",
                            "supporting_refs": supporting,
                            "finding": "formal support present" if supporting else "formal support absent",
                        }
                    )
            joint_support = [member["formal_ref"] for member in formal_members]
            joints = [
                {
                    "constraint_id": item["constraint_id"],
                    "status": "SATISFIED" if joint_support else "GAP",
                    "supporting_refs": joint_support,
                    "finding": (
                        "all published members share the frozen boundary"
                        if joint_support
                        else "formal support absent"
                    ),
                }
                for item in requirement["joint_constraints"]
            ]
            all_satisfied = all(
                item["status"] == "SATISFIED" for item in obligations + joints
            )
            return {
                "obligations": obligations,
                "joint_constraints": joints,
                "overall": "SATISFIED" if all_satisfied else "INSUFFICIENT",
            }
        if role == "ANSWER_GENERATOR":
            assessment = by_kind["ASSESSMENT"][0]
            claims = []
            for item in assessment["obligations"]:
                obligation_id = item["obligation_id"]
                need_id = obligation_id.rsplit("-O", 1)[0]
                formal = item["status"] == "SATISFIED"
                if obligation_id == "JWT-N01-O01":
                    claim_text = (
                        f"the exact target is {TARGET_COMMIT} and its unique parent is "
                        f"{PARENT_COMMIT}"
                    )
                elif obligation_id == "JWT-N01-O02":
                    claim_text = (
                        "the complete changed-file set is pom.xml, mall-security/pom.xml, "
                        "and mall-security/src/main/java/com/macro/mall/security/util/JwtTokenUtil.java"
                    )
                else:
                    claim_text = (
                        f"{obligation_id} has formal support."
                        if formal
                        else f"{obligation_id} remains a knowledge gap."
                    )
                claims.append(
                    {
                        "semantic_key": f"answer:{obligation_id.lower()}",
                        "text": claim_text,
                        "kind": "FORMAL_KNOWLEDGE" if formal else "KNOWLEDGE_GAP",
                        "target": TARGET_COMMIT,
                        "context": "PARENT_TO_TARGET",
                        "modality": "ESTABLISHED" if formal else "UNKNOWN",
                        "coverage": "DIRECT" if formal else "GAP_DISCLOSURE",
                        "condition": None,
                        "limitation": None if formal else item["finding"],
                        "supporting_refs": item["supporting_refs"],
                        "need_ids": [need_id],
                        "obligation_ids": [obligation_id],
                    }
                )
            return {
                "claims": claims,
                "answer": "\n".join(item["text"] for item in claims),
                "gaps": [
                    item["obligation_id"]
                    for item in assessment["obligations"]
                    if item["status"] != "SATISFIED"
                ],
            }
        if role == "ANSWER_REVIEWER":
            candidate = by_kind["ANSWER_CANDIDATE"][0]
            return {
                "decision": "APPROVED",
                "claim_findings": [
                    {
                        "semantic_key": item["semantic_key"],
                        "outcome": "PASS",
                        "finding": None,
                    }
                    for item in candidate["claims"]
                ],
                "missing_obligation_ids": [],
            }
        raise AssertionError(f"unexpected role: {role}")


class RecoveringPlannerTransport(WorldModelTransport):
    def __init__(self):
        super().__init__()
        self.planner_calls = 0

    def _output(self, role, items):
        if role != "INVESTIGATION_PLANNER":
            return super()._output(role, items)
        self.planner_calls += 1
        if self.planner_calls == 1:
            invalid = _planner("RESOLVE")
            invalid["revision_role"] = "TARGET"
            return invalid
        if self.planner_calls == 2:
            return _planner("RESOLVE")
        if self.planner_calls == 3:
            return _planner("COMPARE")
        if self.planner_calls == 4:
            return _planner("READ")
        return _planner("STOP")


class RecoveringStructuredOutputTransport(WorldModelTransport):
    def __init__(self):
        super().__init__()
        self.invalid_output_sent = False

    def _output(self, role, items):
        output = super()._output(role, items)
        if role == "KNOWLEDGE_REVIEWER" and not self.invalid_output_sent:
            self.invalid_output_sent = True
            return {**output, "unexpected_field": True}
        return output


class RecoveringSemanticOutputTransport(WorldModelTransport):
    def __init__(self):
        super().__init__()
        self.invalid_assessment_sent = False

    def _output(self, role, items):
        output = super()._output(role, items)
        if role == "SUFFICIENCY_REVIEWER" and not self.invalid_assessment_sent:
            self.invalid_assessment_sent = True
            output["obligations"][0]["status"] = "GAP"
            return output
        return output


class ComparisonTransport:
    def __init__(self):
        self.calls = []

    def post_json(self, **arguments):
        self.calls.append(arguments)
        wire = json.loads(arguments["body"])
        evaluator_input = json.loads(wire["messages"][-1]["content"])
        findings = [
            {
                "semantic_key": item["semantic_key"],
                "outcome": "EQUIVALENT",
                "target_preserved": True,
                "context_preserved": True,
                "modality_preserved": True,
                "condition_preserved": True,
                "limitation_preserved": True,
                "coverage_preserved": True,
                "factual_error": False,
                "finding": "the frozen typed claim fields and meaning are preserved",
            }
            for item in evaluator_input["common_claims"]
        ]
        output = {
            "claim_findings": findings,
            "direct_score": 10,
            "world_model_score": 10,
            "score_rationale": "all material claims and explicit gaps are preserved",
        }
        return ProviderHTTPResponse(
            status_code=200,
            headers={"x-tt-logid": "ark-comparison-1"},
            body=json.dumps(
                {
                    "id": "chatcmpl-comparison-1",
                    "object": "chat.completion",
                    "model": "glm-5.2",
                    "choices": [
                        {
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": json.dumps(output),
                            },
                            "finish_reason": "stop",
                        }
                    ],
                    "usage": {
                        "prompt_tokens": 30,
                        "completion_tokens": 15,
                        "total_tokens": 45,
                    },
                }
            ).encode("utf-8"),
        )


def _planner(action):
    step = {
        "action": action,
        "revision_role": "NONE",
        "path": "",
        "query": "",
        "start_line": 0,
        "end_line": 0,
        "rationale": "resolve and compare before closing source collection",
        "stop_reason": "minimum frozen boundary is covered" if action == "STOP" else "",
    }
    if action == "READ":
        step.update(
            {
                "revision_role": "TARGET",
                "path": "mall-security/src/main/java/com/macro/mall/security/util/JwtTokenUtil.java",
                "start_line": 150,
                "end_line": 203,
            }
        )
    return step


class JwtWorldModelTests(unittest.TestCase):
    def setUp(self):
        self.configuration = VolcengineArkModelConfiguration()
        self.qualification = ArkChatConformanceQualification(
            result_ref="CC-ARK-CHAT-NO-TOOLS-001:sha256:" + "a" * 64,
            result_digest=Digest("sha256:" + "a" * 64),
            qualified_model_fingerprints=self.configuration.qualified_model_identities,
            adapter_version=self.configuration.adapter_version,
            provider_configuration_fingerprint=self.configuration.fingerprint,
            valid_until=datetime(2099, 1, 1, tzinfo=timezone.utc),
        )
        self.repository = (
            Path(__file__).resolve().parents[1] / "validation-projects" / "mall"
        )

    def test_ambiguous_created_requirement_rejects_related_token_creation_text(self):
        self.assertFalse(
            _frozen_text_covers_obligations(
                {
                    "statement": "JWTUtil.createToken creates a token with a byte-array key",
                    "limitation": None,
                },
                ["JWT-N05-O01"],
            )
        )

    def test_frozen_guards_preserve_parse_order_and_comment_modality(self):
        self.assertFalse(
            _frozen_text_covers_obligations(
                {
                    "statement": "The migration affects Maven dependencies and JwtTokenUtil.java",
                    "limitation": None,
                },
                ["JWT-N01-O02"],
            )
        )
        self.assertTrue(
            _frozen_text_covers_obligations(
                {
                    "statement": "The complete set is pom.xml, mall-security/pom.xml, and mall-security/src/main/java/com/macro/mall/security/util/JwtTokenUtil.java",
                    "limitation": None,
                },
                ["JWT-N01-O02"],
            )
        )
        self.assertFalse(
            _frozen_text_covers_obligations(
                {
                    "statement": "verify is checked before parse",
                    "limitation": None,
                },
                ["JWT-N04-O01"],
            )
        )
        self.assertTrue(
            _frozen_text_covers_obligations(
                {
                    "statement": "verify=false returns null before parse; verify=true attempts parsing and an exception is caught and returns null",
                    "limitation": None,
                },
                ["JWT-N04-O01"],
            )
        )
        self.assertFalse(
            _frozen_text_covers_obligations(
                {
                    "statement": "verify=false returns null; when verify=true an exception during verify or parsing is caught and returns null; exact invalid mapping is unproven",
                    "limitation": None,
                },
                ["JWT-N04-O02"],
            )
        )
        self.assertFalse(
            _frozen_text_covers_obligations(
                {
                    "statement": "String-key semantics and comment modality are unknown",
                    "limitation": None,
                },
                ["JWT-N06-O02"],
            )
        )
        self.assertTrue(
            _frozen_text_covers_obligations(
                {
                    "statement": "String-key semantics are unknown; HMACSHA512 is preserved only as comment-modality evidence",
                    "limitation": None,
                },
                ["JWT-N06-O02"],
            )
        )
        self.assertFalse(
            _frozen_text_covers_obligations(
                {
                    "statement": "JWTUtil.createToken algorithm is unknown and HMACSHA512 is only an old comment",
                    "limitation": None,
                },
                ["JWT-N06-O01"],
            )
        )
        self.assertTrue(
            _frozen_text_covers_obligations(
                {
                    "statement": "The old signWith(SignatureAlgorithm.HS512, secret) code and HMACSHA512 comment do not prove the unknown JWTUtil.createToken algorithm",
                    "limitation": None,
                },
                ["JWT-N06-O01"],
            )
        )
        self.assertFalse(
            _frozen_text_covers_obligations(
                {
                    "statement": "Payload serialization and parsed Java type equivalence to Claims are unknown; getPayloads returns Map<String,Object>",
                    "limitation": None,
                },
                ["JWT-N06-O03"],
            )
        )
        self.assertTrue(
            _frozen_text_covers_obligations(
                {
                    "statement": "getPayloads visibly returns Map<String,Object>, but concrete runtime payload value types and serialization are unknown",
                    "limitation": None,
                },
                ["JWT-N06-O03"],
            )
        )
        self.assertTrue(
            _frozen_text_covers_obligations(
                {
                    "statement": "created accepts Long and Date representations",
                    "limitation": None,
                },
                ["JWT-N05-O01"],
            )
        )
        self.assertTrue(
            _frozen_text_covers_obligations(
                {
                    "statement": "any other created type leaves createdDate null and returns false",
                    "limitation": None,
                },
                ["JWT-N05-O02"],
            )
        )

    def test_seven_role_run_closes_source_and_seals_reviewed_partial_answer(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runtime = root / "runtime"
            run_configuration_path = self._freeze(root, runtime)
            transport = WorldModelTransport()
            result_path = run_world_model(
                run_configuration_path=run_configuration_path,
                repository_path=self.repository,
                runtime_directory=runtime,
                result_directory=runtime / "results",
                qualification=self.qualification,
                configuration=self.configuration,
                transport=transport,
                now=datetime(2026, 8, 6, 2, tzinfo=timezone.utc),
            )
            result = json.loads(result_path.read_text(encoding="utf-8"))
            run_configuration = json.loads(run_configuration_path.read_text(encoding="utf-8"))
            verify_world_model_result(
                result, run_configuration, self.qualification, self.configuration
            )
            self.assertEqual(result_path.stat().st_mode & 0o777, 0o600)
            self.assertEqual(set(result["roles_executed"]), {
                "INVESTIGATION_PLANNER",
                "FACT_PROPOSER",
                "KNOWLEDGE_REVIEWER",
                "INFERENCE_PROPOSER",
                "SUFFICIENCY_REVIEWER",
                "ANSWER_GENERATOR",
                "ANSWER_REVIEWER",
            })
            self.assertTrue(all(value >= 1 for value in result["roles_executed"].values()))
            self.assertEqual([item["kind"] for item in result["snapshots"]], ["ENTITY", "FACT", "INFERENCE"])
            self.assertEqual(result["delivery"]["state"], "DELIVERED")
            self.assertEqual(result["assessment"]["overall"], "INSUFFICIENT")
            self.assertNotIn("oracle-only-answer", result_path.read_text(encoding="utf-8"))
            for recorded_call in transport.calls:
                wire = json.loads(recorded_call["body"])
                system_prompt = wire["messages"][0]["content"]
                self.assertIn("Return exactly one JSON object", system_prompt)
                self.assertIn("Do not emit Markdown fences", system_prompt)
            source_closed = {
                "INFERENCE_PROPOSER",
                "SUFFICIENCY_REVIEWER",
                "ANSWER_GENERATOR",
                "ANSWER_REVIEWER",
            }
            for call in result["model_calls"]:
                kinds = {item["kind"] for item in call["authorized_inputs"]}
                if call["role"] in {"FACT_PROPOSER", "KNOWLEDGE_REVIEWER"}:
                    self.assertIn("REQUIREMENT", kinds)
                wire = json.loads(transport.calls[call["ordinal"]]["body"])
                expected_max_tokens = (
                    8192
                    if call["role"]
                    in {
                        "FACT_PROPOSER",
                        "INFERENCE_PROPOSER",
                        "SUFFICIENCY_REVIEWER",
                        "ANSWER_GENERATOR",
                        "ANSWER_REVIEWER",
                    }
                    else 4096
                )
                self.assertEqual(wire["max_tokens"], expected_max_tokens)
                if call["role"] in source_closed:
                    self.assertFalse({"SOURCE_OBSERVATION", "BUILD_TARGET"} & kinds)

            result["candidate"]["answer"] = "tampered"
            with self.assertRaises(DomainError) as raised:
                verify_world_model_result(
                    result, run_configuration, self.qualification, self.configuration
                )
            self.assertEqual(raised.exception.code, ErrorCode.QUALIFICATION_INVALID)

    def test_planner_that_never_recovers_from_early_stop_exhausts_budget(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runtime = root / "runtime"
            run_configuration_path = self._freeze(root, runtime)
            with self.assertRaises(DomainError) as raised:
                run_world_model(
                    run_configuration_path=run_configuration_path,
                    repository_path=self.repository,
                    runtime_directory=runtime,
                    result_directory=runtime / "results",
                    qualification=self.qualification,
                    configuration=self.configuration,
                    transport=WorldModelTransport(stop_immediately=True),
                )
            self.assertEqual(raised.exception.code, ErrorCode.BUDGET_EXHAUSTED)
            self.assertFalse((runtime / "results").exists())

    def test_invalid_planner_action_is_denied_and_retried_within_budget(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runtime = root / "runtime"
            run_configuration_path = self._freeze(root, runtime)
            result_path = run_world_model(
                run_configuration_path=run_configuration_path,
                repository_path=self.repository,
                runtime_directory=runtime,
                result_directory=runtime / "results",
                qualification=self.qualification,
                configuration=self.configuration,
                transport=RecoveringPlannerTransport(),
                now=datetime(2026, 8, 6, 2, tzinfo=timezone.utc),
            )
            result = json.loads(result_path.read_text(encoding="utf-8"))
            self.assertEqual(
                [item["tool"] for item in result["source_trace"]],
                ["DENIED", "RESOLVE", "COMPARE", "READ"],
            )
            self.assertEqual(result["observations"][0]["tool"], "DENIED")
            self.assertIn('"outcome":"DENIED"', result["observations"][0]["content"])
            self.assertEqual(result["roles_executed"]["FACT_PROPOSER"], 5)

    def test_closed_schema_violation_is_safely_recorded_and_retried(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runtime = root / "runtime"
            run_configuration_path = self._freeze(root, runtime)
            transport = RecoveringStructuredOutputTransport()
            result_path = run_world_model(
                run_configuration_path=run_configuration_path,
                repository_path=self.repository,
                runtime_directory=runtime,
                result_directory=runtime / "results",
                qualification=self.qualification,
                configuration=self.configuration,
                transport=transport,
                now=datetime(2026, 8, 6, 2, tzinfo=timezone.utc),
            )
            result = json.loads(result_path.read_text(encoding="utf-8"))
            self.assertEqual(len(result["failed_model_calls"]), 1)
            failed = result["failed_model_calls"][0]
            self.assertEqual(failed["role"], "KNOWLEDGE_REVIEWER")
            self.assertEqual(failed["outcome"], "DENIED_INVALID_OUTPUT")
            self.assertNotIn("structured_output", failed)
            self.assertEqual(
                result["budget_usage"]["model_calls"],
                len(result["model_calls"]) + 1,
            )
            retry_wire = json.loads(transport.calls[failed["attempt_ordinal"] + 1]["body"])
            retry_input = json.loads(retry_wire["messages"][-1]["content"])
            self.assertEqual(len(retry_input["structured_output_recovery_feedback"]), 1)

    def test_semantic_binding_violation_is_safely_recorded_and_retried(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runtime = root / "runtime"
            run_configuration_path = self._freeze(root, runtime)
            transport = RecoveringSemanticOutputTransport()
            result_path = run_world_model(
                run_configuration_path=run_configuration_path,
                repository_path=self.repository,
                runtime_directory=runtime,
                result_directory=runtime / "results",
                qualification=self.qualification,
                configuration=self.configuration,
                transport=transport,
                now=datetime(2026, 8, 6, 2, tzinfo=timezone.utc),
            )
            result = json.loads(result_path.read_text(encoding="utf-8"))
            self.assertEqual(len(result["failed_model_calls"]), 1)
            failed = result["failed_model_calls"][0]
            self.assertEqual(failed["role"], "SUFFICIENCY_REVIEWER")
            self.assertEqual(
                failed["error_details"]["semantic_error"],
                "NON_SATISFIED_WITH_SUPPORT",
            )
            self.assertNotIn("structured_output", failed)

    def test_post_delivery_comparison_passes_with_exact_obligation_conservation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runtime = root / "runtime"
            run_configuration_path = self._freeze(root, runtime)
            oracle_path = next((root / "oracle").glob("JWT-DIRECT-ORACLE-*.json"))
            world_result_path = run_world_model(
                run_configuration_path=run_configuration_path,
                repository_path=self.repository,
                runtime_directory=runtime,
                result_directory=runtime / "results",
                qualification=self.qualification,
                configuration=self.configuration,
                transport=WorldModelTransport(),
                now=datetime(2026, 8, 6, 2, tzinfo=timezone.utc),
            )
            oracle = json.loads(oracle_path.read_text(encoding="utf-8"))
            world = json.loads(world_result_path.read_text(encoding="utf-8"))
            run_configuration = json.loads(run_configuration_path.read_text(encoding="utf-8"))
            review_path = root / "codex-review.json"
            review_path.write_text(
                json.dumps(
                    self._review_attestation(oracle, world, run_configuration)
                ),
                encoding="utf-8",
            )
            comparison_path = seal_reviewed_capability_comparison(
                oracle_path=oracle_path,
                run_configuration_path=run_configuration_path,
                world_model_result_path=world_result_path,
                review_attestation_path=review_path,
                result_directory=root / "comparison",
                qualification=self.qualification,
                configuration=self.configuration,
                now=datetime(2026, 8, 6, 3, tzinfo=timezone.utc),
            )
            comparison = json.loads(comparison_path.read_text(encoding="utf-8"))
            verify_capability_comparison(comparison, oracle, world, run_configuration)
            malformed = json.loads(json.dumps(comparison))
            malformed["generator_models"]["direct"] = []
            malformed["comparison_digest"] = digest_of(
                {
                    key: value
                    for key, value in malformed.items()
                    if key != "comparison_digest"
                }
            ).value
            with self.assertRaises(DomainError) as raised:
                verify_capability_comparison(
                    malformed, oracle, world, run_configuration
                )
            self.assertEqual(raised.exception.code, ErrorCode.QUALIFICATION_INVALID)
            self.assertEqual(comparison["conclusion"], "PASS")
            self.assertEqual(comparison["missing_direct_obligation_ids"], [])
            self.assertEqual(comparison["missing_world_obligation_ids"], [])
            self.assertTrue(
                comparison["independence"]["independent_from_direct_generator"]
            )
            self.assertTrue(
                comparison["independence"]["independent_from_world_generator"]
            )
            self.assertEqual(comparison_path.stat().st_mode & 0o777, 0o600)

            registration_path = register_capability_evaluation(
                oracle_path=oracle_path,
                run_configuration_path=run_configuration_path,
                world_model_result_path=world_result_path,
                comparison_path=comparison_path,
                database_path=root / "evaluation" / "authority.sqlite3",
                result_directory=root / "evaluation" / "evidence",
                qualification=self.qualification,
                configuration=self.configuration,
                actor="evaluation-authority",
                now=datetime(2026, 8, 6, 4, tzinfo=timezone.utc),
            )
            registration = json.loads(registration_path.read_text(encoding="utf-8"))
            self.assertEqual(registration["conclusion"], "PASS")
            self.assertEqual(registration["validity_status"], "VALID")
            self.assertEqual(
                registration["qualification"]["qualification_kind"],
                "CAPABILITY_EVALUATION",
            )
            self.assertEqual(registration["production_activation"], "NOT_RUN")
            self.assertEqual(registration_path.stat().st_mode & 0o777, 0o600)
            replayed_registration_path = register_capability_evaluation(
                oracle_path=oracle_path,
                run_configuration_path=run_configuration_path,
                world_model_result_path=world_result_path,
                comparison_path=comparison_path,
                database_path=root / "evaluation" / "authority.sqlite3",
                result_directory=root / "evaluation" / "evidence",
                qualification=self.qualification,
                configuration=self.configuration,
                actor="evaluation-authority",
                now=datetime(2026, 8, 6, 4, 30, tzinfo=timezone.utc),
            )
            self.assertEqual(replayed_registration_path, registration_path)
            activation_path = activate_evaluated_strategy(
                registration_path=registration_path,
                run_configuration_path=run_configuration_path,
                database_path=root / "evaluation" / "authority.sqlite3",
                result_directory=root / "evaluation" / "activation",
                activation_scope={"environment": "acceptance"},
                actor="activation-authority",
                reason="verified end-to-end acceptance fixture",
                idempotency_key="activate-jwt-acceptance-fixture",
                now=datetime(2026, 8, 6, 4, 40, tzinfo=timezone.utc),
            )
            activation = json.loads(activation_path.read_text(encoding="utf-8"))
            self.assertEqual(activation["decision_type"], "ACTIVATE")
            self.assertEqual(activation["strategy_id"], "jwt-impact-ark-world-model")
            self.assertEqual(activation["activation_scope"], [["environment", "acceptance"]])
            replayed_activation_path = activate_evaluated_strategy(
                registration_path=registration_path,
                run_configuration_path=run_configuration_path,
                database_path=root / "evaluation" / "authority.sqlite3",
                result_directory=root / "evaluation" / "activation",
                activation_scope={"environment": "acceptance"},
                actor="activation-authority",
                reason="verified end-to-end acceptance fixture",
                idempotency_key="activate-jwt-acceptance-fixture",
                now=datetime(2026, 8, 6, 4, 50, tzinfo=timezone.utc),
            )
            self.assertEqual(replayed_activation_path, activation_path)

            comparison["world_model_score"] = 0
            with self.assertRaises(DomainError) as raised:
                verify_capability_comparison(comparison, oracle, world, run_configuration)
            self.assertEqual(raised.exception.code, ErrorCode.QUALIFICATION_INVALID)

    def test_comparison_rejects_same_model_origin_and_accepts_grouped_direct_claims(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runtime = root / "runtime"
            run_configuration_path = self._freeze(
                root, runtime, grouped_direct_claims=True
            )
            oracle_path = next((root / "oracle").glob("JWT-DIRECT-ORACLE-*.json"))
            world_result_path = run_world_model(
                run_configuration_path=run_configuration_path,
                repository_path=self.repository,
                runtime_directory=runtime,
                result_directory=runtime / "results",
                qualification=self.qualification,
                configuration=self.configuration,
                transport=WorldModelTransport(),
                now=datetime(2026, 8, 6, 2, tzinfo=timezone.utc),
            )
            oracle = json.loads(oracle_path.read_text(encoding="utf-8"))
            world = json.loads(world_result_path.read_text(encoding="utf-8"))
            run_configuration = json.loads(run_configuration_path.read_text(encoding="utf-8"))

            review = self._review_attestation(oracle, world, run_configuration)
            review["reviewer"]["origin"] = "VOLCENGINE_ARK"
            review_path = root / "same-origin-review.json"
            review_path.write_text(json.dumps(review), encoding="utf-8")

            with self.assertRaises(DomainError) as raised:
                seal_reviewed_capability_comparison(
                    oracle_path=oracle_path,
                    run_configuration_path=run_configuration_path,
                    world_model_result_path=world_result_path,
                    review_attestation_path=review_path,
                    result_directory=root / "comparison",
                    qualification=self.qualification,
                    configuration=self.configuration,
                    now=datetime(2026, 8, 6, 3, tzinfo=timezone.utc),
                )
            self.assertEqual(raised.exception.code, ErrorCode.CONTROL_STATE_DENIED)

    def _freeze(self, root, runtime, *, grouped_direct_claims=False):
        draft_path = root / "direct-draft.json"
        draft_path.write_text(
            json.dumps(self._draft(grouped_direct_claims=grouped_direct_claims)),
            encoding="utf-8",
        )
        oracle_path = seal_direct_oracle(
            draft_path=draft_path,
            result_directory=root / "oracle",
            qualification=self.qualification,
            configuration=self.configuration,
            operator="direct-operator",
            reviewer="independent-reviewer",
            now=datetime(2026, 8, 6, tzinfo=timezone.utc),
        )
        return freeze_jwt_run_configuration(
            oracle_path=oracle_path,
            repository_path=self.repository,
            result_directory=root / "run-config",
            qualification=self.qualification,
            configuration=self.configuration,
            operator="world-run-operator",
            runtime_directory=runtime,
            now=datetime(2026, 8, 6, 1, tzinfo=timezone.utc),
        )

    def _draft(self, *, grouped_direct_claims=False):
        requirement = _direct_requirement_view()
        content = "M\tpom.xml"
        content_digest = "sha256:" + hashlib.sha256(content.encode("utf-8")).hexdigest()
        observation_ref = f"direct-observation:000:{content_digest}"
        action = {
            "action": "COMPARE",
            "revision_role": "NONE",
            "path": "",
            "query": "",
            "start_line": 0,
            "end_line": 0,
        }
        claims = []
        answer_lines = []
        for need_id, _, dimensions in _NEEDS:
            for ordinal in range(1, len(dimensions) + 1):
                obligation_id = f"{need_id}-O{ordinal:02d}"
                formal = obligation_id in {"JWT-N01-O01", "JWT-N01-O02"}
                claim_text = (
                    f"{obligation_id} has formal support."
                    if formal
                    else f"{obligation_id} remains a knowledge gap."
                )
                answer_lines.append(claim_text)
                claims.append(
                    {
                        "semantic_key": f"answer:{obligation_id.lower()}",
                        "claim": claim_text,
                        "target": TARGET_COMMIT,
                        "context": "PARENT_TO_TARGET",
                        "modality": "ESTABLISHED" if formal else "UNKNOWN",
                        "condition": None,
                        "limitation": None if formal else "formal support absent",
                        "coverage": "DIRECT" if formal else "GAP_DISCLOSURE",
                        "source_locators": [
                            f"git:compare:{PARENT_COMMIT}..{TARGET_COMMIT}"
                        ],
                        "source_digests": [content_digest],
                        "need_ids": [need_id],
                        "obligation_ids": [obligation_id],
                        "material": True,
                    }
                )
        if grouped_direct_claims:
            grouped = []
            for need_id, _, _ in _NEEDS:
                members = [item for item in claims if item["need_ids"] == [need_id]]
                first = members[0]
                grouped.append(
                    {
                        **first,
                        "semantic_key": f"grouped:{need_id.lower()}",
                        "claim": " ".join(item["claim"] for item in members),
                        "obligation_ids": [
                            obligation_id
                            for item in members
                            for obligation_id in item["obligation_ids"]
                        ],
                    }
                )
            claims = grouped
        return {
            "schema": DIRECT_ORACLE_DRAFT_SCHEMA,
            "question": QUESTION,
            "repository_identity": REPOSITORY_IDENTITY,
            "target_commit": TARGET_COMMIT,
            "parent_commit": PARENT_COMMIT,
            "model_ref": self.configuration.model_ref,
            "adapter_version": self.configuration.adapter_version,
            "conformance_result_ref": self.qualification.result_ref,
            "prompt_ref": DIRECT_AGENT_PROMPT_REF,
            "prompt": DIRECT_AGENT_PROMPT,
            "prompt_digest": digest_of(DIRECT_AGENT_PROMPT).value,
            "tool_policy_ref": DIRECT_AGENT_TOOL_POLICY_REF,
            "requirement": requirement,
            "requirement_digest": digest_of(requirement).value,
            "budget": {
                "max_tool_steps": 40,
                "max_files_read": 16,
                "max_source_bytes": 1_000_000,
                "max_model_calls": 40,
                "timeout_milliseconds": 60_000,
                "max_output_tokens": 4096,
            },
            "started_at": "2026-08-06T00:00:00.000000Z",
            "completed_at": "2026-08-06T00:01:00.000000Z",
            "actual_model_fingerprints": [
                self.configuration.actual_model_fingerprint
            ],
            "provider_request_ids": ["direct-1", "direct-2"],
            "output_normalizations": ["IDENTITY", "IDENTITY"],
            "usage": {"input_tokens": 1, "output_tokens": 1, "complete": True},
            "trace": [
                {
                    "ordinal": 0,
                    "tool": "COMPARE",
                    "request": action,
                    "request_digest": digest_of(action).value,
                    "observation_ref": observation_ref,
                    "result_digest": content_digest,
                }
            ],
            "observations": [
                {
                    "observation_ref": observation_ref,
                    "tool": "COMPARE",
                    "locator": f"git:compare:{PARENT_COMMIT}..{TARGET_COMMIT}",
                    "content": content,
                    "content_digest": content_digest,
                }
            ],
            "direct_answer": "\n".join(answer_lines) + "\noracle-only-answer",
            "claims": claims,
        }

    def _review_attestation(self, oracle, world, run_configuration):
        obligation_ids = sorted(
            obligation["obligation_id"]
            for need in run_configuration["requirement"]["needs"]
            for obligation in need["obligations"]
        )
        return {
            "schema": COMPARISON_REVIEW_ATTESTATION_SCHEMA,
            "reviewer": {
                "identity": "codex-cross-model-evaluator",
                "origin": "OPENAI_CODEX",
                "model_ref": "NOT_EXPOSED_BY_CLIENT",
            },
            "reviewed_at": "2026-08-06T02:30:00.000000Z",
            "method": "SOURCE_RECHECK_AND_CROSS_MODEL_COMPARISON",
            "oracle_ref": oracle["oracle_id"],
            "oracle_digest": oracle["oracle_digest"],
            "world_model_result_ref": world["run_id"],
            "world_model_result_digest": world["result_digest"],
            "run_configuration_ref": run_configuration["run_configuration_id"],
            "run_configuration_digest": run_configuration["configuration_digest"],
            "obligation_findings": [
                {
                    "obligation_id": obligation_id,
                    "outcome": "EQUIVALENT",
                    "meaning_preserved": True,
                    "condition_preserved": True,
                    "limitation_preserved": True,
                    "coverage_preserved": True,
                    "direct_factual_error": False,
                    "world_factual_error": False,
                    "finding": "the obligation meaning and its explicit gap state are preserved",
                }
                for obligation_id in obligation_ids
            ],
            "direct_score": 10,
            "world_model_score": 10,
            "score_rationale": "all registered obligations are preserved without an extra claim",
        }


if __name__ == "__main__":
    unittest.main()
