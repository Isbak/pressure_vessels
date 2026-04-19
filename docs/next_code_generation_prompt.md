# Next Code Generation Prompt (Roadmap-Aligned)

Use this prompt to implement the **current next roadmap item: BL-033 — Deliver model catalog (Llama/Mistral/Qwen) runtime module**.

```text
You are implementing backlog item **BL-033: Deliver model catalog (Llama/Mistral/Qwen) runtime module** for the `pressure_vessels` repository.

Authoritative source:
- `docs/development_backlog.yaml`

Backlog context (resolved as of 2026-04-19):
- `BL-032` status is `done`.
- `BL-033` status is `todo`.
- `BL-033` dependencies are `BL-018` and `BL-032`, and both are `done`.
- Therefore `BL-033` is the next eligible item.

Restate before coding:
- Item ID/title: BL-033 — Deliver model catalog (Llama/Mistral/Qwen) runtime module
- depends_on: [BL-018, BL-032]
- acceptance criteria:
  1) Model catalog module under `infra/platform/model-catalog` documents approved model families and versioning policy.
  2) Module is referenced from the `llm-serving-vllm` consumption path.
  3) Stack registry entry for `models-llama-mistral-qwen` reflects deployment status accurately.
- deliverables:
  1) `infra/platform/model-catalog` module skeleton (README + `module.boundaries.yaml`).
  2) Approved model family documentation.
  3) Stack registry status update for `models-llama-mistral-qwen`.

Repository constraints:
- Keep changes minimal and focused; mirror the existing module skeleton patterns under `infra/platform/{iac,secrets,observability,postgresql,redis,runtime,qdrant,vllm}`.
- Do not introduce runtime code; this is a boundary/ownership skeleton, not a model deployment.
- Prefer deterministic, declarative YAML; no environment-specific secrets or live endpoints.
- Follow existing style for `module.boundaries.yaml` (versioned `kind`, `metadata.name`, `spec` block with owner and lifecycle boundaries).

Likely relevant files:
- `infra/platform/vllm/module.boundaries.yaml` (reference pattern for serving/runtime ownership)
- `docs/platform_runtime_stack_registry.yaml` (flip `models-llama-mistral-qwen` from `planned` to `deployed`)
- `docs/tech-stack.md` (`## Current` section — flip model catalog entry from `planned` to `deployed`)
- `docs/runbooks/platform_runtime_stack_operations.md` (cross-reference new module if applicable)

Task:
1) Create `infra/platform/model-catalog/` with a `README.md` (scope, boundary rules) and a `module.boundaries.yaml` declaring model family ownership, versioning policy, access ownership, and lifecycle boundaries.
2) Add or confirm references from the vLLM consumption path to the model catalog boundary contract.
3) Update `docs/platform_runtime_stack_registry.yaml` so `models-llama-mistral-qwen.status` becomes `deployed`.
4) Update the `## Current` section of `docs/tech-stack.md` so the model catalog row reflects `deployed`.
5) Add/extend any module-skeleton tests or guardrails consistent with prior runtime modules (if no such tests exist for predecessor modules, none are required).
6) Set `BL-033` status to `done` in `docs/development_backlog.yaml`.
7) Update `docs/next_code_generation_prompt.md` so it points at the subsequent eligible backlog item.

Output format:
- Provide a concise implementation plan first.
- Then provide unified diffs/patches per file.
- Then provide test/verification commands and expected results.
```

## Upcoming queue

The following items remain queued in dependency order. Select the next eligible
item from `docs/development_backlog.yaml` after BL-033 is completed.
