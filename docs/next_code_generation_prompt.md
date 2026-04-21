# Next Code Generation Prompt (Roadmap-Aligned)

Use this prompt to implement the **current next roadmap item: BL-038 — Establish production security baseline for runtime interfaces**.

```text
You are implementing backlog item **BL-038: Establish production security baseline for runtime interfaces** for the `pressure_vessels` repository.

Authoritative source:
- `docs/development_backlog.yaml`

Backlog context (resolved as of 2026-04-21):
- `BL-037` status is `done`.
- `BL-038` status is `todo`.
- `BL-038` dependencies are `BL-022`, `BL-027`, and both are `done`.
- Therefore `BL-038` is the next eligible item.

Restate before coding:
- Item ID/title: BL-038 — Establish production security baseline for runtime interfaces
- depends_on: [BL-022, BL-027]
- acceptance criteria:
  1) Backend endpoints require role-scoped auth tokens for engineer/reviewer/approver personas.
  2) Secrets are loaded through approved secrets module paths without plaintext fallbacks.
  3) Security audit trail captures actor, action, artifact, and decision for approval gates.
- deliverables:
  1) Role-based API authorization policy.
  2) Secrets integration hardening checklist and tests.
  3) Security audit event schema and persistence.

Repository constraints:
- Keep changes minimal and focused; implement BL-038 only.
- Follow contract-driven integration and avoid undocumented interface drift.
- Preserve governance-by-default controls from `AGENT_GOVERNANCE.md`.
- Prefer incremental delivery over broad rewrites; keep behavior deterministic.

Likely relevant files:
- `AGENT_GOVERNANCE.md`
- `docs/governance/ci_governance_policy.v1.json`
- `src/pressure_vessels/enterprise_integration_pipeline.py`
- `docs/interfaces/backend_prompt_api_contract.md`

Task:
1) Add role-scoped auth token enforcement for backend runtime interfaces.
2) Remove plaintext secret fallback paths and route through approved secrets module interfaces.
3) Add/extend security audit trail schema coverage for approval-gate events.
4) Set `BL-038` status to `done` in `docs/development_backlog.yaml` once complete.
5) Update `docs/next_code_generation_prompt.md` to the subsequent eligible backlog item.

Output format:
- Provide a concise implementation plan first.
- Then provide unified diffs/patches per file.
- Then provide test/verification commands and expected results.
```

## Upcoming queue

The following items remain queued in dependency order. Select the next eligible
item from `docs/development_backlog.yaml` after BL-038 is completed.

1. **BL-039** — Define SLOs, telemetry, and incident response automation (`todo`, deps: BL-023, BL-026)
2. **BL-040** — Implement performance and scale benchmark suite (`todo`, deps: BL-017, BL-026)
3. **BL-041** — Expand engineering validation with independent references and edge envelopes (`todo`, deps: BL-003e, BL-017)
4. **BL-042** — Automate release pipeline and environment promotion gates (`blocked`, deps: BL-012, BL-026, BL-038)
