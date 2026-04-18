from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
REDIS_MODULE_PATH = REPO_ROOT / "infra/platform/redis/module.boundaries.yaml"
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


def test_redis_module_boundary_contract_declares_queue_cache_and_lifecycle() -> None:
    text = REDIS_MODULE_PATH.read_text(encoding="utf-8")

    assert "kind: PlatformCacheRedisModule" in text
    assert "cache_namespaces:" in text
    assert "queue_streams:" in text
    assert "lifecycle_boundaries:" in text
    assert "direct_service_access:" in text
    assert "allowed: false" in text


def test_dev_and_staging_reference_redis_module() -> None:
    for environment_name in ("dev", "staging"):
        modules = _modules_for_environment(environment_name)
        assert "cache-redis" in modules


def test_registry_marks_redis_component_deployed() -> None:
    lines = REGISTRY_PATH.read_text(encoding="utf-8").splitlines()
    in_redis_entry = False
    status: str | None = None

    for line in lines:
        if line.startswith("  - key: "):
            in_redis_entry = line.strip() == "- key: cache-redis"
            continue

        if in_redis_entry and line.startswith("    status: "):
            status = line.split(": ", 1)[1].strip()
            break

    assert status == "deployed"
