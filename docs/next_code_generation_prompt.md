# Next Code Generation Prompt (Roadmap-Aligned)

Use this prompt to implement the **current next roadmap item: BL-036 — Implement standards package lifecycle controls and migration tests**.

```text
You are implementing backlog item **BL-036: Implement standards package lifecycle controls and migration tests** for the `pressure_vessels` repository.

Authoritative source:
- `docs/development_backlog.yaml`

Backlog context (resolved as of 2026-04-21):
- `BL-035` status is `done`.
- `BL-036` status is `todo`.
- `BL-036` dependencies are `BL-005` and `BL-008`, and both are `done`.
- Therefore `BL-036` is the next eligible item.

Restate before coding:
- Item ID/title: BL-036 — Implement standards package lifecycle controls and migration tests
- depends_on: [BL-005, BL-008]
- acceptance criteria:
  1) Version promotion flow supports draft-to-candidate-to-released transitions with approvals.
  2) Cross-version regression suite detects calculation/compliance drift before release.
  3) Impact analysis reports list affected projects and required selective re-verification scope.
- deliverables:
  1) Standards package promotion workflow.
  2) Cross-version migration regression suite.
  3) Version impact analysis report template.

Repository constraints:
- Keep changes minimal and focused; implement BL-036 only.
- Follow contract-driven integration and avoid undocumented interface drift.
- Preserve governance-by-default controls from `AGENT_GOVERNANCE.md`.
- Prefer incremental delivery over broad rewrites; keep behavior deterministic.

Likely relevant files:
- `src/pressure_vessels/standards_ingestion_pipeline.py`
- `docs/interfaces/standards_ingestion_pipeline_contract.md`
- `docs/runbooks/standards_ingestion_pipeline_runbook.md`
- `artifacts/bl-005/StandardsPackage.v1.sample.json`

Task:
1) Add deterministic standards package lifecycle transitions with approval metadata (draft/candidate/released).
2) Add cross-version migration/regression checks for calculation/compliance drift detection.
3) Add impact analysis report generation listing affected projects and selective re-verification scope.
4) Set `BL-036` status to `done` in `docs/development_backlog.yaml` once complete.
5) Update `docs/next_code_generation_prompt.md` to the subsequent eligible backlog item.

Output format:
- Provide a concise implementation plan first.
- Then provide unified diffs/patches per file.
- Then provide test/verification commands and expected results.
```

## Upcoming queue

The following items remain queued in dependency order. Select the next eligible
item from `docs/development_backlog.yaml` after BL-036 is completed.

1. **BL-037** — Add deterministic PDF generation and signature verification harness (`todo`, deps: BL-015)
2. **BL-038** — Establish production security baseline for runtime interfaces (`todo`, deps: BL-022, BL-027)
3. **BL-039** — Define SLOs, telemetry, and incident response automation (`todo`, deps: BL-023, BL-026)
4. **BL-040** — Implement performance and scale benchmark suite (`todo`, deps: BL-017, BL-026)
5. **BL-041** — Expand engineering validation with independent references and edge envelopes (`todo`, deps: BL-003e, BL-017)
6. **BL-042** — Automate release pipeline and environment promotion gates (`blocked`, deps: BL-012, BL-026, BL-038)
