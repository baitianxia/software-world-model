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
        candidate_mapping = compile_investigation_intent(
            {
                "operation": "implementation_candidates",
                "search_terms": ["credentials", "failure", "session"],
                "relation_intent": None,
                "finish_reason": None,
            },
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
            {
                "operation": "direct_neighborhood",
                "search_terms": [],
                "relation_intent": "DECLARING_TYPE",
                "finish_reason": None,
            },
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
            {
                "operation": "declared_method_inventory",
                "search_terms": [],
                "relation_intent": None,
                "finish_reason": None,
            },
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
            {
                "operation": "FINISH",
                "search_terms": [],
                "relation_intent": None,
                "finish_reason": "typed support is complete",
            },
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
            {
                "operation": "implementation_candidates",
                "search_terms": ["account", "order", "ORDER", "locking"],
                "relation_intent": None,
                "finish_reason": None,
            },
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
                {
                    "operation": "implementation_candidates",
                    "search_terms": [f"term-{index}" for index in range(13)],
                    "relation_intent": None,
                    "finish_reason": None,
                },
                sealed_input=_sealed_input(
                    session,
                    snapshot_id=self.snapshot_id,
                ),
            )

    def test_path_intent_selects_method_endpoints_from_real_batch_results(self) -> None:
        session = self._session()
        candidate_mapping = compile_investigation_intent(
            {
                "operation": "implementation_candidates",
                "search_terms": ["credentials", "failure", "session"],
                "relation_intent": None,
                "finish_reason": None,
            },
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
            {
                "operation": "direct_neighborhood",
                "search_terms": [],
                "relation_intent": "OUTGOING_CALLS",
                "finish_reason": None,
            },
            sealed_input=_sealed_input(
                session,
                snapshot_id=self.snapshot_id,
                previous_step=candidate_step,
            ),
        )
        self.assertEqual(
            candidate_direct_mapping["entity_refs"],
            [
                _ref(
                    candidate_step.results[0],
                    candidate_step.results[0].payload["candidates"][0]["method"],
                )
            ],
        )
        candidate_path_mapping = compile_investigation_intent(
            {
                "operation": "path_exists",
                "search_terms": [],
                "relation_intent": None,
                "finish_reason": None,
            },
            sealed_input=_sealed_input(
                session,
                snapshot_id=self.snapshot_id,
                previous_step=candidate_step,
            ),
        )
        self.assertEqual(len(candidate_path_mapping["entity_refs"]), 2)
        method_mapping = compile_investigation_intent(
            {
                "operation": "method_implementations",
                "search_terms": [],
                "relation_intent": None,
                "finish_reason": None,
            },
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
            {
                "operation": "path_exists",
                "search_terms": [],
                "relation_intent": None,
                "finish_reason": None,
            },
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
        executed = session.submit(
            InvestigationProposal.from_mapping(
                path_mapping,
                model_proposal_digest=digest_of("path-relation-intent"),
            )
        )
        self.assertIsNotNone(executed)

    def test_zero_candidates_are_limitation_without_discovery_oracle(self) -> None:
        session = self._session()
        for term in ("definitelyAbsentFeature", "unrepresentedBusinessEntry"):
            step = session.submit(
                _proposal(
                    session,
                    "implementation_candidates",
                    snapshot_id=self.snapshot_id.value,
                    search_terms=[term],
                    limit=10,
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
        for term in ("definitelyAbsentFeature", "unrepresentedBusinessEntry"):
            session.submit(
                _proposal(
                    session,
                    "implementation_candidates",
                    snapshot_id=self.snapshot_id.value,
                    search_terms=[term],
                    limit=10,
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

    def test_cycle_and_finish_without_result_fail_closed(self) -> None:
        empty = self._session()
        with self.assertRaisesRegex(DomainError, "at least one executed"):
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
                search_terms=["credentials"],
                limit=10,
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

        cycle = self._session()
        for _ in range(2):
            proposal = _proposal(
                cycle,
                "implementation_candidates",
                snapshot_id=self.snapshot_id.value,
                search_terms=["credentials"],
                limit=10,
            )
            if cycle.model_call_count == 0:
                cycle.submit(proposal)
            else:
                with self.assertRaisesRegex(DomainError, "no-progress"):
                    cycle.submit(proposal)

    def test_result_provenance_supports_neighborhood_inventory_and_path(self) -> None:
        inventory_session = self._session()
        first = inventory_session.submit(
            _proposal(
                inventory_session,
                "implementation_candidates",
                snapshot_id=self.snapshot_id.value,
                search_terms=["credentials"],
                limit=10,
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
            )
        )
        assert candidate_step is not None
        candidate_result = candidate_step.results[0]
        values = candidate_result.payload["candidates"]
        path = path_session.submit(
            _proposal(
                path_session,
                "path_exists",
                entity_refs=[
                    _ref(candidate_result, values[0]["method"]),
                    _ref(candidate_result, values[1]["method"]),
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
        last_proposal = None
        for ordinal in range(4):
            last_proposal = _proposal(
                session,
                "implementation_candidates",
                snapshot_id=self.snapshot_id.value,
                search_terms=[f"absent-feature-{ordinal}"],
                limit=10,
            )
            step = session.submit(
                last_proposal
            )
            self.assertIsNotNone(step)

        trace = session.seal()
        self.assertEqual(trace.model_call_count, 4)
        self.assertEqual(
            trace.terminal_status,
            InvestigationTerminalStatus.LIMITATION,
        )
        self.assertEqual(trace.terminal_reason, "INVESTIGATION_BUDGET_EXHAUSTED")
        assert last_proposal is not None
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
        for term in ("credentials", "session"):
            session.submit(
                _proposal(
                    session,
                    "implementation_candidates",
                    snapshot_id=self.snapshot_id.value,
                    search_terms=[term],
                    limit=10,
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
