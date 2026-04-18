# Next Code Generation Prompt (Roadmap-Aligned)

The next actionable backlog item in `docs/development_backlog.yaml` is **BL-021: Deliver IaC foundation module for platform runtime stack**.

Use this prompt to start the next implementation session.

```text
You are implementing backlog item **BL-021: Deliver IaC foundation module for platform runtime stack** for the `pressure_vessels` repository.

Authoritative source:
- `docs/development_backlog.yaml`

Backlog context (resolved from YAML on 2026-04-18):
- `BL-021` status is `todo`.
- `BL-021` depends on: `BL-018` (status `done`).
- This makes `BL-021` the first actionable item in backlog order.

Restate before coding:
- Item ID/title: BL-021 — Deliver IaC foundation module for platform runtime stack
- depends_on: [BL-018]
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
- `scripts/check_tech_stack.py`

Task:
1) Implement BL-021 behavior by populating `infra/platform/iac` with a module skeleton that declares reusable environment provisioning primitives.
2) Update or add automated checks so the stack consistency script recognizes the new module.
3) Add/extend tests under `tests/` for new behavior.
4) Update related docs under `docs/` when contracts change.
5) Update `docs/development_backlog.yaml` status for `BL-021` when complete.
6) Update `docs/next_code_generation_prompt.md` so it points at the subsequent backlog item.

Output format:
- Provide a concise implementation plan first.
- Then provide unified diffs/patches per file.
- Then provide test commands and expected results.
- Then provide a short risk/assumption note.

Do not modify unrelated files.
```

## Upcoming queue after BL-021

The following items are queued in dependency order:

- BL-022 — Deliver secrets management module (depends on BL-018, BL-021)
- BL-023 — Deliver observability module (depends on BL-018, BL-021)
- BL-024 — Deliver datastore (PostgreSQL) runtime module (depends on BL-018, BL-021, BL-022)
- BL-025 — Deliver cache/queue (Redis) runtime module (depends on BL-018, BL-021)
- BL-026 — Deliver runtime platform (Docker/Kubernetes) deployment module (depends on BL-018, BL-021, BL-022)
