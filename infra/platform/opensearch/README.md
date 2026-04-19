# Platform Search/Analytics Module (BL-031)

This module defines deterministic ownership and lifecycle boundaries for the
OpenSearch runtime used for search and analytics workloads.

## Scope

- Declares canonical OpenSearch index ownership for staging runtime operations.
- Defines index lifecycle and retention boundaries for search and analytics
  datasets.
- Defines access ownership boundaries for administrative, write, and read paths.

## Boundary Rules

1. **Index boundary**: each index has a single owning team that governs mapping,
   shard strategy, and schema evolution approvals.
2. **Retention boundary**: retention and rollover policies are declared per
   index class, with lifecycle ownership split between domain and platform
   teams.
3. **Access boundary**: direct OpenSearch access is disallowed for UI and
   operator paths; runtime access is mediated through `services/backend` with
   least-privilege roles.

See `module.boundaries.yaml` for machine-readable contract data.
