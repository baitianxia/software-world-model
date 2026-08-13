"""Execute the sealed ITER-006 Java comparison without hidden retries.

Evaluator-only expectations never enter an external payload.  A suite-bound
user disclosure receipt is verified before output creation or dispatch.
"""

from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Mapping, Sequence
from urllib import error as urllib_error
from urllib import request as urllib_request
from urllib.parse import urlsplit

from software_world_model.ai_infrastructure import (
    AuthorizedInputItem,
    AuthorizedInputManifest,
    InputDisposition,
    ModelExecutionContext,
    ModelGateway,
    OutputSchemaDefinition,
    PlatformProposalMode,
    RecordingChatCompletionsTransport,
    RuntimeAccessMode,
    UrllibVolcengineArkChatTransport,
    VolcengineArkChatCompletionsNoToolsAdapter,
    VolcengineArkModelConfiguration,
    load_ark_chat_conformance_qualification,
)
from software_world_model.cross_cutting import DomainError, canonical_json_bytes
from software_world_model.infrastructure import (
    SqliteDatabase,
    SqliteModelGatewayRepository,
)

from . import live_evaluator


AUTHORIZATION_SCHEMA = "SWM-JAVA-WORLD-MODEL-COMPARISON-AUTHORIZATION@1"
BASELINE_SEAL_SCHEMA = "SWM-JAVA-WORLD-MODEL-BASELINE-SEAL@1"
INPUT_PACKET_SCHEMA = "SWM-JAVA-WORLD-MODEL-COMPARISON-INPUT@1"
TERMINAL_EVIDENCE_SCHEMA = "SWM-JAVA-WORLD-MODEL-COMPARISON-TERMINAL@1"
POPULATION_SCHEMA = live_evaluator.POPULATION_SCHEMA
SUITE_SCHEMA = live_evaluator.SUITE_SCHEMA
_AUTHORIZED_SCOPES = [
    "WORLD_MODEL_ORIGINAL_QUESTION_AND_NO_PAYLOAD_PUBLISHED_STRUCTURE",
    "CONTROLLED_DIRECT_ORIGINAL_QUESTION_AND_EXACT_SEALED_JAVA_SOURCE_CLOSURE",
    "MATURE_SOURCE_AGENT_ORIGINAL_QUESTION_AND_EXACT_SEALED_JAVA_SOURCE_CLOSURE",
]
_DIRECT_SCHEMA_REF = "iter-006-controlled-direct-java-answer@1"
_DIRECT_PROMPT_REF = "iter-006-controlled-direct-java-source-answer@1"
_DIRECT_MAX_OUTPUT_TOKENS = 4096
_DIRECT_RESPONSE_CONTRACT = "STRICT_JSON_OBJECT_ANSWER_STRING_NO_TRAILING_TEXT"
_DIRECT_INSTRUCTION = (
    "Answer the user's question in Chinese using only the exact Java sources "
    "in the second message. Preserve A/B revision labels, use fully qualified "
    "type and method signatures where useful, cite relative source paths, and "
    "distinguish source-level direct calls from runtime dispatch. State a "
    "limitation for reflection, dependency injection, runtime targets, or "
    "design intent that the source closure cannot prove. Do not use an oracle "
    "or any World Model result. Return exactly one valid JSON object shaped as "
    '{"answer":"..."}, with no Markdown fence or trailing text. Escape every '
    "double quote inside the answer string (or use Chinese quotation marks)."
)
_DIRECT_OUTPUT = OutputSchemaDefinition(
    "iter_006_controlled_direct_java_answer",
    {
        "type": "object",
        "properties": {"answer": {"type": "string", "minLength": 1}},
        "required": ["answer"],
        "additionalProperties": False,
    },
)
_MATURE_OUTPUT_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "properties": {
        "answer": {"type": "string", "minLength": 1},
        "claims": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "properties": {
                    "claim": {"type": "string", "minLength": 1},
                    "source_locators": {
                        "type": "array",
                        "items": {"type": "string", "minLength": 1},
                    },
                },
                "required": ["claim", "source_locators"],
                "additionalProperties": False,
            },
        },
        "limitations": {
            "type": "array",
            "items": {"type": "string", "minLength": 1},
        },
    },
    "required": ["answer", "claims", "limitations"],
    "additionalProperties": False,
}


class ComparisonFailure(RuntimeError):
    """A disclosure, input-closure, or execution invariant failed."""


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


def _document(schema: str, core: Mapping[str, object]) -> dict[str, object]:
    return {**core, "document_digest": _digest(schema, core)}


def _file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise ComparisonFailure("duplicate JSON key")
        value[key] = item
    return value


def _load_document(path: Path, schema: str) -> dict[str, object]:
    raw = path.read_bytes()
    try:
        value = json.loads(raw, object_pairs_hook=_unique_object)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ComparisonFailure(f"{path} is not valid JSON") from exc
    if not isinstance(value, dict) or _canonical(value) != raw:
        raise ComparisonFailure(f"{path} is not one canonical JSON object")
    core = {key: item for key, item in value.items() if key != "document_digest"}
    if (
        value.get("schema") != schema
        or value.get("document_digest") != _digest(schema, core)
    ):
        raise ComparisonFailure(f"{path} has an invalid document seal")
    return value


def _write_new(path: Path, value: object) -> None:
    _write_bytes_new(path, _canonical(value))


def _write_bytes_new(path: Path, value: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as stream:
            stream.write(value)
    except FileExistsError as exc:
        raise ComparisonFailure(f"output already exists: {path}") from exc


def _load_suite(path: Path) -> dict[str, object]:
    suite = _load_document(path, SUITE_SCHEMA)
    live_evaluator.validate_suite(suite)
    protocols = suite["comparison_protocols"]
    assert isinstance(protocols, dict)
    direct = protocols["CONTROLLED_DIRECT"]
    assert isinstance(direct, dict)
    if direct.get("runner_digest") != _file_digest(Path(__file__).resolve(strict=True)):
        raise ComparisonFailure("comparison runner bytes drifted from sealed suite")
    if (
        direct.get("max_output_tokens_per_case") != _DIRECT_MAX_OUTPUT_TOKENS
        or direct.get("response_contract") != _DIRECT_RESPONSE_CONTRACT
    ):
        raise ComparisonFailure("controlled Direct response envelope drifted")
    return suite


def disclosure_set_digest(suite: Mapping[str, object]) -> str:
    cases = suite.get("cases")
    if not isinstance(cases, list):
        raise ComparisonFailure("held-out suite cases are invalid")
    disclosed = [
        {
            "case_id": case["case_id"],
            "read_set_id": case["read_set_id"],
            "question": case["question"],
        }
        for case in cases
        if isinstance(case, dict)
    ]
    if len(disclosed) != len(cases):
        raise ComparisonFailure("held-out suite cases are invalid")
    return _digest("SWM-JAVA-WORLD-MODEL-DISCLOSURE-SET@1", disclosed)


def _authorization_core(
    suite: Mapping[str, object],
    *,
    status: str,
    live_dispatch_authorized: bool,
    authorized_at: str | None,
    authorization_ref: str,
) -> dict[str, object]:
    return {
        "schema": AUTHORIZATION_SCHEMA,
        "status": status,
        "live_dispatch_authorized": live_dispatch_authorized,
        "authorized_by": "user",
        "authorized_at": authorized_at,
        "authorization_ref": authorization_ref,
        "suite_digest": suite["document_digest"],
        "disclosure_set_digest": disclosure_set_digest(suite),
        "case_count": len(suite["cases"]),
        "scopes": list(_AUTHORIZED_SCOPES),
        "production_activation": "NOT_EXECUTED",
    }


def pending_authorization(suite: Mapping[str, object]) -> dict[str, object]:
    return _document(
        AUTHORIZATION_SCHEMA,
        _authorization_core(
            suite,
            status="NOT_AUTHORIZED",
            live_dispatch_authorized=False,
            authorized_at=None,
            authorization_ref="PENDING_EXPLICIT_USER_DISCLOSURE_AUTHORIZATION",
        ),
    )


def authorized_document(
    suite: Mapping[str, object],
    *,
    authorized_at: str,
    authorization_ref: str,
) -> dict[str, object]:
    """Build a receipt only after the caller has exact user authorization."""

    return _document(
        AUTHORIZATION_SCHEMA,
        _authorization_core(
            suite,
            status="AUTHORIZED",
            live_dispatch_authorized=True,
            authorized_at=authorized_at,
            authorization_ref=authorization_ref,
        ),
    )


def _require_authorization(
    path: Path, suite: Mapping[str, object]
) -> dict[str, object]:
    value = _load_document(path, AUTHORIZATION_SCHEMA)
    expected = {
        "schema",
        "status",
        "live_dispatch_authorized",
        "authorized_by",
        "authorized_at",
        "authorization_ref",
        "suite_digest",
        "disclosure_set_digest",
        "case_count",
        "scopes",
        "production_activation",
        "document_digest",
    }
    authorized_at = value.get("authorized_at")
    try:
        parsed = (
            datetime.fromisoformat(authorized_at.replace("Z", "+00:00"))
            if isinstance(authorized_at, str)
            else None
        )
    except ValueError as exc:
        raise ComparisonFailure("authorization time is invalid") from exc
    if (
        set(value) != expected
        or value.get("status") != "AUTHORIZED"
        or value.get("live_dispatch_authorized") is not True
        or value.get("authorized_by") != "user"
        or parsed is None
        or parsed.tzinfo is None
        or parsed.utcoffset() is None
        or not isinstance(value.get("authorization_ref"), str)
        or not value.get("authorization_ref")
        or str(value.get("authorization_ref")).startswith("PENDING_")
        or value.get("suite_digest") != suite.get("document_digest")
        or value.get("disclosure_set_digest") != disclosure_set_digest(suite)
        or value.get("case_count") != len(suite["cases"])
        or value.get("scopes") != _AUTHORIZED_SCOPES
        or value.get("production_activation") != "NOT_EXECUTED"
    ):
        raise ComparisonFailure(
            "exact Java comparison disclosure is not explicitly authorized"
        )
    return value


def _git_show(repository: Path, revision: str, path: str) -> bytes:
    completed = subprocess.run(
        ("git", "-C", str(repository), "show", f"{revision}:{path}"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise ComparisonFailure(f"sealed source file is unavailable: {revision}:{path}")
    return completed.stdout


def _input_packet(
    suite: Mapping[str, object],
    case: Mapping[str, object],
    repository: Path,
    authorization: Mapping[str, object],
    *,
    surface: str,
) -> dict[str, object]:
    closures = suite["source_closures"]
    assert isinstance(closures, dict)
    closure = closures[case["read_set_id"]]
    assert isinstance(closure, dict)
    materialized: list[dict[str, object]] = []
    snapshots = closure["snapshots"]
    assert isinstance(snapshots, list)
    for snapshot in snapshots:
        assert isinstance(snapshot, dict)
        raw_files = snapshot["files"]
        assert isinstance(raw_files, list)
        files: list[dict[str, object]] = []
        for item in raw_files:
            assert isinstance(item, dict)
            raw = _git_show(repository, str(snapshot["revision"]), str(item["path"]))
            observed = "sha256:" + hashlib.sha256(raw).hexdigest()
            if observed != item["sha256"] or len(raw) != item["size"]:
                raise ComparisonFailure("sealed Java source closure drifted")
            try:
                content = raw.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise ComparisonFailure("sealed Java source is not UTF-8") from exc
            files.append(
                {"path": item["path"], "sha256": observed, "content": content}
            )
        materialized.append(
            {
                "label": snapshot["label"],
                "revision": snapshot["revision"],
                "files": files,
            }
        )
    core = {
        "schema": INPUT_PACKET_SCHEMA,
        "surface": surface,
        "suite_digest": suite["document_digest"],
        "authorization_digest": authorization["document_digest"],
        "case_id": case["case_id"],
        "read_set_id": case["read_set_id"],
        "question": case["question"],
        "source_snapshots": materialized,
        "oracle_visibility": "NONE",
        "world_model_result_visibility": "NONE",
        "production_activation": "NOT_EXECUTED",
    }
    return _document(INPUT_PACKET_SCHEMA, core)


def _failure_code(exc: BaseException) -> str:
    return exc.code.value if isinstance(exc, DomainError) else type(exc).__name__.upper()


def _terminal(
    *,
    case_id: str,
    status: str,
    answer_body: str | None,
    failure_code: str | None,
    external_task_count: int,
    provider_call_count: int | None,
    evidence: Mapping[str, object],
) -> tuple[dict[str, object], dict[str, object]]:
    core = {
        "schema": TERMINAL_EVIDENCE_SCHEMA,
        "case_id": case_id,
        "status": status,
        "answer_body": answer_body,
        "failure_code": failure_code,
        "external_task_count": external_task_count,
        "provider_call_count": provider_call_count,
        "evidence": dict(evidence),
        "production_activation": "NOT_EXECUTED",
    }
    document = _document(TERMINAL_EVIDENCE_SCHEMA, core)
    terminal = {
        "case_id": case_id,
        "status": status,
        "answer_body": answer_body,
        "failure_code": failure_code,
        "external_task_count": external_task_count,
        "provider_call_count": provider_call_count,
        "terminal_digest": document["document_digest"],
    }
    return terminal, document


def _population(
    *, suite: Mapping[str, object], surface: str, results: list[dict[str, object]]
) -> dict[str, object]:
    return _document(
        POPULATION_SCHEMA,
        {
            "schema": POPULATION_SCHEMA,
            "surface": surface,
            "suite_digest": suite["document_digest"],
            "results": results,
            "failures_preserved": True,
            "missing_outputs_interpolated": False,
            "production_activation": "NOT_EXECUTED",
        },
    )


def _prepare_output(path: Path) -> Path:
    if path.exists() or path.is_symlink():
        raise ComparisonFailure("output root must not already exist")
    path.mkdir(parents=True, mode=0o700)
    return path


def _direct_case(
    *,
    suite: Mapping[str, object],
    case: Mapping[str, object],
    packet: Mapping[str, object],
    case_root: Path,
    configuration: VolcengineArkModelConfiguration,
    qualification: object,
) -> tuple[dict[str, object], dict[str, object]]:
    recording: RecordingChatCompletionsTransport | None = None
    evidence: dict[str, object] = {
        "input_packet_digest": packet["document_digest"],
        "controller_retry_count": 0,
    }
    try:
        recording = RecordingChatCompletionsTransport(
            UrllibVolcengineArkChatTransport(
                api_key_resolver=lambda: configuration.resolve_api_key()
            )
        )
        adapter = VolcengineArkChatCompletionsNoToolsAdapter(
            transport=recording,
            configuration=configuration,
            output_schemas={_DIRECT_SCHEMA_REF: _DIRECT_OUTPUT},
            live_qualification=qualification,
        )
        manifest = AuthorizedInputManifest.create(
            capability_id="iter-006-controlled-direct-java-source-answer",
            strategy_ref="iter-006-controlled-direct-java-source-answer@1",
            execution_stage="ANSWER",
            calling_module=(
                "validation/structure_world_model_iteration_006/live_comparison"
            ),
            proposal_vocabulary_ref=None,
            items=(
                AuthorizedInputItem.create(
                    item_id="instruction",
                    schema_ref="text@1",
                    classification="INTERNAL",
                    purpose="answer only from the exact sealed Java source closure",
                    authority_reference=_DIRECT_PROMPT_REF,
                    disposition=InputDisposition.PROVIDED,
                    content=_DIRECT_INSTRUCTION,
                ),
                AuthorizedInputItem.create(
                    item_id="question-and-source-closure",
                    schema_ref=INPUT_PACKET_SCHEMA,
                    classification="INTERNAL",
                    purpose="exact question and Java source closure",
                    authority_reference=str(packet["document_digest"]),
                    disposition=InputDisposition.PROVIDED,
                    content=_canonical(packet).decode("utf-8"),
                ),
            ),
        )
        with SqliteDatabase(case_root / "model-gateway.sqlite3") as database:
            result = ModelGateway(
                SqliteModelGatewayRepository(database), (adapter,)
            ).invoke(
                ModelExecutionContext(
                    execution_envelope_ref=(
                        f"iter-006-controlled-direct:{suite['document_digest']}:"
                        f"{case['case_id']}"
                    ),
                    manifest=manifest,
                    prompt_program_ref=_DIRECT_PROMPT_REF,
                    rendering_contract_version="manifest-messages@1",
                    output_schema_ref=_DIRECT_SCHEMA_REF,
                    runtime_access_mode=RuntimeAccessMode.NO_EXTERNAL_ACCESS,
                    platform_proposal_mode=PlatformProposalMode.NONE,
                    requested_model_ref=configuration.model_ref,
                    provider_type=configuration.provider_type,
                    adapter_version=configuration.adapter_version,
                    provider_configuration_fingerprint=configuration.fingerprint,
                    max_output_tokens=_DIRECT_MAX_OUTPUT_TOKENS,
                    timeout_milliseconds=180_000,
                    classification="INTERNAL",
                    required_exact_fingerprint=True,
                )
            )
        provider_calls = len(recording.requests)
        evidence.update(
            {
                "manifest_digest": manifest.digest.value,
                "provider_request_digests": [
                    "sha256:" + hashlib.sha256(item.body).hexdigest()
                    for item in recording.requests
                ],
                "model_call_state": result.call.state.value,
                "model_failure_code": result.call.failure_code,
                "provider_request_id": result.call.provider_request_id,
                "actual_model_fingerprint": result.call.actual_model_fingerprint,
                "input_tokens": result.call.input_tokens,
                "output_tokens": result.call.output_tokens,
                "usage_complete": result.call.usage_complete,
                "eligibility": result.eligibility.reason,
                "replayed": result.replayed,
            }
        )
        if provider_calls != 1 or result.replayed or result.response is None:
            raise ComparisonFailure("controlled Direct did not produce one fresh response")
        if not result.eligibility.eligible_for_production_domain_output:
            raise ComparisonFailure(
                f"controlled Direct result is ineligible: {result.eligibility.reason}"
            )
        answer = _DIRECT_OUTPUT.validate_output_text(result.response.output_text).get(
            "answer"
        )
        if not isinstance(answer, str) or not answer:
            raise ComparisonFailure("controlled Direct answer is empty")
        return _terminal(
            case_id=str(case["case_id"]),
            status="SUCCESS",
            answer_body=answer,
            failure_code=None,
            external_task_count=1,
            provider_call_count=provider_calls,
            evidence=evidence,
        )
    except BaseException as exc:
        if isinstance(exc, (KeyboardInterrupt, SystemExit)):
            raise
        provider_calls = len(recording.requests) if recording is not None else 0
        evidence["failure_detail"] = str(exc)[:2000]
        return _terminal(
            case_id=str(case["case_id"]),
            status="FAILURE",
            answer_body=None,
            failure_code=_failure_code(exc),
            external_task_count=1,
            provider_call_count=provider_calls,
            evidence=evidence,
        )


def run_controlled_direct(arguments: argparse.Namespace) -> int:
    suite = _load_suite(Path(arguments.suite).resolve(strict=True))
    authorization = _require_authorization(
        Path(arguments.authorization).resolve(strict=True), suite
    )
    repository = Path(arguments.source_repository).resolve(strict=True)
    configuration = VolcengineArkModelConfiguration()
    qualification = load_ark_chat_conformance_qualification(
        Path(arguments.conformance_result).resolve(strict=True), configuration
    )
    if not configuration.credential_configured():
        raise ComparisonFailure("Ark credential is unavailable")
    prepared = [
        (
            case,
            _input_packet(
                suite,
                case,
                repository,
                authorization,
                surface="CONTROLLED_DIRECT",
            ),
        )
        for case in suite["cases"]
        if isinstance(case, dict)
    ]
    if len(prepared) != len(suite["cases"]):
        raise ComparisonFailure("held-out suite cases are invalid")
    output = _prepare_output(Path(arguments.output).resolve())
    results: list[dict[str, object]] = []
    for case, packet in prepared:
        case_root = output / "cases" / str(case["case_id"])
        case_root.mkdir(parents=True)
        _write_new(case_root / "input.json", packet)
        terminal, evidence = _direct_case(
            suite=suite,
            case=case,
            packet=packet,
            case_root=case_root,
            configuration=configuration,
            qualification=qualification,
        )
        _write_new(case_root / "terminal.json", evidence)
        results.append(terminal)
    population = _population(
        suite=suite, surface="CONTROLLED_DIRECT", results=results
    )
    _write_new(output / "population.json", population)
    print(json.dumps(population, ensure_ascii=False, sort_keys=True))
    return 0


def _materialize_workspace(packet: Mapping[str, object], workspace: Path) -> None:
    workspace.mkdir(parents=True, mode=0o700)
    snapshots = packet["source_snapshots"]
    assert isinstance(snapshots, list)
    for snapshot in snapshots:
        assert isinstance(snapshot, dict)
        label_root = workspace / str(snapshot["label"])
        files = snapshot["files"]
        assert isinstance(files, list)
        for item in files:
            assert isinstance(item, dict)
            target = label_root / Path(str(item["path"]))
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.parent.resolve().is_relative_to(workspace.resolve()):
                raise ComparisonFailure("mature Agent source path escaped workspace")
            _write_bytes_new(target, str(item["content"]).encode("utf-8"))


def _mature_command(
    *, workspace: Path, schema: Path, last_message: Path, prompt: str
) -> list[str]:
    contract = live_evaluator._MATURE_AGENT["command_contract"]
    assert isinstance(contract, dict)
    replacements = {
        "<ISOLATED_WORKSPACE>": str(workspace),
        "<CONTROL_SCHEMA>": str(schema),
        "<LAST_MESSAGE>": str(last_message),
    }
    flags = [replacements.get(item, item) for item in contract["exec_flags"]]
    return [
        str(live_evaluator._MATURE_AGENT["binary_path"]),
        *contract["global_flags"],
        str(contract["subcommand"]),
        *flags,
        prompt,
    ]


def _verify_mature_binary() -> Path:
    agent = live_evaluator._MATURE_AGENT
    binary = Path(str(agent["binary_path"])).resolve(strict=True)
    if _file_digest(binary) != agent["binary_sha256"]:
        raise ComparisonFailure("mature Agent binary digest drifted")
    completed = subprocess.run(
        (str(binary), "--version"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if completed.returncode != 0 or completed.stdout.strip() != agent["version"]:
        raise ComparisonFailure("mature Agent version drifted")
    return binary


def _mature_answer(value: object) -> str:
    if not isinstance(value, dict) or set(value) != {
        "answer",
        "claims",
        "limitations",
    }:
        raise ComparisonFailure("mature Source Agent terminal shape drifted")
    answer = value.get("answer")
    claims = value.get("claims")
    limitations = value.get("limitations")
    if (
        not isinstance(answer, str)
        or not answer
        or not isinstance(claims, list)
        or not claims
        or not isinstance(limitations, list)
        or any(not isinstance(item, str) or not item for item in limitations)
    ):
        raise ComparisonFailure("mature Source Agent terminal is invalid")
    for claim in claims:
        if not isinstance(claim, dict) or set(claim) != {
            "claim",
            "source_locators",
        }:
            raise ComparisonFailure("mature Source Agent claim shape drifted")
        locators = claim.get("source_locators")
        if (
            not isinstance(claim.get("claim"), str)
            or not claim.get("claim")
            or not isinstance(locators, list)
            or any(not isinstance(item, str) or not item for item in locators)
        ):
            raise ComparisonFailure("mature Source Agent claim is invalid")
    return answer


def _mature_case(
    *, case: Mapping[str, object], packet: Mapping[str, object], case_root: Path
) -> tuple[dict[str, object], dict[str, object]]:
    evidence: dict[str, object] = {
        "input_packet_digest": packet["document_digest"],
        "controller_retry_count": 0,
        "provider_call_count_observability": (
            "UNOBSERVABLE_FROM_CODEX_CLI_EVENT_BOUNDARY"
        ),
    }
    workspace = case_root / "workspace"
    _materialize_workspace(packet, workspace)
    control = workspace / ".control"
    control.mkdir()
    schema = control / "answer-schema.json"
    _write_new(schema, _MATURE_OUTPUT_SCHEMA)
    initialized = subprocess.run(
        ("git", "init", "-q"),
        cwd=workspace,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if initialized.returncode != 0:
        raise ComparisonFailure("isolated mature Agent workspace could not initialize")
    prompt = (
        "请只读取当前隔离工作区 A/（以及存在时的 B/）中的 Java 源码，回答下列问题。"
        "A/B 对应 input packet 中的 exact revision；请使用完整类型/方法签名并引用具体相对路径；"
        "只把源码中可见且唯一的直接调用作为静态调用，不要推断运行时分派、反射、依赖注入或设计动机。"
        "若源码闭包无法支持结论，必须明确说明限制。不要访问网络、父目录、其他仓库、Oracle、"
        "World Model 或 controlled Direct 结果。\n\n"
        f"问题：{case['question']}"
    )
    last_message = control / "last-message.json"
    command = _mature_command(
        workspace=workspace,
        schema=schema,
        last_message=last_message,
        prompt=prompt,
    )
    try:
        completed = subprocess.run(
            command,
            cwd=workspace,
            env=dict(os.environ),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        _write_bytes_new(
            case_root / "codex-events.jsonl", completed.stdout.encode("utf-8")
        )
        _write_bytes_new(
            case_root / "codex-stderr.log", completed.stderr.encode("utf-8")
        )
        evidence.update(
            {
                "command_argv_without_prompt": command[:-1],
                "prompt_digest": _digest("SWM-MATURE-JAVA-SOURCE-PROMPT@1", prompt),
                "exit_code": completed.returncode,
                "stdout_sha256": (
                    "sha256:" + hashlib.sha256(completed.stdout.encode()).hexdigest()
                ),
                "stderr_sha256": (
                    "sha256:" + hashlib.sha256(completed.stderr.encode()).hexdigest()
                ),
            }
        )
        if completed.returncode != 0 or not last_message.is_file():
            raise ComparisonFailure("mature Source Agent did not produce a terminal")
        raw = last_message.read_bytes()
        answer = _mature_answer(json.loads(raw, object_pairs_hook=_unique_object))
        evidence["last_message_sha256"] = "sha256:" + hashlib.sha256(raw).hexdigest()
        return _terminal(
            case_id=str(case["case_id"]),
            status="SUCCESS",
            answer_body=answer,
            failure_code=None,
            external_task_count=1,
            provider_call_count=None,
            evidence=evidence,
        )
    except BaseException as exc:
        if isinstance(exc, (KeyboardInterrupt, SystemExit)):
            raise
        evidence["failure_detail"] = str(exc)[:2000]
        return _terminal(
            case_id=str(case["case_id"]),
            status="FAILURE",
            answer_body=None,
            failure_code=_failure_code(exc),
            external_task_count=1,
            provider_call_count=None,
            evidence=evidence,
        )


def run_mature_source_agent(arguments: argparse.Namespace) -> int:
    suite = _load_suite(Path(arguments.suite).resolve(strict=True))
    authorization = _require_authorization(
        Path(arguments.authorization).resolve(strict=True), suite
    )
    repository = Path(arguments.source_repository).resolve(strict=True)
    _verify_mature_binary()
    prepared = [
        (
            case,
            _input_packet(
                suite,
                case,
                repository,
                authorization,
                surface="MATURE_SOURCE_AGENT",
            ),
        )
        for case in suite["cases"]
        if isinstance(case, dict)
    ]
    if len(prepared) != len(suite["cases"]):
        raise ComparisonFailure("held-out suite cases are invalid")
    output = _prepare_output(Path(arguments.output).resolve())
    results: list[dict[str, object]] = []
    for case, packet in prepared:
        case_root = output / "cases" / str(case["case_id"])
        case_root.mkdir(parents=True)
        _write_new(case_root / "input.json", packet)
        terminal, evidence = _mature_case(
            case=case, packet=packet, case_root=case_root
        )
        _write_new(case_root / "terminal.json", evidence)
        results.append(terminal)
    population = _population(
        suite=suite, surface="MATURE_SOURCE_AGENT", results=results
    )
    _write_new(output / "population.json", population)
    print(json.dumps(population, ensure_ascii=False, sort_keys=True))
    return 0


def _reference(path: Path, document: Mapping[str, object]) -> dict[str, object]:
    return {
        "path": str(path),
        "raw_sha256": _file_digest(path),
        "document_digest": document["document_digest"],
    }


def seal_baselines(arguments: argparse.Namespace) -> int:
    suite = _load_suite(Path(arguments.suite).resolve(strict=True))
    direct_path = Path(arguments.controlled_direct).resolve(strict=True)
    mature_path = Path(arguments.mature_source_agent).resolve(strict=True)
    direct = _load_document(direct_path, POPULATION_SCHEMA)
    mature = _load_document(mature_path, POPULATION_SCHEMA)
    cases = live_evaluator._case_map(suite)
    for surface, population in (
        ("CONTROLLED_DIRECT", direct),
        ("MATURE_SOURCE_AGENT", mature),
    ):
        live_evaluator._population_map(
            population,
            expected_surface=surface,
            suite_digest=str(suite["document_digest"]),
            case_ids=set(cases),
        )
    core = {
        "schema": BASELINE_SEAL_SCHEMA,
        "suite_digest": suite["document_digest"],
        "controlled_direct": _reference(direct_path, direct),
        "mature_source_agent": _reference(mature_path, mature),
        "controlled_direct_result_count": len(direct["results"]),
        "mature_source_agent_result_count": len(mature["results"]),
        "sealed_before_world_model_results": True,
        "world_model_result_count_at_seal": 0,
        "sealed_at": datetime.now().astimezone().isoformat(),
        "production_activation": "NOT_EXECUTED",
    }
    seal = _document(BASELINE_SEAL_SCHEMA, core)
    _write_new(Path(arguments.output).resolve(), seal)
    print(json.dumps(seal, ensure_ascii=False, sort_keys=True))
    return 0


def _baseline_seal(path: Path, suite: Mapping[str, object]) -> dict[str, object]:
    seal = _load_document(path, BASELINE_SEAL_SCHEMA)
    expected = {
        "schema",
        "suite_digest",
        "controlled_direct",
        "mature_source_agent",
        "controlled_direct_result_count",
        "mature_source_agent_result_count",
        "sealed_before_world_model_results",
        "world_model_result_count_at_seal",
        "sealed_at",
        "production_activation",
        "document_digest",
    }
    if (
        set(seal) != expected
        or seal.get("suite_digest") != suite.get("document_digest")
        or seal.get("controlled_direct_result_count") != len(suite["cases"])
        or seal.get("mature_source_agent_result_count") != len(suite["cases"])
        or seal.get("sealed_before_world_model_results") is not True
        or seal.get("world_model_result_count_at_seal") != 0
        or seal.get("production_activation") != "NOT_EXECUTED"
    ):
        raise ComparisonFailure("baseline seal is invalid")
    for key, surface in (
        ("controlled_direct", "CONTROLLED_DIRECT"),
        ("mature_source_agent", "MATURE_SOURCE_AGENT"),
    ):
        reference = seal.get(key)
        if not isinstance(reference, dict) or set(reference) != {
            "path",
            "raw_sha256",
            "document_digest",
        }:
            raise ComparisonFailure("baseline population reference is invalid")
        population_path = Path(str(reference["path"])).resolve(strict=True)
        if _file_digest(population_path) != reference["raw_sha256"]:
            raise ComparisonFailure("baseline population bytes drifted")
        population = _load_document(population_path, POPULATION_SCHEMA)
        if population.get("document_digest") != reference["document_digest"]:
            raise ComparisonFailure("baseline population document drifted")
        live_evaluator._population_map(
            population,
            expected_surface=surface,
            suite_digest=str(suite["document_digest"]),
            case_ids=set(live_evaluator._case_map(suite)),
        )
    return seal


def _loopback_base_url(value: str) -> str:
    parsed = urlsplit(value)
    if (
        parsed.scheme != "http"
        or parsed.hostname != "127.0.0.1"
        or parsed.port is None
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
    ):
        raise ComparisonFailure("World Model URL must be exact IPv4 loopback HTTP")
    return f"http://127.0.0.1:{parsed.port}"


def _world_preflight(base_url: str, suite: Mapping[str, object]) -> Mapping[str, object]:
    opener = urllib_request.build_opener(urllib_request.ProxyHandler({}))
    try:
        with opener.open(
            urllib_request.Request(base_url + "/health", method="GET"), timeout=30
        ) as response:
            raw = response.read(1024 * 1024 + 1)
    except (OSError, urllib_error.URLError) as exc:
        raise ComparisonFailure("World Model health request failed") from exc
    if len(raw) > 1024 * 1024:
        raise ComparisonFailure("World Model health exceeds the evidence bound")
    value = json.loads(raw, object_pairs_hook=_unique_object)
    digests = {
        "evaluation_grant_digest",
        "deterministic_qualification_digest",
        "held_out_suite_digest",
        "independent_evaluator_digest",
        "startup_preflight_digest",
        "startup_receipt_digest",
        "stage_manifest_digest",
        "launcher_manifest_digest",
        "provider_subject_digest",
        "gateway_authorization_receipt_digest",
    }
    if (
        not isinstance(value, dict)
        or value.get("status") != "ready"
        or value.get("mode") != "WORLD_MODEL"
        or value.get("environment") != "EVALUATION_ONLY"
        or value.get("evaluation_subject_status") != "CANDIDATE"
        or value.get("evaluation_subject_commit")
        != suite.get("evaluation_subject_commit")
        or value.get("evaluation_subject_tree") != suite.get("evaluation_subject_tree")
        or value.get("held_out_suite_digest") != suite.get("document_digest")
        or value.get("dispatch_policy")
        != "ONE_CALL_PER_QUESTION_NO_HIDDEN_RETRY"
        or value.get("production_activation") != "NOT_EXECUTED"
        or any(
            not isinstance(value.get(field), str)
            or not live_evaluator._DIGEST.fullmatch(str(value.get(field)))
            for field in digests
        )
    ):
        raise ComparisonFailure("World Model health is not the exact suite subject")
    return value


def _world_case(
    *, base_url: str, suite: Mapping[str, object], case: Mapping[str, object]
) -> tuple[dict[str, object], dict[str, object]]:
    request_id = f"iter006-{str(case['case_id']).lower()}"
    request_body = canonical_json_bytes(
        {
            "request_id": request_id,
            "read_set_id": case["read_set_id"],
            "question": case["question"],
        }
    )
    evidence: dict[str, object] = {
        "request_id": request_id,
        "request_body_sha256": "sha256:" + hashlib.sha256(request_body).hexdigest(),
        "controller_retry_count": 0,
    }
    provider_calls: int | None = None
    try:
        opener = urllib_request.build_opener(urllib_request.ProxyHandler({}))
        request = urllib_request.Request(
            base_url + "/v1/world-model/questions",
            data=request_body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with opener.open(request, timeout=900) as response:
            raw = response.read(32 * 1024 * 1024 + 1)
        if len(raw) > 32 * 1024 * 1024:
            raise ComparisonFailure("World Model response exceeds evidence bound")
        value = json.loads(raw, object_pairs_hook=_unique_object)
        if not isinstance(value, dict):
            raise ComparisonFailure("World Model response is not an object")
        execution = value.get("execution")
        page = value.get("page")
        if isinstance(execution, dict):
            observed = execution.get("provider_call_count")
            if isinstance(observed, int) and not isinstance(observed, bool):
                provider_calls = observed
        if (
            value.get("request_id") != request_id
            or value.get("read_set_id") != case["read_set_id"]
            or value.get("question") != case["question"]
            or value.get("mode") != "WORLD_MODEL"
            or value.get("environment") != "EVALUATION_ONLY"
            or value.get("evaluation_subject_status") != "CANDIDATE"
            or value.get("evaluation_subject_commit")
            != suite.get("evaluation_subject_commit")
            or value.get("evaluation_subject_tree") != suite.get("evaluation_subject_tree")
            or value.get("production_activation") != "NOT_EXECUTED"
            or not isinstance(page, dict)
            or not isinstance(execution, dict)
            or provider_calls != 1
        ):
            raise ComparisonFailure("World Model verified terminal boundary drifted")
        answer = page.get("answer")
        if not isinstance(answer, dict) or not isinstance(answer.get("body"), str):
            raise ComparisonFailure("World Model answer body is absent")
        evidence.update(
            {
                "response_sha256": "sha256:" + hashlib.sha256(raw).hexdigest(),
                "result_digest": value.get("result_digest"),
                "evaluation_subject_commit": value.get("evaluation_subject_commit"),
                "evaluation_subject_tree": value.get("evaluation_subject_tree"),
            }
        )
        return _terminal(
            case_id=str(case["case_id"]),
            status="SUCCESS",
            answer_body=str(answer["body"]),
            failure_code=None,
            external_task_count=1,
            provider_call_count=provider_calls,
            evidence=evidence,
        )
    except BaseException as exc:
        if isinstance(exc, (KeyboardInterrupt, SystemExit)):
            raise
        if isinstance(exc, urllib_error.HTTPError):
            raw_error = exc.read(1024 * 1024)
            evidence["http_error_body_sha256"] = (
                "sha256:" + hashlib.sha256(raw_error).hexdigest()
            )
        evidence["failure_detail"] = str(exc)[:2000]
        return _terminal(
            case_id=str(case["case_id"]),
            status="FAILURE",
            answer_body=None,
            failure_code=_failure_code(exc),
            external_task_count=1,
            provider_call_count=provider_calls,
            evidence=evidence,
        )


def run_world_model(arguments: argparse.Namespace) -> int:
    suite = _load_suite(Path(arguments.suite).resolve(strict=True))
    _require_authorization(Path(arguments.authorization).resolve(strict=True), suite)
    _baseline_seal(Path(arguments.baseline_seal).resolve(strict=True), suite)
    base_url = _loopback_base_url(arguments.base_url)
    _world_preflight(base_url, suite)
    output = _prepare_output(Path(arguments.output).resolve())
    results: list[dict[str, object]] = []
    for case in suite["cases"]:
        assert isinstance(case, dict)
        case_root = output / "cases" / str(case["case_id"])
        case_root.mkdir(parents=True)
        terminal, evidence = _world_case(
            base_url=base_url, suite=suite, case=case
        )
        _write_new(case_root / "terminal.json", evidence)
        results.append(terminal)
    population = _population(suite=suite, surface="WORLD_MODEL", results=results)
    _write_new(output / "population.json", population)
    print(json.dumps(population, ensure_ascii=False, sort_keys=True))
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    direct = commands.add_parser("run-controlled-direct")
    direct.add_argument("--suite", required=True)
    direct.add_argument("--source-repository", required=True)
    direct.add_argument("--authorization", required=True)
    direct.add_argument("--conformance-result", required=True)
    direct.add_argument("--output", required=True)
    mature = commands.add_parser("run-mature-source-agent")
    mature.add_argument("--suite", required=True)
    mature.add_argument("--source-repository", required=True)
    mature.add_argument("--authorization", required=True)
    mature.add_argument("--output", required=True)
    seal = commands.add_parser("seal-baselines")
    seal.add_argument("--suite", required=True)
    seal.add_argument("--controlled-direct", required=True)
    seal.add_argument("--mature-source-agent", required=True)
    seal.add_argument("--output", required=True)
    world = commands.add_parser("run-world-model")
    world.add_argument("--suite", required=True)
    world.add_argument("--authorization", required=True)
    world.add_argument("--baseline-seal", required=True)
    world.add_argument("--base-url", required=True)
    world.add_argument("--output", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    if arguments.command == "run-controlled-direct":
        return run_controlled_direct(arguments)
    if arguments.command == "run-mature-source-agent":
        return run_mature_source_agent(arguments)
    if arguments.command == "seal-baselines":
        return seal_baselines(arguments)
    return run_world_model(arguments)


def _entrypoint(argv: Sequence[str] | None = None) -> int:
    try:
        return main(argv)
    except (ComparisonFailure, DomainError, OSError, ValueError) as exc:
        print(
            json.dumps(
                {
                    "error": _failure_code(exc),
                    "message": str(exc),
                    "production_activation": "NOT_EXECUTED",
                },
                ensure_ascii=False,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(_entrypoint())
