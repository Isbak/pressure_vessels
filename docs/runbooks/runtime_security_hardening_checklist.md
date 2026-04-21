# Runtime Security Hardening Checklist (BL-038)

## Scope

Production runtime interfaces for backend design-run APIs and approval-gate workflow events.

## Secrets Integration Controls

- [x] Runtime auth secret is read from `PV_BACKEND_AUTH_TOKEN_SECRET`.
- [x] Secret loading uses approved module boundary path
      `infra/platform/secrets/module.boundaries.yaml`.
- [x] No plaintext default or fallback token secret is present in backend runtime code.
- [x] Contract docs define token shape and scope requirements.
- [x] Repository tests verify approved module path and no fallback behavior.

## Role-Scoped Auth Token Controls

- [x] Auth token format is versioned (`v1`) and deterministic.
- [x] Allowed personas are constrained to `engineer`, `reviewer`, `approver`.
- [x] `POST /api/v1/design-runs` requires `design_runs:write`.
- [x] `GET /api/v1/design-runs/{runId}` requires `design_runs:read` (or stronger write scope).
- [x] Invalid/missing token paths fail closed with `401`/`403`.

## Approval-Gate Security Audit Controls

- [x] Approval decisions emit `SecurityAuditEvent.v1` records.
- [x] Security audit record captures `actor`, `action`, `artifact`, and `decision`.
- [x] Security audit records are persisted in append-only workflow event storage.
- [x] Recovery path restores security audit records without mutation.
