# Runbook: BL-016 Workflow Orchestration Retries and Escalations

## Purpose

Operational runbook for deterministic workflow execution with human approval gates, retry visibility, and escalation handling.

## Inputs

- `workflow_id` identifying the orchestration run.
- Ordered `WorkflowStageSpec[]` definitions.
- Optional `ApprovalGateEvent[]` records for approval-gated stages.

## Procedure

1. Declare stages in strict deterministic order.
2. For every human-gated stage (`requires_approval=True`), collect immutable approval events before release execution.
3. Execute `orchestrate_workflow(...)`.
4. Validate stage-level state transitions:
   - every stage has explicit final state
   - blocked/rejected/failed/escalated states stop downstream execution
5. Inspect `execution_trace[]` for retry and escalation status rows.
6. Persist orchestration report as audit evidence alongside release artifacts.

## Approval-Gate Operations

- Capture decisions via `build_approval_gate_event(...)`.
- Require role + user + timestamp (`decided_at_utc`) for every approval event.
- Reject duplicate decision records for the same `(stage_id, gate_id)`.
- If approval evidence is missing, pipeline should remain blocked (`blocked_stage`).

## Retry and Escalation Policy

- Define retry budget per stage (`max_retries`).
- Use deterministic failure injection (`fail_first_attempts`) in test/replay contexts.
- If retries exhaust:
  - set stage state to `failed` when no escalation role is configured
  - set stage state to `escalated` and route to `escalation_role` when configured

## Audit Trace Expectations

`execution_trace[]` should include ordered events for:

- stage entry (`stage_entered`)
- approval gate checks (`approval_gate`)
- retry/success attempts (`execution_attempt`)
- escalation dispatch (`escalation`)

Each trace row is sequence-numbered and deterministic, enabling replay validation and incident forensics.

## Incident Escalation Checklist

When `escalation_target` is non-null:

- open incident with workflow ID and failed stage
- include full attempt trace rows for that stage
- identify escalation role owner and acknowledgment timestamp
- rerun with a new workflow ID after root-cause resolution
