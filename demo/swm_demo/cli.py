from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from swm_demo.application import ApplicationError, ApplicationServices


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(
        prog="swm-demo",
        description="Software World Model architecture validation CLI",
    )
    root.add_argument(
        "--db",
        type=Path,
        default=Path(".swm-demo/swm-demo.sqlite3"),
        help="SQLite validation state",
    )
    commands = root.add_subparsers(dest="command", required=True)

    configure = commands.add_parser("configure", help="configure a KnowledgeScope")
    configure.add_argument("--scope", required=True)
    configure.add_argument("--name", required=True)
    configure.add_argument("--source", required=True, type=Path)
    configure.add_argument("--expected-revision")

    update = commands.add_parser("update", help="build and publish a Snapshot")
    update.add_argument("--scope", required=True)
    update.add_argument(
        "--profile",
        choices=("structure-core", "full-validation"),
        default="structure-core",
    )

    structure = commands.add_parser(
        "structure", help="query the current Structure View"
    )
    structure.add_argument("--scope", required=True)

    endpoint = commands.add_parser(
        "endpoint", help="query one endpoint's Structure chain"
    )
    endpoint.add_argument("--scope", required=True)
    endpoint.add_argument("--name", required=True)

    view = commands.add_parser(
        "view", help="query a registered Semantic View"
    )
    view.add_argument("--scope", required=True)
    view.add_argument(
        "--name", choices=("structure", "behavior", "business", "history"), required=True
    )

    explain = commands.add_parser("explain", help="trace one Fact to Evidence")
    explain.add_argument("--scope", required=True)
    explain.add_argument("--fact", required=True)

    explain_inference = commands.add_parser(
        "explain-inference", help="trace one Inference to formal Facts"
    )
    explain_inference.add_argument("--scope", required=True)
    explain_inference.add_argument("--inference", required=True)

    snapshot = commands.add_parser("snapshot", help="show the current Snapshot")
    snapshot.add_argument("--scope", required=True)

    knowledge_open = commands.add_parser(
        "knowledge-open",
        help="open a fixed formal-knowledge Snapshot context",
    )
    knowledge_open.add_argument("--scope", required=True)

    knowledge_search = commands.add_parser(
        "knowledge-search",
        help="search formal Entity or Inference knowledge",
    )
    knowledge_search.add_argument("--scope", required=True)
    knowledge_search.add_argument("--context", required=True)
    knowledge_search.add_argument(
        "--kind", type=str.upper, choices=("ENTITY", "INFERENCE"), required=True
    )
    knowledge_search.add_argument("--query", required=True)
    knowledge_search.add_argument(
        "--match",
        type=str.upper,
        choices=("EXACT", "CONTAINS"),
        default="CONTAINS",
    )
    knowledge_search.add_argument(
        "--type",
        dest="type_name",
        help="optional exact Entity or Inference type filter",
    )
    knowledge_search.add_argument("--limit", type=int, default=20)
    knowledge_search.add_argument("--cursor", type=int, default=0)

    neighborhood = commands.add_parser(
        "knowledge-neighborhood",
        help="read a one-hop formal Fact neighborhood",
    )
    neighborhood.add_argument("--scope", required=True)
    neighborhood.add_argument("--context", required=True)
    neighborhood.add_argument(
        "--entity", dest="entity_ids", action="append", required=True
    )
    neighborhood.add_argument(
        "--direction",
        type=str.upper,
        choices=("OUTGOING", "INCOMING", "BOTH"),
        default="BOTH",
    )
    neighborhood.add_argument(
        "--predicate", dest="predicates", action="append"
    )
    neighborhood.add_argument("--limit", type=int, default=100)
    neighborhood.add_argument("--cursor", type=int, default=0)

    knowledge_explain = commands.add_parser(
        "knowledge-explain",
        help="batch trace formal Facts or Inferences",
    )
    knowledge_explain.add_argument("--scope", required=True)
    knowledge_explain.add_argument("--context", required=True)
    knowledge_explain.add_argument(
        "--kind", type=str.upper, choices=("FACT", "INFERENCE"), required=True
    )
    knowledge_explain.add_argument(
        "--id", dest="knowledge_ids", action="append", required=True
    )
    return root


def main(argv: list[str] | None = None) -> None:
    arguments = parser().parse_args(argv)
    services = ApplicationServices(arguments.db)
    try:
        if arguments.command == "configure":
            result = services.configure_scope(
                scope_id=arguments.scope,
                name=arguments.name,
                source_path=arguments.source,
                expected_revision=arguments.expected_revision,
            )
        elif arguments.command == "update":
            result = services.update_knowledge(arguments.scope, arguments.profile)
        elif arguments.command == "structure":
            result = services.query_structure(arguments.scope)
        elif arguments.command == "endpoint":
            result = services.query_endpoint_structure(
                arguments.scope, arguments.name
            )
        elif arguments.command == "view":
            result = services.query_semantic_view(arguments.scope, arguments.name)
        elif arguments.command == "explain":
            result = services.explain_fact(arguments.scope, arguments.fact)
        elif arguments.command == "explain-inference":
            result = services.explain_inference(
                arguments.scope, arguments.inference
            )
        elif arguments.command == "snapshot":
            result = services.current_snapshot(arguments.scope)
        elif arguments.command == "knowledge-open":
            result = services.open_knowledge_context(arguments.scope)
        elif arguments.command == "knowledge-search":
            result = services.search_knowledge(
                scope_id=arguments.scope,
                snapshot_token=arguments.context,
                kind=arguments.kind,
                query=arguments.query,
                match_mode=arguments.match,
                type_name=arguments.type_name,
                limit=arguments.limit,
                cursor=arguments.cursor,
            )
        elif arguments.command == "knowledge-neighborhood":
            result = services.query_knowledge_neighborhood(
                scope_id=arguments.scope,
                snapshot_token=arguments.context,
                entity_ids=tuple(arguments.entity_ids),
                direction=arguments.direction,
                predicates=tuple(arguments.predicates or ()),
                limit=arguments.limit,
                cursor=arguments.cursor,
            )
        elif arguments.command == "knowledge-explain":
            result = services.explain_knowledge_batch(
                scope_id=arguments.scope,
                snapshot_token=arguments.context,
                kind=arguments.kind,
                knowledge_ids=tuple(arguments.knowledge_ids),
            )
        else:
            raise AssertionError(f"unsupported command: {arguments.command}")
    except ApplicationError as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(2) from error
    finally:
        services.close()

    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
