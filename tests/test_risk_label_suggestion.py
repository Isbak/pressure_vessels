from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]


def _run_script(
    tmp_path: Path,
    changed_paths: list[str],
    heuristics_config: Path | None = None,
) -> dict[str, object]:
    changed_paths_file = tmp_path / "changed-paths.txt"
    changed_paths_file.write_text("\n".join(changed_paths) + "\n", encoding="utf-8")

    payload_path = tmp_path / "RiskLabelSuggestion.v1.json"
    summary_path = tmp_path / "RiskLabelSuggestion.summary.md"

    command = [
        sys.executable,
        str(REPO_ROOT / "scripts/suggest_risk_label.py"),
        str(changed_paths_file),
        str(payload_path),
        str(summary_path),
    ]
    if heuristics_config is not None:
        command.append(str(heuristics_config))

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
        cwd=REPO_ROOT,
    )

    assert result.returncode == 0, result.stderr
    assert summary_path.exists()
    return json.loads(payload_path.read_text(encoding="utf-8"))


def test_risk_label_suggestion_high_for_governance_workflow_changes(tmp_path: Path) -> None:
    payload = _run_script(
        tmp_path,
        [".github/workflows/ci.yml", "docs/developer_command_reference.md"],
    )

    assert payload["schema_version"] == "RiskLabelSuggestion.v1"
    assert payload["suggested_risk"] == "high"
    assert payload["advisory_only"] is True


def test_risk_label_suggestion_low_for_docs_only_changes(tmp_path: Path) -> None:
    payload = _run_script(
        tmp_path,
        ["docs/developer_command_reference.md", "README.md"],
    )

    assert payload["suggested_risk"] == "low"
    assert payload["confidence"] == "high"


def test_risk_label_suggestion_medium_for_application_code_changes(tmp_path: Path) -> None:
    payload = _run_script(
        tmp_path,
        ["src/pressure_vessels/requirements_pipeline.py"],
    )

    assert payload["suggested_risk"] == "medium"


def test_risk_label_suggestion_uses_override_heuristics_config(tmp_path: Path) -> None:
    override_config = tmp_path / "risk_label_heuristics.override.json"
    override_config.write_text(
        json.dumps(
            {
                "high_risk_rules": [],
                "medium_risk_prefixes": [],
                "medium_risk_files": [],
                "low_risk_prefixes": [],
                "low_risk_files": [],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    payload = _run_script(
        tmp_path,
        ["docs/developer_command_reference.md"],
        heuristics_config=override_config,
    )

    assert payload["suggested_risk"] == "medium"
    assert payload["confidence"] == "low"
