# Traceability Pipeline Contract (BL-006)

## Purpose

`traceability_pipeline.py` produces immutable, revisioned traceability graph snapshots that extend BL-004 evidence links into a full requirement -> clause -> model -> calculation -> artifact -> approval graph.

## Graph Schema

### `TraceabilityGraphRevision.v1`

Required fields:

- `revision_id` (non-empty)
- `previous_revision_id` (nullable)
- `immutable` (always `true` by default)
- source hash/signature links to upstream artifacts:
  - `source_requirement_set_hash`
  - `source_design_basis_signature`
  - `source_applicability_matrix_hash`
  - `source_compliance_dossier_hash`
- `links[]` containing deterministic `TraceabilityLink` entries

### `TraceabilityLink`

Each link contains:

- `link_id`
- `source_kind`, `source_ref`
- `target_kind`, `target_ref`
- `relation`
- `clause_id` (optional clause scope)

Allowed endpoint kinds:

- `requirement`
- `clause`
- `model`
- `calculation`
- `artifact`
- `approval`

## Query Helpers

- `query_graph_by_revision(graph_revisions, revision_id)`
  - returns one graph revision
  - fails closed when revision is missing
- `query_clause_evidence(graph_revisions, clause_id, revision_id=None)`
  - returns clause-linked evidence rows across all revisions or a single revision
- `build_audit_report_template(graph_revision, clause_id=None)`
  - returns `TraceabilityAuditReportTemplate.v1`
  - includes deterministic `summary_lines` and `evidence_rows`

## Neo4j Persistence Path (BL-035)

`Neo4jTraceabilityStore` provides deterministic runtime persistence wrappers:

- `persist_revision(graph_revision)` appends immutable revision writes
- `get_revision(revision_id)` reads one revision snapshot
- `query_clause_links(clause_id, revision_id=None)` returns clause-scoped evidence links

Immutability is enforced by revision ID; duplicate `revision_id` writes fail closed.

## Write and Immutability Rules

- `write_traceability_graph_revision()` writes `<revision_id>.traceability_graph.json` with file mode `x` (no overwrite).
- `with_additional_links()` blocks mutation when `immutable=true` unless explicitly bypassed.
- Graph build validates upstream artifact hash/signature consistency before emitting a revision.

## Example Usage

```python
from datetime import datetime, timezone

from pressure_vessels.traceability_pipeline import (
    Neo4jTraceabilityStore,
    Neo4jTraceabilityStoreBackend,
    ApprovalRecord,
    build_traceability_graph_revision,
    build_audit_report_template,
    query_clause_evidence,
)

graph = build_traceability_graph_revision(
    requirement_set,
    design_basis,
    applicability_matrix,
    compliance_dossier_machine,
    revision_id="REV-0001",
    approvals=[
        ApprovalRecord(
            approval_id="APR-001",
            approver_role="authorized_inspector",
            status="approved",
            artifact_ref=f"ComplianceDossierMachine.v1#{compliance_dossier_machine.deterministic_hash}",
        )
    ],
    now_utc=datetime(2026, 4, 18, tzinfo=timezone.utc),
)

ug27_links = query_clause_evidence([graph], "UG-27", revision_id="REV-0001")
audit_payload = build_audit_report_template(graph, clause_id="UG-27")

backend = Neo4jTraceabilityStoreBackend()
store = Neo4jTraceabilityStore(backend)
store.persist_revision(graph)
same_revision = store.get_revision("REV-0001")
ug27_links = store.query_clause_links(clause_id="UG-27", revision_id="REV-0001")
```
