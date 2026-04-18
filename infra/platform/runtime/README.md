# Platform Runtime Deployment Module (BL-026)

This module defines deterministic Docker/Kubernetes deployment ownership and
lifecycle boundaries for platform services.

## Scope

- Declares canonical container/runtime deploy targets for Docker image artifacts
  and Kubernetes execution.
- Defines service ownership boundaries for frontend and backend deployment
  paths.
- Defines runtime lifecycle boundaries for provisioning, rollout, rollback, and
  environment promotion policy.

## Boundary Rules

1. **Control boundary**: direct Kubernetes access is disallowed; runtime changes
   must flow through CI/CD-controlled rollout paths.
2. **Ownership boundary**: each service has an owning team and explicit runtime
   lifecycle mode.
3. **Release boundary**: every rollout requires immutable release evidence
   (`image-digest`, deployment manifest revision, rollback plan identifier).

See `module.boundaries.yaml` for machine-readable contract data.
