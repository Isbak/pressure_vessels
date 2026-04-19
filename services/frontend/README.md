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
- `/api/prompt`: Frontend BFF route for prompt execution. It forwards to backend when configured and otherwise serves a local placeholder response.

## Run locally (hot reload)

From repository root:

```bash
npm --prefix services/frontend install
npm --prefix services/frontend run dev
```

Then open `http://localhost:3000`. The Next.js dev server supports hot reload for edits under `services/frontend/app/`.

### Optional backend wiring

Set `BACKEND_API_BASE_URL` to connect the frontend BFF route to a backend service.

Example:

```bash
BACKEND_API_BASE_URL=http://localhost:8000 npm --prefix services/frontend run dev
```

When this variable is not set (or the backend is unavailable), `/api/prompt` returns a deterministic placeholder response so the local developer loop still works.
