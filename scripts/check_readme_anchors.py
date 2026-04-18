#!/usr/bin/env python3
"""Check that README anchor references in the backlog resolve to README headings."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
BACKLOG_README_REF_RE = re.compile(r"README\.md#([a-zA-Z0-9._-]+)")


def _github_anchor_slug(heading: str) -> str:
    value = heading.strip().lower()
    value = re.sub(r"[^\w\- ]", "", value)
    value = value.replace(" ", "-")
    value = re.sub(r"-+", "-", value).strip("-")
    return value


def _extract_readme_anchors(readme_text: str) -> set[str]:
    anchors: set[str] = set()
    seen_counts: dict[str, int] = {}

    for line in readme_text.splitlines():
        match = HEADING_RE.match(line)
        if not match:
            continue

        slug = _github_anchor_slug(match.group(2))
        if not slug:
            continue

        count = seen_counts.get(slug, 0)
        anchor = slug if count == 0 else f"{slug}-{count}"
        seen_counts[slug] = count + 1
        anchors.add(anchor)

    return anchors


def _extract_backlog_readme_refs(backlog_text: str) -> set[str]:
    return {match.group(1).lower() for match in BACKLOG_README_REF_RE.finditer(backlog_text)}


def find_missing_readme_anchor_refs(backlog_path: Path, readme_path: Path) -> list[str]:
    readme_anchors = _extract_readme_anchors(readme_path.read_text(encoding="utf-8"))
    referenced_anchors = _extract_backlog_readme_refs(backlog_path.read_text(encoding="utf-8"))
    return sorted(anchor for anchor in referenced_anchors if anchor not in readme_anchors)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--backlog", type=Path, default=Path("docs/development_backlog.yaml"))
    parser.add_argument("--readme", type=Path, default=Path("README.md"))
    args = parser.parse_args()

    missing = find_missing_readme_anchor_refs(args.backlog, args.readme)
    if missing:
        print("README anchor consistency check failed. Unresolved anchors:")
        for anchor in missing:
            print(f"- README.md#{anchor}")
        return 1

    print("README anchor consistency check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
