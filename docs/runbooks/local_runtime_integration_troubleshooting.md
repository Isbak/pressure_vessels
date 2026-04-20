# Local Runtime Integration Troubleshooting (DX-006)

This runbook covers the DX-006 local frontend/backend integration profile.

## Scope

- Profile file: `infra/local/docker-compose.integration.yml`
- Startup command: `make integration-up` (alias: `make up`)
- Ownership boundaries: frontend remains browser-facing only, backend remains API/data-plane boundary.

## Environment variables and dependencies

Copy `.env.example` to `.env` before startup to keep profile configuration predictable across hosts:

```bash
cp .env.example .env
```

| Variable | Default | Required | Notes |
| --- | --- | --- | --- |
| `FRONTEND_PORT` | `3000` | No | Host port mapped to Next.js dev server. |
| `BACKEND_PORT` | `8000` | No | Host port mapped to backend local integration server. |
| `BACKEND_API_BASE_URL` | `http://backend:8000` | No | Set in compose for frontend container; points to backend service on compose network. |
| `BACKEND_HOST` | `0.0.0.0` | No | Backend bind host in container. |

Service dependencies:

1. `backend` starts first and must pass `GET /health`.
2. `frontend` starts after backend healthcheck succeeds.
3. Browser traffic hits frontend (`http://localhost:${FRONTEND_PORT}`), and frontend BFF calls backend (`/api/prompt` forwarding to `BACKEND_API_BASE_URL`).

## Standard start/stop commands

Start local integration profile:

```bash
make integration-up
```

Stop and remove containers:

```bash
make integration-down
```

Tail logs while debugging:

```bash
make integration-logs
```

## Troubleshooting matrix

### 1) `docker compose` command not found

- Symptom: `make integration-up` fails immediately with a compose command error.
- Fix: install Docker Desktop (or Docker Engine + Compose plugin), then rerun `make integration-up`.

### 2) Frontend fails while installing dependencies

- Symptom: frontend container exits during `npm install`.
- Checks:
  1. Confirm network access to npm registry.
  2. Re-run `make integration-up` and inspect frontend logs.
- Fix: resolve npm/network issue and restart with `make integration-up`.

### 3) Frontend can load `/` but prompt call fails

- Symptom: `/result` shows backend fetch failure.
- Checks:
  1. `curl http://localhost:${BACKEND_PORT:-8000}/health`
  2. `curl "http://localhost:${BACKEND_PORT:-8000}/api/prompt?prompt=test"`
  3. `make integration-logs` and inspect backend/frontend output.
- Fix:
  - If backend health fails, restart profile with `make integration-down && make integration-up`.
  - If host ports conflict, choose new ports (example: `FRONTEND_PORT=3100 BACKEND_PORT=8100 make integration-up`).

### 4) Port conflict on startup

- Symptom: bind error for `:3000` or `:8000`.
- Fix: set custom host ports before start:

```bash
FRONTEND_PORT=3100 BACKEND_PORT=8100 make integration-up
```

### 5) Need a clean restart

Use:

```bash
make integration-down
make integration-up
```

If stale dependencies persist, remove containers/volumes from Docker tooling and rerun startup.
