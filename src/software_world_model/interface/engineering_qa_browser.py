"""Loopback-targeted WSGI surface for the ITER-010 Engineering QA preview.

The adapter does not open a listener or dispatch a model.  A launcher must bind
it to ``127.0.0.1`` and inject already-authorized local application roles.  This
keeps deterministic development and any later live disclosure authorization
separate.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import json
import re
from threading import Lock
from typing import Protocol, Sequence

from software_world_model.application_services.engineering_question_answering import (
    ENGINEERING_QA_MODE,
    ENGINEERING_QA_PROTOCOL,
    EngineeringQuestionAnsweringService,
    EngineeringQuestionExecutionResult,
    EngineeringQuestionRequest,
    EngineeringQuestionResourceLimits,
    SourceReadOperation,
)
from software_world_model.cross_cutting import Digest, DomainError, ErrorCode, StableId
from software_world_model.ai_infrastructure.engineering_question_model_source import (
    EngineeringQuestionModelConfiguration,
    EngineeringQuestionRunDisclosureAuthorization,
)

from .engineering_qa_browser_ui import ENGINEERING_QA_BROWSER_HTML


_CITATION_ROUTE = re.compile(
    r"^/v1/engineering-qa/results/(?P<result>[a-z][a-z0-9_]{1,31}_[0-9a-f]{32})"
    r"/citations/(?P<entry>[a-z][a-z0-9_]{1,31}_[0-9a-f]{32})$"
)


class EngineeringQuestionRequestFactory(Protocol):
    def create(
        self, *, request_ref: str, original_question: str
    ) -> EngineeringQuestionRequest: ...


@dataclass(frozen=True, slots=True)
class ExactAuthorizedEngineeringQuestionRequestFactory:
    """Expose one already sealed Request; arbitrary browser input cannot widen it."""

    request: EngineeringQuestionRequest
    run_authorization: EngineeringQuestionRunDisclosureAuthorization

    def __post_init__(self) -> None:
        if (
            self.request.digest != self.run_authorization.request_digest
            or self.request.provider_disclosure_policy
            != self.run_authorization.provider_disclosure_policy_ref
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "prepared Engineering QA Request does not match its run authorization",
            )

    def create(
        self, *, request_ref: str, original_question: str
    ) -> EngineeringQuestionRequest:
        if (
            request_ref != self.request.request_ref
            or original_question != self.request.original_question
        ):
            raise DomainError(
                ErrorCode.CONTROL_STATE_DENIED,
                "browser input is outside the exact prepared Engineering QA Request",
            )
        return self.request


@dataclass(frozen=True, slots=True)
class EngineeringQuestionWebRuntimeStatus:
    external_provider_dispatch: bool
    provider_type: str | None
    model_ref: str | None
    provider_configuration_fingerprint: Digest | None
    qualification_ref: str | None
    secret_reference: str | None
    run_authorization_digest: Digest | None
    evaluation_subject_digest: Digest | None
    prepared_request_ref: str | None
    prepared_question: str | None

    @classmethod
    def local(cls) -> "EngineeringQuestionWebRuntimeStatus":
        return cls(False, None, None, None, None, None, None, None, None, None)

    @classmethod
    def authorized(
        cls,
        *,
        request: EngineeringQuestionRequest,
        configuration: EngineeringQuestionModelConfiguration,
        run_authorization: EngineeringQuestionRunDisclosureAuthorization,
        at,
    ) -> "EngineeringQuestionWebRuntimeStatus":
        run_authorization.require_current(configuration=configuration, at=at)
        if (
            request.digest != run_authorization.request_digest
            or configuration.digest != run_authorization.provider_binding_digest
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Engineering QA Web runtime does not match its exact Request and Provider grant",
            )
        return cls(
            True,
            configuration.provider_type,
            configuration.model_ref,
            configuration.provider_configuration_fingerprint,
            configuration.qualification_ref,
            configuration.secret_reference,
            run_authorization.digest,
            run_authorization.evaluation_subject_digest,
            request.request_ref,
            request.original_question,
        )

    def model_view(self) -> dict[str, object]:
        return {
            "external_provider_dispatch": self.external_provider_dispatch,
            "provider_type": self.provider_type,
            "model_ref": self.model_ref,
            "provider_configuration_fingerprint": (
                self.provider_configuration_fingerprint.value
                if self.provider_configuration_fingerprint
                else None
            ),
            "qualification_ref": self.qualification_ref,
            "secret_reference": self.secret_reference,
            "run_authorization_digest": (
                self.run_authorization_digest.value
                if self.run_authorization_digest
                else None
            ),
            "evaluation_subject_digest": (
                self.evaluation_subject_digest.value
                if self.evaluation_subject_digest
                else None
            ),
            "prepared_request_id": self.prepared_request_ref,
            "prepared_question": self.prepared_question,
            "request_retry_allowed": False,
            "provider_switch_after_dispatch_allowed": False,
        }


@dataclass(frozen=True, slots=True)
class FixedEngineeringQuestionRequestFactory:
    """Freeze one exact local product subject before any question is accepted."""

    response_language: str
    repository_id: StableId
    binding_id: StableId
    repository_revision: str
    source_profile_ref: str
    source_profile_digest: Digest
    world_model_read_authority_digest: Digest
    source_allowlist: tuple[str, ...]
    registered_operations: tuple[SourceReadOperation, ...] = (
        SourceReadOperation.SEARCH,
        SourceReadOperation.READ,
        SourceReadOperation.PARSE,
    )
    provider_disclosure_policy: str = "NO_EXTERNAL_DISCLOSURE"
    limits: EngineeringQuestionResourceLimits = EngineeringQuestionResourceLimits()

    def __post_init__(self) -> None:
        if self.provider_disclosure_policy != "NO_EXTERNAL_DISCLOSURE":
            raise DomainError(
                ErrorCode.CONTROL_STATE_DENIED,
                "the local Engineering QA preview cannot authorize external disclosure",
            )

    def create(
        self, *, request_ref: str, original_question: str
    ) -> EngineeringQuestionRequest:
        return EngineeringQuestionRequest.create(
            request_ref=request_ref,
            original_question=original_question,
            response_language=self.response_language,
            repository_id=self.repository_id,
            binding_id=self.binding_id,
            repository_revision=self.repository_revision,
            source_profile_ref=self.source_profile_ref,
            source_profile_digest=self.source_profile_digest,
            world_model_read_authority_digest=self.world_model_read_authority_digest,
            source_allowlist=self.source_allowlist,
            registered_operations=self.registered_operations,
            provider_disclosure_policy=self.provider_disclosure_policy,
            limits=self.limits,
        )


class EngineeringQuestionWebProduct(Protocol):
    def health(self) -> dict[str, object]: ...

    def answer(self, *, request_ref: str, question: str) -> dict[str, object]: ...

    def citation(
        self, *, result_id: StableId, entry_id: StableId
    ) -> dict[str, object]: ...


@dataclass(frozen=True, slots=True)
class _StoredWebResult:
    request_ref: str
    question: str
    result: EngineeringQuestionExecutionResult
    page: dict[str, object]
    citations: dict[StableId, dict[str, object]]


class InMemoryEngineeringQuestionWebProduct:
    """Request-scoped Slice 1 product composition with result-scoped citations."""

    def __init__(
        self,
        *,
        service: EngineeringQuestionAnsweringService,
        request_factory: EngineeringQuestionRequestFactory,
        runtime_status: EngineeringQuestionWebRuntimeStatus | None = None,
    ) -> None:
        self._service = service
        self._request_factory = request_factory
        self._runtime_status = runtime_status or EngineeringQuestionWebRuntimeStatus.local()
        if self._runtime_status.external_provider_dispatch and not isinstance(
            request_factory, ExactAuthorizedEngineeringQuestionRequestFactory
        ):
            raise DomainError(
                ErrorCode.CONTROL_STATE_DENIED,
                "live Engineering QA Web requires one exact authorized Request factory",
            )
        self._lock = Lock()
        self._by_request: dict[str, _StoredWebResult] = {}
        self._by_result: dict[StableId, _StoredWebResult] = {}

    def health(self) -> dict[str, object]:
        return {
            "status": "READY",
            "mode": ENGINEERING_QA_MODE,
            "protocol": ENGINEERING_QA_PROTOCOL,
            "environment": "DIRECTION_PREVIEW",
            "acceptance": "NOT_ACCEPTANCE",
            "production": "NOT_PRODUCTION",
            "production_activation": "NOT_EXECUTED",
            "listener_requirement": "127.0.0.1",
            "authentication": "NONE_LOOPBACK_ONLY",
            **self._runtime_status.model_view(),
        }

    def answer(self, *, request_ref: str, question: str) -> dict[str, object]:
        with self._lock:
            existing = self._by_request.get(request_ref)
            if existing is not None:
                if existing.question != question:
                    raise DomainError(
                        ErrorCode.IDEMPOTENCY_MISMATCH,
                        "Engineering QA request ID was reused with another question",
                    )
                return deepcopy(existing.page)
            # Keep the local preview request serialized so an idempotent replay can
            # never duplicate a future model dispatch. Slice 2 owns durable recovery.
            request = self._request_factory.create(
                request_ref=request_ref, original_question=question
            )
            result = self._service.answer(request)
            page, citations = self._present(result)
            stored = _StoredWebResult(
                request_ref=request_ref,
                question=question,
                result=result,
                page=page,
                citations=citations,
            )
            self._by_request[request_ref] = stored
            self._by_result[result.result_id] = stored
            return deepcopy(page)

    def citation(
        self, *, result_id: StableId, entry_id: StableId
    ) -> dict[str, object]:
        with self._lock:
            stored = self._by_result.get(result_id)
        if stored is None:
            raise DomainError(
                ErrorCode.SOURCE_TARGET_NOT_FOUND,
                "Engineering QA Result is unavailable",
            )
        citation = stored.citations.get(entry_id)
        if citation is None:
            raise DomainError(
                ErrorCode.SOURCE_TARGET_NOT_FOUND,
                "Citation is not allowlisted by the authorized answer",
            )
        return deepcopy(citation)

    def _present(
        self,
        result: EngineeringQuestionExecutionResult,
    ) -> tuple[dict[str, object], dict[StableId, dict[str, object]]]:
        page = result.model_view()
        citations: dict[StableId, dict[str, object]] = {}
        public_citations: list[dict[str, object]] = []
        package = result.current_package
        authorized = result.authorized_answer
        if package is not None and authorized is not None:
            support = {item.entry_id: item for item in package.support_citation}
            for entry_id in authorized.citation_entry_ids:
                entry = support.get(entry_id)
                if entry is None:
                    raise DomainError(
                        ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                        "authorized answer cites an entry outside its current Package",
                    )
                url = (
                    f"/v1/engineering-qa/results/{result.result_id.value}"
                    f"/citations/{entry.entry_id.value}"
                )
                public_citations.append(
                    {
                        "entry_id": entry.entry_id.value,
                        "label": entry.locator,
                        "url": url,
                        "content_digest": entry.content_digest.value,
                    }
                )
                citations[entry.entry_id] = {
                    "schema": "ENGINEERING_QA_CITATION_PROJECTION@1",
                    "result_id": result.result_id.value,
                    "result_digest": result.digest.value,
                    "package_id": package.package_id.value,
                    "package_digest": package.digest.value,
                    "package_seal_digest": package.seal_digest.value,
                    "entry_id": entry.entry_id.value,
                    "origin_class": entry.origin_class,
                    "evidence_class": entry.evidence_class.value,
                    "modality": entry.modality,
                    "repository_revision": entry.repository_revision,
                    "locator": entry.locator,
                    "content": entry.content,
                    "content_digest": entry.content_digest.value,
                    "support_references": list(entry.support_references),
                    "coverage": entry.coverage,
                    "projection_is_answer_input": False,
                }
        page["citations"] = public_citations
        if result.authorized_answer is None:
            page["limitation"] = {
                "reason": result.terminal_reason,
                "message": "调查或独立审核未形成可授权答案；本次请求已失败关闭。",
                "delivery_authorized": False,
            }
        details = dict(page["developer_details"])
        details["package_partition_counts"] = (
            {
                "support/citation": len(package.support_citation),
                "boundary/audit": len(package.boundary_audit),
            }
            if package
            else None
        )
        details["role_direct_source_authority"] = {
            "initial_investigation": False,
            "verification_investigation": False,
            "answer": False,
            "review": False,
        }
        details.update(self._runtime_status.model_view())
        page["developer_details"] = details
        return page, citations


class EngineeringQuestionBrowserApplication:
    """Small WSGI adapter; a separate trusted launcher owns loopback binding."""

    maximum_request_bytes = 65_536

    def __init__(self, product: EngineeringQuestionWebProduct) -> None:
        self._product = product

    def __call__(self, environ, start_response):
        try:
            self._require_loopback(environ)
            method = str(environ.get("REQUEST_METHOD", "GET")).upper()
            path = str(environ.get("PATH_INFO", "/"))
            if method == "GET" and path == "/":
                return self._respond(
                    start_response,
                    "200 OK",
                    ENGINEERING_QA_BROWSER_HTML.encode("utf-8"),
                    "text/html; charset=utf-8",
                )
            if method == "GET" and path == "/health":
                return self._json(
                    start_response,
                    "200 OK",
                    self._product.health(),
                )
            if method == "POST" and path == "/v1/engineering-qa/questions":
                payload = self._read_json(environ)
                if set(payload) != {"request_id", "question"}:
                    raise DomainError(
                        ErrorCode.INVALID_ARGUMENT,
                        "Engineering QA request requires exactly request_id and question",
                    )
                if not isinstance(payload["request_id"], str) or not isinstance(
                    payload["question"], str
                ):
                    raise DomainError(
                        ErrorCode.INVALID_ARGUMENT,
                        "Engineering QA request fields must be strings",
                    )
                page = self._product.answer(
                    request_ref=payload["request_id"], question=payload["question"]
                )
                return self._json(start_response, "200 OK", page)
            match = _CITATION_ROUTE.fullmatch(path)
            if method == "GET" and match:
                projection = self._product.citation(
                    result_id=StableId(match.group("result")),
                    entry_id=StableId(match.group("entry")),
                )
                return self._json(start_response, "200 OK", projection)
            return self._json(
                start_response,
                "404 Not Found",
                {"error": "NOT_FOUND", "message": "route not found"},
            )
        except DomainError as exc:
            if exc.code is ErrorCode.SOURCE_TARGET_NOT_FOUND:
                status = "404 Not Found"
            elif exc.code is ErrorCode.CONTROL_STATE_DENIED:
                status = "403 Forbidden"
            elif exc.code in {
                ErrorCode.INVALID_ARGUMENT,
                ErrorCode.IDEMPOTENCY_MISMATCH,
            }:
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
                "request body is empty or exceeds the local preview limit",
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
        if remote != "127.0.0.1" or not re.fullmatch(
            r"127\.0\.0\.1(?::(?:[1-9][0-9]{0,4}))?", host
        ):
            raise DomainError(
                ErrorCode.CONTROL_STATE_DENIED,
                "Engineering QA direction preview accepts only the exact loopback origin",
            )
        if ":" in host and int(host.rsplit(":", 1)[1]) > 65_535:
            raise DomainError(
                ErrorCode.CONTROL_STATE_DENIED,
                "Engineering QA loopback Host port is invalid",
            )

    @staticmethod
    def _json(start_response, status: str, value: object):
        return EngineeringQuestionBrowserApplication._respond(
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
            (
                "Content-Security-Policy",
                "default-src 'self'; style-src 'self' 'unsafe-inline'; "
                "script-src 'self' 'unsafe-inline'; connect-src 'self'; "
                "img-src 'none'; object-src 'none'; frame-ancestors 'none'",
            ),
        ]
        start_response(status, headers)
        return [body]


def _unique_json_object(
    pairs: list[tuple[str, object]],
) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON field: {key}")
        value[key] = item
    return value


__all__ = [
    "EngineeringQuestionBrowserApplication",
    "EngineeringQuestionRequestFactory",
    "EngineeringQuestionWebRuntimeStatus",
    "EngineeringQuestionWebProduct",
    "ExactAuthorizedEngineeringQuestionRequestFactory",
    "FixedEngineeringQuestionRequestFactory",
    "InMemoryEngineeringQuestionWebProduct",
]
