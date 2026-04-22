# Runtime Security Hardening Checklist (BL-038)

## Scope

Production runtime interfaces for backend design-run APIs and approval-gate workflow events.

## Secrets Integration Controls

- [x] Runtime auth provider issuer is read from `PV_AUTH_PROVIDER_ISSUER`.
- [x] Runtime auth provider audience is read from `PV_AUTH_PROVIDER_AUDIENCE`.
- [x] Runtime auth provider key set is read from `PV_AUTH_PROVIDER_JWKS_JSON`.
- [x] Secret loading uses approved module boundary path
      `infra/platform/secrets/module.boundaries.yaml`.
- [x] No plaintext default or fallback token secret is present in backend runtime code.
- [x] Contract docs define token shape and scope requirements.
- [x] Repository tests verify approved module path and no fallback behavior.

### Token key rotation, revocation, and break-glass procedures

1. **Normal rotation (planned)**
   - Generate a new provider signing key with a new `kid`.
   - Publish both old + new keys in `PV_AUTH_PROVIDER_JWKS_JSON` during overlap.
   - Switch provider signing to the new `kid`.
   - After TTL window passes, remove retired key from keyset and redeploy backend.
2. **Revocation (compromise)**
   - Remove compromised `kid` from `PV_AUTH_PROVIDER_JWKS_JSON`.
   - Re-issue runtime tokens from provider with replacement `kid`.
   - Verify backend rejects tokens signed by revoked key (`401 invalid authorization token`).
3. **Break-glass (provider outage)**
   - Record incident ID + approving security reviewer in runtime change record.
   - Temporarily pin `PV_AUTH_PROVIDER_JWKS_JSON` to emergency offline signer keyset.
   - Keep `PV_AUTH_PROVIDER_ISSUER` and `PV_AUTH_PROVIDER_AUDIENCE` unchanged to
     preserve audience/issuer guardrails.
   - Revert to standard provider-managed keyset immediately after outage closure.

## Role-Scoped Auth Token Controls

- [x] Auth token format is provider-issued JWT (`HS256`, `kid`) with deterministic checks.
- [x] Allowed personas are constrained to `engineer`, `reviewer`, `approver`.
- [x] `POST /api/v1/design-runs` requires `design_runs:write`.
- [x] `GET /api/v1/design-runs/{runId}` requires `design_runs:read` (or stronger write scope).
- [x] Invalid/missing token, expired token, invalid issuer/audience, and insufficient scope fail closed with `401`/`403`.

## Approval-Gate Security Audit Controls

- [x] Approval decisions emit `SecurityAuditEvent.v1` records.
- [x] Security audit record captures `actor`, `action`, `artifact`, and `decision`.
- [x] Security audit records are persisted in append-only workflow event storage.
- [x] Recovery path restores security audit records without mutation.
