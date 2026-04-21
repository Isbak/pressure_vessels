from __future__ import annotations

from pathlib import Path
try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python <3.11 fallback for local test runners
    import tomli as tomllib


def test_project_scripts_include_ci_governance_helper_commands() -> None:
    payload = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    scripts = payload["project"]["scripts"]

    assert scripts["pv-suggest-risk-label"] == "pressure_vessels.dev_cli:suggest_risk_label_main"
    assert scripts["pv-check-tech-stack"] == "pressure_vessels.dev_cli:check_tech_stack_main"
    assert scripts["pv-check-readme-anchors"] == "pressure_vessels.dev_cli:check_readme_anchors_main"
    assert scripts["pv-scaffold-governance-baseline"] == "pressure_vessels.governance_scaffold:scaffold_governance_baseline_main"
