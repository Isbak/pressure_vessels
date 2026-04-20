"""Packaged CLI entry points that delegate to canonical repository scripts.

This avoids logic drift between `scripts/*.py` and console entry points exposed via
`[project.scripts]`.
"""

from __future__ import annotations

from pathlib import Path
import runpy
import sys


def suggest_risk_label_main(argv: list[str] | None = None) -> int:
    return _run_repo_script("suggest_risk_label.py", argv)


def check_tech_stack_main(argv: list[str] | None = None) -> int:
    return _run_repo_script("check_tech_stack.py", argv)


def check_readme_anchors_main(argv: list[str] | None = None) -> int:
    return _run_repo_script("check_readme_anchors.py", argv)


def _run_repo_script(script_name: str, argv: list[str] | None) -> int:
    repo_root = Path(__file__).resolve().parents[2]
    script_path = repo_root / "scripts" / script_name

    if not script_path.exists():
        raise FileNotFoundError(f"Expected script entry point not found: {script_path}")

    original_argv = sys.argv
    sys.argv = [str(script_path), *(argv or [])]
    try:
        runpy.run_path(str(script_path), run_name="__main__")
    except SystemExit as exc:
        code = exc.code
        if code is None:
            return 0
        if isinstance(code, int):
            return code
        return 1
    finally:
        sys.argv = original_argv

    return 0
