from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = REPO_ROOT / "docs/platform_runtime_stack_registry.yaml"
BOOTSTRAP_PATH = REPO_ROOT / "infra/platform/environment.bootstrap.yaml"

EXPECTED_BOUNDARY_FILENAMES = ("module.boundaries.yaml", "module.primitives.yaml")


def _parse_registry() -> dict[str, dict[str, str]]:
    components: dict[str, dict[str, str]] = {}
    current: dict[str, str] | None = None

    for line in REGISTRY_PATH.read_text(encoding="utf-8").splitlines():
        if line.startswith("  - key: "):
            if current is not None and "key" in current:
                components[current["key"]] = current
            current = {"key": line.split(": ", 1)[1].strip()}
            continue

        if current is None:
            continue

        if line.startswith("    ") and ": " in line:
            field, raw_value = line.strip().split(": ", 1)
            current[field] = raw_value.strip()

    if current is not None and "key" in current:
        components[current["key"]] = current

    return components


def test_platform_bootstrap_manifest_exists() -> None:
    assert BOOTSTRAP_PATH.is_file(), f"Missing bootstrap manifest: {BOOTSTRAP_PATH}"


def test_every_deployed_registry_component_has_module_directory() -> None:
    registry = _parse_registry()

    for key, entry in sorted(registry.items()):
        if entry.get("status") != "deployed":
            continue

        module_path = entry.get("module_path")
        assert module_path, f"Registry entry {key!r} is deployed but has no module_path"

        module_dir = REPO_ROOT / module_path
        assert module_dir.is_dir(), (
            f"Registry entry {key!r} is deployed but module_path "
            f"{module_path!r} is not a directory"
        )


def test_every_deployed_infra_platform_component_has_boundary_contract_file() -> None:
    registry = _parse_registry()

    for key, entry in sorted(registry.items()):
        if entry.get("status") != "deployed":
            continue

        module_path = entry.get("module_path", "")
        if not module_path.startswith("infra/platform/"):
            continue

        module_dir = REPO_ROOT / module_path
        present = [
            filename
            for filename in EXPECTED_BOUNDARY_FILENAMES
            if (module_dir / filename).is_file()
        ]
        assert present, (
            f"Registry entry {key!r} at {module_path!r} is missing a boundary "
            f"contract file (expected one of: {', '.join(EXPECTED_BOUNDARY_FILENAMES)})"
        )


def test_bootstrap_modules_all_registered_as_runnable_or_scaffolded() -> None:
    registry = _parse_registry()
    declared_modules: set[str] = set()

    for raw_line in BOOTSTRAP_PATH.read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip()
        if line.startswith("        - "):
            declared_modules.add(line.split("- ", 1)[1].strip())

    for module_key in sorted(declared_modules):
        assert module_key in registry, (
            f"Bootstrap manifest references {module_key!r} but registry has no entry"
        )
        assert registry[module_key].get("status") in {"deployed", "scaffolded"}, (
            f"Bootstrap manifest references {module_key!r} but registry status is "
            f"{registry[module_key].get('status')!r}"
        )
