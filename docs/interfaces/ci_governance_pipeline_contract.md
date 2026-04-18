# CI Governance Pipeline Contract (BL-012)

## Purpose

`governance_pipeline.py` enforces CI governance gates from policy-as-data and supports explicit, auditable exception approval records.

## Policy Schemas

### `CIGovernancePolicy.v1`

Required fields:

- `artifact_retention_days` (integer `>= 1`)
- `required_gates[]` (unique gate IDs that must report `success` unless exception-approved)

### `PolicyExceptions.v1`

Required fields per exception:

- `exception_id` (unique)
- `gate_id` (single exception allowed per gate)
- `rationale` (non-empty)
- `approved_by` (non-empty reviewer identity)
- `approved_on` (ISO date)
- `approval_record_ref` (non-empty traceable approval reference)

## Gate Evaluation Contract

`evaluate_governance_gates(policy, gate_results)` emits `GovernanceGateReport.v1`.

### `GovernanceGateReport.v1`

Required fields:

- `policy_schema_version`
- `artifact_retention_days`
- `gate_status` map with one of:
  - `pass`
  - `exception-approved`
  - `fail:<result>`
- `failed_gates[]`
- `applied_exception_ids[]`

Behavior:

- Missing gates fail closed (`fail:missing`).
- Non-success gate results fail closed unless a matching approved exception exists.
- Any exception usage is explicitly listed in `applied_exception_ids[]` for audit review.

## CI Operational Expectations

- CI runs required gate jobs for docs checks, lint, tests, link reporting, and secret scanning.
- CI converts upstream job results into deterministic gate result JSON.
- CI invokes `scripts/check_ci_governance.py` to enforce policy and write `GovernanceGateReport.v1.json`.
- CI uploads governance report plus test report artifacts with explicit retention (`30` days in BL-012 baseline policy).
