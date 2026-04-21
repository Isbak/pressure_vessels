from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
VLLM_MODULE_PATH = REPO_ROOT / "infra/platform/vllm/module.boundaries.yaml"
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


def test_vllm_module_boundary_contract_requires_approved_catalog_and_capacity_envelope() -> None:
    text = VLLM_MODULE_PATH.read_text(encoding="utf-8")

    assert "kind: PlatformLlmServingVllmModule" in text
    assert "endpoint_ownership:" in text
    assert "capacity_envelope:" in text
    assert "access_ownership:" in text
    assert "deployment_targets:" in text
    assert "platform: railway" in text
    assert "providers:" in text
    assert "ollama" in text
    assert "localai" in text
    assert "rollout_status: deployed" in text
    assert "direct_service_access:" in text
    assert "allowed: false" in text
    assert "approved_model_catalog_required: true" in text
    assert "approved_model_catalog_contract: infra/platform/model-catalog/module.boundaries.yaml" in text
    assert "deterministic_inference_defaults_required: true" in text


def test_only_staging_references_vllm_module() -> None:
    assert "llm-serving-vllm" in _modules_for_environment("staging")
    assert "llm-serving-vllm" not in _modules_for_environment("dev")


def test_registry_marks_vllm_component_deployed() -> None:
    lines = REGISTRY_PATH.read_text(encoding="utf-8").splitlines()
    in_vllm_entry = False
    status: str | None = None

    for line in lines:
        if line.startswith("  - key: "):
            in_vllm_entry = line.strip() == "- key: llm-serving-vllm"
            continue

        if in_vllm_entry and line.startswith("    status: "):
            status = line.split(": ", 1)[1].strip()
            break

    assert status == "deployed"
