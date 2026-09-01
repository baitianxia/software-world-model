from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from software_world_model.cross_cutting import (
    CorrelationRef,
    Digest,
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
from software_world_model.knowledge_engine import (
    AssertionOutcome,
    KnowledgeScopeService,
    ScopePurpose,
    ScopeType,
)
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
    TargetKind,
    resolve_local_git_binding_target,
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
            expected_binding_revision=self.binding.definition_revision,
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
            binding_revision=self.binding.definition_revision,
            scope_assertion=assertion,
            binding_eligibility=eligibility,
            tool=tool,
            parameters=parameters,
            budget=budget or OperationBudget(max_calls=1, max_items=100, max_bytes=4096),
            classification="INTERNAL",
            correlation_ref=CorrelationRef("source-operation"),
        )

    def revise_selector(self, selector: dict[str, str], *, key: str) -> None:
        assertion = self.scopes.read_scope_state_assertion(
            scope_id=self.scope.scope_id,
            expected_revision=self.scope.definition_revision,
            purpose=ScopePurpose.BIND_CONFIGURATION,
            caller_ref="test",
            request_ref=key,
            classification="INTERNAL",
        )
        self.binding = self.sources.revise_binding(
            binding_id=self.binding.binding_id,
            expected_revision=self.binding.definition_revision,
            assertion=assertion,
            selector=selector,
            context_constraint={"revision_policy": "exact"},
            context_hint="fixture",
            idempotency_key=IdempotencyKey(key),
            actor="test",
            reason="pin source selector",
            correlation_ref=CorrelationRef("source-operation"),
        )

    def artifact_read_assertion(self, *, key: str, revision: Revision):
        return self.scopes.read_scope_state_assertion(
            scope_id=self.scope.scope_id,
            expected_revision=revision,
            purpose=ScopePurpose.SOURCE_EXECUTION,
            caller_ref="artifact-use-authority",
            request_ref=key,
            classification="INTERNAL",
        )

    def test_artifact_replay_requires_current_active_binding(self) -> None:
        result = self.operations.execute(
            self.intent(
                SourceTool.READ,
                {"revision": self.commit, "path": "src/notes.txt"},
                key="artifact-replay-before-suspend",
            )
        )
        replay = self.operations.current_authorized_replay_port()
        assertion = self.artifact_read_assertion(
            key="artifact-replay-authorized",
            revision=self.scope.definition_revision,
        )
        self.assertEqual(
            replay.replay(
                operation_id=result.operation_id,
                expected_intent_digest=result.intent_digest,
                scope_assertion=assertion,
            ),
            result,
        )

        self.binding = self.sources.suspend_binding(
            binding_id=self.binding.binding_id,
            expected_revision=self.binding.definition_revision,
            idempotency_key=IdempotencyKey("suspend-artifact-binding"),
            actor="test",
            reason="prove current Artifact read fence",
            correlation_ref=CorrelationRef("source-operation"),
        )
        with self.assertRaises(DomainError) as denied:
            replay.replay(
                operation_id=result.operation_id,
                expected_intent_digest=result.intent_digest,
                scope_assertion=self.artifact_read_assertion(
                    key="artifact-replay-after-suspend",
                    revision=self.scope.definition_revision,
                ),
            )
        self.assertIn(
            denied.exception.code,
            {ErrorCode.REVISION_CONFLICT, ErrorCode.CONTROL_STATE_DENIED},
        )

    def test_artifact_replay_rejects_retired_scope_assertion(self) -> None:
        result = self.operations.execute(
            self.intent(
                SourceTool.READ,
                {"revision": self.commit, "path": "src/notes.txt"},
                key="artifact-replay-before-retire",
            )
        )
        retired = self.scopes.retire_scope(
            scope_id=self.scope.scope_id,
            expected_revision=self.scope.definition_revision,
            idempotency_key=IdempotencyKey("retire-artifact-scope"),
            actor="test",
            reason="prove current Artifact Scope fence",
            correlation_ref=CorrelationRef("source-operation"),
        )
        assertion = self.artifact_read_assertion(
            key="artifact-replay-after-retire",
            revision=retired.definition_revision,
        )
        self.assertEqual(assertion.outcome, AssertionOutcome.INELIGIBLE)

        with self.assertRaises(DomainError) as denied:
            self.operations.current_authorized_replay_port().replay(
                operation_id=result.operation_id,
                expected_intent_digest=result.intent_digest,
                scope_assertion=assertion,
            )
        self.assertEqual(denied.exception.code, ErrorCode.SCOPE_ASSERTION_INVALID)

    def test_local_git_selector_requires_exact_unambiguous_revision_bounds(self) -> None:
        provider = LocalGitConfigurationProvider()
        uppercase = self.commit.upper()
        normalized = provider.normalize_selection(
            selector={"paths": "src", "commit": uppercase},
            context_constraint={},
        )
        self.assertEqual(dict(normalized.selector)["commit"], self.commit)

        invalid = (
            {"paths": "src", "commit": self.commit[:12]},
            {"paths": "src", "comparison_base": self.commit},
            {"paths": "src", "comparison_head": self.commit},
            {
                "paths": "src",
                "commit": self.commit,
                "comparison_base": self.commit,
                "comparison_head": self.commit,
            },
        )
        for selector in invalid:
            with self.subTest(selector=selector), self.assertRaises(DomainError) as raised:
                provider.normalize_selection(selector=selector, context_constraint={})
            self.assertEqual(raised.exception.code, ErrorCode.SELECTOR_INVALID)

    def test_commit_pinned_binding_rejects_a_different_exact_revision(self) -> None:
        self.revise_selector(
            {"paths": "src", "commit": self.commit}, key="pin-initial-commit"
        )
        accepted = self.operations.execute(
            self.intent(
                SourceTool.LIST,
                {"revision": self.commit},
                key="pinned-commit-accepted",
            )
        )
        (self.repo_path / "src" / "notes.txt").write_text(
            "different revision\n", encoding="utf-8"
        )
        self._git("add", ".")
        self._git("commit", "-q", "-m", "different revision")
        different = self._git("rev-parse", "HEAD").strip()
        rejected = self.operations.execute(
            self.intent(
                SourceTool.LIST,
                {"revision": different},
                key="pinned-commit-rejected",
            )
        )

        self.assertEqual(accepted.status, SourceOperationStatus.COMPLETED)
        self.assertEqual(rejected.status, SourceOperationStatus.FAILED)
        self.assertEqual(
            rejected.failure_code, ErrorCode.SOURCE_TARGET_OUT_OF_SCOPE.value
        )
        self.assertIsNone(rejected.observation)

    def test_binding_aware_target_resolution_rejects_out_of_scope_revisions(self) -> None:
        (self.repo_path / "src" / "notes.txt").write_text(
            "target revision\n", encoding="utf-8"
        )
        self._git("add", ".")
        self._git("commit", "-q", "-m", "target revision")
        target = self._git("rev-parse", "HEAD").strip()
        connector = LocalGitConnector(str(self.repo_path))

        with self.assertRaises(DomainError) as commit_failure:
            resolve_local_git_binding_target(
                connector=connector,
                selector=(("commit", self.commit), ("paths", "src")),
                target_kind=TargetKind.REPOSITORY_REVISION,
                parameters={"revision": target},
            )
        self.assertEqual(
            commit_failure.exception.code,
            ErrorCode.SOURCE_TARGET_OUT_OF_SCOPE,
        )

        self.assertEqual(
            connector.resolve_tree(self.commit),
            self._git("rev-parse", f"{self.commit}^{{tree}}").strip(),
        )

        selector = (
            ("comparison_base", self.commit),
            ("comparison_head", target),
            ("paths", "src"),
        )
        accepted = resolve_local_git_binding_target(
            connector=connector,
            selector=selector,
            target_kind=TargetKind.REVISION_COMPARISON,
            parameters={"base": self.commit, "target": target},
        )
        self.assertEqual(accepted.outcome, ResolutionOutcome.EXACT)
        with self.assertRaises(DomainError) as comparison_failure:
            resolve_local_git_binding_target(
                connector=connector,
                selector=selector,
                target_kind=TargetKind.REVISION_COMPARISON,
                parameters={"base": target, "target": self.commit},
            )
        self.assertEqual(
            comparison_failure.exception.code,
            ErrorCode.SOURCE_TARGET_OUT_OF_SCOPE,
        )

        with patch.object(
            LocalGitConnector,
            "read_path",
            autospec=True,
            side_effect=AssertionError("out-of-scope path content was read"),
        ) as read_path:
            with self.assertRaises(DomainError) as path_failure:
                resolve_local_git_binding_target(
                    connector=connector,
                    selector=(("commit", self.commit), ("paths", "src")),
                    target_kind=TargetKind.SOURCE_PATH,
                    parameters={
                        "revision": target,
                        "path": "src/missing.txt",
                    },
                )
        self.assertEqual(
            path_failure.exception.code,
            ErrorCode.SOURCE_TARGET_OUT_OF_SCOPE,
        )
        read_path.assert_not_called()

        with patch.object(
            LocalGitConnector,
            "list_paths",
            autospec=True,
            side_effect=AssertionError("out-of-scope symbol tree was scanned"),
        ) as list_paths:
            with self.assertRaises(DomainError) as symbol_failure:
                resolve_local_git_binding_target(
                    connector=connector,
                    selector=(("commit", self.commit), ("paths", "src")),
                    target_kind=TargetKind.SYMBOL,
                    parameters={"revision": target, "symbol": "never-read"},
                )
        self.assertEqual(
            symbol_failure.exception.code,
            ErrorCode.SOURCE_TARGET_OUT_OF_SCOPE,
        )
        list_paths.assert_not_called()

    def test_comparison_pinned_binding_enforces_both_exact_endpoints(self) -> None:
        (self.repo_path / "src" / "notes.txt").write_text(
            "comparison target\n", encoding="utf-8"
        )
        self._git("add", ".")
        self._git("commit", "-q", "-m", "comparison target")
        target = self._git("rev-parse", "HEAD").strip()
        self.revise_selector(
            {
                "paths": "src",
                "comparison_base": self.commit,
                "comparison_head": target,
            },
            key="pin-comparison",
        )

        accepted = self.operations.execute(
            self.intent(
                SourceTool.COMPARE,
                {"base": self.commit, "revision": target},
                key="pinned-comparison-accepted",
            )
        )
        rejected = self.operations.execute(
            self.intent(
                SourceTool.COMPARE,
                {"base": target, "revision": self.commit},
                key="pinned-comparison-rejected",
            )
        )

        self.assertEqual(accepted.status, SourceOperationStatus.COMPLETED)
        self.assertEqual(rejected.status, SourceOperationStatus.FAILED)
        self.assertEqual(
            rejected.failure_code, ErrorCode.SOURCE_TARGET_OUT_OF_SCOPE.value
        )

    def test_commit_fence_freezes_symbolic_revision_before_ref_moves(self) -> None:
        self._git("branch", "moving", self.commit)
        (self.repo_path / "src" / "notes.txt").write_text(
            "content from later commit\n", encoding="utf-8"
        )
        self._git("add", ".")
        self._git("commit", "-q", "-m", "later commit")
        later = self._git("rev-parse", "HEAD").strip()
        self.revise_selector(
            {"paths": "src", "commit": self.commit}, key="pin-moving-ref"
        )
        original_resolve = LocalGitConnector.resolve_revision

        def resolve_then_move(
            connector: LocalGitConnector, proposal: str
        ) -> str:
            exact = original_resolve(connector, proposal)
            if proposal == "moving":
                self._git("update-ref", "refs/heads/moving", later)
            return exact

        with patch.object(
            LocalGitConnector,
            "resolve_revision",
            autospec=True,
            side_effect=resolve_then_move,
        ):
            result = self.operations.execute(
                self.intent(
                    SourceTool.READ,
                    {"revision": "moving", "path": "src/notes.txt"},
                    key="moving-ref-read",
                )
            )

        self.assertEqual(result.status, SourceOperationStatus.COMPLETED)
        self.assertEqual(
            result.observation.source_context.repository_revision, self.commit
        )
        self.assertIn(b"needle one", result.observation.artifacts[0].payload)
        self.assertNotIn(
            b"content from later commit", result.observation.artifacts[0].payload
        )
        self.assertEqual(
            self._git("rev-parse", "refs/heads/moving").strip(), later
        )

    def test_intent_classification_must_match_eligibility(self) -> None:
        intent = self.intent(
            SourceTool.READ,
            {"revision": self.commit, "path": "src/notes.txt"},
            key="classification-mismatch",
        )

        result = self.operations.execute(
            replace(intent, classification="PUBLIC")
        )

        self.assertEqual(result.status, SourceOperationStatus.FAILED)
        self.assertEqual(result.failure_code, "ELIGIBILITY_MISMATCH")
        self.assertIsNone(result.observation)

    def test_tampered_eligibility_digest_fails_revalidation(self) -> None:
        intent = self.intent(
            SourceTool.READ,
            {"revision": self.commit, "path": "src/notes.txt"},
            key="eligibility-digest-tamper",
        )
        tampered = replace(
            intent.binding_eligibility,
            digest=Digest("sha256:" + "0" * 64),
        )

        result = self.operations.execute(
            replace(intent, binding_eligibility=tampered)
        )

        self.assertEqual(result.status, SourceOperationStatus.FAILED)
        self.assertEqual(result.failure_code, "ELIGIBILITY_STALE")
        self.assertIsNone(result.observation)

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
        self.assertEqual(
            first.observation.artifacts[0].artifact_kind,
            "LOCAL_GIT_PATH_LIST@1",
        )
        self.assertFalse(first.observation.artifacts[0].payload.startswith(b"{"))
        self.assertEqual(second.status, SourceOperationStatus.COMPLETED)
        self.assertFalse(second.observation.has_more)

    def test_tree_entry_artifact_preserves_file_and_symlink_git_metadata(self) -> None:
        (self.repo_path / "src" / "notes-link.txt").symlink_to("notes.txt")
        self._git("add", ".")
        self._git("commit", "-q", "-m", "add symlink")
        revision = self._git("rev-parse", "HEAD").strip()

        result = self.operations.execute(
            self.intent(
                SourceTool.TREE,
                {"revision": revision},
                key="tree-entries",
                budget=OperationBudget(max_calls=1, max_items=100, max_bytes=8192),
            )
        )

        self.assertEqual(result.status, SourceOperationStatus.COMPLETED)
        self.assertEqual(
            result.observation.artifacts[0].artifact_kind,
            "LOCAL_GIT_TREE_ENTRY_LIST@1",
        )
        entries = {
            entry["path"]: entry
            for entry in (
                json.loads(line)
                for line in result.observation.artifacts[0].payload.splitlines()
            )
        }
        self.assertNotIn("docs/secret.txt", entries)
        regular = entries["src/notes.txt"]
        self.assertEqual(regular["mode"], "100644")
        self.assertEqual(regular["type"], "blob")
        self.assertFalse(regular["is_symlink"])
        self.assertEqual(
            regular["object_id"],
            self._git("rev-parse", f"{revision}:src/notes.txt").strip(),
        )
        symlink = entries["src/notes-link.txt"]
        self.assertEqual(symlink["mode"], "120000")
        self.assertEqual(symlink["type"], "blob")
        self.assertTrue(symlink["is_symlink"])
        self.assertEqual(
            symlink["object_id"],
            self._git("rev-parse", f"{revision}:src/notes-link.txt").strip(),
        )
        self.assertEqual(result.observation.source_context.repository_revision, revision)
        self.assertEqual(dict(result.observation.coverage)["revision"], revision)

    def test_tree_entry_pagination_is_selector_bounded_and_idempotent(self) -> None:
        first_intent = self.intent(
            SourceTool.TREE,
            {"revision": self.commit, "page_size": "1", "cursor": "0"},
            key="tree-page-1",
            budget=OperationBudget(max_calls=1, max_items=1, max_bytes=2048),
        )
        first = self.operations.execute(first_intent)
        replay = self.operations.execute(first_intent)
        second = self.operations.execute(
            self.intent(
                SourceTool.TREE,
                {
                    "revision": self.commit,
                    "page_size": "1",
                    "cursor": first.observation.next_cursor,
                },
                key="tree-page-2",
                budget=OperationBudget(max_calls=1, max_items=1, max_bytes=2048),
            )
        )

        self.assertEqual(first.status, SourceOperationStatus.PARTIAL)
        self.assertEqual(first.observation.item_count, 1)
        self.assertEqual(first.observation.next_cursor, "1")
        self.assertEqual(second.status, SourceOperationStatus.COMPLETED)
        self.assertFalse(second.observation.has_more)
        paths = {
            json.loads(result.observation.artifacts[0].payload)["path"]
            for result in (first, second)
        }
        self.assertEqual(paths, {"src/OrderService.java", "src/notes.txt"})
        self.assertEqual(replay.operation_id, first.operation_id)
        self.assertEqual(replay.digest, first.digest)
        self.assertEqual(
            replay.observation.artifacts[0].artifact_id,
            first.observation.artifacts[0].artifact_id,
        )

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
