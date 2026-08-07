"""Sanitized model-provider configuration and transport probe CLI."""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Mapping, Sequence, TextIO

from software_world_model.ai_infrastructure import (
    OutputSchemaDefinition,
    ProviderOutcomeUnknown,
    UrllibVolcengineArkChatTransport,
    VolcengineArkChatCompletionsNoToolsAdapter,
    VolcengineArkModelConfiguration,
    run_ark_chat_conformance,
    seal_ark_chat_conformance_result,
)
from software_world_model.ai_infrastructure.model_gateway import ProviderRequest, RenderedMessage
from software_world_model.cross_cutting import DomainError, digest_of


_PROBE_SCHEMA_REF = "provider-transport-probe@1"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="swm-provider",
        description="Inspect or probe the configured model-provider boundary",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("status", help="show sanitized configuration without network access")
    probe = commands.add_parser(
        "probe",
        help="send one minimal strict-JSON request; this is not full live conformance",
    )
    probe.add_argument("--timeout-milliseconds", type=int, default=30_000)
    probe.add_argument("--max-output-tokens", type=int, default=64)
    conformance = commands.add_parser(
        "conformance",
        help="run the two-call live Ark adapter conformance and seal a sanitized result",
    )
    conformance.add_argument("--result-directory", required=True)
    conformance.add_argument("--operator", default="local-operator")
    conformance.add_argument("--timeout-milliseconds", type=int, default=30_000)
    conformance.add_argument("--max-output-tokens", type=int, default=96)
    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    stdout: TextIO | None = None,
    environment: Mapping[str, str] | None = None,
    transport: object | None = None,
) -> int:
    output = stdout or sys.stdout
    arguments = build_parser().parse_args(argv)
    environment_values = os.environ if environment is None else environment
    configuration = VolcengineArkModelConfiguration()
    try:
        if arguments.command == "status":
            payload = configuration.public_status(environment_values)
            exit_code = 0
        elif arguments.command == "probe":
            if arguments.timeout_milliseconds < 1 or arguments.max_output_tokens < 1:
                raise ValueError("probe resource bounds must be positive")
            active_transport = transport or UrllibVolcengineArkChatTransport(
                api_key_resolver=lambda: configuration.resolve_api_key(environment_values)
            )
            response = _probe(
                configuration,
                active_transport,
                timeout_milliseconds=arguments.timeout_milliseconds,
                max_output_tokens=arguments.max_output_tokens,
            )
            payload = {
                **configuration.public_status(environment_values),
                "transport_probe": "PASS",
                "actual_model_fingerprint": response.actual_model_fingerprint,
                "provider_request_id": response.provider_request_id,
                "usage_complete": response.usage_complete,
                "input_tokens": response.input_tokens,
                "output_tokens": response.output_tokens,
                "production_eligible": False,
                "qualification_status": "CAPABILITY_EVALUATION_NOT_RUN",
            }
            exit_code = 0
        else:
            active_transport = transport or UrllibVolcengineArkChatTransport(
                api_key_resolver=lambda: configuration.resolve_api_key(environment_values)
            )
            result = run_ark_chat_conformance(
                configuration=configuration,
                transport=active_transport,
                environment=environment_values,
                operator=arguments.operator,
                timeout_milliseconds=arguments.timeout_milliseconds,
                max_output_tokens=arguments.max_output_tokens,
            )
            result_path = seal_ark_chat_conformance_result(
                result, arguments.result_directory
            )
            payload = {
                "conformance": result["outcome"],
                "fixture_id": result["fixture_id"],
                "run_id": result["run_id"],
                "result_digest": result["result_digest"],
                "result_path": str(result_path),
                "actual_model_fingerprints": result["model"]["actual_model_fingerprints"],
                "request_count": result["execution"]["request_count"],
                "provider_request_ids": result["execution"]["provider_request_ids"],
                "input_tokens": result["execution"]["input_tokens"],
                "output_tokens": result["execution"]["output_tokens"],
                "production_eligible": False,
                "qualification_status": "CAPABILITY_EVALUATION_NOT_RUN",
            }
            exit_code = 0 if result["outcome"] == "PASS" else 4
        json.dump(payload, output, ensure_ascii=False, sort_keys=True)
        output.write("\n")
        return exit_code
    except ProviderOutcomeUnknown as exc:
        payload = {
            "error": "PROVIDER_OUTCOME_UNKNOWN",
            "reason": exc.reason_code,
            "message": "provider request outcome is unknown; inspect network and retry as a new probe",
        }
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
            ):
                if key in exc.details:
                    payload[key] = exc.details[key]
        json.dump(payload, output, ensure_ascii=False, sort_keys=True)
        output.write("\n")
        return 2


def _probe(
    configuration: VolcengineArkModelConfiguration,
    transport: object,
    *,
    timeout_milliseconds: int,
    max_output_tokens: int,
):
    schema = OutputSchemaDefinition(
        "provider_transport_probe",
        {
            "type": "object",
            "properties": {"status": {"type": "string", "enum": ["ok"]}},
            "required": ["status"],
            "additionalProperties": False,
        },
    )
    adapter = VolcengineArkChatCompletionsNoToolsAdapter(
        transport=transport,
        configuration=configuration,
        output_schemas={_PROBE_SCHEMA_REF: schema},
    )
    system_text = 'Return only the JSON object {"status":"ok"}.'
    user_text = "Confirm this provider transport probe."
    request_core = {
        "model_ref": configuration.model_ref,
        "messages": (system_text, user_text),
        "output_schema_ref": _PROBE_SCHEMA_REF,
        "max_output_tokens": max_output_tokens,
        "timeout_milliseconds": timeout_milliseconds,
    }
    return adapter.invoke(
        ProviderRequest(
            model_ref=configuration.model_ref,
            messages=(
                RenderedMessage("system", system_text, "probe-instruction", digest_of(system_text)),
                RenderedMessage("user", user_text, "probe-request", digest_of(user_text)),
            ),
            output_schema_ref=_PROBE_SCHEMA_REF,
            tools=(),
            store=False,
            stream=False,
            max_output_tokens=max_output_tokens,
            timeout_milliseconds=timeout_milliseconds,
            metadata=(("purpose", "transport-probe"),),
            digest=digest_of(request_core),
        )
    )


if __name__ == "__main__":
    raise SystemExit(main())
