from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "docs.py"
SPEC = importlib.util.spec_from_file_location("docs_gate", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
docs_gate = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = docs_gate
SPEC.loader.exec_module(docs_gate)


class ManifestGateTests(unittest.TestCase):
    COMMIT = "a" * 40

    def validate(self, content: str) -> list[str]:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.yaml"
            path.write_text(content, encoding="utf-8")
            return docs_gate.validate_active_manifest(path, "ITER-002")

    def test_manifest_reads_only_exact_nested_fields(self) -> None:
        errors = self.validate(
            f"""iteration:
  id: WRONG
  status: proposed
evidence:
  id: ITER-002
  status: authorized
  commit: {self.COMMIT}
"""
        )

        self.assertTrue(any("iteration.id" in error for error in errors))
        self.assertTrue(any("iteration.status" in error for error in errors))
        self.assertTrue(any("baseline must be a mapping" in error for error in errors))

    def test_manifest_rejects_duplicate_mapping_keys(self) -> None:
        errors = self.validate(
            f"""iteration:
  id: ITER-002
  id: WRONG
  status: authorized
baseline:
  commit: {self.COMMIT}
"""
        )

        self.assertTrue(any("duplicate key 'id'" in error for error in errors))

    def test_manifest_accepts_the_documented_safe_subset(self) -> None:
        errors = self.validate(
            f"""schema_version: 1
iteration:
  id: ITER-002
  status: in-progress
baseline:
  commit: {self.COMMIT}
  dirty_worktree_allowed: false
system_inputs:
  ids:
    - SYS-CONTRACT-EXAMPLE
external_inputs: []
"""
        )

        self.assertEqual(errors, [])

    def test_manifest_rejects_placeholders_inside_scalar_sequences(self) -> None:
        errors = self.validate(
            f"""iteration:
  id: ITER-002
  status: authorized
baseline:
  commit: {self.COMMIT}
system_inputs:
  ids:
    - ITER-NNN
"""
        )

        self.assertTrue(any("template placeholders" in error for error in errors))

    def test_manifest_rejects_indented_root_or_inconsistent_siblings(self) -> None:
        for content in (
            f"""  iteration:
    id: ITER-002
    status: authorized
  baseline:
    commit: {self.COMMIT}
""",
            f"""iteration:
  id: ITER-002
    status: authorized
baseline:
  commit: {self.COMMIT}
""",
        ):
            with self.subTest(content=content):
                errors = self.validate(content)
                self.assertTrue(any("indentation" in error for error in errors), errors)


class FindingGateTests(unittest.TestCase):
    def document(
        self,
        identifier: str,
        kind: str,
        *,
        iteration: str = "",
        path: str | None = None,
        **metadata: object,
    ) -> docs_gate.Document:
        values: dict[str, object] = {
            "id": identifier,
            "kind": kind,
            "status": "current",
            "iteration": iteration,
        }
        values.update(metadata)
        document_path = docs_gate.REPOSITORY / (
            path or f"docs/project/test-fixtures/{identifier}.md"
        )
        return docs_gate.Document(document_path, values, "# Fixture\n")

    def finding(
        self,
        identifier: str,
        classification: object,
        target: object,
        *,
        status: str = "dispositioned",
        iteration: str = "ITER-002",
        disposition: object = "updated",
        **metadata: object,
    ) -> docs_gate.Document:
        code = metadata.pop("code", [])
        tests = metadata.pop("tests", [])
        return self.document(
            identifier,
            "implementation-finding",
            iteration=iteration,
            status=status,
            classification=classification,
            disposition=disposition,
            target=target,
            code=code,
            tests=tests,
            **metadata,
        )

    def fixtures(self) -> tuple[dict[str, docs_gate.Document], dict[str, docs_gate.Document]]:
        iteration = self.document("ITER-002", "iteration-index", iteration="ITER-002")
        other_iteration = self.document("ITER-003", "iteration-index", iteration="ITER-003")
        slice_document = self.document(
            "ITER-002-SLICE-001", "development-slice", iteration="ITER-002"
        )
        verification = self.document(
            "ITER-002-VERIFICATION", "iteration-verification", iteration="ITER-002"
        )
        system_contract = self.document(
            "SYS-CONTRACT-EXAMPLE",
            "system-contract",
            path="docs/system/contracts/example.md",
        )
        system_quality = self.document(
            "SYS-QUALITY-EXAMPLE",
            "system-quality",
            path="docs/system/quality/example.md",
        )
        roadmap = self.document("ROADMAP-EXAMPLE", "roadmap-candidate")
        documents = {
            document.identifier: document
            for document in (
                iteration,
                other_iteration,
                slice_document,
                verification,
                system_contract,
                system_quality,
                roadmap,
            )
        }
        return documents, {"ITER-002": iteration, "ITER-003": other_iteration}

    def test_disposition_and_target_must_be_single_scalars(self) -> None:
        by_id, indexes = self.fixtures()
        finding = self.finding(
            "FINDING-001",
            "system-contract",
            ["SYS-CONTRACT-EXAMPLE"],
            disposition=["updated"],
        )
        by_id[finding.identifier] = finding

        errors = docs_gate.validate_findings([finding], by_id, indexes)

        self.assertTrue(any("disposition must be a single scalar" in error for error in errors))
        self.assertTrue(any("target must be a single scalar" in error for error in errors))

    def test_each_classification_accepts_only_its_destination_type(self) -> None:
        by_id, indexes = self.fixtures()
        valid = [
            self.finding(
                "FINDING-LOCAL",
                "local-implementation",
                "scripts/docs.py",
                code=["scripts/docs.py"],
            ),
            self.finding("FINDING-DESIGN", "iteration-design", "ITER-002-SLICE-001"),
            self.finding("FINDING-SYSTEM", "system-contract", "SYS-CONTRACT-EXAMPLE"),
            self.finding("FINDING-VERIFY", "verification", "ITER-002-VERIFICATION"),
            self.finding("FINDING-QUALITY", "verification", "SYS-QUALITY-EXAMPLE"),
            self.finding("FINDING-ROADMAP", "roadmap", "ROADMAP-EXAMPLE"),
        ]
        by_id.update({document.identifier: document for document in valid})

        self.assertEqual(docs_gate.validate_findings(valid, by_id, indexes), [])

        wrong = self.finding("FINDING-WRONG", "system-contract", "ROADMAP-EXAMPLE")
        by_id[wrong.identifier] = wrong
        errors = docs_gate.validate_findings([wrong], by_id, indexes)
        self.assertTrue(any("non-index System document" in error for error in errors))

    def test_superseded_by_must_be_an_existing_same_iteration_finding(self) -> None:
        by_id, indexes = self.fixtures()
        replacement = self.finding(
            "FINDING-NEW", "system-contract", "pending", status="open"
        )
        cross_iteration = self.finding(
            "FINDING-OTHER",
            "system-contract",
            "pending",
            status="open",
            iteration="ITER-003",
        )
        by_id.update(
            {
                replacement.identifier: replacement,
                cross_iteration.identifier: cross_iteration,
            }
        )

        valid = self.finding(
            "FINDING-OLD",
            "system-contract",
            "pending",
            status="superseded",
            superseded_by="FINDING-NEW",
        )
        by_id[valid.identifier] = valid
        self.assertEqual(docs_gate.validate_findings([valid], by_id, indexes), [])

        for reference, expected in (
            ("FINDING-OLD", "cannot reference the finding itself"),
            ("FINDING-MISSING", "existing Finding"),
            ("FINDING-OTHER", "same iteration"),
        ):
            with self.subTest(reference=reference):
                invalid = self.finding(
                    "FINDING-OLD",
                    "system-contract",
                    "pending",
                    status="superseded",
                    superseded_by=reference,
                )
                candidate_ids = dict(by_id)
                candidate_ids[invalid.identifier] = invalid
                errors = docs_gate.validate_findings([invalid], candidate_ids, indexes)
                self.assertTrue(any(expected in error for error in errors), errors)

    def test_rejected_finding_requires_scalar_none_target(self) -> None:
        by_id, indexes = self.fixtures()
        valid = self.finding(
            "FINDING-REJECTED",
            "invalid",
            "none",
            status="rejected",
            disposition="rejected-with-evidence",
        )
        by_id[valid.identifier] = valid
        self.assertEqual(docs_gate.validate_findings([valid], by_id, indexes), [])

        invalid = self.finding(
            "FINDING-REJECTED",
            "invalid",
            ["none"],
            status="rejected",
            disposition="rejected-with-evidence",
        )
        errors = docs_gate.validate_findings([invalid], by_id, indexes)
        self.assertTrue(any("target must be a single scalar" in error for error in errors))


class PlaceholderAndAcceptanceGateTests(unittest.TestCase):
    ACCEPTANCE_BODY = """# Acceptance

## Exact subject and scope
Exact subject recorded.

## Gate results and limitations
All scoped gates recorded with limitations.

## Finding dispositions and System write-back
All findings were dispositioned.

## Verdict
Accepted for the stated scope.
"""

    def test_body_placeholder_detection_does_not_treat_rule_text_as_pending_input(self) -> None:
        self.assertFalse(
            docs_gate.has_unresolved_placeholder(
                "The field must not remain pending; compare x < y and z > q."
            )
        )
        self.assertTrue(docs_gate.has_unresolved_placeholder("Outcome: <scope>"))
        self.assertTrue(docs_gate.has_unresolved_placeholder("Iteration NNN"))

    def test_required_template_sections_must_have_content(self) -> None:
        document = docs_gate.Document(
            docs_gate.REPOSITORY / "docs/project/iterations/iteration-002/proposal.md",
            {"kind": "iteration-proposal"},
            """# Proposal

## Trigger and evidence

## Outcome and users
real outcome
""",
        )

        empty = docs_gate.empty_active_required_sections(document)

        self.assertIn("Trigger and evidence", empty)
        self.assertNotIn("Outcome and users", empty)
        self.assertIn("Authorization decision", empty)

    def test_heading_only_document_has_no_substantive_body(self) -> None:
        document = docs_gate.Document(
            docs_gate.REPOSITORY / "docs/project/iterations/iteration-002/verification-matrix.md",
            {"kind": "iteration-verification"},
            "# Verification\n\n## Cases\n",
        )

        self.assertFalse(docs_gate.has_substantive_body(document))

    def test_completed_acceptance_rejects_pending_or_collection_critical_fields(self) -> None:
        path = docs_gate.REPOSITORY / "docs/project/iterations/iteration-002/results/acceptance.md"
        for field, value in (
            ("accepted_scope", "pending"),
            ("accepted_scope", "<scope>"),
            ("accepted_scope", ["local"]),
            ("iteration", "ITER-NNN"),
        ):
            with self.subTest(field=field, value=value):
                metadata: dict[str, object] = {
                    "id": "ITER-002-RESULT-ACCEPTANCE",
                    "kind": "iteration-acceptance",
                    "status": "completed",
                    "iteration": "ITER-002",
                    "accepted_scope": "local",
                    "subject_identity": "exact-manifest-subject",
                    "baseline_commit": "a" * 40,
                    "baseline_relation": "exact-at-run",
                    "production_activation": "not-executed",
                }
                metadata[field] = value
                document = docs_gate.Document(path, metadata, self.ACCEPTANCE_BODY)
                errors = docs_gate.validate_completed_acceptance(document)
                self.assertTrue(any(field in error for error in errors), errors)

    def test_completed_acceptance_requires_exact_baseline_and_nonempty_sections(self) -> None:
        path = docs_gate.REPOSITORY / "docs/project/iterations/iteration-002/results/acceptance.md"
        metadata = {
            "id": "ITER-002-RESULT-ACCEPTANCE",
            "kind": "iteration-acceptance",
            "status": "completed",
            "iteration": "ITER-002",
            "accepted_scope": "local",
            "subject_identity": "exact-manifest-subject",
            "baseline_commit": "not-a-commit",
            "baseline_relation": "exact-at-run",
            "production_activation": "not-executed",
        }
        body = self.ACCEPTANCE_BODY.replace(
            "All findings were dispositioned.", ""
        )
        document = docs_gate.Document(path, metadata, body)

        errors = docs_gate.validate_completed_acceptance(document)

        self.assertTrue(any("baseline_commit must be" in error for error in errors))
        self.assertTrue(
            any("Finding dispositions and System write-back" in error for error in errors)
        )


if __name__ == "__main__":
    unittest.main()
