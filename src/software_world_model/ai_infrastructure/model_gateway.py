"""Closed-input, provider-neutral model gateway.

The gateway intentionally contains no production provider implementation.  An
adapter must present current conformance evidence before a call can cross the
dispatch fence, and offline fixtures can never yield production eligibility.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Callable, Mapping, Protocol

from software_world_model.cross_cutting import (
    Digest,
    DomainError,
    ErrorCode,
    IdGenerator,
    NullTelemetryRecorder,
    Revision,
    StableId,
    TelemetryMetric,
    TelemetryRecorder,
    Uuid4IdGenerator,
    digest_of,
)


class RuntimeAccessMode(str, Enum):
    NO_EXTERNAL_ACCESS = "NO_EXTERNAL_ACCESS"
    DECLARED_PROVIDER_TOOL_SET = "DECLARED_PROVIDER_TOOL_SET"


class PlatformProposalMode(str, Enum):
    NONE = "NONE"
    DECLARED_PLATFORM_PROPOSAL_ONLY = "DECLARED_PLATFORM_PROPOSAL_ONLY"


class InputDisposition(str, Enum):
    PROVIDED = "PROVIDED"
    EMPTY = "EMPTY"
    NOT_PROVIDED = "NOT_PROVIDED"
    REJECTED = "REJECTED"


class AdapterConformanceLevel(str, Enum):
    OFFLINE_FIXTURE = "OFFLINE_FIXTURE"
    LIVE_CURRENT = "LIVE_CURRENT"
    LIVE_STALE = "LIVE_STALE"


class ModelCallState(str, Enum):
    PREPARED = "PREPARED"
    DISPATCHED = "DISPATCHED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    OUTCOME_UNKNOWN = "OUTCOME_UNKNOWN"
    CANCELLED_BEFORE_DISPATCH = "CANCELLED_BEFORE_DISPATCH"


class ReplayClassification(str, Enum):
    PINNED = "PINNED"
    OBSERVED_MUTABLE = "OBSERVED_MUTABLE"
    UNRESOLVED_MUTABLE = "UNRESOLVED_MUTABLE"


@dataclass(frozen=True, slots=True)
class AuthorizedInputItem:
    item_id: str
    schema_ref: str
    classification: str
    purpose: str
    authority_reference: str
    disposition: InputDisposition
    content: str
    transformation_ref: str
    content_digest: Digest

    @classmethod
    def create(
        cls,
        *,
        item_id: str,
        schema_ref: str,
        classification: str,
        purpose: str,
        authority_reference: str,
        disposition: InputDisposition,
        content: str = "",
        transformation_ref: str = "identity@1",
    ) -> "AuthorizedInputItem":
        for value, label in (
            (item_id, "item ID"),
            (schema_ref, "schema reference"),
            (classification, "classification"),
            (purpose, "purpose"),
            (authority_reference, "authority reference"),
            (transformation_ref, "transformation reference"),
        ):
            _text(value, label)
        if disposition is InputDisposition.PROVIDED and not content:
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "provided input content cannot be empty")
        if disposition is not InputDisposition.PROVIDED and content:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "empty, missing, or rejected input cannot carry hidden content",
            )
        return cls(
            item_id=item_id,
            schema_ref=schema_ref,
            classification=classification,
            purpose=purpose,
            authority_reference=authority_reference,
            disposition=disposition,
            content=content,
            transformation_ref=transformation_ref,
            content_digest=digest_of(content),
        )


@dataclass(frozen=True, slots=True)
class AuthorizedInputManifest:
    manifest_id: StableId
    version: Revision
    capability_id: str
    strategy_ref: str
    execution_stage: str
    calling_module: str
    proposal_vocabulary_ref: str | None
    items: tuple[AuthorizedInputItem, ...]
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        capability_id: str,
        strategy_ref: str,
        execution_stage: str,
        calling_module: str,
        proposal_vocabulary_ref: str | None,
        items: tuple[AuthorizedInputItem, ...],
        id_generator: IdGenerator | None = None,
    ) -> "AuthorizedInputManifest":
        for value, label in (
            (capability_id, "capability ID"),
            (strategy_ref, "strategy reference"),
            (execution_stage, "execution stage"),
            (calling_module, "calling module"),
        ):
            _text(value, label)
        if not items:
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "authorized input manifest is empty")
        if len({item.item_id for item in items}) != len(items):
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "manifest input item IDs must be unique")
        manifest_id = (id_generator or Uuid4IdGenerator()).new("input_manifest")
        core = {
            "manifest_id": manifest_id.value,
            "version": 1,
            "capability_id": capability_id,
            "strategy_ref": strategy_ref,
            "execution_stage": execution_stage,
            "calling_module": calling_module,
            "proposal_vocabulary_ref": proposal_vocabulary_ref,
            "items": items,
        }
        return cls(
            manifest_id=manifest_id,
            version=Revision(1),
            capability_id=capability_id,
            strategy_ref=strategy_ref,
            execution_stage=execution_stage,
            calling_module=calling_module,
            proposal_vocabulary_ref=proposal_vocabulary_ref,
            items=items,
            digest=digest_of(core),
        )


@dataclass(frozen=True, slots=True)
class ModelExecutionContext:
    execution_envelope_ref: str
    manifest: AuthorizedInputManifest
    prompt_program_ref: str
    rendering_contract_version: str
    output_schema_ref: str
    runtime_access_mode: RuntimeAccessMode
    platform_proposal_mode: PlatformProposalMode
    requested_model_ref: str
    provider_type: str
    adapter_version: str
    provider_configuration_fingerprint: Digest
    max_output_tokens: int
    timeout_milliseconds: int
    classification: str
    required_exact_fingerprint: bool


@dataclass(frozen=True, slots=True)
class RenderedMessage:
    role: str
    content: str
    input_item_id: str
    input_item_digest: Digest


@dataclass(frozen=True, slots=True)
class ProviderAdapterCapabilities:
    no_external_access: bool
    hidden_context_disabled: bool
    stateless_session: bool
    structured_output: bool
    actual_fingerprint_reported: bool
    conformance_level: AdapterConformanceLevel
    conformance_result_ref: str
    qualified_model_fingerprints: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ProviderRequest:
    model_ref: str
    messages: tuple[RenderedMessage, ...]
    output_schema_ref: str
    tools: tuple[object, ...]  # validated as empty for the no-tools slice
    store: bool
    stream: bool
    max_output_tokens: int
    timeout_milliseconds: int
    metadata: tuple[tuple[str, str], ...]
    digest: Digest


@dataclass(frozen=True, slots=True)
class AdapterResponse:
    provider_request_id: str | None
    actual_model_fingerprint: str | None
    replay_classification: ReplayClassification
    output_text: str
    output_digest: Digest
    input_tokens: int | None
    output_tokens: int | None
    usage_complete: bool
    termination_reason: str
    output_normalization: str

    @classmethod
    def create(
        cls,
        *,
        provider_request_id: str | None,
        actual_model_fingerprint: str | None,
        replay_classification: ReplayClassification,
        output_text: str,
        input_tokens: int | None,
        output_tokens: int | None,
        usage_complete: bool,
        termination_reason: str,
        output_normalization: str = "IDENTITY",
    ) -> "AdapterResponse":
        if input_tokens is not None and input_tokens < 0:
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "input tokens cannot be negative")
        if output_tokens is not None and output_tokens < 0:
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "output tokens cannot be negative")
        return cls(
            provider_request_id=provider_request_id,
            actual_model_fingerprint=actual_model_fingerprint,
            replay_classification=replay_classification,
            output_text=output_text,
            output_digest=digest_of(output_text),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            usage_complete=usage_complete,
            termination_reason=_text(termination_reason, "termination reason"),
            output_normalization=_text(output_normalization, "output normalization"),
        )


class ProviderOutputRejected(DomainError):
    """A completed provider response whose content failed the closed contract."""

    def __init__(self, error: DomainError, response: AdapterResponse) -> None:
        super().__init__(error.code, error.message, error.details)
        self.response = response


class ProviderAdapter(Protocol):
    provider_type: str
    adapter_version: str
    capabilities: ProviderAdapterCapabilities

    def invoke(self, request: ProviderRequest) -> AdapterResponse: ...


@dataclass(frozen=True, slots=True)
class IsolationReceipt:
    receipt_id: StableId
    manifest_digest: Digest
    provider_request_digest: Digest
    provider_type: str
    adapter_version: str
    provider_configuration_fingerprint: Digest
    runtime_access_mode: RuntimeAccessMode
    platform_proposal_mode: PlatformProposalMode
    conformance_result_ref: str
    issued_at: datetime
    digest: Digest


MODEL_PROVIDER_HTTP_FAILURE_EVIDENCE_SCHEMA = (
    "MODEL_PROVIDER_HTTP_FAILURE_EVIDENCE@1"
)


@dataclass(frozen=True, slots=True)
class ModelProviderHTTPFailureEvidence:
    """Gateway-sealed, sanitized evidence for one terminal HTTP response.

    This record preserves only the non-secret response metadata needed by an
    execution-profile availability owner.  It is raw evidence, not fallback
    authority: the Application must still apply the registered availability
    policy and seal an exact profile verdict.
    """

    schema: str
    model_call_id: StableId
    provider_request_digest: Digest
    isolation_receipt_digest: Digest
    failure_code: str
    http_status: int
    provider_error_code: str | None
    provider_error_type: str | None
    provider_request_id: str | None
    digest: Digest

    @classmethod
    def seal(
        cls,
        *,
        model_call_id: StableId,
        provider_request_digest: Digest,
        isolation_receipt_digest: Digest,
        details: Mapping[str, str | int],
    ) -> "ModelProviderHTTPFailureEvidence | None":
        """Return no evidence when an adapter did not supply a valid status."""

        status = details.get("http_status")
        if type(status) is not int or not 100 <= status <= 599:
            return None
        error_code = _safe_provider_error_token(details.get("provider_error_code"))
        error_type = _safe_provider_error_token(details.get("provider_error_type"))
        request_id = _safe_provider_request_id(details.get("provider_request_id"))
        core = {
            "schema": MODEL_PROVIDER_HTTP_FAILURE_EVIDENCE_SCHEMA,
            "model_call_id": model_call_id.value,
            "provider_request_digest": provider_request_digest.value,
            "isolation_receipt_digest": isolation_receipt_digest.value,
            "failure_code": ErrorCode.PROVIDER_HTTP_ERROR.value,
            "http_status": status,
            "provider_error_code": error_code,
            "provider_error_type": error_type,
            "provider_request_id": request_id,
        }
        return cls(
            schema=MODEL_PROVIDER_HTTP_FAILURE_EVIDENCE_SCHEMA,
            model_call_id=model_call_id,
            provider_request_digest=provider_request_digest,
            isolation_receipt_digest=isolation_receipt_digest,
            failure_code=ErrorCode.PROVIDER_HTTP_ERROR.value,
            http_status=status,
            provider_error_code=error_code,
            provider_error_type=error_type,
            provider_request_id=request_id,
            digest=digest_of(core),
        )

    def require_exact(self) -> None:
        expected = self.seal(
            model_call_id=self.model_call_id,
            provider_request_digest=self.provider_request_digest,
            isolation_receipt_digest=self.isolation_receipt_digest,
            details={
                "http_status": self.http_status,
                **(
                    {"provider_error_code": self.provider_error_code}
                    if self.provider_error_code is not None
                    else {}
                ),
                **(
                    {"provider_error_type": self.provider_error_type}
                    if self.provider_error_type is not None
                    else {}
                ),
                **(
                    {"provider_request_id": self.provider_request_id}
                    if self.provider_request_id is not None
                    else {}
                ),
            },
        )
        if expected is None or self != expected:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Model Provider HTTP failure evidence is inconsistent",
            )


@dataclass(frozen=True, slots=True)
class ModelCallRecord:
    model_call_id: StableId
    revision: Revision
    state: ModelCallState
    manifest_id: StableId
    manifest_digest: Digest
    provider_request_digest: Digest
    isolation_receipt_id: StableId
    isolation_receipt_digest: Digest
    provider_type: str
    adapter_version: str
    requested_model_ref: str
    actual_model_fingerprint: str | None
    provider_request_id: str | None
    output_digest: Digest | None
    input_tokens: int | None
    output_tokens: int | None
    usage_complete: bool
    failure_code: str | None
    provider_http_failure_evidence: ModelProviderHTTPFailureEvidence | None
    created_at: datetime
    revised_at: datetime


@dataclass(frozen=True, slots=True)
class ModelResultEligibility:
    eligible_for_production_domain_output: bool
    reason: str
    actual_model_fingerprint: str | None
    isolation_receipt_id: StableId
    model_call_id: StableId
    digest: Digest


@dataclass(frozen=True, slots=True)
class ModelGatewayResult:
    call: ModelCallRecord
    response: AdapterResponse | None
    isolation_receipt: IsolationReceipt
    eligibility: ModelResultEligibility
    replayed: bool = False


@dataclass(frozen=True, slots=True)
class RecoveredModelCall:
    call: ModelCallRecord
    response: AdapterResponse | None
    isolation_receipt: IsolationReceipt


class ProviderOutcomeUnknown(RuntimeError):
    def __init__(self, message: str, *, reason_code: str = "UNKNOWN_NETWORK_FAILURE") -> None:
        super().__init__(message)
        self.reason_code = reason_code


class ProviderUnavailable(RuntimeError):
    """Provider-owned pre-HTTP unavailability with a known zero-dispatch outcome."""

    def __init__(
        self,
        message: str,
        *,
        reason_code: str = "PROVIDER_PRE_DISPATCH_UNAVAILABLE",
    ) -> None:
        super().__init__(message)
        self.reason_code = reason_code


class ModelGatewayRepository(Protocol):
    def recover(
        self,
        *,
        execution_envelope_ref: str,
        logical_request_digest: Digest,
    ) -> RecoveredModelCall | None: ...

    def prepare(
        self,
        *,
        manifest: AuthorizedInputManifest,
        request: ProviderRequest,
        receipt: IsolationReceipt,
        provider_type: str,
        adapter_version: str,
        requested_model_ref: str,
        execution_envelope_ref: str,
        logical_request_digest: Digest,
        occurred_at: datetime,
    ) -> ModelCallRecord: ...

    def transition(
        self,
        *,
        model_call_id: StableId,
        expected_revision: Revision,
        target: ModelCallState,
        response: AdapterResponse | None,
        failure_code: str | None,
        provider_http_failure_evidence: ModelProviderHTTPFailureEvidence | None,
        occurred_at: datetime,
    ) -> ModelCallRecord: ...

    def get(self, model_call_id: StableId) -> ModelCallRecord: ...

    def recover_by_id(self, model_call_id: StableId) -> RecoveredModelCall: ...

    def get_manifest(self, model_call_id: StableId) -> AuthorizedInputManifest: ...


class ModelGateway:
    def __init__(
        self,
        repository: ModelGatewayRepository,
        adapters: tuple[ProviderAdapter, ...] = (),
        *,
        id_generator: IdGenerator | None = None,
        clock: Callable[[], datetime] | None = None,
        telemetry: TelemetryRecorder | None = None,
    ) -> None:
        self._repository = repository
        self._adapters = {(item.provider_type, item.adapter_version): item for item in adapters}
        self._ids = id_generator or Uuid4IdGenerator()
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._telemetry = telemetry or NullTelemetryRecorder()

    def recover_call(self, model_call_id: StableId) -> RecoveredModelCall:
        return self._repository.recover_by_id(model_call_id)

    def authorized_manifest(
        self, model_call_id: StableId
    ) -> AuthorizedInputManifest:
        return self._repository.get_manifest(model_call_id)

    def preflight(self, context: ModelExecutionContext) -> None:
        """Validate a no-tools call without preparing, dispatching, or reading a secret."""

        self._preflight(context)

    def invoke(self, context: ModelExecutionContext) -> ModelGatewayResult:
        adapter = self._preflight(context)
        messages = tuple(
            RenderedMessage(
                role="system" if index == 0 else "user",
                content=item.content,
                input_item_id=item.item_id,
                input_item_digest=item.content_digest,
            )
            for index, item in enumerate(context.manifest.items)
            if item.disposition is InputDisposition.PROVIDED
        )
        assert messages
        request_core = {
            "manifest_digest": context.manifest.digest.value,
            "prompt_program_ref": context.prompt_program_ref,
            "rendering_contract_version": context.rendering_contract_version,
            "messages": messages,
            "output_schema_ref": context.output_schema_ref,
            "runtime_access_mode": context.runtime_access_mode.value,
            "platform_proposal_mode": context.platform_proposal_mode.value,
            "model_ref": context.requested_model_ref,
            "provider_type": context.provider_type,
            "adapter_version": context.adapter_version,
            "provider_configuration_fingerprint": context.provider_configuration_fingerprint.value,
            "max_output_tokens": context.max_output_tokens,
            "timeout_milliseconds": context.timeout_milliseconds,
        }
        request_digest = digest_of(request_core)
        logical_request_digest = digest_of(
            {
                "execution_envelope_ref": context.execution_envelope_ref,
                "manifest": {
                    "version": context.manifest.version.value,
                    "capability_id": context.manifest.capability_id,
                    "strategy_ref": context.manifest.strategy_ref,
                    "execution_stage": context.manifest.execution_stage,
                    "calling_module": context.manifest.calling_module,
                    "proposal_vocabulary_ref": (
                        context.manifest.proposal_vocabulary_ref
                    ),
                    "items": tuple(
                        {
                            "item_id": item.item_id,
                            "schema_ref": item.schema_ref,
                            "classification": item.classification,
                            "purpose": item.purpose,
                            "authority_reference": item.authority_reference,
                            "disposition": item.disposition.value,
                            "content_digest": item.content_digest.value,
                            "transformation_ref": item.transformation_ref,
                        }
                        for item in context.manifest.items
                    ),
                },
                "prompt_program_ref": context.prompt_program_ref,
                "rendering_contract_version": context.rendering_contract_version,
                "output_schema_ref": context.output_schema_ref,
                "runtime_access_mode": context.runtime_access_mode.value,
                "platform_proposal_mode": context.platform_proposal_mode.value,
                "model_ref": context.requested_model_ref,
                "provider_type": context.provider_type,
                "adapter_version": context.adapter_version,
                "provider_configuration_fingerprint": (
                    context.provider_configuration_fingerprint.value
                ),
                "max_output_tokens": context.max_output_tokens,
                "timeout_milliseconds": context.timeout_milliseconds,
                "classification": context.classification,
                "required_exact_fingerprint": context.required_exact_fingerprint,
            }
        )
        recovered = self._repository.recover(
            execution_envelope_ref=context.execution_envelope_ref,
            logical_request_digest=logical_request_digest,
        )
        if recovered is not None:
            return self._result(
                recovered.call,
                recovered.response,
                recovered.isolation_receipt,
                adapter.capabilities,
                context,
                replayed=True,
            )
        request = ProviderRequest(
            model_ref=context.requested_model_ref,
            messages=messages,
            output_schema_ref=context.output_schema_ref,
            tools=(),
            store=False,
            stream=False,
            max_output_tokens=context.max_output_tokens,
            timeout_milliseconds=context.timeout_milliseconds,
            metadata=(
                ("manifest_digest", context.manifest.digest.value),
                ("capability_id", context.manifest.capability_id),
            ),
            digest=request_digest,
        )
        issued_at = self._now()
        receipt_id = self._ids.new("isolation_receipt")
        receipt_core = {
            "receipt_id": receipt_id.value,
            "manifest_digest": context.manifest.digest.value,
            "provider_request_digest": request_digest.value,
            "provider_type": context.provider_type,
            "adapter_version": context.adapter_version,
            "provider_configuration_fingerprint": context.provider_configuration_fingerprint.value,
            "runtime_access_mode": context.runtime_access_mode.value,
            "platform_proposal_mode": context.platform_proposal_mode.value,
            "conformance_result_ref": adapter.capabilities.conformance_result_ref,
            "issued_at": issued_at,
        }
        receipt = IsolationReceipt(
            receipt_id=receipt_id,
            manifest_digest=context.manifest.digest,
            provider_request_digest=request_digest,
            provider_type=context.provider_type,
            adapter_version=context.adapter_version,
            provider_configuration_fingerprint=context.provider_configuration_fingerprint,
            runtime_access_mode=context.runtime_access_mode,
            platform_proposal_mode=context.platform_proposal_mode,
            conformance_result_ref=adapter.capabilities.conformance_result_ref,
            issued_at=issued_at,
            digest=digest_of(receipt_core),
        )
        call = self._repository.prepare(
            manifest=context.manifest,
            request=request,
            receipt=receipt,
            provider_type=context.provider_type,
            adapter_version=context.adapter_version,
            requested_model_ref=context.requested_model_ref,
            execution_envelope_ref=context.execution_envelope_ref,
            logical_request_digest=logical_request_digest,
            occurred_at=issued_at,
        )
        call = self._repository.transition(
            model_call_id=call.model_call_id,
            expected_revision=call.revision,
            target=ModelCallState.DISPATCHED,
            response=None,
            failure_code=None,
            provider_http_failure_evidence=None,
            occurred_at=self._now(),
        )
        try:
            response = adapter.invoke(request)
        except ProviderUnavailable:
            call = self._repository.transition(
                model_call_id=call.model_call_id,
                expected_revision=call.revision,
                target=ModelCallState.FAILED,
                response=None,
                failure_code="PROVIDER_UNAVAILABLE",
                provider_http_failure_evidence=None,
                occurred_at=self._now(),
            )
            return self._result(call, None, receipt, adapter.capabilities, context)
        except ProviderOutcomeUnknown:
            call = self._repository.transition(
                model_call_id=call.model_call_id,
                expected_revision=call.revision,
                target=ModelCallState.OUTCOME_UNKNOWN,
                response=None,
                failure_code="PROVIDER_OUTCOME_UNKNOWN",
                provider_http_failure_evidence=None,
                occurred_at=self._now(),
            )
            return self._result(call, None, receipt, adapter.capabilities, context)
        except ProviderOutputRejected as exc:
            call = self._repository.transition(
                model_call_id=call.model_call_id,
                expected_revision=call.revision,
                target=ModelCallState.COMPLETED,
                response=exc.response,
                failure_code=exc.code.value,
                provider_http_failure_evidence=None,
                occurred_at=self._now(),
            )
            return self._result(
                call, exc.response, receipt, adapter.capabilities, context
            )
        except Exception as exc:
            failure_code = (
                exc.code.value
                if isinstance(exc, DomainError)
                else type(exc).__name__
            )
            provider_http_failure_evidence = (
                ModelProviderHTTPFailureEvidence.seal(
                    model_call_id=call.model_call_id,
                    provider_request_digest=call.provider_request_digest,
                    isolation_receipt_digest=call.isolation_receipt_digest,
                    details=exc.details,
                )
                if isinstance(exc, DomainError)
                and exc.code is ErrorCode.PROVIDER_HTTP_ERROR
                else None
            )
            call = self._repository.transition(
                model_call_id=call.model_call_id,
                expected_revision=call.revision,
                target=ModelCallState.FAILED,
                response=None,
                failure_code=failure_code,
                provider_http_failure_evidence=provider_http_failure_evidence,
                occurred_at=self._now(),
            )
            return self._result(call, None, receipt, adapter.capabilities, context)
        call = self._repository.transition(
            model_call_id=call.model_call_id,
            expected_revision=call.revision,
            target=ModelCallState.COMPLETED,
            response=response,
            failure_code=None,
            provider_http_failure_evidence=None,
            occurred_at=self._now(),
        )
        return self._result(call, response, receipt, adapter.capabilities, context)

    def _result(
        self,
        call: ModelCallRecord,
        response: AdapterResponse | None,
        receipt: IsolationReceipt,
        capabilities: ProviderAdapterCapabilities,
        context: ModelExecutionContext,
        *,
        replayed: bool = False,
    ) -> ModelGatewayResult:
        evidence = call.provider_http_failure_evidence
        if evidence is not None:
            evidence.require_exact()
        if evidence is not None and (
            call.state is not ModelCallState.FAILED
            or call.failure_code != ErrorCode.PROVIDER_HTTP_ERROR.value
            or evidence.model_call_id != call.model_call_id
            or evidence.provider_request_digest != call.provider_request_digest
            or evidence.isolation_receipt_digest
            != call.isolation_receipt_digest
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Model call and Provider HTTP failure evidence disagree",
            )
        if call.state is not ModelCallState.COMPLETED:
            reason = f"MODEL_CALL_{call.state.value}"
            eligible = False
        elif capabilities.conformance_level is not AdapterConformanceLevel.LIVE_CURRENT:
            reason = "OFFLINE_FIXTURE_CANNOT_SIGN_LIVE_ELIGIBILITY"
            eligible = False
        elif response is None or response.actual_model_fingerprint is None:
            reason = "MODEL_FINGERPRINT_UNRESOLVED"
            eligible = False
        elif not response.usage_complete:
            reason = "MODEL_USAGE_INCOMPLETE"
            eligible = False
        elif response.replay_classification is ReplayClassification.UNRESOLVED_MUTABLE:
            reason = "MODEL_FINGERPRINT_UNRESOLVED_MUTABLE"
            eligible = False
        elif response.actual_model_fingerprint not in capabilities.qualified_model_fingerprints:
            reason = "MODEL_FINGERPRINT_NOT_EVALUATED"
            eligible = False
        elif call.failure_code:
            reason = f"MODEL_OUTPUT_REJECTED_{call.failure_code}"
            eligible = False
        else:
            reason = "ELIGIBLE"
            eligible = True
        core = {
            "eligible": eligible,
            "reason": reason,
            "actual_model_fingerprint": response.actual_model_fingerprint if response else None,
            "isolation_receipt_id": receipt.receipt_id.value,
            "model_call_id": call.model_call_id.value,
        }
        eligibility = ModelResultEligibility(
            eligible_for_production_domain_output=eligible,
            reason=reason,
            actual_model_fingerprint=response.actual_model_fingerprint if response else None,
            isolation_receipt_id=receipt.receipt_id,
            model_call_id=call.model_call_id,
            digest=digest_of(core),
        )
        metrics: list[TelemetryMetric] = []
        if call.input_tokens is not None:
            metrics.append(TelemetryMetric("input_tokens", call.input_tokens, "tokens"))
        if call.output_tokens is not None:
            metrics.append(TelemetryMetric("output_tokens", call.output_tokens, "tokens"))
        self._telemetry.record(
            owner="ai-infrastructure",
            operation="model-call@1",
            outcome=(f"REPLAYED_{call.state.value}" if replayed else call.state.value),
            correlation_reference=context.execution_envelope_ref,
            causation_reference=context.manifest.manifest_id.value,
            authority_references=(
                call.model_call_id.value,
                receipt.receipt_id.value,
                eligibility.digest.value,
            ),
            metrics=tuple(metrics),
            classification=context.classification,
        )
        return ModelGatewayResult(call, response, receipt, eligibility, replayed)

    @staticmethod
    def _validate_context(
        context: ModelExecutionContext, capabilities: ProviderAdapterCapabilities
    ) -> None:
        if context.runtime_access_mode is not RuntimeAccessMode.NO_EXTERNAL_ACCESS:
            raise DomainError(
                ErrorCode.LIVE_INTEGRATION_HELD,
                "the current model gateway slice permits no-tools execution only",
            )
        if not (
            capabilities.no_external_access
            and capabilities.hidden_context_disabled
            and capabilities.stateless_session
        ):
            raise DomainError(
                ErrorCode.LIVE_INTEGRATION_HELD,
                "adapter cannot mechanically prove the required isolation",
            )
        if capabilities.conformance_level is AdapterConformanceLevel.LIVE_STALE:
            raise DomainError(ErrorCode.LIVE_INTEGRATION_HELD, "adapter conformance is stale")
        if context.required_exact_fingerprint and not capabilities.actual_fingerprint_reported:
            raise DomainError(
                ErrorCode.LIVE_INTEGRATION_HELD,
                "adapter cannot report the actual model fingerprint",
            )
        if context.max_output_tokens < 1 or context.timeout_milliseconds < 1:
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "model resource bounds must be positive")

    def _preflight(self, context: ModelExecutionContext) -> ProviderAdapter:
        adapter = self._adapters.get(
            (context.provider_type, context.adapter_version)
        )
        if adapter is None:
            raise DomainError(
                ErrorCode.LIVE_INTEGRATION_HELD,
                "model provider is not configured",
            )
        self._validate_context(context, adapter.capabilities)
        if not any(
            item.disposition is InputDisposition.PROVIDED
            for item in context.manifest.items
        ):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "manifest has no renderable input",
            )
        return adapter

    def _now(self) -> datetime:
        value = self._clock()
        if value.tzinfo is None or value.utcoffset() is None:
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "clock must return an aware datetime")
        return value.astimezone(timezone.utc)


def _text(value: str, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} must be non-empty")
    return value


def _safe_provider_error_token(value: object) -> str | None:
    if (
        isinstance(value, str)
        and 0 < len(value) <= 128
        and re.fullmatch(r"[A-Za-z0-9._-]+", value)
    ):
        return value
    return None


def _safe_provider_request_id(value: object) -> str | None:
    if (
        isinstance(value, str)
        and value == value.strip()
        and 0 < len(value) <= 256
        and all(0x20 <= ord(character) <= 0x7E for character in value)
    ):
        return value
    return None
