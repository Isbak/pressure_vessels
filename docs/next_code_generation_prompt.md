# Next Code Generation Prompt (Roadmap-Aligned)

Use this prompt to implement the **current next roadmap item: BL-027 — Deliver identity (Keycloak) runtime module**.

```text
You are implementing backlog item **BL-027: Deliver identity (Keycloak) runtime module** for the `pressure_vessels` repository.

Authoritative source:
- `docs/development_backlog.yaml`

Backlog context (resolved as of 2026-04-19):
- `BL-027` status is `todo`.
- `BL-027` dependencies are `BL-018`, `BL-021`, and `BL-022`, and all three are `done`.
- Therefore `BL-027` is the next eligible item.

Restate before coding:
- Item ID/title: BL-027 — Deliver identity (Keycloak) runtime module
- depends_on: [BL-018, BL-021, BL-022]
- acceptance criteria:
  1) Identity module under `infra/platform/keycloak` documents realm, client, and role ownership and lifecycle.
  2) Module is referenced from `environment.bootstrap.yaml` dev and staging environments.
  3) Stack registry entry for `auth-keycloak` reflects deployment status accurately.
- deliverables:
  1) `infra/platform/keycloak` module skeleton (README + `module.boundaries.yaml`).
  2) Realm, client, and role ownership documentation.
  3) Stack registry status update for `auth-keycloak`.

Repository constraints:
- Keep changes minimal and focused; mirror the existing module skeleton patterns under `infra/platform/{iac,secrets,observability,postgresql,redis,runtime}`.
- Do not introduce runtime code; this is a boundary/ownership skeleton, not a Keycloak deployment.
- Prefer deterministic, declarative YAML; no environment-specific secrets or live endpoints.
- Follow existing style for `module.boundaries.yaml` (versioned `kind`, `metadata.name`, `spec` block with owner and lifecycle boundaries).

Likely relevant files:
- `infra/platform/runtime/module.boundaries.yaml` (reference pattern)
- `infra/platform/secrets/module.boundaries.yaml` (reference pattern)
- `infra/platform/environment.bootstrap.yaml` (already lists `auth-keycloak` for dev and staging — verify and keep in sync)
- `docs/platform_runtime_stack_registry.yaml` (flip `auth-keycloak` from `planned` to `deployed`)
- `docs/tech-stack.md` (`## Current` section — flip the Keycloak entry from `planned` to `deployed`)
- `docs/runbooks/platform_runtime_stack_operations.md` (cross-reference new module if applicable)

Task:
1) Create `infra/platform/keycloak/` with a `README.md` (scope, boundary rules) and a `module.boundaries.yaml` declaring realm, client, and role ownership plus lifecycle boundaries.
2) Confirm `infra/platform/environment.bootstrap.yaml` references `auth-keycloak` for both `dev` and `staging`; add it where missing.
3) Update `docs/platform_runtime_stack_registry.yaml` so `auth-keycloak.status` becomes `deployed`.
4) Update the `## Current` section of `docs/tech-stack.md` so the Keycloak row reflects `deployed`.
5) Add/extend any module-skeleton tests or guardrails consistent with prior runtime modules (if no such tests exist for predecessor modules, none are required).
6) Set `BL-027` status to `done` in `docs/development_backlog.yaml`.
7) Update `docs/next_code_generation_prompt.md` so it points at the subsequent backlog item (BL-028 — Deliver workflow orchestration (Temporal) runtime module).

Output format:
- Provide a concise implementation plan first.
- Then provide unified diffs/patches per file.
- Then provide test/verification commands and expected results.
```

## Upcoming queue

The following items remain queued in dependency order. Each delivers a runtime
module skeleton (`infra/platform/<component>/`), wires the module into
`infra/platform/environment.bootstrap.yaml` for the targeted environments, and
flips the corresponding entry in `docs/platform_runtime_stack_registry.yaml`
and the `## Current` section of `docs/tech-stack.md` from `planned` to
`deployed`.

- **BL-028** Deliver workflow orchestration (Temporal) runtime module — depends on BL-016, BL-018, BL-021.
- **BL-029** Deliver knowledge graph (Neo4j) runtime module — depends on BL-006, BL-018, BL-021.
- **BL-030** Deliver vector retrieval (Qdrant) runtime module — depends on BL-018, BL-021.
- **BL-031** Deliver search/analytics (OpenSearch) runtime module — depends on BL-018, BL-021.
- **BL-032** Deliver LLM serving (vLLM) runtime module — depends on BL-018, BL-021, BL-022.
- **BL-033** Deliver model catalog (Llama/Mistral/Qwen) runtime module — depends on BL-018, BL-032.
