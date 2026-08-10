from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import unittest

from software_world_model.cross_cutting import (
    Digest,
    DomainError,
    ErrorCode,
    IdempotencyKey,
    Revision,
    StableId,
    digest_of,
)
from software_world_model.infrastructure.sqlite_artifact_use_authority_repository import (
    SqliteArtifactUseAuthorityRepository,
)
from software_world_model.infrastructure.sqlite_database import SqliteDatabase
from software_world_model.infrastructure.sqlite_source_operation_repository import (
    SqliteSourceOperationRepository,
)
from software_world_model.knowledge_engine import (
    AssertionOutcome,
    ScopeLifecycle,
    ScopePurpose,
    ScopeStateAssertion,
    ScopeType,
)
from software_world_model.source_integration.artifact_use import (
    ArtifactReadOperationReference,
    ArtifactReadProtectionMode,
    ArtifactUseAuthorityService,
    ArtifactUsePurpose,
)
from software_world_model.source_integration.operations import (
    ConnectorOutcome,
    SourceOperationReplayService,
    SourceOperationResult,
    SourceOperationStatus,
    SourceTool,
)


@dataclass(frozen=True)
class _PersistableIntent:
    idempotency_key: IdempotencyKey
    digest: Digest
    source_id: StableId
    source_revision: Revision
    binding_id: StableId
    binding_revision: Revision
    tool: SourceTool


class _StepClock:
    def __init__(self) -> None:
        self.value = datetime(2026, 8, 10, tzinfo=timezone.utc)

    def __call__(self) -> datetime:
        value = self.value
        self.value += timedelta(microseconds=1)
        return value


class _CountingReplay:
    """The only capability given to Artifact authority; no Connector methods."""

    def __init__(self, repository: SqliteSourceOperationRepository) -> None:
        self._replay = SourceOperationReplayService(repository)
        self.calls = 0

    def replay(
        self,
        *,
        operation_id: StableId,
        expected_intent_digest: Digest,
        scope_assertion: ScopeStateAssertion,
    ) -> SourceOperationResult:
        if not isinstance(scope_assertion, ScopeStateAssertion):
            raise AssertionError("fresh Scope assertion was not supplied")
        self.calls += 1
        return self._replay.replay(
            operation_id=operation_id,
            expected_intent_digest=expected_intent_digest,
        )


class ArtifactUseAuthorityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temporary.name) / "authority.sqlite3"
        self.database = SqliteDatabase(self.database_path)
        self.operations = SqliteSourceOperationRepository(self.database)
        self.authorities = SqliteArtifactUseAuthorityRepository(self.database)
        self.clock = _StepClock()
        self.replay = _CountingReplay(self.operations)
        self.service = ArtifactUseAuthorityService(
            self.authorities,
            self.replay,
            clock=self.clock,
        )
        self.result = self._persist_read_operation()
        self.reference = ArtifactReadOperationReference.from_result(self.result)
        self.update_digest = digest_of(
            ["MAVEN_STRUCTURE_UPDATE_REQUEST@1", {"request": "fixture"}]
        )
        self.candidate_digest = digest_of(
            ["STRUCTURE_KNOWLEDGE_CANDIDATE@1", {"candidate": "fixture"}]
        )
        assertion_core = {
            "scope_id": "scope_" + "3" * 32,
            "scope_type": ScopeType.SYSTEM.value,
            "definition_revision": 1,
            "lifecycle": ScopeLifecycle.ACTIVE.value,
            "purpose": ScopePurpose.SOURCE_EXECUTION.value,
            "outcome": AssertionOutcome.ELIGIBLE.value,
            "caller_ref": "artifact-authority-test",
            "request_ref": "artifact-authority-test:read",
            "classification": "INTERNAL",
            "read_at": self.clock(),
        }
        self.scope_assertion = ScopeStateAssertion(
            assertion_id=StableId("scope_assertion_" + "4" * 32),
            scope_id=StableId(assertion_core["scope_id"]),
            scope_type=ScopeType.SYSTEM,
            definition_revision=Revision(1),
            lifecycle=ScopeLifecycle.ACTIVE,
            purpose=ScopePurpose.SOURCE_EXECUTION,
            outcome=AssertionOutcome.ELIGIBLE,
            caller_ref=assertion_core["caller_ref"],
            request_ref=assertion_core["request_ref"],
            classification=assertion_core["classification"],
            read_at=assertion_core["read_at"],
            digest=digest_of(assertion_core),
        )

    def tearDown(self) -> None:
        self.database.close()
        self.temporary.cleanup()

    def _persist_read_operation(self) -> SourceOperationResult:
        intent = _PersistableIntent(
            idempotency_key=IdempotencyKey("source-read"),
            digest=digest_of(["SOURCE_OPERATION_INTENT@1", {"fixture": 1}]),
            source_id=StableId("source_" + "1" * 32),
            source_revision=Revision(1),
            binding_id=StableId("binding_" + "2" * 32),
            binding_revision=Revision(1),
            tool=SourceTool.READ,
        )
        prepared = self.operations.prepare(
            intent=intent, occurred_at=self.clock()
        )
        dispatched = self.operations.mark_dispatched(
            operation_id=prepared.operation_id,
            expected_revision=prepared.revision,
            occurred_at=self.clock(),
        )
        payload = b"<project><artifactId>fixture</artifactId></project>\n"
        return self.operations.complete(
            operation_id=dispatched.operation_id,
            expected_revision=dispatched.revision,
            status=SourceOperationStatus.COMPLETED,
            outcome=ConnectorOutcome(
                repository_revision="a" * 40,
                subject="pom.xml",
                artifact_kind="LOCAL_GIT_FILE@1",
                payload=payload,
                item_count=1,
                total_bytes=len(payload),
                next_cursor=None,
                has_more=False,
                truncated=False,
                truncation_offset=None,
                coverage=(
                    ("path", "pom.xml"),
                    ("range", f"bytes:0-{len(payload)}"),
                    ("revision", "a" * 40),
                ),
            ),
            classification="INTERNAL",
            failure_code=None,
            failure_message=None,
            occurred_at=self.clock(),
        )

    def _persist_partial_tree_operation(self) -> SourceOperationResult:
        intent = _PersistableIntent(
            idempotency_key=IdempotencyKey("source-tree-page"),
            digest=digest_of(["SOURCE_OPERATION_INTENT@1", {"fixture": 2}]),
            source_id=StableId("source_" + "1" * 32),
            source_revision=Revision(1),
            binding_id=StableId("binding_" + "2" * 32),
            binding_revision=Revision(1),
            tool=SourceTool.TREE,
        )
        prepared = self.operations.prepare(intent=intent, occurred_at=self.clock())
        dispatched = self.operations.mark_dispatched(
            operation_id=prepared.operation_id,
            expected_revision=prepared.revision,
            occurred_at=self.clock(),
        )
        payload = b'{"mode":"100644","path":"pom.xml"}'
        return self.operations.complete(
            operation_id=dispatched.operation_id,
            expected_revision=dispatched.revision,
            status=SourceOperationStatus.PARTIAL,
            outcome=ConnectorOutcome(
                repository_revision="a" * 40,
                subject="repository-tree-entries",
                artifact_kind="LOCAL_GIT_TREE_ENTRY_LIST@1",
                payload=payload,
                item_count=1,
                total_bytes=len(payload),
                next_cursor="1",
                has_more=True,
                truncated=False,
                truncation_offset=None,
                # The Source repository persists this as a JSON object and
                # reloads its keys sorted.  Artifact authority must recover the
                # Tool-contract order used by the original identity digest.
                coverage=(
                    ("cursor_start", "0"),
                    ("cursor_end", "1"),
                    ("matched_total", "2"),
                    ("revision", "a" * 40),
                ),
            ),
            classification="INTERNAL",
            failure_code=None,
            failure_message=None,
            occurred_at=self.clock(),
        )

    def _open(self, *, key: str = "read-package", request_digest: Digest | None = None):
        return self.service.open_read_package(
            idempotency_key=IdempotencyKey(key),
            operation_references=(self.reference,),
            purpose=ArtifactUsePurpose.MAVEN_STRUCTURE_EVIDENCE_PERSISTENCE,
            downstream_request_ref="maven-update-attempt:fixture",
            downstream_request_digest=request_digest or self.update_digest,
            protection_mode=ArtifactReadProtectionMode.NO_EVICTION,
            scope_assertion=self.scope_assertion,
        )

    def _confirm(self, read, *, key: str = "confirm-use", candidate_digest: Digest | None = None):
        return self.service.confirm_persistent_use(
            idempotency_key=IdempotencyKey(key),
            package_id=read.package.package_id,
            expected_package_digest=read.package.digest,
            closure_id=read.closure.closure_id,
            expected_closure_digest=read.closure.digest,
            protection_id=read.protection.protection_id,
            expected_protection_digest=read.protection.digest,
            purpose=read.package.purpose,
            downstream_request_ref=read.package.downstream_request_ref,
            downstream_request_digest=read.package.downstream_request_digest,
            downstream_candidate_ref="maven-structure-candidate:fixture",
            downstream_candidate_digest=candidate_digest or self.candidate_digest,
            scope_assertion=self.scope_assertion,
        )

    def test_package_and_confirmation_are_exact_persisted_and_idempotent(self) -> None:
        first = self._open()
        replay = self._open()

        self.assertEqual(first.package, replay.package)
        self.assertEqual(first.closure, replay.closure)
        self.assertEqual(first.protection, replay.protection)
        self.assertEqual(first.operation_results, (self.result,))
        self.assertEqual(first.artifacts, self.result.observation.artifacts)
        self.assertEqual(
            first.protection.mode, ArtifactReadProtectionMode.NO_EVICTION
        )
        self.assertFalse(first.protection.guard_required)
        self.assertEqual(self.replay.calls, 2)

        confirmation = self._confirm(first)
        confirmation_replay = self._confirm(first)
        loaded = self.service.get_confirmation(confirmation.confirmation_id)

        self.assertEqual(confirmation, confirmation_replay)
        self.assertEqual(confirmation, loaded)
        self.assertEqual(confirmation.package_digest, first.package.digest)
        self.assertEqual(confirmation.closure_digest, first.closure.digest)
        self.assertEqual(
            confirmation.protection_digest, first.protection.digest
        )
        self.assertEqual(confirmation.downstream_request_digest, self.update_digest)
        self.assertEqual(
            confirmation.downstream_candidate_digest, self.candidate_digest
        )
        # Opening twice and confirming twice each performs a current replay.
        self.assertEqual(self.replay.calls, 4)

    def test_exact_confirmation_replays_after_repository_restart(self) -> None:
        read = self._open()
        expected = self._confirm(read)
        self.database.close()

        self.database = SqliteDatabase(self.database_path)
        self.operations = SqliteSourceOperationRepository(self.database)
        self.authorities = SqliteArtifactUseAuthorityRepository(self.database)
        self.replay = _CountingReplay(self.operations)
        self.service = ArtifactUseAuthorityService(
            self.authorities,
            self.replay,
            clock=self.clock,
        )

        replayed = self._confirm(read)
        self.assertEqual(replayed, expected)
        self.assertEqual(
            self.service.get_confirmation(expected.confirmation_id), expected
        )
        self.assertEqual(self.replay.calls, 1)

    def test_structure_proof_verification_owner_reads_without_payload_replay(self) -> None:
        confirmation = self._confirm(self._open())
        calls_before = self.replay.calls

        self.service.verify_structure_candidate_use(
            confirmation_id=confirmation.confirmation_id,
            expected_confirmation_digest=confirmation.digest,
            candidate_ref=confirmation.downstream_candidate_ref,
            candidate_digest=confirmation.downstream_candidate_digest,
        )
        self.assertEqual(self.replay.calls, calls_before)

        with self.assertRaises(DomainError) as tampered_digest:
            self.service.verify_structure_candidate_use(
                confirmation_id=confirmation.confirmation_id,
                expected_confirmation_digest=Digest("sha256:" + "f" * 64),
                candidate_ref=confirmation.downstream_candidate_ref,
                candidate_digest=confirmation.downstream_candidate_digest,
            )
        self.assertEqual(
            tampered_digest.exception.details["reason_code"],
            "ARTIFACT_USE_STRUCTURE_PROOF_MISMATCH",
        )

        with self.assertRaises(DomainError) as wrong_candidate:
            self.service.verify_structure_candidate_use(
                confirmation_id=confirmation.confirmation_id,
                expected_confirmation_digest=confirmation.digest,
                candidate_ref="maven-structure-candidate:other",
                candidate_digest=confirmation.downstream_candidate_digest,
            )
        self.assertEqual(
            wrong_candidate.exception.details["reason_code"],
            "ARTIFACT_USE_STRUCTURE_PROOF_MISMATCH",
        )
        self.assertEqual(self.replay.calls, calls_before)

    def test_confirmation_replays_current_payload_and_rejects_source_tamper(self) -> None:
        read = self._open()
        artifact_id = read.artifacts[0].artifact_id.value
        with self.database.transaction() as connection:
            connection.execute(
                "UPDATE src_artifacts SET payload = ? WHERE artifact_id = ?",
                (b"tampered", artifact_id),
            )

        with self.assertRaises(DomainError) as raised:
            self._confirm(read)

        self.assertEqual(
            raised.exception.code, ErrorCode.AUTHORITY_RECORD_INCONSISTENT
        )
        self.assertEqual(
            raised.exception.details["reason_code"],
            "SOURCE_ARTIFACT_CONTENT_OR_CONTEXT_INVALID",
        )
        with self.database.read() as connection:
            count = connection.execute(
                "SELECT COUNT(*) AS count FROM src_artifact_use_confirmations"
            ).fetchone()["count"]
        self.assertEqual(count, 0)

    def test_exact_operation_result_reference_is_required(self) -> None:
        forged = replace(
            self.reference,
            result_digest=Digest("sha256:" + "f" * 64),
        )

        with self.assertRaises(DomainError) as raised:
            self.service.open_read_package(
                idempotency_key=IdempotencyKey("forged-result"),
                operation_references=(forged,),
                purpose=ArtifactUsePurpose.MAVEN_STRUCTURE_EVIDENCE_PERSISTENCE,
                downstream_request_ref="maven-update-attempt:fixture",
                downstream_request_digest=self.update_digest,
                protection_mode=ArtifactReadProtectionMode.NO_EVICTION,
                scope_assertion=self.scope_assertion,
            )

        self.assertEqual(
            raised.exception.details["reason_code"],
            "SOURCE_OPERATION_REPLAY_RESULT_MISMATCH",
        )

    def test_bounded_partial_tree_page_is_exactly_bound_in_ordered_closure(self) -> None:
        tree = self._persist_partial_tree_operation()
        read = self.service.open_read_package(
            idempotency_key=IdempotencyKey("tree-and-pom-package"),
            operation_references=(
                ArtifactReadOperationReference.from_result(tree),
                self.reference,
            ),
            purpose=ArtifactUsePurpose.MAVEN_STRUCTURE_EVIDENCE_PERSISTENCE,
            downstream_request_ref="maven-update-attempt:tree-fixture",
            downstream_request_digest=self.update_digest,
            protection_mode=ArtifactReadProtectionMode.NO_EVICTION,
            scope_assertion=self.scope_assertion,
        )

        self.assertEqual(
            tuple(item.operation_id for item in read.closure.operations),
            (tree.operation_id, self.result.operation_id),
        )
        self.assertEqual(
            read.closure.operations[0].status, SourceOperationStatus.PARTIAL
        )
        self.assertTrue(read.operation_results[0].observation.has_more)

    def test_package_idempotency_key_cannot_change_exact_closure_or_request(self) -> None:
        self._open()

        with self.assertRaises(DomainError) as raised:
            self._open(
                request_digest=Digest("sha256:" + "e" * 64),
            )

        self.assertEqual(raised.exception.code, ErrorCode.IDEMPOTENCY_MISMATCH)
        self.assertEqual(
            raised.exception.details["reason_code"],
            "ARTIFACT_READ_PACKAGE_IDEMPOTENCY_MISMATCH",
        )

    def test_confirmation_is_single_use_and_candidate_bound(self) -> None:
        read = self._open()
        first = self._confirm(read)

        with self.assertRaises(DomainError) as changed_candidate:
            self._confirm(
                read,
                candidate_digest=Digest("sha256:" + "d" * 64),
            )
        self.assertEqual(
            changed_candidate.exception.code, ErrorCode.IDEMPOTENCY_MISMATCH
        )

        with self.assertRaises(DomainError) as second_key:
            self._confirm(read, key="another-confirmation-key")
        self.assertEqual(second_key.exception.code, ErrorCode.IDEMPOTENCY_MISMATCH)
        self.assertEqual(
            second_key.exception.details["reason_code"],
            "ARTIFACT_USE_ALREADY_CONFIRMED",
        )
        another_package = self._open(key="another-read-package")
        with self.assertRaises(DomainError) as another_package_use:
            self._confirm(
                another_package,
                key="another-package-confirmation",
            )
        self.assertEqual(
            another_package_use.exception.details["reason_code"],
            "ARTIFACT_USE_ALREADY_CONFIRMED",
        )
        self.assertEqual(
            self.service.get_confirmation(first.confirmation_id), first
        )

    def test_reopen_issues_current_package_bounded_replay_capability(self) -> None:
        read = self._open()
        reopened = self.service.reopen_authorized_read(
            package_id=read.package.package_id,
            expected_package_digest=read.package.digest,
            closure_id=read.closure.closure_id,
            expected_closure_digest=read.closure.digest,
            protection_id=read.protection.protection_id,
            expected_protection_digest=read.protection.digest,
            purpose=read.package.purpose,
            downstream_request_ref=read.package.downstream_request_ref,
            downstream_request_digest=read.package.downstream_request_digest,
            scope_assertion=self.scope_assertion,
        )

        self.assertEqual(reopened, read)
        self.assertEqual(
            reopened.replay(
                operation_id=self.result.operation_id,
                expected_intent_digest=self.result.intent_digest,
            ),
            self.result,
        )
        with self.assertRaises(DomainError) as outside:
            reopened.replay(
                operation_id=StableId("operation_" + "9" * 32),
                expected_intent_digest=self.result.intent_digest,
            )
        self.assertEqual(outside.exception.code, ErrorCode.CONTROL_STATE_DENIED)

    def test_reopen_authenticates_protection_before_payload_replay(self) -> None:
        read = self._open()
        calls_before = self.replay.calls

        with self.assertRaises(DomainError) as raised:
            self.service.reopen_authorized_read(
                package_id=read.package.package_id,
                expected_package_digest=read.package.digest,
                closure_id=read.closure.closure_id,
                expected_closure_digest=read.closure.digest,
                protection_id=read.protection.protection_id,
                expected_protection_digest=Digest("sha256:" + "f" * 64),
                purpose=read.package.purpose,
                downstream_request_ref=read.package.downstream_request_ref,
                downstream_request_digest=read.package.downstream_request_digest,
                scope_assertion=self.scope_assertion,
            )

        self.assertEqual(
            raised.exception.details["reason_code"],
            "ARTIFACT_READ_REOPEN_AUTHORITY_MISMATCH",
        )
        self.assertEqual(self.replay.calls, calls_before)

    def test_persisted_package_tamper_is_detected_before_confirmation(self) -> None:
        read = self._open()
        with self.database.transaction() as connection:
            connection.execute(
                """UPDATE src_artifact_read_packages
                   SET downstream_request_ref = ?
                   WHERE package_id = ?""",
                ("maven-update-attempt:forged", read.package.package_id.value),
            )

        with self.assertRaises(DomainError) as raised:
            self._confirm(read)

        self.assertEqual(
            raised.exception.details["reason_code"],
            "ARTIFACT_READ_AUTHORITY_DIGEST_INVALID",
        )

    def test_persisted_confirmation_tamper_is_detected_on_audit_read(self) -> None:
        confirmation = self._confirm(self._open())
        with self.database.transaction() as connection:
            connection.execute(
                """UPDATE src_artifact_use_confirmations
                   SET downstream_candidate_ref = ?
                   WHERE confirmation_id = ?""",
                ("maven-structure-candidate:forged", confirmation.confirmation_id.value),
            )

        with self.assertRaises(DomainError) as raised:
            self.service.get_confirmation(confirmation.confirmation_id)

        self.assertEqual(
            raised.exception.details["reason_code"],
            "ARTIFACT_USE_CONFIRMATION_DIGEST_INVALID",
        )


if __name__ == "__main__":
    unittest.main()
