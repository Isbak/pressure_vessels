# Platform Vector Retrieval Module (BL-030)

This module defines deterministic ownership and lifecycle boundaries for the
Qdrant vector retrieval runtime.

## Scope

- Declares canonical Qdrant collection ownership for staging runtime
  operations.
- Defines embedding/indexing ownership boundaries for collection write paths and
  index lifecycle policy.
- Defines lifecycle boundaries for provisioning, indexing policy changes, and
  access control.

## Boundary Rules

1. **Collection boundary**: each collection has a single owning team that
   governs schema and vector payload contract changes.
2. **Indexing boundary**: indexing and reindex lifecycle policies are declared
   per collection and owned by designated teams to preserve deterministic
   retrieval behavior.
3. **Access boundary**: direct Qdrant access is disallowed for UI and operator
   paths; all runtime access is mediated through `services/backend` with
   least-privilege roles.

See `module.boundaries.yaml` for machine-readable contract data.
