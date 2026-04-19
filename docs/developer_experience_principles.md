# Developer Experience Principles

This document captures repository-level principles for an optimal developer
experience (DX) on the pressure_vessels platform.

## Purpose

- Provide a shared definition of "good DX" across platform, domain, and QA teams.
- Align delivery ergonomics with governance and compliance constraints.
- Prioritize fast feedback loops without weakening safety controls.

## Principles

1. **Fast local feedback first**
   - Every common development loop should have a short, deterministic local command path.
   - New contributors should reach a successful baseline check quickly.

2. **Single source of truth for workflows**
   - Commands, runbooks, and ownership boundaries must be documented once and reused.
   - Roadmap items should reference existing contracts/runbooks instead of duplicating behavior text.

3. **Governance by default, automation where possible**
   - Governance controls (risk labels, required checks, approvals) remain non-optional.
   - Developer burden should be reduced through automation, not by bypassing controls.

4. **Contract-driven integration**
   - Frontend/backend/pipeline boundaries should evolve through explicit contracts and contract tests.
   - Schema drift should be detected before merge.

5. **Incremental delivery over big-bang rewrites**
   - Prefer small, reviewable increments with clear acceptance criteria and dependencies.
   - Couple each DX initiative to observable outcomes (time-to-first-success, PR cycle time, etc.).

6. **Operational empathy**
   - DX improvements should help both builders and operators.
   - Local development, CI behavior, and runtime operations should remain aligned.

7. **Portable by default**
   - Baseline DX workflows should be reusable across projects with minimal edits.
   - Project-specific differences should be isolated to configuration, not governance bypasses.

## Applying these principles

- Use `docs/platform_roadmap.yaml` as the planning artifact for DX work.
- Link each DX backlog item to governing contracts/runbooks.
- Evaluate roadmap changes against these principles before introducing new fields or workflows.

## Documentation touchpoints

- `docs/platform_roadmap.yaml` — machine-readable DX roadmap.
- `docs/development_backlog.yaml` — engineering backlog schema baseline.
- `AGENT_GOVERNANCE.md` — governance constraints that DX must preserve.
- `docs/runbooks/platform_runtime_stack_operations.md` — runtime operations and ownership boundaries.
