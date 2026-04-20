from __future__ import annotations

import json
from pathlib import Path
import subprocess

from pressure_vessels.requirements_pipeline import (
    CANONICAL_UNITS,
    MANDATORY_FIELDS,
    REQUIREMENT_SET_VERSION,
)
from pressure_vessels.workflow_orchestrator import (
    APPROVAL_GATE_EVENT_VERSION,
    WORKFLOW_EXECUTION_REPORT_VERSION,
    build_approval_gate_event,
    orchestrate_workflow,
    WorkflowStageSpec,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = REPO_ROOT / '.github/workflows/ci.yml'
REUSABLE_WORKFLOW_PATH = REPO_ROOT / '.github/workflows/reusable-governance-core.yml'
POLICY_PATH = REPO_ROOT / 'docs/governance/ci_governance_policy.v1.json'


def _load_workflow(path: Path) -> dict[str, object]:
    result = subprocess.run(
        [
            'ruby',
            '-e',
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


def test_frontend_backend_contract_shapes_remain_compatible() -> None:
    frontend_contract = Path('services/frontend/lib/prompt-contract.ts').read_text(encoding='utf-8')
    frontend_bff_route = Path('services/frontend/app/api/prompt/route.ts').read_text(encoding='utf-8')
    backend_contract = Path('docs/interfaces/backend_prompt_api_contract.md').read_text(
        encoding='utf-8'
    )
    backend_impl = Path('services/backend/src/main.ts').read_text(encoding='utf-8')

    assert "prompt: string" in frontend_contract
    assert "response: string" in frontend_contract
    assert "source: 'frontend-placeholder' | 'backend-service'" in frontend_contract

    assert 'const endpoint = new URL(\'/api/prompt\', BACKEND_API_BASE_URL);' in frontend_bff_route
    assert "if (!payload.prompt || !payload.response)" in frontend_bff_route
    assert "source: 'backend-service'" in frontend_bff_route

    assert 'GET /api/prompt?prompt=<text>' in backend_contract
    assert 'route": "deterministic-pipeline-v1"' in backend_contract
    assert "export function runDeterministicPromptPipeline" in backend_impl
    assert "route: 'deterministic-pipeline-v1'" in backend_impl


def test_requirements_pipeline_contract_constants_are_enforced() -> None:
    contract = Path('docs/interfaces/requirements_pipeline_contract.md').read_text(
        encoding='utf-8'
    )

    assert REQUIREMENT_SET_VERSION == 'RequirementSet.v1'
    assert all(field in MANDATORY_FIELDS for field in ('fluid', 'design_pressure', 'design_temperature', 'capacity', 'code_standard'))
    assert CANONICAL_UNITS == {
        'design_pressure': 'Pa',
        'design_temperature': 'C',
        'capacity': 'm3',
        'corrosion_allowance': 'mm',
    }

    assert 'downstream_blocked == false' in contract
    assert 'Deterministic regex-based extraction only' in contract


def test_workflow_orchestrator_contract_versions_and_state_vocabulary() -> None:
    contract = Path('docs/interfaces/workflow_orchestrator_contract.md').read_text(
        encoding='utf-8'
    )

    assert WORKFLOW_EXECUTION_REPORT_VERSION == 'WorkflowExecutionReport.v1'
    assert APPROVAL_GATE_EVENT_VERSION == 'ApprovalGateEvent.v1'

    approval = build_approval_gate_event(
        event_id='APR-DX009-1',
        workflow_id='wf-dx009',
        stage_id='approval_stage',
        gate_id='human_approval',
        decision='approved',
        approver_role='authorized_inspector',
        approver_id='insp-09',
        decided_at_utc='2026-04-19T12:00:00+00:00',
        rationale='Contract test approval.',
    )
    report = orchestrate_workflow(
        workflow_id='wf-dx009',
        stage_specs=[
            WorkflowStageSpec(stage_id='prepare', requires_approval=False),
            WorkflowStageSpec(stage_id='approval_stage', requires_approval=True),
        ],
        approval_events=[approval],
    )

    assert set(report.stage_states.values()).issubset(
        {
            'pending',
            'running',
            'pending_approval',
            'approved',
            'blocked',
            'rejected',
            'completed',
            'failed',
            'escalated',
        }
    )
    assert 'ApprovalGateEvent.v1' in contract
    assert 'WorkflowExecutionReport.v1' in contract


def test_contract_tests_are_wired_as_required_ci_gate() -> None:
    ci_workflow = _load_workflow(WORKFLOW_PATH)
    reusable_workflow = _load_workflow(REUSABLE_WORKFLOW_PATH)
    policy = json.loads(POLICY_PATH.read_text(encoding='utf-8'))

    contract_job = ci_workflow['jobs']['contract-tests']
    run_steps = [
        step for step in contract_job['steps'] if step.get('name') == 'Run contract tests'
    ]
    assert len(run_steps) == 1
    assert 'pytest -q tests/test_contract_interfaces_dx009.py' in run_steps[0]['run']

    required_gates = set(policy['required_gates'])
    governance_needs = set(ci_workflow['jobs']['governance-gate']['needs']) | set(
        reusable_workflow['jobs']['governance-gate']['needs']
    )
    assert 'contract-tests' in required_gates
    assert 'contract-tests' in governance_needs
