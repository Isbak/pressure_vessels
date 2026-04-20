"""Regression tests for DX-002 local task runner wiring."""

from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent


def _run_make(target: str, *, dry_run: bool = False) -> str:
    """Return output for a make target, optionally in dry-run mode."""
    cmd = ["make"]
    if dry_run:
        cmd.append("-n")

    completed = subprocess.run(
        [*cmd, target],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout


def test_short_aliases_execute_for_non_pytest_workflows() -> None:
    """Run make aliases directly for governance and stack checks."""
    _run_make("g")
    _run_make("s")


def test_aliases_expand_to_expected_workflows() -> None:
    """Dry-runs should show canonical command wiring for each alias.

    `make t`/`make v`/`make ci` are checked with dry-runs to avoid recursively
    invoking pytest from inside pytest.
    """
    assert "pytest -q" in _run_make("t", dry_run=True)
    assert "python scripts/check_readme_anchors.py" in _run_make("g", dry_run=True)
    assert "python scripts/check_tech_stack.py" in _run_make("s", dry_run=True)
    assert "pytest -q" in _run_make("v", dry_run=True)
    assert "npm --prefix services/frontend run smoke" in _run_make("v", dry_run=True)
    assert "npm --prefix services/backend run smoke" in _run_make("v", dry_run=True)
    assert "pytest -q" in _run_make("ci", dry_run=True)
    assert "npm --prefix services/frontend run smoke" in _run_make("ci", dry_run=True)
    assert "npm --prefix services/backend run smoke" in _run_make("ci", dry_run=True)


def test_bootstrap_remains_canonical_onboarding_entrypoint() -> None:
    """Dry-run bootstrap should include both Python and JS bootstrap steps."""
    output = _run_make("bootstrap", dry_run=True)

    assert "pip install --upgrade pip" in output
    assert "pip install -e . pytest" in output
    assert "command -v node" in output
    assert "npm --prefix services/frontend install" in output
    assert "npm --prefix services/backend install" in output


def test_validate_js_supports_explicit_local_skip_override() -> None:
    """A no-Node local environment can explicitly skip JS validation."""
    output = _run_make("validate-js", dry_run=True)
    assert "npm --prefix services/frontend run smoke" in output
    assert "npm --prefix services/backend run smoke" in output

    skipped = subprocess.run(
        ["make", "JS_VALIDATE=0", "validate-js"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "Skipping JS validation because JS_VALIDATE=0." in skipped.stdout
