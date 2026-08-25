"""Loopback-only Web adapter for the ITER-010 Engineering Chat access slice."""

from __future__ import annotations

import json
import re

from software_world_model.application_services.engineering_conversation import (
    ENGINEERING_CHAT_EXPERIENCE,
    ENGINEERING_CHAT_PROTOCOL,
    ConversationNotFoundError,
    EngineeringChatBinding,
    EngineeringConversationMessage,
    EngineeringConversationSnapshot,
    EngineeringConversationTurn,
    InMemoryEngineeringConversationService,
    RuntimeCapabilityStatus,
)
from software_world_model.cross_cutting import (
    DomainError,
    ErrorCode,
    Revision,
    StableId,
)

from .engineering_chat_browser_ui import (
    ENGINEERING_CHAT_BROWSER_JAVASCRIPT,
    ENGINEERING_CHAT_BROWSER_HTML,
)


ENGINEERING_CHAT_LOOPBACK_ORIGIN = "http://127.0.0.1:8765"
ENGINEERING_CHAT_MAXIMUM_REQUEST_BYTES = 65_536

_CONVERSATION_ROUTE = re.compile(
    r"^/v1/engineering-chat/conversations/"
    r"(?P<conversation>conversation_[0-9a-f]{32})$"
)
_TURN_ROUTE = re.compile(
    r"^/v1/engineering-chat/conversations/"
    r"(?P<conversation>conversation_[0-9a-f]{32})/turns$"
)


class EngineeringChatBrowserApplication:
    """WSGI surface; the trusted launcher owns the exact listener binding."""

    maximum_request_bytes = ENGINEERING_CHAT_MAXIMUM_REQUEST_BYTES

    def __init__(
        self, service: InMemoryEngineeringConversationService
    ) -> None:
        self._service = service

    def __call__(self, environ, start_response):
        try:
            self._require_loopback(environ)
            method = str(environ.get("REQUEST_METHOD", "GET")).upper()
            path = str(environ.get("PATH_INFO", "/"))
            if method == "GET" and path == "/":
                return self._respond(
                    start_response,
                    "200 OK",
                    ENGINEERING_CHAT_BROWSER_HTML.encode("utf-8"),
                    "text/html; charset=utf-8",
                )
            if method == "GET" and path == "/assets/engineering-chat.js":
                return self._respond(
                    start_response,
                    "200 OK",
                    ENGINEERING_CHAT_BROWSER_JAVASCRIPT.encode("utf-8"),
                    "text/javascript; charset=utf-8",
                )
            if method == "GET" and path == "/health":
                return self._json(start_response, "200 OK", self.health())
            if method == "POST" and path == "/v1/engineering-chat/conversations":
                self._require_same_origin_json(environ)
                payload = self._read_json(environ)
                if payload:
                    raise DomainError(
                        ErrorCode.INVALID_ARGUMENT,
                        "new Conversation request must be an empty JSON object",
                    )
                snapshot = self._service.create_conversation()
                return self._json(
                    start_response,
                    "201 Created",
                    _snapshot_view(snapshot, self._service.binding),
                )
            turn_match = _TURN_ROUTE.fullmatch(path)
            if method == "POST" and turn_match is not None:
                self._require_same_origin_json(environ)
                payload = self._read_json(environ)
                if set(payload) != {"conversation_revision", "message"}:
                    raise DomainError(
                        ErrorCode.INVALID_ARGUMENT,
                        "Turn request requires exactly conversation_revision and message",
                    )
                revision = payload["conversation_revision"]
                message = payload["message"]
                if type(revision) is not int or revision < 1 or not isinstance(
                    message, str
                ):
                    raise DomainError(
                        ErrorCode.INVALID_ARGUMENT,
                        "Turn revision must be positive and message must be a string",
                    )
                submission = self._service.submit_turn(
                    conversation_id=StableId(turn_match.group("conversation")),
                    expected_revision=Revision(revision),
                    message=message,
                )
                projection = _snapshot_view(
                    submission.snapshot, self._service.binding
                )
                projection["submitted_turn"] = _turn_view(submission.turn)
                return self._json(start_response, "200 OK", projection)
            conversation_match = _CONVERSATION_ROUTE.fullmatch(path)
            if method == "GET" and conversation_match is not None:
                snapshot = self._service.get_conversation(
                    StableId(conversation_match.group("conversation"))
                )
                return self._json(
                    start_response,
                    "200 OK",
                    _snapshot_view(snapshot, self._service.binding),
                )
            return self._json(
                start_response,
                "404 Not Found",
                {"error": "NOT_FOUND", "message": "route not found"},
            )
        except ConversationNotFoundError as exc:
            return self._json(
                start_response,
                "404 Not Found",
                {
                    "error": "CONVERSATION_NOT_FOUND",
                    "message": str(exc),
                },
            )
        except DomainError as exc:
            if exc.code is ErrorCode.CONTROL_STATE_DENIED:
                status = "403 Forbidden"
            elif exc.code is ErrorCode.REVISION_CONFLICT:
                status = "409 Conflict"
            elif exc.code is ErrorCode.INVALID_ARGUMENT:
                status = "400 Bad Request"
            else:
                status = "409 Conflict"
            return self._json(
                start_response,
                status,
                {
                    "error": exc.code.value,
                    "message": exc.message,
                    "details": dict(exc.details),
                },
            )
        except (ValueError, json.JSONDecodeError, UnicodeDecodeError):
            return self._json(
                start_response,
                "400 Bad Request",
                {"error": "INVALID_JSON", "message": "request JSON is invalid"},
            )

    def health(self) -> dict[str, object]:
        binding = self._service.binding
        conversation_count, turn_count = self._service.statistics()
        return {
            "schema": "ENGINEERING_CHAT_HEALTH@1",
            "status": "READY",
            "mode": "ENGINEERING_CHAT",
            "protocol": ENGINEERING_CHAT_PROTOCOL,
            "experience": ENGINEERING_CHAT_EXPERIENCE,
            "implementation_scope": self._service.implementation_scope,
            "quality": "NOT_ACCEPTED",
            "environment": "ALPHA_EVALUATION_ONLY",
            "production": "NOT_PRODUCTION",
            "production_activation": "NOT_EXECUTED",
            "listener": {
                "origin": ENGINEERING_CHAT_LOOPBACK_ORIGIN,
                "authentication": "NONE_LOOPBACK_ONLY",
            },
            "product": {
                "version": binding.product_version,
                "revision": binding.product_revision,
            },
            "project": {
                "name": binding.project_name,
                "repository_revision": binding.repository_revision,
                "binding_digest": binding.digest.value,
                "excluded_source_paths": list(binding.excluded_source_paths),
            },
            "world_model": {
                "status": binding.world_model_status.value,
                "authority_digest": (
                    binding.world_model_authority_digest.value
                    if binding.world_model_authority_digest is not None
                    else None
                ),
            },
            "source": {
                "status": binding.source_access_status.value,
                "profile_ref": binding.source_profile_ref,
                "read_only": True,
                "dispatch_enabled": (
                    self._service.semantic_agent_execution
                    and binding.source_access_status is RuntimeCapabilityStatus.READY
                ),
            },
            "provider": {
                "status": binding.provider_status.value,
                "route_ref": binding.provider_route_ref,
                "external_dispatch": self._service.semantic_agent_execution,
                "qualification": (
                    "READY"
                    if self._service.semantic_agent_execution
                    else "NOT_EXECUTED"
                ),
            },
            "capabilities": {
                "message_history": True,
                "new_conversation": True,
                "server_owned_conversation_turn_context": True,
                "turn_submission": True,
                "failed_turn_keeps_conversation_active": True,
                "new_conversation_context_isolation": True,
                "semantic_agent_execution": self._service.semantic_agent_execution,
            },
            "storage": "PROCESS_MEMORY_ONLY",
            "known_limitations": list(binding.known_limitations),
            "statistics": {
                "conversation_count": conversation_count,
                "turn_count": turn_count,
                "provider_dispatch_count": self._service.provider_dispatch_count(),
            },
        }

    def _read_json(self, environ) -> dict[str, object]:
        raw_length = str(environ.get("CONTENT_LENGTH", "0") or "0")
        try:
            length = int(raw_length)
        except ValueError as exc:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT, "Content-Length is invalid"
            ) from exc
        if length < 1 or length > self.maximum_request_bytes:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "request body is empty or exceeds the local Chat Access limit",
            )
        stream = environ.get("wsgi.input")
        if stream is None:
            raise ValueError("request body is unavailable")
        raw = stream.read(length)
        if not isinstance(raw, bytes) or len(raw) != length:
            raise ValueError("request body is incomplete")
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_unique_json_object,
        )
        if not isinstance(value, dict):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT, "request JSON must be an object"
            )
        return value

    @staticmethod
    def _require_loopback(environ) -> None:
        remote = str(environ.get("REMOTE_ADDR", ""))
        host = str(environ.get("HTTP_HOST", ""))
        if remote != "127.0.0.1" or host != "127.0.0.1:8765":
            raise DomainError(
                ErrorCode.CONTROL_STATE_DENIED,
                "Engineering Chat accepts only the fixed 127.0.0.1:8765 listener",
            )

    @staticmethod
    def _require_same_origin_json(environ) -> None:
        origin = str(environ.get("HTTP_ORIGIN", ""))
        content_type = str(environ.get("CONTENT_TYPE", ""))
        fetch_site = str(environ.get("HTTP_SEC_FETCH_SITE", ""))
        if (
            origin != ENGINEERING_CHAT_LOOPBACK_ORIGIN
            or content_type.casefold() != "application/json"
            or (fetch_site and fetch_site != "same-origin")
        ):
            raise DomainError(
                ErrorCode.CONTROL_STATE_DENIED,
                "Engineering Chat mutation requires same-origin application/json",
            )

    @staticmethod
    def _json(start_response, status: str, value: object):
        return EngineeringChatBrowserApplication._respond(
            start_response,
            status,
            json.dumps(
                value,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8"),
            "application/json; charset=utf-8",
        )

    @staticmethod
    def _respond(start_response, status: str, body: bytes, content_type: str):
        headers = [
            ("Content-Type", content_type),
            ("Content-Length", str(len(body))),
            ("Cache-Control", "no-store"),
            ("X-Content-Type-Options", "nosniff"),
            ("X-Frame-Options", "DENY"),
            ("Referrer-Policy", "no-referrer"),
            ("Cross-Origin-Resource-Policy", "same-origin"),
            (
                "Permissions-Policy",
                "camera=(), microphone=(), geolocation=(), payment=()",
            ),
            (
                "Content-Security-Policy",
                "default-src 'self'; style-src 'self' 'unsafe-inline'; "
                "script-src 'self'; connect-src 'self'; img-src 'none'; "
                "object-src 'none'; base-uri 'none'; form-action 'self'; "
                "frame-ancestors 'none'",
            ),
        ]
        start_response(status, headers)
        return [body]


def _snapshot_view(
    snapshot: EngineeringConversationSnapshot,
    binding: EngineeringChatBinding,
) -> dict[str, object]:
    conversation = snapshot.conversation
    return {
        "schema": "ENGINEERING_CHAT_CONVERSATION_PROJECTION@1",
        "protocol": ENGINEERING_CHAT_PROTOCOL,
        "experience": ENGINEERING_CHAT_EXPERIENCE,
        "quality": "NOT_ACCEPTED",
        "production": "NOT_PRODUCTION",
        "conversation": {
            "conversation_id": conversation.conversation_id.value,
            "revision": conversation.revision.value,
            "state": conversation.state.value,
            "binding_digest": conversation.binding_digest.value,
            "context_digest": conversation.context_digest.value,
            "turn_count": len(snapshot.turns),
            "message_count": len(snapshot.messages),
            "created_at": _time(conversation.created_at),
            "revised_at": _time(conversation.revised_at),
            "digest": conversation.digest.value,
        },
        "context": {
            "work_state_revision": snapshot.context.work_state_revision.value,
            "included_user_message_ids": [
                item.value for item in snapshot.context.included_user_message_ids
            ],
            "accepted_correction_message_ids": [
                item.value
                for item in snapshot.context.accepted_correction_message_ids
            ],
            "reviewed_conclusion_refs": list(
                snapshot.context.reviewed_conclusion_refs
            ),
            "superseded_conclusion_refs": list(
                snapshot.context.superseded_conclusion_refs
            ),
            "work_state_ref": snapshot.context.work_state_ref,
            "work_state_digest": (
                snapshot.context.work_state_digest.value
                if snapshot.context.work_state_digest is not None
                else None
            ),
            "reducer_status": snapshot.context.reducer_status,
            "digest": snapshot.context.digest.value,
        },
        "messages": [_message_view(item) for item in snapshot.messages],
        "turns": [_turn_view(item) for item in snapshot.turns],
        "project": {
            "name": binding.project_name,
            "repository_revision": binding.repository_revision,
        },
        "provider_status": binding.provider_status.value,
        "known_limitations": list(binding.known_limitations),
    }


def _message_view(message: EngineeringConversationMessage) -> dict[str, object]:
    return {
        "message_id": message.message_id.value,
        "turn_id": message.turn_id.value,
        "sequence": message.sequence,
        "role": message.role.value,
        "kind": message.kind.value,
        "content": message.content,
        "created_at": _time(message.created_at),
        "digest": message.digest.value,
    }


def _turn_view(turn: EngineeringConversationTurn) -> dict[str, object]:
    return {
        "turn_id": turn.turn_id.value,
        "result_id": turn.result_id.value,
        "sequence": turn.sequence,
        "state": turn.state.value,
        "conversation_revision_before": turn.conversation_revision_before.value,
        "conversation_revision_after": turn.conversation_revision_after.value,
        "context_digest_before": turn.context_digest_before.value,
        "context_digest_after": turn.context_digest_after.value,
        "request_digest": turn.request_digest.value,
        "result_digest": turn.digest.value,
        "failure": {
            "code": turn.failure_code,
            "message": turn.failure_message,
        },
        "evidence_package_ref": turn.evidence_package_ref,
        "answer_ref": turn.answer_ref,
        "review_ref": turn.review_ref,
        "delivery_authorization_ref": turn.delivery_authorization_ref,
        "work_state_ref": turn.work_state_ref,
        "work_state_revision": (
            turn.work_state_revision.value
            if turn.work_state_revision is not None
            else None
        ),
        "work_state_digest": (
            turn.work_state_digest.value
            if turn.work_state_digest is not None
            else None
        ),
        "delivery_state": turn.delivery_state,
        "provider_dispatch_count": turn.provider_dispatch_count,
        "model_dispatch_receipt_refs": list(
            turn.model_dispatch_receipt_refs
        ),
        "provider_failure_classification": (
            turn.provider_failure_classification.value
            if turn.provider_failure_classification is not None
            else None
        ),
        "provider_failure_code": turn.provider_failure_code,
        "provider_route_receipt_ref": turn.provider_route_receipt_ref,
        "provider_attempt_receipt_refs": list(
            turn.provider_attempt_receipt_refs
        ),
        "fallback_provider_attempt_count": (
            turn.fallback_provider_attempt_count
        ),
        "provider_duplicate_cost_risk": turn.provider_duplicate_cost_risk,
        "retry_count": turn.retry_count,
        "quality_status": turn.quality_status,
        "production_activation": turn.production_activation,
        "created_at": _time(turn.created_at),
        "completed_at": _time(turn.completed_at),
    }


def _unique_json_object(
    pairs: list[tuple[str, object]],
) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON field: {key}")
        value[key] = item
    return value


def _time(value) -> str:
    return value.isoformat(timespec="microseconds").replace("+00:00", "Z")


__all__ = [
    "ENGINEERING_CHAT_LOOPBACK_ORIGIN",
    "ENGINEERING_CHAT_MAXIMUM_REQUEST_BYTES",
    "EngineeringChatBrowserApplication",
]
