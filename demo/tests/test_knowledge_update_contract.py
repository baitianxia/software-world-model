from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
import unittest

from swm_demo.artifact_contract import ArtifactRequest
from swm_demo.knowledge_contract import (
    Evidence,
    FactCandidate,
    InferenceCandidate,
    KnowledgeBuildTarget,
    KnowledgeEntity,
)
from swm_demo.knowledge_requirement import (
    FACT,
    GAP,
    SATISFIED,
    FormalKnowledgeReference,
    KnowledgeNeed,
    KnowledgeRequirement,
    KnowledgeSufficiencyAssessment,
    KnowledgeSufficiencyItem,
)
from swm_demo.knowledge_update import (
    BuildIntent,
    CandidateBundle,
    InvestigationHandle,
    InvestigationState,
    KnowledgeUpdateResult,
)


SCOPE_ID = "system:update-contract"
REVISION = "revision:target"


def _requirement(scope_id: str = SCOPE_ID) -> KnowledgeRequirement:
    return KnowledgeRequirement(
        requirement_id="requirement:update-contract",
        task_id="task:update-contract",
        scope_id=scope_id,
        knowledge_context_reference="context:target",
        needs=(
            KnowledgeNeed(
                need_id="need:entry",
                question="Which entry handles the request?",
                sufficiency_criterion="An admitted endpoint Fact identifies it.",
            ),
            KnowledgeNeed(
                need_id="need:flow",
                question="What behavior follows from the entry?",
                sufficiency_criterion="Every reported behavior has formal support.",
            ),
        ),
        formation_model_call_id="model-call:requirement",
    )


def _assessment(
    *, complete: bool = False, scope_id: str = SCOPE_ID
) -> KnowledgeSufficiencyAssessment:
    requirement = _requirement(scope_id)
    return KnowledgeSufficiencyAssessment(
        assessment_id=(
            "assessment:complete" if complete else "assessment:with-gap"
        ),
        requirement=requirement,
        snapshot_id="snapshot:before",
        knowledge_context_reference=requirement.knowledge_context_reference,
        items=(
            KnowledgeSufficiencyItem(
                need_id="need:entry",
                status=SATISFIED,
                formal_knowledge_references=(
                    FormalKnowledgeReference(FACT, "fact:entry"),
                ),
            ),
            KnowledgeSufficiencyItem(
                need_id="need:flow",
                status=SATISFIED if complete else GAP,
                formal_knowledge_references=(
                    (FormalKnowledgeReference(FACT, "fact:flow"),)
                    if complete
                    else ()
                ),
                rationale="" if complete else "behavior knowledge is absent",
            ),
        ),
        assessment_model_call_id="model-call:assessment",
    )


def _intent(**overrides: object) -> BuildIntent:
    assessment = overrides.pop("assessment", _assessment())
    assert isinstance(assessment, KnowledgeSufficiencyAssessment)
    values: dict[str, object] = {
        "intent_id": "intent:update-contract",
        "requirement_id": assessment.requirement_id,
        "scope_id": assessment.requirement.scope_id,
        "assessment": assessment,
        "gap_need_ids": ("need:flow",),
        "artifact_request": ArtifactRequest(
            build_profile="model-led",
            include_globs=("**/*.java",),
            derive_java_ast=True,
        ),
        "build_target": KnowledgeBuildTarget(
            behavior_methods=(("ExampleService", "execute"),)
        ),
        "target_revision": REVISION,
        "minimum_result_need_ids": ("need:flow",),
        "formation_model_call_id": "model-call:build-intent",
    }
    values.update(overrides)
    return BuildIntent(**values)  # type: ignore[arg-type]


def _bundle_values() -> dict[str, object]:
    subject = KnowledgeEntity(
        entity_id="entity:subject",
        scope_id=SCOPE_ID,
        entity_type="java-method",
        name="ExampleService#execute",
    )
    operation = KnowledgeEntity(
        entity_id="entity:operation",
        scope_id=SCOPE_ID,
        entity_type="operation",
        name="repository.save",
    )
    observation = Evidence(
        evidence_id="evidence:save-call",
        artifact_id="artifact:example-service",
        scope_id=SCOPE_ID,
        revision=REVISION,
        line_start=10,
        line_end=10,
        quote="repository.save(value);",
        quote_hash="hash:save-call",
    )
    fact = FactCandidate(
        fact_id="fact:calls-save",
        scope_id=SCOPE_ID,
        revision=REVISION,
        subject_id=subject.entity_id,
        predicate="CALLS_OPERATION",
        object_id=operation.entity_id,
        evidence_ids=(observation.evidence_id,),
        model_call_id="model-call:proposal",
    )
    inference = InferenceCandidate(
        inference_id="inference:persists-value",
        scope_id=SCOPE_ID,
        revision=REVISION,
        inference_type="BEHAVIOR",
        statement="The operation persists the supplied value.",
        support_fact_ids=(fact.fact_id,),
        model_call_id="model-call:proposal",
    )
    return {
        "bundle_id": "bundle:update-contract",
        "intent_id": "intent:update-contract",
        "scope_id": SCOPE_ID,
        "source_artifact_ids": (observation.artifact_id,),
        "entities": (subject, operation),
        "evidence": (observation,),
        "fact_candidates": (fact,),
        "inference_candidates": (inference,),
        "covered_need_ids": ("need:flow",),
        "unresolved_need_ids": (),
        "proposal_model_call_id": "model-call:proposal",
    }


def _bundle(**overrides: object) -> CandidateBundle:
    values = _bundle_values()
    values.update(overrides)
    return CandidateBundle(**values)  # type: ignore[arg-type]


class BuildIntentContractTest(unittest.TestCase):
    def test_build_intent_is_frozen_and_exactly_binds_all_gaps(self) -> None:
        intent = _intent()

        self.assertEqual(("need:flow",), intent.gap_need_ids)
        self.assertEqual(intent.gap_need_ids, intent.minimum_result_need_ids)
        self.assertIs(intent.assessment.requirement, intent.assessment.requirement)
        self.assertEqual(REVISION, intent.target_revision)
        with self.assertRaises(FrozenInstanceError):
            intent.target_revision = "revision:changed"  # type: ignore[misc]

    def test_build_intent_rejects_complete_or_inexact_gap_assessment(self) -> None:
        with self.assertRaisesRegex(ValueError, "incomplete GAP assessment"):
            _intent(
                assessment=_assessment(complete=True),
                gap_need_ids=(),
                minimum_result_need_ids=(),
            )

        with self.assertRaisesRegex(ValueError, "exactly match every GAP"):
            _intent(gap_need_ids=("need:entry",))

        with self.assertRaisesRegex(ValueError, "exactly cover all gap_need_ids"):
            _intent(minimum_result_need_ids=("need:entry",))

        with self.assertRaisesRegex(ValueError, "gap_need_ids values must be unique"):
            _intent(gap_need_ids=("need:flow", "need:flow"))

    def test_build_intent_rejects_scope_requirement_and_revision_mismatch(self) -> None:
        with self.assertRaisesRegex(ValueError, "Requirement differ"):
            _intent(requirement_id="requirement:other")

        with self.assertRaisesRegex(ValueError, "Scope differ"):
            _intent(scope_id="system:other")

        with self.assertRaisesRegex(ValueError, "target_revision must not be empty"):
            _intent(target_revision="  ")


class CandidateBundleContractTest(unittest.TestCase):
    def test_candidate_bundle_is_frozen_and_accepts_self_contained_references(self) -> None:
        bundle = _bundle()

        self.assertEqual(("artifact:example-service",), bundle.source_artifact_ids)
        self.assertEqual(
            bundle.evidence[0].evidence_id,
            bundle.fact_candidates[0].evidence_ids[0],
        )
        with self.assertRaises(FrozenInstanceError):
            bundle.scope_id = "system:changed"  # type: ignore[misc]

    def test_candidate_bundle_rejects_scope_mismatch_for_every_content_kind(self) -> None:
        values = _bundle_values()
        replacements = {
            "entities": (replace(values["entities"][0], scope_id="system:other"),),  # type: ignore[index]
            "evidence": (replace(values["evidence"][0], scope_id="system:other"),),  # type: ignore[index]
            "fact_candidates": (
                replace(values["fact_candidates"][0], scope_id="system:other"),  # type: ignore[index]
            ),
            "inference_candidates": (
                replace(values["inference_candidates"][0], scope_id="system:other"),  # type: ignore[index]
            ),
        }
        for field_name, replacement_values in replacements.items():
            with self.subTest(field_name=field_name):
                with self.assertRaisesRegex(ValueError, "share its Scope"):
                    _bundle(**{field_name: replacement_values})

    def test_candidate_bundle_rejects_out_of_bundle_artifact_and_evidence(self) -> None:
        with self.assertRaisesRegex(ValueError, "Artifact outside the bundle"):
            _bundle(source_artifact_ids=("artifact:other",))

        fact = replace(
            _bundle_values()["fact_candidates"][0],  # type: ignore[index]
            evidence_ids=("evidence:not-in-bundle",),
        )
        with self.assertRaisesRegex(ValueError, "Evidence outside the bundle"):
            _bundle(fact_candidates=(fact,))

        fact_without_evidence = replace(fact, evidence_ids=())
        with self.assertRaisesRegex(ValueError, "has no Evidence"):
            _bundle(fact_candidates=(fact_without_evidence,))

    def test_candidate_bundle_rejects_duplicate_ids_and_need_overlap(self) -> None:
        with self.assertRaisesRegex(ValueError, "source_artifact_ids values must be unique"):
            _bundle(
                source_artifact_ids=(
                    "artifact:example-service",
                    "artifact:example-service",
                )
            )

        entity = _bundle_values()["entities"][0]  # type: ignore[index]
        with self.assertRaisesRegex(ValueError, "Entity IDs must be unique"):
            _bundle(entities=(entity, entity))

        with self.assertRaisesRegex(ValueError, "must not overlap"):
            _bundle(
                covered_need_ids=("need:flow",),
                unresolved_need_ids=("need:flow",),
            )

        with self.assertRaisesRegex(ValueError, "bundle_id must not be empty"):
            _bundle(bundle_id="")

    def test_candidate_bundle_requires_candidate_model_provenance(self) -> None:
        values = _bundle_values()
        fact = values["fact_candidates"][0]  # type: ignore[index]
        inference = values["inference_candidates"][0]  # type: ignore[index]

        with self.assertRaisesRegex(ValueError, "Fact Candidate model_call_id"):
            _bundle(fact_candidates=(replace(fact, model_call_id=None),))
        with self.assertRaisesRegex(ValueError, "Inference Candidate model_call_id"):
            _bundle(
                inference_candidates=(
                    replace(inference, model_call_id="model-call:other"),
                )
            )


class UpdateBoundaryContractTest(unittest.TestCase):
    def test_investigation_handle_uses_the_closed_state_enum_and_is_frozen(self) -> None:
        self.assertEqual(
            {"OPEN", "PUBLISHING", "PUBLISHED", "FAILED", "ABORTED"},
            {item.value for item in InvestigationState},
        )
        handle = InvestigationHandle(
            run_id="investigation:1",
            intent_id="intent:update-contract",
            model_context_id="model-context:investigation",
            state=InvestigationState.OPEN,
        )
        with self.assertRaises(FrozenInstanceError):
            handle.state = InvestigationState.PUBLISHED  # type: ignore[misc]
        with self.assertRaisesRegex(TypeError, "InvestigationState"):
            InvestigationHandle(
                run_id="investigation:2",
                intent_id="intent:update-contract",
                model_context_id="model-context:investigation",
                state="OPEN",  # type: ignore[arg-type]
            )

    def test_knowledge_update_result_has_only_the_content_free_whitelist(self) -> None:
        expected_fields = {
            "intent_id",
            "run_id",
            "previous_snapshot_id",
            "published_snapshot_id",
            "status",
            "admitted_reference_ids",
            "rejected_candidate_ids",
            "unresolved_need_ids",
        }
        self.assertEqual(
            expected_fields,
            {item.name for item in fields(KnowledgeUpdateResult)},
        )

        result = KnowledgeUpdateResult(
            intent_id="intent:update-contract",
            run_id="investigation:1",
            previous_snapshot_id="snapshot:before",
            published_snapshot_id="snapshot:after",
            status="PUBLISHED",
            admitted_reference_ids=("fact:calls-save",),
            rejected_candidate_ids=(),
            unresolved_need_ids=(),
        )
        self.assertFalse(
            {
                "content",
                "artifact",
                "artifacts",
                "evidence",
                "quote",
                "candidate_bundle",
                "answer",
            }
            & expected_fields
        )
        with self.assertRaises(FrozenInstanceError):
            result.status = "FAILED"  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()
