"""Independent checks for ITER-003's pre-development validation assets.

These tests deliberately do not import a product parser, query engine, or model.
They verify that the frozen inputs and their independent oracle are internally
consistent before an implementation is authorized.
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import posixpath
import re
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
import xml.etree.ElementTree as ET

from scripts.docs import safe_load_manifest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
VALIDATION_ROOT = REPOSITORY_ROOT / "validation" / "structure_world_model_iteration_003"
MANIFEST_PATH = (
    REPOSITORY_ROOT
    / "docs"
    / "project"
    / "iterations"
    / "iteration-003"
    / "manifest.yaml"
)
MALL_REPOSITORY = REPOSITORY_ROOT / "validation-projects" / "mall"
MALL_ORACLE_PATH = VALIDATION_ROOT / "oracles" / "mall-structure-1.0.0.json"
GENERATOR_PATH = VALIDATION_ROOT / "metamorphic" / "generate_reactor.py"
PRODUCT_SUITE_PATH = VALIDATION_ROOT / "questions" / "product-suite-1.0.0.json"
PRODUCT_INPUT_SUITE_PATH = (
    VALIDATION_ROOT / "questions" / "product-input-suite-1.0.0.json"
)
DIRECT_PROTOCOL_PATH = (
    VALIDATION_ROOT / "questions" / "direct-baseline-protocol-1.0.1.json"
)
MATURE_PROTOCOL_PATH = (
    VALIDATION_ROOT / "questions" / "mature-agent-baseline-protocol-1.0.1.json"
)
MATURE_ANSWER_SCHEMA_PATH = (
    VALIDATION_ROOT / "questions" / "mature-agent-answer-schema-1.0.0.json"
)
DIRECT_IMPLEMENTATION_PATH = (
    REPOSITORY_ROOT / "validation" / "product_holdout_iteration_002" / "direct_answer.py"
)
MAVEN_NAMESPACE = {"m": "http://maven.apache.org/POM/4.0.0"}
PROPERTY_EXPRESSION = re.compile(r"\$\{([^{}]+)\}")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _fixture_digest(path: Path) -> str:
    lines: list[bytes] = []
    for child in sorted(path.rglob("*")):
        relative = child.relative_to(path).as_posix()
        if child.is_symlink():
            target_digest = hashlib.sha256(
                os.readlink(child).encode("utf-8")
            ).hexdigest()
            lines.append(f"symlink:{target_digest}  {relative}\n".encode("utf-8"))
        elif child.is_file():
            lines.append(f"{_sha256(child)}  {relative}\n".encode("utf-8"))
    return hashlib.sha256(b"".join(lines)).hexdigest()


def _reject_duplicate_json_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _load_json(path: Path) -> dict[str, object]:
    value = json.loads(
        path.read_text(encoding="utf-8"), object_pairs_hook=_reject_duplicate_json_keys
    )
    if not isinstance(value, dict):
        raise AssertionError(f"{path} must contain a JSON object")
    return value


def _resolve_json_pointer(document: object, pointer: str) -> object:
    if pointer == "":
        return document
    if not pointer.startswith("/"):
        raise AssertionError(f"JSON pointer must be absolute: {pointer}")
    current = document
    for encoded_token in pointer[1:].split("/"):
        token = encoded_token.replace("~1", "/").replace("~0", "~")
        if isinstance(current, dict):
            if token not in current:
                raise AssertionError(f"JSON pointer token not found: {pointer} at {token}")
            current = current[token]
        elif isinstance(current, list):
            if not token.isdigit():
                raise AssertionError(f"JSON pointer array token is not an index: {pointer}")
            index = int(token)
            if index >= len(current):
                raise AssertionError(f"JSON pointer index out of bounds: {pointer}")
            current = current[index]
        else:
            raise AssertionError(f"JSON pointer descends through scalar: {pointer}")
    return current


def _manifest_external_inputs() -> dict[str, dict[str, object]]:
    manifest = safe_load_manifest(MANIFEST_PATH.read_text(encoding="utf-8"))
    external_inputs = manifest.get("external_inputs")
    if not isinstance(external_inputs, dict):
        raise AssertionError("manifest.external_inputs must be a mapping")
    for name, value in external_inputs.items():
        if not isinstance(value, dict):
            raise AssertionError(f"external_inputs.{name} must be a mapping")
    return external_inputs  # type: ignore[return-value]


def _run(
    arguments: list[str],
    *,
    cwd: Path | None = None,
    check: bool = True,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        arguments,
        cwd=cwd,
        check=check,
        text=True,
        capture_output=True,
        env=env,
    )


def _git(repository: Path, *arguments: str, check: bool = True) -> str:
    completed = _run(["git", "-C", str(repository), *arguments], check=check)
    if check:
        return completed.stdout.strip()
    return completed.stdout.strip()


def _xml_text(root: ET.Element, path: str) -> str | None:
    value = root.findtext(path, namespaces=MAVEN_NAMESPACE)
    return value.strip() if value is not None else None


def _pom_at(revision: str, path: PurePosixPath) -> ET.Element:
    completed = _run(
        ["git", "-C", str(MALL_REPOSITORY), "show", f"{revision}:{path.as_posix()}"]
    )
    return ET.fromstring(completed.stdout)


def _normalize_posix_path(path: PurePosixPath) -> PurePosixPath:
    return PurePosixPath(posixpath.normpath(path.as_posix()))


def _module_pom_path(parent_pom: PurePosixPath, module: str) -> PurePosixPath:
    return _normalize_posix_path(parent_pom.parent / module / "pom.xml")


def _interpolate(value: str, properties: dict[str, str], label: str) -> str:
    current = value
    for _ in range(32):
        matches = list(PROPERTY_EXPRESSION.finditer(current))
        if not matches:
            return current
        missing = [match.group(1) for match in matches if match.group(1) not in properties]
        if missing:
            raise AssertionError(f"unresolved properties in {label}: {sorted(set(missing))}")
        current = PROPERTY_EXPRESSION.sub(
            lambda match: properties[match.group(1)], current
        )
    raise AssertionError(f"property expansion exceeded limit in {label}")


def _all_simple_paths(
    edges: set[tuple[str, str]], source: str, target: str
) -> list[list[str]]:
    adjacency: dict[str, list[str]] = {}
    for left, right in sorted(edges):
        adjacency.setdefault(left, []).append(right)
    results: list[list[str]] = []

    def visit(current: str, route: list[str]) -> None:
        if current == target:
            results.append(route)
            return
        for following in adjacency.get(current, []):
            if following not in route:
                visit(following, [*route, following])

    visit(source, [source])
    return sorted(results)


def _derive_mall_structure(revision: str) -> dict[str, object]:
    """Derive just the frozen oracle's POM-local relation modality from raw Git POMs."""

    root_path = PurePosixPath("pom.xml")
    root = _pom_at(revision, root_path)
    root_group = _xml_text(root, "m:groupId")
    root_artifact = _xml_text(root, "m:artifactId")
    root_version = _xml_text(root, "m:version")
    if not all((root_group, root_artifact, root_version)):
        raise AssertionError("mall root must declare a complete GAV")

    module_poms: list[PurePosixPath] = []
    pending = [root_path]
    seen: set[PurePosixPath] = set()
    poms: dict[PurePosixPath, ET.Element] = {}
    while pending:
        pom_path = pending.pop()
        if pom_path in seen:
            continue
        seen.add(pom_path)
        pom = _pom_at(revision, pom_path)
        poms[pom_path] = pom
        for element in pom.findall("m:modules/m:module", MAVEN_NAMESPACE):
            if element.text is None:
                raise AssertionError(f"empty module declaration in {pom_path}")
            child_path = _module_pom_path(pom_path, element.text.strip())
            module_poms.append(child_path)
            pending.append(child_path)

    def local_parent_path(pom_path: PurePosixPath) -> PurePosixPath | None:
        pom = poms[pom_path]
        parent = pom.find("m:parent", MAVEN_NAMESPACE)
        if parent is None:
            return None
        relative_element = parent.find("m:relativePath", MAVEN_NAMESPACE)
        if relative_element is not None and not (relative_element.text or "").strip():
            return None
        relative = (
            (relative_element.text or "").strip()
            if relative_element is not None
            else "../pom.xml"
        )
        candidate = _normalize_posix_path(pom_path.parent / relative)
        return candidate if candidate in poms else None

    effective_gav_cache: dict[PurePosixPath, tuple[str, str, str]] = {}
    properties_cache: dict[PurePosixPath, dict[str, str]] = {}

    def effective_gav(pom_path: PurePosixPath) -> tuple[str, str, str]:
        cached = effective_gav_cache.get(pom_path)
        if cached is not None:
            return cached
        pom = poms[pom_path]
        parent_path = local_parent_path(pom_path)
        parent_gav = effective_gav(parent_path) if parent_path is not None else None
        group = _xml_text(pom, "m:groupId") or (parent_gav[0] if parent_gav else None)
        artifact = _xml_text(pom, "m:artifactId")
        version = _xml_text(pom, "m:version") or (parent_gav[2] if parent_gav else None)
        if not group or not artifact or not version:
            raise AssertionError(f"incomplete effective GAV in {pom_path}")
        provisional = {"project.groupId": group, "project.artifactId": artifact}
        if parent_gav:
            provisional.update(
                {
                    "project.parent.groupId": parent_gav[0],
                    "project.parent.artifactId": parent_gav[1],
                    "project.parent.version": parent_gav[2],
                }
            )
        group = _interpolate(group, provisional, f"{pom_path} groupId")
        artifact = _interpolate(artifact, provisional, f"{pom_path} artifactId")
        provisional.update(
            {
                "project.groupId": group,
                "pom.groupId": group,
                "project.artifactId": artifact,
                "pom.artifactId": artifact,
            }
        )
        version = _interpolate(version, provisional, f"{pom_path} version")
        result = (group, artifact, version)
        effective_gav_cache[pom_path] = result
        if parent_path is not None:
            declared_parent = (
                _xml_text(pom, "m:parent/m:groupId"),
                _xml_text(pom, "m:parent/m:artifactId"),
                _xml_text(pom, "m:parent/m:version"),
            )
            if declared_parent != parent_gav:
                raise AssertionError(
                    f"local parent GAV mismatch in {pom_path}: {declared_parent} != {parent_gav}"
                )
        return result

    def effective_properties(pom_path: PurePosixPath) -> dict[str, str]:
        cached = properties_cache.get(pom_path)
        if cached is not None:
            return cached
        parent_path = local_parent_path(pom_path)
        values = dict(effective_properties(parent_path)) if parent_path is not None else {}
        properties_element = poms[pom_path].find("m:properties", MAVEN_NAMESPACE)
        if properties_element is not None:
            local_keys: set[str] = set()
            for child in properties_element:
                key = child.tag.rsplit("}", 1)[-1]
                if key in local_keys:
                    raise AssertionError(f"duplicate property {key} in {pom_path}")
                local_keys.add(key)
                values[key] = (child.text or "").strip()
        group, artifact, version = effective_gav(pom_path)
        values.update(
            {
                "project.groupId": group,
                "pom.groupId": group,
                "project.artifactId": artifact,
                "pom.artifactId": artifact,
                "project.version": version,
                "pom.version": version,
            }
        )
        parent_gav = (
            effective_gav(parent_path) if parent_path is not None else None
        )
        if parent_gav:
            values.update(
                {
                    "project.parent.groupId": parent_gav[0],
                    "project.parent.artifactId": parent_gav[1],
                    "project.parent.version": parent_gav[2],
                }
            )
        resolved = {
            key: _interpolate(value, values, f"{pom_path} property {key}")
            for key, value in values.items()
        }
        properties_cache[pom_path] = resolved
        return resolved

    dependency_management_cache: dict[
        PurePosixPath, dict[tuple[str, str], str]
    ] = {}

    def effective_dependency_management(
        pom_path: PurePosixPath,
    ) -> dict[tuple[str, str], str]:
        cached = dependency_management_cache.get(pom_path)
        if cached is not None:
            return cached
        parent_path = local_parent_path(pom_path)
        managed = (
            dict(effective_dependency_management(parent_path))
            if parent_path is not None
            else {}
        )
        properties = effective_properties(pom_path)
        for dependency in poms[pom_path].findall(
            "m:dependencyManagement/m:dependencies/m:dependency", MAVEN_NAMESPACE
        ):
            raw_group = _xml_text(dependency, "m:groupId")
            raw_artifact = _xml_text(dependency, "m:artifactId")
            raw_version = _xml_text(dependency, "m:version")
            if not raw_group or not raw_artifact or not raw_version:
                raise AssertionError(f"incomplete managed dependency in {pom_path}")
            group = _interpolate(raw_group, properties, f"{pom_path} managed group")
            artifact = _interpolate(
                raw_artifact, properties, f"{pom_path} managed artifact"
            )
            managed[(group, artifact)] = _interpolate(
                raw_version, properties, f"{pom_path} managed version"
            )
        dependency_management_cache[pom_path] = managed
        return managed

    modules_by_ga: dict[tuple[str, str], tuple[PurePosixPath, tuple[str, str, str]]] = {}
    modules_by_artifact: dict[str, tuple[str, str, str]] = {}
    for pom_path in module_poms:
        gav = effective_gav(pom_path)
        ga = gav[:2]
        if ga in modules_by_ga:
            raise AssertionError(f"duplicate effective GA in mall reactor: {ga}")
        if gav[1] in modules_by_artifact:
            raise AssertionError(f"duplicate artifact id in mall reactor: {gav[1]}")
        modules_by_ga[ga] = (pom_path, gav)
        modules_by_artifact[gav[1]] = gav

    internal_edges: set[tuple[str, str]] = set()
    internal_edges_gav: set[tuple[str, str]] = set()
    for pom_path in module_poms:
        source_gav = effective_gav(pom_path)
        properties = effective_properties(pom_path)
        managed = effective_dependency_management(pom_path)
        seen_dependency_ga: set[tuple[str, str]] = set()
        for dependency in poms[pom_path].findall(
            "m:dependencies/m:dependency", MAVEN_NAMESPACE
        ):
            raw_group = _xml_text(dependency, "m:groupId")
            raw_artifact = _xml_text(dependency, "m:artifactId")
            if not raw_group or not raw_artifact:
                raise AssertionError(f"incomplete dependency GA in {pom_path}")
            group = _interpolate(raw_group, properties, f"{pom_path} dependency group")
            artifact = _interpolate(
                raw_artifact, properties, f"{pom_path} dependency artifact"
            )
            if (group, artifact) in seen_dependency_ga:
                raise AssertionError(
                    f"duplicate POM-local dependency GA in {pom_path}: {group}:{artifact}"
                )
            seen_dependency_ga.add((group, artifact))
            target_record = modules_by_ga.get((group, artifact))
            if target_record is None:
                continue
            dependency_type = _xml_text(dependency, "m:type") or "jar"
            classifier = _xml_text(dependency, "m:classifier")
            if dependency_type != "jar" or classifier is not None:
                raise AssertionError(
                    f"unsupported reactor dependency shape in {pom_path}: "
                    f"type={dependency_type}, classifier={classifier}"
                )
            raw_version = _xml_text(dependency, "m:version")
            resolved_version = (
                _interpolate(raw_version, properties, f"{pom_path} dependency version")
                if raw_version
                else managed.get((group, artifact))
            )
            if resolved_version is None:
                raise AssertionError(
                    f"reactor dependency version unresolved in {pom_path}: {group}:{artifact}"
                )
            if resolved_version.startswith(("[", "(")):
                raise AssertionError(
                    f"reactor dependency version is not exact in {pom_path}: {resolved_version}"
                )
            target_gav = target_record[1]
            dependency_gav = (group, artifact, resolved_version)
            if dependency_gav != target_gav:
                continue
            internal_edges.add((source_gav[1], target_gav[1]))
            internal_edges_gav.add((":".join(source_gav), ":".join(target_gav)))

    root_internal_dependencies: set[str] = set()
    root_internal_dependency_gavs: set[str] = set()
    root_properties = effective_properties(root_path)
    root_managed = effective_dependency_management(root_path)
    for dependency in root.findall("m:dependencies/m:dependency", MAVEN_NAMESPACE):
        raw_group = _xml_text(dependency, "m:groupId")
        raw_artifact = _xml_text(dependency, "m:artifactId")
        if not raw_group or not raw_artifact:
            raise AssertionError("incomplete root dependency GA")
        group = _interpolate(raw_group, root_properties, "root dependency group")
        artifact = _interpolate(raw_artifact, root_properties, "root dependency artifact")
        target_record = modules_by_ga.get((group, artifact))
        if target_record is None:
            continue
        dependency_type = _xml_text(dependency, "m:type") or "jar"
        classifier = _xml_text(dependency, "m:classifier")
        if dependency_type != "jar" or classifier is not None:
            raise AssertionError(
                "unsupported root reactor dependency shape: "
                f"type={dependency_type}, classifier={classifier}"
            )
        raw_version = _xml_text(dependency, "m:version")
        resolved_version = (
            _interpolate(raw_version, root_properties, "root dependency version")
            if raw_version
            else root_managed.get((group, artifact))
        )
        if resolved_version is None:
            raise AssertionError(
                f"root reactor dependency version unresolved: {group}:{artifact}"
            )
        if resolved_version.startswith(("[", "(")):
            raise AssertionError(
                f"root reactor dependency version is not exact: {resolved_version}"
            )
        if (group, artifact, resolved_version) == target_record[1]:
            root_internal_dependencies.add(artifact)
            root_internal_dependency_gavs.add(":".join(target_record[1]))

    return {
        "root_project": f"{root_group}:{root_artifact}:{root_version}",
        "reactor_child_modules": sorted(modules_by_artifact),
        "reactor_child_module_gavs": sorted(
            ":".join(gav) for gav in modules_by_artifact.values()
        ),
        "contains_module_count": len(modules_by_artifact),
        "internal_depends_on": [list(edge) for edge in sorted(internal_edges)],
        "internal_depends_on_gav": [
            list(edge) for edge in sorted(internal_edges_gav)
        ],
        "reactor_dependency_management_exact_versions": [
            {
                "ga": f"{group}:{artifact}",
                "resolved_version": version,
            }
            for (group, artifact), version in sorted(root_managed.items())
            if (group, artifact) in modules_by_ga
        ],
        "admin_to_common_all_simple_paths": _all_simple_paths(
            internal_edges, "mall-admin", "mall-common"
        ),
        "admin_to_search_all_simple_paths": _all_simple_paths(
            internal_edges, "mall-admin", "mall-search"
        ),
        "root_internal_dependencies": sorted(root_internal_dependencies),
        "root_internal_dependency_gavs": sorted(root_internal_dependency_gavs),
    }


class Iteration003FrozenAssetTests(unittest.TestCase):
    def test_manifest_associates_each_frozen_input_with_its_own_path_ref_and_digest(self) -> None:
        inputs = _manifest_external_inputs()
        fixture_root = VALIDATION_ROOT / "fixtures" / "maven-identity"
        expected: dict[str, dict[str, object]] = {
            "mall_repository": {
                "path": "validation-projects/mall",
                "canonical_remote": "https://github.com/macrozheng/mall.git",
                "revision_a": "a50870fba92d59021f07cacbe947442b1871e78f",
                "revision_b": "cfaadb201bb7aa6425de069fab5e57bf8b5048f3",
                "oracle_path": "validation/structure_world_model_iteration_003/oracles/mall-structure-1.0.0.json",
                "oracle_ref": "MALL-MAVEN-STRUCTURE@1.0.0",
                "oracle_digest": f"sha256:{_sha256(MALL_ORACLE_PATH)}",
            },
            "maven_identity_fixture": {
                "path": "validation/structure_world_model_iteration_003/fixtures/maven-identity",
                "fixture_ref": "maven-identity-anti-name-stitch@1",
                "digest": f"sha256:{_fixture_digest(fixture_root)}",
            },
            "structure_schema": {
                "path": "validation/structure_world_model_iteration_003/schema/maven-reactor-structure-1.0.0.json",
                "schema_ref": "MAVEN-REACTOR-STRUCTURE@1.0.0",
                "digest": f"sha256:{_sha256(VALIDATION_ROOT / 'schema' / 'maven-reactor-structure-1.0.0.json')}",
            },
            "maven_evaluation_context": {
                "path": "validation/structure_world_model_iteration_003/schema/maven-evaluation-context-1.0.0.json",
                "context_ref": "MAVEN-EVALUATION-CONTEXT@1.0.0",
                "digest": f"sha256:{_sha256(VALIDATION_ROOT / 'schema' / 'maven-evaluation-context-1.0.0.json')}",
            },
            "maven_canonicalization": {
                "path": "validation/structure_world_model_iteration_003/schema/maven-reactor-canonicalization-1.0.0.json",
                "canonicalization_ref": "MAVEN-REACTOR-CANONICALIZATION@1.0.0",
                "digest": f"sha256:{_sha256(VALIDATION_ROOT / 'schema' / 'maven-reactor-canonicalization-1.0.0.json')}",
            },
            "product_question_suite": {
                "path": "validation/structure_world_model_iteration_003/questions/product-suite-1.0.0.json",
                "suite_ref": "ITER-003-WORLD-MODEL-PRODUCT-SUITE@1.0.0",
                "digest": f"sha256:{_sha256(VALIDATION_ROOT / 'questions' / 'product-suite-1.0.0.json')}",
            },
            "product_input_suite": {
                "path": "validation/structure_world_model_iteration_003/questions/product-input-suite-1.0.0.json",
                "suite_ref": "ITER-003-WORLD-MODEL-PRODUCT-INPUT-SUITE@1.0.0",
                "digest": f"sha256:{_sha256(PRODUCT_INPUT_SUITE_PATH)}",
            },
            "capability_suite": {
                "path": "validation/structure_world_model_iteration_003/questions/capability-suite-1.0.0.json",
                "suite_ref": "ITER-003-WORLD-MODEL-CAPABILITY-SUITE@1.0.0",
                "digest": f"sha256:{_sha256(VALIDATION_ROOT / 'questions' / 'capability-suite-1.0.0.json')}",
            },
            "metamorphic_generator": {
                "path": "validation/structure_world_model_iteration_003/metamorphic/generate_reactor.py",
                "generator_ref": "MAVEN-STRUCTURE-METAMORPHIC-GENERATOR@1.0.0",
                "digest": f"sha256:{_sha256(GENERATOR_PATH)}",
            },
            "legacy_snapshot_fixture": {
                "database_path": "validation/structure_world_model_iteration_003/legacy/iteration-002-legacy.sqlite3",
                "database_digest": f"sha256:{_sha256(VALIDATION_ROOT / 'legacy' / 'iteration-002-legacy.sqlite3')}",
                "report_path": "validation/structure_world_model_iteration_003/legacy/iteration-002-legacy-report.json",
                "report_digest": f"sha256:{_sha256(VALIDATION_ROOT / 'legacy' / 'iteration-002-legacy-report.json')}",
                "generator_path": "validation/structure_world_model_iteration_003/legacy/generate_legacy_snapshot.py",
                "generator_digest": f"sha256:{_sha256(VALIDATION_ROOT / 'legacy' / 'generate_legacy_snapshot.py')}",
            },
            "direct_investigation_baseline": {
                "protocol_path": "validation/structure_world_model_iteration_003/questions/direct-baseline-protocol-1.0.1.json",
                "protocol_ref": "ITER-003-DIRECT-SOURCE-BASELINE@1.0.1",
                "protocol_digest": f"sha256:{_sha256(DIRECT_PROTOCOL_PATH)}",
                "implementation_path": "validation/product_holdout_iteration_002/direct_answer.py",
                "implementation_file_digest": f"sha256:{_sha256(DIRECT_IMPLEMENTATION_PATH)}",
            },
            "mature_source_agent_baseline": {
                "protocol_path": "validation/structure_world_model_iteration_003/questions/mature-agent-baseline-protocol-1.0.1.json",
                "protocol_ref": "ITER-003-MATURE-SOURCE-AGENT-BASELINE@1.0.1",
                "protocol_digest": f"sha256:{_sha256(MATURE_PROTOCOL_PATH)}",
                "answer_schema_path": "validation/structure_world_model_iteration_003/questions/mature-agent-answer-schema-1.0.0.json",
                "answer_schema_ref": "ITER-003-MATURE-SOURCE-AGENT-ANSWER@1.0.0",
                "answer_schema_digest": f"sha256:{_sha256(MATURE_ANSWER_SCHEMA_PATH)}",
            },
        }
        for name, expected_fields in expected.items():
            self.assertIn(name, inputs)
            for field, expected_value in expected_fields.items():
                self.assertEqual(inputs[name].get(field), expected_value, f"{name}.{field}")

    def test_all_frozen_json_rejects_duplicate_keys_and_question_suites_are_separate(self) -> None:
        frozen_json = sorted(VALIDATION_ROOT.rglob("*.json"))
        self.assertTrue(frozen_json)
        for path in frozen_json:
            with self.subTest(path=path.relative_to(REPOSITORY_ROOT)):
                _load_json(path)

        product = _load_json(PRODUCT_SUITE_PATH)
        product_input = _load_json(PRODUCT_INPUT_SUITE_PATH)
        capability = _load_json(VALIDATION_ROOT / "questions" / "capability-suite-1.0.0.json")
        self.assertEqual(product["suite_ref"], "ITER-003-WORLD-MODEL-PRODUCT-SUITE@1.0.0")
        self.assertEqual(
            product_input["suite_ref"],
            "ITER-003-WORLD-MODEL-PRODUCT-INPUT-SUITE@1.0.0",
        )
        self.assertEqual(capability["suite_ref"], "ITER-003-WORLD-MODEL-CAPABILITY-SUITE@1.0.0")

        product_cases = product_input["cases"]
        product_expectations = product["case_expectations"]
        capability_cases = capability["cases"]
        self.assertIsInstance(product_cases, list)
        self.assertIsInstance(product_expectations, list)
        self.assertIsInstance(capability_cases, list)
        product_ids = [case["case_id"] for case in product_cases]
        expectation_ids = [case["case_id"] for case in product_expectations]
        capability_ids = [case["case_id"] for case in capability_cases]
        self.assertEqual(len(product_ids), len(set(product_ids)))
        self.assertEqual(product_ids, expectation_ids)
        self.assertEqual(len(capability_ids), len(set(capability_ids)))
        self.assertFalse(set(product_ids) & set(capability_ids))
        self.assertEqual(set(capability["must_not_include_product_case_ids"]), set(product_ids))

        self.assertEqual(
            product["product_input"],
            {
                "suite_ref": product_input["suite_ref"],
                "path": PRODUCT_INPUT_SUITE_PATH.relative_to(REPOSITORY_ROOT).as_posix(),
                "digest": f"sha256:{_sha256(PRODUCT_INPUT_SUITE_PATH)}",
            },
        )
        self.assertEqual(
            product["isolation_contract"]["product_read_allowlist"],
            ["PRODUCT_RUNTIME", "RESOLVED_SNAPSHOT_READ_BUNDLES_ONLY"],
        )
        self.assertNotIn(
            "BOUND_SOURCE_REPOSITORY_ONLY",
            product["isolation_contract"]["product_read_allowlist"],
        )
        serialized_product_input = json.dumps(product_input, sort_keys=True)
        for forbidden_key in (
            "oracle_assertions",
            "expected_result",
            "oracle_ref",
            "json_pointer",
            "seed_input_digest",
            "oracle_sha256",
        ):
            self.assertNotIn(forbidden_key, serialized_product_input)

        bindings = product["snapshot_bindings"]
        self.assertIsInstance(bindings, dict)
        self.assertEqual({case["snapshot_selector"] for case in product_cases}, set(bindings))
        fixture_binding = bindings["EXACT_FIXTURE_VALID"]
        self.assertEqual(fixture_binding["fixture_ref"], "maven-identity-anti-name-stitch@1")
        self.assertEqual(
            fixture_binding["fixture_digest"],
            f"sha256:{_fixture_digest(VALIDATION_ROOT / 'fixtures' / 'maven-identity')}",
        )
        self.assertEqual(
            fixture_binding["repository_path"],
            "validation/structure_world_model_iteration_003/fixtures/maven-identity/valid",
        )
        self.assertEqual(
            fixture_binding["source_tree_digest"],
            f"sha256:{_fixture_digest(REPOSITORY_ROOT / fixture_binding['repository_path'])}",
        )
        self.assertEqual(fixture_binding["reactor_root"], "pom.xml")

        oracle_registry = product["oracle_registry"]
        self.assertIsInstance(oracle_registry, dict)
        oracle_documents: dict[str, dict[str, object]] = {}
        for oracle_ref, descriptor in oracle_registry.items():
            self.assertIsInstance(descriptor, dict)
            oracle_path = REPOSITORY_ROOT / descriptor["path"]
            self.assertTrue(oracle_path.is_file(), oracle_ref)
            self.assertEqual(descriptor["digest"], f"sha256:{_sha256(oracle_path)}")
            oracle_document = _load_json(oracle_path)
            self.assertIn(oracle_ref, {oracle_document.get("oracle_ref"), oracle_document.get("fixture_id")})
            oracle_documents[oracle_ref] = oracle_document

        expected_types = {
            "array": list,
            "boolean": bool,
            "object": dict,
            "string": str,
        }
        for expectation in product_expectations:
            assertions = expectation.get("oracle_assertions", [])
            if expectation["direct_parity"]:
                self.assertTrue(assertions, expectation["case_id"])
            for assertion in assertions:
                self.assertEqual(
                    set(assertion), {"oracle_ref", "json_pointer", "expected_type"}
                )
                self.assertIn(assertion["oracle_ref"], oracle_documents)
                resolved = _resolve_json_pointer(
                    oracle_documents[assertion["oracle_ref"]],
                    assertion["json_pointer"],
                )
                self.assertIsInstance(resolved, expected_types[assertion["expected_type"]])

        unsupported_why = [
            case
            for case in product_cases
            if "为什么" in case["question"] or "设计动机" in case["paraphrase"]
        ]
        self.assertEqual(len(unsupported_why), 1)
        gap_expectation = next(
            item
            for item in product_expectations
            if item["case_id"] == unsupported_why[0]["case_id"]
        )
        self.assertFalse(gap_expectation["direct_parity"])
        self.assertEqual(
            gap_expectation["expected_result"],
            {
                "status": "KNOWLEDGE_GAP",
                "reason_code": "CHANGE_INTENT_OUTSIDE_STRUCTURE_COVERAGE",
            },
        )

    def test_agent_baseline_protocols_and_prepared_mature_cli_are_exact(self) -> None:
        inputs = _manifest_external_inputs()
        direct_input = inputs["direct_investigation_baseline"]
        mature_input = inputs["mature_source_agent_baseline"]
        direct = _load_json(DIRECT_PROTOCOL_PATH)
        mature = _load_json(MATURE_PROTOCOL_PATH)
        answer_schema = _load_json(MATURE_ANSWER_SCHEMA_PATH)

        self.assertEqual(direct["protocol_ref"], direct_input["protocol_ref"])
        self.assertEqual(
            direct["implementation"]["path"], direct_input["implementation_path"]
        )
        self.assertEqual(
            direct["implementation"]["file_digest"],
            direct_input["implementation_file_digest"],
        )
        self.assertEqual(
            direct["comparison_protocol"]["run_order"],
            "SEAL_ALL_DIRECT_RESULTS_AFTER_V009_EXACT_MODEL_SELECTION_AND_BEFORE_FIRST_G3B_PRODUCT_RUN",
        )
        self.assertEqual(direct["source_contract"]["oracle_visibility"], "NONE")
        self.assertEqual(
            direct["source_contract"]["revision_path_closure"],
            "EXACT_REQUIRED_POM_PATHS_LISTED_SEPARATELY_FOR_EACH_REVISION_WITH_UNION_AS_SOURCE_ALLOWLIST",
        )

        self.assertEqual(mature["protocol_ref"], mature_input["protocol_ref"])
        self.assertEqual(
            mature["answer_schema"]["schema_ref"], mature_input["answer_schema_ref"]
        )
        self.assertEqual(
            mature["answer_schema"]["schema_digest"],
            mature_input["answer_schema_digest"],
        )
        self.assertEqual(answer_schema["$id"], mature_input["answer_schema_ref"])
        self.assertEqual(mature["command_contract"]["web_search"], "DISABLED")
        self.assertEqual(mature["command_contract"]["network_tools"], "DISABLED")
        command_contract = mature["command_contract"]
        self.assertEqual(
            command_contract["argv_order"],
            ["BINARY", "GLOBAL_FLAGS", "SUBCOMMAND", "EXEC_FLAGS", "PROMPT"],
        )
        self.assertEqual(
            command_contract["global_flags"], ["--ask-for-approval", "never"]
        )
        self.assertEqual(command_contract["subcommand"], "exec")
        self.assertIn("--ignore-user-config", command_contract["exec_flags"])
        self.assertIn("--ignore-rules", command_contract["exec_flags"])
        self.assertNotIn("--ask-for-approval", command_contract["exec_flags"])

        codex_path_text = shutil.which("codex")
        self.assertIsNotNone(codex_path_text, "The frozen mature Agent CLI is required by ITER-003 G0")
        codex_path = Path(codex_path_text).resolve()
        self.assertEqual(
            _sha256(codex_path),
            str(mature_input["prepared_binary_digest"]).removeprefix("sha256:"),
        )
        version = _run([str(codex_path), "--version"]).stdout.strip()
        self.assertEqual(version, mature_input["prepared_tool_version"])
        self.assertEqual(version, mature["agent"]["prepared_version"])
        exec_flags = [
            str(MATURE_ANSWER_SCHEMA_PATH)
            if value == "MATURE_AGENT_ANSWER_SCHEMA"
            else value
            for value in command_contract["exec_flags"]
        ]
        parse_smoke = _run(
            [
                str(codex_path),
                *command_contract["global_flags"],
                command_contract["subcommand"],
                *exec_flags,
                "--help",
            ]
        )
        self.assertIn("Usage: codex exec", parse_smoke.stdout)


class Iteration003MetamorphicGeneratorTests(unittest.TestCase):
    def test_generator_is_independent_deterministic_and_maven_valid(self) -> None:
        parsed = ast.parse(GENERATOR_PATH.read_text(encoding="utf-8"), filename=str(GENERATOR_PATH))
        imported_modules = {
            alias.name
            for node in ast.walk(parsed)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        imported_modules.update(
            node.module or ""
            for node in ast.walk(parsed)
            if isinstance(node, ast.ImportFrom)
        )
        self.assertFalse(
            any(
                module == "software_world_model"
                or module.startswith("software_world_model.")
                for module in imported_modules
            ),
            imported_modules,
        )
        self.assertIsNotNone(shutil.which("mvn"), "Maven is required by ITER-003 G0")

        with TemporaryDirectory() as temporary_directory:
            temporary_root = Path(temporary_directory)

            def generate(
                product_directory: Path,
                evaluator_directory: Path,
                seed: str,
                *,
                env: dict[str, str] | None = None,
            ) -> dict[str, object]:
                completed = _run(
                    [
                        sys.executable,
                        str(GENERATOR_PATH),
                        "--product-directory",
                        str(product_directory),
                        "--evaluator-directory",
                        str(evaluator_directory),
                        "--seed",
                        seed,
                    ],
                    env=env,
                )
                return json.loads(completed.stdout)

            first_product = temporary_root / "first-product"
            first_evaluator = temporary_root / "first-evaluator"
            second_product = temporary_root / "second-product"
            second_evaluator = temporary_root / "second-evaluator"
            first = generate(
                first_product, first_evaluator, "iter-003-fixed-seed"
            )
            second = generate(
                second_product, second_evaluator, "iter-003-fixed-seed"
            )
            different = generate(
                temporary_root / "different-product",
                temporary_root / "different-evaluator",
                "iter-003-other-seed",
            )
            for key in ("revision_a", "tree_a", "revision_b", "tree_b", "oracle_sha256"):
                self.assertEqual(first[key], second[key], key)
            self.assertEqual(
                _load_json(first_evaluator / "oracle.json"),
                _load_json(second_evaluator / "oracle.json"),
            )
            self.assertFalse((first_product / "oracle.json").exists())
            self.assertEqual(
                sorted(path.name for path in first_product.iterdir()), ["repository"]
            )
            for key in ("revision_a", "tree_a", "revision_b", "tree_b"):
                self.assertEqual(len(first[key]), 40, key)
            generation_environment = first["generation_environment"]
            self.assertEqual(generation_environment["git_object_format"], "sha1")
            self.assertEqual(
                generation_environment["generator_sha256"], _sha256(GENERATOR_PATH)
            )
            self.assertEqual(
                first["seed_input_digest"],
                hashlib.sha256(b"iter-003-fixed-seed").hexdigest(),
            )
            self.assertNotEqual(
                first["root_project_gav"], different["root_project_gav"]
            )
            self.assertNotEqual(
                first["revision_a_oracle"], different["revision_a_oracle"]
            )

            hostile_hooks = temporary_root / "hostile-hooks"
            hostile_hooks.mkdir()
            hostile_pre_commit = hostile_hooks / "pre-commit"
            hostile_pre_commit.write_text("#!/bin/sh\nexit 97\n", encoding="utf-8")
            hostile_pre_commit.chmod(0o755)
            hostile_global = temporary_root / "hostile-gitconfig"
            hostile_global.write_text(
                "[init]\n"
                "\tdefaultObjectFormat = sha256\n"
                "\tdefaultBranch = hostile\n"
                "[core]\n"
                f"\thooksPath = {hostile_hooks}\n"
                "[commit]\n"
                "\tgpgSign = true\n",
                encoding="utf-8",
            )
            hostile_environment = dict(os.environ)
            hostile_environment.update(
                {
                    "GIT_CONFIG_GLOBAL": str(hostile_global),
                    "GIT_CONFIG_NOSYSTEM": "0",
                    "GIT_CONFIG_COUNT": "1",
                    "GIT_CONFIG_KEY_0": "core.hooksPath",
                    "GIT_CONFIG_VALUE_0": str(hostile_hooks),
                    "GIT_AUTHOR_NAME": "Hostile inherited identity",
                }
            )
            hostile = generate(
                temporary_root / "hostile-product",
                temporary_root / "hostile-evaluator",
                "iter-003-fixed-seed",
                env=hostile_environment,
            )
            for key in (
                "revision_a",
                "tree_a",
                "revision_b",
                "tree_b",
                "oracle_sha256",
            ):
                self.assertEqual(first[key], hostile[key], key)

            overlapping_product = temporary_root / "overlapping-product"
            overlapping = _run(
                [
                    sys.executable,
                    str(GENERATOR_PATH),
                    "--product-directory",
                    str(overlapping_product),
                    "--evaluator-directory",
                    str(overlapping_product / "evaluator"),
                    "--seed",
                    "must-reject-overlap",
                ],
                check=False,
            )
            self.assertNotEqual(overlapping.returncode, 0)
            self.assertIn("must be disjoint", overlapping.stderr)
            self.assertFalse(overlapping_product.exists())

            settings = temporary_root / "settings.xml"
            settings.write_text(
                '<settings xmlns="http://maven.apache.org/SETTINGS/1.2.0"/>\n',
                encoding="utf-8",
            )
            local_repository = temporary_root / "m2"

            def maven_validate(directory: Path) -> None:
                completed = _run(
                    [
                        "mvn",
                        "--batch-mode",
                        "--offline",
                        "--quiet",
                        "--settings",
                        str(settings),
                        f"-Dmaven.repo.local={local_repository}",
                        "-f",
                        str(directory / "pom.xml"),
                        "validate",
                    ],
                    cwd=directory,
                    check=False,
                )
                self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

            repository = first_product / "repository"
            maven_validate(repository)
            revision_a_directory = temporary_root / "revision-a"
            _git(repository, "worktree", "add", "--detach", str(revision_a_directory), str(first["revision_a"]))
            try:
                maven_validate(revision_a_directory)
            finally:
                _git(repository, "worktree", "remove", "--force", str(revision_a_directory))


class Iteration003MallOracleTests(unittest.TestCase):
    def test_raw_git_poms_match_the_frozen_mall_oracle(self) -> None:
        oracle = _load_json(MALL_ORACLE_PATH)
        repository = oracle["repository"]
        self.assertIsInstance(repository, dict)
        revision_a = repository["revision_a"]
        revision_b = repository["revision_b"]
        self.assertEqual(
            _git(MALL_REPOSITORY, "remote", "get-url", "origin"),
            repository["canonical_remote"],
        )
        self.assertEqual(_git(MALL_REPOSITORY, "rev-parse", f"{revision_a}^{{tree}}"), repository["tree_a"])
        self.assertEqual(_git(MALL_REPOSITORY, "rev-parse", f"{revision_b}^{{tree}}"), repository["tree_b"])
        is_ancestor = (
            _run(
                ["git", "-C", str(MALL_REPOSITORY), "merge-base", "--is-ancestor", str(revision_a), str(revision_b)],
                check=False,
            ).returncode
            == 0
        )
        self.assertEqual(is_ancestor, repository["a_is_ancestor_of_b"])
        self.assertEqual(
            int(_git(MALL_REPOSITORY, "rev-list", "--count", f"{revision_a}..{revision_b}")),
            repository["commit_distance"],
        )

        derived_a = _derive_mall_structure(str(revision_a))
        derived_b = _derive_mall_structure(str(revision_b))
        self.assertEqual(derived_a["root_project"], oracle["root_project"])
        for name, derived in (("revision_a_oracle", derived_a), ("revision_b_oracle", derived_b)):
            expected = oracle[name]
            self.assertIsInstance(expected, dict)
            self.assertEqual(derived["reactor_child_modules"], expected["reactor_child_modules"])
            self.assertEqual(
                derived["reactor_child_module_gavs"],
                expected["reactor_child_module_gavs"],
            )
            self.assertEqual(derived["contains_module_count"], expected["contains_module_count"])
            self.assertEqual(derived["internal_depends_on"], expected["internal_depends_on"])
            self.assertEqual(
                derived["internal_depends_on_gav"],
                expected["internal_depends_on_gav"],
            )
            self.assertEqual(
                derived["reactor_dependency_management_exact_versions"],
                expected["reactor_dependency_management_exact_versions"],
            )
            self.assertEqual(
                derived["admin_to_common_all_simple_paths"],
                expected["admin_to_common_all_simple_paths"],
            )
        expected_b = oracle["revision_b_oracle"]
        self.assertIsInstance(expected_b, dict)
        self.assertEqual(
            derived_b["admin_to_search_all_simple_paths"],
            expected_b["admin_to_search_all_simple_paths"],
        )
        self.assertEqual(derived_b["root_internal_dependencies"], [])
        self.assertEqual(derived_b["root_internal_dependency_gavs"], [])
        self.assertFalse(expected_b["root_locally_declares_security_dependency"])

        expected_delta = oracle["a_to_b"]
        self.assertIsInstance(expected_delta, dict)
        self.assertEqual(
            sorted(set(derived_b["reactor_child_modules"]) - set(derived_a["reactor_child_modules"])),
            expected_delta["added_modules"],
        )
        self.assertEqual(
            sorted(set(map(tuple, derived_b["internal_depends_on"])) - set(map(tuple, derived_a["internal_depends_on"]))),
            [tuple(edge) for edge in expected_delta["added_internal_edges"]],
        )
        self.assertEqual(
            sorted(set(derived_a["reactor_child_modules"]) - set(derived_b["reactor_child_modules"])),
            expected_delta["removed_modules"],
        )
        self.assertEqual(
            sorted(set(map(tuple, derived_a["internal_depends_on"])) - set(map(tuple, derived_b["internal_depends_on"]))),
            [tuple(edge) for edge in expected_delta["removed_internal_edges"]],
        )


if __name__ == "__main__":
    unittest.main()
