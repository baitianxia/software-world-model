from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import shutil
import tempfile
import time

from swm_demo.agent_orchestrator import AgentOrchestrator
from swm_demo.agent_contract import AgentTask
from swm_demo.answer_review_agent import AnswerReviewAgent
from swm_demo.application import ApplicationServices
from swm_demo.codex_cli_provider import CodexCliProvider
from swm_demo.model_gateway import ModelGateway
from swm_demo.task_execution_agent import TaskExecutionAgent, TaskExecutionError


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(
        description=(
            "Run one non-product diagnostic through the built-in Agent with an "
            "ephemeral Codex CLI adapter. The CLI is not a mechanically no-tools "
            "runtime; tool events are detected only after execution."
        )
    )
    root.add_argument("--source-db", required=True, type=Path)
    root.add_argument("--scope", default="system:mall")
    root.add_argument("--request", required=True)
    root.add_argument("--model", default="gpt-5.6-sol")
    root.add_argument("--codex", default="codex")
    root.add_argument("--timeout", type=float, default=300.0)
    root.add_argument(
        "--knowledge-use-only",
        action="store_true",
        help="stop at the first Gap instead of opening Source Investigation",
    )
    root.add_argument(
        "--acknowledge-codex-agent-runtime",
        action="store_true",
        help=(
            "explicitly accept that Codex CLI may attempt read-only tool actions "
            "before the diagnostic rejects their JSONL events"
        ),
    )
    return root


class _KnowledgeUseOnlyTaskAgent(TaskExecutionAgent):
    def _run_investigation(self, task: AgentTask, assessment, context):
        raise TaskExecutionError(
            "DIAGNOSTIC_KNOWLEDGE_GAP",
            "knowledge-use-only diagnostic stopped before Source Investigation",
            str(context["snapshot_id"]),
        )


def main(argv: list[str] | None = None) -> None:
    arguments = parser().parse_args(argv)
    source_database = arguments.source_db.resolve()
    if not source_database.is_file():
        raise SystemExit(f"source database does not exist: {source_database}")

    with tempfile.TemporaryDirectory(prefix="swm-real-model-diagnostic-") as temporary:
        database = Path(temporary) / "diagnostic.sqlite3"
        shutil.copy2(source_database, database)
        services = ApplicationServices(database)
        try:
            before_calls = services.store.model_call_count()
            provider = CodexCliProvider(
                executable=arguments.codex,
                model=arguments.model,
                timeout_seconds=arguments.timeout,
                allow_agent_runtime=arguments.acknowledge_codex_agent_runtime,
            )
            gateway = ModelGateway(provider, services.store)
            task_agent_class = (
                _KnowledgeUseOnlyTaskAgent
                if arguments.knowledge_use_only
                else TaskExecutionAgent
            )
            task_agent = task_agent_class(services, gateway)
            review_agent = AnswerReviewAgent(services, gateway)
            orchestrator = AgentOrchestrator(task_agent, review_agent, gateway)

            started = time.monotonic()
            failure: Exception | None = None
            response = None
            try:
                response = orchestrator.handle(arguments.request, arguments.scope)
            except Exception as error:  # diagnostic boundary: preserve the trace
                failure = error
            elapsed_seconds = time.monotonic() - started
            records = services.store.connection.execute(
                """
                SELECT capability, provider, model, model_version,
                       context_id, phase, response
                FROM model_calls
                ORDER BY rowid
                LIMIT -1 OFFSET ?
                """,
                (before_calls,),
            ).fetchall()
            model_calls = []
            for item in records:
                record = dict(item)
                record["response"] = json.loads(str(record["response"]))
                model_calls.append(record)
            output = {
                "kind": "REAL_MODEL_DIAGNOSTIC_NOT_PRODUCT_GATE",
                "request": arguments.request,
                "scope_id": arguments.scope,
                "model": arguments.model,
                "elapsed_seconds": round(elapsed_seconds, 3),
                "response": asdict(response) if response is not None else None,
                "failure": (
                    {
                        "type": type(failure).__name__,
                        "message": str(failure),
                    }
                    if failure is not None
                    else None
                ),
                "knowledge_use_only": arguments.knowledge_use_only,
                "model_calls": model_calls,
            }
            print(
                json.dumps(
                    output,
                    ensure_ascii=False,
                    indent=2,
                    sort_keys=True,
                )
            )
            if failure is not None:
                raise SystemExit(1)
        finally:
            services.close()


if __name__ == "__main__":
    main()
