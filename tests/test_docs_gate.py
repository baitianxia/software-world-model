"""Tests for the generic documentation gate in ``scripts/docs.py``."""

from __future__ import annotations

import tempfile
import textwrap
import unittest
from pathlib import Path

from scripts import docs


def _front(identifier: str, kind: str, *, depends_on: str = "", authority: str = "normative", extra: str = "") -> str:
    return textwrap.dedent(
        f"""\
        ---
        id: {identifier}
        kind: {kind}
        status: current
        authority: {authority}
        owners: [architecture]
        depends_on: [{depends_on}]
        code: []
        tests: []
        {extra}
        ---

        """
    ).replace("\n\n---\n\n", "\n---\n\n")


class _Fixture:
    def __init__(self) -> None:
        self._temporary = tempfile.TemporaryDirectory()
        self.root = Path(self._temporary.name)
        self.saved = {
            name: getattr(docs, name)
            for name in ("REPOSITORY", "DOCS", "GENERATED", "SCAN_ROOTS", "PLAIN_LINK_FILES")
        }
        docs_root = self.root / "docs"
        docs.REPOSITORY = self.root
        docs.DOCS = docs_root
        docs.GENERATED = docs_root / "_generated"
        docs.SCAN_ROOTS = (docs_root / "system", docs_root / "project")
        docs.PLAIN_LINK_FILES = (self.root / "README.md",)
        self.write("README.md", "# repo\n")
        self.write(
            "docs/system/a.md",
            _front("SYS-A", "system-architecture") + "# A\n",
        )
        self.write(
            "docs/project/current.md",
            _front(
                "PROJECT-CURRENT",
                "project-current",
                authority="current-development",
                extra="active_iteration: none\nactive_slice: none",
            )
            + "# Current\n",
        )

    def write(self, relative: str, text: str) -> None:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def errors(self) -> list[str]:
        documents, errors = docs.load_documents()
        return errors + docs.validate(documents)

    def close(self) -> None:
        for name, value in self.saved.items():
            setattr(docs, name, value)
        self._temporary.cleanup()


class DocumentationGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = _Fixture()

    def tearDown(self) -> None:
        self.fixture.close()

    def test_minimal_valid_set_passes(self) -> None:
        self.assertEqual(self.fixture.errors(), [])

    def test_unknown_dependency_is_rejected(self) -> None:
        self.fixture.write("docs/system/b.md", _front("SYS-B", "system-architecture", depends_on="SYS-MISSING") + "x\n")
        self.assertTrue(any("unknown dependency id: SYS-MISSING" in error for error in self.fixture.errors()))

    def test_system_may_not_depend_on_project(self) -> None:
        self.fixture.write("docs/system/b.md", _front("SYS-B", "system-architecture", depends_on="PROJECT-CURRENT") + "x\n")
        self.assertTrue(any("system document depends on project document" in error for error in self.fixture.errors()))

    def test_system_may_not_link_to_project(self) -> None:
        self.fixture.write("docs/system/b.md", _front("SYS-B", "system-architecture") + "[c](../project/current.md)\n")
        self.assertTrue(any("system document links to project document" in error for error in self.fixture.errors()))

    def test_broken_link_is_rejected(self) -> None:
        self.fixture.write("docs/system/b.md", _front("SYS-B", "system-architecture") + "[x](missing.md)\n")
        self.assertTrue(any("broken link: missing.md" in error for error in self.fixture.errors()))

    def test_dependency_cycle_is_rejected(self) -> None:
        self.fixture.write("docs/system/b.md", _front("SYS-B", "system-architecture", depends_on="SYS-C") + "x\n")
        self.fixture.write("docs/system/c.md", _front("SYS-C", "system-architecture", depends_on="SYS-B") + "x\n")
        self.assertTrue(any("dependency cycle" in error for error in self.fixture.errors()))

    def test_system_authority_must_be_normative(self) -> None:
        self.fixture.write("docs/system/b.md", _front("SYS-B", "system-architecture", authority="historical") + "x\n")
        self.assertTrue(any("system authority must be normative" in error for error in self.fixture.errors()))

    def test_missing_front_matter_field_is_rejected(self) -> None:
        self.fixture.write("docs/system/b.md", "---\nid: SYS-B\n---\nx\n")
        self.assertTrue(any("missing metadata field" in error for error in self.fixture.errors()))

    def test_finding_classification_is_checked(self) -> None:
        self.fixture.write(
            "docs/project/iterations/iteration-001/README.md",
            _front("ITER-001-INDEX", "iteration-index", authority="project", extra="iteration: ITER-001") + "x\n",
        )
        self.fixture.write(
            "docs/project/iterations/iteration-001/findings/FINDING-001-001.md",
            _front(
                "FINDING-001-001",
                "implementation-finding",
                authority="implementation-evidence",
                extra="iteration: ITER-001\nclassification: made-up\ndisposition: x\ntarget: SYS-A",
            ).replace("status: current", "status: dispositioned")
            + "x\n",
        )
        self.assertTrue(any("invalid finding classification" in error for error in self.fixture.errors()))

    def test_generated_outputs_round_trip(self) -> None:
        documents, errors = docs.load_documents()
        self.assertEqual(errors, [])
        outputs = docs.render_outputs(documents)
        self.assertTrue(docs.check_generated(outputs))
        docs.generate(outputs)
        self.assertEqual(docs.check_generated(outputs), [])

    def test_safe_load_manifest_reads_nested_mappings(self) -> None:
        manifest = docs.safe_load_manifest("a:\n  b: 1\n  c:\n    d: text\n")
        self.assertEqual(manifest, {"a": {"b": 1, "c": {"d": "text"}}})


class RepositoryDocumentationTests(unittest.TestCase):
    def test_current_repository_documents_pass(self) -> None:
        documents, errors = docs.load_documents()
        self.assertEqual(errors + docs.validate(documents), [])


if __name__ == "__main__":
    unittest.main()
