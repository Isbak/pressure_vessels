#!/usr/bin/env python3
"""Validate runtime stack declarations against in-repo component mappings."""

from __future__ import annotations

import importlib
import importlib.util
import json
import re
import subprocess
from pathlib import Path
from typing import Any

COMPONENT_RE = re.compile(r"^- Component: `([^`]+)`", re.MULTILINE)


def _parse_declared_components(tech_stack_text: str) -> tuple[set[str], set[str], set[str]]:
    deployed = _extract_section(tech_stack_text, "### Runtime stack components (deployed)")
    scaffolded = _extract_section(tech_stack_text, "### Runtime stack components (scaffolded)")
    planned = _extract_section(tech_stack_text, "### Runtime stack components (planned)")

    return (
        {value.strip() for value in COMPONENT_RE.findall(deployed)},
        {value.strip() for value in COMPONENT_RE.findall(scaffolded)},
        {value.strip() for value in COMPONENT_RE.findall(planned)},
    )


def _extract_section(text: str, header: str) -> str:
    start = text.find(header)
    if start == -1:
        raise ValueError(f"docs/tech-stack.md is missing '{header}'")

    remainder = text[start + len(header) :]
    next_header_token = "\n### " if header.startswith("### ") else "\n## "
    next_header = remainder.find(next_header_token)
    if next_header == -1:
        return remainder
    return remainder[:next_header]


def _load_yaml(path: Path) -> Any:
    if importlib.util.find_spec("yaml"):
        yaml_module = importlib.import_module("yaml")
        return yaml_module.safe_load(path.read_text(encoding="utf-8"))

    result = subprocess.run(
        [
            "ruby",
            "-e",
            (
                "require 'yaml'; require 'json'; "
                "puts JSON.generate(YAML.safe_load(File.read(ARGV[0]), aliases: true))"
            ),
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def _component_key_line_numbers(registry_path: Path) -> dict[str, int]:
    if not importlib.util.find_spec("yaml"):
        return {}

    yaml_module = importlib.import_module("yaml")
    nodes_module = importlib.import_module("yaml.nodes")
    mapping_node = nodes_module.MappingNode
    scalar_node = nodes_module.ScalarNode
    sequence_node = nodes_module.SequenceNode

    node = yaml_module.compose(registry_path.read_text(encoding="utf-8"))
    if not isinstance(node, mapping_node):
        return {}

    for key_node, value_node in node.value:
        if isinstance(key_node, scalar_node) and key_node.value == "components" and isinstance(
            value_node, sequence_node
        ):
            key_lines: dict[str, int] = {}
            for item in value_node.value:
                if not isinstance(item, mapping_node):
                    continue
                for item_key_node, item_value_node in item.value:
                    if (
                        isinstance(item_key_node, scalar_node)
                        and item_key_node.value == "key"
                        and isinstance(item_value_node, scalar_node)
                    ):
                        key_lines[item_value_node.value] = item_value_node.start_mark.line + 1
            return key_lines
    return {}


def _parse_registry(registry_path: Path) -> dict[str, dict[str, str]]:
    parsed = _load_yaml(registry_path)

    if not isinstance(parsed, dict):
        raise ValueError(f"{registry_path} must parse to a mapping at line 1 key '<root>'")

    components_raw = parsed.get("components")
    if not isinstance(components_raw, list):
        raise ValueError(
            f"{registry_path} is missing list key 'components' at line 1 key 'components'"
        )

    key_lines = _component_key_line_numbers(registry_path)
    components: dict[str, dict[str, str]] = {}
    for index, entry in enumerate(components_raw, start=1):
        if not isinstance(entry, dict):
            raise ValueError(
                f"{registry_path} has non-mapping components[{index}] at line 1 key 'components[{index}]'"
            )

        key = entry.get("key")
        line = key_lines.get(str(key), 1)
        if not isinstance(key, str) or not key.strip():
            raise ValueError(
                f"{registry_path} has invalid component key at line {line} key 'components[{index}].key'"
            )

        normalized_entry: dict[str, str] = {}
        for field, value in entry.items():
            if isinstance(field, str) and isinstance(value, str):
                normalized_entry[field] = value
        components[key] = normalized_entry

    return components


def _parse_bootstrap_manifest(manifest_path: Path) -> set[str]:
    parsed = _load_yaml(manifest_path)
    if not isinstance(parsed, dict):
        return set()

    spec = parsed.get("spec")
    if not isinstance(spec, dict):
        return set()

    environments = spec.get("environments")
    if not isinstance(environments, list):
        return set()

    modules: set[str] = set()
    for environment in environments:
        if not isinstance(environment, dict):
            continue
        declared_modules = environment.get("modules")
        if not isinstance(declared_modules, list):
            continue
        for module in declared_modules:
            if isinstance(module, str):
                modules.add(module)

    return modules


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    tech_stack_path = repo_root / "docs/tech-stack.md"
    registry_path = repo_root / "docs/platform_runtime_stack_registry.yaml"
    bootstrap_manifest_path = repo_root / "infra/platform/environment.bootstrap.yaml"

    tech_stack_text = tech_stack_path.read_text(encoding="utf-8")
    current_components, scaffolded_components, planned_components = _parse_declared_components(
        tech_stack_text
    )

    if not current_components and not scaffolded_components and not planned_components:
        print("No `- Component: ` entries found in docs/tech-stack.md; nothing to validate.")
        return 0

    try:
        registry = _parse_registry(registry_path)
        bootstrap_modules = _parse_bootstrap_manifest(bootstrap_manifest_path)
    except (ValueError, subprocess.CalledProcessError, json.JSONDecodeError) as exc:
        print("Tech stack consistency check failed:")
        print(f"- Failed to parse YAML inputs: {exc}")
        return 1

    failures: list[str] = []
    all_declared = current_components | scaffolded_components | planned_components
    for component in sorted(all_declared):
        if component not in registry:
            failures.append(f"{component!r} is declared in docs/tech-stack.md but missing from registry")
            continue

        entry = registry[component]
        status = entry.get("status")
        module_path = entry.get("module_path")
        if status not in {"deployed", "scaffolded", "planned"}:
            failures.append(f"{component!r} has invalid registry status {status!r}")
            continue

        if component in current_components and status != "deployed":
            failures.append(f"{component!r} is under ## Current but status is {status!r}")
        if component in scaffolded_components and status != "scaffolded":
            failures.append(
                f"{component!r} is under ### Runtime stack components (scaffolded) "
                f"but status is {status!r}"
            )
        if component in planned_components and status != "planned":
            failures.append(f"{component!r} is under ## Planned but status is {status!r}")

        if not module_path:
            failures.append(f"{component!r} is missing module_path in registry")
        elif status == "deployed" and not (repo_root / module_path).exists():
            failures.append(
                f"{component!r} is marked deployed but module_path does not exist: {module_path}"
            )

    iac_key = "iac-opentofu-or-terraform"
    if iac_key in registry:
        iac_entry = registry[iac_key]
        iac_status = iac_entry.get("status")
        iac_module_path = iac_entry.get("module_path")
        iac_hcl_exists = bool(iac_module_path and list((repo_root / iac_module_path).glob("**/*.tf")))
        expected_iac_status = "deployed" if iac_hcl_exists else "scaffolded"
        if iac_status != expected_iac_status:
            failures.append(
                f"{iac_key!r} status must be {expected_iac_status!r} when module_path "
                f"{'contains Terraform/OpenTofu HCL' if iac_hcl_exists else 'contains only contract artifacts'}: {iac_module_path}"
            )

    extra_registry_keys = sorted(set(registry) - all_declared)
    if extra_registry_keys:
        failures.append(
            "Registry has components not declared in docs/tech-stack.md: " + ", ".join(extra_registry_keys)
        )

    for module in sorted(bootstrap_modules):
        if module not in registry:
            failures.append(f"Bootstrap manifest references unknown module: {module}")

    if failures:
        print("Tech stack consistency check failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print(
        "Tech stack consistency check passed for "
        f"{len(current_components)} deployed, {len(scaffolded_components)} scaffolded, "
        f"and {len(planned_components)} planned components."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
