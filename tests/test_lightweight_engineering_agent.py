from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import subprocess
import tempfile
import unittest
from typing import Mapping

from software_world_model.application_services.conversational_engineering_agent import (
    EngineeringAgentCitation,
    EngineeringAgentEvidenceDisposition,
    EngineeringAgentLoopLimits,
    EngineeringAgentModelCallReceipt,
    EngineeringAgentModelDispatchState,
    EngineeringAgentModelFailureKind,
    EngineeringAgentModelRole,
    EngineeringAgentToolAuthorityKind,
    EngineeringAgentToolAuthorityReceipt,
    EngineeringAgentToolOperation,
    EngineeringAgentToolResult,
)
from software_world_model.application_services.engineering_conversation import (
    EngineeringChatBinding,
    InMemoryEngineeringConversationService,
    RuntimeCapabilityStatus,
)
from software_world_model.application_services.conversational_engineering_tools import (
    EngineeringAgentEvidenceToolAdapter,
    EngineeringAgentEvidenceToolConfiguration,
)
from software_world_model.application_services.engineering_question_answering import (
    EngineeringEvidenceClass,
    SourceBroker,
    WorldModelCognitionContext,
)
from software_world_model.application_services.java_capability_cognition import (
    ExactJavaCognitionSource,
    JavaCognitionModuleSource,
    build_java_capability_cognition,
)
from software_world_model.application_services.lightweight_engineering_agent import (
    ApplicationOwnedLightweightAgentTurnExecutor,
    LightweightAgentAction,
    LightweightAgentDecision,
    LightweightAgentResponseKind,
    LightweightAgentStepRequest,
    LightweightAgentTraceStore,
    LightweightCitationSelection,
    LightweightCognitionCandidate,
    LightweightDecisionResult,
    LightweightModelCallFailure,
    LightweightObservation,
    LightweightReadCandidate,
    LightweightReview,
    LightweightReviewResult,
    LightweightReviewVerdict,
    SealedLightweightDeliveryControl,
    _LightweightReadNavigationMetadata,
    _ordered_read_candidates,
)
from software_world_model.cross_cutting import (
    Digest,
    DomainError,
    ErrorCode,
    Revision,
    StableId,
    digest_of,
)
from software_world_model.knowledge_engine.capability_cognition import (
    CapabilityCognitionIndex,
    CognitionDirection,
    CognitionEntityKind,
    CognitionProvenance,
    CognitionRelationKind,
)
from software_world_model.interface.engineering_qa_source import (
    LocalGitEvidenceClassProfile,
    LocalGitRetrievalWorker,
)


REVISION = "a" * 40

SOURCE_FILES = {
    "app/src/main/java/com/example/CheckoutController.java": b"""package com.example;
public class CheckoutController {
    private CheckoutService checkoutService;
    public String checkout(String input) {
        if (input == null) { throw new IllegalArgumentException(); }
        return checkoutService.checkout(input);
    }
}
""",
    "app/src/main/java/com/example/CheckoutService.java": b"""package com.example;
public interface CheckoutService {
    String checkout(String input);
}
""",
    "app/src/main/java/com/example/CheckoutServiceImpl.java": b"""package com.example;
public class CheckoutServiceImpl implements CheckoutService {
    @Override
    public String checkout(String input) { return input; }
}
""",
}


def _binding() -> EngineeringChatBinding:
    return EngineeringChatBinding.create(
        product_revision="b" * 40,
        project_name="example",
        repository_revision=REVISION,
        world_model_status=RuntimeCapabilityStatus.READY,
        world_model_authority_digest=digest_of("world-model"),
        source_profile_ref="source-profile",
        source_access_status=RuntimeCapabilityStatus.READY,
        provider_status=RuntimeCapabilityStatus.READY,
        provider_route_ref="preferred-then-fallback",
        known_limitations=("diagnostic baseline",),
    )


def _id(kind: str, ordinal: int) -> StableId:
    return StableId(f"{kind}_{ordinal:032x}")


def _navigation_candidate(
    ordinal: int,
    *,
    resource: str,
    locator: str | None = None,
    modality: str = "JAVA_CAPABILITY_COGNITION_PROVENANCE_NAVIGATION",
    source_revision: str = REVISION,
) -> LightweightReadCandidate:
    content = f"synthetic-source-fragment-{ordinal}"
    citation_locator = locator or f"{resource}:L{ordinal}"
    citation = EngineeringAgentCitation.create(
        citation_ref=_id("citation", ordinal).value,
        evidence_class="SOURCE",
        source_revision=source_revision,
        locator=citation_locator,
        modality=modality,
        content_digest=digest_of(content),
    )
    return LightweightReadCandidate(
        read_index=ordinal,
        citation=citation,
        resource_locator=resource,
    )


def _read_navigation_observation(
    observation_index: int,
    candidate: LightweightReadCandidate,
) -> LightweightObservation:
    return LightweightObservation(
        observation_index=observation_index,
        operation=EngineeringAgentToolOperation.SOURCE_READ,
        disposition=EngineeringAgentEvidenceDisposition.SUPPORT,
        content=f"read-{candidate.read_index}",
        progress=True,
        citations=(candidate.citation,),
        digest=digest_of(
            {
                "fixture": "read-navigation-observation",
                "observation_index": observation_index,
                "read_index": candidate.read_index,
            }
        ),
    )


def _citation_identity(candidate: LightweightReadCandidate) -> tuple[object, ...]:
    """Capture every opaque and visible field that projection must preserve."""

    citation = candidate.citation
    return (
        candidate.read_index,
        citation.citation_ref,
        citation.evidence_class,
        citation.source_revision,
        citation.locator,
        citation.modality,
        citation.content_digest.value,
        citation.digest.value,
        candidate.resource_locator,
    )


def _replay_evidence_status(
    status: str,
    requirement: str,
    reason: str,
    **details: object,
) -> dict[str, object]:
    """Return an auditable machine-readable replay status.

    A missing historical receipt is evidence about the artifact, not a test
    success or a unittest skip.  Callers print and assert this status before
    returning so a gate or log consumer can distinguish NOT_RUN from an
    executed assertion.
    """

    if status not in {"EXECUTED", "NOT_RUN"}:
        raise ValueError("unsupported replay evidence status")
    return {
        "status": status,
        "requirement": requirement,
        "reason": reason,
        **details,
    }


def _emit_replay_evidence_status(status: Mapping[str, object]) -> None:
    print(
        "REPLAY_EVIDENCE_STATUS "
        + json.dumps(dict(status), ensure_ascii=False, sort_keys=True)
    )


class _SourceTool:
    def __init__(self) -> None:
        self.calls = []
        self._ordinal = 0
        self._cognition_paths = {}

    def source_read_options(self, request):
        return ()

    def cognition_source_read_options(self, request, provenances):
        options = []
        for provenance in provenances:
            locator_reference = _id(
                "locator", 10_000 + len(self._cognition_paths) + 1
            )
            option = EngineeringAgentCitation.create(
                citation_ref=locator_reference.value,
                locator=provenance.locator,
                evidence_class="SOURCE",
                source_revision=provenance.source_revision,
                modality=(
                    "JAVA_CAPABILITY_COGNITION_PROVENANCE_NAVIGATION"
                ),
                content_digest=provenance.content_digest,
            )
            self._cognition_paths[locator_reference.value] = provenance.path
            options.append(option)
        return tuple(options)

    def execute(self, request):
        self.calls.append(request)
        self._ordinal += 1
        operation = request.action.operation
        if operation is EngineeringAgentToolOperation.SOURCE_SEARCH:
            locator = f"src/example/Entry{self._ordinal}.java:L1-L8"
            content = json.dumps(
                {
                    "result": "search match",
                    "locator": locator,
                    "next": "read the matching source",
                },
                sort_keys=True,
            )
        else:
            requested_reference = dict(request.action.arguments)[
                "locator_reference"
            ]
            path = self._cognition_paths.get(
                requested_reference,
                f"src/example/Entry{self._ordinal}.java",
            )
            locator = f"{path}:L1-L80"
            content = json.dumps(
                {
                    "result": "full source",
                    "locator": locator,
                    "behavior": (
                        "the implementation fulfills CheckoutService and returns input"
                        if "CheckoutServiceImpl.java" in locator
                        else "the entry delegates after checking its input"
                    ),
                },
                sort_keys=True,
            )
        citation = EngineeringAgentCitation.create(
            citation_ref=_id("locator", self._ordinal).value,
            evidence_class="SOURCE",
            source_revision=REVISION,
            locator=locator,
            modality="SOURCE_TEXT",
            content_digest=digest_of(content),
        )
        evidence_request_digest = digest_of(
            ["test-evidence-request", request.turn_request_digest.value]
        )
        ledger_ref = _id("ledger", self._ordinal)
        prefix = digest_of(
            [
                "EVIDENCE_LEDGER_PREFIX@1",
                ledger_ref.value,
                evidence_request_digest.value,
                1,
                None,
                (),
            ]
        )
        authority = EngineeringAgentToolAuthorityReceipt.create(
            authority_kind=EngineeringAgentToolAuthorityKind.SOURCE,
            turn_request_digest=request.turn_request_digest,
            tool_request_digest=request.digest,
            evidence_request_digest=evidence_request_digest,
            repository_revision=REVISION,
            evidence_digest=digest_of(content),
            ledger_ref=ledger_ref.value,
            ledger_generation=1,
            ledger_parent_seal_digest=None,
            ledger_prefix_digest=prefix,
            ledger_entries=(),
            citations=(citation,),
        )
        return EngineeringAgentToolResult.create(
            tool_request_digest=request.digest,
            result_ref=f"result-{self._ordinal}",
            content=content,
            disposition=EngineeringAgentEvidenceDisposition.SUPPORT,
            progress=True,
            citation_refs=(citation.citation_ref,),
            authority_receipt=authority,
        )


class _Model:
    instance_ref = "test-lightweight-model"

    def __init__(self) -> None:
        self.steps = []
        self.reviews = []
        self._calls = 0

    def _receipt(self, role):
        self._calls += 1
        ref = _id("modelcall", self._calls).value
        return EngineeringAgentModelCallReceipt.create(
            model_call_ref=ref,
            gateway_call_ref=ref,
            role=role,
            state=EngineeringAgentModelDispatchState.DISPATCHED_COMPLETED,
        )

    def decide(self, request):
        self.steps.append(request)
        question = request.turn_request.user_message.content
        if not request.observations:
            decision = LightweightAgentDecision(
                goal=question,
                plan="Find the relevant entry before making a conclusion.",
                action=LightweightAgentAction.SEARCH_SOURCE,
                query="Entry",
                read_index=None,
                response_kind=None,
                answer=None,
                citations=(),
            )
        elif request.observations[-1].operation is (
            EngineeringAgentToolOperation.SOURCE_SEARCH
        ):
            decision = LightweightAgentDecision(
                goal=question,
                plan="The search found a candidate; read it to establish behavior.",
                action=LightweightAgentAction.READ_SOURCE,
                query=None,
                read_index=request.read_candidates[-1].read_index,
                response_kind=None,
                answer=None,
                citations=(),
            )
        else:
            decision = LightweightAgentDecision(
                goal=question,
                plan="The full source answers the current request; stop.",
                action=LightweightAgentAction.FINISH,
                query=None,
                read_index=None,
                response_kind=LightweightAgentResponseKind.ANSWER,
                answer=f"针对“{question}”：入口先检查输入，再调用协作者。",
                citations=(
                    LightweightCitationSelection(
                        request.observations[-1].observation_index,
                        1,
                    ),
                ),
            )
        return LightweightDecisionResult(
            decision=decision,
            receipt=self._receipt(EngineeringAgentModelRole.PRIMARY_AGENT),
            disclosure_record_ref=f"disclosure-{self._calls}",
        )

    def review(self, request):
        self.reviews.append(request)
        return LightweightReviewResult(
            review=LightweightReview(
                verdict=LightweightReviewVerdict.APPROVED,
                findings=(),
            ),
            receipt=self._receipt(
                EngineeringAgentModelRole.INDEPENDENT_REVIEWER
            ),
            disclosure_record_ref=f"disclosure-{self._calls}",
        )


class _NeedsMoreEvidenceModel(_Model):
    def decide(self, request):
        self.steps.append(request)
        if not request.observations:
            decision = LightweightAgentDecision(
                goal=request.goal,
                plan="Search once before deciding.",
                action=LightweightAgentAction.SEARCH_SOURCE,
                query="Entry",
                read_index=None,
                response_kind=None,
                answer=None,
                citations=(),
            )
        else:
            decision = LightweightAgentDecision(
                goal=request.goal,
                plan="The tool budget is closed; report the evidence gap.",
                action=LightweightAgentAction.FINISH,
                query=None,
                read_index=None,
                response_kind=LightweightAgentResponseKind.LIMITATION,
                answer="现有证据不足以确认请求中的实现行为。",
                citations=(),
            )
        return LightweightDecisionResult(
            decision=decision,
            receipt=self._receipt(EngineeringAgentModelRole.PRIMARY_AGENT),
            disclosure_record_ref=f"disclosure-{self._calls}",
        )

    def review(self, request):
        self.reviews.append(request)
        return LightweightReviewResult(
            review=LightweightReview(
                verdict=LightweightReviewVerdict.MORE_EVIDENCE,
                findings=("需要读取实现源码才能回答。",),
            ),
            receipt=self._receipt(
                EngineeringAgentModelRole.INDEPENDENT_REVIEWER
            ),
            disclosure_record_ref=f"disclosure-{self._calls}",
        )


class _ImmediateLimitationModel(_Model):
    def decide(self, request):
        self.steps.append(request)
        return LightweightDecisionResult(
            decision=LightweightAgentDecision(
                goal=request.goal,
                plan="Keep this Turn read-only and finish without a claim.",
                action=LightweightAgentAction.FINISH,
                query=None,
                read_index=None,
                response_kind=LightweightAgentResponseKind.LIMITATION,
                answer="当前夹具不形成源码行为结论。",
                citations=(),
            ),
            receipt=self._receipt(EngineeringAgentModelRole.PRIMARY_AGENT),
            disclosure_record_ref=f"disclosure-{self._calls}",
        )


class _CognitionFirstModel(_Model):
    def decide(self, request):
        self.steps.append(request)
        question = request.turn_request.user_message.content
        cognition_operations = [
            item.operation
            for item in request.observations
            if isinstance(item.operation, LightweightAgentAction)
        ]
        source_operations = [
            item.operation
            for item in request.observations
            if isinstance(item.operation, EngineeringAgentToolOperation)
        ]
        common = {
            "goal": question,
            "response_kind": None,
            "answer": None,
            "citations": (),
        }
        if not request.observations:
            decision = LightweightAgentDecision(
                **common,
                plan="Find the entry in reusable cognition first.",
                action=LightweightAgentAction.SEARCH_COGNITION,
                query="CheckoutServiceImpl",
                read_index=None,
                cursor=None,
            )
        elif len(cognition_operations) == 1:
            decision = LightweightAgentDecision(
                **common,
                plan="Traverse the entry's collaborator relation.",
                action=LightweightAgentAction.TRAVERSE_RELATIONS,
                query=None,
                read_index=None,
                cognition_index=request.cognition_candidates[0].cognition_index,
                relation_kind=CognitionRelationKind.IMPLEMENTS,
                direction=CognitionDirection.OUTGOING,
                maximum_depth=1,
                cursor=None,
            )
        elif not source_operations:
            implementation = next(
                item
                for item in request.read_candidates
                if "CheckoutServiceImpl.java" in item.citation.locator
            )
            decision = LightweightAgentDecision(
                **common,
                plan="Use exact Source to cite the cognition-guided conclusion.",
                action=LightweightAgentAction.READ_SOURCE,
                query=None,
                read_index=implementation.read_index,
            )
        else:
            decision = LightweightAgentDecision(
                goal=question,
                plan="Cognition established the path and Source established the behavior.",
                action=LightweightAgentAction.FINISH,
                query=None,
                read_index=None,
                response_kind=LightweightAgentResponseKind.ANSWER,
                answer=(
                    "CheckoutServiceImpl 实现 CheckoutService，"
                    "其 checkout 方法返回输入值。"
                ),
                citations=(
                    LightweightCitationSelection(
                        request.observations[-1].observation_index,
                        1,
                    ),
                ),
            )
        return LightweightDecisionResult(
            decision=decision,
            receipt=self._receipt(EngineeringAgentModelRole.PRIMARY_AGENT),
            disclosure_record_ref=f"disclosure-{self._calls}",
        )


class _CitationBindingModel(_Model):
    """Deterministic fixture for the Application citation-binding boundary."""

    def __init__(self, *, cognition: bool, repeat_invalid: bool = False) -> None:
        super().__init__()
        self.cognition = cognition
        self.repeat_invalid = repeat_invalid
        self.invalid_submissions = 0

    def decide(self, request):
        self.steps.append(request)
        question = request.turn_request.user_message.content
        cognition_observations = [
            item
            for item in request.observations
            if isinstance(item.operation, LightweightAgentAction)
        ]
        source_observations = [
            item
            for item in request.observations
            if item.operation is EngineeringAgentToolOperation.SOURCE_READ
        ]
        common = {
            "goal": question,
            "response_kind": None,
            "answer": None,
            "citations": (),
        }
        if self.cognition and not cognition_observations:
            decision = LightweightAgentDecision(
                **common,
                plan="Establish reusable cognition before reading exact Source.",
                action=LightweightAgentAction.SEARCH_COGNITION,
                query="CheckoutServiceImpl",
                read_index=None,
                cursor=None,
            )
        elif self.cognition and len(cognition_observations) == 1:
            decision = LightweightAgentDecision(
                **common,
                plan="Check the implementation relation in the cognition snapshot.",
                action=LightweightAgentAction.TRAVERSE_RELATIONS,
                query=None,
                read_index=None,
                cognition_index=request.cognition_candidates[0].cognition_index,
                relation_kind=CognitionRelationKind.IMPLEMENTS,
                direction=CognitionDirection.OUTGOING,
                maximum_depth=1,
                cursor=None,
            )
        elif len(source_observations) < (2 if self.cognition else 1):
            # Cognition pages issue at least two distinct Source navigation
            # candidates in this fixture.  A source-only run gets its single
            # candidate from SEARCH_SOURCE.
            if not request.read_candidates:
                decision = LightweightAgentDecision(
                    **common,
                    plan="Locate a source candidate before reading it.",
                    action=LightweightAgentAction.SEARCH_SOURCE,
                    query="Entry",
                    read_index=None,
                )
            else:
                read_index = request.read_candidates[
                    len(source_observations)
                ].read_index
                decision = LightweightAgentDecision(
                    **common,
                    plan="Read the next exact Source candidate.",
                    action=LightweightAgentAction.READ_SOURCE,
                    query=None,
                    read_index=read_index,
                )
        else:
            source_selections = tuple(
                LightweightCitationSelection(item.observation_index, 1)
                for item in source_observations
            )
            if self.invalid_submissions == 0 or self.repeat_invalid:
                self.invalid_submissions += 1
                if self.cognition:
                    cognition_observation = cognition_observations[0]
                    citations = (
                        LightweightCitationSelection(
                            cognition_observation.observation_index,
                            1,
                        ),
                        source_selections[-1],
                    )
                else:
                    citations = (
                        LightweightCitationSelection(
                            source_observations[-1].observation_index,
                            2,
                        ),
                    )
            else:
                citations = source_selections
            decision = LightweightAgentDecision(
                goal=question,
                plan="Answer from the exact Source observations.",
                action=LightweightAgentAction.FINISH,
                query=None,
                read_index=None,
                response_kind=LightweightAgentResponseKind.ANSWER,
                answer="当前 Source 观察支持该实现行为。",
                citations=citations,
            )
        return LightweightDecisionResult(
            decision=decision,
            receipt=self._receipt(EngineeringAgentModelRole.PRIMARY_AGENT),
            disclosure_record_ref=f"disclosure-{self._calls}",
        )


def _shape_failure(model):
    receipt = EngineeringAgentModelCallReceipt.create(
        model_call_ref=_id("modelcall", model._calls + 1).value,
        gateway_call_ref=_id("gateway", model._calls + 1).value,
        role=EngineeringAgentModelRole.PRIMARY_AGENT,
        state=EngineeringAgentModelDispatchState.DISPATCHED_REJECTED,
        failure_kind=EngineeringAgentModelFailureKind.PROVIDER_OUTPUT_INVALID,
        failure_code=ErrorCode.STRUCTURED_OUTPUT_INVALID.value,
    )
    model._calls += 1
    model.rejected_receipts.append(receipt)
    return LightweightModelCallFailure(
        receipt=receipt,
        code=ErrorCode.STRUCTURED_OUTPUT_INVALID,
        message="lightweight Agent decision branches are inconsistent",
        disclosure_record_ref="shape-rejection",
        bounded_replan_allowed=True,
    )


class _ShapeRepairModel(_Model):
    """Emit one typed action-shape rejection, then resume the same loop."""

    def __init__(self) -> None:
        super().__init__()
        self.shape_failures = 0
        self.rejected_receipts = []

    def _shape_failure(self):
        return _shape_failure(self)

    def decide(self, request):
        if self.shape_failures == 0:
            self.steps.append(request)
            self.shape_failures += 1
            raise self._shape_failure()
        return super().decide(request)


class _RewriteThenShapeModel(_ShapeRepairModel):
    """Exercise shape recovery after an independent rewrite finding."""

    def __init__(self) -> None:
        super().__init__()
        self._inject_after_feedback = True

    def decide(self, request):
        if self._inject_after_feedback and request.review_findings:
            self.steps.append(request)
            self.shape_failures += 1
            self._inject_after_feedback = False
            raise self._shape_failure()
        return _Model.decide(self, request)

    def review(self, request):
        self.reviews.append(request)
        if len(self.reviews) == 1:
            verdict = LightweightReviewVerdict.REWRITE
            findings = ("审核要求保留答案中的条件分支。",)
        else:
            verdict = LightweightReviewVerdict.APPROVED
            findings = ()
        return LightweightReviewResult(
            review=LightweightReview(verdict=verdict, findings=findings),
            receipt=self._receipt(EngineeringAgentModelRole.INDEPENDENT_REVIEWER),
            disclosure_record_ref=f"disclosure-{self._calls}",
        )


class _CitationThenShapeModel(_CitationBindingModel):
    """Exercise shape recovery after Application Citation rejection."""

    def __init__(self) -> None:
        super().__init__(cognition=False)
        self.shape_failures = 0
        self.rejected_receipts = []

    def decide(self, request):
        if self.shape_failures == 0 and request.review_findings:
            self.steps.append(request)
            self.shape_failures += 1
            raise _shape_failure(self)
        return super().decide(request)


def _cognition(
    *,
    source_revision: str = REVISION,
    source_tree: str = "c" * 40,
    source_files=SOURCE_FILES,
) -> CapabilityCognitionIndex:
    source = ExactJavaCognitionSource(
        project_name="example",
        source_revision=source_revision,
        source_tree=source_tree,
        selected_roots=("app/src/main/java",),
        modules=(
            JavaCognitionModuleSource(
                module_root="app",
                module_name="app",
                descriptor_path="app/pom.xml",
                descriptor_bytes=b"<project><artifactId>app</artifactId></project>\n",
            ),
        ),
        source_files=source_files,
    )
    return CapabilityCognitionIndex(build_java_capability_cognition(source))


class _EmptyCognitionProjector:
    def project(self, *, request):
        return WorldModelCognitionContext.create(
            request=request,
            scope_ref="lightweight-agent-fixture-scope",
            context_ref="lightweight-agent-fixture-context",
            schema_ref="lightweight-agent-fixture@1",
            snapshot_ids=("lightweight-agent-fixture-snapshot",),
            read_authority_digest=request.world_model_read_authority_digest,
            source_revision=request.repository_revision,
            items=(),
            coverage=("Capability cognition supplies navigation only.",),
        )

class LightweightEngineeringAgentTest(unittest.TestCase):
    def test_cognition_provenance_becomes_brokered_source_read_in_unrelated_repo(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repository = Path(temporary) / "repository"
            repository.mkdir()
            subprocess.run(
                ("git", "-C", str(repository), "init", "-q"), check=True
            )
            subprocess.run(
                (
                    "git",
                    "-C",
                    str(repository),
                    "config",
                    "user.email",
                    "test@example.com",
                ),
                check=True,
            )
            subprocess.run(
                (
                    "git",
                    "-C",
                    str(repository),
                    "config",
                    "user.name",
                    "Test",
                ),
                check=True,
            )
            source_files = dict(SOURCE_FILES)
            for index in range(65):
                path = (
                    "app/src/main/java/com/example/probe/"
                    f"Probe{index:02d}.java"
                )
                source_files[path] = (
                    "package com.example.probe;\n"
                    f"public final class Probe{index:02d} {{}}\n"
                ).encode("utf-8")
            for relative_path, content in source_files.items():
                target = repository / relative_path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(content)
            descriptor = repository / "app/pom.xml"
            descriptor.parent.mkdir(parents=True, exist_ok=True)
            descriptor.write_bytes(
                b"<project><artifactId>app</artifactId></project>\n"
            )
            subprocess.run(
                ("git", "-C", str(repository), "add", "."), check=True
            )
            subprocess.run(
                (
                    "git",
                    "-C",
                    str(repository),
                    "commit",
                    "-q",
                    "-m",
                    "unrelated checkout fixture",
                ),
                check=True,
            )
            revision = subprocess.run(
                ("git", "-C", str(repository), "rev-parse", "HEAD"),
                check=True,
                stdout=subprocess.PIPE,
                text=True,
            ).stdout.strip()
            source_tree = subprocess.run(
                ("git", "-C", str(repository), "rev-parse", "HEAD^{tree}"),
                check=True,
                stdout=subprocess.PIPE,
                text=True,
            ).stdout.strip()

            repository_id = _id("repository", 51)
            binding_id = _id("binding", 52)
            world_authority = digest_of("unrelated-world-model")
            profile = LocalGitEvidenceClassProfile.create(
                profile_ref="unrelated-checkout-source-profile:1",
                binding_id=binding_id,
                evidence_class_paths={
                    EngineeringEvidenceClass.SOURCE: (
                        "app/src/main/java",
                    ),
                    EngineeringEvidenceClass.BUILD_CONFIGURATION: (
                        "app/pom.xml",
                    ),
                },
            )
            configuration = EngineeringAgentEvidenceToolConfiguration.create(
                project_name="unrelated-checkout",
                response_language="zh-CN",
                repository_id=repository_id,
                binding_id=binding_id,
                repository_revision=revision,
                source_profile_ref=profile.profile_ref,
                source_profile_digest=profile.profile_digest,
                world_model_read_authority_digest=world_authority,
                source_allowlist=("app/src/main/java", "app/pom.xml"),
            )
            tool = EngineeringAgentEvidenceToolAdapter(
                configuration=configuration,
                cognition_projector=_EmptyCognitionProjector(),
                source_broker=SourceBroker(source_profile=profile),
                retrieval_worker=LocalGitRetrievalWorker(
                    repository,
                    repository_id=repository_id,
                    binding_id=binding_id,
                    source_profile=profile,
                ),
            )
            cognition = _cognition(
                source_revision=revision,
                source_tree=source_tree,
                source_files=source_files,
            )
            traces = LightweightAgentTraceStore()
            model = _CognitionFirstModel()
            executor = ApplicationOwnedLightweightAgentTurnExecutor(
                model=model,
                tool_port=tool,
                capability_cognition=cognition,
                delivery_control=SealedLightweightDeliveryControl(),
                trace_store=traces,
                attempt_ref="unrelated-checkout-provenance-read",
            )
            binding = EngineeringChatBinding.create(
                product_revision="d" * 40,
                project_name="unrelated-checkout",
                repository_revision=revision,
                world_model_status=RuntimeCapabilityStatus.READY,
                world_model_authority_digest=world_authority,
                source_profile_ref=profile.profile_ref,
                source_access_status=RuntimeCapabilityStatus.READY,
                provider_status=RuntimeCapabilityStatus.READY,
                provider_route_ref="deterministic-test-route@1",
                known_limitations=("fixture",),
            )
            service = InMemoryEngineeringConversationService(
                binding,
                turn_executor=executor,
            )
            conversation = service.create_conversation()

            submission = service.submit_turn(
                conversation_id=conversation.conversation.conversation_id,
                expected_revision=conversation.conversation.revision,
                message="结账实现如何履行接口契约？",
            )

            self.assertEqual(submission.turn.quality_status, "ACCEPTED")
            self.assertEqual(len(submission.turn.citations), 1)
            citation = submission.turn.citations[0]
            self.assertEqual(citation.evidence_class, "SOURCE")
            self.assertEqual(citation.source_revision, revision)
            self.assertIn("CheckoutServiceImpl.java", citation.locator)
            self.assertNotEqual(
                citation.modality,
                "JAVA_CAPABILITY_COGNITION_PROVENANCE_NAVIGATION",
            )
            trace = traces.for_turn(submission.turn.request_digest)[0]
            actions = [
                item["action"]
                for item in trace.events
                if item["kind"] == "MODEL_DECISION"
            ]
            self.assertEqual(
                actions,
                [
                    "SEARCH_COGNITION",
                    "TRAVERSE_RELATIONS",
                    "READ_SOURCE",
                    "FINISH",
                ],
            )
            self.assertNotIn("SEARCH_SOURCE", actions)

            # A cognition page can contain a module descriptor next to Java
            # entities.  The descriptor remains cognition context, while the
            # existing bridge exposes only the Java Source capability.
            module = next(
                entity
                for entity in cognition.snapshot.entities
                if entity.kind is CognitionEntityKind.MODULE
            )
            implementation = next(
                entity
                for entity in cognition.snapshot.entities
                if entity.kind is CognitionEntityKind.TYPE
                and entity.qualified_name
                == "com.example.CheckoutServiceImpl"
            )
            interface_method = next(
                entity
                for entity in cognition.snapshot.entities
                if entity.kind is CognitionEntityKind.METHOD
                and dict(entity.attributes).get("owner_declaration_kind")
                == "INTERFACE"
            )
            module_provenance = module.provenance
            implementation_provenance = implementation.provenance
            mixed_options = tool.cognition_source_read_options(
                model.steps[0].turn_request,
                (module_provenance, implementation_provenance),
            )
            self.assertEqual(len(mixed_options), 1)
            self.assertEqual(
                mixed_options[0].locator,
                implementation_provenance.locator,
            )

            # The live cognition→Source bridge supplies opaque navigation
            # citations.  Capture every field before the Application's
            # ordering projection and prove that neither the broker reference,
            # content digest, citation digest, nor resource identity changes.
            bridged_options = tool.cognition_source_read_options(
                model.steps[0].turn_request,
                (interface_method.provenance, implementation_provenance),
            )
            self.assertEqual(len(bridged_options), 2)
            bridged_candidates = tuple(
                LightweightReadCandidate(
                    read_index=index,
                    citation=citation,
                    resource_locator=(
                        interface_method.provenance.path
                        if citation.locator == interface_method.provenance.locator
                        else implementation_provenance.path
                    ),
                )
                for index, citation in enumerate(bridged_options, 1)
            )
            bridged_before = {
                item.read_index: _citation_identity(item)
                for item in bridged_candidates
            }
            bridged_after = _ordered_read_candidates(
                bridged_candidates,
                (),
                remaining_tool_actions=1,
            )
            self.assertEqual(
                {
                    item.read_index: _citation_identity(item)
                    for item in bridged_after
                },
                bridged_before,
            )
            bridged_reads = []
            bridge_events = []
            bridge_executor = ApplicationOwnedLightweightAgentTurnExecutor(
                model=_ImmediateLimitationModel(),
                tool_port=tool,
                delivery_control=SealedLightweightDeliveryControl(),
                trace_store=LightweightAgentTraceStore(),
                attempt_ref="mixed-cognition-real-bridge",
            )
            bridge_executor._register_cognition_source_read_candidates(
                request=model.steps[0].turn_request,
                cognition=cognition,
                candidates=(
                    LightweightCognitionCandidate(
                        cognition_index=1,
                        entity_id=module.entity_id,
                        kind=module.kind,
                        name=module.name,
                        qualified_name=module.qualified_name,
                        coverage=module.epistemics.coverage.value,
                        unknowns=module.epistemics.unknowns,
                        provenance=module.provenance,
                    ),
                    LightweightCognitionCandidate(
                        cognition_index=2,
                        entity_id=implementation.entity_id,
                        kind=implementation.kind,
                        name=implementation.name,
                        qualified_name=implementation.qualified_name,
                        coverage=implementation.epistemics.coverage.value,
                        unknowns=implementation.epistemics.unknowns,
                        provenance=implementation.provenance,
                    ),
                ),
                read_candidates=bridged_reads,
                events=bridge_events,
                observation_index=1,
            )
            self.assertEqual(
                [item.resource_locator for item in bridged_reads],
                [implementation.provenance.path],
            )
            self.assertEqual(
                bridge_events[0]["skipped_non_source_count"],
                1,
            )
            self.assertEqual(
                bridge_events[0]["skipped_non_source_paths"],
                (module.provenance.path,),
            )
            self.assertEqual(
                bridge_events[0]["skipped_non_source_evidence_kinds"],
                ("MAVEN_MODULE_DESCRIPTOR",),
            )

            # The production adapter keeps one opaque navigation binding per
            # canonical path.  A later cognition page can therefore discover
            # a different entity/detail in the same file.  Reuse that binding
            # without rebinding the immutable candidate; only the internal
            # typed-origin sidecar may become more specific.
            implementation_method = next(
                entity
                for entity in cognition.snapshot.entities
                if entity.kind is CognitionEntityKind.METHOD
                and entity.provenance.path == implementation.provenance.path
                and dict(entity.attributes).get("owner_declaration_kind")
                == "CLASS"
            )

            def candidate_for(entity, index):
                return LightweightCognitionCandidate(
                    cognition_index=index,
                    entity_id=entity.entity_id,
                    kind=entity.kind,
                    name=entity.name,
                    qualified_name=entity.qualified_name,
                    coverage=entity.epistemics.coverage.value,
                    unknowns=entity.epistemics.unknowns,
                    provenance=entity.provenance,
                )

            repeat_tool = EngineeringAgentEvidenceToolAdapter(
                configuration=configuration,
                cognition_projector=_EmptyCognitionProjector(),
                source_broker=SourceBroker(source_profile=profile),
                retrieval_worker=LocalGitRetrievalWorker(
                    repository,
                    repository_id=repository_id,
                    binding_id=binding_id,
                    source_profile=profile,
                ),
            )
            repeat_executor = ApplicationOwnedLightweightAgentTurnExecutor(
                model=_ImmediateLimitationModel(),
                tool_port=repeat_tool,
                delivery_control=SealedLightweightDeliveryControl(),
                trace_store=LightweightAgentTraceStore(),
                attempt_ref="cognition-navigation-repeat-page",
            )
            repeat_reads = []
            repeat_sidecar: dict[
                int, _LightweightReadNavigationMetadata
            ] = {}
            repeat_events: list[dict[str, object]] = []
            repeat_executor._register_cognition_source_read_candidates(
                request=model.steps[0].turn_request,
                cognition=cognition,
                candidates=(candidate_for(implementation, 21),),
                read_candidates=repeat_reads,
                events=repeat_events,
                observation_index=21,
                read_candidate_metadata=repeat_sidecar,
                cognition_metadata={
                    21: _LightweightReadNavigationMetadata(
                        cognition_kind=implementation.kind,
                        cognition_attributes=implementation.attributes,
                        origin_cognition_index=21,
                    )
                },
            )
            self.assertEqual(len(repeat_reads), 1)
            first_identity = _citation_identity(repeat_reads[0])
            first_citation = repeat_reads[0].citation
            self.assertEqual(
                repeat_sidecar[1].cognition_kind,
                CognitionEntityKind.TYPE,
            )
            self.assertNotEqual(
                implementation.provenance.locator,
                implementation_method.provenance.locator,
            )

            # Different cognition entity, same path, and a different exact
            # locator: the second registration must not call the bridge again
            # or collide with the first opaque reference.
            repeat_executor._register_cognition_source_read_candidates(
                request=model.steps[0].turn_request,
                cognition=cognition,
                candidates=(candidate_for(implementation_method, 22),),
                read_candidates=repeat_reads,
                events=repeat_events,
                observation_index=22,
                read_candidate_metadata=repeat_sidecar,
                cognition_metadata={
                    22: _LightweightReadNavigationMetadata(
                        cognition_kind=implementation_method.kind,
                        cognition_attributes=implementation_method.attributes,
                        origin_cognition_index=22,
                    )
                },
            )
            self.assertEqual(len(repeat_reads), 1)
            self.assertEqual(_citation_identity(repeat_reads[0]), first_identity)
            self.assertEqual(repeat_reads[0].citation, first_citation)
            self.assertEqual(
                repeat_sidecar[1].cognition_kind,
                CognitionEntityKind.METHOD,
            )
            self.assertEqual(
                dict(repeat_sidecar[1].cognition_attributes)[
                    "owner_declaration_kind"
                ],
                "CLASS",
            )
            self.assertEqual(
                dict(repeat_sidecar[1].cognition_attributes)["has_body"],
                "true",
            )
            self.assertEqual(
                repeat_tool.cognition_source_read_options(
                    model.steps[0].turn_request,
                    (implementation_method.provenance,),
                ),
                (first_citation,),
            )
            unbound = CognitionProvenance(
                source_revision=revision,
                source_tree=source_tree,
                path="app/not-authorized.xml",
                start_line=1,
                end_line=1,
                content_digest=module_provenance.content_digest,
                evidence_kind=module_provenance.evidence_kind,
            )
            with self.assertRaisesRegex(
                DomainError,
                "AUTHORITY_RECORD_INCONSISTENT.*required evidence path",
            ):
                tool.cognition_source_read_options(
                    model.steps[0].turn_request,
                    (unbound,),
                )

            followup = service.submit_turn(
                conversation_id=submission.snapshot.conversation.conversation_id,
                expected_revision=submission.snapshot.conversation.revision,
                message="追问：同一实现的源码在当前 revision 是否仍一致？",
            )
            self.assertEqual(followup.turn.quality_status, "ACCEPTED")
            second_turn_steps = [
                item
                for item in model.steps
                if item.turn_request.sequence == 2
            ]
            prior_implementation = second_turn_steps[0].read_candidates[0]
            implementation_candidates = tuple(
                item
                for item in second_turn_steps[1].read_candidates
                if "CheckoutServiceImpl.java" in item.resource_locator
            )
            self.assertEqual(implementation_candidates, (prior_implementation,))
            implementation_provenance = next(
                entity.provenance
                for entity in cognition.snapshot.entities
                if entity.kind is CognitionEntityKind.TYPE
                and entity.qualified_name
                == "com.example.CheckoutServiceImpl"
            )
            self.assertEqual(
                tool.cognition_source_read_options(
                    second_turn_steps[0].turn_request,
                    (implementation_provenance,),
                ),
                (),
            )

            cap_model = _ImmediateLimitationModel()
            cap_executor = ApplicationOwnedLightweightAgentTurnExecutor(
                model=cap_model,
                tool_port=tool,
                delivery_control=SealedLightweightDeliveryControl(),
                trace_store=traces,
                attempt_ref="cognition-source-read-capability-fuse",
            )
            cap_service = InMemoryEngineeringConversationService(
                binding,
                turn_executor=cap_executor,
            )
            cap_conversation = cap_service.create_conversation()
            cap_submission = cap_service.submit_turn(
                conversation_id=cap_conversation.conversation.conversation_id,
                expected_revision=cap_conversation.conversation.revision,
                message="只建立当前 Turn，不形成源码行为结论。",
            )
            self.assertEqual(
                cap_submission.turn.quality_status,
                "REVIEWED_LIMITATION",
            )
            cap_request = cap_model.steps[0].turn_request
            probe_provenances = tuple(
                entity.provenance
                for entity in cognition.snapshot.entities
                if entity.kind is CognitionEntityKind.TYPE
                and entity.name.startswith("Probe")
            )
            self.assertEqual(len(probe_provenances), 65)
            self.assertEqual(
                len(
                    tool.cognition_source_read_options(
                        cap_request,
                        probe_provenances[:32],
                    )
                ),
                32,
            )
            self.assertEqual(
                len(
                    tool.cognition_source_read_options(
                        cap_request,
                        probe_provenances[32:64],
                    )
                ),
                32,
            )
            with self.assertRaisesRegex(
                DomainError,
                "BUDGET_EXHAUSTED.*option limit",
            ):
                tool.cognition_source_read_options(
                    cap_request,
                    probe_provenances[64:],
                )

    def test_world_model_mode_uses_cognition_then_source_in_same_agent(self) -> None:
        model = _CognitionFirstModel()
        tool = _SourceTool()
        traces = LightweightAgentTraceStore()
        executor = ApplicationOwnedLightweightAgentTurnExecutor(
            model=model,
            tool_port=tool,
            capability_cognition=_cognition(),
            delivery_control=SealedLightweightDeliveryControl(),
            trace_store=traces,
            attempt_ref="attempt-world-model",
        )
        service = InMemoryEngineeringConversationService(
            _binding(), turn_executor=executor
        )
        snapshot = service.create_conversation()

        submission = service.submit_turn(
            conversation_id=snapshot.conversation.conversation_id,
            expected_revision=snapshot.conversation.revision,
            message="结账服务实现如何履行接口契约？",
        )

        self.assertEqual(submission.turn.quality_status, "ACCEPTED")
        self.assertEqual(len(tool.calls), 1)
        self.assertTrue(model.steps[0].cognition_enabled)
        self.assertTrue(model.steps[1].cognition_candidates)
        trace = traces.for_turn(submission.turn.request_digest)[0]
        self.assertEqual(trace.mode, "WORLD_MODEL_PLUS_SOURCE")
        self.assertEqual(
            [
                item["action"]
                for item in trace.events
                if item["kind"] == "MODEL_DECISION"
            ],
            [
                "SEARCH_COGNITION",
                "TRAVERSE_RELATIONS",
                "READ_SOURCE",
                "FINISH",
            ],
        )
        cognition_events = [
            item for item in trace.events if item["kind"] == "COGNITION_OBSERVATION"
        ]
        self.assertEqual(len(cognition_events), 2)
        self.assertTrue(all(item["snapshot_digest"] for item in cognition_events))
        self.assertGreater(cognition_events[1]["item_count"], 0)
        navigation_events = [
            item
            for item in trace.events
            if item["kind"] == "COGNITION_SOURCE_READ_OPTIONS"
        ]
        self.assertTrue(navigation_events)
        self.assertTrue(
            all(
                not item["cognition_provenance_grants_source_evidence"]
                for item in navigation_events
            )
        )
        self.assertIn(
            "CheckoutServiceImpl.java",
            submission.turn.citations[0].locator,
        )

    def test_budget_pressure_orders_typed_gap_before_broad_hits(self) -> None:
        """Budget pressure changes presentation, never the candidate domain."""

        candidates = (
            _navigation_candidate(
                1,
                resource="module-a/src/Alpha.java",
                locator="module-a/src/Alpha.java:L10-L12",
            ),
            _navigation_candidate(
                2,
                resource="module-a/src/Alpha.java",
                locator="module-a/src/Alpha.java:L20-L24",
            ),
            _navigation_candidate(
                3,
                resource="module-b/src/Beta.java",
                locator="module-b/src/Beta.java:L4-L8",
            ),
            _navigation_candidate(
                4,
                resource="module-c/src/Gamma.java",
                locator="module-c/src/Gamma.java:L3",
                modality="LITERAL_TEXT_SEARCH_HIT",
            ),
            _navigation_candidate(
                5,
                resource="module-d/src/Delta.java",
                locator="module-d/src/Delta.java",
                modality="EXACT_STATIC_SOURCE_TEXT",
            ),
        )
        metadata = {
            1: _LightweightReadNavigationMetadata(
                origin_observation_index=2,
                cognition_kind=CognitionEntityKind.METHOD,
                cognition_attributes=(
                    ("has_body", "false"),
                    ("owner_declaration_kind", "INTERFACE"),
                ),
                origin_cognition_index=10,
            ),
            2: _LightweightReadNavigationMetadata(
                origin_observation_index=2,
                cognition_kind=CognitionEntityKind.METHOD,
                cognition_attributes=(
                    ("has_body", "true"),
                    ("owner_declaration_kind", "CLASS"),
                ),
                origin_cognition_index=11,
            ),
            3: _LightweightReadNavigationMetadata(
                origin_observation_index=2,
                cognition_kind=CognitionEntityKind.TYPE,
                cognition_attributes=(("declaration_kind", "CLASS"),),
                origin_cognition_index=12,
            ),
        }
        high_remaining = _ordered_read_candidates(
            candidates,
            (),
            remaining_tool_actions=4,
            metadata_by_read_index=metadata,
        )
        low_remaining = _ordered_read_candidates(
            candidates,
            (),
            remaining_tool_actions=2,
            metadata_by_read_index=metadata,
        )

        # Four distinct resources can be sampled breadth-first while the
        # larger budget remains.  With only two actions left, the typed
        # declaration/effect pair occupies the deterministic prefix.
        self.assertEqual(
            [item.read_index for item in high_remaining],
            [1, 3, 5, 4, 2],
        )
        self.assertEqual(
            [item.read_index for item in low_remaining],
            [1, 2, 3, 5, 4],
        )
        self.assertNotEqual(high_remaining, low_remaining)
        self.assertEqual(
            sorted(item.read_index for item in high_remaining),
            [1, 2, 3, 4, 5],
        )
        self.assertEqual(
            [item.citation.citation_ref for item in high_remaining],
            [
                candidates[index - 1].citation.citation_ref
                for index in [1, 3, 5, 4, 2]
            ],
        )

        annotation_only = _navigation_candidate(
            6,
            resource="module-e/src/Epsilon.java",
            locator="module-e/src/Epsilon.java:L6",
        )
        annotation_metadata = {
            6: _LightweightReadNavigationMetadata(
                cognition_kind=CognitionEntityKind.METHOD,
                cognition_attributes=(("annotations", "interface-like"),),
                origin_cognition_index=13,
            ),
            2: metadata[2],
        }
        annotation_order = _ordered_read_candidates(
            (annotation_only, candidates[1]),
            (),
            remaining_tool_actions=1,
            metadata_by_read_index=annotation_metadata,
        )
        # An annotation text by itself has no typed owner/body meaning.
        self.assertEqual(
            [item.read_index for item in annotation_order],
            [2, 6],
        )

    def test_read_coverage_matches_navigation_to_source_by_revision_and_resource(
        self,
    ) -> None:
        """A Broker READ closes a navigation resource without sharing refs."""

        navigation_a = _navigation_candidate(
            1,
            resource="module-a/src/Alpha.java",
            locator="module-a/src/Alpha.java:L10-L12",
        )
        full_a = _navigation_candidate(
            2,
            resource="module-a/src/Alpha.java",
            locator="module-a/src/Alpha.java",
            modality="SOURCE_TEXT",
        )
        unread_typed_b = _navigation_candidate(
            3,
            resource="module-b/src/Beta.java",
            locator="module-b/src/Beta.java:L4-L8",
        )
        # The Source Broker's retrieval citation deliberately has a different
        # opaque reference from navigation_a.  Only the exact revision and
        # canonical resource path connect the two observations.
        broker_read = _navigation_candidate(
            99,
            resource="module-a/src/Alpha.java",
            locator="module-a/src/Alpha.java:L1-L80",
            modality="SOURCE_TEXT",
        )
        observations = (_read_navigation_observation(7, broker_read),)
        metadata = {
            1: _LightweightReadNavigationMetadata(
                cognition_kind=CognitionEntityKind.METHOD,
                cognition_attributes=(
                    ("has_body", "true"),
                    ("owner_declaration_kind", "CLASS"),
                ),
                origin_cognition_index=10,
            ),
            3: _LightweightReadNavigationMetadata(
                cognition_kind=CognitionEntityKind.METHOD,
                cognition_attributes=(
                    ("has_body", "false"),
                    ("owner_declaration_kind", "INTERFACE"),
                ),
                origin_cognition_index=11,
            ),
        }
        candidates = (navigation_a, full_a, unread_typed_b)
        before = {
            item.read_index: _citation_identity(item) for item in candidates
        }

        ordered = _ordered_read_candidates(
            candidates,
            observations,
            remaining_tool_actions=1,
            metadata_by_read_index=metadata,
        )

        # The unread typed declaration wins the scarce prefix; the already
        # covered Alpha resource remains visible and keeps its original order
        # identity.  In particular, no navigation ref is rewritten to the
        # Broker retrieval ref.
        self.assertEqual(
            [item.read_index for item in ordered],
            [3, 1, 2],
        )
        after = {
            item.read_index: _citation_identity(item) for item in ordered
        }
        self.assertEqual(after, before)

    def test_run156_sealed_primary_projection_keeps_unread_declarations(self) -> None:
        """Replay q5's model-facing catalog without opaque identity claims."""

        test_path = Path(__file__).resolve()
        database = next(
            (
                root
                / "var/iteration-010/slice-001/run-156-phase-c-loopback/"
                / "ark-gateway.sqlite3"
                for root in (test_path.parents[1], test_path.parents[4])
                if (
                    root
                    / "var/iteration-010/slice-001/run-156-phase-c-loopback/"
                    / "ark-gateway.sqlite3"
                ).exists()
            ),
            test_path.parents[1]
            / "var/iteration-010/slice-001/run-156-phase-c-loopback/"
            / "ark-gateway.sqlite3",
        )
        if not database.exists():
            status = _replay_evidence_status(
                "NOT_RUN",
                "run156_model_facing_projection",
                "run-156 sealed gateway evidence is not present",
                artifact=str(database),
            )
            _emit_replay_evidence_status(status)
            self.assertEqual(status["status"], "NOT_RUN")
            return
        with sqlite3.connect(database) as connection:
            payloads = connection.execute(
                """
                SELECT content
                FROM ai_model_call_manifest_items
                WHERE schema_ref = 'json-object@1'
                ORDER BY rowid
                """
            ).fetchall()
        sealed = None
        for (content,) in payloads:
            try:
                candidate_payload = json.loads(content)
            except (TypeError, json.JSONDecodeError):
                continue
            if not isinstance(candidate_payload, dict):
                continue
            entries = candidate_payload.get("read_candidates")
            if (
                candidate_payload.get("tools_enabled") is False
                and isinstance(entries, list)
                and len(entries) >= 22
            ):
                sealed = candidate_payload
        if sealed is None:
            status = _replay_evidence_status(
                "NOT_RUN",
                "run156_model_facing_projection",
                "sealed q5 Primary payload was not found",
                artifact=str(database),
            )
            _emit_replay_evidence_status(status)
            self.assertEqual(status["status"], "NOT_RUN")
            return

        # The sealed Gateway payload intentionally contains only the existing
        # model-facing fields.  The opaque citation values below are local
        # placeholders solely to exercise ordering/projection shape; raw
        # identity preservation is tested separately against the live bridge
        # and is explicitly NOT_RUN for this historical artifact (see the
        # companion test below).
        raw_entries = sealed["read_candidates"]
        source_revision = raw_entries[0]["source_revision"]
        candidates = tuple(
            _navigation_candidate(
                item["read_index"],
                resource=(
                    item["locator"].rsplit(":L", 1)[0]
                    if ":L" in item["locator"]
                    else item["locator"]
                ),
                locator=item["locator"],
                modality=item["modality"],
                source_revision=source_revision,
            )
            for item in raw_entries
        )
        by_index = {item.read_index: item for item in candidates}
        # The sealed q5 cognition page established these typed roles by
        # authority-owned provenance.  The model-facing payload intentionally
        # omits the attributes; this sidecar restores only the internal rank.
        metadata = {
            index: _LightweightReadNavigationMetadata(
                origin_observation_index=2,
                cognition_kind=CognitionEntityKind.METHOD,
                cognition_attributes=attributes,
                origin_cognition_index=index,
            )
            for index, attributes in {
                4: (("has_body", "true"), ("owner_declaration_kind", "CLASS")),
                5: (("has_body", "true"), ("owner_declaration_kind", "CLASS")),
                6: (("has_body", "false"), ("owner_declaration_kind", "INTERFACE")),
                20: (("has_body", "true"), ("owner_declaration_kind", "CLASS")),
            }.items()
            if index in by_index
        }
        observations = tuple(
            _read_navigation_observation(position, by_index[index])
            for position, index in enumerate((4, 5, 13, 18), 1)
            if index in by_index
        )
        before_views = {
            item.read_index: item.model_view() for item in candidates
        }
        ordered = _ordered_read_candidates(
            candidates,
            observations,
            remaining_tool_actions=2,
            metadata_by_read_index=metadata,
        )
        ordered_indexes = [item.read_index for item in ordered]
        self.assertEqual(len(ordered_indexes), len(raw_entries))
        self.assertEqual(sorted(ordered_indexes), sorted(by_index))
        self.assertIn(6, ordered_indexes)
        self.assertEqual(ordered_indexes[0], 6)
        # The interface declaration is unread and therefore precedes the
        # already-read controller/service effect options while all siblings
        # remain visible for an explicit model choice.
        self.assertLess(ordered_indexes.index(6), ordered_indexes.index(4))
        self.assertLess(ordered_indexes.index(6), ordered_indexes.index(5))
        for item in ordered:
            self.assertEqual(item.model_view(), before_views[item.read_index])
        status = _replay_evidence_status(
            "EXECUTED",
            "run156_model_facing_projection",
            "sealed model-facing catalog projection assertions passed",
            artifact=str(database),
            candidate_count=len(ordered_indexes),
        )
        _emit_replay_evidence_status(status)
        self.assertEqual(status["status"], "EXECUTED")

    def test_run156_raw_citation_identity_replay_is_explicitly_not_run(
        self,
    ) -> None:
        """Do not claim opaque identity from a model-facing sealed payload."""

        test_path = Path(__file__).resolve()
        database = next(
            (
                root
                / "var/iteration-010/slice-001/run-156-phase-c-loopback/"
                / "ark-gateway.sqlite3"
                for root in (test_path.parents[1], test_path.parents[4])
                if (
                    root
                    / "var/iteration-010/slice-001/run-156-phase-c-loopback/"
                    / "ark-gateway.sqlite3"
                ).exists()
            ),
            test_path.parents[1]
            / "var/iteration-010/slice-001/run-156-phase-c-loopback/"
            / "ark-gateway.sqlite3",
        )
        if not database.exists():
            status = _replay_evidence_status(
                "NOT_RUN",
                "run156_raw_citation_identity",
                "run-156 artifact is unavailable for raw citation replay",
                artifact=str(database),
            )
            _emit_replay_evidence_status(status)
            self.assertEqual(status["status"], "NOT_RUN")
            return
        with sqlite3.connect(database) as connection:
            payloads = connection.execute(
                """
                SELECT content
                FROM ai_model_call_manifest_items
                WHERE schema_ref = 'json-object@1'
                ORDER BY rowid
                """
            ).fetchall()
        sealed = None
        for (content,) in payloads:
            try:
                candidate_payload = json.loads(content)
            except (TypeError, json.JSONDecodeError):
                continue
            if not isinstance(candidate_payload, dict):
                continue
            entries = candidate_payload.get("read_candidates")
            if (
                candidate_payload.get("tools_enabled") is False
                and isinstance(entries, list)
                and len(entries) >= 22
            ):
                sealed = candidate_payload
        if sealed is None:
            status = _replay_evidence_status(
                "NOT_RUN",
                "run156_raw_citation_identity",
                "sealed q5 payload is unavailable",
                artifact=str(database),
            )
            _emit_replay_evidence_status(status)
            self.assertEqual(status["status"], "NOT_RUN")
            return

        entries = sealed["read_candidates"]
        missing = [
            item.get("read_index")
            for item in entries
            if not isinstance(item, dict)
            or not {
                "citation_ref",
                "content_digest",
                "digest",
                "resource_locator",
            }.issubset(item)
        ]
        if missing:
            status = _replay_evidence_status(
                "NOT_RUN",
                "run156_raw_citation_identity",
                "sealed q5 model-facing entries omit opaque citation identity; "
                "no authority receipt is stored in this artifact",
                artifact=str(database),
                missing_read_indexes=missing,
            )
            _emit_replay_evidence_status(status)
            self.assertEqual(status["status"], "NOT_RUN")
            return

        # If a future sealed artifact carries complete authority receipts, the
        # replay must use those raw values and compare the complete identity
        # tuple before/after ordering.  This branch deliberately does not
        # synthesize a citation or digest when the current artifact lacks one.
        candidates = tuple(
            LightweightReadCandidate(
                read_index=item["read_index"],
                citation=EngineeringAgentCitation.create(
                    citation_ref=item["citation_ref"],
                    evidence_class=item["evidence_class"],
                    source_revision=item["source_revision"],
                    locator=item["locator"],
                    modality=item["modality"],
                    content_digest=Digest(item["content_digest"]),
                ),
                resource_locator=item["resource_locator"],
            )
            for item in entries
        )
        for item in entries:
            self.assertEqual(
                next(
                    candidate
                    for candidate in candidates
                    if candidate.read_index == item["read_index"]
                ).citation.digest.value,
                item["digest"],
            )
        before = {
            item.read_index: _citation_identity(item) for item in candidates
        }
        ordered = _ordered_read_candidates(
            candidates,
            (),
            remaining_tool_actions=2,
        )
        self.assertEqual(
            {item.read_index: _citation_identity(item) for item in ordered},
            before,
        )
        status = _replay_evidence_status(
            "EXECUTED",
            "run156_raw_citation_identity",
            "sealed authority receipts carried complete citation identity",
            artifact=str(database),
            candidate_count=len(candidates),
        )
        _emit_replay_evidence_status(status)
        self.assertEqual(status["status"], "EXECUTED")

    def test_source_first_cognition_adds_sidecar_without_rebinding_candidate(self) -> None:
        cognition = _cognition()
        model = _ImmediateLimitationModel()
        tool = _SourceTool()
        executor = ApplicationOwnedLightweightAgentTurnExecutor(
            model=model,
            tool_port=tool,
            capability_cognition=cognition,
            delivery_control=SealedLightweightDeliveryControl(),
            trace_store=LightweightAgentTraceStore(),
            attempt_ref="source-first-cognition-sidecar",
        )
        service = InMemoryEngineeringConversationService(
            _binding(), turn_executor=executor
        )
        conversation = service.create_conversation()
        submission = service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=conversation.conversation.revision,
            message="建立一个只读的通用导航夹具。",
        )
        request = model.steps[0].turn_request

        interface_entity = next(
            item
            for item in cognition.snapshot.entities
            if item.kind is CognitionEntityKind.METHOD
            and dict(item.attributes).get("owner_declaration_kind")
            == "INTERFACE"
        )
        implementation_entity = next(
            item
            for item in cognition.snapshot.entities
            if item.kind is CognitionEntityKind.METHOD
            and dict(item.attributes).get("owner_declaration_kind")
            == "CLASS"
            and dict(item.attributes).get("has_body") == "true"
        )
        existing = [
            _navigation_candidate(
                1,
                resource=interface_entity.provenance.path,
                locator=interface_entity.provenance.locator,
                modality="SOURCE_TEXT",
            ),
            _navigation_candidate(
                2,
                resource=implementation_entity.provenance.path,
                locator=implementation_entity.provenance.locator,
                modality="SOURCE_TEXT",
            ),
            # Same file as the implementation, but a different line range;
            # it must not inherit that method's typed role.
            _navigation_candidate(
                3,
                resource=implementation_entity.provenance.path,
                locator=f"{implementation_entity.provenance.path}:L1",
                modality="LITERAL_TEXT_SEARCH_HIT",
            ),
        ]
        before = tuple(existing)
        sidecar = {
            item.read_index: _LightweightReadNavigationMetadata(
                origin_observation_index=7
            )
            for item in existing
        }
        cognition_candidates = (
            LightweightCognitionCandidate(
                cognition_index=10,
                entity_id=interface_entity.entity_id,
                kind=interface_entity.kind,
                name=interface_entity.name,
                qualified_name=interface_entity.qualified_name,
                coverage=interface_entity.epistemics.coverage.value,
                unknowns=interface_entity.epistemics.unknowns,
                provenance=interface_entity.provenance,
            ),
            LightweightCognitionCandidate(
                cognition_index=11,
                entity_id=implementation_entity.entity_id,
                kind=implementation_entity.kind,
                name=implementation_entity.name,
                qualified_name=implementation_entity.qualified_name,
                coverage=implementation_entity.epistemics.coverage.value,
                unknowns=implementation_entity.epistemics.unknowns,
                provenance=implementation_entity.provenance,
            ),
        )
        cognition_metadata = {
            10: _LightweightReadNavigationMetadata(
                cognition_kind=interface_entity.kind,
                cognition_attributes=interface_entity.attributes,
                origin_cognition_index=10,
            ),
            11: _LightweightReadNavigationMetadata(
                cognition_kind=implementation_entity.kind,
                cognition_attributes=implementation_entity.attributes,
                origin_cognition_index=11,
            ),
        }
        events: list[dict[str, object]] = []
        executor._register_cognition_source_read_candidates(
            request=request,
            cognition=cognition,
            candidates=cognition_candidates,
            read_candidates=existing,
            events=events,
            observation_index=9,
            read_candidate_metadata=sidecar,
            cognition_metadata=cognition_metadata,
        )

        self.assertEqual(submission.turn.quality_status, "REVIEWED_LIMITATION")
        self.assertEqual(existing[:3], list(before))
        self.assertEqual(
            [item.read_index for item in existing],
            [1, 2, 3, 4, 5],
        )
        self.assertEqual(
            [item.citation.citation_ref for item in existing],
            [item.citation.citation_ref for item in before]
            + [item.citation.citation_ref for item in existing[3:]],
        )
        self.assertEqual(
            sidecar[1].cognition_kind,
            CognitionEntityKind.METHOD,
        )
        self.assertEqual(
            dict(sidecar[1].cognition_attributes)["owner_declaration_kind"],
            "INTERFACE",
        )
        self.assertEqual(
            dict(sidecar[2].cognition_attributes)["owner_declaration_kind"],
            "CLASS",
        )
        self.assertIsNone(sidecar[3].cognition_kind)
        self.assertEqual(
            sidecar[4].cognition_kind,
            CognitionEntityKind.METHOD,
        )
        self.assertEqual(
            sidecar[5].cognition_kind,
            CognitionEntityKind.METHOD,
        )
        self.assertEqual(
            [item.read_index for item in _ordered_read_candidates(
                tuple(existing),
                (),
                remaining_tool_actions=1,
                metadata_by_read_index=sidecar,
            )],
            [1, 4, 2, 5, 3],
        )
        projected_request = LightweightAgentStepRequest(
            turn_request=request,
            step=2,
            goal="保留现有候选并按当前预算排序。",
            plan="使用受信候选完成一次受控读取。",
            observations=(),
            read_candidates=tuple(existing),
            tools_enabled=True,
            remaining_tool_actions=1,
            read_candidate_metadata=tuple(sorted(sidecar.items())),
        )
        projected_view = projected_request.model_view()
        self.assertNotIn("remaining_tool_actions", projected_view)
        self.assertNotIn("read_candidate_metadata", projected_view)
        self.assertEqual(
            [item["read_index"] for item in projected_view["read_candidates"]],
            [1, 4, 2, 5, 3],
        )
        self.assertTrue(all(set(item.model_view()) == {
            "read_index",
            "locator",
            "modality",
            "source_revision",
        } for item in existing))

        # A same-file line/literal hit is not a full-resource read.  Cognition
        # must therefore receive a new exact declaration capability rather
        # than silently inheriting the unrelated hit's path/ref.
        line_only = [existing[2]]
        line_sidecar: dict[int, _LightweightReadNavigationMetadata] = {}
        line_events: list[dict[str, object]] = []
        executor._register_cognition_source_read_candidates(
            request=request,
            cognition=cognition,
            candidates=(cognition_candidates[1],),
            read_candidates=line_only,
            events=line_events,
            observation_index=10,
            read_candidate_metadata=line_sidecar,
            cognition_metadata={11: cognition_metadata[11]},
        )
        self.assertEqual(len(line_only), 2)
        self.assertEqual(
            line_only[1].citation.locator,
            implementation_entity.provenance.locator,
        )
        self.assertNotEqual(
            line_only[1].citation.citation_ref,
            line_only[0].citation.citation_ref,
        )
        self.assertEqual(line_only[1].resource_locator, implementation_entity.provenance.path)
        self.assertEqual(
            _citation_identity(line_only[0]),
            _citation_identity(existing[2]),
        )

        # Conversely, an already delivered line-free full Source candidate
        # legitimately suppresses a second cognition origin for that path.
        full_only = [
            _navigation_candidate(
                20,
                resource=implementation_entity.provenance.path,
                locator=implementation_entity.provenance.path,
                modality="SOURCE_TEXT",
            )
        ]
        full_events: list[dict[str, object]] = []
        executor._register_cognition_source_read_candidates(
            request=request,
            cognition=cognition,
            candidates=(cognition_candidates[1],),
            read_candidates=full_only,
            events=full_events,
            observation_index=11,
            read_candidate_metadata={},
            cognition_metadata={11: cognition_metadata[11]},
        )
        self.assertEqual(len(full_only), 1)
        self.assertEqual(
            full_only[0].resource_locator,
            implementation_entity.provenance.path,
        )

    def test_two_questions_and_followup_replan_from_source_observations(self) -> None:
        binding = _binding()
        model = _Model()
        tool = _SourceTool()
        traces = LightweightAgentTraceStore()
        executor = ApplicationOwnedLightweightAgentTurnExecutor(
            model=model,
            tool_port=tool,
            delivery_control=SealedLightweightDeliveryControl(),
            trace_store=traces,
            attempt_ref="attempt-test",
        )
        service = InMemoryEngineeringConversationService(
            binding, turn_executor=executor
        )
        snapshot = service.create_conversation()
        questions = (
            "入口如何处理输入？",
            "失败路径会继续调用协作者吗？",
            "结合前两轮，调用发生在检查之前还是之后？",
        )
        submissions = []
        for question in questions:
            submission = service.submit_turn(
                conversation_id=snapshot.conversation.conversation_id,
                expected_revision=snapshot.conversation.revision,
                message=question,
            )
            submissions.append(submission)
            snapshot = submission.snapshot

        self.assertEqual(len(tool.calls), 6)
        self.assertEqual(len(model.reviews), 3)
        self.assertTrue(all(item.turn.citations for item in submissions))
        self.assertEqual(snapshot.conversation.revision, Revision(4))
        self.assertEqual(snapshot.context.work_state_revision, Revision(3))
        for submission in submissions:
            trajectories = traces.for_turn(submission.turn.request_digest)
            self.assertEqual(len(trajectories), 1)
            trace = trajectories[0]
            self.assertEqual(trace.terminal_status, "SUCCEEDED")
            actions = [
                item["action"]
                for item in trace.events
                if item["kind"] == "MODEL_DECISION"
            ]
            self.assertEqual(
                actions, ["SEARCH_SOURCE", "READ_SOURCE", "FINISH"]
            )
            decisions = [
                item
                for item in trace.events
                if item["kind"] == "MODEL_DECISION"
            ]
            self.assertEqual(decisions[0]["query"], "Entry")
            self.assertIsNone(decisions[0]["read_index"])
            self.assertIsNone(decisions[1]["query"])
            self.assertIsInstance(decisions[1]["read_index"], int)
            self.assertIsNone(decisions[2]["query"])
            self.assertIsNone(decisions[2]["read_index"])
            plans = [
                item["plan"]
                for item in trace.events
                if item["kind"] == "MODEL_DECISION"
            ]
            self.assertEqual(len(set(plans)), 3)

    def test_more_evidence_after_tool_fuse_fails_without_repeated_reviews(self) -> None:
        model = _NeedsMoreEvidenceModel()
        traces = LightweightAgentTraceStore()
        executor = ApplicationOwnedLightweightAgentTurnExecutor(
            model=model,
            tool_port=_SourceTool(),
            delivery_control=SealedLightweightDeliveryControl(),
            trace_store=traces,
            attempt_ref="attempt-tool-fuse",
            limits=EngineeringAgentLoopLimits(
                maximum_agent_steps=11,
                maximum_tool_actions=1,
                maximum_reviews=4,
            ),
        )
        service = InMemoryEngineeringConversationService(
            _binding(), turn_executor=executor
        )
        snapshot = service.create_conversation()

        submission = service.submit_turn(
            conversation_id=snapshot.conversation.conversation_id,
            expected_revision=snapshot.conversation.revision,
            message="实现失败时会发生什么？",
        )

        self.assertEqual(submission.turn.failure_code, "BUDGET_EXHAUSTED")
        self.assertEqual(submission.turn.provider_dispatch_count, 3)
        self.assertEqual(len(model.steps), 2)
        self.assertEqual(len(model.reviews), 1)
        trace = traces.for_turn(submission.turn.request_digest)[0]
        self.assertEqual(trace.terminal_status, "FAILED")
        self.assertEqual(
            [item["kind"] for item in trace.events].count(
                "INDEPENDENT_REVIEW"
            ),
            1,
        )

    def test_action_shape_rejection_replans_once_without_dropping_receipt(self) -> None:
        model = _ShapeRepairModel()
        traces = LightweightAgentTraceStore()
        executor = ApplicationOwnedLightweightAgentTurnExecutor(
            model=model,
            tool_port=_SourceTool(),
            delivery_control=SealedLightweightDeliveryControl(),
            trace_store=traces,
            attempt_ref="attempt-action-shape-repair",
        )
        service = InMemoryEngineeringConversationService(
            _binding(), turn_executor=executor
        )
        conversation = service.create_conversation()

        submission = service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=conversation.conversation.revision,
            message="入口如何处理输入？",
        )

        self.assertEqual(submission.turn.quality_status, "ACCEPTED")
        self.assertEqual(submission.turn.provider_dispatch_count, 5)
        self.assertEqual(submission.turn.retry_count, 0)
        self.assertEqual(len(submission.turn.model_dispatch_receipt_refs), 5)
        self.assertEqual(
            submission.turn.model_dispatch_receipt_refs[0],
            model.rejected_receipts[0].digest.value,
        )
        self.assertIs(
            model.rejected_receipts[0].state,
            EngineeringAgentModelDispatchState.DISPATCHED_REJECTED,
        )
        self.assertIs(
            model.rejected_receipts[0].failure_kind,
            EngineeringAgentModelFailureKind.PROVIDER_OUTPUT_INVALID,
        )
        self.assertEqual(len(model.reviews), 1)
        self.assertEqual(model.shape_failures, 1)
        self.assertEqual(
            model.steps[1].review_findings,
            (
                "Application rejected the previous Agent decision because fields "
                "unused by its selected action were not null. Replan with the same "
                "observations and set every field not used by the selected action "
                "to null; do not alter evidence or answer semantics.",
            ),
        )
        trace = traces.for_turn(submission.turn.request_digest)[0]
        shape_events = [
            item
            for item in trace.events
            if item["kind"] == "MODEL_DECISION_SHAPE_REJECTION"
        ]
        self.assertEqual(len(shape_events), 1)
        self.assertEqual(shape_events[0]["repair_ordinal"], 1)
        self.assertEqual(
            [
                item["action"]
                for item in trace.events
                if item["kind"] == "MODEL_DECISION"
            ],
            ["SEARCH_SOURCE", "READ_SOURCE", "FINISH"],
        )

    def test_second_action_shape_rejection_remains_fail_closed(self) -> None:
        class RepeatShapeFailureModel(_ShapeRepairModel):
            def decide(self, request):
                self.steps.append(request)
                self.shape_failures += 1
                raise self._shape_failure()

        model = RepeatShapeFailureModel()
        traces = LightweightAgentTraceStore()
        executor = ApplicationOwnedLightweightAgentTurnExecutor(
            model=model,
            tool_port=_SourceTool(),
            delivery_control=SealedLightweightDeliveryControl(),
            trace_store=traces,
            attempt_ref="attempt-action-shape-second-rejection",
        )
        service = InMemoryEngineeringConversationService(
            _binding(), turn_executor=executor
        )
        conversation = service.create_conversation()
        submission = service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=conversation.conversation.revision,
            message="入口如何处理输入？",
        )

        self.assertEqual(submission.turn.quality_status, "NOT_ACCEPTED")
        self.assertEqual(
            submission.turn.failure_code, "STRUCTURED_OUTPUT_INVALID"
        )
        trace = traces.for_turn(submission.turn.request_digest)[0]
        self.assertEqual(
            [item["kind"] for item in trace.events].count(
                "MODEL_DECISION_SHAPE_REJECTION"
            ),
            1,
        )

    def test_action_shape_repair_merges_prior_reviewer_feedback(self) -> None:
        model = _RewriteThenShapeModel()
        traces = LightweightAgentTraceStore()
        executor = ApplicationOwnedLightweightAgentTurnExecutor(
            model=model,
            tool_port=_SourceTool(),
            delivery_control=SealedLightweightDeliveryControl(),
            trace_store=traces,
            attempt_ref="attempt-action-shape-after-review",
        )
        service = InMemoryEngineeringConversationService(
            _binding(), turn_executor=executor
        )
        conversation = service.create_conversation()
        submission = service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=conversation.conversation.revision,
            message="入口如何处理输入？",
        )

        self.assertEqual(submission.turn.quality_status, "ACCEPTED")
        self.assertEqual(submission.turn.provider_dispatch_count, 7)
        feedback_requests = [
            item for item in model.steps if item.review_findings
        ]
        self.assertEqual(len(feedback_requests), 2)
        rejected_answer = feedback_requests[0].rejected_answer
        self.assertTrue(rejected_answer)
        self.assertEqual(
            feedback_requests[0].review_findings,
            ("审核要求保留答案中的条件分支。",),
        )
        self.assertEqual(feedback_requests[1].rejected_answer, rejected_answer)
        self.assertEqual(
            feedback_requests[1].review_findings[0],
            "审核要求保留答案中的条件分支。",
        )
        self.assertIn(
            "fields unused by its selected action",
            feedback_requests[1].review_findings[-1],
        )
        trace = traces.for_turn(submission.turn.request_digest)[0]
        self.assertEqual(
            [item["kind"] for item in trace.events].count(
                "MODEL_DECISION_SHAPE_REJECTION"
            ),
            1,
        )

    def test_action_shape_repair_merges_prior_citation_feedback(self) -> None:
        model = _CitationThenShapeModel()
        traces = LightweightAgentTraceStore()
        executor = ApplicationOwnedLightweightAgentTurnExecutor(
            model=model,
            tool_port=_SourceTool(),
            delivery_control=SealedLightweightDeliveryControl(),
            trace_store=traces,
            attempt_ref="attempt-action-shape-after-citation",
        )
        service = InMemoryEngineeringConversationService(
            _binding(), turn_executor=executor
        )
        conversation = service.create_conversation()
        submission = service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=conversation.conversation.revision,
            message="入口如何处理输入？",
        )

        self.assertEqual(submission.turn.quality_status, "ACCEPTED")
        self.assertEqual(submission.turn.provider_dispatch_count, 6)
        feedback_requests = [
            item for item in model.steps if item.review_findings
        ]
        self.assertEqual(len(feedback_requests), 2)
        rejected_answer = feedback_requests[0].rejected_answer
        self.assertTrue(rejected_answer)
        self.assertIn(
            "citation selection",
            feedback_requests[0].review_findings[0],
        )
        self.assertEqual(feedback_requests[1].rejected_answer, rejected_answer)
        self.assertIn(
            "citation selection",
            feedback_requests[1].review_findings[0],
        )
        self.assertIn(
            "fields unused by its selected action",
            feedback_requests[1].review_findings[-1],
        )
        trace = traces.for_turn(submission.turn.request_digest)[0]
        kinds = [item["kind"] for item in trace.events]
        self.assertIn("CITATION_BINDING_REJECTION", kinds)
        self.assertIn("MODEL_DECISION_SHAPE_REJECTION", kinds)

    def test_citation_binding_replans_after_cognition_and_multiple_source_reads(
        self,
    ) -> None:
        model = _CitationBindingModel(cognition=True)
        tool = _SourceTool()
        traces = LightweightAgentTraceStore()
        executor = ApplicationOwnedLightweightAgentTurnExecutor(
            model=model,
            tool_port=tool,
            capability_cognition=_cognition(),
            delivery_control=SealedLightweightDeliveryControl(),
            trace_store=traces,
            attempt_ref="attempt-citation-binding-cognition",
        )
        service = InMemoryEngineeringConversationService(
            _binding(), turn_executor=executor
        )
        conversation = service.create_conversation()

        submission = service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=conversation.conversation.revision,
            message="实现如何履行接口契约？",
        )

        self.assertEqual(submission.turn.quality_status, "ACCEPTED")
        self.assertEqual(len(submission.turn.citations), 2)
        self.assertEqual(len(model.reviews), 1)
        self.assertEqual(model.invalid_submissions, 1)
        self.assertEqual(
            model.steps[-1].review_findings,
            (
                "Application rejected the previous FINISH citation selection at "
                "observation index 1, citation index 1; the selected observation "
                "has 0 delivered Citation(s). Replan and submit FINISH using only "
                "observation/citation pairs present in the current observations; "
                "do not invent evidence or alter the observations.",
            ),
        )
        trace = traces.for_turn(submission.turn.request_digest)[0]
        rejection_events = [
            item
            for item in trace.events
            if item["kind"] == "CITATION_BINDING_REJECTION"
        ]
        self.assertEqual(
            rejection_events,
            [
                {
                    "kind": "CITATION_BINDING_REJECTION",
                    "step": 5,
                    "observation_index": 1,
                    "citation_index": 1,
                    "available_citation_count": 0,
                    "selected_pairs": (
                        {"observation_index": 1, "citation_index": 1},
                        {"observation_index": 4, "citation_index": 1},
                    ),
                    "repair_ordinal": 1,
                }
            ],
        )
        self.assertEqual(
            [
                item["action"]
                for item in trace.events
                if item["kind"] == "MODEL_DECISION"
            ],
            [
                "SEARCH_COGNITION",
                "TRAVERSE_RELATIONS",
                "READ_SOURCE",
                "READ_SOURCE",
                "FINISH",
                "FINISH",
            ],
        )
        self.assertEqual(
            [item["kind"] for item in trace.events].count(
                "INDEPENDENT_REVIEW"
            ),
            1,
        )
        self.assertEqual(
            trace.digest,
            digest_of(
                {
                    "schema": "SWM-LIGHTWEIGHT-AGENT-TRAJECTORY@1",
                    "attempt_ref": "attempt-citation-binding-cognition",
                    "turn_request_digest": submission.turn.request_digest.value,
                    "mode": "WORLD_MODEL_PLUS_SOURCE",
                    "events": tuple(trace.events),
                    "terminal_status": "SUCCEEDED",
                }
            ),
        )

    def test_source_only_out_of_range_citation_replans_once(self) -> None:
        model = _CitationBindingModel(cognition=False)
        traces = LightweightAgentTraceStore()
        executor = ApplicationOwnedLightweightAgentTurnExecutor(
            model=model,
            tool_port=_SourceTool(),
            delivery_control=SealedLightweightDeliveryControl(),
            trace_store=traces,
            attempt_ref="attempt-citation-binding-source-only",
        )
        service = InMemoryEngineeringConversationService(
            _binding(), turn_executor=executor
        )
        conversation = service.create_conversation()

        submission = service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=conversation.conversation.revision,
            message="入口如何处理输入？",
        )

        self.assertEqual(submission.turn.quality_status, "ACCEPTED")
        self.assertEqual(len(model.reviews), 1)
        trace = traces.for_turn(submission.turn.request_digest)[0]
        self.assertEqual(
            [
                item["kind"]
                for item in trace.events
                if item["kind"] == "CITATION_BINDING_REJECTION"
            ],
            ["CITATION_BINDING_REJECTION"],
        )
        rejection = next(
            item
            for item in trace.events
            if item["kind"] == "CITATION_BINDING_REJECTION"
        )
        self.assertEqual(rejection["observation_index"], 2)
        self.assertEqual(rejection["citation_index"], 2)
        self.assertEqual(rejection["available_citation_count"], 1)
        self.assertEqual(rejection["repair_ordinal"], 1)
        self.assertEqual(
            [
                item["action"]
                for item in trace.events
                if item["kind"] == "MODEL_DECISION"
            ],
            ["SEARCH_SOURCE", "READ_SOURCE", "FINISH", "FINISH"],
        )

    def test_second_invalid_citation_selection_remains_fail_closed(self) -> None:
        model = _CitationBindingModel(cognition=False, repeat_invalid=True)
        traces = LightweightAgentTraceStore()
        executor = ApplicationOwnedLightweightAgentTurnExecutor(
            model=model,
            tool_port=_SourceTool(),
            delivery_control=SealedLightweightDeliveryControl(),
            trace_store=traces,
            attempt_ref="attempt-citation-binding-second-invalid",
        )
        service = InMemoryEngineeringConversationService(
            _binding(), turn_executor=executor
        )
        conversation = service.create_conversation()

        submission = service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=conversation.conversation.revision,
            message="入口如何处理输入？",
        )

        self.assertEqual(submission.turn.quality_status, "NOT_ACCEPTED")
        self.assertEqual(submission.turn.failure_code, "CONTROL_STATE_DENIED")
        self.assertEqual(len(model.reviews), 0)
        trace = traces.for_turn(submission.turn.request_digest)[0]
        self.assertEqual(
            [item["kind"] for item in trace.events].count(
                "CITATION_BINDING_REJECTION"
            ),
            1,
        )
        self.assertEqual(
            [item["kind"] for item in trace.events].count(
                "INDEPENDENT_REVIEW"
            ),
            0,
        )


if __name__ == "__main__":
    unittest.main()
