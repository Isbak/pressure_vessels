# Next Code Generation Prompt (Roadmap-Aligned)

Use this prompt to implement the **next queued roadmap item: BL-049 — Publish Railway deployment guide for full backend service rollout**.

```text
You are implementing backlog item **BL-049: Publish Railway deployment guide for full backend service rollout** for the `pressure_vessels` repository.

Authoritative source:
- `docs/development_backlog.yaml`

Backlog context (resolved as of 2026-04-22):
- `BL-047` status is `done`.
- `BL-048` status is `done`.
- `BL-049` status is `todo`.
- `BL-049` dependencies (`BL-047`, `BL-048`) are both `done`.
- Therefore `BL-049` is the next queued item.

Restate before coding:
- Item ID/title: BL-049 — Publish Railway deployment guide for full backend service rollout
- depends_on: [BL-047, BL-048]
- acceptance criteria:
  1) Railway guide includes separate frontend/backend service deployment, backend required environment variables, and cross-service networking configuration.
  2) Guide documents optional staging-only dependencies (for example llm-serving-railway) and clearly distinguishes bootstrap placeholders from production-integrated backend behavior.
  3) Guide includes release verification checks, rollback steps, and evidence-capture checklist aligned to platform governance policy.
- deliverables:
  1) Updated Railway deployment section with backend-first guidance.
  2) Backend deployment checklist (env vars, health checks, smoke tests).
  3) Rollback and post-deploy validation procedure for Railway runtime.

Repository constraints:
- Keep changes minimal and focused; implement BL-049 only.
- Follow contract-driven integration and avoid undocumented interface drift.
- Preserve governance-by-default controls from `AGENT_GOVERNANCE.md`.
- Prefer incremental delivery over broad rewrites; keep behavior deterministic.

Likely relevant files:
- `docs/cloud_getting_started.md`
- `docs/runbooks/platform_runtime_stack_operations.md`
- `infra/platform/environment.bootstrap.yaml`
- `docs/platform_runtime_stack_registry.yaml`

Task:
1) Implement BL-049 deployment guidance updates with backend-first runtime rollout instructions for Railway.
2) Keep deployment documentation aligned with runtime environment variables and service contracts.
3) Add or update verification/rollback/evidence checklist sections for operational readiness.
4) As the final implementation step, update `docs/development_backlog.yaml` to reflect BL-049 status and implementation evidence.
5) As the final documentation step, generate the next `docs/next_code_generation_prompt.md` for the next eligible backlog item using the same template structure previously used for BL-032-style roadmap prompts (title line, authoritative source, backlog context, restate-before-coding, task list, output format).

Output format:
- Provide a concise implementation plan first.
- Then provide unified diffs/patches per file.
- Then provide test/verification commands and expected results.
- Then provide the backlog/progression update summary (BL-049 status change + newly selected next queued backlog item).
```
