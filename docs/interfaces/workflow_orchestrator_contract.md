# Workflow Orchestrator Contract (BL-016)

## Purpose

`workflow_orchestrator.py` provides deterministic stage orchestration with explicit gate states, immutable human-approval events, and observable retry/escalation traces.

## Report Schema

### `WorkflowExecutionReport.v1`

Required fields:

- `workflow_id` (non-empty)
- `stage_states` mapping each declared stage to an explicit state
- `completed_stages[]` ordered by successful completion order
- `blocked_stage` for unresolved approval-gate wait state
- `failed_stage` for terminal rejection/failure/escalation
- `escalation_target` when retry budget exhaustion triggers escalation
- `approval_events[]` (immutable approval records)
- `execution_trace[]` (audit-ready sequence of gate/attempt transitions)

### Stage State Vocabulary

- `pending`
- `running`
- `pending_approval`
- `approved`
- `blocked`
- `rejected`
- `completed`
- `failed`
- `escalated`

## Approval Event Schema

### `ApprovalGateEvent.v1`

`build_approval_gate_event(...)` emits immutable events with required metadata:

- `event_id` (unique)
- `workflow_id`
- `stage_id`
- `gate_id`
- `decision` (`approved` or `rejected`)
- `approver_role`
- `approver_id`
- `decided_at_utc` (ISO-8601 with timezone)
- `rationale`

Immutability constraints enforced by orchestrator input validation:

- duplicate `event_id` disallowed
- duplicate `(stage_id, gate_id)` disallowed
- schema mismatch fails closed

## Deterministic Retry + Escalation Model

Stage execution is deterministic and controlled through stage spec fields:

- `max_retries`: retry budget (`attempts = max_retries + 1`)
- `fail_first_attempts`: deterministic injected adapter failures
- `escalation_role`: escalation destination after retry budget exhaustion

Every attempt is emitted into `execution_trace[]` with ordered `sequence` values and statuses:

- `retrying`
- `failed`
- `success`
- `escalated`

## Example Usage

```python
from pressure_vessels.workflow_orchestrator import (
    WorkflowStageSpec,
    build_approval_gate_event,
    orchestrate_workflow,
)

approval = build_approval_gate_event(
    event_id="APR-100",
    workflow_id="wf-001",
    stage_id="compliance_review",
    gate_id="human_approval",
    decision="approved",
    approver_role="authorized_inspector",
    approver_id="insp-5",
    decided_at_utc="2026-04-18T10:00:00+00:00",
    rationale="Ready for release",
)

report = orchestrate_workflow(
    workflow_id="wf-001",
    stage_specs=[
        WorkflowStageSpec(stage_id="prepare_inputs", requires_approval=False),
        WorkflowStageSpec(stage_id="compliance_review", requires_approval=True),
        WorkflowStageSpec(stage_id="publish_release", requires_approval=False),
    ],
    approval_events=[approval],
)
```
