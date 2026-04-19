# Platform LLM Serving Module (BL-032)

This module defines deterministic ownership, endpoint, and lifecycle boundaries
for the vLLM serving runtime.

## Scope

- Declares the canonical vLLM serving endpoint boundary for staging runtime
  operations.
- Defines capacity envelope ownership for concurrency, throughput, and rollout
  limits.
- Defines lifecycle and access boundaries for provisioning, model rollout, and
  endpoint access.

## Boundary Rules

1. **Endpoint boundary**: the serving endpoint contract is owned by
   `ai-platform`; consumer services may only use approved internal access paths.
2. **Capacity boundary**: concurrency and token throughput envelopes are
   declared in-module and changes require owner approval.
3. **Access boundary**: direct operator/UI access is disallowed; endpoint usage
   is mediated through approved backend service paths with least privilege.

See `module.boundaries.yaml` for machine-readable contract data.
