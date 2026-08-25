"""Start ITER-010 Chat Access or one sealed artifact-backed Chat Session.

No arguments preserves the verified no-Provider Access checkpoint.  The sole
operator input, ``--session-config``, selects an owner-private closed artifact;
it does not expose host, port, project, revision, Provider, question, credential,
or individual authority controls.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys
from typing import Sequence, TextIO
from wsgiref.simple_server import WSGIRequestHandler, make_server

from software_world_model.application_services.engineering_conversation import (
    ENGINEERING_CHAT_ACCESS_VERSION,
    EngineeringChatBinding,
    InMemoryEngineeringConversationService,
    RuntimeCapabilityStatus,
)
from software_world_model.cross_cutting import DomainError, ErrorCode, canonical_json_bytes
from software_world_model.infrastructure import (
    SqliteDatabase,
    SqliteModelGatewayRepository,
)

from .engineering_chat_browser import (
    ENGINEERING_CHAT_LOOPBACK_ORIGIN,
    EngineeringChatBrowserApplication,
)
from .engineering_chat_session_artifact import (
    PreparedEngineeringChatArtifactSession,
    load_engineering_chat_artifact_session_config,
    prepare_engineering_chat_artifact_session,
)
from .engineering_qa_preview_cli import (
    _create_new_private_database,
    _new_database_path,
    _new_private_output_path,
    _private_file_creation_mask,
    _write_new_private_json,
)


ENGINEERING_CHAT_ALPHA_PORT = 8765
ENGINEERING_CHAT_PROJECT_NAME = "mall"
ENGINEERING_CHAT_PROJECT_REVISION = "0504e86b1f1b6f1b8aa6a734d37a90fb67346be7"


@dataclass(frozen=True, slots=True)
class PreparedEngineeringChatAccess:
    application: EngineeringChatBrowserApplication
    binding: EngineeringChatBinding
    product_tree: str

    def public_status(self) -> dict[str, object]:
        health = self.application.health()
        return {
            **health,
            "url": f"{ENGINEERING_CHAT_LOOPBACK_ORIGIN}/",
            "product": {
                **health["product"],
                "tree": self.product_tree,
            },
            "startup": "FIXED_NO_ARGUMENT_COMMAND",
            "model_call_authorized": False,
            "browser_live_verification": "NOT_EXECUTED",
        }


def prepare_engineering_chat_access(
    *,
    product_repository: Path | None = None,
    project_repository: Path | None = None,
    expected_project_revision: str | None = None,
) -> PreparedEngineeringChatAccess:
    product_root = (
        product_repository.resolve()
        if product_repository is not None
        else Path(__file__).resolve().parents[3]
    )
    project_root = (
        project_repository.resolve()
        if project_repository is not None
        else (product_root / "validation-projects" / ENGINEERING_CHAT_PROJECT_NAME)
    )
    if product_root == project_root:
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            "product and fixed engineering project require distinct repositories",
        )
    product_commit, product_tree = _clean_git_identity(
        product_root, "product repository"
    )
    project_commit, _ = _clean_git_identity(project_root, "engineering project")
    required_project_commit = (
        expected_project_revision
        if expected_project_revision is not None
        else ENGINEERING_CHAT_PROJECT_REVISION
    )
    if project_commit != required_project_commit:
        raise DomainError(
            ErrorCode.SOURCE_REVISION_INCONSISTENT,
            "fixed Engineering Chat project revision drifted",
            {
                "expected_revision": required_project_commit,
                "actual_revision": project_commit,
            },
        )
    binding = EngineeringChatBinding.create(
        product_version=ENGINEERING_CHAT_ACCESS_VERSION,
        product_revision=product_commit,
        project_name=ENGINEERING_CHAT_PROJECT_NAME,
        repository_revision=project_commit,
        world_model_status=RuntimeCapabilityStatus.NOT_CONFIGURED,
        source_access_status=RuntimeCapabilityStatus.NOT_CONFIGURED,
        provider_status=RuntimeCapabilityStatus.NOT_CONFIGURED,
        excluded_source_paths=("src/main/resources",),
        known_limitations=(
            "Chat Access only; the conversational engineering Agent is not connected",
            "Provider is not configured or qualified; submitted Turns close with an honest limitation",
            "World Model cognition and controlled Source tools are not connected in this Access build",
            "Conversation state is process-memory only and resets when the service stops",
            "src/main/resources and configuration credentials are excluded",
        ),
    )
    service = InMemoryEngineeringConversationService(binding)
    application = EngineeringChatBrowserApplication(service)
    return PreparedEngineeringChatAccess(
        application=application,
        binding=binding,
        product_tree=product_tree,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="swm-engineering-chat",
        description=__doc__,
    )
    parser.add_argument("--session-config")
    return parser


class _QuietLoopbackHandler(WSGIRequestHandler):
    def setup(self) -> None:
        super().setup()
        self.connection.settimeout(30.0)

    def log_message(self, format: str, *args: object) -> None:
        del format, args


def main(
    argv: Sequence[str] | None = None,
    *,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> int:
    output = stdout or sys.stdout
    error_output = stderr or sys.stderr
    error_model_call_authorized: bool | None = False
    try:
        arguments = build_parser().parse_args(argv)
        if arguments.session_config is None:
            _run_access(output)
        else:
            error_model_call_authorized = None
            _run_artifact_session(arguments.session_config, output)
        return 0
    except (DomainError, OSError, subprocess.SubprocessError, ValueError) as exc:
        payload = {
            "error": (
                exc.code.value if isinstance(exc, DomainError) else "INVALID_ARGUMENT"
            ),
            "message": exc.message if isinstance(exc, DomainError) else str(exc),
            "model_call_authorized": error_model_call_authorized,
            "production_activation": "NOT_EXECUTED",
        }
        error_output.write(canonical_json_bytes(payload).decode("utf-8") + "\n")
        error_output.flush()
        return 2


def _run_access(output: TextIO) -> None:
    prepared = prepare_engineering_chat_access()
    with make_server(
        "127.0.0.1",
        ENGINEERING_CHAT_ALPHA_PORT,
        prepared.application,
        handler_class=_QuietLoopbackHandler,
    ) as server:
        _require_fixed_port(server)
        output.write(
            canonical_json_bytes(prepared.public_status()).decode("utf-8") + "\n"
        )
        output.flush()
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


def _run_artifact_session(value: str | Path, output: TextIO) -> None:
    session_config = load_engineering_chat_artifact_session_config(value)
    ark_route, deepseek_route = session_config.provider_routes
    ark_database_path = _new_database_path(ark_route.gateway_database)
    deepseek_database_path = _new_database_path(deepseek_route.gateway_database)
    launch_receipt_path = _new_private_output_path(session_config.launch_receipt)
    terminal_receipt_path = _new_private_output_path(
        session_config.terminal_receipt
    )
    if len(
        {
            session_config.path,
            ark_database_path,
            deepseek_database_path,
            launch_receipt_path,
            terminal_receipt_path,
        }
    ) != 5:
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            "Chat Session config, Gateway databases, and receipts require distinct paths",
        )
    _create_new_private_database(ark_database_path)
    _create_new_private_database(deepseek_database_path)
    prepared: PreparedEngineeringChatArtifactSession | None = None
    try:
        with _private_file_creation_mask():
            with (
                SqliteDatabase(ark_database_path) as ark_database,
                SqliteDatabase(deepseek_database_path) as deepseek_database,
            ):
                prepared = prepare_engineering_chat_artifact_session(
                    session_config,
                    ark_gateway_repository=SqliteModelGatewayRepository(
                        ark_database
                    ),
                    deepseek_gateway_repository=SqliteModelGatewayRepository(
                        deepseek_database
                    ),
                    at=datetime.now(timezone.utc),
                )
                _write_new_private_json(
                    launch_receipt_path,
                    prepared.launch_receipt(),
                )
                with make_server(
                    "127.0.0.1",
                    ENGINEERING_CHAT_ALPHA_PORT,
                    prepared.runtime.launcher.application,
                    handler_class=_QuietLoopbackHandler,
                ) as server:
                    _require_fixed_port(server)
                    status = {
                        **prepared.public_status(),
                        "listener_started": True,
                    }
                    output.write(
                        canonical_json_bytes(status).decode("utf-8") + "\n"
                    )
                    output.flush()
                    try:
                        server.serve_forever()
                    except KeyboardInterrupt:
                        pass
                _write_new_private_json(
                    terminal_receipt_path,
                    prepared.terminal_receipt(),
                )
    finally:
        if prepared is not None:
            for runtime in (
                prepared.runtime.primary_provider_runtime,
                prepared.runtime.fallback_provider_runtime,
            ):
                close = getattr(runtime.transport, "close", None)
                if callable(close):
                    close()


def _require_fixed_port(server) -> None:
    if server.server_port != ENGINEERING_CHAT_ALPHA_PORT:
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "Engineering Chat listener port drifted",
        )


def _clean_git_identity(repository: Path, label: str) -> tuple[str, str]:
    if not repository.is_absolute() or not repository.is_dir():
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            f"{label} must be an existing absolute directory",
        )
    top_level = Path(_git(repository, "rev-parse", "--show-toplevel")).resolve()
    if top_level != repository:
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            f"{label} must name the exact Git worktree root",
        )
    commit = _git(repository, "rev-parse", "HEAD")
    tree = _git(repository, "rev-parse", "HEAD^{tree}")
    if len(commit) != 40 or len(tree) != 40:
        raise DomainError(
            ErrorCode.SOURCE_REVISION_INCONSISTENT,
            f"{label} did not resolve to exact Git identities",
        )
    dirty = _git(repository, "status", "--porcelain", "--untracked-files=all")
    if dirty:
        raise DomainError(
            ErrorCode.CONTROL_STATE_DENIED,
            f"{label} must be clean before the Chat Access listener starts",
        )
    return commit, tree


def _git(repository: Path, *arguments: str) -> str:
    return subprocess.run(
        ("git", "-C", str(repository), *arguments),
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    ).stdout.strip()


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "ENGINEERING_CHAT_ALPHA_PORT",
    "ENGINEERING_CHAT_PROJECT_NAME",
    "ENGINEERING_CHAT_PROJECT_REVISION",
    "PreparedEngineeringChatAccess",
    "build_parser",
    "main",
    "prepare_engineering_chat_access",
]
