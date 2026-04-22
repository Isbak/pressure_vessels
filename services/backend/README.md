# Backend Service Skeleton

This directory is the bootstrap skeleton for the BL-018 platform backend runtime.

## Ownership boundary

- **Primary owner:** Platform Runtime Team.
- **Responsibility:** API orchestration, platform-side authn/authz hooks, and controlled data plane access.
- **Inbound contract:** Receives API requests from `services/frontend/` and automation clients.
- **Outbound contract:** Owns all access to PostgreSQL, Redis, Neo4j, Qdrant, and OpenSearch.

## Bootstrap structure

- `src/main.ts`: Backend API handlers and runtime adapter usage.
- `src/adapters/`: BL-047 adapter interfaces and runtime adapter implementations.
- `package.json`: Placeholder package metadata for deterministic bootstrapping.

## Backend API skeleton (DX-005, BL-047)

- `GET /health`
  - Returns backend service liveliness for local/runtime checks.
- `POST /api/v1/design-runs`
  - Starts design run and persists run state through configured adapters.
- `GET /api/v1/design-runs/{runId}`
  - Reads run status from adapter-backed runtime state.

See `docs/interfaces/backend_prompt_api_contract.md` for request/response details and fail-closed semantics.

## Required backend adapter environment variables

- `PV_POSTGRES_URL`
- `PV_POSTGRES_SCHEMA`
- `PV_REDIS_URL`
- `PV_REDIS_NAMESPACE`

If any required variable is missing, design-run endpoints fail closed with `503`.

## Optional platform integration interface variables

Each integration defaults to deterministic fallback mode and can be promoted to required mode.

- Neo4j: `PV_NEO4J_MODE`, `PV_NEO4J_ENDPOINT`, `PV_NEO4J_TOKEN`
- Qdrant: `PV_QDRANT_MODE`, `PV_QDRANT_ENDPOINT`, `PV_QDRANT_API_KEY`
- OpenSearch: `PV_OPENSEARCH_MODE`, `PV_OPENSEARCH_ENDPOINT`, `PV_OPENSEARCH_API_KEY`
- Temporal: `PV_TEMPORAL_MODE`, `PV_TEMPORAL_ENDPOINT`, `PV_TEMPORAL_TOKEN`
- LLM serving: `PV_LLM_SERVING_MODE`, `PV_LLM_SERVING_ENDPOINT`, `PV_LLM_SERVING_API_KEY`

## Local integration profile server

DX-006 adds `local-integration-server.js` as a dependency-free local runtime entrypoint for Docker Compose integration runs.

Run directly (without compose) from repository root:

```bash
BACKEND_HOST=0.0.0.0 BACKEND_PORT=8000 node services/backend/local-integration-server.js
```
