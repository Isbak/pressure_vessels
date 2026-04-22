# Next Code Generation Prompt (Roadmap-Aligned)

Use this prompt to implement the **next queued roadmap item: backlog queue refresh (no currently eligible `todo` item after BL-049)**.

```text
You are performing backlog queue refresh for the `pressure_vessels` repository because no backlog item is currently eligible after BL-049.

Authoritative source:
- `docs/development_backlog.yaml`

Backlog context (resolved as of 2026-04-22):
- `BL-047` status is `done`.
- `BL-048` status is `done`.
- `BL-049` status is `done`.
- There are no remaining `todo` items whose dependencies are fully `done`.
- Therefore there is no next queued implementation item at this time.

Restate before coding:
- Item ID/title: Backlog queue refresh — identify and prepare the next eligible roadmap item
- depends_on: []
- acceptance criteria:
  1) Determine whether any existing `todo` item is now dependency-unblocked.
  2) If none are eligible, document that queue is blocked and identify minimal unblocking prerequisite work.
  3) Publish updated operator prompt for the newly eligible item (or explicit blocked-queue handoff).
- deliverables:
  1) Updated backlog progression notes with queued/blocked status.
  2) Next `docs/next_code_generation_prompt.md` targeting the newly eligible backlog item or blocked-queue action.
  3) Evidence references for queue-resolution decision.

Repository constraints:
- Keep changes minimal and focused on backlog progression only.
- Follow contract-driven integration and avoid undocumented interface drift.
- Preserve governance-by-default controls from `AGENT_GOVERNANCE.md`.
- Prefer incremental delivery over broad rewrites; keep behavior deterministic.

Likely relevant files:
- `docs/development_backlog.yaml`
- `docs/next_code_generation_prompt.md`
- `docs/runbooks/platform_runtime_stack_operations.md`

Task:
1) Re-evaluate backlog dependency graph and identify the next eligible `todo` item.
2) If no item is eligible, document blocked state and the concrete prerequisite needed to unblock queue progression.
3) Update `docs/development_backlog.yaml` only if progression metadata needs correction.
4) Generate the next `docs/next_code_generation_prompt.md` using this template structure with refreshed context.

Output format:
- Provide a concise implementation plan first.
- Then provide unified diffs/patches per file.
- Then provide test/verification commands and expected results.
- Then provide the backlog/progression update summary (queue state + next action).
```
