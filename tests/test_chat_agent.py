"""Tests for the V1.4 engineering Chat Agent loop (TASK-1 step A)."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from typing import Callable, Mapping

from software_world_model.application_services.chat_agent import (
    ChatAgentLimits,
    ChatAgentTurnExecutor,
    ChatModelOutput,
)
from software_world_model.application_services.conversational_engineering_agent import (
    EngineeringAgentModelCallReceipt,
    EngineeringAgentModelDispatchState,
    EngineeringAgentModelRole,
)
from software_world_model.application_services.engineering_conversation import (
    EngineeringChatBinding,
    InMemoryEngineeringConversationService,
    RuntimeCapabilityStatus,
)
from software_world_model.application_services.lightweight_engineering_agent import (
    LightweightAgentTraceStore,
    SealedLightweightDeliveryControl,
)
from software_world_model.cross_cutting import digest_of
from software_world_model.source_integration.exact_revision_tools import (
    ExactRevisionReadTools,
    ReadScope,
)


def _git(root: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *arguments], check=True, stdout=subprocess.PIPE, text=True
    ).stdout.strip()


def _action(op: str, **arguments: object) -> dict[str, object]:
    base: dict[str, object] = {
        "op": op, "glob": None, "prefix": None, "pattern": None, "regex": None,
        "path_glob": None, "path": None, "start_line": None, "end_line": None,
    }
    base.update(arguments)
    return base


def _step(plan: str, actions=(), final=None) -> dict[str, object]:
    return {"plan": plan, "actions": list(actions), "final": final}


def _final(kind: str, answer: str, citations=()) -> dict[str, object]:
    return {"kind": kind, "answer": answer, "citations": list(citations)}


def _review(verdict: str, findings=(), requests=()) -> dict[str, object]:
    return {"verdict": verdict, "findings": list(findings), "verification_requests": list(requests)}


class ScriptedModel:
    """Deterministic stand-in for the Provider-backed boundary."""

    def __init__(
        self,
        steps: list[Callable[[Mapping[str, object]], Mapping[str, object]] | Mapping[str, object]],
        reviews: list[Callable[[Mapping[str, object]], Mapping[str, object]] | Mapping[str, object]],
    ) -> None:
        self._steps = list(steps)
        self._reviews = list(reviews)
        self.step_views: list[Mapping[str, object]] = []
        self.review_views: list[Mapping[str, object]] = []
        self._calls = 0

    @property
    def instance_ref(self) -> str:
        return "scripted-model"

    def _receipt(self, role: EngineeringAgentModelRole) -> EngineeringAgentModelCallReceipt:
        self._calls += 1
        ref = f"call-{self._calls}"
        return EngineeringAgentModelCallReceipt.create(
            model_call_ref=ref,
            gateway_call_ref=ref,
            role=role,
            state=EngineeringAgentModelDispatchState.DISPATCHED_COMPLETED,
        )

    def step(self, *, turn_request, view):
        self.step_views.append(view)
        item = self._steps.pop(0)
        payload = item(view) if callable(item) else item
        return ChatModelOutput(payload, self._receipt(EngineeringAgentModelRole.PRIMARY_AGENT))

    def review_draft(self, *, turn_request, view):
        self.review_views.append(view)
        item = self._reviews.pop(0)
        payload = item(view) if callable(item) else item
        return ChatModelOutput(payload, self._receipt(EngineeringAgentModelRole.INDEPENDENT_REVIEWER))


def _evidence_ids(view: Mapping[str, object], fragment: str) -> list[str]:
    ids: list[str] = []
    for observation in view["observations"]:
        for item in observation.get("items", []):
            if "id" in item and fragment in item.get("text", ""):
                ids.append(item["id"])
    return ids


class ChatAgentTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        _git(self.root, "init", "-q")
        files = {
            "app/src/main/java/demo/LoginController.java": (
                "class LoginController {\n  String login(String u) {\n    return service.login(u);\n  }\n}\n"
            ),
            "app/src/main/java/demo/LoginService.java": (
                "class LoginService {\n  String login(String u) {\n    return jwt.generateToken(u);\n  }\n}\n"
            ),
            "app/src/main/resources/application.yml": "jwt:\n  expiration: 604800\n",
        }
        for relative, text in files.items():
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        _git(self.root, "add", "-A")
        _git(self.root, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "init")
        self.revision = _git(self.root, "rev-parse", "HEAD")
        self.binding = EngineeringChatBinding.create(
            product_revision="b" * 40,
            project_name="demo",
            repository_revision=self.revision,
            world_model_status=RuntimeCapabilityStatus.READY,
            world_model_authority_digest=digest_of("world-model"),
            source_profile_ref="source-profile",
            source_access_status=RuntimeCapabilityStatus.READY,
            provider_status=RuntimeCapabilityStatus.READY,
            provider_route_ref="preferred",
            known_limitations=("alpha evaluation",),
        )
        self.traces = LightweightAgentTraceStore()
        self.trace_dir = self.root.parent / (self.root.name + "-traces")

    def _run(self, model: ScriptedModel, message: str = "登录是怎么生成 token 的？", limits=ChatAgentLimits()):
        executor = ChatAgentTurnExecutor(
            model=model,
            tools=ExactRevisionReadTools(ReadScope(repository=self.root, revision=self.revision)),
            delivery_control=SealedLightweightDeliveryControl(),
            trace_store=self.traces,
            attempt_ref="attempt-1",
            limits=limits,
            trace_directory=self.trace_dir,
        )
        service = InMemoryEngineeringConversationService(self.binding, turn_executor=executor)
        conversation = service.create_conversation()
        return service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=conversation.conversation.revision,
            message=message,
        )

    def test_parallel_tools_then_cited_answer_is_reviewed_and_delivered(self) -> None:
        model = ScriptedModel(
            steps=[
                _step("search both layers", [_action("SEARCH", pattern="generateToken"), _action("LIST_PATHS", glob="*.java")]),
                lambda view: _step(
                    "read the service",
                    [_action("READ", path="app/src/main/java/demo/LoginService.java", start_line=1, end_line=5)],
                ),
                lambda view: _step(
                    "answer",
                    final=_final("ANSWER", "LoginService.login 调用 jwt.generateToken 生成 token。", _evidence_ids(view, "generateToken")[-1:]),
                ),
            ],
            reviews=[_review("APPROVED")],
        )
        submission = self._run(model)
        self.assertEqual(submission.turn.quality_status, "ACCEPTED")
        self.assertEqual(len(submission.turn.citations), 1)
        self.assertIn(self.revision, submission.turn.citations[0].locator)
        self.assertEqual(model.review_views[0]["cited_evidence"][0]["id"], "E2")
        trace_files = list(self.trace_dir.rglob("*.json"))
        self.assertEqual(len(trace_files), 1)
        record = json.loads(trace_files[0].read_text(encoding="utf-8"))
        self.assertEqual(record["terminal"], "DELIVERED")
        self.assertEqual(record["tool_actions"], 3)

    def test_read_needs_no_prior_candidate(self) -> None:
        model = ScriptedModel(
            steps=[
                _step("read directly", [_action("READ", path="app/src/main/resources/application.yml")]),
                lambda view: _step("answer", final=_final("ANSWER", "过期时间 604800 秒。", ["E1"])),
            ],
            reviews=[_review("APPROVED")],
        )
        self.assertEqual(self._run(model).turn.quality_status, "ACCEPTED")

    def test_unknown_citation_is_rejected_then_corrected(self) -> None:
        model = ScriptedModel(
            steps=[
                _step("search", [_action("SEARCH", pattern="expiration")]),
                _step("bad", final=_final("ANSWER", "604800", ["E99"])),
                lambda view: _step("fix", final=_final("ANSWER", "604800", ["E1"])),
            ],
            reviews=[_review("APPROVED")],
        )
        submission = self._run(model)
        self.assertEqual(submission.turn.quality_status, "ACCEPTED")
        self.assertIn("unknown: E99", model.step_views[2]["feedback"][0])

    def test_answer_without_citation_is_not_delivered(self) -> None:
        model = ScriptedModel(
            steps=[_step("guess", final=_final("ANSWER", "猜测的答案"))] * 3,
            reviews=[],
        )
        submission = self._run(model)
        self.assertEqual(submission.turn.state.value, "FAILED")
        self.assertEqual(submission.turn.failure_code, "STRUCTURED_OUTPUT_INVALID")

    def test_out_of_scope_and_duplicate_actions_become_observations(self) -> None:
        model = ScriptedModel(
            steps=[
                _step("try", [_action("READ", path="../etc/passwd"), _action("SEARCH", pattern="login"), _action("SEARCH", pattern="login")]),
                lambda view: _step("limit", final=_final("LIMITATION", "无法确认。")),
            ],
            reviews=[_review("APPROVED")],
        )
        submission = self._run(model)
        self.assertEqual(submission.turn.quality_status, "REVIEWED_LIMITATION")
        observations = model.step_views[1]["observations"]
        self.assertIn("SOURCE_TARGET_OUT_OF_SCOPE", observations[0]["error"])
        self.assertIn("duplicate", observations[2]["error"])

    def test_budget_exhaustion_forces_a_reviewed_limited_draft(self) -> None:
        limits = ChatAgentLimits(maximum_model_calls=6, reserved_review_calls=2, maximum_tool_actions=2)
        model = ScriptedModel(
            steps=[
                _step("search", [_action("SEARCH", pattern="login"), _action("SEARCH", pattern="token")]),
                lambda view: _step(
                    "no tools left",
                    final=_final("ANSWER", "Controller 调用 Service 的 login。（未读完全部实现）", _evidence_ids(view, "service.login")),
                ),
            ],
            reviews=[_review("APPROVED")],
        )
        submission = self._run(model, limits=limits)
        self.assertEqual(submission.turn.quality_status, "ACCEPTED")
        self.assertFalse(model.step_views[1]["tools_enabled"])

    def test_reviewer_verification_reads_stay_out_of_the_package(self) -> None:
        model = ScriptedModel(
            steps=[
                _step("search", [_action("SEARCH", pattern="generateToken")]),
                lambda view: _step("answer", final=_final("ANSWER", "Service 生成 token。", ["E1"])),
            ],
            reviews=[
                _review("VERIFY", requests=[{"op": "READ", "path": "app/src/main/java/demo/LoginController.java", "start_line": None, "end_line": None, "pattern": None}]),
                lambda view: _review("APPROVED") if view["verification_results"] else _review("REWRITE", ["missing"]),
            ],
        )
        submission = self._run(model)
        self.assertEqual(submission.turn.quality_status, "ACCEPTED")
        self.assertEqual(len(submission.turn.citations), 1)
        self.assertFalse(model.review_views[1]["verification_allowed"])
        self.assertIn("LoginController", model.review_views[1]["verification_results"][0]["items"][0]["locator"])

    def test_rewrite_finding_returns_to_the_same_agent_without_tools(self) -> None:
        model = ScriptedModel(
            steps=[
                _step("search", [_action("SEARCH", pattern="generateToken")]),
                lambda view: _step("answer", final=_final("ANSWER", "生成 token。", ["E1"])),
                lambda view: _step("rewrite", final=_final("ANSWER", "LoginService.login 调用 jwt.generateToken。", ["E1"])),
            ],
            reviews=[_review("REWRITE", ["未说明调用方"]), _review("APPROVED")],
        )
        submission = self._run(model)
        self.assertEqual(submission.turn.quality_status, "ACCEPTED")
        self.assertFalse(model.step_views[2]["tools_enabled"])
        self.assertEqual(model.step_views[2]["review_findings"], ["[REWRITE] 未说明调用方"])

    def test_more_evidence_reenables_tools(self) -> None:
        model = ScriptedModel(
            steps=[
                _step("search", [_action("SEARCH", pattern="generateToken")]),
                lambda view: _step("answer", final=_final("ANSWER", "生成 token。", ["E1"])),
                lambda view: _step("more", [_action("READ", path="app/src/main/java/demo/LoginController.java")]),
                lambda view: _step("answer2", final=_final("ANSWER", "Controller → Service → generateToken。", ["E1", "E2"])),
            ],
            reviews=[_review("MORE_EVIDENCE", ["缺少调用入口"]), _review("APPROVED")],
        )
        submission = self._run(model)
        self.assertEqual(submission.turn.quality_status, "ACCEPTED")
        self.assertTrue(model.step_views[2]["tools_enabled"])
        self.assertEqual(len(submission.turn.citations), 2)

    def test_unapproved_after_maximum_reviews_fails_closed(self) -> None:
        model = ScriptedModel(
            steps=[
                _step("search", [_action("SEARCH", pattern="generateToken")]),
                lambda view: _step("answer", final=_final("ANSWER", "x", ["E1"])),
                lambda view: _step("answer", final=_final("ANSWER", "y", ["E1"])),
            ],
            reviews=[_review("REWRITE", ["错"]), _review("REWRITE", ["还是错"])],
        )
        submission = self._run(model)
        self.assertEqual(submission.turn.state.value, "FAILED")
        self.assertEqual(submission.turn.failure_code, "REVIEW_NOT_APPROVED")

    def test_follow_up_turn_sees_history_but_not_previous_evidence(self) -> None:
        model = ScriptedModel(
            steps=[
                _step("search", [_action("SEARCH", pattern="generateToken")]),
                lambda view: _step("answer", final=_final("ANSWER", "生成 token。", ["E1"])),
                lambda view: _step("follow-up", final=_final("LIMITATION", "需要重新查看源码。")),
            ],
            reviews=[_review("APPROVED"), _review("APPROVED")],
        )
        executor = ChatAgentTurnExecutor(
            model=model,
            tools=ExactRevisionReadTools(ReadScope(repository=self.root, revision=self.revision)),
            delivery_control=SealedLightweightDeliveryControl(),
            trace_store=self.traces,
            attempt_ref="attempt-1",
        )
        service = InMemoryEngineeringConversationService(self.binding, turn_executor=executor)
        conversation = service.create_conversation()
        first = service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=conversation.conversation.revision,
            message="token 怎么生成？",
        )
        second = service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=first.snapshot.conversation.revision,
            message="那它的过期时间呢？",
        )
        self.assertEqual(second.turn.quality_status, "REVIEWED_LIMITATION")
        follow_view = model.step_views[2]
        self.assertEqual(follow_view["observations"], [])
        self.assertEqual([item["role"] for item in follow_view["conversation_history"]], ["USER", "ASSISTANT"])


if __name__ == "__main__":
    unittest.main()
