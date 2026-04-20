#!/usr/bin/env python3
"""Evaluate CI gate results against BL-012 governance policy and persist audit report."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from fnmatch import fnmatch
import json
from pathlib import Path
import sys
from typing import Any
import re

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
    gate_results_payload = _read_json(job_results_path)

    schema_path = Path(__file__).resolve().parents[1] / "docs/governance/policy_exceptions_schema.v1.json"
    schema_payload = _read_json(schema_path)
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

    report_out_path.parent.mkdir(parents=True, exist_ok=True)
    report_out_path.write_text(
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


if __name__ == "__main__":
    raise SystemExit(main())
