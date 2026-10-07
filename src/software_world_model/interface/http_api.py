"""Small standard-library JSON/HTTP adapter for the modular monolith."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Mapping, Sequence
from wsgiref.simple_server import WSGIRequestHandler, make_server

from software_world_model.application_services import (
    AnswerSectionKind,
    KnowledgeNeed,
    NaturalLanguageTaskRequest,
)
from software_world_model.cross_cutting import (
    CorrelationRef,
    DomainError,
    ErrorCode,
    IdempotencyKey,
    Revision,
    StableId,
)
from software_world_model.infrastructure import SqliteDatabase
from software_world_model.knowledge_engine import KnowledgeObjectKind
from software_world_model.source_integration import (
    LocalGitConnector,
    TargetKind,
)

from .browser_ui import BROWSER_CSS, BROWSER_HTML, BROWSER_JS
from .presenters import (
    authorized_task_answer_payload,
    knowledge_update_payload,
    sufficiency_assessment_payload,
)
from .runtime import ApplicationRuntime
from .agentic_runtime import build_activated_application_runtime


@dataclass(frozen=True, slots=True)
class RawHttpResponse:
    body: bytes
    content_type: str


class LoopbackWsgiRequestHandler(WSGIRequestHandler):
    """Bound incomplete local HTTP requests so one client cannot stall the API."""

    def setup(self) -> None:
        super().setup()
        self._apply_request_timeout()

    def _apply_request_timeout(self) -> None:
        timeout_seconds = getattr(self.server, "request_timeout_seconds", 15.0)
        self.connection.settimeout(timeout_seconds)


class JsonHttpApplication:
    """WSGI application exposing only public ApplicationRuntime use cases."""

    def __init__(
        self,
        runtime: ApplicationRuntime,
        *,
        max_request_bytes: int = 1_000_000,
        live_provider_configured: bool = False,
    ) -> None:
        if max_request_bytes < 1:
            raise ValueError("max_request_bytes must be positive")
        self._runtime = runtime
        self._max_request_bytes = max_request_bytes
        self._live_provider_configured = live_provider_configured

    def __call__(self, environ, start_response):
        try:
            status, payload = self._dispatch(environ)
        except DomainError as exc:
            status = _domain_status(exc.code)
            payload = {"error": exc.code.value, "message": exc.message}
        except (KeyError, TypeError, ValueError) as exc:
            status = "400 Bad Request"
            payload = {"error": ErrorCode.INVALID_ARGUMENT.value, "message": str(exc)}
        except Exception:
            status = "500 Internal Server Error"
            payload = {
                "error": "INTERNAL_ERROR",
                "message": "request failed without a public diagnostic",
            }
        if isinstance(payload, RawHttpResponse):
            encoded = payload.body
            content_type = payload.content_type
        else:
            encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
            content_type = "application/json; charset=utf-8"
        headers = [
            ("Content-Type", content_type),
            ("Content-Length", str(len(encoded))),
            ("Cache-Control", "no-store"),
            ("X-Content-Type-Options", "nosniff"),
            ("Referrer-Policy", "no-referrer"),
            ("X-Frame-Options", "DENY"),
        ]
        if content_type.startswith("text/html"):
            headers.append(
                (
                    "Content-Security-Policy",
                    "default-src 'self'; base-uri 'none'; form-action 'self'; "
                    "frame-ancestors 'none'; img-src 'self' data:; "
                    "style-src 'self'; script-src 'self'; connect-src 'self'",
                )
            )
        start_response(
            status,
            headers,
        )
        return [encoded]

    def _dispatch(
        self, environ
    ) -> tuple[str, dict[str, object] | RawHttpResponse]:
        method = str(environ.get("REQUEST_METHOD", "GET")).upper()
        path = str(environ.get("PATH_INFO", "/"))
        if method == "GET" and path in {"/", "/index.html"}:
            return "200 OK", _raw(BROWSER_HTML, "text/html; charset=utf-8")
        if method == "GET" and path == "/assets/browser.css":
            return "200 OK", _raw(BROWSER_CSS, "text/css; charset=utf-8")
        if method == "GET" and path == "/assets/browser.js":
            return "200 OK", _raw(
                BROWSER_JS, "text/javascript; charset=utf-8"
            )
        if method == "GET" and path == "/health":
            model_active = (
                self._live_provider_configured
                and self._runtime.reviewed_answer_preparation_configured
            )
            return "200 OK", {
                "status": "ready",
                "mode": "ACTIVATED_MODEL" if model_active else "OFFLINE",
                "live_provider_configured": self._live_provider_configured,
                "reviewed_answer_preparation_active": model_active,
            }
        if method == "GET" and path == "/v1/capabilities":
            capabilities = [
                "local-git-target-resolution",
                "knowledge-update",
                "exact-snapshot-query",
                "per-need-sufficiency",
            ]
            if self._runtime.natural_task_planning_configured:
                capabilities.append("natural-language-task-planning")
            if self._runtime.reviewed_answer_preparation_configured:
                capabilities.append("reviewed-answer-preparation")
            if getattr(
                self._runtime, "evidence_answer_preparation_configured", False
            ):
                capabilities.append("evidence-first-answering")
            return "200 OK", {
                "capabilities": capabilities,
                "live_model_execution": (
                    self._live_provider_configured
                    and self._runtime.reviewed_answer_preparation_configured
                ),
            }
        if method != "POST":
            return "404 Not Found", {"error": "NOT_FOUND", "message": "route not found"}
        body = self._read_json(environ)
        if path == "/v1/browser/projects":
            return "200 OK", self._connect_browser_project(body)
        if path == "/v1/browser/chat":
            return "200 OK", self._browser_chat(body)
        if path == "/v1/knowledge/update":
            result = self._runtime.update_knowledge(
                idempotency_key=IdempotencyKey(_text(body, "idempotency_key")),
                scope_id=StableId(_text(body, "scope_id")),
                scope_revision=Revision(_integer(body, "scope_revision", default=1)),
                source_id=StableId(_text(body, "source_id")),
                source_revision=Revision(_integer(body, "source_revision", default=1)),
                binding_id=StableId(_text(body, "binding_id")),
                binding_revision=Revision(_integer(body, "binding_revision", default=1)),
                target_kind=TargetKind(_text(body, "target_kind")),
                target_parameters=_string_mapping(body, "target_parameters"),
                objective_description=_text(body, "objective"),
                classification=_optional_text(body, "classification", "INTERNAL"),
                actor=_text(body, "actor"),
                correlation_ref=CorrelationRef(_text(body, "correlation_ref")),
                max_steps=_integer(body, "max_steps", default=8),
                max_items_per_step=_integer(body, "max_items_per_step", default=100),
                max_bytes_per_step=_integer(body, "max_bytes_per_step", default=256_000),
            )
            return "200 OK", knowledge_update_payload(result)
        if path == "/v1/tasks/prepare-answer":
            return "200 OK", self._prepare_answer(body)
        if path in {"/v1/knowledge/query", "/v1/tasks/query"}:
            needs_value = body.get("needs")
            snapshot = body.get("snapshot_id")
            if snapshot is not None and not isinstance(snapshot, str):
                raise ValueError("snapshot_id must be a string or null")
            common = {
                "idempotency_key": IdempotencyKey(_text(body, "idempotency_key")),
                "scope_id": StableId(_text(body, "scope_id")),
                "snapshot_id": StableId(snapshot) if snapshot else None,
                "original_request": _text(body, "request"),
                "classification": _optional_text(body, "classification", "INTERNAL"),
            }
            if needs_value is None and path == "/v1/tasks/query":
                assessment = self._runtime.query_task(**common)
            else:
                if not isinstance(needs_value, list) or not needs_value:
                    raise ValueError("needs must be a non-empty array")
                assessment = self._runtime.query_knowledge(
                    **common,
                    needs=tuple(_need(item) for item in needs_value),
                )
            return "200 OK", sufficiency_assessment_payload(assessment)
        return "404 Not Found", {"error": "NOT_FOUND", "message": "route not found"}

    def _connect_browser_project(
        self, body: Mapping[str, object]
    ) -> dict[str, object]:
        request_id = _bounded_text(body, "request_id", maximum=160)
        repository_value = _bounded_text(
            body, "repository_path", maximum=4096
        )
        repository = Path(repository_value).expanduser()
        if not repository.is_absolute():
            raise ValueError("repository_path must be an absolute path")
        if not repository.exists() or not repository.is_dir():
            raise ValueError("repository_path must be an existing directory")
        canonical_repository = str(repository.resolve())
        connector = LocalGitConnector(canonical_repository)
        exact_revision = connector.resolve_revision(
            _bounded_text(body, "revision", maximum=256)
        )
        comparison_value = body.get("comparison_base")
        if comparison_value is not None and not isinstance(comparison_value, str):
            raise ValueError("comparison_base must be a string or null")
        comparison_value = comparison_value.strip() if comparison_value else ""
        exact_base = (
            connector.resolve_revision(comparison_value)
            if comparison_value
            else None
        )
        selected_paths = _bounded_text(
            body, "selected_paths", maximum=4096
        )
        display_name_value = body.get("display_name")
        if display_name_value is not None and not isinstance(display_name_value, str):
            raise ValueError("display_name must be a string or null")
        display_name = (
            display_name_value.strip()
            if display_name_value and display_name_value.strip()
            else repository.name or "本地项目"
        )
        if len(display_name) > 120:
            raise ValueError("display_name is too long")
        execution = self._runtime.configure_local_git_project(
            idempotency_key=IdempotencyKey(
                f"browser-project:{request_id}"
            ),
            source_target=canonical_repository,
            selected_paths=selected_paths,
            display_name=display_name,
            actor="browser-local-user",
            correlation_ref=CorrelationRef(
                f"browser-project:{request_id}"
            ),
        )
        if execution.attempt.state.value != "SUCCEEDED":
            failed = next(
                (
                    step
                    for step in execution.result.steps
                    if step.failure_message
                ),
                None,
            )
            raise DomainError(
                ErrorCode.MANAGEMENT_STATE_CONFLICT,
                failed.failure_message if failed else "project configuration did not complete",
            )
        steps = {step.name: dict(step.output) for step in execution.result.steps}
        target_kind = (
            TargetKind.REVISION_COMPARISON
            if exact_base is not None
            else TargetKind.REPOSITORY_REVISION
        )
        target_parameters = (
            {"base": exact_base, "target": exact_revision}
            if exact_base is not None
            else {"revision": exact_revision}
        )
        return {
            "project": {
                "display_name": display_name,
                "scope_id": steps["CREATE_SCOPE"]["scope_id"],
                "scope_revision": int(
                    steps["CREATE_SCOPE"]["scope_revision"]
                ),
                "source_id": steps["REGISTER_SOURCE"]["source_id"],
                "source_revision": int(
                    steps["REGISTER_SOURCE"]["source_revision"]
                ),
                "binding_id": steps["BIND_SOURCE"]["binding_id"],
                "binding_revision": int(
                    steps["BIND_SOURCE"]["binding_revision"]
                ),
                "selected_paths": selected_paths,
                "target_kind": target_kind.value,
                "target_parameters": target_parameters,
            }
        }

    def _browser_chat(
        self, body: Mapping[str, object]
    ) -> dict[str, object]:
        project = _object(body, "project")
        target_kind = TargetKind(_text(project, "target_kind"))
        if target_kind not in {
            TargetKind.REPOSITORY_REVISION,
            TargetKind.REVISION_COMPARISON,
        }:
            raise ValueError("browser chat supports only repository or comparison targets")
        request_id = _bounded_text(body, "request_id", maximum=160)
        conversation_id = _bounded_text(
            body, "conversation_id", maximum=160
        )
        message = _bounded_text(body, "message", maximum=8000)
        original_request = _browser_original_request(
            message, body.get("history")
        )
        turn_number = _integer(body, "turn_number", default=1)
        scope_id = StableId(_text(project, "scope_id"))
        if getattr(
            self._runtime, "evidence_answer_preparation_configured", False
        ):
            request = self._runtime.prepare_evidence_answer_request(
                idempotency_key=IdempotencyKey(
                    f"browser-message:{request_id}"
                ),
                scope_id=scope_id,
                scope_revision=Revision(
                    _integer(project, "scope_revision", default=1)
                ),
                source_id=StableId(_text(project, "source_id")),
                source_revision=Revision(
                    _integer(project, "source_revision", default=1)
                ),
                binding_id=StableId(_text(project, "binding_id")),
                binding_revision=Revision(
                    _integer(project, "binding_revision", default=1)
                ),
                target_kind=target_kind,
                target_parameters=_string_mapping(
                    project, "target_parameters"
                ),
                original_request=original_request,
                classification="INTERNAL",
                caller_ref="browser-local-user",
                correlation_ref=CorrelationRef(
                    f"browser-request:{request_id}"
                ),
                max_steps=20,
                max_items_per_step=200,
                max_bytes_per_step=24_000,
            )
            answer = self._runtime.prepare_evidence_answer(request)
            supported_count = sum(
                section.kind is AnswerSectionKind.SUPPORTED
                for section in answer.draft.sections
            )
            return {
                "message": answer.draft.body,
                "response_kind": (
                    "EVIDENCE_COMPLETE"
                    if answer.unresolved_count == 0
                    else "EVIDENCE_PARTIAL"
                ),
                "claim_count": supported_count,
                "unresolved_count": answer.unresolved_count,
                "evidence_packet_id": answer.evidence_packet.packet_id.value,
                "reviewed": True,
                "sources": list(answer.sources),
            }
        current = self._runtime.knowledge.current_snapshot(scope_id)
        technical = {
            "conversation_ref": f"browser-conversation:{conversation_id}",
            "turn_ref": f"browser-turn:{conversation_id}:{turn_number}",
            "request_ref": f"browser-request:{request_id}",
            "idempotency_key": f"browser-message:{request_id}",
            "scope_id": scope_id.value,
            "snapshot_id": current.snapshot_id.value if current else None,
            "request": original_request,
            "caller_ref": "browser-local-user",
            "classification": "INTERNAL",
            "investigation": {
                "scope_revision": _integer(
                    project, "scope_revision", default=1
                ),
                "source_id": _text(project, "source_id"),
                "source_revision": _integer(
                    project, "source_revision", default=1
                ),
                "binding_id": _text(project, "binding_id"),
                "binding_revision": _integer(
                    project, "binding_revision", default=1
                ),
                "target_kind": target_kind.value,
                "target_parameters": _string_mapping(
                    project, "target_parameters"
                ),
                "max_steps": 12,
                "max_items_per_step": 200,
                "max_bytes_per_step": 16_000,
            },
        }
        answer = self._prepare_answer(technical)
        candidate = _object(answer, "candidate")
        review = _object(answer, "review")
        sources = _browser_answer_sources(self._runtime, answer)
        rendered, confirmed_count, unresolved_count = _browser_answer_projection(
            answer,
            message,
            sources=sources,
        )
        return {
            "message": rendered,
            "response_kind": _text(candidate, "response_kind"),
            "claim_count": confirmed_count,
            "unresolved_count": unresolved_count,
            "snapshot_id": _text(answer, "snapshot_id"),
            "reviewed": review.get("decision") == "APPROVED",
            "sources": list(sources),
        }

    def _prepare_answer(
        self, body: Mapping[str, object]
    ) -> dict[str, object]:
        idempotency_key = IdempotencyKey(_text(body, "idempotency_key"))
        scope_id = StableId(_text(body, "scope_id"))
        snapshot_value = body.get("snapshot_id")
        if snapshot_value is not None and not isinstance(snapshot_value, str):
            raise ValueError("snapshot_id must be a string or null")
        snapshot_id = StableId(snapshot_value) if snapshot_value else None
        original_request = _text(body, "request")
        caller_ref = _text(body, "caller_ref")
        classification = _optional_text(body, "classification", "INTERNAL")
        request_ref = _text(body, "request_ref")
        investigation = body.get("investigation")
        update_request = None
        if investigation is not None:
            if not isinstance(investigation, dict):
                raise ValueError("investigation must be an object")
            update_request = self._runtime.prepare_knowledge_update_request(
                idempotency_key=IdempotencyKey(
                    f"{idempotency_key.value}:knowledge-update"
                ),
                scope_id=scope_id,
                scope_revision=Revision(
                    _integer(investigation, "scope_revision", default=1)
                ),
                source_id=StableId(_text(investigation, "source_id")),
                source_revision=Revision(
                    _integer(investigation, "source_revision", default=1)
                ),
                binding_id=StableId(_text(investigation, "binding_id")),
                binding_revision=Revision(
                    _integer(investigation, "binding_revision", default=1)
                ),
                target_kind=TargetKind(_text(investigation, "target_kind")),
                target_parameters=_string_mapping(
                    investigation, "target_parameters"
                ),
                objective_description=(
                    f"Build formal knowledge required to answer: {original_request}"
                ),
                classification=classification,
                actor=caller_ref,
                correlation_ref=CorrelationRef(
                    f"task-investigation:{request_ref}"
                ),
                expected_current_snapshot_id=snapshot_id,
                max_steps=_integer(investigation, "max_steps", default=8),
                max_items_per_step=_integer(
                    investigation, "max_items_per_step", default=100
                ),
                max_bytes_per_step=_integer(
                    investigation, "max_bytes_per_step", default=256_000
                ),
                allowed_source_paths=_string_sequence(
                    investigation, "allowed_source_paths"
                ),
                required_source_paths=_string_sequence(
                    investigation, "required_source_paths"
                ),
            )
        result = self._runtime.prepare_task_answer(
            NaturalLanguageTaskRequest.create(
                conversation_ref=_text(body, "conversation_ref"),
                turn_ref=_text(body, "turn_ref"),
                request_ref=request_ref,
                idempotency_key=idempotency_key,
                original_request=original_request,
                caller_ref=caller_ref,
                classification=classification,
                scope_id=scope_id,
                snapshot_id=snapshot_id,
                knowledge_update_request=update_request,
            )
        )
        return authorized_task_answer_payload(result)

    def _read_json(self, environ) -> dict[str, object]:
        content_type = str(environ.get("CONTENT_TYPE", "")).split(";", 1)[0].strip().lower()
        if content_type != "application/json":
            raise ValueError("Content-Type must be application/json")
        raw_length = environ.get("CONTENT_LENGTH", "")
        try:
            length = int(raw_length)
        except (TypeError, ValueError) as exc:
            raise ValueError("Content-Length is required") from exc
        if length < 1 or length > self._max_request_bytes:
            raise ValueError("request body size is outside the accepted range")
        body = environ["wsgi.input"].read(length)
        try:
            value = json.loads(body)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("request body must be a JSON object") from exc
        if not isinstance(value, dict):
            raise ValueError("request body must be a JSON object")
        return value


def _need(value: object) -> KnowledgeNeed:
    if not isinstance(value, dict):
        raise ValueError("each Need must be an object")
    kinds = value.get("required_kinds")
    types = value.get("required_type_names")
    terms = value.get("required_terms")
    if not isinstance(kinds, list) or not all(isinstance(item, str) for item in kinds):
        raise ValueError("required_kinds must be a string array")
    if not isinstance(types, list) or not all(isinstance(item, str) for item in types):
        raise ValueError("required_type_names must be a string array")
    if not isinstance(terms, list) or not all(isinstance(item, str) for item in terms):
        raise ValueError("required_terms must be a string array")
    return KnowledgeNeed(
        need_id=_text(value, "need_id"),
        question=_text(value, "question"),
        required_kinds=tuple(KnowledgeObjectKind(item) for item in kinds),
        required_type_names=tuple(types),
        required_terms=tuple(terms),
        minimum_support_count=_integer(value, "minimum_support_count", default=1),
    )


def _text(value: Mapping[str, object], key: str) -> str:
    item = value.get(key)
    if not isinstance(item, str) or not item or item != item.strip():
        raise ValueError(f"{key} must be a non-empty string")
    return item


def _bounded_text(
    value: Mapping[str, object], key: str, *, maximum: int
) -> str:
    item = _text(value, key)
    if len(item) > maximum:
        raise ValueError(f"{key} is too long")
    return item


def _object(
    value: Mapping[str, object], key: str
) -> dict[str, object]:
    item = value.get(key)
    if not isinstance(item, dict):
        raise ValueError(f"{key} must be an object")
    return item


def _optional_text(value: Mapping[str, object], key: str, default: str) -> str:
    return _text(value, key) if key in value else default


def _integer(value: Mapping[str, object], key: str, *, default: int) -> int:
    item = value.get(key, default)
    if not isinstance(item, int) or isinstance(item, bool) or item < 1:
        raise ValueError(f"{key} must be a positive integer")
    return item


def _string_mapping(value: Mapping[str, object], key: str) -> dict[str, str]:
    item = value.get(key)
    if not isinstance(item, dict) or not all(
        isinstance(name, str) and isinstance(content, str) for name, content in item.items()
    ):
        raise ValueError(f"{key} must be a string-to-string object")
    return item


def _string_sequence(
    value: Mapping[str, object], key: str
) -> tuple[str, ...]:
    item = value.get(key, ())
    if not isinstance(item, (list, tuple)) or not all(
        isinstance(content, str) and content and content == content.strip()
        for content in item
    ):
        raise ValueError(f"{key} must be a string array")
    return tuple(item)


def _raw(value: str, content_type: str) -> RawHttpResponse:
    return RawHttpResponse(value.encode("utf-8"), content_type)


def _browser_original_request(message: str, history: object) -> str:
    if history is not None and (
        not isinstance(history, list) or len(history) > 6
    ):
        raise ValueError("history must contain at most six messages")
    lines: list[str] = []
    total = 0
    for item in history or ():
        if not isinstance(item, dict) or set(item) != {"role", "content"}:
            raise ValueError("each history item must contain role and content")
        role = item.get("role")
        content = item.get("content")
        if role not in {"user", "assistant"} or not isinstance(content, str):
            raise ValueError("history role or content is invalid")
        content = content.strip()
        if not content or len(content) > 8000:
            raise ValueError("history content is empty or too long")
        if role != "user":
            continue
        total += len(content)
        if total > 24_000:
            raise ValueError("history is too long")
        lines.append(f"用户先前问题：{content}")
    context = ""
    if lines:
        context = (
            "以下先前问题只用于理解当前问题中的指代，不属于本轮回答目标，"
            "也不作为源码事实：\n"
            + "\n".join(lines[-3:])
            + "\n"
        )
    response_language = (
        "回答语言：简体中文。\n"
        if _contains_cjk(message)
        else "Response language: English.\n"
    )
    return (
        context
        + response_language
        + f"当前问题：{message}\n"
        + "回答约束：忠实回答当前问题，使用与当前问题相同的语言。"
    )


def _browser_answer_sources(
    runtime: ApplicationRuntime, answer: Mapping[str, object]
) -> tuple[str, ...]:
    candidate = _object(answer, "candidate")
    claims = candidate.get("claims")
    if not isinstance(claims, list):
        raise ValueError("candidate claims must be an array")
    sources: list[str] = []
    snapshot_id: StableId | None = None
    for claim in claims:
        if not isinstance(claim, dict):
            raise ValueError("candidate claim must be an object")
        reference = claim.get("formal_reference")
        if not isinstance(reference, str):
            continue
        if snapshot_id is None:
            snapshot_id = StableId(_text(answer, "snapshot_id"))
        for locator in runtime.knowledge.source_locators(
            snapshot_id, StableId(reference)
        ):
            if locator not in sources:
                sources.append(locator)
            if len(sources) == 24:
                return tuple(sources)
    return tuple(sources)


def _browser_answer_projection(
    answer: Mapping[str, object],
    user_message: str,
    *,
    sources: tuple[str, ...] = (),
) -> tuple[str, int, int]:
    candidate = _object(answer, "candidate")
    claims = candidate.get("claims")
    if not isinstance(claims, list):
        raise ValueError("candidate claims must be an array")
    requirement = _object(answer, "requirement")
    needs = requirement.get("needs", [])
    questions = {
        item["need_id"]: item["question"]
        for item in needs
        if isinstance(item, dict)
        and isinstance(item.get("need_id"), str)
        and isinstance(item.get("question"), str)
    }
    assessment = _object(answer, "assessment")
    assessment_items = assessment.get("items", [])
    disclosures = {
        item["need_id"]: item.get("gap")
        for item in assessment_items
        if isinstance(item, dict) and isinstance(item.get("need_id"), str)
    }
    confirmed_by_need: dict[str, list[str]] = {}
    limitations_by_need: dict[str, list[str]] = {}
    unresolved: list[tuple[str, str]] = []
    for claim in claims:
        if not isinstance(claim, dict):
            raise ValueError("candidate claim must be an object")
        kind = claim.get("kind")
        text = claim.get("text")
        need_id = claim.get("need_id")
        if (
            kind == "FORMAL_KNOWLEDGE"
            and isinstance(text, str)
            and isinstance(need_id, str)
        ):
            bucket = confirmed_by_need.setdefault(need_id, [])
            if text not in bucket:
                bucket.append(text)
        elif (
            kind == "APPLICATION_LIMITATION"
            and isinstance(text, str)
            and isinstance(need_id, str)
        ):
            bucket = limitations_by_need.setdefault(need_id, [])
            if text not in bucket:
                bucket.append(text)
        elif kind == "KNOWLEDGE_GAP" and isinstance(need_id, str):
            question = questions.get(need_id, "本问题")
            disclosure = disclosures.get(need_id)
            if not isinstance(disclosure, str) or not disclosure.strip():
                disclosure = "当前固定版本中还没有取得足够的直接依据。"
            item = (question, disclosure)
            if item not in unresolved:
                unresolved.append(item)
    chinese = _contains_cjk(user_message)
    if not confirmed_by_need and not unresolved:
        return _text(candidate, "body"), 0, 0
    sections: list[str] = []
    shown_claims: set[str] = set()
    confirmed_sections: list[str] = []
    ordered_need_ids = list(questions)
    ordered_need_ids.extend(
        need_id
        for need_id in (*confirmed_by_need, *limitations_by_need)
        if need_id not in questions
    )
    for need_id in ordered_need_ids:
        facts = [
            item
            for item in confirmed_by_need.get(need_id, ())
            if item not in shown_claims
        ]
        all_need_facts = confirmed_by_need.get(need_id, ())
        notes = [
            item
            for item in limitations_by_need.get(need_id, ())
            if not any(
                item.casefold() in fact.casefold()
                for fact in all_need_facts
            )
        ]
        if not facts and not notes:
            continue
        shown_claims.update(facts)
        question = questions.get(
            need_id,
            "相关问题" if chinese else "Related question",
        )
        lines = [f"{len(confirmed_sections) + 1}. {question}"]
        lines.extend(
            f"   - {_localized_claim_text(item, chinese)}" for item in facts
        )
        note_label = "说明：" if chinese else "Note: "
        lines.extend(
            f"   - {note_label}{_localized_gap_text(item, chinese)}"
            for item in notes
        )
        confirmed_sections.append("\n".join(lines))
    if confirmed_sections:
        heading = "已确认" if chinese else "Confirmed"
        sections.append(heading + "\n" + "\n".join(confirmed_sections))
    if unresolved:
        heading = "尚未确认" if chinese else "Not yet verified"
        separator = "：" if chinese else ": "
        sections.append(
            heading + "\n" + "\n".join(
                f"- {question}{separator}{_localized_gap_text(disclosure, chinese)}"
                for question, disclosure in unresolved
            )
        )
    if sources:
        heading = "源码位置" if chinese else "Source locations"
        sections.append(heading + "\n" + "\n".join(f"- {item}" for item in sources))
    return "\n\n".join(sections), len(shown_claims), len(unresolved)


def _contains_cjk(value: str) -> bool:
    return any("\u4e00" <= character <= "\u9fff" for character in value)


def _localized_claim_text(value: str, chinese: bool) -> str:
    if not chinese:
        return value
    return value.replace(" Condition: ", " 条件：").replace(
        " Limitation: ", " 限制："
    )


def _localized_gap_text(value: str, chinese: bool) -> str:
    if not chinese:
        return value
    replacements = (
        ("读取集合", "本轮已读取的源码"),
        ("形式记录", "已复核依据"),
        ("formal records", "已复核依据"),
        ("authorized evidence", "已复核依据"),
    )
    rendered = value
    for source, target in replacements:
        rendered = rendered.replace(source, target)
    return rendered


def _domain_status(code: ErrorCode) -> str:
    if code in {
        ErrorCode.REVISION_CONFLICT,
        ErrorCode.IDEMPOTENCY_MISMATCH,
        ErrorCode.MANAGEMENT_STATE_CONFLICT,
    }:
        return "409 Conflict"
    if code in {
        ErrorCode.SCOPE_NOT_FOUND,
        ErrorCode.DATASOURCE_NOT_FOUND,
        ErrorCode.BINDING_NOT_FOUND,
    }:
        return "404 Not Found"
    if code is ErrorCode.LIVE_INTEGRATION_HELD:
        return "503 Service Unavailable"
    return "400 Bad Request"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="swm-http-evaluation",
        description="Software World Model HTTP evaluation API",
    )
    parser.add_argument("--database", required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument(
        "--request-timeout-seconds",
        type=float,
        default=15.0,
        help="maximum idle time while reading or writing one local HTTP request",
    )
    parser.add_argument(
        "--enable-activated-model",
        action="store_true",
        help="load the currently evaluated and explicitly activated model strategy",
    )
    parser.add_argument("--conformance-result")
    parser.add_argument("--activation-environment")
    arguments = parser.parse_args(argv)
    if arguments.host not in {"127.0.0.1", "::1", "localhost"}:
        parser.error("the unauthenticated acceptance API may bind only to loopback")
    if arguments.request_timeout_seconds <= 0:
        parser.error("--request-timeout-seconds must be positive")
    database_path = Path(arguments.database)
    database_path.parent.mkdir(parents=True, exist_ok=True)
    with SqliteDatabase(database_path) as database:
        if arguments.enable_activated_model:
            if not arguments.conformance_result or not arguments.activation_environment:
                parser.error(
                    "--enable-activated-model requires --conformance-result and "
                    "--activation-environment"
                )
            assembly = build_activated_application_runtime(
                database=database,
                conformance_result_path=arguments.conformance_result,
                activation_scope={
                    "environment": arguments.activation_environment
                },
            )
            application = JsonHttpApplication(
                assembly.runtime,
                live_provider_configured=True,
            )
        else:
            application = JsonHttpApplication(ApplicationRuntime(database))
        with make_server(
            arguments.host,
            arguments.port,
            application,
            handler_class=LoopbackWsgiRequestHandler,
        ) as server:
            server.request_timeout_seconds = arguments.request_timeout_seconds
            server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
