# Next DX Generation Prompt (DXR Audit-Aligned)

DXR-003 is the **next eligible DX remediation item** in `docs/dx_reusability_audit_2026-04-20.yaml` as of 2026-04-20.

```text
You are implementing DXR-003 in the `pressure_vessels` repo.

Problem:
`services/frontend` and `services/backend` declare Node dependencies but no
committed lockfiles. This weakens deterministic local/CI installs and drifts
from the reproducibility expectations in README.md and
`docs/developer_experience_principles.md`.

Conventions (apply to every DX-remediation PR):
- Work on a new branch `claude/fix-DXR-003` branched from `main`.
- Keep the diff minimal and scoped to this finding.
- Run `make v`, `./markdownlint-cli2 "**/*.md"`, and
  `python scripts/check_ci_governance.py` before committing.
- Do not introduce new runtime dependencies without updating the
  appropriate manifest (`pyproject.toml` for Python, the relevant
  `services/*/package.json` for Node).
- Reference this finding in the commit body:
  `Fixes DXR-003 per docs/dx_reusability_audit_2026-04-20.yaml`.

Task:
1. Generate and commit deterministic lockfiles for `services/frontend` and
   `services/backend` using the repository’s current package manager path.
2. Ensure bootstrap/CI install commands consume those lockfiles in a
   deterministic mode.
3. Document lockfile hygiene (regeneration command and reviewer expectations).
4. Update docs/developer_command_reference.md parity notes if command behavior
   changes.
5. Add or extend tests that assert lockfiles are present and referenced by the
   canonical bootstrap/validation path.
6. Last step before opening/merging the PR: update
   `docs/next_dx_generation_prompt.md` to the next eligible DXR item and
   set DXR-003 status to `done` in
   `docs/dx_reusability_audit_2026-04-20.yaml`.

Out of scope (tracked separately):
- Providing `.env.example` (DXR-004).
- Formatter/linter baseline (DXR-005).
- Pinning the Node version (DXR-006).

Deliverable: one PR touching only the files needed for DXR-003
remediation plus the prompt/status files in the final step.
```

## Upcoming queue

Pick the first item with `status: todo` whose dependencies are all `done`.

1. **DXR-001** — Extend bootstrap to install JS service toolchains deterministically (`done`, deps: none)
2. **DXR-002** — Add JS service test/lint parity to the baseline validate bundle (`done`, deps: DXR-001)
3. **DXR-003** — Commit deterministic lockfiles for frontend and backend services (`todo`, deps: DXR-001)
4. **DXR-004** — Provide .env.example scaffolding for local runtime profile (`todo`, deps: none)
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
