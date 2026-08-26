from __future__ import annotations

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


class FiveTurnLiteralSearchDriver:
    def __init__(self) -> None:
        self.calls_by_turn = {}
        self.previous_state_revisions = []

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
        if step == 1:
            locator = next(
                reference
                for observation in invocation.observations
                if observation.disposition
                is EngineeringAgentEvidenceDisposition.SUPPORT
                for reference in observation.citation_refs
            )
            return proposal(
                invocation,
                call_ref=f"five-turn-{turn_ref}-read",
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

    def service(self, driver, reviewer):
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
            cognition_projector=ExactCognitionProjector(),
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
            self.assertEqual(search_usage["source_files"], "63")
            self.assertEqual(read_usage["source_files"], "64")
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
