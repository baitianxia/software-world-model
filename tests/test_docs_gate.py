from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import re
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


def reflection_report_digest(body: str) -> str:
    section = docs_gate.markdown_section_body(
        docs_gate.Document(SCRIPT, {}, body),
        "Architecture reflection and continuation decision",
    )
    assert section is not None
    return "sha256:" + hashlib.sha256(section.encode("utf-8")).hexdigest()


def positive_value_report_section(
    metadata: dict[str, object], result_id: str, case_id: str
) -> tuple[str, str]:
    report = {
        "schema": "software-world-model-positive-value-report/v1",
        "result_id": result_id,
        "verification_case_id": case_id,
        "metric": metadata["positive_value_metric"],
        "unit": metadata["positive_value_unit"],
        "comparison": metadata["positive_value_comparison"],
        "threshold": metadata["positive_value_threshold"],
        "actual": metadata["positive_value_actual"],
        "reuse_horizon_questions": metadata[
            "positive_value_reuse_horizon_questions"
        ],
        "mature_source_agent_protocol_digest": metadata[
            "mature_source_agent_protocol_digest"
        ],
        "mature_source_agent_rubric_digest": metadata[
            "mature_source_agent_rubric_digest"
        ],
        "mature_source_agent_cache_policy_digest": metadata[
            "mature_source_agent_cache_policy_digest"
        ],
        "positive_value_protocol_digest": metadata[
            "positive_value_protocol_digest"
        ],
        "freeze_receipt_ref": metadata["positive_value_freeze_receipt_ref"],
        "adjudication_owner": metadata["positive_value_adjudication_owner"],
        "adjudication_receipt_ref": metadata[
            "positive_value_adjudication_receipt_ref"
        ],
        "measurement_input_digest": "sha256:" + "9" * 64,
    }
    body = "## Positive value report\n\n" + json.dumps(
        report, ensure_ascii=False, indent=2, sort_keys=True
    )
    section = docs_gate.markdown_section_body(
        docs_gate.Document(SCRIPT, {}, body), "Positive value report"
    )
    assert section is not None
    digest = "sha256:" + hashlib.sha256(section.encode("utf-8")).hexdigest()
    return body, digest


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
    def test_execution_readiness_resolves_safe_yaml_block_sequences(self) -> None:
        text = """\
product_goal_alignment:
  blocking_case_ids:
    - V-001
    - V-002
  readiness_blocking_case_ids:
    - V-PRE-001
source_scope:
  verification_case_ids:
    - V-001
readiness_inputs:
  required_system_contract_refs:
    - SYS-CONTRACT-A
    - SYS-CONTRACT-B
  system_contract_set_paths:
    - docs/system/a.md
    - docs/system/b.md
"""
        manifest = docs_gate.safe_load_manifest(text)

        cases = (
            ("product_goal_alignment", "blocking_case_ids", ["V-001", "V-002"]),
            ("product_goal_alignment", "readiness_blocking_case_ids", ["V-PRE-001"]),
            ("source_scope", "verification_case_ids", ["V-001"]),
            (
                "readiness_inputs",
                "required_system_contract_refs",
                ["SYS-CONTRACT-A", "SYS-CONTRACT-B"],
            ),
            (
                "readiness_inputs",
                "system_contract_set_paths",
                ["docs/system/a.md", "docs/system/b.md"],
            ),
        )
        for section, field, expected in cases:
            with self.subTest(section=section, field=field):
                self.assertEqual(
                    docs_gate._execution_manifest_sequence(
                        manifest=manifest,
                        manifest_text=text,
                        section=section,
                        field=field,
                    ),
                    expected,
                )

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
  capability_path_ref: ROADMAP-M-002
  capability_path_step: step-1-general-source-qa
  predecessor_result_refs:
    - ITER-006-RESULT-ACCEPTANCE
  end_of_iteration_web_capability: free-source-questions-from-prebuilt-world-model
  next_blocking_gap: real-project-breadth
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

        duplicated_cross_domain = valid.replace(
            "  cross_domain_cases:\n    - V-XD-001\n",
            "  cross_domain_cases:\n    - V-XD-001\n    - V-XD-001\n",
        ).replace("  cross_domain_case_count: 1", "  cross_domain_case_count: 2")
        duplicated_cross_domain_errors = self.validate(
            duplicated_cross_domain, "ITER-007"
        )
        self.assertTrue(
            any(
                "cross_domain_cases must not contain duplicate items" in error
                for error in duplicated_cross_domain_errors
            ),
            duplicated_cross_domain_errors,
        )

        user_held_live = valid.replace(
            "  held_out_free_question_delta:",
            "  evaluation_input_mode: user-held-live-after-product-code-freeze\n"
            "  held_out_free_question_delta:",
        ).replace(
            "held_out_evaluation_owner: independent-evaluator",
            "held_out_evaluation_owner: user",
        )
        for field in docs_gate.PRODUCT_GOAL_ALIGNMENT_MANIFEST_DIGESTS:
            user_held_live = re.sub(
                rf"({field}: )sha256:[0-9a-f]{{64}}",
                rf"\1{docs_gate.USER_HELD_LIVE_UNDISCLOSED}",
                user_held_live,
            )
        user_held_live = user_held_live.replace(
            "held_out_baseline_supported_count: 2",
            "held_out_baseline_supported_count: measured-after-product-code-freeze",
        ).replace(
            "held_out_target_supported_count: 8",
            "held_out_target_supported_count: measured-after-product-code-freeze",
        )
        self.assertEqual(self.validate(user_held_live, "ITER-007"), [])
        wrong_live_owner = user_held_live.replace(
            "held_out_evaluation_owner: user",
            "held_out_evaluation_owner: independent-evaluator",
        )
        self.assertTrue(
            any(
                "user-held live evaluation" in error
                for error in self.validate(wrong_live_owner, "ITER-007")
            )
        )
        unknown_live_marker = user_held_live.replace(
            docs_gate.USER_HELD_LIVE_UNDISCLOSED,
            "unknown-unfrozen-input",
            1,
        )
        self.assertTrue(
            any(
                "closed user-held undisclosed marker" in error
                for error in self.validate(unknown_live_marker, "ITER-007")
            )
        )

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
                    "capability_path_step: step-1-general-source-qa",
                    "capability_path_step: pending",
                ),
                "capability_path_step",
            ),
            (
                valid.replace(
                    "predecessor_result_refs:\n    - ITER-006-RESULT-ACCEPTANCE",
                    "predecessor_result_refs: []",
                ),
                "predecessor_result_refs",
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
        metadata = {**document.metadata, "iteration": "ITER-008"}
        verification = docs_gate.Document(path, metadata, document.body)
        self.assertEqual(
            docs_gate.validate_product_goal_v000(verification, "ITER-008"), []
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

        rejected_verification = product_goal_verification(
            path,
            evidence="ITER-007-RESULT-SLICE-001-FAILED",
            status="FAIL / blocking",
            result_id="ITER-007-RESULT-SLICE-001-FAILED",
        )
        self.assertEqual(
            docs_gate.validate_product_goal_v000(
                rejected_verification,
                "ITER-007",
                require_pass=False,
                by_id={},
            ),
            [],
        )

    def test_manifest_alignment_accepts_safe_yaml_key_whitespace(self) -> None:
        content = f"""iteration:
  id: ITER-007
  status: authorized
baseline:
  commit: {self.COMMIT}
product_goal_alignment :
  target_ref: SYS-PRODUCT-SUCCESS
  capability_path_ref: ROADMAP-M-002
  capability_path_step: step-1-general-source-qa
  predecessor_result_refs:
    - ITER-006-RESULT-ACCEPTANCE
  end_of_iteration_web_capability: free-source-questions-from-prebuilt-world-model
  next_blocking_gap: real-project-breadth
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
  capability_path_ref: ROADMAP-M-002
  capability_path_step: step-1-test
  predecessor_result_refs:
    - SYS-CONTRACT-OLD
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
            capability_path = docs_gate.Document(
                repository / "docs/project/roadmap/milestones/M-002.md",
                {
                    "id": "ROADMAP-M-002",
                    "kind": "roadmap-milestone",
                    "status": "planned",
                    "authority": "planning-only",
                },
                "# Capability Path\n\n"
                "| Step ID | Capability |\n"
                "|---|---|\n"
                "| `step-1-test` | test capability |\n",
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
                capability_path.identifier: capability_path,
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
                manifest.write_text(
                    manifest.read_text(encoding="utf-8").replace(
                        "capability_path_step: step-1-test",
                        "capability_path_step: step-9-unknown",
                    ),
                    encoding="utf-8",
                )
                unknown_step_errors = (
                    docs_gate.validate_product_goal_reference_targets(
                        manifest,
                        "ITER-007",
                        by_id,
                        verification=verification,
                    )
                )
                self.assertTrue(
                    any("registered Step ID" in error for error in unknown_step_errors),
                    unknown_step_errors,
                )
                manifest.write_text(
                    manifest.read_text(encoding="utf-8").replace(
                        "capability_path_step: step-9-unknown",
                        "capability_path_step: step-1-test",
                    ),
                    encoding="utf-8",
                )
                rejected_prior_index = docs_gate.Document(
                    repository
                    / "docs/project/iterations/iteration-006/README.md",
                    {
                        "id": "ITER-006-INDEX",
                        "kind": "iteration-index",
                        "status": "rejected",
                        "iteration": "ITER-006",
                    },
                    "# Rejected iteration\n",
                )
                rejected_reference_errors = (
                    docs_gate.validate_product_goal_reference_targets(
                        manifest,
                        "ITER-007",
                        {
                            **by_id,
                            rejected_prior_index.identifier: rejected_prior_index,
                        },
                        verification=verification,
                    )
                )
                self.assertTrue(
                    any(
                        "earlier accepted iteration" in error
                        for error in rejected_reference_errors
                    ),
                    rejected_reference_errors,
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
        elif status == "blocked":
            authority = "development-evidence"
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

    def test_rejected_sequence_requires_one_preserved_blocked_slice(self) -> None:
        blocked = self.slice_document(1, "blocked")
        proposed = [
            self.slice_document(index, "proposed") for index in range(2, 4)
        ]
        for document in (blocked, *proposed):
            document.metadata["iteration"] = "ITER-007"
        freeze_digest = "sha256:" + "7" * 64
        result = docs_gate.Document(
            docs_gate.REPOSITORY
            / "docs/project/iterations/iteration-007/results/slice-001-failed.md",
            {
                "id": "ITER-007-RESULT-SLICE-001-FAILED",
                "kind": "iteration-result",
                "status": "failed-preserved",
                "authority": "execution-evidence",
                "iteration": "ITER-007",
                "depends_on": [blocked.identifier, "ITER-007-VERIFICATION"],
                "product_code_freeze_digest": freeze_digest,
            },
            "# Failed Result\n",
        )
        slices = [blocked, *proposed]
        refs = [document.identifier for document in slices]
        by_id = {
            document.identifier: document for document in [*slices, result]
        }
        manifest = {
            "authorization": {"active_slice": "none"},
            "development": {
                "slices": {
                    blocked.identifier: {
                        "status": "blocked",
                        "coding_input": False,
                        "result": result.identifier,
                        "product_code_freeze_digest": freeze_digest,
                        "authorized_by": "user",
                        "authorized_at": "2026-08-14T10:00:00+08:00",
                        "authorization_ref": "codex-user-message:sha256:"
                        + "a" * 64,
                    },
                    **{
                        document.identifier: {
                            "status": "proposed",
                            "coding_input": False,
                            "result": "not-executed",
                            "product_code_freeze_digest": "not-executed",
                            "authorized_by": "not-authorized",
                            "authorized_at": "not-authorized",
                            "authorization_ref": "not-authorized",
                        }
                        for document in proposed
                    },
                }
            },
        }

        self.assertEqual(
            docs_gate.validate_product_goal_slice_sequence(
                refs,
                by_id,
                "manifest.yaml",
                manifest=manifest,
                require_rejected=True,
            ),
            [],
        )

        result.metadata["status"] = "accepted"
        errors = docs_gate.validate_product_goal_slice_sequence(
            refs,
            by_id,
            "manifest.yaml",
            manifest=manifest,
            require_rejected=True,
        )
        self.assertTrue(any("failed-preserved" in error for error in errors), errors)
        result.metadata["status"] = "failed-preserved"

        result.metadata["product_code_freeze_digest"] = "sha256:" + "8" * 64
        errors = docs_gate.validate_product_goal_slice_sequence(
            refs,
            by_id,
            "manifest.yaml",
            manifest=manifest,
            require_rejected=True,
        )
        self.assertTrue(any("exact product code freeze" in error for error in errors), errors)
        result.metadata["product_code_freeze_digest"] = freeze_digest

        authorization = manifest["authorization"]
        assert isinstance(authorization, dict)
        authorization["active_slice"] = blocked.identifier
        errors = docs_gate.validate_product_goal_slice_sequence(
            refs,
            by_id,
            "manifest.yaml",
            manifest=manifest,
            require_rejected=True,
        )
        self.assertTrue(any("active_slice" in error for error in errors), errors)

    def test_rejected_sequence_rejects_wrong_order_or_coding_input(self) -> None:
        invalid_sequences = (
            ("proposed", "blocked", "proposed"),
            ("blocked", "completed", "proposed"),
            ("proposed", "proposed", "proposed"),
            ("blocked", "blocked", "proposed"),
        )
        for statuses in invalid_sequences:
            with self.subTest(statuses=statuses):
                documents = [
                    self.slice_document(index, status)
                    for index, status in enumerate(statuses, start=1)
                ]
                refs = [document.identifier for document in documents]
                errors = docs_gate.validate_product_goal_slice_sequence(
                    refs,
                    {
                        document.identifier: document for document in documents
                    },
                    "manifest.yaml",
                    require_rejected=True,
                )
                self.assertTrue(errors)

        blocked = self.slice_document(1, "blocked")
        blocked.metadata["coding_input"] = True
        blocked.metadata["authority"] = "current-development"
        proposed = [self.slice_document(index, "proposed") for index in range(2, 4)]
        errors = docs_gate.validate_product_goal_slice_sequence(
            [blocked.identifier, *(document.identifier for document in proposed)],
            {
                document.identifier: document
                for document in [blocked, *proposed]
            },
            "manifest.yaml",
            require_rejected=True,
        )
        self.assertTrue(any("coding_input false" in error for error in errors), errors)

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
            system_directory.mkdir(parents=True)

            hidden_directory = (
                repository
                / "validation/structure_world_model_iteration_007"
            )
            hidden_directory.mkdir(parents=True)
            hidden_component_paths = tuple(
                hidden_directory / name
                for name in (
                    "hidden_freeze_protocol.json",
                    "hidden_freeze.py",
                    "hidden_freeze_lifecycle.py",
                )
            )
            for ordinal, path in enumerate(hidden_component_paths):
                path.write_text(f"public component {ordinal}\n", encoding="utf-8")
            hidden_protocol_digest = docs_gate.canonical_raw_component_set_digest(
                hidden_component_paths
            )

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
            for document in contract_documents.values():
                document.path.write_text("# Contract\n", encoding="utf-8")
            contract_set_paths = sorted(
                document.path.relative_to(repository).as_posix()
                for document in contract_documents.values()
            )
            contract_set_schema = "ITER-007-SYSTEM-CONTRACT-SET@1"
            contract_set_digest = docs_gate.canonical_fileset_digest(
                contract_set_schema,
                contract_set_paths,
                repository=repository,
            )
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
                            "burn_rule": (
                                "product-change-between-disclosure-and-slice-result-seal-"
                                "burns-canary-and-preserves-result"
                            ),
                        },
                        "slice_002": {
                            "case_id": "V-CANARY-002",
                            "new_slice_ref": "ITER-007-SLICE-002",
                            "project_manifest_digest": digest("5"),
                            "suite_digest": digest("6"),
                            "evaluation_owner": "independent-evaluator",
                            "implementation_visibility": "hidden-until-slice-code-freeze",
                            "burn_rule": (
                                "product-change-between-disclosure-and-slice-result-seal-"
                                "burns-canary-and-preserves-result"
                            ),
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
                    "system_contract_set_schema": contract_set_schema,
                    "system_contract_set_paths": contract_set_paths,
                    "system_contract_set_digest": contract_set_digest,
                    "java_frontend": {
                        "artifact_ref": "tree-sitter-java-offline",
                        "version": "1.2.3",
                        "runtime_version": "tree-sitter==1.2.3",
                        "grammar_version": "tree-sitter-java==1.2.3",
                        "language_abi": 14,
                        "license_ref": "MIT",
                        "runtime_license_digest": digest("7"),
                        "grammar_license_digest": digest("8"),
                        "runtime_fileset_digest": digest("9"),
                        "grammar_fileset_digest": digest("a"),
                        "offline_artifact_digest": digest("8"),
                        "canonicalization_oracle_digest": digest("9"),
                        "information_preservation_oracle_digest": digest("a"),
                        "information_boundary_oracle_digest": digest("b"),
                        "legacy_calls_consistency_oracle_digest": digest("c"),
                        "readiness_oracle_result_digest": digest("d"),
                        "readiness_oracle_result_path": (
                            "var/iteration-007/readiness/oracle-result.json"
                        ),
                    },
                    "hidden_freeze_protocol_digest": hidden_protocol_digest,
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

                original_contract_digest = readiness_inputs[
                    "system_contract_set_digest"
                ]
                readiness_inputs["system_contract_set_digest"] = digest("f")
                contract_digest_errors = (
                    docs_gate.validate_product_goal_execution_readiness(
                        manifest,
                        "manifest.yaml",
                        "ITER-007",
                        by_id,
                        new_refs,
                        verification,
                    )
                )
                self.assertTrue(
                    any(
                        "system_contract_set_digest does not match"
                        in error
                        for error in contract_digest_errors
                    ),
                    contract_digest_errors,
                )
                readiness_inputs["system_contract_set_digest"] = (
                    original_contract_digest
                )

                original_contract_paths = list(
                    readiness_inputs["system_contract_set_paths"]
                )
                readiness_inputs["system_contract_set_paths"] = list(
                    reversed(original_contract_paths)
                )
                contract_order_errors = (
                    docs_gate.validate_product_goal_execution_readiness(
                        manifest,
                        "manifest.yaml",
                        "ITER-007",
                        by_id,
                        new_refs,
                        verification,
                    )
                )
                self.assertTrue(
                    any("canonical lexical order" in error for error in contract_order_errors),
                    contract_order_errors,
                )
                readiness_inputs["system_contract_set_paths"] = (
                    original_contract_paths
                )

                readiness_inputs["system_contract_set_paths"] = (
                    original_contract_paths + [original_contract_paths[-1]]
                )
                duplicate_path_errors = (
                    docs_gate.validate_product_goal_execution_readiness(
                        manifest,
                        "manifest.yaml",
                        "ITER-007",
                        by_id,
                        new_refs,
                        verification,
                    )
                )
                self.assertTrue(
                    any("system_contract_set_paths must be unique" in error for error in duplicate_path_errors),
                    duplicate_path_errors,
                )

                outside_path = repository / "README.md"
                outside_path.write_text("outside system\n", encoding="utf-8")
                readiness_inputs["system_contract_set_paths"] = sorted(
                    original_contract_paths + ["README.md"]
                )
                outside_path_errors = (
                    docs_gate.validate_product_goal_execution_readiness(
                        manifest,
                        "manifest.yaml",
                        "ITER-007",
                        by_id,
                        new_refs,
                        verification,
                    )
                )
                self.assertTrue(
                    any("system Contract set path is invalid" in error for error in outside_path_errors),
                    outside_path_errors,
                )

                missing_contract_paths = original_contract_paths[1:]
                readiness_inputs["system_contract_set_paths"] = (
                    missing_contract_paths
                )
                readiness_inputs["system_contract_set_digest"] = (
                    docs_gate.canonical_fileset_digest(
                        contract_set_schema,
                        missing_contract_paths,
                        repository=repository,
                    )
                )
                missing_contract_errors = (
                    docs_gate.validate_product_goal_execution_readiness(
                        manifest,
                        "manifest.yaml",
                        "ITER-007",
                        by_id,
                        new_refs,
                        verification,
                    )
                )
                self.assertTrue(
                    any("required Contract is absent" in error for error in missing_contract_errors),
                    missing_contract_errors,
                )
                readiness_inputs["system_contract_set_paths"] = (
                    original_contract_paths
                )
                readiness_inputs["system_contract_set_digest"] = (
                    original_contract_digest
                )

                alignment = manifest["product_goal_alignment"]
                assert isinstance(alignment, dict)
                canaries = alignment["early_hidden_canary_bindings"]
                assert isinstance(canaries, dict)
                slice_001_canary = canaries["slice_001"]
                slice_002_canary = canaries["slice_002"]
                assert isinstance(slice_001_canary, dict)
                assert isinstance(slice_002_canary, dict)

                alignment["evaluation_input_mode"] = (
                    docs_gate.USER_HELD_LIVE_EVALUATION_MODE
                )
                alignment["held_out_evaluation_owner"] = "user"
                alignment["authorized_software_sources_digest"] = (
                    docs_gate.USER_HELD_LIVE_UNDISCLOSED
                )
                source_scope["authorized_software_sources_digest"] = (
                    docs_gate.USER_HELD_LIVE_UNDISCLOSED
                )
                for canary in (slice_001_canary, slice_002_canary):
                    canary["evaluation_owner"] = "user"
                    canary["project_manifest_digest"] = (
                        docs_gate.USER_HELD_LIVE_UNDISCLOSED
                    )
                    canary["suite_digest"] = docs_gate.USER_HELD_LIVE_UNDISCLOSED
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
                slice_001_canary["suite_digest"] = "pending"
                live_marker_errors = (
                    docs_gate.validate_product_goal_execution_readiness(
                        manifest,
                        "manifest.yaml",
                        "ITER-007",
                        by_id,
                        new_refs,
                        verification,
                    )
                )
                self.assertTrue(
                    any(
                        "closed user-held undisclosed marker" in error
                        for error in live_marker_errors
                    ),
                    live_marker_errors,
                )
                slice_001_canary["suite_digest"] = (
                    docs_gate.USER_HELD_LIVE_UNDISCLOSED
                )
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
                                "canary_disclosure_receipt_digest": "sha256:"
                                + "f0"[index]
                                * 64,
                                "canary_product_change_before_result_seal_count": 0,
                                "canary_capsule_consumption_status": (
                                    "CONSUMED_AFTER_RESULT_SEAL"
                                ),
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
                overstated_count_result = docs_gate.Document(
                    result.path,
                    {
                        **result.metadata,
                        "cross_domain_pass_count": "999",
                        "live_ad_hoc_pass_count": "999",
                    },
                    result.body,
                )
                overstated_count_errors = docs_gate.validate_product_goal_result(
                    overstated_count_result,
                    "ITER-007",
                    iteration_directory / "manifest.yaml",
                    verification,
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
        self.assertTrue(
            any(
                "cross_domain_pass_count must equal the frozen Manifest count" in error
                for error in overstated_count_errors
            ),
            overstated_count_errors,
        )
        self.assertTrue(
            any(
                "live_ad_hoc_pass_count must equal the frozen Manifest count" in error
                for error in overstated_count_errors
            ),
            overstated_count_errors,
        )


class ReflectionGateTests(unittest.TestCase):
    def valid_alignment(self) -> tuple[dict[str, object], list[str], list[str]]:
        new_refs = ["ITER-008-SLICE-001", "ITER-008-SLICE-002"]
        blocking = ["V-REFLECT-001", "V-REFLECT-002", "V-NEG-EARLY-001"]
        alignment: dict[str, object] = {
            "critical_assumption_ids": ["A1", "A2"],
            "reflection_gate_bindings": {
                "slice_001": {
                    "case_id": "V-REFLECT-001",
                    "new_slice_ref": new_refs[0],
                    "assumption_ids": ["A1"],
                    "conditional_falsifier_bindings": {
                        "deferred_a2": {
                            "assumption_id": "A2",
                            "case_id": "V-NEG-EARLY-001",
                        }
                    },
                    "success_decision": "CONTINUE",
                    "decision_owner": "product-architecture-quality",
                    "required_before_next_authorization_or_acceptance": True,
                },
                "slice_002": {
                    "case_id": "V-REFLECT-002",
                    "new_slice_ref": new_refs[1],
                    "assumption_ids": ["A1", "A2"],
                    "success_decision": "ACCEPT",
                    "decision_owner": "product-architecture-quality",
                    "required_before_next_authorization_or_acceptance": True,
                },
            }
        }
        return alignment, new_refs, blocking

    def test_iter008_answer_protocol_uses_bounded_variable_investigation(
        self,
    ) -> None:
        protocol: dict[str, object] = {
            "mode": "bounded-result-driven-world-model-investigation",
            "max_investigation_steps": 6,
            "max_investigation_model_calls": 4,
            "planner_model_call_upper_bound": 4,
            "max_query_bytes_per_step": 2048,
            "max_result_bytes_per_step": 8192,
            "max_total_query_bytes_per_question": 12288,
            "max_total_result_bytes_per_question": 49152,
            "max_wall_time_milliseconds_per_question": 30000,
            "max_support_items_per_question": 64,
            "max_trace_bytes_per_question": 131072,
            "budget_exhaustion_behavior": "fail-closed-with-explicit-limitation",
            "draft_model_calls": 1,
            "independent_reviewer_model_calls": 1,
            "deterministic_schema_grounding_and_authorization_checks": True,
            "retries_allowed": False,
            "total_model_call_upper_bound_per_question": 6,
            "status": "frozen",
        }
        self.assertEqual(
            docs_gate.validate_answer_protocol_execution_readiness(
                protocol, "manifest.yaml", "ITER-008"
            ),
            [],
        )

        legacy = {
            **protocol,
            "planner_model_calls": 1,
            "exact_total_model_calls_per_question": 3,
        }
        legacy_errors = docs_gate.validate_answer_protocol_execution_readiness(
            legacy, "manifest.yaml", "ITER-008"
        )
        self.assertTrue(
            any("legacy fixed-call" in error for error in legacy_errors),
            legacy_errors,
        )

        wrong_total = {
            **protocol,
            "total_model_call_upper_bound_per_question": 5,
        }
        total_errors = docs_gate.validate_answer_protocol_execution_readiness(
            wrong_total, "manifest.yaml", "ITER-008"
        )
        self.assertTrue(
            any("plus one Draft" in error for error in total_errors), total_errors
        )

        not_result_driven = {
            **protocol,
            "max_investigation_steps": 1,
            "max_investigation_model_calls": 1,
            "planner_model_call_upper_bound": 1,
            "total_model_call_upper_bound_per_question": 3,
        }
        result_driven_errors = (
            docs_gate.validate_answer_protocol_execution_readiness(
                not_result_driven, "manifest.yaml", "ITER-008"
            )
        )
        self.assertTrue(
            any("must be at least 2" in error for error in result_driven_errors),
            result_driven_errors,
        )

        missing_trace_bound = dict(protocol)
        del missing_trace_bound["max_trace_bytes_per_question"]
        trace_errors = docs_gate.validate_answer_protocol_execution_readiness(
            missing_trace_bound, "manifest.yaml", "ITER-008"
        )
        self.assertTrue(
            any("max_trace_bytes_per_question" in error for error in trace_errors),
            trace_errors,
        )

    def test_positive_value_is_frozen_and_measured_not_self_reported(self) -> None:
        alignment: dict[str, object] = {
            "positive_value_metric": "normalized-reuse-cost",
            "positive_value_unit": "basis-points",
            "positive_value_comparison": "at-most",
            "positive_value_threshold": 8000,
            "positive_value_reuse_horizon_questions": 3,
            "mature_source_agent_protocol_digest": "sha256:" + "1" * 64,
            "mature_source_agent_rubric_digest": "sha256:" + "2" * 64,
            "mature_source_agent_cache_policy_digest": "sha256:" + "3" * 64,
            "positive_value_protocol_digest": "sha256:" + "4" * 64,
            "positive_value_freeze_receipt_ref": (
                "codex-user-message:sha256:" + "5" * 64
            ),
            "positive_value_adjudication_owner": "user",
        }
        self.assertEqual(
            docs_gate.validate_positive_value_execution_readiness(
                alignment, "manifest.yaml"
            ),
            [],
        )
        result_id = "ITER-008-RESULT-PRODUCT"
        value_metadata = {
            "id": result_id,
            "iteration": "ITER-008",
            "positive_value_verdict": "PASS",
            "positive_value_actual": 7500,
            "positive_value_case_id": "V-000",
            "positive_value_report_ref": f"{result_id}#positive-value-report",
            "positive_value_adjudication_receipt_ref": (
                "codex-user-message:sha256:" + "6" * 64
            ),
            **{
                field: alignment[field]
                for field in (
                    "positive_value_metric",
                    "positive_value_unit",
                    "positive_value_comparison",
                    "positive_value_threshold",
                    "positive_value_reuse_horizon_questions",
                    "mature_source_agent_protocol_digest",
                    "mature_source_agent_rubric_digest",
                    "mature_source_agent_cache_policy_digest",
                    "positive_value_protocol_digest",
                    "positive_value_freeze_receipt_ref",
                    "positive_value_adjudication_owner",
                )
            },
        }
        value_report_body, value_report_digest = positive_value_report_section(
            value_metadata, result_id, "V-000"
        )
        result = docs_gate.Document(
            docs_gate.REPOSITORY
            / "docs/project/iterations/iteration-008/results/product.md",
            {
                **value_metadata,
                "positive_value_report_digest": value_report_digest,
            },
            "# Result\n\n" + value_report_body,
        )
        self.assertEqual(
            docs_gate.validate_positive_value_result(
                result, alignment, "product.md", expected_case_id="V-000"
            ),
            [],
        )

        missed_threshold = docs_gate.Document(
            result.path,
            {**result.metadata, "positive_value_actual": 8001},
            result.body,
        )
        threshold_errors = docs_gate.validate_positive_value_result(
            missed_threshold,
            alignment,
            "product.md",
            expected_case_id="V-000",
        )
        self.assertTrue(
            any("does not satisfy" in error for error in threshold_errors),
            threshold_errors,
        )

        failed_value_metadata = {
            **value_metadata,
            "positive_value_verdict": "FAIL",
            "positive_value_actual": 8001,
        }
        failed_report_body, failed_report_digest = positive_value_report_section(
            failed_value_metadata, result_id, "V-000"
        )
        failed_value_result = docs_gate.Document(
            result.path,
            {
                **failed_value_metadata,
                "positive_value_report_digest": failed_report_digest,
            },
            "# Result\n\n" + failed_report_body,
        )
        self.assertEqual(
            docs_gate.validate_positive_value_result(
                failed_value_result,
                alignment,
                "product.md",
                require_pass=False,
                expected_case_id="V-000",
            ),
            [],
        )

        forged_digest = docs_gate.Document(
            result.path,
            {
                **result.metadata,
                "positive_value_report_digest": "sha256:" + "f" * 64,
            },
            result.body,
        )
        forged_errors = docs_gate.validate_positive_value_result(
            forged_digest,
            alignment,
            "product.md",
            expected_case_id="V-000",
        )
        self.assertTrue(
            any("exact Positive value report section" in error for error in forged_errors),
            forged_errors,
        )

        duplicate_report_result = docs_gate.Document(
            result.path,
            result.metadata,
            result.body
            + "\n## Positive value report\n\n"
            + '{"actual": 0, "adjudication_receipt_ref": "attacker"}\n',
        )
        duplicate_report_errors = docs_gate.validate_positive_value_result(
            duplicate_report_result,
            alignment,
            "product.md",
            expected_case_id="V-000",
        )
        self.assertTrue(
            any("exactly one Positive value report" in error for error in duplicate_report_errors),
            duplicate_report_errors,
        )

        duplicate_key_body = result.body.replace(
            '"actual": 7500,',
            '"actual": 9999,\n  "actual": 7500,',
        )
        duplicate_key_section = docs_gate.markdown_section_body(
            docs_gate.Document(result.path, {}, duplicate_key_body),
            "Positive value report",
        )
        assert duplicate_key_section is not None
        duplicate_key_result = docs_gate.Document(
            result.path,
            {
                **result.metadata,
                "positive_value_report_digest": "sha256:"
                + hashlib.sha256(duplicate_key_section.encode("utf-8")).hexdigest(),
            },
            duplicate_key_body,
        )
        duplicate_key_errors = docs_gate.validate_positive_value_result(
            duplicate_key_result,
            alignment,
            "product.md",
            expected_case_id="V-000",
        )
        self.assertTrue(
            any("duplicate JSON key" in error for error in duplicate_key_errors),
            duplicate_key_errors,
        )

        extra_field_body = result.body.replace(
            '\n}', '\n  ,"verdict": "FAIL"\n}', 1
        )
        extra_field_section = docs_gate.markdown_section_body(
            docs_gate.Document(result.path, {}, extra_field_body),
            "Positive value report",
        )
        assert extra_field_section is not None
        extra_field_result = docs_gate.Document(
            result.path,
            {
                **result.metadata,
                "positive_value_report_digest": "sha256:"
                + hashlib.sha256(extra_field_section.encode("utf-8")).hexdigest(),
            },
            extra_field_body,
        )
        extra_field_errors = docs_gate.validate_positive_value_result(
            extra_field_result,
            alignment,
            "product.md",
            expected_case_id="V-000",
        )
        self.assertTrue(
            any("exact v1 schema fields" in error for error in extra_field_errors),
            extra_field_errors,
        )

        float_actual_body = result.body.replace(
            '"actual": 7500,', '"actual": 7500.0,', 1
        )
        float_actual_section = docs_gate.markdown_section_body(
            docs_gate.Document(result.path, {}, float_actual_body),
            "Positive value report",
        )
        assert float_actual_section is not None
        float_actual_result = docs_gate.Document(
            result.path,
            {
                **result.metadata,
                "positive_value_report_digest": "sha256:"
                + hashlib.sha256(float_actual_section.encode("utf-8")).hexdigest(),
            },
            float_actual_body,
        )
        float_actual_errors = docs_gate.validate_positive_value_result(
            float_actual_result,
            alignment,
            "product.md",
            expected_case_id="V-000",
        )
        self.assertTrue(
            any("actual must be an exact JSON integer" in error for error in float_actual_errors),
            float_actual_errors,
        )

        with tempfile.TemporaryDirectory() as directory:
            manifest_path = Path(directory) / "manifest.yaml"
            manifest_path.write_text(
                "product_goal_alignment:\n"
                "  positive_value_metric: normalized-reuse-cost\n"
                "  positive_value_unit: basis-points\n"
                "  positive_value_comparison: at-most\n"
                "  positive_value_threshold: 8000\n"
                "  positive_value_reuse_horizon_questions: 3\n"
                f"  mature_source_agent_protocol_digest: {'sha256:' + '1' * 64}\n"
                f"  mature_source_agent_rubric_digest: {'sha256:' + '2' * 64}\n"
                f"  mature_source_agent_cache_policy_digest: {'sha256:' + '3' * 64}\n"
                f"  positive_value_protocol_digest: {'sha256:' + '4' * 64}\n"
                f"  positive_value_freeze_receipt_ref: {'codex-user-message:sha256:' + '5' * 64}\n"
                "  positive_value_adjudication_owner: user\n"
                "development:\n"
                "  slices: {}\n"
                "authorization:\n"
                f"  authorization_ref: {'codex-user-message:sha256:' + '6' * 64}\n",
                encoding="utf-8",
            )
            final_freshness_errors = docs_gate.validate_product_goal_result(
                result,
                "ITER-008",
                manifest_path,
                docs_gate.Document(
                    result.path.parent / "verification-matrix.md",
                    {"id": "ITER-008-VERIFICATION"},
                    "# Verification\n",
                ),
            )
        self.assertTrue(
            any(
                "final positive value adjudication must use a new message" in error
                for error in final_freshness_errors
            ),
            final_freshness_errors,
        )

        unfrozen = {
            **alignment,
            "mature_source_agent_protocol_digest": "user-held-not-disclosed",
        }
        freeze_errors = docs_gate.validate_positive_value_execution_readiness(
            unfrozen, "manifest.yaml"
        )
        self.assertTrue(
            any(
                "mature_source_agent_protocol_digest" in error
                for error in freeze_errors
            ),
            freeze_errors,
        )

    def test_early_evaluation_bindings_are_frozen_before_execution(self) -> None:
        new_refs = ["ITER-008-SLICE-001", "ITER-008-SLICE-002"]
        blocking = [
            "V-CANARY-001",
            "V-NEG-EARLY-001",
            "V-COMP-EARLY-001",
            "V-DIAG-001",
        ]
        alignment: dict[str, object] = {
            "evaluation_input_mode": "user-held-live-after-product-code-freeze",
            "mature_source_agent_protocol_digest": "user-held-not-disclosed",
            "mature_source_agent_rubric_digest": "not-frozen-proposal-only",
            "positive_value_metric": "not-frozen-proposal-only",
            "positive_value_unit": "not-frozen-proposal-only",
            "positive_value_comparison": "not-frozen-proposal-only",
            "positive_value_threshold": "not-frozen-proposal-only",
            "positive_value_reuse_horizon_questions": "not-frozen-proposal-only",
            "mature_source_agent_cache_policy_digest": "not-frozen-proposal-only",
            "positive_value_protocol_digest": "not-frozen-proposal-only",
            "positive_value_freeze_receipt_ref": "not-authorized",
            "positive_value_adjudication_owner": "user",
            "early_hidden_canary_bindings": {
                "slice_001": {
                    "case_id": "V-CANARY-001",
                    "new_slice_ref": new_refs[0],
                    "project_manifest_digest": "user-held-not-disclosed",
                    "suite_digest": "user-held-not-disclosed",
                    "question_count": 3,
                    "answerable_question_count": 1,
                    "boundary_question_count": 2,
                    "bounded_absence_question_count": 1,
                    "coverage_limitation_question_count": 1,
                    "negative_case_id": "V-NEG-EARLY-001",
                    "evaluation_owner": "user",
                    "implementation_visibility": "hidden-until-slice-code-freeze",
                    "burn_rule": "product-change-between-disclosure-and-slice-result-seal-burns-canary-and-preserves-result",
                }
            },
            "early_comparison_binding": {
                "case_id": "V-COMP-EARLY-001",
                "canary_case_id": "V-CANARY-001",
                "new_slice_ref": new_refs[0],
                "protocol_digest_ref": "mature_source_agent_protocol_digest",
                "quality_rule": "zero-major-error-and-no-need-claim-regression",
                "positive_value_rule": "precommitted-measurable-world-model-advantage-must-pass",
                "positive_value_metric_ref": "positive_value_metric",
                "positive_value_unit_ref": "positive_value_unit",
                "positive_value_comparison_ref": "positive_value_comparison",
                "positive_value_threshold_ref": "positive_value_threshold",
                "positive_value_reuse_horizon_ref": "positive_value_reuse_horizon_questions",
                "baseline_cache_policy_digest_ref": "mature_source_agent_cache_policy_digest",
                "positive_value_protocol_digest_ref": "positive_value_protocol_digest",
                "positive_value_adjudication_owner_ref": "positive_value_adjudication_owner",
            },
            "early_diagnostic_binding": {
                "case_id": "V-DIAG-001",
                "canary_case_id": "V-CANARY-001",
                "new_slice_ref": new_refs[0],
                "layer_chain": "source-snapshot-query-trace-draft-review-web",
            },
        }
        self.assertEqual(
            docs_gate.validate_early_evaluation_bindings(
                alignment, new_refs, blocking, "manifest.yaml"
            ),
            [],
        )

        missing_comparison = copy.deepcopy(alignment)
        del missing_comparison["early_comparison_binding"]
        missing_errors = docs_gate.validate_early_evaluation_bindings(
            missing_comparison, new_refs, blocking, "manifest.yaml"
        )
        self.assertTrue(
            any("early_comparison_binding" in error for error in missing_errors),
            missing_errors,
        )

        wrong_canary = copy.deepcopy(alignment)
        wrong_canary["early_diagnostic_binding"][  # type: ignore[index]
            "canary_case_id"
        ] = "V-CANARY-999"
        canary_errors = docs_gate.validate_early_evaluation_bindings(
            wrong_canary, new_refs, blocking, "manifest.yaml"
        )
        self.assertTrue(
            any("same canary" in error for error in canary_errors), canary_errors
        )

        wrong_layers = copy.deepcopy(alignment)
        wrong_layers["early_diagnostic_binding"][  # type: ignore[index]
            "layer_chain"
        ] = "source-answer"
        layer_errors = docs_gate.validate_early_evaluation_bindings(
            wrong_layers, new_refs, blocking, "manifest.yaml"
        )
        self.assertTrue(
            any("layer_chain" in error for error in layer_errors), layer_errors
        )

    def test_direction_preview_defers_early_gates_to_the_following_slice(
        self,
    ) -> None:
        new_refs = ["ITER-009-SLICE-001", "ITER-009-SLICE-002"]
        preview_case = "V-PREVIEW-001"
        later_cases = [
            "V-CANARY-001",
            "V-NEG-EARLY-001",
            "V-COMP-EARLY-001",
            "V-DIAG-001",
        ]
        blocking = [preview_case, *later_cases]
        alignment: dict[str, object] = {
            "direction_preview_checkpoint": preview_case,
            "direction_preview_binding": {
                "case_id": preview_case,
                "new_slice_ref": new_refs[0],
                "real_product_entry": "loopback-product-owned-world-model-web",
                "representative_task_count": 2,
                "status_label": "non-acceptance-non-production",
                "decision_owner": "user",
                "allowed_decisions": "CONTINUE,REDIRECT,REJECT",
                "hardening_requires_continue": True,
            },
            "evaluation_input_mode": "user-held-live-after-product-code-freeze",
            "mature_source_agent_protocol_digest": "user-held-not-disclosed",
            "mature_source_agent_rubric_digest": "sha256:" + "2" * 64,
            "positive_value_metric": "normalized-reuse-cost",
            "positive_value_unit": "basis-points",
            "positive_value_comparison": "at-most",
            "positive_value_threshold": 8000,
            "positive_value_reuse_horizon_questions": 3,
            "mature_source_agent_cache_policy_digest": "sha256:" + "3" * 64,
            "positive_value_protocol_digest": "sha256:" + "4" * 64,
            "positive_value_freeze_receipt_ref": "codex-user-message:sha256:"
            + "5" * 64,
            "positive_value_adjudication_owner": "user",
        }

        self.assertEqual(
            docs_gate.validate_direction_preview_binding(
                alignment, new_refs, blocking, "manifest.yaml"
            ),
            [],
        )

        wrong_entry = copy.deepcopy(alignment)
        wrong_entry["direction_preview_binding"]["real_product_entry"] = (
            "https://public.example.test/"
        )
        self.assertTrue(
            any(
                "real_product_entry" in error
                for error in docs_gate.validate_direction_preview_binding(
                    wrong_entry, new_refs, blocking, "manifest.yaml"
                )
            )
        )
        wrong_owner = copy.deepcopy(alignment)
        wrong_owner["direction_preview_binding"]["decision_owner"] = "automation"
        self.assertTrue(
            any(
                "decision_owner" in error
                for error in docs_gate.validate_direction_preview_binding(
                    wrong_owner, new_refs, blocking, "manifest.yaml"
                )
            )
        )
        self.assertEqual(
            docs_gate.required_early_evaluation_slice_refs(
                alignment, new_refs, direction_preview_enabled=True
            ),
            {new_refs[1]},
        )
        self.assertEqual(
            docs_gate.validate_early_evaluation_bindings(
                alignment,
                new_refs,
                blocking,
                "manifest.yaml",
                defer_until_post_preview=True,
                direction_preview_enabled=True,
            ),
            [],
        )

        preview_owns_comparison = copy.deepcopy(alignment)
        preview_owns_comparison["early_comparison_binding"] = {
            "case_id": "V-COMP-EARLY-001",
            "new_slice_ref": new_refs[0],
        }
        preview_errors = docs_gate.validate_early_evaluation_bindings(
            preview_owns_comparison,
            new_refs,
            blocking,
            "manifest.yaml",
            defer_until_post_preview=True,
            direction_preview_enabled=True,
        )
        self.assertTrue(
            any("direction preview Slice must not own" in error for error in preview_errors),
            preview_errors,
        )

        missing_later_errors = docs_gate.validate_early_evaluation_bindings(
            alignment,
            new_refs,
            blocking,
            "manifest.yaml",
            defer_until_post_preview=False,
            direction_preview_enabled=True,
        )
        self.assertTrue(
            any("early_hidden_canary_bindings" in error for error in missing_later_errors),
            missing_later_errors,
        )

        hardened = copy.deepcopy(alignment)
        hardened["early_hidden_canary_bindings"] = {
            "slice_002": {
                "case_id": "V-CANARY-001",
                "new_slice_ref": new_refs[1],
                "project_manifest_digest": "user-held-not-disclosed",
                "suite_digest": "user-held-not-disclosed",
                "question_count": 3,
                "answerable_question_count": 1,
                "boundary_question_count": 2,
                "bounded_absence_question_count": 1,
                "coverage_limitation_question_count": 1,
                "negative_case_id": "V-NEG-EARLY-001",
                "evaluation_owner": "user",
                "implementation_visibility": "hidden-until-slice-code-freeze",
                "burn_rule": "product-change-between-disclosure-and-slice-result-seal-burns-canary-and-preserves-result",
            }
        }
        hardened["early_comparison_binding"] = {
            "case_id": "V-COMP-EARLY-001",
            "canary_case_id": "V-CANARY-001",
            "new_slice_ref": new_refs[1],
            "protocol_digest_ref": "mature_source_agent_protocol_digest",
            "quality_rule": "zero-major-error-and-no-need-claim-regression",
            "positive_value_rule": "precommitted-measurable-world-model-advantage-must-pass",
            "positive_value_metric_ref": "positive_value_metric",
            "positive_value_unit_ref": "positive_value_unit",
            "positive_value_comparison_ref": "positive_value_comparison",
            "positive_value_threshold_ref": "positive_value_threshold",
            "positive_value_reuse_horizon_ref": "positive_value_reuse_horizon_questions",
            "baseline_cache_policy_digest_ref": "mature_source_agent_cache_policy_digest",
            "positive_value_protocol_digest_ref": "positive_value_protocol_digest",
            "positive_value_adjudication_owner_ref": "positive_value_adjudication_owner",
        }
        hardened["early_diagnostic_binding"] = {
            "case_id": "V-DIAG-001",
            "canary_case_id": "V-CANARY-001",
            "new_slice_ref": new_refs[1],
            "layer_chain": "source-snapshot-query-trace-draft-review-web",
        }
        self.assertEqual(
            docs_gate.validate_early_evaluation_bindings(
                hardened,
                new_refs,
                blocking,
                "manifest.yaml",
                defer_until_post_preview=False,
                direction_preview_enabled=True,
            ),
            [],
        )

        legacy_manifest = {
            "development": {
                "slices": {
                    new_refs[0]: {"status": "authorized"},
                    new_refs[1]: {"status": "proposed"},
                }
            }
        }
        self.assertEqual(
            docs_gate.required_early_evaluation_slice_refs(
                alignment, new_refs, direction_preview_enabled=False
            ),
            {new_refs[0]},
        )
        self.assertFalse(
            docs_gate.direction_preview_hardening_is_deferred(
                legacy_manifest,
                alignment,
                new_refs,
                direction_preview_enabled=False,
            )
        )
        legacy_errors = docs_gate.validate_early_evaluation_bindings(
            alignment,
            new_refs,
            blocking,
            "manifest.yaml",
            defer_until_post_preview=True,
            direction_preview_enabled=False,
        )
        self.assertTrue(
            any("early_hidden_canary_bindings" in error for error in legacy_errors),
            legacy_errors,
        )

    def test_direction_preview_does_not_exempt_contract_and_safety_readiness(
        self,
    ) -> None:
        new_refs = ["ITER-009-SLICE-001", "ITER-009-SLICE-002"]
        alignment: dict[str, object] = {
            "direction_preview_checkpoint": "V-PREVIEW-001",
            "direction_preview_binding": {
                "case_id": "V-PREVIEW-001",
                "new_slice_ref": new_refs[0],
                "real_product_entry": "loopback-product-owned-world-model-web",
                "representative_task_count": 2,
                "status_label": "non-acceptance-non-production",
                "decision_owner": "user",
                "allowed_decisions": "CONTINUE,REDIRECT,REJECT",
                "hardening_requires_continue": True,
            },
            "critical_assumption_ids": "A1",
            "critical_assumption_catalog_digest": "sha256:" + "1" * 64,
            "readiness_blocking_case_ids": [],
            "blocking_case_ids": ["V-PREVIEW-001"],
            "authorized_software_sources_digest": "sha256:" + "2" * 64,
        }
        manifest = {
            "product_goal_alignment": alignment,
            "development": {
                "slices": {
                    new_refs[0]: {"status": "authorized"},
                    new_refs[1]: {"status": "proposed"},
                }
            },
        }
        errors = docs_gate.validate_product_goal_execution_readiness(
            manifest,
            "manifest.yaml",
            "ITER-009",
            {},
            new_refs,
            None,
        )
        self.assertFalse(
            any("early_hidden_canary_bindings" in error for error in errors),
            errors,
        )
        self.assertTrue(any("source_scope must be a mapping" in error for error in errors))
        self.assertTrue(any("answer_protocol must be a mapping" in error for error in errors))
        self.assertTrue(any("readiness_inputs must be a mapping" in error for error in errors))

        hardened_manifest = copy.deepcopy(manifest)
        hardened_manifest["development"]["slices"][new_refs[0]]["status"] = (
            "completed"
        )
        hardened_manifest["development"]["slices"][new_refs[1]]["status"] = (
            "authorized"
        )
        hardened_errors = docs_gate.validate_product_goal_execution_readiness(
            hardened_manifest,
            "manifest.yaml",
            "ITER-009",
            {},
            new_refs,
            None,
        )
        self.assertTrue(
            any("positive_value_" in error for error in hardened_errors),
            hardened_errors,
        )
        self.assertTrue(
            any("early_hidden_canary_bindings" in error for error in hardened_errors),
            hardened_errors,
        )

    def test_reflection_bindings_cover_each_slice_and_distinguish_success_decisions(
        self,
    ) -> None:
        alignment, new_refs, blocking = self.valid_alignment()
        self.assertEqual(
            docs_gate.validate_reflection_gate_bindings(
                alignment, new_refs, blocking, "manifest.yaml"
            ),
            [],
        )

        missing = copy.deepcopy(alignment)
        del missing["reflection_gate_bindings"]["slice_002"]  # type: ignore[index]
        missing_errors = docs_gate.validate_reflection_gate_bindings(
            missing, new_refs, blocking, "manifest.yaml"
        )
        self.assertTrue(
            any("every Slice" in error for error in missing_errors), missing_errors
        )

        wrong_decision = copy.deepcopy(alignment)
        wrong_decision["reflection_gate_bindings"]["slice_001"][  # type: ignore[index]
            "success_decision"
        ] = "ACCEPT"
        decision_errors = docs_gate.validate_reflection_gate_bindings(
            wrong_decision, new_refs, blocking, "manifest.yaml"
        )
        self.assertTrue(
            any("must equal CONTINUE" in error for error in decision_errors),
            decision_errors,
        )

        non_blocking = docs_gate.validate_reflection_gate_bindings(
            alignment, new_refs, ["V-REFLECT-001"], "manifest.yaml"
        )
        self.assertTrue(
            any("blocking_case_ids" in error for error in non_blocking),
            non_blocking,
        )

        final_incomplete = copy.deepcopy(alignment)
        final_incomplete["reflection_gate_bindings"]["slice_002"][  # type: ignore[index]
            "assumption_ids"
        ] = ["A1"]
        final_errors = docs_gate.validate_reflection_gate_bindings(
            final_incomplete, new_refs, blocking, "manifest.yaml"
        )
        self.assertTrue(
            any("final Slice" in error for error in final_errors), final_errors
        )

        wrong_order = copy.deepcopy(alignment)
        wrong_order["reflection_gate_bindings"]["slice_002"][  # type: ignore[index]
            "assumption_ids"
        ] = ["A2", "A1"]
        order_errors = docs_gate.validate_reflection_gate_bindings(
            wrong_order, new_refs, blocking, "manifest.yaml"
        )
        self.assertTrue(
            any("ordered subset" in error for error in order_errors), order_errors
        )

    def test_conditional_falsifier_must_be_owned_by_its_current_slice(self) -> None:
        documents, parse_errors = docs_gate.load_documents()
        self.assertEqual(parse_errors, [])
        by_id = {document.identifier: document for document in documents}
        manifest_path = (
            docs_gate.REPOSITORY
            / "docs/project/iterations/iteration-008/manifest.yaml"
        )
        manifest_text = manifest_path.read_text(encoding="utf-8")
        moved_falsifier_text = manifest_text.replace(
            "          assumption_id: A7\n          case_id: V-NEG-EARLY-001",
            "          assumption_id: A7\n          case_id: V-HARDEN-001",
        ).replace(
            "          assumption_id: A8\n          case_id: V-WEB-001",
            "          assumption_id: A8\n          case_id: V-WEB-002",
        )
        self.assertNotEqual(moved_falsifier_text, manifest_text)
        with tempfile.TemporaryDirectory() as directory:
            moved_manifest = Path(directory) / "manifest.yaml"
            moved_manifest.write_text(moved_falsifier_text, encoding="utf-8")
            ownership_errors = docs_gate.validate_product_goal_reference_targets(
                moved_manifest,
                "ITER-008",
                by_id,
            )
        self.assertTrue(
            any("conditional-falsifier" in error for error in ownership_errors),
            ownership_errors,
        )

    def test_slice_reflection_result_requires_auditable_process_and_decision(
        self,
    ) -> None:
        target = docs_gate.Document(
            docs_gate.REPOSITORY
            / "docs/project/iterations/iteration-008/development-design/SLICE-001.md",
            {
                "id": "ITER-008-SLICE-001",
                "kind": "development-slice",
                "iteration": "ITER-008",
                "product_goal_slice_gate_case_ids": [
                    "V-DIAG-001",
                    "V-CANARY-001",
                    "V-REFLECT-001",
                ],
            },
            "# Slice\n",
        )
        result_body = (
            "# Result\n\n"
            "## Architecture reflection and continuation decision\n\n"
            "### Assumption verdicts\n\n"
            "| Assumption | Expected | Exact evidence refs | Verdict | Impact |\n"
            "|---|---|---|---|---|\n"
            "| A1 | query gap | V-DIAG-001 | SUPPORTED | no material deviation |\n"
            "| A2 | typed query closure | V-CANARY-001 | SUPPORTED | bounded scope |\n\n"
            "### Deviation and issue classification\n\n"
            "No material deviation; classification is none.\n\n"
            "### Layer diagnosis and mature-source-Agent comparison\n\n"
            "Every layer has exact evidence and the comparison did not regress.\n\n"
            "### Findings, alternatives and next risk\n\n"
            "Findings are dispositioned; breadth is the next risk.\n\n"
            "### Decision and rationale\n\n"
            "Decision: CONTINUE\n\n"
            "Decision owner: product-architecture-quality\n\n"
            "Decision ref: codex-user-message:sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc\n\n"
            "The frozen assumptions remain supported.\n"
        )
        result = docs_gate.Document(
            docs_gate.REPOSITORY
            / "docs/project/iterations/iteration-008/results/slice-001.md",
            {
                "id": "ITER-008-RESULT-SLICE-001",
                "kind": "iteration-result",
                "iteration": "ITER-008",
                "reflection_gate_case_id": "V-REFLECT-001",
                "reflection_gate_status": "PASS",
                "reflection_decision": "CONTINUE",
                "reflection_decision_owner": "product-architecture-quality",
                "reflection_decision_ref": "codex-user-message:sha256:" + "c" * 64,
                "reflection_issue_class": "none",
                "reflection_issue_scope": "none",
                "reflection_report_digest": reflection_report_digest(result_body),
                "critical_assumption_catalog_digest": "sha256:" + "9" * 64,
            },
            result_body,
        )
        assumption_expectations = {
            "A1": "query gap",
            "A2": "typed query closure",
        }
        assumption_catalog_digest = "sha256:" + "9" * 64
        binding = {
            "case_id": "V-REFLECT-001",
            "new_slice_ref": target.identifier,
            "assumption_ids": ["A1", "A2"],
            "success_decision": "CONTINUE",
            "decision_owner": "product-architecture-quality",
        }
        manifest_slice = {"reflection_decision": "CONTINUE"}
        verification = docs_gate.Document(
            docs_gate.REPOSITORY
            / "docs/project/iterations/iteration-008/verification-matrix.md",
            {"id": "ITER-008-VERIFICATION", "kind": "iteration-verification"},
            "| Case | Claim | Level | Frozen input / oracle | Expected | Evidence | Status / blocking meaning |\n"
            "|---|---|---|---|---|---|---|\n"
            "| V-DIAG-001 | diagnose | architecture / diagnostic | exact result | layer verdicts | ITER-008-RESULT-SLICE-001#V-DIAG-001 | PASS / blocking |\n"
            "| V-CANARY-001 | hidden check | product / hidden | exact result | product verdicts | ITER-008-RESULT-SLICE-001#V-CANARY-001 | PASS / blocking |\n"
            "| V-REFLECT-001 | review assumptions | architecture / reflection | exact result | explicit decision | ITER-008-RESULT-SLICE-001#V-REFLECT-001 | PASS / blocking |\n",
        )
        self.assertEqual(
            docs_gate.validate_slice_reflection_result(
                target,
                result,
                binding,
                manifest_slice,
                verification,
                "manifest.yaml",
                blocked=False,
                assumption_expectations=assumption_expectations,
                assumption_catalog_digest=assumption_catalog_digest,
            ),
            [],
        )

        blocked_supported_body = result.body.replace(
            "Decision: CONTINUE", "Decision: REDIRECT"
        )
        blocked_supported_result = docs_gate.Document(
            result.path,
            {
                **result.metadata,
                "reflection_decision": "REDIRECT",
                "reflection_issue_class": "architecture",
                "reflection_issue_scope": "systemic",
                "reflection_report_digest": reflection_report_digest(
                    blocked_supported_body
                ),
            },
            blocked_supported_body,
        )
        blocked_supported_errors = docs_gate.validate_slice_reflection_result(
            target,
            blocked_supported_result,
            binding,
            {"reflection_decision": "REDIRECT"},
            verification,
            "manifest.yaml",
            blocked=True,
        )
        self.assertTrue(
            any(
                "requires at least one FALSIFIED or UNRESOLVED" in error
                for error in blocked_supported_errors
            ),
            blocked_supported_errors,
        )

        missing_decision_ref_metadata = dict(result.metadata)
        del missing_decision_ref_metadata["reflection_decision_ref"]
        missing_decision_ref = docs_gate.Document(
            result.path, missing_decision_ref_metadata, result.body
        )
        decision_ref_errors = docs_gate.validate_slice_reflection_result(
            target,
            missing_decision_ref,
            binding,
            manifest_slice,
            verification,
            "manifest.yaml",
            blocked=False,
        )
        self.assertTrue(
            any("exact user message digest" in error for error in decision_ref_errors),
            decision_ref_errors,
        )

        redirect_body = result.body.replace(
            "| A1 | query gap | V-DIAG-001 | SUPPORTED | no material deviation |",
            "| A1 | query gap | V-DIAG-001 | FALSIFIED | architecture deviation |",
        ).replace("Decision: CONTINUE", "Decision: REDIRECT")
        redirect_result = docs_gate.Document(
            result.path,
            {
                **result.metadata,
                "reflection_decision": "REDIRECT",
                "reflection_issue_class": "architecture",
                "reflection_issue_scope": "systemic",
                "reflection_report_digest": reflection_report_digest(redirect_body),
            },
            redirect_body,
        )
        redirect_verification = docs_gate.Document(
            verification.path,
            verification.metadata,
            verification.body.replace(
                "ITER-008-RESULT-SLICE-001#V-DIAG-001 | PASS / blocking",
                "ITER-008-RESULT-SLICE-001#V-DIAG-001 | FAIL / blocking",
            ),
        )
        redirect_errors = docs_gate.validate_slice_reflection_result(
            target,
            redirect_result,
            binding,
            {"reflection_decision": "REDIRECT"},
            redirect_verification,
            "manifest.yaml",
            blocked=False,
        )
        self.assertTrue(
            any("success_decision" in error for error in redirect_errors),
            redirect_errors,
        )
        self.assertEqual(
            docs_gate.validate_slice_reflection_result(
                target,
                redirect_result,
                binding,
                {"reflection_decision": "REDIRECT"},
                redirect_verification,
                "manifest.yaml",
                blocked=True,
                assumption_expectations=assumption_expectations,
                assumption_catalog_digest=assumption_catalog_digest,
            ),
            [],
        )

        missing_catalog_input_errors = docs_gate.validate_slice_reflection_result(
            target,
            result,
            binding,
            manifest_slice,
            verification,
            "manifest.yaml",
            blocked=False,
        )
        self.assertTrue(
            any("frozen assumption catalog" in error for error in missing_catalog_input_errors),
            missing_catalog_input_errors,
        )

        not_run_verification = docs_gate.Document(
            redirect_verification.path,
            redirect_verification.metadata,
            redirect_verification.body.replace(
                "ITER-008-RESULT-SLICE-001#V-DIAG-001 | FAIL / blocking",
                "ITER-008-RESULT-SLICE-001#V-DIAG-001 | NOT-RUN / blocking",
            ),
        )
        not_run_errors = docs_gate.validate_slice_reflection_result(
            target,
            redirect_result,
            binding,
            {"reflection_decision": "REDIRECT"},
            not_run_verification,
            "manifest.yaml",
            blocked=True,
        )
        self.assertTrue(
            any("must be executed" in error for error in not_run_errors),
            not_run_errors,
        )

        conditional_target = docs_gate.Document(
            target.path,
            {
                **target.metadata,
                "product_goal_slice_gate_case_ids": [
                    *target.metadata["product_goal_slice_gate_case_ids"],
                    "V-NEG-EARLY-001",
                ],
            },
            target.body,
        )
        conditional_binding = {
            **binding,
            "conditional_falsifier_bindings": {
                "deferred_a3": {
                    "assumption_id": "A3",
                    "case_id": "V-NEG-EARLY-001",
                }
            },
        }
        conditional_verification = docs_gate.Document(
            redirect_verification.path,
            redirect_verification.metadata,
            redirect_verification.body
            + "| V-NEG-EARLY-001 | early falsifier | product / negative | exact result | stop | ITER-008-RESULT-SLICE-001#V-NEG-EARLY-001 | FAIL / blocking |\n",
        )
        conditional_errors = docs_gate.validate_slice_reflection_result(
            conditional_target,
            redirect_result,
            conditional_binding,
            {"reflection_decision": "REDIRECT"},
            conditional_verification,
            "manifest.yaml",
            blocked=True,
        )
        self.assertTrue(
            any("verdict row for A3" in error for error in conditional_errors),
            conditional_errors,
        )

        for verdict in ("FALSIFIED", "UNRESOLVED"):
            inconsistent_body = result.body.replace(
                "| A1 | query gap | V-DIAG-001 | SUPPORTED | no material deviation |",
                f"| A1 | query gap | V-DIAG-001 | {verdict} | material deviation |",
            )
            inconsistent_result = docs_gate.Document(
                result.path,
                {
                    **result.metadata,
                    "reflection_report_digest": reflection_report_digest(
                        inconsistent_body
                    ),
                },
                inconsistent_body,
            )
            inconsistent_errors = docs_gate.validate_slice_reflection_result(
                target,
                inconsistent_result,
                binding,
                manifest_slice,
                verification,
                "manifest.yaml",
                blocked=False,
            )
            self.assertTrue(
                any(
                    "requires every bound critical assumption verdict to be SUPPORTED"
                    in error
                    for error in inconsistent_errors
                ),
                inconsistent_errors,
            )

        body_mismatch_result = docs_gate.Document(
            result.path,
            {**result.metadata, "reflection_decision": "REDIRECT"},
            result.body,
        )
        body_mismatch_errors = docs_gate.validate_slice_reflection_result(
            target,
            body_mismatch_result,
            binding,
            {"reflection_decision": "REDIRECT"},
            verification,
            "manifest.yaml",
            blocked=True,
        )
        self.assertTrue(
            any("body Decision" in error for error in body_mismatch_errors),
            body_mismatch_errors,
        )

        duplicate_decision_body = result.body.replace(
            "Findings are dispositioned; breadth is the next risk.",
            "Findings are dispositioned; breadth is the next risk.\n\n"
            "Decision: REDIRECT\n\nDecision owner: attacker",
        )
        duplicate_decision_result = docs_gate.Document(
            result.path,
            {
                **result.metadata,
                "reflection_report_digest": reflection_report_digest(
                    duplicate_decision_body
                ),
            },
            duplicate_decision_body,
        )
        duplicate_decision_errors = docs_gate.validate_slice_reflection_result(
            target,
            duplicate_decision_result,
            binding,
            manifest_slice,
            verification,
            "manifest.yaml",
            blocked=False,
        )
        self.assertTrue(
            any(
                "exact reflection section must contain exactly one Decision line"
                in error
                for error in duplicate_decision_errors
            ),
            duplicate_decision_errors,
        )
        self.assertTrue(
            any(
                "exact reflection section must contain exactly one Decision owner line"
                in error
                for error in duplicate_decision_errors
            ),
            duplicate_decision_errors,
        )

        indented_duplicate_body = result.body.replace(
            "Findings are dispositioned; breadth is the next risk.",
            "Findings are dispositioned; breadth is the next risk.\n\n"
            " Decision: REDIRECT\n\n Decision owner: attacker\n\n"
            " Decision ref: codex-user-message:sha256:"
            + "e" * 64,
        )
        indented_duplicate_result = docs_gate.Document(
            result.path,
            {
                **result.metadata,
                "reflection_report_digest": reflection_report_digest(
                    indented_duplicate_body
                ),
            },
            indented_duplicate_body,
        )
        indented_duplicate_errors = docs_gate.validate_slice_reflection_result(
            target,
            indented_duplicate_result,
            binding,
            manifest_slice,
            verification,
            "manifest.yaml",
            blocked=False,
        )
        self.assertTrue(
            any("exactly one Decision line" in error for error in indented_duplicate_errors),
            indented_duplicate_errors,
        )

        duplicate_section_body = (
            result.body
            + "\n## Architecture reflection and continuation decision\n\n"
            + "Decision: REJECT\n\nDecision owner: attacker\n"
        )
        duplicate_section_result = docs_gate.Document(
            result.path,
            result.metadata,
            duplicate_section_body,
        )
        duplicate_section_errors = docs_gate.validate_slice_reflection_result(
            target,
            duplicate_section_result,
            binding,
            manifest_slice,
            verification,
            "manifest.yaml",
            blocked=False,
        )
        self.assertTrue(
            any(
                "exactly one Architecture reflection" in error
                for error in duplicate_section_errors
            ),
            duplicate_section_errors,
        )

        nonblocking_fail_verification = docs_gate.Document(
            redirect_verification.path,
            redirect_verification.metadata,
            redirect_verification.body.replace(
                "ITER-008-RESULT-SLICE-001#V-DIAG-001 | FAIL / blocking",
                "ITER-008-RESULT-SLICE-001#V-DIAG-001 | FAIL / not blocking",
            ),
        )
        nonblocking_fail_errors = docs_gate.validate_slice_reflection_result(
            target,
            redirect_result,
            binding,
            {"reflection_decision": "REDIRECT"},
            nonblocking_fail_verification,
            "manifest.yaml",
            blocked=True,
        )
        self.assertTrue(
            any("exact PASS, FAIL or NOT-RUN" in error for error in nonblocking_fail_errors),
            nonblocking_fail_errors,
        )

        self_evidence_body = result.body.replace(
            "| A1 | query gap | V-DIAG-001 | SUPPORTED | no material deviation |",
            "| A1 | query gap | V-REFLECT-001 | SUPPORTED | no material deviation |",
        )
        self_evidence_result = docs_gate.Document(
            result.path,
            {
                **result.metadata,
                "reflection_report_digest": reflection_report_digest(
                    self_evidence_body
                ),
            },
            self_evidence_body,
        )
        self_evidence_errors = docs_gate.validate_slice_reflection_result(
            target,
            self_evidence_result,
            binding,
            manifest_slice,
            verification,
            "manifest.yaml",
            blocked=False,
        )
        self.assertTrue(
            any("self-evidence" in error for error in self_evidence_errors),
            self_evidence_errors,
        )

        empty_result = docs_gate.Document(result.path, result.metadata, "# Result\n")
        empty_errors = docs_gate.validate_slice_reflection_result(
            target,
            empty_result,
            binding,
            manifest_slice,
            verification,
            "manifest.yaml",
            blocked=False,
        )
        self.assertTrue(
            any("substantive" in error for error in empty_errors), empty_errors
        )

        missing_subsection_result = docs_gate.Document(
            result.path,
            result.metadata,
            result.body.replace(
                "### Findings, alternatives and next risk",
                "### Unstructured notes",
            ),
        )
        subsection_errors = docs_gate.validate_slice_reflection_result(
            target,
            missing_subsection_result,
            binding,
            manifest_slice,
            verification,
            "manifest.yaml",
            blocked=False,
        )
        self.assertTrue(
            any("reflection subsection" in error for error in subsection_errors),
            subsection_errors,
        )

        missing_assumption_result = docs_gate.Document(
            result.path,
            result.metadata,
            result.body.replace(
                "| A2 | typed query closure | V-CANARY-001 | SUPPORTED | bounded scope |\n",
                "",
            ),
        )
        assumption_errors = docs_gate.validate_slice_reflection_result(
            target,
            missing_assumption_result,
            binding,
            manifest_slice,
            verification,
            "manifest.yaml",
            blocked=False,
        )
        self.assertTrue(
            any("verdict row for A2" in error for error in assumption_errors),
            assumption_errors,
        )

        outside_only_body = result.body.replace(
            "# Result\n\n",
            "# Result\n\n"
            "| A2 | typed query closure | V-CANARY-001 | SUPPORTED | forged outside reflection |\n\n",
        ).replace(
            "| A2 | typed query closure | V-CANARY-001 | SUPPORTED | bounded scope |\n",
            "",
        )
        outside_only_result = docs_gate.Document(
            result.path,
            {
                **result.metadata,
                "reflection_report_digest": reflection_report_digest(
                    outside_only_body
                ),
            },
            outside_only_body,
        )
        outside_only_errors = docs_gate.validate_slice_reflection_result(
            target,
            outside_only_result,
            binding,
            manifest_slice,
            verification,
            "manifest.yaml",
            blocked=False,
        )
        self.assertTrue(
            any("verdict row for A2" in error for error in outside_only_errors),
            outside_only_errors,
        )

    def test_critical_assumption_catalog_is_exact_resolved_and_unique(self) -> None:
        path = (
            docs_gate.REPOSITORY
            / "docs/project/iterations/iteration-008/proposal.md"
        )
        body = (
            "# Proposal\n\n"
            "## Critical assumptions and falsification plan\n\n"
            "| Assumption | Earliest falsifier | Action |\n"
            "|---|---|---|\n"
            "| A1: typed queries close the answer | V-DIAG-001 | redirect query architecture |\n"
        )
        proposal = docs_gate.Document(
            path,
            {"id": "ITER-008-PROPOSAL", "iteration": "ITER-008"},
            body,
        )
        digest, expectations, errors = docs_gate.critical_assumption_catalog(
            proposal
        )
        self.assertEqual(errors, [])
        self.assertRegex(str(digest), r"^sha256:[0-9a-f]{64}$")
        self.assertEqual(
            expectations, {"A1": "typed queries close the answer"}
        )

        duplicate = docs_gate.Document(
            path,
            proposal.metadata,
            body
            + "\n## Critical assumptions and falsification plan\n\n"
            + "| A1: attacker rewrite | V-X | accept |\n",
        )
        _, _, duplicate_errors = docs_gate.critical_assumption_catalog(duplicate)
        self.assertTrue(
            any("exactly one" in error for error in duplicate_errors),
            duplicate_errors,
        )

        unresolved = docs_gate.Document(
            path,
            proposal.metadata,
            body.replace("V-DIAG-001", "pending"),
        )
        _, _, unresolved_errors = docs_gate.critical_assumption_catalog(unresolved)
        self.assertTrue(
            any("resolved three-column" in error for error in unresolved_errors),
            unresolved_errors,
        )

        malformed = docs_gate.Document(
            path,
            proposal.metadata,
            body
            + "| A2 | V-CANARY-001 | continue after rewriting the assumption |\n",
        )
        _, _, malformed_errors = docs_gate.critical_assumption_catalog(malformed)
        self.assertTrue(
            any("malformed critical assumption row" in error for error in malformed_errors),
            malformed_errors,
        )

        invalid_readiness = docs_gate.Document(
            path.parent / "readiness-review.md",
            {
                "id": "ITER-008-READINESS",
                "authorized_by": "user",
                "authorized_at": "2026-99-99T99:99:99+09:00",
                "product_goal_alignment_verdict": "accepted",
                "product_goal_alignment_reviewed_by": "user",
                "product_goal_alignment_review_ref": (
                    "codex-user-message:sha256:" + "8" * 64
                ),
            },
            "# Readiness\n",
        )
        invalid_readiness_errors = (
            docs_gate.validate_product_goal_readiness_authorization(
                invalid_readiness
            )
        )
        self.assertTrue(
            any("real ISO-8601" in error for error in invalid_readiness_errors),
            invalid_readiness_errors,
        )

    def test_proposed_reflection_gate_fails_closed_for_invalid_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory)
            iteration_directory = (
                repository / "docs/project/iterations/iteration-008"
            )
            iteration_directory.mkdir(parents=True)
            proposal = docs_gate.Document(
                iteration_directory / "proposal.md",
                {
                    "id": "ITER-008-PROPOSAL",
                    "kind": "iteration-proposal",
                    "status": "proposed",
                    "iteration": "ITER-008",
                    "depends_on": ["SYS-PRODUCT-SUCCESS"],
                },
                "# Proposal\n\n"
                "## Critical assumptions and falsification plan\n\n"
                "| Assumption | Earliest falsifier | Action |\n"
                "|---|---|---|\n"
                "| A1: first assumption | V-PRE-001 | redirect first risk |\n"
                "| A2: second assumption | V-PRE-002 | reject second risk |\n",
            )
            verification = product_goal_verification(
                iteration_directory / "verification-matrix.md"
            )
            verification = docs_gate.Document(
                verification.path,
                {
                    **verification.metadata,
                    "id": "ITER-008-VERIFICATION",
                    "iteration": "ITER-008",
                },
                verification.body,
            )
            manifest = iteration_directory / "manifest.yaml"
            manifest.write_text("product_goal_alignment: [\n", encoding="utf-8")

            with patch.object(docs_gate, "REPOSITORY", repository):
                invalid_yaml_errors = docs_gate.validate_product_goal_alignment_state(
                    [proposal, verification]
                )
                manifest.write_text("schema_version: 1\n", encoding="utf-8")
                missing_alignment_errors = (
                    docs_gate.validate_product_goal_alignment_state(
                        [proposal, verification]
                    )
                )
                manifest.write_text(
                    "schema_version: 1\n"
                    "iteration:\n"
                    "  id: ITER-008\n"
                    "  status: proposed\n"
                    "product_goal_alignment:\n"
                    "  target_ref: SYS-PRODUCT-SUCCESS\n"
                    "  critical_assumption_ids: A1\n"
                    "  critical_assumption_catalog_digest: not-frozen-proposal-only\n",
                    encoding="utf-8",
                )
                mismatched_catalog_errors = (
                    docs_gate.validate_product_goal_alignment_state(
                        [proposal, verification]
                    )
                )

        self.assertTrue(
            any("cannot be loaded" in error for error in invalid_yaml_errors),
            invalid_yaml_errors,
        )
        self.assertTrue(
            any("product_goal_alignment must be a mapping" in error for error in missing_alignment_errors),
            missing_alignment_errors,
        )
        self.assertTrue(
            any(
                "critical_assumption_ids must exactly match" in error
                for error in mismatched_catalog_errors
            ),
            mismatched_catalog_errors,
        )

    def test_follow_up_slice_requires_exact_prior_reflection_result_dependency(
        self,
    ) -> None:
        iteration_directory = (
            docs_gate.REPOSITORY / "docs/project/iterations/iteration-008"
        )
        proposal = docs_gate.Document(
            iteration_directory / "proposal.md",
            {
                "id": "ITER-008-PROPOSAL",
                "kind": "iteration-proposal",
                "status": "accepted",
                "iteration": "ITER-008",
            },
            "# Proposal\n\n"
            "## Critical assumptions and falsification plan\n\n"
            "| Assumption | Earliest falsifier | Action |\n"
            "|---|---|---|\n"
            "| A1: query closes | V-DIAG-001 in Slice 1 | redirect the query architecture |\n",
        )
        catalog_digest, catalog_expectations, catalog_errors = (
            docs_gate.critical_assumption_catalog(proposal)
        )
        self.assertEqual(catalog_errors, [])
        self.assertEqual(catalog_expectations, {"A1": "query closes"})
        first = docs_gate.Document(
            iteration_directory / "development-design/SLICE-001.md",
            {
                "id": "ITER-008-SLICE-001",
                "kind": "development-slice",
                "status": "completed",
                "authority": "historical-development",
                "coding_input": False,
                "iteration": "ITER-008",
                "depends_on": ["ITER-008-PROPOSAL"],
                "product_goal_slice_gate_case_ids": [
                    "V-DIAG-001",
                    "V-COMP-EARLY-001",
                    "V-REFLECT-001",
                ],
            },
            "# Slice\n",
        )
        reflection_body = (
            "# Result\n\n"
            "## Architecture reflection and continuation decision\n\n"
            "### Assumption verdicts\n\n"
            "| Assumption | Expected | Exact evidence refs | Verdict | Impact |\n"
            "|---|---|---|---|---|\n"
            "| A1 | query closes | V-DIAG-001 | SUPPORTED | bounded evidence |\n\n"
            "### Deviation and issue classification\n\nNo deviation.\n\n"
            "### Layer diagnosis and mature-source-Agent comparison\n\nAll layers and the baseline agree.\n\n"
            "### Findings, alternatives and next risk\n\nFindings closed; breadth remains.\n\n"
            "### Decision and rationale\n\nDecision: CONTINUE\n\n"
            "Decision owner: product-architecture-quality\n\n"
            "Decision ref: codex-user-message:sha256:dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd\n\n"
            "The evidence supports continuation.\n"
        )
        result_id = "ITER-008-RESULT-SLICE-001"
        value_metadata = {
            "positive_value_verdict": "PASS",
            "positive_value_metric": "normalized-reuse-cost",
            "positive_value_unit": "basis-points",
            "positive_value_comparison": "at-most",
            "positive_value_threshold": 8000,
            "positive_value_actual": 7500,
            "positive_value_reuse_horizon_questions": 3,
            "mature_source_agent_protocol_digest": "sha256:" + "1" * 64,
            "mature_source_agent_rubric_digest": "sha256:" + "2" * 64,
            "mature_source_agent_cache_policy_digest": "sha256:" + "3" * 64,
            "positive_value_protocol_digest": "sha256:" + "4" * 64,
            "positive_value_freeze_receipt_ref": "codex-user-message:sha256:"
            + "6" * 64,
            "positive_value_case_id": "V-COMP-EARLY-001",
            "positive_value_report_ref": f"{result_id}#positive-value-report",
            "positive_value_adjudication_owner": "user",
            "positive_value_adjudication_receipt_ref": (
                "codex-user-message:sha256:" + "7" * 64
            ),
        }
        value_section, value_digest = positive_value_report_section(
            value_metadata, result_id, "V-COMP-EARLY-001"
        )
        result_body = reflection_body + "\n" + value_section + "\n"
        result = docs_gate.Document(
            iteration_directory / "results/slice-001.md",
            {
                "id": result_id,
                "kind": "iteration-result",
                "status": "accepted",
                "authority": "execution-evidence",
                "iteration": "ITER-008",
                "depends_on": [first.identifier, "ITER-008-VERIFICATION"],
                "product_code_freeze_digest": "sha256:" + "1" * 64,
                "reflection_gate_case_id": "V-REFLECT-001",
                "reflection_gate_status": "PASS",
                "reflection_decision": "CONTINUE",
                "reflection_decision_owner": "product-architecture-quality",
                "reflection_decision_ref": "codex-user-message:sha256:" + "d" * 64,
                "reflection_issue_class": "none",
                "reflection_issue_scope": "none",
                "reflection_report_digest": reflection_report_digest(result_body),
                "critical_assumption_catalog_digest": catalog_digest,
                **value_metadata,
                "positive_value_report_digest": value_digest,
            },
            result_body,
        )
        second = docs_gate.Document(
            iteration_directory / "development-design/SLICE-002.md",
            {
                "id": "ITER-008-SLICE-002",
                "kind": "development-slice",
                "status": "authorized",
                "authority": "current-development",
                "coding_input": True,
                "iteration": "ITER-008",
                "depends_on": [
                    "ITER-008-PROPOSAL",
                    first.identifier,
                    result.identifier,
                ],
                "product_goal_slice_gate_case_ids": ["V-REFLECT-002"],
            },
            "# Slice\n",
        )
        verification = docs_gate.Document(
            iteration_directory / "verification-matrix.md",
            {"id": "ITER-008-VERIFICATION", "kind": "iteration-verification"},
            "| Case | Claim | Level | Frozen input / oracle | Expected | Evidence | Status / blocking meaning |\n"
            "|---|---|---|---|---|---|---|\n"
            f"| V-DIAG-001 | diagnose | architecture / diagnostic | exact result | layer verdicts | {result.identifier}#V-DIAG-001 | PASS / blocking |\n"
            f"| V-COMP-EARLY-001 | compare | product / early comparison | exact result | value verdict | {result.identifier}#V-COMP-EARLY-001 | PASS / blocking |\n"
            f"| V-REFLECT-001 | review | architecture / reflection | exact result | decision | {result.identifier}#V-REFLECT-001 | PASS / blocking |\n",
        )
        binding_owner = "product-architecture-quality"
        manifest = {
            "authorization": {"active_slice": second.identifier},
            "product_goal_alignment": {
                "critical_assumption_ids": ["A1"],
                "critical_assumption_catalog_digest": catalog_digest,
                "positive_value_metric": "normalized-reuse-cost",
                "positive_value_unit": "basis-points",
                "positive_value_comparison": "at-most",
                "positive_value_threshold": 8000,
                "positive_value_reuse_horizon_questions": 3,
                "mature_source_agent_protocol_digest": "sha256:" + "1" * 64,
                "mature_source_agent_rubric_digest": "sha256:" + "2" * 64,
                "mature_source_agent_cache_policy_digest": "sha256:" + "3" * 64,
                "positive_value_protocol_digest": "sha256:" + "4" * 64,
                "positive_value_freeze_receipt_ref": "codex-user-message:sha256:"
                + "6" * 64,
                "positive_value_adjudication_owner": "user",
                "early_comparison_binding": {
                    "case_id": "V-COMP-EARLY-001",
                    "new_slice_ref": first.identifier,
                },
                "reflection_gate_bindings": {
                    "slice_001": {
                        "case_id": "V-REFLECT-001",
                        "new_slice_ref": first.identifier,
                        "assumption_ids": ["A1"],
                        "success_decision": "CONTINUE",
                        "decision_owner": binding_owner,
                    },
                    "slice_002": {
                        "case_id": "V-REFLECT-002",
                        "new_slice_ref": second.identifier,
                        "assumption_ids": ["A1"],
                        "success_decision": "ACCEPT",
                        "decision_owner": binding_owner,
                    },
                },
            },
            "development": {
                "slices": {
                    first.identifier: {
                        "status": "completed",
                        "coding_input": False,
                        "result": result.identifier,
                        "reflection_decision": "CONTINUE",
                        "reflection_prerequisite_result": "none-first-slice",
                        "product_code_freeze_digest": "sha256:" + "1" * 64,
                        "authorized_by": "user",
                        "authorized_at": "2026-08-14T10:00:00+08:00",
                        "authorization_ref": "codex-user-message:sha256:" + "a" * 64,
                    },
                    second.identifier: {
                        "status": "authorized",
                        "coding_input": True,
                        "result": "not-executed",
                        "reflection_decision": "not-executed",
                        "reflection_prerequisite_result": result.identifier,
                        "product_code_freeze_digest": "not-executed",
                        "authorized_by": "user",
                        "authorized_at": "2026-08-14T11:00:00+08:00",
                        "authorization_ref": "codex-user-message:sha256:" + "d" * 64,
                    },
                }
            },
        }
        by_id = {
            item.identifier: item for item in (proposal, first, second, result)
        }
        self.assertEqual(
            docs_gate.validate_product_goal_slice_sequence(
                [first.identifier, second.identifier],
                by_id,
                "manifest.yaml",
                manifest=manifest,
                verification=verification,
            ),
            [],
        )

        changed_proposal = docs_gate.Document(
            proposal.path,
            proposal.metadata,
            proposal.body.replace(
                "A1: query closes", "A1: query may be inferred after the run"
            ),
        )
        changed_catalog_errors = docs_gate.validate_product_goal_slice_sequence(
            [first.identifier, second.identifier],
            {**by_id, proposal.identifier: changed_proposal},
            "manifest.yaml",
            manifest=manifest,
            verification=verification,
        )
        self.assertTrue(
            any(
                "critical_assumption_catalog_digest" in error
                for error in changed_catalog_errors
            ),
            changed_catalog_errors,
        )
        self.assertTrue(
            any("Expected must exactly match" in error for error in changed_catalog_errors),
            changed_catalog_errors,
        )

        reversed_time_manifest = copy.deepcopy(manifest)
        reversed_time_manifest["development"]["slices"][  # type: ignore[index]
            second.identifier
        ]["authorized_at"] = "2026-08-14T09:00:00+08:00"
        reversed_time_errors = docs_gate.validate_product_goal_slice_sequence(
            [first.identifier, second.identifier],
            by_id,
            "manifest.yaml",
            manifest=reversed_time_manifest,
            verification=verification,
        )
        self.assertTrue(
            any("strictly increasing" in error for error in reversed_time_errors),
            reversed_time_errors,
        )

        invalid_time_manifest = copy.deepcopy(manifest)
        invalid_time_manifest["development"]["slices"][  # type: ignore[index]
            second.identifier
        ]["authorized_at"] = "2026-99-99T99:99:99+09:00"
        invalid_time_errors = docs_gate.validate_product_goal_slice_sequence(
            [first.identifier, second.identifier],
            by_id,
            "manifest.yaml",
            manifest=invalid_time_manifest,
            verification=verification,
        )
        self.assertTrue(
            any("real ISO-8601" in error for error in invalid_time_errors),
            invalid_time_errors,
        )

        freeze_receipt = str(value_metadata["positive_value_freeze_receipt_ref"])
        freeze_decision_body = result.body.replace(
            "Decision ref: codex-user-message:sha256:" + "d" * 64,
            "Decision ref: " + freeze_receipt,
        )
        freeze_decision_result = docs_gate.Document(
            result.path,
            {
                **result.metadata,
                "reflection_decision_ref": freeze_receipt,
                "reflection_report_digest": reflection_report_digest(
                    freeze_decision_body
                ),
            },
            freeze_decision_body,
        )
        freeze_decision_manifest = copy.deepcopy(manifest)
        freeze_decision_manifest["development"]["slices"][  # type: ignore[index]
            second.identifier
        ]["authorization_ref"] = freeze_receipt
        freeze_decision_errors = docs_gate.validate_product_goal_slice_sequence(
            [first.identifier, second.identifier],
            {**by_id, result.identifier: freeze_decision_result},
            "manifest.yaml",
            manifest=freeze_decision_manifest,
            verification=verification,
        )
        self.assertTrue(
            any(
                "reflection_decision_ref must use a new user message" in error
                for error in freeze_decision_errors
            ),
            freeze_decision_errors,
        )

        reused_readiness_receipt_manifest = copy.deepcopy(manifest)
        reused_readiness_receipt_manifest["authorization"][  # type: ignore[index]
            "authorization_ref"
        ] = result.metadata["reflection_decision_ref"]
        reused_readiness_receipt_errors = (
            docs_gate.validate_product_goal_slice_sequence(
                [first.identifier, second.identifier],
                by_id,
                "manifest.yaml",
                manifest=reused_readiness_receipt_manifest,
                verification=verification,
            )
        )
        self.assertTrue(
            any(
                "new user message after all prior authorizations" in error
                for error in reused_readiness_receipt_errors
            ),
            reused_readiness_receipt_errors,
        )

        reused_adjudication_metadata = {
            **value_metadata,
            "positive_value_adjudication_receipt_ref": (
                "codex-user-message:sha256:" + "a" * 64
            ),
        }
        reused_adjudication_section, reused_adjudication_digest = (
            positive_value_report_section(
                reused_adjudication_metadata,
                result_id,
                "V-COMP-EARLY-001",
            )
        )
        reused_adjudication_result = docs_gate.Document(
            result.path,
            {
                **result.metadata,
                **reused_adjudication_metadata,
                "positive_value_report_digest": reused_adjudication_digest,
            },
            reflection_body + "\n" + reused_adjudication_section + "\n",
        )
        reused_adjudication_errors = docs_gate.validate_product_goal_slice_sequence(
            [first.identifier, second.identifier],
            {**by_id, result.identifier: reused_adjudication_result},
            "manifest.yaml",
            manifest=manifest,
            verification=verification,
        )
        self.assertTrue(
            any(
                "positive value adjudication must use a new message" in error
                for error in reused_adjudication_errors
            ),
            reused_adjudication_errors,
        )

        completed_second = docs_gate.Document(
            second.path,
            {
                **second.metadata,
                "status": "completed",
                "authority": "historical-development",
                "coding_input": False,
            },
            second.body,
        )
        final_reflection_body = (
            "# Result\n\n"
            "## Architecture reflection and continuation decision\n\n"
            "### Assumption verdicts\n\n"
            "| Assumption | Expected | Exact evidence refs | Verdict | Impact |\n"
            "|---|---|---|---|---|\n"
            "| A1 | query closes | V-FINAL-001 | SUPPORTED | bounded evidence |\n\n"
            "### Deviation and issue classification\n\nNo deviation.\n\n"
            "### Layer diagnosis and mature-source-Agent comparison\n\n"
            "All layers and the baseline agree.\n\n"
            "### Findings, alternatives and next risk\n\n"
            "Findings closed; breadth remains.\n\n"
            "### Decision and rationale\n\nDecision: ACCEPT\n\n"
            "Decision owner: product-architecture-quality\n\n"
            "Decision ref: codex-user-message:sha256:"
            + "d" * 64
            + "\n\nThe final evidence supports acceptance.\n"
        )
        final_result = docs_gate.Document(
            iteration_directory / "results/slice-002.md",
            {
                "id": "ITER-008-RESULT-SLICE-002",
                "kind": "iteration-result",
                "status": "accepted",
                "authority": "execution-evidence",
                "iteration": "ITER-008",
                "depends_on": [
                    completed_second.identifier,
                    "ITER-008-VERIFICATION",
                ],
                "product_code_freeze_digest": "sha256:" + "2" * 64,
                "reflection_gate_case_id": "V-REFLECT-002",
                "reflection_gate_status": "PASS",
                "reflection_decision": "ACCEPT",
                "reflection_decision_owner": "product-architecture-quality",
                "reflection_decision_ref": "codex-user-message:sha256:"
                + "d" * 64,
                "reflection_issue_class": "none",
                "reflection_issue_scope": "none",
                "reflection_report_digest": reflection_report_digest(
                    final_reflection_body
                ),
                "critical_assumption_catalog_digest": catalog_digest,
            },
            final_reflection_body,
        )
        completed_verification = docs_gate.Document(
            verification.path,
            verification.metadata,
            verification.body
            + f"| V-FINAL-001 | final | product / hidden | exact result | answer | {final_result.identifier}#V-FINAL-001 | PASS / blocking |\n"
            + f"| V-REFLECT-002 | review | architecture / reflection | exact result | decision | {final_result.identifier}#V-REFLECT-002 | PASS / blocking |\n",
        )
        completed_manifest = copy.deepcopy(manifest)
        completed_manifest["authorization"]["active_slice"] = "none"  # type: ignore[index]
        completed_manifest["development"]["slices"][  # type: ignore[index]
            second.identifier
        ].update(
            {
                "status": "completed",
                "coding_input": False,
                "result": final_result.identifier,
                "reflection_decision": "ACCEPT",
                "product_code_freeze_digest": "sha256:" + "2" * 64,
            }
        )
        duplicate_final_decision_errors = (
            docs_gate.validate_product_goal_slice_sequence(
                [first.identifier, second.identifier],
                {
                    proposal.identifier: proposal,
                    first.identifier: first,
                    second.identifier: completed_second,
                    result.identifier: result,
                    final_result.identifier: final_result,
                },
                "manifest.yaml",
                manifest=completed_manifest,
                verification=completed_verification,
                require_completed=True,
            )
        )
        self.assertTrue(
            any(
                "reflection_decision_ref must be unique" in error
                or "new user message after all prior authorizations" in error
                for error in duplicate_final_decision_errors
            ),
            duplicate_final_decision_errors,
        )

        missed_early_value = docs_gate.Document(
            result.path,
            {**result.metadata, "positive_value_actual": 8001},
            result.body,
        )
        missed_early_value_errors = docs_gate.validate_product_goal_slice_sequence(
            [first.identifier, second.identifier],
            {**by_id, result.identifier: missed_early_value},
            "manifest.yaml",
            manifest=manifest,
            verification=verification,
        )
        self.assertTrue(
            any(
                "positive_value_actual does not satisfy" in error
                for error in missed_early_value_errors
            ),
            missed_early_value_errors,
        )

        without_result_dependency = docs_gate.Document(
            second.path,
            {
                **second.metadata,
                "depends_on": ["ITER-008-PROPOSAL", first.identifier],
            },
            second.body,
        )
        dependency_errors = docs_gate.validate_product_goal_slice_sequence(
            [first.identifier, second.identifier],
            {**by_id, second.identifier: without_result_dependency},
            "manifest.yaml",
            manifest=manifest,
            verification=verification,
        )
        self.assertTrue(
            any("prior reflection Result" in error for error in dependency_errors),
            dependency_errors,
        )

        reused_authorization_manifest = copy.deepcopy(manifest)
        reused_authorization_manifest["development"]["slices"][  # type: ignore[index]
            second.identifier
        ]["authorization_ref"] = "codex-user-message:sha256:" + "a" * 64
        reused_authorization_errors = docs_gate.validate_product_goal_slice_sequence(
            [first.identifier, second.identifier],
            by_id,
            "manifest.yaml",
            manifest=reused_authorization_manifest,
            verification=verification,
        )
        self.assertTrue(
            any(
                "new user authorization message" in error
                for error in reused_authorization_errors
            ),
            reused_authorization_errors,
        )


if __name__ == "__main__":
    unittest.main()
