# Platform Cache/Queue Module (BL-025)

This module defines deterministic ownership and lifecycle boundaries for the
Redis runtime used for cache and queue workloads.

## Scope

- Declares canonical Redis engine family and major version contract.
- Defines cache namespace and queue stream ownership boundaries.
- Defines provisioning, persistence mode, and retention defaults for dev and
  staging.

## Boundary Rules

1. **Access boundary**: application services do not access Redis directly; all
   cache and queue access flows through `services/backend`.
2. **Ownership boundary**: each cache namespace and queue stream has an owning
   team and explicit producer/consumer contract.
3. **Lifecycle boundary**: platform runtime owns provisioning and scaling,
   while workloads remain ephemeral with environment-specific retention
   defaults.

See `module.boundaries.yaml` for machine-readable contract data.
