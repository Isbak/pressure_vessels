# Next DX Generation Prompt (DXR Audit-Aligned)

DXR-005 is the **next eligible DX remediation item** in `docs/dx_reusability_audit_2026-04-20.yaml` as of 2026-04-20.

```text
You are implementing DXR-005 in the `pressure_vessels` repo.

Problem:
The repository currently lacks a baseline formatting/lint configuration
for Python and JavaScript/TypeScript plus a shared `.editorconfig`.
Pre-commit runs governance and stack checks, but there is no consistent
style baseline to prevent drift across contributors and agent-authored PRs.

Conventions (apply to every DX-remediation PR):
- Work on a new branch `claude/fix-DXR-005` branched from `main`.
- Keep the diff minimal and scoped to this finding.
- Run `make v`, `./markdownlint-cli2 "**/*.md"`, and
  `python scripts/check_ci_governance.py` before committing.
- Do not introduce new runtime dependencies without updating the
  appropriate manifest (`pyproject.toml` for Python, the relevant
  `services/*/package.json` for Node).
- Reference this finding in the commit body:
  `Fixes DXR-005 per docs/dx_reusability_audit_2026-04-20.yaml`.

Task:
1. Add a root `.editorconfig` covering Python, JS/TS, YAML, and Markdown.
2. Add baseline formatter/linter configuration for Python and frontend/backend JS/TS workflows.
3. Wire the new checks into local validation and pre-commit with clear docs.
4. Ensure CI enforces or reports the baseline checks without regressing existing governance gates.
5. Last step before opening/merging the PR: update
   `docs/next_dx_generation_prompt.md` to the next eligible DXR item and
   set DXR-005 status to `done` in
   `docs/dx_reusability_audit_2026-04-20.yaml`.

Out of scope (tracked separately):
- Pinning the Node version (DXR-006).

Deliverable: one PR touching only the files needed for DXR-005
remediation plus the prompt/status files in the final step.
```

## Upcoming queue

Pick the first item with `status: todo` whose dependencies are all `done`.

1. **DXR-001** — Extend bootstrap to install JS service toolchains deterministically (`done`, deps: none)
2. **DXR-002** — Add JS service test/lint parity to the baseline validate bundle (`done`, deps: DXR-001)
3. **DXR-003** — Commit deterministic lockfiles for frontend and backend services (`done`, deps: DXR-001)
4. **DXR-004** — Provide .env.example scaffolding for local runtime profile (`done`, deps: none)
5. **DXR-005** — Baseline formatting and linting configuration (editorconfig + formatters) (`todo`, deps: none)
6. **DXR-006** — Pin Node toolchain version alongside tools/versions.json (`todo`, deps: none)
7. **DXR-007** — Add CODEOWNERS routing to operationalize Level 2 governance (`todo`, deps: none)
8. **DXR-008** — Reconcile platform IaC module deployment status with real artifacts (`todo`, deps: none)
9. **DXR-009** — Extract reusable GitHub Actions for adopters of the governance baseline (`todo`, deps: DXR-010)
10. **DXR-010** — Package governance scripts as a reusable Python module with an entry point (`todo`, deps: none)
11. **DXR-011** — Make risk-label heuristics declarative and project-overridable (`todo`, deps: DXR-010)
12. **DXR-012** — Provide a baseline scaffold for AGENT_GOVERNANCE cross-project adoption (`todo`, deps: DXR-009, DXR-010)
13. **DXR-013** — Ship devcontainer and Codespaces configuration for one-click onboarding (`todo`, deps: DXR-001, DXR-006)
14. **DXR-014** — Replace hard-coded INFRA_BOUNDARY_FILES with a data-driven manifest (`todo`, deps: none)
15. **DXR-015** — Replace ad-hoc YAML parsing in check_tech_stack.py with a robust parser (`todo`, deps: none)
