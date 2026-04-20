from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
KEYCLOAK_MODULE_PATH = REPO_ROOT / "infra/platform/keycloak/module.boundaries.yaml"
BOOTSTRAP_PATH = REPO_ROOT / "infra/platform/environment.bootstrap.yaml"
REGISTRY_PATH = REPO_ROOT / "docs/platform_runtime_stack_registry.yaml"


def _modules_for_environment(environment_name: str) -> list[str]:
    env_name: str | None = None
    in_modules = False
    modules: list[str] = []

    for raw_line in BOOTSTRAP_PATH.read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip()
        if line.startswith("    - name: "):
            env_name = line.split(": ", 1)[1].strip()
            in_modules = False
            continue

        if env_name == environment_name and line.startswith("      modules:"):
            in_modules = True
            continue

        if in_modules and line.startswith("        - "):
            modules.append(line.split("- ", 1)[1].strip())
            continue

        if in_modules and not line.startswith("        "):
            in_modules = False

    return modules


def test_keycloak_module_boundary_contract_declares_realm_client_and_role_ownership() -> None:
    text = KEYCLOAK_MODULE_PATH.read_text(encoding="utf-8")

    assert "kind: PlatformIdentityModule" in text
    assert "realm_ownership:" in text
    assert "client_ownership:" in text
    assert "role_ownership:" in text
    assert "lifecycle_boundaries:" in text
    assert "direct_console_mutation:" in text
    assert "allowed: false" in text
    assert "break_glass_access:" in text


def test_dev_and_staging_reference_keycloak_module() -> None:
    for environment_name in ("dev", "staging"):
        modules = _modules_for_environment(environment_name)
        assert "auth-keycloak" in modules


def test_registry_marks_keycloak_component_scaffolded() -> None:
    lines = REGISTRY_PATH.read_text(encoding="utf-8").splitlines()
    in_keycloak_entry = False
    status: str | None = None

    for line in lines:
        if line.startswith("  - key: "):
            in_keycloak_entry = line.strip() == "- key: auth-keycloak"
            continue

        if in_keycloak_entry and line.startswith("    status: "):
            status = line.split(": ", 1)[1].strip()
            break

    assert status == "scaffolded"
