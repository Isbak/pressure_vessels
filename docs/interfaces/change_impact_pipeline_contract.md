# Change Impact Pipeline Contract (BL-008)

## Purpose

`change_impact_pipeline.py` provides deterministic revision delta detection, minimal selective re-verification, and signed impact report generation for revision-to-revision updates.

## Primary API

- `build_revision_trace_snapshot(...)`
- `detect_revision_delta(previous, current)`
- `compute_minimal_reverification_set(delta, previous_graph, current_graph, current_calculation_records)`
- `execute_selective_reverification(selected_checks, current_graph)`
- `generate_change_impact_report(previous_snapshot, current_snapshot, previous_graph, current_graph, current_calculation_records, signing_key_ref, now_utc=None)`
- `write_impact_report(impact_report, directory, filename_prefix="")`
- `write_baseline_update_status(baseline_update_status, directory, filename_prefix="")`

## Schemas

### `RevisionTraceSnapshot.v1`

Revision-level, immutable snapshot inputs used to detect deltas.

Required fields:

- `revision_id`
- `previous_revision_id` (nullable)
- `requirement_set_hash`
- `calculation_records_hash`
- `traceability_graph_hash`
- `code_fingerprint`
- `model_fingerprint`

### `RevisionDelta.v1`

Computed deterministic comparison between two snapshots.

- `changed_domains[]`: subset of `requirement`, `code`, `model`
- `changed_hashes`: `from`/`to` values by changed domain

### `ImpactReport.v1`

Signed artifact produced per revision delta.

- `revision_delta`
- `impacted_clause_ids[]`
- `minimal_reverification_check_ids[]`
- `reverification_results[]` with evidence links
- `baseline_update_status` (`BaselineUpdateStatus.v1`)
- `signing` (`algorithm`, `signing_key_ref`, deterministic `signature`)
- `deterministic_hash`

### `BaselineUpdateStatus.v1`

Explicit baseline decision persisted with each report.

- `decision`: `accepted` or `rejected`
- `rationale`
- `reverification_check_ids[]`

## Re-verification Scope Rules

- If code changes, all current checks are re-verified.
- If model changes, impacted clauses/models are found from traceability graph link deltas.
- If requirement changes, impacted requirement->clause links define clause scope.
- Re-verification execution uses deterministic, already-produced calculation outcomes and emits clause/check-scoped evidence refs.
- Impact report generation validates snapshot-to-traceability alignment (`revision_id`, requirement hash, and graph hash) and current calculation hash integrity before running delta analysis.

## Artifact Example

- Sample artifact: `artifacts/bl-008/ImpactReport.v1.sample.json`
- Sample artifact: `artifacts/bl-008/BaselineUpdateStatus.v1.sample.json`
