# Next DX Generation Prompt (DXR Audit-Aligned)

DXR-015 is the **next eligible DX remediation item** in `docs/dx_reusability_audit_2026-04-20.yaml` as of 2026-04-20.

```text
You are implementing DXR-015 in the `pressure_vessels` repo.

Problem:
`scripts/check_tech_stack.py` currently parses YAML via ad-hoc prefix/string
logic instead of a robust YAML parser. The current behavior is fragile for
schema evolution and hard to reuse across repositories.

Conventions (apply to every DX-remediation PR):
- Work on a new branch `claude/fix-DXR-015` branched from `main`.
- Keep the diff minimal and scoped to this finding.
- Run `make v`, `./markdownlint-cli2 "**/*.md"`, and
  `python scripts/check_ci_governance.py` before committing.
- Do not introduce new runtime dependencies without updating the
  appropriate manifest (`pyproject.toml` for Python, the relevant
  `services/*/package.json` for Node).
- Reference this finding in the commit body:
  `Fixes DXR-015 per docs/dx_reusability_audit_2026-04-20.yaml`.

Task:
1. Replace ad-hoc YAML parsing in `scripts/check_tech_stack.py` with a robust
   parser implementation.
2. Add the parser dependency to `pyproject.toml` and keep install paths
   consistent with existing tooling.
3. Add/adjust tests to cover prior edge cases and at least one schema variation
   (comments, quoted values, or alternate indentation).
4. Keep the current CLI behavior and error semantics intact where possible.
5. Last step before opening/merging the PR: update
   `docs/next_dx_generation_prompt.md` to the next eligible DXR item and set
   DXR-015 status to `done` in `docs/dx_reusability_audit_2026-04-20.yaml`.

Out of scope (tracked separately):
- Rewriting unrelated governance or CI policies.
- Broad refactors outside `check_tech_stack.py` + directly related tests/docs.

Deliverable: one PR touching only the files needed for DXR-015 remediation
plus the prompt/status files in the final step.
```

## Upcoming queue

Pick the first item with `status: todo` whose dependencies are all `done`.

1. **DXR-001** — Extend bootstrap to install JS service toolchains deterministically (`done`, deps: none)
2. **DXR-002** — Add JS service test/lint parity to the baseline validate bundle (`done`, deps: DXR-001)
3. **DXR-003** — Commit deterministic lockfiles for frontend and backend services (`done`, deps: DXR-001)
4. **DXR-004** — Provide .env.example scaffolding for local runtime profile (`done`, deps: none)
5. **DXR-005** — Baseline formatting and linting configuration (editorconfig + formatters) (`done`, deps: none)
6. **DXR-006** — Pin Node toolchain version alongside tools/versions.json (`done`, deps: none)
7. **DXR-007** — Add CODEOWNERS routing to operationalize Level 2 governance (`done`, deps: none)
8. **DXR-008** — Reconcile platform IaC module deployment status with real artifacts (`done`, deps: none)
9. **DXR-009** — Extract reusable GitHub Actions for adopters of the governance baseline (`done`, deps: DXR-010)
10. **DXR-010** — Package governance scripts as a reusable Python module with an entry point (`done`, deps: none)
11. **DXR-011** — Make risk-label heuristics declarative and project-overridable (`done`, deps: DXR-010)
12. **DXR-012** — Provide a baseline scaffold for AGENT_GOVERNANCE cross-project adoption (`done`, deps: DXR-009, DXR-010)
13. **DXR-013** — Ship devcontainer and Codespaces configuration for one-click onboarding (`done`, deps: DXR-001, DXR-006)
14. **DXR-014** — Replace hard-coded INFRA_BOUNDARY_FILES with a data-driven manifest (`done`, deps: none)
15. **DXR-015** — Replace ad-hoc YAML parsing in check_tech_stack.py with a robust parser (`todo`, deps: none)
