from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODEL_CATALOG_MODULE_PATH = REPO_ROOT / "infra/platform/model-catalog/module.boundaries.yaml"
REGISTRY_PATH = REPO_ROOT / "docs/platform_runtime_stack_registry.yaml"


def test_model_catalog_module_boundary_contract_declares_approval_and_versioning_controls() -> None:
    text = MODEL_CATALOG_MODULE_PATH.read_text(encoding="utf-8")

    assert "kind: PlatformModelCatalogModule" in text
    assert "approved_model_families:" in text
    assert "versioning_policy:" in text
    assert "access_ownership:" in text
    assert "direct_model_artifact_publish:" in text
    assert "allowed: false" in text
    assert "consumption_contracts:" in text
    assert "infra/platform/vllm" in text


def test_registry_marks_model_catalog_component_deployed() -> None:
    lines = REGISTRY_PATH.read_text(encoding="utf-8").splitlines()
    in_model_catalog_entry = False
    status: str | None = None
    module_path: str | None = None

    for line in lines:
        if line.startswith("  - key: "):
            in_model_catalog_entry = line.strip() == "- key: models-llama-mistral-qwen"
            continue

        if in_model_catalog_entry and line.startswith("    status: "):
            status = line.split(": ", 1)[1].strip()
            continue

        if in_model_catalog_entry and line.startswith("    module_path: "):
            module_path = line.split(": ", 1)[1].strip()

    assert status == "deployed"
    assert module_path == "infra/platform/model-catalog"
