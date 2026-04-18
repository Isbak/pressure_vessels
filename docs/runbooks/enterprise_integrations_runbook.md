# Runbook: BL-011 Enterprise Integrations (PLM / ERP / QMS)

## Purpose

Operational runbook for synchronizing certification artifacts and approvals into enterprise systems with deterministic retries and auditable traceability mappings.

## Inputs

- One or more `EnterpriseSystemTarget` entries.
- One or more `ArtifactSyncRecord` entries.
- Zero or more `ApprovalSyncRecord` entries.
- Traceability graph links (`TraceabilityLink`) covering integrated entity references.
- `batch_id` for release/integration correlation.

## Procedure

1. Confirm enterprise targets are configured with unique `system_code` and valid `system_kind` (`plm`, `erp`, `qms`).
2. Build deterministic artifact payload references and approval references.
3. Load traceability links from the project revision to preserve clause/model/calculation/artifact/approval lineage.
4. Run `run_enterprise_integration_batch(...)`.
5. Review `attempt_logs` for retries and confirm no unexpected terminal failures.
6. Persist the batch report with `write_enterprise_integration_batch(...)`.
7. Publish the persisted integration report with release artifacts for audit retrieval.

## Observability and Failure Handling

- Every sync attempt is recorded in `attempt_logs` with:
  - target system
  - entity type/reference
  - attempt number
  - status (`success` or `retryable_failure`)
- Terminal failures are recorded in `failures[]` when retry budgets are exhausted.
- A non-empty `failures[]` set should trigger incident triage and replay planning.

## Deterministic Controls

- Inject `now_utc` in tests and controlled replay jobs.
- Sync ordering is deterministic by `(system_kind, system_code, entity_ref)`.
- External refs are deterministic (`<system_code>:<entity_kind>:<internal_ref>`).
- Hashes use sha256 over canonical JSON (`sort_keys=True`, compact separators).

## Escalation Expectations

- If retry exhaustion occurs for production targets, open an incident record with:
  - `batch_id`
  - failing `system_code`
  - impacted `entity_ref`
  - full `attempt_logs` excerpt
- Re-run the same `batch_id` only after root-cause review; use a new batch ID for replay attempts to preserve audit lineage.

## Example Snippet

```python
from datetime import datetime, timezone

from pressure_vessels.enterprise_integration_pipeline import (
    ApprovalSyncRecord,
    ArtifactSyncRecord,
    EnterpriseSystemTarget,
    run_enterprise_integration_batch,
    write_enterprise_integration_batch,
)

batch = run_enterprise_integration_batch(
    batch_id="release-2026-04-18",
    targets=[
        EnterpriseSystemTarget(system_code="PLM-A", system_kind="plm", endpoint="plm://system-a"),
        EnterpriseSystemTarget(system_code="ERP-A", system_kind="erp", endpoint="erp://system-a"),
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
            approver_role="authorized_inspector",
        )
    ],
    traceability_links=traceability_links,
    now_utc=datetime(2026, 4, 18, tzinfo=timezone.utc),
)

write_enterprise_integration_batch(batch, "artifacts/bl-011", filename_prefix="release-2026-04-18")
```
