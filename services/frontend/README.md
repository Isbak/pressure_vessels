# Frontend Service Skeleton

This directory is the bootstrap skeleton for the BL-018 platform frontend runtime.

## Ownership boundary

- **Primary owner:** Platform Experience Team.
- **Responsibility:** UI composition, operator workflows, and browser-facing integration.
- **Inbound contract:** Calls backend APIs exposed by `services/backend/`.
- **Outbound contract:** No direct datastore access; all writes flow through backend APIs.

## Bootstrap structure

- `app/`: Next.js App Router placeholder.
- `package.json`: Placeholder package metadata for deterministic bootstrapping.
