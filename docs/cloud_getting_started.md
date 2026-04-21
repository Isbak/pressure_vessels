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

