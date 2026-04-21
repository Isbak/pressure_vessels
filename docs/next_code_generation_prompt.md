# Next Code Generation Prompt (Roadmap-Aligned)

Use this prompt to implement the **current next roadmap item: BL-039 — Define SLOs, telemetry, and incident response automation**.

```text
You are implementing backlog item **BL-039: Define SLOs, telemetry, and incident response automation** for the `pressure_vessels` repository.

Authoritative source:
- `docs/development_backlog.yaml`

Backlog context (resolved as of 2026-04-21):
- `BL-038` status is `done`.
- `BL-039` status is `todo`.
- `BL-039` dependencies are `BL-023`, `BL-026`, and both are `done`.
- Therefore `BL-039` is the next eligible item.

Restate before coding:
- Item ID/title: BL-039 — Define SLOs, telemetry, and incident response automation
- depends_on: [BL-023, BL-026]
- acceptance criteria:
  1) SLOs are published for orchestration latency, run success rate, and artifact export success.
  2) RED/USE metrics and traces are instrumented for critical pipeline stages.
  3) Alert routing and incident runbook drill are validated in a simulated failure scenario.
- deliverables:
  1) Service SLO definition and dashboards.
  2) Pipeline telemetry instrumentation updates.
  3) Incident automation drill report.

Repository constraints:
- Keep changes minimal and focused; implement BL-039 only.
- Follow contract-driven integration and avoid undocumented interface drift.
- Preserve governance-by-default controls from `AGENT_GOVERNANCE.md`.
- Prefer incremental delivery over broad rewrites; keep behavior deterministic.

Likely relevant files:
- `docs/runbooks/platform_runtime_stack_operations.md`
- `docs/incidents/TEMPLATE.md`
- `src/pressure_vessels/workflow_orchestrator.py`
- `docs/interfaces/workflow_orchestrator_contract.md`

Task:
1) Define and document runtime SLO targets with deterministic measurement windows.
2) Add telemetry schema/hooks for RED/USE metrics across critical stages.
3) Add simulated incident drill artifact and alert routing coverage.
4) Set `BL-039` status to `done` in `docs/development_backlog.yaml` once complete.
5) Update `docs/next_code_generation_prompt.md` to the subsequent eligible backlog item.

Output format:
- Provide a concise implementation plan first.
- Then provide unified diffs/patches per file.
- Then provide test/verification commands and expected results.
```

## Upcoming queue

The following items remain queued in dependency order. Select the next eligible
item from `docs/development_backlog.yaml` after BL-039 is completed.

1. **BL-040** — Implement performance and scale benchmark suite (`todo`, deps: BL-017, BL-026)
2. **BL-041** — Expand engineering validation with independent references and edge envelopes (`todo`, deps: BL-003e, BL-017)
3. **BL-042** — Automate release pipeline and environment promotion gates (`blocked`, deps: BL-012, BL-026, BL-038)
