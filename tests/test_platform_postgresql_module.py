from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
POSTGRESQL_MODULE_PATH = REPO_ROOT / "infra/platform/postgresql/module.boundaries.yaml"
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


def test_postgresql_module_boundary_contract_declares_ownership_and_lifecycle() -> None:
    text = POSTGRESQL_MODULE_PATH.read_text(encoding="utf-8")

    assert "kind: PlatformDatastorePostgresqlModule" in text
    assert "schema_ownership:" in text
    assert "lifecycle_boundaries:" in text
    assert "migration_approval_required_from:" in text
    assert "direct_service_access:" in text
    assert "allowed: false" in text


def test_dev_and_staging_reference_postgresql_module() -> None:
    for environment_name in ("dev", "staging"):
        modules = _modules_for_environment(environment_name)
        assert "datastore-postgresql" in modules


def test_registry_marks_postgresql_component_deployed() -> None:
    lines = REGISTRY_PATH.read_text(encoding="utf-8").splitlines()
    in_postgresql_entry = False
    status: str | None = None

    for line in lines:
        if line.startswith("  - key: "):
            in_postgresql_entry = line.strip() == "- key: datastore-postgresql"
            continue

        if in_postgresql_entry and line.startswith("    status: "):
            status = line.split(": ", 1)[1].strip()
            break

    assert status == "deployed"
