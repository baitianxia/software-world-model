"""Tests for the read-only exact-revision tool set (baseline V1.4, 7.7)."""

from __future__ import annotations

from pathlib import Path
import subprocess
import tempfile
import unittest

from software_world_model.cross_cutting import DomainError, ErrorCode
from software_world_model.source_integration.exact_revision_tools import (
    ExactRevisionReadTools,
    ObservationStatus,
    ReadScope,
)


def _git(root: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *arguments],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    ).stdout.strip()


class ExactRevisionReadToolsTests(unittest.TestCase):
    def setUp(self) -> None:
        self._temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self._temporary.cleanup)
        self.root = Path(self._temporary.name)
        _git(self.root, "init", "-q")
        self._write(
            "app/src/main/java/demo/LoginService.java",
            "package demo;\n\nclass LoginService {\n  String login(String user) {\n"
            "    return tokenUtil.generateToken(user);\n  }\n}\n",
        )
        self._write("app/src/main/resources/application.yml", "jwt:\n  secret: demo\n  expiration: 604800\n")
        self._write("secret/keys.txt", "generateToken should never be visible\n")
        (self.root / "app" / "logo.bin").write_bytes(b"\0\1\2generateToken")
        self._commit("first")
        self.revision = _git(self.root, "rev-parse", "HEAD")
        self._write("app/src/main/java/demo/LoginService.java", "changed after the bound revision\n")
        self._commit("second")
        self.tools = ExactRevisionReadTools(
            ReadScope(
                repository=self.root,
                revision=self.revision,
                exclude_prefixes=("secret",),
                max_items=50,
            )
        )

    def _write(self, relative: str, text: str) -> None:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def _commit(self, message: str) -> None:
        _git(self.root, "add", "-A")
        _git(self.root, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", message)

    def test_scope_requires_exact_commit(self) -> None:
        with self.assertRaises(DomainError):
            ReadScope(repository=self.root, revision="HEAD")
        with self.assertRaises(DomainError) as missing:
            ExactRevisionReadTools(ReadScope(repository=self.root, revision="0" * 40))
        self.assertIs(missing.exception.code, ErrorCode.SOURCE_REVISION_INCONSISTENT)

    def test_list_paths_supports_glob_and_honours_exclusions(self) -> None:
        listing = self.tools.list_paths(glob="*.java")
        self.assertEqual([item.path for item in listing.items], ["app/src/main/java/demo/LoginService.java"])
        everything = self.tools.list_paths()
        self.assertNotIn("secret/keys.txt", [item.path for item in everything.items])
        self.assertEqual(everything.status, ObservationStatus.COMPLETE)

    def test_literal_search_is_bound_to_the_exact_revision(self) -> None:
        result = self.tools.search("generateToken")
        paths = {item.path for item in result.items}
        self.assertEqual(paths, {"app/src/main/java/demo/LoginService.java"})
        item = result.items[0]
        self.assertEqual(item.start_line, 5)
        self.assertIn(self.revision, item.locator)
        self.assertTrue(item.content_digest.startswith("sha256:"))

    def test_regex_search_with_path_glob(self) -> None:
        result = self.tools.search(r"expiration:\s+[0-9]+", regex=True, path_glob="*.yml")
        self.assertEqual([item.path for item in result.items], ["app/src/main/resources/application.yml"])

    def test_truncated_search_reports_partial_not_absent(self) -> None:
        self._write("many.txt", "".join(f"hit {index}\n" for index in range(30)))
        self._commit("many")
        revision = _git(self.root, "rev-parse", "HEAD")
        tools = ExactRevisionReadTools(ReadScope(repository=self.root, revision=revision, max_items=50))
        result = tools.search("hit", limit=5)
        self.assertEqual(result.status, ObservationStatus.PARTIAL)
        self.assertEqual(len(result.items), 5)
        self.assertEqual(result.omitted_count, 25)

    def test_empty_search_is_empty_with_coverage(self) -> None:
        result = self.tools.search("doesNotExistAnywhere")
        self.assertEqual(result.status, ObservationStatus.EMPTY)
        self.assertIn("exact revision", result.coverage)

    def test_invalid_regex_is_rejected(self) -> None:
        with self.assertRaises(DomainError) as invalid:
            self.tools.search("(", regex=True)
        self.assertIs(invalid.exception.code, ErrorCode.INVALID_ARGUMENT)

    def test_read_returns_requested_range_from_the_bound_revision(self) -> None:
        result = self.tools.read("app/src/main/java/demo/LoginService.java", start_line=4, end_line=5)
        item = result.items[0]
        self.assertEqual((item.start_line, item.end_line), (4, 5))
        self.assertIn("generateToken", item.text)
        self.assertNotIn("changed after", item.text)

    def test_read_rejects_out_of_scope_traversal_missing_and_binary(self) -> None:
        with self.assertRaises(DomainError) as excluded:
            self.tools.read("secret/keys.txt")
        self.assertIs(excluded.exception.code, ErrorCode.SOURCE_TARGET_OUT_OF_SCOPE)
        with self.assertRaises(DomainError) as traversal:
            self.tools.read("../outside.txt")
        self.assertIs(traversal.exception.code, ErrorCode.SOURCE_TARGET_OUT_OF_SCOPE)
        with self.assertRaises(DomainError) as missing:
            self.tools.read("app/missing.java")
        self.assertIs(missing.exception.code, ErrorCode.SOURCE_TARGET_NOT_FOUND)
        with self.assertRaises(DomainError):
            self.tools.read("app/logo.bin")

    def test_include_prefixes_restrict_every_operation(self) -> None:
        tools = ExactRevisionReadTools(
            ReadScope(repository=self.root, revision=self.revision, include_prefixes=("app/src/main/java",))
        )
        self.assertEqual(len(tools.list_paths().items), 1)
        self.assertEqual(tools.search("expiration").status, ObservationStatus.EMPTY)
        with self.assertRaises(DomainError):
            tools.read("app/src/main/resources/application.yml")

    def test_log_and_blame_stop_at_the_exact_revision(self) -> None:
        history = self.tools.log()
        self.assertEqual(len(history.items), 1)
        self.assertIn("first", history.items[0].text)
        blame = self.tools.blame("app/src/main/java/demo/LoginService.java", start_line=5, end_line=5)
        self.assertEqual(len(blame.items), 1)
        self.assertIn("generateToken", blame.items[0].text)

    def test_observation_digest_is_stable(self) -> None:
        first = self.tools.search("generateToken")
        second = self.tools.search("generateToken")
        self.assertEqual(first.digest, second.digest)


if __name__ == "__main__":
    unittest.main()
