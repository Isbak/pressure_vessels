from __future__ import annotations

import json
from pathlib import Path
import subprocess


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = REPO_ROOT / ".github/workflows/ci.yml"
POLICY_PATH = "docs/governance/ci_governance_policy.v1.json"
RETENTION_EXPR = "${{ steps.policy.outputs.retention }}"


def _load_workflow() -> dict[str, object]:
    result = subprocess.run(
        [
            "ruby",
            "-e",
            (
                "require 'yaml'; require 'json'; "
                "puts JSON.generate(YAML.safe_load(File.read(ARGV[0]), aliases: true))"
            ),
            str(WORKFLOW_PATH),
        ],
        check=True,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    return json.loads(result.stdout)


def test_ci_artifact_retention_is_sourced_from_policy_file() -> None:
    workflow = _load_workflow()
    jobs = workflow["jobs"]

    for job_name in ("python-tests", "governance-gate"):
        steps = jobs[job_name]["steps"]
        policy_steps = [step for step in steps if step.get("id") == "policy"]
        assert len(policy_steps) == 1

        policy_step = policy_steps[0]
        assert policy_step["run"]
        assert f"jq -r '.artifact_retention_days' {POLICY_PATH}" in policy_step["run"]

        upload_steps = [
            step
            for step in steps
            if step.get("uses") == "actions/upload-artifact@v4"
        ]
        assert upload_steps
        for upload_step in upload_steps:
            assert upload_step["with"]["retention-days"] == RETENTION_EXPR


def test_governance_gate_needs_and_policy_required_gates_are_in_lockstep() -> None:
    workflow = _load_workflow()
    policy = json.loads((REPO_ROOT / POLICY_PATH).read_text(encoding="utf-8"))

    required_gates = set(policy["required_gates"])
    governance_needs = set(workflow["jobs"]["governance-gate"]["needs"])
    defined_jobs = set(workflow["jobs"].keys())

    assert governance_needs == required_gates
    assert required_gates.issubset(defined_jobs)


def test_readme_anchor_check_job_runs_consistency_script() -> None:
    workflow = _load_workflow()
    steps = workflow["jobs"]["readme-anchor-check"]["steps"]

    check_steps = [
        step
        for step in steps
        if step.get("name") == "Validate backlog README anchor consistency"
    ]
    assert len(check_steps) == 1
    assert "python scripts/check_readme_anchors.py" in check_steps[0]["run"]


def test_governance_gate_emits_checklist_evidence_artifact() -> None:
    workflow = _load_workflow()
    steps = workflow["jobs"]["governance-gate"]["steps"]

    evidence_steps = [
        step
        for step in steps
        if step.get("name") == "Build governance checklist evidence payload"
    ]
    assert len(evidence_steps) == 1
    assert "python scripts/generate_governance_checklist_evidence.py" in evidence_steps[0]["run"]

    upload_steps = [
        step
        for step in steps
        if step.get("name") == "Upload governance audit artifacts"
    ]
    assert len(upload_steps) == 1
    uploaded_paths = upload_steps[0]["with"]["path"]
    assert "artifacts/ci/GovernanceChecklistEvidence.v1.json" in uploaded_paths
