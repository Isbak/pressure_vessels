"""Deterministic workflow orchestration with human approval gates (BL-016)."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

WORKFLOW_EXECUTION_REPORT_VERSION = "WorkflowExecutionReport.v1"
APPROVAL_GATE_EVENT_VERSION = "ApprovalGateEvent.v1"
SECURITY_AUDIT_EVENT_VERSION = "SecurityAuditEvent.v1"
TELEMETRY_METRIC_EVENT_VERSION = "TelemetryMetricEvent.v1"


@dataclass(frozen=True)
class WorkflowStageSpec:
    stage_id: str
    requires_approval: bool
    max_retries: int = 0
    fail_first_attempts: int = 0
    escalation_role: str | None = None

    def __post_init__(self) -> None:
        if self.max_retries < 0:
            raise ValueError("BL-016 orchestration failed: max_retries cannot be negative.")
        if self.max_retries > 10:
            raise ValueError("BL-016 orchestration failed: max_retries cannot exceed 10.")
        if self.fail_first_attempts < 0:
            raise ValueError("BL-016 orchestration failed: fail_first_attempts cannot be negative.")
        if self.fail_first_attempts > self.max_retries:
            raise ValueError(
                "BL-016 orchestration failed: fail_first_attempts cannot exceed max_retries."
            )

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
class SecurityAuditEvent:
    schema_version: str
    event_id: str
    workflow_id: str
    stage_id: str
    actor: str
    action: str
    artifact: str
    decision: str
    recorded_at_utc: str

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
class TelemetryMetricEvent:
    schema_version: str
    metric_id: str
    workflow_id: str
    stage_id: str
    metric_family: str
    metric_name: str
    value: float
    unit: str
    labels: dict[str, str]
    measured_window: str

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
    security_audit_events: list[SecurityAuditEvent]
    telemetry_metric_events: list[TelemetryMetricEvent]
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
            "security_audit_events": [event.to_json_dict() for event in self.security_audit_events],
            "telemetry_metric_events": [event.to_json_dict() for event in self.telemetry_metric_events],
            "execution_trace": [event.to_json_dict() for event in self.execution_trace],
        }


@dataclass(frozen=True)
class WorkflowExecutionEventRecord:
    """Append-only event row persisted in PostgreSQL-backed workflow event store."""

    revision_id: str
    workflow_id: str
    event_sequence: int
    event_kind: str
    payload: dict[str, Any]

    def to_json_dict(self) -> dict[str, Any]:
        return asdict(self)


class PostgresqlWorkflowEventStoreBackend:
    """Deterministic in-memory stand-in for a PostgreSQL append-only table."""

    def __init__(self) -> None:
        self._rows_by_workflow: dict[str, list[WorkflowExecutionEventRecord]] = {}
        self._all_revision_ids: set[str] = set()

    def append(self, record: WorkflowExecutionEventRecord) -> None:
        if record.revision_id in self._all_revision_ids:
            raise ValueError(
                f"BL-035 persistence failed: immutable revision_id '{record.revision_id}' already exists."
            )
        workflow_rows = self._rows_by_workflow.setdefault(record.workflow_id, [])
        workflow_rows.append(record)
        self._all_revision_ids.add(record.revision_id)

    def list_by_workflow(self, workflow_id: str) -> list[WorkflowExecutionEventRecord]:
        return list(sorted(self._rows_by_workflow.get(workflow_id, []), key=lambda row: row.event_sequence))


class PostgresqlWorkflowEventStore:
    """PostgreSQL-facing event store abstraction used by workflow orchestration."""

    def __init__(self, backend: PostgresqlWorkflowEventStoreBackend) -> None:
        self._backend = backend

    def persist_report(self, report: WorkflowExecutionReport) -> list[WorkflowExecutionEventRecord]:
        rows: list[WorkflowExecutionEventRecord] = []
        sequence = 1

        for approval in report.approval_events:
            rows.append(
                WorkflowExecutionEventRecord(
                    revision_id=_build_workflow_revision_id(report.workflow_id, sequence),
                    workflow_id=report.workflow_id,
                    event_sequence=sequence,
                    event_kind="approval_event",
                    payload=approval.to_json_dict(),
                )
            )
            sequence += 1

        for security_event in report.security_audit_events:
            rows.append(
                WorkflowExecutionEventRecord(
                    revision_id=_build_workflow_revision_id(report.workflow_id, sequence),
                    workflow_id=report.workflow_id,
                    event_sequence=sequence,
                    event_kind="security_audit_event",
                    payload=security_event.to_json_dict(),
                )
            )
            sequence += 1

        for event in report.execution_trace:
            rows.append(
                WorkflowExecutionEventRecord(
                    revision_id=_build_workflow_revision_id(report.workflow_id, sequence),
                    workflow_id=report.workflow_id,
                    event_sequence=sequence,
                    event_kind="execution_trace_event",
                    payload=event.to_json_dict(),
                )
            )
            sequence += 1

        for metric in report.telemetry_metric_events:
            rows.append(
                WorkflowExecutionEventRecord(
                    revision_id=_build_workflow_revision_id(report.workflow_id, sequence),
                    workflow_id=report.workflow_id,
                    event_sequence=sequence,
                    event_kind="telemetry_metric_event",
                    payload=metric.to_json_dict(),
                )
            )
            sequence += 1

        rows.append(
            WorkflowExecutionEventRecord(
                revision_id=_build_workflow_revision_id(report.workflow_id, sequence),
                workflow_id=report.workflow_id,
                event_sequence=sequence,
                event_kind="workflow_summary",
                payload={
                    "schema_version": report.schema_version,
                    "workflow_id": report.workflow_id,
                    "stage_states": report.stage_states,
                    "completed_stages": report.completed_stages,
                    "blocked_stage": report.blocked_stage,
                    "failed_stage": report.failed_stage,
                    "escalation_target": report.escalation_target,
                },
            )
        )

        for row in rows:
            self._backend.append(row)
        return rows

    def load_report(self, workflow_id: str) -> WorkflowExecutionReport:
        rows = self._backend.list_by_workflow(workflow_id)
        if not rows:
            raise ValueError(
                f"BL-035 recovery failed: workflow '{workflow_id}' has no persisted events."
            )

        approval_events: list[ApprovalGateEvent] = []
        execution_trace: list[WorkflowExecutionTraceEvent] = []
        security_audit_events: list[SecurityAuditEvent] = []
        telemetry_metric_events: list[TelemetryMetricEvent] = []
        summary_payload: dict[str, Any] | None = None

        for row in rows:
            if row.event_kind == "approval_event":
                approval_events.append(ApprovalGateEvent(**row.payload))
            elif row.event_kind == "execution_trace_event":
                execution_trace.append(WorkflowExecutionTraceEvent(**row.payload))
            elif row.event_kind == "security_audit_event":
                security_audit_events.append(SecurityAuditEvent(**row.payload))
            elif row.event_kind == "telemetry_metric_event":
                telemetry_metric_events.append(TelemetryMetricEvent(**row.payload))
            elif row.event_kind == "workflow_summary":
                summary_payload = row.payload

        if summary_payload is None:
            raise ValueError(
                f"BL-035 recovery failed: workflow '{workflow_id}' has no terminal summary event."
            )

        return WorkflowExecutionReport(
            schema_version=summary_payload["schema_version"],
            workflow_id=summary_payload["workflow_id"],
            stage_states=summary_payload["stage_states"],
            completed_stages=summary_payload["completed_stages"],
            blocked_stage=summary_payload["blocked_stage"],
            failed_stage=summary_payload["failed_stage"],
            escalation_target=summary_payload["escalation_target"],
            approval_events=approval_events,
            security_audit_events=security_audit_events,
            telemetry_metric_events=telemetry_metric_events,
            execution_trace=execution_trace,
        )


def orchestrate_or_resume_workflow(
    *,
    workflow_id: str,
    stage_specs: list[WorkflowStageSpec],
    approval_events: list[ApprovalGateEvent],
    event_store: PostgresqlWorkflowEventStore,
) -> tuple[WorkflowExecutionReport, bool]:
    """Resume from persisted report when available, otherwise execute and persist deterministically."""
    try:
        return event_store.load_report(workflow_id), True
    except ValueError as error:
        if "has no persisted events" not in str(error):
            raise

    report = orchestrate_workflow(
        workflow_id=workflow_id,
        stage_specs=stage_specs,
        approval_events=approval_events,
    )
    event_store.persist_report(report)
    return report, False


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
        security_audit_events=_build_security_audit_events(
            workflow_id=workflow_id,
            approval_events=approval_events,
        ),
        telemetry_metric_events=_build_telemetry_metric_events(
            workflow_id=workflow_id,
            stage_specs=stage_specs,
            stage_states=stage_states,
            failed_stage=failed_stage,
            execution_trace=execution_trace,
        ),
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


def _build_security_audit_events(
    *,
    workflow_id: str,
    approval_events: list[ApprovalGateEvent],
) -> list[SecurityAuditEvent]:
    return [
        SecurityAuditEvent(
            schema_version=SECURITY_AUDIT_EVENT_VERSION,
            event_id=f"{event.event_id}:security",
            workflow_id=workflow_id,
            stage_id=event.stage_id,
            actor=f"{event.approver_role}:{event.approver_id}",
            action="approval_gate_decision",
            artifact=event.gate_id,
            decision=event.decision,
            recorded_at_utc=event.decided_at_utc,
        )
        for event in sorted(approval_events, key=lambda item: item.event_id)
    ]


def _build_workflow_revision_id(workflow_id: str, event_sequence: int) -> str:
    return f"{workflow_id}:rev:{event_sequence:05d}"


def _build_telemetry_metric_events(
    *,
    workflow_id: str,
    stage_specs: list[WorkflowStageSpec],
    stage_states: dict[str, str],
    failed_stage: str | None,
    execution_trace: list[WorkflowExecutionTraceEvent],
) -> list[TelemetryMetricEvent]:
    stage_attempts: dict[str, int] = {stage.stage_id: 0 for stage in stage_specs}
    for row in execution_trace:
        if row.event_type == "execution_attempt":
            stage_attempts[row.stage_id] = stage_attempts.get(row.stage_id, 0) + 1

    metrics: list[TelemetryMetricEvent] = []
    for stage in stage_specs:
        attempts = max(1, stage_attempts.get(stage.stage_id, 0))
        failed_attempts = max(0, attempts - 1)
        stage_state = stage_states.get(stage.stage_id, "pending")
        success_value = 1.0 if stage_state == "completed" else 0.0
        utilization_value = min(1.0, attempts / float(stage.max_retries + 1))

        metrics.extend(
            [
                TelemetryMetricEvent(
                    schema_version=TELEMETRY_METRIC_EVENT_VERSION,
                    metric_id=f"{workflow_id}:{stage.stage_id}:red:requests",
                    workflow_id=workflow_id,
                    stage_id=stage.stage_id,
                    metric_family="RED",
                    metric_name="stage_requests_total",
                    value=float(attempts),
                    unit="count",
                    labels={"stage_status": stage_state},
                    measured_window="per_workflow_run",
                ),
                TelemetryMetricEvent(
                    schema_version=TELEMETRY_METRIC_EVENT_VERSION,
                    metric_id=f"{workflow_id}:{stage.stage_id}:red:errors",
                    workflow_id=workflow_id,
                    stage_id=stage.stage_id,
                    metric_family="RED",
                    metric_name="stage_errors_total",
                    value=float(failed_attempts),
                    unit="count",
                    labels={"stage_status": stage_state},
                    measured_window="per_workflow_run",
                ),
                TelemetryMetricEvent(
                    schema_version=TELEMETRY_METRIC_EVENT_VERSION,
                    metric_id=f"{workflow_id}:{stage.stage_id}:red:latency",
                    workflow_id=workflow_id,
                    stage_id=stage.stage_id,
                    metric_family="RED",
                    metric_name="stage_latency_ms",
                    value=float(attempts * 250),
                    unit="ms",
                    labels={"stage_status": stage_state},
                    measured_window="per_workflow_run",
                ),
                TelemetryMetricEvent(
                    schema_version=TELEMETRY_METRIC_EVENT_VERSION,
                    metric_id=f"{workflow_id}:{stage.stage_id}:use:utilization",
                    workflow_id=workflow_id,
                    stage_id=stage.stage_id,
                    metric_family="USE",
                    metric_name="worker_utilization_ratio",
                    value=utilization_value,
                    unit="ratio",
                    labels={"capacity_scope": "orchestrator_worker"},
                    measured_window="per_workflow_run",
                ),
                TelemetryMetricEvent(
                    schema_version=TELEMETRY_METRIC_EVENT_VERSION,
                    metric_id=f"{workflow_id}:{stage.stage_id}:use:saturation",
                    workflow_id=workflow_id,
                    stage_id=stage.stage_id,
                    metric_family="USE",
                    metric_name="retry_budget_saturation_ratio",
                    value=utilization_value,
                    unit="ratio",
                    labels={"capacity_scope": "retry_budget"},
                    measured_window="per_workflow_run",
                ),
                TelemetryMetricEvent(
                    schema_version=TELEMETRY_METRIC_EVENT_VERSION,
                    metric_id=f"{workflow_id}:{stage.stage_id}:use:errors",
                    workflow_id=workflow_id,
                    stage_id=stage.stage_id,
                    metric_family="USE",
                    metric_name="worker_error_ratio",
                    value=0.0 if attempts == 0 else failed_attempts / float(attempts),
                    unit="ratio",
                    labels={"capacity_scope": "orchestrator_worker"},
                    measured_window="per_workflow_run",
                ),
            ]
        )

    metrics.extend(
        [
            TelemetryMetricEvent(
                schema_version=TELEMETRY_METRIC_EVENT_VERSION,
                metric_id=f"{workflow_id}:slo:orchestration_latency_ms",
                workflow_id=workflow_id,
                stage_id="workflow",
                metric_family="SLO",
                metric_name="orchestration_latency_ms",
                value=float(sum(max(1, stage_attempts.get(stage.stage_id, 0)) * 250 for stage in stage_specs)),
                unit="ms",
                labels={"objective": "P95<=5000ms", "window": "rolling_30d"},
                measured_window="rolling_30d",
            ),
            TelemetryMetricEvent(
                schema_version=TELEMETRY_METRIC_EVENT_VERSION,
                metric_id=f"{workflow_id}:slo:run_success_ratio",
                workflow_id=workflow_id,
                stage_id="workflow",
                metric_family="SLO",
                metric_name="run_success_ratio",
                value=1.0 if failed_stage is None else 0.0,
                unit="ratio",
                labels={"objective": ">=0.995", "window": "rolling_30d"},
                measured_window="rolling_30d",
            ),
            TelemetryMetricEvent(
                schema_version=TELEMETRY_METRIC_EVENT_VERSION,
                metric_id=f"{workflow_id}:slo:artifact_export_success_ratio",
                workflow_id=workflow_id,
                stage_id="workflow",
                metric_family="SLO",
                metric_name="artifact_export_success_ratio",
                value=(
                    1.0
                    if all(
                        stage_states.get(stage.stage_id) == "completed"
                        for stage in stage_specs
                        if "export" in stage.stage_id or "publish" in stage.stage_id
                    )
                    else 0.0
                ),
                unit="ratio",
                labels={"objective": ">=0.999", "window": "rolling_30d"},
                measured_window="rolling_30d",
            ),
        ]
    )
    return metrics
