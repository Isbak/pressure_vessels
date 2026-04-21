# Next DX Generation Prompt (Roadmap-Aligned)

Use this prompt to implement the **next queued DX roadmap item: DX-011 — Keep local `make validate` green across audit cycles**, recorded in `docs/platform_roadmap.yaml`.

> Note: As of 2026-04-21, the predecessor DX reusability audit (`docs/dx_reusability_audit_2026-04-20.yaml`) is fully remediated (DXR-001..DXR-015 `done`). The 2026-04-21 full-repo audit introduced DX-011..DX-014 in `docs/platform_roadmap.yaml` to track audit-driven DX hardening. DX-011 is the first `status: todo` item with all `depends_on` resolved and is therefore the queued target.

```text
You are implementing DX roadmap item **DX-011: Keep local `make validate`
green across audit cycles** for the `pressure_vessels` repository.

Authoritative sources:
- docs/platform_roadmap.yaml
- docs/audit_findings_2026-04-21.yaml (AF-016 supplies the concrete failures)
- docs/development_backlog.yaml (BL-043 supplies the implementation work)

Selection rule used:
1) Choose the first DX-* item in docs/platform_roadmap.yaml with status: todo
   whose depends_on entries are all status: done.
2) Implement only that item with minimal, focused changes.
3) Last step: update this prompt file and the item status in
   docs/platform_roadmap.yaml.

Restate before coding:
- Item ID/title: DX-011 — Keep local `make validate` green across audit cycles
- depends_on: [DX-003, DX-009]
- acceptance criteria:
  1) `make validate` returns 0 on main at all times; an audit cycle must not
     leave a red baseline.
  2) Any audit that introduces failing tests files a corresponding BL-*
     item and opens a remediation PR before the audit is considered closed.
  3) Developers can reproduce the CI-required signal locally via a single
     bootstrap + validate invocation documented in
     docs/developer_quickstart.md.
- deliverables:
  1) Green-baseline check in place on every audit branch (coordinated with
     BL-043 remediation work).
  2) Documented expectation in AGENT_GOVERNANCE.md or
     docs/developer_quickstart.md.

Repository constraints:
- Keep changes minimal and focused; implement DX-011 only.
- Do not rewrite unrelated DX-* items or bypass governance controls.
- Preserve governance-by-default controls from AGENT_GOVERNANCE.md.
- Prefer contract-anchored tests over sentinel strings (this rule is the
  DX-011 follow-up surfaced by DX-012/AF-019).

Likely relevant files:
- Makefile
- .github/workflows/ci.yml
- docs/developer_quickstart.md
- AGENT_GOVERNANCE.md
- docs/platform_roadmap.yaml
- docs/development_backlog.yaml (cross-ref BL-043)

Task:
1) Coordinate with BL-043 so the pytest baseline is restored to green (that
   backlog item performs the concrete test fixes).
2) Add an audit-cycle expectation to AGENT_GOVERNANCE.md (or
   docs/developer_quickstart.md) that no audit may be marked complete while
   `make validate` is red on the audit branch.
3) If useful, add a Makefile/CI sanity step that surfaces the red state
   explicitly rather than just failing pytest.
4) Set DX-011 status to `done` in docs/platform_roadmap.yaml once the
   baseline is green and the expectation is documented.
5) Regenerate this file to point to the next eligible DX-* item (DX-012).

Required checks before closing DX-011:
- pytest
- make validate
- ./markdownlint-cli2 "**/*.md"
- python scripts/check_ci_governance.py

Output format:
- Provide a concise implementation plan first.
- Then provide unified diffs/patches per file.
- Then provide test/verification commands and expected results.
```

## Upcoming DX queue (first-todo-first)

Selection rule: pick the first `status: todo` DX-* item in
`docs/platform_roadmap.yaml` whose `depends_on` are all `done`.

1. **DX-011** — Keep local `make validate` green across audit cycles (P0, deps: DX-003, DX-009).
2. **DX-012** — Guard sprint-brittle tests with backlog-derived expectations (P1, deps: DX-011).
3. **DX-013** — Surface coverage and harness signal to developers (P2, deps: DX-011).
4. **DX-014** — Align onboarding env example and skeleton-module READMEs (P2, deps: DX-001).

## Predecessor manifest (reference)

The 2026-04-20 DX reusability audit (`docs/dx_reusability_audit_2026-04-20.yaml`) is fully remediated; there is no remaining eligible DX roadmap item in the predecessor DXR queue:

- DXR-001..DXR-015 — all `status: done` as of 2026-04-20.

> Compatibility note: the sentinel phrase above ("no remaining eligible DX roadmap item") is preserved for
> `tests/test_preview_environment_dx010.py::test_dx010_closed_out_in_roadmap_and_prompt_advanced`, which is
> flagged under AF-019 (brittle sprint-sentinel tests) and will be rewritten to derive expectations from the
> roadmap itself as part of BL-043.

Regenerate this file whenever any DX-* item changes status.
