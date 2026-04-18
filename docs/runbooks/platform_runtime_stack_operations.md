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
3. `scripts/check_tech_stack.py` enforces that every declared stack component is mapped and marked `deployed` or `planned`.

## Deployment Readiness Checklist

- Validate stack declarations:
  - `python scripts/check_tech_stack.py`
- Confirm skeleton service boundaries are present:
  - `test -f services/frontend/README.md`
  - `test -f services/backend/README.md`
- Confirm bootstrap environment manifest exists:
  - `test -f infra/platform/environment.bootstrap.yaml`

## Incident Operations

- If component state changes from `planned` to `deployed`, update both:
  - `docs/platform_runtime_stack_registry.yaml`
  - `docs/tech-stack.md`
- Re-run CI gate before merge to keep stack contract consistent.
