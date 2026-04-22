# Next Code Generation Prompt (Roadmap-Aligned)

As of 2026-04-22, there is **no queued `todo` item after BL-050** in `docs/development_backlog.yaml`.

Use this prompt to add and queue the next backlog item before implementation work resumes.

```text
You are the Codex implementation agent for `pressure_vessels`.
Task: Propose and add the next backlog item after BL-050 in `docs/development_backlog.yaml`.

Authoritative source:
- `docs/development_backlog.yaml`

Context (resolved as of 2026-04-22):
- BL-047 status is done.
- BL-049 status is done.
- BL-050 status is done.
- No remaining item is marked todo.

Task:
1) Propose BL-051 with clear scope, dependencies, acceptance criteria, and deliverables.
2) Keep backlog ordering deterministic and dependency-consistent.
3) Set BL-051 status to todo and leave all completed items unchanged.
4) Refresh this file so it points to the newly queued item.

Output format:
- Provide a concise implementation plan first.
- Then provide unified diffs/patches per file.
- Then provide validation commands and expected results.
- Then provide backlog progression summary.
```
