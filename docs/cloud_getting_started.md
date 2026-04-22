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

## 11. Railway Quickstart (Single-Service MVP)

For a fast MVP deployment on Railway, run only the frontend `web` process bound to Railway's `PORT`.

- Root `Procfile` now defines:
  - `web`: `cd services/frontend && npm ci && npm run build && npm run start -- --hostname 0.0.0.0 --port ${PORT:-3000}`
  - `backend`: `cd services/backend && npm ci && BACKEND_HOST=0.0.0.0 BACKEND_PORT=${BACKEND_PORT:-8000} node local-integration-server.js`
- Keep `backend` unscaled for single-service MVP deployments.
- The backend process uses the deterministic local integration server and avoids the backend skeleton's incomplete NestJS build path.
- The frontend `/api/prompt` route still works without backend wiring by returning deterministic placeholder responses when `BACKEND_API_BASE_URL` is unset.
- LLM and data-plane infrastructure services (for example `infra/platform/vllm`, PostgreSQL, Redis, Neo4j, Qdrant, OpenSearch) are not launched from the root `Procfile`; run them as dedicated platform services/modules.

Recommended Railway configuration:

1. **Root Directory**: repository root.
2. **Start Command**: leave blank so Railway honors `Procfile` (or copy the command above explicitly).
3. **Environment Variables**:
   - `NODE_ENV=production`
   - Optional: `BACKEND_API_BASE_URL=<your backend URL>` only when a compatible backend is deployed.
4. **Health check**: `GET /` (or `GET /result` after first deploy).

### Railway multi-service environment variable matrix

Use the matrix below when running frontend and backend as separate Railway services
inside one project. Keep service-scoped secrets on the owning service, and expose
only cross-service endpoints needed for API calls.

| Railway service | Variable | Required | Example value | Notes |
| --- | --- | --- | --- | --- |
| `frontend` | `NODE_ENV` | Yes | `production` | Next.js runtime mode in Railway deployment. |
| `frontend` | `BACKEND_API_BASE_URL` | Optional* | `https://<backend-service>.up.railway.app` | Set when frontend `/api/prompt` should call a deployed backend service. |
| `backend` | `PV_BACKEND_AUTH_TOKEN_SECRET` | Yes** | `replace-with-long-random-secret` | Required secret consumed by backend runtime and enforced by backend security baseline. |
| `backend` | `BACKEND_HOST` | No | `0.0.0.0` | Bind host; local profile default is retained here for clarity. |
| `backend` | `BACKEND_PORT` | No | `8000` | Service port if backend runtime uses explicit port configuration. |

- \* Optional for bootstrap mode: frontend falls back to deterministic placeholder responses when `BACKEND_API_BASE_URL` is unset.
- \** Required whenever backend auth-protected runtime paths are enabled.

#### Infra/platform service coverage (what else to configure)

The platform stack includes additional modules under `infra/platform/*`. These are
tracked in the runtime stack registry and environment bootstrap manifests. Include
them in Railway/environment planning even when canonical variable names are managed
by provider modules or external secret stores.

| Stack component key | Module path | Dev | Staging | Variable source of truth |
| --- | --- | --- | --- | --- |
| `frontend-nextjs` | `services/frontend` | ✅ | ✅ | Railway service variables (for example `NODE_ENV`, `BACKEND_API_BASE_URL`). |
| `backend-nestjs` | `services/backend` | ✅ | ✅ | Railway service variables + approved secret module (`PV_BACKEND_AUTH_TOKEN_SECRET`). |
| `datastore-postgresql` | `infra/platform/postgresql` | ✅ | ✅ | Provider-managed DB variables/secrets (module-owned; no repo-global env var contract yet). |
| `cache-redis` | `infra/platform/redis` | ✅ | ✅ | Provider-managed cache variables/secrets (module-owned; no repo-global env var contract yet). |
| `auth-keycloak` | `infra/platform/keycloak` | ✅ | ✅ | Identity-provider variables/secrets per Keycloak module boundaries. |
| `graph-neo4j` | `infra/platform/neo4j` | ❌ | ✅ | Graph service variables/secrets per module boundaries. |
| `retrieval-qdrant` | `infra/platform/qdrant` | ❌ | ✅ | Vector retrieval variables/secrets per module boundaries. |
| `llm-serving-railway` | `infra/platform/vllm` | ❌ | ✅ | Dedicated Railway LLM service variables/secrets per vLLM module boundaries. |
| `search-opensearch` | `infra/platform/opensearch` | ❌ | ✅ | Search cluster variables/secrets per module boundaries. |
| `workflow-temporal` | `infra/platform/temporal` | ❌ | ✅ | Workflow service variables/secrets per module boundaries. |
| `observability-prometheus-grafana-loki-tempo` | `infra/platform/observability` | ✅ | ✅ | Observability stack variables/secrets per module boundaries. |
| `secrets-vault-or-sops-age` | `infra/platform/secrets` | ❌ | ✅ | Centralized secret issuance/encryption source of truth. |
| `iac-opentofu-or-terraform` | `infra/platform/iac` | ✅ | ✅ | IaC backend/provider credentials managed by platform module boundaries. |
| `runtime-docker-kubernetes` | `infra/platform/runtime` | ✅ | ✅ | Runtime target variables/secrets per deployment module boundaries. |
