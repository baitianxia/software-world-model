from __future__ import annotations

from dataclasses import replace
from unittest import TestCase

from software_world_model.application_services.bounded_world_model_investigation import (
    BoundedWorldModelInvestigationSession,
    InvestigationCompleteness,
    InvestigationCompletenessVerdict,
    InvestigationProposal,
    InvestigationTerminalStatus,
    compile_investigation_intent,
    constrained_investigation_operations,
    normalize_investigation_evidence_requests,
    validate_bounded_investigation_trace,
)
from software_world_model.application_services.structure_read_bundle import (
    JAVA_IMPLEMENTATION_FEATURE_DISCOVERY_CONTRACT_REF,
    StructureBusinessDiscoveryRecallBinding,
    StructureBusinessDiscoveryRecallVerdict,
    StructureOrderedReadBundle,
)
from software_world_model.application_services.structure_view import (
    StructureViewService,
)
from software_world_model.knowledge_engine.structure import (
    JAVA_SOURCE_SEMANTICS_PROFILE_REF,
)
from software_world_model.cross_cutting import DomainError, digest_of

from tests import test_java_source_semantics as _java_semantics_tests


def _proposal(
    session: BoundedWorldModelInvestigationSession,
    operation: str,
    **changes: object,
) -> InvestigationProposal:
    evidence_requests = changes.pop("evidence_requests", None)
    if evidence_requests is None:
        evidence_requests = (
            [
                item.canonical_value()
                for item in session.steps[0].proposal.evidence_requests
            ]
            if session.steps
            else [
                {
                    "operation": "method_implementations",
                    "relation_intent": None,
                }
            ]
        )
    value: dict[str, object] = {
        "step_index": session.model_call_count + 1,
        "trace_digest": session.trace_digest.value,
        "operation": operation,
        "snapshot_id": None,
        "search_terms": [],
        "limit": None,
        "candidate_result_id": None,
        "candidate_result_digest": None,
        "method_refs": [],
        "entity_refs": [],
        "direction": None,
        "predicate": None,
        "max_depth": None,
        "max_paths": None,
        "max_expansions": None,
        "finish_reason": None,
        "evidence_requests": evidence_requests,
    }
    value.update(changes)
    return InvestigationProposal.from_mapping(
        value,
        model_proposal_digest=digest_of(
            {"fixture-proposal": value["step_index"], "operation": operation}
        ),
    )


def _ref(result: object, entity: object) -> dict[str, str]:
    return {
        "source_result_id": result.result_id.value,
        "source_result_digest": result.digest.value,
        "entity_root_id": entity["root_id"],
        "entity_state_id": entity["state_id"],
    }


def _sealed_input(
    session: BoundedWorldModelInvestigationSession,
    *,
    snapshot_id: object,
    previous_step: object | None = None,
) -> dict[str, object]:
    previous_result = None
    previous_progress = None
    if previous_step is not None:
        previous_result = {
            "operation": previous_step.proposal.operation.value,
            "results": tuple(
                item.canonical_value() for item in previous_step.results
            ),
            "evidence_requests": [
                item.canonical_value()
                for item in previous_step.proposal.evidence_requests
            ],
        }
        previous_progress = {
            "progress_token": previous_step.progress_token.value,
            "query_bytes": previous_step.query_bytes,
            "result_bytes": previous_step.result_bytes,
            "support_item_count": previous_step.support_item_count,
            "completeness": session.current_completeness.canonical_value(),
        }
    return {
        "original_question": "Explain all relevant methods and direct calls.",
        "response_language": "en",
        "need_key": "implementation-answer",
        "read_authority": {"snapshot_ids": [snapshot_id.value]},
        "profile_ref": JAVA_SOURCE_SEMANTICS_PROFILE_REF,
        "step_index": session.model_call_count + 1,
        "trace_digest": session.trace_digest.value,
        "previous_result": previous_result,
        "progress_receipt": previous_progress,
        "remaining_budget": {
            "model_calls": 4 - session.model_call_count,
            "execution_steps": 4 - len(session.steps),
        },
    }


def _intent(
    operation: str,
    *,
    search_terms: list[str] | None = None,
    relation_intent: str | None = None,
    finish_reason: str | None = None,
    evidence_requests: list[dict[str, str | None]] | None = None,
) -> dict[str, object]:
    return {
        "operation": operation,
        "search_terms": search_terms or [],
        "relation_intent": relation_intent,
        "finish_reason": finish_reason,
        "evidence_requests": evidence_requests or [],
    }


def _evidence(
    operation: str,
    relation_intent: str | None = None,
) -> dict[str, str | None]:
    return {
        "operation": operation,
        "relation_intent": relation_intent,
    }


class BoundedWorldModelInvestigationTests(TestCase):
    def setUp(self) -> None:
        base = _java_semantics_tests.JavaImplementationViewTests(methodName="runTest")
        base.setUp()
        self.addCleanup(base.doCleanups)
        self.view = base.service
        self.snapshot_id = base.snapshot_id
        self.bundle = base.bundle
        self.envelope = base.envelope
        self.question_digest = digest_of("ITER-008 bounded investigation fixture")

    def _session(
        self,
        *,
        view: StructureViewService | None = None,
    ) -> BoundedWorldModelInvestigationSession:
        return BoundedWorldModelInvestigationSession(
            view=view or self.view,
            question_digest=self.question_digest,
            need_ids=("implementation-answer",),
            clock_ns=lambda: 1_000_000,
        )

    def _view_with_complete_discovery_recall(self) -> StructureViewService:
        binding = StructureBusinessDiscoveryRecallBinding.create(
            oracle_ref="fixture-pre-question-discovery-oracle@1",
            oracle_result_digest=digest_of(
                "fixture-pre-question-discovery-oracle-result"
            ),
            profile_ref=JAVA_SOURCE_SEMANTICS_PROFILE_REF,
            discovery_contract_ref=(
                JAVA_IMPLEMENTATION_FEATURE_DISCOVERY_CONTRACT_REF
            ),
            snapshot_id=self.snapshot_id,
            snapshot_bundle_digest=self.bundle.digest,
            counterexample_classes=("naming", "synonym", "alternate-entry"),
            verdict=StructureBusinessDiscoveryRecallVerdict.COMPLETE,
        )
        envelope = StructureOrderedReadBundle.create(
            session=self.view.read_session,
            snapshots=self.envelope.snapshots,
            business_discovery_recall_bindings=(binding,),
        )
        return StructureViewService(
            envelope,
            ((self.bundle, envelope.snapshots[0].file_digest),),
        )

    def test_multi_candidate_result_drives_three_method_batch_without_top_one(self) -> None:
        session = self._session()
        candidate_step = session.submit(
            _proposal(
                session,
                "implementation_candidates",
                snapshot_id=self.snapshot_id.value,
                search_terms=["credentials", "failure", "session"],
                limit=10,
            )
        )
        assert candidate_step is not None
        candidate_result = candidate_step.results[0]
        candidates = candidate_result.payload["candidates"]
        self.assertEqual(len(candidates), 3)

        method_step = session.submit(
            _proposal(
                session,
                "method_implementations",
                candidate_result_id=candidate_result.result_id.value,
                candidate_result_digest=candidate_result.digest.value,
                method_refs=[
                    _ref(candidate_result, candidate["method"])
                    for candidate in candidates
                ],
            )
        )
        assert method_step is not None
        self.assertEqual(len(method_step.results), 3)
        self.assertEqual(
            tuple(item.payload["canonical_signature"] for item in method_step.results),
            tuple(item["canonical_signature"] for item in candidates),
        )

        self.assertIsNone(
            session.submit(
                _proposal(session, "FINISH", finish_reason="support-sufficient")
            )
        )
        trace = session.seal()

        self.assertEqual(trace.model_call_count, 3)
        self.assertEqual(trace.terminal_status, InvestigationTerminalStatus.FINISHED)
        self.assertFalse(trace.completeness.bounded_absence_allowed)
        validate_bounded_investigation_trace(
            trace,
            view=self.view,
            question_digest=self.question_digest,
        )

    def test_platform_compiles_opaque_arguments_and_valid_inventory_transition(self) -> None:
        session = self._session()
        inventory_evidence = [_evidence("declared_method_inventory")]
        candidate_mapping = compile_investigation_intent(
            _intent(
                "implementation_candidates",
                search_terms=["credentials", "failure", "session"],
                evidence_requests=inventory_evidence,
            ),
            sealed_input=_sealed_input(
                session,
                snapshot_id=self.snapshot_id,
            ),
        )
        candidate_step = session.submit(
            InvestigationProposal.from_mapping(
                candidate_mapping,
                model_proposal_digest=digest_of("candidate-intent"),
            )
        )
        assert candidate_step is not None

        declaring_mapping = compile_investigation_intent(
            _intent(
                "direct_neighborhood",
                relation_intent="DECLARING_TYPE",
            ),
            sealed_input=_sealed_input(
                session,
                snapshot_id=self.snapshot_id,
                previous_step=candidate_step,
            ),
        )
        self.assertEqual(declaring_mapping["direction"], "INCOMING")
        self.assertEqual(declaring_mapping["predicate"], "DECLARES_METHOD")
        self.assertEqual(
            declaring_mapping["entity_refs"][0]["source_result_id"],
            candidate_step.results[0].result_id.value,
        )
        declaring_step = session.submit(
            InvestigationProposal.from_mapping(
                declaring_mapping,
                model_proposal_digest=digest_of("declaring-type-intent"),
            )
        )
        assert declaring_step is not None

        inventory_mapping = compile_investigation_intent(
            _intent("declared_method_inventory"),
            sealed_input=_sealed_input(
                session,
                snapshot_id=self.snapshot_id,
                previous_step=declaring_step,
            ),
        )
        inventory_step = session.submit(
            InvestigationProposal.from_mapping(
                inventory_mapping,
                model_proposal_digest=digest_of("inventory-intent"),
            )
        )
        assert inventory_step is not None
        self.assertEqual(inventory_step.results[0].payload["method_count"], 3)

        finish_mapping = compile_investigation_intent(
            _intent(
                "FINISH",
                finish_reason="typed support is complete",
            ),
            sealed_input=_sealed_input(
                session,
                snapshot_id=self.snapshot_id,
                previous_step=inventory_step,
            ),
        )
        session.submit(
            InvestigationProposal.from_mapping(
                finish_mapping,
                model_proposal_digest=digest_of("finish-intent"),
            )
        )
        validate_bounded_investigation_trace(
            session.seal(),
            view=self.view,
            question_digest=self.question_digest,
        )

    def test_platform_deduplicates_model_owned_search_terms_in_first_seen_order(self) -> None:
        session = self._session()

        mapping = compile_investigation_intent(
            _intent(
                "implementation_candidates",
                search_terms=["account", "order", "ORDER", "locking"],
                evidence_requests=[_evidence("method_implementations")],
            ),
            sealed_input=_sealed_input(
                session,
                snapshot_id=self.snapshot_id,
            ),
        )

        self.assertEqual(mapping["search_terms"], ["account", "order", "locking"])
        InvestigationProposal.from_mapping(
            mapping,
            model_proposal_digest=digest_of("deduplicated-search-intent"),
        ).require_valid()

        with self.assertRaisesRegex(DomainError, "outside its closed bound"):
            compile_investigation_intent(
                _intent(
                    "implementation_candidates",
                    search_terms=[f"term-{index}" for index in range(13)],
                    evidence_requests=[_evidence("method_implementations")],
                ),
                sealed_input=_sealed_input(
                    session,
                    snapshot_id=self.snapshot_id,
                ),
            )

    def test_platform_normalizes_evidence_dependencies_and_budget(self) -> None:
        self.assertEqual(
            normalize_investigation_evidence_requests(
                [_evidence("implementation_candidates")]
            ),
            (_evidence("method_implementations"),),
        )
        self.assertEqual(
            normalize_investigation_evidence_requests(
                [
                    _evidence("implementation_candidates"),
                    _evidence("method_implementations"),
                    _evidence("direct_neighborhood", "OUTGOING_CALLS"),
                ]
            ),
            (_evidence("direct_neighborhood", "OUTGOING_CALLS"),),
        )
        session = self._session()
        compiled = compile_investigation_intent(
            _intent(
                "implementation_candidates",
                search_terms=["credentials", "failure", "session"],
                evidence_requests=[_evidence("implementation_candidates")],
            ),
            sealed_input=_sealed_input(
                session,
                snapshot_id=self.snapshot_id,
            ),
            available_operations=("implementation_candidates",),
        )
        self.assertEqual(
            compiled["evidence_requests"],
            [_evidence("method_implementations")],
        )
        candidate_step = session.submit(
            InvestigationProposal.from_mapping(
                compiled,
                model_proposal_digest=digest_of("candidate-evidence-alias"),
            )
        )
        assert candidate_step is not None
        self.assertGreater(
            candidate_step.results[0].payload["candidate_count"],
            0,
        )
        self.assertEqual(
            constrained_investigation_operations(
                sealed_input=_sealed_input(
                    session,
                    snapshot_id=self.snapshot_id,
                    previous_step=candidate_step,
                )
            ),
            ("method_implementations",),
        )
        self.assertEqual(
            normalize_investigation_evidence_requests(
                [
                    _evidence("direct_neighborhood", "OUTGOING_CALLS"),
                    _evidence("direct_neighborhood", "INCOMING_CALLS"),
                ]
            ),
            (_evidence("direct_neighborhood", "BOTH_CALLS"),),
        )
        with self.assertRaisesRegex(DomainError, "cannot be combined"):
            normalize_investigation_evidence_requests(
                [
                    _evidence("declared_method_inventory"),
                    _evidence("direct_neighborhood", "BOTH_CALLS"),
                ]
            )

    def test_platform_projects_only_the_selected_operation_semantic_slots(self) -> None:
        session = self._session()
        sealed_input = _sealed_input(session, snapshot_id=self.snapshot_id)
        direct_evidence = [
            _evidence("direct_neighborhood", "OUTGOING_CALLS")
        ]
        canonical_candidate = compile_investigation_intent(
            _intent(
                "implementation_candidates",
                search_terms=["credentials", "failure", "session"],
                evidence_requests=direct_evidence,
            ),
            sealed_input=sealed_input,
            available_operations=constrained_investigation_operations(
                sealed_input=sealed_input
            ),
        )
        projected_candidate = compile_investigation_intent(
            _intent(
                "implementation_candidates",
                search_terms=["credentials", "failure", "session"],
                relation_intent="BOTH_CALLS",
                finish_reason="irrelevant fixed-envelope residue",
                evidence_requests=direct_evidence,
            ),
            sealed_input=sealed_input,
        )
        self.assertEqual(projected_candidate, canonical_candidate)
        candidate_step = session.submit(
            InvestigationProposal.from_mapping(
                projected_candidate,
                model_proposal_digest=digest_of("projected-candidate-intent"),
            )
        )
        assert candidate_step is not None

        later_input = _sealed_input(
            session,
            snapshot_id=self.snapshot_id,
            previous_step=candidate_step,
        )
        canonical_method_batch = compile_investigation_intent(
            _intent("method_implementations"),
            sealed_input=later_input,
        )
        projected_method_batch = compile_investigation_intent(
            _intent(
                "FINISH",
                search_terms=["irrelevant"],
                relation_intent="INCOMING_CALLS",
                finish_reason="premature terminal intent",
            ),
            sealed_input=later_input,
        )
        self.assertEqual(projected_method_batch, canonical_method_batch)
        method_step = session.submit(
            InvestigationProposal.from_mapping(
                projected_method_batch,
                model_proposal_digest=digest_of("projected-method-intent"),
            )
        )
        assert method_step is not None

        method_input = _sealed_input(
            session,
            snapshot_id=self.snapshot_id,
            previous_step=method_step,
        )
        canonical_direct = compile_investigation_intent(
            _intent(
                "direct_neighborhood",
                relation_intent="OUTGOING_CALLS",
            ),
            sealed_input=method_input,
        )
        projected_direct = compile_investigation_intent(
            _intent(
                "FINISH",
                search_terms=["irrelevant"],
                relation_intent="BOTH_CALLS",
                finish_reason="premature terminal intent",
            ),
            sealed_input=method_input,
        )
        self.assertEqual(projected_direct, canonical_direct)
        direct_step = session.submit(
            InvestigationProposal.from_mapping(
                projected_direct,
                model_proposal_digest=digest_of("projected-direct-intent"),
            )
        )
        assert direct_step is not None

        direct_input = _sealed_input(
            session,
            snapshot_id=self.snapshot_id,
            previous_step=direct_step,
        )
        canonical_finish = compile_investigation_intent(
            _intent(
                "FINISH",
                finish_reason="typed support is complete",
            ),
            sealed_input=direct_input,
        )
        projected_finish = compile_investigation_intent(
            _intent(
                "FINISH",
                search_terms=["irrelevant"],
                relation_intent="BOTH_CALLS",
                finish_reason="untrusted model terminal text",
            ),
            sealed_input=direct_input,
        )
        self.assertEqual(projected_finish, canonical_finish)

        with self.assertRaisesRegex(DomainError, "available operations"):
            compile_investigation_intent(
                _intent("FINISH", finish_reason="done"),
                sealed_input=direct_input,
                available_operations=("method_implementations",),
            )

    def test_truncated_candidate_has_no_illegal_method_batch_transition(self) -> None:
        session = self._session()
        candidate_mapping = compile_investigation_intent(
            _intent(
                "implementation_candidates",
                search_terms=["credentials"],
                evidence_requests=[_evidence("method_implementations")],
            ),
            sealed_input=_sealed_input(
                session,
                snapshot_id=self.snapshot_id,
            ),
            available_operations=("implementation_candidates",),
        )
        candidate_step = session.submit(
            InvestigationProposal.from_mapping(
                candidate_mapping,
                model_proposal_digest=digest_of("candidate-intent"),
            )
        )
        assert candidate_step is not None
        sealed_input = _sealed_input(
            session,
            snapshot_id=self.snapshot_id,
            previous_step=candidate_step,
        )
        previous_result = dict(sealed_input["previous_result"])
        result = dict(previous_result["results"][0])
        result["truncated"] = True
        previous_result["results"] = (result,)
        sealed_input["previous_result"] = previous_result
        progress = dict(sealed_input["progress_receipt"])
        completeness = dict(progress["completeness"])
        completeness["query_result"] = "UNKNOWN"
        progress["completeness"] = completeness
        sealed_input["progress_receipt"] = progress

        self.assertEqual(
            constrained_investigation_operations(sealed_input=sealed_input),
            ("FINISH",),
        )
        compiled = compile_investigation_intent(
            _intent("method_implementations"),
            sealed_input=sealed_input,
            available_operations=("FINISH",),
        )
        self.assertEqual(compiled["operation"], "FINISH")
        self.assertIn("query completeness", compiled["finish_reason"])

    def test_path_intent_selects_method_endpoints_from_real_batch_results(self) -> None:
        session = self._session()
        path_evidence = [_evidence("path_exists")]
        candidate_mapping = compile_investigation_intent(
            _intent(
                "implementation_candidates",
                search_terms=["credentials", "failure", "session"],
                evidence_requests=path_evidence,
            ),
            sealed_input=_sealed_input(
                session,
                snapshot_id=self.snapshot_id,
            ),
        )
        candidate_step = session.submit(
            InvestigationProposal.from_mapping(
                candidate_mapping,
                model_proposal_digest=digest_of("path-candidate-intent"),
            )
        )
        assert candidate_step is not None
        candidate_direct_mapping = compile_investigation_intent(
            _intent(
                "direct_neighborhood",
                relation_intent="OUTGOING_CALLS",
            ),
            sealed_input=_sealed_input(
                session,
                snapshot_id=self.snapshot_id,
                previous_step=candidate_step,
            ),
        )
        self.assertEqual(
            candidate_direct_mapping["operation"],
            "method_implementations",
        )
        candidate_path_mapping = compile_investigation_intent(
            _intent("path_exists"),
            sealed_input=_sealed_input(
                session,
                snapshot_id=self.snapshot_id,
                previous_step=candidate_step,
            ),
        )
        self.assertEqual(candidate_path_mapping, candidate_direct_mapping)
        method_mapping = compile_investigation_intent(
            _intent("method_implementations"),
            sealed_input=_sealed_input(
                session,
                snapshot_id=self.snapshot_id,
                previous_step=candidate_step,
            ),
        )
        method_step = session.submit(
            InvestigationProposal.from_mapping(
                method_mapping,
                model_proposal_digest=digest_of("path-method-intent"),
            )
        )
        assert method_step is not None
        self.assertEqual(len(method_step.results), 3)

        path_mapping = compile_investigation_intent(
            _intent("path_exists"),
            sealed_input=_sealed_input(
                session,
                snapshot_id=self.snapshot_id,
                previous_step=method_step,
            ),
        )
        self.assertEqual(
            tuple(item["entity_root_id"] for item in path_mapping["entity_refs"]),
            tuple(
                item.payload["method"]["root_id"]
                for item in method_step.results[:2]
            ),
        )
        canonical_all_paths_mapping = compile_investigation_intent(
            _intent("all_simple_paths"),
            sealed_input=_sealed_input(
                session,
                snapshot_id=self.snapshot_id,
                previous_step=method_step,
            ),
        )
        projected_all_paths_mapping = compile_investigation_intent(
            _intent(
                "FINISH",
                search_terms=["irrelevant"],
                relation_intent="BOTH_CALLS",
                finish_reason="premature terminal intent",
            ),
            sealed_input=_sealed_input(
                session,
                snapshot_id=self.snapshot_id,
                previous_step=method_step,
            ),
        )
        self.assertEqual(projected_all_paths_mapping, canonical_all_paths_mapping)
        self.assertEqual(projected_all_paths_mapping, path_mapping)
        executed = session.submit(
            InvestigationProposal.from_mapping(
                path_mapping,
                model_proposal_digest=digest_of("path-relation-intent"),
            )
        )
        self.assertIsNotNone(executed)

    def test_zero_candidates_are_limitation_without_discovery_oracle(self) -> None:
        session = self._session()
        step = session.submit(
            _proposal(
                session,
                "implementation_candidates",
                snapshot_id=self.snapshot_id.value,
                search_terms=[
                    "definitelyAbsentFeature",
                    "unrepresentedBusinessEntry",
                ],
                limit=10,
                evidence_requests=[_evidence("implementation_candidates")],
            )
        )
        assert step is not None
        self.assertEqual(step.results[0].payload["candidate_count"], 0)
        session.submit(_proposal(session, "FINISH", finish_reason="no-candidates"))

        completeness = session.seal().completeness
        self.assertFalse(completeness.bounded_absence_allowed)
        self.assertEqual(
            completeness.missing_limitation_codes,
            ("BUSINESS_DISCOVERY_RECALL_UNPROVEN",),
        )

    def test_three_independent_complete_verdicts_allow_bounded_absence(self) -> None:
        bound_view = self._view_with_complete_discovery_recall()
        session = self._session(view=bound_view)
        session.submit(
            _proposal(
                session,
                "implementation_candidates",
                snapshot_id=self.snapshot_id.value,
                search_terms=[
                    "definitelyAbsentFeature",
                    "unrepresentedBusinessEntry",
                ],
                limit=10,
                evidence_requests=[_evidence("implementation_candidates")],
            )
        )
        session.submit(_proposal(session, "FINISH", finish_reason="bounded-absence"))

        trace = session.seal()
        completeness = trace.completeness
        self.assertTrue(completeness.bounded_absence_allowed)
        self.assertEqual(completeness.missing_limitation_codes, ())
        validate_bounded_investigation_trace(
            trace,
            view=bound_view,
            question_digest=self.question_digest,
        )
        forged = replace(
            trace,
            discovery_oracle=None,
            completeness=InvestigationCompleteness(
                query_result=InvestigationCompletenessVerdict.COMPLETE,
                knowledge_representation=(
                    InvestigationCompletenessVerdict.COMPLETE
                ),
                business_discovery_recall=(
                    InvestigationCompletenessVerdict.UNKNOWN
                ),
                missing_limitation_codes=(
                    "BUSINESS_DISCOVERY_RECALL_UNPROVEN",
                ),
            ),
            digest=digest_of("forged-trace-placeholder"),
        )
        forged = replace(
            forged,
            digest=digest_of(
                ["BOUNDED_INVESTIGATION_TRACE@1", forged._canonical_core()]
            ),
        )
        forged.require_valid()
        with self.assertRaisesRegex(
            DomainError,
            "another Question or Read Authority",
        ):
            validate_bounded_investigation_trace(
                forged,
                view=bound_view,
                question_digest=self.question_digest,
            )

    def test_forged_or_reordered_method_ref_fails_closed(self) -> None:
        session = self._session()
        step = session.submit(
            _proposal(
                session,
                "implementation_candidates",
                snapshot_id=self.snapshot_id.value,
                search_terms=["credentials", "failure", "session"],
                limit=10,
            )
        )
        assert step is not None
        result = step.results[0]
        candidates = result.payload["candidates"]

        with self.assertRaisesRegex(DomainError, "forged, reordered"):
            session.submit(
                _proposal(
                    session,
                    "method_implementations",
                    candidate_result_id=result.result_id.value,
                    candidate_result_digest=result.digest.value,
                    method_refs=[
                        _ref(result, candidates[1]["method"]),
                        _ref(result, candidates[0]["method"]),
                    ],
                )
            )

    def test_transition_and_terminal_fences_fail_closed(self) -> None:
        empty = self._session()
        with self.assertRaisesRegex(DomainError, "frozen evidence transition"):
            empty.submit(_proposal(empty, "FINISH", finish_reason="too-early"))
        with self.assertRaisesRegex(DomainError, "terminal investigation"):
            empty.submit(
                _proposal(
                    empty,
                    "implementation_candidates",
                    snapshot_id=self.snapshot_id.value,
                    search_terms=["session"],
                    limit=10,
                )
            )

        session = self._session()
        session.submit(
            _proposal(
                session,
                "implementation_candidates",
                snapshot_id=self.snapshot_id.value,
                search_terms=["definitelyAbsentFeature"],
                limit=10,
                evidence_requests=[_evidence("implementation_candidates")],
            )
        )
        session.submit(_proposal(session, "FINISH", finish_reason="complete"))
        with self.assertRaisesRegex(DomainError, "terminal investigation"):
            session.submit(
                _proposal(
                    session,
                    "implementation_candidates",
                    snapshot_id=self.snapshot_id.value,
                    search_terms=["session"],
                    limit=10,
                )
            )
        self.assertEqual(
            session.seal().terminal_status,
            InvestigationTerminalStatus.FINISHED,
        )

        transition = self._session()
        transition.submit(
            _proposal(
                transition,
                "implementation_candidates",
                snapshot_id=self.snapshot_id.value,
                search_terms=["credentials"],
                limit=10,
                evidence_requests=[_evidence("declared_method_inventory")],
            )
        )
        with self.assertRaisesRegex(DomainError, "frozen evidence transition"):
            transition.submit(
                _proposal(
                    transition,
                    "implementation_candidates",
                    snapshot_id=self.snapshot_id.value,
                    search_terms=["credentials"],
                    limit=10,
                )
            )

    def test_result_provenance_supports_neighborhood_inventory_and_path(self) -> None:
        inventory_session = self._session()
        first = inventory_session.submit(
            _proposal(
                inventory_session,
                "implementation_candidates",
                snapshot_id=self.snapshot_id.value,
                search_terms=["credentials"],
                limit=10,
                evidence_requests=[_evidence("declared_method_inventory")],
            )
        )
        assert first is not None
        candidate = first.results[0]
        method = candidate.payload["candidates"][0]["method"]
        neighborhood = inventory_session.submit(
            _proposal(
                inventory_session,
                "direct_neighborhood",
                entity_refs=[_ref(candidate, method)],
                direction="INCOMING",
                predicate="DECLARES_METHOD",
            )
        )
        assert neighborhood is not None
        neighborhood_result = neighborhood.results[0]
        java_type = neighborhood_result.payload["neighbors"][0]
        inventory = inventory_session.submit(
            _proposal(
                inventory_session,
                "declared_method_inventory",
                entity_refs=[_ref(neighborhood_result, java_type)],
            )
        )
        assert inventory is not None
        self.assertEqual(inventory.results[0].payload["method_count"], 3)
        inventory_session.submit(
            _proposal(inventory_session, "FINISH", finish_reason="inventory-complete")
        )
        validate_bounded_investigation_trace(
            inventory_session.seal(),
            view=self.view,
            question_digest=self.question_digest,
        )

        path_session = self._session()
        candidate_step = path_session.submit(
            _proposal(
                path_session,
                "implementation_candidates",
                snapshot_id=self.snapshot_id.value,
                search_terms=["credentials", "failure", "session"],
                limit=10,
                evidence_requests=[_evidence("path_exists")],
            )
        )
        assert candidate_step is not None
        candidate_result = candidate_step.results[0]
        values = candidate_result.payload["candidates"]
        method_step = path_session.submit(
            _proposal(
                path_session,
                "method_implementations",
                candidate_result_id=candidate_result.result_id.value,
                candidate_result_digest=candidate_result.digest.value,
                method_refs=[
                    _ref(candidate_result, item["method"])
                    for item in values
                ],
            )
        )
        assert method_step is not None
        path = path_session.submit(
            _proposal(
                path_session,
                "path_exists",
                entity_refs=[
                    _ref(method_step.results[0], method_step.results[0].payload["method"]),
                    _ref(method_step.results[1], method_step.results[1].payload["method"]),
                ],
                predicate="CALLS",
                max_depth=4,
                max_expansions=100,
            )
        )
        assert path is not None
        self.assertTrue(path.results[0].payload["exists"])
        path_session.submit(
            _proposal(path_session, "FINISH", finish_reason="path-complete")
        )
        validate_bounded_investigation_trace(
            path_session.seal(),
            view=self.view,
            question_digest=self.question_digest,
        )

    def test_stale_snapshot_unknown_operation_and_oversize_query_fail_closed(self) -> None:
        stale = self._session()
        with self.assertRaises(DomainError):
            stale.submit(
                _proposal(
                    stale,
                    "implementation_candidates",
                    snapshot_id="structure_snapshot_" + "f" * 32,
                    search_terms=["credentials"],
                    limit=10,
                )
            )

        with self.assertRaisesRegex(DomainError, "unregistered operation"):
            _proposal(self._session(), "read_source_file")

        class OversizeView:
            def __getattr__(self, name):
                return getattr(self._delegate, name)

            def __init__(self, delegate) -> None:
                self._delegate = delegate

            def implementation_candidates(self, **arguments):
                result = self._delegate.implementation_candidates(**arguments)
                return replace(
                    result,
                    payload={**result.payload, "oversize": "x" * 270_000},
                )

        oversize = BoundedWorldModelInvestigationSession(
            view=OversizeView(self.view),
            question_digest=self.question_digest,
            need_ids=("implementation-answer",),
            clock_ns=lambda: 1_000_000,
        )
        with self.assertRaisesRegex(DomainError, "byte budget"):
            oversize.submit(
                _proposal(
                    oversize,
                    "implementation_candidates",
                    snapshot_id=self.snapshot_id.value,
                    search_terms=["credentials"],
                    limit=10,
                )
            )
        self.assertEqual(oversize.steps, ())

        class TamperedView(OversizeView):
            def implementation_candidates(self, **arguments):
                result = self._delegate.implementation_candidates(**arguments)
                return replace(
                    result,
                    payload={**result.payload, "unsealed": True},
                )

        tampered = BoundedWorldModelInvestigationSession(
            view=TamperedView(self.view),
            question_digest=self.question_digest,
            need_ids=("implementation-answer",),
            clock_ns=lambda: 1_000_000,
        )
        with self.assertRaisesRegex(DomainError, "not canonical"):
            tampered.submit(
                _proposal(
                    tampered,
                    "implementation_candidates",
                    snapshot_id=self.snapshot_id.value,
                    search_terms=["credentials"],
                    limit=10,
                )
            )
        self.assertTrue(tampered.terminal)
        self.assertEqual(tampered.steps, ())

    def test_fourth_model_call_seals_budget_limitation_without_retry(self) -> None:
        session = self._session()
        plan = [
            _evidence("direct_neighborhood", "BOTH_CALLS"),
            _evidence("all_simple_paths"),
        ]
        candidate = session.submit(
            _proposal(
                session,
                "implementation_candidates",
                snapshot_id=self.snapshot_id.value,
                search_terms=["credentials", "failure", "session"],
                limit=10,
                evidence_requests=plan,
            )
        )
        assert candidate is not None
        candidate_result = candidate.results[0]
        method = session.submit(
            _proposal(
                session,
                "method_implementations",
                candidate_result_id=candidate_result.result_id.value,
                candidate_result_digest=candidate_result.digest.value,
                method_refs=[
                    _ref(candidate_result, item["method"])
                    for item in candidate_result.payload["candidates"]
                ],
            )
        )
        assert method is not None
        direct = session.submit(
            _proposal(
                session,
                "direct_neighborhood",
                entity_refs=[
                    _ref(method.results[0], method.results[0].payload["method"])
                ],
                direction="BOTH",
                predicate="CALLS",
            )
        )
        assert direct is not None
        last_mapping = compile_investigation_intent(
            _intent(
                "FINISH",
                finish_reason="premature terminal intent",
            ),
            sealed_input=_sealed_input(
                session,
                snapshot_id=self.snapshot_id,
                previous_step=direct,
            ),
        )
        self.assertEqual(last_mapping["operation"], "all_simple_paths")
        last_proposal = InvestigationProposal.from_mapping(
            last_mapping,
            model_proposal_digest=digest_of("projected-all-paths-intent"),
        )
        self.assertIsNotNone(session.submit(last_proposal))

        trace = session.seal()
        self.assertEqual(trace.model_call_count, 4)
        self.assertEqual(
            trace.terminal_status,
            InvestigationTerminalStatus.LIMITATION,
        )
        self.assertEqual(trace.terminal_reason, "INVESTIGATION_BUDGET_EXHAUSTED")
        with self.assertRaisesRegex(DomainError, "terminal investigation"):
            session.submit(last_proposal)

    def test_wall_time_and_question_replay_fences_fail_closed(self) -> None:
        clock_values = iter((0, 900_001_000_000))
        timed = BoundedWorldModelInvestigationSession(
            view=self.view,
            question_digest=self.question_digest,
            need_ids=("implementation-answer",),
            clock_ns=lambda: next(clock_values),
        )
        with self.assertRaisesRegex(DomainError, "wall-time budget"):
            timed.submit(
                _proposal(
                    timed,
                    "implementation_candidates",
                    snapshot_id=self.snapshot_id.value,
                    search_terms=["credentials"],
                    limit=10,
                )
            )
        self.assertEqual(timed.steps, ())

        session = self._session()
        session.submit(
            _proposal(
                session,
                "implementation_candidates",
                snapshot_id=self.snapshot_id.value,
                search_terms=["definitelyAbsentFeature", "missingEntry"],
                limit=10,
                evidence_requests=[_evidence("implementation_candidates")],
            )
        )
        session.submit(_proposal(session, "FINISH", finish_reason="done"))
        trace = session.seal()
        with self.assertRaisesRegex(DomainError, "another Question"):
            validate_bounded_investigation_trace(
                trace,
                view=self.view,
                question_digest=digest_of("another question"),
            )
