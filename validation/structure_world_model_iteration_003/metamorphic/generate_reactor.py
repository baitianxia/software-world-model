"""Generate a seeded two-revision Maven reactor and independent graph oracle.

This validation generator intentionally imports no product package.  The seed is
supplied only after the product process is loaded during Product Validation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
from typing import Iterable


GENERATOR_REF = "MAVEN-STRUCTURE-METAMORPHIC-GENERATOR@1.0.0"


def _token(seed: str, label: str, length: int = 10) -> str:
    return hashlib.sha256(f"{seed}:{label}".encode("utf-8")).hexdigest()[:length]


def _xml(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _dependency_xml(node: dict[str, str]) -> str:
    return (
        "    <dependency>\n"
        f"      <groupId>{_xml(node['group_id'])}</groupId>\n"
        f"      <artifactId>{_xml(node['artifact_id'])}</artifactId>\n"
        f"      <version>{_xml(node['version'])}</version>\n"
        "    </dependency>"
    )


def _project_xml(
    node: dict[str, str], dependencies: Iterable[dict[str, str]]
) -> str:
    dependency_items = list(dependencies)
    dependencies_xml = ""
    if dependency_items:
        dependencies_xml = (
            "\n  <dependencies>\n"
            + "\n".join(_dependency_xml(item) for item in dependency_items)
            + "\n  </dependencies>"
        )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<project xmlns="http://maven.apache.org/POM/4.0.0">\n'
        "  <modelVersion>4.0.0</modelVersion>\n"
        f"  <groupId>{_xml(node['group_id'])}</groupId>\n"
        f"  <artifactId>{_xml(node['artifact_id'])}</artifactId>\n"
        f"  <version>{_xml(node['version'])}</version>\n"
        "  <packaging>jar</packaging>\n"
        f"  <name>{_xml(node['label'])}</name>"
        f"{dependencies_xml}\n"
        "</project>\n"
    )


def _root_xml(
    root: dict[str, str], nodes: list[dict[str, str]], root_target: dict[str, str]
) -> str:
    modules = "\n".join(
        f"    <module>{_xml(node['path'])}</module>" for node in nodes
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<project xmlns="http://maven.apache.org/POM/4.0.0">\n'
        "  <modelVersion>4.0.0</modelVersion>\n"
        f"  <groupId>{_xml(root['group_id'])}</groupId>\n"
        f"  <artifactId>{_xml(root['artifact_id'])}</artifactId>\n"
        f"  <version>{_xml(root['version'])}</version>\n"
        "  <packaging>pom</packaging>\n"
        "  <modules>\n"
        f"{modules}\n"
        "  </modules>\n"
        "  <dependencies>\n"
        f"{_dependency_xml(root_target)}\n"
        "  </dependencies>\n"
        "</project>\n"
    )


def _ga(node: dict[str, str]) -> str:
    return f"{node['group_id']}:{node['artifact_id']}"


def _write_revision(
    repository: Path,
    root: dict[str, str],
    nodes: list[dict[str, str]],
    edges: set[tuple[int, int]],
) -> None:
    for child in repository.iterdir():
        if child.name == ".git":
            continue
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()
    (repository / "pom.xml").write_text(
        _root_xml(root, nodes, nodes[1]), encoding="utf-8"
    )
    outgoing: dict[int, list[int]] = {index: [] for index in range(len(nodes))}
    for source, target in sorted(edges):
        outgoing[source].append(target)
    for index, node in enumerate(nodes):
        module_directory = repository / node["path"]
        module_directory.mkdir(parents=True)
        dependencies = [nodes[target] for target in outgoing[index]]
        (module_directory / "pom.xml").write_text(
            _project_xml(node, dependencies), encoding="utf-8"
        )


def _isolated_git_environment(extra: dict[str, str] | None = None) -> dict[str, str]:
    environment = {
        key: value for key, value in os.environ.items() if not key.startswith("GIT_")
    }
    environment.update(
        {
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "LC_ALL": "C",
            "TZ": "UTC",
        }
    )
    if extra:
        environment.update(extra)
    return environment


def _git(repository: Path, *arguments: str, env: dict[str, str] | None = None) -> str:
    completed = subprocess.run(
        [
            "git",
            "-c",
            "core.hooksPath=/dev/null",
            "-c",
            "commit.gpgSign=false",
            "-C",
            str(repository),
            *arguments,
        ],
        check=True,
        capture_output=True,
        text=True,
        env=_isolated_git_environment(env),
    )
    return completed.stdout.strip()


def _commit(repository: Path, message: str, timestamp: str) -> tuple[str, str]:
    environment = {
        "GIT_AUTHOR_NAME": "ITER-003 Metamorphic Generator",
        "GIT_AUTHOR_EMAIL": "iteration-003@example.invalid",
        "GIT_COMMITTER_NAME": "ITER-003 Metamorphic Generator",
        "GIT_COMMITTER_EMAIL": "iteration-003@example.invalid",
        "GIT_AUTHOR_DATE": timestamp,
        "GIT_COMMITTER_DATE": timestamp,
    }
    _git(repository, "add", "-A", env=environment)
    _git(
        repository,
        "commit",
        "--quiet",
        "-m",
        message,
        env=environment,
    )
    revision = _git(repository, "rev-parse", "HEAD")
    tree = _git(repository, "rev-parse", "HEAD^{tree}")
    return revision, tree


def _git_version() -> str:
    completed = subprocess.run(
        ["git", "--version"],
        check=True,
        capture_output=True,
        text=True,
        env=_isolated_git_environment(),
    )
    return completed.stdout.strip()


def _generator_sha256() -> str:
    return hashlib.sha256(Path(__file__).resolve().read_bytes()).hexdigest()


def _prepare_isolated_directories(
    product_directory: Path, evaluator_directory: Path
) -> None:
    product_resolved = product_directory.resolve()
    evaluator_resolved = evaluator_directory.resolve()
    if (
        product_resolved == evaluator_resolved
        or product_resolved in evaluator_resolved.parents
        or evaluator_resolved in product_resolved.parents
    ):
        raise ValueError("product and evaluator directories must be disjoint")
    for label, directory in (
        ("product", product_directory),
        ("evaluator", evaluator_directory),
    ):
        if directory.exists() and any(directory.iterdir()):
            raise ValueError(f"{label} directory must be absent or empty")
    product_directory.mkdir(parents=True, exist_ok=True)
    evaluator_directory.mkdir(parents=True, exist_ok=True)


def _paths(
    node_count: int, edges: set[tuple[int, int]], source: int, target: int
) -> list[list[int]]:
    adjacency = {index: [] for index in range(node_count)}
    for left, right in sorted(edges):
        adjacency[left].append(right)
    results: list[list[int]] = []

    def visit(current: int, path: list[int]) -> None:
        if current == target:
            results.append(path)
            return
        for following in adjacency[current]:
            if following not in path:
                visit(following, [*path, following])

    visit(source, [source])
    return sorted(results)


def _node_report(nodes: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        {
            "ga": _ga(node),
            "gav": f"{_ga(node)}:{node['version']}",
            "path": node["path"],
            "label": node["label"],
        }
        for node in nodes
    ]


def generate(
    product_directory: Path, evaluator_directory: Path, seed: str
) -> dict[str, object]:
    _prepare_isolated_directories(product_directory, evaluator_directory)
    repository = product_directory / "repository"
    repository.mkdir()
    _git(
        repository,
        "init",
        "--quiet",
        "--object-format=sha1",
        "--initial-branch=main",
    )

    count_a = 5 + int(_token(seed, "node-count", 8), 16) % 3
    shared_artifact = f"common-{_token(seed, 'shared-artifact')}"
    nodes_a: list[dict[str, str]] = []
    for index in range(count_a):
        nodes_a.append(
            {
                "group_id": f"org.generated.g{_token(seed, f'group-{index}')}",
                "artifact_id": (
                    shared_artifact
                    if index in (0, 1)
                    else f"module-{_token(seed, f'artifact-{index}')}"
                ),
                "version": f"1.0.{index}",
                "path": f"segment-{_token(seed, f'path-{index}')}",
                "label": f"Label-{_token(seed, f'label-{index}')}",
            }
        )
    root = {
        "group_id": f"org.generated.root{_token(seed, 'root-group')}",
        "artifact_id": f"reactor-{_token(seed, 'root-artifact')}",
        "version": "1.0.0",
    }
    source_index = count_a - 1
    target_index = 0
    middle_index = max(1, count_a // 2)
    edges_a: set[tuple[int, int]] = {
        (source_index, middle_index),
        (middle_index, target_index),
    }
    for left in range(1, count_a):
        for right in range(left):
            if int(_token(seed, f"edge-{left}-{right}", 8), 16) % 10_000 < 2_200:
                edges_a.add((left, right))

    _write_revision(repository, root, nodes_a, edges_a)
    revision_a, tree_a = _commit(
        repository, "generated revision A", "2001-01-01T00:00:00+0000"
    )

    nodes_b = [dict(node) for node in nodes_a]
    moved_index = 2
    version_index = 1
    label_index = min(3, count_a - 1)
    nodes_b[moved_index]["path"] = f"moved-{_token(seed, 'moved-path')}"
    nodes_b[version_index]["version"] = "2.0.0"
    nodes_b[label_index]["label"] = f"Renamed-{_token(seed, 'renamed-label')}"
    nodes_b.append(
        {
            "group_id": f"org.generated.new{_token(seed, 'new-group')}",
            "artifact_id": f"module-{_token(seed, 'new-artifact')}",
            "version": "1.0.0",
            "path": f"added-{_token(seed, 'new-path')}",
            "label": f"Added-{_token(seed, 'new-label')}",
        }
    )
    added_index = len(nodes_b) - 1
    edges_b = set(edges_a)
    edges_b.add((source_index, added_index))
    edges_b.add((added_index, target_index))
    _write_revision(repository, root, nodes_b, edges_b)
    revision_b, tree_b = _commit(
        repository, "generated revision B", "2001-01-01T00:00:01+0000"
    )

    ga_a = [_ga(node) for node in nodes_a]
    ga_b = [_ga(node) for node in nodes_b]
    edge_ga_a = sorted([[ga_a[left], ga_a[right]] for left, right in edges_a])
    edge_ga_b = sorted([[ga_b[left], ga_b[right]] for left, right in edges_b])
    paths_a = [
        [ga_a[index] for index in path]
        for path in _paths(len(nodes_a), edges_a, source_index, target_index)
    ]
    paths_b = [
        [ga_b[index] for index in path]
        for path in _paths(len(nodes_b), edges_b, source_index, target_index)
    ]
    root_ga = f"{root['group_id']}:{root['artifact_id']}"
    report: dict[str, object] = {
        "generator_ref": GENERATOR_REF,
        "seed": seed,
        "seed_input_digest": hashlib.sha256(seed.encode("utf-8")).hexdigest(),
        "product_repository": "repository",
        "generation_environment": {
            "python_implementation": platform.python_implementation(),
            "python_version": platform.python_version(),
            "git_version": _git_version(),
            "git_object_format": _git(repository, "rev-parse", "--show-object-format"),
            "generator_sha256": _generator_sha256(),
        },
        "revision_a": revision_a,
        "tree_a": tree_a,
        "revision_b": revision_b,
        "tree_b": tree_b,
        "root_project_gav": f"{root['group_id']}:{root['artifact_id']}:{root['version']}",
        "revision_a_oracle": {
            "nodes": _node_report(nodes_a),
            "internal_edges": edge_ga_a,
            "root_internal_edges": [[root_ga, ga_a[1]]],
            "all_simple_paths": paths_a,
        },
        "revision_b_oracle": {
            "nodes": _node_report(nodes_b),
            "internal_edges": edge_ga_b,
            "root_internal_edges": [[root_ga, ga_b[1]]],
            "all_simple_paths": paths_b,
        },
        "identity_state_counterexamples": {
            "moved_same_ga": ga_a[moved_index],
            "version_changed_same_ga": ga_a[version_index],
            "label_changed_same_ga": ga_a[label_index],
        },
        "a_to_b": {
            "added_nodes": [ga_b[added_index]],
            "added_edges": sorted(
                [edge for edge in edge_ga_b if edge not in edge_ga_a]
            ),
            "removed_edges": sorted(
                [edge for edge in edge_ga_a if edge not in edge_ga_b]
            ),
            "changed_states": {
                "module_path": [
                    {
                        "ga": ga_a[moved_index],
                        "from": nodes_a[moved_index]["path"],
                        "to": nodes_b[moved_index]["path"],
                    }
                ],
                "version": [
                    {
                        "ga": ga_a[version_index],
                        "from": nodes_a[version_index]["version"],
                        "to": nodes_b[version_index]["version"],
                    }
                ],
                "label": [
                    {
                        "ga": ga_a[label_index],
                        "from": nodes_a[label_index]["label"],
                        "to": nodes_b[label_index]["label"],
                    }
                ],
            },
        },
        "question_selectors": {
            "path_source_ga": ga_a[source_index],
            "path_target_ga": ga_a[target_index],
            "same_artifact_distinct_ga": [ga_a[0], ga_a[1]],
        },
    }
    oracle_path = evaluator_directory / "oracle.json"
    oracle_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    report["oracle_sha256"] = hashlib.sha256(oracle_path.read_bytes()).hexdigest()
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--product-directory", type=Path, required=True)
    parser.add_argument("--evaluator-directory", type=Path, required=True)
    parser.add_argument("--seed", required=True)
    arguments = parser.parse_args()
    result = generate(
        arguments.product_directory, arguments.evaluator_directory, arguments.seed
    )
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
