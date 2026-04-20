#!/usr/bin/env python3
"""Baseline style checks for repository Python files."""

from __future__ import annotations

from pathlib import Path

ROOTS = [Path("src"), Path("tests"), Path("scripts")]


def iter_files() -> list[Path]:
    files: list[Path] = []
    for root in ROOTS:
        if not root.exists():
            continue
        files.extend(path for path in root.rglob("*.py") if path.is_file())
    return sorted(files)


def check_file(path: Path) -> list[str]:
    errors: list[str] = []
    lines = path.read_text(encoding="utf-8").splitlines()
    for line_number, line in enumerate(lines, start=1):
        if "\t" in line:
            errors.append(f"{path}:{line_number}: tab character is not allowed")
        if line.rstrip(" ") != line:
            errors.append(f"{path}:{line_number}: trailing whitespace")
    return errors


def main() -> int:
    files = iter_files()
    errors: list[str] = []
    for file in files:
        errors.extend(check_file(file))

    if errors:
        print("Python style baseline check failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Python style baseline check passed for {len(files)} files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
