from __future__ import annotations

from datetime import datetime, timedelta, timezone
import unittest

from software_world_model.application_services import (
    AllocationKey,
    AllocationState,
    CancellationOutcome,
    ResourceAllocationService,
    ResourceLimits,
    UsageCompleteness,
)
from software_world_model.cross_cutting import (
    CorrelationRef,
    DomainError,
    ErrorCode,
    IdempotencyKey,
    Revision,
    StableId,
    digest_of,
)
from software_world_model.infrastructure import (
    SqliteDatabase,
    SqliteResourceAllocationRepository,
)


class SequenceIds:
    def __init__(self) -> None:
        self._next = 1

    def new(self, kind: str) -> StableId:
        value = self._next
        self._next += 1
        return StableId(f"{kind}_{value:032x}")


class StepClock:
    def __init__(self) -> None:
        self._value = datetime(2026, 8, 6, tzinfo=timezone.utc)

    def __call__(self) -> datetime:
        value = self._value
        self._value += timedelta(microseconds=1)
        return value


class ResourceAllocationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.database = SqliteDatabase()
        self.repository = SqliteResourceAllocationRepository(
            self.database, id_generator=SequenceIds()
        )
        self.service = ResourceAllocationService(self.repository, clock=StepClock())
        self.correlation = CorrelationRef("resource-test")

    def tearDown(self) -> None:
        self.database.close()

    def reserve_root(self, *, key: str = "root-reserve"):
        return self.service.reserve_root(
            allocation_key=AllocationKey(
                owner_control_boundary="management-command-1",
                owner_attempt="attempt-1",
                dispatch_kind="ROOT",
                dispatch_attempt_key="root-1",
            ),
            reserved_limits=ResourceLimits(
                calls=10,
                tokens=1000,
                duration_ms=10000,
                result_bytes=100000,
                cost_microunits=1000,
            ),
            policy_ref="resource-policy@1",
            conversion_rule_ref="budget-conversion@1",
            operation_key=IdempotencyKey(key),
            actor="test-operator",
            reason="reserve root",
            correlation_ref=self.correlation,
        )

    def child_key(self, attempt: str) -> AllocationKey:
        return AllocationKey(
            owner_control_boundary="management-command-1",
            owner_attempt="attempt-1",
            dispatch_kind="OWNER_CALL",
            dispatch_attempt_key=attempt,
        )

    def reserve_child(
        self,
        root,
        *,
        limits: ResourceLimits,
        attempt: str,
        operation_key: str,
        expected_revision: Revision | None = None,
    ):
        return self.service.reserve_child(
            parent_allocation_id=root.allocation_id,
            expected_parent_revision=expected_revision or root.revision,
            allocation_key=self.child_key(attempt),
            reserved_limits=limits,
            policy_ref="resource-policy@1",
            conversion_rule_ref="budget-conversion@1",
            operation_key=IdempotencyKey(operation_key),
            actor="test-operator",
            reason="reserve child",
            correlation_ref=self.correlation,
        )

    def test_child_reservation_is_atomic_and_cannot_over_allocate_parent(self) -> None:
        root = self.reserve_root()
        child = self.reserve_child(
            root,
            limits=ResourceLimits(calls=6, tokens=600),
            attempt="child-1",
            operation_key="child-reserve-1",
        )
        current_root = self.service.get(root.allocation_id)
        self.assertEqual(current_root.available_limits.calls, 4)
        self.assertEqual(current_root.available_limits.tokens, 400)

        with self.assertRaises(DomainError) as exhausted:
            self.reserve_child(
                current_root,
                limits=ResourceLimits(calls=5, tokens=100),
                attempt="child-2",
                operation_key="child-reserve-2",
            )
        self.assertEqual(exhausted.exception.code, ErrorCode.BUDGET_EXHAUSTED)
        self.assertEqual(self.service.get(root.allocation_id), current_root)
        self.assertEqual(child.state, AllocationState.RESERVED)

    def test_allocation_key_replay_does_not_deduct_parent_twice(self) -> None:
        root = self.reserve_root()
        limits = ResourceLimits(calls=3, tokens=300)
        child = self.reserve_child(
            root,
            limits=limits,
            attempt="same-physical-attempt",
            operation_key="child-original",
        )
        root_after_first = self.service.get(root.allocation_id)
        replay = self.reserve_child(
            root_after_first,
            limits=limits,
            attempt="same-physical-attempt",
            operation_key="child-recovery",
        )

        self.assertEqual(replay, child)
        self.assertEqual(self.service.get(root.allocation_id), root_after_first)

        with self.assertRaises(DomainError) as conflict:
            self.reserve_child(
                root_after_first,
                limits=ResourceLimits(calls=4, tokens=300),
                attempt="same-physical-attempt",
                operation_key="child-conflict",
            )
        self.assertEqual(conflict.exception.code, ErrorCode.ALLOCATION_KEY_CONFLICT)

    def test_complete_usage_settlement_returns_only_proven_unused_balance(self) -> None:
        root = self.reserve_root()
        child = self.reserve_child(
            root,
            limits=ResourceLimits(calls=6, tokens=600),
            attempt="settle-child",
            operation_key="settle-reserve",
        )
        bound = self.service.bind_dispatch(
            allocation_id=child.allocation_id,
            expected_revision=Revision(1),
            dispatch_ref="prepared-call-1",
            dispatch_digest=digest_of({"prepared_call": 1}),
            operation_key=IdempotencyKey("bind-dispatch"),
            actor="test-operator",
            reason="bind prepared call",
            correlation_ref=self.correlation,
        )
        reported = self.service.report_usage(
            allocation_id=child.allocation_id,
            expected_revision=bound.revision,
            usage_delta=ResourceLimits(calls=4, tokens=400),
            completeness=UsageCompleteness.COMPLETE,
            operation_key=IdempotencyKey("usage-complete"),
            actor="test-operator",
            reason="provider usage",
            correlation_ref=self.correlation,
        )
        settled = self.service.settle(
            allocation_id=child.allocation_id,
            expected_revision=reported.revision,
            operation_key=IdempotencyKey("settle-complete"),
            actor="test-operator",
            reason="settle call",
            correlation_ref=self.correlation,
        )

        current_root = self.service.get(root.allocation_id)
        self.assertEqual(settled.state, AllocationState.SETTLED)
        self.assertEqual(settled.charged_usage.calls, 4)
        self.assertEqual(current_root.available_limits.calls, 6)
        self.assertEqual(current_root.available_limits.tokens, 600)
        self.assertEqual(current_root.charged_usage.calls, 4)

    def test_unknown_usage_settles_at_full_reservation(self) -> None:
        root = self.reserve_root()
        child = self.reserve_child(
            root,
            limits=ResourceLimits(calls=6, tokens=600),
            attempt="unknown-child",
            operation_key="unknown-reserve",
        )
        settled = self.service.settle(
            allocation_id=child.allocation_id,
            expected_revision=Revision(1),
            operation_key=IdempotencyKey("unknown-settle"),
            actor="test-operator",
            reason="outcome usage unknown",
            correlation_ref=self.correlation,
        )

        self.assertEqual(settled.charged_usage, child.reserved_limits)
        self.assertEqual(self.service.get(root.allocation_id).available_limits.calls, 4)

    def test_parent_container_settles_to_child_charges_without_double_counting(self) -> None:
        root = self.reserve_root()
        child = self.reserve_child(
            root,
            limits=ResourceLimits(calls=6, tokens=600),
            attempt="container-child",
            operation_key="container-reserve",
        )
        reported = self.service.report_usage(
            allocation_id=child.allocation_id,
            expected_revision=Revision(1),
            usage_delta=ResourceLimits(calls=4, tokens=400),
            completeness=UsageCompleteness.COMPLETE,
            operation_key=IdempotencyKey("container-usage"),
            actor="test-operator",
            reason="complete child usage",
            correlation_ref=self.correlation,
        )
        self.service.settle(
            allocation_id=child.allocation_id,
            expected_revision=reported.revision,
            operation_key=IdempotencyKey("container-child-settle"),
            actor="test-operator",
            reason="settle child",
            correlation_ref=self.correlation,
        )
        current_root = self.service.get(root.allocation_id)
        settled_root = self.service.settle(
            allocation_id=root.allocation_id,
            expected_revision=current_root.revision,
            operation_key=IdempotencyKey("container-root-settle"),
            actor="test-operator",
            reason="settle parent container",
            correlation_ref=self.correlation,
        )

        self.assertEqual(settled_root.state, AllocationState.SETTLED)
        self.assertEqual(settled_root.charged_usage.calls, 4)
        self.assertEqual(settled_root.charged_usage.tokens, 400)
        self.assertEqual(settled_root.usage_completeness, UsageCompleteness.COMPLETE)

    def test_bound_allocation_requires_canceled_before_dispatch_to_release(self) -> None:
        root = self.reserve_root()
        child = self.reserve_child(
            root,
            limits=ResourceLimits(calls=2, tokens=100),
            attempt="cancel-child",
            operation_key="cancel-reserve",
        )
        bound = self.service.bind_dispatch(
            allocation_id=child.allocation_id,
            expected_revision=Revision(1),
            dispatch_ref="prepared-call-cancel",
            dispatch_digest=digest_of({"prepared_call": "cancel"}),
            operation_key=IdempotencyKey("cancel-bind"),
            actor="test-operator",
            reason="bind prepared call",
            correlation_ref=self.correlation,
        )

        with self.assertRaises(DomainError) as denied:
            self.service.release(
                allocation_id=child.allocation_id,
                expected_revision=bound.revision,
                cancellation_outcome=None,
                operation_key=IdempotencyKey("release-without-proof"),
                actor="test-operator",
                reason="unsafe release",
                correlation_ref=self.correlation,
            )
        self.assertEqual(denied.exception.code, ErrorCode.ALLOCATION_STATE_CONFLICT)

        released = self.service.release(
            allocation_id=child.allocation_id,
            expected_revision=bound.revision,
            cancellation_outcome=CancellationOutcome.CANCELED_BEFORE_DISPATCH,
            operation_key=IdempotencyKey("release-with-proof"),
            actor="test-operator",
            reason="dispatch canceled",
            correlation_ref=self.correlation,
        )
        self.assertEqual(released.state, AllocationState.RELEASED)
        self.assertEqual(self.service.get(root.allocation_id).available_limits.calls, 10)

    def test_usage_overrun_marks_parent_and_blocks_future_children(self) -> None:
        root = self.reserve_root()
        child = self.reserve_child(
            root,
            limits=ResourceLimits(calls=2, tokens=100),
            attempt="overrun-child",
            operation_key="overrun-reserve",
        )
        reported = self.service.report_usage(
            allocation_id=child.allocation_id,
            expected_revision=Revision(1),
            usage_delta=ResourceLimits(calls=4, tokens=200),
            completeness=UsageCompleteness.COMPLETE,
            operation_key=IdempotencyKey("overrun-usage"),
            actor="test-operator",
            reason="provider exceeded estimate",
            correlation_ref=self.correlation,
        )
        self.service.settle(
            allocation_id=child.allocation_id,
            expected_revision=reported.revision,
            operation_key=IdempotencyKey("overrun-settle"),
            actor="test-operator",
            reason="settle overrun",
            correlation_ref=self.correlation,
        )
        current_root = self.service.get(root.allocation_id)
        self.assertTrue(current_root.overrun)
        self.assertEqual(current_root.charged_usage.calls, 4)

        with self.assertRaises(DomainError) as blocked:
            self.reserve_child(
                current_root,
                limits=ResourceLimits(calls=1),
                attempt="after-overrun",
                operation_key="after-overrun-reserve",
            )
        self.assertEqual(blocked.exception.code, ErrorCode.ALLOCATION_STATE_CONFLICT)


if __name__ == "__main__":
    unittest.main()
