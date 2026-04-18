# IaC Foundation Module Skeleton

This module provides the BL-021 infrastructure-as-code baseline for platform
runtime environment provisioning.

## Ownership boundary

- **Primary owner:** Platform Runtime Team.
- **Responsibility:** Define reusable IaC primitives and composition contracts
  for environment provisioning.
- **Out of scope:** Service-specific configuration for platform components
  (tracked in dedicated modules such as `infra/platform/postgresql` and
  `infra/platform/observability`).

## Module skeleton

- `module.primitives.yaml`: Canonical list of reusable provisioning primitives
  and deterministic default lifecycle settings.

## Deterministic contract

- Primitive identifiers are stable and environment-agnostic.
- Planning/apply/validate stage names are fixed for CI and runbook references.
