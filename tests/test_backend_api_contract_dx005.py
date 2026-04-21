from __future__ import annotations

from pathlib import Path


def _parse_backlog_items() -> list[dict[str, object]]:
    lines = Path('docs/development_backlog.yaml').read_text(encoding='utf-8').splitlines()
    items: list[dict[str, object]] = []
    current: dict[str, object] | None = None
    in_depends_on = False

    for line in lines:
        if line.startswith('- id: '):
            if current is not None:
                items.append(current)
            current = {'id': line.split(': ', maxsplit=1)[1].strip(), 'status': '', 'depends_on': []}
            in_depends_on = False
            continue

        if current is None:
            continue

        if line.startswith('  status: '):
            current['status'] = line.split(': ', maxsplit=1)[1].strip()
            in_depends_on = False
            continue

        if line.startswith('  depends_on:'):
            in_depends_on = True
            continue

        if in_depends_on and line.startswith('  - '):
            current['depends_on'].append(line.strip()[2:])
            continue

        if in_depends_on and not line.startswith('  - '):
            in_depends_on = False

    if current is not None:
        items.append(current)

    return items


def _next_eligible_backlog_id() -> str:
    items = _parse_backlog_items()
    item_by_id = {str(item['id']): item for item in items}
    for item in items:
        if str(item['status']) != 'todo':
            continue
        depends_on = [str(dep) for dep in item['depends_on']]
        if all(str(item_by_id[dep]['status']) == 'done' for dep in depends_on):
            return str(item['id'])
    raise AssertionError('No eligible todo backlog item found.')


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


def test_bl040_is_done_and_next_prompt_advances_to_bl041() -> None:
    backlog = Path('docs/development_backlog.yaml').read_text(encoding='utf-8')
    next_prompt = Path('docs/next_code_generation_prompt.md').read_text(
        encoding='utf-8'
    )

    bl039_block = backlog.split('id: BL-039', maxsplit=1)[1].split(
        'id: BL-041', maxsplit=1
    )[0]
    assert 'status: done' in bl039_block

    bl040_block = backlog.split('id: BL-040', maxsplit=1)[1].split('id: BL-041', maxsplit=1)[0]
    assert 'status: done' in bl040_block
    bl041_block = backlog.split('id: BL-041', maxsplit=1)[1].split('id: BL-042', maxsplit=1)[0]
    assert 'status: done' in bl041_block

    expected_next_backlog_id = _next_eligible_backlog_id()
    assert expected_next_backlog_id in next_prompt
    assert f'next queued roadmap item: {expected_next_backlog_id}' in next_prompt
