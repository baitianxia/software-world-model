"""Fail-closed admission for planned DeepSeek development dispatches.

The policy is intentionally independent from Provider transport code.  A
controller seals one run-level receipt before any DeepSeek credential, TLS, or
HTTP work and then authorizes each exact model execution envelope against that
same receipt.  The caller may inject a clock for deterministic boundary tests.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta, timezone
from enum import Enum
from threading import Lock
from typing import Callable
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from software_world_model.cross_cutting import (
    Digest,
    DomainError,
    ErrorCode,
    digest_of,
)


DEEPSEEK_DISPATCH_ADMISSION_POLICY_REF = "ITER-010-PDR-007@2"
DEEPSEEK_DISPATCH_ADMISSION_SCHEMA = "DEEPSEEK_DISPATCH_ADMISSION@1"
DEEPSEEK_DISPATCH_AUTHORIZATION_SCHEMA = (
    "DEEPSEEK_DISPATCH_AUTHORIZATION@1"
)
DEEPSEEK_OFF_PEAK_TIMEZONE = "Asia/Shanghai"
DEEPSEEK_OFF_PEAK_WINDOWS = (
    "MONDAY-FRIDAY 00:00-09:00",
    "MONDAY-FRIDAY 12:00-14:00",
    "MONDAY-FRIDAY 18:00-24:00",
    "SATURDAY-SUNDAY 00:00-24:00",
)
DEEPSEEK_PRICING_SOURCE = (
    "https://api-docs.deepseek.com/quick_start/pricing/"
)
DEEPSEEK_PRICING_CHECK_MAXIMUM_AGE_SECONDS = 900


class DeepSeekPricingEffectiveStatus(str, Enum):
    EFFECTIVE = "EFFECTIVE"
    NOT_YET_EFFECTIVE = "NOT_YET_EFFECTIVE"
    CHANGED = "CHANGED"


class DeepSeekDispatchAdmissionDecision(str, Enum):
    ALLOWED_OFF_PEAK = "ALLOWED_OFF_PEAK"
    ALLOWED_EXACT_PEAK_OVERRIDE = "ALLOWED_EXACT_PEAK_OVERRIDE"
    DENIED_RUN_AUTHORITY = "DENIED_RUN_AUTHORITY"
    DENIED_PRICING_CHECK = "DENIED_PRICING_CHECK"
    DENIED_PRICING_CHANGED = "DENIED_PRICING_CHANGED"
    DENIED_PEAK_WINDOW = "DENIED_PEAK_WINDOW"
    DENIED_INSUFFICIENT_WINDOW = "DENIED_INSUFFICIENT_WINDOW"

    @property
    def allowed(self) -> bool:
        return self in {
            self.ALLOWED_OFF_PEAK,
            self.ALLOWED_EXACT_PEAK_OVERRIDE,
        }


@dataclass(frozen=True, slots=True)
class DeepSeekOfficialPricingCheck:
    source: str
    checked_at: datetime
    content_digest: Digest
    content_summary: str
    effective_status: DeepSeekPricingEffectiveStatus
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        source: str,
        checked_at: datetime,
        content_digest: Digest,
        content_summary: str,
        effective_status: DeepSeekPricingEffectiveStatus,
    ) -> "DeepSeekOfficialPricingCheck":
        source = _text(source, "DeepSeek pricing source")
        summary = _text(content_summary, "DeepSeek pricing content summary")
        current = _aware_utc(checked_at, "DeepSeek pricing check time")
        if (
            source != DEEPSEEK_PRICING_SOURCE
            or not isinstance(content_digest, Digest)
            or not isinstance(effective_status, DeepSeekPricingEffectiveStatus)
            or len(summary.encode("utf-8")) > 4_096
        ):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "DeepSeek official pricing check is invalid",
            )
        core = {
            "schema": "DEEPSEEK_OFFICIAL_PRICING_CHECK@1",
            "source": source,
            "checked_at": _time(current),
            "content_digest": content_digest.value,
            "content_summary": summary,
            "effective_status": effective_status.value,
        }
        return cls(
            source=source,
            checked_at=current,
            content_digest=content_digest,
            content_summary=summary,
            effective_status=effective_status,
            digest=digest_of(core),
        )


@dataclass(frozen=True, slots=True)
class DeepSeekPeakOverride:
    run_ref: str
    turn_scope_digest: Digest
    product_revision: str
    source_revision: str
    session_ref: str
    provider_configuration_digest: Digest
    model_ref: str
    reason: str
    authorization_message_digest: Digest
    authorized_at: datetime
    expires_at: datetime
    maximum_calls: int
    maximum_input_tokens: int
    maximum_output_tokens: int
    maximum_duration_seconds: int
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        run_ref: str,
        turn_scope_digest: Digest,
        product_revision: str,
        source_revision: str,
        session_ref: str,
        provider_configuration_digest: Digest,
        model_ref: str,
        reason: str,
        authorization_message_digest: Digest,
        authorized_at: datetime,
        expires_at: datetime,
        maximum_calls: int,
        maximum_input_tokens: int,
        maximum_output_tokens: int,
        maximum_duration_seconds: int,
    ) -> "DeepSeekPeakOverride":
        texts = tuple(
            _text(value, label)
            for value, label in (
                (run_ref, "DeepSeek override run reference"),
                (product_revision, "DeepSeek override product revision"),
                (source_revision, "DeepSeek override Source revision"),
                (session_ref, "DeepSeek override Session reference"),
                (model_ref, "DeepSeek override model reference"),
                (reason, "DeepSeek override reason"),
            )
        )
        start = _aware_utc(authorized_at, "DeepSeek override authorization time")
        end = _aware_utc(expires_at, "DeepSeek override expiry")
        _require_digests(
            turn_scope_digest,
            provider_configuration_digest,
            authorization_message_digest,
        )
        _require_positive_budgets(
            maximum_calls,
            maximum_input_tokens,
            maximum_output_tokens,
            maximum_duration_seconds,
        )
        if end <= start:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "DeepSeek peak override expiry must follow authorization",
            )
        core = {
            "schema": "DEEPSEEK_PEAK_OVERRIDE@1",
            "run_ref": texts[0],
            "turn_scope_digest": turn_scope_digest.value,
            "product_revision": texts[1],
            "source_revision": texts[2],
            "session_ref": texts[3],
            "provider_type": "DEEPSEEK",
            "provider_configuration_digest": provider_configuration_digest.value,
            "model_ref": texts[4],
            "reason": texts[5],
            "authorization_message_digest": authorization_message_digest.value,
            "authorized_at": _time(start),
            "expires_at": _time(end),
            "maximum_calls": maximum_calls,
            "maximum_input_tokens": maximum_input_tokens,
            "maximum_output_tokens": maximum_output_tokens,
            "maximum_duration_seconds": maximum_duration_seconds,
            "standing_override": False,
        }
        return cls(
            run_ref=texts[0],
            turn_scope_digest=turn_scope_digest,
            product_revision=texts[1],
            source_revision=texts[2],
            session_ref=texts[3],
            provider_configuration_digest=provider_configuration_digest,
            model_ref=texts[4],
            reason=texts[5],
            authorization_message_digest=authorization_message_digest,
            authorized_at=start,
            expires_at=end,
            maximum_calls=maximum_calls,
            maximum_input_tokens=maximum_input_tokens,
            maximum_output_tokens=maximum_output_tokens,
            maximum_duration_seconds=maximum_duration_seconds,
            digest=digest_of(core),
        )


@dataclass(frozen=True, slots=True)
class DeepSeekDispatchAdmissionPlan:
    run_type: str
    run_ref: str
    turn_scope_digest: Digest
    product_revision: str
    source_revision: str
    session_ref: str
    provider_configuration_digest: Digest
    model_ref: str
    authorization_message_digest: Digest
    authorized_at: datetime
    expires_at: datetime
    maximum_calls: int
    maximum_input_tokens: int
    maximum_output_tokens: int
    maximum_duration_seconds: int
    pricing_check: DeepSeekOfficialPricingCheck
    peak_override: DeepSeekPeakOverride | None
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        run_type: str,
        run_ref: str,
        turn_scope_digest: Digest,
        product_revision: str,
        source_revision: str,
        session_ref: str,
        provider_configuration_digest: Digest,
        model_ref: str,
        authorization_message_digest: Digest,
        authorized_at: datetime,
        expires_at: datetime,
        maximum_calls: int,
        maximum_input_tokens: int,
        maximum_output_tokens: int,
        maximum_duration_seconds: int,
        pricing_check: DeepSeekOfficialPricingCheck,
        peak_override: DeepSeekPeakOverride | None = None,
    ) -> "DeepSeekDispatchAdmissionPlan":
        texts = tuple(
            _text(value, label)
            for value, label in (
                (run_type, "DeepSeek run type"),
                (run_ref, "DeepSeek run reference"),
                (product_revision, "DeepSeek product revision"),
                (source_revision, "DeepSeek Source revision"),
                (session_ref, "DeepSeek Session reference"),
                (model_ref, "DeepSeek model reference"),
            )
        )
        start = _aware_utc(authorized_at, "DeepSeek run authorization time")
        end = _aware_utc(expires_at, "DeepSeek run expiry")
        _require_digests(
            turn_scope_digest,
            provider_configuration_digest,
            authorization_message_digest,
        )
        _require_positive_budgets(
            maximum_calls,
            maximum_input_tokens,
            maximum_output_tokens,
            maximum_duration_seconds,
        )
        if (
            end <= start
            or not isinstance(pricing_check, DeepSeekOfficialPricingCheck)
            or (
                peak_override is not None
                and not isinstance(peak_override, DeepSeekPeakOverride)
            )
        ):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "DeepSeek dispatch admission plan is invalid",
            )
        core = {
            "schema": "DEEPSEEK_DISPATCH_ADMISSION_PLAN@1",
            "policy_ref": DEEPSEEK_DISPATCH_ADMISSION_POLICY_REF,
            "run_type": texts[0],
            "run_ref": texts[1],
            "turn_scope_digest": turn_scope_digest.value,
            "product_revision": texts[2],
            "source_revision": texts[3],
            "session_ref": texts[4],
            "provider_type": "DEEPSEEK",
            "provider_configuration_digest": provider_configuration_digest.value,
            "model_ref": texts[5],
            "authorization_message_digest": authorization_message_digest.value,
            "authorized_at": _time(start),
            "expires_at": _time(end),
            "maximum_calls": maximum_calls,
            "maximum_input_tokens": maximum_input_tokens,
            "maximum_output_tokens": maximum_output_tokens,
            "maximum_duration_seconds": maximum_duration_seconds,
            "timezone": DEEPSEEK_OFF_PEAK_TIMEZONE,
            "allowed_windows": DEEPSEEK_OFF_PEAK_WINDOWS,
            "pricing_check_digest": pricing_check.digest.value,
            "peak_override_digest": (
                peak_override.digest.value if peak_override is not None else None
            ),
        }
        return cls(
            run_type=texts[0],
            run_ref=texts[1],
            turn_scope_digest=turn_scope_digest,
            product_revision=texts[2],
            source_revision=texts[3],
            session_ref=texts[4],
            provider_configuration_digest=provider_configuration_digest,
            model_ref=texts[5],
            authorization_message_digest=authorization_message_digest,
            authorized_at=start,
            expires_at=end,
            maximum_calls=maximum_calls,
            maximum_input_tokens=maximum_input_tokens,
            maximum_output_tokens=maximum_output_tokens,
            maximum_duration_seconds=maximum_duration_seconds,
            pricing_check=pricing_check,
            peak_override=peak_override,
            digest=digest_of(core),
        )


@dataclass(frozen=True, slots=True)
class DeepSeekDispatchAdmissionReceipt:
    schema: str
    plan_digest: Digest
    decision: DeepSeekDispatchAdmissionDecision
    admitted_at: datetime
    valid_until: datetime | None
    local_time: str
    matched_window: str | None
    pricing_check_digest: Digest
    peak_override_digest: Digest | None
    maximum_calls: int
    maximum_input_tokens: int
    maximum_output_tokens: int
    maximum_duration_seconds: int
    digest: Digest

    @property
    def allowed(self) -> bool:
        return self.decision.allowed

    def public_status(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "policy_ref": DEEPSEEK_DISPATCH_ADMISSION_POLICY_REF,
            "plan_digest": self.plan_digest.value,
            "decision": self.decision.value,
            "admitted_at": _time(self.admitted_at),
            "valid_until": (
                _time(self.valid_until) if self.valid_until is not None else None
            ),
            "local_time": self.local_time,
            "timezone": DEEPSEEK_OFF_PEAK_TIMEZONE,
            "timezone_database": "PYTHON_ZONEINFO@1",
            "clock_source": "INJECTED_AWARE_UTC_CLOCK@1",
            "allowed_windows": DEEPSEEK_OFF_PEAK_WINDOWS,
            "matched_window": self.matched_window,
            "pricing_check_digest": self.pricing_check_digest.value,
            "peak_override_digest": (
                self.peak_override_digest.value
                if self.peak_override_digest is not None
                else None
            ),
            "maximum_calls": self.maximum_calls,
            "maximum_input_tokens": self.maximum_input_tokens,
            "maximum_output_tokens": self.maximum_output_tokens,
            "maximum_duration_seconds": self.maximum_duration_seconds,
            "credential_resolution_performed": False,
            "tls_attempt_count": 0,
            "provider_dispatch_count": 0,
            "digest": self.digest.value,
        }


@dataclass(frozen=True, slots=True)
class DeepSeekDispatchAuthorization:
    schema: str
    ordinal: int
    execution_envelope_ref: str
    admission_receipt_digest: Digest
    authorized_at: datetime
    input_token_upper_bound: int
    maximum_output_tokens: int
    digest: Digest


class DeepSeekDispatchAdmissionController:
    """Seal one run receipt and gate every exact DeepSeek model dispatch."""

    def __init__(
        self,
        *,
        plan: DeepSeekDispatchAdmissionPlan,
        admitted_at: datetime,
        clock: Callable[[], datetime],
    ) -> None:
        if not isinstance(plan, DeepSeekDispatchAdmissionPlan) or not callable(clock):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "DeepSeek admission controller requires one plan and clock",
            )
        current = _aware_utc(admitted_at, "DeepSeek admission time")
        self.plan = plan
        self._clock = clock
        self.receipt = _seal_receipt(plan, current)
        self._lock = Lock()
        self._authorizations: dict[str, DeepSeekDispatchAuthorization] = {}
        self._invoked_envelopes: set[str] = set()
        self._reserved_input_tokens = 0
        self._reserved_output_tokens = 0

    @property
    def authorizations(self) -> tuple[DeepSeekDispatchAuthorization, ...]:
        with self._lock:
            return tuple(self._authorizations.values())

    @property
    def invoked_envelopes(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(sorted(self._invoked_envelopes))

    def authorize_dispatch(
        self,
        *,
        execution_envelope_ref: str,
        input_token_upper_bound: int,
        maximum_output_tokens: int,
    ) -> DeepSeekDispatchAuthorization:
        envelope = _text(
            execution_envelope_ref,
            "DeepSeek execution envelope reference",
        )
        if (
            type(input_token_upper_bound) is not int
            or input_token_upper_bound < 1
            or type(maximum_output_tokens) is not int
            or maximum_output_tokens < 1
        ):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "DeepSeek dispatch token reservation is invalid",
            )
        current = _aware_utc(self._clock(), "DeepSeek dispatch clock")
        with self._lock:
            existing = self._authorizations.get(envelope)
            if existing is not None:
                if (
                    existing.input_token_upper_bound != input_token_upper_bound
                    or existing.maximum_output_tokens != maximum_output_tokens
                ):
                    raise DomainError(
                        ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                        "DeepSeek execution envelope was replayed with different bounds",
                    )
                return existing
            self._require_current(current)
            ordinal = len(self._authorizations) + 1
            if ordinal > self.plan.maximum_calls:
                raise DomainError(
                    ErrorCode.BUDGET_EXHAUSTED,
                    "DeepSeek dispatch call budget is exhausted",
                )
            if (
                self._reserved_input_tokens + input_token_upper_bound
                > self.plan.maximum_input_tokens
                or self._reserved_output_tokens + maximum_output_tokens
                > self.plan.maximum_output_tokens
            ):
                raise DomainError(
                    ErrorCode.BUDGET_EXHAUSTED,
                    "DeepSeek dispatch token budget is exhausted",
                )
            core = {
                "schema": DEEPSEEK_DISPATCH_AUTHORIZATION_SCHEMA,
                "ordinal": ordinal,
                "execution_envelope_ref": envelope,
                "admission_receipt_digest": self.receipt.digest.value,
                "authorized_at": _time(current),
                "input_token_upper_bound": input_token_upper_bound,
                "maximum_output_tokens": maximum_output_tokens,
                "request_retry_count": 0,
            }
            authorization = DeepSeekDispatchAuthorization(
                schema=DEEPSEEK_DISPATCH_AUTHORIZATION_SCHEMA,
                ordinal=ordinal,
                execution_envelope_ref=envelope,
                admission_receipt_digest=self.receipt.digest,
                authorized_at=current,
                input_token_upper_bound=input_token_upper_bound,
                maximum_output_tokens=maximum_output_tokens,
                digest=digest_of(core),
            )
            self._authorizations[envelope] = authorization
            self._reserved_input_tokens += input_token_upper_bound
            self._reserved_output_tokens += maximum_output_tokens
            return authorization

    def mark_invoked(self, execution_envelope_ref: str) -> None:
        envelope = _text(
            execution_envelope_ref,
            "DeepSeek invoked execution envelope reference",
        )
        current = _aware_utc(self._clock(), "DeepSeek dispatch clock")
        with self._lock:
            if envelope not in self._authorizations:
                raise DomainError(
                    ErrorCode.CONTROL_STATE_DENIED,
                    "DeepSeek dispatch has no admission authorization",
                )
            self._require_current(current)
            if envelope in self._invoked_envelopes:
                raise DomainError(
                    ErrorCode.CONTROL_STATE_DENIED,
                    "DeepSeek admitted dispatch cannot be invoked twice",
                )
            self._invoked_envelopes.add(envelope)

    def public_audit(self) -> dict[str, object]:
        with self._lock:
            authorizations = tuple(self._authorizations.values())
            invoked = tuple(sorted(self._invoked_envelopes))
            reserved_input = self._reserved_input_tokens
            reserved_output = self._reserved_output_tokens
        return {
            "admission_receipt": self.receipt.public_status(),
            "dispatch_authorization_digests": tuple(
                item.digest.value for item in authorizations
            ),
            "execution_envelope_refs": tuple(
                item.execution_envelope_ref for item in authorizations
            ),
            "invoked_execution_envelope_refs": invoked,
            "reserved_input_token_upper_bound": reserved_input,
            "reserved_output_tokens": reserved_output,
            "authorized_dispatch_count": len(authorizations),
            "invoked_dispatch_count": len(invoked),
        }

    def _require_current(self, current: datetime) -> None:
        if not self.receipt.allowed or self.receipt.valid_until is None:
            raise DomainError(
                ErrorCode.CONTROL_STATE_DENIED,
                "DeepSeek dispatch admission denied this planned run",
                {"decision": self.receipt.decision.value},
            )
        if current < self.receipt.admitted_at or current >= self.receipt.valid_until:
            raise DomainError(
                ErrorCode.CONTROL_STATE_DENIED,
                "DeepSeek dispatch admission is not current",
            )
        if self.receipt.decision is DeepSeekDispatchAdmissionDecision.ALLOWED_OFF_PEAK:
            window = _off_peak_window(current)
            if window is None:
                raise DomainError(
                    ErrorCode.CONTROL_STATE_DENIED,
                    "DeepSeek dispatch crossed outside the off-peak schedule",
                )
        else:
            override = self.plan.peak_override
            if override is None or not _override_matches(self.plan, override, current):
                raise DomainError(
                    ErrorCode.CONTROL_STATE_DENIED,
                    "DeepSeek peak override is not current for this exact run",
                )


def _seal_receipt(
    plan: DeepSeekDispatchAdmissionPlan,
    current: datetime,
) -> DeepSeekDispatchAdmissionReceipt:
    decision, matched_window, valid_until, override_digest = _decision(
        plan,
        current,
    )
    local = _local_time(current)
    core = {
        "schema": DEEPSEEK_DISPATCH_ADMISSION_SCHEMA,
        "policy_ref": DEEPSEEK_DISPATCH_ADMISSION_POLICY_REF,
        "plan_digest": plan.digest.value,
        "decision": decision.value,
        "admitted_at": _time(current),
        "valid_until": _time(valid_until) if valid_until is not None else None,
        "local_time": local.isoformat(),
        "timezone": DEEPSEEK_OFF_PEAK_TIMEZONE,
        "timezone_database": "PYTHON_ZONEINFO@1",
        "clock_source": "INJECTED_AWARE_UTC_CLOCK@1",
        "allowed_windows": DEEPSEEK_OFF_PEAK_WINDOWS,
        "matched_window": matched_window,
        "pricing_check_digest": plan.pricing_check.digest.value,
        "peak_override_digest": (
            override_digest.value if override_digest is not None else None
        ),
        "maximum_calls": plan.maximum_calls,
        "maximum_input_tokens": plan.maximum_input_tokens,
        "maximum_output_tokens": plan.maximum_output_tokens,
        "maximum_duration_seconds": plan.maximum_duration_seconds,
        "credential_resolution_performed": False,
        "tls_attempt_count": 0,
        "provider_dispatch_count": 0,
    }
    return DeepSeekDispatchAdmissionReceipt(
        schema=DEEPSEEK_DISPATCH_ADMISSION_SCHEMA,
        plan_digest=plan.digest,
        decision=decision,
        admitted_at=current,
        valid_until=valid_until,
        local_time=local.isoformat(),
        matched_window=matched_window,
        pricing_check_digest=plan.pricing_check.digest,
        peak_override_digest=override_digest,
        maximum_calls=plan.maximum_calls,
        maximum_input_tokens=plan.maximum_input_tokens,
        maximum_output_tokens=plan.maximum_output_tokens,
        maximum_duration_seconds=plan.maximum_duration_seconds,
        digest=digest_of(core),
    )


def _decision(
    plan: DeepSeekDispatchAdmissionPlan,
    current: datetime,
) -> tuple[
    DeepSeekDispatchAdmissionDecision,
    str | None,
    datetime | None,
    Digest | None,
]:
    if current < plan.authorized_at or current >= plan.expires_at:
        return (
            DeepSeekDispatchAdmissionDecision.DENIED_RUN_AUTHORITY,
            None,
            None,
            None,
        )
    check_age = (current - plan.pricing_check.checked_at).total_seconds()
    if check_age < 0 or check_age > DEEPSEEK_PRICING_CHECK_MAXIMUM_AGE_SECONDS:
        return (
            DeepSeekDispatchAdmissionDecision.DENIED_PRICING_CHECK,
            None,
            None,
            None,
        )
    if plan.pricing_check.effective_status is DeepSeekPricingEffectiveStatus.CHANGED:
        return (
            DeepSeekDispatchAdmissionDecision.DENIED_PRICING_CHANGED,
            None,
            None,
            None,
        )
    window = _off_peak_window(current)
    duration_end = current + timedelta(seconds=plan.maximum_duration_seconds)
    if window is not None:
        window_ref, window_end = window
        valid_until = min(window_end, duration_end, plan.expires_at)
        if duration_end <= window_end and duration_end <= plan.expires_at:
            return (
                DeepSeekDispatchAdmissionDecision.ALLOWED_OFF_PEAK,
                window_ref,
                valid_until,
                None,
            )
        denied = DeepSeekDispatchAdmissionDecision.DENIED_INSUFFICIENT_WINDOW
    else:
        denied = DeepSeekDispatchAdmissionDecision.DENIED_PEAK_WINDOW
    override = plan.peak_override
    if override is not None and _override_matches(plan, override, current):
        valid_until = min(duration_end, plan.expires_at, override.expires_at)
        if duration_end <= valid_until:
            return (
                DeepSeekDispatchAdmissionDecision.ALLOWED_EXACT_PEAK_OVERRIDE,
                None,
                valid_until,
                override.digest,
            )
    return denied, window[0] if window is not None else None, None, None


def _override_matches(
    plan: DeepSeekDispatchAdmissionPlan,
    override: DeepSeekPeakOverride,
    current: datetime,
) -> bool:
    return (
        override.run_ref == plan.run_ref
        and override.turn_scope_digest == plan.turn_scope_digest
        and override.product_revision == plan.product_revision
        and override.source_revision == plan.source_revision
        and override.session_ref == plan.session_ref
        and override.provider_configuration_digest
        == plan.provider_configuration_digest
        and override.model_ref == plan.model_ref
        and override.authorized_at <= current < override.expires_at
        and plan.maximum_calls <= override.maximum_calls
        and plan.maximum_input_tokens <= override.maximum_input_tokens
        and plan.maximum_output_tokens <= override.maximum_output_tokens
        and plan.maximum_duration_seconds <= override.maximum_duration_seconds
        and current + timedelta(seconds=plan.maximum_duration_seconds)
        <= override.expires_at
    )


def _off_peak_window(value: datetime) -> tuple[str, datetime] | None:
    local = _local_time(value)
    minute = local.hour * 60 + local.minute
    weekday = local.weekday()
    if weekday >= 5:
        days_until_monday = 7 - weekday
        end_local = datetime.combine(
            local.date() + timedelta(days=days_until_monday),
            time(hour=9),
            tzinfo=local.tzinfo,
        )
        return (
            DEEPSEEK_OFF_PEAK_WINDOWS[3],
            end_local.astimezone(timezone.utc),
        )
    if minute < 9 * 60:
        end_local = local.replace(
            hour=9,
            minute=0,
            second=0,
            microsecond=0,
        )
        return DEEPSEEK_OFF_PEAK_WINDOWS[0], end_local.astimezone(timezone.utc)
    if 12 * 60 <= minute < 14 * 60:
        end_local = local.replace(
            hour=14,
            minute=0,
            second=0,
            microsecond=0,
        )
        return DEEPSEEK_OFF_PEAK_WINDOWS[1], end_local.astimezone(timezone.utc)
    if 18 * 60 <= minute:
        days_until_morning_end = 3 if weekday == 4 else 1
        end_local = datetime.combine(
            local.date() + timedelta(days=days_until_morning_end),
            time(hour=9),
            tzinfo=local.tzinfo,
        )
        return DEEPSEEK_OFF_PEAK_WINDOWS[2], end_local.astimezone(timezone.utc)
    return None


def _local_time(value: datetime) -> datetime:
    try:
        zone = ZoneInfo(DEEPSEEK_OFF_PEAK_TIMEZONE)
    except ZoneInfoNotFoundError as exc:
        raise DomainError(
            ErrorCode.CONTROL_STATE_DENIED,
            "DeepSeek schedule timezone database is unavailable",
        ) from exc
    return value.astimezone(zone)


def _require_positive_budgets(*values: int) -> None:
    if any(type(value) is not int or value < 1 for value in values):
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            "DeepSeek admission budgets must be positive integers",
        )


def _require_digests(*values: Digest) -> None:
    if any(not isinstance(value, Digest) for value in values):
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            "DeepSeek admission identities must be exact digests",
        )


def _aware_utc(value: datetime, label: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            f"{label} must be timezone-aware",
        )
    return value.astimezone(timezone.utc)


def _time(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _text(value: str, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} must be non-empty")
    return value


__all__ = [
    "DEEPSEEK_DISPATCH_ADMISSION_POLICY_REF",
    "DEEPSEEK_DISPATCH_ADMISSION_SCHEMA",
    "DEEPSEEK_DISPATCH_AUTHORIZATION_SCHEMA",
    "DEEPSEEK_OFF_PEAK_TIMEZONE",
    "DEEPSEEK_OFF_PEAK_WINDOWS",
    "DEEPSEEK_PRICING_CHECK_MAXIMUM_AGE_SECONDS",
    "DEEPSEEK_PRICING_SOURCE",
    "DeepSeekDispatchAdmissionController",
    "DeepSeekDispatchAdmissionDecision",
    "DeepSeekDispatchAdmissionPlan",
    "DeepSeekDispatchAdmissionReceipt",
    "DeepSeekDispatchAuthorization",
    "DeepSeekOfficialPricingCheck",
    "DeepSeekPeakOverride",
    "DeepSeekPricingEffectiveStatus",
]
