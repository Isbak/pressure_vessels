#!/usr/bin/env python3
"""Suggest a governance risk label from changed-file heuristics.

This script is intentionally advisory-only. It does not enforce merge gates.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import sys


DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[1] / "docs/governance/risk_label_heuristics.v1.json"
CONFIG_OVERRIDE_ENV = "PV_RISK_LABEL_CONFIG"


@dataclass(frozen=True)
class Rule:
    risk: str
    reason: str
    patterns: tuple[str, ...]


@dataclass(frozen=True)
class Heuristics:
    high_risk_rules: tuple[Rule, ...]
    medium_risk_prefixes: tuple[str, ...]
    medium_risk_files: tuple[str, ...]
    low_risk_prefixes: tuple[str, ...]
    low_risk_files: tuple[str, ...]


def main() -> int:
    if len(sys.argv) not in {4, 5}:
        print(
            "usage: suggest_risk_label.py <changed_paths.txt> <risk_suggestion.json> <risk_summary.md> [heuristics_config.json]",
            file=sys.stderr,
        )
        return 2

    changed_paths = _read_paths(Path(sys.argv[1]))
    override_config_arg = Path(sys.argv[4]) if len(sys.argv) == 5 else None
    heuristics = _load_heuristics(override_config_arg)
    suggestion = _suggest(changed_paths, heuristics)

    output_json = Path(sys.argv[2])
    output_md = Path(sys.argv[3])
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)

    output_json.write_text(json.dumps(suggestion, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    output_md.write_text(_markdown_summary(suggestion), encoding="utf-8")

    print(f"Suggested risk: {suggestion['suggested_risk']}")
    print(f"Wrote risk suggestion payload: {output_json}")
    return 0


def _load_heuristics(cli_override: Path | None) -> Heuristics:
    config_path = cli_override
    if config_path is None:
        env_override = Path(value) if (value := os.environ.get(CONFIG_OVERRIDE_ENV)) else None
        config_path = env_override if env_override is not None else DEFAULT_CONFIG_PATH

    payload = json.loads(config_path.read_text(encoding="utf-8"))
    rules = tuple(
        Rule(risk=rule["risk"], reason=rule["reason"], patterns=tuple(rule["patterns"]))
        for rule in payload["high_risk_rules"]
    )
    return Heuristics(
        high_risk_rules=rules,
        medium_risk_prefixes=tuple(payload["medium_risk_prefixes"]),
        medium_risk_files=tuple(payload["medium_risk_files"]),
        low_risk_prefixes=tuple(payload["low_risk_prefixes"]),
        low_risk_files=tuple(payload["low_risk_files"]),
    )


def _read_paths(path: Path) -> list[str]:
    if not path.exists():
        return []
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _suggest(changed_paths: list[str], heuristics: Heuristics) -> dict[str, object]:
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
    for rule in heuristics.high_risk_rules:
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
        if path.startswith(heuristics.medium_risk_prefixes) or path in heuristics.medium_risk_files
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

    low_only = all(path.startswith(heuristics.low_risk_prefixes) or path in heuristics.low_risk_files for path in changed_paths)
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
