# CI Governance Pipeline Contract (BL-012)

## Purpose

`governance_pipeline.py` enforces CI governance gates from policy-as-data and supports explicit, auditable exception approval records.

## Policy Schemas

### `CIGovernancePolicy.v1`

Required fields:

- `artifact_retention_days` (integer `>= 1`)
- `required_gates[]` (unique gate IDs that must report `success` unless exception-approved)

### `PolicyExceptionsDocument.v1` (`version: 1`)

Required fields:

- `version` (`1`)
- `exceptions[]` objects validated by `docs/governance/policy_exceptions_schema.v1.json`

Required fields per exception:

- `id` (unique)
- `gate` (gate this exception can waive)
- `scope[]` (one or more paths/globs)
- `justification` (non-empty)
- `approver` (GitHub handle, e.g., `@reviewer`)
- `approved_at` (ISO-8601 datetime)
- `expires_at` (ISO-8601 datetime; expired exceptions are ignored)
- `linked_backlog_id` (traceable backlog/work item reference)

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
- Matching requires same `gate`, unexpired `expires_at`, and at least one `scope` match against changed paths.
- Any exception usage is explicitly listed in `applied_exception_ids[]` for audit review and logged with approver identity.

## CI Operational Expectations

- CI runs required gate jobs for docs checks, lint, tests, link reporting, and secret scanning.
- CI converts upstream job results into deterministic gate result JSON.
- CI invokes `scripts/check_ci_governance.py` to enforce policy and write `GovernanceGateReport.v1.json`.
- CI uploads governance report plus test report artifacts with explicit retention (`30` days in BL-012 baseline policy).
