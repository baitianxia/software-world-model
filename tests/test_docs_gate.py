from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "docs.py"
SPEC = importlib.util.spec_from_file_location("docs_gate", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
docs_gate = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = docs_gate
SPEC.loader.exec_module(docs_gate)


def product_goal_verification(
    path: Path,
    *,
    evidence: str = "pending",
    status: str = "not-run / blocking",
    claim: str | None = None,
    kind: str = "iteration-verification",
    result_id: str = "pending",
) -> docs_gate.Document:
    metadata = {
        "id": "ITER-007-VERIFICATION",
        "kind": kind,
        "status": "not-run",
        "iteration": "ITER-007",
        **docs_gate.PRODUCT_GOAL_V000_METADATA,
        "product_goal_result_id": result_id,
    }
    body = (
        "| Case | Claim | Level | Frozen input / oracle | Expected | Evidence | Status / blocking meaning |\n"
        "|---|---|---|---|---|---|---|\n"
        f"| V-000 | {claim or docs_gate.PRODUCT_GOAL_V000_CLAIM} | "
        f"{docs_gate.PRODUCT_GOAL_V000_LEVEL} | "
        f"{docs_gate.PRODUCT_GOAL_V000_FROZEN_INPUT} | "
        f"{docs_gate.PRODUCT_GOAL_V000_EXPECTED} | {evidence} | {status} |\n"
    )
    return docs_gate.Document(path, metadata, body)


class ManifestGateTests(unittest.TestCase):
    COMMIT = "a" * 40

    def validate(self, content: str, iteration: str = "ITER-002") -> list[str]:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.yaml"
            path.write_text(content, encoding="utf-8")
            return docs_gate.validate_active_manifest(path, iteration)

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

    def test_product_goal_alignment_manifest_is_required_from_iteration_007(self) -> None:
        without_alignment = f"""iteration:
  id: ITER-007
  status: authorized
baseline:
  commit: {self.COMMIT}
"""

        errors = self.validate(without_alignment, "ITER-007")

        self.assertTrue(any("product_goal_alignment" in error for error in errors))
        self.assertEqual(self.validate(without_alignment.replace("ITER-007", "ITER-006"), "ITER-006"), [])

    def test_product_goal_alignment_manifest_requires_resolved_nonempty_fields(self) -> None:
        valid = f"""iteration:
  id: ITER-007
  status: authorized
baseline:
  commit: {self.COMMIT}
product_goal_alignment:
  target_ref: SYS-PRODUCT-SUCCESS
  baseline_gap: general-source-qa-not-supported
  accepted_capability_refs:
    - maven-structure
  new_capability_slice_refs:
    - semantic-source-model
  held_out_free_question_delta: two-new-supported-cross-domain-questions
  held_out_evaluation_owner: independent-evaluator
  implementation_question_visibility: hidden
  implementation_project_identity_and_source_visibility: hidden-until-product-code-freeze
  evaluation_project_manifest_digest: sha256:{'1' * 64}
  held_out_suite_digest: sha256:{'2' * 64}
  baseline_result_digest: sha256:{'3' * 64}
  mature_source_agent_protocol_digest: sha256:{'4' * 64}
  authorized_software_sources_digest: sha256:{'5' * 64}
  held_out_question_count: 10
  held_out_answerable_question_count: 8
  held_out_boundary_question_count: 2
  held_out_answerable_without_symbol_count_minimum: 4
  held_out_answerable_without_symbol_per_project_minimum: 2
  held_out_baseline_supported_count: 2
  held_out_target_supported_count: 8
  supported_count_denominator: answerable-only
  boundary_gap_counted_as_supported: false
  cross_domain_cases:
    - V-XD-001
  blocking_case_ids:
    - V-XD-001
    - V-WEB-001
    - V-ADHOC-001
  cross_domain_case_count: 1
  cross_domain_bindings:
    binding_001:
      case_id: V-XD-001
      accepted_capability_ref: maven-structure
      new_slice_ref: semantic-source-model
  first_product_web_checkpoint: V-WEB-001
  web_checkpoint_binding:
    case_id: V-WEB-001
    new_slice_ref: semantic-source-model
    executes_cross_domain_case_id: V-XD-001
  live_ad_hoc_question_checkpoint: V-ADHOC-001
  live_ad_hoc_checkpoint_binding:
    case_id: V-ADHOC-001
    new_slice_ref: semantic-source-model
    executes_cross_domain_case_id: V-XD-001
  live_ad_hoc_question_count: 2
  live_ad_hoc_without_symbol_count_minimum: 1
  stop_or_redirect_conditions:
    - no-held-out-quality-delta
"""
        self.assertEqual(self.validate(valid, "ITER-007"), [])

        higher_than_minimum = (
            valid.replace("held_out_question_count: 10", "held_out_question_count: 12")
            .replace(
                "held_out_answerable_question_count: 8",
                "held_out_answerable_question_count: 10",
            )
            .replace(
                "held_out_target_supported_count: 8",
                "held_out_target_supported_count: 9",
            )
        )
        self.assertEqual(self.validate(higher_than_minimum, "ITER-007"), [])
        target_above_answerable = higher_than_minimum.replace(
            "held_out_target_supported_count: 9",
            "held_out_target_supported_count: 11",
        )
        self.assertTrue(
            any(
                "held-out target must be above baseline" in error
                for error in self.validate(target_above_answerable, "ITER-007")
            )
        )

        invalid_cases = (
            (
                valid.replace("target_ref: SYS-PRODUCT-SUCCESS", "target_ref: WRONG"),
                "target_ref",
            ),
            (
                valid.replace(
                    "baseline_gap: general-source-qa-not-supported",
                    "baseline_gap: pending",
                ),
                "baseline_gap",
            ),
            (
                valid.replace(
                    "implementation_question_visibility: hidden",
                    "implementation_question_visibility: visible",
                ),
                "implementation_question_visibility",
            ),
            (
                valid.replace(
                    "accepted_capability_refs:\n    - maven-structure",
                    "accepted_capability_refs: []",
                ),
                "accepted_capability_refs",
            ),
            (
                valid.replace(
                    "new_capability_slice_refs:\n    - semantic-source-model",
                    "new_capability_slice_refs: []",
                ),
                "new_capability_slice_refs",
            ),
            (
                valid.replace(
                    "cross_domain_cases:\n    - V-XD-001",
                    "cross_domain_cases: []",
                ),
                "cross_domain_cases",
            ),
            (
                valid.replace(
                    "accepted_capability_ref: maven-structure",
                    "accepted_capability_ref: isolated-view",
                ),
                "cross_domain_bindings",
            ),
            (
                valid.replace(
                    "stop_or_redirect_conditions:\n    - no-held-out-quality-delta",
                    "stop_or_redirect_conditions: []",
                ),
                "stop_or_redirect_conditions",
            ),
            (
                valid.replace(
                    "accepted_capability_refs:\n    - maven-structure",
                    "accepted_capability_refs:\n    bogus:\n      - maven-structure",
                ),
                "accepted_capability_refs",
            ),
            (
                valid.replace("    - maven-structure", '    - ""'),
                "accepted_capability_refs",
            ),
            (
                valid.replace(
                    "held_out_evaluation_owner: independent-evaluator",
                    "held_out_evaluation_owner: developer",
                ),
                "held_out_evaluation_owner",
            ),
            (
                valid.replace(
                    "held_out_target_supported_count: 8",
                    "held_out_target_supported_count: 2",
                ),
                "held-out target",
            ),
            (
                valid.replace(
                    "live_ad_hoc_question_count: 2",
                    "live_ad_hoc_question_count: 0",
                ),
                "live_ad_hoc_question_count",
            ),
            (
                valid.replace(
                    "live_ad_hoc_question_checkpoint: V-ADHOC-001",
                    "live_ad_hoc_question_checkpoint: none",
                ),
                "live_ad_hoc_question_checkpoint",
            ),
        )
        for invalid, field in invalid_cases:
            with self.subTest(field=field, invalid=invalid):
                errors = self.validate(invalid, "ITER-007")
                self.assertTrue(any(field in error for error in errors), errors)

    def test_product_goal_alignment_documents_require_target_and_v000(self) -> None:
        proposal = docs_gate.Document(
            docs_gate.REPOSITORY / "docs/project/iterations/iteration-007/proposal.md",
            {"kind": "iteration-proposal", "depends_on": []},
            "# Proposal\n",
        )
        verification = docs_gate.Document(
            docs_gate.REPOSITORY
            / "docs/project/iterations/iteration-007/verification-matrix.md",
            {"kind": "iteration-verification"},
            "# Verification\n",
        )

        errors = docs_gate.validate_product_goal_alignment_documents(
            proposal, verification, "ITER-007"
        )

        self.assertTrue(any("SYS-PRODUCT-SUCCESS" in error for error in errors))
        self.assertTrue(any("V-000" in error for error in errors))
        proposal.metadata["depends_on"] = ["SYS-PRODUCT-SUCCESS"]
        verification = product_goal_verification(
            verification.path,
        )
        self.assertEqual(
            docs_gate.validate_product_goal_alignment_documents(
                proposal, verification, "ITER-007"
            ),
            [],
        )
        self.assertEqual(
            docs_gate.validate_product_goal_alignment_documents(
                proposal, docs_gate.Document(verification.path, verification.metadata, ""), "ITER-006"
            ),
            [],
        )

    def test_verification_template_carries_the_exact_v000_contract(self) -> None:
        path = (
            docs_gate.REPOSITORY
            / "docs/project/governance/templates/verification-matrix.md"
        )
        document, parse_errors = docs_gate.parse_document(path)
        self.assertEqual(parse_errors, [])
        assert document is not None
        metadata = {**document.metadata, "iteration": "ITER-007"}
        verification = docs_gate.Document(path, metadata, document.body)
        self.assertEqual(
            docs_gate.validate_product_goal_v000(verification, "ITER-007"), []
        )

    def test_v000_rejects_nonblocking_and_requires_pass_at_completion(self) -> None:
        path = (
            docs_gate.REPOSITORY
            / "docs/project/iterations/iteration-007/verification-matrix.md"
        )
        nonblocking = product_goal_verification(
            path, evidence="result-ref", status="PASS / non-blocking"
        )
        errors = docs_gate.validate_product_goal_v000(
            nonblocking, "ITER-007", require_pass=True
        )
        self.assertTrue(any("remain blocking" in error for error in errors), errors)

        for status, evidence in (
            ("not-run / blocking", "pending"),
            ("FAIL / blocking", "result-ref"),
            ("PASS / blocking", "pending"),
            ("PASS / blocking", "none"),
        ):
            with self.subTest(status=status, evidence=evidence):
                document = product_goal_verification(
                    path, evidence=evidence, status=status
                )
                errors = docs_gate.validate_product_goal_v000(
                    document, "ITER-007", require_pass=True
                )
                self.assertTrue(errors)

        risk_only = product_goal_verification(
            path,
            evidence="risk-result",
            status="PASS / blocking",
            claim="仅关闭解析器风险，无用户可见变化",
        )
        errors = docs_gate.validate_product_goal_v000(
            risk_only, "ITER-007", require_pass=True
        )
        self.assertTrue(any("claim" in error for error in errors), errors)

        unbound = product_goal_verification(
            path,
            evidence="risk-result",
            status="PASS / blocking",
            result_id="risk-result",
        )
        errors = docs_gate.validate_product_goal_v000(
            unbound, "ITER-007", require_pass=True, by_id={}
        )
        self.assertTrue(any("same-iteration PASS" in error for error in errors), errors)

    def test_manifest_alignment_accepts_safe_yaml_key_whitespace(self) -> None:
        content = f"""iteration:
  id: ITER-007
  status: authorized
baseline:
  commit: {self.COMMIT}
product_goal_alignment :
  target_ref: SYS-PRODUCT-SUCCESS
  baseline_gap: general-source-qa-not-supported
  accepted_capability_refs :
    - maven-structure
  new_capability_slice_refs:
    - semantic-source-model
  held_out_free_question_delta: two-new-supported-cross-domain-questions
  held_out_evaluation_owner: independent-evaluator
  implementation_question_visibility: hidden
  implementation_project_identity_and_source_visibility: hidden-until-product-code-freeze
  evaluation_project_manifest_digest: sha256:{'1' * 64}
  held_out_suite_digest: sha256:{'2' * 64}
  baseline_result_digest: sha256:{'3' * 64}
  mature_source_agent_protocol_digest: sha256:{'4' * 64}
  authorized_software_sources_digest: sha256:{'5' * 64}
  held_out_question_count: 10
  held_out_answerable_question_count: 8
  held_out_boundary_question_count: 2
  held_out_answerable_without_symbol_count_minimum: 4
  held_out_answerable_without_symbol_per_project_minimum: 2
  held_out_baseline_supported_count: 2
  held_out_target_supported_count: 8
  supported_count_denominator: answerable-only
  boundary_gap_counted_as_supported: false
  cross_domain_cases:
    - V-XD-001
  blocking_case_ids:
    - V-XD-001
    - V-WEB-001
    - V-ADHOC-001
  cross_domain_case_count: 1
  cross_domain_bindings:
    binding_001:
      case_id: V-XD-001
      accepted_capability_ref: maven-structure
      new_slice_ref: semantic-source-model
  first_product_web_checkpoint: V-WEB-001
  web_checkpoint_binding:
    case_id: V-WEB-001
    new_slice_ref: semantic-source-model
    executes_cross_domain_case_id: V-XD-001
  live_ad_hoc_question_checkpoint: V-ADHOC-001
  live_ad_hoc_checkpoint_binding:
    case_id: V-ADHOC-001
    new_slice_ref: semantic-source-model
    executes_cross_domain_case_id: V-XD-001
  live_ad_hoc_question_count: 2
  live_ad_hoc_without_symbol_count_minimum: 1
  stop_or_redirect_conditions:
    - no-held-out-quality-delta
"""
        self.assertEqual(self.validate(content, "ITER-007"), [])

    def test_product_goal_capability_refs_must_resolve_to_old_contract_and_new_slice(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory)
            manifest = repository / "manifest.yaml"
            manifest.write_text(
                """product_goal_alignment:
  accepted_capability_refs:
    - SYS-CONTRACT-OLD
  new_capability_slice_refs:
    - ITER-007-SLICE-001
  cross_domain_cases:
    - V-XD-001
  blocking_case_ids:
    - V-XD-001
    - V-WEB-001
    - V-ADHOC-001
  cross_domain_bindings:
    binding_001:
      case_id: V-XD-001
      accepted_capability_ref: SYS-CONTRACT-OLD
      new_slice_ref: ITER-007-SLICE-001
  first_product_web_checkpoint: V-WEB-001
  web_checkpoint_binding:
    case_id: V-WEB-001
    new_slice_ref: ITER-007-SLICE-001
    executes_cross_domain_case_id: V-XD-001
  live_ad_hoc_question_checkpoint: V-ADHOC-001
  live_ad_hoc_checkpoint_binding:
    case_id: V-ADHOC-001
    new_slice_ref: ITER-007-SLICE-001
    executes_cross_domain_case_id: V-XD-001
""",
                encoding="utf-8",
            )
            prior_acceptance = docs_gate.Document(
                repository
                / "docs/project/iterations/iteration-006/results/acceptance.md",
                {
                    "id": "ITER-006-RESULT-ACCEPTANCE",
                    "kind": "iteration-acceptance",
                    "status": "completed",
                    "iteration": "ITER-006",
                },
                "# Acceptance\n",
            )
            new_slice = docs_gate.Document(
                repository
                / "docs/project/iterations/iteration-007/development-design/SLICE-001.md",
                {
                    "id": "ITER-007-SLICE-001",
                    "kind": "development-slice",
                    "status": "proposed",
                    "iteration": "ITER-007",
                    "depends_on": [
                        "ITER-007-PROPOSAL",
                        "ITER-006-RESULT-ACCEPTANCE",
                    ],
                    "product_goal_gate": "V-000",
                    "product_goal_accepted_capability_refs": [
                        "ITER-006-RESULT-ACCEPTANCE"
                    ],
                    "product_goal_cross_domain_case_ids": ["V-XD-001"],
                    "product_goal_slice_gate_case_ids": [
                        "V-XD-001",
                        "V-WEB-001",
                        "V-ADHOC-001",
                    ],
                    "product_goal_web_checkpoint_id": "V-WEB-001",
                    "product_goal_live_ad_hoc_checkpoint_id": "V-ADHOC-001",
                },
                "# Slice\n",
            )
            verification = docs_gate.Document(
                repository
                / "docs/project/iterations/iteration-007/verification-matrix.md",
                {
                    "id": "ITER-007-VERIFICATION",
                    "kind": "iteration-verification",
                    "iteration": "ITER-007",
                },
                "| Case | Claim | Level | Frozen input / oracle | Expected | Evidence | Status / blocking meaning |\n"
                "|---|---|---|---|---|---|---|\n"
                "| V-XD-001 | combine ITER-006-RESULT-ACCEPTANCE and ITER-007-SLICE-001 | product | hidden suite | correct answer | pending | not-run / blocking |\n"
                "| V-WEB-001 | ITER-007-SLICE-001 formal Web executes V-XD-001 | product | exact UI | answer | pending | not-run / blocking |\n"
                "| V-ADHOC-001 | ITER-007-SLICE-001 live ad-hoc probes V-XD-001 | product | user question | answer | pending | not-run / blocking |\n",
            )
            by_id = {
                prior_acceptance.identifier: prior_acceptance,
                new_slice.identifier: new_slice,
            }
            manifest.write_text(
                manifest.read_text(encoding="utf-8").replace(
                    "SYS-CONTRACT-OLD", "ITER-006-RESULT-ACCEPTANCE"
                ),
                encoding="utf-8",
            )
            with patch.object(docs_gate, "REPOSITORY", repository):
                self.assertEqual(
                    docs_gate.validate_product_goal_reference_targets(
                        manifest,
                        "ITER-007",
                        by_id,
                        verification=verification,
                    ),
                    [],
                )
                prose_only_verification = docs_gate.Document(
                    verification.path,
                    verification.metadata,
                    verification.body.replace(
                        "combine ITER-006-RESULT-ACCEPTANCE and ITER-007-SLICE-001",
                        "the prose deliberately does not encode reference bindings",
                    ),
                )
                prose_errors = docs_gate.validate_product_goal_reference_targets(
                    manifest,
                    "ITER-007",
                    by_id,
                    verification=prose_only_verification,
                )
                self.assertEqual(prose_errors, [])
                readiness_errors = docs_gate.validate_product_goal_reference_targets(
                    manifest,
                    "ITER-007",
                    by_id,
                    require_execution_slice_sequence=True,
                    verification=verification,
                )
                self.assertTrue(
                    any("exactly one" in error for error in readiness_errors),
                    readiness_errors,
                )
                accepted_slice = docs_gate.Document(
                    new_slice.path,
                    {**new_slice.metadata, "status": "accepted"},
                    new_slice.body,
                )
                accepted_errors = docs_gate.validate_product_goal_reference_targets(
                    manifest,
                    "ITER-007",
                    {
                        prior_acceptance.identifier: prior_acceptance,
                        accepted_slice.identifier: accepted_slice,
                    },
                    require_execution_slice_sequence=True,
                    verification=verification,
                )
                self.assertTrue(
                    any("status is invalid" in error for error in accepted_errors),
                    accepted_errors,
                )
                wrong_authority_slice = docs_gate.Document(
                    new_slice.path,
                    {
                        **new_slice.metadata,
                        "status": "authorized",
                        "authority": "proposed-development",
                        "coding_input": "false",
                    },
                    new_slice.body,
                )
                authority_errors = docs_gate.validate_product_goal_reference_targets(
                    manifest,
                    "ITER-007",
                    {
                        prior_acceptance.identifier: prior_acceptance,
                        wrong_authority_slice.identifier: wrong_authority_slice,
                    },
                    require_execution_slice_sequence=True,
                    verification=verification,
                )
                self.assertTrue(
                    any("current-development" in error for error in authority_errors),
                    authority_errors,
                )
                accepted_future = docs_gate.Document(
                    repository
                    / "docs/project/iterations/iteration-008/results/acceptance.md",
                    {
                        "id": "ITER-008-RESULT-ACCEPTANCE",
                        "kind": "iteration-acceptance",
                        "status": "completed",
                        "iteration": "ITER-008",
                    },
                    "# Acceptance\n",
                )
                manifest.write_text(
                    manifest.read_text(encoding="utf-8").replace(
                        "ITER-006-RESULT-ACCEPTANCE",
                        "ITER-008-RESULT-ACCEPTANCE",
                    ),
                    encoding="utf-8",
                )
                future_errors = docs_gate.validate_product_goal_reference_targets(
                    manifest,
                    "ITER-007",
                    {**by_id, accepted_future.identifier: accepted_future},
                    verification=verification,
                )
                self.assertTrue(
                    any("earlier accepted iteration" in error for error in future_errors),
                    future_errors,
                )
                manifest.write_text(
                    manifest.read_text(encoding="utf-8").replace(
                        "ITER-008-RESULT-ACCEPTANCE", "isolated-new-view"
                    ),
                    encoding="utf-8",
                )
                errors = docs_gate.validate_product_goal_reference_targets(
                    manifest,
                    "ITER-007",
                    by_id,
                    verification=verification,
                )
        self.assertTrue(any("isolated-new-view" in error for error in errors), errors)

    def test_product_goal_readiness_requires_exact_user_authorization(self) -> None:
        path = (
            docs_gate.REPOSITORY
            / "docs/project/iterations/iteration-007/readiness-review.md"
        )
        valid = docs_gate.Document(
            path,
            {
                "authorized_by": "user",
                "authorized_at": "2026-08-12T12:00:00+08:00",
                "product_goal_alignment_verdict": "accepted",
                "product_goal_alignment_reviewed_by": "user",
                "product_goal_alignment_review_ref": "codex-user-message:sha256:"
                + "a" * 64,
            },
            "# Readiness\n",
        )
        self.assertEqual(
            docs_gate.validate_product_goal_readiness_authorization(valid), []
        )
        invalid = docs_gate.Document(
            path,
            {
                **valid.metadata,
                "authorized_by": "none",
                "authorized_at": "none",
            },
            valid.body,
        )
        errors = docs_gate.validate_product_goal_readiness_authorization(invalid)
        self.assertTrue(any("authorized_by" in error for error in errors), errors)
        self.assertTrue(any("authorized_at" in error for error in errors), errors)

    def test_additional_web_checkpoint_binds_the_same_slice_cross_domain_case(self) -> None:
        sequences = {
            "accepted_capability_refs": ["ITER-006-RESULT-ACCEPTANCE"],
            "new_capability_slice_refs": [
                "ITER-007-SLICE-001",
                "ITER-007-SLICE-002",
            ],
            "cross_domain_cases": ["V-XD-001", "V-XD-002"],
        }
        alignment = {
            "first_product_web_checkpoint": "V-WEB-001",
            "live_ad_hoc_question_checkpoint": "V-ADHOC-001",
            "cross_domain_bindings": {
                "first": {
                    "case_id": "V-XD-001",
                    "accepted_capability_ref": "ITER-006-RESULT-ACCEPTANCE",
                    "new_slice_ref": "ITER-007-SLICE-001",
                },
                "second": {
                    "case_id": "V-XD-002",
                    "accepted_capability_ref": "ITER-006-RESULT-ACCEPTANCE",
                    "new_slice_ref": "ITER-007-SLICE-002",
                },
            },
            "web_checkpoint_binding": {
                "case_id": "V-WEB-001",
                "new_slice_ref": "ITER-007-SLICE-001",
                "executes_cross_domain_case_id": "V-XD-001",
            },
            "live_ad_hoc_checkpoint_binding": {
                "case_id": "V-ADHOC-001",
                "new_slice_ref": "ITER-007-SLICE-002",
                "executes_cross_domain_case_id": "V-XD-002",
            },
            "additional_web_checkpoint_bindings": {
                "hardening": {
                    "case_id": "V-WEB-002",
                    "new_slice_ref": "ITER-007-SLICE-002",
                    "executes_cross_domain_case_id": "V-XD-002",
                }
            },
        }
        self.assertEqual(
            docs_gate.validate_product_goal_structured_bindings(
                alignment, sequences, "manifest.yaml"
            ),
            [],
        )
        alignment["additional_web_checkpoint_bindings"]["hardening"][  # type: ignore[index]
            "executes_cross_domain_case_id"
        ] = "V-XD-001"
        errors = docs_gate.validate_product_goal_structured_bindings(
            alignment, sequences, "manifest.yaml"
        )
        self.assertTrue(any("same slice" in error for error in errors), errors)
        alignment["additional_web_checkpoint_bindings"]["hardening"][  # type: ignore[index]
            "case_id"
        ] = "V-WEB-X"
        errors = docs_gate.validate_product_goal_structured_bindings(
            alignment, sequences, "manifest.yaml"
        )
        self.assertTrue(any("unique V-WEB" in error for error in errors), errors)


class ProductGoalSliceSequenceTests(unittest.TestCase):
    def slice_document(
        self,
        ordinal: int,
        status: str,
        *,
        depends_on_previous: bool = True,
    ) -> docs_gate.Document:
        identifier = f"ITER-007-SLICE-{ordinal:03d}"
        if status in docs_gate.ACTIVE_SLICE_STATUSES:
            authority = "current-development"
            coding_input = True
        elif status == "completed":
            authority = "historical-development"
            coding_input = False
        else:
            authority = "proposed-development"
            coding_input = False
        dependencies = ["ITER-007-PROPOSAL"]
        if ordinal > 1 and depends_on_previous:
            dependencies.append(f"ITER-007-SLICE-{ordinal - 1:03d}")
        return docs_gate.Document(
            docs_gate.REPOSITORY
            / f"docs/project/iterations/iteration-007/development-design/{identifier}.md",
            {
                "id": identifier,
                "kind": "development-slice",
                "status": status,
                "authority": authority,
                "coding_input": coding_input,
                "depends_on": dependencies,
            },
            "# Slice\n",
        )

    def validate(
        self,
        statuses: tuple[str, str, str],
        *,
        missing_dependency_at: int | None = None,
    ) -> list[str]:
        documents = [
            self.slice_document(
                index,
                status,
                depends_on_previous=index != missing_dependency_at,
            )
            for index, status in enumerate(statuses, start=1)
        ]
        refs = [document.identifier for document in documents]
        return docs_gate.validate_product_goal_slice_sequence(
            refs,
            {document.identifier: document for document in documents},
            "manifest.yaml",
        )

    def test_slice_sequence_allows_one_active_after_completed_prefix(self) -> None:
        for statuses in (
            ("authorized", "proposed", "proposed"),
            ("completed", "in-progress", "proposed"),
            ("completed", "completed", "authorized"),
        ):
            with self.subTest(statuses=statuses):
                self.assertEqual(self.validate(statuses), [])

    def test_slice_sequence_rejects_zero_multiple_or_out_of_order_active(self) -> None:
        invalid = (
            ("proposed", "proposed", "proposed"),
            ("authorized", "in-progress", "proposed"),
            ("proposed", "authorized", "proposed"),
            ("authorized", "completed", "proposed"),
        )
        for statuses in invalid:
            with self.subTest(statuses=statuses):
                self.assertTrue(self.validate(statuses))

    def test_slice_sequence_requires_direct_predecessor_dependency(self) -> None:
        errors = self.validate(
            ("completed", "authorized", "proposed"),
            missing_dependency_at=2,
        )
        self.assertTrue(any("must depend on" in error for error in errors), errors)

    def test_completed_sequence_requires_every_slice_completed(self) -> None:
        documents = [
            self.slice_document(index, "completed") for index in range(1, 4)
        ]
        refs = [document.identifier for document in documents]
        by_id = {document.identifier: document for document in documents}
        self.assertEqual(
            docs_gate.validate_product_goal_slice_sequence(
                refs, by_id, "manifest.yaml", require_completed=True
            ),
            [],
        )
        by_id[refs[-1]] = self.slice_document(3, "authorized")
        errors = docs_gate.validate_product_goal_slice_sequence(
            refs, by_id, "manifest.yaml", require_completed=True
        )
        self.assertTrue(any("every" in error for error in errors), errors)

    def test_completed_prefix_requires_slice_result_and_passed_web_gates(self) -> None:
        completed = self.slice_document(1, "completed")
        active = self.slice_document(2, "authorized")
        proposed = self.slice_document(3, "proposed")
        completed = docs_gate.Document(
            completed.path,
            {
                **completed.metadata,
                "iteration": "ITER-007",
                "product_goal_cross_domain_case_ids": ["V-XD-001"],
                "product_goal_web_checkpoint_id": "V-WEB-001",
                "product_goal_slice_gate_case_ids": ["V-XD-001", "V-WEB-001"],
            },
            completed.body,
        )
        for document in (active, proposed):
            document.metadata["iteration"] = "ITER-007"
        refs = [completed.identifier, active.identifier, proposed.identifier]
        by_id = {item.identifier: item for item in (completed, active, proposed)}
        manifest = {
            "authorization": {"active_slice": active.identifier},
            "development": {
                "slices": {
                    completed.identifier: {
                        "status": "completed",
                        "coding_input": False,
                        "result": "not-executed",
                        "product_code_freeze_digest": "sha256:" + "1" * 64,
                        "authorized_by": "user",
                        "authorized_at": "2026-08-13T11:00:00+08:00",
                        "authorization_ref": "codex-user-message:sha256:" + "b" * 64,
                    },
                    active.identifier: {
                        "status": "authorized",
                        "coding_input": True,
                        "result": "not-executed",
                        "product_code_freeze_digest": "not-executed",
                        "authorized_by": "user",
                        "authorized_at": "2026-08-13T12:00:00+08:00",
                        "authorization_ref": "codex-user-message:sha256:" + "a" * 64,
                    },
                    proposed.identifier: {
                        "status": "proposed",
                        "coding_input": False,
                        "result": "not-executed",
                        "product_code_freeze_digest": "not-executed",
                        "authorized_by": "not-authorized",
                        "authorized_at": "not-authorized",
                        "authorization_ref": "not-authorized",
                    },
                }
            }
        }
        verification = docs_gate.Document(
            docs_gate.REPOSITORY / "docs/project/iterations/iteration-007/verification-matrix.md",
            {"id": "ITER-007-VERIFICATION", "kind": "iteration-verification"},
            "| Case | Claim | Level | Frozen input / oracle | Expected | Evidence | Status / blocking meaning |\n"
            "|---|---|---|---|---|---|---|\n"
            "| V-XD-001 | cumulative | product | exact | answer | pending | not-run / blocking |\n"
            "| V-WEB-001 | web | product | exact | answer | pending | not-run / blocking |\n",
        )
        errors = docs_gate.validate_product_goal_slice_sequence(
            refs,
            by_id,
            "manifest.yaml",
            manifest=manifest,
            verification=verification,
        )
        self.assertTrue(any("must bind accepted execution evidence" in error for error in errors), errors)

        result = docs_gate.Document(
            docs_gate.REPOSITORY / "docs/project/iterations/iteration-007/results/slice-001.md",
            {
                "id": "ITER-007-RESULT-SLICE-001",
                "kind": "iteration-result",
                "status": "accepted",
                "authority": "execution-evidence",
                "iteration": "ITER-007",
                "depends_on": [completed.identifier, "ITER-007-VERIFICATION"],
                "product_code_freeze_digest": "sha256:" + "1" * 64,
            },
            "# Result\n",
        )
        by_id[result.identifier] = result
        manifest["development"]["slices"][completed.identifier]["result"] = result.identifier  # type: ignore[index]
        errors = docs_gate.validate_product_goal_slice_sequence(
            refs,
            by_id,
            "manifest.yaml",
            manifest=manifest,
            verification=verification,
        )
        self.assertTrue(any("completed V-XD-001 must" in error for error in errors), errors)
        passed_verification = docs_gate.Document(
            verification.path,
            verification.metadata,
            verification.body
            .replace("pending | not-run / blocking", f"{result.identifier}#V-XD-001 | PASS / blocking", 1)
            .replace("pending | not-run / blocking", f"{result.identifier}#V-WEB-001 | PASS / blocking", 1),
        )
        self.assertEqual(
            docs_gate.validate_product_goal_slice_sequence(
                refs,
                by_id,
                "manifest.yaml",
                manifest=manifest,
                verification=passed_verification,
            ),
            [],
        )

    def test_execution_readiness_freezes_source_contract_frontend_and_hidden_canaries(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory)
            iteration_directory = repository / "docs/project/iterations/iteration-007"
            system_directory = repository / "docs/system/contracts"

            def digest(character: str) -> str:
                return "sha256:" + character * 64

            contract_ids = [
                "SYS-CONTRACT-SEMANTICS",
                "SYS-CONTRACT-QUERY",
                "SYS-CONTRACT-ANSWER",
                "SYS-CONTRACT-UPDATE",
            ]
            contract_documents = {
                identifier: docs_gate.Document(
                    system_directory / f"{identifier.lower()}.md",
                    {
                        "id": identifier,
                        "kind": "system-contract",
                        "status": "current",
                        "authority": "normative",
                    },
                    "# Contract\n",
                )
                for identifier in contract_ids
            }
            readiness = docs_gate.Document(
                iteration_directory / "readiness-review.md",
                {
                    "id": "ITER-007-READINESS",
                    "kind": "iteration-readiness",
                    "depends_on": contract_ids,
                },
                "# Readiness\n",
            )
            first_slice = docs_gate.Document(
                iteration_directory / "development-design/SLICE-001.md",
                {
                    "id": "ITER-007-SLICE-001",
                    "kind": "development-slice",
                    "depends_on": ["ITER-007-PROPOSAL", readiness.identifier],
                    "product_goal_slice_gate_case_ids": ["V-CANARY-001"],
                },
                "# Slice\n",
            )
            second_slice = docs_gate.Document(
                iteration_directory / "development-design/SLICE-002.md",
                {
                    "id": "ITER-007-SLICE-002",
                    "kind": "development-slice",
                    "depends_on": [
                        "ITER-007-PROPOSAL",
                        readiness.identifier,
                        first_slice.identifier,
                    ],
                    "product_goal_slice_gate_case_ids": ["V-CANARY-002"],
                },
                "# Slice\n",
            )
            by_id = {
                **contract_documents,
                readiness.identifier: readiness,
                first_slice.identifier: first_slice,
                second_slice.identifier: second_slice,
            }
            verification = docs_gate.Document(
                iteration_directory / "verification-matrix.md",
                {"id": "ITER-007-VERIFICATION", "kind": "iteration-verification"},
                "| Case | Claim | Level | Frozen input / oracle | Expected | Evidence | Status / blocking meaning |\n"
                "|---|---|---|---|---|---|---|\n"
                "| V-PRE-001 | baseline | readiness | exact | accepted | baseline-result#V-PRE-001 | PASS / blocking |\n"
                "| V-UPDATE-001 | pre-question build | update | exact | built | pending | not-run / blocking |\n"
                "| V-UPDATE-002 | no-question revision | update | exact | rebuilt | pending | not-run / blocking |\n",
            )
            manifest: dict[str, object] = {
                "product_goal_alignment": {
                    "blocking_case_ids": [
                        "V-UPDATE-001",
                        "V-UPDATE-002",
                        "V-CANARY-001",
                        "V-CANARY-002",
                    ],
                    "readiness_blocking_case_ids": ["V-PRE-001"],
                    "authorized_software_sources_digest": digest("1"),
                    "visible_development_corpus_digest": digest("2"),
                    "early_hidden_canary_bindings": {
                        "slice_001": {
                            "case_id": "V-CANARY-001",
                            "new_slice_ref": "ITER-007-SLICE-001",
                            "project_manifest_digest": digest("3"),
                            "suite_digest": digest("4"),
                            "evaluation_owner": "independent-evaluator",
                            "implementation_visibility": "hidden-until-slice-code-freeze",
                            "burn_rule": "product-change-after-exposure-burns-canary-and-preserves-failure",
                        },
                        "slice_002": {
                            "case_id": "V-CANARY-002",
                            "new_slice_ref": "ITER-007-SLICE-002",
                            "project_manifest_digest": digest("5"),
                            "suite_digest": digest("6"),
                            "evaluation_owner": "independent-evaluator",
                            "implementation_visibility": "hidden-until-slice-code-freeze",
                            "burn_rule": "product-change-after-exposure-burns-canary-and-preserves-failure",
                        },
                    },
                },
                "source_scope": {
                    "provider": "LOCAL_GIT",
                    "content_kind": "java-source",
                    "contract_ref": "SYS-CONTRACT-UPDATE",
                    "authorized_software_sources_digest": digest("1"),
                    "question_or_suite_driven_update_allowed": False,
                    "verification_case_ids": ["V-UPDATE-001", "V-UPDATE-002"],
                },
                "answer_protocol": {
                    "contract_ref": "SYS-CONTRACT-ANSWER",
                    "planner_model_calls": 1,
                    "draft_model_calls": 1,
                    "independent_reviewer_model_calls": 1,
                    "deterministic_schema_grounding_and_authorization_checks": True,
                    "retries_allowed": False,
                    "exact_total_model_calls_per_question": 3,
                    "status": "frozen",
                },
                "readiness_inputs": {
                    "required_system_contract_refs": contract_ids,
                    "source_semantics_contract_ref": "SYS-CONTRACT-SEMANTICS",
                    "implementation_query_contract_ref": "SYS-CONTRACT-QUERY",
                    "no_payload_contract_ref": "SYS-CONTRACT-SEMANTICS",
                    "answer_protocol_contract_ref": "SYS-CONTRACT-ANSWER",
                    "system_contract_set_digest": digest("7"),
                    "java_frontend": {
                        "artifact_ref": "tree-sitter-java-offline",
                        "version": "1.2.3",
                        "license_ref": "MIT",
                        "offline_artifact_digest": digest("8"),
                        "canonicalization_oracle_digest": digest("9"),
                        "information_preservation_oracle_digest": digest("a"),
                        "information_boundary_oracle_digest": digest("b"),
                    },
                    "hidden_freeze_protocol_digest": digest("c"),
                },
            }
            new_refs = [
                "ITER-007-SLICE-001",
                "ITER-007-SLICE-002",
                "ITER-007-SLICE-003",
            ]
            with patch.object(docs_gate, "REPOSITORY", repository):
                self.assertEqual(
                    docs_gate.validate_product_goal_execution_readiness(
                        manifest,
                        "manifest.yaml",
                        "ITER-007",
                        by_id,
                        new_refs,
                        verification,
                    ),
                    [],
                )

                source_scope = manifest["source_scope"]
                assert isinstance(source_scope, dict)
                source_scope["question_or_suite_driven_update_allowed"] = True
                source_errors = docs_gate.validate_product_goal_execution_readiness(
                    manifest,
                    "manifest.yaml",
                    "ITER-007",
                    by_id,
                    new_refs,
                    verification,
                )
                self.assertTrue(
                    any("question_or_suite_driven" in error for error in source_errors),
                    source_errors,
                )
                source_scope["question_or_suite_driven_update_allowed"] = False

                readiness_inputs = manifest["readiness_inputs"]
                assert isinstance(readiness_inputs, dict)
                frontend = readiness_inputs["java_frontend"]
                assert isinstance(frontend, dict)
                frontend["artifact_ref"] = "pending"
                frontend_errors = docs_gate.validate_product_goal_execution_readiness(
                    manifest,
                    "manifest.yaml",
                    "ITER-007",
                    by_id,
                    new_refs,
                    verification,
                )
                self.assertTrue(
                    any("java_frontend.artifact_ref" in error for error in frontend_errors),
                    frontend_errors,
                )
                frontend["artifact_ref"] = "tree-sitter-java-offline"

                alignment = manifest["product_goal_alignment"]
                assert isinstance(alignment, dict)
                canaries = alignment["early_hidden_canary_bindings"]
                assert isinstance(canaries, dict)
                slice_001_canary = canaries["slice_001"]
                slice_002_canary = canaries["slice_002"]
                assert isinstance(slice_001_canary, dict)
                assert isinstance(slice_002_canary, dict)
                slice_001_canary["case_id"] = "V-CANARY-002"
                slice_002_canary["case_id"] = "V-CANARY-001"
                swapped_errors = docs_gate.validate_product_goal_execution_readiness(
                    manifest,
                    "manifest.yaml",
                    "ITER-007",
                    by_id,
                    new_refs,
                    verification,
                )
                self.assertTrue(
                    any("owned by its bound Slice" in error for error in swapped_errors),
                    swapped_errors,
                )

    def test_full_three_slice_final_state_aggregates_slice_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory)
            iteration_directory = (
                repository / "docs/project/iterations/iteration-007"
            )
            (iteration_directory / "development-design").mkdir(parents=True)
            (iteration_directory / "results").mkdir()
            manifest_path = iteration_directory / "manifest.yaml"

            slice_refs = [
                f"ITER-007-SLICE-{ordinal:03d}" for ordinal in range(1, 4)
            ]
            slice_result_refs = [
                f"ITER-007-RESULT-SLICE-{ordinal:03d}"
                for ordinal in range(1, 4)
            ]
            slice_case_ids = ["V-XD-001", "V-WEB-002", "V-ADHOC-001"]
            digest_fields = {
                "evaluation_project_manifest_digest": "sha256:" + "1" * 64,
                "held_out_suite_digest": "sha256:" + "2" * 64,
                "baseline_result_digest": "sha256:" + "3" * 64,
                "mature_source_agent_protocol_digest": "sha256:" + "4" * 64,
                "authorized_software_sources_digest": "sha256:" + "5" * 64,
            }
            manifest_path.write_text(
                f"""product_goal_alignment:
  new_capability_slice_refs:
    - {slice_refs[0]}
    - {slice_refs[1]}
    - {slice_refs[2]}
  blocking_case_ids:
    - {slice_case_ids[0]}
    - {slice_case_ids[1]}
    - {slice_case_ids[2]}
  early_hidden_canary_bindings:
    slice_001:
      case_id: {slice_case_ids[0]}
      new_slice_ref: {slice_refs[0]}
      project_manifest_digest: sha256:{'8' * 64}
      suite_digest: sha256:{'9' * 64}
    slice_002:
      case_id: {slice_case_ids[1]}
      new_slice_ref: {slice_refs[1]}
      project_manifest_digest: sha256:{'a' * 64}
      suite_digest: sha256:{'b' * 64}
  evaluation_project_manifest_digest: {digest_fields['evaluation_project_manifest_digest']}
  held_out_suite_digest: {digest_fields['held_out_suite_digest']}
  baseline_result_digest: {digest_fields['baseline_result_digest']}
  mature_source_agent_protocol_digest: {digest_fields['mature_source_agent_protocol_digest']}
  authorized_software_sources_digest: {digest_fields['authorized_software_sources_digest']}
  held_out_question_count: 3
  held_out_answerable_question_count: 3
  held_out_boundary_question_count: 0
  held_out_answerable_without_symbol_count_minimum: 1
  held_out_baseline_supported_count: 0
  held_out_target_supported_count: 3
  cross_domain_case_count: 3
  live_ad_hoc_question_count: 1
  live_ad_hoc_without_symbol_count_minimum: 1
development:
  slices:
    {slice_refs[0]}:
      status: completed
      coding_input: false
      result: {slice_result_refs[0]}
      product_code_freeze_digest: sha256:{'c' * 64}
      authorized_by: user
      authorized_at: 2026-08-13T10:00:00+08:00
      authorization_ref: codex-user-message:sha256:{'a' * 64}
    {slice_refs[1]}:
      status: completed
      coding_input: false
      result: {slice_result_refs[1]}
      product_code_freeze_digest: sha256:{'d' * 64}
      authorized_by: user
      authorized_at: 2026-08-13T11:00:00+08:00
      authorization_ref: codex-user-message:sha256:{'b' * 64}
    {slice_refs[2]}:
      status: completed
      coding_input: false
      result: {slice_result_refs[2]}
      product_code_freeze_digest: sha256:{'e' * 64}
      authorized_by: user
      authorized_at: 2026-08-13T12:00:00+08:00
      authorization_ref: codex-user-message:sha256:{'c' * 64}
authorization:
  active_slice: none
""",
                encoding="utf-8",
            )
            manifest = docs_gate.safe_load_manifest(
                manifest_path.read_text(encoding="utf-8")
            )

            verification = docs_gate.Document(
                iteration_directory / "verification-matrix.md",
                {
                    "id": "ITER-007-VERIFICATION",
                    "kind": "iteration-verification",
                },
                "| Case | Claim | Level | Frozen input / oracle | Expected | Evidence | Status / blocking meaning |\n"
                "|---|---|---|---|---|---|---|\n"
                + "".join(
                    f"| {case_id} | slice {ordinal} product gate | product | exact frozen input | answer | {result_ref}#{case_id} | PASS / blocking |\n"
                    for ordinal, (case_id, result_ref) in enumerate(
                        zip(slice_case_ids, slice_result_refs, strict=True), start=1
                    )
                ),
            )

            slices: list[docs_gate.Document] = []
            slice_results: list[docs_gate.Document] = []
            for index, (slice_ref, result_ref, case_id) in enumerate(
                zip(slice_refs, slice_result_refs, slice_case_ids, strict=True)
            ):
                dependencies = ["ITER-007-PROPOSAL"]
                if index > 0:
                    dependencies.append(slice_refs[index - 1])
                slice_document = docs_gate.Document(
                    iteration_directory
                    / f"development-design/{slice_ref}.md",
                    {
                        "id": slice_ref,
                        "kind": "development-slice",
                        "status": "completed",
                        "authority": "historical-development",
                        "coding_input": False,
                        "iteration": "ITER-007",
                        "depends_on": dependencies,
                        "product_goal_slice_gate_case_ids": [case_id],
                    },
                    "# Slice\n",
                )
                slice_result = docs_gate.Document(
                    iteration_directory / f"results/slice-{index + 1:03d}.md",
                    {
                        "id": result_ref,
                        "kind": "iteration-result",
                        "status": "accepted",
                        "authority": "execution-evidence",
                        "iteration": "ITER-007",
                        "depends_on": [slice_ref, verification.identifier],
                        "product_code_freeze_digest": "sha256:"
                        + "cde"[index]
                        * 64,
                        **(
                            {
                                "canary_project_manifest_digest": "sha256:"
                                + "8a"[index]
                                * 64,
                                "canary_suite_digest": "sha256:"
                                + "9b"[index]
                                * 64,
                                "canary_exposure_receipt_digest": "sha256:"
                                + "f0"[index]
                                * 64,
                                "canary_product_change_after_exposure_count": 0,
                            }
                            if index < 2
                            else {}
                        ),
                    },
                    "# Slice Result\n",
                )
                slices.append(slice_document)
                slice_results.append(slice_result)

            by_id = {
                document.identifier: document
                for document in [*slices, *slice_results]
            }
            result_metadata = {
                "id": "ITER-007-RESULT-PRODUCT-GOAL",
                "kind": "iteration-result",
                "status": "product-goal-pass",
                "authority": "execution-evidence",
                "owners": ["quality"],
                "depends_on": [
                    verification.identifier,
                    *slice_refs,
                    *slice_result_refs,
                ],
                "iteration": "ITER-007",
                **docs_gate.PRODUCT_GOAL_V000_METADATA,
                "product_goal_verdict": "PASS",
                "product_goal_subject_digest": "sha256:" + "6" * 64,
                "product_goal_report_digest": "sha256:" + "7" * 64,
                **digest_fields,
                "held_out_question_count": "3",
                "held_out_baseline_supported_count": "0",
                "held_out_actual_supported_count": "3",
                "held_out_boundary_correct_gap_count": "0",
                "held_out_answerable_without_symbol_supported_count": "1",
                "live_ad_hoc_without_symbol_pass_count": "1",
                "major_error_count": "0",
                "source_fallback_count": "0",
                "update_fallback_count": "0",
                "direct_fallback_count": "0",
                "cross_domain_pass_count": "3",
                "live_ad_hoc_pass_count": "1",
                "mature_source_agent_comparison": "non-regression",
                "product_web_manual_verification": "passed",
            }
            result_body = """# Result

## Claim and scope
three completed slices
## Exact inputs / baseline
frozen inputs
## Execution and evidence
slice-owned evidence
## Result, failures and limitations
pass
## Findings and system write-back
dispositioned
## Validity / supersession
exact subject only
"""
            result = docs_gate.Document(
                iteration_directory / "results/product-goal.md",
                result_metadata,
                result_body,
            )

            with patch.object(docs_gate, "REPOSITORY", repository):
                sequence_errors = docs_gate.validate_product_goal_slice_sequence(
                    slice_refs,
                    by_id,
                    "manifest.yaml",
                    manifest=manifest,
                    verification=verification,
                    require_completed=True,
                )
                result_errors = docs_gate.validate_product_goal_result(
                    result,
                    "ITER-007",
                    manifest_path,
                    verification,
                    by_id,
                )
                missing_dependency_result = docs_gate.Document(
                    result.path,
                    {
                        **result.metadata,
                        "depends_on": [
                            reference
                            for reference in result.metadata["depends_on"]
                            if reference != slice_result_refs[1]
                        ],
                    },
                    result.body,
                )
                missing_dependency_errors = docs_gate.validate_product_goal_result(
                    missing_dependency_result,
                    "ITER-007",
                    manifest_path,
                    verification,
                    by_id,
                )
                duplicated_manifest = docs_gate.safe_load_manifest(
                    manifest_path.read_text(encoding="utf-8")
                )
                duplicated_development = duplicated_manifest["development"]
                assert isinstance(duplicated_development, dict)
                duplicated_slices = duplicated_development["slices"]
                assert isinstance(duplicated_slices, dict)
                for slice_ref in slice_refs[1:]:
                    duplicated_slice = duplicated_slices[slice_ref]
                    assert isinstance(duplicated_slice, dict)
                    duplicated_slice["result"] = slice_result_refs[0]
                duplicate_result_errors = docs_gate.validate_product_goal_slice_sequence(
                    slice_refs,
                    by_id,
                    "manifest.yaml",
                    manifest=duplicated_manifest,
                    verification=verification,
                    require_completed=True,
                )
                changed_after_exposure = docs_gate.Document(
                    slice_results[0].path,
                    {
                        **slice_results[0].metadata,
                        "product_code_freeze_digest": "sha256:" + "0" * 64,
                    },
                    slice_results[0].body,
                )
                changed_by_id = {
                    **by_id,
                    changed_after_exposure.identifier: changed_after_exposure,
                }
                changed_after_exposure_errors = (
                    docs_gate.validate_product_goal_slice_sequence(
                        slice_refs,
                        changed_by_id,
                        "manifest.yaml",
                        manifest=manifest,
                        verification=verification,
                        require_completed=True,
                    )
                )

        self.assertEqual(sequence_errors, [])
        self.assertEqual(result_errors, [])
        self.assertTrue(
            any(
                f"must depend on {slice_result_refs[1]}" in error
                for error in missing_dependency_errors
            ),
            missing_dependency_errors,
        )
        self.assertTrue(
            any("unique Slice Result" in error for error in duplicate_result_errors),
            duplicate_result_errors,
        )
        self.assertTrue(
            any(
                "must bind its exact product code freeze" in error
                for error in changed_after_exposure_errors
            ),
            changed_after_exposure_errors,
        )


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

    def test_product_goal_alignment_sections_are_required_from_iteration_007(self) -> None:
        body = "# Proposal\n\n## Outcome and users\nreal outcome\n"
        iteration_006 = docs_gate.Document(
            docs_gate.REPOSITORY / "docs/project/iterations/iteration-006/proposal.md",
            {"kind": "iteration-proposal", "iteration": "ITER-006"},
            body,
        )
        iteration_007 = docs_gate.Document(
            docs_gate.REPOSITORY / "docs/project/iterations/iteration-007/proposal.md",
            {"kind": "iteration-proposal", "iteration": "ITER-007"},
            body,
        )

        self.assertNotIn(
            "Product-goal alignment and cumulative delta",
            docs_gate.empty_active_required_sections(iteration_006),
        )
        self.assertIn(
            "Product-goal alignment and cumulative delta",
            docs_gate.empty_active_required_sections(iteration_007),
        )

        cases = (
            ("iteration-proposal", "Product-goal alignment and cumulative delta"),
            ("iteration-readiness", "Product-goal alignment gate"),
            (
                "development-slice",
                "Product-goal contribution and cumulative integration",
            ),
        )
        for kind, section in cases:
            with self.subTest(kind=kind):
                present = docs_gate.Document(
                    docs_gate.REPOSITORY / f"docs/project/test-fixtures/{kind}.md",
                    {"kind": kind, "iteration": "ITER-007"},
                    f"# Document\n\n## {section}\nresolved evidence\n",
                )
                self.assertNotIn(
                    section, docs_gate.empty_active_required_sections(present)
                )
                missing = docs_gate.Document(
                    present.path,
                    present.metadata,
                    "# Document\n\n## Other\nresolved evidence\n",
                )
                self.assertIn(
                    section, docs_gate.empty_active_required_sections(missing)
                )

    def test_iteration_path_identity_cannot_downgrade_the_gate_version(self) -> None:
        repository = Path("/repo")
        document = docs_gate.Document(
            repository / "docs/project/iterations/iteration-007/README.md",
            {
                "id": "ITER-000-INDEX",
                "kind": "iteration-index",
                "iteration": "ITER-000",
            },
            "# Iteration\n",
        )
        with patch.object(docs_gate, "REPOSITORY", repository):
            errors = docs_gate.validate_iteration_document_identity(document)

        self.assertTrue(any("match directory ITER-007" in error for error in errors))
        self.assertTrue(any("ITER-007-INDEX" in error for error in errors))

        malformed = docs_gate.Document(
            repository / "docs/project/iterations/iteration-7/README.md",
            {
                "id": "ITER-000-INDEX",
                "kind": "iteration-index",
                "iteration": "ITER-000",
            },
            "# Iteration\n",
        )
        with patch.object(docs_gate, "REPOSITORY", repository):
            errors = docs_gate.validate_iteration_document_identity(malformed)
        self.assertTrue(any("at least three digits" in error for error in errors))

    def test_accepted_proposal_is_gated_even_before_it_becomes_current(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory)
            proposal_path = (
                repository
                / "docs/project/iterations/iteration-007/proposal.md"
            )
            proposal = docs_gate.Document(
                proposal_path,
                {
                    "id": "ITER-007-PROPOSAL",
                    "kind": "iteration-proposal",
                    "status": "accepted",
                    "iteration": "ITER-007",
                    "depends_on": ["SYS-PRODUCT-SUCCESS"],
                },
                "# Proposal\n\n## Outcome and users\nreal outcome\n",
            )
            proposed = docs_gate.Document(
                proposal.path,
                {**proposal.metadata, "status": "proposed"},
                proposal.body,
            )
            wrong_kind = docs_gate.Document(
                proposal.path,
                {**proposal.metadata, "kind": "project-note"},
                proposal.body,
            )
            with patch.object(docs_gate, "REPOSITORY", repository):
                errors = docs_gate.validate_product_goal_alignment_state([proposal])
                proposed_errors = docs_gate.validate_product_goal_alignment_state(
                    [proposed]
                )
                wrong_kind_errors = docs_gate.validate_product_goal_alignment_state(
                    [wrong_kind]
                )

        self.assertTrue(
            any(
                "Product-goal alignment and cumulative delta" in error
                for error in errors
            ),
            errors,
        )
        self.assertEqual(proposed_errors, [])
        self.assertTrue(
            any("expected kind iteration-proposal" in error for error in wrong_kind_errors),
            wrong_kind_errors,
        )

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

    def test_iteration_007_acceptance_requires_resolved_product_goal_delta(self) -> None:
        path = (
            docs_gate.REPOSITORY
            / "docs/project/iterations/iteration-007/results/acceptance.md"
        )
        metadata = {
            "id": "ITER-007-RESULT-ACCEPTANCE",
            "kind": "iteration-acceptance",
            "status": "completed",
            "iteration": "ITER-007",
            "accepted_scope": "general-source-qa-delta",
            "subject_identity": "exact-manifest-subject",
            "baseline_commit": "a" * 40,
            "baseline_relation": "exact-at-run",
            "production_activation": "not-executed",
        }

        missing = docs_gate.Document(path, metadata, self.ACCEPTANCE_BODY)
        errors = docs_gate.validate_completed_acceptance(missing)
        self.assertTrue(any("Product-goal delta" in error for error in errors))

        unresolved_body = self.ACCEPTANCE_BODY.replace(
            "## Finding dispositions and System write-back",
            "## Product-goal delta and cumulative evidence\n<exact-evidence>\n\n"
            "## Finding dispositions and System write-back",
        )
        errors = docs_gate.validate_completed_acceptance(
            docs_gate.Document(path, metadata, unresolved_body)
        )
        self.assertTrue(any("unresolved product-goal" in error for error in errors))

        resolved_body = unresolved_body.replace(
            "<exact-evidence>", "exact evidence for Map<String, Result>"
        )
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory)
            iteration_directory = (
                repository / "docs/project/iterations/iteration-007"
            )
            (iteration_directory / "results").mkdir(parents=True)
            digest_fields = {
                "evaluation_project_manifest_digest": "sha256:" + "1" * 64,
                "held_out_suite_digest": "sha256:" + "2" * 64,
                "baseline_result_digest": "sha256:" + "3" * 64,
                "mature_source_agent_protocol_digest": "sha256:" + "4" * 64,
                "authorized_software_sources_digest": "sha256:" + "5" * 64,
            }
            (iteration_directory / "manifest.yaml").write_text(
                f"""product_goal_alignment:
  accepted_capability_refs:
    - ITER-006-RESULT-ACCEPTANCE
  new_capability_slice_refs:
    - ITER-007-SLICE-001
  evaluation_project_manifest_digest: {digest_fields['evaluation_project_manifest_digest']}
  held_out_suite_digest: {digest_fields['held_out_suite_digest']}
  baseline_result_digest: {digest_fields['baseline_result_digest']}
  mature_source_agent_protocol_digest: {digest_fields['mature_source_agent_protocol_digest']}
  authorized_software_sources_digest: {digest_fields['authorized_software_sources_digest']}
  held_out_question_count: 10
  held_out_answerable_question_count: 8
  held_out_boundary_question_count: 2
  held_out_answerable_without_symbol_count_minimum: 4
  held_out_answerable_without_symbol_per_project_minimum: 2
  held_out_baseline_supported_count: 2
  held_out_target_supported_count: 8
  supported_count_denominator: answerable-only
  boundary_gap_counted_as_supported: false
  cross_domain_cases:
    - V-XD-001
  blocking_case_ids:
    - V-XD-001
    - V-WEB-001
    - V-WEB-002
    - V-ADHOC-001
  cross_domain_case_count: 1
  first_product_web_checkpoint: V-WEB-001
  additional_web_checkpoint_bindings:
    hardening:
      case_id: V-WEB-002
      new_slice_ref: ITER-007-SLICE-001
      executes_cross_domain_case_id: V-XD-001
  live_ad_hoc_question_checkpoint: V-ADHOC-001
  live_ad_hoc_question_count: 2
  live_ad_hoc_without_symbol_count_minimum: 1
development:
  slices:
    ITER-007-SLICE-001:
      status: completed
      coding_input: false
      result: ITER-007-RESULT-SLICE-001
""",
                encoding="utf-8",
            )
            pending_verification = product_goal_verification(
                iteration_directory / "verification-matrix.md",
                evidence="ITER-007-RESULT-PRODUCT-GOAL",
                status="PASS / blocking",
                result_id="ITER-007-RESULT-PRODUCT-GOAL",
            )
            verification = docs_gate.Document(
                pending_verification.path,
                pending_verification.metadata,
                pending_verification.body
                + "| V-XD-001 | cumulative answer | product | hidden case | correct answer | ITER-007-RESULT-SLICE-001#V-XD-001 | PASS / blocking |\n"
                + "| V-WEB-001 | formal Web answer | product | exact UI | visible answer | ITER-007-RESULT-SLICE-001#V-WEB-001 | PASS / blocking |\n"
                + "| V-WEB-002 | hardening Web answer | product | exact UI | visible answer | ITER-007-RESULT-SLICE-001#V-WEB-002 | PASS / blocking |\n"
                + "| V-ADHOC-001 | live user answer | product | user question | visible answer | ITER-007-RESULT-SLICE-001#V-ADHOC-001 | PASS / blocking |\n",
            )
            result_metadata = {
                "id": "ITER-007-RESULT-PRODUCT-GOAL",
                "kind": "iteration-result",
                "status": "product-goal-pass",
                "authority": "execution-evidence",
                "owners": ["quality"],
                "depends_on": [
                    "ITER-007-VERIFICATION",
                    "ITER-007-SLICE-001",
                    "ITER-007-RESULT-SLICE-001",
                ],
                "iteration": "ITER-007",
                "product_goal_gate": "V-000",
                "product_goal_outcome": "user-visible-general-source-qa-delta",
                "product_goal_evaluation": "independent-hidden-plus-live-ad-hoc",
                "product_goal_verdict": "PASS",
                "product_goal_subject_digest": "sha256:" + "6" * 64,
                "product_goal_report_digest": "sha256:" + "7" * 64,
                **digest_fields,
                "held_out_question_count": "10",
                "held_out_baseline_supported_count": "2",
                "held_out_actual_supported_count": "8",
                "held_out_boundary_correct_gap_count": "2",
                "held_out_answerable_without_symbol_supported_count": "4",
                "live_ad_hoc_without_symbol_pass_count": "1",
                "major_error_count": "0",
                "source_fallback_count": "0",
                "update_fallback_count": "0",
                "direct_fallback_count": "0",
                "cross_domain_pass_count": "1",
                "live_ad_hoc_pass_count": "2",
                "mature_source_agent_comparison": "non-regression",
                "product_web_manual_verification": "passed",
            }
            result_body = """# Result

## Claim and scope
product delta
## Exact inputs / baseline
exact inputs
## Execution and evidence
report digest
## Result, failures and limitations
pass and limitations
## Findings and system write-back
dispositioned
## Validity / supersession
current subject only
"""
            result = docs_gate.Document(
                iteration_directory / "results/product-goal.md",
                result_metadata,
                result_body,
            )
            slice_document = docs_gate.Document(
                iteration_directory / "development-design/SLICE-001.md",
                {
                    "id": "ITER-007-SLICE-001",
                    "kind": "development-slice",
                    "status": "completed",
                    "iteration": "ITER-007",
                    "product_goal_slice_gate_case_ids": [
                        "V-XD-001",
                        "V-WEB-001",
                        "V-WEB-002",
                        "V-ADHOC-001",
                    ],
                },
                "# Slice\n",
            )
            slice_result = docs_gate.Document(
                iteration_directory / "results/slice-001.md",
                {
                    "id": "ITER-007-RESULT-SLICE-001",
                    "kind": "iteration-result",
                    "status": "accepted",
                    "authority": "execution-evidence",
                    "iteration": "ITER-007",
                    "depends_on": ["ITER-007-SLICE-001", "ITER-007-VERIFICATION"],
                },
                "# Slice Result\n",
            )
            result_documents = {
                result.identifier: result,
                slice_document.identifier: slice_document,
                slice_result.identifier: slice_result,
            }
            acceptance_metadata = {
                **metadata,
                "subject_identity": result_metadata["product_goal_subject_digest"],
            }
            with patch.object(docs_gate, "REPOSITORY", repository):
                errors = docs_gate.validate_completed_acceptance(
                    docs_gate.Document(
                        iteration_directory / "results/acceptance.md",
                        acceptance_metadata,
                        resolved_body,
                    ),
                    verification,
                    result_documents,
                )
                invalid_result = docs_gate.Document(
                    iteration_directory / "outside-product-result.md",
                    {**result_metadata, "status": "failed"},
                    "# Result\n",
                )
                invalid_result_errors = docs_gate.validate_product_goal_result(
                    invalid_result,
                    "ITER-007",
                    iteration_directory / "manifest.yaml",
                    verification,
                    result_documents,
                )
                not_run_case_errors = docs_gate.validate_product_goal_result(
                    result,
                    "ITER-007",
                    iteration_directory / "manifest.yaml",
                    docs_gate.Document(
                        verification.path,
                        verification.metadata,
                        verification.body.replace(
                            "ITER-007-RESULT-SLICE-001#V-WEB-001 | PASS / blocking",
                            "pending | not-run / blocking",
                        ),
                    ),
                    result_documents,
                )
                wrong_case_evidence_errors = docs_gate.validate_product_goal_result(
                    result,
                    "ITER-007",
                    iteration_directory / "manifest.yaml",
                    docs_gate.Document(
                        verification.path,
                        verification.metadata,
                        verification.body.replace(
                            "ITER-007-RESULT-SLICE-001#V-ADHOC-001",
                            "ITER-007-RESULT-SLICE-001#V-XD-001",
                        ),
                    ),
                    result_documents,
                )
                not_run_additional_web_errors = docs_gate.validate_product_goal_result(
                    result,
                    "ITER-007",
                    iteration_directory / "manifest.yaml",
                    docs_gate.Document(
                        verification.path,
                        verification.metadata,
                        verification.body.replace(
                            "ITER-007-RESULT-SLICE-001#V-WEB-002 | PASS / blocking",
                            "pending | not-run / blocking",
                        ),
                    ),
                    result_documents,
                )
        self.assertEqual(errors, [])
        self.assertTrue(
            any("results directory" in error for error in invalid_result_errors),
            invalid_result_errors,
        )
        self.assertTrue(
            any("status must be product-goal-pass" in error for error in invalid_result_errors),
            invalid_result_errors,
        )
        self.assertTrue(
            any("section is missing" in error for error in invalid_result_errors),
            invalid_result_errors,
        )
        self.assertTrue(
            any("completed V-WEB-001 must bind resolved evidence" in error for error in not_run_case_errors),
            not_run_case_errors,
        )
        self.assertTrue(
            any("completed V-WEB-001 must be PASS" in error for error in not_run_case_errors),
            not_run_case_errors,
        )
        self.assertTrue(
            any("completed V-ADHOC-001 Evidence must equal" in error for error in wrong_case_evidence_errors),
            wrong_case_evidence_errors,
        )
        self.assertTrue(
            any("completed V-WEB-002 must bind resolved evidence" in error for error in not_run_additional_web_errors),
            not_run_additional_web_errors,
        )
        self.assertTrue(
            any("completed V-WEB-002 must be PASS" in error for error in not_run_additional_web_errors),
            not_run_additional_web_errors,
        )


if __name__ == "__main__":
    unittest.main()
