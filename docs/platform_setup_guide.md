# Platform Infrastructure Setup Guide

This guide explains how to bring up every element under `infra/platform/` in
two target contexts:

- **Local** — a developer laptop or single VM, intended for iteration and
  integration testing.
- **Cloud** — a shared, multi-tenant environment (`dev`, `staging`) bound by
  `infra/platform/environment.bootstrap.yaml`.

Each module section links back to its canonical boundary contract under
`infra/platform/<module>/module.boundaries.yaml` or `module.primitives.yaml`.
The guide is intentionally tool-prescriptive for the local path (Docker
Compose, Helm, `kubectl`) and tool-neutral on the cloud path (OpenTofu or
Terraform) because the IaC module `infra/platform/iac/module.primitives.yaml`
does not pin a specific provider.

## Can it all be done as code?

Yes. Every module below is representable in IaC and configuration-as-code.
The deterministic contract is:

| Layer | Representation | Source of truth |
| --- | --- | --- |
| Environment scaffolding | OpenTofu / Terraform modules | `infra/platform/iac/module.primitives.yaml` |
| Container workloads | Helm charts or Kubernetes manifests | `infra/platform/runtime/module.boundaries.yaml` |
| Local parity | Docker Compose files | This guide |
| Service configuration | Declarative YAML / JSON manifests | Each module's `module.boundaries.yaml` |
| Secrets | Vault policies or SOPS-encrypted files | `infra/platform/secrets/module.boundaries.yaml` |
| Observability | Prometheus rules, Grafana dashboards as JSON, Loki/Tempo configs | `infra/platform/observability/module.boundaries.yaml` |

Direct console mutation is **not** allowed for Keycloak, Temporal, or
Kubernetes in dev/staging; changes must flow through CI-applied manifests.
The only sanctioned console path is break-glass for Keycloak, which is
logged and time-boxed.

## Prerequisites

### Local

- Docker 24+ and Docker Compose v2.
- `kubectl` 1.29+ and `kind` 0.22+ or `minikube` 1.33+ for Kubernetes-parity
  testing.
- `helm` 3.14+.
- `tofu` 1.7+ (OpenTofu) or `terraform` 1.7+.
- `sops` 3.8+ and `age` 1.1+ for local secrets.

### Cloud

- Account + credentials for the target cloud (GCP/AWS/Azure), with permission
  to create projects/subscriptions, VPCs, IAM, and managed services.
- Remote state backend (GCS, S3, or Azure Blob) configured to satisfy the
  `state_backend_contract` primitive from `infra/platform/iac/module.primitives.yaml`.
- A secrets backend reachable from CI (HashiCorp Vault cluster or a KMS key
  that encrypts SOPS `age` recipients).

## Bootstrap order

Modules have a deterministic dependency order. Follow it for both local and
cloud:

1. `iac` — state backend and environment namespace.
2. `secrets` — Vault / SOPS seal so downstream modules can consume handles.
3. `runtime` — container runtime and Kubernetes namespace.
4. `postgresql`, `redis`, `neo4j` — stateful data plane.
5. `keycloak` — requires PostgreSQL.
6. `temporal` — requires PostgreSQL and secrets.
7. `observability` — requires runtime; optional to bring up earlier if you
   want to observe the bootstrap itself.

---

## 1. IaC foundation (`infra/platform/iac`)

Primitives: `environment_namespace`, `network_baseline`,
`secret_reference_bindings`, `state_backend_contract`.

### Local

```bash
# 1. Initialize an OpenTofu workspace that mirrors the primitives.
mkdir -p infra/platform/iac/local && cd infra/platform/iac/local
cat > main.tf <<'EOF'
terraform {
  required_version = ">= 1.7.0"
  backend "local" { path = "terraform.tfstate" }
}
module "environment_namespace" {
  source   = "../modules/environment_namespace"
  name     = "pv-local"
}
EOF
tofu init && tofu plan && tofu apply
```

The local path uses a filesystem state backend. This satisfies
`state_backend_contract` but is **not** acceptable in dev/staging.

### Cloud

- Create a remote state bucket (one per environment) with object versioning
  and server-side encryption enabled.
- Register the backend in `backend.tf`:

```hcl
terraform {
  backend "gcs" {
    bucket = "pv-tfstate-dev"
    prefix = "platform/iac"
  }
}
```

- Apply the same `environment_namespace` and `network_baseline` modules with
  per-environment variables (`env = "dev"` or `env = "staging"`).

### As-code?

Fully. The module already defines four primitives each with `plan/apply/validate`
lifecycle stages so CI can enforce drift-free applies.

---

## 2. Secrets (`infra/platform/secrets`)

Boundary allows two provider modes: `vault` or `sops-age`.
`in_repo_plaintext: false` is non-negotiable.

### Local — SOPS + age

```bash
age-keygen -o ~/.config/sops/age/keys.txt
export SOPS_AGE_RECIPIENTS=$(grep '^# public key:' ~/.config/sops/age/keys.txt | awk '{print $4}')
sops --encrypt --age "$SOPS_AGE_RECIPIENTS" \
  infra/platform/secrets/local/values.yaml > infra/platform/secrets/local/values.enc.yaml
```

Only the `.enc.yaml` files are committed. Decrypt on demand:

```bash
sops --decrypt infra/platform/secrets/local/values.enc.yaml | kubectl apply -f -
```

### Cloud — HashiCorp Vault

- Deploy Vault via the official Helm chart into a dedicated namespace
  (`vault-system`), with auto-unseal bound to a cloud KMS (GCP KMS, AWS KMS,
  Azure Key Vault).
- Enable the `kv-v2` secrets engine at `pv/`.
- Enable the Kubernetes auth method so workloads authenticate by service
  account.
- Define policies per consumer listed in the module boundary
  (`infra/platform/backend`, `infra/platform/workflow`,
  `infra/platform/observability`).

### As-code?

Yes. SOPS files are themselves code (encrypted YAML in Git). Vault is managed
with the `hashicorp/vault` Terraform provider for policies, auth methods, and
engines. Secret **values** are never committed; only references
(`secret_handle`) cross the boundary.

---

## 3. Runtime (`infra/platform/runtime`)

Boundary: Docker for the container runtime, Kubernetes for orchestration,
namespaces follow `pv-{environment}`, images `ghcr.io/pressure-vessels/{service}:{git_sha}`
with immutable tags.

### Local — kind

```bash
kind create cluster --name pv-local --config - <<'EOF'
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
  - role: control-plane
  - role: worker
EOF
kubectl create namespace pv-local
```

For pure Compose workflows (no Kubernetes), a single `docker-compose.yaml`
that composes postgres/redis/keycloak is acceptable but does **not** satisfy
the `rollout_execution_owner` boundary — treat it as a developer-only mode.

### Cloud

- Provision a managed Kubernetes cluster (GKE, EKS, or AKS) sized per
  environment. Enable workload identity / IRSA for pod-level cloud IAM.
- Create namespaces `pv-dev` and `pv-staging`.
- Configure the GHCR pull secret (or use OIDC federation from the cluster to
  GitHub Packages).
- Apply network policies that deny cross-namespace traffic by default.

### As-code?

Fully. The cluster is Terraform; workloads are Helm charts versioned under
`infra/platform/runtime/charts/` (add when you implement; boundary already
requires `deployment-manifest-revision` as release evidence).

---

## 4. PostgreSQL (`infra/platform/postgresql`)

Engine: PostgreSQL 16. Database name `pressure_vessels`, role prefix `pv_`.
Schemas: `platform_control`, `compliance_records`, `traceability_graph`.

### Local — Docker Compose

```yaml
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: pressure_vessels
      POSTGRES_USER: pv_admin
      POSTGRES_PASSWORD_FILE: /run/secrets/pg_password
    ports: ["5432:5432"]
    volumes: ["pgdata:/var/lib/postgresql/data"]
    secrets: [pg_password]
volumes: { pgdata: {} }
secrets:
  pg_password: { file: ./.secrets/pg_password }
```

Apply schema bootstrap with a migration tool (Flyway, Sqitch, or Prisma
migrate — pick and document in an ADR):

```sql
CREATE SCHEMA IF NOT EXISTS platform_control AUTHORIZATION pv_platform_runtime;
CREATE SCHEMA IF NOT EXISTS compliance_records AUTHORIZATION pv_compliance_engineering;
CREATE SCHEMA IF NOT EXISTS traceability_graph AUTHORIZATION pv_knowledge_platform;
```

### Cloud

- **Managed option (recommended):** Cloud SQL for PostgreSQL (GCP), RDS
  PostgreSQL (AWS), or Azure Database for PostgreSQL Flexible Server, version
  16, private IP only, automated daily backups retaining 7 days (dev) or 30
  days (staging) per the boundary.
- **Self-managed option:** CloudNativePG or Zalando Postgres Operator inside
  the Kubernetes cluster with a dedicated StorageClass.
- Enforce TLS in transit, enable pgAudit, and restrict network access to the
  backend service account only (`direct_service_access.allowed: false`).

### As-code?

Fully. The database instance is Terraform (`google_sql_database_instance`,
`aws_db_instance`, `azurerm_postgresql_flexible_server`). Schemas, roles, and
grants go into versioned migration scripts. Migrations require
`owning-domain-team` + `engineering-reviewer` approvals per the boundary.

---

## 5. Redis (`infra/platform/redis`)

Engine: Redis 7. Local: single-node, cache-only (no AOF). Staging: replicated,
AOF + RDB snapshots.

### Local — Docker Compose

```yaml
services:
  redis:
    image: redis:7
    command: ["redis-server", "--appendonly", "no", "--maxmemory", "256mb",
              "--maxmemory-policy", "allkeys-lru"]
    ports: ["6379:6379"]
```

Namespaces and queues from the boundary (`backend-response-cache`,
`standards-read-model-cache`, `workflow-task-queue`, `notification-dispatch-queue`)
are enforced by key prefixes at the application layer with the governance
prefix `pv:`.

### Cloud

- **Managed:** Memorystore for Redis (GCP), ElastiCache Redis (AWS), or Azure
  Cache for Redis, version 7, with Standard (replicated) tier for staging.
  Enable AOF + daily RDB snapshots.
- **Self-managed:** Bitnami Redis Helm chart in `replication` architecture
  with a sidecar Redis Exporter for Prometheus.
- Expose only via private endpoint, require AUTH, enable TLS.

### As-code?

Fully. Terraform for provisioning; Helm values files for self-managed. TTL
defaults and queue message TTLs from the boundary are wired through backend
config, not through Redis server config.

---

## 6. Neo4j (`infra/platform/neo4j`)

Engine: Neo4j 5, community or enterprise. Single database `traceability`.
Graph schema: `Requirement`, `Clause`, `Model`, `Calculation`, `Artifact`,
`Approval` with typed relationships.

### Local — Docker Compose

```yaml
services:
  neo4j:
    image: neo4j:5-community
    environment:
      NEO4J_AUTH: neo4j/pv_local_dev_only
      NEO4J_dbms_default__database: traceability
    ports: ["7474:7474", "7687:7687"]
    volumes: ["neo4jdata:/data"]
volumes: { neo4jdata: {} }
```

Apply the schema with a versioned Cypher migration (Liquibase Neo4j or
`neo4j-migrations`):

```cypher
CREATE CONSTRAINT requirement_id IF NOT EXISTS
  FOR (r:Requirement) REQUIRE r.id IS UNIQUE;
CREATE CONSTRAINT clause_id IF NOT EXISTS
  FOR (c:Clause) REQUIRE c.id IS UNIQUE;
// ...one per node label listed in the boundary
```

### Cloud

- **Managed:** Neo4j AuraDB Professional (staging). Strong option because it
  provides backups, VPC peering, and SSO.
- **Self-managed:** Neo4j Enterprise via the official Helm chart, causal
  cluster with 3 core servers for staging, 1 for dev.
- Restrict Bolt traffic to the backend service account.

### As-code?

Fully. Terraform `neo4j/aura` provider or `helm_release`. Schema constraints
and indexes live as migration files reviewed by `knowledge-platform`
(schema-change owner).

---

## 7. Keycloak (`infra/platform/keycloak`)

Engine: Keycloak 24.x. Realm `pressure-vessels`. Clients `pressure-vessels-frontend`
(public OIDC) and `pressure-vessels-backend` (confidential OIDC).

### Local — Docker Compose

```yaml
services:
  keycloak:
    image: quay.io/keycloak/keycloak:24.0
    command: ["start-dev", "--import-realm"]
    environment:
      KEYCLOAK_ADMIN: admin
      KEYCLOAK_ADMIN_PASSWORD_FILE: /run/secrets/kc_admin
      KC_DB: postgres
      KC_DB_URL: jdbc:postgresql://postgres:5432/keycloak
      KC_DB_USERNAME: pv_keycloak
      KC_DB_PASSWORD_FILE: /run/secrets/kc_db
    volumes: ["./realm:/opt/keycloak/data/import"]
    depends_on: [postgres]
```

Commit the exported realm JSON under `infra/platform/keycloak/realms/pressure-vessels.json`.

### Cloud

- Deploy Keycloak via the Bitnami or official Keycloak Helm chart against the
  managed PostgreSQL instance. Use 2+ replicas in staging.
- Front with an ingress controller that terminates TLS (cert-manager + Let's
  Encrypt or the cloud certificate manager).
- Declarative realm configuration via `keycloak-config-cli` executed by CI,
  taking the committed realm JSON as input. Direct console mutation is
  disallowed except break-glass (30-minute TTL with post-incident review).

### As-code?

Fully. The `mrparkers/keycloak` Terraform provider covers realms, clients,
roles, and identity providers. `keycloak-config-cli` is the simpler path for
teams already using JSON exports. Release evidence required by the boundary
(`realm-config-revision`, `client-config-diff`, `role-mapping-audit-record`)
is produced by CI diffing committed JSON between revisions.

---

## 8. Temporal (`infra/platform/temporal`)

Engine: Temporal. Staging namespace `pressure-vessels-staging`, 14-day
retention. Task queues `workflow-orchestration`, `evidence-assembly`.

### Local — Docker Compose

Use the official `docker-compose` recipe from `temporalio/docker-compose`:

```bash
git clone https://github.com/temporalio/docker-compose temporal-local
cd temporal-local
docker compose up -d
# Web UI at http://localhost:8080
tctl --namespace default namespace register pressure-vessels-local
```

### Cloud

- **Managed:** Temporal Cloud (recommended for staging). Provision namespaces
  via Terraform `temporalio/temporalcloud` provider.
- **Self-managed:** Temporal Helm chart against managed PostgreSQL (history
  and visibility stores). Deploy frontend, matching, history, and worker
  services per the chart defaults.
- Workers live in the application deploy pipeline
  (`orchestration-runtime-worker`, `compliance-evidence-worker`) and roll out
  through `runtime-docker-kubernetes`.

### As-code?

Fully. Terraform for namespaces and allowed regions; Helm values for
self-managed control plane; worker deployments are Kubernetes manifests.
Namespace policy mutation is CI-only per the boundary.

---

## 9. Observability (`infra/platform/observability`)

Metrics: Prometheus. Logs: Loki. Traces: Tempo. Dashboards: Grafana with
required folders `platform-runtime-overview` and `platform-incidents`.

### Local — Docker Compose

```yaml
services:
  prometheus:
    image: prom/prometheus:v2.55.0
    volumes: ["./prometheus.yml:/etc/prometheus/prometheus.yml"]
    ports: ["9090:9090"]
  loki:
    image: grafana/loki:2.9.0
    ports: ["3100:3100"]
  tempo:
    image: grafana/tempo:2.5.0
    ports: ["3200:3200"]
  grafana:
    image: grafana/grafana:11.2.0
    volumes:
      - "./grafana/provisioning:/etc/grafana/provisioning"
      - "./grafana/dashboards:/var/lib/grafana/dashboards"
    ports: ["3000:3000"]
```

All dashboards ship as JSON under `infra/platform/observability/dashboards/`
and are mounted via Grafana's file-based provisioner. Alert rules ship as
Prometheus rule files alongside.

### Cloud

- Use the `kube-prometheus-stack` Helm chart (Prometheus + Grafana +
  Alertmanager) for metrics and dashboards.
- Deploy Loki via `loki-distributed` chart against object storage
  (GCS/S3/Azure Blob) for log retention (14 days dev, 30 days staging).
- Deploy Tempo via `tempo-distributed` against object storage with retention
  7 days dev / 14 days staging.
- Required incident signals from the boundary must be wired as Alertmanager
  routes. The three CI-gating signals are
  `service_error_rate_high`, `api_latency_slo_breach`,
  `deployment_rollout_failures`.

### As-code?

Fully. Helm values, Prometheus rule files, Grafana dashboard JSON, and
Alertmanager routing config all live in Git. `immutable_signal_keys: true`
means the alert name/key cannot change without an ADR.

---

## End-to-end bootstrap recipe

A reproducible local stack in one command (illustrative; implement when
`docker-compose` files land):

```bash
make platform-local-up       # compose: postgres redis neo4j keycloak temporal observability
make platform-local-migrate  # apply all schema migrations in dependency order
make platform-local-seed     # realm import, temporal namespace register, dashboards
```

A reproducible cloud stack for `dev`:

```bash
(cd infra/platform/iac/envs/dev && tofu init && tofu apply)
helm upgrade --install --namespace pv-dev platform ./charts/platform \
  --values values/dev.yaml
scripts/apply_keycloak_realm.sh dev
scripts/register_temporal_namespace.sh dev
```

Both entry points must be callable from CI and must be idempotent — this is
the deterministic contract that makes "infra as code" enforceable in this
repository.

## Traceability

- Each module's lifecycle owner is recorded in its `module.boundaries.yaml`.
- Deployment evidence requirements (image digest, manifest revision, rollback
  plan, etc.) are enforced at release time by the CI governance policy in
  `docs/governance/ci_governance_policy.v1.json`.
- This guide is referenced from
  `docs/runbooks/platform_runtime_stack_operations.md` for operator use.
