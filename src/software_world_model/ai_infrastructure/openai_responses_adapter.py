"""OpenAI Responses API no-tools adapter with an injectable HTTP boundary.

The production transport resolves credentials only at dispatch.  Recording and
fixture transports therefore never need to hold or persist secret material.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import socket
from typing import Callable, Mapping, Protocol
from urllib import error as urllib_error
from urllib import request as urllib_request
from urllib.parse import urlsplit

from software_world_model.cross_cutting import DomainError, ErrorCode

from .direct_https import build_direct_https_opener
from .model_gateway import (
    AdapterConformanceLevel,
    AdapterResponse,
    ProviderAdapterCapabilities,
    ProviderOutcomeUnknown,
    ProviderRequest,
    ReplayClassification,
)


DEFAULT_RESPONSES_ENDPOINT = "https://api.openai.com/v1/responses"
_ALLOWED_OUTPUT_ITEM_TYPES = frozenset({"message", "reasoning"})


@dataclass(frozen=True, slots=True)
class OutputSchemaDefinition:
    name: str
    schema: Mapping[str, object]

    def __post_init__(self) -> None:
        if not self.name or self.name != self.name.strip():
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "output schema name is required")
        try:
            _validate_schema_definition(self.schema, self.schema, path="$", root=True)
        except ValueError as exc:
            raise DomainError(ErrorCode.INVALID_ARGUMENT, str(exc)) from exc

    def validate_output_text(self, output_text: str) -> Mapping[str, object]:
        """Parse and revalidate provider text against the closed schema."""

        try:
            decoded = json.loads(output_text)
        except json.JSONDecodeError as exc:
            raise DomainError(ErrorCode.STRUCTURED_OUTPUT_INVALID, "output text is not JSON") from exc
        if not isinstance(decoded, dict):
            raise DomainError(
                ErrorCode.STRUCTURED_OUTPUT_INVALID,
                "structured output root is not an object",
            )
        try:
            _validate_output(decoded, self.schema, self.schema, path="$")
        except ValueError as exc:
            raise DomainError(ErrorCode.STRUCTURED_OUTPUT_INVALID, str(exc)) from exc
        return decoded


@dataclass(frozen=True, slots=True)
class ProviderHTTPResponse:
    status_code: int
    headers: Mapping[str, str]
    body: bytes


class ResponsesTransport(Protocol):
    def post_json(
        self,
        *,
        endpoint: str,
        body: bytes,
        client_request_id: str,
        timeout_milliseconds: int,
    ) -> ProviderHTTPResponse: ...


@dataclass(frozen=True, slots=True)
class RecordedProviderRequest:
    endpoint: str
    body: bytes
    client_request_id: str
    timeout_milliseconds: int


class RecordingResponsesTransport:
    """Record the non-secret request body before delegating."""

    def __init__(self, delegate: ResponsesTransport) -> None:
        self._delegate = delegate
        self.requests: list[RecordedProviderRequest] = []

    def post_json(
        self,
        *,
        endpoint: str,
        body: bytes,
        client_request_id: str,
        timeout_milliseconds: int,
    ) -> ProviderHTTPResponse:
        self.requests.append(
            RecordedProviderRequest(endpoint, body, client_request_id, timeout_milliseconds)
        )
        return self._delegate.post_json(
            endpoint=endpoint,
            body=body,
            client_request_id=client_request_id,
            timeout_milliseconds=timeout_milliseconds,
        )


class UrllibOpenAIResponsesTransport:
    """Direct HTTPS transport; credentials exist only inside dispatch headers."""

    def __init__(
        self,
        *,
        api_key_resolver: Callable[[], str],
        organization_resolver: Callable[[], str | None] | None = None,
        project_resolver: Callable[[], str | None] | None = None,
    ) -> None:
        self._api_key_resolver = api_key_resolver
        self._organization_resolver = organization_resolver
        self._project_resolver = project_resolver
        # The adapter profile requires direct HTTPS.  Do not forward bearer
        # credentials through ambient HTTP(S)_PROXY settings.
        self._opener = build_direct_https_opener()

    def post_json(
        self,
        *,
        endpoint: str,
        body: bytes,
        client_request_id: str,
        timeout_milliseconds: int,
    ) -> ProviderHTTPResponse:
        _require_https(endpoint)
        api_key = self._api_key_resolver()
        if not api_key:
            raise DomainError(ErrorCode.LIVE_INTEGRATION_HELD, "OpenAI credential is not configured")
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "X-Client-Request-Id": client_request_id,
        }
        organization = self._organization_resolver() if self._organization_resolver else None
        project = self._project_resolver() if self._project_resolver else None
        if organization:
            headers["OpenAI-Organization"] = organization
        if project:
            headers["OpenAI-Project"] = project
        http_request = urllib_request.Request(endpoint, data=body, headers=headers, method="POST")
        try:
            with self._opener.open(
                http_request, timeout=timeout_milliseconds / 1000
            ) as response:
                return ProviderHTTPResponse(
                    status_code=response.status,
                    headers={key.lower(): value for key, value in response.headers.items()},
                    body=response.read(),
                )
        except urllib_error.HTTPError as exc:
            return ProviderHTTPResponse(
                status_code=exc.code,
                headers={key.lower(): value for key, value in exc.headers.items()},
                body=exc.read(),
            )
        except (urllib_error.URLError, TimeoutError, socket.timeout) as exc:
            raise ProviderOutcomeUnknown("OpenAI response outcome is unknown") from exc


class OpenAIResponsesNoToolsAdapter:
    provider_type = "OPENAI"
    adapter_version = "responses-no-tools@1"

    def __init__(
        self,
        *,
        transport: ResponsesTransport,
        output_schemas: Mapping[str, OutputSchemaDefinition],
        pinned_models: frozenset[str] = frozenset(),
        observed_revisions_by_alias: Mapping[str, frozenset[str]] | None = None,
        qualified_model_fingerprints: tuple[str, ...] = (),
        conformance_level: AdapterConformanceLevel = AdapterConformanceLevel.OFFLINE_FIXTURE,
        conformance_result_ref: str = "CC-MODEL-NO-TOOLS-001:OFFLINE-NOT-LIVE",
        endpoint: str = DEFAULT_RESPONSES_ENDPOINT,
        reasoning_effort: str | None = None,
    ) -> None:
        _require_https(endpoint)
        if conformance_level is AdapterConformanceLevel.LIVE_CURRENT and not qualified_model_fingerprints:
            raise DomainError(
                ErrorCode.QUALIFICATION_INVALID,
                "live adapter requires at least one evaluated exact model fingerprint",
            )
        if reasoning_effort not in {None, "none", "low", "medium", "high", "xhigh", "max"}:
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "unsupported reasoning effort")
        self._transport = transport
        self._output_schemas = dict(output_schemas)
        self._pinned_models = pinned_models
        self._observed = dict(observed_revisions_by_alias or {})
        self._endpoint = endpoint
        self._reasoning_effort = reasoning_effort
        self.capabilities = ProviderAdapterCapabilities(
            no_external_access=True,
            hidden_context_disabled=True,
            stateless_session=True,
            structured_output=True,
            actual_fingerprint_reported=True,
            conformance_level=conformance_level,
            conformance_result_ref=conformance_result_ref,
            qualified_model_fingerprints=qualified_model_fingerprints,
        )

    def invoke(self, request: ProviderRequest) -> AdapterResponse:
        if request.tools or request.store or request.stream:
            raise DomainError(
                ErrorCode.PROVIDER_OUTPUT_FORBIDDEN,
                "no-tools adapter requires empty tools, store=false, and stream=false",
            )
        definition = self._output_schemas.get(request.output_schema_ref)
        if definition is None:
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "output schema reference is not registered")
        payload: dict[str, object] = {
            "model": request.model_ref,
            "input": [
                {
                    "role": message.role,
                    "content": [{"type": "input_text", "text": message.content}],
                }
                for message in request.messages
            ],
            "tools": [],
            "tool_choice": "none",
            "parallel_tool_calls": False,
            "store": False,
            "stream": False,
            "max_output_tokens": request.max_output_tokens,
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": definition.name,
                    "strict": True,
                    "schema": definition.schema,
                }
            },
            "metadata": dict(request.metadata),
        }
        if self._reasoning_effort is not None:
            payload["reasoning"] = {"effort": self._reasoning_effort}
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        client_request_id = f"swm-{request.digest.value.removeprefix('sha256:')[:32]}"
        response = self._transport.post_json(
            endpoint=self._endpoint,
            body=body,
            client_request_id=client_request_id,
            timeout_milliseconds=request.timeout_milliseconds,
        )
        if not 200 <= response.status_code < 300:
            raise DomainError(
                ErrorCode.PROVIDER_HTTP_ERROR,
                "OpenAI Responses request returned a non-success status",
                {"http_status": response.status_code},
            )
        provider_payload = _json_object(response.body)
        status = provider_payload.get("status")
        if status != "completed":
            reason = _incomplete_reason(provider_payload)
            raise DomainError(
                ErrorCode.PROVIDER_RESPONSE_INVALID,
                "OpenAI response is not complete",
                {"status": str(status), "reason": reason},
            )
        if provider_payload.get("tools") not in (None, []):
            raise DomainError(ErrorCode.PROVIDER_OUTPUT_FORBIDDEN, "provider response reports tools")
        output_text = _extract_output_text(provider_payload)
        definition.validate_output_text(output_text)
        actual_model = provider_payload.get("model")
        if not isinstance(actual_model, str) or not actual_model:
            raise DomainError(ErrorCode.PROVIDER_RESPONSE_INVALID, "provider model identity is missing")
        replay = self._classify(request.model_ref, actual_model)
        response_id = provider_payload.get("id")
        if not isinstance(response_id, str) or not response_id:
            raise DomainError(ErrorCode.PROVIDER_RESPONSE_INVALID, "provider response identity is missing")
        usage = provider_payload.get("usage")
        input_tokens, output_tokens, usage_complete = _usage(usage)
        request_id = {key.lower(): value for key, value in response.headers.items()}.get("x-request-id")
        return AdapterResponse.create(
            provider_request_id=request_id or response_id,
            actual_model_fingerprint=actual_model,
            replay_classification=replay,
            output_text=output_text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            usage_complete=usage_complete,
            termination_reason="completed",
        )

    def _classify(self, requested: str, actual: str) -> ReplayClassification:
        if requested == actual and actual in self._pinned_models:
            return ReplayClassification.PINNED
        if actual in self._observed.get(requested, frozenset()):
            return ReplayClassification.OBSERVED_MUTABLE
        return ReplayClassification.UNRESOLVED_MUTABLE


def _require_https(endpoint: str) -> None:
    parsed = urlsplit(endpoint)
    if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password:
        raise DomainError(ErrorCode.INVALID_ARGUMENT, "Responses endpoint must be direct HTTPS")


def _json_object(body: bytes) -> Mapping[str, object]:
    try:
        value = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DomainError(ErrorCode.PROVIDER_RESPONSE_INVALID, "provider response is not JSON") from exc
    if not isinstance(value, dict):
        raise DomainError(ErrorCode.PROVIDER_RESPONSE_INVALID, "provider response is not an object")
    return value


def _incomplete_reason(payload: Mapping[str, object]) -> str:
    details = payload.get("incomplete_details")
    if isinstance(details, dict) and isinstance(details.get("reason"), str):
        return details["reason"]
    return "unknown"


def _extract_output_text(payload: Mapping[str, object]) -> str:
    output = payload.get("output")
    if not isinstance(output, list) or not output:
        raise DomainError(ErrorCode.PROVIDER_RESPONSE_INVALID, "provider output is empty")
    texts: list[str] = []
    for item in output:
        if not isinstance(item, dict) or item.get("type") not in _ALLOWED_OUTPUT_ITEM_TYPES:
            raise DomainError(ErrorCode.PROVIDER_OUTPUT_FORBIDDEN, "provider returned a forbidden output item")
        if item.get("type") == "reasoning":
            continue
        if item.get("status") != "completed" or item.get("role") != "assistant":
            raise DomainError(ErrorCode.PROVIDER_RESPONSE_INVALID, "assistant message is incomplete")
        content = item.get("content")
        if not isinstance(content, list) or not content:
            raise DomainError(ErrorCode.PROVIDER_RESPONSE_INVALID, "assistant message content is empty")
        for part in content:
            if not isinstance(part, dict):
                raise DomainError(ErrorCode.PROVIDER_OUTPUT_FORBIDDEN, "provider content is invalid")
            if part.get("type") == "refusal":
                raise DomainError(ErrorCode.PROVIDER_REFUSAL, "provider refused the request")
            if (
                part.get("type") != "output_text"
                or not isinstance(part.get("text"), str)
                or part.get("annotations", []) != []
            ):
                raise DomainError(ErrorCode.PROVIDER_OUTPUT_FORBIDDEN, "provider content is not plain output text")
            texts.append(part["text"])
    if not texts:
        raise DomainError(ErrorCode.PROVIDER_RESPONSE_INVALID, "provider produced no output text")
    return "".join(texts)


def _usage(value: object) -> tuple[int | None, int | None, bool]:
    if not isinstance(value, dict):
        return None, None, False
    input_tokens = value.get("input_tokens")
    output_tokens = value.get("output_tokens")
    if not isinstance(input_tokens, int) or input_tokens < 0:
        return None, None, False
    if not isinstance(output_tokens, int) or output_tokens < 0:
        return None, None, False
    return input_tokens, output_tokens, True


def _validate_schema_definition(
    schema: Mapping[str, object],
    root_schema: Mapping[str, object],
    *,
    path: str,
    root: bool = False,
) -> None:
    if root and schema.get("type") != "object":
        raise ValueError("structured output root must be an object")
    if "$ref" in schema:
        reference = schema["$ref"]
        if not isinstance(reference, str) or _resolve_ref(root_schema, reference) is None:
            raise ValueError(f"{path} has an unresolved local schema reference")
        return
    any_of = schema.get("anyOf")
    if any_of is not None:
        if not isinstance(any_of, list) or not any_of:
            raise ValueError(f"{path}.anyOf must be a non-empty array")
        for index, option in enumerate(any_of):
            if not isinstance(option, dict):
                raise ValueError(f"{path}.anyOf[{index}] must be an object")
            _validate_schema_definition(option, root_schema, path=f"{path}.anyOf[{index}]")
        return
    kind = schema.get("type")
    kinds = kind if isinstance(kind, list) else [kind]
    if not kinds or any(item not in {"object", "array", "string", "integer", "number", "boolean", "null"} for item in kinds):
        raise ValueError(f"{path} has an unsupported schema type")
    if "object" in kinds:
        properties = schema.get("properties")
        required = schema.get("required")
        if not isinstance(properties, dict):
            raise ValueError(f"{path}.properties must be an object")
        if schema.get("additionalProperties") is not False:
            raise ValueError(f"{path} must set additionalProperties=false")
        if not isinstance(required, list) or set(required) != set(properties):
            raise ValueError(f"{path} must require every declared property")
        for name, child in properties.items():
            if not isinstance(name, str) or not isinstance(child, dict):
                raise ValueError(f"{path}.properties contains an invalid definition")
            _validate_schema_definition(child, root_schema, path=f"{path}.{name}")
    if "array" in kinds:
        items = schema.get("items")
        if not isinstance(items, dict):
            raise ValueError(f"{path}.items must be an object")
        _validate_schema_definition(items, root_schema, path=f"{path}[]")
    definitions = schema.get("$defs")
    if definitions is not None:
        if not isinstance(definitions, dict):
            raise ValueError(f"{path}.$defs must be an object")
        for name, child in definitions.items():
            if not isinstance(child, dict):
                raise ValueError(f"{path}.$defs.{name} must be an object")
            _validate_schema_definition(child, root_schema, path=f"{path}.$defs.{name}")


def _validate_output(
    value: object,
    schema: Mapping[str, object],
    root_schema: Mapping[str, object],
    *,
    path: str,
) -> None:
    reference = schema.get("$ref")
    if isinstance(reference, str):
        resolved = _resolve_ref(root_schema, reference)
        if resolved is None:
            raise ValueError(f"{path} uses an unresolved schema reference")
        _validate_output(value, resolved, root_schema, path=path)
        return
    any_of = schema.get("anyOf")
    if isinstance(any_of, list):
        for option in any_of:
            try:
                _validate_output(value, option, root_schema, path=path)
                return
            except ValueError:
                continue
        raise ValueError(f"{path} matches no allowed schema variant")
    kind = schema.get("type")
    kinds = kind if isinstance(kind, list) else [kind]
    if not any(_matches_type(value, item) for item in kinds):
        raise ValueError(f"{path} has the wrong JSON type")
    enum = schema.get("enum")
    if isinstance(enum, list) and value not in enum:
        raise ValueError(f"{path} is outside the allowed enum")
    if isinstance(value, dict):
        properties = schema.get("properties")
        if not isinstance(properties, dict) or set(value) != set(properties):
            raise ValueError(f"{path} object fields do not match the closed schema")
        for name, child in properties.items():
            _validate_output(value[name], child, root_schema, path=f"{path}.{name}")
    elif isinstance(value, list):
        items = schema.get("items")
        if not isinstance(items, dict):
            raise ValueError(f"{path} array schema has no item definition")
        for index, item in enumerate(value):
            _validate_output(item, items, root_schema, path=f"{path}[{index}]")
    elif isinstance(value, (int, float)) and not isinstance(value, bool):
        minimum = schema.get("minimum")
        maximum = schema.get("maximum")
        if isinstance(minimum, (int, float)) and value < minimum:
            raise ValueError(f"{path} is below the schema minimum")
        if isinstance(maximum, (int, float)) and value > maximum:
            raise ValueError(f"{path} is above the schema maximum")


def _matches_type(value: object, kind: object) -> bool:
    return {
        "object": isinstance(value, dict),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "number": isinstance(value, (int, float)) and not isinstance(value, bool),
        "boolean": isinstance(value, bool),
        "null": value is None,
    }.get(kind, False)


def _resolve_ref(
    root_schema: Mapping[str, object], reference: str
) -> Mapping[str, object] | None:
    if not reference.startswith("#/"):
        return None
    current: object = root_schema
    for segment in reference[2:].split("/"):
        name = segment.replace("~1", "/").replace("~0", "~")
        if not isinstance(current, dict) or name not in current:
            return None
        current = current[name]
    return current if isinstance(current, dict) else None
