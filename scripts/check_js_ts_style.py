#!/usr/bin/env python
"""Baseline style checks for JS/TS files without external Node linters."""

from __future__ import annotations

from pathlib import Path

ROOTS = [Path("services/frontend"), Path("services/backend")]
EXTENSIONS = {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"}
SKIP_PARTS = {"node_modules", "dist", ".next"}


def iter_files() -> list[Path]:
    files: list[Path] = []
    for root in ROOTS:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in EXTENSIONS:
                continue
            if SKIP_PARTS.intersection(path.parts):
                continue
            files.append(path)
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
        print("JS/TS style baseline check failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"JS/TS style baseline check passed for {len(files)} files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
