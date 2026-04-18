# Backend Service Skeleton

This directory is the bootstrap skeleton for the BL-018 platform backend runtime.

## Ownership boundary

- **Primary owner:** Platform Runtime Team.
- **Responsibility:** API orchestration, platform-side authn/authz hooks, and controlled data plane access.
- **Inbound contract:** Receives API requests from `services/frontend/` and automation clients.
- **Outbound contract:** Owns all access to PostgreSQL, Redis, Neo4j, Qdrant, and OpenSearch.

## Bootstrap structure

- `src/main.ts`: NestJS-style entrypoint placeholder.
- `package.json`: Placeholder package metadata for deterministic bootstrapping.
