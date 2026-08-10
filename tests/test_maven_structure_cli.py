from __future__ import annotations

from io import StringIO
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from software_world_model.interface.cli import main


ROOT_POM = """\
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>org.example</groupId>
  <artifactId>sample</artifactId>
  <version>1.0.0</version>
  <packaging>pom</packaging>
  <modules><module>module-a</module></modules>
  <dependencies>
    <dependency>
      <groupId>org.example</groupId>
      <artifactId>module-a</artifactId>
      <version>1.0.0</version>
    </dependency>
    <dependency>
      <groupId>org.external</groupId>
      <artifactId>outside</artifactId>
    </dependency>
  </dependencies>
</project>
"""

MODULE_POM = """\
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <parent>
    <groupId>org.example</groupId>
    <artifactId>sample</artifactId>
    <version>1.0.0</version>
    <relativePath>../pom.xml</relativePath>
  </parent>
  <artifactId>module-a</artifactId>
</project>
"""

ROOT_POM_WITHOUT_MODULES = """\
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>org.example</groupId>
  <artifactId>sample</artifactId>
  <version>2.0.0</version>
  <packaging>pom</packaging>
</project>
"""


class MavenStructureCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        self.database = root / "swm.sqlite3"
        self.repository = root / "repository"
        (self.repository / "module-a").mkdir(parents=True)
        (self.repository / "pom.xml").write_text(ROOT_POM, encoding="utf-8")
        (self.repository / "module-a" / "pom.xml").write_text(
            MODULE_POM, encoding="utf-8"
        )
        self._git("init", "-q")
        self._git("config", "user.email", "test@example.com")
        self._git("config", "user.name", "Test")
        self._git("add", ".")
        self._git("commit", "-q", "-m", "fixture")
        self.commit = self._git("rev-parse", "HEAD").strip()
        code, configured = self._cli(
            "configure-system-source",
            "--idempotency-key",
            "configure-maven",
            "--source-target",
            str(self.repository),
            "--paths",
            ".",
            "--display-name",
            "Maven Fixture",
            "--canonical-system-key",
            "fixture:sample",
            "--actor",
            "test",
            "--reason",
            "Maven Structure CLI test",
            "--correlation-ref",
            "maven-cli",
        )
        self.assertEqual(code, 0)
        steps = {item["name"]: item for item in configured["steps"]}
        self.scope_id = steps["CREATE_SCOPE"]["result_reference"]
        self.source_id = steps["REGISTER_SOURCE"]["result_reference"]
        self.binding_id = steps["BIND_SOURCE"]["result_reference"]

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _git(self, *arguments: str) -> str:
        return subprocess.run(
            ("git", "-C", str(self.repository), *arguments),
            check=True,
            stdout=subprocess.PIPE,
            text=True,
        ).stdout

    def _cli(self, *arguments: str) -> tuple[int, dict[str, object]]:
        output = StringIO()
        code = main(["--database", str(self.database), *arguments], stdout=output)
        return code, json.loads(output.getvalue())

    def _build_arguments(
        self,
        *,
        commit: str | None = None,
        idempotency_key: str = "build-maven-a",
        expected_current_snapshot_id: str | None = None,
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
            commit or self.commit,
            "--root-pom",
            "pom.xml",
            "--objective",
            "Build complete exact Maven reactor Structure knowledge",
            "--idempotency-key",
            idempotency_key,
            "--classification",
            "INTERNAL",
            "--actor-ref",
            "test:maven-cli",
            "--correlation-ref",
            "maven-cli",
            "--max-poms",
            "8",
            "--max-calls",
            "16",
            "--tree-page-size",
            "1",
            "--max-bytes-per-call",
            "65536",
        )
        if expected_current_snapshot_id is not None:
            arguments += (
                "--expected-current-snapshot-id",
                expected_current_snapshot_id,
            )
        return arguments

    def test_zero_question_build_prints_complete_auditable_result(self) -> None:
        code, result = self._cli(*self._build_arguments())

        self.assertEqual(code, 0)
        self.assertEqual(result["snapshot"]["revision"], 1)
        self.assertTrue(result["snapshot"]["snapshot_id"].startswith("structure_snapshot_"))
        self.assertTrue(result["snapshot"]["manifest"])
        self.assertTrue(result["snapshot"]["manifest_digest"].startswith("sha256:"))
        self.assertIsNone(result["previous_snapshot_query"])
        self.assertEqual(result["coverage"]["completeness"], "COMPLETE")
        self.assertTrue(result["coverage"]["evidence_locators"])
        self.assertEqual(len(result["entities"]), 2)
        self.assertEqual(len(result["relations"]), 2)
        self.assertTrue(
            all(item["evidence_locators"] for item in result["entities"])
        )
        self.assertTrue(
            all(item["evidence_locators"] for item in result["relations"])
        )
        dependency_decisions = {
            item["resolved_ga"]: item for item in result["dependencies"]
        }
        self.assertEqual(
            dependency_decisions["org.example:module-a"]["resolved_gav"],
            "org.example:module-a:1.0.0",
        )
        self.assertEqual(
            dependency_decisions["org.example:module-a"]["decision"],
            "INTERNAL_DEPENDS_ON",
        )
        self.assertEqual(
            dependency_decisions["org.external:outside"]["exclusion_reason"],
            "GA_NOT_IN_REACTOR_CHILD_SET",
        )
        self.assertEqual(result["deletions"]["removed_members"], [])
        self.assertEqual(result["deletions"]["replaced_members"], [])
        self.assertEqual(result["source_operations"]["count"], 4)
        self.assertEqual(len(result["source_operations"]["operation_ids"]), 4)
        self.assertTrue(result["maven_report"]["complete"])
        self.assertEqual(result["objective"]["description"], (
            "Build complete exact Maven reactor Structure knowledge"
        ))
        self.assertEqual(result["target"]["target_kind"], "REPOSITORY_REVISION")
        self.assertEqual(
            result["target"]["canonical_identity"]["revision"], self.commit
        )
        self.assertIsNone(result["requirement"]["binding"])
        self.assertTrue(result["requirement"]["manual_zero_question_update"])
        self.assertEqual(result["attempt"]["state"], "PUBLISHED")
        self.assertEqual(result["result"]["state"], "PUBLISHED")
        self.assertEqual(result["admission"]["outcome"], "ACCEPT")
        self.assertEqual(result["verifier_assessment"]["outcome"], "PASS")
        self.assertEqual(
            result["verifier_assessment"]["assessment_id"],
            result["admission"]["verifier_assessment_id"],
        )
        self.assertEqual(
            result["verifier_assessment"]["digest"],
            result["admission"]["verifier_assessment_digest"],
        )
        self.assertEqual(
            result["verifier_assessment"]["candidate_digest"],
            result["verifier_assessment"]["verified_candidate_digest"],
        )
        self.assertEqual(result["application_acceptance"]["decision"], "PASS")
        self.assertEqual(
            result["artifact_use"]["purpose"],
            "MAVEN_STRUCTURE_EVIDENCE_PERSISTENCE@1",
        )
        self.assertEqual(
            result["artifact_use"]["confirmation_id"],
            result["result"]["artifact_use_confirmation_id"],
        )
        self.assertEqual(
            result["artifact_use"]["digest"],
            result["result"]["artifact_use_confirmation_digest"],
        )
        self.assertEqual(
            result["artifact_use"]["downstream_candidate_digest"],
            result["admission"]["candidate_digest"],
        )
        self.assertEqual(result["schema"]["registration"]["proposal_ref"], (
            "ITER-003-PROPOSAL"
        ))
        self.assertEqual(result["schema"]["registration"]["review_ref"], (
            "ITER-003-READINESS"
        ))
        self.assertEqual(result["schema"]["availability"]["status"], "AVAILABLE")
        self.assertEqual(result["snapshot"]["schema_adoption_mode"], "INITIAL")
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
            result["admission"]["digest"],
            result["publication"]["admission_digest"],
        )
        self.assertEqual(
            result["application_acceptance"]["digest"],
            result["publication"]["application_acceptance_digest"],
        )
        self.assertEqual(
            result["target_authority"]["canonical_system_key"], "fixture:sample"
        )
        self.assertTrue(
            any(line.startswith("ROOT ") for line in result["maven_report"]["lines"])
        )
        self.assertTrue(
            any(line.startswith("COVERAGE ") for line in result["maven_report"]["lines"])
        )
        audit_prefixes = {line.split(" ", 1)[0] for line in result["audit_lines"]}
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
        external_line = next(
            line
            for line in result["audit_lines"]
            if line.startswith("DEPENDENCY ")
            and "resolved_ga=org.external:outside" in line
        )
        self.assertIn("resolved_version=-", external_line)
        self.assertIn("resolved_gav=-", external_line)
        self.assertTrue(
            all("resolved_gav=" in line and "profile=" in line
                for line in result["audit_lines"]
                if line.startswith("DEPENDENCY "))
        )

    def test_invalid_exact_commit_returns_structured_exit_two(self) -> None:
        code, result = self._cli(*self._build_arguments(commit=self.commit[:8]))

        self.assertEqual(code, 2)
        self.assertEqual(result["error"], "INVALID_ARGUMENT")

    def test_idempotent_replay_returns_the_same_snapshot_and_result(self) -> None:
        first_code, first = self._cli(*self._build_arguments())
        replay_code, replay = self._cli(*self._build_arguments())

        self.assertEqual(first_code, 0)
        self.assertEqual(replay_code, 0)
        self.assertEqual(replay, first)

    def test_replacement_reports_removed_and_replaced_old_states(self) -> None:
        first_code, first = self._cli(*self._build_arguments())
        self.assertEqual(first_code, 0)
        (self.repository / "pom.xml").write_text(
            ROOT_POM_WITHOUT_MODULES, encoding="utf-8"
        )
        self._git("add", "pom.xml")
        self._git("commit", "-q", "-m", "remove module")
        revision_b = self._git("rev-parse", "HEAD").strip()

        second_code, second = self._cli(
            *self._build_arguments(
                commit=revision_b,
                idempotency_key="build-maven-b",
                expected_current_snapshot_id=first["snapshot"]["snapshot_id"],
            )
        )

        self.assertEqual(second_code, 0)
        self.assertEqual(second["snapshot"]["revision"], 2)
        self.assertEqual(second["previous_snapshot_query"], first["snapshot"])
        self.assertNotIn("exclusions", second["previous_snapshot_query"])
        self.assertTrue(
            all(
                set(member) == {"kind", "root_id", "state_id", "state_digest"}
                for member in second["previous_snapshot_query"]["manifest"]
            )
        )
        self.assertEqual(
            [item["kind"] for item in second["deletions"]["replaced_members"]],
            ["ENTITY"],
        )
        self.assertEqual(
            [item["kind"] for item in second["deletions"]["removed_members"]],
            ["ENTITY", "RELATION_FACT", "RELATION_FACT"],
        )
        self.assertEqual(
            len(second["deletions"]["deleted_entity_state_ids"]), 2
        )
        self.assertEqual(
            len(second["deletions"]["deleted_relation_state_ids"]), 2
        )
        history_code, history = self._cli(
            "show-structure-snapshot",
            "--snapshot-id",
            first["snapshot"]["snapshot_id"],
        )
        self.assertEqual(history_code, 0)
        self.assertEqual(history["query"]["mode"], "EXACT_STRUCTURE_SNAPSHOT_ID")
        self.assertTrue(history["query"]["read_only"])
        self.assertEqual(history["snapshot"], first["snapshot"])
        self.assertTrue(
            history["audit_lines"][0].startswith("HISTORICAL_SNAPSHOT_QUERY ")
        )


if __name__ == "__main__":
    unittest.main()
