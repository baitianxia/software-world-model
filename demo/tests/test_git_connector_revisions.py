from __future__ import annotations

from pathlib import Path
import subprocess
import tempfile
import unittest

from swm_demo.artifact_contract import (
    ArtifactRequest,
    RevisionComparison,
    SourceArtifact,
    SourceObjectRef,
)
from swm_demo.source_integration import (
    LocalGitConnector,
    LocalGitConnectorProvider,
    SourceAccessError,
)


SCOPE_ID = "system:revision-test"


class LocalGitRevisionToolsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.repository = Path(self.temporary.name) / "repository"
        self.repository.mkdir()
        self._git("init", "--quiet")
        self._git("config", "user.name", "Revision Test")
        self._git("config", "user.email", "revision-test@example.com")

        (self.repository / "src").mkdir()
        (self.repository / "document").mkdir()
        (self.repository / "README.md").write_text(
            "revision fixture\n", encoding="utf-8"
        )
        (self.repository / "src" / "demo.txt").write_text("alpha\n", encoding="utf-8")
        (self.repository / "document" / "binary.rp").write_bytes(b"\xff\x00\xfe")
        self._git("add", "README.md", "src/demo.txt", "document/binary.rp")
        self._git("commit", "--quiet", "-m", "revision A")
        self.revision_a = self._git("rev-parse", "HEAD")

        (self.repository / "src" / "demo.txt").write_text("beta\n", encoding="utf-8")
        self._git("add", "src/demo.txt")
        self._git("commit", "--quiet", "-m", "revision B")
        self.revision_b = self._git("rev-parse", "HEAD")
        self.connector = LocalGitConnector(self.repository)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _git(self, *args: str) -> str:
        completed = subprocess.run(
            ["git", *args],
            cwd=self.repository,
            check=True,
            capture_output=True,
            text=True,
        )
        return completed.stdout.strip()

    def test_collect_reads_non_head_revision_and_ignores_dirty_worktree(self) -> None:
        (self.repository / "src" / "demo.txt").write_text("dirty\n", encoding="utf-8")
        (self.repository / "untracked.txt").write_text("untracked\n", encoding="utf-8")

        collection = self.connector.collect_sources(
            scope_id=SCOPE_ID,
            request=ArtifactRequest(
                build_profile="revision-test",
                include_globs=("**/*.txt",),
                revision=self.revision_a,
            ),
            expected_revision=self.revision_b,
        )

        self.assertEqual(self.revision_a, collection.revision)
        self.assertEqual(
            ["src/demo.txt"],
            [item.relative_path for item in collection.artifacts],
        )
        self.assertEqual("alpha\n", collection.artifacts[0].content)
        self.assertEqual(self.revision_a, collection.artifacts[0].revision)
        self.assertEqual(self.revision_b, self._git("rev-parse", "HEAD"))
        self.assertEqual(
            "dirty\n",
            (self.repository / "src" / "demo.txt").read_text(encoding="utf-8"),
        )

    def test_resolve_revision_returns_full_oid_and_ordered_parents(self) -> None:
        root = self.connector.resolve_revision(SCOPE_ID, self.revision_a[:8])
        child = self.connector.resolve_revision(SCOPE_ID, "HEAD")

        self.assertEqual(self.revision_a, root.revision)
        self.assertEqual(40, len(root.revision))
        self.assertEqual((), root.parent_revisions)
        self.assertEqual(self.revision_b, child.revision)
        self.assertEqual((self.revision_a,), child.parent_revisions)
        self.assertEqual("git-commit", child.object_type)

    def test_search_returns_refs_and_read_materializes_only_selected_file(self) -> None:
        at_a = self.connector.search_at_revision(
            SCOPE_ID,
            self.revision_a,
            query="alpha",
            include_globs=("**/*.txt",),
        )
        missing_at_a = self.connector.search_at_revision(
            SCOPE_ID,
            self.revision_a,
            query="beta",
            include_globs=("**/*.txt",),
        )
        at_b = self.connector.search_at_revision(
            SCOPE_ID,
            self.revision_b,
            query="beta",
            include_globs=("**/*.txt",),
        )

        self.assertEqual(("src/demo.txt",), tuple(item.external_key for item in at_a))
        self.assertEqual((), missing_at_a)
        self.assertEqual(("src/demo.txt",), tuple(item.external_key for item in at_b))
        self.assertTrue(all(isinstance(item, SourceObjectRef) for item in at_a))
        self.assertTrue(all(not isinstance(item, SourceArtifact) for item in at_a))

        first = self.connector.read_files_at_revision(
            SCOPE_ID, self.revision_a, at_a
        )
        repeated = self.connector.read_files_at_revision(
            SCOPE_ID, self.revision_a, at_a
        )
        self.assertEqual(1, len(first))
        self.assertEqual("alpha\n", first[0].content)
        self.assertEqual(first[0].artifact_id, repeated[0].artifact_id)
        self.assertEqual(first[0].content_hash, repeated[0].content_hash)

    def test_explicit_forward_and_reverse_diffs_have_distinct_identity(self) -> None:
        forward = self.connector.compare_revisions(
            SCOPE_ID,
            RevisionComparison(self.revision_a[:8], self.revision_b[:8]),
            include_globs=("src/*.txt",),
        )
        reverse = self.connector.compare_revisions(
            SCOPE_ID,
            RevisionComparison(self.revision_b, self.revision_a),
            include_globs=("src/*.txt",),
        )

        self.assertEqual("git-diff", forward.artifact_type)
        self.assertEqual(self.revision_b, forward.revision)
        self.assertEqual(
            RevisionComparison(self.revision_a, self.revision_b),
            forward.comparison,
        )
        self.assertEqual(
            RevisionComparison(self.revision_b, self.revision_a),
            reverse.comparison,
        )
        self.assertNotEqual(forward.artifact_id, reverse.artifact_id)
        self.assertIn("-alpha", forward.content)
        self.assertIn("+beta", forward.content)
        self.assertIn("-beta", reverse.content)
        self.assertIn("+alpha", reverse.content)

    def test_commit_and_comparison_requests_are_composed_into_collection(self) -> None:
        collection = self.connector.collect_sources(
            SCOPE_ID,
            ArtifactRequest(
                build_profile="revision-test",
                include_globs=("README.md",),
                revision=self.revision_b,
                commit_revisions=(self.revision_b,),
                comparisons=(
                    RevisionComparison(self.revision_a, self.revision_b),
                ),
            ),
        )

        by_type = {item.artifact_type: item for item in collection.artifacts}
        self.assertEqual(
            {"markdown-document", "git-commit", "git-diff"}, set(by_type)
        )
        self.assertNotIn("diff --git", by_type["git-commit"].content)
        self.assertEqual(
            RevisionComparison(self.revision_a, self.revision_b),
            by_type["git-diff"].comparison,
        )

    def test_commit_only_request_does_not_materialize_the_repository_tree(self) -> None:
        collection = self.connector.collect_sources(
            SCOPE_ID,
            ArtifactRequest(
                build_profile="commit-only",
                include_globs=(),
                revision=self.revision_b,
                git_commit_ids=(self.revision_b,),
            ),
        )

        self.assertEqual(1, len(collection.artifacts))
        self.assertEqual("git-commit", collection.artifacts[0].artifact_type)
        self.assertEqual(
            f".git/commits/{self.revision_b}.patch",
            collection.artifacts[0].relative_path,
        )

    def test_path_traversal_is_rejected(self) -> None:
        with self.assertRaisesRegex(SourceAccessError, "repository-relative path"):
            self.connector.read_files_at_revision(
                SCOPE_ID, self.revision_a, ("../outside.txt",)
            )
        with self.assertRaisesRegex(SourceAccessError, "Git tree pattern"):
            self.connector.search_at_revision(
                SCOPE_ID,
                self.revision_a,
                include_globs=("../*.txt",),
            )

    def test_provider_declares_revision_tool_capabilities(self) -> None:
        capabilities = set(LocalGitConnectorProvider().capabilities())
        self.assertTrue(
            {
                "resolve-revision",
                "search-at-revision",
                "read-files-at-revision",
                "read-commit",
                "compare-revisions",
            }.issubset(capabilities)
        )


if __name__ == "__main__":
    unittest.main()
