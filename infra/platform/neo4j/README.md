# Platform Knowledge Graph Module (BL-029)

This module defines deterministic ownership and lifecycle boundaries for the
Neo4j runtime used for traceability graph workloads.

## Scope

- Declares canonical Neo4j database ownership for staging runtime operations.
- Defines graph schema ownership boundaries for node labels and relationship
  types used by traceability workflows.
- Defines lifecycle boundaries for provisioning, schema evolution, access
  approvals, and backup retention.

## Boundary Rules

1. **Database boundary**: the `traceability` database is owned by the Knowledge
   Platform Team; consuming services may not mutate database-level policy.
2. **Schema boundary**: node labels and relationship contracts are versioned and
   owned per domain to preserve deterministic audit query behavior.
3. **Access boundary**: direct graph access is disallowed for UI and operators;
   all runtime access is mediated through `services/backend` with least-privilege
   roles.

See `module.boundaries.yaml` for machine-readable contract data.
