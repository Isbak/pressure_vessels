from __future__ import annotations

import json
from pathlib import Path
import subprocess


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = REPO_ROOT / ".github/workflows/preview-environment.yml"
RUNBOOK_PATH = REPO_ROOT / "docs/runbooks/preview_environment_lifecycle_operations.md"
ROADMAP_PATH = REPO_ROOT / "docs/platform_roadmap.yaml"
NEXT_PROMPT_PATH = REPO_ROOT / "docs/next_dx_generation_prompt.md"


def _load_yaml(path: Path) -> dict[str, object]:
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


def test_preview_workflow_launches_on_pull_request_and_has_teardown_path() -> None:
    workflow = _load_yaml(WORKFLOW_PATH)

    on_block = workflow.get("on") or workflow.get("true")
    pull_request = on_block["pull_request"]
    assert "closed" in pull_request["types"]
    assert "opened" in pull_request["types"]
    assert workflow["jobs"]["launch-preview"]["if"] == "github.event.action != 'closed'"
    assert workflow["jobs"]["teardown-preview"]["if"] == "github.event.action == 'closed'"


def test_preview_workflow_uses_deterministic_isolation_key_and_ttl_policy() -> None:
    workflow = _load_yaml(WORKFLOW_PATH)

    assert workflow["concurrency"]["group"] == "preview-pr-${{ github.event.pull_request.number }}"

    launch_steps = workflow["jobs"]["launch-preview"]["steps"]
    metadata_steps = [
        step for step in launch_steps if step.get("name") == "Build deterministic preview metadata"
    ]
    assert len(metadata_steps) == 1
    run_script = metadata_steps[0]["run"]
    assert "preview_slug=\"pr-${pr_number}-${short_sha}\"" in run_script
    assert "teardown-on-pr-close-or-72h-ttl" in run_script


def test_preview_lifecycle_runbook_documents_deterministic_teardown_policy() -> None:
    runbook = RUNBOOK_PATH.read_text(encoding="utf-8")

    assert "Teardown trigger (hard stop)" in runbook
    assert "TTL fallback" in runbook and "72 hours" in runbook
    assert ".github/workflows/preview-environment.yml" in runbook


def test_dx010_closed_out_in_roadmap_and_prompt_advanced() -> None:
    roadmap = ROADMAP_PATH.read_text(encoding="utf-8")
    prompt = NEXT_PROMPT_PATH.read_text(encoding="utf-8")

    dx010_section = roadmap.split("id: DX-010", maxsplit=1)[1]
    assert "status: done" in dx010_section
    assert (
        "no remaining eligible dx roadmap item" in prompt.lower()
        or "You are implementing DXR-001" in prompt
        or "You are implementing DXR-002" in prompt
    )
