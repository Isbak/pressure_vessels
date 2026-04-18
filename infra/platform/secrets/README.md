# Platform Secrets Module (BL-022)

This module defines deterministic boundaries for platform secret issuance and encryption.

## Scope

- Provides environment-scoped secret materialization contracts for runtime modules.
- Supports provider-neutral adapters (`vault` or `sops-age`) without changing consumer interfaces.
- Excludes application-level secret value generation and rotation workflows.

## Boundary Rules

1. **Issuance boundary**: only platform modules under `infra/platform/*` receive references to secret handles.
2. **Encryption boundary**: plaintext secret values are never committed; encrypted-at-rest artifacts only.
3. **Consumption boundary**: services consume stable references, not provider-specific secret paths.

See `module.boundaries.yaml` for machine-readable contract data.
