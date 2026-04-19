#!/usr/bin/env python3
"""Generate machine-readable governance checklist evidence for PR consumption."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any


CHECKLIST_ITEMS: list[dict[str, Any]] = [
    {
        "id": "risk_class_selected",
        "label": "Risk class selected (low/medium/high)",
        "source": "pr_metadata",
        "automated": False,
    },
    {
        "id": "agent_author_identified",
        "label": "Agent author identified (Codex / Claude Code / both)",
        "source": "pr_metadata",
        "automated": False,
    },
    {
        "id": "cross_agent_review_completed",
        "label": "Independent cross-agent review completed (for medium/high)",
        "source": "pr_metadata",
        "automated": False,
    },
    {
        "id": "required_tests_executed",
        "label": "Required tests executed and attached",
        "source": "ci_gate:python-tests",
        "automated": True,
    },
    {
        "id": "security_secret_scan_passed",
        "label": "Security/secret scan passed",
        "source": "ci_gate:secret-scan",
        "automated": True,
    },
    {
        "id": "required_human_approvals_obtained",
        "label": "Required human approvals obtained",
        "source": "pr_metadata",
        "automated": False,
    },
    {
        "id": "rollback_plan_included",
        "label": "Rollback plan included (for medium/high)",
        "source": "pr_metadata",
        "automated": False,
    },
]


def main() -> int:
    if len(sys.argv) != 4:
        print(
            "usage: generate_governance_checklist_evidence.py <job_results_json> <governance_gate_report_json> <evidence_out>",
            file=sys.stderr,
        )
        return 2

    job_results = _read_json(Path(sys.argv[1]))
    gate_report = _read_json(Path(sys.argv[2]))
    output_path = Path(sys.argv[3])

    gate_results = {
        str(gate): str(status)
        for gate, status in job_results.items()
        if not str(gate).startswith("_")
    }
    failed_gates = [str(gate) for gate in gate_report.get("failed_gates", [])]

    payload = {
        "schema_version": "GovernanceChecklistEvidence.v1",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "checklist_source": "AGENT_GOVERNANCE.md#10-starter-governance-checklist",
        "ci_evidence": {
            "all_required_gates_passed": len(failed_gates) == 0,
            "failed_gates": failed_gates,
            "applied_exception_ids": [
                str(exception_id)
                for exception_id in gate_report.get("applied_exception_ids", [])
            ],
            "gate_results": gate_results,
        },
        "checklist_items": _build_checklist_items(
            gate_results=gate_results,
        ),
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote governance checklist evidence: {output_path}")
    return 0


def _build_checklist_items(*, gate_results: dict[str, str]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for template in CHECKLIST_ITEMS:
        item = dict(template)
        if template["automated"]:
            gate = str(template["source"]).split(":", maxsplit=1)[1]
            gate_result = gate_results.get(gate, "missing")
            item["status"] = "pass" if gate_result == "success" else "fail"
            item["evidence"] = {"gate": gate, "result": gate_result}
        else:
            item["status"] = "manual"
            item["evidence"] = {
                "instruction": "Populate in PR template checklist and/or PR metadata.",
            }
        items.append(item)
    return items


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    raise SystemExit(main())
