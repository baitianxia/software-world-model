from __future__ import annotations

from io import StringIO
import json
from pathlib import Path
import tempfile
import unittest

from software_world_model.cross_cutting import DomainError, ErrorCode
from software_world_model.interface.cli import main
from software_world_model.source_integration import LocalGitConfigurationProvider


class LocalGitConfigurationTests(unittest.TestCase):
    def test_source_target_requires_absolute_path_and_is_canonical(self) -> None:
        provider = LocalGitConfigurationProvider()
        with self.assertRaises(DomainError) as raised:
            provider.normalize_data_source(
                identity_domain="LOCAL",
                source_target="relative/repo",
                provider_configuration={},
                secret_reference=None,
            )
        self.assertEqual(raised.exception.code, ErrorCode.INVALID_ARGUMENT)

        normalized = provider.normalize_data_source(
            identity_domain="LOCAL",
            source_target="/projects/example/../repo",
            provider_configuration={"read_mode": "read_only"},
            secret_reference=None,
        )
        self.assertEqual(normalized.canonical_source_target, "/projects/repo")

    def test_selector_rejects_parent_traversal_and_normalizes_paths(self) -> None:
        provider = LocalGitConfigurationProvider()
        with self.assertRaises(DomainError) as raised:
            provider.normalize_selection(selector={"paths": "../secret"}, context_constraint={})
        self.assertEqual(raised.exception.code, ErrorCode.SELECTOR_INVALID)

        selection = provider.normalize_selection(
            selector={"paths": "src/main/, src/test,src/main"},
            context_constraint={"revision_policy": "exact"},
        )
        self.assertEqual(dict(selection.selector)["paths"], "src/main,src/test")

    def test_cli_configures_and_reloads_same_effective_result(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "swm.sqlite3"
            source = Path(directory) / "repo"
            source.mkdir()
            first_output = StringIO()
            exit_code = main(
                [
                    "--database",
                    str(database),
                    "configure-system-source",
                    "--idempotency-key",
                    "cli-configure",
                    "--source-target",
                    str(source),
                    "--display-name",
                    "Example",
                    "--actor",
                    "operator",
                    "--reason",
                    "test",
                    "--correlation-ref",
                    "cli-test",
                ],
                stdout=first_output,
            )
            first = json.loads(first_output.getvalue())
            second_output = StringIO()
            replay_code = main(
                [
                    "--database",
                    str(database),
                    "show-attempt",
                    first["attempt_id"],
                ],
                stdout=second_output,
            )
            second = json.loads(second_output.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(replay_code, 0)
        self.assertEqual(first["state"], "SUCCEEDED")
        self.assertEqual(second["result_digest"], first["result_digest"])


if __name__ == "__main__":
    unittest.main()
