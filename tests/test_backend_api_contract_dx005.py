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


def test_dx005_is_done_and_next_prompt_points_to_dx006() -> None:
    roadmap = Path('docs/platform_roadmap.yaml').read_text(encoding='utf-8')
    next_prompt = Path('docs/next_dx_generation_prompt.md').read_text(
        encoding='utf-8'
    )

    assert 'id: DX-005' in roadmap
    assert 'id: DX-005\n  title: Implement minimal runnable backend API path' in roadmap
    assert 'status: done' in roadmap.split('id: DX-005', maxsplit=1)[1].split(
        'id: DX-006', maxsplit=1
    )[0]
    assert 'DX-006 is the next eligible item' in next_prompt
