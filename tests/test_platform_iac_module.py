from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
IAC_MODULE_PATH = REPO_ROOT / "infra/platform/iac/module.primitives.yaml"
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


def test_iac_module_primitive_contract_declares_reusable_lifecycle() -> None:
    text = IAC_MODULE_PATH.read_text(encoding="utf-8")

    assert "kind: PlatformIaCModule" in text
    assert "primitives:" in text
    for primitive_key in (
        "environment_namespace",
        "network_baseline",
        "secret_reference_bindings",
        "state_backend_contract",
    ):
        assert f"- key: {primitive_key}" in text

    for lifecycle_step in ("- plan", "- apply", "- validate"):
        assert lifecycle_step in text


def test_dev_and_staging_reference_iac_module() -> None:
    for environment_name in ("dev", "staging"):
        modules = _modules_for_environment(environment_name)
        assert "iac-opentofu-or-terraform" in modules


def test_registry_marks_iac_component_scaffolded() -> None:
    lines = REGISTRY_PATH.read_text(encoding="utf-8").splitlines()
    in_iac_entry = False
    status: str | None = None

    for line in lines:
        if line.startswith("  - key: "):
            in_iac_entry = line.strip() == "- key: iac-opentofu-or-terraform"
            continue

        if in_iac_entry and line.startswith("    status: "):
            status = line.split(": ", 1)[1].strip()
            break

    assert status == "scaffolded"
