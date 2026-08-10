from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import posixpath
import shutil
import sqlite3
import subprocess
from tempfile import TemporaryDirectory
import unittest
import xml.etree.ElementTree as ET


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = (
    REPOSITORY_ROOT
    / "validation"
    / "structure_world_model_iteration_003"
    / "fixtures"
    / "maven-identity"
)
SCHEMA_ROOT = FIXTURE_ROOT.parents[1] / "schema"
LEGACY_ROOT = FIXTURE_ROOT.parents[1] / "legacy"
MANIFEST_PATH = (
    REPOSITORY_ROOT
    / "docs"
    / "project"
    / "iterations"
    / "iteration-003"
    / "manifest.yaml"
)
FIXTURE_DIGEST = "418c223c43ee969b67370f664b8df04b10502553b5a138da09869284736f41d1"
STRUCTURE_SCHEMA_DIGEST = "947bea83028ff6658b01c18dccfd0c1ef028fa5e9a8701a4a0e90d16b8a58ce9"
EVALUATION_CONTEXT_DIGEST = "4fce4ccbcc8ddbe254dc90e8419a178ce37c6fd9ea287e6fad8d15d571161ffd"
CANONICALIZATION_DIGEST = "4fae328bd8c2959cfc1eaaae3b9b27f40d601bf2ffb488bf3abe2cc81c5da6cf"
LEGACY_DATABASE_DIGEST = "081cc8e392d61204e20f97b48b5dfa44e14aa046edd49ce4eeda4a016d3daaff"
LEGACY_REPORT_DIGEST = "28744a5f279461c13672079e04d984bbaf7a1e1a9cbefd136adadaa9bbf6dc71"
LEGACY_GENERATOR_DIGEST = "e9b3bd97fbb184f636ec1a5963f251149fa97fef4ed29a49161601b807670638"
MAVEN_NAMESPACE = {"m": "http://maven.apache.org/POM/4.0.0"}


def _fixture_digest() -> str:
    digest_lines: list[bytes] = []
    for path in sorted(FIXTURE_ROOT.rglob("*")):
        relative_path = path.relative_to(FIXTURE_ROOT).as_posix()
        if path.is_symlink():
            target_digest = hashlib.sha256(
                os.readlink(path).encode("utf-8")
            ).hexdigest()
            digest_lines.append(
                f"symlink:{target_digest}  {relative_path}\n".encode("utf-8")
            )
        elif path.is_file():
            file_digest = hashlib.sha256(path.read_bytes()).hexdigest()
            digest_lines.append(f"{file_digest}  {relative_path}\n".encode("utf-8"))
    return hashlib.sha256(b"".join(digest_lines)).hexdigest()


def _file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _pom(path: str) -> ET.Element:
    return ET.parse(FIXTURE_ROOT / path).getroot()


def _text(root: ET.Element, path: str) -> str | None:
    value = root.findtext(path, namespaces=MAVEN_NAMESPACE)
    return None if value is None else value.strip()


def _coordinates(root: ET.Element) -> tuple[str, str]:
    group_id = _text(root, "m:groupId") or _text(root, "m:parent/m:groupId")
    artifact_id = _text(root, "m:artifactId")
    assert group_id is not None
    assert artifact_id is not None
    return group_id, artifact_id


def _version(root: ET.Element) -> str | None:
    return _text(root, "m:version") or _text(root, "m:parent/m:version")


class Iteration003MavenIdentityFixtureTests(unittest.TestCase):
    def test_fixture_digest_is_frozen(self) -> None:
        self.assertEqual(_fixture_digest(), FIXTURE_DIGEST)

    def test_schema_digests_are_frozen(self) -> None:
        structure_path = SCHEMA_ROOT / "maven-reactor-structure-1.0.0.json"
        evaluation_path = SCHEMA_ROOT / "maven-evaluation-context-1.0.0.json"
        canonicalization_path = SCHEMA_ROOT / "maven-reactor-canonicalization-1.0.0.json"
        self.assertEqual(_file_digest(structure_path), STRUCTURE_SCHEMA_DIGEST)
        self.assertEqual(_file_digest(evaluation_path), EVALUATION_CONTEXT_DIGEST)
        self.assertEqual(_file_digest(canonicalization_path), CANONICALIZATION_DIGEST)

    def test_schema_and_evaluation_context_are_exact(self) -> None:
        structure_path = SCHEMA_ROOT / "maven-reactor-structure-1.0.0.json"
        evaluation_path = SCHEMA_ROOT / "maven-evaluation-context-1.0.0.json"
        canonicalization_path = SCHEMA_ROOT / "maven-reactor-canonicalization-1.0.0.json"
        structure = json.loads(structure_path.read_text(encoding="utf-8"))
        evaluation = json.loads(evaluation_path.read_text(encoding="utf-8"))
        canonicalization = json.loads(canonicalization_path.read_text(encoding="utf-8"))
        self.assertEqual(structure["schema_ref"], "MAVEN-REACTOR-STRUCTURE@1.0.0")
        self.assertEqual(structure["profile_ref"], "MAVEN_REACTOR_STRUCTURE@1")
        self.assertEqual(
            structure["canonicalization_ref"],
            "MAVEN-REACTOR-CANONICALIZATION@1.0.0",
        )
        self.assertEqual(
            structure["fact_kinds"]["relation"]["DEPENDS_ON"]["subject_types"],
            ["SOFTWARE_SYSTEM", "MAVEN_MODULE"],
        )
        self.assertEqual(
            structure["fact_kinds"]["relation"]["CONTAINS_MODULE"]["observation_modality"],
            "RECURSIVE_REACTOR_MEMBERSHIP@1",
        )
        self.assertEqual(
            structure["fact_kinds"]["relation"]["DEPENDS_ON"]["observation_modality"],
            "POM_LOCAL_DECLARED_INTERNAL_DEPENDENCY@1",
        )
        self.assertEqual(
            structure["reactor_semantics"]["reactor_child_module_definition"],
            "recursive_modules_closure_excluding_root_project",
        )
        self.assertEqual(
            structure["reactor_semantics"]["dependency_declaration_scope"],
            "pom_local_dependencies_only_parent_dependencies_not_reattributed",
        )
        self.assertIn(
            "subject_entity_state_id", structure["relation_state_payload_fields"]
        )
        self.assertNotIn("state_digest", structure["relation_state_payload_fields"])
        self.assertNotIn("state_digest", structure["coverage"]["state_payload_fields"])
        self.assertIn(
            "resolved_dependency_gav",
            structure["predicate_state_payload_fields"]["DEPENDS_ON"],
        )
        derivation = structure["canonical_derivation"]
        self.assertEqual(
            derivation["codec_ref"],
            "software_world_model.cross_cutting.canonical_json_bytes/digest_of@ITER-003-FROZEN",
        )
        self.assertTrue(derivation["state_digest_is_derived_not_payload"])
        for vector in derivation["test_vectors"]:
            canonical_bytes = json.dumps(
                vector["input"],
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            ).encode("utf-8")
            self.assertEqual(canonical_bytes.hex(), vector["canonical_utf8_hex"])
            self.assertEqual(
                f"sha256:{hashlib.sha256(canonical_bytes).hexdigest()}",
                vector["digest"],
            )
        self.assertEqual(
            derivation["id_inputs"]["relation_state"],
            ["RELATION_STATE", "relation_root_id", "relation_state_digest"],
        )
        self.assertEqual(
            derivation["state_digest_inputs"]["relation_state"],
            [
                "RELATION_STATE_PAYLOAD",
                "relation_root_id",
                "relation_state_payload_fields_object_with_exact_declared_fields",
                "predicate_state_payload_fields_object_with_exact_declared_fields",
            ],
        )
        self.assertEqual(
            evaluation["context_ref"], "MAVEN-EVALUATION-CONTEXT@1.0.0"
        )
        self.assertEqual(evaluation["active_profiles"], [])
        self.assertEqual(evaluation["external_parent_resolution"], "DISABLED")
        self.assertEqual(evaluation["external_bom_resolution"], "DISABLED")
        self.assertEqual(
            evaluation["unresolved_required_value_policy"], "FAIL_COMPLETE_COVERAGE"
        )
        self.assertEqual(
            evaluation["dependency_management_resolution"],
            "CURRENT_POM_THEN_REACTOR_PARENT_CHAIN",
        )
        self.assertEqual(
            evaluation["build_report_exclusions"]["publication"],
            "EVALUATOR_DIAGNOSTIC_ONLY_NOT_SNAPSHOT_KNOWLEDGE",
        )
        self.assertEqual(
            canonicalization["canonicalization_ref"],
            "MAVEN-REACTOR-CANONICALIZATION@1.0.0",
        )
        self.assertEqual(
            canonicalization["dependency_candidate_resolution"][
                "ga_not_in_reactor_child_set"
            ],
            "EXCLUDE_WITH_REASON_VERSION_NOT_REQUIRED",
        )
        self.assertEqual(
            canonicalization["property_interpolation"][
                "same_pom_duplicate_property_key_policy"
            ],
            "REJECT",
        )
        self.assertEqual(
            canonicalization["property_interpolation"][
                "reactor_parent_override_policy"
            ],
            "CURRENT_POM_WINS_THEN_NEAREST_REACTOR_PARENT_TO_ROOT",
        )

    def test_iteration_002_legacy_snapshot_input_is_frozen_and_readable(self) -> None:
        database_path = LEGACY_ROOT / "iteration-002-legacy.sqlite3"
        report_path = LEGACY_ROOT / "iteration-002-legacy-report.json"
        generator_path = LEGACY_ROOT / "generate_legacy_snapshot.py"
        self.assertEqual(_file_digest(database_path), LEGACY_DATABASE_DIGEST)
        self.assertEqual(_file_digest(report_path), LEGACY_REPORT_DIGEST)
        self.assertEqual(_file_digest(generator_path), LEGACY_GENERATOR_DIGEST)

        report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(report["fixture_ref"], "ITER-002-LEGACY-SNAPSHOT@1")
        self.assertEqual(
            report["generation_commit"],
            "40c65840eaf146360c58ca888b97fc5bd9a0f2e2",
        )
        self.assertEqual(report["database_sha256"], LEGACY_DATABASE_DIGEST)
        self.assertEqual(report["schema_version"], "INITIAL@1")
        self.assertEqual(report["member_count"], 2)
        self.assertEqual(
            {record["source_locators"][0] for record in report["records"]},
            {"src/LegacyOrderService.java:1"},
        )

        connection = sqlite3.connect(
            f"file:{database_path}?mode=ro&immutable=1", uri=True
        )
        try:
            self.assertEqual(connection.execute("PRAGMA integrity_check").fetchone()[0], "ok")
            self.assertEqual(
                connection.execute("SELECT COUNT(*) FROM knw_snapshots").fetchone()[0], 1
            )
            self.assertEqual(
                connection.execute("SELECT COUNT(*) FROM knw_snapshot_members").fetchone()[0],
                2,
            )
        finally:
            connection.close()

    def test_manifest_digests_match_all_frozen_inputs(self) -> None:
        manifest = MANIFEST_PATH.read_text(encoding="utf-8")
        for digest in (
            FIXTURE_DIGEST,
            STRUCTURE_SCHEMA_DIGEST,
            EVALUATION_CONTEXT_DIGEST,
            CANONICALIZATION_DIGEST,
            LEGACY_DATABASE_DIGEST,
            LEGACY_REPORT_DIGEST,
            LEGACY_GENERATOR_DIGEST,
        ):
            self.assertIn(f"sha256:{digest}", manifest)

    def test_valid_fixture_contains_identity_and_dependency_traps(self) -> None:
        root = _pom("valid/pom.xml")
        libraries = _pom("valid/libraries/pom.xml")
        services = _pom("valid/services/pom.xml")
        shared = _pom("valid/libraries/shared-source/pom.xml")
        legacy = _pom("valid/libraries/legacy-source/pom.xml")
        billing = _pom("valid/services/billing-source/pom.xml")

        self.assertEqual(
            [element.text.strip() for element in root.findall("m:modules/m:module", MAVEN_NAMESPACE)],
            ["libraries", "services"],
        )
        self.assertEqual(
            [element.text.strip() for element in libraries.findall("m:modules/m:module", MAVEN_NAMESPACE)],
            ["shared-source", "legacy-source"],
        )
        self.assertEqual(
            [element.text.strip() for element in services.findall("m:modules/m:module", MAVEN_NAMESPACE)],
            ["billing-source"],
        )
        self.assertEqual(_coordinates(shared), ("org.example.shared", "common-lib"))
        self.assertEqual(_coordinates(legacy), ("org.example.legacy", "common-lib"))
        self.assertEqual(_coordinates(billing), ("org.example.services", "billing"))

        direct_dependencies = {
            (_text(item, "m:groupId"), _text(item, "m:artifactId"))
            for item in billing.findall("m:dependencies/m:dependency", MAVEN_NAMESPACE)
        }
        root_direct_dependencies = {
            (_text(item, "m:groupId"), _text(item, "m:artifactId"))
            for item in root.findall("m:dependencies/m:dependency", MAVEN_NAMESPACE)
        }
        managed_dependencies = {
            (_text(item, "m:groupId"), _text(item, "m:artifactId"))
            for item in root.findall(
                "m:dependencyManagement/m:dependencies/m:dependency", MAVEN_NAMESPACE
            )
        }
        self.assertEqual(
            direct_dependencies,
            {
                ("org.example.shared", "common-lib"),
                ("org.example.legacy", "common-lib"),
                ("org.junit.jupiter", "junit-jupiter-api"),
            },
        )
        self.assertEqual(
            root_direct_dependencies,
            {("org.example.shared", "common-lib")},
        )
        legacy_dependency = next(
            item
            for item in billing.findall("m:dependencies/m:dependency", MAVEN_NAMESPACE)
            if _text(item, "m:groupId") == "org.example.legacy"
        )
        self.assertEqual(_text(legacy_dependency, "m:version"), "2.0.0")
        self.assertEqual(
            managed_dependencies,
            {
                ("org.example.shared", "common-lib"),
                ("org.example.legacy", "common-lib"),
            },
        )
        self.assertEqual(
            (_text(billing, "m:parent/m:groupId"), _text(billing, "m:parent/m:artifactId")),
            ("org.example.services", "services-aggregator"),
        )

    def test_invalid_cases_are_real_counterexamples(self) -> None:
        missing = _pom("invalid-missing-module/pom.xml")
        missing_path = _text(missing, "m:modules/m:module")
        self.assertEqual(missing_path, "does-not-exist")
        self.assertFalse((FIXTURE_ROOT / "invalid-missing-module" / missing_path).exists())

        duplicate_one = _pom("invalid-duplicate-ga/one/pom.xml")
        duplicate_two = _pom("invalid-duplicate-ga/two/pom.xml")
        self.assertEqual(_coordinates(duplicate_one), ("org.example.dupe", "same-module"))
        self.assertEqual(_coordinates(duplicate_two), ("org.example.dupe", "same-module"))

        oracle = json.loads((FIXTURE_ROOT / "oracle.json").read_text(encoding="utf-8"))
        self.assertEqual(oracle["fixture_id"], "maven-identity-anti-name-stitch@1")
        self.assertEqual(
            oracle["valid"]["internal_depends_on"],
            [
                {
                    "source": "org.example.services:billing",
                    "target": "org.example.shared:common-lib",
                }
            ],
        )
        self.assertEqual(
            oracle["valid"]["root_project_internal_depends_on"],
            [
                {
                    "source": "org.example.root:structure-fixture",
                    "target": "org.example.shared:common-lib",
                }
            ],
        )
        self.assertEqual(oracle["invalid_missing_module"]["expected"], "REJECT")
        self.assertEqual(oracle["invalid_duplicate_ga"]["expected"], "REJECT")

        expected_invalid = {
            "invalid_missing_module": "MODULE_TARGET_MISSING",
            "invalid_duplicate_ga": "REACTOR_GA_AMBIGUOUS",
            "invalid_same_ga_different_version": "REACTOR_GA_AMBIGUOUS",
            "invalid_relevant_profile": "RELEVANT_PROFILE_UNSUPPORTED",
            "invalid_unresolved_property": "REQUIRED_PROPERTY_UNRESOLVED",
            "invalid_env_property": "DISALLOWED_PROPERTY_SOURCE",
            "invalid_version_range": "VERSION_RANGE_UNSUPPORTED",
            "invalid_external_parent_required": "EXTERNAL_PARENT_REQUIRED",
            "invalid_duplicate_dependency": "DUPLICATE_LOCAL_DEPENDENCY_GA",
            "invalid_property_cycle": "PROPERTY_CYCLE",
            "invalid_reactor_classifier": "REACTOR_DEPENDENCY_SHAPE_UNSUPPORTED",
            "invalid_module_path_escape": "MODULE_PATH_ESCAPES_ROOT",
            "invalid_duplicate_canonical_module": "MODULE_CANONICAL_TARGET_DUPLICATE",
            "invalid_git_symlink": "MODULE_PATH_SYMLINK_UNSUPPORTED",
            "invalid_parent_relative_path_gav_mismatch": "LOCAL_PARENT_GAV_MISMATCH",
            "invalid_duplicate_property": "DUPLICATE_POM_PROPERTY",
        }
        for key, expected_code in expected_invalid.items():
            case_path = FIXTURE_ROOT / key.replace("_", "-") / "pom.xml"
            self.assertTrue(case_path.is_file(), key)
            self.assertEqual(oracle[key]["expected"], "REJECT")
            self.assertEqual(oracle[key]["expected_code"], expected_code)
            self.assertTrue(oracle[key]["current_must_remain_unchanged"])

        same_ga_one = _pom("invalid-same-ga-different-version/one/pom.xml")
        same_ga_two = _pom("invalid-same-ga-different-version/two/pom.xml")
        self.assertEqual(_coordinates(same_ga_one), _coordinates(same_ga_two))
        self.assertEqual({_version(same_ga_one), _version(same_ga_two)}, {"1.0.0", "2.0.0"})

        relevant_profile = _pom("invalid-relevant-profile/pom.xml")
        self.assertIsNotNone(relevant_profile.find("m:profiles/m:profile/m:modules", MAVEN_NAMESPACE))
        unresolved = _pom("invalid-unresolved-property/app/pom.xml")
        self.assertEqual(
            _text(unresolved, "m:dependencies/m:dependency/m:version"),
            "${missing.version}",
        )
        env_property = _pom("invalid-env-property/app/pom.xml")
        self.assertEqual(
            _text(env_property, "m:dependencies/m:dependency/m:version"),
            "${env.SWM_FIXTURE_VERSION}",
        )
        version_range = _pom("invalid-version-range/app/pom.xml")
        self.assertEqual(
            _text(version_range, "m:dependencies/m:dependency/m:version"),
            "[1.0.0,2.0.0)",
        )
        external_child = _pom("invalid-external-parent-required/child/pom.xml")
        self.assertEqual(_text(external_child, "m:groupId"), "org.example.consumer")
        self.assertEqual(_text(external_child, "m:version"), "1.0.0")
        self.assertIsNotNone(external_child.find("m:parent/m:relativePath", MAVEN_NAMESPACE))
        self.assertEqual(
            _text(external_child, "m:dependencies/m:dependency/m:version"),
            "${external.lib.version}",
        )
        external_lib = _pom("invalid-external-parent-required/lib/pom.xml")
        self.assertEqual(
            (*_coordinates(external_lib), _version(external_lib)),
            ("org.example.internal", "external-parent-lib", "1.0.0"),
        )
        duplicate_dependency = _pom("invalid-duplicate-dependency/app/pom.xml")
        self.assertEqual(
            len(duplicate_dependency.findall("m:dependencies/m:dependency", MAVEN_NAMESPACE)),
            2,
        )
        property_cycle = _pom("invalid-property-cycle/app/pom.xml")
        self.assertEqual(_text(property_cycle, "m:properties/m:version.a"), "${version.b}")
        self.assertEqual(_text(property_cycle, "m:properties/m:version.b"), "${version.a}")
        classifier = _pom("invalid-reactor-classifier/app/pom.xml")
        self.assertEqual(
            _text(classifier, "m:dependencies/m:dependency/m:classifier"), "tests"
        )

        escape_root = _pom("invalid-module-path-escape/pom.xml")
        escape_declaration = _text(escape_root, "m:modules/m:module")
        self.assertEqual(escape_declaration, "../path-escape-target")
        escape_case_root = FIXTURE_ROOT / "invalid-module-path-escape"
        escape_target = (escape_case_root / escape_declaration).resolve()
        self.assertNotIn(escape_case_root.resolve(), escape_target.parents)
        self.assertTrue((escape_target / "pom.xml").is_file())

        duplicate_canonical = _pom("invalid-duplicate-canonical-module/pom.xml")
        duplicate_paths = [
            element.text.strip()
            for element in duplicate_canonical.findall(
                "m:modules/m:module", MAVEN_NAMESPACE
            )
        ]
        self.assertEqual(duplicate_paths, ["module-a", "./module-a"])
        self.assertEqual(
            {posixpath.normpath(f"{path}/pom.xml") for path in duplicate_paths},
            {"module-a/pom.xml"},
        )

        mismatch_child = _pom(
            "invalid-parent-relative-path-gav-mismatch/child/pom.xml"
        )
        mismatch_target = _pom(
            "invalid-parent-relative-path-gav-mismatch/actual-parent/pom.xml"
        )
        declared_parent = (
            _text(mismatch_child, "m:parent/m:groupId"),
            _text(mismatch_child, "m:parent/m:artifactId"),
            _text(mismatch_child, "m:parent/m:version"),
        )
        self.assertEqual(
            declared_parent, ("org.example.parent", "declared-parent", "1.0.0")
        )
        self.assertEqual(
            (*_coordinates(mismatch_target), _version(mismatch_target)),
            ("org.example.parent", "actual-parent", "1.0.0"),
        )

        duplicate_property = _pom("invalid-duplicate-property/app/pom.xml")
        duplicate_property_values = [
            (item.text or "").strip()
            for item in duplicate_property.findall(
                "m:properties/m:lib.version", MAVEN_NAMESPACE
            )
        ]
        self.assertEqual(duplicate_property_values, ["1.0.0", "2.0.0"])

    def test_parent_local_dependency_is_not_reattributed_to_children(self) -> None:
        parent = _pom("valid-parent-local-dependency/parent/pom.xml")
        plain_child = _pom(
            "valid-parent-local-dependency/parent/plain-child/pom.xml"
        )
        override_child = _pom(
            "valid-parent-local-dependency/parent/override-child/pom.xml"
        )
        self.assertEqual(
            [
                (_text(item, "m:groupId"), _text(item, "m:artifactId"))
                for item in parent.findall("m:dependencies/m:dependency", MAVEN_NAMESPACE)
            ],
            [("org.example.inheritance", "inheritance-lib")],
        )
        self.assertEqual(
            plain_child.findall("m:dependencies/m:dependency", MAVEN_NAMESPACE), []
        )
        self.assertEqual(_text(parent, "m:properties/m:lib.version"), "9.9.9")
        self.assertEqual(
            _text(override_child, "m:properties/m:lib.version"), "1.0.0"
        )
        self.assertEqual(
            _text(override_child, "m:dependencies/m:dependency/m:version"),
            "${lib.version}",
        )
        oracle = json.loads((FIXTURE_ROOT / "oracle.json").read_text(encoding="utf-8"))
        expected = oracle["valid_parent_local_dependency"]
        self.assertEqual(
            expected["forbidden_reattributed_edges"][0]["source"],
            "org.example.inheritance:plain-child",
        )
        self.assertEqual(
            expected["property_override"]["resolved_dependency_gav"],
            "org.example.inheritance:inheritance-lib:1.0.0",
        )

    def test_symlink_spec_materializes_as_a_git_tree_symlink(self) -> None:
        source = FIXTURE_ROOT / "invalid-git-symlink"
        spec = json.loads((source / "symlink-spec.json").read_text(encoding="utf-8"))
        with TemporaryDirectory() as temporary_directory:
            repository = Path(temporary_directory) / "repository"
            shutil.copytree(source, repository)
            os.symlink(spec["link_target"], repository / spec["link_path"])
            environment = {
                key: value
                for key, value in os.environ.items()
                if not key.startswith("GIT_")
            }
            environment.update(
                {
                    "GIT_CONFIG_GLOBAL": os.devnull,
                    "GIT_CONFIG_NOSYSTEM": "1",
                    "GIT_AUTHOR_NAME": "ITER-003 Fixture",
                    "GIT_AUTHOR_EMAIL": "iteration-003@example.invalid",
                    "GIT_COMMITTER_NAME": "ITER-003 Fixture",
                    "GIT_COMMITTER_EMAIL": "iteration-003@example.invalid",
                    "GIT_AUTHOR_DATE": "2001-01-01T00:00:00+0000",
                    "GIT_COMMITTER_DATE": "2001-01-01T00:00:00+0000",
                }
            )
            subprocess.run(
                ["git", "-C", str(repository), "init", "--quiet", "--object-format=sha1"],
                check=True,
                env=environment,
            )
            subprocess.run(
                ["git", "-C", str(repository), "add", "-A"],
                check=True,
                env=environment,
            )
            subprocess.run(
                [
                    "git",
                    "-c",
                    "commit.gpgSign=false",
                    "-c",
                    "core.hooksPath=/dev/null",
                    "-C",
                    str(repository),
                    "commit",
                    "--quiet",
                    "-m",
                    "materialize symlink counterexample",
                ],
                check=True,
                env=environment,
            )
            revision = subprocess.run(
                ["git", "-C", str(repository), "rev-parse", "HEAD"],
                check=True,
                capture_output=True,
                text=True,
                env=environment,
            ).stdout.strip()
            self.assertEqual(len(revision), 40)
            tree_line = subprocess.run(
                [
                    "git",
                    "-C",
                    str(repository),
                    "ls-tree",
                    revision,
                    spec["link_path"],
                ],
                check=True,
                capture_output=True,
                text=True,
                env=environment,
            ).stdout.strip()
            self.assertTrue(
                tree_line.startswith(f"{spec['required_git_mode']} blob "), tree_line
            )

            settings = Path(temporary_directory) / "settings.xml"
            settings.write_text(
                '<settings xmlns="http://maven.apache.org/SETTINGS/1.2.0"/>\n',
                encoding="utf-8",
            )
            maven = subprocess.run(
                [
                    "mvn",
                    "--batch-mode",
                    "--offline",
                    "--quiet",
                    "--settings",
                    str(settings),
                    f"-Dmaven.repo.local={Path(temporary_directory) / 'repository-cache'}",
                    "-f",
                    str(repository / "pom.xml"),
                    "validate",
                ],
                cwd=repository,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(maven.returncode, 0, maven.stdout + maven.stderr)

    def test_fixture_matches_maven_reactor_validation(self) -> None:
        self.assertIsNotNone(shutil.which("mvn"), "Maven is required by ITER-003 G0")
        with TemporaryDirectory() as temporary_directory:
            temporary_root = Path(temporary_directory)
            settings = temporary_root / "settings.xml"
            settings.write_text(
                '<settings xmlns="http://maven.apache.org/SETTINGS/1.2.0"/>\n',
                encoding="utf-8",
            )
            repository = temporary_root / "repository"

            def validate(case: str) -> subprocess.CompletedProcess[str]:
                case_root = FIXTURE_ROOT / case
                return subprocess.run(
                    [
                        "mvn",
                        "--batch-mode",
                        "--offline",
                        "--quiet",
                        "--settings",
                        str(settings),
                        f"-Dmaven.repo.local={repository}",
                        "-f",
                        str(case_root / "pom.xml"),
                        "validate",
                    ],
                    cwd=case_root,
                    check=False,
                    capture_output=True,
                    text=True,
                )

            valid = validate("valid")
            self.assertEqual(valid.returncode, 0, valid.stdout + valid.stderr)
            inherited = validate("valid-parent-local-dependency")
            self.assertEqual(
                inherited.returncode, 0, inherited.stdout + inherited.stderr
            )
            escaped = validate("invalid-module-path-escape")
            self.assertEqual(escaped.returncode, 0, escaped.stdout + escaped.stderr)
            duplicate_property = validate("invalid-duplicate-property")
            self.assertEqual(
                duplicate_property.returncode,
                0,
                duplicate_property.stdout + duplicate_property.stderr,
            )
            duplicate_canonical = validate("invalid-duplicate-canonical-module")
            self.assertNotEqual(duplicate_canonical.returncode, 0)
            self.assertIn(
                "duplicated in the reactor",
                duplicate_canonical.stdout + duplicate_canonical.stderr,
            )
            parent_mismatch = validate("invalid-parent-relative-path-gav-mismatch")
            self.assertNotEqual(parent_mismatch.returncode, 0)
            self.assertIn(
                "points at wrong local POM",
                parent_mismatch.stdout + parent_mismatch.stderr,
            )
            missing = validate("invalid-missing-module")
            self.assertNotEqual(missing.returncode, 0)
            self.assertIn("does not exist", missing.stdout + missing.stderr)
            duplicate = validate("invalid-duplicate-ga")
            self.assertNotEqual(duplicate.returncode, 0)
            self.assertIn("duplicated in the reactor", duplicate.stdout + duplicate.stderr)
            same_ga_different_version = validate("invalid-same-ga-different-version")
            self.assertEqual(
                same_ga_different_version.returncode,
                0,
                same_ga_different_version.stdout + same_ga_different_version.stderr,
            )


if __name__ == "__main__":
    unittest.main()
