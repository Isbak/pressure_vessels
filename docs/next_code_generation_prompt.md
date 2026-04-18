# Next Code Generation Prompt (Roadmap-Aligned)

The subsequent backlog item in `docs/development_backlog.yaml` is **BL-026: Deliver runtime platform (Docker/Kubernetes) deployment module**.

Use this prompt to start the next implementation session once `BL-026` is unblocked.

```text
You are implementing backlog item **BL-026: Deliver runtime platform (Docker/Kubernetes) deployment module** for the `pressure_vessels` repository.

Authoritative source:
- `docs/development_backlog.yaml`

Backlog context (resolved from YAML on 2026-04-18):
- `BL-026` status is `blocked`.
- `BL-026` depends on: `BL-018`, `BL-021`, and `BL-022` (all status `done`).
- Unblock `BL-026` before implementation and then proceed in backlog order.

Restate before coding:
- Item ID/title: BL-026 — Deliver runtime platform (Docker/Kubernetes) deployment module
- depends_on: [BL-018, BL-021, BL-022]
- source: Phase 5 Runtime Deployment roadmap item

Repository constraints:
- Keep changes minimal and focused.
- Follow existing style and module patterns in `src/pressure_vessels/` and `infra/platform/`.
- Add/extend tests in `tests/` for any new behavior.
- Prefer deterministic logic (no randomness/time-dependent values unless explicitly controlled).

Likely relevant files:
- `docs/platform_runtime_stack_registry.yaml`
- `infra/platform/environment.bootstrap.yaml`
- `docs/runbooks/platform_runtime_stack_operations.md`
- `infra/platform/runtime/`

Task:
1) Implement BL-026 behavior by populating `infra/platform/runtime` with a deployment module skeleton for Docker/Kubernetes target ownership and lifecycle boundaries.
2) Wire the runtime module into `infra/platform/environment.bootstrap.yaml` dev and staging definitions.
3) Add/extend tests under `tests/` for new behavior.
4) Update related docs under `docs/` when contracts change.
5) Update `docs/development_backlog.yaml` status for `BL-026` when complete.
6) Update `docs/next_code_generation_prompt.md` so it points at the subsequent backlog item.

Output format:
- Provide a concise implementation plan first.
- Then provide unified diffs/patches per file.
- Then provide test commands and expected results.
- Then provide a short risk/assumption note.

Do not modify unrelated files.
```

## Upcoming queue after BL-026

No additional backlog items are currently queued after BL-026 in `docs/development_backlog.yaml`.
