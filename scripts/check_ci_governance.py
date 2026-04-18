#!/usr/bin/env python3
"""Evaluate CI gate results against BL-012 governance policy and persist audit report."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

from pressure_vessels.governance_pipeline import (
    PolicyExceptionApproval,
    build_governance_policy,
    evaluate_governance_gates,
)


def main() -> int:
    if len(sys.argv) != 5:
        print(
            "usage: check_ci_governance.py <policy_json> <exceptions_json> <job_results_json> <report_out>",
            file=sys.stderr,
        )
        return 2

    policy_path = Path(sys.argv[1])
    exceptions_path = Path(sys.argv[2])
    job_results_path = Path(sys.argv[3])
    report_out_path = Path(sys.argv[4])

    policy_payload = _read_json(policy_path)
    exceptions_payload = _read_json(exceptions_path)
    gate_results = _read_json(job_results_path)

    exceptions = [_exception_from_json(item) for item in exceptions_payload.get("exceptions", [])]

    policy = build_governance_policy(
        required_gates=list(policy_payload["required_gates"]),
        artifact_retention_days=int(policy_payload["artifact_retention_days"]),
        approved_exceptions=exceptions,
    )

    report = evaluate_governance_gates(policy=policy, gate_results=gate_results)

    report_out_path.parent.mkdir(parents=True, exist_ok=True)
    report_out_path.write_text(
        json.dumps(report.to_json_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    if report.failed_gates:
        print(f"Governance gate failed for: {', '.join(report.failed_gates)}")
        return 1

    if report.applied_exception_ids:
        print(
            "Governance gates passed with approved exceptions: "
            + ", ".join(report.applied_exception_ids)
        )
    else:
        print("Governance gates passed with no exceptions.")

    return 0


def _exception_from_json(payload: dict[str, Any]) -> PolicyExceptionApproval:
    return PolicyExceptionApproval(
        exception_id=str(payload["exception_id"]),
        gate_id=str(payload["gate_id"]),
        rationale=str(payload["rationale"]),
        approved_by=str(payload["approved_by"]),
        approved_on=str(payload["approved_on"]),
        approval_record_ref=str(payload["approval_record_ref"]),
    )


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    raise SystemExit(main())
