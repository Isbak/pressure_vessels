# Next Code Generation Prompt (Roadmap-Aligned)

Use this prompt to implement the **current next roadmap item: BL-031 — Deliver search/analytics (OpenSearch) runtime module**.

```text
You are implementing backlog item **BL-031: Deliver search/analytics (OpenSearch) runtime module** for the `pressure_vessels` repository.

Authoritative source:
- `docs/development_backlog.yaml`

Backlog context (resolved as of 2026-04-19):
- `BL-030` status is `done`.
- `BL-031` status is `todo`.
- `BL-031` dependencies are `BL-018` and `BL-021`, and both are `done`.
- Therefore `BL-031` is the next eligible item.

Restate before coding:
- Item ID/title: BL-031 — Deliver search/analytics (OpenSearch) runtime module
- depends_on: [BL-018, BL-021]
- acceptance criteria:
  1) Search module under `infra/platform/opensearch` documents index ownership, retention, and access boundaries.
  2) Module is referenced from `environment.bootstrap.yaml` staging environment.
  3) Stack registry entry for `search-opensearch` reflects deployment status accurately.
- deliverables:
  1) `infra/platform/opensearch` module skeleton (README + `module.boundaries.yaml`).
  2) Index and retention policy documentation.
  3) Stack registry status update for `search-opensearch`.

Repository constraints:
- Keep changes minimal and focused; mirror the existing module skeleton patterns under `infra/platform/{iac,secrets,observability,postgresql,redis,runtime}`.
- Do not introduce runtime code; this is a boundary/ownership skeleton, not an OpenSearch deployment.
- Prefer deterministic, declarative YAML; no environment-specific secrets or live endpoints.
- Follow existing style for `module.boundaries.yaml` (versioned `kind`, `metadata.name`, `spec` block with owner and lifecycle boundaries).

Likely relevant files:
- `infra/platform/runtime/module.boundaries.yaml` (reference pattern)
- `infra/platform/redis/module.boundaries.yaml` (reference pattern)
- `infra/platform/environment.bootstrap.yaml` (already lists `retrieval-qdrant` for staging — verify and keep in sync)
- `docs/platform_runtime_stack_registry.yaml` (flip `search-opensearch` from `planned` to `deployed`)
- `docs/tech-stack.md` (`## Current` section — flip the OpenSearch entry from `planned` to `deployed`)
- `docs/runbooks/platform_runtime_stack_operations.md` (cross-reference new module if applicable)

Task:
1) Create `infra/platform/opensearch/` with a `README.md` (scope, boundary rules) and a `module.boundaries.yaml` declaring index ownership, retention policy, and access ownership plus lifecycle boundaries.
2) Confirm `infra/platform/environment.bootstrap.yaml` references `search-opensearch` for `staging`; add it where missing.
3) Update `docs/platform_runtime_stack_registry.yaml` so `search-opensearch.status` becomes `deployed`.
4) Update the `## Current` section of `docs/tech-stack.md` so the OpenSearch row reflects `deployed`.
5) Add/extend any module-skeleton tests or guardrails consistent with prior runtime modules (if no such tests exist for predecessor modules, none are required).
6) Set `BL-031` status to `done` in `docs/development_backlog.yaml`.
7) Update `docs/next_code_generation_prompt.md` so it points at the subsequent backlog item (BL-032 — Deliver LLM serving (vLLM) runtime module).

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

- **BL-032** Deliver LLM serving (vLLM) runtime module — depends on BL-018, BL-021, BL-022.
- **BL-033** Deliver model catalog (Llama/Mistral/Qwen) runtime module — depends on BL-018, BL-032.
