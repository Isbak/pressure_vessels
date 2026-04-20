from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TEMPORAL_MODULE_PATH = REPO_ROOT / "infra/platform/temporal/module.boundaries.yaml"
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


def test_temporal_module_boundary_contract_declares_namespace_queue_and_worker_ownership() -> None:
    text = TEMPORAL_MODULE_PATH.read_text(encoding="utf-8")

    assert "kind: PlatformWorkflowTemporalModule" in text
    assert "workflow_ownership:" in text
    assert "namespaces:" in text
    assert "task_queues:" in text
    assert "workers:" in text
    assert "lifecycle_boundaries:" in text
    assert "direct_namespace_mutation:" in text
    assert "allowed: false" in text


def test_only_staging_references_temporal_module() -> None:
    assert "workflow-temporal" in _modules_for_environment("staging")
    assert "workflow-temporal" not in _modules_for_environment("dev")


def test_registry_marks_temporal_component_scaffolded() -> None:
    lines = REGISTRY_PATH.read_text(encoding="utf-8").splitlines()
    in_temporal_entry = False
    status: str | None = None

    for line in lines:
        if line.startswith("  - key: "):
            in_temporal_entry = line.strip() == "- key: workflow-temporal"
            continue

        if in_temporal_entry and line.startswith("    status: "):
            status = line.split(": ", 1)[1].strip()
            break

    assert status == "scaffolded"
