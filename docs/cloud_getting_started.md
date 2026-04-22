# Cloud Getting Started Guide (Cloud-Agnostic First)

This guide provides a pragmatic, cloud-agnostic path for deploying this platform on **AWS, Azure, or Google Cloud** while keeping portability, traceability, and compliance as first-class requirements.

## 1. Guiding Principles (Cloud-Agnostic)

1. **Design for portability at boundaries**
   - Keep business logic in containerized services.
   - Use open interfaces (HTTP/gRPC, OpenAPI, AsyncAPI) between modules.
   - Avoid provider-specific features in core domain services unless there is a clear, documented tradeoff.

2. **Treat platform controls as product requirements**
   - Identity, auditability, encryption, backup/restore, and policy checks are part of the design tool's acceptance criteria.

3. **Everything as code**
   - Infrastructure as Code (IaC), policy-as-code, and pipeline-as-code should be versioned with reviews.

4. **Separation of concerns**
   - Keep compute/orchestration, data stores, secrets, observability, and networking loosely coupled behind explicit contracts.

5. **Evidence-driven operations**
   - Every deployment should emit evidence: version, migration status, policy checks, smoke tests, and rollback references.

---

## 2. Reference Deployment Pattern

Use the same logical architecture in every cloud:

- **Ingress/API layer** for UI + service APIs.
- **Workflow orchestration** for agent sequencing.
- **Stateless service tier** for parser, design basis, calculations, compliance, documentation.
- **Stateful data tier** for relational/project data, graph/knowledge data, object artifacts, and cache.
- **Observability + audit tier** for logs, metrics, traces, and audit events.
- **Security tier** for IAM, secrets, keys, and policy enforcement.

> Practical rule: if a module can be swapped from one cloud to another with only IaC and configuration changes, your boundary is healthy.

---

## 3. Service Mapping by Cloud (Example Choices)

You can start with managed services per cloud and keep interfaces provider-neutral.

| Capability | AWS | Azure | Google Cloud |
|---|---|---|---|
| Managed Kubernetes | EKS | AKS | GKE |
| Container registry | ECR | ACR | Artifact Registry |
| API ingress | API Gateway / ALB | API Management / Application Gateway | API Gateway / Load Balancing |
| Object storage | S3 | Blob Storage | Cloud Storage |
| Relational DB | RDS (PostgreSQL) | Azure Database for PostgreSQL | Cloud SQL (PostgreSQL) |
| Cache | ElastiCache (Redis) | Azure Cache for Redis | Memorystore (Redis) |
| Secrets | Secrets Manager / SSM | Key Vault | Secret Manager |
| Key management | KMS | Key Vault Keys | Cloud KMS |
| Identity federation | IAM + IAM Identity Center | Microsoft Entra ID | IAM + Cloud Identity |
| Logs/metrics/traces | CloudWatch/X-Ray | Azure Monitor / App Insights | Cloud Logging/Monitoring/Trace |

Use this as a starting point, not a lock-in plan.

### 3.1 On-Prem Primer (for Hybrid or Regulated Deployments)

If you need to run fully on-prem or in a hybrid model, use the same contracts and swap managed services for self-hosted equivalents.

| Capability | Cloud-Managed Pattern | On-Prem Primer |
|---|---|---|
| Container orchestration | EKS/AKS/GKE | Kubernetes distribution (upstream, OpenShift, Rancher-managed, etc.) |
| Container registry | ECR/ACR/Artifact Registry | Harbor, JFrog Artifactory, GitLab Container Registry |
| Relational DB | Managed PostgreSQL | PostgreSQL HA cluster (Patroni/Stolon or managed appliance equivalent) |
| Object storage | S3/Blob/Cloud Storage | S3-compatible storage (e.g., MinIO, Ceph RGW) |
| Secrets & keys | Cloud secrets + KMS | Vault/HSM-backed key management with strict RBAC |
| Observability | Cloud monitoring suites | OpenTelemetry + Prometheus + Grafana + centralized logs |
| Identity federation | Cloud IAM/SSO | Entra/AD/LDAP + OIDC/SAML federation |

On-prem checklist:

- Provide the same `dev`/`staging`/`prod` segmentation as cloud environments.
- Validate backup, restore, and failover using realistic recovery drills.
- Use workload identity where possible; avoid static credentials in applications.
- Keep IaC and policy-as-code even if provisioning targets VMware/bare metal.
- Document hardware and capacity envelopes as part of release evidence.

---

## 4. Phase-by-Phase Rollout

### Phase 0 — Landing Zone and Guardrails

- Create separate accounts/subscriptions/projects for `dev`, `staging`, and `prod`.
- Enforce baseline policies:
  - Encryption at rest and in transit.
  - No public data stores by default.
  - Mandatory tags/labels (project, owner, environment, data classification).
  - Audit log retention policy.
- Configure centralized identity with SSO and least-privilege role mapping.

### Phase 1 — Core Platform Runtime

- Provision Kubernetes cluster (or equivalent container runtime).
- Deploy ingress, certificate management, and DNS.
- Establish CI/CD pipeline for images and deployments.
- Deploy foundational services first:
  - secrets integration,
  - observability stack,
  - base network policies.

### Phase 2 — Data Plane

- Deploy relational database with:
  - private networking,
  - automated backups,
  - tested restore process,
  - migration pipeline.
- Deploy object storage buckets/containers with lifecycle policies.
- Add cache and (if needed) graph/search services.

### Phase 3 — Application Modules

- Deploy modular services from this repository's architecture:
  - requirements parser,
  - design basis,
  - calculation engine,
  - compliance/traceability,
  - reporting.
- Add canary or blue/green rollout strategy.
- Enable feature flags for risky capabilities.

### Phase 4 — Reliability and Governance Hardening

- Define SLOs (availability, latency, error budget).
- Enable autoscaling and capacity policies.
- Run game days for incident response and disaster recovery.
- Add policy gates (security scans, IaC compliance, dependency risk) in CI.

---

## 5. Cloud-Agnostic Architecture Decisions to Make Early

1. **Kubernetes vs serverless containers**
   - If you need maximum portability and consistent control planes, prefer Kubernetes.

2. **Database portability strategy**
   - Standardize on PostgreSQL-compatible features only.
   - Avoid provider-specific SQL extensions in core schemas.

3. **Eventing and workflow contracts**
   - Use explicit event schemas and versioning regardless of cloud-native bus choice.

4. **Identity and authorization model**
   - Implement app-level RBAC/ABAC claims independent from cloud IAM internals.

5. **Artifact and evidence formats**
   - Keep artifacts in open formats (JSON, PDF, CSV) with stable schema versions.

---

## 6. Security Baseline Checklist

- Private-by-default networking for runtime and data stores.
- End-to-end TLS and cert rotation.
- Secrets never committed to source control.
- KMS-backed encryption keys and rotation schedule.
- Workload identity (no long-lived static cloud keys in workloads).
- Immutable deployment artifacts (signed images recommended).
- Vulnerability scanning in CI and at registry.
- Centralized audit trail for user and agent actions.

---

## 7. Reliability and DR Baseline

- Multi-AZ/zonal high availability for runtime and data.
- Defined RPO/RTO per environment.
- Automated backups + periodic restore drills.
- Versioned IaC and tested environment recreation.
- Runbook-driven response for:
  - failed deploy,
  - data corruption,
  - region degradation,
  - secrets compromise.

---

## 8. Cost and FinOps Baseline

- Enforce labels/tags for showback/chargeback.
- Set budgets and anomaly alerts per environment.
- Right-size cluster nodes and autoscaling bounds.
- Use storage lifecycle tiers for artifacts.
- Periodically review idle resources and overprovisioned databases.

---

## 9. Suggested 30/60/90-Day Adoption Plan

### First 30 days

- Stand up landing zone and baseline security controls.
- Deploy dev environment with one end-to-end workflow.
- Capture deployment evidence and rollback process.

### Day 31-60

- Add staging with production-like controls.
- Implement policy gates and vulnerability scanning.
- Validate backup/restore and migration rollback.

### Day 61-90

- Production rollout with SLOs, on-call runbooks, and DR tests.
- Optimize cost and autoscaling behavior.
- Freeze v1 cloud-agnostic platform contract documentation.

---

## 10. “Portable by Design” Definition of Done

You are cloud-agnostic enough when:

- Core services run unchanged as containers across AWS/Azure/GCP.
- Data schema and migrations run on PostgreSQL-compatible managed DBs in each cloud.
- CI/CD pipeline can target all three clouds via environment config, not code rewrites.
- Security, audit, and traceability controls are enforced in every environment.
- Disaster recovery exercises are repeatable and evidenced.

---

## 11. Railway Deployment Guide (Backend-First Full Rollout)

Use this flow for BL-049 production-oriented Railway deployments where frontend
and backend are separate services in the same Railway project.

### 11.1 Service topology and rollout order

1. Deploy and validate `backend` service first.
2. Deploy `frontend` service second and set `BACKEND_API_BASE_URL` to backend
   private domain (preferred) or public Railway URL.
3. Promote optional staging-only integrations (for example
   `llm-serving-railway`) only after backend core checks pass.

> Bootstrap placeholder behavior vs production integration:
>
> - **Bootstrap placeholder**: frontend may run with `BACKEND_API_BASE_URL`
>   unset, and `/api/prompt` returns deterministic placeholder responses.
> - **Production-integrated backend**: frontend `BACKEND_API_BASE_URL` is set,
>   backend design-run endpoints are authenticated, and backend adapters use
>   PostgreSQL/Redis runtime state (fail-closed if required configuration is
>   missing).

### 11.2 Railway process mapping

- Root `Procfile` defines both process types:
  - `web`: `cd services/frontend && npm ci && npm run build && npm run start -- --hostname 0.0.0.0 --port ${PORT:-3000}`
  - `backend`: `cd services/backend && npm ci && BACKEND_HOST=0.0.0.0 BACKEND_PORT=${BACKEND_PORT:-8000} node local-integration-server.js`
- In full rollout mode, scale both `web` and `backend` as dedicated Railway
  services. Do not rely on frontend-only single-service mode for production.

### 11.3 Environment-variable matrix (contract-aligned)

Use service-scoped variables. Required values come from backend API contract and
`infra/platform/environment.bootstrap.yaml`.

| Railway service | Variable | Required | Example value | Notes |
| --- | --- | --- | --- | --- |
| `frontend` | `NODE_ENV` | Yes | `production` | Next.js runtime mode. |
| `frontend` | `BACKEND_API_BASE_URL` | Yes (full rollout) | `https://backend.railway.internal` | Internal Railway DNS is preferred for cross-service calls. |
| `backend` | `PV_AUTH_PROVIDER_ISSUER` | Yes | `https://keycloak.example.com/realms/pv` | JWT issuer validation (BL-048). |
| `backend` | `PV_AUTH_PROVIDER_AUDIENCE` | Yes | `pressure-vessels-backend` | JWT audience validation (BL-048). |
| `backend` | `PV_AUTH_PROVIDER_JWKS_JSON` | Yes | `<jwks-json-from-secrets-module>` | Provider keyset for token verification (BL-048). |
| `backend` | `PV_BACKEND_AUTH_TOKEN_SECRET` | Yes | `replace-with-long-random-secret` | Legacy bootstrap secret remains required by runtime baseline. |
| `backend` | `PV_POSTGRES_URL` | Yes | `postgresql://...` | Required for backend design-run persistence (BL-047). |
| `backend` | `PV_POSTGRES_SCHEMA` | Yes | `public` | Required PostgreSQL adapter schema. |
| `backend` | `PV_REDIS_URL` | Yes | `redis://...` | Required for backend run-status cache. |
| `backend` | `PV_REDIS_NAMESPACE` | Yes | `pv` | Required Redis namespace for deterministic keying. |
| `backend` | `BACKEND_HOST` | No | `0.0.0.0` | Bind host. |
| `backend` | `BACKEND_PORT` | No | `8000` | Explicit backend runtime port. |

### 11.3.1 Copy/paste starter blocks (Railway dashboard)

Use these as starter values when populating Railway service variables.
Replace placeholders before deployment.

Backend service (required first):

```bash
PV_AUTH_PROVIDER_ISSUER=https://<your-keycloak-host>/realms/pv
PV_AUTH_PROVIDER_AUDIENCE=pressure-vessels-backend
PV_AUTH_PROVIDER_JWKS_JSON={"keys":[{"kid":"<kid>","alg":"HS256","k":"<base64url-secret>"}]}
PV_BACKEND_AUTH_TOKEN_SECRET=<long-random-secret>
PV_POSTGRES_URL=postgresql://<user>:<password>@<host>:<port>/<database>
PV_POSTGRES_SCHEMA=public
PV_REDIS_URL=redis://<host>:<port>
PV_REDIS_NAMESPACE=pv
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
```

Frontend service:

```bash
NODE_ENV=production
BACKEND_API_BASE_URL=https://backend.railway.internal
```

### 11.4 Optional staging-only dependencies

Staging may add platform integrations while keeping production cutover
controlled and fail-closed:

- `llm-serving-railway` (`PV_LLM_SERVING_MODE`, `PV_LLM_SERVING_ENDPOINT`,
  `PV_LLM_SERVING_API_KEY`)
- `graph-neo4j` (`PV_NEO4J_MODE`, `PV_NEO4J_ENDPOINT`, `PV_NEO4J_TOKEN`)
- `retrieval-qdrant` (`PV_QDRANT_MODE`, `PV_QDRANT_ENDPOINT`,
  `PV_QDRANT_API_KEY`)
- `search-opensearch` (`PV_OPENSEARCH_MODE`, `PV_OPENSEARCH_ENDPOINT`,
  `PV_OPENSEARCH_API_KEY`)
- `workflow-temporal` (`PV_TEMPORAL_MODE`, `PV_TEMPORAL_ENDPOINT`,
  `PV_TEMPORAL_TOKEN`)

Recommendation: set optional services to `deterministic-fallback` until each
endpoint + credential pair is validated in staging.

Optional staging integration starter block:

```bash
PV_LLM_SERVING_MODE=deterministic-fallback
PV_LLM_SERVING_ENDPOINT=https://<llm-serving-url>
PV_LLM_SERVING_API_KEY=<secret>
PV_NEO4J_MODE=deterministic-fallback
PV_NEO4J_ENDPOINT=bolt://<neo4j-host>:7687
PV_NEO4J_TOKEN=<secret>
PV_QDRANT_MODE=deterministic-fallback
PV_QDRANT_ENDPOINT=https://<qdrant-host>
PV_QDRANT_API_KEY=<secret>
PV_OPENSEARCH_MODE=deterministic-fallback
PV_OPENSEARCH_ENDPOINT=https://<opensearch-host>
PV_OPENSEARCH_API_KEY=<secret>
PV_TEMPORAL_MODE=deterministic-fallback
PV_TEMPORAL_ENDPOINT=<temporal-endpoint>
PV_TEMPORAL_TOKEN=<secret>
```

### 11.5 Backend deployment checklist (Railway)

1. Confirm backend required env vars are present before first deploy:
   - `PV_AUTH_PROVIDER_ISSUER`, `PV_AUTH_PROVIDER_AUDIENCE`,
     `PV_AUTH_PROVIDER_JWKS_JSON`, `PV_BACKEND_AUTH_TOKEN_SECRET`,
     `PV_POSTGRES_URL`, `PV_POSTGRES_SCHEMA`, `PV_REDIS_URL`,
     `PV_REDIS_NAMESPACE`.
2. Deploy `backend` service and run health check:
   - `GET /health` returns `200` with `{"service":"pressure-vessels-backend","status":"ok"}`.
3. Run auth and smoke checks against backend:
   - `POST /api/v1/design-runs` with valid JWT and payload returns `201`.
   - `GET /api/v1/design-runs/{runId}` with valid JWT returns `200`.
   - Missing required adapter vars must return deterministic `503`.
4. Deploy/update `frontend` service and set `BACKEND_API_BASE_URL`.
5. Validate frontend-to-backend networking by executing one complete
   `/api/prompt` flow from UI.

### 11.6 Release verification, rollback, and evidence capture

Release verification checks:

- Backend health and auth-protected smoke checks pass.
- Frontend `/api/prompt` calls backend successfully over configured
  cross-service network path.
- Railway deployment logs show no adapter/auth bootstrap failures.

Rollback steps:

1. Roll back `frontend` to last known-good release if API integration fails.
2. Roll back `backend` to prior Railway deployment if health/auth/smoke checks fail.
3. Revert changed environment variables to last approved values.
4. Re-run `/health` and smoke checks on rolled-back versions.
5. Record incident + rollback reason in platform operations log/runbook.

Evidence-capture checklist (governance aligned):

- Backend and frontend release IDs/commit SHAs.
- Timestamped health and smoke test results.
- Environment-variable change record (names only; no secret values).
- Rollback reference (if used), including triggering condition and validation outcome.
- Operator/reviewer sign-off tied to deployment window.
