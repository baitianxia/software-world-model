"""Skip guards for tests that need local, non-versioned resources.

Some historical validation tests read run evidence under ``var/`` (not in Git),
a prepared ``validation-projects/mall`` checkout, platform-specific sandboxes
or external tools.  On a clean checkout these resources are absent; the tests
are skipped with an explicit reason instead of failing for environmental
reasons.  They still run wherever the resources exist.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import unittest
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def requires_path(relative: str, purpose: str):
    path = REPOSITORY_ROOT / relative
    return unittest.skipUnless(
        path.exists(), f"requires local {purpose} at {relative} (not versioned)"
    )


def _is_git_checkout_with_origin(path: Path) -> bool:
    if not (path / ".git").exists():
        return False
    completed = subprocess.run(
        ["git", "-C", str(path), "config", "--get", "remote.origin.url"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return completed.returncode == 0


def requires_mall_checkout():
    return unittest.skipUnless(
        _is_git_checkout_with_origin(REPOSITORY_ROOT / "validation-projects" / "mall"),
        "requires the prepared validation-projects/mall checkout (see validation-projects/README.md)",
    )


def requires_tool(name: str):
    return unittest.skipUnless(shutil.which(name), f"requires the '{name}' executable")


def requires_macos(purpose: str):
    return unittest.skipUnless(sys.platform == "darwin", f"requires macOS: {purpose}")
