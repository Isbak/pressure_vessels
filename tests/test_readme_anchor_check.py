from __future__ import annotations

from pathlib import Path
import subprocess
import sys


def test_readme_anchor_check_passes_for_repository_state() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/check_readme_anchors.py"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "passed" in result.stdout.lower()


def test_readme_anchor_check_fails_for_unresolved_anchor(tmp_path: Path) -> None:
    backlog = tmp_path / "development_backlog.yaml"
    readme = tmp_path / "README.md"

    backlog.write_text(
        """
items:
- id: BL-999
  references:
  - README.md#missing-anchor
""".strip()
        + "\n",
        encoding="utf-8",
    )
    readme.write_text("# Existing Heading\n", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "scripts/check_readme_anchors.py",
            "--backlog",
            str(backlog),
            "--readme",
            str(readme),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "README.md#missing-anchor" in result.stdout
