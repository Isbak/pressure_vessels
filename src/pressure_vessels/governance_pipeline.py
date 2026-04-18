"""Deterministic governance gate evaluation for CI policy enforcement (BL-012)."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from typing import Any


GOVERNANCE_POLICY_SCHEMA_VERSION = "CIGovernancePolicy.v1"
GOVERNANCE_GATE_REPORT_SCHEMA_VERSION = "GovernanceGateReport.v1"


@dataclass(frozen=True)
class PolicyExceptionApproval:
    exception_id: str
    gate_id: str
    rationale: str
    approved_by: str
    approved_on: str
    approval_record_ref: str

    def to_json_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class GovernancePolicy:
    schema_version: str
    artifact_retention_days: int
    required_gates: list[str]
    approved_exceptions: list[PolicyExceptionApproval]


@dataclass(frozen=True)
class GovernanceGateReport:
    schema_version: str
    policy_schema_version: str
    artifact_retention_days: int
    gate_status: dict[str, str]
    failed_gates: list[str]
    applied_exception_ids: list[str]

    def to_json_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_governance_policy(
    *,
    required_gates: list[str],
    artifact_retention_days: int,
    approved_exceptions: list[PolicyExceptionApproval],
) -> GovernancePolicy:
    """Construct and validate a CI governance policy payload."""
    if artifact_retention_days < 1:
        raise ValueError("BL-012 governance policy failed: artifact_retention_days must be >= 1.")
    if not required_gates:
        raise ValueError("BL-012 governance policy failed: at least one required gate is needed.")

    deduplicated = sorted(set(required_gates))
    if len(deduplicated) != len(required_gates):
        raise ValueError("BL-012 governance policy failed: duplicate required gate ids are not allowed.")

    _validate_exceptions(approved_exceptions)
    return GovernancePolicy(
        schema_version=GOVERNANCE_POLICY_SCHEMA_VERSION,
        artifact_retention_days=artifact_retention_days,
        required_gates=deduplicated,
        approved_exceptions=sorted(approved_exceptions, key=lambda item: item.exception_id),
    )


def evaluate_governance_gates(
    *,
    policy: GovernancePolicy,
    gate_results: dict[str, str],
) -> GovernanceGateReport:
    """Evaluate CI gate results and apply only explicitly approved policy exceptions."""
    exceptions_by_gate = _index_exceptions_by_gate(policy.approved_exceptions)

    gate_status: dict[str, str] = {}
    failed_gates: list[str] = []
    applied_exception_ids: list[str] = []

    for gate_id in policy.required_gates:
        result = gate_results.get(gate_id, "missing")
        if result == "success":
            gate_status[gate_id] = "pass"
            continue

        approved_exception = exceptions_by_gate.get(gate_id)
        if approved_exception is not None:
            gate_status[gate_id] = "exception-approved"
            applied_exception_ids.append(approved_exception.exception_id)
            continue

        gate_status[gate_id] = f"fail:{result}"
        failed_gates.append(gate_id)

    return GovernanceGateReport(
        schema_version=GOVERNANCE_GATE_REPORT_SCHEMA_VERSION,
        policy_schema_version=policy.schema_version,
        artifact_retention_days=policy.artifact_retention_days,
        gate_status=gate_status,
        failed_gates=sorted(failed_gates),
        applied_exception_ids=sorted(applied_exception_ids),
    )


def _validate_exceptions(exceptions: list[PolicyExceptionApproval]) -> None:
    seen_exception_ids: set[str] = set()
    seen_gate_ids: set[str] = set()

    for exception in exceptions:
        if not exception.exception_id.strip():
            raise ValueError("BL-012 governance policy failed: exception_id must be non-empty.")
        if exception.exception_id in seen_exception_ids:
            raise ValueError(
                f"BL-012 governance policy failed: duplicate exception_id '{exception.exception_id}'."
            )
        seen_exception_ids.add(exception.exception_id)

        if not exception.gate_id.strip():
            raise ValueError("BL-012 governance policy failed: gate_id must be non-empty.")
        if exception.gate_id in seen_gate_ids:
            raise ValueError(
                f"BL-012 governance policy failed: only one exception per gate is allowed for '{exception.gate_id}'."
            )
        seen_gate_ids.add(exception.gate_id)

        if not exception.rationale.strip():
            raise ValueError("BL-012 governance policy failed: rationale must be non-empty.")
        if not exception.approved_by.strip():
            raise ValueError("BL-012 governance policy failed: approved_by must be non-empty.")
        if not exception.approval_record_ref.strip():
            raise ValueError("BL-012 governance policy failed: approval_record_ref must be non-empty.")

        try:
            date.fromisoformat(exception.approved_on)
        except ValueError as error:
            raise ValueError(
                "BL-012 governance policy failed: approved_on must be in ISO-8601 date format."
            ) from error


def _index_exceptions_by_gate(
    exceptions: list[PolicyExceptionApproval],
) -> dict[str, PolicyExceptionApproval]:
    return {item.gate_id: item for item in exceptions}
