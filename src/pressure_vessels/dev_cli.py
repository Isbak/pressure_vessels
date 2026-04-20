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


def scaffold_governance_baseline_main(argv: list[str] | None = None) -> int:
    from pressure_vessels.governance_scaffold import scaffold_governance_baseline_main as _main

    return _main(argv)


def check_readme_anchors_main(argv: list[str] | None = None) -> int:
    normalized_args = list(argv or [])
    if normalized_args and not normalized_args[0].startswith("-"):
        normalized_args = ["--backlog", normalized_args[0], *normalized_args[1:]]
    return _run_repo_script("check_readme_anchors.py", normalized_args)


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


def main(argv: list[str] | None = None) -> int:
    args = list(argv or sys.argv[1:])
    if not args:
        print(
            "usage: python -m pressure_vessels.dev_cli <check-readme-anchors|check-tech-stack|suggest-risk-label|scaffold-governance-baseline> [args...]",
            file=sys.stderr,
        )
        return 2

    command, command_args = args[0], args[1:]
    if command == "check-readme-anchors":
        return check_readme_anchors_main(command_args)
    if command == "check-tech-stack":
        return check_tech_stack_main(command_args)
    if command == "suggest-risk-label":
        return suggest_risk_label_main(command_args)
    if command == "scaffold-governance-baseline":
        return scaffold_governance_baseline_main(command_args)

    print(f"unknown command: {command}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
