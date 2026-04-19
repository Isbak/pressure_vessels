# Backend Service Skeleton

This directory is the bootstrap skeleton for the BL-018 platform backend runtime.

## Ownership boundary

- **Primary owner:** Platform Runtime Team.
- **Responsibility:** API orchestration, platform-side authn/authz hooks, and controlled data plane access.
- **Inbound contract:** Receives API requests from `services/frontend/` and automation clients.
- **Outbound contract:** Owns all access to PostgreSQL, Redis, Neo4j, Qdrant, and OpenSearch.

## Bootstrap structure

- `src/main.ts`: Minimal backend API handlers with deterministic local behavior.
- `package.json`: Placeholder package metadata for deterministic bootstrapping.

## Backend API skeleton (DX-005)

- `GET /health`
  - Returns backend service liveliness for local/runtime checks.
- `GET /api/prompt?prompt=<text>`
  - Deterministic pipeline route used by frontend integration in DX-005.

See `docs/interfaces/backend_prompt_api_contract.md` for request/response details.
