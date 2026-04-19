from __future__ import annotations

from pathlib import Path


def test_backend_main_exposes_dx005_routes() -> None:
    main_ts = Path('services/backend/src/main.ts').read_text(encoding='utf-8')

    assert 'export function getHealth' in main_ts
    assert 'export function runDeterministicPromptPipeline' in main_ts
    assert 'Deterministic pipeline response:' in main_ts


def test_backend_api_contract_documented_for_frontend_consumption() -> None:
    contract = Path('docs/interfaces/backend_prompt_api_contract.md').read_text(
        encoding='utf-8'
    )

    assert 'GET /health' in contract
    assert 'GET /api/prompt?prompt=<text>' in contract
    assert 'Primary consumer: `services/frontend`' in contract


def test_dx006_is_done_and_next_prompt_advances() -> None:
    roadmap = Path('docs/platform_roadmap.yaml').read_text(encoding='utf-8')
    next_prompt = Path('docs/next_dx_generation_prompt.md').read_text(
        encoding='utf-8'
    )

    assert 'id: DX-005' in roadmap
    assert 'id: DX-006\n  title: Add local integration profile for runtime services' in roadmap
    assert 'status: done' in roadmap.split('id: DX-006', maxsplit=1)[1].split(
        'id: DX-007', maxsplit=1
    )[0]
    assert 'is the next eligible item' in next_prompt
    assert 'DX-006 is marked status: done' in next_prompt


def test_dx006_integration_profile_and_troubleshooting_docs_exist() -> None:
    compose_profile = Path('infra/local/docker-compose.integration.yml').read_text(
        encoding='utf-8'
    )
    troubleshooting = Path(
        'docs/runbooks/local_runtime_integration_troubleshooting.md'
    ).read_text(encoding='utf-8')

    assert 'services:' in compose_profile
    assert 'frontend:' in compose_profile
    assert 'backend:' in compose_profile
    assert 'make integration-up' in troubleshooting
    assert 'BACKEND_API_BASE_URL' in troubleshooting
