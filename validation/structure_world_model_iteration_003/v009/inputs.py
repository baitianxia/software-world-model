"""Mechanical validation for the exact V-009 input freeze."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Mapping
from urllib.parse import urlsplit

from software_world_model.ai_infrastructure import (
    ARK_CHAT_CONFORMANCE_FIXTURE_ID,
    ARK_CHAT_CONFORMANCE_FIXTURE_VERSION,
    VolcengineArkModelConfiguration,
    current_ark_implementation_manifest,
    world_model_answer_output_contract_digest,
    world_model_answer_prompt_program_digest,
    world_model_answer_strategy_implementation_digest,
)
from software_world_model.cross_cutting import DomainError, ErrorCode

from .manifest import PINNED_SUITE_FILE_DIGEST, PINNED_SUITE_REF, REPOSITORY_ROOT


DEFAULT_INPUT_FREEZE_PATH = Path(__file__).with_name("input-freeze-1.0.2.json")
PINNED_INPUT_FREEZE_FILE_DIGEST = (
    "sha256:f2355e8f681ef5bcf4ada645f741b1acae47d63d56b45f5bcc30342058ec5e3c"
)
EXPECTED_G3A_COMMIT = "f2269ecca5c1e85e69fafd93fe599c841227f3c7"
EXPECTED_G3A_TREE = "936dc1fcab74f45c0342ad0e7055b9d4b314e2e1"
EXPECTED_G3A_RESULT_COMMIT = "8caac3efaf97e169dac91a94a7c8ea2f8baa1b30"


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def _file_digest(path: Path) -> str:
    try:
        payload = path.read_bytes()
    except OSError as exc:
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "V-009 frozen file is unavailable",
        ) from exc
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _repo_path(relative: object) -> Path:
    if not isinstance(relative, str) or not relative:
        _invalid("V-009 frozen repository path is invalid")
    candidate = (REPOSITORY_ROOT / relative).resolve()
    try:
        candidate.relative_to(REPOSITORY_ROOT.resolve())
    except ValueError as exc:
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "V-009 frozen path escapes the repository",
        ) from exc
    return candidate


def load_input_freeze(
    path: str | Path = DEFAULT_INPUT_FREEZE_PATH,
) -> dict[str, object]:
    source = Path(path).resolve()
    try:
        encoded = source.read_bytes()
        value = json.loads(encoded, object_pairs_hook=_unique_object)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "V-009 exact input freeze cannot be loaded",
        ) from exc
    actual_digest = "sha256:" + hashlib.sha256(encoded).hexdigest()
    if actual_digest != PINNED_INPUT_FREEZE_FILE_DIGEST:
        _invalid("V-009 exact input freeze file digest drifted")
    if not isinstance(value, dict):
        _invalid("V-009 exact input freeze must contain one object")
    verify_input_freeze(value)
    return {**value, "_file_digest": actual_digest}


def verify_input_freeze(value: Mapping[str, object]) -> None:
    required_fields = {
        "schema",
        "freeze_ref",
        "checkpoint_binding",
        "predecessor",
        "disclosure",
        "g3a",
        "provider",
        "egress_policy",
        "conformance",
        "strategy",
        "capability_evaluation",
        "baselines",
    }
    if frozenset(value) not in {
        frozenset(required_fields),
        frozenset(required_fields | {"_file_digest"}),
    }:
        _invalid("V-009 exact input freeze fields are invalid")
    if (
        value.get("schema") != "swm.iter-003.v009-input-freeze@1"
        or value.get("freeze_ref") != "ITER-003-V009-EXACT-INPUTS@1.0.2"
        or value.get("checkpoint_binding") != "ENCLOSING_CLEAN_GIT_COMMIT_AND_TREE"
    ):
        _invalid("V-009 exact input freeze identity is invalid")
    predecessor = _mapping(value.get("predecessor"), "predecessor")
    if predecessor != {
        "freeze_ref": "ITER-003-V009-EXACT-INPUTS@1.0.1",
        "freeze_file_digest": "sha256:b4a90907704ffdd888d63718c7118182c8565d0df66d63f35b425d26e2ee1293",
        "checkpoint": "4f884a28c954de8b7edf555092fe08b81bce47ef",
        "conformance_binding_digest": "sha256:17b3ffa926041032e44714ef17c2126f9cb142fe80c954b8d7ee993d86b20868",
        "capability_result_id": "evaluation_result_9f02ae0784aa4ab8879fe836b7ccff64",
        "capability_result_digest": "sha256:58933ff893e1dd808009ef7de28968831285c19a1e9fcb9f9ad90caef1f8aa3e",
        "outcome": "FAIL",
        "failed_case_ids": ["WM-CE-GAP-004"],
        "disposition": "PROMPT_STATUS_CONTRACT_CLARIFICATION_REQUIRES_FULL_NEW_RUN",
    }:
        _invalid("V-009 predecessor failure binding is invalid")
    disclosure = _mapping(value.get("disclosure"), "disclosure")
    scope = disclosure.get("scope")
    if (
        disclosure.get("confirmed") is not True
        or disclosure.get("confirmation_ref")
        != "codex-user-confirmation:2026-08-10T21:01:55+08:00"
        or disclosure.get("message_digest")
        != "sha256:36f33adaf0942634a8ece1eec4a6f30d44dec73e1ef8704b29d983a57f2e09ae"
        or not isinstance(scope, list)
        or len(scope) != 4
        or disclosure.get("g3b_product_dispatch_included") is not False
    ):
        _invalid("V-009 disclosure confirmation is absent or out of scope")
    g3a = _mapping(value.get("g3a"), "G3a binding")
    if (
        g3a.get("commit") != EXPECTED_G3A_COMMIT
        or g3a.get("tree") != EXPECTED_G3A_TREE
        or g3a.get("result_commit") != EXPECTED_G3A_RESULT_COMMIT
        or g3a.get("result_status") != "PASS"
    ):
        _invalid("V-009 G3a checkpoint binding is invalid")
    provider = _mapping(value.get("provider"), "provider")
    endpoint = _mapping(provider.get("endpoint"), "provider endpoint")
    if (
        provider.get("provider_type") != "VOLCENGINE_ARK"
        or provider.get("protocol") != "OPENAI_COMPATIBLE_CHAT_COMPLETIONS"
        or provider.get("adapter_version") != "openai-chat-completions-no-tools@8"
        or provider.get("requested_model_ref") != "glm-5-2-260617"
        or provider.get("actual_model_fingerprint") != "glm-5.2"
        or provider.get("configuration_fingerprint")
        != "sha256:420f553a3ce0075818550e08cb1351ce69eaf9871c5a0257aecf88b7b32b88fd"
        or provider.get("credential_reference") != "env:ARK_API_KEY"
        or endpoint
        != {
            "scheme": "https",
            "host": "ark.cn-beijing.volces.com",
            "port": 443,
            "path": "/api/coding/v3/chat/completions",
        }
    ):
        _invalid("V-009 provider, adapter, model, credential, or endpoint drifted")
    conformance = _mapping(value.get("conformance"), "conformance")
    if (
        conformance.get("fixture_id") != ARK_CHAT_CONFORMANCE_FIXTURE_ID
        or conformance.get("fixture_version") != ARK_CHAT_CONFORMANCE_FIXTURE_VERSION
        or conformance.get("operator") != "iter-003-v009-operator"
        or conformance.get("timeout_milliseconds") != 30_000
        or conformance.get("max_output_tokens") != 96
        or conformance.get("required_request_count") != 2
        or conformance.get("execution_protocol")
        != "V009_PRECALL_SEALED_INVOCATION_AND_EXACT_RESULT_BINDING@1"
        or conformance.get("result_binding")
        != "EXACT_PASS_RESULT_FROM_THESE_INPUTS"
    ):
        _invalid("V-009 Conformance inputs drifted")
    strategy = _mapping(value.get("strategy"), "strategy")
    configuration = _mapping(strategy.get("configuration"), "strategy configuration")
    if (
        strategy.get("capability_id") != "world-model-authority-proposal"
        or strategy.get("capability_contract_version") != "1.0.0"
        or strategy.get("strategy_id") != "model-snapshot-first-world-model-answer"
        or strategy.get("strategy_version") != "1.0.2"
        or strategy.get("tool_policy_ref") != "model-no-tools-no-source-no-evidence@1"
        or configuration
        != {
            "classification": "INTERNAL",
            "max_output_tokens": 1000,
            "timeout_milliseconds": 180000,
            "model_calls_per_case": 1,
            "hidden_retry_count": 0,
            "qualification_ref_binding": "EXACT_CONFORMANCE_RESULT",
        }
    ):
        _invalid("V-009 strategy identity or resource policy drifted")
    evaluation = _mapping(value.get("capability_evaluation"), "capability evaluation")
    if (
        evaluation.get("suite_ref") != PINNED_SUITE_REF
        or evaluation.get("suite_file_digest") != PINNED_SUITE_FILE_DIGEST
        or evaluation.get("required_case_count") != 7
        or evaluation.get("failure_count_required") != 0
        or evaluation.get("unknown_count_required") != 0
        or evaluation.get("valid_for_seconds") != 604_800
        or evaluation.get("result_requirement") != "CLOSED_PASS_AND_VALID"
    ):
        _invalid("V-009 capability evaluation inputs drifted")
    baselines = _mapping(value.get("baselines"), "baselines")
    direct = _mapping(baselines.get("controlled_direct"), "controlled Direct baseline")
    mature = _mapping(
        baselines.get("mature_source_agent"), "mature Source Agent baseline"
    )
    if set(baselines) != {"controlled_direct", "mature_source_agent"}:
        _invalid("V-009 baseline set drifted")
    if direct != {
        "protocol_path": "validation/structure_world_model_iteration_003/questions/direct-baseline-protocol-1.0.0.json",
        "protocol_ref": "ITER-003-DIRECT-SOURCE-BASELINE@1.0.0",
        "protocol_digest": "sha256:af074014318fab1b5e0fdc3dafab70c1fcd45fe1060da4141e8d8fc594094869",
        "implementation_path": "validation/product_holdout_iteration_002/direct_answer.py",
        "implementation_file_digest": "sha256:e04c6cca4eb484cd75512c9d748b3bd142027501c5ebe9c905fb5e1e96b06bbd",
        "provider_adapter_model_binding": "SAME_AS_PROVIDER_BLOCK",
        "result_timing": "AFTER_CE_PASS_BEFORE_FIRST_G3B_PRODUCT_RUN",
    }:
        _invalid("V-009 controlled Direct baseline inputs drifted")
    if mature != {
        "protocol_path": "validation/structure_world_model_iteration_003/questions/mature-agent-baseline-protocol-1.0.1.json",
        "protocol_ref": "ITER-003-MATURE-SOURCE-AGENT-BASELINE@1.0.1",
        "protocol_digest": "sha256:4ac3e880dfc6f359718584e4edc54cc93d8e4b80f89c80804d02776ce8030d53",
        "answer_schema_path": "validation/structure_world_model_iteration_003/questions/mature-agent-answer-schema-1.0.0.json",
        "answer_schema_digest": "sha256:cfe6ea01dedfbbd795676d00a90f7bf74d8227694ccb35a6f9a356a720e8e17d",
        "prepared_binary_path": "/Applications/ChatGPT.app/Contents/Resources/codex",
        "prepared_tool_version": "codex-cli 0.147.0-alpha.1.2",
        "prepared_binary_digest": "sha256:9f6748b4ab10ffc92c28b9ccedae89e61a302bbc011df7d276ee38f55906e481",
        "exact_runtime_model_config_binding": "RECHECK_AND_SEAL_BEFORE_RUN",
        "result_timing": "AFTER_CE_PASS_BEFORE_FIRST_G3B_PRODUCT_RUN",
    }:
        _invalid("V-009 mature Source Agent baseline inputs drifted")


def verify_input_freeze_runtime(
    value: Mapping[str, object],
    *,
    configuration: VolcengineArkModelConfiguration,
    repository_state: Mapping[str, object],
    environment: Mapping[str, str],
) -> None:
    verify_input_freeze(value)
    if (
        repository_state.get("clean") is not True
        or not isinstance(repository_state.get("head"), str)
        or len(str(repository_state["head"])) != 40
        or not isinstance(repository_state.get("tree"), str)
        or len(str(repository_state["tree"])) != 40
        or repository_state.get("g3a_result_is_ancestor") is not True
    ):
        _invalid("V-009 requires a clean checkpoint descended from the G3a Result")
    provider = _mapping(value["provider"], "provider")
    endpoint = urlsplit(configuration.endpoint)
    expected_endpoint = _mapping(provider["endpoint"], "provider endpoint")
    if (
        configuration.provider_type != provider["provider_type"]
        or configuration.adapter_version != provider["adapter_version"]
        or configuration.model_ref != provider["requested_model_ref"]
        or configuration.actual_model_fingerprint
        != provider["actual_model_fingerprint"]
        or configuration.fingerprint.value != provider["configuration_fingerprint"]
        or configuration.secret_reference != provider["credential_reference"]
        or endpoint.scheme != expected_endpoint["scheme"]
        or endpoint.hostname != expected_endpoint["host"]
        or (endpoint.port or 443) != expected_endpoint["port"]
        or endpoint.path != expected_endpoint["path"]
        or endpoint.username is not None
        or endpoint.password is not None
        or endpoint.query
        or endpoint.fragment
        or not configuration.credential_configured(environment)
    ):
        _invalid("V-009 live Provider runtime does not match the exact freeze")
    conformance = _mapping(value["conformance"], "conformance")
    if (
        current_ark_implementation_manifest().get("aggregate_digest")
        != conformance["implementation_manifest_digest"]
    ):
        _invalid("V-009 Adapter Conformance implementation drifted")
    strategy = _mapping(value["strategy"], "strategy")
    strategy_path = (
        REPOSITORY_ROOT
        / "src/software_world_model/ai_infrastructure/world_model_answer_strategy.py"
    )
    if (
        world_model_answer_strategy_implementation_digest().value
        != strategy["implementation_digest"]
        or world_model_answer_prompt_program_digest().value
        != strategy["prompt_program_digest"]
        or world_model_answer_output_contract_digest().value
        != strategy["output_contract_digest"]
        or _file_digest(strategy_path) != strategy["implementation_file_digest"]
    ):
        _invalid("V-009 exact strategy implementation, prompt, or output contract drifted")
    egress = _mapping(value["egress_policy"], "egress policy")
    egress_path = _repo_path(egress["path"])
    evaluation = _mapping(value["capability_evaluation"], "capability evaluation")
    suite_path = _repo_path(evaluation["suite_path"])
    evaluator_path = _repo_path(evaluation["evaluator_path"])
    if (
        _file_digest(egress_path) != egress["file_digest"]
        or _file_digest(suite_path) != evaluation["suite_file_digest"]
        or _file_digest(evaluator_path) != evaluation["evaluator_file_digest"]
    ):
        _invalid("V-009 egress policy, suite, or evaluator file drifted")
    try:
        policy = json.loads(egress_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "V-009 egress policy cannot be loaded",
        ) from exc
    if (
        not isinstance(policy, dict)
        or policy.get("policy_ref") != egress["policy_ref"]
        or policy.get("default_action") != "DENY"
        or policy.get("provider", {}).get("credential_reference")
        != configuration.secret_reference
    ):
        _invalid("V-009 egress policy semantics are invalid")
    baselines = _mapping(value["baselines"], "baselines")
    direct = _mapping(baselines["controlled_direct"], "controlled Direct baseline")
    mature = _mapping(
        baselines["mature_source_agent"], "mature Source Agent baseline"
    )
    direct_protocol_path = _repo_path(direct["protocol_path"])
    direct_implementation_path = _repo_path(direct["implementation_path"])
    mature_protocol_path = _repo_path(mature["protocol_path"])
    mature_schema_path = _repo_path(mature["answer_schema_path"])
    mature_binary_path = Path(str(mature["prepared_binary_path"]))
    if (
        _file_digest(direct_protocol_path) != direct["protocol_digest"]
        or _file_digest(direct_implementation_path)
        != direct["implementation_file_digest"]
        or _file_digest(mature_protocol_path) != mature["protocol_digest"]
        or _file_digest(mature_schema_path) != mature["answer_schema_digest"]
        or _file_digest(mature_binary_path) != mature["prepared_binary_digest"]
    ):
        _invalid("V-009 baseline protocol, implementation, schema, or binary drifted")
    try:
        direct_protocol = json.loads(
            direct_protocol_path.read_text(encoding="utf-8"),
            object_pairs_hook=_unique_object,
        )
        mature_protocol = json.loads(
            mature_protocol_path.read_text(encoding="utf-8"),
            object_pairs_hook=_unique_object,
        )
        mature_schema = json.loads(
            mature_schema_path.read_text(encoding="utf-8"),
            object_pairs_hook=_unique_object,
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "V-009 baseline assets cannot be loaded",
        ) from exc
    if (
        not isinstance(direct_protocol, dict)
        or direct_protocol.get("protocol_ref") != direct["protocol_ref"]
        or direct_protocol.get("implementation", {}).get("path")
        != direct["implementation_path"]
        or direct_protocol.get("implementation", {}).get("file_digest")
        != direct["implementation_file_digest"]
        or not isinstance(mature_protocol, dict)
        or mature_protocol.get("protocol_ref") != mature["protocol_ref"]
        or mature_protocol.get("agent", {}).get("prepared_version")
        != mature["prepared_tool_version"]
        or mature_protocol.get("agent", {}).get("prepared_binary_sha256")
        != str(mature["prepared_binary_digest"]).removeprefix("sha256:")
        or mature_protocol.get("answer_schema", {}).get("schema_digest")
        != mature["answer_schema_digest"]
        or not isinstance(mature_schema, dict)
        or mature_schema.get("$id")
        != mature_protocol.get("answer_schema", {}).get("schema_ref")
    ):
        _invalid("V-009 baseline asset semantics are invalid")


def _mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        _invalid(f"V-009 frozen {label} must be an object")
    return value


def _invalid(message: str) -> None:
    raise DomainError(ErrorCode.QUALIFICATION_INVALID, message)


__all__ = [
    "DEFAULT_INPUT_FREEZE_PATH",
    "EXPECTED_G3A_COMMIT",
    "EXPECTED_G3A_RESULT_COMMIT",
    "EXPECTED_G3A_TREE",
    "PINNED_INPUT_FREEZE_FILE_DIGEST",
    "load_input_freeze",
    "verify_input_freeze",
    "verify_input_freeze_runtime",
]
