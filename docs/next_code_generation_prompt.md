# Next Code Generation Prompt (Roadmap-Aligned)

Use this prompt to implement the **next queued roadmap item: BL-042 — Automate release pipeline and environment promotion gates**.

> Note: As of 2026-04-21, all `todo` items are complete. `BL-042` remains `blocked` in `docs/development_backlog.yaml`; unblock prerequisites/policy approval before execution.

```text
You are implementing backlog item **BL-042: Automate release pipeline and environment promotion gates** for the `pressure_vessels` repository.

Authoritative source:
- `docs/development_backlog.yaml`

Backlog context (resolved as of 2026-04-21):
- `BL-041` status is `done`.
- `BL-042` status is `blocked`.
- `BL-042` dependencies are `BL-012`, `BL-026`, `BL-038`, and all are `done`.
- Therefore `BL-042` is the next queued item pending unblock decision.

Restate before coding:
- Item ID/title: BL-042 — Automate release pipeline and environment promotion gates
- depends_on: [BL-012, BL-026, BL-038]
- acceptance criteria:
  1) Signed release artifacts and provenance attestations are generated on tagged builds.
  2) Promotion requires passing governance, security, and regression gates.
  3) Rollback automation restores the previous known-good release with audit evidence.
- deliverables:
  1) Release provenance and signing workflow.
  2) Environment promotion gate automation.
  3) Rollback automation playbook and validation report.

Repository constraints:
- Keep changes minimal and focused; implement BL-042 only.
- Follow contract-driven integration and avoid undocumented interface drift.
- Preserve governance-by-default controls from `AGENT_GOVERNANCE.md`.
- Prefer incremental delivery over broad rewrites; keep behavior deterministic.

Likely relevant files:
- `AGENT_GOVERNANCE.md`
- `docs/governance/ci_governance_policy.v1.json`
- `docs/runbooks/platform_runtime_stack_operations.md`
- `.github/workflows/`

Task:
1) Implement signed release/provenance workflow for tagged builds.
2) Add promotion gates enforcing governance, security, and regression checks.
3) Add rollback automation with audit evidence capture.
4) Set `BL-042` status to `done` in `docs/development_backlog.yaml` once complete.
5) Update `docs/next_code_generation_prompt.md` to the next backlog state.

Output format:
- Provide a concise implementation plan first.
- Then provide unified diffs/patches per file.
- Then provide test/verification commands and expected results.
```
