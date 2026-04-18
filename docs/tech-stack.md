# Tech Stack Contract (Open-Software Baseline)

This document is the repository source of truth for selected implementation technologies used by the agent-driven pressure vessel platform.

## Purpose

- Provide one canonical, reviewable stack selection for humans and agents.

- Reduce stack drift across features and pull requests.

- Require evidence-based change control for medium/high-risk technology decisions.

## Selection Matrix

| Layer | Selected Technology | Why Selected | Alternatives Considered | Owner | Upgrade Cadence |
|---|---|---|---|---|---|
| Frontend | Next.js + TypeScript | Mature ecosystem, strong DX, type safety | React + Vite, SvelteKit | Platform Eng | Quarterly minor, annual major review |
| Backend API | NestJS (Node.js + TypeScript) | Structured architecture and shared types with frontend | Fastify, FastAPI | Platform Eng | Quarterly minor, annual major review |
| Relational Data | PostgreSQL | ACID reliability and mature tooling | MariaDB, CockroachDB | Data Eng | Quarterly patch, semiannual major review |
| Cache/Queues | Redis | Fast caching and queue support | Valkey, RabbitMQ-only | Platform Eng | Quarterly patch |
| Knowledge Graph | Neo4j Community | Expressive graph traversals and mature graph tooling | JanusGraph, ArangoDB | Data Eng | Semiannual major review |
| Vector Retrieval | Qdrant | Open source, good hybrid retrieval support | Weaviate, Milvus | AI Eng | Quarterly minor |
| LLM Serving | vLLM | High-throughput open model serving | TGI, Ollama (dev) | AI Eng | Monthly patch, quarterly benchmark review |
| Open Models | Llama / Mistral / Qwen families | Strong capability with self-hosted options | Other OSS checkpoints | AI Eng | Monthly quality/safety benchmark review |
| Search/Analytics | OpenSearch | Search + analytics for artifacts and logs | Meilisearch, Solr | Platform Eng | Quarterly minor |
| Workflow Orchestration | Temporal | Durable orchestration and replay for agent workflows | Dagster, Prefect | Platform Eng | Quarterly minor |
| AuthN/AuthZ | Keycloak | Open standard IAM/SSO and policy control | Authentik | Security Eng | Quarterly minor |
| Observability | Prometheus + Grafana + Loki + Tempo | Open observability stack with metrics/logs/traces | Elastic stack | SRE | Quarterly minor |
| Secrets | Vault (OSS) or SOPS+age | Managed secret lifecycle and encryption at rest | External KMS only | Security Eng | Quarterly patch |
| IaC | OpenTofu (or Terraform OSS) | Repeatable environment management | Pulumi | Platform Eng | Quarterly minor |
| Containers/Runtime | Docker + Kubernetes | Portability and scale controls | Nomad + Podman | Platform Eng | Quarterly minor |

## Stack Change Policy

Any pull request that changes selected technologies must include:

1. An ADR in `docs/decision-log/`.

2. Benchmark or operational evidence for the change.

3. Security and compliance impact statement.

4. Migration and rollback plan.

## Validation Requirements for Stack Changes

- Functional: existing workflows remain operational.

- Non-functional: latency, throughput, and cost impact measured.

- Governance: approvals follow risk class and merge gates.

## Exit Strategy Requirements

For each selected component, maintain:

- data export strategy,

- replacement candidate,

- migration runbook link,

- maximum tolerated lock-in boundary.
