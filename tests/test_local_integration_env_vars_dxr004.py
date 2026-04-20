from __future__ import annotations

from pathlib import Path
import re


VAR_WITH_DEFAULT_PATTERN = re.compile(r"\$\{([A-Z0-9_]+):-([^}]+)\}")
ENV_ENTRY_PATTERN = re.compile(r"^([A-Z0-9_]+)=(.*)$")


def _compose_variable_defaults() -> dict[str, str]:
    compose_text = Path('infra/local/docker-compose.integration.yml').read_text(
        encoding='utf-8'
    )
    return {name: default for name, default in VAR_WITH_DEFAULT_PATTERN.findall(compose_text)}


def _env_example_entries() -> dict[str, str]:
    env_lines = Path('.env.example').read_text(encoding='utf-8').splitlines()
    entries: dict[str, str] = {}

    for line in env_lines:
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue
        match = ENV_ENTRY_PATTERN.match(stripped)
        assert match, f'Invalid .env.example entry format: {line}'
        entries[match.group(1)] = match.group(2)

    return entries


def test_dxr004_compose_variables_match_env_example_defaults() -> None:
    compose_defaults = _compose_variable_defaults()
    env_defaults = _env_example_entries()

    assert compose_defaults == env_defaults
    assert set(compose_defaults) == {
        'FRONTEND_PORT',
        'BACKEND_PORT',
        'BACKEND_HOST',
        'BACKEND_API_BASE_URL',
    }
