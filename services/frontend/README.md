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

## Frontend service skeleton

- `/`: Prompt form route for collecting user input.
- `/result`: Result route that renders backend response output.
- `/api/prompt`: Local API route used as the DX-004 backend response placeholder.

## Run locally (hot reload)

From repository root:

```bash
npm --prefix services/frontend install
npm --prefix services/frontend run dev
```

Then open `http://localhost:3000`. The Next.js dev server supports hot reload for edits under `services/frontend/app/`.
