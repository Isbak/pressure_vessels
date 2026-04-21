# Next Code Generation Prompt (Roadmap-Aligned)

Use this prompt to implement the **current next roadmap item: BL-034 — Replace service placeholders with runnable API/UI vertical slice**.

```text
You are implementing backlog item **BL-034: Replace service placeholders with runnable API/UI vertical slice** for the `pressure_vessels` repository.

Authoritative source:
- `docs/development_backlog.yaml`

Backlog context (resolved as of 2026-04-20):
- `BL-033` status is `done`.
- `BL-034` status is `todo`.
- `BL-034` dependencies are `BL-018` and `BL-026`, and both are `done`.
- Therefore `BL-034` is the next eligible item.

Restate before coding:
- Item ID/title: BL-034 — Replace service placeholders with runnable API/UI vertical slice
- depends_on: [BL-018, BL-026]
- acceptance criteria:
  1) Backend exposes versioned endpoints for starting a design run and retrieving run status/artifacts.
  2) Frontend can submit a basic pressure-vessel input payload and display workflow state and compliance summary.
  3) End-to-end contract test validates UI-to-API-to-orchestrator happy-path flow.
- deliverables:
  1) Backend API routes and handlers.
  2) Frontend design-run submission and status views.
  3) End-to-end contract test coverage.

Repository constraints:
- Keep changes minimal and focused; implement BL-034 only.
- Follow contract-driven integration and avoid undocumented interface drift.
- Preserve governance-by-default controls from `AGENT_GOVERNANCE.md`.
- Prefer incremental delivery over broad rewrites; keep behavior deterministic.

Likely relevant files:
- `services/backend/src/main.ts`
- `services/frontend/app/page.tsx`
- `services/frontend/app/result/page.tsx`
- `services/frontend/app/api/prompt/route.ts`
- `docs/interfaces/backend_prompt_api_contract.md`
- `docs/interfaces/workflow_orchestrator_contract.md`
- `README.md#6-end-to-end-workflow`
- `docs/developer_experience_principles.md`

Task:
1) Implement minimal versioned backend endpoints for design-run start and run-status/artifact retrieval.
2) Implement frontend submission + status/result rendering for the happy path.
3) Add/update end-to-end contract tests for UI -> API -> orchestrator flow.
4) Set `BL-034` status to `done` in `docs/development_backlog.yaml` once complete.
5) Update `docs/next_code_generation_prompt.md` so it points at the subsequent eligible backlog item.

Output format:
- Provide a concise implementation plan first.
- Then provide unified diffs/patches per file.
- Then provide test/verification commands and expected results.
```

## Upcoming queue

The following items remain queued in dependency order. Select the next eligible
item from `docs/development_backlog.yaml` after BL-034 is completed.

1. **BL-035** — Persist traceability and workflow state in runtime datastores (`todo`, deps: BL-006, BL-016, BL-024, BL-029)
2. **BL-036** — Implement standards package lifecycle controls and migration tests (`todo`, deps: BL-005, BL-008)
3. **BL-037** — Add deterministic PDF generation and signature verification harness (`todo`, deps: BL-015)
4. **BL-038** — Establish production security baseline for runtime interfaces (`todo`, deps: BL-022, BL-027)
5. **BL-039** — Define SLOs, telemetry, and incident response automation (`todo`, deps: BL-023, BL-026)
6. **BL-040** — Implement performance and scale benchmark suite (`todo`, deps: BL-017, BL-026)
7. **BL-041** — Expand engineering validation with independent references and edge envelopes (`todo`, deps: BL-003e, BL-017)
8. **BL-042** — Automate release pipeline and environment promotion gates (`blocked`, deps: BL-012, BL-026, BL-038)
