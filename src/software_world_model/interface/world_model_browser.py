"""Loopback-only browser adapter for evaluation-only World Model questions.

The adapter owns HTTP validation and presentation only.  A trusted evaluation
runner is injected through a deliberately narrow protocol; the interface has no
repository path, Source connector, Evidence-first fallback, or activation path.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import json
import re
from typing import Protocol
from urllib.parse import unquote

from .world_model_browser_ui import (
    WORLD_MODEL_BROWSER_CSS,
    WORLD_MODEL_BROWSER_HTML,
    WORLD_MODEL_BROWSER_JS,
)


_REQUEST_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,159}$")
_RESULT_ID = re.compile(r"^structure_view_result_[0-9a-f]{32}$")
_CITATION_PATH = re.compile(
    r"^/v1/world-model/requests/([^/]+)/citations/([^/]+)$"
)
_QUESTION_MAXIMUM = 8_000


class WorldModelBrowserRunner(Protocol):
    """Security boundary implemented by the trusted evaluation launcher."""

    def health(self) -> Mapping[str, object]: ...

    def datasets(self) -> tuple[Mapping[str, object], ...]: ...

    def ask(
        self, *, request_id: str, dataset_id: str, question: str
    ) -> Mapping[str, object]: ...

    def citation(
        self, *, request_id: str, result_id: str
    ) -> Mapping[str, object]: ...


@dataclass(frozen=True, slots=True)
class RawHttpResponse:
    body: bytes
    content_type: str


class PublicRunnerError(RuntimeError):
    """Fail-closed runner error with a bounded public diagnostic."""

    def __init__(self, code: str, message: str, *, status: str = "502 Bad Gateway"):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status


class WorldModelBrowserApplication:
    """WSGI application for the distinct WORLD_MODEL evaluation surface."""

    def __init__(
        self,
        runner: WorldModelBrowserRunner,
        *,
        max_request_bytes: int = 16_384,
        selector_field: str = "dataset_id",
    ) -> None:
        if max_request_bytes < 1:
            raise ValueError("max_request_bytes must be positive")
        if selector_field not in {"dataset_id", "read_set_id"}:
            raise ValueError("selector_field must be dataset_id or read_set_id")
        self._runner = runner
        self._max_request_bytes = max_request_bytes
        self._selector_field = selector_field

    def __call__(self, environ, start_response):
        try:
            status, payload = self._dispatch(environ)
        except PublicRunnerError as exc:
            status = exc.status
            payload = {"error": exc.code, "message": exc.message}
        except (KeyError, TypeError, ValueError) as exc:
            status = "400 Bad Request"
            payload = {"error": "INVALID_ARGUMENT", "message": str(exc)}
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
            encoded = json.dumps(
                payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            ).encode("utf-8")
            content_type = "application/json; charset=utf-8"
        headers = [
            ("Content-Type", content_type),
            ("Content-Length", str(len(encoded))),
            ("Cache-Control", "no-store"),
            ("X-Content-Type-Options", "nosniff"),
            ("Referrer-Policy", "no-referrer"),
            ("X-Frame-Options", "DENY"),
            ("Cross-Origin-Resource-Policy", "same-origin"),
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
        start_response(status, headers)
        return [encoded]

    def _dispatch(
        self, environ
    ) -> tuple[str, Mapping[str, object] | RawHttpResponse]:
        method = str(environ.get("REQUEST_METHOD", "GET")).upper()
        path = str(environ.get("PATH_INFO", "/"))
        if method == "GET" and path in {"/", "/index.html"}:
            return "200 OK", _raw(
                WORLD_MODEL_BROWSER_HTML, "text/html; charset=utf-8"
            )
        if method == "GET" and path == "/assets/world-model.css":
            return "200 OK", _raw(
                WORLD_MODEL_BROWSER_CSS, "text/css; charset=utf-8"
            )
        if method == "GET" and path == "/assets/world-model.js":
            return "200 OK", _raw(
                WORLD_MODEL_BROWSER_JS.replace(
                    "__SWM_SELECTOR_FIELD__", self._selector_field
                ),
                "text/javascript; charset=utf-8",
            )
        if method == "GET" and path == "/health":
            return "200 OK", dict(self._runner.health())
        if method == "GET" and path == "/v1/world-model/datasets":
            return "200 OK", {
                "mode": "WORLD_MODEL",
                "environment": "EVALUATION_ONLY",
                "selector_field": self._selector_field,
                "datasets": [dict(item) for item in self._runner.datasets()],
            }
        citation_match = _CITATION_PATH.fullmatch(path)
        if method == "GET" and citation_match:
            request_id = _request_id(unquote(citation_match.group(1)))
            result_id = _result_id(unquote(citation_match.group(2)))
            return "200 OK", dict(
                self._runner.citation(
                    request_id=request_id,
                    result_id=result_id,
                )
            )
        if method == "POST" and path == "/v1/world-model/questions":
            body = self._read_json(environ)
            _exact_keys(body, {"request_id", self._selector_field, "question"})
            request_id = _request_id(_text(body, "request_id"))
            dataset_id = _bounded_text(
                body, self._selector_field, maximum=160
            )
            question = _bounded_text(
                body, "question", maximum=_QUESTION_MAXIMUM
            )
            return "200 OK", dict(
                self._runner.ask(
                    request_id=request_id,
                    dataset_id=dataset_id,
                    question=question,
                )
            )
        return "404 Not Found", {
            "error": "NOT_FOUND",
            "message": "route not found",
        }

    def _read_json(self, environ) -> Mapping[str, object]:
        content_type = str(environ.get("CONTENT_TYPE", "")).split(";", 1)[0]
        if content_type.strip().lower() != "application/json":
            raise ValueError("Content-Type must be application/json")
        raw_length = str(environ.get("CONTENT_LENGTH", ""))
        if not raw_length or not raw_length.isascii() or not raw_length.isdigit():
            raise ValueError("Content-Length must be a non-negative integer")
        length = int(raw_length)
        if length < 1:
            raise ValueError("JSON request body is required")
        if length > self._max_request_bytes:
            raise ValueError("request body is too large")
        stream = environ.get("wsgi.input")
        if stream is None:
            raise ValueError("request body is unavailable")
        raw = stream.read(length)
        if not isinstance(raw, bytes) or len(raw) != length:
            raise ValueError("request body is incomplete")
        try:
            decoded = raw.decode("utf-8")
            value = json.loads(decoded, object_pairs_hook=_unique_object)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("request body must be valid UTF-8 JSON") from exc
        if not isinstance(value, dict):
            raise ValueError("request body must be a JSON object")
        return value


def _raw(value: str, content_type: str) -> RawHttpResponse:
    return RawHttpResponse(value.encode("utf-8"), content_type)


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON field: {key}")
        value[key] = item
    return value


def _exact_keys(value: Mapping[str, object], expected: set[str]) -> None:
    observed = set(value)
    if observed != expected:
        missing = sorted(expected - observed)
        extra = sorted(observed - expected)
        raise ValueError(
            f"request fields do not match the contract (missing={missing}, extra={extra})"
        )


def _text(value: Mapping[str, object], key: str) -> str:
    item = value.get(key)
    if not isinstance(item, str):
        raise ValueError(f"{key} must be a string")
    return item


def _bounded_text(
    value: Mapping[str, object], key: str, *, maximum: int
) -> str:
    item = _text(value, key).strip()
    if not item:
        raise ValueError(f"{key} must not be empty")
    if len(item) > maximum:
        raise ValueError(f"{key} is too long")
    if "\x00" in item:
        raise ValueError(f"{key} contains an invalid character")
    return item


def _request_id(value: str) -> str:
    if not _REQUEST_ID.fullmatch(value):
        raise ValueError("request_id has an invalid format")
    return value


def _result_id(value: str) -> str:
    if not _RESULT_ID.fullmatch(value):
        raise ValueError("result_id has an invalid format")
    return value
