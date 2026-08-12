"""Independent, stdlib-only comparator for ITER-005 SLICE-002 populations."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from typing import Mapping, Sequence


SUITE_SCHEMA = "SWM-WORLD-MODEL-HELD-OUT-SUITE@2"
POPULATION_SCHEMA = "SWM-WORLD-MODEL-COMPARISON-POPULATION@2"
REPORT_SCHEMA = "SWM-WORLD-MODEL-COMPARISON-REPORT@1"
SURFACES = ("WORLD_MODEL", "CONTROLLED_DIRECT", "MATURE_SOURCE_AGENT")
_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
_COMMIT = re.compile(r"^[0-9a-f]{40}$")
_OUTCOMES = {
    "SUPPORTED",
    "SUPPORTED_NEGATIVE",
    "ENTITY_RESOLUTION_LIMITATION",
    "KNOWLEDGE_GAP",
}
_PROVIDER = {
    "provider_type": "VOLCENGINE_ARK",
    "adapter": "openai-chat-completions-no-tools@8",
    "requested_model": "glm-5-2-260617",
    "observed_model": "glm-5.2",
    "endpoint": (
        "https://ark.cn-beijing.volces.com:443/"
        "api/coding/v3/chat/completions"
    ),
    "credential_reference": "env:ARK_API_KEY",
    "conformance_digest": (
        "sha256:c86aad995802b8dcf687fafcbaf36bccb02768ba55b40151ec9aa4704518cade"
    ),
    "qualification_digest": (
        "sha256:005b1bf43c76a64d123b0184cdac1a9e844331896e7ede6279875881d9bcc62c"
    ),
}
_MATURE_AGENT = {
    "implementation": "Codex CLI",
    "binary_path": "/Applications/ChatGPT.app/Contents/Resources/codex",
    "version": "codex-cli 0.147.0-alpha.1.2",
    "binary_sha256": (
        "sha256:9f6748b4ab10ffc92c28b9ccedae89e61a302bbc011df7d276ee38f55906e481"
    ),
    "answer_schema_sha256": (
        "sha256:34b2863dd81ab129beccf86d76d191e293028889c4514555e5669a8b48b2e563"
    ),
    "model": "gpt-5.6-sol",
    "reasoning_effort": "low",
    "workspace": "ISOLATED_EXACT_POM_SOURCE_CLOSURE_AND_CONTROL_SCHEMA_ONLY",
    "network": "DENY",
    "shell_environment": "INHERIT_NONE_LOGIN_DENY_EXPLICIT_NON_SECRET_SET",
    "command_contract": {
        "argv_order": [
            "BINARY",
            "GLOBAL_FLAGS",
            "SUBCOMMAND",
            "EXEC_FLAGS",
            "PROMPT",
        ],
        "global_flags": ["--ask-for-approval", "never"],
        "subcommand": "exec",
        "exec_flags": [
            "--ephemeral",
            "--ignore-user-config",
            "--ignore-rules",
            "--strict-config",
            "--model",
            "gpt-5.6-sol",
            "--config",
            'model_reasoning_effort="low"',
            "--config",
            'web_search="disabled"',
            "--config",
            "features.apps=false",
            "--config",
            "features.multi_agent=false",
            "--config",
            "allow_login_shell=false",
            "--config",
            'shell_environment_policy.inherit="none"',
            "--config",
            "shell_environment_policy.ignore_default_excludes=false",
            "--config",
            'shell_environment_policy.set={PATH="/usr/bin:/bin:/usr/sbin:/sbin",LANG="C",LC_ALL="C",TZ="UTC"}',
            "--config",
            'default_permissions="mature_source"',
            "--config",
            'permissions.mature_source.filesystem={":root"="deny",":minimal"="read",":tmpdir"="deny",":slash_tmp"="deny",":workspace_roots"={"."="read"}}',
            "--config",
            "permissions.mature_source.network.enabled=false",
            "--cd",
            "<ISOLATED_WORKSPACE>",
            "--output-schema",
            "<CONTROL_SCHEMA>",
            "--output-last-message",
            "<LAST_MESSAGE>",
            "--json",
        ],
    },
}


class EvaluationFailure(RuntimeError):
    """A sealed population or comparison invariant failed."""


def _canonical(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _digest(schema: str, core: object) -> str:
    return "sha256:" + hashlib.sha256(_canonical([schema, core])).hexdigest()


def _load(path: Path, schema: str) -> dict[str, object]:
    raw = path.read_bytes()
    value = json.loads(raw, object_pairs_hook=_unique_object)
    if not isinstance(value, dict) or _canonical(value) != raw:
        raise EvaluationFailure(f"{path} is not one canonical JSON object")
    if value.get("schema") != schema:
        raise EvaluationFailure(f"{path} has an unexpected schema")
    core = {key: item for key, item in value.items() if key != "document_digest"}
    if value.get("document_digest") != _digest(schema, core):
        raise EvaluationFailure(f"{path} has an invalid document digest")
    return value


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise EvaluationFailure("duplicate JSON key")
        value[key] = item
    return value


def _file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _validate_suite_boundary(suite: Mapping[str, object]) -> None:
    expected = {
        "schema",
        "environment",
        "evaluation_subject_commit",
        "evaluation_subject_tree",
        "sealed_before_world_model_results",
        "world_model_result_count_at_seal",
        "controlled_direct_result_count_at_seal",
        "mature_source_agent_result_count_at_seal",
        "fixture",
        "catalog_digest",
        "product_oracle_digest",
        "independent_evaluator_digest",
        "comparison_surfaces",
        "comparison_protocols",
        "source_closures",
        "cases",
        "production_activation",
        "document_digest",
    }
    core = {key: item for key, item in suite.items() if key != "document_digest"}
    if (
        set(suite) != expected
        or suite.get("schema") != SUITE_SCHEMA
        or suite.get("environment") != "EVALUATION_ONLY"
        or not isinstance(suite.get("evaluation_subject_commit"), str)
        or not _COMMIT.fullmatch(str(suite.get("evaluation_subject_commit")))
        or not isinstance(suite.get("evaluation_subject_tree"), str)
        or not _COMMIT.fullmatch(str(suite.get("evaluation_subject_tree")))
        or suite.get("sealed_before_world_model_results") is not True
        or suite.get("world_model_result_count_at_seal") != 0
        or suite.get("controlled_direct_result_count_at_seal") != 0
        or suite.get("mature_source_agent_result_count_at_seal") != 0
        or not isinstance(suite.get("fixture"), dict)
        or not isinstance(suite.get("catalog_digest"), str)
        or not _DIGEST.fullmatch(str(suite.get("catalog_digest")))
        or not isinstance(suite.get("product_oracle_digest"), str)
        or not _DIGEST.fullmatch(str(suite.get("product_oracle_digest")))
        or suite.get("independent_evaluator_digest")
        != _file_digest(Path(__file__).resolve(strict=True))
        or suite.get("comparison_surfaces") != list(SURFACES)
        or suite.get("production_activation") != "NOT_EXECUTED"
        or suite.get("document_digest") != _digest(SUITE_SCHEMA, core)
    ):
        raise EvaluationFailure("held-out suite boundary is invalid")
    _validate_comparison_protocols(suite.get("comparison_protocols"))
    _validate_source_closures(
        suite.get("source_closures"),
        suite.get("fixture"),
    )


def _validate_comparison_protocols(value: object) -> None:
    if not isinstance(value, dict) or set(value) != {
        "execution_order",
        "failure_policy",
        "runs_per_case",
        "WORLD_MODEL",
        "CONTROLLED_DIRECT",
        "MATURE_SOURCE_AGENT",
    }:
        raise EvaluationFailure("comparison protocol set is not closed")
    if (
        value.get("execution_order")
        != [
            "CONTROLLED_DIRECT",
            "MATURE_SOURCE_AGENT",
            "SEAL_BASELINE_POPULATIONS",
            "WORLD_MODEL",
        ]
        or value.get("failure_policy")
        != "PRESERVE_ALL_TERMINALS_NO_RETRY_NO_SELECTION_NO_INTERPOLATION"
        or value.get("runs_per_case") != 1
    ):
        raise EvaluationFailure("comparison execution protocol is invalid")

    world = value.get("WORLD_MODEL")
    direct = value.get("CONTROLLED_DIRECT")
    mature = value.get("MATURE_SOURCE_AGENT")
    if not isinstance(world, dict) or set(world) != {
        "entrypoint",
        "provider",
        "payload_boundary",
        "external_task_count_per_case",
        "provider_call_count_observability",
        "provider_call_count_per_case",
        "controller_retry_count_per_case",
        "result_visibility",
        "production_activation",
    }:
        raise EvaluationFailure("World Model comparison protocol is invalid")
    if world != {
        "entrypoint": "software_world_model.interface.world_model_http",
        "provider": _PROVIDER,
        "payload_boundary": "ORIGINAL_QUESTION_AND_NO_PAYLOAD_PUBLISHED_STRUCTURE",
        "external_task_count_per_case": 1,
        "provider_call_count_observability": (
            "EXACT_PRODUCT_GATEWAY_COUNTER_ON_VERIFIED_TERMINAL"
        ),
        "provider_call_count_per_case": 1,
        "controller_retry_count_per_case": 0,
        "result_visibility": "AFTER_BOTH_BASELINE_POPULATIONS_ARE_SEALED",
        "production_activation": "NOT_EXECUTED",
    }:
        raise EvaluationFailure("World Model comparison protocol drifted")

    runner_fields = {
        "runner_path",
        "runner_digest",
        "provider",
        "payload_boundary",
        "external_task_count_per_case",
        "provider_call_count_observability",
        "provider_call_count_per_case",
        "controller_retry_count_per_case",
        "max_output_tokens_per_case",
        "response_contract",
        "oracle_visibility",
        "result_visibility",
        "production_activation",
    }
    if not isinstance(direct, dict) or set(direct) != runner_fields:
        raise EvaluationFailure("controlled Direct comparison protocol is invalid")
    direct_digest = direct.get("runner_digest")
    if (
        direct.get("runner_path")
        != "validation/structure_world_model_iteration_005/slice2_comparison.py"
        or not isinstance(direct_digest, str)
        or not _DIGEST.fullmatch(direct_digest)
        or direct.get("provider") != _PROVIDER
        or direct.get("payload_boundary")
        != "ORIGINAL_QUESTION_AND_EXACT_SEALED_POM_SOURCE_CLOSURE"
        or direct.get("external_task_count_per_case") != 1
        or direct.get("provider_call_count_observability")
        != "EXACT_DIRECT_GATEWAY_COUNTER_ON_TERMINAL"
        or direct.get("provider_call_count_per_case") != 1
        or direct.get("controller_retry_count_per_case") != 0
        or direct.get("max_output_tokens_per_case") != 4096
        or direct.get("response_contract")
        != "STRICT_JSON_OBJECT_ANSWER_STRING_NO_TRAILING_TEXT"
        or direct.get("oracle_visibility") != "NONE"
        or direct.get("result_visibility")
        != "SEALED_BEFORE_FIRST_WORLD_MODEL_RESULT"
        or direct.get("production_activation") != "NOT_EXECUTED"
    ):
        raise EvaluationFailure("controlled Direct comparison protocol drifted")

    mature_fields = (
        runner_fields
        - {"provider", "max_output_tokens_per_case", "response_contract"}
    ) | {"agent"}
    if not isinstance(mature, dict) or set(mature) != mature_fields:
        raise EvaluationFailure("mature Source Agent comparison protocol is invalid")
    if (
        mature.get("runner_path") != direct.get("runner_path")
        or mature.get("runner_digest") != direct_digest
        or mature.get("agent") != _MATURE_AGENT
        or mature.get("payload_boundary")
        != "ORIGINAL_QUESTION_AND_EXACT_SEALED_POM_SOURCE_CLOSURE"
        or mature.get("external_task_count_per_case") != 1
        or mature.get("provider_call_count_observability")
        != "UNOBSERVABLE_FROM_CODEX_CLI_EVENT_BOUNDARY"
        or mature.get("provider_call_count_per_case") is not None
        or mature.get("controller_retry_count_per_case") != 0
        or mature.get("oracle_visibility") != "NONE"
        or mature.get("result_visibility")
        != "SEALED_BEFORE_FIRST_WORLD_MODEL_RESULT"
        or mature.get("production_activation") != "NOT_EXECUTED"
    ):
        raise EvaluationFailure("mature Source Agent comparison protocol drifted")


def _validate_source_closures(value: object, fixture: object) -> None:
    if not isinstance(value, dict) or not value:
        raise EvaluationFailure("sealed source closures are absent")
    if not isinstance(fixture, dict) or set(fixture) != {
        "seed",
        "suffix",
        "workspace_id",
        "revisions",
        "read_sets",
    }:
        raise EvaluationFailure("sealed fixture identity is invalid")
    revisions = fixture.get("revisions")
    read_sets = fixture.get("read_sets")
    if (
        not isinstance(revisions, dict)
        or set(revisions) != {"r1", "r2"}
        or any(
            not isinstance(item, str) or not _COMMIT.fullmatch(item)
            for item in revisions.values()
        )
        or not isinstance(read_sets, dict)
        or set(read_sets) != {"r1", "r2", "ordered"}
        or any(not isinstance(item, str) or not item for item in read_sets.values())
        or set(value) != set(read_sets.values())
    ):
        raise EvaluationFailure("sealed fixture revisions or Read Sets are invalid")
    for read_set_id, closure in value.items():
        if not isinstance(read_set_id, str) or not read_set_id:
            raise EvaluationFailure("sealed source closure identity is invalid")
        if not isinstance(closure, dict) or set(closure) != {"snapshots"}:
            raise EvaluationFailure(f"{read_set_id}: source closure shape is invalid")
        snapshots = closure.get("snapshots")
        if not isinstance(snapshots, list) or len(snapshots) not in {1, 2}:
            raise EvaluationFailure(f"{read_set_id}: source snapshots are invalid")
        labels: list[str] = []
        for snapshot in snapshots:
            if not isinstance(snapshot, dict) or set(snapshot) != {
                "label",
                "revision",
                "files",
            }:
                raise EvaluationFailure(f"{read_set_id}: snapshot shape is invalid")
            label = snapshot.get("label")
            revision = snapshot.get("revision")
            files = snapshot.get("files")
            if (
                label not in {"A", "B"}
                or not isinstance(revision, str)
                or not _COMMIT.fullmatch(revision)
                or not isinstance(files, list)
                or not files
            ):
                raise EvaluationFailure(f"{read_set_id}: snapshot identity is invalid")
            labels.append(str(label))
            paths: list[str] = []
            for item in files:
                if not isinstance(item, dict) or set(item) != {
                    "path",
                    "sha256",
                    "size",
                }:
                    raise EvaluationFailure(f"{read_set_id}: source file is invalid")
                path = item.get("path")
                digest = item.get("sha256")
                size = item.get("size")
                if (
                    not isinstance(path, str)
                    or not path
                    or path.startswith("/")
                    or ".." in Path(path).parts
                    or not path.endswith("pom.xml")
                    or not isinstance(digest, str)
                    or not _DIGEST.fullmatch(digest)
                    or not isinstance(size, int)
                    or isinstance(size, bool)
                    or size < 1
                ):
                    raise EvaluationFailure(f"{read_set_id}: source file is invalid")
                paths.append(path)
            if len(paths) != len(set(paths)):
                raise EvaluationFailure(f"{read_set_id}: source file paths repeat")
        if labels != (["A"] if len(snapshots) == 1 else ["A", "B"]):
            raise EvaluationFailure(f"{read_set_id}: snapshot labels are invalid")
    expected_revisions = {
        read_sets["r1"]: [revisions["r1"]],
        read_sets["r2"]: [revisions["r2"]],
        read_sets["ordered"]: [revisions["r1"], revisions["r2"]],
    }
    for read_set_id, expected in expected_revisions.items():
        closure = value[read_set_id]
        assert isinstance(closure, dict)
        snapshots = closure["snapshots"]
        assert isinstance(snapshots, list)
        observed = [snapshot["revision"] for snapshot in snapshots]
        if observed != expected:
            raise EvaluationFailure(
                f"{read_set_id}: source closure revisions drifted from fixture"
            )


def _case_map(suite: Mapping[str, object]) -> dict[str, Mapping[str, object]]:
    raw = suite.get("cases")
    if not isinstance(raw, list) or not raw:
        raise EvaluationFailure("held-out suite has no cases")
    closures = suite.get("source_closures")
    assert isinstance(closures, dict)
    result: dict[str, Mapping[str, object]] = {}
    for item in raw:
        if not isinstance(item, dict):
            raise EvaluationFailure("held-out suite case is invalid")
        case_id = item.get("case_id")
        if not isinstance(case_id, str) or case_id in result:
            raise EvaluationFailure("held-out suite case IDs are invalid")
        expected = {
            "case_id",
            "read_set_id",
            "question",
            "expected_outcome",
            "required_tokens",
            "forbidden_tokens",
            "outcome_markers_any",
        }
        if set(item) != expected:
            raise EvaluationFailure(f"{case_id}: case shape is not closed")
        if (
            not isinstance(item.get("read_set_id"), str)
            or not item.get("read_set_id")
            or item.get("read_set_id") not in closures
            or not isinstance(item.get("question"), str)
            or not item.get("question")
            or item.get("question") != str(item.get("question")).strip()
            or item.get("expected_outcome") not in _OUTCOMES
        ):
            raise EvaluationFailure(f"{case_id}: case identity is invalid")
        for key in ("required_tokens", "forbidden_tokens", "outcome_markers_any"):
            values = item.get(key)
            if not isinstance(values, list) or any(
                not isinstance(value, str) or not value for value in values
            ):
                raise EvaluationFailure(f"{case_id}: {key} is invalid")
        result[case_id] = item
    return result


def _population_map(
    population: Mapping[str, object],
    *,
    expected_surface: str,
    suite_digest: str,
    case_ids: set[str],
) -> dict[str, Mapping[str, object]]:
    expected_population = {
        "schema",
        "surface",
        "suite_digest",
        "results",
        "failures_preserved",
        "missing_outputs_interpolated",
        "production_activation",
        "document_digest",
    }
    core = {
        key: item for key, item in population.items() if key != "document_digest"
    }
    if (
        set(population) != expected_population
        or population.get("schema") != POPULATION_SCHEMA
        or population.get("document_digest")
        != _digest(POPULATION_SCHEMA, core)
        or population.get("surface") != expected_surface
        or population.get("suite_digest") != suite_digest
        or population.get("failures_preserved") is not True
        or population.get("missing_outputs_interpolated") is not False
        or population.get("production_activation") != "NOT_EXECUTED"
    ):
        raise EvaluationFailure(f"{expected_surface}: population boundary is invalid")
    raw = population.get("results")
    if not isinstance(raw, list):
        raise EvaluationFailure(f"{expected_surface}: results are invalid")
    results: dict[str, Mapping[str, object]] = {}
    for item in raw:
        if not isinstance(item, dict):
            raise EvaluationFailure(f"{expected_surface}: terminal is invalid")
        case_id = item.get("case_id")
        if not isinstance(case_id, str) or case_id in results:
            raise EvaluationFailure(f"{expected_surface}: duplicate terminal")
        if set(item) != {
            "case_id",
            "status",
            "answer_body",
            "failure_code",
            "external_task_count",
            "provider_call_count",
            "terminal_digest",
        }:
            raise EvaluationFailure(f"{expected_surface}/{case_id}: shape is not closed")
        if item.get("status") not in {"SUCCESS", "FAILURE"}:
            raise EvaluationFailure(f"{expected_surface}/{case_id}: status is invalid")
        external_task_count = item.get("external_task_count")
        provider_call_count = item.get("provider_call_count")
        terminal_digest = item.get("terminal_digest")
        if (
            not isinstance(external_task_count, int)
            or isinstance(external_task_count, bool)
            or external_task_count not in {0, 1}
            or not isinstance(terminal_digest, str)
            or not _DIGEST.fullmatch(terminal_digest)
        ):
            raise EvaluationFailure(
                f"{expected_surface}/{case_id}: execution identity is invalid"
            )
        if expected_surface == "MATURE_SOURCE_AGENT":
            if provider_call_count is not None:
                raise EvaluationFailure(
                    f"{expected_surface}/{case_id}: Provider calls are not observable"
                )
        elif provider_call_count is not None and (
            not isinstance(provider_call_count, int)
            or isinstance(provider_call_count, bool)
            or provider_call_count not in {0, 1}
        ):
            raise EvaluationFailure(
                f"{expected_surface}/{case_id}: Provider call count is invalid"
            )
        if item.get("status") == "SUCCESS":
            if not isinstance(item.get("answer_body"), str) or not item.get("answer_body"):
                raise EvaluationFailure(f"{expected_surface}/{case_id}: answer is empty")
            if item.get("failure_code") is not None:
                raise EvaluationFailure(f"{expected_surface}/{case_id}: false failure code")
            if external_task_count != 1 or (
                expected_surface != "MATURE_SOURCE_AGENT"
                and provider_call_count != 1
            ):
                raise EvaluationFailure(
                    f"{expected_surface}/{case_id}: successful execution count drifted"
                )
        elif (
            item.get("answer_body") is not None
            or not isinstance(item.get("failure_code"), str)
            or not item.get("failure_code")
        ):
            raise EvaluationFailure(f"{expected_surface}/{case_id}: failure was altered")
        results[case_id] = item
    if set(results) != case_ids:
        raise EvaluationFailure(
            f"{expected_surface}: terminal population differs from the suite"
        )
    return results


def _score(case: Mapping[str, object], terminal: Mapping[str, object]) -> dict[str, object]:
    if terminal["status"] == "FAILURE":
        return {
            "eligible": False,
            "completeness_ppm": None,
            "major_error": False,
            "missing_tokens": [],
            "forbidden_hits": [],
            "outcome_marker_present": False,
        }
    answer = str(terminal["answer_body"])
    folded = answer.casefold()
    required = [str(item) for item in case["required_tokens"]]
    missing = [item for item in required if item.casefold() not in folded]
    forbidden = [
        str(item)
        for item in case["forbidden_tokens"]
        if str(item).casefold() in folded
    ]
    markers = [str(item) for item in case["outcome_markers_any"]]
    marker_present = not markers or any(item.casefold() in folded for item in markers)
    completeness = (
        1_000_000
        if not required
        else ((len(required) - len(missing)) * 1_000_000) // len(required)
    )
    return {
        "eligible": True,
        "completeness_ppm": completeness,
        "major_error": bool(forbidden) or not marker_present,
        "missing_tokens": missing,
        "forbidden_hits": forbidden,
        "outcome_marker_present": marker_present,
    }


def evaluate(
    suite: Mapping[str, object],
    populations: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    _validate_suite_boundary(suite)
    if set(populations) != set(SURFACES):
        raise EvaluationFailure("comparison surface set is not closed")
    cases = _case_map(suite)
    suite_digest = str(suite["document_digest"])
    indexed = {
        surface: _population_map(
            populations[surface],
            expected_surface=surface,
            suite_digest=suite_digest,
            case_ids=set(cases),
        )
        for surface in SURFACES
    }
    rows: list[dict[str, object]] = []
    blockers: list[str] = []
    for case_id, case in cases.items():
        scores = {
            surface: _score(case, indexed[surface][case_id])
            for surface in SURFACES
        }
        world = indexed["WORLD_MODEL"][case_id]
        if world.get("external_task_count") != 1:
            blockers.append(f"{case_id}: World Model task count is not exactly one")
        if world.get("provider_call_count") != 1:
            blockers.append(f"{case_id}: World Model call count is not exactly one")
        if not scores["WORLD_MODEL"]["eligible"]:
            blockers.append(f"{case_id}: World Model terminal failed")
        if scores["WORLD_MODEL"]["major_error"]:
            blockers.append(f"{case_id}: World Model has a major error")
        eligible_baselines = [
            int(scores[surface]["completeness_ppm"])
            for surface in ("CONTROLLED_DIRECT", "MATURE_SOURCE_AGENT")
            if scores[surface]["eligible"]
        ]
        if len(eligible_baselines) != 2:
            blockers.append(f"{case_id}: both baseline outputs must be eligible")
            stronger = None
        else:
            stronger = max(eligible_baselines)
            if int(scores["WORLD_MODEL"]["completeness_ppm"]) < stronger:
                blockers.append(f"{case_id}: World Model completeness regressed")
        rows.append(
            {
                "case_id": case_id,
                "expected_outcome": case["expected_outcome"],
                "scores": scores,
                "stronger_baseline_completeness_ppm": stronger,
            }
        )
    core = {
        "schema": REPORT_SCHEMA,
        "status": "PASS" if not blockers else "FAIL",
        "suite_digest": suite_digest,
        "case_count": len(cases),
        "rows": rows,
        "blockers": blockers,
        "failures_filtered": False,
        "missing_outputs_interpolated": False,
        "production_activation": "NOT_EXECUTED",
    }
    return {**core, "document_digest": _digest(REPORT_SCHEMA, core)}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", required=True)
    parser.add_argument("--world-model", required=True)
    parser.add_argument("--controlled-direct", required=True)
    parser.add_argument("--mature-source-agent", required=True)
    parser.add_argument("--output", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    suite = _load(Path(arguments.suite).resolve(strict=True), SUITE_SCHEMA)
    populations = {
        "WORLD_MODEL": _load(
            Path(arguments.world_model).resolve(strict=True), POPULATION_SCHEMA
        ),
        "CONTROLLED_DIRECT": _load(
            Path(arguments.controlled_direct).resolve(strict=True), POPULATION_SCHEMA
        ),
        "MATURE_SOURCE_AGENT": _load(
            Path(arguments.mature_source_agent).resolve(strict=True),
            POPULATION_SCHEMA,
        ),
    }
    report = evaluate(suite, populations)
    output = Path(arguments.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists() or output.is_symlink():
        raise EvaluationFailure("comparison output already exists")
    output.write_bytes(_canonical(report))
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
