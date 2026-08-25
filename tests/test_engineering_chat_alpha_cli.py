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
            scripts["swm-engineering-qa"],
            "software_world_model.interface.engineering_qa_alpha_cli:main",
        )

    def test_fixed_command_accepts_no_runtime_scope_arguments(self) -> None:
        parser = build_parser()
        self.assertEqual(parser.prog, "swm-engineering-chat")
        destinations = {
            action.dest for action in parser._actions if action.dest != "help"
        }
        self.assertEqual(destinations, set())

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


if __name__ == "__main__":
    unittest.main()
