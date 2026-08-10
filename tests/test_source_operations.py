from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import subprocess
import tempfile
import unittest

from software_world_model.cross_cutting import (
    CorrelationRef,
    DomainError,
    ErrorCode,
    IdempotencyKey,
    Revision,
)
from software_world_model.infrastructure import (
    SqliteDatabase,
    SqliteKnowledgeScopeRepository,
    SqliteSourceConfigurationRepository,
    SqliteSourceOperationRepository,
)
from software_world_model.knowledge_engine import KnowledgeScopeService, ScopePurpose, ScopeType
from software_world_model.source_integration import (
    LocalGitConfigurationProvider,
    LocalGitConnector,
    LocalGitTargetResolver,
    OperationBudget,
    ProviderRegistry,
    ResolutionOutcome,
    SourceConfigurationService,
    SourceOperationIntent,
    SourceOperationService,
    SourceOperationStatus,
    SourceTool,
)


class StepClock:
    def __init__(self) -> None:
        self.value = datetime(2026, 8, 6, tzinfo=timezone.utc)

    def __call__(self) -> datetime:
        current = self.value
        self.value += timedelta(microseconds=1)
        return current


class SourceOperationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.repo_path = Path(self.temporary.name) / "repository"
        self.repo_path.mkdir()
        self._git("init", "-q")
        self._git("config", "user.email", "test@example.com")
        self._git("config", "user.name", "Test")
        (self.repo_path / "src").mkdir()
        (self.repo_path / "docs").mkdir()
        (self.repo_path / "src" / "OrderService.java").write_text(
            """package com.example;
public class OrderService {
  public String find(String id) { return id; }
  public String find(long id) { return Long.toString(id); }
}
""",
            encoding="utf-8",
        )
        (self.repo_path / "src" / "notes.txt").write_text(
            "alpha\nneedle one\nbeta\nneedle two\nomega\n", encoding="utf-8"
        )
        (self.repo_path / "docs" / "secret.txt").write_text("outside selector\n", encoding="utf-8")
        self._git("add", ".")
        self._git("commit", "-q", "-m", "initial")
        self.commit = self._git("rev-parse", "HEAD").strip()

        self.database = SqliteDatabase()
        self.clock = StepClock()
        self.scopes = KnowledgeScopeService(
            SqliteKnowledgeScopeRepository(self.database), clock=self.clock
        )
        self.sources = SourceConfigurationService(
            SqliteSourceConfigurationRepository(self.database),
            ProviderRegistry((LocalGitConfigurationProvider(),)),
            self.scopes,
            clock=self.clock,
        )
        scope = self.scopes.create_scope(
            scope_type=ScopeType.SYSTEM,
            metadata={"display_name": "Fixture"},
            idempotency_key=IdempotencyKey("scope"),
            actor="test",
            reason="source operation",
            correlation_ref=CorrelationRef("source-operation"),
        )
        source = self.sources.register_data_source(
            provider_type="LOCAL_GIT",
            provider_contract_version="0.1.0",
            identity_domain="LOCAL",
            source_target=str(self.repo_path),
            provider_configuration={"read_mode": "read_only"},
            secret_reference=None,
            idempotency_key=IdempotencyKey("source"),
            actor="test",
            reason="source operation",
            correlation_ref=CorrelationRef("source-operation"),
        )
        bind_assertion = self.scopes.read_scope_state_assertion(
            scope_id=scope.scope_id,
            expected_revision=Revision(1),
            purpose=ScopePurpose.BIND_CONFIGURATION,
            caller_ref="test",
            request_ref="bind",
            classification="INTERNAL",
        )
        binding = self.sources.bind_source_to_scope(
            source_id=source.source_id,
            assertion=bind_assertion,
            selector={"paths": "src"},
            context_constraint={"revision_policy": "exact"},
            context_hint="fixture",
            idempotency_key=IdempotencyKey("binding"),
            actor="test",
            reason="source operation",
            correlation_ref=CorrelationRef("source-operation"),
        )
        self.scope = scope
        self.source = source
        self.binding = binding
        self.operation_repository = SqliteSourceOperationRepository(self.database)
        self.operations = SourceOperationService(
            self.operation_repository, self.sources, clock=self.clock
        )

    def tearDown(self) -> None:
        self.database.close()
        self.temporary.cleanup()

    def _git(self, *arguments: str) -> str:
        result = subprocess.run(
            ("git", "-C", str(self.repo_path), *arguments),
            check=True,
            stdout=subprocess.PIPE,
            text=True,
        )
        return result.stdout

    def intent(
        self,
        tool: SourceTool,
        parameters: dict[str, str],
        *,
        key: str,
        budget: OperationBudget | None = None,
    ) -> SourceOperationIntent:
        assertion = self.scopes.read_scope_state_assertion(
            scope_id=self.scope.scope_id,
            expected_revision=Revision(1),
            purpose=ScopePurpose.SOURCE_EXECUTION,
            caller_ref="application-services",
            request_ref=key,
            classification="INTERNAL",
        )
        eligibility = self.sources.resolve_binding_for_execution(
            binding_id=self.binding.binding_id,
            expected_binding_revision=Revision(1),
            expected_source_revision=Revision(1),
            assertion=assertion,
            tool_id=tool.value,
            classification="INTERNAL",
        )
        return SourceOperationIntent.create(
            idempotency_key=IdempotencyKey(key),
            causation_reference=f"test:{key}",
            source_id=self.source.source_id,
            source_revision=Revision(1),
            binding_id=self.binding.binding_id,
            binding_revision=Revision(1),
            scope_assertion=assertion,
            binding_eligibility=eligibility,
            tool=tool,
            parameters=parameters,
            budget=budget or OperationBudget(max_calls=1, max_items=100, max_bytes=4096),
            classification="INTERNAL",
            correlation_ref=CorrelationRef("source-operation"),
        )

    def test_exact_commit_path_and_language_neutral_symbol_resolution_fail_closed(self) -> None:
        resolver = LocalGitTargetResolver(LocalGitConnector(str(self.repo_path)))

        short = resolver.resolve_revision(self.commit[:8])
        exact = resolver.resolve_revision(self.commit)
        outside = resolver.resolve_path(
            self.commit, "docs/secret.txt", allowed_paths=("src",)
        )
        ambiguous = resolver.resolve_symbol(
            self.commit,
            "needle",
            allowed_paths=("src",),
        )
        symbol = resolver.resolve_symbol(
            self.commit,
            "needle one",
            allowed_paths=("src",),
        )
        compatibility = resolver.resolve_java_symbol(
            self.commit, "needle one", allowed_paths=("src",)
        )

        self.assertEqual(short.outcome, ResolutionOutcome.AMBIGUOUS)
        self.assertEqual(exact.outcome, ResolutionOutcome.EXACT)
        self.assertEqual(outside.outcome, ResolutionOutcome.OUT_OF_SCOPE)
        self.assertEqual(ambiguous.outcome, ResolutionOutcome.AMBIGUOUS)
        self.assertEqual(symbol.outcome, ResolutionOutcome.EXACT)
        self.assertEqual(dict(symbol.canonical_identity)["path"], "src/notes.txt")
        self.assertEqual(compatibility.outcome, ResolutionOutcome.EXACT)
        self.assertEqual(
            dict(compatibility.canonical_identity)["path"], "src/notes.txt"
        )

    def test_list_pagination_records_partial_coverage_and_cursor(self) -> None:
        first = self.operations.execute(
            self.intent(
                SourceTool.LIST,
                {"revision": self.commit, "page_size": "1", "cursor": "0"},
                key="list-page-1",
                budget=OperationBudget(max_calls=1, max_items=1, max_bytes=1024),
            )
        )
        second = self.operations.execute(
            self.intent(
                SourceTool.LIST,
                {
                    "revision": self.commit,
                    "page_size": "1",
                    "cursor": first.observation.next_cursor,
                },
                key="list-page-2",
                budget=OperationBudget(max_calls=1, max_items=1, max_bytes=1024),
            )
        )

        self.assertEqual(first.status, SourceOperationStatus.PARTIAL)
        self.assertTrue(first.observation.has_more)
        self.assertEqual(first.observation.item_count, 1)
        self.assertEqual(second.status, SourceOperationStatus.COMPLETED)
        self.assertFalse(second.observation.has_more)

    def test_bounded_read_records_truncation_and_idempotent_artifact(self) -> None:
        intent = self.intent(
            SourceTool.READ,
            {"revision": self.commit, "path": "src/notes.txt", "max_bytes": "12"},
            key="read-notes",
            budget=OperationBudget(max_calls=1, max_items=1, max_bytes=12),
        )
        first = self.operations.execute(intent)
        replay = self.operations.execute(intent)

        self.assertEqual(first.status, SourceOperationStatus.PARTIAL)
        artifact = first.observation.artifacts[0]
        self.assertTrue(artifact.truncated)
        self.assertEqual(len(artifact.payload), 12)
        self.assertEqual(replay.operation_id, first.operation_id)
        self.assertEqual(replay.digest, first.digest)
        self.assertEqual(replay.observation.artifacts[0].artifact_id, artifact.artifact_id)

    def test_continued_read_has_distinct_coverage_bound_artifact_identity(self) -> None:
        first = self.operations.execute(
            self.intent(
                SourceTool.READ,
                {
                    "revision": self.commit,
                    "path": "src/notes.txt",
                    "offset": "0",
                    "max_bytes": "12",
                },
                key="read-notes-first-range",
                budget=OperationBudget(max_calls=1, max_items=1, max_bytes=12),
            )
        )
        second = self.operations.execute(
            self.intent(
                SourceTool.READ,
                {
                    "revision": self.commit,
                    "path": "src/notes.txt",
                    "offset": first.observation.next_cursor,
                    "max_bytes": "12",
                },
                key="read-notes-second-range",
                budget=OperationBudget(max_calls=1, max_items=1, max_bytes=12),
            )
        )

        first_artifact = first.observation.artifacts[0]
        second_artifact = second.observation.artifacts[0]
        self.assertNotEqual(first_artifact.artifact_id, second_artifact.artifact_id)
        self.assertNotEqual(first_artifact.identity_digest, second_artifact.identity_digest)
        self.assertEqual(
            dict(first.observation.coverage)["range"], "bytes:0-12"
        )
        self.assertEqual(
            dict(second.observation.coverage)["range"], "bytes:12-24"
        )

    def test_search_and_compare_are_selector_bounded(self) -> None:
        search = self.operations.execute(
            self.intent(
                SourceTool.SEARCH,
                {"revision": self.commit, "query": "needle"},
                key="search",
            )
        )
        (self.repo_path / "src" / "notes.txt").write_text("changed\n", encoding="utf-8")
        self._git("add", ".")
        self._git("commit", "-q", "-m", "change")
        target = self._git("rev-parse", "HEAD").strip()
        compare = self.operations.execute(
            self.intent(
                SourceTool.COMPARE,
                {"base": self.commit, "revision": target},
                key="compare",
            )
        )

        self.assertEqual(search.status, SourceOperationStatus.COMPLETED)
        search_text = search.observation.artifacts[0].payload.decode("utf-8")
        self.assertIn("src/notes.txt:2:needle one", search_text)
        self.assertNotIn("docs/secret.txt", search_text)
        self.assertEqual(compare.status, SourceOperationStatus.COMPLETED)
        self.assertIn(b"src/notes.txt", compare.observation.artifacts[0].payload)

    def test_text_discovery_and_symbol_resolution_are_extension_neutral(self) -> None:
        (self.repo_path / "src" / "worker.py").write_text(
            "def cross_language_python_marker():\n    return 1\n",
            encoding="utf-8",
        )
        (self.repo_path / "src" / "panel.ts").write_text(
            "export const cross_language_typescript_marker = 1;\n",
            encoding="utf-8",
        )
        self._git("add", ".")
        self._git("commit", "-q", "-m", "add cross-language fixtures")
        revision = self._git("rev-parse", "HEAD").strip()
        connector = LocalGitConnector(str(self.repo_path))
        resolver = LocalGitTargetResolver(connector)

        for marker, expected_path in (
            ("cross_language_python_marker", "src/worker.py"),
            ("cross_language_typescript_marker", "src/panel.ts"),
        ):
            outcome = connector.execute(
                tool=SourceTool.SEARCH,
                parameters={"revision": revision, "query": marker},
                allowed_paths=("src",),
                budget=OperationBudget(
                    max_calls=1, max_items=20, max_bytes=4096
                ),
            )
            symbol = resolver.resolve_symbol(
                revision, marker, allowed_paths=("src",)
            )

            self.assertIn(expected_path.encode("utf-8"), outcome.payload)
            self.assertEqual(symbol.outcome, ResolutionOutcome.EXACT)
            self.assertEqual(
                dict(symbol.canonical_identity)["path"], expected_path
            )

    def test_out_of_scope_read_fails_without_artifact(self) -> None:
        result = self.operations.execute(
            self.intent(
                SourceTool.READ,
                {"revision": self.commit, "path": "docs/secret.txt"},
                key="read-outside",
            )
        )
        self.assertEqual(result.status, SourceOperationStatus.FAILED)
        self.assertEqual(result.failure_code, ErrorCode.SOURCE_TARGET_OUT_OF_SCOPE.value)
        self.assertIsNone(result.observation)

    def test_control_fence_change_invalidates_prepared_eligibility(self) -> None:
        intent = self.intent(
            SourceTool.READ,
            {"revision": self.commit, "path": "src/notes.txt"},
            key="stale-eligibility",
        )
        self.sources.disable_data_source(
            source_id=self.source.source_id,
            expected_revision=Revision(1),
            idempotency_key=IdempotencyKey("disable"),
            actor="test",
            reason="revoke",
            correlation_ref=CorrelationRef("source-operation"),
        )

        result = self.operations.execute(intent)
        self.assertEqual(result.status, SourceOperationStatus.FAILED)
        self.assertEqual(result.failure_code, "ELIGIBILITY_STALE")

    def test_source_operation_idempotency_key_cannot_change_query(self) -> None:
        self.operations.execute(
            self.intent(
                SourceTool.SEARCH,
                {"revision": self.commit, "query": "needle"},
                key="same-key",
            )
        )
        with self.assertRaises(DomainError) as raised:
            self.operations.execute(
                self.intent(
                    SourceTool.SEARCH,
                    {"revision": self.commit, "query": "alpha"},
                    key="same-key",
                )
            )
        self.assertEqual(raised.exception.code, ErrorCode.IDEMPOTENCY_MISMATCH)

    def test_source_operation_retry_reuses_equivalent_eligibility(self) -> None:
        first_intent = self.intent(
            SourceTool.READ,
            {"revision": self.commit, "path": "src/notes.txt"},
            key="recoverable-read",
        )
        first = self.operations.execute(first_intent)
        replay_intent = self.intent(
            SourceTool.READ,
            {"revision": self.commit, "path": "src/notes.txt"},
            key="recoverable-read",
        )

        replay = self.operations.execute(replay_intent)

        self.assertEqual(replay, first)
        self.assertEqual(replay_intent.digest, first_intent.digest)
        self.assertEqual(
            replay_intent.binding_eligibility.digest,
            first_intent.binding_eligibility.digest,
        )
        self.assertNotEqual(
            replay_intent.binding_eligibility.resolved_at,
            first_intent.binding_eligibility.resolved_at,
        )


if __name__ == "__main__":
    unittest.main()
