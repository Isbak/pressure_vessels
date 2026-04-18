from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
import os
import subprocess
import sys

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import check_ci_governance as governance_check


def _read_schema() -> dict[str, object]:
    return json.loads(
        (REPO_ROOT / "docs/governance/policy_exceptions_schema.v1.json").read_text(encoding="utf-8")
    )


def test_policy_exceptions_schema_validation_rejects_missing_required_fields() -> None:
    document = {
        "version": 1,
        "exceptions": [
            {
                "id": "EX-2026-001",
                "gate": "secret-scan",
                "scope": ["docs/**"],
                "justification": "False positive under review.",
                "approver": "@security-reviewer",
                "approved_at": "2026-04-18T00:00:00Z",
                "expires_at": "2026-05-18T00:00:00Z",
                # linked_backlog_id intentionally missing
            }
        ],
    }

    with pytest.raises(ValueError, match="linked_backlog_id"):
        governance_check._validate_exceptions_document(document, _read_schema())


def test_policy_exception_expiry_and_scope_matching() -> None:
    exception = governance_check.PolicyException(
        id="EX-2026-002",
        gate="markdown-links",
        scope=["docs/**/*.md"],
        justification="Intermittent external docs outage.",
        approver="@docs-reviewer",
        approved_at="2026-04-18T00:00:00Z",
        expires_at="2026-04-19T00:00:00Z",
        linked_backlog_id="BL-099",
    )

    assert governance_check._scope_matches(
        scope_patterns=exception.scope,
        changed_paths=["docs/governance/README.md"],
    )
    assert not governance_check._scope_matches(
        scope_patterns=exception.scope,
        changed_paths=["src/pressure_vessels/governance_pipeline.py"],
    )

    now_before_expiry = datetime(2026, 4, 18, 12, 0, tzinfo=timezone.utc)
    now_after_expiry = datetime(2026, 4, 19, 0, 1, tzinfo=timezone.utc)
    assert not governance_check._is_expired(exception=exception, now_utc=now_before_expiry)
    assert governance_check._is_expired(exception=exception, now_utc=now_after_expiry)


def test_control_drift_validation_rejects_unmanaged_or_missing_gates() -> None:
    with pytest.raises(ValueError, match="missing required gates in CI results: markdown-lint"):
        governance_check._validate_control_drift(
            required_gates=["docs-check", "markdown-lint"],
            gate_results={"docs-check": "success"},
        )

    with pytest.raises(ValueError, match="unmanaged CI gates absent from policy: markdown-links"):
        governance_check._validate_control_drift(
            required_gates=["docs-check"],
            gate_results={"docs-check": "success", "markdown-links": "success"},
        )


def test_check_ci_governance_happy_path_with_matching_unexpired_exception(tmp_path: Path) -> None:
    policy_path = tmp_path / "policy.json"
    exceptions_path = tmp_path / "exceptions.json"
    gate_results_path = tmp_path / "job-results.json"
    report_path = tmp_path / "report.json"

    policy_path.write_text(
        json.dumps(
            {
                "schema_version": "CIGovernancePolicy.v1",
                "artifact_retention_days": 30,
                "required_gates": ["secret-scan"],
            }
        ),
        encoding="utf-8",
    )
    exceptions_path.write_text(
        json.dumps(
            {
                "version": 1,
                "exceptions": [
                    {
                        "id": "EX-2026-003",
                        "gate": "secret-scan",
                        "scope": ["docs/**"],
                        "justification": "False-positive scan signature pending upstream fix.",
                        "approver": "@security-reviewer",
                        "approved_at": "2026-04-18T00:00:00Z",
                        "expires_at": "2099-01-01T00:00:00Z",
                        "linked_backlog_id": "BL-120",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    gate_results_path.write_text(
        json.dumps(
            {
                "_changed_paths": ["docs/governance/README.md"],
                "secret-scan": "failure",
            }
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts/check_ci_governance.py"),
            str(policy_path),
            str(exceptions_path),
            str(gate_results_path),
            str(report_path),
        ],
        capture_output=True,
        text=True,
        check=False,
        cwd=REPO_ROOT,
        env={**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")},
    )

    assert result.returncode == 0
    assert "Exception applied: gate=secret-scan id=EX-2026-003 approver=@security-reviewer" in result.stdout

    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["failed_gates"] == []
    assert report["applied_exception_ids"] == ["EX-2026-003"]


def test_check_ci_governance_failure_when_exception_expired_or_scope_mismatch(tmp_path: Path) -> None:
    policy_path = tmp_path / "policy.json"
    exceptions_path = tmp_path / "exceptions.json"
    gate_results_path = tmp_path / "job-results.json"
    report_path = tmp_path / "report.json"

    policy_path.write_text(
        json.dumps(
            {
                "schema_version": "CIGovernancePolicy.v1",
                "artifact_retention_days": 30,
                "required_gates": ["python-tests"],
            }
        ),
        encoding="utf-8",
    )
    exceptions_path.write_text(
        json.dumps(
            {
                "version": 1,
                "exceptions": [
                    {
                        "id": "EX-2026-004",
                        "gate": "python-tests",
                        "scope": ["docs/**"],
                        "justification": "Temporary issue, expired exception.",
                        "approver": "@eng-reviewer",
                        "approved_at": "2026-04-01T00:00:00Z",
                        "expires_at": "2026-04-02T00:00:00Z",
                        "linked_backlog_id": "BL-121",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    gate_results_path.write_text(
        json.dumps(
            {
                "_changed_paths": ["src/pressure_vessels/governance_pipeline.py"],
                "python-tests": "failure",
            }
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts/check_ci_governance.py"),
            str(policy_path),
            str(exceptions_path),
            str(gate_results_path),
            str(report_path),
        ],
        capture_output=True,
        text=True,
        check=False,
        cwd=REPO_ROOT,
        env={**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")},
    )

    assert result.returncode == 1
    assert "Governance gate failed for: python-tests" in result.stdout

    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["failed_gates"] == ["python-tests"]
    assert report["applied_exception_ids"] == []
