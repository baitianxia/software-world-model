from __future__ import annotations

from hashlib import sha256
from io import StringIO
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest

from software_world_model.interface.cli import main


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MALL_REPOSITORY = PROJECT_ROOT / "validation-projects" / "mall"
ORACLE_PATH = (
    PROJECT_ROOT
    / "validation"
    / "structure_world_model_iteration_003"
    / "oracles"
    / "mall-structure-1.0.0.json"
)


class Iteration003G1MallIntegrationTests(unittest.TestCase):
    """Exercise the public, zero-question G1 path against the frozen mall Git repo."""

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.database = Path(self.temporary.name) / "iteration-003-g1.sqlite3"
        self.oracle = json.loads(ORACLE_PATH.read_text(encoding="utf-8"))
        self.repository_before = self._repository_signature()
        configured = self._successful_cli(
            "configure-system-source",
            "--idempotency-key",
            "iter-003-g1-configure-mall",
            "--source-target",
            str(MALL_REPOSITORY),
            "--paths",
            ".",
            "--display-name",
            "ITER-003 frozen mall",
            "--canonical-system-key",
            "https://github.com/macrozheng/mall.git",
            "--classification",
            "INTERNAL",
            "--actor",
            "iter-003-g1-test",
            "--reason",
            "verify frozen Maven Structure A-B-A",
            "--correlation-ref",
            "iter-003-g1-mall",
        )
        self._write_report("configure.json", configured)
        steps = {item["name"]: item for item in configured["steps"]}
        self.scope_id = steps["CREATE_SCOPE"]["result_reference"]
        self.source_id = steps["REGISTER_SOURCE"]["result_reference"]
        self.binding_id = steps["BIND_SOURCE"]["result_reference"]
        self.initial_interactions = self._interaction_counts()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_frozen_mall_a_to_b_to_a_is_exact_atomic_and_zero_question(self) -> None:
        revision_a = self.oracle["repository"]["revision_a"]
        revision_b = self.oracle["repository"]["revision_b"]

        a1 = self._successful_cli(
            *self._build_arguments(revision_a, key="iter-003-g1-mall-a1")
        )
        self._write_report("a1.json", a1)
        b = self._successful_cli(
            *self._build_arguments(
                revision_b,
                key="iter-003-g1-mall-b",
                expected_current=a1["snapshot"]["snapshot_id"],
            )
        )
        self._write_report("b.json", b)
        after_b_updates = self._interaction_counts()
        self.assertEqual(
            after_b_updates["counts"],
            {
                "questions": 0,
                "tasks": 0,
                "legacy_answer_read_sessions": 0,
                "structure_read_sessions": 0,
            },
        )

        current_b_session = self._successful_cli(
            "open-structure-read-session",
            "--scope-id",
            self.scope_id,
            "--scope-revision",
            "1",
            "--task-id",
            "task_" + "1" * 32,
            "--task-revision",
            "1",
            "--caller-ref",
            "iter-003-g1-test",
            "--classification",
            "INTERNAL",
            "--idempotency-key",
            "iter-003-g1-current-b",
            "--current",
        )
        ordered_a1_b_session = self._successful_cli(
            "open-structure-read-session",
            "--scope-id",
            self.scope_id,
            "--scope-revision",
            "1",
            "--task-id",
            "task_" + "2" * 32,
            "--task-revision",
            "1",
            "--caller-ref",
            "iter-003-g1-test",
            "--classification",
            "INTERNAL",
            "--idempotency-key",
            "iter-003-g1-ordered-a1-b",
            "--snapshot-id",
            a1["snapshot"]["snapshot_id"],
            "--snapshot-id",
            b["snapshot"]["snapshot_id"],
        )
        self._write_report("read-session-current-b.json", current_b_session)
        self._write_report(
            "read-session-ordered-a1-b.json", ordered_a1_b_session
        )
        self.assertEqual(
            self._interaction_counts()["counts"]["structure_read_sessions"],
            2,
        )

        stale_code, stale = self._cli(
            *self._build_arguments(
                revision_a,
                key="iter-003-g1-mall-stale-cas",
                expected_current=a1["snapshot"]["snapshot_id"],
            )
        )
        self.assertEqual(stale_code, 2)
        self.assertEqual(stale["error"], "REVISION_CONFLICT")
        self.assertNotIn("snapshot", stale)

        # This succeeds only if the failed stale CAS left B as CURRENT.
        a2 = self._successful_cli(
            *self._build_arguments(
                revision_a,
                key="iter-003-g1-mall-a2",
                expected_current=b["snapshot"]["snapshot_id"],
            )
        )
        self._write_report("a2.json", a2)
        after_a2_update = self._interaction_counts()
        self.assertEqual(
            after_a2_update["counts"]["structure_read_sessions"],
            2,
            "the A2 update must not create or replace a read Session",
        )
        historical_b = self._successful_cli(
            "show-structure-snapshot",
            "--snapshot-id",
            b["snapshot"]["snapshot_id"],
        )
        self._write_report("historical-b-after-a2.json", historical_b)
        current_b_after_a2 = self._successful_cli(
            "show-structure-read-session",
            "--session-id",
            current_b_session["session_id"],
        )
        ordered_a1_b_after_a2 = self._successful_cli(
            "show-structure-read-session",
            "--session-id",
            ordered_a1_b_session["session_id"],
        )
        current_a2_session = self._successful_cli(
            "open-structure-read-session",
            "--scope-id",
            self.scope_id,
            "--scope-revision",
            "1",
            "--task-id",
            "task_" + "3" * 32,
            "--task-revision",
            "1",
            "--caller-ref",
            "iter-003-g1-test",
            "--classification",
            "INTERNAL",
            "--idempotency-key",
            "iter-003-g1-current-a2",
            "--current",
        )
        self._write_report(
            "read-session-current-b-after-a2.json", current_b_after_a2
        )
        self._write_report(
            "read-session-ordered-a1-b-after-a2.json",
            ordered_a1_b_after_a2,
        )
        self._write_report("read-session-current-a2.json", current_a2_session)

        self._assert_oracle_revision(a1, self.oracle["revision_a_oracle"])
        self._assert_oracle_revision(b, self.oracle["revision_b_oracle"])
        self._assert_oracle_revision(a2, self.oracle["revision_a_oracle"])
        self._assert_complete_cli_result(a1, expects_history=False)
        self._assert_complete_cli_result(b, expects_history=True)
        self._assert_complete_cli_result(a2, expects_history=True)

        self.assertEqual(a1["snapshot"]["revision"], 1)
        self.assertEqual(b["snapshot"]["revision"], 2)
        self.assertEqual(a2["snapshot"]["revision"], 3)
        self.assertEqual(a1["snapshot"]["schema_adoption_mode"], "INITIAL")
        self.assertEqual(b["snapshot"]["schema_adoption_mode"], "UNCHANGED")
        self.assertEqual(a2["snapshot"]["schema_adoption_mode"], "UNCHANGED")
        self.assertEqual(
            {
                a1["snapshot"]["schema_adoption_digest"],
                b["snapshot"]["schema_adoption_digest"],
                a2["snapshot"]["schema_adoption_digest"],
            },
            {a1["schema"]["adoption"]["digest"]},
        )
        self.assertEqual(b["previous_snapshot_query"], a1["snapshot"])
        self.assertEqual(a2["previous_snapshot_query"], b["snapshot"])
        self.assertEqual(historical_b["snapshot"], b["snapshot"])
        self.assertEqual(
            historical_b["query"],
            {
                "mode": "EXACT_STRUCTURE_SNAPSHOT_ID",
                "read_only": True,
                "snapshot_id": b["snapshot"]["snapshot_id"],
            },
        )
        self.assertEqual(
            b["previous_snapshot_query"]["snapshot_id"],
            a1["snapshot"]["snapshot_id"],
        )
        self.assertNotEqual(
            a1["snapshot"]["snapshot_id"], a2["snapshot"]["snapshot_id"]
        )

        a1_manifest = self._manifest_by_root(a1)
        b_manifest = self._manifest_by_root(b)
        a2_manifest = self._manifest_by_root(a2)
        self.assertEqual(a1_manifest, a2_manifest)
        common_a_b_roots = set(a1_manifest) & set(b_manifest)
        self.assertEqual(common_a_b_roots, set(a1_manifest))
        self.assertTrue(
            all(a1_manifest[key] != b_manifest[key] for key in common_a_b_roots)
        )
        self.assertEqual(
            a1["source_operations"]["operation_ids"],
            a2["source_operations"]["operation_ids"],
        )
        self.assertEqual(
            a1["admission"]["read_set_digest"],
            a2["admission"]["read_set_digest"],
        )
        self.assertNotEqual(
            a1["admission"]["read_set_digest"],
            b["admission"]["read_set_digest"],
        )

        self.assertEqual(a1["coverage"]["root_id"], b["coverage"]["root_id"])
        self.assertEqual(b["coverage"]["root_id"], a2["coverage"]["root_id"])
        self.assertNotEqual(a1["coverage"]["state_id"], b["coverage"]["state_id"])
        self.assertNotEqual(
            a1["coverage"]["state_digest"], b["coverage"]["state_digest"]
        )
        self.assertEqual(a1["coverage"]["state_id"], a2["coverage"]["state_id"])
        self.assertEqual(
            a1["coverage"]["state_digest"], a2["coverage"]["state_digest"]
        )

        self.assertEqual(current_b_after_a2, current_b_session)
        self.assertEqual(ordered_a1_b_after_a2, ordered_a1_b_session)
        self.assertEqual(current_b_session["selection_mode"], "CURRENT")
        self.assertEqual(current_b_session["order"], "SINGLE")
        self.assertEqual(current_b_session["scope_revision"], 1)
        self.assertEqual(
            current_b_session["purpose"],
            "STRUCTURE_EXACT_SNAPSHOT_READ@1",
        )
        self.assertEqual(
            current_b_session["scope_assertion"]["purpose"],
            "KNOWLEDGE_USE@1",
        )
        self.assertEqual(
            current_b_session["scope_assertion"]["outcome"],
            "ELIGIBLE",
        )
        self.assertEqual(
            [item["snapshot_id"] for item in current_b_session["snapshots"]],
            [b["snapshot"]["snapshot_id"]],
        )
        self.assertEqual(
            [item["snapshot_id"] for item in ordered_a1_b_session["snapshots"]],
            [a1["snapshot"]["snapshot_id"], b["snapshot"]["snapshot_id"]],
        )
        self.assertEqual(ordered_a1_b_session["order"], "CALLER_DECLARED")
        self.assertEqual(
            ordered_a1_b_session["purpose"],
            "STRUCTURE_SNAPSHOT_COMPARISON@1",
        )
        self.assertEqual(len(ordered_a1_b_session["context_comparisons"]), 1)
        self.assertEqual(
            ordered_a1_b_session["context_comparisons"][0]["base_snapshot_id"],
            a1["snapshot"]["snapshot_id"],
        )
        self.assertEqual(
            ordered_a1_b_session["context_comparisons"][0]["target_snapshot_id"],
            b["snapshot"]["snapshot_id"],
        )
        self.assertEqual(
            ordered_a1_b_session["context_comparisons"][0]["outcome"],
            "COMPATIBLE",
        )
        self.assertEqual(
            [
                item["snapshot_manifest_digest"]
                for item in ordered_a1_b_session["snapshots"]
            ],
            [
                a1["snapshot"]["manifest_digest"],
                b["snapshot"]["manifest_digest"],
            ],
        )
        self.assertEqual(
            current_a2_session["snapshots"][0]["snapshot_id"],
            a2["snapshot"]["snapshot_id"],
        )
        self.assertNotEqual(
            current_b_session["read_set_digest"],
            current_a2_session["read_set_digest"],
        )
        for session in (
            current_b_session,
            ordered_a1_b_session,
            current_a2_session,
        ):
            self.assertEqual(
                session["payload_policy"],
                {"evidence_payload_fields": 0, "source_payload_fields": 0},
            )

        self._assert_a_to_b_delta(a1, b)
        self._assert_b_to_a_deletions(b, a2)
        paths_a = self._all_simple_dependency_paths(
            a1, "mall-admin", "mall-common"
        )
        paths_b = self._all_simple_dependency_paths(
            b, "mall-admin", "mall-common"
        )

        final_interactions = self._interaction_counts()
        initial_zero_counts = {
            "questions": 0,
            "tasks": 0,
            "legacy_answer_read_sessions": 0,
            "structure_read_sessions": 0,
        }
        self.assertEqual(self.initial_interactions["counts"], initial_zero_counts)
        self.assertEqual(
            final_interactions["counts"],
            {**initial_zero_counts, "structure_read_sessions": 3},
        )
        self.assertTrue(final_interactions["tables"]["app_snapshot_read_sessions"])
        self.assertTrue(final_interactions["tables"]["app_structure_read_sessions"])
        self.assertEqual(self.repository_before, self._repository_signature())

        self._write_report(
            "oracle-comparison-summary.json",
            {
                "schema": "iteration-003-g1-mall-oracle-comparison@1",
                "oracle": {
                    "path": str(ORACLE_PATH.relative_to(PROJECT_ROOT)),
                    "ref": self.oracle["oracle_ref"],
                    "sha256": f"sha256:{sha256(ORACLE_PATH.read_bytes()).hexdigest()}",
                },
                "repository": {
                    "path": str(MALL_REPOSITORY.relative_to(PROJECT_ROOT)),
                    "revision_a": revision_a,
                    "revision_b": revision_b,
                    "unchanged": True,
                },
                "snapshots": {
                    "a1": a1["snapshot"]["snapshot_id"],
                    "b": b["snapshot"]["snapshot_id"],
                    "a2": a2["snapshot"]["snapshot_id"],
                    "distinct_a_snapshots": (
                        a1["snapshot"]["snapshot_id"]
                        != a2["snapshot"]["snapshot_id"]
                    ),
                    "b_readable_from_a2_history": (
                        historical_b["snapshot"] == b["snapshot"]
                    ),
                },
                "counts": {
                    "a1": self._result_counts(a1),
                    "b": self._result_counts(b),
                    "a2": self._result_counts(a2),
                },
                "identity": {
                    "a1_a2_manifest_equal": a1_manifest == a2_manifest,
                    "coverage_root_stable": (
                        a1["coverage"]["root_id"]
                        == b["coverage"]["root_id"]
                        == a2["coverage"]["root_id"]
                    ),
                    "coverage_a_b_state_changed": (
                        a1["coverage"]["state_id"] != b["coverage"]["state_id"]
                    ),
                    "all_common_a_b_states_changed": all(
                        a1_manifest[key] != b_manifest[key]
                        for key in common_a_b_roots
                    ),
                    "a1_a2_read_set_equal": (
                        a1["admission"]["read_set_digest"]
                        == a2["admission"]["read_set_digest"]
                    ),
                },
                "paths": {
                    "a_admin_to_common": paths_a,
                    "b_admin_to_common": paths_b,
                    "added_admin_to_common": sorted(
                        [path for path in paths_b if path not in paths_a]
                    ),
                    "b_admin_to_search": self._all_simple_dependency_paths(
                        b, "mall-admin", "mall-search"
                    ),
                },
                "structure_read_sessions": {
                    "current_b": current_b_session,
                    "ordered_a1_b": ordered_a1_b_session,
                    "current_a2": current_a2_session,
                    "current_b_unchanged_after_a2": (
                        current_b_after_a2 == current_b_session
                    ),
                    "ordered_a1_b_unchanged_after_a2": (
                        ordered_a1_b_after_a2 == ordered_a1_b_session
                    ),
                },
                "stale_current_cas": {
                    "exit_code": stale_code,
                    "error": stale["error"],
                    "current_remained_b": (
                        a2["previous_snapshot_query"] == b["snapshot"]
                    ),
                },
                "interactions": {
                    "initial": self.initial_interactions,
                    "final": final_interactions,
                },
                "reports_complete": all(
                    result["maven_report"]["complete"] for result in (a1, b, a2)
                ),
                "oracle_comparison": "PASS",
            },
        )

    def _build_arguments(
        self,
        revision: str,
        *,
        key: str,
        expected_current: str | None = None,
    ) -> tuple[str, ...]:
        arguments = (
            "build-maven-structure",
            "--scope-id",
            self.scope_id,
            "--scope-revision",
            "1",
            "--source-id",
            self.source_id,
            "--source-revision",
            "1",
            "--binding-id",
            self.binding_id,
            "--binding-revision",
            "1",
            "--repository-revision",
            revision,
            "--root-pom",
            "pom.xml",
            "--objective",
            "Build frozen mall Maven reactor Structure knowledge",
            "--idempotency-key",
            key,
            "--classification",
            "INTERNAL",
            "--actor-ref",
            "iter-003-g1-test",
            "--correlation-ref",
            "iter-003-g1-mall",
            "--max-poms",
            "32",
            "--max-calls",
            "32",
            "--tree-page-size",
            "500",
            "--max-bytes-per-call",
            "1000000",
        )
        if expected_current is not None:
            arguments += ("--expected-current-snapshot-id", expected_current)
        return arguments

    def _assert_oracle_revision(
        self, result: dict[str, object], oracle_revision: dict[str, object]
    ) -> None:
        entities = result["entities"]
        relations = result["relations"]
        expected_entity_count = 1 + len(oracle_revision["reactor_child_module_gavs"])
        expected_relation_count = (
            oracle_revision["contains_module_count"]
            + len(oracle_revision["internal_depends_on_gav"])
        )
        self.assertEqual(len(entities), expected_entity_count)
        self.assertEqual(len(relations), expected_relation_count)

        gav_by_root = self._gav_by_root(result)
        system_entities = [
            item for item in entities if item["entity_type"] == "SOFTWARE_SYSTEM"
        ]
        module_entities = [
            item for item in entities if item["entity_type"] == "MAVEN_MODULE"
        ]
        self.assertEqual(len(system_entities), 1)
        self.assertEqual(
            gav_by_root[system_entities[0]["root_id"]], self.oracle["root_project"]
        )
        self.assertEqual(
            {gav_by_root[item["root_id"]] for item in module_entities},
            set(oracle_revision["reactor_child_module_gavs"]),
        )

        actual_contains = {
            (gav_by_root[item["source_root_id"]], gav_by_root[item["target_root_id"]])
            for item in relations
            if item["predicate"] == "CONTAINS_MODULE"
        }
        expected_contains = {
            (self.oracle["root_project"], child)
            for child in oracle_revision["reactor_child_module_gavs"]
        }
        self.assertEqual(actual_contains, expected_contains)

        actual_dependencies = {
            (gav_by_root[item["source_root_id"]], gav_by_root[item["target_root_id"]])
            for item in relations
            if item["predicate"] == "DEPENDS_ON"
        }
        expected_dependencies = {
            tuple(item) for item in oracle_revision["internal_depends_on_gav"]
        }
        self.assertEqual(actual_dependencies, expected_dependencies)

        self.assertEqual(
            self._all_simple_dependency_paths(
                result, "mall-admin", "mall-common"
            ),
            oracle_revision["admin_to_common_all_simple_paths"],
        )
        if "admin_to_search_all_simple_paths" in oracle_revision:
            self.assertEqual(
                self._all_simple_dependency_paths(
                    result, "mall-admin", "mall-search"
                ),
                oracle_revision["admin_to_search_all_simple_paths"],
            )
        if "root_locally_declares_security_dependency" in oracle_revision:
            self.assertFalse(
                (
                    self.oracle["root_project"],
                    "com.macro.mall:mall-security:1.0-SNAPSHOT",
                )
                in actual_dependencies
            )

    def _assert_a_to_b_delta(
        self, revision_a: dict[str, object], revision_b: dict[str, object]
    ) -> None:
        gav_a = self._gav_by_root(revision_a)
        gav_b = self._gav_by_root(revision_b)
        entity_roots_a = set(gav_a)
        entity_roots_b = set(gav_b)
        expected_added_gavs = set(
            self.oracle["revision_b_oracle"]["reactor_child_module_gavs"]
        ) - set(self.oracle["revision_a_oracle"]["reactor_child_module_gavs"])
        self.assertEqual(
            {gav_b[root] for root in entity_roots_b - entity_roots_a},
            expected_added_gavs,
        )
        self.assertFalse(entity_roots_a - entity_roots_b)

        relations_a = self._relation_definitions(revision_a)
        relations_b = self._relation_definitions(revision_b)
        expected_added_relations = {
            ("CONTAINS_MODULE", self.oracle["root_project"], gav)
            for gav in expected_added_gavs
        } | {
            ("DEPENDS_ON", source, target)
            for source, target in (
                set(
                    map(
                        tuple,
                        self.oracle["revision_b_oracle"]["internal_depends_on_gav"],
                    )
                )
                - set(
                    map(
                        tuple,
                        self.oracle["revision_a_oracle"]["internal_depends_on_gav"],
                    )
                )
            )
        }
        self.assertEqual(relations_b - relations_a, expected_added_relations)
        self.assertFalse(relations_a - relations_b)

        paths_a = self._all_simple_dependency_paths(
            revision_a, "mall-admin", "mall-common"
        )
        paths_b = self._all_simple_dependency_paths(
            revision_b, "mall-admin", "mall-common"
        )
        self.assertEqual(
            sorted(path for path in paths_b if path not in paths_a),
            self.oracle["a_to_b"]["added_admin_to_common_paths"],
        )

        root_keys_a = set(self._manifest_by_root(revision_a))
        root_keys_b = set(self._manifest_by_root(revision_b))
        self.assertEqual(len(root_keys_b - root_keys_a), 1 + len(expected_added_relations))
        self.assertFalse(root_keys_a - root_keys_b)

    def _assert_b_to_a_deletions(
        self, revision_b: dict[str, object], revision_a2: dict[str, object]
    ) -> None:
        b_manifest = self._manifest_by_root(revision_b)
        a2_manifest = self._manifest_by_root(revision_a2)
        removed_keys = set(b_manifest) - set(a2_manifest)
        replaced_keys = {
            key
            for key in set(b_manifest) & set(a2_manifest)
            if b_manifest[key] != a2_manifest[key]
        }
        actual_removed = {
            (item["kind"], item["root_id"]): (
                item["state_id"],
                item["state_digest"],
            )
            for item in revision_a2["deletions"]["removed_members"]
        }
        actual_replaced = {
            (item["kind"], item["root_id"]): (
                item["state_id"],
                item["state_digest"],
            )
            for item in revision_a2["deletions"]["replaced_members"]
        }
        self.assertEqual(actual_removed, {key: b_manifest[key] for key in removed_keys})
        self.assertEqual(
            actual_replaced, {key: b_manifest[key] for key in replaced_keys}
        )

        retired = {**actual_removed, **actual_replaced}
        self.assertEqual(
            set(revision_a2["deletions"]["deleted_entity_state_ids"]),
            {value[0] for key, value in retired.items() if key[0] == "ENTITY"},
        )
        self.assertEqual(
            set(revision_a2["deletions"]["deleted_relation_state_ids"]),
            {
                value[0]
                for key, value in retired.items()
                if key[0] == "RELATION_FACT"
            },
        )
        self.assertEqual(
            revision_a2["deletions"]["deleted_literal_state_ids"], []
        )

    def _assert_complete_cli_result(
        self, result: dict[str, object], *, expects_history: bool
    ) -> None:
        self.assertTrue(result["maven_report"]["complete"])
        self.assertEqual(
            result["previous_snapshot_query"] is not None, expects_history
        )
        self.assertTrue(result["snapshot"]["manifest"])
        self.assertEqual(result["coverage"]["completeness"], "COMPLETE")
        self.assertTrue(result["coverage"]["evidence_locators"])
        self.assertTrue(result["dependencies"])
        self.assertTrue(result["exclusions"])
        self.assertEqual(result["target"]["target_kind"], "REPOSITORY_REVISION")
        self.assertIsNone(result["requirement"]["binding"])
        self.assertEqual(result["attempt"]["state"], "PUBLISHED")
        self.assertEqual(result["result"]["state"], "PUBLISHED")
        self.assertEqual(result["admission"]["outcome"], "ACCEPT")
        self.assertEqual(result["application_acceptance"]["decision"], "PASS")
        self.assertEqual(
            result["artifact_use"]["purpose"],
            "MAVEN_STRUCTURE_EVIDENCE_PERSISTENCE@1",
        )
        self.assertEqual(
            result["artifact_use"]["downstream_candidate_digest"],
            result["admission"]["candidate_digest"],
        )
        self.assertEqual(result["schema"]["availability"]["status"], "AVAILABLE")
        self.assertEqual(
            result["schema"]["registration"]["digest"],
            result["admission"]["schema_registration_digest"],
        )
        self.assertEqual(
            result["schema"]["registration"]["digest"],
            result["snapshot"]["schema_registration_digest"],
        )
        self.assertEqual(
            result["schema"]["availability"]["digest"],
            result["admission"]["schema_availability_digest"],
        )
        self.assertEqual(
            result["schema"]["availability"]["digest"],
            result["snapshot"]["schema_availability_digest"],
        )
        self.assertEqual(
            result["schema"]["adoption"]["digest"],
            result["snapshot"]["schema_adoption_digest"],
        )
        self.assertEqual(
            result["admission"]["admission_id"],
            result["publication"]["admission_id"],
        )
        self.assertEqual(
            result["application_acceptance"]["digest"],
            result["publication"]["application_acceptance_digest"],
        )
        self.assertEqual(
            result["target_authority"]["canonical_system_key"],
            "https://github.com/macrozheng/mall.git",
        )
        self.assertEqual(
            set(result["deletions"]),
            {
                "removed_members",
                "replaced_members",
                "deleted_entity_state_ids",
                "deleted_relation_state_ids",
                "deleted_literal_state_ids",
                "digest",
            },
        )
        for entity in result["entities"]:
            self.assertTrue(entity["root_id"].startswith("entity_root_"))
            self.assertTrue(entity["state_id"].startswith("entity_state_"))
            self.assertTrue(entity["root_digest"].startswith("sha256:"))
            self.assertTrue(entity["state_digest"].startswith("sha256:"))
            self.assertTrue(entity["root_fields"])
            self.assertTrue(entity["state_fields"])
            self.assertTrue(entity["evidence_locators"])
        for relation in result["relations"]:
            self.assertTrue(relation["fact_root_id"].startswith("relation_root_"))
            self.assertTrue(relation["fact_state_id"].startswith("relation_state_"))
            self.assertTrue(relation["fact_root_digest"].startswith("sha256:"))
            self.assertTrue(relation["fact_state_digest"].startswith("sha256:"))
            self.assertTrue(relation["predicate_state_fields"])
            self.assertTrue(relation["evidence_locators"])
        line_prefixes = {
            line.split(" ", 1)[0] for line in result["maven_report"]["lines"]
        }
        self.assertTrue(
            {"ROOT", "MODULE", "RELATION", "DEPENDENCY", "COVERAGE"}
            <= line_prefixes
        )
        audit_prefixes = {
            line.split(" ", 1)[0] for line in result["audit_lines"]
        }
        self.assertTrue(
            {
                "SNAPSHOT",
                "SCHEMA",
                "OBJECTIVE",
                "TARGET",
                "REQUIREMENT",
                "ATTEMPT",
                "RESULT",
                "ADMISSION",
                "VERIFIER_ASSESSMENT",
                "ARTIFACT_USE",
                "ENTITY",
                "RELATION",
                "COVERAGE",
                "DEPENDENCY",
                "DELETION",
                "OLD_SNAPSHOT_QUERY",
            }
            <= audit_prefixes
        )

    def _gav_by_root(self, result: dict[str, object]) -> dict[str, str]:
        projected = {}
        for entity in result["entities"]:
            root_fields = entity["root_fields"]
            state_fields = entity["state_fields"]
            group_id = root_fields.get(
                "effective_group_id", state_fields.get("effective_group_id")
            )
            artifact_id = root_fields.get("artifact_id", state_fields.get("artifact_id"))
            projected[entity["root_id"]] = (
                f"{group_id}:{artifact_id}:{state_fields['effective_version']}"
            )
        return projected

    def _relation_definitions(
        self, result: dict[str, object]
    ) -> set[tuple[str, str, str]]:
        gav_by_root = self._gav_by_root(result)
        return {
            (
                item["predicate"],
                gav_by_root[item["source_root_id"]],
                gav_by_root[item["target_root_id"]],
            )
            for item in result["relations"]
        }

    def _all_simple_dependency_paths(
        self,
        result: dict[str, object],
        source_artifact_id: str,
        target_artifact_id: str,
    ) -> list[list[str]]:
        """Independently project and traverse only typed DEPENDS_ON facts."""

        gav_by_root = self._gav_by_root(result)
        artifact_by_root = {
            root_id: gav.split(":", 2)[1]
            for root_id, gav in gav_by_root.items()
        }
        adjacency: dict[str, set[str]] = {}
        for relation in result["relations"]:
            if relation["predicate"] != "DEPENDS_ON":
                continue
            source = artifact_by_root[relation["source_root_id"]]
            target = artifact_by_root[relation["target_root_id"]]
            adjacency.setdefault(source, set()).add(target)

        paths: list[list[str]] = []

        def visit(node: str, path: list[str]) -> None:
            if node == target_artifact_id:
                paths.append(path)
                return
            for successor in sorted(adjacency.get(node, ())):
                if successor not in path:
                    visit(successor, [*path, successor])

        visit(source_artifact_id, [source_artifact_id])
        return sorted(paths)

    def _manifest_by_root(
        self, result: dict[str, object]
    ) -> dict[tuple[str, str], tuple[str, str]]:
        return {
            (item["kind"], item["root_id"]): (
                item["state_id"],
                item["state_digest"],
            )
            for item in result["snapshot"]["manifest"]
        }

    def _result_counts(self, result: dict[str, object]) -> dict[str, int]:
        return {
            "entities": len(result["entities"]),
            "relations": len(result["relations"]),
            "dependencies": len(result["dependencies"]),
            "exclusions": len(result["exclusions"]),
            "source_operations": result["source_operations"]["count"],
        }

    def _interaction_counts(self) -> dict[str, object]:
        connection = sqlite3.connect(self.database)
        try:
            table_names = {
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }

            def count(table_name: str) -> int:
                if table_name not in table_names:
                    return 0
                return connection.execute(
                    f'SELECT COUNT(*) FROM "{table_name}"'
                ).fetchone()[0]

            question_tables = sorted(
                name for name in table_names if "question" in name.lower()
            )
            return {
                "counts": {
                    "questions": sum(count(name) for name in question_tables),
                    "tasks": count("app_tasks"),
                    "legacy_answer_read_sessions": count(
                        "app_snapshot_read_sessions"
                    ),
                    "structure_read_sessions": count(
                        "app_structure_read_sessions"
                    ),
                },
                "tables": {
                    "question_tables": question_tables,
                    "app_tasks": "app_tasks" in table_names,
                    "app_snapshot_read_sessions": (
                        "app_snapshot_read_sessions" in table_names
                    ),
                    "app_structure_read_sessions": (
                        "app_structure_read_sessions" in table_names
                    ),
                },
            }
        finally:
            connection.close()

    def _repository_signature(self) -> dict[str, str]:
        paths = [MALL_REPOSITORY / ".git" / "HEAD", MALL_REPOSITORY / ".git" / "index"]
        module_names = set(self.oracle["revision_a_oracle"]["reactor_child_modules"])
        module_names.update(self.oracle["revision_b_oracle"]["reactor_child_modules"])
        paths.extend(MALL_REPOSITORY / name / "pom.xml" for name in module_names)
        paths.append(MALL_REPOSITORY / "pom.xml")
        return {
            str(path.relative_to(MALL_REPOSITORY)): sha256(path.read_bytes()).hexdigest()
            for path in sorted(paths)
        }

    def _cli(self, *arguments: str) -> tuple[int, dict[str, object]]:
        output = StringIO()
        code = main(["--database", str(self.database), *arguments], stdout=output)
        return code, json.loads(output.getvalue())

    def _successful_cli(self, *arguments: str) -> dict[str, object]:
        code, payload = self._cli(*arguments)
        self.assertEqual(code, 0, payload)
        return payload

    def _write_report(self, name: str, payload: dict[str, object]) -> None:
        configured = os.environ.get("ITER003_G1_REPORT_DIR")
        if configured is None:
            return
        report_directory = Path(configured)
        report_directory.mkdir(parents=True, exist_ok=True)
        (report_directory / name).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


if __name__ == "__main__":
    unittest.main()
