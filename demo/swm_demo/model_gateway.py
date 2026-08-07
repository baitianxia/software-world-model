from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import json
from typing import Protocol
import uuid
import re

from swm_demo.ids import content_hash
from swm_demo.knowledge_requirement import GAP, SATISFIED


class ModelProvider(Protocol):
    provider_name: str
    model_name: str
    model_version: str

    def invoke(
        self, capability: str, payload: dict[str, object]
    ) -> dict[str, object]: ...


class ModelCallRepository(Protocol):
    def record_model_call(self, record: dict[str, object]) -> None: ...


@dataclass(frozen=True)
class ModelResult:
    model_call_id: str
    output: dict[str, object]


class ModelPhase(str, Enum):
    ROUTING = "ROUTING"
    REQUIREMENT = "REQUIREMENT"
    KNOWLEDGE_USE = "KNOWLEDGE_USE"
    INVESTIGATION = "INVESTIGATION"
    ASSESSMENT = "ASSESSMENT"
    ANSWER = "ANSWER"
    REVIEW = "REVIEW"


@dataclass(frozen=True)
class ModelExecutionContext:
    """One phase-isolated model context.

    The Demo provider is stateless, but the explicit identity makes the
    isolation rule testable and prevents a later conversational provider from
    silently reusing Investigation memory while drafting an answer.
    """

    context_id: str
    task_id: str
    phase: ModelPhase


_CAPABILITY_PHASES = {
    "route-task": ModelPhase.ROUTING,
    "form-knowledge-requirement": ModelPhase.REQUIREMENT,
    "plan-formal-knowledge-step": ModelPhase.KNOWLEDGE_USE,
    "assess-knowledge-sufficiency": ModelPhase.ASSESSMENT,
    "derive-build-intent": ModelPhase.INVESTIGATION,
    "propose-knowledge-candidates": ModelPhase.INVESTIGATION,
    "draft-answer": ModelPhase.ANSWER,
    "review-answer": ModelPhase.REVIEW,
}

_ANSWER_FORBIDDEN_KEYS = frozenset(
    {
        "artifact",
        "artifacts",
        "artifact_content",
        "candidate_bundle",
        "evidence_quote",
        "investigation",
        "source_content",
    }
)


class ModelGateway:
    """Provider-neutral model access and provenance recording.

    The bundled provider is deterministic so the architecture tests are
    replayable. It validates the gateway boundary, not real-model quality.
    """

    def __init__(
        self,
        provider: ModelProvider,
        repository: ModelCallRepository | None = None,
    ):
        self.provider = provider
        self.repository = repository
        self._closed_context_ids: set[str] = set()

    @staticmethod
    def open_context(task_id: str, phase: ModelPhase) -> ModelExecutionContext:
        if not isinstance(task_id, str) or not task_id.strip():
            raise ValueError("task_id must not be empty")
        if not isinstance(phase, ModelPhase):
            raise TypeError("phase must be a ModelPhase")
        return ModelExecutionContext(
            context_id=f"model-context:{uuid.uuid4()}",
            task_id=task_id,
            phase=phase,
        )

    def close_context(self, context: ModelExecutionContext) -> None:
        self._closed_context_ids.add(context.context_id)

    def invoke(
        self,
        capability: str,
        payload: dict[str, object],
        context: ModelExecutionContext | None = None,
    ) -> ModelResult:
        expected_phase = _CAPABILITY_PHASES.get(capability)
        if expected_phase is not None and context is None:
            raise ValueError(
                f"{capability} requires an explicit "
                f"{expected_phase.value} context"
            )
        if context is not None:
            if context.context_id in self._closed_context_ids:
                raise ValueError(f"model context is closed: {context.context_id}")
            if expected_phase is not None and context.phase is not expected_phase:
                raise ValueError(
                    f"{capability} requires {expected_phase.value} context, "
                    f"received {context.phase.value}"
                )
            if context.phase is ModelPhase.ANSWER:
                forbidden = self._find_forbidden_answer_keys(payload)
                if forbidden:
                    raise ValueError(
                        "answer context contains investigation-only fields: "
                        + ", ".join(sorted(forbidden))
                    )
        output = self.provider.invoke(capability, payload)
        call_id = f"model-call:{uuid.uuid4()}"
        if self.repository is not None:
            request_json = json.dumps(
                payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            )
            response_json = json.dumps(
                output, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            )
            self.repository.record_model_call(
                {
                    "model_call_id": call_id,
                    "provider": self.provider.provider_name,
                    "model": self.provider.model_name,
                    "model_version": self.provider.model_version,
                    "capability": capability,
                    "request_hash": content_hash(request_json),
                    "response": response_json,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "context_id": context.context_id if context else None,
                    "phase": context.phase.value if context else None,
                }
            )
        return ModelResult(model_call_id=call_id, output=output)

    @classmethod
    def _find_forbidden_answer_keys(
        cls, payload: dict[str, object]
    ) -> set[str]:
        found: set[str] = set()

        def walk(value: object) -> None:
            if isinstance(value, dict):
                for key, nested in value.items():
                    normalized = str(key).lower()
                    if normalized in _ANSWER_FORBIDDEN_KEYS or "quote" in normalized:
                        found.add(str(key))
                    walk(nested)
            elif isinstance(value, (list, tuple)):
                for nested in value:
                    walk(nested)

        walk(payload)
        return found


class DeterministicValidationProvider:
    """Replayable test double for Agent orchestration and review control flow."""

    provider_name = "validation"
    model_name = "deterministic-semantic-double"
    model_version = "1"

    def invoke(
        self, capability: str, payload: dict[str, object]
    ) -> dict[str, object]:
        if capability == "route-task":
            request = str(payload.get("request", "")).lower()
            if any(token in request for token in ("为什么", "历史", "升级", "提交")):
                return {"use_case": "history-view"}
            if any(token in request for token in ("业务", "约束", "能力")):
                return {"use_case": "business-view"}
            if any(token in request for token in ("流程", "行为", "创建订单", "取消")):
                return {"use_case": "behavior-view"}
            if any(token in request for token in ("generateorder", "入口", "承接", "结构")):
                return {
                    "use_case": "endpoint-structure",
                    "endpoint": "POST /order/generateOrder",
                }
            return {"use_case": "structure-view"}

        if capability == "draft-answer":
            claims = [str(item) for item in payload.get("claims", [])]
            return {"answer": "\n".join(claims)}

        if capability == "form-knowledge-requirement":
            request = str(payload.get("original_request", ""))
            commit = re.search(r"\b[0-9a-fA-F]{7,40}\b", request)
            if commit is not None:
                commit_id = commit.group(0).lower()
                return {
                    "needs": [
                        {
                            "need_id": "need:requested-commit",
                            "question": f"What changed in commit {commit_id}?",
                            "sufficiency_criterion": (
                                "An admitted History Inference for the exact commit "
                                "is supported by formal commit and diff Facts."
                            ),
                        }
                    ]
                }
            return {
                "needs": [
                    {
                        "need_id": "need:requested-view",
                        "question": request,
                        "sufficiency_criterion": (
                            "At least one admitted formal proposition directly "
                            "answers the requested view."
                        ),
                    }
                ]
            }

        if capability == "plan-formal-knowledge-step":
            trace = list(payload.get("tool_trace", []))
            if trace:
                return {"action": "STOP", "arguments": {}}

            request = str(payload.get("original_request", ""))
            lowered = request.lower()
            commit = re.search(r"\b[0-9a-fA-F]{7,40}\b", request)
            if commit is not None:
                return {
                    "action": "SEARCH",
                    "arguments": {
                        "kind": "INFERENCE",
                        "query": commit.group(0).lower()[:7],
                        "match_mode": "CONTAINS",
                        "type_name": "HISTORY_IMPACT",
                        "limit": 20,
                        "cursor": 0,
                    },
                }
            if "约束" in lowered:
                query = "业务约束候选"
                inference_type = "BUSINESS_CONSTRAINT"
            elif "能力" in lowered or "业务" in lowered:
                query = "承载的业务能力"
                inference_type = "BUSINESS_CAPABILITY"
            elif "取消" in lowered:
                query = "B-02 取消订单"
                inference_type = "BEHAVIOR_FLOW"
            elif "创建订单" in lowered:
                query = "B-01 创建订单"
                inference_type = "BEHAVIOR_FLOW"
            elif "流程" in lowered or "行为" in lowered:
                query = "综合实际调用"
                inference_type = "BEHAVIOR_FLOW"
            elif any(token in lowered for token in ("为什么", "历史", "升级", "提交")):
                query = "提交"
                inference_type = "HISTORY_IMPACT"
            else:
                query = request
                inference_type = None
            return {
                "action": "SEARCH",
                "arguments": {
                    "kind": "INFERENCE",
                    "query": query,
                    "match_mode": "CONTAINS",
                    "type_name": inference_type,
                    "limit": 20,
                    "cursor": 0,
                },
            }

        if capability == "assess-knowledge-sufficiency":
            request = str(payload.get("original_request", ""))
            commit = re.search(r"\b[0-9a-fA-F]{7,40}\b", request)
            formal_claims = list(payload.get("formal_claims", []))
            if commit is not None:
                marker = commit.group(0).lower()[:7]
                formal_claims = [
                    item
                    for item in formal_claims
                    if marker in str(item.get("text", "")).lower()
                ]
            references = [
                reference
                for claim in formal_claims
                for reference in claim.get("references", [])
            ]
            items = []
            for need in payload.get("requirement", []):
                items.append(
                    {
                        "need_id": need["need_id"],
                        "status": SATISFIED if references else GAP,
                        "references": references,
                        "rationale": "" if references else "formal knowledge is absent",
                    }
                )
            return {"items": items}

        if capability == "derive-build-intent":
            request = str(payload.get("original_request", ""))
            commit = re.search(r"\b[0-9a-fA-F]{7,40}\b", request)
            commits = [commit.group(0).lower()] if commit is not None else []
            return {
                "target_revision": payload.get("target_revision"),
                "artifact_request": {
                    "build_profile": "model-led",
                    "include_globs": ["pom.xml"],
                    "git_commit_ids": commits,
                    "derive_java_ast": False,
                    "revision": payload.get("target_revision"),
                },
                "knowledge_target": {
                    "history_commits": commits,
                    "required_inference_types": (
                        ["HISTORY_IMPACT"] if commits else []
                    ),
                },
            }

        if capability == "propose-knowledge-candidates":
            return {
                "covered_need_ids": list(payload.get("gap_need_ids", [])),
                "unresolved_need_ids": [],
            }

        if capability == "plan-knowledge-gap":
            return {
                "action": "knowledge-update",
                "build_profile": "full-validation",
            }

        if capability == "review-answer":
            candidate_claims = [
                str(item) for item in payload.get("candidate_claims", [])
            ]
            authoritative_claims = {
                str(item) for item in payload.get("authoritative_claims", [])
            }
            unsupported = [
                item for item in candidate_claims if item not in authoritative_claims
            ]
            return {
                "decision": "PASS" if not unsupported else "REJECT",
                "unsupported_claims": unsupported,
            }

        raise ValueError(f"unsupported validation model capability: {capability}")
