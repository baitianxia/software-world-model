"""Minimal structured CLI for recoverable source configuration."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Sequence, TextIO

from software_world_model.application_services import (
    ConfigureSystemSourceCommand,
    KnowledgeNeed,
    ManagementApplicationService,
)
from software_world_model.cross_cutting import (
    CorrelationRef,
    DomainError,
    IdempotencyKey,
    Revision,
    StableId,
)
from software_world_model.infrastructure import (
    SqliteDatabase,
    SqliteKnowledgeScopeRepository,
    SqliteManagementRepository,
    SqliteSourceConfigurationRepository,
    SqliteTelemetryRepository,
)
from software_world_model.knowledge_engine import (
    KnowledgeObjectKind,
    KnowledgeScopeService,
    ScopeType,
)
from software_world_model.source_integration import (
    LocalGitConfigurationProvider,
    ProviderRegistry,
    SourceConfigurationService,
    TargetKind,
)

from .runtime import ApplicationRuntime
from .agentic_runtime import activate_browser_experience
from .presenters import (
    knowledge_update_payload as _update_payload,
    management_execution_payload as _execution_payload,
    sufficiency_assessment_payload as _assessment_payload,
    target_resolution_payload as _resolution_payload,
    telemetry_events_payload as _telemetry_payload,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="swm", description="Software World Model management CLI")
    parser.add_argument("--database", required=True, help="SQLite database file")
    commands = parser.add_subparsers(dest="command", required=True)

    configure = commands.add_parser(
        "configure-system-source", help="create a system scope, Local Git source, and binding"
    )
    configure.add_argument("--idempotency-key", required=True)
    configure.add_argument("--source-target", required=True)
    configure.add_argument("--paths", default=".")
    configure.add_argument("--display-name", required=True)
    configure.add_argument("--classification", default="INTERNAL")
    configure.add_argument("--actor", required=True)
    configure.add_argument("--reason", required=True)
    configure.add_argument("--correlation-ref", required=True)

    activate = commands.add_parser(
        "activate-browser-experience",
        help="activate the evaluated answer strategy for one local browser environment",
    )
    activate.add_argument("--conformance-result", required=True)
    activate.add_argument("--qualification-proof", required=True)
    activate.add_argument("--environment", default="local-browser")
    activate.add_argument("--actor", default="local-experience-owner")
    activate.add_argument(
        "--reason", default="enable reviewed local browser experience"
    )

    show = commands.add_parser("show-attempt", help="show the effective management result")
    show.add_argument("attempt_id")

    resolve = commands.add_parser("resolve-target", help="resolve an exact Local Git target")
    _add_source_identity(resolve)
    _add_target(resolve)

    update = commands.add_parser(
        "update-knowledge", help="read an exact Local Git target and publish formal knowledge"
    )
    _add_source_identity(update)
    _add_target(update)
    update.add_argument("--scope-id", required=True)
    update.add_argument("--scope-revision", type=int, default=1)
    update.add_argument("--idempotency-key", required=True)
    update.add_argument("--objective", required=True)
    update.add_argument("--classification", default="INTERNAL")
    update.add_argument("--actor", required=True)
    update.add_argument("--correlation-ref", required=True)
    update.add_argument("--max-steps", type=int, default=8)
    update.add_argument("--max-items", type=int, default=100)
    update.add_argument("--max-bytes", type=int, default=256_000)

    query = commands.add_parser(
        "query-knowledge", help="assess one Need against an exact knowledge Snapshot"
    )
    query.add_argument("--scope-id", required=True)
    query.add_argument("--snapshot-id")
    query.add_argument("--idempotency-key", required=True)
    query.add_argument("--request", required=True)
    query.add_argument("--need-id", required=True)
    query.add_argument("--question", required=True)
    query.add_argument("--kinds", required=True, help="comma-separated ENTITY,FACT,INFERENCE")
    query.add_argument("--types", required=True, help="comma-separated formal type names")
    query.add_argument("--terms", required=True, help="comma-separated exact search terms")
    query.add_argument("--minimum-support", type=int, default=1)
    query.add_argument("--classification", default="INTERNAL")

    telemetry = commands.add_parser(
        "show-telemetry", help="list structured runtime events for one correlation reference"
    )
    telemetry.add_argument("--correlation-ref", required=True)
    return parser


def main(argv: Sequence[str] | None = None, *, stdout: TextIO | None = None) -> int:
    output = stdout or sys.stdout
    arguments = build_parser().parse_args(argv)
    database_path = Path(arguments.database)
    if database_path.parent != Path("."):
        database_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with SqliteDatabase(database_path) as database:
            if arguments.command == "activate-browser-experience":
                decision = activate_browser_experience(
                    database=database,
                    conformance_result_path=arguments.conformance_result,
                    qualification_proof_path=arguments.qualification_proof,
                    environment_name=arguments.environment,
                    actor=arguments.actor,
                    reason=arguments.reason,
                )
                payload = {
                    "status": "ACTIVATED",
                    "environment": arguments.environment,
                    "activation_revision": decision.activation_revision.value,
                    "strategy_version": decision.strategy_version,
                    "qualification_ref": (
                        decision.qualification.proof_ref
                        if decision.qualification
                        else None
                    ),
                    "activation_digest": decision.digest.value,
                }
            elif arguments.command == "configure-system-source":
                service = _management_service(database)
                command = ConfigureSystemSourceCommand.create(
                    idempotency_key=IdempotencyKey(arguments.idempotency_key),
                    caller="cli",
                    purpose="configure system source",
                    classification=arguments.classification,
                    request_context={"interface": "cli"},
                    scope_type=ScopeType.SYSTEM,
                    scope_metadata={"display_name": arguments.display_name},
                    provider_type=LocalGitConfigurationProvider.provider_type,
                    provider_contract_version=LocalGitConfigurationProvider.contract_version,
                    identity_domain="LOCAL",
                    source_target=arguments.source_target,
                    provider_configuration={"read_mode": "read_only"},
                    secret_reference=None,
                    selector={"paths": arguments.paths},
                    context_constraint={"revision_policy": "exact"},
                    context_hint=arguments.display_name,
                    actor=arguments.actor,
                    reason=arguments.reason,
                    correlation_ref=CorrelationRef(arguments.correlation_ref),
                )
                execution = service.configure(command)
                payload = _execution_payload(execution)
            elif arguments.command == "show-attempt":
                service = _management_service(database)
                execution = service.get(StableId(arguments.attempt_id))
                payload = _execution_payload(execution)
            else:
                runtime = ApplicationRuntime(database)
                if arguments.command == "resolve-target":
                    receipt = runtime.resolve_target(
                        source_id=StableId(arguments.source_id),
                        source_revision=Revision(arguments.source_revision),
                        binding_id=StableId(arguments.binding_id),
                        binding_revision=Revision(arguments.binding_revision),
                        target_kind=TargetKind(arguments.target_kind),
                        parameters=_target_parameters(arguments),
                    )
                    payload = _resolution_payload(receipt)
                elif arguments.command == "update-knowledge":
                    result = runtime.update_knowledge(
                        idempotency_key=IdempotencyKey(arguments.idempotency_key),
                        scope_id=StableId(arguments.scope_id),
                        scope_revision=Revision(arguments.scope_revision),
                        source_id=StableId(arguments.source_id),
                        source_revision=Revision(arguments.source_revision),
                        binding_id=StableId(arguments.binding_id),
                        binding_revision=Revision(arguments.binding_revision),
                        target_kind=TargetKind(arguments.target_kind),
                        target_parameters=_target_parameters(arguments),
                        objective_description=arguments.objective,
                        classification=arguments.classification,
                        actor=arguments.actor,
                        correlation_ref=CorrelationRef(arguments.correlation_ref),
                        max_steps=arguments.max_steps,
                        max_items_per_step=arguments.max_items,
                        max_bytes_per_step=arguments.max_bytes,
                    )
                    payload = _update_payload(result)
                elif arguments.command == "query-knowledge":
                    need = KnowledgeNeed(
                        need_id=arguments.need_id,
                        question=arguments.question,
                        required_kinds=tuple(
                            KnowledgeObjectKind(item) for item in _csv(arguments.kinds)
                        ),
                        required_type_names=_csv(arguments.types),
                        required_terms=_csv(arguments.terms),
                        minimum_support_count=arguments.minimum_support,
                    )
                    assessment = runtime.query_knowledge(
                        idempotency_key=IdempotencyKey(arguments.idempotency_key),
                        scope_id=StableId(arguments.scope_id),
                        snapshot_id=StableId(arguments.snapshot_id) if arguments.snapshot_id else None,
                        original_request=arguments.request,
                        needs=(need,),
                        classification=arguments.classification,
                    )
                    payload = _assessment_payload(assessment)
                else:
                    events = SqliteTelemetryRepository(database).list_by_correlation(
                        arguments.correlation_ref
                    )
                    payload = _telemetry_payload(events)
        json.dump(payload, output, ensure_ascii=False, sort_keys=True)
        output.write("\n")
        return 0
    except (DomainError, ValueError) as exc:
        payload = {
            "error": exc.code.value if isinstance(exc, DomainError) else "INVALID_ARGUMENT",
            "message": exc.message if isinstance(exc, DomainError) else str(exc),
        }
        json.dump(payload, output, ensure_ascii=False, sort_keys=True)
        output.write("\n")
        return 2


def _management_service(database: SqliteDatabase) -> ManagementApplicationService:
    scopes = KnowledgeScopeService(SqliteKnowledgeScopeRepository(database))
    sources = SourceConfigurationService(
        SqliteSourceConfigurationRepository(database),
        ProviderRegistry((LocalGitConfigurationProvider(),)),
        scopes,
    )
    return ManagementApplicationService(SqliteManagementRepository(database), scopes, sources)


def _add_source_identity(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--source-revision", type=int, default=1)
    parser.add_argument("--binding-id", required=True)
    parser.add_argument("--binding-revision", type=int, default=1)


def _add_target(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--target-kind",
        required=True,
        choices=tuple(item.value for item in TargetKind),
    )
    parser.add_argument("--revision")
    parser.add_argument("--base")
    parser.add_argument("--target")
    parser.add_argument("--path")
    parser.add_argument("--symbol")


def _target_parameters(arguments: argparse.Namespace) -> dict[str, str]:
    return {
        key: value
        for key in ("revision", "base", "target", "path", "symbol")
        if (value := getattr(arguments, key, None)) is not None
    }


def _csv(value: str) -> tuple[str, ...]:
    items = tuple(item.strip() for item in value.split(",") if item.strip())
    if not items:
        raise ValueError("comma-separated argument cannot be empty")
    return items


if __name__ == "__main__":
    raise SystemExit(main())
