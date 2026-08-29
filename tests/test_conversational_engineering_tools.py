from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from software_world_model.application_services.conversational_engineering_agent import (
    ApplicationOwnedEngineeringAgentTurnExecutor,
    EngineeringAgentClaimProposal,
    EngineeringAgentDeliveryAuthorization,
    EngineeringAgentDraftProposal,
    EngineeringAgentEvidenceDisposition,
    EngineeringAgentResponseKind,
    EngineeringAgentReviewDecision,
    EngineeringAgentReviewProposal,
    EngineeringAgentToolActionProposal,
    EngineeringAgentToolOperation,
    EngineeringAgentWorkPhase,
    EngineeringAgentWorkStateProposal,
)
from software_world_model.application_services.conversational_engineering_tools import (
    EngineeringAgentEvidenceToolAdapter,
    EngineeringAgentEvidenceToolConfiguration,
)
from software_world_model.application_services.engineering_conversation import (
    ENGINEERING_CHAT_APPLICATION_CLARIFICATION_QUALITY,
    ENGINEERING_CHAT_EMPTY_CONTEXT_REFERENT_POLICY_ZH_CN,
    ConversationMessageKind,
    ConversationTurnState,
    EngineeringChatBinding,
    InMemoryEngineeringConversationService,
    RuntimeCapabilityStatus,
)
from software_world_model.application_services.engineering_question_answering import (
    CognitionDimension,
    CognitionItem,
    EngineeringEvidenceClass,
    SourceBroker,
    WorldModelCognitionContext,
)
from software_world_model.cross_cutting import (
    DomainError,
    Revision,
    StableId,
    digest_of,
)
from software_world_model.interface.engineering_qa_source import (
    LocalGitEvidenceClassProfile,
    LocalGitRetrievalWorker,
)


class SequentialIdGenerator:
    def __init__(self) -> None:
        self.value = 0

    def new(self, kind: str) -> StableId:
        self.value += 1
        return StableId(f"{kind}_{self.value:032x}")


class ExactCognitionProjector:
    def project(self, *, request):
        item = CognitionItem.create(
            dimension=CognitionDimension.BEHAVIOR,
            statement="LoginController delegates credential verification.",
            modality="STRUCTURE_BEHAVIOR_RELATION",
            context_ref="snapshot-context",
            source_revision=request.repository_revision,
            locator="world-model:login-controller",
            support_references=("snapshot-evidence",),
            coverage="Exact fixture behavior relation.",
        )
        return WorldModelCognitionContext.create(
            request=request,
            scope_ref="fixture-scope",
            context_ref="fixture-context",
            schema_ref="fixture-schema@1",
            snapshot_ids=("fixture-snapshot",),
            read_authority_digest=request.world_model_read_authority_digest,
            source_revision=request.repository_revision,
            items=(item,),
            coverage=("Controller behavior is represented.",),
            unknowns=("Runtime credential store remains outside this Snapshot.",),
        )


class QueryAwareCognitionProjector(ExactCognitionProjector):
    def __init__(self) -> None:
        self.queries = []

    def project_for_query(self, *, request, query):
        self.queries.append(query)
        item = CognitionItem.create(
            dimension=CognitionDimension.BEHAVIOR,
            statement=f"Query-relevant World Model behavior: {query}",
            modality="QUERY_RELEVANT_BEHAVIOR_RELATION",
            context_ref="query-relevant-context",
            source_revision=request.repository_revision,
            locator="world-model:query-relevant-behavior",
            support_references=("query-relevant-snapshot-evidence",),
            coverage="Only records relevant to the semantic query are projected.",
        )
        return WorldModelCognitionContext.create(
            request=request,
            scope_ref="fixture-scope",
            context_ref="query-relevant-context",
            schema_ref="fixture-schema@1",
            snapshot_ids=("fixture-snapshot",),
            read_authority_digest=request.world_model_read_authority_digest,
            source_revision=request.repository_revision,
            items=(item,),
            coverage=("Query-relevant behavior is represented.",),
        )


class JavaEntityCognitionProjector:
    def project(self, *, request):
        item = CognitionItem.create(
            dimension=CognitionDimension.ENTITY,
            statement=json.dumps(
                {
                    "kind": "STRUCTURE_ENTITY",
                    "entity_type": "JAVA_METHOD",
                    "root_fields": {
                        "declaring_type_qualified_name": (
                            "com.example.auth.CredentialVerifier"
                        ),
                        "method_name": "verify",
                    },
                    "state_fields": {
                        "source_path": (
                            "src/main/java/com/example/auth/CredentialVerifier.java"
                        )
                    },
                },
                sort_keys=True,
                separators=(",", ":"),
            ),
            modality="STRUCTURE_ENTITY_STATE",
            context_ref="java-entity-context",
            source_revision=request.repository_revision,
            locator="world-model:credential-verifier",
            support_references=("java-entity-snapshot-evidence",),
            coverage="Exact Java declaring type and source path.",
        )
        return WorldModelCognitionContext.create(
            request=request,
            scope_ref="fixture-scope",
            context_ref="java-entity-context",
            schema_ref="java-source-semantics@1",
            snapshot_ids=("fixture-snapshot",),
            read_authority_digest=request.world_model_read_authority_digest,
            source_revision=request.repository_revision,
            items=(item,),
            coverage=("Java entity state is represented.",),
        )


class OverlappingQueryCognitionProjector(ExactCognitionProjector):
    def __init__(self) -> None:
        self.queries = []

    def project_for_query(self, *, request, query):
        self.queries.append(query)
        shared = CognitionItem.create(
            dimension=CognitionDimension.BEHAVIOR,
            statement="Shared login behavior.",
            modality="QUERY_RELEVANT_BEHAVIOR_RELATION",
            context_ref="overlap-context",
            source_revision=request.repository_revision,
            locator="world-model:shared-login-behavior",
            support_references=("shared-snapshot-evidence",),
            coverage="Shared behavior represented for both queries.",
        )
        unique = CognitionItem.create(
            dimension=CognitionDimension.RELATION,
            statement=f"Unique cognition for {query}.",
            modality="QUERY_RELEVANT_RESPONSIBILITY_RELATION",
            context_ref="overlap-context",
            source_revision=request.repository_revision,
            locator=f"world-model:unique-{len(self.queries)}",
            support_references=(f"unique-snapshot-{len(self.queries)}",),
            coverage="One query-specific responsibility is represented.",
        )
        return WorldModelCognitionContext.create(
            request=request,
            scope_ref="fixture-scope",
            context_ref="overlap-context",
            schema_ref="fixture-schema@1",
            snapshot_ids=("fixture-snapshot",),
            read_authority_digest=request.world_model_read_authority_digest,
            source_revision=request.repository_revision,
            items=(shared, unique),
            coverage=("Overlapping query cognition is represented.",),
        )


class RepeatedQueryCognitionProjector(ExactCognitionProjector):
    def __init__(self) -> None:
        self.queries = []

    def project_for_query(self, *, request, query):
        self.queries.append(query)
        return self.project(request=request)


class RecordingReviewer:
    def __init__(self) -> None:
        self.requests = []

    def review(self, request):
        self.requests.append(request)
        return EngineeringAgentReviewProposal.create(
            model_call_ref=f"tool-review-{len(self.requests)}",
            decision=EngineeringAgentReviewDecision.APPROVED,
        )


class ResponseControl:
    def authorize(self, request):
        return EngineeringAgentDeliveryAuthorization.create(
            authorization_ref="tool-delivery",
            turn_request_digest=request.turn_request_digest,
            work_state_digest=request.work_state.digest,
            package_digest=request.package.digest,
            answer_digest=request.draft.digest,
            review_digest=request.review.digest,
        )


def proposal(
    invocation,
    *,
    call_ref,
    action=None,
    draft=None,
    resolved_referents=(),
    accepted_correction_message_ids=(),
):
    previous = invocation.previous_work_state
    return EngineeringAgentWorkStateProposal.create(
        model_call_ref=call_ref,
        expected_context_digest=invocation.request.snapshot_before.context.digest,
        expected_previous_work_state_digest=(
            previous.digest if previous is not None else None
        ),
        goal=invocation.request.user_message.content,
        response_language="zh-CN",
        audience="software engineer",
        constraints=("use only sealed evidence",),
        resolved_referents=resolved_referents,
        accepted_correction_message_ids=accepted_correction_message_ids,
        hypotheses=("the evidence can falsify the current explanation",),
        plan=("inspect exact evidence",),
        observation_ids=tuple(
            item.observation_id for item in invocation.observations
        ),
        open_items=("complete fresh review",),
        phase=(
            EngineeringAgentWorkPhase.RESPONSE_READY
            if draft is not None
            else EngineeringAgentWorkPhase.INVESTIGATING
        ),
        action=action,
        draft=draft,
    )


class WorldThenAnswerDriver:
    def __init__(self) -> None:
        self.calls = 0

    def propose(self, invocation):
        self.calls += 1
        if self.calls == 1:
            return proposal(
                invocation,
                call_ref="world-agent-1",
                action=EngineeringAgentToolActionProposal.create(
                    operation=EngineeringAgentToolOperation.WORLD_MODEL_QUERY,
                    arguments=(("query", "login behavior and boundaries"),),
                    evidence_need="understand known behavior and unknown boundaries",
                ),
            )
        support = tuple(
            item.observation_id
            for item in invocation.observations
            if item.disposition is EngineeringAgentEvidenceDisposition.SUPPORT
        )
        return proposal(
            invocation,
            call_ref="world-agent-2",
            draft=EngineeringAgentDraftProposal.create(
                response_kind=EngineeringAgentResponseKind.ANSWER,
                content="世界模型支持控制器委托凭据验证这一有限结论。",
                claims=(
                    EngineeringAgentClaimProposal.create(
                        statement="控制器委托凭据验证。",
                        support_observation_ids=support,
                    ),
                ),
            ),
        )


class SemanticNeedWorldThenAnswerDriver(WorldThenAnswerDriver):
    def propose(self, invocation):
        if self.calls == 0:
            self.calls += 1
            return proposal(
                invocation,
                call_ref="semantic-world-agent-1",
                action=EngineeringAgentToolActionProposal.create(
                    operation=EngineeringAgentToolOperation.WORLD_MODEL_QUERY,
                    arguments=(),
                    evidence_need=(
                        "Locate AdminService login credential verification and token generation"
                    ),
                ),
            )
        return super().propose(invocation)


class TwoWorldQueriesThenAnswerDriver:
    def __init__(self) -> None:
        self.calls = 0

    def propose(self, invocation):
        self.calls += 1
        if self.calls <= 2:
            return proposal(
                invocation,
                call_ref=f"two-world-agent-{self.calls}",
                action=EngineeringAgentToolActionProposal.create(
                    operation=EngineeringAgentToolOperation.WORLD_MODEL_QUERY,
                    arguments=(("query", f"semantic need {self.calls}"),),
                    evidence_need=f"inspect semantic need {self.calls}",
                ),
            )
        support = tuple(
            item.observation_id
            for item in invocation.observations
            if item.disposition is EngineeringAgentEvidenceDisposition.SUPPORT
        )
        return proposal(
            invocation,
            call_ref="two-world-agent-3",
            draft=EngineeringAgentDraftProposal.create(
                response_kind=EngineeringAgentResponseKind.ANSWER,
                content="世界模型提供共享行为与两条独有职责认知。",
                claims=(
                    EngineeringAgentClaimProposal.create(
                        statement="共享行为与两条独有职责认知均有支持。",
                        support_observation_ids=support,
                    ),
                ),
            ),
        )


class SearchReadAnswerDriver:
    def __init__(self) -> None:
        self.calls = 0

    def propose(self, invocation):
        self.calls += 1
        if self.calls == 1:
            return proposal(
                invocation,
                call_ref="source-agent-1",
                action=EngineeringAgentToolActionProposal.create(
                    operation=EngineeringAgentToolOperation.SOURCE_SEARCH,
                    arguments=(
                        (
                            "evidence_class",
                            EngineeringEvidenceClass.REPOSITORY_DOCUMENT.value,
                        ),
                        ("query", "login"),
                    ),
                    evidence_need="locate the exact login documentation",
                ),
            )
        if self.calls == 2:
            locator = next(
                reference
                for observation in invocation.observations
                for reference in observation.citation_refs
            )
            return proposal(
                invocation,
                call_ref="source-agent-2",
                action=EngineeringAgentToolActionProposal.create(
                    operation=EngineeringAgentToolOperation.SOURCE_READ,
                    arguments=(("locator_reference", locator),),
                    evidence_need="read the exact issued document locator",
                ),
            )
        support = tuple(
            item.observation_id
            for item in invocation.observations
            if item.disposition is EngineeringAgentEvidenceDisposition.SUPPORT
        )
        return proposal(
            invocation,
            call_ref="source-agent-3",
            draft=EngineeringAgentDraftProposal.create(
                response_kind=EngineeringAgentResponseKind.ANSWER,
                content="README 明确说明登录端点以及凭据验证行为。",
                claims=(
                    EngineeringAgentClaimProposal.create(
                        statement="登录端点和验证行为有精确文档证据。",
                        support_observation_ids=support,
                    ),
                ),
            ),
        )


class CrossTurnSourceRevalidationDriver:
    def __init__(self) -> None:
        self.calls_by_turn = {}
        self.second_turn_options = ()

    def propose(self, invocation):
        turn_ref = invocation.request.turn_id.value
        step = self.calls_by_turn.get(turn_ref, 0)
        self.calls_by_turn[turn_ref] = step + 1
        if invocation.request.sequence == 1 and step == 0:
            return proposal(
                invocation,
                call_ref="revalidation-turn-1-search",
                action=EngineeringAgentToolActionProposal.create(
                    operation=EngineeringAgentToolOperation.SOURCE_SEARCH,
                    arguments=(
                        (
                            "evidence_class",
                            EngineeringEvidenceClass.REPOSITORY_DOCUMENT.value,
                        ),
                        ("query", "login"),
                    ),
                    evidence_need="locate the exact login documentation",
                ),
            )
        if invocation.request.sequence == 1 and step == 1:
            locator = next(
                reference
                for observation in invocation.observations
                for reference in observation.citation_refs
            )
            return proposal(
                invocation,
                call_ref="revalidation-turn-1-read",
                action=EngineeringAgentToolActionProposal.create(
                    operation=EngineeringAgentToolOperation.SOURCE_READ,
                    arguments=(("locator_reference", locator),),
                    evidence_need="read the exact login documentation",
                ),
            )
        if invocation.request.sequence == 2 and step == 0:
            self.second_turn_options = invocation.preissued_source_read_options
            option = self.second_turn_options[0]
            return proposal(
                invocation,
                call_ref="revalidation-turn-2-read",
                action=EngineeringAgentToolActionProposal.create(
                    operation=EngineeringAgentToolOperation.SOURCE_READ,
                    arguments=(
                        ("locator_reference", option.locator_reference.value),
                    ),
                    evidence_need=(
                        "revalidate the prior exact login resource for this follow-up"
                    ),
                ),
            )
        read_support = tuple(
            item.observation_id
            for item in invocation.observations
            if item.operation is EngineeringAgentToolOperation.SOURCE_READ
            and item.disposition is EngineeringAgentEvidenceDisposition.SUPPORT
        )
        return proposal(
            invocation,
            call_ref=f"revalidation-turn-{invocation.request.sequence}-answer",
            draft=EngineeringAgentDraftProposal.create(
                response_kind=EngineeringAgentResponseKind.ANSWER,
                content="当前轮重新读取的精确来源支持登录说明。",
                claims=(
                    EngineeringAgentClaimProposal.create(
                        statement="登录说明由当前轮精确来源读取支持。",
                        support_observation_ids=read_support,
                    ),
                ),
            ),
        )


class FiveTurnLiteralSearchDriver:
    def __init__(self, *, read_count: int = 1) -> None:
        self.calls_by_turn = {}
        self.previous_state_revisions = []
        self.read_count = read_count

    def propose(self, invocation):
        turn_ref = invocation.request.turn_id.value
        step = self.calls_by_turn.get(turn_ref, 0)
        self.calls_by_turn[turn_ref] = step + 1
        corrections = (
            invocation.previous_work_state.accepted_correction_message_ids
            if invocation.previous_work_state is not None
            else ()
        )
        if (
            invocation.request.sequence == 3
            and invocation.request.user_message.message_id not in corrections
        ):
            corrections = (*corrections, invocation.request.user_message.message_id)
        if step == 0:
            self.previous_state_revisions.append(
                (
                    invocation.previous_work_state.revision.value
                    if invocation.previous_work_state is not None
                    else None
                )
            )
            return proposal(
                invocation,
                call_ref=f"five-turn-{turn_ref}-search",
                resolved_referents=("fixture login and authentication flow",),
                accepted_correction_message_ids=corrections,
                action=EngineeringAgentToolActionProposal.create(
                    operation=EngineeringAgentToolOperation.SOURCE_SEARCH,
                    arguments=(
                        ("evidence_class", EngineeringEvidenceClass.SOURCE.value),
                        ("query", "LoginService"),
                    ),
                    evidence_need="locate the exact login service declaration",
                ),
            )
        if 1 <= step <= self.read_count:
            locators = next(
                observation.citation_refs
                for observation in invocation.observations
                if observation.operation
                is EngineeringAgentToolOperation.SOURCE_SEARCH
                and observation.disposition
                is EngineeringAgentEvidenceDisposition.SUPPORT
            )
            locator = locators[step - 1]
            return proposal(
                invocation,
                call_ref=f"five-turn-{turn_ref}-read-{step}",
                resolved_referents=("fixture login and authentication flow",),
                accepted_correction_message_ids=corrections,
                action=EngineeringAgentToolActionProposal.create(
                    operation=EngineeringAgentToolOperation.SOURCE_READ,
                    arguments=(("locator_reference", locator),),
                    evidence_need="read the exact issued login service locator",
                ),
            )
        support = tuple(
            item.observation_id
            for item in invocation.observations
            if item.disposition is EngineeringAgentEvidenceDisposition.SUPPORT
        )
        return proposal(
            invocation,
            call_ref=f"five-turn-{turn_ref}-answer",
            resolved_referents=("fixture login and authentication flow",),
            accepted_correction_message_ids=corrections,
            draft=EngineeringAgentDraftProposal.create(
                response_kind=EngineeringAgentResponseKind.ANSWER,
                content="登录服务的精确源码证据已由当前轮搜索并读取。",
                claims=(
                    EngineeringAgentClaimProposal.create(
                        statement="当前轮已定位并读取登录服务。",
                        support_observation_ids=support,
                    ),
                ),
            ),
        )


class TwoSearchThenReadDriver:
    def __init__(self) -> None:
        self.calls = 0

    def propose(self, invocation):
        self.calls += 1
        if self.calls == 1:
            return proposal(
                invocation,
                call_ref="two-search-read-1",
                action=EngineeringAgentToolActionProposal.create(
                    operation=EngineeringAgentToolOperation.SOURCE_SEARCH,
                    arguments=(
                        ("evidence_class", EngineeringEvidenceClass.SOURCE.value),
                        ("query", "LoginService"),
                    ),
                    evidence_need="locate the login service",
                ),
            )
        if self.calls == 2:
            return proposal(
                invocation,
                call_ref="two-search-read-2",
                action=EngineeringAgentToolActionProposal.create(
                    operation=EngineeringAgentToolOperation.SOURCE_SEARCH,
                    arguments=(
                        ("evidence_class", EngineeringEvidenceClass.SOURCE.value),
                        ("query", "token"),
                    ),
                    evidence_need="locate the related token implementation",
                ),
            )
        if self.calls == 3:
            locator = next(
                observation.citation_refs[0]
                for observation in invocation.observations
                if observation.operation
                is EngineeringAgentToolOperation.SOURCE_SEARCH
                and observation.disposition
                is EngineeringAgentEvidenceDisposition.SUPPORT
                and observation.citation_refs
            )
            return proposal(
                invocation,
                call_ref="two-search-read-3",
                action=EngineeringAgentToolActionProposal.create(
                    operation=EngineeringAgentToolOperation.SOURCE_READ,
                    arguments=(("locator_reference", locator),),
                    evidence_need="use the reserved slot for the exact source",
                ),
            )
        support = tuple(
            item.observation_id
            for item in invocation.observations
            if item.disposition is EngineeringAgentEvidenceDisposition.SUPPORT
        )
        return proposal(
            invocation,
            call_ref="two-search-read-4",
            draft=EngineeringAgentDraftProposal.create(
                response_kind=EngineeringAgentResponseKind.ANSWER,
                content="登录服务和 token 生成的精确源码已读取。",
                claims=(
                    EngineeringAgentClaimProposal.create(
                        statement="最后一个文件槽位用于精确源码读取。",
                        support_observation_ids=support,
                    ),
                ),
            ),
        )


class RawPathReadDriver:
    def propose(self, invocation):
        return proposal(
            invocation,
            call_ref="raw-path-agent-1",
            action=EngineeringAgentToolActionProposal.create(
                operation=EngineeringAgentToolOperation.SOURCE_READ,
                arguments=(("path", "README.md"),),
                evidence_need="attempt a raw path read",
            ),
        )


class ConversationalEngineeringToolAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.repository = Path(self.temporary.name) / "repository"
        self.repository.mkdir()
        self.git("init", "-q")
        self.git("config", "user.email", "test@example.com")
        self.git("config", "user.name", "Test")
        (self.repository / "README.md").write_text(
            "The login endpoint verifies credentials before issuing a token.\n",
            encoding="utf-8",
        )
        self.git("add", "README.md")
        self.git("commit", "-q", "-m", "fixture")
        self.revision = self.git("rev-parse", "HEAD").strip()
        self.repository_id = StableId("repository_" + "1" * 32)
        self.binding_id = StableId("binding_" + "2" * 32)
        self.world_authority = digest_of({"world": "fixture"})
        self.profile = LocalGitEvidenceClassProfile.create(
            profile_ref="engineering-agent-tool-test:1",
            binding_id=self.binding_id,
            evidence_class_paths={
                EngineeringEvidenceClass.SOURCE: ("src/main/java",),
                EngineeringEvidenceClass.REPOSITORY_DOCUMENT: ("README.md",),
            },
        )
        self.configuration = EngineeringAgentEvidenceToolConfiguration.create(
            project_name="fixture",
            response_language="zh-CN",
            repository_id=self.repository_id,
            binding_id=self.binding_id,
            repository_revision=self.revision,
            source_profile_ref=self.profile.profile_ref,
            source_profile_digest=self.profile.profile_digest,
            world_model_read_authority_digest=self.world_authority,
            source_allowlist=("README.md", "src/main/java"),
        )
        self.worker = LocalGitRetrievalWorker(
            self.repository,
            repository_id=self.repository_id,
            binding_id=self.binding_id,
            source_profile=self.profile,
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def git(self, *arguments: str) -> str:
        completed = subprocess.run(
            ("git", "-C", str(self.repository), *arguments),
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return completed.stdout

    def service(self, driver, reviewer, *, cognition_projector=None):
        binding = EngineeringChatBinding.create(
            product_revision="a" * 40,
            project_name="fixture",
            repository_revision=self.revision,
            world_model_status=RuntimeCapabilityStatus.READY,
            world_model_authority_digest=self.world_authority,
            source_profile_ref=self.profile.profile_ref,
            source_access_status=RuntimeCapabilityStatus.READY,
            provider_status=RuntimeCapabilityStatus.READY,
            provider_route_ref="deterministic-test-route@1",
            conversation_input_policy_ref=(
                ENGINEERING_CHAT_EMPTY_CONTEXT_REFERENT_POLICY_ZH_CN
            ),
            known_limitations=("Alpha only", "Production is disabled"),
        )
        tools = EngineeringAgentEvidenceToolAdapter(
            configuration=self.configuration,
            cognition_projector=cognition_projector or ExactCognitionProjector(),
            source_broker=SourceBroker(source_profile=self.profile),
            retrieval_worker=self.worker,
        )
        executor = ApplicationOwnedEngineeringAgentTurnExecutor(
            driver=driver,
            tool_port=tools,
            reviewer=reviewer,
            response_control=ResponseControl(),
            available_operations=(
                EngineeringAgentToolOperation.WORLD_MODEL_QUERY,
                EngineeringAgentToolOperation.SOURCE_SEARCH,
                EngineeringAgentToolOperation.SOURCE_READ,
            ),
            require_tool_authority_receipts=True,
            id_generator=SequentialIdGenerator(),
        )
        return InMemoryEngineeringConversationService(
            binding,
            turn_executor=executor,
            id_generator=SequentialIdGenerator(),
        )

    def test_world_model_tool_splits_support_and_unknown_boundary(self) -> None:
        reviewer = RecordingReviewer()
        service = self.service(WorldThenAnswerDriver(), reviewer)
        conversation = service.create_conversation()

        submission = service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=Revision(1),
            message="登录流程是怎样的？",
        )

        self.assertEqual(submission.turn.state, ConversationTurnState.SUCCEEDED)
        package = reviewer.requests[0].package
        self.assertEqual(len(package.support_observations), 1)
        self.assertEqual(len(package.boundary_observations), 1)
        support = package.support_observations[0]
        boundary = package.boundary_observations[0]
        self.assertEqual(support.authority_receipt, boundary.authority_receipt)
        self.assertEqual(len(support.citation_refs), 1)
        self.assertEqual(
            tuple(item.kind for item in support.authority_receipt.ledger_entries),
            ("COGNITION_CONTEXT", "RESOURCE_RECEIPT"),
        )
        self.assertIn("WORLD_MODEL_UNKNOWN_REPORTED", boundary.content)

    def test_world_model_tool_records_query_relevant_cognition_context(self) -> None:
        reviewer = RecordingReviewer()
        projector = QueryAwareCognitionProjector()
        service = self.service(
            WorldThenAnswerDriver(),
            reviewer,
            cognition_projector=projector,
        )
        conversation = service.create_conversation()

        submission = service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=Revision(1),
            message="登录流程是怎样的？",
        )

        self.assertEqual(submission.turn.state, ConversationTurnState.SUCCEEDED)
        self.assertEqual(projector.queries, ["login behavior and boundaries"])
        support = reviewer.requests[0].package.support_observations[0]
        self.assertIn("login behavior and boundaries", support.content)
        self.assertEqual(
            tuple(item.kind for item in support.authority_receipt.ledger_entries),
            ("COGNITION_CONTEXT", "COGNITION_CONTEXT", "RESOURCE_RECEIPT"),
        )

    def test_world_model_tool_compiles_semantic_need_with_exact_turn(self) -> None:
        reviewer = RecordingReviewer()
        projector = QueryAwareCognitionProjector()
        service = self.service(
            SemanticNeedWorldThenAnswerDriver(),
            reviewer,
            cognition_projector=projector,
        )
        conversation = service.create_conversation()

        submission = service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=Revision(1),
            message="管理员登录从用户名和密码到 token 的流程是什么？",
        )

        self.assertEqual(submission.turn.state, ConversationTurnState.SUCCEEDED)
        self.assertEqual(len(projector.queries), 1)
        query = projector.queries[0]
        self.assertIn("AdminService login", query)
        self.assertIn("管理员登录", query)

    def test_world_model_tool_projects_exact_java_declaring_type_search_target(
        self,
    ) -> None:
        reviewer = RecordingReviewer()
        service = self.service(
            WorldThenAnswerDriver(),
            reviewer,
            cognition_projector=JavaEntityCognitionProjector(),
        )
        conversation = service.create_conversation()

        submission = service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=Revision(1),
            message="凭据校验实现在哪里？",
        )

        self.assertEqual(submission.turn.state, ConversationTurnState.SUCCEEDED)
        support = reviewer.requests[0].package.support_observations[0]
        payload = json.loads(support.content)
        item_view = payload["dimensions"][0]
        self.assertEqual(payload["schema"], "ENGINEERING_AGENT_WORLD_MODEL_SUPPORT@3")
        self.assertEqual(
            payload["source_search_target_projection"],
            {
                "schema": "ENGINEERING_AGENT_COGNITION_SOURCE_SEARCH_TARGETS@1",
                "kind": "JAVA_DECLARING_TYPE_LITERAL",
                "options": [
                    {
                        "literal": "CredentialVerifier",
                        "resource_locators": [
                            "src/main/java/com/example/auth/CredentialVerifier.java"
                        ],
                        "source_revision": self.revision,
                        "cognition_item_ids": [item_view["item_id"]],
                        "cognition_item_digests": [item_view["digest"]],
                    }
                ],
                "truncated": False,
                "grants_source_authority": False,
            },
        )

    def test_world_model_tool_projects_only_novel_items_across_one_turn(self) -> None:
        reviewer = RecordingReviewer()
        projector = OverlappingQueryCognitionProjector()
        service = self.service(
            TwoWorldQueriesThenAnswerDriver(),
            reviewer,
            cognition_projector=projector,
        )
        conversation = service.create_conversation()

        submission = service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=Revision(1),
            message="登录行为和职责分别是什么？",
        )

        self.assertEqual(submission.turn.state, ConversationTurnState.SUCCEEDED)
        self.assertEqual(projector.queries, ["semantic need 1", "semantic need 2"])
        support = reviewer.requests[0].package.support_observations
        self.assertEqual(len(support), 2)
        first = json.loads(support[0].content)
        second = json.loads(support[1].content)
        self.assertEqual(first["schema"], "ENGINEERING_AGENT_WORLD_MODEL_SUPPORT@3")
        self.assertEqual(first["projection"]["novel_item_count"], 2)
        self.assertEqual(
            first["projection"]["previously_observed_item_count"],
            0,
        )
        self.assertEqual(second["projection"]["current_context_item_count"], 2)
        self.assertEqual(second["projection"]["novel_item_count"], 1)
        self.assertEqual(
            second["projection"]["previously_observed_item_count"],
            1,
        )
        self.assertIn("Shared login behavior.", support[0].content)
        self.assertNotIn("Shared login behavior.", support[1].content)
        self.assertIn("Unique cognition for semantic need 2.", support[1].content)
        self.assertEqual(len(support[0].citation_refs), 2)
        self.assertEqual(len(support[1].citation_refs), 1)
        self.assertEqual(len(submission.turn.citations), 3)

    def test_world_model_tool_marks_fully_repeated_context_as_no_progress(self) -> None:
        reviewer = RecordingReviewer()
        projector = RepeatedQueryCognitionProjector()
        service = self.service(
            TwoWorldQueriesThenAnswerDriver(),
            reviewer,
            cognition_projector=projector,
        )
        conversation = service.create_conversation()

        submission = service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=Revision(1),
            message="重复查询不应复制认知。",
        )

        self.assertEqual(submission.turn.state, ConversationTurnState.SUCCEEDED)
        package = reviewer.requests[0].package
        self.assertEqual(len(package.support_observations), 1)
        self.assertEqual(len(package.boundary_observations), 2)
        repeated = next(
            item
            for item in package.boundary_observations
            if "WORLD_MODEL_HAS_NO_NEW_SUPPORTED_ITEMS" in item.content
        )
        self.assertFalse(repeated.progress)
        self.assertIn("WORLD_MODEL_HAS_NO_NEW_SUPPORTED_ITEMS", repeated.content)
        self.assertEqual(len(submission.turn.citations), 1)

    def test_source_search_then_opaque_read_extends_one_turn_ledger(self) -> None:
        reviewer = RecordingReviewer()
        service = self.service(SearchReadAnswerDriver(), reviewer)
        conversation = service.create_conversation()

        submission = service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=Revision(1),
            message="登录说明是什么？",
        )

        self.assertEqual(submission.turn.state, ConversationTurnState.SUCCEEDED)
        support = reviewer.requests[0].package.support_observations
        self.assertEqual(len(support), 2)
        search_receipt = support[0].authority_receipt
        read_receipt = support[1].authority_receipt
        self.assertIsNotNone(search_receipt)
        self.assertIsNotNone(read_receipt)
        self.assertEqual(search_receipt.ledger_ref, read_receipt.ledger_ref)
        self.assertEqual(
            read_receipt.ledger_entries[: len(search_receipt.ledger_entries)],
            search_receipt.ledger_entries,
        )
        self.assertEqual(len(search_receipt.ledger_entries), 6)
        self.assertEqual(len(read_receipt.ledger_entries), 11)
        self.assertEqual(len(support[0].citation_refs), 1)
        read_proposal = read_receipt.ledger_entries[6]
        self.assertEqual(
            dict(read_proposal.details)["locator_reference"],
            support[0].citation_refs[0],
        )
        self.assertIn("README.md", support[1].content)
        self.assertIn("issuing a token", support[1].content)
        self.assertGreaterEqual(len(submission.turn.citations), 2)
        self.assertEqual(
            tuple(item.source_revision for item in submission.turn.citations),
            (self.revision,) * len(submission.turn.citations),
        )
        self.assertTrue(
            any("README.md" in item.locator for item in submission.turn.citations)
        )
        receipt_citations = {
            item.citation_ref: item
            for observation in support
            for item in observation.authority_receipt.citations
        }
        for citation in submission.turn.citations:
            authority_citation = receipt_citations[citation.citation_ref]
            self.assertEqual(citation.evidence_class, authority_citation.evidence_class)
            self.assertEqual(citation.locator, authority_citation.locator)
            self.assertEqual(citation.content_digest, authority_citation.content_digest)
            self.assertEqual(citation.digest, authority_citation.digest)

    def test_follow_up_revalidates_prior_full_source_without_search(self) -> None:
        driver = CrossTurnSourceRevalidationDriver()
        reviewer = RecordingReviewer()
        service = self.service(driver, reviewer)
        conversation = service.create_conversation()

        first = service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=Revision(1),
            message="登录说明是什么？",
        )
        first_citation = next(
            item for item in first.turn.citations if item.locator == "README.md"
        )
        second = service.submit_turn(
            conversation_id=first.snapshot.conversation.conversation_id,
            expected_revision=first.snapshot.conversation.revision,
            message="沿用上一轮，失败分支呢？",
        )

        self.assertEqual(second.turn.state, ConversationTurnState.SUCCEEDED)
        self.assertEqual(len(driver.second_turn_options), 1)
        option = driver.second_turn_options[0]
        self.assertEqual(option.locator, "README.md")
        self.assertEqual(option.source_revision, self.revision)
        self.assertEqual(option.content_digest, first_citation.content_digest)
        self.assertEqual(option.origin_turn_id, first.turn.turn_id)
        self.assertEqual(
            option.origin_citation_digest,
            first_citation.digest,
        )
        package = reviewer.requests[-1].package
        self.assertEqual(len(package.support_observations), 1)
        support = package.support_observations[0]
        self.assertIs(
            support.operation,
            EngineeringAgentToolOperation.SOURCE_READ,
        )
        self.assertIn("issuing a token", support.content)
        proposal_entry = next(
            item
            for item in support.authority_receipt.ledger_entries
            if item.kind == "INVESTIGATION_PROPOSAL"
        )
        proposal_details = dict(proposal_entry.details)
        self.assertEqual(
            proposal_details["locator_origin"],
            "PRIOR_TURN_EXACT_SOURCE_REVALIDATION",
        )
        self.assertEqual(
            proposal_details["origin_turn_id"],
            first.turn.turn_id.value,
        )
        usage = dict(support.authority_receipt.ledger_entries[-1].details)
        self.assertEqual(usage["source_files"], "1")
        second_citation = next(
            item for item in second.turn.citations if item.locator == "README.md"
        )
        self.assertNotEqual(
            second_citation.citation_ref,
            first_citation.citation_ref,
        )
        self.assertEqual(
            second_citation.content_digest,
            first_citation.content_digest,
        )

    def test_raw_path_read_is_rejected_before_retrieval(self) -> None:
        reviewer = RecordingReviewer()
        service = self.service(RawPathReadDriver(), reviewer)
        conversation = service.create_conversation()

        submission = service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=Revision(1),
            message="直接读取路径",
        )

        self.assertEqual(submission.turn.state, ConversationTurnState.FAILED)
        self.assertEqual(submission.turn.failure_code, "AGENT_PROTOCOL_VIOLATION")
        self.assertEqual(len(reviewer.requests), 0)

    def test_fixed_five_turn_chat_keeps_read_budget_and_new_chat_clarifies(
        self,
    ) -> None:
        source_root = self.repository / "src/main/java/example"
        source_root.mkdir(parents=True)
        for index in range(70):
            (source_root / f"AUnrelated{index:02d}.java").write_text(
                f"final class AUnrelated{index:02d} {{}}\n",
                encoding="utf-8",
            )
        (source_root / "LoginService.java").write_text(
            "public interface LoginService { boolean authenticate(); }\n",
            encoding="utf-8",
        )
        self.git("add", "src/main/java")
        self.git("commit", "-q", "-m", "large source fixture")
        self.revision = self.git("rev-parse", "HEAD").strip()
        self.configuration = EngineeringAgentEvidenceToolConfiguration.create(
            project_name="fixture",
            response_language="zh-CN",
            repository_id=self.repository_id,
            binding_id=self.binding_id,
            repository_revision=self.revision,
            source_profile_ref=self.profile.profile_ref,
            source_profile_digest=self.profile.profile_digest,
            world_model_read_authority_digest=self.world_authority,
            source_allowlist=("README.md", "src/main/java"),
        )
        self.worker = LocalGitRetrievalWorker(
            self.repository,
            repository_id=self.repository_id,
            binding_id=self.binding_id,
            source_profile=self.profile,
        )
        questions = (
            "登录流程是怎样的？",
            "它失败时会记录什么？",
            "我指的是认证失败，不是权限不足。",
            "那 401 和 403 分别由谁产生？",
            "总结一下，只保留用户能看到的流程。",
        )
        driver = FiveTurnLiteralSearchDriver()
        reviewer = RecordingReviewer()
        service = self.service(driver, reviewer)
        current = service.create_conversation()
        work_state_ref = None

        for sequence, question in enumerate(questions, 1):
            submission = service.submit_turn(
                conversation_id=current.conversation.conversation_id,
                expected_revision=current.conversation.revision,
                message=question,
            )

            self.assertEqual(submission.turn.state, ConversationTurnState.SUCCEEDED)
            self.assertEqual(submission.turn.provider_dispatch_count, 4)
            self.assertEqual(
                submission.snapshot.messages[-1].kind,
                ConversationMessageKind.ANSWER,
            )
            self.assertEqual(
                submission.snapshot.context.work_state_revision.value,
                sequence * 3,
            )
            if work_state_ref is None:
                work_state_ref = submission.snapshot.context.work_state_ref
            else:
                self.assertEqual(
                    submission.snapshot.context.work_state_ref,
                    work_state_ref,
                )
            package = reviewer.requests[-1].package
            self.assertEqual(len(package.support_observations), 2)
            self.assertEqual(len(package.boundary_observations), 1)
            self.assertIn(
                "LoginService.java",
                package.support_observations[0].content,
            )
            self.assertIn(
                "SOURCE_FILE_FUSE_EXHAUSTED",
                package.boundary_observations[0].content,
            )
            self.assertIn(
                "authenticate",
                package.support_observations[1].content,
            )
            search_usage = dict(
                package.support_observations[0]
                .authority_receipt.ledger_entries[-1]
                .details
            )
            read_usage = dict(
                package.support_observations[1]
                .authority_receipt.ledger_entries[-1]
                .details
            )
            self.assertEqual(search_usage["source_files"], "56")
            self.assertEqual(read_usage["source_files"], "57")
            self.assertEqual(search_usage["maximum_source_files"], "64")
            self.assertEqual(read_usage["maximum_source_files"], "64")
            current = submission.snapshot

        self.assertEqual(driver.previous_state_revisions, [None, 3, 6, 9, 12])
        self.assertEqual(
            current.context.accepted_correction_message_ids,
            (current.messages[4].message_id,),
        )
        self.assertEqual(len(reviewer.requests), 5)
        self.assertEqual(service.provider_dispatch_count(), 20)
        sealed_conversation_digest = current.conversation.digest

        fresh = service.create_conversation()
        self.assertEqual(fresh.messages, ())
        self.assertEqual(fresh.turns, ())
        self.assertIsNone(fresh.context.work_state_ref)
        calls_before_probe = dict(driver.calls_by_turn)
        probe = service.submit_turn(
            conversation_id=fresh.conversation.conversation_id,
            expected_revision=fresh.conversation.revision,
            message="它呢？",
        )

        self.assertEqual(probe.turn.state, ConversationTurnState.SUCCEEDED)
        self.assertEqual(probe.turn.provider_dispatch_count, 0)
        self.assertEqual(
            probe.turn.quality_status,
            ENGINEERING_CHAT_APPLICATION_CLARIFICATION_QUALITY,
        )
        self.assertEqual(
            probe.snapshot.messages[-1].kind,
            ConversationMessageKind.CLARIFICATION,
        )
        self.assertIn("请明确", probe.snapshot.messages[-1].content)
        self.assertEqual(driver.calls_by_turn, calls_before_probe)
        self.assertEqual(len(reviewer.requests), 5)
        self.assertEqual(service.provider_dispatch_count(), 20)
        self.assertEqual(
            service.get_conversation(
                current.conversation.conversation_id
            ).conversation.digest,
            sealed_conversation_digest,
        )

    def test_large_search_preserves_multiple_exact_reads_for_one_agent_turn(
        self,
    ) -> None:
        source_root = self.repository / "src/main/java/example"
        source_root.mkdir(parents=True)
        for index in range(70):
            (source_root / f"AUnrelated{index:02d}.java").write_text(
                f"final class AUnrelated{index:02d} {{}}\n",
                encoding="utf-8",
            )
        for name, declaration in (
            ("LoginService.java", "interface LoginService {}"),
            ("LoginServiceAudit.java", "final class LoginServiceAudit {}"),
            ("LoginServiceToken.java", "final class LoginServiceToken {}"),
        ):
            (source_root / name).write_text(declaration + "\n", encoding="utf-8")
        self.git("add", "src/main/java")
        self.git("commit", "-q", "-m", "multi-read source fixture")
        self.revision = self.git("rev-parse", "HEAD").strip()
        self.configuration = EngineeringAgentEvidenceToolConfiguration.create(
            project_name="fixture",
            response_language="zh-CN",
            repository_id=self.repository_id,
            binding_id=self.binding_id,
            repository_revision=self.revision,
            source_profile_ref=self.profile.profile_ref,
            source_profile_digest=self.profile.profile_digest,
            world_model_read_authority_digest=self.world_authority,
            source_allowlist=("README.md", "src/main/java"),
        )
        self.worker = LocalGitRetrievalWorker(
            self.repository,
            repository_id=self.repository_id,
            binding_id=self.binding_id,
            source_profile=self.profile,
        )
        reviewer = RecordingReviewer()
        service = self.service(
            FiveTurnLiteralSearchDriver(read_count=3),
            reviewer,
        )
        conversation = service.create_conversation()

        submission = service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=Revision(1),
            message="登录流程是怎样的？",
        )

        self.assertEqual(submission.turn.state, ConversationTurnState.SUCCEEDED)
        self.assertEqual(submission.turn.provider_dispatch_count, 6)
        package = reviewer.requests[-1].package
        self.assertEqual(len(package.support_observations), 4)
        self.assertEqual(len(package.boundary_observations), 1)
        self.assertIn(
            "SOURCE_FILE_FUSE_EXHAUSTED",
            package.boundary_observations[0].content,
        )
        search_usage = dict(
            package.support_observations[0]
            .authority_receipt.ledger_entries[-1]
            .details
        )
        final_read_usage = dict(
            package.support_observations[-1]
            .authority_receipt.ledger_entries[-1]
            .details
        )
        self.assertEqual(search_usage["source_files"], "56")
        self.assertEqual(final_read_usage["source_files"], "59")

    def test_two_searches_preserve_the_last_slot_for_an_exact_read(self) -> None:
        source_root = self.repository / "src/main/java/example"
        source_root.mkdir(parents=True)
        for index in range(70):
            (source_root / f"AUnrelated{index:02d}.java").write_text(
                f"final class AUnrelated{index:02d} {{}}\n",
                encoding="utf-8",
            )
        (source_root / "LoginService.java").write_text(
            "final class LoginService { String token() { return \"token\"; } }\n",
            encoding="utf-8",
        )
        self.git("add", "src/main/java")
        self.git("commit", "-q", "-m", "two-search source fixture")
        self.revision = self.git("rev-parse", "HEAD").strip()
        self.configuration = EngineeringAgentEvidenceToolConfiguration.create(
            project_name="fixture",
            response_language="zh-CN",
            repository_id=self.repository_id,
            binding_id=self.binding_id,
            repository_revision=self.revision,
            source_profile_ref=self.profile.profile_ref,
            source_profile_digest=self.profile.profile_digest,
            world_model_read_authority_digest=self.world_authority,
            source_allowlist=("README.md", "src/main/java"),
        )
        self.worker = LocalGitRetrievalWorker(
            self.repository,
            repository_id=self.repository_id,
            binding_id=self.binding_id,
            source_profile=self.profile,
        )
        driver = TwoSearchThenReadDriver()
        reviewer = RecordingReviewer()
        service = self.service(driver, reviewer)
        conversation = service.create_conversation()

        submission = service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=Revision(1),
            message="登录后 token 是怎么生成的？",
        )

        self.assertEqual(submission.turn.state, ConversationTurnState.SUCCEEDED)
        self.assertEqual(driver.calls, 4)
        package = reviewer.requests[-1].package
        support = package.support_observations
        observations = (*support, *package.boundary_observations)
        source_file_usage = {
            dict(observation.authority_receipt.ledger_entries[-1].details)[
                "source_files"
            ]
            for observation in observations
        }
        self.assertEqual(source_file_usage, {"56", "63", "64"})
        self.assertTrue(
            all(
                dict(observation.authority_receipt.ledger_entries[-1].details)[
                    "maximum_source_files"
                ]
                == "64"
                for observation in observations
            )
        )
        self.assertIn("LoginService.java", support[-1].content)

    def test_configuration_rejects_allowlist_that_contains_resources(self) -> None:
        with self.assertRaises(DomainError):
            EngineeringAgentEvidenceToolConfiguration.create(
                project_name="fixture",
                response_language="zh-CN",
                repository_id=self.repository_id,
                binding_id=self.binding_id,
                repository_revision=self.revision,
                source_profile_ref=self.profile.profile_ref,
                source_profile_digest=self.profile.profile_digest,
                world_model_read_authority_digest=self.world_authority,
                source_allowlist=(".",),
            )


if __name__ == "__main__":
    unittest.main()
