from __future__ import annotations

from datetime import datetime, timedelta, timezone
import unittest

from software_world_model.application_services.deepseek_dispatch_admission import (
    DEEPSEEK_OFF_PEAK_WINDOWS,
    DEEPSEEK_PRICING_SOURCE,
    DeepSeekDispatchAdmissionController,
    DeepSeekDispatchAdmissionDecision,
    DeepSeekDispatchAdmissionPlan,
    DeepSeekOfficialPricingCheck,
    DeepSeekPeakOverride,
    DeepSeekPricingEffectiveStatus,
)
from software_world_model.cross_cutting import Digest, DomainError, digest_of


class _Clock:
    def __init__(self, value: datetime) -> None:
        self.value = value

    def __call__(self) -> datetime:
        return self.value


class DeepSeekDispatchAdmissionTests(unittest.TestCase):
    def _at(
        self,
        hour: int,
        minute: int = 0,
        second: int = 0,
        *,
        day: int = 27,
    ) -> datetime:
        shanghai = timezone(timedelta(hours=8))
        return datetime(
            2026,
            8,
            day,
            hour,
            minute,
            second,
            tzinfo=shanghai,
        ).astimezone(timezone.utc)

    def _plan(
        self,
        current: datetime,
        *,
        duration: int = 60,
        override: DeepSeekPeakOverride | None = None,
        status: DeepSeekPricingEffectiveStatus = (
            DeepSeekPricingEffectiveStatus.EFFECTIVE
        ),
    ) -> DeepSeekDispatchAdmissionPlan:
        return DeepSeekDispatchAdmissionPlan.create(
            run_type="DIRECTION_CANARY",
            run_ref="run-044",
            turn_scope_digest=digest_of("five-frozen-turns"),
            product_revision="a" * 40,
            source_revision="b" * 40,
            session_ref="iter-010-run-044",
            provider_configuration_digest=digest_of("deepseek-config"),
            model_ref="deepseek-v4-pro",
            authorization_message_digest=digest_of("exact-grant"),
            authorized_at=current - timedelta(minutes=1),
            expires_at=current + timedelta(hours=8),
            maximum_calls=75,
            maximum_input_tokens=10_000_000,
            maximum_output_tokens=75 * 8_192,
            maximum_duration_seconds=duration,
            pricing_check=DeepSeekOfficialPricingCheck.create(
                source=DEEPSEEK_PRICING_SOURCE,
                checked_at=current - timedelta(seconds=30),
                content_digest=digest_of("official-pricing-page"),
                content_summary=(
                    "官方页面定义北京时间周一至周五高峰，周末全天闲时，"
                    "峰谷价格已经生效。"
                ),
                effective_status=status,
            ),
            peak_override=override,
        )

    def test_half_open_window_boundaries(self) -> None:
        cases = (
            (self._at(8, 59, 59), True),
            (self._at(9, 0, 0), False),
            (self._at(12, 0, 0), True),
            (self._at(14, 0, 0), False),
            (self._at(18, 0, 0), True),
        )
        for current, allowed in cases:
            with self.subTest(current=current):
                clock = _Clock(current)
                controller = DeepSeekDispatchAdmissionController(
                    plan=self._plan(current, duration=1),
                    admitted_at=current,
                    clock=clock,
                )
                self.assertEqual(controller.receipt.allowed, allowed)

    def test_weekend_is_off_peak_all_day(self) -> None:
        cases = (
            self._at(0, 0, 0, day=29),
            self._at(11, 0, 0, day=29),
            self._at(17, 0, 0, day=30),
            self._at(23, 59, 59, day=30),
        )
        for current in cases:
            with self.subTest(current=current):
                controller = DeepSeekDispatchAdmissionController(
                    plan=self._plan(current, duration=1),
                    admitted_at=current,
                    clock=_Clock(current),
                )
                self.assertEqual(
                    controller.receipt.decision,
                    DeepSeekDispatchAdmissionDecision.ALLOWED_OFF_PEAK,
                )
                self.assertEqual(
                    controller.receipt.matched_window,
                    "SATURDAY-SUNDAY 00:00-24:00",
                )
                self.assertEqual(
                    controller.receipt.public_status()["allowed_windows"],
                    DEEPSEEK_OFF_PEAK_WINDOWS,
                )
                self.assertEqual(
                    controller.receipt.public_status()["policy_ref"],
                    "ITER-010-PDR-007@3",
                )

        monday_peak = self._at(11, 0, 0, day=31)
        controller = DeepSeekDispatchAdmissionController(
            plan=self._plan(monday_peak, duration=1),
            admitted_at=monday_peak,
            clock=_Clock(monday_peak),
        )
        self.assertEqual(
            controller.receipt.decision,
            DeepSeekDispatchAdmissionDecision.DENIED_PEAK_WINDOW,
        )

    def test_contiguous_off_peak_span_crosses_into_weekend(self) -> None:
        current = self._at(23, 59, 0, day=28)
        clock = _Clock(current)
        controller = DeepSeekDispatchAdmissionController(
            plan=self._plan(current, duration=180),
            admitted_at=current,
            clock=clock,
        )
        first = controller.authorize_dispatch(
            execution_envelope_ref="deepseek:friday",
            input_token_upper_bound=1_000,
            maximum_output_tokens=8_192,
        )
        controller.mark_invoked(first.execution_envelope_ref)

        clock.value = self._at(0, 0, 0, day=29)
        second = controller.authorize_dispatch(
            execution_envelope_ref="deepseek:saturday",
            input_token_upper_bound=1_000,
            maximum_output_tokens=8_192,
        )
        controller.mark_invoked(second.execution_envelope_ref)
        self.assertEqual(controller.public_audit()["invoked_dispatch_count"], 2)

    def test_peak_denial_happens_before_any_dispatch_authorization(self) -> None:
        current = self._at(11, 19)
        controller = DeepSeekDispatchAdmissionController(
            plan=self._plan(current),
            admitted_at=current,
            clock=_Clock(current),
        )
        self.assertEqual(
            controller.receipt.decision,
            DeepSeekDispatchAdmissionDecision.DENIED_PEAK_WINDOW,
        )
        with self.assertRaises(DomainError):
            controller.authorize_dispatch(
                execution_envelope_ref="deepseek:1",
                input_token_upper_bound=1_000,
                maximum_output_tokens=8_192,
            )
        self.assertEqual(controller.public_audit()["authorized_dispatch_count"], 0)

    def test_exact_override_matches_identity_budgets_and_time(self) -> None:
        current = self._at(11, 19)
        base = self._plan(current)
        override = DeepSeekPeakOverride.create(
            run_ref=base.run_ref,
            turn_scope_digest=base.turn_scope_digest,
            product_revision=base.product_revision,
            source_revision=base.source_revision,
            session_ref=base.session_ref,
            provider_configuration_digest=base.provider_configuration_digest,
            model_ref=base.model_ref,
            reason="用户要求在本次冻结 run 中立即验证。",
            authorization_message_digest=digest_of("exact-peak-override-grant"),
            authorized_at=current - timedelta(minutes=1),
            expires_at=current + timedelta(minutes=10),
            maximum_calls=base.maximum_calls,
            maximum_input_tokens=base.maximum_input_tokens,
            maximum_output_tokens=base.maximum_output_tokens,
            maximum_duration_seconds=base.maximum_duration_seconds,
        )
        plan = self._plan(current, override=override)
        controller = DeepSeekDispatchAdmissionController(
            plan=plan,
            admitted_at=current,
            clock=_Clock(current),
        )
        self.assertEqual(
            controller.receipt.decision,
            DeepSeekDispatchAdmissionDecision.ALLOWED_EXACT_PEAK_OVERRIDE,
        )
        self.assertEqual(controller.receipt.peak_override_digest, override.digest)

        wrong = DeepSeekPeakOverride.create(
            run_ref=base.run_ref,
            turn_scope_digest=base.turn_scope_digest,
            product_revision=base.product_revision,
            source_revision=base.source_revision,
            session_ref=base.session_ref,
            provider_configuration_digest=base.provider_configuration_digest,
            model_ref=base.model_ref,
            reason="wrong run",
            authorization_message_digest=digest_of("undersized-override-grant"),
            authorized_at=current - timedelta(minutes=1),
            expires_at=current + timedelta(minutes=10),
            maximum_calls=base.maximum_calls - 1,
            maximum_input_tokens=base.maximum_input_tokens,
            maximum_output_tokens=base.maximum_output_tokens,
            maximum_duration_seconds=base.maximum_duration_seconds,
        )
        denied = DeepSeekDispatchAdmissionController(
            plan=self._plan(current, override=wrong),
            admitted_at=current,
            clock=_Clock(current),
        )
        self.assertFalse(denied.receipt.allowed)

    def test_new_dispatch_is_blocked_after_window_closes(self) -> None:
        current = self._at(8, 58)
        clock = _Clock(current)
        controller = DeepSeekDispatchAdmissionController(
            plan=self._plan(current, duration=60),
            admitted_at=current,
            clock=clock,
        )
        first = controller.authorize_dispatch(
            execution_envelope_ref="deepseek:1",
            input_token_upper_bound=1_000,
            maximum_output_tokens=8_192,
        )
        controller.mark_invoked(first.execution_envelope_ref)
        clock.value = self._at(9, 0)
        with self.assertRaises(DomainError):
            controller.authorize_dispatch(
                execution_envelope_ref="deepseek:2",
                input_token_upper_bound=1_000,
                maximum_output_tokens=8_192,
            )
        self.assertEqual(controller.public_audit()["invoked_dispatch_count"], 1)

    def test_each_invoked_dispatch_points_to_same_receipt(self) -> None:
        current = self._at(12, 0)
        clock = _Clock(current)
        controller = DeepSeekDispatchAdmissionController(
            plan=self._plan(current, duration=600),
            admitted_at=current,
            clock=clock,
        )
        authorizations = []
        for ordinal in range(1, 3):
            item = controller.authorize_dispatch(
                execution_envelope_ref=f"deepseek:{ordinal}",
                input_token_upper_bound=1_000,
                maximum_output_tokens=8_192,
            )
            controller.mark_invoked(item.execution_envelope_ref)
            authorizations.append(item)
        self.assertEqual(
            {item.admission_receipt_digest for item in authorizations},
            {controller.receipt.digest},
        )
        self.assertEqual(controller.public_audit()["invoked_dispatch_count"], 2)

    def test_fallback_duration_starts_at_first_deepseek_preflight(self) -> None:
        prepared_at = self._at(18, 46, day=29)
        clock = _Clock(prepared_at)
        controller = DeepSeekDispatchAdmissionController(
            plan=self._plan(prepared_at, duration=600),
            admitted_at=prepared_at,
            clock=clock,
        )
        preparation_digest = controller.preparation_receipt.digest

        clock.value = prepared_at + timedelta(minutes=11)
        authorization = controller.authorize_dispatch(
            execution_envelope_ref="deepseek:late-fallback",
            input_token_upper_bound=1_000,
            maximum_output_tokens=8_192,
        )
        self.assertNotEqual(controller.receipt.digest, preparation_digest)
        self.assertEqual(controller.receipt.admitted_at, clock.value)
        self.assertEqual(
            controller.receipt.valid_until,
            clock.value + timedelta(seconds=600),
        )
        self.assertEqual(
            authorization.admission_receipt_digest,
            controller.receipt.digest,
        )
        audit = controller.public_audit()
        self.assertTrue(audit["dispatch_admission_activated"])
        self.assertEqual(
            audit["activation_mode"],
            "FIRST_DEEPSEEK_PREFLIGHT",
        )
        self.assertEqual(
            audit["preparation_admission_receipt"]["digest"],
            preparation_digest.value,
        )
        self.assertEqual(
            audit["admission_receipt"]["digest"],
            controller.receipt.digest.value,
        )

    def test_first_preflight_rechecks_pricing_freshness(self) -> None:
        prepared_at = self._at(18, 46, day=29)
        clock = _Clock(prepared_at)
        controller = DeepSeekDispatchAdmissionController(
            plan=self._plan(prepared_at, duration=600),
            admitted_at=prepared_at,
            clock=clock,
        )
        self.assertTrue(controller.preparation_receipt.allowed)

        clock.value = prepared_at + timedelta(minutes=16)
        with self.assertRaises(DomainError):
            controller.authorize_dispatch(
                execution_envelope_ref="deepseek:stale-first-fallback",
                input_token_upper_bound=1_000,
                maximum_output_tokens=8_192,
            )
        self.assertEqual(
            controller.receipt.decision,
            DeepSeekDispatchAdmissionDecision.DENIED_PRICING_CHECK,
        )
        self.assertEqual(
            controller.public_audit()["authorized_dispatch_count"],
            0,
        )

    def test_changed_or_stale_pricing_check_fails_closed(self) -> None:
        current = self._at(14, 50, day=29)
        changed = DeepSeekDispatchAdmissionController(
            plan=self._plan(
                current,
                status=DeepSeekPricingEffectiveStatus.CHANGED,
            ),
            admitted_at=current,
            clock=_Clock(current),
        )
        self.assertEqual(
            changed.receipt.decision,
            DeepSeekDispatchAdmissionDecision.DENIED_PRICING_CHANGED,
        )

        plan = self._plan(current)
        stale_check = DeepSeekOfficialPricingCheck.create(
            source=DEEPSEEK_PRICING_SOURCE,
            checked_at=current - timedelta(minutes=16),
            content_digest=Digest("sha256:" + "c" * 64),
            content_summary="stale",
            effective_status=DeepSeekPricingEffectiveStatus.NOT_YET_EFFECTIVE,
        )
        stale_plan = DeepSeekDispatchAdmissionPlan.create(
            run_type=plan.run_type,
            run_ref=plan.run_ref,
            turn_scope_digest=plan.turn_scope_digest,
            product_revision=plan.product_revision,
            source_revision=plan.source_revision,
            session_ref=plan.session_ref,
            provider_configuration_digest=plan.provider_configuration_digest,
            model_ref=plan.model_ref,
            authorization_message_digest=plan.authorization_message_digest,
            authorized_at=plan.authorized_at,
            expires_at=plan.expires_at,
            maximum_calls=plan.maximum_calls,
            maximum_input_tokens=plan.maximum_input_tokens,
            maximum_output_tokens=plan.maximum_output_tokens,
            maximum_duration_seconds=plan.maximum_duration_seconds,
            pricing_check=stale_check,
        )
        stale = DeepSeekDispatchAdmissionController(
            plan=stale_plan,
            admitted_at=current,
            clock=_Clock(current),
        )
        self.assertEqual(
            stale.receipt.decision,
            DeepSeekDispatchAdmissionDecision.DENIED_PRICING_CHECK,
        )


if __name__ == "__main__":
    unittest.main()
