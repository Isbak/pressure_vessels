"""Reusable governance check entry points for CI and cross-project adoption."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
from fnmatch import fnmatch
import json
from pathlib import Path
import re
from typing import Any

from pressure_vessels.governance_pipeline import (
    PolicyExceptionApproval,
    build_governance_policy,
    evaluate_governance_gates,
)


@dataclass(frozen=True)
class PolicyException:
    id: str
    gate: str
    scope: list[str]
    justification: str
    approver: str
    approved_at: str
    expires_at: str
    linked_backlog_id: str


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


def check_ci_governance_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="pv-check-ci-governance",
        description="Evaluate CI gate results against governance policy and emit a report.",
    )
    parser.add_argument("policy_json", type=Path)
    parser.add_argument("exceptions_json", type=Path)
    parser.add_argument("job_results_json", type=Path)
    parser.add_argument("report_out", type=Path)
    parser.add_argument(
        "--exceptions-schema",
        dest="exceptions_schema_json",
        type=Path,
        required=True,
        help="Path to policy exceptions schema JSON (required; no repository path is assumed).",
    )
    args = parser.parse_args(argv)

    policy_payload = _read_json(args.policy_json)
    exceptions_payload = _read_json(args.exceptions_json)
    gate_results_payload = _read_json(args.job_results_json)
    schema_payload = _read_json(args.exceptions_schema_json)

    _validate_exceptions_document(exceptions_payload, schema_payload)

    all_exceptions = [_exception_from_json(item) for item in exceptions_payload.get("exceptions", [])]
    changed_paths = _extract_changed_paths(gate_results_payload)
    gate_results = _extract_gate_results(gate_results_payload)
    _validate_control_drift(
        required_gates=list(policy_payload["required_gates"]),
        gate_results=gate_results,
    )

    approved_exceptions = _eligible_exceptions(
        all_exceptions=all_exceptions,
        gate_results=gate_results,
        changed_paths=changed_paths,
        now_utc=datetime.now(timezone.utc),
    )

    policy = build_governance_policy(
        required_gates=list(policy_payload["required_gates"]),
        artifact_retention_days=int(policy_payload["artifact_retention_days"]),
        approved_exceptions=approved_exceptions,
    )

    report = evaluate_governance_gates(policy=policy, gate_results=gate_results)

    args.report_out.parent.mkdir(parents=True, exist_ok=True)
    args.report_out.write_text(
        json.dumps(report.to_json_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    if report.failed_gates:
        print(f"Governance gate failed for: {', '.join(report.failed_gates)}")
        return 1

    if report.applied_exception_ids:
        exception_index = {item.id: item for item in all_exceptions}
        for exception_id in sorted(report.applied_exception_ids):
            matched = exception_index[exception_id]
            print(
                f"Exception applied: gate={matched.gate} id={matched.id} approver={matched.approver}"
            )
        print(
            "Governance gates passed with approved exceptions: "
            + ", ".join(report.applied_exception_ids)
        )
    else:
        print("Governance gates passed with no exceptions.")

    return 0


def generate_governance_checklist_evidence_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="pv-generate-governance-checklist-evidence",
        description="Generate machine-readable governance checklist evidence for PR consumption.",
    )
    parser.add_argument("job_results_json", type=Path)
    parser.add_argument("governance_gate_report_json", type=Path)
    parser.add_argument("evidence_out", type=Path)
    args = parser.parse_args(argv)

    job_results = _read_json(args.job_results_json)
    gate_report = _read_json(args.governance_gate_report_json)

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

    args.evidence_out.parent.mkdir(parents=True, exist_ok=True)
    args.evidence_out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote governance checklist evidence: {args.evidence_out}")
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


def _validate_exceptions_document(document: dict[str, Any], schema: dict[str, Any]) -> None:
    if not isinstance(document, dict):
        raise ValueError("Policy exceptions document validation failed: document must be an object.")

    root_required = set(schema.get("required", []))
    missing_root = sorted(field for field in root_required if field not in document)
    if missing_root:
        raise ValueError(
            "Policy exceptions document validation failed: missing required root fields: "
            + ", ".join(missing_root)
        )

    allowed_root = set(schema.get("properties", {}).keys())
    unexpected_root = sorted(key for key in document if key not in allowed_root)
    if unexpected_root:
        raise ValueError(
            "Policy exceptions document validation failed: unexpected root fields: "
            + ", ".join(unexpected_root)
        )

    if document.get("version") != schema["properties"]["version"]["const"]:
        raise ValueError("Policy exceptions document validation failed: version must equal 1.")

    exceptions = document.get("exceptions")
    if not isinstance(exceptions, list):
        raise ValueError("Policy exceptions document validation failed: exceptions must be a list.")

    item_schema = schema["properties"]["exceptions"]["items"]
    required_fields = set(item_schema.get("required", []))
    allowed_fields = set(item_schema.get("properties", {}).keys())

    for index, item in enumerate(exceptions):
        if not isinstance(item, dict):
            raise ValueError(f"Policy exceptions document validation failed: exceptions[{index}] must be an object.")

        missing_fields = sorted(field for field in required_fields if field not in item)
        if missing_fields:
            raise ValueError(
                f"Policy exceptions document validation failed: exceptions[{index}] missing required fields: "
                + ", ".join(missing_fields)
            )

        unexpected_fields = sorted(field for field in item if field not in allowed_fields)
        if unexpected_fields:
            raise ValueError(
                f"Policy exceptions document validation failed: exceptions[{index}] has unexpected fields: "
                + ", ".join(unexpected_fields)
            )

        _validate_exception_item(index=index, item=item)


def _validate_exception_item(*, index: int, item: dict[str, Any]) -> None:
    string_fields = ["id", "gate", "justification", "approver", "approved_at", "expires_at", "linked_backlog_id"]
    for field in string_fields:
        value = item[field]
        if not isinstance(value, str) or not value.strip():
            raise ValueError(
                f"Policy exceptions document validation failed: exceptions[{index}].{field} must be a non-empty string."
            )

    if not re.fullmatch(r"@[A-Za-z0-9-]+", item["approver"]):
        raise ValueError(
            f"Policy exceptions document validation failed: exceptions[{index}].approver must be a GitHub handle."
        )

    scope = item["scope"]
    if not isinstance(scope, list) or not scope:
        raise ValueError(
            f"Policy exceptions document validation failed: exceptions[{index}].scope must be a non-empty list."
        )
    if any(not isinstance(pattern, str) or not pattern.strip() for pattern in scope):
        raise ValueError(
            f"Policy exceptions document validation failed: exceptions[{index}].scope entries must be non-empty strings."
        )

    try:
        approved_at = _parse_iso8601(item["approved_at"])
        expires_at = _parse_iso8601(item["expires_at"])
    except ValueError as error:
        raise ValueError(
            f"Policy exceptions document validation failed: exceptions[{index}] timestamps must be ISO-8601."
        ) from error

    if approved_at == expires_at:
        raise ValueError(
            f"Policy exceptions document validation failed: exceptions[{index}] approved_at must not equal expires_at."
        )
    if approved_at > expires_at:
        raise ValueError(
            f"Policy exceptions document validation failed: exceptions[{index}] approved_at must be earlier than expires_at."
        )


def _eligible_exceptions(
    *,
    all_exceptions: list[PolicyException],
    gate_results: dict[str, str],
    changed_paths: list[str],
    now_utc: datetime,
) -> list[PolicyExceptionApproval]:
    eligible: list[PolicyExceptionApproval] = []

    for exception in all_exceptions:
        gate_result = gate_results.get(exception.gate, "missing")
        if gate_result == "success":
            continue
        if _is_expired(exception=exception, now_utc=now_utc):
            continue
        if not _scope_matches(scope_patterns=exception.scope, changed_paths=changed_paths):
            continue

        eligible.append(
            PolicyExceptionApproval(
                exception_id=exception.id,
                gate_id=exception.gate,
                rationale=exception.justification,
                approved_by=exception.approver,
                approved_on=_parse_iso8601(exception.approved_at).date().isoformat(),
                approval_record_ref=exception.linked_backlog_id,
            )
        )

    return eligible


def _is_expired(*, exception: PolicyException, now_utc: datetime) -> bool:
    return _parse_iso8601(exception.expires_at) < now_utc


def _scope_matches(*, scope_patterns: list[str], changed_paths: list[str]) -> bool:
    universal_patterns = {"*", "**", "**/*"}
    if not changed_paths:
        return any(pattern in universal_patterns for pattern in scope_patterns)

    return any(fnmatch(path, pattern) for pattern in scope_patterns for path in changed_paths)


def _extract_changed_paths(gate_results_payload: dict[str, Any]) -> list[str]:
    changed_paths = gate_results_payload.get("_changed_paths", [])
    if not isinstance(changed_paths, list):
        raise ValueError("Gate results payload _changed_paths must be a list when present.")
    return [str(path) for path in changed_paths]


def _extract_gate_results(gate_results_payload: dict[str, Any]) -> dict[str, str]:
    return {
        str(gate): str(result)
        for gate, result in gate_results_payload.items()
        if not str(gate).startswith("_")
    }


def _validate_control_drift(*, required_gates: list[str], gate_results: dict[str, str]) -> None:
    required = set(required_gates)
    observed = set(gate_results.keys())
    missing = sorted(required - observed)
    unmanaged = sorted(observed - required)

    if not missing and not unmanaged:
        return

    details: list[str] = []
    if missing:
        details.append(f"missing required gates in CI results: {', '.join(missing)}")
    if unmanaged:
        details.append(f"unmanaged CI gates absent from policy: {', '.join(unmanaged)}")

    raise ValueError("CI governance control drift detected: " + "; ".join(details))


def _exception_from_json(payload: dict[str, Any]) -> PolicyException:
    return PolicyException(
        id=str(payload["id"]),
        gate=str(payload["gate"]),
        scope=[str(pattern) for pattern in payload["scope"]],
        justification=str(payload["justification"]),
        approver=str(payload["approver"]),
        approved_at=str(payload["approved_at"]),
        expires_at=str(payload["expires_at"]),
        linked_backlog_id=str(payload["linked_backlog_id"]),
    )


def _parse_iso8601(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
