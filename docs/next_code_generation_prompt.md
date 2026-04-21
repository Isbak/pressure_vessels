# Next Code Generation Prompt (Roadmap-Aligned)

Use this prompt to implement the **current next roadmap item: BL-035 — Persist traceability and workflow state in runtime datastores**.

```text
You are implementing backlog item **BL-035: Persist traceability and workflow state in runtime datastores** for the `pressure_vessels` repository.

Authoritative source:
- `docs/development_backlog.yaml`

Backlog context (resolved as of 2026-04-21):
- `BL-034` status is `done`.
- `BL-035` status is `todo`.
- `BL-035` dependencies are `BL-006`, `BL-016`, `BL-024`, and `BL-029`, and all are `done`.
- Therefore `BL-035` is the next eligible item.

Restate before coding:
- Item ID/title: BL-035 — Persist traceability and workflow state in runtime datastores
- depends_on: [BL-006, BL-016, BL-024, BL-029]
- acceptance criteria:
  1) Workflow execution events are persisted in PostgreSQL with immutable revision IDs.
  2) Traceability graph writes are persisted in Neo4j with read/query API examples.
  3) Recovery test demonstrates run resume after process restart without evidence loss.
- deliverables:
  1) Persistent workflow event store integration.
  2) Neo4j-backed traceability write path.
  3) Recovery and resume test suite.

Repository constraints:
- Keep changes minimal and focused; implement BL-035 only.
- Follow contract-driven integration and avoid undocumented interface drift.
- Preserve governance-by-default controls from `AGENT_GOVERNANCE.md`.
- Prefer incremental delivery over broad rewrites; keep behavior deterministic.

Likely relevant files:
- `src/pressure_vessels/workflow_orchestrator.py`
- `src/pressure_vessels/traceability_pipeline.py`
- `docs/interfaces/workflow_orchestrator_contract.md`
- `docs/interfaces/traceability_pipeline_contract.md`
- `infra/platform/postgresql/module.boundaries.yaml`
- `infra/platform/neo4j/module.boundaries.yaml`

Task:
1) Add deterministic persistence path for workflow execution events (PostgreSQL-facing interface).
2) Add deterministic persistence path for traceability graph writes (Neo4j-facing interface).
3) Add recovery/resume test coverage proving no evidence loss after simulated restart.
4) Set `BL-035` status to `done` in `docs/development_backlog.yaml` once complete.
5) Update `docs/next_code_generation_prompt.md` to the subsequent eligible backlog item.

Output format:
- Provide a concise implementation plan first.
- Then provide unified diffs/patches per file.
- Then provide test/verification commands and expected results.
```

## Upcoming queue

The following items remain queued in dependency order. Select the next eligible
item from `docs/development_backlog.yaml` after BL-035 is completed.

1. **BL-036** — Implement standards package lifecycle controls and migration tests (`todo`, deps: BL-005, BL-008)
2. **BL-037** — Add deterministic PDF generation and signature verification harness (`todo`, deps: BL-015)
3. **BL-038** — Establish production security baseline for runtime interfaces (`todo`, deps: BL-022, BL-027)
4. **BL-039** — Define SLOs, telemetry, and incident response automation (`todo`, deps: BL-023, BL-026)
5. **BL-040** — Implement performance and scale benchmark suite (`todo`, deps: BL-017, BL-026)
6. **BL-041** — Expand engineering validation with independent references and edge envelopes (`todo`, deps: BL-003e, BL-017)
7. **BL-042** — Automate release pipeline and environment promotion gates (`blocked`, deps: BL-012, BL-026, BL-038)
