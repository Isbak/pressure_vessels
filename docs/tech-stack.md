# Tech Stack Contract

This document mixes deployed and planned capabilities; see section headers.

## Current

Technologies below are present in this repository today via imports and/or direct invocation under `src/`, `tests/`, `scripts/`, or `.github/workflows/`.

- Python 3.11 runtime for package and CI execution (`pyproject.toml:9`, `.github/workflows/ci.yml:47`).
- `setuptools` build backend for packaging (`pyproject.toml:2`, `pyproject.toml:3`).
- `wheel` build dependency for package builds (`pyproject.toml:2`).
- `pytest` test runner invoked by CI and imported by tests (`.github/workflows/ci.yml:52`, `tests/test_calculation_pipeline.py:5`).
- Ruby runtime used for YAML validation in CI (`.github/workflows/ci.yml:29`).
- Repository policy scripts executed in CI (`scripts/check_ci_governance.py:1`, `.github/workflows/ci.yml:115`).

### Current Python dependencies declared in `pyproject.toml`

- None. `dependencies = []` and `src/` currently uses only standard library + local package imports (`pyproject.toml:10`, `src/pressure_vessels/requirements_pipeline.py:5`).

## Planned

The technologies below are documented target-state components and are **not** currently deployed in this codebase. Each item references the backlog work item that introduces it.

- Next.js + TypeScript frontend (BL-018).
- NestJS (Node.js + TypeScript) backend API (BL-018).
- PostgreSQL relational store (BL-018).
- Redis cache/queue layer (BL-018).
- Neo4j knowledge graph (BL-006).
- Qdrant vector retrieval (BL-018).
- vLLM model serving (BL-018).
- Llama / Mistral / Qwen model families (BL-018).
- OpenSearch search/analytics layer (BL-018).
- Temporal workflow orchestration (BL-016).
- Keycloak AuthN/AuthZ (BL-018).
- Prometheus + Grafana + Loki + Tempo observability stack (BL-018).
- Vault (OSS) or SOPS+age secrets management (BL-018).
- OpenTofu (or Terraform OSS) infrastructure as code (BL-018).
- Docker + Kubernetes runtime platform (BL-018).

## Stack Change Policy

Any pull request that changes selected technologies must include:

1. An ADR in `docs/decision-log/`.
2. Benchmark or operational evidence for the change.
3. Security and compliance impact statement.
4. Migration and rollback plan.
