# Tech Stack Contract

This document defines declared stack components and their implementation state.

## Current

Technologies below are present in this repository today via imports and/or direct invocation under `src/`, `tests/`, `scripts/`, `.github/workflows/`, or in-repo runtime skeletons.

- Python 3.11 runtime for package and CI execution (`pyproject.toml:9`, `.github/workflows/ci.yml:47`).
- `setuptools` build backend for packaging (`pyproject.toml:2`, `pyproject.toml:3`).
- `wheel` build dependency for package builds (`pyproject.toml:2`).
- `pytest` test runner invoked by CI and imported by tests (`.github/workflows/ci.yml:52`, `tests/test_calculation_pipeline.py:5`).
- Ruby runtime used for YAML validation in CI (`.github/workflows/ci.yml:29`).
- Repository policy scripts executed in CI (`scripts/check_ci_governance.py:1`, `.github/workflows/ci.yml:115`).

### Runtime stack components (deployed)

- Component: `frontend-nextjs`
- Component: `backend-nestjs`
- Component: `datastore-postgresql`
- Component: `cache-redis`
- Component: `iac-opentofu-or-terraform`
- Component: `secrets-vault-or-sops-age`
- Component: `observability-prometheus-grafana-loki-tempo`
- Component: `runtime-docker-kubernetes`
- Component: `auth-keycloak`
- Component: `workflow-temporal`
- Component: `graph-neo4j`
- Component: `retrieval-qdrant`
- Component: `search-opensearch`
- Component: `llm-serving-vllm`
- Component: `models-llama-mistral-qwen`

## Planned

The technologies below are documented target-state components and are **not** currently deployed in this codebase.

### Runtime stack components (planned)

- None currently.

### Runtime mapping source of truth

- `docs/platform_runtime_stack_registry.yaml` maps each component to ownership, module path, and deployment status.
- `infra/platform/environment.bootstrap.yaml` maps component modules to deployable environments.

## Stack Change Policy

Any pull request that changes selected technologies must include:

1. An ADR in `docs/decision-log/`.
2. Benchmark or operational evidence for the change.
3. Security and compliance impact statement.
4. Migration and rollback plan.
