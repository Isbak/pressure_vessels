# Platform Model Catalog Module (BL-033)

This module defines deterministic ownership, approved model families, and
versioning boundaries for model artifacts consumed by `infra/platform/vllm`.

## Scope

- Declares the approved model family set for production-eligible serving:
  Llama, Mistral, and Qwen.
- Defines semantic versioning and approval lifecycle controls for model catalog
  entries consumed by vLLM serving.
- Defines ownership and access boundaries for catalog publication, review, and
  rollout authorization.

## Approved Model Families

- `llama`
- `mistral`
- `qwen`

Each family may include multiple approved versions. Catalog changes must follow
module lifecycle policy in `module.boundaries.yaml`.

## Boundary Rules

1. **Catalog ownership boundary**: `ai-platform` owns approved family entries,
   promotion policy, and deprecation decisions.
2. **Versioning boundary**: model versions use deterministic
   `major.minor.patch` semantics with immutable approved revisions.
3. **Consumption boundary**: serving modules may consume only catalog-approved
   families/versions; direct ad-hoc model rollout is prohibited.
4. **Access boundary**: publication access is limited to designated catalog
   maintainers; consumers are read-only through approved serving paths.

See `module.boundaries.yaml` for machine-readable contract data.
