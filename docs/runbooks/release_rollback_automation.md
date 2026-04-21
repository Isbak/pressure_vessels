# Release Rollback Automation Runbook (BL-042)

## Objective

Restore the previous known-good tagged release and capture deterministic rollback audit evidence.

## Trigger

Run `.github/workflows/release-rollback.yml` with:

- `failed_release_tag`: the currently promoted tag that must be rolled back.
- `rollback_to_tag`: the prior known-good release tag.
- `target_environment`: `staging` or `production`.
- `rollback_reason`: concise incident/change rationale.

## Automated controls

1. **Governance-by-default:** rollback can only execute through protected GitHub environments (`staging`/`production`) configured with required human reviewers.
2. **Deterministic target selection:** rollback target is an explicit immutable tag input (`rollback_to_tag`).
3. **Audit evidence capture:** workflow emits `RollbackAuditEvidence.v1.json` artifact with actor, timestamp, source/target release, and reason.

## Validation report

Validation completed by repository automation update for BL-042:

- Workflow-level validation:
  - YAML parses successfully.
  - Rollback evidence file is generated deterministically from workflow inputs.
- Governance alignment validation:
  - Uses environment protection as promotion/rollback gate.
  - Keeps security and governance evidence in retained CI artifacts.

## Rollback evidence payload

`RollbackAuditEvidence.v1.json` contains:

- `schema_version`
- `failed_release_tag`
- `rollback_to_tag`
- `target_environment`
- `rollback_reason`
- `rollback_actor`
- `rollback_run_id`
- `rollback_timestamp`

## Post-rollback checklist

1. Confirm service health on rolled-back tag in target environment.
2. Link incident ticket to rollback evidence artifact.
3. Open a corrective action backlog item if release regression root cause is unresolved.
