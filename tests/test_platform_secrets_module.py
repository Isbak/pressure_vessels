from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SECRETS_MODULE_PATH = REPO_ROOT / "infra/platform/secrets/module.boundaries.yaml"
BOOTSTRAP_PATH = REPO_ROOT / "infra/platform/environment.bootstrap.yaml"
REGISTRY_PATH = REPO_ROOT / "docs/platform_runtime_stack_registry.yaml"


def test_secrets_module_boundary_contract_exists_and_is_provider_neutral() -> None:
    text = SECRETS_MODULE_PATH.read_text(encoding="utf-8")

    assert "kind: PlatformSecretsModule" in text
    assert "- vault" in text
    assert "- sops-age" in text
    assert "allowed: false" in text
    assert "provider_specific_secret_values_allowed: false" in text


def test_staging_environment_references_secrets_module() -> None:
    env_name: str | None = None
    in_modules = False
    staging_modules: list[str] = []

    for raw_line in BOOTSTRAP_PATH.read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip()
        if line.startswith("    - name: "):
            env_name = line.split(": ", 1)[1].strip()
            in_modules = False
            continue

        if env_name == "staging" and line.startswith("      modules:"):
            in_modules = True
            continue

        if in_modules and line.startswith("        - "):
            staging_modules.append(line.split("- ", 1)[1].strip())
            continue

        if in_modules and not line.startswith("        "):
            in_modules = False

    assert "secrets-vault-or-sops-age" in staging_modules


def test_registry_marks_secrets_component_deployed() -> None:
    lines = REGISTRY_PATH.read_text(encoding="utf-8").splitlines()
    in_secrets_entry = False
    status: str | None = None

    for line in lines:
        if line.startswith("  - key: "):
            in_secrets_entry = line.strip() == "- key: secrets-vault-or-sops-age"
            continue

        if in_secrets_entry and line.startswith("    status: "):
            status = line.split(": ", 1)[1].strip()
            break

    assert status == "deployed"
