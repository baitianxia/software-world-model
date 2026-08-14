from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import tempfile
import unittest

from software_world_model.application_services.world_model_answering import (
    WorldModelAuthorityChain,
    WorldModelGapReason,
    WorldModelGapProposal,
    WorldModelQueryPlanProposal,
)
from software_world_model.cross_cutting import (
    DomainError,
    ErrorCode,
    canonical_json_bytes,
    digest_of,
)
from software_world_model.interface.world_model_evaluation import (
    WORLD_MODEL_EVALUATION_PAGE_FORMAT,
    read_world_model_evaluation_page,
    world_model_evaluation_page_envelope,
    world_model_evaluation_page_payload,
    write_world_model_evaluation_page,
)
from tests import test_world_model_answering as answering_fixtures


_IMPLEMENTATION_COMMIT = "a" * 40
_PAGE_DIGEST_DOMAIN = "WORLD_MODEL_EVALUATION_PAGE_PAYLOAD@1"


class _ForbiddenCanonicalChain:
    """Delegate a valid chain while exposing a forbidden future DTO field."""

    def __init__(self, chain: WorldModelAuthorityChain) -> None:
        self._chain = chain

    def __getattr__(self, name: str) -> object:
        return getattr(self._chain, name)

    def require_valid(self) -> None:
        self._chain.require_valid()

    def canonical_value(self) -> dict[str, object]:
        value = self._chain.canonical_value()
        draft = value["draft"]
        assert isinstance(draft, dict)
        claims = draft["claims"]
        assert isinstance(claims, tuple)
        claim = claims[0]
        assert isinstance(claim, dict)
        claim["provider_input"] = {"secret": "must-not-cross"}
        return value


class _ExplicitKnowledgeGapPlanner:
    strategy_ref = "test-world-model-explicit-gap-planner@1"

    def plan(self, *, question, requirement, invocation):
        del question
        return WorldModelQueryPlanProposal(
            requirement_id=requirement.requirement_id,
            requirement_digest=requirement.digest,
            read_set_digest=requirement.read_authority.read_set_digest,
            ordered_bundle_digest=requirement.read_authority.ordered_bundle_digest,
            selectors=(),
            steps=(),
            explicit_gaps=(
                WorldModelGapProposal(
                    need_id=answering_fixtures.INVENTORY_NEED.need_id,
                    reason_code=(
                        WorldModelGapReason.UNSUPPORTED_STRUCTURE_SEMANTICS
                    ),
                    detail="the published Structure profile does not cover this Need",
                ),
            ),
            invocation_id=invocation.invocation_id,
            invocation_digest=invocation.digest,
        )


class WorldModelEvaluationPageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.answering_fixture = answering_fixtures.WorldModelAnsweringTests(
            methodName="runTest"
        )
        self.answering_fixture.setUp()
        self.addCleanup(self.answering_fixture.doCleanups)

    def _chain(self) -> WorldModelAuthorityChain:
        return self.answering_fixture._execute()

    @staticmethod
    def _reason(error: DomainError) -> str | None:
        value = error.details.get("reason_code")
        return value if isinstance(value, str) else None

    @staticmethod
    def _read_page(
        path: Path,
        expected_page_digest: str,
        *,
        expected_implementation_commit: str = _IMPLEMENTATION_COMMIT,
    ) -> dict[str, object]:
        return read_world_model_evaluation_page(
            path,
            expected_implementation_commit=expected_implementation_commit,
            expected_page_digest=expected_page_digest,
        )

    def test_complete_evaluation_only_payload_projects_all_ten_authorities(self):
        chain = self._chain()

        page = world_model_evaluation_page_payload(
            chain, _IMPLEMENTATION_COMMIT
        )

        self.assertIs(page["evaluation_only"], True)
        self.assertEqual(page["environment"], "EVALUATION_ONLY")
        self.assertEqual(page["mode"], "WORLD_MODEL")
        self.assertEqual(page["implementation_commit"], _IMPLEMENTATION_COMMIT)
        expected_authorities = (
            ("QUESTION", chain.question.question_id.value, chain.question.digest.value),
            (
                "REQUIREMENT_REVISION",
                chain.requirement.requirement_id.value,
                chain.requirement.digest.value,
            ),
            (
                "CANDIDATE_RESOLUTION_SET",
                chain.resolutions.resolution_set_id.value,
                chain.resolutions.digest.value,
            ),
            ("QUERY_PLAN", chain.plan.plan_id.value, chain.plan.digest.value),
            (
                "QUERY_RESULT_SET",
                chain.result_set.result_set_id.value,
                chain.result_set.digest.value,
            ),
            (
                "ASSESSMENT",
                chain.assessment.assessment_id.value,
                chain.assessment.digest.value,
            ),
            ("ANSWER_DRAFT", chain.draft.draft_id.value, chain.draft.digest.value),
            ("ANSWER_REVIEW", chain.review.review_id.value, chain.review.digest.value),
            (
                "RESPONSE_AUTHORIZATION",
                chain.authorization.authorization_id.value,
                chain.authorization.digest.value,
            ),
            ("DELIVERY", chain.delivery.delivery_id.value, chain.delivery.digest.value),
        )
        stages = page["authority_chain"]["stages"]
        self.assertEqual(len(stages), 10)
        self.assertEqual(
            tuple(
                (
                    item["stage"],
                    item["authority_id"],
                    item["authority_digest"],
                )
                for item in stages
            ),
            expected_authorities,
        )
        self.assertEqual(
            page["authority_chain"]["chain_digest"], chain.digest.value
        )

        read_binding = page["read_binding"]
        authority = chain.question.read_authority
        self.assertEqual(read_binding["scope_id"], authority.scope_id.value)
        self.assertEqual(read_binding["session_id"], authority.session_id.value)
        self.assertEqual(
            read_binding["session_digest"], authority.session_digest.value
        )
        self.assertEqual(
            read_binding["read_set_digest"], authority.read_set_digest.value
        )
        self.assertEqual(
            read_binding["ordered_bundle_digest"],
            authority.ordered_bundle_digest.value,
        )

        requirements = page["requirements"]
        self.assertEqual(
            [item["need_id"] for item in requirements["needs"]],
            [item.need_id for item in chain.requirement.needs],
        )
        self.assertEqual(requirements["joint_constraints"], [])
        self.assertEqual(
            page["answer"]["claims"][0]["need_id"],
            chain.draft.claims[0].need_id,
        )
        self.assertEqual(
            page["answer"]["claims"][0]["digest"],
            chain.draft.claims[0].digest.value,
        )

        result = chain.result_set.step_results[0].view_result
        view = page["views"]["query_result_views"][0]["view"]
        self.assertEqual(view["result_id"], result.result_id.value)
        self.assertEqual(view["result_digest"], result.digest.value)
        self.assertEqual(view["profile_refs"], list(result.profile_refs))
        self.assertEqual(
            view["relation_modalities"], list(result.relation_modalities)
        )
        self.assertEqual(view["completeness"], result.completeness.value)
        self.assertEqual(len(view["coverage"]), len(result.coverage))
        self.assertEqual(len(view["support"]), len(result.support_map))
        self.assertEqual(
            view["evidence_metadata_ids"],
            [item.value for item in result.evidence_allowlist],
        )

        separation = page["review"]["invocation_separation"]
        self.assertIs(separation["invocations_separate"], True)
        self.assertNotEqual(
            separation["generation"]["invocation_id"],
            separation["review"]["invocation_id"],
        )
        self.assertEqual(page["authorization"]["sink_id"], "EVALUATION_ONLY")
        self.assertEqual(page["delivery"]["sink_id"], "EVALUATION_ONLY")
        self.assertEqual(page["delivery"]["state"], "DELIVERED")
        self.assertEqual(page["execution_boundary"]["provider_call_count"], 0)
        self.assertEqual(page["execution_boundary"]["network_operation_count"], 0)
        self.assertNotIn("investigation_trace", page["query_plan"])

    def test_candidate_ambiguity_projects_application_limitation(self):
        chain = self.answering_fixture._execute(
            query_planner=answering_fixtures.AmbiguousPathQueryPlanner(
                self.answering_fixture.snapshot_b
            )
        )

        page = world_model_evaluation_page_payload(
            chain, _IMPLEMENTATION_COMMIT
        )

        self.assertEqual(page["query_results"]["step_results"], [])
        assessment = page["assessment"]["needs"][0]
        self.assertEqual(assessment["outcome"], "LIMITATION")
        self.assertIsNone(assessment["gap_code"])
        self.assertIn(
            "ENTITY_RESOLUTION_NOT_UNIQUE", assessment["limitations"]
        )
        claim = page["answer"]["claims"][0]
        self.assertEqual(claim["kind"], "APPLICATION_LIMITATION")
        self.assertIn(
            "ENTITY_RESOLUTION_NOT_UNIQUE", claim["limitation_codes"]
        )
        limitation_codes = {item["code"] for item in page["limitations"]}
        self.assertIn("ENTITY_RESOLUTION_NOT_UNIQUE", limitation_codes)
        self.assertTrue(page["views"]["candidate_resolution_views"])
        self.assertTrue(
            any(
                entry["view"]["limitations"]
                for entry in page["views"]["candidate_resolution_views"]
            )
        )

    def test_explicit_plan_gap_projects_as_knowledge_gap(self):
        chain = self.answering_fixture._execute(
            query_planner=_ExplicitKnowledgeGapPlanner()
        )

        page = world_model_evaluation_page_payload(
            chain, _IMPLEMENTATION_COMMIT
        )

        self.assertEqual(page["query_results"]["step_results"], [])
        self.assertEqual(
            page["query_plan"]["explicit_gaps"],
            [
                {
                    "need_id": answering_fixtures.INVENTORY_NEED.need_id,
                    "reason_code": (
                        WorldModelGapReason.UNSUPPORTED_STRUCTURE_SEMANTICS.value
                    ),
                    "detail": (
                        "the published Structure profile does not cover this Need"
                    ),
                }
            ],
        )
        assessment = page["assessment"]["needs"][0]
        self.assertEqual(assessment["outcome"], "KNOWLEDGE_GAP")
        self.assertEqual(
            assessment["gap_code"],
            WorldModelGapReason.UNSUPPORTED_STRUCTURE_SEMANTICS.value,
        )
        self.assertEqual(page["answer"]["claims"][0]["kind"], "KNOWLEDGE_GAP")

    def test_canonical_new_file_round_trip_and_overwrite_rejection(self):
        chain = self._chain()
        expected = world_model_evaluation_page_payload(
            chain, _IMPLEMENTATION_COMMIT
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory).resolve() / "evaluation-page.json"

            page_digest = write_world_model_evaluation_page(
                path, chain, _IMPLEMENTATION_COMMIT
            )

            envelope = json.loads(path.read_bytes())
            self.assertEqual(
                envelope["format_ref"], WORLD_MODEL_EVALUATION_PAGE_FORMAT
            )

            self.assertEqual(
                page_digest,
                digest_of([_PAGE_DIGEST_DOMAIN, expected]),
            )
            encoded = path.read_bytes()
            self.assertEqual(
                encoded,
                canonical_json_bytes(json.loads(encoded.decode("utf-8"))),
            )
            self.assertEqual(
                self._read_page(path, page_digest.value),
                expected,
            )
            before = path.read_bytes()
            with self.assertRaises(DomainError) as raised:
                write_world_model_evaluation_page(
                    path, chain, _IMPLEMENTATION_COMMIT
                )
            self.assertEqual(
                self._reason(raised.exception),
                "WORLD_MODEL_EVALUATION_FILE_UNAVAILABLE",
            )
            self.assertEqual(path.read_bytes(), before)

    def test_reader_rejects_tampered_page_digest(self):
        envelope = world_model_evaluation_page_envelope(
            self._chain(), _IMPLEMENTATION_COMMIT
        )
        page = envelope["page"]
        assert isinstance(page, dict)
        answer = page["answer"]
        assert isinstance(answer, dict)
        trusted_page_digest = envelope["page_digest"]
        assert isinstance(trusted_page_digest, str)
        answer["body"] = "tampered after sealing"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory).resolve() / "tampered.json"
            path.write_bytes(canonical_json_bytes(envelope))

            with self.assertRaises(DomainError) as raised:
                self._read_page(path, trusted_page_digest)

        self.assertEqual(
            raised.exception.code, ErrorCode.AUTHORITY_RECORD_INCONSISTENT
        )
        self.assertEqual(
            self._reason(raised.exception),
            "WORLD_MODEL_EVALUATION_PAGE_DIGEST_MISMATCH",
        )

    def test_reader_rejects_coordinated_body_chain_and_delivery_tamper(self):
        envelope = world_model_evaluation_page_envelope(
            self._chain(), _IMPLEMENTATION_COMMIT
        )
        page = envelope["page"]
        assert isinstance(page, dict)
        answer = page["answer"]
        delivery = page["delivery"]
        authority_chain = page["authority_chain"]
        assert isinstance(answer, dict)
        assert isinstance(delivery, dict)
        assert isinstance(authority_chain, dict)

        answer["body"] = "forged answer accepted by a recomputed outer digest"
        answer["body_digest"] = digest_of(answer["body"]).value
        delivery["body_digest"] = answer["body_digest"]
        authority_chain["chain_digest"] = digest_of(
            "attacker-selected chain"
        ).value
        envelope["page_digest"] = digest_of(
            [_PAGE_DIGEST_DOMAIN, page]
        ).value
        recomputed_page_digest = envelope["page_digest"]
        assert isinstance(recomputed_page_digest, str)

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory).resolve() / "coordinated-tamper.json"
            path.write_bytes(canonical_json_bytes(envelope))
            with self.assertRaises(DomainError) as raised:
                self._read_page(path, recomputed_page_digest)

        self.assertEqual(
            raised.exception.code, ErrorCode.AUTHORITY_RECORD_INCONSISTENT
        )
        self.assertEqual(
            self._reason(raised.exception),
            "WORLD_MODEL_EVALUATION_AUTHORITY_RECORD_MISMATCH",
        )

    def test_reader_rejects_forged_implementation_commit_against_anchor(self):
        envelope = world_model_evaluation_page_envelope(
            self._chain(), _IMPLEMENTATION_COMMIT
        )
        page = envelope["page"]
        assert isinstance(page, dict)
        page["implementation_commit"] = "b" * 40
        envelope["page_digest"] = digest_of(
            [_PAGE_DIGEST_DOMAIN, page]
        ).value
        recomputed_page_digest = envelope["page_digest"]
        assert isinstance(recomputed_page_digest, str)

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory).resolve() / "forged-commit.json"
            path.write_bytes(canonical_json_bytes(envelope))
            with self.assertRaises(DomainError) as raised:
                self._read_page(
                    path,
                    expected_implementation_commit=_IMPLEMENTATION_COMMIT,
                    expected_page_digest=recomputed_page_digest,
                )

        self.assertEqual(
            raised.exception.code, ErrorCode.AUTHORITY_RECORD_INCONSISTENT
        )
        self.assertEqual(
            self._reason(raised.exception),
            "WORLD_MODEL_EVALUATION_IMPLEMENTATION_COMMIT_MISMATCH",
        )

    def test_reader_rejects_fully_recomputed_page_against_trusted_digest(self):
        trusted = world_model_evaluation_page_envelope(
            self._chain(), _IMPLEMENTATION_COMMIT
        )
        forged_fixture = answering_fixtures.WorldModelAnsweringTests(
            methodName="runTest"
        )
        forged_fixture.setUp()
        self.addCleanup(forged_fixture.doCleanups)
        forged = world_model_evaluation_page_envelope(
            forged_fixture._execute(
                query_planner=answering_fixtures.AmbiguousPathQueryPlanner(
                    forged_fixture.snapshot_b
                )
            ),
            _IMPLEMENTATION_COMMIT,
        )
        trusted_digest = trusted["page_digest"]
        forged_digest = forged["page_digest"]
        assert isinstance(trusted_digest, str)
        assert isinstance(forged_digest, str)
        self.assertNotEqual(forged_digest, trusted_digest)

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory).resolve() / "fully-recomputed-forgery.json"
            path.write_bytes(canonical_json_bytes(forged))
            with self.assertRaises(DomainError) as raised:
                self._read_page(path, trusted_digest)

        self.assertEqual(
            self._reason(raised.exception),
            "WORLD_MODEL_EVALUATION_EXPECTED_PAGE_DIGEST_MISMATCH",
        )

    def test_projection_and_reader_reject_boolean_operation_counters(self):
        chain = self._chain()
        forged_chain = replace(chain, provider_call_count=False)
        chain_core = forged_chain.canonical_value()
        chain_core.pop("digest")
        forged_chain = replace(
            forged_chain,
            digest=digest_of(["WORLD_MODEL_AUTHORITY_CHAIN@1", chain_core]),
        )
        with self.assertRaises(DomainError) as projection_error:
            world_model_evaluation_page_payload(
                forged_chain, _IMPLEMENTATION_COMMIT
            )
        self.assertEqual(
            self._reason(projection_error.exception),
            "WORLD_MODEL_CHAIN_EXECUTION_BOUNDARY_INVALID",
        )

        envelope = world_model_evaluation_page_envelope(
            chain, _IMPLEMENTATION_COMMIT
        )
        page = envelope["page"]
        assert isinstance(page, dict)
        boundary = page["execution_boundary"]
        authority_chain = page["authority_chain"]
        assert isinstance(boundary, dict)
        assert isinstance(authority_chain, dict)
        boundary["provider_call_count"] = False
        forged_core = chain.canonical_value()
        forged_core.pop("digest")
        forged_core["provider_call_count"] = False
        authority_chain["chain_digest"] = digest_of(
            ["WORLD_MODEL_AUTHORITY_CHAIN@1", forged_core]
        ).value
        envelope["page_digest"] = digest_of(
            [_PAGE_DIGEST_DOMAIN, page]
        ).value
        recomputed_page_digest = envelope["page_digest"]
        assert isinstance(recomputed_page_digest, str)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory).resolve() / "boolean-counter.json"
            path.write_bytes(canonical_json_bytes(envelope))
            with self.assertRaises(DomainError) as reader_error:
                self._read_page(path, recomputed_page_digest)
        self.assertEqual(
            self._reason(reader_error.exception),
            "WORLD_MODEL_EVALUATION_EXECUTION_BOUNDARY_INVALID",
        )

    def test_reader_rejects_recomputed_omitted_limitations(self):
        chain = self.answering_fixture._execute(
            query_planner=answering_fixtures.AmbiguousPathQueryPlanner(
                self.answering_fixture.snapshot_b
            )
        )
        envelope = world_model_evaluation_page_envelope(
            chain, _IMPLEMENTATION_COMMIT
        )
        page = envelope["page"]
        assert isinstance(page, dict)
        self.assertTrue(page["limitations"])
        page["limitations"] = []
        envelope["page_digest"] = digest_of(
            [_PAGE_DIGEST_DOMAIN, page]
        ).value
        recomputed_page_digest = envelope["page_digest"]
        assert isinstance(recomputed_page_digest, str)

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory).resolve() / "omitted-limitations.json"
            path.write_bytes(canonical_json_bytes(envelope))
            with self.assertRaises(DomainError) as raised:
                self._read_page(path, recomputed_page_digest)

        self.assertEqual(
            self._reason(raised.exception),
            "WORLD_MODEL_EVALUATION_AUTHORITY_RECORD_MISMATCH",
        )

    def test_reader_rejects_duplicate_keys_and_noncanonical_json(self):
        envelope = world_model_evaluation_page_envelope(
            self._chain(), _IMPLEMENTATION_COMMIT
        )
        trusted_page_digest = envelope["page_digest"]
        assert isinstance(trusted_page_digest, str)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            duplicate = root / "duplicate.json"
            duplicate.write_bytes(b'{"format_ref":1,"format_ref":2}')
            with self.assertRaises(DomainError) as duplicate_error:
                self._read_page(duplicate, trusted_page_digest)
            self.assertEqual(
                self._reason(duplicate_error.exception),
                "WORLD_MODEL_EVALUATION_JSON_INVALID",
            )

            noncanonical = root / "noncanonical.json"
            noncanonical.write_text(
                json.dumps(envelope, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            with self.assertRaises(DomainError) as noncanonical_error:
                self._read_page(noncanonical, trusted_page_digest)
            self.assertEqual(
                self._reason(noncanonical_error.exception),
                "WORLD_MODEL_EVALUATION_JSON_NONCANONICAL",
            )

    def test_forbidden_nested_payload_key_is_rejected_before_projection(self):
        chain = _ForbiddenCanonicalChain(self._chain())

        with self.assertRaises(DomainError) as raised:
            world_model_evaluation_page_payload(chain, _IMPLEMENTATION_COMMIT)

        self.assertEqual(raised.exception.code, ErrorCode.CONTROL_STATE_DENIED)
        self.assertEqual(
            self._reason(raised.exception),
            "WORLD_MODEL_EVALUATION_FORBIDDEN_PAYLOAD_KEY",
        )
        self.assertEqual(raised.exception.details.get("field"), "provider_input")

    def test_reader_rejects_forbidden_key_even_with_recomputed_page_digest(self):
        envelope = world_model_evaluation_page_envelope(
            self._chain(), _IMPLEMENTATION_COMMIT
        )
        page = envelope["page"]
        assert isinstance(page, dict)
        views = page["views"]
        assert isinstance(views, dict)
        query_views = views["query_result_views"]
        assert isinstance(query_views, list)
        view = query_views[0]["view"]
        assert isinstance(view, dict)
        result_payload = view["result_payload"]
        assert isinstance(result_payload, dict)
        result_payload["excerpt"] = "forbidden observation payload"
        envelope["page_digest"] = digest_of(
            [_PAGE_DIGEST_DOMAIN, page]
        ).value
        recomputed_page_digest = envelope["page_digest"]
        assert isinstance(recomputed_page_digest, str)

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory).resolve() / "forbidden.json"
            path.write_bytes(canonical_json_bytes(envelope))
            with self.assertRaises(DomainError) as raised:
                self._read_page(path, recomputed_page_digest)

        self.assertEqual(raised.exception.code, ErrorCode.CONTROL_STATE_DENIED)
        self.assertEqual(
            self._reason(raised.exception),
            "WORLD_MODEL_EVALUATION_FORBIDDEN_PAYLOAD_KEY",
        )
        self.assertEqual(raised.exception.details.get("field"), "excerpt")


if __name__ == "__main__":
    unittest.main()
