# Platform Runtime Stack Operations Runbook (BL-018)

This runbook defines BL-018 runtime foundation ownership and deployment operations.

## Service Ownership Boundaries

| Service/module | Owner | Boundary |
| --- | --- | --- |
| `services/frontend` | Platform Experience Team | Browser and operator workflows; no direct datastore access. |
| `services/backend` | Platform Runtime Team | API orchestration and all data plane access. |
| `infra/platform/*` | Platform Runtime + domain teams | Environment modules, deploy orchestration, and infrastructure lifecycle. |
| `infra/platform/postgresql` | Data Platform Team + owning domain teams | Relational schema ownership boundaries, migration approvals, backup lifecycle defaults. |
| `infra/platform/redis` | Data Platform Team + owning domain teams | Cache namespace and queue stream ownership boundaries, retention defaults, and persistence mode by environment. |
| `infra/platform/runtime` | Platform Runtime Team + Platform Experience Team | Docker/Kubernetes deployment target ownership, rollout lifecycle, and release evidence boundaries. |
| `infra/platform/keycloak` | Security Platform Team + consuming service teams | Realm, client, and role ownership boundaries with promotion and break-glass lifecycle controls. |
| `infra/platform/temporal` | Orchestration Platform Team + Platform Runtime Team | Temporal namespace, task queue, and worker ownership boundaries with rollout and recovery controls. |
| `infra/platform/neo4j` | Knowledge Platform Team + Platform Runtime Team | Neo4j database, graph schema, and access ownership boundaries with revisioned write controls. |
| `infra/platform/qdrant` | Retrieval Platform Team + Platform Runtime Team | Qdrant collection, indexing lifecycle, and access ownership boundaries with deterministic embedding version controls. |
| `infra/platform/opensearch` | Retrieval Platform Team + Platform Runtime Team | OpenSearch index, retention, and access ownership boundaries with deterministic lifecycle policy controls. |
| `infra/platform/vllm` | AI Platform Team + Platform Runtime Team | vLLM endpoint, capacity envelope, and access ownership boundaries with deterministic inference policy controls. |

## Environment Provisioning Inputs

1. `docs/platform_runtime_stack_registry.yaml` declares each stack component, status, and module mapping.
2. `infra/platform/environment.bootstrap.yaml` binds components to target environments.
3. `infra/platform/iac/module.primitives.yaml` defines reusable IaC provisioning primitives shared across environments.
4. `infra/platform/secrets/module.boundaries.yaml` defines issuance and encryption boundaries for provider-neutral secret handling.
5. `infra/platform/observability/module.boundaries.yaml` defines metrics/logs/traces/dashboard boundaries and incident signal inventory.
6. `infra/platform/postgresql/module.boundaries.yaml` defines datastore schema ownership, migration approval, and backup lifecycle boundaries.
7. `infra/platform/redis/module.boundaries.yaml` defines queue/cache ownership, retention defaults, and persistence boundaries.
8. `infra/platform/runtime/module.boundaries.yaml` defines Docker/Kubernetes target ownership, rollout lifecycle, and release evidence boundaries.
9. `infra/platform/keycloak/module.boundaries.yaml` defines Keycloak realm/client/role ownership and identity lifecycle boundaries.
10. `infra/platform/temporal/module.boundaries.yaml` defines Temporal namespace, task queue, and worker ownership and lifecycle boundaries.
11. `infra/platform/neo4j/module.boundaries.yaml` defines Neo4j database, graph schema, and access ownership and lifecycle boundaries.
12. `infra/platform/qdrant/module.boundaries.yaml` defines Qdrant collection, indexing lifecycle, and access ownership and lifecycle boundaries.
13. `infra/platform/opensearch/module.boundaries.yaml` defines OpenSearch index ownership, retention lifecycle, and access ownership boundaries.
14. `infra/platform/vllm/module.boundaries.yaml` defines vLLM endpoint ownership, capacity envelope, and access ownership boundaries.
15. `scripts/check_tech_stack.py` enforces that every declared stack component is mapped and marked `deployed` or `planned`.
16. `scripts/check_tech_stack.py` deterministically requires `iac-opentofu-or-terraform` to be `deployed` when the IaC module path exists.

## Deployment Readiness Checklist

- Validate stack declarations:
  - `python scripts/check_tech_stack.py`
- Confirm skeleton service boundaries are present:
  - `test -f services/frontend/README.md`
  - `test -f services/backend/README.md`
- Confirm bootstrap environment manifest exists:
  - `test -f infra/platform/environment.bootstrap.yaml`
- Confirm IaC foundation module exists:
  - `test -f infra/platform/iac/module.primitives.yaml`
- Confirm secrets boundary module exists:
  - `test -f infra/platform/secrets/module.boundaries.yaml`
- Confirm observability boundary module exists:
  - `test -f infra/platform/observability/module.boundaries.yaml`
- Confirm datastore boundary module exists:
  - `test -f infra/platform/postgresql/module.boundaries.yaml`
- Confirm cache/queue boundary module exists:
  - `test -f infra/platform/redis/module.boundaries.yaml`
- Confirm runtime deployment boundary module exists:
  - `test -f infra/platform/runtime/module.boundaries.yaml`
- Confirm identity boundary module exists:
  - `test -f infra/platform/keycloak/module.boundaries.yaml`
- Confirm workflow orchestration boundary module exists:
  - `test -f infra/platform/temporal/module.boundaries.yaml`
- Confirm knowledge graph boundary module exists:
  - `test -f infra/platform/neo4j/module.boundaries.yaml`
- Confirm vector retrieval boundary module exists:
  - `test -f infra/platform/qdrant/module.boundaries.yaml`
- Confirm search/analytics boundary module exists:
  - `test -f infra/platform/opensearch/module.boundaries.yaml`
- Confirm LLM serving boundary module exists:
  - `test -f infra/platform/vllm/module.boundaries.yaml`

## Incident Operations

- Required incident signals exposed by observability module:
  - `service_error_rate_high`
  - `api_latency_slo_breach`
  - `workflow_backlog_growth`
  - `secrets_resolution_failures`
  - `deployment_rollout_failures`
- If component state changes from `planned` to `deployed`, update both:
  - `docs/platform_runtime_stack_registry.yaml`
  - `docs/tech-stack.md`
- Re-run CI gate before merge to keep stack contract consistent.
