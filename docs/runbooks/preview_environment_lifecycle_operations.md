# Preview Environment Lifecycle Operations Runbook (DX-010)

This runbook defines deterministic operations for PR-scoped ephemeral preview
environments.

## Scope and ownership

- **Workflow source of truth**: `.github/workflows/preview-environment.yml`
- **Primary owner**: Platform Runtime Team
- **Supporting owner**: Platform Experience Team

## Deterministic lifecycle policy

Every preview environment follows the same immutable lifecycle:

1. **Provision trigger**: `pull_request` events (`opened`, `reopened`,
   `synchronize`, `ready_for_review`).
2. **Isolation key**: `pr-<pr_number>-<head_sha_12>`.
3. **Preview URL format**:
   `https://pr-<pr_number>-<head_sha_12>.preview.pressure-vessels.internal`.
4. **Teardown trigger (hard stop)**: PR `closed` event.
5. **TTL fallback**: 72 hours from latest provision event, whichever comes first.

This dual-trigger policy guarantees deterministic teardown even if close event
handling is delayed.

## Operational procedure

### Launch path

1. Open or update a PR.
2. Wait for **Preview Environment** workflow to complete.
3. Retrieve the preview URL from:
   - PR comment added by workflow, or
   - workflow summary/artifact (`artifacts/preview/metadata.json`).

### Teardown path

1. Close or merge the PR.
2. Confirm **Preview Environment** workflow executes teardown path.
3. Verify summary states teardown completion.
4. If close-event automation is unavailable, enforce TTL cleanup at
   `provisioned_at + 72h`.

## Failure handling

- If launch fails, rerun the workflow after validating PR branch health.
- If teardown fails on PR close, manually remove resources using the same
  isolation key (`pr-<pr_number>-<head_sha_12>`) and record incident notes.
- Any manual teardown must preserve deterministic keying and be completed within
  the 72-hour TTL boundary.
