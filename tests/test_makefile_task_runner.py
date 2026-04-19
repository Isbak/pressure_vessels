"""Regression tests for DX-002 local task runner wiring."""

from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent


def _run_make_dry_run(target: str) -> str:
    """Return make dry-run output for a target."""
    completed = subprocess.run(
        ["make", "-n", target],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout


def test_short_alias_targets_are_available() -> None:
    """Short aliases should resolve without make errors."""
    for target in ("t", "g", "s", "v", "ci"):
        _run_make_dry_run(target)


def test_aliases_expand_to_expected_workflows() -> None:
    """Alias dry-runs should include canonical workflow commands."""
    assert "pytest -q" in _run_make_dry_run("t")
    assert "python scripts/check_readme_anchors.py" in _run_make_dry_run("g")
    assert "python scripts/check_tech_stack.py" in _run_make_dry_run("s")
