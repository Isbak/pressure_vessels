#!/usr/bin/env python3
"""Validate tech stack documentation against declared and imported Python dependencies."""

from __future__ import annotations

import re
import sys
from pathlib import Path

DEPENDENCY_LINE_RE = re.compile(r"^- Dependency: `([^`]+)`", re.MULTILINE)
IMPORT_RE = re.compile(
    r"^\s*(?:from\s+([a-zA-Z_][\w]*)\s+import\b|import\s+([a-zA-Z_][\w]*))",
    re.MULTILINE,
)


def _extract_current_section(text: str) -> str:
    marker = "## Current"
    start = text.find(marker)
    if start == -1:
        raise ValueError("docs/tech-stack.md is missing a '## Current' section")

    remainder = text[start + len(marker) :]
    next_header = remainder.find("\n## ")
    if next_header == -1:
        return remainder
    return remainder[:next_header]


def _declared_dependencies(pyproject_path: Path) -> set[str]:
    content = pyproject_path.read_text(encoding="utf-8")
    match = re.search(r"(?ms)^\[project\].*?^dependencies\s*=\s*\[(.*?)\]", content)
    deps: list[str] = []
    if match:
        deps = re.findall(r'"([^"]+)"', match.group(1))
    normalized: set[str] = set()
    for dep in deps:
        name = re.split(r"[<>=!~\s\[]", dep, maxsplit=1)[0].strip().lower()
        if name:
            normalized.add(name)
    return normalized


def _imported_top_level_modules(src_root: Path) -> set[str]:
    modules: set[str] = set()
    for py_file in src_root.rglob("*.py"):
        text = py_file.read_text(encoding="utf-8")
        for from_mod, import_mod in IMPORT_RE.findall(text):
            module = (from_mod or import_mod).strip()
            if module:
                modules.add(module.lower())
    return modules


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    tech_stack_path = repo_root / "docs/tech-stack.md"
    pyproject_path = repo_root / "pyproject.toml"
    src_root = repo_root / "src"

    current_section = _extract_current_section(tech_stack_path.read_text(encoding="utf-8"))
    current_dependencies = {
        match.strip().lower() for match in DEPENDENCY_LINE_RE.findall(current_section)
    }

    if not current_dependencies:
        print("No `- Dependency: ` entries found in docs/tech-stack.md ## Current; nothing to validate.")
        return 0

    declared_dependencies = _declared_dependencies(pyproject_path)
    imported_modules = _imported_top_level_modules(src_root)

    failures: list[str] = []
    for dependency in sorted(current_dependencies):
        if dependency not in declared_dependencies:
            failures.append(
                f"{dependency!r} is listed in docs/tech-stack.md ## Current but not in pyproject.toml project.dependencies"
            )
        if dependency not in imported_modules:
            failures.append(
                f"{dependency!r} is listed in docs/tech-stack.md ## Current but not imported anywhere under src/"
            )

    if failures:
        print("Tech stack consistency check failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Tech stack consistency check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
