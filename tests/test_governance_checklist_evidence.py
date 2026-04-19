from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_generate_governance_checklist_evidence_outputs_machine_readable_payload(tmp_path: Path) -> None:
    job_results = tmp_path / "job-results.json"
    gate_report = tmp_path / "GovernanceGateReport.v1.json"
    checklist = tmp_path / "GovernanceChecklistEvidence.v1.json"

    job_results.write_text(
        json.dumps(
            {
                "python-tests": "success",
                "secret-scan": "failure",
                "docs-check": "success",
                "_changed_paths": ["docs/developer_command_reference.md"],
            }
        ),
        encoding="utf-8",
    )
    gate_report.write_text(
        json.dumps(
            {
                "failed_gates": ["secret-scan"],
                "applied_exception_ids": ["EX-2026-007"],
            }
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts/generate_governance_checklist_evidence.py"),
            str(job_results),
            str(gate_report),
            str(checklist),
        ],
        capture_output=True,
        text=True,
        check=False,
        cwd=REPO_ROOT,
    )

    assert result.returncode == 0
    assert checklist.exists()

    payload = json.loads(checklist.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "GovernanceChecklistEvidence.v1"
    assert payload["ci_evidence"]["failed_gates"] == ["secret-scan"]

    items = {item["id"]: item for item in payload["checklist_items"]}
    assert items["required_tests_executed"]["status"] == "pass"
    assert items["security_secret_scan_passed"]["status"] == "fail"
    assert items["risk_class_selected"]["status"] == "manual"
