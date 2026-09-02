from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from software_world_model.application_services.conversational_engineering_agent import (
    EngineeringAgentCitation,
    EngineeringAgentEvidenceDisposition,
    EngineeringAgentLoopLimits,
    EngineeringAgentModelCallReceipt,
    EngineeringAgentModelDispatchState,
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
    LightweightAgentTraceStore,
    LightweightCitationSelection,
    LightweightCognitionCandidate,
    LightweightDecisionResult,
    LightweightReview,
    LightweightReviewResult,
    LightweightReviewVerdict,
    SealedLightweightDeliveryControl,
)
from software_world_model.cross_cutting import (
    DomainError,
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


if __name__ == "__main__":
    unittest.main()
