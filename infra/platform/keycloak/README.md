# Platform Identity Module (BL-027)

This module defines deterministic ownership and lifecycle boundaries for the
Keycloak identity runtime.

## Scope

- Declares canonical identity object boundaries for realms, clients, and roles.
- Defines ownership contracts for realm-level configuration and client-level
  protocol settings.
- Defines lifecycle boundaries for provisioning, promotion, and emergency
  access revocation in dev and staging.

## Boundary Rules

1. **Realm boundary**: `pressure-vessels` realm configuration is owned by the
   Security Platform Team; consuming services may not mutate realm-level policy.
2. **Client boundary**: each runtime client has a single owning team and
   constrained protocol and redirect URI ownership.
3. **Role boundary**: realm and client roles are managed through declarative
   identity manifests with approval-gated promotion between environments.

See `module.boundaries.yaml` for machine-readable contract data.
