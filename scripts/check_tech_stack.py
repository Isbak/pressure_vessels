#!/usr/bin/env python3
"""Validate runtime stack declarations against in-repo component mappings."""

from __future__ import annotations

import re
from pathlib import Path

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


def _parse_registry(registry_path: Path) -> dict[str, dict[str, str]]:
    lines = registry_path.read_text(encoding="utf-8").splitlines()
    components: dict[str, dict[str, str]] = {}

    current: dict[str, str] | None = None
    for line in lines:
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


def _parse_bootstrap_manifest(manifest_path: Path) -> set[str]:
    modules: set[str] = set()
    for line in manifest_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("        - "):
            modules.add(line.strip()[2:].strip())
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

    registry = _parse_registry(registry_path)
    bootstrap_modules = _parse_bootstrap_manifest(bootstrap_manifest_path)

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
        iac_hcl_exists = bool(
            iac_module_path
            and list((repo_root / iac_module_path).glob("**/*.tf"))
        )
        expected_iac_status = "deployed" if iac_hcl_exists else "scaffolded"
        if iac_status != expected_iac_status:
            failures.append(
                f"{iac_key!r} status must be {expected_iac_status!r} when module_path "
                f"{'contains Terraform/OpenTofu HCL' if iac_hcl_exists else 'contains only contract artifacts'}: {iac_module_path}"
            )

    extra_registry_keys = sorted(set(registry) - all_declared)
    if extra_registry_keys:
        failures.append(
            "Registry has components not declared in docs/tech-stack.md: "
            + ", ".join(extra_registry_keys)
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
