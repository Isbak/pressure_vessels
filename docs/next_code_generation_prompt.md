# Next Code Generation Prompt (Roadmap-Aligned)

Use this prompt to implement the **current next roadmap item: BL-016**.

```text
You are implementing backlog item **BL-016: Implement workflow orchestrator with human-in-the-loop approval gates** for the `pressure_vessels` repository.

Authoritative source:
- `docs/development_backlog.yaml`

Backlog context (resolved as of 2026-04-18):
- `BL-016` status is `todo`.
- `BL-016` dependencies are `BL-004`, `BL-007`, and `BL-012`, and all are `done`.
- Therefore `BL-016` is the next eligible item.

Restate before coding:
- Item ID/title: BL-016 — Implement workflow orchestrator with human-in-the-loop approval gates
- depends_on: [BL-004, BL-007, BL-012]
- acceptance criteria:
  1) End-to-end stage orchestration is deterministic with explicit gate states.
  2) Human approvals are captured as immutable events with role and timestamp metadata.
  3) Retry/escalation logic is observable and produces audit-ready execution traces.
- deliverables:
  1) Orchestrator state model and execution API
  2) Approval-gate event schema
  3) Operational runbook for retries/escalations

Repository constraints:
- Keep changes minimal and focused.
- Follow existing style and module patterns in `src/pressure_vessels/`.
- Add/extend tests in `tests/` for any new behavior.
- Prefer deterministic logic (no randomness/time-dependent values unless explicitly controlled).

Likely relevant files:
- `src/pressure_vessels/` (new orchestrator module expected)
- `docs/interfaces/` (new/updated orchestrator contract)
- `docs/runbooks/` (runbook for retry/escalation flow)
- `tests/` (orchestrator and gate-event coverage)

Task:
1) Implement BL-016 behavior using existing repository patterns.
2) Satisfy each BL-016 acceptance criterion explicitly.
3) Deliver each BL-016 deliverable with minimal, auditable changes.
4) Add/extend tests under `tests/` for new behavior.
5) Update related architecture/interface docs under `docs/`.
6) Update `docs/development_backlog.yaml` status for BL-016 when complete.
7) Update `docs/next_code_generation_prompt.md` so it points at the subsequent backlog item.

Output format:
- Provide a concise implementation plan first.
- Then provide unified diffs/patches per file.
- Then provide test commands and expected results.
- Then provide a short risk/assumption note.

Do not modify unrelated files.
```
