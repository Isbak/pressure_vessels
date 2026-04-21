# Next Code Generation Prompt (Roadmap-Aligned)

Use this prompt to implement the **current next roadmap item: BL-040 — Implement performance and scale benchmark suite**.

```text
You are implementing backlog item **BL-040: Implement performance and scale benchmark suite** for the `pressure_vessels` repository.

Authoritative source:
- `docs/development_backlog.yaml`

Backlog context (resolved as of 2026-04-21):
- `BL-039` status is `done`.
- `BL-040` status is `todo`.
- `BL-040` dependencies are `BL-017`, `BL-026`, and both are `done`.
- Therefore `BL-040` is the next eligible item.

Restate before coding:
- Item ID/title: BL-040 — Implement performance and scale benchmark suite
- depends_on: [BL-017, BL-026]
- acceptance criteria:
  1) Benchmark harness measures throughput and latency under concurrent workflow runs.
  2) Bottlenecks are identified with profiling artifacts and mitigation recommendations.
  3) Capacity envelope is documented with tested limits and safe operating guidance.
- deliverables:
  1) Load and concurrency benchmark harness.
  2) Profiling artifact bundle.
  3) Capacity envelope report.

Repository constraints:
- Keep changes minimal and focused; implement BL-040 only.
- Follow contract-driven integration and avoid undocumented interface drift.
- Preserve governance-by-default controls from `AGENT_GOVERNANCE.md`.
- Prefer incremental delivery over broad rewrites; keep behavior deterministic.

Likely relevant files:
- `tests/golden_examples/benchmark_manifest.json`
- `docs/runbooks/workflow_orchestrator_retries_and_escalations.md`
- `src/pressure_vessels/workflow_orchestrator.py`
- `README.md`

Task:
1) Add deterministic concurrency/latency benchmark harness for workflow orchestration paths.
2) Produce profiling outputs and mitigation notes suitable for CI artifact retention.
3) Document tested capacity envelope and safe operating guidance.
4) Set `BL-040` status to `done` in `docs/development_backlog.yaml` once complete.
5) Update `docs/next_code_generation_prompt.md` to the subsequent eligible backlog item.

Output format:
- Provide a concise implementation plan first.
- Then provide unified diffs/patches per file.
- Then provide test/verification commands and expected results.
```

## Upcoming queue

The following items remain queued in dependency order. Select the next eligible
item from `docs/development_backlog.yaml` after BL-040 is completed.

1. **BL-041** — Expand engineering validation with independent references and edge envelopes (`todo`, deps: BL-003e, BL-017)
2. **BL-042** — Automate release pipeline and environment promotion gates (`blocked`, deps: BL-012, BL-026, BL-038)
