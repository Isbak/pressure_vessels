from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
NEO4J_MODULE_PATH = REPO_ROOT / "infra/platform/neo4j/module.boundaries.yaml"
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


def test_neo4j_module_boundary_contract_declares_schema_and_access_ownership() -> None:
    text = NEO4J_MODULE_PATH.read_text(encoding="utf-8")

    assert "kind: PlatformKnowledgeGraphNeo4jModule" in text
    assert "database_ownership:" in text
    assert "graph_schema:" in text
    assert "node_labels:" in text
    assert "relationship_types:" in text
    assert "access_ownership:" in text
    assert "direct_service_access:" in text
    assert "allowed: false" in text
    assert "schema_versioning_required: true" in text


def test_only_staging_references_neo4j_module() -> None:
    assert "graph-neo4j" in _modules_for_environment("staging")
    assert "graph-neo4j" not in _modules_for_environment("dev")


def test_registry_marks_neo4j_component_scaffolded() -> None:
    lines = REGISTRY_PATH.read_text(encoding="utf-8").splitlines()
    in_neo4j_entry = False
    status: str | None = None

    for line in lines:
        if line.startswith("  - key: "):
            in_neo4j_entry = line.strip() == "- key: graph-neo4j"
            continue

        if in_neo4j_entry and line.startswith("    status: "):
            status = line.split(": ", 1)[1].strip()
            break

    assert status == "scaffolded"
