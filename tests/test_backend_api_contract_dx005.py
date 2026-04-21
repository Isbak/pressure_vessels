from __future__ import annotations

from pathlib import Path


def test_backend_main_exposes_bl034_versioned_design_run_routes() -> None:
    main_ts = Path('services/backend/src/main.ts').read_text(encoding='utf-8')

    assert 'export function startDesignRun' in main_ts
    assert 'export function getDesignRunStatus' in main_ts
    assert 'authorizeRuntimeToken' in main_ts
    assert "['engineer', 'reviewer', 'approver']" in main_ts
    assert "statusUrl: `/api/${DESIGN_RUN_API_VERSION}/design-runs/${runId}`" in main_ts
    assert "workflowState: 'completed'" in main_ts


def test_backend_api_contract_documents_versioned_design_run_endpoints() -> None:
    contract = Path('docs/interfaces/backend_prompt_api_contract.md').read_text(
        encoding='utf-8'
    )

    assert 'POST /api/v1/design-runs' in contract
    assert 'GET /api/v1/design-runs/{runId}' in contract
    assert 'Primary consumer: `services/frontend`' in contract
    assert 'Authorization: Bearer v1:<actorId>:<role>:<scope>:<secret>' in contract
    assert 'engineer' in contract
    assert 'reviewer' in contract
    assert 'approver' in contract


def test_backend_secrets_integration_uses_approved_module_path_without_plaintext_fallback() -> None:
    secrets_ts = Path('services/backend/src/secrets.ts').read_text(encoding='utf-8')
    assert "infra/platform/secrets/module.boundaries.yaml" in secrets_ts
    assert 'PV_BACKEND_AUTH_TOKEN_SECRET' in secrets_ts
    assert 'fallback' not in secrets_ts.lower()


def test_frontend_route_implements_ui_to_api_to_orchestrator_happy_path() -> None:
    frontend_route = Path('services/frontend/app/api/prompt/route.ts').read_text(
        encoding='utf-8'
    )

    assert "const startEndpoint = new URL('/api/v1/design-runs', BACKEND_API_BASE_URL)" in frontend_route
    assert "const statusEndpoint = new URL(startPayload.statusUrl, BACKEND_API_BASE_URL)" in frontend_route
    assert 'WorkflowExecutionReport.v1' in frontend_route
    assert "source: 'backend-service'" in frontend_route


def test_frontend_result_view_displays_workflow_and_compliance_summary() -> None:
    result_page = Path('services/frontend/app/result/page.tsx').read_text(
        encoding='utf-8'
    )

    assert 'Workflow state:' in result_page
    assert 'Compliance status:' in result_page
    assert 'Checks:' in result_page
    assert 'Artifacts' in result_page


def test_bl036_is_done_and_next_prompt_advances_to_bl037() -> None:
    backlog = Path('docs/development_backlog.yaml').read_text(encoding='utf-8')
    next_prompt = Path('docs/next_code_generation_prompt.md').read_text(
        encoding='utf-8'
    )

    bl036_block = backlog.split('id: BL-036', maxsplit=1)[1].split(
        'id: BL-037', maxsplit=1
    )[0]
    assert 'status: done' in bl036_block

    assert 'BL-039' in next_prompt
    assert 'current next roadmap item: BL-039' in next_prompt
