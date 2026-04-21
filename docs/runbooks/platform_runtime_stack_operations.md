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
| `infra/platform/model-catalog` | AI Platform Team | Approved model families, version policy, and serving consumption contract boundaries. |

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
15. `infra/platform/model-catalog/module.boundaries.yaml` defines approved model families, version policy, and vLLM consumption contract boundaries.
16. `infra/platform/infra_boundary_files.manifest` is the make-based stack check source of truth for required infra boundary files (one path per line).
17. `scripts/check_tech_stack.py` enforces that every declared stack component is mapped and marked `deployed`, `scaffolded`, or `planned`.
18. `scripts/check_tech_stack.py` deterministically requires `iac-opentofu-or-terraform` to be `scaffolded` until Terraform/OpenTofu HCL exists under `infra/platform/iac`, then `deployed`.
19. `docs/runbooks/preview_environment_lifecycle_operations.md` defines deterministic ephemeral preview launch/teardown controls for pull requests.

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
- Confirm model catalog boundary module exists:
  - `test -f infra/platform/model-catalog/module.boundaries.yaml`

## Incident Operations

- Required incident signals exposed by observability module:
  - `service_error_rate_high`
  - `api_latency_slo_breach`
  - `workflow_backlog_growth`
  - `secrets_resolution_failures`
  - `deployment_rollout_failures`
- If component state changes (for example `scaffolded` to `deployed`), update both:
  - `docs/platform_runtime_stack_registry.yaml`
  - `docs/tech-stack.md`
- Re-run CI gate before merge to keep stack contract consistent.

## BL-039 Runtime SLOs and Deterministic Measurement Windows

The runtime stack publishes the following service-level objectives against deterministic windows:

| SLO ID | Objective | Metric name | Window | Deterministic measurement rule |
| --- | --- | --- | --- | --- |
| `slo.orchestration_latency` | P95 orchestration latency ≤ 5000 ms | `orchestration_latency_ms` | rolling 30 days | Derived from per-stage deterministic latency events (`stage_latency_ms`) aggregated per workflow run. |
| `slo.run_success_rate` | Successful workflow runs ≥ 99.5% | `run_success_ratio` | rolling 30 days | `1.0` for runs without terminal failure/escalation; `0.0` otherwise. |
| `slo.artifact_export_success` | Artifact export success ≥ 99.9% | `artifact_export_success_ratio` | rolling 30 days | `1.0` when all `*export*`/`*publish*` stages complete; `0.0` otherwise. |

Dashboard coverage (required panels):

1. `pv-runtime-overview`:
   - SLO burn-down panel for the three SLO metrics above.
   - Stage-level RED panels: `stage_requests_total`, `stage_errors_total`, `stage_latency_ms`.
2. `pv-runtime-capacity`:
   - Stage-level USE panels: `worker_utilization_ratio`, `retry_budget_saturation_ratio`, `worker_error_ratio`.
   - Saturation heatmap by `stage_id` for retry pressure.

## BL-039 Alert Routing Matrix and Incident Drill Coverage

| Alert | Trigger | Route | Escalation SLA |
| --- | --- | --- | --- |
| `api_latency_slo_breach` | `orchestration_latency_ms` exceeds objective for 3 consecutive windows | Platform Runtime primary on-call | 15 minutes |
| `workflow_run_success_breach` | `run_success_ratio` drops below objective over rolling window | Platform Runtime primary on-call, then Engineering Reviewer | 15 minutes / 60 minutes |
| `artifact_export_success_breach` | `artifact_export_success_ratio` drops below objective over rolling window | Reporting Operations on-call + Platform Runtime secondary | 15 minutes / 60 minutes |
| `workflow_backlog_growth` | queue depth or retry saturation exceeds threshold | Orchestration Platform on-call | 30 minutes |

Simulated failure drill evidence is recorded in:

- `docs/incidents/2026-04-21_bl-039_incident_drill.md`

The drill validates:

1. alert routing dispatch to primary + secondary responders,
2. runbook execution timeline with deterministic timestamps,
3. closure criteria and follow-up action capture.
