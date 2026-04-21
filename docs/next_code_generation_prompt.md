# Next Code Generation Prompt (Roadmap-Aligned)

Use this prompt to implement the **current next roadmap item: BL-041 — Expand engineering validation with independent references and edge envelopes**.

```text
You are implementing backlog item **BL-041: Expand engineering validation with independent references and edge envelopes** for the `pressure_vessels` repository.

Authoritative source:
- `docs/development_backlog.yaml`

Backlog context (resolved as of 2026-04-21):
- `BL-040` status is `done`.
- `BL-041` status is `todo`.
- `BL-041` dependencies are `BL-003e`, `BL-017`, and both are `done`.
- Therefore `BL-041` is the next eligible item.

Restate before coding:
- Item ID/title: BL-041 — Expand engineering validation with independent references and edge envelopes
- depends_on: [BL-003e, BL-017]
- acceptance criteria:
  1) Independent reference cases cover additional ASME Div 1 edge conditions.
  2) Explicit reject tests enforce invalid-domain or extrapolated input handling.
  3) Discrepancy triage workflow is documented when model-vs-reference deltas exceed tolerance.
- deliverables:
  1) Expanded reference-case dataset.
  2) Domain-envelope reject test suite.
  3) Validation discrepancy triage runbook.

Repository constraints:
- Keep changes minimal and focused; implement BL-041 only.
- Follow contract-driven integration and avoid undocumented interface drift.
- Preserve governance-by-default controls from `AGENT_GOVERNANCE.md`.
- Prefer incremental delivery over broad rewrites; keep behavior deterministic.

Likely relevant files:
- `tests/golden_examples/README.md`
- `tests/test_calculation_pipeline_golden_examples.py`
- `docs/interfaces/calculation_pipeline_contract.md`
- `README.md`

Task:
1) Extend independent reference/edge-case benchmark dataset for calculation validation.
2) Add explicit invalid-domain reject tests for envelope enforcement.
3) Document discrepancy triage workflow for tolerance exceedance.
4) Set `BL-041` status to `done` in `docs/development_backlog.yaml` once complete.
5) Update `docs/next_code_generation_prompt.md` to the subsequent eligible backlog item.

Output format:
- Provide a concise implementation plan first.
- Then provide unified diffs/patches per file.
- Then provide test/verification commands and expected results.
```

## Upcoming queue

The following items remain queued in dependency order. Select the next eligible
item from `docs/development_backlog.yaml` after BL-041 is completed.

1. **BL-042** — Automate release pipeline and environment promotion gates (`blocked`, deps: BL-012, BL-026, BL-038)
