"""CLI for the isolated JWT capability-evaluation lifecycle."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Sequence, TextIO

from software_world_model.ai_infrastructure import (
    ProviderOutcomeUnknown,
    UrllibVolcengineArkChatTransport,
    VolcengineArkModelConfiguration,
    load_ark_chat_conformance_qualification,
)
from software_world_model.cross_cutting import DomainError

from .comparison import seal_reviewed_capability_comparison
from .direct_agent import run_direct_agent
from .evaluation_bridge import activate_evaluated_strategy, register_capability_evaluation
from .manifest import freeze_jwt_run_configuration, seal_direct_oracle
from .world_model import run_world_model


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="swm-jwt-evaluation",
        description="Run the isolated JWT Oracle, World Model, comparison, CE, and activation lifecycle",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    direct = commands.add_parser("run-direct")
    direct.add_argument("--cc-result", required=True)
    direct.add_argument("--repository", required=True)
    direct.add_argument("--result-directory", required=True)
    direct.add_argument("--max-tool-steps", type=int, default=40)
    direct.add_argument("--max-files-read", type=int, default=16)
    direct.add_argument("--max-source-bytes", type=int, default=1_000_000)
    direct.add_argument("--max-model-calls", type=int, default=40)
    direct.add_argument("--timeout-milliseconds", type=int, default=60_000)
    direct.add_argument("--max-output-tokens", type=int, default=4096)
    world = commands.add_parser("run-world")
    world.add_argument("--run-configuration", required=True)
    world.add_argument("--cc-result", required=True)
    world.add_argument("--repository", required=True)
    world.add_argument("--runtime-directory", required=True)
    world.add_argument("--result-directory", required=True)
    comparison = commands.add_parser("compare")
    comparison.add_argument("--oracle", required=True)
    comparison.add_argument("--run-configuration", required=True)
    comparison.add_argument("--world-result", required=True)
    comparison.add_argument("--review-attestation", required=True)
    comparison.add_argument("--cc-result", required=True)
    comparison.add_argument("--result-directory", required=True)
    evaluation = commands.add_parser("record-ce")
    evaluation.add_argument("--oracle", required=True)
    evaluation.add_argument("--run-configuration", required=True)
    evaluation.add_argument("--world-result", required=True)
    evaluation.add_argument("--comparison", required=True)
    evaluation.add_argument("--cc-result", required=True)
    evaluation.add_argument("--database", required=True)
    evaluation.add_argument("--result-directory", required=True)
    evaluation.add_argument("--actor", required=True)
    activation = commands.add_parser("activate")
    activation.add_argument("--cc-result", required=True)
    activation.add_argument("--registration", required=True)
    activation.add_argument("--run-configuration", required=True)
    activation.add_argument("--database", required=True)
    activation.add_argument("--result-directory", required=True)
    activation.add_argument("--environment", required=True)
    activation.add_argument("--actor", required=True)
    activation.add_argument("--reason", required=True)
    activation.add_argument("--idempotency-key", required=True)
    oracle = commands.add_parser("seal-oracle")
    oracle.add_argument("--draft", required=True)
    oracle.add_argument("--cc-result", required=True)
    oracle.add_argument("--result-directory", required=True)
    oracle.add_argument("--operator", required=True)
    oracle.add_argument("--reviewer", required=True)
    run = commands.add_parser("freeze-run")
    run.add_argument("--oracle", required=True)
    run.add_argument("--cc-result", required=True)
    run.add_argument("--repository", required=True)
    run.add_argument("--result-directory", required=True)
    run.add_argument("--runtime-directory", required=True)
    run.add_argument("--operator", required=True)
    return parser


def main(argv: Sequence[str] | None = None, *, stdout: TextIO | None = None) -> int:
    output = stdout or sys.stdout
    arguments = build_parser().parse_args(argv)
    configuration = VolcengineArkModelConfiguration()
    try:
        qualification = load_ark_chat_conformance_qualification(
            arguments.cc_result, configuration
        )
        if arguments.command == "activate":
            path = activate_evaluated_strategy(
                registration_path=arguments.registration,
                run_configuration_path=arguments.run_configuration,
                database_path=arguments.database,
                result_directory=arguments.result_directory,
                activation_scope={"environment": arguments.environment},
                actor=arguments.actor,
                reason=arguments.reason,
                idempotency_key=arguments.idempotency_key,
            )
            payload = {
                "status": "JWT_MODEL_STRATEGY_ACTIVATED",
                "result_path": str(path),
                "environment": arguments.environment,
            }
        elif arguments.command == "run-direct":
            transport = UrllibVolcengineArkChatTransport(
                api_key_resolver=configuration.resolve_api_key
            )
            path = run_direct_agent(
                repository_path=arguments.repository,
                result_directory=arguments.result_directory,
                qualification=qualification,
                configuration=configuration,
                transport=transport,
                max_tool_steps=arguments.max_tool_steps,
                max_files_read=arguments.max_files_read,
                max_source_bytes=arguments.max_source_bytes,
                max_model_calls=arguments.max_model_calls,
                timeout_milliseconds=arguments.timeout_milliseconds,
                max_output_tokens=arguments.max_output_tokens,
            )
            payload = {
                "status": "DIRECT_ORACLE_DRAFT_CREATED",
                "result_path": str(path),
                "conformance_result_ref": qualification.result_ref,
                "independent_review": "REQUIRED",
                "available_to_swm_runtime": False,
            }
        elif arguments.command == "record-ce":
            path = register_capability_evaluation(
                oracle_path=arguments.oracle,
                run_configuration_path=arguments.run_configuration,
                world_model_result_path=arguments.world_result,
                comparison_path=arguments.comparison,
                database_path=arguments.database,
                result_directory=arguments.result_directory,
                qualification=qualification,
                configuration=configuration,
                actor=arguments.actor,
            )
            payload = {
                "status": "JWT_CAPABILITY_EVALUATION_RECORDED",
                "result_path": str(path),
                "production_activation": "NOT_RUN",
            }
        elif arguments.command == "compare":
            path = seal_reviewed_capability_comparison(
                oracle_path=arguments.oracle,
                run_configuration_path=arguments.run_configuration,
                world_model_result_path=arguments.world_result,
                review_attestation_path=arguments.review_attestation,
                result_directory=arguments.result_directory,
                qualification=qualification,
                configuration=configuration,
            )
            payload = {
                "status": "JWT_CAPABILITY_COMPARISON_CREATED",
                "result_path": str(path),
                "conformance_result_ref": qualification.result_ref,
                "capability_evaluation_registration": "NOT_RUN",
            }
        elif arguments.command == "run-world":
            transport = UrllibVolcengineArkChatTransport(
                api_key_resolver=configuration.resolve_api_key
            )
            path = run_world_model(
                run_configuration_path=arguments.run_configuration,
                repository_path=arguments.repository,
                runtime_directory=arguments.runtime_directory,
                result_directory=arguments.result_directory,
                qualification=qualification,
                configuration=configuration,
                transport=transport,
            )
            payload = {
                "status": "JWT_WORLD_MODEL_RESULT_CREATED",
                "result_path": str(path),
                "conformance_result_ref": qualification.result_ref,
                "oracle_content_available_to_runtime": False,
                "comparison": "NOT_RUN",
            }
        elif arguments.command == "seal-oracle":
            path = seal_direct_oracle(
                draft_path=arguments.draft,
                result_directory=arguments.result_directory,
                qualification=qualification,
                configuration=configuration,
                operator=arguments.operator,
                reviewer=arguments.reviewer,
            )
            payload = {
                "status": "DIRECT_ORACLE_SEALED",
                "result_path": str(path),
                "conformance_result_ref": qualification.result_ref,
                "available_to_swm_runtime": False,
            }
        else:
            path = freeze_jwt_run_configuration(
                oracle_path=arguments.oracle,
                repository_path=arguments.repository,
                result_directory=arguments.result_directory,
                qualification=qualification,
                configuration=configuration,
                operator=arguments.operator,
                runtime_directory=arguments.runtime_directory,
            )
            payload = {
                "status": "JWT_RUN_CONFIGURATION_FROZEN",
                "result_path": str(path),
                "conformance_result_ref": qualification.result_ref,
                "oracle_content_available_to_runtime": False,
                "live_capability_run": "NOT_RUN",
            }
        json.dump(payload, output, ensure_ascii=False, sort_keys=True)
        output.write("\n")
        return 0
    except ProviderOutcomeUnknown as exc:
        payload = {
            "error": "PROVIDER_OUTCOME_UNKNOWN",
            "message": "provider request outcome is unknown; start a new isolated run",
            "reason": exc.reason_code,
        }
        for key in ("world_role", "world_call_ordinal"):
            if hasattr(exc, key):
                payload[key] = getattr(exc, key)
        json.dump(payload, output, ensure_ascii=False, sort_keys=True)
        output.write("\n")
        return 3
    except (DomainError, ValueError) as exc:
        payload = {
            "error": exc.code.value if isinstance(exc, DomainError) else "INVALID_ARGUMENT",
            "message": exc.message if isinstance(exc, DomainError) else str(exc),
        }
        if isinstance(exc, DomainError):
            for key in (
                "http_status",
                "provider_error_code",
                "provider_error_type",
                "provider_request_id",
                "provider_envelope_class",
                "provider_choice_class",
                "provider_finish_reason",
                "finish_reason",
                "world_role",
                "world_call_ordinal",
                "semantic_id",
                "semantic_error",
                "semantic_expected",
                "assistant_message_class",
                "reasoning_content_present",
                "reasoning_content_bytes",
                "reasoning_content_digest",
                "assistant_content_class",
                "assistant_content_bytes",
                "assistant_content_digest",
                "assistant_content_prefix_class",
                "assistant_content_suffix_class",
                "content_json_parse",
                "content_json_error_position",
            ):
                if key in exc.details:
                    payload[key] = exc.details[key]
        json.dump(payload, output, ensure_ascii=False, sort_keys=True)
        output.write("\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
