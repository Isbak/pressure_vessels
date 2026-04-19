# Platform Workflow Orchestration Module (BL-028)

This module defines deterministic ownership and lifecycle boundaries for the
Temporal workflow orchestration runtime.

## Scope

- Declares canonical Temporal namespace boundaries for platform workflow
  execution.
- Defines task queue and worker ownership contracts for staging runtime
  operations.
- Defines lifecycle boundaries for provisioning, worker rollout, and recovery
  operations.

## Boundary Rules

1. **Namespace boundary**: the `pressure-vessels-staging` namespace is owned by
   the Orchestration Platform Team; consuming services may not mutate namespace
   policy.
2. **Task queue boundary**: each queue has an explicit owning team and producer
   and worker contract for workflow/task execution.
3. **Worker boundary**: workers are owned and operated by designated teams with
   approval-gated rollout and rollback paths.

See `module.boundaries.yaml` for machine-readable contract data.
