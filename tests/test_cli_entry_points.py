from __future__ import annotations

from pathlib import Path
import tomli


def test_project_scripts_include_ci_governance_helper_commands() -> None:
    payload = tomli.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    scripts = payload["project"]["scripts"]

    assert scripts["pv-suggest-risk-label"] == "pressure_vessels.dev_cli:suggest_risk_label_main"
    assert scripts["pv-check-tech-stack"] == "pressure_vessels.dev_cli:check_tech_stack_main"
    assert scripts["pv-check-readme-anchors"] == "pressure_vessels.dev_cli:check_readme_anchors_main"
