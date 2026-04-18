# Enterprise Integration Pipeline Contract (BL-011)

## Purpose

`enterprise_integration_pipeline.py` synchronizes deterministic certification artifacts and approvals into configured enterprise systems (PLM/ERP/QMS) while preserving traceability links across system boundaries.

## Batch Schema

### `EnterpriseIntegrationBatch.v1`

Required fields:

- `batch_id` (non-empty)
- `targets[]` with unique `system_code` and supported `system_kind`
- `mappings[]` containing successful cross-boundary synchronization records
- `attempt_logs[]` containing every retry/success attempt for observability
- `failures[]` containing terminal sync failures after retry budget exhaustion
- `deterministic_hash` over canonicalized payload (sha256)

### `EnterpriseSystemTarget`

Each target includes:

- `system_code` (unique identifier)
- `system_kind` (`plm`, `erp`, or `qms`)
- `endpoint`
- `max_retries` (retry budget, default `2`)
- `fail_first_attempts` (deterministic adapter behavior for testable retries)

### `IntegrationBoundaryMapping`

Each mapping row includes:

- `system_code`
- `entity_kind` (`artifact` or `approval`)
- `internal_ref`
- `external_ref`
- `traceability_link_ids[]` copied from inbound traceability graph link IDs for the entity

## Sync Behavior

- Artifacts and approvals are synchronized for each target in deterministic sorted order.
- External IDs are deterministic: `<system_code>:<entity_kind>:<internal_ref>`.
- Retry behavior is deterministic and adapter-driven (`fail_first_attempts`).
- A failure is emitted only when all retries are exhausted.

## Traceability Preservation Rules

- Link IDs are indexed from incoming `TraceabilityLink` rows by source and target reference.
- Every successful boundary mapping must carry exactly the link IDs associated with its `internal_ref`.
- Mismatch in expected vs emitted link IDs fails closed.

## Write Contract

- `write_enterprise_integration_batch(...)` persists `<filename_prefix>.json` with stable key ordering and newline termination.

## Example Usage

```python
from datetime import datetime, timezone

from pressure_vessels.enterprise_integration_pipeline import (
    ApprovalSyncRecord,
    ArtifactSyncRecord,
    EnterpriseSystemTarget,
    run_enterprise_integration_batch,
)

batch = run_enterprise_integration_batch(
    batch_id="batch-001",
    targets=[
        EnterpriseSystemTarget(system_code="PLM-A", system_kind="plm", endpoint="plm://system-a"),
        EnterpriseSystemTarget(system_code="QMS-A", system_kind="qms", endpoint="qms://system-a"),
    ],
    artifacts=[
        ArtifactSyncRecord(
            artifact_ref="dossier-001",
            artifact_type="certification_dossier",
            content_hash="hash-dossier-001",
        )
    ],
    approvals=[
        ApprovalSyncRecord(
            approval_id="approval-001",
            artifact_ref="dossier-001",
            status="approved",
            approver_role="design_authority",
        )
    ],
    traceability_links=traceability_links,
    now_utc=datetime(2026, 4, 18, tzinfo=timezone.utc),
)
```
