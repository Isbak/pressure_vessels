# Platform Datastore Module (BL-024)

This module defines deterministic ownership and lifecycle boundaries for the
PostgreSQL runtime datastore.

## Scope

- Declares canonical PostgreSQL engine family and major version contract.
- Defines schema ownership boundaries for platform, compliance, and
  traceability domains.
- Defines provisioning, migration approval, and backup retention boundaries for
  dev and staging.

## Boundary Rules

1. **Access boundary**: application services do not access PostgreSQL directly;
   all datastore access flows through `services/backend`.
2. **Schema boundary**: each schema has a single owning domain team with an
   explicit lifecycle mode.
3. **Lifecycle boundary**: migration execution is centralized in platform
   runtime and requires owning-domain plus engineering review approvals.

See `module.boundaries.yaml` for machine-readable contract data.
