"""Load and verify the sealed product validation inputs.

The task manifest deliberately contains no reference answers.  Both answer
paths receive the same path-neutral task payload.  Acceptance dimensions are
available only to the independent evaluator.
"""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Mapping

from software_world_model.cross_cutting import DomainError, ErrorCode, digest_of


PRODUCT_HOLDOUT_SUITE_SCHEMA = "swm.product-holdout-suite@2"
TASK_INPUT_SCHEMA = "swm.product-holdout-task-input@1"
DEFAULT_SUITE_PATH = Path(__file__).with_name("suite.json")

# This value is replaced only when a new suite version is intentionally sealed.
PINNED_SUITE_DIGEST = "sha256:19b955badc095cf4fb6d8b20f3b2d02aec228c1f32b1ad26f13198e048474f25"

_EXPECTED_REPOSITORY_IDS = {
    "transmittable-thread-local",
    "poi-tl",
}
_EXPECTED_TASK_COUNT_PER_REPOSITORY = 3
_EXPECTED_TASK_COUNT = 6
_ANSWER_PATHS = {"direct", "world_assisted"}
_REQUIRED_RESOURCE_FIELDS = {
    "maximum_model_calls",
    "maximum_source_actions",
    "maximum_source_bytes_per_action",
    "maximum_total_input_tokens",
    "maximum_total_output_tokens",
    "maximum_output_tokens_per_call",
    "timeout_per_call_milliseconds",
}


def load_holdout_suite(path: str | Path = DEFAULT_SUITE_PATH) -> dict[str, object]:
    source = Path(path)
    try:
        value = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "product validation suite cannot be loaded",
        ) from exc
    if not isinstance(value, dict):
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "product validation suite must be a JSON object",
        )
    verify_holdout_suite(value)
    return value


def verify_holdout_suite(suite: Mapping[str, object]) -> None:
    if suite.get("schema") != PRODUCT_HOLDOUT_SUITE_SCHEMA:
        _invalid("product validation suite schema is unsupported")
    if suite.get("status") != "SEALED_NOT_EXECUTED":
        _invalid("product validation suite status is not sealed and unexecuted")
    if not _clean_text(suite.get("suite_id")) or not _clean_text(
        suite.get("suite_version")
    ):
        _invalid("product validation suite identity is invalid")

    recorded_digest = suite.get("suite_digest")
    if not isinstance(recorded_digest, str):
        _invalid("product validation suite digest is missing")
    calculated = _suite_digest(suite)
    if recorded_digest != calculated or recorded_digest != PINNED_SUITE_DIGEST:
        _invalid("product validation suite digest does not match the sealed version")

    repositories = suite.get("repositories")
    tasks = suite.get("tasks")
    if not isinstance(repositories, list) or not isinstance(tasks, list):
        _invalid("product validation repositories and tasks must be arrays")
    if len(repositories) != len(_EXPECTED_REPOSITORY_IDS):
        _invalid("product validation suite must contain exactly two repositories")
    repository_by_id: dict[str, Mapping[str, object]] = {}
    for repository in repositories:
        if not isinstance(repository, Mapping):
            _invalid("product validation repository entry is invalid")
        repository_id = repository.get("repository_id")
        if not isinstance(repository_id, str) or repository_id in repository_by_id:
            _invalid("product validation repository identities must be unique")
        repository_by_id[repository_id] = repository
        _verify_repository_entry(repository)
    if set(repository_by_id) != _EXPECTED_REPOSITORY_IDS:
        _invalid("product validation suite contains an unexpected repository")

    answer_paths = suite.get("answer_paths")
    if not isinstance(answer_paths, Mapping) or set(answer_paths) != _ANSWER_PATHS:
        _invalid("both answer paths must be declared")
    if answer_paths["direct"] != answer_paths["world_assisted"]:
        _invalid("both answer paths must have identical resource limits")
    resource_policy = answer_paths["direct"]
    if (
        not isinstance(resource_policy, Mapping)
        or set(resource_policy) != _REQUIRED_RESOURCE_FIELDS
        or any(not isinstance(value, int) or value <= 0 for value in resource_policy.values())
    ):
        _invalid("answer path resource limits are incomplete or invalid")

    if len(tasks) != _EXPECTED_TASK_COUNT:
        _invalid("product validation suite must contain exactly six tasks")
    task_ids: set[str] = set()
    counts = {repository_id: 0 for repository_id in repository_by_id}
    for task in tasks:
        if not isinstance(task, Mapping):
            _invalid("product validation task entry is invalid")
        task_id = task.get("task_id")
        repository_id = task.get("repository_id")
        if not isinstance(task_id, str) or task_id in task_ids:
            _invalid("product validation task identities must be unique")
        if repository_id not in repository_by_id:
            _invalid("product validation task refers to an unknown repository")
        task_ids.add(task_id)
        counts[repository_id] += 1
        _verify_task_entry(task, repository_by_id[repository_id])
    if any(count != _EXPECTED_TASK_COUNT_PER_REPOSITORY for count in counts.values()):
        _invalid("each repository must contribute exactly three validation tasks")

    evaluator = suite.get("independent_evaluator")
    if not isinstance(evaluator, Mapping):
        _invalid("independent evaluator policy is missing")
    if evaluator.get("must_differ_from") != ["direct", "world_assisted"]:
        _invalid("independent evaluator must differ from both answer paths")
    if evaluator.get("oracle_delivery") != "EVALUATOR_ONLY_AFTER_ANSWERS_SEALED":
        _invalid("reference answers must remain evaluator-only until answers are sealed")


def build_task_input(
    suite: Mapping[str, object], *, task_id: str
) -> dict[str, object]:
    """Create the exact payload shared by both answer paths.

    Acceptance dimensions and evaluator policy are intentionally excluded.
    """

    verify_holdout_suite(suite)
    tasks = suite["tasks"]
    repositories = suite["repositories"]
    task = next((item for item in tasks if item["task_id"] == task_id), None)
    if task is None:
        raise DomainError(ErrorCode.INVALID_ARGUMENT, "validation task was not found")
    repository = next(
        item for item in repositories if item["repository_id"] == task["repository_id"]
    )
    resource_policy = suite["answer_paths"]["direct"]
    core = {
        "schema": TASK_INPUT_SCHEMA,
        "suite_id": suite["suite_id"],
        "suite_version": suite["suite_version"],
        "suite_digest": suite["suite_digest"],
        "task_id": task["task_id"],
        "repository": {
            "repository_id": repository["repository_id"],
            "remote": repository["remote"],
            "frozen_tag": repository["frozen_tag"],
            "frozen_commit": repository["frozen_commit"],
            "frozen_tree": repository["frozen_tree"],
        },
        "question": task["question"],
        "revision_scope": deepcopy(task["revision_scope"]),
        "allowed_paths": deepcopy(task["allowed_paths"]),
        "source_policy": suite["source_policy"],
        "resource_policy": deepcopy(resource_policy),
    }
    return {**core, "task_input_digest": digest_of(core).value}


def verify_answer_path_parity(
    direct_input: Mapping[str, object], world_assisted_input: Mapping[str, object]
) -> None:
    if direct_input != world_assisted_input:
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "the two answer paths did not receive the same task and resource limits",
        )


def verify_frozen_checkouts(
    suite: Mapping[str, object], *, workspace_root: str | Path
) -> None:
    """Fail closed when a local checkout differs from its sealed repository entry."""

    verify_holdout_suite(suite)
    root = Path(workspace_root).resolve()
    tasks = suite["tasks"]
    for repository in suite["repositories"]:
        repository_tasks = [
            task for task in tasks if task["repository_id"] == repository["repository_id"]
        ]
        verify_repository_checkout(repository, repository_tasks, workspace_root=root)


def verify_repository_checkout(
    repository: Mapping[str, object],
    tasks: list[Mapping[str, object]],
    *,
    workspace_root: str | Path,
) -> None:
    root = Path(workspace_root).resolve()
    checkout = (root / str(repository["local_path"])).resolve()
    if checkout == root or root not in checkout.parents or not checkout.is_dir():
        _revision_error("sealed repository checkout is missing or outside the workspace")
    if _git(checkout, "rev-parse", "HEAD") != repository["frozen_commit"]:
        _revision_error("sealed repository head has drifted")
    if _git(checkout, "rev-parse", "HEAD^{tree}") != repository["frozen_tree"]:
        _revision_error("sealed repository tree has drifted")
    if _git(checkout, "remote", "get-url", "origin") != repository["remote"]:
        _revision_error("sealed repository remote identity has drifted")
    if _git(checkout, "describe", "--tags", "--exact-match", "HEAD") != repository["frozen_tag"]:
        _revision_error("sealed repository tag has drifted")
    if _git(checkout, "status", "--porcelain"):
        _revision_error("sealed repository checkout is not clean")
    license_path = checkout / str(repository["license_path"])
    if _file_digest(license_path) != repository["license_digest"]:
        _revision_error("sealed repository license has drifted")

    frozen_commit = str(repository["frozen_commit"])
    for task in tasks:
        scope = task["revision_scope"]
        target = str(scope["target"])
        if _git(checkout, "merge-base", "--is-ancestor", target, frozen_commit) != "":
            _revision_error("task revision is not reachable from the frozen release")
        if scope["kind"] == "PARENT_TO_TARGET":
            if _git(checkout, "rev-parse", f"{target}^") != scope["parent"]:
                _revision_error("task parent revision has drifted")
        for path in task["allowed_paths"]:
            _git(checkout, "cat-file", "-e", f"{target}:{path}")


def _verify_repository_entry(repository: Mapping[str, object]) -> None:
    required = {
        "repository_id",
        "remote",
        "local_path",
        "frozen_tag",
        "frozen_commit",
        "frozen_tree",
        "license_path",
        "license_digest",
    }
    if set(repository) != required:
        _invalid("product validation repository fields are incomplete")
    text_fields = required - {"frozen_commit", "frozen_tree", "license_digest"}
    if any(not _clean_text(repository.get(field)) for field in text_fields):
        _invalid("product validation repository text field is invalid")
    if not _hex_identifier(repository["frozen_commit"], 40):
        _invalid("product validation repository commit is invalid")
    if not _hex_identifier(repository["frozen_tree"], 40):
        _invalid("product validation repository tree is invalid")
    if not _sha256(repository["license_digest"]):
        _invalid("product validation repository license digest is invalid")
    _verify_relative_path(repository["local_path"])
    _verify_relative_path(repository["license_path"])


def _verify_task_entry(
    task: Mapping[str, object], repository: Mapping[str, object]
) -> None:
    required = {
        "task_id",
        "repository_id",
        "category",
        "question",
        "revision_scope",
        "allowed_paths",
        "acceptance_dimensions",
    }
    if set(task) != required:
        _invalid("product validation task fields are incomplete")
    for field in ("task_id", "repository_id", "category", "question"):
        if not _clean_text(task.get(field)):
            _invalid("product validation task text field is invalid")
    scope = task["revision_scope"]
    if not isinstance(scope, Mapping) or set(scope) != {"kind", "parent", "target"}:
        _invalid("product validation task revision scope is invalid")
    if scope["kind"] not in {"FROZEN_SNAPSHOT", "PARENT_TO_TARGET"}:
        _invalid("product validation task revision kind is invalid")
    if not _hex_identifier(scope["target"], 40):
        _invalid("product validation task target revision is invalid")
    if scope["kind"] == "FROZEN_SNAPSHOT":
        if scope["target"] != repository["frozen_commit"] or scope["parent"] is not None:
            _invalid("snapshot task must use the frozen repository revision")
    elif not _hex_identifier(scope["parent"], 40):
        _invalid("comparison task parent revision is invalid")
    paths = task["allowed_paths"]
    if not isinstance(paths, list) or not paths or len(set(paths)) != len(paths):
        _invalid("product validation task paths are missing or duplicated")
    for path in paths:
        _verify_relative_path(path)
    dimensions = task["acceptance_dimensions"]
    if (
        not isinstance(dimensions, list)
        or len(dimensions) < 3
        or any(not _clean_text(item) for item in dimensions)
        or len(set(dimensions)) != len(dimensions)
    ):
        _invalid("product validation acceptance dimensions are incomplete")


def _suite_digest(suite: Mapping[str, object]) -> str:
    return digest_of({key: value for key, value in suite.items() if key != "suite_digest"}).value


def _git(checkout: Path, *arguments: str) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(checkout), *arguments],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise DomainError(
            ErrorCode.SOURCE_REVISION_INCONSISTENT,
            "sealed repository verification failed",
        ) from exc
    return result.stdout.strip()


def _file_digest(path: Path) -> str:
    try:
        content = path.read_bytes()
    except OSError as exc:
        raise DomainError(
            ErrorCode.SOURCE_REVISION_INCONSISTENT,
            "sealed repository license cannot be read",
        ) from exc
    return "sha256:" + hashlib.sha256(content).hexdigest()


def _clean_text(value: object) -> bool:
    return isinstance(value, str) and bool(value) and value == value.strip()


def _hex_identifier(value: object, length: int) -> bool:
    return (
        isinstance(value, str)
        and len(value) == length
        and all(character in "0123456789abcdef" for character in value)
    )


def _sha256(value: object) -> bool:
    return isinstance(value, str) and value.startswith("sha256:") and _hex_identifier(
        value.removeprefix("sha256:"), 64
    )


def _verify_relative_path(value: object) -> None:
    if not _clean_text(value):
        _invalid("product validation path is invalid")
    path = Path(value)
    if path.is_absolute() or ".." in path.parts or "." in path.parts:
        _invalid("product validation path escapes its declared boundary")


def _invalid(message: str) -> None:
    raise DomainError(ErrorCode.AUTHORITY_RECORD_INCONSISTENT, message)


def _revision_error(message: str) -> None:
    raise DomainError(ErrorCode.SOURCE_REVISION_INCONSISTENT, message)
