from __future__ import annotations

import json
from pathlib import Path
import subprocess


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = REPO_ROOT / ".github/workflows/ci.yml"
REUSABLE_WORKFLOW_PATH = REPO_ROOT / ".github/workflows/reusable-governance-core.yml"
POLICY_PATH = "docs/governance/ci_governance_policy.v1.json"
RETENTION_EXPR = "${{ steps.policy.outputs.retention }}"


def _load_workflow(path: Path) -> dict[str, object]:
    result = subprocess.run(
        [
            "ruby",
            "-e",
            (
                "require 'yaml'; require 'json'; "
                "puts JSON.generate(YAML.safe_load(File.read(ARGV[0]), aliases: true))"
            ),
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    return json.loads(result.stdout)


def test_ci_artifact_retention_is_sourced_from_policy_file() -> None:
    ci_workflow = _load_workflow(WORKFLOW_PATH)
    reusable_workflow = _load_workflow(REUSABLE_WORKFLOW_PATH)
    ci_jobs = ci_workflow["jobs"]
    reusable_jobs = reusable_workflow["jobs"]

    for job_name in ("python-tests",):
        steps = ci_jobs[job_name]["steps"]
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

    for job_name in ("governance-gate", "risk-label-suggestion"):
        steps = reusable_jobs[job_name]["steps"]
        policy_steps = [step for step in steps if step.get("id") == "policy"]
        assert len(policy_steps) == 1

        policy_step = policy_steps[0]
        assert policy_step["run"]
        assert (
            "jq -r '.artifact_retention_days' \"${{ inputs.ci_policy_path }}\""
            in policy_step["run"]
        )

        upload_steps = [
            step
            for step in steps
            if step.get("uses") == "actions/upload-artifact@v4"
        ]
        assert upload_steps
        for upload_step in upload_steps:
            assert upload_step["with"]["retention-days"] == RETENTION_EXPR


def test_governance_gate_needs_and_policy_required_gates_are_in_lockstep() -> None:
    ci_workflow = _load_workflow(WORKFLOW_PATH)
    reusable_workflow = _load_workflow(REUSABLE_WORKFLOW_PATH)
    policy = json.loads((REPO_ROOT / POLICY_PATH).read_text(encoding="utf-8"))

    required_gates = set(policy["required_gates"])
    governance_needs = set(ci_workflow["jobs"]["governance-gate"]["needs"]) | set(
        reusable_workflow["jobs"]["governance-gate"]["needs"]
    )
    defined_jobs = set(ci_workflow["jobs"].keys()) | set(reusable_workflow["jobs"].keys())

    assert required_gates.issubset(governance_needs)
    assert required_gates.issubset(defined_jobs)


def test_readme_anchor_check_job_runs_consistency_script() -> None:
    workflow = _load_workflow(REUSABLE_WORKFLOW_PATH)
    steps = workflow["jobs"]["readme-anchor-check"]["steps"]

    check_steps = [
        step
        for step in steps
        if step.get("name") == "Validate backlog README anchor consistency"
    ]
    assert len(check_steps) == 1
    assert "pv-check-readme-anchors" in check_steps[0]["run"]


def test_governance_gate_emits_checklist_evidence_artifact() -> None:
    workflow = _load_workflow(REUSABLE_WORKFLOW_PATH)
    steps = workflow["jobs"]["governance-gate"]["steps"]

    enforce_steps = [
        step
        for step in steps
        if step.get("name") == "Enforce governance policy gates"
    ]
    assert len(enforce_steps) == 1
    assert "pv-check-ci-governance" in enforce_steps[0]["run"]
    assert "--exceptions-schema \"${{ inputs.exceptions_schema_path }}\"" in enforce_steps[0]["run"]

    evidence_steps = [
        step
        for step in steps
        if step.get("name") == "Build governance checklist evidence payload"
    ]
    assert len(evidence_steps) == 1
    assert "pv-generate-governance-checklist-evidence" in evidence_steps[0]["run"]

    upload_steps = [
        step
        for step in steps
        if step.get("name") == "Upload governance audit artifacts"
    ]
    assert len(upload_steps) == 1
    uploaded_paths = upload_steps[0]["with"]["path"]
    assert "${{ inputs.checklist_evidence_path }}" in uploaded_paths


def test_risk_label_suggestion_job_is_advisory_and_publishes_artifacts() -> None:
    workflow = _load_workflow(REUSABLE_WORKFLOW_PATH)
    job = workflow["jobs"]["risk-label-suggestion"]

    assert job["if"] == "github.event_name == 'pull_request'"

    steps = job["steps"]
    build_steps = [
        step
        for step in steps
        if step.get("name") == "Build advisory risk label suggestion"
    ]
    assert len(build_steps) == 1
    assert "pv-suggest-risk-label" in build_steps[0]["run"]

    publish_steps = [
        step
        for step in steps
        if step.get("name") == "Publish risk suggestion summary"
    ]
    assert len(publish_steps) == 1
    assert "GITHUB_STEP_SUMMARY" in publish_steps[0]["run"]

    upload_steps = [
        step
        for step in steps
        if step.get("name") == "Upload risk suggestion artifact"
    ]
    assert len(upload_steps) == 1
    uploaded_paths = upload_steps[0]["with"]["path"]
    assert "${{ inputs.risk_suggestion_json_path }}" in uploaded_paths
