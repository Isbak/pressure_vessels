# Next DX Generation Prompt (DXR Audit-Aligned)

DXR-015 was completed on 2026-04-20 and there is currently **no remaining eligible DX roadmap item** in `docs/dx_reusability_audit_2026-04-20.yaml`.

```text
No remaining eligible DX roadmap item.

When a new DXR finding is added with status: todo (and all dependencies done), update this file to point to that item.
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
15. **DXR-015** — Replace ad-hoc YAML parsing in check_tech_stack.py with a robust parser (`done`, deps: none)
