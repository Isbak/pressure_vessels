# Next Audit Generation Prompt (Findings-Aligned)

The next eligible audit finding is **AF-004** from
`docs/audit_findings_2026-04-20.yaml` (severity: critical, status: todo,
no open dependencies).

```text
Selection rule used:
1) Choose the first finding in docs/audit_findings_2026-04-20.yaml with
   status: todo (or in_progress if already claimed for active remediation).
2) Verify every depends_on entry has status: done.
3) Implement only that finding with minimal, focused changes.
4) Last step: update this prompt file and the finding status in
   docs/audit_findings_2026-04-20.yaml.
```

## Prompt — AF-004 Fail closed on MVP geometry defaults in production mode (Critical)

```text
You are fixing audit finding AF-004 in the `pressure_vessels` repo.

Problem:
`src/pressure_vessels/calculation_pipeline.py` currently applies MVP geometry
defaults when `sizing_input` is missing and only emits `warnings.warn(...)`.
In production this can allow placeholder geometry to flow into certification
artifacts.

Conventions (apply to every audit-remediation PR):
- Work on a new branch `claude/fix-AF-004` branched from `main`.
- Keep the diff minimal and scoped to this finding.
- Run `pytest`, `./markdownlint-cli2 "**/*.md"`, and
  `python scripts/check_ci_governance.py` before committing.
- Do not introduce new runtime dependencies without adding them to
  `pyproject.toml`.
- Reference this finding in the commit body: `Fixes AF-004 per
  docs/audit_findings_2026-04-20.yaml`.

Task:
1. Make missing-geometry behavior fail closed by default via
   `MissingGeometryInputError`.
2. Keep MVP default behavior behind an explicit opt-in (`use_mvp_defaults=True`)
   and ensure this path is visibly tagged for non-production use.
3. Preserve deterministic behavior for callers/tests that intentionally opt in.
4. Add/adjust tests to cover default fail-closed and explicit opt-in behavior.
5. Update docs (including `docs/architecture.md` if needed) to call out the
   behavior change.
6. Last step before opening/merging the PR: update
   `docs/next_audit_generation_prompt.md` to the next eligible finding and
   update AF-004 status in `docs/audit_findings_2026-04-20.yaml`.

Out of scope (tracked separately):
- Geometry typed input validation (AF-002).
- Safety-critical rounding rationale (AF-003).

Deliverable: one PR touching only files needed for AF-004 remediation plus
`docs/next_audit_generation_prompt.md` and
`docs/audit_findings_2026-04-20.yaml` status updates in the final step.
```

## Upcoming queue

Pulled from `docs/audit_findings_2026-04-20.yaml` order and dependency gating:

1. **AF-004** — Fail closed on MVP geometry defaults in production mode *(this prompt)*
2. **AF-005** — Version and source material allowables from standards packages *(depends on AF-001)*
3. **AF-006** — Validate governance exception date ordering
4. **AF-007** — Document and test design_basis deterministic_signature
5. **AF-008** — Replace inf utilization sentinel *(depends on AF-003)*

Regenerate this file after each finding merges by re-applying the selection
rule above against the updated `status` fields.
