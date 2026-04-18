# Platform Runtime Stack Operations Runbook (BL-018)

This runbook defines BL-018 runtime foundation ownership and deployment operations.

## Service Ownership Boundaries

| Service/module | Owner | Boundary |
| --- | --- | --- |
| `services/frontend` | Platform Experience Team | Browser and operator workflows; no direct datastore access. |
| `services/backend` | Platform Runtime Team | API orchestration and all data plane access. |
| `infra/platform/*` | Platform Runtime + domain teams | Environment modules, deploy orchestration, and infrastructure lifecycle. |

## Environment Provisioning Inputs

1. `docs/platform_runtime_stack_registry.yaml` declares each stack component, status, and module mapping.
2. `infra/platform/environment.bootstrap.yaml` binds components to target environments.
3. `infra/platform/iac/module.primitives.yaml` defines reusable IaC provisioning primitives shared across environments.
4. `infra/platform/secrets/module.boundaries.yaml` defines issuance and encryption boundaries for provider-neutral secret handling.
5. `infra/platform/observability/module.boundaries.yaml` defines metrics/logs/traces/dashboard boundaries and incident signal inventory.
6. `scripts/check_tech_stack.py` enforces that every declared stack component is mapped and marked `deployed` or `planned`.
7. `scripts/check_tech_stack.py` deterministically requires `iac-opentofu-or-terraform` to be `deployed` when the IaC module path exists.

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
