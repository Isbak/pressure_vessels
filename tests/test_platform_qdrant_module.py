from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
QDRANT_MODULE_PATH = REPO_ROOT / "infra/platform/qdrant/module.boundaries.yaml"
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


def test_qdrant_module_boundary_contract_declares_collection_and_indexing_policy() -> None:
    text = QDRANT_MODULE_PATH.read_text(encoding="utf-8")

    assert "kind: PlatformVectorRetrievalQdrantModule" in text
    assert "collection_ownership:" in text
    assert "indexing_policy:" in text
    assert "access_ownership:" in text
    assert "direct_service_access:" in text
    assert "allowed: false" in text
    assert "deterministic_embedding_version_required: true" in text


def test_only_staging_references_qdrant_module() -> None:
    assert "retrieval-qdrant" in _modules_for_environment("staging")
    assert "retrieval-qdrant" not in _modules_for_environment("dev")


def test_registry_marks_qdrant_component_deployed() -> None:
    lines = REGISTRY_PATH.read_text(encoding="utf-8").splitlines()
    in_qdrant_entry = False
    status: str | None = None

    for line in lines:
        if line.startswith("  - key: "):
            in_qdrant_entry = line.strip() == "- key: retrieval-qdrant"
            continue

        if in_qdrant_entry and line.startswith("    status: "):
            status = line.split(": ", 1)[1].strip()
            break

    assert status == "deployed"
