from __future__ import annotations

from io import StringIO
import json
from pathlib import Path
import subprocess
from types import SimpleNamespace
import tempfile
import tomllib
import unittest
from unittest.mock import patch

from software_world_model.cross_cutting import DomainError, ErrorCode
from software_world_model.interface.engineering_chat_alpha_cli import (
    ENGINEERING_CHAT_ALPHA_PORT,
    build_parser,
    main,
    prepare_engineering_chat_access,
)


class EngineeringChatAlphaCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.product = self.root / "product"
        self.project = self.root / "mall"
        self.product.mkdir()
        self.project.mkdir()
        self._initialize(self.product, "product.txt", "chat access\n")
        self._initialize(self.project, "README.md", "mall fixture\n")
        self.project_revision = self.git(self.project, "rev-parse", "HEAD")

    def _initialize(self, repository: Path, name: str, content: str) -> None:
        self.git(repository, "init", "-q")
        self.git(repository, "config", "user.email", "chat@example.invalid")
        self.git(repository, "config", "user.name", "Chat Test")
        (repository / name).write_text(content, encoding="utf-8")
        self.git(repository, "add", name)
        self.git(repository, "commit", "-q", "-m", "initial")

    @staticmethod
    def git(repository: Path, *arguments: str) -> str:
        return subprocess.run(
            ("git", "-C", str(repository), *arguments),
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        ).stdout.strip()

    def test_distribution_exposes_distinct_chat_command_without_rebranding_qa(self) -> None:
        project = tomllib.loads(
            (Path(__file__).parents[1] / "pyproject.toml").read_text(
                encoding="utf-8"
            )
        )
        scripts = project["project"]["scripts"]

        self.assertEqual(
            scripts["swm-engineering-chat"],
            "software_world_model.interface.engineering_chat_alpha_cli:main",
        )
        self.assertEqual(
            scripts["swm-engineering-qa-evaluation"],
            "software_world_model.interface.engineering_qa_alpha_cli:main",
        )

    def test_fixed_command_accepts_only_one_sealed_session_artifact(self) -> None:
        parser = build_parser()
        self.assertEqual(parser.prog, "swm-engineering-chat")
        destinations = {
            action.dest for action in parser._actions if action.dest != "help"
        }
        self.assertEqual(destinations, {"session_config"})

    def test_prepare_binds_clean_exact_revisions_without_provider(self) -> None:
        prepared = prepare_engineering_chat_access(
            product_repository=self.product,
            project_repository=self.project,
            expected_project_revision=self.project_revision,
        )
        status = prepared.public_status()

        self.assertEqual(
            prepared.binding.product_revision,
            self.git(self.product, "rev-parse", "HEAD"),
        )
        self.assertEqual(prepared.binding.repository_revision, self.project_revision)
        self.assertEqual(status["url"], "http://127.0.0.1:8765/")
        self.assertEqual(status["project"]["name"], "mall")
        self.assertEqual(status["provider"]["status"], "NOT_CONFIGURED")
        self.assertFalse(status["provider"]["external_dispatch"])
        self.assertFalse(status["model_call_authorized"])
        self.assertEqual(status["browser_live_verification"], "NOT_EXECUTED")
        self.assertEqual(status["production_activation"], "NOT_EXECUTED")
        self.assertIn(
            "src/main/resources",
            status["project"]["excluded_source_paths"],
        )

    def test_prepare_fails_before_listener_for_dirty_or_drifted_repository(self) -> None:
        (self.product / "untracked.txt").write_text("dirty\n", encoding="utf-8")
        with self.assertRaises(DomainError) as dirty:
            prepare_engineering_chat_access(
                product_repository=self.product,
                project_repository=self.project,
                expected_project_revision=self.project_revision,
            )
        self.assertEqual(dirty.exception.code, ErrorCode.CONTROL_STATE_DENIED)

        (self.product / "untracked.txt").unlink()
        with self.assertRaises(DomainError) as drifted:
            prepare_engineering_chat_access(
                product_repository=self.product,
                project_repository=self.project,
                expected_project_revision="f" * 40,
            )
        self.assertEqual(
            drifted.exception.code, ErrorCode.SOURCE_REVISION_INCONSISTENT
        )

    def test_main_binds_only_fixed_loopback_and_prints_truthful_status(self) -> None:
        events: list[object] = []
        application = object()
        prepared = SimpleNamespace(
            application=application,
            public_status=lambda: {
                "status": "READY",
                "model_call_authorized": False,
                "production_activation": "NOT_EXECUTED",
            },
        )

        class FakeServer:
            server_port = ENGINEERING_CHAT_ALPHA_PORT

            def __enter__(self):
                events.append("enter")
                return self

            def __exit__(self, *_):
                events.append("exit")
                return False

            def serve_forever(self):
                events.append("serve")

        def server_factory(host, port, app, *, handler_class):
            events.append((host, port, app, handler_class.__name__))
            return FakeServer()

        stdout = StringIO()
        stderr = StringIO()
        with (
            patch(
                "software_world_model.interface.engineering_chat_alpha_cli.prepare_engineering_chat_access",
                return_value=prepared,
            ),
            patch(
                "software_world_model.interface.engineering_chat_alpha_cli.make_server",
                side_effect=server_factory,
            ),
        ):
            outcome = main([], stdout=stdout, stderr=stderr)

        self.assertEqual(outcome, 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(json.loads(stdout.getvalue())["status"], "READY")
        self.assertEqual(events[0][0:3], ("127.0.0.1", 8765, application))
        self.assertEqual(events[1:], ["enter", "serve", "exit"])

    def test_artifact_main_starts_with_denied_unused_fallback_and_seals_receipts(self) -> None:
        events: list[object] = []
        application = object()
        session_path = self.root / "session.json"
        ark_database = self.root / "ark.sqlite3"
        deepseek_database = self.root / "deepseek.sqlite3"
        launch_path = self.root / "launch.json"
        terminal_path = self.root / "terminal.json"
        session_config = SimpleNamespace(
            path=session_path,
            provider_routes=(
                SimpleNamespace(gateway_database=str(ark_database)),
                SimpleNamespace(gateway_database=str(deepseek_database)),
            ),
            launch_receipt=str(launch_path),
            terminal_receipt=str(terminal_path),
        )

        class FakeDatabase:
            def __enter__(self):
                return self

            def __exit__(self, *_):
                return False

        class FakeServer:
            server_port = ENGINEERING_CHAT_ALPHA_PORT

            def __enter__(self):
                events.append("listener-enter")
                return self

            def __exit__(self, *_):
                events.append("listener-exit")
                return False

            def serve_forever(self):
                events.append("serve")

        primary_transport = object()

        class FallbackTransport:
            def close(self):
                events.append("transport-close")

        prepared = SimpleNamespace(
            runtime=SimpleNamespace(
                launcher=SimpleNamespace(application=application),
                primary_provider_runtime=SimpleNamespace(
                    transport=primary_transport
                ),
                fallback_provider_runtime=SimpleNamespace(
                    transport=FallbackTransport(),
                    dispatch_admission_controller=SimpleNamespace(
                        receipt=SimpleNamespace(
                            allowed=False,
                            decision=SimpleNamespace(value="DENIED_PEAK_WINDOW"),
                        )
                    ),
                ),
            ),
            public_status=lambda: {
                "status": "ARK_TRANSPORT_SESSION_AUDIT_LOCAL_CANDIDATE",
                "production_activation": "NOT_EXECUTED",
            },
            launch_receipt=lambda: {"schema": "launch"},
            terminal_receipt=lambda: {"schema": "terminal"},
        )

        def create_database(path):
            events.append(("create-database", path.name))

        def write_receipt(path, value):
            events.append(("write", path.name, value["schema"]))

        stdout = StringIO()
        stderr = StringIO()
        with (
            patch(
                "software_world_model.interface.engineering_chat_alpha_cli.load_engineering_chat_artifact_session_config",
                return_value=session_config,
            ),
            patch(
                "software_world_model.interface.engineering_chat_alpha_cli._new_database_path",
                side_effect=(ark_database, deepseek_database),
            ),
            patch(
                "software_world_model.interface.engineering_chat_alpha_cli._new_private_output_path",
                side_effect=(launch_path, terminal_path),
            ),
            patch(
                "software_world_model.interface.engineering_chat_alpha_cli._create_new_private_database",
                side_effect=create_database,
            ),
            patch(
                "software_world_model.interface.engineering_chat_alpha_cli.SqliteDatabase",
                side_effect=(FakeDatabase(), FakeDatabase()),
            ),
            patch(
                "software_world_model.interface.engineering_chat_alpha_cli.SqliteModelGatewayRepository",
                side_effect=(object(), object()),
            ),
            patch(
                "software_world_model.interface.engineering_chat_alpha_cli.prepare_engineering_chat_artifact_session",
                return_value=prepared,
            ),
            patch(
                "software_world_model.interface.engineering_chat_alpha_cli.make_server",
                return_value=FakeServer(),
            ) as make_server,
            patch(
                "software_world_model.interface.engineering_chat_alpha_cli._write_new_private_json",
                side_effect=write_receipt,
            ),
        ):
            outcome = main(
                ["--session-config", str(session_path)],
                stdout=stdout,
                stderr=stderr,
            )

        self.assertEqual(outcome, 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertTrue(json.loads(stdout.getvalue())["listener_started"])
        self.assertEqual(
            make_server.call_args.args[:3],
            ("127.0.0.1", ENGINEERING_CHAT_ALPHA_PORT, application),
        )
        self.assertEqual(
            events,
            [
                ("create-database", "ark.sqlite3"),
                ("create-database", "deepseek.sqlite3"),
                ("write", "launch.json", "launch"),
                "listener-enter",
                "serve",
                "listener-exit",
                ("write", "terminal.json", "terminal"),
                "transport-close",
            ],
        )

        failed_stdout = StringIO()
        failed_stderr = StringIO()
        with patch(
            "software_world_model.interface.engineering_chat_alpha_cli.load_engineering_chat_artifact_session_config",
            side_effect=DomainError(
                ErrorCode.CONTROL_STATE_DENIED,
                "sealed artifact rejected",
            ),
        ):
            failed_outcome = main(
                ["--session-config", str(session_path)],
                stdout=failed_stdout,
                stderr=failed_stderr,
            )
        self.assertEqual(failed_outcome, 2)
        self.assertEqual(failed_stdout.getvalue(), "")
        self.assertIsNone(
            json.loads(failed_stderr.getvalue())["model_call_authorized"]
        )


if __name__ == "__main__":
    unittest.main()
