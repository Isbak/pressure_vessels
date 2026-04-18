"""Deterministic workflow orchestration with human approval gates (BL-016)."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

WORKFLOW_EXECUTION_REPORT_VERSION = "WorkflowExecutionReport.v1"
APPROVAL_GATE_EVENT_VERSION = "ApprovalGateEvent.v1"


@dataclass(frozen=True)
class WorkflowStageSpec:
    stage_id: str
    requires_approval: bool
    max_retries: int = 0
    fail_first_attempts: int = 0
    escalation_role: str | None = None

    def to_json_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ApprovalGateEvent:
    schema_version: str
    event_id: str
    workflow_id: str
    stage_id: str
    gate_id: str
    decision: str
    approver_role: str
    approver_id: str
    decided_at_utc: str
    rationale: str

    def to_json_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class WorkflowExecutionTraceEvent:
    sequence: int
    stage_id: str
    event_type: str
    status: str
    detail: str

    def to_json_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class WorkflowExecutionReport:
    schema_version: str
    workflow_id: str
    stage_states: dict[str, str]
    completed_stages: list[str]
    blocked_stage: str | None
    failed_stage: str | None
    escalation_target: str | None
    approval_events: list[ApprovalGateEvent]
    execution_trace: list[WorkflowExecutionTraceEvent]

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "workflow_id": self.workflow_id,
            "stage_states": self.stage_states,
            "completed_stages": self.completed_stages,
            "blocked_stage": self.blocked_stage,
            "failed_stage": self.failed_stage,
            "escalation_target": self.escalation_target,
            "approval_events": [event.to_json_dict() for event in self.approval_events],
            "execution_trace": [event.to_json_dict() for event in self.execution_trace],
        }


def orchestrate_workflow(
    *,
    workflow_id: str,
    stage_specs: list[WorkflowStageSpec],
    approval_events: list[ApprovalGateEvent],
) -> WorkflowExecutionReport:
    """Execute deterministic stages with explicit approval, retry, and escalation states."""
    if not workflow_id.strip():
        raise ValueError("BL-016 orchestration failed: workflow_id must be non-empty.")
    if not stage_specs:
        raise ValueError("BL-016 orchestration failed: at least one stage is required.")

    _validate_stage_specs(stage_specs)
    _validate_approval_events(workflow_id=workflow_id, approval_events=approval_events)

    stage_states: dict[str, str] = {stage.stage_id: "pending" for stage in stage_specs}
    completed_stages: list[str] = []
    execution_trace: list[WorkflowExecutionTraceEvent] = []
    blocked_stage: str | None = None
    failed_stage: str | None = None
    escalation_target: str | None = None

    approvals_by_stage = {event.stage_id: event for event in sorted(approval_events, key=lambda item: item.event_id)}

    sequence = 1
    for stage in stage_specs:
        stage_states[stage.stage_id] = "running"
        execution_trace.append(
            WorkflowExecutionTraceEvent(
                sequence=sequence,
                stage_id=stage.stage_id,
                event_type="stage_entered",
                status="running",
                detail=f"Stage '{stage.stage_id}' started.",
            )
        )
        sequence += 1

        if stage.requires_approval:
            stage_states[stage.stage_id] = "pending_approval"
            execution_trace.append(
                WorkflowExecutionTraceEvent(
                    sequence=sequence,
                    stage_id=stage.stage_id,
                    event_type="approval_gate",
                    status="pending_approval",
                    detail="Awaiting human approval event.",
                )
            )
            sequence += 1

            approval_event = approvals_by_stage.get(stage.stage_id)
            if approval_event is None:
                blocked_stage = stage.stage_id
                stage_states[stage.stage_id] = "blocked"
                execution_trace.append(
                    WorkflowExecutionTraceEvent(
                        sequence=sequence,
                        stage_id=stage.stage_id,
                        event_type="approval_gate",
                        status="blocked",
                        detail="No immutable approval event found for stage.",
                    )
                )
                break

            if approval_event.decision == "rejected":
                failed_stage = stage.stage_id
                stage_states[stage.stage_id] = "rejected"
                execution_trace.append(
                    WorkflowExecutionTraceEvent(
                        sequence=sequence,
                        stage_id=stage.stage_id,
                        event_type="approval_gate",
                        status="rejected",
                        detail=f"Approval rejected by role '{approval_event.approver_role}'.",
                    )
                )
                break

            stage_states[stage.stage_id] = "approved"
            execution_trace.append(
                WorkflowExecutionTraceEvent(
                    sequence=sequence,
                    stage_id=stage.stage_id,
                    event_type="approval_gate",
                    status="approved",
                    detail=f"Approval granted by role '{approval_event.approver_role}'.",
                )
            )
            sequence += 1

        success, trace_rows, escalated = _execute_stage_with_retry(stage=stage, start_sequence=sequence)
        execution_trace.extend(trace_rows)
        sequence += len(trace_rows)

        if success:
            stage_states[stage.stage_id] = "completed"
            completed_stages.append(stage.stage_id)
            continue

        if escalated:
            stage_states[stage.stage_id] = "escalated"
            failed_stage = stage.stage_id
            escalation_target = stage.escalation_role
            break

        stage_states[stage.stage_id] = "failed"
        failed_stage = stage.stage_id
        break

    return WorkflowExecutionReport(
        schema_version=WORKFLOW_EXECUTION_REPORT_VERSION,
        workflow_id=workflow_id,
        stage_states=stage_states,
        completed_stages=completed_stages,
        blocked_stage=blocked_stage,
        failed_stage=failed_stage,
        escalation_target=escalation_target,
        approval_events=sorted(approval_events, key=lambda item: item.event_id),
        execution_trace=execution_trace,
    )


def build_approval_gate_event(
    *,
    event_id: str,
    workflow_id: str,
    stage_id: str,
    gate_id: str,
    decision: str,
    approver_role: str,
    approver_id: str,
    decided_at_utc: str,
    rationale: str,
) -> ApprovalGateEvent:
    """Construct immutable approval event payload with deterministic schema version."""
    event = ApprovalGateEvent(
        schema_version=APPROVAL_GATE_EVENT_VERSION,
        event_id=event_id,
        workflow_id=workflow_id,
        stage_id=stage_id,
        gate_id=gate_id,
        decision=decision,
        approver_role=approver_role,
        approver_id=approver_id,
        decided_at_utc=decided_at_utc,
        rationale=rationale,
    )
    _validate_approval_events(workflow_id=workflow_id, approval_events=[event])
    return event


def _execute_stage_with_retry(
    *,
    stage: WorkflowStageSpec,
    start_sequence: int,
) -> tuple[bool, list[WorkflowExecutionTraceEvent], bool]:
    trace_rows: list[WorkflowExecutionTraceEvent] = []
    max_attempts = stage.max_retries + 1

    for attempt in range(1, max_attempts + 1):
        if attempt <= stage.fail_first_attempts:
            status = "retrying" if attempt < max_attempts else "failed"
            trace_rows.append(
                WorkflowExecutionTraceEvent(
                    sequence=start_sequence + len(trace_rows),
                    stage_id=stage.stage_id,
                    event_type="execution_attempt",
                    status=status,
                    detail=f"Attempt {attempt}/{max_attempts} produced deterministic retryable failure.",
                )
            )
            continue

        trace_rows.append(
            WorkflowExecutionTraceEvent(
                sequence=start_sequence + len(trace_rows),
                stage_id=stage.stage_id,
                event_type="execution_attempt",
                status="success",
                detail=f"Attempt {attempt}/{max_attempts} succeeded.",
            )
        )
        return True, trace_rows, False

    if stage.escalation_role is not None:
        trace_rows.append(
            WorkflowExecutionTraceEvent(
                sequence=start_sequence + len(trace_rows),
                stage_id=stage.stage_id,
                event_type="escalation",
                status="escalated",
                detail=(
                    f"Retry budget exhausted after {max_attempts} attempts; escalated to "
                    f"'{stage.escalation_role}'."
                ),
            )
        )
        return False, trace_rows, True

    return False, trace_rows, False


def _validate_stage_specs(stage_specs: list[WorkflowStageSpec]) -> None:
    seen_stage_ids: set[str] = set()
    for stage in stage_specs:
        if not stage.stage_id.strip():
            raise ValueError("BL-016 orchestration failed: stage_id must be non-empty.")
        if stage.stage_id in seen_stage_ids:
            raise ValueError(
                f"BL-016 orchestration failed: duplicate stage_id '{stage.stage_id}'."
            )
        seen_stage_ids.add(stage.stage_id)

        if stage.max_retries < 0:
            raise ValueError("BL-016 orchestration failed: max_retries cannot be negative.")
        if stage.fail_first_attempts < 0:
            raise ValueError("BL-016 orchestration failed: fail_first_attempts cannot be negative.")
        if stage.escalation_role is not None and not stage.escalation_role.strip():
            raise ValueError(
                "BL-016 orchestration failed: escalation_role must be non-empty when supplied."
            )


def _validate_approval_events(
    *,
    workflow_id: str,
    approval_events: list[ApprovalGateEvent],
) -> None:
    seen_event_ids: set[str] = set()
    seen_stage_gates: set[tuple[str, str]] = set()

    for event in approval_events:
        if event.schema_version != APPROVAL_GATE_EVENT_VERSION:
            raise ValueError(
                "BL-016 orchestration failed: approval event schema_version must be ApprovalGateEvent.v1."
            )
        if event.workflow_id != workflow_id:
            raise ValueError("BL-016 orchestration failed: approval event workflow_id mismatch.")
        if not event.event_id.strip():
            raise ValueError("BL-016 orchestration failed: approval event_id must be non-empty.")
        if event.event_id in seen_event_ids:
            raise ValueError(
                f"BL-016 orchestration failed: duplicate approval event_id '{event.event_id}'."
            )
        seen_event_ids.add(event.event_id)

        if not event.stage_id.strip():
            raise ValueError("BL-016 orchestration failed: approval stage_id must be non-empty.")
        if not event.gate_id.strip():
            raise ValueError("BL-016 orchestration failed: approval gate_id must be non-empty.")
        stage_gate = (event.stage_id, event.gate_id)
        if stage_gate in seen_stage_gates:
            raise ValueError(
                "BL-016 orchestration failed: approval events are immutable; duplicate stage/gate decision is not allowed."
            )
        seen_stage_gates.add(stage_gate)

        if event.decision not in {"approved", "rejected"}:
            raise ValueError("BL-016 orchestration failed: approval decision must be 'approved' or 'rejected'.")
        if not event.approver_role.strip():
            raise ValueError("BL-016 orchestration failed: approver_role must be non-empty.")
        if not event.approver_id.strip():
            raise ValueError("BL-016 orchestration failed: approver_id must be non-empty.")
        if not event.rationale.strip():
            raise ValueError("BL-016 orchestration failed: rationale must be non-empty.")

        try:
            timestamp = datetime.fromisoformat(event.decided_at_utc.replace("Z", "+00:00"))
        except ValueError as error:
            raise ValueError(
                "BL-016 orchestration failed: decided_at_utc must be ISO-8601 timestamp."
            ) from error
        if timestamp.tzinfo is None:
            raise ValueError(
                "BL-016 orchestration failed: decided_at_utc must include timezone information."
            )
