#!/usr/bin/env python3
"""Suggest a governance risk label from changed-file heuristics.

This script is intentionally advisory-only. It does not enforce merge gates.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import sys


@dataclass(frozen=True)
class Rule:
    risk: str
    reason: str
    patterns: tuple[str, ...]


HIGH_RISK_RULES: tuple[Rule, ...] = (
    Rule(
        risk="high",
        reason="Compliance calculation logic changed.",
        patterns=(
            "src/pressure_vessels/calculation_pipeline.py",
            "src/pressure_vessels/compliance_pipeline.py",
        ),
    ),
    Rule(
        risk="high",
        reason="CI workflow or governance policy controls changed.",
        patterns=(
            ".github/workflows/",
            ".github/governance/",
            "docs/governance/",
        ),
    ),
    Rule(
        risk="high",
        reason="Infrastructure-as-code primitives changed (potential permission/runtime impact).",
        patterns=(
            "infra/platform/iac/",
        ),
    ),
)

MEDIUM_RISK_PREFIXES: tuple[str, ...] = (
    "src/",
    "services/",
    "scripts/",
    "tests/",
)

MEDIUM_RISK_FILES: tuple[str, ...] = (
    "pyproject.toml",
    "Makefile",
    ".pre-commit-config.yaml",
)

LOW_RISK_PREFIXES: tuple[str, ...] = (
    "docs/",
    "artifacts/",
)

LOW_RISK_FILES: tuple[str, ...] = (
    "README.md",
    "LICENSE",
    "AGENT_GOVERNANCE.md",
)


def main() -> int:
    if len(sys.argv) != 4:
        print(
            "usage: suggest_risk_label.py <changed_paths.txt> <risk_suggestion.json> <risk_summary.md>",
            file=sys.stderr,
        )
        return 2

    changed_paths = _read_paths(Path(sys.argv[1]))
    suggestion = _suggest(changed_paths)

    output_json = Path(sys.argv[2])
    output_md = Path(sys.argv[3])
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)

    output_json.write_text(json.dumps(suggestion, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    output_md.write_text(_markdown_summary(suggestion), encoding="utf-8")

    print(f"Suggested risk: {suggestion['suggested_risk']}")
    print(f"Wrote risk suggestion payload: {output_json}")
    return 0


def _read_paths(path: Path) -> list[str]:
    if not path.exists():
        return []
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _suggest(changed_paths: list[str]) -> dict[str, object]:
    if not changed_paths:
        return {
            "schema_version": "RiskLabelSuggestion.v1",
            "suggested_risk": "low",
            "confidence": "low",
            "advisory_only": True,
            "rationale": ["No changed files were detected from the workflow diff context."],
            "matched_paths": [],
            "changed_paths": [],
        }

    high_matches: list[dict[str, object]] = []
    for rule in HIGH_RISK_RULES:
        matched = [path for path in changed_paths if any(path.startswith(pattern) for pattern in rule.patterns)]
        if matched:
            high_matches.append({"reason": rule.reason, "paths": sorted(matched)})

    if high_matches:
        return {
            "schema_version": "RiskLabelSuggestion.v1",
            "suggested_risk": "high",
            "confidence": "medium",
            "advisory_only": True,
            "rationale": [match["reason"] for match in high_matches],
            "matched_paths": high_matches,
            "changed_paths": changed_paths,
        }

    medium_paths = [
        path
        for path in changed_paths
        if path.startswith(MEDIUM_RISK_PREFIXES) or path in MEDIUM_RISK_FILES
    ]
    if medium_paths:
        return {
            "schema_version": "RiskLabelSuggestion.v1",
            "suggested_risk": "medium",
            "confidence": "medium",
            "advisory_only": True,
            "rationale": [
                "Application/test/tooling code or developer automation changed.",
            ],
            "matched_paths": [{"reason": "Medium-risk file classes", "paths": sorted(medium_paths)}],
            "changed_paths": changed_paths,
        }

    low_only = all(path.startswith(LOW_RISK_PREFIXES) or path in LOW_RISK_FILES for path in changed_paths)
    if low_only:
        return {
            "schema_version": "RiskLabelSuggestion.v1",
            "suggested_risk": "low",
            "confidence": "high",
            "advisory_only": True,
            "rationale": ["Changes are documentation/artifact metadata only."],
            "matched_paths": [{"reason": "Low-risk file classes", "paths": sorted(changed_paths)}],
            "changed_paths": changed_paths,
        }

    return {
        "schema_version": "RiskLabelSuggestion.v1",
        "suggested_risk": "medium",
        "confidence": "low",
        "advisory_only": True,
        "rationale": [
            "Changed files do not match explicit high-risk rules, but include non-doc paths.",
        ],
        "matched_paths": [{"reason": "Fallback medium classification", "paths": sorted(changed_paths)}],
        "changed_paths": changed_paths,
    }


def _markdown_summary(payload: dict[str, object]) -> str:
    lines = [
        "## Risk Label Suggestion (Advisory)",
        "",
        f"- Suggested risk: **{payload['suggested_risk']}**",
        f"- Confidence: **{payload['confidence']}**",
        "- Authority: advisory only (human reviewers assign final PR risk class).",
        "",
        "### Rationale",
    ]

    for reason in payload["rationale"]:
        lines.append(f"- {reason}")

    lines.append("")
    lines.append("### Matched paths")
    for match in payload["matched_paths"]:
        lines.append(f"- {match['reason']}")
        for path in match["paths"]:
            lines.append(f"  - `{path}`")

    lines.append("")
    lines.append("Artifact: `artifacts/ci/RiskLabelSuggestion.v1.json`")
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
